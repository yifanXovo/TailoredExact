"""Independent standard-library, zero-native R121 pre-contract review.

This reviewer never imports the campaign, generator, Gurobi, or production
modules; it writes only its two review artifacts.  Re-deriving expected input
values in memory is not another research draw and creates no input file.
"""
from pathlib import Path
from fractions import Fraction
import argparse
import ast
import copy
import csv
import datetime
import hashlib
import json
import math
import re
import statistics
import time
import types

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round121'
OLD = Path('C:/Users/Administrator/.codex/worktrees/round120-native-proof-disjunction/ExactEBRP')
RAW = 'd4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8'
TABLE = 'd982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa'
FAMILY = 'round121-frozen-d1-confirmation-v1|source_sha256=' + RAW
EXPECTED = [
    ('F2', 20, 2, [30, 30], 3600, 1200, 1, ['MB-D0', 'P-GRB', 'MB-D1', 'M-B']),
    ('Q30-C2-B', 30, 3, [20, 25, 30], 7200, 1800, 0, ['P-GRB', 'MB-D1', 'M-B']),
    ('R98-C2', 30, 3, [20, 25, 30], 7200, 1800, 1, ['M-B', 'P-GRB', 'MB-D1']),
    ('Q40-R2-S', 40, 4, [20, 25, 35, 40], 10800, 3600, 0, ['MB-D1', 'M-B', 'P-GRB']),
    ('Q50-C2-U', 50, 4, [30, 30, 30, 30], 10800, 3600, 0, ['M-B', 'P-GRB', 'MB-D1']),
]
H_SOURCES = OUT / 'review/h_reselection_sources'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def order(indices, material):
    return sorted(indices, key=lambda i: (hashlib.sha256(f'{material}|{i}'.encode()).digest(), i))


def unit(material):
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], 'big') / float((1 << 64) - 1)


def coordinates(row):
    return float(row['utm18n_easting_m']), float(row['utm18n_northing_m'])


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def independent_selection(rows, role):
    """Separate implementation of original anchor, tie, and coverage rules."""
    v = role['V']
    ids = list(range(len(rows)))
    points = [coordinates(r) for r in rows]
    anchors = [order(ids, f'{FAMILY}|geographic-anchor-set|V={v}')[0]]
    for _ in range(3):
        anchors.append(max((i for i in ids if i not in anchors),
                           key=lambda i: (min(distance(points[i], points[a]) for a in anchors), -i)))
    slot = (0 if role['geometry'] == 'compact' else 2) + role['replicate'] - 1
    anchor = anchors[slot]
    nearest = sorted(ids, key=lambda i: (distance(points[i], points[anchor]), i))
    if role['geometry'] == 'compact':
        chosen = nearest[:v]
    else:
        pool = nearest[:2 * v]
        chosen = [anchor]
        while len(chosen) < v:
            chosen.append(max((i for i in pool if i not in chosen),
                              key=lambda i: (min(distance(points[i], points[j]) for j in chosen),
                                             -distance(points[i], points[anchor]), -i)))
    depot = [round(statistics.fmean(points[i][j] for i in chosen), 3) for j in range(2)]
    return chosen, depot, anchors


def independent_landscape(rows, role, chosen):
    caps = [int(rows[i]['capacity']) for i in chosen]
    sid = role['selection_id']
    target = [max(1, min(c, math.floor(c * (.44 + .12 * unit(
        f'{FAMILY}|target-profile|{sid}|row={i}')) + .5))) for c, i in zip(caps, chosen)]
    delta = max(role['V'], math.floor(.12 * sum(target) + .5))
    regime = role['inventory']
    desired = (sum(target) if regime == 'balanced' else max(0, sum(target) - delta)
               if regime == 'shortage' else min(sum(caps), sum(target) + delta))
    scale = .18 if regime == 'balanced' else .30
    material = f'{FAMILY}|inventory|{sid}|{regime}'
    idx_order = order(range(role['V']), material)
    initial = target.copy()
    for rank, i in enumerate(idx_order):
        bump = max(1, math.floor(scale * caps[i] + .5))
        initial[i] = min(caps[i], max(0, target[i] + (bump if rank % 2 == 0 else -bump)))
    before = initial.copy()
    # One-unit cyclic total correction, in the fixed hash order.
    while sum(initial) != desired:
        step = 1 if sum(initial) < desired else -1
        progress = False
        for i in idx_order:
            if (step > 0 and initial[i] < caps[i]) or (step < 0 and initial[i] > 0):
                initial[i] += step
                progress = True
                if sum(initial) == desired:
                    break
        assert progress
    corrected = initial.copy()
    sign_repair_used = not (any(b > d for b, d in zip(initial, target))
                           and any(b < d for b, d in zip(initial, target)))
    if sign_repair_used:
        repair_order = order(range(role['V']), material + '|sign-repair')
        receiver = next((i for i in repair_order if initial[i] < caps[i]), None)
        donor = next((i for i in reversed(repair_order) if initial[i] > 0 and i != receiver), None)
        assert receiver is not None and donor is not None
        move = min(caps[receiver] - initial[receiver], initial[donor],
                   max(1, target[receiver] + 1 - initial[receiver], initial[donor] - target[donor] + 1))
        initial[receiver] += move
        initial[donor] -= move
        if not (any(b > d for b, d in zip(initial, target))
                and any(b < d for b, d in zip(initial, target))):
            found = False
            for receiver in repair_order:
                for donor in reversed(repair_order):
                    if receiver == donor:
                        continue
                    move = max(1, target[receiver] + 1 - initial[receiver], initial[donor] - target[donor] + 1)
                    if initial[receiver] + move <= caps[receiver] and initial[donor] - move >= 0:
                        initial[receiver] += move
                        initial[donor] -= move
                        found = True
                        break
                if found:
                    break
            assert found
    weights0 = [round(max(.1, (d / max(target)) ** 2), 6) for d in target]
    weights = [round(w / max(weights0), 6) for w in weights0]
    minimum = [round(.10 + .40 * d / c, 4) for d, c in zip(target, caps)]
    return dict(capacities=caps, initial=initial, target=target, weights=weights, min_ratio=minimum,
                delta=delta, desired_total=desired, initial_before_total_correction=before,
                initial_after_total_correction=corrected, sign_repair_used=sign_repair_used)


def parse_input(path):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    v, m, qs = lines[0].split(maxsplit=2)
    values = {k.strip(): ast.literal_eval(v.strip()) for k, v in (line.split('=', 1) for line in lines[1:])}
    return int(v), int(m), ast.literal_eval(qs), values


def residual(matrix, point):
    maximum = 0.
    worst = None
    for row, (rhs, sense) in enumerate(zip(matrix['rhs'], matrix['senses'])):
        lhs = math.fsum(matrix['coefficients'][j] * point[matrix['column_indices'][j]]
                        for j in range(matrix['row_starts'][row], matrix['row_starts'][row + 1]))
        violation = abs(lhs - rhs) if sense == '=' else max(0., lhs - rhs) if sense == '<' else max(0., rhs - lhs)
        if violation > maximum:
            maximum, worst = violation, row
    bounds = max([0.] + [max(lo - x, x - hi) for lo, x, hi in zip(matrix['lower_bounds'], point, matrix['upper_bounds'])])
    return dict(maximum_row_violation=maximum, worst_row=worst, maximum_bound_violation=bounds)


