#!/usr/bin/env python3
"""Prepare and freeze Round 33 protocol, inventories, and run matrices."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_v10_convergence_round33"
V10_MANIFEST = OUT / "round33_v10_instance_manifest.csv"
ROUND32_EXISTING = (
    ROOT / "results/gf_c6_long_run_validation_round32"
    / "round32_existing_instance_manifest.csv"
)
STARTING_HEAD = "2db8fe5b5c33145e1a8cd6dca86f8459885fa2bf"
OBSERVED_LIVE_MAIN = "e352055138c4ea00f308bed94523ee161dad1a6d"
BRANCH = "codex/round33-v10-convergence-benchmark"
PROCESS_CAP = 3600
SHUTDOWN_MARGIN = 15
WATCHDOG = 3690
REPEAT_CELLS = (
    (1, 20, "high_imbalance"),
    (1, 30, "moderate"),
    (2, 20, "moderate"),
    (2, 30, "tight_T"),
    (3, 30, "high_imbalance"),
    (3, 20, "tight_T"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, material: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    values = list(material)
    columns = fields or list(values[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def anchors() -> list[dict[str, Any]]:
    selected = {
        row["instance_id"]: row for row in rows(ROUND32_EXISTING)
        if row["instance_id"] in {"V12_M1", "V12_M2"}
    }
    if set(selected) != {"V12_M1", "V12_M2"}:
        raise RuntimeError("Round 33 V12 anchors are unavailable")
    output = []
    for name in ("V12_M1", "V12_M2"):
        source = selected[name]
        path = ROOT / source["path"]
        if sha256(path) != source["instance_sha256"]:
            raise RuntimeError(f"V12 anchor hash mismatch: {name}")
        output.append({
            "instance_id": name,
            "path": source["path"],
            "sha256": source["instance_sha256"],
            "scenario": "v12_anchor",
            "family": "v12_anchor",
            "V": int(source["V"]),
            "M": int(source["M"]),
            "Q": int(source["Q"]),
            "T": float(source["T"]),
            "lambda": float(source["lambda"]),
            "origin": "round32_explicit_historical_anchor_identity",
            "frozen_before_round33_results": True,
        })
    return output


def matrix_row(stage: str, item: dict[str, Any], arm: str,
               repetition: str = "primary") -> dict[str, Any]:
    arm_token = "p_grb" if arm == "P-GRB" else "c6_frozen"
    repeat_token = "" if repetition == "primary" else "__repeat1"
    return {
        "round_id": 33,
        "stage_id": stage,
        "run_id": (
            f"{stage}__{item['instance_id']}__{arm_token}"
            f"{repeat_token}__3600s"
        ),
        "instance_id": item["instance_id"],
        "V": item["V"],
        "M": item["M"],
        "Q": item["Q"],
        "scenario": item["scenario"],
        "arm": arm,
        "nominal_process_cap_seconds": PROCESS_CAP,
        "actual_process_cap_seconds": PROCESS_CAP,
        "shutdown_margin_seconds": SHUTDOWN_MARGIN,
        "emergency_watchdog_seconds": WATCHDOG,
        "repetition": repetition,
        "serial_order": 0,
        "frozen_before_stage1_results": True,
    }


def preexisting_worktree() -> list[dict[str, Any]]:
    intended_prefixes = (
        "build_round33/",
        "reference/qualification_round33/",
        "results/gf_v10_convergence_round33/",
    )
    intended_files = {
        "scripts/generate_round33_v10.py",
        "scripts/prepare_round33.py",
        "scripts/round33_common.py",
        "scripts/run_round33_build_and_tests.py",
        "scripts/run_round33_preflight.py",
        "scripts/freeze_round33.py",
        "scripts/run_round33_experiments.py",
        "scripts/analyze_round33.py",
        "scripts/package_round33_evidence.py",
        "tests/round33_protocol_tests.py",
        "tests/round33_runner_tests.py",
    }
    text = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-uall"),
        cwd=ROOT, text=True, encoding="utf-8", errors="replace")
    output = []
    for line in text.splitlines():
        if len(line) < 4:
            continue
        status, path_text = line[:2], line[3:].replace("\\", "/")
        if (
            path_text in intended_files
            or path_text.startswith(intended_prefixes)
        ):
            continue
        path = ROOT / path_text
        output.append({
            "status": status,
            "path": path_text,
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.is_file() else "",
            "preserve_untouched": True,
        })
    return output


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "runs").exists():
        raise RuntimeError("Round 33 official runs already exist")
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=ROOT,
        text=True).strip()
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    if branch != BRANCH or head != STARTING_HEAD:
        raise RuntimeError(
            f"unexpected Round 33 starting identity: {branch} {head}")
    v10 = rows(V10_MANIFEST)
    if len(v10) != 18:
        raise RuntimeError("Round 33 requires exactly 18 V10 instances")
    inventory: list[dict[str, Any]] = []
    for row in v10:
        path = ROOT / row["path"]
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"V10 hash mismatch: {row['instance_id']}")
        inventory.append({
            "instance_id": row["instance_id"],
            "path": row["path"],
            "sha256": row["sha256"],
            "scenario": row["scenario"],
            "family": row["family"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
            "origin": "round33_v10_new",
        })
    anchor_rows = anchors()
    write_csv(OUT / "round33_v12_anchor_manifest.csv", anchor_rows)

    official: list[dict[str, Any]] = []
    for item in inventory:
        for arm in ("P-GRB", "C6-FROZEN"):
            official.append(matrix_row("stage1", item, arm))
    for item in anchor_rows:
        for arm in ("P-GRB", "C6-FROZEN"):
            official.append(matrix_row("stage2", item, arm))
    repeat_items = {
        (item["M"], item["Q"], item["scenario"]): item
        for item in inventory
    }
    selected = []
    for cell in REPEAT_CELLS:
        if cell not in repeat_items:
            raise RuntimeError(f"repeatability cell missing: {cell}")
        item = repeat_items[cell]
        selected.append({
            "instance_id": item["instance_id"],
            "M": item["M"],
            "Q": item["Q"],
            "scenario": item["scenario"],
            "selection_rule": (
                "predeclared_M1_high_moderate_M2_moderate_tight_"
                "M3_high_tight_Q_balanced"
            ),
            "frozen_before_stage1_results": True,
        })
        for arm in ("P-GRB", "C6-FROZEN"):
            official.append(matrix_row(
                "stage3", item, arm, repetition="repeat1"))
    for index, row in enumerate(official, start=1):
        row["serial_order"] = index
    write_csv(OUT / "round33_official_matrix.csv", official)
    write_csv(OUT / "round33_repeatability_freeze.csv", selected)

    stage0 = []
    for index, item in enumerate(inventory + anchor_rows, start=1):
        stage0.append({
            "round_id": 33,
            "stage_id": "stage0_fingerprint",
            "instance_id": item["instance_id"],
            "instance_sha256": item["sha256"],
            "serial_order": index,
            "probe_seconds": 0.001,
            "frozen_before_fingerprint_results": True,
        })
    write_csv(OUT / "round33_stage0_matrix.csv", stage0)

    source = f"""# Round 33 source of truth

