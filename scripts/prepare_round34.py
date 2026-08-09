#!/usr/bin/env python3
"""Prepare Round 34 identities, predeclared sets, and source audit evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import round34_common as common


STARTING_HEAD = "201798c6c9daa9b1f6bfae583af5bbdc53608219"
OBSERVED_LIVE_MAIN = "afb3f1043fab73ae28dd5b1a2d71501f6f732b3c"
BRANCH = "codex/round34-c6-algorithm-documentation-hga-ablation"
R33 = common.ROOT / "results/gf_v10_convergence_round33"
R32 = common.ROOT / "results/gf_c6_long_run_validation_round32"

CASE_IDS = (
    "V12_M2",
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
    "round33_v10_high_imbalance_M3_Q30_seed1765289896",
)
DEVELOPMENT_IDS = (
    "round33_v10_high_imbalance_M1_Q20_seed2098545008",
    "round33_v10_moderate_M1_Q30_seed82526096",
    "round33_v10_tight_T_M1_Q20_seed1215342007",
    "round33_v10_moderate_M2_Q20_seed1118884127",
    "round33_v10_tight_T_M2_Q30_seed1783646009",
    "round33_v10_high_imbalance_M3_Q30_seed1765289896",
    "round33_v10_tight_T_M3_Q20_seed284843780",
)
TRANSFER_IDS = (
    "V12_M1",
    "V12_M2",
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
    "tight_T_seed4101",
)
REPEAT_IDS = (
    "round33_v10_high_imbalance_M1_Q20_seed2098545008",
    "round33_v10_moderate_M2_Q20_seed1118884127",
    "round33_v10_high_imbalance_M3_Q30_seed1765289896",
    "V12_M2",
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def normalized_scenario(value: str, instance_id: str) -> str:
    value = value.strip()
    if value:
        return value
    for candidate in ("high_imbalance", "moderate", "tight_T"):
        if candidate in instance_id:
            return candidate
    return "anchor"


def load_inventory() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in read_csv(R33 / "round33_v10_instance_manifest.csv"):
        output.append({
            "instance_id": row["instance_id"],
            "path": row["path"],
            "sha256": row["sha256"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "scenario": row["scenario"],
            "family": row.get("family", row["scenario"]),
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
            "origin": "round33_frozen_v10_identity",
        })
    existing = {
        row["instance_id"]: row
        for row in read_csv(R32 / "round32_existing_instance_manifest.csv")
    }
    multi = {
        row["instance_id"]: row
        for row in read_csv(R32 / "round32_multi_m_manifest.csv")
    }
    for name in ("V12_M1", "V12_M2", "tight_T_seed4101"):
        row = existing[name]
        output.append({
            "instance_id": name,
            "path": row["path"],
            "sha256": row["instance_sha256"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "scenario": normalized_scenario(row.get("family", ""), name),
            "family": row.get("family", "v12_anchor") or "v12_anchor",
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
            "origin": "round32_frozen_existing_identity",
        })
    name = "round32_multi_m_high_imbalance_V20_M2_seed1052706459"
    row = multi[name]
    output.append({
        "instance_id": name,
        "path": row["path"],
        "sha256": row["sha256"],
        "V": int(row["V"]),
        "M": int(row["M"]),
        "Q": int(row["Q"]),
        "scenario": "high_imbalance",
        "family": "high_imbalance",
        "T": float(row["T"]),
        "lambda": float(row["lambda"]),
        "origin": "round32_frozen_multi_m_identity",
    })
    for item in output:
        path = common.ROOT / item["path"]
        if not path.is_file() or common.sha256(path) != item["sha256"]:
            raise RuntimeError(
                f"authoritative instance identity mismatch: {item['instance_id']}")
    return output


def select_rows(items: dict[str, dict[str, Any]], names: tuple[str, ...],
                purpose: str) -> list[dict[str, Any]]:
    output = []
    for order, name in enumerate(names, start=1):
        item = items[name]
        output.append({
            "round_id": 34,
            "selection_order": order,
            "purpose": purpose,
            "instance_id": name,
            "path": item["path"],
            "instance_sha256": item["sha256"],
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "scenario": item["scenario"],
            "T": item["T"],
            "lambda": item["lambda"],
            "predeclared_before_round34_solver_results": True,
        })
    return output


def preexisting_worktree() -> list[dict[str, Any]]:
    intended_prefixes = (
        "build_round34/",
        "results/gf_c6_documentation_hga_round34/",
    )
    intended_files = {
        "include/Instance.hpp",
        "include/Result.hpp",
        "include/hga_tgbc/HybridGA.h",
        "src/HgaTgbcRunner.cpp",
        "src/PaperExternalGiniTree.cpp",
        "src/Result.cpp",
        "src/main.cpp",
        "scripts/round34_common.py",
        "scripts/prepare_round34.py",
        "scripts/run_round34_build_and_tests.py",
        "scripts/run_round34_preflight.py",
        "scripts/run_round34_development.py",
        "scripts/freeze_round34.py",
        "scripts/run_round34_experiments.py",
        "scripts/analyze_round34.py",
        "scripts/package_round34_evidence.py",
        "tests/round34_protocol_tests.py",
    }
    status = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-uall"),
        cwd=common.ROOT, text=True, encoding="utf-8", errors="replace")
    output = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        state, path_text = line[:2], line[3:].replace("\\", "/")
        if path_text in intended_files or path_text.startswith(intended_prefixes):
            continue
        path = common.ROOT / path_text
        output.append({
            "status": state,
            "path": path_text,
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.is_file() else "",
            "preserve_untouched": True,
        })
    return output


def function_body(source: str, name: str) -> str:
    start = source.index(name)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise RuntimeError(f"unclosed function: {name}")


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def frozen_equivalence() -> list[dict[str, Any]]:
    current_paper = (common.ROOT / "src/PaperExternalGiniTree.cpp").read_text(
        encoding="utf-8")
    starting_paper = subprocess.check_output(
        ("git", "show", f"{STARTING_HEAD}:src/PaperExternalGiniTree.cpp"),
        cwd=common.ROOT, text=True, encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for name in (
        "evaluateC6FrontierDecision",
        "evaluateC6CurrentSplitDecision",
        "evaluatePaperTerminalMipDecision",
    ):
        before = digest_text(function_body(starting_paper, name))
        after = digest_text(function_body(current_paper, name))
        rows.append({
            "component": name,
            "scope": "mathematical_decision_function",
            "starting_sha256": before,
            "round34_sha256": after,
            "identical": before == after,
            "evidence": "function_body_sha256",
        })
    for path_text in (
        "src/ControllingLeafScheduler.cpp",
        "include/ControllingLeafScheduler.hpp",
        "src/IntervalRowFactory.cpp",
        "include/IntervalRowFactory.hpp",
        "src/GurobiBaseline.cpp",
        "src/CplexBaseline.cpp",
    ):
        current = common.sha256(common.ROOT / path_text)
        before_text = subprocess.check_output(
            ("git", "show", f"{STARTING_HEAD}:{path_text}"),
            cwd=common.ROOT)
        before = hashlib.sha256(before_text).hexdigest()
        rows.append({
            "component": path_text,
            "scope": "frozen_exact_source_file",
            "starting_sha256": before,
            "round34_sha256": current,
            "identical": before == current,
            "evidence": "whole_file_sha256",
        })
    return rows


def historical_hga_rows() -> list[dict[str, Any]]:
    manifest = read_csv(R33 / "round33_v10_instance_manifest.csv")
    output: list[dict[str, Any]] = []
    for item in manifest:
        run_id = f"stage1__{item['instance_id']}__c6_frozen__3600s"
        path = R33 / "runs" / run_id / "hga_generations.csv"
        rows = read_csv(path)
        improvements = [
            int(row["generation"]) for row in rows
            if row["strict_improvement"].lower() == "true"
        ]
        fitness = [float(row["best_fitness"]) for row in rows]
        last = improvements[-1]
        full_last = int(rows[-1]["generation"])
        full_fitness = fitness[-1]
        record: dict[str, Any] = {
            "round_id": 34,
            "evidence_origin": "historical_round33_frozen_hga_log",
            "instance_id": item["instance_id"],
            "V": int(item["V"]),
            "M": int(item["M"]),
            "Q": int(item["Q"]),
            "scenario": item["scenario"],
            "first_improvement_generation": improvements[0],
            "last_improvement_generation": last,
            "full_stop_generation": full_last,
            "post_last_improvement_generations": full_last - last,
            "full_final_fitness": full_fitness,
            "strict_improvement_count": len(improvements),
        }
        for limit in (250, 500, 1000):
            last_seen_improvement = 0
            stop = full_last
            for row in rows:
                generation = int(row["generation"])
                if row["strict_improvement"].lower() == "true":
                    last_seen_improvement = generation
                if generation - last_seen_improvement >= limit:
                    stop = generation
                    break
            retained = fitness[stop]
            record[f"candidate_{limit}_stop_generation"] = stop
            record[f"candidate_{limit}_fitness"] = retained
            record[f"candidate_{limit}_matches_full"] = (
                abs(retained - full_fitness) <= 1e-12)
        output.append(record)
    return output


def main() -> int:
    common.OUT.mkdir(parents=True, exist_ok=True)
    if common.RUNS.exists() or common.DEVELOPMENT_RUNS.exists():
        raise RuntimeError("Round 34 solver-result directories already exist")
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=common.ROOT,
        text=True).strip()
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT, text=True).strip()
    if branch != BRANCH or head != STARTING_HEAD:
        raise RuntimeError(f"unexpected starting identity: {branch} {head}")
    items = load_inventory()
    keyed = {item["instance_id"]: item for item in items}
    if len(items) != 22 or len(keyed) != 22:
        raise RuntimeError(f"Round 34 requires 22 unique identities, got {len(keyed)}")
    common.write_csv(common.INSTANCE_MANIFEST, items)
    common.write_csv(common.CASE_MANIFEST,
                     select_rows(keyed, CASE_IDS, "complete_convergence"))
    common.write_csv(common.DEVELOPMENT_MANIFEST,
                     select_rows(keyed, DEVELOPMENT_IDS, "startup_development"))
    common.write_csv(common.TRANSFER_MANIFEST,
                     select_rows(keyed, TRANSFER_IDS, "startup_transfer"))
    common.write_csv(common.REPEAT_MANIFEST,
                     select_rows(keyed, REPEAT_IDS, "repeatability"))
    common.write_csv(common.OUT / "preexisting_worktree_manifest.csv",
                     preexisting_worktree())
    equivalence = frozen_equivalence()
    common.write_csv(common.OUT / "frozen_c6_equivalence.csv", equivalence)
    if not all(row["identical"] for row in equivalence):
        raise RuntimeError("frozen C6 decision/source identity changed")
    historical = historical_hga_rows()
    common.write_csv(
        common.OUT / "hga_generation_improvement_summary.csv", historical)
    candidates = {
        limit: sum(bool(row[f"candidate_{limit}_matches_full"])
                   for row in historical)
        for limit in (250, 500, 1000)
    }
    protocol = f"""# Round 34 frozen protocol before new solver results

