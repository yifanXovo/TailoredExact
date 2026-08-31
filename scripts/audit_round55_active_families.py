#!/usr/bin/env python3
"""Quantify the 17 active F0-CLEAN families and isolated optional removals."""

from __future__ import annotations

import csv
import argparse
import json
import math
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/gf_k1_am_sf_station_state_chain_round55"
RAW = EVIDENCE / "local_raw/formulation_root_lp_census/F0-CLEAN"
REMOVAL_RAW = EVIDENCE / "local_raw/family_removal_diagnostics"
GUROBI_CL = Path("D:/gurobi1302/win64/bin/gurobi_cl.exe")
REMOVABLE = (
    "objective_lower_estimator",
    "penalty_lower_bound_closure",
    "sp_product_objective_estimator",
    "pair_support_duration_cover",
    "triple_support_duration_cover",
)
CATEGORY = {
    "gini_interval_bounds": "domain",
    "direct_gini_cap_floor": "required_interval_scope",
    "interval_tight_g_times_binary_mccormick_hull": "required_extended_formulation",
    "final_inventory_penalty_domains": "domain",
    "movement_reachability_domains": "domain",
    "inventory_conservation": "core_feasibility",
    "visit_inventory_linking": "core_feasibility",
    "verified_incumbent_objective_row": "required_certificate_scope",
    "objective_lower_estimator": "optional_strengthening",
    "penalty_lower_bound_closure": "optional_strengthening_and_closure",
    "sp_product_mccormick_rows": "required_extended_formulation",
    "sp_product_objective_estimator": "optional_strengthening",
    "pair_support_duration_cover": "optional_strengthening",
    "triple_support_duration_cover": "optional_strengthening",
    "connectivity_flow_formulation": "required_extended_formulation",
    "iterative_domain_propagation": "domain",
    "tight_denominator_bounds": "domain",
}


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def constraint_lines(path: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*(c\d+):", line)
        if match:
            found[match.group(1)] = line
    return found


def family_rows(model: Path) -> dict[str, list[str]]:
    lines = constraint_lines(model)
    numbered = sorted(((int(name[1:]), name, line) for name, line in lines.items()))
    wsp = [(number, name, line) for number, name, line in numbered if "W_SP" in line]
    if len(wsp) != 5:
        raise RuntimeError(f"expected five W_SP rows in {model}, got {len(wsp)}")
    first = wsp[0][0]
    pair = []
    triple = []
    for _, name, line in numbered:
        if "120 p_" not in line:
            continue
        count = len(re.findall(r"\bp_\d+_\d+\b", line))
        if count == 2:
            pair.append(name)
        elif count == 3:
            triple.append(name)
    return {
        "objective_lower_estimator": [f"c{first - 2}"],
        "penalty_lower_bound_closure": [f"c{first - 1}"],
        "sp_product_mccormick_rows": [name for _, name, _ in wsp[:4]],
        "sp_product_objective_estimator": [wsp[4][1]],
        "pair_support_duration_cover": pair,
        "triple_support_duration_cover": triple,
    }


def continuous_without_rows(source: Path, target: Path, removed: set[str]) -> None:
    output = []
    skip_integer_section = False
    for line in source.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = re.match(r"(c\d+):", stripped)
        if match and match.group(1) in removed:
            continue
        if stripped in {"Generals", "Binaries"}:
            skip_integer_section = True
            continue
        if stripped == "End":
            skip_integer_section = False
            output.append("End")
            break
        if skip_integer_section:
            continue
        output.append(line)
    target.write_text("\n".join(output) + "\n", encoding="utf-8")


def solve_removed(state: str, family: str, row_names: list[str]) -> dict:
    artifact = REMOVAL_RAW / state / family
    artifact.mkdir(parents=True, exist_ok=True)
    result_path = artifact / "result.json"
    if result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    source = RAW / state / "canonical_model.lp"
    with tempfile.TemporaryDirectory(prefix="round55_family_", dir=artifact) as temp:
        model = Path(temp) / "relaxed.lp"
        continuous_without_rows(source, model, set(row_names))
        log_path = artifact / "gurobi.log"
        command = [
            str(GUROBI_CL), "Threads=1", "Presolve=-1", "Method=1",
            f"LogFile={log_path}", str(model),
        ]
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True,
            timeout=300, check=False,
        )
    (artifact / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (artifact / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    objective_matches = re.findall(
        r"Optimal objective\s+([-+0-9.eE]+)", completed.stdout)
    solved = re.findall(
        r"Solved in\s+([0-9]+) iterations and\s+([0-9.]+) seconds\s+\(([0-9.]+) work units\)",
        completed.stdout,
    )
    if completed.returncode != 0 or not objective_matches or not solved:
        raise RuntimeError(f"removal LP failed {state}/{family}: {completed.stdout[-1000:]}")
    iterations, seconds, work = solved[-1]
    result = {
        "schema": "round55-family-removal-lp-v1",
        "state_id": state, "family": family,
        "rows_removed": len(row_names),
        "objective": float(objective_matches[-1]),
        "simplex_iterations": int(iterations),
        "solver_time_seconds": float(seconds),
        "work": float(work),
        "return_code": completed.returncode,
        "integrality_relaxed_by_lp_rewrite": True,
    }
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def geometric_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(1e-12, value)) for value in values) / len(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    root_census = csv_rows(EVIDENCE / "formulation_root_lp_census.csv")
    states = [row["state_id"] for row in root_census if row["arm"] == "F0-CLEAN"]
    mappings = {state: family_rows(RAW / state / "canonical_model.lp") for state in states}
    evidence_by_state = {}
    for state in states:
        evidence_by_state[state] = {
            row["row_name"]: row
            for row in csv_rows(RAW / state / "lp_constraint_evidence.csv")
        }

    tasks = [(state, "baseline", []) for state in states]
    tasks += [
        (state, family, mappings[state][family])
        for state in states for family in REMOVABLE
    ]
    removal_results = []
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {
            pool.submit(solve_removed, state, family, names): (state, family)
            for state, family, names in tasks
        }
        for ordinal, future in enumerate(as_completed(futures), start=1):
            state, family = futures[future]
            removal_results.append(future.result())
            print(f"[{ordinal}/{len(tasks)}] {state}/{family}", flush=True)
    removal_by_key = {(row["state_id"], row["family"]): row for row in removal_results}

    detailed = []
    for state in states:
        base = removal_by_key[(state, "baseline")]
        official = next(
            row for row in root_census
            if row["state_id"] == state and row["arm"] == "F0-CLEAN")
        for family in REMOVABLE:
            result = removal_by_key[(state, family)]
            detailed.append({
                "state_id": state, "family": family,
                "rows_removed": result["rows_removed"],
                "official_root_objective": official["root_bound"],
                "cli_baseline_objective": base["objective"],
                "removed_objective": result["objective"],
                "objective_loss_from_removal": base["objective"] - result["objective"],
                "strict_root_contribution": base["objective"] - result["objective"] > 1e-8,
                "baseline_work": base["work"],
                "removed_work": result["work"],
                "work_ratio_removed_over_baseline": (result["work"] + 1e-12) / (base["work"] + 1e-12),
                "baseline_matches_official": abs(base["objective"] - float(official["root_bound"])) <= 1e-7,
            })
    with (EVIDENCE / "active_family_removal_diagnostics.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(detailed[0]))
        writer.writeheader(); writer.writerows(detailed)

    base_manifest = [
        row for row in csv_rows(
            ROOT / "results/gf_k1_am_sf_inventory_route_round54/active_family_manifest.csv")
        if row["active"] == "True"
    ]
    census_rows = []
    for source in base_manifest:
        family = source["family_name"]
        mapped_rows = [
            (state, name)
            for state in states for name in mappings[state].get(family, [])
        ]
        evidence = [
            evidence_by_state[state][name]
            for state, name in mapped_rows
            if name in evidence_by_state[state]
        ]
        diagnostic = [row for row in detailed if row["family"] == family]
        census_rows.append({
            "family": family,
            "category": CATEGORY[family],
            "state_count": len(states),
            "family_rows_identified": len(mapped_rows) if mapped_rows else "not_stably_mapped",
            "representative_D1_count": source["representative_D1_count"],
            "columns_caused": "1 W_SP" if family == "sp_product_mccormick_rows" else ("0" if family in REMOVABLE else "bundle_or_not_isolated"),
            "nonzeros_identified": "not_serialized_by_family",
            "root_active_rate": (sum(abs(float(row["slack"])) <= 1e-8 for row in evidence) / len(evidence)) if evidence else "not_stably_mapped",
            "dual_nonzero_rate": (sum(abs(float(row["dual_multiplier"])) > 1e-10 for row in evidence) / len(evidence)) if evidence else "not_stably_mapped",
            "maximum_absolute_slack": max((abs(float(row["slack"])) for row in evidence), default="not_stably_mapped"),
            "aggregate_absolute_slack": sum(abs(float(row["slack"])) for row in evidence) if evidence else "not_stably_mapped",
            "strict_root_contribution_states": sum(bool(row["strict_root_contribution"]) for row in diagnostic) if diagnostic else "not_removed",
            "maximum_root_objective_loss_if_removed": max((float(row["objective_loss_from_removal"]) for row in diagnostic), default="not_removed"),
            "removal_work_geometric_mean_ratio": geometric_mean([float(row["work_ratio_removed_over_baseline"]) for row in diagnostic]) if diagnostic else "not_removed",
            "presolve_elimination": "not_exposed_per_family",
            "model_build_cost": "not_exposed_per_family",
            "exactness_after_removal": family in REMOVABLE,
            "sparse_candidate_selected": False,
            "selection_reason": "required/core/domain" if family not in REMOVABLE else "did_not_meet_all pre-pilot sparse entry criteria",
        })
    with (EVIDENCE / "active_family_efficacy_census.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(census_rows[0]))
        writer.writeheader(); writer.writerows(census_rows)
    print(json.dumps({
        "families": len(census_rows),
        "removal_rows": len(detailed),
        "all_cli_baselines_match": all(row["baseline_matches_official"] for row in detailed),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
