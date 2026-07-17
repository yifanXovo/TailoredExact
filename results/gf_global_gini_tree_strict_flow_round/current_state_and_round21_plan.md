# Round 21 current state and plan

Audit date: 2026-07-16 (Asia/Shanghai).

The live GitHub `main`, fetched `origin/main`, and Round 21 branch base are all
`239d82772161acf7b86353fcfc8b7c3fc9f39e1f`, the merge of Round 20 PR #66.
Round 20 implementation commit
`421b3cb4be0e7dbee751b9feaa65be43b7267168` is its direct parent, and the two
tracked trees are identical. Only `main` was fetched. No clone, pull, rebase,
reset, clean, force push, or unrelated-file overwrite was used.

The branch is `codex/round21-strict-certificate-normalized-flow`. The isolated
build directory is `build_round21/`; the fresh evidence package is
`results/gf_global_gini_tree_strict_flow_round/`. Round 20 raw rows are
historical inputs only and cannot enter fresh Round 21 numerical tables.

The pre-existing dirty worktree is preserved. In particular, the two tracked
Round 10/legacy time-profile result files remain outside Round 21 staging, as
do manuscript auxiliaries, `build_round18/`, older result packages, and Python
caches. The protected tracked paths are:

- `results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv`
- `results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json`

Work proceeds in evidence order:

1. installed CPLEX 22.1.1 status/gap/API audit and historical reclassification;
2. one shared strict-certificate policy for Tailored and plain CPLEX;
3. formal F0/F1/F2/F3 projection and dominance proofs;
4. same-binary implementation with raw native fields and parameter round-trip;
5. deterministic C++/Python, lifecycle, source, and small-route gates;
6. diagnostic-only root-flow degeneracy min/max solves;
7. matched 300-second F0--F3 causal ablation;
8. fresh eight-instance 900-second F0/selected/plain matrix;
9. five-instance continuous 1,800-second F0/selected/plain trends;
10. conditional 3,600-second rows only when the 1,800-second evidence is near
    closure or ambiguous, with finalization reserve inside the process budget;
11. fail-closed promotion decision, compression, intentional commit, normal
    push, and three-way SHA verification.

GitHub CLI is not installed. No pull request was requested; publication will
therefore use local Git and a normal non-force push, with `git ls-remote`
verification.

## Execution outcome

The plan completed through the conditional Stage 4 gate using frozen executable
SHA-256
`dfd67bcf4e4dd19cf7096bf5fa16c100d5a6ccefd3bb6df8a30547de39f7136a`.
All 80 official rows validate: 10 Stage 0, 25 Stage 1, 24 Stage 2, 15 Stage 3,
and 6 conditional Stage 4 rows. F3 (`normalized-start-coupled`) was selected
from Stage 1 only. It recovers `moderate_seed3301` and remains much stronger
than plain CPLEX on the V20 cases, but it loses to F0 on multiple controls and
does not satisfy the fresh V12 strict-certificate gate. It therefore remains
optional/research-only rather than becoming the default. Detailed causal and
certificate conclusions are in `final_report.md` and the two root-cause
documents.
