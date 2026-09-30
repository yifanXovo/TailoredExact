"""R97 v3 analysis: exact acknowledged interruption and unknown completion fields.

Versioned from the original analyzer; historical analyzer hashes stay intact.
Summarize a fully completed frozen batch without re-running optimization.

Requires idle machine and complete successful audit receipts. Timings include
all solver work; nested callback costs are explanatory, never subtracted.
"""
import argparse
import csv
import json
from pathlib import Path
from round97_campaign import ROOT, OUT, read, write, sha, ext
import round97_interrupted_evidence as interrupted


def relative(path):
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def table(path, rows):
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def difference(left, right):
    return None if left is None or right is None else left-right


def material_difference(left, right, absolute, relative):
    delta = difference(left, right)
    return None if delta is None else abs(delta) >= absolute and abs(delta) >= relative*abs(right)


def compare(candidate, baseline):
    cu, bu = candidate['U'], baseline['U']
    cg, bg = candidate['absolute_gap'], baseline['absolute_gap']
    ct, bt = candidate['process_wall_seconds'], baseline['process_wall_seconds']
    certified = candidate['certificate'], baseline['certificate']
    if certified == (True, True):
        delta = ct - bt
        material = abs(delta) > 5 and abs(delta) > .05 * bt
        severe = bt >= 60 and delta >= 30 and delta >= .2 * bt
        classification = ('material_time_regression' if delta > 0 else 'material_time_gain') if material else 'similar_certification_time'
    elif certified == (False, True):
        classification, severe = 'one_sided_certificate_loss', True
    elif certified == (True, False):
        classification, severe = 'one_sided_certificate_gain', False
    else:
        classification, severe = 'both_uncertified_final_order_unknown', False
    complete=candidate['normal_return'] and baseline['normal_return']
    if not complete:
        classification,severe='interrupted_comparison_final_certification_order_unknown',None
    return dict(id=candidate['id'], candidate=candidate['arm'], baseline=baseline['arm'],
                certificate_comparison_available=complete,
                candidate_certificate_status=candidate['certificate_status'],baseline_certificate_status=baseline['certificate_status'],
                candidate_endpoint_source=candidate['endpoint_source'],baseline_endpoint_source=baseline['endpoint_source'],
                common_cap_seconds=candidate['cap_seconds'],
                candidate_certificate=certified[0], baseline_certificate=certified[1],
                classification=classification, severe=severe,
                candidate_minus_baseline_process_cost_seconds=ct-bt,
                candidate_has_physical_UB=cu is not None, baseline_has_physical_UB=bu is not None,
                candidate_minus_baseline_U=difference(cu,bu),
                candidate_minus_baseline_L=candidate['L']-baseline['L'],
                candidate_minus_baseline_absolute_gap=difference(cg,bg),
                material_UB_difference=material_difference(cu,bu,1e-5,.01),
                material_gap_difference=material_difference(cg,bg,1e-5,.1))


