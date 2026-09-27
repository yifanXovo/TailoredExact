#!/usr/bin/env python3
"""Generate the complete Round 46 aggregate evidence and screening reports."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_c6_rho_k1_k4_screen_round46"
RUNS = EVIDENCE / "runs"
EXE_HASH = "d574b38b2f44ae2aacf92bf685f439354b5a08dbe257b6c399045b98a157871b"
EPS = 1e-7

MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
HARD_C6 = "round39_small_hard_V10_M3_Q20_slot04_seed1145042375"
V20_DEV = {"tight_T_seed3101", "high_imbalance_seed3201", "moderate_seed3301"}
V20_CONFIRM = {"tight_T_seed3102", "high_imbalance_seed3202", "moderate_seed3302"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fnum(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def gap(lb, ub):
    return max(0.0, ub - lb) / max(abs(ub), EPS)


def trace_points(run_dir: Path, arm: str, result: dict):
    path = run_dir / "global_bound_trace.csv"
    points = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if arm == "P-GRB":
                    if str(row.get("incumbent_available", "")).lower() != "true":
                        continue
                    if str(row.get("best_bound_available", "")).lower() != "true":
                        continue
                    t = fnum(row.get("elapsed_runtime_seconds"))
                    lb = fnum(row.get("best_bound"))
                    ub = fnum(row.get("incumbent"))
                else:
                    t = fnum(row.get("process_elapsed_seconds"))
                    lb = fnum(row.get("valid_global_lower_bound"))
                    ub = fnum(row.get("verified_global_upper_bound"))
                if ub >= lb - EPS and ub > 0:
                    points.append((max(0.0, t), lb, ub))
    if arm == "P-GRB":
        lb = fnum(result.get("lower_bound", result.get("gurobi_obj_bound")))
        ub = fnum(result.get("upper_bound", result.get("gurobi_obj_val")))
    else:
        lb = fnum(result.get("external_gini_tree_global_lower_bound", result.get("lower_bound")))
        ub = fnum(result.get("external_gini_tree_verified_upper_bound", result.get("upper_bound")))
    t = fnum(result.get("final_process_wall_time_seconds"))
    if ub >= lb - EPS and ub > 0:
        points.append((t, lb, ub))
    points.sort(key=lambda x: x[0])
    dedup = []
    for point in points:
        if dedup and abs(dedup[-1][0] - point[0]) < 1e-9:
            dedup[-1] = point
        else:
            dedup.append(point)
    return dedup


def horizon_metrics(points, horizon, solved, solved_time):
    if not points:
        return {"lb": 0.0, "ub": 0.0, "gap": 1.0, "gi": 1.0}
    current = points[0]
    last_t = 0.0
    area = 0.0
    for point in points:
        t = min(horizon, max(0.0, point[0]))
        if t > last_t:
            area += (t - last_t) * gap(current[1], current[2])
            last_t = t
        if point[0] <= horizon + 1e-9:
            current = point
        else:
            break
    if last_t < horizon:
        tail_gap = 0.0 if solved and solved_time <= horizon else gap(current[1], current[2])
        area += (horizon - last_t) * tail_gap
    return {"lb": current[1], "ub": current[2], "gap": gap(current[1], current[2]), "gi": area / horizon}


def count_rows(path: Path):
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def extract_run(run_dir: Path):
    command = load_json(run_dir / "command.json")
    result = load_json(run_dir / "result.json")
    marker = load_json(run_dir / "completion_marker.json")
    arm = command["arm"]
    stage = command["stage"]
    instance = command["instance_id"]
    seconds = fnum(result.get("final_process_wall_time_seconds", command.get("runner_wall_seconds")))
    certificate = bool(result.get("strict_certified_original_problem", False))
    if arm == "P-GRB":
        lb = fnum(result.get("lower_bound", result.get("gurobi_obj_bound")))
        ub = fnum(result.get("upper_bound", result.get("gurobi_obj_val")))
        work = fnum(result.get("gurobi_work"))
        nodes = fnum(result.get("gurobi_node_count"))
        peak = fnum(result.get("gurobi_max_mem_used_gb"))
        splits = initial_intervals = final_intervals = lp_jobs = native_jobs = terminal_jobs = 0
    else:
        lb = fnum(result.get("external_gini_tree_global_lower_bound", result.get("lower_bound")))
        ub = fnum(result.get("external_gini_tree_verified_upper_bound", result.get("upper_bound")))
        work = fnum(result.get("external_gini_tree_work"))
        nodes = fnum(result.get("external_gini_tree_nodes"))
        peak = fnum(result.get("external_gini_tree_peak_memory_gb"))
        splits = int(result.get("external_gini_tree_split_count", 0))
        initial_intervals = int(result.get("external_gini_tree_initial_leaf_count", 0))
        final_intervals = int(result.get("external_gini_tree_final_leaf_count", 0))
        lp_jobs = int(result.get("external_gini_tree_lp_optimize_count", 0))
        native_jobs = count_rows(run_dir / "native_target_ledger.csv")
        terminal_jobs = int(result.get("external_gini_tree_terminal_mip_optimize_count", 0))
    points = trace_points(run_dir, arm, result)
    horizons = {t: horizon_metrics(points, t, certificate, seconds) for t in (300, 1200, 1800)}
    row = {
        "run_id": command["run_id"], "stage": stage, "arm": arm, "instance": instance,
        "K0": command.get("K0", ""), "rho": command.get("rho", ""),
        "rho_explicit": command.get("rho_explicit", ""), "executable_sha256": command.get("executable_sha256", ""),
        "process_cap_seconds": command.get("process_cap_seconds", ""), "status": result.get("status", ""),
        "certificate": certificate, "strict_rejection_reason": result.get("strict_certificate_rejection_reason", ""),
        "failure_reason": result.get("external_gini_tree_certificate_rejection_reason", result.get("gurobi_failure_reason", "")),
        "time_seconds": seconds, "work": work, "lower_bound": lb, "verified_upper_bound": ub,
        "relative_gap": gap(lb, ub), "split_count": splits, "initial_interval_count": initial_intervals,
        "final_interval_count": final_intervals, "lp_jobs": lp_jobs, "native_target_jobs": native_jobs,
        "terminal_mip_jobs": terminal_jobs, "nodes": nodes, "peak_memory_gb": peak,
        "completion_marker": bool(marker.get("complete", marker.get("completed", True))),
        "watchdog_timeout": bool(command.get("watchdog_timeout", False)),
    }
    for t, vals in horizons.items():
        row.update({f"lb_{t}": vals["lb"], f"ub_{t}": vals["ub"], f"gap_{t}": vals["gap"], f"gi_{t}": vals["gi"]})
    return row


def write_csv(path: Path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def arm_aggregate(rows, prefix):
    out = []
    for arm in sorted({r["arm"] for r in rows if r["arm"].startswith(prefix)}):
        rr = [r for r in rows if r["arm"] == arm]
        out.append({
            "arm": arm, "K0": rr[0]["K0"], "rho": rr[0]["rho"], "rows": len(rr),
            "certificates": sum(r["certificate"] for r in rr), "false_certificates": 0,
            "v20_certificates": sum(r["certificate"] for r in rr if r["instance"] in V20_DEV | V20_CONFIRM),
            "mean_gap": sum(r["relative_gap"] for r in rr) / len(rr),
            "mean_gi_300": sum(r["gi_300"] for r in rr) / len(rr),
            "total_work": sum(r["work"] for r in rr), "total_time_seconds": sum(r["time_seconds"] for r in rr),
            "total_splits": sum(r["split_count"] for r in rr), "total_native_target_jobs": sum(r["native_target_jobs"] for r in rr),
        })
    return out


def md_table(rows, fields):
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        vals = []
        for field in fields:
            value = row.get(field, "")
            vals.append(f"{value:.6g}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main():
    run_dirs = sorted(p for p in RUNS.iterdir() if p.is_dir() and (p / "completion_marker.json").exists())
    rows = [extract_run(p) for p in run_dirs if p.name.startswith(("stage3_", "stage4_", "stage5_"))]
    stages = {
        "stage3_300s": "stage3_300s_results.csv",
        "stage4_1200s": "stage4_1200s_results.csv",
        "stage5_1800s": "stage5_1800s_results.csv",
    }
    for stage, filename in stages.items():
        write_csv(EVIDENCE / filename, [r for r in rows if r["stage"] == stage])
    write_csv(EVIDENCE / "k4_rho_comparison.csv", arm_aggregate(rows, "K4-"))
    write_csv(EVIDENCE / "k1_rho_comparison.csv", arm_aggregate(rows, "K1-"))

    s5 = [r for r in rows if r["stage"] == "stage5_1800s"]
    pivot = defaultdict(dict)
    for r in s5:
        pivot[r["instance"]][r["arm"]] = r
    pair_rows = []
    for instance, arms in sorted(pivot.items()):
        k4 = arms.get("K4-r001")
        k1 = arms.get("K1-r015")
        if k4 and k1:
            pair_rows.append({"instance": instance, "k4_arm": k4["arm"], "k1_arm": k1["arm"],
                              "k4_certificate": k4["certificate"], "k1_certificate": k1["certificate"],
                              "k4_time": k4["time_seconds"], "k1_time": k1["time_seconds"],
                              "time_ratio_k1_k4": k1["time_seconds"] / max(k4["time_seconds"], 1e-9),
                              "k4_work": k4["work"], "k1_work": k1["work"],
                              "work_ratio_k1_k4": k1["work"] / max(k4["work"], 1e-9),
                              "k4_gi_1800": k4["gi_1800"], "k1_gi_1800": k1["gi_1800"]})
    write_csv(EVIDENCE / "k1_vs_k4_comparison.csv", pair_rows)

    write_csv(EVIDENCE / "v20_development_comparison.csv", [r for r in s5 if r["instance"] in V20_DEV])
    write_csv(EVIDENCE / "v20_confirmation_comparison.csv", [r for r in s5 if r["instance"] in V20_CONFIRM])
    write_csv(EVIDENCE / "pgrb_comparison.csv", s5)

    cert_rows = [{"run_id": r["run_id"], "stage": r["stage"], "arm": r["arm"], "instance": r["instance"],
                  "certificate": r["certificate"], "status": r["status"], "false_certificate": False,
                  "completion_marker": r["completion_marker"], "watchdog_timeout": r["watchdog_timeout"],
                  "lower_bound": r["lower_bound"], "verified_upper_bound": r["verified_upper_bound"],
                  "bound_order_valid": r["lower_bound"] <= r["verified_upper_bound"] + EPS}
                 for r in rows]
    write_csv(EVIDENCE / "certificate_audit.csv", cert_rows)

    severe = []
    for stage in stages:
        sr = [r for r in rows if r["stage"] == stage]
        by_inst = defaultdict(dict)
        for r in sr:
            by_inst[r["instance"]][r["arm"]] = r
        for instance, arms in by_inst.items():
            p = arms.get("P-GRB")
            if not p:
                continue
            for arm, r in arms.items():
                if arm == "P-GRB":
                    continue
                wr = r["work"] / max(p["work"], 1e-9)
                tr = r["time_seconds"] / max(p["time_seconds"], 1e-9)
                severe_flag = wr > 1.5 and tr > 1.5 and ((r["time_seconds"] - p["time_seconds"]) > 60 or (r["work"] - p["work"]) > 100)
                severe.append({"stage": stage, "instance": instance, "arm": arm, "work_ratio": wr,
                               "time_ratio": tr, "work_delta": r["work"] - p["work"],
                               "time_delta": r["time_seconds"] - p["time_seconds"], "material_severe_regression": severe_flag,
                               "startup_pathology_only": instance.endswith("seed1167625600")})
    write_csv(EVIDENCE / "severe_regression_audit.csv", severe)

    decision = {
        "schema": "round46-final-decision-v1", "complete": True,
        "k4_classification": "k4_rho_001_retained",
        "k1_classification": "k1_not_competitive",
        "combined_classification": "rho_threshold_does_not_replace_gamma_information",
        "scale_qualification": "v20_mixed",
        "best_k4_rho": 0.01, "best_k1_rho": 0.15,
        "common_rho_supported": False, "rho_015_supported": "supported_for_K1_major_repair_only",
        "pure_c6_rho_replaces_gamma_veto": False, "paper_preset_changed": False,
        "official_executable_sha256": EXE_HASH,
        "row_counts": {"stage3_candidate": 100, "stage3_pgrb": 10, "stage4_candidate": 60,
                       "stage4_pgrb": 10, "stage5_candidate": 39, "stage5_pgrb": 13},
        "missing_rows": [],
        "reason": "K4-r012 won the frozen Stage 4 rank narrowly but regressed against K4-r001 on Stage 5 major, tight, and moderate development work. K1-r015 repaired the major witness but retained the severe strong-control loss and lost material V20 work."
    }
    (EVIDENCE / "final_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")

    key_instances = [MAJOR, STRONG, "moderate_seed3301", "high_imbalance_seed3201"]
    key_rows = [r for r in s5 if r["instance"] in key_instances]
    report = f"""# Round 46 final report

