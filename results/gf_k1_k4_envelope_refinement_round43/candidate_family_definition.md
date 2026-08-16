# Candidate family definition

`A(K0,d,rho)` starts from the existing complete strict-improver Gini range and
uses an equal-width exact cover with `K0` in `{1,4}`. At every active interval
the shared node operator completes the parent LP, completes every cell of the
fixed dyadic depth-`d` lookahead profile, constructs the greatest convex affine
minorant of the clipped descendant bounds, computes `D_d`, and either performs
one binary midpoint split when the frozen score is at least `rho` or solves the
envelope-strengthened parent MIP exactly.

Lookahead depth never directly creates active leaves. Completed bounds are
retained, midpoint-child records receive valid aggregate descendant bounds, and
every facet is tagged with its source interval and propagated only to nested
descendants. The complete objective expression is used for envelope rows:
`(1-beta) G + lambda * sum_i weight_i e_i >= alpha`.

The Stage 1 depth choices are 1 and 2. The threshold grid is fixed at
`{0.01,0.03,0.05,0.10}`; no more than two values may be frozen from structural
scores before exact candidate runtimes are observed.
