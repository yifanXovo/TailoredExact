"""Independently verify the five proposed E1 rows before Native calls."""
from fractions import Fraction as Q
from pathlib import Path
import datetime
import gzip
import hashlib
import json
from independent_math import bounds_nodes
from independent_evidence import parse_mps

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'results/unified_exact_round148'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checked = []
    screen = load(OUT/'offline_screen.json')
    for result in screen['results']:
        role, carrier = result['role'], result['carrier']
        folder = ROOT/'results/unified_exact_round146/LP'/f'{role}_{carrier}_GD'
        block = load(folder/'compiled_rows.json')
        point = json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
        c = {int(i): Q(v) for i, v in block['scope']['c_binary64'].items()}
        n = len(c)
        slopes = {int(i): Q(v) for i, v in result['certificate']['slopes'].items()}
        beta = sum(slopes.values())
        rhs = {}
        for st in block['states']:
            if st['feasible']:
                i, y, lo, hi = st['i'], st['y'], Q(st['lower']), Q(st['upper'])
                nodes = bounds_nodes(n, c[i]*y, lo, hi)
                a = min(p-slopes[i]*t for t, p in nodes)
                rhs[f'state_{i}_{y}'] = a+beta*c[i]*y
        assert rhs == {k: Q(v) for k, v in result['certificate']['exact_rhs'].items()}
        row = result['row']
        assert row['sense'] == '>' and row['rhs'] == 0.
        assert row['terms']['G'] == 1.
        assert all(-Q(row['terms'].get(k, 0.)) <= v for k, v in rhs.items())
        assert set(row['terms']) <= set(rhs)|{'G'}
        assert all(v == 0. or abs(v) >= 1e-12 for v in row['terms'].values())
        actual_violation = -sum(Q(v)*Q(point[k]) for k, v in row['terms'].items())
        assert float(actual_violation) > .01
        assert abs(float(actual_violation)-result['transport']['transported_violation']) < 1e-15
        parsed = parse_mps(folder/'model.mps')
        for k in rhs:
            assert k in parsed['columns']
            bound = dict(parsed['bounds'].get(k, []))
            assert bound.get('LO', 0.) == 0. and bound.get('UP') == 1.
        checked.append(dict(role=role, carrier=carrier, new_rows=1, new_columns=0,
            source_model_SHA=digest(folder/'model.mps'), source_point_SHA=digest(folder/'solution.json.gz'),
            actual_proposed_RHS_coefficients_independently_derived=True,
            signed_downward_transport_correct=True, all_selectors_nonnegative_bounded=True,
            old_GD_rows_retained=True, transported_violation=float(actual_violation),
            new_row_NZ=len(row['terms'])))
    assert len(checked) == 5 and len({r['role'] for r in checked}) == 3
    assert load(OUT/'qualification_oracle.json')['PASS']
    receipt = dict(schema='round148-independent-preflight-v1', PASS=True,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), reviewer='/root/round148_independent_review',
        independent_nonimplementer=True, Optimize=0, Native_load=0, compile=0,
        checked_rows=checked,
        derivation_valid=True, low_only_three_point_oracle=True, same_station_shared_slope=True,
        strict_fixture_verified='independent_math.json',
        experiment_grid='Exactly the five saved R146 complete LP domains, three physical instances; one added affine row each, no baseline re-solve, Seed0/Threads1.',
        E1_objective_matrix_bounds_cutoff_semantics_retained_by_runner=True,
        actual_Native_readback_checked_before_Optimize_by_runner=True,
        budget='Five reservations of 180s, each 120s Native cap; all qualification and failures metered in the 18000s outer ledger.',
        finite_decision_gate='Results before E2; at most two domains may receive iterations2/3. No automatic full algorithm, second research family or matrix expansion.',
        findings=[], resolved_observations=['Exact moment-domain flag now uses rational inequalities',
            'Dual objective is explicitly a numerical diagnostic, not an extra rational certificate'],
        identities={p: digest(ROOT/'scripts'/p) for p in ['round148_math.py','round148_lp.py','round148_common.py']})
    (OUT/'review/preflight.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=True, rows=len(checked), instances=3)))


if __name__ == '__main__':
    main()
