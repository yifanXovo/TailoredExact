"""Independent Round151 review: stdlib and accepted text parser; no Native."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import csv, hashlib, json, math, sys, time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from round108_reader import lp_model
OUT = ROOT / 'results/unified_exact_round151'
START = time.perf_counter()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def parse_mps(path):
    rows, coeff, rhs, bounds, columns = {}, {}, {}, {}, []
    objective = None
    section = None
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        if not raw or raw.startswith('*'):
            continue
        t = raw.split()
        if not raw[0].isspace():
            if t[0] == 'NAME':
                continue
            section = t[0]
            assert section in ('ROWS', 'COLUMNS', 'RHS', 'BOUNDS', 'ENDATA'), section
            continue
        if section == 'ROWS':
            sense, name = t
            if sense == 'N':
                assert objective is None
                objective = name
            else:
                assert name not in rows and sense in ('L', 'G', 'E')
                rows[name] = sense
                coeff[name] = {}
        elif section == 'COLUMNS':
            assert 'MARKER' not in raw and len(t) in (3, 5), raw
            name = t[0]
            if name not in bounds:
                columns.append(name)
                bounds[name] = [0., math.inf]
            for j in range(1, len(t), 2):
                row, value = t[j], float(t[j+1])
                coeff.setdefault(row, {})[name] = value
        elif section == 'RHS':
            assert len(t) in (3, 5)
            for j in range(1, len(t), 2):
                rhs[t[j]] = float(t[j+1])
        elif section == 'BOUNDS':
            kind, _, name = t[:3]
            assert kind in ('LO', 'UP', 'FX', 'FR', 'MI', 'PL'), kind
            value = float(t[3]) if len(t) > 3 else None
            if kind in ('LO', 'FX'):
                bounds[name][0] = value
            if kind in ('UP', 'FX'):
                bounds[name][1] = value
            if kind == 'FR':
                bounds[name] = [-math.inf, math.inf]
            if kind == 'MI':
                bounds[name][0] = -math.inf
            if kind == 'PL':
                bounds[name][1] = math.inf
    assert section == 'ENDATA'
    normalized = {n: (tuple(sorted((k,v) for k,v in coeff[n].items() if v)), {'L':'<=','G':'>=','E':'='}[s], rhs.get(n, 0.)) for n,s in rows.items()}
    return dict(columns=columns, bounds={k:tuple(v) for k,v in bounds.items()},
                objective=(tuple(sorted((k,v) for k,v in coeff.get(objective, {}).items() if v)), -rhs.get(objective, 0.)), rows=normalized)

def upward_transport(x):
    if -1e-12 < x < 0:
        return 0.
    if 0 < x < 1e-12:
        return 1e-12
    return x

facts = []
reuse = read(OUT / 'reuse_index.json')
frozen = read(OUT / 'LP_frozen.json')
assert frozen['LP_script_SHA'] == sha(ROOT/'scripts/round151_lp.py')
assert frozen['math_SHA'] == sha(ROOT/'scripts/round151_math.py')
for domain in frozen['domains']:
    role = domain['role']
    record = next(v for v in reuse['domains'] if v['role'] == role)
    for member in record['members']:
        assert sha(member['restored']) == member['SHA256']
    source = next(Path(v['restored']) for v in record['members'] if v['member'].endswith('.lp'))
    model = lp_model(source)
    scope = domain['scope']
    ar_path = OUT/'LP/arithmetic'/f'{role}.json'
    assert sha(ar_path) == domain['arithmetic_SHA']
    ar = read(ar_path)
    assert ar['scope'] == scope
    mu, nu = F(ar['mu']), F(ar['nu'])
    assert mu >= 0 and nu >= 0
    slope = nu-mu
    minima = []
    for s in scope['stations']:
        c,w,lo,hi = map(F, (s['c'],s['omega'],s['lo'],s['hi']))
        points = [lo,hi]
        if lo <= 1/c <= hi:
            points.append(1/c)
        minima.append(min(w*abs(c*z-1)+slope*z for z in points))
    resource = mu*scope['Bminus']-nu*scope['B']
    exact_d = resource + sum(minima)
    assert F(ar['dual_lower']) <= exact_d
    assert 0 <= F(ar['penalty_lower']) <= max(F(0), exact_d)
    assert F(ar['beta0']) >= min(F(scope['gamma_U']), F(scope['cutoff'])-F(ar['penalty_lower']))
    actual = {(v['i'],v['y']):v for v in ar['states']}
    expected = set()
    for j,s in enumerate(scope['stations']):
        c,w = F(s['c']),F(s['omega'])
        # Independent leave-one-out sum, not the implementation's prefix/suffix.
        other = sum(v for k,v in enumerate(minima) if k != j)
        for y in s['support']:
            key = (s['i'],y)
            expected.add(key)
            v = actual[key]
            exact_diy = resource+other+w*abs(c*y-1)+slope*y
            assert exact_diy >= exact_d
            assert F(v['dual_lower']) <= exact_diy
            assert 0 <= F(v['penalty_lower']) <= max(F(0),exact_diy)
            assert v['penalty_lower'] >= ar['penalty_lower']
            assert F(v['beta']) >= min(F(ar['beta0']),F(scope['cutoff'])-F(v['penalty_lower']))
            assert v['beta'] <= ar['beta0']
            assert v['transported_beta'] == upward_transport(v['beta']) >= v['beta']
            assert v['transported_beta'] <= upward_transport(ar['beta0'])
    assert set(actual) == expected
    csvpath = next(Path(v['restored']) for v in record['members'] if v['member'].endswith('round127_root_lp.csv'))
    with csvpath.open(encoding='utf-8-sig', newline='') as f:
        point = {r['name']:float(r['value']) for r in csv.DictReader(f)}
    assert set(point) == set(model['order'])
    maximum = 0.
    for terms,sense,rhs in model['rows']:
        lhs = math.fsum(a*point[n] for n,a in terms)
        maximum = max(maximum, max(0,lhs-rhs) if sense=='<=' else max(0,rhs-lhs) if sense=='>=' else abs(lhs-rhs))
    assert maximum <= 1e-6
    assert all(lo-1e-6 <= point[n] <= hi+1e-6 for n,(lo,hi) in model['bounds'].items())
    stripped = []
    for item in domain['variants']:
        tag = item['variant']
        folder = OUT/'LP'/f'{role}_{tag}'
        assert sha(folder/'model.mps') == item['model_SHA']
        assert sha(folder/'rows.json') == item['rows_SHA']
        assert sha(folder/'construction.json') == item['construction_SHA']
        mps = parse_mps(folder/'model.mps')
        assert set(mps['columns']) == set(model['order'])
        assert mps['bounds'] == model['bounds']
        assert mps['objective'] == model['objective']
        oldrows = [row for n,row in mps['rows'].items() if not n.startswith('r151_cap_')]
        assert Counter(oldrows) == Counter(model['rows'])
        caprows = read(folder/'rows.json')
        assert len(caprows) == len(expected)
        for row in caprows:
            name = row['name']
            i,y = map(int,name.removeprefix('r151_cap_').split('_'))
            beta = upward_transport(ar['beta0']) if tag=='P' else actual[(i,y)]['transported_beta']
            target = {f'state_g_{i}_{y}':1.}
            if beta:
                target[f'state_{i}_{y}'] = -beta
            assert row['terms'] == target
            assert mps['rows'][name] == (tuple(sorted(target.items())),'<=',0.)
        stripped.append(dict(bounds=mps['bounds'],objective=mps['objective'],rows=Counter(oldrows)))
    if stripped:
        assert all(v == stripped[0] for v in stripped)
    facts.append(dict(role=role,state_count=len(expected),global_floor=ar['penalty_lower'],
        uniform_only=sum(v['transported_beta']==upward_transport(ar['beta0']) for v in actual.values()),
        conditional_stricter=sum(v['transported_beta']<upward_transport(ar['beta0']) for v in actual.values()),
        conditional_stricter_by_more_than_1e_12=sum(upward_transport(ar['beta0'])-v['transported_beta']>1e-12 for v in actual.values()),
        baseline_max_row_residual=maximum,new_MPS_compared=bool(stripped),
        all_original_rows_bounds_objective_retained=True if stripped else None,
        actual_fraction_caps_checked=True,independent_leave_one_out_sum=True))

report = dict(decision='ACCEPT_LP_INPUTS_ONLY',independent_nonimplementer_review=True,
    full_campaign_admission=False,source_commit='c26382d9b',
    reviewed=dict(header_SHA=sha(ROOT/'include/Round151Research.hpp'),LP_frozen_SHA=sha(OUT/'LP_frozen.json'),
        source_hashes={p:sha(ROOT/p) for p in ['src/main.cpp','src/GurobiBaseline.cpp','src/PaperExternalGiniTree.cpp']}),
    mathematical_statement='Fixed nonnegative duals give safe conditional penalty floors; one cap per covered state. GD is unnecessary.',
    findings=[],domains=facts,Optimize=0,Native_load=0,compile=0,
    static_code_review=dict(default_off=True,old_R149_GD_requirement_retained=True,
        independent_final_SHA_expected_map=True,root_once_before_formal_Optimize=True,
        no_floor_positive_group_gate=True,per_state_child_dominance=True,
        signed_non_tiny_caps_valid=True,tiny_transport_monotone_and_upward=True,
        integer_and_nonminimal_epigraph_valid_by_cutoff=True,
        local_interval_hull_only_not_full_joint_hull=True),
    remaining_for_full_admission=['production PE/source identity','writer/Start and nonminimal epigraph','floor0/child/signed/tiny boundary qualification','real Native readback','frozen complete own-H paired matrix and budget'],
    reviewer_outer_seconds=time.perf_counter()-START)
(OUT/'review/LP_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
