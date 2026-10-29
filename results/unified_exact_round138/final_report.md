# Round138 scientific report and stage decision

Decision: RESEARCH_ONLY. Retain the repaired uniform candidate for focused study and keep accepted GI-TBC as the stable entry.

## 1. Missing information and what is proved

Station VD-P mixtures share one Gini epigraph g but do not automatically preserve products of the cross-station physical budget with that g. Empty departure and loaded return imply Bminus <= tau = sum(Y) = B - sum(return load) <= B, with depot excluded. The four new slack-product rows couple the existing unscaled inventory products J = sum(Z) to this budget; no variable is added. They remain valid for a nonminimal epigraph g, unequal targets/weights/capacities, S = 0 and a collapsed interval. Cumulative pickups are never capped by vehicle capacity.

For the continuous selected-resource set P, full station VD-P plus both products of every defining resource row gives the common-factor product hull by the two-endpoint decomposition. With only four stock rows, this statement covers only the continuous stock-budget product block. It does not claim the hull of integer inventories, routes or the original objective. The heterogeneous two-station witness satisfies lawful ratio aggregate McCormick and violates J <= Bg by 1/8; it is explicitly a product-block witness. These are applications of standard RLT/disjunctive tools. Complete proofs and verified primary references are in mathematical_analysis.md.

## 2. TC, historical GS and AP/IND

The complete retained J2/J3 reference has exact original binary64 lambda_hat = 5404319552844595/36028797018963968 > 1/12. Exact full-matrix witnesses and lower-bound arguments establish the four cells lambda_hat, lambda_hat, lambda_hat + 3/16, lambda_hat + 1/4 = IP optimum for base, stock, TC and both. The old zero-g point is stock-feasible and TC-infeasible; the old TC attaining point violates stock by 3/16. The TC-only cell is limited to this reference/coefficient. All noncomparison auxiliaries retain their freedom; full 583-row and 284/298-bound replay, old state penalty and declared R88 extensions are retained, including zero-inventory loaded return. No unchanged historical enumeration or new tiny Optimize was used.

Historical independent aggregate GS was already implemented and fixed-subproblem tested. With equal targets and tight S, it can also close the same tiny TC gap. The present distinction is shared Z/q consistency in a physical stock direction, which differs from the ratio direction under heterogeneous targets. Current GS controls use safe same-domain S bounds, no reverse-H row and no old bucket architecture. R55 station MC4/VD-P and R135 AP/IND keep their original scope and mixed/negative evidence; AP remains off.

For S bounds valid for the selected continuous stock polytope, endpoint decomposition also proves the ideal conditional inclusion: stock is contained in shared GS, which is contained in the original-variable projection of independent GS (choose its independent W equal to shared W). The present fractional-knapsack bounds satisfy that premise. The heterogeneous witness establishes reverse failure only in the pure product block. This is not a claim about arbitrary route/cutoff-tightened historical GS, strict inclusion of full BRP/TC formulations, or an exact dominance certificate for outward floating matrices.

## 3. Saved points and same-domain original-objective LP gains

| Saved role | J - Bg | True G at saved Y |
|---|---|---|
| K-35-U | 8.30742 | 0.0714063 |
| R-X20-S-T1 | 6.54633 | 0.175199 |
| R-X35-S-T2 | 7.30714 | 0.0892857 |
| K-20-S | 4.7315 | 0.046519 |

The first three motivating points came from fixed R137 carriers; K20 is an additional known control. K35 has integer Y at all 35 stations and still has 78 fractional station selectors. Auxiliary g, true G and the full LP objective remain distinct.

| Role | Fresh base L | Stock L | TC L | TC + stock L |
|---|---|---|---|---|
| K-35-U | 0.200178 | 0.218089 | 0.200178 | 0.218089 |
| R-X20-S-T1 | 0.331594 | 0.377558 | 0.332136 | 0.377558 |
| R-X35-S-T2 | 0.1861 | 0.193136 | 0.1861 | 0.194522 |
| K-20-S | 0.195149 | 0.20459 | 0.202625 | 0.224542 |

| Role | Stock delta L | TC + stock delta L | Common validated U |
|---|---|---|---|
| K-35-U | 0.0179111 | 0.0179111 | 0.767457 |
| R-X20-S-T1 | 0.0459632 | 0.0459632 | 0.753054 |
| R-X35-S-T2 | 0.00703632 | 0.00842207 | 0.42465 |
| K-20-S | 0.00944129 | 0.0293929 | 0.775213 |

