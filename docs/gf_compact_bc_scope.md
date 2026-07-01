# GF Compact BC Scope

`paper-gf-compact-bc` is the new paper-facing exact line.  It uses:

- native HGA-TGBC only as a verified upper-bound source;
- the full Gini-frontier ledger over the original improving Gini range;
- valid non-enumerative relaxation bounds for interval screening;
- compact fixed-Gini-interval MIP/branch-and-cut certificates solved by CPLEX;
- exact full-frontier ledger aggregation.

It does not use route-load BPC, archive incumbent scanning, known-UB injection,
focus-only certificates, imported focus bounds, route-mask all-subset
enumeration as certificate evidence, plain CPLEX benchmark rows, or unproved
aggressive cuts.

The legacy interval-oracle code path is retained, but in this preset it is the
compact interval BC subsolver.  Legacy `interval_oracle_*` fields remain for
backward compatibility; paper summaries should use `compact_interval_bc_*` and
`compact_bc_*` fields.

`paper-gf-bpc-core` remains available for BPC research.  It is not enabled by
default in `paper-gf-compact-bc`, and BPC can contribute to the new paper-core
certificate only if a future explicit mode proves exact pricing closure and the
result is classified outside the compact-BC preset.
