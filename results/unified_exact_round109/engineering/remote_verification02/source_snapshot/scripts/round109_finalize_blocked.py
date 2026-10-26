"""Explicit incomplete-panel publication after an actual native stack fault.

The unchanged admitted reader audits all present raw endpoints. This wrapper
adds the frozen BLOCKED decision and complete missing-arm inventory; it never
changes evidence, pair thresholds, physical arithmetic, or solver behavior.
"""
from pathlib import Path
import argparse, copy, json
import round109_reader as reader

REL = Path('results/unified_exact_round109')
FREEZE = REL / 'blocked_finalization_freeze.json'
FAULTS = ['NATIVE_STACK_OVERFLOW_BEFORE_INSTANCE_PARSED',
          'FINAL_PE_REPAIR_REQUIRES_ALL42_BEYOND_FROZEN_BUDGET']


def freeze(root, diagnosis):
    root = Path(root).resolve()
    diagnosis = Path(diagnosis)
    assert not diagnosis.is_absolute() and '..' not in diagnosis.parts
    audit = reader.read(root / diagnosis)
    assert audit['decision'] == 'ACCEPT_DIAGNOSIS_BLOCKED'
    assert audit['stage'] == 'BLOCKED' and audit['resumption_allowed'] is False
    assert audit['valid_normal_formal_arms'] == 24
    assert audit['failed_formal_numbers'] == [25]
    assert audit['unstarted_formal_numbers'] == list(range(26, 43))
    assert audit['same_PE_ordinary_environment_recovery_qualified'] is False
    assert audit['original_PE_change_requires_all42'] is True
    assert audit['final_PE_rerun_minimum_native_starts'] == 42
    out = root / REL
    fees = reader.fee_records(out)
    assert len(fees) == 13
    assert sum(f['conservative_process_starts'] for f in fees) == 51
    assert all((out / 'fees' / f['label'] / 'receipt.json').exists() for f in fees)
    ident = reader.read(out / 'campaign/identity.json')
    assert len(ident['launches']) == 42
    for launch in ident['launches']:
        d = reader.portable(root, launch['destination'])
        if launch['number'] <= 24:
            c = reader.read(d / 'completion.json')
            assert c['returncode'] == 0 and c['stop_reason'] == 'normal_return'
        elif launch['number'] == 25:
            c = reader.read(d / 'completion.json')
            assert c['returncode'] == 0xC00000FD
            assert c['stop_reason'] == 'abnormal_process_exit'
            assert reader.read(d / 'observations.json') == []
            assert not (d / 'result.json').exists()
        else:
            assert not d.exists()
    files = [root / diagnosis, out / 'candidate_identity.json',
             out / 'campaign/identity.json', out / 'protocol.json',
             out / 'input_manifest.json', out / 'review/sealed_input_eligibility.json',
             root / 'scripts/round109_finalize_blocked.py']
    files += [root / 'scripts' / name for name in reader.numerical.SOURCES]
    files += sorted((out / 'fees').glob('*/launch.json'))
    files += sorted((out / 'fees').glob('*/receipt.json'))
    value = dict(schema='round109-actual-stack-fault-finalization-v1',
                 failure_review=diagnosis.as_posix(), failure_review_SHA=reader.sha(root / diagnosis),
                 bindings={p.relative_to(root).as_posix(): reader.sha(p) for p in files},
                 valid_normal_formal_numbers=list(range(1, 25)), failed_formal_numbers=[25],
                 unstarted_formal_numbers=list(range(26, 43)), unresolved_faults=FAULTS,
                 conservative_process_starts=51,
                 closed_outer_seconds=sum(f['outer_seconds'] for f in fees),
                 full_new_PE_nominal_seconds=88200, full_new_PE_minimum_native_starts=42,
                 no_anticipated_early_stop_savings=True, no_solve=True)
    reader.write(root / FREEZE, value)
    print(json.dumps(value, allow_nan=False))


def rebuild(root, dest, compare=None):
    root = Path(root).resolve()
    dest = Path(dest)
    sealed = reader.read(root / FREEZE)
    for name, digest in sealed['bindings'].items():
        assert reader.sha(root / name) == digest, name
    captured = {}
    original_table = reader.table

    def capture(path, data):
        captured[Path(path).stem] = copy.deepcopy(data)
        return original_table(path, data)

    reader.table = capture
    try:
        summary = reader.rebuild(root, dest)
    finally:
        reader.table = original_table
    arms = captured['arms']
    assert len(arms) == 24 and summary['failed_formal_arms'] == 1
    assert [f['number'] for f in captured['failures']] == [25]
    missing = [f['number'] for f in captured['unstarted']
               if f['campaign'] == 'campaign']
    assert missing == list(range(26, 43))
    assert all(a['seed'] == 0 for a in arms)
    roles = reader.read(root / REL / 'input_manifest.json')['roles']
    eligible = reader.read(root / REL / 'review/sealed_input_eligibility.json')['eligibility']
    selection = reader.decision.selection(arms, roles, eligible, sealed['unresolved_faults'])
    assert selection['stage'] == 'BLOCKED'
    selection.update(failure_review=sealed['failure_review'],
                     failure_review_SHA=sealed['failure_review_SHA'],
                     finalization_freeze_SHA=reader.sha(root / FREEZE),
                     valid_normal_formal_numbers=list(range(1, 25)), failed_formal_numbers=[25],
                     unstarted_formal_numbers=missing,
                     completed_main_roles=[r['id'] for r in roles[:8]],
                     completed_formal_seed1_arms=0,
                     formal_seed_sensitivity_assessed=False,
                     reason_code_interpretation='Incomplete-panel gate placeholders; no observed Seed sensitivity or V100 performance rejection',
                     effective_stage_reason_codes=sealed['unresolved_faults'],
                     original_frozen_stage_function_retained=True,
                     resource_accounting=dict(conservative_process_starts=summary['conservative_starts'],
                                              closed_outer_seconds=summary['outer_solver_fee_seconds'],
                                              limit_starts=72, limit_outer_seconds=100000,
                                              final_PE_full_rerun_minimum_starts=42,
                                              final_PE_full_rerun_nominal_seconds=88200,
                                              early_stop_savings_credited=False))
    reader.write(dest / 'selection_decision.json', selection)
    summary.update(stage='BLOCKED', incomplete_panel=True,
                   finalization_source_SHA=reader.sha(root / 'scripts/round109_finalize_blocked.py'),
                   finalization_freeze_SHA=reader.sha(root / FREEZE),
                   valid_main_roles=8, frozen_main_denominator=12,
                   frozen_seed_groups=3, formal_seed1_arms_completed=0)
    old_summary = dest / 'summary.json'
    original_bytes = old_summary.read_bytes()
    with (dest / 'inherited_raw_summary.json').open('xb') as file:
        file.write(original_bytes)
    old_summary.unlink()
    reader.write(old_summary, summary)
    print(json.dumps(summary, allow_nan=False))
    if compare:
        print(json.dumps(reader.compare(compare, dest), allow_nan=False))
    return selection


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['freeze', 'rebuild'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--diagnosis')
    parser.add_argument('--out')
    parser.add_argument('--compare')
    args = parser.parse_args()
    if args.mode == 'freeze':
        freeze(args.root, args.diagnosis)
    else:
        assert args.out
        rebuild(args.root, args.out, args.compare)
