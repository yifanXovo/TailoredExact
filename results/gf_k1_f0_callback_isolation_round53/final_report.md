# Round 53 final report

## Decision

Round 53 is **complete** at the evidence level. The bounded classifications are `f0_fixed_interval_supported`, `mixed_callback_regression`, `f0_backend_promoted`, `k1_am_f0_supported`, and `sealed_v12_supports_candidate`. This does not establish a universally validated paper algorithm.

## Answers to the frozen research questions

1. **F0 definition.** F0-CLEAN removes only the historical exhaustive V<=12 subset-duration row block from the Round 50 v0 canonical interval MIP. It adds no row, cut, callback, PreCrush setting, symmetry rule, branching rule, or dispatch.
2. **Integer feasible set.** Preserved. Every removed inequality follows from the core route-duration bound and a valid route-duration lower bound for its support; all audited historical coefficients dominate that lower bound. Independently reconstructed incumbents remain feasible.
3. **Size.** Across the frozen state audits, 120,540 row observations and 1,433,600 nonzero observations were removed. Per-state values are in `f0_formulation_size_audit.csv`.
4. **Activity.** 0/120,540 removed row observations were active at scaled 1e-7 and 0/120,540 had absolute dual above 1e-9.
5. **Plain LP.** The exact objective comparisons are in `f0_plain_lp_comparison.csv`; no favorable claim is inferred from size alone.
6. **Root/node cost.** `f0_node_lp_cost_analysis.md` and the paired fixed-state ledgers record root Work, presolved size, nodes, and iterations per node.
7. **Development.** 28 physical rows completed; the common-exact Work GM ratio was 0.542494 with 0 severe regressions.
8. **Confirmation and proof tails.** 18 confirmation and 12 long rows completed. Their Work GM ratios were 0.509424 and 0.414713; no baseline certificate was allowed to be lost.
9. **Callback source.** The causal classification is `mixed_callback_regression` from the complete C0-C5 matrix.
10. **PreCrush.** Its isolated effect is C1-C0 and C3-C2 in `callback_isolation_pairwise_effects.csv`; it was not conflated with separator work.
11. **No-op MIPNODE.** Its isolated effect is C2-C0 and C3-C1 in the same ledger.
12. **Separator enumeration.** C4-C3 isolates relaxation extraction and dry-run enumeration while guaranteeing zero `GRBcbcut` calls.
13. **Actual submission.** C5-C4 isolates submission; C4 submitted zero cuts by construction and telemetry.
14. **Bounded rescue.** Not opened. F0 passed the entered fixed-interval qualification ladder, so the conditional rescue gate did not apply.
15. **Frozen inner backend.** The evaluated candidate is F0-CLEAN with Gurobi Auto/Seed0/Threads1/zero gaps, default branching and PreCrush, no callback, and the Round 50 core otherwise unchanged.
16. **Major repair.** Full K1 integration reports `major_repair_preserved=True` with K0=1, one initial complete interval, midpoint, and tau=0.08 unchanged.
17. **Full K1 effect.** Integration—not isolated-MIP performance—passed=True; all entered 300/1800/conditional-3600 rows are retained.
18. **Sealed panel.** Opened only after source, executable, candidate backend, and integration were frozen; 36 3600-second rows completed.
19. **Versus K1-AM-v0.** Sealed candidate/v0 shifted Work GM=0.262842, GI ratio=0.336210, certificate gains/losses=1/0.
20. **Versus P-GRB.** The candidate had 0 severe P-GRB regressions under the frozen rule; direct values are in `sealed_v12_direct_comparison.csv`.
21. **M/Q breadth.** Benefiting configurations: M2-Q20, M2-Q30, M3-Q20, M3-Q30; the sealed panel spans M=2/3 and Q=20/30 without filtering.
22. **Replacement decision.** F0-CLEAN. The research policy remains explicit/default-off; no paper-facing preset was silently changed.
23. **Unproven.** Behavior beyond the frozen states, generator distribution, machine, Gurobi version, time horizons, and V12 sealed panel remains unproven; V20/V50 evidence is limited to identity/dispatch sentinels.

## Evidence integrity

The certificate audit contains 160 rows, 0 false certificates, and 0 correctness failures. Missing entered rows: none. The official exact executable SHA-256 is `b49cc5a5e631c6a8ce7a8bd4d0e6da44162800c97996494b1ee6a04071286c85`; the fixed-interval harness SHA-256 is `7f8bc2b5c36d552d5d9c405cb85bac64ce68e6fa4eae91b4dff33ad7f7a0de52`.
