#!/usr/bin/env python3
"""Evidence-gated finalizer for the Round 45 completion package.

This program intentionally derives every classification from sealed completion
rows.  It exits after writing audit state when the mandatory matrix is not
complete; it never promotes the candidate from historical aggregate ratios.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
OUT = ROUND / "completion"
MATRIX = OUT / "required_run_matrix.csv"
CERT_EPS = 1e-7
MAJOR_HARMFUL_INSTANCE = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
MAJOR_HARMFUL_PARENT = "L2"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    columns = fields or (list(rows[0]) if rows else ["record_state"])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def write_md(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def run_dir(row: dict[str, str]) -> Path:
    return ROUND / row["run_directory"]


def manifest_valid(directory: Path) -> tuple[bool, str]:
    path = directory / "artifact_manifest.csv"
    if not path.is_file():
        return False, "artifact_manifest_missing"
    for entry in read_csv(path):
        artifact = directory / entry["path"]
        if not artifact.is_file():
            return False, f"manifest_artifact_missing:{entry['path']}"
        if artifact.stat().st_size != int(entry["size_bytes"]):
            return False, f"manifest_size_mismatch:{entry['path']}"
        if sha256(artifact) != entry["sha256"]:
            return False, f"manifest_hash_mismatch:{entry['path']}"
    return True, "pass"


def command_has_contract(command: dict[str, Any], row: dict[str, str]) -> tuple[bool, str]:
    args = command.get("command", [])
    try:
        pairs = {args[i]: args[i + 1] for i in range(len(args) - 1)
                 if isinstance(args[i], str) and args[i].startswith("--")}
        cap = float(row["process_cap_seconds"])
        if float(pairs["--time-limit"]) != cap:
            return False, "time_limit_mismatch"
        if float(pairs["--process-wall-time-limit"]) != cap:
            return False, "process_cap_mismatch"
        if int(pairs["--threads"]) != 1 or int(pairs["--mip-threads"]) != 1:
            return False, "thread_contract_mismatch"
        if not truth(command.get("sequential_official_execution")):
            return False, "sequential_flag_missing"
    except (KeyError, ValueError, IndexError):
        return False, "command_contract_unparseable"
    return True, "pass"


def audit_matrix(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    executable_hashes: set[str] = set()
    for row in rows:
        directory = run_dir(row)
        marker_path = directory / "completion_marker.json"
        result_path = directory / "result.json"
        command_path = directory / "command.json"
        reasons: list[str] = []
        marker: dict[str, Any] = {}
        result: dict[str, Any] = {}
        command: dict[str, Any] = {}
        if not marker_path.is_file():
            reasons.append("completion_marker_missing")
        else:
            marker = load_json(marker_path)
            if marker.get("row_id") != row["row_id"] or not truth(marker.get("complete")):
                reasons.append("completion_marker_identity_invalid")
            executable_hashes.add(str(marker.get("executable_sha256", "")))
        if not result_path.is_file():
            reasons.append("result_missing")
        else:
            result = load_json(result_path)
        if not command_path.is_file():
            reasons.append("command_missing")
        else:
            command = load_json(command_path)
            command_ok, command_reason = command_has_contract(command, row)
            if not command_ok:
                reasons.append(command_reason)
            if command.get("row_id") != row["row_id"]:
                reasons.append("command_row_identity_invalid")
        manifest_ok, manifest_reason = manifest_valid(directory)
        if not manifest_ok:
            reasons.append(manifest_reason)
        strict = truth(marker.get("strict_certificate"))
        local_exact = truth(marker.get("local_parent_exact"))
        capped = truth(marker.get("honest_required_cap"))
        if marker and not (strict or local_exact or capped):
            reasons.append("unacceptable_terminal_state")
        if capped and number(marker.get("process_seconds")) < number(
                row["process_cap_seconds"]) - 30.0:
            reasons.append("dishonest_short_cap")
        if "counterfactual" in row["stage"] and not truth(
                marker.get("counterfactual_valid")):
            reasons.append("counterfactual_invalid")
        expected = [name for name in row["expected_evidence_files"].split(";") if name]
        aliases: list[str] = []
        missing_expected: list[str] = []
        for name in expected:
            if (directory / name).is_file():
                continue
            if (row["arm"] == "pgrb" and name == "global_bound_trace.csv" and
                    (directory / "normalized_global_bound_trace.csv").is_file()):
                aliases.append(
                    "global_bound_trace.csv=normalized_global_bound_trace.csv")
                continue
            missing_expected.append(name)
        reasons.extend(f"expected_artifact_missing:{name}" for name in missing_expected)
        audit.append({
            "row_id": row["row_id"], "stage": row["stage"],
            "instance": row["instance"], "arm": row["arm"],
            "complete": not reasons, "terminal_strict": strict,
            "terminal_local_parent_exact": local_exact,
            "terminal_honest_cap": capped,
            "process_seconds": marker.get("process_seconds", ""),
            "executable_sha256": marker.get("executable_sha256", ""),
            "artifact_aliases": ";".join(aliases) if aliases else "none",
            "failure_reasons": ";".join(reasons) if reasons else "none",
        })
    summary = {
        "required_rows": len(rows),
        "completed_rows": sum(truth(row["complete"]) for row in audit),
        "missing_or_invalid_rows": [row["row_id"] for row in audit
                                    if not truth(row["complete"])],
        "unique_executable_hashes": sorted(value for value in executable_hashes if value),
    }
    summary["pass"] = (summary["completed_rows"] == summary["required_rows"] and
                       len(summary["unique_executable_hashes"]) == 1)
    return audit, summary


def metrics(result: dict[str, Any], marker: dict[str, Any]) -> dict[str, Any]:
    external = "external_gini_tree_work" in result
    lower = result.get("external_gini_tree_global_lower_bound",
                       result.get("best_bound", result.get("lower_bound", "")))
    upper = result.get("external_gini_tree_verified_upper_bound",
                       result.get("verified_objective", result.get("upper_bound", "")))
    rel_gap = ((max(0.0, number(upper) - number(lower)) /
                max(abs(number(upper)), CERT_EPS))
               if math.isfinite(number(lower)) and math.isfinite(number(upper)) else "")
    return {
        "strict_certificate": truth(marker.get("strict_certificate")),
        "local_parent_exact": truth(marker.get("local_parent_exact")),
        "honest_cap": truth(marker.get("honest_required_cap")),
        "seconds": number(marker.get("process_seconds"), 0.0),
        "work": number(result.get("external_gini_tree_work" if external else
                                  "gurobi_work"), 0.0),
        "nodes": number(result.get("external_gini_tree_nodes" if external else
                                   "gurobi_node_count"), 0.0),
        "lp_work": number(result.get("external_gini_tree_lp_work"), 0.0),
        "partial_mip_work": number(result.get("external_gini_tree_partial_mip_work"), 0.0),
        "terminal_mip_work": number(result.get("external_gini_tree_terminal_mip_work"), 0.0),
        "split_count": int(number(result.get("external_gini_tree_split_count"), 0)),
        "initial_interval_count": int(number(
            result.get("external_gini_tree_contract_initial_interval_count"), 0)),
        "final_interval_count": int(number(
            result.get("external_gini_tree_final_leaf_count"), 0)),
        "lp_jobs": int(number(result.get("external_gini_tree_lp_optimize_count"), 0)),
        "target_mip_jobs": int(number(
            result.get("external_gini_tree_partial_mip_optimize_count"), 0)),
        "terminal_mip_jobs": int(number(
            result.get("external_gini_tree_terminal_mip_optimize_count"), 0)),
        "peak_memory_gb": number(result.get("external_gini_tree_peak_memory_gb"), 0.0),
        "lower_bound": lower, "verified_upper_bound": upper,
        "relative_gap": rel_gap,
        "failure_reason": result.get("external_gini_tree_failure_reason",
                                     result.get("gurobi_failure_reason", "none")),
    }


def completed_records(rows: list[dict[str, str]], audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = {row["row_id"] for row in audit if truth(row["complete"])}
    records = []
    for row in rows:
        if row["row_id"] not in valid:
            continue
        directory = run_dir(row)
        marker = load_json(directory / "completion_marker.json")
        result = load_json(directory / "result.json")
        records.append({**row, **metrics(result, marker), "directory": directory})
    return records


def parent_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (row["stage"], row["instance"], row["K0"], row["parent_id"])


def counterfactual_tables(records: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    cf = [row for row in records if "counterfactual" in row["stage"]]
    groups: dict[tuple[str, str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    validity = []
    for row in cf:
        audit = load_json(row["directory"] / "counterfactual_validity.json")
        state = load_json(row["directory"] / "parent_state.json")
        groups[parent_key(row)][row["arm"]] = row
        validity.append({
            "row_id": row["row_id"], "stage": row["stage"],
            "instance": row["instance"], "parent_id": row["parent_id"],
            "arm": row["arm"], "counterfactual_valid": audit["counterfactual_valid"],
            "split_count": audit["split_count"],
            "actual_split_events": audit["actual_split_events"],
            "child_count": audit["child_count"],
            "exact_two_child_union": audit["exact_two_child_union"],
            "point_certified": audit["point_certified"],
            "parent_state_sha256": sha256(row["directory"] / "parent_state.json"),
            "parent_canonical_model_sha256": state["parent_canonical_model_sha256"],
        })
    pairs = []
    parents = []
    required_arms = {"retain", "midpoint-split", "pmm-split", "fpmm-split"}
    for key, arms in sorted(groups.items()):
        stage, instance, k0, parent_id = key
        base = arms.get("retain")
        mid = arms.get("midpoint-split")
        state = load_json(base["directory"] / "parent_state.json") if base else {}
        model_hashes = set()
        for arm in arms.values():
            model_hashes.add(load_json(arm["directory"] / "parent_state.json").get(
                "parent_canonical_model_sha256", ""))
        parents.append({
            "stage": stage, "selection_use": base["selection_use"] if base else "",
            "instance": instance, "K0": k0, "parent_id": parent_id,
            "parent_lower": base["parent_lower"] if base else "",
            "parent_upper": base["parent_upper"] if base else "",
            "parent_canonical_model_sha256": state.get("parent_canonical_model_sha256", ""),
            "matched_parent_identity": len(model_hashes) == 1 and bool(next(iter(model_hashes), "")),
            "old_c6_action": state.get("old_c6_action", ""),
            "Gamma_sum": state.get("Gamma_sum", ""), "D_R43": state.get("D_R43", ""),
            "verified_incumbent": state.get("verified_incumbent", ""),
            "all_four_arms_present": required_arms <= set(arms),
        })
        label = "inconclusive"
        gain: float | str = ""
        if base and mid and base["local_parent_exact"] and mid["local_parent_exact"]:
            gain = (base["work"] - mid["work"]) / max(base["work"], 1e-12)
            if mid["work"] <= 0.85 * base["work"]:
                label = "beneficial"
            elif mid["work"] >= 1.25 * base["work"]:
                label = "harmful"
            else:
                label = "neutral"
        pairs.append({
            "stage": stage, "selection_use": base["selection_use"] if base else "",
            "instance": instance, "K0": k0, "parent_id": parent_id,
            "matched_parent_identity": len(model_hashes) == 1,
            "retain_work": base["work"] if base else "",
            "midpoint_work": mid["work"] if mid else "",
            "retain_seconds": base["seconds"] if base else "",
            "midpoint_seconds": mid["seconds"] if mid else "",
            "pmm_seconds": arms.get("pmm-split", {}).get("seconds", ""),
            "fpmm_seconds": arms.get("fpmm-split", {}).get("seconds", ""),
            "retain_exact": base["local_parent_exact"] if base else False,
            "midpoint_exact": mid["local_parent_exact"] if mid else False,
            "midpoint_honest_cap": mid["honest_cap"] if mid else False,
            "relative_split_gain": gain, "label": label,
            "pmm_work": arms.get("pmm-split", {}).get("work", ""),
            "fpmm_work": arms.get("fpmm-split", {}).get("work", ""),
            "pmm_exact": arms.get("pmm-split", {}).get("local_parent_exact", False),
            "fpmm_exact": arms.get("fpmm-split", {}).get("local_parent_exact", False),
            "pmm_honest_cap": arms.get("pmm-split", {}).get("honest_cap", False),
            "fpmm_honest_cap": arms.get("fpmm-split", {}).get("honest_cap", False),
            "midpoint_run_directory": (arms.get("midpoint-split", {}).get(
                "run_directory", "")),
            "pmm_run_directory": arms.get("pmm-split", {}).get("run_directory", ""),
            "fpmm_run_directory": arms.get("fpmm-split", {}).get("run_directory", ""),
        })
    dev = [row for row in pairs if row["stage"] == "true_counterfactual_development"]
    counts = Counter(row["label"] for row in dev)
    gate = {
        "development_parent_count": len(dev),
        "post_selection_parent_count": len(pairs) - len(dev),
        "beneficial_count": counts["beneficial"], "harmful_count": counts["harmful"],
        "neutral_count": counts["neutral"], "inconclusive_count": counts["inconclusive"],
        "all_counterfactual_rows_valid": all(truth(row["counterfactual_valid"])
                                              for row in validity),
        "all_parent_identities_matched": all(truth(row["matched_parent_identity"])
                                               for row in parents),
        "all_four_arms_present": all(truth(row["all_four_arms_present"])
                                      for row in parents),
    }
    gate["pass"] = all((gate["all_counterfactual_rows_valid"],
                         gate["all_parent_identities_matched"],
                         gate["all_four_arms_present"]))
    return parents, pairs, validity, gate


def decision_for(parent: dict[str, Any], rule: str) -> bool:
    old_split = str(parent["old_c6_action"]).lower() == "split"
    gamma = number(parent["Gamma_sum"], -math.inf)
    d43 = number(parent["D_R43"], -math.inf)
    return {"c6": old_split, "gamma-veto": old_split and gamma >= 0.012,
            "d-r43": d43 >= 0.10, "no-adaptive": True}[rule]


def timing_regret(parents: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pair_by_key = {(row["stage"], row["instance"], row["K0"], row["parent_id"]): row
                   for row in pairs}
    rows = []
    for rule in ("c6", "gamma-veto", "d-r43", "no-adaptive"):
        split_count = beneficial_split = harmful_split = false_split = false_retain = 0
        regrets, weighted = [], []
        signatures = []
        for parent in parents:
            if parent["stage"] != "true_counterfactual_development":
                continue
            pair = pair_by_key[(parent["stage"], parent["instance"],
                                parent["K0"], parent["parent_id"])]
            split = decision_for(parent, rule)
            signatures.append(f"{parent['instance']}:{parent['parent_id']}={int(split)}")
            split_count += int(split)
            beneficial_split += int(split and pair["label"] == "beneficial")
            harmful_split += int(split and pair["label"] == "harmful")
            false_split += int(split and pair["label"] == "harmful")
            false_retain += int(not split and pair["label"] == "beneficial")
            if pair["label"] != "inconclusive":
                chosen = number(pair["midpoint_work"] if split else pair["retain_work"])
                oracle = min(number(pair["retain_work"]), number(pair["midpoint_work"]))
                regret = max(0.0, chosen - oracle) / max(oracle, 1e-12)
                weight = max(oracle, 1.0)
                regrets.append(regret)
                weighted.append((regret, weight))
        major = next((p for p in parents if p["stage"] == "true_counterfactual_development"
                      and p["instance"] == MAJOR_HARMFUL_INSTANCE
                      and p["parent_id"] == MAJOR_HARMFUL_PARENT), None)
        rows.append({
            "rule": rule, "split_count": split_count,
            "retain_count": len(signatures) - split_count,
            "true_beneficial_split_count": beneficial_split,
            "true_harmful_split_count": harmful_split,
            "false_split_count": false_split, "false_retain_count": false_retain,
            "mean_oracle_regret": sum(regrets) / len(regrets) if regrets else "",
            "max_oracle_regret": max(regrets) if regrets else "",
            "weighted_oracle_regret": (sum(r * w for r, w in weighted) /
                                        sum(w for _, w in weighted)) if weighted else "",
            "major_harmful_retained": bool(major and not decision_for(major, rule)),
            "decision_signature": "|".join(signatures),
        })
    gamma = next(row for row in rows if row["rule"] == "gamma-veto")
    return rows, gamma


def point_arm_details(relative_directory: str) -> dict[str, Any]:
    directory = ROUND / relative_directory
    choices = [row for row in read_csv(directory / "split_point_choice_ledger.csv")
               if row.get("parent_id") == "L0"]
    choice = choices[0] if choices else {}
    children = sorted((row for row in read_csv(directory / "interval_coverage_ledger.csv")
                       if row.get("parent_id") == "L0" and
                       row.get("child_index") in {"0", "1"}),
                      key=lambda row: row["child_index"])
    queries = [row for row in read_csv(directory / "parametric_segment_ledger.csv")
               if row.get("parent_id") == "L0"]
    checkpoint = checkpoint_map(directory)[3600]
    result = load_json(directory / "result.json")
    return {
        "selected_point": choice.get("selected_point", ""),
        "midpoint": choice.get("midpoint", ""),
        "point_certified": choice.get("certified", ""),
        "point_reason": choice.get("reason", ""),
        "query_count": len({row.get("query_index", "") for row in queries}),
        "child_0_width": (number(children[0]["gamma_U"]) - number(children[0]["gamma_L"]))
            if len(children) == 2 else "",
        "child_1_width": (number(children[1]["gamma_U"]) - number(children[1]["gamma_L"]))
            if len(children) == 2 else "",
        "child_0_lp_bound": children[0].get("lp_bound", "") if len(children) == 2 else "",
        "child_1_lp_bound": children[1].get("lp_bound", "") if len(children) == 2 else "",
        "target_attainment_count": result.get(
            "external_gini_tree_next_leaf_target_reached_count", 0),
        "GI_3600": checkpoint["normalized_gap_integral"],
        "final_gap": checkpoint["relative_gap"],
    }


def point_tables(parents: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parent_by_key = {(row["stage"], row["instance"], row["K0"], row["parent_id"]): row
                     for row in parents}
    output = []
    for pair in pairs:
        if pair["stage"] != "true_counterfactual_development":
            continue
        parent = parent_by_key[(pair["stage"], pair["instance"], pair["K0"], pair["parent_id"])]
        if not decision_for(parent, "gamma-veto"):
            continue
        values = {name: number(pair[field]) for name, field in
                  (("midpoint", "midpoint_work"), ("pmm", "pmm_work"),
                   ("fpmm", "fpmm_work"))}
        finite = {key: value for key, value in values.items() if math.isfinite(value)}
        all_exact = all(truth(pair[field]) for field in
                        ("midpoint_exact", "pmm_exact", "fpmm_exact"))
        best = min(finite, key=finite.get) if len(finite) == 3 and all_exact else "inconclusive"
        details = {arm: point_arm_details(pair[f"{arm}_run_directory"])
                   for arm in ("midpoint", "pmm", "fpmm")}
        output.append({
            "instance": pair["instance"], "parent_id": pair["parent_id"],
            "retain_work": pair["retain_work"], **{f"{key}_work": value for key, value in values.items()},
            "retain_seconds": pair["retain_seconds"],
            "midpoint_seconds": pair["midpoint_seconds"],
            "pmm_seconds": pair["pmm_seconds"],
            "fpmm_seconds": pair["fpmm_seconds"],
            "best_split_point": best,
            "evidence_conclusive": all_exact,
            "midpoint_exact": pair["midpoint_exact"],
            "pmm_exact": pair["pmm_exact"], "fpmm_exact": pair["fpmm_exact"],
            **{f"{arm}_{field}": value for arm, detail in details.items()
               for field, value in detail.items()},
            "pmm_improves_midpoint_15pct": (all_exact and
                                             values["pmm"] <= 0.85 * values["midpoint"]),
            "fpmm_improves_midpoint_15pct": (all_exact and
                                              values["fpmm"] <= 0.85 * values["midpoint"]),
        })
    gate = {
        "required_true_gamma_split_parents": len(output),
        "all_required_point_arms_present": all(math.isfinite(number(row[f"{arm}_work"]))
                                                for row in output
                                                for arm in ("midpoint", "pmm", "fpmm")),
        "all_point_comparisons_conclusive": all(truth(row["evidence_conclusive"])
                                                 for row in output),
        "pmm_material_improvement_count": sum(truth(row["pmm_improves_midpoint_15pct"])
                                               for row in output),
        "fpmm_material_improvement_count": sum(truth(row["fpmm_improves_midpoint_15pct"])
                                                for row in output),
        "live_basis_continuation_used": False,
        "method": "monotone-root PMM/FPMM",
    }
    gate["pass"] = gate["all_required_point_arms_present"]
    return output, gate


def checkpoint_map(directory: Path) -> dict[int, dict[str, str]]:
    path = directory / "common_horizon_trace.csv"
    return {int(float(row["horizon_seconds"])): row for row in read_csv(path)}


def trace_resource_at(directory: Path, horizon: int,
                      final_work: float, final_nodes: float) -> tuple[Any, Any]:
    trace = read_csv(directory / "normalized_global_bound_trace.csv")
    eligible = [row for row in trace
                if number(row.get("process_elapsed_seconds"), math.inf) <= horizon]
    point = eligible[-1] if eligible else (trace[0] if trace else {})
    work = number(point.get("work"))
    nodes = number(point.get("nodes"))
    return (work if math.isfinite(work) else final_work,
            nodes if math.isfinite(nodes) else final_nodes)


def full_and_complex(records: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    full, horizons = [], []
    for row in records:
        if "counterfactual" in row["stage"]:
            continue
        plain = {key: value for key, value in row.items() if key != "directory"}
        full.append(plain)
        for horizon, point in checkpoint_map(row["directory"]).items():
            horizon_work, horizon_nodes = trace_resource_at(
                row["directory"], horizon, row["work"], row["nodes"])
            horizons.append({
                "row_id": row["row_id"], "stage": row["stage"],
                "instance": row["instance"], "arm": row["arm"],
                "horizon_seconds": horizon, "lower_bound": point["lower_bound"],
                "verified_upper_bound": point["verified_upper_bound"],
                "relative_gap": point["relative_gap"],
                "normalized_gap_integral": point["normalized_gap_integral"],
                "strict_closed_before_horizon": point["strict_closed_before_horizon"],
                "certificate_count": int(truth(point["strict_closed_before_horizon"])),
                "work": horizon_work, "nodes": horizon_nodes,
                "peak_memory_gb": row["peak_memory_gb"],
                "split_count": row["split_count"],
            })
    complex_rows = [row for row in records if row["stage"].startswith("complex_")]
    complex_horizons = [row for row in horizons if row["stage"].startswith("complex_")]
    by_instance_horizon: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in complex_horizons:
        if row["arm"] in {"pgrb", "c6", "gamma-veto", "no-adaptive"}:
            by_instance_horizon[(row["instance"], row["horizon_seconds"])][row["arm"]] = row
    retention = []
    for (instance, horizon), arms in sorted(by_instance_horizon.items()):
        if not all(arm in arms for arm in ("pgrb", "c6", "gamma-veto", "no-adaptive")):
            continue
        gi_p = number(arms["pgrb"]["normalized_gap_integral"])
        gi_c = number(arms["c6"]["normalized_gap_integral"])
        denominator = max(gi_p - gi_c, 1e-12)
        for arm in ("gamma-veto", "no-adaptive"):
            gi_a = number(arms[arm]["normalized_gap_integral"])
            retention.append({
                "instance": instance, "horizon_seconds": horizon, "arm": arm,
                "GI_pgrb": gi_p, "GI_c6": gi_c, "GI_arm": gi_a,
                "c6_advantage_over_pgrb": gi_c < gi_p,
                "retention": (gi_p - gi_a) / denominator,
                "arm_advantage_over_pgrb": gi_a < gi_p,
            })
    mandatory_count = sum(row["stage"].startswith("complex_mandatory_")
                          for row in complex_rows)
    gate = {
        "mandatory_required": 48, "mandatory_completed": mandatory_count,
        "secondary_required": 6,
        "secondary_completed": sum(row["stage"].startswith("complex_secondary_")
                                   for row in complex_rows),
        "false_certificate_count": 0,
        "gamma_material_advantage_supported": False,
    }
    gamma_3600 = [row for row in retention if row["arm"] == "gamma-veto" and
                  row["horizon_seconds"] == 3600 and
                  truth(row["c6_advantage_over_pgrb"])]
    gate["gamma_material_advantage_supported"] = bool(gamma_3600) and all(
        truth(row["arm_advantage_over_pgrb"]) and number(row["retention"]) >= 0.5
        for row in gamma_3600)
    gate["pass"] = gate["mandatory_completed"] == 48
    return full, horizons, retention, gate


def certificate_rows(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    rows, false_count = [], 0
    for row in records:
        ledger = read_csv(row["directory"] / "certificate_ledger.csv")[0]
        result = load_json(row["directory"] / "result.json")
        result_strict = truth(result.get("strict_certified_original_problem"))
        counterfactual_scope_violation = ("counterfactual" in row["stage"] and
                                          row["strict_certificate"])
        marker_result_mismatch = row["strict_certificate"] != result_strict
        lower, upper = number(row["lower_bound"]), number(row["verified_upper_bound"])
        invalid_bounds = (not math.isfinite(lower) or not math.isfinite(upper) or
                          lower > upper + CERT_EPS)
        false = (truth(ledger.get("false_certificate")) or
                 counterfactual_scope_violation or marker_result_mismatch or
                 invalid_bounds)
        false_count += int(false)
        rows.append({
            "row_id": row["row_id"], "stage": row["stage"], "arm": row["arm"],
            "strict_certificate": row["strict_certificate"],
            "local_parent_exact": row["local_parent_exact"],
            "honest_cap": row["honest_cap"],
            "certificate_class": ledger.get("certificate_class", ""),
            "rejection_reason": ledger.get("rejection_reason", ""),
            "false_certificate": false,
            "counterfactual_scope_violation": counterfactual_scope_violation,
            "marker_result_mismatch": marker_result_mismatch,
            "invalid_bounds": invalid_bounds,
        })
    return rows, false_count


def inventory(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(set(paths)):
        if path.is_file():
            rows.append({"path": path.relative_to(ROOT).as_posix(),
                         "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    return rows


def pgrb_reference(instance: str) -> dict[str, Any] | None:
    path = (ROOT / "results" / "gf_small_hard_light_round39" / "runs" /
            f"primary__{instance}__p_grb" / "result.json")
    return load_json(path) if path.is_file() else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = read_csv(MATRIX)
    matrix_audit, matrix_gate = audit_matrix(matrix)
    write_csv(OUT / "matrix_completion_audit.csv", matrix_audit)
    if not matrix_gate["pass"]:
        incomplete = {
            "round45_completion_status": "incomplete",
            "timing_classification": "round45_completion_incomplete",
            "point_classification": "round45_completion_incomplete",
            "final_algorithm_classification": "round45_completion_incomplete",
            "scale_qualification": "complex_incomplete",
            "matrix_gate": matrix_gate,
        }
        write_json(OUT / "counterfactual_gate_audit.json",
                   {"pass": False, "reason": "matrix_incomplete"})
        write_json(OUT / "point_gate_audit.json",
                   {"pass": False, "reason": "matrix_incomplete"})
        write_json(OUT / "complex_gate_audit.json",
                   {"pass": False, "reason": "matrix_incomplete"})
        write_json(OUT / "classification_gate_audit.json", incomplete)
        write_json(OUT / "final_decision.json", incomplete)
        print(json.dumps(incomplete, sort_keys=True))
        return 2

    records = completed_records(matrix, matrix_audit)
    parents, pairs, validity, cf_gate = counterfactual_tables(records)
    timing_rows, gamma = timing_regret(parents, pairs)
    point_rows, point_gate = point_tables(parents, pairs)
    full, horizons, retention, complex_gate = full_and_complex(records)
    certs, false_certificates = certificate_rows(records)
    complex_gate["false_certificate_count"] = false_certificates

    write_csv(OUT / "true_counterfactual_parent_manifest.csv", parents)
    write_csv(OUT / "true_counterfactual_pair_summary.csv", pairs)
    write_csv(OUT / "true_retain_results.csv", [row for row in records if row["arm"] == "retain"])
    write_csv(OUT / "true_midpoint_results.csv", [row for row in records if row["arm"] == "midpoint-split"])
    for label, name in (("beneficial", "true_beneficial_leaves.csv"),
                        ("harmful", "true_harmful_leaves.csv"),
                        ("neutral", "true_neutral_leaves.csv"),
                        ("inconclusive", "inconclusive_counterfactual_leaves.csv")):
        write_csv(OUT / name, [row for row in pairs if row["label"] == label])
    write_csv(OUT / "counterfactual_validity_audit.csv", validity)
    write_csv(OUT / "timing_oracle_regret.csv", timing_rows)
    write_csv(OUT / "point_oracle_regret.csv", point_rows)
    write_csv(OUT / "full_run_matrix_results.csv", full)
    write_csv(OUT / "common_horizon_complex_results.csv",
              [row for row in horizons if row["stage"].startswith("complex_")])
    write_csv(OUT / "c6_advantage_retention.csv", retention)
    write_csv(OUT / "k1_vs_k4_completion.csv",
              [row for row in full if row["stage"] == "k1_k4_completion"])
    write_csv(OUT / "certificate_audit.csv", certs)
    write_json(OUT / "counterfactual_gate_audit.json", cf_gate)
    write_json(OUT / "point_gate_audit.json", point_gate)
    write_json(OUT / "complex_gate_audit.json", complex_gate)

    small_reruns = [row for row in records if row["stage"].startswith("small_panel_rerun_")]
    small_audit = []
    for row in small_reruns:
        reference = pgrb_reference(row["instance"])
        p_work = number((reference or {}).get("gurobi_work"), math.nan)
        p_time = number((reference or {}).get("final_process_wall_time_seconds"), math.nan)
        work_ratio = row["work"] / max(p_work, 1e-12) if math.isfinite(p_work) else math.nan
        time_ratio = row["seconds"] / max(p_time, 1e-12) if math.isfinite(p_time) else math.nan
        severe = (math.isfinite(work_ratio) and math.isfinite(time_ratio) and
                  work_ratio > 1.5 and time_ratio > 1.5 and
                  (row["seconds"] - p_time > 60 or row["work"] - p_work > 100))
        small_audit.append({
            "stage": row["stage"], "instance": row["instance"],
            "candidate_work": row["work"], "candidate_seconds": row["seconds"],
            "pgrb_work": p_work, "pgrb_seconds": p_time,
            "work_ratio_over_pgrb": work_ratio, "time_ratio_over_pgrb": time_ratio,
            "severe_pgrb_regression": severe,
            "candidate_terminal_valid": row["strict_certificate"] or row["honest_cap"],
        })
    write_csv(OUT / "small_panel_rerun_audit.csv", small_audit)
    small_gate = (len(small_reruns) == 19 and
                  all(row["strict_certificate"] or row["honest_cap"]
                      for row in small_reruns) and
                  all(math.isfinite(number(row["pgrb_work"])) for row in small_audit) and
                  not any(truth(row["severe_pgrb_regression"]) for row in small_audit
                          if row["stage"] != "small_panel_rerun_holdout"))
    beneficial = cf_gate["beneficial_count"] > 0
    gamma_distinguishes = (gamma["true_beneficial_split_count"] > 0 and
                           gamma["major_harmful_retained"] and
                           gamma["false_split_count"] == 0 and
                           gamma["split_count"] > 0 and gamma["retain_count"] > 0)
    if not beneficial:
        timing_class = "no_beneficial_recursive_split_evidence"
    elif gamma_distinguishes and small_gate and complex_gate["pass"] and \
            complex_gate["gamma_material_advantage_supported"] and false_certificates == 0:
        timing_class = "validated_adaptive_timing"
    elif gamma_distinguishes and small_gate and complex_gate["pass"]:
        timing_class = "adaptive_timing_small_only"
    else:
        timing_class = "bounded_negative_timing_mechanism"

    point_improved = (point_gate["pmm_material_improvement_count"] +
                      point_gate["fpmm_material_improvement_count"] > 0)
    eligible_point_keys = {(row["instance"], row["parent_id"])
                           for row in pairs
                           if row["stage"] == "true_counterfactual_development" and
                           row["label"] in {"beneficial", "neutral"}}
    midpoint_negative_gate = (
        len(point_rows) >= 3 and
        len({row["instance"] for row in point_rows}) >= 2 and
        any((row["instance"], row["parent_id"]) in eligible_point_keys
            for row in point_rows) and
        point_gate["all_required_point_arms_present"] and
        point_gate["all_point_comparisons_conclusive"])
    point_gate["midpoint_not_improved_eligibility"] = midpoint_negative_gate
    write_json(OUT / "point_gate_audit.json", point_gate)
    if not point_rows or not point_gate["all_point_comparisons_conclusive"]:
        point_class = "parametric_point_inconclusive_insufficient_true_split_evidence"
    elif point_improved and timing_class == "validated_adaptive_timing":
        point_class = "validated_parametric_split_point"
    elif point_improved:
        point_class = "parametric_point_small_only"
    elif midpoint_negative_gate and all(row["best_split_point"] == "midpoint"
                                        for row in point_rows):
        point_class = "midpoint_not_improved"
    elif not midpoint_negative_gate:
        point_class = "parametric_point_inconclusive_insufficient_true_split_evidence"
    else:
        point_class = "bounded_negative_parametric_point"

    if timing_class == "validated_adaptive_timing":
        final_class = ("validated_k4_adaptive_parametric" if point_improved else
                       "validated_k4_adaptive_midpoint")
    elif timing_class == "adaptive_timing_small_only":
        final_class = "adaptive_k4_small_material_candidate"
    elif timing_class == "no_beneficial_recursive_split_evidence":
        final_class = "no_beneficial_recursive_split_evidence"
    else:
        final_class = "bounded_systematic_negative_result"
    panels = {row["stage"].split("complex_mandatory_")[-1]
              for row in records if row["stage"].startswith("complex_mandatory_")}
    scale = ("v20_v50_supported" if complex_gate["gamma_material_advantage_supported"] else
             "complex_mixed_complete" if len(panels) == 4 else "complex_negative_complete")
    decision = {
        "round45_completion_status": "complete",
        "timing_classification": timing_class,
        "point_classification": point_class,
        "final_algorithm_classification": final_class,
        "scale_qualification": scale,
        "matrix_gate": matrix_gate, "counterfactual_gate": cf_gate,
        "point_gate": point_gate, "complex_gate": complex_gate,
        "small_panel_rerun_gate": small_gate,
        "gamma_veto_false_split_count": gamma["false_split_count"],
        "gamma_veto_false_retain_count": gamma["false_retain_count"],
        "false_certificate_count": false_certificates,
    }
    write_json(OUT / "classification_gate_audit.json", decision)
    write_json(OUT / "final_decision.json", decision)

    def arm_line(instance: str, arms: tuple[str, ...]) -> str:
        values = {row["arm"].lower(): row for row in records
                  if row["stage"] == "small_sentinel" and row["instance"] == instance}
        parts = []
        for arm in arms:
            row = values.get(arm.lower())
            parts.append(f"{arm}: Work {row['work']:.6g}, {row['seconds']:.3f} s, "
                         f"{'exact' if row['strict_certificate'] else 'capped'}"
                         if row else f"{arm}: missing")
        return "; ".join(parts)

    horizon_summary = []
    for horizon in (300, 1200, 3600):
        for arm in ("pgrb", "c6", "gamma-veto", "no-adaptive"):
            selected = [row for row in horizons
                        if row["stage"].startswith("complex_mandatory_") and
                        row["horizon_seconds"] == horizon and row["arm"] == arm]
            mean_gi = (sum(number(row["normalized_gap_integral"]) for row in selected) /
                       len(selected)) if selected else math.nan
            certificates = sum(int(row["certificate_count"]) for row in selected)
            horizon_summary.append(f"{horizon}s {arm}: {certificates}/{len(selected)} "
                                   f"certificates, mean GI {mean_gi:.6g}")
    timing_by_rule = {row["rule"]: row for row in timing_rows}
    no_adaptive = timing_by_rule["no-adaptive"]
    d43 = timing_by_rule["d-r43"]
    k_rows = [row for row in records if row["stage"] == "k1_k4_completion"]
    k1_exact = sum(row["strict_certificate"] for row in k_rows if row["arm"] == "K1-gamma-veto")
    k4_exact = sum(row["strict_certificate"] for row in k_rows if row["arm"] == "K4-gamma-veto")
    complex_records = [row for row in records if row["stage"].startswith("complex_")]
    exact_count = sum(row["strict_certificate"] for row in records)
    local_exact_count = sum(row["local_parent_exact"] for row in records)
    cap_count = sum(row["honest_cap"] for row in records)
    beneficial_keys = {(row["instance"], row["parent_id"])
                       for row in pairs if row["stage"] == "true_counterfactual_development"
                       and row["label"] == "beneficial"}
    beneficial_point_improvements = [row for row in point_rows
                                     if (row["instance"], row["parent_id"]) in beneficial_keys and
                                     (truth(row["pmm_improves_midpoint_15pct"]) or
                                      truth(row["fpmm_improves_midpoint_15pct"]))]
    retention_3600 = [row for row in retention if row["horizon_seconds"] == 3600 and
                      row["arm"] == "gamma-veto"]
    retention_text = ", ".join(
        f"{row['instance']}={number(row['retention']):.4g}" for row in retention_3600)
    report = f"""# Round 45 completion report

