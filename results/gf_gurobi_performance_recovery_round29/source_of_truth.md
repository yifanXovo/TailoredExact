# Round 29 source of truth

- Repository: `yifanXovo/TailoredExact`
- Authoritative workspace: `E:\codes\ExactEBRP`
- Round 29 branch: `codex/round29-gurobi-performance-recovery`
- Starting local HEAD: `901510b1dd39edd5d093ffe27bf9fd4bebe6a702`
- Cached `origin/main` observed at start:
  `639c3772687d4a22e6b2cf3daa4d16c03d015ecd`
- Live GitHub `main` observed with `git ls-remote` at start:
  `1a92489cc3076aba49a6e42e54f8064076b4b887`
- Stable paper mainline: corrected CPLEX S0/F0, unchanged by Round 29.
- Frozen C2 reference: Round 27 `paper-lp-event`.
- Frozen C3 reference: Round 28 `cplex-algorithm-replica`.
- New arm: explicit `round29-bound-gain-incremental`, serialized as
  `C4-CANDIDATE`.

Pre-existing tracked and untracked workspace files are user-owned. Round 29
uses only `build_round29/` and
`results/gf_gurobi_performance_recovery_round29/` for new build/evidence
artifacts and does not modify Round 22–28 evidence.

The Gurobi license is supplied only in child-process environments. Its file
and contents are never opened, parsed, copied, hashed, printed, serialized, or
committed.
