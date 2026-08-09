#!/usr/bin/env python3
"""Freeze Round 34 variants, commands, matrices, source, and executable."""

from __future__ import annotations

import json
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

import round34_common as common


STARTING_HEAD = "201798c6c9daa9b1f6bfae583af5bbdc53608219"
OBSERVED_LIVE_MAIN = "afb3f1043fab73ae28dd5b1a2d71501f6f732b3c"


def matrix_row(stage: str, item: dict[str, Any], arm: str,
               cap: int, repetition: str = "primary") -> dict[str, Any]:
    token = arm.lower().replace("-", "_")
    repeat = "" if repetition == "primary" else f"__{repetition}"
    return {
        "round_id": 34,
        "stage": stage,
        "run_id": f"{stage}__{item['instance_id']}__{token}{repeat}__{cap}s",
        "instance_id": item["instance_id"],
        "instance_sha256": item["sha256"],
        "V": item["V"],
        "M": item["M"],
        "Q": item["Q"],
        "scenario": item["scenario"],
        "arm": arm,
        "startup_variant": (
            "not_applicable" if arm == "P-GRB"
            else common.startup_definition(arm)["startup_variant"]),
        "process_cap_seconds": cap,
        "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
        "watchdog_seconds": cap + 90,
        "repetition": repetition,
        "serial_order": 0,
        "frozen_before_official_results": True,
    }


