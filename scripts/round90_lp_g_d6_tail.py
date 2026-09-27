"""One conditional D6 tail pair using the preserved Round90 source objects.

Import is inert. ``prepare`` audits historical Git blobs but never optimizes;
``run`` needs a separate root lease and starts at most two fresh processes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round90/preregistration_d6_tail.json"
CAMPAIGN = ROOT / "results/unified_exact_round90/runner_lp_g_d6_tail"
REF = "a71bd53ca412e9b9e529e7237446687d360a94ce"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen_modules(prereg: dict):
    path = ROOT / prereg["frozen_priority_wrapper"]
    assert sha(path) == prereg["frozen_priority_wrapper_sha256"]
    spec = importlib.util.spec_from_file_location("round90_priority_readonly_for_d6_tail", path)
    assert spec is not None and spec.loader is not None
    priority = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(priority)
    r90 = priority.frozen_runner()  # Loads helpers only; do not call old validate().
    assert sha(ROOT / prereg["frozen_g3_runner"]) == prereg["frozen_g3_runner_sha256"]
    return priority, r90


def source_rows(r90, prereg: dict, source_hashes: list[dict]) -> list[dict]:
    path = ROOT / prereg["source_manifest_path"]
    assert r90.sha(path) == prereg["source_manifest_sha256"]
    rows = r90.read(path)
    assert isinstance(rows, list) and len(rows) == 165
    assert len({row["path"] for row in rows}) == 165
    assert all(row["matches"] is True and row["actual"] == row["expected"]
               and re.fullmatch(r"[0-9a-f]{64}", row["expected"])
               for row in rows)
    assert all(re.fullmatch(r"(?:CMakeLists\.txt|(?:include|src|tests)/[A-Za-z0-9_./+-]+)",
                            row["path"]) and ".." not in Path(row["path"]).parts
               for row in rows)
    expected = {row["path"]: row["expected"] for row in rows}
    assert len(source_hashes) == 7 and len({row["path"] for row in source_hashes}) == 7
    extra_test_path = "tests/round90_lp_g_split_tests.cpp"
    assert extra_test_path not in expected
    extras = []
    for row in source_hashes:
        if row["path"] in expected:
            assert row["sha256"] == expected[row["path"]]
        else:
            assert row["path"] == extra_test_path
            assert row["sha256"] == "2dd4582bb757624228fb610a2c9b3cc55fec0b84dca892601ecc1bec83a58d4d"
            extras.append(dict(path=row["path"], expected=row["sha256"],
                               actual=row["sha256"], matches=True))
    assert len(extras) == 1
    # The measured production manifest has 165 entries. The separately pinned
    # critical test source is a 166th immutable blob, not a missing production entry.
    return rows + extras


def audit_preserved_blobs(rows: list[dict], source_ref: str) -> list[dict]:
    """Read exact bytes via one `git cat-file --batch`; never touch checkout."""
    assert source_ref == REF and re.fullmatch(r"[0-9a-f]{40}", source_ref)
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    receipts = []
    try:
        assert process.stdin is not None and process.stdout is not None
        for row in rows:
            request = f'{source_ref}:{row["path"]}\n'.encode("ascii")
            process.stdin.write(request)
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii", errors="strict").strip().split()
            assert len(header) == 3 and header[1] == "blob", (row["path"], header)
            oid, size_text = header[0], header[2]
            assert re.fullmatch(r"[0-9a-f]{40}", oid) and size_text.isdecimal()
            remaining = int(size_text)
            digest = hashlib.sha256()
            while remaining:
                block = process.stdout.read(min(1024 * 1024, remaining))
                assert block, (row["path"], "truncated Git blob")
                digest.update(block)
                remaining -= len(block)
            assert process.stdout.read(1) == b"\n"
            actual = digest.hexdigest()
            assert actual == row["expected"], (row["path"], actual, row["expected"])
            receipts.append(dict(path=row["path"], git_oid=oid, size_bytes=int(size_text),
                                 expected_sha256=row["expected"], actual_sha256=actual))
        process.stdin.close()
        assert process.wait() == 0, process.stderr.read().decode("utf-8", errors="replace")
        assert process.stdout.read() == b""
        return receipts
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def validate_snapshot(priority, r90, prereg: dict) -> tuple[dict, dict, list[dict]]:
    """A new explicit source gate; never invoke the old working-tree gate."""
    assert os.name == "nt" and priority.ROOT == ROOT and r90.ROOT == ROOT
    assert prereg["schema"] == "round90-lp-g-d6-tail-preregistration-v1"
    assert prereg["status"] == "source_only_pending_independent_review_and_root_gates"
    assert prereg["runtime_root"] == CAMPAIGN.relative_to(ROOT).as_posix()
    assert prereg["source_preservation_ref"] == REF
    assert prereg["planned_runs"] == 2 and prereg["sum_process_caps_seconds"] == 14400
    assert prereg["execution_order"] == ["D6/ENS-C", "D6/LP-G"]
    assert prereg["seed"] == 0 and prereg["role"]["method_order"] == ["ENS-C", "LP-G"]
    assert prereg["role"]["cap_seconds"] == 7200
    assert prereg["no_component_time_or_work_slices"] is True
    assert prereg["prepare_does_not_authorize_optimize"] is True
    assert prereg["run_requires_separate_root_lease"] is True
    for key in ("frozen_priority_preregistration", "frozen_g3_preregistration",
                "frozen_g3_qualification_gate"):
        assert r90.sha(ROOT / prereg[key]) == prereg[key + "_sha256"]
    baseline = r90.read(ROOT / prereg["frozen_priority_preregistration"])
    g3 = r90.read(ROOT / prereg["frozen_g3_preregistration"])
    old_gate = r90.read(ROOT / prereg["frozen_g3_qualification_gate"])
    assert baseline["source_commit"] == old_gate["source_commit"] == \
        prereg["historical_build_source_commit_provisional"]
    assert old_gate["qualified"] is True and old_gate["authorized_by"] == "root"
    assert baseline["source_hashes"] == old_gate["source_hashes"]
    assert baseline["harness_hashes"] == old_gate["harness_hashes"] == r90.harness_hashes()
    assert baseline["candidate_binary"] == g3["candidate_binary"] == prereg["candidate_binary"]
    assert baseline["candidate_binary_sha256"] == old_gate["candidate_binary_sha256"] == \
        prereg["candidate_binary_sha256"]
    assert r90.sha(ROOT / prereg["candidate_binary"]) == prereg["candidate_binary_sha256"]
    assert baseline["common"] == prereg["common"]
    assert baseline["common"] == {key: g3["common"][key] for key in baseline["common"]}
    assert baseline["planning_manifest"] == prereg["planning_manifest"]
    assert baseline["input_identity_audit"] == prereg["input_identity_audit"]
    rows = source_rows(r90, prereg, baseline["source_hashes"])

    # The original nineteen-role protocol identifies D6; only this new outer
    # deadline and paired order differ from its earlier 3600-second screening.
    role, previous = prereg["role"], baseline["roles"][1]
    assert previous["id"] == role["id"] == "D6" and previous["cap_seconds"] == 3600
    for key in ("scenario_id", "input_path", "input_sha256", "T_seconds",
                "pickup_seconds", "drop_seconds", "lambda"):
        assert role[key] == previous[key], key
    manifest = r90.read(ROOT / prereg["planning_manifest"])
    input_audit = r90.read(ROOT / prereg["input_identity_audit"])
    assert manifest["canonical_development_root"].replace("\\", "/") == str(ROOT).replace("\\", "/")
    assert input_audit["role_count"] == 19 and input_audit["all_hashes_match"] is True
    assert input_audit["all_scenarios_match"] is True
    assert r90.sha(ROOT / prereg["input_identity_audit"]) == \
        baseline["harness_hashes"]["input_identity_audit"]
    source = {row["id"]: row for row in manifest["roles"]}["D6"]
    audited = {row["id"]: row for row in input_audit["roles"]}["D6"]
    assert len(manifest["roles"]) == len(input_audit["roles"]) == 19
    relative = source["input_path"].replace("\\", "/").split("/reference/", 1)
    assert len(relative) == 2 and role["input_path"] == "reference/" + relative[1]
    assert source["source_protocol"].replace("\\", "/").endswith("/protocol.json")
    assert audited["historical_source_path"].replace("\\", "/") == \
        source["input_path"].replace("\\", "/")
    assert Path(audited["execution_path"]).resolve() == (ROOT / role["input_path"]).resolve()
    assert audited["passed"] is True and audited["hash_matches_planning_and_protocol"] is True
    assert audited["scenario_matches_protocol"] is True
    for key in ("scenario_id", "T_seconds", "pickup_seconds", "drop_seconds", "lambda"):
        assert role[key] == source[key] == audited[key], key
    assert role["input_sha256"] == source["input_sha256_from_protocol"] == \
        audited["actual_sha256"] == audited["planning_sha256"]
    assert source["development_full_run_cap_seconds"] == 3600
    assert r90.sha(ROOT / role["input_path"]) == role["input_sha256"]
    return baseline, g3, rows


def launches_for(r90, prereg: dict, g3: dict) -> list[dict]:
    role, launches = prereg["role"], []
    exemplar = g3["panel"][0]
    options = ("--input", "--lambda", "--T", "--pickup-time", "--drop-time",
               "--time-limit", "--process-wall-time-limit")

    def masked(command: list[str]) -> list[str]:
        result = command.copy()
        for option in options:
            assert result.count(option) == 1
            result[result.index(option) + 1] = "<registered-role-value>"
        return result

    for number, arm in enumerate(role["method_order"], 1):
        destination = CAMPAIGN / "D6" / "raw" / f"{number:02d}_D6_{arm}"
        command = r90.command_for(g3, role, arm, destination)
        assert masked(command) == masked(r90.command_for(g3, exemplar, arm, destination))
        assert command[command.index("--round90-lp-g-split") + 1] == \
            ("true" if arm == "LP-G" else "false")
        assert command[command.index("--gurobi-seed") + 1] == "0"
        assert command[command.index("--time-limit") + 1] == "7194"
        assert command[command.index("--process-wall-time-limit") + 1] == "7200"
        assert "--round88-constructive-only-descent" not in command
        assert "--round89-native-ot-b1" not in command
        launches.append(dict(number=number, id="D6", arm=arm, seed=0,
                             stage="d6_tail", panel=dict(role, instance_path=role["input_path"]),
                             destination=str(destination), cap_seconds=7200,
                             hard_stop_seconds=7198, command=command))
    assert [f'{row["id"]}/{row["arm"]}' for row in launches] == prereg["execution_order"]
    assert sum(row["cap_seconds"] for row in launches) == 14400
    return launches


def root_prepare_gate(r90, prereg: dict) -> tuple[dict, str]:
    path = ROOT / prereg["prepare_gate_path"]
    gate = r90.read(path)
    assert gate["schema"] == "round90-lp-g-d6-tail-prepare-gate-v1"
    assert gate["authorized_by"] == "root" and gate["allow_prepare"] is True
    assert gate["allow_optimize"] is False and gate["finite_d6_tail_accepted"] is True
    assert gate["prereg_sha256"] == r90.sha(PREREG)
    assert gate["wrapper_sha256"] == r90.sha(Path(__file__))
    assert gate["source_preservation_ref"] == REF
    assert gate["source_manifest_sha256"] == prereg["source_manifest_sha256"]
    assert gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert gate["frozen_g3_runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert gate["decision_sha256"] == r90.sha(ROOT / prereg["decision_path"])
    review = gate["independent_static_review_path"]
    assert review.startswith("results/unified_exact_round90/") and ".." not in Path(review).parts
    assert r90.sha(ROOT / review) == gate["independent_static_review_sha256"]
    return gate, r90.sha(path)


def prepare(priority, r90) -> None:
    invocation_started = time.perf_counter()
    prereg = r90.read(PREREG)
    baseline, g3, rows = validate_snapshot(priority, r90, prereg)
    launches = launches_for(r90, prereg, g3)
    gate, gate_sha = root_prepare_gate(r90, prereg)
    assert not CAMPAIGN.exists(), "Never overwrite, resume or splice a campaign"
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    # This audit is intentionally deferred until the separately authorized
    # zero-Optimize prepare, after other I/O-intensive work has released its slot.
    blobs = audit_preserved_blobs(rows, REF)
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    snapshot_path = CAMPAIGN / "source_snapshot_receipt.json"
    r90.write_new(snapshot_path, dict(
        schema="round90-lp-g-d6-tail-source-snapshot-v1", optimizer_calls=0,
        source_preservation_ref=REF, historical_build_source_commit_provisional=
        prereg["historical_build_source_commit_provisional"],
        source_manifest_sha256=prereg["source_manifest_sha256"],
        production_manifest_blob_count=165, additional_critical_test_blob_count=1,
        critical_source_count=7,
        verified_blob_count=len(blobs), all_byte_hashes_match=True, blobs=blobs))
    r90.write_new(CAMPAIGN / "identity.json", dict(
        schema="round90-lp-g-d6-tail-identity-v1", optimizer_calls=0,
        prereg_sha256=r90.sha(PREREG), wrapper_sha256=r90.sha(Path(__file__)),
        frozen_priority_wrapper_sha256=prereg["frozen_priority_wrapper_sha256"],
        runner_sha256=prereg["frozen_g3_runner_sha256"], gate_sha256=gate_sha,
        decision_sha256=gate["decision_sha256"],
        independent_static_review_sha256=gate["independent_static_review_sha256"],
        source_preservation_ref=REF, source_manifest_sha256=prereg["source_manifest_sha256"],
        source_snapshot_receipt_sha256=r90.sha(snapshot_path),
        historical_build_source_commit_provisional=prereg["historical_build_source_commit_provisional"],
        source_hashes=baseline["source_hashes"], harness_hashes=baseline["harness_hashes"],
        candidate_binary_sha256=prereg["candidate_binary_sha256"], launches=launches,
        prepared_unix=time.time()))
    r90.write_new(CAMPAIGN / "preflight.json", dict(
        schema="round90-lp-g-d6-tail-preflight-v1", optimizer_calls=0,
        planned_runs=2, process_cap_sum_seconds=14400, canonical_inputs_verified=1,
        git_source_blob_count_verified=166, production_manifest_blob_count=165,
        additional_critical_test_blob_count=1, binary_harness_verified=True,
        preparation_elapsed_seconds_before_preflight_write=time.perf_counter() - invocation_started,
        disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        memory_available_bytes=r90.memory_available(),
        note="Prepare cannot start Optimize; root must issue a separate exact two-arm lease."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def run(priority, r90) -> None:
    invocation_started = time.perf_counter()
    prereg = r90.read(PREREG)
    baseline, g3, _ = validate_snapshot(priority, r90, prereg)
    gate, gate_sha = root_prepare_gate(r90, prereg)
    identity_path = CAMPAIGN / "identity.json"
    identity = r90.read(identity_path)
    assert identity["schema"] == "round90-lp-g-d6-tail-identity-v1"
    assert identity["prereg_sha256"] == r90.sha(PREREG)
    assert identity["wrapper_sha256"] == r90.sha(Path(__file__))
    assert identity["runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert identity["gate_sha256"] == gate_sha
    assert identity["decision_sha256"] == gate["decision_sha256"]
    assert identity["source_preservation_ref"] == REF
    assert identity["source_manifest_sha256"] == prereg["source_manifest_sha256"]
    snapshot_path = CAMPAIGN / "source_snapshot_receipt.json"
    assert identity["source_snapshot_receipt_sha256"] == r90.sha(snapshot_path)
    snapshot = r90.read(snapshot_path)
    assert snapshot["verified_blob_count"] == 166 and snapshot["all_byte_hashes_match"] is True
    assert snapshot["production_manifest_blob_count"] == 165
    assert snapshot["additional_critical_test_blob_count"] == 1 and snapshot["critical_source_count"] == 7
    assert snapshot["source_preservation_ref"] == REF
    assert identity["source_hashes"] == baseline["source_hashes"]
    assert identity["harness_hashes"] == baseline["harness_hashes"]
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["launches"] == launches_for(r90, prereg, g3)
    lease_path = CAMPAIGN / prereg["run_lease_name"]
    lease = r90.read(lease_path)
    assert lease == dict(schema="round90-lp-g-d6-tail-run-lease-v1",
                         authorized_by="root", allow_optimize=True,
                         identity_sha256=r90.sha(identity_path), planned_runs=2,
                         execution_order=prereg["execution_order"])
    assert not (CAMPAIGN / "run_started.json").exists(), "Never rerun or resume"
    assert not (CAMPAIGN / "active_run.lock").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["launches"])
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    preflight_seconds = time.perf_counter() - invocation_started
    started = time.perf_counter()
    r90.write_new(CAMPAIGN / "run_started.json", dict(
        identity_sha256=r90.sha(identity_path), lease_sha256=r90.sha(lease_path),
        started_unix=time.time(), complete_process_runs_planned=2,
        preflight_seconds=preflight_seconds,
        internal_optimize_calls_unbounded_by_arm_count=True))
    records, run_error = [], None
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(pid=os.getpid(), started_unix=time.time())) + "\n")
    try:
        for launch in identity["launches"]:
            attempt_started = time.perf_counter()
            try:
                if launch["number"] == 1:
                    (CAMPAIGN / "D6").mkdir(exist_ok=False)
                r90.CAMPAIGN = CAMPAIGN / "D6"  # Only this loaded G3 module object.
                record = r90.run_one(launch, g3, identity)
                params = priority.native_parameters(r90, launch, record)
                r90.write_new(Path(launch["destination"]) / "native_parameter_evidence.json", params)
                assert params["status"] == "native_result_readback_verified" or \
                    record["completion"]["stop_reason"] != "normal_return"
                record["seed"] = 0
                records.append(record)
                r90.append_jsonl(CAMPAIGN / "summary.jsonl", dict(
                    seed=0, role="D6", record=record, native_parameter_evidence=params))
            except Exception as exc:
                r90.write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', dict(
                    schema="round90-lp-g-d6-tail-failure-v1", number=launch["number"],
                    role="D6", arm=launch["arm"], error=repr(exc),
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination=launch["destination"],
                    destination_exists=Path(launch["destination"]).exists(),
                    completion_exists=(Path(launch["destination"]) / "completion.json").is_file(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
        assert {row["arm"] for row in records} == {"ENS-C", "LP-G"}
        r90.cross_arm_contradiction(records, "D6")
        signals = r90.severe_risk_signal(records, "D6")
        if signals:
            r90.write_new(CAMPAIGN / "D6" / "runner_tail_risk_stop.json", dict(
                role="D6", signals=signals, research_signal_only=True,
                requires_paired_review=True,
                summary_sha256=r90.sha(CAMPAIGN / "summary.jsonl")))
            raise RuntimeError("Severe paired signal; no further run is admitted")
    except Exception as exc:
        run_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        failures = [r90.read(path) for path in sorted(CAMPAIGN.glob("runner_failure_*.json"))]
        attempted = {row["number"] for row in records} | {row["number"] for row in failures}
        paid = [r90.read(Path(row["destination"]) / "completion.json")
                for row in identity["launches"]
                if (Path(row["destination"]) / "completion.json").is_file()]
        r90.write_new(CAMPAIGN / "run_completion.json", dict(
            schema="round90-lp-g-d6-tail-run-completion-v1", planned=2,
            completed=len(records), attempted=sorted(attempted), error=run_error,
            not_run=[f'{row["id"]}/{row["arm"]}' for row in identity["launches"]
                     if row["number"] not in attempted],
            paid_process_wall_seconds_with_completion=sum(row["process_wall_seconds"] for row in paid),
            completed_process_receipts=len(paid),
            precompletion_failed_attempt_elapsed_seconds=sum(
                row["attempt_elapsed_seconds"] for row in failures if not row["completion_exists"]),
            full_outer_wall_seconds=time.perf_counter() - started,
            outer_wall_excludes_preflight_validation=True,
            full_invocation_wall_seconds_before_receipt_write=time.perf_counter() - invocation_started,
            failed_attempt_costs=failures, ended_unix=time.time()))


def main() -> None:
    if not __debug__:
        raise RuntimeError("Python -O would disable the identity and lease assertions")
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round90_lp_g_d6_tail.py prepare|run"
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    priority, r90 = frozen_modules(prereg)
    if sys.argv[1] == "prepare":
        prepare(priority, r90)
    else:
        run(priority, r90)


if __name__ == "__main__":
    main()
