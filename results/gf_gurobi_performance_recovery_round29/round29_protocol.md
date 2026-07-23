# Round 29 frozen protocol

Round 29 separates development from official evidence. The development set is
V12_M1, V12_M2, high_imbalance_seed3202, moderate_seed3302,
tight_T_seed3101, and moderate_seed6301. No more than the selected primary C4
prototype is used.

Official runs use one solver thread, Gurobi Seed 0, automatic/default Gurobi
presolve, zero relative and absolute MIP gaps, a 300-second process cap, and a
fixed five-second shutdown margin. The exact C4 arm is
`round29-bound-gain-incremental`; its local re-decode repair is explicitly and
uniformly disabled. C3 remains the frozen `cplex-algorithm-replica` reference
and retains its frozen algorithmic options while observing the repaired
process deadline.

Stage 1 runs C3 and C4 on six mechanism anchors. Stage 2 runs P-GRB, C3, and
C4 on all 17 authoritative non-toy instances. Stage 3 compares S0, C2, C3,
and C4 on five anchors. Stage 4 runs two C4 repeats on V12_M2,
moderate_seed3302, tight_T_seed3101, moderate_seed6301, and the preselected
additional V50 instance `high_imbalance_seed5202`.

No official result may change C4 source, geometry, threshold, command
construction, instance selection, or parameters. A general correctness bug
stops the matrix and requires uniform rebuilding and rerunning of affected
rows. Failed, interrupted, excluded, and invalid evidence is retained.

The corrected CPLEX S0/F0 remains the stable paper mainline. Round 29 evaluates
C4 as a distinct candidate and does not replace, retune, or redirect S0/F0.
