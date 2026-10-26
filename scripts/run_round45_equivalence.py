#!/usr/bin/env python3
"""Run final Round 45 default-off and candidate determinism sentinels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
COMP = OUT / "completion"
RUNS = COMP / "equivalence_runs"
EXE = ROOT / "build_round45_completion" / "ExactEBRP.exe"
CASES = (
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def remove(args: list[str], option: str) -> None:
    while option in args:
        index = args.index(option)
        del args[index:index + 2]


def replace(args: list[str], option: str, value: Any) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    if option in args:
        args[args.index(option) + 1] = rendered
    else:
        args.extend((option, rendered))


def relocate(args: list[str], old: Path, new: Path) -> list[str]:
    old_text, new_text = str(old), str(new)
    return [str(EXE) if index == 0 else value.replace(old_text, new_text)
            for index, value in enumerate(args)]


def execute(name: str, template: Path, explicit_defaults: bool | None) -> Path:
    directory = RUNS / name
    marker = directory / "completion_marker.json"
    if marker.is_file():
        return directory
    directory.mkdir(parents=True, exist_ok=True)
    source = load(template / "command.json")["command"]
    args = relocate(list(source), template, directory)
    round45_options = (
        "--round45-adaptive-parametric-partition", "--round45-initial-k0",
        "--round45-timing-rule", "--round45-rho-gamma",
        "--round45-point-rule", "--round45-minimum-child-width",
        "--round45-counterfactual-mode")
    if explicit_defaults is not None:
        for option in round45_options:
            remove(args, option)
        if explicit_defaults:
            defaults = {
                "--round45-adaptive-parametric-partition": "off",
                "--round45-initial-k0": 4,
                "--round45-timing-rule": "gamma-positive",
                "--round45-rho-gamma": 0.0,
                "--round45-point-rule": "midpoint",
                "--round45-minimum-child-width": 1e-4,
                "--round45-counterfactual-mode": "off",
            }
            for option, value in defaults.items():
                replace(args, option, value)
    executable_hash = hashlib.sha256(EXE.read_bytes()).hexdigest()
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        replace(args, option, executable_hash)
    write_json(directory / "command.json", {
        "schema": "round45-equivalence-command-v1", "command": args,
        "sequential_official_execution": True,
        "executable_sha256": executable_hash,
    })
    with (directory / "stdout.log").open("wb") as stdout, \
            (directory / "stderr.log").open("wb") as stderr:
        process = subprocess.run(args, cwd=ROOT, stdout=stdout, stderr=stderr,
                                 timeout=3660, check=False)
    if process.returncode or not (directory / "result.json").is_file():
        raise RuntimeError(f"equivalence sentinel failed: {name}")
    write_json(marker, {"complete": True, "name": name,
                        "executable_sha256": executable_hash})
    return directory


def close(a: Any, b: Any, tolerance: float = 1e-9) -> bool:
    try:
        return abs(float(a) - float(b)) <= tolerance * max(1.0, abs(float(a)), abs(float(b)))
    except (TypeError, ValueError):
        return a == b


def decisions(directory: Path) -> list[tuple[str, ...]] | None:
    path = directory / "external" / "timing_decision_ledger.csv"
    if not path.is_file():
        return None
    with path.open(newline="", encoding="utf-8-sig") as stream:
        values = list(csv.DictReader(stream))
    fields = ("parent_id", "old_c6_action", "final_action", "reason",
              "Gamma_sum", "D_R43", "split_point_rule")
    return [tuple(row.get(field, "") for field in fields) for row in values]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run final Round 45 default-off and candidate determinism sentinels.")
    parser.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    output: list[dict[str, Any]] = []
    for instance in CASES:
        c6 = COMP / "runs" / f"sentinel__{instance}__c6"
        implicit = execute(f"default_implicit__{instance}", c6, False)
        explicit = execute(f"default_explicit__{instance}", c6, True)
        left, right = load(implicit / "result.json"), load(explicit / "result.json")
        fields = ("strict_certified_original_problem", "status", "objective",
                  "lower_bound", "upper_bound", "external_gini_tree_split_count")
        passed = all(close(left.get(field), right.get(field)) for field in fields)
        output.append({
            "check": "implicit_vs_explicit_default_off", "instance": instance,
            "left_run": implicit.relative_to(ROOT).as_posix(),
            "right_run": explicit.relative_to(ROOT).as_posix(),
            "decision_identity": decisions(implicit) == decisions(explicit),
            "certificate_identity": passed, "pass": passed and decisions(implicit) == decisions(explicit),
        })

        candidate = COMP / "runs" / f"sentinel__{instance}__gamma-veto"
        repeat = execute(f"candidate_repeat__{instance}", candidate, None)
        a, b = load(candidate / "result.json"), load(repeat / "result.json")
        cert_fields = ("strict_certified_original_problem", "status", "objective",
                       "lower_bound", "upper_bound", "external_gini_tree_split_count")
        cert_same = all(close(a.get(field), b.get(field)) for field in cert_fields)
        decision_same = decisions(candidate) == decisions(repeat)
        output.append({
            "check": "candidate_deterministic_decision_repeat", "instance": instance,
            "left_run": candidate.relative_to(ROOT).as_posix(),
            "right_run": repeat.relative_to(ROOT).as_posix(),
            "decision_identity": decision_same, "certificate_identity": cert_same,
            "pass": decision_same and cert_same,
        })
    path = OUT / "completion" / "default_off_equivalence.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({"checks": len(output),
                      "passed": sum(bool(row["pass"]) for row in output)}, sort_keys=True))
    return 0 if all(row["pass"] for row in output) else 1


if __name__ == "__main__":
    raise SystemExit(main())
