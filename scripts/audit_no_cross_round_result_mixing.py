#!/usr/bin/env python3
"""Reject result packages that reference evidence artifacts from another round."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def as_bool(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["artifact", "passed", "reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.results).resolve()
    round_name = root.name
    package_prefix = f"results/{round_name}/"
    rows: List[Dict[str, Any]] = []
    failures = 0

    def add(artifact: Path, passed: bool, reason: str) -> None:
        nonlocal failures
        if not passed:
            failures += 1
        rows.append({"artifact": str(artifact), "passed": passed, "reason": reason})

    result_pointer_tokens = {
        "artifact", "json", "result", "progress", "model", "log", "ledger",
        "trace", "output", "summary", "raw_file", "csv_file",
    }

    def is_result_pointer(key: str) -> bool:
        lowered = key.lower()
        if lowered in {"result_package", "source_round", "fresh_run"}:
            return False
        return any(token in lowered for token in result_pointer_tokens)

    for path in sorted(root.rglob("*.csv")):
        if path.name == Path(args.out).name:
            continue
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                table = list(csv.DictReader(handle))
        except Exception as exc:
            add(path, False, f"csv_read_error:{exc}")
            continue
        bad: List[str] = []
        for number, row in enumerate(table, 2):
            if row.get("source_round") and row.get("source_round") != round_name:
                bad.append(f"line{number}:source_round={row.get('source_round')}")
            if row.get("fresh_run") and not as_bool(row.get("fresh_run")):
                bad.append(f"line{number}:fresh_run_false")
            for key, value in row.items():
                if not value or not is_result_pointer(key):
                    continue
                normalized = value.replace("\\", "/")
                if normalized.startswith("results/") and not normalized.startswith(package_prefix):
                    bad.append(f"line{number}:{key}={value}")
        add(path, not bad, "none" if not bad else "|".join(bad[:20]))

    raw_count = 0
    for path in sorted((root / "raw").rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        raw_count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            add(path, False, f"json_read_error:{exc}")
            continue
        reasons = []
        if data.get("source_round") != round_name:
            reasons.append("wrong_or_missing_source_round")
        if not as_bool(data.get("fresh_run")):
            reasons.append("fresh_run_not_true")
        package = str(data.get("result_package", "")).replace("\\", "/")
        if package != f"results/{round_name}":
            reasons.append(f"wrong_result_package:{package}")
        for key, value in data.items():
            if not isinstance(value, str) or not value or not is_result_pointer(key):
                continue
            normalized = value.replace("\\", "/")
            if normalized.startswith("results/") and not normalized.startswith(package_prefix):
                reasons.append(f"cross_round_pointer:{key}={value}")
        add(path, not reasons, "none" if not reasons else "|".join(reasons))
    add(root / "raw", raw_count > 0, f"fresh_raw_rows={raw_count}")

    out = Path(args.out) if args.out else root / "no_cross_round_result_mixing_audit.csv"
    write_csv(out, rows)
    print(f"audited={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
