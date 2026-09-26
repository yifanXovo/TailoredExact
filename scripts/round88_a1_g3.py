"""Frozen, serial Round 88 A1 G3 screen. Importing this module never solves.

Commands: dry-run | prepare | run-smoke | run-rest.  A run additionally needs
an identity-bound, stage-specific lease file supplied after coordinator review.
"""

from __future__ import annotations

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
STAGE = ROOT / "results/unified_exact_round88"
PREREG = STAGE / "preregistration_a1_g3.json"
CAMPAIGN = STAGE / "runner_a1_g3"
SOURCE_HASHES = STAGE / "qualification/a1_source_hashes.json"
INPUT_AUDIT = STAGE / "input_identity_audit.json"


def read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def append_jsonl(path: Path, value: object) -> None:
    with path.open("a", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()


def atomic_status(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    os.replace(temporary, path)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def memory_available() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
            ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
            ("available_extended", ctypes.c_ulonglong),
        ]
    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(status.available_physical)


def ensure_static_identity(prereg: dict, *, require_frozen_head: bool) -> None:
    assert os.name == "nt", "Windows-only native benchmark"
    assert prereg["schema"] == "round88-a1-g3-preregistration-v1"
    assert prereg["planned_runs"] == 24 and len(prereg["panel"]) == 8
    assert prereg["execution_order"] == [
        f'{item["id"]}/{arm}' for item in prereg["panel"] for arm in item["method_order"]
    ]
    assert prereg["maximum_process_wall_seconds"] == 18720
    assert prereg["no_component_time_or_work_slices"] is True
    assert [p["id"] for p in prereg["panel"]] == ["E8", "S12", "D3", "C2", "D7", "U6", "F5", "F6"]
    assert prereg["stages"][0]["ids"] == ["E8", "S12"]
    assert prereg["stages"][1]["ids"] == ["D3", "C2", "D7", "U6", "F5", "F6"]
    assert set(prereg["common"].items()) >= {
        ("threads", 1), ("mip_threads", 1), ("gurobi_seed", 0),
        ("gurobi_presolve", -1), ("affinity_mask", 4),
        ("requested_mip_gap", 0), ("requested_mip_gap_abs", 0),
    }
    if require_frozen_head:
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", prereg["source_commit"], "HEAD"],
            cwd=ROOT, check=False,
        ).returncode == 0, "A1 frozen source commit is not an ancestor"
    candidate = ROOT / prereg["candidate_binary"]
    assert sha(candidate) == prereg["candidate_binary_sha256"], "candidate binary changed"
    assert sha(Path(prereg["historical_frozen_binary"])) == prereg["historical_frozen_binary_sha256"]
    for row in read(SOURCE_HASHES):
        assert sha(ROOT / row["path"]) == row["sha256"], f'source byte drift: {row["path"]}'
    input_audit = read(INPUT_AUDIT)
    assert input_audit["role_count"] == 19 and input_audit["all_hashes_match"]
    audited = {row["id"]: row for row in input_audit["roles"]}
    for item in prereg["panel"]:
        assert set(item["method_order"]) == {"P-GRB", "ENS-C", "A1"}
        assert sha(ROOT / item["input_path"]) == item["input_sha256"]
        old = audited[item["id"]]
        assert old["passed"] and old["actual_sha256"] == item["input_sha256"]
        for key in ("scenario_id", "T_seconds", "lambda", "pickup_seconds", "drop_seconds"):
            assert item[key] == old[key], (item["id"], key)
        source_identity_path = ROOT / f'results/unified_exact_round{item["reference"]["source_round"]}/campaign/identity.json'
        old_reference = read(source_identity_path)["references"][item["id"]]
        for key in ("fingerprint", "canonical_sha256"):
            assert item["reference"][key] == old_reference[key], (item["id"], key)
        assert item["cap_seconds"] in {120, 600, 1200}


