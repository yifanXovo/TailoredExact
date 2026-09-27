#!/usr/bin/env python3
"""Generate compact final Round 55 reports from frozen decision tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"


STAGES = [
    ("stable_requalification_300s", "stable_requalification_results.csv"),
    ("live_pilot_120s", "live_pilot_120s.csv"),
    ("fixed_interval_development_300s", "fixed_interval_development_300s.csv"),
    ("revision_1_development_300s", "revision_1_results.csv"),
    ("fixed_interval_confirmation_1200s", "fixed_interval_confirmation_1200s.csv"),
    ("fixed_interval_confirmation_1800s", "fixed_interval_confirmation_1800s.csv"),
    ("fixed_interval_key_long_3600s", "fixed_interval_key_long_3600s.csv"),
    ("k1_integration_1800s", "k1_integration_1800s.csv"),
    ("k1_integration_3600s", "k1_integration_3600s.csv"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true"}


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    certificates: list[dict[str, object]] = []
    for stage, filename in STAGES:
        for row in read_csv(EVIDENCE / filename):
            engineering = row.get("engineering_gate", row.get("correctness_gate", ""))
            certificates.append({
                "stage": stage,
                "state_or_instance": row.get("state_id", row.get("instance_id", "")),
                "arm": row.get("arm", ""),
                "cap_seconds": row.get("cap_seconds", ""),
                "certificate": row.get("certificate", ""),
                "correctness_gate": engineering,
                "false_certificate": row.get("false_certificate", ""),
                "source_file": filename,
            })
    write_csv(EVIDENCE / "certificate_audit.csv", [
        "stage", "state_or_instance", "arm", "cap_seconds", "certificate",
        "correctness_gate", "false_certificate", "source_file"], certificates)

    severe = [
        {"stage": "live_pilot_120s", "baseline": "F0-CLEAN", "candidate": "SF-MC4",
         "state_or_instance": "D1", "classification": "severe_regression"},
        {"stage": "fixed_interval_development_300s", "baseline": "F0-CLEAN", "candidate": "VD-J",
         "state_or_instance": "D13", "classification": "severe_regression"},
        {"stage": "revision_1_development_300s", "baseline": "F0-CLEAN", "candidate": "SF-R1",
         "state_or_instance": "D1", "classification": "severe_regression"},
        {"stage": "revision_1_development_300s", "baseline": "F0-CLEAN", "candidate": "SF-R1",
         "state_or_instance": "D12", "classification": "severe_regression"},
        {"stage": "k1_integration_effective", "baseline": "K1-AM-SF", "candidate": "K1-AM-SF-CANDIDATE",
         "state_or_instance": "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
         "classification": "severe_regression"},
    ]
    write_csv(EVIDENCE / "severe_regression_audit.csv",
              ["stage", "baseline", "candidate", "state_or_instance", "classification"], severe)

    decision = {
        "schema": "round55-final-decision-v1",
        "complete": True,
        "entered_stage_missing_rows": [],
        "classifications": {
            "engineering": "engineering_semantic_bug_fixed",
            "mainline": "k1_am_sf_corrected_baseline",
            "aggregate_hull": "aggregate_mc_strictly_strengthening",
            "station_state": "station_state_partial",
            "sparse_management": "no_additional_family_removed",
            "cover_dp": "penalty_cover_not_opened",
            "split": "stable_split_rule_retained",
            "algorithm": "strengthened_candidate_mixed",
            "pgrb": "pgrb_panel_not_opened",
            "scale": "generalization_not_opened",
        },
        "stable_algorithm": {
            "name": "K1-AM-SF", "preset": "paper-k1-am-sf", "initial_intervals": 1,
            "split_point": "midpoint", "split_score": "balanced-normalized-closure",
            "tau": 0.08, "inner_backend": "F0-CLEAN", "threads": 1,
            "seed": 0, "presolve": "Auto", "dynamic_user_cut_callback": False,
        },
        "final_inner_candidate": {"formulation": "VD-P", "preset": "research-k1-am-sf-vdp",
                                  "status": "default-off mixed research candidate"},
        "engineering_bug": "stale incumbent epoch in artifact/LP cache identity",
        "historical_performance_evidence_invalidated": True,
        "historical_exact_certificates_invalidated": False,
        "k1_integration": {
            "entered_physical_rows": 44, "effective_pairs": 17,
            "stable_certificates": 12, "candidate_certificates": 14,
            "false_certificates": 0, "severe_regressions": 1,
            "shifted_work_geometric_mean_ratio": 0.5691998368030589,
            "aggregate_gi_ratio": 0.6090974547960206,
            "gate_pass": False,
        },
        "sealed_rows": 0, "expansion_rows": 0,
        "recommendation": "Study the uniform VD-P formulation-lifecycle cost on the major witness without changing the split controller or dispatching by instance."
    }
    write_json(EVIDENCE / "final_decision.json", decision)

    report = """# Round 55 final report

