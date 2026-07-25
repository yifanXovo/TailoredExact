#!/usr/bin/env python3
"""Freeze Round 32 instances, stage membership, commands, and provenance."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
ROUND31 = ROOT / "results" / "gf_nonblocking_gurobi_c6_round31"
STARTING_HEAD = "919fd688a29a730d897db612213982ba8792a53f"
OBSERVED_LIVE_MAIN = "2acc29c5556ddd3b229d65fd2b3fb8982ce6b8d2"
BRANCH = "codex/round32-c6-long-run-validation"
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    columns = fields or list(material[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def q_from_instance(path: Path, expected_m: int) -> int:
    fields = path.read_text(encoding="utf-8").splitlines()[0].split(maxsplit=2)
    if len(fields) != 3 or int(fields[1]) != expected_m:
        raise RuntimeError(f"invalid instance header: {path}")
    capacities = fields[2].strip()
    if not (capacities.startswith("[") and capacities.endswith("]")):
        raise RuntimeError(f"invalid vehicle-capacity header: {path}")
    values = [int(value.strip()) for value in capacities[1:-1].split(",")]
    if len(values) != expected_m or len(set(values)) != 1:
        raise RuntimeError(f"nonuniform qualification Q values: {path}")
    return values[0]


def existing_manifest() -> list[dict[str, Any]]:
    old = csv_rows(ROUND31 / "round31_instance_manifest.csv")
    if len(old) != 23:
        raise RuntimeError(f"expected 23 Round 31 authoritative rows, got {len(old)}")
    rows: list[dict[str, Any]] = []
    for item in old:
        path = ROOT / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise RuntimeError(
                f"authoritative instance mismatch: {item['instance']}")
        m = int(item["M"])
        rows.append({
            "instance_id": item["instance"],
            "path": item["path"],
            "instance_sha256": item["sha256"],
            "bytes": path.stat().st_size,
            "family": item["family"],
            "V": int(item["V"]),
            "M": m,
            "Q": q_from_instance(path, m),
            "T": 3600,
            "lambda": "0.15",
            "origin": (
                "round31_sealed_heldout"
                if item["sealed_heldout"].lower() == "true"
                else "round31_existing_primary"),
            "sealed_heldout": item["sealed_heldout"].lower(),
            "frozen_before_round32_solver_results": "true",
        })
    write_csv(OUT / "round32_existing_instance_manifest.csv", rows)
    return rows


def multi_manifest() -> list[dict[str, Any]]:
    rows = csv_rows(OUT / "round32_multi_m_manifest.csv")
    if len(rows) != 12:
        raise RuntimeError(f"expected 12 multi-M rows, got {len(rows)}")
    expected = {
        (v, m, family)
        for v in (20, 50)
        for m in (2, 4)
        for family in ("high_imbalance", "moderate", "tight_T")
    }
    observed: set[tuple[int, int, str]] = set()
    for item in rows:
        path = ROOT / item["path"]
        key = (int(item["V"]), int(item["M"]), item["stress_type"])
        observed.add(key)
        if (
            not path.is_file()
            or sha256(path) != item["sha256"]
            or item["structurally_valid"].lower() != "true"
            or int(item["Q"]) != 30
        ):
            raise RuntimeError(f"multi-M freeze mismatch: {item['instance_id']}")
    if observed != expected:
        raise RuntimeError("multi-M V/M/family coverage is incomplete")
    return rows


def inventory(existing: list[dict[str, Any]],
              multi: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    items = {row["instance_id"]: dict(row) for row in existing}
    for row in multi:
        items[row["instance_id"]] = {
            "instance_id": row["instance_id"],
            "path": row["path"],
            "instance_sha256": row["sha256"],
            "bytes": (ROOT / row["path"]).stat().st_size,
            "family": row["stress_type"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "T": int(row["T"]),
            "lambda": row["lambda"],
            "origin": "round32_multi_m",
            "sealed_heldout": "false",
            "frozen_before_round32_solver_results": "true",
        }
    if len(items) != 35:
        raise RuntimeError(f"expected 35 total Round 32 instances, got {len(items)}")
    return items


def one(items: dict[str, dict[str, Any]], *, origin: str | None = None,
        v: int | None = None, m: int | None = None,
        family: str | None = None) -> str:
    choices = [
        name for name, item in items.items()
        if (origin is None or item["origin"] == origin)
        and (v is None or int(item["V"]) == v)
        and (m is None or int(item["M"]) == m)
        and (family is None or item["family"] == family)
    ]
    if len(choices) != 1:
        raise RuntimeError(
            f"selection is not unique: origin={origin} V={v} M={m} "
            f"family={family}: {choices}")
    return choices[0]


def matrix_and_subsets(items: dict[str, dict[str, Any]]) -> None:
    existing = [
        name for name, item in items.items()
        if item["origin"] != "round32_multi_m"
    ]
    multi = [
        name for name, item in items.items()
        if item["origin"] == "round32_multi_m"
    ]
    stage3 = [
        name for name, item in items.items() if int(item["V"]) == 50
    ]
    if len(existing) != 23 or len(multi) != 12 or len(stage3) != 12:
        raise RuntimeError("primary stage cardinality mismatch")
    stage3_rows = [{
        "serial_order": index,
        "instance_id": name,
        "path": items[name]["path"],
        "instance_sha256": items[name]["instance_sha256"],
        "family": items[name]["family"],
        "V": items[name]["V"],
        "M": items[name]["M"],
        "origin": items[name]["origin"],
        "budget_seconds": 3600,
        "frozen_before_round32_1800s_results": "true",
    } for index, name in enumerate(stage3, start=1)]
    write_csv(OUT / "round32_stage3_freeze.csv", stage3_rows)

    sealed_v50_moderate = one(
        items, origin="round31_sealed_heldout", v=50, m=3,
        family="moderate")
    new_v20_high_m2 = one(
        items, origin="round32_multi_m", v=20, m=2,
        family="high_imbalance")
    new_v20_moderate_m2 = one(
        items, origin="round32_multi_m", v=20, m=2,
        family="moderate")
    new_v50_moderate_m4 = one(
        items, origin="round32_multi_m", v=50, m=4,
        family="moderate")
    new_v50_tight_m4 = one(
        items, origin="round32_multi_m", v=50, m=4,
        family="tight_T")
    stage4 = (
        "V12_M2",
        "high_imbalance_seed3202",
        "moderate_seed3302",
        "tight_T_seed3101",
        "high_imbalance_seed6202",
        sealed_v50_moderate,
        new_v20_high_m2,
        new_v50_moderate_m4,
    )
    stage5 = (
        "V12_M1",
        "V12_M2",
        "high_imbalance_seed3202",
        "moderate_seed3302",
        "tight_T_seed3101",
        "moderate_seed6301",
        sealed_v50_moderate,
    )
    repeat = (
        "V12_M2",
        "high_imbalance_seed3202",
        "moderate_seed3302",
        "tight_T_seed3101",
        "high_imbalance_seed6202",
        sealed_v50_moderate,
        new_v20_moderate_m2,
        new_v50_tight_m4,
    )
    rows: list[dict[str, Any]] = []

    def add(stage_id: str, names: Iterable[str], arms: Iterable[str],
            budget: int, repetition: int = 0,
            category: str = "official") -> None:
        for name in names:
            for arm in arms:
                slug = arm.lower().replace("-", "_")
                rep = f"__repeat{repetition}" if repetition else ""
                run_id = (
                    f"{stage_id}__{name}__{slug}{rep}__{budget}s"
                )
                rows.append({
                    "round_id": 32,
                    "stage_id": stage_id,
                    "serial_order": len(rows) + 1,
                    "run_id": run_id,
                    "instance_id": name,
                    "arm": arm,
                    "nominal_budget_seconds": budget,
                    "actual_process_cap_seconds": budget,
                    "shutdown_margin_seconds": SHUTDOWN_MARGIN,
                    "emergency_watchdog_seconds":
                        budget + WATCHDOG_SEPARATION,
                    "repetition": repetition,
                    "category": category,
                    "frozen_before_official_results": "true",
                })

    add("stage1", existing, ("P-GRB", "C6-FROZEN"), 1800)
    add("stage2", multi, ("P-GRB", "C6-FROZEN"), 1800)
    add("stage3", stage3, ("P-GRB", "C6-FROZEN"), 3600)
    add("stage4", stage4, ("C5-REFERENCE", "C6-FROZEN"), 1800,
        category="limited_reference")
    add("stage5", stage5, ("S0-CPLEX",), 1800,
        category="contextual_anchor")
    add("repeatability", repeat, ("P-GRB", "C6-FROZEN"), 1800,
        repetition=1, category="repeatability")
    if len(rows) != 133:
        raise RuntimeError(f"expected 133 frozen official rows, got {len(rows)}")
    write_csv(OUT / "round32_official_matrix.csv", rows)

    stage0: list[dict[str, Any]] = []

    def add0(suite: str, name: str, arm: str, budget: int,
             baseline_run_id: str = "") -> None:
        stage0.append({
            "round_id": 32,
            "stage_id": "stage0",
            "suite": suite,
            "serial_order": len(stage0) + 1,
            "run_id": (
                f"stage0__{suite}__{name}__"
                f"{arm.lower().replace('-', '_')}__{budget}s"
            ),
            "instance_id": name,
            "arm": arm,
            "nominal_budget_seconds": budget,
            "actual_process_cap_seconds": budget,
            "shutdown_margin_seconds": SHUTDOWN_MARGIN,
            "emergency_watchdog_seconds":
                budget + WATCHDOG_SEPARATION,
            "baseline_round31_run_id": baseline_run_id,
            "frozen_before_stage0_results": "true",
        })

    for arm in ("P-GRB", "C6-FROZEN"):
        add0("exactness_sentinel", "toy", arm, 60)
        add0("exactness_sentinel", "moderate_seed4301", arm, 300)
        add0("exactness_sentinel", new_v20_high_m2, arm, 300)
        add0("exactness_sentinel", new_v50_tight_m4, arm, 300)
        add0("v12_trace_qualification", "V12_M2", arm, 300,
             "stage2__V12_M2__c6_candidate__300s"
             if arm == "C6-FROZEN" else "")
    add0("frozen_equivalence", "V12_M1", "C6-FROZEN", 300,
         "stage2__V12_M1__c6_candidate__300s")
    add0("frozen_equivalence", "moderate_seed4301", "C6-FROZEN", 120,
         "sentinel__moderate_seed4301__c6_candidate__120s")
    if len(stage0) != 12:
        raise RuntimeError(f"expected 12 Stage 0 rows, got {len(stage0)}")
    write_csv(OUT / "round32_stage0_matrix.csv", stage0)

    subset_rows = []
    for label, names in (
        ("stage4_c5_reference", stage4),
        ("stage5_s0_anchor", stage5),
        ("repeatability", repeat),
    ):
        for index, name in enumerate(names, start=1):
            subset_rows.append({
                "subset": label,
                "subset_order": index,
                "instance_id": name,
                "family": items[name]["family"],
                "V": items[name]["V"],
                "M": items[name]["M"],
                "origin": items[name]["origin"],
                "frozen_before_official_results": "true",
            })
    write_csv(OUT / "round32_limited_subset_freeze.csv", subset_rows)


def preservation_manifest() -> None:
    raw = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=ROOT)
    entries = raw.decode("utf-8", errors="surrogateescape").split("\0")
    rows: list[dict[str, Any]] = []
    intended_before_capture = {
        "src/PaperExternalGiniTree.cpp",
        "scripts/generate_hard_exact_stress_instances.py",
        "scripts/generate_round32_multi_m.py",
        "scripts/prepare_round32.py",
    }
    intended_prefixes = (
        "reference/qualification_round32/",
        "results/gf_c6_long_run_validation_round32/",
    )
    for entry in entries:
        if not entry:
            continue
        status, path_text = entry[:2], entry[3:]
        normalized = path_text.replace("\\", "/")
        if (
            normalized in intended_before_capture
            or normalized.startswith(intended_prefixes)
            or (
                normalized.startswith(("scripts/", "tests/"))
                and "round32" in Path(normalized).name.lower()
            )
        ):
            continue
        path = ROOT / path_text
        volatile_cache = path.is_file() and path.suffix.lower() == ".pyc"
        rows.append({
            "status": status,
            "path": normalized,
            "kind": (
                "volatile_python_cache" if volatile_cache
                else "file" if path.is_file() else "directory"),
            "bytes": path.stat().st_size if path.is_file() else "",
            "sha256": (
                "" if volatile_cache
                else sha256(path) if path.is_file() else ""),
            "captured_as_preexisting": "true",
        })
    if len(rows) != 509:
        raise RuntimeError(
            f"pre-existing worktree reconstruction expected 509 entries, "
            f"got {len(rows)}")
    write_csv(OUT / "preexisting_worktree_manifest.csv", rows)


def write_protocol() -> None:
    protocol = """# Round 32 frozen protocol

