#!/usr/bin/env python3
"""Fail-closed final delivery audit for the completed Round 56 package."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import round56_common as r56
from round56_route_archive import EXECUTABLE_SHA256, SOURCE_FREEZE


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object in {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def truth(value: Any) -> bool:
    return str(value).lower() == "true"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=r56.ROOT, text=True).strip()


def main() -> int:
    results = read_csv(r56.EVIDENCE / "official_results.csv")
    checkpoints = read_csv(r56.EVIDENCE / "official_checkpoints.csv")
    execution = load_json(r56.EVIDENCE / "execution_manifest.json")
    summary = load_json(r56.EVIDENCE / "analysis_summary.json")
    preservation = load_json(r56.EVIDENCE / "preexisting_files_final_verification.json")
    decision = load_json(r56.EVIDENCE / "final_decision.json")
    route_verification = read_csv(r56.EVIDENCE / "independent_route_verification.csv")
    inventory = read_csv(r56.EVIDENCE / "final_evidence_inventory.csv")
    inventory_failures = []
    for row in inventory:
        path = r56.ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
            inventory_failures.append(row["path"])
    forbidden = (
        "--incumbent-json", "--hga-incumbent", "--external-incumbent",
        "--frontier-focus-from-result", "--frontier-import-interval-bound", "--frontier-focus-only",
        "--frontier-resume-state", "--frontier-resume-open-nodes", "--incumbent-archive-auto",
    )
    forbidden_rows = [row["scenario_id"] for row in execution["rows"] if any(option in row["command"] for option in forbidden)]
    algorithm_source_changes = git("diff", "--name-only", SOURCE_FREEZE, "--", "CMakeLists.txt", "include", "src").splitlines()
    checks = {
        "mandatory_row_count_50": len(results) == 50,
        "primary_q30_count_40": sum(row["panel_class"] == "primary_q30" for row in results) == 40,
        "q20_sentinel_count_10": sum(row["panel_class"] == "q20_sentinel" for row in results) == 10,
        "extension_count_9": sum(int(row["solver_process_cap_seconds"]) == 7200 for row in results) == 9,
        "all_process_caps_respected": all(truth(row["process_cap_respected"]) for row in results),
        "common_3600_checkpoint_count_50": sum(int(row["checkpoint_seconds"]) == 3600 for row in checkpoints) == 50,
        "zero_correctness_failures": summary["correctness_failures"] == 0,
        "zero_false_certificates": summary["false_certificates"] == 0,
        "all_verified_witnesses_packaged": summary["verified_incumbents"] == summary["exact_route_packages"] + summary["nonexact_route_packages"],
        "all_route_packages_independently_verified": all(not truth(row["package_available"]) or truth(row["passed"]) for row in route_verification),
        "no_route_postsolve": all(not truth(row.get("optimization_or_repair_performed")) for row in route_verification if truth(row["package_available"])),
        "one_official_executable": execution["executable_sha256"] == EXECUTABLE_SHA256 and sha256(r56.ROOT / "build" / "official-round56-paper-dataset-75e585211" / "ExactEBRP.exe") == EXECUTABLE_SHA256,
        "source_freeze_identity": execution["source_freeze_commit"] == SOURCE_FREEZE,
        "no_algorithm_source_change_after_freeze": not algorithm_source_changes,
        "no_forbidden_external_or_resume_inputs": not forbidden_rows,
        "user_files_preserved": bool(preservation["all_preserved"]),
        "final_evidence_hashes_match": not inventory_failures,
        "panel_not_overclaimed_as_final_paper_evidence": decision["ready_as_final_paper_evidence"] is False,
    }
    output = {
        "schema": "round56-publication-readiness-audit-v1", "checks": checks,
        "all_checks_pass": all(checks.values()), "algorithm_source_changes_after_freeze": algorithm_source_changes,
        "forbidden_command_rows": forbidden_rows, "evidence_inventory_hash_failures": inventory_failures,
        "missing_scenarios": decision["missing_scenarios"],
    }
    r56.write_json(r56.EVIDENCE / "publication_readiness_audit.json", output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
