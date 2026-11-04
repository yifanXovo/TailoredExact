"""Bounded residual potentials; exact complement-DP lift to the full scope.

The active face is a discovery/pricing device. It never fixes selectors in
the complete BRP LP. The final full-domain lower bound is the minimum of the
active oracle bound and the exact unary-resource complement bound.
"""
from fractions import Fraction as F
from round152_math import h_exact,evaluate,states,outward
from round152_oracle import price,pi_json
from round152_common import *

def complement_dp(scope,active,pi):
    dp={(0,False):F(0)}
    for s in scope['stations']:
        nxt={};i=s['i'];cost={y:h_exact(s,y)-F(pi[i,y]) for y in s['support']}
        for (t,flag),v in dp.items():
            for y in s['support']:
                u=t+y
                if u>scope['B']:continue
                key=(u,flag or y not in active[i]);vv=v+cost[y]
                if key not in nxt or vv<nxt[key]:nxt[key]=vv
        dp=nxt
    values=[v for (t,flag),v in dp.items() if flag and t>=scope['Bminus']]
    if not values:return dict(empty=True,lower=None,exact=None)
    val=F(scope['gamma_L'])+min(values)
    return dict(empty=False,lower=outward(val,False),exact=str(val))

def make_pi(scope,psi,active,M,anchors):
    return {(s['i'],y):float(h_exact(s,y))+(psi.get((s['i'],y),0.) if y in active[s['i']] else -M)-anchors[s['i']]
            for s in scope['stations'] for y in s['support']}

def dual_master(scope,active,point,columns,radius,target):
    from round100_gurobi_runtime import gp
    target=Path(target);target.mkdir(parents=True,exist_ok=False);ss=scope['stations']
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.Model(env=env) as m:
            keys=[(s['i'],y) for s in ss for y in active[s['i']]]
            psi=m.addVars(keys,lb=-radius,ub=radius,name='psi');a=m.addVar(lb=-gp.GRB.INFINITY,name='a')
            anchors={}
            for s in ss:
                i=s['i'];anchor=max(active[i],key=lambda y:point[f'state_{i}_{y}']);psi[i,anchor].LB=psi[i,anchor].UB=0.
                anchors[i]=float(h_exact(s,anchor))
            for k,Y in enumerate(columns):
                ev=evaluate(scope,Y,exact=True);assert ev['feasible']
                cost=outward(max(F(scope['gamma_L']),ev['G']),True)
                m.addConstr(a+gp.quicksum(psi[s['i'],y] for s,y in zip(ss,Y))<=cost,name=f'column_{k}')
            m.setObjective(a+gp.quicksum(point[f'state_{i}_{y}']*psi[i,y] for i,y in keys),gp.GRB.MAXIMIZE)
            m.Params.TimeLimit=30;m.update();m.write(str(target/'model.mps'))
            write(target/'call.json',dict(UTC=utc(),kind='LP_master_candidate_only',Seed=0,Threads=1,cap=30,model_SHA=sha(target/'model.mps')))
            m.optimize();write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
            assert m.Status==gp.GRB.OPTIMAL
            result=dict(a=a.X,psi=pi_json({k:v.X for k,v in psi.items()}),objective=m.ObjVal,Runtime=m.Runtime,Work=m.Work,
                        columns=len(columns),variables=m.NumVars,rows=m.NumConstrs,radius=radius,
                        restricted_intercept_never_used_as_global_lower=True)
            write(target/'result.json',result)
            return {k:v.X for k,v in psi.items()},anchors,result

