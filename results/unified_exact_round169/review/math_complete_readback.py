"""Independent final mathematical readback. No H or optimizer is executed.

Uses the separate reviewer Fraction/physical implementation, actual Start
vectors and LP objective text, and an independently computed one-dimensional
envelope of the audit's numerically qualified original-objective scoped bounds.
No producer, solver API or complete-audit adapter is imported/executed.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import csv, hashlib, json, math, re, time, zipfile
import math_readback as independent

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
R169=OUT.parent
TOL=1e-7
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(p):
    p=Path(p);return dict(path=p.relative_to(ROOT).as_posix(),SHA256=sha(p),bytes=p.stat().st_size)
def canonical(routes):
    return sorted((r['vehicle'],tuple(r['nodes']),tuple(sorted((o['station'],o['pickup'],o['drop']) for o in r['operations']))) for r in routes)

def bound_envelope(proofs,initial_U,n):
    # F=G+lambda P>=G. Above the initial G cap, this supplies a lower at least
    # initial_U. Within a proof interval, dropping its cutoff relaxes its bound
    # to min(L,cutoff). Piecewise maximum followed by minimum covers the whole G
    # range. This recomputes the cover independently of the adapter's tree code.
    upper=min(initial_U,(n-1)/n)
    knots=sorted({0.,upper}|{max(0.,min(upper,p[k])) for p in proofs for k in ['lo','hi']})
    pieces=[]
    for lo,hi in zip(knots,knots[1:]):
        if hi<=lo:continue
        mid=(lo+hi)/2
        eligible=[p for p in proofs if p['lo']<=mid<=p['hi']]
        assert eligible,('uncovered G interval',lo,hi)
        value=max([lo]+[min(p['L'],p['cutoff']) for p in eligible])
        pieces.append(dict(lo=lo,hi=hi,L=value,calls=sorted({p['call'] for p in eligible})))
    assert pieces
    lower=min([x['L'] for x in pieces]+([upper] if upper<(n-1)/n else []))
    return dict(L=lower,pieces=pieces,outside_G_cap_lower=upper,
        scope='combination of inherited qualified numerical bounds; not a rational Native certificate')

def main():
    started=time.perf_counter();rows=read(R169/'complete_arms.json')['rows']
    roles={p['id']:p for p in read(R169/'h_panel_frozen.json')['roles'][:6]}
    matrix=read(R169/'matrix_execution_frozen.json')['positions']
    prior=read(OUT/'math_review_initial.json')
    initial_code={x['path']:x['SHA256'] for x in prior['file_bindings'] if x['path'].startswith(('src/','include/'))}
    assert all(sha(ROOT/p)==h for p,h in initial_code.items())
    assert len(rows)==len(matrix)==18
    result=[];unique_models={};total_calls=lp_calls=mip_calls=0
    for row in rows:
        p=roles[row['role']];a=independent.instance(p);d=R169/'complete_raw'/row['run_id']
        raw=read(ROOT/row['raw_result']);audit=read(ROOT/row['audit_path'])
        position=next(x for x in matrix if x['position']==row['position'])
        assert audit['passed'] and audit['Optimize_run_by_reviewer']==0
        assert (audit['role'],audit['research_arm'])==(row['role'],row['arm'])
        argv=read(d/'invocation.json')['argv']
        assert row['lambda_value']==p['lambda']==float(argv[argv.index('--lambda')+1])
        assert raw['route_time_limit_seconds']==p['T_seconds']
        assert row['input_SHA256']==p['input_sha256']
        final,G,P=independent.physical(p,a,raw['routes']);F=G+independent.rat(p['lambda'])*P
        assert all(abs(float(v)-row[k])<1e-12 for v,k in [(G,'G'),(P,'P'),(F,'U')])
        assert abs(raw['objective']-float(F))<1e-12 and abs(raw['upper_bound']-float(F))<1e-12
        s=read(d/'primal/selection.json');path=d/'primal'/s['selected'];meta=read(path/'path.json')
        start_fleet=read(path/'fleet.json')['routes'];start_physical,sg,sp=independent.physical(p,a,start_fleet)
        start_F=sg+independent.rat(p['lambda'])*sp
        assert abs(float(start_F)-row['initial_U'])<1e-12
        assert abs(float(start_F)-raw['initial_heuristic_UB'])<1e-12
        assert s['selected']==row['selected_H']==audit['full_paid_H']['selection']['selected']
        assert canonical(read(d/'external/initial_witness.json')['routes'])==canonical(start_fleet)
        assert audit['full_paid_H']['complete_arm_initialization']
        identity=read(d/'journal/event_1.json')
        assert identity['kind']=='identity' and identity['lambda']==p['lambda'] and identity['input_sha256']==p['input_sha256']
        assert (identity['V'],identity['M'],identity['T'],identity['pickup_seconds'],identity['drop_seconds'])==(p['V'],p['M'],p['T_seconds'],60,60)
        call_records={}
        for fact in audit['models']:
            call_id=fact['call'];m=ROOT/fact['model']['path'];assert sha(m)==fact['model']['SHA']
            assert fact['scope']['true_G_cap_floor_checked'] and fact['scope']['metadata_scope_is_actual_model_scope']
            assert not fact['no_improver_shortcut_check']['model_scope_issue']
            with m.open(encoding='utf-8') as stream:
                objective=next(line.strip() for line in stream if line.lstrip().startswith('obj:'))
            assert objective.startswith('obj: G + ')
            coeffs={int(i):float(c) for c,i in re.findall(r'\+\s+([-+0-9.eE]+)\s+e_(\d+)\b',objective)}
            assert set(coeffs)==set(range(1,a['n']+1))
            assert all(coeffs[i]==p['lambda']*a['weights'][i] for i in coeffs)
            unique_models[str(m)]=sha(m)
            call_records[call_id]=dict(model_SHA256=sha(m),scope=fact['scope'],solve_kind=fact['solve_kind'])
        assert len(call_records)==row['actual_Optimize']==audit['actual_Optimize']
        quality=audit['actual_native_quality']['quality'];assert len(quality)==len(call_records)
        assert all(q['sufficient'] and not q['violated_attributes'] and q['optimize_return_code']==0 for q in quality)
        assert all(q['native_status'] in [2,3,9,11,15] for q in quality)
        starts=[]
        for check in audit['Start_checks']:
            st=ROOT/check['start_path'];sv=read(st)
            assert sha(st)==check['start_sha256'] and check['maximum_absolute_residual']<=TOL
            assert sv['mapping_complete'] and sv['rows_valid'] and sv['objective_valid'] and sv['readback_valid'] and sv['submitted']
            vector=st.with_name(st.name.replace('.start.json','.start.values.csv'))
            with vector.open(encoding='utf-8-sig',newline='') as stream:
                vr=list(csv.DictReader(stream))
            values={r['variable']:float(r['value']) for r in vr}
            assert len(values)==len(vr)==check['columns']
            assert all(float(r['value'])==float(r['readback']) for r in vr)
            assert all(abs(values['r_'+str(i)]-start_physical['Y'][i]/a['target'][i])<1e-12 for i in range(1,a['n']+1))
            assert all(abs(values['e_'+str(i)]-abs(start_physical['Y'][i]/a['target'][i]-1))<1e-12 for i in range(1,a['n']+1))
            objective=values['G']+math.fsum(p['lambda']*a['weights'][i]*values['e_'+str(i)] for i in range(1,a['n']+1))
            assert abs(values['G']-float(sg))<1e-12 and abs(objective-float(start_F))<1e-12
            assert abs(check['objective']-objective)<1e-12
            starts.append(dict(path=st.relative_to(ROOT).as_posix(),vector_SHA256=sha(vector),
                original_objective=objective,max_row_residual=check['maximum_absolute_residual'],selected_H=s['selected']))
        assert starts
        cover=audit['qualified_cover'];assert cover['complete_coverage']
        for proof in cover['scoped_proofs']:
            assert proof['call'] in call_records and all(math.isfinite(proof[k]) for k in ['lo','hi','L','cutoff'])
            assert proof['L']>=0 and proof['lo']>=0 and proof['hi']>=proof['lo'] and proof['cutoff']<=row['initial_U']+TOL
            event=read(d/f"journal/event_{proof['sequence']}.json")
            assert event['call']==proof['call']
        envelope=bound_envelope(cover['scoped_proofs'],row['initial_U'],a['n'])
        assert abs(envelope['L']-row['L'])<TOL and abs(cover['L']-row['L'])<1e-14
        assert row['L']<=float(F)+TOL
        certificate=cover['all_relevant_closed'] and float(F)-row['L']<=TOL
        assert certificate==row['certificate']==raw['strict_certified_original_problem']
        assert certificate==(a['n']==20)
        for key in ['root_coverage_valid','parent_child_coverage_valid','all_leaf_bounds_valid','leaf_bounds_monotone','global_bound_monotone','feasibility_consistency_gate']:
            assert raw['external_gini_tree_'+key] is True
        total_calls+=row['actual_Optimize'];lp_calls+=row['LP'];mip_calls+=row['MIP']
        result.append(dict(position=row['position'],role=row['role'],arm=row['arm'],raw_result=binding(ROOT/row['raw_result']),
            audit=binding(ROOT/row['audit_path']),final_physical=final,initial_physical=start_physical,
            U_error=float(F)-row['U'],selected_H=s['selected'],Start_checks=starts,qualified_L=row['L'],
            independent_interval_envelope=envelope,certificate=certificate,
            certificate_scope='original fixed-lambda global problem under inherited numerical qualification',
            actual_calls=len(call_records),actual_models=call_records))
    assert (total_calls,lp_calls,mip_calls)==(93,66,27)
    pool=[]
    for name in roles:
        r={x['arm']:x for x in result if x['role']==name}
        raw={x['arm']:x for x in rows if x['role']==name}
        assert raw['M']['initial_U']<=raw['B']['initial_U'] and raw['C']['initial_U']<=raw['B']['initial_U']
        pool.append(dict(role=name,initial_B=raw['B']['initial_U'],initial_M=raw['M']['initial_U'],initial_C=raw['C']['initial_U'],
            C_minus_B_U=raw['C']['U']-raw['B']['U'],C_minus_M_U=raw['C']['U']-raw['M']['U'],
            C_minus_B_L=raw['C']['L']-raw['B']['L'],C_minus_M_L=raw['C']['L']-raw['M']['L']))
    outcome=dict(UTC=datetime.now(timezone.utc).isoformat(),schema='round169-independent-final-mathematics-readback-v1',
        H_or_Optimize_executed=0,final_fleets_recomputed=18,selected_Start_fleets_recomputed=18,
        actual_calls_with_original_lambda_LP_objective_checked=total_calls,LP=lp_calls,MIP=mip_calls,
        unique_actual_LP_files=len(unique_models),all_checks_PASS=True,certificate_count=sum(r['certificate'] for r in result),
        original_exact_code_hashes_unchanged_from_initial_review=True,pool_inclusion_checks=pool,rows=result,
        initial_35_H_review_not_rerun=True,seconds=time.perf_counter()-started)
    target=OUT/'math_complete_readback.json';target.write_text(json.dumps(outcome,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in outcome.items() if k not in ['rows','pool_inclusion_checks']},indent=2))

if __name__=='__main__':main()
