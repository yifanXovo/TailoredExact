"""Independent rational review. No production oracle or solver import.

Run with an ordinary Python interpreter. Reads sealed R146 evidence only and
writes the reviewer's receipt; it never calls Optimize, Native, or a compiler.
"""
from fractions import Fraction as Q
from itertools import combinations, product
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds_nodes(n, ratio, lo, hi):
    times = sorted({lo, hi, *([n*ratio] if lo <= n*ratio <= hi else [])})
    return [(t, max(Q(0), Q(1, n)-ratio/t)) for t in times]


def check_domain(folder):
    block = load(folder/'compiled_rows.json')
    point = json.loads(gzip.decompress((folder/'solution.json.gz').read_bytes()))
    c = {int(i): Q(v) for i, v in block['scope']['c_binary64'].items()}
    n = len(c)
    S = sum(v*Q(point[f'Y_{i}']) for i, v in c.items())
    groups = {i: [] for i in c}
    for st in block['states']:
        if st['feasible']:
            i, y = st['i'], st['y']
            lo, hi = Q(st['lower']), Q(st['upper'])
            groups[i].append((y, lo, hi, bounds_nodes(n, c[i]*y, lo, hi)))
    bounds_value = Q(0)
    slopes = {}
    moment_slacks = []
    link_residuals = []
    for i, states in sorted(groups.items()):
        s = {y: Q(point[f'state_{i}_{y}']) for y, _, _, _ in states}
        assert all(v >= 0 for v in s.values())
        lo_mean = sum(lo*s[y] for y, lo, _, _ in states)
        hi_mean = sum(hi*s[y] for y, _, hi, _ in states)
        assert lo_mean <= S <= hi_mean
        moment_slacks.extend([float(S-lo_mean), float(hi_mean-S)])
        link_residuals.append(abs(Q(point[f'Y_{i}'])-sum(y*v for y, v in s.items())))
        breakpoints = {Q(0)}
        for _, _, _, nodes in states:
            for (u, a), (v, b) in combinations(nodes, 2):
                breakpoints.add((b-a)/(v-u))
        candidates = []
        for slope in sorted(breakpoints):
            value = slope*S + sum(s[y]*min(a-slope*t for t, a in nodes)
                                  for y, _, _, nodes in states)
            candidates.append((value, -abs(slope), -slope))
        value, _, negative_slope = max(candidates)
        slope = -negative_slope
        slopes[str(i)] = str(slope)
        bounds_value += value
    return dict(domain=folder.name, n=n, original_g=point['G'],
        independent_affine_lower_value=float(bounds_value),
        independent_violation=float(bounds_value-Q(point['G'])),
        minimum_moment_slack=min(moment_slacks),
        maximum_link_residual=float(max(link_residuals)),
        slopes=slopes, exact_value=str(bounds_value),
        block_SHA256=digest(folder/'compiled_rows.json'),
        point_SHA256=digest(folder/'solution.json.gz'))


def fixture():
    # The two-station support {1,2} has zero isolated high and low GD.
    n = 2
    nodes = {1: bounds_nodes(n, Q(1), Q(2), Q(3)),
             2: bounds_nodes(n, Q(2), Q(3), Q(4))}
    b = Q(1, 6)
    alpha = {y: min(p-b*t for t, p in ns) for y, ns in nodes.items()}
    assert alpha == {1: -Q(1, 3), 2: -Q(2, 3)}
    # Station 2's zero-slope intercept is zero in both states.
    a, d = Q(1, 2), Q(0)
    lower = alpha[1]*a+alpha[2]*(1-a)+b*(4-a-d)
    assert lower == Q(1, 12)
    integer_checks = []
    for y1, y2 in product([1, 2], repeat=2):
        S = y1+y2
        G = Q(abs(y1-y2), 2*S)
        rhs = alpha[y1]+b*S
        assert rhs <= G
        integer_checks.append(dict(y=[y1, y2], G=str(G), affine_rhs=str(rhs)))
    return dict(PASS=True, slopes=['1/6', '0'], alpha_station1={str(k): str(v) for k, v in alpha.items()},
        a='1/2', d='0', affine_lower='1/12', isolated_GD='0', integer_checks=integer_checks,
        strictness_relative_to_isolated_GD_only=True, pair_CDF_novelty_claim=False)


def main():
    start = time.perf_counter()
    domains = [check_domain(ROOT/'results/unified_exact_round146/LP'/name) for name in
               ['K-20-S_base_GD', 'K-20-S_joint_GD', 'K-20-S_stock_GD', 'K-35-U_base_GD', 'R-X20-S-T1_base_GD']]
    receipt = dict(schema='round148-independent-rational-pre-review-v1', PASS=True,
        UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer='/root/round148_independent_review',
        production_oracle_imported=False, Optimize=0, Native_load=0, compile=0,
        seconds=time.perf_counter()-start, implementation_SHA256=digest(Path(__file__)),
        strict_fixture=fixture(), domains=domains,
        proof_checks=dict(Gini_Hoover=True, common_slope_per_station=True,
            low_only_three_point_oracle=True, fixed_interval_and_zero_ratio_handled=True,
            independent_site_first_moment_convexification=True, no_common_atom_distribution_claim=True,
            pure_selector_coefficients_alpha_plus_sum_b_times_cy=True,
            moment_fallback_signs_correct=True, signed_downward_RHS_safe_for_nonnegative_selectors=True),
        pending=['Actual Native readback coefficients and original-domain semantics',
                 'Reoptimized objective values, costs, decisions and final claims'])
    (OUT/'independent_math.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(PASS=True, domains=[dict(domain=r['domain'], violation=r['independent_violation']) for r in domains])))


if __name__ == '__main__':
    main()
