"""Necessary paid postexit audit; original ENS/MB predicates plus isolated P-S."""
import csv, collections, math, time
from pathlib import Path
from round112_common import ROOT, read, sha
import round90_lp_g_g3 as native_runner
import round111_seed_audit as inherited
import round108_reader as core
import round94_lpg_formal_recovery_v3 as scopes
import round94_lpg_contemporary as parameters

last_metrics={}

def start_audit(root,p,d):
    base=d/'native.log.round112.start'
    a=read(str(base)+'.before.matrix.json');b=read(str(base)+'.after.matrix.json')
    assert a==b,'Start changed actual native matrix/domain/objective/name metadata'
    lp=core.lp_model(d/'compact.lp');names=[c[0] for c in a['columns']]
    assert len(names)==len(set(names))==len(lp['order']) and set(names)==set(lp['order'])
    co=dict(lp['objective'][0]);assert a['sense']==1 and a['constant']==lp['objective'][1]
    for name,typ,lo,hi,obj in a['columns']:
        assert lp['types'][name]==typ and lp['bounds'][name]==(lo,hi) and obj==co.get(name,0)
    rows=[]
    for name,sense,rhs,terms in a['rows']:
        merged=collections.defaultdict(float)
        for idx,v in terms:merged[names[idx]]+=v
        rows.append((tuple(sorted((n,v) for n,v in merged.items() if v)),{'<':'<=','>':'>=','=':'='}[sense],rhs))
    assert rows==lp['rows'],'all original row coefficients/order/senses/RHS must match'
    with Path(str(base)+'.values.csv').open(newline='',encoding='utf-8') as f:vectors=list(csv.DictReader(f))
    assert [v['variable'] for v in vectors]==names and len(vectors)==len(a['columns'])
    values={v['variable']:float(v['value']) for v in vectors}
    for v,c in zip(vectors,a['columns']):
        val=values[v['variable']]
        assert math.isfinite(val) and val==float(v['readback']) and v['type']==c[1]
        assert c[2]-1e-7<=val<=c[3]+1e-7
        if c[1] in 'BIN':assert abs(val-round(val))<=1e-7
    maxv=0
    for terms,sense,rhs in rows:
        lhs=sum(v*values[n] for n,v in terms)
        violation=abs(lhs-rhs) if sense=='=' else max(0,lhs-rhs) if sense=='<=' else max(0,rhs-lhs)
        maxv=max(maxv,violation);assert violation<=1e-7
    objective=a['constant']+sum(c[4]*values[c[0]] for c in a['columns'])
    seed=read(d/'result.json.round112.startup.json');physical=core.full_fleet(root,p,seed)
    assert abs(physical['F']-objective)<=1e-7
    receipt=read(str(base)+'.json')
    assert receipt['submitted'] and receipt['submission_count']==1 and receipt['readback_valid'] and receipt['matrix_unchanged']
    assert receipt['columns']==len(names) and receipt['rows_checked']==len(rows)
    return dict(columns=len(names),rows=len(rows),maximum_row_violation=maxv,objective=objective,
        all_native_columns_checked=True,all_original_numeric_rows_checked=True,names_metadata_also_unchanged=True,
        before_SHA=sha(str(base)+'.before.matrix.json'),after_SHA=sha(str(base)+'.after.matrix.json'),vector_SHA=sha(str(base)+'.values.csv'))

def adapter(launch,observations,completion,identity):
    global last_metrics
    tick=time.perf_counter();d=Path(launch['destination']);p=launch['panel'];arm=launch['arm']
    if arm!='P-S':
        audited=inherited.adapter(launch,observations,completion,identity)
        if arm!='P-GRB':
            context=inherited.ArmModels()
            try:
                contracts=[]
                for rec in observations:
                    call=rec['payload']
                    if call['kind']!='call':continue
                    path=Path(call['model_path']);contract,m=context.model_contract(ROOT,p,path,arm)
                    contracts.append(dict(contract,scope=context.model_scope_contract(call,m,p)))
                audited['current_saved_model_contracts']=contracts
            finally:context.clear()
        last_metrics=dict(inherited.last_metrics or {},inclusive_seconds=time.perf_counter()-tick)
        return audited
    assert completion['returncode']==0 and completion['stop_reason']=='normal_return'
    r=read(d/'result.json');assert r['algorithm_preset']=='research-round112-self-paid-ens-start-original-compact'
    assert '--round112-ens-start-compact' in launch['command'] and r['gurobi_hga_start_requested'] is False
    assert not any(s in r['status'].lower() for s in ('error','failed','invalid'))
    audited=native_runner.evidence.audit(ROOT,p,observations,identity['candidate_binary_sha256'])
    calls=[q['payload'] for q in observations if q['payload']['kind']=='call']
    assert len(calls)<=1 and all(c['full_original'] and c['native_preconditions'] for c in calls)
    physical=core.full_fleet(ROOT,p,r);seed=read(d/'result.json.round112.startup.json');own=core.full_fleet(ROOT,p,seed)
    assert physical['F']<=own['F']+1e-7 and math.isfinite(physical['F'])
    U=min([physical['F']]+[w['F'] for w in audited['witnesses']]);L=audited['LB']
    damage=[]
    if calls:
        assert sha(d/'compact.lp')==p['reference']['canonical_sha256']
        assert r['gurobi_model_fingerprint']==p['reference']['fingerprint'] and r['gurobi_optimize_count']==1
        assert r['gurobi_lifecycle_valid'] and r['gurobi_native_domain_audit_passed']
        audited['Start']=start_audit(ROOT,p,d)
        audited['parameter_readback']=parameters.parameter_readback(r,require_call=True,arm='P-GRB')
        assert all(c['settings']==dict(read_return_code=0,Threads=1,Seed=0,Presolve=-1,MIPGap=0,MIPGapAbs=0,FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6) for c in calls)
        if r['gurobi_obj_bound_c_available']:
            nativeL=r['gurobi_obj_bound_c'];assert math.isfinite(nativeL)
            if nativeL>U+1e-7:damage.append('full_original_native_bound_exceeds_own_physical_UB');L=0
            else:L=max(L,nativeL)
        cert=bool(r['strict_certified_original_problem'] and not damage and U-L<=1e-7)
    else:
        assert r['gurobi_optimize_count']==0 and r['status'] in ('startup_zero','startup_deadline')
        cert=r['status']=='startup_zero';assert not cert or own['F']<=1e-7
        L=0
    audited.update(passed=True,own_startup=own,final_physical_verification=physical,numerical_damage=damage,
        native_scope_adapter=dict(native_calls=len(calls),full_original=True),normal_result_certificate=cert,
        endpoint=dict(U=U,L=L,gap=U-L,certificate=cert,status=r['status'],source='own_H_and_original_compact'))
    last_metrics=dict(inclusive_seconds=time.perf_counter()-tick)
    return audited