- Branch: `{BRANCH}`
- Starting HEAD: `{STARTING_HEAD}`
- Observed live main at preparation: `{OBSERVED_LIVE_MAIN}`
- C6 source: unchanged Round 31/32 `round31-nonblocking-native-bound`
- Primary benchmark: P-GRB versus C6-FROZEN
- New matrix: 18 deterministic V10 instances, M in {{1,2,3}}, Q in
  {{20,30}}, and three scenarios
- Safety cap and primary timing: 3,600 process-entry seconds
- Round 32 raw evidence is read-only and never copied into Round 33 raw rows.
- Official source commit and executable hash are bound later by
  `round33_frozen_manifest.json` after clean build and certificate preflight.
"""
    write_text(OUT / "source_of_truth.md", source)
    protocol = f"""# Round 33 frozen V10 convergence protocol

## Frozen arms

P-GRB is the complete compact original MILP in Gurobi 13.0.2 with one
thread, Seed 0, automatic presolve, zero relative/absolute MIP gaps, and no
HGA or decomposition. C6-FROZEN is the unchanged validated Round 31/32
nonblocking native-bound Gini interval decomposition with its fixed HGA,
four initial intervals, rho 0.01, lazy child lookahead, adaptive split
geometry, native targets, requeues, and exact-closure semantics.

