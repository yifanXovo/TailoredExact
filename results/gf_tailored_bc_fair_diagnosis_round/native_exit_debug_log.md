# Native Exit Debug Log

## engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__300s

- Return code: `0` / `0x00000000`.
- Status: `interval_unresolved_timeout`.
- Final JSON present: `True`.
- Finalization source: `solver_final_json`.
- Last valid bound: `0.35108451463`.
- Last node count: `11712`.

### Solver Log Tail

```text
  10854  4399        0.4113   224                      0.3502  3518108         
  10930  4439    infeasible                            0.3504  3543773         
  11054  4512    infeasible                            0.3505  3567375         
  11121  4545    infeasible                            0.3506  3595295         
  11172  4568    infeasible                            0.3507  3615017         
  11262  4630        0.3698   206                      0.3508  3637457         
  11351  4682        0.3999   227                      0.3508  3664325         
  11442  4735        0.4008   264                      0.3509  3691972         
  11547  4790        0.4105   202                      0.3509  3716927         
  11637  4844    infeasible                            0.3510  3743478         
Elapsed time = 298.44 sec. (744463.40 ticks, tree = 8.59 MB, solutions = 0)
  11708  4885        0.4546   219                      0.3511  3767266         
Advanced basis not built.

GUB cover cuts applied:  13
Clique cuts applied:  1
Cover cuts applied:  37
Implied bound cuts applied:  41
Flow cuts applied:  30
Mixed integer rounding cuts applied:  206
Zero-half cuts applied:  30
Lift and project cuts applied:  9
Gomory fractional cuts applied:  9

Root node processing (before b&c):
  Real time             =    1.14 sec. (2617.96 ticks)
Sequential b&c:
  Real time             =  298.88 sec. (745809.03 ticks)
                          ------------
Total (root+branch&cut) =  300.02 sec. (748426.99 ticks)


MIP - Time limit exceeded, no integer solution.
Current MIP best bound =  3.5108451463e-01 (gap is infinite)
Solution time =  300.02 sec.  Iterations = 3767722  Nodes = 11712 (4886)
Deterministic time = 748426.99 ticks  (2494.62 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX> 
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 300 --interval-exact-cutoff-time-limit 300 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__300s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__300s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__300s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__300s.json --compact-bc-direct-gini-rows false --compact-bc-tight-mccormick false --compact-bc-inventory-conservation false --compact-bc-movement-reachability false --compact-bc-visit-inventory-linking false --compact-bc-objective-estimator-cutoff false --compact-bc-penalty-lb-closure false --compact-bc-gini-spread false --compact-bc-required-movement false --compact-bc-global-handling-capacity false --compact-bc-low-gini-centering false --compact-bc-support-duration false --compact-bc-transfer-compat false --compact-bc-receiver-source-cover off --compact-bc-variable-s-centering false --compact-bc-s-range-refinement off --compact-bc-sp-product-estimator off --tailored-bc-enabled false --tailored-bc-mode off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-support-duration-cover-mode off --compact-bc-root-cut-rounds 0

tight_T_seed3102.txt interval-cutoff-oracle interval_unresolved_timeout obj=0 runtime=300.16 columns=0
```

## engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__900s

- Return code: `0` / `0x00000000`.
- Status: `interval_unresolved_timeout`.
- Final JSON present: `True`.
- Finalization source: `solver_final_json`.
- Last valid bound: `0.36821327`.
- Last node count: `42650`.

### Solver Log Tail

