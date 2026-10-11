"""Finite saved-G50 counterexample replay; imported by the budgeted driver.

No entry point, subprocess, solver API, DLL, environment, or Optimize is used.
The two matrices and the ENS fleet are management-review sources from R113;
neither vector is a new solver solution or the cold arm's own incumbent.
"""

from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
import time
import traceback


ROUND = Path("results/unified_exact_round114")
SOURCE = ROUND / "management_counterexample/source"
COLD = Path("campaign/raw/04_G50-C1_S0_P-GRB")
ENS = Path("campaign/raw/02_G50-C1_S0_ENS-C")
START = Path("campaign/raw/03_G50-C1_S0_P-S")
INPUT = Path("reference/round109_geographic/G50-C1.txt")
EXPECTED_SHA = {
    COLD / "compact.lp": "3c4385055008239f0b26af749792e95eeb7ef22403ef58035a51b5e75eb16b8c",
    ENS / "result.json": "10442b3cbca6fc1484f06e6bf1ec0aa17e65cb15638ba5cba06d0185305ad751",
    START / "native.log.round112.start.before.matrix.json": "29bbffdd02ba923fe5e47dac1b5cef21b0d05ddb1961a74401584ef3285be4c2",
}
INPUT_SHA = "5740d09bf218cf6921cee6e60198f673151d6426fbcb0840259647129f3c4ed5"
EXPECTED_OBJECTIVES = {
    "printed_decimal": 2.9256256379999997e-16,
    "api_binary64": 1.979712144217771e-16,
}
NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
RELATION = re.compile(r"\s(<=|>=|=)\s(\S+)\s*\Z")
ZERO = Fraction(0)
ONE = Fraction(1)


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)
        stream.write("\n")


def _q(value):
    return [value.numerator, value.denominator]


def _lp(path):
    """Independent exact parser for the saved C++ one-line linear grammar.

    Fraction(token) interprets the literal printed decimal, without an
    intermediate binary64 conversion. Unknown grammar is a hard failure.
    """
    seen = set()
    order = []
    bounds = {}
    types = {}
    rows = []
    objective = None
    section = None
    row_names = set()

    def register(name):
        assert NAME.fullmatch(name), ("unsupported column name", name)
        if name not in seen:
            seen.add(name)
            order.append(name)

    def expression(body):
        tokens = body.split()
        assert tokens, "empty linear expression"
        terms = {}
        constant = ZERO
        i = 0
        while i < len(tokens):
            sign = ONE
            if tokens[i] in ("+", "-"):
                sign = ONE if tokens[i] == "+" else -ONE
                i += 1
                assert i < len(tokens), "trailing LP sign"
            token = tokens[i]
            i += 1
            if NAME.fullmatch(token):
                register(token)
                terms[token] = terms.get(token, ZERO) + sign
            else:
                assert NUMBER.fullmatch(token), ("unsupported numeric token", token)
                coefficient = sign * Fraction(token)
                if i < len(tokens) and NAME.fullmatch(tokens[i]):
                    name = tokens[i]
                    i += 1
                    register(name)
                    terms[name] = terms.get(name, ZERO) + coefficient
                else:
                    constant += coefficient
        return {name: coefficient for name, coefficient in terms.items() if coefficient}, constant

    with Path(path).open(encoding="utf-8") as stream:
        for line_number, raw in enumerate(stream, 1):
            line = raw.strip()
            if not line or line.startswith("\\"):
                continue
            if line in ("Minimize", "Subject To", "Bounds", "Generals", "Binaries", "End"):
                section = line
                continue
            if section == "Minimize":
                assert objective is None and line.startswith("obj:"), ("objective grammar", line_number)
                objective = expression(line.split(":", 1)[1])
            elif section == "Subject To":
                name, body = line.split(":", 1)
                assert NAME.fullmatch(name) and name not in row_names, ("row name", line_number)
                row_names.add(name)
                relation = RELATION.search(body)
                assert relation and NUMBER.fullmatch(relation[2]), ("row grammar", line_number)
                terms, constant = expression(body[:relation.start()])
                rows.append((name, terms, relation[1], Fraction(relation[2]) - constant))
            elif section == "Bounds":
                tokens = line.split()
                assert len(tokens) == 5 and tokens[1] == tokens[3] == "<=", ("bound grammar", line_number)
                low, name, high = tokens[0], tokens[2], tokens[4]
                assert NUMBER.fullmatch(low) and NUMBER.fullmatch(high), ("finite bound grammar", line_number)
                register(name)
                assert name not in bounds
                bounds[name] = (Fraction(low), Fraction(high))
                assert bounds[name][0] <= bounds[name][1]
            elif section in ("Generals", "Binaries"):
                for name in line.split():
                    register(name)
                    assert name not in types
                    types[name] = "I" if section == "Generals" else "B"
            else:
                raise AssertionError(("unsupported LP section", section, line_number))
    assert section == "End" and objective is not None and seen == set(bounds)
    assert len(order) == 13326 and len(rows) == 35567
    return dict(order=order, bounds=bounds, types={name: types.get(name, "C") for name in order},
                rows=rows, objective=objective, sense=1)


