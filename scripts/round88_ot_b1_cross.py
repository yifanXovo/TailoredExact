"""D7 parent/left-child cross-point B1 attribution diagnostic.

`prepare` verifies frozen source evidence and writes a de-duplicated exact B1
row bank. `diagnose` alone calls Optimize on six fixed same-source LP arms.
`supervise` applies one external whole-process deadline to that diagnosis.
This is an offline one-round mechanism experiment, not an ENS algorithm.
"""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from gurobipy import GRB

from round88_ot_diagnostic import (add_cut, audit_model, load_model, optimize,
                                    process_peak_memory_bytes, read_instance, sha256,
                                    write_json)
from round88_ot_math import h_name, pair_cut, support_fingerprint

ROOT = Path(__file__).resolve().parents[1]
PREP_DIR = Path("results/unified_exact_round88/ot_b1_cross_preparation")
DIAGNOSTIC_OUT = Path("results/unified_exact_round88/ot_b1_cross_diagnostic_001")
SOURCE = {
    "parent": {
        "manifest": ("results/unified_exact_round88/ot_qualification_d7_audit_v4/manifest.json",
                     "a0996967e9278469defa43ab1c630b0d16f7e996062f71bf91efa9a656f99a4d"),
        "rows": ("results/unified_exact_round88/ot_d7_diagnostic_001/diagnostic/fixed_point_rows.jsonl",
                 "f4f0efb37b97071fea157fc33bf139f0b6d2d2aa229d63ffaa533fb2e191a7b8"),
        "primal": ("results/unified_exact_round88/ot_d7_diagnostic_001/diagnostic/fixed_point_primal.json",
                   "d23b0ef63c7c7aeb259846bc7fda207af24cef0a3bfda5dde71ed7d2af4b6b87"),
        "result": ("results/unified_exact_round88/ot_d7_diagnostic_001/diagnostic/result.json",
                   "c4af54afd0c36e986e546fb1eee555e1b807cefc95d0c0af982b6f5a1a0e2253"),
        "supervision": ("results/unified_exact_round88/ot_d7_diagnostic_001/supervision.json",
                        "824c0425d857518a22bebbadaef50f557c957ae3e4ec0b5b4964c71cae6f8555"),
    },
    "child": {
        "manifest": ("results/unified_exact_round88/ot_qualification_d7_l00_audit/manifest.json",
                     "e73e08318afe65d9c4d145f2dd8efe8732783b11e0628f347434b4093c2f09fd"),
        "rows": ("results/unified_exact_round88/ot_d7_l00_diagnostic_001/diagnostic/fixed_point_rows.jsonl",
                 "cf30d7e75d73edd2ccbcb205b0200e9fb5f4c14ac3c3d8c56aa5a0ce3e21bccc"),
        "primal": ("results/unified_exact_round88/ot_d7_l00_diagnostic_001/diagnostic/fixed_point_primal.json",
                   "09c7610bce13cb7f028042ccfe5c5a635ac704830c1bd778fea03a10ba43af7c"),
        "result": ("results/unified_exact_round88/ot_d7_l00_diagnostic_001/diagnostic/result.json",
                   "f7568e4bab4e42a49ca8efdaa79306f67f0a17cdcbc00b0eea667c8777681603"),
        "supervision": ("results/unified_exact_round88/ot_d7_l00_diagnostic_001/supervision.json",
                        "2b78ccf8483ffa4462b9035ef682a8ad9b6d89cd79811a4e1ffb10211154343b"),
    },
}
FROZEN_DEPENDENCIES = {
    "scripts/round88_ot_math.py": "2b8855609cf469098d050fcd9c89efac01b2cb41ee07f023b5a7b79f9ff71840",
    "scripts/round88_ot_diagnostic.py": "c1cb1776d1b1eef0f03977e00060c1690e5505517d0e4baa71feb3b672fa0756",
}
ARM_ORDER = ("parent+R_parent", "parent+R_child", "parent+union",
             "child+R_parent", "child+R_child", "child+union")


