"""Finite pure aggregation of RN science, complete clocks and paired outcomes."""
import csv,re
from round143_common import *

def require_idle():assert not budget()['unclosed'],'wait for timed producers before heavy reads/export'
def csv_write(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def csv_rows(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def LP():
    require_idle();rows=[]
    for path in sorted((OUT/'LP').glob('*/result.json')):
        r=read(path);assert r['qualified'] and r['Seed']==0 and r['Threads']==1
        assert sha(path.parent/'model.mps')==r['canonical_SHA'] and sha(path.parent/'solution.json.gz')==r['solution_SHA']
        rows.append(dict(r,result_path=path.relative_to(ROOT).as_posix(),result_SHA=sha(path),
            added_rows=r['after']['rows']-r['before']['rows'],added_columns=r['after']['columns']-r['before']['columns'],
            added_nonzeros=r['after']['nonzeros']-r['before']['nonzeros']))
    write(OUT/'reports/LP.json',dict(PASS=True,positions=rows,LP_Optimize=len(rows),MIP_Optimize=0,
        old_optima_reused_without_Optimize=True,original_objective_support_cutoff_and_g_domain_retained=True,
        numerical_not_rational_optimum_certificates=True,BASE_includes_physical_inventory_bound_information=True))
    csv_write(OUT/'reports/LP.csv',rows)
    print(json.dumps([{k:r[k] for k in ['role','variant','old_L','L','difference','added_rows','added_columns']} for r in rows]))

def full():
    require_idle();rows=[];qualification=[];missing=[];failures=[]
    for matrix_path in sorted(OUT.glob('*_matrix.json')):
        matrix=read(matrix_path)
        if 'batch' not in matrix:continue
        batch=matrix['batch'];isq=batch.startswith('qualification')
        for group in matrix['groups']:
            launch=group['launch'];d=Path(launch['destination'])
            if not (d/'verification_closeout.json').exists():
                item=dict(batch=batch,position=group['position'],role=launch['id'],RN=launch['RN'],destination=str(d))
                (failures if (d/'producer_seal.json').exists() else missing).append(item);continue
            a=read(d/'round135_endpoint.json');audit=read(d/'audit.json');control=read(d/'round143_control_audit.json')
            assert a['native_proof_qualified'] and a['performance_eligible'] and not audit['source_rejections'] and control['PASS']
            assert a['T_cert'] is None if not a['certificate'] else a['T_cert']==a['T_produce']
            ledger=csv_rows(d/'external/paper_optimize_ledger.csv');terminal=next((r for r in reversed(ledger) if 'terminal' in r['native_log']),None)
            observed=[r['payload'] for r in read(d/'observations.json')]
            bylog={r['native_log_path']:r['call'] for r in observed if r['kind']=='call'}
            call=bylog[terminal['native_log']] if terminal else None
            quality=next((r for r in observed if r['kind']=='native_quality' and r['call']==call),None)
            am=csv_rows(d/'external/adaptive_mass_decision_ledger.csv');lp=csv_rows(d/'external/lp_status_ledger.csv')
            raw=read(d/'result.json');raw=raw[0] if isinstance(raw,list) else raw
            identity=read(OUT/group['group']/'identity.json');p=launch['panel']
            r=dict(batch=batch,position=group['position'],role=launch['id'],RN=launch['RN'],method='RN' if launch['RN'] else 'stable-off',seed=launch['seed'],
                formal_entered=not isq,input_SHA=p['input_sha256'],physical_T=p['T_seconds'],lambda_value=p['lambda'],cap=launch['cap_seconds'],
                source_commit=identity['measured_source_commit'],PE_SHA=identity['candidate_binary_sha256'],DLL_SHA=identity['dll_sha256'],
                **{k:a[k] for k in ['U','L','certificate','signed_gap','relative_gap','T_produce','T_cert','T_verify','T_total','H_complete','H_semantic_SHA','H_fleet_SHA','declared_calls','returned_calls']},
                external_merged_final_L=a['L'],terminal_native_return_ObjBoundC=quality.get('ObjBoundC') if quality else None,
                terminal_native_return_ObjVal=quality.get('ObjVal') if quality else None,
                LP_calls=sum(v['solve_kind']=='LP' for v in ledger),target_calls=sum('TARGET' in v['solve_kind'] for v in ledger),terminal_calls=sum(v['solve_kind']=='MIP' for v in ledger),
                root_LP_seconds=sum(float(v['solver_runtime']) for v in ledger if v['solve_kind']=='LP' and v['leaf_id']=='L0'),
                root_LP_Work=sum(float(v['work']) for v in ledger if v['solve_kind']=='LP' and v['leaf_id']=='L0'),
                Native_total_Work=sum(float(v['work']) for v in ledger),Native_total_runtime=sum(float(v['solver_runtime']) for v in ledger),
                terminal_Work=float(terminal['work']) if terminal else 0,terminal_nodes=float(terminal['nodes']) if terminal else 0,
                root_L=next((float(v['lower_bound']) for v in lp if v['leaf_id']=='L0'),None),
                AM_action_sequence=';'.join(v['selected_action'] for v in am),actual_split_count=raw['external_gini_tree_split_count'],
                RN_models_checked=len(control['models']),Native_RN_receipts=len(control['native_audits']),
                performance_eligible=a['performance_eligible'],native_proof_qualified=a['native_proof_qualified'],destination=str(d))
            if terminal:
                text=Path(terminal['native_log']).read_text();match=re.search(r'Best objective\s+([-+0-9.eE]+), best bound\s+([-+0-9.eE]+)',text)
                if match:r.update(printed_terminal_ObjVal=float(match[1]),printed_terminal_ObjBound=float(match[2]))
            (qualification if isq else rows).append(r)
    pairs=[]
    for candidate in [r for r in rows if r['RN']]:
        off=next((r for r in rows if not r['RN'] and (r['role'],r['seed'])==(candidate['role'],candidate['seed'])),None)
        if off is None:continue
        for key in ['input_SHA','physical_T','lambda_value','cap','source_commit','PE_SHA','H_semantic_SHA','H_fleet_SHA']:assert candidate[key]==off[key],(candidate['role'],key)
        pairs.append(dict(role=candidate['role'],seed=candidate['seed'],same_PE=True,own_H_equal=True,
            off_U=off['U'],RN_U=candidate['U'],off_L=off['L'],RN_L=candidate['L'],
            off_certificate=off['certificate'],RN_certificate=candidate['certificate'],
            **{'delta_'+k:candidate[k]-off[k] for k in ['U','L','T_produce','T_verify','T_total']},
            off_T_cert=off['T_cert'],RN_T_cert=candidate['T_cert'],off_splits=off['actual_split_count'],RN_splits=candidate['actual_split_count']))
    write(OUT/'reports/full.json',dict(UTC=utc(),new_arms=rows,qualification=qualification,pairs=pairs,failures=failures,unstarted=missing,
        all_entered_preserved=True,budget=budget(),Optimize=0,clocks='Full producer + all mandatory postverification; complete experimental outer charged once'))
    csv_write(OUT/'reports/new_arms.csv',rows);csv_write(OUT/'reports/qualification.csv',qualification);csv_write(OUT/'reports/same_PE_pairs.csv',pairs)
    write(OUT/'cost_report.json',dict(UTC=utc(),charged_new_experiment_seconds=budget()['G1_seconds'],experiment=budget(),
        ceiling_seconds=28800,all_complete_experimental_outers_charged=True,qualifications_and_failures_included=True,
        offline_arithmetic_seconds=read(OUT/'math/offline_point_checks.json')['seconds'],
        build_seconds_separate=sum(read(p)['separately_reported_seconds'] for p in (OUT/'fees').glob('*/receipt.json')),
        H_LP_MIP_Work_not_added_again=True))
    print(json.dumps(pairs,indent=2))

if __name__=='__main__':globals()[sys.argv[1]]()
