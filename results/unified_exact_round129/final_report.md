# Round129 final report

Execution: **COMPLETE**. Scientific recommendation: **`RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE`**.

The five fixed conditions support recommending uniform MS2 as the single method candidate for the next paper revision. This is a recommendation awaiting the user's adoption; the current method identity and historical full-M-B tables remain unchanged.

Four new problems, one existing protection role, thirty complete independently paid arms, ten serial groups and thirty typed shared-data comparisons were frozen before once-only generation. No tuning, redraw, additional role/Seed, extended cap or performance retry was used. Two Seeds are not two new problems.

## Candidate conditions and certification risk

| Fixed condition | Requirement | Satisfied |
| --- | --- | --- |
| 1 | Retain per-Seed and both-Seed new-problem certification counts relative to MB | True |
| 2 | Add no per-Seed P-certified/method-open risk relative to MB | True |
| 3 | Retain every protected MB certificate and avoid a large slowdown at both Seeds | True |
| 4 | One new input has eligible triple deletion and material MS2/MB support at both Seeds | True |
| 5 | One new input gives direct MS2/P certification Wins at both Seeds | True |

| Seed | P certified | MB certified | MS2 certified |
| --- | --- | --- | --- |
| 0 | 1 | 2 | 2 |
| 1 | 1 | 2 | 2 |

Both-Seed-certified new problems: `{"P": 1, "MB": 2, "MS2": 2}`; P-certified/method-open new risks: `{"0": {"MB": 0, "MS2": 0}, "1": {"MB": 0, "MS2": 0}}`.

New roles satisfying condition4: `["UC-C20-U"]`; condition5: `["UC-B20-B", "UC-C20-U"]`. Protection retention and both-Seed slowdown checks are retained verbatim in scientific_decision.json.

| Role | Seed | P | MB | MS2 |
| --- | --- | --- | --- | --- |
| UC-C15-S | 0 | O (571.153) | O (570.623) | O (570.589) |
| UC-C15-S | 1 | O (570.546) | O (570.698) | O (570.797) |
| UC-B20-B | 0 | C 316.976 | C 4.018 | C 3.631 |
| UC-B20-B | 1 | C 317.545 | C 3.778 | C 3.594 |
| UC-C20-U | 0 | O (1170.625) | C 701.525 | C 554.378 |
| UC-C20-U | 1 | O (1170.568) | C 632.520 | C 481.105 |
| UC-B30-S | 0 | O (1171.634) | O (1170.425) | O (1170.476) |
| UC-B30-S | 1 | O (1170.482) | O (1170.431) | O (1170.723) |
| PB-C20-B | 0 | O (870.586) | C 393.721 | C 369.589 |
| PB-C20-B | 1 | O (870.721) | C 413.767 | C 294.156 |

| Role | Seed | MS2/MB status | Direction | MS2 saving (s) |
| --- | --- | --- | --- | --- |
| UC-C15-S | 0 | BOTH_OPEN | UNDETERMINED | N/A |
| UC-C15-S | 1 | BOTH_OPEN | UNDETERMINED | N/A |
| UC-B20-B | 0 | BOTH_CERTIFIED | Win | 0.387 |
| UC-B20-B | 1 | BOTH_CERTIFIED | Win | 0.185 |
| UC-C20-U | 0 | BOTH_CERTIFIED | Win | 147.147 |
| UC-C20-U | 1 | BOTH_CERTIFIED | Win | 151.415 |
| UC-B30-S | 0 | BOTH_OPEN | UNDETERMINED | N/A |
| UC-B30-S | 1 | BOTH_OPEN | UNDETERMINED | N/A |
| PB-C20-B | 0 | BOTH_CERTIFIED | Win | 24.133 |
| PB-C20-B | 1 | BOTH_CERTIFIED | Win | 119.611 |

## Actual exposure and costs

| Role | Seed | Same complete H | Same initial U/root | Triple cover removed | Triple conditional removed |
| --- | --- | --- | --- | --- | --- |
| UC-C15-S | 0 | True | True | 0 | 910 |
| UC-C15-S | 1 | True | True | 0 | 910 |
| UC-B20-B | 0 | True | True | 2204 | 76 |
| UC-B20-B | 1 | True | True | 2204 | 76 |
| UC-C20-U | 0 | True | True | 0 | 2280 |
| UC-C20-U | 1 | True | True | 0 | 2280 |
| UC-B30-S | 0 | True | True | 3969 | 8211 |
| UC-B30-S | 1 | True | True | 3969 | 8211 |
| PB-C20-B | 0 | True | True | 0 | 2280 |
| PB-C20-B | 1 | True | True | 0 | 2280 |

