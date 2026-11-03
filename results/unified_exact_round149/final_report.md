# Round149: penalty floors in state-product envelopes

Decision: **RESEARCH_ONLY_PENALTY_PRODUCT_FEEDBACK_NO_PROMOTION**.

Retain frozen penalty-product feedback as research only; do not recommend the current uniform D+PF implementation as a paper enhancement. Three same-domain product LP increments and block validity are established. K35 gives a real 2.00348% physical-U improvement and 6.69155% smaller signed gap with 0.87754% lower supported L. RB35 instead loses 3.08518% in physical U, gains 2.26970% in L, and has 4.62638% larger signed gap. This is not a trigger of the inherited severe double-open reference rule, but it gives up important standalone-D incumbent value. The one final K20 proof clarification returns identical U, no certificate on either arm, and a slightly lower PF L. That supplies no proof advantage to justify the mixed hard-role tradeoffs. All six formal own-H arms use the same new PE and original matched windows. Keep the valid implementation and complete evidence; preserve stable R137 and R147's previously limited D candidate. This finite known-Seed0 result neither invalidates the propagation family nor establishes broader robustness. No further experiment is queued.

The study separates four claims. The resource floor and integer validity are mathematically established; the product block is strictly stronger; three same-domain numerical LP increments are positive; complete algorithm value is assessed only by the entered new-PE own-H pairs below. No historical beta or incumbent is injected into a complete arm.

## Entered complete results

| Role | Method | Physical U | Supported L | Signed U−L | Relative gap % | Certified | T_produce | T_cert | T_verify | T_total |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| K-35-U | D | 0.676798845196 | 0.545729444783 | 0.131069400413 | 19.366079 | False | 2371.146937 | — | 7.683751 | 2378.830688 |
| K-35-U | D_PF | 0.663239294207 | 0.540940474850 | 0.122298819357 | 18.439622 | False | 2371.170972 | — | 14.913482 | 2386.084454 |
| R-B35-S-T2 | D | 0.335883588950 | 0.219657578677 | 0.116226010272 | 34.603063 | False | 2371.397338 | — | 7.344774 | 2378.742112 |
| R-B35-S-T2 | D_PF | 0.346246203574 | 0.224643138352 | 0.121603065222 | 35.120404 | False | 2371.086629 | — | 12.124699 | 2383.211327 |
| K-20-S | D | 0.716806546278 | 0.704552496300 | 0.012254049978 | 1.709534 | False | 1172.037299 | — | 38.725127 | 1210.762426 |
| K-20-S | D_PF | 0.716806546278 | 0.703950558029 | 0.012855988249 | 1.793509 | False | 1172.082794 | — | 46.057038 | 1218.139832 |

U is recomputed from the physical fleet and original objective. L is the external supported proof-cover lower value. Open T_cert entries are null. Complete arms pay their own H, construction, all LP/MIP calls and necessary verification. Small cap-near total-time differences on open runs are not convergence or certification speed. All admitted difficult windows were retained.

## Comparisons and search observations

For K-35-U, PF changes U by -0.013559550988, L by -0.004788969933, signed gap by -0.008770581056, and relative gap by -0.926457 percentage points. U improvement is +2.003483% and L improvement -0.877536%. Serious double-open regression under the inherited reference rule: False.

For R-B35-S-T2, PF changes U by +0.010362614624, L by +0.004985559675, signed gap by +0.005377054949, and relative gap by +0.517341 percentage points. U improvement is -3.085180% and L improvement +2.269696%. Serious double-open regression under the inherited reference rule: False.

For K-20-S, PF changes U by +0.000000000000, L by -0.000601938272, signed gap by +0.000601938272, and relative gap by +0.083975 percentage points. U improvement is +0.000000% and L improvement -0.085436%. Serious double-open regression under the inherited reference rule: False.

| Role | Method | Initial formal LP L | Printed Native root-after-cuts | Final supported L | Native Work (all calls) | Simplex iterations | Terminal nodes | Outer splits |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| K-35-U | D | 0.204187028164 | 0.44681 | 0.545729444783 | 4732.628700 | 7815897 | 16122 | 0 |
| K-35-U | D_PF | 0.206104958905 | 0.44823 | 0.540940474850 | 4683.709443 | 5696660 | 12456 | 0 |
| R-B35-S-T2 | D | 0.135292103721 | 0.18147 | 0.219657578677 | 5616.158906 | 6301173 | 6765 | 0 |
| R-B35-S-T2 | D_PF | 0.135404155912 | 0.18120 | 0.224643138352 | 5474.898256 | 5945567 | 7484 | 0 |
| K-20-S | D | 0.236010302342 | 0.55900 | 0.704552496300 | 1911.302111 | 8615858 | 392090 | 0 |
| K-20-S | D_PF | 0.237043344714 | 0.56100 | 0.703950558029 | 1980.053016 | 8966684 | 373556 | 0 |

The LP, printed Native root-after-cuts and final supported L are different evidence layers. Witness trajectories, per-target logs/Work and AM records are retained in reports and raw carriers. Keeping the AM geometry does not keep Native target/search paths identical. These observations locate changes without uniquely attributing them to one static row, branch, target or AM decision.

