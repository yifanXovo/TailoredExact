#!/usr/bin/env python3
"""Freeze the non-destructive Round 45 completion contract and run matrix."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from typing import Any

import round45_experiment as round45


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
COMPLETION = OUT / "completion"
RUNS = OUT / "runs"
PLACEHOLDER = "PENDING_FINAL_COMPLETION_EXECUTABLE_SHA256"
CHECKPOINTS = "300;1200;3600"
LOCAL_EXPECTED = (
    "command.json;parent_state.json;result.json;global_bound_trace.csv;"
    "interval_tree_events.csv;interval_coverage_ledger.csv;"
    "parametric_segment_ledger.csv;parametric_breakpoint_ledger.csv;"
    "split_point_choice_ledger.csv;artifact_manifest.csv;completion_marker.json"
)
FULL_EXPECTED = (
    "command.json;process_phases.csv;progress.csv;result.json;"
    "global_bound_trace.csv;interval_tree_events.csv;"
    "interval_coverage_ledger.csv;timing_decision_ledger.csv;"
    "certificate_ledger.csv;artifact_manifest.csv;completion_marker.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"empty completion matrix: {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def base_row(*, row_id: str, stage: str, instance_id: str,
             input_path: Path, arm: str, k0: int, timing: str,
             threshold: str, point: str, expected: str,
             parent_id: str = "", lower: str = "", upper: str = "",
             selection_use: str = "") -> dict[str, Any]:
    return {
        "row_id": row_id,
        "stage": stage,
        "instance": instance_id,
        "input_path": input_path.relative_to(ROOT).as_posix(),
        "input_sha256": sha256(input_path),
        "arm": arm,
        "K0": k0,
        "timing_rule": timing,
        "timing_threshold": threshold,
        "point_rule": point,
        "envelope_mode": "all-parent-scope",
        "lookahead_mode": "frontier-d2",
        "process_cap_seconds": 3600,
        "required_checkpoints_seconds": CHECKPOINTS,
        "acceptable_terminal": "strict_exact_or_honest_3600s_cap",
        "executable_sha256": PLACEHOLDER,
        "expected_evidence_files": expected,
        "completion_state": "required_pending",
        "run_directory": f"completion/runs/{row_id}",
        "parent_id": parent_id,
        "parent_lower": lower,
        "parent_upper": upper,
        "selection_use": selection_use,
    }


def item_path(inventory: dict[str, dict[str, Any]], instance_id: str) -> Path:
    item = inventory[instance_id]
    path = Path(item.get("instance_path") or item.get("path") or item["input"])
    return path if path.is_absolute() else ROOT / path


def material_parents(inventory: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    parents: list[dict[str, str]] = []
    for directory in sorted(RUNS.glob("timing_census__*")):
        instance_id = directory.name.split("__")[1]
        rows = read_csv(directory / "timing_decision_ledger.csv")
        for row in rows:
            parents.append({
                "instance": instance_id, "input": str(item_path(inventory, instance_id)),
                "parent_id": row["parent_id"], "lower": row["lower"],
                "upper": row["upper"], "K0": "4", "selection_use": "true",
                "selection_reason": "all_material_K4_roots_superset_of_actual_and_near_threshold_leaves",
            })
    if len(parents) != 20:
        raise RuntimeError(f"expected 20 frozen material K4 parents, got {len(parents)}")
    return parents


def complex_parents(inventory: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    freeze = json.loads((OUT / "complex_panel_freeze.json").read_text(encoding="utf-8"))
    dev = {Path(path).stem for role in ("v20_development", "v50_development")
           for path in freeze[role]}
    parents: list[dict[str, str]] = []
    for directory in sorted(RUNS.glob("complex_timing_atlas__*")):
        command = json.loads((directory / "command.json").read_text(encoding="utf-8"))
        instance_id = command["instance_id"]
        if instance_id not in dev:
            continue
        for row in read_csv(directory / "timing_decision_ledger.csv"):
            if row["old_c6_action"] != "split" and row["final_action"] != "split":
                continue
            parents.append({
                "instance": instance_id, "input": str(item_path(inventory, instance_id)),
                "parent_id": row["parent_id"], "lower": row["lower"],
                "upper": row["upper"], "K0": "4", "selection_use": "true",
                "selection_reason": "frozen_complex_development_old_c6_or_gamma_veto_split",
            })
    if len(parents) != 5:
        raise RuntimeError(f"expected 5 frozen complex development parents, got {len(parents)}")
    return parents


def validation_parents(inventory: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    parents: list[dict[str, str]] = []
    for directory in sorted(RUNS.glob("validation__*")):
        events = read_csv(directory / "interval_tree_events.csv")
        split_ids = {row["leaf_id"] for row in events
                     if row["event"] == "round44_atomic_split"}
        if not split_ids:
            continue
        command = json.loads((directory / "command.json").read_text(encoding="utf-8"))
        instance_id = command["instance_id"]
        decisions = {row["parent_id"]: row for row in
                     read_csv(directory / "timing_decision_ledger.csv")}
        for parent_id in sorted(split_ids):
            row = decisions[parent_id]
            parents.append({
                "instance": instance_id, "input": str(item_path(inventory, instance_id)),
                "parent_id": parent_id, "lower": row["lower"],
                "upper": row["upper"], "K0": "4", "selection_use": "false",
                "selection_reason": "post_selection_validation_live_gamma_veto_split",
            })
    if len(parents) != 2:
        raise RuntimeError(f"expected 2 consumed-validation split parents, got {len(parents)}")
    return parents


def add_counterfactual(rows: list[dict[str, Any]], parent: dict[str, str],
                       stage: str) -> None:
    instance = parent["instance"]
    path = Path(parent["input"])
    safe_parent = parent["parent_id"].replace("/", "_")
    for arm, point in (("retain", "retain"), ("midpoint-split", "midpoint"),
                       ("pmm-split", "pmm"), ("fpmm-split", "fpmm")):
        row_id = f"cf__{instance}__k{parent['K0']}__{safe_parent}__{point}"
        rows.append(base_row(
            row_id=row_id, stage=stage, instance_id=instance, input_path=path,
            arm=arm, k0=int(parent["K0"]), timing="gamma-veto",
            threshold="rho_gamma=0.012", point=point, expected=LOCAL_EXPECTED,
            parent_id=parent["parent_id"], lower=parent["lower"],
            upper=parent["upper"], selection_use=parent["selection_use"]))


def main() -> int:
    COMPLETION.mkdir(parents=True, exist_ok=True)
    inventory = round45.inventory()
    material = material_parents(inventory)
    complex_dev = complex_parents(inventory)
    post_selection = validation_parents(inventory)

    # A K1 root superset is frozen for every material instance. The common rule
    # will later determine which of these states is a true split state.
    k1_parents: list[dict[str, str]] = []
    by_instance: dict[str, list[dict[str, str]]] = {}
    for parent in material:
        by_instance.setdefault(parent["instance"], []).append(parent)
    for instance, values in sorted(by_instance.items()):
        k1_parents.append({
            "instance": instance, "input": values[0]["input"],
            "parent_id": "K1ROOT", "lower": min(values, key=lambda x: float(x["lower"]))["lower"],
            "upper": max(values, key=lambda x: float(x["upper"]))["upper"],
            "K0": "1", "selection_use": "true",
            "selection_reason": "frozen_K1_material_root_superset",
        })

    rows: list[dict[str, Any]] = []
    for parent in material + complex_dev + k1_parents:
        add_counterfactual(rows, parent, "true_counterfactual_development")
    for parent in post_selection:
        add_counterfactual(rows, parent, "post_selection_counterfactual")

    # Contemporaneous small sentinels.
    sentinels = {
        "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
            ("pgrb", "c6", "gamma-veto", "no-adaptive"),
        "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
            ("pgrb", "c6", "gamma-veto", "no-adaptive"),
        "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
            ("pgrb", "c6", "gamma-veto", "d-r43", "no-adaptive"),
    }
    for instance, arms in sentinels.items():
        for arm in arms:
            timing = arm if arm in {"gamma-veto", "d-r43", "no-adaptive"} else "n/a"
            threshold = ("rho_gamma=0.012" if arm == "gamma-veto" else
                         "rho_D=0.10" if arm == "d-r43" else "n/a")
            rows.append(base_row(
                row_id=f"sentinel__{instance}__{arm}", stage="small_sentinel",
                instance_id=instance, input_path=item_path(inventory, instance),
                arm=arm, k0=4, timing=timing, threshold=threshold,
                point="midpoint" if arm not in {"pgrb", "c6"} else "n/a",
                expected=FULL_EXPECTED))

    # K1 versus K4: all material, both material-validation, and one frozen V20
    # plus one frozen V50 development instance.
    validation_material = [
        "round39_small_hard_V10_M2_Q20_slot03_seed490008310",
        "round39_small_medium_V8_M2_Q20_slot02_seed890603285",
    ]
    k_instances = sorted(by_instance) + validation_material + [
        "high_imbalance_seed3201",
        "round32_multi_m_tight_T_V50_M2_seed104207248",
    ]
    for instance in k_instances:
        for k0 in (1, 4):
            rows.append(base_row(
                row_id=f"kcompare__{instance}__k{k0}_gamma_veto",
                stage="k1_k4_completion", instance_id=instance,
                input_path=item_path(inventory, instance), arm=f"K{k0}-gamma-veto",
                k0=k0, timing="gamma-veto", threshold="rho_gamma=0.012",
                point="midpoint", expected=FULL_EXPECTED))

    # Complete frozen complex matrix and secondary development diagnostic.
    complex_freeze = json.loads((OUT / "complex_panel_freeze.json").read_text(encoding="utf-8"))
    complex_roles = ("v20_development", "v20_confirmation",
                     "v50_development", "v50_confirmation")
    for role in complex_roles:
        for rel in complex_freeze[role]:
            instance = Path(rel).stem
            for arm in ("pgrb", "c6", "gamma-veto", "no-adaptive"):
                timing = arm if arm in {"gamma-veto", "no-adaptive"} else "n/a"
                threshold = "rho_gamma=0.012" if arm == "gamma-veto" else "n/a"
                rows.append(base_row(
                    row_id=f"complex__{instance}__{arm}",
                    stage=f"complex_mandatory_{role}", instance_id=instance,
                    input_path=ROOT / rel, arm=arm, k0=4, timing=timing,
                    threshold=threshold,
                    point="midpoint" if arm not in {"pgrb", "c6"} else "n/a",
                    expected=FULL_EXPECTED))
            if role.endswith("development"):
                rows.append(base_row(
                    row_id=f"complex__{instance}__d-r43",
                    stage=f"complex_secondary_{role}", instance_id=instance,
                    input_path=ROOT / rel, arm="d-r43", k0=4, timing="d-r43",
                    threshold="rho_D=0.10", point="midpoint",
                    expected=FULL_EXPECTED))

    if len({row["row_id"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate row_id in required completion matrix")
    mandatory_complex = [row for row in rows
                         if row["stage"].startswith("complex_mandatory_")]
    if len(mandatory_complex) != 48:
        raise RuntimeError(f"mandatory complex matrix is {len(mandatory_complex)}, not 48")

    erratum = """# Round 45 completion erratum

