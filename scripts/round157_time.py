"""Time-free full-fleet minimax diagnostic with exact lazy subtour separation.

This alternative is used only after original-T feasibility is attempted.
Its bounds are on required time, never on the original inventory objective.
"""
from round157_fleet import build, decode, verify, lift
from round157_inventory import instance, classes, value
from round157_common import *
from round143_math import outward
from fractions import Fraction as F
from types import SimpleNamespace

def components(selected):
    succ={i:j for i,j in selected};cycles=[];unseen=set(succ)
    while unseen:
        first=min(unseen);cycle=[];i=first
        while i not in cycle:
            assert i in succ
            cycle.append(i);i=succ[i]
        assert i==first
        unseen.difference_update(cycle)
        if 0 not in cycle:cycles.append(cycle)
    return cycles

def reformulate(model,ref,data):
    # A bound for every time-free simple feasible tour, from R61. No
    # original-T arc deletion or original-T propagated inventory domain.
    safe=(data['n']+1)*max(max(r) for r in data['distance'])+(data['pickup']+data['drop'])*sum(data['initial'][1:])
    for c in model.getConstrs():
        if c.ConstrName.startswith(('order_','original_time_')):model.remove(c)
    model.remove(list(ref['u'].values()));ref['u']={}
    t=model.addVar(lb=0,ub=safe,name='Tstar')
    from round100_gurobi_runtime import gp
    for k,ids in ref['active'].items():
        travel=gp.quicksum(data['distance'][i][j]*v for (kk,i,j),v in ref['x'].items() if kk==k)
        model.addConstr(travel+(data['pickup']+data['drop'])*gp.quicksum(ref['p'][k,i] for i in ids)<=t,
                        name=f'time_free_duration_{k}')
    model.setObjective(t);model.update()
    return t,safe

def nearest_seed(data,Y):
    """One deterministic load-feasible tour; diagnostic start, no T claim."""
    remaining={i for i,v in enumerate(Y,1) if v!=data['initial'][i]}
    k=max(range(len(data['Q'])),key=lambda k:(data['Q'][k],-k));Q=data['Q'][k]
    load=0;nodes=[0];ops=[]
    while remaining:
        eligible=[i for i in remaining if 0<=load+data['initial'][i]-Y[i-1]<=Q]
        if not eligible:return None
        i=min(eligible,key=lambda i:(data['distance'][nodes[-1]][i],i))
        delta=data['initial'][i]-Y[i-1];load+=delta
        nodes.append(i);ops.append(dict(station=i,pickup=max(0,delta),drop=max(0,-delta)))
        remaining.remove(i)
    witness=dict(routes=[dict(vehicle=k,nodes=nodes+[0],operations=ops)] if ops else [])
    witness['objective']=verify(data,witness)['J']
    return witness

