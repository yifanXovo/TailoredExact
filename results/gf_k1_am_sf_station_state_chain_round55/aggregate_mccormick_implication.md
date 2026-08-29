# Aggregate McCormick implication audit

For (G\in[\ell,u]), (Y_i\in[L_i,U_i]), and the unscaled product
(Z_i=GY_i), MC4 is the standard four-row McCormick envelope over that box.
Every row is valid for the original integer model.

F0-CLEAN instead applies an interval-tight binary-product hull independently
to each (p_{ib}=G b_{ib}), then reconstructs (Y_i) and (Z_i) with powers
of two.  Summing the bit inequalities produces bounds based on zero and on the
full representable binary weight (W_i=2^{k_i}-1).  When the propagated box
has (L_i>0), (U_i<W_i), or fractional mass is distributed among bits, those
sums do not in general reproduce the four facets using the tighter aggregate
endpoints (L_i,U_i).  The station bound (L_i\le Y_i\le U_i) does not couple
that fractional bit mass to (G) strongly enough to complete the implication.

The official census therefore tests the distinction rather than assuming
redundancy.  The preliminary engineering-only D1 smoke (excluded from all
selection statistics) already exhibited an F0 root value of
0.0209774956 and an MC4 value of 0.0281003490.  The official all-state census
is the controlling evidence.  A strict objective increase on any feasible
root LP proves that F0 does not imply MC4; equality elsewhere does not undo
that counterexample.

No empirical parameter is introduced.  SF-MC4 is exactly F0-CLEAN plus four
interval-local valid rows per station.
