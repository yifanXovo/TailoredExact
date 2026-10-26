"""Read-only exact replay of the fixed R132 tiny carrier; no solver imports.

The bytes of the loaded binary64 matrices are interpreted as the stored exact
rationals.  This proves feasibility of these finite LP points, not MIP tree
correctness or a new separator.  Run after native production has exited.
"""
from pathlib import Path
from fractions import Fraction as F
import argparse, datetime, hashlib, io, itertools, json, re, subprocess, time, zipfile

PIN = '52b02252ba47e8228b73e071d6ed692385a4f816'
CARRIER = 'results/unified_exact_round132/artifacts/complete_tiny_joint_study.zip'
CARRIER_SHA = 'd2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1'
PREFIX = 'results/unified_exact_round132/joint/'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def physical(y, coefficient):
    total = sum(y)
    a = sum(abs(y[i] - y[j]) for i in range(4) for j in range(i + 1, 4))
    g = F(a, 4 * total) if total else F(0)
    p = sum(abs(v - 1) for v in y)
    return dict(Y=y, tau=total, G=str(g), P=p, F=str(g + coefficient * p))

def row_check(matrix, values):
    assert not (set(values) - set(matrix['bounds'])), 'unmapped saved columns'
    failures = []
    equality_nonzero = 0
    max_equality_residual = F(0)
    max_inequality_violation = F(0)
    for index, row in enumerate(matrix['rows']):
        lhs = sum(F(a) * values.get(n, F(0)) for n, a in row['coefficients'].items())
        rhs = F(row['RHS'])
        residual = lhs - rhs
        sense = row['sense']
        assert sense in ('=', '<', '>')
        if sense == '=':
            max_equality_residual = max(max_equality_residual, abs(residual))
            equality_nonzero += int(bool(residual))
            violation = abs(residual)
        else:
            violation = max(F(0), residual if sense == '<' else -residual)
            max_inequality_violation = max(max_inequality_violation, violation)
        if violation:
            failures.append(dict(kind='row', index=index, name=row['name'],
                                 sense=sense, lhs=str(lhs), RHS=str(rhs), violation=str(violation)))
    for name, (lo, hi) in matrix['bounds'].items():
        value = values.get(name, F(0))
        if not F(lo) <= value <= F(hi):
            failures.append(dict(kind='bound', column=name, value=str(value), lower=lo, upper=hi))
    return dict(status='EXACT_FEASIBLE' if not failures else 'NOT_EXACT_FEASIBLE',
                rows=len(matrix['rows']), bounds=len(matrix['bounds']),
                equality_nonzero=equality_nonzero,
                max_equality_residual=str(max_equality_residual),
                max_inequality_violation=str(max_inequality_violation), failures=failures)

def loaded_lower_bound_rows(matrix):
    """Verify the exact retained rows used by sum e >= 4-sum Y >= 1."""
    signatures = {(r['sense'], F(r['RHS']), tuple(sorted((n,F(a)) for n,a in r['coefficients'].items()))):
                  r['name'] for r in matrix['rows']}
    def identify(sense, rhs, terms):
        return signatures[(sense,F(rhs),tuple(sorted((n,F(a)) for n,a in terms.items())))]
    used = [identify('<',3,{f'Y_{i}':1 for i in range(1,5)})]
    for i in range(1,5):
        used.append(identify('=',0,{f'r_{i}':1,f'Y_{i}':-1}))
        used.append(identify('>',1,{f'e_{i}':1,f'r_{i}':1}))
    assert F(matrix['bounds']['G'][0]) >= 0
    return dict(rows=used, G_lower=matrix['bounds']['G'][0],
                sum_Y_upper='3', sum_e_lower='1', coefficients_checked_exactly=True)

