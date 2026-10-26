# Supporting material: complete results, historical layers and implementation qualification

The main manuscript reports the final fixed implementation. This supplement retains complete tables, historical evidence with its own versions and engineering details. No historical observation is relabelled as final-version evidence.

## S1. Every final-version method position

| Position / problem | Seed / repeat | method | proof | U | L | production / certification seconds |
|---|---|---|---|---|---|---|
| C01 SM-B10-B | 0 / 1 | P | native/outer | 0.5358910753 | 0.5358910753 | 1.64120847 / 1.64120847 |
| C02 SM-B10-B | 0 / 1 | S2 | native/outer | 0.5358910753 | 0.5358910753 | 0.857334769 / 0.857334769 |
| C03 SM-B10-B | 0 / 2 | S2 | native/outer | 0.5358910753 | 0.5358910753 | 0.77449898 / 0.77449898 |
| C04 SM-B10-B | 0 / 2 | P | native/outer | 0.5358910753 | 0.5358910753 | 1.04087407 / 1.04087407 |
| C05 SM-B10-B | 1 / 1 | S2 | native/outer | 0.5358910753 | 0.5358910753 | 0.804835074 / 0.804835074 |
| C06 SM-B10-B | 1 / 1 | P | native/outer | 0.5358910753 | 0.5358910753 | 1.04329514 / 1.04329514 |
| C07 SM-B10-B | 1 / 2 | P | native/outer | 0.5358910753 | 0.5358910753 | 1.01620935 / 1.01620935 |
| C08 SM-B10-B | 1 / 2 | S2 | native/outer | 0.5358910753 | 0.5358910753 | 0.773128129 / 0.773128129 |
| C09 K-15-S | 0 / 1 | P | open | 0.5922648823 | 0.5274147657 | 571.090118 / unresolved |
| C10 K-15-S | 0 / 1 | S2 | native/outer | 0.5922648823 | 0.5922648792 | 112.934953 / 112.934953 |
| C11 K-15-S | 0 / 1 | PS | open | 0.5922648823 | 0.5202155244 | 571.01766 / unresolved |
| C12 K-15-S | 1 / 1 | PS | open | 0.5922648823 | 0.5318726124 | 571.178008 / unresolved |
| C13 K-15-S | 1 / 1 | S2 | native/outer | 0.5922648823 | 0.5922648823 | 115.020576 / 115.020576 |
| C14 K-15-S | 1 / 1 | P | open | 0.5922648823 | 0.5289006134 | 571.129094 / unresolved |
| C15 UC-B20-B | 0 / 1 | P | native/outer | 0.57733307 | 0.57733307 | 319.060049 / 319.060049 |
| C16 UC-B20-B | 0 / 1 | S2 | native/outer | 0.57733307 | 0.57733307 | 3.96571526 / 3.96571526 |
| C17 UC-B20-B | 1 / 1 | S2 | native/outer | 0.57733307 | 0.57733307 | 3.82069015 / 3.82069015 |
| C18 UC-B20-B | 1 / 1 | P | native/outer | 0.57733307 | 0.57733307 | 318.377442 / 318.377442 |
| C19 K-35-U | 0 / 1 | P | open | 0.6647466018 | 0.3355012377 | 2370.86275 / unresolved |
| C20 K-35-U | 0 / 1 | S2 | open | 0.6928543586 | 0.5649415039 | 2370.94178 / unresolved |
| C21 K-35-U | 1 / 1 | S2 | open | 0.6683582547 | 0.5542719638 | 2370.78494 / unresolved |
| C22 K-35-U | 1 / 1 | P | open | 0.7588515976 | 0.330548324 | 2370.84408 / unresolved |
| C23 X-35-U | 0 / 1 | P | open | 0.01626456434 | 6.938893904e-18 | 2370.86403 / unresolved |
| C24 X-35-U | 0 / 1 | S2 | independent zero | 0 | 0 | 120.256685 / 120.256685 |
| C25 X-35-U | 1 / 1 | S2 | independent zero | 0 | 0 | 452.84144 / 452.84144 |
| C26 X-35-U | 1 / 1 | P | independent zero | 0 | 0 | 2064.94937 / 2064.94937 |
| C27 X-35-B | 0 / 1 | P | independent zero | 0 | 0 | 157.954177 / 157.954177 |
| C28 X-35-B | 0 / 1 | PS | independent zero | 0 | 0 | 7.25054622 / 7.25054622 |
| C29 X-35-B | 0 / 1 | S2 | independent zero | 0 | 0 | 17.6060326 / 17.6060326 |
| C30 X-35-B | 1 / 1 | S2 | independent zero | 0 | 0 | 18.2774496 / 18.2774496 |
| C31 X-35-B | 1 / 1 | PS | independent zero | 0 | 0 | 7.19577947 / 7.19577947 |
| C32 X-35-B | 1 / 1 | P | independent zero | 0 | 0 | 50.1505475 / 50.1505475 |

## S2. Production and postproduction clocks

The C01 native producer sealed normally. Its first postreader failed on a missing launch-metadata field; a bounded read-only adapter derived the already registered settings and reused that same raw arm. The failed logs, unchanged producer clock and real verification delay remain. No healthy native arm was repeated.

| Position | production seconds | postverification seconds | total seconds |
|---|---|---|---|
| C01 | 1.641208466 | 46.6456324 | 48.28684087 |
| C02 | 0.8573347687 | 0.2301405 | 1.087475269 |
| C03 | 0.7744989803 | 0.2266128999 | 1.00111188 |
| C04 | 1.040874065 | 0.2392841 | 1.280158165 |
| C05 | 0.8048350738 | 0.2269227999 | 1.031757874 |
| C06 | 1.043295143 | 0.2257164001 | 1.269011543 |
| C07 | 1.016209355 | 0.2338855 | 1.250094855 |
| C08 | 0.7731281291 | 0.228319 | 1.001447129 |
| C09 | 571.0901177 | 2.4273113 | 573.517429 |
| C10 | 112.9349527 | 3.758351 | 116.6933037 |
| C11 | 571.0176604 | 2.2171897 | 573.2348501 |
| C12 | 571.1780076 | 3.1282583 | 574.3062659 |
| C13 | 115.0205757 | 4.0986801 | 119.1192558 |
| C14 | 571.1290941 | 2.9784281 | 574.1075222 |
| C15 | 319.0600493 | 1.2434149 | 320.3034642 |
| C16 | 3.965715262 | 2.2022368 | 6.167952062 |
| C17 | 3.820690154 | 2.2351581 | 6.055848254 |
| C18 | 318.3774422 | 1.431066 | 319.8085082 |
| C19 | 2370.862752 | 0.7067805 | 2371.569532 |
| C20 | 2370.941779 | 3.6650486 | 2374.606828 |
| C21 | 2370.784945 | 3.616341 | 2374.401286 |
| C22 | 2370.844082 | 0.7103621 | 2371.554444 |
| C23 | 2370.86403 | 0.5900696 | 2371.454099 |
| C24 | 120.2566853 | 3.4503352 | 123.7070205 |
| C25 | 452.8414402 | 3.4633972 | 456.3048374 |
| C26 | 2064.949368 | 0.5909130001 | 2065.540281 |
| C27 | 157.9541769 | 0.5901521 | 158.544329 |
| C28 | 7.250546223 | 1.3739651 | 8.624511323 |
| C29 | 17.60603262 | 3.5490938 | 21.15512642 |
| C30 | 18.27744961 | 3.5100392 | 21.78748881 |
| C31 | 7.195779469 | 1.3705275 | 8.566306969 |
| C32 | 50.15054751 | 0.5871859 | 50.73773341 |

Full machine-readable arms, matched pairs, all six weight points, complete inventories/vehicle work, raw producer seals, source qualifications and construction/LP receipts are supplied through the finite reproduction entry. Open certification times are null.

## S3. Source access, model inheritance and novelty boundary

# Literature and provenance checks for the review manuscript

The pre-existing routing/model comparison is retained from the R124/R125 source review, with the access limits in `results/unified_exact_round125/literature_scope.md`. This round adds a targeted TC positioning search on 26 October 2026 (Asia/Shanghai). Searches covered Gini/CDF/threshold representations and budget-derived cardinality/concave epigraph inequalities. It is not an exhaustive priority search.