The classifications `validated_adaptive_timing`,
`validated_k4_adaptive_midpoint`, and `midpoint_not_improved` in the original
Round 45 report are provisional and are not accepted as final.

The original counterfactual dataset contained only eight initial K4 leaves from
two instances. Its strong-control L3 “beneficial split” label was inferred from
a Round 44 overlay trajectory whose full-instance `split_count` was zero. That
label is withdrawn and must not be treated as a verified split counterfactual.

Although the frozen complex panel contains twelve V20/V50 instances, the prior
runtime screen covered only four instances, two arms, and approximately 300
seconds. It was not the required 48-row, 3600-second common-horizon matrix.
PMM/FPMM were tested on only two startup-scale instances, not on every live
development split leaf.

All old raw files remain immutable historical evidence. Evidence below
`completion/` is non-destructive and supersedes only the old derived
classifications. Until every completion gate passes, PR #95 remains draft, C6
remains the broad validated mainline, all Round 45 behavior remains default-off,
and the adaptive preset is experimental rather than promoted.
"""
    write_text(COMPLETION / "round45_completion_erratum.md", erratum)
    write_json(COMPLETION / "prior_classification_disposition.json", {
        "schema": "round45-prior-classification-disposition-v1",
        "round45_completion_status": "incomplete",
        "prior_timing_classification": "provisional_not_final",
        "prior_point_classification": "provisional_not_final",
        "prior_algorithm_classification": "provisional_not_final",
        "prior_scale_classification": "invalid_for_incomplete_complex_matrix",
        "strong_control_L3_beneficial_label": "withdrawn_invalid_no_live_split",
        "old_raw_evidence_immutable": True,
        "c6_broad_mainline_preserved": True,
        "round45_default_off": True,
        "pr95_must_remain_draft": True,
    })
    contract = f"""# Round 45 completion contract

