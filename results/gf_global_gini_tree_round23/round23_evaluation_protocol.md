# Frozen Round 23 targeted evaluation protocol

This protocol is frozen before observing an official candidate result.

The performance subset is exactly V12_M1, V12_M2,
high_imbalance_seed3202, high_imbalance_seed4201, tight_T_seed3101, and
moderate_seed4302. moderate_seed4301 is correctness-only. Instances may not be
replaced after a result is observed.

One clean Round 23 release executable is used for both arms. Runs are serial,
one thread, on the same host. S0-C and S0-M differ only in child-estimate mode:
`parent-copy` versus `dispersion-coupled`. Both use F0, presolve off,
Reduce=0, Linear=0, traditional search, native best-bound selection, full
inherited row packs, deferred rows, native MIP start off, default native cuts,
and exact-zero gap requests/readbacks.

Stage 1 runs both arms for V12_M2, high_imbalance_seed3202, and
tight_T_seed3101 under a 300-second process-wall budget and 282-second native
deadline. Stage 2 runs both arms for all six fixed instances under a 900-second
process-wall budget and 882-second native deadline. Heuristic, solve, logging,
serialization, and finalization time are inside the process budget. The same
18-second reserve policy applies to every row.

Stage 1 gates only correctness and structural integrity: solve finalization,
lifecycle, callback/coverage/column/estimate failures, verifier status,
feasibility consistency, exact parameter readbacks, telemetry presence, and
manifest identity. Performance does not cancel Stage 2.

Pair decisions follow the preregistered hierarchy: strict certificate,
process-wall strict time, common-UB final native LB, common-UB AUC, then tie or
unavailable. Common U values are frozen in `comparison_ub_manifest.csv`.
Plain data is reused from Round 22 because the parser, objective, plain writer,
plain baseline implementation, and plain certificate semantics are unchanged.
Plain evidence never enters a Tailored solve.

Failed, interrupted, or excluded attempts remain separate and never enter the
official summary. No portfolio, instance dispatcher, or F3 selection is
authorized.
