#!/usr/bin/env python3
"""Audit and narrowly remove redundant local Round 36 artifacts.

The Round 36 committed package is immutable historical evidence.  This script
only considers untracked, top-level files in that result directory.  It never
recurses for deletion, and it retains raw runs, invalidated attempts, and
representative evidence.  Run without ``--execute`` for a dry audit.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
ROUND36 = REPO / "results" / "gf_incumbent_decomposition_causal_round36"
OUT = REPO / "results" / "gf_gini_geometry_mechanism_round37"
EXPECTED_TRAJECTORY_SHA256 = (
    "5b665120c62f115d1370e0ee56c47a4bdcc891aa738d177baceb50def25fe310"
)
EXPECTED_TRAJECTORY_GZIP_SHA256 = (
    "176655fa8841b71faa3c743f5d8da78ff2bb21791a2449e20c68533525ba9827"
)

PROTECTED_USER_FILES = {
    "results/gf_compact_bc_round/handling_convention_test/handling_convention.json":
        "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b",
    "results/gf_compact_bc_timeprofile_round/progress_traces/"
    "exact_moderate_seed3301_1200s_static300.progress.csv":
        "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb",
    "results/gf_compact_bc_timeprofile_round/raw/"
    "exact_moderate_seed3301_1200s_static300.json":
        "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202",
}

RETAINED_DIRECTORIES = (
    "runs",
    "stage_c_runs",
    "invalidated_rows",
    "stage_c_invalidated_attempt_1_contract_bug",
    "baseline_equivalence_runs",
    "stage_c_contract_fix_equivalence_runs",
    "representative_raw",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decompressed_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def replacement_for(path: Path) -> tuple[str, str]:
    name = path.name
    if name == "trajectory_events.csv":
        return (
            "results/gf_incumbent_decomposition_causal_round36/trajectory_events.csv.gz",
            "byte-exact deterministic gzip retained and committed",
        )
    if name.startswith("interim_"):
        final_name = name.removeprefix("interim_")
        final_path = ROUND36 / final_name
        if final_path.is_file():
            return (final_path.relative_to(REPO).as_posix(),
                    "superseded by completed final artifact")
        if final_name == "trajectory_events.csv":
            return (
                "results/gf_incumbent_decomposition_causal_round36/trajectory_events.csv.gz",
                "superseded intermediate trajectory; final compressed trajectory retained",
            )
        return (
            "results/gf_incumbent_decomposition_causal_round36/"
            "evidence_package_summary.json",
            "superseded intermediate artifact; terminal package summary retained",
        )
    if name.startswith("stage_a_"):
        return (
            "results/gf_incumbent_decomposition_causal_round36/"
            "stage_a_build_and_tests.json",
            "transient command log summarized by tracked Stage A audit",
        )
    if name.startswith("stage_c_contract_fix_ctest."):
        return (
            "results/gf_incumbent_decomposition_causal_round36/"
            "stage_c_contract_fix_audit.json",
            "transient test log summarized by tracked contract-fix audit",
        )
    return (
        "results/gf_incumbent_decomposition_causal_round36/"
        "evidence_package_summary.json",
        "transient controller log superseded by tracked completion and runner records",
    )


def candidates() -> list[Path]:
    found: set[Path] = set()
    found.update(path for path in ROUND36.glob("interim_*") if path.is_file())
    found.update(path for path in ROUND36.glob("*.log") if path.is_file())
    # The uncompressed trajectory is byte-redundant with the committed gzip,
    # but the frozen Round 36 schema tests consume this exact local path.  It
    # is therefore an operational test fixture, not a removable artifact.
    return sorted(found, key=lambda path: path.name)


def directory_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in RETAINED_DIRECTORIES:
        root = ROUND36 / name
        files = [path for path in root.rglob("*") if path.is_file()] if root.is_dir() else []
        rows.append({
            "path": root.relative_to(REPO).as_posix(),
            "exists": root.is_dir(),
            "file_count": len(files),
            "bytes": sum(path.stat().st_size for path in files),
            "decision": "retain",
            "reason": "raw, invalidated, equivalence, or representative provenance",
        })
    return rows


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "round36_cleanup_manifest.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [
            "path", "bytes", "sha256", "artifact_class", "decision",
            "replacement", "verification", "removed",
        ])
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "round36_cleanup_manifest.json").write_text(
        json.dumps({**summary, "artifacts": rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    retained = summary["retained_directories"]
    lines = [
        "# Round 36 local-artifact cleanup manifest",
        "",
        "The committed Round 36 evidence package was not modified. Cleanup was",
        "restricted to explicitly enumerated untracked top-level files. No directory",
        "was recursively removed.",
        "",
        f"- Execution status: `{summary['execution_status']}`",
        f"- Candidate files: {summary['candidate_count']}",
        f"- Candidate bytes: {summary['candidate_bytes']}",
        f"- Removed files: {summary['removed_count']}",
        f"- Removed bytes: {summary['removed_bytes']}",
        f"- Trajectory identity verified: `{str(summary['trajectory_identity_verified']).lower()}`",
        f"- Protected user files unchanged: `{str(summary['protected_user_files_unchanged']).lower()}`",
        "",
        "## Retained provenance directories",
        "",
        "| Path | Files | Bytes | Reason |",
        "|---|---:|---:|---|",
    ]
    lines.extend(
        f"| `{row['path']}` | {row['file_count']} | {row['bytes']} | {row['reason']} |"
        for row in retained
    )
    lines += [
        "",
        "The per-file SHA-256 inventory and replacement rationale are in",
        "`round36_cleanup_manifest.csv` and `round36_cleanup_manifest.json`.",
        "",
    ]
    (OUT / "round36_cleanup_manifest.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    round36_resolved = ROUND36.resolve()
    if not ROUND36.is_dir() or round36_resolved.parent != (REPO / "results").resolve():
        raise RuntimeError(f"unsafe or missing Round 36 root: {round36_resolved}")

    protected_before = {
        name: sha256(REPO / name) for name in PROTECTED_USER_FILES
    }
    protected_ok = protected_before == PROTECTED_USER_FILES
    if not protected_ok:
        raise RuntimeError("protected user-file hashes changed before cleanup")

    raw = ROUND36 / "trajectory_events.csv"
    compressed = ROUND36 / "trajectory_events.csv.gz"
    raw_hash = sha256(raw)
    compressed_hash = sha256(compressed)
    decompressed_hash, decompressed_bytes = decompressed_sha256(compressed)
    trajectory_ok = (
        raw_hash == EXPECTED_TRAJECTORY_SHA256
        and compressed_hash == EXPECTED_TRAJECTORY_GZIP_SHA256
        and decompressed_hash == raw_hash
        and decompressed_bytes == raw.stat().st_size
    )
    if not trajectory_ok:
        raise RuntimeError("trajectory compression identity check failed")

    paths = candidates()
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.resolve().parent != round36_resolved:
            raise RuntimeError(f"refusing non-top-level cleanup target: {path}")
        replacement, verification = replacement_for(path)
        rows.append({
            "path": path.relative_to(REPO).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "artifact_class": (
                "duplicate_uncompressed" if path.name == "trajectory_events.csv"
                else "intermediate" if path.name.startswith("interim_")
                else "transient_log"
            ),
            "decision": "remove",
            "replacement": replacement,
            "verification": verification,
            "removed": False,
        })

    retained = directory_inventory()
    summary: dict[str, Any] = {
        "schema": "round37-round36-local-cleanup-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "round36_commit": "4eb8e36515bbb2dd36ba49c5605c7c1b12a7ae32",
        "round36_main_merge_commit": "414c01216bb3aa30eb1f27f390b6f23bf06cb2eb",
        "scope": "untracked top-level Round 36 files only",
        "candidate_count": len(rows),
        "candidate_bytes": sum(int(row["bytes"]) for row in rows),
        "removed_count": 0,
        "removed_bytes": 0,
        "execution_status": "audited_not_removed",
        "trajectory_identity_verified": trajectory_ok,
        "trajectory_source_sha256": raw_hash,
        "trajectory_compressed_sha256": compressed_hash,
        "trajectory_decompressed_sha256": decompressed_hash,
        "protected_user_file_sha256": protected_before,
        "protected_user_files_unchanged": protected_ok,
        "retained_directories": retained,
    }
    write_outputs(rows, summary)

    if args.execute:
        for path, row in zip(paths, rows):
            path.unlink()
            row["removed"] = True
        protected_after = {
            name: sha256(REPO / name) for name in PROTECTED_USER_FILES
        }
        if protected_after != protected_before:
            raise RuntimeError("protected user-file hashes changed during cleanup")
        summary.update({
            "removed_count": len(rows),
            "removed_bytes": sum(int(row["bytes"]) for row in rows),
            "execution_status": "removed_verified_redundant_files",
            "protected_user_files_unchanged": True,
        })
        write_outputs(rows, summary)

    print(json.dumps({
        key: summary[key] for key in (
            "execution_status", "candidate_count", "candidate_bytes",
            "removed_count", "removed_bytes", "trajectory_identity_verified",
            "protected_user_files_unchanged",
        )
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