def selected(path: Path, items: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [items[row["instance_id"]] for row in common.csv_rows(path)]


def main() -> int:
    if common.RUNS.exists():
        raise RuntimeError("official results exist before Round 34 freeze")
    build = common.load_json(common.OUT / "stage0_build_and_tests.json")
    preflight = common.load_json(common.OUT / "round34_preflight_summary.json")
    development = common.load_json(
        common.OUT / "round34_development_summary.json")
    if not build.get("passed") or not preflight.get("passed"):
        raise RuntimeError("build or fingerprint/certificate gate failed")
    if not development.get("all_verifier_passed"):
        raise RuntimeError("development verifier gate failed")
    if development["light_matches_full_fitness"] != 7:
        raise RuntimeError("predeclared LIGHT did not replicate FULL in development")
    simple_valid = development["simple_verifier_passed"] == 7
    if not simple_valid:
        raise RuntimeError("SIMPLE did not pass the predeclared viability gate")
    items = common.inventory()
    v10 = sorted(
        (item for item in items.values() if item["V"] == 10),
        key=lambda item: (item["M"], item["Q"], item["scenario"],
                          item["instance_id"]))
    if len(v10) != 18:
        raise RuntimeError("official V10 inventory must contain 18 identities")

    arms = list(common.STARTUP_ARMS)
    rows: list[dict[str, Any]] = []
    for item in selected(common.CASE_MANIFEST, items):
        for arm in ("P-GRB", "C6-HGA-FULL"):
            rows.append(matrix_row("case", item, arm, 7200))
    for item in v10:
        for arm in arms:
            rows.append(matrix_row("v10", item, arm, 3600))
    for item in selected(common.TRANSFER_MANIFEST, items):
        for arm in arms:
            rows.append(matrix_row("transfer", item, arm, 3600))
    # Repeat arms are frozen before official results.  LIGHT is the sole
    # predeclared primary exploratory HGA arm; SIMPLE remains fully represented
    # in the primary V10/transfer matrices without post-selection.
    for item in selected(common.REPEAT_MANIFEST, items):
        for arm in ("C6-HGA-FULL", "C6-HGA-LIGHT"):
            rows.append(matrix_row("repeat", item, arm, 3600, "repeat1"))
    for order, row in enumerate(rows, start=1):
        row["serial_order"] = order
    common.write_csv(common.OFFICIAL_MATRIX, rows)

    development_rows = common.csv_rows(
        common.OUT / "hga_development_results.csv")
    medians = {
        arm: statistics.median(float(row["reported_runtime_seconds"])
                               for row in development_rows
                               if row["arm"] == arm)
        for arm in common.STARTUP_ARMS
    }
    freeze = {
        "schema": "round34-hga-variant-freeze-v1",
        "round_id": 34,
        "frozen_before_official_results": True,
        "official_results_started_when_written": False,
        "historical_candidate_set": [250, 500, 1000],
        "historical_full_fitness_matches": {
            "250": 15, "500": 17, "1000": 18,
        },
        "development_instance_count": 7,
        "development_all_verifier_passed": True,
        "development_light_matches_full_fitness": 7,
        "development_light_matches_full_verified_objective": 7,
        "development_simple_verifier_passed": 7,
        "development_median_reported_runtime_seconds": medians,
        "variants": {
            "C6-HGA-FULL": {
                "status": "validated_mainline_unchanged",
                "startup_variant": "hga-full",
                "primal_heuristic": "hga-tgbc",
                "seed": 20260626,
                "stop": "generation-stagnation",
                "no_improve_generations": 2000,
                "all_other_hga_settings": "unchanged",
            },
            "C6-HGA-LIGHT": {
                "status": "exploratory_uniform_arm",
                "startup_variant": "hga-light-1000",
                "primal_heuristic": "hga-tgbc",
                "seed": 20260626,
                "stop": "generation-stagnation",
                "no_improve_generations": 1000,
                "all_other_hga_settings": "identical_to_full",
            },
            "C6-SIMPLE-START": {
                "status": "exploratory_uniform_arm",
                "startup_variant": "simple-start",
                "primal_heuristic": "greedy",
                "constructor": "existing_three_mode_deterministic_greedy",
                "independent_verifier_required": True,
            },
        },
        "exact_phase_identity": (
            "all arms use unchanged C6 after verified incumbent availability"),
        "automatic_promotion_allowed": False,
    }
    common.write_json(common.VARIANT_FREEZE, freeze)

    commands: dict[str, Any] = {}
    for row in rows:
        item = items[row["instance_id"]]
        directory = common.RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "serial_order": int(row["serial_order"]),
            "stage": row["stage"],
            "instance_id": row["instance_id"],
            "instance_sha256": row["instance_sha256"],
            "arm": row["arm"],
            "startup_variant": row["startup_variant"],
            "process_cap_seconds": int(row["process_cap_seconds"]),
            "command": common.command_for(row, item, directory),
        }
    command_path = common.OUT / "round34_command_freeze.json"
    common.write_json(command_path, {
        "schema": "round34-command-freeze-v1",
        "round_id": 34,
        "frozen_before_official_results": True,
        "row_count": len(commands),
        "commands": commands,
    })

    source_files = (
        "CMakeLists.txt",
        "include/Instance.hpp",
        "include/Result.hpp",
        "include/hga_tgbc/HybridGA.h",
        "src/CplexBaseline.cpp",
        "src/GurobiBaseline.cpp",
        "src/HgaTgbcRunner.cpp",
        "src/IntervalRowFactory.cpp",
        "src/PaperExternalGiniTree.cpp",
        "src/ControllingLeafScheduler.cpp",
        "src/Result.cpp",
        "src/main.cpp",
        "scripts/round34_common.py",
        "scripts/run_round34_experiments.py",
    )
    for path_text in source_files:
        if not (common.ROOT / path_text).is_file():
            raise RuntimeError(f"freeze source missing: {path_text}")
    artifacts = {
        "protocol": common.OUT / "round34_protocol.md",
        "instance_manifest": common.INSTANCE_MANIFEST,
        "case_manifest": common.CASE_MANIFEST,
        "development_manifest": common.DEVELOPMENT_MANIFEST,
        "transfer_manifest": common.TRANSFER_MANIFEST,
        "repeat_manifest": common.REPEAT_MANIFEST,
        "fingerprints": common.FINGERPRINTS,
        "certificate_preflight":
            common.OUT / "round34_certificate_preflight.csv",
        "development_results":
            common.OUT / "hga_development_results.csv",
        "variant_freeze": common.VARIANT_FREEZE,
        "official_matrix": common.OFFICIAL_MATRIX,
        "command_freeze": command_path,
        "frozen_c6_equivalence":
            common.OUT / "frozen_c6_equivalence.csv",
    }
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT, text=True).strip()
    manifest: dict[str, Any] = {
        "schema": "round34-frozen-manifest-v1",
        "round_id": 34,
        "branch": subprocess.check_output(
            ("git", "branch", "--show-current"), cwd=common.ROOT,
            text=True).strip(),
        "starting_head": STARTING_HEAD,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "solver_source_commit": build["source_commit"],
        "validation_commit_at_freeze": head,
        "gurobi_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "gurobi_version": "13.0.2",
        "source_file_sha256": {
            path_text: common.sha256(common.ROOT / path_text)
            for path_text in source_files
        },
        "frozen_before_official_results": True,
        "official_results_started_when_written": False,
        "official_row_count": len(rows),
        "case_rows": sum(row["stage"] == "case" for row in rows),
        "v10_rows": sum(row["stage"] == "v10" for row in rows),
        "transfer_rows": sum(row["stage"] == "transfer" for row in rows),
        "repeat_rows": sum(row["stage"] == "repeat" for row in rows),
        "primary_timing_field": "final_process_wall_time_seconds",
        "one_thread": True,
        "initial_intervals": 4,
        "maximum_adaptive_depth": 8,
        "minimum_adaptive_width": 1e-4,
        "normalized_split_threshold_rho": 0.01,
        "certificate_tolerance": 1e-7,
        "c6_algorithm_selector": "round31-nonblocking-native-bound",
        "c6_lifecycle": "round31-open-native-bounded",
        "mainline_remains": "C6-HGA-FULL",
        "automatic_promotion_allowed": False,
        "written_at_unix_seconds": time.time(),
    }
    for key, path in artifacts.items():
        manifest[f"{key}_path"] = common.relative(path)
        manifest[f"{key}_sha256"] = common.sha256(path)
    if manifest["gurobi_executable_sha256"] != build[
            "gurobi_executable_sha256"]:
        raise RuntimeError("executable changed after clean build")
    common.write_json(common.FROZEN_MANIFEST, manifest)

    design = (common.OUT / "hga_variant_design_decision.md").read_text(
        encoding="utf-8")
    design += f"""

## Development gate results and official inclusion

All 21 heuristic-only development rows passed the independent verifier.
HGA-LIGHT matched FULL final fitness and verified objective on 7/7 identities.
SIMPLE produced a verified original solution on 7/7 identities. Median reported
startup runtimes were {medians['C6-HGA-FULL']:.6f}s (FULL),
{medians['C6-HGA-LIGHT']:.6f}s (LIGHT), and
{medians['C6-SIMPLE-START']:.6f}s (SIMPLE).

Accordingly all three uniform arms are frozen for the official 18-instance V10
and four-anchor transfer matrices. Repeatability was predeclared for FULL and
the sole primary exploratory HGA arm, LIGHT. This is an inclusion decision for
measurement, not a promotion: C6-HGA-FULL remains the validated mainline.
"""
    common.write_text(common.OUT / "hga_variant_design_decision.md", design)
    # The design appendix is intentionally not a frozen runner input; the
    # executable/commands/variants/manifests were already bound above.
    print(json.dumps({
        "official_rows": len(rows),
        "case_rows": manifest["case_rows"],
        "v10_rows": manifest["v10_rows"],
        "transfer_rows": manifest["transfer_rows"],
        "repeat_rows": manifest["repeat_rows"],
        "simple_included": simple_valid,
        "executable_sha256": manifest["gurobi_executable_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
