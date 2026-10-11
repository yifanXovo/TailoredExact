"""R86 reader: qualified no-UB and final-only physical outcomes; no optimization."""
import hashlib
import json
import math
from pathlib import Path
import analyze_round61 as physical_module


def receipt(path, observed, cutoff):
    path = Path(path)
    raw = path.read_bytes()
    assert raw.endswith(b'\n'), 'incomplete_receipt'
    fields = raw.decode('ascii').split()
    assert len(fields) == 5 and fields[0] == 'NEJ1', 'invalid_receipt'
    sequence, timestamp, size = int(fields[1]), float(fields[2]), int(fields[3])
    assert sequence > 0 and path.name == f'event_{sequence}.commit'
    assert all(math.isfinite(t) and 0 <= t <= cutoff for t in [observed, timestamp]), 'outside_cutoff'
    data = path.with_suffix('.json').read_bytes()
    assert len(data) == size and hashlib.sha256(data).hexdigest() == fields[4], 'data_hash_or_length_mismatch'
    payload = json.loads(data)
    assert payload['schema'] == 1 and payload['sequence'] == sequence
    return dict(sequence=sequence, data_close_seconds=timestamp, first_observed_seconds=observed,
                effective_available_seconds=max(timestamp, observed), sha256=fields[4], payload=payload)


def replay_bound(scope, bound, witnesses):
    """Separate Python implementation of scope/coverage, with exact gap checks."""
    tolerance = 1e-7
    upper = min((w['F'] for w in witnesses), default=math.inf)
    if scope['full_original']:
        assert scope['native_preconditions'], 'missing_full_native_preconditions'
        assert bound <= upper+tolerance, 'full_bound_witness_inconsistency'
        return bound
    cutoff = scope['cutoff']
    assert math.isfinite(upper) and cutoff+tolerance >= upper, 'unwitnessed_cutoff'
    pieces = [dict(p) for p in scope['cover']]
    found = False
    for p in pieces:
        assert all(math.isfinite(p[k]) for k in ['lower_g', 'upper_g', 'lower', 'cutoff'])
        assert 0 <= p['lower_g'] <= p['upper_g'] and p['cutoff']+tolerance >= cutoff
        if (p['id'] == scope['leaf'] and p['lower_g'] == scope['lower_g'] and
                p['upper_g'] == scope['upper_g'] and p['cutoff'] == cutoff and
                scope['native_preconditions'] and scope['model_sha256']):
            assert not found, 'duplicate_active_scope'
            found = True
            p['lower'] = max(p['lower'], bound)
        for w in witnesses:
            if p['lower_g']-tolerance <= w['G'] <= p['upper_g']+tolerance and w['F'] <= p['cutoff']+tolerance:
                assert p['lower'] <= w['F']+tolerance, 'local_bound_witness_inconsistency'
    assert found, 'scope_not_matching_live_leaf'
    covered, lower = 0, cutoff
    for p in sorted(pieces, key=lambda x: x['lower_g']):
        assert p['lower_g'] <= covered, 'uncovered_gini_range'
        covered = max(covered, p['upper_g'])
        lower = min(lower, p['cutoff'], p['lower'])
    assert pieces and covered >= min(cutoff, scope['gmax']), 'uncovered_gini_tail'
    assert lower <= upper+tolerance, 'global_bound_witness_inconsistency'
    return lower


def audit(root, panel, records, binary_hash):
    physical_module.ROOT = root
    calls, witnesses, bounds, returned = {}, [], [], []
    identity = None
    for expected, record in enumerate(records, 1):
        event = record['payload']
        assert event['sequence'] == expected, 'incomplete_committed_sequence'
        kind = event['kind']
        assert kind != 'failure', ('journal_failure', event)
        if kind == 'identity':
            assert expected == 1 and event['input_sha256'] == panel['input_sha256']
            assert event['lambda'] == float(panel['lambda'])
            assert event['T'] == float(panel['T_seconds'])
            assert event['pickup_seconds'] == float(panel['pickup_seconds'])
            assert event['drop_seconds'] == float(panel['drop_seconds'])
            identity = event
        elif kind == 'call':
            assert event['call'] not in calls
            calls[event['call']] = event
            model = Path(event['model_path'])
            assert model.is_file() and hashlib.sha256(model.read_bytes()).hexdigest() == event['model_sha256']
            if event['native_preconditions']:
                assert event['settings'] == dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1,
                    MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
        elif kind == 'witness':
            witness = physical_module.physical(panel, event)
            assert witness['original_T_feasible']
            assert abs(witness['G']-event['G']) < 1e-7 and abs(witness['P']-event['P']) < 1e-7
            witnesses.append(dict(witness, source=event['source'], call=event['call'],
                sequence=expected, available=record['effective_available_seconds']))
            # A later physical witness can contradict an earlier numerical claim.
            for b in bounds:
                if b['global_available']:
                    replay_bound(calls[b['call']], b['native_bound'], witnesses)
        elif kind == 'bound':
            scope = calls[event['call']]
            assert not event['inconsistent']
            if event['global_available']:
                recomputed = replay_bound(scope, event['native_bound'], witnesses)
                assert abs(recomputed-event['global_bound']) < 1e-10
            else:
                assert event['global_bound'] is None
            bounds.append(dict(event, available=record['effective_available_seconds']))
        elif kind == 'returned':
            assert event['call'] in calls and event['return_code'] == 0
            returned.append(event['call'])
        elif kind == 'witness_rejected':
            pass  # An invalid raw vector never becomes a physical UB.
        else:
            raise AssertionError(('unknown_event_kind', kind))
    assert identity is not None
    # A missing incumbent is a legitimate open result only for a complete
    # original-model native call; restricted cutoffs still require witnesses.
    if not witnesses:
        assert calls and all(c['full_original'] and c['native_preconditions'] for c in calls.values()), 'missing_witness_for_restricted_scope'
    upper = min((w['F'] for w in witnesses), default=None)
    native_global = [b['global_bound'] for b in bounds if b['global_available']]
    assert all(math.isfinite(b) for b in native_global), 'nonfinite_global_bound'
    lower = max([0]+native_global)
    if upper is not None:
        assert lower <= upper+1e-7, 'final_endpoint_inconsistency'
    return dict(binary_sha256=binary_hash, committed_events=len(records), native_calls_started=len(calls),
        native_calls_returned=len(returned), physical_witnesses=len(witnesses),
        native_physical_witnesses=sum(w['source'].startswith('native_MIPSOL') for w in witnesses),
        scoped_bound_events=len(bounds), global_native_bound_events=len(native_global),
        UB=upper, LB=lower, gap=upper-lower if upper is not None else None,
        physical_upper_available=upper is not None,
        lower_bound_source='complete_domain_native_evidence' if native_global else 'analytical_nonnegative_objective_only',
        certificate=False, solver_finalization_certificate=False,
        explanation='Observational interrupted endpoint; no native optimality or rational certificate is inferred.',
        witnesses=witnesses)


