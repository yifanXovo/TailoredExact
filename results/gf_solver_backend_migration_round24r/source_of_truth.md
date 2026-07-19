# Round 24R source of truth

- Authoritative checkout: `E:/codes/ExactEBRP`
- Starting local branch: `codex/round24-gurobi-baseline-external-tree`
- Starting local HEAD and merge base: `aa726494a2074adbb84ca65f31f3fe0ee0e9a31f`
- Round 24R branch: `codex/round24r-licensed-gurobi-qualification`
- Observed `origin/main`: `5166ecc910da7cebca7e0f1c7f48172302d8b62c`
- Relationship at start: remote main had three history-only commits; local and remote source trees were identical (`39210368d199ddffacf8757c3d133de88afb01eb`). No remote change was integrated.
- Build roots: `build_round24r/no_gurobi`, `build_round24r/with_gurobi_clean`, and the qualification build `build_round24r/mingw`.
- Evidence root: `results/gf_solver_backend_migration_round24r`.

Pre-existing tracked modifications in the Round 18/compact-BC evidence area and all pre-existing untracked build, manuscript, manual-result, and cache files are user-owned. They are excluded from this round's commit. Round 22--24 official evidence is immutable and is not reused as candidate Round 24R output.

The stable paper mainline remains corrected CPLEX S0/F0: one persistent native global-Gini tree, parent-copy estimates, full inherited rows, deferred child-local rows, one thread, presolve/Reduce/Linear off, exact-zero gap settings, no native MIP start, and P1/P2/F3 off. Round 24R is a qualification round and cannot promote Gurobi or an external tree to stable mainline.
