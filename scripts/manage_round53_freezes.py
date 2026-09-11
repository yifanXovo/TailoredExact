#!/usr/bin/env python3
"""Freeze the Round 53 inner backend and authorize the sealed panel."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
F0 = "interval-mip-core-no-exhaustive-subset-duration"
V0 = "interval-mip-v0"


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        errors="replace").strip()


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def algorithm_scope_dirty() -> list[str]:
    unstaged = git("diff", "--name-only", "--", "CMakeLists.txt", "include",
                   "src", "tests", "scripts")
    staged = git("diff", "--cached", "--name-only", "--", "CMakeLists.txt",
                 "include", "src", "tests", "scripts")
    return sorted({line for text in (unstaged, staged)
                   for line in text.splitlines() if line.strip()})


def freeze_backend(args: argparse.Namespace) -> None:
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    if args.source_commit and args.source_commit != source_commit:
        raise RuntimeError("source commit does not match HEAD")
    dirty = algorithm_scope_dirty()
    if dirty:
        raise RuntimeError(f"algorithm/source scope is dirty: {dirty}")
    development = read_json(OUT / "f0_development_decision.json")
    confirmation = (read_json(OUT / "f0_confirmation_decision.json")
                    if (OUT / "f0_confirmation_decision.json").is_file()
                    else None)
    key_long = (read_json(OUT / "f0_key_long_decision.json")
                if (OUT / "f0_key_long_decision.json").is_file() else None)
    entered_confirmation = bool(development["stage_pass"])
    entered_key_long = entered_confirmation and bool(
        confirmation and confirmation["stage_pass"])
    if entered_confirmation and confirmation is None:
        raise RuntimeError("eligible confirmation evidence is missing")
    if entered_key_long and key_long is None:
        raise RuntimeError("eligible key-long evidence is missing")
    f0_supported = bool(development["stage_pass"]) and bool(
        confirmation and confirmation["stage_pass"]) and bool(
            key_long and key_long["stage_pass"])
    promotion = {
        "schema": "round53-f0-fixed-interval-promotion-v1",
        "classification": ("f0_fixed_interval_supported" if f0_supported
                           else "f0_fixed_interval_negative"),
        "development_entered": True,
        "development_passed": bool(development["stage_pass"]),
        "confirmation_entered": entered_confirmation,
        "confirmation_passed": bool(
            confirmation and confirmation["stage_pass"]),
        "key_long_entered": entered_key_long,
        "key_long_passed": bool(key_long and key_long["stage_pass"]),
        "false_certificates": sum(int(item.get("false_certificates", 0))
                                  for item in (development, confirmation,
                                               key_long) if item),
        "certificate_losses": sum(int(item.get("certificate_losses", 0))
                                  for item in (development, confirmation,
                                               key_long) if item),
        "severe_regressions": sum(int(item.get("severe_regressions", 0))
                                  for item in (development, confirmation,
                                               key_long) if item),
        "source_commit": source_commit,
    }
    write_json(OUT / "f0_fixed_interval_promotion_decision.json", promotion)

    rescue_opened = False
    rescue = {
        "schema": "round53-bounded-rescue-selection-v1",
        "opened": rescue_opened,
        "selected_candidate": "none",
        "reason": ("F0-CLEAN passed every entered fixed-interval stage; "
                   "the conditional rescue gate did not open" if f0_supported
                   else "no bounded rescue implementation was frozen; "
                   "production v0 is retained"),
        "candidate_limit": 1,
        "R1_selected": False,
        "R2_selected": False,
    }
    write_json(OUT / "bounded_rescue_selection.json", rescue)
    rescue_fields = ["candidate", "state_id", "policy", "cap_seconds",
                     "status", "certificate", "work", "gap", "gi",
                     "entered", "reason"]
    write_csv(OUT / "bounded_rescue_development.csv", rescue_fields, [])
    write_csv(OUT / "bounded_rescue_confirmation.csv", rescue_fields, [])
    write_json(OUT / "bounded_rescue_decision.json", {
        "schema": "round53-bounded-rescue-decision-v1", "opened": False,
        "classification": "bounded_rescue_not_opened",
        "reason": rescue["reason"]})

    backend = F0 if f0_supported else V0
    classification = ("f0_backend_promoted" if f0_supported
                      else "production_v0_backend_retained")
    definition = {
        "schema": "round53-final-inner-backend-definition-v1",
        "classification": classification,
        "backend_name": "F0-CLEAN" if f0_supported else "production-v0",
        "policy": backend,
        "canonical_compact_model": "Round50 interval-MIP v0 core",
        "exhaustive_subset_duration_policy": (
            "off: omit only the historical exhaustive V<=12 subset-duration "
            "row block" if f0_supported else
            "historical-100000 under the frozen V<=12 writer guard"),
        "support_duration_callback": "off",
        "tailored_user_cuts": "off",
        "precrush": "Gurobi default",
        "branching": "Gurobi default",
        "symmetry_numerical": "Round50 v0 unchanged",
        "presolve": "Auto", "seed": 0, "threads": 1,
        "mip_gap": 0, "mip_gap_abs": 0,
        "controller": {"K0": 1, "intervals": 1,
                       "point_rule": "midpoint", "tau": 0.08},
        "instance_size_time_or_history_dispatch": False,
        "source_commit": source_commit, "source_tree": source_tree,
    }
    write_json(OUT / "final_inner_backend_definition.json", definition)

    pair_files = (("development", "f0_development_pair_summary.csv"),
                  ("confirmation", "f0_confirmation_pair_summary.csv"),
                  ("key-long", "f0_key_long_pair_summary.csv"))
    ablation: list[dict[str, object]] = []
    for stage, name in pair_files:
        for row in csv_rows(OUT / name):
            ablation.append({"stage": stage, **row})
    write_csv(OUT / "final_fixed_interval_ablation.csv",
              list(ablation[0]) if ablation else ["stage"], ablation)

    exact_executable = args.exact_executable.resolve()
    fixed_executable = args.fixed_executable.resolve()
    manifest = {
        "schema": "round53-final-inner-backend-freeze-v1",
        "frozen": True, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit, "source_tree": source_tree,
        "backend_policy": backend, "classification": classification,
        "exact_executable_path": str(exact_executable),
        "exact_executable_sha256": sha256(exact_executable),
        "fixed_interval_harness_path": str(fixed_executable),
        "fixed_interval_harness_sha256": sha256(fixed_executable),
        "post_freeze_algorithm_changes_permitted": False,
        "sealed_panel_opened": False,
    }
    write_json(OUT / "final_inner_backend_freeze_manifest.json", manifest)
    print(json.dumps({"promotion": promotion, "backend": definition,
                      "freeze": manifest}, indent=2, sort_keys=True))


def authorize_sealed(args: argparse.Namespace) -> None:
    freeze = read_json(OUT / "final_inner_backend_freeze_manifest.json")
    integration = read_json(OUT / "k1_backend_integration_decision.json")
    if not freeze.get("frozen") or not integration.get("gate_pass"):
        raise RuntimeError("backend freeze or K1 integration gate failed")
    if integration.get("candidate_promoted_to_sealed") is not True:
        raise RuntimeError("K1 candidate was not promoted to sealed panel")
    if git("rev-parse", "HEAD") != freeze["source_commit"]:
        raise RuntimeError("source commit changed after backend freeze")
    if git("rev-parse", "HEAD^{tree}") != freeze["source_tree"]:
        raise RuntimeError("source tree changed after backend freeze")
    if algorithm_scope_dirty():
        raise RuntimeError("algorithm/source scope changed after freeze")
    executable = args.exact_executable.resolve()
    executable_hash = sha256(executable)
    if executable_hash != freeze["exact_executable_sha256"]:
        raise RuntimeError("official executable changed after freeze")
    manifest = read_json(OUT / "sealed_v12_instance_manifest.json")
    rows = manifest.get("rows", [])
    if len(rows) != 12:
        raise RuntimeError("sealed manifest does not contain twelve rows")
    hashes_ok = all(sha256(ROOT / str(row["input_path"])) ==
                    row["input_sha256"] for row in rows)
    opening = {
        "schema": "round53-sealed-v12-opening-audit-v1",
        "opening_authorized": hashes_ok,
        "opened_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_frozen": True, "source_commit": freeze["source_commit"],
        "source_tree": freeze["source_tree"],
        "executable_sha256": executable_hash,
        "backend_policy": freeze["backend_policy"],
        "k1_integration_passed": True,
        "sealed_input_count": len(rows),
        "sealed_input_hashes_pass": hashes_ok,
        "algorithm_changes_after_opening_permitted": False,
    }
    write_json(OUT / "sealed_v12_opening_audit.json", opening)
    print(json.dumps(opening, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("backend", "sealed-opening"))
    parser.add_argument("--source-commit")
    parser.add_argument("--exact-executable", type=Path, required=True)
    parser.add_argument("--fixed-executable", type=Path)
    args = parser.parse_args()
    if args.phase == "backend":
        if args.fixed_executable is None:
            raise RuntimeError("backend freeze requires --fixed-executable")
        freeze_backend(args)
    else:
        authorize_sealed(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
