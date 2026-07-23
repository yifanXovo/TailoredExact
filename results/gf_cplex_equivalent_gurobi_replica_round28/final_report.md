# Round 28 final report

## Outcome

Classification: **paper_valid_but_performance_risky**. The stable mainline remains unchanged and
C3 is not automatically promoted. All 65 official rows
were expected; 65 were observed, 3 failed, 60
were time-limited, and 3 were excluded. Stage 0, static equivalence,
and dynamic C3 exactness passed respectively: True,
True, and True. Repeatability passed: True.

## Contract and implementation

The accepted S0 contract uses the complete improving range, recursive median
construction of four initial intervals, then unconditional midpoint binary
splits through adaptive depth 8 subject to minimum width 1e-4. Leaves are
selected by valid lower bound, smaller width, greater depth, lower endpoint,
upper endpoint, then deterministic ID. Children inherit the complete parent LP
bound; pruning uses valid infeasibility or lower bound versus the verified
cutoff; terminal leaves receive one exact MIP; the global certificate is the
minimum valid bound over complete non-replaced coverage.

C3 reproduces that paper algorithm with an external structural tree and a
fresh Gurobi model for each complete LP or terminal MIP event. It adds zero
outer-tree selector variables, registers all six global and nine interval-local
families, has no C2 child-benefit gate, splits every eligible non-pruned leaf
unconditionally, defers child LPs to ordinary best-bound selection, and has no
internal time, Work, node, solution, attempt, retry, or warm-start scheduling.
The remaining overall deadline is its only interruption limit. One native
Gurobi tree and equivalence of solver-internal trajectories are not required.

## Primary P-GRB versus C3 matrix

C3 won 12/16 completed final common-UB gaps and
9/16 completed bound-progress AUC
comparisons; one Moderate6301 pair is unavailable because C3 did not finalize.

- high_imbalance: 5/5 completed comparisons; C3 final-gap wins 4, AUC wins 3, median C3-minus-P gap -0.0778885.
- moderate: 4/5 completed comparisons; C3 final-gap wins 3, AUC wins 3, median C3-minus-P gap -0.0559743.
- tight_T: 5/5 completed comparisons; C3 final-gap wins 5, AUC wins 3, median C3-minus-P gap -0.0809179.
- v12: 2/2 completed comparisons; C3 final-gap wins 0, AUC wins 0, median C3-minus-P gap 0.100804.

Across the twelve V20 comparisons C3 won 11/12 final
common-gap endpoints and 9/12 AUC comparisons.

V12 certificate outcomes:

- V12_M1: P-GRB strict=True, gap 1.24325e-15; C3 strict=False, gap 0.113573.
- V12_M2: P-GRB strict=True, gap 0; C3 strict=False, gap 0.0880362.

V50 outcomes:

- high_imbalance_seed6202: P-GRB LB/UB 7.85742/10.0516; C3 status cplex_replica_external_gini_tree_time_limit, rc 0, LB/UB 7.48714/9.82066.
- moderate_seed6301: P-GRB LB/UB 0.43346/1.04213; C3 status missing, rc 124, LB/UB unavailable/unavailable.
- tight_T_seed6102: P-GRB LB/UB 0.511408/0.704346; C3 status cplex_replica_external_gini_tree_time_limit, rc 0, LB/UB 0.552812/0.685597.

C3 produced verified-UB/valid-LB progress on High6202 and Tight6102. The
Moderate6301 process completed the same 3,326-generation HGA trajectory in all
three attempts but did not finalize a result JSON before the runner emergency
margin, so it is failed/excluded rather than assigned a synthetic bound.

The detailed 34 rows and pairwise calculations are in
`stage2_all_instances_300s.csv`, `p_grb_vs_c3.csv`,
`bound_progress_auc.csv`, and `time_to_gap_thresholds.csv`.

## Five-anchor comparison

- V12_M1: C3-minus-C2 gap 0.113573, AUC -0.0684066; C3-minus-S0 gap 0.111473.
- V12_M2: C3-minus-C2 gap 0, AUC 0.00118736; C3-minus-S0 gap 0.072218.
- high_imbalance_seed3202: C3-minus-C2 gap 7.11792e-05, AUC 0.00599673; C3-minus-S0 gap 0.0403704.
- moderate_seed3302: C3-minus-C2 gap 0.000505127, AUC 0.00222652; C3-minus-S0 gap 0.0101696.
- tight_T_seed3101: C3-minus-C2 gap 0.281533, AUC -0.108883; C3-minus-S0 gap 0.15027.

