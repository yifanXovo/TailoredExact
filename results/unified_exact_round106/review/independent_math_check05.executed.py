"""Independent Round106 arithmetic/physical review; standard library only.

No project modules, solver imports, Optimize, IIS, subprocess, DP or route search.
Only Kruskal/Floyd arithmetic, fixed three-stop six-order checks and witness
decoding. Reads original inputs and SHA-bound R105 raw evidence, including the
compact tar when loose evidence is absent. Output must have a fresh identity.
"""
import argparse
import ast
import csv
from decimal import Decimal, localcontext
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[3]
R105 = "results/unified_exact_round105/"
C2 = R105 + "control01/raw/06_R98-C2_IR-CORE/external/round105/"
F2 = R105 + "diagnostic02/raw/01_F2_IR-FULL/external/round105/"
NUM = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relocated(name):
    normalized = str(name).replace("\\", "/")
    for marker in ("results/", "reference/"):
        at = normalized.find(marker)
        if at >= 0:
            normalized = normalized[at:]
            break
    relative = Path(normalized)
    assert not relative.is_absolute() and ".." not in relative.parts
    return ROOT / relative


class Evidence:
    def __init__(self, names):
        manifest_path = ROOT / (R105 + "compact_evidence/manifest.json")
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
        self.container_identity = dict(manifest_absolute_path=str(manifest_path.resolve()),
                                       manifest_sha256=digest(manifest_bytes), archive_used=False)
        entries = {entry["path"]: entry for entry in manifest["files"]}
        self.data, self.identity, self.origins = {}, {}, {}
        missing = set()
        for name in names:
            path = relocated(name)
            if path.is_file():
                self.data[name] = path.read_bytes()
                self.origins[name] = dict(actual_path=str(path.resolve()), source="loose_exact_bytes")
            else:
                missing.add(name)
        if missing:
            archive = ROOT / (R105 + "compact_evidence/evidence.tar.gz")
            assert digest(archive.read_bytes()) == manifest["archive_sha256"]
            self.container_identity.update(archive_used=True, archive_absolute_path=str(archive.resolve()),
                                           archive_sha256=manifest["archive_sha256"])
            # One sequential decompression pass, without restoring or rewriting history.
            with tarfile.open(archive, mode="r|gz") as source:
                for member in source:
                    if member.name in missing:
                        assert member.isfile()
                        self.data[member.name] = source.extractfile(member).read()
                        self.origins[member.name] = dict(actual_path=str(archive.resolve()),
                                                        member=member.name, source="compact_archive_exact_bytes")
            assert missing <= self.data.keys(), sorted(missing - self.data.keys())
        for name in names:
            actual = digest(self.data[name])
            assert actual == entries[name]["sha256"], (name, actual)
            self.identity[name] = actual

    def text(self, name):
        return self.data[name].decode("utf-8-sig")

    def json(self, name):
        return json.loads(self.text(name))


def parse_input(role):
    path = relocated(role["input_path"])
    raw = path.read_bytes()
    assert digest(raw) == role["input_sha256"]
    text = raw.decode("utf-8-sig")
    def payload(name):
        return re.search(r"(?m)^\s*" + name + r"\s*=\s*\[([^\n]*)\]", text).group(1)
    def vector(name):
        return ast.literal_eval("[" + payload(name) + "]")
    first = text.splitlines()[0]
    V, M = map(int, first[:first.index("[")].split())
    q = ast.literal_eval(first[first.index("["):])
    tokens = list(map(Decimal, NUM.findall(payload("points"))))
    points = list(zip(tokens[::2], tokens[1::2]))
    data = dict(V=V, M=M, Q=q, b=vector("initial"), capacity=vector("capacities"),
                target=vector("target"), weights=vector("weights"), points=points,
                T=role["T_seconds"], h=role["pickup_seconds"] + role["drop_seconds"],
                lam=role["lambda"], input_sha256=digest(raw))
    data["input_absolute_path"] = str(path.resolve())
    assert len(points) == V + 1 and len(q) == M
    assert q == role["Q_vector"]
    with localcontext() as context:
        context.prec = 70
        data["decimal_travel"] = [[((a[0]-b[0])**2 + (a[1]-b[1])**2).sqrt() / Decimal("1.5")
                                   for b in points] for a in points]
    floats = [(float(x), float(y)) for x, y in points]
    data["travel"] = [[math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2) / 1.5
                       for b in floats] for a in floats]
    return data