def _binary64(value):
    assert isinstance(value, (int, float)) and not isinstance(value, bool)
    assert math.isfinite(value)
    return Fraction.from_float(float(value))


def _api(path):
    """Exact rational interpretation of the actually saved API binary64 data."""
    data = _read(path)
    assert set(data) == {"sense", "constant", "columns", "rows"}
    assert data["sense"] == 1 and len(data["columns"]) == 13326 and len(data["rows"]) == 35567
    order = []
    bounds = {}
    types = {}
    objective = {}
    for column in data["columns"]:
        assert len(column) == 5
        name, kind, low, high, coefficient = column
        assert NAME.fullmatch(name) and name not in bounds and kind in ("C", "I", "B")
        order.append(name)
        bounds[name] = (_binary64(low), _binary64(high))
        assert bounds[name][0] <= bounds[name][1]
        types[name] = kind
        coefficient = _binary64(coefficient)
        if coefficient:
            objective[name] = coefficient
    rows = []
    seen = set()
    for row in data["rows"]:
        assert len(row) == 4
        name, sense, rhs, indexed = row
        assert NAME.fullmatch(name) and name not in seen and sense in ("<", ">", "=")
        seen.add(name)
        terms = {}
        for index, coefficient in indexed:
            assert type(index) is int and 0 <= index < len(order)
            column = order[index]
            terms[column] = terms.get(column, ZERO) + _binary64(coefficient)
        rows.append((name, {name: value for name, value in terms.items() if value},
                     {"<": "<=", ">": ">=", "=": "="}[sense], _binary64(rhs)))
    return dict(order=order, bounds=bounds, types=types, rows=rows,
                objective=(objective, _binary64(data["constant"])), sense=data["sense"])


def _matrix_equivalence(decimal, binary):
    """Compare every source element after the specified decimal-to-binary64 conversion."""
    assert set(decimal["order"]) == set(binary["order"])
    assert decimal["sense"] == binary["sense"] and decimal["types"] == binary["types"]
    for name in decimal["order"]:
        assert tuple(_binary64(float(value)) for value in decimal["bounds"][name]) == binary["bounds"][name], ("matrix bound", name)
    left, left_constant = decimal["objective"]
    right, right_constant = binary["objective"]
    assert {name: _binary64(float(value)) for name, value in left.items()} == right
    assert _binary64(float(left_constant)) == right_constant
    nonzeros = 0
    for lrow, rrow in zip(decimal["rows"], binary["rows"]):
        lname, lterms, lsense, lrhs = lrow
        rname, rterms, rsense, rrhs = rrow
        assert (lname, lsense) == (rname, rsense), ("matrix row identity", lname, rname)
        assert _binary64(float(lrhs)) == rrhs, ("matrix rhs", lname)
        assert {name: _binary64(float(value)) for name, value in lterms.items()} == rterms, ("matrix coefficients", lname)
        nonzeros += len(lterms)
    return dict(passed=True, columns=13326, rows=35567, row_nonzeros=nonzeros,
                all_names_types_bounds_objective_rhs_senses_coefficients_checked=True,
                binary64_snapshot_is_P_S_not_unsaved_cold_API=True)