All ten matched MB/MS2 observations have the same complete H actions and fleets, initial U, root scope and settings. After triple deletion, the remaining rows and all columns, types, bounds and objective match exactly. The actual triple cover/conditional counts removed at each Seed are 0/910 (UC-C15-S), 2204/76 (UC-B20-B), 0/2280 (UC-C20-U), 3969/8211 (UC-B30-S), and 0/2280 (PB-C20-B). UC-B20-B naturally has three splits in each MB and MS2 arm at both Seeds; every other MB/MS2 arm has zero splits. This new exposure coexists with the historical R128 no-split observations. Without a new D control it does not identify a net decomposition speed benefit. At UC-C20-U Seed0, MB and MS2 respectively use 698.099 and 551.181 native MIP seconds, 1412.023 and 1058.789 work units, and 49499 and 54557 nodes. Model-generation plus native-read seconds are 1.145 and 0.850. At UC-C20-U Seed1, MB and MS2 respectively use 629.024 and 478.057 native MIP seconds, 1272.487 and 911.262 work units, and 41225 and 45006 nodes. Model-generation plus native-read seconds are 1.150 and 0.849. The C20 saving accompanies lower MIP time/work despite more MS2 nodes at both Seeds; fixed row-writing/read savings are about 0.3 seconds. All observed matched root LP bounds agree within 1e-12. This finite agreement does not prove global redundancy of triple rows. Native costs remain nested explanatory measurements rather than T_cert.

No-native MB/MS2 observations: `[]`. Unexposed observations are retained and do not satisfy the new triple-removal signal. All actual split/target, LP/MIP seconds/work/nodes, modeling/Start and first retained own witness matching final U are in mechanism_costs.csv; native seconds remain nested explanatory costs, not certification time. Fixed-scope LP deletion monotonicity is a mathematical statement, not a speed claim or a claim of global redundancy. Missing diagnostics remain unknown.

UC-C15-S and UC-B30-S remain open for all three methods at both Seeds. UC-B30-S has an open-endpoint reversal: MS2 and MB U are respectively 0.381251 and 0.429057 at Seed0 but 0.429057 and 0.365930 at Seed1. UC-C15-S Seed1 also has slightly worse MS2 U than MB. Both-open comparisons remain UNDETERMINED with no certification ratio or Win. The three tiny negative signed gaps and all fifteen Seed1 raw top-level LB=0/certificate=false records are preserved. Qualified final endpoints use the original source/return/coverage and numerical policy; no raw field, LB or gap is clipped or rewritten.

In the new layer, MS2/P and MB/P each have two both-certified observations, two method-only certificates and four both-open observations. Their certification-time ratio geometric means (right/left) are 87.827903 and 81.425709 respectively, solely on UC-B20-B at the two Seeds. MS2/MB has four both-certified observations (UC-B20-B and UC-C20-U at both Seeds) and four both-open observations; its right/left geometric mean is 1.179515 on those four observations only. In protection, MS2/P and MB/P are method-only certified at both Seeds and have no ratio; MS2/MB is both-certified at both Seeds with a 1.224121 right/left geometric mean. These intersections do not represent the full panel.

## Complete arms and typed comparisons

