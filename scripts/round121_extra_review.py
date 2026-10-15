"""Independent finite blocked-delivery review; no campaign imports or native work."""
from pathlib import Path
import ast
import collections
import copy
import csv
import ctypes
import datetime
import hashlib
import json
import math
import re
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round121'
REVIEW = OUT / 'review'
RAW_SHA = 'd4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8'
TABLE_SHA = 'd982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa'
PE_SHA = '5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
EXPECTED = [
    ('F2', 1, 1200, ['MB-D0', 'P-GRB', 'MB-D1', 'M-B']),
    ('Q30-C2-B', 0, 1800, ['P-GRB', 'MB-D1', 'M-B']),
    ('R98-C2', 1, 1800, ['M-B', 'P-GRB', 'MB-D1']),
    ('Q40-R2-S', 0, 3600, ['MB-D1', 'M-B', 'P-GRB']),
    ('Q50-C2-U', 0, 3600, ['M-B', 'P-GRB', 'MB-D1']),
]
F2_PAIRS = [('MB-D1', 'M-B'), ('MB-D1', 'P-GRB'), ('MB-D1', 'MB-D0'),
            ('MB-D0', 'M-B'), ('MB-D0', 'P-GRB'), ('M-B', 'P-GRB')]
OTHER_PAIRS = [('MB-D1', 'M-B'), ('MB-D1', 'P-GRB'), ('M-B', 'P-GRB')]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(path):
    return Path(path).read_text(encoding='utf-8-sig')


def parse_instance(path):
    lines = text(path).splitlines()
    header = re.fullmatch(r'(\d+)\s+(\d+)\s+(\[.*\])', lines[0])
    assert header
    values = {}
    for line in lines[1:]:
        name, literal = line.split('=', 1)
        values[name.strip()] = ast.literal_eval(literal.strip())
    v, m, q = int(header[1]), int(header[2]), ast.literal_eval(header[3])
    assert len(q) == m and all(len(a) == v + 1 for a in values.values())
    return v, m, q, values


def physical(instance_path, panel, result):
    v, m, q, a = parse_instance(instance_path)
    y = a['initial'].copy()
    stations, vehicles, route_checks = set(), set(), []
    for route in result['routes']:
        k = route.get('vehicle', route.get('vehicle_id'))
        assert k not in vehicles and 0 <= k < m
        vehicles.add(k)
        nodes = route['nodes']
        assert nodes[0] == nodes[-1] == 0
        operations = {o['station']: (o['pickup'], o['drop']) for o in route['operations']}
        assert len(operations) == len(route['operations'])
        assert len(nodes[1:-1]) == len(set(nodes[1:-1])) and set(nodes[1:-1]) == set(operations)
        load, total_pick, prefixes = 0, 0, []
        for station in nodes[1:-1]:
            assert station not in stations and 1 <= station <= v
            stations.add(station)
            pick, drop = operations[station]
            assert type(pick) is int and type(drop) is int
            assert pick >= 0 and drop >= 0 and (bool(pick) != bool(drop))
            load += pick - drop
            total_pick += pick
            prefixes.append(load)
            assert 0 <= load <= q[k]
            y[station] += drop - pick
            assert 0 <= y[station] <= a['capacities'][station]
        travel = math.fsum(math.dist(a['points'][i], a['points'][j]) / 1.5 for i, j in zip(nodes, nodes[1:]))
        duration = travel + (panel['pickup_seconds'] + panel['drop_seconds']) * total_pick
        assert duration <= panel['T_seconds'] + 1e-7
        route_checks.append(dict(vehicle=k, prefix_loads=prefixes, return_load=load,
                                 cumulative_pickup=total_pick, travel=travel, duration=duration))
    assert sum(y[1:]) + sum(c['return_load'] for c in route_checks) == sum(a['initial'][1:])
    ratios = [y[i] / a['target'][i] for i in range(1, v + 1)]
    denominator = math.fsum(ratios)
    g = math.fsum(abs(ratios[i] - ratios[j]) for i in range(v) for j in range(i + 1, v)) / (v * denominator) if denominator else 0.
    p = math.fsum(a['weights'][i] * abs(ratios[i - 1] - 1) for i in range(1, v + 1))
    f = g + panel['lambda'] * p
    assert abs(f - result['upper_bound']) <= 1e-7
    return dict(G=g, P=p, lambda_P=panel['lambda'] * p, F=f, Y=y, routes=route_checks,
                empty_vehicles=m-len(vehicles), original_physical_check=True)


def expression(source, register):
    words = source.split()
    coefficients, constant, sign, i = {}, 0., 1., 0
    while i < len(words):
        if words[i] in ['+', '-']:
            sign = -1. if words[i] == '-' else 1.
            i += 1
        item = words[i]
        try:
            value = float(item) * sign
        except ValueError:
            register(item)
            coefficients[item] = coefficients.get(item, 0.) + sign
            i += 1
        else:
            i += 1
            if i < len(words) and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', words[i]):
                register(words[i])
                coefficients[words[i]] = coefficients.get(words[i], 0.) + value
                i += 1
            else:
                constant += value
        sign = 1.
    return coefficients, constant


def lp(path):
    order, names, bounds, types, rows, section, objective = [], set(), {}, {}, [], None, None
    def register(name):
        assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name)
        if name not in names:
            names.add(name)
            order.append(name)
    for line in text(path).splitlines():
        line = line.strip()
        if not line or line.startswith('\\'):
            continue
        if line in ['Minimize', 'Subject To', 'Bounds', 'Generals', 'Binaries', 'End']:
            section = line
            continue
        if section == 'Minimize':
            assert objective is None
            objective = expression(line.split(':', 1)[1], register)
        elif section == 'Subject To':
            body = line.split(':', 1)[1]
            match = re.fullmatch(r'(.*)\s(<=|>=|=)\s(\S+)', body)
            assert match
            terms, constant = expression(match[1], register)
            rows.append((terms, match[2], float(match[3]) - constant))
        elif section == 'Bounds':
            lo, le, name, le2, hi = line.split()
            assert le == le2 == '<=' and name not in bounds
            register(name)
            bounds[name] = (float(lo), float(hi))
        elif section in ['Generals', 'Binaries']:
            for name in line.split():
                register(name)
                assert name not in types
                types[name] = 'I' if section == 'Generals' else 'B'
        else:
            raise AssertionError(('unsupported LP content', section))
    assert section == 'End' and names == set(bounds) and objective
    return dict(order=order, bounds=bounds, types={n: types.get(n, 'C') for n in order}, rows=rows, objective=objective)


