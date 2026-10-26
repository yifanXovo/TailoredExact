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
import builtins
import collections
import hashlib
import json
import math
import os
import re
import statistics
import tempfile
import time
import types
import traceback

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
                argv_SHA=sha(OUT / 'argv_freeze.json'), protocol_SHA=sha(OUT / 'protocol.json'),
                prospective_helper_freeze_SHA=sha(OUT / 'prospective_helper_freeze.json'),
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


def qualification01_reentry_review(final_wiring, previous_review):
    """Execute only the corrected zero/result and not-started fixture block.

    The actual current fixture AST supplies the input, result and call-path
    expressions. Complete original physical/full-fleet/event functions and
    the call-view body are compiled separately. No full finite() call occurs.
    """
    fee = OUT / 'fees/qualification01'
    if not (fee / 'receipt.json').is_file():
        return None
    if (OUT / 'fees/qualification02/receipt.json').is_file() and previous_review.get('qualification01_reentry'):
        # Preserve that earlier, already executed decision as historical. The
        # new continuation has a separate current budget and helper binding.
        historical = copy.deepcopy(previous_review['qualification01_reentry'])
        historical['historical_as_of_qualification01_closeout'] = True
        return historical
    receipt = read(fee / 'receipt.json')
    assert receipt['exit_code'] == 1 and receipt['actual_native_children'] == 0
    assert receipt['conservative_process_starts'] == 1 and receipt['actual_exit_observed']
    assert not (fee / '01_reference_before.json').exists()
    assert 'physical' in (fee / 'failure.txt').read_text(encoding='utf-8')
    changed = {k: dict(before=previous_review['helpers'].get(k), after=v)
               for k, v in final_wiring['helpers'].items() if previous_review['helpers'].get(k) != v}
    assert set(changed) <= {'scripts/round121_fixtures.py'}
    assert set(previous_review['helpers']) == set(final_wiring['helpers'])
    assert previous_review['source_bindings'] == final_wiring['source_bindings']
    original_fixture = previous_review.get('qualification01_reentry', {}).get('initial_review_fixture_SHA',
                       previous_review['helpers']['scripts/round121_fixtures.py'])
    if not changed and previous_review.get('qualification01_reentry'):
        changed = previous_review['qualification01_reentry']['changed_helpers_from_previous_bound_review']
    physical_scope = definitions(ROOT / 'scripts/round107_reader.py', ['close', 'instance', 'objective', 'physical', 'portable'],
                                 dict(ast=ast, re=re, math=math, Path=Path, TOL=1e-7))
    full_scope = definitions(ROOT / 'scripts/round108_reader.py', ['full_fleet'],
                            dict(evidence=types.SimpleNamespace(**physical_scope), math=math))
    event_scope = definitions(ROOT / 'scripts/round120_evidence.py', ['event_chain'],
                             dict(NEW=['MB-D0', 'MB-D1'], core=types.SimpleNamespace(full_fleet=full_scope['full_fleet']),
                                  read=read, json=json))
    log_tree = ast.parse((ROOT / 'scripts/round118_call_logs.py').read_text(encoding='utf-8-sig'))
    log_nodes = [copy.deepcopy(n) for n in log_tree.body if isinstance(n, ast.FunctionDef) and n.name in ['digest', 'segments', 'build']]
    # Replace only build's import binding with the exact pure reader portable
    # definition above; all other build statements and predicates are unchanged.
    build_node = next(n for n in log_nodes if n.name == 'build')
    assert isinstance(build_node.body[0], ast.Import)
    assert build_node.body[0].names[0].name == 'round108_reader'
    build_node.body = build_node.body[1:]
    def forbidden_model_read(*args, **kwargs):
        raise AssertionError('not_started fixture unexpectedly read a native model or ledger')
    log_scope = dict(Path=Path, collections=__import__('collections'), re=re, hashlib=hashlib,
                     core=types.SimpleNamespace(portable=physical_scope['portable'], lp_model=forbidden_model_read,
                                                rows=forbidden_model_read, sha=sha))
    exec(compile(ast.Module(body=log_nodes, type_ignores=[]), 'round118_call_logs::isolated_not_started', 'exec'), log_scope)
    fixture_path = ROOT / 'scripts/round121_fixtures.py'
    fixture_tree = ast.parse(fixture_path.read_text(encoding='utf-8-sig'))
    run_node = next(n for n in fixture_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    with_node = next(copy.deepcopy(n) for n in run_node.body if isinstance(n, ast.With))
    split = next(i for i, n in enumerate(with_node.body) if isinstance(n, ast.For))
    zero = next(i for i, n in enumerate(with_node.body)
                if isinstance(n, ast.Expr) and 'zero.txt' in ast.unparse(n) and 'write_text' in ast.unparse(n))
    with_node.body = with_node.body[:split] + with_node.body[zero:]
    result_nodes = [n for n in with_node.body if isinstance(n, ast.Expr) and "'result.json'" in ast.unparse(n)]
    assert len(result_nodes) == 1 and 'F=0.0' in ast.unparse(result_nodes[0])
    call_node = next(n for n in with_node.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'j' for t in n.targets))
    assert "native_log_path='raw/missing.log'" in ast.unparse(call_node)
    with_node.body += ast.parse("physical_replay=full_fleet(root,p,read(d/'result.json'))\nmissing_F_still_rejected=reject_missing_F(root,p)").body

    class GuardedTemporaryDirectory:
        def __init__(self, *args, **kwargs):
            assert not kwargs.get('dir'), 'must use the actual system temp shape'
            self.context = tempfile.TemporaryDirectory(*args, **kwargs)
        def __enter__(self):
            self.value = Path(self.context.__enter__()).resolve()
            assert self.value.parent == Path(tempfile.gettempdir()).resolve()
            assert self.value.name.startswith('r121-finite-')
            assert 'results/' not in self.value.as_posix()
            return str(self.value)
        def __exit__(self, *args):
            # Verify the absolute target before the context's recursive cleanup.
            assert self.value.parent == Path(tempfile.gettempdir()).resolve()
            assert self.value.name.startswith('r121-finite-')
            return self.context.__exit__(*args)

    def write_fixture(path, value):
        path = Path(path)
        path.write_text(json.dumps(value, allow_nan=False) + '\n', encoding='utf-8')

    def reject_missing_F(root, panel):
        try:
            full_scope['full_fleet'](root, panel, dict(routes=[]))
        except AssertionError:
            return True
        raise AssertionError('original physical reported-objective requirement was weakened')

    isolate = ast.FunctionDef(name='isolated_case', args=ast.arguments(posonlyargs=[], args=[], vararg=None,
              kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), decorator_list=[],
              body=[with_node] + ast.parse("return dict(zero_event=value,physical=physical_replay,view_actual=view['actual'],view_bindings=view['bindings'],checks=checks,missing_F_still_rejected=missing_F_still_rejected,temporary_root=str(root))").body)
    isolated_tree = ast.fix_missing_locations(ast.Module(body=[isolate], type_ignores=[]))
    isolated_scope = dict(tempfile=types.SimpleNamespace(TemporaryDirectory=GuardedTemporaryDirectory), Path=Path,
                          write=write_fixture, event_chain=event_scope['event_chain'], build=log_scope['build'],
                          checks=[], full_fleet=full_scope['full_fleet'], read=read, reject_missing_F=reject_missing_F)
    exec(compile(isolated_tree, str(fixture_path) + '::isolated_reentry_case', 'exec'), isolated_scope)
    result = isolated_scope['isolated_case']()
    assert result['zero_event']['not_exposed_original_verified_zero_H']
    assert result['physical']['G'] == result['physical']['P'] == result['physical']['F'] == 0.
    assert not result['view_actual'] and not result['view_bindings']
    assert result['missing_F_still_rejected'] and not Path(result['temporary_root']).exists()
    q_remaining_starts = 8 - receipt['conservative_process_starts']
    q_remaining_seconds = 1800 - receipt['outer_seconds_upper']
    total_remaining_seconds = 48000 - receipt['outer_seconds_upper']
    assert q_remaining_starts >= 6 and q_remaining_seconds >= 1200
    assert 40 - receipt['conservative_process_starts'] >= 6 + 21
    assert total_remaining_seconds >= 1200 + 37800
    return dict(decision='ACCEPT_REENTRY_TO_ACTUAL_QUALIFICATION_ONLY',
                initial_review_fixture_SHA=original_fixture, current_fixture_SHA=sha(fixture_path),
                changed_helpers_from_previous_bound_review=changed,
                every_other_helper_and_all_production_source_bindings_unchanged=True,
                qualification01_failure=dict(fee_SHA=sha(fee / 'receipt.json'), failure_SHA=sha(fee / 'failure.txt'),
                    actual_native_children=0, exporter_started=False, Optimize=0,
                    charged_starts=receipt['conservative_process_starts'], charged_outer_seconds=receipt['outer_seconds_upper'],
                    reason='Fixture result omitted the required reported F; unchanged physical reader rejected it before native launch.'),
                additional_caught_fixture_error=dict(reason='Absolute system-temp missing.log path violates unchanged portable evidence-path rule.',
                    fixed_to='raw/missing.log', native_or_qualification_retry_used_for_this_diagnosis=False),
                isolated_actual_system_temp_result=result,
                execution_method='AST-isolated current zero and subsequent not_started statements; unchanged original physical/full_fleet/event_chain predicates, unchanged call-view body and portable rule; no full finite() run',
                remaining_qualification_starts=q_remaining_starts, remaining_qualification_seconds=q_remaining_seconds,
                next_qualification_obligation=dict(wrapper=1, children=5, conservative_starts=6, outer_cap_seconds=1200),
                remaining_formal_obligation=dict(starts=21, nominal_plus_management_seconds=37800),
                reviewer_Optimize=0, reviewer_native_starts=0, reviewer_compiles=0, reviewer_Git_commands=0,
                limitations='Only the failed and subsequent zero/not_started fixture paths were replayed; actual returned Seed1 CLI evidence remains pending.')


