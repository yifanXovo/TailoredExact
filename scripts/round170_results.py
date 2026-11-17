"""Qualified endpoint/cost comparisons and the original 28-column B increment."""
from round170_common import *

def table_csv(path,rows):
    scalar=[{k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v) for k,v in r.items()} for r in rows]
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(scalar[0]));w.writeheader();w.writerows(scalar)

def complete_tables():
    matrix=read(OUT/'matrix_frozen.json');rows=[];hrows=[]
    roles={p['id']:p for p in read(OUT/'inputs_frozen.json')['roles']}
    for p in matrix['positions']:
        d=Path(p['directory']);a=read(OUT/f"review/complete_audit_{p['position']:02}.json");assert a['passed']
        r=result(d/'result.json');q=roles[p['role']];is_plain=p['arm']=='P'
        choice=read(d/'primal/selection.json') if not is_plain else None
        ledger=list(csv.DictReader((d/'external/paper_optimize_ledger.csv').open(newline='',encoding='utf-8-sig'))) if not is_plain else []
        paths=[read(v) for v in sorted((d/'primal').glob('*/path.json'))] if not is_plain else []
        for v in paths:hrows.append(dict(position=p['position'],role=p['role'],arm=p['arm'],Native_Seed=p['Native_Seed'],**v))
        phase=list(csv.DictReader((d/'phases.csv').open(newline='',encoding='utf-8-sig')))
        events={x['event']:float(x['process_seconds']) for x in phase}
        build=(events['root_canonical_model_construction_complete']-events['root_canonical_model_construction_start']) if not is_plain else None
        audit_costs=[v for v in read(OUT/'review/audit_process_costs.json') if p['position'] in v['positions'] and v['rc']==0]
        assert audit_costs and audit_costs[-1]['positions']==[p['position']], 'one measured audit process per returned position'
        process=a['completion']['process_outer_seconds'];audit=audit_costs[-1]['audit_process_outer_seconds'];phys=a['true_final_physical']
        selected=a['full_paid_H']['selected'] if not is_plain else None
        row=dict(position=p['position'],role=p['role'],arm=p['arm'],run_id=d.name,
            input_path=q['input_path'],input_SHA256=q['input_sha256'],T_seconds=q['T_seconds'],lambda_value=q['lambda'],
            lambda_decimal17=q['base_lambda_decimal17'],lambda_binary64=q['base_lambda_binary64'],
            cap_seconds=600,Native_Seed=p['Native_Seed'],Threads=1,source_commit=MEASURED,delivery_base=BASE,PE_SHA256=PE_SHA,DLL_SHA256=DLL_SHA,
            initial_U=r['initial_heuristic_UB'] if selected else None,selected_H=choice['selected'] if choice else None,
            selected_H_seed=selected['effective_seed'] if selected else None,
            selected_H_search_lambda=selected['search_lambda'] if selected else None,H_calls=len(paths),
            full_initialization_complete=a['full_paid_H']['complete_arm_initialization'] if selected else None,
            H_seconds=sum(x['H_seconds'] for x in paths),initialization_seconds=choice['total_initialization_seconds'] if choice else 0.,
            decoded_checks=sum(x['decoded_checks'] for x in paths),physical_work_counter_sum=sum(x['physical_work_counter_sum'] for x in paths),
            U=a['U'],L=a['L'],G=phys['G'],P=phys['P'],signed_absolute_gap=a['absolute_gap'],
            absolute_gap=max(0,a['absolute_gap']),relative_gap=max(0,a['relative_gap']),signed_relative_gap=a['relative_gap'],
            certificate=a['certificate'],state='CERT' if a['certificate'] else 'OPEN',certificate_basis=a['certificate_basis'],
            T_cert_process=process if a['certificate'] else None,certification_censored=not a['certificate'],
            process_outer_seconds=process,CPP_final_process_wall_seconds=r['final_process_wall_time_seconds'],
            audit_seconds=audit,audit_function_seconds=a['audit_seconds'],
            audit_seconds_scope='successful audit process outer clock, including interpreter/import/serialization; first two manual clocks conservatively include brief status readback',
            T_total_with_independent_audit=process+audit,process_wall_time_comparable=r['process_wall_time_comparable'],
            raw_status=r['status'],actual_Optimize=a['actual_Optimize'],LP=a['LP'],MIP=a['MIP'],Native_seconds=a['Native_seconds'],
            Work=r['gurobi_work'] if is_plain else sum(float(x['work']) for x in ledger),
            nodes=r['gurobi_node_count'] if is_plain else sum(float(x['nodes']) for x in ledger),
            root_model_construction_seconds=build,all_model_build_seconds=None if is_plain else r['external_gini_tree_model_build_seconds'],
            original_H_reverification_seconds=sum(x['original_verification_seconds'] for x in paths),
            process_residual_after_Native_and_H_seconds=process-a['Native_seconds']-sum(x['H_seconds'] for x in paths),
            residual_scope='remaining construction, transformations, checks, logging, serialization and process overhead; not a pure verifier timer',
            exact_first_hit_global_seconds=None,cold_NumStart=0 if is_plain else None,
            actual_model_registry=[x['model_sha256'] for x in ledger] if ledger else [a['models'][0]['model']['SHA']],
            audit_path=f"results/unified_exact_round170/review/complete_audit_{p['position']:02}.json",
            raw_result=f"results/unified_exact_round170/complete_raw/{d.name}/result.json",
            raw_fleet_SHA256=sha(d/'fleet.json'),
            raw_archive_path='results/unified_exact_round170/artifacts/round170_new_raw.zip',
            raw_archive_member=f'complete_raw/{d.name}/result.json')
        assert row['H_calls']==(0 if is_plain else 1 if p['arm']=='B' else 3)
        if selected:assert abs(row['initial_U']-selected['original_F'])<1e-10
        rows.append(row)
    assert len(rows)==22 and sum(r['H_calls'] for r in rows)==41
    write(OUT/'complete_arms.json',dict(UTC=utc(),rows=rows,all_22_qualified=True,
        known_exposed_roles=True,Native_Seeds=[1,2],M_P_Seed1_only=True,new_physical_inputs=0,
        extra_H_paid_in_process=True,postreturn_audit_separate_from_algorithm=True))
    table_csv(OUT/'complete_arms.csv',rows)
    write(OUT/'h_path_results.json',dict(UTC=utc(),rows=hrows,H_calls=len(hrows),
        no_H_only_calls=True,all_H_fleets_produced_independently_inside_own_process=True))
    table_csv(OUT/'h_path_results.csv',hrows)
    comparisons(rows)
    costs(rows)
    csv_increment(rows)
    print(json.dumps(dict(positions=len(rows),H_calls=len(hrows),actual_Optimize=sum(r['actual_Optimize'] for r in rows),
        certified=sum(r['certificate'] for r in rows),process_seconds=sum(r['process_outer_seconds'] for r in rows)),indent=2))

