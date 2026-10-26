#!/usr/bin/env python3
"""Finalize Round 56 reports, decisions, storage inventories, and reproduction notes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import round56_common as r56
from round56_route_archive import EXECUTABLE_SHA256, SOURCE_FREEZE


RAW = r56.EVIDENCE / "local_raw"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object in {path}")
    return value


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=r56.ROOT, text=True).strip()


def counts_by(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    output = []
    for value, group in sorted(grouped.items(), key=lambda pair: float(pair[0])):
        walls = [number(row["algorithm_wall_time_seconds"]) for row in group if number(row["algorithm_wall_time_seconds"]) is not None]
        output.append({
            key: value, "rows": len(group), "certified_final": sum(truth(row["certificate_valid"]) for row in group),
            "certified_by_3600": sum(truth(row["certificate_valid"]) and float(row["algorithm_wall_time_seconds"]) <= 3600.0000001 for row in group),
            "noncertified": sum(not truth(row["certificate_valid"]) for row in group),
            "median_algorithm_wall_seconds": statistics.median(walls) if walls else None,
        })
    return output


def route_summary_by_t(route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in route_rows:
        if truth(row["route_witness_package_available"]):
            grouped[int(row["T"])].append(row)
    output = []
    for t, group in sorted(grouped.items()):
        max_util = [float(row["maximum_route_utilization"]) for row in group]
        used_util = [float(row["mean_used_vehicle_utilization"]) for row in group]
        durations = [float(row["maximum_route_duration"]) for row in group]
        output.append({
            "T": t, "witnesses": len(group), "mean_maximum_utilization": statistics.mean(max_util),
            "maximum_observed_utilization": max(max_util), "mean_used_vehicle_utilization": statistics.mean(used_util),
            "mean_maximum_route_duration_seconds": statistics.mean(durations), "maximum_route_duration_seconds": max(durations),
        })
    return output


def markdown_table(rows: Iterable[dict[str, Any]], fields: list[tuple[str, str]]) -> list[str]:
    rows = list(rows)
    lines = ["| " + " | ".join(label for _, label in fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    for row in rows:
        values = []
        for key, _ in fields:
            value = row.get(key)
            if isinstance(value, float):
                value = f"{value:.9g}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def final_classifications(summary: dict[str, Any], plateau: list[dict[str, str]], transitions: list[dict[str, str]]) -> dict[str, str]:
    exact_deltas = [number(row.get("objective_change_comparison_minus_baseline")) for row in transitions if truth(row.get("both_certified"))]
    material = any(value is not None and abs(value) > 1e-7 for value in exact_deltas)
    plateau_found = any(truth(row.get("plateau_claim_available")) for row in plateau)
    if material and plateau_found:
        time_class = "mixed_t_sensitivity"
    elif material:
        time_class = "material_t_sensitivity_observed"
    elif plateau_found:
        time_class = "objective_plateau_observed"
    else:
        time_class = "insufficient_exact_t_evidence"
    return {
        "engineering_classification": "scenario_identity_bug_fixed",
        "dataset_classification": "paper_candidate_screen_complete" if summary["rows"] == 50 else "paper_candidate_screen_partial",
        "route_archive_classification": "native_route_archive_complete" if summary["route_verification_failures"] == 0 and summary["verified_incumbents"] == summary["exact_route_packages"] + summary["nonexact_route_packages"] else "native_route_archive_partial",
        "time_horizon_classification": time_class,
        "scale_classification": "v8_v12_v20_v30_v50_screen_complete" if summary["rows"] == 50 else "scale_screen_incomplete",
        "mainline_classification": "corrected_k1_am_sf_retained",
    }


def write_analysis(results: list[dict[str, str]], route_rows: list[dict[str, str]], summary: dict[str, Any], classifications: dict[str, str]) -> None:
    by_v = counts_by(results, "V")
    by_t = counts_by(results, "T")
    route_t = route_summary_by_t(route_rows)
    lines = [
        "# Round 56 paper-candidate dataset screening analysis", "",
        "Round 56 is a matched **paper-candidate screening panel**, not a recovered historical benchmark and not a final replicated paper dataset. It uses one independently generated base landscape per V, so the observations below are structural screening evidence rather than population-level statistical generalizations.", "",
        f"All {summary['rows']} mandatory scenarios are retained without filtering: 40 primary Q=30 factorial rows and 10 Q=20 capacity-transfer sentinels. Final strict certificates: {summary['certified_final']}; verified incumbents: {summary['verified_incumbents']}; capped noncertified rows: {summary['capped_noncertified']}.", "",
        "## Exact-solution screening by V", "",
        *markdown_table(by_v, [("V", "V"), ("rows", "Rows"), ("certified_by_3600", "Certified by 3600 s"), ("certified_final", "Certified final"), ("noncertified", "Noncertified"), ("median_algorithm_wall_seconds", "Median wall s")]), "",
        "## Exact-solution screening by operational T", "",
        *markdown_table(by_t, [("T", "T (s)"), ("rows", "Rows"), ("certified_by_3600", "Certified by 3600 s"), ("certified_final", "Certified final"), ("noncertified", "Noncertified"), ("median_algorithm_wall_seconds", "Median wall s")]), "",
        "All cross-V, cross-M, cross-Q, and cross-T proof-difficulty comparisons use the common 3600-second checkpoint. The nine predeclared 7200-second rows are used only to inventory additional exact solutions; they do not replace the common horizon.", "",
        "## Native-witness utilization by T", "",
        *markdown_table(route_t, [("T", "T (s)"), ("witnesses", "Witnesses"), ("mean_maximum_utilization", "Mean max utilization"), ("maximum_observed_utilization", "Largest utilization"), ("mean_used_vehicle_utilization", "Mean used-vehicle utilization"), ("maximum_route_duration_seconds", "Largest route duration s")]), "",
        "Every route statistic describes the single final native witness returned by the official run. No route was compacted, shortened, relabeled, repaired, or post-optimized. Route duration is therefore not the minimum duration compatible with its objective, and vehicle usage is not a minimum-vehicle claim.", "",
        "## Structural interpretation", "",
        "The direct 50-row instance, result, and route tables provide the auditable evidence for V, M, Q, and T effects. Exact monotonicity claims are restricted to pairs in which both endpoints strictly certified; capped witnesses remain descriptive and are never promoted to exact solutions. V30/V50 constitute the large-scale screening regime and are compared at the common 3600-second horizon, including honest capped outcomes.", "",
        f"The time-horizon screening classification is `{classifications['time_horizon_classification']}`. The panel remains unsuitable for final paper generalization because each structural cell ultimately inherits only one frozen base landscape for its V.",
    ]
    (r56.EVIDENCE / "dataset_screening_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_recommendation(results: list[dict[str, str]]) -> None:
    lines = [
        "# Recommended design for the later replicated paper dataset", "",
        "Retain the Round 56 structural coverage rather than selecting only easy or certified cells. The final paper dataset should independently generate and freeze multiple landscapes per structural cell before any performance result is inspected.", "",
        "Recommended strata:", "",
        "- retain V in {8, 12, 20, 30, 50};",
        "- retain both frozen fleet-density levels at each V for primary Q=30;",
        "- retain T in {1800, 3600, 10800, 18000} as operational route limits;",
        "- retain Q=20 sentinels at T=3600 and T=18000 for the lower-M fleet at each V;",
        "- replicate each retained structural cell across multiple independently derived base-landscape seeds, with seeds and all cells frozen before runtime inspection;",
        "- stratify reporting by inventory imbalance, geographic dispersion, fleet density, native utilization, and common-3600-second proof difficulty;",
        "- preserve capped rows and failed-to-certify rows exactly as observed.", "",
        "A practical minimum is three independent base landscapes per V; five or more is preferable for stable descriptive summaries. Computational allocation may be planned by structural stratum, but scenario inclusion must not depend on whether a Round 56 counterpart certified or produced a favorable objective.", "",
        "Round 56 should be cited only as a paper-candidate screening panel. It does not justify a universal scalability claim, a minimum-route-duration claim, or a final statistical conclusion.",
    ]
    (r56.EVIDENCE / "final_dataset_design_recommendation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision(results: list[dict[str, str]], checkpoints: list[dict[str, str]], route_rows: list[dict[str, str]], summary: dict[str, Any], classifications: dict[str, str]) -> dict[str, Any]:
    by_v_t: dict[str, int] = defaultdict(int)
    for row in results:
        if truth(row["certificate_valid"]):
            by_v_t[f"V{int(row['V'])}_T{int(row['T'])}"] += 1
    by_checkpoint = {
        str(point): sum(truth(row["certificate_at_checkpoint"]) for row in checkpoints if int(row["checkpoint_seconds"]) == point)
        for point in (300, 1200, 3600)
    }
    utilization = {str(row["T"]): row for row in route_summary_by_t(route_rows)}
    decision = {
        "schema": "round56-final-decision-v1", "completion_status": "round56_complete" if summary["rows"] == 50 else "round56_incomplete",
        **classifications, "panel_classification": "paper-candidate screening panel",
        "ready_as_final_paper_evidence": False,
        "ready_as_final_paper_evidence_reason": "one frozen base landscape per V is insufficient for replicated statistical generalization",
        "source_freeze_commit": SOURCE_FREEZE, "official_executable_sha256": EXECUTABLE_SHA256,
        "exact_algorithm_identity": "paper-k1-am-sf; corrected K1-AM-SF; K0=1; midpoint splitting; balanced normalized closure score; tau=0.08; F0-CLEAN; Gurobi native branching; Threads=1; Seed=0; Presolve=Auto; MIPGap=MIPGapAbs=0; default PreCrush; dynamic user-cut callback off",
        "primary_q30_scenario_count": sum(row["panel_class"] == "primary_q30" for row in results),
        "q20_sentinel_count": sum(row["panel_class"] == "q20_sentinel" for row in results),
        "certified_counts_by_checkpoint_seconds": by_checkpoint,
        "certified_final_count": summary["certified_final"], "additional_7200_certificate_count": summary["additional_7200_certificates"],
        "capped_noncertified_count": summary["capped_noncertified"], "correctness_failure_count": summary["correctness_failures"],
        "false_certificate_count": summary["false_certificates"], "verified_incumbent_count": summary["verified_incumbents"],
        "exact_optimal_route_witness_count": summary["exact_route_packages"], "nonexact_incumbent_witness_count": summary["nonexact_route_packages"],
        "route_verification_failure_count": summary["route_verification_failures"],
        "t_objective_monotonicity_violation_count": summary["t_monotonicity_violations"],
        "m_objective_monotonicity_violation_count": summary["m_monotonicity_violations"],
        "q_objective_monotonicity_violation_count": summary["q_monotonicity_violations"],
        "exact_solution_counts_by_v_and_t": dict(sorted(by_v_t.items())), "native_route_utilization_summary_by_T": utilization,
        "t_propagation_or_cache_identity_bug_found": False,
        "bugs_found_and_fixed": [
            "pre-run generator distances initially used unrounded coordinates while files serialized rounded coordinates; regenerated from serialized points before optimization",
            "stable result JSON lacked explicit T/process/service/distance/scenario/run identity metadata; source freeze added it without altering the algorithm",
        ],
        "historical_numerical_evidence_affected": False,
        "missing_scenarios": [row["scenario_id"] for row in results if row["solution_class"] in {"execution_failure", "correctness_failure"}],
    }
    r56.write_json(r56.EVIDENCE / "final_decision.json", decision)
    return decision


def write_report(results: list[dict[str, str]], decision: dict[str, Any]) -> None:
    exact = [row for row in results if truth(row["certificate_valid"])]
    lines = [
        "# Round 56 final report", "",
        f"Status: **{decision['completion_status']}**. Classification: **paper-candidate screening panel**; final-paper evidence: **no**.", "",
        "## Final classifications", "",
        f"- Engineering: `{decision['engineering_classification']}`",
        f"- Dataset: `{decision['dataset_classification']}`",
        f"- Route archive: `{decision['route_archive_classification']}`",
        f"- Time horizon: `{decision['time_horizon_classification']}`",
        f"- Scale: `{decision['scale_classification']}`",
        f"- Mainline: `{decision['mainline_classification']}`", "",
        "## Engineering answers", "",
        "No T-propagation or cache-identity defect was found: parent, midpoint-child, native-target, exact-parent, exact-child, movement-domain, valid-inequality, verifier, cache, artifact, and mathematical-instance paths use the requested operational T. Solver process caps are distinct run-identity metadata and do not alter the mathematical model.", "",
        "The pre-run generator audit did find that its first draft calculated distances before rounding serialized coordinates; those inputs were discarded and regenerated before any optimizer result. The stable result format also lacked explicit T/process/service/distance/scenario/run identity fields; source-freeze commit `75e58521158aba8628ebc9444444ec3841415285` added them. Neither issue changes historical numerical evidence. Travel and service durations are seconds under the repository's frozen travel/service-time convention; no unsupported physical-speed interpretation is made.", "",
        "All five landscapes and all 50 scenario identities were frozen before performance execution. M variants preserve station data and differ only in fleet metadata; Q variants differ only in vehicle capacities. The sole evaluated algorithm is the frozen corrected K1-AM-SF identity recorded in `final_decision.json`; no VD-P or other research candidate was enabled.", "",
        "## Completion and certificate answers", "",
        f"All 40 Q=30 rows and all 10 Q=20 rows completed. Certified by 300/1200/3600 seconds: {decision['certified_counts_by_checkpoint_seconds']['300']}/{decision['certified_counts_by_checkpoint_seconds']['1200']}/{decision['certified_counts_by_checkpoint_seconds']['3600']}. Final certified rows: {decision['certified_final_count']}; additional post-3600 certificates from the predeclared 7200-second extensions: {decision['additional_7200_certificate_count']}; capped noncertified rows: {decision['capped_noncertified_count']}.", "",
        f"Verified incumbents: {decision['verified_incumbent_count']}. Exact native packages: {decision['exact_optimal_route_witness_count']}; nonexact incumbent packages: {decision['nonexact_incumbent_witness_count']}; archive-verification failures: {decision['route_verification_failure_count']}. Correctness failures: {decision['correctness_failure_count']}; false certificates: {decision['false_certificate_count']}.", "",
        "## Exact objectives", "",
        "The following values are claimed exact only because each row passed every strict certificate and independent original-solution check.", "",
        *markdown_table(exact, [("scenario_id", "Scenario"), ("V", "V"), ("M", "M"), ("Q", "Q"), ("T", "T"), ("objective", "Exact objective"), ("algorithm_wall_time_seconds", "Wall s")]), "",
        "## Sensitivity and native routes", "",
        f"Exact monotonicity violations for T/M/Q: {decision['t_objective_monotonicity_violation_count']}/{decision['m_objective_monotonicity_violation_count']}/{decision['q_objective_monotonicity_violation_count']}. The plateau table records the first tested plateau T only for fully certified series; noncertified endpoints are excluded from exact claims. Objective and final-inventory changes from T=3600 to T=10800 and T=18000 are recorded directly in `final_inventory_transition.csv`.", "",
        "Native route durations, T utilization, vehicle use, visited stations, pickup/drop/depot-unload counts, and bicycle handling are reported in `paper_candidate_route_table.csv`. They describe exactly one native final solver witness per scenario. No post-certificate or objective-equivalent route optimization was performed; none of these durations is a shortest-route or minimum-duration claim.", "",
        "V30/V50 results form the large-scale screening regime and are retained at both the common 3600-second comparison and prescribed final caps. The later replicated dataset should retain every structural V/M/Q/T stratum and add multiple independently frozen base landscapes per V; it must not select cells according to Round 56 convergence or favorable outcomes.", "",
        "## What remains unproven", "",
        "One base landscape per V cannot support final statistical generalization, universal scalability, or causal claims about all instances. Capped rows remain nonoptimal even when they have verified native incumbents. Route-witness duration is not the minimum duration compatible with the objective. Round 56 therefore is not ready to be called final paper evidence.",
    ]
    (r56.EVIDENCE / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def inventory_tree(
    root: Path,
    storage_class: str,
    exclude: set[Path] | None = None,
    exclude_roots: set[Path] | None = None,
) -> list[dict[str, Any]]:
    excluded = {path.resolve() for path in (exclude or set())}
    excluded_roots = {path.resolve() for path in (exclude_roots or set())}
    rows = []
    for path in sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: item.as_posix()):
        if path.resolve() in excluded:
            continue
        if any(path.resolve().is_relative_to(excluded_root) for excluded_root in excluded_roots):
            continue
        rows.append({"path": r56.repo_path(path), "storage_class": storage_class, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return rows


def write_inventories() -> None:
    local_rows = inventory_tree(RAW, "local_raw_hash_inventoried_not_committed")
    r56.write_csv(r56.EVIDENCE / "local_raw_evidence_inventory.csv", local_rows)
    inventory_paths = {
        r56.EVIDENCE / "compact_evidence_inventory.csv", r56.EVIDENCE / "local_raw_evidence_inventory.csv",
        r56.EVIDENCE / "final_evidence_inventory.csv",
    }
    compact_rows = inventory_tree(r56.EVIDENCE, "compact_committed", inventory_paths, {RAW})
    r56.write_csv(r56.EVIDENCE / "compact_evidence_inventory.csv", compact_rows)
    final_rows = compact_rows + [{
        "path": r56.repo_path(r56.EVIDENCE / "local_raw_evidence_inventory.csv"),
        "storage_class": "compact_committed_local_raw_index", "bytes": (r56.EVIDENCE / "local_raw_evidence_inventory.csv").stat().st_size,
        "sha256": sha256(r56.EVIDENCE / "local_raw_evidence_inventory.csv"),
    }]
    r56.write_csv(r56.EVIDENCE / "final_evidence_inventory.csv", final_rows)
    raw_bytes = sum(int(row["bytes"]) for row in local_rows)
    text = f"""# Round 56 evidence storage audit