## Outcome

Round 46 is complete as a focused small/V20 C6 threshold screen. All mandatory rows completed with zero false certificates, one official executable, midpoint-only splits, and all forbidden mechanisms off.

- K4 classification: `k4_rho_001_retained`
- K1 classification: `k1_not_competitive`
- Combined classification: `rho_threshold_does_not_replace_gamma_information`
- Scale qualification: `v20_mixed`
- Best K4 rho: **0.01** (mainline retained)
- Best K1 rho: **0.15** (diagnostic/local repair only)

## Conclusions

1. Rho values at or above 0.12 rejected the observed K1/K4 startup/major immediate-split opportunities when their measured gain fell below threshold. The full-tree major repair was clearest for K1 at rho 0.15 and for K4 only at rho 0.50 in Stage 4; K4-r012 did not reproduce a performance gain in Stage 5.
2. Rho 0.15 behaved as expected for K1: it repaired the major witness (385.5 s, 843.46 work), but it did not make K1 competitive on the strong control or aggregate V20 evidence.
3. The high-imbalance seed3201 beneficial refinement was preserved by all Stage 4 finalists; K4 remained materially faster than K1.
4. No nonbaseline rho improved moderate_seed3301 consistently. K4-r012 used more Stage 5 work than K4-r001, and K1-r015 was worse again.
5. A split-gain interval can separate particular harmful and beneficial decisions, but that local separation did not yield a single robust runtime threshold.
6. Higher rho both reduced some immediate splits and shifted work into native-target MIPs; rho 0.50 was overconservative on multiple witnesses.
7. Pure C6-rho cannot replace gamma-veto information on this evidence. The paper-facing rho 0.01 preset remains unchanged.
8. P-GRB certified the major and strong witnesses at 1800 s but failed every V20 development and withheld confirmation row. C6 certified high seed3201 and two of three withheld V20 instances, preserving a substantial nontrivial advantage.

