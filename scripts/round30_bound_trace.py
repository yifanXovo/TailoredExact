#!/usr/bin/env python3
"""Round 30 observed-bound trace validation and AUC primitives.

No routine in this module interpolates between observations or extends a
trajectory after its last recorded event.  Integrals are left-continuous
step-function integrals over consecutive observed timestamps only.
"""

from __future__ import annotations

import csv
import gzip
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO


REQUIRED_COLUMNS = (
    "process_elapsed_seconds",
    "exact_phase_elapsed_seconds",
    "event_type",
    "active_leaf",
    "active_leaf_valid_lower_bound",
    "other_open_leaf_min_valid_lower_bound",
    "valid_global_lower_bound",
    "verified_global_upper_bound",
    "open_relevant_leaf_count",
    "closed_relevant_leaf_count",
    "event_source",
)

INITIAL_EVENT = "exact_tree_initialization"
FINAL_EVENT = "finalization"
INTERRUPTION_EVENT = "interruption"
OBSERVED_PROGRESS_EVENTS = {
    "parent_lp_completion",
    "child_lp_completion",
    "native_root_processing_bound",
    "partial_native_mip_bound_improvement",
    "partial_native_bound_target",
    "split",
    "declined_split",
    "infeasible_closure",
    "lp_cutoff_pruning",
    "terminal_mip_bound_improvement",
    "incumbent_improvement",
    "terminal_mip_closure",
}


@dataclass(frozen=True)
class BoundObservation:
    process_seconds: float
    exact_seconds: float
    event_type: str
    global_lower_bound: float
    verified_upper_bound: float
    open_relevant_leaves: int
    closed_relevant_leaves: int
    active_lower_bound: float | None
    other_lower_bound: float | None
    event_source: str


@dataclass(frozen=True)
class TraceAudit:
    complete: bool
    reason: str
    observations: tuple[BoundObservation, ...]
    bound_observation_count: int
    first_process_seconds: float | None
    last_process_seconds: float | None
    interrupted: bool
    exact_tree_closed: bool


def _open_text(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def _finite(text: str, field: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field}_not_numeric") from error
    if not math.isfinite(value):
        raise ValueError(f"{field}_not_finite")
    return value


def _optional_finite(text: str, field: str) -> float | None:
    return None if text.strip() == "" else _finite(text, field)


def _integer(text: str, field: str) -> int:
    try:
        value = int(text)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field}_not_integer") from error
    if value < 0:
        raise ValueError(f"{field}_negative")
    return value