def q(value):
    return Fraction.from_float(float(value))


def row_terms(matrix, row):
    return {matrix['column_indices'][j]: matrix['coefficients'][j]
            for j in range(matrix['row_starts'][row], matrix['row_starts'][row + 1])}


def exact_activity_without_h(matrix, row, point, h):
    terms = row_terms(matrix, row)
    return sum((q(c) * q(point[i]) for i, c in terms.items() if i != h), Fraction()), q(terms.get(h, 0.))


def add_interval(lo, hi, coeff, rhs, sense):
    if coeff == 0:
        assert (rhs == 0 if sense == '=' else rhs >= 0 if sense == '<' else rhs <= 0)
        return lo, hi
    endpoint = rhs / coeff
    if sense == '=':
        return max(lo, endpoint), min(hi, endpoint)
    upper = (sense == '<' and coeff > 0) or (sense == '>' and coeff < 0)
    return (lo, min(hi, endpoint)) if upper else (max(lo, endpoint), hi)


def snapshot_h_sources():
    """Copy just the two saved points/base matrices and extract actual D1 rows.

    No historical carrier, executable, native log, other LP point, or MPS is
    restored.  The complete D1 export is read once to verify all preceding
    rows equal the D0 base, then only the actual three changed rows are saved.
    """
    H_SOURCES.mkdir(parents=True, exist_ok=True)
    summaries = []
    for role in ['F2', 'R98-C2']:
        source = OLD / 'results/unified_exact_round120/qualification/diagnostics' / role
        base_path = source / 'D0_max_conditional_violation/full_primal_and_original_matrix.json'
        d1_path = source / 'D1_original_objective/full_primal_and_original_matrix.json'
        record_path = source / 'D0_max_conditional_violation/record.json'
        p, d1 = read(base_path), read(d1_path)
        assert p['names'] == d1['names'] and len(p['rhs']) == len(d1['rhs'])
        for key in ['original_objective', 'original_objective_constant', 'lower_bounds', 'upper_bounds']:
            assert p[key] == d1[key]
        nrows = len(p['rhs'])
        for r in range(nrows - 3):
            assert p['rhs'][r] == d1['rhs'][r] and p['senses'][r] == d1['senses'][r]
            assert row_terms(p, r) == row_terms(d1, r)
        dest = H_SOURCES / role
        dest.mkdir(exist_ok=True)
        for original, name in [(base_path, 'saved_D0_witness_and_matrix.json'), (record_path, 'saved_D0_witness_record.json')]:
            target = dest / name
            if target.exists():
                assert sha(target) == sha(original)
            else:
                target.write_bytes(original.read_bytes())
        extracted = dict(schema='r121-minimal-old-h-source-v1', role=role,
                         source_D0_path=str(base_path), source_D0_SHA=sha(base_path),
                         source_D1_path=str(d1_path), source_D1_SHA=sha(d1_path),
                         source_D0_record_path=str(record_path), source_D0_record_SHA=sha(record_path),
                         source_D1_record=read(source / 'D1_original_objective/record.json'),
                         source_D1_record_SHA=sha(source / 'D1_original_objective/record.json'),
                         all_preceding_rows_equal_independently_checked=nrows - 3,
                         names_bounds_and_full_objective_with_ObjCon_equal=True,
                         rows=[dict(index=r, rhs=d1['rhs'][r], sense=d1['senses'][r],
                                    terms=[[i, c] for i, c in row_terms(d1, r).items()])
                               for r in range(nrows - 3, nrows)],
                         no_original_variable_primal_replaced=True, native_starts=0, Optimize=0)
        target = dest / 'actual_D1_three_rows_and_provenance.json'
        if target.exists():
            assert read(target) == extracted
        else:
            target.write_text(json.dumps(extracted, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        summaries.append(dict(role=role, saved_D0_SHA=sha(dest / 'saved_D0_witness_and_matrix.json'),
                              actual_D1_rows_SHA=sha(target), copied_full_witnesses=1,
                              copied_other_LP_primals=0, copied_MPS=0))
    print(json.dumps(dict(snapshot='two_existing_points_and_base_matrices_only', roles=summaries, Optimize=0, native_starts=0)))


def saved_h_data(role):
    local = H_SOURCES / role
    ppath = local / 'saved_D0_witness_and_matrix.json'
    rows_path = local / 'actual_D1_three_rows_and_provenance.json'
    if ppath.is_file() and rows_path.is_file():
        p = read(ppath)
        meta = read(rows_path)
        assert sha(ppath) == meta['source_D0_SHA']
        assert sha(local / 'saved_D0_witness_record.json') == meta['source_D0_record_SHA']
        nrows = len(p['rhs'])
        assert meta['all_preceding_rows_equal_independently_checked'] == nrows - 3
        d1 = copy.deepcopy(p)
        d1['primal'] = []  # No unneeded second D1 LP point is published.
        d1['rhs'] = p['rhs'][:nrows - 3]
        d1['senses'] = p['senses'][:nrows - 3]
        cut = p['row_starts'][nrows - 3]
        d1['row_starts'] = p['row_starts'][:nrows - 2]
        d1['column_indices'] = p['column_indices'][:cut]
        d1['coefficients'] = p['coefficients'][:cut]
        for row in meta['rows']:
            assert row['index'] == len(d1['rhs'])
            d1['rhs'].append(row['rhs'])
            d1['senses'] += row['sense']
            d1['column_indices'].extend(i for i, _ in row['terms'])
            d1['coefficients'].extend(c for _, c in row['terms'])
            d1['row_starts'].append(len(d1['coefficients']))
        return p, d1, read(local / 'saved_D0_witness_record.json'), dict(
            mode='local_minimal_safe_snapshot', witness_path=ppath.relative_to(ROOT).as_posix(),
            actual_D1_rows_path=rows_path.relative_to(ROOT).as_posix(),
            witness_SHA=sha(ppath), actual_D1_rows_SHA=sha(rows_path),
            original_paths_and_hashes={k: v for k, v in meta.items() if k.startswith('source_')},
            full_D1_reconstruction='unchanged complete D0 original rows and actual extracted final three rows')
    directory = OLD / 'results/unified_exact_round120/qualification/diagnostics' / role
    ppath = directory / 'D0_max_conditional_violation/full_primal_and_original_matrix.json'
    d1path = directory / 'D1_original_objective/full_primal_and_original_matrix.json'
    if not ppath.is_file() or not d1path.is_file():
        return None
    return read(ppath), read(d1path), read(directory / 'D0_max_conditional_violation/record.json'), dict(
        mode='original_worktree_read_only', witness_path=str(ppath), actual_D1_matrix_path=str(d1path),
        witness_SHA=sha(ppath), actual_D1_matrix_SHA=sha(d1path))


def old_h_review(role):
    data = saved_h_data(role)
    if data is None:
        return dict(role=role, result='UNKNOWN_MISSING_SAVED_PRIMAL', no_recovery_or_solver_requested=True)
    p, d1, witness_record, provenance = data
    point = p['primal']
    assert point and p['names'] == d1['names']
    assert p['original_objective'] == d1['original_objective']
    assert p['original_objective_constant'] == d1['original_objective_constant']
    assert p['lower_bounds'] == d1['lower_bounds'] and p['upper_bounds'] == d1['upper_bounds']
    assert len(p['rhs']) == len(d1['rhs']) == witness_record['rows']
    nrows = len(d1['rhs'])
    unchanged_rows = 0
    for row in range(nrows - 3):
        assert p['rhs'][row] == d1['rhs'][row] and p['senses'][row] == d1['senses'][row]
        assert row_terms(p, row) == row_terms(d1, row)
        unchanged_rows += 1
    h = p['names'].index('r120_h')
    g = p['names'].index('G')
    hrows = [r for r in range(nrows) if h in row_terms(d1, r)]
    assert hrows == list(range(nrows - 3, nrows))
    old_check = residual(p, point)
    assert old_check['maximum_row_violation'] <= 1e-7 and old_check['maximum_bound_violation'] <= 1e-7
    lo, hi = q(d1['lower_bounds'][h]), q(d1['upper_bounds'][h])
    serialized_rows = []
    for row in hrows[:2]:
        base, coeff = exact_activity_without_h(d1, row, point, h)
        lo, hi = add_interval(lo, hi, coeff, q(d1['rhs'][row]) - base, d1['senses'][row])
    assert lo <= hi
    frow = nrows - 1
    fterms = row_terms(d1, frow)
    for i, c in enumerate(p['original_objective']):
        if i != h:
            assert fterms.get(i, 0.) == c
    # Full objective expression includes saved ObjCon, even when it is zero.
    const = q(p['original_objective_constant'])
    f = const + sum((q(c) * q(x) for c, x in zip(p['original_objective'], point)), Fraction())
    f_hcoeff = q(fterms[h])
    selected = lo if f_hcoeff <= 0 else hi
    required = const + q(d1['rhs'][frow]) - f_hcoeff * selected
    repaired = point.copy()
    repaired[h] = float(selected)
    repaired_check = residual(d1, repaired)
    old_d1 = residual(d1, point)
    assert abs(old_d1['maximum_row_violation'] - witness_record['actual_D1_row_violation']) <= 1e-7
    assert repaired_check['maximum_row_violation'] <= 1e-7 and repaired_check['maximum_bound_violation'] <= 1e-7
    for row in hrows:
        terms = row_terms(d1, row)
        serialized_rows.append(dict(row_zero_based=row, sense=d1['senses'][row], rhs=d1['rhs'][row],
                                    coefficients_by_name={p['names'][i]: c for i, c in terms.items()}))
    return dict(role=role, result='SAVED_POINT_EXTENDS_TO_D1_BY_H_RESELECTION',
                saved_source_provenance=provenance,
                original_columns=len(point), original_rows=nrows, original_D0_nonzeros=len(p['coefficients']),
                original_D1_nonzeros=len(d1['coefficients']), unchanged_rows_before_selector=unchanged_rows,
                rows_containing_h=hrows, actual_three_rows=serialized_rows,
                original_h=point[h], original_g=point[g], full_objective_with_ObjCon=float(f),
                actual_ObjCon=float(const), actual_link_h_interval=[float(lo), float(hi)],
                selected_h=float(selected), actual_minimum_required_objective=float(required),
                objective_slack_at_selected_h=float(f - required),
                original_D0_full_residual=old_check, original_D1_full_residual=old_d1,
                repaired_D1_full_residual=repaired_check, evidence_tolerance=1e-7,
                all_original_coordinates_other_than_h_unchanged=True,
                calculation='exact Fraction arithmetic on saved binary64 coefficients for interval/ObjCon; independent fsum full-row and bound residuals',
                scope='Two saved fractional complete-LP witness points only. This neither proves strict original-variable projection shrinkage nor cancels R120 extended-space nonredundancy or performance evidence.',
                Optimize=0, native_starts=0)


def definitions(path, names, namespace):
    """Compile only selected pure function definitions, never module imports."""
    text = Path(path).read_text(encoding='utf-8-sig')
    tree = ast.parse(text)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path) + '::review_in_memory', 'exec'), namespace)
    return namespace


