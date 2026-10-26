"""Offline endpoint diagnostic for the explicit Round88 composite proxy.

Only ``supervise`` is an execution entry. Its 120-second whole-case deadline
covers source checks, every original C++ verification, and result writing.
This module never changes the frozen linear probe or native ENS-C behavior.
"""

from __future__ import annotations

import argparse
from fractions import Fraction as F
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable

import round88_quantity_flow as flow
import round88_quantity_probe as probe
import round88_quantity_composite as composite


ROOT = Path(__file__).resolve().parents[1]
METHOD_ID = "round88-a2-composite-penalty-offline"
WHOLE_CASE_SECONDS = 120.0
FLOW_SHA = probe.FLOW_SHA
PROBE_SHA = "6a06a03212dc5da954be57e7c81b5a0f67c77bea592720955dc9c2b8e3c9c77c"
COMPOSITE_SHA = "dccbf59fa462a25308419f49a719f59d0d9ef514f917ab377b9215ffdcdcd898"


def source_assets(case: probe.Case) -> tuple[tuple[str, Path, str], ...]:
    return (
        ("binary", probe.BINARY, probe.BINARY_SHA),
        ("flow", ROOT / "scripts/round88_quantity_flow.py", FLOW_SHA),
        ("old_probe", ROOT / "scripts/round88_quantity_probe.py", PROBE_SHA),
        ("composite", ROOT / "scripts/round88_quantity_composite.py", COMPOSITE_SHA),
        ("input", (ROOT / case.input_relative).resolve(), case.input_sha256),
        ("witness", (ROOT / case.witness_relative).resolve(), case.witness_sha256),
    )


def require_frozen_sources(case: probe.Case) -> None:
    for _label, path, expected in source_assets(case):
        probe.require_sha(path, expected)


def certificate_json(cert: composite.CompositeCertificate) -> dict[str, Any]:
    return dict(
        network=probe._certificate_json(cert.network),
        gini_gradient=[str(x) for x in cert.gini_gradient],
        marginal_arcs=[dict(station=a.station, direction=a.direction,
                            first_unit=a.first_unit, units=a.units,
                            rational_cost=str(a.rational_cost), arc_id=a.arc_id)
                       for a in cert.marginal_arcs],
        projections=[dict(station=p.station, raw_pickup=p.raw_pickup,
                          raw_drop=p.raw_drop, canceled=p.canceled,
                          canonical_pickup=p.canonical_pickup,
                          canonical_drop=p.canonical_drop,
                          final_inventory=p.final_inventory,
                          raw_cost_from_initial=str(p.raw_cost_from_initial),
                          projected_cost_from_initial=str(
                              p.projected_cost_from_initial))
                     for p in cert.projections],
        raw_flow_cost_from_initial=str(cert.raw_flow_cost_from_initial),
        proxy_cost_from_initial=str(cert.proxy_cost_from_initial))


