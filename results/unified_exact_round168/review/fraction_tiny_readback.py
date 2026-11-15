"""Independent offline readback of frozen tiny spaces; never calls Optimize.

The primary research oracle/model/driver is C++. This reviewer-only script
recomputes its saved small discrete spaces using Fraction arithmetic and
plain permutations; it is not used to construct or solve a research model.
"""
from pathlib import Path
from fractions import Fraction
import hashlib
import itertools
import json

HERE = Path(__file__).resolve().parent
OUT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fleet(path):
    tokens = iter(path.read_text().split())
    routes = []
    for _ in range(int(next(tokens))):
        vehicle = int(next(tokens))
        length = int(next(tokens))
        nodes = [int(next(tokens)) for _ in range(length)]
        quantities = [int(next(tokens)) for _ in range(length - 2)]
        routes.append((vehicle, nodes[1:-1], quantities))
    return routes


def check_case(case, scope):
    n, vehicles = case['V'], case['M']
    initial, capacities = case['b'], case['C']
    targets, vehicle_capacity = case['target'], case['Q']
    weights = [Fraction.from_float(v) for v in case['weights']]
    lam = Fraction.from_float(case['lambda'])
    parent_path = OUT / 'tiny_frozen' / f"{case['id']}_parent.fleet"
    parent = load_fleet(parent_path)
    sequences = {k: seq for k, seq, _ in parent}
    owners = {i: k for k, seq, _ in parent for i in seq}
    candidates = feasible = 0
    best = None

    domains = [range(capacities[i] + 1) if i in owners else [initial[i]]
               for i in range(1, n + 1)]
    for stock in itertools.product(*domains):
        final = [0] + list(stock)
        active = [i for i in range(1, n + 1) if final[i] != initial[i]]
        allowed_owners = [range(vehicles) if scope == 'eligible' else [owners[i]]
                          for i in active]
        for allocation in itertools.product(*allowed_owners):
            assignment = [[] for _ in range(vehicles)]
            for station, vehicle in zip(active, allocation):
                assignment[vehicle].append(station)
            choices = []
            for k in range(vehicles):
                if scope == 'order':
                    choices.append([tuple(i for i in sequences[k]
                                          if i in assignment[k])])
                else:
                    choices.append(list(itertools.permutations(assignment[k])))
            for routes in itertools.product(*choices):
                candidates += 1
                legal = True
                for vehicle, sequence in enumerate(routes):
                    load = pickup = drop = travel = last = 0
                    for station in sequence:
                        travel += abs(last - station)
                        last = station
                        quantity = initial[station] - final[station]
                        load += quantity
                        pickup += max(quantity, 0)
                        drop += max(-quantity, 0)
                        if not 0 <= load <= vehicle_capacity[vehicle]:
                            legal = False
                            break
                    if not legal:
                        break
                    travel += abs(last)
                    # Direct station handling plus unloading of loaded return.
                    duration = travel + pickup + drop + load
                    if duration > case['T']:
                        legal = False
                        break
                if not legal:
                    continue
                feasible += 1
                ratios = [Fraction(final[i], targets[i]) for i in range(1, n + 1)]
                total = sum(ratios)
                dispersion = sum(abs(ratios[i] - ratios[j])
                                 for i in range(n) for j in range(i + 1, n))
                gini = dispersion / (n * total) if total else Fraction(0)
                penalty = sum(weights[i] * abs(ratios[i - 1] - 1)
                              for i in range(1, n + 1))
                objective = gini + lam * penalty
                if best is None or objective < best:
                    best = objective

    frozen = next(row for row in case['families'] if row['scope'] == scope)
    native_path = OUT / 'tiny_qualification' / f"{case['id']}_{scope}" / 'result.json'
    native = json.loads(native_path.read_text())
    assert candidates == frozen['candidates'] and feasible == frozen['feasible']
    assert abs(float(best) - frozen['optimum']) <= 1e-15
    assert abs(float(best) - native['true_U']) <= 1e-15
    assert native['status'] == 2 and native['bound_qualified']
    return dict(case=case['id'], scope=scope, candidates=candidates, feasible=feasible,
                optimum_fraction=str(best), optimum_float=float(best),
                primary_Cpp_enumeration_optimum=frozen['optimum'],
                native_physical_U=native['true_U'], PASS=True,
                parent_SHA256=sha(parent_path), native_result_SHA256=sha(native_path))


if __name__ == '__main__':
    source = OUT / 'tiny_frozen' / 'enumeration.json'
    data = json.loads(source.read_text())
    records = [check_case(case, scope) for case in data['cases']
               for scope in ['order', 'owner', 'eligible']]
    result = dict(schema='round168-independent-fraction-tiny-readback-v1',
                  reviewer_kind='independent agent, not human peer review',
                  new_Optimize=0,
                  purpose='offline recomputation only; C++ remains primary research implementation',
                  arithmetic='exact Fraction of frozen binary64 objective coefficients; integer distances/handling',
                  enumeration_SHA256=sha(source), reviewer_script_SHA256=sha(Path(__file__)),
                  records=records, PASS=True,
                  limitation='Does not turn substantive Native bounds into rational certificates')
    (HERE / 'fraction_tiny_readback.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Independent offline Fraction readback PASS for all six frozen tiny spaces.')
