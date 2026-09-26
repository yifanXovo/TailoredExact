"""Round 88 D6 G2 startup-only diagnostic, separate from the G3 screen.

dry-run and prepare perform zero Optimize calls. run requires an explicit,
identity-bound Astra lease; importing the module is inert.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import analyze_round61 as physical_module
import round70_affinity as affinity
from round73_seed_diagnostic import replay_joint, route_hash
from round75_startup import normalize
from round83_audit_v2 import audit as replay_exchange
import round88_a1_g3 as common


ROOT = common.ROOT
STAGE = common.STAGE
PREREG = STAGE / "preregistration_a1_startup_d6.json"
OUT = STAGE / "runner_a1_startup_d6"


def csvrows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def validate(prereg: dict) -> dict:
    assert prereg["schema"] == "round88-a1-startup-d6-preregistration-v1"
    common.ensure_static_identity(common.read(common.PREREG), require_frozen_head=True)
    assert prereg["source_commit"] == common.read(common.PREREG)["source_commit"]
    assert prereg["binary_sha256"] == common.read(common.PREREG)["candidate_binary_sha256"]
    assert prereg["arms"] == ["ENS-C", "A1"]
    assert prereg["whole_diagnostic_process_cap_seconds"] == 120
    assert prereg["native_limit_seconds"] == 114 and prereg["external_hard_stop_seconds"] == 118
    assert prereg["expected_optimize_calls"] == 0
    assert (prereg["threads"], prereg["mip_threads"], prereg["gurobi_seed"],
            prereg["gurobi_presolve"], prereg["affinity_mask"]) == (1, 1, 0, -1, 4)
    row = next(row for row in common.read(common.INPUT_AUDIT)["roles"] if row["id"] == "D6")
    assert row["passed"] and row["actual_sha256"] == prereg["input_sha256"]
    assert Path(row["execution_path"]).relative_to(ROOT).as_posix() == prereg["input_path"]
    for key in ("scenario_id", "T_seconds", "lambda", "pickup_seconds", "drop_seconds"):
        assert row[key] == prereg[key], key
    assert common.sha(ROOT / prereg["input_path"]) == prereg["input_sha256"]
    return dict(id="D6", scenario_id=prereg["scenario_id"], input_path=prereg["input_path"],
                instance_path=prereg["input_path"],
                input_sha256=prereg["input_sha256"], T_seconds=prereg["T_seconds"],
                lambda_=prereg["lambda"], pickup_seconds=prereg["pickup_seconds"],
                drop_seconds=prereg["drop_seconds"])


def launches(prereg: dict) -> list[dict]:
    panel = validate(prereg)
    panel["lambda"] = panel.pop("lambda_")
    items = []
    for arm in prereg["arms"]:
        number = len(items) + 1
        dest = OUT / "raw" / f"{number:02d}_D6_{arm}"
        command = [
            str((ROOT / prereg["binary"]).resolve()),
            "--input", prereg["input_path"], "--lambda", str(prereg["lambda"]),
            "--T", str(prereg["T_seconds"]), "--pickup-time", str(prereg["pickup_seconds"]),
            "--drop-time", str(prereg["drop_seconds"]),
            "--time-limit", str(prereg["native_limit_seconds"]),
            "--process-wall-time-limit", str(prereg["whole_diagnostic_process_cap_seconds"]),
            "--process-shutdown-margin", str(prereg["shutdown_margin_seconds"]),
            "--threads", "1", "--mip-threads", "1", "--gurobi-seed", "0",
            "--gurobi-presolve", "-1", "--method", "primal-heuristic",
            "--algorithm-preset", "research-round83-vds-equal-net-exchange",
            "--round61-candidate-mode", "off", "--out", str(dest / "result.json"),
            "--log", str(dest / "native.log"), "--process-phase-ledger", str(dest / "phases.csv"),
            "--external-gini-artifact-dir", str(dest / "external"),
            "--heuristic-candidates-csv", str(dest / "heuristic.csv"),
            "--primal-heuristic-generation-log", str(dest / "hga.csv"),
            "--progress-log", str(dest / "progress.csv"),
            "--round65-hga-zero-stop", "true",
            "--round60-hga-candidate-log", str(dest / "hga_events.csv"),
        ]
        if arm == "A1":
            command += ["--round88-constructive-only-descent", "true"]
        items.append(dict(number=number, id="D6", arm=arm, panel=panel,
                          destination=str(dest), command=command,
                          process_cap_seconds=120, hard_stop_seconds=118,
                          expected_optimize_calls=0))
    return items


def dry_run() -> None:
    prereg = common.read(PREREG)
    items = launches(prereg)
    assert len(items) == 2 and all(item["expected_optimize_calls"] == 0 for item in items)
    report = dict(schema="round88-a1-startup-d6-dryrun-v1", optimizer_calls=0,
                  processes_started=0, prereg_sha256=common.sha(PREREG),
                  runner_sha256=common.sha(Path(__file__)), launches=items)
    path = STAGE / f'screen_a1_startup_d6_dryrun_{report["runner_sha256"][:12]}.json'
    if path.exists():
        assert common.read(path) == report
    else:
        common.write_new(path, report)
    print(json.dumps(dict(optimizer_calls=0, processes_started=0, planned_runs=2,
                          full_diagnostic_cap_seconds=240)), flush=True)


def prepare() -> None:
    prereg = common.read(PREREG)
    items = launches(prereg)
    assert not OUT.exists(), "Diagnostic root already exists; never overwrite or rerun"
    OUT.mkdir()
    identity = dict(schema="round88-a1-startup-d6-identity-v1",
                    source_commit=prereg["source_commit"], binary_sha256=prereg["binary_sha256"],
                    prereg_sha256=common.sha(PREREG), runner_sha256=common.sha(Path(__file__)),
                    physical_reader_sha256=common.sha(Path(physical_module.__file__)),
                    affinity_sha256=common.sha(ROOT / "scripts/round70_affinity.py"),
                    normalizer_sha256=common.sha(ROOT / "scripts/round75_startup.py"),
                    common_runner_sha256=common.sha(ROOT / "scripts/round88_a1_g3.py"),
                    joint_reader_sha256=common.sha(ROOT / "scripts/round73_seed_diagnostic.py"),
                    exchange_reader_sha256=common.sha(ROOT / "scripts/round83_audit_v2.py"),
                    input_audit_sha256=common.sha(common.INPUT_AUDIT),
                    prepared_unix=time.time(), launches=items, optimizer_calls=0)
    common.write_new(OUT / "identity.json", identity)
    common.write_new(OUT / "preflight.json", dict(schema="round88-a1-startup-d6-preflight-v1",
                     planned_runs=2, optimizer_calls=0, input_hash_verified=True,
                     binary_hash_verified=True, total_process_cap_seconds=240))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, diagnostic_root=str(OUT))), flush=True)


def audit_primal_trace(item: dict, dest: Path, outer: dict) -> dict:
    """Replay constructive seed and physical equal-net closure on saved bytes."""
    # Independently replay the constructive prefix and the inherited equal-net
    # closure.  Fitness in descent.csv is never treated as a physical UB.
    joint = csvrows(dest / "hga.csv.joint.csv")
    prefix: dict[int, dict] = {}
    for row in joint:
        if row["status"] != "accepted_verified":
            continue
        vehicle, pick, drop, quantity, pickup_leg, drop_leg = [int(row[key]) for key in
            ("vehicle", "pickup", "drop", "quantity", "pickup_leg", "drop_leg")]
        route = prefix.setdefault(vehicle, dict(vehicle=vehicle, nodes=[0, 0], operations=[]))
        if drop:
            route["nodes"].insert(drop_leg + 1, drop)
            route["operations"].append(dict(station=drop, pickup=0, drop=quantity))
        if pick:
            route["nodes"].insert(pickup_leg + 1, pick)
            route["operations"].append(dict(station=pick, pickup=quantity, drop=0))
    joint_result = dict(routes=list(prefix.values()), objective=float(joint[-1]["objective"]),
                        upper_bound=float(joint[-1]["objective"]))
    joint_audit = replay_joint(item["panel"], dest, joint_result)
    folder = dest / "hga.csv.exchange"
    initial = normalize(common.read(folder / "initial.json"))
    neutral = replay_exchange(item["panel"], folder, initial)
    assert not common.read(folder / "result.json")["verification_failed"]
    final = normalize(common.read(folder / "final.json"))
    outer = normalize(outer)
    returned_final = route_hash(outer) == route_hash(final)
    returned_initial = route_hash(outer) == route_hash(initial)
    assert returned_final or returned_initial
    if returned_initial and not returned_final:
        assert 0 <= initial["F"] - final["F"] <= 1e-10
    return dict(constructive_prefix=joint_audit, neutral_closure=neutral,
                outer_handoff=dict(final_route_match=returned_final, initial_route_match=returned_initial))


def audit_one(item: dict, completion: dict) -> dict:
    dest = Path(item["destination"])
    result = common.read(dest / "result.json")
    expected = "research-round88-ensc-constructive-only" if item["arm"] == "A1" else "research-round83-vds-equal-net-exchange"
    assert result["algorithm_preset"] == expected
    assert result["method"] == "primal-heuristic"
    assert result["certificate_scope"] == "primal_heuristic_ub_only"
    assert result["strict_certified_original_problem"] is False
    assert result["hga_total_generations"] == 0
    assert result["decoded_descent_complete"] is True
    assert result["decoded_descent_seeds_completed"] == (1 if item["arm"] == "A1" else 25)
    assert not (dest / "external").exists(), "unexpected exact external-model phase"
    for path in dest.rglob("*.log"):
        assert "Optimize a model" not in path.read_text(encoding="utf-8", errors="replace")
    assert result.get("native_mipopt_count", 0) == 0
    physical_module.ROOT = ROOT
    physical = physical_module.physical(item["panel"],
        dict(result, inventory=result["verification"]["final_inventories"]))
    assert physical["original_T_feasible"]
    assert abs(physical["F"] - result["upper_bound"]) < 1e-7
    assert result["verification"]["original_solution_feasible"]
    assert result["verification"]["objective_matches"]
    trace = audit_primal_trace(item, dest, result)
    return dict(passed=True, physical_UB=physical["F"], original_T_feasible=True,
                expected_optimize_calls=0, observed_optimize_calls=0,
                decoded_paths=result["decoded_descent_seeds_completed"],
                **trace,
                result_sha256=common.sha(dest / "result.json"),
                physical=physical, process_wall_seconds=completion["process_wall_seconds"])


def offline_replay() -> None:
    """No-solver check of the very readers used by audit_one on retained D6."""
    item = launches(common.read(PREREG))[0]
    historical = Path("E:/codes/ExactEBRP-round87-runtime/campaign/local_raw/02_D6_ENS-C")
    witness = common.read(historical / "external/initial_witness.json")
    exact_result = common.read(historical / "result.json")
    physical_module.ROOT = ROOT
    physical = physical_module.physical(item["panel"], witness)
    assert physical["original_T_feasible"]
    assert abs(physical["F"] - exact_result["initial_heuristic_UB"]) < 1e-7
    trace = audit_primal_trace(item, historical, witness)
    assert trace["constructive_prefix"]["all_prefixes_independently_replayed"]
    assert trace["neutral_closure"]["passed"]
    assert abs(trace["neutral_closure"]["final"]["F"] - physical["F"]) < 1e-7
    report = dict(schema="round88-a1-startup-d6-offline-replay-v1", optimizer_calls=0,
                  historical_source=str(historical), historical_result_sha256=common.sha(historical / "result.json"),
                  historical_witness_sha256=common.sha(historical / "external/initial_witness.json"),
                  physical_F=physical["F"], original_T_feasible=physical["original_T_feasible"],
                  constructive_replay=True, closure_replay=True, prereg_sha256=common.sha(PREREG),
                  runner_sha256=common.sha(Path(__file__)))
    path = STAGE / f'screen_a1_startup_d6_offline_replay_{report["runner_sha256"][:12]}.json'
    if path.exists():
        assert common.read(path) == report
    else:
        common.write_new(path, report)
    print(json.dumps(dict(optimizer_calls=0, physical_F=physical["F"],
                          original_T_feasible=True, constructive_replay=True, closure_replay=True)), flush=True)


def run() -> None:
    prereg = common.read(PREREG)
    items = launches(prereg)
    identity = common.read(OUT / "identity.json")
    assert identity["schema"] == "round88-a1-startup-d6-identity-v1"
    assert identity["launches"] == items
    assert identity["prereg_sha256"] == common.sha(PREREG)
    assert identity["runner_sha256"] == common.sha(Path(__file__))
    assert identity["physical_reader_sha256"] == common.sha(Path(physical_module.__file__))
    assert identity["affinity_sha256"] == common.sha(ROOT / "scripts/round70_affinity.py")
    assert identity["normalizer_sha256"] == common.sha(ROOT / "scripts/round75_startup.py")
    assert identity["common_runner_sha256"] == common.sha(ROOT / "scripts/round88_a1_g3.py")
    assert identity["joint_reader_sha256"] == common.sha(ROOT / "scripts/round73_seed_diagnostic.py")
    assert identity["exchange_reader_sha256"] == common.sha(ROOT / "scripts/round83_audit_v2.py")
    assert identity["input_audit_sha256"] == common.sha(common.INPUT_AUDIT)
    lease = common.read(OUT / "runner_startup_lease.json")
    assert lease == dict(schema="round88-a1-startup-d6-lease-v1",
                         identity_sha256=common.sha(OUT / "identity.json"),
                         authorized_by="Astra", allow_startup_diagnostic=True)
    assert not (OUT / "active_run.lock").exists()
    assert not (OUT / "summary.jsonl").exists(), "Never rerun startup diagnostic"
    common.write_new(OUT / "active_run.lock", dict(pid=os.getpid(), started_unix=time.time()))
    records = []
    error = None
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    current_item = None
    attempt_started = None
    try:
        for item in items:
            current_item = item
            attempt_started = time.monotonic()
            admission_started = time.monotonic()
            assert not common.foreign_heavy_processes(), "another solver/build active"
            assert common.memory_available() >= 2 * 1024**3
            assert common.shutil.disk_usage(OUT).free >= 10 * 1024**3
            dest = Path(item["destination"])
            dest.mkdir(parents=True, exist_ok=False)
            prelaunch_seconds = time.monotonic() - admission_started
            common.write_new(dest / "launch.json", dict(item, prelaunch_seconds=prelaunch_seconds,
                identity_sha256=common.sha(OUT / "identity.json")))
            common.append_jsonl(OUT / "processes.jsonl", dict(item, started_unix=time.time()))
            started = time.monotonic()
            watchdog = False
            child = None
            with affinity.inherited_core(prereg["affinity_mask"]) as binding:
                try:
                    with (dest / "stdout.log").open("x") as stdout, (dest / "stderr.log").open("x") as stderr:
                        child = subprocess.Popen(item["command"], cwd=ROOT, env=environment,
                                                 stdout=stdout, stderr=stderr)
                        mask = affinity.read_masks(child.pid)
                        assert mask["process_mask"] == prereg["affinity_mask"]
                        common.write_new(dest / "affinity.json", dict(parent=binding, child=mask, pid=child.pid))
                        try:
                            child.wait(timeout=max(0.01, item["hard_stop_seconds"] - (time.monotonic() - started)))
                        except subprocess.TimeoutExpired:
                            watchdog = True
                            child.kill()
                            child.wait(timeout=5)
                        exit_observed_seconds = time.monotonic() - started
                finally:
                    if child is not None and child.poll() is None:
                        child.kill()
                        child.wait(timeout=5)
            wrapper_wall = time.monotonic() - started
            wall = exit_observed_seconds
            completion = dict(returncode=child.returncode, process_wall_seconds=wall,
                              prelaunch_seconds=prelaunch_seconds, end_to_end_seconds=prelaunch_seconds + wall,
                              wrapper_wall_seconds=wrapper_wall,
                              postexit_affinity_restore_seconds=wrapper_wall - wall,
                              fully_observed_end_to_end_seconds=prelaunch_seconds + wrapper_wall,
                              within_cap=wall <= item["process_cap_seconds"], watchdog=watchdog,
                              ended_unix=time.time())
            common.write_new(dest / "completion.json", completion)
            audit_started = time.perf_counter()
            try:
                assert not watchdog and child.returncode == 0 and completion["within_cap"]
                assert affinity.read_masks() == binding["before"]
                audit = audit_one(item, completion)
            except Exception as exc:
                audit = dict(passed=False, classification="unknown_or_evidence_failure",
                             error=repr(exc), optimize_calls_unverified=True)
            audit["offline_audit_seconds"] = time.perf_counter() - audit_started
            common.write_new(dest / "audit.json", audit)
            record = dict(number=item["number"], id=item["id"], arm=item["arm"],
                          destination=str(dest), completion=completion,
                          audit_passed=audit["passed"], physical_UB=audit.get("physical_UB"),
                          audit_error=audit.get("error"))
            records.append(record)
            common.append_jsonl(OUT / "summary.jsonl", record)
            print(json.dumps(dict(completed=record)), flush=True)
            if not audit["passed"]:
                raise RuntimeError("Startup diagnostic uncertain or invalid; preserve and stop")
            current_item = None
    except Exception as exc:
        error = repr(exc)
        if current_item is not None:
            already = []
            summary = OUT / "summary.jsonl"
            if summary.exists():
                already = [json.loads(line) for line in summary.read_text(encoding="utf-8").splitlines()]
            if not already or already[-1]["number"] != current_item["number"]:
                dest = Path(current_item["destination"])
                failure = dict(schema="round88-a1-startup-d6-failure-v1",
                               number=current_item["number"], arm=current_item["arm"],
                               destination=str(dest), destination_exists=dest.exists(),
                               total_attempt_elapsed_seconds=time.monotonic() - attempt_started,
                               error=error, optimize_calls_unverified=True, physical_UB=None,
                               recorded_unix=time.time())
                common.write_new(OUT / f'runner_failure_{current_item["number"]:02d}.json', failure)
                synthetic = dict(number=current_item["number"], id="D6", arm=current_item["arm"],
                                 destination=str(dest), completion=None, audit_passed=False,
                                 physical_UB=None, audit_error=error)
                records.append(synthetic)
                common.append_jsonl(summary, synthetic)
        raise
    finally:
        (OUT / "active_run.lock").unlink(missing_ok=True)
        failed_attempt_cost = sum(common.read(path)["total_attempt_elapsed_seconds"]
                                  for path in OUT.glob("runner_failure_*.json"))
        observed_process_wall = sum(r["completion"]["process_wall_seconds"]
                                    for r in records if r["completion"])
        common.write_new(OUT / "runner_startup_completion.json", dict(
            completed=len(records), planned=2, all_valid=len(records) == 2 and all(r["audit_passed"] for r in records),
            stop_reason=error, process_wall_seconds=observed_process_wall,
            failed_attempt_elapsed_lower_bound_seconds=failed_attempt_cost,
            process_wall_total_if_any_failed="unknown" if failed_attempt_cost else observed_process_wall,
            optimizer_calls=0 if len(records) == 2 and all(r["audit_passed"] for r in records) else None,
            ended_unix=time.time()))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"dry-run", "offline-replay", "prepare", "run"}, \
        "Usage: round88_startup_diagnostic.py dry-run|offline-replay|prepare|run"
    if sys.argv[1] == "dry-run":
        dry_run()
    elif sys.argv[1] == "offline-replay":
        offline_replay()
    elif sys.argv[1] == "prepare":
        prepare()
    else:
        run()


if __name__ == "__main__":
    main()
