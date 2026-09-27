#!/usr/bin/env python3
"""Run and summarize the frozen Round 54 inventory-route root-LP census."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


EVIDENCE_REL = Path("results/gf_k1_am_sf_inventory_route_round54")
ROUND53_REL = Path("results/gf_k1_f0_callback_isolation_round53/local_raw")
ROUND52_REL = Path(
    "results/gf_k1_tailored_cut_final_validation_round52/local_raw/"
    "final_panel_runs"
)
TOLERANCE = 1e-7


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_single_csv(path: Path) -> dict[str, str]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row in {path}, found {len(rows)}")
    return rows[0]


def state_from_command(root: Path, state_id: str, role: str, stage: str) -> dict:
    if stage == "development":
        command_path = (
            root / ROUND53_REL / "f0_development_300s" / "F0-CLEAN"
            / f"{state_id}__F0-CLEAN" / "command.json"
        )
    else:
        command_path = (
            root / ROUND53_REL / "f0_confirmation_1200s" / "F0-CLEAN"
            / f"{state_id}__F0-CLEAN" / "command.json"
        )
    command = read_json(command_path)
    return {
        "state_id": state_id,
        "source_state_id": state_id,
        "structural_role": role,
        "input": Path(command["input"]),
        "input_sha256": sha256(Path(command["input"])),
        "gamma_lower": float(command["gamma_lower"]),
        "gamma_upper": float(command["gamma_upper"]),
        "cutoff": float(command["verified_cutoff"]),
        "route_time_limit": float(command["route_time_limit"]),
        "pickup_time": float(command["pickup_time"]),
        "drop_time": float(command["drop_time"]),
        "origin": f"round53_{stage}",
    }


def v50_state(root: Path, state_id: str, run_name: str, role: str) -> dict:
    run_dir = root / ROUND52_REL / run_name
    command = read_json(run_dir / "command.json")
    with (run_dir / "external" / "initial_decomposition_ledger.csv").open(
        "r", newline="", encoding="utf-8-sig"
    ) as handle:
        active = [row for row in csv.DictReader(handle) if row["active"] == "1"]
    if len(active) != 1:
        raise RuntimeError(f"expected one active initial interval in {run_dir}")
    interval = active[0]
    input_path = root / command["input_path"]
    return {
        "state_id": state_id,
        "source_state_id": state_id,
        "structural_role": role,
        "input": input_path,
        "input_sha256": sha256(input_path),
        "gamma_lower": float(interval["active_lower"]),
        "gamma_upper": float(interval["active_upper"]),
        "cutoff": float(interval["U_proof_launch"]),
        "route_time_limit": float(command["T"]),
        "pickup_time": 60.0,
        "drop_time": 60.0,
        "origin": "round52_v50_initial_active_interval",
    }


def frozen_states(root: Path) -> list[dict]:
    freeze = read_json(root / EVIDENCE_REL / "offline_root_census_freeze.json")
    roles = {row["state_id"]: row["role"] for row in freeze["fixed_states"]}
    states = [
        state_from_command(
            root, f"D{index}", roles[f"D{index}"], "development"
        )
        for index in range(1, 15)
    ]
    states.extend(
        state_from_command(
            root, f"C{index}", roles[f"C{index}"], "confirmation"
        )
        for index in range(1, 10)
    )
    aliases = [
        ("ROLE_MAJOR", "D1", "major"),
        ("ROLE_STRONG_CONTROL", "D3", "strong control"),
        ("ROLE_NUMERICAL_ENDPOINT", "D12", "numerical endpoint"),
        ("ROLE_V12_M2", "D6", "V12 M2"),
        ("ROLE_TIGHT3102", "D9", "tight3102"),
        ("ROLE_HIGH3201", "D13", "high-imbalance 3201"),
        ("ROLE_HIGH3202", "C4", "high-imbalance 3202"),
        ("ROLE_MODERATE3301", "D14", "moderate3301"),
        ("ROLE_MODERATE3302", "C5", "moderate3302"),
    ]
    by_id = {state["state_id"]: state for state in states}
    for alias_id, source_id, role in aliases:
        alias = dict(by_id[source_id])
        alias.update(
            state_id=alias_id,
            source_state_id=source_id,
            structural_role=role,
            origin="structural_role_alias",
        )
        states.append(alias)
    states.extend(
        [
            v50_state(
                root,
                "V50_TIGHT",
                "validation__round52_validation_tight_T_2400_V50_M3_seed1300319903__K1-AM-FINAL__official",
                "V50 tight",
            ),
            v50_state(
                root,
                "V50_MODERATE",
                "validation__round52_validation_moderate_3600_V50_M3_seed664120090__K1-AM-FINAL__official",
                "V50 moderate",
            ),
        ]
    )
    return states


def as_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def one_pass_objective(ledger_path: Path, final_objective: float) -> float:
    with ledger_path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) >= 2:
        return as_float(rows[1]["lp_objective"], final_objective)
    return final_objective


def run_state(
    root: Path,
    executable: Path,
    gurobi_home: str,
    state: dict,
    variant: str,
    force: bool,
) -> dict:
    run_dir = root / EVIDENCE_REL / "local_raw" / "inventory_route_census" / variant / state["state_id"]
    result_path = run_dir / "result.json"
    if force or not result_path.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
        process_cap = 3600.0 if state["state_id"].startswith("V50") else 120.0
        command = [
            str(executable),
            "--mode", "closure",
            "--state-id", state["state_id"],
            "--input", str(state["input"]),
            "--artifact-dir", str(run_dir),
            "--variant", variant,
            "--gurobi-home", gurobi_home,
            "--gamma-lower", repr(state["gamma_lower"]),
            "--gamma-upper", repr(state["gamma_upper"]),
            "--cutoff", repr(state["cutoff"]),
            "--process-cap", repr(process_cap),
            "--route-time-limit", repr(state["route_time_limit"]),
            "--pickup-time", repr(state["pickup_time"]),
            "--drop-time", repr(state["drop_time"]),
        ]
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=process_cap + 60.0,
            check=False,
        )
        (run_dir / "runner_stdout.txt").write_text(
            completed.stdout, encoding="utf-8"
        )
        (run_dir / "runner_stderr.txt").write_text(
            completed.stderr, encoding="utf-8"
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"{variant}/{state['state_id']} returned {completed.returncode}: "
                f"{completed.stderr[-500:]}"
            )
    result = read_json(result_path)
    result["closure_variant"] = result["variant"]
    result["variant"] = variant.upper()
    overhead = read_single_csv(run_dir / "root_closure_overhead_audit.csv")
    result.update(
        state_id=state["state_id"],
        source_state_id=state["source_state_id"],
        structural_role=state["structural_role"],
        origin=state["origin"],
        input=str(state["input"].relative_to(root)).replace("\\", "/"),
        input_sha256=state["input_sha256"],
        one_pass_root_lp_objective=one_pass_objective(
            run_dir / "external_root_closure_ledger.csv",
            as_float(result["final_root_closure_objective"]),
        ),
        model_read_time_seconds=as_float(overhead["model_read_time"]),
    )
    return result


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def concatenate_ledgers(root: Path, states: list[dict], variants: list[str], name: str) -> None:
    output_path = root / EVIDENCE_REL / name
    writer = None
    handle = output_path.open("w", newline="", encoding="utf-8")
    try:
        for variant in variants:
            for state in states:
                source = (
                    root / EVIDENCE_REL / "local_raw" / "inventory_route_census"
                    / variant / state["state_id"] / name
                )
                with source.open("r", newline="", encoding="utf-8-sig") as source_handle:
                    reader = csv.DictReader(source_handle)
                    if writer is None:
                        writer = csv.DictWriter(handle, fieldnames=reader.fieldnames)
                        writer.writeheader()
                    writer.writerows(reader)
    finally:
        handle.close()


def evaluate_gate(rows: list[dict], variant: str) -> dict:
    selected = [row for row in rows if row["variant"] == variant]
    unique_roles = {
        row["structural_role"]
        for row in selected
        if max(
            as_float(row["initial_max_inbound_violation"]),
            as_float(row["initial_max_outbound_violation"]),
            as_float(row["initial_max_projected_inbound_violation"]),
            as_float(row["initial_max_projected_outbound_violation"]),
        ) > TOLERANCE
    }
    gain_states = [
        row["state_id"]
        for row in selected
        if as_float(row["root_bound_gain"]) > TOLERANCE
    ]
    infeasible = [row["state_id"] for row in selected if bool(row["closure_infeasible"])]
    all_valid = all(
        bool(row["closure_valid"])
        and not bool(row["fallback_required"])
        and bool(row["cap_respected"])
        for row in selected
    )
    no_numerical_issue = all(
        str(row.get("closure_failure_reason", "")).lower() in {"", "none"}
        for row in selected
    )
    alternative = bool(infeasible) and len(unique_roles) >= 2
    passed = (
        all_valid
        and len(unique_roles) >= 2
        and (len(gain_states) >= 2 or alternative)
        and no_numerical_issue
    )
    return {
        "variant": variant,
        "row_count": len(selected),
        "valid_every_state": all_valid,
        "strict_violation_role_count": len(unique_roles),
        "strict_violation_roles": sorted(unique_roles),
        "strict_bound_gain_state_count": len(gain_states),
        "strict_bound_gain_states": gain_states,
        "infeasible_closure_states": infeasible,
        "no_numerical_inconsistency": no_numerical_issue,
        "new_parameter": False,
        "live_entry_gate_passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--executable",
        type=Path,
        default=Path("build/dev-gurobi-release/Round54InventoryRouteExperiment.exe"),
    )
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    executable = args.executable
    if not executable.is_absolute():
        executable = root / executable
    evidence = root / EVIDENCE_REL
    states = frozen_states(root)
    variants = ["ir1", "ir2"]
    rows: list[dict] = []
    for variant in variants:
        for ordinal, state in enumerate(states, start=1):
            print(f"[{variant} {ordinal}/{len(states)}] {state['state_id']}", flush=True)
            rows.append(
                run_state(root, executable, args.gurobi_home, state, variant, args.force)
            )

    census_fields = [
        "state_id", "source_state_id", "structural_role", "origin", "variant",
        "closure_variant",
        "input", "input_sha256", "closure_valid", "closure_converged",
        "closure_infeasible", "fallback_required", "closure_failure_reason",
        "initial_root_lp_objective", "initial_max_inbound_violation",
        "initial_inbound_subset", "initial_max_outbound_violation",
        "initial_outbound_subset", "initial_max_projected_inbound_violation",
        "initial_projected_inbound_subset", "initial_max_projected_outbound_violation",
        "initial_projected_outbound_subset", "one_pass_root_lp_objective",
        "final_root_closure_objective", "root_bound_gain", "closure_rounds",
        "cuts_generated", "cuts_added", "duplicate_rejections",
        "dominated_rejections", "nonviolated_rejections", "closure_work",
        "closure_solver_time_seconds", "model_read_time_seconds",
        "closure_simplex_iterations", "process_time_seconds", "process_cap_seconds",
        "cap_respected", "model_sha256", "model_rows", "model_columns",
        "model_nonzeros", "subset_duration_rows",
    ]
    write_csv(evidence / "inventory_route_root_census.csv", rows, census_fields)
    bound_rows = [
        {
            "state_id": row["state_id"],
            "structural_role": row["structural_role"],
            "variant": row["variant"],
            "initial_root_lp_objective": row["initial_root_lp_objective"],
            "one_pass_root_lp_objective": row["one_pass_root_lp_objective"],
            "final_root_closure_objective": row["final_root_closure_objective"],
            "one_pass_gain": as_float(row["one_pass_root_lp_objective"])
            - as_float(row["initial_root_lp_objective"]),
            "full_closure_gain": row["root_bound_gain"],
            "closure_work": row["closure_work"],
            "closure_solver_time_seconds": row["closure_solver_time_seconds"],
            "model_read_time_seconds": row["model_read_time_seconds"],
            "valid": row["closure_valid"],
        }
        for row in rows
    ]
    write_csv(
        evidence / "inventory_route_bound_gain.csv",
        bound_rows,
        list(bound_rows[0]),
    )
    for name in [
        "external_root_closure_ledger.csv",
        "root_cut_pool_ledger.csv",
        "root_closure_overhead_audit.csv",
    ]:
        concatenate_ledgers(root, states, variants, name)

    gate_variants = [evaluate_gate(rows, variant.upper()) for variant in variants]
    passing = [gate for gate in gate_variants if gate["live_entry_gate_passed"]]
    selected = None
    selection_reason = "No variant passed the frozen offline live-entry gate."
    if passing:
        selected = "IR1"
        selection_reason = "IR1 passed; it is the least expansive valid family."
        ir2 = next((gate for gate in passing if gate["variant"] == "ir2"), None)
        if ir2:
            ir1_rows = {row["state_id"]: row for row in rows if row["variant"] == "IR1"}
            strict_ir2_advantage = any(
                as_float(row["final_root_closure_objective"])
                > as_float(ir1_rows[row["state_id"]]["final_root_closure_objective"])
                + TOLERANCE
                for row in rows if row["variant"] == "IR2"
            )
            if strict_ir2_advantage:
                selected = "IR2"
                selection_reason = "IR2 passed and supplied a strict nondominated closure improvement over IR1."
    gate = {
        "schema": "round54-inventory-route-offline-gate-v1",
        "executable": str(executable.relative_to(root)).replace("\\", "/"),
        "executable_sha256": sha256(executable),
        "tolerance": TOLERANCE,
        "physical_state_count": len(states),
        "variant_count": len(variants),
        "row_count": len(rows),
        "variants": gate_variants,
        "live_stage_opened": selected is not None,
        "selected_candidate": selected,
        "selection_reason": selection_reason,
        "final_mip_runtime_used_for_selection": False,
        "iteration_2_status": "not_opened_pending_overhead_condition",
        "classification": (
            "inventory_route_offline_gate_passed" if selected
            else "offline_negative_inventory_route_strengthening"
        ),
    }
    (evidence / "inventory_route_offline_gate.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired as exc:
        print(f"census process exceeded external safety cap: {exc}", file=sys.stderr)
        raise SystemExit(3)
    except Exception as exc:  # concise failure marker for the orchestrating shell
        print(f"Round 54 census failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
