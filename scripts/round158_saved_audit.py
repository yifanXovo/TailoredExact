"""Separate finite checks of saved numerical rows, points and completed fees."""
import re
from itertools import combinations
from fractions import Fraction as F
from round143_lp import residual
from round157_inventory import value,instance
from round157_resource import travel_bounds
from round158_common import *

def level(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    from round143_math import outward
    affinity();assert binding()['sha256']==DLL_SHA
    folder=OUT/'level'/label;result=read(folder/'result.json');call=read(folder/'call.json')
    role=call['role'];source=read(OLD157/'inventory_sources.json')[role];scope=source['scope'];data=instance(source['panel'])
    assert call['scope']==scope and call['tau_exact']==result['tau_exact']
    assert sha(folder/'model.mps')==call['model_SHA']==result['model_SHA']
    admission=OUT/call.get('admission_relative','qualification/level_v1/result.json')
    assert sha(admission)==call['admission_SHA']
    if call.get('admission_relative')=='qualification/level_v2/result.json':
        package=read(OUT/'qualification/coefficient_v2'/(source['panel']['input_sha256']+'.json'))
        data=dict(data,distance=package['distance'])
    if 'actual_row_gate_relative' in call:
        gate=OUT/call['actual_row_gate_relative'];assert read(gate)['PASS'] and sha(gate)==call['actual_row_gate_SHA']
    approved=next(r for r in read(admission)['facts'] if r['role']==role and r['variant']==call['variant'])
    assert approved['model_SHA']==call['model_SHA'],'a changed level/matrix needs new cutoff qualification'
    fee=read(OUT/'fees'/('level_'+label)/'receipt.json')
    assert fee['exit_observed'] and fee['exit_code']==0 and not fee['timeout']
    bounds=travel_bounds(data,list(range(1,data['n']+1)));tau=F(call['tau_exact']);records=[];best=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'model.mps'),env=env) as m:
            paths=sorted(folder.glob('incumbent_*.json.gz'))+list(folder.glob('solution.json.gz'))
            for path in paths:
                p=load_gz(path);q=residual(m,p)
                integer=max([abs(p[v.VarName]-round(p[v.VarName])) for v in m.getVars() if v.VType!='C']+[0.])
                assert max(q['constraints'],q['bounds'],integer)<=1e-5
                Y=[]
                for s in scope['stations']:
                    selected=[y for y in s['support'] if abs(p[f'x[{s["i"]},{y}]']-1)<=1e-5]
                    assert len(selected)==1;Y.append(selected[0])
                owners={k:[] for k in range(len(data['Q']))}
                for name,x in p.items():
                    match=re.fullmatch(r'resource_service\[(\d+),(\d+),(\d+)\]',name)
                    if match and x>.5:
                        k,i,y=map(int,match.groups());assert y==Y[i-1] and y!=data['initial'][i]
                        assert abs(y-data['initial'][i])<=data['Q'][k];owners[k].append(i)
                flat=[i for part in owners.values() for i in part]
                assert len(flat)==len(set(flat)) and set(flat)=={i for i,y in enumerate(Y,1) if y!=data['initial'][i]}
                val=value(scope,Y);assert val['feasible'];times=[]
                for k,ids in owners.items():
                    P=sum(max(0,data['initial'][i]-Y[i-1]) for i in ids);D=sum(max(0,Y[i-1]-data['initial'][i]) for i in ids)
                    assert 0<=P-D<=data['Q'][k]
                    ell=max([F(0)]+[F(r['lower']) for r in bounds if set(r['stations'])<=set(ids)])
                    times.append((F(data['pickup'])+F(data['drop']))*P+ell)
                in_level=val['phi']<=tau;fits=max(times)<=F(data['T'])
                record=dict(path=path.name,SHA256=sha(path),matrix=q,integer=integer,J_exact=str(val['phi']),
                    J=outward(val['phi'],True),times_exact=[str(v) for v in times],fits_original_T=fits,true_J_in_level=in_level)
                records.append(record)
                if fits and (best is None or val['phi']<F(best['J_exact'])):
                    # Canonical reconstruction is independent of the returned
                    # continuous auxiliary values, using the decoded integers.
                    canonical={v.VarName:0. for v in m.getVars()};t=1/val['S'];canonical['t']=float(t);canonical['q']=float(val['G'])
                    for s,y in zip(scope['stations'],Y):
                        i=s['i'];canonical[f'x[{i},{y}]']=1.;canonical[f'w[{i},{y}]']=float(t)
                        canonical[f'z[{i}]']=float(t*y);canonical[f'r[{i}]']=float(F(s['c'])*t*y)
                    for a,b in combinations(scope['stations'],2):
                        i,j=a['i'],b['i'];canonical[f'a[{i},{j}]']=abs(canonical[f'r[{i}]']-canonical[f'r[{j}]'])
                    for k,ids in owners.items():
                        for i in ids:
                            canonical[f'resource_service[{k},{i},{Y[i-1]}]']=1.;canonical[f'resource_visit[{k},{i}]']=1.
                        canonical[f'resource_pickup[{k}]']=sum(max(0,data['initial'][i]-Y[i-1]) for i in ids)
                        canonical[f'resource_drop[{k}]']=sum(max(0,Y[i-1]-data['initial'][i]) for i in ids)
                    cq=residual(m,canonical);assert max(cq['constraints'],cq['bounds'])<=1e-7,cq
                    best=dict(Y=Y,assignment=owners,J_exact=str(val['phi']),J=outward(val['phi'],True),true_J_in_level=in_level,
                        vehicles=[dict(vehicle=k,stations=owners[k],required_time_exact=str(times[k]),required_time=float(times[k])) for k in owners],
                        physical_U=None,canonical_quality=cq)
                    save_gz(OUT/'review'/f'{label}_canonical.json.gz',canonical)
    log=(folder/'native.log').read_text(encoding='utf-8',errors='replace')
    if result['level_excluded']:
        assert result['status']==3 and result['SolCount']==0 and result['numerical_quality']['numeric_ok']
        assert re.search(r'(?m)^Model is infeasible\s*$',log) and not (best and best['true_J_in_level'])
        assert F(result['new_lower'])<=tau
    if best:
        assert result['U_R']==best['J'];write(OUT/'review'/f'{label}_accepted.json',best)
    else:assert result['U_R'] is None
    write(OUT/'review'/f'{label}_level.json',dict(UTC=utc(),PASS=True,Optimize=0,role=role,
        complete_scope_matrix_matches_pre_long_qualification=True,source_result_SHA=sha(folder/'result.json'),
        fee_closed=True,classification=result['classification'],level_excluded=result['level_excluded'],
        original_objective_lower=result['new_lower'],U_R=None if best is None else best['J'],physical_U=None,points=records,
        review='Same agent separate saved-matrix identity, integer arithmetic, canonical lift and final-log/fee checks'))
    print(json.dumps(dict(label=label,PASS=True,classification=result['classification'],U_R=None if best is None else best['J'])),flush=True)