def discover(role,variant,label,radius=.05,iterations=12):
    from round150_lp import affinity
    from round100_gurobi_runtime import binding
    configure();affinity();assert binding()['sha256']==DLL_SHA
    target=OUT/'discovery'/f'{role}_{variant}_{label}';target.mkdir(parents=True,exist_ok=False)
    d=read(OUT/'domains'/role/'domain.json');scope=d['scope'];ss=scope['stations']
    point=load_gz(OUT/'LP'/f'{role}_{variant}'/'solution.json.gz');eta=read(OUT/'LP'/f'{role}_{variant}'/'result.json')['L']
    proj=read(OUT/'projection'/f'{role}_{variant}'/'result.json');assert proj['full_oracle_projection_feasible']
    active={s['i']:[y for y in s['support'] if point[f'state_{s["i"]}_{y}']>1e-10] for s in ss}
    restricted=dict(scope,stations=[dict(s,support=active[s['i']],lo=min(active[s['i']]),hi=max(active[s['i']])) for s in ss])
    columns={tuple(p['Y']) for p in proj['paths']};assert all(all(y in active[s['i']] for s,y in zip(ss,Y)) for Y in columns)
    records=[];rows=[];started=time.perf_counter()
    write(target/'plan.json',dict(scope=scope,active_scope=restricted,point_SHA=sha(OUT/'LP'/f'{role}_{variant}'/'solution.json.gz'),
          radius=radius,iterations=iterations,active_states=sum(map(len,active.values())),full_states=len(states(scope)),
          projection_mixture_qualified=True,all_original_complete_LP_selectors_remain_free=True,
          complement='hard-resource DP with at least one inactive choice; exact dyadic costs',before_results=True))
    for iteration in range(iterations):
        folder=target/f'iter{iteration:02}';psi,anchors,master=dual_master(scope,active,point,sorted(columns),radius,folder/'master')
        M=1+len(ss)*radius;pi=make_pi(scope,psi,active,M,anchors)
        dot=math.fsum(pi[i,y]*point[f'state_{i}_{y}'] for i,y in pi)
        activity_error=math.fsum(abs(pi[i,y]*point[f'state_{i}_{y}']) for i,y in pi if y not in active[i] or point[f'state_{i}_{y}']<0)
        rr=price(restricted,pi,folder/'pricing',threshold=eta-dot+activity_error+1e-6,cap=20,max_calls=24,width=.10)
        assert rr['lower'] is not None
        for p in rr['stocks']:
            assert evaluate(scope,p['Y'],pi)['feasible'];columns.add(tuple(p['Y']))
        # Lift by actual complement pricing, then reduce the uniform inactive
        # penalty while retaining the achieved active lower bound.
        comp=complement_dp(scope,active,pi)
        lift_trials=[dict(M=M,**comp)]
        if not comp['empty'] and comp['lower']>=rr['lower']:
            low,high=0.,M
            for k in range(12):
                mid=(low+high)/2;test=make_pi(scope,psi,active,mid,anchors);cc=complement_dp(scope,active,test)
                lift_trials.append(dict(M=mid,**cc))
                if cc['empty'] or cc['lower']>=rr['lower']:high=mid
                else:low=mid
            M=high;pi=make_pi(scope,psi,active,M,anchors);comp=complement_dp(scope,active,pi)
        full_lower=min(rr['lower'],comp['lower']) if not comp['empty'] else rr['lower']
        dot=math.fsum(pi[i,y]*point[f'state_{i}_{y}'] for i,y in pi)
        activity_error=math.fsum(abs(pi[i,y]*point[f'state_{i}_{y}']) for i,y in pi if y not in active[i] or point[f'state_{i}_{y}']<0)
        # Drop Native-tiny written coefficients using exact one-hot transport.
        pi_hat={k:(v if abs(v)>=1e-12 else 0.) for k,v in pi.items()}
        correction=sum(max(F(pi_hat[s['i'],y])-F(pi[s['i'],y]) for y in s['support']) for s in ss)
        alpha=outward(F(full_lower)-correction,False)
        activity=alpha+math.fsum(pi_hat[i,y]*point[f'state_{i}_{y}'] for i,y in pi_hat)
        separated=activity>eta+activity_error+1e-6
        rec=dict(iteration=iteration,master=master,pricing=rr['decision'],active_lower=rr['lower'],active_upper=rr['upper'],
                 complement=comp,M=M,lift_trials=lift_trials,full_lower=full_lower,transported_alpha=alpha,
                 pi=pi_json(pi_hat),potential_transport_exact=str(correction),activity=activity,eta=eta,
                 activity_uncertainty=activity_error,separation=separated,violation=activity-eta,
                 column_count=len(columns),pricing_seconds=rr['seconds'])
        records.append(rec);write(folder/'lift.json',rec)
        print(json.dumps(dict(role=role,iteration=iteration,decision=rr['decision'],violation=activity-eta,separated=separated,columns=len(columns))),flush=True)
        if separated:
            terms={'G':1.};terms.update({f'e_{s["i"]}':s['omega'] for s in ss if s['omega']})
            terms.update({f'state_{i}_{y}':-v for (i,y),v in pi_hat.items() if v})
            rows.append(dict(name=f'r152_epigraph_{label}',terms=terms,sense='>',rhs=alpha));break
        if rr['decision']=='UNDECIDED':break
        if master['objective']+math.fsum(float(h_exact(s,y))*point[f'state_{s["i"]}_{y}'] for s in ss for y in s['support'])<=eta+1e-7:break
    result=dict(role=role,parent=variant,scope=scope,active_scope=restricted,qualified=bool(rows),rows=rows,iterations=records,
                seconds=time.perf_counter()-started,all_original_variables_free_for_followup=True,
                negative_and_zero_mass_used_only_for_discovery=True,complete_parent_scope_covered_by_active_and_complement=True)
    write(target/'result.json',result);print(json.dumps(dict(qualified=bool(rows),iterations=len(records),seconds=result['seconds'])),flush=True)

if __name__=='__main__':discover(*sys.argv[1:4],radius=float(sys.argv[4]) if len(sys.argv)>4 else .05)