| Role | Seed | Method | Certified | T_produce | T_verify | T_total | T_cert | U | L |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UC-C15-S | 0 | P | False | 571.153 | 1.474 | 572.626 | open | 0.443202107839 | 0.358153496453 |
| UC-C15-S | 0 | MB | False | 570.623 | 3.235 | 573.857 | open | 0.445818728244 | 0.417138663152 |
| UC-C15-S | 0 | MS2 | False | 570.589 | 3.211 | 573.799 | open | 0.443202107839 | 0.421873682698 |
| UC-C15-S | 1 | MS2 | False | 570.797 | 6.685 | 577.482 | open | 0.443482971999 | 0.421648430727 |
| UC-C15-S | 1 | MB | False | 570.698 | 7.970 | 578.668 | open | 0.443202107839 | 0.419280838463 |
| UC-C15-S | 1 | P | False | 570.546 | 3.315 | 573.860 | open | 0.460131564922 | 0.341515513766 |
| UC-B20-B | 0 | MB | True | 4.018 | 3.497 | 7.515 | 4.018 | 0.57733306997 | 0.57733306997 |
| UC-B20-B | 0 | MS2 | True | 3.631 | 2.892 | 6.523 | 3.631 | 0.57733306997 | 0.57733306997 |
| UC-B20-B | 0 | P | True | 316.976 | 1.830 | 318.807 | 316.976 | 0.57733306997 | 0.57733306997 |
| UC-B20-B | 1 | P | True | 317.545 | 4.999 | 322.544 | 317.545 | 0.57733306997 | 0.57733306997 |
| UC-B20-B | 1 | MS2 | True | 3.594 | 6.374 | 9.968 | 3.594 | 0.57733306997 | 0.57733306997 |
| UC-B20-B | 1 | MB | True | 3.778 | 7.621 | 11.399 | 3.778 | 0.57733306997 | 0.57733306997 |
| UC-C20-U | 0 | MS2 | True | 554.378 | 5.164 | 559.542 | 554.378 | 0.383553588512 | 0.383553588512 |
| UC-C20-U | 0 | P | False | 1170.625 | 1.478 | 1172.103 | open | 0.3899379585 | 0.320776603029 |
| UC-C20-U | 0 | MB | True | 701.525 | 5.225 | 706.750 | 701.525 | 0.383553588512 | 0.383553588512 |
| UC-C20-U | 1 | MB | True | 632.520 | 9.917 | 642.436 | 632.520 | 0.383553588512 | 0.383553588151 |
| UC-C20-U | 1 | P | False | 1170.568 | 3.179 | 1173.747 | open | 0.399554330983 | 0.315027990901 |
| UC-C20-U | 1 | MS2 | True | 481.105 | 9.642 | 490.747 | 481.105 | 0.383553588512 | 0.383553588512 |
| UC-B30-S | 0 | P | False | 1171.634 | 0.543 | 1172.177 | open | 0.465384249789 | 0.235298157666 |
| UC-B30-S | 0 | MB | False | 1170.425 | 5.609 | 1176.034 | open | 0.429057253958 | 0.242416026189 |
| UC-B30-S | 0 | MS2 | False | 1170.476 | 3.813 | 1174.289 | open | 0.381251045205 | 0.24785444425 |
| UC-B30-S | 1 | MS2 | False | 1170.723 | 8.598 | 1179.321 | open | 0.429057253958 | 0.244647889669 |
| UC-B30-S | 1 | MB | False | 1170.431 | 12.612 | 1183.043 | open | 0.365930367536 | 0.244207142448 |
| UC-B30-S | 1 | P | False | 1170.482 | 2.078 | 1172.560 | open | 0.45955584661 | 0.235344298539 |
| PB-C20-B | 0 | MB | True | 393.721 | 3.338 | 397.059 | 393.721 | 0.224680311823 | 0.224680311823 |
| PB-C20-B | 0 | MS2 | True | 369.589 | 3.073 | 372.662 | 369.589 | 0.224680311823 | 0.224680311823 |
| PB-C20-B | 0 | P | False | 870.586 | 1.279 | 871.865 | open | 0.224680311823 | 0.176558000789 |
| PB-C20-B | 1 | P | False | 870.721 | 2.651 | 873.372 | open | 0.241267780643 | 0.17050677888 |
| PB-C20-B | 1 | MS2 | True | 294.156 | 16.453 | 310.609 | 294.156 | 0.224680311823 | 0.224680311823 |
| PB-C20-B | 1 | MB | True | 413.767 | 7.690 | 421.458 | 413.767 | 0.224680311823 | 0.224680311823 |

| Role | Seed | Comparison | Typed status | Direction |
| --- | --- | --- | --- | --- |
| UC-C15-S | 0 | MS2/P | BOTH_OPEN | UNDETERMINED |
| UC-C15-S | 0 | MS2/MB | BOTH_OPEN | UNDETERMINED |
| UC-C15-S | 0 | MB/P | BOTH_OPEN | UNDETERMINED |
| UC-C15-S | 1 | MS2/P | BOTH_OPEN | UNDETERMINED |
| UC-C15-S | 1 | MS2/MB | BOTH_OPEN | UNDETERMINED |
| UC-C15-S | 1 | MB/P | BOTH_OPEN | UNDETERMINED |
| UC-B20-B | 0 | MS2/P | BOTH_CERTIFIED | Win |
| UC-B20-B | 0 | MS2/MB | BOTH_CERTIFIED | Win |
| UC-B20-B | 0 | MB/P | BOTH_CERTIFIED | Win |
| UC-B20-B | 1 | MS2/P | BOTH_CERTIFIED | Win |
| UC-B20-B | 1 | MS2/MB | BOTH_CERTIFIED | Win |
| UC-B20-B | 1 | MB/P | BOTH_CERTIFIED | Win |
| UC-C20-U | 0 | MS2/P | LEFT_ONLY_CERTIFIED | Win |
| UC-C20-U | 0 | MS2/MB | BOTH_CERTIFIED | Win |
| UC-C20-U | 0 | MB/P | LEFT_ONLY_CERTIFIED | Win |
| UC-C20-U | 1 | MS2/P | LEFT_ONLY_CERTIFIED | Win |
| UC-C20-U | 1 | MS2/MB | BOTH_CERTIFIED | Win |
| UC-C20-U | 1 | MB/P | LEFT_ONLY_CERTIFIED | Win |
| UC-B30-S | 0 | MS2/P | BOTH_OPEN | UNDETERMINED |
| UC-B30-S | 0 | MS2/MB | BOTH_OPEN | UNDETERMINED |
| UC-B30-S | 0 | MB/P | BOTH_OPEN | UNDETERMINED |
| UC-B30-S | 1 | MS2/P | BOTH_OPEN | UNDETERMINED |
| UC-B30-S | 1 | MS2/MB | BOTH_OPEN | UNDETERMINED |
| UC-B30-S | 1 | MB/P | BOTH_OPEN | UNDETERMINED |
| PB-C20-B | 0 | MS2/P | LEFT_ONLY_CERTIFIED | Win |
| PB-C20-B | 0 | MS2/MB | BOTH_CERTIFIED | Win |
| PB-C20-B | 0 | MB/P | LEFT_ONLY_CERTIFIED | Win |
| PB-C20-B | 1 | MS2/P | LEFT_ONLY_CERTIFIED | Win |
| PB-C20-B | 1 | MS2/MB | BOTH_CERTIFIED | Win |
| PB-C20-B | 1 | MB/P | LEFT_ONLY_CERTIFIED | Win |

