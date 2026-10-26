"""Independent R104 delivery reader. No Optimize, DP, build or model mutation.

Run only after explicit idle admission, through the round104 paid wrapper.
The exact-arithmetic checks below are independent of the implementation's
interval accumulation and of its production/audit/reporting helper routines.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys
import time
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'results/unified_exact_round104'
sys.path.insert(0, str(ROOT / 'scripts'))
EXPECTED_SOURCE = 'a37e2165fb900bb0d26d9158b89ade883202049456b7d1c6180f361070638091'
COUNTERS = dict(checks=0, phases_started=0, phases_returned=0, model_reads_started=0,
                model_reads_returned=0, aggregate_rows=0, aggregate_source_rows=0,
                coefficient_conversions=0, deleted_nonzero_coefficients=0,
                python_grouped_rows=0, python_grouped_native_tiny_terms=0,
                primal_rows=0, primal_bound_coordinates=0, dual_rows=0,
                stationarity_coordinates=0, start_rows=0, support_profit_rows=0,
                production_Optimize_begin=0, production_Optimize_return=0,
                production_DP_begin=0, production_DP_return=0,
                Optimize_calls=0, DP_calls=0)
HASHES = {}
WARNINGS = []
DEST = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path):
    path = Path(path).resolve()
    label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    HASHES[label] = sha(path)
    return path


def read(path):
    return json.loads(bind(path).read_text(encoding='utf-8-sig'))


def save(name, value):
    path = DEST / name
    with path.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def log(event, **data):
    with (DEST / 'attempts.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(event=event, elapsed=time.perf_counter()-START,
                                     **data), allow_nan=False) + '\n')


def check(condition, label):
    COUNTERS['checks'] += 1
    if not condition:
        raise AssertionError(label)


def exact(value):
    value = float(value)
    check(math.isfinite(value), 'nonfinite exact-arithmetic input')
    return Fraction.from_float(value)


def number(value):
    return dict(exact=str(value), float=float(value))


def phase(name, action):
    COUNTERS['phases_started'] += 1
    log('phase_begin', phase=name)
    result = action()
    COUNTERS['phases_returned'] += 1
    log('phase_return', phase=name)
    save('counters.json', COUNTERS)
    return result


def read_model(gp, env, path):
    path = bind(path)
    COUNTERS['model_reads_started'] += 1
    log('model_read_begin', path=str(path), sha256=sha(path))
    model = gp.read(str(path), env=env)
    COUNTERS['model_reads_returned'] += 1
    log('model_read_return', path=str(path))
    return model


def extract(model):
    variables = model.getVars()
    check(model.ModelSense == 1 and model.NumQNZs == 0 and model.NumQConstrs == 0 and
          model.NumGenConstrs == 0 and model.NumSOS == 0,
          'actual original source must be linear minimization')
    names = [v.VarName for v in variables]
    check(len(set(names)) == len(names), 'duplicate original column names')
    rows = []
    for constr in model.getConstrs():
        expr = model.getRow(constr)
        rows.append(dict(sense=constr.Sense, rhs=constr.RHS,
                         coefficients=[(expr.getVar(j).index, expr.getCoeff(j))
                                       for j in range(expr.size())]))
    return dict(names=names, types=[v.VType for v in variables],
                lower=[v.LB for v in variables], upper=[v.UB for v in variables],
                objective=[v.Obj for v in variables], constant=model.ObjCon,
                sense=model.ModelSense, rows=rows)


def literal_rows(rows, matrix):
    byname = {name: j for j, name in enumerate(matrix['names'])}
    result = []
    for row in rows:
        terms = [(byname[name], value) for name, value in row['coefficients']]
        check(len({j for j, value in terms}) == len(terms), 'duplicate new row column')
        result.append(dict(sense='<', rhs=row['rhs'], coefficients=terms))
    return result


def aggregates(matrix):
    pooldir = OUT / 'diagnostics/pool_F2_02'
    old = read(pooldir / 'ALL.rows.json')
    dual = read(pooldir / 'dual_support.json')
    cpp = read(OUT / 'diagnostics/cpp_qualify02/grouped.cpp.json')['rows']
    check(len(old) == len(dual['multipliers']) == len(dual['all_Pi']), 'historical pool dual map')
    for lam, pi in zip(dual['multipliers'], dual['all_Pi']):
        check(lam == max(0.0, -pi), 'actual nonnegative sign repair mapping')
    names = matrix['names']
    byname = {name: i for i, name in enumerate(names)}
    results = []
    for row in cpp:
        COUNTERS['aggregate_rows'] += 1
        log('aggregate_begin', vehicle=row['vehicle'])
        expected = [j for j, source in enumerate(old)
                    if source['vehicle'] == row['vehicle'] and dual['multipliers'][j] > 0]
        check(row['source_rows'] == expected, 'group source rows exactly match repaired support')
        abar = {}
        bbar = Fraction(0)
        for j in expected:
            source = old[j]
            check(source['sense'] == '<' and source['index'] == j, 'actual source row sense/index')
            weight = exact(dual['multipliers'][j])
            check(weight >= 0, 'nonnegative aggregate multiplier')
            bbar += weight * exact(source['rhs'])
            for name, value in source['coefficients']:
                i = byname[name]
                abar[i] = abar.get(i, Fraction(0)) + weight * exact(value)
            COUNTERS['aggregate_source_rows'] += 1
        ahat = {int(i): exact(value) for i, value in row['coefficients']}
        check(len(ahat) == len(row['coefficients']), 'distinct submitted aggregate columns')
        check(set(ahat) <= set(abar), 'aggregate has no unexplained submitted columns')
        correction = Fraction(0)
        deleted = []
        conversions = []
        for i, a in abar.items():
            delta = ahat.get(i, Fraction(0)) - a
            if not delta:
                continue
            lo, hi = matrix['lower'][i], matrix['upper'][i]
            check(math.isfinite(lo) and math.isfinite(hi) and abs(lo) < 1e100 and abs(hi) < 1e100,
                  'actual changed aggregate coordinate has finite global bounds')
            margin = max(delta * exact(lo), delta * exact(hi))
            correction += margin
            COUNTERS['coefficient_conversions'] += 1
            conversions.append(dict(column=names[i], delta=str(delta), required_margin=str(margin)))
            if i not in ahat and a:
                COUNTERS['deleted_nonzero_coefficients'] += 1
                deleted.append(names[i])
        saved_correction = exact(row['compensation_upper'])
        safe_margin = exact(row['rhs']) - bbar - correction
        check(saved_correction >= correction, 'C++ compensation encloses exact signed endpoint sum')
        check(safe_margin >= 0, 'actual C++ RHS is safe for exact nonnegative combination')
        result = dict(vehicle=row['vehicle'], source_rows=expected,
                      exact_weighted_rhs=number(bbar), exact_required_compensation=number(correction),
                      saved_compensation_excess=number(saved_correction-correction),
                      rhs_minus_exact_weighted_rhs=number(exact(row['rhs'])-bbar),
                      exact_validity_margin=number(safe_margin), deleted_nonzero_columns=deleted,
                      conversions=conversions)
        results.append(result)
        log('aggregate_return', vehicle=row['vehicle'], safe=True)
    save('independent_aggregates.json', results)
    return results


def row_violation(row, x):
    activity = sum((exact(a)*x[j] for j, a in row['coefficients']), Fraction(0))
    signed = activity-exact(row['rhs'])
    if row['sense'] == '<':
        violation = max(Fraction(0), signed)
    elif row['sense'] == '>':
        violation = max(Fraction(0), -signed)
    else:
        check(row['sense'] == '=', 'unsupported original row sense')
        violation = abs(signed)
    return activity, signed, violation


def python_grouped_scope(matrix):
    """Inspect potentially native-deleted terms without building or solving a model."""
    rows = read(OUT/'diagnostics/pool_F2_02/GROUPED.rows.json')
    byname = {name: i for i, name in enumerate(matrix['names'])}
    result = []
    for r, row in enumerate(rows):
        COUNTERS['python_grouped_rows'] += 1
        terms = []
        for name, coefficient in row['coefficients']:
            if coefficient and abs(coefficient) < 1e-13:
                j = byname[name]
                fixed_zero = matrix['lower'][j] == matrix['upper'][j] == 0
                terms.append(dict(column=name, coefficient=coefficient,
                    lower=matrix['lower'][j], upper=matrix['upper'][j], fixed_zero=fixed_zero))
                COUNTERS['python_grouped_native_tiny_terms'] += 1
        harmless = all(term['fixed_zero'] for term in terms)
        result.append(dict(row=r, vehicle=row['vehicle'], tiny_terms=terms,
            deleting_all_potential_native_tiny_terms_harmless=harmless,
            native_added_coefficient_readback_available=False,
            scope='Python exported coefficient conversion is compensated, but native deletion was not explicitly compensated or individually read back; zero-fixed terms contribute exactly zero'))
        if not harmless:
            WARNINGS.append(f'Python historical GROUPED row {r} has potentially dropped nonzero-domain tiny terms; emitted native-row validity unqualified without native readback')
    save('python_grouped_scope.json', result)
    return result


def full_solution(matrix, added, solution, tag):
    for attribute in ['ConstrVio', 'BoundVio', 'DualVio']:
        check(0 <= solution[attribute] <= 1e-7, tag+' saved official production residual '+attribute)
    records = solution['variables']
    check([r[0] for r in records] == matrix['names'], tag+' full-X column order')
    x = [exact(r[1]) for r in records]
    rc = [exact(r[2]) for r in records]
    rows = matrix['rows'] + literal_rows(added, matrix)
    pi = [exact(value) for value in solution['Pi']]
    check(len(pi) == len(rows), tag+' complete old/new Pi count')
    primal = Fraction(0)
    max_row = -1
    sign_error = Fraction(0)
    complementarity = Fraction(0)
    station = [exact(c)-r for c, r in zip(matrix['objective'], rc)]
    dual = exact(matrix['constant'])
    for r, (row, multiplier) in enumerate(zip(rows, pi)):
        activity, signed, violation = row_violation(row, x)
        if violation > primal:
            primal, max_row = violation, r
        if row['sense'] == '<':
            sign_error = max(sign_error, multiplier)
        elif row['sense'] == '>':
            sign_error = max(sign_error, -multiplier)
        complementarity = max(complementarity, abs(multiplier*signed))
        dual += multiplier*exact(row['rhs'])
        for j, coefficient in row['coefficients']:
            station[j] -= multiplier*exact(coefficient)
        COUNTERS['primal_rows'] += 1
        COUNTERS['dual_rows'] += 1
    bound_residual = Fraction(0)
    rc_complementarity = Fraction(0)
    unbounded_dual_terms = []
    for j, (lo, hi, value, reduced) in enumerate(zip(matrix['lower'], matrix['upper'], x, rc)):
        if abs(lo) < 1e100:
            bound_residual = max(bound_residual, exact(lo)-value)
        if abs(hi) < 1e100:
            bound_residual = max(bound_residual, value-exact(hi))
        if reduced:
            endpoint = lo if reduced > 0 else hi
            if not math.isfinite(endpoint) or abs(endpoint) >= 1e100:
                unbounded_dual_terms.append(matrix['names'][j])
            else:
                dual += reduced*exact(endpoint)
                rc_complementarity = max(rc_complementarity, abs(reduced*(value-exact(endpoint))))
        COUNTERS['primal_bound_coordinates'] += 1
        COUNTERS['stationarity_coordinates'] += 1
    objective = exact(matrix['constant']) + sum((exact(c)*v for c, v in zip(matrix['objective'], x)), Fraction(0))
    obj_error = objective-exact(solution['objective'])
    stationarity = max(map(abs, station), default=Fraction(0))
    check(max(primal, bound_residual) <= exact(1e-7), tag+' original numerical primal qualification')
    check(stationarity <= exact(1e-7) and sign_error <= exact(1e-7), tag+' numerical dual qualification')
    check(abs(obj_error) <= exact(1e-7), tag+' saved objective agrees with full-X reconstruction')
    if unbounded_dual_terms:
        WARNINGS.append(tag+' dual bound evaluation has unbounded endpoint terms')
    else:
        check(abs(objective-dual) <= exact(1e-6), tag+' reconstructed numerical primal-dual objective qualification')
    check(max(complementarity, rc_complementarity) <= exact(1e-6), tag+' reconstructed numerical complementarity qualification')
    result = dict(tag=tag, rows=len(rows), new_rows=len(added), columns=len(x),
                  exact_objective=number(objective), saved_objective_difference=number(obj_error),
                  maximum_primal_row_residual=number(primal), maximum_primal_row_index=max_row,
                  maximum_bound_residual=number(bound_residual), stationarity_max=number(stationarity),
                  dual_sign_error=number(sign_error), row_complementarity_max=number(complementarity),
                  RC_complementarity_max=number(rc_complementarity),
                  dual_objective=number(dual) if not unbounded_dual_terms else None,
                  signed_primal_minus_dual=number(objective-dual) if not unbounded_dual_terms else None,
                  unbounded_dual_endpoint_terms=unbounded_dual_terms,
                  saved_official_solver_residuals={key: solution[key] for key in ['ConstrVio', 'BoundVio', 'DualVio']},
                  qualification_tolerances=dict(primal=1e-7, stationarity=1e-7, dual_sign=1e-7,
                      objective_reconstruction=1e-7, primal_dual_objective=1e-6, complementarity=1e-6),
                  official_production_qualification='saved solver ConstrVio/BoundVio/DualVio <=1e-7; saved compressed/pool objective difference <=1e-7',
                  independent_dual_gap_scope='1e-6 descriptive consistency tolerance; does not replace or relax official production1e-7 qualification',
                  qualification='exact residual evaluation of binary64 data; numerical optimum only, no rational optimality')
    save(tag+'_independent_solution.json', result)
    return result


def start_and_readback(original, actual, selected, prefix):
    for field in ['names', 'types', 'lower', 'upper', 'objective', 'constant', 'sense']:
        check(original[field] == actual[field], 'typed readback preserves old '+field)
    old_count = len(original['rows'])
    check(len(actual['rows']) == old_count+len(selected), 'canonical row count')
    check(actual['rows'][:old_count] == original['rows'], 'every original typed row unchanged')
    expected_new = literal_rows(selected, original)
    for expected, got in zip(expected_new, actual['rows'][old_count:]):
        check(expected['sense'] == got['sense'] and expected['rhs'] == got['rhs'] and
              dict(expected['coefficients']) == dict(got['coefficients']), 'actual submitted ACTIVE readback')
    metadata = read(str(prefix).replace('.round104', '.round68.start.json'))
    values_path = bind(str(prefix).replace('.round104', '.round68.start.values.csv'))
    with values_path.open(encoding='utf-8-sig', newline='') as stream:
        records = list(csv.DictReader(stream))
    check([r['variable'] for r in records] == actual['names'], 'Start full-column order')
    check([r['type'] for r in records] == actual['types'], 'Start actual original integer types')
    for row in records:
        check(float(row['value']) == float(row['readback']), 'Start submission readback exact value')
    x = [exact(r['value']) for r in records]
    maximum = Fraction(0)
    for row in actual['rows']:
        maximum = max(maximum, row_violation(row, x)[2])
        COUNTERS['start_rows'] += 1
    for j, value in enumerate(x):
        lo, hi = actual['lower'][j], actual['upper'][j]
        if abs(lo) < 1e100:
            maximum = max(maximum, exact(lo)-value)
        if abs(hi) < 1e100:
            maximum = max(maximum, value-exact(hi))
        if actual['types'][j] in ['B', 'I']:
            check(abs(value-round(value)) <= exact(1e-5), 'physical Start original integer coordinate')
    objective = exact(actual['constant'])+sum((exact(c)*v for c, v in zip(actual['objective'], x)), Fraction(0))
    check(maximum <= exact(1e-6), 'all-row original Start numerical validity')
    check(metadata['checked_rows'] == len(actual['rows']) and metadata['rows_valid'] and metadata['readback_valid'],
          'Start metadata agrees with actual submitted model')
    check(abs(objective-exact(metadata['objective'])) <= exact(1e-7), 'Start full-X objective')
    result = dict(rows=len(actual['rows']), columns=len(x), residual=number(maximum), objective=number(objective),
                  native_status=metadata['status'], exact_saved_vector_observed=metadata['exact_vector_observed_in_mipsol'],
                  qualification='full typed model/Start re-evaluation; existing physical route audit is read, not rerun')
    save('independent_readback_start.json', result)
    return result


def production_rows_and_calls(prefix, pool, selected, summary):
    dual = read(str(prefix)+'.dual.json')
    check(len(pool) == summary['pool_rows'] == len(dual['Pi']), 'fresh production pool size/dual')
    expected = [r for r, pi in zip(pool, dual['Pi']) if pi < 0]
    check([(r['coefficients'], r['rhs']) for r in expected] ==
          [(r['coefficients'], r['rhs']) for r in selected], 'selected ACTIVE is literal negative-Pi support')
    check(len(selected) == summary['submitted'], 'actual submitted count')
    for row in pool:
        proof = row['proofs'][0]
        check(proof['valid'], 'fresh row has valid support certificate')
        coefficients = dict(row['coefficients'])
        ratios = []
        for i, weights in enumerate(proof['weights'][1:], 1):
            for tag, weight in zip(['p', 'd', 'z'], weights):
                if weight:
                    ratios.append(exact(coefficients.pop(f'{tag}_{proof["vehicle"]}_{i}'))/weight)
        check(not coefficients and ratios and ratios[0] > 0 and all(r == ratios[0] for r in ratios),
              'source row matches exact signed support direction/positive scale')
        check(exact(row['rhs']) == ratios[0]*proof['upper'], 'source RHS matches retained support upper')
        profit = sum(a*b for w, p in zip(proof['weights'], proof['solution']) for a, b in zip(w, p))
        check(profit == proof['upper'], 'saved legal-plan profit matches support value')
        COUNTERS['support_profit_rows'] += 1
    calls = bind(str(prefix)+'.calls.jsonl')
    events = [json.loads(line) for line in calls.read_text().splitlines()]
    optimize_pending = {}
    dp_pending = None
    times = {}
    for event in events:
        kind = event['event']
        if kind == 'Optimize_begin':
            check(event['serial'] not in optimize_pending, 'unique ahead-of-Optimize serial')
            optimize_pending[event['serial']] = event
            COUNTERS['production_Optimize_begin'] += 1
        elif kind == 'Optimize_return':
            check(event['serial'] in optimize_pending, 'Optimize return has earlier begin')
            begin = optimize_pending.pop(event['serial'])
            check(event['return_code'] == 0, 'production auxiliary API returned successfully')
            times[begin['kind']] = times.get(begin['kind'], 0.0)+event['seconds']
            COUNTERS['production_Optimize_return'] += 1
        elif kind == 'DP_begin':
            check(dp_pending is None, 'support is serial and logged ahead of call')
            dp_pending = event
            COUNTERS['production_DP_begin'] += 1
        elif kind == 'DP_return':
            check(dp_pending is not None and dp_pending['vehicle'] == event['proof']['vehicle'], 'DP return has earlier vehicle begin')
            dp_pending = None
            COUNTERS['production_DP_return'] += 1
        else:
            raise AssertionError('unexpected production call record '+kind)
    check(not optimize_pending and dp_pending is None, 'all production auxiliary attempts returned')
    check(COUNTERS['production_Optimize_begin'] == summary['Optimize_calls'] and
          COUNTERS['production_DP_begin'] == summary['DP_calls'], 'fresh pool production accounting totals')
    save('independent_production_accounting.json', dict(stage_native_LP_seconds=times,
         whole_preparation_seconds=summary['seconds'], summary=summary,
         scope='saved serial attempts and exact direction/profit consistency; no independent full-support recurrence'))
    return times


def outcomes():
    campaign = OUT / 'control01'
    lines = bind(campaign / 'summary.jsonl').read_text().splitlines()
    records = [json.loads(line) for line in lines]
    check(len(records) == 4 and {r['arm'] for r in records} == {'P-GRB', 'ENS-C', 'OC-ACTIVE', 'OC-SHADOW'},
          'one completed four-arm F2 control, no unfinished arm')
    arms = {}
    for record in records:
        directory = Path(record['destination'])
        audit = read(directory/'audit.json')
        result = read(directory/'result.json')
        completion = read(directory/'completion.json')
        endpoint = record['endpoint']
        check(audit['passed'] and record['audit_passed'], record['arm']+' original physical/native audit')
        check(completion['returncode'] == 0 and completion['stop_reason'] == 'normal_return', record['arm']+' normal return')
        check(completion['end_to_end_seconds'] == record['completion']['end_to_end_seconds'], 'complete control publication clock')
        if endpoint['certificate']:
            check(audit['normal_result_certificate'] and endpoint['source'] == 'normal_finalized_physical_endpoint',
                  'certificate uses normal finalized complete endpoint, not earlier observational prefix')
        arms[record['arm']] = dict(seconds=completion['end_to_end_seconds'], endpoint=endpoint,
            normal_result_certificate=audit.get('normal_result_certificate'),
            final_physical_verification=audit.get('final_physical_verification'),
            physical_witness_scope='existing independent original-route audit inspected; routes not re-solved',
            audit_prefix_certificate=audit.get('certificate'),
            preparation=audit.get('resource_hull'), status=result['status'])
    a, e, s, p = (arms[name] for name in ['OC-ACTIVE', 'ENS-C', 'OC-SHADOW', 'P-GRB'])
    check(a['endpoint']['certificate'] and e['endpoint']['certificate'] and s['endpoint']['certificate'],
          'ACTIVE SHADOW ENS certified control endpoints')
    check(a['endpoint']['U'] == e['endpoint']['U'] == s['endpoint']['U'], 'same observed physical Fstar')
    protocol = read(OUT/'protocol.json')['materiality']
    difference = a['seconds']-e['seconds']
    ratio = a['seconds']/e['seconds']
    severe = difference >= protocol['severe_time_absolute'] and ratio-1 >= protocol['severe_time_relative']
    native = read(OUT/'diagnostics/native_points02/summary.json')
    c2 = [r for r in native['records'] if r['role'] == 'R98-C2']
    f5 = [r for r in native['records'] if r['role'] == 'F5']
    check(len(c2) == 5 and len(f5) == 2, 'medium-large original ENS observation scope')
    check(all(r['sets']['ALL']['reliable_over_10_native_FeasibilityTol'] == 0 for r in c2+f5),
          'finite pools have no observed C2/F5 reliable increment')
    actual_f5 = read(OUT/'diagnostics/pool_F5_native01/summary.json')
    check(actual_f5['source_sha256'] == f5[0]['source_sha256'] and actual_f5['records']['ACTIVE']['rows'] == 0,
          'actual F5 terminal source has zero objective dual support')
    decision = dict(recommendation='stop_objective_certificate_root_preprocessing',
                    cancel_unstarted_holdouts_and_long_windows=True, severe_ENS_regression=severe,
                    ACTIVE_minus_ENS_seconds=difference, ACTIVE_over_ENS_ratio=ratio,
                    ACTIVE_minus_SHADOW_seconds=a['seconds']-s['seconds'],
                    SHADOW_minus_ENS_seconds=s['seconds']-e['seconds'],
                    P_certificate=p['endpoint']['certificate'], P_censoring=not p['endpoint']['certificate'],
                    P_time_comparison='exact certified ratio only if both certify; otherwise one-sided observed bound',
                    conclusion_scope='this self-paid objective-selected single-vehicle root preprocessing; no universal valid-inequality or full-hull/native-implication rejection',
                    limitations=['one control per arm, no statistical stability',
                                 'different native paths after row submission',
                                 '12 observable original-ENS points; F5 positive nodes unavailable',
                                 'LP residuals do not establish rational optimality'])
    check(severe, 'pre-frozen severe ENS certification regression established')
    save('independent_control_outcomes.json', dict(arms=arms, decision=decision))
    return decision


def main(label):
    global DEST, START
    from round100_idle import ensure_idle
    ensure_idle()
    DEST = OUT / 'diagnostics' / label
    DEST.mkdir(parents=True, exist_ok=False)
    START = time.perf_counter()
    bind(__file__)
    log('review_begin', scope='independent exact aggregation/RHS and saved full-vector checks; zero Optimize/DP')
    try:
        from round100_gurobi_runtime import gp, binding
        from round70_affinity import inherited_core
        freeze = read(OUT/'production_freeze.json')
        identity = read(OUT/'control01/identity.json')
        for path, expected in identity['source_hashes'].items():
            check(sha(bind(ROOT/path)) == expected, 'frozen actual production source '+path)
        check(freeze['source_bindings'] == identity['source_hashes'], 'measured source vs consolidated freeze')
        check(sha(bind(ROOT/freeze['binary'])) == freeze['PE_sha256'] == identity['candidate_binary_sha256'], 'measured production PE')
        directory = OUT/'control01/raw/01_F2_OC-ACTIVE/external/native_logs'
        prefix = directory/'L0_c6_1_child_disjunction_target_mip.gurobi.log.round104'
        contract = read(str(prefix)+'.contract.json')
        summary = read(str(prefix)+'.summary.json')
        check(contract['source_sha256'] == summary['source_sha256'] == EXPECTED_SOURCE, 'actual F2 original source identity')
        check(sha(bind(contract['source_path'])) == EXPECTED_SOURCE, 'original LP bytes')
        check(sha(bind(summary['canonical_path'])) == summary['canonical_sha256'], 'actual submitted LP bytes')
        pool = read(str(prefix)+'.pool.rows.json')['rows']
        selected = read(str(prefix)+'.rows.json')['rows']
        pool_solution = read(str(prefix)+'.pool.solution.json')
        compressed_solution = read(str(prefix)+'.compressed.solution.json')
        with inherited_core() as affinity, gp.Env(empty=True) as engine:
            engine.setParam('OutputFlag', 0)
            engine.start()
            runtime = binding()
            check(gp.gurobi.version() == (13, 0, 2), 'actual Gurobi runtime version')
            check(runtime['sha256'] == freeze['DLL_sha256'], 'actual numerical-reader DLL matches measured production freeze')
            with read_model(gp, engine, contract['source_path']) as old:
                matrix = phase('actual_original_matrix', lambda: extract(old))
                aggregate_results = phase('independent_actual_CPP_aggregates', lambda: aggregates(matrix))
                phase('historical_Python_GROUPED_native_tiny_scope', lambda: python_grouped_scope(matrix))
                phase('fresh_pool_rows_and_ahead_of_call_accounting', lambda: production_rows_and_calls(prefix, pool, selected, summary))
                pool_result = phase('fresh_pool_full_X_Pi_RC', lambda: full_solution(matrix, pool, pool_solution, 'pool'))
                compressed_result = phase('ACTIVE_full_X_Pi_RC', lambda: full_solution(matrix, selected, compressed_solution, 'compressed'))
                reconstructed_difference = Fraction(compressed_result['exact_objective']['exact'])-Fraction(pool_result['exact_objective']['exact'])
                check(abs(reconstructed_difference) <= exact(1e-7), 'independent full-X compressed/pool objective preservation qualification')
                with read_model(gp, engine, summary['canonical_path']) as submitted:
                    actual = extract(submitted)
                    phase('actual_typed_readback_and_full_Start', lambda: start_and_readback(matrix, actual, selected, prefix))
            decision = phase('complete_control_outcome_scope', outcomes)
        check(COUNTERS['Optimize_calls'] == COUNTERS['DP_calls'] == 0, 'independent reader performed no solve or DP')
        result = dict(passed=True, counters=COUNTERS, source_hashes=HASHES,
                      warnings=WARNINGS, runtime=runtime, affinity=affinity,
                      seconds=time.perf_counter()-START, decision=decision,
                      independent_aggregate_rows=len(aggregate_results),
                      signed_compressed_minus_pool=number(exact(compressed_solution['objective'])-exact(pool_solution['objective'])),
                      signed_reconstructed_compressed_minus_pool=number(reconstructed_difference),
                      numeric_scope='independent exact binary-rational aggregation/RHS bounds, original/new full LP vectors/Pi/RC and Start; no rational optimality',
                      unreviewed='no independent full support maximum recurrence, native B&B, statistics, hidden cuts or every historical row repricing')
        save('summary.json', result)
        log('review_return', passed=True)
        print(json.dumps(dict(passed=True, checks=COUNTERS['checks'], model_reads=COUNTERS['model_reads_returned'],
                              aggregate_rows=COUNTERS['aggregate_rows'], Optimize_calls=0, DP_calls=0,
                              decision=decision['recommendation'])), flush=True)
    except BaseException as error:
        save('summary.json', dict(passed=False, error=repr(error), counters=COUNTERS,
             source_hashes=HASHES, warnings=WARNINGS, seconds=time.perf_counter()-START))
        log('review_return', passed=False, error=repr(error))
        raise


if __name__ == '__main__':
    main(sys.argv[1])