def scope_check(model, call, panel):
    if call['full_original']:
        return dict(full_original=True, canonical_reference_binding=True)
    assert model['bounds']['G'] == (call['lower_g'], call['upper_g'])
    terms, constant = model['objective']
    assert any(t == terms and s == '<=' and abs(r-(call['cutoff']-constant)) <= 1e-12 for t, s, r in model['rows'])
    for gamma, sense in [(call['lower_g'], '>='), (call['upper_g'], '<=')]:
        expected = {f'h_{i}_{j}': 1. for i in range(1, panel['V']+1) for j in range(i+1, panel['V']+1)}
        if gamma:
            expected.update({f'r_{i}': -panel['V']*gamma for i in range(1, panel['V']+1)})
        assert any(s == sense and r == 0 and set(t) == set(expected) and
                   all(abs(t[n]-expected[n]) <= 1e-12 for n in expected) for t, s, r in model['rows'])
    return dict(full_original=False, actual_G_interval=[call['lower_g'], call['upper_g']],
                objective_cutoff=call['cutoff'], true_G_caps_and_objective_cutoff_recomputed=True)


def start_check(path, model):
    metadata = read(path)
    if not metadata['submitted']:
        return dict(source=str(path), submitted=False)
    for name in ['mapping_complete', 'rows_valid', 'objective_valid', 'readback_valid']:
        assert metadata[name]
    values_path = path.with_name(path.name[:-5] + '.values.csv')
    with values_path.open(newline='') as f:
        values = list(csv.DictReader(f))
    assert [v['variable'] for v in values] == model['order']
    point = {v['variable']: float(v['value']) for v in values}
    maximum = 0.
    for row in values:
        name, value = row['variable'], float(row['value'])
        assert math.isfinite(value) and abs(value-float(row['readback'])) <= 1e-7
        assert row['type'] == model['types'][name]
        lo, hi = model['bounds'][name]
        maximum = max(maximum, lo-value, value-hi)
        if row['type'] in ['I', 'B'] or name.startswith(('p_', 'd_')):
            assert abs(value-round(value)) <= 1e-5
    for terms, sense, rhs in model['rows']:
        activity = math.fsum(c*point[n] for n, c in terms.items())
        violation = abs(activity-rhs) if sense == '=' else max(0., activity-rhs) if sense == '<=' else max(0., rhs-activity)
        maximum = max(maximum, violation)
    terms, constant = model['objective']
    objective = constant + math.fsum(c*point[n] for n, c in terms.items())
    assert maximum <= 1e-7 and abs(objective-metadata['objective']) <= 1e-7
    return dict(source=str(path), metadata_SHA=sha(path), values_SHA=sha(values_path), submitted=True,
                columns=len(values), rows=len(model['rows']), maximum_residual=maximum, objective=objective,
                complete_type_and_value_readback_recomputed=True)


def current_pid(pid):
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    api.OpenProcess.restype = ctypes.c_void_p
    api.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_ulonglong)]*4
    api.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        return dict(pid=pid, status='NOT_PRESENT' if ctypes.get_last_error() == 87 else 'QUERY_UNAVAILABLE', error=ctypes.get_last_error())
    try:
        creation, end, kernel, user = [ctypes.c_ulonglong() for _ in range(4)]
        exit_code = ctypes.c_ulong()
        assert api.GetProcessTimes(handle, *[ctypes.byref(x) for x in [creation, end, kernel, user]])
        assert api.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        return dict(pid=pid, current_creation_unix=creation.value/1e7-11644473600,
                    status='CURRENTLY_RUNNING' if exit_code.value == 259 else 'EXITED_HANDLE', exit_code=exit_code.value)
    finally:
        api.CloseHandle(handle)


