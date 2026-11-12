"""Independent Round163 offline execution/data check, standard library only.

Author: canonical independent agent /root/round163_execution_review.
No project imports, solver bindings, subprocesses, model construction, H or
inventory producer. The root agent must meter execution. Only this review's
JSON output is written. Fleet objectives use exact rational arithmetic and a
sorted-ratio Gini identity, independent of the inherited pairwise fleet reader.
"""
import argparse
import ast
import collections
import csv
import datetime
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

AGENT = '/root/round163_execution_review'
TOL = 1e-7
PE_SHA = 'fa7283b0ad3e54dc47315ea3d5987a0aaf8daefe58048beb3dae4be76642be93'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
CPP = 'e920b92e199e825ec89a2932f701861ff158e0d4'
SPECS = [
    ('R163-C20-S', 'CITI', 20, 'shortage', 'compact', 1, 5400, 1200),
    ('R163-B20-B', 'CABI', 20, 'balanced', 'regional', 1, 7200, 1200),
    ('R163-X20-S', 'DIVVY', 20, 'shortage', 'compact', 2, 5400, 1200),
    ('R163-C35-U', 'CITI', 35, 'surplus', 'regional', 2, 10800, 2400),
    ('R163-B35-S', 'CABI', 35, 'shortage', 'compact', 1, 7200, 2400),
    ('R163-X35-S', 'DIVVY', 35, 'shortage', 'regional', 2, 10800, 2400)]
ORDERS = [('P', 'B', 'Eplus'), ('B', 'Eplus', 'P'), ('Eplus', 'P', 'B')] * 2
OFF = ['--round146-gd', '--round148-shared-s', '--round149-penalty-feedback',
       '--round151-penalty-propagation', '--round143-rn', '--round144-projection',
       '--round145-projection', '--round140-counts', '--round141-count-proof',
       '--round142-count-products', '--round160-physical-neighborhood',
       '--round162-physical-completion']
PROOF = ['--round153-root-floor', '--round154-proof-floor', '--round156-rn-refinement']


def require(value, message):
    if not value:
        raise AssertionError(message)


def same(a, b, message, tol=TOL):
    require(math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol,
            f'{message}: {a!r} versus {b!r}')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        while True:
            block = stream.read(1024*1024)
            if not block:
                return h.hexdigest()
            h.update(block)


def tab(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def local(root, value):
    value = str(value).replace('\\', '/')
    if value.startswith(str(root).replace('\\', '/') + '/'):
        return Path(value)
    for marker in ('results/', 'scripts/', 'src/', 'include/', 'config/', 'reference/'):
        if marker in value:
            return root / value[value.index(marker):]
    return Path(value) if Path(value).is_absolute() else root/value


def parse_input(path):
    text = path.read_text(encoding='utf-8-sig')
    match = re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\[[^\n]+\])\s*', text.splitlines()[0])
    require(match is not None, f'input header {path}')
    n, m = int(match[1]), int(match[2])
    a = {'V': n, 'M': m, 'Q': ast.literal_eval(match[3])}
    for field in ('capacities', 'initial', 'target', 'weights', 'min_ratio', 'points'):
        found = re.findall(r'^\s*' + field + r'\s*=\s*(\[[^\n]+\])\s*$', text, re.M)
        require(len(found) == 1, f'unique input vector {field}')
        a[field] = ast.literal_eval(found[0])
        require(len(a[field]) == n+1, f'input length {field}')
    require(len(a['Q']) == m and all(type(q) is int and q > 0 for q in a['Q']), 'fleet capacity')
    for field in ('capacities', 'initial', 'target'):
        require(all(type(x) is int for x in a[field]), f'integer input {field}')
    for i in range(1, n+1):
        require(0 <= a['initial'][i] <= a['capacities'][i] < 100, f'input inventory {i}')
        require(0 < a['target'][i] <= a['capacities'][i], f'input target {i}')
    require(all(len(xy) == 2 and all(math.isfinite(v) for v in xy) for xy in a['points']), 'finite points')
    require(all(math.isfinite(w) and w >= 0 for w in a['weights']), 'finite nonnegative weights')
    raw = list(a['weights'])
    scaled = abs(max(raw[1:])-10.) <= 1e-6
    a['weights'] = [raw[0]] + [w/10 if scaled else w for w in raw[1:]]
    # Exact decimal weights independently preserve all six serialized values.
    a['rational_weights'] = [Fraction(str(w)) / (10 if scaled and i else 1)
                             for i, w in enumerate(raw)]
    a['legacy_max10_scaled'] = scaled
    require(sum(a['weights'][1:]) > 0, 'positive Omega')
    return a