def actual_P_readonly_review(arm='P-GRB'):
    """Replay the real sealed H100 P audit while isolating every derived write.

    This optional branch imports the existing read-only audit chain. No native
    entry point is called. The original source and evidence paths stay fixed;
    only new audit sidecar I/O is routed to a temporary shadow directory.
    """
    import round121_evidence as evidence
    import read_round118 as reader
    import read_round116 as inherited_reader
    tick = time.perf_counter()
    identity_path = OUT / 'qualification/h100/identity.json'
    identity = read(identity_path)
    launch = next(l for l in identity['launches'] if l['arm'] == arm)
    assert launch['arm'] == arm and launch['seed'] == 1
    directory = Path(launch['destination']).resolve()
    originals = {p.relative_to(directory).as_posix(): sha(p) for p in directory.rglob('*') if p.is_file()}
    seal = read(directory / 'producer_seal.json')
    producer = read(directory / 'producer_receipt.json')
    assert sha(directory / 'producer_seal.json') == producer['producer_seal_SHA']
    for name, digest in seal['required_SHA'].items():
        assert originals[name] == digest
    result = read(directory / 'result.json')
    observations = read(directory / 'observations.json')
    calls = [v['payload'] for v in observations if v['payload']['kind'] == 'call']
    assert calls and all(type(c['native_preconditions']) is int and c['native_preconditions'] == 0 for c in calls)
    assert all(v['payload']['global_available'] == 0 and v['payload']['global_bound'] is None
               for v in observations if v['payload']['kind'] == 'bound')
    proof = evidence.qualify_seed(ROOT, launch, observations, read(directory / 'completion.json'), identity)
    parameters = evidence._parameters(result, seed=1, require_call=True, arm='P-GRB') if arm == 'P-GRB' else dict(per_call_settings=[c['settings'] for c in calls])
    model = directory / 'compact.lp' if arm == 'P-GRB' else Path(calls[0]['model_path'])
    reference = OUT / 'qualification/h100/reference/H100/original.lp'
    if arm == 'P-GRB':
        assert sha(model) == sha(reference) == launch['panel']['reference']['canonical_sha256'] == calls[0]['model_sha256']
    else:
        assert sha(model) == calls[0]['model_sha256']
    # Independent direct grammar/section checks; do not call the shared parser.
    lines = model.read_text(encoding='utf-8').splitlines()
    marks = {name: lines.index(name) for name in ['Minimize', 'Subject To', 'Bounds', 'Generals', 'Binaries', 'End']}
    row_count = marks['Bounds'] - marks['Subject To'] - 1
    bounds = lines[marks['Bounds'] + 1:marks['Generals']]
    generals = [line.strip() for line in lines[marks['Generals'] + 1:marks['Binaries']]]
    binaries = [line.strip() for line in lines[marks['Binaries'] + 1:marks['End']]]
    if arm == 'P-GRB':
        assert row_count == result['gurobi_num_constrs'] == 3689
        assert len(bounds) == result['gurobi_num_vars'] == 1591
        assert len(generals) == result['gurobi_num_int_vars'] == 140
        assert len(binaries) == result['gurobi_num_bin_vars'] == 1040
        assert len(bounds) - len(generals) - len(binaries) == result['gurobi_num_cont_vars'] == 411
    p = launch['panel']
    v, m, qs, instance = parse_input(ROOT / p['input_path'])
    assert (v, m, qs) == (p['V'], p['M'], p['Q_vector'])
    quantities = [f'{prefix}_{k}_{i}' for prefix in ['p', 'd'] for k in range(m) for i in range(1, v + 1)]
    if arm == 'P-GRB':
        assert all(name in generals for name in quantities)
    else:
        assert all(name not in generals and name not in binaries for name in quantities)
        assert all(any(re.search(r'\b' + re.escape(name) + r'\b', line) for line in bounds) for name in quantities)
    # Independent complete physical route replay, including every prefix load.
    inventories = instance['initial'].copy()
    seen, vehicles, routes = set(), set(), []
    for route in result['routes']:
        k = route['vehicle']
        assert k not in vehicles and 0 <= k < m
        vehicles.add(k)
        assert route['nodes'][0] == route['nodes'][-1] == 0
        ops = {op['station']: (op['pickup'], op['drop']) for op in route['operations']}
        assert len(ops) == len(route['operations']) and set(route['nodes'][1:-1]) == set(ops)
        load, pickup, loads = 0, 0, []
        for i in route['nodes'][1:-1]:
            assert i not in seen and 1 <= i <= v
            seen.add(i)
            pick, drop = ops[i]
            assert type(pick) is int and type(drop) is int and pick >= 0 and drop >= 0 and bool(pick) != bool(drop)
            load += pick - drop
            pickup += pick
            loads.append(load)
            assert 0 <= load <= qs[k]
            inventories[i] += drop - pick
            assert 0 <= inventories[i] <= instance['capacities'][i]
        travel = math.fsum(distance(instance['points'][a], instance['points'][b]) / 1.5 for a, b in zip(route['nodes'], route['nodes'][1:]))
        duration = travel + (p['pickup_seconds'] + p['drop_seconds']) * pickup
        assert duration <= p['T_seconds'] + 1e-7
        routes.append(dict(vehicle=k, prefix_loads=loads, return_load=load, cumulative_pickup=pickup,
                           travel_seconds=travel, full_duration_seconds=duration))
    assert sum(inventories[1:]) == sum(instance['initial'][1:]) - sum(r['return_load'] for r in routes)
    ratio = [inventories[i] / instance['target'][i] for i in range(1, v + 1)]
    g = math.fsum(abs(a - b) for i, a in enumerate(ratio) for b in ratio[i + 1:]) / (v * math.fsum(ratio)) if math.fsum(ratio) else 0.
    penalty = math.fsum(instance['weights'][i] * abs(ratio[i - 1] - 1) for i in range(1, v + 1))
    f = g + p['lambda'] * penalty
    assert abs(f - result['upper_bound']) <= 1e-7
    source_open, source_stat, source_mkdir, regular_open = Path.open, Path.stat, Path.mkdir, builtins.open
    shadow_files, audit_value, endpoint, readout_error = {}, None, None, None
    with tempfile.TemporaryDirectory(prefix='r121-actualP-readonly-') as temporary:
        shadow = Path(temporary).resolve()
        assert shadow.parent == Path(tempfile.gettempdir()).resolve() and shadow.name.startswith('r121-actualP-readonly-')
        writes = []
        def absolute(path):
            # resolve() on Windows invokes stat(); avoid recursive interception.
            return Path(os.path.abspath(os.fspath(path)))
        def target(path, mode='r'):
            if isinstance(path, int):
                return path
            actual = absolute(path)
            if actual.is_relative_to(directory):
                rel = actual.relative_to(directory)
                replacement = shadow / rel
                if any(ch in mode for ch in 'wxa+'):
                    allowed_derived = {'round120_model_contracts.json', 'call_log_views.json', 'computed_seed_scope.json',
                        'independent_evidence.json', 'native_claims.json', 'claim_rejections.json', 'audit.json',
                        'audit_execution_metrics.json', 'postexit_audit_receipt.json', 'verification_closeout.json',
                        'arm_total_receipt.json', 'round120_extended_verification.json'}
                    assert rel.as_posix() not in originals or rel.as_posix() in allowed_derived, ('immutable original file write attempted', str(rel))
                    source_mkdir(replacement.parent, parents=True, exist_ok=True)
                    writes.append(rel.as_posix())
                    return replacement
                try:
                    source_stat(replacement)
                    return replacement
                except FileNotFoundError:
                    pass
            if any(ch in mode for ch in 'wxa+'):
                assert actual.is_relative_to(shadow), ('unexpected audit output outside shadow', str(actual))
            return path
        def path_open(self, mode='r', *args, **kwargs):
            return source_open(target(self, mode), mode, *args, **kwargs)
        def safe_open(file, mode='r', *args, **kwargs):
            return regular_open(target(file, mode), mode, *args, **kwargs)
        def path_stat(self, *args, **kwargs):
            actual = absolute(self)
            if actual.is_relative_to(directory):
                try:
                    return source_stat(shadow / actual.relative_to(directory), *args, **kwargs)
                except FileNotFoundError:
                    pass
            return source_stat(self, *args, **kwargs)
        def path_mkdir(self, *args, **kwargs):
            actual = absolute(self)
            if actual.is_relative_to(directory):
                return None if actual == directory else source_mkdir(shadow / actual.relative_to(directory), *args, **kwargs)
            return source_mkdir(self, *args, **kwargs)
        Path.open, Path.stat, Path.mkdir, builtins.open = path_open, path_stat, path_mkdir, safe_open
        try:
            audit_value = evidence.verify(launch, identity)
            assert audit_value['passed'] and audit_value['native_proof_qualified']
            recs = collections.defaultdict(list)
            with evidence.extension():
                item = reader.item(ROOT, launch, identity, recs)
                final = inherited_reader.reconcile(item['claims'], item['ind']['witnesses'])
                assert not final['rejections']
                endpoint = reader.finalize(ROOT, item, final, recs)
            assert endpoint['formal_protocol_qualified'] and endpoint['actually_executed']
        except BaseException:
            readout_error = traceback.format_exc(limit=12)
        finally:
            Path.open, Path.stat, Path.mkdir, builtins.open = source_open, source_stat, source_mkdir, regular_open
        for path in shadow.rglob('*'):
            if path.is_file():
                shadow_files[path.relative_to(shadow).as_posix()] = sha(path)
        derived = {name: read(shadow / name) for name in ['audit.json', 'verification_closeout.json', 'arm_total_receipt.json'] if (shadow / name).exists()}
        assert shadow.parent == Path(tempfile.gettempdir()).resolve() and shadow.name.startswith('r121-actualP-readonly-')
    unchanged = originals == {p.relative_to(directory).as_posix(): sha(p) for p in directory.rglob('*') if p.is_file()}
    assert unchanged, 'original P evidence directory changed during read-only review'
    label = 'P' if arm == 'P-GRB' else 'MB'
    record = dict(status='ACTUAL_' + label + '_FULL_SHADOW_AUDIT_AND_READOUT_OK' if not readout_error else 'ACTUAL_' + label + '_READOUT_FIX_NEEDED', arm=arm,
                  actual_source_identity_SHA=sha(identity_path), actual_launch_SHA=sha(directory / 'launch.json'),
                  producer_receipt_SHA=sha(directory / 'producer_receipt.json'), producer_seal_SHA=sha(directory / 'producer_seal.json'),
                  original_T_produce=producer['T_produce'], original_raw_file_SHA=originals, original_raw_unchanged=unchanged,
                  actual_result_status=result['gurobi_status'] if arm == 'P-GRB' else result['status'], actual_Optimize_in_historical_record=len(calls),
                  raw_native_preconditions=dict(value=calls[0]['native_preconditions'], type=type(calls[0]['native_preconditions']).__name__),
                  actual_parameter_readback=parameters, actual_settings=calls[0]['settings'], raw_global_flags_all_unchanged_and_unavailable=True,
                  recovered_call_count=len(proof['recovered_calls']), actual_model_SHA=sha(model), reference_bytes_identical=True if arm == 'P-GRB' else None,
                  independent_matrix_counts=dict(rows=row_count, columns=len(bounds), C=len(bounds)-len(generals)-len(binaries), I=len(generals), B=len(binaries), quantity_type='I' if arm == 'P-GRB' else 'C'),
                  independent_physical=dict(G=g, P=penalty, lambda_P=p['lambda'] * penalty, F=f, Y=inventories, routes=routes),
                  shadow_audit_summary={k: audit_value.get(k) for k in ['passed', 'native_proof_qualified', 'independent_evidence_audit_passed']} if audit_value else None,
                  endpoint=endpoint, shadow_file_SHA=shadow_files, readout_error=readout_error,
                  shadow_clock_values_are_review_products_not_original_arm_receipts=True,
                  no_T_produce_backfill=True, original_identity_retained=True,
                  later_readonly_audit_helper_SHA=sha(ROOT / 'scripts/round121_evidence.py'),
                  scope='Existing real H100 ' + arm + ' Seed1 evidence only; original paths and all audit predicates unchanged; new derived writes isolated to deleted temp overlay; independent section/count and complete physical replay also performed.',
                  limits='No new native execution, compilation, Git, cross-arm proof, replacement route, or new bound. Endpoint reconciliation here uses only this arm own witnesses; later full cohort adjudication remains necessary.',
                  reviewer_native_starts=0, reviewer_Optimize=0, reviewer_compiles=0, reviewer_Git=0, seconds=time.perf_counter() - tick)
    destination = OUT / ('review/actual_H100_' + label + '_readonly_review.json')
    destination.write_text(json.dumps(record, indent=2, allow_nan=False, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=record['status'], raw_unchanged=unchanged, original_T_produce=producer['T_produce'],
                          full_audit=record['shadow_audit_summary'], readout_error=readout_error, native_starts=0, Optimize=0)))
    return record