Round 32 validates the mathematically frozen Round 31 C6 algorithm. It does
not develop C7 and does not change leaf selection, native targets, requeue,
lazy child lookahead, split decisions, exact closure, interval geometry,
strengthening rows, rho, HGA, or exactness semantics.

## Frozen arms

- `P-GRB`: compact original MILP, Gurobi 13.0.2, one thread, Seed 0,
  automatic presolve, zero relative and absolute MIP gaps, no HGA.
- `C6-FROZEN`: selector `round31-nonblocking-native-bound`, lifecycle
  `round31-open-native-bounded`, one-thread Gurobi, four initial intervals,
  parent-native-first scheduling, one launch-frozen strictly higher
  next-leaf target with ties ignored, valid partial-bound requeue, lazy child
  LPs, current normalized child-gain rho 0.01, no mandatory target split,
  exact closure after no unused milestone, depth 8, width 1e-4, unchanged
  six global and nine interval-local row families, unchanged HGA.
- `C5-REFERENCE`: frozen Round 30 C5, limited diagnostic only.
- `S0-CPLEX`: unchanged accepted CPLEX S0/F0 mainline, contextual only.

## Timing and runner

Every official row is serial and independent. The nominal and process caps
are 1,800 or 3,600 seconds. The fixed shutdown margin is 15 seconds. The
runner watchdog is separated from the process cap by 90 seconds. Completion
is an atomic checksum-bearing marker written only after process exit, result
JSON parse and flush verification, required trace checks, and artifact
inventory. Resume skips only checksum-valid complete rows. Incomplete or
invalid rows are preserved under `invalidated_rows/` with an explicit
invalidation record before a fresh uniform rerun. This is experiment-row
resume, never native solve-state resume.

