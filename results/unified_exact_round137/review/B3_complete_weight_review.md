# Independent completed-weight-panel review

Disposition: **PASS for the complete two-configuration weight panel and
inspected Section5.3 narrative**. Separate reviewer `/root/independent_review`,
2026-10-28 (Asia/Shanghai), while C1 production is active. This review reuses
the nine n20 checks in `B3_n20_weight_review.md` and reads only the additional
nine sealed n35 endpoint/qualification JSONs, launch metadata and authoring
source. No heavy reader, raw LP/journal, full aggregation, optimizer/build,
archive, PDF or native asset was used. Only this review was written; final120/
PDF acceptance remains pending.

## Counts and parameter identity

The full weight view has18 eligible observations: twelve newly run B3 positions
plus six actual B2 rho1 baselines. It represents two fixed physical
configurations × three rho values × three methods, not18 new inputs. The
new-B3-only stage has four extra objective configurations and GI-TBC1/4
certificates; the full weight view including baselines has GI-TBC2/6, versus
P0/6 and PS0/6. Across the study, the four extra weights raise20 physical
configurations to24 objective configurations while retaining16 base inputs.

The n35 view uses the same R-X35-S input SHA, T6300, Seed0, complete cap2400
and PE at every weight. Omega=13.261724; lambda=rho/Omega and floor scaling
match all nine launch/manifest records:

| rho | lambda | Positive floor |
| ---: | ---: | ---: |
| .5 | .0377024887563638 | .048873547662430614 |
| 1 | .0754049775127276 | .09774709532486123 |
| 2 | .1508099550254552 | .19549419064972245 |

All six PS/GI-TBC weight pairs across n20/n35 complete their independently
paid H, with matching nonempty64-character semantic and fleet hashes within
each weight. No across-weight H identity is required or inferred.

## Endpoint and proof interpretation

The earlier n20 conclusions remain: GI-TBC certifies at rho1/2 in784.143484/
309.113066s, while rho.5 is open for all methods. P and PS remain open at all
six physical/weight points of the full panel. Equal attained U at a weight
does not transfer another run's certificate/time.

All nine n35 observations are open with null T_cert. GI-TBC has lower U and
higher L than P/PS at each weight. The final rho2 values are:

| Method | U | L |
| --- | ---: | ---: |
| P | .6204431452400982 | .36178003909414147 |
| PS | .6118919449370832 | .36357213315065523 |
| GI-TBC | .5245527536064684 | .38843769204319056 |

The within-weight GI-TBC/PS primal difference is .08733919133061485 at rho2,
versus .0012952281510949515 at rho1 and .0018060910473023384 at rho.5.
The source correctly presents those as objective-specific finite endpoint
comparisons, not an across-weight algorithmic objective improvement, monotone
weight effect or complete-proof-time robustness. The nonclosed n35 gaps remain
visible; the points are not an exact optimal trade-off curve.

At rho.5, P/PS have opposed endpoints: PS U=.2576313710463639 is better than
P .26097830906922687, but P L=.10822328567959878 is higher than PS
.10801858574776797. GI-TBC U/L=.25582527999906157/.12233201951089322
improves both. The new paragraph retains that startup counterexample and does
not assign a certificate-time ordering.

The complete n35 paragraph, source assertions and shared-baseline counting
agree with these records. No further scientific correction was found in this
limited completed-weight scope. Plot/PDF rendering, actual second-Seed and
AM/mechanism outcomes and final integration are still subject to later review;
no healthy native rerun or larger parameter grid is needed for this review.

## 2026-10-28: limited operating decomposition checkpoint

Disposition: **PASS for the stated operating facts and scientific limits**,
not final integration acceptance. While native94 remained active, read only
the9517-byte `resource_weight_GI_operating_checkpoint.json`, its twelve sealed
GI-TBC small physical-evidence files (919955 bytes combined), small endpoint/
panel metadata and four small serialized input files. No audit, LP, native,
full aggregation, PDF or archive was used. Only this review was appended.

All twelve physical-file and endpoint SHAs match the checkpoint. Recomputed
G, P_avg, S and F=G+rho P_avg from the actual nondepot Y/target/weight arrays;
checked return vectors, pickup totals, duration/T and inventory conservation.
The recomputed components match the checkpoint/physical original objectives
within numerical tolerance. This verifies saved feasible plans, not exact
optimal operation at open points.

