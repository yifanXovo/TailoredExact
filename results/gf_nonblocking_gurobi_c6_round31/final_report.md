# Round 31 final report

## Outcome

Final classification: **paper_exact_and_broadly_dominant**.

S0/F0-CPLEX remains the stable accepted paper mainline. C0-DIAG remains the exact but non-paper-compatible performance teacher. C5 remains the exact first-generation partial-bound transfer. C6 is retained as the Round 31 candidate; it is not automatically promoted.

## Frozen provenance and toolchain

- Starting HEAD: `893656f85fa6394dac787fee78baad2a52cdd2d2`
- Frozen C6 source commit: `23ea2d7733a61fc86dae1da5ffaba2b8b1e2e533`
- Observed live main at entry: `224e9bb333d08956dc37172d12544201bc48e5f5`
- Compiler: `g++.exe (Rev2, Built by MSYS2 project) 14.2.0`
- CMake: `cmake version 3.30.5-msvc23`
- CPLEX: `22.1.1`
- Gurobi: `13.0.2`
- CPLEX executable SHA-256: `d56515ad5ceaaf6420d6935facfddbd376c2e5f45d8bab1012b4e0dede35b01b`
- Gurobi executable SHA-256: `113c7c912a078bd35430e4eb0bbc15d5dcb5ecc44529b931a835ed75f2e6f842`

## Forensic diagnosis

Phase A found that C5's failures were primarily continuation and scheduling failures, not evidence for a new inequality family. Thirty of 55 selected parents were no longer strictly controlling after their complete LP, making 60 child LPs avoidable. Eighty-six of 94 attained child targets then forced delayed splits with zero current child gain and zero immediate global-bound gain. No-gain terminal parents consumed 98.13% of terminal Work; a small set of root/cut-loop or deep one-node MIPs dominated the deadline losses. C5 interval models were also materially larger than P-GRB, especially at V50.

## Selected C6 algorithm

C6 is parent-native-first. After a complete parent LP, it requeues a parent that is no longer controlling. Otherwise it processes one launch-frozen target equal to the smallest strictly higher valid bound of another relevant leaf. Ties do not create targets. After that one OPEN_NATIVE_BOUNDED transition, child LPs are computed lazily only when the leaf controls again.

The split threshold remains `rho=0.01`, and it is the sole policy threshold. A small current child gain targets the complete child disjunction bound. Reaching it retains and requeues the open parent with cached complete children; it never forces a delayed split. A no-gain parent launches exact closure after its unused frontier milestone is exhausted. Only optimality, infeasibility, or verified cutoff closes coverage.

C6 adds zero strategy parameters and contains no internal time, Work, node, solution, attempt, retry, family, size, seed, path, or historical-objective dispatch.

The implementation retains the same model object only. It makes no LP-basis, simplex-reoptimization, or native-tree continuation claim.

## Tests and correctness

- C++ tests per clean build: 14
- Python test scripts: 14
- Stage 0 state-machine cases: 18
- Tiny exactness rows: 4
- Moderate4301 sentinel rows: 4
- All Stage 0 gates: True
- Official false certificates: 0

## Development mechanism evidence

The 71-second development matrix contained 11 rows: 10 reached exact C6 and 1 was retained as a pre-exact HGA-deadline exclusion. C6 avoided 37 child lookaheads, ran 19 next-leaf targets, reached 12, and issued 12 native requeues.

## Primary same-solver result: C6 versus P-GRB

- Final-LB wins/losses/ties: 15/0/2
- Observed-AUC wins/losses/ties over 16 compatible pairs: 13/3/0
- Short-run broad-nonregression gate: True

### Existing-family breakdown