def qualification02_continuation_review(final_wiring):
    patch_path = OUT / 'qualification/read_only_patch_identity.json'
    if not patch_path.exists():
        return None
    patch = read(patch_path)
    assert patch['final_helpers'] == final_wiring['helpers']
    assert set(patch['changed_helpers']) == {'scripts/qualify_round121.py', 'scripts/round121_evidence.py'}
    saved_candidate = OUT / 'qualification/candidate_identity_before_readonly_fix.json'
    saved_freeze = OUT / 'qualification/prospective_helper_freeze_before_readonly_fix.json'
    saved_adapter = OUT / 'qualification/Seed1_evidence_adapter_original.py'
    assert sha(saved_candidate) == patch['original_candidate_identity_SHA']
    assert sha(saved_freeze) == patch['original_prospective_helper_freeze_SHA']
    assert sha(saved_adapter) == patch['old_adapter_source_SHA']
    old_helpers = read(saved_freeze)['helpers']
    differences = {k: dict(before=old_helpers.get(k), after=v) for k, v in final_wiring['helpers'].items() if old_helpers.get(k) != v}
    assert differences == patch['changed_helpers']
    assert read(saved_freeze)['argv_SHA'] == final_wiring['argv_SHA']
    assert read(saved_freeze)['protocol_SHA'] == final_wiring['protocol_SHA']
    old_ast = ast.parse(saved_adapter.read_text(encoding='utf-8-sig'))
    new_ast = ast.parse((ROOT / 'scripts/round121_evidence.py').read_text(encoding='utf-8-sig'))
    old_asserts = [n for n in ast.walk(old_ast) if isinstance(n, ast.Assert) and "c['native_preconditions'] is False" in ast.unparse(n)]
    new_asserts = [n for n in ast.walk(new_ast) if isinstance(n, ast.Assert) and "type(c['native_preconditions'])" in ast.unparse(n)]
    assert len(old_asserts) == len(new_asserts) == 1
    assert ast.unparse(new_asserts[0]) == "assert type(c['native_preconditions']) in [bool, int] and c['native_preconditions'] == 0 and (cid in j['returned_ids'])"
    new_asserts[0].test = copy.deepcopy(old_asserts[0].test)
    assert ast.dump(old_ast, include_attributes=False) == ast.dump(new_ast, include_attributes=False), 'read-only adapter changed beyond typed raw-zero predicate'
    hpath = OUT / 'qualification/h100/identity.json'
    assert sha(hpath) == patch['original_H100_identity_SHA']
    h = read(hpath)
    assert h['helpers'] == old_helpers
    assert [l['arm'] for l in h['launches']] == ['P-GRB', 'M-B', 'MB-D0', 'MB-D1']
    first = Path(h['launches'][0]['destination'])
    assert sha(first / 'producer_receipt.json') == patch['preserved_P_producer_receipt_SHA']
    assert sha(first / 'producer_seal.json') == patch['preserved_P_producer_seal_SHA']
    assert read(first / 'producer_receipt.json')['T_produce'] == patch['preserved_P_T_produce']
    assert all(not Path(l['destination']).exists() for l in h['launches'][1:])
    actual_review_path = OUT / 'review/actual_H100_P_readonly_review.json'
    actual = read(actual_review_path)
    assert actual['status'] == 'ACTUAL_P_FULL_SHADOW_AUDIT_AND_READOUT_OK' and actual['original_raw_unchanged']
    assert actual['actual_source_identity_SHA'] == patch['original_H100_identity_SHA']
    assert actual['later_readonly_audit_helper_SHA'] == sha(ROOT / 'scripts/round121_evidence.py')
    assert actual['producer_receipt_SHA'] == patch['preserved_P_producer_receipt_SHA']
    assert actual['producer_seal_SHA'] == patch['preserved_P_producer_seal_SHA']
    assert actual['endpoint']['complete_seconds'] == patch['preserved_P_T_produce']
    assert actual['endpoint']['formal_protocol_qualified'] and not actual['endpoint']['certificate']
    for name, digest in actual['original_raw_file_SHA'].items():
        assert sha(first / name) == digest
    q_starts, q_seconds = 0, 0.
    fees = []
    for fee_name in ['qualification01', 'qualification02']:
        d = OUT / 'fees' / fee_name
        launch, receipt = read(d / 'launch.json'), read(d / 'receipt.json')
        assert launch['qualification'] and receipt['actual_exit_observed']
        assert receipt['exit_code'] == 1
        q_starts += receipt['conservative_process_starts']
        q_seconds += receipt['outer_seconds_upper']
        fees.append(dict(label=fee_name, receipt_SHA=sha(d / 'receipt.json'),
                         conservative_starts=receipt['conservative_process_starts'], outer_seconds=receipt['outer_seconds_upper']))
    assert q_starts == 4 and 8 - q_starts == 4 and q_seconds < 1800 - 900
    assert 40 - q_starts >= 4 + 21 and 48000 - q_seconds >= 900 + 37800
    assert read(OUT / 'fees/qualification02/01_reference_return.json')['exit_code'] == 0
    continue_tree = ast.parse((ROOT / 'scripts/qualify_round121.py').read_text(encoding='utf-8-sig'))
    function = next(n for n in continue_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'continue_sealed_P')
    code = ast.unparse(function)
    assert "fee_begin(label, 3, 900, True, dict(starts=21, seconds=37800))" in code
    calls = [n for n in ast.walk(function) if isinstance(n, ast.Call)]
    execute_calls = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'execute']
    assert len(execute_calls) == 1 and ast.unparse(execute_calls[0]) == 'execute(l, h)'
    assert "for l in h['launches'][1:]" in code and 'verify(first, h)' in code
    assert 'subprocess' not in code and 'resolve()' not in code and 'finite()' not in code
    assert "assert not Path(l['destination']).exists()" in code
    candidate = read(OUT / 'candidate_identity.json')
    assert candidate['helpers'] == final_wiring['helpers'] and candidate['source_bindings'] == final_wiring['source_bindings']
    assert candidate['campaign_identities']['qualification/h100'] == patch['original_H100_identity_SHA']
    for group in range(1, 6):
        path = OUT / f'campaign/group{group:02d}/identity.json'
        identity = read(path)
        assert identity['helpers'] == final_wiring['helpers'] and identity['source_hashes'] == final_wiring['source_bindings']
        assert candidate['campaign_identities'][f'campaign/group{group:02d}'] == sha(path)
        assert all(not Path(l['destination']).exists() for l in identity['launches'])
    return dict(decision='ACCEPT_CONTINUE_SEALED_P_PLUS_THREE_UNSTARTED_CLI',
                patch_identity_SHA=sha(patch_path), actual_P_readonly_review_SHA=sha(actual_review_path),
                helper_changes=patch['changed_helpers'], adapter_AST_only_change='raw Seed1 zero permits bool/int with value==0; every other AST node unchanged',
                original_H100_identity_SHA=patch['original_H100_identity_SHA'], original_H100_identity_unchanged=True,
                original_candidate_and_helper_freeze_and_adapter_source_preserved=True,
                P_producer_receipt_SHA=patch['preserved_P_producer_receipt_SHA'], P_producer_seal_SHA=patch['preserved_P_producer_seal_SHA'],
                preserved_P_T_produce=patch['preserved_P_T_produce'], P_existing_evidence_full_shadow_audit_and_readout_passed=True,
                P_reconstruction=dict(U=actual['endpoint']['U'], L=actual['endpoint']['L'], gap=actual['endpoint']['gap'], certificate=False),
                existing_exporter_and_P_launches_not_repeated=True,
                continuation=dict(wrapper=1, unstarted_CLI=['M-B', 'MB-D0', 'MB-D1'], conservative_starts=4,
                                  outer_cap=900, each_CLI_produce_cap=120,
                                  original_P_verify_only=True, P_verify_clock_includes_elapsed_gap=True),
                previous_failed_fees=fees, paid_qualification_starts=q_starts, paid_qualification_seconds=q_seconds,
                remaining_qualification_starts=8 - q_starts, remaining_qualification_seconds=1800 - q_seconds,
                reserved_formal_starts=21, reserved_formal_nominal_plus_management_seconds=37800,
                actual_flags_review='Journal native_preconditions/full_original/global flags are streamed as numeric 0/1; not_started actual_Optimize is emitted as JSON false; result lifecycle/domain/Start-request flags are emitted as JSON true/false. Real P result flags and all whole-audit branches were actually exercised.',
                limitations='Three remaining real warm CLI and cross-arm H/cohort checks remain pending. This review issued no native or performance certificate and did not alter source raw flags or original clock.')