## Frozen matrices

Stage 1 is 23 retained authoritative instances by P-GRB and C6 at 1,800s
(46 rows). Stage 2 is 12 deterministic V20/V50, M2/M4, Q30 qualification
instances by both arms at 1,800s (24 rows). Stage 3 is the predeclared 12
V50 instances by both arms in independent 3,600s runs (24 rows). Stage 4 is
eight predeclared instances by C5 and C6 at 1,800s (16 rows). Stage 5 is
seven predeclared S0 anchors at 1,800s. Repeatability independently repeats
both primary arms on eight predeclared instances at 1,800s (16 rows).

All primary comparisons require the same instance, nominal budget, solver
version, executable, machine, and independently verified common UB. Metrics
are strict certification/time/work, valid LB, verified UB, common-UB gap,
observed proof AUC without interpolation or endpoint extension, time and work
to fixed common-gap thresholds, final-gap and AUC wins/losses/ties at stated
tolerance, and family/V/M/VxM summaries. Time-limited valid rows are retained.

Historical Round 31 rows are derived context only and never official Round 32
rows. No instance, comparison rule, or algorithm setting may change after
official execution begins. A general bug requires retaining and invalidating
all affected rows, rebuilding and rehashing, and uniform rerun.
"""
    write_text(OUT / "round32_protocol.md", protocol)


def write_audits() -> None:
    root_cause = """# V12_M2 trace root cause

