#!/usr/bin/env python3
"""Create Round 23 environment records, cautious inventory, and evidence manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_gini_tree_round23"
IMMUTABLE = "results/gf_global_gini_tree_unified_validation_round/"
SELF_EXCLUDED = {
    "results/gf_global_gini_tree_round23/artifact_inventory.csv",
    "results/gf_global_gini_tree_round23/duplicate_artifact_groups.csv",
    "results/gf_global_gini_tree_round23/evidence_package_manifest.csv",
}
TEXT_SUFFIXES = {".md", ".json", ".csv", ".txt", ".cpp", ".hpp", ".h",
                 ".py", ".cmake", ".yml", ".yaml"}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty required artifact: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def workspace_files(tracked: set[str]) -> list[Path]:
    """Return the bounded per-file audit set.

    The checkout contains more than 288,000 result scratch files (about 72 GB).
    Hashing all of them would create a larger, less useful audit artifact.
    Track every repository file, every Round22/Round23 evidence file, and every
    non-result/non-build file individually; summarize other result/build trees.
    """
    selected: set[Path] = set()
    for rel in tracked:
        path = ROOT / rel
        if path.is_file():
            selected.add(path)
    for base in (ROOT / IMMUTABLE, OUT):
        if base.exists():
            selected.update(path for path in base.rglob("*") if path.is_file())
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = relative(path)
        first = rel.split("/", 1)[0]
        if rel.startswith(".git/") or rel in SELF_EXCLUDED:
            continue
        if first == "results" or first.startswith("build"):
            continue
        selected.add(path)
    for rel in (
        "build_round22/ExactEBRP-frozen.exe",
        "build_round22/frozen_executable.json",
        "build_round23/ExactEBRP-frozen.exe",
        "build_round23/frozen_executable.json",
    ):
        path = ROOT / rel
        if path.is_file():
            selected.add(path)
    return sorted((path for path in selected if relative(path) not in SELF_EXCLUDED),
                  key=relative)


def directory_summaries() -> list[dict[str, Any]]:
    rows = []
    candidates = [path for path in (ROOT / "results").iterdir() if path.is_dir() and
                  path not in {ROOT / IMMUTABLE.rstrip("/"), OUT}]
    candidates.extend(path for path in ROOT.iterdir()
                      if path.is_dir() and path.name.startswith("build"))
    for directory in sorted(candidates, key=relative):
        count = 0
        size = 0
        maximum = 0
        for path in directory.rglob("*"):
            if path.is_file():
                value = path.stat().st_size
                count += 1
                size += value
                maximum = max(maximum, value)
        rows.append({
            "path": relative(directory) + "/",
            "file_count": count,
            "bytes": size,
            "largest_file_bytes": maximum,
        })
    return rows


def git_state() -> tuple[set[str], dict[str, str]]:
    tracked = set(subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT, text=True).splitlines())
    output = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, text=True, errors="replace")
    states: dict[str, str] = {}
    for line in output.splitlines():
        if len(line) >= 4:
            states[line[3:].replace("\\", "/")] = line[:2]
    return tracked, states


def classify(rel: str, tracked: bool) -> tuple[str, str, str]:
    if rel.startswith(IMMUTABLE):
        return ("immutable official evidence", "retain", "Round22 immutable package")
    if rel.startswith("results/gf_global_gini_tree_round23/official/"):
        return ("current-round official evidence", "retain", "Round23 official run evidence")
    if rel.startswith("results/gf_global_gini_tree_round23/diagnostics/"):
        return ("excluded-attempt or required diagnostic evidence", "retain",
                "forensic, correction, smoke, or excluded-attempt audit path")
    if rel.startswith("results/gf_global_gini_tree_round23/"):
        return ("current-round analysis evidence", "retain", "required Round23 artifact")
    if rel.startswith("build_round23/"):
        return ("reproducible build output", "retain",
                "isolated official build retained; cleanup not required")
    if rel.startswith("build_"):
        return ("uncertain - retain", "retain", "pre-existing isolated build; entry state preserved")
    if "__pycache__" in rel or rel.endswith((".pyc", ".aux", ".blg", ".bbl", ".out")):
        return ("temporary or cache candidate", "retain",
                "pre-existing ownership or reference uncertain; conservative retention")
    if tracked:
        return ("tracked repository content", "retain", "tracked content defaults to retention")
    if rel.startswith("results/"):
        return ("uncertain - retain", "retain", "historical result ownership/reference uncertain")
    return ("uncertain - retain", "retain", "untracked entry-state ownership/reference uncertain")


def referenced_counts(files: list[Path], known: set[str]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    token = re.compile(r"[A-Za-z0-9_.-]+(?:[/\\][A-Za-z0-9_.-]+)+")
    root_text = str(ROOT).replace("\\", "/").lower() + "/"
    for source in files:
        rel_source = relative(source)
        if source.suffix.lower() not in TEXT_SUFFIXES or source.stat().st_size > 8 * 1024 * 1024:
            continue
        if rel_source.startswith("results/") and not (
                rel_source.startswith(IMMUTABLE) or
                rel_source.startswith("results/gf_global_gini_tree_round23/") or
                source.suffix.lower() == ".md" or
                any(marker in source.name.lower() for marker in (
                    "manifest", "report", "summary", "audit", "command",
                    "protocol", "index"))):
            # Raw historical streams/results are inventory targets, not likely
            # inbound-reference documents; scanning tens of thousands of them
            # would dominate the audit without improving path dependency data.
            continue
        try:
            text = source.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        seen = set()
        for match in token.findall(text.replace("\\\\", "/").replace("\\", "/")):
            normalized = match.strip("./").lower()
            if normalized.startswith(root_text):
                normalized = normalized[len(root_text):]
            if normalized in known and normalized != relative(source).lower():
                seen.add(normalized)
        for item in seen:
            counts[item] += 1
    return counts


def write_environments() -> int:
    count = 0
    frozen = json.loads((ROOT / "build_round23" / "frozen_executable.json").read_text(
        encoding="utf-8"))
    for directory in sorted((OUT / "official").glob("round23_*")):
        if not directory.is_dir() or not (directory / "command.json").exists():
            continue
        command = json.loads((directory / "command.json").read_text(encoding="utf-8"))
        payload = {
            "schema": "round23-run-environment-v1",
            "run_id": command["run_id"],
            "captured_post_run_from_frozen_host_configuration": True,
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "timezone": "Asia/Shanghai",
            "compiler": frozen["compiler"],
            "compiler_version": frozen["compiler_version"],
            "optimization": frozen["optimization"],
            "cplex_version": "22.1.1.0",
            "cplex_studio_dir2211": os.environ.get("CPLEX_STUDIO_DIR2211", ""),
            "threads": 1,
            "source_commit": command["source_commit"],
            "executable_sha256": command["executable_sha256"],
            "instance_sha256": command["instance_sha256"],
            "option_manifest_sha256": command["option_manifest_sha256"],
            "process_wall_budget_seconds": command["process_wall_budget_seconds"],
            "native_deadline_seconds": command["native_deadline_seconds"],
            "environment_variables_recorded": ["CPLEX_STUDIO_DIR2211"],
            "sensitive_environment_variables_recorded": False,
        }
        (directory / "environment.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        count += 1
    return count


def compression_audit() -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    saved = 0
    for manifest in sorted(OUT.rglob("compressed_artifacts.csv")):
        with manifest.open("r", encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                original = int(row["original_bytes"])
                stored = int(row["stored_bytes"])
                saved += original - stored
                rows.append({
                    "manifest": relative(manifest),
                    "logical_path": row["logical_path"],
                    "stored_path": str(manifest.parent.joinpath(row["stored_path"])
                                       .relative_to(ROOT)).replace("\\", "/"),
                    "original_bytes": original,
                    "stored_bytes": stored,
                    "bytes_saved": original - stored,
                    "original_sha256": row["original_sha256"],
                    "stored_sha256": row["stored_sha256"],
                })
    return rows, saved


def main() -> int:
    environment_count = write_environments()
    tracked, states = git_state()
    files = workspace_files(tracked)
    summaries = directory_summaries()
    hashes = {relative(path): sha(path) for path in files}
    known = {item.lower() for item in hashes}
    refs = referenced_counts(files, known)
    groups: dict[str, list[str]] = defaultdict(list)
    for rel, digest in hashes.items():
        groups[digest].append(rel)
    duplicate_id = {}
    duplicate_rows = []
    next_group = 1
    for digest, paths in sorted(groups.items()):
        if len(paths) < 2:
            continue
        group_id = f"dup_{next_group:05d}"
        next_group += 1
        total = sum((ROOT / path).stat().st_size for path in paths)
        duplicate_rows.append({
            "duplicate_group": group_id,
            "sha256": digest,
            "file_count": len(paths),
            "total_bytes_across_copies": total,
            "paths": "|".join(paths),
            "disposition": "retain_all_conservatively",
            "reason": "no duplicate removed without complete ownership and inbound-reference proof",
        })
        for path in paths:
            duplicate_id[path] = group_id
    inventory = []
    for path in files:
        rel = relative(path)
        category, decision, reason = classify(rel, rel in tracked)
        inventory.append({
            "record_type": "file",
            "path": rel,
            "file_count": 1,
            "bytes": path.stat().st_size,
            "largest_file_bytes": path.stat().st_size,
            "sha256": hashes[rel],
            "git_tracking": "tracked" if rel in tracked else "untracked",
            "git_worktree_state": states.get(rel, "unchanged_or_ignored"),
            "artifact_class": category,
            "inbound_exact_path_reference_count": refs.get(rel.lower(), 0),
            "exact_duplicate_group": duplicate_id.get(rel, ""),
            "retention_decision": decision,
            "retention_reason": reason,
        })
    for summary in summaries:
        rel = summary["path"]
        if rel.startswith("build"):
            category = "reproducible or pre-existing build tree summary"
            reason = "directory-level summary; build ownership defaults to retention"
        else:
            category = "uncertain historical/scratch result tree summary"
            reason = "directory-level summary; ownership and references uncertain"
        inventory.append({
            "record_type": "directory_summary",
            **summary,
            "sha256": "not_computed_directory_summary",
            "git_tracking": "mixed_or_untracked",
            "git_worktree_state": "summarized",
            "artifact_class": category,
            "inbound_exact_path_reference_count": refs.get(rel.rstrip("/").lower(), 0),
            "exact_duplicate_group": "not_evaluated_for_summary",
            "retention_decision": "retain",
            "retention_reason": reason,
        })
    write_rows(OUT / "artifact_inventory.csv", inventory)
    if duplicate_rows:
        write_rows(OUT / "duplicate_artifact_groups.csv", duplicate_rows)
    else:
        write_rows(OUT / "duplicate_artifact_groups.csv", [{
            "duplicate_group": "none", "sha256": "", "file_count": 0,
            "total_bytes_across_copies": 0, "paths": "",
            "disposition": "no_exact_duplicates", "reason": "none found"}])

    compression, saved = compression_audit()
    compressed_lines = "\n".join(
        f"- `{row['stored_path']}`: {row['original_bytes']} -> "
        f"{row['stored_bytes']} bytes; saved {row['bytes_saved']}; original "
        f"SHA-256 `{row['original_sha256']}`, stored SHA-256 `{row['stored_sha256']}`."
        for row in compression)
    (OUT / "artifact_retention_policy.md").write_text(f"""# Round 23 artifact retention policy