For all four B2 T1/T2 pairs, the saved GI-TBC plan has both lower G and lower
P_avg at T2. RX35 specifically has S=28.759126984126983 to28.223809523809525,
and return load1 to0. Here S=sum_i(Y_i/D_i), excluding the depot; it is not
sum_i Y_i. Indeed the station inventory total rises145 to146 in this pair,
consistent with one fewer returned bicycle even though S falls. Different
target denominators make these movements compatible.

The strict resource-value evidence remains the previously reviewed original
target separation L(T1)>U(T2), with four margins
.28226197612912823/.21052939956455918/.1112612656599235/
.06008599838541817. These margins were rechecked from the small sealed data.
Near-horizon maximum duration describes each attained route; it does not
establish an exactly binding optimal resource constraint or explain proof cost.

At the same RX35 physical input and T6300, the rho2 saved plan has
(G,P_avg)=(.14845887933113597,.1880469371376662), strictly below the rho1
saved plan's (.1825495914579768,.22072240740487795) in both components.
Both own runs are open with null certificate times. It is valid to say
**the saved rho2 feasible plan strictly dominates the saved rho1 feasible
plan in these two objective components**. This supplies an offline witness
of remaining primal improvement for the saved rho1 plan; it is not an exact
optimal trade-off curve, a monotone causal weight effect, or a general
algorithmic performance claim.

The offline comparison does not replace either run's own U/L, assign a new
certificate, transfer a Start or imply that the native runs borrowed a plan
across weights during execution. The checkpoint is a later physical summary
of separately sealed evidence. Final all120 analysis and manuscript/PDF review
remain outside this limited operating check.

Checkpoint SHA:
`d5f60e627f1cd0bf35b979c49b3afaabb269ac21ee427be68cc48b058587d731`.

## 2026-10-28: source-only shared-baseline analysis coverage amendment

Disposition: **PASS for B3 view construction/counting and the revised report
caption; preflight order is sound with the limited semantics below**.
Reviewed only analyzer/decision/document source excerpts, the959-byte
`infra/B3_shared_baseline_analysis_fix.json`, frozen matrix and plan metadata.
Native96 was still active. Did not execute main/preflight/gather, import heavy
readers, or read audit/LP/live96 files. Only this review was appended.

The plan already declares B3 rho1 sharing from B2. The metadata-only check
confirms the exact actual triplets:37/38/39 for R-B20-S-T1 and58/59/60 for
R-X35-S-T2. The latter's physical order is PS/GI/P; the source correctly uses
declared method keys rather than assuming position order. Each baseline
triplet matches its own input, T, lambda, Q, handling, cap and Seed0, with
rho1 as registered.

Baseline comparison orientation remains S2/P, S2/PS and PS/P. New records
receive comparison_kind=B3 and shared_baseline=true, while their source-stage
fields stay B2. Existing arms are not relabelled or copied into the native
position list. The four added weight targets yield twelve new method views;
the two rho1 triplets give eighteen full weight views, six target
configurations per method and six comparisons per contrast. Matrix keys are
unique across120 registered positions. The shared positions are exactly
[37,38,39,58,59,60]; no new input or native run is manufactured.

The summary deliberately retains B3 completion/certificate counts for its
twelve newly executed positions (four targets per method), while comparison
summaries cover all six targets. The decision report now explicitly explains
that distinction immediately between the position and paired-summary tables.
The manuscript's extra-weight design row and eighteen-row full-weight table
are consistent with it. No denominator or direction correction remains in
this inspected source. This is not a newly executed aggregation or new
scientific result.

`analysis_preflight()` is called before gather and all its large reads. It
first requires120 closeout/fee-receipt files, then the original driver return
with stop_after120 and no recorded unclosed fee, then the current budget's
no-unclosed condition. However, the inspected version checks closeout and
fee **existence with is_file**, not their semantic completion contents.
Describe this as a presence/idle preflight, not a fresh qualification of120
seals. If semantic completion is claimed here, additionally inspect the small
closeout necessary_verification_complete and corresponding fee-finalization
fields. Actual OS process and root-session exit still require the separate
operational confirmation already stated in the receipt. No current idle or
all120 completion claim is made by this review.

Frozen execution matrix SHA remains
`26f295da36097cd662b9c2ca049ab2452f0b295dfcdb12dd4b726ff25190c894`;
these offline analysis/authoring files are outside its frozen execution
helper table. Full120 materialization, root/cost/Seed1 integration and final
manuscript/PDF acceptance remain pending.

Reviewed analyzer SHA:
`f0c581718d92c827d9d182c7cd7b6d351e8660b0613023e242bac4b4b6f1ff86`.
Correction receipt SHA:
`b58eccd6662bf377836f8f1285324bd4486e6f1a333dfede79b4a0af7e0ef57b`.
