"""Independent, paid R103 evidence review. No production algorithm imports."""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
import sys
import time
import traceback
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round103'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
COUNTS = dict(Optimize_attempts=0, DP_attempts=0, DP_returns=0,
              support_recomputations=0, model_read_attempts=0,
              model_read_returns=0, validated_plans=0)
REPORT = dict(schema='round103-independent-review-v1', status='RUNNING',
              method='original station order; independent full 2D DP per distinct travel layer',
              own_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              counts=COUNTS, members=[], supports=[], matrices=[], fees=[], notes=[])


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write_report():
    (HERE / 'independent_review01.json').write_text(
        json.dumps(REPORT, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def event(kind, **extra):
    with (HERE / 'independent_review01.calls.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps(dict(event=kind, seconds=time.perf_counter()-TICK, **extra))+'\n')


def exact(x):
    return F.from_float(float(x))


def lower_add(a, b):
    if not a:
        return b
    if not b:
        return a
    return max(0., math.nextafter(a+b, -math.inf))


def lower_mul(a, n):
    return max(0., math.nextafter(a*n, -math.inf)) if a and n else 0.


def plan_check(c, vehicle, plan, anchors=()):
    assert c['valid'] and len(plan)==len(c['initial']) and plan[0]==[0, 0, 0]
    q = c['capacities'][vehicle]
    total_p = total_d = 0
    travel = 0.
    for i, (p, d, z) in enumerate(plan[1:], 1):
        assert all(type(x) is int for x in (p, d, z))
        assert 0 <= p <= min(q, c['initial'][i])
        assert 0 <= d <= min(q, c['station_capacity'][i]-c['initial'][i])
        assert not (p and d) and z==int(bool(p or d))
        total_p += p
        total_d += d
        if z:
            travel = max(travel, lower_add(c['shortest_lower'][0][i], c['shortest_lower'][i][0]))
    active = [i for i in anchors if plan[i][2]]
    if active:
        costs = []
        for order in itertools.permutations(active):
            val, prev = 0., 0
            for i in order:
                val = lower_add(val, c['shortest_lower'][prev][i])
                prev = i
            costs.append(lower_add(val, c['shortest_lower'][prev][0]))
        travel = max(travel, min(costs))
    assert total_d <= total_p
    assert lower_add(travel, lower_mul(c['handling_lower'], total_p)) <= c['horizon_upper']
    COUNTS['validated_plans'] += 1
    return dict(P=total_p, D=total_d, travel=travel)


def mixture(c, vehicle, entries, point, anchors=(), reported=None, restricted=None):
    weights = [F(x['lambda_rational']) for x in entries]
    assert all(x >= 0 for x in weights) and sum(weights, F(0))==1
    for e in entries:
        plan_check(c, vehicle, e['plan'], anchors)
    n = len(c['initial'])
    mean = [[sum((a*e['plan'][i][t] for a, e in zip(weights, entries)), F(0))
             for t in range(3)] for i in range(n)]
    maximum = zero = F(0)
    q = c['capacities'][vehicle]
    for i in range(1, n):
        widths = (min(q, c['initial'][i]), min(q, c['station_capacity'][i]-c['initial'][i]), 1)
        for t, tag in enumerate(('p', 'd', 'z')):
            error = abs(mean[i][t]-exact(point[f'{tag}_{vehicle}_{i}']))
            if widths[t]:
                maximum = max(maximum, error/widths[t])
            else:
                zero = max(zero, error)
    assert maximum <= exact(1e-8) and zero <= exact(1e-8)
    return dict(vehicle=vehicle, anchors=list(anchors), plan_count=len(entries),
                exact_nonnegative_mass_one=True, exact_rational_normalized_residual=str(maximum),
                normalized_residual=float(maximum), zero_width_residual=float(zero),
                reported_residual=reported, reported_restricted_distance=restricted,
                reported_float_covers_exact_residual=(exact(reported)>=maximum if reported is not None else None),
                exact_matching_point=(maximum==0 and zero==0)), mean


def own_support(c, proof):
    """Rebuild every layer separately, never use the production sorted prefix DP."""
    k, weights = proof['vehicle'], proof['weights']
    assert not proof['anchors']
    COUNTS['support_recomputations'] += 1
    event('support_begin', vehicle=k)
    q, n = c['capacities'][k], len(c['initial'])
    aa = [0]+[min(q, c['initial'][i]) for i in range(1, n)]
    bb = [0]+[min(q, c['station_capacity'][i]-c['initial'][i]) for i in range(1, n)]
    ell = [0.]+[lower_add(c['shortest_lower'][0][i], c['shortest_lower'][i][0]) for i in range(1, n)]
    limit = next((p-1 for p in range(1, sum(aa)+2)
                  if p>sum(aa) or lower_mul(c['handling_lower'], p)>c['horizon_upper']), sum(aa))
    assert limit==proof['resource_limit']
    best, layers = 0, []
    for level in sorted(set(ell[1:])):
        cap = max([-1]+[p for p in range(limit+1)
                       if lower_add(level, lower_mul(c['handling_lower'], p))<=c['horizon_upper']])
        COUNTS['DP_attempts'] += 1
        event('DP_begin', vehicle=k, level=level, limit=limit, cap=cap)
        # Sparse exact Python integers and no D<=P intermediate restriction.
        table = {(0, 0): 0}
        for i in range(1, n):
            if ell[i]>level:
                continue
            nxt = dict(table)
            wp, wd, wz = weights[i]
            for (p, d), value in table.items():
                for add in range(1, min(aa[i], limit-p)+1):
                    key = (p+add, d)
                    score = value+wp*add+wz
                    if key not in nxt or score>nxt[key]:
                        nxt[key] = score
                for add in range(1, min(bb[i], limit-d)+1):
                    key = (p, d+add)
                    score = value+wd*add+wz
                    if key not in nxt or score>nxt[key]:
                        nxt[key] = score
            table = nxt
        layer_best = max([0]+[v for (p, d), v in table.items() if d<=p<=cap])
        best = max(best, layer_best)
        COUNTS['DP_returns'] += 1
        layers.append(dict(level=level, cap=cap, best=layer_best, states=len(table)))
        event('DP_return', vehicle=k, level=level, best=layer_best)
    witness = plan_check(c, k, proof['solution'])
    witness_score = sum(a*b for wr, pr in zip(weights, proof['solution']) for a, b in zip(wr, pr))
    assert best==proof['upper']==witness_score
    event('support_return', vehicle=k, upper=best)
    return dict(vehicle=k, independent_upper=best, saved_upper=proof['upper'],
                witness_score=witness_score, witness_resources=witness,
                level_DP_count=len(layers), layers=layers)


def matrix_check(model, values, label, integer=False):
    variables = model.getVars()
    assert len(values)==len(variables) and set(values)=={v.VarName for v in variables}
    maximum, where = 0., None
    worst_signed = 0.
    for v in variables:
        x = values[v.VarName]
        assert math.isfinite(x)
        residual = max(v.LB-x, x-v.UB, 0.)
        if integer and v.VType!='C':
            residual = max(residual, abs(x-round(x)))
        if residual>maximum:
            maximum, where = residual, 'bound:'+v.VarName
    for row in model.getConstrs():
        expression = model.getRow(row)
        lhs = math.fsum(expression.getCoeff(j)*values[expression.getVar(j).VarName]
                        for j in range(expression.size()))
        signed = lhs-row.RHS
        residual = abs(signed) if row.Sense=='=' else max(0., signed if row.Sense=='<' else -signed)
        if residual>maximum:
            maximum, where, worst_signed = residual, row.ConstrName, signed
    objective = math.fsum([model.ObjCon]+[v.Obj*values[v.VarName] for v in variables])
    assert maximum <= 1e-6
    return dict(label=label, scope='reader-only numerical full original matrix; no rational matrix proof',
                columns=len(variables), rows=model.NumConstrs, objective=objective,
                maximum_absolute_residual=maximum, worst_row=where, worst_signed_residual=worst_signed,
                integer_domain_checked=integer, Optimize_calls=0)


def load_model(gp, engine, path):
    COUNTS['model_read_attempts'] += 1
    event('model_read_begin', path=str(path))
    m = gp.read(str(path), env=engine)
    COUNTS['model_read_returns'] += 1
    event('model_read_return', rows=m.NumConstrs, columns=m.NumVars)
    return m


def same_original_model(original, enriched, rows):
    oldv, newv = original.getVars(), enriched.getVars()
    assert len(oldv)==len(newv)
    for a, b in zip(oldv, newv):
        assert (a.VarName, a.VType, a.LB, a.UB, a.Obj)==(b.VarName, b.VType, b.LB, b.UB, b.Obj)
    assert (original.ModelSense, original.ObjCon)==(enriched.ModelSense, enriched.ObjCon)
    newer = {r.ConstrName:r for r in enriched.getConstrs()}
    oldnames = set()
    def coefficients(m, r):
        expr = m.getRow(r)
        return {expr.getVar(j).VarName:exact(expr.getCoeff(j)) for j in range(expr.size())}
    for a in original.getConstrs():
        b = newer[a.ConstrName]
        oldnames.add(a.ConstrName)
        assert (a.Sense, exact(a.RHS))==(b.Sense, exact(b.RHS))
        assert coefficients(original, a)==coefficients(enriched, b)
    extras = [r for r in enriched.getConstrs() if r.ConstrName not in oldnames]
    assert len(extras)==len(rows)
    for saved in rows:
        want = {name:exact(a) for name, a in saved['coefficients']}
        matches = [r for r in extras if coefficients(enriched, r)==want]
        assert len(matches)==1 and matches[0].Sense=='<' and exact(matches[0].RHS)==exact(saved['rhs'])
    return dict(exact_binary64_coefficients_domains_objective_original_rows_preserved=True,
                original_rows=original.NumConstrs, enriched_rows=enriched.NumConstrs, new_rows=len(extras))


def fee_check(label):
    folder = OUT/'diagnostics'/label
    summary = read(folder/'summary.json')
    receipt = read(OUT/'fees'/label/'receipt.json')
    record = dict(label=label, receipt=receipt)
    assert receipt['exit_code']==0 and receipt['stop_reason']=='normal_return'
    if label.startswith('capacity'):
        outer = [json.loads(s) for s in (folder/'outer_calls.jsonl').read_text().splitlines()]
        master = []
        for p in folder.glob('iteration_*/master_calls.jsonl'):
            master += [json.loads(s) for s in p.read_text().splitlines()]
        dp = sum(1 for _ in (folder/'oracle_calls.jsonl').open())
        outer_begin = sum(x.get('event')=='begin' for x in outer)
        outer_return = sum('status' in x for x in outer)
        master_begin = sum(x.get('event')=='begin' for x in master)
        master_return = sum('status' in x for x in master)
        assert outer_begin==outer_return==summary['outer_Optimize_calls']
        assert master_begin==master_return==summary['master_Optimize_calls']
        assert dp==summary['DP_calls']
        record.update(outer_Optimize_attempts=outer_begin, master_Optimize_attempts=master_begin,
                      DP_returns=dp, declared_status=summary['status'],
                      L0=summary['L0'], LJ=summary['LJ'], LH=summary['LH'],
                      signed_LJ_minus_L0=summary['LJ']-summary['L0'])
    else:
        assert read(folder/'Optimize_begin.json')['call']==1
        assert read(folder/'Optimize_return.json')['call']==1
        record.update(Optimize_attempts=1, DP_returns=summary['DP_calls'])
    return record


def run():
    global TICK
    TICK = time.perf_counter()
    from round100_idle import ensure_idle
    ensure_idle()
    write_report()
    event('audit_begin')
    from round100_gurobi_runtime import gp, binding
    # Catch accidental Optimize calls, including ones inherited from helpers.
    def forbidden_optimize(*args, **kwargs):
        COUNTS['Optimize_attempts'] += 1
        event('FORBIDDEN_Optimize_attempt')
        raise RuntimeError('Independent review forbids Optimize')
    gp.Model.optimize = forbidden_optimize
    native = OUT/'native01/raw/02_F2_H-SUBMIT/external/native_logs'
    prefix = native/'L0_c6_1_child_disjunction_target_mip.gurobi.log'
    rows_document = read(str(prefix)+'.round103.rows.json')
    contract_document = read(str(prefix)+'.round103.contract.json')
    c = contract_document['column_contract']['resource']
    assert rows_document['source_sha256']==contract_document['source_sha256']
    for row in rows_document['rows']:
        assert len(row['proofs'])==1
        proof = row['proofs'][0]
        result = own_support(c, proof)
        factors = []
        for name, a in row['coefficients']:
            tag, k, i = name.split('_')
            assert int(k)==proof['vehicle']
            factors.append(exact(a)/proof['weights'][int(i)][('p', 'd', 'z').index(tag)])
        factor = factors[0]
        assert factor>0 and all(f==factor for f in factors)
        assert factor.numerator & (factor.numerator-1)==0
        assert factor.denominator & (factor.denominator-1)==0
        assert exact(row['rhs'])==factor*result['independent_upper']
        result.update(exact_dyadic_row_scaling=str(factor), rhs=row['rhs'], exact_rhs_matched=True)
        REPORT['supports'].append(result)
        write_report()
    with gp.Env(empty=True) as engine:
        engine.setParam('OutputFlag', 0)
        engine.start()
        REPORT['runtime'] = binding()
        for label in ('capacity_C2_01', 'capacity_F2_01'):
            folder = OUT/'diagnostics'/label
            plan = read(folder/'plan.json')
            contract = read(folder/'contract.json')['resource']
            iteration = max(folder.glob('iteration_*'), key=lambda p:int(p.name.split('_')[1]))
            point_file = read(iteration/'complete_point.json')
            point = dict(zip(point_file['names'], point_file['values']))
            for path in sorted(iteration.glob('vehicle_*.json')):
                saved = read(path)
                assert saved['status']=='INSIDE'
                record, _ = mixture(contract, saved['vehicle'], saved['combination'], point,
                                    reported=saved['normalized_residual'], restricted=saved['restricted_distance'])
                record.update(label=label, iteration=iteration.name,
                              saved_reason=saved['reason'], certificate_arithmetic='exact rational, generally not dyadic')
                REPORT['members'].append(record)
            source = ROOT/plan['source']
            assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['source_sha256']
            with load_model(gp, engine, source) as model:
                REPORT['matrices'].append(matrix_check(model, point, label))
            write_report()
        for label in ('primal_F5_base01', 'primal_F5_anchor01'):
            folder = OUT/'diagnostics'/label
            saved, plan = read(folder/'upper_witness.json'), read(folder/'plan.json')
            parent = OUT/'diagnostics'/plan['parent']
            parent_plan = read(parent/'plan.json')
            contract = read(parent/'contract.json')['resource']
            for combo in saved['combinations']:
                record, _ = mixture(contract, combo['vehicle'], combo['combination'], saved['point'], combo['anchors'])
                record.update(label=label, certificate_arithmetic='exact rational, generally not dyadic')
                REPORT['members'].append(record)
            source = ROOT/parent_plan['source']
            assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['source_sha256']
            with load_model(gp, engine, source) as model:
                check = matrix_check(model, saved['point'], label)
            summary = read(parent/'summary.json')
            check.update(hull_upper_numeric_objective=check['objective'],
                         outer_LB=summary['certified_outer_approximation_LB'],
                         signed_upper_minus_outer_LB=check['objective']-summary['certified_outer_approximation_LB'],
                         restricted_finite_column_direction='upper for hull LP; not route UB nor BRP LB')
            REPORT['matrices'].append(check)
            write_report()
        source = Path(contract_document['source_path'])
        enriched = Path(str(prefix)+'.round103.lp')
        summary = read(str(prefix)+'.round103.summary.json')
        assert hashlib.sha256(enriched.read_bytes()).hexdigest()==summary['canonical_sha256']
        with load_model(gp, engine, source) as original, load_model(gp, engine, enriched) as augmented:
            REPORT['native_model_preservation'] = same_original_model(original, augmented, rows_document['rows'])
            start = {}
            for item in csv.DictReader(Path(str(prefix)+'.round68.start.values.csv').open(newline='')):
                assert exact(float(item['value']))==exact(float(item['readback']))
                start[item['variable']] = float(item['value'])
            REPORT['matrices'].append(matrix_check(augmented, start, 'native01_F2_Start', integer=True))
        calls = [json.loads(s) for s in Path(str(prefix)+'.round103.calls.jsonl').read_text().splitlines()]
        for kind, total in [('Optimize', summary['Optimize_calls']), ('DP', summary['DP_calls'])]:
            assert sum(x['event']==kind+'_begin' for x in calls)==total
            assert sum(x['event']==kind+'_return' for x in calls)==total
        REPORT['native_preparation'] = summary
        write_report()
    for label in ('capacity_C2_01', 'capacity_F2_01', 'capacity_F5_01', 'capacity_anchor_F5_01',
                  'primal_F5_base01', 'primal_F5_anchor01'):
        REPORT['fees'].append(fee_check(label))
    for arm in ('01_F2_H-SHADOW', '02_F2_H-SUBMIT'):
        completion = read(OUT/'native01/raw'/arm/'completion.json')
        assert completion['returncode']==0 and completion['within_cap']
        REPORT['fees'].append(dict(label=arm, end_to_end_seconds=completion['end_to_end_seconds'],
                                  process_cap_seconds=completion['process_cap_seconds'],
                                  process_wall_seconds=completion['process_wall_seconds'], within_cap=True))
    REPORT['notes'] += ['Tiny signed brackets retained; no clipping and no exact full-hull equality claimed.',
                        'No native branch-and-bound rerun and no Optimize; saved native acceptance claims not regenerated.',
                        'Historic C2 reason string says exact_dyadic; normalized supplied weights are exact rational.',
                        'Each full travel-layer recurrence is counted as an independent DP attempt.']
    assert COUNTS['Optimize_attempts']==0 and COUNTS['DP_attempts']==COUNTS['DP_returns']
    REPORT['status'] = 'PASSED_WITH_NUMERICAL_SCOPE_LIMITATIONS'
    REPORT['inner_seconds'] = time.perf_counter()-TICK
    event('audit_return', status=REPORT['status'], counts=COUNTS)
    write_report()
    print(json.dumps(dict(status=REPORT['status'], counts=COUNTS, inner_seconds=REPORT['inner_seconds'])), flush=True)


if __name__=='__main__':
    if sys.argv[1:] == ['--receipt']:
        from round103_common import receipt, PYTHON
        receipt('independent_review01', [PYTHON, __file__, '--run'], cap=300, engineering=False)
    elif sys.argv[1:] == ['--run']:
        try:
            run()
        except BaseException:
            REPORT['status']='FAILED_PRESERVED_ATTEMPT'
            REPORT['error']=traceback.format_exc()
            if 'TICK' in globals():
                REPORT['inner_seconds']=time.perf_counter()-TICK
                event('audit_failure', error=REPORT['error'])
            write_report()
            raise
    else:
        raise SystemExit('Use --receipt exactly once; --run is its exclusive child.')
