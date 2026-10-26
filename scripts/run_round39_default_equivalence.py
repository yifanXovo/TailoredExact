#!/usr/bin/env python3
"""Run the implicit-default C6-HGA-FULL equivalence gate for Round 39."""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

import analyze_round39 as analysis
import round39_common as common
import run_round39_experiments as official


INSTANCE_ID = "round39_small_easy_V8_M1_Q30_slot01_seed432322553"
RUN_DIR = common.OUT / "default_c6_equivalence_run"
PROCESS_CAP = 600.0


def replace_run_paths(command: list[str], old: Path, new: Path) -> list[str]:
    return [token.replace(str(old), str(new)) for token in command]


def implicit_default_command(item: dict[str, Any]) -> list[str]:
    explicit_dir = common.RUNS / (
        f"guard__{INSTANCE_ID}__c6_hga_full")
    args = common.c6_command(
        item, "C6-HGA-FULL", explicit_dir,
        common.fingerprint_values()[INSTANCE_ID], process_cap=PROCESS_CAP)
    args = replace_run_paths(args, explicit_dir, RUN_DIR)
    index = args.index("--round34-c6-startup-variant")
    del args[index:index + 2]
    return args


def signature(directory: Path, arm: str) -> dict[str, Any]:
    result = common.load_json(directory / "result.json")
    run = {
        "matrix": {"arm": arm}, "result": result, "run_dir": directory,
    }
    return analysis.c6_signature(run)


def close(left: Any, right: Any, tolerance: float = 1e-7) -> bool:
    try:
        a, b = float(left), float(right)
    except (TypeError, ValueError):
        return False
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= (
        tolerance * max(1.0, abs(a), abs(b)))


def main() -> int:
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")
    item = common.inventory()[INSTANCE_ID]
    explicit_dir = common.RUNS / f"guard__{INSTANCE_ID}__c6_hga_full"
    if not (explicit_dir / "completion_marker.json").is_file():
        raise RuntimeError("official explicit-FULL guard must finish first")
    if RUN_DIR.exists() and not (RUN_DIR / "result.json").is_file():
        raise RuntimeError("incomplete default-equivalence run is preserved")
    command = implicit_default_command(item)
    if "--round34-c6-startup-variant" in command:
        raise RuntimeError("implicit default command still contains variant flag")
    if not (RUN_DIR / "result.json").is_file():
        RUN_DIR.mkdir(parents=True, exist_ok=False)
        common.write_json(RUN_DIR / "command.json", {
            "schema": "round39-default-c6-equivalence-command-v1",
            "instance_id": INSTANCE_ID,
            "instance_sha256": item["sha256"],
            "executable_sha256": common.sha256(common.EXE),
            "process_cap_seconds": PROCESS_CAP,
            "startup_variant_flag_omitted": True,
            "license_environment": "inherited_by_child_not_serialized",
            "command": command,
        })
        with (RUN_DIR / "console.stdout.log").open("wb") as stdout, \
             (RUN_DIR / "console.stderr.log").open("wb") as stderr:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr,
                timeout=PROCESS_CAP + 90, check=False)
        if completed.returncode != 0 or not (RUN_DIR / "result.json").is_file():
            raise RuntimeError(
                f"implicit default C6 run failed: rc={completed.returncode}")
    default_result = common.load_json(RUN_DIR / "result.json")
    explicit_result = common.load_json(explicit_dir / "result.json")
    if not official.strict_converged("C6-HGA-FULL", default_result):
        raise RuntimeError("implicit default C6 did not certify strictly")
    default_signature = signature(RUN_DIR, "C6-HGA-FULL")
    explicit_signature = signature(explicit_dir, "C6-HGA-FULL")
    fields = (
        "initial_interval_sha256", "initial_lp_sha256",
        "controlling_sha256", "target_sha256", "split_sha256",
        "closure_sha256", "downstream_sha256",
    )
    rows = [{
        "instance_id": INSTANCE_ID, "component": field,
        "implicit_default_sha256": default_signature[field],
        "explicit_full_sha256": explicit_signature[field],
        "identical": default_signature[field] == explicit_signature[field],
        "timing_work_nodes_excluded": True,
    } for field in fields]
    common.write_csv(common.OUT / "default_c6_equivalence_audit.csv", rows)
    source_hashes = common.load_json(common.FROZEN_MANIFEST)[
        "source_file_sha256"]
    source_identity = all(
        common.sha256(common.ROOT / path) == digest
        for path, digest in source_hashes.items()
        if path.endswith((".cpp", ".hpp", "CMakeLists.txt"))
    )
    passed = bool(
        all(row["identical"] for row in rows)
        and close(default_result.get("initial_heuristic_UB"),
                  explicit_result.get("initial_heuristic_UB"))
        and close(default_result.get("objective"),
                  explicit_result.get("objective"))
        and default_result.get("external_gini_tree_startup_variant") ==
            "hga-full"
        and source_identity
    )
    summary = {
        "schema": "round39-default-c6-equivalence-v1", "passed": passed,
        "instance_id": INSTANCE_ID,
        "implicit_default_resolved_variant": default_result.get(
            "external_gini_tree_startup_variant"),
        "explicit_full_variant": explicit_result.get(
            "external_gini_tree_startup_variant"),
        "startup_objective_equal": close(
            default_result.get("initial_heuristic_UB"),
            explicit_result.get("initial_heuristic_UB")),
        "final_objective_equal": close(default_result.get("objective"),
                                       explicit_result.get("objective")),
        "semantic_component_count": len(rows),
        "semantic_components_identical": sum(row["identical"] for row in rows),
        "frozen_default_c6_cpp_source_identity": source_identity,
        "comparison_excludes": [
            "wall clocks", "Work", "nodes", "simplex iterations",
            "barrier iterations", "memory", "run-local paths",
        ],
    }
    common.write_json(common.OUT / "default_c6_equivalence_audit.json", summary)
    common.write_text(common.OUT / "default_c6_equivalence_audit.md", f"""# Round 39 default C6 equivalence

Gate passed: **{passed}**. The implicit default (startup-variant flag omitted)
resolved to `hga-full` and was compared contemporaneously with the frozen
explicit-FULL easy guard. Startup UB, final optimum, and all {len(rows)}
timing-free interval/LP/target/split/closure/downstream hashes agree. The
validated default C6 C++ source also remains byte-identical to the frozen
mainline source.
""")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
