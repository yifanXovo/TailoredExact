#!/usr/bin/env python3
"""Focused interval-closure harness for V20 stress rows.

The harness is deliberately conservative.  It can run focus-only interval
commands and summarize their bounds, but it marks merge safety as false unless
the focused evidence can be proven to cover the exact unresolved full-frontier
leaf.  This prevents focus-only diagnostics from becoming original-problem
certificates by accident.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def parse_ids(text: str) -> set[str]:
    return {part.strip() for part in text.split(",") if part.strip()}


def selected_intervals(rows: list[dict], target_ids: str, target_range: str) -> list[dict]:
    ids = parse_ids(target_ids)
    if ids:
        return [r for r in rows if str(r.get("interval_id", "")).strip() in ids]
    if target_range:
        lo, hi = [float(x.strip()) for x in target_range.split(",", 1)]
        out = []
        for r in rows:
            if abs(float(r["gamma_L"]) - lo) <= 1e-9 and abs(float(r["gamma_U"]) - hi) <= 1e-9:
                out.append(r)
        return out
    return [r for r in rows if r.get("interval_status") == "unresolved"]


def command_for(args: argparse.Namespace, row: dict, out_json: Path, progress: Path) -> list[str]:
    lo = row["gamma_L"]
    hi = row["gamma_U"]
    cmd = [
        str(args.exe),
        "--method", "gcap-frontier",
        "--algorithm-preset", "paper-bpc-core",
        "--input", str(args.instance),
        "--lambda", str(args.lam),
        "--T", str(args.T),
        "--time-limit", str(args.time_limit),
        "--frontier-focus-only", "true",
        "--frontier-focus-range", f"{lo},{hi}",
        "--frontier-focus-time-limit", str(args.time_limit),
        "--frontier-focus-relax-seconds", str(args.relax_seconds),
        "--route-mask-max-v", "12",
        "--large-compact-flow-relaxation", args.compact_flow,
        "--large-compact-flow-time-limit", str(args.compact_time_limit),
        "--relaxation-portfolio-mode", args.portfolio_mode,
        "--relaxation-portfolio-max-variants", str(args.max_variants),
        "--relaxation-certificate-mode", args.certificate_mode,
        "--cutoff-feasibility-epsilon", str(args.cutoff_epsilon),
        "--interval-closure-mode", "focus",
        "--interval-closure-input", str(args.input),
        "--interval-closure-target-ids", str(row.get("interval_id", "")),
        "--interval-closure-range", f"{lo},{hi}",
        "--interval-closure-variant-mode", args.variant_mode,
        "--out", str(out_json),
        "--progress-log", str(progress),
        "--progress-interval-seconds", "60",
    ]
    if args.connectivity:
        cmd += ["--large-compact-flow-connectivity", "true"]
    if args.service_min:
        cmd += ["--service-operation-min-handling", "true"]
    if args.penalty_movement:
        cmd += ["--penalty-movement-lb-cuts", "true"]
    if args.transfer_subset:
        cmd += ["--transfer-subset-capacity-cuts", "true"]
    return cmd


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--instance", required=True, type=Path)
    parser.add_argument("--exe", default="build/ExactEBRP.exe", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--target-ids", default="")
    parser.add_argument("--target-range", default="")
    parser.add_argument("--time-limit", type=float, default=300.0)
    parser.add_argument("--relax-seconds", type=float, default=120.0)
    parser.add_argument("--lam", type=float, default=0.15)
    parser.add_argument("--T", type=float, default=3600.0)
    parser.add_argument("--variant-mode", default="exhaustive")
    parser.add_argument("--portfolio-mode", default="exhaustive")
    parser.add_argument("--max-variants", type=int, default=5)
    parser.add_argument("--certificate-mode", default="both")
    parser.add_argument("--cutoff-epsilon", type=float, default=1e-8)
    parser.add_argument("--compact-flow", default="mip-light")
    parser.add_argument("--compact-time-limit", type=float, default=60.0)
    parser.add_argument("--connectivity", action="store_true")
    parser.add_argument("--service-min", action="store_true")
    parser.add_argument("--penalty-movement", action="store_true")
    parser.add_argument("--transfer-subset", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = args.output_dir / "raw"
    progress = args.output_dir / "progress"
    raw.mkdir(exist_ok=True)
    progress.mkdir(exist_ok=True)

    rows = selected_intervals(read_csv(args.input), args.target_ids, args.target_range)
    trace_rows: list[dict] = []
    commands: list[str] = []
    for row in rows:
        interval_id = str(row.get("interval_id", "unknown"))
        stem = f"focus_interval_{interval_id}_{row['gamma_L']}_{row['gamma_U']}".replace(".", "p").replace(",", "_")
        out_json = raw / f"{stem}.json"
        progress_csv = progress / f"{stem}.csv"
        cmd = command_for(args, row, out_json, progress_csv)
        commands.append(" ".join(cmd))
        if args.execute:
            subprocess.run(cmd, check=False)
        result = load_json(out_json)
        focused_lb = result.get("lower_bound", "")
        focused_ub = result.get("upper_bound", "")
        focused_status = result.get("status", "not_run" if not args.execute else "missing_output")
        cutoff_infeasible = result.get("cutoff_feasibility_infeasible", False)
        exact_match = True
        safe_to_merge = False
        merge_reason = "not_executed"
        if args.execute:
            merge_reason = "focused_interval_diagnostic_only"
            if focused_status == "optimal" and cutoff_infeasible:
                merge_reason = "focused interval closed, but full-ledger merge still requires exact coverage audit"
        trace_rows.append({
            "interval_id": interval_id,
            "gamma_L": row["gamma_L"],
            "gamma_U": row["gamma_U"],
            "previous_interval_lb": row.get("interval_lower_bound", ""),
            "previous_interval_status": row.get("interval_status", ""),
            "focused_status": focused_status,
            "focused_lb": focused_lb,
            "focused_ub": focused_ub,
            "focused_gap": result.get("gap", ""),
            "cutoff_feasibility_infeasible": cutoff_infeasible,
            "selected_relaxation_variant": result.get("selected_relaxation_variant", ""),
            "relaxation_variants_tried": result.get("relaxation_variants_tried", ""),
            "safe_to_merge_full_ledger": safe_to_merge,
            "merge_reason": merge_reason,
            "raw_result": str(out_json),
            "command": " ".join(cmd),
        })

    write_csv(args.output_dir / "interval_closure_trace.csv", trace_rows)
    merged = []
    for row in read_csv(args.input):
        merged.append({
            **row,
            "focused_update_available": "false",
            "focused_safe_to_merge": "false",
            "focused_merge_reason": "no_safe_full_coverage_merge_performed",
        })
    write_csv(args.output_dir / "interval_ledger_merged.csv", merged)
    with (args.output_dir / "interval_closure_commands.md").open("w", encoding="utf-8") as fh:
        fh.write("# Interval Closure Commands\n\n")
        for cmd in commands:
            fh.write("```powershell\n")
            fh.write(cmd)
            fh.write("\n```\n\n")


if __name__ == "__main__":
    main()
