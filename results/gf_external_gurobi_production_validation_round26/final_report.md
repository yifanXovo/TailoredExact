# Round 26 final report

## Decision

**C1 is not promoted.** It equals C0 because the sole uniform prototype P1 was
rejected by the frozen difficult-case development guard. The final production
audit passes 8/10 gates and fails Gates
3, 9. Corrected CPLEX S0/F0 remains
stable mainline; no alias, fallback, portfolio, or instance-dependent selector
was added.

The positive result is substantial but insufficient for promotion: C1 beats
P-GRB on 16/18 official pairs, including 9/9 non-V12 known/held-out V20, 3/3
V50, and 4/4 long rows. The blockers are the persistent V12_M2 structural
overhead and failure to broadly nonregress against independent C0 repetitions.

## Provenance and qualification

The branch starts from `d8cba691424eb990fc22357f7a2911ec5d34f3df`;
live `origin/main` was observed as
`4a608eeae559cc69ca5c37b6eb4abab74fd3bc3b` before Round 26. Frozen C0/C1
executable SHA-256 is `002ab0f3f3fc1f80bb4b8a6eb10fddaaf013f5c493317884c977098ede0cc15c` using Gurobi
13.0.2; the Stage 0 current Gurobi build and CPLEX-only
control hashes are `31a5cc71a454bcdba1b287ddd2f0c84a1b4c4a72c3baa517cab9a06caa7dc299`
and `f16ec489a9811f5aaa79ed914d473fd2470f7fa0e1edf75121071eea18be0c8a`. CPLEX 22.1.1.0 is
historical S0-REF only.

Stage 0 passed 18/18 C++ tests, 7 Python suites, 15 native imports, 2 license
checks, 2 moderate4301 sentinels, and the static scan with zero forbidden
dispatch findings. All 47 official rows are authoritative and pass every
coverage, lifecycle, consistency, witness, bound, and certificate gate.

## C0, C1, and exactness

C0 is the frozen Round 25 cold, one-thread, solver-neutral external global-Gini
tree with static F0 leaf models, same-run independently verified HGA UB,
non-strict cutoff, parent-bound inheritance, immutable artifact cache, and no
cross-model warm start. P1 uniformly split unresolved leaves after one attempt;
it removed 70.0% of V12_M2 excess Work but failed high3202 by losing strict
closure and 0.028835 normalized LB, beyond the 0.02 guard. P1 was rejected
without tuning, so C1 is exactly C0 with the two-attempt rule.

The exactness argument is unchanged: root intervals cover the complete original
feasible region; atomic parent-to-child replacement preserves coverage; inherited
bounds remain valid; cutoffs use independently verified feasible UBs; unresolved
intervals cannot disappear; lifecycle/verifier checks agree; and a strict
certificate is asserted only for the complete original problem.

## V12 repeatability and diagnosis

Across three forensic repetitions, V12_M1 median C0/P-GRB certificate wall is
37.559/36.498 seconds (1.029x), while Work is 34.781/53.573. This is bounded
fixed orchestration overhead inside 5% and the enhanced replay classifies it as
timing noise.

V12_M2 forensic median wall is 183.022/179.187 seconds (1.021x), but Work is
341.716/282.097 (1.211x), with repeated model/presolve/root execution. In the
official row C1 loses 198.413 to 169.709 seconds and uses 365.361 versus 282.097
Work. Its replay remains a persistent external-overhead regression: repeated
same-leaf attempts, fresh roots, and delayed partitioning dominate; model I/O,
initial allocation, scheduler starvation, and numerical failure do not. Thus
only V12_M1 is resolved as timing noise; V12_M2 is unresolved.

## Official rows and strict certificates

All 47/47 official processes completed with return code zero: 38 valid time
limits, 9 optimal rows, 0 failures, 0 interruptions, and 0 exclusions. Official
solve wall totals 21.45 hours.

| Stage | Seconds | Completed | Time-limited | Strict |
| --- | ---: | ---: | ---: | ---: |
| stage1 | 1200 | 15/15 | 8 | 7 |
| stage2 | 1800 | 18/18 | 16 | 2 |
| stage3 | 1800 | 6/6 | 6 | 0 |
| stage4 | 3600 | 8/8 | 8 | 0 |

