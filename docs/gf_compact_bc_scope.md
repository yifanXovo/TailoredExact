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

## Strengthening Round Status

The 2026-07-02 strengthening round uses
`results/gf_compact_bc_strengthening_round/` and enforces one-thread fairness
for the controlled exact-vs-CPLEX comparison:

- plain CPLEX rows use `--cplex-threads 1`;
- compact interval BC rows use `--compact-bc-threads 1`;
- paper rows emit `solver_thread_policy` and `thread_fairness_class`.

The round keeps the paper-core evidence sources separated:

- `paper-gf-compact-bc` rows may use verified UB generation, relaxation bounds,
  valid compact interval BC bounds/infeasibility, and full-ledger aggregation;
- plain CPLEX rows are benchmark-only;
- BPC rows remain diagnostic and are not part of this preset;
- receiver-set source-cover is paper-safe only for the implemented singleton
  delivery lower-bound row. Pair/set receiver-cover variants remain diagnostic.

Under the controlled 300s one-thread suite, V12 M1, V12 M2, and
`tight_T_seed3101` certify.  The prior high-imbalance V20 certificate is not
reproduced by this short one-thread compact-BC run, so it is not counted as a
new fair-suite certificate in this round.  `moderate_seed3301` remains open but
retains a substantially better compact-BC bound than plain CPLEX under the same
thread/time policy.
