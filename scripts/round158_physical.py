"""Free-fleet physical completion of one prespecified checked resource stock.

Reuse the qualified R157 exact arc-load-flow/MTZ fleet. Resource assignment
is a partial start only. Common-envelope time and rounded budget rows are
necessary for every lawful original-T route. FEAS needs raw physical checks;
an INFEAS excludes only the declared stock, never an objective level.
"""
from fractions import Fraction as F
from round157_fleet import build,decode,verify,lift
from round157_inventory import instance,value
from round157_resource import travel_bounds,native_quality
from round158_level import envelope,budgets,coefficient_package
from round107_reader import physical
from round143_lp import residual,semantics
from round143_math import outward
from round158_common import *

def add_budgets(model,ref,data,plan):
    from round100_gurobi_runtime import gp
    for k in range(len(data['Q'])):
        P=gp.quicksum(ref['p'][k,i] for i in ref['active'][k]);model.addConstr(P<=plan['U'],name=f'completion_global_{k}')
        for row in plan['kept']:
            ids=row['stations'];b=row['budget'];visit=gp.quicksum(ref['s'][k,i] for i in ids)
            if b<0:model.addConstr(visit<=len(ids)-1,name=f'completion_forbidden_{k}_{row["index"]}')
            else:model.addConstr(P+(plan['U']-b)*visit<=b+(plan['U']-b)*len(ids),name=f'completion_budget_{k}_{row["index"]}')
    model.update()

def run(role,resource_path,label,nodes=2000000000,cap=21600):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    assert read(OUT/'qualification/physical_v1/result.json')['PASS']
    checked=read(OUT/resource_path);Y=checked['Y'];source=read(OLD157/'inventory_sources.json')[role]
    scope=source['scope'];val=value(scope,Y);assert val['feasible']
    assert F(checked['J_exact'])==val['phi']
    data=instance(source['panel']);actual,package_SHA=coefficient_package(source)
    data=dict(data,distance=actual['distance'])
    modeldata,contract=envelope(data,actual);contract['coefficient_package_SHA']=package_SHA
    supports={i:[y] for i,y in enumerate(Y,1)};active=[i for i,y in enumerate(Y,1) if y!=data['initial'][i]]
    bounds=travel_bounds(modeldata,active);plan=budgets(modeldata,bounds)
    folder=OUT/'physical'/label;folder.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start();m,ref=build(modeldata,supports,env)
        add_budgets(m,ref,modeldata,plan)
        for (i,y),var in ref['z'].items():var.Start=1.
        for (k,i,y),var in ref['w'].items():
            var.Start=float(i in checked['assignment'].get(str(k),checked['assignment'].get(k,[])))
        m.Params.Threads=1;m.Params.Seed=0;m.Params.MIPFocus=1;m.Params.DualReductions=0
        m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap);m.Params.MIPGap=0;m.Params.MIPGapAbs=0
        m.Params.IntFeasTol=1e-6;m.Params.SolutionLimit=1;m.Params.LogFile=str(folder/'native.log')
        m.Params.OutputFlag=1;m.Params.LogToConsole=0
        m.write(str(folder/'model.mps'))
        with gp.read(str(folder/'model.mps'),env=env) as back:assert semantics(back)==semantics(m)
        write(folder/'condition.json',dict(UTC=utc(),role=role,Y=Y,J_exact=str(val['phi']),
            inventory_scope='one checked resource inventory; all vehicle assignment/order/prefix load free',
            assignment_is_start_only=True,no_arc_or_assignment_bounds_fixed=True,original_T=data['T'],contract=contract,
            resource_source=str(resource_path),resource_source_SHA=sha(OUT/resource_path),
            Seed=0,Threads=1,MIPFocus=1,NodeLimit=int(nodes),TimeLimit=float(cap),SolutionLimit=1,
            model_SHA=sha(folder/'model.mps'),rounded_subsets=plan['kept_subsets'],
            strictly_more_travel_load_information_than_resource_projection=True))
        durable=Durable(folder);m.optimize(durable.observe);assert not durable.errors
        q=native_quality(m,folder/'native.log')
        result=dict(UTC=utc(),role=role,Y=Y,J_exact=str(val['phi']),status=m.Status,SolCount=m.SolCount,
            NodeCount=m.NodeCount,Runtime=m.Runtime,Work=m.Work,IterCount=m.IterCount,classification='UNKNOWN',
            physical_U=None,whole_level_exclusion=False,numerical_quality=q,normal_Optimize_return=True,
            graceful_external_stop=durable.stopped,model_SHA=sha(folder/'model.mps'),
            NumVars=m.NumVars,NumConstrs=m.NumConstrs,NumNZs=m.NumNZs)
        if m.SolCount:
            point={v.VarName:v.X for v in m.getVars()};save_gz(folder/'solution.json.gz',point)
            witness,raw=decode(data,ref);quality=residual(m,point);assert raw['Y']==Y
            write(folder/'witness.json',witness);write(folder/'physical_check.json',raw)
            if q['numeric_ok'] and max(quality['constraints'],quality['bounds'])<=1e-5 and raw['original_T_feasible']:
                independent=physical(ROOT,source['panel'],witness)
                result.update(classification='PHYSICAL_FEAS',physical_U=outward(val['phi'],True),
                    maximum_duration=raw['maximum_duration'],independent=independent,witness_SHA=sha(folder/'witness.json'))
            else:result['classification']='RELAXED_TIME_FLEET_POINT_ONLY'
        elif m.Status==gp.GRB.INFEASIBLE and q['numeric_ok']:
            result.update(classification='FIXED_STOCK_PHYSICAL_INFEAS',exclusion_scope='one inventory only')
        result['total_seconds']=time.perf_counter()-tick;write(folder/'result.json',result);m.dispose()
    print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
