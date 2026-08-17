#!/usr/bin/env python3
"""Run the mandatory full-matrix Round 44 rank-1 CGLP pilot.

The selected Stage 3 trajectories retain every canonical parent model. For the
``on`` arm this script solves the normalized CGLP at every parent, audits all
multiplier identities, and repeats separation until no violated cut exists. A
generated cut fails closed because it requires a fresh integrated trajectory.
"""

from __future__ import annotations

import csv
from pathlib import Path
import time
from typing import Any

import analyze_round44_stage3 as stage3
import round44_common as common
from round44_cglp import separate_model


PILOT_TAGS = ("noadaptive", "veto-f05")
WITNESSES = (stage3.MAJOR, stage3.CONTROL)
EPSILON_SEP = 1e-7


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_rows(path: Path, rows: list[dict[str, Any]],
               fields: list[str]) -> None:
    """Write a schema-bearing ledger even when a valid pilot has zero cuts."""
    if rows:
        common.write_csv(path, rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=fields).writeheader()


def contextualize(row: dict[str, Any], *, tag: str, instance_id: str,
                  parent_id: str, model_path: Path) -> dict[str, Any]:
    return {
        "candidate_tag": tag,
        "candidate_family": stage3.BY_TAG[tag]["family"],
        "instance_id": instance_id,
        "witness_role": common.MECHANISM_ROLES[instance_id],
        "parent_id": parent_id,
        "canonical_parent_model": common.relative(model_path),
        "canonical_parent_model_sha256": common.sha256(model_path),
        **row,
    }


