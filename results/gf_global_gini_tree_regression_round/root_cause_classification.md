# Round 20 root-cause classification

## Classification

The Round 19 regression is mixed, with one dominant formulation defect and
three amplifiers:

1. **Dominant: missing scalable root connectivity-flow strength.** The legacy
   V20 interval model has 3,033 variables, 24,250 rows and 215,457 nonzeros;
   the compact fixed-interval/global child has about 2,124 variables, 10,616
   rows and 62,010 nonzeros. The legacy `fcb` single-commodity connectivity
   flow (1,260 continuous variables at V20/M3) was absent. Other legacy-only
   route-mask/pool families are non-unified and were excluded. The proved
   O(MV^2) root-flow projection is the only migrated family.
2. **Major amplifier: equal sibling estimates and native queue ordering.** In
   every fresh 300-second Round 19 baseline, all created sibling pairs had
   equal estimates. Mean sibling delay was 12.59 seconds on `tight_T_seed3101`
   and 11.82 seconds on `high_imbalance_seed3202`; maxima were 163.73 and
   165.30 seconds. The selected high-imbalance child was never processed in the
   baseline window, so its useful interval rows could not influence the bound.
3. **Secondary: deferred child rows.** Explicit state now distinguishes the
   pre-row callback from the separately reoptimized post-row relaxation.
   Observed mean lifts were 0.000281 on tight3101, 0.004329 on high3202,
   0.000720 on moderate3302 and 0.000522 on V12_M2. There were no failures;
   only children still open and unprocessed at timeout lacked observations.
   Eager presolve-on/off gates passed, but 60-second evidence did not show a
   consistent performance gain, so timing is not the primary explanation.
4. **Engineering amplifier: inherited-state duplication.** Baseline rows and
   native tree memory reached 165,831/764.87 MB on tight3101 and
   224,518/531.66 MB on moderate3302. Exact delta omitted 60,840--110,190
   cumulative exact duplicates in the four Stage 1 cases and roughly halved
   row-API time, but its lower-bound effect was mixed. Immutable shared state
   fixed the metadata OOM without changing the model.

Native-incumbent absence is not a root cause. Complete verified MIP starts were
submitted in all six gates, but CPLEX reported acceptance in only three and no
consistent short-run dual improvement. The incumbent cutoff was present in
all compared compact models.

## Answers to the required causal questions

1. `tight_T_seed3101` certifies through short standalone partitions because
   each exact interval receives its own model root, presolve and native cuts.
   In the global tree the compact relaxation lacks legacy connectivity flow,
   all sibling estimates tie, and useful interval work waits behind thousands
   of ordinary nodes. At 300 seconds it had 69 Gini branches, 8,611 ordinary
   branches, 7,043 open nodes and LB 0.017086 versus UB 0.107253.
2. `high_imbalance_seed3202` has the same mechanism more starkly: targeted
   legacy intervals become infeasible quickly, but the corresponding high
   global child was never selected in 300 seconds. Its 69 sibling pairs all
   tied; the baseline LB was 1.612076 versus UB 1.749313.
3. No. The compact root contains scalable route/operation variables and all
   required compact static families, but it is not the legacy extended
   interval formulation. `fcb` connectivity flow was absent; non-unified
   route-mask/pool families remain diagnostic-only.
4. Representative pre/post reoptimized child relaxations were
   0.00773785/0.00793315 (tight3101), 0.60648049/0.61732314 (V12_M2), and
   0.12494329/0.13207560 (moderate3302). The selected high3202 child was not
   processed, which is direct queue-starvation evidence.
5. Deferred rows do forgo interval-specific presolve/root-cut exposure and
   cause one reoptimization, but every observable post-row lift was valid and
   eager evidence was inconsistent. It is a secondary cost, not the isolated
   regression cause.
6. All baseline sibling pairs tied: 69/69 tight3101, 69/69 high3202,
   116/116 moderate3302, 146/146 V12_M2, 233/233 V12_M1 and 43/43 tight3102.
7. Factory-domain was usually dominated by the parent relaxation. It
   discriminated 9/121 tight3101 pairs, 1 V12_M2 pair, and none on high3202 or
   moderate3302.
8. The limited discrimination changed order on tight3101 but produced only a
   small 300-second LB change (0.017086 to 0.017391); high3202 and moderate3302
   were effectively identical. It does not solve the queue problem.
9. Exact delta avoided 60,840 high3202, 110,190 moderate3302, 97,771 tight3101
   and 89,305 V12_M2 cumulative duplicate rows. Dominance omission remained
   zero.
10. Delta reduced row-API time from 0.0516 to 0.0241 seconds on high3202,
    0.0751 to 0.0490 on moderate3302, 0.0467 to 0.0283 on tight3101 and
    0.0434 to 0.0253 on V12_M2. Open-node and LB effects were mixed, so delta
    is an engineering fix rather than a promoted performance mechanism.
11. Yes. The instrumented ordinary-branch count before terminal Gini
    refinement was zero on all six forensic runs; useful ordinary branching
    began only after terminal refinement.
12. No consistent effect was observed. The native verified start was accepted
    on moderate3302, V12_M1 and tight3102, and not reported accepted on
    tight3101, high3202 or V12_M2.
13. Both regressions are primarily missing formulation strength plus equal-
    estimate queue ordering. Deferred timing and row duplication amplify cost;
    native-incumbent absence does not explain the dual regression.
14. Yes. At 900 seconds both baseline and root flow certified V12_M1 at
    0.357200583208 and V12_M2 at 0.718504070755, with verifier pass.
15. Mostly. Root flow improved the 900-second LB on five of six V20 seeds,
    including both high-imbalance seeds and both tight-T seeds, but regressed
    on `moderate_seed3301` (0.0465584 to 0.0449719).
16. Yes for the four measured 1,800-second pairs. Selected gaps versus plain
    were 58.64%/85.04% (tight3101), 0.99%/31.93% (high3202),
    25.47%/43.60% (moderate3302), and 7.53%/20.21% (tight3102). None reached
    gap zero, so no certification time is extrapolated.
17. **One further optimization round; do not promote root flow as the default
    yet.** Exactness, certificate preservation and long-run trend gates pass,
    but Stage 2 broad non-regression fails on moderate3301. A held-out random
    suite is also required before any stable-superiority claim.

The detailed source rows are `forensic_model_diff.csv`,
`forensic_interval_bound_comparison.csv`,
`post_local_row_reoptimization_audit.csv`, `gini_sibling_delay_audit.csv`, and
`tree_memory_and_row_growth.csv`.
