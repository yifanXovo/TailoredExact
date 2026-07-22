#!/usr/bin/env python3
"""Create the solver-blind Round 26 manifests and immutable protocol seal."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_external_gurobi_production_validation_round26"
BASE_COMMIT = "d8cba691424eb990fc22357f7a2911ec5d34f3df"
GENERATOR_COMMIT = "0573d21c39d7c8fa8edb29f9eacb4184faa26bde"
OBSERVED_MAIN = "4a608eeae559cc69ca5c37b6eb4abab74fd3bc3b"
BRANCH = "codex/round26-external-gurobi-production-validation"

DEVELOPMENT = (
    ("V12_M1", "reference/regen_candidate_V12_M1_average.txt", "v12", 12, 1, ""),
    ("V12_M2", "reference/regen_candidate_V12_M2_average.txt", "v12", 12, 2, ""),
    ("high_imbalance_seed3202", "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "high_imbalance", 20, 3, "3202"),
    ("moderate_seed3302", "reference/hard_stress/V20_M3/moderate_seed3302.txt", "moderate", 20, 3, "3302"),
    ("tight_T_seed3101", "reference/hard_stress/V20_M3/tight_T_seed3101.txt", "tight_T", 20, 3, "3101"),
)

GENERATED = (
    ("round26_heldout_v20_manifest.csv", "reference/heldout_round26/V20_M3/manifest.csv", "round26-heldout-v20"),
    ("round26_v50_manifest.csv", "reference/heldout_round26/V50_M3/manifest.csv", "round26-v50"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fields = (
        "instance", "full_path", "relative_path", "generator_command",
        "generator_commit", "family", "V", "M", "seed", "sha256",
        "sealed_before_solver_runs",
    )
    development_rows: list[dict[str, object]] = []
    for instance, relative, family, v, m, seed in DEVELOPMENT:
        path = ROOT / relative
        development_rows.append(dict(zip(fields, (
            instance, str(path.resolve()), relative,
            "pre-existing tracked reference; no Round 26 generation",
            BASE_COMMIT, family, v, m, seed, sha256(path), "yes",
        ))))
    write_csv(OUT / "round26_development_manifest.csv", development_rows)

    seal_rows: list[dict[str, object]] = []
    for output_name, source_name, suite in GENERATED:
        source = ROOT / source_name
        rows: list[dict[str, object]] = []
        with source.open(newline="", encoding="utf-8") as stream:
            for item in csv.DictReader(stream):
                relative = item["path"]
                path = ROOT / relative
                actual = sha256(path)
                if actual != item["sha256"]:
                    raise RuntimeError(f"generated hash mismatch: {relative}")
                row = dict(zip(fields, (
                    item["instance_id"], str(path.resolve()), relative,
                    "D:/msys64/ucrt64/bin/python.exe "
                    "scripts/generate_hard_exact_stress_instances.py "
                    f"--suite {suite}", GENERATOR_COMMIT,
                    item["stress_type"], item["V"], item["M"], item["seed"],
                    actual, "yes",
                )))
                rows.append(row)
                seal_rows.append(row)
        write_csv(OUT / output_name, rows)

    seal = {
        "schema": "round26-heldout-seal-v1",
        "created_before_any_round26_solver_run": True,
        "generator_commit": GENERATOR_COMMIT,
        "seed_rule": (
            "Keep every unused preferred seed. For each conflicting preferred "
            "seed, choose the first globally unused integer strictly above the "
            "maximum preferred seed for that family."
        ),
        "conflicts": {
            "5101": "tracked V50 moderate evidence",
            "5201": "tracked V50 high-imbalance evidence",
            "6101": "tracked V100 moderate evidence",
            "6201": "tracked V100 high-imbalance evidence",
        },
        "files": [
            {"path": row["relative_path"], "sha256": row["sha256"]}
            for row in seal_rows
        ],
    }
    (OUT / "heldout_seal.json").write_text(
        json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    source = f"""# Round 26 source of truth

- Authoritative checkout: `{ROOT}`
- Branch: `{BRANCH}`
- Round 25 base/current starting HEAD: `{BASE_COMMIT}`
- Generator commit: `{GENERATOR_COMMIT}`
- Observed live `origin/main` before Round 26 work: `{OBSERVED_MAIN}`
- Gurobi license policy: `GRB_LICENSE_FILE` is set only in child-process
  environments. Its file is never opened, copied, hashed, printed, or serialized.
- Dirty-tree policy: all pre-existing staged, unstaged, and untracked user paths
  are preserved and excluded from Round 26 commits.

The held-out seal was produced before any Round 26 solver execution. A solver
runner must verify every sealed hash and the protocol hash before launching a
held-out or V50 process. Round 22--25 evidence is immutable context only.
"""
    (OUT / "source_of_truth.md").write_text(source, encoding="utf-8")

    protocol = """# Round 26 frozen evaluation protocol

