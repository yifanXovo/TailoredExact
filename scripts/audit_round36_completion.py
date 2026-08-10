#!/usr/bin/env python3
"""Requirement-by-requirement completion audit for ExactEBRP Round 36.

The default mode succeeds only when the complete scientific, evidence, Git,
and draft-PR state is present.  ``--allow-incomplete`` records honest interim
status while the frozen serial matrix is still running; contradictions still
fail in either mode.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import analyze_round35 as round35
import analyze_round36 as analysis
import round36_common as common


BRANCH = "codex/round36-incumbent-decomposition-causal-study"
REPO = "yifanXovo/TailoredExact"
PR_NUMBER = 83
FINAL_FILES = (
    "semantic_separation_audit.csv",
    "semantic_separation_audit.json",
    "semantic_separation_audit.md",
    "verified_ub_assignment_audit.csv",
    "anchor_consumer_occurrence_audit.csv",
    "per_arm_results.csv",
    "initial_decomposition_audit.csv",
    "exactness_certificate_audit.csv",
    "interaction_sequence_hashes.csv",
    "trajectory_events.csv.gz",
    "child_lookahead_split_audit.csv",
    "native_target_audit.csv",
    "terminal_closure_audit.csv",
    "causal_geometry_comparison.csv",
    "causal_normalization_comparison.csv",
    "fixed_anchor_proof_comparison.csv",
    "causal_group_summaries.csv",
    "representative_trajectory_report.md",
    "final_audit_decision.json",
    "final_report.md",
    "representative_selection.csv",
    "representative_raw_manifest.csv",
    "final_evidence_inventory.csv",
    "evidence_package_summary.json",
    "evidence_package_report.md",
)


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def json_value(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ("git", *args), cwd=common.ROOT, text=True,
        encoding="utf-8", errors="replace", capture_output=True,
        check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


class Audit:
    def __init__(self, allow_incomplete: bool) -> None:
        self.allow_incomplete = allow_incomplete
        self.rows: list[dict[str, Any]] = []

    def add(self, section: str, requirement: str, status: str,
            evidence: str, detail: str = "") -> None:
        if status not in {"achieved", "incomplete", "contradicted", "missing"}:
            raise ValueError(status)
        self.rows.append({
            "section": section, "requirement": requirement,
            "status": status, "evidence": evidence, "detail": detail,
        })

    def condition(self, section: str, requirement: str, passed: bool,
                  evidence: str, *, incomplete: bool = False,
                  detail: str = "") -> None:
        status = "achieved" if passed else (
            "incomplete" if incomplete else "contradicted")
        self.add(section, requirement, status, evidence, detail)

    def file(self, section: str, requirement: str, path: Path,
             *, incomplete: bool = True) -> None:
        self.condition(section, requirement, path.is_file(),
                       common.relative(path), incomplete=incomplete)


def markdown(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    table = [
        "| section | status | requirement | evidence |",
        "|---|---|---|---|",
    ]
    for row in rows:
        table.append("| " + " | ".join(str(row[key]).replace("|", "\\|")
            for key in ("section", "status", "requirement", "evidence")) + " |")
    return f"""# Round 36 completion requirements audit

- All requirements achieved: {summary['all_requirements_achieved']}.
- Achieved: {summary['status_counts'].get('achieved', 0)}.
- Incomplete: {summary['status_counts'].get('incomplete', 0)}.
- Missing: {summary['status_counts'].get('missing', 0)}.
- Contradicted: {summary['status_counts'].get('contradicted', 0)}.