| Role | Independent GS L | Shared GS L | Stock L |
|---|---|---|---|
| K-35-U | 0.218089 | 0.218089 | 0.218089 |
| R-X20-S-T1 | 0.364502 | 0.364502 | 0.377558 |

All 20 new LPs use explicit Seed0, Threads1 and the exact original input, T, binary64 lambda, supports, g interval, native cutoff and old rows. Noncomparison auxiliaries reoptimize freely. Four rows/zero columns are the stock delta. Full vectors, quality and original-matrix residual checks are preserved; the reported LP optima are numerical, not rational certificates. Equal objective values do not establish row redundancy or polytope equality.

## 4. Complete method, finite second Seed and exploration

There are eight physical/objective configurations on six inputs and sixteen nominal core method positions. Eight exactly matched accepted R137 baselines are reused. Eleven new Seed0 positions comprise eight uniform stock candidates, a contemporaneous frozen-PE K15 bridge, and two 90-second micro controls. Full own H and all online construction/search/proof costs are paid independently. Resource-panel rho is 1 with original exact lambda = 1/Omega; physical T and compute cap are separate. No cross-method/Seed/weight solution, bound, tree or Start is transferred.

| Role | Base U | Stock U | Base L | Stock L | Base cert s | Stock cert s |
|---|---|---|---|---|---|---|
| K-15-S | 0.592265 | 0.592265 | 0.592265 | 0.592265 | 112.769 | 33.8182 |
| R-X20-S-T1 | 0.645325 | 0.645325 | 0.645325 | 0.645325 | 20.5065 | 15.3405 |
| K-20-S | 0.716807 | 0.716807 | 0.705356 | 0.716807 | open | 101.635 |
| K-35-U | 0.692854 | 0.669596 | 0.565766 | 0.556777 | open | open |
| R-B35-S-T1 | 0.591518 | 0.569975 | 0.455904 | 0.500843 | open | open |
| R-B35-S-T2 | 0.344643 | 0.4012 | 0.218986 | 0.229182 | open | open |
| R-X35-S-T1 | 0.59219 | 0.592026 | 0.463358 | 0.491023 | open | open |
| R-X35-S-T2 | 0.403272 | 0.409855 | 0.210887 | 0.21498 | open | open |

| Role | Base signed gap | Stock signed gap | Base relative gap | Stock relative gap |
|---|---|---|---|---|
| K-15-S | 3.01757e-09 | 1.87628e-14 | 5.09497e-09 | 3.16797e-14 |
| R-X20-S-T1 | 2.22045e-16 | 1.22125e-15 | 3.44082e-16 | 1.89245e-15 |
| K-20-S | 0.0114508 | 7.77156e-15 | 0.0159747 | 1.08419e-14 |
| K-35-U | 0.127089 | 0.112819 | 0.183428 | 0.168488 |
| R-B35-S-T1 | 0.135614 | 0.0691321 | 0.229264 | 0.12129 |
| R-B35-S-T2 | 0.125657 | 0.172019 | 0.3646 | 0.42876 |
| R-X35-S-T1 | 0.128832 | 0.101003 | 0.217552 | 0.170605 |
| R-X35-S-T2 | 0.192385 | 0.194875 | 0.47706 | 0.475473 |

Open certificate times are null. A timeout is not a known convergence time. For both-certified pairs the substantive threshold is max(10 seconds, 10% of the smaller certificate time). Qualified T_produce/T_cert include full online production and seal; T_verify is separately retained, and T_total is also in the full arm data. Native process trace time is a separate diagnostic clock. G/P_avg/S and complete phase/effort fields are retained in reports/new_arms.csv and pairs.csv.

The primary certificate count is 2/8 for matched GI-TBC and 3/8 for stock RLT. K15 certifies in 33.818227 seconds versus 112.769303 seconds, a substantive difference under the declared rule; the separate contemporaneous BASE bridge takes 122.579382 seconds. RX20 certifies in 15.340479 versus 20.506462 seconds, below the ten-second substantive threshold. K20 adds a certificate in 101.635385 seconds while its baseline remains open at cap1200; no baseline convergence time or capped time ratio is invented. All five n35 primary configurations remain open. RB35-T1 and RX35-T1 improve both U and L, with the RX35-T1 improvement mostly in L. K35 improves U but loses L. RB35-T2 improves L but materially worsens U and both gap measures. RX35-T2 improves L but worsens U and signed gap, even though its relative gap is slightly smaller. The component table shows that RB35-T2 worsens both true G and P_avg; RX35-T2 improves P_avg but its G increase is larger. No endpoint is hidden by a preferred gap measure. Both micro controls certify in about one second; their small time difference gives no substantive overhead conclusion.

