"""R94 offline-audit timing repair over the immutable v3 paid prefix.

Only neutral_exchange.offline_seconds is excluded from semantic replay equality.
The original formal processes and v3 prepare remain immutable; running the
ten never-started arms requires a new, exact root lease.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys
import time

import round94_lpg_formal_recovery_v3 as v3


v2 = v3.v2
ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = v3.CAMPAIGN
PREREG = ROOT / "results/unified_exact_round94/formal_recovery_preregistration_v4.json"
RECOVERY = CAMPAIGN / "formal_recovery_v4"
REMAINING = v3.REMAINING


def ens_semantics(audit: dict) -> tuple[dict, float]:
    """Exclude exactly one measured offline cost; retain every evidence field."""
    normalized = copy.deepcopy(audit)
    exchange = normalized["neutral_exchange"]
    assert isinstance(exchange, dict) and "offline_seconds" in exchange
    elapsed = exchange.pop("offline_seconds")
    assert type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0
    return normalized, float(elapsed)


def compare_ens(saved: dict, replayed: dict) -> dict:
    left, saved_seconds = ens_semantics(saved)
    right, replay_seconds = ens_semantics(replayed)
    assert left == right, "ENS scope/physical/coverage/parameter semantic mismatch"
    return dict(schema="round94-ens-single-timing-field-comparison-v4",
                excluded_path="neutral_exchange.offline_seconds", semantic_equal=True,
                saved_offline_seconds=saved_seconds, replay_offline_seconds=replay_seconds,
                both_finite_nonnegative=True)


def contract() -> tuple[dict, dict, object]:
    prereg = v2.read(PREREG)
    assert prereg["schema"] == "round94-formal-prefix-recovery-preregistration-v4"
    assert prereg["status"] == "source_only_no_new_native_authorization"
    assert prereg["recovery_root"] == RECOVERY.relative_to(ROOT).as_posix()
    assert prereg["semantic_compare_exclusion"] == "neutral_exchange.offline_seconds"
    assert prereg["v3_offline_reverification_fault_path"] == "neutral_exchange.offline_seconds"
    assert prereg["original_paid_arms_must_not_rerun"] is True
    assert prereg["new_native_processes_authorized"] == 0
    assert prereg["remaining_formal_requires_new_root_lease"] is True
    assert v2.sha(Path(v3.__file__)) == prereg["v3_runner_sha256"]
    assert v2.sha(v3.PREREG) == prereg["v3_preregistration_sha256"]
    pinned = {
        "v3_prepare_outer_receipt_sha256": ROOT / "results/unified_exact_round94/formal_recovery_prepare_outer_v3.json",
        "v3_prepare_stdout_sha256": ROOT / "results/unified_exact_round94/formal_recovery_prepare_stdout_v3.log",
        "v3_prepare_stderr_sha256": ROOT / "results/unified_exact_round94/formal_recovery_prepare_stderr_v3.log",
        "v3_prepared_identity_sha256": v3.RECOVERY / "identity.json",
        "v3_preflight_sha256": v3.RECOVERY / "preflight.json",
        "v3_prefix_manifest_sha256": v3.RECOVERY / "prefix_manifest.json",
        "v3_offline_p_audit_sha256": v3.RECOVERY / "offline_p_audit.json",
        "v3_offline_ens_audit_sha256": v3.RECOVERY / "offline_ens_audit.json",
        "v3_offline_prefix_check_sha256": v3.RECOVERY / "offline_prefix_check.json",
    }
    for key, path in pinned.items():
        assert v2.sha(path) == prereg[key], key
    outer = v2.read(ROOT / "results/unified_exact_round94/formal_recovery_prepare_outer_v3.json")
    assert outer["exit_code"] == 0
    assert outer["actual_command_launch_to_exit_seconds"] == prereg["v3_paid_prepare_outer_wall_seconds"]
    v3_identity = v2.read(v3.RECOVERY / "identity.json")
    assert v3_identity["schema"] == "round94-formal-recovery-identity-v3"
    assert v3_identity["optimizer_calls"] == 0
    assert v3_identity["runner_sha256"] == prereg["v3_runner_sha256"]
    assert v3_identity["recovery_prereg_sha256"] == prereg["v3_preregistration_sha256"]
    q = v2.read(v2.PREREG)
    d6, priority, r90, old = v2.modules(q)
    original = v3.contract(v2.read(v3.PREREG), q, d6, priority, r90, old)
    assert v3_identity["original_formal_launches"] == original["formal_launches"]
    assert v3_identity["remaining_formal_launches"] == original["formal_launches"][2:]
    assert [x["number"] for x in original["formal_launches"][2:]] == prereg["remaining_original_launch_numbers"]
    assert [x["id"] + "/" + x["arm"] for x in original["formal_launches"][2:]] == prereg["remaining_order"]
    assert sum(x["cap_seconds"] for x in original["formal_launches"][2:]) == prereg["remaining_process_cap_seconds"]
    return prereg, original, r90


def recovered_prefix(r90, original: dict) -> tuple[dict, dict, dict, dict]:
    p, ens, check = v3.offline_prefix(r90, original)
    assert v2.read(v3.RECOVERY / "offline_p_audit.json") == p
    comparison = compare_ens(v2.read(v3.RECOVERY / "offline_ens_audit.json"), ens)
    assert v2.read(v3.RECOVERY / "offline_prefix_check.json") == check
    return p, ens, check, comparison


def prepare() -> None:
    began = time.perf_counter()
    prereg, original, r90 = contract()
    assert not RECOVERY.exists(), "never overwrite the v4 recovery"
    assert all(not Path(x["destination"]).exists() for x in original["formal_launches"][2:])
    manifest = v3.prefix_manifest(original)
    v3_manifest = v2.read(v3.RECOVERY / "prefix_manifest.json")
    assert v3_manifest["files"] == manifest and v3_manifest["file_count"] == len(manifest)
    p, ens, check, comparison = recovered_prefix(r90, original)
    RECOVERY.mkdir(parents=True, exist_ok=False)
    r90.write_new(RECOVERY / "prefix_manifest.json", dict(
        schema="round94-paid-formal-prefix-manifest-v4", file_count=len(manifest),
        total_bytes=sum(x["size_bytes"] for x in manifest), files=manifest))
    r90.write_new(RECOVERY / "offline_p_audit.json", p)
    r90.write_new(RECOVERY / "offline_ens_audit.json", ens)
    r90.write_new(RECOVERY / "offline_prefix_check.json", check)
    r90.write_new(RECOVERY / "v3_timing_fault_comparison.json", comparison)
    identity = dict(schema="round94-formal-recovery-identity-v4", optimizer_calls=0,
                    recovery_prereg_sha256=v2.sha(PREREG), prereg_sha256=v2.sha(v2.PREREG),
                    runner_sha256=v2.sha(Path(__file__)),
                    v3_runner_sha256=prereg["v3_runner_sha256"],
                    v3_prepared_identity_sha256=prereg["v3_prepared_identity_sha256"],
                    v3_prepare_outer_receipt_sha256=prereg["v3_prepare_outer_receipt_sha256"],
                    original_recovery_identity_sha256=v2.sha(v2.RECOVERY / "identity.json"),
                    original_formal_completion_sha256=v2.sha(v2.RECOVERY / "formal_completion.json"),
                    original_formal_outer_receipt_sha256=v2.sha(
                        ROOT / "results/unified_exact_round94/formal_outer_receipt_v2.json"),
                    qualification_completion_sha256=v2.sha(v2.RECOVERY / "qualification_completion.json"),
                    candidate_binary_sha256=original["candidate_binary_sha256"],
                    prefix_manifest_sha256=v2.sha(RECOVERY / "prefix_manifest.json"),
                    offline_p_audit_sha256=v2.sha(RECOVERY / "offline_p_audit.json"),
                    offline_ens_audit_sha256=v2.sha(RECOVERY / "offline_ens_audit.json"),
                    offline_prefix_check_sha256=v2.sha(RECOVERY / "offline_prefix_check.json"),
                    v3_timing_fault_comparison_sha256=v2.sha(RECOVERY / "v3_timing_fault_comparison.json"),
                    original_formal_launches=original["formal_launches"],
                    remaining_formal_launches=original["formal_launches"][2:],
                    prepared_unix=time.time())
    r90.write_new(RECOVERY / "identity.json", identity)
    r90.write_new(RECOVERY / "preflight.json", dict(
        schema="round94-formal-recovery-preflight-v4", new_optimize_calls=0,
        original_paid_formal_arms=2, remaining_formal_processes=10,
        remaining_process_caps_seconds=prereg["remaining_process_cap_seconds"],
        original_paid_outer_wall_seconds=v2.read(v3.PREREG)["original_paid_outer_wall_seconds"],
        v3_paid_offline_prepare_outer_wall_seconds=prereg["v3_paid_prepare_outer_wall_seconds"],
        prefix_file_count=len(manifest), identity_sha256=v2.sha(RECOVERY / "identity.json"),
        prepare_elapsed_before_receipt_seconds=time.perf_counter() - began,
        note="Only a single non-semantic offline timing field is excluded on replay; no native launch."))
    print(json.dumps(dict(formal_recovery_v4_prepared=True, new_optimize_calls=0,
                          paid_prefix_verified=2, remaining=10)), flush=True)


def require_prepared() -> tuple[dict, dict, object]:
    prereg, original, r90 = contract()
    manifest = v2.read(RECOVERY / "prefix_manifest.json")
    assert manifest["schema"] == "round94-paid-formal-prefix-manifest-v4"
    assert manifest["files"] == v3.prefix_manifest(original)
    assert manifest["file_count"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(x["size_bytes"] for x in manifest["files"])
    p, ens, check, _ = recovered_prefix(r90, original)
    assert v2.read(RECOVERY / "offline_p_audit.json") == p
    compare_ens(v2.read(RECOVERY / "offline_ens_audit.json"), ens)
    assert v2.read(RECOVERY / "offline_prefix_check.json") == check
    fault = v2.read(RECOVERY / "v3_timing_fault_comparison.json")
    assert fault["schema"] == "round94-ens-single-timing-field-comparison-v4"
    assert fault["excluded_path"] == "neutral_exchange.offline_seconds"
    assert fault["semantic_equal"] is True and fault["both_finite_nonnegative"] is True
    assert type(fault["saved_offline_seconds"]) in (int, float)
    assert type(fault["replay_offline_seconds"]) in (int, float)
    assert all(math.isfinite(x) and x >= 0 for x in
               (fault["saved_offline_seconds"], fault["replay_offline_seconds"]))
    assert fault["saved_offline_seconds"] == ens_semantics(
        v2.read(v3.RECOVERY / "offline_ens_audit.json"))[1]
    identity = v2.read(RECOVERY / "identity.json")
    assert identity["schema"] == "round94-formal-recovery-identity-v4"
    assert identity["optimizer_calls"] == 0
    assert identity["runner_sha256"] == v2.sha(Path(__file__))
    assert identity["recovery_prereg_sha256"] == v2.sha(PREREG)
    assert identity["prereg_sha256"] == v2.sha(v2.PREREG)
    assert identity["v3_runner_sha256"] == prereg["v3_runner_sha256"]
    assert identity["v3_prepared_identity_sha256"] == prereg["v3_prepared_identity_sha256"]
    assert identity["v3_prepare_outer_receipt_sha256"] == prereg["v3_prepare_outer_receipt_sha256"]
    assert identity["original_recovery_identity_sha256"] == v2.sha(v2.RECOVERY / "identity.json")
    assert identity["original_formal_completion_sha256"] == v2.sha(v2.RECOVERY / "formal_completion.json")
    assert identity["original_formal_outer_receipt_sha256"] == v2.sha(
        ROOT / "results/unified_exact_round94/formal_outer_receipt_v2.json")
    assert identity["qualification_completion_sha256"] == v2.sha(v2.RECOVERY / "qualification_completion.json")
    assert identity["candidate_binary_sha256"] == original["candidate_binary_sha256"]
    for key, name in (("prefix_manifest_sha256", "prefix_manifest.json"),
                      ("offline_p_audit_sha256", "offline_p_audit.json"),
                      ("offline_ens_audit_sha256", "offline_ens_audit.json"),
                      ("offline_prefix_check_sha256", "offline_prefix_check.json"),
                      ("v3_timing_fault_comparison_sha256", "v3_timing_fault_comparison.json")):
        assert identity[key] == v2.sha(RECOVERY / name)
    assert identity["original_formal_launches"] == original["formal_launches"]
    assert identity["remaining_formal_launches"] == original["formal_launches"][2:]
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
    receipt = dict(schema="round94-formal-recovery-cross-bound-v4", role=role,
                   compared_arms=list(same), strongest_global_L=strongest,
                   minimum_physical_U=weakest, tolerance=1e-7, passed=passed,
                   scope="offline contradiction only; no merged endpoint")
    r90.write_new(RECOVERY / f"cross_arm_{role}_{len(same)}.json", receipt)
    assert passed, f"cross-arm original-problem contradiction: {role}"
    return receipt


def run_remaining() -> None:
    invocation = time.perf_counter()
    identity, prefix, r90 = require_prepared()
    lease_path = RECOVERY / "remaining_formal_lease.json"
    assert v2.read(lease_path) == dict(
        schema="round94-formal-recovery-remaining-lease-v4", authorized_by="root",
        allow_optimize=True, formal_recovery_identity_sha256=v2.sha(RECOVERY / "identity.json"),
        offline_prefix_check_sha256=v2.sha(RECOVERY / "offline_prefix_check.json"),
        planned_processes=10, execution_order=list(REMAINING))
    assert not (RECOVERY / "formal_started.json").exists()
    assert not (RECOVERY / "summary.jsonl").exists()
    assert all(not Path(x["destination"]).exists() for x in identity["remaining_formal_launches"])
    assert not r90.foreign_heavy_processes(), "another solver/build process is active"
    r90.CAMPAIGN = RECOVERY
    r90.audit_launch = v3.audit_adapter(r90)
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
                    schema="round94-formal-recovery-failure-v4", number=launch["number"],
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
            schema="round94-formal-recovery-completion-v4", planned_remaining=10,
            completed_remaining=len(records) - 2, verified_original_prefix=2,
            passed=error is None and len(records) == 12, error=error,
            attempted_remaining=attempted,
            not_run=[x["id"] + "/" + x["arm"] for x in identity["remaining_formal_launches"]
                     if x["number"] not in attempted],
            original_paid_process_wall_seconds=sum(
                v2.read(Path(x["destination"]) / "completion.json")["process_wall_seconds"]
                for x in identity["original_formal_launches"][:2]),
            remaining_paid_process_wall_seconds_with_receipt=sum(x["process_wall_seconds"] for x in paid),
            remaining_completed_process_receipts=len(paid),
            remaining_process_wall_if_missing_receipt="unknown"
            if any(not x["completion_exists"] for x in failures)
            else sum(x["process_wall_seconds"] for x in paid),
            original_outer_wall_seconds=v2.read(v3.PREREG)["original_paid_outer_wall_seconds"],
            v3_offline_prepare_outer_wall_seconds=v2.read(PREREG)["v3_paid_prepare_outer_wall_seconds"],
            continuation_outer_wall_before_receipt_seconds=time.perf_counter() - started,
            precompletion_failed_attempt_elapsed_seconds=sum(x["attempt_elapsed_seconds"] for x in failures
                                                             if not x["completion_exists"]),
            ended_unix=time.time()))


def main() -> None:
    if not __debug__:
        raise RuntimeError("Python -O disables identity and lease assertions")
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round94_lpg_formal_recovery_v4.py prepare|run"
    if sys.argv[1] == "prepare":
        prepare()
    else:
        run_remaining()


if __name__ == "__main__":
    main()
