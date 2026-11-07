"""Route an accepted resource assignment as a heuristic upper attempt only.

Infeasible/unknown individual vehicle subproblems never exclude a stock or
family. A full assembled original-T fleet is independently checked.
"""
from round157_fleet import build,decode,verify
from round157_inventory import instance,value
from round107_reader import physical
from round143_math import outward
from round157_common import *

def run(role,label,nodes=4096,cap=300):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_sources.json')[role];data=instance(source['panel'])
    origin=OUT/'review'/f'{label}_full_point';point=read(origin/'result.json')
    assert point['PASS'] and point['role']==role
    target=OUT/'completion'/label;target.mkdir(parents=True,exist_ok=False);tick=time.perf_counter()
    Y=point['Y'];assignment={int(k):v for k,v in point['assignment'].items()};calls=[];witness=dict(routes=[])
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        for k,ids in assignment.items():
            if not ids:continue
            local=dict(data,Q=[data['Q'][k]])
            localY=[Y[i-1] if i in ids else data['initial'][i] for i in range(1,data['n']+1)]
            m,ref=build(local,{i:[v] for i,v in enumerate(localY,1)},env)
            folder=target/f'car_{k}';folder.mkdir();m.Params.Seed=0;m.Params.Threads=1
            m.Params.MIPFocus=1;m.Params.SolutionLimit=1;m.Params.NodeLimit=int(nodes);m.Params.TimeLimit=float(cap)
            m.Params.DualReductions=0;m.Params.MIPGap=0;m.Params.MIPGapAbs=0
            m.Params.LogFile=str(folder/'native.log');m.Params.OutputFlag=1;m.Params.LogToConsole=0
            m.write(str(folder/'model.mps'));m.optimize()
            row=dict(vehicle=k,status=m.Status,SolCount=m.SolCount,NodeCount=m.NodeCount,Work=m.Work,Runtime=m.Runtime,
                     model_SHA=sha(folder/'model.mps'),assignment_fixed_for_upper_only=True,no_stock_exclusion=True)
            if m.SolCount:
                localw,check=decode(local,ref);assert check['original_T_feasible'] and check['Y']==localY
                for route in localw['routes']:
                    route['vehicle']=k;witness['routes'].append(route)
                write(folder/'witness.json',localw);row['classification']='FEASIBLE_CAR_ROUTE'
            else:row['classification']='NO_ROUTE_FROM_THIS_ASSIGNMENT'
            calls.append(row);write(folder/'result.json',row);m.dispose()
            if not row['SolCount']:break
    result=dict(UTC=utc(),role=role,calls=calls,physical_U=None,classification='NO_FULL_ROUTE_FROM_THIS_ASSIGNMENT',
                failed_template_is_not_inventory_infeasibility=True,total_seconds=time.perf_counter()-tick,
                source_point_SHA=sha(origin/'result.json'),source_SHA=sha(__file__))
    if len(witness['routes'])==sum(bool(ids) for ids in assignment.values()):
        check=verify(data,witness);assert check['original_T_feasible'] and check['Y']==Y
        witness['objective']=check['J'];independent=physical(ROOT,source['panel'],witness)
        val=value(source['scope'],Y);assert val['feasible']
        write(target/'witness.json',witness);write(target/'physical_check.json',dict(check,independent_R107=independent))
        result.update(classification='ORIGINAL_T_FULL_FLEET_FEAS',physical_U=outward(val['phi'],True),
                      maximum_duration=check['maximum_duration'],witness_SHA=sha(target/'witness.json'))
    write(target/'result.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
