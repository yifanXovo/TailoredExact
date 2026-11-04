"""Independent Fraction reconstruction of the strengthened C3 inventory example.

Stdlib only: no import of the producer's mathematical code, Native API or
solver. The parent runs this once through the serial Round153 outer meter.
"""
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path
import gzip
import hashlib
import json
import math
import time


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'results/unified_exact_round152'
OUT = ROOT/'results/unified_exact_round153/review'
FIXED_SCIENCE = 'd489ec2948f079105e4532a2e06ae4eed9fcd500'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def outward(q, upper):
    value = float(q)
    if (F(value) < q) if upper else (F(value) > q):
        value = math.nextafter(value, math.inf if upper else -math.inf)
    assert F(value) >= q if upper else F(value) <= q
    return F(value)


def load_matrix(path):
    """Small independent MPS reader; decimal fields mean loaded binary64."""
    section = None
    senses, rows, rhs, bounds, variables = {}, defaultdict(dict), {}, {}, set()
    for raw in path.read_text().splitlines():
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
    return senses, dict(rows), rhs, bounds, variables


def main():
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    output_path = OUT/'exact_strict_example.json'
    report_path = OUT/'exact_strict_example.md'
    assert not output_path.exists() and not report_path.exists(), 'Closed verification is not rerun'
    source = OLD/'small/v2/heterogeneous_wide'
    inputs = [source/'reference.mps', source/'exact_extension.json.gz', source/'result.json']
    index_path = OLD/'artifacts/qualification_failures_and_fees.members.json.gz'
    with gzip.open(index_path, 'rt', encoding='utf-8') as stream:
        member_index = {row['member']:row for row in json.load(stream)}
    dependencies = []
    for path in inputs:
        name = path.relative_to(ROOT).as_posix()
        member = member_index[name]
        assert digest(path) == member['SHA256'], name
        dependencies.append(dict(member, commit=FIXED_SCIENCE,
            archive='results/unified_exact_round152/artifacts/qualification_failures_and_fees.zip',
            archive_SHA256='c508887df98f402b7b3048b4cbdd652968015b652c97676f2859f8a8975b3006'))

    senses, rows, rhs, bounds, variables = load_matrix(source/'reference.mps')
    assert sum(sense != 'N' for sense in senses.values()) == 117
    assert len(variables) == 46
    with gzip.open(source/'exact_extension.json.gz', 'rt', encoding='utf-8') as stream:
        old_point = {k:F(v) for k,v in json.load(stream).items()}
    assert set(old_point) == variables and old_point['G'] == F(1,10)
    point = {name:value*F(10,9) if name == 'G' or name.startswith(('state_g_', 'zprod_')) else value
             for name,value in old_point.items()}
    c, n, bm, upper = {1:F(1), 2:F(1,2), 3:F(1,4)}, 3, 2, 5
    support = range(5)
    inventories = [Y for Y in product(support, repeat=n) if bm <= sum(Y) <= upper]
    assert len(inventories) == 49

    def evaluate(Y):
        r = [c[i]*Y[i-1] for i in c]
        S = sum(r)
        A = sum(abs(a-b) for a,b in combinations(r,2))
        G = A/(n*S) if S else F(0)
        H = F(1,8)*sum(abs(a-1) for a in r)
        return dict(S=S, G=G, H=H, phi=G+H)

    true_values = {Y:evaluate(Y) for Y in inventories}
    assert all(value['G'] <= F(3,4) for value in true_values.values())
    sl = min(value['S'] for value in true_values.values())
    su = max(value['S'] for value in true_values.values())
    assert sl == F(1,2) and su == F(9,2)
    L, U = outward(1/su, False), outward(1/sl, True)
    assert L <= F(2,9) and U == 2

    added = []

    def add(name, terms, sense, target=F(0)):
        assert name not in senses
        assert sense in ('G', 'L', 'E')
        terms = {key:F(value) for key,value in terms.items() if value}
        senses[name], rows[name], rhs[name] = sense, terms, F(target)
        added.append(name)

    point['rn_t'] = F(4,9)
    bounds['rn_t'] = (L,U)
    variables.add('rn_t')
    for i in c:
        name = f'rn_Y_{i}'
        variables.add(name)
        bounds[name] = (F(0),None)
        point[name] = [F(4,9),F(5,9),F(10,9)][i-1]
        for y in support:
            w, s = f'rn_w_{i}_{y}', f'state_{i}_{y}'
            variables.add(w)
            bounds[w] = (F(0),U)
            point[w] = F(0)
            add(f'rn_lb_{i}_{y}', {w:1,s:-L}, 'G')
            add(f'rn_ub_{i}_{y}', {w:1,s:-U}, 'L')
        add(f'rn_mass_{i}', {**{f'rn_w_{i}_{y}':1 for y in support},'rn_t':-1}, 'E')
        add(f'rn_inventory_{i}', {name:1,**{f'rn_w_{i}_{y}':-y for y in support if y}}, 'E')
    for name,value in {'rn_w_1_1':F(4,9), 'rn_w_2_1':F(1,3),
                       'rn_w_2_2':F(1,9), 'rn_w_3_2':F(2,9),
                       'rn_w_3_3':F(2,9)}.items():
        point[name] = value
    add('rn_normalization', {f'rn_Y_{i}':c[i] for i in c}, 'E', 1)
    Hterms = {}
    for i,j in combinations(c,2):
        name = f'rn_h_{i}_{j}'
        Hterms[name] = F(1)
        variables.add(name)
        bounds[name] = (F(0),None)
        point[name] = F(1,6) if i == 1 else F(0)
        add(f'rn_abs_p_{i}_{j}', {name:1,f'rn_Y_{i}':-c[i],f'rn_Y_{j}':c[j]}, 'G')
        add(f'rn_abs_m_{i}_{j}', {name:1,f'rn_Y_{i}':c[i],f'rn_Y_{j}':-c[j]}, 'G')
    add('rn_gini', {**Hterms,'G':-n}, 'L')
    assert len(added) == 44
    add('r152_known_RN_stock_low', {**{f'rn_Y_{i}':1 for i in c},'rn_t':-bm}, 'G')
    add('r152_known_RN_stock_high', {**{f'rn_Y_{i}':1 for i in c},'rn_t':-upper}, 'L')

    # Derive the old TC/TC2 coefficient tables independently from exact finite
    # count intervals, then check that they equal the saved old aggregate rows.
    thresholds = sorted({c[i]*y for i in c for y in support if y})
    tc = {(i,y):F(0) for i in c for y in support}
    tc2 = dict(tc)
    constant, previous, intervals = F(0), F(0), []
    for theta in thresholds:
        delta = theta-previous
        counts = [sum(c[i]*Y[i-1] >= theta for i in c) for Y in inventories]
        ell, u = min(counts), max(counts)
        for i,y in tc:
            if c[i]*y >= theta:
                tc[i,y] += delta*(n-u)
                tc2[i,y] += delta*(n-ell-u)
        constant += delta*ell*u
        intervals.append(dict(theta=str(theta),delta=str(delta),ell=ell,u=u))
        previous = theta
    old_H = {f'h_{i}_{j}':F(1) for i,j in combinations(c,2)}
    for oldname,table,b in [('r152_known_TC',tc,F(0)),('r152_known_TC2',tc2,constant)]:
        expected = {**old_H,**{f'state_{i}_{y}':-value for (i,y),value in table.items() if value}}
        assert rows[oldname] == expected and rhs.get(oldname,F(0)) == b, oldname
    for label,table,b in [('NC1',tc,F(0)),('NC2',tc2,constant)]:
        terms = {**Hterms,'rn_t':-b,**{f'rn_w_{i}_{y}':-value for (i,y),value in table.items() if value}}
        assert all(F(float(value)) == value for value in terms.values())
        add(f'r145_{label}', terms, 'G')
    for number,slope,endpoint,sense in [(1,L,bm,'G'),(2,U,upper,'G'),(3,U,bm,'L'),(4,L,upper,'L')]:
        terms = {**{f'rn_Y_{i}':1 for i in c},**{f'Y_{i}':-slope for i in c},'rn_t':-endpoint}
        # The slope is the actual binary64 RN endpoint. Coefficients are exact;
        # only a non-dyadic representability of the RHS may need direction.
        assert all(F(float(value)) == value for value in terms.values())
        add(f'r145_TS{number}', terms, sense, outward(-endpoint*slope,sense=='L'))
    assert len(added) == 52 and len(variables) == 68
    assert sum(sense != 'N' for sense in senses.values()) == 169
    assert set(point) == variables

    row_checks, bound_checks = [], []
    for name,sense in senses.items():
        if sense == 'N':
            continue
        activity = sum(a*point[key] for key,a in rows[name].items())
        target = rhs.get(name,F(0))
        slack = activity-target if sense == 'G' else target-activity if sense == 'L' else -abs(activity-target)
        assert slack >= 0, (name,str(activity),str(target),str(slack))
        row_checks.append(dict(name=name,sense=sense,activity=str(activity),rhs=str(target),slack=str(slack)))
    for name in sorted(variables):
        lo,hi = bounds.get(name,(F(0),None))
        assert point[name] >= lo and (hi is None or point[name] <= hi), name
        bound_checks.append(dict(variable=name,value=str(point[name]),LB=str(lo),UB=str(hi) if hi is not None else None))

    # A symbolic affine calculation verifies the lower proof from the two
    # NC aggregates rather than trusting the proposed witness's value alone.
    w_affine = {(1,1):(1,0,0), (2,1):(1,-1,0), (2,2):(0,1,0),
                (3,2):(1,0,-1), (3,3):(0,0,1)}
    affine_proofs = []
    for label,table,b in [('NC1',tc,F(0)),('NC2',tc2,constant)]:
        coefficients = [b,F(0),F(0)]
        for key,affine in w_affine.items():
            for j in range(3):
                coefficients[j] += table[key]*affine[j]
        assert coefficients == [F(1,2),F(1,2),F(1,4)], (label,coefficients)
        affine_proofs.append(dict(row=label,t_u_v_coefficients=list(map(str,coefficients))))
    assert F(2,3)*F(1)+F(1,3)*F(-1) == F(1,3)
    assert F(2,3)*F(-3,2)+F(1,3)*F(3) == 0
    assert sum(point[name] for name in Hterms) == F(1,3)
    assert point['G'] == F(1,9)

    mixture = [((1,1,2),F(1,4)),((1,1,3),F(1,2)),((1,2,2),F(1,4))]
    active = {Y for Y in inventories if all(point[f'state_{i}_{Y[i-1]}'] > 0 for i in c)}
    assert active == {Y for Y,_ in mixture}
    assert [Y for Y in active if Y[1] == 2] == [(1,2,2)]
    assert [Y for Y in active if Y[2] == 3] == [(1,1,3)]
    for i in c:
        for y in support:
            assert sum(weight for Y,weight in mixture if Y[i-1] == y) == point[f'state_{i}_{y}']
    H = sum(weight*true_values[Y]['H'] for Y,weight in mixture)
    gamma = sum(weight*true_values[Y]['G'] for Y,weight in mixture)
    theta = H+gamma
    reference = sum(a*point[key] for key,a in rows['OBJ'].items())
    floor = min(value['phi'] for value in true_values.values())
    assert H == F(3,32) and gamma == F(161,1080) and theta == F(1049,4320)
    assert reference == F(59,288) and theta-reference == F(41,1080)
    assert floor == F(47,240) and floor-reference == F(-13,1440)

    result = dict(PASS=True,reviewer='independent nonimplementer',
        fixed_science=FIXED_SCIENCE,dependencies=dependencies,
        member_index_SHA256=digest(index_path),reviewer_script_SHA256=digest(__file__),
        reference_rows=169,reference_variables=68,old_rows=117,added_rows=52,
        no_Optimize=True,new_Native_calls=0,new_compiler_calls=0,
        full_extension_feasible=True,all_rows_checked=True,all_variable_bounds_checked=True,
        exact_reference_fixed_marginal_optimum=str(reference),exact_g_minimum='1/9',
        H=str(H),Gamma=str(gamma),Theta=str(theta),strict_fixed_marginal_gap=str(theta-reference),
        global_integer_floor=str(floor),floor_minus_new_reference=str(floor-reference),
        old_global_floor_gap_not_inherited=True,common_distribution_unique=True,
        marginal_scope='inventory block only; no complete route-extension claim',
        reciprocal_bounds=dict(S_lower=str(sl),S_upper=str(su),L_binary64=str(L),U_binary64=str(U)),
        extension={key:str(value) for key,value in sorted(point.items())},
        appended_rows=[dict(name=name,sense=senses[name],rhs=str(rhs[name]),
                       terms={key:str(value) for key,value in rows[name].items()}) for name in added],
        row_checks=row_checks,bound_checks=bound_checks,threshold_intervals=intervals,
        lower_proof=dict(normalization='2t+u/2+v/4=1',NC_affine=affine_proofs,
            NC_equivalent='Hhat>=1-3t/2',absolute_differences='Hhat>=3t-1',
            weights=['2/3','1/3'],implied_Hhat='1/3',implied_g='1/9'),
        mixture=[dict(Y=Y,weight=str(weight),G=str(true_values[Y]['G']),penalty=str(true_values[Y]['H']))
                 for Y,weight in mixture],
        inside_verification_seconds=time.perf_counter()-started,
        accounting='Charged once by parent serial outer ledger; inside time is not an additional fee')
    with output_path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False)
        stream.write('\n')
    report = f'''# Independent exact verification of the strengthened fixed-marginal example

The stdlib-only reviewer script checked **169 rows and 68 variable bounds**
with Fraction arithmetic. The saved original 117-row matrix and rational
extension are fixed R152 carrier members; their hashes were checked. The
reviewer independently reconstructed the 44 RN rows, two scaled-stock rows,
NC1/NC2 and TS1--TS4. No solver, Native API, Optimize or compiler was used.

The original G/state_g/zprod extension is scaled by 10/9. The new coordinates
are t=4/9, nonzero w=(4/9,1/3,1/9,2/9,2/9) on (11,21,22,32,33),
Yhat=(4/9,5/9,10/9), and hhat=(1/6,1/6,0). Every original and appended row
and every original and appended variable bound is satisfied exactly.

At the fixed marginal, u=w22 and v=w33 give 2t+u/2+v/4=1. Both NC rows give
Hhat>=1-3t/2, while the two differences against station 1 give Hhat>=3t-1.
The weighted sum (2/3,1/3) proves Hhat>=1/3 and g>=1/9. The extension attains
this lower bound, so its fixed-marginal optimum is exactly **59/288**.

The hard resource excludes the fourth 2-by-2 corner (1,2,3). The unique
compatible distribution assigns (1/4,1/2,1/4) to (1,1,2), (1,1,3), (1,2,2).
Consequently H=3/32, Gamma=161/1080 and Theta=1049/4320. The remaining exact
fixed-marginal gap is **41/1080**.

This statement is restricted to the declared inventory block. It does not
establish a complete routing extension or domination of all historical
disjunctions. The old global-floor gap is not inherited: the global integer
floor remains 47/240, and floor minus the new reference is **-13/1440**.

Full exact coordinates, all row slacks, all bound checks, source identities
and the lower proof are in [exact_strict_example.json](exact_strict_example.json).
The parent serial ledger charges this one verification process; the script's
{result['inside_verification_seconds']:.6f} seconds are a nested observation.
'''
    with report_path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(report)
    print(json.dumps({key:result[key] for key in ['PASS','reference_rows','reference_variables',
        'exact_reference_fixed_marginal_optimum','strict_fixed_marginal_gap','new_Native_calls',
        'inside_verification_seconds']}),flush=True)


if __name__ == '__main__':
    main()
