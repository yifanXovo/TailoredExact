#!/usr/bin/env python3
"""Audit transfer cut rows and diagnostic contamination for Tailored-BC rounds."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "build" / "ExactEBRP.exe"
SMOKE = ROOT / "testdata" / "examples" / "gcap_smoke_V4_M1.txt"


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_s_bucket_strengthening_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = ROOT / args.results
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    failures = 0

    validity_json = raw / "validity_transfer-cutset-validity-test.json"
    cmd = [
        str(EXE), "--method", "transfer-cutset-validity-test",
        "--input", str(SMOKE), "--lambda", "0.15", "--T", "3600",
        "--out", str(validity_json),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    data = read_json(validity_json)
    ok = proc.returncode == 0 and data.get("status") == "diagnostic_passed"
    failures += 0 if ok else 1
    rows.append({
        "row_type": "built_in_transfer_validity_test",
        "path": str(validity_json.relative_to(ROOT)),
        "proof_status": "paper_safe_guard" if ok else "failed_guard",
        "paper_safe": ok,
        "diagnostic_contamination": False,
        "audit_passed": ok,
        "failures": "" if ok else "transfer_cutset_validity_test_failed",
    })

    transfer_csv = root / "transfer_cut_audit.csv"
    for row in read_csv(transfer_csv):
        proof = row.get("proof_status", row.get("paper_safe_assumption", ""))
        paper_safe = b(row.get("paper_safe", True))
        diagnostic = str(row.get("row_class", "")).lower().startswith("diagnostic")
        contamination = b(row.get("paper_certificate_contamination")) or (
            diagnostic and b(row.get("selected_for_paper_certificate"))
        )
        reasons: List[str] = []
        if not proof:
            reasons.append("missing_proof_status")
        if contamination:
            reasons.append("diagnostic_transfer_used_for_paper_certificate")
        if not paper_safe and b(row.get("selected_for_paper_certificate")):
            reasons.append("non_paper_safe_transfer_used")
        row_ok = not reasons
        failures += 0 if row_ok else 1
        rows.append({
            **row,
            "row_type": "transfer_cut_audit_row",
            "proof_status": proof,
            "paper_safe": paper_safe,
            "diagnostic_contamination": contamination,
            "audit_passed": row_ok,
            "failures": "|".join(reasons),
        })

    out = Path(args.out) if args.out else root / "transfer_cut_validity_audit.csv"
    write_csv(out, rows)
    print(f"transfer_cut_audit_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