The policy is conservative: immutable Round 22 evidence, all Round 23 official
evidence, forensic diagnostics, excluded attempts, commands, manifests, native
logs, result JSONs, canonical checkpoints, and uncertain historical artifacts
are retained. Tracked historical files default to retention. Pre-existing
untracked content is user-owned and retained.

Only the Round 23 runner's deterministic gzip operation was applied to new
streams exceeding 1 MiB. It records original/stored paths, sizes, hashes, and
`mtime=0`; canonical checkpoints remain directly readable. Exact duplicates
are inventoried but not removed because ownership and all inbound references
cannot be proved expendable. Reproducible builds are classified but retained
for final executable verification. No broad ignore rule was added.

`artifact_inventory.csv` hashes every tracked file, every immutable Round 22
and current Round 23 evidence file, and every non-result/non-build workspace
file. The remaining 288k-file/72GB scratch-result and build trees are recorded
as directory summaries with file counts, aggregate bytes, and largest-file
sizes; this avoids manufacturing an oversized inventory. `.git` internals and
the inventory/duplicate/evidence-manifest files themselves are excluded because
their changing self-hashes prevent a closed manifest. Those generated artifacts
are included in `evidence_package_manifest.csv` where applicable.
""", encoding="utf-8")
    (OUT / "artifact_cleanup_audit.md").write_text(f"""# Round 23 artifact cleanup audit

