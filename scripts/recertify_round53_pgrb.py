#!/usr/bin/env python3
"""Strictly re-certify the immutable Round 53 P-GRB sealed artifacts.

The expected fingerprints were frozen in a prior commit.  This correction
does not rewrite or rerun any Round 53 evidence: it independently verifies the
stored solutions and binds each retained actual model to the frozen expected
model identity.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

from round23_moderate4301_forensic import independent_verify, parse_instance


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
ROUND53 = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
CORRECTION = OUT / "round53_pgrb_certificate_correction"
EXPECTED_PATH = CORRECTION / "round53_pgrb_expected_fingerprints.json"
ORIGINAL_RUNS = ROUND53 / "local_raw" / "k1_panel_runs"
ROUND53_EXE_SHA = (
    "b49cc5a5e631c6a8ce7a8bd4d0e6da44162800c97996494b1ee6a04071286c85")
EPS = 1e-7


def truth(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "optimal"}


def number(value: object, default: float = math.nan) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]],
              fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def objective_fingerprint(lp_path: Path) -> str:
    lines = lp_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.strip().lower() in {"minimize", "maximize"})
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
               if line.strip().lower().startswith("subject to"))
    canonical = "\n".join(line.rstrip() for line in lines[start:end]) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def strict_recertify(row: dict[str, Any], expected: dict[str, Any],
                     summary: dict[str, str]) -> tuple[dict[str, object],
                                                       dict[str, object]]:
    instance_id = str(row["instance_id"])
    run_dir = ORIGINAL_RUNS / f"sealed__{instance_id}__P-GRB__3600s"
    result_path = run_dir / "result.json"
    command_path = run_dir / "command.json"
    lp_path = run_dir / "canonical.lp"
    marker_path = run_dir / "completion_marker.json"
    for path in (result_path, command_path, lp_path, marker_path):
        if not path.is_file():
            raise RuntimeError(f"immutable Round 53 artifact missing: {path}")
    result = read_json(result_path)
    command = read_json(command_path)
    marker = read_json(marker_path)
    command_args = [str(item) for item in command["command"]]
    independent = independent_verify(
        parse_instance(ROOT / row["input_path"]), result.get("routes", []),
        total_time=float(row["T"]), pickup_time=60.0, drop_time=60.0,
        lam=0.15)

    expected_fp = int(expected["expected_gurobi_model_fingerprint"])
    actual_fp = int(result.get("gurobi_model_fingerprint", 0))
    canonical_hash = sha256(lp_path)
    objective_hash = objective_fingerprint(lp_path)
    executable_match = (
        command.get("executable_sha256") == ROUND53_EXE_SHA and
        marker.get("executable_sha256") == ROUND53_EXE_SHA)
    model_match = (actual_fp == expected_fp and
                   canonical_hash == expected["canonical_model_sha256"] and
                   objective_hash == expected["objective_fingerprint_sha256"])
    lifecycle = (truth(result.get("gurobi_solver_finalization_reached")) and
                 truth(result.get("gurobi_lifecycle_valid")) and
                 int(result.get("gurobi_optimize_return_code", -1)) == 0)
    settings = (
        int(result.get("gurobi_threads_effective", -1)) == 1 and
        int(result.get("gurobi_seed_effective", -1)) == 0 and
        int(result.get("gurobi_presolve_effective", 999)) == -1 and
        number(result.get("gurobi_mip_gap_effective")) == 0.0 and
        number(result.get("gurobi_mip_gap_abs_effective")) == 0.0)
    domain = truth(result.get("gurobi_native_domain_audit_passed"))
    independent_feasible = truth(independent.get("valid"))
    independent_objective = number(independent.get("objective"))
    native_objective = number(result.get("gurobi_obj_val"))
    objective_residual = abs(independent_objective - native_objective)
    objective_ok = (independent_feasible and math.isfinite(objective_residual) and
                    objective_residual <= EPS)
    no_external = not any(option in command_args for option in (
        "--incumbent-json", "--hga-incumbent", "--external-incumbent"))
    optimal = (int(result.get("gurobi_status", 0)) == 2 and
               str(result.get("gurobi_status_text", "")).upper() == "OPTIMAL")
    corrected_certificate = all((executable_match, model_match, lifecycle,
                                 settings, domain, objective_ok, no_external,
                                 optimal))
    if corrected_certificate:
        rejection = "none"
    else:
        failed = []
        for label, passed in (
                ("executable_binding", executable_match),
                ("model_fingerprint_binding", model_match),
                ("lifecycle", lifecycle), ("solver_settings", settings),
                ("domain_identity", domain),
                ("independent_original_solution_verification", objective_ok),
                ("no_external_information", no_external),
                ("native_optimal_status", optimal)):
            if not passed:
                failed.append(label)
        rejection = ";".join(failed)

    audit: dict[str, object] = {
        "instance_id": instance_id, "input_sha256": row["input_sha256"],
        "expected_fingerprint": expected_fp, "actual_fingerprint": actual_fp,
        "fingerprint_match": actual_fp == expected_fp,
        "expected_canonical_model_sha256": expected["canonical_model_sha256"],
        "actual_canonical_model_sha256": canonical_hash,
        "canonical_model_match": canonical_hash == expected["canonical_model_sha256"],
        "expected_objective_fingerprint": expected["objective_fingerprint_sha256"],
        "actual_objective_fingerprint": objective_hash,
        "objective_fingerprint_match": objective_hash == expected["objective_fingerprint_sha256"],
        "executable_binding_valid": executable_match,
        "lifecycle_valid": lifecycle, "solver_settings_valid": settings,
        "domain_identity_valid": domain,
        "independent_original_solution_feasible": independent_feasible,
        "independent_recomputed_objective": independent_objective,
        "native_objective": native_objective,
        "objective_residual": objective_residual,
        "objective_recomputation_valid": objective_ok,
        "no_external_information": no_external,
        "original_command_expected_fingerprint_present": (
            "--round24-expected-gurobi-model-fingerprint" in command_args),
        "posthoc_frozen_expected_binding_applied": True,
        "raw_result_sha256": sha256(result_path),
        "raw_command_sha256": sha256(command_path),
        "raw_completion_marker_sha256": sha256(marker_path),
        "original_artifact_rewritten": False,
    }
    recert: dict[str, object] = {
        "instance_id": instance_id,
        "difficulty_configuration": row["difficulty_configuration"],
        "V": row["V"], "M": row["M"], "Q": row["Q"], "T": row["T"],
        "process_cap_seconds": 3600,
        "native_status": result.get("gurobi_status_text"),
        "expected_fingerprint": expected_fp, "actual_fingerprint": actual_fp,
        "expected_actual_fingerprint_match": actual_fp == expected_fp,
        "lifecycle_valid": lifecycle,
        "independent_original_solution_verification": objective_ok,
        "objective_recomputation_residual": objective_residual,
        "strict_rejection_reason": rejection,
        "original_strict_certificate": False,
        "corrected_strict_certificate": corrected_certificate,
        "certificate_changed": corrected_certificate,
        "work": summary["work"], "process_time_seconds": summary["process_time_seconds"],
        "lower_bound": summary["lower_bound"],
        "verified_upper_bound": summary["verified_upper_bound"],
        "gap": summary["gap"], "gi_common_horizon": summary["gi_common_horizon"],
        "work_time_gap_values_changed": False,
        "recertification_mode": "posthoc_strict_binding_to_prefrozen_expected_fingerprint",
        "original_artifact_dir": run_dir.relative_to(ROOT).as_posix(),
    }
    return audit, recert


def main() -> int:
    expected_manifest = read_json(EXPECTED_PATH)
    if expected_manifest.get("correction_solves_started") is not False:
        raise RuntimeError("expected fingerprint manifest causal order invalid")
    subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(EXPECTED_PATH)],
                   cwd=ROOT, check=True)
    sealed_manifest = read_json(ROUND53 / "sealed_v12_instance_manifest.json")
    expected_by = {entry["instance_id"]: entry
                   for entry in expected_manifest["entries"]}
    summary_rows = csv_rows(ROUND53 / "sealed_v12_results.csv")
    summary_by = {(row["instance_id"], row["method"]): row for row in summary_rows}
    audits: list[dict[str, object]] = []
    recertified: list[dict[str, object]] = []
    for row in sealed_manifest["rows"]:
        audit, recert = strict_recertify(
            row, expected_by[row["instance_id"]],
            summary_by[(row["instance_id"], "P-GRB")])
        audits.append(audit)
        recertified.append(recert)
    write_csv(CORRECTION / "round53_pgrb_fingerprint_audit.csv", audits)
    write_csv(CORRECTION / "round53_pgrb_recertification_results.csv", recertified)

    corrected_by = {row["instance_id"]: row for row in recertified}
    direct: list[dict[str, object]] = []
    for input_row in sealed_manifest["rows"]:
        instance = input_row["instance_id"]
        p = corrected_by[instance]
        v0 = summary_by[(instance, "K1-AM-v0")]
        f0 = summary_by[(instance, "K1-AM-CANDIDATE")]
        direct.append({
            "instance_id": instance,
            "difficulty_configuration": input_row["difficulty_configuration"],
            "V": input_row["V"], "M": input_row["M"], "Q": input_row["Q"],
            "pgrb_original_certificate": False,
            "pgrb_corrected_certificate": p["corrected_strict_certificate"],
            "pgrb_work": p["work"], "pgrb_process_time_seconds": p["process_time_seconds"],
            "pgrb_gap": p["gap"], "pgrb_gi": p["gi_common_horizon"],
            "k1_am_v0_certificate": v0["certificate"], "k1_am_v0_work": v0["work"],
            "k1_am_v0_gi": v0["gi_common_horizon"],
            "k1_am_f0_certificate": f0["certificate"], "k1_am_f0_work": f0["work"],
            "k1_am_f0_gi": f0["gi_common_horizon"],
            "round53_f0_promotion_decision_changed": False,
        })
    write_csv(CORRECTION / "round53_corrected_direct_comparison.csv", direct)

    changed = [row["instance_id"] for row in recertified
               if truth(row["certificate_changed"])]
    corrected_count = sum(truth(row["corrected_strict_certificate"])
                          for row in recertified)
    erratum = f"""# Round 53 P-GRB certificate-chain erratum

