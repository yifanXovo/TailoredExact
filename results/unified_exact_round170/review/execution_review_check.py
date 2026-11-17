"""Independent R170 execution/data/cost readback. Standard library only.

This file never imports producer, qualification, model or solver modules and
never launches subprocesses. Its only writes are this reviewer's JSON reports.
"""
from pathlib import Path
from datetime import datetime, timezone
import collections
import csv
import hashlib
import io
import json
import math
import re
import sys
import time
import zipfile
import gzip

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round170'
REVIEW = OUT / 'review'
START = 1794905664.6404333  # First instrumented independent data read, UTC.
REVIEWER = '/root/execution_review'
PE_SHA = 'c6ddf0b62f1200d02a8c654fd3f278ced704130f1a8950fc1e6464b9cbb11e57'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
MEASURED = '781c548b410a2749190e3f0c4b149c2ad885c054'
MODE = {'B': 'off', 'C': 'reweight', 'M': 'multistart', 'P': 'off'}
HASHES = {}
ERRORS = []
CHECKS = collections.Counter()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    p = Path(path)
    key = (str(p.resolve()), p.stat().st_size, p.stat().st_mtime_ns)
    if key not in HASHES:
        HASHES[key] = hashlib.sha256(p.read_bytes()).hexdigest()
    return HASHES[key]


def bind(path):
    p = Path(path)
    return {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),
            'bytes': p.stat().st_size, 'SHA256': sha(p)}


def csvrows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check(ok, group, message, **details):
    CHECKS[group] += 1
    if not ok:
        ERRORS.append({'group': group, 'message': message, **details})


def near(a, b, tolerance=1e-9):
    return isinstance(a, (float, int)) and isinstance(b, (float, int)) and math.isclose(a, b, rel_tol=1e-10, abs_tol=tolerance)


def same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if a is None or b is None:
        return a is b
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return near(a, b, 1e-10)
    return a == b


def argv_tokens(argv):
    tokens = {}
    i = 1
    while i < len(argv):
        key = argv[i]
        check(key.startswith('--') and key not in tokens, 'argv', 'Unique option', key=key)
        if key == '--plain-baseline':
            tokens[key] = True
            i += 1
        else:
            tokens[key] = argv[i + 1]
            i += 2
    return tokens


def table_twins(json_rows, path):
    exported = csvrows(path)
    check(len(exported) == len(json_rows), 'CSV_twins', 'CSV/JSON row count agrees', file=str(path.relative_to(OUT)))
    for index, (csv_row, json_row) in enumerate(zip(exported, json_rows), 1):
        check(list(csv_row) == list(json_row), 'CSV_twins', 'CSV/JSON schema agrees', file=str(path.relative_to(OUT)), row=index)
        for key, value in json_row.items():
            actual = csv_row[key]
            if value is None:
                ok = actual == ''
            elif isinstance(value, (dict, list)):
                ok = json.loads(actual) == value
            elif isinstance(value, bool):
                ok = actual == str(value)
            elif isinstance(value, (float, int)):
                ok = float(actual) == value
            else:
                ok = actual == value
            check(ok, 'CSV_twins', 'CSV retains actual JSON endpoint/cost/provenance value', file=str(path.relative_to(OUT)), row=index, key=key)


def result(path):
    value = read(path)
    return value[0] if isinstance(value, list) else value['results'][0] if 'results' in value else value


