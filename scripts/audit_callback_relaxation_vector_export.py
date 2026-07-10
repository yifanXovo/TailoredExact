#!/usr/bin/env python3
"""Audit Tailored-BC callback relaxation-vector export artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return default


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def candidate_jsons(results: Path) -> Iterable[Path]:
    direct = results / "callback_vector_smoke.json"
    if direct.exists():
        yield direct
    raw = results / "raw"
    if raw.exists():
        for path in sorted(raw.glob("*.json")):
            data = read_json(path)
            if (
                data.get("method") == "tailored-bc-relaxation-vector-smoke-test"
                or "callback_vector" in path.name
                or as_bool(data.get("tailored_bc_callback_vector_api_called"))
            ):
                yield path


def audit_row(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    status = str(data.get("tailored_bc_callback_vector_export_status", "not_attempted"))
    working = as_bool(data.get("tailored_bc_callback_vector_export_working"))
    claimed = as_bool(data.get("tailored_bc_callback_vector_export_claimed")) or as_bool(
        data.get("tailored_bc_callback_vector_api_called")
    )
    nonzero = as_int(data.get("tailored_bc_callback_vector_nonzero_values_count"))
    rc = as_int(data.get("tailored_bc_callback_vector_api_return_code"), -999999)
    names = str(data.get("tailored_bc_callback_vector_sample_variable_names", ""))
    values = str(data.get("tailored_bc_callback_vector_sample_variable_values", ""))
    role = str(data.get("paper_certificate_role", "diagnostic_only"))
    method = str(data.get("method", ""))
    failures: List[str] = []

    if working:
        if not claimed:
            failures.append("working_without_claimed_api_call")
        if rc != 0:
            failures.append("working_with_nonzero_api_return_code")
        if nonzero <= 0:
            failures.append("working_without_nonzero_values")
        if not names or names == "not_available" or names.strip(" ;") == "":
            failures.append("working_without_sample_variable_names")
        if not values or values == "not_available" or values.strip(" ;") == "":
            failures.append("working_without_sample_variable_values")
    elif claimed and status == "callback_vector_export_working":
        failures.append("status_claims_working_but_working_flag_false")

    if not working:
        if names not in {"", "not_available"} and values == "0":
            failures.append("missing_vector_appears_zero_filled")
        if values == "0" and nonzero == 0:
            failures.append("missing_values_zero_filled")

    if method == "tailored-bc-relaxation-vector-smoke-test" and role not in {
        "diagnostic_only",
        "diagnostic",
        "none",
        "",
    }:
        failures.append("smoke_vector_row_not_diagnostic_only")
    if as_bool(data.get("certified_original_problem")) and method == "tailored-bc-relaxation-vector-smoke-test":
        failures.append("diagnostic_vector_row_marked_original_certificate")

    return {
        "path": str(path.relative_to(ROOT) if path.is_absolute() else path),
        "method": method,
        "status": status,
        "claimed": claimed,
        "working": working,
        "api_return_code": rc,
        "nonzero_values_count": nonzero,
        "sample_variable_names": names,
        "sample_variable_values": values,
        "paper_certificate_role": role,
        "audit_passed": not failures,
        "failure_reason": ";".join(failures) if failures else "none",
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(ROOT / "results" / "gf_tailored_bc_stability_round"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    results = Path(args.results)
    rows = [audit_row(path, read_json(path)) for path in candidate_jsons(results)]
    if not rows:
        rows = [{
            "path": "",
            "method": "",
            "status": "missing_callback_vector_artifact",
            "claimed": False,
            "working": False,
            "api_return_code": "",
            "nonzero_values_count": "",
            "sample_variable_names": "",
            "sample_variable_values": "",
            "paper_certificate_role": "",
            "audit_passed": False,
            "failure_reason": "no_callback_vector_smoke_json_found",
        }]

    out = Path(args.out) if args.out else results / "relaxation_vector_export_audit.csv"
    write_csv(out, rows)
    failed = [row for row in rows if not as_bool(row.get("audit_passed"))]
    if failed:
        for row in failed:
            print(f"FAIL {row['path']}: {row['failure_reason']}", file=sys.stderr)
        return 1
    print(f"PASS callback vector export audit ({len(rows)} row(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