def math_keys(a, p):
    hx = lambda x: float(0 if x == 0 else x).hex()
    stations = sorted((hx(a['points'][i][0]), hx(a['points'][i][1]), a['capacities'][i],
                       a['initial'][i], a['target'][i], hx(a['weights'][i])) for i in range(1, a['V']+1))
    hash_json = lambda v: hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    base = hash_json(dict(n=a['V'], M=a['M'], Q=sorted(a['Q']),
                         depot=[hx(x) for x in a['points'][0]], stations=stations))
    full = hash_json(dict(base=base, T=hx(p['T_seconds']), lam=hx(p['lambda']),
                         tp=hx(p['pickup_seconds']), td=hx(p['drop_seconds'])))
    return base, full


def fleet(a, p, witness):
    """Replay each vehicle from zero load, then include depot unloading."""
    n, m = a['V'], a['M']
    inventory = list(a['initial'])
    seen, cars, details = set(), set(), []
    for route in witness['routes']:
        k = route.get('vehicle', route.get('vehicle_id'))
        require(type(k) is int and 0 <= k < m and k not in cars, 'unique valid vehicle')
        cars.add(k)
        nodes = route['nodes']
        require(len(nodes) >= 2 and nodes[0] == nodes[-1] == 0, 'closed depot route')
        require(all(type(i) is int and 0 <= i <= n for i in nodes), 'valid route nodes')
        require(len(set(nodes[1:-1])) == len(nodes)-2 and 0 not in nodes[1:-1], 'simple station route')
        operations = {}
        for op in route['operations']:
            i, take, give = (op['station'], op['pickup'], op['drop']) if isinstance(op, dict) else op
            require(all(type(x) is int for x in (i, take, give)), 'integer operation')
            require(i not in operations and take >= 0 and give >= 0 and (take > 0) != (give > 0), 'one-direction positive service')
            operations[i] = take, give
        require(set(operations) == set(nodes[1:-1]), 'operations equal visited stations')
        load, pickups, drops, prefixes = 0, 0, 0, [0]
        for i in nodes[1:-1]:
            require(i not in seen, 'cross-vehicle station disjointness')
            seen.add(i)
            take, give = operations[i]
            load += take-give
            pickups += take
            drops += give
            prefixes.append(load)
            require(0 <= load <= a['Q'][k], f'prefix load vehicle {k}')
            inventory[i] += give-take
            require(0 <= inventory[i] <= a['capacities'][i], f'station inventory {i}')
        travel = math.fsum(math.hypot(a['points'][j][0]-a['points'][i][0],
                                      a['points'][j][1]-a['points'][i][1])/1.5
                           for i, j in zip(nodes, nodes[1:]))
        handling = p['pickup_seconds']*pickups + p['drop_seconds']*(drops+load)
        duration = travel+handling
        require(duration <= p['T_seconds']+TOL, f'physical T vehicle {k}: {duration}')
        details.append(dict(vehicle=k, visited=len(nodes)-2, pickups=pickups, station_drops=drops,
                            depot_unload=load, min_prefix=min(prefixes), max_prefix=max(prefixes),
                            travel_seconds=travel, handling_seconds=handling, duration_seconds=duration,
                            time_slack_seconds=p['T_seconds']-duration))
    missing = sorted(set(range(m))-cars)
    for k in missing:
        details.append(dict(vehicle=k, explicit_empty_completion=True, visited=0, depot_unload=0,
                            duration_seconds=0, time_slack_seconds=p['T_seconds']))
    require(sum(inventory[1:]) + sum(r['depot_unload'] for r in details) == sum(a['initial'][1:]),
            'fleet-wide stock conservation with depot returns')
    ratios = [Fraction(inventory[i], a['target'][i]) for i in range(1, n+1)]
    ordered, total = sorted(ratios), sum(ratios, Fraction(0))
    g = sum(((2*i-n+1)*r for i, r in enumerate(ordered)), Fraction(0))/(n*total) if total else Fraction(0)
    penalty = sum((a['rational_weights'][i]*abs(ratios[i-1]-1) for i in range(1, n+1)), Fraction(0))
    objective = g + Fraction.from_float(float(p['lambda']))*penalty
    for field, value in [('G', g), ('P', penalty), ('objective', objective)]:
        reported = witness.get(field, witness.get('F') if field == 'objective' else None)
        if reported is not None:
            same(float(value), reported, f'recomputed fleet {field}')
    return dict(feasible=True, complete_fleet_vehicles=m, empty_vehicles_added=missing,
                G=float(g), P=float(penalty), U=float(objective), final_inventory=inventory,
                vehicles=sorted(details, key=lambda v: v['vehicle']))