def rule_replay():
    """Separate verbal-rule calculation against frozen pure functions only."""
    def take(path, names, namespace):
        tree = ast.parse(text(path))
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        assert len(selected) == len(names)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
        return namespace
    frozen = take(ROOT/'scripts/round108_decisions.py', ['finite', 'qualified_numbers', 'pair'],
                  dict(math=math, CLOSURE_TOL=1e-7, ZERO_TOL=1e-12))['pair']
    decide = take(ROOT/'scripts/round121_decision.py', ['decide'], {})['decide']
    def independent(c, p):
        assert c['certificate_qualified'] is True and p['certificate_qualified'] is True
        valid = []
        for item in [c, p]:
            valid.append(item['numbers_qualified'] and all(isinstance(item[k], (int, float)) and math.isfinite(item[k]) for k in ['U', 'L']))
            if valid[-1]:
                assert item['L'] <= item['U']+1e-7
        if c['certificate'] != p['certificate']:
            return ('WIN', False) if c['certificate'] else ('LOSS', True)
        if c['certificate']:
            saving = p['complete_seconds']-c['complete_seconds']
            threshold = max(30., p['complete_seconds']/10)
            return ('WIN' if saving >= threshold else 'LOSS' if saving <= -threshold else 'TIE',
                    c['complete_seconds'] >= 2*p['complete_seconds'] and -saving >= 120)
        if not all(valid):
            return 'UNEVALUABLE', False
        du, dg = p['U']-c['U'], p['gap']-c['gap']
        material_u, material_g = max(.001, abs(p['U'])/100), max(.001, abs(p['gap'])/10)
        favorable = du >= material_u or dg >= material_g
        adverse = du <= -material_u or dg <= -material_g
        return ('MIXED' if favorable and adverse else 'WIN' if favorable else 'LOSS' if adverse else 'TIE',
                -du >= max(.001, .05*abs(p['U'])) and -dg >= max(.005, .25*abs(p['gap'])))
    def arm(u=10., gap=6., cert=False, seconds=100.):
        return dict(arm='SYNTHETIC', U=u, L=u-gap, gap=gap, certificate=cert,
                    certificate_qualified=True, numbers_qualified=True, complete_seconds=seconds)
    p = arm()
    cases = [
        ('certificate_first_win', arm(cert=True), p, ('WIN', False)),
        ('certificate_first_loss', p, arm(cert=True), ('LOSS', True)),
        ('certified_30_seconds_win', arm(cert=True, seconds=70), arm(cert=True), ('WIN', False)),
        ('certified_30_seconds_loss', arm(cert=True, seconds=130), arm(cert=True), ('LOSS', False)),
        ('certified_10_percent_win', arm(cert=True, seconds=360), arm(cert=True, seconds=400), ('WIN', False)),
        ('certified_time_severe_120', arm(cert=True, seconds=220), arm(cert=True), ('LOSS', True)),
        ('certified_double_without_120_not_severe', arm(cert=True, seconds=200), arm(cert=True), ('LOSS', False)),
        ('open_U_gain', arm(u=9), p, ('WIN', False)),
        ('open_gap_gain', arm(gap=5), p, ('WIN', False)),
        ('open_gap_loss', arm(gap=7), p, ('LOSS', False)),
        ('open_mixed', arm(u=9, gap=7), p, ('MIXED', False)),
        ('open_tie', arm(u=10.0001), p, ('TIE', False)),
        ('open_severe_both_conjuncts', arm(u=11, gap=8), p, ('LOSS', True)),
        ('open_U_only_not_severe', arm(u=11), p, ('LOSS', False)),
        ('open_gap_only_not_severe', arm(gap=8), p, ('LOSS', False)),
        ('unqualified_not_time_loss', dict(p, numbers_qualified=False), p, ('UNEVALUABLE', False)),
        ('signed_negative_tiny_gap', arm(u=1, gap=-5e-8), arm(u=1, gap=-5e-8), ('TIE', False)),
        ('zero_objective', arm(u=0, gap=0), arm(u=0, gap=0), ('TIE', False)),
    ]
    checked = []
    for name, c, p, expected in cases:
        actual = frozen(c, p)
        assert independent(c, p) == (actual['classification'], actual['severe_regression']) == expected
        if name in ['signed_negative_tiny_gap', 'zero_objective']:
            assert not actual['percentage_gap_path_applicable'] and actual['gap_ratio'] is None
        checked.append(dict(case=name, classification=actual['classification'], severe=actual['severe_regression']))
    small = frozen(arm(u=.02, gap=.002), arm(u=.02, gap=.002))
    large = frozen(arm(), arm())
    assert (small['a_U'], small['a_gap'], large['a_U'], large['a_gap']) == (.001, .001, .1, .6000000000000001)
    for c, p in [(dict(arm(), L=11), arm()), (dict(arm(), certificate_qualified=False), arm())]:
        for evaluator in [independent, frozen]:
            try:
                evaluator(c, p)
            except AssertionError:
                pass
            else:
                raise AssertionError('qualification/contradictory-bound rejection weakened')
    old = read(OUT/'preflight_R120_pair_replay.json')
    counts, old_pairs = collections.Counter(), 0
    for group in old['saved_groups']:
        by = {a['arm']: a for a in group['arms']}
        for pair in group['pairs']:
            result = independent(by[pair['candidate']], by[pair['control']])
            assert result == (pair['classification'], pair['severe_regression'])
            assert (frozen(by[pair['candidate']], by[pair['control']])['classification'],
                    frozen(by[pair['candidate']], by[pair['control']])['severe_regression']) == result
            counts[result[0]] += 1
            old_pairs += 1
    assert old_pairs == 18
    values = []
    for number, (role, seed, cap, methods) in enumerate(EXPECTED, 1):
        values.append(dict(group=dict(number=number, seed=seed),
            arms=[dict(arm=m, actually_executed=True, formal_protocol_qualified=True, certificate=False) for m in methods],
            pairs=[dict(candidate=c, control=p, classification='WIN', severe_regression=False, evaluable=True)
                   for c, p in (F2_PAIRS if number == 1 else OTHER_PAIRS)],
            mechanism=[dict(arm='MB-D1', installed=1, actual_extended_Optimize=1)]))
    stage_cases = []
    def check(name, data, expected, new=True, proof=False, blockers=()):
        result = decide(data, new, proof_risk=proof, blockers=blockers)
        assert result['stage'] == expected
        stage_cases.append(dict(case=name, expected=expected))
    check('all_support', values, 'ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK')
    check('proof_priority_over_blocker', values, 'PROOF_RELIABILITY_PRIORITY', proof=True, blockers=['MEMORY'])
    check('blocker_before_performance', values, 'BLOCKED', blockers=['MEMORY'])
    check('actual_empty_payload', [], 'BLOCKED')
    check('missing_new_identity_support', values, 'RETAIN_D1_AS_DEVELOPMENT_COMPONENT', new=False)
    for reason in ['severe_primary', 'two_new_losses', 'certificate_deficit', 'no_exposure', 'incomplete', 'known_seed_missing']:
        changed = copy.deepcopy(values)
        if reason == 'severe_primary':
            next(p for p in changed[0]['pairs'] if (p['candidate'], p['control']) == ('MB-D1', 'P-GRB'))['severe_regression'] = True
        elif reason == 'two_new_losses':
            for index in [1, 3]:
                next(p for p in changed[index]['pairs'] if (p['candidate'], p['control']) == ('MB-D1', 'P-GRB'))['classification'] = 'LOSS'
        elif reason == 'certificate_deficit':
            next(a for a in changed[0]['arms'] if a['arm'] == 'M-B')['certificate'] = True
        elif reason == 'no_exposure':
            for value in changed:
                value['mechanism'][0]['installed'] = 0
        elif reason == 'incomplete':
            changed[0]['arms'][0]['actually_executed'] = False
        else:
            changed[0]['group']['seed'] = 0
        expected = 'STOP_FROZEN_D1_CONFIRMATION' if reason in ['severe_primary', 'two_new_losses', 'certificate_deficit'] else 'BLOCKED' if reason == 'incomplete' else 'RETAIN_D1_AS_DEVELOPMENT_COMPONENT'
        check(reason, changed, expected)
    changed = copy.deepcopy(values)
    for value in changed:
        for pair in value['pairs']:
            if pair['candidate'] == 'MB-D1' and pair['control'] in ['M-B', 'MB-D0']:
                pair['classification'] = 'LOSS'
    next(p for p in changed[1]['pairs'] if (p['candidate'], p['control']) == ('MB-D1', 'M-B'))['classification'] = 'WIN'
    check('no_hidden_all_MB_D0_dominance_veto', changed, 'ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK')
    return dict(pair_fixtures=checked, stage_fixtures=stage_cases, R120_saved_pairs_recomputed=old_pairs,
                R120_classifications=dict(counts), R120_replay_SHA=sha(OUT/'preflight_R120_pair_replay.json'),
                thresholds=dict(a_U='max(.001,.01*abs(control_U))', a_gap='max(.001,.10*abs(control_gap))',
                    a_t='max(30,.10*control_certified_seconds)', open_severe='UB worsening >= max(.001,.05*abs(control_U)) AND gap worsening >= max(.005,.25*abs(control_gap))',
                    certified_severe='candidate_time >= 2*control_time AND candidate_time-control_time >= 120'),
                synthetic_only_not_current_formal_evidence=True,
                current_18_UNEVALUABLE_not_converted_to_R120_outcomes=True,
                method='New verbal-rule classifier and explicit expected stage scenarios; only AST-extracted pure frozen functions were compared, without module imports.')


