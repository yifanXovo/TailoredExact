"""Finite R94 three-arm adapter over immutable R90/R88 evidence code.

Import and ``prepare`` never call Optimize. ``qualify`` and ``run`` require
distinct root leases bound to the prepared identity. The frozen R90 G3 module
is changed only in this private in-memory import: CAMPAIGN points at R94's
new directory and audit_launch adds P plus stricter parameter checks. Its
supervision, journal timing, LP-G split audit and physical reader are retained.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round94/preregistration.json"
CAMPAIGN = ROOT / "results/unified_exact_round94/runner_lpg_contemporary"
RECOVERY_PREREG = ROOT / "results/unified_exact_round94/recovery_preregistration_v2.json"
RECOVERY = CAMPAIGN / "recovery_v2"
REFERENCE_IDS = ("F2", "C20", "B50", "U6")
ORDER = (
    "F2/P-GRB", "F2/ENS-C", "F2/LP-G",
    "C20/LP-G", "C20/ENS-C", "C20/P-GRB",
    "B50/ENS-C", "B50/P-GRB", "B50/LP-G",
    "U6/LP-G", "U6/P-GRB", "U6/ENS-C",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pinned(prereg: dict, stem: str) -> Path:
    path = ROOT / prereg[stem]
    assert path.is_file() and sha(path) == prereg[stem + "_sha256"], stem
    return path


def modules(prereg: dict):
    path = pinned(prereg, "frozen_d6_runner")
    pinned(prereg, "frozen_d6_preregistration")
    spec = importlib.util.spec_from_file_location("round90_d6_readonly_for_r94", path)
    assert spec is not None and spec.loader is not None
    d6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d6)
    old = read(ROOT / prereg["frozen_d6_preregistration"])
    priority, r90 = d6.frozen_modules(old)
    assert sha(ROOT / prereg["frozen_g3_runner"]) == prereg["frozen_g3_runner_sha256"]
    assert sha(ROOT / prereg["frozen_r88_runner"]) == prereg["frozen_r88_runner_sha256"]
    assert sha(ROOT / prereg["frozen_native_reader"]) == prereg["frozen_native_reader_sha256"]
    assert Path(r90.audited_runner_utilities.__file__).resolve() == (ROOT / prereg["frozen_r88_runner"]).resolve()
    assert Path(r90.evidence.__file__).resolve() == (ROOT / prereg["frozen_native_reader"]).resolve()
    return d6, priority, r90, old


def validate(prereg: dict, d6, priority, r90, old: dict) -> tuple[dict, dict, list[dict]]:
    assert os.name == "nt" and prereg["schema"] == "round94-lpg-contemporary-preregistration-v1"
    assert prereg["status"] == "source_only_pending_independent_review_and_separate_leases"
    assert prereg["runtime_root"] == CAMPAIGN.relative_to(ROOT).as_posix()
    assert prereg["source_preservation_ref"] == d6.REF == old["source_preservation_ref"]
    assert prereg["candidate_binary"] == old["candidate_binary"]
    assert prereg["candidate_binary_sha256"] == old["candidate_binary_sha256"]
    assert sha(ROOT / prereg["candidate_binary"]) == prereg["candidate_binary_sha256"]
    assert {k: v for k, v in prereg["common"].items() if k != "gurobi_version"} == old["common"]
    assert prereg["common"]["gurobi_version"] == "13.0.2"
    assert prereg["qualification_order"] == list(REFERENCE_IDS)
    assert prereg["execution_order"] == list(ORDER)
    assert prereg["planned_qualification_processes"] == 4
    assert prereg["qualification_process_cap_seconds"] == 15
    assert prereg["maximum_qualification_process_seconds"] == 60
    assert prereg["planned_formal_runs"] == 12 and prereg["maximum_formal_process_seconds"] == 13500
    assert prereg["prepare_has_zero_optimize_calls"] is True
    assert prereg["qualification_requires_separate_root_lease"] is True
    assert prereg["formal_requires_separate_root_lease"] is True
    assert sha(ROOT / prereg["plan_path"]) == prereg["plan_sha256"]
    for key in ("frozen_r87_reference_identity", "planning_manifest", "input_identity_audit",
                "frozen_g4_remaining_preregistration"):
        pinned(prereg, key)
    assert old["source_manifest_path"] and old["source_manifest_sha256"]
    assert sha(ROOT / old["source_manifest_path"]) == old["source_manifest_sha256"]
    for key in ("frozen_priority_preregistration", "frozen_g3_preregistration",
                "frozen_g3_qualification_gate"):
        assert sha(ROOT / old[key]) == old[key + "_sha256"]
    baseline = read(ROOT / old["frozen_priority_preregistration"])
    g3 = read(ROOT / old["frozen_g3_preregistration"])
    gate = read(ROOT / old["frozen_g3_qualification_gate"])
    assert gate["qualified"] is True and gate["authorized_by"] == "root"
    assert baseline["candidate_binary_sha256"] == gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert baseline["harness_hashes"] == gate["harness_hashes"] == r90.harness_hashes()
    assert baseline["source_hashes"] == gate["source_hashes"]
    assert baseline["source_commit"] == gate["source_commit"] == old["historical_build_source_commit_provisional"]
    source_rows = d6.source_rows(r90, old, baseline["source_hashes"])
    assert len(source_rows) == 166
    planning = read(ROOT / prereg["planning_manifest"])
    input_audit = read(ROOT / prereg["input_identity_audit"])
    references = read(ROOT / prereg["frozen_r87_reference_identity"])["references"]
    remaining = read(ROOT / prereg["frozen_g4_remaining_preregistration"])
    historical = {
        "F2": baseline["roles"][0],
        "C20": next(r for r in remaining["roles"] if r["id"] == "C20"),
        "B50": next(r for r in remaining["roles"] if r["id"] == "B50"),
        "U6": next(r for r in g3["panel"] if r["id"] == "U6"),
    }
    assert len(planning["roles"]) == len(input_audit["roles"]) == 19
    assert input_audit["all_hashes_match"] is True and input_audit["all_scenarios_match"] is True
    planned = {r["id"]: r for r in planning["roles"]}
    audited = {r["id"]: r for r in input_audit["roles"]}
    expected_caps = (900, 600, 1800, 1200)
    expected_orders = (("P-GRB", "ENS-C", "LP-G"), ("LP-G", "ENS-C", "P-GRB"),
                       ("ENS-C", "P-GRB", "LP-G"), ("LP-G", "P-GRB", "ENS-C"))
    assert len(prereg["roles"]) == 4
    for role, rid, cap, order in zip(prereg["roles"], REFERENCE_IDS, expected_caps, expected_orders):
        assert rid == role["id"]
        assert role["cap_seconds"] == cap and tuple(role["method_order"]) == order
        assert role["reference"] == {k: references[rid][k] for k in ("fingerprint", "canonical_sha256", "columns", "rows")}
        source, audit, prior = planned[rid], audited[rid], historical[rid]
        assert audit["passed"] is True and audit["hash_matches_planning_and_protocol"] is True
        assert audit["scenario_matches_protocol"] is True
        assert role["input_path"] == prior["input_path"]
        for key in ("scenario_id", "T_seconds", "pickup_seconds", "drop_seconds", "lambda"):
            assert role[key] == prior[key] == audit[key], (rid, key)
        assert role["input_sha256"] == prior["input_sha256"]
        assert role["input_sha256"] == source["input_sha256_from_protocol"] == audit["actual_sha256"]
        assert sha(ROOT / role["input_path"]) == role["input_sha256"]
    assert sum(3 * r["cap_seconds"] for r in prereg["roles"]) == 13500
    return baseline, g3, source_rows


def replace_option(command: list[str], option: str, value: object) -> None:
    assert command.count(option) == 1
    command[command.index(option) + 1] = str(value)


def formal_launches(prereg: dict, r90, g3: dict) -> list[dict]:
    launches = []
    for role in prereg["roles"]:
        for arm in role["method_order"]:
            number = len(launches) + 1
            destination = CAMPAIGN / "formal" / "raw" / f'{number:02d}_{role["id"]}_{arm}'
            command = (r90.audited_runner_utilities.command_for(prereg, role, arm, destination)
                       if arm == "P-GRB" else r90.command_for(g3, role, arm, destination))
            assert command[0] == str((ROOT / prereg["candidate_binary"]).resolve())
            assert command[command.index("--method") + 1] == ("gurobi" if arm == "P-GRB" else "gcap-frontier")
            assert command[command.index("--gurobi-seed") + 1] == "0"
            assert command[command.index("--time-limit") + 1] == str(role["cap_seconds"] - 6)
            assert command[command.index("--process-wall-time-limit") + 1] == str(role["cap_seconds"])
            if arm == "P-GRB":
                assert command.count("--plain-baseline") == command.count("--gurobi-model-export") == 1
                assert command[command.index("--round24-expected-gurobi-model-fingerprint") + 1] == str(role["reference"]["fingerprint"])
                for flag in ("--round24-executable-sha256", "--round24-manifest-executable-sha256"):
                    assert command[command.index(flag) + 1] == prereg["candidate_binary_sha256"]
                for forbidden in ("--algorithm-preset", "--round90-lp-g-split", "--gurobi-hga-start",
                                  "--hga-incumbent", "--external-incumbent", "--incumbent-json",
                                  "--frontier-import-interval-bound", "--round88-constructive-only-descent"):
                    assert forbidden not in command, forbidden
            else:
                assert command[command.index("--algorithm-preset") + 1] == "research-round83-vds-equal-net-exchange"
                assert command[command.index("--round90-lp-g-split") + 1] == ("true" if arm == "LP-G" else "false")
                assert "--plain-baseline" not in command and "--gurobi-model-export" not in command
            launches.append(dict(number=number, id=role["id"], arm=arm, seed=0, stage="formal",
                                 panel=dict(role, instance_path=role["input_path"]),
                                 destination=str(destination), cap_seconds=role["cap_seconds"],
                                 hard_stop_seconds=role["cap_seconds"] - 2, command=command))
    assert [f'{x["id"]}/{x["arm"]}' for x in launches] == list(ORDER)
    assert sum(x["cap_seconds"] for x in launches) == 13500
    assert len({x["destination"] for x in launches}) == 12
    for role in prereg["roles"]:
        pair = [x["command"] for x in launches if x["id"] == role["id"] and x["arm"] != "P-GRB"]
        left, right = [c.copy() for c in pair]
        replace_option(left, "--round90-lp-g-split", "<split>")
        replace_option(right, "--round90-lp-g-split", "<split>")
        # The per-arm destination changes only artifact paths, not solver policy.
        for flag in ("--out", "--log", "--process-phase-ledger", "--external-gini-artifact-dir",
                     "--primal-heuristic-generation-log", "--progress-log", "--native-evidence-dir"):
            replace_option(left, flag, "<artifact>")
            replace_option(right, flag, "<artifact>")
        assert left == right, role["id"]
    return launches


def qualification_launches(prereg: dict, r90) -> list[dict]:
    launches = []
    for number, role in enumerate(prereg["roles"], 1):
        destination = CAMPAIGN / "qualification" / f'{number:02d}_{role["id"]}_P-GRB'
        command = r90.audited_runner_utilities.command_for(prereg, role, "P-GRB", destination)
        for flag in ("--time-limit", "--process-wall-time-limit", "--process-shutdown-margin"):
            replace_option(command, flag, 0)
        assert "--algorithm-preset" not in command and "--round90-lp-g-split" not in command
        launches.append(dict(number=number, id=role["id"], arm="P-GRB", panel=role,
                             destination=str(destination), external_cap_seconds=15,
                             expected_optimize_calls=1, formal_timing=False, command=command))
    assert [x["id"] for x in launches] == list(REFERENCE_IDS)
    return launches


def prepare(prereg: dict, d6, priority, r90, old: dict) -> None:
    started = time.perf_counter()
    baseline, g3, rows = validate(prereg, d6, priority, r90, old)
    formal, qualification = formal_launches(prereg, r90, g3), qualification_launches(prereg, r90)
    assert not CAMPAIGN.exists(), "Never overwrite prepared or paid R94 prefix"
    assert not r90.foreign_heavy_processes(), "Heavy solver/build process active"
    blobs = d6.audit_preserved_blobs(rows, prereg["source_preservation_ref"])
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    snapshot_path = CAMPAIGN / "source_snapshot_receipt.json"
    r90.write_new(snapshot_path, dict(schema="round94-source-snapshot-v1", optimizer_calls=0,
                                      source_preservation_ref=prereg["source_preservation_ref"],
                                      source_manifest_sha256=old["source_manifest_sha256"],
                                      verified_blob_count=len(blobs), all_byte_hashes_match=True, blobs=blobs))
    identity = dict(schema="round94-lpg-contemporary-identity-v1", optimizer_calls=0,
                    prereg_sha256=sha(PREREG), runner_sha256=sha(Path(__file__)),
                    plan_sha256=prereg["plan_sha256"], source_preservation_ref=prereg["source_preservation_ref"],
                    source_snapshot_sha256=sha(snapshot_path), source_hashes=baseline["source_hashes"],
                    old_harness_hashes=baseline["harness_hashes"],
                    candidate_binary_sha256=prereg["candidate_binary_sha256"],
                    qualification_launches=qualification, formal_launches=formal,
                    prepared_unix=time.time())
    r90.write_new(CAMPAIGN / "identity.json", identity)
    r90.write_new(CAMPAIGN / "preflight.json", dict(schema="round94-preflight-v1", optimizer_calls=0,
                    formal_runs=12, formal_process_caps_seconds=13500,
                    qualification_processes=4, qualification_process_caps_seconds=60,
                    git_source_blobs_verified=len(blobs), canonical_inputs_verified=4,
                    identity_sha256=sha(CAMPAIGN / "identity.json"),
                    prepare_elapsed_before_receipt_seconds=time.perf_counter() - started,
                    disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
                    memory_available_bytes=r90.memory_available(),
                    note="Prepare starts no ExactEBRP process and grants neither qualification nor formal Optimize."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def require_prepared(prereg: dict, d6, priority, r90, old: dict) -> dict:
    baseline, g3, _ = validate(prereg, d6, priority, r90, old)
    path = CAMPAIGN / "identity.json"
    identity = read(path)
    assert identity["schema"] == "round94-lpg-contemporary-identity-v1"
    assert identity["prereg_sha256"] == sha(PREREG) and identity["runner_sha256"] == sha(Path(__file__))
    assert identity["plan_sha256"] == prereg["plan_sha256"]
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["source_hashes"] == baseline["source_hashes"]
    assert identity["old_harness_hashes"] == baseline["harness_hashes"]
    assert sha(CAMPAIGN / "source_snapshot_receipt.json") == identity["source_snapshot_sha256"]
    assert identity["qualification_launches"] == qualification_launches(prereg, r90)
    assert identity["formal_launches"] == formal_launches(prereg, r90, g3)
    return identity


def parameter_readback(result: dict, *, require_call: bool, arm: str) -> dict:
    names = {"threads": 1, "seed": 0, "presolve": -1,
             "mip_gap": 0.0, "mip_gap_abs": 0.0}
    if require_call:
        for name, expected in names.items():
            prefix = "gurobi_" + name
            for suffix in ("requested", "effective"):
                assert result[prefix + "_" + suffix] == expected, (prefix, suffix)
            assert result[prefix + "_set_return_code"] == 0, prefix
            assert result[prefix + "_get_return_code"] == 0, prefix
        if arm == "P-GRB":
            assert result["gurobi_version"] == "13.0.2"
            assert result["native_mip_strict_gap_parameters_valid"] is True
        else:
            assert arm in {"ENS-C", "LP-G"}
            assert result["external_gini_tree_backend_parameter_roundtrip_valid"] is True
    return {name: {suffix: result["gurobi_" + name + "_" + suffix]
                   for suffix in ("requested", "effective", "set_return_code", "get_return_code")}
            for name in names} if require_call else {}


def audit_adapter(r90):
    original = r90.audit_launch
    r88 = r90.audited_runner_utilities
    expected_settings = dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1,
                             MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6,
                             IntFeasTol=1e-5, OptimalityTol=1e-6)

    def audit(launch: dict, observations: list[dict], completion: dict, identity: dict) -> dict:
        destination = Path(launch["destination"])
        calls = [row["payload"] for row in observations if row["payload"]["kind"] == "call"]
        for call in calls:
            assert native_true(call["native_preconditions"]), "native parameter/domain preconditions failed"
            assert call["settings"] == expected_settings, "journal native parameter readback differs"
        if launch["arm"] == "P-GRB":
            assert len(calls) <= 1, "P has more than one native model call"
            compact = destination / "compact.lp"
            assert compact.is_file() and sha(compact) == launch["panel"]["reference"]["canonical_sha256"]
            audited = r88.audit_launch(launch, observations, completion, identity)
            assert audited.get("lp_g_split_evidence") is None
        else:
            audited = original(launch, observations, completion, identity)
        if completion["stop_reason"] == "normal_return":
            result = read(destination / "result.json")
            if launch["arm"] == "P-GRB":
                assert result["method"] == "gurobi" and result["algorithm_preset"] == "custom"
                assert result["gurobi_hga_start_requested"] is False
                assert result["gurobi_optimize_count"] == 1
                assert result["gurobi_model_fingerprint"] == launch["panel"]["reference"]["fingerprint"]
                assert result["gurobi_canonical_model_sha256"] == launch["panel"]["reference"]["canonical_sha256"]
                assert result["gurobi_num_vars"] == launch["panel"]["reference"]["columns"]
                assert result["gurobi_num_constrs"] == launch["panel"]["reference"]["rows"]
                assert result["gurobi_native_domain_audit_passed"] is True
            audited["five_native_parameter_readback"] = parameter_readback(
                result, require_call=bool(calls), arm=launch["arm"])
            if launch["arm"] == "P-GRB":
                assert calls, "P returned without native call receipt"
        audited["passed"] = True
        return audited

    return audit


def qualification_journal_audit(r90, launch: dict) -> dict:
    destination = Path(launch["destination"])
    journal = destination / "journal"
    commits = sorted(journal.glob("event_*.commit"),
                     key=lambda path: int(path.stem.removeprefix("event_")))
    assert commits, "P qualification has no committed native journal"
    assert [path.name for path in commits] == [f"event_{i}.commit" for i in range(1, len(commits) + 1)]
    records = [r90.evidence.receipt(path, 0.0, 15.0) for path in commits]
    calls = [row["payload"] for row in records if row["payload"]["kind"] == "call"]
    assert len(calls) == 1 and native_true(calls[0]["full_original"])
    assert native_true(calls[0]["native_preconditions"])
    assert calls[0]["settings"] == dict(read_return_code=0, Threads=1, Seed=0,
                                      Presolve=-1, MIPGap=0, MIPGapAbs=0,
                                      FeasibilityTol=1e-6, IntFeasTol=1e-5,
                                      OptimalityTol=1e-6)
    panel = dict(launch["panel"], instance_path=launch["panel"]["input_path"])
    audited = r90.evidence.audit(ROOT, panel, records,
                                 sha(ROOT / "build/research/round90-lp-g-split/ExactEBRP.exe"))
    assert audited["native_calls_started"] == audited["native_calls_returned"] == 1
    return dict(committed_events=len(records), native_calls_started=1,
                native_calls_returned=1, original_scope=True,
                physical_witnesses=audited["physical_witnesses"],
                global_bound_events=audited["global_native_bound_events"])


def native_true(value: object) -> bool:
    """The frozen NEJ1 C++ writer encodes scope flags as JSON integer 1."""
    return value is True or (type(value) is int and value == 1)


def preserved_f2_manifest() -> list[dict]:
    folder = CAMPAIGN / "qualification/01_F2_P-GRB"
    assert folder.is_dir()
    files = sorted(path for path in folder.rglob("*") if path.is_file())
    assert files
    return [dict(path=path.relative_to(folder).as_posix(), size_bytes=path.stat().st_size,
                 sha256=sha(path)) for path in files]


def recovery_contract(prereg: dict) -> tuple[dict, dict]:
    repair = read(RECOVERY_PREREG)
    assert repair["schema"] == "round94-qualification-recovery-preregistration-v2"
    assert repair["status"] == "source_only_no_new_native_authorization"
    assert repair["recovery_root"] == RECOVERY.relative_to(ROOT).as_posix()
    assert repair["remaining_qualification_roles"] == ["C20", "B50", "U6"]
    assert repair["remaining_original_launch_numbers"] == [2, 3, 4]
    assert repair["remaining_external_process_cap_seconds_each"] == 15
    assert repair["remaining_maximum_process_seconds"] == 45
    assert repair["original_preregistration_sha256"] == sha(PREREG)
    assert repair["original_preregistration_sha256"] == "767b8abe628bb5e84c8c44ddf2b65869f44212e17bea362fc0284b4afb445774"
    preserved = {
        "original_identity_sha256": CAMPAIGN / "identity.json",
        "original_qualification_completion_sha256": CAMPAIGN / "qualification_completion.json",
        "original_qualification_failure_sha256": CAMPAIGN / "qualification_failure_01.json",
        "preserved_f2_completion_sha256": CAMPAIGN / "qualification/01_F2_P-GRB/completion.json",
        "preserved_f2_result_sha256": CAMPAIGN / "qualification/01_F2_P-GRB/result.json",
    }
    for key, path in preserved.items():
        assert sha(path) == repair[key], key
    old_source = subprocess.check_output(
        ["git", "show", repair["original_source_commit"] + ":scripts/round94_lpg_contemporary.py"],
        cwd=ROOT)
    assert hashlib.sha256(old_source).hexdigest() == repair["original_runner_sha256"]
    original = read(CAMPAIGN / "identity.json")
    assert original["runner_sha256"] == repair["original_runner_sha256"]
    assert original["prereg_sha256"] == repair["original_preregistration_sha256"]
    failed = read(CAMPAIGN / "qualification_completion.json")
    assert failed["passed"] is False and failed["attempted"] == ["F2"]
    assert failed["not_run"] == repair["remaining_qualification_roles"]
    assert failed["completed"] == 0 and failed["records"] == []
    f2_completion = read(CAMPAIGN / "qualification/01_F2_P-GRB/completion.json")
    assert f2_completion["reason"] == "normal_return" and f2_completion["returncode"] == 0
    assert f2_completion["whole_process_wall_seconds"] == repair["original_paid_f2_process_wall_seconds"]
    assert failed["outer_wall_seconds"] == repair["original_paid_qualification_outer_wall_seconds"]
    assert failed["full_invocation_wall_before_write_seconds"] == repair["original_paid_full_invocation_wall_before_receipt_seconds"]
    assert original["qualification_launches"][0]["id"] == "F2"
    assert [x["id"] for x in original["qualification_launches"][1:]] == repair["remaining_qualification_roles"]
    assert [x["number"] for x in original["qualification_launches"][1:]] == [2, 3, 4]
    assert all(x["external_cap_seconds"] == 15 for x in original["qualification_launches"])
    assert original["formal_launches"] and len(original["formal_launches"]) == 12
    return repair, original


def verify_preserved_f2(r90, original: dict) -> dict:
    launch = original["qualification_launches"][0]
    destination = Path(launch["destination"])
    assert read(destination / "launch.json") == launch
    result = read(destination / "result.json")
    reference = launch["panel"]["reference"]
    compact = destination / "compact.lp"
    assert sha(compact) == reference["canonical_sha256"]
    assert result["gurobi_canonical_model_sha256"] == reference["canonical_sha256"]
    assert result["gurobi_model_fingerprint"] == reference["fingerprint"]
    assert result["gurobi_num_vars"] == reference["columns"]
    assert result["gurobi_num_constrs"] == reference["rows"]
    assert result["gurobi_native_domain_audit_passed"] is True
    assert result["gurobi_optimize_count"] == 1 and result["gurobi_optimize_return_code"] == 0
    assert result["gurobi_lifecycle_valid"] is True
    assert result["gurobi_hga_start_requested"] is False
    assert result["method"] == "gurobi" and result["algorithm_preset"] == "custom"
    parameters = parameter_readback(result, require_call=True, arm="P-GRB")
    journal = qualification_journal_audit(r90, launch)
    assert journal["committed_events"] == 3
    return dict(schema="round94-offline-f2-requalification-v2", role="F2", passed=True,
                original_qualification_processes_started=1, new_processes_started=0,
                original_native_optimize_calls_verified=1, new_native_optimize_calls=0,
                search_result_excluded=True, preserved_result_sha256=sha(destination / "result.json"),
                compact_sha256=sha(compact), native_fingerprint=result["gurobi_model_fingerprint"],
                native_domain_passed=True, native_parameters=parameters, native_journal=journal,
                original_whole_process_wall_seconds=read(destination / "completion.json")["whole_process_wall_seconds"])


def repair_prepare(prereg: dict, d6, priority, r90, old: dict) -> None:
    started = time.perf_counter()
    baseline, g3, _ = validate(prereg, d6, priority, r90, old)
    repair, original = recovery_contract(prereg)
    assert original["qualification_launches"] == qualification_launches(prereg, r90)
    assert original["formal_launches"] == formal_launches(prereg, r90, g3)
    assert not RECOVERY.exists(), "Never replace recovery identity or offline audit"
    assert not (CAMPAIGN / "formal_started.json").exists()
    assert all(not Path(row["destination"]).exists() for row in original["qualification_launches"][1:])
    assert not r90.foreign_heavy_processes()
    manifest = preserved_f2_manifest()
    audited = verify_preserved_f2(r90, original)
    RECOVERY.mkdir(parents=True, exist_ok=False)
    r90.write_new(RECOVERY / "preserved_f2_file_manifest.json", dict(
        schema="round94-preserved-f2-raw-manifest-v2", directory=repair["preserved_f2_relative_directory"],
        file_count=len(manifest), files=manifest))
    r90.write_new(RECOVERY / "offline_f2_audit.json", audited)
    identity = dict(schema="round94-recovery-identity-v2", optimizer_calls=0,
                    recovery_prereg_sha256=sha(RECOVERY_PREREG),
                    original_identity_sha256=repair["original_identity_sha256"],
                    original_qualification_completion_sha256=repair["original_qualification_completion_sha256"],
                    original_qualification_failure_sha256=repair["original_qualification_failure_sha256"],
                    original_source_commit=repair["original_source_commit"],
                    original_runner_sha256=repair["original_runner_sha256"],
                    prereg_sha256=sha(PREREG), runner_sha256=sha(Path(__file__)),
                    candidate_binary_sha256=prereg["candidate_binary_sha256"],
                    source_snapshot_sha256=original["source_snapshot_sha256"],
                    source_hashes=baseline["source_hashes"], old_harness_hashes=baseline["harness_hashes"],
                    preserved_f2_file_manifest_sha256=sha(RECOVERY / "preserved_f2_file_manifest.json"),
                    offline_f2_audit_sha256=sha(RECOVERY / "offline_f2_audit.json"),
                    qualification_launches=original["qualification_launches"][1:],
                    formal_launches=original["formal_launches"],
                    prepared_unix=time.time())
    r90.write_new(RECOVERY / "identity.json", identity)
    r90.write_new(RECOVERY / "preflight.json", dict(
        schema="round94-recovery-preflight-v2", new_optimize_calls=0,
        preserved_f2_original_optimize_calls_verified=1, preserved_f2_passed=True,
        remaining_qualification_processes=3, remaining_qualification_process_caps_seconds=45,
        formal_runs=12, formal_process_caps_seconds=13500,
        identity_sha256=sha(RECOVERY / "identity.json"),
        prepare_elapsed_before_receipt_seconds=time.perf_counter() - started,
        note="Offline requalification only; requires new root lease for three remaining native diagnostics."))
    print(json.dumps(dict(recovery_prepared=True, new_optimize_calls=0,
                          preserved_f2_verified=True, remaining_qualification_processes=3)), flush=True)


def require_recovery(prereg: dict, d6, priority, r90, old: dict) -> dict:
    baseline, g3, _ = validate(prereg, d6, priority, r90, old)
    repair, original = recovery_contract(prereg)
    manifest_path = RECOVERY / "preserved_f2_file_manifest.json"
    manifest = read(manifest_path)
    assert manifest["schema"] == "round94-preserved-f2-raw-manifest-v2"
    assert manifest["directory"] == repair["preserved_f2_relative_directory"]
    assert manifest["files"] == preserved_f2_manifest()
    assert manifest["file_count"] == len(manifest["files"])
    offline = read(RECOVERY / "offline_f2_audit.json")
    assert offline == verify_preserved_f2(r90, original) and offline["passed"] is True
    identity = read(RECOVERY / "identity.json")
    assert identity["schema"] == "round94-recovery-identity-v2"
    assert identity["recovery_prereg_sha256"] == sha(RECOVERY_PREREG)
    assert identity["original_identity_sha256"] == repair["original_identity_sha256"]
    assert identity["original_qualification_completion_sha256"] == repair["original_qualification_completion_sha256"]
    assert identity["original_qualification_failure_sha256"] == repair["original_qualification_failure_sha256"]
    assert identity["original_runner_sha256"] == repair["original_runner_sha256"]
    assert identity["runner_sha256"] == sha(Path(__file__))
    assert identity["prereg_sha256"] == sha(PREREG)
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["source_snapshot_sha256"] == original["source_snapshot_sha256"]
    assert identity["source_hashes"] == baseline["source_hashes"]
    assert identity["old_harness_hashes"] == baseline["harness_hashes"]
    assert identity["preserved_f2_file_manifest_sha256"] == sha(manifest_path)
    assert identity["offline_f2_audit_sha256"] == sha(RECOVERY / "offline_f2_audit.json")
    assert identity["qualification_launches"] == original["qualification_launches"][1:]
    assert identity["formal_launches"] == formal_launches(prereg, r90, g3)
    return identity


def cross_arm(r90, records: list[dict], role: str) -> dict:
    same = {row["arm"]: row for row in records if row["id"] == role}
    assert 2 <= len(same) <= 3 and set(same) <= {"P-GRB", "ENS-C", "LP-G"}
    lowers, uppers, arms = [], [], []
    for arm in ("P-GRB", "ENS-C", "LP-G"):
        if arm not in same:
            continue
        record = same[arm]
        audit = read(Path(record["destination"]) / "audit.json")
        assert audit["passed"] is True
        endpoint = record["endpoint"]
        assert endpoint is not None
        lower = max(x for x in (audit["LB"], endpoint["L"]) if x is not None)
        physical = [w["F"] for w in audit["witnesses"]]
        if audit.get("final_physical_verification") is not None:
            physical.append(audit["final_physical_verification"]["F"])
        upper = min(physical) if physical else None
        lowers.append(lower)
        if upper is not None:
            uppers.append(upper)
        arms.append(dict(arm=arm, strongest_global_L=lower, minimum_physical_U=upper,
                         physical_witness_rows=len(audit["witnesses"])))
    strongest, weakest = max(lowers), min(uppers) if uppers else None
    passed = weakest is None or strongest <= weakest + 1e-7
    result = dict(schema="round94-cross-bound-v1", role=role,
                  compared_arms=[x["arm"] for x in arms],
                  strongest_global_L=strongest, minimum_physical_U=weakest,
                  tolerance=1e-7, passed=passed, arms=arms,
                  scope="offline contradiction only; no merged algorithm endpoint")
    r90.write_new(CAMPAIGN / f"cross_arm_{role}_{len(same)}.json", result)
    assert passed, f"cross-arm original-problem bound contradiction: {role}"
    return result


def severe_signals(records: list[dict], role: str) -> list[dict]:
    same = {row["arm"]: row for row in records if row["id"] == role}
    candidate = same.get("LP-G")
    if candidate is None:
        return []
    result = []
    for comparator in ("ENS-C", "P-GRB"):
        reference = same.get(comparator)
        if reference is None:
            continue
        c, r = candidate["endpoint"], reference["endpoint"]
        assert c is not None and r is not None
        ct = candidate["completion"]["process_wall_seconds"]
        rt = reference["completion"]["process_wall_seconds"]
        slower = ct > 1.5 * rt and ct - rt > 30
        if r["certificate"] and c["certificate"] and slower:
            result.append(dict(kind="severe_certification_time", reference=comparator, role=role))
        elif r["certificate"] and not c["certificate"]:
            if comparator == "P-GRB" or slower:
                result.append(dict(kind="P_certificate_LP_open_promotion_blocker" if comparator == "P-GRB"
                                   else "severe_reference_certificate_LP_censored", reference=comparator,
                                   role=role, severe_censoring=slower))
        elif not r["certificate"] and not c["certificate"]:
            if all(x is not None and math.isfinite(x) for x in (c["U"], c["L"], r["U"], r["L"])):
                cg, rg = c["U"] - c["L"], r["U"] - r["L"]
                assert cg >= -1e-7 and rg >= -1e-7
                cg, rg = max(0.0, cg), max(0.0, rg)
                if cg > 1.5 * rg and cg - rg > 0.01:
                    result.append(dict(kind="severe_open_absolute_gap", reference=comparator,
                                       role=role, lp_gap=cg, reference_gap=rg))
    return result


def lease(prereg: dict, identity: dict, name: str, schema: str, count: int) -> Path:
    path = CAMPAIGN / name
    content = read(path)
    assert content == dict(schema=schema, authorized_by="root", allow_optimize=True,
                           identity_sha256=sha(CAMPAIGN / "identity.json"), planned_processes=count)
    return path


def qualify(prereg: dict, d6, priority, r90, old: dict) -> None:
    invocation = time.perf_counter()
    identity = require_prepared(prereg, d6, priority, r90, old)
    lease_path = lease(prereg, identity, "qualification_lease.json", "round94-qualification-lease-v1", 4)
    assert not (CAMPAIGN / "qualification_started.json").exists()
    assert not (CAMPAIGN / "qualification_completion.json").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["qualification_launches"])
    assert not r90.foreign_heavy_processes()
    r90.write_new(CAMPAIGN / "qualification_started.json", dict(
        identity_sha256=sha(CAMPAIGN / "identity.json"), lease_sha256=sha(lease_path),
        started_unix=time.time(), native_optimize_calls_planned=4,
        preflight_wall_seconds=time.perf_counter() - invocation))
    started = time.perf_counter()
    completed, error = [], None
    active_launch: dict | None = None
    active_started: float | None = None
    try:
        for launch in identity["qualification_launches"]:
            active_launch = launch
            destination = Path(launch["destination"])
            assert not r90.foreign_heavy_processes()
            destination.mkdir(parents=True, exist_ok=False)
            r90.write_new(destination / "launch.json", launch)
            began = time.perf_counter()
            active_started = began
            reason, returncode = "normal_return", None
            env = dict(os.environ)
            env["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + env.get("PATH", "")
            with r90.affinity.inherited_core(prereg["common"]["affinity_mask"]) as binding:
                with (destination / "stdout.log").open("x") as out, (destination / "stderr.log").open("x") as err:
                    child = subprocess.Popen(launch["command"], cwd=ROOT, env=env, stdout=out, stderr=err)
                    try:
                        mask = r90.affinity.read_masks(child.pid)
                        assert mask["process_mask"] == prereg["common"]["affinity_mask"]
                        r90.write_new(destination / "affinity.json", dict(parent=binding, child=mask, pid=child.pid))
                        child.wait(timeout=max(0.001, 15 - (time.perf_counter() - began)))
                    except subprocess.TimeoutExpired:
                        reason = "external_whole_process_cap"
                        child.kill()
                        child.wait()
                    finally:
                        if child.poll() is None:
                            child.kill()
                            child.wait()
                    returncode = child.returncode
            elapsed = time.perf_counter() - began
            completion = dict(schema="round94-qualification-process-v1", role=launch["id"],
                              whole_process_wall_seconds=elapsed, cap_seconds=15,
                              reason=reason, returncode=returncode, ended_unix=time.time())
            r90.write_new(destination / "completion.json", completion)
            assert reason == "normal_return" and returncode == 0 and elapsed <= 15
            result = read(destination / "result.json")
            compact = destination / "compact.lp"
            ref = launch["panel"]["reference"]
            assert compact.is_file() and sha(compact) == ref["canonical_sha256"]
            assert result["gurobi_canonical_model_sha256"] == ref["canonical_sha256"]
            assert result["gurobi_model_fingerprint"] == ref["fingerprint"]
            assert result["gurobi_num_vars"] == ref["columns"] and result["gurobi_num_constrs"] == ref["rows"]
            assert result["gurobi_native_domain_audit_passed"] is True
            assert result["gurobi_optimize_count"] == 1 and result["gurobi_hga_start_requested"] is False
            assert result["gurobi_lifecycle_valid"] is True
            assert result["method"] == "gurobi" and result["algorithm_preset"] == "custom"
            assert result["gurobi_optimize_return_code"] == 0
            parameters = parameter_readback(result, require_call=True, arm="P-GRB")
            journal_audit = qualification_journal_audit(r90, launch)
            receipt = dict(schema="round94-qualification-audit-v1", role=launch["id"], passed=True,
                           official_benchmark_run=False, native_optimize_calls=1,
                           search_result_excluded=True, compact_sha256=sha(compact),
                           result_sha256=sha(destination / "result.json"),
                           native_fingerprint=result["gurobi_model_fingerprint"],
                           native_domain_passed=True, native_parameters=parameters,
                           native_journal=journal_audit)
            r90.write_new(destination / "audit.json", receipt)
            completed.append(dict(role=launch["id"], completion=completion, audit=receipt))
            active_launch = None
            active_started = None
    except Exception as exc:
        error = repr(exc)
        if active_launch is not None:
            destination = Path(active_launch["destination"])
            r90.write_new(CAMPAIGN / f'qualification_failure_{active_launch["number"]:02d}.json', dict(
                schema="round94-qualification-failure-v1", role=active_launch["id"],
                error=error, destination=str(destination), destination_exists=destination.exists(),
                result_exists=(destination / "result.json").is_file(),
                completion_exists=(destination / "completion.json").is_file(),
                attempted_wall_lower_bound_seconds=(time.perf_counter() - active_started)
                if active_started is not None else None,
                native_optimize_calls="unknown_without_valid_final_receipt",
                requires_independent_review=True, recorded_unix=time.time()))
        raise
    finally:
        attempted = [x["id"] for x in identity["qualification_launches"]
                     if Path(x["destination"]).exists()]
        r90.write_new(CAMPAIGN / "qualification_completion.json", dict(
            schema="round94-qualification-completion-v1", planned=4, completed=len(completed),
            passed=error is None and len(completed) == 4, error=error,
            attempted=attempted, not_run=[rid for rid in REFERENCE_IDS if rid not in attempted],
            records=completed,
            outer_wall_seconds=time.perf_counter() - started,
            full_invocation_wall_before_write_seconds=time.perf_counter() - invocation,
            actual_optimize_calls_confirmed=sum(x["audit"]["native_optimize_calls"] for x in completed),
            actual_optimize_calls_total="unknown_if_failed" if error is not None else 4,
            attempted_processes=len(attempted),
            ended_unix=time.time()))


def qualify_recovery(prereg: dict, d6, priority, r90, old: dict) -> None:
    invocation = time.perf_counter()
    identity = require_recovery(prereg, d6, priority, r90, old)
    lease_path = RECOVERY / "remaining_qualification_lease.json"
    assert read(lease_path) == dict(
        schema="round94-recovery-remaining-qualification-lease-v2",
        authorized_by="root", allow_optimize=True,
        recovery_identity_sha256=sha(RECOVERY / "identity.json"),
        preserved_f2_audit_sha256=sha(RECOVERY / "offline_f2_audit.json"),
        planned_processes=3, execution_order=["C20", "B50", "U6"])
    assert not (RECOVERY / "qualification_started.json").exists()
    assert not (RECOVERY / "qualification_completion.json").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["qualification_launches"])
    assert not r90.foreign_heavy_processes()
    r90.write_new(RECOVERY / "qualification_started.json", dict(
        recovery_identity_sha256=sha(RECOVERY / "identity.json"), lease_sha256=sha(lease_path),
        preserved_f2_audit_sha256=sha(RECOVERY / "offline_f2_audit.json"),
        started_unix=time.time(), native_optimize_calls_planned=3,
        preflight_wall_seconds=time.perf_counter() - invocation))
    started = time.perf_counter()
    completed, error = [], None
    active: dict | None = None
    active_started: float | None = None
    try:
        for launch in identity["qualification_launches"]:
            active = launch
            destination = Path(launch["destination"])
            assert not r90.foreign_heavy_processes()
            destination.mkdir(parents=True, exist_ok=False)
            r90.write_new(destination / "launch.json", launch)
            began = time.perf_counter()
            active_started = began
            reason, returncode = "normal_return", None
            env = dict(os.environ)
            env["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + env.get("PATH", "")
            with r90.affinity.inherited_core(prereg["common"]["affinity_mask"]) as binding:
                with (destination / "stdout.log").open("x") as out, (destination / "stderr.log").open("x") as err:
                    child = subprocess.Popen(launch["command"], cwd=ROOT, env=env, stdout=out, stderr=err)
                    try:
                        mask = r90.affinity.read_masks(child.pid)
                        assert mask["process_mask"] == prereg["common"]["affinity_mask"]
                        r90.write_new(destination / "affinity.json", dict(parent=binding, child=mask, pid=child.pid))
                        child.wait(timeout=max(0.001, 15 - (time.perf_counter() - began)))
                    except subprocess.TimeoutExpired:
                        reason = "external_whole_process_cap"
                        child.kill()
                        child.wait()
                    finally:
                        if child.poll() is None:
                            child.kill()
                            child.wait()
                    returncode = child.returncode
            elapsed = time.perf_counter() - began
            completion = dict(schema="round94-recovery-qualification-process-v2", role=launch["id"],
                              whole_process_wall_seconds=elapsed, cap_seconds=15,
                              reason=reason, returncode=returncode, ended_unix=time.time())
            r90.write_new(destination / "completion.json", completion)
            assert reason == "normal_return" and returncode == 0 and elapsed <= 15
            result = read(destination / "result.json")
            compact = destination / "compact.lp"
            ref = launch["panel"]["reference"]
            assert compact.is_file() and sha(compact) == ref["canonical_sha256"]
            assert result["gurobi_canonical_model_sha256"] == ref["canonical_sha256"]
            assert result["gurobi_model_fingerprint"] == ref["fingerprint"]
            assert result["gurobi_num_vars"] == ref["columns"] and result["gurobi_num_constrs"] == ref["rows"]
            assert result["gurobi_native_domain_audit_passed"] is True
            assert result["gurobi_optimize_count"] == 1 and result["gurobi_optimize_return_code"] == 0
            assert result["gurobi_lifecycle_valid"] is True
            assert result["gurobi_hga_start_requested"] is False
            assert result["method"] == "gurobi" and result["algorithm_preset"] == "custom"
            parameters = parameter_readback(result, require_call=True, arm="P-GRB")
            journal = qualification_journal_audit(r90, launch)
            receipt = dict(schema="round94-recovery-qualification-audit-v2", role=launch["id"], passed=True,
                           official_benchmark_run=False, native_optimize_calls=1,
                           search_result_excluded=True, compact_sha256=sha(compact),
                           result_sha256=sha(destination / "result.json"),
                           native_fingerprint=result["gurobi_model_fingerprint"],
                           native_domain_passed=True, native_parameters=parameters,
                           native_journal=journal)
            r90.write_new(destination / "audit.json", receipt)
            completed.append(dict(role=launch["id"], completion=completion, audit=receipt))
            active = None
            active_started = None
    except Exception as exc:
        error = repr(exc)
        if active is not None:
            destination = Path(active["destination"])
            r90.write_new(RECOVERY / f'qualification_failure_{active["number"]:02d}.json', dict(
                schema="round94-recovery-qualification-failure-v2", role=active["id"],
                error=error, destination=str(destination), destination_exists=destination.exists(),
                result_exists=(destination / "result.json").is_file(),
                completion_exists=(destination / "completion.json").is_file(),
                attempted_wall_lower_bound_seconds=(time.perf_counter() - active_started)
                if active_started is not None else None,
                native_optimize_calls="unknown_without_valid_final_receipt",
                requires_independent_review=True, recorded_unix=time.time()))
        raise
    finally:
        attempted = [x["id"] for x in identity["qualification_launches"]
                     if Path(x["destination"]).exists()]
        r90.write_new(RECOVERY / "qualification_completion.json", dict(
            schema="round94-recovery-qualification-completion-v2", planned_remaining=3,
            completed_remaining=len(completed),
            passed=error is None and len(completed) == 3,
            preserved_f2_passed=True, verified_total_identity_qualifications=1 + len(completed),
            original_f2_native_optimize_calls_verified=1,
            remaining_native_optimize_calls_confirmed=sum(x["audit"]["native_optimize_calls"] for x in completed),
            native_optimize_calls_total="unknown_if_failed" if error is not None else 4,
            original_f2_whole_process_wall_seconds=read(CAMPAIGN / "qualification/01_F2_P-GRB/completion.json")["whole_process_wall_seconds"],
            remaining_paid_process_wall_seconds_with_receipt=sum(x["completion"]["whole_process_wall_seconds"] for x in completed),
            error=error, attempted=attempted,
            not_run=[rid for rid in ("C20", "B50", "U6") if rid not in attempted],
            records=completed, outer_wall_seconds=time.perf_counter() - started,
            full_invocation_wall_before_write_seconds=time.perf_counter() - invocation,
            ended_unix=time.time()))


def run(prereg: dict, d6, priority, r90, old: dict) -> None:
    invocation = time.perf_counter()
    identity = require_recovery(prereg, d6, priority, r90, old)
    qualification_path = RECOVERY / "qualification_completion.json"
    qualification = read(qualification_path)
    assert qualification["schema"] == "round94-recovery-qualification-completion-v2"
    assert qualification["passed"] is True and qualification["planned_remaining"] == qualification["completed_remaining"] == 3
    assert qualification["verified_total_identity_qualifications"] == 4
    assert qualification["native_optimize_calls_total"] == 4
    lease_path = RECOVERY / "formal_lease.json"
    expected_lease = dict(schema="round94-formal-after-recovery-lease-v2", authorized_by="root", allow_optimize=True,
                          recovery_identity_sha256=sha(RECOVERY / "identity.json"),
                          qualification_completion_sha256=sha(qualification_path),
                          planned_processes=12)
    assert read(lease_path) == expected_lease
    assert not (RECOVERY / "formal_started.json").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["formal_launches"])
    assert not r90.foreign_heavy_processes()
    r90.CAMPAIGN = CAMPAIGN  # Scoped to this imported G3 module, not the frozen file.
    r90.audit_launch = audit_adapter(r90)  # Its original ENS/LP audit is called inside.
    r90.write_new(RECOVERY / "formal_started.json", dict(
        recovery_identity_sha256=sha(RECOVERY / "identity.json"), lease_sha256=sha(lease_path),
        qualification_completion_sha256=sha(qualification_path),
        preflight_wall_seconds=time.perf_counter() - invocation, started_unix=time.time()))
    started = time.perf_counter()
    records, error = [], None
    try:
        for launch in identity["formal_launches"]:
            attempt_started = time.perf_counter()
            try:
                record = r90.run_one(launch, prereg, identity)
                records.append(record)
            except Exception as exc:
                r90.write_new(CAMPAIGN / f'failure_{launch["number"]:02d}.json', dict(
                    schema="round94-formal-failure-v1", number=launch["number"], role=launch["id"],
                    arm=launch["arm"], error=repr(exc), destination=launch["destination"],
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination_exists=Path(launch["destination"]).exists(),
                    completion_exists=(Path(launch["destination"]) / "completion.json").is_file(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            same = [x for x in records if x["id"] == launch["id"]]
            if len(same) >= 2:
                cross_arm(r90, same, launch["id"])
            signals = severe_signals(same, launch["id"])
            if signals:
                r90.write_new(CAMPAIGN / f'risk_stop_{launch["id"]}.json', dict(
                    role=launch["id"], signals=signals, summary_sha256=sha(CAMPAIGN / "summary.jsonl"),
                    research_signal_only=True, requires_independent_review=True))
                raise RuntimeError("Severe or promotion-blocking same-role comparison")
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        paid = [read(Path(x["destination"]) / "completion.json") for x in identity["formal_launches"]
                if (Path(x["destination"]) / "completion.json").is_file()]
        failures = [read(path) for path in sorted(CAMPAIGN.glob("failure_*.json"))]
        attempted = {x["number"] for x in identity["formal_launches"] if Path(x["destination"]).exists()}
        r90.write_new(RECOVERY / "formal_completion.json", dict(
            schema="round94-formal-after-recovery-completion-v2", planned=12, completed=len(records),
            error=error, attempted=sorted(attempted),
            not_run=[f'{x["id"]}/{x["arm"]}' for x in identity["formal_launches"]
                     if x["number"] not in attempted],
            paid_process_wall_seconds_with_receipt=sum(x["process_wall_seconds"] for x in paid),
            completed_process_receipts=len(paid), outer_wall_seconds=time.perf_counter() - started,
            precompletion_failed_attempt_elapsed_seconds=sum(x["attempt_elapsed_seconds"] for x in failures
                                                             if not x["completion_exists"]),
            total_process_wall_if_any_missing_receipt="unknown" if any(not x["completion_exists"] for x in failures)
                                                      else sum(x["process_wall_seconds"] for x in paid),
            full_invocation_wall_before_write_seconds=time.perf_counter() - invocation,
            ended_unix=time.time()))


def main() -> None:
    if not __debug__:
        raise RuntimeError("Python -O disables identity/lease assertions")
    assert len(sys.argv) == 2 and sys.argv[1] in {"repair-prepare", "qualify-recovery", "run"}, \
        "Usage: round94_lpg_contemporary.py repair-prepare|qualify-recovery|run"
    prereg = read(PREREG)
    d6, priority, r90, old = modules(prereg)
    if sys.argv[1] == "repair-prepare":
        repair_prepare(prereg, d6, priority, r90, old)
    elif sys.argv[1] == "qualify-recovery":
        qualify_recovery(prereg, d6, priority, r90, old)
    else:
        run(prereg, d6, priority, r90, old)


if __name__ == "__main__":
    main()