def argv_flags(command):
    found, index = {}, 1
    while index < len(command):
        flag = command[index]
        require(flag.startswith('--') and flag not in found, f'unique CLI flag {flag}')
        if flag == '--plain-baseline':
            found[flag], index = True, index+1
        else:
            require(index+1 < len(command) and not command[index+1].startswith('--'), f'CLI value {flag}')
            found[flag], index = command[index+1], index+2
    return found


def journal_anchor(d, item):
    event = item['payload']
    path = d/'journal'/f'event_{event["sequence"]}.json'
    require(digest(path) == item['sha256'] and read(path) == event, 'raw committed journal anchor')
    commit = path.with_suffix('.commit').read_text().split()
    require(commit[0] == 'NEJ1' and int(commit[1]) == event['sequence'] and
            int(commit[3]) == path.stat().st_size and commit[4] == item['sha256'], 'journal commit receipt')


def raw_lower(d, method, endpoint, report):
    if method == 'P':
        r = read(d/'result.json')
        same(r['native_mip_best_bound'], endpoint['L'], 'cold native bound')
        native = (d/'native.log').read_text(encoding='utf-8', errors='strict')
        values = re.findall(r'Best objective [^,]+, best bound ([^,]+), gap', native)
        require(values, 'cold final native log bound')
        same(float(values[-1]), endpoint['L'], 'cold printed final bound')
        return endpoint['L']
    trace, leaves = tab(d/'external/global_bound_trace.csv'), tab(d/'external/paper_leaf_ledger.csv')
    require(trace and leaves, 'complete raw interval bound evidence')
    previous = -math.inf
    for row in trace:
        candidates = [float(row['verified_global_upper_bound'])]
        candidates += [float(row[k]) for k in ('active_leaf_valid_lower_bound', 'other_open_leaf_min_valid_lower_bound') if row[k] != '']
        value = min(candidates)
        same(value, float(row['valid_global_lower_bound']), 'unclipped interval-cover readback')
        require(value >= previous-TOL, 'monotonic valid search bound')
        previous = value
    live = [r for r in leaves if r['status'] not in ('replaced', 'coalesced')]
    require(live, 'nonempty final interval cover')
    covered = 0.
    for leaf in sorted(live, key=lambda v: float(v['gamma_L'])):
        lo, hi = float(leaf['gamma_L']), float(leaf['gamma_U'])
        require(0 <= lo <= hi and lo <= covered+TOL and leaf['status'] != 'invalid', 'final interval coverage')
        covered = max(covered, hi)
    require(covered+TOL >= min(endpoint['U'], 1-1/endpoint['V']), 'whole relevant true-G domain covered')
    lower = min([endpoint['U']] + [float(r['lower_bound']) for r in live])
    same(lower, previous, 'final leaves versus trace')
    if method == 'B':
        same(lower, report['raw_search_L'], 'reported raw search L')
        same(lower, endpoint['L'], 'stable proof lower is full search cover')
        return lower
    # R154 exports its proof copy at finalization. The separate raw-search
    # scheduler survives in the committed proof ledger and the pre-final trace.
    # Rebuild both full covers; never rename the proof lower as raw search L.
    audit = read(d/'round154_control_audit.json')
    ledger_path = d/'external/round154_proof_ledger.json'
    ledger = read(ledger_path)
    require(digest(ledger_path) == audit['proof_ledger_SHA'] and ledger == audit['proof_ledger'],
            'actual raw/proof ledger bytes and qualified audit binding')
    meta = read(d/'external/models/round153_root.json')
    by_id = {v['id']: v for v in ledger['leaves']}
    require(len(by_id) == len(ledger['leaves']) and set(by_id) == {v['leaf_id'] for v in leaves},
            'raw/proof ledger contains every original scheduler leaf')
    raw_values, proof_values = [], []
    for leaf in live:
        record = by_id[leaf['leaf_id']]
        same(record['gamma_L'], float(leaf['gamma_L']), 'raw/proof leaf lower scope', 1e-12)
        same(record['gamma_U'], float(leaf['gamma_U']), 'raw/proof leaf upper scope', 1e-12)
        raw = record['raw_search_lower']
        require(math.isfinite(raw) and raw >= -TOL, 'finite qualified raw leaf lower')
        eligible = (meta['qualified'] and ledger['root_complete'] and ledger['source_qualified'] and
                    ledger['sources_live'] and record['gamma_L'] >= meta['gamma_L'] and
                    record['gamma_U'] <= meta['gamma_U'] and record['cutoff'] <= meta['own_cutoff'])
        composed = max(raw, min(meta['own_cutoff'], meta['lower'])) if eligible else raw
        same(composed, record['proof_lower'], 'scope-correct leaf proof-floor composition')
        same(composed, float(leaf['lower_bound']), 'exported final proof leaf')
        if composed > raw+TOL:
            require('round154_own_root_floor' in leaf['lower_bound_sources'].split(';'),
                    'extra leaf information has explicit own-root provenance')
        raw_values.append(raw)
        proof_values.append(composed)
    search_lower = min([endpoint['U']] + raw_values)
    proof_lower = min([endpoint['U']] + proof_values)
    same(search_lower, ledger['raw_search_L'], 'raw complete-cover reconstruction')
    same(search_lower, report['raw_search_L'], 'reported raw search L')
    prefinal = [row for row in trace if row['event_type'] != 'finalization']
    require(prefinal, 'actual raw-search trace before proof export')
    same(float(prefinal[-1]['valid_global_lower_bound']), search_lower,
         'raw Native/search trace versus separate raw complete cover')
    same(proof_lower, ledger['proof_L'], 'proof complete-cover reconstruction')
    same(proof_lower, lower, 'proof ledger versus exported final cover')
    same(proof_lower, endpoint['L'], 'proof cover versus qualified endpoint')
    return search_lower


