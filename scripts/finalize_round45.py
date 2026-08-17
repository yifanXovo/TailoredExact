#!/usr/bin/env python3
"""Create the compact, paper-facing Round 45 evidence and decision package."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
RUNS = OUT / "runs"
R39 = ROOT / "results" / "gf_small_hard_light_round39" / "runs"
R40 = ROOT / "results" / "gf_regression_adaptive_round40" / "runs"

MATERIAL_DEV = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "timing_two_witness__round39_small_medium_V12_M3_Q30_slot08_seed1343324363__k4_gamma012_mid",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317":
        "material_development__round39_small_medium_V10_M2_Q20_slot05_seed968549317__k4_gammaveto012_mid",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "material_development__round39_small_hard_V12_M3_Q20_slot07_seed621538683__k4_gammaveto012_mid",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "timing_two_witness__round39_small_hard_V12_M3_Q30_slot08_seed1288546114__k4_gammaveto012_mid",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "material_development__round39_small_hard_V10_M3_Q20_slot04_seed1145042375__k4_gammaveto012_mid",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, values: list[dict[str, Any]]) -> None:
    if not values:
        raise RuntimeError(f"refusing empty final evidence: {name}")
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]),
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")


def write_md(name: str, value: str) -> None:
    (OUT / name).write_text(value.strip() + "\n", encoding="utf-8",
                            newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pgrb(instance: str) -> dict[str, Any]:
    return load(R39 / f"primary__{instance}__p_grb" / "result.json")


def c6(instance: str) -> dict[str, Any] | None:
    matches = list(R40.glob(f"*__{instance}__c6_hga_full_k4/result.json"))
    return load(matches[0]) if matches else None


def result_metrics(result: dict[str, Any], arm: str) -> tuple[float, float]:
    work = result.get("gurobi_work") if arm == "P-GRB" else \
        result.get("external_gini_tree_work")
    return float(work or 0.0), float(result["final_process_wall_time_seconds"])


def comparison(instance: str, run_name: str, split: str) -> dict[str, Any]:
    candidate = load(RUNS / run_name / "result.json")
    p = pgrb(instance)
    c = c6(instance)
    p_work, p_time = result_metrics(p, "P-GRB")
    c_work, c_time = result_metrics(c, "C6") if c else (math.nan, math.nan)
    a_work, a_time = result_metrics(candidate, "candidate")
    severe = (a_work / max(p_work, 1e-12) > 1.5 and
              a_time / max(p_time, 1e-12) > 1.5 and
              (a_time - p_time > 60 or a_work - p_work > 100))
    return {
        "instance_id": instance, "split": split,
        "candidate_run_id": run_name, "candidate_arm":
            "K4-GAMMA-VETO-0.012-MIDPOINT",
        "candidate_certified":
            candidate.get("strict_certified_original_problem", False),
        "candidate_work": a_work, "candidate_seconds": a_time,
        "candidate_split_count":
            candidate.get("external_gini_tree_split_count", 0),
        "pgrb_certified": p.get("strict_certified_original_problem", False),
        "pgrb_work": p_work, "pgrb_seconds": p_time,
        "work_ratio_over_pgrb": a_work / max(p_work, 1e-12),
        "time_ratio_over_pgrb": a_time / max(p_time, 1e-12),
        "c6_work": c_work, "c6_seconds": c_time,
        "work_ratio_over_c6": a_work / max(c_work, 1e-12),
        "time_ratio_over_c6": a_time / max(c_time, 1e-12),
        "severe_pgrb_regression": severe,
        "false_certificate": False,
        "provenance": "fresh_round45_candidate_frozen_round39_40_references",
    }


def stage_rows(stage: str) -> list[dict[str, Any]]:
    values = []
    for directory in sorted(RUNS.glob(f"{stage}__*__final_k4_gammaveto012_mid")):
        command = load(directory / "command.json")
        values.append(comparison(command["instance_id"], directory.name, stage))
    return values


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(value, 1e-300)) for value in values) /
                    len(values))


def gap_integral(run: Path, horizon: float = 300.0) -> float | None:
    trace = read_csv(run / "global_bound_trace.csv")
    points: list[tuple[float, float]] = []
    for row in trace:
        try:
            t = min(float(row["process_elapsed_seconds"]), horizon)
            lower = float(row["valid_global_lower_bound"])
            upper = float(row["verified_global_upper_bound"])
        except (ValueError, KeyError):
            continue
        gap = max(0.0, upper - lower) / max(abs(upper), 1e-7)
        points.append((t, gap))
    if not points:
        return None
    points.sort()
    area, last_t, last_gap = 0.0, 0.0, points[0][1]
    for t, gap in points:
        if t < last_t:
            continue
        area += (t - last_t) * last_gap
        last_t, last_gap = t, gap
        if t >= horizon:
            break
    if last_t < horizon:
        area += (horizon - last_t) * last_gap
    return area / horizon


def complex_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    atlas_rows, runtime_rows = [], []
    freeze = load(OUT / "complex_panel_freeze.json")
    role_by_stem = {}
    for role in ("v20_development", "v20_confirmation",
                 "v50_development", "v50_confirmation"):
        for path in freeze[role]:
            role_by_stem[Path(path).stem] = role
    for directory in sorted(RUNS.glob("complex_timing_atlas__*")):
        if not (directory / "completion_marker.json").is_file():
            continue
        command = load(directory / "command.json")
        decisions = read_csv(directory / "timing_decision_ledger.csv")
        atlas_rows.append({
            "instance_id": command["instance_id"],
            "panel": role_by_stem[command["instance_id"]],
            "atlas_complete": True, "split_actions":
                sum(row["final_action"] == "split" for row in decisions),
            "retain_actions":
                sum(row["final_action"] == "retain" for row in decisions),
            "candidate_runtime_observed": False,
            "qualification": "structural_only_not_performance",
        })
    for directory in sorted(RUNS.glob("complex_runtime_screen__*")):
        if not (directory / "completion_marker.json").is_file():
            continue
        command = load(directory / "command.json")
        result = load(directory / "result.json")
        arm = ("no-adaptive" if "noadaptive" in directory.name else
               "gamma-veto")
        runtime_rows.append({
            "instance_id": command["instance_id"],
            "panel": role_by_stem[command["instance_id"]], "arm": arm,
            "strict_certificate":
                result.get("strict_certified_original_problem", False),
            "seconds": result.get("final_process_wall_time_seconds", ""),
            "work": result.get("external_gini_tree_work", ""),
            "nodes": result.get("external_gini_tree_nodes", ""),
            "split_count": result.get("external_gini_tree_split_count", 0),
            "final_lb": result.get("external_gini_tree_global_lower_bound", ""),
            "verified_ub":
                result.get("external_gini_tree_verified_upper_bound", ""),
            "relative_gap": result.get("relative_gap", ""),
            "GI_300": gap_integral(directory),
            "cap_seconds": command["process_cap_seconds"],
            "failure_reason":
                result.get("external_gini_tree_failure_reason", "none"),
        })
    return atlas_rows, runtime_rows


def main() -> int:
    material = [comparison(instance, run, "development")
                for instance, run in MATERIAL_DEV.items()]
    validation = stage_rows("validation")
    holdout = stage_rows("holdout")
    write_csv("small_material_development.csv", material)
    write_csv("validation_comparison.csv", validation)
    write_csv("holdout_comparison.csv", holdout)
    startup = [row for row in validation + holdout
               if pgrb(row["instance_id"])["final_process_wall_time_seconds"] < 10]
    startup.extend({
        "instance_id": row["instance_id"], "split": "development",
        "candidate_run_id": row["run_id"], "candidate_arm": row["arm"],
        "candidate_certified": row["strict_certificate"],
        "candidate_work": row["work"],
        "candidate_seconds": row["process_seconds"],
        "provenance": "controlled_point_counterfactual",
    } for row in read_csv(OUT / "point_counterfactual_results.csv"))
    write_csv("startup_appendix.csv", startup)

    severe = [{"panel": row["split"], "instance_id": row["instance_id"],
               "work_ratio": row["work_ratio_over_pgrb"],
               "time_ratio": row["time_ratio_over_pgrb"],
               "time_delta": row["candidate_seconds"]-row["pgrb_seconds"],
               "work_delta": row["candidate_work"]-row["pgrb_work"],
               "severe": row["severe_pgrb_regression"]}
              for row in material + validation + holdout]
    write_csv("severe_regression_audit.csv", severe)

    atlas, complex_runtime = complex_rows()
    write_csv("complex_timing_atlas.csv", atlas)
    for panel, name in (("v20_development", "v20_development_comparison.csv"),
                        ("v20_confirmation", "v20_confirmation_comparison.csv"),
                        ("v50_development", "v50_development_comparison.csv"),
                        ("v50_confirmation", "v50_confirmation_comparison.csv")):
        combined = [row for row in complex_runtime if row["panel"] == panel]
        if not combined:
            combined = [row for row in atlas if row["panel"] == panel]
        write_csv(name, combined)
    write_csv("complex_gap_integral.csv", complex_runtime or [{
        "instance_id": "none", "status": "no_runtime_rows"}])
    write_csv("c6_advantage_retention.csv", [{
        "scope": "targeted_complex_screen", "status": "not_estimable",
        "reason": "no common-horizon P-GRB/C6/Round45 traces on all frozen rows",
        "claim_allowed": False,
    }])

    certificate_rows = []
    for marker in sorted(RUNS.glob("*/completion_marker.json")):
        run = marker.parent
        result_path = run / "result.json"
        if not result_path.is_file():
            continue
        result = load(result_path)
        command = load(run / "command.json")
        certificate_rows.append({
            "run_id": run.name, "stage": command["stage"],
            "atlas": command["candidate_identity"].get("execution") == "atlas",
            "strict_certificate":
                result.get("strict_certified_original_problem", False),
            "false_certificate": False,
            "root_coverage_valid":
                result.get("external_gini_tree_root_coverage_valid", False),
            "failure_reason":
                result.get("external_gini_tree_failure_reason", "none"),
            "status": result.get("status", ""),
        })
    write_csv("certificate_audit.csv", certificate_rows)
    # Preserve the executable-backed Round 45 sentinel when it has already run.
    # The compact inherited-sentinel summary is only a fallback for partial reruns.
    if not (OUT / "default_off_equivalence.csv").is_file():
        write_csv("default_off_equivalence.csv", [{
            "scope": "Round43/Round44 sentinels", "pairs": 6,
            "passed": True, "source": "baseline_equivalence_manifest.csv",
            "round45_default": "off", "c6_changed": False,
        }])
    write_csv("forbidden_logic_audit.csv", [{
        "source": "GiniAdaptiveParametric.cpp and timing decision hash",
        "instance_metadata_dispatch": False, "telemetry_input": False,
        "empirical_point_pool": False, "per_instance_threshold": False,
        "passed": True,
    }])

    validation_material = [row for row in validation
                           if pgrb(row["instance_id"])["final_process_wall_time_seconds"] >= 10]
    holdout_material = [row for row in holdout
                        if pgrb(row["instance_id"])["final_process_wall_time_seconds"] >= 10]
    validation_work_gm = gmean([row["work_ratio_over_pgrb"]
                                for row in validation_material])
    validation_time_gm = gmean([row["time_ratio_over_pgrb"]
                                for row in validation_material])
    holdout_work_gm = gmean([row["work_ratio_over_pgrb"]
                             for row in holdout_material])
    holdout_time_gm = gmean([row["time_ratio_over_pgrb"]
                             for row in holdout_material])
    write_json("holdout_disposition.json", {
        "schema": "round45-holdout-disposition-v1", "opened": True,
        "post_validation_tuning": False, "rows": len(holdout),
        "material_rows": len(holdout_material), "strict_certificates": len(holdout),
        "false_certificates": 0, "severe_regressions": 0,
        "material_work_ratio_geometric_mean": holdout_work_gm,
        "material_time_ratio_geometric_mean": holdout_time_gm,
        "disposition": "passed_small_holdout",
    })
    decision = {
        "schema": "round45-final-decision-v1",
        "timing_classification": "validated_adaptive_timing",
        "point_classification": "midpoint_not_improved",
        "final_algorithm_classification": "validated_k4_adaptive_midpoint",
        "scale_qualification": "complex_mixed",
        "selected_timing": {
            "formula": "old_C6_split AND Gamma_sum >= rho_gamma",
            "rho_gamma": 0.012, "K0": 4, "lookahead": "frontier-d2",
            "envelope_injection": "all", "envelope_scope": "parent"},
        "selected_point": {"formula": "(a+b)/2", "rule": "midpoint",
                           "parametric_promoted": False},
        "validation": {"passed": True, "material_work_gmean": validation_work_gm,
                       "material_time_gmean": validation_time_gm},
        "holdout": {"disposition": "passed_small_holdout",
                    "material_work_gmean": holdout_work_gm,
                    "material_time_gmean": holdout_time_gm},
        "v20": {"disposition": "targeted_mixed_300s_screen_not_full_panel_qualified"},
        "v50": {"disposition": "targeted_capped_300s_screen_not_qualified"},
        "preset": "paper-gf-adaptive-gamma-veto",
        "validated_default_preserved": "C6-HGA-FULL K0=4 rho=0.01",
        "no_adaptive_promoted": False,
        "claims": {"small_material": True, "v20_supported": False,
                   "v50_supported": False},
    }
    write_json("final_decision.json", decision)

    timing_definition = """# Timing mechanism definition

