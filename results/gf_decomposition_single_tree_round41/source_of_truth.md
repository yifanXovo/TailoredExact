# Round 41 source of truth

## Immutable baseline

Round 41 starts from Round 40 commit `3db7a5efbace14dfed7557560e96636f749b84bc` on `codex/round40-regression-adaptive`. The validated algorithm remains `C6-HGA-FULL`, four equal-width initial intervals, `rho=0.01`, one thread, Gurobi Seed 0, Presolve Auto, and zero relative and absolute gaps. Round 41 mechanisms are explicit and default-off.

The research branch is `codex/round41-decomposition-single-tree-feasibility`. Round 40 remains stacked on Round 39, so the Round 41 pull request must target `codex/round40-regression-adaptive`, not `main`.

## Authoritative inputs

- Frozen instances and hashes: `results/gf_small_hard_light_round39/frozen_instance_manifest.csv`.
- Unchanged ten-instance panel: `diagnostic_panel_manifest.csv`, copied by identity from the Round 40 predeclared diagnostic panel.
- Frozen gates and caps: `decision_gates_frozen.json`.
- Before/after default checks: `pre_default_c6_equivalence*.csv` and `post_default_c6_equivalence*.csv`.
- Static formulation code: `include/StaticSegmentedGini.hpp`, `src/StaticSegmentedGini.cpp`, and the canonical writer in `src/CplexBaseline.cpp`.
- One-job execution and certificate code: `src/PaperExternalGiniTree.cpp` and `src/GurobiBaseline.cpp`.

Raw LP models, native logs, progress traces, and per-run command manifests live under the local `runs/` tree. Compact summaries, hashes, audits, and recreation scripts are the committed evidence.

## Interpretation rules

1. A Gurobi status or bound is accepted only after the existing parameter, lifecycle, model-fingerprint, and finalization gates.
2. A strict certificate additionally requires native exact optimality, one static model and one integer optimize, a native bound matching the independently recomputed objective, and the original-problem verifier.
3. A root-LP run is diagnostic and never issues an original-problem certificate.
4. A capped run is a noncertificate unless native exact optimality was reached before the external process deadline.
5. Integer equivalence does not imply equality with the external-K2 LP relaxation.
6. Historical CPLEX results are API and engineering evidence only; they are not a performance target.

## Recreation

```text
D:/msys64/ucrt64/bin/python.exe scripts/freeze_round41.py
D:/msys64/ucrt64/bin/python.exe scripts/run_round41_direct_root_references.py --panel --process-cap 300 --force
D:/msys64/ucrt64/bin/python.exe scripts/run_round41_panel.py --stage root --force
D:/msys64/ucrt64/bin/python.exe scripts/run_round41_panel.py --stage exact
D:/msys64/ucrt64/bin/python.exe scripts/run_round41_default_equivalence.py --phase post --force
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round41_default_equivalence.py --phase post
D:/msys64/ucrt64/bin/python.exe scripts/analyze_round41.py --require-final
D:/msys64/ucrt64/bin/python.exe scripts/decide_round41.py --require-complete-witnesses
```

Replace the arm with `st-k2-p-core` or `st-k2-p-extended`, and use `--solve mip` only for an exact one-tree run. No official process cap is 3600 seconds or more.
