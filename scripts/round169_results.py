"""Aggregate the qualified fixed panel and produce the unpaired B CSV increment."""
from round169_common import *
from round169_run import result

def complete_tables():
    matrix=read(OUT/'matrix_execution_frozen.json');rows=[]
    attempts=read(OUT/'review/complete_audit_attempts.json')
    for p in matrix['positions']:
        d=Path(p['directory']);a=read(OUT/f"review/complete_audit_{p['position']:02}.json");assert a['passed']
        r=result(d/'result.json');choice=read(d/'primal/selection.json')
        ledger=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='',encoding='utf-8-sig')))
        paths=[read(q) for q in sorted((d/'primal').glob('*/path.json'))]
        phase=list(csv.DictReader((d/'phases.csv').open(newline='',encoding='utf-8-sig')))
        events={x['event']:float(x['process_seconds']) for x in phase}
        rootbuild=events['root_canonical_model_construction_complete']-events['root_canonical_model_construction_start']
        process=a['completion']['process_outer_seconds'];audit=a['audit_seconds'];phys=a['true_final_physical']
        selected=a['full_paid_H']['selected'];q=next(v for v in read(OUT/'h_panel_frozen.json')['roles'] if v['id']==p['role'])
        row=dict(position=p['position'],role=p['role'],arm=p['arm'],run_id=d.name,input_path=q['input_path'],input_SHA256=q['input_sha256'],
            T_seconds=q['T_seconds'],lambda_value=q['lambda'],cap_seconds=p['cap'],Native_Seed=0,Threads=1,
            source_commit=p['source_commit'],measured_core_source_commit=read(OUT/'candidate_manifest.json')['source_commit'],PE_SHA256=p['PE_SHA256'],
            initial_U=r['initial_heuristic_UB'],selected_H=choice['selected'],selected_H_seed=selected['effective_seed'],
            selected_H_search_lambda=selected['search_lambda'],H_calls=len(paths),full_initialization_complete=a['full_paid_H']['complete_arm_initialization'],
            H_seconds=sum(x['H_seconds'] for x in paths),initialization_seconds=choice['total_initialization_seconds'],
            decoded_checks=sum(x['decoded_checks'] for x in paths),physical_work_counter_sum=sum(x['physical_work_counter_sum'] for x in paths),
            U=a['U'],L=a['L'],G=phys['G'],P=phys['P'],signed_absolute_gap=a['absolute_gap'],relative_gap=a['relative_gap'],
            certificate=a['certificate'],certificate_basis=a['certificate_basis'],T_cert_process=process if a['certificate'] else None,
            process_outer_seconds=process,CPP_final_process_wall_seconds=r['final_process_wall_time_seconds'],
            postreturn_independent_audit_seconds=audit,T_total_with_independent_audit=process+audit,
            process_wall_time_comparable=r['process_wall_time_comparable'],status=r['status'],
            actual_Optimize=a['actual_Optimize'],LP=a['LP'],MIP=a['MIP'],Native_seconds=a['Native_seconds'],
            Work=sum(float(x['work']) for x in ledger),nodes=sum(float(x['nodes']) for x in ledger),
            root_model_construction_seconds=rootbuild,
            all_model_build_seconds=r['external_gini_tree_model_build_seconds'],
            original_H_reverification_seconds=sum(x['original_verification_seconds'] for x in paths),
            process_residual_after_Native_and_H_seconds=process-a['Native_seconds']-sum(x['H_seconds'] for x in paths),
            residual_scope='includes all remaining model build, transformation, checks, logging, serialization and process overhead; not a pure verifier timer',
            actual_model_registry=[x['model_sha256'] for x in ledger],
            end_state_source_rejected=False,audit_path=f"results/unified_exact_round169/review/complete_audit_{p['position']:02}.json",
            raw_result=f"results/unified_exact_round169/complete_raw/{d.name}/result.json",raw_fleet_SHA256=sha(d/'fleet.json'))
        row['raw_archive_path']='results/unified_exact_round169/artifacts/round169_new_raw_and_runtime.zip'
        row['raw_archive_member']=f'complete_raw/{d.name}/result.json'
        assert row['H_calls']==(1 if p['arm']=='B' else 3)
        assert abs(row['initial_U']-selected['original_F'])<1e-10
        rows.append(row)
    assert len(rows)==18
    write(OUT/'complete_arms.json',dict(UTC=utc(),rows=rows,all_18_qualified=True,short_cap_known_roles_Native_Seed0=True,
        extra_H_paid_in_process=True,independent_postreturn_audit_separate_from_CPP_algorithm_checks=True,new_P_pairs=0))
    scalar=[{k:v for k,v in r.items() if k!='actual_model_registry'} for r in rows]
    with (OUT/'complete_arms.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(scalar[0]));w.writeheader();w.writerows(scalar)
    pairs=[]
    for role in dict.fromkeys(r['role'] for r in rows):
        arm={r['arm']:r for r in rows if r['role']==role};b,m,c=(arm[k] for k in ['B','M','C'])
        pairs.append(dict(role=role,B={k:b[k] for k in ['U','L','certificate','process_outer_seconds','initial_U']},
            M={k:m[k] for k in ['U','L','certificate','process_outer_seconds','initial_U']},
            C={k:c[k] for k in ['U','L','certificate','process_outer_seconds','initial_U']},
            C_minus_B_U=c['U']-b['U'],C_minus_M_U=c['U']-m['U'],C_minus_B_L=c['L']-b['L'],C_minus_M_L=c['L']-m['L']))
    write(OUT/'complete_comparisons.json',dict(rows=pairs,no_single_win_score=True))
    cost=dict(UTC=utc(),complete_positions=18,H_only_calls=read(OUT/'h_results.json')['H_calls'],H_only_Optimize=0,
        complete_H_calls=sum(r['H_calls'] for r in rows),actual_Optimize=sum(r['actual_Optimize'] for r in rows),
        LP=sum(r['LP'] for r in rows),MIP=sum(r['MIP'] for r in rows),Native_seconds=sum(r['Native_seconds'] for r in rows),
        Native_Work=sum(r['Work'] for r in rows),Native_nodes=sum(r['nodes'] for r in rows),
        complete_process_outer_seconds=sum(r['process_outer_seconds'] for r in rows),nominal_process_cap_sum=8100,
        complete_H_seconds=sum(r['H_seconds'] for r in rows),complete_initialization_seconds=sum(r['initialization_seconds'] for r in rows),
        root_model_construction_seconds=sum(r['root_model_construction_seconds'] for r in rows),
        all_model_build_seconds=sum(r['all_model_build_seconds'] for r in rows),
        original_H_reverification_seconds=sum(r['original_H_reverification_seconds'] for r in rows),
        process_residual_after_Native_and_H_seconds=sum(r['process_residual_after_Native_and_H_seconds'] for r in rows),
        postreturn_audit_success_seconds=sum(r['postreturn_independent_audit_seconds'] for r in rows),
        all_recorded_audit_attempt_seconds=sum(x['audit_inclusive_seconds'] for x in attempts),
        qualification_cpp_process_seconds=sum(read(p)['process_outer_seconds'] for p in (OUT/'qualification').rglob('completion.json')),
        source_provenance_cpp_process_seconds=sum(read(p)['process_outer_seconds'] for p in (OUT/'provenance_revalue').rglob('completion.json')),
        H_only_shared_outer_seconds=read(OUT/'h_results.json')['shared_outer_seconds'],
        primary_and_reviewer_read_only_Optimize=0,
        Native_H_model_checks_nested_not_added_to_process_total=True,
        science_elapsed_conservative_seconds=time.time()-read(OUT/'entry_state.json')['science_start_epoch'],science_cap_seconds=28800,
        ordinary_Git_public_recovery_IO='separate delivery receipts; conservative science window also includes waiting/initial transport')
    write(OUT/'cost_report.json',cost)
    csv_increment(rows)
    print(json.dumps(dict(cost=cost,comparisons=pairs),indent=2))

def csv_increment(arms):
    base=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    raw=base.read_bytes();header=next(csv.reader(io.StringIO(raw.decode('gb18030'))));assert len(header)==28
    roles={p['id']:p for p in read(OUT/'h_panel_frozen.json')['roles']};values=[];mapping=[]
    ref=read(OUT/'data_commit.json')['commit'] if (OUT/'data_commit.json').is_file() else 'codex/round169-primal-reweight'
    url='https://github.com/yifanXovo/TailoredExact/blob/'+ref+'/'
    for arm in arms:
        if arm['arm']!='B':continue
        p=roles[arm['role']]
        scenario={'shortage':'库存短缺','balanced':'库存平衡','surplus':'库存过剩'}[p['inventory']]
        geometry={'compact':'紧凑分布','regional':'区域分布','clustered':'簇状分布'}.get(p['geometry'],p['geometry'])
        row=[p['id'],p['V'],p['M'],scenario,p['id'].split('-')[-1],p['source'],geometry,p['T_seconds'],p['lambda'],p['lambda']/.15,
            0,1,169,arm['cap_seconds'],'已收敛' if arm['certificate'] else '未收敛',arm['T_total_with_independent_audit'] if arm['certificate'] else '',
            '' if arm['certificate'] else 100*arm['relative_gap'],arm['L'],arm['U'],'无配对结果','','','','','N/A',
            f"本轮同构建B控制；N/A-P；无同轮P、不计新胜率；Native Seed0；cap={arm['cap_seconds']}s；run={arm['run_id']}；CPP={arm['measured_core_source_commit']}；PE={arm['PE_SHA256']}；M/C独立记录",
            url+'results/unified_exact_round169/complete_arms.json',url+arm['audit_path']]
        assert len(row)==28;values.append(row);mapping.append(dict(row=len(values),position=arm['position'],role=p['id'],run_id=arm['run_id'],new_strict_P_pair=False))
    target=OUT/'GI_TBC_R169_B_controls_increment_28col.csv'
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(values)
    assert base.read_bytes()==raw
    reconcile=read(OUT/'CSV_reconciliation.json');reconcile.update(UTC=utc(),eligible_B_increment_rows=len(values),
        increment=bind(target),increment_mapping=mapping,new_P_pairs=0,M_C_in_master=False)
    master=WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    if reconcile['authoritative_112_available']:
        src=next(Path(x['path']) if Path(x['path']).is_absolute() else ROOT/x['path'] for x in reconcile['found'] if x['SHA256']==reconcile['expected_SHA256'])
        master.parent.mkdir(parents=True,exist_ok=True)
        old=src.read_bytes();assert hashlib.sha256(old).hexdigest()==reconcile['expected_SHA256']
        extra=io.StringIO(newline='');csv.writer(extra).writerows(values)
        master.write_bytes(old+(b'' if old.endswith(b'\n') else b'\r\n')+extra.getvalue().encode('utf-8'))
        reconcile.update(new_master_rows=len(values),actual_master=bind(master),actual_records=112+len(values))
    else:
        reconcile.update(new_master_rows=0,actual_master=None,actual_records=None,
            missing_master_disposition='112-row attachment absent in bounded lookup. Six qualified B rows delivered separately; cannot claim actual 112->118 append. Protected 91/103 versions unchanged.')
    write(OUT/'CSV_reconciliation.json',reconcile)

if __name__=='__main__':complete_tables()
