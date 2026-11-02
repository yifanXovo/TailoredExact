# Independent review of the finite NC-PC output

Reviewer: `/root/independent_math_review`. Date: 2 November 2026 (Asia/Shanghai). This is a bounded light read of the output, its small history/metadata and the current script/text while full runs are active. The reviewer did not execute the reconstruction, Optimize, compile, load Native, scan raw recursively or perform full aggregation.

**Disposition: PASS. No substantive mathematical or provenance issue was found.**

Inspected SHA256: `math/saved_point_NC_PC.json` is `7bf3a2b8eab96bebf506eaf8e7173fd61b6b085fae36c7a7c06b918e3fececfa`; `scripts/round145_offline.py` is `890fe0fd481a3ffe8ff9ef1cc55dfc9d5d946848c7f32c979ca9855ee91f3130`; mathematical analysis is `8eb837cf06cca86d0abac676dd0bafcd9c6491152c02b6a486c4364c3e2e253b`.

The reviewed `box_dual` body retains the earlier inspected endpoint, exact mass, subgradient and signed-row logic. The subsequent changes add gzip loading, point selection and provenance labels; they do not change the one-dimensional multiplier calculation. Actual selector masses remain rational binary64 values without normalization. The output explicitly identifies ideal exact NC2 based on actual binary64 ratios, distinct from production R140-down floating rows, and records zero Optimize/Native loading and exact box primal/dual identities.

| Role | Recorded violation / n | Difference from supplied rounded signal |
| --- | --- | --- |
| K35 | 0.086235264110508 | +7.99e-15 |
| RX20-T1 | 0.012514522443175217 | -2.478e-14 |
| K20 | 0.11390593691520633 | +6.33e-15 |
| RB35-T2 | 0.13404431115422097 | +2.10e-14 |

These agree with the four supplied rounded signals within 2.5e-14. They are saved-original-point separation results; neither the certificate output nor C4 relabels them as reoptimized objective gains or full algorithm benefits. Old TC2 violation is retained, so these values alone are not used to claim information beyond the strong old carrier.

RX20's distinction is explicit and necessary. The initial complete-production point has source SHA `67aead12ff69ce08b26f0bde7e879622075dc3a9a47bb9e274c4f38b7c8600db` and gives 0.013287136895526536. It remains in `math/history/first_production_point_reconstruction.json` (SHA `ffac9f59979ed871003967e5aa95c9f3e2e478b6bc440839f6348a3845db9183`) with its original zero-Optimize receipt. The final goal-matching RX20 point comes from the independently saved standalone production-capped RN LP, source SHA `5d5713b87ef3725b1fc87a3890eff8e0ac0311c6876663142e0a7450479e2635`, with a distinct point-evidence SHA and `point_kind`. That source SHA agrees with its sealed source-scope metadata.

The script keeps the complete-production model as the RX20 count-matrix authority but explicitly checks equality of the supports, actual rational ratios and reciprocal bounds before using the standalone point. Those are the relevant mathematical ingredients for this count/box certificate. Separate `source`, `source_SHA`, `evidence_SHA`, `count_matrix` and `count_matrix_SHA` fields prevent the two point identities from being confused. The different separator values are compatible with different numerical optimal points of a degenerate source; neither old output is discarded nor a new optimization introduced to force agreement.

C4 now explains the exact NC2 identity, preserved masses, standalone-versus-complete RX20 distinction, retained history and four evidence levels. It also retains the independent all-n algebra review while correctly attributing the earlier unrecovered finite Fraction checks to the supplied goal. The scope is finite proof/diagnostic reconstruction, with no production historical-cut injection or second complete algorithm. Full scientific and adoption review remains deferred until the entered complete results and final manuscript are sealed.
