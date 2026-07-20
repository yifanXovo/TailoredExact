# Round 24R final report

## Audit outcome

Round 24R used the authorized non-default license at `E:\gurobi\gurobi.lic`
only through the process-local environment. The file was never opened, parsed,
hashed, copied, or committed. The `gurobi_cl` check and the independent C++
environment/tiny-optimize check both returned 0 and reported `OPTIMAL` under
Gurobi 13.0.2.

Official rows: 45; completed: 45; failed:
0; interrupted/time-limited: 28; excluded:
0; strict original-problem certificates: 10. Stage 2 contains
28 rows and 8 strict certificates. Fifteen preliminary
attempts are retained separately as excluded evidence: 12 successful but
superseded protocol/debug attempts and three process failures from the diagnosed
controller split use-after-reallocation. Every affected matched row was rebuilt
and rerun after the fix.

The final CPLEX-only executable SHA-256 is
`f67ae4583f4002dca0403f75025eb6577feda76751c9fa02e09200bf9a50bc71`;
the final unified Gurobi-enabled executable SHA-256 is
`1154393cbc850513a8f0707d0e3e3b10d3d121db4dfc0bb9c6f9e881d2b95ac2`.

Both clean release configurations passed all nine CTest targets (18/18 across
the two builds). The Round 24 backend executable passed 98/98 checks; the
Round 20 Python regression suite passed six groups; the Round 22 static suite
passed 21 checks; handling-convention tests passed in both configurations; the
no-instance-dispatch audit passed; and all ten Stage 0 native commands passed.
The evidence package contains 1,103 files (501.41 MiB); its largest artifact is
the V12_M1 P-CPX Stage 2 `dense_progress.csv` at 43,429,739 bytes (41.42 MiB).

## Correctness and mechanical qualification

The external CPLEX adapter now classifies native numeric statuses explicitly.
Only exact optimal with exact-zero gaps and passing lifecycle/model-identity
gates can close a leaf as exact; tolerance-optimal, unscaled-infeasibility,
ambiguous, and unsupported statuses fail closed. Direct status tests cover exact
optimal, tolerance optimal, infeasible, time-limit with/without incumbent,
unscaled infeasibility, and unsupported cases.

Immutable canonical leaf artifacts are keyed by model scope, interval, cutoff,
row signature, and fingerprint. A retained unchanged leaf reuses the identical
path/SHA without rewriting; a split child or identity change creates or
invalidates an artifact. The Stage 1B fresh and retained runs each generated
five artifacts and recorded one artifact-cache hit. Fresh opened six native
models; retained opened five models for six optimize calls.

Native import succeeded for toy (77 rows, 44 columns, 217 nonzeros; 18 binary,
8 integer, 18 continuous; fingerprint 1305815249) and V12_M1 (992 rows,
489 columns, 3867 nonzeros; 253 binary, 48 integer, 188 continuous;
fingerprint 1133953353). Objective sense, variable names/types/bounds, native
domain audit, and known-feasible-route verification passed. Toy CPLEX and Gurobi
both strictly certified the same exact optimum. Canonical LP byte identity is
reported only alongside this successful native import audit.

The moderate4301 sentinel completed all six arms. S0-SAFE emitted a valid
time-limit bound; the unsafe presolve-on persistent arm remained permanently
non-certifying; both static external backends retained the verified witness;
the feasibility-consistency gates passed and no contradicted infeasibility was
serialized.

## Stage 2 results

