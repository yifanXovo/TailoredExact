#!/usr/bin/env python3
"""Run compact fixed-interval cutoff-oracle jobs for unresolved frontier leaves.

The script is intentionally conservative.  It never upgrades a focused interval
result into a full certificate; it only records per-leaf oracle evidence that a
separate full-ledger merge audit can consume.
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
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def unresolved_final_leaves(rows: list[dict]) -> list[dict]:
    return [
        row for row in rows
        if row.get("interval_status") == "unresolved"
    ]


def selected(rows: list[dict], ids: str) -> list[dict]:
    if not ids.strip():
        return unresolved_final_leaves(rows)
    wanted = {x.strip() for x in ids.split(",") if x.strip()}
    return [row for row in rows if row.get("interval_id", "").strip() in wanted]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--instance", required=True, type=Path)
    parser.add_argument("--exe", default="build/ExactEBRP.exe", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--target-ids", default="")
    parser.add_argument("--time-limit", type=float, default=3600.0)
    parser.add_argument("--lambda", dest="lam", type=float, default=0.15)
    parser.add_argument("--T", type=float, default=3600.0)
    parser.add_argument("--epsilon", type=float, default=1e-8)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    out = args.output_dir
    raw = out / "raw"
    logs = out / "logs"
    cplex = out / "cplex"
    raw.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    cplex.mkdir(parents=True, exist_ok=True)

    rows = selected(read_csv(args.ledger), args.target_ids)
    summary: list[dict] = []
    commands: list[str] = []
    for row in rows:
        interval_id = row.get("interval_id", "unknown")
        gamma_l = row.get("gamma_L", "")
        gamma_u = row.get("gamma_U", "")
        ub = row.get("incumbent_upper_bound", "")
        stem = f"interval_oracle_{interval_id}_{gamma_l}_{gamma_u}".replace(".", "p").replace(",", "_")
        out_json = raw / f"{stem}.json"
        lp = cplex / f"{stem}.lp"
        sol = cplex / f"{stem}.sol"
        log = logs / f"{stem}.cplex.log"
        cmd = [
            str(args.exe),
            "--method", "interval-cutoff-oracle",
            "--input", str(args.instance),
            "--lambda", str(args.lam),
            "--T", str(args.T),
            "--threads", str(args.threads),
            "--time-limit", str(args.time_limit),
            "--interval-exact-cutoff-oracle", "compact-mip",
            "--interval-exact-cutoff-gamma-L", str(gamma_l),
            "--interval-exact-cutoff-gamma-U", str(gamma_u),
            "--interval-exact-cutoff-UB", str(ub),
            "--interval-exact-cutoff-epsilon", str(args.epsilon),
            "--interval-exact-cutoff-time-limit", str(args.time_limit),
            "--interval-exact-cutoff-export-lp", str(lp),
            "--interval-exact-cutoff-result", str(sol),
            "--log", str(log),
            "--out", str(out_json),
        ]
        commands.append(" ".join(cmd))
        if args.execute:
            subprocess.run(cmd, check=False)
        result = load_json(out_json)
        summary.append({
            "interval_id": interval_id,
            "gamma_L": gamma_l,
            "gamma_U": gamma_u,
            "previous_interval_lower_bound": row.get("interval_lower_bound", ""),
            "incumbent_upper_bound": ub,
            "oracle_status": result.get("status", "not_run"),
            "oracle_certificate_basis": result.get("interval_exact_cutoff_certificate_basis", ""),
            "oracle_solver_status": result.get("interval_exact_cutoff_solver_status", ""),
            "oracle_proven_infeasible": result.get("interval_exact_cutoff_proven_infeasible", ""),
            "oracle_feasible_improving": result.get("interval_exact_cutoff_feasible_improving", ""),
            "oracle_timeout": result.get("interval_exact_cutoff_timeout", ""),
            "oracle_best_bound": result.get("interval_exact_cutoff_best_bound", ""),
            "oracle_objective": result.get("interval_exact_cutoff_objective", ""),
            "oracle_gap": result.get("interval_exact_cutoff_gap", result.get("gap", "")),
            "runtime_seconds": result.get("runtime_seconds", ""),
            "nodes": result.get("interval_exact_cutoff_nodes", ""),
            "lp_path": str(lp),
            "solution_path": str(sol),
            "log_path": str(log),
            "raw_result": str(out_json),
            "command": " ".join(cmd),
        })

    write_csv(out / "high_imbalance_seed3202_interval_oracle_results.csv", summary)
    with (out / "interval_oracle_commands.md").open("w", encoding="utf-8") as fh:
        fh.write("# Interval Cutoff Oracle Commands\n\n")
        for command in commands:
            fh.write("```powershell\n")
            fh.write(command)
            fh.write("\n```\n\n")


if __name__ == "__main__":
    main()
