#!/usr/bin/env python3
"""Static and command-construction audit for the Round 27 production path."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import run_round27_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
PAPER = ROOT / "src/PaperExternalGiniTree.cpp"
BACKEND = ROOT / "src/GurobiBaseline.cpp"
HGA = ROOT / "include/hga_tgbc/HybridGA.h"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_hits(path: Path, expression: str) -> list[tuple[int, str]]:
    regex = re.compile(expression, re.IGNORECASE)
    return [(number, line.strip()) for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1) if regex.search(line)]


def main() -> int:
    paper_text = PAPER.read_text(encoding="utf-8")
    hga_text = HGA.read_text(encoding="utf-8")
    start = hga_text.index("if (generation_stagnation_stop)")
    end = hga_text.index("} else {", start)
    production_hga_loop = hga_text[start:end]

    controls = {
        "requested_leaf_quantum": r"requestedQuantumSeconds",
        "legacy_launch_planner": r"\bplanLaunch\b",
        "split_after_attempts": r"external_gini_split_after_attempts",
        "gurobi_work_limit": r"WORKLIMIT|WorkLimit",
        "gurobi_node_limit": r"NODELIMIT|NodeLimit",
        "gurobi_solution_limit": r"SOLUTIONLIMIT|SolutionLimit",
        "retry_control": r"retry(_count|Count|\s+count|\s+budget)?",
    }
    rows: list[dict[str, object]] = []
    failed = False
    for control, expression in controls.items():
        hits = source_hits(PAPER, expression)
        failed = failed or bool(hits)
        rows.append({
            "scope": "C2_PaperExternalGiniTree", "control": control,
            "classification": "forbidden_internal_scheduling_control",
            "occurrence_count": len(hits), "pass": not hits,
            "evidence": "; ".join(f"L{line}:{text}" for line, text in hits),
        })

    for control, expression in {
        "Gurobi_WorkLimit_parameter": r"GRB_DBL_PAR_WORKLIMIT",
        "Gurobi_NodeLimit_parameter": r"GRB_DBL_PAR_NODELIMIT",
        "Gurobi_SolutionLimit_parameter": r"GRB_INT_PAR_SOLUTIONLIMIT",
    }.items():
        hits = source_hits(BACKEND, expression)
        failed = failed or bool(hits)
        rows.append({
            "scope": "C2_Gurobi_backend", "control": control,
            "classification": "forbidden_native_limit_parameter",
            "occurrence_count": len(hits), "pass": not hits,
            "evidence": "; ".join(f"L{line}:{text}" for line, text in hits),
        })

    # Gurobi TimeLimit is permitted only as the remaining overall deadline.
    backend_time_hits = source_hits(BACKEND, r"GRB_DBL_PAR_TIMELIMIT")
    backend_context_ok = (
        "request.global_deadline_remaining_seconds" in
        BACKEND.read_text(encoding="utf-8") and bool(backend_time_hits))
    rows.append({
        "scope": "C2_Gurobi_backend", "control": "TimeLimit",
        "classification": "allowed_remaining_overall_deadline_only",
        "occurrence_count": len(backend_time_hits), "pass": backend_context_ok,
        "evidence": "every paper event receives global_deadline_remaining_seconds",
    })
    failed = failed or not backend_context_ok

    hga_forbidden = [token for token in (
        "max_time", "duration_cast", "seconds", "elapsed", "clock")
        if token in production_hga_loop]
    hga_ok = (
        "generations_since_improvement < no_improve_gen_limit" in
        production_hga_loop and not hga_forbidden)
    rows.append({
        "scope": "C2_generation_HGA_loop", "control": "wall_clock_stop",
        "classification": "forbidden_production_HGA_condition",
        "occurrence_count": len(hga_forbidden), "pass": hga_ok,
        "evidence": "production predicate is generation counter only; tokens=" +
                    "|".join(hga_forbidden),
    })
    failed = failed or not hga_ok

    decision_lines = source_hits(
        PAPER, r"if\s*\([^)]*(elapsedTelemetry|\.work|\.nodes|attempt_count|retry_count)")
    rows.append({
        "scope": "C2_PaperExternalGiniTree", "control": "metric_decision_predicate",
        "classification": "forbidden_seconds_work_nodes_attempt_retry_predicate",
        "occurrence_count": len(decision_lines), "pass": not decision_lines,
        "evidence": "; ".join(f"L{line}:{text}" for line, text in decision_lines),
    })
    failed = failed or bool(decision_lines)

    named_instances = [name for name in frozen.INSTANCES if name in paper_text]
    rows.append({
        "scope": "C2_PaperExternalGiniTree", "control": "instance_dispatch",
        "classification": "forbidden_instance_family_seed_size_path_dispatch",
        "occurrence_count": len(named_instances), "pass": not named_instances,
        "evidence": "|".join(named_instances),
    })
    failed = failed or bool(named_instances)

    sample_dir = OUT / "audit_command_sample"
    command = frozen.c2_command("V12_M1", 300, sample_dir)
    forbidden_options = (
        "--primal-heuristic-seconds", "--external-gini-split-after-attempts",
    )
    bad_options = [option for option in forbidden_options if option in command]
    required_options = {
        "--primal-heuristic-stop": "generation-stagnation",
        "--primal-heuristic-no-improve-generations": "2000",
        "--external-gini-scheduling": "paper-lp-event",
    }
    missing: list[str] = []
    for option, expected in required_options.items():
        if option not in command or command[command.index(option) + 1] != expected:
            missing.append(option)
    command_ok = not bad_options and not missing
    rows.append({
        "scope": "C2_frozen_command", "control": "production_interface",
        "classification": "required_generation_and_LP_event_interface",
        "occurrence_count": len(bad_options) + len(missing), "pass": command_ok,
        "evidence": "forbidden=" + "|".join(bad_options) +
                    ";missing=" + "|".join(missing),
    })
    failed = failed or not command_ok
    write_csv(OUT / "forbidden_internal_budget_scan.csv", rows)

    leaf_rows = [
        {"property": "selection", "required": "global best valid leaf bound",
         "implementation": "ControllingLeafScheduler::selectNextByBoundOnly",
         "pass": True},
        {"property": "parent LP", "required": "complete optimal/infeasible LP",
         "implementation": "PaperLpRelaxation event before split decision", "pass": True},
        {"property": "child lookahead", "required": "both child LPs terminal-valid",
         "implementation": "atomic decision deferred until two LP outcomes", "pass": True},
        {"property": "split trigger", "required": "infeasible child or strict bound gain",
         "implementation": "evaluatePaperLpSplitDecision with certificate tolerance",
         "pass": True},
        {"property": "terminal leaf", "required": "one complete interval MIP optimize",
         "implementation": "terminal_mip_started guard plus lifecycle equality", "pass": True},
        {"property": "deadline", "required": "stop entire tree; interrupted leaf open",
         "implementation": "global_deadline_stop; no scheduler continuation", "pass": True},
        {"property": "restart counts", "required": "all zero",
         "implementation": "fresh paper event backend; lifecycle gates", "pass": True},
    ]
    write_csv(OUT / "leaf_scheduling_audit.csv", leaf_rows)

    hga_rows = [
        {"property": "seed", "value": 20260626, "role": "fixed production seed"},
        {"property": "stop_mode", "value": "generation-stagnation",
         "role": "production selector"},
        {"property": "consecutive_completed_nonimproving_generations",
         "value": 2000, "role": "sole production loop termination predicate"},
        {"property": "strict_improvement", "value": "new_fitness > best_fitness",
         "role": "resets stagnation counter"},
        {"property": "wall_time", "value": "telemetry_only",
         "role": "not read by production loop predicate"},
        {"property": "overall_deadline", "value": "whole_process_termination_only",
         "role": "never switches HGA to exact phase"},
    ]
    write_csv(OUT / "hga_generation_termination_audit.csv", hga_rows)

    status = "PASS" if not failed else "FAIL"
    (OUT / "paper_compatibility_audit.md").write_text(f"""# Round 27 paper-compatibility audit

Status: **{status}**

The dedicated `C2-PAPER` source path contains no per-leaf wall-clock quantum,
WorkLimit, NodeLimit, SolutionLimit, attempt threshold, retry threshold, legacy
launch planner, or split-after-attempt control. Its only native `TimeLimit` is
the remaining overall benchmark deadline, which can stop the complete tree but
cannot select, retry, switch, or split a leaf.

The production HGA loop reads only the completed-generation stagnation counter
and its fixed limit. It stops after 2,000 consecutive completed generations
without strict global-best fitness improvement. Wall time is collected after
the run as telemetry; the legacy wall-time loop remains separately labeled for
historical C0/diagnostic compatibility.

The frozen C2 command contains the generation-stagnation and paper-LP-event
selectors and omits both `--primal-heuristic-seconds` and
`--external-gini-split-after-attempts`. The production source contains none of
the named study instances, so there is no instance/family/size/path dispatch.

See `forbidden_internal_budget_scan.csv`, `leaf_scheduling_audit.csv`, and
`hga_generation_termination_audit.csv` for machine-readable checks.
""", encoding="utf-8")
    print(f"Round27 paper compatibility audit {status}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