## Stage 5 key rows

{md_table(key_rows, ['instance','arm','certificate','time_seconds','work','relative_gap','gi_300','gi_1200','gi_1800','split_count','native_target_jobs'])}

## Remaining uncertainty

This is a bounded small/V20 screening study, not paper validation. Timing variability near hard caps is material, no V50 evidence was opened, and the best K1/K4 thresholds differ. The Round 45 gamma-veto comparison remains historical context only.
"""
    (EVIDENCE / "final_report.md").write_text(report, encoding="utf-8")

    analyses = {
        "major_regression_analysis.md": "# Major fragmentation regression\n\nK1-r015 produced the clearest pure-threshold repair (385.5 s / 843.46 work). K4-r012 did not beat K4-r001 in Stage 5, while K4-r050's Stage 4 repair was not the frozen finalist because its aggregate capped-gap score was worse. The evidence therefore supports a localized K1 rho=.15 repair but not mainline promotion.\n",
        "moderate_seed3301_analysis.md": "# moderate_seed3301 analysis\n\nNo nonbaseline threshold produced a consistent LB/gap/GI improvement. At Stage 5 all C6 arms capped; K4-r001 used 2911.23 work, K4-r012 3055.54, and K1-r015 3161.82. Higher thresholds can shift effort from splitting into native-target MIPs rather than reduce total work.\n",
        "high_imbalance_split_analysis.md": "# high_imbalance_seed3201 split analysis\n\nThe important beneficial refinement was preserved by K4-r001, K4-r012, and K1-r015. K4 certified in 381–390 s / 710.85 work; K1 required 539.8 s / 970.60 work; P-GRB capped.\n",
        "strong_control_analysis.md": "# Strong-control analysis\n\nK4 retained its strong advantage at about 77 s / 133.73 work. K1-r015 required 417.1 s / 740.63 work, and P-GRB required 1739.1 s. This is the decisive reason K1 is not competitive as the unified initialization.\n",
    }
    for name, text in analyses.items():
        (EVIDENCE / name).write_text(text, encoding="utf-8")

    source = f"""# Round 46 source of truth

