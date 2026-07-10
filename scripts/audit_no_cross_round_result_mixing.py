#!/usr/bin/env python3
"""Reject structural-policy summaries that reference result artifacts from another round."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


ROUND = "gf_tailored_bc_structural_policy_round"


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
    ap.add_argument("--results", default=f"results/{ROUND}")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.results).resolve()
    rows: List[Dict[str, Any]] = []
    failures = 0

    def add(artifact: Path, passed: bool, reason: str) -> None:
        nonlocal failures
        if not passed:
            failures += 1
        rows.append({"artifact": str(artifact), "passed": passed, "reason": reason})

    for path in sorted(root.glob("*.csv")):
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
            if row.get("source_round") and row.get("source_round") != ROUND:
                bad.append(f"line{number}:source_round={row.get('source_round')}")
            if row.get("fresh_run") and not as_bool(row.get("fresh_run")):
                bad.append(f"line{number}:fresh_run_false")
            for key, value in row.items():
                if not value or "path" not in key.lower():
                    continue
                normalized = value.replace("\\", "/")
                if normalized.startswith("results/") and not normalized.startswith(f"results/{ROUND}/"):
                    bad.append(f"line{number}:{key}={value}")
        add(path, not bad, "none" if not bad else "|".join(bad[:20]))

    raw_count = 0
    for path in sorted((root / "raw").glob("*.json")):
        raw_count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            add(path, False, f"json_read_error:{exc}")
            continue
        reasons = []
        if data.get("source_round") != ROUND:
            reasons.append("wrong_or_missing_source_round")
        if not as_bool(data.get("fresh_run")):
            reasons.append("fresh_run_not_true")
        package = str(data.get("result_package", "")).replace("\\", "/")
        if package != f"results/{ROUND}":
            reasons.append(f"wrong_result_package:{package}")
        add(path, not reasons, "none" if not reasons else "|".join(reasons))
    add(root / "raw", raw_count > 0, f"fresh_raw_rows={raw_count}")

    out = Path(args.out) if args.out else root / "no_cross_round_result_mixing_audit.csv"
    write_csv(out, rows)
    print(f"audited={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