def run_review(final=False):
    tick = time.perf_counter()
    matrix = read(OUT / 'matrix_frozen.json')
    candidate = read(OUT / 'candidate_manifest.json')
    environment = read(OUT / 'environment_manifest.json')
    inputs = read(OUT / 'inputs_frozen.json')
    arms = read(OUT / 'complete_arms.json')
    rows = arms['rows']
    by_pos = {x['position']: x for x in rows}
    roles = {x['id']: x for x in inputs['roles']}
    status = read(OUT / 'complete_status.json')
    by_status = {x['position']: x for x in status['records']}
    costs = read(OUT / 'cost_report.json')
    audit_costs = read(REVIEW / 'audit_process_costs.json')
    audit_attempts = read(REVIEW / 'complete_audit_attempts.json')
    hrows = read(OUT / 'h_path_results.json')['rows']
    old_h = read(ROOT / 'results/unified_exact_round169/h_path_results.json')['rows']
    inherited_roles = {x['id']: x for x in read(ROOT / 'results/unified_exact_round163/input_manifest.json')['roles']}
    desired = [
        ('R163-C20-S', 1, 'BC'), ('R163-C35-U', 1, 'MPCB'),
        ('R163-B35-S', 1, 'CBPM'), ('R163-X35-S', 1, 'PMBC'),
        ('R163-C20-S', 2, 'CB'), ('R163-C35-U', 2, 'BC'),
        ('R163-B35-S', 2, 'CB'), ('R163-X35-S', 2, 'BC')]
    expected = [(role, seed, arm) for role, seed, order in desired for arm in order]
    actual = [(p['role'], p['Native_Seed'], p['arm']) for p in matrix['positions']]
    check(actual == expected and len(rows) == 22, 'matrix', 'Exactly the 22 prescribed positions and order')
    check([p['position'] for p in matrix['positions']] == list(range(1, 23)), 'matrix', 'Consecutive prescribed indices')
    check(sorted(p.name for p in (OUT / 'complete_raw').iterdir() if p.is_dir()) == sorted(Path(p['directory']).name for p in matrix['positions']), 'matrix', 'No extra actual raw production directory')
    check(collections.Counter(p['arm'] for p in matrix['positions']) == {'B': 8, 'C': 8, 'M': 3, 'P': 3}, 'matrix', 'Arm counts')
    check(matrix['serial'] and matrix['nominal_process_cap_sum'] == 13200 and matrix['expected_H_calls'] == 41, 'matrix', 'Serial fixed caps and H expectation')
    for key, path in [('candidate_manifest_SHA256', OUT / 'candidate_manifest.json'),
                      ('inputs_SHA256', OUT / 'inputs_frozen.json'),
                      ('runner_SHA256', ROOT / 'scripts/round170_run.py')]:
        check(matrix[key] == sha(path), 'frozen_bindings', key)
    check(datetime.fromisoformat(matrix['UTC']).timestamp() < by_status[1]['receipt']['started_epoch'], 'matrix', 'Frozen before first actual launch')
    check(candidate['source_commit'] == MEASURED and candidate['rebuilt'] is False, 'common_identity', 'Inherited measured source and no rebuild')
    for key, expected_sha in [('PE', PE_SHA), ('DLL', DLL_SHA)]:
        fact = candidate[key]
        check(sha(fact['path']) == expected_sha == fact['SHA256'] == environment[key]['SHA256'], 'common_identity', f'Actual {key} bytes')
        check(Path(fact['path']).stat().st_size == fact['bytes'] == environment[key]['bytes'], 'common_identity', f'Actual {key} length')
    for name, digest in candidate['source_hashes'].items():
        check(sha(ROOT / name) == digest, 'source_bytes', name)
    for fact in list(candidate['actual_build_evidence'].values()) + [candidate['compiler'], candidate['inherited_manifest']]:
        check(sha(ROOT / fact['path']) == fact['SHA256'] and Path(ROOT / fact['path']).stat().st_size == fact['bytes'], 'build_bytes', fact['path'])
    check(environment['PATH_prefix'] == ['D:/msys64/ucrt64/bin', 'D:/gurobi1302/win64/bin'] and environment['affinity_mask'] == 4, 'common_identity', 'Common DLL search path and affinity policy')
    for role, p in roles.items():
        check(sha(ROOT / p['input_path']) == p['input_sha256'] == inherited_roles[role]['input_sha256'], 'inputs', 'Inherited physical bytes', role=role)
        for key in ['lambda', 'T_seconds', 'pickup_seconds', 'drop_seconds', 'Q_vector', 'normalized_base_key', 'normalized_full_key']:
            check(p[key] == inherited_roles[role][key], 'inputs', key, role=role)
        for tag, multiplier in [('base', 1.), ('half', .5), ('double', 2.)]:
            value = p['lambda'] * multiplier
            check(float(p[tag + '_lambda_decimal17']) == value and p[tag + '_lambda_binary64'] == value.hex(), 'inputs', 'Binary64 lambda/multiplier', role=role, tag=tag)
        ref = p['compact_reference']
        check(sha(ref['local_metadata']['path']) == ref['local_metadata']['SHA256'] and read(ref['local_metadata']['path']) == ref['metadata'], 'compact_reference', 'Actual inherited compact metadata bytes', role=role)

    facts = []
    totals = collections.Counter()
    all_log_bindings = []
    all_start_bindings = []
    all_h_bindings = []
    last_ended = 0
    identity_instances = collections.defaultdict(set)
    native_clock_offsets = []
    for pos in matrix['positions']:
        n, arm, role, seed = pos['position'], pos['arm'], pos['role'], pos['Native_Seed']
        p, row = roles[role], by_pos[n]
        d = Path(pos['directory'])
        inv, completion = read(d / 'invocation.json'), read(d / 'completion.json')
        raw = result(d / 'result.json')
        a = read(REVIEW / f'complete_audit_{n:02}.json')
        check(d.parent == OUT / 'complete_raw' and d.name == f'{n:02}_{role}_S{seed}_{arm}', 'own_process', 'Own registered output directory', position=n)
        check(row['position'] == n and row['role'] == role and row['arm'] == arm and row['Native_Seed'] == seed and row['run_id'] == d.name and row['input_SHA256'] == p['input_sha256'] and row['PE_SHA256'] == PE_SHA and row['DLL_SHA256'] == DLL_SHA and row['source_commit'] == MEASURED and row['cap_seconds'] == 600, 'endpoint_row', 'Complete row retains actual own identity', position=n)
        check(inv['argv'] == pos['argv'] and inv['measured_core_source'] == MEASURED and inv['H_free_reuse'] is False, 'own_process', 'Actual invocation and no free H', position=n)
        check(inv['PE'] == candidate['PE'] and inv['DLL'] == candidate['DLL'] and inv['deadline_seconds'] == 602, 'common_identity', 'Actual invocation binary/library and outer safety boundary', position=n)
        t = argv_tokens(inv['argv'])
        exact = {'--lambda': p['base_lambda_decimal17'], '--T': str(p['T_seconds']), '--pickup-time': '60', '--drop-time': '60',
                 '--threads': '1', '--mip-threads': '1', '--gurobi-seed': str(seed), '--gurobi-presolve': '-1',
                 '--time-limit': '594', '--process-wall-time-limit': '600', '--process-shutdown-margin': '6',
                 '--round166-breakpoint': 'off', '--round169-primal-mode': MODE[arm],
                 '--algorithm-preset': 'custom' if arm == 'P' else 'research-round83-vds-equal-net-exchange',
                 '--method': 'gurobi' if arm == 'P' else 'gcap-frontier', '--round127-mode': 'p' if arm == 'P' else 'ms2'}
        for key, value in exact.items():
            check(t.get(key) == value, 'argv', key, position=n)
        check(Path(t['--input']) == ROOT / p['input_path'], 'inputs', 'Actual original input argument', position=n)
        for key in ['--out', '--log', '--process-phase-ledger', '--external-gini-artifact-dir', '--primal-heuristic-generation-log', '--progress-log', '--native-evidence-dir', '--export-incumbent']:
            check(Path(t[key]).is_relative_to(d), 'own_process', 'Own output/evidence path', position=n, key=key)
        check(not any(re.search('(?:import|resume|warm|start|cutoff|known)', key) for key in t), 'own_process', 'No external fleet/tree/Start/cutoff input flags', position=n)
        check('--round169-h-panel' not in t and '--round112-ens-start-compact' not in t, 'own_process', 'No extra screen or ENS Start', position=n)
        check(completion['rc'] == 0 and not completion['affinity'].get('wrapper_killed') and completion['affinity'] == {'mask': 4, 'set_success': True}, 'completion', 'Normal return on fixed CPU affinity', position=n)
        check(completion == by_status[n]['receipt'] == a['completion'], 'completion', 'Actual receipts equal both readbacks', position=n)
        check(near(completion['ended_epoch'] - completion['started_epoch'], completion['process_outer_seconds'], .003), 'clocks', 'Epoch/performance outer process clocks agree', position=n)
        check(completion['started_epoch'] >= last_ended and completion['process_outer_seconds'] < 602, 'clocks', 'Serial process clocks within safety boundary', position=n)
        last_ended = completion['ended_epoch']
        check(sha(d / 'result.json') == completion['result']['SHA256'] and (d / 'result.json').stat().st_size == completion['result']['bytes'], 'raw_bindings', 'Actual result bytes', position=n)
        check(raw['process_return_code'] == 0 and raw['overall_deadline_started_at_process_entry'] is True and raw['nominal_process_wall_budget_seconds'] == 600 and raw['process_shutdown_margin_seconds'] == 6 and raw['process_wall_time_comparable'] is True, 'clocks', 'One cap includes complete C++ process', position=n)
        check(raw['external_incumbent_used'] is False and raw['resumed_from_state'] is False and raw['no_archive_scanning'] is True, 'own_process', 'No archived or resumed state readback', position=n)
        check(raw['gurobi_seed_requested'] == raw['gurobi_seed_effective'] == seed and raw['gurobi_seed_set_return_code'] == raw['gurobi_seed_get_return_code'] == 0, 'settings', 'Actual requested/effective Native Seed', position=n)
        identity_instances[role].add(raw['instance_hash'])
        phase = csvrows(d / 'phases.csv')
        phase_times = [float(x['process_seconds']) for x in phase]
        check(phase_times == sorted(phase_times) and phase[0]['event'] == 'process_entry' and phase_times[0] == 0 and phase[-1]['event'] == 'process_exit', 'clocks', 'Monotone process-entry phase ledger', position=n)
        check(phase_times[-1] <= completion['process_outer_seconds'] + .005, 'clocks', 'C++ exit nested in outer process', position=n)
        for event in phase:
            seconds = float(event['process_seconds'])
            check(abs(seconds + float(event['nominal_deadline_remaining_seconds']) - 600) < .005 and abs(seconds + float(event['work_deadline_remaining_seconds']) - 594) < .005, 'clocks', 'Shared absolute deadline never resets', position=n, event=event['event'])
        events = []
        commits = {}
        for event_file in (d / 'journal').glob('event_*.json'):
            data = event_file.read_bytes()
            event = json.loads(data)
            commit = event_file.with_suffix('.commit').read_text().split()
            check(len(commit) == 5 and commit[0] == 'NEJ1' and int(commit[1]) == event['sequence'] and int(commit[3]) == len(data) and commit[4] == hashlib.sha256(data).hexdigest(), 'journal', 'Actual commit bytes/hash/sequence', position=n, event=event['sequence'])
            commits[event['sequence']] = float(commit[2])
            events.append(event)
        events.sort(key=lambda x: x['sequence'])
        check([e['sequence'] for e in events] == list(range(1, len(events) + 1)), 'journal', 'No missing or duplicate journal sequence', position=n)
        check(list(commits[k] for k in sorted(commits)) == sorted(commits.values()), 'journal', 'Monotone journal process clock', position=n)
        identity = events[0]
        check(identity['kind'] == 'identity' and identity['input_sha256'] == p['input_sha256'] and identity['lambda'] == p['lambda'] and identity['T'] == p['T_seconds'] and identity['pickup_seconds'] == identity['drop_seconds'] == 60, 'journal', 'Actual original-problem identity', position=n)
        calls = [e for e in events if e['kind'] == 'call']
        returned = {e['call']: e for e in events if e['kind'] == 'returned'}
        quality = {e['call']: e for e in events if e['kind'] == 'native_quality'}
        check(len(calls) == len(returned) == len(quality) == row['actual_Optimize'] == a['actual_Optimize'], 'Optimize', 'Every actual call returned and has native-quality readback', position=n)
        check(set(returned) == set(quality) == {e['call'] for e in calls} and all(e['return_code'] == 0 for e in returned.values()), 'Optimize', 'No unreturned/failed optimizer call', position=n)
        ledger = csvrows(d / 'external/paper_optimize_ledger.csv') if arm != 'P' else []
        ordered_calls = sorted(calls, key=lambda x: x['call'])
        check(arm == 'P' or len(ledger) == len(calls), 'Optimize', 'Native ledger has exactly actual calls', position=n)
        limits = []
        root_bounds = [0.]
        for j, call in enumerate(ordered_calls):
            settings = call['settings']
            expected_settings = {'Threads': 1, 'Seed': seed, 'Presolve': -1, 'MIPFocus': 0, 'Cuts': -1, 'MIPGap': 0, 'MIPGapAbs': 0, 'FeasibilityTol': 1e-6, 'IntFeasTol': 1e-5, 'OptimalityTol': 1e-6}
            check(settings['read_return_code'] == 0 and settings['qualification_reason'] == '' and settings['expected'] == expected_settings and all(settings[k] == v for k, v in expected_settings.items()), 'settings', 'Every Optimize actual readback agrees with fixed values', position=n, call=call['call'])
            check(call['native_preconditions'] == 1 and call['precondition_reason'] == '', 'Optimize', 'Qualified call preconditions', position=n, call=call['call'])
            model_path, log_path = Path(call['model_path']), Path(call['native_log_path'])
            check(model_path.is_relative_to(d) and log_path.is_relative_to(d) and sha(model_path) == call['model_sha256'], 'own_process', 'Actual own model/log bindings', position=n, call=call['call'])
            native = log_path.read_text(encoding='utf-8')
            log_limits = re.findall(r'(?:Set parameter TimeLimit to value |^TimeLimit\s+)([0-9.eE+-]+)', native, re.M)
            effective_limit = float(log_limits[-1])
            limits.append(effective_limit)
            check(0 < effective_limit <= 594 and native.count('Optimize a model with') == 1 and 'using up to 1 threads' in native and re.search(r'^Seed\s+' + str(seed) + r'\s*$', native, re.M), 'settings', 'Actual call log Seed/Threads/time-limit', position=n, call=call['call'])
            check(re.search(r'^MIPGap\s+0\s*$', native, re.M) and re.search(r'^MIPGapAbs\s+0\s*$', native, re.M), 'settings', 'Native zero gaps', position=n, call=call['call'])
            offset = effective_limit + commits[call['sequence']] - 594
            native_clock_offsets.append(offset)
            check(abs(offset) < .25, 'clocks', 'Native limit is remaining process time, with bounded setup/commit delay', position=n, call=call['call'], seconds=offset)
            q = quality[call['call']]
            check(q['optimize_return_code'] == q['native_status_read_return_code'] == q['solution_count_read_return_code'] == 0, 'native_quality', 'Actual native readback success', position=n, call=call['call'])
            for key, tol in [('ConstrVio', 1e-6), ('BoundVio', 1e-6), ('IntVio', 1e-5)]:
                check(q[key] is None or q[key] <= tol, 'native_quality', 'Reported residual tolerance', position=n, call=call['call'], attribute=key)
            solve_kind = 'MIP' if arm == 'P' else ('LP' if ledger[j]['solve_kind'] == 'LP' else 'MIP')
            if arm != 'P':
                before_start = float(ledger[j]['global_deadline_remaining_at_launch'])
                check(ledger[j]['solve_kind'] in ['LP', 'MIP', 'CHILD_BOUND_TARGET_MIP'], 'Optimize', 'Recognized actual LP/MIP phase', position=n, call=call['call'])
                check(ledger[j]['model_sha256'] == call['model_sha256'] and Path(ledger[j]['native_log']) == log_path and -.000001 <= before_start - effective_limit <= .05, 'Optimize', 'Native ledger/model binding and shared remaining budget reduced by Start/setup work', position=n, call=call['call'], before_Start=before_start, actual_request=effective_limit)
                if solve_kind == 'LP':
                    check(near(before_start, effective_limit, 1e-6), 'Optimize', 'LP actual remaining request', position=n, call=call['call'])
                else:
                    start_meta = read(Path(str(log_path) + '.round68.start.json'))
                    check(near(start_meta['native_deadline_remaining_at_optimize'], effective_limit, 1e-6), 'Optimize', 'Actual post-Start-mapping Native request equals linked log', position=n, call=call['call'])
            if solve_kind == 'MIP' and call['lower_g'] == 0 and near(call['upper_g'], row['initial_U'] if arm != 'P' else call['gmax']) and q['ObjBoundC'] is not None:
                root_bounds.append(q['ObjBoundC'])
            all_log_bindings.append(bind(log_path))
        check(limits == sorted(limits, reverse=True), 'clocks', 'Remaining Native requests decrease across actual calls', position=n)
        check(near(max(root_bounds), row['L']), 'lower_bound_scope', 'Endpoint lower matches qualified full-root native bound, never speculative-child max', position=n, independently_read=max(root_bounds), reported=row['L'])
        globals_available = [e['global_bound'] for e in events if e['kind'] == 'bound' and e.get('global_available') and e['global_bound'] is not None]
        check(globals_available and near(max(globals_available), row['L']), 'lower_bound_scope', 'Qualified global journal endpoint equals row L', position=n)

        path_metas = []
        start_checks = a['Start_checks']
        if arm == 'P':
            params = read(d / 'round127_parameters.json')
            check(params == {'MIPFocus': 0, 'Cuts': -1, 'NumStart_before_optimize': 0, 'loaded_after_presets': True, 'authoritative_model_environment': True}, 'P_cold', 'Actual zero user starts after presets', position=n)
            check(raw['algorithm_preset'] == 'custom' and t.get('--plain-baseline') is True and raw['gurobi_hga_start_requested'] is False and not (d / 'primal').exists() and not (d / 'hga.csv').exists() and not start_checks and len(calls) == 1, 'P_cold', 'No custom H or Start production/submission', position=n)
            native = (d / 'native.log').read_text()
            check('Loaded user MIP start' not in native and not list(d.rglob('*start*.json')), 'P_cold', 'Actual cold log and absent user Start records', position=n)
            for key in ['--round24-executable-sha256', '--round24-manifest-executable-sha256']:
                check(t[key] == PE_SHA, 'P_cold', 'Actual common PE identification', position=n, key=key)
            ref = p['compact_reference']['metadata']
            check(sha(d / 'compact.lp') == ref['canonical_sha256'] == calls[0]['model_sha256'], 'P_compact', 'Actual P LP byte identity to original compact reference', position=n)
            for key, field in [('columns', 'gurobi_num_vars'), ('rows', 'gurobi_num_constrs'), ('fingerprint', 'gurobi_model_fingerprint')]:
                check(raw[field] == ref[key], 'P_compact', 'Actual original model dimensions/fingerprint', position=n, key=key)
            check(calls[0]['full_original'] == 1 and calls[0]['model_scope'] == 'complete_original_compact_milp' and calls[0]['cutoff'] == 0, 'P_compact', 'Complete original P domain without external cutoff', position=n)
            check(a['models'][0]['AP']['one_hot_AP_contract_applicable'] is False and a['models'][0]['AP']['full_matrix_byte_identity_verified'] is True, 'P_compact', 'Correct original compact contract after reader-only correction', position=n)
            lp_count, mip_count = 0, 1
            native_seconds, work, nodes = raw['gurobi_runtime'], raw['gurobi_work'], raw['gurobi_node_count']
        else:
            order = ['base'] + ([] if arm == 'B' else [f'{arm}_s1', f'{arm}_s2'])
            check(sorted(q.name for q in (d / 'primal').iterdir() if q.is_dir()) == sorted(order), 'paid_H', 'Exactly required own complete paths', position=n)
            selection = read(d / 'primal/selection.json')
            previous_elapsed = 0
            for j, name in enumerate(order):
                folder = d / 'primal' / name
                meta = read(folder / 'path.json')
                path_metas.append(meta)
                expected_lambda = p['lambda'] * ([1, .5, 2][j] if arm == 'C' else 1)
                check(meta['name'] == name and meta['effective_seed'] == 20260626 + j and meta['search_lambda'] == expected_lambda and meta['evaluation_lambda'] == p['lambda'] and meta['preset'] == 'research-round83-vds-equal-net-exchange', 'paid_H', 'Actual complete-H seed and search/original objective', position=n, path=name)
                check(all(meta[k] is True for k in ['valid', 'complete', 'joint_complete', 'descent_complete', 'closure_complete']) and meta['descent_seeds_completed'] == 25, 'paid_H', 'Full H actually completed 25 decoded orders and physical closure', position=n, path=name)
                descent = csvrows((d if name == 'base' else folder) / 'hga.csv.descent.csv')
                last_descent = {int(v['seed']): v for v in descent}
                check(set(last_descent) == set(range(1, 26)) and all(v['exhausted'] == '1' and v['interrupted'] == '0' for v in last_descent.values()) and all(v['interrupted'] == '0' for v in descent), 'paid_H', 'Actual descent transcript exhausts all 25 seeds without interruption', position=n, path=name)
                check(meta['input_SHA256'] == p['input_sha256'] and sha(folder / 'fleet.json') == meta['fleet_SHA256'] and hashlib.sha256((folder / 'initial_random_orders.txt').read_bytes().replace(b'\r\n', b'\n')).hexdigest() == meta['initial_random_orders_SHA256'], 'paid_H', 'Own physical fleet and random orders actual bytes', position=n, path=name)
                check(near(meta['G'] + p['lambda'] * meta['P'], meta['F']) and near(meta['G'] + expected_lambda * meta['P'], meta['search_F']), 'paid_H', 'Original and search objectives correctly separate', position=n, path=name)
                previous = next(x for x in old_h if x['role'] == role and x['name'] == name)
                for key in ['effective_seed', 'search_lambda', 'evaluation_lambda', 'G', 'P', 'F', 'physical_R169_SHA256', 'fleet_SHA256', 'initial_random_orders_SHA256', 'decoded_checks', 'physical_work_counter_sum']:
                    check(meta[key] == previous[key], 'fixed_H', 'Fixed recipe reproduces inherited deterministic identity without input reuse', position=n, path=name, key=key)
                check(meta['H_seconds'] > 0 and meta['whole_run_elapsed_seconds'] >= previous_elapsed + meta['H_seconds'] - .005, 'paid_H', 'Each independent H is paid on monotonically increasing common process clock', position=n, path=name)
                previous_elapsed = meta['whole_run_elapsed_seconds']
                check(next(x for x in hrows if x['position'] == n and x['name'] == name) == {'position': n, 'role': role, 'arm': arm, 'Native_Seed': seed, **meta}, 'H_table', 'H table equals actual own path metadata', position=n, path=name)
                all_h_bindings.append(bind(folder / 'path.json'))
            selected = 0
            for j in range(1, len(path_metas)):
                if path_metas[j]['F'] < path_metas[selected]['F'] - 1e-10:
                    selected = j
            check(selection['calls'] == len(order) and selection['mode'] == MODE[arm] and selection['h_panel'] is False and selection['selected'] == order[selected] and selection['greedy_restored'] is True and selection['guard_exception_early_return_pass'] is True, 'paid_H', 'Correct deterministic original-objective own-pool selection', position=n)
            check(selection['total_initialization_seconds'] >= sum(m['H_seconds'] for m in path_metas) and selection['total_initialization_seconds'] < raw['process_elapsed_at_exact_phase_start_seconds'] and previous_elapsed <= raw['process_elapsed_at_exact_phase_start_seconds'], 'clocks', 'All H/selection costs included before exact stage', position=n)
            check(selection['necessary_H_complete'] is False and a['full_paid_H']['complete_arm_initialization'] is True, 'H_semantics', 'Panel-only diagnostic correctly separated from complete one/three-path initialization', position=n)
            check(near(raw['initial_heuristic_UB'], path_metas[selected]['F']) and row['selected_H'] == order[selected], 'Start', 'Selected own original-objective UB', position=n)
            check(row['initialization_seconds'] == selection['total_initialization_seconds'] and row['decoded_checks'] == sum(v['decoded_checks'] for v in path_metas) and row['physical_work_counter_sum'] == sum(v['physical_work_counter_sum'] for v in path_metas), 'cost_row', 'Actual complete H initialization/work counters', position=n)
            check(row['all_model_build_seconds'] == raw['external_gini_tree_model_build_seconds'] and near(row['root_model_construction_seconds'], next(float(v['process_seconds']) for v in phase if v['event'] == 'root_canonical_model_construction_complete') - next(float(v['process_seconds']) for v in phase if v['event'] == 'root_canonical_model_construction_start')), 'cost_row', 'Actual C++ model-build timers retained', position=n)
            for entry in start_checks:
                sp = ROOT / entry['start_path']
                sm = read(sp)
                vp = sp.with_suffix('.values.csv')
                vectors = csvrows(vp)
                check(sp.is_relative_to(d) and sha(sp) == entry['start_sha256'] and sha(vp) == entry['vector_sha256'], 'Start', 'Actual own Start and vector bytes', position=n)
                check(sm['model_sha256'] == entry['model_sha256'] and sm['mapping_complete'] and sm['rows_valid'] and sm['objective_valid'] and sm['submitted'] and sm['readback_valid'], 'Start', 'Actual complete valid mapping/submission/readback', position=n)
                check(near(sm['objective'], path_metas[selected]['F']) and sm['status'] == 'accepted_by_native_log' and sm['maximum_row_violation'] <= 1e-6, 'Start', 'Native accepted selected own H objective', position=n)
                check(len(vectors) == entry['columns'] and len({v['variable'] for v in vectors}) == len(vectors) and all(near(float(v['value']), float(v['readback'])) for v in vectors), 'Start', 'Full unique native column readback', position=n)
                all_start_bindings.extend([bind(sp), bind(vp)])
            check(len(start_checks) == row['MIP'], 'Start', 'Every tailored MIP has an actual checked own Start', position=n)
            lp_count = sum(v['solve_kind'] == 'LP' for v in ledger)
            mip_count = sum(v['solve_kind'].endswith('MIP') for v in ledger)
            native_seconds = sum(float(v['solver_runtime']) for v in ledger)
            work = sum(float(v['work']) for v in ledger)
            nodes = sum(float(v['nodes']) for v in ledger)
            leaves = csvrows(d / 'external/paper_leaf_ledger.csv')
            check(len(leaves) == 1 and leaves[0]['leaf_id'] == 'L0' and float(leaves[0]['gamma_L']) == 0 and near(float(leaves[0]['gamma_U']), row['initial_U']) and near(float(leaves[0]['lower_bound']), row['L']), 'lower_bound_scope', 'Actual final leaf ledger covers whole improving domain', position=n)
            check(a['qualified_cover']['complete_coverage'] is True and near(a['qualified_cover']['L'], row['L']) and all(x['future_evidence_used'] is False for x in a['chronological_cover']), 'lower_bound_scope', 'Existing qualified cover is linked to actual chronology', position=n)
        for key, val in [('H_calls', len(path_metas)), ('H_seconds', sum(m['H_seconds'] for m in path_metas)), ('LP', lp_count), ('MIP', mip_count), ('Native_seconds', native_seconds), ('Work', work), ('nodes', nodes), ('process_outer_seconds', completion['process_outer_seconds'])]:
            check(same(row[key], val), 'cost_row', 'Independent actual raw cost matches row', position=n, key=key, actual=val, reported=row[key])
            totals[key] += val
        totals['actual_Optimize'] += len(calls)
        cert = raw['strict_certified_original_problem']
        check(a['passed'] is True and a['Optimize_run_by_reviewer'] == 0 and a['raw_bytes_unchanged'] is True and row['certificate'] == a['certificate'] == cert, 'qualification', 'Actual reader success without optimization; certificate agrees', position=n)
        for key in ['U', 'L', 'certificate', 'certificate_basis', 'actual_Optimize', 'LP', 'MIP', 'Native_seconds']:
            check(same(row[key], a[key]), 'endpoint_row', 'Row equals actual independently qualified readback', position=n, key=key)
        check(near(row['U'], raw['upper_bound']) and near(row['L'], raw['lower_bound']) and near(row['U'], row['G'] + p['lambda'] * row['P']) and near(row['signed_absolute_gap'], row['U'] - row['L']) and near(row['signed_relative_gap'], (row['U'] - row['L']) / max(abs(row['U']), 1e-12)), 'endpoint_row', 'Original physical objective and exact gap arithmetic', position=n)
        check(row['state'] == ('CERT' if cert else 'OPEN') and row['certification_censored'] is (not cert) and (row['T_cert_process'] == completion['process_outer_seconds'] if cert else row['T_cert_process'] is None) and row['exact_first_hit_global_seconds'] is None, 'cert_clock', 'CERT outer endpoint; OPEN censored; exact first-hit unknown', position=n)
        successful_cost = [v for v in audit_costs if v['positions'] == [n] and v['rc'] == 0][-1]
        check(row['audit_seconds'] == successful_cost['audit_process_outer_seconds'] and near(row['T_total_with_independent_audit'], row['process_outer_seconds'] + row['audit_seconds']) and row['audit_function_seconds'] == a['audit_seconds'], 'audit_cost', 'Independent audit nested and separately billed', position=n)
        for key in ['audit_seconds', 'audit_function_seconds', 'initialization_seconds', 'process_residual_after_Native_and_H_seconds', 'original_H_reverification_seconds']:
            totals[key] += row[key]
        check(near(row['process_residual_after_Native_and_H_seconds'], row['process_outer_seconds'] - native_seconds - row['H_seconds']), 'cost_row', 'Residual is actual remaining process, not a pure verifier timer', position=n)
        check(sha(d / 'fleet.json') == row['raw_fleet_SHA256'] and a['actual_invocation']['SHA256'] == sha(d / 'invocation.json'), 'raw_bindings', 'Actual final fleet/invocation bytes', position=n)
        facts.append({'position': n, 'role': role, 'arm': arm, 'Native_Seed': seed, 'H_calls': len(path_metas), 'actual_Optimize': len(calls), 'LP': lp_count, 'MIP': mip_count,
                      'state': row['state'], 'U': row['U'], 'L': row['L'], 'T_cert_process': row['T_cert_process'], 'process_outer_seconds': completion['process_outer_seconds'],
                      'started_epoch': completion['started_epoch'], 'ended_epoch': completion['ended_epoch'], 'journal_events': len(events), 'Native_seconds': native_seconds,
                      'H_seconds': row['H_seconds'], 'Work': work, 'nodes': nodes, 'audit_seconds': row['audit_seconds'], 'Start_count': len(start_checks)})
    check(all(len(v) == 1 for v in identity_instances.values()), 'inputs', 'Physical parser identity common across arms/seeds of each original input')
    check(totals['H_calls'] == 41 and totals['actual_Optimize'] == 84 and totals['LP'] == 57 and totals['MIP'] == 27, 'totals', '41 complete paid H, 84 Optimize=57 LP+27 MIP')
    for key, value in totals.items():
        check(near(costs[key], value, 1e-7), 'totals', 'Cost report agrees with independently read process/journal/H/Native endpoints', key=key, actual=value, reported=costs[key])
    check(near(status['process_outer_seconds'], totals['process_outer_seconds']) and status['positions_finished'] == 22 and sum(x['state'] == 'CERT' for x in facts) == 4, 'totals', 'All 22 receipts, four true certificates and 18 OPEN')
    check(costs['qualification_H'] == costs['qualification_Optimize'] == 0 and costs['Native_H_model_checks_nested_not_added_to_process'] is True and costs['P_model_build_separate_timer'] is None, 'totals', 'No extra qualification and nested timers not double counted')
    check(len(audit_attempts) == 23 and sum(v['PASS'] for v in audit_attempts) == 22 and [v['position'] for v in audit_attempts if not v['PASS']] == [4] and all(v['Optimize'] == 0 for v in audit_attempts), 'audit_cost', 'Failed P reader and all successful attempts retained without optimizer retry')
    check(near(costs['all_model_build_reported_tailored_seconds'], sum(v['all_model_build_seconds'] or 0 for v in rows)), 'totals', 'All tailored C++ model build timers retained; P remains missing')
    check(near(costs['postreturn_audit_all_attempt_seconds'], sum(v['audit_inclusive_seconds'] for v in audit_attempts)) and near(costs['instrumented_audit_process_outer_seconds'], sum(v['audit_process_outer_seconds'] for v in audit_costs)), 'audit_cost', 'All inner and outer audit attempt costs retained')
    failure = read(REVIEW / 'complete_audit_04_failure.json')
    check(failure['Optimize'] == 0 and 'AssertionError' in failure['error'], 'audit_cost', 'Original reader failure retained')

    index = {(x['role'], x['Native_Seed'], x['arm']): x for x in rows}
    expected_pairs = {'CB': [('C', 'B', x['role'], x['Native_Seed']) for x in rows if x['arm'] == 'C'],
                      'CM': [('C', 'M', x['role'], 1) for x in rows if x['arm'] == 'M'],
                      'BP': [('B', 'P', x['role'], 1) for x in rows if x['arm'] == 'P'],
                      'CP': [('C', 'P', x['role'], 1) for x in rows if x['arm'] == 'P']}
    for group, pairs in expected_pairs.items():
        document = read(OUT / f'comparison_{group}.json')
        cr = document['rows']
        check(len(cr) == len(pairs) and document['no_cross_arm_endpoint_splicing'] is True, 'comparisons', 'Exactly prescribed comparison group', group_name=group)
        for pairrow, (subject_arm, reference_arm, role, seed) in zip(cr, pairs):
            subject, reference = index[(role, seed, subject_arm)], index[(role, seed, reference_arm)]
            check(pairrow['subject_run'] == subject['run_id'] and pairrow['reference_run'] == reference['run_id'] and pairrow['role'] == role and pairrow['Native_Seed'] == seed, 'comparisons', 'Actual correct arms matched without substitutions', group_name=group, role=role)
            for which, source in [('subject', subject), ('reference', reference)]:
                check(all(same(v, source[k]) for k, v in pairrow[which].items()), 'comparisons', 'Own endpoint retained intact', group_name=group, role=role, which=which)
            delta = max(1e-6, .001 * max(abs(reference['U']), 1e-12))
            check(pairrow['delta'] == delta, 'comparisons', 'Frozen materiality scale and correct reference', group_name=group, role=role)
            for metric in ['U', 'L', 'absolute_gap', 'relative_gap', 'process_outer_seconds', 'H_seconds', 'Native_seconds', 'Work', 'nodes']:
                difference = subject[metric] - reference[metric]
                percent = 100 * difference / abs(reference[metric]) if abs(reference[metric]) > 1e-12 else None
                check(same(pairrow[metric + '_difference'], difference) and same(pairrow[metric + '_change_percent'], percent), 'comparisons', 'Independent pair arithmetic', group_name=group, role=role, metric=metric)
            ratio = subject['T_cert_process'] / reference['T_cert_process'] if subject['certificate'] and reference['certificate'] else None
            check(same(pairrow['T_cert_ratio'], ratio), 'comparisons', 'No time ratio for OPEN pair', group_name=group, role=role)
            for metric, lower_better in [('U', True), ('L', False), ('absolute_gap', True)]:
                difference = subject[metric] - reference[metric]
                improvement = difference < -delta if lower_better else difference > delta
                regression = difference > delta if lower_better else difference < -delta
                check(pairrow[metric + '_material_improvement'] is improvement and pairrow[metric + '_material_regression'] is regression, 'comparisons', 'Correct material direction using fixed common scale', group_name=group, role=role, metric=metric)
            state_comparison = 'both_CERT' if subject['certificate'] and reference['certificate'] else 'subject_only_CERT' if subject['certificate'] else 'reference_only_CERT' if reference['certificate'] else 'both_OPEN'
            check(pairrow['certificate_comparison'] == state_comparison and pairrow['no_composite_win_score'] is True, 'comparisons', 'Actual certificate state and separate indicators', group_name=group, role=role)
        table_twins(cr, OUT / f'comparison_{group}.csv')
    table_twins(rows, OUT / 'complete_arms.csv')
    table_twins(hrows, OUT / 'h_path_results.csv')

    rec = read(OUT / 'CSV_reconciliation.json')
    inc = OUT / 'GI_TBC_R170_B_increment_28col.csv'
    rawcsv = inc.read_bytes()
    table = list(csv.reader(io.StringIO(rawcsv.decode('utf-8-sig'))))
    check(rawcsv.startswith(b'\xef\xbb\xbf') and len(table) == 9 and all(len(v) == 28 for v in table) and table[0][-2:] == ['实验数据来源', '实例元数据来源'], 'CSV', 'Eight records, original 28-column schema, UTF-8 BOM')
    old_header = next(csv.reader(io.StringIO((ROOT / 'results/unified_exact_round164/reports/GI_TBC_vs_P_GRB_All_Tested_Instances.csv').read_bytes().decode('gb18030'))))
    check(table[0][:-2] == old_header[:-2] and len(rec['increment_mapping']) == 8 and len({(v[0], v[10], v[12], v[13]) for v in table[1:]}) == 8, 'CSV', 'Original 26 data headers, exact mapping count and distinct new run keys')
    check(rec['increment']['SHA256'] == sha(inc) and rec['qualified_new_B_records'] == 8 and rec['new_strict_P_pairs'] == 3 and rec['new_physical_inputs'] == 0 and rec['actual_master_rows_appended'] == 0 and rec['actual_master'] is None and rec['actual_records'] is None, 'CSV', 'Actual mergeable increment only; no invented master')
    check(rec['authoritative_118_available'] is False and rec['package_received'] is False and rec['expected_SHA256'] == '5e3303adfba0092c465b8dab3232e1ced7d0e85d8d21aa3e8398ed0d3e5880e3', 'CSV', 'Missing authoritative base disclosed with expected identity')
    for old in rec['found']:
        check(sha(ROOT / old['path']) == old['SHA256'] and old['SHA256'] != rec['expected_SHA256'], 'CSV', 'Older actual copies preserved and never relabelled 118', path=old['path'])
    paired = 0
    data_commit = read(OUT / 'data_commit.json')['commit']
    csv_qa = read(OUT / 'CSV_QA.json')
    check(csv_qa['PASS'] is True and csv_qa['Optimize'] == 0 and csv_qa['source_CSV_SHA256'] == sha(inc), 'CSV', 'Read-only Artifact Tool QA binds final actual bytes')
    for values, mapping in zip(table[1:], rec['increment_mapping']):
        b = by_pos[mapping['position']]
        plain = index.get((b['role'], b['Native_Seed'], 'P'))
        check(b['arm'] == 'B' and values[0] == b['role'] and int(values[10]) == b['Native_Seed'] and int(values[12]) == 170 and int(values[13]) == 600 and float(values[8]) == b['lambda_value'], 'CSV', 'Actual B-only physical/Seed/cap/objective identity', row=mapping['increment_row'])
        check(values[14] == ('已收敛' if b['certificate'] else '未收敛') and (near(float(values[15]), b['T_cert_process']) if b['certificate'] else values[15] == '' and near(float(values[16]), 100 * b['relative_gap'])) and near(float(values[17]), b['L']) and near(float(values[18]), b['U']), 'CSV', 'B CERT process time and OPEN percentage gap', row=mapping['increment_row'])
        check(mapping['run_id'] == b['run_id'] and mapping['T_cert_process'] == b['T_cert_process'] and mapping['audit_seconds'] == b['audit_seconds'] and mapping['T_total_with_independent_audit'] == b['T_total_with_independent_audit'], 'CSV', 'Per-row exact independent audit/certificate clocks', row=mapping['increment_row'])
        if plain:
            paired += 1
            check(mapping['P_run_id'] == plain['run_id'] and values[19] == '未收敛' and values[20] == '' and near(float(values[21]), 100 * plain['relative_gap']) and near(float(values[22]), plain['L']) and near(float(values[23]), plain['U']) and values[24] == '分指标比较', 'CSV', 'Actual same-budget Seed1 P endpoint on same B record', row=mapping['increment_row'])
        else:
            check(mapping['P_run_id'] is None and values[19:24] == ['无配对结果', '', '', '', ''] and values[24] == 'N/A' and 'N/A-P' in values[25], 'CSV', 'Five genuinely unpaired B records', row=mapping['increment_row'])
        check(b['run_id'] in values[25] and PE_SHA in values[25] and MEASURED in values[25] and values[27] == 'https://github.com/yifanXovo/TailoredExact/blob/8ae25cbcbb88caa283d345b1b143ff0da6e5c0eb/results/unified_exact_round163/input_manifest.json', 'CSV', 'Run/source/PE/fixed metadata provenance', row=mapping['increment_row'])
        check(values[26] == 'https://github.com/yifanXovo/TailoredExact/blob/' + data_commit + '/results/unified_exact_round170/complete_arms.json', 'CSV', 'Source link pinned to actual data commit', row=mapping['increment_row'])
    check(paired == 3 and 8 - paired == 5 and rec['candidate_C_rows_in_master'] == rec['candidate_M_rows_in_master'] == 0, 'CSV', 'Eight B increments, three new pairs, five N/A-P, no candidate substitution')

    gap = read(OUT / 'work_interruption.json')
    final_audit_end = max(x['start_epoch'] + x['audit_process_outer_seconds'] for x in audit_costs if 'start_epoch' in x)
    check(abs(gap['first_science_segment_end_epoch'] - final_audit_end) < .01 and gap['first_science_segment_end_epoch'] >= last_ended, 'science_clock', 'Recorded first segment ends after every process and final audit')
    check(near(gap['first_science_segment_seconds'], gap['first_science_segment_end_epoch'] - gap['science_start_epoch']) and near(gap['inactive_postcompletion_gap_seconds'], gap['resume_epoch'] - gap['first_science_segment_end_epoch']), 'science_clock', 'Exact first segment and inactive gap arithmetic')
    export_epoch = datetime.fromisoformat(costs['UTC']).timestamp()
    check(near(costs['science_gross_wall_seconds'], export_epoch - costs['science_start_epoch'], .02) and near(costs['science_elapsed_conservative_seconds'], costs['science_gross_wall_seconds']), 'science_clock', 'Gross wall time retained rather than rewritten as six hours')
    check(near(costs['inactive_postcompletion_gap_seconds'], gap['inactive_postcompletion_gap_seconds']) and near(costs['science_charged_seconds'], costs['science_gross_wall_seconds'] - gap['inactive_postcompletion_gap_seconds']) and costs['science_charged_seconds'] <= 21600, 'science_clock', 'Occupied scientific capacity is transparent subtraction of disclosed inactive gap')
    check(gap['gross_wall_clock_must_remain_reported'] is True and gap['no_solver_restarts'] is True, 'science_clock', 'No hidden postgap solver restart')
    for name in ['final_report.md']:
        text = (OUT / name).read_text(encoding='utf-8-sig')
        check('gross' in text.lower() and ('inactive' in text.lower() or 'interruption' in text.lower()), 'science_clock', 'Human-readable gross/inactive disclosure', file=name)

    protected = read(OUT / 'entry_state.json')['protected']
    for state in protected:
        for p in state['files']:
            check(sha(Path(state['root']) / p['path']) == p['SHA256'], 'protected_bytes', 'Recorded preexisting user/other-worktree dirty file preserved', path=str(Path(state['root']) / p['path']))

    archive_fact = {'status': 'PENDING', 'reason': 'Awaiting completed archive and exact member-map identity from parent.'}
    if final:
        archive_fact = verify_archive()
    important_files = [OUT / n for n in ['goal.md', 'matrix_frozen.json', 'candidate_manifest.json', 'environment_manifest.json', 'inputs_frozen.json', 'complete_status.json', 'complete_arms.json', 'h_path_results.json', 'comparison_CB.json', 'comparison_CM.json', 'comparison_BP.json', 'comparison_CP.json', 'cost_report.json', 'CSV_reconciliation.json', 'GI_TBC_R170_B_increment_28col.csv', 'work_interruption.json']]
    report = {
        'schema': 'round170-independent-execution-data-cost-review-v1',
        'UTC': datetime.now(timezone.utc).isoformat(),
        'reviewer_id': REVIEWER,
        'status': 'FAIL' if ERRORS else 'PASS' if final else 'PASS_PENDING_ARCHIVE',
        'scope': ['actual frozen 22-position order and serial clocks', 'actual common PE/DLL/source/input identities', 'every Optimize journal/commit/model/log/settings binding', 'all 41 complete paid-H paths and selected own Start/vector records', 'correct cold original compact P qualification', 'complete cost/attempt accounting and gross/occupied science clocks', 'eight B CSV increment rows and all four comparison groups', 'exact archive member bytes' if final else 'archive member bytes pending'],
        'Optimize_run_by_reviewer': 0, 'H_run_by_reviewer': 0, 'solver_API_calls': 0, 'model_construction_calls': 0,
        'review_clock_start_epoch': START, 'review_seconds': time.time() - START,
        'review_seconds_scope': 'Independent data reads/checking/authoring since first instrumented Python read; earlier read-only setup is inside parent gross/occupied closeout clock. Concurrent review wall is not added again to the parent elapsed science segments.',
        'check_process_seconds': time.perf_counter() - tick,
        'error_count': len(ERRORS), 'errors': ERRORS, 'checks_by_scope': dict(CHECKS),
        'findings': [
            {'severity': 'info', 'finding': '22 prescribed positions returned once normally, with 41 own paid complete H and 84 actual Optimize calls (57 LP, 27 MIP).'},
            {'severity': 'info', 'finding': 'Actual Native Seeds 1/2, single-thread settings and zero gaps match every actual call; all arms share measured PE/DLL and each role retains original input/clock.'},
            {'severity': 'info', 'finding': 'P has zero user starts and its byte-exact original compact reference. The retained position-4 failure is a reader AP-contract applicability error, followed by a successful reader-only retry; no optimizer rerun is present.'},
            {'severity': 'info', 'finding': 'Four C20 certificates use process outer endpoints only. Eighteen OPEN rows have null certificate time and unknown exact first hit; the 600s cap and observed ~594s endpoints are not convergence times.'},
            {'severity': 'limitation', 'finding': 'The byte-pinned 118-row authoritative package was absent in the bounded entry lookup. Only the qualified eight-row increment is delivered, with three new strict P pairs, five explicit N/A-P records, no candidate substitution, no master append and zero new physical inputs.'},
            {'severity': 'info', 'finding': 'Gross elapsed wall remains reported. Occupied work subtracts only the explicitly recorded postcompletion inactive interval; this is not a claim of gross wall delivery within six hours.'}
        ],
        'initial_review_resolution': {
            'initial_report_retained': 'review/execution_review_initial.json',
            'initial_checker_false_assertions': [
                'The first checker counted only literal MIP phase names; five actual CHILD_BOUND_TARGET_MIP phases must also be counted as MIP. Actual total is 27.',
                'The first checker equated the pre-Start ledger remaining budget with the slightly smaller actual post-mapping Optimize request. Actual Start JSON and log requests agree; the additional setup cost is paid.',
                'The first checker demanded duplicate gross/inactive prose in every engineering/reproduction note. The required disclosure is present in cost_report, work_interruption and final_report; the other notes make no contradictory six-hour gross-wall claim.'
            ],
            'production_changes_requested': [],
            'producer_or_optimizer_reruns_requested': 0,
            'only_reviewer_checker_corrected': True
        } if final else None,
        'actual_totals': dict(totals), 'per_position': facts,
        'native_requested_limit_plus_commit_clock_minus_594_range_seconds': [min(native_clock_offsets), max(native_clock_offsets)],
        'native_clock_note': 'TimeLimit is set just before serialized call-commit observation; small bounded setup/commit offsets do not reset the shared deadline. The actual process/phase deadlines are independently checked.',
        'science_clock_snapshot': {k: costs[k] for k in ['UTC', 'science_start_epoch', 'science_gross_wall_seconds', 'inactive_postcompletion_gap_seconds', 'science_charged_seconds', 'science_clock_scope']},
        'last_actual_process_end_epoch': last_ended, 'last_instrumented_reader_end_epoch': final_audit_end,
        'archive_verification': archive_fact,
        'bindings': [bind(p) for p in important_files],
        'actual_H_metadata_bindings': all_h_bindings,
        'actual_Start_and_vector_bindings': all_start_bindings,
        'actual_native_log_bindings': all_log_bindings,
        'checker': bind(Path(__file__)),
        'writes': ['review/execution_review_initial.json' if not final else 'review/execution_review_final.json'],
        'production_raw_CPP_CSV_Git_modified_by_reviewer': False,
    }
    target = REVIEW / ('execution_review_final.json' if final else 'execution_review_initial.json')
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'errors': ERRORS[:20], 'error_count': len(ERRORS), 'check_count': sum(CHECKS.values()), 'review_seconds': report['review_seconds'], 'check_process_seconds': report['check_process_seconds'], 'archive': archive_fact, 'output': str(target)}, ensure_ascii=False, indent=2))
    return report