def one_round(
        parsed: probe.Parsed, current: tuple[int, ...],
        current_evidence: probe.CppEvidence,
        verifier: Callable[[tuple[int, ...]], probe.CppEvidence],
        event: Callable[[dict[str, Any]], None],
        checkpoint: Callable[[dict[str, Any]], None] | None = None
        ) -> tuple[str, tuple[int, ...], probe.CppEvidence, dict[str, Any]]:
    """One complete composite proxy and every admissible primitive point."""
    started = time.perf_counter()
    budgets = probe.cpp_nominal_budgets(parsed, current_evidence)
    try:
        flow.validate_current(parsed.problem, current, budgets)
    except flow.QuantityDomainError as error:
        raise probe.ProbeError(error.code) from error
    if not flow.exact_physical_feasible(parsed.problem, current):
        raise probe.ProbeError("domain_rejected_current_internal_physical")
    gradient = composite.gini_local_gradient(parsed.problem, current)
    if gradient is None:
        return ("no_gradient_at_zero", current, current_evidence,
                dict(status="no_gradient_at_zero", budgets=budgets,
                     current_inventory=current,
                     current_cpp_objective=str(current_evidence.objective),
                     round_wall_seconds=time.perf_counter() - started))
    oracle_started = time.perf_counter()
    proposal, certificate = composite.composite_oracle(
        parsed.problem, gradient, budgets)
    oracle_seconds = time.perf_counter() - oracle_started
    line = flow.primitive_segment(current, proposal)
    if any(not flow.in_nominal_network_domain(parsed.problem, point, budgets)
           for point in line):
        raise probe.ProbeError("composite_line_outside_nominal_domain")
    proxy_delta = (composite.proxy_increment(parsed.problem, gradient, proposal) -
                   composite.proxy_increment(parsed.problem, gradient, current))
    record: dict[str, Any] = dict(
        current_inventory=current,
        current_cpp_objective=str(current_evidence.objective), budgets=budgets,
        gini_gradient=[str(x) for x in gradient],
        proposal_inventory=proposal,
        proxy_delta_from_current=str(proxy_delta),
        primitive_steps=len(line) - 1, oracle_seconds=oracle_seconds,
        certificate=certificate_json(certificate))
    event(dict(kind="composite_oracle_complete", proposal=proposal,
               proxy_delta_from_current=str(proxy_delta),
               proxy_cost_from_initial=str(
                   certificate.proxy_cost_from_initial),
               primitive_steps=len(line) - 1,
               oracle_seconds=oracle_seconds))
    if checkpoint is not None:
        checkpoint(record)
    if len(line) == 1:
        record.update(status="no_direction", round_wall_seconds=
                      time.perf_counter() - started)
        return "no_direction", current, current_evidence, record
    best, best_evidence, rejected, cpp_calls = probe.scan_integer_line(
        parsed, current, proposal, current_evidence, verifier, event)
    status = "improved" if best != current else "no_verified_improvement"
    record.update(status=status, internal_rejected_points=rejected,
                  cpp_verified_line_points=cpp_calls,
                  accepted_inventory=best if best != current else None,
                  best_cpp_objective=str(best_evidence.objective),
                  round_wall_seconds=time.perf_counter() - started)
    return status, best, best_evidence, record


