"""Necessary free-fleet handling/geography resource projection.

Every complete route projects to this model; a feasible resource assignment
is not a route. Small-subset tour lower bounds use exact rational shortest
paths of the actual binary distance coefficients, rounded downward once.
"""
from fractions import Fraction as F
from itertools import combinations,permutations
from round143_math import outward
from round157_fleet import build,verify,lift
from round157_inventory import instance,classes
from round157_common import *

def native_quality(model,logfile):
    text=Path(logfile).read_text(encoding='utf-8',errors='replace').lower()
    warning=any(s in text for s in ('numerical trouble','unscaled primal violation','unscaled dual violation'))
    primal=None
    if model.SolCount:
        primal=dict(constraints=model.ConstrVio,bounds=model.BoundVio,integer=model.IntVio)
    return dict(numerical_warning=warning,primal=primal,
                numeric_ok=not warning and (primal is None or max(primal.values())<=1e-5),
                policy='inherited R61 threshold-time quality and log gate')

def travel_bounds(data,active):
    d=[[F(v) for v in row] for row in data['distance']]
    for h in range(data['n']+1):
        for i in range(data['n']+1):
            for j in range(data['n']+1):d[i][j]=min(d[i][j],d[i][h]+d[h][j])
    bounds=[]
    for size in (1,2,3):
        for subset in combinations(active,size):
            bound=min(sum((d[i][j] for i,j in zip((0,)+order,order+(0,))),F(0)) for order in permutations(subset))
            bounds.append(dict(stations=list(subset),exact=str(bound),lower=outward(bound,False)))
    return bounds

def attach(model,z,supports,data,bounds,env,existing=False):
    from round100_gurobi_runtime import gp
    ks=range(len(data['Q']));b=data['initial']
    wkeys=[(k,i,v) for k in ks for i,vs in supports.items() for v in vs
           if v!=b[i] and abs(b[i]-v)<=data['Q'][k]]
    w=model.addVars(wkeys,vtype='B',name='resource_service')
    for i,vs in supports.items():
        for v in vs:
            if v!=b[i]:model.addConstr(gp.quicksum(w[k,i,v] for k in ks if (k,i,v) in w)==z[i,v],
                                      name=f'resource_assign_{i}_{v}')
    s={(k,i):gp.quicksum(w[k,i,v] for v in vs if (k,i,v) in w) for k in ks for i,vs in supports.items()}
    P={k:gp.quicksum(max(0,b[i]-v)*x for (kk,i,v),x in w.items() if kk==k) for k in ks}
    D={k:gp.quicksum(max(0,v-b[i])*x for (kk,i,v),x in w.items() if kk==k) for k in ks}
    safe=(data['n']+1)*max(max(r) for r in data['distance'])+(data['pickup']+data['drop'])*sum(b[1:])
    t=model.addVar(lb=0,ub=data['T'] if existing else safe,name='resource_Tstar')
    for k in ks:
        model.addConstr(P[k]>=D[k],name=f'resource_return_nonnegative_{k}')
        model.addConstr(P[k]-D[k]<=data['Q'][k],name=f'resource_return_capacity_{k}')
        handling=(data['pickup']+data['drop'])*P[k]
        model.addConstr(t>=handling,name=f'resource_handling_{k}')
        for no,row in enumerate(bounds):
            ids=row['stations'];lb=row['lower']
            model.addConstr(t>=handling+lb*(gp.quicksum(s[k,i] for i in ids)-len(ids)+1),
                            name=f'resource_subset_{k}_{no}')
    model.update()
    return dict(z=z,w=w,s=s,P=P,D=D,t=t,supports=supports,bounds=bounds)

def fixed_model(data,supports,groups,env,bounds):
    from round100_gurobi_runtime import gp
    model=gp.Model(env=env);model.ModelName='R157_necessary_fleet_resource'
    z=model.addVars([(i,v) for i,vs in supports.items() for v in vs],vtype='B',name='resource_select')
    for i,vs in supports.items():model.addConstr(gp.quicksum(z[i,v] for v in vs)==1,name=f'resource_one_{i}')
    if groups:
        for no,group in enumerate(groups):
            for v,count in group['counts'].items():
                v=int(v);model.addConstr(gp.quicksum(z[i,v] for i in group['stations'] if (i,v) in z)==count,
                                        name=f'resource_count_{no}_{v}')
    ref=attach(model,z,supports,data,bounds,env)
    model.setObjective(ref['t']);model.update()
    return model,ref