def verify_archive():
    # Deliberately narrow: the final exact map is supplied by parent, not guessed.
    archive = OUT / 'artifacts/round170_new_raw.zip'
    candidates = [p for p in (OUT / 'artifacts').glob('*') if 'member' in p.name.lower()]
    candidates += [p for p in (OUT / 'evidence').glob('*') if 'member' in p.name.lower()] if (OUT / 'evidence').is_dir() else []
    check(archive.is_file() and archive.stat().st_size > 0 and len(candidates) == 1, 'archive', 'Completed archive and unique exact member map')
    if not archive.is_file() or not candidates:
        return {'status': 'FAIL', 'archive': str(archive), 'maps': [str(p) for p in candidates]}
    membermap_path = candidates[0]
    membermap_text = gzip.decompress(membermap_path.read_bytes()).decode('utf-8-sig')
    entries = list(csv.DictReader(io.StringIO(membermap_text)))
    members = {x['member']: x for x in entries}
    carrier = read(OUT / 'evidence_archives.json')
    check(carrier['carrier'] == bind(archive) and carrier['membermap'] == bind(membermap_path), 'archive', 'Carrier and member map actual bytes equal evidence archive record')
    check(carrier['new_only'] is True and carrier['historical_carriers_repacked'] is False and carrier['commercial_DLL_licenses_credentials_included'] is False, 'archive', 'Only this round raw is packaged')
    raw_files = {p.relative_to(OUT).as_posix(): p for p in (OUT / 'complete_raw').rglob('*') if p.is_file()}
    total_bytes = 0
    with zipfile.ZipFile(archive) as z:
        infos = [v for v in z.infolist() if not v.is_dir()]
        check(len(infos) == len({v.filename for v in infos}) == len(members), 'archive', 'No duplicate or missing member names')
        check({v.filename for v in infos} == set(members), 'archive', 'Exact actual ZIP member names agree with member map')
        check(set(raw_files) == set(members), 'archive', 'Exactly all actual raw member files covered, no runtime or historical payload')
        for v in infos:
            data = z.read(v)
            digest = hashlib.sha256(data).hexdigest()
            meta = members[v.filename]
            check(len(data) == int(meta['bytes']) == v.file_size and digest == meta['SHA256'], 'archive', 'Actual uncompressed ZIP member bytes match exact map', member=v.filename)
            if v.filename in raw_files:
                check(sha(raw_files[v.filename]) == digest and raw_files[v.filename].stat().st_size == len(data), 'archive', 'Archive member equals actual production raw file', member=v.filename)
            total_bytes += len(data)
    check(len(members) == carrier['members'] == 51718 and total_bytes == carrier['raw_uncompressed_bytes'] == 206513335, 'archive', 'Exact archive member count and uncompressed bytes')
    return {'status': 'FAIL' if any(e['group'] == 'archive' for e in ERRORS) else 'PASS', 'archive': bind(archive), 'member_map': bind(membermap_path), 'member_count': len(members), 'uncompressed_bytes': total_bytes, 'actual_raw_files_checked': len(raw_files)}


if __name__ == '__main__':
    run_review(final='--final' in sys.argv)