```text
  41953 18959    infeasible                            0.3678 12736374         
  42005 18955    infeasible                            0.3679 12761640         
  42078 18976        0.4169   184                      0.3679 12782576         
  42166 19012    infeasible                            0.3679 12809717         
Elapsed time = 885.69 sec. (2136461.84 ticks, tree = 33.43 MB, solutions = 0)
  42214 18994    infeasible                            0.3680 12835045         
  42261 18991        0.4219   212                      0.3680 12856873         
  42324 19000        0.3991   199                      0.3681 12881636         
  42373 19005        0.4054   226                      0.3681 12905636         
  42439 19025    infeasible                            0.3681 12932402         
  42479 19035        0.4181   210                      0.3681 12953054         
  42552 19050    infeasible                            0.3681 12978151         
  42613 19045    infeasible                            0.3682 13001701         

GUB cover cuts applied:  13
Clique cuts applied:  1
Cover cuts applied:  46
Implied bound cuts applied:  51
Flow cuts applied:  32
Mixed integer rounding cuts applied:  231
Zero-half cuts applied:  32
Lift and project cuts applied:  9
Gomory fractional cuts applied:  9

Root node processing (before b&c):
  Real time             =    1.16 sec. (2617.96 ticks)
Sequential b&c:
  Real time             =  898.86 sec. (2167413.82 ticks)
                          ------------
Total (root+branch&cut) =  900.01 sec. (2170031.78 ticks)


MIP - Time limit exceeded, no integer solution.
Current MIP best bound =  3.6821327000e-01 (gap is infinite)
Solution time =  900.01 sec.  Iterations = 13013850  Nodes = 42650 (19047)
Deterministic time = 2170031.79 ticks  (2411.11 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX> 
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 900 --interval-exact-cutoff-time-limit 900 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__900s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__900s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__900s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__plain_fixed_interval_mip__ga074ec730af64a8c__900s.json --compact-bc-direct-gini-rows false --compact-bc-tight-mccormick false --compact-bc-inventory-conservation false --compact-bc-movement-reachability false --compact-bc-visit-inventory-linking false --compact-bc-objective-estimator-cutoff false --compact-bc-penalty-lb-closure false --compact-bc-gini-spread false --compact-bc-required-movement false --compact-bc-global-handling-capacity false --compact-bc-low-gini-centering false --compact-bc-support-duration false --compact-bc-transfer-compat false --compact-bc-receiver-source-cover off --compact-bc-variable-s-centering false --compact-bc-s-range-refinement off --compact-bc-sp-product-estimator off --tailored-bc-enabled false --tailored-bc-mode off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-support-duration-cover-mode off --compact-bc-root-cut-rounds 0

tight_T_seed3102.txt interval-cutoff-oracle interval_unresolved_timeout obj=0 runtime=900.133 columns=0
```

## engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__300s

- Return code: `0` / `0x00000000`.
- Status: `interval_closed`.
- Final JSON present: `True`.
- Finalization source: `cplex_solver_final`.
- Last valid bound: `0.600704436685`.
- Last node count: `185`.

### Solver Log Tail

```text
missing
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 300 --interval-exact-cutoff-time-limit 300 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__300s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__300s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__300s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__300s.json --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode callback --tailored-bc-callback-cut-profile route-cutset-only --tailored-bc-local-centering true --tailored-bc-gini-branching off --tailored-bc-branching-priority off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset true --tailored-bc-vector-route-cutset-max-size 4 --tailored-bc-vector-route-cutset-max-cuts 50 --tailored-bc-vector-cut-min-violation 0.000001 --tailored-bc-vector-cut-candidate-source callback --tailored-bc-structural-profile structural_route_limited --tailored-bc-s-bucket-ledger off --compact-bc-root-cut-rounds 1 --compact-bc-root-cut-time-limit 10

tight_T_seed3102.txt interval-cutoff-oracle interval_closed obj=0 runtime=30.3798 columns=0
```

## engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__900s

- Return code: `0` / `0x00000000`.
- Status: `interval_closed`.
- Final JSON present: `True`.
- Finalization source: `cplex_solver_final`.
- Last valid bound: `0.600704436685`.
- Last node count: `185`.

### Solver Log Tail

```text
missing
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 900 --interval-exact-cutoff-time-limit 900 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__900s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__900s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__900s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__tailored_route_leaf__ga074ec730af64a8c__900s.json --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode callback --tailored-bc-callback-cut-profile route-cutset-only --tailored-bc-local-centering true --tailored-bc-gini-branching off --tailored-bc-branching-priority off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset true --tailored-bc-vector-route-cutset-max-size 4 --tailored-bc-vector-route-cutset-max-cuts 50 --tailored-bc-vector-cut-min-violation 0.000001 --tailored-bc-vector-cut-candidate-source callback --tailored-bc-structural-profile structural_route_limited --tailored-bc-s-bucket-ledger off --compact-bc-root-cut-rounds 1 --compact-bc-root-cut-time-limit 10

tight_T_seed3102.txt interval-cutoff-oracle interval_closed obj=0 runtime=30.3901 columns=0
```

## engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__300s

- Return code: `0` / `0x00000000`.
- Status: `interval_closed`.
- Final JSON present: `True`.
- Finalization source: `solver_final_json`.
- Last valid bound: `0.600704436685`.
- Last node count: `211`.

### Solver Log Tail

