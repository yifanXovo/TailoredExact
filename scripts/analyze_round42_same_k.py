#!/usr/bin/env python3
"""Quantify the fixed-K2 multi-tree versus single-tree causal effect."""

from __future__ import annotations

import math

import analyze_round42_development as dev
import round42_common as common


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def main() -> int:
    per_run = common.csv_rows(common.OUT / "per_run_results.csv")
    by_key = {(row["instance_id"], row["arm"]): row for row in per_run}
    manifests = common.csv_rows(common.OUT / "development_manifest.csv")
    rows = []
    for item in manifests:
        instance = item["instance_id"]
        external = by_key.get((instance, "EXTERNAL-K2-FIXED"))
        static = by_key.get((instance, "ST-K2-P-CORE"))
        if not external or not static:
            continue
        work_ratio = dev.ratio(dev.number(static["solver_work"]),
                               dev.number(external["solver_work"]))
        time_ratio = dev.ratio(
            dev.number(static["exact_phase_seconds"]) + 1.0,
            dev.number(external["exact_phase_seconds"]) + 1.0)
        rows.append({
            "instance_id": instance,
            "diagnostic_role": item["diagnostic_role"],
            "external_k2_exact_seconds": external["exact_phase_seconds"],
            "static_k2_exact_seconds": static["exact_phase_seconds"],
            "static_over_external_shifted_time_ratio": time_ratio,
            "external_k2_work": external["solver_work"],
            "static_k2_work": static["solver_work"],
            "static_over_external_work_ratio": work_ratio,
            "external_k2_nodes": external["solver_nodes"],
            "static_k2_nodes": static["solver_nodes"],
            "external_k2_proof_jobs": external[
                "independent_integer_proof_jobs"],
            "static_k2_proof_jobs": static[
                "independent_integer_proof_jobs"],
            "external_k2_model_variables": external["model_variables"],
            "static_k2_model_variables": static["model_variables"],
            "external_k2_model_nonzeros": external["model_nonzeros"],
            "static_k2_model_nonzeros": static["model_nonzeros"],
            "external_k2_strict_certificate": external[
                "strict_certificate"],
            "static_k2_strict_certificate": static["strict_certificate"],
            "objective_match": abs(dev.number(external["objective"]) -
                                   dev.number(static["objective"])) <= 1e-7,
            "false_certificate": dev.truth(external["false_certificate"]) or
                dev.truth(static["false_certificate"]),
        })
    if len(rows) != len(manifests):
        raise RuntimeError(
            f"same-K evidence incomplete: {len(rows)}/{len(manifests)}")
    common.write_csv(common.OUT / "external_k2_vs_static_k2.csv", rows)
    work_gmean = gmean([dev.number(row[
        "static_over_external_work_ratio"]) for row in rows])
    time_gmean = gmean([dev.number(row[
        "static_over_external_shifted_time_ratio"]) for row in rows])
    static_work_wins = sum(dev.number(row[
        "static_over_external_work_ratio"]) <= 0.95 for row in rows)
    external_work_wins = sum(dev.number(row[
        "static_over_external_work_ratio"]) >= 1.05 for row in rows)
    report = f"""# External K2 versus static K2 Core

This is the fixed-granularity causal comparison. Both arms use the same two
midpoint intervals and complete interval-local row packs. External-K2-Fixed
uses two independent native MIP jobs; ST-K2-P-Core uses one static segmented
native tree.

- Development pairs: {len(rows)}.
- Geometric mean static/external Work ratio: {work_gmean:.6f}.
- Geometric mean shifted exact-time ratio: {time_gmean:.6f}.
- Material Work wins for the static tree: {static_work_wins}.
- Material Work wins for the two external trees: {external_work_wins}.
- False certificates: {sum(dev.truth(row['false_certificate']) for row in rows)}.

The per-instance table records exact time, Work, nodes, model size, proof-job
count, objective agreement, and certificate status. This comparison isolates
proof architecture at K2 and is not used to attribute any K2-versus-K4 effect.
"""
    common.write_text(common.OUT / "external_k2_vs_static_k2.md", report)
    print({"pairs": len(rows), "work_gmean": work_gmean,
           "time_gmean": time_gmean})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
