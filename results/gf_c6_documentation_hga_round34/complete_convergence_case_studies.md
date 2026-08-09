# Round 34 complete-convergence case studies

All cases and commands were predeclared before these official solves.  Times
are process-entry wall times and include every applicable startup, model,
search, verification, and serialization phase.  Bounds are original-problem
valid.  Proof AUC uses a left-continuous observed trace, with no interpolation
and no extension beyond the last observation.

## Strict convergence

| Instance | Arm | Strict | Process s | Objective | Work | Nodes | Normalized proof-gap AUC |
|---|---|---|---|---|---|---|---|
| V12_M2 | C6-HGA-FULL | True | 122.994 | 0.719 | 219.713 | 2107.000 | 0.086 |
| V12_M2 | P-GRB | True | 171.944 | 0.719 | 282.097 | 85427.000 | 0.045 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | C6-HGA-FULL | True | 10.721 | 4.357 | 4.853 | 3.000 | 0.195 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | P-GRB | True | 325.920 | 4.357 | 603.643 | 26003.000 | 0.090 |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | C6-HGA-FULL | True | 76.811 | 1.006 | 140.866 | 8964.000 | 0.134 |
| round33_v10_high_imbalance_M3_Q30_seed1765289896 | P-GRB | True | 2529.931 | 1.006 | 3864.904 | 1408752.000 | 0.092 |

## Mechanism reading

The plot-ready `case_bound_trajectories.csv` records every observed valid
lower-bound event against the common final verified optimum.  The phase and
mechanism tables separate heuristic startup, construction, first LP, native
targets, child lookahead/splitting, and terminal work.  Runtime alone is not
used as a mechanism claim: the final interpretation cross-checks these ledgers.
The executable does not expose a standalone final-verifier timer; the phase
table therefore reports the auditable combined interval from the last observed
bound through verification/result retrieval/finalization, plus serialization
and startup-verifier timers separately, rather than inventing a finer split.

## V12_M2

Both arms strictly certified at objective 0.718504071.
P-GRB required 171.944 s; C6-HGA-FULL required
122.994 s (P-GRB/C6 ratio
1.40).
C6's first observed valid lower bound strictly above the left-current P-GRB
bound occurs at 9.610 process s.
C6's verified startup incumbent has relative gap
0.000000 to the final optimum; P-GRB
first records that final UB at
52.208 process s.  Because the
remaining certificate times are much longer than final-UB acquisition where
applicable, the dominant measured difference is proof progress, not merely
incumbent discovery.
C6 spent 6.832 s in HGA and
116.154 s after exact-phase entry.  Its ledger
records 3 next-frontier native phases,
0 child-bound target phases,
2 atomic splits, and
2 terminal MIP leaves.  P-GRB spends
171.913 s after native
optimize launch.  The observed bound trajectory and work decomposition
therefore attribute the difference to
the combined verified-incumbent cutoff, interval lower bounds, nonblocking
scheduling, adaptive splitting where active, and terminal closure—not to wall
time alone.

## round32_multi_m_high_imbalance_V20_M2_seed1052706459

Both arms strictly certified at objective 4.356924113.
P-GRB required 325.920 s; C6-HGA-FULL required
10.721 s (P-GRB/C6 ratio
30.40).
C6's first observed valid lower bound strictly above the left-current P-GRB
bound occurs at 7.697 process s.
C6's verified startup incumbent has relative gap
0.000000 to the final optimum; P-GRB
first records that final UB at
14.601 process s.  Because the
remaining certificate times are much longer than final-UB acquisition where
applicable, the dominant measured difference is proof progress, not merely
incumbent discovery.
C6 spent 6.889 s in HGA and
3.822 s after exact-phase entry.  Its ledger
records 3 next-frontier native phases,
0 child-bound target phases,
3 atomic splits, and
1 terminal MIP leaves.  P-GRB spends
325.870 s after native
optimize launch.  The observed bound trajectory and work decomposition
therefore attribute the difference to
the combined verified-incumbent cutoff, interval lower bounds, nonblocking
scheduling, adaptive splitting where active, and terminal closure—not to wall
time alone.

## round33_v10_high_imbalance_M3_Q30_seed1765289896

Both arms strictly certified at objective 1.005915740.
P-GRB required 2529.931 s; C6-HGA-FULL required
76.811 s (P-GRB/C6 ratio
32.94).
C6's first observed valid lower bound strictly above the left-current P-GRB
bound occurs at 2.237 process s.
C6's verified startup incumbent has relative gap
0.000000 to the final optimum; P-GRB
first records that final UB at
77.952 process s.  Because the
remaining certificate times are much longer than final-UB acquisition where
applicable, the dominant measured difference is proof progress, not merely
incumbent discovery.
C6 spent 1.971 s in HGA and
74.835 s after exact-phase entry.  Its ledger
records 3 next-frontier native phases,
0 child-bound target phases,
1 atomic splits, and
1 terminal MIP leaves.  P-GRB spends
2529.900 s after native
optimize launch.  The observed bound trajectory and work decomposition
therefore attribute the difference to
the combined verified-incumbent cutoff, interval lower bounds, nonblocking
scheduling, adaptive splitting where active, and terminal closure—not to wall
time alone.

