# Round 32 source of truth

- Authoritative workspace: `E:\codes\ExactEBRP`
- Round 32 branch: `codex/round32-c6-long-run-validation`
- Round 32 starting HEAD: `919fd688a29a730d897db612213982ba8792a53f`
- Observed live `main` before Round 32: `2acc29c5556ddd3b229d65fd2b3fb8982ce6b8d2`
- Pre-freeze working HEAD: `919fd688a29a730d897db612213982ba8792a53f`
- Frozen C6 source commit: recorded after the intended pre-run commit in
  `round32_frozen_manifest.json`
- Isolated build root: `build_round32/`
- Isolated evidence root: `results/gf_c6_long_run_validation_round32/`
- Pre-existing status entries preserved: 509 (3 tracked dirty, 506 untracked)
- Stable CPLEX paper mainline: S0/F0-CPLEX
- Same-solver benchmark: P-GRB
- Validated candidate under test: C6-FROZEN

The Gurobi license is inherited only by licensed child processes. Its path
and contents are never read, copied, hashed, printed, or serialized by Round
32 scripts or evidence.
