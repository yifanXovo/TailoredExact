"""Independent offline review of already executed Round113 qualification.

Never starts qualification, a subprocess, native code, a compiler, or fixtures.
Reads current H100 raw and bounded retained R112 authority. Output is review
engineering, not a new qualification or performance observation.
"""
from pathlib import Path
import collections, csv, datetime, hashlib, json, math, sys, time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round113'
sys.path.insert(0, str(ROOT / 'scripts'))
import round108_reader as core
import round113_audit as paid
from compare_round112_startup import compare as compare_H

csv.field_size_limit(64 * 1024 * 1024)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def csvrows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def main(destination):
    started = time.perf_counter()
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=False)
    production = read(OUT / 'production_identity.json')
    candidate = read(OUT / 'candidate_identity.json')
    formal = read(OUT / 'campaign/identity.json')
    qualification = read(OUT / 'qualification/cli01/identity.json')
    protocol = read(OUT / 'protocol.json')
    manifest = read(OUT / 'input_manifest.json')
    bindings = {}

    def bind(path):
        path = Path(path)
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        digest = sha(path)
        bindings[key] = digest
        return digest

    PE_SHA = 'a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8'
    DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
    assert sha(ROOT / 'build/research/round113-inherited/ExactEBRP.exe') == PE_SHA
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll')) == DLL_SHA
    assert production['measured_source_commit'] == 'd0014a7163e3996fe120471420e56b089c9715ae'
    assert not production['production_recompiled']
    assert len(production['source_bindings']) == 206
    for name, digest in production['source_bindings'].items():
        assert bind(ROOT / name) == digest, name
    for identity in (candidate, formal, qualification):
        assert identity['source_bindings' if identity is candidate else 'source_hashes'] == production['source_bindings']
        assert identity['production_PE_SHA' if identity is candidate else 'candidate_binary_sha256'] == PE_SHA
        assert identity['DLL_SHA' if identity is candidate else 'dll_sha256'] == DLL_SHA
        assert identity['helpers'] == candidate['helpers']
    for name, digest in candidate['helpers'].items():
        assert bind(ROOT / name) == digest, name
    assert len(candidate['helpers']) == 42
    assert candidate['campaign_identity_SHA'] == bind(OUT / 'campaign/identity.json')
    assert candidate['qualification_campaign_identity_SHA'] == bind(OUT / 'qualification/cli01/identity.json')
    assert formal == read(OUT / 'fixed_manifest.json')
    assert candidate['protocol_SHA'] == bind(OUT / 'protocol.json')
    assert candidate['input_manifest_SHA'] == bind(OUT / 'input_manifest.json')
    assert formal['prereg_sha256'] == qualification['prereg_sha256'] == sha(OUT / 'protocol.json')
    assert candidate['full_argv'] == [entry['command'] for entry in formal['launches']]
    assert len(formal['launches']) == 8
    assert sum(entry['cap_seconds'] for entry in formal['launches']) == 21600
    assert not (OUT / 'campaign/summary.jsonl').exists()
    assert not list((OUT / 'campaign/raw').glob('*'))
    assert protocol['total_start_limit'] == 28 and protocol['total_outer_seconds_limit'] == 26000
    assert protocol['qualification_start_limit'] == 12 and protocol['qualification_outer_seconds_limit'] == 1200
    assert protocol['primary_benchmark'] == 'cold P-GRB' and protocol['default'] == 'ENS-C'
    expected = [
        ('G50-C1', 'M-B', 1800), ('G50-C1', 'ENS-C', 1800),
        ('G50-C1', 'P-S', 1800), ('G50-C1', 'P-GRB', 1800),
        ('G100-R2', 'P-GRB', 3600), ('G100-R2', 'ENS-C', 3600),
        ('G100-R2', 'P-S', 3600), ('G100-R2', 'M-B', 3600)]
    assert [(q['id'], q['arm'], q['cap_seconds']) for q in formal['launches']] == expected
    expected_inputs = {
        'G50-C1': '5740d09bf218cf6921cee6e60198f673151d6426fbcb0840259647129f3c4ed5',
        'G100-R2': 'b3f3a1270f062e9f3af64d5b00392f51821bb775818edc6cd383fcd62550618f',
        'H100': '04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71'}
    for launch in formal['launches'] + qualification['launches']:
        p = launch['panel']; command = launch['command']
        assert bind(ROOT / p['input_path']) == p['input_sha256'] == expected_inputs[p['id']]
        assert command[0] == str(ROOT / 'build/research/round113-inherited/ExactEBRP.exe')
        def option(name):
            assert command.count(name) == 1, name
            return command[command.index(name) + 1]
        assert option('--input') == p['input_path']
        assert int(option('--T')) == p['T_seconds']
        assert float(option('--lambda')) == .15
        assert option('--pickup-time') == option('--drop-time') == '60'
        assert int(option('--process-wall-time-limit')) == launch['cap_seconds']
        assert int(option('--time-limit')) == launch['cap_seconds'] - 6
        assert option('--process-shutdown-margin') == '30'
        assert option('--threads') == option('--mip-threads') == '1'
        assert option('--gurobi-seed') == '0' and option('--gurobi-presolve') == '-1'
        assert ('--round112-ens-start-compact' in command) == (launch['arm'] == 'P-S')
        assert ('--round98-state-service' in command) == (launch['arm'] == 'M-B')
        if launch['arm'] == 'M-B':
            assert option('--round98-state-service') == 'm-binary'
        if launch['arm'] in ('ENS-C', 'M-B'):
            assert option('--algorithm-preset') == 'research-round83-vds-equal-net-exchange'
        assert '--round100-continuous-quantities' not in command
    assert len(qualification['launches']) == 4
    assert [l['arm'] for l in qualification['launches']] == ['P-GRB', 'P-S', 'ENS-C', 'M-B']
    assert all((l['panel']['V'], l['panel']['M'], l['panel']['Q_vector'], l['panel']['T_seconds'], l['cap_seconds']) ==
               (20, 2, [13, 21], 5100, 120) for l in qualification['launches'])

    fee_rows = []
    for path in sorted((OUT / 'fees').glob('*/launch.json')):
        launch = read(path); receipt = read(path.parent / 'receipt.json')
        pending = read(path.parent / 'pending_exit_receipt.json')
        assert launch['qualification'] and receipt['qualification']
        assert receipt['actual_exit_observed'] and receipt['necessary_trailer_complete']
        assert receipt['outer_seconds_upper'] >= receipt['outer_seconds_lower'] > 0
        assert receipt['exit_code'] == pending['exit_code']
        assert not receipt['nested_native_seconds_added']
        fee_rows.append(dict(label=path.parent.name, starts=launch['conservative_process_starts'],
            outer_seconds_upper=receipt['outer_seconds_upper'], outer_seconds_lower=receipt['outer_seconds_lower'],
            exit_code=receipt['exit_code'], actual_children=receipt['actual_native_children']))
        for member in path.parent.glob('*'):
            if member.is_file(): bind(member)
    assert len(fee_rows) == 6
    assert sum(f['starts'] for f in fee_rows) == 10
    outer = sum(f['outer_seconds_upper'] for f in fee_rows)
    assert abs(outer - 470.4929027557373) < 1e-10
    assert {f['label'] for f in fee_rows if f['exit_code']} == {'finite01', 'post01'}
    assert sum(f['actual_children'] for f in fee_rows) == 4
    assert 28 - sum(f['starts'] for f in fee_rows) >= 10
    assert 26000 - outer >= 21600 + 240

    sharing = read(OUT / 'qualification/finite01/sharing/receipt.json')
    assert sharing['os_name'] == 'nt' and sharing['actual_CreateFileW']
    assert sharing['share_READ'] and sharing['share_WRITE'] and not sharing['share_DELETE']
    assert sharing['old_replace_failure']['winerror'] == 5
    assert sharing['new_current_arm']['failure_count'] == sharing['new_current_arm']['attempts'] == 1
    assert sharing['new_current_arm']['disabled'] and not sharing['next_arm']['disabled']
    assert sharing['no_unique_historical_handle_holder_claim'] and sharing['non_filesystem_errors_propagate']
    mocks = read(OUT / 'qualification/finite01/supervisor/receipt.json')
    assert mocks['supervisor_source_SHA'] == sha(ROOT / 'scripts/round90_lp_g_g3.py')
    assert mocks['extractor_SHA'] == sha(ROOT / 'scripts/round113_campaign.py')
    assert len(mocks['cases']) == 7 and all(case['passed'] for case in mocks['cases'])
    assert not mocks['actual_OS_child_execution'] and not mocks['native_execution']
    normal, failed = [next(c for c in mocks['cases'] if c['case'] == name) for name in ['normal', 'display_failure']]
    assert normal['sample_seconds'] == failed['sample_seconds']
    assert normal['memory_check_seconds'] == failed['memory_check_seconds']
    assert normal['disk_check_seconds'] == failed['disk_check_seconds']
    assert all(c['child']['affinity_restored'] for c in mocks['cases'])
    life = read(OUT / 'qualification/finite03/lifecycle/receipt.json')
    assert life['no_extra_Optimize'] and not life['actual_deadline_cancellation_executed']
    assert len([q for q in life['cases'] if q.get('passed')]) == 3
    assert len([q for q in life['cases'] if q.get('rejected')]) == 13
    declared = next(q for q in life['cases'] if q.get('case') == 'declaration_without_cancel_and_return')
    active = next(q for q in life['cases'] if q.get('case') == 'actual_native_activity_without_return')
    assert declared['actual_Optimize'] == 'UNKNOWN_PENDING_DECLARATION'
    assert active['actual_Optimize'] == 1
    assert not declared['normal_no_Optimize_eligible'] and not active['normal_no_Optimize_eligible']
    for q in life['cases']:
        if q.get('passed'):
            assert q['synthetic_fixture'] and q['offline_endpoint']['native_Optimize'] == 0
            assert q['lifecycle']['backend_exposure'] == 'BACKEND_NOT_EXPOSED'

    compatibility = read(OUT / 'qualification/finite02/compatibility/receipt.json')
    assert len(compatibility['qualified12']) == 12
    assert compatibility['evaluable_old_pairs'] == 18 and compatibility['missing_old_pairs'] == 12
    assert compatibility['signed_L48_PS_gap'] == -9.43689570931383e-16
    assert compatibility['old_LP_matrices_reparsed'] == 0
    assert compatibility['partial13_endpoint_rejected']
    assert compatibility['performance_times_from_original_receipts_only']
    for row in compatibility['qualified12']:
        assert max(abs(v) for v in row['original_necessary_audit_to_signed_final_reader_differences'].values()) <= 1e-7
    small = read(OUT / 'qualification/finite02/compatibility/small_restore_receipt.json')
    assert small['empty_root_created'] and small['CSV_field_limit'] == 67108864
    assert small['source_SHA'] == small['restored_SHA'] and small['Optimize'] == 0

    reviewed = []
    start = None
    core.start_reader.ROOT = ROOT
    for launch in qualification['launches']:
        d = core.portable(ROOT, launch['destination']); p = launch['panel']
        rawlaunch = read(d / 'launch.json')
        assert rawlaunch['command'] == launch['command']
        completion = read(d / 'completion.json'); audit = read(d / 'audit.json')
        whole = read(d / 'whole_arm_receipt.json'); post = read(d / 'postexit_audit_receipt.json')
        native = read(d / 'native_end_receipt.json'); progress = read(d / 'progress_publication_receipt.json')
        assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
        assert 0 < native['complete_seconds_until_native_end'] <= post['complete_seconds_until_audit_end'] <= whole['complete_seconds'] <= 120
        assert whole['metrics_written_before_whole'] and whole['progress_publication_receipt_written_before_whole']
        assert whole['progress_receipt_SHA'] == sha(d / 'progress_publication_receipt.json')
        assert audit['passed']
        samples = [json.loads(row) for row in (d / 'samples.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(samples) == 2
        assert samples[1]['process_seconds'] - samples[0]['process_seconds'] >= 60
        assert all(not q['formal_endpoint'] for q in samples)
        if launch['arm'] == 'P-S':
            j = paid.ps_journal(ROOT, p, d)
            ep = paid.paid_endpoint(ROOT, launch, qualification, d, j)
            start = ep['Start']
            assert j['declared'] == j['started'] == j['returned'] == 1 and j['not_started'] == 0
            assert progress['qualification_fault_injected'] and progress['sharing_mask'] == 3
            assert progress['failure_count'] == progress['attempts'] == progress['disabled_calls_skipped'] == 1
            assert progress['disabled'] and progress['successes'] == 0
            failure = progress['first_failure']
            assert failure['winerror'] == 5 and failure['errno'] == 13 and failure['failure_stage'] == 'os.replace'
            assert core.portable(ROOT, failure['path']) == d.parents[1] / 'runtime_status.json'
            assert progress['holder_process'] == read(OUT / 'fees/cli01/launch.json')['wrapper_pid']
            marker = read(d / 'process_start_marker.json')
            assert marker['unix_seconds'] <= failure['failed_unix'] <= completion['ended_unix']
            assert 0 <= failure['process_seconds'] < completion['process_wall_seconds']
            assert start['columns'] == 1591 and start['rows'] == 3689
            assert start['all_native_columns_checked'] and start['all_original_numeric_rows_checked']
        else:
            j = core.evidence.journal(ROOT, p, d)
            observations = read(d / 'observations.json')
            j['return_sequences'] = {q['payload']['call']: q['payload']['sequence'] for q in observations if q['payload']['kind'] == 'returned'}
            j['return_available'] = {q['payload']['call']: q['effective_available_seconds'] for q in observations if q['payload']['kind'] == 'returned'}
            ep = core.endpoint(ROOT, launch, qualification, d, j, False)
            assert not progress['disabled'] and progress['failure_count'] == 0
            assert progress['successes'] == 2
        assert j['started'] == j['returned']
        for key in ('U', 'L', 'gap'):
            assert abs(ep['arm'][key] - audit['endpoint'][key]) <= 1e-7
        assert ep['arm']['certificate'] == audit['endpoint']['certificate']
        reviewed.append(dict(number=launch['number'], arm=launch['arm'],
            complete_seconds=whole['complete_seconds'], endpoint=ep['arm'],
            native_Optimize=j['started'], native_returned=j['returned'], display=progress))
        for member in d.rglob('*'):
            if member.is_file(): bind(member)
    assert sum(q['native_Optimize'] for q in reviewed) == 12
    panel = qualification['launches'][0]['panel']
    same = compare_H(ROOT, panel, {l['arm']: core.portable(ROOT, l['destination']) for l in qualification['launches'] if l['arm'] != 'P-GRB'})
    assert len(same['comparisons']) == 2 and all(q['qualified'] for q in same['comparisons'])
    assert all(q['full_H_complete'] and q['semantic_trace_equal'] and q['complete_capacity_assigned_fleet_equal'] and q['final_inventory_equal'] for q in same['comparisons'])
    assert same == read(OUT / 'qualification/post02/H100_same_H.json')
    for value in same['arms'].values():
        assert value['seed_ids'] == list(range(1, 26)) and value['complete']

    for subdir in ['qualification/finite01', 'qualification/finite02', 'qualification/finite03',
                   'qualification/post01', 'qualification/post02']:
        for path in (OUT / subdir).rglob('*'):
            if path.is_file(): bind(path)
    for path in [OUT / 'goal.md', OUT / 'production_identity.json', OUT / 'candidate_identity.json',
                 OUT / 'fixed_manifest.json', ROOT / 'scripts/qualify_round113.py',
                 ROOT / 'scripts/qualify_round113_post.py', ROOT / 'scripts/read_round113.py',
                 ROOT / 'scripts/round113_initialize.py', ROOT / 'scripts/round113_seal.py']:
        bind(path)
    result = dict(schema='round113-independent-offline-admission-audit-v1',
        decision='OFFLINE_QUALIFICATION_EVIDENCE_PASS_PENDING_FINAL_SEAL',
        reviewer='/root/independent_review', signed_at_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        candidate_identity_SHA=sha(OUT / 'candidate_identity.json'), campaign_identity_SHA=sha(OUT / 'campaign/identity.json'),
        qualification_campaign_identity_SHA=sha(OUT / 'qualification/cli01/identity.json'),
        production_PE_SHA=PE_SHA, DLL_SHA=DLL_SHA, production_source_files=206, performance_helpers=42,
        formal_started=0, formal_reserved=dict(starts=10, nominal_seconds=21600, administrative_seconds=240),
        finite_mock_control_cases=7, legal_synthetic_lifecycle_cases=3, illegal_lifecycle_cases=13,
        unresolved_call_counter_cases=2, actual_deadline_cancellation_executed=False,
        actual_Windows_platform=sharing['platform'], actual_Windows_sharing_failure=sharing['old_replace_failure'],
        retained12_endpoint_clock_pair_mapping_pass=True, old_LP_matrices_reparsed=0,
        qualification_actual_CLI=reviewed, P_S_full_Start=start, same_H_comparisons=same['comparisons'],
        same_H_seed_ids=list(range(1,26)), qualification_actual_Optimize=12, qualification_fees=fee_rows,
        qualification_conservative_starts=10, qualification_outer_seconds_upper=outer,
        failed_labels_retained=['finite01', 'post01'], no_failed_slot_refund=True,
        current_reviewer_native_starts=0, current_reviewer_Optimize=0, current_reviewer_compiler_starts=0,
        current_reviewer_qualification_or_fixture_starts=0, current_reviewer_performance_mutations=0,
        current_H100_matrices_reparsed=True, bindings=bindings,
        review_engineering_seconds=time.perf_counter()-started,
        limitations=['Synthetic no-Optimize branches are source-derived fixtures; none was a new native CLI cancellation.',
                    'Mocks execute the real extracted supervisor control flow with in-process fake clock/child; no OS fake child was executed.',
                    'Real sharing failure demonstrates a class of Windows failure; historical unique handle holder remains unknown.',
                    'Finite02 inherits signed old matrix/Start authority and binds old raw SHAs; no old LP matrices are reparsed.',
                    'Post02 reconstruction correctly marks its then-active own fee pending; this audit charges all six final closed fees.',
                    'Final admission still needs the final offline-reader seal and recoverable old12 authority manifest.'])
    (dest / 'raw_audit.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['decision','formal_started','qualification_actual_Optimize','qualification_conservative_starts','qualification_outer_seconds_upper','review_engineering_seconds']}, ensure_ascii=False))

if __name__ == '__main__':
    main(sys.argv[1])
