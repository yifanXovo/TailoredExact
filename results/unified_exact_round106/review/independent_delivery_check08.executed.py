"""Independent zero-solver Round106 delivery check.

Imports only stdlib and the SHA-checked independent reviewer arithmetic source.
Never imports a project implementation, solver, or engineering report reader.
Raw current call scope is qualification/, fixed_Y/, development01/raw/ only.
Supports restored-root execution and semantic comparison without original paths.
"""
import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path
import re

BASE = "results/unified_exact_round106/"
MATH_SHA = "5a649ace202cf880c2e60d47accbebc5152e36b7412c71918871dfb1218df675"
ROOT = None
READS = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    normalized = str(name).replace("\\", "/")
    for marker in ("results/", "reference/", "src/", "include/", "tests/", "build/"):
        at = normalized.find(marker)
        if at >= 0:
            normalized = normalized[at:]
            break
    path = Path(normalized)
    assert not path.is_absolute() and ".." not in path.parts, normalized
    path = ROOT / path
    data = path.read_bytes()
    key = path.relative_to(ROOT).as_posix()
    READS[key] = {"sha256": sha(data), "actual_absolute_path": str(path.resolve())}
    return data.decode("utf-8-sig")


def js(name):
    return json.loads(read(name))


def rows(name):
    return list(csv.DictReader(io.StringIO(read(name))))


def close(a, b, tol=1e-10):
    assert abs(float(a) - float(b)) <= tol * max(1, abs(float(a)), abs(float(b))), (a, b)


def native_calls():
    grouped = collections.defaultdict(lambda: dict(started=0, returned=0, seconds=0.0))
    calls = []
    for scope in ("qualification", "fixed_Y", "development01/raw"):
        for path in sorted((ROOT / BASE / scope).rglob("calls.csv")):
            name = path.relative_to(ROOT).as_posix()
            records = rows(name)
            before, after = {}, {}
            for row in records:
                key = (row["call"], row["phase"])
                target = before if row["stage"] == "before" else after
                assert row["stage"] in ("before", "after") and key not in target
                target[key] = row
            assert before.keys() == after.keys(), name
            for key, before_row in before.items():
                after_row = after[key]
                assert float(after_row["process_seconds"]) >= float(before_row["process_seconds"])
                assert before_row["model_sha256"] == after_row["model_sha256"]
                group = grouped[(name, key[1])]
                group["started"] += 1
                group["returned"] += 1
                group["seconds"] += float(after_row["seconds"])
            calls.extend(dict(path=name, phase=phase, **value) for (path_, phase), value in grouped.items() if path_ == name)
    total = collections.Counter()
    for value in calls:
        total["raw_started"] += value["started"]
        total["raw_returned"] += value["returned"]
        total["IIS" if value["phase"] == "iis" else "Optimize_raw"] += value["started"]
    total["control_Optimize"] = 12  # Independently corroborated by four result ledgers below.
    total["Optimize"] = total["Optimize_raw"] + total["control_Optimize"]
    assert total["raw_started"] == total["raw_returned"] == 5778
    assert total["IIS"] == 156 and total["Optimize"] == 5634
    published = rows(BASE + "reports02/native_calls.csv")
    actual = {(value["path"], value["phase"]): value for value in calls}
    assert len(actual) == len(published)
    for item in published:
        observed = actual[(item["path"], item["phase"])]
        assert int(item["started"]) == observed["started"] == int(item["returned"])
        assert int(item["missing_after"]) == 0
        close(item["native_seconds"], observed["seconds"])
    correction = js(BASE + "reader_correction.json")
    assert correction["corrected_Optimize_starts"] == total["Optimize"]
    assert len(correction["excluded_paths"]) == 2
    assert not any(item["path"] in correction["excluded_paths"] for item in calls)
    return {"scope": ["qualification/", "fixed_Y/", "development01/raw/"], "totals": dict(total),
            "phase_ledger_rows": calls, "withdrawn_reader_difference": 2,
            "missing_after": 0, "nested_seconds_added_to_fees": False}