def diagnose(case: probe.Case, directory: Path) -> dict[str, Any]:
    if os.environ.get("ROUND88_A2_COMPOSITE_SUPERVISED") != "1":
        raise probe.ProbeError("composite_diagnose_requires_supervisor")
    ready_path = os.environ.get("ROUND88_A2_COMPOSITE_READY_PATH")
    if not ready_path:
        raise probe.ProbeError("composite_diagnose_requires_ready_path")
    while not Path(ready_path).is_file():
        time.sleep(0.01)
    started = time.perf_counter()
    events = directory / "events.jsonl"
    candidates = directory / "candidates"
    candidates.mkdir(exist_ok=False)

    def event(item: dict[str, Any]) -> None:
        item["elapsed_seconds"] = time.perf_counter() - started
        probe._append_jsonl(events, item)

    require_frozen_sources(case)
    source = (ROOT / case.input_relative).resolve()
    witness = (ROOT / case.witness_relative).resolve()
    with witness.open("r", encoding="utf-8") as stream:
        historical = json.load(stream)
    if not isinstance(historical, dict):
        raise probe.ProbeError("historical_witness_shape")
    parsed = probe.parse_instance(source.read_text(encoding="utf-8"), case,
                                  source)
    canonical = probe.canonical_routes(historical.get("routes"),
                                       len(parsed.problem.vehicles),
                                       len(parsed.problem.stations))
    parsed = probe.attach_fixed_routes(parsed, canonical)
    current = probe.inventory_from_routes(parsed, canonical)
    if probe.canonical_routes(
            probe.routes_from_inventory(parsed, current)["routes"],
            len(parsed.problem.vehicles),
            len(parsed.problem.stations)) != canonical:
        raise probe.ProbeError("historical_route_mapping_not_reversible")
    result: dict[str, Any] = dict(
        status="running", method=METHOD_ID, case=case.key,
        input_path=str(source), input_sha256=case.input_sha256,
        witness_path=str(witness), witness_sha256=case.witness_sha256,
        binary_sha256=probe.BINARY_SHA, flow_sha256=FLOW_SHA,
        old_probe_sha256=PROBE_SHA, composite_sha256=COMPOSITE_SHA,
        original_inventory=list(current), original_routes=historical["routes"],
        cpp_calls=0, internal_rejected_points=0, rounds=[],
        start_wall_time=time.time())
    probe._write_json(directory / "result.json", result)
    event(dict(kind="historical_witness_mapped", inventory=current,
               source_objective=historical.get("objective")))

    def verify(inventory: tuple[int, ...]) -> probe.CppEvidence:
        call_number = result["cpp_calls"]
        result["cpp_calls"] += 1
        probe._write_json(directory / "result.json", result)
        return probe.cpp_verify(
            parsed, case, probe.routes_from_inventory(parsed, inventory),
            candidates, call_number, event)

    evidence = verify(current)
    historical_objective = probe._finite_fraction(
        historical.get("objective"), "historical_objective")
    if abs(evidence.objective - historical_objective) > F(1, 10_000_000):
        raise probe.ProbeError("historical_objective_cpp_mismatch")
    result.update(original_cpp_objective=str(evidence.objective),
                  original_cpp_G=str(evidence.gini),
                  original_cpp_P=str(evidence.penalty),
                  original_route_travel=[str(x) for x in evidence.route_travel],
                  original_route_duration=[str(x) for x in evidence.route_duration])
    probe._write_json(directory / "result.json", result)
    seen = {current}
    while True:
        def checkpoint(record: dict[str, Any]) -> None:
            record["index"] = len(result["rounds"])
            record["status"] = "oracle_complete_line_pending"
            result["rounds"].append(record)
            probe._write_json(directory / "result.json", result)

        status, best, best_evidence, record = one_round(
            parsed, current, evidence, verify, event, checkpoint)
        if not result["rounds"] or result["rounds"][-1] is not record:
            record["index"] = len(result["rounds"])
            result["rounds"].append(record)
        result["internal_rejected_points"] += record.get(
            "internal_rejected_points", 0)
        probe._write_json(directory / "result.json", result)
        if status != "improved":
            event(dict(kind="terminal", reason=status))
            break
        if best in seen or not best_evidence.objective < evidence.objective:
            raise probe.ProbeError("strict_descent_or_cycle_failure")
        event(dict(kind="round_strict_cpp_improvement", round=record["index"],
                   objective_before=str(evidence.objective),
                   objective_after=str(best_evidence.objective),
                   inventory=best))
        current, evidence = best, best_evidence
        seen.add(current)
        parsed = probe.attach_fixed_routes(parsed, probe.canonical_routes(
            probe.routes_from_inventory(parsed, current)["routes"],
            len(parsed.problem.vehicles), len(parsed.problem.stations)))
    result.update(status="completed_composite_endpoint", stop_reason=status,
                  final_inventory=current,
                  final_cpp_objective=str(evidence.objective),
                  final_cpp_G=str(evidence.gini),
                  final_cpp_P=str(evidence.penalty),
                  final_route_travel=[str(x) for x in evidence.route_travel],
                  final_route_duration=[str(x) for x in evidence.route_duration],
                  final_receipt_path=evidence.receipt_path,
                  diagnosis_wall_seconds=time.perf_counter() - started)
    probe._write_json(directory / "result.json", result)
    return result


def classify_supervision(expired: bool, elapsed: float, limit: float,
                         stable: bool, returncode: int | None,
                         child: dict[str, Any] | None,
                         case: probe.Case) -> str:
    if expired or elapsed > limit:
        return "unknown_whole_process_deadline"
    if not stable:
        return "invalid_source_identity_drift"
    identity = (child is not None and child.get("method") == METHOD_ID and
                child.get("case") == case.key)
    if (identity and returncode == 0 and
            child.get("status") == "completed_composite_endpoint"):
        return "diagnostic_completed"
    if (identity and returncode == 2 and
            str(child.get("status", "")).startswith(
                ("domain_rejected", "domain_uncertain"))):
        return "diagnostic_inapplicable"
    return "diagnostic_invalid"