def command_for(prereg: dict, item: dict, arm: str, destination: Path) -> list[str]:
    cap = item["cap_seconds"]
    binary = str((ROOT / prereg["candidate_binary"]).resolve())
    common = prereg["common"]
    command = [
        binary, "--input", item["input_path"], "--lambda", str(item["lambda"]),
        "--T", str(item["T_seconds"]), "--pickup-time", str(item["pickup_seconds"]),
        "--drop-time", str(item["drop_seconds"]),
        "--time-limit", str(cap - common["native_limit_offset_seconds"]),
        "--process-wall-time-limit", str(cap),
        "--process-shutdown-margin", str(common["shutdown_margin_seconds"]),
        "--threads", "1", "--mip-threads", "1", "--gurobi-seed", "0",
        "--gurobi-presolve", "-1", "--method", "gurobi" if arm == "P-GRB" else "gcap-frontier",
        "--round61-candidate-mode", "off", "--out", str(destination / "result.json"),
        "--log", str(destination / "native.log"),
        "--process-phase-ledger", str(destination / "phases.csv"),
        "--external-gini-artifact-dir", str(destination / "external"),
        "--primal-heuristic-generation-log", str(destination / "hga.csv"),
        "--progress-log", str(destination / "progress.csv"),
        "--native-evidence-dir", str(destination / "journal"),
    ]
    if arm == "P-GRB":
        command += [
            "--plain-baseline", "--gurobi-model-export", str(destination / "compact.lp"),
            "--round24-expected-gurobi-model-fingerprint", str(item["reference"]["fingerprint"]),
            "--round24-executable-sha256", prereg["candidate_binary_sha256"],
            "--round24-manifest-executable-sha256", prereg["candidate_binary_sha256"],
        ]
    else:
        command += [
            "--algorithm-preset", "research-round83-vds-equal-net-exchange",
            "--round65-witness-audit", "true", "--round65-hga-zero-stop", "true",
        ]
        if arm == "A1":
            command += ["--round88-constructive-only-descent", "true"]
    return command


def build_launches(prereg: dict) -> list[dict]:
    launches = []
    for item in prereg["panel"]:
        audit_panel = dict(item, instance_path=item["input_path"])
        for arm in item["method_order"]:
            number = len(launches) + 1
            destination = CAMPAIGN / "raw" / f'{number:02d}_{item["id"]}_{arm}'
            launches.append(dict(
                number=number, id=item["id"], arm=arm, stage="smoke" if number <= 6 else "rest",
                panel=audit_panel, destination=str(destination), cap_seconds=item["cap_seconds"],
                hard_stop_seconds=item["cap_seconds"] - prereg["common"]["hard_stop_offset_seconds"],
                command=command_for(prereg, item, arm, destination),
            ))
    assert len(launches) == 24 and sum(row["cap_seconds"] for row in launches) == 18720
    return launches


def dry_run() -> None:
    prereg = read(PREREG)
    ensure_static_identity(prereg, require_frozen_head=False)
    launches = build_launches(prereg)
    assert all(Path(row["destination"]).is_relative_to(CAMPAIGN) for row in launches)
    assert all("--round88-constructive-only-descent" not in row["command"] for row in launches if row["arm"] != "A1")
    assert all("--round88-constructive-only-descent" in row["command"] for row in launches if row["arm"] == "A1")
    assert all("--plain-baseline" in row["command"] for row in launches if row["arm"] == "P-GRB")
    assert all("--plain-baseline" not in row["command"] for row in launches if row["arm"] != "P-GRB")
    report = dict(schema="round88-a1-g3-dryrun-v1", optimizer_calls=0, processes_started=0,
                  candidate_binary_sha256=prereg["candidate_binary_sha256"], planned_runs=len(launches),
                  smoke_runs=sum(row["stage"] == "smoke" for row in launches),
                  maximum_process_wall_seconds=sum(row["cap_seconds"] for row in launches),
                  prereg_sha256=sha(PREREG), runner_sha256=sha(Path(__file__)),
                  launch_commands=launches)
    destination = STAGE / f'screen_a1_g3_dryrun_{report["runner_sha256"][:12]}.json'
    if destination.exists():
        assert read(destination) == report, "dry-run bytes/identity changed; review existing report"
    else:
        write_new(destination, report)
    print(json.dumps({key: report[key] for key in ("optimizer_calls", "processes_started", "planned_runs", "smoke_runs", "maximum_process_wall_seconds")}), flush=True)


