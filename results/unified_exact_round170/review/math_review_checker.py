"""Actual R170 mathematics review by /root/math_review; offline only.

The physical/objective checker below is separate from the producer, C++
verifier, and inherited floating-point physical reader. It uses integer loads
and stock, Fraction target ratios/weights/lambda, and Decimal square roots.
The second part reruns the established *pure saved-evidence* reader to check
actual LP text, actual Start CSV, journals, numerical qualification and cover.
No solver module/API, model creation, H generation, or optimization is used.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext
from datetime import datetime, timezone
import ast
import collections
import csv
import hashlib
import json
import math
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round170'
REVIEW = OUT / 'review'
REVIEWER = '/root/math_review'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    path = Path(path)
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                SHA256=sha(path))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                   allow_nan=False) + '\n', encoding='utf-8')


def local_path(value):
    value = str(value).replace('\\', '/')
    marker = 'results/'
    if marker in value:
        return ROOT / value[value.index(marker):]
    return Path(value)


def load_input(panel):
    path = ROOT / panel['input_path']
    assert sha(path) == panel['input_sha256']
    text = path.read_text(encoding='utf-8-sig')
    head = text.splitlines()[0]
    n, m = map(int, head.split('[')[0].split())
    q = ast.literal_eval(head[head.index('['):])
    assert (n, m, q) == (panel['V'], panel['M'], panel['Q_vector'])
    def vector(name):
        body = re.search(r'^\s*' + name + r'\s*=\s*(\[[^\n]*\])', text, re.M)[1]
        return ast.literal_eval(body)
    initial, target, capacities = map(vector, ['initial', 'target', 'capacities'])
    weights = vector('weights')
    if abs(max(weights[1:])-10) <= 1e-6:
        weights = [v / 10.0 for v in weights]
    assert all(type(v) is int for v in initial + target + capacities + q)
    assert all(v > 0 for v in target[1:])
    assert all(math.isfinite(v) and v >= 0 for v in weights)
    points = vector('points')
    # Exact rational values of the binary64 coordinates/weights actually read.
    # sqrt is evaluated at 80 decimal digits; duration checks retain a 1e-55
    # envelope, vastly smaller than the existing 1e-7 acceptance tolerance.
    xy = [[Fraction.from_float(float(v)) for v in point] for point in points]
    distances = []
    with localcontext() as ctx:
        ctx.prec = 80
        for a in xy:
            row = []
            for b in xy:
                squared = sum((x-y)**2 for x, y in zip(a, b))
                exact_squared = Decimal(squared.numerator) / Decimal(squared.denominator)
                row.append(exact_squared.sqrt() / Decimal('1.5'))
            distances.append(row)
    lam = float(panel['lambda_decimal17'])
    assert lam == panel['lambda']
    assert lam.hex() == panel['lambda_binary64'] == panel['base_lambda_binary64']
    assert (lam * .5).hex() == panel['half_lambda_binary64']
    assert (lam * 2).hex() == panel['double_lambda_binary64']
    return dict(n=n, m=m, Q=q, initial=initial, target=target,
                capacities=capacities, weights=list(map(Fraction.from_float, weights)),
                lambda_exact=Fraction.from_float(lam), distance=distances,
                panel=panel, input=binding(path))


def canonical(routes, m):
    answer = []
    mapping = {r.get('vehicle', r.get('vehicle_id')): r for r in routes}
    assert len(mapping) == len(routes)
    for k in range(m):
        r = mapping.get(k, dict(nodes=[0, 0], operations=[]))
        ops = {o['station']: (o['pickup'], o['drop']) for o in r['operations']}
        answer.append((k, tuple(r['nodes']), tuple((i, *ops[i]) for i in r['nodes'][1:-1])))
    return tuple(answer)


def same_capacity_signature(routes, Q):
    """Only identical-capacity vehicles may exchange full routes.

    The frozen native Start mapper canonicalizes homogeneous vehicle classes
    to satisfy its symmetry rows. H keeps its original vehicle labels. This
    is checked explicitly instead of demanding an invalid label identity.
    """
    groups = collections.defaultdict(list)
    for k, nodes, operations in canonical(routes, len(Q)):
        groups[Q[k]].append((nodes, operations))
    return tuple((capacity, tuple(sorted(fleets))) for capacity, fleets in sorted(groups.items()))


def physical(data, routes):
    n, m = data['n'], data['m']
    y = data['initial'].copy()
    seen, vehicles, fleet = set(), set(), []
    total_return = 0
    with localcontext() as ctx:
        ctx.prec = 80
        for route in routes:
            k = route.get('vehicle', route.get('vehicle_id'))
            assert type(k) is int and 0 <= k < m and k not in vehicles
            vehicles.add(k)
            nodes = route['nodes']
            assert len(nodes) >= 2 and nodes[0] == nodes[-1] == 0
            assert all(type(i) is int and 1 <= i <= n for i in nodes[1:-1])
            ops = {}
            for op in route['operations']:
                i, pick, drop = op['station'], op['pickup'], op['drop']
                assert type(i) is int and type(pick) is type(drop) is int
                assert i not in ops and pick >= 0 and drop >= 0 and bool(pick) != bool(drop)
                ops[i] = (pick, drop)
            assert len(ops) == len(nodes)-2 and set(ops) == set(nodes[1:-1])
            load = pickups = drops = 0
            prefix = []
            for i in nodes[1:-1]:
                assert i not in seen
                seen.add(i)
                pick, drop = ops[i]
                load += pick-drop
                pickups += pick
                drops += drop
                assert 0 <= load <= data['Q'][k]
                prefix.append(load)
                y[i] += drop-pick
                assert 0 <= y[i] <= data['capacities'][i]
            travel = sum((data['distance'][i][j] for i, j in zip(nodes, nodes[1:])), Decimal(0))
            handling = Decimal(data['panel']['pickup_seconds'] * pickups +
                               data['panel']['drop_seconds'] * (drops+load))
            duration = travel+handling
            slack = Decimal(data['panel']['T_seconds'])-duration
            assert slack >= Decimal('-0.0000001')+Decimal('1e-55')
            total_return += load
            fleet.append(dict(vehicle=k, nodes=nodes, prefix_loads=prefix,
                              pickups=pickups, station_drops=drops, return_load=load,
                              travel_seconds_80digits=str(travel),
                              handling_seconds=int(handling), duration_seconds_80digits=str(duration),
                              duration_slack_seconds=float(slack)))
    assert sum(y[1:])+total_return == sum(data['initial'][1:])
    ratios = [Fraction(y[i], data['target'][i]) for i in range(1, n+1)]
    S = sum(ratios)
    H = sum(abs(a-b) for i, a in enumerate(ratios) for b in ratios[i+1:])
    G = H/(n*S) if S else Fraction(0)
    P = sum(w*abs(r-1) for w, r in zip(data['weights'][1:], ratios))
    F = G+data['lambda_exact']*P
    return dict(G=G, P=P, F=F, Y=y, routes=fleet,
                canonical=canonical(routes, m), return_load_sum=total_return,
                missing_vehicles_are_empty=sorted(set(range(m))-vehicles))


def serial_physical(fact):
    return {k: str(v) if isinstance(v, Fraction) else v for k, v in fact.items() if k != 'canonical'}


def check_reported(fact, reported, fields=('G', 'P', 'F')):
    errors = {}
    for key in fields:
        errors[key] = abs(float(fact[key])-reported[key])
        assert errors[key] < 5e-14, (key, errors[key])
    return max(errors.values(), default=0)


def start_fleet(data, values):
    arcs = collections.defaultdict(list)
    for name, v in values.items():
        match = re.fullmatch(r'x_(\d+)_(\d+)_(\d+)', name)
        if match and v > .5:
            assert abs(v-1) <= 1e-7
            k, i, j = map(int, match.groups())
            arcs[k].append((i, j))
    routes = []
    for k in range(data['m']):
        edges = arcs[k]
        if not edges:
            routes.append(dict(vehicle=k, nodes=[0, 0], operations=[]))
            continue
        successor = dict(edges)
        assert len(successor) == len(edges)
        nodes, used = [0], set()
        while True:
            i = nodes[-1]
            assert i in successor and i not in used
            used.add(i)
            nodes.append(successor[i])
            if nodes[-1] == 0:
                break
        assert len(used) == len(edges), 'Start contains disconnected cycle'
        operations = []
        for i in nodes[1:-1]:
            p, d = values[f'p_{k}_{i}'], values[f'd_{k}_{i}']
            assert abs(p-round(p)) <= 1e-7 and abs(d-round(d)) <= 1e-7
            operations.append(dict(station=i, pickup=round(p), drop=round(d)))
        routes.append(dict(vehicle=k, nodes=nodes, operations=operations))
    fact = physical(data, routes)
    maximum_primary_error = 0.
    for i in range(1, data['n']+1):
        r = Fraction(fact['Y'][i], data['target'][i])
        for name, wanted in [(f'Y_{i}', fact['Y'][i]), (f'r_{i}', r), (f'e_{i}', abs(r-1))]:
            maximum_primary_error = max(maximum_primary_error, abs(values[name]-float(wanted)))
        for name, v in values.items():
            match = re.fullmatch(r'state_'+str(i)+r'_(\d+)', name)
            if match:
                assert abs(v-int(int(match[1]) == fact['Y'][i])) <= 1e-7
    by_car = {r['vehicle']: r for r in fact['routes']}
    for k in range(data['m']):
        route = routes[k]
        ops = {o['station']: o for o in route['operations']}
        loads = dict(zip(route['nodes'][1:-1], by_car[k]['prefix_loads']))
        for i in range(1, data['n']+1):
            op = ops.get(i, dict(pickup=0, drop=0))
            for prefix, wanted in [('p', op['pickup']), ('d', op['drop']),
                                   ('z', int(i in ops)), ('load', loads.get(i, 0))]:
                name = f'{prefix}_{k}_{i}'
                maximum_primary_error = max(maximum_primary_error, abs(values[name]-wanted))
    maximum_primary_error = max(maximum_primary_error, abs(values['G']-float(fact['G'])))
    assert maximum_primary_error <= 1e-7
    return fact, maximum_primary_error


def main():
    tick = time.perf_counter()
    matrix = read(OUT/'matrix_frozen.json')
    rows = read(OUT/'complete_arms.json')['rows']
    panels = {p['id']: p for p in read(OUT/'inputs_frozen.json')['roles']}
    data = {role: load_input(panel) for role, panel in panels.items()}
    positions = matrix['positions']
    assert len(positions) == len(rows) == 22
    assert collections.Counter(x['arm'] for x in rows) == dict(B=8, C=8, M=3, P=3)
    expected = [('R163-C20-S', 1, 'BC'), ('R163-C35-U', 1, 'MPCB'),
                ('R163-B35-S', 1, 'CBPM'), ('R163-X35-S', 1, 'PMBC'),
                ('R163-C20-S', 2, 'CB'), ('R163-C35-U', 2, 'BC'),
                ('R163-B35-S', 2, 'CB'), ('R163-X35-S', 2, 'BC')]
    assert [(x['role'], x['Native_Seed'], x['arm']) for x in positions] == [
        (r, s, a) for r, s, arms in expected for a in arms]
    independent = []
    bound_files = {str(OUT/'goal.md'), str(OUT/'matrix_frozen.json'), str(OUT/'inputs_frozen.json'),
                   str(OUT/'complete_arms.json'), str(OUT/'h_path_results.json'),
                   str(OUT/'candidate_manifest.json')}
    h_count, start_count, optimize_count, journal_count = 0, 0, 0, 0
    max_error, min_time_slack = 0., math.inf
    # First independently check original physical fleets and Start semantics.
    for registered, row in zip(positions, rows):
        n, arm, role = registered['position'], registered['arm'], registered['role']
        assert (row['position'], row['arm'], row['role']) == (n, arm, role)
        d = Path(registered['directory'])
        assert d.is_relative_to(OUT/'complete_raw')
        item = data[role]
        result_path = d/'result.json'
        result = read(result_path)
        audit_path = REVIEW/f'complete_audit_{n:02}.json'
        audited = read(audit_path)
        assert audited['passed'] and (audited['position'], audited['research_arm']) == (n, arm)
        assert audited['input'] == item['input']
        bound_files.update(map(str, [result_path, audit_path, d/'invocation.json', d/'completion.json']))
        fact = physical(item, result['routes'])
        max_error = max(max_error, check_reported(fact, dict(G=result['G'], P=result['P'], F=result['objective'])),
                        check_reported(fact, dict(G=row['G'], P=row['P'], F=row['U'])))
        assert fact['Y'] == result['verification']['final_inventories']
        min_time_slack = min(min_time_slack, *(r['duration_slack_seconds'] for r in fact['routes']))
        record = dict(position=n, role=role, arm=arm, final=serial_physical(fact),
                      reported_U=row['U'], reported_L=row['L'], final_result=binding(result_path), H=[])
        events = []
        for p in sorted((d/'journal').glob('event_*.json'), key=lambda x: int(x.stem.split('_')[-1])):
            raw = p.read_bytes()
            event = json.loads(raw)
            fields = p.with_suffix('.commit').read_text().split()
            assert fields[0] == 'NEJ1' and int(fields[1]) == event['sequence']
            assert int(fields[3]) == len(raw) and fields[4] == hashlib.sha256(raw).hexdigest()
            assert 0 <= float(fields[2]) <= registered['cap']
            events.append(event)
        assert [e['sequence'] for e in events] == list(range(1, len(events)+1))
        assert events[0]['kind'] == 'identity'
        ident = events[0]
        assert ident['input_sha256'] == item['input']['SHA256']
        assert (ident['lambda'], ident['T'], ident['pickup_seconds'], ident['drop_seconds']) == (
            panels[role]['lambda'], panels[role]['T_seconds'], 60, 60)
        calls = [e for e in events if e['kind'] == 'call']
        witnesses = [e for e in events if e['kind'] == 'witness']
        assert len(calls) == row['actual_Optimize'] == audited['actual_Optimize']
        journal_count += len(events)
        optimize_count += len(calls)
        for e in calls:
            model, log = local_path(e['model_path']), local_path(e['native_log_path'])
            assert model.is_relative_to(d) and log.is_relative_to(d), 'cross-arm native source'
            assert sha(model) == e['model_sha256']
            bound_files.update(map(str, [model, log]))
            assert e['settings']['Seed'] == registered['Native_Seed']
        if arm != 'P':
            selection_path = d/'primal/selection.json'
            selection = read(selection_path)
            names = ['base'] if arm == 'B' else ['base', arm+'_s1', arm+'_s2']
            assert selection['mode'] == {'B':'off', 'M':'multistart', 'C':'reweight'}[arm]
            assert selection['calls'] == len(names) and not selection['h_panel']
            assert selection['greedy_restored'] and selection['guard_exception_early_return_pass']
            bound_files.add(str(selection_path))
            facts = []
            for name in names:
                folder = d/'primal'/name
                meta = read(folder/'path.json')
                hf = physical(item, read(folder/'fleet.json')['routes'])
                max_error = max(max_error, check_reported(hf, meta))
                mult = .5 if name == 'C_s1' else 2. if name == 'C_s2' else 1.
                wanted_search = panels[role]['lambda'] * mult
                assert meta['search_lambda'] == wanted_search and meta['evaluation_lambda'] == panels[role]['lambda']
                assert meta['effective_seed'] == 20260626+(0 if name == 'base' else int(name[-1]))
                assert abs(float(hf['G']+Fraction.from_float(wanted_search)*hf['P'])-meta['search_F']) < 5e-14
                assert meta['input_SHA256'] == item['input']['SHA256']
                assert meta['fleet_SHA256'] == sha(folder/'fleet.json')
                assert all(meta[k] for k in ['complete', 'valid', 'joint_complete', 'descent_complete', 'closure_complete'])
                assert meta['descent_seeds_completed'] == 25
                orders = (folder/'initial_random_orders.txt').read_bytes().replace(b'\r\n', b'\n')
                assert hashlib.sha256(orders).hexdigest() == meta['initial_random_orders_SHA256']
                lines = orders.decode().splitlines()
                assert len(lines) == 24
                for j, line in enumerate(lines):
                    index, body = line.split(':')
                    order = [int(v) for v in body.split(',') if v]
                    assert int(index) == j and sorted(v for v in order if v > 0) == list(range(1, item['n']+1))
                    assert sum(v <= 0 for v in order) == item['m']-1
                bound_files.update(map(str, [folder/'path.json', folder/'fleet.json', folder/'initial_random_orders.txt']))
                facts.append((name, hf, meta))
                record['H'].append(dict(path=name, effective_seed=meta['effective_seed'],
                                        search_lambda_hex=wanted_search.hex(), evaluation_lambda_hex=panels[role]['lambda'].hex(),
                                        physical=serial_physical(hf), path_metadata=binding(folder/'path.json'),
                                        fleet=binding(folder/'fleet.json')))
                min_time_slack = min(min_time_slack, *(r['duration_slack_seconds'] for r in hf['routes']))
                h_count += 1
            best = facts[0]
            # The exact evaluation confirms the same strict >1e-10 decision as
            # the producer's reported binary64 objective, rather than changing
            # the implementation's tolerance or treating ties as improvements.
            for candidate in facts[1:]:
                if candidate[1]['F'] < best[1]['F']-Fraction('1e-10'):
                    best = candidate
            assert best[0] == selection['selected'] == row['selected_H']
            initial = [w for w in witnesses if w['call'] == 0]
            assert len(initial) == 1
            assert canonical(initial[0]['routes'], item['m']) == best[1]['canonical']
            assert abs(float(best[1]['F'])-row['initial_U']) < 5e-14
            assert abs(float(best[1]['F'])-result['initial_heuristic_UB']) < 5e-14
            assert best[1]['F'] <= facts[0][1]['F']+Fraction('1e-10')
        else:
            assert not (d/'primal').exists()
            assert read(d/'round127_parameters.json')['NumStart_before_optimize'] == 0
            assert not result['gurobi_hga_start_requested']
        record['Start_mappings'] = []
        for start_check in audited['Start_checks']:
            path = ROOT/start_check['start_path']
            assert path.is_relative_to(d)
            meta = read(path)
            vector = path.with_name(path.name[:-5]+'.values.csv')
            with vector.open(encoding='utf-8-sig', newline='') as stream:
                vals = list(csv.DictReader(stream))
            values = {x['variable']: float(x['value']) for x in vals}
            assert len(values) == len(vals)
            assert all(abs(float(x['readback'])-values[x['variable']]) < 1e-7 for x in vals)
            sf, primary_error = start_fleet(item, values)
            call = next(e for e in calls if local_path(e['native_log_path']).name+'.round68.start.json' == path.name)
            assert meta['model_sha256'] == call['model_sha256'] == start_check['model_sha256']
            prior = [w for w in witnesses if w['sequence'] < call['sequence'] and
                     same_capacity_signature(w['routes'], item['Q']) ==
                     same_capacity_signature([dict(vehicle=r['vehicle'], nodes=r['nodes'],
                         operations=[dict(station=i, pickup=values[f'p_{r["vehicle"]}_{i}'].__round__(),
                                          drop=values[f'd_{r["vehicle"]}_{i}'].__round__())
                                     for i in r['nodes'][1:-1]]) for r in sf['routes']], item['Q'])]
            assert prior, 'Start has no own pre-call physical witness'
            assert abs(float(sf['F'])-meta['objective']) < 5e-14
            record['Start_mappings'].append(dict(start=binding(path), vector=binding(vector),
                                                call=call['call'], own_pre_call_witness_sequences=[w['sequence'] for w in prior],
                                                identity_rule='exact routes and operations, allowing permutation only inside identical Q classes',
                                                physical=serial_physical(sf), maximum_primary_mapping_error=primary_error))
            bound_files.update(map(str, [path, vector]))
            start_count += 1
        record['journal_events'] = len(events)
        record['actual_Optimize_in_saved_run'] = len(calls)
        independent.append(record)
        print(json.dumps(dict(physical_review_position=n, H=len(record['H']), Starts=len(record['Start_mappings']))), flush=True)
    assert h_count == 41
    independent_seconds = time.perf_counter()-tick
    # Import only the inspected offline adapter. Import audit guard rejects any
    # late attempt to load a solver Python binding. The adapter imports standard
    # library readers, not C++ verification or production code.
    class NoSolverImport:
        def find_spec(self, fullname, path=None, target=None):
            if any(x in fullname.lower() for x in ['gurobipy', 'cplex', 'round100_gurobi_runtime']):
                raise RuntimeError('solver import forbidden during review: '+fullname)
            return None
    sys.meta_path.insert(0, NoSolverImport())
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT/'scripts'))
    import round170_audit as pure
    pure_seconds = time.perf_counter()
    readbacks = []
    for n, record in enumerate(independent, 1):
        fresh = pure.audit(n)
        old_path = REVIEW/f'complete_audit_{n:02}.json'
        old = read(old_path)
        for key in ['position', 'role', 'research_arm', 'U', 'L', 'certificate', 'certificate_basis',
                    'actual_Optimize', 'LP', 'MIP', 'models', 'Start_checks', 'actual_call_log_bindings',
                    'actual_native_quality']:
            assert fresh[key] == old[key], (n, key, 'saved audit differs from fresh pure readback')
        for contract in fresh['models']:
            model_path = ROOT/contract['model']['path']
            model = pure.core.lp_model(model_path)
            coefficients, constant = model['objective']
            wanted = [('G', 1.)]+[(f'e_{i}', float(data[record['role']]['lambda_exact'])*float(w))
                    for i, w in enumerate(data[record['role']]['weights']) if i and w]
            assert constant == 0. and tuple(sorted(wanted)) == coefficients, (n, 'objective uses nonoriginal lambda')
            assert not contract['no_improver_shortcut_check']['model_scope_issue']
        if record['arm'] == 'P':
            cover = fresh['qualified_cold_bound']
            assert cover['full_original']
            assert sha(ROOT/fresh['models'][0]['model']['path']) == panels[record['role']]['compact_reference']['metadata']['canonical_sha256']
        else:
            cover = fresh['qualified_cover']
            assert cover['complete_coverage'] and cover['covered_gini_upper'] >= min(fresh['U'], (panels[record['role']]['V']-1)/panels[record['role']]['V'])-1e-7
            assert all(not x['future_evidence_used'] for x in fresh['chronological_cover'])
            for proof in cover['scoped_proofs']:
                assert proof['call'] in [x['call'] for x in fresh['actual_Optimize_parameters']]
                if 'native_log' in proof:
                    assert local_path(proof['native_log']).is_relative_to(Path(positions[n-1]['directory']))
        readbacks.append(dict(position=n, U=fresh['U'], L=fresh['L'], certificate=fresh['certificate'],
                              actual_Optimize=fresh['actual_Optimize'], LP=fresh['LP'], MIP=fresh['MIP'],
                              model_scopes_checked=len(fresh['models']), original_objective_coefficients_checked=True,
                              Starts_checked=len(fresh['Start_checks']), saved_audit=binding(old_path),
                              fresh_readonly_audit_seconds=fresh['audit_seconds'],
                              complete_original_cold_domain=record['arm'] == 'P',
                              all_relevant_closed=cover.get('all_relevant_closed', False),
                              qualified_L=cover.get('L'), cross_arm_sources=False))
        print(json.dumps(dict(pure_readback_position=n, U=fresh['U'], L=fresh['L'], certificate=fresh['certificate'])), flush=True)
    pure_seconds = time.perf_counter()-pure_seconds
    for name in ['src/Round169Primal.inc', 'src/main.cpp', 'src/Parser.cpp', 'src/Evaluator.cpp', 'src/Result.cpp',
                 'include/PhysicalDurationTolerance.hpp', 'scripts/round170_audit.py',
                 'results/unified_exact_round169/review/round169_complete_audit.py', 'scripts/round108_reader.py',
                 'scripts/round107_reader.py', 'scripts/round99_pure_start_audit.py', 'scripts/round111_seed_audit.py',
                 'scripts/round135_read.py', 'scripts/round118_call_logs.py', 'scripts/compare_round112_startup.py']:
        bound_files.add(str(ROOT/name))
    # Every bound file is read anew before the review receipt is sealed.
    bindings = [binding(Path(p)) for p in sorted(bound_files)]
    clock = read(REVIEW/'math_review_clock.json')
    conclusion = dict(
        schema='round170-independent-mathematics-review-v1', status='PASS', reviewer_canonical_id=REVIEWER,
        UTC=datetime.now(timezone.utc).isoformat(), findings=[], unresolved_findings=[],
        scope=['22 final fleets: original integer physical feasibility and exact rational G/P/F',
               '41 independently paid H terminal fleets: full own-H, seeds, weight multipliers, original reevaluation and base-first selection',
               'submitted Start CSVs decoded to physical fleets and matched to same-run pre-call witnesses',
               'all actual model objectives, scoped true-G/cutoff rows, original state/service/link contracts and numerical prerequisites',
               'all per-run immutable journal commits and actual native log/model/return bindings',
               'qualified full original cover or cold compact L; no cross-arm certificate splicing',
               'C169 correctness inheritance and absence of terminal U/L/gap/time dominance'],
        reviewed_bindings=bindings, final_fleets=22, H_terminal_fleets=h_count,
        actual_submitted_Starts=start_count, saved_run_actual_Optimize=optimize_count,
        journal_events=journal_count, maximum_reported_objective_difference=max_error,
        minimum_route_duration_slack_seconds=min_time_slack,
        arithmetic='integer stocks/prefix loads; exact Fraction target ratios, actual binary64 weights/lambda; Decimal80 loaded-coordinate travel',
        physical_checker_independent_of_Cpp_and_inherited_physical_reader=True,
        no_cross_arm_sources=True,
        inherited_proof_reader_reexecuted_after_independent_physical_checks=True,
        mathematical_interpretation={
            'G':'sum_{i<j}|Y_i/D_i-Y_j/D_j| /(n sum_i Y_i/D_i), with G=0 at zero sum',
            'P':'sum_i w_i |Y_i/D_i-1| using original loaded nonnegative w',
            'F':'G + original binary64 lambda * P; search weights never enter the exact layer',
            'correctness':'Only original-verified physical UB/Start is passed. Inclusive F<=own UB and true-G cover retain all potential original-objective improvers. C++ guard restores global greedy lambda/scaling.',
            'cold_P':'cold full original compact matrix matches inherited qualified reference; no user Start/H; per-run original objective and native bound qualified',
            'dominance_boundary':'Keeping base H guarantees initialization U no worse under the original selection rule. Extra work and changed UB/Start/search do not guarantee final U, L, gap, certification or time dominance under one process cap.',
            'finite_precision':'CERT qualification uses the inherited 1e-7 numerical tolerance, not a new exact rational proof. Raw signed last-bit gaps and bounds are retained.'},
        independent_physical_Start_seconds=independent_seconds,
        fresh_pure_readback_seconds=pure_seconds,
        checker_seconds=time.perf_counter()-tick,
        review_seconds=time.time()-clock['start_epoch'],
        review_seconds_scope='measured wall interval beginning at math_review_clock.json after initial unmetered orientation; parent task wall accounting includes orientation',
        Optimize=0, H_calls=0, solver_API_calls=0, solver_models_created=0,
        independent_fleet_results=independent, pure_readback_results=readbacks,
        checker=binding(Path(__file__)))
    write(REVIEW/'math_review_initial.json', conclusion)
    # No mathematical findings require source/data corrections; final receipt
    # independently rebinds every reviewed artifact and checker after reread.
    for item in bindings:
        assert binding(ROOT/item['path']) == item, 'reviewed artifact changed before finalization'
    conclusion = dict(conclusion, schema='round170-independent-mathematics-review-final-v1',
                      initial_review=binding(REVIEW/'math_review_initial.json'),
                      final_readback_UTC=datetime.now(timezone.utc).isoformat(),
                      review_seconds=time.time()-clock['start_epoch'])
    write(REVIEW/'math_review_final.json', conclusion)
    print(json.dumps({k: conclusion[k] for k in ['status', 'final_fleets', 'H_terminal_fleets',
          'actual_submitted_Starts', 'saved_run_actual_Optimize', 'journal_events',
          'maximum_reported_objective_difference', 'minimum_route_duration_slack_seconds',
          'checker_seconds', 'review_seconds', 'Optimize', 'H_calls']}), flush=True)


if __name__ == '__main__':
    main()