def pair(subject,reference,label):
    assert (subject['role'],subject['Native_Seed'],subject['cap_seconds'],subject['input_SHA256'],subject['PE_SHA256'])==(
        reference['role'],reference['Native_Seed'],reference['cap_seconds'],reference['input_SHA256'],reference['PE_SHA256'])
    delta=max(1e-6,.001*max(abs(reference['U']),1e-12))
    v=dict(comparison=label,role=subject['role'],Native_Seed=subject['Native_Seed'],cap_seconds=600,
        subject_arm=subject['arm'],reference_arm=reference['arm'],subject_run=subject['run_id'],reference_run=reference['run_id'],
        delta=delta,delta_reference_U=reference['U'],
        subject={k:subject[k] for k in ['initial_U','U','L','absolute_gap','relative_gap','state','T_cert_process','process_outer_seconds','H_seconds','Native_seconds','Work','nodes']},
        reference={k:reference[k] for k in ['initial_U','U','L','absolute_gap','relative_gap','state','T_cert_process','process_outer_seconds','H_seconds','Native_seconds','Work','nodes']})
    for metric in ['U','L','absolute_gap','relative_gap','process_outer_seconds','H_seconds','Native_seconds','Work','nodes']:
        difference=subject[metric]-reference[metric];v[metric+'_difference']=difference
        v[metric+'_change_percent']=100*difference/abs(reference[metric]) if abs(reference[metric])>1e-12 else None
    v.update(U_material_improvement=v['U_difference']<-delta,U_material_regression=v['U_difference']>delta,
        L_material_improvement=v['L_difference']>delta,L_material_regression=v['L_difference']<-delta,
        absolute_gap_material_improvement=v['absolute_gap_difference']<-delta,
        absolute_gap_material_regression=v['absolute_gap_difference']>delta,
        T_cert_ratio=subject['T_cert_process']/reference['T_cert_process'] if subject['certificate'] and reference['certificate'] else None,
        certificate_comparison=('both_CERT' if subject['certificate'] and reference['certificate'] else
            'subject_only_CERT' if subject['certificate'] else 'reference_only_CERT' if reference['certificate'] else 'both_OPEN'),
        no_composite_win_score=True)
    return v