def _physical(root, source):
    # Invoke only the existing complete physical-fleet pure function, never a
    # historical reader entry point, model runtime, or native proof gate.
    import round108_reader as core
    assert Path(core.__file__).resolve() == (root / "scripts/round108_reader.py").resolve()
    assert Path(core.evidence.__file__).resolve() == (root / "scripts/round107_reader.py").resolve()
    panel = dict(input_path=INPUT.as_posix(), input_sha256=INPUT_SHA, V=50, M=4,
                 Q_vector=[30, 30, 30, 30], T_seconds=7200, pickup_seconds=60,
                 drop_seconds=60, **{"lambda": 0.15})
    original = _read(source / ENS / "result.json")
    physical = core.full_fleet(root, panel, original)
    assert physical["F"] == physical["G"] == physical["P"] == 0.0
    text = (root / INPUT).read_text(encoding="utf-8")

    def vector(name):
        match = re.search(r"^\s*" + name + r"\s*=\s*(\[[^\n]*\])", text, re.M)
        assert match
        return ast.literal_eval(match[1])

    initial = vector("initial")
    target = vector("target")
    capacity = vector("capacities")
    weights = [Fraction(str(value)) for value in vector("weights")]
    assert all(type(value) is int for value in initial + target + capacity)
    assert len(initial) == len(target) == len(capacity) == len(weights) == 51
    assert physical["Y"][1:] == target[1:]
    assert all(value > 0 for value in target[1:]) and all(value > 0 for value in weights[1:])
    Y = initial.copy()
    seen = set()
    vehicles = set()
    prefixes = []
    for route in physical["routes"]:
        k = route["vehicle"]
        assert type(k) is int and 0 <= k < 4 and k not in vehicles
        vehicles.add(k)
        nodes = route["nodes"]
        assert nodes[0] == nodes[-1] == 0 and all(type(node) is int for node in nodes)
        operations = {operation["station"]: operation for operation in route["operations"]}
        assert len(operations) == len(route["operations"]) == len(nodes) - 2
        assert set(nodes[1:-1]) == set(operations)
        load = 0
        row = []
        for node in nodes[1:-1]:
            assert 1 <= node <= 50 and node not in seen
            seen.add(node)
            op = operations[node]
            pickup, drop = op["pickup"], op["drop"]
            assert type(pickup) is type(drop) is int and pickup >= 0 and drop >= 0 and bool(pickup) != bool(drop)
            load += pickup - drop
            assert 0 <= load <= 30
            Y[node] += drop - pickup
            assert 0 <= Y[node] <= capacity[node]
            row.append(dict(station=node, pickup=pickup, drop=drop, prefix_load=load))
        prefixes.append(dict(vehicle=k, empty_departure_load=0, stops=row, return_load=load))
    assert vehicles == set(range(4)) and Y[1:] == target[1:]
    assert sum(Y[1:]) == sum(initial[1:]) - sum(row["return_load"] for row in prefixes)
    delta = Fraction("0.15") * min(weights[i] / target[i] for i in range(1, 51))
    assert delta == Fraction("0.006")
    return physical, target, dict(passed=True, existing_full_verifier=physical,
        independent_integer_prefix_and_inventory_check=prefixes, final_inventory=Y,
        true_physical_G=[0, 1], true_physical_F=[0, 1], positive_inventory_delta=_q(delta),
        delta_is_separation_from_zero_not_a_common_positive_objective_lattice=True,
        physical_floor_source="true G >= 0, positive targets, nonnegative lambda and weights",
        existing_physical_helper_bindings={path.relative_to(root).as_posix(): _sha(path) for path in
            [root / "scripts/round108_reader.py", root / "scripts/round107_reader.py"]})


