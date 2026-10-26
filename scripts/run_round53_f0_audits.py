#!/usr/bin/env python3
"""Build, compare, and LP-audit the frozen Round 53 F0 states."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
MANIFEST = ROUND50 / "fixed_interval_state_manifest.csv"
RECONSTRUCTION = ROUND50 / "fixed_interval_state_reconstruction_audit.csv"
V0 = "interval-mip-v0"
F0 = "interval-mip-core-no-exhaustive-subset-duration"
TARGET_TOLERANCE = 1e-7
DUAL_TOLERANCE = 1e-9


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def section(lines: list[str], start: str, end: str | None) -> list[str]:
    begin = next(i for i, line in enumerate(lines) if line.strip() == start) + 1
    finish = len(lines) if end is None else next(
        i for i in range(begin, len(lines)) if lines[i].strip() == end)
    return lines[begin:finish]


def canonical_constraint(line: str) -> str:
    return re.sub(r"^\s*c\d+:\s*", "", line).strip()


def target_details(line: str, route_time_limit: float) -> dict[str, object]:
    name_match = re.match(r"\s*(c\d+):\s*(.*)", line)
    if not name_match:
        raise RuntimeError(f"target row has no canonical name: {line}")
    row_name, body = name_match.group(1), name_match.group(2)
    sense_match = re.match(r"(.*)\s(<=|>=|=)\s([^\s]+)\s*$", body)
    if not sense_match:
        raise RuntimeError(f"target row has no terminal sense/RHS: {line}")
    lhs, sense, rhs_text = sense_match.groups()
    rhs = float(rhs_text)
    terms = re.findall(
        r"(?:^|\s[+]\s)(?:(-?[0-9.eE+\-]+)\s+)?([pz]_\d+_\d+)", lhs)
    if not terms:
        raise RuntimeError(f"target row terms unavailable: {line}")
    coefficients = [float(value) if value else 1.0 for value, _ in terms]
    p_names = [name for _, name in terms if name.startswith("p_")]
    z_values = [float(value) if value else 1.0 for value, name in terms
                if name.startswith("z_")]
    if not p_names or len(p_names) != len(z_values):
        raise RuntimeError(f"target support mapping invalid: {line}")
    vehicle = int(p_names[0].split("_")[1])
    support = sorted(int(name.split("_")[2]) for name in p_names)
    big_m = max(z_values)
    route_lb = route_time_limit + big_m * len(support) - rhs
    normalized = " ".join(canonical_constraint(line).split())
    return {
        "row_name": row_name, "vehicle_index": vehicle,
        "support_size": len(support),
        "support": ";".join(map(str, support)),
        "coefficient_min_abs": min(abs(value) for value in coefficients),
        "coefficient_max_abs": max(abs(value) for value in coefficients),
        "rhs": rhs, "sense": sense, "historical_big_m": big_m,
        "route_duration_lower_bound": route_lb,
        "big_m_dominates_route_lb": big_m + 1e-9 >= route_lb,
        "canonical_signature": hashlib.sha256(
            normalized.encode("utf-8")).hexdigest(),
    }


def command_contract(command: dict[str, object]) -> dict[str, object]:
    return {
        key: command.get(key) for key in (
            "mode", "state_id", "input", "gamma_lower", "gamma_upper",
            "verified_cutoff", "route_time_limit", "pickup_time",
            "drop_time", "process_cap_seconds", "solver",
            "known_optimum_injection", "archive_winner_injection")
    }


def run_artifact(executable: Path, executable_hash: str,
                 frozen: dict[str, str], state: dict[str, str],
                 policy: str, mode: str, artifact: Path,
                 gurobi_home: str) -> None:
    marker = artifact / "completion_marker.json"
    expected_status = "model_built" if mode == "build" else "lp_optimal"
    if marker.is_file():
        completion = read_json(marker)
        command = read_json(artifact / "command.json")
        if (completion.get("status") == expected_status and
                completion.get("evidence_complete") is True and
                command.get("executable_sha256") == executable_hash and
                command.get("policy") == policy and
                command.get("mode") == mode):
            return
        raise RuntimeError(f"stale script-owned artifact: {artifact}")
    artifact.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable), "--mode", mode, "--state-id", frozen["state_id"],
        "--input", str(ROOT / frozen["input_path"]),
        "--artifact-dir", str(artifact), "--policy", policy,
        "--gurobi-home", gurobi_home,
        "--gamma-lower", state["gamma_lower"],
        "--gamma-upper", state["gamma_upper"],
        "--cutoff", state["verified_cutoff"], "--process-cap", "60",
        "--T", state["route_time_limit"], "--pickup-time", "60",
        "--drop-time", "60"]
    completed = subprocess.run(command, cwd=ROOT, timeout=120.0, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"{mode} {frozen['state_id']} {policy} returned "
            f"{completed.returncode}")


def run_incumbent_verification(executable: Path, executable_hash: str,
                               frozen: dict[str, str], state: dict[str, str],
                               artifact: Path) -> dict[str, object]:
    result_path = artifact / "cutoff_resolution.json"
    if result_path.is_file():
        command = read_json(artifact / "command.json")
        if (command.get("executable_sha256") != executable_hash or
                command.get("expected_cutoff") !=
                float(state["verified_cutoff"])):
            raise RuntimeError(f"stale incumbent artifact: {artifact}")
    else:
        artifact.mkdir(parents=True, exist_ok=True)
        command = [
            str(executable), "--mode", "resolve-cutoff", "--state-id",
            frozen["state_id"], "--input", str(ROOT / frozen["input_path"]),
            "--artifact-dir", str(artifact), "--policy", F0,
            "--expected-cutoff", state["verified_cutoff"],
            "--process-cap", "300", "--T", state["route_time_limit"],
            "--pickup-time", "60", "--drop-time", "60"]
        completed = subprocess.run(command, cwd=ROOT, timeout=345.0,
                                   check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"incumbent verification {frozen['state_id']} returned "
                f"{completed.returncode}")
    return read_json(result_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--states", default=(
        ",".join([f"D{i}" for i in range(1, 15)] +
                 [f"C{i}" for i in range(1, 10)])))
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    executable = args.executable.resolve()
    executable_hash = sha256(executable)
    frozen_map = {row["state_id"]: row for row in csv.DictReader(
        MANIFEST.open(newline="", encoding="utf-8-sig"))}
    state_map = {row["state_id"]: row for row in csv.DictReader(
        RECONSTRUCTION.open(newline="", encoding="utf-8-sig"))}
    state_ids = [value.strip() for value in args.states.split(",")
                 if value.strip()]
    if len(state_ids) != len(set(state_ids)) or any(
            value not in frozen_map or value not in state_map
            for value in state_ids):
        raise RuntimeError("unknown or duplicate frozen state")

    # Keep evidence from distinct binaries physically separate.  This makes a
    # development smoke run incapable of being resumed as an official run.
    raw_root = (OUT / "local_raw" / "f0_model_lp_audit" /
                executable_hash[:16])
    model_rows: list[dict[str, object]] = []
    vgt12_rows: list[dict[str, object]] = []
    activity_rows: list[dict[str, object]] = []
    dual_rows: list[dict[str, object]] = []
    lp_rows: list[dict[str, object]] = []
    size_rows: list[dict[str, object]] = []
    incumbent_rows: list[dict[str, object]] = []
    small_rows: list[dict[str, object]] = []

    for state_id in state_ids:
        frozen, state = frozen_map[state_id], state_map[state_id]
        input_path = ROOT / frozen["input_path"]
        if sha256(input_path) != frozen["input_sha256"]:
            raise RuntimeError(f"input hash mismatch: {state_id}")
        artifacts: dict[str, dict[str, Path]] = {}
        for label, policy in (("production-v0", V0), ("F0-CLEAN", F0)):
            build = raw_root / "build" / f"{state_id}__{label}"
            lp = raw_root / "plain_lp" / f"{state_id}__{label}"
            run_artifact(executable, executable_hash, frozen, state,
                         policy, "build", build, args.gurobi_home)
            run_artifact(executable, executable_hash, frozen, state,
                         policy, "lp", lp, args.gurobi_home)
            artifacts[label] = {"build": build, "lp": lp}

        v0_model = read_json(
            artifacts["production-v0"]["build"] / "model_fingerprint.json")
        f0_model = read_json(
            artifacts["F0-CLEAN"]["build"] / "model_fingerprint.json")
        v0_command = read_json(
            artifacts["production-v0"]["build"] / "command.json")
        f0_command = read_json(artifacts["F0-CLEAN"]["build"] / "command.json")
        v0_path = artifacts["production-v0"]["build"] / "canonical_model.lp"
        f0_path = artifacts["F0-CLEAN"]["build"] / "canonical_model.lp"
        v0_lines = v0_path.read_text(encoding="utf-8").splitlines()
        f0_lines = f0_path.read_text(encoding="utf-8").splitlines()
        v0_constraints = section(v0_lines, "Subject To", "Bounds")
        f0_constraints = section(f0_lines, "Subject To", "Bounds")
        first_id = int(v0_model["round51_subset_duration_first_row_id"])
        last_id = int(v0_model["round51_subset_duration_last_row_id"])
        target_lines, nontarget_v0 = [], []
        for line in v0_constraints:
            matched = re.match(r"\s*c(\d+):", line)
            row_id = int(matched.group(1)) if matched else -1
            (target_lines if first_id <= row_id <= last_id
             else nontarget_v0).append(line)
        nontarget_identity = (
            [canonical_constraint(line) for line in nontarget_v0] ==
            [canonical_constraint(line) for line in f0_constraints])
        objective_identity = (
            section(v0_lines, "Minimize", "Subject To") ==
            section(f0_lines, "Minimize", "Subject To"))
        domain_identity = (
            v0_lines[v0_lines.index("Bounds"):] ==
            f0_lines[f0_lines.index("Bounds"):])
        command_identity = command_contract(v0_command) == command_contract(
            f0_command)
        removed_rows = int(v0_model["rows"]) - int(f0_model["rows"])
        removed_nonzeros = int(v0_model["nonzeros"]) - int(
            f0_model["nonzeros"])
        size_match = re.search(
            r"(?:_|/)V(\d+)(?:_|/)",
            frozen["instance"] + "_" + frozen["input_path"])
        if not size_match:
            raise RuntimeError(f"cannot determine V: {state_id}")
        V = int(size_match.group(1))
        changed_expected = V <= 12
        byte_identical = v0_path.read_bytes() == f0_path.read_bytes()
        model_pass = (objective_identity and domain_identity and
                      nontarget_identity and command_identity and
                      int(v0_model["columns"]) == int(f0_model["columns"]) and
                      removed_rows == len(target_lines) and
                      removed_rows == int(
                          v0_model["round51_subset_duration_rows"]) and
                      ((changed_expected and removed_rows > 0) or
                       (not changed_expected and removed_rows == 0 and
                        removed_nonzeros == 0 and byte_identical)))
        model_rows.append({
            "state_id": state_id, "instance": frozen["instance"], "V": V,
            "objective_identity": objective_identity,
            "variable_order_type_bound_identity": domain_identity,
            "interval_cutoff_symmetry_and_nontarget_rows_identity":
                nontarget_identity,
            "solver_command_contract_identity": command_identity,
            "v0_model_sha256": v0_model["sha256"],
            "f0_model_sha256": f0_model["sha256"],
            "byte_identical": byte_identical,
            "v0_rows": v0_model["rows"], "f0_rows": f0_model["rows"],
            "removed_rows": removed_rows,
            "v0_columns": v0_model["columns"],
            "f0_columns": f0_model["columns"],
            "v0_nonzeros": v0_model["nonzeros"],
            "f0_nonzeros": f0_model["nonzeros"],
            "removed_nonzeros": removed_nonzeros,
            "target_first_row_id": first_id, "target_last_row_id": last_id,
            "pass": model_pass, "executable_sha256": executable_hash})
        if V > 12:
            vgt12_rows.append({
                "state_id": state_id, "instance": frozen["instance"],
                "V": V, "v0_sha256": v0_model["sha256"],
                "f0_sha256": f0_model["sha256"],
                "rows_identity": v0_model["rows"] == f0_model["rows"],
                "columns_identity": v0_model["columns"] == f0_model["columns"],
                "nonzeros_identity": v0_model["nonzeros"] == f0_model["nonzeros"],
                "byte_identity": byte_identical,
                "command_contract_identity": command_identity,
                "pass": model_pass})

        v0_lp = read_json(
            artifacts["production-v0"]["lp"] / "lp_result.json")
        f0_lp = read_json(artifacts["F0-CLEAN"]["lp"] / "lp_result.json")
        evidence = {row["row_name"]: row for row in csv.DictReader(
            (artifacts["production-v0"]["lp"] /
             "lp_constraint_evidence.csv").open(
                 newline="", encoding="utf-8-sig"))}
        slacks, scaled_slacks, duals = [], [], []
        active_count = dual_count = safe_count = parsed_nonzeros = 0
        for target in target_lines:
            detail = target_details(target, float(state["route_time_limit"]))
            row_evidence = evidence.get(str(detail["row_name"]))
            if row_evidence is None:
                raise RuntimeError(
                    f"missing target LP evidence {state_id} {detail['row_name']}")
            slack = float(row_evidence["slack"])
            dual = float(row_evidence["dual_multiplier"])
            scale = max(1.0, abs(float(detail["rhs"])),
                        float(detail["coefficient_max_abs"]))
            scaled_slack = slack / scale
            active = abs(scaled_slack) <= TARGET_TOLERANCE
            nonzero_dual = abs(dual) > DUAL_TOLERANCE
            active_count += int(active)
            dual_count += int(nonzero_dual)
            safe_count += int(bool(detail["big_m_dominates_route_lb"]))
            parsed_nonzeros += 2 * int(detail["support_size"])
            slacks.append(slack)
            scaled_slacks.append(scaled_slack)
            duals.append(abs(dual))
            activity_rows.append({
                "state_id": state_id, "instance": frozen["instance"],
                **detail, "lp_slack": slack,
                "scaled_slack": scaled_slack,
                "active_at_1e_7_scaled_tolerance": active,
                "dual_multiplier": dual,
                "nonzero_dual_at_1e_9_tolerance": nonzero_dual})
        if parsed_nonzeros != removed_nonzeros:
            raise RuntimeError(f"removed nonzero mismatch: {state_id}")
        count = len(target_lines)
        dual_rows.append({
            "state_id": state_id, "instance": frozen["instance"], "V": V,
            "removed_rows": count, "removed_nonzeros": removed_nonzeros,
            "big_m_valid_rows": safe_count,
            "big_m_valid_all": safe_count == count,
            "active_rows": active_count,
            "active_percentage": 0.0 if not count else 100 * active_count / count,
            "nonzero_dual_rows": dual_count,
            "nonzero_dual_percentage": 0.0 if not count else 100 * dual_count / count,
            "slack_p00": percentile(slacks, 0),
            "slack_p25": percentile(slacks, .25),
            "slack_p50": percentile(slacks, .5),
            "slack_p75": percentile(slacks, .75),
            "slack_p100": percentile(slacks, 1),
            "scaled_slack_p50": percentile(scaled_slacks, .5),
            "dual_abs_p50": percentile(duals, .5),
            "dual_abs_p90": percentile(duals, .9),
            "dual_abs_p100": percentile(duals, 1)})
        lp_rows.append({
            "state_id": state_id, "instance": frozen["instance"], "V": V,
            "v0_lp_valid": v0_lp["valid"], "f0_lp_valid": f0_lp["valid"],
            "v0_lp_objective": v0_lp["objective"],
            "f0_lp_objective": f0_lp["objective"],
            "objective_difference_f0_minus_v0":
                float(f0_lp["objective"]) - float(v0_lp["objective"]),
            "v0_work": v0_lp["work"], "f0_work": f0_lp["work"],
            "v0_solver_time": v0_lp["solver_time_seconds"],
            "f0_solver_time": f0_lp["solver_time_seconds"],
            "v0_simplex_iterations": v0_lp["simplex_iterations"],
            "f0_simplex_iterations": f0_lp["simplex_iterations"],
            "v0_presolved_rows": v0_lp["presolved_rows"],
            "f0_presolved_rows": f0_lp["presolved_rows"],
            "v0_presolved_columns": v0_lp["presolved_columns"],
            "f0_presolved_columns": f0_lp["presolved_columns"],
            "v0_presolved_nonzeros": v0_lp["presolved_nonzeros"],
            "f0_presolved_nonzeros": f0_lp["presolved_nonzeros"],
            "pass": (v0_lp["valid"] and f0_lp["valid"] and
                     float(f0_lp["objective"]) <=
                     float(v0_lp["objective"]) + 1e-7)})
        size_rows.append({
            "state_id": state_id, "instance": frozen["instance"], "V": V,
            "v0_rows": v0_model["rows"], "f0_rows": f0_model["rows"],
            "removed_rows": removed_rows,
            "removed_row_percentage": 100 * removed_rows /
                max(1, int(v0_model["rows"])),
            "v0_columns": v0_model["columns"],
            "f0_columns": f0_model["columns"],
            "v0_nonzeros": v0_model["nonzeros"],
            "f0_nonzeros": f0_model["nonzeros"],
            "removed_nonzeros": removed_nonzeros,
            "removed_nonzero_percentage": 100 * removed_nonzeros /
                max(1, int(v0_model["nonzeros"]))})
        small_rows.append({
            "test_id": f"frozen_model_{state_id}", "scope": "frozen_state",
            "integer_validity_rows_safe": safe_count == count,
            "core_and_objective_identity": model_pass,
            "false_certificate": False,
            "pass": model_pass and safe_count == count})

        incumbent = run_incumbent_verification(
            executable, executable_hash, frozen, state,
            raw_root / "incumbent_verification" / state_id)
        incumbent_rows.append({
            "state_id": state_id, "instance": frozen["instance"],
            "historical_cutoff": state["verified_cutoff"],
            "independent_verifier_found": incumbent["found"],
            "independent_verifier_feasible": incumbent["verified"],
            "verified_objective": incumbent["verified_objective"],
            "objective_matches_historical_cutoff":
                incumbent["expected_cutoff_matches"],
            "f0_preserves_all_core_feasibility_rows": model_pass,
            "accepted_by_f0_integer_model":
                incumbent["verified"] and incumbent["expected_cutoff_matches"]
                and model_pass,
            "false_certificate": False})
        print(f"{state_id}: model={model_pass} rows={removed_rows} "
              f"LPdiff={lp_rows[-1]['objective_difference_f0_minus_v0']}",
              flush=True)

    write_csv(OUT / "f0_model_delta_audit.csv", list(model_rows[0]), model_rows)
    write_csv(OUT / "f0_v_gt_12_equivalence_audit.csv",
              list(vgt12_rows[0]) if vgt12_rows else ["state_id"], vgt12_rows)
    write_csv(OUT / "exhaustive_row_activity_ledger.csv",
              list(activity_rows[0]) if activity_rows else ["state_id"],
              activity_rows)
    write_csv(OUT / "exhaustive_row_dual_summary.csv", list(dual_rows[0]),
              dual_rows)
    write_csv(OUT / "f0_plain_lp_comparison.csv", list(lp_rows[0]), lp_rows)
    write_csv(OUT / "f0_formulation_size_audit.csv", list(size_rows[0]),
              size_rows)
    write_csv(OUT / "f0_small_exact_validation.csv", list(small_rows[0]),
              small_rows)
    write_csv(OUT / "f0_incumbent_feasibility_audit.csv",
              list(incumbent_rows[0]), incumbent_rows)

    total_rows = sum(int(row["removed_rows"]) for row in dual_rows)
    total_active = sum(int(row["active_rows"]) for row in dual_rows)
    total_dual = sum(int(row["nonzero_dual_rows"]) for row in dual_rows)
    objective_changes = sum(abs(float(row[
        "objective_difference_f0_minus_v0"])) > 1e-9 for row in lp_rows)
    classification = ("mostly inactive/dual-zero" if total_rows and
                      total_active / total_rows < .05 and
                      total_dual / total_rows < .05 and
                      objective_changes == 0 else
                      "locally useful but globally expensive" if
                      objective_changes or total_dual else "inconclusive")
    (OUT / "f0_node_lp_cost_analysis.md").write_text(
        "# F0 node-LP cost analysis\n\n"
        f"The frozen audit covered {len(state_ids)} states and "
        f"{total_rows} state-row observations. "
        f"{total_active} rows were active at the scaled 1e-7 tolerance and "
        f"{total_dual} had a dual magnitude above 1e-9. Plain-LP objectives "
        f"changed on {objective_changes} states.\n\n"
        f"Current classification: **{classification}**. This classification "
        "is diagnostic only; row activity, duals, Work, time, iterations, and "
        "presolved size are not algorithm inputs. Terminal-MIP root and "
        "per-node costs are evaluated in the contemporaneous development, "
        "confirmation, and long-horizon panels.\n",
        encoding="utf-8")

    if not all(bool(row["pass"]) for row in model_rows + lp_rows + small_rows):
        raise RuntimeError("F0 model/LP exactness gate failed")
    if not all(bool(row["accepted_by_f0_integer_model"])
               for row in incumbent_rows):
        raise RuntimeError("F0 incumbent verification gate failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