Round 31 row 409 (CSV data row 409; analyzer position 411 including its
internal endpoints) reported a terminal native callback bound
`0.745321425521423` for the sole still-active leaf while the independently
verified incumbent was `0.71850407075497091`. The next native infeasible
closure correctly set the global optimum bound to the incumbent, so the CSV
aggregate fell and the trace analyzer rejected it.

The scheduler bound was not regressing and C6 did not make a different
decision. The defect was telemetry aggregation during the narrow interval
between a callback proving that the active leaf cannot beat the incumbent
and the scheduler recording its closure. The trace used only the active and
other-open-leaf minima; it omitted the already closed branch that contains
the verified feasible incumbent. For a minimization problem that incumbent
remains a candidate global optimum, so the exported global bound cannot
exceed it.

The general repair retains the native leaf-bound event and all event order.
Only `valid_global_lower_bound` is computed as the minimum of the active/open
aggregate and the verified incumbent. No row is deleted, no timestamp is
changed, and no scheduler, target, requeue, child, split, closure, or solver
decision reads this trace value. Frozen-decision equivalence and an actual
V12_M2 rerun qualify the repair before official conclusions.
"""
    write_text(OUT / "v12_m2_trace_root_cause.md", root_cause)
    engineering = """# Round 32 engineering-fix audit

