"""Separate-executor R120 review: saved bytes and stdlib arithmetic only.

No project audit module, solver library, subprocess, compiler, or native entry
point is imported or executed. The only writes are this review's JSON and MD.
"""
from pathlib import Path
from fractions import Fraction as F
import collections
import csv
import datetime
import hashlib
import itertools
import json
import math
import re
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round120'
DEST = OUT / 'review'
PE = '5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
NUM = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
CACHE = {}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as s:
        for b in iter(lambda: s.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return Path(p).relative_to(ROOT).as_posix()


def rows(p):
    with Path(p).open(encoding='utf-8-sig', newline='') as s:
        return list(csv.DictReader(s))


def close(a, b, tol=1e-10):
    assert abs(a-b) <= tol, (a, b, tol)


def expression(text, exact=False):
    """Independent token parser for the saved canonical linear LP grammar."""
    cast = F if exact else float
    parts = text.split()
    d, constant, sign, i = {}, cast(0), 1, 0
    while i < len(parts):
        t = parts[i]
        if t in ('+', '-'):
            sign = 1 if t == '+' else -1
            i += 1
            continue
        if re.fullmatch(NUM, t):
            coefficient = sign * cast(t)
            i += 1
            if i == len(parts) or parts[i] in ('+', '-'):
                constant += coefficient
                sign = 1
                continue
            name = parts[i]
        else:
            coefficient, name = cast(sign), t
        d[name] = d.get(name, cast(0)) + coefficient
        i += 1
        sign = 1
    return {k: v for k, v in d.items() if v}, constant


def lp(path):
    path = Path(path)
    if path in CACHE:
        return CACHE[path]
    model = dict(objective={}, constant=0., rows=[], bounds={}, types={})
    section = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('\\'):
            continue
        if line in ('Minimize', 'Subject To', 'Bounds', 'Generals', 'Binaries', 'End'):
            section = line
            continue
        if section == 'Minimize':
            assert line.startswith('obj:')
            model['objective'], model['constant'] = expression(line.split(':', 1)[1])
        elif section == 'Subject To':
            name, body = line.split(':', 1)
            m = re.fullmatch(r'(.*?)\s*(<=|>=|=)\s*(' + NUM + r')', body)
            assert m, (path, line)
            coefficients, constant = expression(m[1])
            model['rows'].append((name, coefficients, m[2], float(m[3])-constant))
        elif section == 'Bounds':
            m = re.fullmatch(r'(' + NUM + r') <= (\S+) <= (' + NUM + r')', line)
            assert m, (path, line)
            model['bounds'][m[2]] = (float(m[1]), float(m[3]))
        elif section in ('Generals', 'Binaries'):
            for name in line.split():
                assert name not in model['types']
                model['types'][name] = 'I' if section == 'Generals' else 'B'
        else:
            raise AssertionError((path, section, line))
    names = set(model['objective']) | set(model['bounds']) | set(model['types'])
    names.update(k for _, d, _, _ in model['rows'] for k in d)
    for name in names:
        model['bounds'].setdefault(name, (0., math.inf))
        model['types'].setdefault(name, 'C')
    model['names'] = names
    CACHE[path] = model
    return model


def mps(path):
    """Read the complete saved free-format MPS without any solver API."""
    section, objective_name, integer = None, None, False
    m = dict(objective={}, constant=0., rows={}, bounds={}, types={}, sense='MIN')
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith('*'):
            continue
        t = line.split()
        if not line[0].isspace():
            section = t[0]
            if section == 'OBJSENSE':
                m['sense'] = t[1]
            continue
        if section == 'ROWS':
            if t[0] == 'N':
                objective_name = t[1]
            else:
                m['rows'][t[1]] = ({}, {'L':'<=', 'G':'>=', 'E':'='}[t[0]], 0.)
        elif section == 'COLUMNS':
            if len(t) > 1 and t[1] == "'MARKER'":
                integer = t[2] == "'INTORG'"
                continue
            variable = t[0]
            m['types'].setdefault(variable, 'I' if integer else 'C')
            m['bounds'].setdefault(variable, (0., math.inf))
            for name, value in zip(t[1::2], t[2::2]):
                target = m['objective'] if name == objective_name else m['rows'][name][0]
                target[variable] = target.get(variable, 0.) + float(value)
        elif section == 'RHS':
            for name, value in zip(t[1::2], t[2::2]):
                if name == objective_name:
                    m['constant'] = -float(value)
                else:
                    d, sense, _ = m['rows'][name]
                    m['rows'][name] = d, sense, float(value)
        elif section == 'BOUNDS':
            typ, _, name = t[:3]
            value = float(t[3]) if len(t) > 3 else 0.
            lo, hi = m['bounds'].get(name, (0., math.inf))
            if typ in ('LO', 'LI'):
                lo = value
            elif typ in ('UP', 'UI'):
                hi = value
            elif typ == 'FX':
                lo = hi = value
            elif typ == 'BV':
                lo, hi = 0., 1.
                m['types'][name] = 'B'
            elif typ == 'FR':
                lo, hi = -math.inf, math.inf
            elif typ == 'MI':
                lo = -math.inf
            elif typ == 'PL':
                hi = math.inf
            else:
                raise AssertionError((path, typ))
            if typ in ('LI', 'UI'):
                m['types'][name] = 'I'
            m['bounds'][name] = lo, hi
        elif section not in ('NAME', 'OBJSENSE', 'ENDATA'):
            raise AssertionError((path, section, line))
    m['objective'] = {k:v for k,v in m['objective'].items() if v}
    for name, (d, s, r) in list(m['rows'].items()):
        m['rows'][name] = {k:v for k,v in d.items() if v}, s, r
    return m


def residual(model, values, integral=True):
    assert set(values) == model['names'], (len(values), len(model['names']))
    assert all(math.isfinite(x) for x in values.values())
    bound = max([0.] + [max(lo-values[n], values[n]-hi) for n, (lo,hi) in model['bounds'].items()])
    integ = max([0.] + [abs(values[n]-round(values[n])) for n,t in model['types'].items() if t != 'C']) if integral else 0.
    errors = []
    for name, d, sense, rhs in model['rows']:
        lhs = math.fsum(a*values[n] for n,a in d.items())
        e = max(0., lhs-rhs) if sense == '<=' else max(0., rhs-lhs) if sense == '>=' else abs(lhs-rhs)
        errors.append((e, name))
    worst = max(errors, default=(0., ''))
    objective = model['constant'] + math.fsum(a*values[n] for n,a in model['objective'].items())
    return dict(maximum_row_violation=worst[0], worst_row=worst[1], maximum_bound_violation=bound,
                maximum_integrality_violation=integ, objective=objective)


def instance(path, T):
    text = Path(path).read_text()
    head = re.findall(NUM, text.splitlines()[0])
    V, M = int(head[0]), int(head[1])
    def vector(name):
        return [F(x) for x in re.findall(NUM, re.search(name+r'\s*=\s*\[([^\]]*)\]', text)[1])]
    weights = vector('weights')
    if max(weights[1:]) == 10:
        weights = [w/10 for w in weights]
    pts = vector('points')
    return dict(V=V, M=M, Q=list(map(int,head[2:])), C=list(map(int,vector('capacities'))),
                b=list(map(int,vector('initial'))), D=vector('target'), w=weights,
                points=list(zip(map(float,pts[::2]),map(float,pts[1::2]))), T=T)


def physical(ins, fleet):
    """Replay station service, every load prefix/return, travel and exact F."""
    Y, used, vehicles, detail = list(ins['b']), set(), set(), []
    for route in fleet:
        k, nodes, operations = route['vehicle'], route['nodes'], route['operations']
        assert 0 <= k < ins['M'] and k not in vehicles
        vehicles.add(k)
        assert nodes[0] == nodes[-1] == 0 and len(nodes) >= 2
        station_set = set(nodes[1:-1])
        assert len(station_set) == len(nodes)-2 and all(1 <= i <= ins['V'] for i in station_set)
        op = {v['station']:v for v in operations}
        assert len(op) == len(operations) and set(op) == station_set
        load, pickups, prefixes = 0, 0, [0]
        for i in nodes[1:-1]:
            assert i not in used
            used.add(i)
            p, d = op[i]['pickup'], op[i]['drop']
            assert isinstance(p,(int,float)) and isinstance(d,(int,float))
            assert p == round(p) and d == round(d) and p >= 0 and d >= 0 and (p > 0) != (d > 0)
            load += int(p-d)
            pickups += int(p)
            assert 0 <= load <= ins['Q'][k]
            prefixes.append(load)
            Y[i] += int(d-p)
            assert 0 <= Y[i] <= ins['C'][i]
        assert 0 <= load <= ins['Q'][k]
        travel = math.fsum(math.hypot(ins['points'][a][0]-ins['points'][b][0],
                                     ins['points'][a][1]-ins['points'][b][1])/1.5
                           for a,b in zip(nodes,nodes[1:]))
        duration = travel + 120*pickups
        assert duration <= ins['T'] + 1e-7, (duration, ins['T'])
        detail.append(dict(vehicle=k, prefix_loads=prefixes, return_load=load, cumulative_pickup=pickups,
                           travel=travel, duration=duration))
    r = [F(Y[i])/ins['D'][i] for i in range(1,ins['V']+1)]
    total = sum(r)
    G = sum(abs(a-b) for i,a in enumerate(r) for b in r[i+1:])/(ins['V']*total) if total else F(0)
    penalty = sum(ins['w'][i]*abs(r[i-1]-1) for i in range(1,ins['V']+1))
    objective = G + F(3,20)*penalty
    return dict(Y=Y, G=float(G), P=float(penalty), F=float(objective), exact_G=str(G), exact_F=str(objective), routes=detail)


def from_vector(ins, values):
    fleet = []
    for k in range(ins['M']):
        arcs = {(int(a),int(b)) for name,x in values.items()
                if x > .5 and (m:=re.fullmatch(r'x_'+str(k)+r'_(\d+)_(\d+)',name))
                for a,b in [m.groups()]}
        nodes, ops, cur = [0], [], 0
        while arcs:
            nxt = [b for a,b in arcs if a == cur]
            assert len(nxt) == 1
            b = nxt[0]
            arcs.remove((cur,b))
            nodes.append(b)
            if b:
                ops.append(dict(station=b, pickup=values['p_'+str(k)+'_'+str(b)], drop=values['d_'+str(k)+'_'+str(b)]))
            cur = b
            if not b:
                assert not arcs
                break
        if nodes == [0]:
            nodes.append(0)
        fleet.append(dict(vehicle=k,nodes=nodes,operations=ops))
    return fleet


def endpoints(meta, actual=None):
    """Exact sums of decimal literals AND binary64 stored coefficients."""
    a,m,b = [F.from_float(float(meta[k])) for k in ('a','m','b')]
    b0,b1 = [F.from_float(float(meta[k])) for k in ('beta0','beta1')]
    if not meta['conditional']:
        b0=b1=min(b0,b1)
    targets = [a,m,m,b,b0,b1]
    outputs = {}
    for mode in ('decimal_literals','binary64') if actual is None else ('actual_native_binary64',):
        source = meta if actual is None else actual
        conv = F if mode == 'decimal_literals' else lambda x:F.from_float(float(x))
        lb,ld,ub,ud,fb,fd,c = [conv(source[k]) for k in
            ('lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta','objective_constant')]
        ends = [lb,lb+ld,ub,ub+ud,fb+c,fb+fd+c]
        slacks = [targets[i]-ends[i] if i in (0,1,4,5) else ends[i]-targets[i] for i in range(6)]
        assert min(slacks) >= 0, (mode,slacks)
        outputs[mode] = dict(exact_endpoints=list(map(str,ends)), exact_outward_slacks=list(map(str,slacks)))
    return outputs


def extension_audit(path):
    path=Path(path)
    meta=read(str(path)+'.round120.json')
    model=lp(path)
    assert digest(path)==meta['SHA']
    assert model['types']['r120_h']=='B' and model['bounds']['r120_h']==(0.,1.)
    assert sum(n=='r120_h' for n in model['names'])==1 and 'r120_h' not in model['objective']
    expected = [
        ('r120_g_lower', {'G':1.,'r120_h':-float(meta['lower_delta'])},'>=',float(meta['lower_base'])),
        ('r120_g_upper', {'G':1.,'r120_h':-float(meta['upper_delta'])},'<=',float(meta['upper_base']))]
    objective=dict(model['objective'])
    if float(meta['objective_delta']):
        objective['r120_h']=-float(meta['objective_delta'])
    expected.append(('r120_f_lower',objective,'>=',float(meta['objective_base'])))
    assert model['rows'][-3:]==expected
    close(model['constant'],meta['objective_constant'],0)
    return dict(path=rel(path), rows=len(model['rows']), columns=len(model['names']),
                full_objective_coefficients_recomputed=True, endpoint_audit=endpoints(meta))


def small_enumeration():
    folder=OUT/'qualification/native_contract02'
    ins=instance(ROOT/'reference/round119_qualification/micro_enumeration.txt',1000)
    fleets=[]
    for Y in itertools.product(*(range(c+1) for c in ins['C'][1:])):
        delta={i+1:Y[i]-ins['b'][i+1] for i in range(ins['V'])}
        active=[i for i,d in delta.items() if d]
        for order in itertools.permutations(active):
            route=dict(vehicle=0,nodes=[0,*order,0],operations=[dict(station=i,pickup=max(0,-delta[i]),drop=max(0,delta[i])) for i in order])
            try:
                result=physical(ins,[route])
            except AssertionError:
                continue
            fleets.append((route,result))
    assert len(fleets)==3 and {v['exact_F'] for _,v in fleets}=={'3/10','13/20'}
    signatures={tuple(v['Y']) for _,v in fleets}
    checks=[]
    midpoint=[]
    for i in range(6):
        path=folder/f'extension_{i}.lp'
        model=lp(path)
        meta=read(str(path)+'.round120.json')
        checked=[]
        for file in sorted(folder.glob(f'extension_{i}.lp.fleet*.csv')):
            data=rows(file)
            values={q['variable']:float(q['value']) for q in data}
            assert len(values)==len(data)
            for q in data:
                name=q['variable']
                assert model['types'][name]==q['type']
                assert model['bounds'][name]==(float(q['lower']),float(q['upper']))
                assert model['objective'].get(name,0.)==float(q['objective_coefficient'])
            replay=physical(ins,from_vector(ins,values))
            assert tuple(replay['Y']) in signatures
            for k in range(1,ins['V']+1):
                close(values[f'Y_{k}'],replay['Y'][k],0)
            test=residual(model,values)
            assert max(test[k] for k in ('maximum_row_violation','maximum_bound_violation','maximum_integrality_violation'))<=1e-7
            close(test['objective'],replay['F'],1e-12)
            close(values['G'],replay['G'],1e-12)
            assert values['r120_h']==(0 if replay['G']<=meta['m'] else 1)
            checked.append((file,values,replay,test))
        assert len(checked)==3 and {tuple(q[2]['Y']) for q in checked}==signatures
        for file,values,replay,test in checked:
            checks.append(dict(path=rel(file),physical=replay,residual=test))
        zero=next(v for _,v,p,_ in checked if p['G']==0)
        for h in (0,1):
            x=dict(zero)
            x.update(G=meta['m'],state_g_1_0=meta['m'],state_g_2_0=meta['m'],r120_h=h)
            test=residual(model,x)
            expected_failure=meta['conditional'] and h==1 and meta['beta1']>.55+1e-7
            assert (test['maximum_row_violation']>1e-7)==expected_failure
            assert test['maximum_bound_violation']==0 and test['maximum_integrality_violation']==0
            if expected_failure:
                assert test['worst_row']=='r120_f_lower'
            midpoint.append(dict(model=i,h=h,expected_auxiliary_removal=expected_failure,residual=test))
        for state in (0,1):
            data=rows(folder/f'type_start_{i+1}.json.state{state}.csv')
            x={q['variable']:float(q['value']) for q in data}
            assert all(q['value']==q['readback'] for q in data)
            assert all(model['types'][q['variable']]==q['type'] for q in data)
            test=residual(model,x)
            assert max(test[k] for k in ('maximum_row_violation','maximum_bound_violation','maximum_integrality_violation'))<=1e-7
            close(test['objective'],physical(ins,from_vector(ins,x))['F'],1e-12)
        assert rows(folder/f'type_start_{i+1}.json.state0.csv') != rows(folder/f'type_start_{i+1}.json.state1.csv')
    synthetic=mps(folder/'synthetic_constant_actual.mps')
    assert synthetic['constant']==.25
    source=lp(folder/'synthetic_constant_D1.lp')
    assert synthetic['objective']==source['objective'] and synthetic['rows']['r120_f_lower'][0].keys()==source['rows'][-1][1].keys()
    assert synthetic['bounds']==source['bounds'] and synthetic['types']==source['types']
    assert len(synthetic['rows'])==len(source['rows'])
    for name,coefficient,sense,rhs in source['rows'][:-1]:
        assert synthetic['rows'][name]==(coefficient,sense,rhs)
    meta=read(folder/'synthetic_constant_D1.lp.round120.json')
    d,s,r=synthetic['rows']['r120_f_lower']
    actual={k:float(meta[k]) for k in ('lower_base','lower_delta','upper_base','upper_delta')}
    actual.update(objective_base=r,objective_delta=-d['r120_h'],objective_constant=synthetic['constant'])
    constant_check=endpoints(meta,actual)
    assert {k:v for k,v in d.items() if k!='r120_h'}==source['objective']
    constant_values=[]
    actual_model=dict(objective=synthetic['objective'],constant=synthetic['constant'],bounds=synthetic['bounds'],
        types=synthetic['types'],names=set(synthetic['bounds']),
        rows=[(name,*parts) for name,parts in synthetic['rows'].items()])
    for j in range(3):
        x={q['variable']:float(q['value']) for q in rows(folder/f'extension_1.lp.fleet{j}.csv')}
        linear=math.fsum(c*x[n] for n,c in synthetic['objective'].items())
        close(linear+.25,physical(ins,from_vector(ins,x))['F']+.25,1e-12)
        actual_residual=residual(actual_model,x)
        assert max(actual_residual[k] for k in ('maximum_row_violation','maximum_bound_violation','maximum_integrality_violation'))<=1e-7
        constant_values.append(linear+.25)
    failed=(OUT/'fees/qual02_fixed/01_zero_native_matrix_Start_stdout.txt').read_text().strip()
    assert failed=='actual objective constant lost'
    assert read(OUT/'fees/qual02_fixed/receipt.json')['exit_code']==1
    # A pure mathematical resource example: Q limits prefixes, not totals.
    resource=dict(V=4,M=1,Q=[1],C=[100,1,1,1,1],b=[50,1,0,1,0],D=[F(0)]+[F(1)]*4,
                  w=[F(0)]+[F(1)]*4,points=[(0.,0.),(1.,0.),(2.,0.),(3.,0.),(4.,0.)],T=1000)
    example=[dict(vehicle=0,nodes=[0,1,2,3,4,0],operations=[dict(station=i,pickup=1 if i%2 else 0,drop=0 if i%2 else 1) for i in range(1,5)])]
    resource_check=physical(resource,example)
    assert resource_check['routes'][0]['cumulative_pickup']==2>resource['Q'][0]
    return dict(enumeration_method='all integer station final inventories, all permutations of nonzero services; independently replay every physical rule',
                complete_feasible_fleets=[dict(route=r,physical=p) for r,p in fleets], embeddings=checks,
                shared_midpoint_auxiliary_cases=midpoint, full_Start_readbacks=12,
                Q_is_prefix_capacity_example=resource_check, zero_denominator_covered=True, loaded_return_covered=True,
                synthetic_constant=dict(actual_MPS_ObjCon=.25,exact_endpoint_check=constant_check,
                    original_F_plus_constant=constant_values,original_BRP_ObjCon=0,
                    failed_LP_text_fixture_preserved=failed,
                    limit='corrected synthetic actual-API/MPS coefficient arithmetic check; not an original BRP offset or a native proof'),
                injected_lifecycle_fixtures='archive/late/split/deadline/bad exercise C++ control predicates with analytic injected proofs, Optimize=0; not native exposure')


def diagnostics():
    output=[]
    for role in ('F2','R98-C2'):
        external=OUT/'qualification'/('export_'+role)/'external'
        pair=read(external/'round120_root_pair.json')
        d1path=next((external/'models').glob('*_round120_d1.lp'))
        source_models={'D0':lp(external/'round120_D0.lp'),'D1':lp(d1path)}
        values=[]
        for kind in ('D0_original_objective','D1_original_objective','D0_max_conditional_violation'):
            folder=OUT/'qualification/diagnostics'/role/kind
            p=read(folder/'full_primal_and_original_matrix.json')
            record=read(folder/'record.json')
            model=source_models['D1' if kind.startswith('D1') else 'D0']
            x=dict(zip(p['names'],p['primal']))
            assert len(x)==len(p['names'])==len(p['primal'])
            parsed=mps(folder/'actual_complete_relaxation.mps')
            assert len(p['rhs'])==len(model['rows'])==len(parsed['rows'])
            assert set(x)==model['names']==set(parsed['bounds'])
            assert p['row_starts'][-1]==len(p['column_indices'])==len(p['coefficients'])
            original_obj={n:c for n,c in zip(p['names'],p['original_objective']) if c}
            assert original_obj==model['objective'] and p['original_objective_constant']==model['constant']
            for i,(name,d,sense,rhs) in enumerate(model['rows']):
                a,b=p['row_starts'][i:i+2]
                saved={p['names'][p['column_indices'][k]]:p['coefficients'][k] for k in range(a,b)}
                assert saved==d and p['rhs'][i]==rhs and p['senses'][i]=={'<=':'<','>=':'>','=':'='}[sense]
                assert parsed['rows'][name]==(d,sense,rhs)
            for i,n in enumerate(p['names']):
                assert model['bounds'][n]==(p['lower_bounds'][i],p['upper_bounds'][i])==parsed['bounds'][n]
                assert parsed['types'][n]=='C'
            check=residual(model,x,integral=False)
            assert check['maximum_row_violation']<=1e-7 and check['maximum_bound_violation']<=1e-7
            lhs=math.fsum(c*x[n] for n,c in source_models['D1']['rows'][-1][1].items())
            row_violation=source_models['D1']['rows'][-1][3]-lhs
            beta_violation=pair['beta0']+(pair['beta1']-pair['beta0'])*x['r120_h']-check['objective']
            if 'violation' in kind:
                expected={k:-v for k,v in original_obj.items()}
                expected['r120_h']=pair['beta1']-pair['beta0']
                assert parsed['objective']==expected and parsed['constant']==pair['beta0']-model['constant']
                assert parsed['sense']=='MAX'
                obj=parsed['constant']+math.fsum(c*x[n] for n,c in parsed['objective'].items())
                close(obj,beta_violation,1e-12)
                assert row_violation>1e-7 and beta_violation>1e-7
            else:
                assert parsed['objective']==original_obj and parsed['constant']==model['constant']
                obj=check['objective']
            close(obj,record['objective'],1e-10)
            close(row_violation,record['actual_D1_row_violation'],1e-10)
            close(beta_violation,record['qualified_beta_violation'],1e-10)
            values.append(dict(kind=kind,residual=check,independent_actual_D1_violation=row_violation,
                               independent_beta_violation=beta_violation,independent_objective=obj,
                               all_source_LP_API_matrix_and_MPS_rows_bounds_equal=True,
                               rows=len(model['rows']),columns=len(x),nonzeros=len(p['coefficients'])))
        close(values[0]['independent_objective'],values[1]['independent_objective'],1e-10)
        output.append(dict(role=role,points=values,complete_LP_nonredundant=True,
                           inference='positive feasible D0 violation proves nonredundancy in the extended (original variables, h) LP; no stronger original-objective minimum is shown by equal D0/D1 minima and no LP optimality claim is needed for the feasible-point inference'))
    return output


def classify(c,p):
    """Own implementation of frozen R108 decision rules, without importing it."""
    du=p['U']-c['U']; dg=p['gap']-c['gap']
    au=max(.001,.01*abs(p['U'])); ag=max(.001,.10*abs(p['gap']))
    severe=False
    if c['certificate']!=p['certificate']:
        decision='WIN' if c['certificate'] else 'LOSS'
        severe=not c['certificate']
        basis='candidate_only_complete_certificate' if c['certificate'] else 'control_only_complete_certificate'
    elif c['certificate']:
        dt=p['T_produce']-c['T_produce']; threshold=max(30.,.1*p['T_produce'])
        decision='WIN' if dt>=threshold else 'LOSS' if -dt>=threshold else 'TIE'
        severe=c['T_produce']>=2*p['T_produce'] and -dt>=120
        basis='both_complete_certificate_time'
    else:
        good=du>=au or dg>=ag
        bad=-du>=au or -dg>=ag
        decision='MIXED' if good and bad else 'WIN' if good else 'LOSS' if bad else 'TIE'
        severe=-du>=max(.001,.05*abs(p['U'])) and -dg>=max(.005,.25*abs(p['gap']))
        basis='both_uncertified_absolute_materiality'
    return dict(id=c['id'],candidate=c['arm'],control=p['arm'],classification=decision,
                severe_regression=severe,basis=basis,UB_improvement=du,gap_improvement=dg,a_U=au,a_gap=ag)


def native_points(directory,launch,ins,events):
    call_by_sha={v['model_sha256']:v for v in events if v['kind']=='call'}
    checks=[]
    for receipt in sorted((directory/'external/native_logs').glob('*.round68.start.json')):
        rec=read(receipt)
        file=Path(str(receipt).replace('.round68.start.json','.round68.start.values.csv'))
        if not file.exists():
            assert not rec['submitted']
            continue
        data=rows(file)
        x={r['variable']:float(r['value']) for r in data}
        assert len(x)==len(data)
        assert all(float(r['readback'])==float(r['value']) for r in data)
        model=lp(call_by_sha[rec['model_sha256']]['model_path'])
        assert all(model['types'][r['variable']]==r['type'] for r in data)
        result=residual(model,x)
        assert max(result[k] for k in ('maximum_row_violation','maximum_bound_violation','maximum_integrality_violation'))<=1e-7
        physical_result=physical(ins,from_vector(ins,x))
        close(result['objective'],physical_result['F'],1e-9)
        close(x['G'],physical_result['G'],1e-10)
        if 'r120_h' in x:
            pair=read(directory/'external/round120_root_pair.json')
            assert x['r120_h']==(0 if physical_result['G']<=pair['m'] else 1)
        checks.append(dict(path=rel(file),columns=len(x),residual=result,physical=physical_result))
    return checks


def formal_and_exposure():
    order=[('F2',1200,['P-GRB','M-B','MB-D0','MB-D1']),
           ('R98-C2',1800,['MB-D1','MB-D0','M-B','P-GRB']),
           ('N40-R1-S',5400,['M-B','MB-D1','P-GRB','MB-D0'])]
    arms=[]; all_pairs=[]; exposure=[]; start_checks=[]; identity=read(OUT/'production_identity.json')
    for g,(role,cap,methods) in enumerate(order,1):
        folder=OUT/'campaign'/f'group{g:02}'
        current=read(OUT/'reconstruction'/f'group{g:02}'/'current_core.json')
        frozen=read(folder/'identity.json')
        assert frozen['candidate_binary_sha256']==PE and frozen['dll_sha256']==DLL
        assert frozen['source_hashes']==identity['source_bindings']
        assert [v['arm'] for v in frozen['launches']]==methods
        rawdirs=sorted((folder/'raw').iterdir())
        assert len(rawdirs)==4
        group_arms=[]
        for num,(directory,method) in enumerate(zip(rawdirs,methods),1):
            launch=read(directory/'launch.json'); result=read(directory/'result.json')
            assert launch['id']==role and launch['arm']==method and launch['number']==num
            assert launch['cap_seconds']==cap and launch['global_launch_number']==(g-1)*4+num
            assert {k:launch[k] for k in frozen['launches'][num-1]}==frozen['launches'][num-1]
            assert launch['runner_sha256']==frozen['runner_sha256'] and launch['prereg_sha256']==frozen['prereg_sha256']
            command=launch['command']; panel=launch['panel']
            assert panel['cap_seconds']==cap and digest(ROOT/panel['input_path'])==panel['input_sha256']
            for flag,value in [('--threads','1'),('--mip-threads','1'),('--gurobi-seed','0'),('--gurobi-presolve','-1'),('--process-wall-time-limit',str(cap))]:
                assert command[command.index(flag)+1]==value
            assert '--round119-proof-contraction' not in command and not any('qualification' in q for q in command)
            assert read(directory/'affinity.json')['child']['process_mask']==4
            assert read(directory/'completion.json')['returncode']==0
            producer=read(directory/'producer_receipt.json'); total=read(directory/'arm_total_receipt.json')
            produce=producer['t_produce_perf']-producer['t0_perf']
            verify=total['t_verified_perf']-producer['t_produce_perf']
            whole=total['t_verified_perf']-producer['t0_perf']
            close(produce,producer['T_produce'],1e-8);close(verify,total['T_verify'],1e-8);close(whole,total['T_total'],1e-8)
            assert produce<=cap and abs(whole-produce-verify)<1e-8
            ins=instance(ROOT/panel['input_path'],panel['T_seconds'])
            phy=physical(ins,result['routes'])
            close(phy['F'],result['upper_bound'],1e-10)
            obs=read(directory/'observations.json')
            events=[v['payload'] for v in obs]
            assert [e['sequence'] for e in events]==list(range(1,len(events)+1))
            calls={e['call']:e for e in events if e['kind']=='call'}
            returned={e['call'] for e in events if e['kind']=='returned' and e['return_code']==0}
            assert set(calls)==returned
            witnesses=[physical(ins,e['routes']) for e in events if e['kind']=='witness']
            for e,w in zip([v for v in events if v['kind']=='witness'],witnesses):
                close(w['F'],e['objective'],1e-9)
            U=min([phy['F']]+[w['F'] for w in witnesses])
            for cid,c in calls.items():
                assert digest(c['model_path'])==c['model_sha256']
                for setting,value in [('Threads',1),('Seed',0),('Presolve',-1),('MIPGap',0),('MIPGapAbs',0),('FeasibilityTol',1e-6),('OptimalityTol',1e-6),('IntFeasTol',1e-5)]:
                    assert c['settings'][setting]==value
            if method=='P-GRB':
                assert len(calls)==1 and next(iter(calls.values()))['full_original']
                L=max(e['native_bound'] for e in events if e['kind']=='bound')
                source='full-original committed native-bound observations'
            else:
                leaves=rows(directory/'external/paper_leaf_ledger.csv')
                assert len(leaves)==1 and leaves[0]['leaf_id']=='L0'
                leaf=leaves[0]
                assert float(leaf['gamma_L'])==0 and float(leaf['gamma_U'])>=min(float(leaf.get('cutoff',result.get('upper_bound',U))), (ins['V']-1)/ins['V'])
                # Every actual role retained the original root: cutoff tail has F>=G.
                cutoff=max(c['cutoff'] for c in calls.values())
                assert float(leaf['gamma_U'])==cutoff and U<=cutoff+1e-7
                L=min(cutoff,float(leaf['lower_bound']))
                source='single complete final root leaf plus original cutoff complement'
                assert len(calls)==5 and sum(c['native_preconditions'] for c in calls.values())==2
            close(L,result['lower_bound'],1e-10)
            assert L<=U+1e-7
            # Final log is a coarser printed check, never promoted to a high precision proof.
            finalcall=calls[max(calls)]
            log=Path(finalcall['native_log_path']).read_text()
            native_matches=re.findall(r'Best objective\s+('+NUM+r'), best bound\s+('+NUM+r')',log)
            assert native_matches
            printed_bound=float(native_matches[-1][1])
            # The completed controller may retain a slightly weaker qualified
            # leaf bound than the final printed native bound. Never replace it
            # by the rounded log value or silently close a larger gap.
            assert printed_bound>=L-1e-10 and abs(printed_bound-L)<=1e-7, (role,method,printed_bound,L)
            certificate=(U-L<=1e-7)
            a=dict(id=role,arm=method,U=U,L=L,gap=U-L,certificate=certificate,T_produce=produce,T_verify=verify,T_total=whole,
                   physical=phy,physical_witnesses_recomputed=len(witnesses),lower_bound_raw_source=source,
                   final_native_printed_bound=printed_bound,retained_qualified_L=L,
                   native_calls=len(calls),PE_SHA=frozen['candidate_binary_sha256'],DLL_SHA=frozen['dll_sha256'])
            published=next(v for v in current['arms'] if v['arm']==method)
            for k in ('U','L','gap','T_produce','T_verify','T_total'):
                close(a[k],published[k],1e-9)
            assert certificate==published['certificate']
            arms.append(a);group_arms.append(a)
            start_checks.extend(native_points(directory,launch,ins,events))
            if method in ('MB-D0','MB-D1'):
                ep=directory/'external/round120_events.jsonl'
                ee=[json.loads(s) for s in ep.read_text().splitlines()]
                assert [q['sequence'] for q in ee]==list(range(1,len(ee)+1))
                pair=read(directory/'external/round120_root_pair.json')
                assert pair['input_SHA']==panel['input_sha256']
                installed=[e for e in ee if e['kind']=='root_formulation_installed']
                paid=[e for e in ee if e['kind']=='paid_root_LP_returned']
                assert len(installed)==1 and len(paid)==2
                assert len([e for e in ee if e['kind']=='root_pair_registered'])==1
                assert not [e for e in ee if e['kind'] in ('revoked','termination_requested','atomic_contraction_committed','root_formulation_carried_to_original_MIP')]
                mipcalls=[c for c in calls.values() if c['native_preconditions']]
                assert mipcalls[0]['leaf']=='L0' and all(c['model_sha256']==installed[0]['model'] for c in mipcalls)
                model=lp(installed[0]['path'])
                basepath=next(Path(installed[0]['path']).parent.glob('L0_epoch_0_generation_1.lp'))
                base=lp(basepath)
                assert model['rows'][:-3]==base['rows'] and model['objective']==base['objective']
                assert model['names']==base['names']|{'r120_h'}
                assert {n:v for n,v in model['types'].items() if n!='r120_h'}==base['types']
                assert {n:v for n,v in model['bounds'].items() if n!='r120_h'}==base['bounds']
                for j,e in enumerate(paid):
                    c=calls[e['call']]
                    assert e['side']==j and e['status']=='OPTIMAL' and c['leaf']==f'L0.{j}'
                    assert e['model']==c['model_sha256']==pair['proofs'][j]['model']
                    assert (e['lower'],e['upper'],e['cutoff'])==(c['lower_g'],c['upper_g'],c['cutoff'])
                    assert (e['bound'],e['cutoff'])==(pair['proofs'][j]['bound'],pair['proofs'][j]['cutoff'])
                    assert pair['a']==0 and pair['m']==pair['a']+(pair['b']-pair['a'])/2
                    assert (e['lower'],e['upper'])==((pair['a'],pair['m']) if j==0 else (pair['m'],pair['b']))
                    lpstatus=next(v for v in rows(directory/'external/lp_status_ledger.csv') if v['leaf_id']==c['leaf'])
                    assert lpstatus['native_status']=='OPTIMAL' and lpstatus['optimal']=='1'
                    close(float(lpstatus['lower_bound']),e['bound'],0)
                    bound=F.from_float(min(e['bound'],e['cutoff']))-F.from_float(1e-7)
                    beta=F.from_float(pair['beta0' if j==0 else 'beta1'])
                    assert beta<=bound if bound>=0 else beta==0
                    assert e['process_seconds']<installed[0]['process_seconds']
                    for w in witnesses:
                        if e['lower']<=w['G']<=e['upper'] and w['F']<=e['cutoff']:
                            assert e['bound']<=w['F']+1e-7
                native_ep=[]
                for q in sorted((directory/'external/native_logs').glob('*.round120.native.json')):
                    r=read(q)
                    assert r['model_SHA']==installed[0]['model'] and r['h_type']=='B'
                    assert (r['h_LB'],r['h_UB'],r['h_BranchPriority'])==(0,1,0)
                    assert r['rows']==len(model['rows']) and r['columns']==len(model['names']) and r['objective_constant']==0
                    meta=read(str(installed[0]['path'])+'.round120.json')
                    for k in ('lower_base','lower_delta','upper_base','upper_delta','objective_base','objective_delta','objective_constant'):
                        close(float(meta[k]),r[k],0)
                    native_ep.append(dict(path=rel(q),check=endpoints(dict(pair,conditional=method=='MB-D1'),r)))
                assert len(native_ep)==2
                assert len([e for e in ee if e['kind']=='extended_native_returned'])==2
                exposure.append(dict(id=role,arm=method,actual_paid_root_LPs=paid,installation=installed[0],
                                     actual_MIP_models=[c['model_sha256'] for c in mipcalls],
                                     target_terminal_same_artifact=True,actual_native_endpoint_audits=native_ep,
                                     conditional_beta0=pair['beta0'],conditional_beta1=pair['beta1'],
                                     h_fixing_or_branching='unknown',whole_tree_retention='not observed or claimed'))
        lookup={a['arm']:a for a in group_arms}
        names=[('MB-D1','M-B'),('MB-D1','P-GRB'),('MB-D1','MB-D0'),('MB-D0','M-B'),('MB-D0','P-GRB'),('M-B','P-GRB')]
        csvpairs=rows(OUT/'reconstruction'/f'group{g:02}'/'pairs.csv')
        assert len(csvpairs)==6
        for c,p in names:
            v=classify(lookup[c],lookup[p])
            saved=next(s for s in csvpairs if s['candidate']==c and s['control']==p)
            assert (v['classification'],v['basis'],v['severe_regression'])==(saved['classification'],saved['basis'],saved['severe_regression']=='True')
            corepair=next(s for s in current['pairs'] if s['candidate']==c and s['control']==p)
            assert v['classification']==corepair['classification'] and v['severe_regression']==corepair['severe_regression']
            all_pairs.append(v)
        CACHE.clear()
    # H100 and actual V8 chain saved all-column Start vectors, without new calls.
    supplementary=[]
    for name in ('h100','chain'):
        for d in sorted((OUT/'qualification'/name/'raw').iterdir()):
            launch=read(d/'launch.json')
            panel=launch['panel']
            ins=instance(ROOT/panel['input_path'],panel['T_seconds'])
            obs=read(d/'observations.json')
            ev=[v['payload'] for v in obs]
            supplementary.extend(native_points(d,launch,ins,ev))
            CACHE.clear()
    return dict(arms=arms,pairs=all_pairs,formal_actual_exposure=exposure,
                formal_all_column_Start_vectors=start_checks,supplementary_Start_vectors=supplementary)


def math_and_stage(formal):
    projections=[]
    for a,m,b in [(F(0),F(1,3),F(1)),(F(1,10),F(2,5),F(7,10))]:
        for b0,b1 in [(F(1,5),F(4,5)),(F(4,5),F(1,5)),(F(2,5),F(2,5)),(F(0),F(0))]:
            for i in range(17):
                g=a+(b-a)*F(i,16)
                lo=max(F(0),(g-m)/(b-m));hi=min(F(1),(g-a)/(m-a))
                assert lo<=hi
                exact=b0+(b1-b0)*(lo if b1>=b0 else hi)
                formula=max(b0,b0+(b1-b0)*(g-m)/(b-m)) if b1>=b0 else max(b1,b1+(b0-b1)*(m-g)/(m-a))
                assert exact==formula
                projections.append(str(exact))
    pairs=formal['pairs']; arms=formal['arms']
    core=[p for p in pairs if p['id']!='N40-R1-S']
    chosen=[p for p in core if p['candidate']=='MB-D1']
    mb=[p for p in chosen if p['control']=='M-B']
    d0=[p for p in chosen if p['control']=='MB-D0']
    primary=[p for p in chosen if p['control']=='P-GRB']
    certs={m:sum(a['certificate'] for a in arms if a['arm']==m) for m in ('P-GRB','M-B','MB-D0','MB-D1')}
    gain=any(p['classification']=='WIN' for p in mb)
    conditional=any(p['classification']=='WIN' for p in d0) and not any(p['severe_regression'] for p in d0)
    primary_ok=not any(p['severe_regression'] for p in primary) and sum(p['classification']=='LOSS' for p in primary)<2
    cert_ok=certs['MB-D1']>=certs['M-B']
    gate=gain and conditional and primary_ok and cert_ok and len(core)==12 and len(formal['formal_actual_exposure'])>=4
    severe_primary=any(p['candidate']=='MB-D1' and p['control']=='P-GRB' and p['severe_regression'] for p in pairs)
    n40_complete=sum(a['id']=='N40-R1-S' for a in arms)==4
    # Priority in goal section 13: evidence barriers; historical/no-information
    # stops; severe primary or uncompensated certificate risk; attribution;
    # then completed confirmation-admission obligations. No D0/P hidden veto.
    if severe_primary or not cert_ok:
        stage='STOP_TESTED_NATIVE_DISJUNCTION'
    elif gain and not conditional:
        stage='RETAIN_NATIVE_ENCODING_WITHOUT_CONDITIONAL_ATTRIBUTION'
    elif not gain:
        stage='STOP_TESTED_NATIVE_DISJUNCTION'
    elif gate and n40_complete:
        stage='ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION'
    else:
        stage='RETAIN_NATIVE_ENCODING_WITHOUT_CONDITIONAL_ATTRIBUTION'
    assert stage==read(OUT/'stage_decision.json')['stage']
    assert read(OUT/'core_admission.json')['admitted']==gate
    return dict(exact_scalar_projection_cases=len(projections),stage=stage,core_admitted=gate,
                actual_correctness_or_necessary_evidence_barrier_found=False,
                certificate_counts=certs,severe_primary_risk=severe_primary,
                D1_MB_positive_signal=gain,D1_D0_conditional_signal=conditional,
                no_hidden_D0_primary_veto=True,D0_promoted=False,
                finite_risks=['C2 D1/M-B severe LOSS; D1/P nonsevere LOSS; D1/D0 WIN',
                    'all N40 arms remain open; weaker D1 lower bound than M-B and D0 despite better own U',
                    'known roles and one seed; native h fixing/branching and full tree retention unobserved'])


def fees_and_freeze():
    entries=[]
    for p in sorted((OUT/'fees').glob('*/launch.json')):
        launch=read(p);receipt=read(p.parent/'receipt.json')
        assert receipt['actual_exit_observed'] and receipt['exit_code'] in (0,1)
        assert not receipt['nested_native_seconds_added']
        assert receipt['conservative_process_starts']==receipt['actual_native_children']+1
        assert receipt['outer_seconds_upper']>=receipt['outer_seconds_lower']
        assert launch['qualification']==receipt['qualification']
        entries.append(dict(name=p.parent.name,**receipt))
    starts=sum(e['conservative_process_starts'] for e in entries)
    seconds=sum(e['outer_seconds_upper'] for e in entries)
    qs=sum(e['conservative_process_starts'] for e in entries if e['qualification'])
    qt=sum(e['outer_seconds_upper'] for e in entries if e['qualification'])
    assert starts==31 and qs==16
    close(seconds,32358.098361730576,1e-8);close(qt,817.8110692501068,1e-8)
    identity=read(OUT/'production_identity.json')
    for name,value in identity['source_bindings'].items():
        assert digest(ROOT/name)==value
    frozen=read(OUT/'pre_formal_freeze.json')
    assert frozen['source_bindings']==identity['source_bindings']
    for name,value in frozen['helpers'].items():
        assert digest(ROOT/name)==value
    assert digest(ROOT/identity['production_PE_path'])==PE
    assert digest(identity['DLL_path'])==DLL
    return dict(entries=entries,paid_starts=starts,paid_outer_seconds=seconds,qualification_starts=qs,
                qualification_seconds=qt,qualification_budget_exhausted=True,all_fees_closed=True,
                frozen_production_source_files=len(identity['source_bindings']),frozen_helper_files=len(frozen['helpers']),
                live_PE_SHA=PE,live_DLL_SHA=DLL,
                identity_check_limitation='hash equality binds reviewed live source and saved bytes; it is not native reproduction')


def main():
    began=time.perf_counter();at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    findings=[]
    result=dict(executor='Codex separate task agent /root/round120_extra_review',
        executor_relationship='different executor from implementation/orchestration; not independent third-party native reproduction',
        review_started_UTC=at,implementation='new stdlib-only LP/MPS parsers, full-row and all-column residual calculations, exact Fraction physical objective/enumeration and endpoint algebra, own R108 comparisons',
        imports_no_prior_audit_implementation=True,Optimize=0,new_native_starts=0,
        write_scope=['scripts/round120_extra_review.py','results/unified_exact_round120/review/extra_review.json','results/unified_exact_round120/review/extra_review.md'],
        limits=['no executable or solver API, no Optimize, compilation, retry, candidate/helper/criteria mutation, package or Git action',
                'saved numerical LP proofs remain numerical; exact coefficient arithmetic is not a rational solver certificate',
                'formal native API complete matrices were not re-read here; exported complete matrices, all-column native Start type/value readbacks, scalar native row coefficients and saved complete diagnostic API matrices are reviewed',
                'historical directed comparison relies on frozen source/reports, not a new exhaustive history search',
                'pre-script source-inspection/tooling duration unmeasured; measured engineering_seconds covers this pure review computation'])
    result['small_BRP']=small_enumeration()
    print('tiny physical enumeration, all-column embeddings, midpoint and actual-MPS objective constant checked',flush=True)
    result['complete_LP_diagnostics']=diagnostics()
    print('six complete LP primal/matrix/MPS checks finished',flush=True)
    CACHE.clear()
    result['formal']=formal_and_exposure()
    print('twelve formal arms, all eighteen pair decisions and full Start vectors checked',flush=True)
    result['stage']=math_and_stage(result['formal'])
    result['fees_and_freeze']=fees_and_freeze()
    directories=[OUT/'qualification/native_contract',OUT/'qualification/native_contract02']
    directories += list((OUT/'qualification').glob('export_*/external'))
    directories += list((OUT/'qualification').glob('export_*/external/models'))
    for base in [OUT/'campaign',OUT/'qualification/h100',OUT/'qualification/chain']:
        directories += list(base.glob('group*/raw/*/external/models')) if base.name=='campaign' else list(base.glob('raw/*/external/models'))
    paths=sorted(set(Path(str(p)[:-len('.round120.json')]) for d in directories for p in d.glob('*.lp.round120.json')))
    result['all_saved_extension_endpoint_checks']=[extension_audit(p) for p in paths]
    result['source_review']=dict(
        reviewed=['src/Round120NativeProof.cpp','include/Round120NativeProof.hpp','src/PaperExternalGiniTree.cpp','src/GurobiBaseline.cpp','src/MipStartMapping.cpp','src/main.cpp','tests/round120_qualification.cpp','tests/round120_lp_diagnostics.cpp','tests/round120_qualification_support.hpp'],
        installation='solveBudgeted installs before backend solve; proof capture requires complete returned optimal child LP and readback gates; firstInteger seals first root-or-descendant request and forbids late root repair',
        frozen_pair='add rejects overwrite, ignores after decision/readiness, checks own model SHA and witnesses; only L0 depth0 paid pair admitted; incumbent changes observe but do not replace pair',
        lifecycle='initial discard is paid LP state before first integer request; original ensureArtifact carries root extension only after admitted installation and rechecks containing root scope; target/terminal reuse same extended artifact in actual arms',
        model='exactly one B selector/default priority and three ordinary linear rows; no indicator, user-cut or lazy-row installation; actual Start loops over every native column and complete matrix',
        callbacks='R120 records physical/native/relaxation values and fails on real evidence contradiction; valid-proof/U crossing has no terminate, contraction, model edit or Optimize path; R119 terminate path is isolated by main option validation',
        scope_limit='descendant carry/late/split/deadline negative cases are injected finite C++ fixtures; actual formal run exposure is one root and two original MIP requests per candidate; no descendant carry observed',
        solver_internal='h incumbent values/numerical crossings do not establish fixing or branching; tree retention unknown')
    result['mathematical_review']=dict(
        embedding='For each original physical solution in root and cutoff, set g=true G, exact inventory state and g-state/product auxiliaries, original route/resource columns, and h=0 for G<=m else1. Child proof plus its own cutoff complement gives beta. Full physical F is preserved. Every strict improver lies below original own cutoff; outside tail F>=G suffices.',
        converse='Extension restricts original integer formulation; unchanged integer projection and native f>=physical F survive. Native auxiliary f is never an unverified physical UB.',
        model_g='Epigraph model g can exceed true G. A virtual-g auxiliary completion may be removed while exact-g completion survives; the twelve actual full-matrix midpoint cases verify this distinction. Thus pre-Optimize projection equivalence does not license callback g<=m or global user-cut validity.',
        cutoff='min(ell_j,c_j) separately for each source: F<=c_j uses the LP proof; F>c_j uses cutoff complement. Example ell=1,c=.5,F=.6 shows why ell alone is invalid.',
        symmetric_projection='If beta1>=beta0: f>=beta0 and f>=beta0+(beta1-beta0)(g-m)/(b-m). If beta0>beta1: f>=beta1 and f>=beta1+(beta0-beta1)(m-g)/(m-a). Proven by feasible h interval elimination; shared midpoint closed on both sides; no epsilon gap.',
        improvement='For the ideal exact mathematical rows, f<=u<beta1 excludes h1, yielding g<=m, and symmetrically. For the conservatively serialized rows, the exact operative threshold is the stored objective_base+objective_delta+ObjCon and the remaining g bound is the stored upper_base, with the recorded tiny outward slacks. A separately recorded physical own U need not be native incumbent/cutoff, so propagation is not inferred.',
        scope='a root certificate can be carried to a contained descendant; child bound cannot be generalized to its parent. Degenerate/missing/unknown proofs are rejected. Source contradiction invalidates all dependent rows/bounds/closure and a valid own fleet does not restore exactness.',
        history='R119 remains STOP, original failed tail preserved and only authorized R120 supplement passed; R41/R42 copied full child blocks/segment hierarchies/coalescing, whereas R120 adds only paid scalar root proof rows; this is a directed substantive distinction, not a novelty theorem')
    result['findings']=findings
    result['audit_development_notes']=[
        'Auditor initially compared runtime launch metadata with frozen launch dictionaries as full equality; corrected to exact frozen-field equality plus separate runner/protocol hash checks.',
        'Auditor initially required printed native final bound and retained qualified controller L to agree within 1e-10. Actual F2 controller L is slightly weaker; preserved original L and checked printed bound is no lower and differs by at most the inherited 1e-7 policy. No bound was replaced or clipped.',
        'A duplicate qualification keyword in the new review dictionary was corrected. These were Python reviewer-development failures; frozen experiment artifacts and decision criteria were never changed.']
    result['conclusion']='No blocking mathematical, data-comparison, budget, or lifecycle evidence defect found within the stated saved-data/source review scope. The finite ADVANCE exit follows the frozen priority rules; C2 severe M-B loss and all-open N40 risk remain explicit.'
    result['engineering_seconds']=time.perf_counter()-began
    result['human_seconds']='unknown'
    result['review_completed_UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['audit_script_SHA']=digest(Path(__file__))
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'extra_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md='''# Round120 separate-executor review\n\nDifferent executor: `/root/round120_extra_review`. This is a pure saved-data/source review, not independent third-party native reproduction. Optimize **0**, new native starts **0**. No frozen artifact, candidate, helper, criterion, argv, or fee was changed.\n\nThe new Python implementation independently parses LP/MPS, enumerates all three legal tiny BRP fleets, replays physical feasibility and exact rational objectives, checks all 18 saved complete embeddings and 12 native Start-state readbacks, and recomputes the 12 midpoint auxiliary cases. It checks every row/bound of all six complete diagnostic primal points against the original LP, saved API matrix and actual MPS; positive D1-row violations independently establish nonredundancy in the extended (original variables, h) LP. Equal D0/D1 objective minima do not show a stronger objective minimum. Full formal and qualification Start vectors, source model continuity, one-selector/three-row construction, decimal/binary64 endpoint sums, and the corrected actual MPS objective constant are audited directly.\n\nThe failed LP-text offset fixture remains a charged failure. Corrected actual API/MPS ObjCon=.25 tests coefficient arithmetic, while production original BRP ObjCon remains zero. Injected negative lifecycle cases are distinct from the real C++ chain and six formal candidate native exposures. Native h fixing/branching and whole-tree retention remain unknown.\n\nAll 18 pair classifications/severities agree with an independently implemented R108 rule. All 12 formal positions and their three clocks agree with raw-backed replay, prescribed order/caps, the same PE/DLL, and closed fees: 31 starts / 32358.098361730576 outer seconds; qualification 16 / 817.8110692501068. No further native qualification was run.\n\n**ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION** follows the frozen stage priority. F2 retains the same nonzero certificate and D1 wins versus M-B and D0; C2 D1/M-B is a severe loss, D1/P a nonsevere loss and D1/D0 a win. N40 remains open for every method; D1 improves own U while its L is slightly weaker than M-B/D0. D0/P severe outcomes are not an invented veto on D1, and D0 is not promoted.\n\nNo blocking defect was found within this scope. The detailed JSON records exact limits: saved numerical LP proofs are not rational certificates; this review did not re-read every formal matrix through a solver API or reproduce native search, and historical novelty is only the directed documented comparison.\n'''
    md+=f'\nMeasured pure-review computation: {result["engineering_seconds"]:.6f} seconds. Prior source inspection/tooling duration is unmeasured; human time unknown.\n'
    (DEST/'extra_review.md').write_text(md,encoding='utf-8')
    print(json.dumps(dict(stage=result['stage']['stage'],findings=findings,engineering_seconds=result['engineering_seconds'],Optimize=0,new_native_starts=0,output=rel(DEST/'extra_review.json'))),flush=True)


if __name__=='__main__':
    main()