def regenerate(case, k):
    q = case['Q'][k]
    options = [[(0, 0, 0)] + [(p, 0, 1) for p in range(1, min(b, q) + 1)]
               + [(0, d, 1) for d in range(1, min(2-b, q) + 1)] for b in case['b']]
    result = {}
    for service in itertools.product(*options):
        pickup = sum(p for p, d, z in service)
        drop = sum(d for p, d, z in service)
        if not 0 <= pickup - drop <= q or 120 * pickup > case['T']:
            continue
        active = [i for i, t in enumerate(service) if t[2]]
        for route in itertools.permutations(active):
            load = 0
            for i in route:
                load += service[i][0] - service[i][1]
                if not 0 <= load <= q:
                    break
            else:
                result[service] = tuple(route)
                break
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--carrier', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    blob = (args.carrier.read_bytes() if args.carrier else
            subprocess.check_output(['git', 'show', f'{PIN}:{CARRIER}']))
    assert sha(blob) == CARRIER_SHA, 'fixed public carrier SHA256 mismatch'
    archive = zipfile.ZipFile(io.BytesIO(blob))
    dependencies = []
    def read(case, name):
        path = PREFIX + case + '/' + name
        raw = archive.read(path)
        dependencies.append(dict(member=path, SHA256=sha(raw), bytes=len(raw)))
        return json.loads(raw)
    receipt = dict(schema='round133-exact-joint-replay-v1', UTC=utc, pin=PIN,
                   carrier_path=CARRIER, carrier_SHA256=sha(blob), carrier_bytes=len(blob),
                   source_SHA256=sha(Path(__file__).read_bytes()), Optimize=0,
                   solver_modules_loaded=False, cases={})
    for case_id in ('J2', 'J3'):
        saved = read(case_id, 'enumeration.json')
        case = saved['case']
        cars = saved['cars']
        reproduced = [regenerate(case, k) for k in range(2)]
        for k in range(2):
            recorded = {tuple(tuple(s) for s in plan['v']) for plan in cars[k]}
            assert recorded == set(reproduced[k]), (case_id, k, 'complete single-car service universe')
            for plan in cars[k]:
                load = 0
                assert set(plan['route']) == {i for i, t in enumerate(plan['v']) if t[2]}
                assert len(plan['route']) == len(set(plan['route']))
                for i in plan['route']:
                    load += plan['v'][i][0] - plan['v'][i][1]
                    assert 0 <= load <= case['Q'][k]
                assert load == plan['return_load']
                assert 120 * plan['pickup'] <= case['T']
        expected_pairs = [(a, b) for a, pa in enumerate(cars[0]) for b, pb in enumerate(cars[1])
                          if all(pa['v'][i][2] + pb['v'][i][2] <= 1 for i in range(4))]
        assert expected_pairs == [tuple(p) for p in saved['joint_pair_indices']]
        conflict_values = [cars[0][a]['v'][2][1] + cars[1][b]['v'][1][1] for a, b in expected_pairs]
        assert max(conflict_values) == 1
        matrix = read(case_id, 'B_joint_exact_matrix.json')
        original = read(case_id, 'original_objective_joint.json')
        values = {n: F(a) for n, a in original['values'].items()}
        check = row_check(matrix, values)
        lower_rows = loaded_lower_bound_rows(matrix)
        coefficient = F(original['objective_coefficients']['e_1'])
        assert coefficient == F(5404319552844595, 36028797018963968)
        assert {n:F(a) for n,a in original['objective_coefficients'].items()} == {
            'G':F(1), **{f'e_{i}':coefficient for i in range(1,5)}}
        assert F(original['objective_constant']) == 0
        obj = F(original['objective_constant']) + sum(F(a) * values.get(n, F(0))
                            for n, a in original['objective_coefficients'].items())
        assert all(values['Y_' + str(i)] == F(3, 4) and values['e_' + str(i)] == F(1, 4)
                   for i in range(1, 5))
        assert values.get('G', F(0)) == 0 and obj == coefficient
        joint_columns = []
        weighted_y = [F(0)] * 4
        mass = F(0)
        for n, weight in values.items():
            match = re.fullmatch(r'joint_mix\[(\d+)\]', n)
            if not match or not weight:
                continue
            pair_index = int(match.group(1))
            a, b = expected_pairs[pair_index]
            y = [case['b'][i] + sum(cars[k][j]['v'][i][1] - cars[k][j]['v'][i][0]
                                    for k, j in enumerate((a, b))) for i in range(4)]
            fact = physical(y, coefficient)
            fact.update(pair_index=pair_index, vehicle_plan_indices=[a, b], weight=str(weight),
                        routes_zero_based=[cars[0][a]['route'], cars[1][b]['route']],
                        service=[cars[0][a]['v'], cars[1][b]['v']])
            joint_columns.append(fact)
            for i in range(4):
                weighted_y[i] += weight * y[i]
            mass += weight
        assert mass == 1 and weighted_y == [F(3, 4)] * 4
        all_fleets = [physical([case['b'][i] + cars[0][a]['v'][i][1] - cars[0][a]['v'][i][0]
                              + cars[1][b]['v'][i][1] - cars[1][b]['v'][i][0]
                              for i in range(4)], coefficient) for a, b in expected_pairs]
        min_ip = min(F(v['F']) for v in all_fleets)
        assert min_ip == F(1, 4) + coefficient
        result = dict(case=case, single_car_counts=list(map(len, cars)), joint_fleets=len(expected_pairs),
                      complete_enumeration_matches=True,
                      simple_conflict=dict(form='d_0,3 + d_1,2 <= 1; zero-based cars, one-based stations',
                                           exact_integer_max=max(conflict_values)),
                      saved_joint_primal_check=check,
                      exact_loaded_lower_bound_derivation=lower_rows,
                      objective_coefficient=str(coefficient), exact_primal_objective=str(obj),
                      analytic_LP_lower_bound=str(coefficient), exact_IP_optimum=str(min_ip),
                      exact_gap=str(min_ip-obj), loaded_primal_nonzero_values={n:str(a) for n,a in values.items()},
                      joint_mixture=joint_columns,
                      proof_status='EXACT_LP_AND_IP' if check['status']=='EXACT_FEASIBLE' else 'EXACT_IP_ONLY_LP_NUMERIC')
        if case_id == 'J2':
            separation = read(case_id, 'best_separation.json')['best_strict']
            ref = read(case_id, 'B_ref_exact_matrix.json')
            witness = {n:F(a) for n,a in separation['proof']['values'].items()}
            full_check = row_check(ref, witness)
            assert full_check['status'] == 'EXACT_FEASIBLE'
            lhs = witness['d_0_3'] + witness['d_1_2']
            assert lhs == F(3, 2)
            names = [f'{p}_{k}_{i}' for k in range(2) for i in range(1,5) for p in ('p','d','z')]
            old_lhs = sum(F(a) * witness.get(n,F(0)) for a,n in zip(separation['w'],names))
            # Independent full joint maximum of the original 24-dimensional direction.
            old_max = max(sum(F(w) * value for w,value in zip(separation['w'],
                          [t for k,p in enumerate((a,b)) for triple in cars[k][p]['v'] for t in triple]))
                          for a,b in expected_pairs)
            assert old_lhs == F(15,2) and old_max == 7
            strict_y=[F(case['b'][i])+sum(witness.get(f'd_{k}_{i+1}',F(0))-
                         witness.get(f'p_{k}_{i+1}',F(0)) for k in range(2)) for i in range(4)]
            assert strict_y == [1,1,1,0]
            result['strict_reference'] = dict(check=full_check, simple_lhs=str(lhs),
                         original_direction_lhs=str(old_lhs), original_direction_max=str(old_max),
                         inventory=[str(a) for a in strict_y],
                         per_car_mixture={n:str(a) for n,a in witness.items() if n.startswith('mix')})
        receipt['cases'][case_id]=result
    receipt['dependencies']=dependencies
    receipt['seconds']=time.perf_counter()-started
    receipt['budget_category']='E; this outer process only; limit1800s'
    receipt['status']='PASS' if all(v['proof_status']=='EXACT_LP_AND_IP' for v in receipt['cases'].values()) else 'PARTIAL'
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=receipt['status'],seconds=receipt['seconds'],
        cases={k:dict(primal=v['saved_joint_primal_check']['status'],rows=v['saved_joint_primal_check']['rows'],
                       bounds=v['saved_joint_primal_check']['bounds'],gap=v['exact_gap'])
               for k,v in receipt['cases'].items()})))

if __name__ == '__main__':
    main()