```text
      2     2        0.5454   279                      0.5454     5072         
      4     2    infeasible                            0.5454     5811         
      8     2    infeasible                            0.5464     6037         
     14     6    infeasible                            0.5486     7133         
     18    10        0.5503   238                      0.5487     7417         
     20     8    infeasible                            0.5487     8554         
     24     8    infeasible                            0.5491    11125         
     29    11    infeasible                            0.5491    12166         
     36    14    infeasible                            0.5491    13141         
     49    19        0.5524   289                      0.5491    15640         
Elapsed time = 4.05 sec. (9690.88 ticks, tree = 0.11 MB, solutions = 0)
     84    44        0.5533   270                      0.5493    18572         
    111    47    infeasible                            0.5501    20847         
    125    41    infeasible                            0.5508    24296         
    144    32    infeasible                            0.5523    27692         
    179    15    infeasible                            0.5547    31423         

Cover cuts applied:  7
Implied bound cuts applied:  140
Flow cuts applied:  11
Mixed integer rounding cuts applied:  63
Zero-half cuts applied:  20
Gomory fractional cuts applied:  4

Root node processing (before b&c):
  Real time             =    2.28 sec. (5289.88 ticks)
Sequential b&c:
  Real time             =    4.22 sec. (9900.51 ticks)
                          ------------
Total (root+branch&cut) =    6.50 sec. (15190.40 ticks)


MIP - Integer infeasible.
Current MIP best bound is infinite.
Solution time =    6.50 sec.  Iterations = 34007  Nodes = 211
Deterministic time = 15190.40 ticks  (2336.98 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX> 
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 300 --interval-exact-cutoff-time-limit 300 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__300s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__300s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__300s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__300s.json --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode static --tailored-bc-callback-cut-profile off --compact-bc-root-cut-rounds 0 --compact-bc-dynamic-cut-families none --tailored-bc-branching-priority off --tailored-bc-gini-branching off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-cross-h-centering false --tailored-bc-local-q-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset false --tailored-bc-s-bucket-ledger off

tight_T_seed3102.txt interval-cutoff-oracle interval_closed obj=0 runtime=6.6632 columns=0
```

## engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__900s

- Return code: `0` / `0x00000000`.
- Status: `interval_closed`.
- Final JSON present: `True`.
- Finalization source: `solver_final_json`.
- Last valid bound: `0.600704436685`.
- Last node count: `211`.

### Solver Log Tail

```text
      2     2        0.5454   279                      0.5454     5072         
      4     2    infeasible                            0.5454     5811         
      8     2    infeasible                            0.5464     6037         
     14     6    infeasible                            0.5486     7133         
     18    10        0.5503   238                      0.5487     7417         
     20     8    infeasible                            0.5487     8554         
     24     8    infeasible                            0.5491    11125         
     29    11    infeasible                            0.5491    12166         
     36    14    infeasible                            0.5491    13141         
     49    19        0.5524   289                      0.5491    15640         
Elapsed time = 4.08 sec. (9690.88 ticks, tree = 0.11 MB, solutions = 0)
     84    44        0.5533   270                      0.5493    18572         
    111    47    infeasible                            0.5501    20847         
    125    41    infeasible                            0.5508    24296         
    144    32    infeasible                            0.5523    27692         
    179    15    infeasible                            0.5547    31423         

Cover cuts applied:  7
Implied bound cuts applied:  140
Flow cuts applied:  11
Mixed integer rounding cuts applied:  63
Zero-half cuts applied:  20
Gomory fractional cuts applied:  4

Root node processing (before b&c):
  Real time             =    2.30 sec. (5289.88 ticks)
Sequential b&c:
  Real time             =    4.25 sec. (9900.51 ticks)
                          ------------
Total (root+branch&cut) =    6.55 sec. (15190.40 ticks)


MIP - Integer infeasible.
Current MIP best bound is infinite.
Solution time =    6.55 sec.  Iterations = 34007  Nodes = 211
Deterministic time = 15190.40 ticks  (2320.21 ticks/sec)

CPLEX> CPLEX Error  1217: No solution exists.
No file written.
CPLEX> 
```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method interval-cutoff-oracle --input E:\codes\ExactEBRP\reference\hard_stress\V20_M3\tight_T_seed3102.txt --lambda 0.15 --T 3600 --time-limit 900 --interval-exact-cutoff-time-limit 900 --interval-exact-cutoff-oracle compact-mip --interval-exact-oracle-mode objective-bound --interval-exact-cutoff-gamma-L 0.0750880545856 --interval-exact-cutoff-gamma-U 0.112632081878 --interval-exact-cutoff-UB 0.600704436685 --interval-exact-cutoff-export-lp E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\model_exports\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__900s.lp --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__900s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__900s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\engineering__tight_T_seed3102__tailored_static_leaf_no_callback__ga074ec730af64a8c__900s.json --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode static --tailored-bc-callback-cut-profile off --compact-bc-root-cut-rounds 0 --compact-bc-dynamic-cut-families none --tailored-bc-branching-priority off --tailored-bc-gini-branching off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-cross-h-centering false --tailored-bc-local-q-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset false --tailored-bc-s-bucket-ledger off