def audit_external_trace(
        path: Path, *, require_interruption_if_open: bool = True,
        tolerance: float = 1e-7) -> TraceAudit:
    """Validate one C0/C3/C4/C5 trace without manufacturing observations."""
    if not path.is_file():
        return TraceAudit(
            False, "trace_missing", (), 0, None, None, False, False)
    try:
        with _open_text(path) as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise ValueError("header_missing")
            missing = [name for name in REQUIRED_COLUMNS
                       if name not in reader.fieldnames]
            if missing:
                raise ValueError("required_columns_missing:" + ";".join(missing))
            observations: list[BoundObservation] = []
            previous_process = -math.inf
            previous_exact = -math.inf
            previous_bound = -math.inf
            for row_number, row in enumerate(reader, start=2):
                process = _finite(
                    row["process_elapsed_seconds"], "process_elapsed_seconds")
                exact = _finite(
                    row["exact_phase_elapsed_seconds"],
                    "exact_phase_elapsed_seconds")
                global_bound = _finite(
                    row["valid_global_lower_bound"],
                    "valid_global_lower_bound")
                upper = _finite(
                    row["verified_global_upper_bound"],
                    "verified_global_upper_bound")
                active = _optional_finite(
                    row["active_leaf_valid_lower_bound"],
                    "active_leaf_valid_lower_bound")
                other = _optional_finite(
                    row["other_open_leaf_min_valid_lower_bound"],
                    "other_open_leaf_min_valid_lower_bound")
                open_count = _integer(
                    row["open_relevant_leaf_count"],
                    "open_relevant_leaf_count")
                closed_count = _integer(
                    row["closed_relevant_leaf_count"],
                    "closed_relevant_leaf_count")
                if process + tolerance < previous_process:
                    raise ValueError(
                        f"process_time_nonmonotone_at_row_{row_number}")
                if exact + tolerance < previous_exact:
                    raise ValueError(
                        f"exact_time_nonmonotone_at_row_{row_number}")
                scale = max(1.0, abs(previous_bound), abs(global_bound))
                if global_bound + tolerance * scale < previous_bound:
                    raise ValueError(
                        f"global_bound_nonmonotone_at_row_{row_number}")
                if active is not None and other is not None:
                    expected = min(active, other)
                    scale = max(1.0, abs(expected), abs(global_bound))
                    if abs(expected - global_bound) > tolerance * scale:
                        raise ValueError(
                            f"active_other_min_mismatch_at_row_{row_number}")
                elif active is None and other is None:
                    raise ValueError(
                        f"no_bound_component_at_row_{row_number}")
                event = row["event_type"].strip()
                source = row["event_source"].strip()
                if not event:
                    raise ValueError(f"event_type_empty_at_row_{row_number}")
                if not source:
                    raise ValueError(f"event_source_empty_at_row_{row_number}")
                observations.append(BoundObservation(
                    process, exact, event, global_bound, upper,
                    open_count, closed_count, active, other, source))
                previous_process = process
                previous_exact = exact
                previous_bound = global_bound
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        return TraceAudit(
            False, str(error), (), 0, None, None, False, False)
    if not observations:
        return TraceAudit(
            False, "trace_has_no_rows", (), 0, None, None, False, False)
    if observations[0].event_type != INITIAL_EVENT:
        return TraceAudit(
            False, "initialization_not_first", tuple(observations), 0,
            observations[0].process_seconds,
            observations[-1].process_seconds, False, False)
    if observations[-1].event_type != FINAL_EVENT:
        return TraceAudit(
            False, "finalization_not_last", tuple(observations), 0,
            observations[0].process_seconds,
            observations[-1].process_seconds,
            any(item.event_type == INTERRUPTION_EVENT
                for item in observations),
            observations[-1].open_relevant_leaves == 0)
    interrupted = any(
        item.event_type == INTERRUPTION_EVENT for item in observations)
    exact_tree_closed = observations[-1].open_relevant_leaves == 0
    if require_interruption_if_open and not exact_tree_closed and not interrupted:
        return TraceAudit(
            False, "open_finalization_without_interruption",
            tuple(observations), 0, observations[0].process_seconds,
            observations[-1].process_seconds, interrupted, exact_tree_closed)
    internal = [
        item for item in observations
        if item.event_type in OBSERVED_PROGRESS_EVENTS
    ]
    if not exact_tree_closed and not internal:
        return TraceAudit(
            False, "endpoint_only_open_trace", tuple(observations), 0,
            observations[0].process_seconds,
            observations[-1].process_seconds, interrupted, exact_tree_closed)
    return TraceAudit(
        True, "complete_observed_trace", tuple(observations),
        len(internal), observations[0].process_seconds,
        observations[-1].process_seconds, interrupted, exact_tree_closed)


def observed_step_auc(
        observations: Iterable[BoundObservation], *,
        common_verified_upper_bound: float | None = None) -> dict[str, float]:
    """Integrate only consecutive observed steps, ending at the last event."""
    rows = tuple(observations)
    if len(rows) < 2:
        raise ValueError("at_least_two_observations_required")
    initial_bound = rows[0].global_lower_bound
    final_time = rows[-1].process_seconds
    first_time = rows[0].process_seconds
    duration = final_time - first_time
    if duration <= 0.0:
        raise ValueError("positive_observed_duration_required")
    common_ub = (
        common_verified_upper_bound
        if common_verified_upper_bound is not None
        else min(item.verified_upper_bound for item in rows)
    )
    if not math.isfinite(common_ub):
        raise ValueError("common_upper_bound_not_finite")
    proof_denominator = max(common_ub - initial_bound, 1e-12)
    raw_area = 0.0
    normalized_proof_area = 0.0
    normalized_gap_area = 0.0
    for left, right in zip(rows, rows[1:]):
        delta = right.process_seconds - left.process_seconds
        if delta < 0.0:
            raise ValueError("observation_time_nonmonotone")
        raw_area += delta * left.global_lower_bound
        proof = max(
            0.0, min(1.0, (left.global_lower_bound - initial_bound) /
                         proof_denominator))
        normalized_proof_area += delta * proof
        gap = max(
            0.0, min(1.0, (common_ub - left.global_lower_bound) /
                         max(abs(common_ub), 1e-12)))
        normalized_gap_area += delta * gap
    return {
        "observed_start_process_seconds": first_time,
        "observed_end_process_seconds": final_time,
        "observed_duration_seconds": duration,
        "raw_lower_bound_time_integral": raw_area,
        "mean_observed_lower_bound": raw_area / duration,
        "normalized_proof_progress_auc": normalized_proof_area / duration,
        "normalized_gap_auc": normalized_gap_area / duration,
        "common_verified_upper_bound": common_ub,
        "initial_valid_lower_bound": initial_bound,
        "final_observed_lower_bound": rows[-1].global_lower_bound,
    }
