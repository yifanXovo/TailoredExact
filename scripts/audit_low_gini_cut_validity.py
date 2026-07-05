#!/usr/bin/env python3
"""Run the built-in low-Gini tailored cut validity guards."""

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


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_plateau_diagnosis_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = ROOT / args.results
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    tests = [
        "tailored-bc-cut-validity-test",
        "low-gini-l1-centering-test",
        "gini-subset-envelope-test",
        "transfer-cutset-validity-test",
        "s-bucket-coverage-test",
    ]
    rows: List[Dict[str, Any]] = []
    failures = 0
    for method in tests:
        out_json = raw / f"validity_{method}.json"
        cmd = [
            str(EXE),
            "--method", method,
            "--input", str(SMOKE),
            "--lambda", "0.15",
            "--T", "3600",
            "--out", str(out_json),
        ]
        proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        data = read_json(out_json)
        ok = proc.returncode == 0 and data.get("status") == "diagnostic_passed"
        if not ok:
            failures += 1
        rows.append({
            "method": method,
            "row_type": "built_in_validity_test",
            "returncode": proc.returncode,
            "json_path": str(out_json.relative_to(ROOT)),
            "status": data.get("status", "missing"),
            "audit_passed": ok,
            "stdout_tail": proc.stdout[-500:].replace("\n", " "),
        })
    proof_ok = failures == 0
    proof_guard_fields = {
        "tailored_bc_subset_cross_h_centering_rows_added": "subset_cross_h_centering",
        "tailored_bc_local_q_centering_rows_added": "local_q_centering",
        "tailored_bc_compatible_source_transfer_cuts_added": "compatible_source_transfer",
        "tailored_bc_required_external_source_cuts_added": "required_external_source",
    }
    for path in sorted(raw.glob("*.json")):
        if path.name.startswith("validity_"):
            continue
        data = read_json(path)
        if not data:
            continue
        used = []
        for field, family in proof_guard_fields.items():
            try:
                value = float(data.get(field, 0) or 0)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0:
                used.append(family)
        if not used:
            continue
        diagnostic_only = str(data.get("row_class", "")).lower().startswith("diagnostic") or \
            str(data.get("tailored_bc_source_class", "")).lower() == "diagnostic"
        ok = proof_ok or diagnostic_only
        if not ok:
            failures += 1
        rows.append({
            "method": data.get("method", "json_scan"),
            "row_type": "round_json_cut_scan",
            "returncode": "",
            "json_path": str(path.relative_to(ROOT)),
            "status": data.get("status", "missing"),
            "audit_passed": ok,
            "stdout_tail": "families=" + "|".join(used),
        })
    out = ROOT / args.out if args.out else root / "low_gini_cut_validity_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"low_gini_cut_validity_tests={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
