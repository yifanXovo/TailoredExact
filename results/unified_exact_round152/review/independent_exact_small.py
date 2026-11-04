"""Independent stdlib-only verification of the R152 three-station theorem.

No imports from the main implementation and no solver/native/process calls.
MPS decimal strings are interpreted as their loaded binary64 coefficients.
"""
from pathlib import Path
from fractions import Fraction as F
from itertools import product, combinations
from collections import defaultdict
import gzip, hashlib, json, time


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def matrix(p):
    section = None
    senses, rows, rhs, bounds, variables = {}, defaultdict(dict), {}, {}, set()
    for raw in p.read_text().splitlines():
        if not raw or raw.startswith('*'):
            continue
        fields = raw.split()
        if fields[0] in {'NAME', 'ROWS', 'COLUMNS', 'RHS', 'BOUNDS', 'ENDATA'}:
            section = fields[0]
            continue
        if section == 'ROWS':
            senses[fields[1]] = fields[0]
        elif section == 'COLUMNS':
            name = fields[0]
            variables.add(name)
            for j in range(1, len(fields), 2):
                rows[fields[j]][name] = F(float(fields[j+1]))
        elif section == 'RHS':
            for j in range(1, len(fields), 2):
                rhs[fields[j]] = F(float(fields[j+1]))
        elif section == 'BOUNDS':
            kind, _, name, *value = fields
            lo, hi = bounds.get(name, (F(0), None))
            if kind == 'UP':
                hi = F(float(value[0]))
            elif kind == 'LO':
                lo = F(float(value[0]))
            elif kind == 'FX':
                lo = hi = F(float(value[0]))
            else:
                raise AssertionError(('unexpected bound', fields))
            bounds[name] = lo, hi
    return senses, rows, rhs, bounds, variables


def main():
    start = time.perf_counter()
    base = Path(__file__).resolve().parents[1]
    source = base / 'small/v2/heterogeneous_wide'
    result = json.loads((source / 'result.json').read_text())
    with gzip.open(source / 'exact_extension.json.gz', 'rt') as stream:
        extension = {k:F(v) for k,v in json.load(stream).items()}
    c, omega, n = [F(1), F(1,2), F(1,4)], F(1,8), 3

    def evaluate(Y):
        ratio = [a*y for a,y in zip(c,Y)]
        S = sum(ratio)
        A = sum(abs(a-b) for a,b in combinations(ratio,2))
        G = A/(n*S) if S else F(0)
        penalty = omega*sum(abs(a-1) for a in ratio)
        return dict(Y=Y, S=S, G=G, penalty=penalty, phi=G+penalty)

    universe = [evaluate(Y) for Y in product(range(5), repeat=3)
                if 2 <= sum(Y) <= 5]
    assert len(universe) == 49
    assert all(v['G'] <= F(3,4) for v in universe)
    integer_min = min(v['phi'] for v in universe)
    assert integer_min == F(47,240)

    senses, rows, rhs, bounds, variables = matrix(source / 'reference.mps')
    assert variables == set(extension)
    for name, sense in senses.items():
        if sense == 'N':
            continue
        activity = sum(a*extension[k] for k,a in rows[name].items())
        target = rhs.get(name,F(0))
        assert (activity == target if sense == 'E' else
                activity >= target if sense == 'G' else activity <= target), name
    for name in variables:
        lo, hi = bounds.get(name,(F(0),None))
        assert extension[name] >= lo
        assert hi is None or extension[name] <= hi
    reference = sum(a*extension[k] for k,a in rows['OBJ'].items())
    assert reference == F(31,160)

    # Check the ideal conditional GD rows independently, before coefficient
    # rounding. All states receiving positive witness mass have zero terms.
    low_activity = high_activity = F(0)
    for i in range(n):
        for y in range(5):
            choices = [v['S'] for v in universe if v['Y'][i] == y]
            if not choices:
                continue
            low = max(F(0),1-n*c[i]*y/min(choices))
            high = max(F(0),n*c[i]*y/max(choices)-1)
            s = extension[f'state_{i+1}_{y}']
            if s:
                assert low == high == 0
            low_activity += low*s
            high_activity += high*s
    assert n*extension['G'] >= max(low_activity,high_activity)

    thresholds = sorted({c[i]*y for i in range(n) for y in range(1,5)})
    intervals = []
    for j,t in enumerate(thresholds):
        count = [sum(c[i]*v['Y'][i] >= t for i in range(n)) for v in universe]
        ell, upper = min(count), max(count)
        assert rhs.get(f'r152_known_count_{j}_low',F(0)) == ell
        assert rhs.get(f'r152_known_count_{j}_high',F(0)) == upper
        intervals.append(dict(threshold=str(t),lower=ell,upper=upper))

    mixture = [(tuple(p['Y']),F(p['weight'])) for p in result['mixture']]
    assert mixture == [((1,1,2),F(1,4)),((1,1,3),F(1,2)),((1,2,2),F(1,4))]
    assert sum(w for _,w in mixture) == 1
    for i in range(n):
        for y in range(5):
            assert sum(w for Y,w in mixture if Y[i] == y) == extension[f'state_{i+1}_{y}']
    active_joint = [v for v in universe if all(extension[f'state_{i+1}_{y}'] > 0
                                             for i,y in enumerate(v['Y']))]
    assert {v['Y'] for v in active_joint} == {Y for Y,_ in mixture}
    # Y2=2 identifies the third column, Y3=3 the second; residual mass fixes
    # the first. Thus the common distribution is unique, without an LP claim.
    assert [v['Y'] for v in active_joint if v['Y'][1] == 2] == [(1,2,2)]
    assert [v['Y'] for v in active_joint if v['Y'][2] == 3] == [(1,1,3)]
    theta = sum(w*evaluate(Y)['phi'] for Y,w in mixture)
    ap = sum(w*evaluate(Y)['penalty'] for Y,w in mixture)
    assert theta == F(1049,4320) and ap == F(3,32)
    assert theta-reference == F(53,1080)
    assert integer_min-reference == F(1,480)
    assert theta-ap == F(161,1080)
    inputs = {str(p.relative_to(base)):digest(p) for p in
              [source/'result.json',source/'reference.mps',source/'exact_extension.json.gz']}
    output = dict(PASS=True,source_SHA256=inputs,reviewer_script_SHA256=digest(Path(__file__)),
                  enumerated_vectors=125,feasible_inventory_vectors=49,
                  reference_rows=sum(s!='N' for s in senses.values()),reference_variables=len(variables),
                  exact_full_reference_extension=True,ideal_GD_checked=True,
                  exact_threshold_ranges_equal_saved=True,threshold_ranges=intervals,
                  common_distribution_unique=True,reference_objective=str(reference),
                  integer_minimum=str(integer_min),global_strict_gap=str(integer_min-reference),
                  Theta=str(theta),AP=str(ap),Gamma=str(theta-ap),
                  same_marginal_objective_gap=str(theta-reference),
                  integer_minimizers=[v['Y'] for v in universe if v['phi']==integer_min],
                  new_Optimize=0,new_Native_calls=0,new_compiler_calls=0,
                  scope='complete declared inventory block, no route-model extension')
    output['outer_experimental_seconds'] = time.perf_counter()-start
    target = Path(__file__).with_name('independent_exact_small.json')
    assert not target.exists()
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__ == '__main__':
    main()
