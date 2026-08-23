# Round 40 final report

## Outcomes

1. **Was Round 39 presolve unfair?** No at the solver level: both P-GRB and the Gurobi fixed-interval C6 backend used Presolve Auto (`-1`). The `global-gini-tree-presolve off` label belonged to a different legacy/global-tree safety control and made the configuration look ambiguous.
2. **Fair policy going forward.** Uniform Gurobi Presolve Auto for P-GRB and every C6 LP, target MIP, and terminal MIP. The 8-row Off/Auto ablation preserves objectives/certificates and shows material performance distortion from forcing Off (for example, the positive witness changes from 93.897 to 63.208 s for P-GRB and 15.550 to 9.387 s for C6).
3. **Cause of Round 39 regressions.** It is heterogeneous. The major medium regression is dominated by proof fragmentation/repeated terminal work: K4 uses 8 integer jobs and 4373.078 Work versus K1's one job and about 3052.420 Work. Very easy/short P wins include irreducible HGA startup and C6 proof overhead. The strongest C6 control has the opposite mechanism: K4's narrower interval models are much stronger than one coarse MIP.
4. **Does simple K1 reduce fragmentation?** Yes. It wins 8/10 diagnostic cases, has median time ratio 0.757, and materially reduces the major regression.
5. **Did adaptive K1 solve the failure?** No. Original adaptive recreates jobs on the major witness; decisive adaptive preserves the K1-single recovery but cannot detect the strong control's coarse-MIP weakness.
6. **Improve regressions without losing strong positives?** Not uniformly. K1 still beats P-GRB strongly on the positive control (432.328 vs 6327.611 s) but loses 5.24x to K4 there. It also does not beat P-GRB on the major regression.
7. **Does incumbent-stable geometry reduce UB path sensitivity?** Structurally yes: all relevant boundaries are preserved on all 10 Round 36 pairs with different verified UBs. Empirically it wins 10/24, exactly resolves the numerical endpoint, but median time/Work ratios are 1.011/1.042; total time and Work are worse. No runtime-monotonicity theorem is claimed.
8. **Unified mechanism?** Not implemented: current complete LP evidence cannot safely select between K1 and decomposed K4, and adding outcome/timing/Work dispatch would violate the protocol.
9. **Credible replacement for frozen K4?** No. K1 has a severe strong-control regression; nested dyadic is neutral-to-negative in aggregate and leaves the major regression intact.
10. **Falsified mechanisms.** Universal K1, nondecisive `rho` refinement from a K1 root, proof-only decisive refinement as a protector against coarse-MIP weakness, and nested dyadic K4 as a performance replacement. Nested dyadic remains a positive exactness/geometry result, not a promoted runtime result.

## Exactness and protection

All 112 audited rows have accepted outcomes: 107 strict exact certificates and 5 predeclared fail-closed endpoint outcomes, with zero false certificates. The Part 2 candidate itself is strict on all 24 instances and resolves the endpoint. Three implicit-default/explicit-off pairs match on all 25 deterministic fields. The validated default was not changed.

## Recommendation

Keep `C6-HGA-FULL, K=4, rho=0.01` as the mainline. Use uniform Gurobi Auto presolve in future fair comparisons. Retain K1-decisive and nested-dyadic as explicit research arms; do not promote or merge behavior automatically.
