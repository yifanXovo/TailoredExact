# 06 Compact Interval BC Role

The legacy compact interval oracle is now reframed as the compact interval
branch-and-cut/cutoff subsolver for `paper-gf-compact-bc`.

In the compact-BC preset it may:

- prove fixed-interval infeasibility;
- provide valid original fixed-interval lower bounds;
- help diagnose tight leaves;
- certify full rows when all merge and coverage audits pass.

It must still not be counted as `paper-gf-bpc-core` certificate evidence.
Reports must separate `paper-gf-compact-bc`, BPC diagnostics, auxiliary
portfolio rows, and plain CPLEX benchmark rows.
