# Round 52 final report

## Decision

Round 52 is complete at the evidence level: all 48 entered validation/holdout method rows are present, satisfy the official strict contract, respect the 1800-second process cap, and are free of false certificates. The frozen classifications are `tau_008_adopted`, `gurobi_tailored_cut_infrastructure_complete`, `production_v0_backend_retained`, `k1_am_v0_final`, `pgrb_advantage_supported`, and `v12_v20_supported_v50_mixed`.

The benchmark label means an advantage **over** P-GRB. It is supported by all predeclared gates, but this is not a claim that every size class is solved: V50 remains mixed and has no strict certificate from either method.

## Frozen controller and evidence corrections

1. **Tau.** Tau 0.08 was adopted. The complete 334-row replay changed zero historical AM decisions relative to 0.07915; three paired runtime sentinels and one explicit/implicit default-off pair were action-equivalent.
2. **K1 labels and telemetry.** Round 50 action labels and root telemetry were corrected before reuse. Five of seven historical action labels changed; the corrected severe error count is three false retains and zero false splits.
3. **Plain LP.** All 15 frozen states passed `LP_M1 >= LP_v0 - 1e-7`; M1 did not enter the final backend.

## Tailored user-cut architecture

4. **Infrastructure.** The solver-independent candidate/separator/manager layers, deterministic global pool, dominance logic, strict scaled-violation test, Gurobi `GRBcbcut` callback, `PreCrush=1`, exception boundary, and telemetry are independently tested. The live fixture executed one successful native `GRBcbcut`; the production path remains default-off.
5. **Formulations.** The bounded study compared production v0; F0 with rank-3 support-duration rows removed and no dynamic cuts; F1 static rank-3 rows with the historical loose 100000 coefficient; F2 static rank-3 rows with exact TSP/permutation duration coefficients; and F3 dynamic exact-duration rank-3 rows with root-only block-max selection. F4 tree separation is implemented and unit-tested but was not opened as a benchmark iteration. The proof and unit census cover exact route lower bounds through rank 4, but rank 4 was not promoted into the bounded candidate.
6. **Cut census.** Across the 14-row core and 14-row complete-development panels, iteration 1 generated 1,705,140 candidates, found 4 strictly violated candidates, selected 4, added 4, rejected 0 duplicates, and rejected 0 dominated rows. Core alone was 852,570/2/2/2; total callback overhead was 11.171557 seconds. The complete per-state counts are in `cut_family_violation_census.csv`.
7. **Static congestion.** Dynamic separation avoided adding the large static subset-duration matrix and submitted only selected violated rows, so it did not reproduce the Round 51 static-row congestion. This engineering result did not translate into promotion-worthy solve performance.
8. **Iterations.** Iteration 1, SD-R3-ROOT-BLOCKMAX, was attempted. Iterations 2 and 3 were formally skipped because the required callback/`PreCrush` path itself lost complete-development certificates; changing the family would not remove that retained path.
9. **Rejections.** F1 and F2 failed certificate retention in the bounded screen. F3 retained the core certificate set but failed the 0.97 Work gate, then lost D1 and D13 on the complete development panel and gained no certificate.
10. **Second family.** No second cut family was opened; the predeclared trigger was not met after the callback-path failure.

## Final backend and integration

11. **Final backend.** The final inner solver is historical production v0: interval-mip-v0, support rank 0, no separation scope or selection rule, tailored callback off, historical 100000 subset-duration coefficients under the frozen V<=12 writer guard, Gurobi default branching, Presolve Auto, Seed 0, Threads 1, and zero MIP gaps.
12. **Fixed interval.** F0 certified 11/14 development states and F3 9/14. F3 lost D1/D13, gained none, and obtained a common-exact Work GM ratio of 0.977612 against the required 0.97. It therefore did not improve the promotion-level combination of Work, certificates, and GI.
13. **K1 integration.** Because the final backend is exactly historical production v0, no new integration method row was required. Twelve integration audit properties pass, the 334-row replay is action-equivalent, and the major and strong-control repairs remain RETAIN.

## Independent comparison

14. **Validation.** K1-AM-FINAL certified 7/12 versus P-GRB 3/12, gaining 4 and losing 0. Its shifted Work GM ratio is 0.658881, shifted process-time GM ratio 0.565376, and aggregate GI ratio 0.468701.
15. **Sealed holdout.** K1-AM-FINAL certified 6/12 versus P-GRB 3/12, gaining 3 and losing 0. Its shifted Work GM ratio is 0.511427, shifted process-time GM ratio 0.463308, and aggregate GI ratio 0.445539.
16. **Severe regressions.** The frozen exact/capped rule finds 0 severe P-GRB regressions, including zero on holdout.
17. **Scale.** Combined subgroup evidence is:

| size | P-GRB certs | K1 certs | K1 gains | Work GM ratio | GI ratio |
| --- | --- | --- | --- | --- | --- |
| V12 | 6 | 7 | 1 | 0.436197 | 0.468547 |
| V20 | 0 | 6 | 6 | 0.374232 | 0.435809 |
| V50 | 0 | 0 | 0 | 1.198293 | 0.487612 |

V12 and V20 support the comparison across two size classes. V50 shows materially better gaps/GI for K1 on many rows but worse Work and no strict certificate for either method, so the correct qualification is `v12_v20_supported_v50_mixed`.
18. **Algorithm description.** It is legitimate to describe the full method as an exact tailored K1-AM search/controller using a frozen exact production-v0 interval MIP backend. It is not legitimate to describe the **final inner backend** as dynamic branch-and-cut, because the researched user-cut policy was rejected and is off.
19. **Unproven.** Dynamic support-duration cuts are not shown beneficial beyond the bounded panels; V50 exact scalability is unproven; performance beyond the frozen generator distribution, machine, executable, and 1800-second cap is unproven; and no claim of a universally validated paper algorithm is made.

## Reproducibility and scope

The validation and holdout panels use one executable SHA-256, `d245c76f6397c757894610d8f5238cfeb971761ff7e05edf51058e451d810151`. All 24 instance-method pairs use the frozen inputs, Threads=1, Seed=0, Presolve=Auto, zero MIP gaps, and the same process cap. Invalid fingerprint-discovery attempts are retained locally and explicitly excluded. Full raw logs remain local under `local_raw`; committed ledgers carry their hashes and reproduction anchors.