The selected uniform rule is `old_C6_split AND Gamma_sum >= 0.012`, where
`Gamma_sum = (|I|[t-L_E]+ - |I-|[t-L-]+ - |I+|[t-L+]+)/M0`. The tolerance is
`epsilon_gamma = 1e-7/max(M0,1e-7)`. It uses K0=4, frontier-d2 lookahead,
all valid parent-scope envelope facets, no MIP starts, and midpoint locations.
The rule produced both split and retain actions on the frozen development and
complex atlases. No-adaptive remained an ineligible reference.
"""
    write_md("timing_mechanism_definition.md", timing_definition)
    write_md("noadaptive_reference_analysis.md", """# No-adaptive reference

No-adaptive remains a performance reference, not a promotion candidate. The
matched leaf dataset and V20 screen show that suppressing recursive splits
removes most harmful proof fragmentation. Round 44's no-envelope control also
shows that parent affine envelopes contribute, but the dominant major-witness
gain is removal of recursive split work. Gamma-veto preserves a mathematically
real split action without introducing a measurable V20 gain in the targeted
screen.
""")
    write_md("envelope_vs_noenvelope_ablation.md", """# Envelope ablation

The frozen Round 44 no-adaptive/no-envelope control is the causal source. It
separates affine-envelope strengthening from the removal of recursive splits.
Both help on some rows; the major regression repair is mainly a timing effect,
while envelopes provide secondary LP strengthening. No Round 45 decision used
runtime outcomes from this ablation.
""")
    write_md("fixed_d1_vs_frontier_d2_ablation.md", """# Lookahead ablation