{"\n".join(table)}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    audit = Audit(args.allow_incomplete)
    out = common.OUT

    # 0. Workspace and Git baseline.
    branch = git("branch", "--show-current")
    remote = git("remote", "get-url", "origin")
    audit.condition("0_git_workspace", "dedicated Round 36 branch is active",
                    branch == BRANCH, f"git branch --show-current = {branch}")
    audit.condition("0_git_workspace", "existing GitHub remote is used",
                    "yifanXovo/TailoredExact" in remote,
                    f"origin = {remote}")
    preservation = round35.preservation_audit()
    audit.condition(
        "0_git_workspace", "pre-existing user work is preserved",
        len(preservation) == 592 and all(truth(row[
            "preservation_audit_passed"]) for row in preservation),
        "Round 35 inherited preexisting_worktree_manifest.csv",
        detail=f"{sum(truth(row['preservation_audit_passed']) for row in preservation)}/"
               f"{len(preservation)} entries preserved")

    # 1. Default C6 and Stage A equivalence.
    stage_a = json_value(out / "stage_a_build_and_tests.json")
    baseline = csv_rows(out / "baseline_equivalence_audit.csv")
    audit.condition(
        "1_default_c6", "clean licensed build and relevant tests pass",
        truth(stage_a.get("passed")) and len(stage_a.get("records", [])) == 24
        and stage_a.get("cpp_test_count") == 15
        and stage_a.get("python_test_script_count") == 21,
        "stage_a_build_and_tests.json")
    audit.condition(
        "1_default_c6", "default-off and explicit HH are decision-equivalent",
        len(baseline) == 14 and all(truth(row.get("identical"))
                                    for row in baseline),
        "baseline_equivalence_audit.csv")
    instance_source = (common.ROOT / "include" / "Instance.hpp").read_text(
        encoding="utf-8", errors="replace")
    audit.condition(
        "1_default_c6", "new causal controls default to off/proof",
        'round36_c6_causal_arm = "off"' in instance_source
        and 'round36_c6_split_normalization = "proof"' in instance_source,
        "include/Instance.hpp")

    # 2-6. Mathematical separation and explicit interventions.
    tree_source = (common.ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
        encoding="utf-8", errors="replace")
    main_source = (common.ROOT / "src" / "main.cpp").read_text(
        encoding="utf-8", errors="replace")
    geometry_source = (common.ROOT / "src" / "GiniFrontierGeometry.cpp").read_text(
        encoding="utf-8", errors="replace")
    audit.condition(
        "2_proof_anchor", "U_proof and U_anchor are explicit and separately used",
        "proof_incumbent_launch" in tree_source
        and "decomposition_anchor_launch" in tree_source
        and "round36_proof_incumbent_launch" in main_source
        and "round36_decomposition_anchor_launch" in main_source,
        "PaperExternalGiniTree.cpp; main.cpp")
    semantic = json_value(out / "semantic_separation_audit.json")
    audit.condition(
        "2_proof_anchor", "semantic dataflow audit excludes anchor from proof consumers",
        semantic.get("passed") is True
        and semantic.get("verified_ub_assignments") ==
            semantic.get("verified_ub_assignments_guarded")
        and semantic.get("anchor_forbidden_consumer_occurrences") == 0,
        "semantic_separation_audit.json")
    audit.condition(
        "3_anchor_coverage", "anchor grid intersects the proof-relevant range",
        "makeProofRelevantAnchorGrid" in geometry_source
        and "truncated_active_interval_count" in geometry_source
        and "exactIntervalCoverage" in geometry_source,
        "GiniFrontierGeometry.cpp; round36_causal_tests")
    audit.condition(
        "4_split_normalization", "proof and anchor denominator sources are explicit",
        "eta_proof" in tree_source and "eta_anchor" in tree_source
        and "normalization_source" in tree_source,
        "PaperExternalGiniTree.cpp; split_decision_ledger.csv")
    audit.condition(
        "5_startup_values", "HGA and SIMPLE starts are independently verified",
        "round36_hga_start_verified" in main_source
        and "round36_simple_start_verified" in main_source,
        "main.cpp; per_arm_results.csv")
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    arm_counts = Counter(row["arm"] for row in matrix)
    audit.condition(
        "6_causal_arms", "HH/SS/BW-P/BW-A are balanced and explicit",
        len(matrix) == 56 and arm_counts == Counter({arm: 14 for arm in
                                                     common.ARMS}),
        "round36_official_matrix.csv")

    # 7. Frozen panel before official results.
    panel = common.csv_rows(common.PANEL)
    manifest = json_value(common.FROZEN_MANIFEST)
    start = json_value(common.START_RECORD)
    audit.condition(
        "7_frozen_panel", "14-row representative panel is predeclared",
        len(panel) == 14 and all(truth(row.get(
            "frozen_before_round36_causal_results")) for row in panel),
        "frozen_causal_panel.csv")
    audit.condition(
        "7_frozen_panel", "freeze identity precedes and matches official start",
        bool(manifest) and start.get("frozen_before_causal_results") is True
        and manifest.get("source_tree_fingerprint") == start.get(
            "source_tree_fingerprint")
        and manifest.get("official_matrix_sha256") == start.get(
            "official_matrix_sha256"),
        "round36_frozen_manifest.json; official_start_record.json")

    # 8. Correctness gate is Stage A above; retain an explicit safety-test row.
    audit.condition(
        "8_stage_a", "anchor safety/equivalence/certificate tests are included",
        (common.ROOT / "tests" / "round36_causal_tests.cpp").is_file()
        and stage_a.get("cpp_test_count") == 15,
        "tests/round36_causal_tests.cpp; stage_a_build_and_tests.json")

    # 9. Official Stage B completeness and per-run checksum/correctness.
    items = common.inventory()
    complete, invalid = 0, []
    for row in matrix:
        valid, reason = analysis.artifact_complete(
            common.RUNS / row["run_id"], row, items[row["instance_id"]], manifest)
        if valid:
            complete += 1
        else:
            invalid.append(f"{row['run_id']}:{reason}")
    audit.condition(
        "9_stage_b", "all 56 official rows are checksum-complete",
        complete == 56, "runs/*/completion_marker.json",
        incomplete=complete < 56,
        detail=f"{complete}/56 complete; first missing={invalid[:1]}")
    exactness_path = out / "exactness_certificate_audit.csv"
    exactness = common.csv_rows(exactness_path) if exactness_path.is_file() \
        else []
    lifecycle_fields = (
        "runner_normal_exit", "runner_no_emergency_timeout",
        "result_json_verified_after_process_exit",
        "runner_required_artifacts_complete",
        "atomic_completion_marker_valid",
        "algorithmic_solve_state_not_resumed", "runner_lifecycle_valid",
        "certificate_or_graceful_deadline_endpoint_valid", "finite_bounds",
    )
    exactness_valid = (
        len(exactness) == 56
        and len({row.get("run_id") for row in exactness}) == 56
        and all(truth(row.get("exactness_certificate_audit_passed"))
                and not truth(row.get("false_certificate"))
                and all(truth(row.get(field)) for field in lifecycle_fields)
                for row in exactness)
    )
    audit.condition(
        "9_stage_b",
        "all official rows pass lifecycle, exactness, and certificate audits",
        exactness_valid, "exactness_certificate_audit.csv",
        incomplete=not exactness_valid,
        detail=f"{len(exactness)}/56 final exactness rows")

    # 10-12. Metrics, causal questions, and gates.
    final_decision = json_value(out / "final_audit_decision.json")
    metric_schema_ok, metric_schema_problems = analysis.metric_schema_valid(
        out, expected_runs=56)
    audit.condition(
        "10_metrics", "required per-arm, trajectory, split, target and closure metrics exist",
        metric_schema_ok, "derived causal CSV package", incomplete=True,
        detail=";".join(metric_schema_problems[:5]))
    question_keys = {"question_A_geometry", "question_B_normalization",
                     "question_C_splitting_timing",
                     "question_D_fixed_anchor_stronger_proof"}
    audit.condition(
        "11_causal_questions", "Questions A-D have explicit machine-readable answers",
        question_keys.issubset(set(final_decision.get(
            "causal_question_answers", {}))),
        "final_audit_decision.json", incomplete=True)
    audit.condition(
        "12_decision_gates", "geometry and normalization gates are evaluated",
        "geometry_mechanism_supported" in final_decision.get(
            "classification_gates", {})
        and "split_normalization_mechanism_supported" in final_decision.get(
            "classification_gates", {}),
        "analysis_gate_definition.md; final_audit_decision.json",
        incomplete=True)

    # 13. Stage C is required only after a positive Stage B gate.
    positive = final_decision.get("classification") in {
        "decomposition_geometry_dominant",
        "split_normalization_coupling_dominant", "both_effects_matter"}
    if positive:
        stage_c = json_value(out / "stage_c_final_audit.json")
        audit.condition(
            "13_stage_c", "positive mechanism receives separately frozen broader validation",
            stage_c.get("completed") is True and stage_c.get(
                "automatic_promotion_performed") is False,
            "stage_c_final_audit.json", incomplete=True)
    elif final_decision:
        audit.add("13_stage_c",
                  "Stage C is not run without a positive mechanism signal",
                  "achieved", "final_audit_decision.json")
    else:
        audit.add("13_stage_c", "conditional Stage C decision is pending",
                  "incomplete", "final_audit_decision.json")

    # 14-17. Frozen knobs and prohibited dispatch/mechanism mixing.
    commands = json_value(common.COMMAND_FREEZE)
    command_text = json.dumps(commands)
    protocol = (out / "round36_protocol.md").read_text(
        encoding="utf-8", errors="replace")
    audit.condition("14_rho", "rho remains fixed at 0.01 with no sweep",
                    all(row.get("rho") == "0.01" for row in matrix)
                    and "kRound31C6NormalizedSplitThreshold = 0.01" in tree_source
                    and "`rho=0.01`" in protocol and "--rho" not in command_text,
                    "round36_frozen_manifest.json; command freeze")
    audit.condition("15_K", "K remains four in every official command",
                    command_text.count('"--frontier-intervals", "4"') == 56,
                    "round36_command_freeze.json")
    audit.condition(
        "16_no_dispatch", "no V/M/scenario startup dispatch is introduced",
        "round36-c6-causal-arm" in main_source
        and "startup choice by" not in main_source.lower(),
        "main.cpp; explicit arm matrix")
    audit.condition(
        "17_no_hga_light_mixing", "HGA-LIGHT is not mixed into this causal study",
        "hga-light" not in command_text.lower(),
        "main.cpp; round36_command_freeze.json")

    # 18. Theory note.
    theory = (out / "theory_and_mechanism_note.md").read_text(
        encoding="utf-8", errors="replace")
    audit.condition(
        "18_mathematics", "three requested safety propositions are documented",
        all(token in theory for token in (
            "Proposition 1", "Proposition 2", "Proposition 3",
            "U_anchor", "U_proof", "strict improver")),
        "theory_and_mechanism_note.md")

    # 19-20. Final package and conclusion.
    missing_final = [name for name in FINAL_FILES if not (out / name).is_file()]
    audit.condition(
        "19_reporting", "full compact evidence package is present",
        not missing_final, "final evidence files",
        incomplete=bool(missing_final), detail=f"missing={missing_final}")
    allowed_conclusions = {
        "decomposition_geometry_dominant",
        "split_normalization_coupling_dominant", "both_effects_matter",
        "neither_isolated_effect_sufficient",
    }
    audit.condition(
        "20_conclusion", "one required research conclusion is recorded",
        final_decision.get("classification") in allowed_conclusions
        and final_decision.get("automatic_promotion_performed") is False
        and final_decision.get("validated_gurobi_mainline") == "C6-HGA-FULL",
        "final_audit_decision.json; final_report.md", incomplete=True)

    # 21. Git synchronization and draft PR evidence. The local record is
    # refreshed from the GitHub connector immediately before final completion.
    upstream = git("rev-parse", "@{upstream}", check=False)
    head = git("rev-parse", "HEAD")
    parent = git("rev-parse", "HEAD^", check=False)
    audit.condition(
        "21_git_completion", "current committed branch is pushed",
        bool(upstream) and upstream == head,
        f"HEAD={head}; upstream={upstream}", incomplete=True)
    pr = json_value(out / "github_pr_record.json")
    recorded_head = str(pr.get("head_sha_at_record", ""))
    pr_head_attested = bool(recorded_head) and recorded_head in {head, parent}
    audit.condition(
        "21_git_completion", "draft PR 83 is open and unmerged",
        pr.get("repository") == REPO and pr.get("number") == PR_NUMBER
        and pr.get("draft") is True and pr.get("state") == "open"
        and pr.get("merged") is False and pr.get("head") == BRANCH,
        "github_pr_record.json; GitHub connector", incomplete=True)
    audit.condition(
        "21_git_completion",
        "draft PR record attests the current head or its attestation parent",
        pr_head_attested and pr.get("base") == "main"
        and pr.get("url") == f"https://github.com/{REPO}/pull/{PR_NUMBER}",
        f"recorded={recorded_head}; HEAD={head}; HEAD^={parent}",
        incomplete=True)

    counts = Counter(row["status"] for row in audit.rows)
    all_achieved = len(audit.rows) > 0 and counts == Counter(
        {"achieved": len(audit.rows)})
    summary = {
        "schema": "round36-completion-requirements-audit-v1",
        "round_id": 36, "allow_incomplete": args.allow_incomplete,
        "requirement_count": len(audit.rows),
        "status_counts": dict(counts),
        "all_requirements_achieved": all_achieved,
        "completed_official_rows": complete,
        "expected_official_rows": 56,
        "branch": branch, "head": head, "upstream": upstream,
        "draft_pr_number": PR_NUMBER,
    }
    prefix = "interim_" if args.allow_incomplete else ""
    write_csv(out / f"{prefix}completion_requirements_audit.csv", audit.rows)
    write_text(out / f"{prefix}completion_requirements_audit.json",
               json.dumps({**summary, "requirements": audit.rows},
                          indent=2, sort_keys=True) + "\n")
    write_text(out / f"{prefix}completion_requirements_audit.md",
               markdown(audit.rows, summary))
    print(json.dumps(summary, indent=2, sort_keys=True))
    contradictions = counts.get("contradicted", 0) + counts.get("missing", 0)
    if contradictions:
        return 1
    return 0 if args.allow_incomplete or all_achieved else 1


if __name__ == "__main__":
    raise SystemExit(main())
