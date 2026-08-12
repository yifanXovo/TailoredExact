#!/usr/bin/env python3
"""Post-implementation old/new default-off C6 equivalence for Round 37."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

import round35_common as r35
import run_round25_experiments as licensed
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_gini_geometry_mechanism_round37"
RUNS = OUT / "baseline_equivalence_post_implementation_runs"
OLD_EXE = (ROOT / "build_round36_stage_c_contract_fix" / "official" /
           "gurobi" / "ExactEBRP.exe")
NEW_EXE = ROOT / "build_round37" / "official" / "gurobi" / "ExactEBRP.exe"
PROCESS_CAP = 180
CASES = (
    "V12_M1",
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value[0] if isinstance(value, list) else value


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def command(exe: Path, item: dict[str, Any], run_dir: Path) -> list[str]:
    args = [str(exe), "--input", str(ROOT / item["path"])]
    args.extend(r31.tailored_options(run_dir, PROCESS_CAP))
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", PROCESS_CAP),
        ("--process-wall-time-limit", PROCESS_CAP),
        ("--process-shutdown-margin", 15),
        ("--primal-heuristic", "hga-tgbc"),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", 2000),
    ):
        r35.replace(args, name, value)
    for name, value in (
        ("--round34-c6-startup-variant", "hga-full"),
        ("--heuristic-candidates-csv", run_dir / "heuristic_candidates.csv"),
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "round31-nonblocking-native-bound"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "round31-open-native-bounded"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--round24-executable-sha256", sha256(exe)),
        ("--round24-manifest-executable-sha256", sha256(exe)),
        ("--round24-expected-gurobi-model-fingerprint",
         r35.fingerprint_values()[item["instance_id"]]),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        r35.add(args, name, value)
    return [str(value) for value in args]


def run_one(label: str, exe: Path, item: dict[str, Any]) -> Path:
    run_dir = RUNS / f"{item['instance_id']}__{label}"
    result_path = run_dir / "result.json"
    if result_path.is_file():
        return run_dir
    run_dir.mkdir(parents=True, exist_ok=False)
    args = command(exe, item, run_dir)
    write_json(run_dir / "command.json", {
        "schema": "round37-c6-equivalence-command-v1",
        "label": label,
        "instance_id": item["instance_id"],
        "instance_sha256": sha256(ROOT / item["path"]),
        "executable_sha256": sha256(exe),
        "process_cap_seconds": PROCESS_CAP,
        "command": args,
        "license_environment": "child_only_not_serialized",
    })
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        completed = subprocess.run(
            args, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
            timeout=PROCESS_CAP + 60, check=False,
        )
    if completed.returncode != 0 or not result_path.is_file():
        raise RuntimeError(
            f"equivalence run failed: {run_dir.name} rc={completed.returncode}"
        )
    return run_dir


def selected(rows: list[dict[str, str]], fields: tuple[str, ...]) \
        -> list[dict[str, str]]:
    return [{field: row.get(field, "") for field in fields} for row in rows]


def signature(run_dir: Path) -> dict[str, Any]:
    result = load_json(run_dir / "result.json")
    external = run_dir / "external"
    initial = csv_rows(external / "initial_decomposition_ledger.csv")
    lp = csv_rows(external / "lp_status_ledger.csv")
    parents = csv_rows(external / "parent_child_bound_ledger.csv")
    global_trace = csv_rows(external / "global_bound_trace.csv")
    targets = csv_rows(external / "native_target_ledger.csv")
    splits = csv_rows(external / "split_decision_ledger.csv")
    events = csv_rows(external / "paper_tree_events.csv")
    closures = [row for row in events if row.get("event") in {
        "terminal_mip_complete", "lp_bound_prune", "atomic_split",
        "lp_complete", "parent_lp_requeue",
    }]
    return {
        "startup": {key: result.get(key) for key in (
            "hga_verified_objective", "round36_hga_start_attempted",
            "round36_hga_start_verified", "round36_hga_start_objective",
            "round36_proof_incumbent_launch",
        )},
        "proof_range_and_four_intervals": {
            "root_lower": result.get("external_gini_tree_root_gamma_L"),
            "root_upper": result.get("external_gini_tree_root_gamma_U"),
            "proof_upper": result.get(
                "external_gini_tree_proof_relevant_gamma_upper"),
            "initial_leaf_count": result.get(
                "external_gini_tree_initial_leaf_count"),
            "active_intervals": result.get(
                "external_gini_tree_active_initial_intervals"),
            "rows": selected(initial, (
                "anchor_cell_index", "anchor_lower", "anchor_upper", "active",
                "active_lower", "active_upper", "truncated_by_proof_range",
                "proof_range_lower", "proof_range_upper",
                "normalization_source",
            )),
        },
        "parent_lp_bounds": selected(parents, (
            "parent_id", "parent_lp_bound", "left_id", "left_lp_bound",
            "left_infeasible", "right_id", "right_lp_bound",
            "right_infeasible", "post_split_bound", "decision",
        )),
        "lp_and_child_lookahead": selected(lp, (
            "leaf_id", "parent_id", "depth", "gamma_L", "gamma_U",
            "terminal_valid", "optimal", "infeasible", "bound_available",
            "lower_bound", "native_status",
        )),
        "controlling_leaf_sequence": selected(global_trace, (
            "event_type", "active_leaf", "active_leaf_valid_lower_bound",
            "other_open_leaf_min_valid_lower_bound", "valid_global_lower_bound",
            "verified_global_upper_bound", "open_relevant_leaf_count",
            "closed_relevant_leaf_count", "event_source",
        )),
        "targets_and_requeues": selected(targets, (
            "phase_index", "leaf_id", "target_kind", "current_bound",
            "target_bound", "other_open_min_bound", "verified_cutoff", "status",
            "native_status", "native_bound", "target_reached", "exact_closure",
            "requeued", "event_source",
        )),
        "split_decisions": selected(splits, (
            "parent_id", "eligible", "decision_valid", "split",
            "child_infeasibility_trigger", "strict_bound_trigger",
            "normalized_disjunction_gain", "parent_native_bound_target",
            "target_phase_required", "reason", "b_plus", "eta_proof",
            "eta_anchor", "normalization_source", "normalization_upper_bound",
        )),
        "closures": selected(closures, (
            "event", "leaf_id", "gamma_L", "gamma_U", "status", "global_lb",
            "verified_ub", "detail",
        )),
        "final_objective_and_certificate": {key: result.get(key) for key in (
            "status", "objective", "external_gini_tree_global_lower_bound",
            "external_gini_tree_verified_upper_bound",
            "strict_certified_original_problem", "strict_certificate_class",
            "strict_certificate_rejection_reason",
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_split_count",
            "external_gini_tree_terminal_mip_optimize_count",
        )},
    }


def numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def compare(left: Any, right: Any, path: str = "") \
        -> tuple[list[str], float, float, int]:
    problems: list[str] = []
    max_abs = 0.0
    max_rel = 0.0
    numeric_pairs = 0
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            return ([f"{path}:key_mismatch"], 0.0, 0.0, 0)
        for key in left:
            child = compare(left[key], right[key], f"{path}.{key}")
            problems.extend(child[0])
            max_abs = max(max_abs, child[1])
            max_rel = max(max_rel, child[2])
            numeric_pairs += child[3]
        return problems, max_abs, max_rel, numeric_pairs
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return ([f"{path}:length:{len(left)}!={len(right)}"], 0.0, 0.0, 0)
        for index, (a, b) in enumerate(zip(left, right)):
            child = compare(a, b, f"{path}[{index}]")
            problems.extend(child[0])
            max_abs = max(max_abs, child[1])
            max_rel = max(max_rel, child[2])
            numeric_pairs += child[3]
        return problems, max_abs, max_rel, numeric_pairs
    a, b = numeric(left), numeric(right)
    if a is not None and b is not None:
        absolute = abs(a - b)
        relative = absolute / max(1.0, abs(a), abs(b))
        if relative > 5e-6:
            problems.append(f"{path}:numeric:{a}!={b}:rel={relative}")
        return problems, absolute, relative, 1
    if left != right:
        problems.append(f"{path}:categorical:{left!r}!={right!r}")
    return problems, 0.0, 0.0, 0


def main() -> int:
    if not OLD_EXE.is_file() or not NEW_EXE.is_file():
        raise SystemExit("old and new Gurobi executables are required")
    inventory = r35.inventory()
    RUNS.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict[str, Any]] = []
    run_records: dict[str, Any] = {}
    for instance_id in CASES:
        item = inventory[instance_id]
        old_dir = run_one("round36_frozen", OLD_EXE, item)
        new_dir = run_one("round37_candidate_default_off", NEW_EXE, item)
        old_signature, new_signature = signature(old_dir), signature(new_dir)
        run_records[instance_id] = {
            "old_executable_sha256": sha256(OLD_EXE),
            "new_executable_sha256": sha256(NEW_EXE),
            "old_result_sha256": sha256(old_dir / "result.json"),
            "new_result_sha256": sha256(new_dir / "result.json"),
        }
        for component in old_signature:
            problems, max_abs, max_rel, numeric_pairs = compare(
                old_signature[component], new_signature[component], component
            )
            audit_rows.append({
                "instance_id": instance_id,
                "component": component,
                "identical_within_logged_precision": not problems,
                "numeric_pairs": numeric_pairs,
                "max_absolute_delta": max_abs,
                "max_relative_delta": max_rel,
                "problem_count": len(problems),
                "problems": ";".join(problems[:20]),
            })
    passed = all(row["identical_within_logged_precision"] for row in audit_rows)
    with (OUT / "baseline_equivalence_post_implementation_audit.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)
    summary = {
        "schema": "round37-c6-baseline-equivalence-v1",
        "passed": passed,
        "process_cap_seconds": PROCESS_CAP,
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
    write_json(
        OUT / "baseline_equivalence_post_implementation_audit.json", summary
    )
    lines = [
        "# Round 37 contemporaneous C6 equivalence",
        "",
        f"Gate passed: **{passed}** ({len(audit_rows)} component comparisons).",
        "",
        "The frozen Round 36 Stage C executable and the clean Round 37",
        "executable were run contemporaneously in default C6-HGA-FULL mode.",
        "The V12 case exercises targets, requeue, lookahead, and closure; the",
        "short V20/M2 case additionally exercises actual splits. Clocks and",
        "solver-effort counters are excluded. Numeric ledger comparisons allow",
        "only the precision already lost by the old six-digit CSV writer.",
        "",
        "| Instance | Component | Equivalent | Max relative delta |",
        "|---|---|---:|---:|",
    ]
    lines.extend(
        f"| {row['instance_id']} | {row['component']} | "
        f"{row['identical_within_logged_precision']} | "
        f"{row['max_relative_delta']:.3g} |"
        for row in audit_rows
    )
    (OUT / "baseline_equivalence_post_implementation_audit.md").write_text(
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
