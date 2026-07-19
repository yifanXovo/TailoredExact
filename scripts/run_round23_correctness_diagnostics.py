#!/usr/bin/env python3
"""Run the preregistered short Round 23 moderate4301 diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND22 = ROOT / "results" / "gf_global_gini_tree_unified_validation_round"
OUT = ROOT / "results" / "gf_global_gini_tree_round23" / "diagnostics"
PATH_FLAGS = {
    "--progress-log": "legacy_progress.csv",
    "--log": "native.log",
    "--out": "result.json",
    "--global-gini-tree-node-trace": "global_node_trace.csv",
    "--global-gini-tree-bound-trace": "legacy_global_bound.csv",
    "--global-gini-tree-manifest": "model_lifecycle_manifest.csv",
    "--global-gini-tree-root-export": "global_root.lp",
    "--global-gini-tree-post-row-trace": "post_rows.csv",
    "--global-gini-tree-topology-trace": "gini_topology.csv",
    "--global-gini-tree-sibling-trace": "sibling_delay.csv",
    "--global-gini-tree-row-delta-trace": "row_delta.csv",
    "--global-gini-tree-memory-trace": "tree_memory.csv",
    "--global-gini-tree-mip-start-audit": "mip_start_audit.csv",
    "--dense-progress-raw": "raw_progress.csv",
    "--dense-progress-checkpoints": "canonical_checkpoints.csv",
}
CASES = {
    "s0_frozen_equivalent": ("s0", {}),
    "s1_frozen_equivalent": ("s1", {}),
    "s0_eager_rows": ("s0", {"--global-gini-tree-row-timing": "eager"}),
    "s0_presolve_off": ("s0", {"--global-gini-tree-presolve": "off"}),
    "s0_incremental_pack": (
        "s0",
        {"--global-gini-tree-row-attachment": "exact-incremental-delta"},
    ),
    "s0_complete_mip_start": ("s0", {"--global-gini-tree-native-mip-start": "true"}),
    "s0_corrected": ("s0", {"--global-gini-tree-presolve": "off"}),
    "s1_corrected": ("s1", {"--global-gini-tree-presolve": "off"}),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_flag(command: list[str], flag: str, value: str) -> None:
    try:
        index = command.index(flag)
    except ValueError:
        command.extend([flag, value])
    else:
        command[index + 1] = value


def prepare(
    case: str,
    executable_override: Path | None = None,
    output_tag: str = "",
) -> tuple[list[str], Path, dict]:
    arm, overrides = CASES[case]
    retained = ROUND22 / "commands" / f"stage4__moderate_seed4301__{arm}__900s__dense_on.json"
    source = json.loads(retained.read_text(encoding="utf-8"))
    command = list(source["command"])
    run_dir = OUT / (f"{output_tag}_{case}" if output_tag else case)
    run_dir.mkdir(parents=True, exist_ok=True)
    set_flag(command, "--time-limit", "102")
    set_flag(command, "--process-wall-time-limit", "120")
    set_flag(command, "--dense-progress-run-id", f"round23_diag__{case}")
    if executable_override is not None:
        command[0] = str(executable_override.resolve())
    for flag, filename in PATH_FLAGS.items():
        set_flag(command, flag, str((run_dir / filename).resolve()))
    for flag, value in overrides.items():
        set_flag(command, flag, value)
    executable = Path(command[0])
    metadata = {
        "schema": "round23-correctness-diagnostic-v1",
        "case": case,
        "source_retained_command": str(retained.resolve()),
        "source_retained_command_sha256": sha256(retained),
        "actual_frozen_round22_executable": executable_override is None,
        "executable": str(executable),
        "executable_sha256": sha256(executable),
        "nominal_process_wall_seconds": 120,
        "native_deadline_seconds": 102,
        "overrides": overrides,
        "command": command,
    }
    return command, run_dir, metadata


def run_case(
    case: str,
    executable_override: Path | None = None,
    output_tag: str = "",
) -> None:
    command, run_dir, metadata = prepare(
        case, executable_override, output_tag)
    metadata["started_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    start = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=150,
    )
    metadata["runner_wall_seconds"] = time.perf_counter() - start
    metadata["return_code"] = completed.returncode
    metadata["finished_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    (run_dir / "console.log").write_text(completed.stdout, encoding="utf-8")
    result_path = run_dir / "result.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        metadata["result_summary"] = {
            key: result.get(key)
            for key in (
                "status",
                "objective",
                "upper_bound",
                "lower_bound",
                "native_mip_status_code",
                "native_mip_status_text",
                "strict_certificate_class",
                "strict_certified_original_problem",
                "strict_native_model_scope",
                "strict_infeasibility_scope",
                "feasibility_consistency_gate_passed",
                "verified_incumbent_original_problem_feasible",
                "global_gini_tree_native_mip_start_attempted",
                "global_gini_tree_native_mip_start_mapping_complete",
                "global_gini_tree_native_mip_start_stored",
                "global_gini_tree_native_mip_start_accepted",
                "global_gini_tree_native_mip_start_failure_reason",
                "global_gini_tree_gini_children_created",
                "global_gini_tree_sibling_first_process_count",
                "global_gini_tree_callback_failures",
                "global_gini_tree_preprocessing_reduce_effective",
                "global_gini_tree_preprocessing_linear_effective",
                "global_gini_tree_continuous_branch_presolve_valid",
            )
        }
    (run_dir / "command.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata.get("result_summary", metadata), indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", nargs="+", choices=sorted(CASES))
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--output-tag", default="")
    args = parser.parse_args()
    for case in args.cases:
        run_case(case, args.executable, args.output_tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