Status: **{decision['round45_completion_status']}**

- Timing classification: `{timing_class}`
- Point classification: `{point_class}`
- Final algorithm classification: `{final_class}`
- Scale qualification: `{scale}`
- Required runtime rows: {matrix_gate['completed_rows']}/{matrix_gate['required_rows']}
- Fresh true counterfactual parents: {cf_gate['development_parent_count']} development and {cf_gate['post_selection_parent_count']} post-selection
- Development labels: {cf_gate['beneficial_count']} beneficial, {cf_gate['harmful_count']} harmful, {cf_gate['neutral_count']} neutral, {cf_gate['inconclusive_count']} inconclusive
- Gamma-veto false splits / false retains: {gamma['false_split_count']} / {gamma['false_retain_count']}
- False certificates: {false_certificates}
- Complex mandatory rows: {complex_gate['mandatory_completed']}/48

## Required questions

1. **Prior label:** withdrawn. The old strong-control L3 trajectory had zero
   full-instance splits and is not a verified split counterfactual.
2. **Fresh matched evidence:** {cf_gate['development_parent_count']} development
   and {cf_gate['post_selection_parent_count']} post-selection parents, each with
   retain, midpoint, PMM, and FPMM arms.
3. **Development labels:** {cf_gate['beneficial_count']} beneficial,
   {cf_gate['harmful_count']} harmful, {cf_gate['neutral_count']} neutral, and
   {cf_gate['inconclusive_count']} inconclusive.
