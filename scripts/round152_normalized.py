"""Exact positive-denominator integer pricing using the historical RN lift.

This is a solver formulation of the same pricing problem, not a new
normalization theorem. Binary selectors make the local t-selector products
exact. Zero stock is a separate exact component. No denominator bins remain.
"""
from fractions import Fraction as F
from itertools import combinations
from round152_math import h_exact,evaluate,states,s_bounds,outward
from round152_oracle import fallback,pi_json
from round143_lp import semantics
from round152_common import *

def price_normalized(scope,pi,target,threshold=None,cap=120):
    from round100_gurobi_runtime import gp
    target=Path(target);target.mkdir(parents=True,exist_ok=False);start=time.perf_counter();ss=scope['stations'];n=len(ss)
    low0,dp=fallback(scope,pi);b=s_bounds(scope);zero=None;stocks={};best=None;calls=[]
    if b['zero_possible']:
        ev=evaluate(scope,[0]*n,pi,True);assert ev['feasible'];zero=outward(ev['price'],False);best=outward(ev['price'],True)
        stocks[tuple(ev['Y'])]=evaluate(scope,ev['Y'],pi)
    ev=evaluate(scope,dp['Y'],pi)
    if ev['feasible']:
        best=min(best if best is not None else math.inf,outward(evaluate(scope,dp['Y'],pi,True)['price'],True));stocks[tuple(dp['Y'])]=ev
    lower=low0;reason=None
    if threshold is not None and best is not None and best<=threshold+1e-9:
        decision='DIRECTION_NONSEPARATING';reason='true_inventory_upper'
    elif b['upper']<=0:
        assert zero is not None;lower=zero;decision='PRICE_RESOLVED';reason='zero_only'
    else:
        tl=outward(1/F(b['upper']),False);tu=outward(1/F(b['lower']),True)
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
            with gp.Model(env=env) as m:
                x=m.addVars(states(scope),vtype=gp.GRB.BINARY,name='x');w=m.addVars(states(scope),lb=0,ub=tu,name='w');t=m.addVar(lb=tl,ub=tu,name='t')
                z=m.addVars([s['i'] for s in ss],lb=0,name='z');r=m.addVars([s['i'] for s in ss],lb=0,name='r')
                for s in ss:
                    i=s['i'];ys=s['support'];m.addConstr(gp.quicksum(x[i,y] for y in ys)==1,name=f'onehot_{i}')
                    m.addConstr(gp.quicksum(w[i,y] for y in ys)==t,name=f'mass_{i}')
                    for y in ys:m.addConstr(w[i,y]>=tl*x[i,y]);m.addConstr(w[i,y]<=tu*x[i,y])
                    m.addConstr(z[i]==gp.quicksum(y*w[i,y] for y in ys),name=f'normalized_inventory_{i}')
                    m.addConstr(r[i]==s['c']*z[i],name=f'normalized_ratio_{i}')
                total=gp.quicksum(y*x[i,y] for i,y in x)
                m.addConstr(total>=scope['Bminus'],name='hard_lower');m.addConstr(total<=scope['B'],name='hard_upper')
                m.addConstr(gp.quicksum(r.values())==1,name='normalization')
                # These old scaled-stock rows strengthen only the relaxation;
                # they are implied at integer selectors.
                m.addConstr(gp.quicksum(z.values())>=scope['Bminus']*t,name='scaled_stock_lower')
                m.addConstr(gp.quicksum(z.values())<=scope['B']*t,name='scaled_stock_upper')
                pairs=list(combinations([s['i'] for s in ss],2));a=m.addVars(pairs,lb=0,name='a')
                for i,j in pairs:m.addConstr(a[i,j]>=r[i]-r[j]);m.addConstr(a[i,j]>=r[j]-r[i])
                q=m.addVar(lb=scope['gamma_L'],name='q');A=gp.quicksum(a.values())
                m.addConstr(A<=n*q,name='true_G_epigraph');m.addConstr(A<=outward(F(n)*F(scope['gamma_U']),True),name='physical_G_upper')
                costs={(s['i'],y):h_exact(s,y)-F(pi.get((s['i'],y),0)) for s in ss for y in s['support']}
                m.setObjective(q+gp.quicksum(outward(v,False)*x[k] for k,v in costs.items()))
                m.update();m.write(str(target/'model.mps'));expected=semantics(m)
            with gp.read(str(target/'model.mps'),env=env) as m:
                assert semantics(m)==expected
                correction=sum(max(max(F(0),F(m.getVarByName(f'x[{s["i"]},{y}]').Obj)-costs[s['i'],y]) for y in s['support']) for s in ss)
                guard=1e-6*(1+sum(max(abs(float(costs[s['i'],y])) for y in s['support']) for s in ss))
                m.Params.TimeLimit=cap;m.Params.MIPGap=1e-4;m.Params.MIPGapAbs=1e-7;m.Params.IntFeasTol=1e-6;m.Params.FeasibilityTol=1e-6
                m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
                write(target/'call.json',dict(UTC=utc(),kind='MIP_normalized_exact_positive',scope=scope,pi=pi_json(pi),cap=cap,Seed=0,Threads=1,
                       model_SHA=sha(target/'model.mps'),t_bounds=[tl,tu],numerical_guard=guard,objective_correction=str(correction),complete_matrix_readback=True))
                built=time.perf_counter();m.optimize();done=time.perf_counter()
                write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
                qualified=m.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT) and math.isfinite(m.ObjBound) and abs(m.ObjBound)<1e90
                positive_lower=max(low0,m.ObjBound-guard-float(correction)) if qualified else low0
                empty=m.Status==gp.GRB.INFEASIBLE
                call=dict(Status=m.Status,proven_empty=empty,lower=positive_lower if not empty else None,
                          native_bound=m.ObjBound if qualified else None,bound_status_qualified=qualified,approximation_epsilon=0.,
                          objective_correction=float(correction),numerical_guard=guard,Runtime=m.Runtime,Work=m.Work,nodes=m.NodeCount,iterations=m.IterCount,
                          columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs,construct_seconds=built-start,optimize_seconds=done-built)
                if m.SolCount:
                    yy=[max(s['support'],key=lambda y:m.getVarByName(f'x[{s["i"]},{y}]').X) for s in ss]
                    ev=evaluate(scope,yy,pi);quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','IntVio']}
                    call.update(native_incumbent=m.ObjVal,native_gap=m.MIPGap,quality=quality,candidate=ev)
                    if ev['feasible'] and max(quality.values())<=1e-6:
                        ub=outward(evaluate(scope,yy,pi,True)['price'],True);best=min(best if best is not None else math.inf,ub);stocks[tuple(yy)]=ev
                        call['upper']=ub
                    save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
                calls.append(call)
                components=([positive_lower] if not empty else [])+([zero] if zero is not None else [])
                lower=min(components) if components else None
                if lower is None:decision='EMPTY_DOMAIN';reason='positive_infeasible_and_no_zero'
                elif threshold is not None and lower>threshold+1e-7:decision='SEPARATION';reason='qualified_complete_domain_lower'
                elif threshold is not None and best is not None and best<=threshold+1e-9:decision='DIRECTION_NONSEPARATING';reason='true_inventory_upper'
                elif best is not None and best-lower<=1e-5:decision='PRICE_RESOLVED';reason='global_gap'
                else:decision='UNDECIDED';reason='MIP_gap_or_qualification'
        write(target/'positive_result.json',calls[-1])
    result=dict(scope=scope,pi=pi_json(pi),threshold=threshold,lower=lower,upper=best,decision=decision,reason=reason,
                calls=calls,stocks=list(stocks.values()),zero_lower=zero,fallback_lower=low0,denominator_scope=b,
                denominator_approximation_error=0.,complete_domain=True,positive_formulation='historical_RN_with_binary_selectors',
                seconds=time.perf_counter()-start,inventory_upper_is_not_physical_BRP_U=True)
    write(target/'result.json',result);return result

