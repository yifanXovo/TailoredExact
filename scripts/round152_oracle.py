"""Reference denominator-bin MILP and complete-cover bound aggregation.

This module never treats a restricted-master intercept or an inventory
incumbent as a pricing lower bound. Every inventory UB is reevaluated using
the exact dyadic model coefficients and all actual oracle-domain conditions.
"""
from fractions import Fraction as F
from itertools import combinations
from round152_math import evaluate,h_exact,unary_dp,bins,outward,states
from round143_lp import semantics
from round152_common import *

def pi_json(pi):return {f'{i}:{y}':v for (i,y),v in pi.items()}
def pi_read(data):return {tuple(map(int,k.split(':'))):v for k,v in data.items()}

def fallback(scope,pi):
    costs={(s['i'],y):h_exact(s,y)-F(pi.get((s['i'],y),0)) for s in scope['stations'] for y in s['support']}
    d=unary_dp(scope,costs)
    assert d is not None
    return outward(F(scope['gamma_L'])+F(d['exact']),False),d

def solve_bin(scope,pi,interval,target,cap=30,warm=None):
    from round100_gurobi_runtime import gp
    target=Path(target);target.mkdir(parents=True,exist_ok=False);ss=scope['stations'];n=len(ss);ell,upper=interval
    start=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.setParam('Threads',1);env.setParam('Seed',0);env.start()
        with gp.Model(env=env) as m:
            xx=m.addVars(states(scope),vtype=gp.GRB.BINARY,name='x')
            Y=m.addVars([s['i'] for s in ss],lb=0,name='Y');r=m.addVars([s['i'] for s in ss],lb=0,name='r')
            for s in ss:
                i=s['i'];m.addConstr(gp.quicksum(xx[i,y] for y in s['support'])==1,name=f'onehot_{i}')
                m.addConstr(Y[i]==gp.quicksum(y*xx[i,y] for y in s['support']),name=f'inventory_{i}')
                m.addConstr(r[i]==s['c']*Y[i],name=f'ratio_{i}')
            pairs=list(combinations([s['i'] for s in ss],2));aa=m.addVars(pairs,lb=0,name='a')
            for i,j in pairs:m.addConstr(aa[i,j]>=r[i]-r[j]);m.addConstr(aa[i,j]>=r[j]-r[i])
            S=gp.quicksum(r.values());A=gp.quicksum(aa.values());total=gp.quicksum(Y.values())
            m.addConstr(total>=scope['Bminus'],name='hard_lower');m.addConstr(total<=scope['B'],name='hard_upper')
            m.addConstr(S>=ell,name='bin_lower');m.addConstr(S<=upper,name='bin_upper')
            # Coefficients multiplying nonnegative q/S are rounded UP: relaxation.
            den=outward(F(n)*F(upper),True);gcap=outward(F(n)*F(scope['gamma_U']),True)
            q=m.addVar(lb=scope['gamma_L'],name='q')
            m.addConstr(A<=den*q,name='surrogate_G');m.addConstr(A<=gcap*S,name='physical_G_upper')
            costs={(s['i'],y):h_exact(s,y)-F(pi.get((s['i'],y),0)) for s in ss for y in s['support']}
            m.setObjective(q+gp.quicksum(outward(v,False)*xx[k] for k,v in costs.items()))
            if warm:
                for s,y0 in zip(ss,warm):
                    for y in s['support']:xx[s['i'],y].Start=float(y==y0)
            m.update();m.write(str(target/'model.mps'))
            expected=semantics(m)
        with gp.read(str(target/'model.mps'),env=env) as m:
            assert semantics(m)==expected
            if warm:
                for s,y0 in zip(ss,warm):
                    for y in s['support']:m.getVarByName(f'x[{s["i"]},{y}]').Start=float(y==y0)
            correction=F(0)
            for s in ss:
                correction+=max([max(F(0),F(m.getVarByName(f'x[{s["i"]},{y}]').Obj)-costs[s['i'],y]) for y in s['support']])
            # Accepted floating MIP bound, with a declared objective guard;
            # this does not claim exact rational MIP optimality.
            guard=1e-6*(1+sum(max(abs(float(costs[s['i'],y])) for y in s['support']) for s in ss))
            m.Params.TimeLimit=float(cap);m.Params.MIPGap=1e-4;m.Params.MIPGapAbs=1e-7
            m.Params.IntFeasTol=1e-6;m.Params.FeasibilityTol=1e-6;m.Params.OptimalityTol=1e-6
            m.Params.OutputFlag=1;m.Params.LogToConsole=0;m.Params.LogFile=str(target/'native.log')
            write(target/'call.json',dict(UTC=utc(),kind='MIP',model_SHA=sha(target/'model.mps'),scope=scope,pi=pi_json(pi),bin=interval,cap=cap,Seed=0,Threads=1,
                  numerical_guard=guard,objective_transport_correction=str(correction),denominator_coefficient=den,gini_cap_coefficient=gcap))
            built=time.perf_counter();m.optimize();done=time.perf_counter()
            write(target/'return.json',dict(UTC=utc(),Status=m.Status,Runtime=m.Runtime,Work=m.Work))
            bound=m.ObjBound if m.Status not in (gp.GRB.INFEASIBLE,gp.GRB.INF_OR_UNBD) else None
            valid_bound=m.Status in (gp.GRB.OPTIMAL,gp.GRB.TIME_LIMIT) and bound is not None and math.isfinite(bound) and abs(bound)<1e90
            result=dict(Status=m.Status,proven_empty=m.Status==gp.GRB.INFEASIBLE,lower=bound-guard-float(correction) if valid_bound else None,
                        native_bound=bound if valid_bound else None,upper=None,incumbent=None,bin=interval,
                        approximation_epsilon=min(scope['gamma_U'],(n-1)/n)*(1-ell/upper),numerical_guard=guard,
                        objective_correction=float(correction),Runtime=m.Runtime,Work=m.Work,nodes=m.NodeCount,iterations=m.IterCount,
                        construct_seconds=built-start,optimize_seconds=done-built,columns=m.NumVars,rows=m.NumConstrs,nonzeros=m.NumNZs,
                        complete_matrix_native_readback=True,bound_status_qualified=valid_bound,
                        accepted_bound_statuses=['OPTIMAL','TIME_LIMIT'],abnormal_status_falls_back=True)
            if m.SolCount:
                yy=[int(round(m.getVarByName(f'Y[{s["i"]}]').X)) for s in ss];ev=evaluate(scope,yy,pi)
                quality={k:m.getAttr(k) for k in ['ConstrVio','BoundVio','IntVio']}
                result.update(native_incumbent=m.ObjVal,native_gap=m.MIPGap,quality=quality,candidate=ev)
                if ev['feasible'] and max(quality.values())<=1e-6:
                    exact=evaluate(scope,yy,pi,True);result.update(upper=outward(exact['price'],True),incumbent=ev)
                save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
            write(target/'result.json',result)
    return result