def comparisons(rows):
    index={(r['role'],r['Native_Seed'],r['arm']):r for r in rows};out={k:[] for k in ['CB','CM','BP','CP']}
    for r in rows:
        if r['arm']=='C':out['CB'].append(pair(r,index[(r['role'],r['Native_Seed'],'B')],'C/B'))
        if r['arm']=='M':out['CM'].append(pair(index[(r['role'],1,'C')],r,'C/M'))
        if r['arm']=='P':
            out['BP'].append(pair(index[(r['role'],1,'B')],r,'B/P'))
            out['CP'].append(pair(index[(r['role'],1,'C')],r,'C/P'))
    for key,values in out.items():
        write(OUT/f'comparison_{key}.json',dict(UTC=utc(),rows=values,material_scale_preregistered=True,
            no_statistical_test=True,no_cross_arm_endpoint_splicing=True))
        table_csv(OUT/f'comparison_{key}.csv',values)
    mechanism=[]
    for r in rows:
        if r['arm']!='M':continue
        b=index[(r['role'],1,'B')];c=index[(r['role'],1,'C')]
        bm=Path(OUT/'complete_raw'/b['run_id']);mm=Path(OUT/'complete_raw'/r['run_id'])
        same_fleet=sha(bm/'primal/base/fleet.json')==sha(mm/'primal/base/fleet.json')
        assert same_fleet and b['initial_U']==r['initial_U']
        ba=read(ROOT/b['audit_path']);ma=read(ROOT/r['audit_path'])
        mechanism.append(dict(role=r['role'],Native_Seed=1,B_initial_U=b['initial_U'],M_initial_U=r['initial_U'],C_initial_U=c['initial_U'],
            Delta_restart=b['initial_U']-r['initial_U'],Delta_weight=r['initial_U']-c['initial_U'],
            M_endpoint_U_minus_B=r['U']-b['U'],C_endpoint_U_minus_M=c['U']-r['U'],
            B_M_identical_base_fleet_and_selected_original_U=same_fleet,
            B_M_first_actual_model_equal=b['actual_model_registry'][0]==r['actual_model_registry'][0],
            B_actual_native_endpoints=dict(Work=b['Work'],nodes=b['nodes'],Native_seconds=b['Native_seconds']),
            M_actual_native_endpoints=dict(Work=r['Work'],nodes=r['nodes'],Native_seconds=r['Native_seconds']),
            interpretation='An endpoint difference with identical initial fleet/first model is a finite search-progress/cutoff observation, not a better H initialization',
            equal_H_call_count_not_equal_actual_work=True))
    write(OUT/'mechanism_initialization.json',dict(rows=mechanism))

def costs(rows):
    attempts=read(OUT/'review/complete_audit_attempts.json')
    totals={key:sum(r[key] for r in rows) for key in ['H_calls','actual_Optimize','LP','MIP','Native_seconds',
        'Work','nodes','process_outer_seconds','H_seconds','initialization_seconds','audit_seconds','audit_function_seconds',
        'process_residual_after_Native_and_H_seconds','original_H_reverification_seconds']}
    totals.update(UTC=utc(),complete_positions=22,nominal_process_cap_sum=13200,qualification_H=0,qualification_Optimize=0,
        all_model_build_reported_tailored_seconds=sum(r['all_model_build_seconds'] or 0 for r in rows),
        P_model_build_separate_timer=None,postreturn_audit_all_attempt_seconds=sum(r['audit_inclusive_seconds'] for r in attempts),
        postreturn_audit_attempts=len(attempts),science_start_epoch=SCIENCE_START,science_cap_seconds=SCIENCE_CAP,
        instrumented_audit_process_outer_seconds=sum(r['audit_process_outer_seconds'] for r in read(OUT/'review/audit_process_costs.json')),
        **science_clock(),Native_H_model_checks_nested_not_added_to_process=True,
        independent_reviews_separate_from_successful_reader=True,ordinary_Git_public_recovery_IO='recorded separately at publication',
        no_extra_solver_qualification=True)
    write(OUT/'cost_report.json',totals)

