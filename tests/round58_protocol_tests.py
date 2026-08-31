#!/usr/bin/env python3
"""Protocol-level tests for the frozen Round 58 paired benchmark runner."""

from __future__ import annotations

import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import round58_common as r58  # noqa: E402
import run_round58_paired_benchmark as runner  # noqa: E402
from round58_route_archive import archive_native_result, verify_native_result  # noqa: E402


def main() -> int:
    checks = 0

    def require(value: bool, label: str) -> None:
        nonlocal checks
        if not value:
            raise AssertionError(label)
        checks += 1

    panel = runner.panel()
    primary, matched, reserve = r58.build_panel()
    frozen = r58.read_csv(r58.EVIDENCE / "round58_complete_panel.csv")

    require(all(row["dataset_family"] == r58.DATASET_FAMILY for row in panel),
            "1 dataset-family identity")
    require(all(r58.sha256_file(ROOT / row["instance_path"]) ==
                row["instance_file_sha256"] for row in panel),
            "2 source hash verification")
    determinism_fields = (
        "panel_class", "scenario_id", "scenario_sha256", "method_first",
        "method_second", "V", "M", "Q", "T_seconds")
    require([
        tuple(str(row.get(field, "")) for field in determinism_fields)
        for row in r58.normalized_panel_rows(primary + matched)
    ] == [
        tuple(str(row.get(field, "")) for field in determinism_fields)
        for row in frozen
    ], "3 panel-selection determinism")
    require(len(primary) == 30, "4 primary-panel cardinality")
    require(len(matched) == 20, "5 matched-T cardinality")
    require(len({row["scenario_id"] for row in panel}) == 50,
            "6 no duplicate scenario")
    require(len(reserve) == 910 and not ({row["scenario_id"] for row in reserve} &
                                         {row["scenario_id"] for row in panel}),
            "7 reserve scenarios unselected")
    require({int(row["M"]) for row in panel} == {1, 2, 3, 4, 5, 7} and
            {int(row["Q"]) for row in panel} == {20, 30} and
            {int(row["T_seconds"]) for row in panel} == {1800, 3600, 10800, 18000},
            "8 M/Q/T representation")
    require(all(row["method_first"] ==
                ("k1_am_sf" if int(row["scenario_sha256"][0], 16) % 2 == 0
                 else "pgrb") for row in panel),
            "9 method-order determinism")

    sample = panel[0]
    k1_command, _ = runner.command_for(
        sample, "k1_am_sf", 3600, Path("round58-test-k1"))
    p_command, _ = runner.command_for(
        sample, "pgrb", 3600, Path("round58-test-pgrb"))
    require(runner.option_value(k1_command, "--algorithm-preset") ==
            "paper-k1-am-sf", "10 K1 preset identity")
    require(runner.option_value(p_command, "--method") == "gurobi" and
            "--plain-baseline" in p_command, "11 P-GRB plain identity")
    require(not any(option in p_command for option in runner.FORBIDDEN_OPTIONS),
            "12 P-GRB tailored mechanisms disabled")
    expected_fp = runner.fingerprint_index()[sample["scenario_id"]][
        "expected_gurobi_model_fingerprint"]
    require(int(runner.option_value(
        p_command, "--round24-expected-gurobi-model-fingerprint")) == expected_fp,
        "13 expected fingerprint binding")
    scope_probe = {
        "method": "gurobi", "method_scope": "plain_gurobi",
        "cplex_plain_baseline": True, "gurobi_hga_incumbent_found": False,
        "gurobi_hga_start_submitted": False,
        "gurobi_model_fingerprint": int(expected_fp) + 1,
        "gurobi_native_domain_audit_passed": True,
        "gurobi_native_variable_names_match": True,
        "gurobi_native_variable_types_match": True,
        "gurobi_native_variable_bounds_match": True,
        "gurobi_lifecycle_valid": True, "gurobi_threads_effective": 1,
        "gurobi_seed_effective": 0, "gurobi_presolve_effective": -1,
    }
    require(not runner.pgrb_scope_valid(sample, scope_probe),
            "14 fingerprint mismatch rejection")

    gaps = runner.explicit_gaps(90.0, 100.0)
    require(gaps["absolute_gap"] == 10.0, "15 absolute-gap formula")
    require(abs(gaps["relative_gap"] - 0.1) < 1e-12,
            "16 relative-gap formula")
    require(abs(gaps["scaled_gap"] - 0.1) < 1e-12,
            "17 scaled-gap formula")
    require("gap" not in runner.RUN_FIELDS,
            "18 no ambiguous summary-gap field")
    require(len(list(runner.execution_order(panel))) == 100,
            "19 mandatory dual-method screen")

    def fake_summary(cert: bool, rel: float | None, wall: float) -> dict:
        return {"strict_certificate": cert, "relative_gap": rel,
                "actual_wall_time_seconds": wall}

    row = sample
    with mock.patch.object(runner, "marker_summary") as marker:
        marker.side_effect = lambda _r, method, cap: (
            fake_summary(True, 0.0, 20.0) if cap == 3600 else None)
        decision = runner.screen_action(row)
    require(not decision["extend_k1_to_10800"] and
            not decision["extend_pgrb_to_10800"], "20 both-certified stop")
    with mock.patch.object(runner, "marker_summary") as marker:
        marker.side_effect = lambda _r, method, cap: (
            fake_summary(method == "k1_am_sf", 0.08 if method == "pgrb" else 0.0,
                         100.0) if cap == 3600 else None)
        decision = runner.screen_action(row)
    require(decision["extend_pgrb_to_10800"],
            "21 single-certified extension rule")
    with mock.patch.object(runner, "marker_summary") as marker:
        marker.side_effect = lambda _r, method, cap: (
            fake_summary(False, 0.2, 3600.0) if cap == 3600 else None)
        decision = runner.screen_action(row)
    require(decision["extend_k1_to_10800"] and
            decision["extend_pgrb_to_10800"], "22 neither-certified rule")
    with mock.patch.object(runner, "marker_summary",
                           return_value=fake_summary(False, 0.05, 10800.0)):
        near = runner.near_action(row, "k1_am_sf")
    require(near["authorized_next_cap_seconds"] == 21600,
            "23 five-percent tier")
    with mock.patch.object(runner, "marker_summary",
                           return_value=fake_summary(False, 0.08, 10800.0)):
        near = runner.near_action(row, "k1_am_sf")
    require(near["authorized_next_cap_seconds"] == 16200,
            "24 ten-percent tier")
    require(max(runner.STAGE_CAP.values()) == 21600,
            "25 six-hour hard cap")
    with mock.patch.object(runner, "marker_summary",
                           return_value=fake_summary(False, 0.11, 10800.0)):
        near = runner.near_action(row, "k1_am_sf")
    require(near["authorized_next_cap_seconds"] is None,
            "26 no unauthorized extension")
    require("fresh independent optimizer process" in
            runner.summarize_result.__doc__ if runner.summarize_result.__doc__ else
            all(runner.option_value(k1_command, option) is not None for option in
                ("--process-wall-time-limit", "--time-limit")),
            "27 fresh-run accounting command")
    require(runner.pair_class(
        {"strict_certificate": False, "relative_gap": 0.01,
         "valid_lower_bound": 1.0, "verified_upper_bound": 2.0},
        {"strict_certificate": False, "relative_gap": 0.02,
         "valid_lower_bound": 0.9, "verified_upper_bound": 2.1}) ==
            "neither_certified_k1_better_bound", "28 common-horizon comparison")

    with tempfile.TemporaryDirectory(prefix="round58-protocol-") as temporary:
        root = Path(temporary)
        live = root / "live_runs.csv"
        simple = {field: "" for field in runner.RUN_FIELDS}
        simple.update({"run_identity_sha256": "one", "scenario_id": "s",
                       "completion_sequence_number": 1})
        with mock.patch.object(r58, "LIVE_RUNS", live):
            runner.append_live_run(simple)
            runner.append_live_run(simple)
        require(len(r58.read_csv(live)) == 1, "29 live CSV append and deduplicate")
        pair_file = root / "pairs.csv"
        r58.write_csv(pair_file, [{"scenario_id": "s", "state": "done"}],
                      atomic=True)
        require(pair_file.is_file() and not pair_file.with_suffix(
            pair_file.suffix + ".tmp").exists(), "30 atomic pair rewrite")

        run_root = root / "run"
        run_root.mkdir()
        identity = runner.expected_identity(sample, "k1_am_sf", 3600)
        result = {
            "run_identity_sha256": identity,
            "mathematical_instance_sha256": sample["scenario_sha256"],
            "route_time_limit_seconds": int(sample["T_seconds"]),
            "solver_process_cap_seconds": 3600,
        }
        r58.write_json(run_root / "result.json", result)
        r58.write_json(run_root / "command.json", {"identity": identity})
        r58.write_json(run_root / "independent_verification.json", {"passed": False})
        marker_value = {
            "complete": True, "source_freeze_commit": runner.SOURCE_FREEZE,
            "executable_sha256": runner.EXE_SHA256,
            "scenario_sha256": sample["scenario_sha256"],
            "run_identity_sha256": identity,
            "result_sha256": r58.sha256_file(run_root / "result.json"),
            "verification_sha256": r58.sha256_file(
                run_root / "independent_verification.json"),
            "command_sha256": r58.sha256_file(run_root / "command.json"),
            "summary": {"completion_sequence_number": 1},
        }
        r58.write_json(run_root / "completion_marker.json", marker_value)
        with mock.patch.object(runner, "run_dir", return_value=run_root):
            resumed = runner.completion_marker(sample, "k1_am_sf", 3600)
        require(resumed is not None, "31 interruption/resume behavior")
        (run_root / "result.json").write_text(
            (run_root / "result.json").read_text(encoding="utf-8") + " ",
            encoding="utf-8")
        rejected = False
        try:
            with mock.patch.object(runner, "run_dir", return_value=run_root):
                runner.completion_marker(sample, "k1_am_sf", 3600)
        except RuntimeError:
            rejected = True
        require(rejected, "32 completion-marker hash validation")
        require(len(r58.read_csv(live)) == 1, "33 no duplicate completed run")

        scenario_id = "cb443_V08_compact_r1_shortage_M01_Q30_T03600"
        probe_result = (r58.RAW / "fingerprint_preflight" / scenario_id /
                        "result.json")
        verified = verify_native_result(scenario_id, probe_result)
        require(verified["passed"] and
                not verified["optimization_or_repair_performed"],
                "34 route archive roundtrip verifier")
        solutions = root / "solutions"
        with mock.patch.object(r58, "SOLUTIONS", solutions), \
                mock.patch.object(r58, "repo_path", side_effect=lambda path: str(path)):
            archive = archive_native_result(
                scenario_id, "pgrb", probe_result, runner.SOURCE_FREEZE,
                runner.EXE_SHA256)
        package_path = solutions / scenario_id / "pgrb"
        package = r58.read_json(package_path / "native_solution.json")
        audit = r58.read_json(package_path / "solution_verification.json")
        require(package["certificate_label"] == "noncertified",
                "35 exact/nonexact route labeling")
        require(audit["archive_time_excluded_from_algorithm_time"] is True,
                "36 archive time excluded")

    contract = r58.read_json(r58.EVIDENCE / "paired_solver_contract.json")
    require(contract["k1_am_sf"]["preset"] == "paper-k1-am-sf" and
            contract["k1_am_sf"]["tau"] == 0.08,
            "37 no algorithm tuning")
    require("VD-P" not in json.dumps(contract), "38 no VD-P")
    require(runner.option_value(p_command, "--gurobi-hga-start") == "false" and
            not any(option in p_command for option in
                    ("--incumbent-json", "--external-incumbent")),
            "39 no external incumbent or HGA start")
    require(all(row["selection_status"] == "selected_round58_before_performance"
                for row in panel), "40 no scenario replacement")
    preservation = r58.read_json(
        r58.EVIDENCE / "preexisting_file_preservation_audit.json")
    require(all(r58.sha256_file(ROOT / item["path"]) == item["sha256"]
                for item in preservation["tracked_modified_files"]),
            "41 user-file preservation")
    require(checks == 41, "42 protocol check-count guard")
    print(f"Round58 protocol tests passed {checks} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
