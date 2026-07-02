# GF Compact BC Strengthening Round Final Report

Date: 2026-07-02

## Summary

This round strengthened and audited the `paper-gf-compact-bc` mainline, with
single-thread CPLEX benchmark fairness and clearer compact-BC result accounting.
The algorithm remains the Gini-frontier compact branch-and-cut/certification
framework; BPC is not used as paper-core certificate evidence.

## CPLEX Thread Fairness

Plain compact CPLEX benchmark rows were rerun with `--cplex-threads 1`.
Controlled compact-BC paper rows were run with `--compact-bc-threads 1` and
emit `thread_fairness_class=one_thread_fair`.

Previous multithread CPLEX comparisons should not be used as fair controlled
paper comparisons. The single-thread comparison makes compact-BC look stronger
against CPLEX on the tested V20 rows, but the short one-thread compact-BC suite
also did not reproduce the earlier longer/multithread `high_imbalance_seed3202`
certificate.

## V20 Compact-BC Mini-Suite

| Row | Status | LB | UB | Gap | Notes |
|---|---|---:|---:|---:|---|
| high_imbalance_seed3201 | not closed | 2.307421 | 2.44340319194 | 0.0556527847682 | compact-BC leaves timed out |
| high_imbalance_seed3202 | not closed | 1.619911 | 1.74931345205 | 0.0739732790021 | short one-thread run did not certify |
| tight_T_seed3101 | optimal | 0.107252734134 | 0.107252734134 | 0 | certified |
| tight_T_seed3102 | not closed | 0.520346 | 0.600704436685 | 0.133773669342 | compact-BC leaves timed out |
| moderate_seed3301 | not closed | 0.046285 | 0.0491525526647 | 0.058339852343 | 4 leaves closed, 2 unresolved |
| moderate_seed3302 | not closed | 0.13884 | 0.195636206549 | 0.290315415285 | compact-BC leaves timed out |

`moderate_seed3301` did not certify. The controlled row improves over plain
CPLEX under the same 300s one-thread policy, but it did not improve over the
prior longer strengthened-oracle evidence. The exact remaining blocker is
timeout in the compact interval BC subsolver on low-Gini leaves.

## Cut Ablation

The no-new-cuts rows now truthfully report effective enabled families as `none`
for this round's new cut families. Top-level rows aggregate child interval
cut/domain counts.

Selected ablation signal:

| Row | Variant | LB | Gap |
|---|---|---:|---:|
| moderate_seed3301 | no_new_cuts, 60s | 0.043246 | 0.120167770432 |
| moderate_seed3301 | receiver singleton, 60s | 0.043381 | 0.117421219283 |
| moderate_seed3301 | all safe, 300s | 0.046285 | 0.058339852343 |
| V12 M2 | no_new_cuts, 60s | 0.649065 | 0.0966439489786 |
| V12 M2 | dynamic-root metadata/static probe, 60s | 0.653506 | 0.090463051499 |

The strongest practical gain came from the all-safe static compact-BC cut set
combined with more time. Receiver singleton cuts were implemented safely but
only gave a small short-run improvement in this sample.

## Dynamic Root Separation

Dynamic root-cut CLI fields and accounting were added. The current
implementation is not a true CPLEX callback or fractional root-solution
separation loop; it records/probes root-round configuration and reuses static
valid cut generation. Therefore dynamic-root rows are diagnostic and should not
be claimed as evidence for a new dynamic separator.

## Receiver-Set Source Cover

The old receiver-set source-cover form remains disabled because it can cut
valid solutions when stations inside the receiver set exchange bikes.

Implemented paper-safe subset: singleton net-delivery lower-bound rows
`sum_k d[k,j] >= max(0,L_j-initial_j)`. Pair/set receiver-cover remains
diagnostic until a stronger proof is added.

## Large-V Diagnostics

Generated V50/V100 diagnostic instances and manifest under
`reference/large_diagnostics/`. Compact-BC V50/V100 rows produced final wrapper
JSONs but failed before useful proof work due memory/model-size failures
(`std::bad_alloc` for V50). Plain single-thread CPLEX built the selected V50 and
V100 moderate benchmark rows but did not certify them in 300s.

## Exact vs CPLEX, Single Thread

| Row | Compact-BC status/gap | Plain CPLEX status/gap |
|---|---|---|
| V12 M1 | optimal / 0 | optimal / 0 |
| V12 M2 | optimal / 0 | not certified / 0.139283390494 |
| high_imbalance_seed3202 | not closed / 0.0739732790021 | not certified / 0.625200254678 |
| tight_T_seed3101 | optimal / 0 | not certified / 0.901498877155 |
| moderate_seed3301 | not closed / 0.058339852343 | not certified / 0.442849635501 |
| tight_T_seed3102 | not closed / 0.133773669342 | not certified / 0.269248675986 |
| high_imbalance_seed3201 | not closed / 0.0556527847682 | not certified / 0.225923879082 |

The comparison changed the interpretation: previous multithread CPLEX numbers
are not fair one-thread comparisons. In this controlled table, compact-BC gives
better bounds on all compared V20 rows, but still leaves most V20 rows open in
the short one-thread run.

## Audits

Audits run:

- `scripts/audit_bpc_certificate.py --self-test`
- `scripts/audit_bpc_certificate.py results\gf_compact_bc_strengthening_round\raw --csv-out results\gf_compact_bc_strengthening_round\certificate_audit.csv --fail-on-error --require-progress-finals results\gf_compact_bc_strengthening_round\raw`
- `build\ExactEBRP.exe --method certificate-basis-test`
- `build\ExactEBRP.exe --method option-consistency-test`
- `scripts/audit_gf_compact_bc_summary.py`
- `scripts/audit_no_instance_special_cases.py`
- `scripts/audit_objective_convention.py`

All optimal claims pass. Benchmark CPLEX rows are benchmark-only. Diagnostic
cuts do not enter certified paper rows.

## Readiness Decision

Not ready for broader benchmark claims. The compact-BC line is now better
accounted and fairer to compare, but `moderate_seed3301` did not certify,
V20 one-thread 300s certification is only 1/6 in this round, and large-V
compact-BC needs memory reduction.

Next targeted work should focus on:

- memory-safe compact model generation for V50/V100;
- true dynamic root separation using root LP/fractional solutions or callbacks;
- deeper low-Gini leaf strengthening for `moderate_seed3301`;
- longer single-thread controlled rows for `high_imbalance_seed3202` to
  reproduce the earlier certificate under fair thread policy.

Final pushed commit SHA is recorded in the final assistant response.  It is not
embedded here because a Git commit cannot contain its own final hash without
changing that hash.