def fees():
    out = []
    for directory in sorted((ROOT / BASE / "fees").iterdir()):
        name = directory.name
        receipt = js(BASE + "fees/" + name + "/receipt.json")
        launch = js(BASE + "fees/" + name + "/launch.json")
        assert receipt["engineering"] is False
        assert receipt["conservative_process_starts"] == launch["conservative_process_starts"]
        assert launch["conservative_process_starts"] == 1 + launch["declared_nested_process_starts"]
        out.append(dict(label=name, **receipt, declared_children=launch["declared_nested_process_starts"]))
    assert len(out) == 7
    assert sum(item["conservative_process_starts"] for item in out) == 30
    close(sum(item["outer_seconds"] for item in out), 13089.59282640001)
    failures = [item["label"] for item in out if item["exit_code"]]
    assert failures == ["development_batch01"]
    stderr = read(BASE + "fees/development_batch01/stderr.log")
    assert "competing" in stderr
    published = {item["label"]: item for item in rows(BASE + "reports02/fees.csv")}
    assert len(published) == len(out)
    for item in out:
        close(item["outer_seconds"], published[item["label"]]["outer_seconds"])
    return {"conservative_starts": 30, "outer_seconds": 13089.59282640001,
            "receipts": out, "failed_batch_charge": "1 wrapper + 8 declared unlaunched children conservatively retained; not 9 proven process starts"}


def vector(name, names, independent):
    sparse = independent.values(read(name))
    assert sparse.keys() <= names
    return collections.defaultdict(float, sparse)


def prove_certificate(cert, data, lower, independent, names):
    family, k = cert["family"], cert["vehicle"]
    operation = dict(zip(cert["support"], cert["operations"]))
    h = math.nextafter(float(data["h"]), -math.inf)
    assert h == cert["handling_lower"]
    if family == "A_MST":
        assert all(q > 0 for q in operation.values())
        ms, edges = independent.mst(lower, operation)
        travel = math.nextafter(ms / 1000.0, -math.inf)
        close(travel, cert["travel_lower"], 1e-14)
        assert sum(operation.values()) == cert["pickup"]
        assert travel + h*cert["pickup"] > data["T"] + 1e-7 + 1e-5*max(1, data["T"])
        coefficients = {f"p_{k}_{i}": h for i in operation}
        coefficients.update({f"z_{k}_{i}": travel for i in operation})
        close(cert["rhs"], data["T"] + 1e-7 + travel*(len(operation)-1), 1e-14)
        declared_edges = cert["mst_edges"]
        assert len(declared_edges) == len(operation)
        assert sum(lower[a][b] for a, b in declared_edges) == ms
        decimal_mst, _ = independent.mst(data["decimal_travel"], operation)
        return coefficients, {"integer_milliseconds": ms, "Kruskal_edges": edges,
                              "unrounded_decimal_MST": str(decimal_mst), "pickup": cert["pickup"],
                              "conservative_duration": travel+h*cert["pickup"]}
    assert family in ("B_EXACT", "B_THRESHOLD")
    orders = independent.six_orders(data, k, operation, lower)
    assert independent.b_qualification(data, operation, orders)
    assert len(cert["orders"]) == 6
    for source, expected in zip(cert["orders"], orders):
        assert source["order"] == expected["nodes"][1:-1]
        assert source["loads"] == expected["prefixes"]
        assert source["prefix_feasible"] == expected["load_ok"]
        close(source["travel_lower"], expected["lower_travel"], 1e-14)
        close(source["duration_lower"], expected["lower_duration"], 1e-14)
    if family == "B_THRESHOLD":
        global_states = {f"state_{i}_{inventory}" for i in operation for inventory in range(data["capacity"][i]+1)}
        coefficients, thresholds = independent.b_row(data, operation, k, global_states)
    else:
        coefficients = {f"z_{k}_{i}": 1 for i in operation}
        coefficients.update({f"state_{i}_{data['b'][i]-q}": 1 for i, q in operation.items()})
        thresholds = []
    assert cert["rhs"] == 5
    return coefficients, {"operations": operation, "orders": orders, "thresholds": thresholds,
                          "strict_extra_unit_lower_duration": min(item["lower_travel"] for item in orders) + h*(cert["pickup"]+1)}


def local_operation(data, candidate, vehicle):
    operation = {}
    for i in range(1, data["V"]+1):
        raw = [candidate[f"{prefix}_{vehicle}_{i}"] for prefix in ("p", "d", "z")]
        assert all(math.isfinite(value) and abs(value-round(value)) <= 1e-5 for value in raw)
        p, d, z = map(round, raw)
        assert p >= 0 and d >= 0 and z in (0,1) and not (p and d)
        assert bool(z) == bool(p or d)
        if z:
            operation[i] = p-d
            assert round(candidate[f"Y_{i}"]) == data["b"][i] - operation[i]
    return operation


