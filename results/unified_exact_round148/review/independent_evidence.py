"""Independent MPS/receipt audit, with zero solver imports or solver calls."""
from fractions import Fraction as Q
from pathlib import Path
import collections
import datetime
import gzip
import hashlib
import json
import math
import os
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'results/unified_exact_round148'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_mps(path):
    """Sufficient free MPS parser for these continuous linear models.

    Independently parse every original/new coefficient, objective, RHS and bound.
    Reject unsupported range/quad constructs rather than silently ignore them.
    """
    rows, columns, rhs, bounds, obj, sense = {}, {}, {}, {}, None, 'MIN'
    section = None
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('*'):
            continue
        fields = line.split()
        if not line[0].isspace():
            section = fields[0]
            assert section in {'NAME', 'OBJSENSE', 'ROWS', 'COLUMNS', 'RHS', 'BOUNDS', 'ENDATA'}
            continue
        if section == 'OBJSENSE':
            sense = fields[0]
        elif section == 'ROWS':
            st, name = fields
            if st == 'N':
                assert obj is None
                obj = name
            else:
                assert st in ('G', 'L', 'E')
                rows[name] = st
        elif section == 'COLUMNS':
            assert 'MARKER' not in line
            name = fields[0]
            terms = columns.setdefault(name, {})
            assert len(fields) in (3, 5)
            for j in range(1, len(fields), 2):
                assert fields[j] not in terms
                terms[fields[j]] = float(fields[j+1])
        elif section == 'RHS':
            assert len(fields) in (3, 5)
            for j in range(1, len(fields), 2):
                assert fields[j] not in rhs
                rhs[fields[j]] = float(fields[j+1])
        elif section == 'BOUNDS':
            typ, _, name, *value = fields
            bounds.setdefault(name, []).append((typ, float(value[0]) if value else None))
    assert obj is not None and sense == 'MIN'
    row_names = set(rows)|{obj}
    assert all(set(c) <= row_names for c in columns.values())
    return dict(rows=rows, columns=columns, rhs=rhs, bounds=bounds, objective=obj, sense=sense)


def check_one(folder):
    result = load(folder/'result.json')
    role, carrier, iteration = result['role'], result['carrier'], result['iteration']
    oldfolder = ROOT/'results/unified_exact_round146/LP'/f'{role}_{carrier}_GD'
    old = parse_mps(oldfolder/'model.mps')
    new = parse_mps(folder/'model.mps')
    assert old['objective'] == new['objective'] and old['sense'] == new['sense']
    assert old['bounds'] == new['bounds']
    assert old['rhs'] == {k: v for k, v in new['rhs'].items() if k in old['rhs']}
    assert set(old['columns']) == set(new['columns'])
    assert old['rows'] == {k: v for k, v in new['rows'].items() if k in old['rows']}
    for variable, coefficients in old['columns'].items():
        assert coefficients == {k: v for k, v in new['columns'][variable].items() if k in old['rows'] or k == old['objective']}
    added = sorted(set(new['rows'])-set(old['rows']))
    assert len(added) == iteration
    assert all(name.startswith('r148_shared_S_') for name in added)
    construction = load(folder/'construction.json')
    row = construction['new_row']
    assert new['rows'][row['name']] == 'G'
    assert new['rhs'].get(row['name'], 0.) == row['rhs'] == 0.
    actual = {v: coeffs[row['name']] for v, coeffs in new['columns'].items() if row['name'] in coeffs}
    assert actual == row['terms']
    exact_rhs = {k: Q(v) for k, v in construction['certificate']['exact_rhs'].items()}
    assert all(-Q(actual.get(k, 0.)) <= v for k, v in exact_rhs.items())
    assert all(abs(v) >= 1e-12 for v in actual.values())
    point = json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
    assert set(point) == set(new['columns'])
    assert digest(folder/'model.mps') == result['model_SHA']
    assert digest(folder/'solution.json.gz') == result['solution_SHA']
    values = collections.defaultdict(list)
    for v, coefficients in new['columns'].items():
        for name, a in coefficients.items():
            values[name].append(a*point[v])
    activities = {k: math.fsum(v) for k, v in values.items()}
    high = 0.
    for name, sense in new['rows'].items():
        residual = activities.get(name, 0.)-new['rhs'].get(name, 0.)
        high = max(high, max(0., -residual) if sense == 'G' else max(0., residual) if sense == 'L' else abs(residual))
    objective = activities[new['objective']]-new['rhs'].get(new['objective'], 0.)
    assert high <= 1e-6
    assert abs(objective-result['L']) < 1e-9
    assert result['qualified'] and result['Status'] == 2
    assert result['Seed'] == 0 and result['Threads'] == 1
    assert max(result['quality'].values()) <= 1e-6
    oldresult = load(oldfolder/'result.json')
    assert result['old_L'] == oldresult['L']
    assert abs(result['gain']-(objective-oldresult['L'])) < 1e-9
    call, returned = load(folder/'call.json'), load(folder/'return.json')
    assert call['model_SHA'] == result['model_SHA']
    assert returned['Status'] == 2 and call['Seed'] == 0 and call['Threads'] == 1
    return dict(domain=f'{role}_{carrier}', iteration=iteration, original_rows=len(old['rows']),
        original_columns=len(old['columns']), original_NZ=sum(len(v) for v in old['columns'].values()),
        added_rows=added, independently_parsed_original_semantics_identical=True,
        actual_signed_row_coefficients_valid=True, actual_coefficients_equal_declared=True,
        independent_full_matrix_residual=high, independent_objective=objective,
        old_L=oldresult['L'], gain=objective-oldresult['L'],
        new_row_NZ=len(actual), Native_call_and_return_match=True,
        exact_rational_optimality_certificate_claim=False)


def main():
    start = time.perf_counter()
    results = sorted(OUT.glob('LP/*/iteration*/result.json'))
    assert results
    checks = [check_one(p.parent) for p in results]
    fee_rows, current_outer_pending = [], []
    current_label = os.environ.get('ROUND140_METERED_PARENT_LABEL')
    for path in sorted((OUT/'fees').glob('*/launch.json')):
        launch = load(path)
        receipt_path = path.parent/'receipt.json'
        if not receipt_path.exists():
            assert current_label and path.parent.name == current_label, 'Unclosed noncurrent fee'
            current_outer_pending.append(dict(label=current_label, kind=launch['kind'],
                parent_closes_and_charges_after_auditor_exit=True,
                current_seconds_not_added_to_audited_closed_fee_sum=True))
            continue
        receipt = load(receipt_path)
        assert receipt['exit_observed']
        fee_rows.append(dict(label=path.parent.name, kind=launch['kind'],
                             exit_code=receipt['exit_code'], seconds=receipt['G1_seconds']))
    receipt = dict(schema='round148-independent-evidence-review-v1', PASS=True,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer='/root/round148_independent_review',
        implementation_SHA256=digest(Path(__file__)),
        Optimize=0, Native_load=0, compile=0, seconds=time.perf_counter()-start,
        checked_LPs=checks, fee_rows=fee_rows, current_outer_pending=current_outer_pending,
        summed_G1_seconds=math.fsum(r['seconds'] for r in fee_rows))
    (OUT/'review/independent_evidence.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=True, LPs=len(checks), total_fee_seconds=receipt['summed_G1_seconds'])))


if __name__ == '__main__':
    main()