def main(label):
    ext.ensure_idle()
    camp = OUT / label
    identity = read(camp / 'identity.json')
    completed = [json.loads(line) for line in (camp / 'summary.jsonl').read_text().splitlines()]
    assert len(completed) == len(identity['launches'])
    assert all(row['audit_passed'] for row in completed)
    destination = OUT / (label + '_analysis')
    assert not destination.exists(), 'Never overwrite a completed analysis'
    rows, bindings = [], {relative(camp / 'identity.json'): sha(camp / 'identity.json'),
                         relative(camp / 'summary.jsonl'): sha(camp / 'summary.jsonl')}
    for launch, completed_row in zip(identity['launches'], completed):
        assert (launch['number'], launch['id'], launch['arm']) == (
            completed_row['number'], completed_row['id'], completed_row['arm'])
        raw = Path(launch['destination'])
        audit, receipt = read(raw / 'audit.json'), read(raw / 'completion.json')
        assert audit['passed'] and receipt == completed_row['completion']
        result,extra_paths=interrupted.validate_outcome(launch,audit,receipt)
        for path in extra_paths:bindings[relative(path)]=sha(path)
        endpoint = completed_row['endpoint']
        assert endpoint == audit['endpoint']
        events_path = raw / 'external/round97/events.jsonl'
        events = [json.loads(line) for line in events_path.read_text().splitlines()] if events_path.exists() else []
        solutions = [event for event in events if event['kind'] == 'solution']
        assert not any(event['kind'] == 'failure' for event in events)
        improvements = [event for event in solutions if event.get('candidate_F', float('inf')) < event.get('input_F', 0)-1e-9]
        by_event = {event['event']: event for event in solutions}
        checkpoints = [event for event in events if event['kind'] == 'predeadline_verified_candidate']
        checkpoint_hashes = set()
        witness_checks = {w['path']: w for w in audit.get('round97', {}).get('physical_witnesses', [])}
        for checkpoint in checkpoints:
            source = by_event[checkpoint['event']]
            assert checkpoint['F'] < source['input_F'] - 1e-9
            witness_path = events_path.parent / checkpoint['witness']
            assert sha(witness_path) == witness_checks[checkpoint['witness']]['sha256']
            witness = read(witness_path)
            assert abs(witness['F'] - checkpoint['F']) <= 1e-12
            checkpoint_hashes.add(witness['sha256'])
            bindings[relative(witness_path)] = sha(witness_path)
        submitted = [event for event in solutions if event.get('submission_return_code') == 0]
        native_calls = None if result is None else audit['native_calls_started']
        stats = audit.get('round97', {})
        rows.append(dict(number=launch['number'], id=launch['id'], arm=launch['arm'],
                         operator=launch.get('operator', 'r83' if events else 'none'),
                         input_sha256=launch['panel']['input_sha256'],
                         mathematical_T_seconds=launch['panel']['T_seconds'], cap_seconds=launch['cap_seconds'],
                         process_wall_seconds=receipt['process_wall_seconds'],
                         end_to_end_seconds=receipt['fully_observed_end_to_end_seconds'],
                         stop_reason=receipt['stop_reason'], normal_return=result is not None,
                         certificate=endpoint['certificate'] if result is not None else None,
                         certificate_status=interrupted.certificate_status(endpoint,result),
                         endpoint_source=endpoint['source'],
                         U=endpoint['U'], L=endpoint['L'], absolute_gap=endpoint['gap'],
                         relative_gap=None if endpoint['U'] is None or endpoint['gap'] is None else endpoint['gap']/max(abs(endpoint['U']), 1e-10),
                         verified_complete_native_optimize_calls=native_calls,
                         observed_native_call_scopes=audit['native_calls_started'],
                         observed_native_calls_returned=audit['native_calls_returned'],
                         native_LP_calls=None if result is None else result.get('external_gini_tree_lp_optimize_count', 0),
                         MIPSOL_events=len(solutions), unique_physical_inputs=len({e['input_hash'] for e in solutions}),
                         excluded_start_matching_events=stats.get('excluded_start_matching_events', 0),
                         eligible_physical_events=stats.get('eligible_physical_events', 0),
                         post_start_events=stats.get('post_start_events', 0),
                         accepted_order_moves=stats.get('accepted_order_moves', 0),
                         order_proposals=stats.get('order_proposals', 0),
                         recorded_fresh_joint_increment_events=stats.get('incremental_order_improvement_events', 0),
                         strict_improvement_events=len(improvements),
                         unique_completed_closure_candidates=len({e['candidate_hash'] for e in improvements}),
                         predeadline_checkpoint_records=len(checkpoints),
                         unique_predeadline_checkpoints=len(checkpoint_hashes),
                         all_improved_source_events=len({e['event'] for e in improvements + checkpoints}),
                         best_completed_closure_F=min((e['candidate_F'] for e in improvements), default=None),
                         best_predeadline_checkpoint_F=min((e['F'] for e in checkpoints), default=None),
                         best_optional_candidate_F=min([e['candidate_F'] for e in improvements] +
                                                       [e['F'] for e in checkpoints], default=None),
                         submissions=len(submitted),
                         vector_observations=stats.get('vector_observations', 0),
                         native_incumbent_changes=stats.get('native_incumbent_changes', 0),
                         archive_handoffs=stats.get('archive_handoffs', 0),
                         complete_callback_seconds=stats.get('complete_callback_seconds', 0),
                         nested_closure_seconds=stats.get('closure_seconds', 0),
                         nested_mapping_validation_seconds=stats.get('mapping_validation_seconds', 0),
                         result_status=endpoint['status']))
        for path in [raw / 'audit.json', raw / 'completion.json'] + ([raw/'result.json'] if result is not None else []) + ([events_path] if events else []):
            bindings[relative(path)] = sha(path)
    comparisons = []
    for candidate in rows:
        if candidate['arm'] in ('P-GRB', 'OFF', 'SHADOW'):
            continue
        for baseline in rows:
            if candidate['id'] == baseline['id'] and candidate['number'] != baseline['number']:
                assert candidate['cap_seconds'] == baseline['cap_seconds'], 'No mixed-cap endpoint pairing'
                assert candidate['input_sha256'] == baseline['input_sha256'], 'No same-label/different-input pairing'
                assert candidate['mathematical_T_seconds'] == baseline['mathematical_T_seconds'], 'No different-physical-T pairing'
                comparisons.append(compare(candidate, baseline))
    destination.mkdir()
    table(destination / 'arms.csv', rows)
    if comparisons:
        table(destination / 'pairs.csv', comparisons)
    bindings[relative(interrupted.__file__)]=sha(interrupted.__file__)
    write(destination / 'identity.json', dict(batch=label, source_bindings=bindings,
        analyzer_sha256=sha(__file__), solver_starts=len(rows), new_optimizer_calls=0,
        verified_completed_native_optimize_calls=sum(r['verified_complete_native_optimize_calls'] or 0 for r in rows),
        observed_native_call_scopes=sum(r['observed_native_call_scopes'] for r in rows),
        all_optimize_counts_complete=all(r['normal_return'] for r in rows),
        paid_process_seconds=sum(r['process_wall_seconds'] for r in rows),
        caveats=['Frozen single-run comparisons, not causal timing subtraction.',
                 'Only exact acknowledged interrupted arm5 is accepted; its endpoint is committed evidence, not a normal finalized result.',
                 'An interrupted run has unknown complete Optimize count and unobserved certificate status; no certificate gain/loss or speed classification is inferred against it.',
                 'Missing physical U or gap remains null; no numeric substitute or invented quality comparison.',
                 'Optional SHADOW candidate F is never its official U.',
                 'Both censored endpoints do not establish eventual certification order.',
                 'Vector matches and native changes do not establish unique candidate provenance.',
                 'Recorded fresh joint R96/R83 increments are a lower-bound count; cache reuse is excluded and objective descent is not assigned to ordering alone.',
                 'Callback, closure and mapping timing fields are nested and must not be added together.']))
    print(json.dumps(dict(batch=label, completed_arms=len(rows), pairs=len(comparisons), destination=str(destination))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    main(parser.parse_args().label)