## Instances and pre-result freeze

The 18 V10 instances and six repeats are frozen in their manifests before
any solver result. Seeds are SHA-256-derived from the starting commit,
`round33-v10-convergence`, M, Q, and scenario. Structural invalidity alone
permits the recorded counter-based deterministic replacement rule; solver
performance never permits replacement.

Every V10 and V12 canonical compact model is imported before official runs.
Its Gurobi fingerprint, model export hash, instance hash, executable hash,
and verifier contract are frozen. Each V10 fingerprint is then exercised by
a non-performance native-optimal certificate-promotion preflight. No
fingerprint is created from an official result.

## Timing and execution

Every row is an independent process with a 3,600-second process-entry cap,
a {SHUTDOWN_MARGIN}-second internal shutdown margin, and a {WATCHDOG}-second
external emergency watchdog. Rows stop naturally after strict
original-problem certification. The primary certificate time is
`final_process_wall_time_seconds`, covering process entry, parsing, HGA when
present, construction, scheduling, native solves, verification, and exact
finalization. Solver-only `runtime_seconds` is diagnostic only.

Runs are serial, one-thread, and checksum-resumable at row granularity.
Algorithmic solve-state resume is not claimed. Partial and invalid rows are
preserved with explicit reasons. Result JSON is parsed after child exit and
all required artifacts are hashed before an atomic completion marker.

## Comparison and traces

Stage 1 contains 18 V10 x two arms (36 rows). Stage 2 contains V12_M1 and
V12_M2 x two arms (four rows). Stage 3 independently repeats the six
predeclared V10 cells x two arms (12 rows). Certificate-time speedup is
P-GRB time divided by C6 time when both strictly certify. Timing ties use
max(0.05 seconds, 0.1% of the faster time). Shifted geometric means use a
one-second shift and only both-certified pairs.

AUC and gap thresholds use observed, left-continuous bound steps only. A
real final-result bound may be added at its recorded process-entry time; no
interpolation or post-final-event extension is allowed. Round 32 evidence
may appear only in explicitly historical derived tables and is never mixed
with Round 33 raw rows.
"""
    write_text(OUT / "round33_protocol.md", protocol)
    baseline = preexisting_worktree()
    write_csv(
        OUT / "preexisting_worktree_manifest.csv", baseline,
        ["status", "path", "exists", "bytes", "preserve_untouched"])
    write_json(OUT / "round33_preparation_summary.json", {
        "schema": "round33-preparation-v1",
        "branch": branch,
        "starting_head": head,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "v10_instances": len(inventory),
        "v12_anchors": len(anchor_rows),
        "official_rows": len(official),
        "stage1_rows": sum(row["stage_id"] == "stage1" for row in official),
        "stage2_rows": sum(row["stage_id"] == "stage2" for row in official),
        "stage3_rows": sum(row["stage_id"] == "stage3" for row in official),
        "preexisting_worktree_entries": len(baseline),
        "prepared_at_unix_seconds": time.time(),
        "official_results_started": False,
    })
    print(json.dumps({
        "v10_instances": len(inventory),
        "official_rows": len(official),
        "repeat_instances": len(selected),
        "preexisting_entries": len(baseline),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