def main() -> int:
    cut_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    accepted_cuts = 0
    for tag in PILOT_TAGS:
        for instance_id in WITNESSES:
            base = stage3.metrics("development", instance_id, tag)
            source_dir = stage3.candidate_dir("development", instance_id, tag)
            external = source_dir / "external"
            decisions = read_rows(external / "refinement_decision_ledger.csv")
            seen: set[str] = set()
            cglp_work = 0.0
            cglp_solver_seconds = 0.0
            cglp_wall_seconds = 0.0
            parent_count = 0
            for decision in decisions:
                parent_id = decision["parent_id"]
                if parent_id in seen:
                    continue
                seen.add(parent_id)
                lower = float(decision["lower"])
                upper = float(decision["upper"])
                gamma = .5 * (lower + upper)
                envelope_model = external / "models" / f"{parent_id}.r44E.lp"
                model_path = envelope_model if envelope_model.is_file() else (
                    external / "models" / f"{parent_id}.lp")
                if not model_path.is_file():
                    raise RuntimeError(
                        f"missing canonical parent model: {model_path}")
                started = time.monotonic()
                audits, cuts, model = separate_model(
                    model_path, gamma,
                    f"{tag}:{instance_id}:{parent_id}", EPSILON_SEP)
                replay_wall = time.monotonic() - started
                model.dispose()
                parent_count += 1
                cglp_work += sum(float(row["cglp_work"]) for row in audits)
                cglp_solver_seconds += sum(
                    float(row["cglp_solver_seconds"]) for row in audits)
                cglp_wall_seconds += replay_wall
                for row in audits:
                    audit_rows.append(contextualize(
                        row, tag=tag, instance_id=instance_id,
                        parent_id=parent_id, model_path=model_path))
                for row in cuts:
                    cut_rows.append(contextualize(
                        row, tag=tag, instance_id=instance_id,
                        parent_id=parent_id, model_path=model_path))
                    accepted_cuts += int(
                        row["certificate_status"] ==
                        "audited_valid_violated_rank1_cut")

            common_base = {
                "candidate_tag": tag,
                "candidate_family": stage3.BY_TAG[tag]["family"],
                "instance_id": instance_id,
                "witness_role": common.MECHANISM_ROLES[instance_id],
                "base_run_id": base["run_id"],
                "strict_certified_original_problem": base["certified"],
                "correctness": base["correctness"],
                "parent_cglps": parent_count,
                "accepted_rank1_cuts": 0,
                "epsilon_sep": EPSILON_SEP,
            }
            result_rows.append({
                **common_base,
                "rank1_mode": "off",
                "execution_basis": "sealed_stage3_exact_run",
                "work": base["work"],
                "process_seconds": base["process_seconds"],
                "separator_work": 0.0,
                "separator_solver_seconds": 0.0,
                "separator_wall_seconds": 0.0,
                "trajectory_identity": "base_exact_trajectory",
            })
            result_rows.append({
                **common_base,
                "rank1_mode": "on",
                "execution_basis": "full_matrix_no_cut_exact_replay",
                "work": base["work"] + cglp_work,
                "process_seconds": base["process_seconds"] +
                    cglp_wall_seconds,
                "separator_work": cglp_work,
                "separator_solver_seconds": cglp_solver_seconds,
                "separator_wall_seconds": cglp_wall_seconds,
                "trajectory_identity": (
                    "identical_because_every_complete_normalized_cglp_"
                    "proved_no_violated_cut"),
            })

    write_rows(common.OUT / "cglp_cut_ledger.csv", cut_rows, [
        "candidate_tag", "candidate_family", "instance_id",
        "witness_role", "parent_id", "canonical_parent_model",
        "canonical_parent_model_sha256", "source_interval", "round",
        "source_disjunction", "propagation_scope", "sense", "rhs",
        "violation", "coefficient_count", "coefficients_json",
        "certificate_status",
    ])
    common.write_csv(
        common.OUT / "multiplier_certificate_audit.csv", audit_rows)
    common.write_csv(common.OUT / "rank1_pilot_results.csv", result_rows)
    all_audited = all(row["audit_valid"] for row in audit_rows)
    if not all_audited:
        raise RuntimeError("rank-1 pilot contains an invalid multiplier audit")
    disposition = {
        "schema": "round44-stage4-disposition-v1",
        "mandatory_pilot_complete": True,
        "candidate_tags": list(PILOT_TAGS),
        "witnesses": list(WITNESSES),
        "off_on_rows": len(result_rows),
        "parent_cglps": len(audit_rows),
        "all_multiplier_certificates_valid": all_audited,
        "accepted_rank1_cuts": accepted_cuts,
        "no_cut_result": accepted_cuts == 0,
        "mechanism6_extension_triggered": accepted_cuts > 0,
        "selected_lifted_cut_mode": "off" if accepted_cuts == 0 else None,
        "mathematical_disposition": (
            "The midpoint disjunction G<=m or G>=m covers the complete "
            "continuous parent domain. Full-matrix normalized CGLPs confirmed "
            "that no inequality valid for both branches violated any audited "
            "parent LP solution." if accepted_cuts == 0 else
            "At least one audited violated common inequality was generated; "
            "an integrated mechanism-6 extension is required."),
        "validation_observed": False,
    }
    common.write_json(common.OUT / "stage4_disposition.json", disposition)
    report = f"""# Round 44 rank-1 lifted-cut ablation

The mandatory pilot evaluated `{', '.join(PILOT_TAGS)}` on the major
fragmentation witness and strongest K4 positive control, with lifted separation
off and on. The on arm solved a normalized full-matrix CGLP at every encountered
parent and independently replayed both multiplier identities, RHS inequalities,
nonnegativity, and the finite normalization.

- Audited parent CGLPs: {len(audit_rows)}
- Valid multiplier audits: {sum(bool(row['audit_valid']) for row in audit_rows)}
- Violated valid rank-1 cuts: {accepted_cuts}
- Mechanism-6 lifted extension: {'required' if accepted_cuts else 'not triggered'}

This is a genuine no-cut result when the generated-cut count is zero. The `on`
trajectory is then mathematically identical to `off`; its reported time and Work
include the measured separator overhead.
"""
    common.write_text(common.OUT / "lifted_cut_ablation.md", report)
    common.write_text(common.OUT / "rank1_lifted_cut_analysis.md", report)
    if accepted_cuts:
        raise RuntimeError(
            "rank-1 cuts generated: integrated mechanism-6 extension required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
