# Round 50 final report

## Outcome

`Interval-MIP-vNext` is frozen as exact `Interval-MIP-v0`: Gurobi default branching, the original v0 cut/formulation pack, v0 nonincreasing route-use-cardinality symmetry for identical vehicles, and no numerical or model-reuse change. Fixed-state promotion failed because C1 exposed an honest strict-certificate correctness failure and the unchanged backend has an exact-row Work ratio of 1.0 rather than the required 0.95. K1 integration was therefore correctly not opened. All 7 retain/split labels were recomputed under the frozen retained backend; 4 severe split errors remain, but the LP-tail stage was not eligible because K1-AM-vNext did not complete qualification. Draft stacked PR: https://github.com/yifanXovo/TailoredExact/pull/104.

## Required questions

1. **Dominant bottlenecks.** Hard states combine weak root bounds, excessive nodes, high iterations per node, delayed incumbents, expensive root LPs, and in D9/D11/D13 excessive root cuts. Model build was negligible (maximum observed share 0.002741), and size alone was not used as diagnosis.
2. **Branching policies.** B1 primitive-first, B2 route-first, and B3 operation-first were tested with uniform ordinal tiers.
3. **Semantic branching result.** No policy passed. B1 lost D3/D13 certificates and severely regressed D14; B2 lost D4/D10 core certificates; B3 severely regressed D4. Default Gurobi branching was retained.
4. **Essential cut families.** Core feasibility/model-definition and exact-reformulation families are protected. The retained strengthening pack includes direct Gini bounds, interval-tight McCormick rows, objective-estimator cutoff, penalty closure, Gini spread, required movement, low-Gini/variable-s centering, and the SP-product estimator.
5. **Redundant or expensive families.** Exact zero-bound mode-link duplicates exist (51 rows over development states). Root cut activity is high on D11/D13, but the audit found no separately delayable family with a complete exact separator and no empirically safe family removal.
6. **Cut changes.** C1 exact duplicate elimination was tested and rejected after D12's native-optimal point missed the independent original-objective certificate tolerance. No cuts were delayed, strengthened, or added; generic Gurobi Cuts settings were unchanged.
7. **Exact symmetry.** Yes. Identical vehicle capacities make vehicle labels interchangeable in every frozen multivehicle state. S1 route-start ordering and the used-first revision each passed 14-state model-delta proofs, but both lost D13's v0 certificate and were rejected. The v0 cardinality representative remains.
8. **Big-M/bounds.** No additional uniform analytic tightening was proved, so none was tested or accepted.
9. **Model/basis reuse.** Not opened. The fixed-state chain builds one MIP and has no already-solved corresponding LP object; build share was too small to justify a different model chain.
10. **Rejected changes.** B1/B2/B3, C1, S1, and S1-R1 were rejected for the certificate, correctness, or severe-regression failures above. R1 and a numerical candidate were audited but not opened.
11. **Exact vNext definition.** Default branching; original v0 cut/formulation; v0 cardinality symmetry; no numerical change; no reuse; Presolve Auto, Seed 0, Threads 1, MIPGap/MIPGapAbs 0; no runtime/instance dispatch.
12. **Development improvement.** No. The 14-state 300-second frozen result is definitionally v0, and the 1,200-second logical comparison shares the same physical runs.
13. **Confirmation improvement.** No. The 9 confirmation states have a Work ratio of 1.0 and no proof-progress difference.
14. **Severe fixed-state regression.** No vNext-versus-v0 severe regression occurred because the runs are identical. C1 is a correctness failure, not a promoted regression.
15. **Strong control.** Fixed D3/D4/D5 are exact at Work 349.018/129.528/8.362 under both names. In the recomputed parent counterfactual, MIDPOINT is severely better: 147.530 Work and 84.221 s versus RETAIN 740.634 Work and 409.322 s, both exact.
16. **V12 M2.** Fixed D6/D7/D8 are exact and unchanged. The matched parent counterfactual confirms MIDPOINT: 9.651 Work versus RETAIN 38.809, both exact; the absolute difference is below the frozen severe threshold.
17. **tight3102.** Fixed D9 is capped while D10/D11 certify. The matched L0.0 counterfactual is a severe false retain: MIDPOINT certifies at 1500.198 Work; RETAIN is capped at 2476.505 Work and gap 0.07370.
18. **V20 difficult intervals.** Across D9/D10/D11/D13/D14/C3/C4/C5, 4 of 8 certify and 4 cap, identically for v0/vNext. Counterfactual midpoint is severe-better on tight3102 and high3201; moderate3301 remains capped/capped.
19. **K1-AM-vNext versus K1-AM.** No integration row was eligible because the backend accepted zero changes and failed Stage 4. The retained algorithm is historical K1-AM; no claim of a new K1 candidate is made.
20. **Versus P-GRB.** No P-GRB rerun occurred. The required benchmark label is `k1_am_vnext_pgrb_mixed`, inherited only as contextual historical K1-AM evidence, not as a new contemporaneous advantage.
21. **Gap to K4-AMC.** It remains unclosed and unquantified by a new matched K1 run; historical K4-AMC is contextual only.
22. **Major regression.** Under the retained backend, the major parent still favors RETAIN: it certifies at 843.456 Work while one midpoint split caps at 2651.321 Work and gap 0.03330. The historical K1-AM major repair is therefore preserved, not newly improved.
23. **New labels.** major=RETAIN; strong=MIDPOINT; numerical-endpoint=MIDPOINT; V12/M2=MIDPOINT; tight3102=MIDPOINT; high-imbalance=MIDPOINT; moderate3301=MIDPOINT.
24. **Label changes.** No previously resolved label changed. Numerical-endpoint, high-imbalance, and moderate3301 moved from unresolved to MIDPOINT.
25. **Severe split errors.** Yes: major is a severe false split; strong, tight3102, and high-imbalance are severe false retains.
26. **LP tail opened.** No. Backend freeze and severe-error gates pass, but K1-AM-vNext qualification did not occur, so Gate 2 fails.
27. **Rules tested.** Zero.
28. **Split-rule success.** None was eligible or tested; the original AM gate remains unchanged.
29. **Primary-candidate readiness.** No. The K1 classification is `historical_k1_am_retained`.
30. **Unproven.** No uniform branch/cut/symmetry/reuse improvement is supported; K1 behavior with a genuinely improved MIP backend remains untested; the four severe split labels remain unrepaired; V20 qualification is negative; no claim beyond this frozen machine/Gurobi/evidence contract is made.

## Counts and correctness

- Fixed Stage 1: 14 physical v0 rows.
- Fixed confirmation: 23 physical runs represented as 46 explicit logical v0/vNext rows; 17 exact, 5 capped, 1 honest failed row, 0 false certificates.
- K1 integration: 0 physical/logical rows, formally not opened.
- Counterfactuals: 14 physical rows/7 pairs; 9 exact and 5 capped/not-exact, 0 false certificates.
- Verification: full build 100%; 28/28 CTests; 162/162 historical and 22/22 Round 50 protocol tests.
- Missing entered-stage rows: none.

## Final classifications

- Fixed interval: `interval_mip_v0_retained`
- Branching: `default_branching_retained`
- Cut/formulation: `original_cut_pack_retained`
- Reuse: `model_reuse_not_opened`
- K1: `historical_k1_am_retained`
- Split: `severe_split_error_remains`
- Benchmark: `k1_am_vnext_pgrb_mixed`
- Scale: `v20_negative`
