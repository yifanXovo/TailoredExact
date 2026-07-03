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
## Round 2 Scope Update

The current audited round is
`results/gf_compact_bc_strengthening_round2/`.

The paper-facing line remains `paper-gf-compact-bc`: Gini-frontier ledger plus
compact fixed-interval CPLEX MIP/BC certificates. Route-load BPC, route-mask
enumeration certificates, archive/known-UB imports, and plain CPLEX benchmark
bounds remain outside the paper-core certificate evidence.

Round 2 adds one-thread fairness auditing, true root LP cut probing for compact
interval BC, and model-size finalization for large diagnostics. The controlled
one-thread evidence certifies V12 M1, V12 M2, `high_imbalance_seed3202`, and
`tight_T_seed3101`; `moderate_seed3301` remains open.

## Time-Profile Round Update

`results/gf_compact_bc_timeprofile_round/` is the current time-profile package.
It treats 300s as a comparison budget, not a certification requirement. In this
round, `tight_T_seed3101` certifies at 300s and `high_imbalance_seed3202`
certifies in a controlled one-thread 1200s static compact-BC recovery row.
`moderate_seed3301` remains open with two unresolved leaves in the best
solver-final diagnostic row. Same-budget CPLEX rows are single-thread and
benchmark-only.

## Effectiveness Round Update

`results/gf_compact_bc_effectiveness_round/` separates attribution from
dominance. A certified row may be relaxation-only, relaxation plus Compact-BC,
or empty/out-of-range; relaxation-only closure is not a failure. Compact-BC
effectiveness is measured on leaves that relaxation/frontier does not close.

The round adds:

- `scripts/audit_certificate_sources.py`;
- `scripts/audit_timeprofile_finalization.py`;
- `scripts/audit_compact_bc_effectiveness.py`;
- selected-row de-duplication for conflicting time-profile artifacts;
- `best_valid_lb_seen` / `best_valid_gap_seen` checkpoint fields;
- diagnostic-only `--compact-bc-diagnostic-force-leaf-solve`.

Paper-core certificates still exclude BPC, archive scanning, known UB injection,
external incumbents, focus-only evidence, route-mask enumeration certificates,
and CPLEX benchmark bounds.

## Effectiveness Round 2 Scope

Compact-BC is evaluated as an unresolved-interval subsolver. Relaxation-only certificates remain valid framework successes; diagnostic activation and plain-MIP comparisons are not paper-core evidence.

## Effectiveness Round 3 Scope

Compact-BC is evaluated as an unresolved-interval subsolver. Relaxation-only certificates remain framework successes; forced activation, plain fixed-interval MIP comparisons, and generated diagnostics are evidence channels, not paper-core certificate imports.

## Low-Gini Round Scope

`results/gf_compact_bc_lowgini_round/` targets the low-Gini
`moderate_seed3301` leaves where prior tailored Compact-BC did not dominate
plain fixed-interval MIP at short budgets.  The paper-safe additions in this
round are:

- variable-S low-Gini centering:
  `(V-1)(r_max-r_min) <= V gamma_U sum_i r_i`;
- S*P McCormick objective estimator over valid interval bounds for
  `S=sum_i r_i` and `P=sum_i w_i e_i`.

S-range denominator bucket refinement is implemented as diagnostic
fixed-interval infrastructure only.  It must not be used as a full parent-leaf
certificate until the ledger proves exact S-bucket coverage and merges every
bucket.
