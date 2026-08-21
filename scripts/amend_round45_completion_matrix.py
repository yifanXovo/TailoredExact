#!/usr/bin/env python3
"""One-time transparent amendment adding the mandatory Round 45 19-row rerun.

The original completion freeze assumed the already-certified small panel could be
reused.  A subsequent scope audit established that the parent-bound correction
touches the ordinary adaptive split path.  Section 9.2 therefore requires all
five development, seven validation, and seven holdout rows to be rerun.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
COMPLETION = OUT / "completion"
MATRIX = COMPLETION / "required_run_matrix.csv"
MANIFEST = COMPLETION / "completion_freeze_manifest.json"
OLD_RUNS = OUT / "runs"

MATERIAL = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "timing_two_witness__round39_small_medium_V12_M3_Q30_slot08_seed1343324363__k4_gamma012_mid",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317":
        "material_development__round39_small_medium_V10_M2_Q20_slot05_seed968549317__k4_gammaveto012_mid",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "material_development__round39_small_hard_V12_M3_Q20_slot07_seed621538683__k4_gammaveto012_mid",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "timing_two_witness__round39_small_hard_V12_M3_Q30_slot08_seed1288546114__k4_gammaveto012_mid",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "material_development__round39_small_hard_V10_M3_Q20_slot04_seed1145042375__k4_gammaveto012_mid",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def command_input(directory: Path) -> Path:
    value = json.loads((directory / "command.json").read_text(encoding="utf-8"))
    command = value[0] if isinstance(value, list) else value
    args = command.get("command", command.get("argv", []))
    return Path(args[args.index("--input") + 1]).resolve()


def main() -> int:
    original_bytes = MATRIX.read_bytes()
    rows = read_csv(MATRIX)
    fields = list(rows[0])
    if any(row["stage"].startswith("small_panel_rerun_") for row in rows):
        raise SystemExit("Round 45 small-panel amendment is already present")

    sources: list[tuple[str, str, Path]] = []
    for instance, run_name in MATERIAL.items():
        sources.append(("material", instance, OLD_RUNS / run_name))
    for role in ("validation", "holdout"):
        pattern = f"{role}__*__final_k4_gammaveto012_mid"
        for directory in sorted(OLD_RUNS.glob(pattern)):
            instance = directory.name.split("__")[1]
            sources.append((role, instance, directory))
    if len(sources) != 19 or len({item[1] for item in sources}) != 19:
        raise RuntimeError(f"expected fixed 19-row panel, found {len(sources)}")

    expected = ";".join((
        "command.json", "result.json", "global_bound_trace.csv",
        "common_horizon_trace.csv", "certificate_ledger.csv",
        "artifact_manifest.csv", "completion_marker.json"))
    additions = []
    for role, instance, old_directory in sources:
        input_path = command_input(old_directory)
        relative_input = input_path.relative_to(ROOT).as_posix()
        row_id = f"rerun19__{role}__{instance}__k4_gamma_veto"
        additions.append({
            "row_id": row_id,
            "stage": f"small_panel_rerun_{role}",
            "instance": instance,
            "input_path": relative_input,
            "input_sha256": digest(input_path),
            "arm": "gamma-veto",
            "K0": "4",
            "timing_rule": "gamma-veto",
            "timing_threshold": "rho_gamma=0.012",
            "point_rule": "midpoint",
            "envelope_mode": "all-parent-scope",
            "lookahead_mode": "frontier-d2",
            "process_cap_seconds": "3600",
            "required_checkpoints_seconds": "300;1200;3600",
            "acceptable_terminal": "strict_exact_or_honest_3600s_cap",
            "executable_sha256": "PENDING_FINAL_COMPLETION_EXECUTABLE_SHA256",
            "expected_evidence_files": expected,
            "completion_state": "required_pending",
            "run_directory": f"completion/runs/{row_id}",
            "parent_id": "",
            "parent_lower": "",
            "parent_upper": "",
            "selection_use": "true" if role == "material" else "false",
        })

    rows.extend(additions)
    with MATRIX.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["amendment"] = {
        "schema": "round45-completion-freeze-amendment-v1",
        "reason": "ordinary split-path parent-bound correction triggers Section 9.2 mandatory rerun",
        "original_required_run_matrix_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "original_row_count": len(rows) - len(additions),
        "added_row_count": len(additions),
        "amended_row_count": len(rows),
        "selection_basis": "the already-fixed five-development/seven-validation/seven-holdout panel; no new rerun result inspected",
    }
    manifest["required_run_matrix_sha256"] = digest(MATRIX)
    manifest["required_run_count"] = len(rows)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    print(json.dumps({"rows": len(rows), "added": len(additions),
                      "matrix_sha256": digest(MATRIX)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