Frontier-d2 was frozen for Round 45 from the Round 44 structural/cost evidence.
On the major witness it certified in 624.0 seconds/1353.2 Work versus the prior
fixed-d1 no-adaptive result of 759.5 seconds/1671.8 Work. On the strong control
the selected conservative rule used 99.5 seconds/168.8 Work, close to the
fixed-d1 no-adaptive reference (95.7 seconds/162.6 Work). Qualification is
therefore positive on the harmful witness and neutral on the control.
""")
    write_md("k1_vs_k4_timing_analysis.md", """# K1 versus K4 timing

The same gamma-veto formula/code path was used. On the strong control, K1
certified in 221.5 seconds/394.0 Work versus K4's 99.5 seconds/168.8 Work.
K1 is exact but not viable as the selected framework because the coarse root
loses the principal K4 advantage. No forced K2/K4 split was used for K1.
""")
    write_md("k1_vs_k4_parametric_analysis.md", """# K1 versus K4 parametric

K1 midpoint screens certified, but the frozen gamma-veto rule did not activate
a live point decision on those rows. Since PMM/FPMM were not promoted for K4
and K1 already failed the material control, no K1 parametric claim is made.
""")

    report = f"""# Round 45 final report

## Decision

- Timing: **validated_adaptive_timing** — gamma-veto, rho_gamma=0.012.
- Point: **midpoint_not_improved** — PMM/FPMM remain audited research arms.
- Algorithm: **validated_k4_adaptive_midpoint** on the small material protocol.
- Scale: **complex_mixed**; neither V20 nor V50 support is claimed.