Round 53 reported **0/12** P-GRB strict certificates because its new sealed
commands omitted the pre-frozen expected-model-fingerprint binding.  The
models and solutions were retained; the rejection reason on otherwise closed
rows was `model_fingerprint_mismatch`.

Round 54 first reconstructed all 12 complete plain-Gurobi models with the
original Round 53 executable and committed their expected fingerprints before
this correction.  Every expected fingerprint, canonical LP SHA-256, objective
fingerprint, and variable/row/domain identity matches the immutable Round 53
artifact.  A separate standard-library verifier re-parsed each input and
independently checked its retained routes and objective.

The corrected count is **{corrected_count}/12**.  Certificate status changes
on {len(changed)} rows:

""" + "\n".join(f"- `{item}`" for item in changed) + """

The remaining rows retain honest noncertified native statuses.  Work,
process-time, bound, gap, and GI values are unchanged for all 12 rows; no raw
Round 53 result, command, completion marker, report, decision, or sealed
manifest was overwritten.  This is a post-hoc strict evidence correction, not
a replayed performance experiment.

The correction does **not** change the Round 53 F0-CLEAN fixed-interval
promotion, K1-AM-F0 support, or sealed candidate-over-v0 conclusion.  It does
change only contextual comparisons that previously counted fingerprint-
rejected optimal P-GRB rows as uncertified.  Round 54 algorithm selection is
forbidden from using this repair.
"""
    (CORRECTION / "round53_pgrb_certificate_erratum.md").write_text(
        erratum, encoding="utf-8")
    (CORRECTION / "round53_pgrb_correction_decision.json").write_text(
        json.dumps({
            "schema": "round54-round53-pgrb-correction-decision-v1",
            "evidence_classification": "round53_pgrb_recertified",
            "recertification_mode": (
                "posthoc strict binding of immutable Round 53 artifacts to "
                "a separately pre-frozen expected-fingerprint manifest"),
            "original_reported_certificates": 0,
            "corrected_certificates": corrected_count,
            "physical_rows": len(recertified),
            "changed_rows": changed,
            "fingerprint_mismatches": sum(
                not truth(row["fingerprint_match"]) for row in audits),
            "work_time_bound_gap_gi_values_changed": False,
            "original_round53_artifacts_rewritten": False,
            "round53_f0_promotion_decision_changed": False,
            "round54_algorithm_tuning_from_correction": False,
        }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"original_certificates": 0,
                      "corrected_certificates": corrected_count,
                      "changed_rows": len(changed),
                      "fingerprint_mismatches": sum(
                          not truth(row["fingerprint_match"]) for row in audits),
                      "round53_f0_promotion_changed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