def independent_pair(candidate, control):
    """Separate small decision implementation from the frozen verbal rule."""
    c, p = candidate, control
    cc, pc = bool(c['certificate']), bool(p['certificate'])
    if cc != pc:
        return ('WIN', False) if cc else ('LOSS', True)
    if cc:
        improvement = p['complete_seconds'] - c['complete_seconds']
        material = max(30., .10 * p['complete_seconds'])
        kind = 'WIN' if improvement >= material else 'LOSS' if -improvement >= material else 'TIE'
        severe = c['complete_seconds'] >= 2 * p['complete_seconds'] and -improvement >= 120
        return kind, severe
    if not c['numbers_qualified'] or not p['numbers_qualified']:
        return 'UNEVALUABLE', False
    du, dg = p['U'] - c['U'], p['gap'] - c['gap']
    better = du >= max(.001, .01 * abs(p['U'])) or dg >= max(.001, .10 * abs(p['gap']))
    worse = -du >= max(.001, .01 * abs(p['U'])) or -dg >= max(.001, .10 * abs(p['gap']))
    kind = 'MIXED' if better and worse else 'WIN' if better else 'LOSS' if worse else 'TIE'
    severe = -du >= max(.001, .05 * abs(p['U'])) and -dg >= max(.005, .25 * abs(p['gap']))
    return kind, severe


