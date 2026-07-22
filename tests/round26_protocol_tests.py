#!/usr/bin/env python3
"""Static and manifest integrity tests for the frozen Round 26 protocol."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_external_gurobi_production_validation_round26"
sys.path.insert(0, str(ROOT / "scripts"))
import run_round26_experiments as runner  # noqa: E402

checks = 0


def require(value: bool, message: str) -> None:
    global checks
    checks += 1
    if not value:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    development = rows("round26_development_manifest.csv")
    heldout = rows("round26_heldout_v20_manifest.csv")
    v50 = rows("round26_v50_manifest.csv")
    require(len(development) == 5, "five development instances")
    require(len(heldout) == 6, "six held-out V20 instances")
    require(len(v50) == 3, "three held-out V50 instances")
    require({row["family"] for row in heldout} ==
            {"high_imbalance", "moderate", "tight_T"}, "V20 families")
    require({row["family"] for row in v50} ==
            {"high_imbalance", "moderate", "tight_T"}, "V50 families")
    for row in development + heldout + v50:
        path = Path(row["full_path"])
        require(path.is_file(), f"manifest path exists: {row['instance']}")
        require(sha256(path) == row["sha256"], f"manifest hash: {row['instance']}")
        require(row["sealed_before_solver_runs"] == "yes", "sealed marker")

    seal = json.loads((OUT / "heldout_seal.json").read_text(encoding="utf-8"))
    require(seal["created_before_any_round26_solver_run"], "seal chronology")
    require(len(seal["files"]) == 9, "nine sealed new files")
    require(set(item["sha256"] for item in seal["files"]) ==
            set(row["sha256"] for row in heldout + v50), "seal hash set")
    require({row["seed"] for row in heldout} ==
            {"5102", "5103", "5202", "5203", "5301", "5302"},
            "advanced V20 seeds")
    require({row["seed"] for row in v50} == {"6102", "6202", "6301"},
            "advanced V50 seeds")

    pgrb = json.loads((OUT / "p_grb_manifest.json").read_text(encoding="utf-8"))
    c0 = json.loads((OUT / "c0_manifest.json").read_text(encoding="utf-8"))
    c1 = json.loads((OUT / "c1_manifest.json").read_text(encoding="utf-8"))
    require(pgrb["configuration"]["HGA_or_known_UB"] is False,
            "plain Gurobi has no HGA/known UB")
    require(c0["configuration"]["explicit_cross_model_warm_start"] is False,
            "C0 is cold")
    require(c1["selection"].startswith("C1_equals_C0"), "C1 selection")
    require(c1["executable_sha256"] == c0["executable_sha256"], "C1=C0 binary")
    require(c1["configuration"]["external_gini_split_after_attempts"] == 2,
            "C1 keeps C0 threshold")
    require(c1["configuration"]["instance_or_family_dispatch"] is False,
            "C1 no dispatch")
    require(c1["heldout_access_authorized"] is True, "C1 frozen before unseal")

    require(len(runner.OFFICIAL_STAGES["stage1"][1]) == 15, "Stage 1 rows")
    require(len(runner.OFFICIAL_STAGES["stage2"][1]) == 18, "Stage 2 rows")
    require(len(runner.OFFICIAL_STAGES["stage3"][1]) == 6, "Stage 3 rows")
    require(len(runner.OFFICIAL_STAGES["stage4"][1]) == 8, "Stage 4 rows")
    require(sum(len(item[1]) for item in runner.OFFICIAL_STAGES.values()) == 47,
            "47 official rows")
    require(set(runner.LONG_CASES) == {
        "high_imbalance_seed5202", "moderate_seed5301",
        "tight_T_seed5102", "moderate_seed6301"}, "blind long cases")
    require(not set(runner.DEVELOPMENT) & set(runner.HELDOUT_V20 + runner.V50),
            "development/held-out disjoint")
    require(runner.executable_for_arm("C1") == runner.executable_for_arm("C0"),
            "runner binds C1 to C0")
    c0_command = runner.external_command("V12_M1", "C0", 1200, Path("same"))
    c1_command = runner.external_command("V12_M1", "C1", 1200, Path("same"))
    def normalize(command: list[str]) -> list[str]:
        output = list(command)
        index = output.index("--dense-progress-algorithm-arm")
        output[index + 1] = "C0_OR_C1"
        return output
    require(normalize(c0_command) == normalize(c1_command),
            "C0/C1 commands differ only in reporting arm")
    require("--external-gini-split-after-attempts" not in c1_command,
            "rejected P1 flag absent from C1")
    require("--external-gini-warm-start" in c1_command and
            c1_command[c1_command.index("--external-gini-warm-start") + 1] == "false",
            "C1 cold command")

    diagnostic = runner.diagnostic_matrix()
    require(len(diagnostic) == 2, "two Stage 1 regression diagnostics")
    require({item[0] for item in diagnostic} == {"stage1"},
            "Stage 1 diagnostic provenance")
    require({item[1] for item in diagnostic} == {"V12_M1", "V12_M2"},
            "only P-GRB-winning V12 pairs replay")
    require({item[2] for item in diagnostic} == {600},
            "V12 diagnostic budget")
    require(len({item[3]["trigger_id"] for item in diagnostic}) ==
            len(diagnostic), "diagnostic trigger IDs unique")
    for source_stage, instance, budget, trigger in diagnostic:
        require(trigger["replay_arm"] == "C1", "diagnostic is C1-only")
        run_id = (f"diagnostic_{source_stage}_{trigger['official_horizon_seconds']}s"
                  f"__{instance}__c1__{budget}s")
        state = json.loads((OUT / "runs" / run_id / "run_state.json").read_text(
            encoding="utf-8"))
        require(state["completed"] and state["return_code"] == 0,
                f"diagnostic completed: {trigger['trigger_id']}")
        require(state["diagnostic_only"] and not state["official"],
                f"diagnostic excluded from official: {trigger['trigger_id']}")
        require(state["diagnostic_trigger"]["trigger_id"] == trigger["trigger_id"],
                f"diagnostic linkage: {trigger['trigger_id']}")

    source = (ROOT / "src/ExternalGiniTree.cpp").read_text(encoding="utf-8")
    helper = source[source.index("bool externalLeafReadyForAdaptiveSplit"):]
    helper = helper[:helper.index("SolveResult solveExternalGiniTree")]
    require("instance" not in helper.lower(), "split helper has no instance dispatch")
    require("seed" not in helper.lower(), "split helper has no seed dispatch")
    require("path" not in helper.lower(), "split helper has no path dispatch")
    require("completed_attempts >= split_after_attempts" in helper,
            "uniform state rule")
    require("external_gini_split_after_attempts = 2" in
            (ROOT / "include/Instance.hpp").read_text(encoding="utf-8"),
            "C0 default in source")

    protocol = (OUT / "round26_evaluation_protocol.md").read_text(encoding="utf-8")
    require("Exactly 47 official rows" in protocol, "protocol row count")
    require("at least 80%" in protocol, "promotion threshold frozen")
    require("one enhanced C1 replay" in protocol, "diagnostic rule frozen")
    require("C1 is frozen equal to C0" in
            (OUT / "candidate_selection_protocol.md").read_text(encoding="utf-8"),
            "selection documented")
    require("complete root and parent/child coverage" in
            (OUT / "c1_exactness_argument.md").read_text(encoding="utf-8"),
            "exactness scope documented")
    c0_c1 = rows("c0_vs_c1.csv")
    require(len(c0_c1) == 11, "C0/C1 table has only matched official rows")
    require({row["stage"] for row in c0_c1} == {"stage1", "stage2"},
            "C0/C1 table excludes stages without C0")
    require(all(row["decision_reason"] != "missing_matched_row"
                for row in c0_c1), "no unmatched pair classified as tie")
    for name in ("family_summary.csv", "scalability_summary.csv",
                 "promotion_gate_audit.csv", "evidence_package_manifest.csv"):
        require((OUT / name).is_file(), f"final artifact exists: {name}")
    gates = rows("promotion_gate_audit.csv")
    require(len(gates) == 10, "ten frozen promotion gates")
    require({row["gate"] for row in gates if row["passed"] == "False"} ==
            {"3", "9"}, "promotion fails only unresolved V12 and C0 gates")
    final = json.loads((OUT / "final_audit_summary.json").read_text(
        encoding="utf-8"))
    require(final["official"]["completed"] == 47, "47 completed final rows")
    require(final["official"]["failed"] == 0, "zero failed official rows")
    require(final["promotion"] is False, "promotion fails closed")
    require(final["stable_mainline"] == "corrected_CPLEX_S0_F0",
            "CPLEX S0/F0 remains stable")
    package = final["evidence_package"]
    require(package["status"] == "passed", "final evidence package passes")
    require(package["raw_lp_files"] == 0, "no raw LP remains")
    require(package["compression_mismatches"] == 0,
            "compressed evidence round trips")
    require(package["sensitive_marker_hits"] == 0,
            "no sensitive license marker retained")
    require(len(rows("evidence_package_manifest.csv")) ==
            package["files_excluding_manifest"], "manifest covers retained files")
    require("C1 is not promoted" in
            (OUT / "final_report.md").read_text(encoding="utf-8"),
            "final report states no promotion")
    require(checks >= 65, "minimum Round 26 static check count")
    print(f"round26_protocol_tests passed {checks} checks")


if __name__ == "__main__":
    main()
