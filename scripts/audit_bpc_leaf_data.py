#!/usr/bin/env python3
"""Audit BPC leaf validation artifacts against a frozen target manifest."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        first = data["results"][0]
        return first if isinstance(first, dict) else {}
    return data if isinstance(data, dict) else {}


def manifest_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def result_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".json":
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*.json")):
                if child.name.endswith(".trace.json"):
                    continue
                yield child


def close(a: str, b: Any, tol: float = 1e-8) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def basename(value: Any) -> str:
    try:
        return Path(str(value)).name.lower()
    except TypeError:
        return ""


def command_options(result_path: Path) -> Dict[str, str]:
    cmd_path = result_path.with_suffix(".cmd.txt")
    if not cmd_path.exists():
        return {}
    try:
        parts = shlex.split(cmd_path.read_text(encoding="utf-8"), posix=False)
    except ValueError:
        return {}
    opts: Dict[str, str] = {}
    idx = 0
    while idx < len(parts):
        part = parts[idx]
        if part.startswith("--") and idx + 1 < len(parts):
            opts[part] = parts[idx + 1]
            idx += 2
        else:
            idx += 1
    return opts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--results", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    targets = {row["target_name"]: row for row in manifest_rows(Path(args.manifest))}
    rows: List[Dict[str, Any]] = []
    failures = 0
    for result_path in result_files(Path(p) for p in args.results):
        result = load_json(result_path)
        cmd_opts = command_options(result_path)
        stem = result_path.parent.name
        target_name = result.get("bpc_leaf_target") or stem
        if target_name not in targets:
            for known in targets:
                if known in str(result_path):
                    target_name = known
                    break
        gamma_l = result.get("gini_floor", result.get("gamma_L", "")) or cmd_opts.get("--gini-floor", "")
        gamma_u = result.get("gini_cap", result.get("gamma_U", "")) or cmd_opts.get("--gini-cap", "")
        if target_name not in targets:
            result_instance = basename(
                result.get("instance_source_path") or
                result.get("input_path") or
                result.get("instance_name") or
                cmd_opts.get("--input")
            )
            for known, candidate in targets.items():
                if result_instance and result_instance != basename(candidate.get("instance_path")):
                    continue
                if close(candidate.get("gamma_L", ""), gamma_l) and close(candidate.get("gamma_U", ""), gamma_u):
                    target_name = known
                    break
        target = targets.get(target_name, {})
        preset = result.get("algorithm_preset", "")
        oracle_used = bool(result.get("certificate_uses_interval_oracle", False))
        sealed = bool(result.get("sealed_run", False))
        final_json = bool(result)
        gamma_match = bool(target) and close(target.get("gamma_L", ""), gamma_l) and close(target.get("gamma_U", ""), gamma_u)
        ub_match = bool(target) and (
            close(target.get("incumbent_UB", ""), result.get("upper_bound", "")) or
            close(target.get("incumbent_UB", ""), result.get("incumbent_upper_bound", ""))
        )
        pass_row = final_json and gamma_match and preset == "paper-gf-bpc-core" and not oracle_used
        if not pass_row:
            failures += 1
        rows.append({
            "result_file": str(result_path),
            "target_name": target_name,
            "final_json_present": final_json,
            "manifest_target_found": bool(target),
            "gamma_L_manifest": target.get("gamma_L", ""),
            "gamma_U_manifest": target.get("gamma_U", ""),
            "gamma_L_result": gamma_l,
            "gamma_U_result": gamma_u,
            "gamma_range_match": gamma_match,
            "incumbent_UB_manifest": target.get("incumbent_UB", ""),
            "upper_bound_result": result.get("upper_bound", ""),
            "ub_match_or_available": ub_match,
            "algorithm_preset": preset,
            "sealed_run": sealed,
            "certificate_uses_interval_oracle": oracle_used,
            "pricing_calls": result.get("pricing_calls", ""),
            "exact_pricing_closed": result.get("pricing_closure_certified_exact", ""),
            "status": result.get("status", ""),
            "audit_pass": pass_row,
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else [
        "result_file", "target_name", "audit_pass"
    ]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited={len(rows)} failures={failures} out={out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