def journal_and_native(directory, launch):
    panel = launch['panel']
    observations = read(directory/'observations.json')
    calls, returned, cancelled = {}, {}, set()
    for sequence, row in enumerate(observations, 1):
        receipt = (directory/'journal'/f'event_{sequence}.commit').read_text().split()
        assert len(receipt) == 5 and receipt[:2] == ['NEJ1', str(sequence)]
        body = directory/'journal'/f'event_{sequence}.json'
        assert body.stat().st_size == int(receipt[3]) and sha(body) == receipt[4] == row['sha256']
        assert read(body) == row['payload'] and row['sequence'] == row['payload']['sequence'] == sequence
        assert abs(float(receipt[2])-row['data_close_seconds']) <= 1e-12
        assert row['effective_available_seconds'] == max(row['first_observed_seconds'], row['data_close_seconds'])
        assert 0 <= row['effective_available_seconds'] <= launch['cap_seconds']
        event = row['payload']
        if event['kind'] == 'call':
            cid = event['call']
            assert cid == len(calls)+1
            assert event['settings'] == dict(read_return_code=0, Threads=1, Seed=1, Presolve=-1,
                MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, OptimalityTol=1e-6, IntFeasTol=1e-5)
            assert event['native_preconditions'] == 0
            assert sha(Path(event['model_path'])) == event['model_sha256']
            calls[cid] = event
        elif event['kind'] == 'returned':
            assert event['call'] in calls and event['call'] not in returned and event['return_code'] == 0
            returned[event['call']] = sequence
        elif event['kind'] == 'not_started':
            assert event['actual_Optimize'] is False
            cancelled.add(event['call'])
        elif event['kind'] == 'bound':
            assert event['global_available'] == 0 and event['global_bound'] is None
        else:
            assert event['kind'] in ['identity', 'witness', 'witness_rejected']
    assert set(calls) == set(returned) and not cancelled
    ledger_path = directory/'external/paper_optimize_ledger.csv'
    if ledger_path.exists():
        with ledger_path.open(newline='') as f:
            ledger = list(csv.DictReader(f))
        assert len(ledger) == len(calls)
    else:
        ledger = [None]*len(calls)
    models, checks, log_groups = {}, [], collections.defaultdict(list)
    for (cid, call), entry in zip(calls.items(), ledger):
        path = Path(call['model_path'])
        if call['model_sha256'] not in models:
            models[call['model_sha256']] = lp(path)
        model = models[call['model_sha256']]
        if launch['arm'] == 'P-GRB':
            assert sha(path) == panel['reference']['canonical_sha256']
            assert all(model['types'][n] == 'I' for n in model['types'] if n.startswith(('p_', 'd_')))
        else:
            assert all(model['types'][n] == 'C' for n in model['types'] if n.startswith(('p_', 'd_')))
            assert all(model['types'][n] == 'I' for n in model['types'] if n.startswith(('Y_', 'load_')))
            assert 'r120_h' not in model['types']
            assert entry['model_sha256'] == call['model_sha256'] and entry['leaf_id'] == call['leaf']
            assert int(entry['optimize_return_code']) == 0
            if entry['solve_kind'] == 'LP':
                assert int(entry['integer_domain_restored']) == 1
        scope = scope_check(model, call, panel)
        checks.append(dict(call=cid, SHA=call['model_sha256'], rows=len(model['rows']), columns=len(model['order']),
                           types=dict(collections.Counter(model['types'].values())), scope=scope,
                           solve_kind=entry['solve_kind'] if entry else 'MIP', return_sequence=returned[cid]))
        log_groups[Path(call['native_log_path'])].append((cid, call, entry, model))
    spans = []
    for path, entries in log_groups.items():
        content = path.read_bytes()
        starts = [m.start() for m in re.finditer(rb'(?m)^Gurobi Optimizer version ', content)]
        assert len(starts) == len(entries)
        for (cid, call, entry, model), lo, hi in zip(entries, starts, starts[1:]+[len(content)]):
            part = content[lo:hi]
            assert part.count(b'Optimize a model with ') == 1
            frame = part.decode()
            match = re.search(r'Optimize a model with (\d+) rows, (\d+) columns', frame)
            assert (int(match[1]), int(match[2])) == (len(model['rows']), len(model['order']))
            assert re.search(r'(Solved in |Explored \d+ nodes)', frame)
            assert re.search(r'(Optimal objective|Best objective )', frame)
            types = re.search(r'Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)', frame)
            lp_call = entry and entry['solve_kind'] == 'LP'
            if types:
                actual = dict(C=int(types[1]), I=int(types[2])-int(types[3]), B=int(types[3]))
                expected = dict(C=len(model['order']), I=0, B=0) if lp_call else dict(collections.Counter(model['types'].values()))
                assert all(actual[k] == expected.get(k, 0) for k in actual)
            else:
                assert lp_call
            for name, value in re.findall(r'(?m)^(Seed|Threads|Presolve|MIPGap|MIPGapAbs|FeasibilityTol|OptimalityTol|IntFeasTol)\s+([-+0-9.eE]+)\s*$', frame):
                assert float(value) == call['settings'][name]
            if launch['arm'] == 'P-GRB':
                assert 'Loaded user MIP start' not in frame
            spans.append(dict(call=cid, raw_log_SHA=sha(path), start_byte=lo, end_byte=hi,
                              segment_SHA=hashlib.sha256(part).hexdigest(), solve_kind='LP' if lp_call else 'MIP'))
    starts = []
    for path in sorted((directory/'external/native_logs').glob('*.round68.start.json')):
        metadata = read(path)
        assert metadata['model_sha256'] in models
        starts.append(start_check(path, models[metadata['model_sha256']]))
    assert len(calls) == (1 if launch['arm'] == 'P-GRB' else 5)
    return dict(events=len(observations), calls=checks, call_log_spans=spans, complete_Starts=starts,
                raw_seed_guard_int0_preserved=True, raw_global_flags_not_promoted=True)