def in_memory_fixtures():
    checks = []
    evidence_path = ROOT / 'scripts/round121_evidence.py'
    journal_text = (ROOT / 'scripts/round114_audit.py').read_text(encoding='utf-8-sig')
    journal_node = next(n for n in ast.parse(journal_text).body if isinstance(n, ast.FunctionDef) and n.name == 'journal')
    journal_source = ast.get_source_segment(journal_text, journal_node)
    observations = []

    class MemoryPath:
        def __init__(self, name='memory'):
            self.name = name
        def __truediv__(self, name):
            return MemoryPath(self.name + '/' + str(name))
        def glob(self, pattern):
            assert pattern == 'event_*.commit'
            return list(range(len(observations)))

    def receipt(path, first, cap):
        index = int(re.search(r'event_(\d+)\.commit$', path.name)[1]) - 1
        return copy.deepcopy(observations[index])

    settings = dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1, MIPGap=0, MIPGapAbs=0,
                    FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    audit_namespace = types.SimpleNamespace(journal_receipts=types.SimpleNamespace(receipt=receipt),
                                           core=types.SimpleNamespace(portable=lambda root, path: path),
                                           sha=lambda path: 'MEMORY_MODEL', math=math, FAILURES=set())
    scope = dict(__file__=str(evidence_path), _JOURNAL_SOURCE=journal_source, audit=audit_namespace,
                 computed=types.SimpleNamespace(expected=lambda seed: dict(settings, Seed=seed)))
    definitions(evidence_path, ['_compile', '_raw_journal'], scope)
    panel = dict(V=2, M=1, input_sha256='MEMORY_INPUT', **{'lambda': .15},
                 T_seconds=120, pickup_seconds=60, drop_seconds=60,
                 reference=dict(canonical_sha256='MEMORY_MODEL'))

    def make_records(seed, raw_guard, disposition='returned'):
        payloads = [dict(kind='identity', input_sha256='MEMORY_INPUT', V=2, M=1, **{'lambda': .15},
                         T=120, pickup_seconds=60, drop_seconds=60, analytical_full_domain_lower_bound=0),
                    dict(kind='call', call=1, settings=dict(settings, Seed=seed), model_path='MEMORY',
                         model_sha256='MEMORY_MODEL', gmax=.5, lower_g=0., upper_g=.5,
                         full_original=True, native_preconditions=raw_guard)]
        if disposition == 'returned':
            payloads.append(dict(kind='returned', call=1, return_code=0))
        elif disposition == 'not_started':
            payloads.append(dict(kind='not_started', call=1, actual_Optimize=False,
                                 reason='no_remaining_original_work_window'))
        return [dict(payload=dict(sequence=i, **p), first_observed_seconds=float(i), effective_available_seconds=float(i))
                for i, p in enumerate(payloads, 1)]

    for seed, guard in [(0, True), (1, False)]:
        observations[:] = make_records(seed, guard)
        original = copy.deepcopy(observations)
        result = scope['_raw_journal'](None, dict(panel=panel, cap_seconds=120, seed=seed), MemoryPath(), observations)
        assert result['returned_ids'] == {1} and result['started'] == 1 and observations == original
        observations[:] = make_records(seed, not guard)
        try:
            scope['_raw_journal'](None, dict(panel=panel, cap_seconds=120, seed=seed), MemoryPath(), observations)
        except AssertionError:
            pass
        else:
            raise AssertionError('wrong actual raw guard accepted')
    checks.append('actual_R121_raw_journal_transform_accepts_only_Seed0_true_and_Seed1_false_without_mutation')
    observations[:] = make_records(0, False)
    try:
        scope['_raw_journal'](None, dict(panel=panel, cap_seconds=120, seed=1), MemoryPath(), observations)
    except AssertionError:
        pass
    else:
        raise AssertionError('wrong actual Seed settings accepted')
    checks.append('actual_R121_journal_rejects_wrong_Seed_settings')
    for disposition in ['not_started', 'unreturned']:
        observations[:] = make_records(1, False, disposition)
        result = scope['_raw_journal'](None, dict(panel=panel, cap_seconds=120, seed=1), MemoryPath(), observations)
        if disposition == 'not_started':
            assert result['not_started_ids'] == {1} and result['started'] == 0 and not result['unreturned_ids']
        else:
            assert result['unreturned_ids'] == {1} and result['not_started_ids'] == set()
    checks.append('actual_R121_journal_explicit_not_started_and_unknown_disposition_remain_distinct')
    projection = definitions(ROOT / 'scripts/round109_seed_scope.py', ['projected_records', 'projected_journal'], {'copy': copy})
    raw = make_records(1, False)
    raw.append(dict(payload=dict(kind='bound', call=1, global_available=False, global_bound=None)))
    before = copy.deepcopy(raw)
    projected = projection['projected_records'](raw, dict(recovered_calls=[dict(call=1)]), legacy_seed=True)
    assert raw == before and projected[1]['payload']['native_preconditions'] is True
    assert projected[1]['payload']['raw_native_preconditions'] is False
    assert raw[1]['payload']['settings']['Seed'] == 1 and projected[1]['payload']['settings']['Seed'] == 0
    assert projected[-1]['payload'] == raw[-1]['payload']
    checks.append('legacy_projection_deepcopies_raw_and_never_promotes_global_available_or_global_bound')
    param_source = dict(seed_audit=types.SimpleNamespace(_parameters=lambda result, **kwargs: dict(projected_requested=result['gurobi_seed_requested'])))
    definitions(evidence_path, ['_parameters'], param_source)
    parameter = dict(gurobi_seed_requested=1, gurobi_seed_effective=1,
                     gurobi_seed_set_return_code=0, gurobi_seed_get_return_code=0)
    before = parameter.copy()
    output = param_source['_parameters'](parameter, seed=1, require_call=True, arm='P-GRB')
    assert parameter == before and output['seed']['effective'] == 1 and output['projected_requested'] == 0
    for key in ['gurobi_seed_requested', 'gurobi_seed_effective', 'gurobi_seed_set_return_code', 'gurobi_seed_get_return_code']:
        wrong = dict(parameter)
        wrong[key] = 0 if key in ['gurobi_seed_requested', 'gurobi_seed_effective'] else 1
        try:
            param_source['_parameters'](wrong, seed=1, require_call=True, arm='P-GRB')
        except AssertionError:
            pass
        else:
            raise AssertionError('wrong actual Seed return/readback accepted')
    checks.append('actual_R121_parameter_adapter_checks_both_Seed_values_and_both_return_codes_before_projection')
    log_scope = definitions(ROOT / 'scripts/round118_call_logs.py', ['segments'], {'re': re})
    log = b'Gurobi Optimizer version 13.0.2\nOptimize a model with 1 rows, 1 columns\nTime limit reached\nExplored 0 nodes\nBest objective 1, best bound 0, gap 100%\n'
    spans = log_scope['segments'](log + log)
    assert spans == [(0, len(log)), (len(log), 2 * len(log))]
    try:
        log_scope['segments'](log + log.replace(b'Gurobi Optimizer version 13.0.2\n', b''))
    except AssertionError:
        pass
    else:
        raise AssertionError('missing second call preamble accepted')
    checks.append('same_log_two_normal_time_limit_calls_have_distinct_byte_spans_and_missing_preamble_rejects')
    claim_scope = definitions(ROOT / 'scripts/round114_claims.py', ['in_domain', 'reconcile'], {'math': math, 'TOL': 1e-7})
    claim = dict(arm='MB-D1', call=1, sequence=2, model_SHA='MEMORY', input_SHA='MEMORY',
                 scope=dict(full_original=False, lower_g=0., upper_g=.5, cutoff=1.),
                 value=.4, source='MEMORY', available=2., domain_verified=True, dependencies=[1])
    witness = dict(arm='M-B', call=0, sequence=1, G=.2, F=.3, input_SHA='MEMORY',
                   physical_verified=True, source='MEMORY', available=1.)
    damage = claim_scope['reconcile']([claim], [witness])
    assert damage['damaged_calls'] == [dict(arm='MB-D1', call=1)]
    assert damage['rejections'][0]['call_rejected_as_a_whole']
    assert 'dependent_cover' in damage['rejections'][0]['rejected_native_kinds']
    assert not claim_scope['reconcile']([claim], [dict(witness, G=.7)])['rejections']
    checks.append('same_domain_counterexample_revokes_whole_D1_call_and_dependent_cover_outside_domain_does_not_transfer')
    decision = definitions(ROOT / 'scripts/round121_decision.py', ['decide'], {})['decide']
    values = []
    f2pairs = [('MB-D1', 'M-B'), ('MB-D1', 'P-GRB'), ('MB-D1', 'MB-D0'), ('MB-D0', 'M-B'), ('MB-D0', 'P-GRB'), ('M-B', 'P-GRB')]
    for number, role in enumerate(EXPECTED, 1):
        values.append(dict(group=dict(number=number, seed=role[6]),
                           arms=[dict(arm=a, formal_protocol_qualified=True, actually_executed=True, certificate=False) for a in role[7]],
                           pairs=[dict(candidate=c, control=p, classification='WIN', evaluable=True, severe_regression=False)
                                  for c, p in f2pairs if number == 1] if number == 1 else
                                 [dict(candidate=c, control=p, classification='WIN', evaluable=True, severe_regression=False)
                                  for c, p in [('MB-D1', 'M-B'), ('MB-D1', 'P-GRB'), ('M-B', 'P-GRB')]],
                           mechanism=[dict(arm='MB-D1', installed=1, actual_extended_Optimize=1)]))
    assert decision(values, True)['stage'] == 'ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK'
    assert decision(values, True, proof_risk=True, blockers=['MEMORY'])['stage'] == 'PROOF_RELIABILITY_PRIORITY'
    assert decision(values, True, blockers=['MEMORY'])['stage'] == 'BLOCKED'
    incomplete = copy.deepcopy(values)
    incomplete[0]['arms'][0]['actually_executed'] = False
    assert decision(incomplete, True)['stage'] == 'BLOCKED'
    for which in ['severe', 'new_losses', 'certificate_loss']:
        changed = copy.deepcopy(values)
        if which == 'severe':
            next(p for p in changed[0]['pairs'] if p['candidate'] == 'MB-D1' and p['control'] == 'P-GRB')['severe_regression'] = True
        elif which == 'new_losses':
            for n in [1, 3]:
                next(p for p in changed[n]['pairs'] if p['candidate'] == 'MB-D1' and p['control'] == 'P-GRB')['classification'] = 'LOSS'
        else:
            next(a for a in changed[0]['arms'] if a['arm'] == 'M-B')['certificate'] = True
        assert decision(changed, True)['stage'] == 'STOP_FROZEN_D1_CONFIRMATION'
    changed = copy.deepcopy(values)
    for value in changed:
        value['mechanism'][0]['installed'] = 0
    assert decision(changed, True)['stage'] == 'RETAIN_D1_AS_DEVELOPMENT_COMPONENT'
    assert decision(values, False)['stage'] == 'RETAIN_D1_AS_DEVELOPMENT_COMPONENT'
    changed = copy.deepcopy(values)
    for value in changed:
        for p in value['pairs']:
            if (p['candidate'], p['control']) in [('MB-D1', 'MB-D0'), ('MB-D1', 'M-B')]:
                p['classification'] = 'LOSS'
    # A single predeclared exposed new M-B gain suffices; no all-M-B dominance veto.
    next(p for p in changed[1]['pairs'] if p['candidate'] == 'MB-D1' and p['control'] == 'M-B')['classification'] = 'WIN'
    assert decision(changed, True)['stage'] == 'ADVANCE_FROZEN_D1_TO_PAPER_BENCHMARK'
    checks.append('actual_stage_function_priority_all_three_vetoes_incomplete_positions_exposure_and_no_hidden_D0_or_MB_dominance_veto')
    replay = read(OUT / 'preflight_R120_pair_replay.json')
    count = 0
    pair_counts = {}
    for group in replay['saved_groups']:
        by = {a['arm']: a for a in group['arms']}
        for p in group['pairs']:
            kind, severe = independent_pair(by[p['candidate']], by[p['control']])
            assert (kind, severe) == (p['classification'], p['severe_regression'])
            count += 1
            pair_counts[kind] = pair_counts.get(kind, 0) + 1
    assert count == 18
    checks.append('all18_R120_pairs_recomputed_by_separate_verbal_rule_implementation')
    return dict(checks=checks, fixture_count=len(checks), in_memory_only=True,
                method='AST extracts pure functions only; synthetic records/byte strings; no module import, research draw, or native execution',
                R120_replayed_pairs=count, R120_classifications=pair_counts,
                limitations='Raw receipt I/O is mocked only in the explicit journal branch fixture. Full real returned native settings/types/Starts/scopes remain qualification duties.',
                Optimize=0, native_starts=0)