def minimal_qualification_scope_review():
    """Bounded actual R120 D0 model/native/Start recheck; no native replay."""
    import round121_evidence as evidence
    import round99_pure_start_audit as start_audit
    old_out = OLD / 'results/unified_exact_round120'
    h_identity_path = old_out / 'qualification/h100/identity.json'
    h_identity = read(h_identity_path)
    launch = next(l for l in h_identity['launches'] if l['arm'] == 'MB-D0')
    directory = Path(launch['destination'])
    p = launch['panel']
    assert launch['seed'] == 0
    old_production = read(old_out / 'production_identity.json')
    current_production = read(OUT / 'production_identity.json')
    assert old_production['production_PE_SHA'] == current_production['production_PE_SHA']
    assert old_production['DLL_SHA'] == current_production['DLL_SHA']
    assert old_production['source_bindings'] == current_production['source_bindings']
    audit = read(directory / 'audit.json')
    assert audit['passed'] and audit['native_proof_qualified']
    pair = read(directory / 'external/round120_root_pair.json')
    event = read(directory / 'round120_extended_verification.json')['event_contract']
    assert event['installed'] == 1 and event['actual_extended_Optimize'] == 2
    installed = Path(event['install_events'][0]['path'])
    context = evidence.ArmModels()
    try:
        fact, model = context.model_contract(OLD, p, installed, 'MB-D0')
    finally:
        context.clear()
    assert fact['original_rows_types_bounds_objective_equal']
    assert fact['rows'] == 9355 and fact['columns'] == 3533 and fact['extension']['conditional'] is False
    assert model['types']['r120_h'] == 'B' and model['bounds']['r120_h'] == (0., 1.)
    assert all(model['types'][name] == 'C' for name in model['types'] if name.startswith(('p_', 'd_')))
    native_checks = []
    for path in sorted((directory / 'external/native_logs').glob('*.round120.native.json')):
        native = read(path)
        assert native['model_SHA'] == sha(installed) and native['h_type'] == 'B'
        assert native['h_LB'] == 0 and native['h_UB'] == 1 and native['h_BranchPriority'] == 0
        assert native['objective_delta'] == 0 and native['complete_objective_row_matches_native']
        assert q(native['lower_base']) <= q(pair['a'])
        assert q(native['lower_base']) + q(native['lower_delta']) <= q(pair['m'])
        assert q(native['upper_base']) >= q(pair['m'])
        assert q(native['upper_base']) + q(native['upper_delta']) >= q(pair['b'])
        assert q(native['objective_base']) + q(native['objective_constant']) <= min(q(pair['beta0']), q(pair['beta1']))
        native_checks.append(dict(path=str(path), SHA=sha(path), binary64_conservative_endpoint_recomputed=True,
                                  h_type='B', h_bounds=[0, 1], objective_delta=0, actual_ObjCon=native['objective_constant']))
    starts = [(path, read(path)) for path in sorted((directory / 'external/native_logs').glob('*.round68.start.json'))]
    submitted = [(path, meta) for path, meta in starts if meta['submitted'] and meta['model_sha256'] == sha(installed)]
    assert len(submitted) == 2
    original_root = start_audit.ROOT
    start_audit.ROOT = OLD
    try:
        start_checks = start_audit.audit_model(installed, submitted, 'm-binary')
    finally:
        start_audit.ROOT = original_root
    assert all(v['per_column_restored_type_checked'] and v['ordered_native_columns_checked'] for v in start_checks)
    actual_p = read(OUT / 'review/actual_H100_P_readonly_review.json')
    actual_mb = read(OUT / 'review/actual_H100_MB_readonly_review.json')
    assert actual_p['status'] == 'ACTUAL_P_FULL_SHADOW_AUDIT_AND_READOUT_OK'
    assert actual_mb['status'] == 'ACTUAL_MB_FULL_SHADOW_AUDIT_AND_READOUT_OK'
    assert actual_mb['recovered_call_count'] == 2 and actual_mb['actual_Optimize_in_historical_record'] == 5
    fees = []
    for name in ['qualification01', 'qualification02', 'qualification03']:
        path = OUT / 'fees' / name / 'receipt.json'
        value = read(path)
        fees.append(dict(name=name, SHA=sha(path), starts=value['conservative_process_starts'], outer_seconds=value['outer_seconds_upper']))
    paid_starts = sum(v['starts'] for v in fees)
    paid_seconds = sum(v['outer_seconds'] for v in fees)
    assert paid_starts == 6 and 8 - paid_starts == 2
    d0 = OUT / 'qualification/h100/raw/03_H100_S1_MB-D0'
    d1 = OUT / 'qualification/h100/raw/04_H100_S1_MB-D1'
    assert not d0.exists() and not d1.exists()
    report = dict(decision='MINIMAL_COMPOSITION_CAN_COVER_REQUIRED_QUALIFICATION_IF_FINAL_D1_CLI_FULL_AUDIT_PASSES',
                  execution_admission_now=False, interpretation='Goal section 6 recommends the four-H100-CLI package with the word 建议, while requiring reuse of the already-passed R120 qualification and preserving actual necessary settings/types/Start/domain/clock evidence. The formal 16 arms and 18 pairs remain mandatory and unchanged.',
                  independent_interpretation=True, no_standard_weakened=True,
                  old_D0_actual_evidence=dict(source=str(directory), H100_identity_SHA=sha(h_identity_path),
                    audit_SHA=sha(directory / 'audit.json'), model_SHA=sha(installed),
                    complete_model_rechecked=fact, actual_native_checks=native_checks, actual_complete_Start_rechecks=start_checks,
                    original_PE_DLL_all_source_bindings_identical=True, historical_Seed=0, installed=1, actual_extended_Optimize=2),
                  R121_actual_P=dict(review_SHA=sha(OUT / 'review/actual_H100_P_readonly_review.json'), full_audit_and_readout=True, Seed=1),
                  R121_actual_MB=dict(review_SHA=sha(OUT / 'review/actual_H100_MB_readonly_review.json'), full_audit_and_readout=True, Seed=1,
                                     original_T_produce=actual_mb['original_T_produce'], native_Optimize=5, LP=3, MIP=2),
                  prospective_last_D1_requirement='Run exactly the never-started fixed H100 D1 Seed1 position and audit every naturally occurring call, actual model/type/Start/parameter/three-row/scope/return and full H semantics. If naturally unexposed, report it; no artificial proof, weak H or extra native diagnostic is permitted.',
                  H100_D0_Seed1=dict(state='NOT_STARTED', not_replaced_with_other_Seed=True,
                                    limitation='No direct H100 D0 Seed1 CLI observation; rely on frozen R120 D0 actual native model/Start plus shared Seed1 adapter/native setting evidence. This is an explicit qualification coverage limit.'),
                  formal_F2_D0_Seed1_remains_mandatory=True, formal_arms=16, formal_pairs=18,
                  forbidden_claims=['H100 four Seed1 CLI completed', 'H100 D0 Seed1 actually tested', 'old D0 Seed0 is a current Seed1 measurement'],
                  fees=fees, paid_qualification_starts=paid_starts, paid_qualification_seconds=paid_seconds,
                  remaining_qualification_starts=8-paid_starts, remaining_qualification_seconds=1800-paid_seconds,
                  next_maximum_native_plan=dict(wrapper=1, child_D1=1, total_starts=2, no_other_launch_available=True),
                  stop_rule='Any unresolved necessary identity, model, Start, scope, return, clock or native correctness gap means BLOCKED. No attempt may exceed qualification 8 starts/1800 seconds. Final D1 success is not presumed.',
                  reviewer_Optimize=0, reviewer_native_starts=0, historical_carriers_restored=0)
    destination = OUT / 'review/minimal_qualification_scope_review.json'
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(decision=report['decision'], historical_D0_full_Start_vectors=len(start_checks),
                         historical_D0_actual_native_endpoints=len(native_checks), paid_starts=paid_starts,
                         paid_seconds=paid_seconds, remaining_starts=8-paid_starts, Optimize=0, native_starts=0)))
    return report


