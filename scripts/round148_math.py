"""Exact finite low-deviation oracle; pure-selector conservative transport.

This is a diagnostic implementation. No solver, runtime load or process starts
at import. Every station shares one actual finite rational slope across states.
"""
from fractions import Fraction as F
from itertools import combinations
import math
import time


def station_data(block):
    spec = block['scope']
    c = {int(i): F(v) for i, v in spec['c_binary64'].items()}
    n = len(c)
    data = {i: [] for i in c}
    for state in block['states']:
        if not state['feasible']:
            continue
        i, y = state['i'], state['y']
        lo, hi, r = F(state['lower']), F(state['upper']), c[i] * y
        assert 0 < lo <= hi
        ts = sorted({lo, hi} | ({n * r} if lo <= n * r <= hi else set()))
        nodes = [(t, max(F(0), F(1, n) - r/t)) for t in ts]
        data[i].append(dict(y=y, lo=lo, hi=hi, nodes=nodes))
    return c, data


def alpha(state, b):
    return min(p - b*t for t, p in state['nodes'])


def choose(block, point):
    """Return a finite valid row and exact certificate, even outside moment box.

    Within the moment box, positive state masses make the finite breakpoint
    search exact. Outside it we return an explicit one-station moment row;
    we never label an unbounded dual ray an infinite Gini improvement.
    """
    start = time.perf_counter()
    assert block['applicable']
    c, data = station_data(block)
    S = sum(c[i] * F(point[f'Y_{i}']) for i in c)
    masses = {(i, st['y']): F(point[f"state_{i}_{st['y']}"])
              for i, states in data.items() for st in states}
    stations, moments, rays = [], [], []
    exact_moment_domain = True
    for i, states in sorted(data.items()):
        low = sum(st['lo'] * masses[i, st['y']] for st in states)
        high = sum(st['hi'] * masses[i, st['y']] for st in states)
        exact_moment_domain = exact_moment_domain and low <= S <= high
        moments.append(dict(i=i, lower_slack=float(S-low), upper_slack=float(high-S)))
        if low-S > F(1, 10**8):
            rays.append((low-S, i, 'lower'))
        if S-high > F(1, 10**8):
            rays.append((S-high, i, 'upper'))
        candidates = {F(0)}
        for st in states:
            for (t, p), (u, q) in combinations(st['nodes'], 2):
                candidates.add((q-p)/(u-t))
        def H(b):
            return b*S + sum(masses[i, st['y']] * alpha(st, b) for st in states)
        b = max(candidates, key=lambda b: (H(b), -abs(b), -b))
        stations.append(dict(i=i, b=b, H=H(b), candidates=len(candidates),
                             alpha={st['y']: alpha(st, b) for st in states}))
    if rays:
        _, i, side = max(rays)
        bounds = {st['y']: st['lo'] if side == 'lower' else st['hi'] for st in data[i]}
        # sum D^- s_i - S <= 0, or S - sum D^+ s_i <= 0.
        sign = 1 if side == 'lower' else -1
        rhs = {f"state_{j}_{st['y']}": sign * ((bounds[st['y']] if i == j else F(0)) - c[j]*st['y'])
               for j, states in data.items() for st in states}
        g_coefficient, kind = F(0), 'moment_' + side
    else:
        beta = sum(st['b'] for st in stations)
        by_i = {st['i']: st for st in stations}
        rhs = {f"state_{i}_{st['y']}": by_i[i]['alpha'][st['y']] + beta*c[i]*st['y']
               for i, states in data.items() for st in states}
        g_coefficient, kind = F(1), 'affine_low'
    exact = dict(kind=kind, G=g_coefficient, rhs=rhs)
    certificate = dict(kind=kind, S=str(S), moments=moments,
        minimum_mass=float(min(masses.values())),
        sum_station_H=str(sum(st['H'] for st in stations)),
        slopes={str(st['i']): str(st['b']) for st in stations},
        breakpoint_counts={str(st['i']): st['candidates'] for st in stations},
        exact_rhs={k: str(v) for k, v in rhs.items()},
        seconds=time.perf_counter()-start,
        exact_breakpoint_maximum_on_moment_domain=exact_moment_domain and min(masses.values()) >= 0)
    return exact, certificate


def downward(q):
    """Nonnegative selectors permit componentwise downward RHS rounding.

    Protect nonzero tiny terms from Native's coefficient omission. Negative
    terms are never erased toward zero. All decisions are rational-checked.
    """
    if not q:
        return 0.
    if abs(q) < F(1, 10**12):
        v = -1e-12
    else:
        v = float(q)
        if F(v) > q:
            v = math.nextafter(v, -math.inf)
    assert math.isfinite(v) and F(v) <= q
    return v


def compile_row(exact, point, name):
    q = exact['rhs']
    rounded = {k: downward(v) for k, v in q.items() if v}
    terms = {k: -v for k, v in rounded.items()}
    if exact['G']:
        terms['G'] = float(exact['G'])
    ideal = sum(v * F(point[k]) for k, v in q.items()) - exact['G']*F(point['G'])
    actual = sum(F(v) * F(point[k]) for k, v in rounded.items()) - exact['G']*F(point['G'])
    loss = sum(q[k]-F(rounded.get(k, 0.)) for k in q)
    row = dict(name=name, sense='>', rhs=0., terms=terms)
    certificate = dict(ideal_violation=float(ideal), transported_violation=float(actual),
        box_loss_bound=float(loss), coefficient_loss_direction_PASS=all(F(rounded.get(k, 0.)) <= v for k, v in q.items()),
        pure_selectors=True, columns_added=0, negative_RHS_terms=sum(v < 0 for v in rounded.values()),
        nonzeros=len(terms), G_coefficient=float(exact['G']), Native_tiny_floor=1e-12)
    return row, certificate


def activity(row, point):
    return row['rhs'] - math.fsum(v*point[k] for k, v in row['terms'].items())