This protocol was sealed before V12 forensics, candidate development, or any
held-out solve. All runs are serial, one-threaded, Seed 0, and include model
generation, HGA (where applicable), artifact work, native optimization,
verification, certification, and finalization in the process-wall budget.

## Frozen arms

- **P-GRB**: the complete original compact MILP in Gurobi 13.0.2, automatic
  presolve, `MIPGap=0`, `MIPGapAbs=0`, with no HGA, known UB, or Tailored data.
- **C0**: the exact Round 25 `EXT-GRB-COLD` solver-neutral external global-Gini
  tree, static F0 leaf models, independently verified same-run HGA UB,
  non-strict cutoff, frozen interval/scheduler/lifecycle/certificate rules, and
  no explicit cross-model warm start.
- **C1**: at most C0 plus one uniform solver-independent mechanism, with one
  parameter set on every instance. It equals C0 if no prototype passes.
- **S0-REF**: immutable corrected CPLEX S0/F0 historical context; it receives no
  Round 26 optimization work.

No arm may dispatch on instance, family, seed, V, M, path, known objective, or
observed result. There is no plain-Gurobi fallback, warm production arm,
portfolio, restricted-route proof, enumeration, or heuristic proof.

## Sealing and blind choices

The development suite is exactly V12_M1, V12_M2, high3202, moderate3302, and
tight3101. The six new V20 and three V50 files are fixed by the accompanying
SHA-256 manifests. They remain solver-sealed until C1 and its exactness argument
are frozen. Seed substitutions follow the preregistered audit rule in
`heldout_seal.json`; no performance filtering is allowed.

The four long cases are fixed blindly as high-imbalance 5202, moderate 5301,
tight-time 5102, and V50 moderate 6301. They may not be replaced.

## V12 forensics and candidate selection

Run three fresh 300-second repetitions of P-GRB and C0 on each V12 case (12
runs). Classify noise when wall ordering changes but median Work and structure
stay within 5%; structural overhead when C0 repeatedly incurs more Work,
presolve/root/model-read executions, or restarts; otherwise classify mixed.

At most two prototypes may run, only on the five development instances, at no
more than 600 seconds per run. C1 passes development only if all correctness,
coverage, lifecycle, verifier, bound, and certificate gates pass; V12_M1 median
certificate Work/time is no more than 5% worse than P-GRB; V12_M2 is within 5%
or reduces C0's excess deterministic Work by at least 50%; each difficult
development case loses at most 0.02 normalized final-LB and bound-AUC versus
C0; and one uniform parameter set is used. A failed prototype cannot become C1.

## Official matrix

- Stage 0: clean Gurobi-enabled and CPLEX-only builds, all C++/Python tests,
  license/model/import/coverage/lifecycle/scheduler/status/artifact/certificate
  gates, no-dispatch scans, and C0/C1 moderate4301 120-second sentinels.
- Stage 1: 5 development instances x P-GRB/C0/C1 x 1200 seconds = 15 rows.
- Stage 2: 6 sealed V20 x P-GRB/C0/C1 x 1800 seconds = 18 rows.
- Stage 3: 3 sealed V50 x P-GRB/C1 x 1800 seconds = 6 rows.
- Stage 4: 4 fixed long cases x P-GRB/C1 x 3600 seconds = 8 rows.

Exactly 47 official rows are required. Every official P-GRB/C1 pair is ranked
by strict certificate, certificate time, valid final LB, common-UB gap,
normalized bound-progress AUC, then gap-threshold crossings. Each P-GRB win
triggers exactly one enhanced C1 replay (600 seconds for V12/V20, 900 for V50),
which never replaces the official row.

## Frozen promotion rule

C1 is promoted only if every qualitative gate in the task passes and all of:

1. zero correctness, verifier, coverage, lifecycle, bound, or certificate
   failures and zero no-dispatch findings;
2. both V12 regressions meet the development bounds above or are supported as
   timing noise by three-repeat Work/structure evidence;
3. C1 wins at least 80% of non-V12 P-GRB pairs across known and held-out V20,
   with no family having a majority of C1 regressions;
4. held-out V20 mean and median common-UB gap or bound-AUC improve materially;
5. C1 produces at least one strict held-out V20 certificate on a case not
   strictly certified by its matched P-GRB row or not certified at 1800 seconds
   before its fixed 3600-second closure run;
6. all V50 models and bounds validate and C1 wins at least two of three
   1800-second V50 pairs;
7. each non-certified 3600-second C1 row improves its valid global LB after
   the halfway checkpoint (a strict certificate also satisfies this gate);
8. C1 wins or ties at least 80% of C0 pairs, has no family-level majority
   regression, and loses at most 0.02 normalized final-LB/AUC on any difficult
   case;
9. source/manifests prove no warm-start, seed/objective knowledge, portfolio,
   or instance-dependent resolution.

One failed gate retains corrected CPLEX S0/F0 as stable mainline. No mixed
selector is permitted, and official observations cannot change this rule.
"""
    (OUT / "round26_evaluation_protocol.md").write_text(
        protocol, encoding="utf-8")


if __name__ == "__main__":
    main()
