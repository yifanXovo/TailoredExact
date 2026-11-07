"""Aggregate fleet travel lower from one mandatory-set metric TSP.

Concatenate the real depot tours and shortcut repeated vertices in exact
shortest-path distances. The mandatory-set TSP optimum cannot exceed the
actual fleet's total travel. Its upper is not a physical fleet witness.
"""
from fractions import Fraction as F
from itertools import combinations
from round143_math import outward
from round157_inventory import instance
from round157_common import *

def shortest(data):
    d=[[F(v) for v in row] for row in data['distance']]
    for h in range(data['n']+1):
        for i in range(data['n']+1):
            for j in range(data['n']+1):d[i][j]=min(d[i][j],d[i][h]+d[h][j])
    return d

def parts(nodes,edges):
    adjacency={i:set() for i in nodes}
    for i,j in edges:adjacency[i].add(j);adjacency[j].add(i)
    assert all(len(v)==2 for v in adjacency.values())
    remaining=set(nodes);result=[]
    while remaining:
        stack=[min(remaining)];component=set()
        while stack:
            i=stack.pop()
            if i in component:continue
            component.add(i);stack.extend(adjacency[i]-component)
        result.append(sorted(component));remaining-=component
    return result

def solve(data,mandatory,env,target,node_limit=4096,cap=900,exclude_threshold=None):
    from round100_gurobi_runtime import gp
    target=Path(target);target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    d=shortest(data);nodes=[0]+sorted(mandatory)
    guard=1e-5*max(1,len(data['Q'])*data['T'])
    if len(nodes)<=2:
        exact=F(0) if len(nodes)==1 else d[0][nodes[1]]+d[nodes[1]][0]
        result=dict(lower=outward(exact,False),lower_exact=str(exact),upper=outward(exact,True),
                    Native_Optimize=0,qualified=True,mandatory=mandatory,seconds=time.perf_counter()-tick)
        write(target/'result.json',result);return result
    edges=list(combinations(nodes,2));m=gp.Model(env=env);m.ModelName='R157_mandatory_metric_tour'
    x=m.addVars(edges,vtype='B',name='edge')
    for i in nodes:m.addConstr(gp.quicksum(v for (a,b),v in x.items() if i in (a,b))==2,name=f'degree_{i}')
    costs={e:outward(d[e[0]][e[1]],False) for e in edges}
    m.setObjective(gp.quicksum(costs[e]*v for e,v in x.items()))
    m.Params.Seed=0;m.Params.Threads=1;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
    m.Params.NodeLimit=int(node_limit);m.Params.TimeLimit=float(cap);m.Params.LazyConstraints=1
    m.Params.DualReductions=0;m.Params.MIPFocus=3
    m.Params.LogFile=str(target/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
    m.update();m.write(str(target/'model.mps'))
    write(target/'condition.json',dict(mandatory=mandatory,original_T=data['T'],fleet_size=len(data['Q']),
        costs=[dict(edge=e,exact=str(d[e[0]][e[1]]),lower=costs[e]) for e in edges],
        no_original_T_deletion=True,guard=guard,exclude_threshold=exclude_threshold,
        model_SHA=sha(target/'model.mps'),source_SHA=sha(__file__),Seed=0,Threads=1,
        NodeLimit=int(node_limit),TimeLimit=float(cap),lower_is_on_total_travel=True))
    lazy=[];errors=[];bound_stop=[False]
    def callback(model,where):
        try:
            if where==gp.GRB.Callback.MIPSOL:
                selected=[e for e,v in x.items() if model.cbGetSolution(v)>.5]
                for subset in parts(nodes,selected):
                    if len(subset)==len(nodes):continue
                    model.cbLazy(gp.quicksum(x[a,b] for a,b in combinations(subset,2))<=len(subset)-1)
                    lazy.append(dict(stations=subset,rhs=len(subset)-1))
            elif where==gp.GRB.Callback.MIP and exclude_threshold is not None:
                lb=model.cbGet(gp.GRB.Callback.MIP_OBJBND)
                if exclude_threshold+guard<lb<gp.GRB.INFINITY:
                    bound_stop[0]=True;model.terminate()
        except BaseException as error:
            errors.append(dict(type=type(error).__name__,message=str(error)));model.terminate()
    m.optimize(callback);assert not errors,errors
    qualified=m.Status in (gp.GRB.OPTIMAL,gp.GRB.NODE_LIMIT,gp.GRB.TIME_LIMIT,gp.GRB.WORK_LIMIT) or (m.Status==gp.GRB.INTERRUPTED and bound_stop[0])
    raw=m.ObjBound if abs(m.ObjBound)<gp.GRB.INFINITY else None
    lower=max(0.,math.nextafter(raw-guard,-math.inf)) if qualified and raw is not None else 0.
    result=dict(qualified=qualified,lower=lower,native_lower=raw,numerical_guard=guard,status=m.Status,
        upper=m.ObjVal if m.SolCount else None,SolCount=m.SolCount,NodeCount=m.NodeCount,Work=m.Work,
        Runtime=m.Runtime,Native_Optimize=1,mandatory=mandatory,lazy_rows=len(lazy),bound_stop=bound_stop[0],
        model_SHA=sha(target/'model.mps'),condition_SHA=sha(target/'condition.json'),
        physical_U=None,tour_upper_is_not_fleet_upper=True,seconds=time.perf_counter()-tick)
    if m.SolCount:
        selected=[e for e,v in x.items() if v.X>.5];assert len(parts(nodes,selected))==1
        write(target/'tour.json',dict(edges=selected,cost=m.ObjVal))
    write(target/'lazy_rows.json',lazy);write(target/'result.json',result);m.dispose();return result

def run(role,rank,label,nodes=4096,cap=900):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_families.json')[role];candidate=source['candidates'][int(rank)-1]
    data=instance(source['panel']);members=candidate['members']
    mandatory=[i for i in range(1,data['n']+1) if all(Y[i-1]!=data['initial'][i] for Y in members)]
    pmin=candidate['pickup_range'][0];handling=(data['pickup']+data['drop'])*pmin
    threshold=len(data['Q'])*data['T']-handling
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        result=solve(data,mandatory,env,OUT/'tour'/label,int(nodes),float(cap),threshold)
    result.update(role=role,rank=int(rank),minimum_family_pickup=pmin,minimum_handling=handling,
        aggregate_original_time=len(data['Q'])*data['T'],exclusion_threshold=threshold,
        family_excluded=result['qualified'] and result['lower']+handling>len(data['Q'])*data['T'])
    write(OUT/'tour'/label/'family_result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
