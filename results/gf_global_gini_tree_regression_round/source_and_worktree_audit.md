# Round 20 source and worktree audit

Audit date: 2026-07-15 (Asia/Shanghai).

The verified live `main`, `origin/main`, and local `main` all identified commit
`16d810f1cf6673f4c2203d472613433a6ad674de`, the merge of Round 19 PR #65.
The Round 19 implementation commit `5c2b1ef...` is contained in that history.
The Round 20 branch was created directly from the verified commit as
`codex/round20-global-tree-regression-diagnosis`.

No clone, pull, rebase, reset, clean, checkout-overwrite, or force push was
used. The only network mutation before implementation was `git fetch origin
main`. A stale local `main` reference was fast-forwarded because it was a
strict ancestor; the dirty working tree was not touched.

Before Round 20, the worktree contained 22 collapsed porcelain entries (70
entries with untracked directory contents expanded). That set included two
tracked user-owned result files and unrelated manuscript, old-build, result,
and Python-cache artifacts. Both tracked files and every unrelated untracked
artifact remain excluded from Round 20 staging. The protected tracked files
are:

- `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
- `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`

The isolated build directory is `build_round20/`; the fresh evidence package
is `results/gf_global_gini_tree_regression_round/`. Historical Round 19 values
are not eligible for fresh numerical tables.