def path_for(relative: str) -> Path:
    return ROOT / relative


def verified_file(relative: str, expected_sha: str) -> Path:
    path = path_for(relative)
    if sha256(path) != expected_sha:
        raise ValueError(f"source SHA256 mismatch: {relative}")
    return path


def verify_model_assets(manifest: dict[str, Any],
                        result: dict[str, Any] | None = None) -> None:
    if (sha256(Path(manifest["lp"])) != manifest["lp_sha256"]
            or sha256(Path(manifest["input"])) != manifest["input_sha256"]
            or result is not None and result.get("lp_sha256") != manifest["lp_sha256"]):
        raise ValueError("source LP/input bytes changed since original audit")


def load_source(label: str) -> dict[str, Any]:
    paths = {key: verified_file(*entry) for key, entry in SOURCE[label].items()}
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    result = json.loads(paths["result"].read_text(encoding="utf-8"))
    supervision = json.loads(paths["supervision"].read_text(encoding="utf-8"))
    primal = json.loads(paths["primal"].read_text(encoding="utf-8"))
    verify_model_assets(manifest, result)
    if (supervision.get("status") != "diagnostic_process_finished"
            or supervision.get("exit_code") != 0
            or not supervision.get("manifest_identity_consistent")
            or supervision.get("manifest_sha256_before") != SOURCE[label]["manifest"][1]
            or supervision.get("manifest_sha256_after") != SOURCE[label]["manifest"][1]
            or supervision.get("diagnostic_result_manifest_sha256") != SOURCE[label]["manifest"][1]
            or result.get("status") != "completed_fixed_point_one_round"
            or not result.get("all_arm_objectives_comparable")
            or result.get("manifest_sha256") != SOURCE[label]["manifest"][1]
            or result["arms"]["base"].get("status_code") != GRB.OPTIMAL):
        raise ValueError(f"{label} source did not complete its fixed-LP qualification")
    return {"paths": paths, "manifest": manifest, "result": result,
            "supervision": supervision, "primal": primal}


def verify_shared_identity(parent: dict[str, Any], child: dict[str, Any]) -> None:
    p, c = parent["manifest"], child["manifest"]
    for field in ("input_sha256", "source_sha256", "binary_sha256", "scenario_id",
                  "verified_ub", "lambda", "T", "pickup_time", "drop_time"):
        if p[field] != c[field]:
            raise ValueError(f"parent/child {field} mismatch")
    for field in ("n", "vehicles", "targets", "capacities", "weights"):
        if p["instance"][field] != c["instance"][field]:
            raise ValueError(f"parent/child instance {field} mismatch")
    if p["structure"]["support"] != c["structure"]["support"]:
        raise ValueError("parent/child inventory support differs")
    if (p["leaf_id"] != "L0" or c["leaf_id"] != "L0.0"
            or c["parent_id"] != "L0"):
        raise ValueError("unexpected parent/left-child tree identity")
    pa, pb = p["structure"]["g_bounds"]
    ca, cb = c["structure"]["g_bounds"]
    if not pa <= ca <= cb <= pb:
        raise ValueError("child G domain is not contained in parent")


def canonical_coefficients(coeff: dict[str, Fraction]) -> dict[str, str]:
    return {name: str(value) for name, value in sorted(coeff.items()) if value}


