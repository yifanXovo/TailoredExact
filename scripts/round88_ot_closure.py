"""Offline Round88 OT LP separation to an observed numerical stopping state.

Each supervised arm starts from its own frozen original LP. It never launches
the original MIP or modifies an ENS-C production algorithm. The only runtime
budget is the external 300-second whole-arm process deadline.
"""

from __future__ import annotations

import argparse
from ctypes import wintypes
import ctypes
from fractions import Fraction
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from round88_ot_math import (PairCut, h_name, q_name, ratio, row_value,
                             state_name, support_fingerprint)


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "results/unified_exact_round88"
WHOLE_ARM_SECONDS = 300.0
SOURCES = {
    "F2-root": ("ot_qualification_f2_l0_audit/manifest.json",
                "d223756f601a5f9c1966e5087e6ddace81bcf1b53130afdad2bb79366421b905"),
    "D7-root": ("ot_qualification_d7_audit_v4/manifest.json",
                "a0996967e9278469defa43ab1c630b0d16f7e996062f71bf91efa9a656f99a4d"),
    "D7-child": ("ot_qualification_d7_l00_audit/manifest.json",
                 "e73e08318afe65d9c4d145f2dd8efe8732783b11e0628f347434b4093c2f09fd"),
}
ARMS = ("B1", "B2", "B1+B2")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sgn(value: Fraction, zero_sign: int = 1) -> int:
    if zero_sign not in (-1, 0, 1):
        raise ValueError("invalid zero tie")
    return -1 if value < 0 else 1 if value > 0 else zero_sign


def fast_pair_cut(kind: str, i: int, j: int,
                  supports: Mapping[int, Sequence[int]], targets: Mapping[int, int],
                  a: Fraction, b: Fraction, values: Mapping[str, float],
                  zero_sign: int = 1) -> PairCut:
    """One support sort, exact-rational CDF prefix, then coefficient suffix.

    The input primal's binary floating values are interpreted exactly via
    Fraction.from_float. This chooses the mathematical sign at that represented
    point; it need not reproduce the old float-summation sign near zero.
    """
    if i >= j or kind not in {"B1", "B2"} or kind == "B2" and not a < b:
        raise ValueError("invalid pair/kind/G interval")
    grouped: dict[Fraction, list[tuple[int, int]]] = {}
    for station in (i, j):
        for y in supports[station]:
            grouped.setdefault(ratio(y, targets[station]), []).append((station, y))
    levels = sorted(grouped)
    prefix_a = prefix_b = Fraction(0)
    intervals: list[Fraction] = []
    signs: list[tuple[int, int]] = []
    state_factors: list[Fraction] = []
    q_factors: list[Fraction] = []
    a_values: list[float] = []
    b_values: list[float] = []
    for k, lo in enumerate(levels[:-1]):
        for station, y in grouped[lo]:
            direction = 1 if station == i else -1
            prefix_a += direction * Fraction.from_float(values[state_name(station, y)])
            prefix_b += direction * Fraction.from_float(values[q_name(station, y)])
        delta = levels[k + 1] - lo
        if delta <= 0:
            raise AssertionError("non-increasing support levels")
        if kind == "B1":
            alpha, beta = _sgn(prefix_a, zero_sign), 0
            state_factor, q_factor = Fraction(alpha), Fraction(0)
        else:
            alpha = _sgn(b * prefix_a - prefix_b, zero_sign)
            beta = _sgn(prefix_b - a * prefix_a, zero_sign)
            state_factor = b * alpha - a * beta
            q_factor = Fraction(beta - alpha)
        intervals.append(delta)
        signs.append((alpha, beta))
        state_factors.append(state_factor)
        q_factors.append(q_factor)
        a_values.append(float(prefix_a))
        b_values.append(float(prefix_b))
    suffix_s = [Fraction(0)] * len(levels)
    suffix_q = [Fraction(0)] * len(levels)
    for k in range(len(intervals) - 1, -1, -1):
        suffix_s[k] = suffix_s[k + 1] + intervals[k] * state_factors[k]
        suffix_q[k] = suffix_q[k + 1] + intervals[k] * q_factors[k]
    position = {level: k for k, level in enumerate(levels)}
    coeff: dict[str, Fraction] = {}
    for station in (i, j):
        direction = 1 if station == i else -1
        for y in supports[station]:
            k = position[ratio(y, targets[station])]
            s_value = -direction * suffix_s[k]
            q_value = -direction * suffix_q[k]
            if s_value:
                coeff[state_name(station, y)] = s_value
            if q_value:
                coeff[q_name(station, y)] = q_value
    coeff[h_name(i, j)] = b - a if kind == "B2" else Fraction(1)
    return PairCut(kind, i, j, coeff, tuple(signs), tuple(intervals),
                   tuple(a_values), tuple(b_values),
                   support_fingerprint({i: supports[i], j: supports[j]}, targets, a, b))