def _construct(model, physical, target):
    values = {name: ZERO for name in model["order"]}
    expected_families = {"G", "e", "x", "z", "mode", "p", "d", "load", "ord", "Y", "r", "h", "bit", "prod", "zprod"}
    assert {name.split("_", 1)[0] for name in values} == expected_families
    for route in physical["routes"]:
        k = route["vehicle"]
        nodes = route["nodes"]
        ops = {op["station"]: op for op in route["operations"]}
        if nodes == [0, 0]:
            assert not ops
            continue
        for i, j in zip(nodes, nodes[1:]):
            name = f"x_{k}_{i}_{j}"
            assert name in values
            values[name] = ONE
        load = 0
        for position, i in enumerate(nodes[1:-1], 1):
            op = ops[i]
            load += op["pickup"] - op["drop"]
            for name, value in {f"p_{k}_{i}": op["pickup"], f"d_{k}_{i}": op["drop"],
                                f"z_{k}_{i}": 1, f"mode_{k}_{i}": int(op["pickup"] > 0),
                                f"load_{k}_{i}": load, f"ord_{k}_{i}": position}.items():
                assert name in values
                values[name] = Fraction(value)
    ratio_rows = {}
    for row_name, terms, sense, rhs in model["rows"]:
        if sense == "=" and rhs == 0 and len(terms) == 2:
            for name in terms:
                if re.fullmatch(r"r_\d+", name):
                    i = int(name.split("_")[1])
                    if set(terms) == {name, f"Y_{i}"}:
                        assert i not in ratio_rows and terms[name] == 1 and terms[f"Y_{i}"] < 0
                        ratio_rows[i] = (row_name, -terms[f"Y_{i}"])
    assert set(ratio_rows) == set(range(1, 51))
    for i in range(1, 51):
        values[f"Y_{i}"] = Fraction(target[i])
        values[f"r_{i}"] = ratio_rows[i][1] * target[i]
        values[f"e_{i}"] = abs(values[f"r_{i}"] - ONE)
    h_names = {f"h_{i}_{j}" for i in range(1, 51) for j in range(i + 1, 51)}
    zprod_names = {f"zprod_{i}" for i in range(1, 51)}
    for name in h_names:
        _, i, j = name.split("_")
        values[name] = abs(values[f"r_{i}"] - values[f"r_{j}"])
    gini_rows = [(name, terms) for name, terms, sense, rhs in model["rows"]
                 if sense == ">=" and rhs == 0 and set(terms) == h_names | zprod_names]
    assert len(gini_rows) == 1
    gini_name, coefficients = gini_rows[0]
    assert all(coefficients[name] == -1 for name in h_names)
    assert all(coefficients[name] > 0 for name in zprod_names)
    numerator = sum((values[name] for name in h_names), ZERO)
    denominator = sum((coefficients[f"zprod_{i}"] * target[i] for i in range(1, 51)), ZERO)
    assert denominator > 0
    G = numerator / denominator
    values["G"] = G
    for i in range(1, 51):
        values[f"zprod_{i}"] = G * target[i]
    for name in values:
        if re.fullmatch(r"(?:bit|prod)_\d+_\d+", name):
            family, i, bit = name.split("_")
            binary = Fraction((target[int(i)] >> int(bit)) & 1)
            values[name] = binary if family == "bit" else G * binary
    assert set(values) == set(model["bounds"])
    return values, dict(ratio_rows={str(i): dict(row=ratio_rows[i][0], a_i=_q(ratio_rows[i][1])) for i in range(1, 51)},
        gini_row=gini_name, b_i={str(i): _q(coefficients[f"zprod_{i}"]) for i in range(1, 51)},
        h_sum=_q(numerator), sum_b_i_D_i=_q(denominator), G=_q(G),
        formula="r_i=a_i D_i; e_i=abs(r_i-1); h_ij=abs(r_i-r_j); G=sum(h)/sum(b_i D_i); zprod_i=G D_i; prod_ib=G bit_ib")


def _dot(terms, values, constant=ZERO):
    return constant + sum((coefficient * values[name] for name, coefficient in terms.items() if values[name]), ZERO)


