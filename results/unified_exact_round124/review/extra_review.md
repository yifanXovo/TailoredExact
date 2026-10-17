# Actual additional review of the assembled manuscript

Review date: 18 October 2026 (Asia/Shanghai). Reviewer: a separate delegated executor after the complete manuscript and research decision existed. This is an additional computational/mathematical editorial review, not external academic peer review.

**Assessment: the reviewed bounded narrative supports READY_FOR_ADVISOR_REVIEW after the two precision corrections below.** No foundational contradiction was found in the checked model group, integrality argument, complete-cover argument, arithmetic or three nearest-paper descriptions. This assessment does not establish firstness, submission suitability, a new optimality certificate or a native replication. Public reconstruction and publication receipts are the main executor's separate delivery work.

## Findings and author responses

1. **Actual aggregate-product variable bound was incompletely transcribed.** The first appendix table gave W_SP a zero lower bound. Frozen `src/CplexBaseline.cpp` around 1001 instead writes `max(0, S_lower*P_lower)`, with upper bound `max(w_lb, S_upper*P_upper)`. The omitted restriction is redundant for the physical SP completion and the stated envelopes, so this was a specification precision issue, not a discovered invalid inequality. It was reported immediately; the main executor repaired the table. The repaired bounds were reread.
2. **Ikonen's exact scope needed an explicit finite-duplication qualifier.** Its publisher conclusion says that even the “all” picking option can miss an unrestricted solution needing more visits than the generated station copies, or temporary operations. The initial phrase “single-vehicle exact model” was defensible only with that fixed-model scope. This was reported immediately; the manuscript now explicitly limits its certificates to the generated finite duplication model. The new sentence was reread.

No production source, parameter, default or solver setting was changed by this reviewer. A tentative support-enumeration-order concern was withdrawn after reading the active loop: the frozen F0 static loop does all increasing pairs and then triples per vehicle, with a shared count. The preceding dormant rank3 option has a different order and is not the active formulation.

## Mathematical and source checks

The reviewer read the actual frozen source sections in `CplexBaseline.cpp` for routing, unique assignment, direction/nonzero service, load recurrences, duration, inventory, absolute values, VD-P and A/B; the interval factory's centering, penalty closure, cutoff and SP rows; the M-B isolation header; and the scheduler's atomic split and minimum-bound logic. Nine directly read source files were independently SHA256-matched to the supplied production-identity bindings. This checks those source files, not every behavior of all 216 production bindings.

One actual R123 saved matrix was additionally read as plain LP text:

`E:/codes/ExactEBRP-work/worktrees/round123/results/unified_exact_round123/campaign/group01/raw/02_PB-C50-S_S0_M-B/external/models/L0.0.0.0_epoch_0_generation_6.lp`

It has 16,864,314 bytes and SHA256 `086c6ba3c5890b993449ef8b10aa9807e125c49b77e1dc39e637fdeb8959c564`. No solver reader or library loaded it. A small semantic coefficient parser checked the original service/direction/nonzero rows for all four vehicles at station 1, station-1 unique service and inventory balance, and both A/B equalities for all 50 stations: 126 actual rows. It also checked all 400 pickup/drop columns are continuous, all 200 load columns integer, all 200 direction columns binary, and all 50 Y columns integer. This confirms the material M-B representation against an actual submitted matrix; it is not a revalidation of every matrix row.

**Implicit integrality was checked as a derivation.** Unique assignment leaves at most one nonzero pair p,d at a station. At that vehicle, the binary direction makes one quantity zero. Inventory balance then fixes the other to either b−Y or Y−b, an integer. An unassigned station has both quantities zero from its visit bounds. Integer loads and A/B are unnecessary to this inference. The premises matter: two vehicles could each pick up 1/2 if unique service were removed; without direction, p=3/2 and d=1/2 can give an integer net change; without integer Y, the sole quantity can be fractional. These are algebraic premise checks, not counterexamples to the frozen model. A/B follow independently because one-way nonzero service makes total movement |b−Y| and service equivalent to Y≠b.

**Physical embedding was checked independently of auxiliary epigraph inflation.** At the selected inventory state, putting q=g and all other selected-G products zero gives Z=gY. Choosing g=true Gini, e=|r−1| and H=|r_i−r_j| preserves the physical objective, including S=0. Conversely, the product and absolute-value inequalities can make a native completion's objective larger, so arbitrary native g is not asserted equal to physical Gini. The appendix correctly uses preservation of physical points rather than preservation of every nonminimal epigraph completion. SP envelopes and their domain bounds preserve the exact physical SP completion. An inventory vector alone supplies no compatible ordered fleet.