The source audit found one general trace-only issue: a native callback leaf
bound may exceed the verified incumbent immediately before leaf closure.
`writeGlobalTrace` now includes the verified incumbent in the minimization
aggregate. The active leaf value remains visible, preserving audit evidence.

The runner is hardened separately with atomic writes and completion markers,
post-exit JSON parsing, fixed shutdown and watchdog separation, required
trace checks, checksum-validated resume, preserved invalidated/partial rows,
and explicit invalidation records. These mechanisms do not enter the solver
command's mathematical decisions.

The multi-M generator generalizes only its `M` and `Q` function parameters;
the legacy M3/Q30 defaults and byte output are unchanged. No C6 predicate,
row family, geometry, target, requeue, split, exact-closure, HGA, or solver
strategy setting is changed.
"""
    write_text(OUT / "engineering_fix_audit.md", engineering)
    separation = """# Round 32 result-separation audit

All new raw runs are rooted under
`results/gf_c6_long_run_validation_round32/`. Round 22-31 evidence is
read-only. Historical Round 31 context is emitted only to
`historical_round31_reference.csv`; it is never inserted into an official
Round 32 stage CSV. The matrix gives every row `round_id=32`, a stage and run
ID, nominal and actual cap, arm, and frozen instance identity.
"""
    write_text(OUT / "result_separation_audit.md", separation)


def write_source_of_truth() -> None:
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=ROOT, text=True).strip()
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    text = f"""# Round 32 source of truth

- Authoritative workspace: `{ROOT}`
- Round 32 branch: `{branch}`
- Round 32 starting HEAD: `{STARTING_HEAD}`
- Observed live `main` before Round 32: `{OBSERVED_LIVE_MAIN}`
- Pre-freeze working HEAD: `{head}`
- Frozen C6 source commit: recorded after the intended pre-run commit in
  `round32_frozen_manifest.json`
- Isolated build root: `build_round32/`
- Isolated evidence root: `results/gf_c6_long_run_validation_round32/`
- Pre-existing status entries preserved: 509 (3 tracked dirty, 506 untracked)
- Stable CPLEX paper mainline: S0/F0-CPLEX
- Same-solver benchmark: P-GRB
- Validated candidate under test: C6-FROZEN

The Gurobi license is inherited only by licensed child processes. Its path
and contents are never read, copied, hashed, printed, or serialized by Round
32 scripts or evidence.
"""
    write_text(OUT / "source_of_truth.md", text)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=ROOT, text=True).strip()
    if branch != BRANCH:
        raise RuntimeError(f"unexpected Round 32 branch: {branch}")
    preservation_manifest()
    existing = existing_manifest()
    multi = multi_manifest()
    items = inventory(existing, multi)
    matrix_and_subsets(items)
    write_protocol()
    write_audits()
    write_source_of_truth()
    summary = {
        "schema": "round32-preparation-v1",
        "starting_head": STARTING_HEAD,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "branch": branch,
        "existing_instance_count": len(existing),
        "multi_m_instance_count": len(multi),
        "stage3_instance_count": len(csv_rows(
            OUT / "round32_stage3_freeze.csv")),
        "official_row_count": len(csv_rows(
            OUT / "round32_official_matrix.csv")),
        "stage0_row_count": len(csv_rows(
            OUT / "round32_stage0_matrix.csv")),
        "protocol_sha256": sha256(OUT / "round32_protocol.md"),
        "prepared_before_solver_results": True,
    }
    write_json(OUT / "round32_preparation_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