| Instance | Arm | Result | Strict | Final LB | Common gap | Bound-progress AUC | Wall s |
|---|---|---|---:|---:|---:|---:|---:|
| V12_M1 | P-CPX | time_limit | no | 0.345376 | 0.0331034 | 0.938424 | 294.896 |
| V12_M1 | P-GRB | optimal | yes | 0.357201 | 1.24325e-15 | 0.99128 | 34.9516 |
| V12_M1 | S0-SAFE | global_gini_tree_time_limit | no | 0.356679 | 0.00145977 | 0.973937 | 294.249 |
| V12_M1 | T-CPX-ST-PON-DIAG | global_gini_tree_not_certified | no | -- | -- | 0.973928 | 280.325 |
| V12_M1 | T-CPX-EXT-PON | optimal | yes | 0.357201 | 0 | 0.957281 | 89.7647 |
| V12_M1 | T-GRB-EXT-COLD | optimal | yes | 0.357201 | 0 | 0.970776 | 35.2278 |
| V12_M1 | T-GRB-EXT-WARM | optimal | yes | 0.357201 | 0 | 0.975936 | 31.4457 |
| V12_M2 | P-CPX | time_limit | no | 0.569576 | 0.207276 | 0.771439 | 294.246 |
| V12_M2 | P-GRB | optimal | yes | 0.718504 | 0 | 0.974247 | 170.421 |
| V12_M2 | S0-SAFE | global_gini_tree_time_limit | no | 0.707138 | 0.0158188 | 0.959817 | 294.333 |
| V12_M2 | T-CPX-ST-PON-DIAG | global_gini_tree_not_certified | no | -- | -- | 0.964065 | 294.317 |
| V12_M2 | T-CPX-EXT-PON | optimal | yes | 0.718504 | 0 | 0.931496 | 225.066 |
| V12_M2 | T-GRB-EXT-COLD | optimal | yes | 0.718504 | 0 | 0.93556 | 196.011 |
| V12_M2 | T-GRB-EXT-WARM | optimal | yes | 0.718504 | 0 | 0.937422 | 173.383 |
| high_imbalance_seed3202 | P-CPX | time_limit | no | 1.04711 | 0.401416 | 0.586303 | 294.192 |
| high_imbalance_seed3202 | P-GRB | time_limit | no | 1.07466 | 0.385668 | 0.604983 | 294.079 |
| high_imbalance_seed3202 | S0-SAFE | global_gini_tree_time_limit | no | 1.68091 | 0.0391021 | 0.953569 | 294.23 |
| high_imbalance_seed3202 | T-CPX-ST-PON-DIAG | global_gini_tree_not_certified | no | -- | -- | 0.951147 | 294.199 |
| high_imbalance_seed3202 | T-CPX-EXT-PON | external_gini_tree_time_limit | no | 1.70719 | 0.0240815 | 0.900275 | 288.742 |
| high_imbalance_seed3202 | T-GRB-EXT-COLD | external_gini_tree_time_limit | no | 1.69747 | 0.0296384 | 0.90072 | 288.579 |
| high_imbalance_seed3202 | T-GRB-EXT-WARM | external_gini_tree_time_limit | no | 1.69909 | 0.0287114 | 0.90167 | 288.582 |
| tight_T_seed3101 | P-CPX | time_limit | no | 0.0128709 | 0.879995 | 0.109082 | 294.09 |
| tight_T_seed3101 | P-GRB | time_limit | no | 0.0193785 | 0.819319 | 0.165784 | 294.081 |
| tight_T_seed3101 | S0-SAFE | global_gini_tree_time_limit | no | 0.039643 | 0.630378 | 0.338604 | 294.198 |
| tight_T_seed3101 | T-CPX-ST-PON-DIAG | global_gini_tree_not_certified | no | -- | -- | 0.351064 | 294.186 |
| tight_T_seed3101 | T-CPX-EXT-PON | external_gini_tree_time_limit | no | 0.0483282 | 0.549399 | 0.419355 | 288.718 |
| tight_T_seed3101 | T-GRB-EXT-COLD | external_gini_tree_time_limit | no | 0.0528193 | 0.507524 | 0.476926 | 288.698 |
| tight_T_seed3101 | T-GRB-EXT-WARM | external_gini_tree_time_limit | no | 0.052886 | 0.506903 | 0.477417 | 288.696 |

The AUC column is normalized common-UB bound-progress AUC (larger is better).
Unsafe diagnostic bounds and AUCs are displayed only as non-authoritative speed
signals and are excluded from exact comparisons.

## Lifecycle and restart evidence