4. **Gamma-veto beneficial action:** {gamma['true_beneficial_split_count']} true
   beneficial parents split.
5. **Major harmful action:** retained = {gamma['major_harmful_retained']}.
6. **Corrected D_R43:** false splits {d43['false_split_count']}, false retains
   {d43['false_retain_count']}, weighted oracle regret
   {number(d43['weighted_oracle_regret']):.6g}; gamma-veto weighted regret
   {number(gamma['weighted_oracle_regret']):.6g}.
7. **Gamma-veto versus no-adaptive on useful splits:** gamma weighted regret
   {number(gamma['weighted_oracle_regret']):.6g} versus no-adaptive
   {number(no_adaptive['weighted_oracle_regret']):.6g}.
8. **Point coverage:** all gamma-veto development split parents have all three
   split-point arms = {point_gate['all_required_point_arms_present']}.
9. **Parametric improvement on beneficial parents:**
   {len(beneficial_point_improvements)} material 15% improvements over midpoint.
10. **Implementation tested:** monotone-root PMM/FPMM only; live basis
    continuation was not used.
11. **Frozen complex matrix:** {complex_gate['mandatory_completed']}/48 mandatory
    rows and {complex_gate['secondary_completed']}/6 D_R43 rows completed.
12. **Cap integrity:** {cap_count} honest caps; every capped marker passed the
    3570-second minimum finalization-tolerance check.
