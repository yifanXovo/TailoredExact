"""Separate saved-matrix and exact arithmetic readback; no new research solve."""
from fractions import Fraction as F
from round157_inventory import instance,value,family
from round157_resource import travel_bounds
from round157_family_floor import inventory_point
from round157_floor import attach
from round153_pricing import Oracle
from round143_lp import residual,semantics
from round158_resource import arithmetic
from round158_common import *

def full_lift(oracle,ref,checked,data):
    point,_=inventory_point(oracle,checked['Y'],[]);Y=checked['Y']
    for key,ids in checked['assignment'].items():
        k=int(key)
        for i in ids:
            point[ref['service'][k,i,Y[i-1]].VarName]=1.
            point[ref['s'][k,i].VarName]=1.
        point[ref['P'][k].VarName]=sum(max(0,data['initial'][i]-Y[i-1]) for i in ids)
        point[ref['D'][k].VarName]=sum(max(0,Y[i-1]-data['initial'][i]) for i in ids)
    return point

def run(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    folder=OUT/'resource'/label;condition=read(folder/'condition.json');result=read(folder/'result.json')
    source=read(OLD157/'inventory_sources.json')[condition['role']];scope=source['scope'];data=instance(source['panel'])
    assert condition['scope']==scope and sha(folder/'model.mps')==condition['model_SHA']==result['model_SHA']
    candidate=read(OUT/'candidates.json')[condition['role']]
    assert family(scope,candidate['Y'])==condition['members']
    for member in condition['members']:assert str(value(scope,member)['phi'])==candidate['J_exact']
    bounds=read(folder/'travel_bounds.json');assert bounds==travel_bounds(data,sorted({i for Y in condition['members'] for i,y in enumerate(Y,1) if y!=data['initial'][i]}))
    target=OUT/'review'/f'{label}_readback';target.mkdir(parents=True,exist_ok=False)
    records=[];upper=None;accepted=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'model.mps'),env=env) as saved:
            paths=sorted(folder.glob('incumbent_*.json.gz'))+list(folder.glob('solution.json.gz'))
            for path in paths:
                point=load_gz(path);q=residual(saved,point)
                integer=max([abs(point[v.VarName]-round(point[v.VarName])) for v in saved.getVars() if v.VType!='C']+[0.])
                checked=arithmetic(data,scope,condition['members'],point,bounds)
                matrix_ok=max(q['constraints'],q['bounds'])<=1e-5 and integer<=1e-5
                records.append(dict(path=path.name,SHA256=sha(path),matrix=q,integer=integer,
                    original_T_resource_feasible=checked['original_T_resource_feasible'],required_time=checked['required_time']))
                if matrix_ok and checked['original_T_resource_feasible'] and (upper is None or checked['J']<upper):
                    upper=checked['J'];accepted=checked
        if accepted:
            o=Oracle(scope,env,old_joint=True);allbounds=travel_bounds(data,list(range(1,data['n']+1)))
            ref=attach(o,data,allbounds);point=full_lift(o,ref,accepted,data)
            q=residual(o.model,point);assert max(q['constraints'],q['bounds'])<=1e-7,q
            o.model.write(str(target/'full_resource.mps'));save_gz(target/'full_point.json.gz',point)
            with gp.read(str(target/'full_resource.mps'),env=env) as back:
                assert semantics(back)==semantics(o.model)
                qb=residual(back,point);assert max(qb['constraints'],qb['bounds'])<=1e-7
            write(target/'accepted.json',dict(accepted,full_original_scope=True,full_matrix=q,
                model_SHA=sha(target/'full_resource.mps'),point_SHA=sha(target/'full_point.json.gz')))
            o.close()
    assert upper==result['valid_resource_upper'],(upper,result)
    write(target/'result.json',dict(UTC=utc(),PASS=True,Optimize=0,role=condition['role'],points=records,
        U_R=upper,physical_U=None,full_inventory_resource_lift=accepted is not None,
        source_result_SHA=sha(folder/'result.json'),review='Same agent separate exact arithmetic and saved full-matrix readback'))
    print(json.dumps(dict(label=label,PASS=True,U_R=upper,points=len(records))),flush=True)

if __name__=='__main__':run(*sys.argv[1:])