## Mathematics, LP signal and qualification

See mathematical_analysis.md for the continuous-resource primal/dual construction, outward floor and upward beta, whole-block facet implication, strict example, valid nonminimal completions and compatible child/proof-cover scope. The scalar G bound was already implicit in the old LP. LP_report.md gives three positive PF optima and one redundant scalar control. All old variable domains and objective semantics are retained. No extra root LP, new column or source optimization is added.

The K35 PF floating primal-dual diagnostic difference is about .000619046, while its diagnostic dual still exceeds the old saved primal. Scalar-only differs by -3.225e-7 within the inherited quality tolerance. The resource arithmetic uses exact diagnostic certificates; the actual LP optima are qualified floating evidence, not exact rational optimality proofs. No old LP or tiny-gap search was repeated.

Qualification includes exact actual-weighted resource primal/dual checks, positive/zero floors, safe coefficient direction, real writer and Native matrix readback, child domination/compatibility, OFF, complete and feasible nonminimal g/e Starts, SHA-selected zero-GD context, actual dry CLI and one short cap90 own-H producer. All existing accepted H, physical input/objective, Start, quality, lifecycle and R134 proof predicates are reused. The short producer is a health check, not a performance comparison.

Two no-Optimize fixture corrections are preserved: raising e requires a compatible W_SP completion; a fixed W_SP box can forbid nonminimal e, and r_max must not be counted as a station ratio. A separate boundary test initially assumed an old RB35 GD block had zero rows; the mistaken test assumption is preserved and corrected. None required a production source change, old qualification panel or extra baseline Optimize. The current zero-GD matrix test labels its synthetic call wrapper explicitly.

## Historical and adoption boundaries

R137 GI-TBC remains stable. R147 D remains its previously limited unified enhancement candidate: known Seed0 hard-role U gains do not establish broad robustness, and K20 was unproved and K35 L once declined. K20 STOCK/STOCK+GD certification around94.261/74.916s remains strong prior evidence. R140 TC+STOCK Seed0 K35 U/L≈.650438712/.5682885263 and RB35≈.3190804927/.2339272621 remain stronger historical endpoints; accompanying Seed1 losses and source/PE/V2 transport differences prevent interpreting them as pure seed interventions.

R47 eta/mu, R48/R49 primal-dual/formulation work, corrected R52 three severe false-retains and its true correct-retain negative anchor (parent Work≈843.456 proved; forced midpoint≈2651.321 capped), and R130/R137 root-only evidence are preserved. R119 dynamic incumbent rebuilding and R120–R122 domain/conditional propagation are distinct predecessors. R131 left this product feedback incomplete. R88, R133, R144 and R145 remain context, not an obligation to replay a historical grid.

R148 produced positive five-model/three-instance Shared-S LP increments but a serious RB35 incumbent/signed-gap loss. It remains research only. This round does not rescue it through Shared-S/STOCK/RN/AM combinations, extra seeds, instance-name switches or timed algorithm switching. The present decision concerns only the frozen PF implementation and entered known Seed0 scope.

## Cost, identities and reproducibility

cost_report.json counts all new outer experiment, qualification, failure and necessary verification once, including complete own H. Nested solver Runtime/Work is descriptive, never added a second time. Necessary compile time and pure manuscript/public I/O are separate. The ceiling is18000s; released nominal capacity is never counted twice. No more optimization is queued.

candidate_manifest.json and identity_index.json separate production source, PE/DLL, executed wrapper/helper, fixed scientific and delivery identities. The default-off research entry is scripts/paper_s2_penalty_feedback.py with config/gi_tbc_penalty_feedback_round149.json; --pf off uses the same new PE control. Original profiles, historical evidence and the protected user tree retain their bytes. New carriers contain necessary incremental evidence; fixed R146 references avoid copying old large history. Independent final review, public recovery and bounded current-round cleanup are recorded separately.

The formal scopes are K35: 35 stations / 3 vehicles, physical T10800, lambda .15, cap2400; RB35-T2: 35/3, T7200, rho1, original lambda 1/Omega, cap2400; K20: 20/2, T5400, lambda .15, cap1200. All use Seed0/Threads1, H seed20260626, pair-only, AM .08, depth8, width1e-4, AP off, Shared-S/STOCK off. No RX20 full arm, extra seed or other clarification is entered.

The RB35 reference-rule flag is false: its U loss is below 5% and its signed-gap loss is below 25%. The adoption decision instead reflects the complete mixed value and the absent K20 certification gain. This is not an all-cases-must-win rule. K20 necessary verification extends complete totals beyond the nominal production cap; the actual extra time is retained and charged from the reserved verification capacity.

<!-- ROUND149 COST -->
Charged new experimental outer cost: **12060.885540600s / 18000s**. Necessary build: **56.177043000s separately**. All 35 complete/qualification Native calls returned; four standalone diagnostic LP calls are separate. Public I/O and offline authoring are separate.
