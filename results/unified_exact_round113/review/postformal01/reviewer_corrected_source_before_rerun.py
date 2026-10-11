"""Independent postformal offline review of the four actual Round113 G50 arms.

No subprocess, solver DLL, native invocation, qualification or fixtures. Only
current new raw is parsed; retained old authority is checked by bytes alone.
All output is confined to review/postformal01.
"""
from pathlib import Path
import collections, csv, datetime, hashlib, json, math, re, sys, time

ROOT = Path('E:/codes/ExactEBRP-round113')
OUT = ROOT / 'results/unified_exact_round113'
DEST = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
import round108_reader as core
import round113_audit as paid
import round94_lpg_contemporary as parameters
import round86_native_evidence as receipts
from compare_round112_startup import compare as compare_H
csv.field_size_limit(64 * 1024 * 1024)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(name, value):
    (DEST / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
        allow_nan=False) + '\n', encoding='utf-8')

def main():
    started = time.perf_counter()
    bindings = {}
    def bind(path):
        path = Path(path)
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        value = sha(path); bindings[key] = value; return value

    candidate = read(OUT / 'candidate_identity.json')
    ident = read(OUT / 'campaign/identity.json')
    production = read(OUT / 'production_identity.json')
    admission = read(OUT / 'review/performance_admission.json')
    assert bind(OUT / 'candidate_identity.json') == admission['candidate_identity_SHA'] == '303e900baf8d6dfb6f80570a9c585aded727ef66202148df2237a900eee0ba2b'
    assert bind(OUT / 'campaign/identity.json') == admission['campaign_identity_SHA']
    assert candidate['production_PE_SHA'] == ident['candidate_binary_sha256'] == admission['production_PE_SHA']
    assert candidate['DLL_SHA'] == ident['dll_sha256'] == admission['DLL_SHA']
    assert bind(ROOT / 'build/research/round113-inherited/ExactEBRP.exe') == admission['production_PE_SHA']
    assert bind(Path('D:/gurobi1302/win64/bin/gurobi130.dll')) == admission['DLL_SHA']
    assert production['measured_source_commit'] == ident['measured_source_commit'] == admission['measured_source_commit']
    assert not production['production_recompiled']
    assert ident['source_hashes'] == candidate['source_bindings'] == production['source_bindings']
    assert ident['helpers'] == candidate['helpers'] and len(candidate['helpers']) == 42
    assert len(candidate['source_bindings']) == 206
    for name, digest in {**candidate['source_bindings'], **candidate['helpers']}.items():
        assert bind(ROOT / name) == digest, name
    assert candidate['full_argv'] == [l['command'] for l in ident['launches']]
    assert len(ident['launches']) == 8
    assert [(l['id'], l['arm'], l['cap_seconds']) for l in ident['launches']] == [
        ('G50-C1','M-B',1800), ('G50-C1','ENS-C',1800), ('G50-C1','P-S',1800), ('G50-C1','P-GRB',1800),
        ('G100-R2','P-GRB',3600), ('G100-R2','ENS-C',3600), ('G100-R2','P-S',3600), ('G100-R2','M-B',3600)]
    summaries = [json.loads(s) for s in (OUT / 'campaign/summary.jsonl').read_text().splitlines()]
    processes = [json.loads(s) for s in (OUT / 'campaign/processes.jsonl').read_text().splitlines()]
    assert len(summaries) == len(processes) == 4
    assert [x['number'] for x in summaries] == [1,2,3,4]
    assert [x['number'] for x in processes] == [1,2,3,4]
    assert len(list((OUT / 'campaign/raw').iterdir())) == 4
    core.start_reader.ROOT = ROOT
    reviewed = []; endpoint_objects = {}; journals = {}; start_records = []; models = []; native_logs = []
    for launch, summary, process in zip(ident['launches'][:4], summaries, processes):
        d = core.portable(ROOT, launch['destination']); p = launch['panel']; arm = launch['arm']
        assert summary['number'] == process['number'] == launch['number']
        rawlaunch = read(d / 'launch.json'); result = read(d / 'result.json'); audit = read(d / 'audit.json')
        completion = read(d / 'completion.json'); observations = read(d / 'observations.json')
        native_end = read(d / 'native_end_receipt.json'); postexit = read(d / 'postexit_audit_receipt.json')
        progress = read(d / 'progress_publication_receipt.json')
        assert rawlaunch['command'] == launch['command'] and rawlaunch['panel'] == p
        assert rawlaunch['prereg_sha256'] == ident['prereg_sha256']
        assert bind(ROOT / p['input_path']) == p['input_sha256']
        assert completion == summary['completion']
        assert completion['returncode'] == result['process_return_code'] == 0
        assert completion['within_cap'] and completion['stop_reason'] == 'normal_return'
        assert completion['process_cap_seconds'] == launch['cap_seconds']
        assert audit['passed'] and summary['audit_passed']
        assert audit['binary_sha256'] == admission['production_PE_SHA']
        assert not progress['disabled'] and progress['failure_count'] == 0 and not progress['qualification_fault_injected']
        assert 0 < native_end['complete_seconds_until_native_end'] <= postexit['complete_seconds_until_audit_end'] < 1800
        samples = [json.loads(s) for s in (d / 'samples.jsonl').read_text().splitlines()]
        assert samples and all(not x['formal_endpoint'] for x in samples)
        assert all(b['process_seconds'] - a['process_seconds'] >= 60 for a,b in zip(samples,samples[1:]))
        for seq, observation in enumerate(observations, 1):
            checked = receipts.receipt(d / 'journal' / f'event_{seq}.commit', observation['first_observed_seconds'], 1800)
            assert checked == observation, ('receipt differs', arm, seq)
        life = paid.event_lifecycle(observations)
        assert life['declared'] == life['started'] == life['returned'] and not life['not_started']
        assert not life['pending_declaration_ids'] and not life['unreturned_ids']
        identity = life['identity']
        assert identity['input_sha256'] == p['input_sha256']
        assert (identity['V'],identity['M'],identity['T'],identity['lambda'],identity['pickup_seconds'],identity['drop_seconds']) == (
            p['V'],p['M'],p['T_seconds'],p['lambda'],p['pickup_seconds'],p['drop_seconds'])
        assert identity['analytical_full_domain_lower_bound'] == 0
        if arm == 'P-S':
            j = paid.ps_journal(ROOT,p,d); ep = paid.paid_endpoint(ROOT,launch,ident,d,j)
            assert ep['lifecycle']['branch'] == 'ONE_STARTED_RETURNED_ORIGINAL_COMPACT_MIP'
            start = dict(ep['Start'], arm=arm, API=read(d / 'native.log.round112.start.json')['API'])
            assert start['columns'] == 13326 and start['rows'] == 35567
            assert start['API'] == 'GRBsetdblattrarray(Start)'
            assert read(d / 'native.log.round112.start.json')['submission_count'] == 1
            assert start['all_native_columns_checked'] and start['all_original_numeric_rows_checked']
            adoption = read(d / 'native.log.round112.native.json')
            assert adoption['exact_vector_observed_in_mipsol'] == adoption['integer_vector_observed_in_mipsol'] == 1
            assert adoption['Optimize_count'] == 1 and adoption['optimize_return_code'] == 0
            start['native_adoption'] = adoption; start_records.append(start)
        else:
            j = core.evidence.journal(ROOT,p,d)
            j['return_sequences'] = {q['payload']['call']:q['payload']['sequence'] for q in observations if q['payload']['kind']=='returned'}
            j['return_available'] = {q['payload']['call']:q['effective_available_seconds'] for q in observations if q['payload']['kind']=='returned'}
            ep = core.endpoint(ROOT,launch,ident,d,j,False)
        for key in ['U','L','gap']:
            assert abs(ep['arm'][key] - audit['endpoint'][key]) <= 1e-7
            assert audit['endpoint'][key] == summary['endpoint'][key]
        assert ep['arm']['certificate'] == audit['endpoint']['certificate'] == summary['endpoint']['certificate']
        for q in observations:
            e = q['payload']
            if e['kind'] == 'witness':
                w = core.full_fleet(ROOT,p,e)
                assert w['complete_fleet_vehicles'] == p['M']
        model_paths = [d/'compact.lp'] if arm in ['P-GRB','P-S'] else sorted((d/'external/models').glob('*.lp'))
        parsed = {}; bysha = {}
        for path in model_paths:
            contract, model = core.model_contract(ROOT,p,path,arm)
            models.append(dict(arm=arm,**contract));parsed[contract['SHA']] = model;bysha[contract['SHA']] = path
        for call_id, call in j['calls'].items():
            assert call['settings'] == paid.SETTINGS
            if not call['native_preconditions']:
                # Original LP relaxations do not claim MILP callback-bound
                # prerequisites; their separate returned LP ledger is checked.
                assert arm in ['ENS-C','M-B'] and '_lp.gurobi.log' in call['native_log_path']
                assert not any(b['call']==call_id for b in j['bounds'])
            assert sha(core.portable(ROOT,call['model_path'])) == call['model_sha256']
            scope = core.model_scope_contract(call, parsed[call['model_sha256']], p)
            models.append(dict(arm=arm,call=call_id,model_SHA=call['model_sha256'],actual_scope=scope))
        controller = ep['controller']
        proofs = controller['controller_native']
        lp_proofs = [q for q in proofs if q['solve_kind']=='LP']
        assert len(lp_proofs) == len(controller['controller_LP_status'])
        lp_status = {q['native_log']:s for q,s in zip(lp_proofs,controller['controller_LP_status'])}
        if arm in ['P-GRB','P-S']:
            proofs = [dict(model_sha256=sha(d/'compact.lp'),solve_kind='MIP',native_status='OPEN',native_log=str(d/'native.log'))]
        for proof in proofs:
            model = parsed[proof['model_sha256']]; log = core.portable(ROOT,proof['native_log']); text = log.read_text(encoding='utf-8')
            size = re.search(r'Optimize a model with (\d+) rows, (\d+) columns',text)
            assert size and (int(size[1]),int(size[2])) == (len(model['rows']),len(model['order']))
            counts = collections.Counter(model['types'].values()); native_types = None
            if proof['solve_kind'] != 'LP':
                match = re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)',text)
                assert match
                native_types = dict(C=int(match[1]),I=int(match[2])-int(match[3]),B=int(match[3]))
                assert native_types == {k:counts.get(k,0) for k in ['C','I','B']}
                if proof['native_status'] == 'OPTIMAL':assert 'Optimal solution found' in text
            elif proof['native_status'] == 'OPTIMAL':
                objective = re.findall(r'Optimal objective\s+([-+0-9.eE]+)',text);assert objective
                status = lp_status[proof['native_log']]
                if int(status['terminal_valid']):assert int(status['optimal']) and core.close(float(objective[-1]),float(status['lower_bound']))
            elif proof['native_status'] == 'INFEASIBLE':assert 'Infeasible model' in text
            native_logs.append(dict(arm=arm,model_SHA=proof['model_sha256'],solve_kind=proof['solve_kind'],rows=int(size[1]),
                columns=int(size[2]),actual_native_types=native_types,path=log.relative_to(ROOT).as_posix(),SHA=sha(log)))
        submitted = [(path,read(path)) for path in sorted((d/'external/native_logs').glob('*.round68.start.json')) if read(path).get('submitted')]
        for digest in sorted({m['model_sha256'] for _,m in submitted}):
            assert digest in bysha
            audited_starts = core.start_reader.audit_model(bysha[digest],[(path,m) for path,m in submitted if m['model_sha256']==digest],
                'm-binary' if arm=='M-B' else 'off')
            start_records.extend(dict(arm=arm,**q) for q in audited_starts)
        if arm in ['ENS-C','M-B']:
            assert ep['cover']['complete_coverage']
            assert ep['cover']['all_relevant_closed'] == ep['arm']['certificate']
            assert audit['current_saved_model_contracts']
        if arm in ['P-GRB','P-S']:
            roundtrip = parameters.parameter_readback(result,require_call=True,arm='P-GRB')
            assert result['gurobi_lifecycle_valid'] and result['gurobi_solver_finalization_reached']
            assert result['gurobi_optimize_count'] == j['started'] == j['returned'] == 1
        else:roundtrip = audit['parameter_readback']
        record = dict(number=launch['number'],id=launch['id'],arm=arm,process_returncode=0,stop_reason='normal_return',
            process_wall_seconds=completion['process_wall_seconds'],native_end_receipt=native_end,
            necessary_postexit_audit_receipt=postexit,necessary_audit_passed=True,raw_claimed_endpoint=audit['endpoint'],
            internally_reconstructed_endpoint=ep['arm'],physical=ep['physical'],native_declared=life['declared'],
            actual_Optimize=life['started'],native_returned=life['returned'],explicit_not_started=0,
            parameter_readback=roundtrip,complete_scope_cover=ep['cover'],progress=progress,
            full_arm_performance_qualified=arm!='P-GRB')
        if arm != 'P-GRB':
            whole = read(d/'whole_arm_receipt.json')
            assert whole['number']==launch['number'] and whole['arm']==arm and whole['cap_seconds']==1800
            assert whole['includes_admission_identity_startup_native_outputs_necessary_postexit_audit_crosscheck_metrics']
            assert whole['metrics_written_before_whole'] and whole['progress_publication_receipt_written_before_whole']
            assert whole['progress_receipt_SHA']==sha(d/'progress_publication_receipt.json')
            assert (d/'audit_execution_metrics.json').exists()
            assert postexit['complete_seconds_until_audit_end'] <= whole['complete_seconds'] <= 1800
            after = read(OUT/'fees/main01'/f"{launch['number']:02d}_after.json")
            assert after['completed_and_audited'] and after['whole_arm_receipt_SHA']==sha(d/'whole_arm_receipt.json')
            record.update(whole_arm_receipt=whole,qualified_endpoint=ep['arm'],complete_seconds=whole['complete_seconds'],
                state='QUALIFIED_COMPLETE_WHOLE')
        else:
            assert not (d/'whole_arm_receipt.json').exists()
            assert not (d/'audit_execution_metrics.json').exists()
            assert not (OUT/'fees/main01/04_after.json').exists()
            assert '--round112-ens-start-compact' not in launch['command']
            assert result['gurobi_hga_start_requested'] is False
            assert not (d/'result.json.round112.startup.json').exists()
            assert 'Loaded user MIP start' not in (d/'native.log').read_text(encoding='utf-8')
            record.update(whole_arm_receipt=None,qualified_endpoint=None,complete_seconds=None,
                state='NORMAL_RETURN_POSTVALIDATION_FAILED_NO_WHOLE',raw_numbers_retained_without_performance_promotion=True)
        reviewed.append(record); endpoint_objects[arm] = ep; journals[arm] = j
        for member in d.rglob('*'):
            if member.is_file():bind(member)

    p = ident['launches'][0]['panel']
    same_H = compare_H(ROOT,p,{l['arm']:core.portable(ROOT,l['destination']) for l in ident['launches'][:3]})
    assert len(same_H['comparisons'])==2 and all(q['qualified'] for q in same_H['comparisons'])
    assert all(a['complete'] and a['seed_ids']==list(range(1,26)) for a in same_H['arms'].values())
    for a in same_H['arms'].values():assert a['physical']['complete_fleet_vehicles']==p['M']
    zero = endpoint_objects['ENS-C']['physical']; instance = core.evidence.instance(ROOT,p)
    assert zero['F']==zero['G']==zero['P']==0 and zero['Y']==instance['D']
    assert zero['complete_fleet_vehicles']==p['M']==4
    assert p['lambda']>=0 and all(x>=0 for x in instance['w'][1:])
    zero_floor = dict(ENS_C_own_full_physical_fleet=zero,full_fleet_vehicles=p['M'],Q_vector=p['Q_vector'],
        original_input_SHA=p['input_sha256'],lambda_value=p['lambda'],all_weights_nonnegative=True,
        independently_recomputed_F=0,independent_original_objective_floor=0,independent_zero_certificate=True,
        cold_fleet_or_bound_imported_into_ENS=False)
    cold_d = core.portable(ROOT,ident['launches'][3]['destination']); cold = endpoint_objects['P-GRB']; j = journals['P-GRB']
    returned = core.cold_returned_bound(ROOT,cold_d,j,cold['result'])
    call = next(iter(j['calls'].values()))
    assert sha(cold_d/'compact.lp')==sha(OUT/'campaign/reference/G50-C1/original.lp')==p['reference']['canonical_sha256']
    assert call['full_original'] and call['native_preconditions']
    assert call['model_scope']=='complete_original_compact_milp'
    assert call['lower_g']==0 and call['upper_g']==call['gmax']==.98
    assert returned['L']==cold['result']['native_mip_best_bound']==2.2806283239409983e-6
    assert returned['L']>zero['F']+1e-7
    rejected = False
    try:core.evidence.bound(call,returned['L'],[zero])
    except AssertionError:rejected = True
    assert rejected, 'full-original bound must fail against independently legal same-role zero fleet'
    event53 = read(cold_d/'journal/event_53.json')
    assert event53['global_available']==1 and event53['inconsistent']==0 and event53['reason']=='full_original_native_callback'
    assert event53['global_bound']==returned['L']
    event68 = read(cold_d/'journal/event_68.json')
    assert event68['kind']=='witness' and 'F' not in event68
    frozen_failed = max(r['raw_claimed_endpoint']['L'] for r in reviewed)>min(r['raw_claimed_endpoint']['U'] for r in reviewed)+1e-7
    assert frozen_failed
    failure = (OUT/'fees/main01/failure.txt').read_text()
    assert "max(r['endpoint']['L'] for r in same)<=min(upper)+1e-7" in failure and 'AssertionError' in failure
    contradiction = dict(state='NORMAL_NATIVE_RETURN_AUTHORITY_POSTVALIDATION_FAILED',own_necessary_audit_passed=True,
        cold_call=call,linked_returned_native_bound=returned,retained_callback_event53=event53,
        native_returned_status=cold['result']['gurobi_status'],cold_own_recomputed_physical_F=cold['physical']['F'],
        same_role_independent_ENS_own_zero_F=zero['F'],objective_floor=0,tolerance=1e-7,
        strict_excess_over_zero=returned['L']-zero['F'],excess_beyond_frozen_tolerance=returned['L']-zero['F']-1e-7,
        frozen_cross_arm_check_failed=True,independent_full_original_bound_witness_check_rejected=True,
        global_callback_flag_is_own_journal_local=True,authority_qualification='REJECTED',
        whole_receipt_missing=True,metrics_missing=True,qualified_performance_endpoint=None,
        first_three_qualified_endpoints_unchanged=True,cold_repair_clipping_or_bound_downgrade_performed=False,
        algorithm_LOSS_assigned=False,unknown_numerical_or_hidden_branch_root_cause='UNKNOWN',
        earlier_event68_serialized_F='ABSENT_UNKNOWN_AT_MANAGEMENT_READ',offline_current_fleet_replay_now_authorized=True)
    fees = []
    for launch_path in sorted((OUT/'fees').glob('*/launch.json')):
        launch = read(launch_path); receipt = read(launch_path.parent/'receipt.json'); pending = read(launch_path.parent/'pending_exit_receipt.json')
        assert receipt['actual_exit_observed'] and receipt['necessary_trailer_complete']
        assert receipt['qualification']==launch['qualification'] and receipt['exit_code']==pending['exit_code']
        assert receipt['outer_seconds_upper']>=receipt['outer_seconds_lower']>0
        assert not receipt['nested_native_seconds_added']
        assert launch['conservative_process_starts']==launch['declared_native_children']+1
        assert receipt['actual_native_children']<=launch['declared_native_children']
        helper_differences = sorted(name for name in set(launch['helpers'])|set(candidate['helpers'])
            if launch['helpers'].get(name)!=candidate['helpers'].get(name))
        if launch_path.parent.name in ['cli01','main01']:assert not helper_differences
        fees.append(dict(label=launch_path.parent.name,qualification=launch['qualification'],
            conservative_process_starts=launch['conservative_process_starts'],actual_native_children=receipt['actual_native_children'],
            exit_code=receipt['exit_code'],outer_seconds_lower=receipt['outer_seconds_lower'],outer_seconds_upper=receipt['outer_seconds_upper'],
            actual_exit_observed=True,nested_native_seconds_added=False,
            helper_differences_from_final_admitted_closure=helper_differences))
        for path in launch_path.parent.iterdir():
            if path.is_file():bind(path)
    assert len(fees)==7
    totals=dict(conservative_process_starts=sum(q['conservative_process_starts'] for q in fees),
        outer_seconds_upper=sum(q['outer_seconds_upper'] for q in fees),
        qualification_starts=sum(q['conservative_process_starts'] for q in fees if q['qualification']),
        qualification_outer_seconds_upper=sum(q['outer_seconds_upper'] for q in fees if q['qualification']),
        formal_conservative_starts=sum(q['conservative_process_starts'] for q in fees if not q['qualification']),
        formal_outer_seconds_upper=sum(q['outer_seconds_upper'] for q in fees if not q['qualification']),
        all_fees_closed=True,failed_slots_refunded=False)
    assert totals['conservative_process_starts']==15 and totals['qualification_starts']==10 and totals['formal_conservative_starts']==5
    assert abs(totals['outer_seconds_upper']-6112.501114845276)<1e-9
    assert abs(totals['qualification_outer_seconds_upper']-470.4929027557373)<1e-9
    assert {q['label'] for q in fees if q['exit_code']}=={'finite01','post01','main01'}
    assert next(q for q in fees if q['label']=='main01')['actual_native_children']==4
    assert next(q for q in fees if q['label']=='main01')['exit_code']==1
    assert totals['conservative_process_starts']<=28 and totals['outer_seconds_upper']<=26000
    assert totals['qualification_starts']<=12 and totals['qualification_outer_seconds_upper']<=1200
    unstarted=[]
    for launch in ident['launches'][4:]:
        d=core.portable(ROOT,launch['destination']);assert not d.exists()
        assert not any(q['number']==launch['number'] for q in summaries+processes)
        unstarted.append(dict(number=launch['number'],id=launch['id'],arm=launch['arm'],cap_seconds=3600,
            state='FIXED_UNSTARTED',actual_Optimize=0,qualified_endpoint=None))
    clock_path=OUT/'inherited_r112/clock_manifest.json'; clock=read(clock_path)
    assert bind(clock_path)==admission['inherited_clock_manifest_SHA']
    assert len(clock['files'])==146 and len(clock['arms'])==12 and clock['old_qualified']==12
    assert not clock['old_raw_reaudited'] and not clock['original_clock_adjusted'] and clock['old_partial13_excluded']
    for name,digest in clock['files'].items():assert bind(OUT/'inherited_r112'/name)==digest,name
    assert bind(OUT/'inherited_r112/dependency_manifest.json')==admission['inherited_dependency_manifest_SHA']
    for path in [OUT/'review/performance_admission.json',OUT/'production_identity.json',OUT/'protocol.json',OUT/'input_manifest.json',
        OUT/'campaign/summary.jsonl',OUT/'campaign/processes.jsonl',Path(__file__)]:bind(path)
    save('new_raw.json',dict(arms=reviewed,models=models,current_native_log_type_and_size_readbacks=native_logs,
        current_actual_Start_API_readbacks=start_records,actual_Optimize=sum(q['actual_Optimize'] for q in reviewed),
        actual_returned=sum(q['native_returned'] for q in reviewed)))
    save('same_H.json',same_H)
    save('zero_floor.json',zero_floor)
    save('cold_contradiction.json',contradiction)
    save('fees.json',dict(rows=fees,totals=totals))
    save('unstarted.json',unstarted)
    save('bindings.json',bindings)
    report=dict(schema='round113-independent-postformal-review-v1',reviewer='/root/independent_review',
        signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='BLOCKED_FINITE_INSUFFICIENT',
        candidate_identity_SHA=sha(OUT/'candidate_identity.json'),campaign_identity_SHA=sha(OUT/'campaign/identity.json'),
        performance_admission_SHA=sha(OUT/'review/performance_admission.json'),production_PE_SHA=admission['production_PE_SHA'],
        DLL_SHA=admission['DLL_SHA'],source_files_checked=206,performance_helpers_checked_unchanged=42,
        admitted_offline_reader_SHA=admission['offline_reader_SHA'],new_reader_not_signed_in_this_review=True,
        actual_formal_children=4,qualified_new_full_arm_endpoints=3,normal_return_but_authority_failed=1,
        G100_fixed_unstarted=4,actual_formal_Optimize=sum(q['actual_Optimize'] for q in reviewed),
        actual_formal_returned=sum(q['native_returned'] for q in reviewed),native_call_statistics_include_cold_authority_failure=True,
        first_three_new_endpoint_checks_pass=True,first_three_whole_cap_checks_pass=True,
        complete_H25_trace_fleet_inventory_checks_pass=True,current_P_S_full_native_Start_checks_pass=True,
        current_ENS_MB_saved_original_model_scope_cover_and_Start_checks_pass=True,
        ENS_own_zero_physical_fleet_and_independent_floor0_pass=True,cold_full_original_identity_parameters_returned_log_pass=True,
        frozen_cross_arm_L_versus_min_own_U_check='FAIL',whole_for_cold_generated=False,
        numerical_or_hidden_branch_root_cause='UNKNOWN',algorithm_LOSS_assigned=False,
        retained_old12_authority_files_hashed=146,old_LP_matrices_reparsed=0,old_original_clocks_changed=False,
        total_fees=totals,budget_exhausted=False,no_retries_or_G100_authorized_by_this_review=True,
        reviewer_native_starts=0,reviewer_Optimize=0,reviewer_compiler_starts=0,reviewer_qualification_or_fixture_starts=0,
        performance_or_raw_mutations=0,review_engineering_seconds=time.perf_counter()-started,
        output_bindings={name:sha(DEST/name) for name in ['new_raw.json','same_H.json','zero_floor.json','cold_contradiction.json','fees.json','unstarted.json','bindings.json']},
        limitations=['Cold raw claimed U/L/gap remain forensic evidence and are not a qualified performance endpoint.',
            'Global_available=1/inconsistent=0 records own-journal qualification, not a successful cross-arm authority gate.',
            'No new solver reproduction or native numerical diagnosis was performed; hidden causes remain unknown.',
            'G100-R2 native exposure and all four endpoints remain unobserved; no algorithmic LOSS is inferred.',
            'The admitted offline reader identity is preserved separately; its later pure offline reporting delta needs final review.',
            'Public export, empty-root restoration and final whole-goal review are pending separate independent review.'])
    save('report.json',report)
    print(json.dumps({k:report[k] for k in ['decision','qualified_new_full_arm_endpoints','normal_return_but_authority_failed',
        'G100_fixed_unstarted','actual_formal_Optimize','review_engineering_seconds']},ensure_ascii=False))

if __name__=='__main__':main()
