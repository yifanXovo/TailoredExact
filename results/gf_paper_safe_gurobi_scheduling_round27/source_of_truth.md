# Round 27 source of truth

- Authoritative checkout: `E:\codes\ExactEBRP`
- Branch: `codex/round27-paper-safe-gurobi-scheduling`
- Local source base: `372d2ad7dda5a0b80593f25b087ed7fee9b79bbc`
- `origin/main` observed when the Round 27 goal began: `3adffe8237101add1671ad84454d6bfde6968122`
- `origin/main` observed again before implementation: `639c3772687d4a22e6b2cf3daa4d16c03d015ecd`
- C0 is the immutable Round 26 executable at
  `build_round26/with_gurobi/ExactEBRP.exe`, SHA-256
  `002ab0f3f3fc1f80bb4b8a6eb10fddaaf013f5c493317884c977098ede0cc15c`.
- C2 is built only from the Round 27 implementation commit in
  `build_round27/with_gurobi/`; its final commit and executable hash are
  recorded in `c2_paper_manifest.json` before solver runs.
- The existing Gurobi license is exposed only as `GRB_LICENSE_FILE` in each
  child-process environment. Its file is never opened, copied, hashed,
  printed, or serialized.
- All pre-existing tracked, staged, unstaged, and untracked user paths are
  preserved and excluded from Round 27 commits.
- Round 22--26 evidence is immutable historical context. No earlier result is
  rewritten or reclassified.