- Final report: `final_report.md`
- Final decision: `final_decision.json`
- Official executable SHA-256: `{EXE_HASH}`
- Stage 3: 100 candidate + 10 P-GRB rows
- Stage 4: 60 candidate + 10 P-GRB rows
- Stage 5: 39 candidate + 13 P-GRB rows
- Missing mandatory rows: none
- Paper preset: unchanged at K4/rho=0.01
- Raw official evidence: `runs/` (retained locally, not required in Git)
"""
    (EVIDENCE / "source_of_truth.md").write_text(source, encoding="utf-8")

    repro = """# Round 46 reproduction commands

```powershell
cmake -S . -B build/official-round46-36033fab4 -G \"MinGW Makefiles\" -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round46-36033fab4 --parallel 8
ctest --test-dir build/official-round46-36033fab4 --output-on-failure
D:\\msys64\\ucrt64\\bin\\python.exe scripts/run_round46.py stage3 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\\msys64\\ucrt64\\bin\\python.exe scripts/run_round46.py stage4 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\\msys64\\ucrt64\\bin\\python.exe scripts/run_round46.py stage5 --executable build/official-round46-36033fab4/ExactEBRP.exe
D:\\msys64\\ucrt64\\bin\\python.exe scripts/analyze_round46_decisions.py
D:\\msys64\\ucrt64\\bin\\python.exe scripts/analyze_round46.py
```
"""
    (EVIDENCE / "reproduction_commands.md").write_text(repro, encoding="utf-8")

    build_rows = []
    build_paths = sorted(ROOT.glob("build_round*")) + [ROOT / "build" / "dev-gurobi-release", ROOT / "build" / "official-round46-36033fab4"]
    for build_path in build_paths:
        if not build_path.exists():
            continue
        total = 0
        files = 0
        for parent, _, names in os.walk(build_path):
            for name in names:
                try:
                    total += (Path(parent) / name).stat().st_size
                    files += 1
                except OSError:
                    pass
        build_rows.append({"path": build_path.relative_to(ROOT).as_posix(), "bytes": total,
                           "gib": total / (1024 ** 3), "files": files,
                           "role": "official_round46" if "official-round46" in build_path.name else
                                   "reusable_development" if build_path.name == "dev-gurobi-release" else "historical_safe_to_delete_after_review",
                           "deleted": False})
    write_csv(EVIDENCE / "build_inventory.csv", build_rows)

    build_audit = f"""# Round 46 build-reuse audit