- Branch: `{git('branch', '--show-current')}`
- Starting local commit: `{git('rev-parse', 'HEAD')}`
- Starting tree: `{git('rev-parse', 'HEAD^{tree}')}`
- Machine: `{platform.node()}`
- Frozen rows: {len(rows)} total; 48 mandatory complex; 6 D_R43 complex diagnostics.

All official Gurobi rows run sequentially with Presolve Auto, Seed 0, Threads 1,
MIPGap 0, MIPGapAbs 0, certificate tolerance 1e-7, no known/archive optimum
injection, and a 3600-second total-process cap. Unsolved rows must reach the cap
within finalization tolerance and preserve 300/1200/3600 reconstructible traces.

The K4 candidate is frozen at gamma-veto/rho_gamma=0.012/frontier-d2/all
parent-scope facets/midpoint/no MIP starts. D_R43 is frozen at rho_D=0.10.
Thresholds will not be retuned from validation or the consumed holdout.

The finalizer must derive every classification from completed evidence. Missing
rows force `round45_completion_incomplete`; no-adaptive is never promotion
eligible; C6 remains the broad validated mainline until all gates pass.
"""
    write_text(COMPLETION / "completion_contract.md", contract)
    write_csv(COMPLETION / "required_run_matrix.csv", rows)

    frozen_files = [
        COMPLETION / "round45_completion_erratum.md",
        COMPLETION / "prior_classification_disposition.json",
        COMPLETION / "completion_contract.md",
        COMPLETION / "required_run_matrix.csv",
    ]
    write_json(COMPLETION / "completion_freeze_manifest.json", {
        "schema": "round45-completion-freeze-manifest-v1",
        "frozen_before_completion_candidate_results": True,
        "starting_local_commit": git("rev-parse", "HEAD"),
        "starting_local_tree": git("rev-parse", "HEAD^{tree}"),
        "matrix_rows": len(rows),
        "mandatory_complex_rows": len(mandatory_complex),
        "complex_d_r43_rows": len([r for r in rows if r["arm"] == "d-r43" and
                                    r["stage"].startswith("complex_secondary_")]),
        "counterfactual_rows": len([r for r in rows if "counterfactual" in r["stage"]]),
        "files": [{"path": path.relative_to(ROOT).as_posix(),
                   "sha256": sha256(path), "size_bytes": path.stat().st_size}
                  for path in frozen_files],
    })
    print(json.dumps({
        "rows": len(rows), "mandatory_complex": len(mandatory_complex),
        "counterfactual": len([r for r in rows if "counterfactual" in r["stage"]]),
        "freeze_sha256": sha256(COMPLETION / "completion_freeze_manifest.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
