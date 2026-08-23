# Mathematical mechanism note

Round 43 implements one node operator A(K0,d,rho). K0 changes only the equal
initial partition of the complete strict-improver Gini range. Every active
interval then completes its parent LP, completes all 2^d dyadic lookahead LPs,
constructs the frozen greatest-convex-minorant affine objective-Gini envelope,
and evaluates the same globally fixed score.

For each accepted facet `(alpha,beta)`, the native row is
`(1-beta) G + lambda sum_i w_i e_i >= alpha`. Facets are interval-local and
inherited only by nested descendants. The executable-normalized
residual-volume score is
`D_R43=V_residual/(|I|*max(U-L_I,epsilon_cert))`. The separately useful profile
fraction is `P_profile=V_residual/max(V_local,epsilon_volume)=1-tau_d` when
`V_local` is positive; it is not the Round 43 decision score. A node splits at
its midpoint exactly when `D_R43 >= rho`; otherwise the strengthened parent MIP
is solved to a protocol terminal condition. Descendant LP bounds and
infeasibility proofs remain valid lower-bound information, while an incumbent
is never treated as a lower bound.

The contraction candidate C_d is mathematically rejected for decision use: the
chosen normalization makes it identically `1-2^-d`, observed as 0.5 and 0.75.
Timing, Work, nodes, iterations, memory, hardware, instance identity, and
historical outcomes are absent from the deterministic decision functions and
their hashes.