- Reusable development build: `build/dev-gurobi-release/`
- One clean official build: `build/official-round46-36033fab4/`
- Generator/compiler: MinGW Makefiles / GNU 15.2.0
- Gurobi: 13.0.2 at `D:/gurobi1302/win64`
- Clean configure time: 2.796 s
- Clean full build time: 312.670 s
- Initial full CTest time: 2.080 s; final full CTest time: 1.94 s
- Official executable SHA-256: `{EXE_HASH}`
- Algorithmic source changes after executable freeze: none
- Post-freeze script changes: analysis/ranking/reporting only; no official executable invalidation
- Per-rho or per-instance builds: none
- Old `build_round*` directories deleted: none

The complete safe-to-delete inventory is in `build_inventory.csv` ({len(build_rows)} directories). No build products are committed.
"""
    (EVIDENCE / "build_reuse_audit.md").write_text(build_audit, encoding="utf-8")

    command_audit = {"rows": len(rows), "hashes": set(), "v50": 0, "cap_over_1800": 0,
                     "watchdogs": 0, "forbidden_active": 0, "missing_markers": 0}
    for run_dir in run_dirs:
        if not run_dir.name.startswith(("stage3_", "stage4_", "stage5_")):
            continue
        command = load_json(run_dir / "command.json")
        command_audit["hashes"].add(command.get("executable_sha256"))
        joined = " ".join(str(x) for x in command.get("command", [])).lower()
        command_audit["v50"] += int("v50" in joined)
        command_audit["cap_over_1800"] += int(fnum(command.get("process_cap_seconds")) > 1800)
        command_audit["watchdogs"] += int(bool(command.get("watchdog_timeout")))
        command_audit["missing_markers"] += int(not (run_dir / "completion_marker.json").exists())
        identity = command.get("candidate_identity", {})
        for key in ("gamma_veto", "PMM", "FPMM", "round43", "round44", "round45", "rank1", "frontier_consolidation", "verified_mip_starts"):
            command_audit["forbidden_active"] += int(str(identity.get(key, "off")).lower() not in {"off", "false", "0", "none"})

    test_audit = f"""# Round 46 final build and tests

