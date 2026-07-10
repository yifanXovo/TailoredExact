# Dominant Bucket Structural Cut Round

Status label: `compact_bc_needs_structural_low_gini_strengthening`.

Final commit SHA: recorded in the Codex final response; embedding the exact self-referential SHA in this tracked file would change the commit hash.

Target: `moderate_seed3301`, low-Gini interval `[0.0122881381662, 0.0245762763324]`, dominant S bucket `[16.59546103547, 23.272821182835]`, old cutoff `0.0491525526647`.

## Required Answers

1. Complete callback/root vector parsing succeeded. The round wrote `17220` callback-vector rows and `23649` root-LP-vector rows. Missing quantities are labelled unavailable; no missing vector values are zero-filled.

2. Dominant static root values: `S=20.19106430348409`, `P=0.16707394042433668`, `H=8.036227884863253`, `G=0.015516153171051544`, `W_SP=2.7726690683547552`. Static callback values: `S=20.187451100631584`, `P=0.16884315531485783`, `H=7.853307835041007`, `G=0.016764828795065082`, `W_SP=2.802030005133801`.

3. Static root G-S-H gap was `0.004384303199335414`; with GS coupling callback snapshot it became `-0.0009283349809778713`, so the coupling removes the observed positive G-S-H relaxation slack at the sampled relaxation point.

4. Static root SP gap was `0.6007316061894965`; static callback SP gap was `0.606482936461235`. Disaggregated SP rows were generated (`81` rows), but at 300s they did not improve the final bound beyond the static tailored baseline.

5. Vector-route cuts reduced the branch tree size (`183` nodes in vector-only at 300s) but harmed the bound (`LB=0.0429769807153`). The cutset rows are valid, but this static all-subset deployment is too heavy/degenerate for this bucket.

6. GS product coupling improved the 300s bound most: `LB=0.0487181971446`, gap-to-cutoff `0.0004343555200999952`.

7. A 14400s matrix was not started in this run. The runner supports the required long rows, but this committed evidence is the 300s dominant-bucket matrix plus 300s sanity rows.

8. No new variant closed the dominant bucket. Best 300s row remains open by `0.0004343555200999952`.

9. No new fixed-interval improving solution was imported or promoted. This round did not use the prior 14400s fixed-interval incumbent as UB.

10. Paper-safe by default: GS upper coupling, disaggregated SP estimator, support-duration covers, and directed route cutsets. GS lower/equality row remains off by default and is not used as paper evidence.

11. Non-regression sanity: `high_imbalance_seed3201_hard` closed at 300s, `tight_T_seed3102_hard` closed at 300s, and `low_gini_2` remained open with gap-to-cutoff `0.0007780419706999997`. No crash or audit regression was observed.

12. UB import/full-frontier rerun: no.

13. Remaining weakness: low-Gini objective-denominator coupling is still weak. GS coupling helps substantially; disaggregated SP alone is neutral at 300s; vector cutsets currently hurt the dominant bucket when added statically.

14. Recommended next step: keep GS coupling in the paper-safe candidate set, disable static vector-route cutsets for this bucket, and develop callback-separated/violation-filtered GS/SP rows or narrower adaptive S buckets for the remaining `4.34e-4` cutoff gap.

## 300s Dominant Bucket Matrix

| variant | LB | gap-to-cutoff | status |
|---|---:|---:|---|
| gs_product_coupling | 0.0487181971446 | 0.0004343555201 | unresolved timeout |
| static_tailored_compact_bc | 0.0483881628340 | 0.0007643898307 | unresolved timeout |
| disaggregated_sp_estimator | 0.0483881628340 | 0.0007643898307 | unresolved timeout |
| gs_plus_disagg_sp | 0.0483881628340 | 0.0007643898307 | unresolved timeout |
| plain_fixed_interval_mip | 0.0455082511430 | 0.0036443015217 | unresolved timeout |
| current_best_new_combined_paper_safe | 0.0441094021110 | 0.0050431505537 | unresolved timeout |
| all_new_structural_cuts | 0.0440671889108 | 0.0050853637539 | unresolved timeout |
| vector_route_structural | 0.0429769807153 | 0.0061755719494 | unresolved timeout |

## Audit Summary

All required audits run on the final `results/gf_tailored_bc_structural_cut_round/raw` directory passed: certificate audit, Tailored-BC callback audit, summary cleanup, thread fairness, objective convention, timeprofile finalization, paper-strict algorithm audit, no-instance-special-case audit, callback vector parser audit, vector structural summary audit, GS coupling audit, disaggregated SP audit, and vector route cut audit.