S0/C2/C3 results preserve solver-internal execution differences while testing
the same paper-level geometry and certificate invariants. See
`stage3_anchor_comparison.csv`, `c2_vs_c3_anchor.csv`, and
`s0_cplex_vs_c3_anchor.csv`.

## Exactness and resources

The exact toy optimum and all four moderate4301 sentinel arms passed Stage 0;
no false infeasibility, invalid bound, or false certificate was accepted.
Across official C3 rows there were 5764 separate
optimizes, 5764 presolve executions,
1628 terminal root relaxations,
2646.97 LP Work, 10850.1
terminal-MIP Work, and 2366 structural splits.
Maximum C3 depth was 10 and maximum retained
peak memory was 0.566829 GB. Model and
environment creation/free symmetry is audited per row.

The two requested Stage 4 repetitions are deterministic within each instance:
True. Moderate3302 has full semantic identity with its Stage 2
baseline. The two V12_M2 repeats are identical to each other and retain the
same HGA, 58 splits, final LB, and certificate outcome as Stage 2, but the
earlier Stage 2 endpoint recorded one extra terminal decision and two extra
optimizes; this is a deadline-bound solver-event difference, not an algorithm
or certificate difference. All three Moderate6301 attempts have the same HGA
trajectory and the same rc=124 emergency-margin outcome without a result JSON,
so the failure is itself repeatable but provides no exact-tree endpoint.

Fresh-model startup evidence shows a median build/read share of
0.0712751 of exact-phase wall time. Future incremental
reoptimization is
true based on
the measured repeated-startup evidence; it was not implemented in Round 28.

Lossless packaging retained 4807 compressed artifacts and
verified every restoration byte count and hash: True. The
largest retained artifact is `results/gf_cplex_equivalent_gurobi_replica_round28/runs/stage3__tight_T_seed3101__s0_cplex__300s/global_node_trace.csv.gz` (6101829
bytes). The final package manifest is generated after this report.

The key distinction is that C3-REPLICA reproduces the accepted CPLEX paper
algorithm at the level of Gini decomposition, tailored strengthening, pruning,
terminal exact subproblems, and global certification. It does not reproduce
CPLEX's internal native branch-and-cut state or event sequence.

## Evaluation questions

1. The accepted CPLEX contract is identified unambiguously in
   `cplex_algorithm_contract.md` and the source/evidence matrix.
2. C3 matches the root range, recursive geometry, eligibility and terminal
   rules, row registries, pruning logic, inheritance, and global certificate.
3. C3 adds zero interval-selector variables.
4. The C2 child-LP-benefit split gate is absent from C3.
5. Every eligible non-pruned C3 interval splits unconditionally.
6. Child LPs are deferred ordinary best-bound leaves, not lookahead gates.
7. C3 contains no time-, Work-, node-, solution-, attempt-, or retry-based
   internal scheduling.
8. Only the overall experiment deadline can interrupt an LP or terminal MIP.
9. All six accepted global and nine interval-local families are registered.
10. Matched interval models are mathematically equivalent through the shared
    canonical F0 writer and interval-row factory; Stage 1 signatures pass.
11. P-GRB, S0, and C3 return the same exact toy optimum; the sentinel issues no
    false certificate.
12. No completed row contains false infeasibility, an invalid bound, or a false
    certificate; incomplete Moderate6301 rows are excluded.
13. C3 used 5764 separate Gurobi optimizes.
14. Repeated presolve/root work materially harms V12: P-GRB certifies both V12
    instances while C3 reaches neither strict certificate in 300 seconds.
15. C3 improves the final common gap on 11/12 V20
    instances, so tailored decomposition retains broad difficult-V20 value.
16. C3 makes valid V50 progress on two of three instances; Moderate6301 is a
    reproducible process-finalization failure.
17. C3 is near C2 on three anchors and regresses materially on V12_M1 and
    Tight3101, as quantified above.
18. C3 reproduces S0 at the paper-algorithm level while allowing different
    native node, cut, basis, and event trajectories.
19. The principal unresolved mechanisms are the reproducible Moderate6301
    finalization failure and repeated fresh-model optimize/presolve/root cost;
    weak endpoint progress also appears on V12 and Tight3101.
20. Future incremental reoptimization is justified by the measured 7.1%
    median build/read share, thousands of repeated presolves, and V12 evidence,
    but it was not implemented here.