def run(root, out):
    matrix, manifest = read(out/'matrix_frozen.json'), read(out/'input_manifest.json')
    candidate, helper = read(out/'candidate_manifest.json'), read(out/'helper_manifest_Eplus.json')
    freeze, identity = read(out/'method_freeze.json'), read(out/'science_identity.json')
    reports = read(out/'reports/complete_arms.json')
    report_by = {a['position']: a for a in reports}
    require(len(reports) == len(matrix['groups']) == 18 and len(report_by) == 18, '18 unique actual arms')
    require(read(out/'panel_complete.json')['arms'] == 18 and len(manifest['roles']) == 6, 'complete six configurations')
    for name, value in [('candidate_manifest.json', matrix['candidate_manifest_SHA256']),
                        ('input_manifest.json', matrix['input_manifest_SHA256']),
                        ('method_freeze.json', matrix['method_freeze_SHA256']),
                        ('helper_manifest_Eplus.json', matrix['helper_manifest_SHA256'])]:
        require(digest(out/name) == value, f'actual freeze bytes {name}')
    require(candidate['source_commit'] == CPP and identity['measured_CPP_commit'] == CPP, 'measured C++ source')
    require(digest(candidate['production_PE']) == PE_SHA and digest(candidate['DLL']) == DLL_SHA, 'actual shared runtime images')
    for mapping in (candidate['source_hashes'], matrix['helpers'], helper['helper_dependencies']):
        for name, value in mapping.items():
            require(digest(root/name) == value, f'frozen source/helper dependency {name}')
    require(digest(helper['python']) == helper['python_SHA'] if 'python' in helper else True, 'frozen helper Python')
    require(freeze['rn_nodes'] == 16384 and freeze['price_absolute_gap'] == 1e-4 and freeze['old_joint'], 'frozen E+ capacity')
    parsed, inputs = {}, []
    used = collections.defaultdict(set)
    effective = read(out/'effective_input_novelty.json')
    attempts = read(out/'generation_attempts.json')
    require(len(attempts) == 6 and all(a['k'] == 0 and not a['collision'] for a in attempts), 'six retained first draws')
    old_keys = {a['base_key'] for a in effective['old']}
    for spec, p in zip(SPECS, manifest['roles']):
        actual = tuple(p[k] for k in ('id', 'source', 'V', 'inventory', 'geometry', 'replicate', 'T_seconds', 'cap_seconds'))
        require(actual == spec, f'prospective config contract {p["id"]}')
        a = parse_input(root/p['input_path'])
        require(digest(root/p['input_path']) == p['input_sha256'], 'actual input digest')
        require((a['V'], a['M'], a['Q']) == (p['V'], p['M'], p['Q_vector']), 'actual complete fleet input')
        require(a['Q'] == ([30, 30] if p['V'] == 20 else [20, 25, 30]), 'prespecified fleet')
        omega = math.fsum(a['weights'][1:])
        same(omega, p['Omega'], 'actual serialized Omega', 1e-12)
        same(p['lambda'], 1/omega, 'rho=1 normalization', 1e-14)
        require(not a['legacy_max10_scaled'] and p['rho'] == 1, 'new max-one actual weights')
        require(float(p['lambda_decimal17']) == p['lambda'] and float.fromhex(p['lambda_binary64']) == p['lambda'], 'actual lambda precision')
        base, full = math_keys(a, p)
        require((base, full) == (p['normalized_base_key'], p['normalized_full_key']), 'independent input math keys')
        require(base not in old_keys and effective['new_keys'][p['id']] == {'base': base, 'full': full}, 'effective historical novelty readback')
        selection = read(root/p['selection_path'])
        chosen = set(selection['selected_source_station_row_indices'])
        require(len(chosen) == p['V'] and not used[p['source']] & chosen, 'within-panel source disjointness')
        used[p['source']] |= chosen
        require(selection['selection_id'] == p['selection_id'] == 'r163_'+p['id'], 'landscape selection identity')
        delta = sum(a['initial'][1:])-sum(a['target'][1:])
        require((delta < 0, delta == 0, delta > 0) == (p['inventory'] == 'shortage', p['inventory'] == 'balanced', p['inventory'] == 'surplus'), 'actual inventory scenario')
        parsed[p['id']] = a
        inputs.append(dict(id=p['id'], input_SHA256=p['input_sha256'], n=a['V'], M=a['M'], Q=a['Q'],
                           Omega=omega, actual_lambda=p['lambda'], base_key=base, full_key=full,
                           legacy_max10_scaled=a['legacy_max10_scaled'], source_rows=len(chosen)))
    require(len({a['base_key'] for a in inputs}) == len({a['full_key'] for a in inputs}) == 6, 'six distinct mathematical inputs')
    arms, last_exit, pids = [], 0., set()
    expected_sequence = [(s[0], method) for s, order in zip(SPECS, ORDERS) for method in order]
    for group, expected in zip(matrix['groups'], expected_sequence):
        launch, pos = group['launch'], group['position']
        p, method = launch['panel'], launch['R163_method']
        require((p['id'], method) == expected and pos == len(arms)+1, 'prespecified complete arm order')
        d, r = local(root, launch['destination']), report_by[pos]
        require(d.parent == out/'campaign'/f'{pos:03}'/'raw' and d.name == launch['arm_id'], 'actual owned raw destination')
        raw_launch = read(d/'launch.json')
        own_identity = read(out/group['group']/'identity.json')
        require(all(raw_launch.get(key) == value for key, value in launch.items()) and
                own_identity['launches'] == [launch], 'actual frozen argv/identity')
        require(set(raw_launch)-set(launch) <= {'prelaunch_seconds', 'prereg_sha256', 'runner_sha256'},
                'only observed supervisor metadata extends raw launch')
        require(raw_launch['prereg_sha256'] == own_identity['prereg_sha256'] and
                raw_launch['runner_sha256'] == own_identity['runner_sha256'] and
                raw_launch['prelaunch_seconds'] >= 0, 'bound supervisor metadata')
        require(digest(out/group['group']/'identity.json') == group['identity_SHA256'], 'own identity SHA')
        flags = argv_flags(launch['command'])
        require('--round138-stock-rlt' not in flags and '--round112-ens-start-compact' not in flags, 'no stock or PS switch')
        for flag in OFF:
            require(flags[flag] == 'off', f'inactive mechanism {flag}')
        for flag in PROOF:
            require(flags[flag] == ('on' if method == 'Eplus' else 'off'), f'method proof contract {flag}')
        require(flags['--method'] == ('gurobi' if method == 'P' else 'gcap-frontier') and
                flags['--round127-mode'] == ('p' if method == 'P' else 'ms2'), 'complete method identity')
        require(('--plain-baseline' in flags) == (method == 'P') and ('--algorithm-preset' in flags) == (method != 'P'), 'clean P versus B/E+ entry')
        require(flags['--threads'] == flags['--mip-threads'] == '1' and flags['--gurobi-seed'] == '0', 'common threads/Seed')
        require(local(root, flags['--input']) == root/p['input_path'], 'argv actual input')
        for flag, value in [('--lambda', p['lambda']), ('--T', p['T_seconds']), ('--pickup-time', 60), ('--drop-time', 60),
                            ('--process-wall-time-limit', p['cap_seconds']), ('--time-limit', p['cap_seconds']-6), ('--process-shutdown-margin', 30)]:
            require(float(flags[flag]) == value, f'actual CLI {flag}')
        require(not any('node-limit' in flag for flag in flags), 'no finite Native development NodeLimit')
        endpoint, result = read(d/'round163_endpoint.json'), read(d/'result.json')
        producer, clock = read(d/'producer_receipt.json'), read(d/'arm_total_receipt.json')
        fee = read(out/'fees'/f'arm_{pos:03}'/'receipt.json')
        origin, osbind = read(d/'child_process_origin.json'), read(out/group['group']/'runtime_os_binding.json')
        completion, closeout = read(d/'completion.json'), read(d/'verification_closeout.json')
        require(origin['command'] == launch['command'] and origin['PE_SHA'] == PE_SHA and origin['source_commit'] == CPP, 'actual launched source/PE/argv')
        require(origin['pid'] not in pids and origin['actual_creation_unix'] >= last_exit, 'fresh serial processes')
        pids.add(origin['pid'])
        last_exit = fee['end_unix']
        require(osbind['PID'] == origin['pid'] and osbind['PE'] == launch['command'][0] and
                osbind['PrelaunchSHA'] == PE_SHA and osbind['ProcessorAffinity'] == 4, 'live OS common binding')
        require(any(v['FileName'] == candidate['DLL'] for v in osbind['DLL']), 'live loaded Gurobi DLL')
        require(fee['exit_observed'] and fee['exit_code'] == 0 and not fee['timeout'], 'healthy formal fee exit')
        require(completion['returncode'] == 0 and completion['within_cap'] and completion['stop_reason'] == 'normal_return', 'normal producer close')
        require(producer['required_outputs_closed'] and producer['native_stopped_no_reentry'] and producer['T_produce'] <= p['cap_seconds'], 'single paid producer deadline')
        for key in ('implementation_qualified', 'evidence_complete', 'performance_eligible'):
            require(endpoint[key] and closeout[key] and r[key], f'qualified evidence {key}')
        require(endpoint['input_SHA'] == p['input_sha256'] and endpoint['PE_SHA'] == PE_SHA and endpoint['DLL_SHA'] == DLL_SHA, 'endpoint actual identity')
        seal = read(d/'producer_seal.json')
        for name, value in seal['required_SHA'].items():
            require(digest(d/name) == value, f'raw sealed producer output {pos}:{name}')
        physical = fleet(parsed[p['id']], p, result)
        same(physical['U'], endpoint['U'], 'raw final fleet versus endpoint U')
        same(physical['U'], r['U'], 'raw final fleet versus report U')
        for key in ('physical_G', 'physical_P'):
            same(physical[key[-1]], r[key], 'physical report component')
        for key in ('U', 'L', 'T_produce'):
            same(r[key], endpoint[key], f'report transport {key}')
        observations = read(d/'observations.json')
        require(len(observations) == completion['committed_events'], 'actual committed event count')
        calls, returned, not_started, startups = {}, set(), set(), []
        for item in observations:
            event = item['payload']
            kind = event['kind']
            if kind in ('identity', 'call', 'returned', 'not_started') or (kind == 'witness' and event.get('source') == 'same_run_verified_startup'):
                journal_anchor(d, item)
            if kind == 'identity':
                require(event['input_sha256'] == p['input_sha256'] and event['lambda'] == p['lambda'] and
                        (event['T'], event['pickup_seconds'], event['drop_seconds']) == (p['T_seconds'], 60, 60), 'raw journal physical identity')
            elif kind == 'call':
                require(event['call'] not in calls, 'unique actual Native call')
                calls[event['call']] = event
                require(digest(local(root, event['model_path'])) == event['model_sha256'], 'actual Native model bytes')
                for key, value in dict(Threads=1, Seed=0, Presolve=-1, MIPFocus=0, Cuts=-1, MIPGap=0, MIPGapAbs=0).items():
                    require(event['settings'][key] == value, f'actual q0 parameter {key}')
            elif kind == 'returned':
                require(event['return_code'] == 0, 'returned Native call success')
                returned.add(event['call'])
            elif kind == 'not_started':
                require(not event['actual_Optimize'], 'deadline skip is no Optimize')
                not_started.add(event['call'])
            elif kind == 'witness' and event.get('source') == 'same_run_verified_startup':
                startups.append(event)
        require(not returned & not_started and returned | not_started == set(calls), 'all Native intentions closed')
        require(len(calls) == r['Native_calls'], 'actual call count readback')
        startup = None
        if method == 'P':
            parameters = read(d/'round127_parameters.json')
            require(parameters == dict(MIPFocus=0, Cuts=-1, NumStart_before_optimize=0,
                                       loaded_after_presets=True, authoritative_model_environment=True), 'cold P NumStart0')
            require(not startups and not endpoint.get('H_complete', False), 'P has no supplied own H')
            require(len(calls) == 1 and next(iter(calls.values()))['full_original'], 'one cold original model')
        else:
            require(len(startups) == 1 and endpoint['H_complete'], 'own fresh H present')
            startup = fleet(parsed[p['id']], p, startups[0])
            require(startup['final_inventory'] == endpoint['H_final_inventory'], 'own H fleet inventory')
            params = read(d/'round137_parameters.json')
            require(params == dict(split_threshold=.08, delete_ab=False, delete_cr=False, delete_cg=False, loaded_after_presets=True), 'stable B parameter readback')
        search = raw_lower(d, method, endpoint, r)
        helper_seconds, helper_floor = 0., None
        if method == 'Eplus':
            meta, audit = read(d/'external/models/round153_root.json'), read(d/'round154_control_audit.json')
            src = read(d/'external/round153_floor/source.json')
            require(local(root, src['source']).is_relative_to(d/'external/models'), 'own fresh root source path')
            require(digest(local(root, src['source'])) == src['source_SHA'] == meta['source_SHA'], 'own helper source digest')
            require(meta['source_SHA'] in {c['model_sha256'] for c in calls.values()}, 'helper root belongs to actual Native model')
            require(meta['input_SHA'] == p['input_sha256'] and meta['helper_manifest_SHA'] == digest(out/'helper_manifest_Eplus.json'), 'helper input/closure binding')
            require(meta['node_limit'] == src['node_limit'] == 16384 and meta['price_gap_target'] == src['absolute_price_gap'] == 1e-4, 'RN16384 original price gap')
            require(src['no_historical_inventory_or_price_loaded'] and src['own_current_canonical_source'] and src['fresh_RN_tree'], 'fresh own helper')
            require(meta['root_once'] and meta['extra_root_LP'] == meta['formal_new_columns'] == 0 and not meta['offline_data_used'], 'frozen helper semantics')
            helper_seconds, helper_floor = meta['helper_process_seconds'], meta['lower'] if meta['qualified'] else None
            require(0 < helper_seconds <= producer['T_produce'] and helper_seconds <= meta['whole_method_remaining_at_launch']+TOL, 'paid helper deadline')
            same(r['helper_seconds'], helper_seconds, 'actual helper expense')
            ledger = audit['proof_ledger']
            require(audit['proof_only'] and ledger['native_floor_rows'] == 0 and ledger['AM_uses_search_bounds'] and
                    all(v['floor_rows'] == 0 for v in audit['models']), 'no floor in Native rows/raw AM')
            same(ledger['raw_search_L'], search, 'ledger raw search lower')
            composed = max(search, min(meta['own_cutoff'], meta['lower'])) if meta['qualified'] and ledger['root_complete'] and ledger['sources_live'] else search
            same(composed, endpoint['L'], 'qualified proof-only lower composition')
        signed = endpoint['U']-endpoint['L']
        same(r['signed_gap'], signed, 'unclipped signed gap', 1e-12)
        require(endpoint['certificate'] == (signed <= TOL), 'certificate at inherited qualification tolerance')
        require((r['T_cert'] is not None) == endpoint['certificate'], 'OPEN has no convergence time')
        if endpoint['certificate']:
            same(r['T_cert'], producer['T_produce'], 'paid CERT closure time')
        same(r['T_produce'], producer['T_produce'], 'complete production charge')
        trailer = fee['end_unix']-clock['t_verified_unix']
        require(trailer >= 0, 'nonnegative reader exit trailer')
        same(r['T_verify'], endpoint['T_verify']+trailer, 'complete verification expense', 1e-6)
        same(r['T_total'], r['T_produce']+r['T_verify'], 'total equals produce plus verify', 1e-6)
        same(r['scientific_outer_seconds'], fee['outer_seconds'], 'observed scientific outer fee', 1e-6)
        require(0 <= fee['outer_seconds']-r['T_total'] < .2, 'outer wrapper entry expense explicitly retained')
        arms.append(dict(position=pos, id=p['id'], method=method, state=r['state'], physical=physical,
                         own_H=startup, raw_search_L=search, proof_L=endpoint['L'], certificate=endpoint['certificate'],
                         signed_gap=signed, helper_seconds=helper_seconds, helper_floor=helper_floor,
                         T_produce=r['T_produce'], T_verify=r['T_verify'], T_total=r['T_total'],
                         outer_fee_seconds=fee['outer_seconds'], Native_calls=len(calls),
                         returned_calls=len(returned), deadline_skipped_calls=len(not_started),
                         raw_result_SHA256=digest(d/'result.json'), raw_destination=str(d)))
    summary = read(out/'reports/summary.json')['methods']
    for method in ('B', 'Eplus', 'P'):
        current = [a for a in arms if a['method'] == method]
        require(len(current) == 6 and sum(a['certificate'] for a in current) == summary[method]['CERT'], 'all-six certificate denominator')
        for key in ('T_produce', 'T_verify', 'T_total', 'helper_seconds'):
            same(sum(a[key] for a in current), summary[method][key], f'complete method expense {method}/{key}', 1e-6)
    fees, pending = [], []
    for path in sorted((out/'fees').glob('*/launch.json')):
        fee_launch = read(path)
        receipt_path = path.with_name('receipt.json')
        if not receipt_path.exists():
            pending.append(path.parent.name)
            continue
        receipt = read(receipt_path)
        require(receipt['exit_observed'] and receipt['outer_seconds'] >= receipt['G1_seconds'] >= 0, 'all incurred fee receipts retained')
        fees.append(dict(label=path.parent.name, kind=fee_launch['kind'], seconds=receipt['G1_seconds'],
                         outer_seconds=receipt['outer_seconds'], exit_code=receipt['exit_code'], timeout=receipt['timeout']))
    external = read(out/'infra/external_costs.json')['processes']
    charged = sum(f['seconds'] for f in fees)+sum(f['outer_seconds'] for f in external)
    require(charged < 72000, 'total closed science remains below authorized capacity')
    return dict(PASS=True, canonical_agent_identity=AGENT, UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                scope='independent six text-input parses and 18 raw complete-fleet reconstructions, execution identities, counts, q0/cold P, proof-ledger composition and expenses',
                no_project_imports=True, no_solver_or_native_calls=True, no_old_archive_reads=True,
                objective_method='exact rational satisfaction ratios and decimal weights; sorted-ratio Gini identity; actual binary64 lambda',
                physical_method='zero-start prefix loads, global station disjointness, station inventory, travel / 1.5, pickup/drop plus depot unloading, complete unused vehicles',
                proof_limit='Final trace/cover and proof-only composition independently read back; inherited mathematical source qualification and chronological cover audit remain separately required.',
                novelty_timing_departure='History-manifest raw keys, recipe, six first inputs and matrix were sealed before formal panel. Master row-to-input crosswalk began after first-arm exposure and completed post-panel; effective max10 and R57-pilot metadata checks are post-panel strengthenings. No redraw or producer change.',
                inputs=inputs, arms=arms, closed_fee_scientific_seconds=charged, fee_snapshot=fees,
                retained_nonzero_exit_fees=[f for f in fees if f['exit_code'] != 0 or f['timeout']],
                external_initial_preparation=external, pending_fee_labels=pending,
                pending_fee_policy='The root-metered checker itself has no closed receipt until after this JSON is written; final cost closeout must include its actual observed exit.',
                later_CSV_check_required=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    out = root/'results/unified_exact_round163'
    output = args.output or out/'review/execution_readback.json'
    require(output.resolve().is_relative_to(out/'review'), 'only review output may be written')
    tick = time.perf_counter()
    try:
        value = run(root, out)
    except Exception as error:
        value = dict(PASS=False, canonical_agent_identity=AGENT, error_type=type(error).__name__, error=str(error),
                     no_solver_or_native_calls=True, no_project_imports=True)
    value['offline_checker_seconds'] = time.perf_counter()-tick
    value['checker_SHA256'] = digest(Path(__file__))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=value['PASS'], output=str(output), error=value.get('error'),
                          arms=len(value.get('arms', [])), seconds=value['offline_checker_seconds'])))
    return 0 if value['PASS'] else 1


if __name__ == '__main__':
    sys.exit(main())