Round 34 documents and observes the validated C6 exact framework. It does not
create C7 or change C6 mathematical decisions. The default `C6-HGA-FULL` arm
retains seed 20260626, generation-stagnation stopping, and 2000 generations
without strict improvement. `C6-HGA-LIGHT` changes only that final count to
1000. `C6-SIMPLE-START` uses the already implemented three-mode deterministic
greedy constructor and the same independent original-problem verifier.

All post-incumbent C6 options are identical: four initial intervals; binary
midpoint splitting; depth 8; width 1e-4; rho 0.01; full static inherited row
pack; presolve off; traditional search; no native MIP start; one thread; the
Round 31 nonblocking native-bound scheduler and lifecycle; and certificate
tolerance 1e-7. Startup time, verification, construction, exact search, and
finalization all count from process entry.

The complete-convergence cases were selected from historical evidence only:
V12_M2, the Round 32 V20/M2 high-imbalance anchor, and the Round 33 V10/M3/Q30
high-imbalance reference. No Round 34 trial selected a case. P-GRB and
C6-HGA-FULL receive a 7200-second process-entry cap.

The seven development identities, 18 V10 official identities, four transfer
anchors, and five repeat identities are predeclared in their CSV manifests.
Historical Round 33 HGA logs give full-fitness matches of {candidates[250]}/18,
{candidates[500]}/18, and {candidates[1000]}/18 for the natural candidate
stagnation values 250, 500, and 1000. Therefore 1000 is the predeclared primary
LIGHT candidate. Development is a viability/replication gate, not a parameter
sweep. At most this one reduced setting is retained.

