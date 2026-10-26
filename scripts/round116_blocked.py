"""Finite offline diagnosis of the stopped, frozen Round116 campaign.

This appends evidence only. It neither repairs the admitted return predicate,
closes a failed arm, changes a sealed result, nor authorizes another native run.
"""
import argparse, collections, csv, json, time
from pathlib import Path
import round108_reader as core
from read_round116 import ROUND

def run(root):
    tick = time.perf_counter()
    root = Path(root).resolve()
    out = root / ROUND
    fixed = core.read(out / 'fixed_manifest.json')
    rows = []
    for launch in fixed['launches']:
        d = core.portable(root, launch['destination'])
        started = (d / 'launch.json').is_file()
        closed = (d / 'arm_total_receipt.json').is_file()
        rows.append(dict(id=launch['id'], arm=launch['arm'],
            global_launch_number=launch['global_launch_number'], actually_started=started,
            verification_closed=closed,
            state='VERIFICATION_CLOSED' if closed else 'PENDING_VERIFICATION_FAILED' if started else 'UNSTARTED'))
    assert sum(q['actually_started'] for q in rows) == 18
    assert sum(q['verification_closed'] for q in rows) == 17
    failed = next(l for l in fixed['launches'] if l['id'] == 'E100-C1' and l['arm'] == 'ENS-C')
    d = core.portable(root, failed['destination'])
    receipt = core.read(d / 'producer_receipt.json')
    seal = core.read(d / 'producer_seal.json')
    assert receipt['state'] == 'PRODUCED_PENDING_VERIFICATION' and receipt['verification_passed'] is None
    assert receipt['producer_seal_SHA'] == core.sha(d / 'producer_seal.json')
    for n, digest in seal['required_SHA'].items():
        assert core.sha(d / n) == digest, ('sealed bytes changed', n)
    assert not (d / 'arm_total_receipt.json').exists()
    completion = core.read(d / 'completion.json')
    assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
    ledger = core.rows(d / 'external/paper_optimize_ledger.csv')
    logs = {}
    for n, call in enumerate(ledger, 1):
        path = core.portable(root, call['native_log'])
        key = path.relative_to(root).as_posix()
        if key not in logs:
            content = path.read_text(encoding='utf-8')
            logs[key] = dict(path=key, SHA=core.sha(path), Optimize_headers=content.count('Optimize a model with '), calls=[])
        logs[key]['calls'].append(dict(ledger_number=n, leaf=call['leaf_id'], solve_kind=call['solve_kind'],
            model_SHA=call['model_sha256'], return_code=int(call['optimize_return_code']),
            solver_runtime=float(call['solver_runtime'])))
    assert len(ledger) == 10 and sum(q['Optimize_headers'] for q in logs.values()) == 10
    reused = [q for q in logs.values() if q['Optimize_headers'] != 1]
    assert len(reused) == 3 and all(q['Optimize_headers'] == len(q['calls']) == 2 for q in reused)
    fees = []
    for p in sorted((out / 'fees').glob('*/launch.json')):
        launch = core.read(p); r = core.read(p.parent / 'receipt.json')
        assert r['actual_exit_observed']
        fees.append(dict(label=p.parent.name, conservative_starts=launch['conservative_process_starts'],
            actual_native_children=r['actual_native_children'], qualification=launch['qualification'],
            exit_code=r['exit_code'], outer_seconds_lower=r['outer_seconds_lower'],
            outer_seconds_upper=r['outer_seconds_upper'],
            actual_exit_observation_delay_included=True, receipt_SHA=core.sha(p.parent / 'receipt.json')))
    result = dict(schema='round116-actual-execution-stop-v1', execution_stage='BLOCKED',
        failed_role='E100-C1', failed_arm='ENS-C', failed_global_launch_number=18,
        failure_kind='FROZEN_RETURN_AUDIT_REJECTS_REUSED_LP_LOG',
        failure_file='results/unified_exact_round116/fees/formal05/failure.txt',
        failure_SHA=core.sha(out / 'fees/formal05/failure.txt'),
        frozen_predicate='round114_audit.return_chain: text.count("Optimize a model with ") == 1',
        predicate_SHA=core.sha(root / 'scripts/round114_audit.py'),
        observed_log_fact='three LP paths each contain two Optimize headers and are each named by two ledger calls',
        individual_epoch_return_and_scope_not_qualified_under_frozen_predicate=True,
        native_result_normal_return=True, failed_arm_T_produce=receipt['T_produce'], failed_arm_cap=3600,
        failed_arm_T_verify_complete=None, failed_arm_T_total_complete=None,
        failed_arm_producer_seal_SHA=core.sha(d / 'producer_seal.json'),
        reported_failed_arm_Optimize=len(ledger), failed_arm_unique_log_Optimize_headers=10,
        failed_arm_Optimize_lifecycle_qualified=False, unique_logs=list(logs.values()),
        original_claim_that_extra_unknown_Optimize_exists_not_established=True,
        algorithm_or_solver_internal_root_cause='unknown',
        actual_formal_children=18, verification_closed_formal_arms=17, unstarted_formal_positions=6,
        unstarted_global_launch_numbers=[q['global_launch_number'] for q in rows if not q['actually_started']],
        minimum_failed_position=[18], remaining_positions_unstarted_due_to_stop=[19,20,21,22,23,24],
        all_24_positions=rows, fees=fees,
        conservative_starts=sum(q['conservative_starts'] for q in fees),
        paid_outer_seconds=sum(q['outer_seconds_upper'] for q in fees),
        stop_reason='Required serial verification failed; no next native arm may start under the unchanged admitted helper identity.',
        sole_remaining_evidence_gap='Six-position panel completion and the failed arm return/scope qualification under one valid frozen contract.',
        full_panel_A_D_assessed=False, formal_retries=0, default_changed=False,
        native_processes_reentered=False, source_draws_added=0, sealed_bytes_modified=False,
        diagnostic_qualifies_failed_endpoint=False, next_phase_automatically_executed=False,
        Optimize=0, native_starts=0, created_unix=time.time(), engineering_seconds=time.perf_counter()-tick,
        diagnostic_SHA=core.sha(__file__))
    core.write(out / 'execution_stop.json', result)
    core.table(out / 'execution_positions.csv', rows)
    core.table(out / 'budget_actual.csv', fees)
    print(json.dumps({k: result[k] for k in ['execution_stage','failure_kind','actual_formal_children','verification_closed_formal_arms','unstarted_formal_positions','conservative_starts','paid_outer_seconds','engineering_seconds']}), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', required=True)
    run(parser.parse_args().root)