| Control | Method | Certificate s | T produce s | U | L |
|---|---|---|---|---|---|
| K-15-S | BASE | 122.579 | 122.579 | 0.592265 | 0.592265 |
| SM-B10-B | BASE | 1.13214 | 1.13214 | 0.535891 | 0.535891 |
| SM-B10-B | STOCK | 1.04893 | 1.04893 | 0.535891 | 0.535891 |

The K15 bridge initially failed only the postreader lifecycle version adapter after normal sealed native completion. Its failed fee/logs remain. The reviewed strict modern adapter repair reused that sealed run and performed verification only; no native repetition or tolerance relaxation occurred. Pre-Optimize setup/parser/cutoff preflight failures likewise remain in the diagnostic carrier. The actual stored native cutoff was used after detecting that Python physical U reconstruction differed by one ULP.

The bridge recorded T_verify = 342.185105 seconds, an elapsed closeout interval that includes the postreader repair delay. Actual verification-process wall costs are separately metered in fees; the delay is not relabeled as native computation.

Before any Seed1 Optimize, actual native readback found that the V1 tiny-alpha qualification file lost negative 1e-13 Y coefficients on import. Such loss can invalidate an upper row; the failure is retained and its 4.3128927000798285 seconds are charged. V2 fixes only these new rows by exact positive power-of-two scaling for nonzero slopes below 1e-12, including the already outward RHS; finite guards reject unrepresentable transport. Seven actual Native domains pass after repair. All 33 used primary STOCK calls (25 unique models) have positive interval endpoints at least 0.21232492258182034, and their original Native coefficient maps/RHS were checked exactly; the changed branch is absent. The 20 real LP domains also remain unchanged. V1 science/source/PE and the unused original Seed1 registration remain retained. The new Seed1 registration and private scaled-row reader were independently accepted after this bridge. There was no full primary rerun, retagging, tolerance change or bound backfill.

The limited second Seed was selected after all eleven new Seed0 positions and the complete eight-configuration comparison were sealed. K-20-S tests the main certificate benefit: stock certifies in 101.63538490096107 seconds while matched GI-TBC remains open at its 1200-second cap. R-B35-S-T2 tests the largest observed U regression: stock U rises by 0.05655759224710244 and the signed gap worsens from 0.12565667598847344 to 0.172018618174727 despite a higher L. K35 and RX35-T2 opposed endpoints remain in the primary table; they are not replaced or discarded. This is conditional finite confirmation, not a new independent sample or a runtime-distribution estimate. Both methods start fresh, pay their full own H and other costs, use Gurobi Seed1 with H seed20260626, and retain the original physical parameters and caps. Before any Seed1 Optimize, actual native coefficient readback exposed a tiny-slope LP-reader transport defect. All primary scopes were natively bridged and unaffected. STOCK Seed1 therefore uses the separately registered V2 exact power-of-two transport build; this is disclosed as a build confirmation as well as a limited second Seed, not a pure Seed-only change. The original unused registration/gate is retained under repair/seed1_pre_coefficient_fix.

| Selected role | Method | Seed | Certificate s | U | L |
|---|---|---|---|---|---|
| K-20-S | BASE | 1 | open | 0.716807 | 0.701669 |
| K-20-S | STOCK | 1 | 90.2348 | 0.716807 | 0.716807 |
| R-B35-S-T2 | STOCK | 1 | open | 0.322245 | 0.231139 |
| R-B35-S-T2 | BASE | 1 | open | 0.359554 | 0.218146 |

K20 retains the selected certificate benefit: BASE remains open at its 1200-second cap, whereas V2 STOCK certifies in 90.234798 seconds at U=0.716806546278. For RB35-T2, Seed1 STOCK U=0.322244841747 is better than BASE U=0.359553680417; STOCK L=0.231139449096 is better than BASE L=0.218146224605. The respective signed gaps are 0.091105392651 and 0.141407455812. These observations complement the adverse primary Seed0 result rather than replacing it. STOCK uses the separately disclosed V2 repair build; all primary model scopes were exactly/native bridged with scale one. This finite conditional check does not estimate a runtime distribution or establish independent validation.

The mathematical budget-product gap and all four real same-domain LP increments are established. Those increments sometimes yield complete proof benefits, particularly on K20 and K15, but they do not order finite-budget primal/dual endpoints on the resource-constrained n35 roles. The selected second Seed retains the K20 certificate benefit and reverses the RB35-T2 U direction. The known panel and selected second Seed support a focused research conclusion, not universal dominance, a new unseen benchmark claim, or an additive allocation of runtime benefit.

