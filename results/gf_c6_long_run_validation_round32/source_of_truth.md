# Round 32 source of truth

- Authoritative workspace: `E:\codes\ExactEBRP`
- Round 32 branch: `codex/round32-c6-long-run-validation`
- Round 32 starting HEAD: `919fd688a29a730d897db612213982ba8792a53f`
- Observed live `main` before Round 32: `2acc29c5556ddd3b229d65fd2b3fb8982ce6b8d2`
- Pre-freeze working HEAD: `0927d055710f43836053ecca055c0780b955a845`
- Frozen C6 source commit: `0927d055710f43836053ecca055c0780b955a845`
- Round 32 pre-official commits:
  - `3aeedec1eb2b9670c78a6f801a606b6008ed9e1b` — initial trace,
    runner, protocol, instances, matrices, tests, and evidence freeze;
  - `71bfa89b810b74ba2795013d0642aece4233da4a` — general completion
    metadata projection repair;
  - `353747407c586e001dbc3d29e42d0157264a1531` — distinguish
    deadline-sampled endpoints from frozen mathematical decisions;
  - `40c06de90f7e91f9a4322681bc4664328020d212` — explicitly classify
    instantaneous certified single-callback traces as AUC-unavailable.
  - `0927d055710f43836053ecca055c0780b955a845` — replace
    rollback-prone native callback wall-clock trace timestamps with local
    monotonic elapsed timestamps after the first long-run matrix exposed a
    host-clock correction.
- Isolated build root: `build_round32/`
- Isolated evidence root: `results/gf_c6_long_run_validation_round32/`
- Pre-existing status entries preserved: 509 (3 tracked dirty, 506 untracked)
- Stable CPLEX paper mainline: S0/F0-CPLEX
- Same-solver benchmark: P-GRB
- Validated candidate under test: C6-FROZEN

The Gurobi license is inherited only by licensed child processes. Its path
and contents are never read, copied, hashed, printed, or serialized by Round
32 scripts or evidence.