Official startup rows use a 3600-second cap. Runs are serial, paired on the
same machine, Gurobi 13.0.2, Seed 0 for exact Gurobi, automatic plain-Gurobi
presolve, zero exact gaps, and one effective thread. Partial native MIP bounds
may strengthen open leaves but never close them. A deadline preserves open
coverage and yields a time-limited, non-certified result.

Fresh canonical fingerprints are generated for all 22 identities before the
official matrix. The executable, source hashes, protocol, commands, instances,
fingerprints, chosen variants, and matrices are frozen before official solver
results. Raw Round 32/33 rows remain read-only historical evidence and are not
mixed into Round 34 official tables.
"""
    common.write_text(common.OUT / "round34_protocol.md", protocol)
    common.write_json(common.OUT / "round34_preparation_summary.json", {
        "schema": "round34-preparation-v1",
        "round_id": 34,
        "branch": branch,
        "starting_head": head,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "instance_count": len(items),
        "case_count": len(CASE_IDS),
        "development_count": len(DEVELOPMENT_IDS),
        "transfer_count": len(TRANSFER_IDS),
        "repeat_count": len(REPEAT_IDS),
        "historical_hga_candidate_full_matches": candidates,
        "selected_primary_light_candidate": 1000,
        "frozen_c6_equivalence_rows": len(equivalence),
        "prepared_at_unix_seconds": time.time(),
        "new_solver_results_started": False,
    })
    print(json.dumps({
        "instances": len(items),
        "cases": len(CASE_IDS),
        "development": len(DEVELOPMENT_IDS),
        "historical_candidate_matches": candidates,
        "preexisting_entries": len(preexisting_worktree()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
