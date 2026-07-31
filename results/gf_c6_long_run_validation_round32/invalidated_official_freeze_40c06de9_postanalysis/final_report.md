# Round 32 final report

## Outcome

Classification: `c6_engineering_evidence_incomplete`.

Round 32 completed 133 of 133 frozen official,
limited-reference, contextual, and repeatability rows. It retained
44 valid time-limited rows, recorded
0 failed rows, 36
invalidations/reruns, and found 0 false
certificates. The frozen C6 mathematical decisions did not change; the only
source repair was the verified-incumbent-aware trace aggregate described in
`v12_m2_trace_root_cause.md`.

## Same-solver comparison

At 1,800 seconds C6/P-GRB final-gap outcomes were
31/1/3 C6 wins/losses/ties across 35 pairs.
Observed common-window AUC outcomes were
29/5/0 over 34 compatible pairs. At 3,600 seconds
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
280 child-lookahead pairs,
125 native-target rows,
108 requeues, and
86 exact-closure launches. A zero split
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