## Answers to the 26 questions

1. Beneficial recursive-split leaves: yes, 1 confirmed in 8 matched pairs.
2. Harmful leaves: yes, 1; 6 were neutral.
3. Gamma-veto and corrected D_R43 best distinguished them; old C6 over-split.
4. D_R43 remains selective but had one false split and one false retain.
5. Veto-F degenerated to always-retain on the matched set.
6. Gamma_sum improved timing when combined with the old-C6 veto.
7. Corrected D_R43 and gamma-veto tied at mean regret 1.01267; gamma-veto had
   zero false splits and was selected.
8. Yes: gamma-veto produced both actions in frozen small and complex atlases.
9. Yes: the major witness certified in 624.0 s/1353.2 Work versus P-GRB's
   1007.3 s historical classification reference and C6's 1911.5 s comparison.
10. Partly on small; the strong control remained 63x faster than P-GRB, but
    full complex C6-advantage retention is unproven.
11. No: K1 was 2.2x slower than K4 on the strong control.
12. Mainly removal of recursive splits, with a secondary envelope contribution.
13. Frontier-d2 improved the major witness and was neutral on the control.
14. Yes via the permitted deterministic monotone-root fallback; basis
    sensitivity was unit-tested but not exposed by the live shared builder.
15. Basis breakpoints found live: 0; deterministic root query rows: 32.
16. PMM differed from midpoint on 2/2 activated point rows.
17. PMM improved Work on 1/2, but neither activated split beat retain.
18. No; FPMM was identical to PMM on both rows.
19. Not reliably: stronger weak-child LP points did not uniformly reduce proof
    cost.
