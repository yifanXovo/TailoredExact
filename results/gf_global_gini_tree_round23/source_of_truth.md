# Round 23 source of truth

The authoritative workspace is the existing local checkout at
`E:\codes\ExactEBRP`. Round 23 was branched from local HEAD
`3c69cb2c04889db5ceb40e313a710d600089879d` as
`codex/round23-moderate4301-correctness-unified-convergence`, with the working
tree preserved exactly as found.

The single permitted inspection fetch observed `origin/main` at
`91ed0e314caae51ddbd8375d88cd65a5352c917f`. The merge base is the local base
SHA. Remote main has one history-only merge commit not present locally; both
commits resolve to tree `1b6e852b48dad4f5697909642e10acfb0b6fa81e`.
Therefore the relationship is **different commit history, identical source
tree**. No remote content was integrated or copied into the workspace.

No pull, merge, rebase, reset, restore, checkout-path, stash, clean, force
push, reclone, or remote-file replacement was performed. The local base, not
`origin/main`, remains the scientific and repository base.

At entry there were no staged changes. The two pre-existing tracked content
modifications were:

- `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
- `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`

They are user-owned, remain preserved, and are excluded from every Round 23
commit. All pre-existing untracked manuscript auxiliaries, older isolated
builds, scratch results, and historical diagnostics are likewise retained and
excluded. The handling-convention test touched a tracked JSON timestamp/line
ending state during validation, but its content has no Git diff and it is not
staged.

The immutable Round 22 evidence package is
`results/gf_global_gini_tree_unified_validation_round/`; no file beneath it is
modified. The actual frozen Round 22 executable is available and hashes to
`b3fecef84dce8d6a2323d25a7877d5f16d14aa5f1fb644ae642bf636a229ee62`.
It is kept distinct from all Round 23 rebuilds.

The stable paper mainline remains manifest-defined S0/F0. Corrected S0 changes
only the solver configuration required for safe continuous generic branching
(presolve, Reduce, and Linear all off) and accepts only nested native local-bound
contractions. P2 is independently switchable and is not promoted by this
targeted round.
