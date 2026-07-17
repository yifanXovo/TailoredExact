#!/usr/bin/env python3
"""Audit Round-20 V12 global-tree certificate evidence without rerunning CPLEX.

The audit is deliberately observational.  It reads the four selected Round-20
Stage-2 result bundles, preserves the native values recorded in the final bound
trajectory, and applies the Round-21 fail-closed historical classification:

* CPLEX status 101 -> historical strict candidate (not a new strict certificate)
* CPLEX status 102 -> tolerance-only

Round-20 did not persist the strict zero-gap parameter readbacks or the native
objective/bound API return codes required by the hardened Round-21 policy.  The
script therefore never upgrades a historical record to a Round-21 strict
certificate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any


RUNS = (
    "stage2__V12_M1__baseline__900s",
    "stage2__V12_M1__root_flow_only__900s",
    "stage2__V12_M2__baseline__900s",
    "stage2__V12_M2__root_flow_only__900s",
)

AUDIT_COLUMNS = (
    "run_id",
    "instance",
    "arm",
    "historical_classification",
    "round21_strict_certificate_claimable",
    "classification_reason",
    "native_status_code",
    "native_status_text",
    "global_tree_return_code",
    "process_return_code",
    "solver_finalization_reached",
    "verification_feasible",
    "verification_objective_matches",
    "native_best_bound_available",
    "json_native_objective",
    "json_native_best_bound",
    "trajectory_native_incumbent",
    "trajectory_native_best_bound",
    "trajectory_recorded_native_gap",
    "computed_absolute_native_gap",
    "computed_project_relative_gap_max1",
    "computed_cplex_denominator_relative_gap",
    "serialized_status",
    "serialized_objective",
    "serialized_lower_bound",
    "serialized_upper_bound",
    "serialized_gap",
    "serialized_lower_bound_differs_from_native_bound",
    "serialized_zero_gap_contradicts_native_gap",
    "lifecycle_status_text",
    "lifecycle_cpxmipopt_count",
    "final_trajectory_event",
    "missing_round21_evidence",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="ExactEBRP repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: Round-21 historical_audit directory)",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decimal_text(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def relative_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream, parse_float=Decimal, parse_int=int)


def read_lifecycle(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.reader(stream):
            if len(row) != 2:
                raise ValueError(f"expected two lifecycle columns in {path}: {row!r}")
            values[row[0]] = row[1]
    return values


def read_final_trajectory(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"empty bound trajectory: {path}")
    final = rows[-1]
    if final.get("event_source") != "solver_final":
        raise ValueError(f"last trajectory row is not solver_final: {path}")
    return final


def classify(status_code: int) -> tuple[str, str]:
    if status_code == 101:
        return (
            "historical_strict_candidate",
            "CPXMIP_OPTIMAL (101) is the only selected status that can be a strict "
            "candidate; Round-20 omitted evidence required for a Round-21 strict claim.",
        )
    if status_code == 102:
        return (
            "tolerance_only",
            "CPXMIP_OPTIMAL_TOL (102) is tolerance termination and is never strict.",
        )
    return (
        "uncertified",
        f"native status {status_code} is neither strict candidate 101 nor tolerance-only 102",
    )


def audit_run(repo_root: Path, run_id: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    round20 = repo_root / "results" / "gf_global_gini_tree_regression_round"
    raw_path = round20 / "raw" / f"{run_id}.json"
    command_path = round20 / "commands" / f"{run_id}.json"
    run_dir = round20 / "runs" / run_id
    lifecycle_path = run_dir / "model_lifecycle_manifest.csv"
    trajectory_path = run_dir / "global_bound_trajectory.csv"

    sources = (
        ("raw_result_json", raw_path),
        ("command_json", command_path),
        ("model_lifecycle_manifest", lifecycle_path),
        ("global_bound_trajectory", trajectory_path),
    )
    for role, path in sources:
        if not path.is_file():
            raise FileNotFoundError(f"missing {role} for {run_id}: {path}")

    result = read_json(raw_path)
    lifecycle = read_lifecycle(lifecycle_path)
    final = read_final_trajectory(trajectory_path)

    status_code = int(result["global_gini_tree_status_code"])
    status_text = str(result["global_gini_tree_solver_status"])
    lifecycle_status = lifecycle.get("solver_final_status", "")
    if lifecycle_status != status_text:
        raise ValueError(
            f"status disagreement for {run_id}: JSON={status_text!r}, "
            f"lifecycle={lifecycle_status!r}"
        )

    native_incumbent = Decimal(final["native_incumbent"])
    native_bound = Decimal(final["native_global_LB"])
    recorded_gap = Decimal(final["native_gap"])
    absolute_gap = abs(native_incumbent - native_bound)
    project_denominator = max(Decimal(1), abs(native_incumbent))
    project_relative_gap = absolute_gap / project_denominator
    cplex_denominator_gap = absolute_gap / (Decimal("1e-10") + abs(native_incumbent))

    serialized_lower = result["lower_bound"]
    serialized_gap = result["gap"]
    classification, reason = classify(status_code)
    instance = "V12_M1" if "V12_M1" in run_id else "V12_M2"
    arm = "baseline" if "__baseline__" in run_id else "root_flow_only"
    verification = result.get("verification", {})

    missing_round21_evidence = (
        "relative_gap_parameter_set_rc_and_readback|"
        "absolute_gap_parameter_set_rc_and_readback|"
        "CPXgetstat_return_code|CPXgetobjval_return_code|"
        "CPXgetbestobjval_return_code|CPXgetmiprelgap_return_code"
    )
    row = {
        "run_id": run_id,
        "instance": instance,
        "arm": arm,
        "historical_classification": classification,
        "round21_strict_certificate_claimable": "false",
        "classification_reason": reason,
        "native_status_code": str(status_code),
        "native_status_text": status_text,
        "global_tree_return_code": decimal_text(result.get("global_gini_tree_return_code")),
        "process_return_code": decimal_text(result.get("process_return_code")),
        "solver_finalization_reached": decimal_text(
            result.get("global_gini_tree_solver_finalization_reached")
        ),
        "verification_feasible": decimal_text(verification.get("feasible")),
        "verification_objective_matches": decimal_text(
            verification.get("objective_matches")
        ),
        "native_best_bound_available": decimal_text(
            result.get("global_gini_tree_native_best_bound_available")
        ),
        "json_native_objective": decimal_text(
            result.get("global_gini_tree_native_objective")
        ),
        "json_native_best_bound": decimal_text(
            result.get("global_gini_tree_native_best_bound")
        ),
        "trajectory_native_incumbent": decimal_text(native_incumbent),
        "trajectory_native_best_bound": decimal_text(native_bound),
        "trajectory_recorded_native_gap": decimal_text(recorded_gap),
        "computed_absolute_native_gap": decimal_text(absolute_gap),
        "computed_project_relative_gap_max1": decimal_text(project_relative_gap),
        "computed_cplex_denominator_relative_gap": decimal_text(cplex_denominator_gap),
        "serialized_status": decimal_text(result.get("status")),
        "serialized_objective": decimal_text(result.get("objective")),
        "serialized_lower_bound": decimal_text(serialized_lower),
        "serialized_upper_bound": decimal_text(result.get("upper_bound")),
        "serialized_gap": decimal_text(serialized_gap),
        "serialized_lower_bound_differs_from_native_bound": decimal_text(
            serialized_lower != native_bound
        ),
        "serialized_zero_gap_contradicts_native_gap": decimal_text(
            serialized_gap == 0 and absolute_gap > 0
        ),
        "lifecycle_status_text": lifecycle_status,
        "lifecycle_cpxmipopt_count": lifecycle.get("CPXmipopt_count", ""),
        "final_trajectory_event": final.get("event_source", ""),
        "missing_round21_evidence": missing_round21_evidence,
    }

    hashes = [
        {
            "run_id": run_id,
            "artifact_role": role,
            "source_path": relative_path(path, repo_root),
            "size_bytes": str(path.stat().st_size),
            "sha256": sha256(path),
        }
        for role, path in sources
    ]
    return row, hashes


def write_csv(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict[str, str]]) -> None:
    strict_candidates = sum(
        row["historical_classification"] == "historical_strict_candidate" for row in rows
    )
    tolerance_only = sum(row["historical_classification"] == "tolerance_only" for row in rows)
    contradictory = sum(
        row["serialized_zero_gap_contradicts_native_gap"] == "true" for row in rows
    )

    lines = [
        "# Historical Round-20 V12 certificate audit",
        "",
        "This is a no-rerun audit of the official Round-20 Stage-2 global-Gini-tree "
        "artifacts. It treats native numeric CPLEX status as authoritative and applies "
        "a fail-closed historical classification: status 101 is only a historical "
        "strict candidate; status 102 is tolerance-only.",
        "",
        "## Conclusion",
        "",
        f"Of the four selected records, **{strict_candidates} is a historical strict "
        f"candidate** and **{tolerance_only} are tolerance-only**. In "
        f"**{contradictory} tolerance-only records**, the Round-20 public serializer "
        "reported `lower_bound == upper_bound` and `gap == 0` even though the final "
        "native trajectory retained a positive best-bound gap.",
        "",
        "None of the four is promoted to a hardened Round-21 strict certificate. The "
        "historical schema does not record both zero-gap parameter set/readback results "
        "or the native objective/bound/gap API return codes required by the new policy.",
        "",
        "## Per-run evidence",
        "",
        "| Instance | Arm | Status | Native status text | Final native incumbent | "
        "Final native best bound | Absolute gap | Round-20 serialized LB / UB / gap | "
        "Historical class |",
        "|---|---|---:|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['instance']} | {row['arm']} | {row['native_status_code']} | "
            f"{row['native_status_text']} | {row['trajectory_native_incumbent']} | "
            f"{row['trajectory_native_best_bound']} | "
            f"{row['computed_absolute_native_gap']} | "
            f"{row['serialized_lower_bound']} / {row['serialized_upper_bound']} / "
            f"{row['serialized_gap']} | {row['historical_classification']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation rules",
            "",
            "- `CPXMIP_OPTIMAL` (101) is a strict-status candidate. Historical evidence "
            "still cannot satisfy the full Round-21 evidence contract.",
            "- `CPXMIP_OPTIMAL_TOL` (102) is tolerance-only regardless of how small the "
            "remaining best-bound gap is or whether rounded public fields coincide.",
            "- The final `solver_final` row of `global_bound_trajectory.csv` supplies "
            "higher-precision native incumbent, best bound, and the project-recorded "
            "gap. JSON values are retained separately because its 12-digit rendering "
            "rounds those quantities.",
            "- `computed_project_relative_gap_max1` uses "
            "`abs(incumbent-bound)/max(1,abs(incumbent))`. "
            "`computed_cplex_denominator_relative_gap` is an audit-derived diagnostic "
            "using `abs(incumbent-bound)/(1e-10+abs(incumbent))`; it is not a historical "
            "`CPXgetmiprelgap` observation.",
            "",
            "## Reproduction and provenance",
            "",
            "Run from the repository root:",
            "",
            "```text",
            "D:\\msys64\\ucrt64\\bin\\python.exe scripts/round21_historical_certificate_audit.py",
            "```",
            "",
            "The script is standard-library-only and may also be run with any Python "
            "3 interpreter available on another host.",
            "",
            "The machine-readable records are in `v12_round20_certificate_audit.csv` "
            "and `historical_certificate_audit.json`. Exact paths, byte sizes, and "
            "SHA-256 digests for every input used by the audit are in "
            "`source_artifact_hashes.csv`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else repo_root
        / "results"
        / "gf_global_gini_tree_strict_flow_round"
        / "historical_audit"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    hashes: list[dict[str, str]] = []
    for run_id in RUNS:
        row, run_hashes = audit_run(repo_root, run_id)
        rows.append(row)
        hashes.extend(run_hashes)

    write_csv(output_dir / "v12_round20_certificate_audit.csv", rows, AUDIT_COLUMNS)
    write_csv(
        output_dir.parent / "historical_certificate_reclassification.csv",
        rows,
        AUDIT_COLUMNS,
    )
    write_csv(
        output_dir / "source_artifact_hashes.csv",
        hashes,
        ("run_id", "artifact_role", "source_path", "size_bytes", "sha256"),
    )
    payload = {
        "audit_scope": "Round-20 Stage-2 V12 global-tree baseline/root-flow artifacts",
        "reruns_performed": False,
        "classification_policy": {
            "101": "historical_strict_candidate",
            "102": "tolerance_only",
            "round21_strict_certificate_requires_new_evidence": True,
        },
        "records": rows,
        "source_artifacts": hashes,
    }
    (output_dir / "historical_certificate_audit.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    write_report(output_dir / "README.md", rows)

    print(f"wrote {len(rows)} audit rows and {len(hashes)} source hashes to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
