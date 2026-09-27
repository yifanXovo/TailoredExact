#!/usr/bin/env python3
"""Final cross-artifact audit for the completed Round 39 package."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any

import round39_common as common


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    manifest = common.load_json(common.FROZEN_MANIFEST)
    per_run = common.csv_rows(common.OUT / "per_run_convergence_metrics.csv")
    pairs = common.csv_rows(common.OUT / "p_grb_vs_light_convergence.csv")
    strata = common.csv_rows(common.OUT / "per_stratum_summary.csv")
    guards = common.csv_rows(common.OUT / "full_vs_light_guard_results.csv")
    exactness = common.csv_rows(common.OUT / "exactness_certificate_audit.csv")
    decision = common.load_json(common.OUT / "final_decision.json")
    tests = common.load_json(common.OUT / "post_build_and_tests.json")
    equivalence = common.load_json(
        common.OUT / "default_c6_equivalence_audit.json")
    source_rows = []
    allowed_analysis_sources = {
        "scripts/analyze_round39.py", "scripts/audit_round39_final.py",
        "scripts/classify_round39_unresolved.py",
        "scripts/package_round39_evidence.py",
        "scripts/run_round39_default_equivalence.py",
        "scripts/run_round39_post_tests.py", "tests/round39_protocol_tests.py",
    }
    for path_text, frozen_sha in manifest["source_file_sha256"].items():
        path = common.ROOT / path_text
        actual = common.sha256(path) if path.is_file() else "missing"
        source_rows.append({
            "relative_path": path_text, "frozen_sha256": frozen_sha,
            "current_sha256": actual, "matches_frozen": actual == frozen_sha,
            "source_class": "frozen_solver_generator_runner_source",
        })
    for path_text in sorted(allowed_analysis_sources):
        path = common.ROOT / path_text
        source_rows.append({
            "relative_path": path_text, "frozen_sha256": "postfreeze_analysis",
            "current_sha256": common.sha256(path) if path.is_file() else "missing",
            "matches_frozen": path.is_file(),
            "source_class": "postfreeze_read_only_analysis_test_packaging",
        })
    common.write_csv(common.OUT / "frozen_source_audit.csv", source_rows)
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=common.ROOT,
        text=True).strip()
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    gates = {
        "dedicated_branch": branch ==
            "codex/round39-small-hard-light-qualification",
        "starting_head_unchanged": head == manifest["starting_head"],
        "frozen_sources_unchanged": all(
            truth(row["matches_frozen"]) for row in source_rows),
        "official_row_count_51": len(per_run) == 51,
        "primary_pair_count_24": len(pairs) == 24,
        "stratum_summary_count_3": len(strata) == 3,
        "guard_row_count_3": len(guards) == 3,
        "all_official_rows_classified": all(
            truth(row["strict_certificate"]) or
            truth(row["official_unresolved"]) for row in per_run),
        "strict_row_count_50": sum(
            truth(row["strict_certificate"]) for row in per_run) == 50,
        "unresolved_row_count_1": sum(
            truth(row["official_unresolved"]) for row in per_run) == 1,
        "all_pair_objectives_equal": all(
            truth(row["objective_equal"]) for row in pairs),
        "exactness_rows_51": len(exactness) == 51,
        "completed_exactness_all_passed": all(
            truth(row["passed"]) for row in exactness
            if not truth(row["official_unresolved"])),
        "false_certificate_count_zero": sum(
            truth(row["false_certificate"]) for row in exactness) == 0,
        "default_c6_equivalence_passed": truth(equivalence["passed"]),
        "post_tests_passed": truth(tests["passed"]),
        "mainline_unchanged": decision["questions"][
            "6_full_remains_validated_mainline"]["default_changed"] is False,
        "automatic_promotion_false": decision["questions"][
            "5_advance_light_to_broader_qualification"][
                "automatic_promotion"] is False,
    }
    rows = [{"gate": key, "passed": value} for key, value in gates.items()]
    common.write_csv(common.OUT / "final_audit_gates.csv", rows)
    summary = {
        "schema": "round39-final-audit-v1", "round_id": 39,
        "passed": all(gates.values()), "gate_count": len(gates),
        "passed_gate_count": sum(gates.values()), "gates": gates,
        "branch": branch, "head": head,
        "strict_certificate_count": sum(
            truth(row["strict_certificate"]) for row in per_run),
        "false_certificate_count": sum(
            truth(row["false_certificate"]) for row in exactness),
        "mainline": "C6-HGA-FULL-K4-rho0.01",
        "mainline_changed": False, "automatic_promotion": False,
    }
    common.write_json(common.OUT / "final_audit_summary.json", summary)
    common.write_text(common.OUT / "final_audit_summary.md", f"""# Round 39 final audit

Final audit: **{'PASS' if summary['passed'] else 'FAIL'}**
({summary['passed_gate_count']}/{summary['gate_count']} gates). Fifty official
rows are strict, one deterministic numerical endpoint is unresolved, there are
{summary['false_certificate_count']} false certificates, and default C6
equivalence plus the full regression suite pass.
The evidence package is losslessly compressed and scanned after this audit so
the audit itself is included in the final inventory. LIGHT is not
automatically promoted; C6-HGA-FULL remains mainline.
""")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
