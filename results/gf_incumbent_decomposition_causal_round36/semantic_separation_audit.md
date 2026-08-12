# Round 36 semantic separation audit

- Semantic invariants: 19/
  19 passed.
- `verified_ub` assignments: 4/
  4 originate from the verified seed or are
  guarded by independent incumbent verification.
- Decomposition-anchor symbol occurrences: 9.
- Forbidden anchor consumers: 0.
- Hardware-dependent split-decision tokens: 0.
- Per-leaf/per-action native time-slice tokens: 0.

The audit anchors each claim to normalized source fragments and source hashes.
`U_anchor` is confined to launch-frozen grid construction, safety/telemetry,
and the explicit split-normalization intervention. Cutoff, pruning, global UB,
native incumbent updates, final route verification, and strict certification
continue to use the independently verified proof incumbent.