def conservative_metric(data):
    n = data["V"] + 1
    raw = [[0 if i == j else max(0, math.floor(math.nextafter(
            min(data["travel"][i][j], data["travel"][j][i]) * 1000, -math.inf)))
            for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            assert Decimal(raw[i][j]) / 1000 <= data["decimal_travel"][i][j]
    closed = [row[:] for row in raw]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                closed[i][j] = min(closed[i][j], closed[i][k] + closed[k][j])
    assert all(closed[i][j] <= raw[i][j] for i in range(n) for j in range(n))
    assert all(closed[i][j] <= closed[i][k] + closed[k][j]
               for i in range(n) for j in range(n) for k in range(n))
    return raw, closed


def mst(matrix, support):
    nodes = [0] + sorted(support)
    parent = {node: node for node in nodes}
    def root(node):
        while parent[node] != node:
            node = parent[node]
        return node
    edges = sorted((matrix[a][b], a, b) for a, b in itertools.combinations(nodes, 2))
    used = []
    for weight, a, b in edges:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[rb] = ra
            used.append((a, b, weight))
    assert len(used) == len(nodes) - 1
    return sum(edge[2] for edge in used), used


def values(text):
    out = {}
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            name, value = line.split()
            out[name] = float(value)
    return out


def objective(data, y):
    ratios = [y[i] / data["target"][i] for i in range(1, data["V"] + 1)]
    total = sum(ratios)
    numerator = sum(abs(a-b) for a, b in itertools.combinations(ratios, 2))
    penalty = sum(data["weights"][i] * abs(ratios[i-1]-1) for i in range(1, data["V"] + 1))
    return dict(G=numerator / (len(ratios) * total) if total > 0 else 0.0,
                P=penalty, F=(numerator / (len(ratios) * total) if total > 0 else 0.0) + data["lam"] * penalty)


def physical(data, vehicle, nodes, operation):
    assert nodes[0] == nodes[-1] == 0 and len(nodes) >= 2
    assert len(nodes[1:-1]) == len(set(nodes[1:-1]))
    assert set(nodes[1:-1]) == set(operation)
    load, pickup, delivery, prefixes = 0, 0, 0, []
    station_ok = True
    for station in nodes[1:-1]:
        q = operation[station]
        assert isinstance(q, int) and q != 0
        pickup += max(0, q)
        delivery += max(0, -q)
        load += q
        prefixes.append(load)
        station_ok &= 0 <= data["b"][station] - q <= data["capacity"][station]
    travel = sum(data["travel"][a][b] for a, b in zip(nodes, nodes[1:]))
    duration = travel + data["h"] * pickup
    load_ok = all(0 <= value <= data["Q"][vehicle] for value in prefixes)
    return dict(nodes=nodes, operations=operation, prefixes=prefixes, pickup=pickup,
                delivery=delivery, return_load=load, travel=travel,
                handling=data["h"]*pickup, duration=duration, station_ok=station_ok,
                load_ok=load_ok, feasible=station_ok and load_ok and duration <= data["T"] + 1e-7)


def complete_paid_seed(data, seed):
    checks, global_seen, inventory = [], set(), data["b"][:]
    assert len(seed["routes"]) == data["M"]
    assert sorted(route["vehicle"] for route in seed["routes"]) == list(range(data["M"]))
    for route in seed["routes"]:
        operations = {item["station"]:item["pickup"]-item["drop"] for item in route["operations"]}
        assert len(operations) == len(route["operations"]) and not (global_seen & operations.keys())
        global_seen.update(operations)
        check = physical(data, route["vehicle"], route["nodes"], operations)
        assert check["feasible"]
        checks.append(check)
        for station, quantity in operations.items():
            inventory[station] -= quantity
    parts = objective(data, inventory)
    assert abs(parts["F"]-seed["objective"]) < 1e-13
    assert sum(inventory[1:]) == sum(data["b"][1:])-sum(row["return_load"] for row in checks)
    return dict(routes=checks, objective=parts, Y=inventory)


def six_orders(data, vehicle, operation, conservative):
    assert len(operation) == 3
    rows = []
    for order in itertools.permutations(sorted(operation)):
        nodes = [0, *order, 0]
        row = physical(data, vehicle, nodes, operation)
        row["lower_travel"] = sum(conservative[a][b] for a, b in zip(nodes, nodes[1:])) / 1000
        row["lower_duration"] = row["lower_travel"] + row["handling"]
        rows.append(row)
    return rows


def decode_native_local(vector, data, operation):
    arcs = {(i,j) for i in range(data["V"]+1) for j in range(data["V"]+1)
            if i != j and vector[f"x_{i}_{j}"] > 0.5}
    nodes, used, seen = [0], set(), set()
    while True:
        outgoing = [b for a,b in arcs if a == nodes[-1]]
        assert len(outgoing) == 1
        next_node = outgoing[0]
        used.add((nodes[-1],next_node))
        nodes.append(next_node)
        if next_node == 0:
            break
        assert next_node not in seen and next_node in operation
        seen.add(next_node)
    assert used == arcs and seen == set(operation)
    for i in range(1,data["V"]+1):
        q = operation.get(i,0)
        assert abs(vector[f"z_{i}"]-bool(q)) <= 1e-5
        assert abs(vector[f"p_{i}"]-max(0,q)) <= 1e-5
        assert abs(vector[f"d_{i}"]-max(0,-q)) <= 1e-5
    return nodes


def b_qualification(data, operation, orders):
    pickup = sum(max(0,q) for q in operation.values())
    delivery = sum(max(0,-q) for q in operation.values())
    safety = 1e-5*max(1,data["T"])
    return (data["h"] > 0 and pickup == delivery and pickup > 0 and
            min(row["lower_travel"] for row in orders) + data["h"]*(pickup+1) > data["T"]+safety and
            all(not row["load_ok"] or row["lower_duration"] > data["T"]+safety for row in orders))


def local_mode(data, vector, vehicle):
    operation = {}
    for i in range(1, data["V"] + 1):
        p, d, z = (vector[f"{name}_{vehicle}_{i}"] for name in ("p", "d", "z"))
        assert all(abs(x-round(x)) <= 1e-5 for x in (p, d, z))
        if round(z):
            assert p >= 0 and d >= 0 and not (round(p) and round(d))
            operation[i] = round(p) - round(d)
            assert operation[i] != 0
            assert round(vector[f"Y_{i}"]) == data["b"][i] - operation[i]
        else:
            assert round(p) == round(d) == 0
    return operation


def b_row(data, operation, vehicle, available_names):
    coefficients = {f"z_{vehicle}_{i}": 1 for i in operation}
    thresholds = []
    for station, q in operation.items():
        theta = data["b"][station] - q
        choices = range(theta+1) if q > 0 else range(theta, data["capacity"][station]+1)
        thresholds.append(dict(station=station, operation=q, inventory_threshold=theta,
                               direction="le" if q > 0 else "ge"))
        for y in choices:
            name = f"state_{station}_{y}"
            if name in available_names:
                coefficients[name] = 1
    return coefficients, thresholds


def evaluate(coefficients, vector):
    return sum(coefficient * vector[name] for name, coefficient in coefficients.items())


def fixture(points, operations, Q, h, T):
    data = dict(V=len(points)-1, M=1, Q=[Q], h=h, T=T,
                b=[0] + [max(0, operations.get(i, 0)) for i in range(1, len(points))],
                capacity=[0] + [20]*(len(points)-1))
    data["travel"] = [[math.hypot(a[0]-b[0], a[1]-b[1]) for b in points] for a in points]
    return data


def counterexamples():
    operation = {1:2, 2:-3, 3:1}
    data = fixture([(0,0),(3,0),(3,3),(0,3),(3,2)], {**operation,4:1}, 3, 2, 20)
    exact_ms = [[value*1000 for value in row] for row in data["travel"]]
    orders = six_orders(data, 0, operation, exact_ms)
    lower = min(row["travel"] for row in orders)
    legal_min = min(row["duration"] for row in orders if row["load_ok"])
    assert abs(legal_min-(12+6*math.sqrt(2))) < 1e-12 and legal_min > 20
    assert lower + 2*(3+1) == 20
    assert not b_qualification(data,operation,orders)
    zero_h = dict(data, h=0)
    assert not b_qualification(zero_h,operation,orders)
    helper = physical(data, 0, [0,1,4,2,3,0], {**operation, 4:1})
    assert helper["feasible"] and helper["duration"] == 20
    assert helper["pickup"] > 3 and helper["return_load"] == 1
    old = fixture([(0,0),(0,0),(0,0),(0,0),(0,0)], {1:2,2:2,3:-3}, 3, 2, 100)
    old_orders = six_orders(old, 0, {1:2,2:2,3:-3}, [[0]*5 for _ in range(5)])
    assert not any(row["feasible"] for row in old_orders)
    assert not b_qualification(old,{1:2,2:2,3:-3},old_orders)
    repair = physical(old, 0, [0,1,4,2,3,0], {1:2,2:2,3:-3,4:-1})
    assert repair["feasible"] and repair["prefixes"] == [2,1,3,0]
    unequal = fixture([(0,0),(1,0),(2,0),(3,0)], {1:2,2:-1,3:-1}, 2, 2, 100)
    varied = six_orders(unequal, 0, {1:2,2:-1,3:-1}, [[value*1000 for value in row] for row in unequal["travel"]])
    assert any(row["feasible"] for row in varied) and any(not row["load_ok"] for row in varied)
    assert not b_qualification(unequal,{1:2,2:-1,3:-1},varied)
    # Unique supplier4 and four unit deliveries: single service assigns the
    # supplier to one vehicle; no other vehicle can leave empty and deliver.
    supplier = dict(V=5, M=1, Q=[4], h=2, T=16, b=[0,4,0,0,0,0], capacity=[0,9,9,9,9,9],
                    travel=[[0 if i == j else 1 if i == 0 or j == 0 else 2 for j in range(6)] for i in range(6)])
    supplier_route = physical(supplier, 0, [0,1,2,3,4,5,0], {1:4,2:-1,3:-1,4:-1,5:-1})
    assert supplier_route["travel"] == 10 and supplier_route["duration"] == 18 and not supplier_route["feasible"]
    return dict(balanced_equality_boundary=dict(orders=orders, lower=lower,
                minimum_prefix_feasible_duration=legal_min, extra_unit_budget=20,
                strict_budget_gate=False, helper=helper, unsafe_absence_free_row_activity=6, unsafe_rhs=5),
                unbalanced_capacity_helper=dict(orders=old_orders, helper=repair,
                balance_premise=False), zero_handling_gate=False, one_order_failure_is_insufficient=varied,
                unique_supplier_integer_assignment=supplier_route)


def main():
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="Repository/recovery root; historical absolute results/reference paths relocate here")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    assert not args.output.exists(), "fresh output identity required"
    protocol_path = ROOT / (R105 + "control01_protocol.json")
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes.decode("utf-8-sig"))
    roles = {role["id"]: role for role in protocol["roles"]}
    data_c, data_f = parse_input(roles["R98-C2"]), parse_input(roles["F2"])
    names = [C2 + name for name in ("master_1.lp.sol", "master_2.lp.sol", "master_3.lp.sol", "master_4.lp.sol", "start.mst", "seed.json", "patterns.csv")]
    names += [F2 + name for name in ("master_1.lp.sol", "start.mst", "seed.json")]
    positive_name = R105 + "modes/C2_controls01/R98-C2_seed_k0/native/oracle/full.lp.sol"
    names.append(positive_name)
    evidence = Evidence(names)
    c_vectors = [values(evidence.text(C2 + f"master_{i}.lp.sol")) for i in range(1, 5)]
    y_vectors = [[data_c["b"][0]] + [round(vector[f"Y_{i}"]) for i in range(1, data_c["V"]+1)] for vector in c_vectors]
    assert all(y == y_vectors[0] for y in y_vectors)
    memberships = [tuple(tuple(local_mode(data_c, vector, k)) for k in range(data_c["M"])) for vector in c_vectors]
    assert len(set(memberships)) == 4
    pattern_rows = list(csv.DictReader(io.StringIO(evidence.text(C2+"patterns.csv"))))
    for row in pattern_rows:
        event, vehicle, station = (int(row[name]) for name in ("iteration","vehicle","station"))
        assert int(row["inventory"]) == y_vectors[event-1][station]
        assert int(row["operation"]) == local_mode(data_c,c_vectors[event-1],vehicle).get(station,0)
    c_obj = objective(data_c, y_vectors[0])
    assert abs(c_obj["F"] - 0.19293317528184115) < 1e-13
    assert objective(data_c, [data_c["b"][0]] + [0]*data_c["V"])["G"] == 0
    operation_c = local_mode(data_c, c_vectors[0], 0)
    support_c = sorted(i for i, q in operation_c.items() if q > 0)
    assert support_c == [1,5,6,13,17,21] and sum(operation_c[i] for i in support_c) == 43
    c_raw, c_closed = conservative_metric(data_c)
    exact_mst, exact_edges = mst(data_c["decimal_travel"], support_c)
    floor_mst, floor_edges = mst(c_raw, support_c)
    closed_mst, closed_edges = mst(c_closed, support_c)
    assert abs(float(exact_mst)-2387.254251) < 1e-6
    coefficients_a = {f"p_0_{i}":data_c["h"] for i in support_c}
    coefficients_a.update({f"z_0_{i}":closed_mst/1000 for i in support_c})
    rhs_a = data_c["T"] + (len(support_c)-1)*closed_mst/1000
    c_start = values(evidence.text(C2 + "start.mst"))
    a_violation = evaluate(coefficients_a, c_vectors[0]) - rhs_a
    assert a_violation > 300 and rhs_a-evaluate(coefficients_a, c_start) >= -1e-7
    f_vector, f_start = values(evidence.text(F2 + "master_1.lp.sol")), values(evidence.text(F2 + "start.mst"))
    operation_f = local_mode(data_f, f_vector, 0)
    assert operation_f == {6:9,7:-16,9:7}
    f_raw, f_closed = conservative_metric(data_f)
    orders = six_orders(data_f, 0, operation_f, f_closed)
    lower = min(row["lower_travel"] for row in orders)
    exact_lower = min(row["travel"] for row in orders)
    pickup = sum(max(0,q) for q in operation_f.values())
    delivery = sum(max(0,-q) for q in operation_f.values())
    margin = 1e-5*max(1, data_f["T"])
    assert pickup == delivery == 16
    assert lower + data_f["h"]*(pickup+1) > data_f["T"] + margin
    assert all(not row["load_ok"] or row["lower_duration"] > data_f["T"] + margin for row in orders)
    assert sum(row["load_ok"] for row in orders) == 2
    assert b_qualification(data_f,operation_f,orders)
    assert abs(exact_lower-1661.1355644215034) < 1e-8
    ordinary_mst, _ = mst(data_f["decimal_travel"], list(operation_f))
    assert float(ordinary_mst) + data_f["h"]*(pickup+1) < data_f["T"]
    coefficients_b, thresholds = b_row(data_f, operation_f, 0, f_vector)
    assert evaluate(coefficients_b, f_vector)-5 > 0.999
    assert 5-evaluate(coefficients_b, f_start) >= -1e-7
    reassigned_literal = dict(f_vector)
    reassigned_literal["z_0_6"] = 0
    assert evaluate(coefficients_b,reassigned_literal) <= 5+1e-7
    # Existing one-hot state domain is enough: indicators retain exact iff
    # meaning at every inventory represented in the actual master.
    mapping_checks = []
    for item in thresholds:
        station, theta, sign = item["station"], item["inventory_threshold"], item["direction"]
        for y in range(max(0,theta-1), min(data_f["capacity"][station],theta+1)+1):
            event = (y <= theta) if sign == "le" else (y >= theta)
            amount = (data_f["b"][station]-y) if sign == "le" else (y-data_f["b"][station])
            assert event == (amount >= abs(operation_f[station]))
            mapping_checks.append(dict(station=station, y=y, event=event, implied_amount=amount))
    # 108 constant arithmetic cases test the threshold-budget argument:
    # all true thresholds plus total pickup<=P0 and delivery<=pickup force
    # equality at every threshold and no outside pickup/delivery.
    budget_cases = 0
    for deltas in itertools.product(range(3), repeat=3):
        for outside_p, outside_d in itertools.product(range(2), repeat=2):
            p = 9+deltas[0] + 7+deltas[2] + outside_p
            d = 16+deltas[1] + outside_d
            if p <= 16 and d <= p:
                assert deltas == (0,0,0) and outside_p == outside_d == 0
            budget_cases += 1
    assert budget_cases == 108
    seed = evidence.json(C2 + "seed.json")
    c_paid_seed = complete_paid_seed(data_c, seed)
    f_paid_seed = complete_paid_seed(data_f, evidence.json(F2 + "seed.json"))
    car0_seed = next(route for route in seed["routes"] if route["vehicle"] == 0)
    car0_ops = {item["station"]:item["pickup"]-item["drop"] for item in car0_seed["operations"]}
    native_positive = physical(data_c,0,decode_native_local(values(evidence.text(positive_name)),data_c,car0_ops),car0_ops)
    assert native_positive["feasible"] and native_positive["pickup"] > data_c["Q"][0]
    assert abs(native_positive["duration"]-7193.634304515107) < 1e-8
    output = dict(status="PASS", reviewer="/root/independent_review", Optimize_calls=0, IIS_calls=0,
            subprocess_calls=0, DP_calls=0, source_sha256=digest(Path(__file__).read_bytes()),
            source_absolute_path=str(Path(__file__).resolve()), root_absolute_path=str(ROOT),
            invocation=sys.argv, evidence_sha256=evidence.identity, evidence_origins=evidence.origins,
            evidence_container_identity=evidence.container_identity,
            protocol_identity=dict(actual_path=str(protocol_path.resolve()), sha256=digest(protocol_bytes)),
            input_sha256={key:roles[key]["input_sha256"] for key in roles},
            input_absolute_paths={"R98-C2":data_c["input_absolute_path"],"F2":data_f["input_absolute_path"]},
            numeric_contract=dict(FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6,
                                  physical_duration_tolerance=1e-7, structure_gate_margin="1e-5*max(1,T)",
                                  lower_travel="symmetric min; downward nextafter milliseconds; integer Floyd metric closure"),
            C2=dict(Y=y_vectors[0], objective=c_obj, optimal_events=4, distinct_Y=1, distinct_memberships=4,
                    support=support_c, pickup=sum(operation_c[i] for i in support_c),
                    decimal_MST=str(exact_mst), decimal_edges=[(a,b,str(w)) for a,b,w in exact_edges],
                    floor_MST_ms=floor_mst, floor_edges=floor_edges, closed_MST_ms=closed_mst,
                    closed_edges=closed_edges, complete_lower_duration=closed_mst/1000+data_c["h"]*43,
                    A=dict(coefficients=coefficients_a, rhs=rhs_a, current_raw_violation=a_violation,
                           legal_start_slack=rhs_a-evaluate(coefficients_a,c_start)),
                    paid_seed=c_paid_seed, native_positive_control=native_positive),
            F2=dict(operations=operation_f, orders=orders, exact_lower_travel=exact_lower,
                    conservative_lower_travel=lower, ordinary_MST=str(ordinary_mst),
                    extra_pickup_unit_lower_duration=lower+data_f["h"]*(pickup+1),
                    strict_budget_gate=True, all_orders_rejected=True, threshold_coefficients=coefficients_b,
                    thresholds=thresholds, rhs=5, nonzero_coefficients=len(coefficients_b),
                    current_raw_violation=evaluate(coefficients_b,f_vector)-5,
                    legal_start_slack=5-evaluate(coefficients_b,f_start), mapping_checks=mapping_checks,
                    z_removed_same_Y_activity=evaluate(coefficients_b,reassigned_literal),
                    z_removed_point_scope="Boolean/literal mapping only; no claim of a feasible alternate master/fleet",
                    threshold_budget_cases=budget_cases, paid_seed=f_paid_seed), counterexamples=counterexamples(),
            scope="Independent arithmetic and physical checks of retained evidence; no independent model/performance rerun")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=output["status"], C2_MST=float(exact_mst), C2_conservative_MST=closed_mst/1000,
                          C2_F=c_obj["F"], F2_travel_lower=lower, F2_nonzeros=len(coefficients_b),
                          Optimize_calls=0, IIS_calls=0), sort_keys=True))


if __name__ == "__main__":
    main()