| Stage | Strict certificates by arm |
| --- | --- |
| stage1 | C0: 3/5 | C1: 2/5 | P-GRB: 2/5 |
| stage2 | C0: 1/6 | C1: 1/6 | P-GRB: 0/6 |
| stage3 | C1: 0/3 | P-GRB: 0/3 |
| stage4 | C1: 0/4 | P-GRB: 0/4 |

## Frozen hierarchy comparisons

`P-GRB` versus C0: C0 9, left arm 2, ties 0 (11 pairs). `P-GRB` versus C1:
C1 16, left arm 2, ties 0 (18 pairs). C0 versus C1: C1 4, left arm 7, ties 0 (11 pairs). C1 wins all
six sealed V20 pairs, including the new strict certificate on high5203; all
three V50 pairs; and all four fixed 3600-second pairs. C0 and C1 are identical
algorithms, so their 4-7 hierarchy split measures independent run variability,
not a mechanism improvement.

| Scope | Family | Pairs | P-GRB-C1 wins | Mean gap P-GRB-C1 | Mean AUC P-GRB-C1 |
| --- | --- | ---: | ---: | ---: | ---: |
| stage1 | high_imbalance | 1 | 0-1-0 | 0.3393-0.0240 | 0.6286-0.9562 |
| stage1 | moderate | 1 | 0-1-0 | 0.3385-0.1712 | 0.6597-0.7885 |
| stage1 | tight_T | 1 | 0-1-0 | 0.7725-0.4814 | 0.1962-0.5038 |
| stage1 | v12 | 2 | 2-0-0 | 0.0000-0.0000 | 0.9957-0.9883 |
| stage2 | high_imbalance | 2 | 0-2-0 | 0.1471-0.0262 | 0.8375-0.9587 |
| stage2 | moderate | 2 | 0-2-0 | 0.5655-0.3732 | 0.3819-0.6143 |
| stage2 | tight_T | 2 | 0-2-0 | 0.3498-0.1334 | 0.6169-0.8522 |
| stage3 | high_imbalance | 1 | 0-1-0 | 0.1895-0.0969 | 0.8084-0.8563 |
| stage3 | moderate | 1 | 0-1-0 | 0.3094-0.1480 | 0.6858-0.8240 |
| stage3 | tight_T | 1 | 0-1-0 | 0.2492-0.1120 | 0.7432-0.8635 |
| stage4 | high_imbalance | 1 | 0-1-0 | 0.1685-0.0520 | 0.8195-0.9397 |
| stage4 | moderate | 2 | 0-2-0 | 0.4234-0.2571 | 0.5675-0.7314 |
| stage4 | tight_T | 1 | 0-1-0 | 0.3199-0.1105 | 0.6573-0.8811 |
| known_and_heldout_v20 | high_imbalance | 3 | 0-3-0 | 0.2112-0.0255 | 0.7679-0.9579 |
| known_and_heldout_v20 | moderate | 3 | 0-3-0 | 0.4899-0.3059 | 0.4745-0.6724 |
| known_and_heldout_v20 | tight_T | 3 | 0-3-0 | 0.4907-0.2494 | 0.4767-0.7361 |
| known_and_heldout_v20 | all_non_v12 | 9 | 0-9-0 | 0.3972-0.1936 | 0.5730-0.7888 |

## Scalability and long-run closure

All V50 rows have valid models and bounds. At 1800 seconds C1 common-UB gaps
are 0.0969, 0.1480, and 0.1120 versus P-GRB's 0.1895, 0.3094, and 0.2492.
At 3600 seconds C1 wins all four pairs and every C1 lower bound improves after
the 1800-second checkpoint. Long-run peak memory reaches 6.078 GB on V50
moderate6301; progress is sustained despite 299.4 seconds of final stagnation.