def run(role,rank,mode,label,nodes=65536,cap=7200):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_lp import residual
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_families.json')[role];c=source['candidates'][int(rank)-1]
    data=instance(source['panel']);members=[c['Y']] if mode=='fixed' else c['members']
    # Time-free inventory support is exactly this externally specified
    # finite family, not a domain inferred with original-T propagation.
    supports={i:sorted({v[i-1] for v in members}) for i in range(1,data['n']+1)}
    target=OUT/'time'/label;target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        model,ref=build(data,supports,env,classes(source['scope'],c['Y']) if mode=='family' else None)
        start=nearest_seed(data,c['Y']);point=lift(data,ref,start) if start else None
        t,safe=reformulate(model,ref,data)
        if point:
            point={v.VarName:point.get(v.VarName,verify(data,start)['maximum_duration'] if v.VarName=='Tstar' else 0.) for v in model.getVars()}
            q=residual(model,point);assert q['constraints']<=1e-7 and q['bounds']<=1e-7,q
            for v in model.getVars():v.Start=point[v.VarName]
            write(target/'start.json',dict(witness=start,physical=verify(data,start),quality=q))
        model.Params.Threads=1;model.Params.Seed=0;model.Params.MIPGap=0;model.Params.MIPGapAbs=0
        model.Params.NodeLimit=int(nodes);model.Params.TimeLimit=float(cap);model.Params.LazyConstraints=1
        model.Params.DualReductions=0;model.Params.MIPFocus=1
        model.Params.LogFile=str(target/'native.log');model.Params.OutputFlag=1;model.Params.LogToConsole=0
        model.write(str(target/'model.mps'))
        write(target/'condition.json',dict(role=role,rank=int(rank),mode=mode,members=members,panel=source['panel'],
            safe_time_bound=safe,original_T=data['T'],original_T_arc_deletions=0,original_T_rows=0,
            inventory_condition_from_saved_family=True,canonical_SHA=sha(target/'model.mps'),source_SHA=sha(__file__),
            lazy_constraints=True,stop='original_T_witness_or_guarded_time_lower_or_capacity',
            Seed=0,Threads=1,NodeLimit=int(nodes),TimeLimit=float(cap),historical_route_start=False))
        lazy=[];incumbents=[];progress=[];errors=[];margin=1e-5*max(1,data['T']);stop=[None]
        callback_feasible=[None]
        allvars=model.getVars();varnames=[v.VarName for v in allvars]
        def callback(m,where):
            try:
                if where==gp.GRB.Callback.MIPSOL:
                    disconnected=[]
                    for k in ref['active']:
                        selected=[(i,j) for (kk,i,j),v in ref['x'].items() if kk==k and m.cbGetSolution(v)>.5]
                        for cycle in components(selected):
                            terms=[ref['x'][k,i,j] for i in cycle for j in cycle if i!=j]
                            m.cbLazy(gp.quicksum(terms)<=len(cycle)-1)
                            lazy.append(dict(vehicle=k,stations=cycle,rhs=len(cycle)-1,
                                             seconds=time.perf_counter()-tick))
                            disconnected.append(cycle)
                    if not disconnected:
                        upper=m.cbGet(gp.GRB.Callback.MIPSOL_OBJ)
                        incumbents.append(dict(seconds=time.perf_counter()-tick,time_upper=upper))
                        if upper<=data['T']:
                            # A physical callback vector can be valid even
                            # if termination precedes native acceptance.
                            physical_ref=dict(ref,
                                x={k:SimpleNamespace(X=m.cbGetSolution(v)) for k,v in ref['x'].items()},
                                w={k:SimpleNamespace(X=m.cbGetSolution(v)) for k,v in ref['w'].items()})
                            witness,checked=decode(data,physical_ref)
                            assert checked['original_T_feasible'] and checked['Y'] in members
                            assert str(value(source['scope'],checked['Y'])['phi'])==c['J_exact']
                            point=dict(zip(varnames,m.cbGetSolution(allvars)))
                            write(target/'callback_witness.json',witness)
                            write(target/'callback_physical_check.json',checked)
                            save_gz(target/'callback_solution.json.gz',point)
                            callback_feasible[0]=(witness,checked)
                            stop[0]='verified_original_T_callback_vector';m.terminate()
                elif where==gp.GRB.Callback.MIP:
                    lower=m.cbGet(gp.GRB.Callback.MIP_OBJBND);node=m.cbGet(gp.GRB.Callback.MIP_NODCNT)
                    if not progress or node>=progress[-1]['nodes']+1024:
                        progress.append(dict(seconds=time.perf_counter()-tick,nodes=node,time_lower=lower))
                    if lower>data['T']+margin and lower<gp.GRB.INFINITY:
                        stop[0]='guarded_time_lower';m.terminate()
            except BaseException as error:
                errors.append(dict(type=type(error).__name__,message=str(error)));m.terminate()
        write(target/'native_call.json',dict(UTC=utc(),state='BEFORE_OPTIMIZE'))
        model.optimize(callback)
        write(target/'lazy_rows.json',lazy);write(target/'incumbents.json',incumbents);write(target/'progress.json',progress)
        result=dict(role=role,rank=int(rank),mode=mode,status=model.Status,SolCount=model.SolCount,
            Runtime=model.Runtime,Work=model.Work,NodeCount=model.NodeCount,IterCount=model.IterCount,
            time_lower=model.ObjBound if abs(model.ObjBound)<gp.GRB.INFINITY else None,time_upper=None,
            classification='UNKNOWN',physical_U=None,physical_L_change=0.,stop=stop[0],callback_errors=errors,
            lazy_rows=len(lazy),model_SHA=sha(target/'model.mps'),condition_SHA=sha(target/'condition.json'),
            time_lower_is_not_J_lower=True,inventory_J=c['J'],original_T=data['T'])
        assert not errors,errors
        if model.SolCount:
            witness,check=decode(data,ref);assert check['Y'] in members
            assert abs(check['maximum_duration']-model.ObjVal)<=1e-5
            v=value(source['scope'],check['Y']);assert str(v['phi'])==c['J_exact']
            write(target/'witness.json',witness);write(target/'physical_check.json',check)
            save_gz(target/'solution.json.gz',{v.VarName:v.X for v in model.getVars()})
            result['time_upper']=check['maximum_duration']
            if check['original_T_feasible']:result.update(classification='FEAS',physical_U=outward(F(c['J_exact']),True))
        if callback_feasible[0] is not None:
            witness,check=callback_feasible[0]
            result.update(classification='FEAS',physical_U=outward(F(c['J_exact']),True),
                          time_upper=check['maximum_duration'],callback_physical_vector_verified=True)
        bound_qualified=model.Status in (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT,gp.GRB.TIME_LIMIT,gp.GRB.WORK_LIMIT) or (model.Status==gp.GRB.INTERRUPTED and stop[0] is not None)
        result['bound_status_qualified']=bound_qualified
        if result['classification']=='UNKNOWN' and bound_qualified and result['time_lower'] is not None and result['time_lower']>data['T']+margin:
            result.update(classification='INFEAS',exclusion_scope='one_inventory' if mode=='fixed' else 'exact_finite_class_family')
        if model.Status==gp.GRB.INFEASIBLE:result.update(classification='TIME_INDEPENDENT_INFEAS')
        result['total_seconds']=time.perf_counter()-tick;write(target/'result.json',result);model.dispose()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