def row_signature(cut: PairCut, supports: Mapping[int, Sequence[int]],
                  targets: Mapping[int, int], a: Fraction, b: Fraction,
                  lp_sha256: str) -> str:
    """Exact signed row identity, scoped to the original LP and local B2 domain."""
    scale = b-a if cut.kind == "B2" else Fraction(1)
    payload = {
        "lp_sha256": lp_sha256, "kind": cut.kind, "pair": [cut.i, cut.j],
        "support": [(k, targets[k], list(supports[k])) for k in (cut.i, cut.j)],
        "b2_domain": [str(a), str(b)] if cut.kind == "B2" else None,
        "normalized_coefficients": [(name, str(value/scale))
                                    for name, value in sorted(cut.coeff.items())],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def model_row_signature(cut: PairCut, supports: Mapping[int, Sequence[int]],
                        targets: Mapping[int, int], a: Fraction, b: Fraction,
                        lp_sha256: str) -> str:
    """Deduplicate exactly identical normalized inequalities in a combined arm."""
    scale = b-a if cut.kind == "B2" else Fraction(1)
    payload = {
        "lp_sha256": lp_sha256, "pair": [cut.i, cut.j],
        "support": [(k, targets[k], list(supports[k])) for k in (cut.i, cut.j)],
        "normalized_coefficients": [(name, str(value/scale))
                                    for name, value in sorted(cut.coeff.items())],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def frozen_source(label: str) -> tuple[dict[str, Any], Path]:
    relative, expected_manifest_sha = SOURCES[label]
    path = CAMPAIGN / relative
    if sha(path) != expected_manifest_sha:
        raise ValueError(f"qualification manifest changed: {label}")
    manifest = read(path)
    if manifest["contract"] != "round88_same_source_one_round_ot_diagnostic_v1":
        raise ValueError("unexpected qualification contract")
    for field in ("lp", "input"):
        if sha(Path(manifest[field])) != manifest[field + "_sha256"]:
            raise ValueError(f"frozen {field} changed: {label}")
    if manifest["source_sha256"] != "4496078f25c0cdad1cf7a5c39835fd23121e8978":
        raise ValueError("unqualified ENS-C source")
    return manifest, path


def prepare(out: Path) -> None:
    started = time.perf_counter()
    if out.exists():
        raise FileExistsError(out)
    sources = {}
    for label in SOURCES:
        manifest, path = frozen_source(label)
        sources[label] = {
            "qualification_manifest": str(path.resolve()), "qualification_sha256": sha(path),
            "lp_sha256": manifest["lp_sha256"], "input_sha256": manifest["input_sha256"],
            "leaf_id": manifest["leaf_id"], "parent_id": manifest["parent_id"],
            "support_fingerprint": manifest["structure"]["support_fingerprint"],
            "effective_gamma_l": manifest["structure"]["effective_gamma_l"],
            "effective_gamma_u": manifest["structure"]["effective_gamma_u"],
            "lp_fingerprint": manifest["lp_sha256"],
        }
    manifest = {
        "schema": "round88-ot-closure-prereg-v1", "status": "prepared_not_admitted",
        "arms": list(ARMS), "source_order": list(SOURCES), "whole_arm_seconds": WHOLE_ARM_SECONDS,
        "each_arm_starts_from_own_original_lp": True, "historical_rowbank_as_start": False,
        "all_reliable_new_pair_rows_each_round": True, "zero_tie": 1,
        "source_manifests": sources,
        "script_sha256": sha(Path(__file__)),
        "math_sha256": sha(ROOT / "scripts/round88_ot_math.py"),
        "diagnostic_sha256": sha(ROOT / "scripts/round88_ot_diagnostic.py"),
        "numeric_protocol": {"FeasibilityTol": 1e-6, "OptimalityTol": 1e-6,
                             "Threads": 1, "Seed": 0, "Presolve": -1,
                             "MIPGap": 0.0, "violation_tolerance": 1e-6},
    }
    out.mkdir(parents=True, exist_ok=False)
    save(out / "manifest.json", manifest)
    save(out / "preparation_cost.json", {"shared_offline_wall_seconds":
                                          time.perf_counter() - started,
                                          "scope": "Shared frozen fingerprint audit, not a free per-arm model start"})


def supervise_prepare(out: Path) -> int:
    """Record shared preparation from outside the preparing Python process."""
    started = time.perf_counter()
    if out.exists():
        raise FileExistsError(out)
    command = [sys.executable, str(Path(__file__).resolve()), "prepare",
               "--out-dir", str(out.resolve())]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                               check=False)
    elapsed = time.perf_counter()-started
    out.mkdir(parents=True, exist_ok=True)
    (out / "preparation_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (out / "preparation_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    save(out / "preparation_supervision.json", {
        "status": "prepared" if completed.returncode == 0 else "preparation_failed",
        "external_launch_to_exit_wall_seconds": elapsed,
        "returncode": completed.returncode, "command": command,
        "manifest_sha256": sha(out / "manifest.json") if (out / "manifest.json").is_file() else None,
        "shared_research_cost_not_per_arm": True})
    return completed.returncode


def verify_prepared(path: Path, source: str, arm: str) -> tuple[dict[str, Any], dict[str, Any]]:
    prepared = read(path)
    if (prepared.get("schema") != "round88-ot-closure-prereg-v1"
            or prepared.get("whole_arm_seconds") != WHOLE_ARM_SECONDS
            or prepared.get("arms") != list(ARMS)
            or prepared.get("source_order") != list(SOURCES)
            or prepared.get("zero_tie") != 1
            or not prepared.get("all_reliable_new_pair_rows_each_round")
            or prepared.get("historical_rowbank_as_start")):
        raise ValueError("closure preregistration drift")
    if prepared["script_sha256"] != sha(Path(__file__)) or (
            prepared["math_sha256"] != sha(ROOT / "scripts/round88_ot_math.py") or
            prepared["diagnostic_sha256"] != sha(ROOT / "scripts/round88_ot_diagnostic.py")):
        raise ValueError("diagnostic code identity drift")
    source_manifest, source_path = frozen_source(source)
    stored = prepared["source_manifests"][source]
    if (stored["qualification_sha256"] != sha(source_path)
            or stored["lp_sha256"] != source_manifest["lp_sha256"]
            or stored["input_sha256"] != source_manifest["input_sha256"]
            or stored["support_fingerprint"] != source_manifest["structure"]["support_fingerprint"]):
        raise ValueError("source/LP/support identity drift")
    if arm not in ARMS:
        raise ValueError("unregistered arm")
    return prepared, source_manifest


def require_lease(manifest_path: Path, source: str, arm: str) -> None:
    """Optimization stays closed until root signs the frozen manifest and arms."""
    lease = read(CAMPAIGN / "ot_closure_lease.json")
    if lease != {"schema": "round88-ot-closure-lease-v1",
                 "manifest_sha256": sha(manifest_path),
                 "authorized_by": "Astra", "allow_optimize": True,
                 "source_arms": [[s, a] for s in SOURCES for a in ARMS]}:
        raise ValueError("missing or changed Round88 OT closure lease")
    if [source, arm] not in lease["source_arms"]:
        raise ValueError("arm outside signed lease")


def _primal_residuals(model: Any, destination: Path, original_rows: int) -> dict[str, Any]:
    """Audit every original and added row; persist the largest residuals."""
    from round88_ot_diagnostic import row_terms
    started = time.perf_counter()
    values = {var.VarName: var.X for var in model.getVars()}
    save(destination / "primal.json", values)
    original_max = added_max = bound_max = 0.0
    largest: list[tuple[float, int, dict[str, Any]]] = []
    constraints = model.getConstrs()
    for index, row in enumerate(constraints):
        terms = row_terms(model, row)
        lhs = math.fsum(coef * values[name] for name, coef in terms.items())
        violation = (max(0.0, row.RHS - lhs) if row.Sense == ">" else
                     max(0.0, lhs - row.RHS) if row.Sense == "<" else
                     abs(lhs - row.RHS) if row.Sense == "=" else float("inf"))
        if index < original_rows:
            original_max = max(original_max, violation)
        else:
            added_max = max(added_max, violation)
        if violation > 0:
            item = {"name": row.ConstrName, "index": index,
                    "original": index < original_rows, "violation": violation}
            if len(largest) < 20:
                heapq.heappush(largest, (violation, index, item))
            elif violation > largest[0][0]:
                heapq.heapreplace(largest, (violation, index, item))
    for var in model.getVars():
        bound_max = max(bound_max, var.LB - var.X, var.X - var.UB)
    largest_rows = [item for _, _, item in sorted(largest, reverse=True)]
    result = {"original_rows": original_rows, "added_rows": len(constraints) - original_rows,
              "original_maximum_row_violation": original_max,
              "added_maximum_row_violation": added_max,
              "maximum_bound_violation": bound_max,
              "largest_residuals": largest_rows, "primal_variables": len(values),
              "audit_wall_seconds": time.perf_counter() - started}
    save(destination / "residuals.json", result)
    return result


def _scan(values: dict[str, float], supports: dict[int, list[int]],
          targets: dict[int, int], a: Fraction, b: Fraction, arm: str,
          lp_sha256: str, residual: float, existing: set[str],
          destination: Path) -> dict[str, Any]:
    from round88_ot_diagnostic import reliable
    started = time.perf_counter()
    kinds = ("B1", "B2") if arm == "B1+B2" and a < b else (
        ("B1",) if arm == "B1" or a == b else ("B2",))
    records: list[dict[str, Any]] = []
    new_rows: list[tuple[PairCut, Fraction, str, str]] = []
    planned_model_rows: set[str] = set()
    exact_point = {name: Fraction.from_float(value) for name, value in values.items()}
    maximum_raw = maximum_normalized = -math.inf
    maximum_exact = Fraction(0)
    positive = unreliable = existing_reliable = numeric_rejection = boundary_disagreement = 0
    for i in sorted(supports):
        for j in sorted(k for k in supports if k > i):
            for kind in kinds:
                cut = fast_pair_cut(kind, i, j, supports, targets, a, b, values)
                scale = b - a if kind == "B2" else Fraction(1)
                signature = row_signature(cut, supports, targets, a, b, lp_sha256)
                model_signature = model_row_signature(cut, supports, targets, a, b, lp_sha256)
                record: dict[str, Any] = {"kind": kind, "pair": [i, j],
                    "row_signature": signature, "model_row_signature": model_signature,
                    "signs": cut.signs, "intervals_exact": [str(v) for v in cut.intervals],
                    "cdf_a_values": cut.a_values, "cdf_b_values": cut.b_values,
                    "coefficients_exact": {k: str(v) for k, v in sorted(cut.coeff.items())},
                    "scale_exact": str(scale), "previously_added": model_signature in existing}
                try:
                    raw = -math.fsum(float(coef) * values[name]
                                     for name, coef in cut.coeff.items())
                    normalized = raw / float(scale)
                    exact_raw = -row_value(cut.coeff, exact_point)
                    exact_normalized = exact_raw / scale
                    reliable_new, reason, margin = reliable(
                        cut.coeff, scale, normalized, values, residual)
                    if not math.isfinite(raw) or not math.isfinite(normalized):
                        raise ArithmeticError("nonfinite row activity")
                    maximum_raw = max(maximum_raw, raw)
                    maximum_normalized = max(maximum_normalized, normalized)
                    maximum_exact = max(maximum_exact, exact_normalized)
                    if (normalized > 0) != (exact_normalized > 0):
                        boundary_disagreement += 1
                    if normalized > 0 or exact_normalized > 0:
                        positive += 1
                    if reason == "unreliable_scaled_coefficient":
                        numeric_rejection += 1
                    elif reliable_new and exact_normalized <= 0:
                        numeric_rejection += 1
                        reliable_new = False
                        reason = "float_reliable_violation_not_positive_at_exact_binary_point"
                    elif reliable_new and model_signature in existing:
                        existing_reliable += 1
                    elif reliable_new:
                        if model_signature not in planned_model_rows:
                            new_rows.append((cut, scale, signature, model_signature))
                            planned_model_rows.add(model_signature)
                        else:
                            reason = "identical_normalized_row_already_planned_this_round"
                    elif normalized > 0 or exact_normalized > 0:
                        unreliable += 1
                    record.update(raw_violation=raw, normalized_violation=normalized,
                                  exact_binary_point_raw_violation=str(exact_raw),
                                  exact_binary_point_normalized_violation=str(exact_normalized),
                                  reliable=reliable_new, reason=reason,
                                  reliability_margin=margin)
                except (ArithmeticError, OverflowError, ValueError) as exc:
                    numeric_rejection += 1
                    record.update(raw_violation=None, normalized_violation=None,
                                  reliable=False, reason="coefficient_or_activity_numeric_rejection",
                                  error=repr(exc))
                records.append(record)
    with (destination / "all_pair_rows.jsonl").open("x", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    if numeric_rejection or existing_reliable:
        status = "existing_row_violation_or_numeric_rejection"
    elif new_rows:
        status = "add_all_reliable_new_rows"
    elif positive:
        status = "no_reliable_new_row"
    else:
        status = "complete_scan_no_observed_violation"
    return {"status": status, "pair_count": len(supports) * (len(supports)-1)//2,
            "candidate_count": len(records), "positive_candidate_count": positive,
            "unreliable_positive_count": unreliable,
            "float_exact_sign_disagreement_count": boundary_disagreement,
            "existing_reliably_violated_count": existing_reliable,
            "numeric_rejection_count": numeric_rejection,
            "maximum_raw_violation": maximum_raw if math.isfinite(maximum_raw) else None,
            "maximum_normalized_violation": maximum_normalized if math.isfinite(maximum_normalized) else None,
            "maximum_exact_binary_point_normalized_violation": str(maximum_exact),
            "new_rows": new_rows, "separation_wall_seconds": time.perf_counter()-started}


def diagnose(manifest_path: Path, source: str, arm: str, out: Path) -> None:
    ready = Path(os.environ["ROUND88_OT_CLOSURE_READY_PATH"])
    while not ready.is_file():
        time.sleep(0.01)  # supervisor must first assign this process to its Win32 job
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    save(out / "inflight.json", {"phase": "source_verification", "source": source,
                                 "arm": arm, "manifest_sha256": sha(manifest_path)})
    require_lease(manifest_path, source, arm)
    verification_started = time.perf_counter()
    prepared, source_manifest = verify_prepared(manifest_path, source, arm)
    verification_seconds = time.perf_counter() - verification_started
    from gurobipy import GRB
    from round88_ot_diagnostic import (add_cut, audit_model, configure, load_model,
                                       process_peak_memory_bytes, read_instance)
    lp = Path(source_manifest["lp"])
    input_path = Path(source_manifest["input"])
    instance = read_instance(input_path)
    a, b = Fraction(source_manifest["gamma_l"]), Fraction(source_manifest["gamma_u"])
    loaded = time.perf_counter()
    original = load_model(lp)
    read_seconds = time.perf_counter() - loaded
    audited = time.perf_counter()
    structure = audit_model(original, instance, a, b,
                            source_manifest["verified_ub"], source_manifest["lambda"])
    audit_seconds = time.perf_counter() - audited
    if structure != source_manifest["structure"]:
        raise ValueError("actual model structure differs from qualified source")
    a, b = Fraction(structure["effective_gamma_l"]), Fraction(structure["effective_gamma_u"])
    if arm == "B2" and a == b:
        raise ValueError("B2 inapplicable for zero-width G domain")
    relaxed_at = time.perf_counter()
    model = original.relax()
    relax_seconds = time.perf_counter() - relaxed_at
    if any(var.VType != GRB.CONTINUOUS for var in model.getVars()):
        raise ValueError("model.relax left integer variables")
    original_rows = len(model.getConstrs())
    supports = {int(k): value for k, value in structure["support"].items()}
    targets = instance["targets"]
    provenance = {"schema": "round88-ot-closure-arm-v1", "source": source, "arm": arm,
                  "manifest_sha256": sha(manifest_path),
                  "qualification_manifest_sha256": prepared["source_manifests"][source]["qualification_sha256"],
                  "lp": str(lp), "lp_sha256": source_manifest["lp_sha256"],
                  "input": str(input_path), "input_sha256": source_manifest["input_sha256"],
                  "source_sha256": source_manifest["source_sha256"],
                  "binary_sha256": source_manifest["binary_sha256"],
                  "scenario_id": source_manifest["scenario_id"],
                  "T_seconds": source_manifest["T"],
                  "lambda": source_manifest["lambda"],
                  "pickup_seconds": source_manifest["pickup_time"],
                  "drop_seconds": source_manifest["drop_time"],
                  "verified_cutoff_UB": source_manifest["verified_ub"],
                  "leaf_id": source_manifest["leaf_id"], "parent_id": source_manifest["parent_id"],
                  "support_fingerprint": structure["support_fingerprint"],
                  "supports": structure["support"],
                  "effective_gamma_l": str(a), "effective_gamma_u": str(b),
                  "original_model": {"variables": original.NumVars,
                                     "constraints": original.NumConstrs,
                                     "nonzeros": original.NumNZs},
                  "startup_costs": {"source_verification_seconds": verification_seconds,
                                    "model_read_seconds": read_seconds,
                                    "model_structure_audit_seconds": audit_seconds,
                                    "relax_seconds": relax_seconds,
                                    "process_wall_through_relax_seconds": time.perf_counter()-started},
                  "original_rows": original_rows,
                  "whole_arm_deadline_seconds": WHOLE_ARM_SECONDS,
                  "no_historical_rows_in_initial_model": True,
                  "no_mip_transition": True,
                  "gurobi_version": __import__("gurobipy").gurobi.version()}
    save(out / "provenance.json", provenance)
    existing: set[str] = set()
    iteration = 0
    while True:  # no internal iteration, row, solver-time, or Work stopping budget
        round_dir = out / f"round_{iteration:06d}"
        round_dir.mkdir()
        save(out / "inflight.json", {"phase": "optimize", "round": iteration,
                                     "rows_added_so_far": len(existing),
                                     "elapsed_seconds": time.perf_counter()-started})
        configure(model, round_dir / "optimizer.log")
        optimized = time.perf_counter()
        model.optimize()
        optimize_seconds = time.perf_counter() - optimized
        round_record: dict[str, Any] = {
            "round": iteration, "status_code": model.Status,
            "optimize_wall_seconds": optimize_seconds,
            "solver_runtime_seconds": model.Runtime, "solver_work": model.Work,
            "variables": model.NumVars, "constraints": model.NumConstrs,
            "nonzeros": model.NumNZs,
            "process_peak_working_set_bytes_so_far": process_peak_memory_bytes(),
            "cumulative_added_rows": len(existing),
            "process_elapsed_seconds": time.perf_counter()-started}
        if model.Status != GRB.OPTIMAL:
            round_record["status"] = ("observed_lp_infeasible" if model.Status == GRB.INFEASIBLE
                                      else "unknown_lp_not_optimal")
            save(round_dir / "round.json", round_record)
            terminal = round_record["status"]
            break
        round_record["objective"] = model.ObjVal
        residuals = _primal_residuals(model, round_dir, original_rows)
        round_record["residuals"] = residuals
        if (max(residuals["original_maximum_row_violation"],
                residuals["added_maximum_row_violation"],
                residuals["maximum_bound_violation"]) > 1e-5):
            round_record["status"] = "existing_row_violation_or_numeric_rejection"
            round_record["reason"] = "original_or_added_row_or_bound_residual_exceeds_existing_1e-5_guard"
            save(round_dir / "round.json", round_record)
            terminal = round_record["status"]
            break
        values = read(round_dir / "primal.json")
        scan = _scan(values, supports, targets, a, b, arm, source_manifest["lp_sha256"],
                     max(residuals["original_maximum_row_violation"],
                         residuals["added_maximum_row_violation"],
                         residuals["maximum_bound_violation"]),
                     existing, round_dir)
        new_rows = scan.pop("new_rows")
        round_record["scan"] = scan
        round_record["status"] = scan["status"]
        if scan["status"] != "add_all_reliable_new_rows":
            save(round_dir / "round.json", round_record)
            terminal = scan["status"]
            break
        adding = time.perf_counter()
        new_ledger: list[dict[str, Any]] = []
        for cut, scale, signature, model_signature in new_rows:
            name = f"ot_closure_{len(existing):08d}"
            add_cut(model, cut.coeff, name, scale)
            existing.add(model_signature)
            new_ledger.append({"row_signature": signature,
                                 "model_row_signature": model_signature, "name": name,
                                 "kind": cut.kind, "pair": [cut.i, cut.j],
                                 "scale_exact": str(scale),
                                 "coefficients_exact": {k: str(v) for k, v in sorted(cut.coeff.items())},
                                 "added_after_round": iteration})
        model.update()
        with (out / "added_rows.jsonl").open("a", encoding="utf-8") as stream:
            for record in new_ledger:
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False)+"\n")
        round_record["rows_added_this_round"] = len(new_rows)
        round_record["add_rows_wall_seconds"] = time.perf_counter()-adding
        round_record["cumulative_added_rows_after"] = len(existing)
        round_record["model_constraints_after"] = model.NumConstrs
        round_record["model_nonzeros_after"] = model.NumNZs
        save(round_dir / "round.json", round_record)
        iteration += 1
    save(out / "result.json", {"status": terminal, "source": source, "arm": arm,
                                "manifest_sha256": sha(manifest_path),
                                "lp_sha256": source_manifest["lp_sha256"],
                                "completed_rounds": iteration+1,
                                "cumulative_added_rows": len(existing),
                                "last_complete_round": str(round_dir / "round.json"),
                                "last_lp_objective_if_optimal": round_record.get("objective"),
                                "diagnose_wall_seconds_through_result_write":
                                    time.perf_counter()-started,
                                "scope": "Observed numerical fixed-LP family only; no exact or MIP certificate"})


class _WindowsJob:
    """Kill-on-close job, copied in scope from the qualified A2 supervisor."""

    def __init__(self) -> None:
        class BasicLimit(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]
        class IoCounters(ctypes.Structure):
            _fields_ = [(key, ctypes.c_uint64) for key in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
        class ExtendedLimit(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimit), ("IoInfo", IoCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]
        self.api = ctypes.windll.kernel32
        self.api.CreateJobObjectW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p)
        self.api.CreateJobObjectW.restype = ctypes.c_void_p
        self.api.SetInformationJobObject.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint)
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = (ctypes.c_void_p,)
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise RuntimeError("supervisor_job_create_failed")
        info = ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = 0x00002000
        if not self.api.SetInformationJobObject(
                self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close()
            raise RuntimeError("supervisor_job_kill_on_close_failed")

    def assign(self, process: subprocess.Popen[str]) -> None:
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise RuntimeError("supervisor_job_assignment_failed")

    def close(self) -> None:
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def _kill_tree(process: subprocess.Popen[str], job: _WindowsJob | None) -> None:
    if job:
        job.close()
    if os.name == "nt" and process.poll() is None:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, check=False)
    elif os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _wait_with_deadline(process: subprocess.Popen[str], job: _WindowsJob | None,
                        remaining: float) -> tuple[str, str, bool]:
    """The same whole-child deadline path used by real arms and microqualification."""
    try:
        output, error = process.communicate(timeout=max(0.0, remaining))
        return output, error, False
    except subprocess.TimeoutExpired:
        _kill_tree(process, job)
        output, error = process.communicate()
        return output, error, True


