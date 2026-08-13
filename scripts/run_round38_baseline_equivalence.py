#!/usr/bin/env python3
"""Pre-mechanism C6 equivalence against the frozen Round 37 executable."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import round35_common as r35
import run_round37_baseline_equivalence as r37


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_frontier_lift_round38"
RUNS = OUT / "baseline_equivalence_pre_mechanism_runs"
OLD_EXE = ROOT / "build_round37" / "official" / "gurobi" / "ExactEBRP.exe"
NEW_EXE = (ROOT / "build_round38_baseline" / "official" / "gurobi" /
           "ExactEBRP.exe")
CASES = (
    "V12_M1",
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main() -> int:
    if not OLD_EXE.is_file() or not NEW_EXE.is_file():
        raise SystemExit("frozen Round 37 and clean Round 38 executables required")
    r37.RUNS = RUNS
    inventory = r35.inventory()
    RUNS.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    run_records: dict[str, Any] = {}
    for instance_id in CASES:
        item = inventory[instance_id]
        old_dir = r37.run_one("round37_frozen", OLD_EXE, item)
        new_dir = r37.run_one("round38_baseline", NEW_EXE, item)
        old_signature = r37.signature(old_dir)
        new_signature = r37.signature(new_dir)
        run_records[instance_id] = {
            "round37_executable_sha256": r37.sha256(OLD_EXE),
            "round38_executable_sha256": r37.sha256(NEW_EXE),
            "round37_result_sha256": r37.sha256(old_dir / "result.json"),
            "round38_result_sha256": r37.sha256(new_dir / "result.json"),
        }
        for component in old_signature:
            problems, max_abs, max_rel, numeric_pairs = r37.compare(
                old_signature[component], new_signature[component], component
            )
            audit_rows.append({
                "instance_id": instance_id,
                "component": component,
                "equivalent": not problems,
                "numeric_pairs": numeric_pairs,
                "max_absolute_delta": max_abs,
                "max_relative_delta": max_rel,
                "problem_count": len(problems),
                "problems": ";".join(problems[:20]),
            })
    passed = all(row["equivalent"] for row in audit_rows)
    csv_path = OUT / "baseline_equivalence_pre_mechanism_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)
    summary = {
        "schema": "round38-pre-mechanism-c6-equivalence-v1",
        "passed": passed,
        "baseline_commit": "1459308492a5eceed523dee53b5f9d79141b5242",
        "process_cap_seconds": r37.PROCESS_CAP,
        "instances": list(CASES),
        "comparison_count": len(audit_rows),
        "semantic_numeric_tolerance": 5e-6,
        "excluded_nondeterministic_fields": [
            "wall clocks", "solver runtime", "Work", "nodes",
            "simplex iterations", "barrier iterations", "memory",
        ],
        "runs": run_records,
        "comparisons": audit_rows,
    }
    write_json(OUT / "baseline_equivalence_pre_mechanism_audit.json", summary)
    lines = [
        "# Round 38 pre-mechanism C6 equivalence",
        "",
        f"Gate passed: **{passed}** ({len(audit_rows)} comparisons).",
        "",
        "The frozen Round 37 executable and a clean executable built from the",
        "Round 38 baseline merge were run in default C6-HGA-FULL mode.",
        "The V12 case exercises targets, requeue, lookahead, and closure; the",
        "V20/M2 case exercises real splits. Clocks and solver-effort counters",
        "are excluded.",
        "",
        "| Instance | Component | Equivalent | Max relative delta |",
        "|---|---|---:|---:|",
    ]
    lines.extend(
        f"| {row['instance_id']} | {row['component']} | "
        f"{row['equivalent']} | {row['max_relative_delta']:.3g} |"
        for row in audit_rows
    )
    (OUT / "baseline_equivalence_pre_mechanism_audit.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "passed": passed,
        "comparison_count": len(audit_rows),
        "instances": list(CASES),
    }, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
