# Round 28 source of truth

- Authoritative checkout: `E:\codes\ExactEBRP`.
- Branch: `codex/round28-cplex-equivalent-gurobi-replica`.
- Starting local HEAD: `c76192a9d6641a784888a82d3098187a962f7764`.
- Cached local `origin/main` at branch creation: `639c3772687d4a22e6b2cf3daa4d16c03d015ecd`.
- Live GitHub `main` observed at branch creation: `fbec14f2fc8c9f438ac5e224f5a9d060177677a5`.
- Corrected S0 option authority: `results/gf_global_gini_tree_round23/corrected_s0_manifest.json` and `stable_s0_reference_manifest.json`.
- Corrected S0 command authority: Round 23 official corrected-S0 command manifests, including `official/round23_stage2__V12_M2__s0c__900s/command.json`.
- P-GRB and prior external-Gurobi authority: accepted Round 25 and Round 27 protocols and frozen executables.
- Instance authority: `results/gf_solver_backend_validation_round25/round25_instance_manifest.csv`, `results/gf_external_gurobi_production_validation_round26/round26_heldout_v20_manifest.csv`, and `round26_v50_manifest.csv`.
- License policy: `GRB_LICENSE_FILE=E:\gurobi\gurobi.lic` is supplied only to licensed child processes. The file and its contents are never opened, parsed, copied, hashed, printed, serialized, or committed.
- Dirty-worktree policy: every pre-existing tracked, staged, unstaged, and untracked user path is preserved and excluded from Round 28 commits.
- Evidence policy: Round 22--27 evidence is immutable input. Round 28 writes only under its isolated build/results paths.

The local checkout is authoritative. Round 28 does not pull, merge, rebase,
reset, clean, restore, stash, force-push, modify `main`, or replace any frozen
historical arm.