| Primary source | Material actually available | Manuscript use and remaining question |
|---|---|---|
| [Yitzhaki and Schechtman, chapter 2](https://link.springer.com/chapter/10.1007/978-1-4614-4720-7_2) | Publisher abstract, notes, bibliography and citation metadata; full subscription chapter unavailable. | Established alternative Gini representations; the paper independently proves its finite threshold identities. Before asserting a precise equation-to-equation literature equivalence, inspect the complete chapter's CDF formulas and discrete-distribution convention. Citation year 2013 follows publisher citation, with online dates in 2012. |
| [Yu and Ahmed](https://www.sciencedirect.com/science/article/pii/S1572528615000444) | Publisher-indexed article text, including the mean-risk knapsack section's sorted-cost cardinality argument; direct open requests returned 403/redirect error. | A budget-derived activation count and concave epigraph strengthening are established tools. Their complete lifted inequalities are not implemented or dominated here. Final volume date is May 2017, volume 24, pp.87-102, despite the DOI's 2015 component. |
| [Dorfman](https://www.jstor.org/stable/1924845) | JSTOR landing page did not expose article text. | Bibliographic lead for the distribution-function Gini formula, also listed by the inspected Springer notes. No claim to have read the original proof; no statement depends on access to it. |

The TC contribution is the specified all-station inventory-state aggregate and its demonstrated increment over the explicitly retained controls. The threshold identity, cheapest-increment count and chord inequality are not presented as newly invented mathematics. No general dominance over historical DP, VD-J equality or complete concave epigraph closures is asserted.

The physical problem and startup descend from the supplied project model/heuristic code. The available project material does not identify a verified external same-problem heuristic article by author, title and DOI. Before journal submission the authors should confirm whether such a paper exists, add its precise citation if applicable, and align model-inheritance wording. The current draft explicitly claims the exact algorithm and evidence, rather than invention of the underlying model or heuristic. This bibliographic clarification does not require new optimization runs.

Other specific access gaps remain the final Raviv article, full Chemla article and complete recent Qiao/Caggiani formulations. Their unread constraints are not used to claim mathematical equivalence or performance superiority. No foreign full text is redistributed.

## S4. Historical reading extract, version R133

The following dated text is a historical evidence extract at base 39043b15b3cceae2cab14a3fbaec39e2b16339ce. Its terms “current” and “replacement” refer to R133 or earlier versions, never to the final panel in S1. The main manuscript states the updated scientific conclusions. Old historical_evidence.md references resolve to the [fixed R130 historical account](https://github.com/yifanXovo/TailoredExact/blob/39043b15b3cceae2cab14a3fbaec39e2b16339ce/results/unified_exact_round130/manuscript.md), including Sections6.8-6.10, rather than a missing current relative file.

## 5. Complete-method evidence and new inputs

### 5.1 Protocol and interpretation

P is the primary cold original compact benchmark. PS pays the same complete H independently and maps its fleet to the original compact model. S2R is the valid pair-only inclusive-root LP-plus-MIP control. Every arm pays H when applicable, modeling, all native calls, full Start/physical checks and required output under its own cap. Production T_produce is the certification time only for a qualified certificate. Independent postproduction verification T_verify is separate; T_total=T_produce+T_verify. Open T_cert is null, with the actual observation horizon retained. Physical T is unrelated to these computational clocks.

Threads and MIPThreads are one, H seed is fixed, and native Seeds 0/1 are repeated observations of the same problem. Native defaults and requested zero gaps are fixed. Method order is counterbalanced prospectively. Native optimization is serial and does not compete with compilation or PDF export. No arm receives another arm's incumbent, Start, bound, parameter, basis, tree or cache.

The timing environment has a recorded limitation: an initial dependency waiter repeatedly parsed completed evidence files in the background until it was repaired partway through the first new 35-station group. Immutable producer intervals determine conservative overlap with the original waiter's lifetime in the supporting timing-environment table. These durations are not measured parsing, CPU-contention or slowdown seconds; absence of that overlap also does not prove a quiescent machine. Earlier partial table refreshes also involved brief decoding work. The repair changed neither production code nor native caps and did not restart an arm. We retain the observed clocks and certificate qualifications without estimating counterfactual clean-machine times. Timing directions describe these observations; they do not isolate a causal algorithm effect under a quiescent machine, and differences between source layers cannot be attributed solely to geography.

For each comparison distinguish both certified, only left certified, only right certified, both open and unevaluable evidence. Both-certified time directions use unrounded complete certification time; one-sided certificates determine the corresponding direction. Both open is UNDETERMINED. Time ratios are confined to explicit both-certified intersections. No cap is substituted for an unknown certification time, and endpoint gaps do not predict final certification speed. Near-zero objectives are reported separately. Each arm's attained endpoint is distinct from the problem-level zero/positive/unknown stratum. A qualified legal zero establishes a zero optimum for that problem; a positive qualified lower bound establishes positivity under the numerical policy. Otherwise the optimum class remains unknown. This descriptive classification changes no other arm's U, L, certificate or time and supplies no information to production.

For magnitude only, a both-certified delay is material when slower minus faster is at least max(10 seconds, 0.10 times faster); this threshold never changes a strict Win/Lose direction. Displayed seconds are rounded to three decimals. All directions, signed differences and ratios use the unrounded supporting records, so equal-looking printed times need not be a Tie.

### 5.2 Current S2 on the known main, tiny and size-boundary panels

The main final-version evidence measures six known SC inputs at two Seeds, with 600-second caps at 15 stations and 1200 at 20. These twelve observations are not unseen validation. S2 and P certify 10 and 5 observations; strict directions are 10 Win and 2 UNDETERMINED. No predecessor M-B or ENS time is relabelled as final S2. C denotes qualified T_cert; O @ gives actual open T_produce with null T_cert.

**Table 1. Every known-main final-version observation (seconds).**

| Known problem / Seed | P | S2 |
| --- | --- | --- |
| SC-C15-S / 0 | C 460.809 | C 33.167 |
| SC-C15-S / 1 | C 469.536 | C 35.538 |
| SC-B15-S / 0 | C 12.875 | C 2.851 |
| SC-B15-S / 1 | C 16.181 | C 2.245 |
| SC-C15-B / 0 | C 242.256 | C 57.928 |
| SC-C15-B / 1 | O @ 570.429 | C 33.444 |
| SC-B20-S / 0 | O @ 1170.605 | C 982.279 |
| SC-B20-S / 1 | O @ 1170.903 | C 676.371 |
| SC-C20-S / 0 | O @ 1171.043 | O @ 1170.676 |
| SC-C20-S / 1 | O @ 1170.577 | O @ 1171.035 |
| SC-B20-U / 0 | O @ 1170.574 | C 26.893 |
| SC-B20-U / 1 | O @ 1171.024 | C 15.998 |

The separate tiny layer has two inputs, three Seeds and two opposite-order repeats per Seed. It gives 9 Win and 3 Lose; the three strict reverse differences are subsecond, while no >=10-second delay and no P-only certificate is observed. This finite absolute-overhead result is not a population noise bound.

**Table 2. Every repeated tiny final-version observation (seconds).**

| Tiny problem / Seed / repeat | P | S2 |
| --- | --- | --- |
| SM-C8-S / 0 / 1 | C 5.568 | C 2.645 |
| SM-C8-S / 0 / 2 | C 5.143 | C 2.865 |
| SM-C8-S / 1 / 1 | C 3.904 | C 3.227 |
| SM-C8-S / 1 / 2 | C 4.197 | C 2.845 |
| SM-C8-S / 2 / 1 | C 4.611 | C 3.781 |
| SM-C8-S / 2 / 2 | C 4.307 | C 4.126 |
| SM-B10-B / 0 / 1 | C 0.778 | C 0.792 |
| SM-B10-B / 0 / 2 | C 1.122 | C 0.461 |
| SM-B10-B / 1 / 1 | C 1.067 | C 0.511 |
| SM-B10-B / 1 / 2 | C 0.708 | C 0.801 |
| SM-B10-B / 2 / 1 | C 0.794 | C 0.800 |
| SM-B10-B / 2 / 2 | C 1.129 | C 0.461 |

Both original 35-station roles remain open for both methods at their 2400-second caps and original Seed 0. Their final certification-time ordering is unknown. Earlier results at 50/60 stations retain their historical M-B/ENS identity and do not extend final-S2 validation. The complete signed endpoints and all three clocks are in the supporting tables.

**Table 3. Every original known 35-station boundary observation (Seed 0; seconds).**

| Known role / method | U / L | Signed U-L | T_produce | T_verify | T_total | T_cert |
| --- | --- | --- | --- | --- | --- | --- |
| PB-C35-U / P | 0.17477189 / 0.05970290 | 0.115069 | 2370.823 | 1.107 | 2371.930 | null |
| PB-C35-U / S2 | 0.18370156 / 0.08472828 | 0.0989733 | 2370.592 | 5.475 | 2376.067 | null |
| PB-B35-B / P | 0.30555578 / 0.00000000 | 0.305556 | 2370.555 | 0.546 | 2371.101 | null |
| PB-B35-B / S2 | 0.24650447 / 0.12194212 | 0.124562 | 2370.807 | 5.246 | 2376.053 | null |

P retains the lower physical U on PB-C35-U, while S2 retains the lower U on PB-B35-B. These endpoint directions do not rank the unobserved certification times. All four T_cert entries remain null; T_total includes the separate independent verification.

### 5.3 Prospective known-source and geography-transfer validation

The new study fixes six K and six X inputs before H or optimization. K uses the existing CITI/CABI source snapshots and generator; X uses an official Chicago Divvy station snapshot with UTM16N conversion and the same synthetic target, inventory and weight rules. This changes geography, not the demand-generation mechanism and not real operational validation. The source snapshots, field provenance, missing/duplicate handling, IDs, coordinates, transformations and one-time seeds are retained. No difficulty-based filter or redraw is applied.

The six roles per layer cover shortage, balanced and surplus scenarios and compact/regional geometry at 15, 20 and 35 stations. New sets from the same source are disjoint, rather than nested enlargements. Five K roles have no overlap with the recorded historical small selections. K-35-B follows the preregistered next exposure tier and has partial historical overlap, so its stations are not all unseen. Shortage is guaranteed structurally by total initial stock below total target and positive weights/lambda; balanced or surplus zero objectives remain legitimate outcomes.

**Table 4. Fixed new-input design, physical/computational limits and effective weights.**

| Input | Source / inventory / geography | n / Q | Physical T / cap (s) | Omega / rho |
| --- | --- | --- | --- | --- |
| K-15-S | CITI / shortage / compact | 15 / [30, 30] | 3600 / 600 | 9.473371 / 1.421006 |
| K-15-B | CABI / balanced / regional | 15 / [30, 30] | 5400 / 600 | 3.312808 / 0.496921 |
| K-20-S | CITI / shortage / compact | 20 / [30, 30] | 5400 / 1200 | 11.312498 / 1.696875 |
| K-20-U | CABI / surplus / compact | 20 / [30, 30] | 7200 / 1200 | 10.561986 / 1.584298 |
| K-35-B | CITI / balanced / compact | 35 / [25, 25, 25] | 7200 / 2400 | 16.722652 / 2.508398 |
| K-35-U | CABI / surplus / regional | 35 / [20, 25, 30] | 10800 / 2400 | 15.005326 / 2.250799 |
| X-15-S | DIVVY / shortage / compact | 15 / [30, 30] | 3600 / 600 | 5.106124 / 0.765919 |
| X-15-B | DIVVY / balanced / regional | 15 / [30, 30] | 5400 / 600 | 3.678125 / 0.551719 |
| X-20-S | DIVVY / shortage / compact | 20 / [30, 30] | 5400 / 1200 | 6.585322 / 0.987798 |
| X-20-U | DIVVY / surplus / compact | 20 / [30, 30] | 7200 / 1200 | 7.899997 / 1.185000 |
| X-35-B | DIVVY / balanced / compact | 35 / [25, 25, 25] | 7200 / 2400 | 9.884375 / 1.482656 |
| X-35-U | DIVVY / surplus / regional | 35 / [20, 25, 30] | 10800 / 2400 | 9.621875 / 1.443281 |

All twelve inputs have independently paid P and S2 at both Seeds: 48 arms. The preselected 15-S, 20-U and 35-B role in each layer also has PS at both Seeds: 12 additional arms. The PS subset is fixed without reference to which method wins. K/X, sizes and positive/zero outcomes are reported separately; shared controls and Seed repeats are not independent new problems.

All 60 fixed D positions are sealed. Across the full 24 S2/P positions the directions are 16 Win, 1 Lose, 6 UNDETERMINED and 1 UNEVALUABLE. Performance-eligible certificates are 17/24 for S2 and 9/24 for P; one further own-zero S2 proof is excluded from formal timing after native source loss. In K, S2/P certificates are 6/2 on 12 repeated comparisons over six problems, with 6 Win and 6 both-open. In X they are 11/7 on 12 comparisons over six problems, with 10 Win, 1 Lose and 1 UNEVALUABLE. These are finite within-mechanism and geography-transfer observations. Seeds are repeats and shared controls do not create independent trials. PS attribution is limited to the preselected six-problem subset. Problem-level zero/positive/unknown status remains distinct from each attained endpoint. K-35-B has optimum class UNKNOWN: its positive attained U supplies no positive optimum proof. K-35-U has separately recorded qualified positive lower-bound evidence under the historical policy, while the X35 own-zero observations establish different zero-optimum roles. Zero-optimum 35 cases do not establish positive-objective 35 proof performance.

**Table 5. Every fixed new-input method position (seconds).**

| New input / Seed | P | S2 | PS (preselected subset) |
| --- | --- | --- | --- |
| K-15-S / 0 | O @ 571.093 | C 112.642 | O @ 570.602 |
| K-15-S / 1 | O @ 570.746 | C 114.759 | O @ 571.207 |
| K-15-B / 0 | C 478.447 | C 29.201 | not selected |
| K-15-B / 1 | C 465.514 | C 36.323 | not selected |
| K-20-S / 0 | O @ 1171.019 | O @ 1171.416 | not selected |
| K-20-S / 1 | O @ 1170.687 | O @ 1171.715 | not selected |
| K-20-U / 0 | O @ 1170.818 | C 5.800 | O @ 1171.322 |
| K-20-U / 1 | O @ 1171.688 | C 5.158 | O @ 1170.895 |
| K-35-B / 0 | O @ 2370.959 | O @ 2370.552 | O @ 2370.426 |
| K-35-B / 1 | O @ 2370.482 | O @ 2370.368 | O @ 2370.913 |
| K-35-U / 0 | O @ 2370.545 | O @ 2370.889 | not selected |
| K-35-U / 1 | O @ 2370.981 | O @ 2370.515 | not selected |
| X-15-S / 0 | O @ 571.160 | C 95.039 | O @ 570.777 |
| X-15-S / 1 | O @ 570.660 | C 33.016 | O @ 571.272 |
| X-15-B / 0 | C 6.357 | C 4.294 | not selected |
| X-15-B / 1 | C 2.524 | C 2.633 | not selected |
| X-20-S / 0 | O @ 1171.067 | C 489.669 | not selected |
| X-20-S / 1 | O @ 1170.565 | C 460.549 | not selected |
| X-20-U / 0 | C 163.040 | C 22.327 | C 152.633 |
| X-20-U / 1 | C 149.774 | C 9.241 | C 585.777 |
| X-35-B / 0 | C 159.661 | C 17.198 | C 6.850 |
| X-35-B / 1 | C 50.073 | C 17.994 | C 7.537 |
| X-35-U / 0 | O @ 2370.438 | C 120.829 | not selected |
| X-35-U / 1 | C 2072.220 | E (own zero) | not selected |

E denotes the disclosed source-reduced own-zero proof, excluded from formal timing; C denotes a performance-eligible certificate and O an ordinary open result. On X-35-U Seed1, S2's own exact-zero fleet refutes three call4 local bounds above zero by more than1e-7. The whole call's dependent native claims are rejected. Its raw 448.483-second production clock and own physical zero remain, but derived formal T_cert is null and the comparison is UNEVALUABLE. No favorable Win is recovered from that arm, and native source reliability remains an unresolved limitation. The separate source-loss note retains the exact values and complete receipt chain.

The finite new-input results do not show uniform dominance. K-20-S and both K35 roles remain open at both Seeds; better endpoints do not order their final certification times. X-15-B Seed1 is a strict small reversal (P 2.524 versus S2 2.633 seconds). In the preselected PS subset S2/PS gives 8 Win, 2 Lose and 2 UNDETERMINED; PS/P gives 3 Win, 1 Lose and 8 UNDETERMINED. Both X-35-B Seeds are physically zero and PS certifies in 6.850/7.537 seconds versus S2 17.198/17.994. On X-20-U Seed1, however, PS takes 585.777 versus P 149.774 seconds. All 12 S2/PS comparisons have equal complete realized H and actual native exposure, supporting a scoped complete-backend comparison rather than attribution from equal startup rules alone. Neither those reversals nor geography-transfer successes erase the positive K35 proof boundary or the numerical source loss.

### 5.4 Numerical sources and implementation qualification

The frozen X-35-U / Seed1 / S2 call4 has three local native bounds, 2.2155204177669103e-7, 2.3794866331140976e-7 and 2.889725344877011e-7, refuted beyond the inherited 1e-7 contract by that arm's own later exact-zero fleet. Its physical G=F=0 lies in the call's interval and cutoff [0,0.16038610038610038]. The exported `global_bound_trace.csv` placed these observations in columns named `active_leaf_valid_lower_bound` and `valid_global_lower_bound`. Those names overstate qualification. Source rejection, the own-zero proof and original formal-performance exclusion all remain; no revised trace overwrites the old bytes.

This trajectory is retrospective callback replay after the terminal native call returns. The actual outer path has a parent LP, two child LPs and one terminal MIP, no committed split and no target request; the terminal event has L=U=0. The trace's callback timestamps therefore do not establish that the scheduler consumed those transient values online or performed erroneous outer pruning. Possible effects inside native search and counterfactual search behavior remain unresolved.

The D24 physical zero was also extended into the complete rounded linear model with exact rational arithmetic, adjusting rounded ratio identities and using legal epigraph slack. Its model objective is about 9.095107e-13, still below all three rejected bounds beyond the 1e-7 contract. A fresh load through the same original DLL compared 269,462 matrix/objective/domain/type items: only three RHS values differ as positive versus negative zero; every other numeric and structural comparison agrees. The exact rational linear models are therefore the same and the existing full-point proof transfers. This is not raw-bit identity and says nothing about the historical retained model, invisible presolve/cut matrices or internal tree state. Small coefficient rounding does not explain the demonstrated bound violation; the native internal numerical cause remains UNKNOWN.

A separate inclusive-cutoff defect was found in the inherited MS2 factory and its compact fallback. When an analytic floor reached c-1e-9, they could emit the artificial row 0<=-1, although a legal boundary point F=c belongs to the required inclusive set. Both emitters now omit that row and retain the valid penalty lower bound. An exact dyadic boundary fixture with lambda=2^-39 checks all 27 generated rows/bounds and confirms that the old trigger would exclude the legal boundary fleet. This is a necessary model-embedding repair, not a numerical tolerance adjustment. S2R already excluded the marker; D24's actual matrix has an exact feasible extension. Consequently this independent scope defect does not explain either inherited numerical anomaly. The candidate model changes in triggered domains, and its paired version bridge remains required if adopted as the paper implementation.

The journal also has an obsolete Seed=0 predicate in the journal's parameter readback. The registered study supports Seeds 0/1. In X-15-B, the same method/model and otherwise matching readback can therefore change journal eligibility solely with Seed, and the reported scope failure need not indicate an actual cover mismatch. The independent offline reader also checks actual Seed, so this defect alone neither invalidates every Seed1 result nor qualifies its native source. Parameter agreement, model/scope identity, cover completeness, source contradiction, native quality and missing evidence are distinct tests.

The corrected implementation is frozen at 4507c3554c6544048d307168779c8757f53cc5ae. Requested versus actual registered parameters, local versus global qualification, later source revocation, complete unresolved-domain handling and actual proof consumers share the defined contract. The passive journal's global flag is not a blanket local-bound switch. Raw values remain; a readable finite value is not automatically a qualified original-problem bound.

**Table Q1. Corrected-version evidence, separate from the original benchmark.**

| Stage | Fixed scope | Result | Claim boundary |
| --- | --- | --- | --- |
| Numerical diagnosis | D24 full point/same-DLL load and GEOM original/cold replay | Finite work complete; internal causes UNKNOWN | No repair of old native tree inferred |
| Focused checks | ABI, parameters, rejection/cover/quality/receipt faults, inclusive boundary and positive native unit | PASS | Controlled/unit evidence excluded from formal sample |
| D1 qualification | 14 exposed positions over four roles, Seeds 0/1 | 14/14 implementation;13/14 sources;8 cert / 5 open / 1 rejected safe-open | Finite handling qualification, not holdout |
| D3 version bridge | Eight independent original/new S2 runs, four known-role/Seed pairs | 8/8 certificates;2 Win / 2 Lose; all time-close | No broad speed or NEXT-path stability claim |

The new X35 Seed1 arm naturally reproduces the rejected raw claims and safely opens the full physical domain, with T_cert null and native/performance proof unavailable despite an independent physical zero. Its rejection and valid-trace behavior, normal positive certificates, and actual UC splits/child targets are independently checked. No natural NEXT call occurs in D1; controlled/static checks supply only its semantic coverage. D3 changes are mixed and small, preserving all clocks. Full14/8-arm tables and the accepted-H reader correction are in Appendix B.4.2. Neither study silently changes original17/24 counts or the old source's REJECTED status.

The original research PE repeats the GEOM workflow in 709.219 seconds, again returning native OPTIMAL with the same physical gap. The single cold serialized-model diagnostic uses no Start, returns TIME_LIMIT at its 1168.6-second native cap (1169.336-second outer cost), and saves eight point vectors. Its final native ObjVal=0.31538912105344014 agrees with independently replayed physical F=0.31538912105343897 to about 1.2e-15; it does not reproduce the original discrepancy. This different search does not repair or validate the historical failing point. That point's complete g/e vector remains unavailable, and its internal numerical cause stays UNKNOWN. 

Official documentation distinguishes callback objective-bound observations from independent original-problem qualification [@gurobiCallbackCodes]. It also motivates diagnosis through formulation and residual analysis; numerical parameters are possible diagnostics with costs, rather than a proof of a fixed physical-objective tolerance [@gurobiNumericParameters]. Root-cause status, implementation qualification and submission readiness are reported separately. The new finite replacement data do not relabel the frozen benchmark as measurements of the new version.

## 6. Expression mechanisms and joint-structure limits

### 6.1 What existing paid-start and root controls establish

Known paid-H controls provide scoped backend evidence. On UC-B20-B, S2 saves 233.716 and 123.613 seconds against independently paid PS at the two Seeds. On UC-C20-U, S2 certifies at both Seeds while PS remains open. Every method stays open on the UC-B30-S shortage boundary. These three known problems are attribution evidence, not new-input validation.

None of the 24 new S2 validation arms commits a natural multi-leaf split; eight use a target, and paid child-LP probes remain part of the complete cost. Their overall advantage cannot be attributed directly to realized multi-leaf decomposition. The earlier R130 UC-B20-B path supplies separate evidence for three natural splits, eight child LPs and one target, rather than new-input performance evidence. The outer-package comparison is mixed/time-close. UC-B20-B exposes three natural splits at each Seed, yet S2R certifies in 1.398 and 1.586 seconds versus S2 in 3.559 and 3.504. Across the four both-certified S2/S2R observations, strict directions are three Lose and one Win; all are time-close under the declared absolute/relative materiality rule. A zero split count also does not mean no child LP was probed. Accordingly we do not attribute all speed to decomposition or disaggregate a bundle's effect among its individual rows. Earlier reverse/open outcomes and the selected tuned-P holdout's adverse 0/3 versus cold-P 1/3 certificate result remain in the historical supplement.

### 6.2 Two equivalent-expression propositions

Compare models on the same input, domains, G interval, cutoff and objective, projecting to all common physical/target-objective coordinates while allowing other auxiliaries to reoptimize. Projection inclusion, the current LP optimum and full search cost are different questions.

First, deleting only H-spread and the two centering families leaves the ideal projection unchanged under the audited H-use and additive-bound conditions. At a zero lower endpoint set H_ij=|r_i-r_j|. At a positive endpoint retain enough additional H mass to meet the total floor, interpolating between absolute differences and the truncated individual upper bounds. The capacity inequality for that interpolation is proved in Appendix C. The remaining Gini epigraph, total cap/floor, scalar/SP rows, bounds and domain generation stay in the model; the entire geometry package is not declared redundant.

Second, eliminate continuous zero-cost W_SP from its actual MC rows, SP cutoff and bounds by retaining every lower/upper compatibility and lower-plane cutoff combination. This is complete Fourier-Motzkin projection. Inflated native P can lie outside the tight physical penalty estimate, so discarding the compatibility rows or retaining only two cutoffs without proved domain premises can be invalid. The original unmultiplied objective cutoff is retained at S=0. Degenerate boxes and lambda=0 are treated explicitly.

These are ideal algebraic projection results. Serialized H bounds and projected coefficients have rounding effects, separately audited against the original numerical policy. Finite LP agreement and residual checks are implementation evidence, not a theorem of exact rational equality for every binary64 matrix. Equivalent projections can still differ in size, presolve, native cuts, root processing and branching.

The known-role cost panel contains four problems, two Seeds and three expressions: same-build S2R, deletion of exactly the three geometry families, and full W projection. It has 24 independently paid workflow arms and eight shared baseline observations. Each candidate has eight repeated baseline comparisons; their sixteen typed comparisons are not independent trials. No combined candidate or input-specific expression is run.

All 24 same-build cost workflows are sealed. Against S2R, geometry deletion records 2 Win, 4 Lose and 2 UNDETERMINED; full W projection records 3 Win, 3 Lose and 2 UNDETERMINED. Each candidate has eight repeated comparisons across four known problems. These mixed cost effects do not establish a stronger ideal relaxation. Unrecorded root/node fields remain unknown.

**Table 6. Every fixed same-build expression workflow (seconds).**

| Known role / Seed | S2R | Delete geometry | Project W |
| --- | --- | --- | --- |
| SC-C15-B / 0 | C 57.898 | C 26.059 | C 41.745 |
| SC-C15-B / 1 | C 32.462 | C 42.838 | C 48.594 |
| SC-B20-S / 0 | C 981.118 | O @ 707.443 | C 730.350 |
| SC-B20-S / 1 | C 675.086 | C 776.573 | C 821.224 |
| UC-C20-U / 0 | C 552.603 | C 513.698 | C 540.917 |
| UC-C20-U / 1 | C 476.819 | C 611.265 | C 497.246 |
| PB-C35-U / 0 | O @ 2370.810 | O @ 2370.559 | O @ 2372.429 |
| PB-C35-U / 1 | O @ 2373.483 | O @ 2381.417 | O @ 2370.426 |


**Table 6a. Actual expression size and costs. Paired values are Seed0 / Seed1; nodes and Work refer to MIP calls.**

| Role / expression | Root rows / columns | Continuous LP bound | H + admission (s) | MIP Work | MIP nodes |
| --- | --- | --- | --- | --- | --- |
| SC-C15-B / root | 4382 / 2321 | 0.000000 / 0.000000 | 0.619 / 0.617 | 93.23 / 54.61 | 5264 / 2144 |
| SC-C15-B / root-GEOM | 3857 / 2321 | 0.000000 / 0.000000 | 0.626 / 0.620 | 43.86 / 73.04 | 1592 / 3306 |
| SC-C15-B / root-SP | 4389 / 2320 | 0.000000 / 0.000000 | 0.620 / 0.619 | 67.81 / 86.49 | 3374 / 3351 |
| SC-B20-S / root | 6643 / 3102 | 0.117214 / 0.117214 | 1.024 / 1.010 | 1952.27 / 1320.99 | 70275 / 51800 |
| SC-B20-S / root-GEOM | 5693 / 3102 | 0.117214 / 0.117214 | 1.012 / 1.018 | 1383.68 / 1528.87 | 53604 / 52642 |
| SC-B20-S / root-SP | 6650 / 3101 | 0.117214 / 0.117214 | 1.015 / 1.015 | 1492.88 / 1681.78 | 58399 / 56807 |
| UC-C20-U / root | 7043 / 3502 | 0.122973 / 0.122973 | 0.968 / 0.963 | 1058.79 / 911.26 | 54557 / 45006 |
| UC-C20-U / root-GEOM | 6093 / 3502 | 0.122973 / 0.122973 | 0.979 / 0.963 | 975.72 / 1180.51 | 50213 / 59103 |
| UC-C20-U / root-SP | 7050 / 3501 | 0.122973 / 0.122973 | 0.989 / 0.979 | 1028.63 / 950.73 | 57467 / 49276 |
| PB-C35-U / root | 24754 / 11149 | 0.000000 / 0.000000 | 6.620 / 6.603 | 5581.54 / 5567.66 | 8607 / 9470 |
| PB-C35-U / root-GEOM | 21779 / 11149 | 0.000000 / 0.000000 | 6.597 / 6.604 | 5335.20 / 5429.23 | 10202 / 10216 |
| PB-C35-U / root-SP | 24761 / 11148 | 0.000000 / 0.000000 | 6.602 / 6.643 | 5529.99 / 5526.63 | 10202 / 9398 |

All16 candidate/baseline comparisons have identical complete realized H fleets/traces and matching actual root intervals/cutoffs; all expose their own native backend. Every workflow submits one restored-integer Start and retains its native-log acceptance evidence. Thus these comparisons control the paid startup and root domain. H + admission includes the recorded pre-exact boundary rather than an inferred pure-H CPU cost.

Deleting geometry reduces rows without changing the audited ideal projection. On SC-C15-B at Seed0 it reduces MIP Work from 93.23 to 43.86 and complete time from 57.898 to 26.059 seconds, but Seed1 reverses the cost direction (Work 54.61 to 73.04; time 32.462 to 42.838). On SC-B20-S Seed0 GEOM returns native OPTIMAL with native objective and bound about 0.3153886972242, while physical replay gives U=0.31538912105343897 and L=0.31538869722423574. The physical signed gap is about 4.238292032e-7, above the unchanged contract, so the result remains uncertified. Production takes 707.443 seconds; this is not a 1200-second timeout. A shorter process than the certified baseline does not make this certificate-direction Loss a time Win. This native/physical mismatch is distinct from X-35-U's lower bound exceeding a same-domain legal zero. W projection is also mixed. None of these observations identifies a unique presolve/cut/branching cause.

**Table 6b. All open PB-C35-U diagnostic endpoints, U / L.**

| Seed | S2R | Delete geometry | Project W |
| --- | --- | --- | --- |
| 0 | 0.18370156 / 0.08472828 | 0.17413854 / 0.08596586 | 0.16237905 / 0.08472217 |
| 1 | 0.18026766 / 0.08370043 | 0.16747142 / 0.08559747 | 0.18714524 / 0.08576977 |

At Seed0 SP has the best attained U while GEOM has the best L; at Seed1 GEOM has the best U while SP has the best L and a worse U than baseline. All six remain open, so no certification-time ranking follows. Canonical continuous LP bounds, actual MIP initial-root observations and terminal search bounds are separate fields. Unrecorded presolve/root-end Work or post-cut bounds remain unknown; a last zero-node callback is not declared the exact end of root processing. Full per-call logs, all24 cost rows, production/verification/total clocks and trajectories accompany the paper.

### 6.3 What a new joint quantity structure would have to add

Let R_k be a complete finite necessary service domain and v_k its pickup, delivery and assignment vector. Convexifying each vehicle independently and then imposing unique service gives P_sep. Convexifying jointly unique integer selections gives H_joint, which is contained in P_sep. That elementary inclusion is not itself a new result. A useful increment must survive the current canonical model, single-station theta, event rank and relevant inventory-route structure, with exactly the same R_k on both sides.

The existing independent-support/unique-access bound cannot separate points already in the product of those vehicle hulls with unique service. A genuinely joint weighted support maximum is a possible stronger object. Its exact maximum or a reliable upper bound is required as a valid cut RHS; a feasible solution or a restricted column maximum supplies only a lower bound. Quantity-weighted supports and vehicle-labelled compatibility must be compared with the actual indices and domains of existing event-count ranks; a different name alone establishes no new family.

The four-case complete tiny study is finished. J2 retains an exact full-reference service-coordinate witness with weighted value 15/2 above the complete joint support maximum 7. Its full rational extension satisfies every saved reference row and bound. Reoptimizing the original complete micro objective after adding all joint columns gives no qualified increment in any case. This is a strict projection difference on that finite loaded reference, rather than a theorem for all inventory-routing instances. Finite failure to separate other tested normals does not establish hull equality. No full-size production cut is admitted: the tiny support maxima do not include outside donors and receivers.

The complete tiny universes have four stations with capacity 2, target 1 and weight 1; all station and depot coordinates coincide. Both pickup and drop take 60 seconds per bicycle, including return unloading, and lambda is 0.15. J2/J3 cover shortage under two handling budgets; J1 is a balanced control and J4 is the physical startup-zero control. The current canonical continuous reference uses the same complete car plans on both sides, together with theta, exact same-domain threshold ranks and all 30 inventory-route subset rows. The original micro objective is reoptimized after adding every joint column. An artificial canonical model for J4 is reported separately from production backend exposure.

**Table 7. Complete tiny domains and their actual joint-structure outcomes.**

| Case / initial inventory | Q / physical T | Car plans / joint pairs | Reference / joint objective | Full-reference witness |
| --- | --- | --- | --- | --- |
| J1 / [2, 0, 1, 1] | [1, 2] / 240 | [18, 32] / 119 | 0.000000 / 0.000000 | no separated tested normal |
| J2 / [2, 1, 0, 0] | [1, 2] / 240 | [11, 23] / 59 | 0.150000 / 0.150000 | exact strict |
| J3 / [2, 1, 0, 0] | [1, 2] / 360 | [11, 30] / 66 | 0.150000 / 0.150000 | no separated tested normal |
| J4 / [1, 1, 1, 1] | [1, 1] / 240 | [35, 35] / 177 | 0.000000 / 0.000000 | no separated tested normal |

An exact strict entry denotes a rational extension in the entire saved reference matrix and an exact complete-universe support RHS. A numerical-only entry lacks that strict extension. No separated tested normal means only that the fixed finite directions did not separate; it is not a hull-equivalence conclusion. The table retains the original native floating-point observations. Proposition 4 supplies a later analytic explanation and full rational primal replay for the J2/J3 loaded LP values. Neither explanation retroactively turns the original native MIP search into a rational proof. The supporting joint note retains controls, coefficients, witnesses or explicit obstacles and measured costs.

**Proposition 3 (a vehicle-labelled J2 conflict).** Use zero-based vehicle indices and one-based station indices. In the complete J2 integer universe,

\[
d_{0,3}+d_{1,2}\le1.
\]

Each delivery is at most one. If vehicle 1 delivers at station 2, it occupies that station and must first pick up at station 1. Those are the only initially stocked stations. Empty departure and unique nonzero service then prevent vehicle 0 from acquiring a bicycle to deliver at station 3. The saved reference point has these coordinates 1 and 1/2, hence violates the inequality at 3/2; the original 24-coordinate 15/2>7 witness remains separate evidence. Its inventory (1,1,1,0) is attainable by a legal pickup at station 1 and delivery at station 3. This is a service-coordinate distinction, not a strict inventory-projection witness. The argument uses the complete four-station domain and does not permit deleting outside supply in a larger problem.

**Proposition 4 (service convexification and the objective gap).** For J2/J3, \(b=(2,1,0,0)\), \(D_i=\omega_i=1\), and \(\tau=\sum_iY_i\). Empty departure and nonnegative loaded return imply \(0\le\tau\le3\), including convex mixtures. The penalty epigraph satisfies \(\sum_i e_i\ge4-\tau\ge1\) and \(g\ge0\), so the service-hull LP has lower bound \(\widehat\lambda\). A mixture of four saved legal joint fleets, each with weight 1/4, has inventories (0,2,1,0), (2,0,0,1), (0,0,2,1) and (1,1,0,1), averaging to Y_i=3/4. At tight completion \(e_i=1/4\) and \(g=0\), it attains \(\widehat\lambda\) in the physical service-hull relaxation. Full rational replay of the saved loaded binary64 joint matrices verifies every one of the 583 rows and all 284 J2 or 298 J3 variable bounds, with zero equality residual and no violation; it attains this lower bound. Thus the loaded LP optimum is exactly \(\widehat\lambda\). This is a direct primal construction and analytic lower bound, rather than a rounded dual or a new native solve.

For integer stock and equal target \(D>0\), put \(q=\lfloor\tau/n\rfloor\), \(m=\tau-nq\). A unit transfer from a largest to a smallest stock when they differ by at least two cannot increase any third-point pair's total absolute distance. Repetition leaves \(q\) and \(q+1\), proving \(G\ge m(n-m)/(n\tau)\) for \(\tau>0\). Equal-weight relative target deviation is minimized by the same balance; with integer \(D\) and unit weights it is at least \( |\tau-nD|/D\). For \(\tau=0\) the convention here is \(G=0\) and \(P=4\). Thus \(\tau=0,1,2,3\) give lower bounds \(4\widehat\lambda\), \(3/4+3\widehat\lambda\), \(1/2+2\widehat\lambda\) and \(1/4+\widehat\lambda\). Legal fleets attain \(\tau=0\) (both vehicles pick up and return loaded) and balanced \(\tau=3\) (one pickup and delivery), within both handling budgets. Consequently

\[
F^*_{\rm IP}=\min\{4\widehat\lambda,1/4+\widehat\lambda\},\qquad
\widehat\lambda=\frac{5404319552844595}{36028797018963968}.
\]

The displayed coefficient 0.15 is this loaded binary64 value; ideal decimal 3/20 is a separate coefficient. Since the loaded value exceeds 1/12, the integer optimum is \(1/4+\widehat\lambda\), displayed about 0.40. The loaded service-hull LP value is \(\widehat\lambda\), displayed about 0.15: an exact gap of 1/4. This standard discrete balancing argument is included as a self-contained explanation, not a new majorization theorem. The first three mixture fleets have G=7/12 and P=3, and the fourth G=1/4 and P=1; they do not all have objective 0.40. Already on fixed \(\tau=3\), evaluating the objective after averaging inventories differs from convexifying its integer epigraph. No global Jensen claim for a variable-denominator fractional objective is needed. The supporting joint-objective note retains full proofs, exact matrix status and the history-to-mechanism mapping.

## 7. Operational meaning, limitations and next step

Reported fleets are interpreted through physical Gini, P_avg, final inventories, serviced stations, pickups/deliveries, loaded return and route travel/handling/prefix resources. A smaller ratio dispersion can coexist with target shortages; the penalty and actual service outcomes must be read together. Omega/rho varies because the original weights are not sum-normalized. No policy or sensitivity conclusion is inferred for an untested weight range.

**Table 8. Operational outcomes of existing and new legal S2 fleets.**

| Role / evidence | G / P_avg | Omega / rho | Initial / final stock | Pickup / delivery / return | Max route use |
| --- | --- | --- | --- | --- | --- |
| SC-C15-B (known) | 0.00284 / 0.00382 | 6.8442 / 1.0266 | 276 / 275 | 49 / 48 / 1 | 0.989 T |
| PB-C35-U (known) | 0.08058 / 0.05932 | 11.5901 / 1.7385 | 660 / 622 | 174 / 136 / 38 | 0.996 T |
| K-15-S (new) | 0.22215 / 0.26046 | 9.4734 / 1.4210 | 135 / 135 | 28 / 28 / 0 | 0.998 T |
| K-15-B (new) | 0.11765 / 0.12723 | 3.3128 / 0.4969 | 144 / 143 | 16 / 15 / 1 | 0.987 T |
| K-20-S (new) | 0.20411 / 0.30214 | 11.3125 / 1.6969 | 208 / 208 | 40 / 40 / 0 | 0.989 T |
| K-20-U (new) | 0.28241 / 0.37872 | 10.5620 / 1.5843 | 176 / 163 | 23 / 10 / 13 | 0.999 T |
| K-35-B (new) | 0.03790 / 0.02850 | 16.7227 / 2.5084 | 381 / 380 | 62 / 61 / 1 | 0.984 T |
| K-35-U (new) | 0.18694 / 0.22477 | 15.0053 / 2.2508 | 326 / 308 | 66 / 48 / 18 | 0.999 T |
| X-15-S (new) | 0.21733 / 0.28777 | 5.1061 / 0.7659 | 30 / 30 | 10 / 10 / 0 | 0.987 T |
| X-15-B (new) | 0.00000 / 0.00000 | 3.6781 / 0.5517 | 37 / 37 | 8 / 8 / 0 | 0.998 T |
| X-20-S (new) | 0.17404 / 0.25922 | 6.5853 / 0.9878 | 247 / 246 | 54 / 53 / 1 | 0.993 T |
| X-20-U (new) | 0.07744 / 0.13440 | 7.9000 / 1.1850 | 106 / 96 | 26 / 16 / 10 | 0.956 T |
| X-35-B (new) | 0.00000 / 0.00000 | 9.8844 / 1.4827 | 109 / 109 | 23 / 23 / 0 | 0.958 T |
| X-35-U (new) | 0.00000 / 0.00000 | 9.6219 / 1.4433 | 134 / 99 | 48 / 13 / 35 | 0.992 T |

The display fixes S2 at Seed0 for every new input, plus two existing final-version fleets with their historical identities. It is descriptive, not another performance panel. Full per-arm inventories, station counts, per-vehicle quantities, route travel/handling and prefix peaks are in the physical outcome tables.


An existing valid 35-station S2 fleet illustrates why these definitions matter. Its first vehicle picks up 58 bicycles over its route with Q=20 and a maximum prefix load of 20. Across the fleet, 38 bicycles return to the depot, reducing station stock from 660 to 622. This legal loaded return and repeated use of vehicle capacity would be excluded by the incorrect bound \(\sum_i p_{ki}\le Q_k\) or a fixed station-stock equality. The example remains an open historical timing observation; its physical validity does not certify optimality.

The finite inputs, synthetic inventory mechanism, Euclidean distance convention, current parser/physical semantics and single backend limit performance generalization. Finite manageable inventory states, nonnegative inventories, positive targets and unique one-way service are explicit mathematical premises. A constructible formulation in another problem does not imply measured cross-problem performance. Timeouts, reversals and lack of objective increments constrain the claims.

Fractional reformulations remain a possible separate comparison. For S>0,

\[
F=\frac{A(r)+n\lambda S P_{true}}{nS},\qquad
\min\{A(r)+nS(\lambda P_{true}-\eta)\}
\]

is the corresponding parameter subproblem. Its numerator is not simply linear because S P_true remains. Existing MILFP work is relevant background [@yue2013], but applying it here requires an exact treatment and globally qualified subproblem bounds plus the separate S=0 branch. We do not infer that general methods are mathematically unusable from an old toy comparison, nor report an unimplemented method as a weak benchmark.

The structural formulation, complete ideal-arithmetic controller and finite historical comparisons support continued manuscript preparation. Finite implementation qualification and the complete known-role version bridge support scoped manuscript preparation; final scientific/PDF/release review remains separate, and a retained own-zero proof does not restore a rejected native source. The positive-objective 35 boundary, K-35-B's UNKNOWN optimum class, native numerical uncertainty and paid-start reversals remain explicit limitations. Equivalent-expression costs are mixed, so neither candidate replaces S2. The J2 service conflict and integer-objective explanation motivate two gated research directions: an inventory-objective envelope demonstrably beyond existing state/penalty mechanisms on the same full model, or a full-site joint support bound with a proved outside interface. Neither is implemented here. Missing full-universe support and absent original-objective gain do not justify a production separator or larger matrix. The corrected implementation has its scoped finite qualification and paired bridge; broader performance claims still need broader validation, especially for unobserved natural NEXT and other untested paths. No universal speed or target-journal guarantee follows.



\clearpage


## S5. Historical implementation/source qualification tables

### B.4.1 Frozen certificate admission and replacement qualification

The following functions describe the historical E3 evidence chain. They are retained to explain the reported benchmark and its limitations. The corrected replacement has separate finite qualification in Section 5.4 and B.4.2; these historical functions do not imply that all old producer fields were correctly gated.

The native certificate function requires valid complete coverage, all relevant leaves closed, all used bounds certified, monotone bound history, a verified own finite U, completed lifecycle, and source consistency. It then accepts the one-sided test L+max(0,tolerance)≥U. It does **not** enforce a lower bound on the signed gap U−L. In particular, a negative gap of −2e−7 is not rejected by that predicate alone.

The published post-seal reader applies the stronger admission policy. Each native source must have a finished request with matching interval, epoch, model bytes/row signature and parentage; the saved parameters must match the frozen original model (including requested zero relative/absolute MIP gap); every used bound must be finite, available and sourced to the corresponding returned native request, without a counterexample or consistency failure. It reconstructs the represented children and their full interval union, preserves unresolved obligations, requires every relevant unit closed for certification, replays the own physical fleet and objective, and requires normal process completion (no killed, timed-out producer, missing seal, or failed engineering gate). These gates are conjunctions, not substitutes for one another. A clean nonzero certificate additionally requires −1e−7≤U−L≤1e−7; gaps are never clipped. Thus the above −2e−7 case is rejected after sealing.

The clean independent own-zero branch requires a physically replayed own U≤1e−12, nonnegative lambda and weights, and **no started native request**; it returns L=0 and a synthetic complete zero cover. The startup early-stop test is 0≤verified F≤1e−12; the neutral physical loop itself stops only on exact F=0. If native sources are damaged, the source-reduced fallback is stricter: it needs every Y_i=D_i and recomputed F=G=P=0 exactly. Its independent L=0 does not restore any invalid native source or dependent nonzero certificate. A retained positive feasible fleet alone supplies U, never certificate credit for damaged proof dependencies.

These are distinct functions in the frozen evidence chain: ExternalGiniTree.cpp:460–489 for native admission; read_round122/123 → read_round118.item/finalize → read_round116.reconstruct_arm → round108_reader.endpoint (328–391), with CLOSURE_TOL=1e−7 and ZERO_TOL=1e−12; round114_claims/round114_audit supplies damaged-source fallback. The rules are stated here so those links are audit references, not missing algorithm definitions.

### B.4.2 Corrected-version qualification and complete bridge

The entire 22-position D1/D3 execution matrix and original helper identities were frozen before the separate bounded positive native unit. That unit independently qualifies own U=L=1.5 against exact oracle 3/2, with complete H/Start/seal/clock and actual 3 LP+1 MIP OPTIMAL. It is excluded from the 14-position/performance sample. Independent D1 completion review passes; D3 execution was admitted before all eight full arms ran. Final science/delivery review remains a separate gate.

All 14 fixed D1 positions are sealed and independently pass finite implementation/failure-disposition qualification: 14/14 implementation, 13/14 native/source, eight certificates, five qualified-open and one naturally source-rejected safe-open. The set is exposed regression evidence, not holdout. X-35-U Seed1 reproduces the same three raw bad bounds; sequence 27 is its own zero witness, 28 records rejection and 31 the API return. Native MIP is INTERRUPTED; the dependent controller is replaced by an OPEN full domain [0,34/35], with own U=L=0 but certificate/native/performance false and T_cert null. The independent physical zero remains. Rejected raw values are absent from the qualified trace. This demonstrates correct source rejection and complete-domain preservation, not repair of the native internal search, whose cause remains UNKNOWN.

Normal positive proof functionality remains: K-15-S S2 certifies at both Seeds while cold P and paid PS remain open; the four corresponding S2 comparisons are one-sided certificate Wins and the two PS/P comparisons are both-open. GEOM loses to S2R at both Seeds; Seed0 is native OPTIMAL with physical gap 4.238292032e-7 and remains qualified-open, while Seed1 certifies in 781.293 seconds versus 681.174. These are known qualification controls, not a new performance population.

UC-B20-B at each Seed has three actual atomic splits, nine LP calls (one root and eight child), one CHILD_BOUND_TARGET_MIP interrupted after reaching its target and requeued, cached-child reuse, and one terminal OPTIMAL MIP: 11 Optimize calls. Positive certificates take 4.117/4.011 seconds. Natural NEXT calls are zero throughout D1; NEXT coverage is static and controlled D2 semantics only, with no natural NEXT performance claim. Actual native statuses come from per-call journal quality/optimize ledgers, never the generic legacy endpoint.native_status=0.

The first D1 position's original postverifier failed on accepted-H==exchange-final although its normal four-call producer was sealed. Actual reused main accepts routes only if F_new<F_old-1e-10; two neutral and zero strict improvements retain the initial accepted fleet, matching the journal. The explicit pure post-seal adapter and 41 controlled fixtures receive independent admission. The frozen four helpers, matrix, PE/native argv and original seal remain; the original failure and real delay are retained without native rerun. Adapter SHA256 is 8feae1d544d92fba843f4836f0c685c2cf38151f20386cd2538396ac34af6640, amendment SHA256 7501459291ac9a7a2945f0ce022f52a72d09822df21cec7eb014889f0a8e4f6b, normal commit c23f01aac25c55e73ea2cf2b7cc64c79db065b12. The effective reader is explicitly the original reader plus adapter, including cold P no-H and original PS numerical Start audits. First T_produce/T_cert 120.17624272953253, T_verify 1743.5059913999867 and T_total 1863.6822341295192 preserve the real repair/disposition delay. The first qualification wrapper differs; later K15 methods and both D3 versions share the amended wrapper, with all management/import/admission wall paid. No first-arm cross-version comparison is invented.

**Table Q2. All 14 fixed qualification positions (seconds).**

| Role / Seed / method | Status | Signed U-L | T_produce | T_verify | T_total | T_cert |
| --- | --- | --- | --- | --- | --- | --- |
| X-35-U / 0 / S2 | CERT | 0 | 120.176 | 1743.506 | 1863.682 | 120.176 |
| X-35-U / 1 / S2 | SOURCE_REJECTED / safe OPEN | 0 | 452.876 | 3.511 | 456.387 | null |
| SC-B20-S / 0 / GEOM | qualified OPEN | 4.23829e-07 | 712.967 | 4.689 | 717.656 | null |
| SC-B20-S / 0 / S2R | CERT | -1.66533e-16 | 990.233 | 7.881 | 998.115 | 990.233 |
| SC-B20-S / 1 / S2R | CERT | 2.46734e-10 | 681.174 | 4.641 | 685.815 | 681.174 |
| SC-B20-S / 1 / GEOM | CERT | 3.88578e-16 | 781.293 | 4.883 | 786.177 | 781.293 |
| K-15-S / 0 / P | qualified OPEN | 0.0648711 | 571.313 | 2.459 | 573.772 | null |
| K-15-S / 0 / S2 | CERT | 3.01757e-09 | 113.108 | 3.710 | 116.818 | 113.108 |
| K-15-S / 0 / PS | qualified OPEN | 0.0719118 | 571.216 | 2.285 | 573.501 | null |
| K-15-S / 1 / PS | qualified OPEN | 0.0604999 | 571.402 | 3.260 | 574.663 | null |
| K-15-S / 1 / S2 | CERT | 2.67564e-14 | 115.376 | 4.113 | 119.489 | 115.376 |
| K-15-S / 1 / P | qualified OPEN | 0.0634909 | 571.332 | 3.036 | 574.368 | null |
| UC-B20-B / 0 / S2 | CERT | 2.22045e-16 | 4.117 | 2.213 | 6.330 | 4.117 |
| UC-B20-B / 1 / S2 | CERT | 2.22045e-16 | 4.011 | 2.193 | 6.205 | 4.011 |

All eight fixed D3 arms and four complete known-role/Seed pairs finish with source/model/implementation qualification and certificates on both sides. Candidate versus original E3 gives two strict Win and two Lose; every difference is TIME_CLOSE under the unchanged materiality convention. Signed candidate-minus-original T_cert is +0.002491188934072852, -0.30825315485708416, +1.2644485813798383 and -2.450773081742227 seconds in the table order. Both sides have identical corresponding qualified endpoints; their separate actual production/verification/total clocks are retained. Independent D3 review accepts all eight arms and four pairs. Each old/new pair has the same four actual canonical model SHA values, complete own-H semantic SHA and accepted-H fleet SHA. All 32 actual model-contract marker checks are empty, and a separate scan of six unique actual canonical LPs finds no known artificial 0<=-1 row. The conservative legacy UNEVALUABLE branch was not triggered; no marker case was promoted back into eligibility. Consequently D3 does not exercise a domain where removal of that row changes the model. The bridge bounds timing claims to the two reached known-role domains; performance in changed-marker, natural NEXT or other untested domains is not established. Exact dyadic D2 tests supply the removed row's correctness check, not changed-domain performance evidence.

Each arm actually executes three LP calls and one terminal MIP, with no target or NEXT call; these known mostly-root paths do not validate broader split/target/NEXT performance stability. Both versions pay their own complete H/Start/physical/source/return costs, under the same amended management wrapper and declared resource/cap policy. Original and candidate verifiers can have different actual costs; none is subtracted. Four Seed pairs on two previously seen inputs are not four independent new problems, and this bounded bridge does not support a global speed claim or retroactively relabel R132 timings as candidate measurements.

**Table Q3. All eight complete version-bridge positions (seconds).**

| Role / Seed / method / version | Status | Signed U-L | T_produce | T_verify | T_total | T_cert |
| --- | --- | --- | --- | --- | --- | --- |
| SC-C15-B / 0 / S2 / E3 | CERT | 2.42138e-09 | 58.058 | 9.978 | 68.036 | 58.058 |
| SC-C15-B / 0 / S2 / candidate | CERT | 2.42138e-09 | 58.060 | 0.752 | 58.813 | 58.060 |
| SC-C15-B / 1 / S2 / candidate | CERT | 1.38778e-17 | 34.018 | 0.786 | 34.804 | 34.018 |
| SC-C15-B / 1 / S2 / E3 | CERT | 1.38778e-17 | 34.326 | 10.106 | 44.432 | 34.326 |
| SC-B20-S / 0 / S2 / candidate | CERT | -1.66533e-16 | 985.877 | 8.508 | 994.385 | 985.877 |
| SC-B20-S / 0 / S2 / E3 | CERT | -1.66533e-16 | 984.613 | 16.802 | 1001.415 | 984.613 |
| SC-B20-S / 1 / S2 / E3 | CERT | 2.46734e-10 | 678.002 | 13.904 | 691.906 | 678.002 |
| SC-B20-S / 1 / S2 / candidate | CERT | 2.46734e-10 | 675.551 | 5.286 | 680.836 | 675.551 |

**Table Q4. Candidate versus original E3 S2 on all four fixed pairs.**

| Role / Seed | Original T_cert | Candidate T_cert | Candidate minus original | Direction | Materiality |
| --- | --- | --- | --- | --- | --- |
| SC-C15-B / 0 | 58.058 | 58.060 | +0.002491 | Lose | TIME_CLOSE |
| SC-C15-B / 1 | 34.326 | 34.018 | -0.308253 | Win | TIME_CLOSE |
| SC-B20-S / 0 | 984.613 | 985.877 | +1.264449 | Lose | TIME_CLOSE |
| SC-B20-S / 1 | 678.002 | 675.551 | -2.450773 | Win | TIME_CLOSE |


## S6. Relation of TC to retained historical mechanisms

# Threshold-count inventory strengthening and its comparison scope

The complete derivation and actual tiny witnesses are in manuscript Section 6 and `math/tiny_exact.json`. `scripts/round134_count_bound.py` generates thresholds with exact rational comparisons, the budget-derived counts and the one-row aggregate. Actual loaded ratio coefficients define the numerical-matrix version. Noncontinuous supports use their real minimum allowed activation states. All stations remain in both budget and counts; returned load gives an upper stock budget rather than equality. Leaf-derived rows remain local. Nonnegative selectors permit downward coefficient rounding. No new DP or production switch is introduced.

The exact J2/J3 extension uses the four balanced true-fleet columns listed in the goal and verifies their actual complete services, rather than relying on saved column indices alone. Old and new points pass 583 actual matrix rows and 284/298 variable bounds. The old state-penalty rows and full sparse-prefix R88 B1/B2 plans are checked as explicit exact algebraic extensions; CDF/q-CDF prefixes have their actual cumulative values, and pairwise absolute-difference auxiliaries are zero. This is not an assertion that a new native matrix containing every historical oracle was exported or solved.

For the named reference, old LP value is lambda_hat and new LP value is lambda_hat+3/16; the integer optimum is lambda_hat+1/4. The gain is exactly 3/16, closes 75% of the 1/4 gap and leaves 1/16. Full witnesses, all row-check results and actual loaded binary64 coefficients are sealed. The original tiny carrier remains unchanged at pin 52b02252ba47e8228b73e071d6ed692385a4f816, SHA256 d2e55d7ae5fcaf5bb0c9d39a489b589006f3a29eb350b167fd790ad399a0aac1.

| Directly checked old mechanism/source | Comparison that is supported | Comparison not established |
|---|---|---|
| R55, pin06b4c0634cbb85d3440be88511c736dd3282fdc9, `results/gf_k1_am_sf_station_state_chain_round55/station_state_exactness_proof.md`; `prepare_round55_stage0.py` | State-weighted penalty/VD-J is already known; the tiny balanced mixture satisfies its lower-bound version. TC adds a strict objective increment with this old lower bound retained. | Dominance over the complete VD-J equality formulation with arbitrary nonobjective uses of e. |
| Same pin, `penalty_budget_validity.md`, `penalty_cover_validity.md`, `penalty_cover_dp_design.md`, `penalty_cover_final_decision.json` | Penalty-budget covers use a strict-improver penalty budget and multiple-choice state costs. Their prerequisite gate failed, so zero live cover positions is not evidence of invalidity or ineffectiveness. | Dominance over all penalty covers or exact DP closures. |
| R88 `scripts/round88_ot_epigraph.py` make_plan and `round88_ot_math.py` | Complete B1/B2 pairwise CDF/product algebraic extensions hold at both tiny points. TC is strictly stronger on their stated complete common reference. | Full real-root R88 closure, which the real-root three-layer comparison does not include. |
| R98 `mathematical_algorithm.md`, theta section; R101 `mathematical_algorithm.md` | Tiny common references retain stock/service marginals, theta, all tiny station-event ranks and physical cutset rows. These alone do not remove the balanced old witness. | TC dominance over every dynamic matching/Hall resource separator. |
| R103 `mathematical_algorithm.md` and `capability_table.md` | Complete tiny independent single-car support and complete joint service marginals are retained in the checked carrier. TC adds an original-objective increment beyond that specified reference. | A universal full-route hull or every historical support oracle. |
| `docs/algorithm_report.md`, frontier objective/inventory-probe sections; R90 `lp_g_split_implementation_handoff.md` / `lp_g_g3_decision.md` | Inventory-budget DP and objective bounds are pre-existing directions. LP-G changes a coverage-preserving split proposal, rather than supplying the TC inventory epigraph. | Dominance over those complete DP value functions. |
| R118 `positive_objective_proof.md` / `scripts/round118_math.py`; R114 source/floor policy | R118 gives positive stock-deficit and bulk greedy penalty floors; R114 gives source revocation and independent floor0. TC additionally connects inventory counts to the Gini numerator. | A claim that the shortage bound originated in R114, or that TC supersedes the R118 optimum penalty relaxation. |
| R120 `mathematical_contract.md` | Its qualified child bounds give a scalar g/objective envelope. TC is derived directly from inventory support and all-station budget. | A general dominance theorem against all possible qualified scalar envelopes. |

The R55 documents were read from their actual pinned blobs. R98/R101/R103/R118/R120 formulas and the maintained R133 historical-source map were read in the verified current research lineage. No historical campaign was rerun. These limited direct comparisons do not make generic threshold identities, cardinality bounds or chord inequalities novel. The targeted literature check and remaining source questions are in `literature_scope.md`.

Real-root results are stored separately in `reports/roots.json`: all three layers share the exact same current S2 matrix, actual input, stock domains, interval and cutoff. All six continuous LP positions completed OPTIMAL with recorded primal/dual quality. K-20-S gives 0.195149152441, 0.318758542616, 0.318758542616; K-35-U gives 0.200177661949, 0.273857681327, 0.273857681327. The old state penalty strengthens these roots, but TC adds no reliable objective increment. The saved old optimal points already satisfy TC with slacks about 32.4353 and 54.7314. This supports stopping the present TC exploration without new roots, Seeds or a production test. These are numerical LP observations, separate from the exact tiny theorem. A primal objective from an unfinished minimization would not be a lower bound.
