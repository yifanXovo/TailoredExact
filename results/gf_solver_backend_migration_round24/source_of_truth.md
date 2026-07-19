# Round 24 source of truth

The existing local checkout is authoritative. No pull, merge, rebase, reset, restore, checkout-path, clean, stash, repository synchronization, re-clone, or force push is permitted or used.

## Repository provenance captured before editing

| Field | Value |
|---|---|
| Initial local branch | `codex/round23-moderate4301-correctness-unified-convergence` |
| Local branch base / initial HEAD | `a977efe52a79877c057ce8e3421901979d16f1be` |
| Round 24 branch | `codex/round24-gurobi-baseline-external-tree` |
| Observed `origin/main` | `f115e9bb600f68e5368df78f06203331a800a33b` |
| Merge base | `a977efe52a79877c057ce8e3421901979d16f1be` |
| Local source-tree object | `625acf423cae776c31b40c5d283f47da0b6c9c7b` |
| Remote source-tree object | `625acf423cae776c31b40c5d283f47da0b6c9c7b` |
| Ahead/behind (local/remote) | `0/2` |
| Local-only commits | none |
| Remote-only commits | `f115e9bb` and `91ed0e31`, both history-only merges |
| Integration conclusion | different commit history, identical source tree |

The only permitted inspection fetch was `git fetch --no-tags origin main`. It was not followed by an integration operation.

## Pre-existing user-owned working-tree state

No staged modification existed. The content-different tracked files were:

- `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
- `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`

`results/gf_compact_bc_round/handling_convention_test/handling_convention.json` appeared modified in short status because of line-ending/stat behavior, but did not appear in `git diff --name-status`; it is still treated as user-owned. The pre-existing untracked set includes manuscript build by-products, earlier isolated build directories, retained diagnostic results, manual results, and Python bytecode. None belongs to Round 24 and none may be staged.

## Frozen stable algorithm

The paper mainline remains corrected CPLEX `S0-SAFE`: F0, parent-copy, full inherited row pack, deferred child-local rows, no native MIP start, one environment/problem/model-read/`CPXmipopt`, one thread, presolve off, Reduce 0, Linear 0, traditional best-bound search, exact-zero gap settings, and fail-closed certificate semantics. P1, P2, and F3 remain off.
