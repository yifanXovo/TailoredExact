#!/usr/bin/env python3
"""Classify the one reproducible Round 39 numerical endpoint as unresolved."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import round39_common as common


RUN_ID = (
    "primary__round39_small_hard_V12_M3_Q20_slot07_seed621538683__"
    "c6_hga_light_1000")


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def endpoint(path: Path) -> dict[str, Any]:
    result = common.load_json(path / "result.json")
    lower = float(result["external_gini_tree_global_lower_bound"])
    upper = float(result["external_gini_tree_verified_upper_bound"])
    return {
        "path": common.relative(path), "result_sha256": common.sha256(
            path / "result.json"),
        "process_seconds": common.process_entry_time(result),
        "valid_lower_bound": lower, "verified_upper_bound": upper,
        "absolute_residual": upper - lower,
        "relative_residual": max(0.0, (upper - lower) /
                                 max(abs(upper), 1e-12)),
        "strict_certificate": truth(result.get(
            "strict_certified_original_problem")),
        "rejection_reason": result.get("strict_certificate_rejection_reason"),
        "all_relevant_leaves_closed": truth(result.get(
            "external_gini_tree_all_relevant_leaves_closed")),
        "open_leaf_count": int(result.get("external_gini_tree_open_leaf_count")),
        "all_leaf_bounds_valid": truth(result.get(
            "external_gini_tree_all_leaf_bounds_valid")),
        "global_bound_monotone": truth(result.get(
            "external_gini_tree_global_bound_monotone")),
        "lifecycle_complete": truth(result.get(
            "external_gini_tree_lifecycle_complete")),
        "global_deadline_interruptions": int(result.get(
            "external_gini_tree_global_deadline_interruption_count")),
        "final_objective": float(result["objective"]),
        "startup_variant": result.get("external_gini_tree_startup_variant"),
    }


def main() -> int:
    run_dir = common.RUNS / RUN_ID
    invalidated = sorted(common.INVALIDATED.glob(f"{RUN_ID}__invalidated__*"))
    if len(invalidated) != 1:
        raise RuntimeError(
            f"expected one preserved first attempt, found {len(invalidated)}")
    attempts = [endpoint(invalidated[0]), endpoint(run_dir)]
    first, second = attempts
    deterministic = all(
        first[key] == second[key] for key in (
            "valid_lower_bound", "verified_upper_bound", "absolute_residual",
            "relative_residual", "strict_certificate", "rejection_reason",
            "all_relevant_leaves_closed", "open_leaf_count",
            "all_leaf_bounds_valid", "global_bound_monotone",
            "lifecycle_complete", "global_deadline_interruptions",
            "final_objective", "startup_variant",
        ))
    absolute = second["absolute_residual"]
    valid = bool(
        deterministic and not second["strict_certificate"]
        and second["rejection_reason"] == "global_bound_gap_not_closed"
        and second["all_relevant_leaves_closed"]
        and second["open_leaf_count"] == 0
        and second["all_leaf_bounds_valid"]
        and second["global_bound_monotone"]
        and second["lifecycle_complete"]
        and second["global_deadline_interruptions"] == 0
        and absolute > 1e-7
        and absolute < 2e-7
    )
    if not valid:
        raise RuntimeError("unresolved numerical endpoint classification failed")
    classification = {
        "schema": "round39-unresolved-classification-v1", "round_id": 39,
        "run_id": RUN_ID, "official_unresolved": True,
        "completed": False, "completion_marker_atomic": False,
        "return_code": 0, "emergency_timeout": False, "threads": 1,
        "unresolved_reason": (
            "deterministic_closed_tree_lb_ub_residual_exceeds_"
            "frozen_certificate_tolerance"),
        "not_reported_as_optimal": True, "not_reported_as_strict": True,
        "not_a_timeout": True, "additional_time_cannot_continue_closed_tree": True,
        "rerun_count": 2, "rerun_endpoint_identical": deterministic,
        "certificate_tolerance": 1e-7,
        "absolute_residual": absolute,
        "relative_residual": second["relative_residual"],
        "result_sha256": second["result_sha256"],
        "attempts": attempts,
        "correctness_interpretation": (
            "No false certificate: both runs reject the endpoint. The original "
            "solution is verified feasible, all exact leaves close, and the "
            "remaining valid-bound residual is retained rather than rounded "
            "or relabelled as optimal."),
    }
    common.write_json(run_dir / "unresolved_classification.json", classification)
    common.write_json(common.OUT / "official_unresolved_row.json", classification)
    common.write_text(common.OUT / "official_unresolved_row.md", f"""# Round 39 unresolved official row

`{RUN_ID}` is **not** reported as optimal or strict. Two independent Seed-0
runs close all four relevant leaves with zero open leaves, complete lifecycle,
monotone valid bounds, and the identical endpoint LB
`{second['valid_lower_bound']:.17g}` versus verified UB
`{second['verified_upper_bound']:.17g}`. The absolute residual
`{absolute:.17g}` exceeds the frozen `1e-7` certificate tolerance, so both runs
correctly reject with `global_bound_gap_not_closed` after about 76 to 78 seconds.
Because the tree is already closed, this is not a timeout and further wall time
does not provide a continuation state. Both attempts and hashes are retained.
""")
    print(json.dumps(classification, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
