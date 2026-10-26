# What the isolated VD-P relaxation can and cannot strengthen

This is an algebraic attribution note, not a new experiment or a change to the
frozen candidate. For a single station on integer domain L,...,U and G in[a,b],
VD-P with relaxed selectors is the convex hull of the segments

    (Y,G,Z)=(y,g,y*g), g in[a,b], y in{L,...,U}.

Indeed, for s_y>0 set g_y=q_y/s_y. The perspective bounds give g_y in[a,b],
and the reconstruction equations express (Y,G,Z) as the convex combination
of those points. Conversely any such combination defines feasible s and q.
Every intermediate-y segment lies in the hull of the L and U segments, using
the same g and weights (U-y)/(U-L), (y-L)/(U-L). Consequently the projection
is just the bilinear rectangle hull with its four McCormick inequalities:

    Z >= L*G + a*Y - L*a
    Z >= U*G + b*Y - U*b
    Z <= U*G + a*Y - U*a
    Z <= L*G + b*Y - L*b.

For L=U this reduces to Y=L,Z=L*G. LOG's relaxed code coordinates do not change
this projection. Intermediate states matter to the chosen integer formulation
and native branching, even though they add no isolated continuous hull beyond
the two endpoint segments. The statement projects out the encoding variables;
it does not assert that retaining Y integrality with these four rows alone
enforces the nonconvex equality Z=G*Y.

This explains why root agreement and reduced binary count cannot determine
the final search cost. It also separates product-hull strength from VD-J's
additional penalty-state equality, which is absent in this stage. General
convex-hull/disjunctive and McCormick principles are established mathematics,
not a new theoretical contribution here. No unmeasured MC4 runtime claim or
new component combination is inferred from this derivation.

Historical source checked at publisher abstract/bibliographic level on
2026-09-15: G. P. McCormick, [Computability of global solutions to factorable
nonconvex programs: Part I — Convex underestimating problems](https://link.springer.com/article/10.1007/BF01580665),
Mathematical Programming10,147–175(1976). The page confirms the original work
on convex underestimators; full-paper access was not obtained. The exact
special-case projection claim above is derived explicitly here rather than
attributed to an unread theorem in that paper.