| Arm | Optimize | Models/reads | Artifacts/hits | Presolve/root | Same-leaf/child | Starts accepted/submitted |
|---|---:|---:|---:|---:|---:|---:|
| P-CPX | 4 | 4/4 | 0/0 | 4/4 | 0/0 | 0/0 |
| P-GRB | 4 | 4/4 | 0/0 | 4/4 | 0/0 | 0/0 |
| S0-SAFE | 4 | 4/4 | 0/0 | 0/4 | 0/0 | 0/0 |
| T-CPX-ST-PON-DIAG | 4 | 4/4 | 0/0 | 4/4 | 0/0 | 0/0 |
| T-CPX-EXT-PON | 35 | 35/35 | 26/9 | unavailable | 0/26 | 0/0 |
| T-GRB-EXT-COLD | 31 | 24/24 | 24/7 | 31/23 | 7/24 | 0/0 |
| T-GRB-EXT-WARM | 31 | 24/24 | 24/7 | 31/23 | 7/24 | 1/6 |

For external CPLEX, native presolve/root execution counts were not instrumented
and are reported as unavailable rather than fabricated. All seven Stage 2
same-leaf Gurobi re-optimizations reran presolve and were conservatively
classified as observed fresh restarts: confirmed continuation 0, partial reuse
0, ambiguous 0. Warm starts are primal information only. Stage 2 produced 24
candidates: six complete candidates were submitted, one was affirmatively
accepted, and 23 were conservatively classified rejected (five after submission
without affirmative acceptance and 18 before submission because the complete
mapping/compatibility gates did not pass). No warm start is described as native
tree reuse.

Stage 1B isolates artifact/native-model lifecycle on V12_M2. Fresh cold used
6 models for 6 optimizes and
finished at LB 0.651908, gap
0.0926872. Retained cold used
5 models for 6
optimizes, reused one unchanged leaf artifact/model, and finished at LB
0.686046, gap 0.0451738; native
logs nevertheless classify that same-leaf attempt as a fresh restart. Warm
matched retained cold at LB 0.686046, gap
0.0451738.

## Paired interpretation

- **Plain Gurobi versus plain CPLEX:** Gurobi strictly certified both V12 cases
  (34.95 s and 170.42 s); CPLEX certified none within the cap. On both hard
  time-limited cases Gurobi had higher final LB and bound-progress AUC. Plain
  Gurobi dominated plain CPLEX on this short matrix.
- **Safe persistent CPLEX versus external CPLEX:** mixed. External CPLEX
  strictly certified V12_M1 in 89.61 s while S0 did not within 180 s; S0 had a
  slightly better V12_M2 bound/gap. This is an architecture comparison, not a
  pure restart-only ablation.
- **Presolve-on diagnostic architecture:** the persistent diagnostic remains
  unsafe and non-certifying. External presolve-on CPLEX certified both V12
  cases and gave stronger hard-case bounds, but this comparison is speed
  potential only and supplies no exact evidence for the unsafe arm.
- **External Gurobi versus external CPLEX:** Gurobi certified both V12 cases
  faster. On the hard cases CPLEX had the better high-imbalance LB, while
  Gurobi had the better tight-T LB. The result is mixed and preliminary
  promising.
- **Warm versus cold Gurobi:** identical Stage 1B endpoints; in Stage 2 warm
  certified both V12 cases faster and made marginally better hard-case
  LB/AUC progress. With only one affirmatively accepted start, the supported
  conclusion is mixed, preliminary proof-progress benefit, not tree reuse.
- **Warm Gurobi versus S0:** warm Gurobi certified both V12 cases and had the
  strongest tight-T LB/AUC; S0 was materially stronger on high imbalance. This
  is enough to justify a later longer Gurobi migration study, not promotion.

## Decision and limitations

The persistent and external algorithms share fixed mathematical and scheduling
settings, but native search order and split timing are not identical. Results
therefore compare persistent-single-tree architecture with external-multi-
optimize architecture. There was no instance-dependent dispatch and no solver
portfolio.

**Corrected CPLEX S0/F0 remains the stable paper mainline.** Licensed Gurobi is
strong enough to justify a later longer migration study, but Round 24R does not
promote a backend or alter the paper mainline.