def bind_minimum_admission():
    gate_path = OUT / 'review/pre_contract.json'
    gate = read(gate_path)
    previous_gate_SHA = sha(gate_path)
    actual_bindings = {name: sha(ROOT / name) for name in gate['source_bindings']}
    assert actual_bindings == gate['source_bindings']
    wiring = final_wiring_review(actual_bindings)
    minimum_path = OUT / 'qualification/minimum_admission_plan.json'
    minimum = read(minimum_path)
    assert minimum['final_helpers'] == wiring['helpers'] and minimum['source_bindings'] == actual_bindings
    assert minimum['formal_positions_unchanged'] == 16 and minimum['formal_pairs_unchanged'] == 18
    assert minimum['formal_argv_SHA'] == wiring['argv_SHA'] and minimum['protocol_SHA'] == wiring['protocol_SHA']
    assert minimum['last_parent_starts'] == 2 and minimum['last_parent_cap'] == 600
    scope_path = OUT / 'review/minimal_qualification_scope_review.json'
    scope = read(scope_path)
    assert scope['decision'] == 'MINIMAL_COMPOSITION_CAN_COVER_REQUIRED_QUALIFICATION_IF_FINAL_D1_CLI_FULL_AUDIT_PASSES'
    mb_path = OUT / 'review/actual_H100_MB_readonly_review.json'
    mb = read(mb_path)
    assert mb['status'] == 'ACTUAL_MB_FULL_SHADOW_AUDIT_AND_READOUT_OK' and mb['original_raw_unchanged']
    assert mb['later_readonly_audit_helper_SHA'] == sha(ROOT / 'scripts/round121_evidence.py')
    assert mb['shadow_audit_summary']['passed'] and mb['endpoint']['formal_protocol_qualified']
    old_source = OUT / 'qualification/Seed1_evidence_adapter_bool_fix_only.py'
    old_ast = ast.parse(old_source.read_text(encoding='utf-8-sig'))
    new_ast = ast.parse((ROOT / 'scripts/round121_evidence.py').read_text(encoding='utf-8-sig'))
    fn = next(n for n in new_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'qualify_seed')
    fn.body = [n for n in fn.body if not ((isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'scope_owner' for t in n.targets))
                                       or isinstance(n, ast.If) and ast.unparse(n.test) == 'scope_owner is None')]
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and ast.unparse(node.func) == 'logs.build':
            node.keywords = [k for k in node.keywords if k.arg != 'model_parser']
    assert ast.dump(old_ast, include_attributes=False) == ast.dump(new_ast, include_attributes=False)
    source = (ROOT / 'scripts/round121_evidence.py').read_text(encoding='utf-8-sig')
    assert "assert isinstance(scope_owner,ArmModels)" in source and 'scope_owner.data(path)[1][0]' in source
    hpath = OUT / 'qualification/h100/identity.json'
    assert sha(hpath) == minimum['original_H100_identity_SHA']
    h = read(hpath)
    plain, warm, d0, d1 = h['launches']
    assert [l['arm'] for l in h['launches']] == ['P-GRB', 'M-B', 'MB-D0', 'MB-D1']
    for launch in [plain, warm]:
        directory = Path(launch['destination'])
        preserved = minimum['preserved_producers'][launch['arm']]
        assert sha(directory / 'producer_receipt.json') == preserved['receipt_SHA']
        assert sha(directory / 'producer_seal.json') == preserved['seal_SHA']
        assert read(directory / 'producer_receipt.json')['T_produce'] == preserved['T_produce']
    assert not Path(d0['destination']).exists() and not Path(d1['destination']).exists()
    assert read(Path(plain['destination']) / 'audit.json')['passed']
    for name, digest in mb['original_raw_file_SHA'].items():
        assert sha(Path(warm['destination']) / name) == digest
    tree = ast.parse((ROOT / 'scripts/qualify_round121.py').read_text(encoding='utf-8-sig'))
    last = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'minimal_final')
    last_text = ast.unparse(last)
    assert 'fee_begin(label, 1, 600, True, dict(starts=21, seconds=37800))' in last_text
    execute = [n for n in ast.walk(last) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'execute']
    assert len(execute) == 1 and ast.unparse(execute[0]) == 'execute(d1, h)'
    assert 'verify(mb, h)' in last_text and 'subprocess' not in last_text and 'finite()' not in last_text
    assert 'H100_four_Seed1_actual_CLI=False' in last_text and '[mb, d1]' in last_text
    assert scope['paid_qualification_starts'] == 6 and scope['paid_qualification_seconds'] + 600 <= 1800
    candidate = read(OUT / 'candidate_identity.json')
    assert candidate['helpers'] == wiring['helpers'] and candidate['source_bindings'] == actual_bindings
    assert candidate['campaign_identities']['qualification/h100'] == sha(hpath)
    for group in range(1, 6):
        identity_path = OUT / f'campaign/group{group:02d}/identity.json'
        identity = read(identity_path)
        assert identity['helpers'] == wiring['helpers'] and identity['source_hashes'] == actual_bindings
        assert candidate['campaign_identities'][f'campaign/group{group:02d}'] == sha(identity_path)
        assert all(not Path(l['destination']).exists() for l in identity['launches'])
    minimum_review = dict(decision='ACCEPT_COMPOSED_MINIMUM_PENDING_ACTUAL_D1',
        no_formal_performance_admission=True, minimum_plan_SHA=sha(minimum_path),
        actual_MB_full_audit_and_readout_SHA=sha(mb_path), independent_old_D0_native_Start_reuse_review_SHA=sha(scope_path),
        cache_owner_repair_AST_only=True, scope_checks_not_skipped=True,
        actual_MB_raw_and_seal_clock_unchanged=True, actual_P_raw_and_seal_clock_unchanged=True,
        H100_D0_Seed1='NOT_STARTED; direct Seed1 qualification absent, explicitly reuse unchanged R120 D0 native model/type/Start',
        last_fixed_D1_CLI_required=True, last_attempt=dict(parent=1, D1_child=1, launches=2, outer_cap_seconds=600),
        paid_qualification_starts=6, paid_qualification_seconds=scope['paid_qualification_seconds'],
        remaining_qualification_starts=2, remaining_qualification_seconds=1800-scope['paid_qualification_seconds'],
        full_formal_obligation_preserved=dict(arms=16, pairs=18, starts=21, nominal_plus_management_seconds=37800),
        failure_limit='Last D1 must pass actual complete audit and H comparison; any necessary unresolved gap is BLOCKED. No additional qualification launch fits the 8-start cap.',
        disclosure='The four-CLI design in section 6 is explicitly suggested. This composed minimum preserves necessary mathematical/native criteria and the unchanged formal plan; it does not claim H100 D0 Seed1 was run.')
    gate.update(decision='ACCEPT', status='ACCEPT_COMPOSED_MINIMUM_PENDING_ACTUAL_D1',
                admission_scope='One last qualification parent plus exactly the never-started H100 D1 Seed1 CLI; no formal performance admission yet.',
                reviewer_script_SHA=sha(__file__), previous_pre_contract_SHA=previous_gate_SHA,
                helpers=wiring['helpers'], source_bindings=actual_bindings, final_wiring=wiring,
                independent_in_memory_fixtures=in_memory_fixtures(), minimum_admission=minimum_review)
    gate['limitations'][0] = 'Real P and M-B Seed1 full audits/readouts pass. H100 D0 Seed1 is explicitly NOT_STARTED; frozen R120 D0 full native matrix/type/Start evidence is reused. One final real D1 Seed1 CLI plus necessary audit/H comparison is still required. No formal performance admission.'
    for name in ['review/actual_H100_MB_readonly_review.json', 'review/minimal_qualification_scope_review.json']:
        gate['restrictions']['allowed_outputs'].append('results/unified_exact_round121/' + name)
    gate['minimum_admission_binding_UTC'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    gate_path.write_text(json.dumps(gate, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    md = OUT / 'review/pre_contract.md'
    text = md.read_text(encoding='utf-8')
    text += ('\nCurrent final minimum gate: **ACCEPT_COMPOSED_MINIMUM_PENDING_ACTUAL_D1**. Qualification03 sealed the real M-B Seed1 endpoint, then failed in read-only cache ownership: a newly parsed model was not registered in the active ArmModels scope path cache. The repair chooses that owner\'s pure parser and retains every scope/hash/type/Start check. An independent AST comparison found no other adapter change. The reviewer passed the full M-B inherited audit and item/reconcile/finalize in a deleted output overlay, with all original bytes and producer seal/clock unchanged. Five actual calls (3 LP, 2 MIP), p/d type C, 9352 rows and 3532 columns were audited; the complete endpoint is U=0.160589067255049, L=0.16058906725504898 at the original 89.6098965-second T_produce.\n\n'
             'The minimum scope was checked against section 6\'s suggested four-CLI design. The reviewer rechecked R120\'s actual D0 complete installed model (9355 rows/3533 columns), both actual native h/ObjCon/three-row endpoint audits and both complete submitted/read-back Start vectors, under identical production PE/DLL/source identity. Together with real P/M-B Seed1, the last D1 Seed1 can cover the new shared Seed1 and extension wiring. **H100 D0 Seed1 is NOT_STARTED** and never counted as tested; lack of its direct Seed1 qualification is explicit. The formal F2 D0 Seed1 arm and all 16 formal arms/18 pairs remain mandatory.\n\n'
             'All failed fees remain charged: 6 starts and 423.4524049759 seconds. Exactly 2 qualification starts and 1376.5475950241 seconds remain. The last permitted entry is 1 parent plus the fixed D1 child, 600 outer seconds, with 21 formal starts and 37800 nominal/management seconds reserved. It verifies existing MB, runs only unstarted D1, and cannot repeat P/MB/exporter or launch D0. Final D1 must pass complete actual audit and full H comparison; unresolved necessary evidence means BLOCKED. This gate does not presume success or issue formal performance admission.\n')
    md.write_text(text, encoding='utf-8')
    print(json.dumps(dict(decision='ACCEPT', minimum_admission=minimum_review['decision'],
                          helpers=len(wiring['helpers']), sources=len(actual_bindings), native_starts=0, Optimize=0)))
    return minimum_review


def run():
    started = time.perf_counter()
    previous_review = read(OUT / 'review/pre_contract.json') if (OUT / 'review/pre_contract.json').is_file() else None
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
    reentry = qualification01_reentry_review(final_wiring, previous_review) if previous_review else None
    continuation = qualification02_continuation_review(final_wiring)
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
                  qualification01_reentry=reentry,
                  qualification02_continuation=continuation,
                  old_saved_h_reselection=[old_h_review(role) for role in ['F2', 'R98-C2']],
                  restrictions=dict(Optimize=0, native_starts=0, compiles=0, Git_commands=0,
                                    research_input_files_written=0, production_files_modified=0,
                                    allowed_outputs=['scripts/round121_precontract_review.py',
                                                     'results/unified_exact_round121/review/pre_contract.json',
                                                     'results/unified_exact_round121/review/pre_contract.md',
                                                     'results/unified_exact_round121/review/h_reselection_sources/**',
                                                     'explicitly authorized isolated system-temp zero/not_started fixture files, removed after replay']),
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
    if reentry:
        lines += ['', '**Qualification01 reentry: ACCEPT for actual qualification only.** Qualification01 stopped before its exporter or any native child: the zero-fixture result omitted reported F, which the unchanged physical reader correctly requires. Its failed parent remains charged as 1 conservative start and 16.0007817745 outer seconds; no launch or cost was refunded.', '',
                  'The independent replay then caught the subsequent not_started fixture using an absolute system-temp log path, which the unchanged portable-path rule rejects. The parent fixed only the fixture result to include F=0 and that log path to relative `raw/missing.log`. No production or reader standard was changed. Every other helper and all production source bindings match the previous review.', '',
                  'The actual current zero/not_started statements were isolated from the fixture AST and executed in a real system temp directory, with the original complete physical/full_fleet/event predicates and call-view body. The empty fleet has G=P=F=0, duration=0, pickups=0 and return load=0; D1 is unexposed. The subsequent log view has no actual call or binding. A result without F still fails the original physical requirement. The isolated directory was removed after checking its resolved cleanup boundary.', '',
                  f"The final gate is rebound to the corrected helper, argv and protocol. Qualification has {reentry['remaining_qualification_starts']} starts and {reentry['remaining_qualification_seconds']:.10f} seconds left, sufficient for the fixed next parent plus five children (6 starts, 1200 outer-second cap), with all 21 formal starts and 37800 nominal/management seconds still reserved. Actual Seed1 CLI qualification remains pending."]
    lines += ['', 'For public old-witness replay, run `python -B scripts/round121_precontract_review.py --h-only`. It reads the local `review/h_reselection_sources` snapshot: exactly the two original D0 witness/base-matrix files and their historical records, plus extracted actual D1 three rows and provenance. It writes nothing, needs no PE/DLL or original worktree, and performs no Optimize. The complete D1 matrix is reconstructed from the independently verified identical original rows plus those actual three rows. No other LP primal, MPS, carrier or historical restoration was added.', '',
              'Executed by this reviewer: standard-library Python arithmetic and read-only file access; 0 Optimize, 0 native starts, 0 compilation, 0 Git commands. Persistent writes were limited to this reviewer script, the two permitted review files, and the explicitly authorized minimal h snapshot. The explicitly authorized isolated temp fixture files were removed. Snapshot source absolute paths and SHA256 values are recorded.', '', 'Limitations:', '']
    lines += ['- ' + limitation for limitation in report['limitations']]
    (review_dir / 'pre_contract.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], inputs=len(new_evidence), pairs=pair_count,
                          h_results=[{'role': v['role'], 'result': v['result']} for v in report['old_saved_h_reselection']],
                          Optimize=0, native_starts=0, engineering_seconds=report['engineering_seconds'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-h-sources', action='store_true')
    parser.add_argument('--h-only', action='store_true', help='Public replay from local minimal sources; no PE/DLL, native, Git, or writes')
    parser.add_argument('--actual-p-review', action='store_true', help='Bounded read-only real P replay with temporary derived-output shadow')
    parser.add_argument('--actual-mb-review', action='store_true', help='Bounded read-only real M-B replay with temporary derived-output shadow')
    parser.add_argument('--minimal-scope-review', action='store_true', help='Bounded original D0 native/Start reuse audit and explicit final-D1 minimum scope')
    parser.add_argument('--bind-minimum', action='store_true', help='Bind the final fixed D1-only qualification entry after independent scope and real MB review')
    args = parser.parse_args()
    if args.snapshot_h_sources:
        snapshot_h_sources()
    elif args.actual_p_review:
        actual_P_readonly_review()
    elif args.actual_mb_review:
        actual_P_readonly_review('M-B')
    elif args.minimal_scope_review:
        minimal_qualification_scope_review()
    elif args.bind_minimum:
        bind_minimum_admission()
    elif args.h_only:
        print(json.dumps(dict(roles=[old_h_review(role) for role in ['F2', 'R98-C2']], Optimize=0, native_starts=0), indent=2, allow_nan=False))
    else:
        run()