| Family | V | Rows | C6 final W/L/T | C6 AUC W/L/T |
|---|---:|---:|---:|---:|
| high_imbalance | 20 | 4 | 4/0/0 | 4/0/0 |
| high_imbalance | 50 | 1 | 1/0/0 | 0/1/0 |
| moderate | 20 | 4 | 4/0/0 | 4/0/0 |
| moderate | 50 | 1 | 1/0/0 | 0/1/0 |
| tight_T | 20 | 4 | 4/0/0 | 4/0/0 |
| tight_T | 50 | 1 | 1/0/0 | 1/0/0 |
| v12 | 12 | 2 | 0/0/2 | 0/1/0 |

## Sealed held-out evidence

Final-LB wins/ties versus P-GRB: 6/6. The frozen audit reports AUC wins/ties 4/6 where compatible.

| Family | V | Rows | C6 final W/L/T | C6 AUC W/L/T |
|---|---:|---:|---:|---:|
| high_imbalance | 20 | 1 | 1/0/0 | 1/0/0 |
| high_imbalance | 50 | 1 | 1/0/0 | 0/1/0 |
| moderate | 20 | 1 | 1/0/0 | 0/1/0 |
| moderate | 50 | 1 | 1/0/0 | 1/0/0 |
| tight_T | 20 | 1 | 1/0/0 | 1/0/0 |
| tight_T | 50 | 1 | 1/0/0 | 1/0/0 |

## Ablations and anchors

- C6 versus C5 final-LB wins/losses/ties on directly paired mechanism/sealed rows: 10/1/4.
- P-GRB-HGA ablation rows: 7.
- S0/F0 anchor rows: 7.

P-GRB-HGA changes only the independently verified incumbent start; it leaves the compact model and plain one-tree Gurobi configuration unchanged. S0 comparisons remain cross-solver anchors, not the primary promotion criterion.

## C6 mechanism totals on the 17-instance primary matrix

- Parent/child LP optimize calls recorded: 120
- Native target phases: 34
- Partial target optimize calls: 34
- Native requeues: 27
- Child lookaheads avoided: 68
- Forced delayed splits avoided: 0
- Atomic splits: 0
- Terminal MIP calls: 20
- Terminal MIP Work: 6002.015317
- Total external Work: 8149.897891
- LP cutoff prunes: 0
- Mean observed time to common 10% gap among reached rows: 78.742565s
- Mean final stagnation: 195.771272s

## Repeatability and conditional medium runs

Repeatability rows: 8. Exact target-sequence matches: 8; exact split-sequence matches: 8.

Conditional Stage 6 executed: True. Excluded conditional rows: 0.

### Conditional 1200-second results

Stage 6 materialized 27 rows over 9 instances. C6 final-LB wins/losses/ties were 8/0/1 versus P-GRB and 5/1/3 versus C5.

Strict certificates: P-GRB 1, C5 3, C6 4.

On sealed V50, C6 uniquely certified optimality in 1037.620s; P-GRB and C5 remained open at their fixed caps. On sealed V20, C5 and C6 certified while P-GRB remained open.

The first Stage 6 launch was a zero-solve preflight refusal: the source freeze guard correctly detected the analyzer's analysis-only keyword-interface repair. The frozen analyzer bytes were restored for all 27 solver runs, and the one-line repair was reapplied only after the runner exited.

## Final interpretation

Completed process rows: 148; failed rows: 0; time-limited rows: 110; emergency timeouts: 0.

The unresolved mechanism, if C6 is not broadly dominant, is the remaining cost of complete parent closure and the gap between external interval-model proof structure and P-GRB's single compact native tree—not correctness, target validity, or delayed-split degeneracy.

A later long-run promotion study is justified: True. Regardless, C6 does not replace S0/F0-CPLEX in this round.

## Evidence package

- Files excluding manifest: 6622
- Bytes excluding manifest: 983555778
- Largest artifact: `results/gf_nonblocking_gurobi_c6_round31/runs/stage4__tight_T_seed3101__s0_cplex__300s/global_node_trace.csv.gz` (6102157 bytes)
- Losslessly compressed files: 1717
- Restoration hashes verified: True

Task wall-clock and token usage are recorded in the final Codex handoff because those counters are supplied by the execution orchestrator, not by repository code.
