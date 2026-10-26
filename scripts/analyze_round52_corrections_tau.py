#!/usr/bin/env python3
"""Produce additive Round 52 K1-AM corrections and complete tau replay."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
TAU_REFERENCE = 0.07915
TAU_CANDIDATE = 0.08
CERT_EPS = 1e-7
ROOTS = (
    ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47",
    ROOT / "results" / "gf_k1_amf_formulation_rescue_round48",
    ROOT / "results" / "gf_k1_lp_primal_dual_rescue_round49",
    ROOT / "results" / "gf_k1_interval_mip_vnext_round50",
    ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51",
)


def number(row: dict[str, str], *names: str) -> float:
    for name in names:
        value = row.get(name, "")
        if value not in (None, ""):
            return float(value)
    return math.nan


def replay_action(row: dict[str, str], tau: float) -> str:
    parent = number(row, "B_p", "parent_bound")
    left = number(row, "B_L", "left_child_bound")
    right = number(row, "B_R", "right_child_bound")
    if all(math.isfinite(value) for value in (parent, left, right)):
        if min(left, right) <= parent + CERT_EPS:
            return "exact-close"
    score = number(row, "S_AM")
    tolerance = number(row, "score_tolerance")
    if not math.isfinite(tolerance):
        tolerance = 0.0
    if not math.isfinite(score):
        raise ValueError("missing finite S_AM")
    return "split" if score + tolerance >= tau else "native-target"


def semantic_action(action: str) -> str:
    return "MIDPOINT" if action == "split" else "RETAIN"


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instance_from_run(run_id: str, path: Path) -> str:
    match = re.match(r"^[^_]+(?:_[^_]+)*?__(.+)__(?:K[14].*)$", run_id)
    if match:
        return match.group(1)
    parts = path.parts
    if "counterfactual_runs" in parts:
        idx = parts.index("counterfactual_runs")
        return parts[idx + 1].split("__", 1)[0]
    return run_id


def result_outcome(path: Path, selected: str, reason: str) -> str:
    result_path = path.parent / "result.json"
    if result_path.exists():
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            return "|".join((str(payload.get("status", "")),
                             str(payload.get("strict_certificate_class", "")),
                             selected, reason))
        except (OSError, json.JSONDecodeError):
            pass
    return "|".join((selected, reason))


def corrected_mapping() -> None:
    with (ROUND50 / "vnext_counterfactual_pair_summary.csv").open(
            encoding="utf-8", newline="") as src:
        pairs = list(csv.DictReader(src))
    rows: list[dict[str, object]] = []
    pair_by_case = {row["case"]: row for row in pairs}
    for pair in pairs:
        case = pair["case"]
        ledger = (ROUND50 / "counterfactual_runs" / f"{case}__retain" /
                  "adaptive_mass_decision_ledger.csv")
        with ledger.open(encoding="utf-8", newline="") as src:
            decisions = list(csv.DictReader(src))
        target = next(row for row in decisions
                      if row["interval_id"] == pair["interval_id"])
        raw_action = replay_action(target, TAU_REFERENCE)
        actual = semantic_action(raw_action)
        rows.append({
            "case": case,
            "instance": pair["instance"],
            "interval_id": pair["interval_id"],
            "parent_id": target["parent_id"],
            "depth": target["depth"],
            "S_AM": target["S_AM"],
            "score_tolerance": target["score_tolerance"],
            "authoritative_raw_action": raw_action,
            "K1_AM_action": actual,
            "round50_reported_action": pair["new_label"],
            "round50_action_correct": pair["new_label"] == actual,
            "mapping_rule": "split=>MIDPOINT; native-target/exact-close=>RETAIN",
            "source_ledger": relative(ledger),
            "source_ledger_sha256": file_sha(ledger),
        })

    # The requested high-imbalance root anchor is distinct from Round 50's
    # matched difficult child L0.1.0 and is included explicitly.
    ledger = (ROUND50 / "counterfactual_runs" /
              "high_imbalance_matched__retain" /
              "adaptive_mass_decision_ledger.csv")
    with ledger.open(encoding="utf-8", newline="") as src:
        root_row = next(row for row in csv.DictReader(src)
                        if row["interval_id"] == "L0")
    raw_action = replay_action(root_row, TAU_REFERENCE)
    rows.append({
        "case": "high_imbalance_root_anchor",
        "instance": "high_imbalance_seed3201",
        "interval_id": "L0",
        "parent_id": root_row["parent_id"],
        "depth": root_row["depth"],
        "S_AM": root_row["S_AM"],
        "score_tolerance": root_row["score_tolerance"],
        "authoritative_raw_action": raw_action,
        "K1_AM_action": semantic_action(raw_action),
        "round50_reported_action": "not_a_pair_target",
        "round50_action_correct": True,
        "mapping_rule": "split=>MIDPOINT; native-target/exact-close=>RETAIN",
        "source_ledger": relative(ledger),
        "source_ledger_sha256": file_sha(ledger),
    })

    fields = list(rows[0].keys())
    with (OUT / "corrected_k1_action_mapping.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    mapping = {row["case"]: row for row in rows}
    error_rows: list[dict[str, object]] = []
    for pair in pairs:
        action = str(mapping[pair["case"]]["K1_AM_action"])
        old_error = pair["severe_error"].lower() == "true"
        retain_preferred = pair["severe_error_kind"] == "false_split"
        midpoint_preferred = pair["severe_error_kind"] == "false_retain"
        false_split = old_error and action == "MIDPOINT" and retain_preferred
        false_retain = old_error and action == "RETAIN" and midpoint_preferred
        error_rows.append({
            "case": pair["case"],
            "instance": pair["instance"],
            "interval_id": pair["interval_id"],
            "K1_AM_action": action,
            "retain_certificate": pair["retain_certificate"],
            "midpoint_certificate": pair["midpoint_certificate"],
            "retain_work": pair["retain_work"],
            "midpoint_work": pair["midpoint_work"],
            "retain_gi_1200": pair["retain_gi_1200"],
            "midpoint_gi_1200": pair["midpoint_gi_1200"],
            "pair_difference_severe": old_error,
            "outcome_preferred_action_if_severe": (
                "RETAIN" if retain_preferred else
                "MIDPOINT" if midpoint_preferred else "NONE"),
            "false_split": false_split,
            "false_retain": false_retain,
            "severe_split_error": false_split or false_retain,
            "corrected_error_kind": (
                "false_split" if false_split else
                "false_retain" if false_retain else "none"),
            "source_pair_summary": relative(
                ROUND50 / "vnext_counterfactual_pair_summary.csv"),
        })
    with (OUT / "corrected_split_error_audit.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(error_rows[0].keys()))
        writer.writeheader()
        writer.writerows(error_rows)

    false_split_count = sum(bool(row["false_split"]) for row in error_rows)
    false_retain_count = sum(bool(row["false_retain"]) for row in error_rows)
    changed = [row for row in rows[:-1] if not row["round50_action_correct"]]
    (OUT / "round50_k1_action_mapping_erratum.md").write_text(
        f"""# Round 50 K1-AM action-mapping erratum