## Identity, review and limits

All formal arms use original E2 PE `ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa` and Gurobi DLL `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. No production program or exporter was compiled. Preformal review accepted the frozen panel after correcting only two equal legacy P identity declarations from E0 to actual E2; the original argv/binding and missing-sparse-import failure remain preserved. The source and H/controller/model bytes remain frozen.

The separate final executor's actual finite recomputation and representative matrix/physical/certificate-chain checks are documented in review/final_independent_review.md. These are finite internal evidence checks, not external replication, statistical evidence from IID problems or a rational audit of every matrix. Current paper defaults and all historical labels remain unchanged. R127 PT 0/3 versus P1/3, K1 timing reversal, K3 open outcomes and the R128 absence of actual MB splits remain in the maintained manuscript.

If adopted, the main-method performance claims would require separately labelled MS2 measurements for Tables SC3-SC5, R127-S and R127-T, the full-MB entries and derived comparisons in Tables 3-6, and their Supplement S authorities. Tables R127-C through R127-E and R128.1-R128.2 remain historical full-MB diagnostic evidence; any renewed mechanism claim must identify its new MS2 reference explicitly. This is a table-migration scope, not authorization to execute another batch.

Resource accounting is recorded in resource_accounting.json. Actual publication, one public recovery and safe owned duplicate cleanup are added only after execution, with retained failures and receipts. PDF export and visual verification are separate from the scientific decision. No further experiment is executed by this confirmation.

## Science publication snapshot

All11 current-only carriers and actual precompression content scan are complete. Raw evidence remains authoritative in place. Packing fee is closed in resource_accounting.json; later public restore and cleanup fees will be included once closed, without recursively repacking. The science export manifest pins the current sources, paper, finite carriers and small inherited dependencies.

## Actual finite delivery and closure

Science commit `aa033d57639453544343b4481ed301150b1de94c` is published in [Draft PR #191](https://github.com/yifanXovo/TailoredExact/pull/191) stacked on `codex/round128-inclusive-root-ablation` at `cc70757304a2019d95f0f934aa5520d0caa946c6`. The first created-PR readback is open, Draft and unmerged with that science head. A small subsequent metadata commit carries these actual delivery receipts; its final remote observation is retained separately to avoid a recursive self-commit claim.

Exactly one anonymous public empty-root recovery passed on that science commit: 463 declared files, 11 current archives, and 249512 indexed raw members. All file/part/member hashes and the isolated portable check pass; zero Optimize, native starts or compilation, no local-raw or historical-carrier fallback. Same-root attempts/failures are retained in review/public_recovery_attempts; no second recovery is performed for metadata.

Guarded owned cleanup status: PASS. Its 31 recorded actions address only declared duplicate archives, inspected regenerable page PNGs, the byte-identical final temporary PDF and this verified recovery expansion. The observed E-volume free-space delta is 2022694912 bytes; this is not an exact attributed reclamation measurement. Authoritative raw/models/tables, distinct prior PDFs, failures, original binaries, main user content and old worktrees remain. Main HEAD matches the initial snapshot: True; the three initial dirty-file SHA256 values still match: True.

Closed outer accounting is 23163.385099 / 39600 seconds: 22203.385099 measured nonoverlapping child seconds, the explicit 900-second conservative setup allowance and 60-second final metadata allowance. Formal group outer time is 19453.391538 seconds; no formal recovery/retry and no production compilation occurred. Nested H/LP/MIP seconds are not added again, and interactive waiting is not claimed as measured CPU. All closed launch/receipt objects are retained in resource_accounting.json without recursively repacking future fees.

The complete 30-arm confirmation ends here. The recommendation remains a uniform next-paper candidate; actual defaults and historical full-MB identities remain unchanged.
