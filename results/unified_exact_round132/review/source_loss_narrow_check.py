"""Finite one-arm read-only investigation; no campaign replay or native imports."""
from pathlib import Path
from fractions import Fraction as F
import ast
import hashlib
import json
import math
import re
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round132'
CAMP = OUT / 'campaign/D_group24'
DEST = CAMP / 'raw/02_X-35-U_S1_R1_S2'
INPUTS = {}


def blob(p):
    b = p.read_bytes()
    INPUTS[p.relative_to(ROOT).as_posix()] = dict(SHA=hashlib.sha256(b).hexdigest(), bytes=len(b))
    return b


def read(p):
    return json.loads(blob(p).decode('utf-8-sig'))


def digest(p):
    blob(p)
    return INPUTS[p.relative_to(ROOT).as_posix()]['SHA']


def check():
    started = time.perf_counter()
    identity = read(CAMP / 'identity.json')
    launch = next(l for l in identity['launches'] if l['method'] == 'S2')
    assert launch['id'] == 'X-35-U' and launch['seed'] == launch['repeat'] == 1
    panel = launch['panel']
    ip = ROOT / panel['input_path']
    text = blob(ip).decode('utf-8')
    assert digest(ip) == panel['input_sha256']
    vector = lambda name: ast.literal_eval(re.search(r'^\s*' + name + r'\s*=\s*(\[[^\n]*\])', text, re.M)[1])
    b, target, capacities, xy, weights = map(vector, ['initial', 'target', 'capacities', 'points', 'weights'])
    result = read(DEST / 'result.json')
    ind = read(DEST / 'independent_evidence.json')
    obs = read(DEST / 'observations.json')
    events = {}
    for j, observation in enumerate(obs, 1):
        p = DEST / 'journal' / f'event_{j}.json'
        raw = blob(p)
        event = json.loads(raw)
        commit = blob(p.with_suffix('.commit')).decode('utf-8').split()
        assert commit[0] == 'NEJ1' and int(commit[1]) == j
        assert int(commit[3]) == len(raw) and commit[4] == hashlib.sha256(raw).hexdigest() == observation['sha256']
        assert observation['payload'] == event and event['sequence'] == j
        events[j] = event
    ownzero = events[21]
    assert ownzero['kind'] == 'witness' and ownzero['call'] == 4
    assert ownzero['routes'] == result['routes'] == ind['physical']['routes']
    # Recompute loads in route order and objectives using exact integer ratios.
    y = b.copy()
    seen = set()
    cars = set()
    routes = []
    for route in result['routes']:
        k = route['vehicle']
        assert k not in cars and 0 <= k < panel['M']
        cars.add(k)
        nodes = route['nodes']
        assert nodes[0] == nodes[-1] == 0
        operations = {}
        for op in route['operations']:
            i, pickup, drop = op['station'], op['pickup'], op['drop']
            assert i not in operations and type(pickup) is int and type(drop) is int
            assert pickup >= 0 and drop >= 0 and bool(pickup) != bool(drop)
            operations[i] = (pickup, drop)
        assert set(nodes[1:-1]) == set(operations)
        load = pickup_total = drop_total = peak = 0
        for i in nodes[1:-1]:
            assert 1 <= i <= panel['V'] and i not in seen
            seen.add(i)
            pickup, drop = operations[i]
            load += pickup - drop
            pickup_total += pickup
            drop_total += drop
            peak = max(peak, load)
            assert 0 <= load <= panel['Q_vector'][k]
            y[i] += drop - pickup
            assert 0 <= y[i] <= capacities[i]
        travel = math.fsum(math.dist(xy[i], xy[j]) / 1.5 for i, j in zip(nodes, nodes[1:]))
        handling = (panel['pickup_seconds'] + panel['drop_seconds']) * pickup_total
        duration = travel + handling
        assert duration <= panel['T_seconds'] + 1e-7
        routes.append(dict(vehicle=k, Q=panel['Q_vector'][k], peak_load=peak,
            cumulative_pickup=pickup_total, cumulative_drop=drop_total, return_load=load,
            travel_seconds=travel, handling_seconds=handling, duration_seconds=duration,
            duration_margin_seconds=panel['T_seconds'] - duration))
    assert cars == set(range(panel['M']))
    assert sum(y[1:]) == sum(b[1:]) - sum(r['return_load'] for r in routes)
    assert y[1:] == target[1:] and all(t > 0 for t in target[1:])
    ratios = [F(y[i], target[i]) for i in range(1, len(y))]
    G = sum(abs(x - z) for j, x in enumerate(ratios) for z in ratios[j + 1:]) / (len(ratios) * sum(ratios))
    P = sum(F(str(weights[i])) * abs(ratios[i-1] - 1) for i in range(1, len(y)))
    objective = G + F(str(panel['lambda'])) * P
    assert objective == G == P == 0 and all(w >= 0 for w in weights) and panel['lambda'] >= 0
    assert ind['own_exact_zero'] is True and ind['own_U'] == 0 and ind['independent_floor0'] is True
    assert all(ind['physical'][k] == 0 for k in ['G', 'P', 'F'])
    assert all(result[k] == 0 for k in ['upper_bound', 'lower_bound', 'objective'])
    # The same own witness lies in the call's admitted G/cutoff scope. No P arm is used.
    scope = events[9]
    assert scope['kind'] == 'call' and scope['call'] == 4 and not scope['full_original']
    assert scope['lower_g'] <= G <= scope['upper_g'] and objective <= scope['cutoff']
    model = DEST / 'external/models/L0_epoch_0_generation_1.lp'
    assert digest(model) == scope['model_sha256']
    contracts = read(DEST / 'round120_model_contracts.json')
    saved_scope = next(c for c in contracts['contracts'] if c['call'] == 4)
    assert saved_scope['SHA'] == scope['model_sha256']
    assert saved_scope['scope']['metadata_scope_is_actual_model_scope'] is True
    assert (saved_scope['scope']['saved_G_lower'], saved_scope['scope']['saved_G_upper'], saved_scope['scope']['saved_objective_cutoff']) == (scope['lower_g'], scope['upper_g'], scope['cutoff'])
    local = read(DEST / 'claim_rejections.json')
    assert local['damaged_calls'] == [dict(arm='M-B', call=4)] and len(local['rejections']) == 3
    rejected = []
    for seq, rejection in zip([17,18,19], local['rejections']):
        event = events[seq]
        assert event['kind'] == 'bound' and event['call'] == 4
        assert event['native_bound'] == rejection['value'] > float(objective) + 1e-7
        assert rejection['counterexample']['arm'] == 'M-B' and rejection['counterexample']['F'] == 0
        assert rejection['counterexample']['source'] == ownzero['source']
        assert rejection['reason'] == 'local_bound_witness_inconsistency' and rejection['call_rejected_as_a_whole'] is True
        rejected.append(dict(call=4, sequence=seq, native_bound=event['native_bound'],
            excess_over_own_objective=event['native_bound'], original_global_available=event['global_available']))
    # Check producer byte closure and subsequent necessary verification, without
    # treating the deliberately pending pre-close evidence snapshot as terminal.
    producer = read(DEST / 'producer_receipt.json')
    seal = read(DEST / 'producer_seal.json')
    assert producer['producer_seal_SHA'] == digest(DEST / 'producer_seal.json')
    for name, h in seal['required_SHA'].items():
        assert digest(DEST / name) == h
    for name in ['result.json', 'observations.json', 'completion.json']:
        assert digest(DEST / name) == ind[name.removesuffix('.json') + '_SHA']
    closeout = read(DEST / 'verification_closeout.json')
    total = read(DEST / 'arm_total_receipt.json')
    for key, name in [('audit_SHA','audit.json'),('own_evidence_SHA','independent_evidence.json'),
            ('claims_SHA','native_claims.json'),('rejection_SHA','claim_rejections.json'),
            ('metrics_SHA','audit_execution_metrics.json'),('producer_receipt_SHA','producer_receipt.json')]:
        assert closeout[key] == digest(DEST / name)
    assert closeout['necessary_verification_complete'] and closeout['no_new_solution_or_certificate_backfilled']
    assert closeout['native_proof_qualified'] is False
    assert total['producer_receipt_SHA'] == digest(DEST / 'producer_receipt.json')
    assert total['verification_closeout_SHA'] == digest(DEST / 'verification_closeout.json')
    assert total['necessary_verification_complete']
    assert producer['T_produce'] == producer['t_produce_perf'] - producer['t0_perf']
    assert total['T_verify'] == total['t_verified_perf'] - producer['t_produce_perf']
    assert total['T_total'] == total['t_verified_perf'] - producer['t0_perf']
    assert abs(total['T_total'] - producer['T_produce'] - total['T_verify']) < 1e-8
    assert producer['required_outputs_closed'] and producer['native_stopped_no_reentry']
    assert producer['T_produce'] <= producer['cap_seconds'] == launch['cap_seconds']
    completion = read(DEST / 'completion.json')
    assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
    raw = next(a for a in read(CAMP / 'reconstructed.json')['arms'] if a['method'] == 'S2')
    assert raw['source_reduced'] is True and raw['native_proof_qualified'] is False
    assert raw['certificate'] is True and raw['own_exact_zero'] is True
    assert raw['certificate_source'] == 'OWN_ZERO_CERTIFICATE' and raw['U'] == raw['L'] == raw['gap'] == 0
    assert raw['T_cert'] == raw['T_produce'] == producer['T_produce']
    assert all(raw[k] is True for k in ['formal_protocol_qualified', 'numbers_qualified', 'certificate_qualified'])
    source_ids = {n:digest(ROOT / n) for n in ['scripts/round114_claims.py','scripts/read_round116.py',
        'scripts/round115_common.py','scripts/round127_analysis.py','scripts/round132_analysis.py']}
    binding = read(OUT / 'D_execution_binding.json')
    assert binding['groups']['campaign/D_group24'] == digest(CAMP / 'identity.json')
    assert digest(OUT / 'experiment_plan.json') == binding['plan_SHA']
    assert digest(OUT / 'D_argv_freeze.json') == binding['argv_SHA']
    return dict(status='FINITE_ONE_ARM_FINDINGS_CONFIRMED', full_final_review=False,
        scope='Only D_group24 X-35-U Seed1 S2 own fleet, three rejected call4 bounds, original seals and clocks; saved model hash/scope receipt, not a full model replay.',
        own_zero=dict(G=str(G),P=str(P),F=str(objective),integer_inventory_matches_target=True,
            original_station_stock=sum(b[1:]),final_station_stock=sum(y[1:]),fleet_return=sum(r['return_load'] for r in routes),
            witness_sequence=21,witness_SHA=digest(DEST/'journal/event_21.json'),requires_P_certificate=False,routes=routes),
        source_loss=dict(real=True,damaged_calls=local['damaged_calls'],rejections=rejected,
            rejected_call_proof_reliability_restored=False,pruning_correctness_or_native_cause_inferred=False,
            own_zero_rejects_same_call_bounds=True),
        measured_clocks={k:raw[k] for k in ['T_produce','T_verify','T_total','T_cert']},
        disposition=dict(raw_certificate_retained=True,raw_certificate_source='OWN_ZERO_CERTIFICATE',raw_U=0,raw_L=0,
            raw_and_frozen_scripts_modified=False,formal_performance_eligible=False,formal_performance_T_cert=None,
            formal_pair_direction='UNEVALUABLE',formal_censoring=None,own_physical_rows_retained=True,
            all_cost_timing_and_trajectory_rows_retained=True,native_retry_needed=False,
            reason='Frozen R127 qualified() excludes source_reduced evidence, even when independently exact physical zero plus objective floor remains valid.',
            report_completable_with_explicit_source_loss=True,native_proof_correctness_claim_for_rejected_call_remains_unavailable=True),
        source_identities=source_ids,checked_inputs=INPUTS,no_Optimize=True,no_native_import=True,
        no_campaign_wide_replay=True,elapsed_seconds=time.perf_counter()-started)


if __name__ == '__main__':
    value = check()
    p = OUT / 'review/source_loss_narrow_check.json'
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:value[k] for k in ['status','own_zero','measured_clocks','elapsed_seconds']}))