def prepare() -> None:
    prereg = read(PREREG)
    ensure_static_identity(prereg, require_frozen_head=True)
    assert not CAMPAIGN.exists(), "Never replace prepared or running Round 88 campaign"
    launches = build_launches(prereg)
    CAMPAIGN.mkdir()
    identity = dict(schema="round88-a1-g3-identity-v1", prereg_sha256=sha(PREREG),
                    runner_sha256=sha(Path(__file__)), source_commit=prereg["source_commit"],
                    preparation_head=git("rev-parse", "HEAD"), candidate_binary_sha256=prereg["candidate_binary_sha256"],
                    reader_sha256=sha(Path(evidence.__file__)),
                    physical_reader_sha256=sha(Path(evidence.physical_module.__file__)),
                    exchange_reader_sha256=sha(ROOT / "scripts/round83_audit_v2.py"),
                    affinity_sha256=sha(ROOT / "scripts/round70_affinity.py"),
                    normalizer_sha256=sha(ROOT / "scripts/round75_startup.py"),
                    input_audit_sha256=sha(INPUT_AUDIT), source_hashes_sha256=sha(SOURCE_HASHES),
                    launches=launches, prepared_unix=time.time(), optimizer_calls=0)
    write_new(CAMPAIGN / "identity.json", identity)
    write_new(CAMPAIGN / "preflight.json", dict(
        schema="round88-a1-g3-preflight-v1", optimizer_calls=0, input_hashes_verified=8,
        reference_fingerprints_inherited=8, binary_hash_verified=True, source_hashes_verified=True,
        planned_runs=24, process_cap_sum_seconds=18720,
        memory_available_bytes=memory_available(), disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        note="No model export or Optimize. Historical reference fingerprints are development controls.",
    ))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def foreign_heavy_processes() -> list[dict]:
    """Host admission guard; read only and fail closed if enumeration fails."""
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|Round[0-9]+.*Experiment|Round65ReferenceBuild|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'round88[_-]ot|ot[_-]diagnostic|ot[_-]root') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    raw = subprocess.check_output(["powershell.exe", "-NoProfile", "-Command", expression], text=True, timeout=30).strip()
    if not raw:
        return []
    payload = json.loads(raw)
    return payload if isinstance(payload, list) else [payload]


def require_lease(stage: str, identity: dict) -> dict:
    path = CAMPAIGN / f"runner_{stage}_lease.json"
    lease = read(path)
    assert lease == dict(schema="round88-a1-g3-lease-v1", stage=stage,
                         identity_sha256=sha(CAMPAIGN / "identity.json"),
                         authorized_by="Astra", allow_optimize=True), "Missing or changed stage-specific Astra lease"
    return lease


def bound_preview(observations: list[dict]) -> tuple[float | None, float]:
    payloads = [row["payload"] for row in observations]
    upper = min((row["objective"] for row in payloads if row["kind"] == "witness"), default=None)
    lower = max([0.0, *(row["global_bound"] for row in payloads
                         if row["kind"] == "bound" and row["global_available"])])
    return upper, lower


def audit_launch(launch: dict, observations: list[dict], completion: dict, identity: dict) -> dict:
    """Offline audit after the process is closed; never an optimizer call."""
    destination = Path(launch["destination"])
    reason = completion["stop_reason"]
    result_path = destination / "result.json"
    result = read(result_path) if reason == "normal_return" and result_path.is_file() else None
    if reason == "normal_return" and result is None:
        raise AssertionError("normal exit without result.json")
    if launch["arm"] == "P-GRB":
        compact = destination / "compact.lp"
        assert compact.is_file(), "missing original compact export"
        assert sha(compact) == launch["panel"]["reference"]["canonical_sha256"], \
            "P-GRB canonical LP bytes differ from frozen original compact export"
    audited = evidence.audit(ROOT, launch["panel"], observations, identity["candidate_binary_sha256"])
    evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], audited,
                               observations, result, reason, launch["panel"]["reference"])
    if result is not None:
        expected = {"P-GRB": "custom", "ENS-C": "research-round83-vds-equal-net-exchange",
                    "A1": "research-round88-ensc-constructive-only"}[launch["arm"]]
        assert result["algorithm_preset"] == expected, (launch["id"], launch["arm"], result["algorithm_preset"])
    if result is not None and launch["arm"] != "P-GRB":
        folder = destination / "hga.csv.exchange"
        if folder.is_dir():
            initial = normalize(read(folder / "initial.json"))
            audited["neutral_exchange"] = replay_exchange(launch["panel"], folder, initial)
            assert not read(folder / "result.json")["verification_failed"]
            final = normalize(read(folder / "final.json"))
            startup = [row["payload"] for row in observations
                       if row["payload"]["kind"] == "witness" and row["payload"]["call"] == 0]
            assert len(startup) == 1
            handed = normalize(startup[0])
            assert route_hash(handed) in {route_hash(initial), route_hash(final)}
            audited["outer_handoff"] = dict(initial_match=route_hash(handed) == route_hash(initial),
                                            final_match=route_hash(handed) == route_hash(final))
        else:
            assert not result.get("external_gini_tree_root_coverage_valid"), "missing exchange artifact"
    audited["passed"] = True
    return audited


