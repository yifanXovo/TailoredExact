#!/usr/bin/env python3
"""Audit exact common-row factoring for paired and sibling blocks."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import round42_common as common


def num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def component(instance: str, arm: str, tag: str) -> dict[str, Any] | None:
    path = common.RUNS / f"static__{instance}__{arm}__mip__{tag}" / \
        "result.json"
    return common.load_json(path) if path.is_file() else None


def sibling(instance: str, arm: str, tag: str) -> dict[str, Any] | None:
    path = common.RUNS / f"c6__{instance}__{arm}__{tag}" / "result.json"
    return common.load_json(path) if path.is_file() else None


def sibling_models(result: dict[str, Any]) -> list[dict[str, str]]:
    path = Path(str(result.get("round42_sibling_coverage_ledger_path", "")))
    if not path.is_file():
        return []
    return [row for row in common.csv_rows(path) if row.get("model_sha256")]


def main() -> int:
    manifests = common.csv_rows(common.OUT / "development_manifest.csv")
    rows: list[dict[str, Any]] = []
    for manifest in manifests:
        instance = manifest["instance_id"]
        paired_base_parts = [
            component(instance, "paired-k4-lower",
                      "development_family_b_base"),
            component(instance, "paired-k4-upper",
                      "development_family_b_base"),
        ]
        paired_fact_parts = [
            component(instance, "paired-k4-lower-factored",
                      "development_family_b_factored"),
            component(instance, "paired-k4-upper-factored",
                      "development_family_b_factored"),
        ]
        if all(paired_base_parts) and all(paired_fact_parts):
            base = [part for part in paired_base_parts if part]
            fact = [part for part in paired_fact_parts if part]
            rows.append({
                "instance_id": instance,
                "family": "paired-k4",
                "base_model_count": len(base),
                "factored_model_count": len(fact),
                "base_indicator_rows": sum(int(part.get(
                    "round41_static_indicator_rows", 0)) for part in base),
                "factored_indicator_rows": sum(int(part.get(
                    "round41_static_indicator_rows", 0)) for part in fact),
                "reported_indicator_rows_removed": sum(int(part.get(
                    "round42_factored_indicator_rows_removed", 0))
                    for part in fact),
                "base_model_nonzeros": sum(int(part.get(
                    "round41_static_model_nonzeros", 0)) for part in base),
                "factored_model_nonzeros": sum(int(part.get(
                    "round41_static_model_nonzeros", 0)) for part in fact),
                "base_work": sum(num(part.get(
                    "round41_static_solver_work")) for part in base),
                "factored_work": sum(num(part.get(
                    "round41_static_solver_work")) for part in fact),
                "base_exact_seconds": sum(num(part.get(
                    "round41_static_solver_runtime_seconds")) for part in base),
                "factored_exact_seconds": sum(num(part.get(
                    "round41_static_solver_runtime_seconds")) for part in fact),
                "base_strict": all(bool(part.get(
                    "round42_block_strict_certificate")) for part in base),
                "factored_strict": all(bool(part.get(
                    "round42_block_strict_certificate")) for part in fact),
            })
        sibling_base = sibling(
            instance, "sibling-core", "development_family_c_base")
        sibling_fact = sibling(
            instance, "sibling-core-factored",
            "development_family_c_factored")
        if sibling_base and sibling_fact:
            base_models = sibling_models(sibling_base)
            fact_models = sibling_models(sibling_fact)
            rows.append({
                "instance_id": instance,
                "family": "terminal-sibling",
                "base_model_count": len(base_models),
                "factored_model_count": len(fact_models),
                "base_indicator_rows": sum(int(row.get(
                    "indicator_rows") or 0) for row in base_models),
                "factored_indicator_rows": sum(int(row.get(
                    "indicator_rows") or 0) for row in fact_models),
                "reported_indicator_rows_removed": "ledger-model-difference",
                "base_model_nonzeros": sum(int(row.get(
                    "model_nonzeros") or 0) for row in base_models),
                "factored_model_nonzeros": sum(int(row.get(
                    "model_nonzeros") or 0) for row in fact_models),
                "base_work": num(sibling_base.get("external_gini_tree_work")),
                "factored_work": num(sibling_fact.get(
                    "external_gini_tree_work")),
                "base_exact_seconds": num(sibling_base.get(
                    "runtime_seconds")),
                "factored_exact_seconds": num(sibling_fact.get(
                    "runtime_seconds")),
                "base_strict": bool(sibling_base.get(
                    "strict_certified_original_problem")),
                "factored_strict": bool(sibling_fact.get(
                    "strict_certified_original_problem")),
            })
    if not rows:
        raise RuntimeError("no completed factoring pairs")
    for row in rows:
        row["work_ratio_factored_over_base"] = (
            num(row["factored_work"]) / num(row["base_work"])
            if num(row["base_work"]) > 0.0 else
            (1.0 if num(row["factored_work"]) == 0.0 else math.inf))
        row["shifted_time_ratio_factored_over_base"] = (
            (num(row["factored_exact_seconds"]) + 1.0) /
            (num(row["base_exact_seconds"]) + 1.0))
    common.write_csv(common.OUT / "common_row_factoring_audit.csv", rows)
    paired = [row for row in rows if row["family"] == "paired-k4"]
    siblings = [row for row in rows if row["family"] == "terminal-sibling"]
    text = f"""# Common-row factoring audit

The transformation was uniform and exact: coefficient-identical rows present
once in every segment were written once; shared LHS/sense rows with varying RHS
were replaced by an exact selector-weighted RHS row; all other rows remained
conditional. No instance-specific row selection was permitted.

- Completed paired-K4 base/refined comparisons: {len(paired)}.
- Completed terminal-sibling base/refined comparisons: {len(siblings)}.
- Every reported strict result is audited again in `certificate_audit.csv`.

Per-instance indicator, nonzero, Work, and shifted-time effects are in
`common_row_factoring_audit.csv`. Final interpretation is added after the
development gate is complete.
"""
    common.write_text(common.OUT / "common_row_factoring_audit.md", text)
    print({"rows": len(rows), "paired": len(paired),
           "siblings": len(siblings)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
