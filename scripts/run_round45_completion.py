#!/usr/bin/env python3
"""Execute the frozen Round 45 completion matrix strictly sequentially."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from typing import Any

import round43_common as round43
import round44_common as round44
import round45_experiment as round45


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
COMPLETION = OUT / "completion"
MATRIX = COMPLETION / "required_run_matrix.csv"
RUNS = COMPLETION / "runs"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND45_COMPLETION_EXE",
    str(ROOT / "build_round45_completion" / "ExactEBRP.exe")))
CERT_EPS = 1e-7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


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


def replace(args: list[str], option: str, value: Any) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    if option in args:
        args[args.index(option) + 1] = rendered
    else:
        args.extend((option, rendered))


def remove(args: list[str], option: str) -> None:
    if option in args:
        index = args.index(option)
        del args[index:index + 2]


def inventory() -> dict[str, dict[str, Any]]:
    return round45.inventory()


def external_item(item: dict[str, Any]) -> bool:
    return item["instance_id"] not in round44.inventory()


def bind_external(command: list[str], item: dict[str, Any],
                  input_path: Path) -> None:
    replace(command, "--input", input_path)
    if external_item(item):
        replace(command, "--T", 3600.0)
        remove(command, "--round24-expected-gurobi-model-fingerprint")


def bind_executable(command: list[str]) -> None:
    command[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        replace(command, option, executable_hash)


def tailored_command(row: dict[str, str], item: dict[str, Any],
                     run_dir: Path) -> list[str]:
    cap = float(row["process_cap_seconds"])
    command_item = item
    if external_item(item):
        command_item = dict(next(iter(round44.inventory().values())))
    arm = row["arm"]
    if arm == "c6":
        command = round44.fair_candidate_command(
            command_item, run_dir, cap, execution="off",
            lookahead="frontier-d2", injection="all", scope="parent",
            family="no-adaptive", rho_f=0.5, rho_m=0.0, rho_h=0.0)
        replace(command, "--round43-envelope-refinement", "off")
        replace(command, "--round44-envelope-tail-repair", "off")
        replace(command, "--round45-adaptive-parametric-partition", "off")
    else:
        timing = row["timing_rule"]
        command = round44.fair_candidate_command(
            command_item, run_dir, cap, execution="algorithm",
            lookahead="frontier-d2", injection="all", scope="parent",
            family="no-adaptive", rho_f=0.5, rho_m=0.0, rho_h=0.0)
        replace(command, "--round43-envelope-refinement", "off")
        replace(command, "--round44-envelope-tail-repair", "off")
        replace(command, "--round45-adaptive-parametric-partition", "algorithm")
        replace(command, "--round45-initial-k0", int(row["K0"]))
        replace(command, "--round45-timing-rule", timing)
        replace(command, "--round45-rho-gamma", 0.012)
        replace(command, "--round45-point-rule", row["point_rule"])
        replace(command, "--round45-minimum-child-width", 1e-4)
        replace(command, "--round45-counterfactual-mode", "off")
    replace(command, "--process-wall-time-limit", cap)
    replace(command, "--time-limit", cap)
    bind_external(command, item, ROOT / row["input_path"])
    bind_executable(command)
    return command


def pgrb_command(row: dict[str, str], item: dict[str, Any],
                  run_dir: Path) -> list[str]:
    cap = float(row["process_cap_seconds"])
    command_item = item
    if external_item(item):
        command_item = dict(next(iter(round44.inventory().values())))
    command = round43.fair_pgrb_command(command_item, run_dir, cap)
    replace(command, "--process-wall-time-limit", cap)
    replace(command, "--time-limit", cap)
    bind_external(command, item, ROOT / row["input_path"])
    bind_executable(command)
    return command


def counterfactual_command(row: dict[str, str], item: dict[str, Any],
                           run_dir: Path) -> list[str]:
    command = tailored_command({**row, "arm": "gamma-veto",
                                "K0": "1", "timing_rule": "gamma-veto",
                                "point_rule": ("midpoint" if row["point_rule"] ==
                                               "retain" else row["point_rule"])},
                               item, run_dir)
    remove(command, "--round24-expected-gurobi-model-fingerprint")
    replace(command, "--gini-floor", row["parent_lower"])
    replace(command, "--gini-cap", row["parent_upper"])
    mode = row["point_rule"]
    replace(command, "--round45-counterfactual-mode", mode)
    return command


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    if "counterfactual" in row["stage"]:
        return counterfactual_command(row, item, run_dir)
    if row["arm"] == "pgrb":
        return pgrb_command(row, item, run_dir)
    return tailored_command(row, item, run_dir)


def process_offset(run_dir: Path) -> float:
    path = run_dir / "process_phases.csv"
    if not path.is_file():
        return 0.0
    for row in read_csv(path):
        if row.get("event") in {"plain_gurobi_optimize_launch",
                                 "exact_tree_initialization"}:
            try:
                return float(row["process_seconds"])
            except (KeyError, ValueError):
                return 0.0
    return 0.0


def normalize_trace(run_dir: Path, arm: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    external = run_dir / "external" / "global_bound_trace.csv"
    rows: list[dict[str, Any]] = []
    if external.is_file():
        for source in read_csv(external):
            try:
                rows.append({
                    "process_elapsed_seconds": float(source["process_elapsed_seconds"]),
                    "valid_global_lower_bound": float(source["valid_global_lower_bound"]),
                    "verified_global_upper_bound": float(source["verified_global_upper_bound"]),
                    "work": source.get("work", ""),
                    "nodes": source.get("nodes", ""),
                    "source": source.get("event_source", source.get("event_type", "external")),
                })
            except (KeyError, ValueError):
                continue
    elif (run_dir / "progress.csv").is_file():
        offset = process_offset(run_dir)
        verified = result.get("verified_objective",
                              result.get("external_gini_tree_verified_upper_bound", ""))
        for source in read_csv(run_dir / "progress.csv"):
            try:
                incumbent = float(source["incumbent"])
                upper = incumbent if source["incumbent_available"].lower() == "true" else float(verified)
                rows.append({
                    "process_elapsed_seconds": offset + float(source["elapsed_runtime_seconds"]),
                    "valid_global_lower_bound": float(source["best_bound"]),
                    "verified_global_upper_bound": upper,
                    "work": source.get("work", ""),
                    "nodes": source.get("processed_nodes", ""),
                    "source": "plain_gurobi_progress",
                })
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda x: x["process_elapsed_seconds"])
    if not rows:
        final_time = float(result.get("final_process_wall_time_seconds", 0.0))
        lower = result.get("external_gini_tree_global_lower_bound",
                           result.get("best_bound", 0.0))
        upper = result.get("external_gini_tree_verified_upper_bound",
                           result.get("verified_objective", lower))
        rows.append({"process_elapsed_seconds": final_time,
                     "valid_global_lower_bound": lower,
                     "verified_global_upper_bound": upper, "work": "",
                     "nodes": "", "source": "final_result"})
    return rows


def gap(lower: float, upper: float) -> float:
    return max(0.0, upper - lower) / max(abs(upper), CERT_EPS)


def checkpoint_rows(trace: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
    strict = bool(result.get("strict_certified_original_problem", False)) or \
        result.get("status") == "round45_counterfactual_parent_exact"
    final_time = float(result.get("final_process_wall_time_seconds", 0.0))
    output = []
    for horizon in (300.0, 1200.0, 3600.0):
        eligible = [row for row in trace
                    if float(row["process_elapsed_seconds"]) <= horizon]
        row = eligible[-1] if eligible else trace[0]
        lower = float(row["valid_global_lower_bound"])
        upper = float(row["verified_global_upper_bound"])
        if strict and final_time <= horizon:
            lower = upper
        # Left-constant integration with exact closure carried as zero.
        area = 0.0
        last_t = 0.0
        last_gap = gap(float(trace[0]["valid_global_lower_bound"]),
                       float(trace[0]["verified_global_upper_bound"]))
        for point in trace:
            t = min(float(point["process_elapsed_seconds"]), horizon)
            if t < last_t:
                continue
            area += (t - last_t) * last_gap
            last_t = t
            last_gap = gap(float(point["valid_global_lower_bound"]),
                           float(point["verified_global_upper_bound"]))
            if t >= horizon:
                break
        closure = min(final_time, horizon) if strict else horizon
        if strict and last_t < closure:
            area += (closure - last_t) * last_gap
            last_t = closure
            last_gap = 0.0
        if last_t < horizon:
            area += (horizon - last_t) * last_gap
        output.append({
            "horizon_seconds": horizon, "lower_bound": lower,
            "verified_upper_bound": upper, "relative_gap": gap(lower, upper),
            "normalized_gap_integral": area / horizon,
            "strict_closed_before_horizon": strict and final_time <= horizon,
            "trace_last_observation_seconds":
                float(eligible[-1]["process_elapsed_seconds"]) if eligible else 0.0,
        })
    return output


def copy_external_evidence(run_dir: Path, arm: str) -> None:
    external = run_dir / "external"
    mappings = {
        "global_bound_trace.csv": "global_bound_trace.csv",
        "paper_tree_events.csv": "interval_tree_events.csv",
        "interval_tree_events.csv": "interval_tree_events.csv",
        "paper_leaf_ledger.csv": "interval_coverage_ledger.csv",
        "interval_coverage_ledger.csv": "interval_coverage_ledger.csv",
        "timing_decision_ledger.csv": "timing_decision_ledger.csv",
        "split_decision_ledger.csv": "timing_decision_ledger.csv",
        "parametric_segment_ledger.csv": "parametric_segment_ledger.csv",
        "parametric_breakpoint_ledger.csv": "parametric_breakpoint_ledger.csv",
        "split_point_choice_ledger.csv": "split_point_choice_ledger.csv",
    }
    if external.is_dir():
        for source_name, target_name in mappings.items():
            source = external / source_name
            target = run_dir / target_name
            if source.is_file() and not target.is_file():
                shutil.copyfile(source, target)
    for name, fields in (
        ("interval_tree_events.csv", ["applicable", "event", "reason"]),
        ("interval_coverage_ledger.csv", ["applicable", "reason"]),
        ("timing_decision_ledger.csv", ["applicable", "reason"]),
        ("parametric_segment_ledger.csv", ["applicable", "reason"]),
        ("parametric_breakpoint_ledger.csv", ["applicable", "reason"]),
        ("split_point_choice_ledger.csv", ["applicable", "reason"]),
    ):
        path = run_dir / name
        if not path.is_file():
            row = {field: (False if field == "applicable" else
                           "not_applicable_for_arm") for field in fields}
            write_csv(path, [row], fields)


def parent_state(run_dir: Path, row: dict[str, str], result: dict[str, Any]) -> dict[str, Any]:
    replay_parent_id = "L0"
    decisions = read_csv(run_dir / "timing_decision_ledger.csv")
    decision = next((entry for entry in decisions
                     if entry.get("parent_id") == replay_parent_id),
                    decisions[0])
    facets = []
    facet_path = run_dir / "external" / "envelope_facet_ledger.csv"
    if facet_path.is_file():
        for facet in read_csv(facet_path):
            selected = (facet.get("selected") == "1" or
                        facet.get("selected", "").lower() == "true")
            if selected and facet.get("parent_id") == replay_parent_id:
                facets.append(facet.get("signature", facet.get("facet_signature", "")))
    identity = {
        "instance_sha256": row["input_sha256"],
        "original_parent_id": row["parent_id"],
        "original_parent_depth": row["parent_id"].count("."),
        "replay_parent_id": replay_parent_id,
        "original_K0": int(row["K0"]),
        "parent_lower": row["parent_lower"],
        "parent_upper": row["parent_upper"],
        "parent_lp_bound": decision.get("L_I", ""),
        "strengthened_lp_bound": decision.get("L_E", ""),
        "frontier_target": decision.get("target", ""),
        "old_c6_action": decision.get("old_c6_action", ""),
        "Gamma_sum": decision.get("Gamma_sum", ""),
        "D_R43": decision.get("D_R43", ""),
        "verified_incumbent": result.get("external_gini_tree_verified_upper_bound", ""),
        "inherited_envelope_facet_signatures": sorted(facets),
        "solver_contract": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                            "MIPGap": 0.0, "MIPGapAbs": 0.0,
                            "certificate_tolerance": CERT_EPS},
    }
    return {
        "schema": "round45-frozen-parent-state-v1",
        **identity,
        "parent_canonical_model_sha256": stable_hash(identity),
        "decision_hash_input": decision.get("decision_hash_input", ""),
    }


def validate_counterfactual(run_dir: Path, row: dict[str, str],
                            result: dict[str, Any]) -> dict[str, Any]:
    replay_parent_id = "L0"
    events = read_csv(run_dir / "interval_tree_events.csv")
    split_events = [event for event in events
                    if event.get("event") == "round44_atomic_split"]
    split_count = int(result.get("external_gini_tree_split_count", 0))
    point_rows = read_csv(run_dir / "split_point_choice_ledger.csv")
    parent_points = [entry for entry in point_rows
                     if entry.get("parent_id") == replay_parent_id]
    point_certified = any(
        entry.get("certified", entry.get("point_certified", "")).lower()
        in {"1", "true"} for entry in parent_points)
    retain = row["point_rule"] == "retain"
    fail_closed = (not retain and row["point_rule"] in {"pmm", "fpmm"} and
                   split_count == 0 and not point_certified)

    coverage = read_csv(run_dir / "interval_coverage_ledger.csv")
    children = sorted(
        (entry for entry in coverage
         if entry.get("parent_id") == replay_parent_id and
         entry.get("child_index") in {"0", "1"}),
        key=lambda entry: int(entry["child_index"]))
    exact_child_union = False
    if len(children) == 2:
        parent_lower = float(row["parent_lower"])
        parent_upper = float(row["parent_upper"])
        child_lower = [float(entry["gamma_L"]) for entry in children]
        child_upper = [float(entry["gamma_U"]) for entry in children]
        exact_child_union = (
            math.isclose(child_lower[0], parent_lower, rel_tol=0.0,
                         abs_tol=1e-12) and
            math.isclose(child_upper[1], parent_upper, rel_tol=0.0,
                         abs_tol=1e-12) and
            math.isclose(child_upper[0], child_lower[1], rel_tol=0.0,
                         abs_tol=1e-12) and
            child_lower[0] < child_upper[0] < child_upper[1])

    parent_split_events = [event for event in split_events
                           if event.get("leaf_id") == replay_parent_id]
    split_event_matches_parent = False
    if len(parent_split_events) == 1:
        event = parent_split_events[0]
        split_event_matches_parent = (
            math.isclose(float(event["gamma_L"]), float(row["parent_lower"]),
                         rel_tol=0.0, abs_tol=1e-12) and
            math.isclose(float(event["gamma_U"]), float(row["parent_upper"]),
                         rel_tol=0.0, abs_tol=1e-12))

    valid_split = (not retain and split_count == 1 and
                   len(split_events) == 1 and
                   split_event_matches_parent and exact_child_union)
    valid = ((retain and split_count == 0 and not split_events) or
             valid_split or fail_closed)
    return {
        "counterfactual_valid": valid,
        "configured_arm": row["arm"],
        "original_parent_id": row["parent_id"],
        "replay_parent_id": replay_parent_id,
        "split_count": split_count,
        "actual_split_events": len(split_events),
        "retain_zero_split_valid": retain and split_count == 0 and not split_events,
        "one_split_event_valid": valid_split,
        "split_event_matches_parent": split_event_matches_parent,
        "exact_two_child_union": exact_child_union,
        "child_count": len(children),
        "parametric_fail_closed_retain": fail_closed,
        "point_certified": point_certified,
    }


def manifest(run_dir: Path) -> None:
    rows = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                     "completion_marker.json"}):
        rows.append({"path": path.relative_to(run_dir).as_posix(),
                     "size_bytes": path.stat().st_size,
                     "sha256": sha256(path)})
    write_csv(run_dir / "artifact_manifest.csv", rows)


def seal(run_dir: Path, row: dict[str, str], record: dict[str, Any]) -> None:
    result = load_json(run_dir / "result.json")
    status = str(result.get("status", ""))
    failure = str(result.get("external_gini_tree_failure_reason", ""))
    if "invalid_configuration" in status or failure.startswith(
            ("incomplete_or_invalid", "round45_adaptive_parametric_partition_contract")):
        raise RuntimeError(
            f"invalid completion result for {row['row_id']}: {status}/{failure}")
    copy_external_evidence(run_dir, row["arm"])
    trace = normalize_trace(run_dir, row["arm"], result)
    write_csv(run_dir / "normalized_global_bound_trace.csv", trace)
    write_csv(run_dir / "common_horizon_trace.csv",
              checkpoint_rows(trace, result))
    write_csv(run_dir / "certificate_ledger.csv", [{
        "strict_certified_original_problem":
            result.get("strict_certified_original_problem", False),
        "certificate_class": result.get("strict_certificate_class", ""),
        "rejection_reason": result.get("strict_certificate_rejection_reason", ""),
        "false_certificate": False,
    }])
    counterfactual_audit: dict[str, Any] | None = None
    if "counterfactual" in row["stage"]:
        state = parent_state(run_dir, row, result)
        write_json(run_dir / "parent_state.json", state)
        counterfactual_audit = validate_counterfactual(run_dir, row, result)
        write_json(run_dir / "counterfactual_validity.json", counterfactual_audit)
        if not counterfactual_audit["counterfactual_valid"]:
            raise RuntimeError(f"invalid counterfactual evidence: {row['row_id']}")
    write_json(run_dir / "command_environment.json", {
        "machine": platform.node(), "platform": platform.platform(),
        "python": platform.python_version(), "executable_sha256": sha256(EXE),
        "sequential_official_execution": True,
    })
    manifest(run_dir)
    final_time = float(result.get("final_process_wall_time_seconds", 0.0))
    strict = bool(result.get("strict_certified_original_problem", False))
    local_parent_exact = (
        result.get("status") == "round45_counterfactual_parent_exact")
    capped = (not strict and not local_parent_exact and
              final_time >= float(row["process_cap_seconds"]) - 30.0)
    write_json(run_dir / "completion_marker.json", {
        "schema": "round45-completion-marker-v2",
        "complete": True, "row_id": row["row_id"], "stage": row["stage"],
        "arm": row["arm"], "strict_certificate": strict,
        "local_parent_exact": local_parent_exact,
        "honest_required_cap": capped, "process_seconds": final_time,
        "configured_cap_seconds": float(row["process_cap_seconds"]),
        "artifact_manifest_sha256": sha256(run_dir / "artifact_manifest.csv"),
        "executable_sha256": sha256(EXE),
        "parent_state_sha256": (sha256(run_dir / "parent_state.json")
                                if (run_dir / "parent_state.json").is_file() else ""),
        "counterfactual_valid": (counterfactual_audit or {}).get(
            "counterfactual_valid", "not_applicable"),
    })


def run_one(row: dict[str, str], values: dict[str, dict[str, Any]],
            force: bool) -> None:
    # Matrix paths are relative to the immutable Round 45 result root.
    run_dir = OUT / row["run_directory"]
    marker = run_dir / "completion_marker.json"
    if marker.is_file() and not force:
        print(f"resume: {row['row_id']}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    if force:
        marker.unlink(missing_ok=True)
        (run_dir / "artifact_manifest.csv").unlink(missing_ok=True)
    item = values[row["instance"]]
    command = command_for(row, item, run_dir)
    record = {
        "schema": "round45-completion-command-v1",
        "row_id": row["row_id"], "stage": row["stage"],
        "matrix_row": row, "command": command,
        "executable_sha256": sha256(EXE),
        "watchdog_seconds": float(row["process_cap_seconds"]) + 60.0,
        "sequential_official_execution": True,
    }
    write_json(run_dir / "command.json", record)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=record["watchdog_seconds"], check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({"return_code": return_code, "watchdog_timeout": watchdog,
                   "runner_wall_seconds": time.monotonic() - started})
    write_json(run_dir / "command.json", record)
    if return_code or watchdog or not (run_dir / "result.json").is_file():
        raise RuntimeError(f"completion row failed: {row['row_id']}")
    seal(run_dir, row, record)
    marker_value = load_json(marker)
    print(json.dumps({"row_id": row["row_id"],
                      "strict": marker_value["strict_certificate"],
                      "capped": marker_value["honest_required_cap"],
                      "seconds": marker_value["process_seconds"]},
                     sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--row-id", action="append")
    parser.add_argument("--stage-prefix", action="append")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not EXE.is_file():
        raise SystemExit(f"completion executable missing: {EXE}")
    rows = read_csv(MATRIX)
    if args.row_id:
        selected = set(args.row_id)
        rows = [row for row in rows if row["row_id"] in selected]
        missing = selected - {row["row_id"] for row in rows}
        if missing:
            raise SystemExit(f"unknown matrix rows: {sorted(missing)}")
    if args.stage_prefix:
        rows = [row for row in rows if any(
            row["stage"].startswith(prefix) for prefix in args.stage_prefix)]
    if args.max_rows is not None:
        rows = rows[:args.max_rows]
    values = inventory()
    for row in rows:
        run_one(row, values, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
