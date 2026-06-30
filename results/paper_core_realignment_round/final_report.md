# Paper Core Realignment Round Final Report

Branch: `codex/longrun-round17-local-results`

Final commit SHA: recorded in the final response after commit creation.

## Algorithm Realignment

The paper-core algorithm is now `paper-gf-bpc-core`:

1. native HGA-TGBC UB, verifier-gated and UB-only;
2. full improving-Gini frontier decomposition;
3. valid non-enumerative relaxation lower-bound screening;
4. route-load BPC tree on unresolved intervals;
5. exact pricing closure required for every BPC lower-bound certificate.

The core preset disables:

- archive scanning;
- known-UB or external incumbent injection;
- complete all-subset route-mask enumeration as certificate evidence;
- compact interval-oracle certificates;
- CPLEX benchmark bounds as exact-pipeline evidence.

The auxiliary exact portfolio remains separate from the paper core.

## Unified Core Results

See `unified_core_summary.csv`.

| Instance | Status | Certified | LB | UB | Gap | Relaxation | BPC | Oracle |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V12 M1 regenerated | not closed | false | 0.348563141040 | 0.357200583208 | 0.0241809296353 | 6 | 0 | 0 |
| V12 M2 regenerated | not closed | false | 0.698792929290 | 0.718504070755 | 0.0274335835624 | 5 | 0 | 0 |
| high_imbalance_seed3202 | not closed | false | 1.06421478404 | 1.74931345205 | 0.391638598107 | 6 | 0 | 0 |
| tight_T_seed3101 | optimal | true | 0.107252734134 | 0.107252734134 | 0 | 4 | 0 | 0 |
| moderate_seed3301 | not closed | false | 0.0122881381662 | 0.0491525526647 | 0.75 | 2 | 0 | 0 |

The realigned core certifies only `tight_T_seed3101` under the tested budgets.
Previously certified V12 and V20 rows that depended on route-mask/oracle
portfolio evidence are not counted as BPC-core certificates.

## Closure Source Accounting

Implemented and audited fields:

- `interval_closure_source`;
- `intervals_closed_by_relaxation_count`;
- `intervals_closed_by_bpc_count`;
- `intervals_closed_by_oracle_count`;
- `certificate_uses_interval_oracle`;
- `bpc_core_certificate_valid`;
- `exact_portfolio_certificate_valid`.

`paper-gf-bpc-core` optimal rows fail audit if any interval oracle evidence is
used as certificate evidence.

## BPC Validation

See:

- `bpc_leaf_validation_summary.csv`;
- `bpc_pricing_profile.csv`;
- `docs/bpc_leaf_validation_report.md`;
- `docs/bpc_improvement_attempt.md`.

BPC diagnostic leaf runs start the tree and call pricing, but no nontrivial leaf
closed in this round.

Observed bottleneck:

- V12 M2 leaf baseline: pricing consumed the 120s budget, left negative reduced
  cost, and did not close.
- After BPC seeding/pruning/branching improvements, the same V12 leaf generated
  far more columns but still did not close.
- V20 moderate/high-imbalance leaves generated thousands to hundreds of
  thousands of columns and still lacked exact pricing closure.

Conclusion: BPC remains theoretically valid but empirically not yet effective as
the primary fallback.  The next targeted round should focus on exact pricing
state reduction, stronger DP dominance, and leaf-domain transfer into pricing.

## Large-V Diagnostics

See `large_v_summary.csv`.

Short sealed diagnostics were produced for V50/M3 and V100/M5.  They are
noncertified and show no false certificate, no route-mask enumeration, and no
interval-oracle evidence.  The runs are stability probes only; they do not
support broad large-V benchmark claims yet.

The attempted 300s V50/V100 batch did not leave final JSONs; replacement 10s
sealed diagnostic rows were run and are listed in `skipped_or_interrupted_runs.csv`.

## CPLEX Comparison

See:

- `cplex_summary.csv`;
- `exact_vs_cplex_bound_quality.csv`;
- `docs/cplex_same_budget_comparison_realigned.md`.

CPLEX rows are benchmark-only.  Their LB/UB/gap values are not imported into
`paper-gf-bpc-core`.

## Audit

Completed:

- `audit_bpc_certificate.py --self-test`;
- certificate audit for `results/paper_core_realignment_round/raw`, failures 0;
- `certificate-basis-test`;
- `option-consistency-test`;
- no-instance-special-case audit;
- no-V-threshold paper-core audit;
- proof coverage audit.

## Answers

1. Is the paper-core algorithm unified across V/M?
   Yes.  The new core preset uses the same GF-BPC framework for all V/M and
   disables complete route-mask enumeration.

2. Was any V-threshold enumeration removed from paper-core?
   Yes.  `paper-gf-bpc-core` and legacy `paper-bpc-core` now mark route-mask
   all-subset enumeration noncertifying/disabled.

3. Which intervals closed by relaxation?
   See `closure_source_audit.csv`; the only certified core row in this round is
   closed by relaxation-bound intervals.

4. Which intervals closed by BPC exact tree?
   None in this round.

5. Did any paper-core certificate use interval oracle?
   No.  Audit would fail that condition.

6. Did BPC close any nontrivial leaf?
   No.

7. If BPC did not close, what is the bottleneck?
   Exact pricing/column-generation state growth before closure.

8. How do V50/V100 diagnostics behave?
   They produce honest noncertified final JSONs under the unified preset but do
   not make progress in short diagnostic budgets.

9. How does the realigned exact method compare with CPLEX?
   CPLEX remains benchmark-only.  The comparison table separates CPLEX LB/UB/gap
   from core exact evidence.

10. What should be claimed in the paper?
    Claim the unified GF-BPC certificate theorem and relaxation-only core
    certificates where they occur.  Report BPC as a valid but currently
    bottlenecked exact fallback.  Report interval-oracle results only as
    auxiliary exact-portfolio evidence.

## Recommendation

Do not start a broad paper benchmark matrix yet.  Run another targeted BPC/pricing
closure round focused on exact label dominance, pricing completion bounds,
operation-DP dominance, and better leaf-domain transfer into the pricing engine.