def severe_risk_signal(records: list[dict], role: str) -> list[dict]:
    """Offline research alarm after a complete triple; never an algorithm rule."""
    same = {row["arm"]: row for row in records if row["id"] == role}
    assert set(same) == {"P-GRB", "ENS-C", "A1"}
    candidate = same["A1"]
    found = []
    for reference_arm in ("ENS-C", "P-GRB"):
        reference = same[reference_arm]
        cand_end = candidate["endpoint"]
        ref_end = reference["endpoint"]
        if cand_end is None or ref_end is None:
            continue  # Audit anomaly is handled separately before this point.
        cand_cert = cand_end["certificate"]
        ref_cert = ref_end["certificate"]
        ref_time = reference["completion"]["process_wall_seconds"]
        cand_time = candidate["completion"]["process_wall_seconds"]
        small = role in {"E8", "S12"} and cand_cert and ref_cert and max(cand_time, ref_time) < 60
        excess_ratio, excess_seconds = (0.5, 5) if small else (0.5, 30)
        if cand_cert and ref_cert and cand_time > ref_time * (1 + excess_ratio) and cand_time - ref_time > excess_seconds:
            found.append(dict(role=role, reference=reference_arm, kind="severe_certification_time_signal",
                              candidate_seconds=cand_time, reference_seconds=ref_time))
        elif ref_cert and not cand_cert and cand_time > ref_time * (1 + excess_ratio) and cand_time - ref_time > excess_seconds:
            found.append(dict(role=role, reference=reference_arm, kind="certificate_loss_with_severe_censoring_lower_bound",
                              candidate_observed_seconds=cand_time, reference_certified_seconds=ref_time))
        elif not cand_cert and not ref_cert:
            cand_gap, ref_gap = cand_end["gap"], ref_end["gap"]
            if (cand_gap is not None and ref_gap is not None and cand_gap > ref_gap * 1.5
                    and cand_gap - ref_gap > 0.01):
                found.append(dict(role=role, reference=reference_arm, kind="severe_open_gap_signal",
                                  candidate_gap=cand_gap, reference_gap=ref_gap,
                                  candidate_U=cand_end["U"], candidate_L=cand_end["L"],
                                  reference_U=ref_end["U"], reference_L=ref_end["L"]))
    return found


def cross_arm_contradiction_check(records: list[dict], role: str) -> dict:
    """Offline comparison only; never combines bounds into an arm endpoint."""
    same = {row["arm"]: row for row in records if row["id"] == role}
    assert set(same) == {"P-GRB", "ENS-C", "A1"}
    arms = []
    lowers, uppers = [], []
    for arm in ("P-GRB", "ENS-C", "A1"):
        row = same[arm]
        audit = read(Path(row["destination"]) / "audit.json")
        assert audit["passed"]
        all_l = [audit["LB"]]
        if row["endpoint"] is not None and row["endpoint"]["L"] is not None:
            all_l.append(row["endpoint"]["L"])
        all_u = [w["F"] for w in audit["witnesses"]]
        final = audit.get("final_physical_verification")
        if final is not None:
            all_u.append(final["F"])
        maximum_l = max(all_l)
        minimum_u = min(all_u) if all_u else None
        lowers.append(maximum_l)
        if minimum_u is not None:
            uppers.append(minimum_u)
        arms.append(dict(arm=arm, strongest_same_arm_global_L=maximum_l,
                         minimum_same_arm_physical_U=minimum_u,
                         physically_verified_witness_rows=len(audit["witnesses"]),
                         final_physical_verification_present=final is not None))
    strongest = max(lowers)
    weakest_upper = min(uppers) if uppers else None
    passed = weakest_upper is None or strongest <= weakest_upper + 1e-7
    report = dict(schema="round88-a1-g3-cross-arm-v1", id=role, arms=arms,
                  strongest_global_L=strongest, minimum_physical_U=weakest_upper,
                  tolerance=1e-7, passed=passed,
                  scope="Offline original-problem contradiction check, not a combined algorithm endpoint")
    write_new(CAMPAIGN / f'runner_cross_arm_{role}.json', report)
    assert passed, f"Cross-arm original-problem bound contradiction on {role}"
    return report