def price(scope,pi,target,threshold=None,cap=30,max_calls=32,width=.15,refine=True):
    target=Path(target);target.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();lower0,dp=fallback(scope,pi);b,intervals=bins(scope,width)
    nodes=[dict(id=f'b{k:03}',interval=v,lower=lower0,solved=False,empty=False,depth=0) for k,v in enumerate(intervals)]
    best=None;stocks={};zero=None
    if b['zero_possible']:
        ez=evaluate(scope,[0]*len(scope['stations']),pi,True)
        assert ez['feasible'];zero=outward(ez['price'],False)
        best=outward(ez['price'],True);stocks[tuple(ez['Y'])]=evaluate(scope,ez['Y'],pi)
    ev=evaluate(scope,dp['Y'],pi)
    if ev['feasible']:
        best=min(best if best is not None else math.inf,outward(evaluate(scope,dp['Y'],pi,True)['price'],True));stocks[tuple(dp['Y'])]=ev
    calls=[];decision='UNDECIDED';reason='call_limit'
    for iteration in range(max_calls+1):
        valid=[v['lower'] for v in nodes if not v['empty']]+([zero] if zero is not None else [])
        lower=min(valid) if valid else None
        if not valid:decision='EMPTY_DOMAIN';reason='all_components_proven_empty';break
        if threshold is not None and lower>threshold+1e-7:decision='SEPARATION';reason='complete_cover_lower_exceeds_threshold';break
        if threshold is not None and best is not None and best<=threshold+1e-9:decision='DIRECTION_NONSEPARATING';reason='true_feasible_upper_at_or_below_threshold';break
        if best is not None and best-lower<=1e-5:decision='PRICE_RESOLVED';reason='global_gap';break
        if iteration==max_calls:break
        candidates=[v for v in nodes if not v['empty']]
        candidates.sort(key=lambda v:(v['lower'],v['solved'],v['id']))
        node=candidates[0]
        if node['solved']:
            if not refine:break
            gap=(node['result'].get('native_incumbent',math.inf)-(node['result'].get('native_bound') if node['result'].get('native_bound') is not None else -math.inf))
            eps=node['result']['approximation_epsilon']
            if eps>1e-5 and (gap<=eps or node['depth']<1):
                ell,u=node['interval'];mid=math.sqrt(ell*u);nodes.remove(node)
                for tag,inter in [('L',[ell,mid]),('R',[mid,u])]:
                    nodes.append(dict(id=node['id']+tag,interval=inter,lower=node['lower'],solved=False,empty=False,depth=node['depth']+1))
                node=next(v for v in nodes if v['id']==node['id']+'L')
            else:
                # A deterministic deeper MIP solve on the limiting bin, with
                # doubled offline cap; bounds from previous calls are retained.
                node['revisits']=node.get('revisits',0)+1
        call_id=f'{iteration:03}_{node["id"]}'
        thiscap=cap*(2**min(node.get('revisits',0),3))
        rr=solve_bin(scope,pi,node['interval'],target/call_id,thiscap,warm=next(iter(stocks),None))
        calls.append(dict(id=call_id,bin_id=node['id'],cap=thiscap,**rr))
        node.update(solved=True,empty=rr['proven_empty'],result=rr)
        if rr['lower'] is not None:node['lower']=max(node['lower'],rr['lower'])
        if rr['upper'] is not None:
            best=min(best if best is not None else math.inf,rr['upper']);stocks[tuple(rr['incumbent']['Y'])]=rr['incumbent']
        write(target/'progress.json',dict(iteration=iteration,calls=len(calls),best_upper=best,nodes=nodes))
    result=dict(scope=scope,pi=pi_json(pi),threshold=threshold,decision=decision,reason=reason,lower=lower,upper=best,zero_lower=zero,
                fallback_lower=lower0,fallback_dp=dp,denominator_scope=b,active_bins=nodes,calls=calls,stocks=list(stocks.values()),
                complete_cover=True,all_unprocessed_bins_keep_fallback=True,seconds=time.perf_counter()-start,
                negative_lower_retained=True,inventory_upper_is_not_physical_BRP_U=True)
    write(target/'result.json',result);return result

if __name__=='__main__':
    from round150_lp import affinity
    from round100_gurobi_runtime import binding
    configure();affinity();assert binding()['sha256']==DLL_SHA
    role,variant,label= sys.argv[1:4]
    scope=read(OUT/'domains'/role/'domain.json')['scope'];point=load_gz(OUT/'LP'/f'{role}_{variant}'/'solution.json.gz')
    if label=='zero':pi={k:0. for k in states(scope)}
    elif label=='ap':pi={(s['i'],y):float(h_exact(s,y)) for s in scope['stations'] for y in s['support']}
    else:pi=pi_read(read(label)['pi'])
    eta=read(OUT/'LP'/f'{role}_{variant}'/'result.json')['L'];dot=math.fsum(pi[i,y]*point[f'state_{i}_{y}'] for i,y in pi)
    result=price(scope,pi,OUT/'oracle'/f'{role}_{variant}_{Path(label).stem}',eta-dot,cap=20,max_calls=24)
    print(json.dumps({k:result[k] for k in ['decision','lower','upper','threshold','seconds']}),flush=True)
