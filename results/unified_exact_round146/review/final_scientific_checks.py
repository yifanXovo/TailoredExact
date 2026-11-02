"""Finite Round146 closeout review of existing bytes/receipts; no model execution."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round146'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


bound = {}


def bind(path):
    path = Path(path)
    bound[str(path.relative_to(ROOT)).replace('\\', '/')] = sha(path)


manifest = read(OUT / 'candidate_manifest.json')
assert manifest['source_commit'] == '1f470aa5d6a8289347b9d4323764e6e74fa83b2b'
assert sha(manifest['production_PE']) == manifest['production_PE_SHA']
assert sha(manifest['DLL']) == manifest['DLL_SHA']
for path, value in manifest['source_hashes'].items():
    assert sha(ROOT / path) == value, path
for path, value in manifest['objects'].items():
    assert sha(path) == value, path
assert sha(manifest['main_object']['path']) == manifest['main_object']['SHA']
assert set(manifest['compiled_units']) == {'main', 'GurobiBaseline', 'PaperExternalGiniTree'}
publication = read(OUT / 'source_publication.json')
assert publication['production_source_commit'] == manifest['source_commit']
assert publication['PE_SHA256'] == manifest['production_PE_SHA']
assert len(publication['sources']) == len(manifest['source_hashes'])
for source in publication['sources']:
    assert source['actual_compiler_bytes_SHA256'] == manifest['source_hashes'][source['path']]
    assert source['equal_after_CRLF_normalization']
    if source['path'] in manifest['changed_old_source'] + ['include/Round146Research.hpp']:
        blob = subprocess.check_output(['git', 'cat-file', 'blob', source['Git_blob']], cwd=ROOT)
        actual = (ROOT / source['path']).read_bytes()
        assert digest(blob) == source['Git_bytes_SHA256']
        assert blob.replace(b'\r\n', b'\n') == actual.replace(b'\r\n', b'\n')

full = read(OUT / 'reports/full.json')
assert len(full['new_arms']) == 7 and len(full['qualification']) == 1
assert all(r['formal_entered'] for r in full['new_arms'])
assert not full['qualification'][0]['formal_entered']
assert not full['pending'] and not full['failed_qualifications']
assert len(full['pairs']) == 3 and len(full['same_PE_BASE_bridges']) == 1
assert full['all_entered_observed_Native_Optimize'] == full['all_entered_observed_Native_returned'] == 35
assert full['standalone_LP_Optimize_separate'] == 5
assert full['all_entered_preserved']
trajectories = rows(OUT / 'reports/verified_U_trajectories.csv')
all_reports = full['new_arms'] + full['qualification']
assert len({r['destination'] for r in all_reports}) == 8
raw_summary = []
for report in all_reports:
    dest = Path(report['destination'])
    audit = read(dest / 'audit.json')
    endpoint = audit['endpoint']
    close = read(dest / 'verification_closeout.json')
    total = read(dest / 'arm_total_receipt.json')
    producer = read(dest / 'producer_receipt.json')
    launch = read(dest / 'launch.json')
    control = read(dest / 'round146_control_audit.json')
    assert audit['passed'] and audit['implementation_qualified'] and audit['evidence_complete']
    assert not audit['source_rejections'] and audit['raw_bytes_unchanged']
    assert audit['raw_observations_SHA'] == sha(dest / 'observations.json')
    assert audit['producer_seal_SHA'] == sha(dest / 'producer_seal.json')
    assert close['audit_SHA'] == sha(dest / 'audit.json')
    assert close['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
    assert close['native_proof_qualified'] and close['necessary_verification_complete']
    assert total['verification_closeout_SHA'] == sha(dest / 'verification_closeout.json')
    assert total['producer_receipt_SHA'] == sha(dest / 'producer_receipt.json')
    assert total['necessary_verification_complete'] and total['T_total'] == producer['T_produce'] + total['T_verify']
    assert audit['full_H']['complete'] and audit['full_H']['seed_ids'] == list(range(1, 26))
    assert endpoint['H_complete'] and endpoint['performance_eligible'] and endpoint['formal_protocol_qualified']
    assert endpoint['declared_calls'] == endpoint['returned_calls'] == len(audit['model_contracts'])
    assert endpoint['PE_SHA'] == manifest['production_PE_SHA'] and endpoint['DLL_SHA'] == manifest['DLL_SHA']
    assert endpoint['source_commit'] == manifest['source_commit'] and endpoint['stop_reason'] == 'normal_return'
    assert producer['native_stopped_no_reentry'] and producer['required_outputs_closed']
    assert producer['cap_seconds'] == report['cap'] == launch['cap_seconds']
    assert sha(ROOT / launch['panel']['input_path']) == report['input_SHA'] == endpoint['input_SHA']
    assert launch['seed'] == report['seed'] == 0
    command = launch['command']
    assert command[command.index('--threads') + 1] == command[command.index('--mip-threads') + 1] == '1'
    assert command[command.index('--gurobi-seed') + 1] == '0'
    assert command[command.index('--round146-gd') + 1] == ('on' if report['method'] == 'STOCK_GD' else 'off')
    assert ('--round138-stock-rlt' in command) == (report['method'] != 'BASE')
    if not report['certificate']:
        assert endpoint['T_cert'] is None and endpoint['raw_tree_termination_reason'] == 'overall_global_deadline'
        assert report['cap'] - 30 < report['T_produce'] < report['cap']
    for key in ['U', 'L', 'T_produce', 'T_cert', 'certificate', 'relative_gap', 'H_semantic_SHA', 'H_fleet_SHA']:
        assert report[key] == endpoint[key], (report['batch'], report['position'], key)
    for key in ['T_verify', 'T_total']:
        assert report[key] == total[key]
    assert report['signed_gap'] == report['U'] - report['L']
    assert report['external_supported_final_L'] == report['L']
    assert report['new_columns'] == report['paid_source_solves'] == 0
    assert control['PASS'] and control['all_H_Start_physical_scope_quality_lifecycle_inherited']
    assert len(control['models']) == len(audit['model_contracts'])
    assert audit['Start_checks']
    for start in audit['Start_checks']:
        assert sha(ROOT / start['start_path']) == start['start_sha256']
        assert start['ordered_native_columns_checked'] and start['per_column_restored_type_checked']
        assert start['maximum_absolute_residual'] <= 1e-6
        bind(ROOT / start['start_path'])
    for model, checked, call in zip(audit['model_contracts'], control['models'], audit['call_log_bindings']):
        path = ROOT / model['model']['path']
        assert sha(path) == model['model']['SHA'] == checked['model_SHA'] == call['model_SHA']
        assert checked['actual_scope_and_rows'] and checked['new_columns'] == 0
        assert checked['GD_rows'] == report['GD_rows'] and checked['GD_nonzeros'] == report['GD_nonzeros']
        assert checked['stock_rows'] == (0 if report['method'] == 'BASE' else 4)
        assert model['raw_native_preconditions'] == 1 and not model['raw_precondition_reason']
        assert call['journal_returned'] and call['return_code'] == 0
        log = ROOT / call['raw_log']
        assert sha(log) == call['raw_log_SHA']
        assert digest(log.read_bytes()[call['byte_begin']:call['byte_end']]) == call['segment_SHA']
        assert call['parameters']['Threads'] == 1
        assert model['scope']['metadata_scope_is_actual_model_scope']
        bind(path); bind(log)
        if report['method'] == 'STOCK_GD':
            sidecar = Path(str(log) + '.round146.native.json')
            native = read(sidecar)
            assert native in control['Native_audits'] and native['PASS']
            assert native['model_SHA'] == checked['model_SHA'] and native['GD_rows'] == 2
            assert native['source_solves'] == native['new_columns'] == native['Optimize_extra'] == 0
            bind(sidecar)
    if report['method'] == 'STOCK_GD':
        assert control['independent_exact_root_coefficients'] and control['root_generation']['S_lower'] > 0
        assert control['root_generation']['input_SHA'] == report['input_SHA']
        assert len(control['Native_audits']) == endpoint['declared_calls']
    else:
        assert not control['Native_audits'] and control['root_generation'] is None
    if report['formal_entered']:
        events = {x['sequence']: x for x in read(dest / 'observations.json')}
        selected = [x for x in trajectories if x['role'] == report['role'] and x['method'] == report['method']]
        assert selected and abs(float(selected[-1]['U']) - report['U']) < 1e-12
        assert all(float(a['U']) > float(b['U']) for a, b in zip(selected, selected[1:]))
        for row in selected:
            event = events[int(row['sequence'])]
            assert row['committed_event_SHA'] == event['sha256'] == sha(dest / 'journal' / ('event_' + row['sequence'] + '.json'))
            assert row['raw_observation_SHA'] == sha(dest / 'observations.json')
            assert float(row['U']) == event['payload']['objective']
            assert float(row['producer_seconds']) == event['effective_available_seconds']
            assert row['PE_SHA'] == manifest['production_PE_SHA']
    for name in ['audit.json', 'verification_closeout.json', 'arm_total_receipt.json', 'producer_receipt.json', 'producer_seal.json', 'round146_control_audit.json', 'launch.json', 'observations.json']:
        bind(dest / name)
    raw_summary.append(dict(batch=report['batch'], role=report['role'], method=report['method'], calls=endpoint['returned_calls'], Start_checks=len(audit['Start_checks']), GD_rows=report['GD_rows'], GD_nonzeros=report['GD_nonzeros']))

matrices = {}
archived_review_evidence = {}
for batch in ['k20', 'rx20', 'rb35', 'base_bridge']:
    matrix_path = OUT / (batch + '_matrix.json')
    matrix = read(matrix_path)
    previous = read(OUT / 'review' / (batch + '_admission.json'))
    assert previous['decision'] == 'ACCEPT' and previous['independent_nonimplementer_review']
    assert sha(matrix_path) == previous['matrix_SHA']
    assert matrix['candidate_manifest_SHA'] == sha(OUT / 'candidate_manifest.json')
    assert matrix['serial'] and matrix['all_own_H'] and matrix['H_seed'] == 20260626
    assert matrix['Seed_default'] == 0 and matrix['threads'] == 1 and matrix['affinity_mask'] == 4
    for path, value in matrix['helpers'].items():
        assert sha(ROOT / path) == value, path
    for group in matrix['groups']:
        identity_path = OUT / group['group'] / 'identity.json'
        identity = read(identity_path)
        assert sha(identity_path) == group['identity_SHA']
        assert identity['launches'] == [group['launch']] and identity['no_cross_arm_information']
        actual = read(Path(group['launch']['destination']) / 'launch.json')
        assert actual['command'] == group['launch']['command']
        bind(identity_path)
    for rel, value in previous.get('evidence_SHA', {}).items():
        matches = [p for p in [OUT / rel, *list((OUT / 'stages').glob('*/' + Path(rel).name))] if p.exists() and sha(p) == value]
        assert matches, (batch, rel)
        archived_review_evidence[batch + ':' + rel] = str(matches[0].relative_to(OUT)).replace('\\', '/')
    matrices[batch] = sha(matrix_path)
    bind(matrix_path); bind(OUT / 'review' / (batch + '_admission.json'))

lp_reports = read(OUT / 'reports/LP.json')
lp_paths = list((OUT / 'LP').glob('*/result.json'))
assert lp_reports['PASS'] and len(lp_paths) == len(lp_reports['new_LPs']) == 5
for path in lp_paths:
    lp = read(path)
    assert lp in lp_reports['new_LPs'] and lp['qualified'] and lp['LP_Optimize'] == 1
    assert lp['L'] - lp['old_L'] == lp['gain'] > 0 and abs(lp['g'] + lp['weighted_penalty'] - lp['L']) < 1e-12
    assert lp['added_rows'] == 2 and lp['columns'] == lp['before']['columns']
    assert lp['actual_Native_GD_readback'] and lp['complete_objective_constants_old_matrix_support_bounds_cutoff_retained']
    assert lp['baseline_reused']['baseline_Optimize_new'] == 0
    for kind in ['result', 'solution', 'matrix']:
        assert sha(ROOT / lp['baseline_reused'][kind]) == lp['baseline_reused'][kind + '_SHA']
    assert sha(path.parent / 'model.mps') == lp['model_SHA'] == read(path.parent / 'call.json')['model_SHA']
    assert read(path.parent / 'return.json')['Status'] == 2
    assert max(lp['quality'][k] for k in ['ConstrVio', 'BoundVio', 'DualVio']) <= 1e-6
    bind(path); bind(path.parent / 'model.mps'); bind(path.parent / 'call.json'); bind(path.parent / 'return.json')
saved = read(OUT / 'review/independent_saved_point_check.json')
assert saved['PASS'] and saved['Optimize_calls'] == saved['Native_loads'] == 0
assert len(saved['points']) == 4
for point in saved['points']:
    assert not point['saved_values_renormalized']
    if point['point'] == 'joint' and point['role'] != 'K-20-S':
        assert point['violation']['state_low'] < 0 and point['violation']['state_high'] < 0
for rel in ['qualification_exact_rows.json', 'qualification_native_writer.json', 'qualification_units.json', 'qualification/writer/cpp_receipt.json']:
    assert read(OUT / rel)['PASS']
    bind(OUT / rel)
assert len(read(OUT / 'qualification_exact_rows.json')['facts']) == 8
assert read(OUT / 'qualification_native_writer.json')['actual_off_K35_equals_historical_BASE']
assert read(OUT / 'qualification_units.json')['exact_power_of_two_inventory_unit_invariance']

fees = []
for folder in (OUT / 'fees').iterdir():
    fee = read(folder / 'receipt.json')
    assert fee['exit_code'] == 0 and fee['exit_observed'] and not fee['timeout'] and not fee['supervisor_failure']
    assert fee['nested_H_LP_MIP_not_added'] and fee['G1_seconds'] >= 0
    assert fee['outer_seconds'] == fee['G1_seconds'] + fee['separately_reported_seconds']
    fees.append(fee)
    bind(folder / 'launch.json'); bind(folder / 'receipt.json')
fees.sort(key=lambda x: x['start_unix'])
assert all(a['end_unix'] <= b['start_unix'] for a, b in zip(fees, fees[1:]))
cost = read(OUT / 'cost_report.json')
paid = sum(x['G1_seconds'] for x in fees)
assert abs(paid - 7412.7863601001445) < 1e-9
assert abs(paid - cost['charged_new_experiment_seconds']) < 1e-9
assert cost['experiment'] == full['budget'] == read(OUT / 'base_bridge_run_return.json')['budget']
assert not cost['experiment']['unclosed'] and paid < 28800
assert abs(sum(x['separately_reported_seconds'] for x in fees) - cost['build_seconds_separate']) < 1e-9
assert len(list((OUT / 'fees').glob('LP_*'))) == 5 and len(list((OUT / 'fees').glob('qualification_*'))) == 1
for report in all_reports:
    fee = read(OUT / 'fees' / (report['batch'] + '_' + str(report['position']).zfill(3)) / 'receipt.json')
    assert fee['G1_seconds'] == report['fee_outer_seconds'] >= report['T_total']

decision = read(OUT / 'candidate_decision.json')
assert decision['decision'] == 'RESEARCH_ONLY' and decision['study_complete'] and not decision['new_candidate_promoted_to_stable']
assert decision['same_PE_pairs'] == full['pairs'] and decision['same_PE_BASE_bridge'] == full['same_PE_BASE_bridges'][0]
assert decision['formal_positions'] == 7 and decision['short_health_qualifications'] == 1
assert decision['all_entered_Native_Optimize'] == 35 and decision['new_standalone_LP_Optimize'] == 5
assert decision['total_new_experiment_seconds'] == cost['charged_new_experiment_seconds']
for pair in full['pairs']:
    assert pair['same_PE'] and pair['own_H_equal']
    matching = [r for r in full['new_arms'] if r['role'] == pair['role'] and r['method'] in ['STOCK', 'STOCK_GD']]
    for key in ['input_SHA', 'PE_SHA', 'DLL_SHA', 'H_semantic_SHA', 'H_fleet_SHA', 'physical_T', 'lambda_value', 'cap']:
        assert len({r[key] for r in matching}) == 1
bridge = full['same_PE_BASE_bridges'][0]
assert bridge['BASE_U'] < bridge['GD_U'] and bridge['BASE_L'] < bridge['GD_L']
assert abs(100 * (bridge['GD_U'] - bridge['BASE_U']) / bridge['BASE_U'] - decision['observations']['RB35_U_regression_vs_BASE_percent']) < 1e-12
assert abs(100 * bridge['delta_relative_gap'] - decision['observations']['RB35_gap_regression_vs_BASE_percentage_points']) < 1e-12
early = next(r for r in trajectories if r['role'] == 'R-B35-S-T2' and r['method'] == 'BASE' and abs(float(r['producer_seconds']) - 850.641) < .001)
base_last = [r for r in trajectories if r['role'] == 'R-B35-S-T2' and r['method'] == 'BASE'][-1]
gd_last = [r for r in trajectories if r['role'] == 'R-B35-S-T2' and r['method'] == 'STOCK_GD'][-1]
assert abs(float(early['U']) - .362136826572) < 1e-12 and float(early['U']) < bridge['GD_U']
assert abs(float(base_last['producer_seconds']) - 2366.781) < .001
assert abs(float(gd_last['producer_seconds']) - 2217.750) < .001
assert read(OUT / 'stage_base_bridge.json')['decision'] == 'STOP_FULL_EXPANSION_RETAIN_RESEARCH'
assert read(OUT / 'entry_check.json')['PASS']
assert read(OUT / 'entry_check.json')['config_SHA'] == sha(ROOT / 'config/gi_tbc_gd_round146.json')
unchanged = subprocess.check_output(['git', 'diff', manifest['base'], '--name-only', '--', 'config/gi_tbc_round137.json', 'scripts/paper_s2.py', 'config/gi_tbc_rnjp_round145.json', 'scripts/paper_s2_rnjp.py'], cwd=ROOT, text=True)
assert not unchanged.strip()
original = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd='E:/codes/ExactEBRP', text=True)
assert original.strip() == (OUT / 'protected_original_tracked_status.txt').read_text(encoding='utf-8').strip()
for name in ['goal.md', 'candidate_manifest.json', 'candidate_selection.json', 'candidate_decision.json', 'cost_report.json', 'source_publication.json', 'stage_base_bridge.json', 'stage_evidence.md', 'final_report.md', 'mathematical_analysis.md', 'manuscript.md', 'LP_report.md', 'RESUME.md', 'entry_check.json', 'reports/full.json', 'reports/LP.json', 'reports/new_arms.csv', 'reports/same_PE_pairs.csv', 'reports/same_PE_BASE_bridges.csv', 'reports/verified_U_trajectories.csv', 'review/math_pre_review.md', 'review/production_static_review.md', 'review/production_static_identity.json', 'review/independent_saved_point_check.json', 'review/final_scientific_checks.py']:
    bind(OUT / name)
for name in ['scripts/paper_s2_gd.py', 'config/gi_tbc_gd_round146.json', 'docs/round146_research.md', 'docs/current_mainline.md', 'docs/unified_exact_research_index.md', 'results/unified_exact_round145/stage_evidence.md']:
    bind(ROOT / name)
result = dict(PASS=True, UTC=datetime.now(timezone.utc).isoformat(), reviewer='gd_independent_review',
              scope='Finite existing-byte, receipt, trajectory and source identity checks only; not re-running model verification',
              Optimize=0, Native_load=0, compile=0, reverification=0,
              formal_positions=7, health_positions=1, Native_returned=35, standalone_LP=5,
              charged_seconds=paid, source_files_checked=len(manifest['source_hashes']),
              matrix_SHA=matrices, raw_summary=raw_summary,
              archived_review_evidence=archived_review_evidence,
              early_BASE=early, final_BASE=base_last, final_GD=gd_last, evidence_SHA=bound)
(OUT / 'review/final_scientific_checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ['PASS', 'formal_positions', 'health_positions', 'Native_returned', 'standalone_LP', 'charged_seconds', 'source_files_checked']}, indent=2))