def expression():
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    folder=OUT/'level/rx35_raw_quarter';info=read(folder/'mathematics.json');plan=info['budget_plan']
    H=F(info['contract']['H_exact']);h=F(info['contract']['h_exact']);U=plan['U'];count=0;minimum=None
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag',0);env.start()
        with gp.read(str(folder/'model.mps'),env=env) as m:
            for k in range(3):
                row=m.getConstrByName(f'resource_handling_{k}');assert h*U<=F(row.RHS)
                for r in plan['rows']:
                    row=m.getConstrByName(f'resource_subset_{k}_{r["index"]}');e=m.getRow(row)
                    coeff={e.getVar(j).VarName:F(e.getCoeff(j)) for j in range(e.size())}
                    ell=F(r['lower']);ids=r['stations'];b=r['budget']
                    expected={f'resource_pickup[{k}]':h}|{f'resource_visit[{k},{i}]':ell for i in ids}
                    expected={n:a for n,a in expected.items() if a}
                    assert coeff==expected and row.Sense=='<'
                    endpoints=[h*U+ell*(len(ids)-1)]
                    if b>=0:endpoints.append(h*min(b,U)+ell*len(ids))
                    slack=F(row.RHS)-max(endpoints);assert slack>=0,(k,r,slack)
                    minimum=slack if minimum is None else min(minimum,slack);count+=1
    target=OUT/'review/actual_raw_rounding_implication.json'
    write(target,dict(UTC=utc(),PASS=True,Optimize=0,actual_raw_rows=count,
        actual_binary_RHS_rounding_included=True,minimum_endpoint_slack_exact=str(minimum),
        all_new_rounded_budgets_imply_actual_saved_raw_rows=True,
        scope='RX35 exact actual primary-level coefficient package; dominance chains were separately qualified',
        source_model_SHA=sha(folder/'model.mps'),
        qualification_count_note='level_v1 facts.NumNZs was recorded after removing the cutoff for the positive control; actual run NumNZs and saved matrix are authoritative'))
    print(json.dumps(read(target)),flush=True)