def arm_check(published, data, independent):
    destination = published["destination"]
    audit = js(destination + "/audit.json")
    assert audit["passed"]
    completion = js(destination + "/completion.json")
    close(published["observed_end_to_end_seconds"], completion["end_to_end_seconds"])
    result = js(destination + "/result.json")
    if published["arm"] in ("P-GRB", "ENS-C"):
        physical = independent.complete_paid_seed(data, dict(objective=result["objective"], routes=result["routes"]))
        assert physical["Y"] == result["final_inventories"]
        close(published["U"], physical["objective"]["F"])
        close(published["L"], result["lower_bound"])
        return {"id": published["id"], "arm": published["arm"], "physical_final": physical,
                "control_Optimize": int(published["control_native_calls"]),
                "process_seconds": completion["process_wall_seconds"], "U": float(published["U"]), "L": float(published["L"]),
                "certified": published["certificate"] == "True"}
    base = destination + "/external/round106/"
    summary = js(base + "summary.json")
    names = {item["name"] for item in rows(base + "variables.csv")}
    seed = js(base + "seed.json")
    seed_physical = independent.complete_paid_seed(data, seed)
    start = collections.defaultdict(float)
    for i, inventory in enumerate(seed_physical["Y"][1:], 1):
        start[f"Y_{i}"] = inventory
        start[f"state_{i}_{inventory}"] = 1
    for k, route in enumerate(seed_physical["routes"]):
        for i, quantity in route["operations"].items():
            start[f"z_{k}_{i}"] = 1
            start[f"p_{k}_{i}"] = max(0, quantity)
            start[f"d_{k}_{i}"] = max(0, -quantity)
    events = [json.loads(line) for line in read(base + "events.jsonl").splitlines()]
    assert len(events) == summary["events"]
    lazy = rows(base + "lazy.csv")
    assert len(lazy) == summary["lazy_calls"]
    by_event = collections.defaultdict(list)
    for item in lazy:
        by_event[int(item["event"])].append(item)
    all_modes, tagged_modes, fleets, stocks = set(), set(), set(), set()
    candidates, proof_results = {}, []
    row_cache = {}
    for event in events:
        e = event["event"]
        assert e == len(candidates) + 1
        candidate = vector(base + f"candidate_{e}.sol", names, independent)
        candidates[e] = candidate
        stock = [round(candidate[f"Y_{i}"]) for i in range(1, data["V"]+1)]
        assert stock == event["Y"]
        seen = set()
        modes = []
        for k in range(data["M"]):
            operation = local_operation(data, candidate, k)
            assert not seen.intersection(operation)
            seen.update(operation)
            assert [operation.get(i, 0) for i in range(1, data["V"]+1)] == event["operations"][k]
            key = (data["Q"][k], data["T"], data["h"], data["input_sha256"], tuple(sorted(operation.items())))
            modes.append(key)
            all_modes.add(key)
            tagged_modes.add((k, key))
        fleet = tuple(modes)
        assert event["repeat"] == (fleet in fleets)
        fleets.add(fleet)
        stocks.add(tuple(stock))
        parts = independent.objective(data, [data["b"][0], *stock])
        close(parts["F"], event["Ftrue"])
        assert event["model_objective"] + 1e-7 >= parts["F"]
        assert sorted(event["submitted_lazy_rows"]) == sorted(int(item["row"]) for item in by_event[e])
        for item in by_event[e]:
            row_id = int(item["row"])
            if row_id not in row_cache:
                rr = rows(base + f"row_{row_id}.csv")
                coefficients = {term["variable"]: float(term["coefficient"]) for term in rr}
                assert len(coefficients) == len(rr)
                row_cache[row_id] = coefficients
            coefficients = row_cache[row_id]
            activity = sum(value*candidate[name] for name, value in coefficients.items())
            start_activity = sum(value*start[name] for name, value in coefficients.items())
            close(activity, item["activity"])
            close(start_activity, item["start_activity"])
            rhs = float(item["rhs"])
            assert start_activity <= rhs + 1e-6*max(1, abs(rhs))
            assert activity-rhs > max(1e-7, 1e-6*max(1, abs(activity), abs(rhs)))
            assert int(item["api_return"]) == 0
        if event["outcome"] == "REJECTED_PROVED_LAZY":
            assert by_event[e]
        if event["outcome"] == "UNKNOWN_SAFE_INTERRUPT":
            assert not by_event[e]
    assert len(fleets) == summary["distinct_fleet_candidates"]
    assert len(stocks) == summary["distinct_Y"]
    assert len(tagged_modes) == summary["distinct_car_modes"]
    _, lower = independent.conservative_metric(data)
    for path in sorted((ROOT / base).glob("certificate_*.json")):
        cert = js(path.relative_to(ROOT).as_posix())
        e = int(path.stem.split("_")[1])
        coefficients, proof = prove_certificate(cert, data, lower, independent, names)
        assert coefficients == cert["coefficients"]
        mapped_coefficients = {name:value for name,value in coefficients.items() if name in names}
        absent = sorted(coefficients.keys()-names)
        assert all(name.startswith("state_") for name in absent)
        matches = [item for item in by_event[e] if item["family"] == cert["family"] and int(item["vehicle"]) == cert["vehicle"]]
        # Cross-car pooled A copies need not be submitted at this event, but source copy must be.
        assert matches, path.name
        for item in matches:
            assert row_cache[int(item["row"])] == mapped_coefficients
        proof_results.append({"event": e, "vehicle": cert["vehicle"], "family": cert["family"],
                              "absent_zero_states_in_current_domain": absent, **proof})
    physical_ubs = []
    for path in sorted((ROOT / base).glob("physical_ub_*.json")):
        witness = js(path.relative_to(ROOT).as_posix())
        physical_ubs.append(independent.complete_paid_seed(data, witness))
    assert len(physical_ubs) == summary["new_physical_UBs"]
    close(summary["UB"], min([seed_physical["objective"]["F"]] + [item["objective"]["F"] for item in physical_ubs]))
    close(summary["LB"], published["L"])
    assert 0 <= summary["LB"] <= summary["UB"]
    close(summary["UB"], published["U"])
    acceptance = rows(base + "submission_acceptance.csv")
    assert len(acceptance) == summary["submission_attempts"]
    final_vector = vector(base + "master_0.lp.sol", names, independent)
    acceptance_proof = []
    for index, item in enumerate(acceptance, 1):
        submitted = vector(base + f"submission_{index}.sol", names, independent)
        def equal(a, b):
            return all(abs(a.get(name, 0)-b.get(name, 0)) <= 1e-5 for name in a.keys() | b.keys())
        observed_events = [e for e, candidate in candidates.items() if equal(candidate, submitted)]
        assert bool(observed_events) == bool(int(item["observed_MIPSOL_vector"]))
        assert equal(final_vector, submitted) == bool(int(item["final_native_accepted"]))
        witness = physical_ubs[index-1]
        for k, route in enumerate(witness["routes"]):
            arcs = {(a,b) for a in range(data["V"]+1) for b in range(data["V"]+1)
                    if a != b and submitted.get(f"x_{k}_{a}_{b}", 0) > .5}
            assert arcs == set(zip(route["nodes"], route["nodes"][1:]))
        close(item["physical_F"], witness["objective"]["F"])
        acceptance_proof.append(dict(event=int(item["event"]), matched_raw_MIPSOL_events=observed_events,
                                     final_native_vector_matches=equal(final_vector, submitted), physical_F=float(item["physical_F"])))
    close(summary["master_exclusive_seconds"] + summary["callback_inclusive_seconds"], summary["master_inclusive_seconds"])
    close(sum(summary[key] for key in ("oracle_seconds", "iis_seconds", "core_confirmation_seconds", "separation_seconds", "audit_mapping_seconds", "callback_other_seconds")), summary["callback_inclusive_seconds"])
    if summary["unresolved_candidate"]:
        assert events[-1]["outcome"] == "UNKNOWN_SAFE_INTERRUPT" and not summary["final_native_bound_qualified"]
        assert summary["LB"] <= max(item["native_global_bound"] for item in events if item["native_global_bound"] is not None)
        assert summary["UB"] > events[-1]["Ftrue"]  # Native tentative objective is not a verified UB.
    return {"id": published["id"], "arm": published["arm"], "summary": summary,
            "verified_lazy_calls": len(lazy), "verified_raw_candidates": len(candidates),
            "structural_certificates": proof_results, "independent_physical_UBs": physical_ubs,
            "native_acceptance": acceptance_proof, "first_events": events[:6], "last_events": events[-3:],
            "physical_mode_count": len(all_modes), "vehicle_tagged_mode_count": len(tagged_modes),
            "certified": summary["certified"]}