def row_id(coeff: dict[str, Fraction]) -> str:
    payload = json.dumps(canonical_coefficients(coeff), sort_keys=True,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_selected_b1(record: dict[str, Any], source: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if record.get("kind") != "B1" or not record.get("selected"):
        raise ValueError("cross-point row must be an already selected B1 cut")
    if Fraction(record["solver_row_scale"]) != 1:
        raise ValueError("B1 row was unexpectedly scaled")
    i, j = record["pair"]
    manifest = source["manifest"]
    supports = {int(k): v for k, v in manifest["structure"]["support"].items()}
    targets = {int(k): v for k, v in manifest["instance"]["targets"].items()}
    a = Fraction(manifest["structure"]["effective_gamma_l"])
    b = Fraction(manifest["structure"]["effective_gamma_u"])
    wanted_scope = support_fingerprint({i: supports[i], j: supports[j]}, targets, a, b)
    if record.get("support_fingerprint") != wanted_scope:
        raise ValueError("B1 source support or leaf identity mismatch")
    coeff = {name: Fraction(value) for name, value in record["coefficients_exact"].items()}
    if not coeff or coeff.get(h_name(i, j)) != 1:
        raise ValueError("B1 must contain its pair h with unit coefficient")
    if any(name != h_name(i, j) and not name.startswith((f"state_{i}_", f"state_{j}_"))
           for name in coeff):
        raise ValueError("B1 cross row contains G, perspective, product, or unrelated station")
    expected = pair_cut("B1", i, j, supports, targets, a, b, source["primal"])
    if coeff != expected.coeff or record.get("signs") != [list(s) for s in expected.signs]:
        raise ValueError("B1 coefficients/signs differ from frozen x0 recomputation")
    margin = record.get("selection_margin")
    if (margin is None or not math.isfinite(margin)
            or not record["normalized_violation"] > margin):
        raise ValueError("B1 source was not reliably violated")
    identifier = row_id(coeff)
    return identifier, {"pair": [i, j], "coefficients_exact": canonical_coefficients(coeff)}


def extract_rows(source: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    rows: dict[str, dict[str, Any]] = {}
    count = 0
    for line in source["paths"]["rows"].open(encoding="utf-8"):
        record = json.loads(line)
        if record.get("kind") != "B1" or not record.get("selected"):
            continue
        identifier, row = parse_selected_b1(record, source)
        if identifier in rows and rows[identifier] != row:
            raise ValueError("B1 exact row hash collision")
        rows[identifier] = row
        count += 1
    expected = source["result"]["fixed_point"]["selected_rows"]["B1"]
    if count != expected:
        raise ValueError("B1 raw selected count differs from source result")
    return rows, {"raw_selected": count, "unique_exact": len(rows)}


def validate_row_bank(row_bank: dict[str, Any]) -> None:
    if row_bank.get("contract") != "round88_d7_exact_b1_cross_point_v1":
        raise ValueError("wrong B1 bank contract")
    rows = row_bank["rows"]
    if set(row_bank["sets"]) != {"R_parent", "R_child", "union"}:
        raise ValueError("B1 bank has unexpected row-set names")
    for name, ids in row_bank["sets"].items():
        if len(ids) != len(set(ids)) or any(identifier not in rows for identifier in ids):
            raise ValueError(f"invalid exact row set {name}")
    if (set(row_bank["sets"]["union"]) !=
            set(row_bank["sets"]["R_parent"]) | set(row_bank["sets"]["R_child"])):
        raise ValueError("B1 union is not the exact set union")
    if set(rows) != set(row_bank["sets"]["union"]):
        raise ValueError("B1 bank contains an unselected row")
    for identifier, row in rows.items():
        coeff = {name: Fraction(value) for name, value in row["coefficients_exact"].items()}
        if row_id(coeff) != identifier:
            raise ValueError("B1 row-bank identifier mismatch")


def verify_dependencies() -> None:
    for path, expected in FROZEN_DEPENDENCIES.items():
        verified_file(path, expected)


def verify_bank_against_frozen_sources(row_bank: dict[str, Any]) -> None:
    """Rebuild both selected B1 sets from immutable raw x0 evidence before Optimize."""
    parent, child = load_source("parent"), load_source("child")
    verify_shared_identity(parent, child)
    p_rows, _ = extract_rows(parent)
    c_rows, _ = extract_rows(child)
    expected_rows = dict(p_rows)
    expected_rows.update(c_rows)
    if (row_bank["sets"]["R_parent"] != sorted(p_rows)
            or row_bank["sets"]["R_child"] != sorted(c_rows)
            or row_bank["sets"]["union"] != sorted(expected_rows)
            or row_bank["rows"] != {k: expected_rows[k] for k in sorted(expected_rows)}):
        raise ValueError("prepared B1 bank differs from frozen source-selected rows")


def prepare(output: Path) -> None:
    preparation_started = time.perf_counter()
    verify_dependencies()
    parent, child = load_source("parent"), load_source("child")
    verify_shared_identity(parent, child)
    p_rows, p_count = extract_rows(parent)
    c_rows, c_count = extract_rows(child)
    union = dict(p_rows)
    for identifier, row in c_rows.items():
        if identifier in union and union[identifier] != row:
            raise ValueError("same exact B1 hash has conflicting row content")
        union[identifier] = row
    row_bank = {"contract": "round88_d7_exact_b1_cross_point_v1",
                "rows": {k: union[k] for k in sorted(union)},
                "sets": {"R_parent": sorted(p_rows), "R_child": sorted(c_rows),
                         "union": sorted(union)}}
    validate_row_bank(row_bank)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    write_json(output / "row_bank.json", row_bank)
    preparation_seconds = time.perf_counter() - preparation_started
    write_json(output / "preparation_timing.json", {
        "row_bank_preparation_wall_seconds_through_bank_write": preparation_seconds,
        "includes_source_hashing_exact_row_recomputation_and_union": True,
        "optimize_invocations": 0})
    pp, cp = parent["manifest"], child["manifest"]
    manifest = {
        "contract": "round88_d7_b1_cross_six_arms_v1",
        "status": "prepared_only_no_optimize_authorization",
        "script_sha256": sha256(Path(__file__)),
        "frozen_dependencies_sha256": FROZEN_DEPENDENCIES,
        "source_files": SOURCE,
        "parent_lp": {"path": pp["lp"], "sha256": pp["lp_sha256"],
                      "g_bounds": pp["structure"]["g_bounds"]},
        "child_lp": {"path": cp["lp"], "sha256": cp["lp_sha256"],
                     "g_bounds": cp["structure"]["g_bounds"]},
        "shared_input_sha256": pp["input_sha256"],
        "shared_cutoff": pp["verified_ub"],
        "shared_support": pp["structure"]["support"],
        "shared_targets": pp["instance"]["targets"],
        "row_bank": str(output / "row_bank.json"),
        "row_bank_sha256": sha256(output / "row_bank.json"),
        "preparation_timing": str(output / "preparation_timing.json"),
        "preparation_timing_sha256": sha256(output / "preparation_timing.json"),
        "preparation_wall_seconds_through_bank_write": preparation_seconds,
        "row_counts": {"R_parent": p_count, "R_child": c_count,
                       "union_unique_exact": len(union),
                       "overlap_unique_exact": len(p_rows) + len(c_rows) - len(union)},
        "arm_order": ARM_ORDER,
        "solver_settings": {"Threads": 1, "Seed": 0, "Presolve": -1,
                            "FeasibilityTol": 1e-6, "OptimalityTol": 1e-6,
                            "MIPGap": 0.0},
        "whole_process_limit_seconds": 120,
        "output_directory": str(DIAGNOSTIC_OUT),
        "prior_base_reference_only": {
            "parent": parent["result"]["arms"]["base"]["objective"],
            "child": child["result"]["arms"]["base"]["objective"]},
        "interpretation": "B1 global in G on identical input/support. Within each actual LP compare parent-selected, child-selected and exact-union rows. Parent/child LPs may differ beyond G bounds; cross-LP monotonicity is conditional on separate full formulation nesting evidence. No B2/aggregate transfer."
    }
    write_json(output / "manifest.json", manifest)
    print(output / "manifest.json")


def load_prepared(manifest_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != "round88_d7_b1_cross_six_arms_v1":
        raise ValueError("wrong cross-point manifest contract")
    if manifest["script_sha256"] != sha256(Path(__file__)):
        raise ValueError("cross-point diagnostic script changed")
    verify_dependencies()
    for label in ("parent", "child"):
        for key, (relative, expected) in SOURCE[label].items():
            if manifest["source_files"][label][key] != [relative, expected]:
                raise ValueError("prepared source identity changed")
            verified_file(relative, expected)
    row_path = path_for(manifest["row_bank"])
    if sha256(row_path) != manifest["row_bank_sha256"]:
        raise ValueError("prepared B1 bank changed")
    timing_path = path_for(manifest["preparation_timing"])
    if sha256(timing_path) != manifest["preparation_timing_sha256"]:
        raise ValueError("source B1 preparation cost receipt changed")
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    if (timing["row_bank_preparation_wall_seconds_through_bank_write"] !=
            manifest["preparation_wall_seconds_through_bank_write"]):
        raise ValueError("source B1 preparation cost mismatch")
    row_bank = json.loads(row_path.read_text(encoding="utf-8"))
    validate_row_bank(row_bank)
    return manifest, row_bank


def diagnose(manifest_path: Path, out: Path) -> None:
    process_started = time.perf_counter()
    manifest, bank = load_prepared(manifest_path)
    verify_bank_against_frozen_sources(bank)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    models = {}
    model_costs = {}
    for label in ("parent", "child"):
        old = json.loads(verified_file(*SOURCE[label]["manifest"]).read_text(encoding="utf-8"))
        lp = Path(old["lp"])
        verify_model_assets(old)
        instance = read_instance(Path(old["input"]))
        started = time.perf_counter()
        original = load_model(lp)
        read_seconds = time.perf_counter() - started
        structure = audit_model(original, instance, Fraction(old["gamma_l"]),
                                Fraction(old["gamma_u"]), old["verified_ub"], old["lambda"])
        if structure != old["structure"]:
            raise ValueError("LP domain/support/row identity changed")
        started = time.perf_counter()
        relaxed = original.relax()
        relax_seconds = time.perf_counter() - started
        if any(var.VType != GRB.CONTINUOUS for var in relaxed.getVars()):
            raise ValueError("integrality survived LP relaxation")
        models[label] = relaxed
        model_costs[label] = {"read_seconds": read_seconds,
                              "relax_seconds": relax_seconds,
                              "variables": relaxed.NumVars,
                              "constraints": relaxed.NumConstrs,
                              "nonzeros": relaxed.NumNZs}
    result: dict[str, Any] = {
        "status": "running", "manifest_sha256": sha256(manifest_path),
        "source_lp_sha256": {k: manifest[f"{k}_lp"]["sha256"]
                              for k in ("parent", "child")},
        "row_bank_sha256": manifest["row_bank_sha256"],
        "source_row_sets_reverified_from_frozen_raw": True,
        "source_row_bank_preparation_wall_seconds":
            manifest["preparation_wall_seconds_through_bank_write"],
        "prior_base_reference_only": manifest["prior_base_reference_only"],
        "model_costs": model_costs, "arms": {},
        "shared_preparation_wall_seconds": time.perf_counter() - process_started}
    write_json(out / "result.json", result)
    for arm in ARM_ORDER:
        domain, row_set = arm.split("+", 1)
        started = time.perf_counter()
        model = models[domain].copy()
        copy_seconds = time.perf_counter() - started
        started = time.perf_counter()
        for index, identifier in enumerate(bank["sets"][row_set]):
            row = bank["rows"][identifier]
            coeff = {name: Fraction(value)
                     for name, value in row["coefficients_exact"].items()}
            add_cut(model, coeff, f"cross_B1_{domain}_{row_set}_{index}")
        model.update()
        add_seconds = time.perf_counter() - started
        solved = optimize(model, out / f"{arm}.log")
        solved.update({"new_rows": len(bank["sets"][row_set]),
                       "copy_seconds": copy_seconds,
                       "add_rows_seconds": add_seconds,
                       "marginal_wall_seconds": copy_seconds + add_seconds + solved["wall_seconds"],
                       "shared_plus_arm_component_seconds":
                           result["shared_preparation_wall_seconds"] + copy_seconds
                           + add_seconds + solved["wall_seconds"]})
        result["arms"][arm] = solved
        result["elapsed_wall_seconds_through_arm"] = time.perf_counter() - process_started
        result["process_peak_working_set_bytes_so_far"] = process_peak_memory_bytes()
        write_json(out / "result.json", result)
        if model.Status != GRB.OPTIMAL:
            result["status"] = "partial_unknown_arm_not_optimal"
            write_json(out / "result.json", result)
            break
    else:
        result["status"] = "completed_six_arms_optimal"
        write_json(out / "result.json", result)
    write_json(out / "timing.json", {
        "diagnose_wall_seconds_through_result_write": time.perf_counter() - process_started,
        "whole_process_paid_cost_in_supervision": True})


def supervise(manifest_path: Path, out: Path, limit: float) -> int:
    started = time.perf_counter()
    if limit <= 0:
        raise ValueError("whole-process limit must be positive")
    expected_limit = json.loads(manifest_path.read_text(encoding="utf-8"))[
        "whole_process_limit_seconds"]
    if limit != expected_limit:
        raise ValueError("whole-process limit differs from frozen manifest")
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    before = sha256(manifest_path)
    command = [sys.executable, str(Path(__file__)), "diagnose", "--manifest",
               str(manifest_path.resolve()), "--out-dir", str((out / "diagnostic").resolve())]
    deadline = started + limit
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=max(0.0, deadline - time.perf_counter()))
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    wall = time.perf_counter() - started
    timed_out = timed_out or time.perf_counter() > deadline
    after = sha256(manifest_path) if manifest_path.is_file() else None
    result_path = out / "diagnostic" / "result.json"
    partial_result = False
    result_manifest = None
    result_status = None
    if result_path.is_file():
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result_manifest = result["manifest_sha256"]
            result_status = result["status"]
        except (OSError, ValueError, KeyError):
            partial_result = True
    identity_ok = before == after and (result_manifest is None or result_manifest == before)
    (out / "stdout.txt").write_text(stdout, encoding="utf-8")
    (out / "stderr.txt").write_text(stderr, encoding="utf-8")
    status = ("invalid_manifest_drift" if not identity_ok else
              "unknown_whole_process_deadline" if timed_out else
              "invalid_diagnostic_result" if process.returncode == 0 and
              (not result_path.is_file() or partial_result) else
              "partial_unknown_arm_not_optimal" if process.returncode == 0 and
              result_status != "completed_six_arms_optimal" else
              "diagnostic_process_finished" if process.returncode == 0 else
              "diagnostic_process_failed")
    write_json(out / "supervision.json", {
        "status": status, "wall_seconds": wall, "whole_process_limit_seconds": limit,
        "exit_code": process.returncode, "manifest_sha256_before": before,
        "manifest_sha256_after": after, "diagnostic_result_manifest_sha256": result_manifest,
        "diagnostic_result_status": result_status,
        "manifest_identity_consistent": identity_ok,
        "diagnostic_result_file_invalid": partial_result,
        "command": command})
    print(status, file=sys.stderr if status != "diagnostic_process_finished" else sys.stdout)
    return (125 if not identity_ok else 124 if timed_out else
            126 if status in ("invalid_diagnostic_result", "partial_unknown_arm_not_optimal")
            else process.returncode)


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="verify frozen sources and write exact row bank; no Optimize")
    p.add_argument("--out-dir", type=Path, default=PREP_DIR)
    d = sub.add_parser("diagnose", help="Optimize six same-source cross-point B1 arms")
    d.add_argument("--manifest", type=Path, required=True)
    d.add_argument("--out-dir", type=Path, required=True)
    s = sub.add_parser("supervise", help="one external whole-process deadline")
    s.add_argument("--manifest", type=Path, required=True)
    s.add_argument("--out-dir", type=Path, required=True)
    s.add_argument("--whole-process-limit-seconds", type=float, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    options = cli()
    if options.command == "prepare":
        prepare(options.out_dir)
    elif options.command == "diagnose":
        diagnose(options.manifest, options.out_dir)
    else:
        raise SystemExit(supervise(options.manifest, options.out_dir,
                                   options.whole_process_limit_seconds))