**Full cover was checked as a union argument.** A regional cutoff-model lower bound ell constrains physical points inside F≤c through their objective-preserving embeddings; outside points have F>c. Thus min(ell,c), not an unbounded infeasibility label, is the unconditional regional floor. Every feasible point is in an active/qualified closed region or the analytic complement. The minimum of all regional floors and U consequently bounds the original optimum. Replacing a parent by both closed children preserves all true-G points and their shared boundary; retaining unresolved and unsplit units prevents a schedule/depth limit from deleting an obligation. Bounds on a common domain may use maximum, whereas a union needs minimum. The source's split checks both endpoints, adjacency, lineage and inherited bounds before parent replacement. No claim that these tolerance-based source checks constitute a rational proof is made.

The original load/time transcription is consistent: selected arcs propagate post-service loads from an empty departure; the last load equals total pickup minus total drop, is nonnegative and at most Q. Paying return unloading gives t_p*pickup+t_d*(drop+return)=(t_p+t_d)*pickup. Cumulative pickup can exceed Q. The station-stock sum may decrease on a loaded return. `min_ratio` remains a compatibility field. G=0 means equal inventory-to-target ratios, including a common shortage; with positive lambda and weights, F=0 requires all Y=D.

**Numerical boundary remains explicit.** The factory really can write an impossible row at alpha+lambda*P_lower≥c−1e−9. A physical objective in [c−1e−9,c) need not be mathematically infeasible. Both main text and appendix identify this as numerical closure, retain the original 1e−7 evidence policy, and do not infer a global error bound from 1e−9<1e−7. No changed tolerance or strict rational certificate is claimed.

## Independent arithmetic and result retention

The new [independent_review.py](independent_review.py) implements the published comparison equations directly using Python's standard library; it does not import or call `round124_derive.py`. The executable receipt is [independent_checks.json](independent_checks.json). Its successful final pass took about 0.80 seconds; interactive review and network waiting were not separately metered as zero machine work. During construction, adapter issues concerning sparse input paths, CRLF, source variable names, endpoint null fields and binary64 display precision were corrected in this review script alone. No authority value was edited to satisfy a check.

Checked computations comprise all 32 R122 U−L identities and three-clock sums, all 48 R122 certificate-first pair classifications/severe flags/deltas, all three R123 pairs, main result-table cells, pair-count tables, six actual serialized input hashes and weight totals, final cover-table cells, and checkpoint CSV unknowns. The main table and complete CSVs agree with the authority values at their displayed precision. Exact decimal sums differ only in harmless last-bit display tails from binary64 accumulation.

The independent count is six new Seed0 problems plus two fixed Seed1 repeats, 32 arms and 48 pairs; seven nonzero numerical certificates, all at V20, and 25 open arms. No zero certificate, source-reduced arm or missing arm is introduced. Both M-B/P and ENS-C/P have six new-role WIN. All nine adverse observations survive:

| Role | Seed | Pair | Class |
|---|---|---|---|
| PB-C20-B | 0 | MB-D1/M-B | LOSS |
| PB-C20-B | 0 | MB-D1/ENS-C | LOSS |
| PB-C35-U | 0 | MB-D1/P-GRB | MIXED |
| PB-C35-U | 0 | MB-D1/M-B | LOSS |
| PB-C35-U | 0 | MB-D1/ENS-C | LOSS |
| PB-C35-U | 0 | M-B/ENS-C | LOSS |
| PB-B35-B | 0 | MB-D1/M-B | MIXED |
| PB-B35-B | 0 | MB-D1/ENS-C | MIXED |
| PB-B35-B | 1 | M-B/ENS-C | LOSS |

Seven of these nine involve D1; two are M-B/ENS-C losses. Their denominator is all directed comparisons, as Table 4 states. The finite panel decision remains MIXED, with no D1 promotion or best-of-Seed selector.

The three R123 final fleets were independently replayed from ordered nodes and integer operations, checking single service, station capacities, every vehicle load prefix, return load, full handling/travel duration and exact-rational inventory objective arithmetic. The three final F values agree with their own published U within 1e−15. This is physical witness arithmetic, not rational optimization. P's final fleet was retained rather than replaced by a historical minimum.

