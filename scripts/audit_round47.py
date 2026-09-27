#!/usr/bin/env python3
"""Independently verify sealed Round 47 rows and top-level evidence hashes."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47"
RUNS = OUT / "runs"
EXPECTED = {"stage3_300s": 40, "stage4_1200s": 40, "stage5_1800s": 28}
ARMS = {"K4-AM", "K4-AMC", "K1-AM", "K1-AMC"}
FORBIDDEN_KEYS = ("gamma_veto", "Gamma_sum", "round43", "round44", "round45",
                  "PMM", "FPMM", "rank1", "frontier_consolidation",
                  "verified_mip_starts")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    failures = []
    counts = Counter()
    hashes = set()
    arms = set()
    artifacts = 0
    contractions = 0
    certificates = 0
    false_certificates = 0
    extra_lp = 0
    extra_mip = 0
    v50_rows = 0
    cap_over_1800 = 0
    forbidden_active = 0
    watchdogs = 0
    for run_dir in sorted(path for path in RUNS.iterdir() if path.is_dir() and
                          path.name.startswith(("stage3_", "stage4_", "stage5_"))):
        marker_path = run_dir / "completion_marker.json"
        if not marker_path.is_file():
            failures.append(f"missing marker: {run_dir.name}")
            continue
        marker = load_json(marker_path)
        command = load_json(run_dir / "command.json")
        result = load_json(run_dir / "result.json")
        if isinstance(result, list):
            result = result[0]
        counts[command["stage"]] += 1
        hashes.add(command.get("executable_sha256"))
        arms.add(command.get("arm"))
        watchdogs += int(bool(command.get("watchdog_timeout")))
        cap_over_1800 += int(float(command.get("process_cap_seconds", 0)) > 1800)
        v50_rows += int("v50" in " ".join(str(x).lower() for x in command.get("command", [])))
        identity = command.get("candidate_identity", {})
        forbidden_active += sum(str(identity.get(key, "off")).lower() not in
                                {"off", "false", "0", "none"} for key in FORBIDDEN_KEYS)
        contractions += int(result.get("round47_single_child_contraction_count", 0))
        certificates += int(bool(result.get("strict_certified_original_problem")))
        coverage = bool(result.get("external_gini_tree_root_coverage_valid"))
        false_certificates += int(bool(result.get("strict_certified_original_problem")) and not coverage)
        extra_lp += int(result.get("round47_adaptive_mass_extra_lp_count", 0))
        extra_mip += int(result.get("round47_adaptive_mass_extra_mip_count", 0))
        manifest_path = run_dir / "artifact_manifest.csv"
        if sha256(manifest_path) != marker.get("artifact_manifest_sha256"):
            failures.append(f"manifest hash mismatch: {run_dir.name}")
        manifest = rows(manifest_path)
        if len(manifest) != int(marker.get("artifact_count", -1)):
            failures.append(f"artifact count mismatch: {run_dir.name}")
        for row in manifest:
            path = run_dir / row["path"]
            artifacts += 1
            if not path.is_file():
                failures.append(f"missing artifact: {run_dir.name}/{row['path']}")
            elif path.stat().st_size != int(row["size_bytes"]):
                failures.append(f"artifact size mismatch: {run_dir.name}/{row['path']}")
            elif sha256(path) != row["sha256"]:
                failures.append(f"artifact hash mismatch: {run_dir.name}/{row['path']}")

    for stage, expected in EXPECTED.items():
        if counts[stage] != expected:
            failures.append(f"{stage}: expected {expected}, found {counts[stage]}")
    if not arms <= ARMS:
        failures.append(f"noncandidate benchmark arms found: {sorted(arms - ARMS)}")

    stage0 = load_json(OUT / "stage0_freeze_manifest.json")
    stage0_files = 0
    for row in stage0["files"]:
        path = OUT / row["path"]
        stage0_files += 1
        if not path.is_file() or sha256(path) != row["sha256"]:
            failures.append(f"stage0 freeze mismatch: {row['path']}")

    inventory_path = OUT / "final_evidence_inventory.csv"
    inventory_files = 0
    if inventory_path.exists():
        for row in rows(inventory_path):
            path = ROOT / row["path"]
            inventory_files += 1
            if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
                failures.append(f"final inventory mismatch: {row['path']}")

    report = {
        "pass": not failures, "failures": failures, "stage_rows": dict(counts),
        "arms": sorted(arms), "unique_executable_hashes": sorted(hashes),
        "sealed_artifacts_verified": artifacts, "stage0_files_verified": stage0_files,
        "final_inventory_files_verified": inventory_files,
        "certificates": certificates, "false_certificates": false_certificates,
        "contractions": contractions, "extra_lp_queries": extra_lp,
        "extra_mip_queries": extra_mip, "v50_rows": v50_rows,
        "cap_over_1800_rows": cap_over_1800, "watchdog_failures": watchdogs,
        "forbidden_mechanisms_active": forbidden_active,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
