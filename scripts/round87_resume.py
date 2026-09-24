"""Recover the quota-interrupted eighth arm, then continue only arms 9--18.

This is an operational continuation, not a change to the frozen protocol,
optimizer, original serial driver, or offline analyzer. Never replays an arm.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import round70_affinity as affinity
import round86_native_evidence as evidence
import round87_research as frozen
from round75_startup import normalize, route_hash
from round83_audit_v2 import audit as replay_exchange


ROOT = frozen.ROOT
OUT = frozen.OUT
EXPECTED_INTERRUPTED_COMMITS = 719974


def verified_context():
    protocol = frozen.read(frozen.PROTOCOL_PATH)
    frozen.source_history_check(protocol)
    identity = frozen.read(OUT / "identity.json")
    assert frozen.sha(frozen.PROTOCOL_PATH) == identity["protocol_sha256"]
    assert frozen.sha(frozen.PLAN_PATH) == identity["plan_sha256"]
    assert frozen.sha(frozen.__file__) == identity["driver_sha256"]
    assert frozen.sha(evidence.__file__) == identity["reader_sha256"]
    assert frozen.sha(evidence.physical_module.__file__) == identity["physical_reader_sha256"]
    assert frozen.sha(identity["binary_path"]) == identity["binary_sha256"] == protocol["binary_sha256"]
    assert frozen.sha(identity["reference_binary_path"]) == identity["reference_binary_sha256"]
    assert len(identity["launches"]) == 18
    raw_campaign = Path(identity["runtime_root"]) / "campaign"
    assert raw_campaign.is_dir()
    summary = frozen.read(OUT / "summary.json")
    assert frozen.read(raw_campaign / "summary.json") == summary
    for position, row in enumerate(summary["records"]):
        launch = identity["launches"][position]
        assert (row["number"], row["id"], row["arm"]) == (
            launch["number"], launch["panel"]["id"], launch["arm"])
        assert row["audit"]["passed"]
    return protocol, identity, raw_campaign, summary


def publish_summary(records, identity, raw_campaign):
    summary = dict(schema="round87-running-summary-v1", records=records,
                   total_wall_seconds=sum(row["wall_seconds"] for row in records),
                   offline_replay_seconds=sum(row["audit"]["offline_replay_seconds"] for row in records),
                   completed=len(records), planned=len(identity["launches"]),
                   completed_pairs=len(records) // 2, formal_performance=True)
    frozen.write(OUT / "summary.json", summary)
    frozen.write(raw_campaign / "summary.json", summary)
    return summary


def recover():
    protocol, identity, raw_campaign, summary = verified_context()
    assert summary["completed"] == len(summary["records"]) == 7
    launch = identity["launches"][7]
    assert (launch["number"], launch["panel"]["id"], launch["arm"]) == (8, "F2", "P-GRB")
    destination = Path(launch["destination"])
    assert frozen.read(destination / "launch.json") == launch
    assert not (destination / "result.json").exists()
    assert not (destination / "completion.json").exists()
    assert not (destination / "observations.json").exists()
    assert not (destination / "audit.json").exists()
    assert not (destination / "journal" / f"event_{EXPECTED_INTERRUPTED_COMMITS + 1}.commit").exists()
    tail = evidence.receipt(destination / "journal" / f"event_{EXPECTED_INTERRUPTED_COMMITS}.commit",
                            0, launch["cap"])
    conservative_available = tail["data_close_seconds"]
    assert conservative_available < launch["cap"]
    recovery_dir = raw_campaign / "quota_interruption_recovery"
    recovery_dir.mkdir(exist_ok=False)
    shutil.copy2(OUT / "summary.json", recovery_dir / "seven_run_summary.json")
    shutil.copy2(OUT / "runtime_status.json", recovery_dir / "last_original_runtime_status.json")
    status = frozen.read(OUT / "runtime_status.json")
    assert (status["number"], status["committed_events"]) == (8, 719869)
    assert status["process_seconds"] < conservative_available
    observations = []
    start = time.perf_counter()
    for sequence in range(1, EXPECTED_INTERRUPTED_COMMITS + 1):
        receipt = evidence.receipt(destination / "journal" / f"event_{sequence}.commit",
                                   conservative_available, launch["cap"])
        assert receipt["sequence"] == sequence
        observations.append(receipt)
        if sequence % 100000 == 0:
            print(json.dumps(dict(recovery_verified_commits=sequence)), flush=True)
    audited = evidence.audit(ROOT, launch["panel"], observations, identity["binary_sha256"])
    evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], audited,
                               observations, None, "quota_interrupted", identity["references"]["F2"])
    assert audited["committed_events"] == EXPECTED_INTERRUPTED_COMMITS
    assert audited["native_calls_started"] == 1
    assert audited["native_calls_returned"] == 0
    assert not audited["endpoint"]["certificate"]
    audited.update(passed=True, offline_replay_seconds=time.perf_counter() - start,
                   recovery_observation_policy="all committed receipts conservatively available at final receipt close")
    completion = dict(returncode=None, wall_seconds=conservative_available, within_cap=True,
                      stop_reason="quota_interrupted", restored=None,
                      observed_commits=len(observations), ended_unix=None,
                      recovered=True, wall_seconds_precision="last_committed_event_lower_bound_on_actual_exit")
    frozen.write(destination / "observations.json", observations)
    frozen.write(destination / "audit.json", audited)
    frozen.write(destination / "completion.json", completion)
    frozen.write(recovery_dir / "manifest.json", dict(
        schema="round87-quota-interruption-recovery-v1", original_completed=7,
        run_number=8, committed_events=len(observations),
        original_driver_observed_commits=status["committed_events"],
        last_original_driver_status_seconds=status["process_seconds"],
        last_commit_close_seconds=conservative_available,
        first_observed_seconds_semantics="conservative reconstruction upper bound, not actual original poll time",
        wall_seconds_semantics="last committed event time; actual process exit unknown and later",
        original_summary_sha256=frozen.sha(recovery_dir / "seven_run_summary.json"),
        original_runtime_status_sha256=frozen.sha(recovery_dir / "last_original_runtime_status.json"),
        physical_and_scope_audit_passed=True, optimality_certificate=False))
    record = dict(number=8, id="F2", arm="P-GRB", destination=str(destination),
                  **completion, audit=audited)
    publish_summary([*summary["records"], record], identity, raw_campaign)
    print(json.dumps(dict(recovered=8, endpoint=audited["endpoint"],
                          commits=len(observations), replay_seconds=audited["offline_replay_seconds"])), flush=True)


def run_remaining():
    protocol, identity, raw_campaign, summary = verified_context()
    assert summary["completed"] == len(summary["records"]) == 8
    assert summary["records"][7]["stop_reason"] == "quota_interrupted"
    assert summary["records"][7]["audit"]["passed"]
    assert not (OUT / "driver_completion.json").exists()
    assert not (raw_campaign / "driver_completion.json").exists()
    assert not Path(identity["launches"][8]["destination"]).exists()
    lock = raw_campaign / "resume_run.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    limits = protocol["limits"]
    records = list(summary["records"])
    driver_started = time.time()
    frozen.write(OUT / "continuation_freeze.json", dict(
        head=frozen.git("rev-parse", "HEAD"), started_unix=driver_started,
        identity_sha256=frozen.sha(OUT / "identity.json"),
        recovered_run=8, first_new_run=9, last_new_run=18))
    try:
        for launch in identity["launches"][8:]:
            assert launch["number"] == len(records) + 1
            free_disk = shutil.disk_usage(identity["runtime_root"]).free
            if free_disk < limits["minimum_free_bytes_before_launch"]:
                frozen.write(OUT / "resource_stop.json", dict(reason="insufficient_disk_before_launch",
                             free_bytes=free_disk, threshold=limits["minimum_free_bytes_before_launch"],
                             next_number=launch["number"], next_id=launch["panel"]["id"], next_arm=launch["arm"]))
                raise RuntimeError("Frozen disk admission boundary reached before next launch")
            destination = Path(launch["destination"])
            assert not destination.exists(), "Never restart or overwrite an arm"
            destination.mkdir(parents=True)
            started = time.monotonic()
            frozen.write(OUT / "active_experiment.json", dict(number=launch["number"], id=launch["panel"]["id"],
                         arm=launch["arm"], started_unix=time.time(), driver_pid=os.getpid(),
                         destination=str(destination), completed_runs=len(records), completed_pairs=len(records) // 2))
            frozen.write(destination / "launch.json", launch)
            with (raw_campaign / "processes.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(dict(launch, started_unix=time.time())) + "\n")
            observations = []
            reason = "normal_return"
            next_event = 1
            child = None
            last_status = 0.0
            last_console = 0.0
            low_memory_checks = 0
            with affinity.inherited_core() as binding:
                try:
                    with (destination / "stdout.log").open("w") as stdout, (destination / "stderr.log").open("w") as stderr:
                        child = subprocess.Popen(launch["command"], cwd=ROOT, env=environment,
                                                 stdout=stdout, stderr=stderr)
                        child_binding = affinity.read_masks(child.pid)
                        assert child_binding["process_mask"] == protocol["common"]["affinity_mask"]
                        frozen.write(destination / "affinity.json", dict(binding=binding, child=child_binding, pid=child.pid))
                        while True:
                            while True:
                                receipt_path = destination / "journal" / f"event_{next_event}.commit"
                                if not receipt_path.exists():
                                    break
                                try:
                                    receipt = evidence.receipt(receipt_path, 0, launch["cap"])
                                except (AssertionError, FileNotFoundError, UnicodeError, ValueError):
                                    break
                                observed = time.monotonic() - started
                                if observed > launch["cap"]:
                                    break
                                receipt["first_observed_seconds"] = observed
                                receipt["effective_available_seconds"] = max(observed, receipt["data_close_seconds"])
                                observations.append(receipt)
                                next_event += 1
                            elapsed = time.monotonic() - started
                            if child.poll() is not None:
                                break
                            if elapsed >= launch["hard_stop_seconds"]:
                                reason = "whole_run_hard_stop"
                                child.kill()
                                break
                            if elapsed - last_status >= 30:
                                memory = frozen.available_memory_bytes()
                                disk = shutil.disk_usage(identity["runtime_root"]).free
                                low_memory_checks = low_memory_checks + 1 if memory < limits["hard_memory_stop_available_bytes"] else 0
                                upper, lower = frozen.current_bounds(observations)
                                status = dict(number=launch["number"], id=launch["panel"]["id"], arm=launch["arm"],
                                    process_seconds=elapsed, latest_verified_UB=upper, latest_global_LB=lower,
                                    gap=upper - lower if upper is not None else None, committed_events=len(observations),
                                    completed_runs=len(records), completed_pairs=len(records) // 2,
                                    available_memory_bytes=memory, runtime_disk_free_bytes=disk, updated_unix=time.time())
                                frozen.write(OUT / "runtime_status.json", status)
                                frozen.write(raw_campaign / "runtime_status.json", status)
                                last_status = elapsed
                                if elapsed - last_console >= 1800:
                                    print(json.dumps(dict(progress=status)), flush=True)
                                    last_console = elapsed
                                if disk < limits["hard_disk_stop_free_bytes"]:
                                    reason = "host_disk_safety_stop"
                                    child.kill()
                                    break
                                if low_memory_checks >= 2:
                                    reason = "host_memory_safety_stop"
                                    child.kill()
                                    break
                            time.sleep(0.01)
                        child.wait(timeout=max(0.01, launch["cap"] - (time.monotonic() - started)))
                finally:
                    if child is not None and child.poll() is None:
                        child.kill()
                        child.wait(timeout=2)
            wall = time.monotonic() - started
            if reason == "normal_return" and child.returncode != 0:
                reason = "abnormal_process_exit"
            completion = dict(returncode=child.returncode, wall_seconds=wall, within_cap=wall <= launch["cap"],
                              stop_reason=reason, restored=affinity.read_masks(),
                              observed_commits=len(observations), ended_unix=time.time())
            frozen.write(destination / "completion.json", completion)
            frozen.write(destination / "observations.json", observations)
            audit_started = time.perf_counter()
            try:
                assert completion["within_cap"] and completion["restored"] == binding["before"]
                assert reason in {"normal_return", "whole_run_hard_stop", "host_disk_safety_stop", "host_memory_safety_stop"}
                result = frozen.read(destination / "result.json") if reason == "normal_return" else None
                audited = evidence.audit(ROOT, launch["panel"], observations, identity["binary_sha256"])
                evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], audited, observations,
                                           result, reason, identity["references"][launch["panel"]["id"]])
                if launch["arm"] == "ENS-C":
                    folder = destination / "hga.csv.exchange"
                    initial = normalize(frozen.read(folder / "initial.json"))
                    audited["neutral"] = replay_exchange(launch["panel"], folder, initial)
                    assert not frozen.read(folder / "result.json")["verification_failed"]
                    startup_events = [row["payload"] for row in observations
                                      if row["payload"]["kind"] == "witness" and row["payload"]["call"] == 0]
                    assert len(startup_events) == 1
                    handed = normalize(startup_events[0])
                    final = normalize(frozen.read(folder / "final.json"))
                    final_match = route_hash(handed) == route_hash(final)
                    initial_match = route_hash(handed) == route_hash(initial)
                    assert final_match or initial_match
                    if not final_match:
                        assert frozen.read(folder / "initial.json")["F"] - frozen.read(folder / "final.json")["F"] <= 1.0001e-10
                    audited["outer_handoff"] = dict(final_route_match=final_match, initial_route_match=initial_match)
                audited.update(passed=True, offline_replay_seconds=time.perf_counter() - audit_started)
            except Exception as exc:
                audited = dict(passed=False, error=repr(exc), offline_replay_seconds=time.perf_counter() - audit_started)
            frozen.write(destination / "audit.json", audited)
            record = dict(number=launch["number"], id=launch["panel"]["id"], arm=launch["arm"],
                          destination=str(destination), **completion, audit=audited)
            records.append(record)
            publish_summary(records, identity, raw_campaign)
            print(json.dumps(dict(completed=dict(number=launch["number"], id=launch["panel"]["id"],
                  arm=launch["arm"], wall_seconds=wall, reason=reason, passed=audited["passed"],
                  endpoint=audited.get("endpoint"), error=audited.get("error")))), flush=True)
            assert audited["passed"], "Stop after first correctness/evidence failure; no automatic rerun"
            if reason in {"host_disk_safety_stop", "host_memory_safety_stop"}:
                raise RuntimeError(f"Resource safety stop: {reason}")
            native_calls = sum(row["audit"].get("native_calls_started", 0) for row in records)
            assert native_calls <= limits["maximum_native_calls"]
    finally:
        if lock.exists():
            lock.unlink()
        completion = dict(completed=len(records), planned=len(identity["launches"]),
                          all_valid=len(records) == len(identity["launches"]) and all(row["audit"]["passed"] for row in records),
                          ended_unix=time.time(), elapsed_calendar_seconds=time.time() - driver_started,
                          continuation=True, recovered_quota_interruption_run=8)
        frozen.write(OUT / "driver_completion.json", completion)
        frozen.write(raw_campaign / "driver_completion.json", completion)


def wait_then_run_remaining():
    """Detached handoff; a failed recovery must never start another arm."""
    deadline = time.monotonic() + 12 * 3600
    while time.monotonic() < deadline:
        if (OUT / "summary.json").exists():
            summary = frozen.read(OUT / "summary.json")
            if summary["completed"] == 8:
                assert len(summary["records"]) == 8
                assert summary["records"][7]["audit"]["passed"]
                assert summary["records"][7]["stop_reason"] == "quota_interrupted"
                print(json.dumps(dict(recovery_handoff="audited_run_8", started_unix=time.time())), flush=True)
                run_remaining()
                return
            assert summary["completed"] == 7, "Unexpected campaign state during recovery"
        time.sleep(30)
    raise RuntimeError("Recovery did not finish in twelve hours; no remaining arm was started")


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in {"recover", "run_remaining", "wait_then_run_remaining"}
    if sys.argv[1] == "recover":
        recover()
    elif sys.argv[1] == "run_remaining":
        run_remaining()
    else:
        wait_then_run_remaining()
