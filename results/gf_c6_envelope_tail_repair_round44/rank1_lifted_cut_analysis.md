# Round 44 rank-1 lifted-cut ablation

The mandatory pilot evaluated `noadaptive, veto-f05` on the major
fragmentation witness and strongest K4 positive control, with lifted separation
off and on. The on arm solved a normalized full-matrix CGLP at every encountered
parent and independently replayed both multiplier identities, RHS inequalities,
nonnegativity, and the finite normalization.

- Audited parent CGLPs: 13
- Valid multiplier audits: 13
- Violated valid rank-1 cuts: 0
- Mechanism-6 lifted extension: not triggered

This is a genuine no-cut result when the generated-cut count is zero. The `on`
trajectory is then mathematically identical to `off`; its reported time and Work
include the measured separator overhead.