- Workspace files individually inspected and SHA-256 hashed: {len(files)}.
- Large result/build trees inventoried at directory level: {len(summaries)}.
- Files represented by directory summaries: {sum(row['file_count'] for row in summaries)}.
- Bytes represented by directory summaries: {sum(row['bytes'] for row in summaries)}.
- Structured exact-path reference scan inputs: source/docs/tests plus Round22/
  Round23 evidence and historical report/manifest/audit/index files up to 8 MiB.
- Files removed: 0.
- Exact duplicate groups removed: 0.
- Deterministically compressed new Round 23 streams: {len(compression)}.
- Bytes before compression: {sum(row['original_bytes'] for row in compression)}.
- Bytes after compression: {sum(row['stored_bytes'] for row in compression)}.
- Bytes saved: {saved}.
- Official run environment records retained: {environment_count}.
- Round 22 official files affected: 0.
- Uncertain files retained: {sum(row['artifact_class'] == 'uncertain - retain' for row in inventory)}.

No candidate was deleted merely because it was large, duplicated, ignored, or
untracked. All pre-existing content was retained. Compression affected only
new Round 23 paths listed below; their per-run `compressed_artifacts.csv`
manifests remain authoritative.

{compressed_lines}
""", encoding="utf-8")

    # Generate this last so it contains the final hashes of every other Round23 file.
    evidence = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path.name == "evidence_package_manifest.csv":
            continue
        rel = relative(path)
        category, _, _ = classify(rel, rel in tracked)
        evidence.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha(path),
            "evidence_class": category,
            "exists": True,
        })
    write_rows(OUT / "evidence_package_manifest.csv", evidence)
    largest = max(evidence, key=lambda row: int(row["bytes"]))
    print(json.dumps({
        "workspace_files_individually_hashed": len(files),
        "directory_summaries": len(summaries),
        "files_in_directory_summaries": sum(row["file_count"] for row in summaries),
        "duplicate_groups": len(duplicate_rows),
        "files_removed": 0,
        "compressed_files": len(compression),
        "bytes_saved": saved,
        "environment_records": environment_count,
        "evidence_files": len(evidence),
        "largest_round23_artifact": largest,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