def primal(label):
    from round100_gurobi_runtime import gp,binding
    from round150_lp import affinity
    affinity();assert binding()['sha256']==DLL_SHA
    folder=OUT/'primal'/label;result=read(folder/'result.json');record=dict(UTC=utc(),PASS=True,Optimize=0,source_result_SHA=sha(folder/'result.json'))
    if result['U_R'] is not None:
        saved=read(folder/'best_assignment.json');role=result['role'];source=read(OLD157/'inventory_sources.json')[role]
        data=instance(source['panel']);scope=source['scope'];point=load_gz(folder/'full_point.json.gz')
        Y=[]
        for s in scope['stations']:
            chosen=[y for y in s['support'] if abs(point[f'x[{s["i"]},{y}]']-1)<=1e-5]
            assert len(chosen)==1;Y.append(chosen[0])
        owners={k:[] for k in range(len(data['Q']))}
        for name,x in point.items():
            match=re.fullmatch(r'resource_service\[(\d+),(\d+),(\d+)\]',name)
            if match and x>.5:
                k,i,y=map(int,match.groups());assert y==Y[i-1] and y!=data['initial'][i] and abs(y-data['initial'][i])<=data['Q'][k]
                owners[k].append(i)
        flat=[i for part in owners.values() for i in part]
        assert len(flat)==len(set(flat)) and set(flat)=={i for i,y in enumerate(Y,1) if y!=data['initial'][i]}
        val=value(scope,Y);assert val['feasible'] and str(val['phi'])==saved['J_exact']
        assert F(result['U_R'])>=val['phi'] and Y==saved['Y']
        bounds=travel_bounds(data,list(range(1,data['n']+1)));times=[]
        for k,ids in owners.items():
            P=sum(max(0,data['initial'][i]-Y[i-1]) for i in ids);D=sum(max(0,Y[i-1]-data['initial'][i]) for i in ids)
            assert 0<=P-D<=data['Q'][k]
            ell=max([F(0)]+[F(r['lower']) for r in bounds if set(r['stations'])<=set(ids)])
            duration=(F(data['pickup'])+F(data['drop']))*P+ell;assert duration<=F(data['T']);times.append(float(duration))
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start()
            with gp.read(str(folder/'full_resource.mps'),env=env) as m:
                q=residual(m,point);integer=max([abs(point[v.VarName]-round(point[v.VarName])) for v in m.getVars() if v.VType!='C']+[0.])
                assert max(q['constraints'],q['bounds'],integer)<=1e-7
        record.update(U_R=result['U_R'],Y=Y,assignment=owners,J_exact=str(val['phi']),times=times,
            matrix=q,integer=integer,physical_U=None,point_SHA=sha(folder/'full_point.json.gz'))
    write(OUT/'review'/f'{label}_primal.json',record);print(json.dumps(record),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='expression':expression()
    elif sys.argv[1]=='primal':primal(sys.argv[2])
    elif sys.argv[1]=='level':level(sys.argv[2])
    else:raise ValueError(sys.argv[1])