def final_wiring_review(bindings):
    frozen = read(OUT / 'prospective_helper_freeze.json')
    assert frozen['source_bindings'] == bindings
    for path, digest in frozen['helpers'].items():
        assert sha(ROOT / path) == digest, 'helper freeze stale: ' + path
    assert frozen['argv_SHA'] == sha(OUT / 'argv_freeze.json')
    assert frozen['protocol_SHA'] == sha(OUT / 'protocol.json')
    argv = read(OUT / 'argv_freeze.json')
    manifest = read(OUT / 'input_manifest.json')
    assert len(argv['groups']) == 5 and len(argv['plans']) == 6
    assert sum(g['management_reserve'] for g in argv['groups']) == 600
    seen = set()
    inspected = []
    for plan in argv['plans']:
        launches = plan['launches']
        panel = next(p for p in manifest['roles'] + manifest['qualification_roles'] if p['id'] == launches[0]['id'])
        assert [l['arm'] for l in launches] == panel['method_order']
        for launch in launches:
            args = launch['command']
            arm = launch['arm']
            assert launch['seed'] == panel['gurobi_seed'] and launch['panel']['gurobi_seed'] == panel['gurobi_seed']
            assert launch['cap_seconds'] == panel['cap_seconds']
            assert launch['hard_stop_seconds'] == panel['cap_seconds'] - 2
            def option(name):
                assert args.count(name) == 1
                return args[args.index(name) + 1]
            for name, value in [('--gurobi-seed', panel['gurobi_seed']), ('--T', panel['T_seconds']),
                                ('--threads', 1), ('--mip-threads', 1), ('--gurobi-presolve', -1),
                                ('--pickup-time', 60), ('--drop-time', 60), ('--lambda', .15),
                                ('--process-wall-time-limit', panel['cap_seconds']),
                                ('--process-shutdown-margin', 30), ('--time-limit', panel['cap_seconds'] - 6)]:
                assert float(option(name)) == value
            assert option('--input') == panel['input_path']
            assert Path(args[0]).resolve() == (ROOT / 'build/research/round120/ExactEBRP.exe').resolve()
            if arm == 'P-GRB':
                assert option('--method') == 'gurobi' and '--plain-baseline' in args
                assert not any(a.startswith(('--round98-state-service', '--round120-native-proof', '--round112-ens-start')) for a in args)
            else:
                assert option('--method') == 'gcap-frontier' and option('--round98-state-service') == 'm-binary'
                assert option('--algorithm-preset') == 'research-round83-vds-equal-net-exchange'
                assert option('--round90-lp-g-split') == 'false'
                assert ('--round120-native-proof-d0' in args) == (arm == 'MB-D0')
                assert ('--round120-native-proof-d1' in args) == (arm == 'MB-D1')
            assert not any(a.startswith(('--round119', '--round120-qualification', '--round100-continuous-quantities')) for a in args)
            assert launch['destination'] not in seen
            seen.add(launch['destination'])
            inspected.append(dict(id=panel['id'], arm=arm, Seed=launch['seed'], cap=launch['cap_seconds'],
                                  formal=plan['name'].startswith('campaign/')))
    assert len(inspected) == 20 and sum(l['formal'] for l in inspected) == 16
    protocol = read(OUT / 'protocol.json')
    assert protocol['own_H_seed'] == 20260626 and protocol['own_H_semantics'] == 'full24+1 closure/exchange'
    assert protocol['common']['affinity_mask'] == 4
    assert protocol['native_reserve'] == 30 and protocol['evidence_tolerance'] == 1e-7
    assert protocol['default_ENS_changed'] is False
    compile_receipt = read(OUT / 'engineering/reference_compile02/receipt.json')
    assert compile_receipt['exit_code'] == 0
    assert compile_receipt['production_PE_SHA_after'] == '5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
    qualifier_text = (ROOT / 'scripts/qualify_round121.py').read_text(encoding='utf-8-sig')
    assert "engineering/reference_compile02/receipt.json" in qualifier_text
    return dict(helpers=frozen['helpers'], source_bindings=bindings, inspected_launches=inspected,
                helper_files_independently_hashed=len(frozen['helpers']), all20_argv_Seed_role_cap_and_physical_flags_checked=True,
                source_PE_DLL_identity_unchanged=True,
                prequalification_reference_resolution='Three new cold reference slots deliberately unresolved until one zero-Optimize batch; old safe reference copies then assigned by resolve.',
                reviewed_boundaries=[
                    'Seed1 readback checks exact nine journal settings and both Seed request/effective return codes. False raw native_preconditions is recovered only for returned integer calls with complete model and scope proof; LP calls are not promoted.',
                    'The compatibility projection is a deep copy. Raw observations, per-call settings, callback global_available and global_bound remain preserved.',
                    'Shared native logs are read through serial call/model/ledger and byte interval views. Start and Fingerprint are audited in their actual attribute states; no arbitrary cross-state fingerprint equality is added.',
                    'Inherited full production/Start/model/type/scope/physical/coverage audit remains required. Rejected D0/D1 dependent source is rejected again at complete group reconstruction, regardless of own UB or floor0.',
                    'Inherited producer seal and cap include H/model/LP/Start/installation/validation/cleanup/trailer. Verification is postseal, group reconciliation is outer group cost, and every group reserves all later unconditional obligations.',
                    'Five groups are unconditional and D0 appears only at F2 Seed1. Formal children have unique destinations and cannot overwrite or retry a position.',
                ],
                resolved_findings=[dict(finding='Read-only exporter duplicate main on engineering compile01', resolution='Parent changed only read-only entry point and compile02 succeeded; production PE unchanged.'),
                                   dict(finding='Concurrent review first observed qualifier reading compile01 while producer wrote compile02', resolution='Reread final qualifier binds compile02 receipt and exporter SHA.')],
                stage_review='Pure-function in-memory fixtures executed independently; performance threshold application awaits actual 16 formal positions.')


