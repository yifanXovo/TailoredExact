"""Finite new-interface qualification; actual rows, boundary and saved points."""
from fractions import Fraction as F
from itertools import combinations
from round158_level import build,envelope,budgets
from round157_resource import travel_bounds
from round157_floor import lifted
from round157_inventory import instance
from round152_math import h_exact
from round143_lp import residual,semantics
from round158_common import *

def terms(m,c):
    row=m.getRow(c);return {row.getVar(j).VarName:F(row.getCoeff(j)) for j in range(row.size())}

def run():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'qualification/level_v1';target.mkdir(parents=True,exist_ok=False)
    facts=[];families=read(OLD157/'inventory_families.json')
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for role,source in read(OLD157/'inventory_sources.json').items():
            tau=F(read(OUT/'initial_intervals.json')[role]['tau']);data=instance(source['panel'])
            reference=None
            for variant in ('raw','rounded'):
                o,ref,info=build(source,env,variant,tau);m=o.model;plan=info['budget_plan'];contract=info['contract']
                h,H=F(contract['h_exact']),F(contract['H_exact']);assert plan['U']==H//h
                # Read back the real cutoff coefficients, including Native omissions.
                c=m.getConstrByName('original_objective_level');a=terms(m,c);scale=F(info['cutoff']['scale'])
                assert a['q']==1/scale and c.Sense=='<'
                anchors={int(i):F(v) for i,v in info['cutoff']['anchors_exact'].items()}
                excess=F(0);states=0
                for s in o.scope['stations']:
                    dev=[]
                    for y in s['support']:
                        dev.append(a.get(o.x[s['i'],y].VarName,F(0))-(h_exact(s,y)-anchors[s['i']])/scale);states+=1
                    excess+=max(dev)
                assert F(c.RHS)>=(tau-sum(anchors.values(),F(0)))/scale+excess
                checked_rows=0
                if variant=='rounded':
                    by={tuple(r['stations']):r for r in plan['rows']}
                    for r in plan['rows']:
                        ids=tuple(r['stations']);b=r['budget'];ell=F(r['lower']);assert b==(H-ell)//h
                        if r['reason']=='global_budget':assert b>=plan['U']
                        elif r['reason']!='keep':
                            R=tuple(r['dominator']);assert set(R)<set(ids)
                            assert by[R]['budget']<0 if r['reason']=='forbidden_subset' else by[R]['budget']<=b
                        if r['reason']!='keep':continue
                        for k in range(len(data['Q'])):
                            name=f'rounded_forbidden_{k}_{r["index"]}' if b<0 else f'rounded_budget_{k}_{r["index"]}'
                            row=m.getConstrByName(name);actual=terms(m,row)
                            expected={ref['s'][k,i].VarName:F(1 if b<0 else plan['U']-b) for i in ids}
                            if b>=0:expected[ref['P'][k].VarName]=F(1)
                            assert actual==expected and row.Sense=='<'
                            assert F(row.RHS)==(len(ids)-1 if b<0 else b+(plan['U']-b)*len(ids));checked_rows+=1
                        if b>=0:
                            # Exact endpoint proof of LP implication, plus all integer
                            # deltas. For delta>=1 the global bound suffices.
                            assert h*b+ell<=H and h*(b+1)+ell>H
                            assert h*plan['U']<=H
                            for delta in range(1,len(ids)+1):assert h*plan['U']+ell*(1-delta)<=H
                    for k in range(len(data['Q'])):
                        row=m.getConstrByName(f'rounded_global_{k}');assert terms(m,row)=={ref['P'][k].VarName:F(1)} and row.RHS==plan['U']
                else:
                    # One common envelope and all original real-valued tour rows.
                    assert sum(c.ConstrName.startswith('resource_subset_') for c in m.getConstrs())==len(data['Q'])*len(plan['rows'])
                path=target/f'{role}_{variant}.mps';m.write(str(path))
                with gp.read(str(path),env=env) as back:assert semantics(back)==semantics(m)
                # The historical physical control lies outside this level. Check
                # all other actual rows, never inject it into a level start.
                positive,physical=lifted(data,source['scope'],o,ref,families[role]['positive_control']['witness'])
                level_residual=residual(m,positive);assert physical['J']>float(tau)
                m.remove(c);m.update();q=residual(m,positive);assert max(q['constraints'],q['bounds'])<=1e-7,q
                write(target/f'{role}_{variant}_positive.json',dict(physical=physical,point=positive,all_other_rows=q,
                    cutoff_violation=level_residual['constraints'],outside_level=True,used_as_start=False))
                # Both variants share exactly the same coefficient envelope.
                if reference is None:reference=contract
                else:assert reference==contract
                bare,_=envelope(dict(data,T=data['T']))
                bare['T']=data['T'];old=budgets(bare,info['bounds'])
                threshold_changes=sum(a['budget']!=b['budget'] for a,b in zip(old['rows'],plan['rows']))
                facts.append(dict(role=role,variant=variant,NumVars=m.NumVars,NumConstrs=m.NumConstrs+1,NumNZs=m.NumNZs,
                    original_subsets=plan['original_subsets'],kept_subsets=plan['kept_subsets'],negative=plan['negative'],
                    minimal_forbidden=plan['minimal_forbidden'],time_acceptance_threshold_changes=threshold_changes,
                    cutoff_states_checked=states,cutoff_excess_exact=str(excess),actual_integer_rows_checked=checked_rows,
                    positive_control_other_rows=q,physical_control_outside_level=True,model_SHA=sha(path)))
                o.close()
        # The specific R92 near-one dyadic counterexample and a route accepted
        # at the floating comparison boundary must both survive our floor.
        delta=2.**-42
        micro=dict(n=2,pickup=(1-delta)/2,drop=(1-delta)/2,T=2-delta,distance=[[0.]*3 for _ in range(3)])
        md,contract=envelope(micro);assert F(md['T'])//F(md['pickup'])>=2
        boundary=dict(micro,pickup=.5,drop=.5,T=2-5e-8)
        md2,_=envelope(boundary);assert F(md2['T'])//F(md2['pickup'])>=2
        # Actual Optimize callbacks verify point persistence and normal stop.
        for label,stop in (('durable_point',False),('durable_stop',True)):
            folder=target/label;folder.mkdir()
            m=gp.Model(env=env);x=m.addVars(30,vtype='B');m.addConstr(gp.quicksum((i+1)*x[i] for i in x)<=200)
            m.setObjective(-gp.quicksum((i%7+1)*x[i] for i in x));m.Params.Threads=1;m.Params.Seed=0;m.Params.Presolve=0
            m.Params.TimeLimit=10;m.Params.SolutionLimit=1;m.Params.OutputFlag=0
            if stop:write(folder/'TERMINATE.json',dict(reason='explicit interface qualification'))
            d=Durable(folder);m.optimize(d.observe);assert not d.errors
            if stop:assert d.stopped and m.Status==gp.GRB.INTERRUPTED
            else:
                assert d.events and (folder/'incumbent_best.json.gz').exists()
                p=load_gz(folder/'incumbent_best.json.gz');q=residual(m,p);assert max(q['constraints'],q['bounds'])<=1e-7
            write(folder/'result.json',dict(status=m.Status,normal_return=True,stopped=d.stopped,saved=len(d.events),Optimize=1));m.dispose()
    write(target/'result.json',dict(UTC=utc(),PASS=True,facts=facts,R92_counterexample_retained=True,
        physical_comparison_boundary_retained=True,hard_level_full_coverage=True,known_lower_auxiliary_row_not_used=True,
        rounded_same_integer_domain_and_LP_implication=True,actual_cutoff_and_budget_rows_read=True,
        callback_Optimize_calls=2,old_positive_control_not_level_upper=True,
        review='Same agent separate source derivation, real matrix readback and exact endpoint checks; no independent human or subagent'))
    print(json.dumps(dict(PASS=True,facts=facts)),flush=True)

if __name__=='__main__':run()
