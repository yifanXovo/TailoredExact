"""Lift one accepted family resource assignment into the full inventory model.

This can certify an upper for that necessary relaxation. Only a separately
verified full original-T route can become a physical upper.
"""
import re
from fractions import Fraction as F
from itertools import combinations
from round153_pricing import Oracle
from round157_floor import objective,attach,retain_known_lower
from round157_resource import travel_bounds
from round157_inventory import instance,value
from round157_fleet import verify
from round107_reader import physical
from round143_lp import residual
from round143_math import outward
from round157_common import *

def run(role,label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    source=read(OUT/'inventory_sources.json')[role];scope=source['scope'];data=instance(source['panel'])
    folder=OUT/'resource'/label;condition=read(folder/'condition.json');result=read(folder/'result.json')
    assert condition['role']==role and result['SolCount'] and result['numerical_quality']['numeric_ok']
    assert result['resource_relaxation_upper']<=data['T']-result['margin']
    old=load_gz(folder/'solution.json.gz');members=condition['members']
    supports={i:sorted({Y[i-1] for Y in members}) for i in range(1,data['n']+1)}
    Y=[max(vs,key=lambda v:old[f'resource_select[{i},{v}]']) for i,vs in supports.items()]
    assert Y in members
    assignment={k:[] for k in range(len(data['Q']))}
    pattern=re.compile(r'resource_service\[(\d+),(\d+),(\d+)\]')
    for name,x in old.items():
        match=pattern.fullmatch(name)
        if match and x>.5:
            k,i,v=map(int,match.groups());assert v==Y[i-1] and v!=data['initial'][i]
            assignment[k].append(i)
    visited=[i for ids in assignment.values() for i in ids]
    assert len(visited)==len(set(visited)) and set(visited)=={i for i,v in enumerate(Y,1) if v!=data['initial'][i]}
    val=value(scope,Y);assert val['feasible'];target=OUT/'review'/f'{label}_full_point';target.mkdir(parents=True,exist_ok=False)
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        o=Oracle(scope,env,old_joint=True);objective(o);bounds=travel_bounds(data,list(range(1,data['n']+1)))
        ref=attach(o,data,bounds)
        retain_known_lower(o,source['lower']);p={v.VarName:0. for v in o.model.getVars()};t=1/val['S']
        for s,y in zip(scope['stations'],Y):
            i=s['i'];p[f'x[{i},{y}]']=1.;p[f'w[{i},{y}]']=float(t)
            p[f'z[{i}]']=float(t*y);p[f'r[{i}]']=float(F(s['c'])*t*y)
        p['t']=float(t);p['q']=float(val['G'])
        for a,b in combinations(scope['stations'],2):
            i,j=a['i'],b['i'];p[f'a[{i},{j}]']=abs(p[f'r[{i}]']-p[f'r[{j}]'])
        for k,ids in assignment.items():
            pickup=drop=0
            for i in ids:
                p[ref['service'][k,i,Y[i-1]].VarName]=1.;p[ref['s'][k,i].VarName]=1.
                pickup+=max(0,data['initial'][i]-Y[i-1]);drop+=max(0,Y[i-1]-data['initial'][i])
            p[ref['P'][k].VarName]=pickup;p[ref['D'][k].VarName]=drop
            assert 0<=pickup-drop<=data['Q'][k]
            exact_time=F(data['pickup']+data['drop'])*pickup
            longest=max([F(0)]+[F(row['lower']) for row in bounds if set(row['stations'])<=set(ids)])
            assert exact_time+longest<=F(data['T'])
        quality=residual(o.model,p);assert quality['constraints']<=1e-7 and quality['bounds']<=1e-7,quality
        o.model.write(str(target/'full_model.mps'));save_gz(target/'point.json.gz',p);o.close()
    # A deterministic load-feasible order is only an upper attempt. Its
    # failure or excessive duration cannot exclude the inventory/family.
    witness=dict(routes=[]);construction_failed=False
    for k,ids in assignment.items():
        todo=set(ids);nodes=[0];ops=[];load=0
        while todo:
            legal=[i for i in todo if 0<=load+data['initial'][i]-Y[i-1]<=data['Q'][k]]
            if not legal:construction_failed=True;break
            i=min(legal,key=lambda i:(data['distance'][nodes[-1]][i],i));delta=data['initial'][i]-Y[i-1]
            load+=delta;nodes.append(i);ops.append(dict(station=i,pickup=max(0,delta),drop=max(0,-delta)));todo.remove(i)
        if construction_failed:break
        if ops:witness['routes'].append(dict(vehicle=k,nodes=nodes+[0],operations=ops))
    outcome=dict(UTC=utc(),PASS=True,role=role,Y=Y,assignment=assignment,J_exact=str(val['phi']),
        new_global_resource_inventory_upper=outward(val['phi'],True),quality=quality,
        source_result_SHA=sha(folder/'result.json'),model_SHA=sha(target/'full_model.mps'),Optimize=0,
        physical_U=None,greedy_order_failed=construction_failed,source_SHA=sha(__file__))
    if not construction_failed:
        check=verify(data,witness);witness['objective']=check['J'];assert check['Y']==Y
        safe=(data['n']+1)*max(max(v) for v in data['distance'])+(data['pickup']+data['drop'])*sum(data['initial'][1:])
        independent=physical(ROOT,dict(source['panel'],T_seconds=safe),witness)
        outcome.update(true_required_time_upper=check['maximum_duration'],original_T_feasible=check['original_T_feasible'],
                       independent_non_time_check=independent)
        write(target/'greedy_witness.json',witness)
        if check['original_T_feasible']:
            physical(ROOT,source['panel'],witness);outcome['physical_U']=outward(val['phi'],True)
    write(target/'result.json',outcome);print(json.dumps(outcome),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
