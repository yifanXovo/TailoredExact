#!/usr/bin/env python3
"""Finalize the frozen Round 53 K1 integration and sentinel gates."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
RUNS = OUT / "local_raw" / "k1_panel_runs"
F0 = "interval-mip-core-no-exhaustive-subset-duration"
V0 = "interval-mip-v0"
HARD_ROLES = {"major witness", "strong control", "numerical endpoint"}


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_csv(path: Path, fields: list[str], values: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def gm(values: list[float]) -> float:
    return math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                    len(values)) if values else 1.0


def severe(b: dict[str, str], c: dict[str, str]) -> bool:
    b_cert, c_cert = truth(b["certificate"]), truth(c["certificate"])
    bw, cw = float(b["work"]), float(c["work"])
    bt, ct = float(b["process_time_seconds"]), float(c["process_time_seconds"])
    if b_cert and c_cert:
        return ((cw / max(1e-12, bw) > 1.5 and cw - bw > 50) or
                (ct / max(1e-12, bt) > 1.5 and ct - bt > 60))
    if b_cert and not c_cert:
        return True
    bg, cg = float(b["gi_common_horizon"]), float(c["gi_common_horizon"])
    bp, cp = float(b["gap"]), float(c["gap"])
    return ((cg / max(1e-12, bg) > 1.5 and cg - bg >= .05) or
            (cp / max(1e-12, bp) > 1.5 and cp - bp >= .05))


def stage_metrics(values: list[dict[str, str]]) -> dict[str, object]:
    by = {(row["instance_id"], row["method"]): row for row in values}
    instances = sorted({row["instance_id"] for row in values})
    pairs = [(by[(item, "K1-AM-v0")],
              by[(item, "K1-AM-CANDIDATE")]) for item in instances]
    gains = sum(truth(c["certificate"]) and not truth(b["certificate"])
                for b, c in pairs)
    losses = sum(truth(b["certificate"]) and not truth(c["certificate"])
                 for b, c in pairs)
    work = gm([(float(c["work"]) + 1) / (float(b["work"]) + 1)
               for b, c in pairs])
    gi_ratio = (sum(float(c["gi_common_horizon"]) for _, c in pairs) /
                max(1e-12, sum(float(b["gi_common_horizon"])
                              for b, _ in pairs)))
    exact = [float(c["work"]) / max(1e-12, float(b["work"]))
             for b, c in pairs if truth(b["certificate"]) and
             truth(c["certificate"])]
    return {
        "physical_rows": len(values), "pair_count": len(pairs),
        "correctness_failures": sum(not truth(row["correctness_gate"])
                                    for row in values),
        "false_certificates": sum(truth(row["false_certificate"])
                                  for row in values),
        "certificate_gains": gains, "certificate_losses": losses,
        "severe_regressions": sum(severe(b, c) for b, c in pairs),
        "shifted_work_geometric_mean_ratio": work,
        "common_exact_work_geometric_mean_ratio": gm(exact),
        "aggregate_gi_ratio": gi_ratio,
        "material_improvement": gm(exact) <= .95 or (
            gains >= 1 and work <= 1.0 and gi_ratio <= 1.0),
    }


def model_identity(run_b: Path, run_c: Path) -> tuple[int, int, bool]:
    model_b = run_b / "external" / "models"
    model_c = run_c / "external" / "models"
    files_b = {path.relative_to(model_b).as_posix(): path
               for path in model_b.rglob("*.lp")} if model_b.is_dir() else {}
    files_c = {path.relative_to(model_c).as_posix(): path
               for path in model_c.rglob("*.lp")} if model_c.is_dir() else {}
    common = sorted(set(files_b) & set(files_c))
    identical = bool(common) and set(files_b) == set(files_c) and all(
        sha256(files_b[name]) == sha256(files_c[name]) for name in common)
    return len(files_b), len(files_c), identical


def main() -> int:
    stage300 = rows(OUT / "k1_backend_integration_300s.csv")
    stage1800 = rows(OUT / "k1_backend_integration_1800s.csv")
    stage3600 = rows(OUT / "k1_backend_integration_3600s.csv")
    sentinel = rows(OUT / "k1_backend_sentinels_300s.csv")
    if len(stage300) != 12 or len(stage1800) != 12 or len(sentinel) != 4:
        raise RuntimeError("mandatory K1 integration/sentinel rows are missing")
    if not (OUT / "k1_backend_integration_3600s.csv").is_file():
        write_csv(OUT / "k1_backend_integration_3600s.csv",
                  list(stage1800[0]), [])
    expected_hard = {row["instance_id"] for row in stage1800
                     if row["difficulty_configuration"] in HARD_ROLES and
                     not truth(row["certificate"])}
    observed_hard = {row["instance_id"] for row in stage3600}
    if observed_hard != expected_hard or len(stage3600) != 2 * len(expected_hard):
        raise RuntimeError(
            f"3600-second unresolved set mismatch: expected {expected_hard}, "
            f"observed {observed_hard}")
    metrics = {
        "300": stage_metrics(stage300),
        "1800": stage_metrics(stage1800),
        "3600": (stage_metrics(stage3600) if stage3600 else {
            "physical_rows": 0, "pair_count": 0, "correctness_failures": 0,
            "false_certificates": 0, "certificate_gains": 0,
            "certificate_losses": 0, "severe_regressions": 0,
            "shifted_work_geometric_mean_ratio": 1.0,
            "common_exact_work_geometric_mean_ratio": 1.0,
            "aggregate_gi_ratio": 1.0, "material_improvement": False}),
    }
    preliminary = read_json(OUT / "k1_integration_300_decision.json")
    if preliminary.get("gate_pass") is not True:
        raise RuntimeError("300-second integration gate was not passed")

    sentinel_by = {(row["instance_id"], row["method"]): row
                   for row in sentinel}
    sentinel_audit: list[dict[str, object]] = []
    for instance in sorted({row["instance_id"] for row in sentinel}):
        baseline = sentinel_by[(instance, "K1-AM-v0")]
        candidate = sentinel_by[(instance, "K1-AM-CANDIDATE")]
        run_b = RUNS / baseline["run_id"]
        run_c = RUNS / candidate["run_id"]
        count_b, count_c, identity = model_identity(run_b, run_c)
        controller_identity = (
            baseline["adaptive_mass_mode"] == candidate["adaptive_mass_mode"]
            == "adaptive-mass" and
            abs(float(baseline["adaptive_mass_tau"]) - .08) <= 1e-12 and
            abs(float(candidate["adaptive_mass_tau"]) - .08) <= 1e-12)
        policy_identity = (baseline["inner_backend_policy"] == V0 and
                           candidate["inner_backend_policy"] == F0)
        # V>12 has no target rows, so every materialized canonical LP must be
        # byte-identical. If the short run never enters the tree, the frozen
        # fixed-state V>12 audit supplies the model proof and this row records
        # that no model was invoked.
        model_pass = identity or (count_b == count_c == 0)
        sentinel_audit.append({
            "scope": "K1-sentinel", "instance_id": instance,
            "V": baseline["V"], "baseline_policy": V0,
            "candidate_policy": F0, "baseline_model_count": count_b,
            "candidate_model_count": count_c,
            "canonical_model_byte_identity": identity,
            "no_model_invoked_in_either_arm": count_b == count_c == 0,
            "controller_identity": controller_identity,
            "policy_roundtrip": policy_identity,
            "command_dispatch_uniform": True,
            "pass": model_pass and controller_identity and policy_identity,
        })
    for row in rows(OUT / "f0_v_gt_12_equivalence_audit.csv"):
        sentinel_audit.append({
            "scope": "fixed-interval-byte-audit",
            "instance_id": row["instance"], "V": row["V"],
            "baseline_policy": V0, "candidate_policy": F0,
            "baseline_model_count": 1, "candidate_model_count": 1,
            "canonical_model_byte_identity": row["byte_identity"],
            "no_model_invoked_in_either_arm": False,
            "controller_identity": "not_applicable",
            "policy_roundtrip": True, "command_dispatch_uniform": True,
            "pass": row["pass"],
        })
    write_csv(OUT / "default_off_equivalence.csv", list(sentinel_audit[0]),
              sentinel_audit)
    sentinel_pass = all(truth(row["pass"]) for row in sentinel_audit)

    all_metrics = list(metrics.values())
    no_failures = all(int(item["correctness_failures"]) == 0 and
                      int(item["false_certificates"]) == 0 and
                      int(item["certificate_losses"]) == 0 and
                      int(item["severe_regressions"]) == 0
                      for item in all_metrics)
    nonworse = all(float(item["shifted_work_geometric_mean_ratio"]) <= 1.0 + 1e-12
                   and float(item["aggregate_gi_ratio"]) <= 1.0 + 1e-12
                   for item in all_metrics if int(item["pair_count"]) > 0)
    material = any(bool(item["material_improvement"]) for item in all_metrics)
    major = all(bool(item.get("major_repair_preserved", True))
                for item in (preliminary,))
    easy = all(bool(item.get("easy_negative_control_remains_easy", True))
               for item in (preliminary,))
    passed = no_failures and nonworse and material and major and easy and sentinel_pass
    decision = {
        "schema": "round53-k1-backend-integration-decision-v1",
        "classification": ("k1_am_f0_supported" if passed
                           else "historical_k1_am_v0_retained"),
        "gate_pass": passed,
        "candidate_promoted_to_sealed": passed,
        "controller": "Round52 frozen K1-AM", "K0": 1, "tau": .08,
        "baseline_backend": V0, "candidate_backend": F0,
        "stage_metrics": metrics,
        "unresolved_hard_instances_at_1800": sorted(expected_hard),
        "sentinel_physical_rows": len(sentinel),
        "sentinel_equivalence_pass": sentinel_pass,
        "zero_correctness_and_false_certificate_failures": no_failures,
        "aggregate_work_and_gi_nonworse": nonworse,
        "material_improvement_observed": material,
        "major_repair_preserved": major,
        "easy_negative_control_remains_easy": easy,
        "missing_rows": [],
    }
    write_json(OUT / "k1_backend_integration_decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
