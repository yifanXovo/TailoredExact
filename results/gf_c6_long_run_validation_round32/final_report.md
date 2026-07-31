# Round 32 final report

## Outcome

Classification: `c6_long_run_same_solver_advantage_confirmed`.

Round 32 completed 133 of 133 frozen official,
limited-reference, contextual, and repeatability rows. It retained
44 valid time-limited rows, recorded
0 failed rows, 181
invalidations/reruns, and found 0 false
certificates. The frozen C6 mathematical decisions did not change. The two
telemetry-only source repairs were the verified-incumbent-aware trace
aggregate described in `v12_m2_trace_root_cause.md` and the monotonic
callback timestamp described in
`long_run_callback_timestamp_root_cause.md`.

## Same-solver comparison

At 1,800 seconds C6/P-GRB final-gap outcomes were
31/1/3 C6 wins/losses/ties across 35 pairs.
Observed common-window AUC outcomes were
30/5/0 over 35 compatible pairs. At 3,600 seconds
on the frozen V50 matrix, final-gap outcomes were
12/0/0; AUC outcomes were
11/1/0 over 12 compatible pairs.

The 1,800-second strict-certificate counts were
15 for C6 and
2 for P-GRB. The 3,600-second counts were
3 and
0. Certification times, fixed
common-gap times, Work, nodes, common-UB gaps, and pair-level AUC are retained
in the comparison and threshold CSVs.

## Mechanisms and references

Across the recorded tailored rows the audit observed
99 atomic splits,
282 child-lookahead pairs,
124 native-target rows,
106 requeues, and
85 exact-closure launches. A zero split
count, if observed, is evidence only for this tested range and is not a proof
that adaptive splitting is unnecessary.

Stage 4 contains 8 C5/C6 diagnostic pairs. Stage 5 contains
7 CPLEX S0 contextual comparisons. Neither changes the primary
same-solver conclusion. S0/F0-CPLEX remains the accepted stable CPLEX paper
mainline; C6 is evaluated as the tailored Gurobi mainline, and P-GRB remains
its primary same-solver benchmark.

## Evidence semantics

All AUCs use observed left-continuous steps on the common observed window:
no interpolation, endpoint-only pseudo-AUC, or post-final-event extension.
Historical Round 31 rows are isolated in
`historical_round31_reference.csv`. Time-limited valid endpoints are not
algorithm failures. Work-to-gap is reported only where synchronized native
work observations exist; unavailable C6 work trajectories are not
manufactured. No V>50 instance was generated or tested.

## Group and threshold results

At 1,800 seconds the V12 final gaps tied 2/2 and C6 certified both instances
faster: V12_M1 in 29.070 versus 35.891 seconds and V12_M2 in 121.484 versus
169.558 seconds. V20 outcomes were 19/1/1 in C6/P-GRB/ties with 19/2 AUC
wins; V50 outcomes were 12/0/0 with 11/1 AUC wins. At 3,600 seconds the V50
outcomes remained 12/0/0 with 11/1 AUC wins.

The 1,800-second family final-gap results were high-imbalance 10/0/1,
moderate 10/1/0, tight-T 11/0/0, and V12 0/0/2. The corresponding AUC
results were 9/2/0, 10/1/0, 11/0/0, and 0/2/0. At 3,600 seconds every
high-imbalance, moderate, and tight-T family was 4/0/0 in final gap; AUC was
3/1/0, 4/0/0, and 4/0/0.

At 1,800 seconds M2 was 5/0/2, M3 was 20/1/0, and M4 was 6/0/0 in final
gap; their AUC outcomes were 4/3/0, 20/1/0, and 6/0/0. At 3,600 seconds
M2/M3/M4 final-gap outcomes were 3/0/0, 6/0/0, and 3/0/0, with AUC outcomes
2/1/0, 6/0/0, and 3/0/0.

Observed time-to-gap performance profiles favor P-GRB at the loose 50%
threshold (28 versus 6 fastest observations), then C6 at 25% (18 versus
13), 20% (20 versus 8), 10% (21 versus 2), 5% (19 versus 2), 2% (15 versus
1), and each of 1%, 0.5%, and 0.1% (15 versus 0). Unreached thresholds are
treated as infinite and no interpolation is used.

## Reference arms, mechanisms, and resources

Against C5 on the eight-row diagnostic subset, C6 had 4/1/3 final-gap and
7/1/0 AUC outcomes. Three pairs certified in both arms; C6 certified faster
on V12_M2 and the new V20/M2 case, while C5 was faster on
high_imbalance_seed3202. Against the seven S0 contextual anchors, C6 had
5/0/2 final-gap outcomes and three one-sided certificates. These
cross/reference-arm results do not replace the primary same-solver
comparison.

The 99 atomic splits occurred in 23 runs. Sixty-one produced an immediate
positive global-LB change and 38 were neutral; none decreased the bound.
The median immediate gain was 9.0966e-5 and the maximum was 0.0307669.
Seventy-one split descendant sets closed, but no counterfactual runtime
claim is made. LP-cutoff pruning remained zero.

Across 63 official C6 rows, terminal native Work summed to 185267.6121 and
total native Work to 226836.7433; all 63 lifecycle audits passed. Peak
recorded C6 native memory was 1.404585189 GB. Plain-Gurobi Work is retained
in pair tables, but its peak-memory field was unavailable and is not
manufactured.

All eight C6 repeatability rows reproduced HGA, target, and split sequences,
verified UBs, certificate states, and lifecycle validity exactly. Seven
deadline/final LBs were exact; the remaining time-limited tight-T row
differed by 0.0003370340 under acceptable timing variation.

## Evidence package

The package contains 10230 files excluding its self-manifest, totaling 1634122705 bytes. The largest retained artifact is `results/gf_c6_long_run_validation_round32/invalidated_rows/stage5__moderate_seed3302__s0_cplex__1800s__invalidated001/global_node_trace.csv.gz` (10682601 bytes). 2085 large artifacts were compressed losslessly and every restoration hash was verified.
