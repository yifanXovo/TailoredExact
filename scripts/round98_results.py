"""Compact durable run/pair/cost extraction, no native calls or optimization."""
import csv,json,math,sys
from round98_common import *

def csv_write(path,rows):
    assert rows
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def extract(label,campaigns):
    target=OUT/label;target.mkdir(exist_ok=False);rows=[];cost=[]
    # Immutable v1 prefix is retired because of the result-label defect. Its
    # separate offline physics audit cannot turn it into a formal time panel.
    retired=read(OUT/'qualification/v1_paid_prefix_offline_audit.json')['records']
    for r in retired:
        cost.append(dict(category='retired_paid_qualification',label='development01/F2/'+r['arm'],experimental_starts=1,
            optimizer_calls=r['optimizer_calls'],outer_seconds=r['outer_seconds'],
            failed=r['arm']=='R2',stop_reason='normal_return_original_identity_audit_failed' if r['arm']=='R2' else 'normal_return_retired_prefix'))
    for name in campaigns:
        camp=OUT/name;identity=read(camp/'identity.json')
        records=[json.loads(s) for s in (camp/'summary.jsonl').read_text().splitlines()]
        for r in records:
            launch=identity['launches'][r['number']-1];d=Path(r['destination']);audit=read(d/'audit.json')
            original_audit_passed=r['audit_passed'];recovery_path=None
            if name=='development02' and r['number']==14:
                recovery_path=OUT/'recovered_models/C3_R1/qualified_recovery.json'
                recovered=read(recovery_path)
                assert sha(recovery_path)=='96edc767b6f971f295c28b0ebdeec15ff692a64d27ff92d22016327abf20f2cb'
                for filename,key in [('observations.json','original_observations_sha256'),
                    ('audit.json','original_failed_audit_sha256'),('completion.json','original_completion_sha256'),
                    ('result.json','original_result_sha256')]:assert sha(d/filename)==recovered[key]
                assert sha(camp/'identity.json')==recovered['original_identity_sha256']
                assert recovered['audit']['passed'] and recovered['no_performance_replay']
                audit=recovered['audit'];e=audit['endpoint']
            else:e=r['endpoint'] or {}
            p=launch['panel'];c=r['completion']
            native=read(d/'result.json') if (d/'result.json').exists() and c['stop_reason']=='normal_return' else {}
            native_prefix='gurobi_' if r['arm']=='P-GRB' else 'external_gini_tree_'
            rows.append(dict(campaign=name,number=r['number'],role=r['id'],arm=r['arm'],
                V=p['V'],M=p['M'],Q=json.dumps(p['Q_vector']),T=p['T_seconds'],cap=launch['cap_seconds'],
                input_sha256=p['input_sha256'],binary_sha256=identity['candidate_binary_sha256'],
                audit_passed=audit.get('passed',False),original_audit_passed=original_audit_passed,
                exact_recovery_sha256=sha(recovery_path) if recovery_path else None,
                stop_reason=c['stop_reason'],outer_seconds=c['process_wall_seconds'],
                end_to_end_seconds=c['end_to_end_seconds'],certificate=e.get('certificate',False),
                U=e.get('U'),L=e.get('L'),gap=e.get('gap'),
                relative_gap=e['gap']/max(abs(e['U']),1e-12) if e.get('U') is not None and e.get('gap') is not None else None,
                optimizer_calls=audit.get('native_calls_started'),receipt_sha256=sha(d/'completion.json'),
                audit_sha256=sha(d/'audit.json'),endpoint_source=e.get('source'),status=e.get('status'),
                work=native.get(native_prefix+'work'),nodes=native.get('gurobi_node_count' if r['arm']=='P-GRB' else 'external_gini_tree_nodes'),
                model_build_seconds=native.get('external_gini_tree_model_build_seconds') if r['arm']!='P-GRB' else None,
                lp_calls=native.get('external_gini_tree_lp_optimize_count') if r['arm']!='P-GRB' else 0,
                partial_mip_calls=native.get('external_gini_tree_partial_mip_optimize_count') if r['arm']!='P-GRB' else 0,
                terminal_mip_calls=native.get('external_gini_tree_terminal_mip_optimize_count') if r['arm']!='P-GRB' else 1))
            cost.append(dict(category='full_'+name,label=f'{name}/{r["number"]}/{r["id"]}/{r["arm"]}',
                experimental_starts=1,optimizer_calls=audit.get('native_calls_started'),
                outer_seconds=c['process_wall_seconds'],failed=not original_audit_passed,stop_reason=c['stop_reason']))
    pairs=[]
    for name in campaigns:
        for role in sorted({r['role'] for r in rows if r['campaign']==name}):
            group={r['arm']:r for r in rows if r['campaign']==name and r['role']==role}
            for ref in ['P-GRB','ENS-C','R1']:
                if ref not in group or 'R2' not in group:continue
                a,b=group[ref],group['R2'];both=a['certificate'] and b['certificate']
                delta=b['outer_seconds']-a['outer_seconds'] if both else None
                ratio=b['outer_seconds']/a['outer_seconds'] if both else None
                pairs.append(dict(campaign=name,role=role,reference=ref,candidate='R2',reference_certified=a['certificate'],
                    candidate_certified=b['certificate'],censoring='both_certified' if both else 'reference_only' if a['certificate']
                    else 'candidate_only' if b['certificate'] else 'both_unproved',certified_time_delta=delta,certified_time_ratio=ratio,
                    material_time_change=bool(both and abs(delta)>=30 and abs(ratio-1)>=.1),
                    severe_time_regression=bool(both and delta>=120 and ratio>=1.25),
                    reference_U=a['U'],candidate_U=b['U'],reference_L=a['L'],candidate_L=b['L'],
                    reference_gap=a['gap'],candidate_gap=b['gap'],reference_relative_gap=a['relative_gap'],candidate_relative_gap=b['relative_gap'],
                    eventual_time_order_known=both))
    # Every diagnostic starts/complete ledger is charged exactly once; failed
    # wrappers never invent actual Optimize counts from their planned count.
    for d in sorted((OUT/'diagnostic_receipts').iterdir()):
        if not (d/'receipt.json').exists():continue
        r=read(d/'receipt.json');local=OUT/'diagnostics'/d.name/'calls.jsonl'
        calls=sum(json.loads(s)['kind']=='start' for s in local.read_text().splitlines()) if local.exists() else None
        cost.append(dict(category='diagnostic',label=d.name,experimental_starts=1,optimizer_calls=calls,
            outer_seconds=r['outer_seconds'],failed=r['exit_code']!=0,stop_reason=r['stop_reason']))
    for d in sorted((OUT/'qualification').iterdir()):
        if not d.is_dir() or not (d/'receipt.json').exists():continue
        r=read(d/'receipt.json');calls=r.get('optimizer_calls')
        actual=OUT/'diagnostics'/d.name/'calls.jsonl'
        if actual.exists():calls=sum(json.loads(s)['kind']=='start' for s in actual.read_text().splitlines())
        if d.name=='integer01':calls=0
        if d.name=='integer03':calls=7
        cost.append(dict(category='qualification',label=d.name,experimental_starts=1,
            optimizer_calls=calls,outer_seconds=r['outer_seconds'],failed=r['exit_code']!=0,stop_reason=r['stop_reason']))
    # Earlier CTest wrappers included the existing Round68 native fixture.
    # Preserve their inaccurate planned-zero receipts and charge the three
    # actual calls proven by the passed fixture/source in a separate correction.
    corrected=read(OUT/'qualification/ctest_native_cost_correction.json')
    for row in corrected['records']:
        d=OUT/'engineering'/row['label'];assert sha(d/'receipt.json')==row['receipt_sha256']
        r=read(d/'receipt.json')
        cost.append(dict(category='native_ctest_qualification_correction',label=row['label'],
            experimental_starts=1,optimizer_calls=3,outer_seconds=r['outer_seconds'],
            failed=r['exit_code']!=0,stop_reason=r['stop_reason']))
    # Conservatively also charge zero-Optimize matrix-export/vector diagnostic
    # batches and fresh P-reference build-only processes. Pure compilation and
    # zero-Optimize CTest stay engineering; native CTest is corrected above.
    for d in sorted((OUT/'engineering').iterdir()):
        if not (d.name.startswith(('export_','start_')) or d.name=='F5_projection_vectors'):continue
        r=read(d/'receipt.json')
        cost.append(dict(category='zero_optimize_diagnostic',label=d.name,experimental_starts=1,optimizer_calls=0,
            outer_seconds=r['outer_seconds'],failed=r['exit_code']!=0,stop_reason=r['stop_reason']))
    for name in ['development01']+campaigns:
        batch=OUT/name/'reference_batch_receipt.json'
        if batch.exists():
            r=read(batch);assert r['passed'] and r['actual_children']==3 and r['optimizer_calls']==0
            for role,h in r['completion_sha256'].items():assert sha(OUT/name/'reference'/role/'completion.json')==h
            cost.append(dict(category='plain_matrix_qualification_batch',label=name+'/reference_batch',
                experimental_starts=1,optimizer_calls=0,outer_seconds=r['outer_seconds'],failed=False,stop_reason=r['stop_reason']))
            continue
        for d in sorted((OUT/name/'reference').iterdir()):
            r=read(d/'completion.json')
            if 'already_billed_parent' in r:
                assert r['already_billed_parent']=='qualification/vehicle01' and r.get('copy_only') and r['outer_seconds']==0
                continue
            cost.append(dict(category='plain_matrix_qualification',label=name+'/reference/'+d.name,experimental_starts=1,
                optimizer_calls=0,outer_seconds=r['outer_seconds'],failed=r['returncode']!=0,stop_reason='normal_return'))
    csv_write(target/'runs.csv',rows);csv_write(target/'pairs.csv',pairs);csv_write(target/'cost_failures.csv',cost)
    write(target/'summary.json',dict(actual_starts=sum(r['experimental_starts'] for r in cost),
        actual_optimizer_calls=sum(r['optimizer_calls'] for r in cost if r['optimizer_calls'] is not None),
        missing_optimize_count=[r['label'] for r in cost if r['optimizer_calls'] is None],
        outer_solver_seconds=sum(r['outer_seconds'] for r in cost if r['experimental_starts']),
        failed_started_processes=[r['label'] for r in cost if r['experimental_starts'] and r['failed']],
        no_double_count_internal_calls=True,campaigns=campaigns,source_sha256=sha(__file__)))
if __name__=='__main__':extract(sys.argv[1],sys.argv[2:])