def qualify(label='v1'):
    from itertools import product
    from round152_qualify import scope
    from round150_lp import affinity
    configure();affinity();target=OUT/'qualification_normalized'/label;target.mkdir(parents=True,exist_ok=True);facts=[]
    assert not (target/'result.json').exists(),'Closed qualification is not rerun'
    domains=[('hetero',scope([1.,.5,.25],[[0,1,2,3,4]]*3,2,5,0.,.75)),
             ('nonminimal_zero',scope([.5,1.],[[0,1,3],[0,1,2]],0,3,.2,.5)),
             ('zero_only',scope([1.,.5],[[0],[0]],0,0,.3,.5))]
    for tag,d in domains:
        pi={(s['i'],y):(.625 if y%2 else -.375) for s in d['stations'] for y in s['support']}
        universe=[evaluate(d,Y,pi,True) for Y in product(*[s['support'] for s in d['stations']])];universe=[v for v in universe if v['feasible']]
        true=min(v['price'] for v in universe);bounds=s_bounds(d)
        for p in universe:
            if not p['S']:continue
            t=1/p['S'];assert F(outward(1/F(bounds['upper']),False))<=t<=F(outward(1/F(bounds['lower']),True))
            normalized=[F(s['c'])*y*t for s,y in zip(d['stations'],p['Y'])];assert sum(normalized)==1
            assert sum(abs(a-b) for a,b in combinations(normalized,2))/len(d['stations'])==p['G']
        saved=target/tag/'result.json'
        rr=read(saved) if saved.exists() else price_normalized(d,pi,target/tag,None,30)
        assert rr['scope']==d and rr['pi']==pi_json(pi)
        assert rr['lower'] is not None and F(rr['lower'])<=true<=F(rr['upper'])
        if rr['calls'] and rr['calls'][0]['Status']==2:
            cc=rr['calls'][0]
            assert rr['upper']-rr['lower']<=max(1e-7,1e-4*abs(cc['native_incumbent']))+cc['numerical_guard']+cc['objective_correction']+1e-9
        facts.append(dict(tag=tag,feasible=len(universe),exact_price=str(true),lower=rr['lower'],upper=rr['upper'],decision=rr['decision']))
    write(target/'result.json',dict(PASS=True,positive_integer_equivalence=True,zero_separate=True,nonminimal_completion=True,negative_potentials=True,facts=facts))
    print(json.dumps(facts),flush=True)

if __name__=='__main__':qualify(*sys.argv[1:])