## Outcome

Round 55 is complete with no missing entered-stage row. The stable paper preset remains K1-AM-SF/F0-CLEAN. VD-P is exact and passed fixed-interval confirmation and long checks, but remains a default-off mixed research candidate because it severely regressed the frozen major witness in full K1 integration. The sealed P-GRB and expansion panels did not open.

## Required scientific answers

1. **Engineering bugs:** one semantic cache-identity bug was found and fixed: artifact/LP reuse could retain a stale incumbent epoch.
2. **Historical impact:** pre-fix performance trajectories are invalid comparators; no historical exact certificate was shown false or invalidated.
3. **First-class equivalence:** the explicit K1 controller matches the Round 54 stable algorithm on 11 semantic sentinels.
4. **Historical fields:** the paper preset no longer depends on inert K4/C6 fields; they are neutral compatibility adapters.
5. **Current product relation:** the implementation represents unscaled `Z_i = G Y_i`; the ratio is `Y_i / D`, and the penalty uses that relation consistently.
6. **Aggregate implication:** aggregate McCormick rows are not already implied on 24 of 27 frozen roots.
7. **MC4:** exact and strictly strengthening on 24/27 roots, but rejected after a severe D1 pilot regression.
8. **VD-P exactness:** proved by integer-state mapping and reverse projection; selector and perspective reconstruction is exact.
9. **VD-J exactness:** proved; it additionally imposes exact joint penalty equality.
10. **VD-J joint strength:** yes, it strictly improves the root bound beyond isolated G-times-Y McCormick on 24/27 states, but failed MIP development through a certificate loss and severe D13 regression.
11. **D1 size:** F0 3,764 rows/1,404 columns/16,888 nonzeros; MC4 3,812/1,404/16,992; VD-P 4,008/1,964/18,164; VD-J 4,032/1,964/18,864. VD-P/VD-J use 348 selector and 348 perspective variables on D1.
12. **Root LP:** MC4, VD-P, and VD-J strictly dominate F0 on 24/27 states with no root-bound loss. Root-Work GMs are 0.94146, 1.05378, and 1.16033 respectively.
13. **Active-family efficacy:** pair and triple support-duration covers had no activity, nonzero dual, or isolated root-bound contribution in 162 diagnostics.
14. **Sparse removal:** no additional family was removed; SF-R1 lost D12 and was severe on D1/D12.
15. **Live candidates:** MC4, VD-P, and VD-J entered the pilot; VD-P and VD-J entered development; VD-P alone entered confirmation, long, and K1.
16. **Rejected candidates:** MC4 (severe D1), VD-J (loss/severe D13), and SF-R1 (loss/severe D1/D12).
17. **Controlled revisions:** SF-R1 removed triple covers only and was rejected; SF-R2 was declined. No split revision opened.
18. **Penalty covers violated:** the live cover gate did not open because VD-J failed; no performance-row violation claim is made.
19. **Exact DP practicality:** the exact multiple-choice cover DP and one-pass separator were implemented and passed reconstruction, strict-cover, duplicate, and termination tests.
20. **Cover MIP performance:** untested because the prerequisite gate was false.
21. **Interactions:** untested because fewer than two independent mechanisms qualified.
22. **Final inner candidate:** exact VD-P, policy `round55-vd-p`, preset `research-k1-am-sf-vdp`, default-off.
23. **Full K1:** mixed rejection: 14 versus 12 certificates, Work GM 0.5691998368, GI ratio 0.6090974548, but one severe major-witness regression.
24. **Split actions:** materially changed on three instances.
25. **Split causality:** the severe witness had no materially changed action, so its failure is attributed to inner-MIP cost rather than the split controller.
26. **Split revision:** not opened; midpoint balanced normalized closure with tau=0.08 is retained.
27. **Major repair:** not preserved in the candidate integration because the designated witness was severely slower.
28. **P-GRB:** no direct Round 55 comparison; sealed P-GRB remained unopened after K1 failed.
29. **Scale:** K1 V20/V50 behavior was nonworse, but sealed V12/V20/V50 generalization remains unproven.
30. **Expansion:** not opened.
31. **V70:** no diagnostics were run because expansion did not open.
32. **Severe regressions:** one in the effective K1 comparison; five gate-level severe rows across all candidate/revision stages.
33. **Stable mainline:** remains unchanged as corrected K1-AM-SF/F0-CLEAN.
34. **Future mainline:** VD-P is not supported for promotion; it is a mixed default-off research candidate.
35. **Next step:** isolate the parameter-free, uniform formulation-lifecycle cause of VD-P cost on the major witness without changing the split controller.
36. **Unproven:** sealed P-GRB advantage, generalization across new V12/V20/V50 seeds, V70 behavior, universal scale, and literature novelty.

