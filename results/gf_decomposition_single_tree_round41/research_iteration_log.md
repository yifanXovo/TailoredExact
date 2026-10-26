# Round 41 research iteration log

## Baseline and audit

1. Checked out `codex/round41-decomposition-single-tree-feasibility` directly from Round 40 commit `3db7a5efbace14dfed7557560e96636f749b84bc`; unrelated tracked and raw local files were left untouched.
2. Ran the three pre-implementation implicit-default/explicit-off pairs with the unchanged Round 40 executable. All 25 deterministic fields and trajectory hashes matched in every pair.
3. Audited the Round 19 CPLEX persistent tree, Round 20 regression diagnosis, Round 28 Gurobi replica, current fixed-interval backend, installed Gurobi 13.0.2 header, and official Gurobi callback/model documentation. The audit rejected direct callback migration and selected static pre-optimize construction.

## Formulation iterations

1. Implemented ST-K2-I in the canonical LP writer: midpoint selectors, exact G/Y/S/P aggregation, infeasible-selector fixing, and the complete interval-row-factory packs as native indicators.
2. Implemented ST-K2-P-Core uniformly for every inventory expansion bit: selected `G_k`, selector/bit activations, perspective products, and exact sum-back equations. The original interval-tight McCormick indicator rows are replaced, while every other family stays present.
3. Implemented one predeclared Extended pack with selected `S_k`, `P_k`, `H_k`, and `WSP_k`. It replaces direct Gini, objective estimator, penalty closure, and SP estimator rows uniformly; it does not disaggregate routing or stationwise decisions.
4. Added one-model/one-optimize execution, strict certificate gating, original/presolved size, fractionality, and McCormick-ambiguity telemetry.

## Engineering gates

- The first native ST-K2-I root model loaded with nonzero Gurobi general-constraint count.
- The zero-objective easy sentinel certified with one static model, one terminal MIP optimize, one verified original solution, and no auxiliary-decoding dependence.
- On the nontrivial V8/M3 sentinel, I, Core, and Extended all returned the same independently verified objective with strict certificates. Core and Extended increased Work/nodes relative to I on this sentinel.
- Root-LP runs explicitly rejected certificates.
- Algebraic tests cover exact geometry, integral selector/bit products, valid fractional perspective points, selected continuous copies, and default-off options. Static protocol tests cover the emitted aggregation rows, one-call mechanism, panel/gate freeze, native smoke, certificate behavior, and post-default equivalence.

## Frozen progression rule

`decision_gates_frozen.json` was written after exploratory smoke/root evidence but before the two named confirmation MIPs. It requires success on both opposing mechanisms and forbids capped noncertificates from counting as passes. K4 and held-out expansion require Gates A, B, and C; no outcome-dependent threshold revision is permitted.

The first fragmentation-witness MIP was interrupted and retained under `runs/invalidated_pre_aggregation__...` after a source audit found that safe `S` and `P` domain aggregations were still only indicator activated. It produced no result/certificate and is excluded. Fourteen pre-aggregation runs are retained under `runs/invalidated_pre_aggregation/`.

After adding the direct K1/left/right root-reference API, the executable hash changed. Thirty-three otherwise valid static runs from the preceding binary were retained under `runs/invalidated_pre_final_api/`. A final provenance audit also moved ten older external-K2 scheduler diagnostics into `runs/invalidated_pre_final_api/external_k2_diagnostic/`; the direct final-hash one-interval LPs supersede them. Every official root and MIP row was regenerated from final executable SHA-256 `572834f01bf923ae0026300b4f6a5b88f9ca78db27cc0bb38b39938de836fcdd`. No invalidated raw evidence was deleted.

## Confirmation result

1. Completed 30 direct one-interval roots, 30 final-hash static roots, and 30 final-hash static MIPs over the unchanged ten-instance panel.
2. Twenty-seven static MIPs issued strict certificates. The three other rows were accepted noncertificates: one native time limit and two fail-closed native-bound residuals. The independent verifier passed every incumbent and the false-certificate count is zero.
3. Core captured essentially all external-K2 root improvement wherever the denominator was positive, with maximum variable growth 1.474 times ST-K2-I.
4. On the fragmentation witness, Core used 0.428 of external K4 exact-phase time and 0.433 of its Work and one integer job, passing the frozen half-gate.
5. On the strongest K4 positive control, Core used 0.242 of K1 time and 0.248 of K1 Work, but 1.313 of K4 time and 1.371 of K4 Work. The frozen 1.25 K4 ceilings failed.
6. Final gates are A pass, B pass, C fail. Consequently Gate D (ST-K4) and Gate E (held-out validation) were not opened.
7. Repeated the post-implementation default-off audit with the final binary. All three implicit/explicit pairs match in all 25 fields, all trajectory hashes match within each pair, and every pre/post trajectory hash is identical.

The final recommendation is to retain the validated C6-HGA-FULL K=4, rho=0.01 default. Core remains an explicit default-off research arm; no automatic promotion or merge is authorized.