def _verify(model, values, output, label, construction):
    vector_path = output / f"{label}_complete_vector.json"
    objective = _dot(model["objective"][0], values, model["objective"][1])
    _write(vector_path, dict(matrix_interpretation=label, complete_column_values={name: _q(values[name]) for name in model["order"]},
                            exact_objective=_q(objective), exact_objective_float=float(objective), construction=construction,
                            submitted_to_native=False, is_cold_own_incumbent=False))
    bound_bad = []
    integer_bad = []
    with (output / f"{label}_columns.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["column", "type", "value_n", "value_d", "lower_n", "lower_d", "upper_n", "upper_d", "bound_valid", "integer_valid"])
        for name in model["order"]:
            value = values[name]
            low, high = model["bounds"][name]
            bounded = low <= value <= high
            integral = model["types"][name] == "C" or value.denominator == 1
            if not bounded:
                bound_bad.append(name)
            if not integral:
                integer_bad.append(name)
            writer.writerow([name, model["types"][name], *_q(value), *_q(low), *_q(high), int(bounded), int(integral)])
    row_bad = []
    with (output / f"{label}_rows.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["row", "name", "sense", "lhs_n", "lhs_d", "rhs_n", "rhs_d", "signed_residual_n", "signed_residual_d", "violation_n", "violation_d", "valid"])
        for number, (name, terms, sense, rhs) in enumerate(model["rows"], 1):
            lhs = _dot(terms, values)
            residual = lhs - rhs
            violation = abs(residual) if sense == "=" else max(ZERO, residual if sense == "<=" else -residual)
            if violation:
                row_bad.append(dict(row=number, name=name, exact_violation=_q(violation)))
            writer.writerow([number, name, sense, *_q(lhs), *_q(rhs), *_q(residual), *_q(violation), int(violation == 0)])
    report = dict(matrix_interpretation=label, columns=len(values), rows=len(model["rows"]),
                  column_type_counts=dict(Counter(model["types"].values())), exact_objective=_q(objective),
                  exact_objective_float=float(objective), expected_objective_float=EXPECTED_OBJECTIVES[label],
                  row_violations=row_bad, bound_violations=bound_bad, integer_violations=integer_bad,
                  row_violation_count=len(row_bad), bound_violation_count=len(bound_bad), integer_violation_count=len(integer_bad),
                  exact_zero_violations_without_tolerance=not (row_bad or bound_bad or integer_bad))
    _write(output / f"{label}_verification.json", report)
    assert not (row_bad or bound_bad or integer_bad), ("exact model violations", label, report)
    assert float(objective) == EXPECTED_OBJECTIVES[label], ("supplied management objective differs", label, float(objective))
    return report, objective


def _pair_add(left, right):
    """Second arithmetic implementation: normalized integer pairs only."""
    ln, ld = left
    rn, rd = right
    divisor = math.gcd(ld, rd)
    numerator = ln * (rd // divisor) + rn * (ld // divisor)
    denominator = ld * (rd // divisor)
    divisor = math.gcd(numerator, denominator)
    return (numerator // divisor, denominator // divisor)


def _pair_mul(left, right):
    ln, ld = left
    rn, rd = right
    first = math.gcd(ln, rd)
    second = math.gcd(rn, ld)
    return ((ln // first) * (rn // second), (ld // second) * (rd // first))


def _pair_dot(terms, values, constant=(0, 1)):
    total = constant
    for name, coefficient in terms.items():
        if values[name][0]:
            total = _pair_add(total, _pair_mul((coefficient.numerator, coefficient.denominator), values[name]))
    return total


def _compare(left, right):
    value = left[0] * right[1] - right[0] * left[1]
    return (value > 0) - (value < 0)


def _recheck_saved_arithmetic(model, output, label):
    """Re-read the full saved vector and every residual, then recompute.

    No Fraction arithmetic is used by this second dot-product/comparison
    implementation. Source parsing is shared; this is independent arithmetic
    verification, not an independent-person signature or a second model run.
    """
    saved = _read(output / f"{label}_complete_vector.json")
    values = {name: tuple(pair) for name, pair in saved["complete_column_values"].items()}
    assert set(values) == set(model["bounds"])
    for name, pair in values.items():
        assert len(pair) == 2 and all(type(value) is int for value in pair) and pair[1] > 0
        assert math.gcd(*pair) == 1, ("unreduced vector value", name)
    with (output / f"{label}_columns.csv").open(encoding="utf-8", newline="") as stream:
        records = csv.DictReader(stream)
        count = 0
        for name, row in zip(model["order"], records):
            count += 1
            assert row["column"] == name and row["type"] == model["types"][name]
            value = values[name]
            low, high = (tuple(_q(bound)) for bound in model["bounds"][name])
            assert value == (int(row["value_n"]), int(row["value_d"]))
            assert low == (int(row["lower_n"]), int(row["lower_d"]))
            assert high == (int(row["upper_n"]), int(row["upper_d"]))
            assert _compare(low, value) <= 0 and _compare(value, high) <= 0
            assert model["types"][name] == "C" or value[0] % value[1] == 0
            assert row["bound_valid"] == row["integer_valid"] == "1"
        assert count == 13326 and next(records, None) is None
    with (output / f"{label}_rows.csv").open(encoding="utf-8", newline="") as stream:
        records = csv.DictReader(stream)
        count = 0
        for number, ((name, terms, sense, rhs), row) in enumerate(zip(model["rows"], records), 1):
            count += 1
            assert (int(row["row"]), row["name"], row["sense"]) == (number, name, sense)
            lhs = _pair_dot(terms, values)
            right = tuple(_q(rhs))
            residual = _pair_add(lhs, (-right[0], right[1]))
            assert lhs == (int(row["lhs_n"]), int(row["lhs_d"]))
            assert right == (int(row["rhs_n"]), int(row["rhs_d"]))
            assert residual == (int(row["signed_residual_n"]), int(row["signed_residual_d"]))
            compare = _compare(lhs, right)
            assert compare == 0 if sense == "=" else compare <= 0 if sense == "<=" else compare >= 0
            assert row["violation_n"] == "0" and row["violation_d"] == "1" and row["valid"] == "1"
        assert count == 35567 and next(records, None) is None
    terms, constant = model["objective"]
    objective = _pair_dot(terms, values, tuple(_q(constant)))
    assert list(objective) == saved["exact_objective"]
    report = dict(passed=True, columns=13326, rows=35567, exact_objective=list(objective),
                  all_saved_column_checks_and_row_residuals_recomputed=True,
                  arithmetic="integer numerator/denominator pairs with gcd and cross multiplication",
                  Fraction_arithmetic_used=False, source_parser_shared=True,
                  independent_person_signature=False, Optimize=0, native_environment=0)
    _write(output / f"{label}_second_arithmetic_check.json", report)
    return report


def _cold_claim_bindings(source, model_sha, objectives):
    cold = source / COLD
    observations = _read(cold / "observations.json")
    assert len(observations) == 82
    assert {path.name for path in (cold / "journal").iterdir()} == {
        f"event_{sequence}.{suffix}" for sequence in range(1, 83) for suffix in ("json", "commit")}
    events = {}
    commit_times = {}
    for sequence, observation in enumerate(observations, 1):
        path = cold / "journal" / f"event_{sequence}.json"
        commit = (cold / "journal" / f"event_{sequence}.commit").read_text(encoding="utf-8").split()
        event = _read(path)
        assert len(commit) == 5 and commit[0] == "NEJ1" and int(commit[1]) == sequence
        assert int(commit[3]) == path.stat().st_size and commit[4] == _sha(path) == observation["sha256"]
        assert event == observation["payload"] and event["sequence"] == sequence
        assert float(commit[2]) == observation["data_close_seconds"]
        assert observation["effective_available_seconds"] >= observation["data_close_seconds"]
        events[sequence] = event
        commit_times[sequence] = commit[2]
    identity = events[1]
    assert identity["kind"] == "identity" and identity["input_sha256"] == INPUT_SHA
    assert (identity["V"], identity["M"], identity["T"], identity["pickup_seconds"], identity["drop_seconds"], identity["lambda"]) == (50, 4, 7200, 60, 60, 0.15)
    calls = [event for event in events.values() if event["kind"] == "call"]
    returns = [event for event in events.values() if event["kind"] == "returned"]
    assert len(calls) == len(returns) == 1 and calls[0]["sequence"] == 2 and returns[0]["sequence"] == 82
    call = calls[0]
    assert call["call"] == call["full_original"] == call["native_preconditions"] == 1
    assert call["model_sha256"] == model_sha and call["model_scope"] == "complete_original_compact_milp"
    assert call["lower_g"] == call["cutoff"] == 0 and call["upper_g"] == call["gmax"] == 0.98 and call["cover"] == []
    assert call["settings"] == dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1,
        MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
    assert str(call["model_path"]).replace("\\", "/").endswith("/" + (Path("results/unified_exact_round113") / COLD / "compact.lp").as_posix())
    assert str(call["native_log_path"]).replace("\\", "/").endswith("/" + (Path("results/unified_exact_round113") / COLD / "native.log").as_posix())
    assert returns[0]["call"] == 1 and returns[0]["return_code"] == 0
    positive = [event for event in events.values() if event["kind"] == "bound" and event["global_available"] and event["global_bound"] > 1e-7]
    assert positive and positive[0]["sequence"] == 52
    assert events[52]["native_bound"] == 7.578293621148189e-7
    assert events[53]["native_bound"] == 2.2806283239409983e-6
    for sequence in (52, 53):
        event = events[sequence]
        assert event["kind"] == "bound" and event["call"] == 1 and event["global_available"] == 1 and event["inconsistent"] == 0
        assert event["reason"] == "full_original_native_callback" and event["global_bound"] == event["native_bound"]
        assert all(_binary64(event["native_bound"]) - objective > Fraction(1, 10**7) for objective in objectives)
    result = _read(cold / "result.json")
    completion = _read(cold / "completion.json")
    assert completion["returncode"] == 0 and completion["stop_reason"] == "normal_return" and completion["within_cap"] is True
    assert completion["committed_events"] == 82
    assert result["gurobi_optimize_count"] == result["native_mip_mipopt_count"] == 1
    assert result["gurobi_optimize_return_code"] == result["native_mipopt_return_code"] == 0
    assert result["gurobi_status"] == 9 and result["gurobi_status_text"] == "TIME_LIMIT"
    assert result["native_mip_best_bound_available"] and result["gurobi_obj_bound_available"] and result["gurobi_obj_bound_c_available"]
    final = result["gurobi_obj_bound_c"]
    assert final == result["gurobi_obj_bound"] == result["native_mip_best_bound"] == result["lower_bound"] == events[53]["native_bound"]
    assert result["strict_lower_bound_source"] == "Gurobi_ObjBoundC"
    text = (cold / "native.log").read_text(encoding="utf-8")
    sizes = re.findall(r"Optimize a model with (\d+) rows, (\d+) columns", text)
    assert sizes == [("35567", "13326")] and "Time limit reached" in text
    printed = re.findall(r"Best objective ([^,]+), best bound ([^,]+), gap", text)
    assert len(printed) == 1
    printed_bound = Decimal(printed[0][1].strip())
    half_quantum = Fraction(Decimal(1).scaleb(printed_bound.as_tuple().exponent)) / 2
    printed_rational = Fraction(printed_bound)
    assert abs(_binary64(final) - printed_rational) <= half_quantum
    with (cold / "phases.csv").open(encoding="utf-8", newline="") as stream:
        phases = list(csv.DictReader(stream))
    phase_names = [row["event"] for row in phases]
    required = ["plain_gurobi_optimize_launch", "final_result_serialization_start", "final_result_serialization_complete", "process_exit"]
    assert all(phase_names.count(name) == 1 for name in required)
    assert [phase_names.index(name) for name in required] == sorted(phase_names.index(name) for name in required)
    assert phases[-1]["event"] == "process_exit" and phases[-1]["status"] == "complete" and phases[-1]["detail"] == "rc=0"
    return dict(passed=True, call=call, retained_event52=events[52], retained_event53=events[53], retained_returned82=events[82],
        event52_data_close_seconds_decimal=commit_times[52], event53_data_close_seconds_decimal=commit_times[53],
        returned82_data_close_seconds_decimal=commit_times[82], observations_at_bound_events=[observations[51], observations[52]],
        original_native_lower_bound=final, ObjBoundC_binary64_exact=_q(_binary64(final)),
        final_log_printed_objective=printed[0][0], final_log_printed_bound=printed[0][1],
        final_log_last_digit_interval_check=True, normal_return_completion=completion,
        rejected_all_native_proof_claims_from_this_call=True, dependent_native_closure_proofs_rejected=True,
        original_cold_whole_seconds=None, old_formal_endpoint_requalified=False,
        counterexample_does_not_become_cold_own_UB=True,
        physical_true_G=[0, 1], full_original_domain_membership=True,
        hidden_cold_in_memory_matrix_not_observed=True,
        identified_internal_failure_node=None, unique_native_internal_cause="unknown")


def run(root, output):
    """Run exactly one finite arithmetic/source replay in the enclosing driver.

    root is the worktree or restored root. Sources live strictly beneath
    results/unified_exact_round114/management_counterexample/source/campaign/raw.
    output is a new directory; existing output/raw is never overwritten.
    """
    root = Path(root).resolve()
    output = Path(output).resolve()
    assert output.is_relative_to(root) and not output.is_relative_to(root / SOURCE)
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    source = root / SOURCE
    try:
        assert _sha(root / INPUT) == INPUT_SHA
        for relative, expected in EXPECTED_SHA.items():
            assert _sha(source / relative) == expected, ("specified management source SHA differs", relative.as_posix())
        required = [source / relative for relative in EXPECTED_SHA]
        required += [source / COLD / name for name in ("result.json", "native.log", "completion.json", "observations.json", "phases.csv")]
        required += list((source / COLD / "journal").iterdir())
        required += [root / INPUT]
        assert all(path.is_file() and path.resolve().is_relative_to(root) for path in required)
        source_bindings = {path.relative_to(root).as_posix(): _sha(path) for path in sorted(required)}
        decimal = _lp(source / COLD / "compact.lp")
        binary = _api(source / START / "native.log.round112.start.before.matrix.json")
        equivalence = _matrix_equivalence(decimal, binary)
        _write(output / "matrix_equivalence.json", equivalence)
        physical, target, physical_report = _physical(root, source)
        _write(output / "physical_zero_fleet.json", physical_report)
        verifications = {}
        objectives = []
        second_checks = {}
        for label, model in (("printed_decimal", decimal), ("api_binary64", binary)):
            values, construction = _construct(model, physical, target)
            verification, objective = _verify(model, values, output, label, construction)
            verifications[label] = verification
            objectives.append(objective)
            second_checks[label] = _recheck_saved_arithmetic(model, output, label)
        claims = _cold_claim_bindings(source, EXPECTED_SHA[COLD / "compact.lp"], objectives)
        _write(output / "cold_claim_bindings.json", claims)
        # This floor proves an original physical property and is not a
        # numerical subtraction, clipping, or repair of the original L.
        for model in (decimal, binary):
            objective, constant = model["objective"]
            assert constant == 0 and all(coefficient >= 0 and model["bounds"][name][0] >= 0 for name, coefficient in objective.items())
        outputs = {path.relative_to(root).as_posix(): _sha(path) for path in sorted(output.iterdir()) if path.is_file()}
        receipt = dict(schema="round114-saved-G50-exact-counterexample-replay-v1", passed=True,
            source_kind="explicit R113 management review dependency; not original R113 report",
            source_bindings=source_bindings, script_path=Path(__file__).resolve().relative_to(root).as_posix(), script_SHA=_sha(__file__),
            matrix_equivalence=equivalence, verifications=verifications, second_arithmetic_checks=second_checks,
            outputs=outputs, cold_call=1, first_contradictory_bound_sequence=52, later_bound_sequence=53, returned_sequence=82,
            original_native_lower_bound=claims["original_native_lower_bound"],
            original_consistency_threshold=1e-7, exact_checks_have_no_feasibility_tolerance=True,
            independent_global_physical_floor=[0, 1], own_zero_fleet_source=(SOURCE / ENS / "result.json").as_posix(),
            old_cold_formal_endpoint_unchanged_and_unqualified=True, cold_API_snapshot_claimed=False,
            unique_native_internal_cause="unknown", Optimize=0, native_environment=0, subprocess_starts=0,
            enclosing_driver_counts_this_work_as_qualification=True,
            elapsed_inside_enclosing_driver_seconds=time.perf_counter() - started)
        _write(output / "replay.json", receipt)
        return receipt
    except Exception:
        _write(output / "failure.json", dict(passed=False, traceback=traceback.format_exc(),
            elapsed_inside_enclosing_driver_seconds=time.perf_counter() - started,
            no_solver_or_API_invoked=True, qualification_must_stop_before_formal=True))
        raise
