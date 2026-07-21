#!/usr/bin/env python3
"""Mechanical regression gates for the frozen Round 25 protocol."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_round25_experiments as runner  # noqa: E402
import summarize_round25_results as summary  # noqa: E402


def option(command: list[str], name: str) -> str:
    position = command.index(name)
    return command[position + 1]


def row(**changes: object) -> dict[str, object]:
    base: dict[str, object] = {
        "strict_certificate": False,
        "certificate_wall_seconds": "",
        "final_lb": 0.0,
        "common_ub_gap": 1.0,
        "bound_progress_auc": 0.0,
    }
    base.update(changes)
    return base


def main() -> None:
    assert len(runner.ARMS) == 6 and len(set(runner.ARMS)) == 6
    assert len(runner.STAGE1_INSTANCES) == 8
    assert len(runner.STAGE2_INSTANCES) == 4
    assert len(runner.STAGES["stage1"][1]) == 48
    assert len(runner.STAGES["stage2"][1]) == 24
    assert runner.STAGES["sentinel"] == (
        120, [("moderate_seed4301", arm) for arm in
              ("S0-SAFE", "EXT-CPX", "EXT-GRB-COLD")])
    assert not any("PON" in arm or "UNSAFE" in arm for arm in runner.ARMS)

    for arm in runner.ARMS:
        config = runner.configuration(arm)
        assert config["uniform_all_instances"] is True
        assert config["instance_or_family_dispatch"] is False
        assert config["threads"] == 1
        assert config["relative_mip_gap"] == 0.0
        assert config["absolute_mip_gap"] == 0.0
    assert runner.configuration("P-CPX")["hga_or_known_ub"] is False
    assert runner.configuration("P-GRB")["hga_or_known_ub"] is False
    for arm in ("S0-SAFE", "EXT-CPX", "EXT-GRB-COLD", "EXT-GRB-WARM"):
        assert runner.configuration(arm)["same_run_verified_hga"] is True
        assert runner.configuration(arm)["hga_seed"] == 20260626
    assert runner.configuration("EXT-GRB-COLD")[
        "explicit_cross_model_warm_start"] is False
    assert runner.configuration("EXT-GRB-WARM")[
        "explicit_cross_model_warm_start"] is True

    manifest = {"executable_sha256": "a" * 64, "source_commit": "b" * 40}
    with tempfile.TemporaryDirectory(dir=ROOT / "build_round25") as directory:
        run_dir = Path(directory)
        for arm in runner.ARMS:
            first = runner.make_command(Path("ExactEBRP.exe"), "V12_M1", arm,
                                        900, run_dir / arm, manifest)
            second = runner.make_command(Path("ExactEBRP.exe"), "V12_M2", arm,
                                         900, run_dir / arm, manifest)
            # Apart from input/output paths, the complete mathematical option
            # vocabulary is invariant across independent instances.
            assert option(first, "--process-wall-time-limit") == "900"
            assert option(first, "--time-limit") == "882.0"
            assert option(first, "--threads") == "1"
            assert first.count("--input") == second.count("--input") == 1
            assert not any("seed3202" in token or "seed4201" in token
                           for token in first)
        assert "--primal-heuristic" not in runner.make_command(
            Path("ExactEBRP.exe"), "V12_M1", "P-CPX", 900,
            run_dir / "plain", manifest)
        assert option(runner.make_command(
            Path("ExactEBRP.exe"), "V12_M1", "S0-SAFE", 900,
            run_dir / "s0", manifest), "--global-gini-tree-presolve") == "off"

    assert summary.comparison_reason(
        row(strict_certificate=True, certificate_wall_seconds=10),
        row(strict_certificate=False))[0] is True
    assert summary.comparison_reason(
        row(final_lb=10), row(final_lb=9))[0] is True
    assert summary.comparison_reason(
        row(final_lb=10), row(final_lb=10, common_ub_gap=0.1,
                              bound_progress_auc=0.5))[0] is False
    assert summary.comparison_reason(
        row(strict_certificate=True, certificate_wall_seconds=100),
        row(strict_certificate=True, certificate_wall_seconds=101),
        material=True)[0] is False
    assert summary.comparison_reason(
        row(strict_certificate=True, certificate_wall_seconds=100),
        row(strict_certificate=True, certificate_wall_seconds=102.1),
        material=True)[0] is True

    external_source = (ROOT / "src" / "ExternalGiniTree.cpp").read_text(
        encoding="utf-8")
    result_source = (ROOT / "src" / "Result.cpp").read_text(encoding="utf-8")
    required_trace_fields = (
        "enhanced_attempt_trace.csv", "controlling_leaves_before",
        "allocated_time_seconds", "last_native_lb_improvement_time_seconds",
        "presolve_time_available", "native_cut_count_available",
        "warm_mapping_complete", "model_read_seconds", "interval_row_count",
        "cutoff_row_count",
    )
    assert all(field in external_source for field in required_trace_fields)
    assert "unavailable_cplex_callable_library_has_no_safe_phase_timer" \
        in external_source
    assert "WRITE_EXT_PATH(enhanced_attempt_trace_path)" in result_source
    production_source = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for folder in (ROOT / "src", ROOT / "include")
        for path in sorted(folder.rglob("*"))
        if path.suffix in (".cpp", ".hpp"))
    assert not re.search(
        r"(?:310[12]|320[12]|330[12]|410[12]|420[12]|430[12])",
        production_source)
    assert not re.search(
        r"(?:moderate_seed|tight_T_seed|high_imbalance_seed)",
        production_source, re.IGNORECASE)
    assert "status_input.native_status_code = out.native_status_code" \
        in external_source
    assert "evaluateExternalCplexLeafStatus(status_input)" in external_source
    assert "verified_seed.verification.original_solution_feasible" \
        in external_source

    protocol = runner.PROTOCOL.read_text(encoding="utf-8")
    normalized_protocol = " ".join(protocol.split())
    assert "Round 25 frozen evaluation protocol" in protocol
    assert "minimum independently verified UB" in normalized_protocol
    assert "exactly one 300-second replay" in normalized_protocol
    assert "No family-dependent selector" in normalized_protocol

    print(json.dumps({
        "round25_protocol_test_groups": 6,
        "arms": len(runner.ARMS),
        "stage1_rows": len(runner.STAGES["stage1"][1]),
        "stage2_rows": len(runner.STAGES["stage2"][1]),
        "status": "passed",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
