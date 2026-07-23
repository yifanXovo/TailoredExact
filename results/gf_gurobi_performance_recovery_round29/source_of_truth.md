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

## Frozen implementation and observed outcome

- Implementation commit:
  `2a1d015c3f4dca5798b12eb1cfd8f933e0c3ec7f`
- Frozen protocol SHA-256:
  `9b4ef4a6c8ae8e3771e0b0cc2b8b8734ba45ee78144259ffdc5198e66403929c`
- Frozen CPLEX executable SHA-256:
  `5bc380b6ba63253309458b69226f86a159516eb30e2814ab32378b83f6335c99`
- Frozen Gurobi executable SHA-256:
  `ad8e8cb83a121c8aea1e97890c7aceb9d5d90e6c0cb5a60fd6d20260821b43b2`
- Official execution: 61/61 rows completed with zero process failures and
  zero emergency watchdog terminations.
- Final C4 classification: `exact_but_mixed`.
- Stable-mainline decision: corrected CPLEX S0/F0 remains unchanged.
- Final evidence package: 14,911 files, 1,691,235,630 bytes; all manifest
  hashes and all 5,613 compression-restoration records independently pass.
