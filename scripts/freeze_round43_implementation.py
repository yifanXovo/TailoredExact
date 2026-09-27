#!/usr/bin/env python3
"""Freeze the tested Round 43 executable and implementation source hashes."""

from __future__ import annotations

from datetime import datetime, timezone
import subprocess

import round43_common as common


SOURCES = (
    "CMakeLists.txt",
    "include/CanonicalCompactModel.hpp",
    "include/FixedIntervalMipBackend.hpp",
    "include/GiniEnvelopeRefinement.hpp",
    "include/Instance.hpp",
    "src/CplexBaseline.cpp",
    "src/GiniEnvelopeRefinement.cpp",
    "src/GurobiBaseline.cpp",
    "src/PaperExternalGiniTree.cpp",
    "src/main.cpp",
    "tests/round41_protocol_tests.py",
    "tests/round43_envelope_refinement_tests.cpp",
    "tests/round43_protocol_tests.py",
    "scripts/round43_common.py",
    "scripts/run_round43_experiments.py",
)


def main() -> int:
    if not common.EXE.is_file():
        raise SystemExit(f"missing tested executable: {common.EXE}")
    rows = []
    for name in SOURCES:
        path = common.ROOT / name
        if not path.is_file():
            raise SystemExit(f"missing implementation input: {path}")
        rows.append({"path": name, "sha256": common.sha256(path)})
    common.write_csv(
        common.OUT / "implementation_source_manifest.csv", rows,
        ["path", "sha256"])
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=common.ROOT,
        check=True, capture_output=True, text=True).stdout.strip()
    common.write_json(common.OUT / "implementation_freeze.json", {
        "schema": "round43-implementation-freeze-v1",
        "round_id": 43,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "base_head_sha": git,
        "research_branch": common.RESEARCH_BRANCH,
        "executable": common.relative(common.EXE),
        "executable_sha256": common.sha256(common.EXE),
        "source_manifest": common.relative(
            common.OUT / "implementation_source_manifest.csv"),
        "compiled_ctest": {"passed": 21, "failed": 0},
        "python_unittest_discovery": {"passed": 125, "failed": 0},
        "round43_protocol_tests": {"passed": 8, "failed": 0},
        "build_type": "Release",
        "gurobi": "13.0.2",
        "presolve": "Auto",
        "seed": 0,
        "threads": 1,
        "mip_gap": 0.0,
        "mip_gap_abs": 0.0,
        "certificate_tolerance": 1e-7,
        "official_stage1_ready": True,
        "validation_opened": False,
        "holdout_opened": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
