# Tailored BC Convergence And Exactness

The paper-facing line is `paper-gf-tailored-bc`: Gini-frontier decomposition, valid interval relaxation/frontier bounds, CPLEX-managed tailored fixed-interval branch-and-cut, and audited full-frontier ledger aggregation.

Cut admissibility follows [Diagnostic vs Paper-Safe Cuts](diagnostic_vs_paper_safe_cuts.md). Tailored-BC callback cuts may contribute paper-core evidence only when they are globally valid for the fixed interval or when a conditional split, such as the S-domain bucket ledger, is completely covered and audited.

S-domain bucket refinement is exact only as a ledger: child fixed-S buckets are solved independently, and the parent interval is closed only if the audited union of children covers the parent S-domain and every child is closed by valid evidence.