Offline handling-product checks found no violation at the four saved stock LP optima. When mT/(pickup+drop) >= B, local VD-P already implies those handling products; RX20 and RX35-T2 satisfy this sufficient condition. Other nonviolations are point observations. The four GS optimum witnesses also satisfy product rows for a tighter safe lower S bound. These zero-Optimize checks did not justify a second full variant. No broad AM/Seed/ablation matrix, P/PS rerun, or unchanged tiny enumeration was performed. TC+stock remains an LP comparison rather than an untested full algorithm result.

## 5. Adoption, preserved entry and next question

Keep GI-TBC+stock-RLT research-only. The continuous-block explanation, real-root improvements and repeated K20 certificate benefit justify retaining the uniform four-row mechanism for further study. The primary upper-bound regressions on two resource configurations and K35 lower-bound regression leave insufficient evidence for a default promotion. Preserve the accepted GI-TBC entry/profile/PE and expose the repaired V2 only through its separate explicit research entry. This decision does not require every role to win; it reflects the size and practical relevance of the observed opposed endpoints.

The next informative question is whether the four inventory rows in the target MIP delay verified incumbent discovery even when their LP bounds improve. A minimal screen is one Seed0 BASE/STOCK target-MIP pair on the same saved initial RB35-T2 interval, exact objective/cutoff and physical input, with no imported Start and at most 120 seconds each. Record first own physically verified improvement and supported L. Label it a fixed-subproblem diagnostic; do not backfill it into the completed full runs. Only if that screen supports the mechanism should a separately named uniform LP-bound-only placement of stock RLT receive a small complete pilot. This directly tests a primal/dual placement question without another AM grid or broad Seed repetition.

Primary measured STOCK source is 83928377336a860acf78f684d1723a5040467bb5; PE SHA256 is a41ea8eefd8551799a1d08e6d328beba1b70856433b07d96551790f0f5a4d8ae. Delivered/Seed1 V2 source is 04506fa613446d2ef2bd19794f778909422c51fd; PE SHA256 is f4c764ff7164bf042ef612403f82b850698b97c80018bf06b2feff1167d65403. The explicit candidate entry is scripts/paper_s2_stock_rlt.py with config/gi_tbc_stock_rlt_round138.json. The stable scripts/paper_s2.py, config/gi_tbc_round137.json, compatibility config/paper_s2.json and frozen R137 PE retain their bytes and identity. Production C++ defaults stock RLT off. The new entry is separately validated and marked research-only.

## 6. Cost, validation and finite delivery

At this scientific freeze, charged new outer experiment computation is 18214.684111 seconds (5.059634 hours); remaining allowance is 68185.315889 seconds out of 86400. Native complete outers contribute 18139.989472 seconds and diagnostics 74.694639 seconds. Qualification includes the 26 zero-Optimize native exporter processes (28.384607 seconds), charged once. Reused baselines retain their original complete costs in the comparisons and incur no new fictitious computation. Nested H/LP/MIP/Work is never added twice.

At the same freeze, disjoint fee-recorded ordinary work after qualification reclassification is 145.303484 seconds; additional disjoint analysis/document/delivery stages recorded so far are 40.087757 seconds. Final delivery cost_report.json includes subsequent recorded steps. Interactive reading/writing is not precision-metered, and offline point checks overlapping native time are not added again.

Independent reviews cover math, implementation, LP/full admission, the postreader amendment, selected Seed1 admission and final integration. The native seven-domain coefficient/RHS readback has zero Optimize; the new entry dry check, exact tiny replay and additive local sealed-run semantic checks likewise have no Optimize or commercial DLL load. Original full postreaders retain H/Start/proof qualification; the additive local replay is not mislabeled as a new independent full semantic proof.

Scientific artifacts include the incremental manuscript/PDF, exact tiny dependencies, necessary new source/raw/failed-attempt carriers and their per-member indices. source_publication.json and carrier_manifest.json bind actual source/input bytes. The final publication pin, open Draft PR readback, bounded anonymous new-carrier byte/member recovery and current-round preview-only cleanup are recorded separately in publication_pin.json, PR_delivery.json, public_restore_receipt.json and cleanup_receipt.json. Those late metadata records are authoritative for delivery state; they do not trigger recursive repackaging of already fixed science. Public byte readability does not imply a full public semantic replay. R137 historical recovery limitations remain unchanged. No old round is restored wholesale or deleted, and no commercial native asset or credential is published.