def run_one(launch: dict, prereg: dict, identity: dict) -> dict:
    admission_started = time.monotonic()
    competing = foreign_heavy_processes()
    assert not competing, f"other solver/build process active: {competing}"
    free = shutil.disk_usage(CAMPAIGN).free
    available = memory_available()
    assert free >= 10 * 1024**3 and available >= 2 * 1024**3, "resource admission failed"
    destination = Path(launch["destination"])
    destination.mkdir(parents=True, exist_ok=False)
    prelaunch_seconds = time.monotonic() - admission_started
    write_new(destination / "launch.json", dict(launch, prelaunch_seconds=prelaunch_seconds,
                                                 prereg_sha256=identity["prereg_sha256"],
                                                 runner_sha256=identity["runner_sha256"]))
    append_jsonl(CAMPAIGN / "processes.jsonl", dict(number=launch["number"], id=launch["id"],
              arm=launch["arm"], destination=str(destination), started_unix=time.time()))
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    observations: list[dict] = []
    next_event = 1
    reason = "normal_return"
    child = None
    last_sample = -60.0
    low_memory_checks = 0
    started = time.monotonic()
    write_new(destination / "process_start_marker.json", dict(
        monotonic_seconds=started, unix_seconds=time.time(),
        scope="wrapper start before affinity and child creation; not a certificate time"))
    with affinity.inherited_core(prereg["common"]["affinity_mask"]) as binding:
        try:
            with (destination / "stdout.log").open("x") as stdout, (destination / "stderr.log").open("x") as stderr:
                child = subprocess.Popen(launch["command"], cwd=ROOT, env=environment, stdout=stdout, stderr=stderr)
                mask = affinity.read_masks(child.pid)
                assert mask["process_mask"] == prereg["common"]["affinity_mask"]
                write_new(destination / "affinity.json", dict(parent=binding, child=mask, pid=child.pid))
                while True:
                    for _ in range(256):
                        path = destination / "journal" / f"event_{next_event}.commit"
                        if not path.exists():
                            break
                        try:
                            row = evidence.receipt(path, 0, launch["cap_seconds"])
                        except (AssertionError, FileNotFoundError, UnicodeError, ValueError):
                            break  # Incomplete final write; retry unless the child has exited.
                        observed = time.monotonic() - started
                        if observed > launch["cap_seconds"]:
                            break  # A post-deadline observation cannot improve the formal endpoint.
                        row["first_observed_seconds"] = observed
                        row["effective_available_seconds"] = max(observed, row["data_close_seconds"])
                        observations.append(row)
                        next_event += 1
                    elapsed = time.monotonic() - started
                    if child.poll() is not None:
                        break
                    if elapsed >= launch["hard_stop_seconds"]:
                        reason = "whole_run_hard_stop"
                        child.kill()
                        break
                    if elapsed - last_sample >= 60:
                        upper, lower = bound_preview(observations)
                        available = memory_available()
                        free = shutil.disk_usage(CAMPAIGN).free
                        low_memory_checks = low_memory_checks + 1 if available < 2 * 1024**3 else 0
                        sample = dict(number=launch["number"], id=launch["id"], arm=launch["arm"],
                                      process_seconds=elapsed, observed_events=len(observations),
                                      provisional_U=upper, provisional_L=lower,
                                      provisional_gap=upper - lower if upper is not None else None,
                                      available_memory_bytes=available, free_disk_bytes=free,
                                      sampled_unix=time.time(), formal_endpoint=False)
                        append_jsonl(destination / "samples.jsonl", sample)
                        atomic_status(CAMPAIGN / "runtime_status.json", sample)
                        last_sample = elapsed
                        if free < 5 * 1024**3:
                            reason = "host_disk_safety_stop"
                            child.kill()
                            break
                        if low_memory_checks >= 2:
                            reason = "host_memory_safety_stop"
                            child.kill()
                            break
                    time.sleep(0.05)
                child.wait(timeout=max(2.0, launch["cap_seconds"] - (time.monotonic() - started)))
                exit_observed_seconds = time.monotonic() - started
                # Drain commits completed at shutdown, preserving actual observation times.
                while True:
                    path = destination / "journal" / f"event_{next_event}.commit"
                    if not path.exists():
                        break
                    row = evidence.receipt(path, 0, launch["cap_seconds"])
                    observed = time.monotonic() - started
                    if observed > launch["cap_seconds"]:
                        break
                    row["first_observed_seconds"] = observed
                    row["effective_available_seconds"] = max(observed, row["data_close_seconds"])
                    observations.append(row)
                    next_event += 1
        finally:
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=5)
    wrapper_wall = time.monotonic() - started
    wall = exit_observed_seconds
    if reason == "normal_return" and child.returncode != 0:
        reason = "abnormal_process_exit"
    completion = dict(schema="round88-a1-g3-completion-v1", number=launch["number"], id=launch["id"],
                      arm=launch["arm"], returncode=child.returncode, process_wall_seconds=wall,
                      prelaunch_seconds=prelaunch_seconds, end_to_end_seconds=prelaunch_seconds + wall,
                      postexit_drain_and_restore_seconds=wrapper_wall - wall,
                      wrapper_wall_seconds=wrapper_wall,
                      fully_observed_end_to_end_seconds=prelaunch_seconds + wrapper_wall,
                      process_cap_seconds=launch["cap_seconds"], within_cap=wall <= launch["cap_seconds"],
                      stop_reason=reason, committed_events=len(observations), ended_unix=time.time())
    write_new(destination / "completion.json", completion)
    write_new(destination / "observations.json", observations)
    audit_started = time.perf_counter()
    try:
        assert completion["within_cap"], "process wall exceeded whole-run cap"
        assert affinity.read_masks() == binding["before"], "launcher affinity not restored"
        assert reason in {"normal_return", "whole_run_hard_stop", "host_disk_safety_stop", "host_memory_safety_stop"}
        audited = audit_launch(launch, observations, completion, identity)
    except Exception as exc:
        audited = dict(passed=False, error=repr(exc), status="requires_independent_review",
                       certificate=False, endpoint=None)
    audited["offline_audit_seconds"] = time.perf_counter() - audit_started
    write_new(destination / "audit.json", audited)
    record = dict(number=launch["number"], id=launch["id"], arm=launch["arm"],
                  destination=str(destination), completion=completion,
                  audit_passed=audited["passed"], endpoint=audited.get("endpoint"),
                  audit_error=audited.get("error"))
    append_jsonl(CAMPAIGN / "summary.jsonl", record)
    print(json.dumps(dict(completed=record), ensure_ascii=False), flush=True)
    if not audited["passed"]:
        raise RuntimeError("Audit failed; preserve evidence and stop before next run")
    if reason in {"host_disk_safety_stop", "host_memory_safety_stop"}:
        raise RuntimeError("Resource safety stop; no next launch")
    return record


