#!/usr/bin/env python3
"""Source-anchored semantic audit of Round 36 proof/anchor separation."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import round36_common as common


OUT = common.OUT
TREE = common.ROOT / "src" / "PaperExternalGiniTree.cpp"
MAIN = common.ROOT / "src" / "main.cpp"
GEOMETRY = common.ROOT / "src" / "GiniFrontierGeometry.cpp"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def line_number(text: str, fragment: str) -> int:
    position = text.find(fragment)
    return text.count("\n", 0, position) + 1 if position >= 0 else -1


def balanced_body(text: str, marker: str) -> str:
    """Return the brace-balanced body beginning after a unique marker."""
    marker_position = text.find(marker)
    if marker_position < 0:
        return ""
    opening = text.find("{", marker_position + len(marker))
    if opening < 0:
        return ""
    depth = 0
    for position in range(opening, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return text[opening + 1:position]
    return ""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def main() -> int:
    sources = {
        "main": MAIN.read_text(encoding="utf-8", errors="replace"),
        "tree": TREE.read_text(encoding="utf-8", errors="replace"),
        "geometry": GEOMETRY.read_text(encoding="utf-8", errors="replace"),
    }
    compact = {name: normalized(value) for name, value in sources.items()}
    invariants = [
        {
            "id": "S01_startup_pair",
            "claim": "BW arms choose min verified startup as proof and max as anchor",
            "source": "main",
            "fragment": "result.round36_proof_incumbent_launch = std::min( result.round36_hga_start_objective, result.round36_simple_start_objective); result.round36_decomposition_anchor_launch = std::max( result.round36_hga_start_objective, result.round36_simple_start_objective);",
        },
        {
            "id": "S02_proof_range",
            "claim": "proof-relevant Gini upper range derives from verified result upper bound",
            "source": "main",
            "fragment": "const double relevant_gini_upper_for_improvement = std::min(result.upper_bound, gini_max_possible);",
        },
        {
            "id": "S03_proof_launch",
            "claim": "tree proof incumbent is the independently verified seed objective",
            "source": "tree",
            "fragment": "const double proof_incumbent_launch = verified_seed.objective;",
        },
        {
            "id": "S04_anchor_grid_intersection",
            "claim": "anchor defines grid placement while root proof range defines active intersection",
            "source": "tree",
            "fragment": "makeProofRelevantAnchorGrid( root_gamma_L, root_gamma_U, anchor_grid_upper, options.frontier_intervals, 1e-7)",
        },
        {
            "id": "S05_anchor_safety_reject",
            "claim": "unsafe, unverified, or weaker-current-proof launch configurations are rejected",
            "source": "tree",
            "fragment": "round36ProofAnchorLaunchContractValid( verified_seed.round36_anchor_safety_valid, verified_seed.round36_proof_incumbent_launch, proof_incumbent_launch, decomposition_anchor_launch, 1e-7) && causal_grid.valid",
        },
        {
            "id": "S06_exact_active_cover",
            "claim": "active anchor intersections receive an exact coverage check",
            "source": "geometry",
            "fragment": "exactIntervalCoverage( {proof_lower, proof_upper}, result.active_intervals, tol, &coverage_reason)",
        },
        {
            "id": "S07_initial_cutoff",
            "claim": "initial leaf cutoff uses verified proof seed, not anchor",
            "source": "tree",
            "fragment": "leaf.cutoff = verified_seed.objective;",
        },
        {
            "id": "S08_runtime_proof_ub",
            "claim": "runtime global UB starts from the verified proof seed",
            "source": "tree",
            "fragment": "double verified_ub = verified_seed.objective;",
        },
        {
            "id": "S09_cutoff_tightening",
            "claim": "better verified native incumbents tighten the proof cutoff",
            "source": "tree",
            "fragment": "outcome.incumbent_independently_verified && outcome.incumbent_objective < verified_ub - 1e-9) { verified_ub = outcome.incumbent_objective;",
        },
        {
            "id": "S10_split_isolation",
            "claim": "causal split receives proof UB and launch-frozen anchor separately",
            "source": "tree",
            "fragment": "evaluateC6CurrentSplitDecision( bounded.lower_bound, verified_ub, decomposition_anchor_launch, options.round36_c6_split_normalization,",
        },
        {
            "id": "S11_eta_formulas",
            "claim": "both proof and anchor eta denominators are ledgered from the same gain",
            "source": "tree",
            "fragment": "decision.eta_proof = gain / std::max( 1e-7, proof_upper_bound - current_parent_bound); decision.eta_anchor = gain / std::max( 1e-7, anchor_upper_bound - current_parent_bound);",
        },
        {
            "id": "S12_final_ub",
            "claim": "serialized final UB is the verified proof UB",
            "source": "tree",
            "fragment": "result.external_gini_tree_verified_upper_bound = verified_ub;",
        },
        {
            "id": "S13_final_verifier",
            "claim": "final incumbent routes pass the original verifier",
            "source": "tree",
            "fragment": "result.verification = verifySolution(instance, best_routes, options.lambda);",
        },
        {
            "id": "S14_certificate",
            "claim": "strict certificate compares the valid LB with verified proof UB",
            "source": "tree",
            "fragment": "certificate_input.verified_ub = verified_ub;",
        },
        {
            "id": "S15_default_wrapper",
            "claim": "legacy C6 wrapper delegates with proof normalization and equal proof/anchor UB",
            "source": "tree",
            "fragment": "current_parent_bound, verified_upper_bound, verified_upper_bound, \"proof\", left, right, normalized_split_threshold, certificate_tolerance",
        },
    ]
    rows = []
    for invariant in invariants:
        fragment = normalized(invariant["fragment"])
        passed = fragment in compact[invariant["source"]]
        original = sources[invariant["source"]]
        first_token = invariant["fragment"].strip().splitlines()[0].strip()
        rows.append({
            **{key: invariant[key] for key in ("id", "claim", "source")},
            "passed": passed,
            "source_path": common.relative({
                "main": MAIN, "tree": TREE, "geometry": GEOMETRY,
            }[invariant["source"]]),
            "approximate_line": line_number(original, first_token),
            "normalized_fragment_sha256": hashlib.sha256(
                fragment.encode()).hexdigest(),
        })

    tree_lines = sources["tree"].splitlines()
    ub_assignments = []
    for index, line in enumerate(tree_lines):
        if re.match(r"^\s*(?:double\s+)?verified_ub\s*=", line):
            context = "\n".join(tree_lines[max(0, index - 4):index + 2])
            initial = "double verified_ub = verified_seed.objective" in line
            guarded = "incumbent_independently_verified" in context
            ub_assignments.append({
                "line": index + 1, "text": line.strip(),
                "initial_from_verified_seed": initial,
                "guarded_by_independent_verifier": guarded,
                "passed": initial or guarded,
            })
    rows.append({
        "id": "S16_all_ub_updates_verified",
        "claim": "every verified_ub assignment is seed initialization or independently verified",
        "source": "tree", "passed": bool(ub_assignments) and all(
            row["passed"] for row in ub_assignments),
        "source_path": common.relative(TREE),
        "approximate_line": min(row["line"] for row in ub_assignments),
        "normalized_fragment_sha256": hashlib.sha256(json.dumps(
            ub_assignments, sort_keys=True).encode()).hexdigest(),
    })

    anchor_occurrences = []
    forbidden = ("cutoff", "prun", "certificate_input", "verified_ub =",
                 "upper_bound =", "penalty")
    for index, line in enumerate(tree_lines):
        if "decomposition_anchor_launch" not in line:
            continue
        context_lines = tree_lines[max(0, index - 2):index + 3]
        context = " ".join(value.strip() for value in context_lines)
        violations = [token for token in forbidden if token in context.lower()]
        anchor_occurrences.append({
            "line": index + 1, "source_path": common.relative(TREE),
            "source_line": line.strip(),
            "context_sha256": hashlib.sha256(normalized(context).encode()).hexdigest(),
            "forbidden_consumer_tokens": ";".join(violations),
            "passed": not violations,
        })
    rows.append({
        "id": "S17_anchor_consumer_exclusion",
        "claim": "decomposition anchor is absent from cutoff/pruning/global-UB/certificate consumers",
        "source": "tree", "passed": bool(anchor_occurrences) and all(
            row["passed"] for row in anchor_occurrences),
        "source_path": common.relative(TREE),
        "approximate_line": min(row["line"] for row in anchor_occurrences),
        "normalized_fragment_sha256": hashlib.sha256(json.dumps(
            anchor_occurrences, sort_keys=True).encode()).hexdigest(),
    })

    c5_body = balanced_body(
        sources["tree"],
        "C5BoundTargetSplitDecision evaluateC5BoundTargetSplitDecision(\n"
        "    double parent_lower_bound,")
    c6_body = balanced_body(
        sources["tree"],
        "C6CurrentSplitDecision evaluateC6CurrentSplitDecision(\n"
        "    double current_parent_bound,\n"
        "    double proof_upper_bound,")
    split_decision_body = c5_body + "\n" + c6_body
    hardware_pattern = re.compile(
        r"\b(?:elapsed|seconds|runtime|work|nodes?|machine|threads?|"
        r"memory|clock|chrono)\b", re.IGNORECASE)
    hardware_tokens = sorted(set(
        match.group(0).lower()
        for match in hardware_pattern.finditer(split_decision_body)))
    rows.append({
        "id": "S18_hardware_independent_split_inputs",
        "claim": "C6 split decisions depend only on bounds, child LP states, rho, and tolerance",
        "source": "tree",
        "passed": bool(c5_body) and bool(c6_body) and not hardware_tokens,
        "source_path": common.relative(TREE),
        "approximate_line": line_number(
            sources["tree"],
            "C5BoundTargetSplitDecision evaluateC5BoundTargetSplitDecision("),
        "normalized_fragment_sha256": hashlib.sha256(
            normalized(split_decision_body).encode()).hexdigest(),
    })

    native_target_body = balanced_body(
        sources["tree"], "auto runC6NativeTarget = [&](")
    time_slice_pattern = re.compile(
        r"request\.time_limit_seconds|requested_quantum_seconds|planLaunch|"
        r"per[_-]?(?:leaf|action)", re.IGNORECASE)
    time_slice_tokens = sorted(set(
        match.group(0).lower()
        for match in time_slice_pattern.finditer(native_target_body)))
    global_deadline_only = (
        "const double remaining = globalDeadlineRemaining();" in
            native_target_body
        and "request.global_deadline_remaining_seconds = remaining;" in
            native_target_body
        and not time_slice_tokens
    )
    rows.append({
        "id": "S19_global_deadline_only",
        "claim": "C6 native actions use the remaining global deadline without per-leaf or per-action slices",
        "source": "tree",
        "passed": bool(native_target_body) and global_deadline_only,
        "source_path": common.relative(TREE),
        "approximate_line": line_number(
            sources["tree"], "auto runC6NativeTarget = [&]("),
        "normalized_fragment_sha256": hashlib.sha256(
            normalized(native_target_body).encode()).hexdigest(),
    })

    write_csv(OUT / "semantic_separation_audit.csv", rows)
    write_csv(OUT / "verified_ub_assignment_audit.csv", ub_assignments)
    write_csv(OUT / "anchor_consumer_occurrence_audit.csv", anchor_occurrences)
    passed = all(bool(row["passed"]) for row in rows)
    summary = {
        "schema": "round36-semantic-separation-audit-v1",
        "round_id": 36,
        "passed": passed,
        "semantic_invariants": len(rows),
        "semantic_invariants_passed": sum(bool(row["passed"]) for row in rows),
        "verified_ub_assignments": len(ub_assignments),
        "verified_ub_assignments_guarded": sum(bool(row["passed"])
                                               for row in ub_assignments),
        "anchor_symbol_occurrences": len(anchor_occurrences),
        "anchor_forbidden_consumer_occurrences": sum(not bool(row["passed"])
                                                     for row in anchor_occurrences),
        "hardware_dependent_split_tokens": hardware_tokens,
        "native_action_time_slice_tokens": time_slice_tokens,
        "source_sha256": {
            common.relative(path): sha256(path) for path in (MAIN, TREE, GEOMETRY)
        },
    }
    write_text(OUT / "semantic_separation_audit.json",
               json.dumps(summary, indent=2, sort_keys=True) + "\n")
    report = f"""# Round 36 semantic separation audit

- Semantic invariants: {summary['semantic_invariants_passed']}/
  {summary['semantic_invariants']} passed.
- `verified_ub` assignments: {summary['verified_ub_assignments_guarded']}/
  {summary['verified_ub_assignments']} originate from the verified seed or are
  guarded by independent incumbent verification.
- Decomposition-anchor symbol occurrences: {summary['anchor_symbol_occurrences']}.
- Forbidden anchor consumers: {summary['anchor_forbidden_consumer_occurrences']}.
- Hardware-dependent split-decision tokens: {len(hardware_tokens)}.
- Per-leaf/per-action native time-slice tokens: {len(time_slice_tokens)}.

The audit anchors each claim to normalized source fragments and source hashes.
`U_anchor` is confined to launch-frozen grid construction, safety/telemetry,
and the explicit split-normalization intervention. Cutoff, pruning, global UB,
native incumbent updates, final route verification, and strict certification
continue to use the independently verified proof incumbent.
"""
    write_text(OUT / "semantic_separation_audit.md", report)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