def resource_lift(data,ref,witness):
    checked=verify(data,witness);Y=checked['Y'];point={v.VarName:0. for group in ('z','w') for v in ref[group].values()}
    for i,vs in ref['supports'].items():point[ref['z'][i,Y[i-1]].VarName]=1.
    for route in witness['routes']:
        k=route['vehicle']
        for i in route['nodes'][1:-1]:point[ref['w'][k,i,Y[i-1]].VarName]=1.
    point[ref['t'].VarName]=checked['maximum_duration']
    return point

def run(role,rank,mode,label,nodes=65536,cap=3600):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_families.json')[role];c=source['candidates'][int(rank)-1]
    data=instance(source['panel']);members=[c['Y']] if mode=='fixed' else c['members']
    supports={i:sorted({v[i-1] for v in members}) for i in range(1,data['n']+1)}
    active=[i for i,vs in supports.items() if any(v!=data['initial'][i] for v in vs)]
    target=OUT/'resource'/label;target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    bounds=travel_bounds(data,active);write(target/'travel_bounds.json',bounds)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        m,ref=fixed_model(data,supports,classes(source['scope'],c['Y']) if mode=='family' else None,env,bounds)
        m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
        m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap);m.Params.DualReductions=0;m.Params.MIPFocus=3
        m.Params.LogFile=str(target/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
        m.write(str(target/'model.mps'))
        write(target/'condition.json',dict(role=role,rank=int(rank),mode=mode,members=members,panel=source['panel'],
            model_SHA=sha(target/'model.mps'),bounds_SHA=sha(target/'travel_bounds.json'),source_SHA=sha(__file__),
            physical_projection_is_necessary_only=True,maximum_subset_cardinality=3,
            exact_rational_shortest_path=True,rounding='lower_coefficients_downward',
            Seed=0,Threads=1,NodeLimit=int(nodes),TimeLimit=float(cap),MIPFocus=3))
        stop=[False];relaxation_stop=[False];margin=1e-5*max(1,data['T'])
        def observe(model,where):
            if where==gp.GRB.Callback.MIP:
                lb=model.cbGet(gp.GRB.Callback.MIP_OBJBND)
                if data['T']+margin<lb<gp.GRB.INFINITY:stop[0]=True;model.terminate()
                elif model.cbGet(gp.GRB.Callback.MIP_OBJBST)<=data['T']-margin:
                    relaxation_stop[0]=True;model.terminate()
        m.optimize(observe)
        lb=m.ObjBound if abs(m.ObjBound)<gp.GRB.INFINITY else None
        ub=m.ObjVal if m.SolCount else None
        quality=native_quality(m,target/'native.log')
        qualified_status=quality['numeric_ok'] and (m.Status in (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT,gp.GRB.TIME_LIMIT,gp.GRB.WORK_LIMIT) or (m.Status==gp.GRB.INTERRUPTED and (stop[0] or relaxation_stop[0])))
        result=dict(role=role,rank=int(rank),mode=mode,status=m.Status,SolCount=m.SolCount,
            NodeCount=m.NodeCount,Work=m.Work,Runtime=m.Runtime,IterCount=m.IterCount,
            required_time_lower=lb,resource_relaxation_upper=ub,
            classification='RESOURCE_INFEAS' if qualified_status and lb is not None and lb>data['T']+margin else 'RESOURCE_UNRESOLVED',
            physical_U=None,physical_L_change=0.,no_route_claim=True,original_T=data['T'],margin=margin,
            bound_stop=stop[0],necessary_relaxation_feasible_stop=relaxation_stop[0],
            resource_relaxation_fits_original_T=quality['numeric_ok'] and ub is not None and ub<=data['T']-margin,
            bound_status_qualified=qualified_status,numerical_quality=quality,canonical_SHA=sha(target/'model.mps'),condition_SHA=sha(target/'condition.json'),
            NumVars=m.NumVars,NumConstrs=m.NumConstrs,NumNZs=m.NumNZs,
            total_seconds=time.perf_counter()-tick)
        if m.Status==gp.GRB.INFEASIBLE and quality['numeric_ok']:result.update(classification='RESOURCE_INFEAS',time_independent_resource_infeasible=True)
        if m.SolCount:save_gz(target/'solution.json.gz',{v.VarName:v.X for v in m.getVars()})
        write(target/'result.json',result);m.dispose()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