def supervise(manifest_path: Path, source: str, arm: str, out: Path) -> int:
    started = time.perf_counter()  # includes per-arm source hashing and process launch
    out.mkdir(parents=True, exist_ok=False)
    process: subprocess.Popen[str] | None = None
    job: _WindowsJob | None = None
    output = error_output = ""
    expired = False
    assigned = False
    before = sha(manifest_path)
    command: list[str] | None = None
    try:
        require_lease(manifest_path, source, arm)
        verify_prepared(manifest_path, source, arm)
        command = [sys.executable, str(Path(__file__).resolve()), "diagnose",
                   "--manifest", str(manifest_path.resolve()), "--source", source,
                   "--arm", arm, "--out-dir", str((out / "diagnostic").resolve())]
        if time.perf_counter()-started >= WHOLE_ARM_SECONDS:
            expired = True
        else:
            ready = out / "supervisor_ready.flag"
            env = os.environ.copy()
            env["ROUND88_OT_CLOSURE_READY_PATH"] = str(ready)
            if os.name == "nt":
                job = _WindowsJob()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt")
            if job:
                job.assign(process)
                assigned = True
            ready.write_text("assigned\n", encoding="ascii")
            remaining = max(0.0, WHOLE_ARM_SECONDS-(time.perf_counter()-started))
            output, error_output, expired = _wait_with_deadline(process, job, remaining)
            if job:
                job.close()
    except Exception as exc:
        if process:
            _kill_tree(process, job)
        elif job:
            job.close()
        error_output += "\nsupervisor_exception=" + repr(exc)
    (out / "stdout.txt").write_text(output, encoding="utf-8")
    (out / "stderr.txt").write_text(error_output, encoding="utf-8")
    after = sha(manifest_path) if manifest_path.is_file() else None
    final_identity_ok = False
    if after == before:
        try:
            require_lease(manifest_path, source, arm)
            verify_prepared(manifest_path, source, arm)
            final_identity_ok = True
        except Exception as exc:
            error_output += "\nfinal_identity_exception=" + repr(exc)
            (out / "stderr.txt").write_text(error_output, encoding="utf-8")
    elapsed = time.perf_counter()-started
    child_path = out / "diagnostic/result.json"
    child = None
    if child_path.is_file():
        try:
            child = read(child_path)
        except (OSError, ValueError):
            pass
    if expired or elapsed > WHOLE_ARM_SECONDS:
        status = "unknown_whole_diagnostic_deadline"
    elif not final_identity_ok:
        status = "invalid_source_or_manifest_drift"
    elif process is None or process.returncode != 0 or child is None:
        status = "invalid_or_unknown_diagnostic_failure"
    elif child.get("manifest_sha256") != before or child.get("source") != source or child.get("arm") != arm:
        status = "invalid_result_identity"
    else:
        status = child["status"]
    receipt = {"status": status, "whole_arm_limit_seconds": WHOLE_ARM_SECONDS,
               "whole_arm_wall_seconds_before_receipt": elapsed,
               "exit_code": process.returncode if process else None,
               "child_pid": process.pid if process else None,
               "source": source, "arm": arm, "manifest_sha256_before": before,
               "manifest_sha256_after": after, "diagnostic_result_status":
                   child.get("status") if child else None,
               "command": command, "timed_out": expired or elapsed > WHOLE_ARM_SECONDS,
               "source_identity_consistent_after": final_identity_ok,
               "job_object_assigned": assigned if os.name == "nt" else None}
    save(out / "supervision.json", receipt)
    after_write = time.perf_counter()-started
    if after_write > WHOLE_ARM_SECONDS and status != "unknown_whole_diagnostic_deadline":
        receipt["status"] = "unknown_whole_diagnostic_deadline"
        receipt["timed_out"] = True
        receipt["after_first_receipt_wall_seconds"] = after_write
        save(out / "supervision.json", receipt)
    print(receipt["status"])
    return 0 if receipt["status"] in {
        "complete_scan_no_observed_violation", "no_reliable_new_row",
        "existing_row_violation_or_numeric_rejection", "observed_lp_infeasible",
        "unknown_lp_not_optimal"} else 124 if (
        receipt["status"] == "unknown_whole_diagnostic_deadline") else 125


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare", help="freeze source identities, never Optimize")
    p.add_argument("--out-dir", type=Path, required=True)
    ps = commands.add_parser("prepare-supervise", help="externally time shared preparation")
    ps.add_argument("--out-dir", type=Path, required=True)
    for mode in ("supervise", "diagnose"):
        part = commands.add_parser(mode)
        part.add_argument("--manifest", type=Path, required=True)
        part.add_argument("--source", choices=tuple(SOURCES), required=True)
        part.add_argument("--arm", choices=ARMS, required=True)
        part.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out_dir)
        return 0
    if args.command == "prepare-supervise":
        return supervise_prepare(args.out_dir)
    if args.command == "supervise":
        return supervise(args.manifest, args.source, args.arm, args.out_dir)
    diagnose(args.manifest, args.source, args.arm, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