def finalize_endpoint(root, panel, arm, audited, records, result, reason, reference):
    """Keep observed history separate from evidence first available at normal exit."""
    physical_module.ROOT = root
    if reason != 'normal_return':
        assert result is None
        audited['normal_result_certificate'] = False
        audited['endpoint'] = dict(U=audited['UB'], L=audited['LB'], gap=audited['gap'],
            certificate=False, source='interrupted_committed_evidence', status=reason)
        return
    assert result is not None
    assert not any(t in result['status'].lower() for t in ['failed','invalid','error','numeric']), result['status']
    if arm == 'P-GRB':
        assert result['gurobi_native_domain_audit_passed']
        assert result['gurobi_model_fingerprint'] == reference['fingerprint']
        assert result['gurobi_lifecycle_valid'] and result['native_mip_strict_gap_parameters_valid']
        if not result['verified_incumbent_objective_available']:
            assert audited['physical_witnesses'] == 0 and audited['UB'] is None
            assert result['status'] == 'time_limit' and result['gurobi_solution_count'] == 0
            assert result['upper_bound'] is None and result['gap'] is None
            assert not result['strict_certified_original_problem']
            lower = audited['LB']
            if result['lower_bound'] is not None:
                assert result['native_mip_best_bound_available']
                assert math.isfinite(result['lower_bound'])
                lower = max(lower, result['lower_bound'])
            audited['normal_result_certificate'] = False
            audited['endpoint'] = dict(U=None, L=lower, gap=None, certificate=False,
                source='normal_full_original_no_physical_UB', status=result['status'])
            return
        assert result['gurobi_solution_count'] > 0
        assert result['verified_incumbent_original_problem_feasible']
    else:
        assert audited['physical_witnesses'] >= 1, 'restricted_scope_needs_observed_physical_witness'
        assert result['external_gini_tree_root_coverage_valid']
        assert result['external_gini_tree_parent_child_coverage_valid']
        if audited['native_calls_started']:
            assert result['external_gini_tree_backend_parameter_roundtrip_valid']
    physical = physical_module.physical(panel, result)
    assert physical['original_T_feasible']
    upper = result['upper_bound']
    assert math.isfinite(upper) and abs(physical['F']-upper) < 1e-7
    lower = result['lower_bound']
    if lower is None:
        assert arm == 'P-GRB' and not result['strict_certified_original_problem']
        lower = audited['LB']
    assert math.isfinite(lower) and lower <= upper+1e-7
    assert audited['LB'] <= physical['F']+1e-7
    if audited['UB'] is not None:
        assert audited['UB']+1e-7 >= upper
    else:
        assert arm == 'P-GRB' and audited['physical_witnesses'] == 0
    scopes = {r['payload']['call']:r['payload'] for r in records if r['payload']['kind']=='call'}
    for row in records:
        event = row['payload']
        if event['kind']=='bound' and event['global_available']:
            replay_bound(scopes[event['call']], event['native_bound'], audited['witnesses']+[physical])
    if audited['native_calls_started'] == 0:
        assert arm != 'P-GRB' and result['strict_certified_original_problem']
        assert abs(physical['F']) <= 1e-7 and abs(lower) <= 1e-7 and audited['LB'] == 0
    audited['normal_result_certificate'] = result['strict_certified_original_problem']
    audited['final_only_physical_witness'] = audited['physical_witnesses'] == 0
    audited['final_physical_verification'] = physical
    audited['endpoint'] = dict(U=upper, L=lower, gap=upper-lower,
        certificate=result['strict_certified_original_problem'],
        source='normal_final_only_physical_endpoint' if audited['physical_witnesses']==0 else 'normal_finalized_physical_endpoint',
        status=result['status'])