def run():
    tick = time.perf_counter()
    rules = rule_replay()
    core = read(OUT/'blocked_current_core.json')
    slots, pairs = read(OUT/'all16_arms.json'), read(OUT/'all18_pairs.json')
    manifest, frozen = read(OUT/'input_manifest.json'), read(OUT/'argv_freeze.json')
    expected_slots, expected_pairs = [], []
    for number, (role, seed, cap, methods) in enumerate(EXPECTED, 1):
        group = frozen['groups'][number-1]
        assert (group['id'], group['seed'], group['cap_seconds'], group['methods']) == (role, seed, cap, methods)
        identity = read(OUT/group['campaign']/'identity.json')
        for method, launch in zip(methods, identity['launches']):
            assert launch['id'] == role and launch['arm'] == method and launch['seed'] == seed
            assert not Path(launch['destination']).exists()
            expected_slots.append((number, role, seed, method, cap))
        expected_pairs.extend((number, role, seed, c, p) for c, p in (F2_PAIRS if number == 1 else OTHER_PAIRS))
    assert len(slots) == len(set(expected_slots)) == 16
    assert [(s['group'], s['id'], s['seed'], s['arm'], s['cap_seconds']) for s in slots] == expected_slots
    assert all(not s['actually_executed'] and not s['formal_protocol_qualified'] and s['state'].startswith('NOT_STARTED') for s in slots)
    assert all(s[k] is None for s in slots for k in ['U', 'L', 'gap', 'certificate', 'T_produce', 'T_verify', 'T_total'])
    assert [(p['group'], p['id'], p['seed'], p['candidate'], p['control']) for p in pairs] == expected_pairs
    assert len(pairs) == 18 and all(p['classification'] == 'UNEVALUABLE' and not p['evaluable'] and p['severe_regression'] is None for p in pairs)
    assert slots == core['formal_slots'] and pairs == core['pair_slots']
    assert core['actual_formal_arms'] == core['actual_formal_pairs'] == []
    stage = read(OUT/'stage_decision.json')
    assert stage['stage'] == stage['execution_stage'] == 'BLOCKED' and stage['performance_gate_evaluated'] is False
    assert stage['all_support_and_veto_counts_unobserved'] and stage['observed_zero_certificate_counts_are_not_a_performance_tie']
    assert stage['formal_arms'] == stage['formal_pairs'] == 0
    assert not (OUT/'review/performance_admission.json').exists()
    production = read(OUT/'production_identity.json')
    assert sha(ROOT/'build/research/round120/ExactEBRP.exe') == production['production_PE_SHA'] == PE_SHA
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll')) == production['DLL_SHA'] == DLL_SHA
    candidate = read(OUT/'candidate_identity.json')
    for name, digest in candidate['source_bindings'].items():
        assert sha(ROOT/name) == digest
    for name, digest in candidate['helpers'].items():
        assert sha(ROOT/name) == digest
    assert candidate['source_bindings'] == production['source_bindings']
    assert candidate['argv_freeze_SHA'] == sha(OUT/'argv_freeze.json') and candidate['protocol_SHA'] == sha(OUT/'protocol.json')
    assert candidate['input_manifest_SHA'] == sha(OUT/'input_manifest.json')
    fees = []
    for name in ['qualification01', 'qualification02', 'qualification03', 'qualification04']:
        directory = OUT/'fees'/name
        launch, receipt = read(directory/'launch.json'), read(directory/'receipt.json')
        assert receipt['actual_exit_observed'] and receipt['exit_code'] == 1 and launch['qualification']
        assert receipt['conservative_process_starts'] == 1+receipt['actual_native_children']
        assert receipt['outer_seconds_upper'] >= receipt['outer_seconds_lower'] and not receipt['nested_native_seconds_added']
        assert abs(receipt['outer_seconds_upper'] - max(receipt['outer_seconds_lower'], receipt['caller_observed_unix']-launch['wrapper_creation_unix'])) <= 1e-8
        process = current_pid(launch['wrapper_pid'])
        assert not (process['status'] == 'CURRENTLY_RUNNING' and abs(process['current_creation_unix']-launch['wrapper_creation_unix']) < 1e-4)
        fees.append(dict(name=name, parent_pid=launch['wrapper_pid'], parent_creation_unix=launch['wrapper_creation_unix'],
                         current_pid_check=process, starts=receipt['conservative_process_starts'], children=receipt['actual_native_children'],
                         seconds=receipt['outer_seconds_upper'], receipt_SHA=sha(directory/'receipt.json')))
    starts, seconds = sum(v['starts'] for v in fees), sum(v['seconds'] for v in fees)
    assert starts == 7 and abs(seconds-445.13650035858154) < 1e-9
    resource = read(OUT/'resource_summary.json')
    assert resource['paid_starts'] == resource['qualification_starts'] == starts
    assert resource['paid_outer_seconds'] == resource['qualification_seconds'] == seconds
    assert resource['qualification_remaining_starts'] == 1 and resource['last_reviewed_minimum_needed_starts'] == 2
    assert resource['formal_seconds_spent'] == 0 and resource['actual_H100_CLI'] == 2
    exporter = read(OUT/'fees/qualification02/01_reference_PID.json')
    assert exporter['parent_pid'] == fees[1]['parent_pid'] and exporter['actual_creation_unix'] > fees[1]['parent_creation_unix']
    assert read(OUT/'fees/qualification02/01_reference_return.json')['exit_code'] == 0
    actual = []
    hidentity = read(OUT/'qualification/h100/identity.json')
    for launch in hidentity['launches']:
        directory = Path(launch['destination'])
        if not directory.exists():
            assert launch['arm'] in ['MB-D0', 'MB-D1']
            actual.append(dict(arm=launch['arm'], Seed=launch['seed'], state='NOT_STARTED'))
            continue
        seal, producer = read(directory/'producer_seal.json'), read(directory/'producer_receipt.json')
        assert producer['producer_seal_SHA'] == sha(directory/'producer_seal.json')
        assert all(sha(directory/name) == digest for name, digest in seal['required_SHA'].items())
        assert producer['T_produce'] == producer['t_produce_perf']-producer['t0_perf'] and producer['T_produce'] <= 120
        completion = read(directory/'completion.json')
        assert completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return' and completion['within_cap']
        assert completion['fully_observed_end_to_end_seconds'] <= read(directory/'native_end_receipt.json')['complete_seconds_until_native_end'] <= producer['T_produce']
        affinity = read(directory/'affinity.json')
        assert affinity['child']['process_mask'] == 4 and affinity['parent']['effective']['process_mask'] == 4
        assert launch['command'][launch['command'].index('--gurobi-seed')+1] == '1'
        result = read(directory/'result.json')
        fleet = physical(ROOT/launch['panel']['input_path'], launch['panel'], result)
        native = journal_and_native(directory, launch)
        total_path = directory/'arm_total_receipt.json'
        if launch['arm'] == 'P-GRB':
            assert total_path.exists() and read(directory/'audit.json')['passed']
            total = read(total_path)
            assert abs(total['T_total']-producer['T_produce']-total['T_verify']) <= 1e-8
            closeout = dict(state='COMPLETE', T_verify=total['T_verify'], T_total=total['T_total'])
        else:
            assert not total_path.exists() and read(directory/'audit.json')['passed'] is False
            closeout = dict(state='INCOMPLETE_ORIGINAL_CLOSEOUT', T_verify=None, T_total=None,
                            overlay_does_not_replace_original_closeout=True)
        actual.append(dict(arm=launch['arm'], Seed=1, state='ACTUAL_CLI_SEALED', child_pid=affinity['pid'],
                           launcher_pid=affinity['parent']['launcher_pid'], current_pid_check=current_pid(affinity['pid']),
                           exact_child_OS_creation='NOT_PERSISTED_IN_RAW; prelaunch marker is not child creation',
                           T_produce=producer['T_produce'], producer_receipt_SHA=sha(directory/'producer_receipt.json'),
                           producer_seal_SHA=sha(directory/'producer_seal.json'), physical=fleet, native=native, closeout=closeout))
    source_table = ROOT/'results/unified_exact_round116/source/source_station_table.csv'
    assert sha(source_table) == TABLE_SHA
    with source_table.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 865
    snapshot = read(ROOT/'results/unified_exact_round116/source/snapshot.json')
    assert sha(ROOT/snapshot['station_response_path']) == RAW_SHA
    recipe, receipt = read(OUT/'source_recipe.json'), read(OUT/'generation_receipt.json')
    assert manifest['source_recipe_SHA'] == sha(OUT/'source_recipe.json')
    assert recipe['generated_input_count'] == 0 and receipt['unique_new_input_files_written'] == 3
    assert recipe['frozen_UTC'] < receipt['generated_UTC']
    assert receipt['recipe_commit'] == manifest['recipe_commit_before_generation']
    assert receipt['Optimize'] == receipt['native_starts'] == 0
    for name, digest in recipe['generation_dependencies'].items():
        assert sha(ROOT/name) == digest
    old_roles = read(ROOT/'results/unified_exact_round116/input_manifest.json')['roles'] + read(ROOT/'results/unified_exact_round118/input_manifest.json')['roles']
    old_hashes = set(read(ROOT/'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths']) | {p['input_sha256'] for p in old_roles}
    overlap, new_inputs = [], []
    for panel in manifest['new_roles']:
        path = ROOT/panel['input_path']
        assert sha(path) == panel['input_sha256'] and sha(path) not in old_hashes
        v, m, q, values = parse_instance(path)
        assert (v, m, q) == (panel['V'], panel['M'], panel['Q_vector'])
        selection = read(ROOT/panel['selection_path'])
        landscape = read(ROOT/panel['landscape_path'])
        assert selection['dataset_family'] == landscape['dataset_family'] == manifest['family'] == recipe['family']
        selected = selection['selected_source_station_row_indices']
        assert len(selected) == len(set(selected)) == v
        for j, idx in enumerate(selected, 1):
            row = rows[idx]
            assert int(row['source_row_index']) == idx and values['capacities'][j] == int(row['capacity'])
            assert values['points'][j] == (float(row['utm18n_easting_m']), float(row['utm18n_northing_m']))
            assert 0 <= values['initial'][j] <= values['capacities'][j] and 0 < values['target'][j] <= values['capacities'][j]
        total = sum(values['target'][1:])
        delta = max(v, math.floor(.12*total+.5))
        desired = total if panel['inventory'] == 'balanced' else max(0, total-delta) if panel['inventory'] == 'shortage' else min(sum(values['capacities'][1:]), total+delta)
        assert sum(values['initial'][1:]) == desired
        assert abs(math.fsum(values['weights'][1:])-panel['sum_weights']) <= 1e-12
        assert abs(panel['lambda_sum_weights']-.15*math.fsum(values['weights'][1:])) <= 1e-12
        for previous in old_roles:
            if previous['V'] <= 50:
                old = read(ROOT/previous['selection_path'])['selected_source_station_row_indices']
                overlap.append(dict(id=panel['id'], old_id=previous['id'], old_V=previous['V'], new_V=v,
                                    overlap=len(set(selected)&set(old))))
        new_inputs.append(dict(id=panel['id'], SHA=sha(path), B=sum(values['initial'][1:]), D=total,
                               sum_weights=panel['sum_weights'], lambda_sum_weights=panel['lambda_sum_weights'], performance_measured=False))
    assert overlap == manifest['overlaps'] and len(overlap) == 15
    assert len(list((ROOT/'reference/round121_confirmation').glob('*.txt'))) == 3
    adapter = text(ROOT/'scripts/round121_data.py')
    assert "old.FAMILY=FAMILY;landscape_math.VERSION=FAMILY;landscape_math.SOURCE_SHA=RAW_SHA" in adapter
    assert "path.open('x'" in adapter and "assert not REF.exists()" in adapter
    assert 'Optimize' not in adapter[:adapter.index('def freeze')]
    mechanism, layers = read(OUT/'mechanism_account.json'), read(OUT/'seed_stratification.json')
    assert mechanism['formal_mechanism'] == mechanism['formal_costs'] == []
    assert mechanism['new_D1_native_types_rows_Start_physical_endpoint'].startswith('UNAVAILABLE')
    assert layers['measured_new_problems'] == layers['measured_known_Seed1_blocks'] == layers['evaluable_pairs'] == 0
    assert layers['planned_new_problem_denominator'] == 3 and layers['planned_known_Seed1_blocks'] == 2
    assert layers['Seed0_history_separate'] and layers['no_best_of_Seeds'] and layers['no_pooled_mean_or_win_rate']
    report = text(OUT/'final_report.md')
    assert '**Execution: BLOCKED. Decision: BLOCKED.**' in report
    assert 'All 18 pair slots are UNEVALUABLE' in report and 'No formal arm was started' in report
    assert 'No U/L/gap' in report and 'M-B retains its failed canonical audit' in report
    findings = []
    resume = text(OUT/'RESUME.md')
    if 'BLOCKED' not in resume[:1500] or '445.136500' not in resume[:2000]:
        findings.append(dict(id='RESUME_STALE_ACTIVE_STATE', severity='correction_required', detail='Current BLOCKED/7 starts/445.136500 seconds and no further native authority must override historical running/continuation notes at the top.'))
    spec = text(OUT/'paper_algorithm_spec.md')
    if not ('Seed1' in spec[:2000] and ('historical' in spec[:2000].lower() or '历史' in spec[:2000])):
        findings.append(dict(id='SPEC_HISTORICAL_SEED_EXAMPLE_SCOPE', severity='clarification_required', detail='Scope inherited All methods Seed0/current B239-D279 examples as historical; frozen R121 roles govern Seed and input.'))
    output = dict(review_kind='real_different_executor_post_organization_extra_review',
        limited_blocked_delivery_review='ACCEPT_WITH_EXPLICIT_UNAVAILABLE_CHECKS' if not findings else 'CORRECTIONS_REQUIRED',
        original_scientific_confirmation='INCOMPLETE_NOT_PERFORMED', all_scientific_extra_review_requirements_completed=False,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), script_SHA=sha(__file__),
        method='Independent standard-library slot/fee/physical/LP/Start/journal parser; no production or blocked-core functions imported.',
        formal_slots_checked=16, formal_pairs_checked=18, actual_formal_arms=0, evaluable_formal_pairs=0,
        expected_slots=expected_slots, expected_pairs=expected_pairs, frozen_stage=dict(execution='BLOCKED', performance_gate_evaluated=False),
        frozen_rule_replay=rules,
        source_identity=dict(production_source='355eefd2be3fe5651195681faf7b3a63ee4032f8', PE_SHA=PE_SHA, DLL_SHA=DLL_SHA,
                             source_files=len(candidate['source_bindings']), helper_files=len(candidate['helpers']), all_current_hashes_match=True),
        fees=fees, total_starts=starts, total_outer_seconds=seconds, qualification_remaining_starts=1,
        qualification_remaining_seconds=1800-seconds, required_minimum_starts=2, start_deficit=1,
        parent_and_exporter_OS_creation_recorded=True, child_creation_record_limit='P/MB PID and affinity are persisted; exact OS creation is absent in raw. P has a historical RESUME observation; no prelaunch marker was promoted to actual creation.',
        exporter=dict(pid=exporter['pid'], creation_unix=exporter['actual_creation_unix'], parent_pid=exporter['parent_pid']),
        actual_qualification=actual, new_inputs=new_inputs, source_rows=865, independent_overlaps=overlap,
        once_only_generation_scope='Recorded pre-generation commit/UTC/SHA links and exclusive single-draw adapter agree; no Git operation or network was used. Unlogged external prior measurements cannot be ruled out from these artifacts.',
        new_D1_physical_endpoint_and_actual_three_rows=dict(status='UNAVAILABLE_NO_NEW_D1_EXECUTION', checked=False,
            reason='H100 D1 and every formal D1 position are NOT_STARTED; no physical endpoint, native h/three-row/Start or extended-search record exists to inspect.'),
        default_state=dict(ENS_C_changed=False, M_B_retained=True, D0_not_promoted=True, R119_MB_PC_still_stopped=True),
        current_stage_is_not_scientific_STOP_RETAIN_or_ADVANCE=True, findings=findings,
        limitations=['No native rerun, Optimize, compilation, Git, historical-carrier restore, new route, new bound or LP was performed.',
            'Existing native/Start scope checks cover actual P/MB qualification only, not an unrun D1.',
            'P/MB physical replay does not convert H100 qualification into formal benchmark data or repair MB original closeout.',
            'All formal thresholds, severe flags, certificate counts, Seed flips and effect decompositions remain unobserved; empty counts are not performance support.',
            'Publication/export/rebuild/remote receipts occur separately and are not certified by this earlier extra review.'],
        artifact_SHA={name: sha(OUT/name) for name in ['final_report.md', 'stage_decision.json', 'all16_arms.json', 'all18_pairs.json',
            'resource_summary.json', 'seed_stratification.json', 'mechanism_account.json', 'paper_algorithm_spec.md',
            'paper_claim_evidence_map.md', 'RESUME.md', 'blocked_current_core.json']},
        reviewer_native_starts=0, reviewer_Optimize=0, reviewer_compiles=0, reviewer_Git=0,
        seconds=time.perf_counter()-tick, human_time='unknown')
    (REVIEW/'extra_review.json').write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    md = ['# R121 independent post-organization extra review', '',
          '**Limited blocked-delivery review: '+output['limited_blocked_delivery_review']+'.**',
          '**Original scientific confirmation: INCOMPLETE / NOT PERFORMED.** The unavailable D1 check is not passed.', '',
          'A separate standard-library implementation checked all 16 fixed role/Seed/method slots and all 18 pairs. Every formal slot is NOT_STARTED with null endpoint/certificate/clocks; every pair is UNEVALUABLE with an unknown severe flag. The stage is BLOCKED, with performance_gate_evaluated=false. Empty counts do not evaluate support or veto thresholds.', '',
          'A new verbal-rule comparison reproduced all 18 historical R120 classifications (13 WIN, 4 LOSS, 1 TIE). Finite synthetic cases checked the frozen absolute/time materiality thresholds, conjunctive severe flags, certificate priority, signed/zero gaps, UNEVALUABLE, contradiction rejection and final stage/veto priority. They are rule checks, not measured R121 results.', '',
          f'Four closed failed-parent fees total {starts} starts and {seconds:.12f} outer seconds. Only one qualification launch remains versus two required. Parent PID/OS-creation and exporter PID/creation receipts were checked; child P/MB persisted PID and affinity do not contain exact OS creation, and their prelaunch markers are not child creation timestamps.', '',
          'Actual P and M-B Seed1 journals, nine-setting readbacks, returned calls, model SHA/types, actual true-G interval/cutoff rows, per-call log spans and complete submitted Start value/type/readback vectors were independently parsed. Both complete physical fleets were recalculated, including all prefix/return loads and complete durations. P original closeout is complete; MB original closeout remains incomplete despite the separate successful overlay. No raw files were changed.', '',
          'The three once-only prospective inputs, safe source SHA/table/865 rows, fixed inventory totals, sum(w), lambda*sum(w) and all 15 R116/R118 overlaps were rechecked. Recorded recipe commit/chronology/hash links and exclusive generation agree; this review does not independently run Git or prove absence of unlogged external measurements.', '',
          '**New D1 full physical endpoint and actual three-row check: UNAVAILABLE.** No H100 or formal D1 CLI was run. No actual installed selector/Start/type/search record exists. All formal performance calculations and Seed sensitivity comparisons are unavailable. The 3-new-problem and 2-known-Seed-block denominators remain planned, with zero measured formal problems.', '',
          'ENS-C stays default; M-B is retained; D0 is not promoted; R119 MB-PC remains stopped. R120 development/old witness material remains historical and is not substituted for this missing confirmation. No STOP/RETAIN/ADVANCE performance outcome is supported.', '', 'Findings:', '']
    md += ['- '+v['id']+': '+v['detail'] for v in findings] if findings else ['- No unresolved reporting correction in the inspected bounded blocked payload.']
    md += ['', 'Limits: zero native starts, Optimize, compilation or Git; no new solution/bound, no historical carrier restoration, and no public rebuild/remote receipt certification in this review. Exact P/MB OS creation is not persisted in raw. This accepts only the bounded blocked delivery, not the original scientific confirmation.', '']
    (REVIEW/'extra_review.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps(dict(limited_review=output['limited_blocked_delivery_review'], scientific_confirmation=output['original_scientific_confirmation'],
                          slots=16, pairs=18, fees=starts, seconds=seconds, unavailable_D1=True, findings=findings, Optimize=0, native_starts=0)))


if __name__ == '__main__':
    run()