def run_stage(stage: str) -> None:
    prereg = read(PREREG)
    ensure_static_identity(prereg, require_frozen_head=True)
    identity = read(CAMPAIGN / "identity.json")
    assert identity["schema"] == "round88-a1-g3-identity-v1"
    assert identity["prereg_sha256"] == sha(PREREG)
    assert identity["runner_sha256"] == sha(Path(__file__))
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["reader_sha256"] == sha(Path(evidence.__file__))
    assert identity["physical_reader_sha256"] == sha(Path(evidence.physical_module.__file__))
    assert identity["exchange_reader_sha256"] == sha(ROOT / "scripts/round83_audit_v2.py")
    assert identity["affinity_sha256"] == sha(ROOT / "scripts/round70_affinity.py")
    assert identity["normalizer_sha256"] == sha(ROOT / "scripts/round75_startup.py")
    assert identity["input_audit_sha256"] == sha(INPUT_AUDIT)
    assert identity["source_hashes_sha256"] == sha(SOURCE_HASHES)
    assert identity["launches"] == build_launches(prereg)
    require_lease(stage, identity)
    assert not (CAMPAIGN / "active_run.lock").exists(), "another stage is active"
    existing = []
    summary_path = CAMPAIGN / "summary.jsonl"
    if summary_path.exists():
        existing = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()]
    expected_before = 0 if stage == "smoke" else 6
    assert len(existing) == expected_before, "Never rerun, skip or splice a formal arm"
    assert all(row["number"] == i and row["audit_passed"] for i, row in enumerate(existing, 1))
    if stage == "rest":
        gate = read(CAMPAIGN / "runner_smoke_gate.json")
        assert gate == dict(schema="round88-a1-g3-smoke-gate-v1", smoke_runs=6,
                            summary_sha256=sha(summary_path), authorized_by="Astra", accepted=True)
    launches = [row for row in identity["launches"] if row["stage"] == stage]
    assert len(launches) == (6 if stage == "smoke" else 18)
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(stage=stage, pid=os.getpid(), started_unix=time.time())) + "\n")
    stage_records = []
    stage_error = None
    try:
        for launch in launches:
            attempt_started = time.monotonic()
            try:
                stage_records.append(run_one(launch, prereg, identity))
            except Exception as exc:
                # A failure in Popen, affinity readback, receipt handling or
                # finalization must leave a counted, non-overwritable record.
                # If run_one already saved a failed audit, retain that record.
                recorded = []
                if summary_path.exists():
                    recorded = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()]
                if not recorded or recorded[-1]["number"] != launch["number"]:
                    destination = Path(launch["destination"])
                    marker = destination / "process_start_marker.json"
                    elapsed = time.monotonic() - attempt_started
                    wrapper_lower = (time.monotonic() - read(marker)["monotonic_seconds"]) if marker.exists() else None
                    failure = dict(schema="round88-a1-g3-failure-v1", number=launch["number"],
                                   id=launch["id"], arm=launch["arm"], error=repr(exc),
                                   destination=str(destination), destination_exists=destination.exists(),
                                   total_attempt_elapsed_seconds=elapsed,
                                   process_wrapper_elapsed_lower_bound_seconds=wrapper_lower,
                                   endpoint=None, certificate=False, needs_independent_review=True,
                                   recorded_unix=time.time())
                    write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', failure)
                    synthetic = dict(number=launch["number"], id=launch["id"], arm=launch["arm"],
                                     destination=str(destination), completion=None,
                                     audit_passed=False, endpoint=None, audit_error=repr(exc),
                                     failure_record=str(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json'))
                    append_jsonl(summary_path, synthetic)
                raise
            if launch["arm"] == launch["panel"]["method_order"][-1]:
                all_records = existing + stage_records
                cross_arm_contradiction_check(all_records, launch["id"])
                signals = severe_risk_signal(all_records, launch["id"])
                if signals:
                    write_new(CAMPAIGN / f'runner_{stage}_risk_stop.json', dict(
                        role=launch["id"], signals=signals, research_signal_only=True,
                        requires_paired_review=True, summary_sha256=sha(summary_path),
                    ))
                    raise RuntimeError("Severe screen signal; pause next role for coordinator review")
    except Exception as exc:
        stage_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        stage_summary = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()][expected_before:] \
            if summary_path.exists() else []
        observed_process_wall = sum(row["completion"]["process_wall_seconds"]
                                    for row in stage_summary if row["completion"] is not None)
        failure_cost = sum(
            read(path)["total_attempt_elapsed_seconds"]
            for path in CAMPAIGN.glob("runner_failure_*.json")
        )
        write_new(CAMPAIGN / f"runner_{stage}_completion.json", dict(
            stage=stage, completed=len(stage_summary), planned=len(launches),
            all_audits_passed=len(stage_summary) == len(launches) and all(row["audit_passed"] for row in stage_summary),
            stop_reason=stage_error,
            process_wall_seconds=observed_process_wall,
            failed_attempt_elapsed_lower_bound_seconds=failure_cost,
            process_wall_total_if_any_failed="unknown" if failure_cost else
                observed_process_wall,
            ended_unix=time.time(),
        ))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"dry-run", "prepare", "run-smoke", "run-rest"}, \
        "Usage: round88_a1_g3.py dry-run|prepare|run-smoke|run-rest"
    command = sys.argv[1]
    if command == "dry-run":
        dry_run()
    elif command == "prepare":
        prepare()
    else:
        run_stage(command.removeprefix("run-"))


if __name__ == "__main__":
    main()