13. **Common horizons:** {'; '.join(horizon_summary)}.
14. **C6 advantage retention at 3600 s:** {retention_text or 'no estimable rows'}.
15. **K1 beyond strong control:** {len(k_rows)}/18 rows completed; K1 exact
    {k1_exact}/9 and K4 exact {k4_exact}/9.
16. **Certificate scope:** {exact_count} strict original-problem certificates,
    {local_exact_count} exact restricted-parent certificates, and {cap_count}
    honest capped rows; false certificates = {false_certificates}.
17. **Timing conclusion:** `{timing_class}`.
18. **Point conclusion:** `{point_class}`.
19. **What remains unproven:** the classification and scale qualification above
    delimit the evidence. Counterfactual exactness does not certify the original
    problem, and the point study does not claim live-basis continuation.

## Contemporaneous sentinels

- Major harmful witness: {arm_line(MAJOR_HARMFUL_INSTANCE, ('pgrb', 'c6', 'gamma-veto', 'no-adaptive'))}
- Strong K4 control: {arm_line('round39_small_hard_V12_M3_Q30_slot08_seed1288546114', ('pgrb', 'c6', 'gamma-veto', 'no-adaptive'))}

All claims are derived from the sealed completion matrix and its gate audits.
"""
    write_md(OUT / "final_report.md", report)
    write_md(OUT / "reproduction_commands.md", """# Reproduction commands

```powershell
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round45_completion.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\finalize_round45.py
D:\\msys64\\ucrt64\\bin\\python.exe tests\\round45_completion_protocol_tests.py
```

The runner resumes sealed rows and executes remaining official Gurobi rows
strictly sequentially.
""")
    generated = [path for path in OUT.iterdir()
                 if path.is_file() and
                 path.name != "final_evidence_inventory.csv"]
    write_csv(OUT / "final_evidence_inventory.csv", inventory(generated))
    print(json.dumps(decision, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
