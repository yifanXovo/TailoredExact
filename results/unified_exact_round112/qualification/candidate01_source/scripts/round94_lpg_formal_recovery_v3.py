"""Scope-aware R94 formal-prefix recovery; no native work in prepare.

The paid v2 P and ENS processes are immutable. A new root lease is required
before this file can run only the ten never-started original commands.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import round94_lpg_contemporary as v2


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = v2.CAMPAIGN
PREREG = ROOT / "results/unified_exact_round94/formal_recovery_preregistration_v3.json"
RECOVERY = CAMPAIGN / "formal_recovery_v3"
PREFIX = ("F2/P-GRB", "F2/ENS-C")
REMAINING = v2.ORDER[2:]
SETTINGS = dict(read_return_code=0, Threads=1, Seed=0, Presolve=-1,
                MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6,
                IntFeasTol=1e-5, OptimalityTol=1e-6)
MIP_KINDS = {"MIP", "CHILD_BOUND_TARGET_MIP", "NEXT_LEAF_TARGET_MIP",
             "PARTIAL_MIP_TARGET", "MIP_CONSOLIDATION_TARGET", "MIP_BLOCK"}


def flag(value: object) -> bool:
    """The frozen NEJ1 writer emits JSON integers; reject other coercions."""
    assert type(value) in (bool, int) and value in (0, 1, False, True), value
    return bool(value)


def ledger_rows(destination: Path) -> tuple[Path, list[dict]]:
    path = destination / "external/paper_optimize_ledger.csv"
    assert path.is_file(), f"missing native optimize ledger: {path}"
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames is not None
        assert {"leaf_id", "solve_kind", "model_sha256"} <= set(reader.fieldnames)
        rows = list(reader)
    assert all(None not in row and all(value is not None for value in row.values())
               for row in rows), "incomplete native optimize ledger"
    return path, rows


def scope_receipt(launch: dict, observations: list[dict]) -> dict:
    """Check call types/parameters; leave bound promotion to frozen R86/R90."""
    calls = [row["payload"] for row in observations if row["payload"]["kind"] == "call"]
    global_calls = {row["payload"]["call"] for row in observations
                    if row["payload"]["kind"] == "bound"
                    and flag(row["payload"]["global_available"])}
    destination = Path(launch["destination"])
    ledger_path, rows = (ledger_rows(destination) if launch["arm"] != "P-GRB" and calls
                         else (None, []))
    lp_calls, mip_calls = [], []
    for position, call in enumerate(calls, 1):
        assert type(call["call"]) is int and call["call"] == position
        full, preconditions = flag(call["full_original"]), flag(call["native_preconditions"])
        assert call["settings"] == SETTINGS, "native nine-setting readback differs"
        if full:
            assert preconditions, "full original call lacks native prerequisites"
        if launch["arm"] == "P-GRB":
            assert len(calls) <= 1 and full and preconditions
            continue
        assert position <= len(rows), "call has no same-position optimize ledger row"
        ledger = rows[position - 1]
        assert ledger["leaf_id"] == call["leaf"]
        assert ledger["model_sha256"] == call["model_sha256"]
        kind = ledger["solve_kind"]
        if kind == "LP":
            assert not full and not preconditions, "LP must use restricted 0/0 scope flags"
            assert call["call"] not in global_calls, "LP call published a global native bound"
            lp_calls.append(call["call"])
        else:
            assert kind in MIP_KINDS, f"unexpected native solve kind: {kind}"
            assert preconditions, "MIP call lacks native prerequisites"
            mip_calls.append(call["call"])
        if call["call"] in global_calls:
            assert preconditions and kind in MIP_KINDS
    return dict(schema="round94-native-scope-adapter-v3", arm=launch["arm"],
                native_calls=len(calls), lp_calls=lp_calls, mip_calls=mip_calls,
                global_bound_call_ids=sorted(global_calls),
                ledger_sha256=v2.sha(ledger_path) if ledger_path else None,
                settings=SETTINGS, all_flags_strictly_decoded=True)


def audit_adapter(r90):
    original = r90.audit_launch
    r88 = r90.audited_runner_utilities

    def audit(launch: dict, observations: list[dict], completion: dict, identity: dict) -> dict:
        scope = scope_receipt(launch, observations)
        destination = Path(launch["destination"])
        if launch["arm"] == "P-GRB":
            compact = destination / "compact.lp"
            assert compact.is_file()
            assert v2.sha(compact) == launch["panel"]["reference"]["canonical_sha256"]
            audited = r88.audit_launch(launch, observations, completion, identity)
            assert audited.get("lp_g_split_evidence") is None
        else:
            audited = original(launch, observations, completion, identity)
        if completion["stop_reason"] == "normal_return":
            result = v2.read(destination / "result.json")
            if launch["arm"] == "P-GRB":
                reference = launch["panel"]["reference"]
                assert result["method"] == "gurobi" and result["algorithm_preset"] == "custom"
                assert result["gurobi_hga_start_requested"] is False
                assert result["gurobi_optimize_count"] == 1
                assert result["gurobi_model_fingerprint"] == reference["fingerprint"]
                assert result["gurobi_canonical_model_sha256"] == reference["canonical_sha256"]
                assert result["gurobi_num_vars"] == reference["columns"]
                assert result["gurobi_num_constrs"] == reference["rows"]
                assert result["gurobi_native_domain_audit_passed"] is True
                assert result["gurobi_lifecycle_valid"] is True
                assert scope["native_calls"] == 1
            audited["five_native_parameter_readback"] = v2.parameter_readback(
                result, require_call=scope["native_calls"] > 0, arm=launch["arm"])
        audited["native_scope_adapter"] = scope
        audited["passed"] = True
        return audited

    return audit


def contract(prereg: dict, q: dict, d6, priority, r90, old: dict) -> dict:
    assert prereg["schema"] == "round94-formal-prefix-recovery-preregistration-v3"
    assert prereg["status"] == "source_only_no_new_native_authorization"
    assert prereg["recovery_root"] == RECOVERY.relative_to(ROOT).as_posix()
    assert prereg["original_paid_arms_must_not_rerun"] is True
    assert prereg["formal_continuation_requires_new_root_lease"] is True
    assert prereg["no_algorithm_or_input_change"] is True
    assert prereg["original_preregistration_sha256"] == v2.sha(v2.PREREG)
    assert prereg["original_runner_sha256"] == v2.sha(Path(v2.__file__))
    prior_source = subprocess.check_output(
        ["git", "show", prereg["original_source_commit"] + ":scripts/round94_lpg_contemporary.py"],
        cwd=ROOT)
    assert hashlib.sha256(prior_source).hexdigest() == prereg["original_runner_sha256"]
    identity = v2.require_recovery(q, d6, priority, r90, old)
    pinned = {
        "original_recovery_identity_sha256": v2.RECOVERY / "identity.json",
        "original_qualification_completion_sha256": v2.RECOVERY / "qualification_completion.json",
        "original_formal_lease_sha256": v2.RECOVERY / "formal_lease.json",
        "original_formal_started_sha256": v2.RECOVERY / "formal_started.json",
        "original_formal_completion_sha256": v2.RECOVERY / "formal_completion.json",
        "original_formal_failure_sha256": CAMPAIGN / "failure_02.json",
        "original_formal_outer_receipt_sha256": ROOT / "results/unified_exact_round94/formal_outer_receipt_v2.json",
        "original_formal_outer_stdout_sha256": ROOT / "results/unified_exact_round94/formal_outer_stdout_v2.log",
        "original_formal_outer_stderr_sha256": ROOT / "results/unified_exact_round94/formal_outer_stderr_v2.log",
        "original_summary_sha256": CAMPAIGN / "summary.jsonl",
        "preserved_p_launch_sha256": CAMPAIGN / "formal/raw/01_F2_P-GRB/launch.json",
        "preserved_p_completion_sha256": CAMPAIGN / "formal/raw/01_F2_P-GRB/completion.json",
        "preserved_p_audit_sha256": CAMPAIGN / "formal/raw/01_F2_P-GRB/audit.json",
        "preserved_p_result_sha256": CAMPAIGN / "formal/raw/01_F2_P-GRB/result.json",
        "preserved_ens_launch_sha256": CAMPAIGN / "formal/raw/02_F2_ENS-C/launch.json",
        "preserved_ens_completion_sha256": CAMPAIGN / "formal/raw/02_F2_ENS-C/completion.json",
        "preserved_ens_failed_audit_sha256": CAMPAIGN / "formal/raw/02_F2_ENS-C/audit.json",
        "preserved_ens_result_sha256": CAMPAIGN / "formal/raw/02_F2_ENS-C/result.json",
        "preserved_ens_observations_sha256": CAMPAIGN / "formal/raw/02_F2_ENS-C/observations.json",
    }
    for key, path in pinned.items():
        assert v2.sha(path) == prereg[key], key
    completed = v2.read(v2.RECOVERY / "formal_completion.json")
    assert completed["completed"] == 1 and completed["attempted"] == [1, 2]
    assert completed["not_run"] == list(REMAINING)
    assert completed["paid_process_wall_seconds_with_receipt"] == sum(
        prereg["original_paid_process_wall_seconds"])
    outer = v2.read(ROOT / "results/unified_exact_round94/formal_outer_receipt_v2.json")
    assert outer["exit_code"] == 1
    assert outer["actual_command_launch_to_exit_seconds"] == prereg["original_paid_outer_wall_seconds"]
    summary = [json.loads(line) for line in (CAMPAIGN / "summary.jsonl").read_text().splitlines()]
    assert len(summary) == 2
    assert [(row["number"], row["id"], row["arm"], row["audit_passed"])
            for row in summary] == [(1, "F2", "P-GRB", True), (2, "F2", "ENS-C", False)]
    assert [x["number"] for x in identity["formal_launches"][2:]] == prereg["remaining_original_launch_numbers"]
    assert [f'{x["id"]}/{x["arm"]}' for x in identity["formal_launches"][2:]] == prereg["remaining_order"]
    assert sum(x["cap_seconds"] for x in identity["formal_launches"][2:]) == prereg["remaining_formal_process_cap_seconds"]
    assert len(identity["formal_launches"]) == 12
    return identity


def prefix_manifest(identity: dict) -> list[dict]:
    files = []
    for launch in identity["formal_launches"][:2]:
        directory = Path(launch["destination"])
        assert directory.is_dir()
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            files.append(dict(path=path.relative_to(CAMPAIGN).as_posix(),
                              size_bytes=path.stat().st_size, sha256=v2.sha(path)))
    assert files
    return files


def offline_prefix(r90, identity: dict) -> tuple[dict, dict, dict]:
    adapter = audit_adapter(r90)
    audits = []
    for launch in identity["formal_launches"][:2]:
        directory = Path(launch["destination"])
        assert v2.read(directory / "launch.json")["command"] == launch["command"]
        completion = v2.read(directory / "completion.json")
        assert completion["stop_reason"] == "normal_return" and completion["returncode"] == 0
        observations = v2.read(directory / "observations.json")
        audited = adapter(launch, observations, completion, identity)
        assert audited["passed"] is True and audited["endpoint"] is not None
        audits.append(audited)
    p, ens = audits
    prior_p = v2.read(Path(identity["formal_launches"][0]["destination"]) / "audit.json")
    prior_ens = v2.read(Path(identity["formal_launches"][1]["destination"]) / "audit.json")
    assert prior_p["passed"] is True and prior_p["endpoint"] == p["endpoint"]
    assert prior_ens["passed"] is False and prior_ens["endpoint"] is None
    assert p["endpoint"]["certificate"] is False and ens["endpoint"]["certificate"] is True
    assert p["endpoint"]["U"] == ens["endpoint"]["U"]
    lower = max(p["LB"], p["endpoint"]["L"], ens["LB"], ens["endpoint"]["L"])
    physical = [w["F"] for audit in audits for w in audit["witnesses"]]
    physical += [audit["final_physical_verification"]["F"] for audit in audits
                 if audit.get("final_physical_verification") is not None]
    upper = min(physical)
    assert lower <= upper + 1e-7, "original-problem cross-arm contradiction"
    summary = [json.loads(line) for line in (CAMPAIGN / "summary.jsonl").read_text().splitlines()]
    records = [summary[0], dict(summary[1], audit_passed=True, endpoint=ens["endpoint"],
                                split_evidence=ens.get("lp_g_split_evidence"), audit_error=None)]
    return p, ens, dict(schema="round94-formal-prefix-offline-v3", passed=True,
                        original_paid_arms=2, new_native_processes=0, new_optimize_calls=0,
                        recovered_records=records, strongest_original_global_L=lower,
                        minimum_original_physical_U=upper,
                        cross_arm_passed=True,
                        original_process_wall_seconds=[x["completion"]["process_wall_seconds"]
                                                       for x in records],
                        P_endpoint=p["endpoint"], ENS_endpoint=ens["endpoint"],
                        scope_check=[x["native_scope_adapter"] for x in audits])


def prepare() -> None:
    began = time.perf_counter()
    q = v2.read(v2.PREREG)
    d6, priority, r90, old = v2.modules(q)
    prereg = v2.read(PREREG)
    identity = contract(prereg, q, d6, priority, r90, old)
    assert not RECOVERY.exists(), "do not overwrite a recovery prefix"
    assert all(not Path(x["destination"]).exists() for x in identity["formal_launches"][2:])
    manifest = prefix_manifest(identity)
    p, ens, check = offline_prefix(r90, identity)
    RECOVERY.mkdir(parents=True, exist_ok=False)
    r90.write_new(RECOVERY / "prefix_manifest.json", dict(
        schema="round94-paid-formal-prefix-manifest-v3", file_count=len(manifest),
        total_bytes=sum(x["size_bytes"] for x in manifest), files=manifest))
    r90.write_new(RECOVERY / "offline_p_audit.json", p)
    r90.write_new(RECOVERY / "offline_ens_audit.json", ens)
    r90.write_new(RECOVERY / "offline_prefix_check.json", check)
    new_identity = dict(schema="round94-formal-recovery-identity-v3", optimizer_calls=0,
                        recovery_prereg_sha256=v2.sha(PREREG), prereg_sha256=v2.sha(v2.PREREG),
                        runner_sha256=v2.sha(Path(__file__)),
                        original_recovery_identity_sha256=prereg["original_recovery_identity_sha256"],
                        original_formal_completion_sha256=prereg["original_formal_completion_sha256"],
                        original_formal_outer_receipt_sha256=prereg["original_formal_outer_receipt_sha256"],
                        qualification_completion_sha256=prereg["original_qualification_completion_sha256"],
                        candidate_binary_sha256=identity["candidate_binary_sha256"],
                        prefix_manifest_sha256=v2.sha(RECOVERY / "prefix_manifest.json"),
                        offline_p_audit_sha256=v2.sha(RECOVERY / "offline_p_audit.json"),
                        offline_ens_audit_sha256=v2.sha(RECOVERY / "offline_ens_audit.json"),
                        offline_prefix_check_sha256=v2.sha(RECOVERY / "offline_prefix_check.json"),
                        original_formal_launches=identity["formal_launches"],
                        remaining_formal_launches=identity["formal_launches"][2:],
                        prepared_unix=time.time())
    r90.write_new(RECOVERY / "identity.json", new_identity)
    r90.write_new(RECOVERY / "preflight.json", dict(
        schema="round94-formal-recovery-preflight-v3", new_optimize_calls=0,
        preserved_paid_processes=2, remaining_formal_processes=10,
        remaining_process_caps_seconds=prereg["remaining_formal_process_cap_seconds"],
        original_paid_outer_wall_seconds=prereg["original_paid_outer_wall_seconds"],
        original_paid_process_wall_seconds=sum(prereg["original_paid_process_wall_seconds"]),
        prefix_file_count=len(manifest), identity_sha256=v2.sha(RECOVERY / "identity.json"),
        prepare_elapsed_before_receipt_seconds=time.perf_counter() - began,
        note="Offline re-audit only; no remaining arm can start without a new root lease."))
    print(json.dumps(dict(formal_recovery_prepared=True, new_optimize_calls=0,
                          paid_prefix_verified=2, remaining=10)), flush=True)


def require_prepared() -> tuple[dict, dict, dict]:
    q = v2.read(v2.PREREG)
    d6, priority, r90, old = v2.modules(q)
    prereg = v2.read(PREREG)
    old_identity = contract(prereg, q, d6, priority, r90, old)
    manifest = v2.read(RECOVERY / "prefix_manifest.json")
    assert manifest["schema"] == "round94-paid-formal-prefix-manifest-v3"
    assert manifest["files"] == prefix_manifest(old_identity)
    assert manifest["file_count"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(x["size_bytes"] for x in manifest["files"])
    p, ens, check = offline_prefix(r90, old_identity)
    assert v2.read(RECOVERY / "offline_p_audit.json") == p
    assert v2.read(RECOVERY / "offline_ens_audit.json") == ens
    assert v2.read(RECOVERY / "offline_prefix_check.json") == check
    identity = v2.read(RECOVERY / "identity.json")
    assert identity["schema"] == "round94-formal-recovery-identity-v3"
    assert identity["optimizer_calls"] == 0
    assert identity["runner_sha256"] == v2.sha(Path(__file__))
    assert identity["recovery_prereg_sha256"] == v2.sha(PREREG)
    assert identity["prereg_sha256"] == v2.sha(v2.PREREG)
    assert identity["original_recovery_identity_sha256"] == prereg["original_recovery_identity_sha256"]
    assert identity["original_formal_completion_sha256"] == prereg["original_formal_completion_sha256"]
    assert identity["original_formal_outer_receipt_sha256"] == prereg["original_formal_outer_receipt_sha256"]
    assert identity["qualification_completion_sha256"] == prereg["original_qualification_completion_sha256"]
    assert identity["candidate_binary_sha256"] == old_identity["candidate_binary_sha256"]
    for key, file in (("prefix_manifest_sha256", "prefix_manifest.json"),
                      ("offline_p_audit_sha256", "offline_p_audit.json"),
                      ("offline_ens_audit_sha256", "offline_ens_audit.json"),
                      ("offline_prefix_check_sha256", "offline_prefix_check.json")):
        assert identity[key] == v2.sha(RECOVERY / file)
    assert identity["original_formal_launches"] == old_identity["formal_launches"]
    assert identity["remaining_formal_launches"] == old_identity["formal_launches"][2:]
    return identity, check, r90


def cross_arm(r90, records: list[dict], role: str) -> dict:
    same = {row["arm"]: row for row in records if row["id"] == role}
    assert 2 <= len(same) <= 3
    lowers, uppers = [], []
    for arm, row in same.items():
        audit = (v2.read(RECOVERY / ("offline_p_audit.json" if arm == "P-GRB" else "offline_ens_audit.json"))
                 if role == "F2" and arm in {"P-GRB", "ENS-C"}
                 else v2.read(Path(row["destination"]) / "audit.json"))
        assert audit["passed"] is True
        lowers.append(max(audit["LB"], row["endpoint"]["L"]))
        uppers.extend(w["F"] for w in audit["witnesses"])
        if audit.get("final_physical_verification") is not None:
            uppers.append(audit["final_physical_verification"]["F"])
    strongest, weakest = max(lowers), min(uppers) if uppers else None
    passed = weakest is None or strongest <= weakest + 1e-7
    result = dict(schema="round94-formal-recovery-cross-bound-v3", role=role,
                  compared_arms=list(same), strongest_global_L=strongest,
                  minimum_physical_U=weakest, tolerance=1e-7, passed=passed,
                  scope="offline contradiction only; no merged endpoint")
    r90.write_new(RECOVERY / f"cross_arm_{role}_{len(same)}.json", result)
    assert passed, f"cross-arm original-problem contradiction: {role}"
    return result


def run_remaining() -> None:
    invocation = time.perf_counter()
    identity, prefix, r90 = require_prepared()
    lease_path = RECOVERY / "remaining_formal_lease.json"
    assert v2.read(lease_path) == dict(
        schema="round94-formal-recovery-remaining-lease-v3", authorized_by="root",
        allow_optimize=True, formal_recovery_identity_sha256=v2.sha(RECOVERY / "identity.json"),
        offline_prefix_check_sha256=v2.sha(RECOVERY / "offline_prefix_check.json"),
        planned_processes=10, execution_order=list(REMAINING))
    assert not (RECOVERY / "formal_started.json").exists()
    assert not (RECOVERY / "summary.jsonl").exists()
    assert all(not Path(x["destination"]).exists() for x in identity["remaining_formal_launches"])
    assert not r90.foreign_heavy_processes(), "another solver/build process is active"
    r90.CAMPAIGN = RECOVERY
    r90.audit_launch = audit_adapter(r90)
    r90.write_new(RECOVERY / "formal_started.json", dict(
        formal_recovery_identity_sha256=v2.sha(RECOVERY / "identity.json"),
        lease_sha256=v2.sha(lease_path),
        offline_prefix_check_sha256=v2.sha(RECOVERY / "offline_prefix_check.json"),
        preflight_wall_seconds=time.perf_counter() - invocation, started_unix=time.time()))
    started = time.perf_counter()
    records = list(prefix["recovered_records"])
    error = None
    try:
        for launch in identity["remaining_formal_launches"]:
            attempt_started = time.perf_counter()
            try:
                record = r90.run_one(launch, v2.read(v2.PREREG), identity)
                records.append(record)
            except Exception as exc:
                r90.write_new(RECOVERY / f'failure_{launch["number"]:02d}.json', dict(
                    schema="round94-formal-recovery-failure-v3", number=launch["number"],
                    role=launch["id"], arm=launch["arm"], error=repr(exc),
                    destination=launch["destination"],
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination_exists=Path(launch["destination"]).exists(),
                    completion_exists=(Path(launch["destination"]) / "completion.json").is_file(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            same = [x for x in records if x["id"] == launch["id"]]
            if len(same) >= 2:
                cross_arm(r90, same, launch["id"])
            signals = v2.severe_signals(same, launch["id"])
            if signals:
                r90.write_new(RECOVERY / f'risk_stop_{launch["id"]}.json', dict(
                    role=launch["id"], signals=signals,
                    continuation_summary_sha256=v2.sha(RECOVERY / "summary.jsonl"),
                    research_signal_only=True, requires_independent_review=True))
                raise RuntimeError("Severe or promotion-blocking same-role comparison")
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        paid = [v2.read(Path(x["destination"]) / "completion.json")
                for x in identity["remaining_formal_launches"]
                if (Path(x["destination"]) / "completion.json").is_file()]
        failures = [v2.read(path) for path in sorted(RECOVERY.glob("failure_*.json"))]
        attempted = [x["number"] for x in identity["remaining_formal_launches"]
                     if Path(x["destination"]).exists()]
        r90.write_new(RECOVERY / "formal_completion.json", dict(
            schema="round94-formal-recovery-completion-v3", planned_remaining=10,
            completed_remaining=len(records) - 2, verified_original_prefix=2,
            passed=error is None and len(records) == 12, error=error,
            attempted_remaining=attempted,
            not_run=[f'{x["id"]}/{x["arm"]}' for x in identity["remaining_formal_launches"]
                     if x["number"] not in attempted],
            original_paid_process_wall_seconds=sum(
                v2.read(Path(x["destination"]) / "completion.json")["process_wall_seconds"]
                for x in identity["original_formal_launches"][:2]),
            remaining_paid_process_wall_seconds_with_receipt=sum(x["process_wall_seconds"] for x in paid),
            remaining_completed_process_receipts=len(paid),
            remaining_process_wall_if_missing_receipt="unknown"
            if any(not x["completion_exists"] for x in failures)
            else sum(x["process_wall_seconds"] for x in paid),
            original_outer_wall_seconds=v2.read(PREREG)["original_paid_outer_wall_seconds"],
            continuation_outer_wall_before_receipt_seconds=time.perf_counter() - started,
            precompletion_failed_attempt_elapsed_seconds=sum(x["attempt_elapsed_seconds"] for x in failures
                                                             if not x["completion_exists"]),
            ended_unix=time.time()))


def main() -> None:
    if not __debug__:
        raise RuntimeError("Python -O disables identity and lease assertions")
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round94_lpg_formal_recovery_v3.py prepare|run"
    if sys.argv[1] == "prepare":
        prepare()
    else:
        run_remaining()


if __name__ == "__main__":
    main()
