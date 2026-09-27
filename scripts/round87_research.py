"""Frozen serial Round 87 ENS-C versus P-GRB long-certification driver."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import round70_affinity as affinity
import round86_native_evidence as evidence
from round75_startup import normalize, route_hash
from round83_audit_v2 import audit as replay_exchange


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "results/unified_exact_round87"
OUT = STAGE / "campaign"
PROTOCOL_PATH = STAGE / "protocol.json"
PLAN_PATH = STAGE / "plan.md"
BRANCH = "codex/round87-ensc-pgrb-long-convergence"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def runtime_root(protocol):
    return Path(os.environ.get("ROUND87_RUNTIME_ROOT", protocol["runtime_root_default"])).resolve()


def binary_paths(protocol):
    configured = os.environ.get("ROUND87_BINARY_DIR")
    if configured:
        directory = Path(configured).resolve()
        return directory / "ExactEBRP.exe", directory / "Round65ReferenceBuild.exe"
    return Path(protocol["binary_default_path"]), Path(protocol["reference_binary_default_path"])


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
        ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
        ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
        ("available_extended", ctypes.c_ulonglong),
    ]


def available_memory_bytes():
    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return status.available_physical


def source_history_check(protocol):
    assert git("branch", "--show-current") == BRANCH
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", protocol["research_base"], "HEAD"],
        cwd=ROOT,
    ).returncode == 0
    changed = git("diff", "--name-only", protocol["qualified_source"], "HEAD", "--", "src", "include", "CMakeLists.txt")
    assert not changed, f"Algorithm/model files differ from qualified source: {changed}"
    critical = git("status", "--porcelain", "--", "src", "include", "tests", "CMakeLists.txt",
                   "scripts/round87_research.py", "scripts/round87_analyze.py",
                   "results/unified_exact_round87/protocol.json",
                   "results/unified_exact_round87/plan.md",
                   "results/unified_exact_round87/reproduce.md")
    assert not critical, f"Commit frozen code/protocol first: {critical}"


def expanded_panel(protocol):
    common = protocol["common"]
    rows = []
    for panel in protocol["panel"]:
        row = dict(panel)
        row.update(lambda_=common["lambda"], pickup_seconds=common["pickup_seconds"],
                   drop_seconds=common["drop_seconds"])
        row["lambda"] = row.pop("lambda_")
        rows.append(row)
    return rows


def prepare():
    started = time.perf_counter()
    protocol = read(PROTOCOL_PATH)
    source_history_check(protocol)
    assert protocol["limits"]["planned_runs"] == len(protocol["execution_order"]) == 18
    binary, reference_binary = binary_paths(protocol)
    assert sha(binary) == protocol["binary_sha256"]
    assert sha(reference_binary) == protocol["reference_binary_sha256"]
    prior_identity_path = ROOT / "results/unified_exact_round86/campaign/identity.json"
    prior_identity = read(prior_identity_path)
    assert prior_identity["source_commit"] == protocol["qualified_source"]
    assert prior_identity["binary_sha256"] == protocol["binary_sha256"]
    assert prior_identity["reference_binary_sha256"] == protocol["reference_binary_sha256"]
    prior_qualification = ROOT / "results/unified_exact_round83/qualification_v1.json"
    qualification = read(prior_qualification)
    assert len(qualification["attempts"]) == 3
    assert all(attempt["returncode"] == 0 for attempt in qualification["attempts"])
    assert read(ROOT / "results/unified_exact_round83/qualification_v1_audit.json")["actual_optimize_calls"] == 165
    assert read(ROOT / "results/unified_exact_round83/native_integration_audit.json")["passed"]
    assert read(ROOT / "results/unified_exact_round86/campaign/driver_completion.json")["all_valid"]
    assert read(ROOT / "results/unified_exact_round86/campaign/audit.json")["all_checks_passed"]
    assert not OUT.exists(), "Round 87 preparation already exists; never replace it"
    raw = runtime_root(protocol)
    assert not raw.exists(), f"Runtime root already exists: {raw}"
    raw.mkdir(parents=True)
    OUT.mkdir(parents=True)
    panel = expanded_panel(protocol)
    by_id = {item["id"]: item for item in panel}
    for item in panel:
        assert len(item["complete_Q_vector"]) == item["M"]
        assert all(q == item["Q"] for q in item["complete_Q_vector"])
        assert sha(ROOT / item["instance_path"]) == item["input_sha256"], item["id"]
    declared = [f'{item["id"]}/{arm}' for item in panel for arm in item["method_order"]]
    assert declared == protocol["execution_order"]
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    references = {}
    reference_wall = 0.0
    for item in panel:
        destination = raw / "reference" / item["id"]
        destination.mkdir(parents=True)
        command = list(map(str, [reference_binary, item["instance_path"], item["T_seconds"],
                                  item["pickup_seconds"], item["drop_seconds"], item["lambda"], destination]))
        start = time.monotonic()
        with (destination / "stdout.log").open("w") as stdout, (destination / "stderr.log").open("w") as stderr:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, timeout=60)
        elapsed = time.monotonic() - start
        reference_wall += elapsed
        assert result.returncode == 0
        reference = read(destination / "build.json")
        assert reference["optimizer_calls"] == 0
        references[item["id"]] = reference
        write(destination / "launch.json", dict(command=command, input=item,
              binary_sha256=sha(reference_binary), expected_optimize_calls=0))
        write(destination / "completion.json", dict(returncode=result.returncode, wall_seconds=elapsed))
    launches = []
    limits = protocol["limits"]
    common = protocol["common"]
    for number, declared_run in enumerate(protocol["execution_order"], 1):
        identity, arm = declared_run.split("/")
        item = by_id[identity]
        destination = raw / "campaign" / "local_raw" / f'{number:02d}_{identity}_{arm}'
        command = [binary, "--input", item["instance_path"], "--lambda", item["lambda"],
                   "--T", item["T_seconds"], "--pickup-time", item["pickup_seconds"],
                   "--drop-time", item["drop_seconds"], "--time-limit", limits["native_time_limit_seconds"],
                   "--process-wall-time-limit", limits["per_run_process_wall_seconds"],
                   "--process-shutdown-margin", limits["shutdown_margin_seconds"],
                   "--threads", common["threads"], "--mip-threads", common["mip_threads"],
                   "--gurobi-seed", common["gurobi_seed"], "--gurobi-presolve", common["gurobi_presolve"],
                   "--method", "gurobi" if arm == "P-GRB" else "gcap-frontier",
                   "--round61-candidate-mode", "off", "--out", destination / "result.json",
                   "--log", destination / "native.log", "--process-phase-ledger", destination / "phases.csv",
                   "--external-gini-artifact-dir", destination / "external",
                   "--primal-heuristic-generation-log", destination / "hga.csv",
                   "--progress-log", destination / "progress.csv", "--native-evidence-dir", destination / "journal"]
        if arm == "P-GRB":
            command += ["--plain-baseline", "--gurobi-model-export", destination / "compact.lp",
                        "--round24-expected-gurobi-model-fingerprint", references[identity]["fingerprint"],
                        "--round24-executable-sha256", protocol["binary_sha256"],
                        "--round24-manifest-executable-sha256", protocol["binary_sha256"]]
        else:
            command += ["--algorithm-preset", protocol["ens_preset"],
                        "--round65-witness-audit", "true", "--round65-hga-zero-stop", "true"]
        launches.append(dict(number=number, panel=item, arm=arm, command=list(map(str, command)),
                             destination=str(destination), cap=limits["per_run_process_wall_seconds"],
                             hard_stop_seconds=limits["external_hard_stop_seconds"]))
    identity = dict(
        schema="round87-campaign-identity-v1", research_base=protocol["research_base"],
        preparation_head=git("rev-parse", "HEAD"), qualified_source=protocol["qualified_source"],
        binary_path=str(binary.resolve()), binary_sha256=sha(binary),
        reference_binary_path=str(reference_binary.resolve()), reference_binary_sha256=sha(reference_binary),
        protocol_sha256=sha(PROTOCOL_PATH), plan_sha256=sha(PLAN_PATH), driver_sha256=sha(__file__),
        reader_path=str(Path(evidence.__file__).relative_to(ROOT)), reader_sha256=sha(evidence.__file__),
        physical_reader_sha256=sha(evidence.physical_module.__file__),
        exchange_replay_sha256=sha(ROOT / "scripts/round83_audit_v2.py"),
        inherited_round86_identity_sha256=sha(prior_identity_path),
        inherited_qualification_sha256=sha(prior_qualification),
        inherited_qualification_tests=62, inherited_qualification_native_calls=165,
        new_builds=0, new_tests=0, new_native_fixture_calls=0,
        runtime_root=str(raw), references=references, launches=launches,
        maximum_process_seconds=limits["maximum_process_seconds"], formal_performance=True,
    )
    write(OUT / "identity.json", identity)
    write(raw / "campaign_identity.json", identity)
    preflight = dict(
        schema="round87-preflight-v1", passed=True, optimizer_calls=0, reference_exports=len(panel),
        reference_wall_seconds=reference_wall, wall_seconds=time.perf_counter() - started,
        source_diff_from_qualified_commit=False, binary_reused=True,
        input_hashes_verified=len(panel), panel_pairs=len(panel), planned_runs=len(launches),
        available_memory_bytes=available_memory_bytes(), runtime_disk_free_bytes=shutil.disk_usage(raw).free,
        note="Inherited qualification was hash-checked, not rerun or recharged.",
    )
    write(STAGE / "preflight.json", preflight)
    print(json.dumps(preflight, indent=2), flush=True)


def current_bounds(observations):
    payloads = [record["payload"] for record in observations]
    uppers = [row["objective"] for row in payloads if row["kind"] == "witness"]
    lowers = [row["global_bound"] for row in payloads if row["kind"] == "bound" and row["global_available"]]
    upper = min(uppers) if uppers else None
    lower = max([0.0, *lowers])
    return upper, lower


def run():
    protocol = read(PROTOCOL_PATH)
    source_history_check(protocol)
    identity = read(OUT / "identity.json")
    assert sha(PROTOCOL_PATH) == identity["protocol_sha256"]
    assert sha(PLAN_PATH) == identity["plan_sha256"]
    assert sha(__file__) == identity["driver_sha256"]
    assert sha(evidence.__file__) == identity["reader_sha256"]
    assert sha(evidence.physical_module.__file__) == identity["physical_reader_sha256"]
    assert sha(identity["binary_path"]) == identity["binary_sha256"] == protocol["binary_sha256"]
    assert sha(identity["reference_binary_path"]) == identity["reference_binary_sha256"]
    critical = git("status", "--porcelain", "--", "src", "include", "tests", "CMakeLists.txt",
                   "scripts/round87_research.py", "scripts/round87_analyze.py",
                   "results/unified_exact_round87/protocol.json", "results/unified_exact_round87/plan.md",
                   "results/unified_exact_round87/reproduce.md", "results/unified_exact_round87/campaign/identity.json",
                   "results/unified_exact_round87/preflight.json")
    assert not critical, f"Commit the complete prelaunch freeze first: {critical}"
    raw = Path(identity["runtime_root"])
    raw_campaign = raw / "campaign"
    assert not raw_campaign.exists(), "Never repeat or overwrite a formal Round 87 campaign"
    raw_campaign.mkdir()
    lock = raw_campaign / "active_run.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    limits = protocol["limits"]
    records = []
    driver_started = time.time()
    write(OUT / "launch_freeze.json", dict(
        head=git("rev-parse", "HEAD"), branch=BRANCH, started_unix=driver_started,
        identity_sha256=sha(OUT / "identity.json"), runtime_root=str(raw),
        execution_order=protocol["execution_order"],
    ))
    try:
        for launch in identity["launches"]:
            free_disk = shutil.disk_usage(raw).free
            if free_disk < limits["minimum_free_bytes_before_launch"]:
                write(OUT / "resource_stop.json", dict(reason="insufficient_disk_before_launch",
                      free_bytes=free_disk, threshold=limits["minimum_free_bytes_before_launch"],
                      next_number=launch["number"], next_id=launch["panel"]["id"], next_arm=launch["arm"]))
                raise RuntimeError("Frozen disk admission boundary reached before next launch")
            started = time.monotonic()
            destination = Path(launch["destination"])
            destination.mkdir(parents=True)
            write(OUT / "active_experiment.json", dict(number=launch["number"], id=launch["panel"]["id"],
                  arm=launch["arm"], started_unix=time.time(), driver_pid=os.getpid(),
                  destination=str(destination), completed_runs=len(records), completed_pairs=len(records) // 2))
            write(destination / "launch.json", launch)
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
                        child = subprocess.Popen(launch["command"], cwd=ROOT, env=environment, stdout=stdout, stderr=stderr)
                        child_binding = affinity.read_masks(child.pid)
                        assert child_binding["process_mask"] == protocol["common"]["affinity_mask"]
                        write(destination / "affinity.json", dict(binding=binding, child=child_binding, pid=child.pid))
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
                                memory = available_memory_bytes()
                                disk = shutil.disk_usage(raw).free
                                low_memory_checks = low_memory_checks + 1 if memory < limits["hard_memory_stop_available_bytes"] else 0
                                upper, lower = current_bounds(observations)
                                status = dict(number=launch["number"], id=launch["panel"]["id"], arm=launch["arm"],
                                    process_seconds=elapsed, latest_verified_UB=upper, latest_global_LB=lower,
                                    gap=upper - lower if upper is not None else None, committed_events=len(observations),
                                    completed_runs=len(records), completed_pairs=len(records) // 2,
                                    available_memory_bytes=memory, runtime_disk_free_bytes=disk, updated_unix=time.time())
                                write(OUT / "runtime_status.json", status)
                                write(raw_campaign / "runtime_status.json", status)
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
            write(destination / "completion.json", completion)
            write(destination / "observations.json", observations)
            audit_started = time.perf_counter()
            try:
                assert completion["within_cap"] and completion["restored"] == binding["before"]
                assert reason in {"normal_return", "whole_run_hard_stop", "host_disk_safety_stop", "host_memory_safety_stop"}
                result = read(destination / "result.json") if reason == "normal_return" else None
                audited = evidence.audit(ROOT, launch["panel"], observations, identity["binary_sha256"])
                evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], audited, observations,
                                           result, reason, identity["references"][launch["panel"]["id"]])
                if launch["arm"] == "ENS-C":
                    folder = destination / "hga.csv.exchange"
                    initial = normalize(read(folder / "initial.json"))
                    audited["neutral"] = replay_exchange(launch["panel"], folder, initial)
                    assert not read(folder / "result.json")["verification_failed"]
                    startup_events = [row["payload"] for row in observations
                                      if row["payload"]["kind"] == "witness" and row["payload"]["call"] == 0]
                    assert len(startup_events) == 1
                    handed = normalize(startup_events[0])
                    final = normalize(read(folder / "final.json"))
                    final_match = route_hash(handed) == route_hash(final)
                    initial_match = route_hash(handed) == route_hash(initial)
                    assert final_match or initial_match
                    if not final_match:
                        assert read(folder / "initial.json")["F"] - read(folder / "final.json")["F"] <= 1.0001e-10
                    audited["outer_handoff"] = dict(final_route_match=final_match, initial_route_match=initial_match)
                audited.update(passed=True, offline_replay_seconds=time.perf_counter() - audit_started)
            except Exception as exc:
                audited = dict(passed=False, error=repr(exc), offline_replay_seconds=time.perf_counter() - audit_started)
            write(destination / "audit.json", audited)
            record = dict(number=launch["number"], id=launch["panel"]["id"], arm=launch["arm"],
                          destination=str(destination), **completion, audit=audited)
            records.append(record)
            summary = dict(schema="round87-running-summary-v1", records=records,
                           total_wall_seconds=sum(row["wall_seconds"] for row in records),
                           offline_replay_seconds=sum(row["audit"]["offline_replay_seconds"] for row in records),
                           completed=len(records), planned=len(identity["launches"]),
                           completed_pairs=len(records) // 2, formal_performance=True)
            write(OUT / "summary.json", summary)
            write(raw_campaign / "summary.json", summary)
            print(json.dumps(dict(completed=dict(number=launch["number"], id=launch["panel"]["id"],
                  arm=launch["arm"], wall_seconds=wall, reason=reason, passed=audited["passed"],
                  endpoint=audited.get("endpoint"), error=audited.get("error")))), flush=True)
            assert audited["passed"], "Stop after first correctness/evidence failure; no automatic rerun"
            native_calls = sum(row["audit"].get("native_calls_started", 0) for row in records)
            assert native_calls <= limits["maximum_native_calls"], "Frozen campaign native-call ceiling reached"
    finally:
        if lock.exists():
            lock.unlink()
        completion = dict(completed=len(records), planned=len(identity["launches"]),
                          all_valid=len(records) == len(identity["launches"]) and all(row["audit"]["passed"] for row in records),
                          ended_unix=time.time(), elapsed_calendar_seconds=time.time() - driver_started)
        write(OUT / "driver_completion.json", completion)
        write(raw_campaign / "driver_completion.json", completion)


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, "Use: round87_research.py prepare|run"
    prepare() if sys.argv[1] == "prepare" else run()


if __name__ == "__main__":
    main()