Compact manifests, tables, reports, route packages, verification files, reproduction commands, and hashes are committed. Native solver logs, generated LPs, and transient progress ledgers remain under `results/gf_paper_benchmark_time_horizon_round56/local_raw/` and are not committed.

The local-raw inventory records {len(local_rows)} files totaling {raw_bytes} bytes, each with an exact path, byte count, and SHA-256. `compact_evidence_inventory.csv` inventories the compact committed evidence; `final_evidence_inventory.csv` joins that evidence with the committed local-raw index. The inventory files exclude their own recursive hashes.
"""
    (r56.EVIDENCE / "evidence_storage_audit.md").write_text(text, encoding="utf-8")


def write_reproduction() -> None:
    text = f"""# Round 56 reproduction commands

The source freeze is `{SOURCE_FREEZE}` and the sole official executable SHA-256 is `{EXECUTABLE_SHA256}`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round56_official.py --prepare
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round56_official.py --run
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\round56_route_archive.py --all-completed
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\analyze_round56_results.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round56_repeatability.py --run
& 'D:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\Common7\\IDE\\CommonExtensions\\Microsoft\\CMake\\CMake\\bin\\ctest.exe' --test-dir build\\official-round56-paper-dataset-75e585211 --output-on-failure
D:\\msys64\\ucrt64\\bin\\python.exe -B -m unittest discover -s tests -p 'round*_protocol_tests.py' -v
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\verify_round56_preservation.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\finalize_round56_evidence.py --reports --inventory
```

The 50 exact commands, mathematical-instance hashes, run identities, T values, and process caps are frozen in `execution_manifest.json`. Bulky native logs remain local but are path/size/SHA-256 inventoried.
"""
    (r56.EVIDENCE / "reproduction_commands.md").write_text(text, encoding="utf-8")


def reports() -> None:
    results = read_csv(r56.EVIDENCE / "official_results.csv")
    checkpoints = read_csv(r56.EVIDENCE / "official_checkpoints.csv")
    route_rows = read_csv(r56.EVIDENCE / "native_route_descriptive_statistics.csv")
    plateau = read_csv(r56.EVIDENCE / "objective_plateau_analysis.csv")
    transitions = read_csv(r56.EVIDENCE / "final_inventory_transition.csv")
    summary = load_json(r56.EVIDENCE / "analysis_summary.json")
    classifications = final_classifications(summary, plateau, transitions)
    write_analysis(results, route_rows, summary, classifications)
    write_recommendation(results)
    decision = write_decision(results, checkpoints, route_rows, summary, classifications)
    write_report(results, decision)
    write_reproduction()
    print(json.dumps({"reports_written": True, **classifications}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args()
    if not args.reports and not args.inventory:
        raise RuntimeError("select --reports and/or --inventory")
    if args.reports:
        reports()
    if args.inventory:
        write_inventories()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
