# Mathematical mechanism

Round 44 separates the corrected descriptive `D_R43(I)` and `P_profile(I)`
scores from the actual repair, which uses valid affine Gini-envelope facets.
The development-leading path starts from a complete K4 interval cover, injects
all facets at parent scope, and uses the exact next-distinct frontier bound as a
fixed depth-1 lookahead target. Its refinement family is `no-adaptive`.
It passed development but not sealed validation, and the pre-frozen C6-veto
fallback also failed validation; therefore neither mechanism is promoted.
