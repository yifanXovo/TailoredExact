# Round 30 source of truth

- Repository: `yifanXovo/TailoredExact`
- Authoritative workspace: `E:\codes\ExactEBRP`
- Branch: `codex/round30-c0-mechanism-transfer-c5`
- Starting local HEAD: `483272b4c4630835c32014171539740bd978207e`
- Cached `origin/main` at start:
  `639c3772687d4a22e6b2cf3daa4d16c03d015ecd`
- Live GitHub `main` at start:
  `51d3d74d178383f135820243a5627f115736f72f`
- Stable paper mainline: corrected CPLEX S0/F0, unchanged.
- Historical teacher: C0-LEGACY, exact but non-paper-compatible.
- Frozen references: C3-REPLICA and Round 29 C4-CANDIDATE.

All pre-existing workspace files are user-owned. Round 30 writes new build
artifacts only below `build_round30/` and new evidence only below
`results/gf_c0_mechanism_transfer_c5_round30/`. Historical Round 22--29
evidence is read-only.

The Gurobi license is exposed only in child-process environments. Its file and
contents are never opened, inspected, parsed, copied, hashed, printed,
serialized, or committed.