def main():
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    math_path = Path(__file__).with_name("independent_math_check05.executed.py")
    assert sha(math_path.read_bytes()) == MATH_SHA
    spec = importlib.util.spec_from_file_location("independent_reviewer_arithmetic", math_path)
    independent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(independent)
    independent.ROOT = ROOT
    protocol = js(BASE + "development_protocol.json")
    data = {role["id"]: independent.parse_input(role) for role in protocol["roles"]}
    for role in protocol["roles"]:
        read(role["input_path"])
    identity = js(BASE + "development01/identity.json")
    qualification = js(BASE + "qualification/identity.json")
    assert identity["candidate_binary_sha256"] == qualification["production_PE_SHA"]
    assert identity["source_hashes"] == qualification["source_bindings"]
    for name, expected in qualification["source_bindings"].items():
        read(name)
        assert READS[name]["sha256"] == expected
    calls = native_calls()
    paid = fees()
    published = rows(BASE + "reports02/arm_results.csv")
    assert len(published) == 8
    arms = [arm_check(item, data[item["id"]], independent) for item in published]
    assert sum(item.get("control_Optimize", 0) for item in arms) == 12
    fixed = js(BASE + "fixed_Y/native/diagnostic.json")
    assert fixed["classification"] == "UNKNOWN" and fixed["physical_verified"] is False
    assert fixed["Optimize_calls"] == 1 and fixed["IIS_calls"] == 0 and fixed["production_handoff"] is False
    close(independent.objective(data["R98-C2"], [data["R98-C2"]["b"][0], *fixed["Y"]])["F"], fixed["Ftrue_fixed_Y"])
    selected = js(BASE + "real_modes_report02.json")
    assert len(selected["selected_modes"]) == 8
    assert selected["independent_formal_inputs"] == 2
    for mode in selected["selected_modes"]:
        assert mode["source"] == "current_formal_native_MIPSOL_noninitial" and not mode["matches_start_fleet"]
        assert READS[mode["candidate"]]["sha256"] == mode["candidate_SHA"]
        for proof in mode["proof_files"]:
            assert READS[proof["path"]]["sha256"] == proof["SHA"]
    by_key = {(item["id"], item["arm"]): item for item in arms}
    for item in selected["coverage"]:
        actual = by_key[(item["id"], item["arm"])]
        assert item["physical_parameter_keyed_car_modes"] == actual["physical_mode_count"]
        assert item["vehicle_tagged_car_modes"] == actual["vehicle_tagged_mode_count"]
    assert by_key[("F2", "ENS-C")]["certified"]
    assert not by_key[("F2", "EVENT-STRUCT")]["certified"]
    p_ub = by_key[("R98-C2", "P-GRB")]["U"]
    assert all(p_ub < by_key[("R98-C2", arm)]["summary"]["UB"] for arm in ("EVENT-FULL", "EVENT-CORE", "EVENT-STRUCT"))
    semantics = {"math_source_SHA": MATH_SHA, "production_PE_SHA": qualification["production_PE_SHA"],
                 "raw_native": calls, "research_fees": paid, "arms": arms, "fixed_Y": fixed,
                 "negative_result": "RETAIN_COMPONENT_ONLY is supported for this frozen candidate and this two-input development panel"}
    out = {"passed": True, "root": str(ROOT), "checker_SHA": sha(Path(__file__).read_bytes()),
           "Optimize_calls": 0, "IIS_calls": 0, "native_process_starts": 0,
           "implementation_scope": "stdlib plus own SHA-bound independent arithmetic; no production math, physical or report imports",
           "semantic_result": semantics, "source_evidence": READS}
    if args.compare:
        previous = json.loads(args.compare.read_text(encoding="utf-8"))
        assert previous["semantic_result"] == json.loads(json.dumps(semantics, ensure_ascii=False, default=str))
        assert {k:v["sha256"] for k,v in previous["source_evidence"].items()} == {k:v["sha256"] for k,v in READS.items()}
        out["comparison"] = {"passed": True, "baseline_absolute_path": str(args.compare.resolve()), "baseline_SHA": sha(args.compare.read_bytes())}
    assert not args.output.exists(), "Output identity must be fresh"
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "output": str(args.output.resolve()), "evidence_files": len(READS),
                      "native_counts": calls["totals"], "Optimize_calls": 0, "IIS_calls": 0}))


if __name__ == "__main__":
    main()