Round 50's pair interpretation inferred K1-AM actions from comparison labels.
The authoritative adaptive-mass ledger instead records lifecycle actions:
`split` means MIDPOINT, while `native-target` and `exact-close` both retain the
parent rather than creating a midpoint split. Historical raw evidence is not
modified.

The corrected mapping changes {len(changed)} of seven pair labels. Major root,
strong-control root, tight3102 L0.0, and the high-imbalance root are verified as
RETAIN, RETAIN, RETAIN, and MIDPOINT respectively. The high-imbalance Round 50
pair target is the distinct child L0.1.0 and is RETAIN.

Under the frozen ratio-plus-absolute rule the corrected audit has
{false_split_count} severe false split(s) and {false_retain_count} severe false
retain(s), {false_split_count + false_retain_count} total. The major root is not
a K1-AM false split; strong-control root, tight3102 L0.0, and high-imbalance
L0.1.0 are severe false retains. This additive erratum supersedes only the
mapping/count interpretation in Round 50, not its native logs, exact results,
or production-v0 decision.
""", encoding="utf-8")


def append_replay(rows: list[dict[str, object]], ledger: Path,
                  source_kind: str) -> None:
    ledger_sha = file_sha(ledger)
    with ledger.open(encoding="utf-8-sig", newline="") as src:
        for source_row_number, row in enumerate(csv.DictReader(src), start=2):
            k0 = row.get("K0", "")
            if k0 and int(float(k0)) != 1:
                continue
            run_id = row.get("run_id") or row.get("source_run_id") or ledger.parent.name
            reference_action = replay_action(row, TAU_REFERENCE)
            candidate_action = replay_action(row, TAU_CANDIDATE)
            score = number(row, "S_AM")
            tolerance = number(row, "score_tolerance")
            if not math.isfinite(tolerance):
                tolerance = 0.0
            selected = row.get("selected_action") or row.get("round47_replay_action", "")
            reason = row.get("deterministic_reason") or row.get("round46_reason", "")
            rows.append({
                "record_id": len(rows) + 1,
                "round_root": ledger.parts[ledger.parts.index("results") + 1],
                "source_kind": source_kind,
                "source_run_id": run_id,
                "stage": row.get("stage", ""),
                "instance": row.get("instance") or instance_from_run(run_id, ledger),
                "interval": row.get("interval_id", ""),
                "parent_id": row.get("parent_id", ""),
                "depth": row.get("depth", ""),
                "decision_sequence": row.get("decision_sequence", ""),
                "S_AM": format(score, ".17g"),
                "score_tolerance": format(tolerance, ".17g"),
                "action_at_0_07915": reference_action,
                "action_at_0_08": candidate_action,
                "semantic_action_at_0_07915": semantic_action(reference_action),
                "semantic_action_at_0_08": semantic_action(candidate_action),
                "action_changed": reference_action != candidate_action,
                "raw_score_margin_to_0_07915": format(score - TAU_REFERENCE, ".17g"),
                "raw_score_margin_to_0_08": format(score - TAU_CANDIDATE, ".17g"),
                "tolerance_adjusted_margin_to_0_07915": format(
                    score + tolerance - TAU_REFERENCE, ".17g"),
                "tolerance_adjusted_margin_to_0_08": format(
                    score + tolerance - TAU_CANDIDATE, ".17g"),
                "historical_selected_action": selected,
                "historical_outcome": result_outcome(ledger, selected, reason),
                "historical_reason": reason,
                "source_ledger": relative(ledger),
                "source_ledger_sha256": ledger_sha,
                "source_row_number": source_row_number,
            })


def tau_replay() -> None:
    rows: list[dict[str, object]] = []
    authoritative_replay = ROOTS[0] / "adaptive_mass_action_replay.csv"
    append_replay(rows, authoritative_replay, "round47_authoritative_offline_replay")
    ledgers: list[Path] = []
    for evidence_root in ROOTS:
        for ledger in evidence_root.rglob("adaptive_mass_decision_ledger.csv"):
            relative_parts = ledger.relative_to(evidence_root).parts
            if "external" in relative_parts:
                # Round 47/50 often mirror the same ledger at the run root;
                # Round 48/49 sometimes retain only the external-engine copy.
                # Keep the latter while excluding only a provable path mirror.
                run_root_copy = ledger.parent.parent / ledger.name
                if run_root_copy.exists():
                    continue
            ledgers.append(ledger)
    for ledger in sorted(set(ledgers), key=lambda path: relative(path)):
        append_replay(rows, ledger, "live_adaptive_mass_decision_ledger")

    if not rows:
        raise RuntimeError("no K1-AM replay rows discovered")
    fields = list(rows[0].keys())
    with (OUT / "tau_008_complete_replay.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    changed = [row for row in rows if row["action_changed"]]
    with (OUT / "tau_008_changed_decisions.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(changed)

    closest = sorted(
        (row for row in rows
         if row["action_at_0_07915"] != "exact-close"),
        key=lambda row: abs(float(str(row["tolerance_adjusted_margin_to_0_08"]))))[:20]
    anchors = {
        "major_root": ("round39_small_medium_V12_M3_Q30_slot08_seed1343324363", "L0", "RETAIN"),
        "strong_control_root": ("round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "L0", "RETAIN"),
        "tight3102_L0.0": ("tight_T_seed3102", "L0.0", "RETAIN"),
        "high_imbalance_root": ("high_imbalance_seed3201", "L0", "MIDPOINT"),
    }
    anchor_results: list[tuple[str, str, bool]] = []
    for name, (instance, interval, expected) in anchors.items():
        # "Original anchor" means the canonical Round 47 stage-5 K1-AM run,
        # not a legacy Round 46 rho arm replayed offline during Round 47.
        matches = [row for row in rows if row["instance"] == instance and
                   row["interval"] == interval and
                   row["source_kind"] == "live_adaptive_mass_decision_ledger" and
                   "/runs/stage5_1800s__" in str(row["source_ledger"]) and
                   str(row["source_run_id"]).endswith("__K1-AM")]
        actions = sorted({str(row["semantic_action_at_0_08"]) for row in matches})
        passed = bool(matches) and actions == [expected]
        anchor_results.append((name, "/".join(actions) if actions else "missing", passed))
    if not all(item[2] for item in anchor_results):
        raise RuntimeError(f"tau anchor audit failed: {anchor_results}")

    round_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["round_root"])
        round_counts[key] = round_counts.get(key, 0) + 1
    closest_lines = "\n".join(
        f"- `{row['instance']}` `{row['interval']}`: S_AM={row['S_AM']}, "
        f"adjusted margin to 0.08={row['tolerance_adjusted_margin_to_0_08']}"
        for row in closest)
    anchor_lines = "\n".join(
        f"- {name}: {action} ({'pass' if passed else 'FAIL'})"
        for name, action, passed in anchor_results)
    (OUT / "tau_008_margin_audit.md").write_text(
        f"""# Tau 0.08 complete replay and margin audit

The replay evaluated {len(rows)} available K1-AM decision records from
{len(ledgers)} non-duplicated native ledgers plus the authoritative Round 47
offline replay. Exact-parent closure is reconstructed first from child/parent
bounds at certificate tolerance 1e-7; otherwise the frozen rule compares
`S_AM + score_tolerance` with tau. External mirror ledgers are excluded to avoid
byte-for-byte duplicate records; every retained row includes its source hash and
row number.

Records by evidence root: {json.dumps(round_counts, sort_keys=True)}.
Changed actions between 0.07915 and 0.08: {len(changed)}.

## Anchor audit

{anchor_lines}

## Twenty closest non-closure margins to 0.08

{closest_lines}

The complete row-level evidence, including both raw and tolerance-adjusted
margins, is in `tau_008_complete_replay.csv`.
""", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    corrected_mapping()
    tau_replay()
    print("wrote action erratum and complete tau replay")


if __name__ == "__main__":
    main()