R123 remains one known problem and three open endpoints, not three independent samples. Its independently classified pairs are WIN, WIN, TIE for M-B/P, ENS-C/P and M-B/ENS-C. Sorting actual final cover intervals and checking endpoints directly establishes a contiguous [0,U] cover for each integrated method, with two open regions and minima 0.3580114855518426 and 0.35894366616771595. No `complete_coverage` boolean was used as a substitute for this geometry/minimum calculation. The fixed-U counterfactual gives 0.013513933206048268 after closing only M-B I0; closing only I1 leaves L=0.3580114855518426. Those are accounting consequences, not schedule predictions. The own G=0.050119584194518604 lies in I1 and outside I0.

The ENS-C 3600/7200/10800/14400 prefix U/L fields remain unknown in both authority and table. Its endpoint remains separate. No wider clock threshold, early-time interpolation, new speed ratio or proof-time extrapolation was added. Pair calculations use the published qualification states; this review does not independently regenerate all historical native source/return qualifications or the 200-witness/302-bound audit.

## Three nearest primary-paper rechecks

The following sources were reopened directly on the review date. Only short paraphrases are stored; no PDF is republished.

- [Erdoğan, Laporte and Wolfler Calvo 2014, Bath early manuscript](https://purehost.bath.ac.uk/ws/portalfiles/portal/87724146/bike_repositioning_post_refereeing.pdf): checked Sections 1–4, especially the problem definition, fixed-route constraints (1)–(9), general objective (10), depot departure bound (16), and Benders construction. It uses one vehicle, at most one visit, hard final inventory intervals, travel plus handling cost, and depot stock limiting departure supply. The manuscript's comparison is supported and its preprint/version qualification is retained.
- [Schuijbroek, Hampshire and van Hoeve 2017, author manuscript](https://www.andrew.cmu.edu/user/vanhoeve/papers/bike_sharing_final_draft_EJOR.pdf): checked Sections 3–6, P1 (1)–(13), initial vehicle inventory q0, artificial final vertex, transshipment limits (8)–(9), makespan objective, and clustered heuristics. The routing model is more flexible than unique one-way station service; P1 and CP P3 should not be presumed identical in every service restriction. The current work-level comparison does not make that identity claim. Clustered routing is correctly not presented as a joint global certificate.
- [Ikonen, Heljanko and Harjunkoski 2025, publisher full text](https://link.springer.com/article/10.1007/s11081-024-09942-z): checked Sections 2, 3.1–3.7, equations (3)–(18), multi-vehicle clustering discussion and conclusion. Routing/handling cost, demand intervals, prescribed arriving load q0, open/loop variants, duplicated split visits and prohibition of temporary operations are supported. Its arc-load disjunctions differ substantively from the present Gini cover. Multi-vehicle clustering is approximate; fixed-duplication single-vehicle certificate scope now appears explicitly in the draft.

The review did not reread all other literature in full. Chemla remains abstract-only, Raviv's accessible early version remains distinguished from final metadata, and recent 2026 papers remain abstract/excerpt-level. No unread initial-load/visit equivalence is inferred. The title/contributions make no affirmative firstness, universal dominance, all-V50 certification or SOTA claim.

## Consistency, attribution and execution boundary

All 13 bibliography keys resolve, without duplicate entries or unused citation keys in the main text plus appendix. The ten main equations and eighteen appendix equations have unique tags. Symbols, service/inventory semantics and generated result tables agree in the checked sections. Source hashes, PE/DLL identity, lambda, Seed and route/computation horizons remain distinct. The H bridge/preset was read for its inherited decoder, 24 fixed-seed orders, additional constructive seed, verified full-fleet publication and finite-descent configuration. Gurobi receives native LP/MIP/presolve/cuts/branching credit; H supplies upper bounds and no proof. The limited historical-attribution note is compatible with that scope; the reviewer did not newly rebuild all its old controls.

The reviewer wrote only under this Round124 E-root's `review/` directory. Solver/native launches: **0**. LP/MIP/CP/DP optimization calls: **0**. Production compilations: **0**. New formal arms, instances, Seeds, model variants, parameters and defaults: **0**. No human messaging, commits, PR operations, external submissions or cleanup were performed by this reviewer. The research decision retains one priority—substantive advisor feedback—and does not execute or schedule a follow-up experiment.

The scope is deliberately finite: real source/matrix semantics, derivations, arithmetic and three primary-paper comparisons were checked. Absence of a found issue is not proof that every historical row or native call is correct. Within that stated scope, no unresolved core factual gap requires withholding the complete bounded draft from advisor review.
