#!/usr/bin/env python3
"""Bind the frozen Round 50 definition to its clean official executables."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
BUILD = ROOT / "build" / "official-round50-fe793b20e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    fixed_exe = BUILD / "Round50IntervalMipExperiment.exe"
    full_exe = BUILD / "ExactEBRP.exe"
    if not fixed_exe.is_file() or not full_exe.is_file():
        raise RuntimeError("clean official executables are missing")
    fixed_hash = sha256(fixed_exe)
    full_hash = sha256(full_exe)

    definition_path = EVIDENCE / "interval_mip_vnext_definition.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    definition["official_executable_sha256"] = fixed_hash
    definition["official_full_solver_executable_sha256"] = full_hash
    definition["official_build_directory"] = str(
        BUILD.relative_to(ROOT)).replace("\\", "/")
    definition_path.write_text(
        json.dumps(definition, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = EVIDENCE / "interval_mip_vnext_freeze_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["official_executable_sha256"] = fixed_hash
    manifest["official_full_solver_executable_sha256"] = full_hash
    manifest["official_build_directory"] = str(
        BUILD.relative_to(ROOT)).replace("\\", "/")
    manifest["official_source_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest["official_source_tree"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip()
    definition_key = (
        "results/gf_k1_interval_mip_vnext_round50/"
        "interval_mip_vnext_definition.json")
    manifest["input_hashes"][definition_key] = sha256(definition_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# Round 50 clean official build and initial tests

- Build directory: `build/official-round50-fe793b20e`
- Source commit at configure/build: `{manifest['official_source_commit']}`
- Source tree: `{manifest['official_source_tree']}`
- Configuration: clean Release, MinGW GCC 14.2.0, Gurobi 13.0.2 enabled
- Full build: passed (100%)
- CTests: 28 passed, 0 failed
- Historical Python protocol tests: 158 distinct tests passed after binding the Round 46--49 suites to their existing SHA-named official executables
- Round 50 fixed-state executable SHA-256: `{fixed_hash}`
- Round 50 full-solver executable SHA-256: `{full_hash}`

The first broad protocol discovery attempt reported four class-setup errors solely because those historical suites defaulted to unsuffixed build paths. The expected official binaries existed in their SHA-named directories; rerunning the four suites with their documented environment overrides passed all 42 tests. No source or evidence assertion failed.

Final post-run evidence, default-off, certificate, coverage, source-scope, and storage audits are recorded separately and will be appended to the final test summary.
"""
    (EVIDENCE / "final_build_and_tests.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "fixed_executable_sha256": fixed_hash,
        "full_executable_sha256": full_hash,
        "ctests_passed": 28,
        "historical_protocol_tests_passed": 158,
    }, indent=2))


if __name__ == "__main__":
    main()
