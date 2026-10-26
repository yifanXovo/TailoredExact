"""Lightweight narrative binding after the completed independent raw audit.

This does not rebuild evidence, invoke any solver, or approve resumption.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    root = args.root.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report_root = root / 'results/unified_exact_round109'
    bindings = {}

    def read(relative):
        p = (report_root / relative).resolve(strict=True)
        assert p.is_relative_to(root)
        payload = p.read_bytes()
        bindings[relative] = hashlib.sha256(payload).hexdigest()
        return payload

    raw = json.loads(read('review/final_blocked_raw01/audit.json'))
    comparison = json.loads(read('review/final_blocked_compare02/audit.json'))
    assert bindings['review/final_blocked_raw01/audit.json'] == 'ff08f530e59a9edd0641e08e656d761937f6d043c758c80e77877484ef16980d'
    assert bindings['review/final_blocked_compare02/audit.json'] == 'b08eb3f90646d48528bf0a89aed3a1eef8f96eb00bd67557f8cf2c98917feb31'
    assert raw['decision'] == 'ACCEPT_INDEPENDENT_BLOCKED'
    assert comparison['decision'] == 'ACCEPT_INDEPENDENT_BLOCKED_PUBLICATION'
    assert raw['stage'] == comparison['stage'] == 'BLOCKED'
    assert raw['resumption_allowed'] is comparison['resumption_allowed'] is False

    documents = {name: read(name).decode('utf-8') for name in (
        'final_report.md', 'paper_candidate_spec.md',
        'main09_stack_failure.md', 'reproduce.md')}
    required = {
        'final_report.md': (
            '**Stage: BLOCKED.**', 'All6 formal Seed1 arms are unstarted.',
            'micro-positive objective1.000173407530002e-12',
            "separately\r\nfrom ENS's physical F=0 fleet",
            'combined qualification/formal rebuild has99 actual Optimize calls',
            '63LP and36MIP', '54LP and28MIP',
            'maximum simultaneously relevant active\r\nleaves is1',
            'NEXT_LEAF target MIP count\r\nis0',
            '51 conservative starts', '18618.079987913487',
            'final526 and return1', 'target/final795 and return95',
            'unknown exact;[1770.375,1771.833281]',
            'unknown exact;[643.7820000000065,645.352919]'),
        'reproduce.md': (
            'python <new-recovered-root>/scripts/round109_finalize_blocked.py rebuild',
            'review/round109_independent_blocked.py --root <new-recovered-root> --public',
            'There is no original-worktree fallback.',
            'All six formal Seed1 arms are\r\nunmeasured.'),
        'paper_candidate_spec.md': (
            'Round109 stage is BLOCKED', 'ENS-C remains the default',
            'including return\r\nunloading',
            'representation', 'This equivalence does not require the two'),
        'main09_stack_failure.md': (
            '0xC00000FD', '1,414,288bytes', 'or valid physical endpoint.',
            'No\r\nqualified ordinary environment-only same-PE/same-entry repair was found.'),
    }
    # Normalize only line endings for text assertions; SHA binds original bytes.
    checks = []
    for name, fragments in required.items():
        text = documents[name].replace('\r\n', '\n')
        for fragment in fragments:
            needle = fragment.replace('\r\n', '\n')
            assert needle in text, (name, needle)
            checks.append({'file': name, 'required_statement': needle})
    assert 'full exactly feasible zero-valued vector' not in documents['final_report.md']

    arms = raw['own_actual_arms']
    qualified = raw['own_qualification']
    certified = sum(arm['certificate'] is True for arm in arms)
    solve_kinds = Counter()
    targets = Counter()
    for mechanism in raw['mechanism']:
        solve_kinds.update(mechanism['solve_kinds'])
        targets.update(mechanism['target_kind_counts'])
    assert len(arms) == 24 and len(qualified) == 5
    assert certified == 14
    assert solve_kinds == Counter({'LP': 54, 'MIP': 24, 'CHILD_BOUND_TARGET_MIP': 4})
    assert targets == Counter({'child_disjunction': 4})
    assert comparison['actual_Optimize'] == 99
    assert comparison['journal_returned'] == 98
    assert comparison['independently_proved_rc0_without_returned'] == 1
    assert comparison['formal_Seed1_sensitivity_not_assessed'] is True
    assert comparison['V100_performance_not_assessed'] is True
    assert comparison['exact_bounded_clocks_and_ratio_remain_null'] is True
    assert raw['fees']['paid_starts'] == 51
    assert raw['fees']['paid_outer_seconds'] == 18618.079987913487
    assert raw['science']['formal_seed1_arms_completed'] == 0
    assert raw['science']['frozen_main_denominator'] == 12
    assert raw['science']['frozen_seed_groups'] == 3
    source = Path(__file__).resolve(strict=True)
    source_bytes = source.read_bytes()
    (out / 'source_snapshot.py').write_bytes(source_bytes)
    audit = {
        'decision': 'ACCEPT_LIGHTWEIGHT_NARRATIVE_REVIEW',
        'stage': 'BLOCKED', 'resumption_allowed': False,
        'scope': 'Narrative snapshot after completed independent raw and comparison audits; future delivery receipts must be reviewed separately.',
        'actual_utc': datetime.now(timezone.utc).isoformat(),
        'explicit_read_root': str(root),
        'bindings': bindings,
        'source_SHA': hashlib.sha256(source_bytes).hexdigest(),
        'text_checks': checks,
        'own_valid_arms': 24, 'own_certified_arms': certified,
        'own_open_arms': len(arms) - certified, 'own_qualification_arms': 5,
        'own_pair_counts': comparison['own_pair_counts'],
        'formal_solve_kinds': dict(solve_kinds), 'formal_target_kinds': dict(targets),
        'actual_Optimize_prior_audit': 99, 'formal_Optimize_prior_audit': 82,
        'formal_Seed1_unmeasured': 6, 'V100_performance_unassessed': True,
        'micro_positive_cold_countervector_distinct_from_ENS_zero_fleet': True,
        'operations_paragraph_future_receipts_not_claimed_as_completed': True,
        'unchanged_original_audits_and_core_files': True,
        'raw_rebuilds_this_review': 0, 'Optimize_this_review': 0,
        'native_environments_this_review': 0, 'production_edits': 0,
        'engineering_elapsed_seconds': time.perf_counter() - started,
    }
    (out / 'audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'decision': audit['decision'], 'audit': str(out / 'audit.json'), 'checks': len(checks), 'Optimize': 0}))


if __name__ == '__main__':
    main()