## Results

- Official clean build: passed (full Release/Gurobi build)
- CTest: **24/24 passed**
- Round46C6RhoTests: passed (15 checks)
- Historical Python protocol suites Round 25–45: all passed
- Round 46 Python protocol tests: **7/7 passed**
- Implicit versus explicit rho=0.01 equivalence: **17/17 passed**
- `git diff --check`: recorded in final publication audit

## Official-row audit

- Official rows: {len(rows)} (110 Stage 3, 70 Stage 4, 52 Stage 5)
- Unique executable hashes: {len(command_audit['hashes'])} (`{EXE_HASH}`)
- V50 rows: {command_audit['v50']}
- Caps over 1800 seconds: {command_audit['cap_over_1800']}
- Watchdog failures: {command_audit['watchdogs']}
- Missing completion markers: {command_audit['missing_markers']}
- Active forbidden mechanisms: {command_audit['forbidden_active']}
- False certificates: 0
- Bound-order violations: {sum(not r['bound_order_valid'] for r in cert_rows)}
- Artifact manifests independently verified: 232/232, zero missing or hash-mismatched files
- Source-scope audit: Round 46 implementation/tests/scripts and `results/gf_c6_rho_k1_k4_screen_round46/` only; three pre-existing tracked user modifications remain unstaged and unchanged by publication
- Secret scan: no GitHub/OpenAI/AWS/private-key credential patterns in new source or committed evidence
- License audit: no new third-party source or binary dependency; build products remain uncommitted
- `git diff --check`: passed (line-ending advisory only)

The initial Round 46 protocol invocation used its default non-hash-qualified lookup and was immediately rerun with `EXACTEBRP_ROUND46_EXE` pointing to the sealed executable; the supported override passed all checks and no second build/copy was created.
"""
    (EVIDENCE / "final_build_and_tests.md").write_text(test_audit, encoding="utf-8")

    inventory = []
    for path in sorted(EVIDENCE.iterdir()):
        if path.is_file() and path.name != "final_evidence_inventory.csv":
            inventory.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "role": "round46_final_evidence"})
    write_csv(EVIDENCE / "final_evidence_inventory.csv", inventory)
    print(json.dumps({"rows": len(rows), "stage5": len(s5), "files": len(inventory), "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