def run():
    started = time.perf_counter()
    recipe = read(OUT / 'source_recipe.json')
    manifest = read(OUT / 'input_manifest.json')
    receipt = read(OUT / 'generation_receipt.json')
    assert recipe['family'] == manifest['family'] == FAMILY
    assert recipe['raw_source_SHA'] == manifest['raw_source_SHA'] == RAW
    assert recipe['table_SHA'] == manifest['table_SHA'] == TABLE
    assert sha(OUT / 'source_recipe.json') == manifest['source_recipe_SHA']
    assert sha(ROOT / 'scripts/round121_data.py') == recipe['adapter_SHA']
    for path, expected_hash in recipe['generation_dependencies'].items():
        assert sha(ROOT / path) == expected_hash, path
    assert recipe['frozen_UTC'] < receipt['generated_UTC']
    assert recipe['generated_input_count'] == 0 and receipt['unique_new_input_files_written'] == 3
    assert receipt['Optimize'] == receipt['native_starts'] == 0
    assert recipe['formal_arms'] == 16 and recipe['formal_pairs'] == 18
    assert recipe['total_limit'] == [40, 48000] and recipe['qualification_limit'] == [8, 1800]
    table_path = ROOT / 'results/unified_exact_round116/source/source_station_table.csv'
    assert sha(table_path) == TABLE
    snapshot = read(ROOT / 'results/unified_exact_round116/source/snapshot.json')
    response_path = ROOT / snapshot['station_response_path']
    assert sha(response_path) == RAW
    raw = read(response_path)['data']['stations']
    with table_path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(raw) == 865
    assert [r['station_id'] for r in rows] == sorted((r['station_id'] for r in rows), key=lambda s: s.encode())
    assert len({r['station_id'] for r in rows}) == 865
    for i, row in enumerate(rows):
        assert int(row['source_row_index']) == i and row['raw_source_SHA'] == RAW
        assert 0 < int(row['capacity']) < 100  # No new source eligibility filtering occurs.
        for original in json.loads(row['original_row_indices']):
            assert raw[original]['station_id'] == row['station_id']
            assert raw[original]['capacity'] == int(row['capacity'])
            assert raw[original]['lat'] == float(row['latitude'])
            assert raw[original]['lon'] == float(row['longitude'])
        assert float(row['utm18n_easting_m']) == round(float(row['utm18n_easting_unrounded_m']), 3)
        assert float(row['utm18n_northing_m']) == round(float(row['utm18n_northing_unrounded_m']), 3)
    historic = read(ROOT / 'results/unified_exact_round116/historical_input_hash_index.json')['SHA_to_paths']
    old_roles = read(ROOT / 'results/unified_exact_round116/input_manifest.json')['roles'] + read(ROOT / 'results/unified_exact_round118/input_manifest.json')['roles']
    historic_hashes = set(historic) | {r['input_sha256'] for r in old_roles}
    assert len(manifest['roles']) == 5 and len(manifest['new_roles']) == 3
    arm_count = pair_count = formal_seconds = 0
    for role, expected in zip(manifest['roles'], EXPECTED):
        actual = tuple(role[k] for k in ['id', 'V', 'M', 'Q_vector', 'T_seconds', 'cap_seconds', 'gurobi_seed', 'method_order'])
        assert actual == expected
        assert role['pickup_seconds'] == role['drop_seconds'] == 60 and role['lambda'] == .15
        arm_count += len(role['method_order'])
        pair_count += 6 if role['id'] == 'F2' else 3
        formal_seconds += role['cap_seconds'] * len(role['method_order'])
        assert sha(ROOT / role['input_path']) == role['input_sha256']
    assert arm_count == 16 and pair_count == 18 and formal_seconds == 37200
    new_evidence, computed_overlaps = [], []
    for role in manifest['new_roles']:
        selected, depot, anchors = independent_selection(rows, role)
        landscape = independent_landscape(rows, role, selected)
        saved_s = read(ROOT / role['selection_path'])
        saved_l = read(ROOT / role['landscape_path'])
        assert saved_s['selected_source_station_row_indices'] == selected
        assert saved_s['dataset_family'] == saved_l['dataset_family'] == FAMILY
        assert saved_s['seed_derivation_material'].startswith(FAMILY + '|')
        assert saved_l['seed_derivation_material'].startswith(FAMILY + '|')
        assert saved_s['depot_coordinate_utm18n_meters'] == saved_l['depot']['coordinate_utm18n_meters'] == depot
        v, m, qs, values = parse_input(ROOT / role['input_path'])
        assert (v, m, qs) == (role['V'], role['M'], role['Q_vector'])
        for key in ['capacities', 'initial', 'target', 'weights', 'min_ratio']:
            assert saved_l[key] == landscape[key] == values[key][1:], (role['id'], key)
        assert values['points'][0] == tuple(depot)
        assert values['points'][1:] == [coordinates(rows[i]) for i in selected]
        assert len(set(selected)) == v
        assert all(len(values[k]) == v + 1 for k in values)
        assert all(0 <= b <= c and 0 < d <= c for b, c, d in zip(landscape['initial'], landscape['capacities'], landscape['target']))
        assert min(landscape['weights']) > 0 and max(landscape['weights']) == 1
        assert sum(landscape['initial']) == landscape['desired_total']
        mapping_path = ROOT / Path(role['input_path']).with_name(role['id'] + '_source_mapping.json')
        mapping = read(mapping_path)
        for j, (item, source_idx) in enumerate(zip(mapping, selected), 1):
            row = rows[source_idx]
            assert item['local_station_index'] == j and item['source_row_index'] == source_idx
            assert item['station_id'] == row['station_id'] and item['capacity'] == int(row['capacity'])
            assert (item['x'], item['y']) == coordinates(row)
            assert item['latitude'] == float(row['latitude']) and item['longitude'] == float(row['longitude'])
            assert item['original_row_indices'] == json.loads(row['original_row_indices'])
            assert item['source_response_SHA'] == RAW
        assert len(mapping) == v
        assert role['input_sha256'] not in historic_hashes
        ratio = [b / d for b, d in zip(landscape['initial'], landscape['target'])]
        ratio_sum = math.fsum(ratio)
        gini = math.fsum(abs(a - b) for i, a in enumerate(ratio) for b in ratio[i + 1:]) / (v * ratio_sum) if ratio_sum else 0.
        penalty = math.fsum(w * abs(r - 1) for w, r in zip(landscape['weights'], ratio))
        sw = math.fsum(landscape['weights'])
        for key, value in [('G', gini), ('P', penalty), ('lambda_P', .15 * penalty), ('F', gini + .15 * penalty)]:
            assert abs(role['empty_fleet'][key] - value) < 1e-12
        assert abs(role['sum_weights'] - sw) < 1e-12
        assert abs(role['lambda_sum_weights'] - .15 * sw) < 1e-12
        for previous in old_roles:
            if previous['V'] <= 50:
                old_selected = read(ROOT / previous['selection_path'])['selected_source_station_row_indices']
                computed_overlaps.append(dict(id=role['id'], old_id=previous['id'], old_V=previous['V'], new_V=v,
                                              overlap=len(set(selected) & set(old_selected))))
        new_evidence.append(dict(id=role['id'], SHA=role['input_sha256'], V=v, M=m, Q=qs,
                                 total_initial=sum(landscape['initial']), total_target=sum(landscape['target']),
                                 total_capacity=sum(landscape['capacities']), inventory_delta=landscape['delta'],
                                 sum_weights=sw, lambda_sum_weights=.15 * sw,
                                 empty_fleet=dict(G=gini, P=penalty, lambda_P=.15 * penalty, F=gini + .15 * penalty,
                                                  duration=0, all_prefix_and_return_loads=0, feasible=True),
                                 anchor_indices=anchors, independent_selection_and_landscape_match=True,
                                 no_historical_exact_SHA_duplicate=True, source_mapping_rows_checked=len(mapping),
                                 sign_repair_used=landscape['sign_repair_used']))
    assert computed_overlaps == manifest['overlaps']
    assert len({r['input_sha256'] for r in manifest['new_roles']}) == 3
    production = read(OUT / 'production_identity.json')
    actual_bindings = {p.relative_to(ROOT).as_posix(): sha(p) for p in [ROOT / 'CMakeLists.txt'] +
                       sorted(p for folder in ['src', 'include'] for p in (ROOT / folder).rglob('*') if p.suffix in ['.cpp', '.inc', '.hpp', '.h'])}
    assert actual_bindings == production['source_bindings']
    assert production['source_commit_before_native'] == '355eefd2be3fe5651195681faf7b3a63ee4032f8'
    assert sha(ROOT / production['production_PE_path']) == production['production_PE_SHA'] == '5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
    assert sha(Path('D:/gurobi1302/win64/bin/gurobi130.dll')) == production['DLL_SHA'] == '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
    final_wiring = final_wiring_review(actual_bindings)
    finite = in_memory_fixtures()
    report = dict(review_kind='real_different_executor_pre_contract', reviewer='round121_contract_review subagent',
                  status='FINAL_PREQUALIFICATION_CONTRACT_REVIEW_COMPLETE', decision='ACCEPT',
                  reviewer_script_SHA=sha(__file__),
                  admission_scope='Prequalification contract only. Actual H100 Seed1 CLI qualification and formal admission remain required.',
                  helpers=final_wiring['helpers'], source_bindings=actual_bindings,
                  UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  method='Independent standard-library implementation; no campaign/generator imports; full saved-matrix arithmetic; no external requests',
                  reviewed_file_SHA={p: sha(ROOT / p) for p in ['scripts/round121_data.py', 'scripts/round121_common.py',
                                      'results/unified_exact_round121/goal.md', 'results/unified_exact_round121/source_recipe.json',
                                      'results/unified_exact_round121/input_manifest.json', 'results/unified_exact_round121/generation_receipt.json']},
                  freeze_record=dict(recipe_UTC=recipe['frozen_UTC'], generation_UTC=receipt['generated_UTC'],
                                     recorded_recipe_commit=manifest['recipe_commit_before_generation'],
                                     chronology_and_hash_links_consistent=True,
                                     Git_commit_independently_read_by_this_reviewer=False),
                  input_evidence=new_evidence, same_source_not_IID=True, overlap_evidence=computed_overlaps,
                  resource_contract=dict(formal_arms=arm_count, pairs=pair_count, new_problems=3, known_seed_blocks=2,
                                         formal_seconds=formal_seconds, management_reserve=600, qualification_max_seconds=1800,
                                         conservative_plan_seconds=39600, conservative_plan_starts=29,
                                         total_limit=[40, 48000], qualification_limit=[8, 1800],
                                         qualification_planned_native_children=5, formal_children_and_wrappers=21),
                  frozen_source=dict(source_bindings_checked=len(actual_bindings), PE_SHA=production['production_PE_SHA'],
                                     DLL_SHA=production['DLL_SHA'], unchanged_source_identity=True),
                  final_wiring=final_wiring, independent_in_memory_fixtures=finite,
                  old_saved_h_reselection=[old_h_review(role) for role in ['F2', 'R98-C2']],
                  restrictions=dict(Optimize=0, native_starts=0, compiles=0, Git_commands=0,
                                    research_input_files_written=0, production_files_modified=0,
                                    allowed_outputs=['scripts/round121_precontract_review.py',
                                                     'results/unified_exact_round121/review/pre_contract.json',
                                                     'results/unified_exact_round121/review/pre_contract.md',
                                                     'results/unified_exact_round121/review/h_reselection_sources/**']),
                  limitations=[
                      'This accepts only the final frozen prequalification contract. Actual H100 Seed1 returned settings/model/Start/domain/log evidence is not yet available; no native or performance admission is issued here.',
                      'Recorded pre-generation commit and generation chronology are cross-checked as artifacts, not independently verified with Git; this reviewer was explicitly barred from Git operations.',
                      'Absence of unrecorded external prior measurements cannot be inferred from a no-filter assertion; source code/receipts and fixed hashes support the declared once-only procedure.',
                      'No native model was built, solved, replayed, or altered by this reviewer. The old h analysis uses the existing complete matrices and primals only; its minimal local safe snapshot permits public --h-only replay without the original worktree.',
                      'No new projection theorem, exact rational solver certificate, h branching/fixing claim, or performance conclusion follows from the two h repairs.',
                      'No historical carrier restoration, website acquisition, or license endpoint access occurred.',
                  ], engineering_seconds=time.perf_counter() - started, human_time='unknown')
    review_dir = OUT / 'review'
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / 'pre_contract.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    lines = ['# R121 independent pre-contract review', '',
             'Decision: **ACCEPT for actual qualification only**. Status: **' + report['status'] + '**. This is a real different executor, using an independent standard-library implementation. No native or performance admission is issued.', '',
             'The frozen source/PE/DLL hashes, declared generation dependencies, safe 865-row source, selected station mappings, new input dimensions, target/inventory rules, and empty-fleet objective were recalculated. All three serialized new inputs match the fixed mathematics. No input was generated or rewritten by this review.', '',
             'The table contains 16 formal arms, 18 pairs, three new problems and two known Seed1 blocks. Its formal window is 37200 seconds; management 600 plus qualification 1800 gives 39600 of 48000 seconds. The conservative declared plan is 29 of 40 launches, within qualification 8/1800. Runtime accounting remains the campaign executor\'s responsibility.', '',
             '| Input | B / D | sum(w) | lambda sum(w) | Empty F |', '|---|---:|---:|---:|---:|']
    for value in new_evidence:
        lines.append(f"| {value['id']} | {value['total_initial']} / {value['total_target']} | {value['sum_weights']:.6f} | {value['lambda_sum_weights']:.8f} | {value['empty_fleet']['F']:.12f} |")
    lines += ['', 'These are subsets of the same previously known city source, with all 15 overlaps independently recomputed. They are not three cities or IID samples.', '',
              f"The review binds all {final_wiring['helper_files_independently_hashed']} helper file hashes and all {len(actual_bindings)} production source bindings, plus frozen argv/protocol. All 20 planned argv positions (16 formal plus four qualification) were checked for the actual role, Seed, cap, method and physical flags. New cold reference slots deliberately remain placeholders until the one zero-Optimize exporter batch.", '',
              f"The reviewer executed {finite['fixture_count']} finite in-memory checks by compiling selected pure function definitions without importing campaign or generator modules. The raw journal tests mocked receipt I/O only. Their full predicates and actual results are in the JSON:", '']
    lines += ['- ' + check for check in finite['checks']]
    lines += ['', 'The separate comparison implementation reproduced all 18 R120 classifications and severe flags. This is a preflight comparison-rule check; the current formal 18 pairs do not yet exist.', '',
              'The final Seed1 adapter checks the actual nine call settings, Seed request/effective readbacks and return codes before an in-memory compatibility projection. It permits only returned integer calls with complete model/scope checks. It leaves LP calls and raw callback/global flags unpromoted. The inherited complete Start, model/domain, parameter, physical and coverage audits remain mandatory for real qualification.', '',
              'Call logs retain all raw bytes and use per-call serial/model/ledger/byte-span views. T_produce remains sealed before read-only verification; group reconciliation is charged to the outer group clock. All later unconditional groups remain reserved. A rejected D0/D1 source stops native disjunction qualification even if independent physical UB or floor0 exists.', '',
              'Two engineering findings were resolved by the parent before this binding: duplicate main in read-only exporter compile01, and a concurrent snapshot in which the qualifier still named compile01 while the exporter wrote compile02. The final read-only compile02 receipt is successful and the qualifier names that same receipt. The production PE hash is unchanged.', '',
              'The two old D0 maximum-violation witnesses both extend to D1 with every original coordinate fixed and h=0. The actual saved three rows, full objective including ObjCon, all original rows and bounds are used; the saved matrices have h only in those three rows. The JSON records all coefficients and residuals. This limits the old witnesses\' projection interpretation without changing their established nonredundancy in the extended space.', '',
              '| Saved witness | Original h | Actual link h interval | Selected h | D1 residual after repair |',
              '|---|---:|---|---:|---:|']
    for value in report['old_saved_h_reselection']:
        if 'selected_h' in value:
            lines.append(f"| {value['role']} | {value['original_h']:.16g} | {value['actual_link_h_interval']} | {value['selected_h']} | {value['repaired_D1_full_residual']['maximum_row_violation']:.6g} |")
        else:
            lines.append(f"| {value['role']} | unknown | unknown | unknown | unknown |")
    lines += ['', 'For public old-witness replay, run `python -B scripts/round121_precontract_review.py --h-only`. It reads the local `review/h_reselection_sources` snapshot: exactly the two original D0 witness/base-matrix files and their historical records, plus extracted actual D1 three rows and provenance. It writes nothing, needs no PE/DLL or original worktree, and performs no Optimize. The complete D1 matrix is reconstructed from the independently verified identical original rows plus those actual three rows. No other LP primal, MPS, carrier or historical restoration was added.', '',
              'Executed by this reviewer: standard-library Python arithmetic and read-only file access; 0 Optimize, 0 native starts, 0 compilation, 0 Git commands. Writes were limited to this reviewer script, the two permitted review files, and the explicitly authorized minimal h snapshot. Snapshot source absolute paths and SHA256 values are recorded.', '', 'Limitations:', '']
    lines += ['- ' + limitation for limitation in report['limitations']]
    (review_dir / 'pre_contract.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], inputs=len(new_evidence), pairs=pair_count,
                          h_results=[{'role': v['role'], 'result': v['result']} for v in report['old_saved_h_reselection']],
                          Optimize=0, native_starts=0, engineering_seconds=report['engineering_seconds'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-h-sources', action='store_true')
    parser.add_argument('--h-only', action='store_true', help='Public replay from local minimal sources; no PE/DLL, native, Git, or writes')
    args = parser.parse_args()
    if args.snapshot_h_sources:
        snapshot_h_sources()
    elif args.h_only:
        print(json.dumps(dict(roles=[old_h_review(role) for role in ['F2', 'R98-C2']], Optimize=0, native_starts=0), indent=2, allow_nan=False))
    else:
        run()