def supervise(case: probe.Case, directory: Path, limit: float) -> dict[str, Any]:
    if limit != WHOLE_CASE_SECONDS:
        raise probe.ProbeError("whole_case_limit_must_be_120_seconds")
    started = time.perf_counter()
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    assets = source_assets(case)
    preflight: dict[str, str] = {}
    process: subprocess.Popen[str] | None = None
    job: probe._WindowsJob | None = None
    stdout = stderr = ""
    expired = False
    returncode: int | None = None
    try:
        for label, path, expected in assets:
            probe.require_sha(path, expected)
            preflight[label + "_sha256"] = expected
        preflight["adapter_sha256"] = probe.sha256(script)
        command = [sys.executable, str(script), "diagnose", "--case",
                   case.key, "--out-dir", str(directory)]
        if time.perf_counter() - started >= limit:
            expired = True
        else:
            env = os.environ.copy()
            env["ROUND88_A2_COMPOSITE_SUPERVISED"] = "1"
            ready = directory / "supervisor_ready.flag"
            env["ROUND88_A2_COMPOSITE_READY_PATH"] = str(ready)
            if os.name == "nt":
                job = probe._WindowsJob()
            flags = (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt"
                     else 0)
            process = subprocess.Popen(
                command, cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, creationflags=flags,
                start_new_session=os.name != "nt")
            if job is not None:
                job.assign(process)
            ready.write_text("assigned\n", encoding="ascii")
            remaining = max(0.0, limit - (time.perf_counter() - started))
            if remaining <= 0:
                expired = True
                probe._kill_process_tree(process, job)
                stdout, stderr = process.communicate()
            else:
                try:
                    stdout, stderr = process.communicate(timeout=remaining)
                except subprocess.TimeoutExpired:
                    expired = True
                    probe._kill_process_tree(process, job)
                    stdout, stderr = process.communicate()
            if job is not None:
                job.close()
        returncode = process.returncode if process is not None else None
    except Exception as error:
        if process is not None:
            probe._kill_process_tree(process, job)
        elif job is not None:
            job.close()
        stderr += "\nsupervisor_exception=" + repr(error)
    (directory / "supervisor_stdout.txt").write_text(stdout, encoding="utf-8")
    (directory / "supervisor_stderr.txt").write_text(stderr, encoding="utf-8")
    final_hashes = {
        label + "_sha256": probe.sha256(path) if path.is_file() else None
        for label, path, _expected in (*assets, ("adapter", script, ""))}
    elapsed = time.perf_counter() - started
    child_path = directory / "result.json"
    child: dict[str, Any] | None = None
    if child_path.is_file():
        try:
            with child_path.open("r", encoding="utf-8") as stream:
                loaded = json.load(stream)
            if isinstance(loaded, dict):
                child = loaded
        except (OSError, ValueError):
            pass
    stable = all(final_hashes.get(label) == expected
                 for label, expected in preflight.items())
    status = classify_supervision(expired, elapsed, limit, stable,
                                  returncode, child, case)
    summary = dict(
        status=status, method=METHOD_ID, case=case.key,
        whole_process_limit_seconds=limit,
        whole_process_wall_seconds=elapsed,
        wall_clock_boundary="before_supervision_json_write",
        child_returncode=returncode,
        child_pid=process.pid if process is not None else None,
        timed_out=expired or elapsed > limit, preflight=preflight,
        final_hashes=final_hashes,
        child_status=child.get("status") if child else None,
        child_cpp_calls=child.get("cpp_calls") if child else None,
        child_rounds=len(child.get("rounds", [])) if child else None,
        command=command if "command" in locals() else None)
    probe._write_json(directory / "supervision.json", summary)
    after_write = time.perf_counter() - started
    if after_write > limit and status != "unknown_whole_process_deadline":
        summary["status"] = "unknown_whole_process_deadline"
        summary["timed_out"] = True
        summary["after_first_summary_write_wall_seconds"] = after_write
        probe._write_json(directory / "supervision.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("supervise", "diagnose"))
    parser.add_argument("--case", required=True, choices=tuple(probe.CASES))
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--whole-process-limit-seconds", type=float,
                        default=WHOLE_CASE_SECONDS)
    args = parser.parse_args()
    case = probe.CASES[args.case]
    if args.mode == "supervise":
        result = supervise(case, args.out_dir,
                           args.whole_process_limit_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in (
            "diagnostic_completed", "diagnostic_inapplicable") else 2
    directory = args.out_dir.resolve()
    if not directory.is_dir():
        raise probe.ProbeError("diagnose_output_directory_missing")
    try:
        diagnose(case, directory)
        return 0
    except (probe.ProbeError, flow.QuantityDomainError) as error:
        result_path = directory / "result.json"
        result: dict[str, Any] = {}
        if result_path.is_file():
            try:
                with result_path.open("r", encoding="utf-8") as stream:
                    result = json.load(stream)
            except (OSError, ValueError):
                pass
        result.update(status=error.code, method=METHOD_ID, case=case.key,
                      error_type=type(error).__name__, error_text=str(error))
        probe._write_json(result_path, result)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