## Entered-stage row closure

- root census: 108 rows; pilot: 32; development: 42; sparse revision: 28;
- confirmation: 18 plus 38 rows; key-long: 22 rows;
- penalty-cover: 0 eligible rows; interaction: 0 eligible rows;
- K1 integration: 34 initial plus 10 conditional rows;
- sealed: 0 authorized rows; expansion: 0 authorized rows;
- missing entered-stage rows: none.
"""
    (EVIDENCE / "final_report.md").write_text(report, encoding="utf-8")

    reproduction = """# Round 55 reproduction commands

Use the frozen one-thread executable and manifests. Bulky native logs remain local and are hash-inventoried.

```powershell
& 'D:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\Common7\\IDE\\CommonExtensions\\Microsoft\\CMake\\CMake\\bin\\ctest.exe' --test-dir build\\official-round55-final-6d0818126 --output-on-failure
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round55_stable_requalification.py --executable build\\official-round55-final-6d0818126\\ExactEBRP.exe
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round55_k1_integration.py --executable build\\official-round55-final-6d0818126\\ExactEBRP.exe --cap 1800 --jobs 4
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\run_round55_k1_integration.py --executable build\\official-round55-final-6d0818126\\ExactEBRP.exe --cap 3600 --instances tight_T_seed3102,tight_T_seed3101,moderate_seed3301,moderate_seed3302,round54_generalization_moderate_3600_V50_M2_Q20_seed1123418787 --jobs 4
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\analyze_round55_k1_integration.py --cap 1800 --output results\\gf_k1_am_sf_station_state_chain_round55\\k1_integration_1800s.csv --decision results\\gf_k1_am_sf_station_state_chain_round55\\k1_integration_1800s_decision.json --split-diff results\\gf_k1_am_sf_station_state_chain_round55\\k1_split_action_diff_1800s.csv
D:\\msys64\\ucrt64\\bin\\python.exe scripts\\finalize_round55_k1_integration.py --rows-1800 results\\gf_k1_am_sf_station_state_chain_round55\\k1_integration_1800s.csv --rows-3600 results\\gf_k1_am_sf_station_state_chain_round55\\k1_integration_3600s.csv --diff-1800 results\\gf_k1_am_sf_station_state_chain_round55\\k1_split_action_diff_1800s.csv --diff-3600 results\\gf_k1_am_sf_station_state_chain_round55\\k1_split_action_diff_3600s.csv --split-output results\\gf_k1_am_sf_station_state_chain_round55\\k1_split_action_diff.csv --decision results\\gf_k1_am_sf_station_state_chain_round55\\k1_integration_decision.json
```

Do not run the sealed or expansion runners for this evidence freeze: their opening audits record false gates.
"""
    (EVIDENCE / "reproduction_commands.md").write_text(reproduction, encoding="utf-8")
    print(f"certificate_rows={len(certificates)} severe_rows={len(severe)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