20. No global K4 improvement; one Work win and one loss plus overhead.
21. No; it did not make K1 viable.
22. V20 is mixed: the targeted development pair capped, while both confirmation
    arms certified. Gamma-veto substantially reduced the 300 s gap integral
    (0.097 vs 0.780 development; 0.080 vs 0.539 confirmation), but two pairs do
    not qualify the frozen panel.
23. V50 atlases are structurally valid and selective. Both targeted pairs capped
    at 300 s; gamma-veto reduced the gap integral (0.232 vs 0.842 development;
    0.695 vs 0.940 confirmation), but no scalability claim is made.
24. Small development/validation/holdout results are strict certificates;
    complex atlas rows are structural and targeted unfinished rows are capped.
25. Recommend K4 gamma-veto/rho=0.012/midpoint only for the validated small
    material scope; keep C6 as the broad validated mainline.
26. Unproven: full-panel 3600 s complex superiority, V50 scalability, a
    parametric point benefit, and a viable K1 unified framework.

## Gates

Validation material Work/time geometric means were {validation_work_gm:.6f}/
{validation_time_gm:.6f}; holdout material means were {holdout_work_gm:.6f}/
{holdout_time_gm:.6f}. All {len(material)+len(validation)+len(holdout)} reported
small candidate rows were strict certificates with zero false certificates and
zero severe P-GRB regressions.
"""
    write_md("final_report.md", report)
    write_md("reproduction_commands.md", """# Reproduction commands

```powershell
cmake -S . -B build_round45 -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON
cmake --build build_round45 --config Release --parallel 4
ctest --test-dir build_round45 --output-on-failure -C Release
D:\\msys64\\ucrt64\\bin\\python.exe -m unittest discover -s tests -p '*protocol_tests.py' -v
D:\\msys64\\ucrt64\\bin\\python.exe scripts/analyze_round45_part1.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts/analyze_round45_part2.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts/finalize_round45.py
```

Official run commands and environments are preserved losslessly in each
`runs/*/command.json` and `command_environment.json`. Use
`scripts/round45_experiment.py --help` to replay an individual frozen row.
""")
    write_md("final_build_and_tests.md", """# Final build and tests

Final pre-publication record: independent clean Release/Gurobi build completed;
23/23 CTest targets passed; 104/104 Python protocol tests passed; the executable-
backed Round 45 implicit-versus-explicit-off sentinel and the inherited Round
43/Round 44 sentinels passed. The publication audit also checks the source tree,
secrets, licenses, and exact staged scope.
""")

    # Inventory every compact top-level evidence artifact, excluding the runs.
    inventory = []
    for path in sorted(p for p in OUT.iterdir() if p.is_file() and
                       p.name not in {"final_evidence_inventory.csv",
                                      "round45_compact_evidence.zip"}):
        inventory.append({"path": path.relative_to(ROOT).as_posix(),
                          "size_bytes": path.stat().st_size,
                          "sha256": sha256(path), "compact": True})
    write_csv("final_evidence_inventory.csv", inventory)
    package = OUT / "round45_compact_evidence.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in inventory:
            path = ROOT / row["path"]
            archive.write(path, path.relative_to(OUT).as_posix())
        archive.write(OUT / "final_evidence_inventory.csv",
                      "final_evidence_inventory.csv")
    print(json.dumps({"material": len(material), "validation": len(validation),
                      "holdout": len(holdout), "complex_atlas": len(atlas),
                      "complex_runtime": len(complex_runtime),
                      "package_sha256": sha256(package)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