def csv_increment(rows):
    # Only the header of the historical 28-column schema is reused. No old data
    # rows are substituted for the absent byte-pinned authoritative 118 records.
    source=ROOT/'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv'
    header=next(csv.reader(io.StringIO(source.read_bytes().decode('gb18030'))));assert len(header)==28
    header[-2:]=['实验数据来源','实例元数据来源']
    roles={p['id']:p for p in read(OUT/'inputs_frozen.json')['roles']}
    index={(r['role'],r['Native_Seed'],r['arm']):r for r in rows};values=[];mapping=[]
    ref=read(OUT/'data_commit.json')['commit'] if (OUT/'data_commit.json').exists() else BRANCH
    baseurl='https://github.com/yifanXovo/TailoredExact/blob/'+ref+'/'
    metadata='https://github.com/yifanXovo/TailoredExact/blob/8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb/results/unified_exact_round163/input_manifest.json'
    for b in rows:
        if b['arm']!='B':continue
        p=roles[b['role']];plain=index.get((b['role'],b['Native_Seed'],'P'))
        scenario={'shortage':'库存短缺','balanced':'库存平衡','surplus':'库存过剩'}[p['inventory']]
        geometry={'compact':'紧凑分布','regional':'区域分布','clustered':'簇状分布'}.get(p['geometry'],p['geometry'])
        if plain:
            comparison=pair(b,plain,'B/P')
            outcome='分指标比较'
            note=f"新同预算严格B/P配对；B {b['state']}，P {plain['state']}；ΔU={comparison['U_difference']:.17g}；ΔL={comparison['L_difference']:.17g}；Δ绝对gap={comparison['absolute_gap_difference']:.17g}；不合成单一胜率"
            pv=['已收敛' if plain['certificate'] else '未收敛',plain['T_cert_process'] if plain['certificate'] else '',
                '' if plain['certificate'] else 100*plain['relative_gap'],plain['L'],plain['U']]
        else:
            outcome='N/A';note='本轮B控制；N/A-P；无同轮同预算P、不计新胜例';pv=['无配对结果','','','','']
        note+=f"；Native Seed{b['Native_Seed']}；cap=600s；run={b['run_id']}；CPP={MEASURED}；PE={PE_SHA}；CERT时间=T_cert_process；独立事后审计另列；M/C独立记录"
        v=[p['id'],p['V'],p['M'],scenario,p['id'].split('-')[-1],p['source'],geometry,p['T_seconds'],
            format(p['lambda'],'.17g'),format(p['lambda']/.15,'.17g'),b['Native_Seed'],1,170,600,
            '已收敛' if b['certificate'] else '未收敛',b['T_cert_process'] if b['certificate'] else '',
            '' if b['certificate'] else 100*b['relative_gap'],b['L'],b['U'],*pv,outcome,note,
            baseurl+'results/unified_exact_round170/complete_arms.json',metadata]
        assert len(v)==28;values.append(v)
        mapping.append(dict(increment_row=len(values),position=b['position'],run_id=b['run_id'],role=b['role'],
            Native_Seed=b['Native_Seed'],P_run_id=plain['run_id'] if plain else None,new_strict_pair=plain is not None,
            T_cert_process=b['T_cert_process'],audit_seconds=b['audit_seconds'],T_total_with_independent_audit=b['T_total_with_independent_audit']))
    target=OUT/'GI_TBC_R170_B_increment_28col.csv'
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(values)
    assert len(values)==8 and sum(x['new_strict_pair'] for x in mapping)==3
    reconciliation=read(OUT/'CSV_reconciliation.json')
    reconciliation.update(UTC=utc(),qualified_new_B_records=8,new_strict_P_pairs=3,new_physical_inputs=0,
        candidate_C_rows_in_master=0,candidate_M_rows_in_master=0,increment=bind(target),increment_mapping=mapping,
        clock_policy='qualified CERT uses process outer T_cert_process only; OPEN gaps expressed in percent; independent audit separate')
    if reconciliation['authoritative_118_available']:
        master=WORK/'data/GI_TBC_vs_P_GRB_All_Tested_Instances.csv';old=master.read_bytes()
        assert hashlib.sha256(old).hexdigest()==reconciliation['expected_SHA256']
        table=list(csv.reader(io.StringIO(old.decode('utf-8-sig'))));assert table[0]==header and len(table)==119
        assert all((str(row[0]),str(row[10]),str(row[12]),str(row[13])) not in
            {(str(v[0]),str(v[10]),str(v[12]),str(v[13])) for v in values} for row in table[1:])
        stream=io.StringIO(newline='');csv.writer(stream).writerows(values)
        master.write_bytes(old+(b'' if old.endswith(b'\n') else b'\r\n')+stream.getvalue().encode('utf-8'))
        copy=OUT/'GI_TBC_vs_P_GRB_All_Tested_Instances.csv';copy.write_bytes(master.read_bytes())
        reconciliation.update(actual_master=bind(copy),actual_records=126,actual_master_rows_appended=8,old_118_bytes_preserved=True)
    else:reconciliation.update(actual_master=None,actual_records=None,actual_master_rows_appended=0,
        disposition='Authoritative 118-row package absent. Deliver 8-row qualified mergeable increment with 3 strict P pairs; no 126-row master is claimed.')
    write(OUT/'CSV_reconciliation.json',reconciliation)

if __name__=='__main__':complete_tables()
