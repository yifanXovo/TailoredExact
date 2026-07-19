#!/usr/bin/env python3
"""Final Round 23 official-evidence and cleanup-integrity gates."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_gini_tree_round23"
checks = 0


def require(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    required = (
        "stage1_300s_gate_results.csv", "stage2_900s_results.csv",
        "paired_candidate_comparison.csv", "time_to_strict_certificate.csv",
        "common_ub_time_to_gap_thresholds.csv",
        "common_ub_bound_progress_auc.csv", "mechanism_overhead.csv",
        "exactness_audit.csv", "artifact_inventory.csv",
        "duplicate_artifact_groups.csv", "artifact_retention_policy.md",
        "artifact_cleanup_audit.md", "evidence_package_manifest.csv",
    )
    require(all((OUT / name).is_file() and (OUT / name).stat().st_size > 0
                for name in required), "required final artifact missing/empty")

    stage1 = rows(OUT / "stage1_300s_gate_results.csv")
    stage2 = rows(OUT / "stage2_900s_results.csv")
    require(len(stage1) == 6, "Stage 1 row count changed")
    require(len(stage2) == 12, "Stage 2 row count changed")
    require(all(row["structural_gate_passed"] == "True" for row in stage1),
            "Stage 1 structural failure")
    require(all(row["structural_gate_passed"] == "True" for row in stage2),
            "Stage 2 structural failure")
    require(not any(row["interrupted"] == "True" for row in stage1 + stage2),
            "official run interruption present")

    exact = rows(OUT / "exactness_audit.csv")
    require(len(exact) == 18, "exactness audit must cover all official runs")
    require(all(row["exactness_audit_passed"] == "True" for row in exact),
            "official exactness audit failure")
    require(all(row["raw_timestamps_strictly_increase"] == "True" for row in exact),
            "raw timestamp monotonicity failure")
    require(all(row["solver_final_endpoint_matches_result"] == "True" for row in exact),
            "raw solver-final endpoint mismatch")
    require(all(row["callback_and_exactness_failure_count"] == "0" for row in exact),
            "callback/exactness failure counter nonzero")
    require(len({row["run_id"] for row in exact}) == 18,
            "duplicate exactness-audit run id")

    pairs = rows(OUT / "paired_candidate_comparison.csv")
    counts = Counter(row["classification"] for row in pairs)
    require(len(pairs) == 6, "paired matrix must contain six instances")
    require(counts == Counter({"regress": 4, "improve": 2}),
            f"unexpected paired classification: {counts}")
    require(not any(row["certificate_loss"] == "True" for row in pairs),
            "candidate lost a strict certificate")
    require(not any(row["certificate_gain"] == "True" for row in pairs),
            "unexpected certificate gain accounting")
    require(not any(row["material_regression"] == "True" for row in pairs),
            "material-regression flag present")

    environments = sorted((OUT / "official").glob("round23_*/environment.json"))
    require(len(environments) == 18, "one environment record required per official run")
    for path in environments:
        data = json.loads(path.read_text(encoding="utf-8"))
        command = json.loads((path.parent / "command.json").read_text(encoding="utf-8"))
        require(data["run_id"] == command["run_id"], f"environment run mismatch: {path}")
        require(data["executable_sha256"] == command["executable_sha256"],
                f"environment executable mismatch: {path}")

    compression = []
    for manifest in OUT.rglob("compressed_artifacts.csv"):
        compression.extend((manifest.parent, row) for row in rows(manifest))
    require(len(compression) == 58, "compression manifest row count changed")
    require(all((base / row["stored_path"]).is_file() for base, row in compression),
            "compressed stored path missing")
    require(all(sha(base / row["stored_path"]) == row["stored_sha256"]
                for base, row in compression), "compressed stored hash mismatch")

    evidence = rows(OUT / "evidence_package_manifest.csv")
    require(len(evidence) > 600, "evidence package unexpectedly small")
    require(len({row["path"] for row in evidence}) == len(evidence),
            "duplicate evidence-manifest path")
    require(all((ROOT / row["path"]).is_file() for row in evidence),
            "evidence-manifest path missing")
    require(all(sha(ROOT / row["path"]) == row["sha256"] for row in evidence),
            "evidence-manifest hash mismatch")

    cleanup = (OUT / "artifact_cleanup_audit.md").read_text(encoding="utf-8")
    require("Files removed: 0" in cleanup, "cleanup removal accounting changed")
    require("Round 22 official files affected: 0" in cleanup,
            "Round22 cleanup protection missing")
    immutable_diff = subprocess.check_output(
        ["git", "diff", "--name-only", "--",
         "results/gf_global_gini_tree_unified_validation_round"],
        cwd=ROOT, text=True).strip()
    require(not immutable_diff, "immutable Round22 package has a worktree diff")

    require(checks >= 35, "final evidence suite did not reach required breadth")
    print(f"Round23FinalEvidenceTests: {checks} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
