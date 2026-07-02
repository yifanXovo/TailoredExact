#!/usr/bin/env python3
"""Audit objective/convention metadata for GF compact-BC result rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def iter_json(raw_dir: Path) -> Iterable[tuple[Path, Dict[str, Any]]]:
    for path in sorted(raw_dir.rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "trace_schema" not in data:
            yield path, data


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def has_note(data: Dict[str, Any], needle: str) -> bool:
    notes = data.get("notes", [])
    if not isinstance(notes, list):
        notes = [notes]
    return any(needle.lower() in str(note).lower() for note in notes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_strengthening_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    results = Path(args.results)
    raw_dir = results / "raw"
    rows: List[Dict[str, Any]] = []
    failures = 0
    for path, data in iter_json(raw_dir):
        method = str(data.get("method", ""))
        preset = str(data.get("algorithm_preset", ""))
        failures_here: List[str] = []
        if method in {"gcap-frontier", "cplex", "interval-cutoff-oracle"}:
            if not data.get("input_path"):
                failures_here.append("missing_input_path")
            if not has_note(data, "distance") and not has_note(data, "coordinate"):
                failures_here.append("missing_distance_convention_note")
            if as_bool(data.get("certified_original_problem")):
                if not as_bool(data.get("verifier_passed")):
                    failures_here.append("certified_without_verifier")
                if not as_bool(data.get("solves_original_objective", True)):
                    failures_here.append("certified_not_original_objective")
            if preset == "paper-gf-compact-bc":
                if as_bool(data.get("incumbent_archive_auto")):
                    failures_here.append("archive_auto_enabled")
                if not as_bool(data.get("no_archive_scanning", True)):
                    failures_here.append("archive_scanning_not_disabled")
                if not as_bool(data.get("no_external_known_ub", True)):
                    failures_here.append("external_known_ub_not_disabled")
                if as_bool(data.get("certificate_uses_bpc_tree")):
                    failures_here.append("bpc_used_in_compact_bc_certificate")
        if failures_here:
            failures += 1
        rows.append(
            {
                "file": str(path),
                "method": method,
                "algorithm_preset": preset,
                "status": data.get("status", ""),
                "certified_original_problem": data.get("certified_original_problem", ""),
                "verifier_passed": data.get("verifier_passed", ""),
                "thread_fairness_class": data.get("thread_fairness_class", ""),
                "audit_passed": not failures_here,
                "failures": "|".join(failures_here),
            }
        )

    out_path = Path(args.out) if args.out else results / "objective_convention_audit.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "file",
            "method",
            "algorithm_preset",
            "status",
            "certified_original_problem",
            "verifier_passed",
            "thread_fairness_class",
            "audit_passed",
            "failures",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