tight_T_seed3102.txt interval-cutoff-oracle interval_closed obj=0 runtime=6.70135 columns=0
```

## pref_fix_incident__V12_M2__tailored_cheap_cuts__300s

- Return code: `3221225477` / `0xC0000005`.
- Status: `native_exit_noncertified`.
- Final JSON present: `True`.
- Finalization source: `stale_checkpoint_rejected`.
- Last valid bound: `0.0`.
- Last node count: `not_finalized`.

### Solver Log Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --input E:\codes\ExactEBRP\reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 204 --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --auto-interval-oracle-leaf-budget-policy total --auto-interval-oracle-total-budget 84 --auto-interval-oracle-time-limit 84 --auto-interval-oracle-child-time-limit 84 --compact-bc-time-limit 84 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\full__V12_M2__tailored_cheap_cuts__300s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --ub-event-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\full__V12_M2__tailored_cheap_cuts__300s.ub_events.csv --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\full__V12_M2__tailored_cheap_cuts__300s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\full__V12_M2__tailored_cheap_cuts__300s.json --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode callback --tailored-bc-callback-cut-profile cheap --compact-bc-root-cut-rounds 0 --compact-bc-dynamic-cut-families none --tailored-bc-branching-priority off --tailored-bc-gini-branching off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-cross-h-centering false --tailored-bc-local-q-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset false --tailored-bc-s-bucket-ledger off

```

### Stdout Tail

```text
COMMAND: E:\codes\ExactEBRP\build\ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-gf-tailored-bc --paper-run-sealed true --input E:\codes\ExactEBRP\reference\regen_candidate_V12_M2_average.txt --lambda 0.15 --T 3600 --time-limit 204 --threads 1 --mip-threads 1 --compact-bc-threads 1 --cplex-threads 1 --auto-interval-oracle-leaf-budget-policy total --auto-interval-oracle-total-budget 84 --auto-interval-oracle-time-limit 84 --auto-interval-oracle-child-time-limit 84 --compact-bc-time-limit 84 --progress-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\progress_traces\full__V12_M2__tailored_cheap_cuts__300s.progress.csv --progress-interval-seconds 30 --compact-bc-progress-interval 30 --ub-event-log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\full__V12_M2__tailored_cheap_cuts__300s.ub_events.csv --log E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\logs\full__V12_M2__tailored_cheap_cuts__300s.solver.log.txt --out E:\codes\ExactEBRP\results\gf_tailored_bc_fair_diagnosis_round\raw\full__V12_M2__tailored_cheap_cuts__300s.json --compact-bc-cut-profile balanced --compact-bc-low-gini-strengthening safe --compact-bc-denominator-bound-mode tight --compact-bc-objective-estimator-mode adaptive --compact-bc-domain-propagation-mode iterative --compact-bc-domain-propagation-rounds 2 --compact-bc-variable-s-centering true --compact-bc-sp-product-estimator paper-safe --compact-bc-sp-product-bounds tight --tailored-bc-enabled true --tailored-bc-mode callback --tailored-bc-callback-cut-profile cheap --compact-bc-root-cut-rounds 0 --compact-bc-dynamic-cut-families none --tailored-bc-branching-priority off --tailored-bc-gini-branching off --tailored-bc-gini-subset-envelope false --tailored-bc-low-gini-l1-centering false --tailored-bc-local-centering false --tailored-bc-subset-cross-h-centering false --tailored-bc-local-q-centering false --tailored-bc-subset-inventory-imbalance false --tailored-bc-transfer-cutset false --tailored-bc-gs-product-coupling false --tailored-bc-gs-product-lower-row off --tailored-bc-disaggregated-sp-estimator false --tailored-bc-disaggregated-sp-replace-aggregate false --tailored-bc-vector-support-cover false --tailored-bc-vector-route-cutset false --tailored-bc-s-bucket-ledger off

regen_candidate_V12_M2_average.txt gcap-frontier optimal obj=0.718504 runtime=200.987 columns=0
```