| Stage | V | Arm | Rows | Mean gap | Mean AUC | Max GB | Sustained/checked |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| stage2 | 20 | C0 | 6 | 0.1768 | 0.8090 | 1.1841 | 0/0 |
| stage2 | 20 | C1 | 6 | 0.1776 | 0.8084 | 1.2647 | 0/0 |
| stage2 | 20 | P-GRB | 6 | 0.3541 | 0.6121 | 0.2446 | 0/0 |
| stage3 | 50 | C1 | 3 | 0.1190 | 0.8479 | 4.4489 | 0/0 |
| stage3 | 50 | P-GRB | 3 | 0.2494 | 0.7458 | 0.5664 | 0/0 |
| stage4 | mixed | C1 | 4 | 0.1692 | 0.8209 | 6.0783 | 4/4 |
| stage4 | mixed | P-GRB | 4 | 0.3338 | 0.6530 | 0.7917 | 0/0 |

## Automatic diagnostics

Exactly 2/18 P-GRB/C1 pairs triggered, and both exactly-once diagnostic C1
replays completed. They never replace official rows.

| Trigger | Classification | Wall ratio | Work ratio | Restarts/splits/reads | GB | Stagnation s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| stage1__V12_M1__1200s__c1 | timing noise | 1.0170 | 0.6492 | 4/0/4 | 0.0798 | 0.0004 |
| stage1__V12_M2__1200s__c1 | persistent external-overhead regression | 1.0321 | 1.1464 | 6/1/6 | 0.2152 | 0.0004 |

## Lifecycle and resource summary

Unsupported native phase times and cut counts remain marked unavailable; they
are not estimated. Restart columns are fresh/same-leaf/child.

| Arm | Rows | Work | Restarts | Splits | Reads | Read s | Max GB | Max stagnation s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P-GRB | 18 | 67511.6 | 0/0/0 | 0 | 18 | 0.00 | 0.7917 | 791.1 |
| C0 | 11 | 22871.5 | 181/116/181 | 70 | 181 | 3.88 | 1.1841 | 1050.1 |
| C1 | 18 | 67242.4 | 413/313/413 | 173 | 413 | 29.92 | 6.0783 | 1202.5 |

## Promotion audit

| Gate | Requirement | Result | Evidence |
| ---: | --- | --- | --- |
| 1 | exactness_and_correctness | PASS | 47/47 authoritative; zero applicable gate failures |
| 2 | uniform_no_dispatch | PASS | zero static no-dispatch findings; one uniform C1 manifest |
| 3 | v12_regressions_resolved_or_bounded | FAIL | V12_M1 is timing noise; V12_M2 remains persistent external-overhead regression |
| 4 | broad_p_grb_advantage_known_and_heldout_v20 | PASS | C1 wins 9/9 non-V12 pairs; held-out mean/median gap and AUC all improve |
| 5 | no_family_systematic_regression | PASS | no P-GRB-favoring family majority |
| 6 | new_heldout_v20_strict_certificate | PASS | new C1-only strict certificates: high_imbalance_seed5203 |
| 7 | v50_validity_and_advantage | PASS | C1 wins 3/3 V50 pairs; all bounds valid |
| 8 | long_run_sustained_progress | PASS | 4/4 C1 rows improve after halfway |
| 9 | broad_c0_nonregression | FAIL | C1 wins/ties 4/11; C0-favoring family majorities=high_imbalance,tight_T; max normalized gap loss=0.024002 |
| 10 | independent_of_warm_start_selection_and_known_objective | PASS | cold C1=C0 binary; no portfolio, known-objective, family, seed, or size dispatch |

Promotion fails closed. The strong held-out and large-instance result does not
override V12_M2 or C0 nonregression gates, and mean performance alone is not a
promotion criterion.

## Evidence package and limitations

The package has 3142 retained files excluding
its self-excluded manifest, totaling 443.1
MiB. The largest artifact is `results/gf_external_gurobi_production_validation_round26/runs/stage4__tight_T_seed5102__p_grb__3600s/progress.csv` at
3993192 bytes. It has 0 raw
LPs, 812 verified
compression entries, 0 compression mismatch,
and 0 sensitive-marker hits; package status is
**passed**.

Limitations are the unresolved V12_M2 repeated-root overhead, C0/C1 run
variability, no strict V50 or 3600-second certificate, unavailable safe native
per-leaf phase timing/cut totals, and increased external-tree memory at V50.
All time-limited rows retain valid global bounds; none is presented as a strict
certificate.
