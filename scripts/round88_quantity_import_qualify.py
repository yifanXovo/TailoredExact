"""One-shot E8 historical witness and frozen C++ importer qualification."""

from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import subprocess
import sys
import time

import round88_quantity_probe as probe
import round88_quantity_flow as flow


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: round88_quantity_import_qualify.py OUT_DIR")
    directory = Path(sys.argv[1]).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    case = probe.CASES["E8"]
    source = (probe.ROOT / case.input_relative).resolve()
    witness = (probe.ROOT / case.witness_relative).resolve()
    for path, digest in ((source, case.input_sha256),
                         (witness, case.witness_sha256),
                         (probe.BINARY, probe.BINARY_SHA),
                         (probe.ROOT / "scripts/round88_quantity_flow.py",
                          probe.FLOW_SHA)):
        probe.require_sha(path, digest)
    historical = json.loads(witness.read_text(encoding="utf-8"))
    parsed = probe.parse_instance(source.read_text(encoding="utf-8"),
                                  case, source)
    canonical = probe.canonical_routes(historical["routes"],
                                       len(parsed.problem.vehicles),
                                       len(parsed.problem.stations))
    parsed = probe.attach_fixed_routes(parsed, canonical)
    inventory = probe.inventory_from_routes(parsed, canonical)
    candidate = probe.routes_from_inventory(parsed, inventory)
    if probe.canonical_routes(candidate["routes"],
                              len(parsed.problem.vehicles),
                              len(parsed.problem.stations)) != canonical:
        raise probe.ProbeError("E8_witness_not_reversible")
    candidate_path = directory / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, sort_keys=True) + "\n",
                              encoding="utf-8")
    result_path = directory / "cpp_result.json"
    command = [str(probe.BINARY), "--input", str(source),
               "--T", str(case.route_deadline),
               "--pickup-time", str(case.pickup_seconds),
               "--drop-time", str(case.drop_seconds),
               "--lambda", repr(case.penalty_lambda),
               "--method", "incumbent-import-test",
               "--incumbent-json", str(candidate_path),
               "--incumbent-format", "route_json",
               "--out", str(result_path), "--log", str(directory / "cpp.log")]
    probe._write_json(directory / "command.json", dict(
        command=command, binary_sha256=probe.BINARY_SHA,
        input_sha256=case.input_sha256,
        witness_sha256=case.witness_sha256,
        candidate_sha256=probe.sha256(candidate_path)))
    call_started = time.perf_counter()
    try:
        completed = subprocess.run(command, text=True, capture_output=True,
                                   check=False, timeout=30)
    except subprocess.TimeoutExpired as error:
        (directory / "timeout.json").write_text(json.dumps(dict(
            error=repr(error), call_wall_seconds=time.perf_counter() -
            call_started)) + "\n", encoding="utf-8")
        raise
    call_wall = time.perf_counter() - call_started
    (directory / "cpp.stdout.txt").write_text(completed.stdout,
                                                encoding="utf-8")
    (directory / "cpp.stderr.txt").write_text(completed.stderr,
                                                encoding="utf-8")
    probe._write_json(directory / "call_cost.json", dict(
        returncode=completed.returncode, call_wall_seconds=call_wall,
        result_exists=result_path.is_file(),
        result_sha256=probe.sha256(result_path)
        if result_path.is_file() else None))
    if completed.returncode != 0 or not result_path.is_file():
        raise probe.ProbeError("E8_cpp_import_process_failed")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    evidence = probe.validate_cpp_receipt(result, candidate, parsed,
                                          case, result_path)
    source_objective = probe._finite_fraction(historical["objective"],
                                               "source_objective")
    if abs(evidence.objective - source_objective) > F(1, 10_000_000):
        raise probe.ProbeError("E8_source_objective_mismatch")
    budgets = probe.cpp_nominal_budgets(parsed, evidence)
    flow.validate_current(parsed.problem, inventory, budgets)
    if not flow.exact_physical_feasible(parsed.problem, inventory):
        raise probe.ProbeError("E8_internal_physical_mismatch")
    summary = dict(status="qualified", case="E8", inventory=inventory,
                   objective=str(evidence.objective), G=str(evidence.gini),
                   P=str(evidence.penalty),
                   route_travel=[str(x) for x in evidence.route_travel],
                   route_duration=[str(x) for x in evidence.route_duration],
                   budgets=budgets, cpp_call_wall_seconds=call_wall,
                   full_wall_seconds=time.perf_counter() - started,
                   cpp_result_sha256=probe.sha256(result_path))
    probe._write_json(directory / "qualification.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
