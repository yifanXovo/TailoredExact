# Current G-times-inventory semantics

The fixed-interval model contains one continuous Gini variable
\(G\in[\ell,u]\).  For station (i), the propagated integer final-inventory
domain is the complete interval
\(Y_i\in\{L_i,L_i+1,\ldots,U_i\}\), intersected with the original capacity and
reachability bounds.  The ratio and penalty variables satisfy

\[
r_i=Y_i/D_i,\qquad e_i\ge r_i-1,\qquad e_i\ge1-r_i,
\]

and the objective has coefficient \(\lambda w_i\) on (e_i\).  Therefore an
optimal solution uses (e_i=|Y_i/D_i-1|); VD-J makes this minimum explicit by
equality without removing either original absolute-value inequality.

The aggregate product is unscaled:

\[
Z_i=G Y_i.
\]

It appears in the direct Gini numerator/denominator linearization.  In
F0-CLEAN, (Y_i=\sum_b2^b b_{ib}),
\(Z_i=\sum_b2^b p_{ib}), and each (p_{ib}) represents (G b_{ib}) with the
current interval endpoints.  The explicit integer bound on (Y_i) excludes
binary codes above the propagated station domain; no such code can satisfy
both the bit reconstruction equality and the bound.

VD-P replaces only the bits used by this product and their product variables.
VD-J adds exact ratio and minimal-penalty state equalities.  Routing,
inventory conservation, visit links, and all nonobjective uses of the original
variables are retained.
