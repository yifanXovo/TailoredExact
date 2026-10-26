# Historical evidence with original version identities

### 6.1 Historical R126 predecessor design and one-method question

At execution of the historical R126 panel, full three-station M-B was the sole proposed method; the current paper method is S2/MS2. Before generating any Round126 input or seeing its difficulty, we fixed the six problems, two method entries, order, Seed and budgets in Table SC1. Cold P-GRB is the complete original compact model. It receives no H, incumbent, route, bound, Start, certificate, cache or prior solve from M-B. M-B pays for its own unchanged H, VD-P, implicit integer service, A/B, static strengthening, NEXT/AM, full cover and outputs on every problem. ENS-C is a predecessor/representation comparator retained in the historical section; it is not selected per instance or run in this panel. D1 selection is closed, D0 is not a fallback, and no engine switch or fusion is used.

**Table SC1. The entire fixed Seed0 panel.** Pickup/drop are 60/60 seconds and lambda is .15 in every row. P denotes cold P-GRB. Each method occupies the first position three times.

| Problem | Source | n/m | Geometry / stock | Q | Physical T (s) | Production cap (s) | Order |
|---|---|---|---|---|---|---|---|
| SC-C15-S | CITI | 15/2 | compact / shortage | [30, 30] | 3600 | 600 | P, M-B |
| SC-B15-S | CABI | 15/2 | regional / shortage | [20, 40] | 5400 | 600 | M-B, P |
| SC-C15-B | CITI | 15/2 | regional / balanced | [30, 30] | 5400 | 600 | P, M-B |
| SC-B20-S | CABI | 20/2 | compact / shortage | [30, 30] | 5400 | 1200 | M-B, P |
| SC-C20-S | CITI | 20/2 | regional / shortage | [20, 40] | 7200 | 1200 | P, M-B |
| SC-B20-U | CABI | 20/2 | compact / surplus | [30, 30] | 7200 | 1200 | M-B, P |

**Table SC1b. All six station-stock and weight totals.** Depot placeholders are excluded. Weights are maximum-normalized, not sum-normalized.

| Problem | sum initial | sum target | sum weights | lambda sum weights |
|---|---|---|---|---|
| SC-C15-S | 157 | 178 | 9.599999 | 1.43999985 |
| SC-B15-S | 99 | 114 | 8.98 | 1.347 |
| SC-C15-B | 276 | 276 | 6.844233 | 1.02663495 |
| SC-B20-S | 191 | 217 | 6.98892 | 1.048338 |
| SC-C20-S | 231 | 263 | 7.721076 | 1.1581614 |
| SC-B20-U | 149 | 129 | 6.270832 | 0.9406248 |

All six inputs were generated once from the two already safe frozen station tables. CITI source identity is `9f9aad24e61d661971c24c6f5ec78a69081edf01ffc433563e52a70b2eaca2d0`. CABI source identity is `d4e664c3ecb8c580e95d39541555be9cf592666a515cb854a857fb1d117ff0b8`, with safe-table identity `d982051e5871c575ecdf9df538605401bd98341ae9b3b48112482eff80d42ffa`. The family is `round126-small-certification-v1|source=<source>|source_sha256=<identity>`, and each selection ID is `r126_<problem>_<geometry>_r<replicate>`. The family enters the original anchor hash and the real selection ID enters target/inventory hash material. The adapter is `round126-thin-offline-adapter-v1`.

The original four anchors, compact/regional geometry, tie rules, three-decimal coordinates, target fractions [.44,.56], total correction/sign repair, maximum-normalized six-decimal weights, centroid depot and distances are retained. Only the declared family/ID and table parameters change. Source capacities and coordinates are geographical data; inventories, targets, weights, depot and fleet settings are constructed. No H, LP, MIP or difficulty filter chose or redrew a problem. Station overlaps are recorded. The six problems are not a complete factorial design, IID city samples or six cities.

For the four shortage problems, service stations alone satisfy s=sum D-sum b>0. Empty departure and nonnegative loaded return imply sum Y<=sum b. Thus, with delta=min(lambda*omega_i/D_i)>0,

\[
F(Y)\ge\sum_i(\lambda\omega_i/D_i)|Y_i-D_i|
\ge\delta\sum_i|Y_i-D_i|\ge\delta s>0.
\]

**Table SC2. Independent positive-objective arithmetic.** The coefficients are the exact decimal interpretation of the serialized weights and lambda=.15; parsed binary64 values are also recorded. These floors are not injected into the solver or substituted for its reported L. Empty fleets remain legal, so shortage does not mean infeasibility.

| Shortage problem | sum b | sum D | s | Exact-decimal positive floor |
|---|---|---|---|---|
| SC-C15-S | 157 | 178 | 21 | 0.111999825 |
| SC-B15-S | 99 | 114 | 15 | 0.09 |
| SC-B20-S | 191 | 217 | 26 | 0.0864264375 |
| SC-C20-S | 231 | 263 | 32 | 0.089256 |

Balanced and surplus objectives were not presumed zero or positive. A qualified H zero termination is labelled startup-zero and supports termination of the complete method, without credit to a nonzero native proof or interval backend.

### 6.2 Complete production clocks and certificate admission

The production executable and DLL are the unchanged frozen identities specified in Section 5 and the reproducibility record. Both entries use Gurobi Seed0, Threads1, PresolveAuto and the original remaining parameters, requesting relative/absolute MIP gaps zero. Evidence tolerance remains 1e-7. H retains seed 20260626. The 30-second native reserve, cap-minus6 CLI request, cap-minus2 external hard stop and common absolute deadline are inherited; preparation is not moved outside the clock. A larger cap can change a path and is not treated as a freely reusable prefix.

T_produce runs from full method start through normal output sealing, including own H, all models/LP/MIP work, static rows, Start, online verification, callbacks, cleanup and required output. T_verify is independent post-seal validation without new optimization or route search. T_total is their sum; cross-arm reconciliation is separately billed group work. Define T_cert=T_produce only when the final certificate passes every own physical, numerical, identity, scope, cover, return and lifecycle gate; otherwise T_cert is null. It is not first incumbent discovery, Gurobi Runtime or the final MIP call's runtime.

Clean nonzero certification uses the inherited signed-gap admission -1e-7<=U-L<=1e-7 alongside all other gates. Raw L is not clipped to U. Clean own-zero and damaged-source exact-zero retain their distinct inherited policies. Same-input cross-arm witnesses are reconciled only after both own productions, using the unchanged 1e-7 scope/consistency rule; they never supply the other arm's starting information. A damaged bound cannot be repaired by a good fleet or another certificate.

The five main categories are BOTH_CERTIFIED, MB_ONLY_CERTIFIED, P_ONLY_CERTIFIED, BOTH_OPEN and UNEVALUABLE. Both-certification speedup is T_cert(P)/T_cert(M-B), so values above one favor M-B. We display every exact observed time difference and ratio; the descriptive materiality threshold is max(30 seconds,.10*T_cert(P)), producing MB_FASTER/P_FASTER/TIME_CLOSE. This threshold is neither statistical significance nor an engineering gate. Open U/L/gap comparisons are supplementary and generate no main WIN. A normal open native return before its nominal cap is reported at its actual duration: neither the cap nor actual open duration is substituted as a hypothetical certification time, exact speedup or unproved speedup lower bound.

### 6.3 All twelve arms, six pairs and evidence limits

**Table SC3. Complete own endpoints.** All signed gaps are retained. Full-precision CSV and source/call/model/fleet indices are part of the package.

| Problem | Method | Own U | Qualified L | Raw signed U-L | Certificate / evidence |
|---|---|---|---|---|---|
| SC-C15-S | P-GRB | 0.462806408538 | 0.462806408538 | 1.11022302463e-16 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-C15-S | M-B | 0.462806408538 | 0.462806408538 | 5.55111512313e-17 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-B15-S | M-B | 0.94700467634 | 0.94700467634 | 1.55431223448e-15 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-B15-S | P-GRB | 0.94700467634 | 0.94700467634 | 8.881784197e-16 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-C15-B | P-GRB | 0.0067607771599 | 0.0067607771599 | -1.73472347598e-17 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-C15-B | M-B | 0.0067607771599 | 0.0067607771599 | 1.56125112838e-17 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-B20-S | M-B | 0.315389121053 | 0.315389106185 | 1.48683525492e-08 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-B20-S | P-GRB | 0.340249880289 | 0.209049610255 | 0.131200270034 | no / RELIABLE_POSITIVE_LB_OPEN |
| SC-C20-S | P-GRB | 0.280579842119 | 0.161051808386 | 0.119528033733 | no / RELIABLE_POSITIVE_LB_OPEN |
| SC-C20-S | M-B | 0.216430184034 | 0.207366884943 | 0.00906329909051 | no / RELIABLE_POSITIVE_LB_OPEN |
| SC-B20-U | M-B | 0.173761789119 | 0.173761789119 | 4.16333634234e-16 | yes / CLEAN_NONZERO_CERTIFICATE |
| SC-B20-U | P-GRB | 0.221769088877 | 0.0133968443922 | 0.208372244485 | no / RELIABLE_POSITIVE_LB_OPEN |

**Table SC4. All three clocks and certification costs (seconds).** Unknown certification time is shown as unknown, never replaced by the cap.

| Problem | Method | Cap | T_produce | T_verify | T_total | T_cert |
|---|---|---|---|---|---|---|
| SC-C15-S | P-GRB | 600 | 464.293373 | 6.0499092 | 470.343282 | 464.293373 |
| SC-C15-S | M-B | 600 | 41.5624639 | 1.1568301 | 42.719294 | 41.5624639 |
| SC-B15-S | M-B | 600 | 6.85265371 | 0.9079541 | 7.76060781 | 6.85265371 |
| SC-B15-S | P-GRB | 600 | 12.9786823 | 0.3325261 | 13.3112084 | 12.9786823 |
| SC-C15-B | P-GRB | 600 | 243.923894 | 0.3062603 | 244.230154 | 243.923894 |
| SC-C15-B | M-B | 600 | 44.0815251 | 0.9998445 | 45.0813696 | 44.0815251 |
| SC-B20-S | M-B | 1200 | 1069.00171 | 5.1936419 | 1074.19536 | 1069.00171 |
| SC-B20-S | P-GRB | 1200 | 1170.67074 | 23.7145084 | 1194.38525 | unknown |
| SC-C20-S | P-GRB | 1200 | 1173.28631 | 1.3285943 | 1174.6149 | unknown |
| SC-C20-S | M-B | 1200 | 1170.76201 | 4.9794916 | 1175.7415 | unknown |
| SC-B20-U | M-B | 1200 | 18.8735701 | 1.7018773 | 20.5754474 | 18.8735701 |
| SC-B20-U | P-GRB | 1200 | 1170.65504 | 1.7020734 | 1172.35712 | unknown |

**Table SC5. All six fixed paired outcomes.** Positive P-minus-M-B means less M-B production time. Single-sided categories are qualitative censored observations; failures are UNEVALUABLE rather than ordinary censoring.

| Problem | Main category | P minus M-B (s) | T_cert P/M-B | Time description | T_total P/M-B |
|---|---|---|---|---|---|
| SC-C15-S | BOTH_CERTIFIED | 422.730909 | 11.1709781 | MB_FASTER | 11.0100902 |
| SC-B15-S | BOTH_CERTIFIED | 6.12602859 | 1.89396442 | TIME_CLOSE | 1.71522756 |
| SC-C15-B | BOTH_CERTIFIED | 199.842369 | 5.5334722 | MB_FASTER | 5.41754069 |
| SC-B20-S | MB_ONLY_CERTIFIED | unknown | unknown | censored / no time ratio | unknown |
| SC-C20-S | BOTH_OPEN | unknown | unknown | censored / no time ratio | unknown |
| SC-B20-U | MB_ONLY_CERTIFIED | unknown | unknown | censored / no time ratio | unknown |

The fixed denominator is six problems and twelve arms. The pairs comprise 3 both-certified, 2 M-B-only, 0 P-only, 1 both-open and 0 unevaluable observations. M-B certifies 5/6 problems, including 5 nonzero and 0 zero objectives (0 startup-zero). Cold P certifies 3/6, including 3 nonzero and 0 zero objectives. A problem certified by both remains one problem. All certified physical values appear in Table SC3 and the summary, rather than being pooled across instances.

The BOTH_CERTIFIED intersection is {SC-C15-S, SC-B15-S, SC-C15-B}, size 3. Its observed speedup median is 5.5334722 and geometric mean 4.89200527. This conditional intersection does not estimate a whole-panel mean. The neighboring single-sided and open counts above remain part of the result; no cap filling, PAR-2 time, best-of-Seed or selected-problem average is used. T_total reverses the observed production-cost ordering on SC-C20-S. Both cost views are retained. On an open pair this is an output-cost observation, with no certification-time ordering or speedup inference; T_produce remains the main certification clock where qualified.

The evidence provides limited direct certification support on SC-C15-S, SC-C15-B, SC-B20-S, SC-B20-U. No problem meets the predeclared opposite material-time or P-only category. This does not turn the remaining problems into wins or establish a population runtime claim.

For the historical Round126 Seed0 cohort, the preregistered evidence classification is `LIMITED_DIRECT_CERTIFICATION_SUPPORT`, with w=4 and l=0, and the execution state is `COMPLETE`. These are bounded evidence labels, not acceptance standards or universal stability tests. The mathematical propositions establish representation, valid embedding and complete proof obligations under their premises; the measured speed/certification counts are empirical statements. This cold-baseline comparison measures the complete method and does not identify the separate causal contribution of cuts, AM or H. All four shortage cases remain visible, including the both-open SC-C20-S.

### 6.4 Seed confirmation with the original executable

Round127 v3 retains the six problems and original complete caps, changes Gurobi Seed from 0 to 1, and independently pays both original executable E0 arms. These are six problems under two Seeds, with no best-of-Seed selection. The new symmetric direction uses strict unrounded complete certification cost on both-certified pairs, or a qualified certificate against a valid open comparator. Both-open is undetermined. The historical materiality labels in Section 6.3 remain historical; Table R127-S reports the additional symmetric direction.

**Table R127-S. E0 Seed1 certification and transition from the same six Seed0 problems.** Times are complete production seconds, present only for qualified certificates.

| Problem | Seed0 status / direction | Seed1 status / direction | MB cert s | P cert s |
| --- | --- | --- | --- | --- |
| SC-C15-S | Both certified / Win | Both certified / Win | 35.556 | 474.432 |
| SC-B15-S | Both certified / Win | Both certified / Win | 2.917 | 16.098 |
| SC-C15-B | Both certified / Win | Left only certified / Win | 65.243 | open |
| SC-B20-S | Left only certified / Win | Left only certified / Win | 975.413 | open |
| SC-C20-S | Both open / Undetermined | Both open / Undetermined | open | open |
| SC-B20-U | Left only certified / Win | Left only certified / Win | 15.455 | open |

Seed1 gives BOTH_CERTIFIED: 2, LEFT_ONLY_CERTIFIED: 3, BOTH_OPEN: 1. MB has 5 observed wins, 1 undetermined comparison. The conditional geometric mean P/MB ratio is 8.582 over 2 both-certified problems; this intersection does not represent the open runs.

The symmetric directions remain five wins and one undetermined comparison across the two Seeds. MB retains five certifications; P changes from three to two because SC-C15-B is valid open at Seed1. This preserves the limited confirmation while retaining the observed certification-status change.

### 6.5 Historical full-M-B tiny cases, repeated Seeds and absolute delay risk

Two once-generated geographic cases, SM-C8-S (V8/M1, shortage, Q=20, T=2400) and SM-B10-B (V10/M2, balanced, Q=15/25, T=3600), use E0 and a 90-second complete cap. Each uses Seeds 0,1,2 and two independent repetitions with reversed method order. No warmup or cross-run fleet, bound, Start or basis is shared. Twelve matched observations still concern two problems. The 10-second axis is an absolute observed-delay warning, not an internal method switch or statistical significance threshold. A smaller positive delay is still a direction Lose.

**Table R127-T. All tiny observations.** Delta is MB minus P, only when both certify. Displayed values are rounded; directions and the >=10-second test use original unrounded times.

| Problem | Seed / repeat | Status | Direction | MB cert s | P cert s | Delta s | Delta >=10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SM-C8-S | 0/1 | Both certified | Win | 3.407 | 5.661 | -2.254 | False |
| SM-C8-S | 0/2 | Both certified | Win | 3.723 | 5.230 | -1.507 | False |
| SM-C8-S | 1/1 | Both certified | Win | 2.832 | 3.893 | -1.061 | False |
| SM-C8-S | 1/2 | Both certified | Win | 2.469 | 4.214 | -1.745 | False |
| SM-C8-S | 2/1 | Both certified | Win | 2.650 | 4.693 | -2.043 | False |
| SM-C8-S | 2/2 | Both certified | Win | 2.975 | 4.335 | -1.360 | False |
| SM-B10-B | 0/1 | Both certified | Win | 0.814 | 0.869 | -0.055 | False |
| SM-B10-B | 0/2 | Both certified | Win | 0.481 | 1.170 | -0.689 | False |
| SM-B10-B | 1/1 | Both certified | Win | 0.534 | 1.069 | -0.536 | False |
| SM-B10-B | 1/2 | Both certified | Lose | 0.830 | 0.746 | 0.083 | False |
| SM-B10-B | 2/1 | Both certified | Lose | 0.900 | 0.824 | 0.077 | False |
| SM-B10-B | 2/2 | Both certified | Win | 0.471 | 1.134 | -0.663 | False |

SM-C8-S: 6/6 both-certified, 0 P-only, 0 observed delays at least 10 seconds. Median delta -1.626 seconds (all six pairs); repeated warning=no, all-six median warning=no. Per-Seed paired differences in seconds (repeat1, repeat2) are Seed0: (-2.253792, -1.507034); Seed1: (-1.060989, -1.744591); Seed2: (-2.043333, -1.360336). No cap is substituted for a missing certification time.

SM-B10-B: 6/6 both-certified, 0 P-only, 0 observed delays at least 10 seconds. Median delta -0.295 seconds (all six pairs); repeated warning=no, all-six median warning=no. Per-Seed paired differences in seconds (repeat1, repeat2) are Seed0: (-0.054771, -0.689162); Seed1: (-0.535587, +0.083291); Seed2: (+0.076776, -0.662628). No cap is substituted for a missing certification time.

The twelve observations give ten wins and two losses for MB. The losses are SM-B10-B Seed1/repeat2 (+0.083291 seconds) and Seed2/repeat1 (+0.076776 seconds). Thus no 10-second warning or P-only event was observed in this finite sample, while the small timing regressions remain explicit; the data do not establish their absence on other runs.

The SM-B10-B Seed0/repeat1 MB producer was sealed once at 0.814122304 seconds. A legacy comparison treated H's omitted empty vehicles and the committed explicit [0,0] unused routes as different. The correction normalizes only this handoff comparison after validating unique in-range vehicle identities; all physical/model/type/return/coverage checks remain. The original failed audit and each read-only recovery attempt are preserved. No native solve was repeated. Its actual verification span remains 650.179386500 seconds and total 650.993508804 seconds, including the recovery delay; these values are not substituted for its original certification production cost. Machine fees separately measure actual verification processes and retain both failed and successful parent segments.


### 6.6 Grouped mechanism diagnostics on three known roles

All core methods use the same frozen E1 executable and DLL and fresh Seed1 runs. Each MB-type arm independently pays the unchanged full H pipeline; its observed completion is reported below. P and PT remain cold compact runs without H. K1 is SC-C15-S (600 seconds), K2 SC-B20-S (1200), and K3 PB-B35-B (1200). E1 pays its own P and MB comparators; the same-named E0 observations are not reused. MR deletes only support cover/conditional handling and ordered compatible-supply rows C_R. MG deletes only explicit H-spread, variable-S/fixed centering, objective estimators and the dedicated W_SP block C_G. Existing derived inventory domains, exact Gini/state products, cap/floor, penalty-LB closure and required movement remain. MS2 deletes only three-station support, retaining pairs and ordered compatibility. Native Gurobi Cuts retain their original settings in all MB-type arms. These are deletion diagnostics around the same H and representation, not alternative proposed algorithms.

The required MD specification did not pass mathematical qualification. The retained numerical closure can emit an impossible row when \(\gamma_L+\lambda P_{LB}\ge U_0-10^{-9}\). As already explained in Appendix A.5.6/A.7, that closure establishes no strict improver under the declared numerical policy; it need not retain an equal-U0 physical solution or its Start. A legal V2, zero-stock, T=60, handling-unit=120 boundary has forced Y=0, P_LB=2 and U0=0.3. Its equal-U0 empty fleet violates only the impossible row. Thus the requested inclusive root embedding and retained own-U0 Start cannot both be guaranteed while preserving that closure. Three MD arms were blocked before formal evaluation. This is a specification incompatibility, not evidence that interval control is beneficial or harmful, and does not by itself revoke the existing no-strict-improver proof policy. No replacement experiment was added.

K3 is a fresh 1200-second evaluation on a known role. It does not continue the historical 2400-second run or reuse that run as a comparator or presumed prefix.

**Table R127-C. All predeclared core comparisons.** Left is the evaluated method; ratios use the both-certified intersection only. PT aliases, when applicable, are marked and not counted independently.

| Role | Left / right | Status | Direction | Left cert s | Right cert s | Right / left |
| --- | --- | --- | --- | --- | --- | --- |
| SC-C15-S | MB/P | Both certified | Win | 35.558 | 473.821 | 13.325 |
| SC-C15-S | MB/PT | Left only certified | Win | 35.558 | open | N/A |
| SC-C15-S | MB/MD | Unevaluable | Unevaluable | 35.558 | not run | N/A |
| SC-C15-S | MB/MR | Both certified | Lose | 35.558 | 35.251 | 0.991 |
| SC-C15-S | MB/MG | Both certified | Win | 35.558 | 40.673 | 1.144 |
| SC-C15-S | MB/MS2 | Both certified | Lose | 35.558 | 35.242 | 0.991 |
| SC-C15-S | PT/P | Right only certified | Lose | open | 473.821 | N/A |
| SC-B20-S | MB/P | Left only certified | Win | 966.283 | open | N/A |
| SC-B20-S | MB/PT | Left only certified | Win | 966.283 | open | N/A |
| SC-B20-S | MB/MD | Unevaluable | Unevaluable | 966.283 | not run | N/A |
| SC-B20-S | MB/MR | Both certified | Lose | 966.283 | 743.130 | 0.769 |
| SC-B20-S | MB/MG | Left only certified | Win | 966.283 | open | N/A |
| SC-B20-S | MB/MS2 | Both certified | Lose | 966.283 | 679.866 | 0.704 |
| SC-B20-S | PT/P | Both open | Undetermined | open | open | N/A |
| PB-B35-B | MB/P | Both open | Undetermined | open | open | N/A |
| PB-B35-B | MB/PT | Both open | Undetermined | open | open | N/A |
| PB-B35-B | MB/MD | Unevaluable | Unevaluable | open | not run | N/A |
| PB-B35-B | MB/MR | Both open | Undetermined | open | open | N/A |
| PB-B35-B | MB/MG | Both open | Undetermined | open | open | N/A |
| PB-B35-B | MB/MS2 | Both open | Undetermined | open | open | N/A |
| PB-B35-B | PT/P | Both open | Undetermined | open | open | N/A |

**Table R127-M. Original root exposure and cost.** Native seconds are diagnostics within the complete production clock. Unknown means unavailable from the original run; no extra Optimize was used.

| Role / mode | H complete | Root rows / cols | Root LP L | LP native s | MIP native s | Splits / target hits |
| --- | --- | --- | --- | --- | --- | --- |
| SC-C15-S/P | N/A | 2199/976 | unknown | 0.000 | 472.444 | 0/0 |
| SC-C15-S/MR | True | 3904/2083 | 0.18563301 | 0.181 | 33.584 | 0/1 |
| SC-C15-S/MB | True | 5054/2083 | 0.18563301 | 0.205 | 33.683 | 0/1 |
| SC-C15-S/PT | N/A | 2199/976 | unknown | 0.000 | 569.926 | 0/0 |
| SC-C15-S/MG | True | 4523/2080 | 0.18563301 | 0.245 | 38.908 | 0/1 |
| SC-C15-S/MS2 | True | 4144/2083 | 0.18563301 | 0.169 | 33.498 | 0/1 |
| SC-B20-S/MG | True | 7967/3099 | 0.11721380 | 0.366 | 1167.708 | 0/0 |
| SC-B20-S/PT | N/A | 3629/1551 | unknown | 0.000 | 1169.890 | 0/0 |
| SC-B20-S/MS2 | True | 6643/3102 | 0.11721380 | 0.368 | 676.869 | 0/0 |
| SC-B20-S/MB | True | 8923/3102 | 0.11721380 | 0.401 | 962.891 | 0/0 |
| SC-B20-S/MR | True | 6223/3102 | 0.11721380 | 0.444 | 740.106 | 0/0 |
| SC-B20-S/P | N/A | 3629/1551 | unknown | 0.000 | 1169.891 | 0/0 |
| PB-B35-B/MS2 | True | 23500/9893 | 0.00000000 | 0.962 | 1163.970 | 0/0 |
| PB-B35-B/P | N/A | 13955/5434 | unknown | 0.000 | 1169.650 | 0/0 |
| PB-B35-B/MG | True | 40154/9890 | 0.00000000 | 1.802 | 1163.219 | 0/0 |
| PB-B35-B/PT | N/A | 13955/5434 | unknown | 0.000 | 1169.614 | 0/0 |
| PB-B35-B/MR | True | 21610/9893 | 0.00000000 | 1.273 | 1164.145 | 0/0 |
| PB-B35-B/MB | True | 43135/9893 | 0.00000000 | 1.718 | 1161.300 | 0/0 |

Actual family counts, nonzeros, H/fleet identities, native calls/nodes and first logged own-witness availability are in mechanism_costs.csv. Saved original root-LP points are tested against actual deleted rows without a new solve. For MG, W is eliminated using its serialized bounds and every W-containing inequality; an empty interval identifies only non-extendibility of that saved point. A nonempty interval or equal LP objective does not establish global redundancy. These root diagnostics do not establish certification-time causality. Full H/scope matching and actual row/column differences are recorded per role. Pair/triple totals 1120,2660,21420 are below the shared 50000 cap, so MS2 does not redistribute a binding truncation budget.

**Table R127-D. Component interpretation after checking actual exposure.** Eligible roles require complete identical H actions/fleet, matched root scope and actual removal of the declared rows. Timing directions in unexposed roles cannot establish a component effect.

| Comparison | Eligible known roles | Eligible directions | Disposition |
| --- | --- | --- | --- |
| MB/MD | none | none | Blocked before formal |
| MB/MR | SC-C15-S, SC-B20-S, PB-B35-B | 2 observed losses, 1 undetermined comparison | Reverse certification observations |
| MB/MG | SC-C15-S, SC-B20-S, PB-B35-B | 2 observed wins, 1 undetermined comparison | Direct certification increment in this panel |
| MB/MS2 | SC-C15-S, SC-B20-S, PB-B35-B | 2 observed losses, 1 undetermined comparison | Reverse certification observations |

All three observed roles have complete identical H actions/fleet, matched root scope and the prescribed actual row deletions. C_R and the three-station package show reverse certification-time observations: on K1 the deleted variants are faster by 0.307 and 0.316 seconds; on K2 MR certifies at 743.130 seconds and MS2 at 679.866, versus MB at 966.283. These losses remain losses under the symmetric rule. C_G has direct certification support within this panel: MB is faster than MG on K1 (35.558 versus 40.673 seconds), and only MB certifies on K2. All six executed K3 methods remain valid open, so that role supplies no certification-time direction. The mixed component evidence does not establish that every row package is necessary.


**Table R127-E. Checks at the saved original root-LP points.** Delta L is deleted-model minus full-model root LP bound. Missing points remain unknown. The W result fixes every surviving original variable and checks the actual serialized W block.

| Role / mode | Matched H / scope | Delta L | Deleted rows | Ordinary-point check | W extension |
| --- | --- | --- | --- | --- | --- |
| SC-C15-S/MR | True | -1.110e-16 | 1150 | No violation at saved point | Not applicable / unavailable |
| SC-C15-S/MG | True | -1.110e-16 | 531 | No violation at saved point | Extension interval nonempty at saved point |
| SC-C15-S/MS2 | True | -2.776e-17 | 910 | No violation at saved point | Not applicable / unavailable |
| SC-B20-S/MR | True | 1.388e-17 | 2700 | No violation at saved point | Not applicable / unavailable |
| SC-B20-S/MG | True | 2.776e-17 | 956 | No violation at saved point | Extension interval nonempty at saved point |
| SC-B20-S/MS2 | True | 8.327e-17 | 2280 | No violation at saved point | Not applicable / unavailable |
| PB-B35-B/MR | True | 0.000e+00 | 21525 | No violation at saved point | Not applicable / unavailable |
| PB-B35-B/MG | True | 0.000e+00 | 2981 | No violation at saved point | Extension interval nonempty at saved point |
| PB-B35-B/MS2 | True | 0.000e+00 | 19635 | No violation at saved point | Not applicable / unavailable |

At these nine saved points, the deleted ordinary rows have no detected violation, all three MG W-extension intervals are nonempty, and the root LP values agree within the recorded numerical tolerance. These observations explain no additional exclusion at the retained root optima; they do not show global redundancy or explain away the opposing certification-time results.

### 6.7 A bounded, separately trained compact baseline

The six fixed configurations vary only MIPFocus (0/1/2/3) and native Cuts (-1/2). S12, PB-B20-S and R98-C2 each use Seeds 2 and 3, totaling 36 E1 cold-P runs in a precommitted cyclic order. None is a core, main or tiny evaluation input. Actual model environments read back the settings after presets, with zero Starts. Selection maximizes qualified certifications N, then the minimum per-Seed count, then the declared censored penalty score and tie-breakers. A nondefault requires no loss in N or its per-Seed minimum, and either more certifications or at least a 10% score improvement when N ties above zero. The score's open-run value 1 is an artificial training penalty; it is never a certification time or speedup. Complete training clocks use the uniformly recorded parent admission marker; original sealed receipts and the initial import-prefix correction are preserved separately.

**Table R127-Q. All six predeclared configurations.** Each denominator is six training positions; the two per-Seed counts each have denominator three.

| Config | Focus / Cuts | N Seed2 / Seed3 | N / N_min | Score |
| --- | --- | --- | --- | --- |
| q0 | 0/-1 | 2 / 1 | 3/1 | 0.742 |
| q1 | 1/-1 | 1 / 1 | 2/1 | 0.894 |
| q2 | 2/-1 | 2 / 2 | 4/2 | 0.657 |
| q3 | 3/-1 | 0 / 0 | 0/0 | 1.000 |
| q4 | 2/2 | 2 / 2 | 4/2 | 0.658 |
| q5 | 3/2 | 0 / 0 | 0/0 | 1.000 |

The committed selection is q2 (MIPFocus=2, Cuts=-1). This one parameter file is used unchanged in all three held-out known roles, including adverse outcomes. This is parameter holdout confirmation on known instances, not an independently sampled benchmark or an optimally tuned general solver. The main comparison MB/P changes the whole integrated method and cannot identify one component. Shared MB arms across seven core comparisons are not independent replications.

PT/P gives RIGHT_ONLY_CERTIFIED: 1, BOTH_OPEN: 2 among 3 nonalias typed entries: 1 observed loss, 2 undetermined comparisons, plus 0 aliases. The conditional right/left geometric mean is N/A over 0 both-certified roles. The per-role outcomes, including any reverse direction or valid open endpoint, remain in Table R127-C.

MB/PT gives LEFT_ONLY_CERTIFIED: 2, BOTH_OPEN: 1 among 3 nonalias typed entries: 2 observed wins, 1 undetermined comparison, plus 0 aliases. The conditional right/left geometric mean is N/A over 0 both-certified roles. The per-role outcomes, including any reverse direction or valid open endpoint, remain in Table R127-C.

Although q2 has four training certifications against q0's three, it does not strengthen the baseline on the three held-out roles: PT has no certification, while default P certifies K1; both remain open on K2/K3. MB certifies K1/K2 against valid-open PT and both are open on K3. This supports MB's bounded competitiveness against the unchanged selected file, with no both-certified MB/PT ratio and no claim about optimal Gurobi tuning.

### 6.8 Inclusive-root control and a bounded support Seed check (Round128)

Round128 follows the separately preserved PARTIAL Round127 study. It evaluates MD-R (inclusive-root control v1), a newly corrected research control, rather than relabelling the three unstarted historical MD positions. At the Round128 stage, frozen full M-B / GI-TBC was the sole proposed method; P-GRB remains the primary benchmark. One separately sealed E2 build supplies all 16 formal arms: twelve Seed0 arms on the same three known research roles, followed by only MB/MS2 on K1 and K2 at Seed1. These yield 15 core typed comparisons and two additional support comparisons, not 17 independent trials or five distinct problems. Each Seed has one matched observation per role. E1 Seed1 times are historical context, never same-build comparators.

The old named penalty-closure shortcut can write \(0\le-1\) at an equal-cutoff lower bound. A legal empty-stock two-station fleet at \(T=60\) has \(F=U_0=.3\) and violates that shortcut. On an actual interval \(I=[a,b]\), suppose the cutoff domain supports \(F(x)\ge L_a:=a+\lambda\underline P\). The complement has \(F(x)>c\), so coverage of the two domains gives the regional bound

\[
B_I=\min\{L_a,c\}.
\]

This minimum follows from coverage; it is not numerical clipping. If \(L_a>c\), the inclusive cutoff domain is empty, subject to investigating any contradicting known witness first. At \(L_a=c\), strict improvement is excluded but an equal-\(c\) physical solution may remain. When \(c-10^{-9}\le L_a<c\), the directly supported bound remains \(L_a\); it is not exact \(c\) and does not rule out every arbitrarily small improvement. The shortcut is therefore an encoding of proof/control closure rather than an ordinary valid inequality for every non-strict cutoff solution. This finite counterexample does not itself revoke every frozen M-B numerical result. In the three saved R127 core MB call histories, none of the nine actual matrices contains the shortcut.

MD-R suppresses only that semantically marked pseudo-infeasibility row, in both shared and fallback emission paths. It retains the physical model, all valid domains and strengthening, \(P\ge\underline P\), the same complete independently paid H, and fixed own-\(U_0\) root \(I_0=[0,\min\{U_0,(n-1)/n\}]\) with \(F_{model}\le U_0\) and the original \(n=1\) convention. Before LP, its own entire physical fleet is mapped and checked against actual columns, original types, bounds, every row and objective. It then pays one complete root LP, restores integer VTypes and submits the complete legal own Start to one complete root MIP. It has no child LP, target handoff, split or root rebuild. The original startup-zero policy is retained. A numerical relevance threshold cannot waive the nonzero two-call obligation; TIME_LIMIT/INTERRUPTED cannot become native optimality. Raw signed-gap and full physical/source/return/coverage checks remain, without a new analytic certificate or rational error claim. Finite native boundary, nonempty-fleet, open-return and full E1/E2 model/H/parameter bridges precede the E2 seal.

**Table R128.1. All core Seed0 certification times (seconds).** Open entries have null T_cert in the authority, not the cap or a native Runtime substituted as certification time.

| Known role, Seed0 | P T_cert | MB T_cert | MD-R T_cert | MS2 T_cert | MB splits |
| --- | --- | --- | --- | --- | --- |
| SC-C15-S | 464.967 | 41.554 | 40.670 | 33.427 | 0 |
| SC-B20-S | open | 1066.781 | 1067.337 | 991.422 | 0 |
| PB-B35-B | open | open | open | open | 0 |

Every formal arm independently pays its entire method. T_produce includes admission, H where applicable, modeling, LP/MIP, Start checks and required output; T_verify and T_total remain separate. Only final qualified certificates receive T_cert=T_produce. Actual same-H action/fleet, initial U0, root scope and complete matrix differences are retained in the current evidence. All prescribed component comparisons pass that finite eligibility check. The per-arm call counts distinguish actual splits, child probes, target calls and terminal calls. An observed absence of splits restricts the outer-control interpretation to the exposed probing, target handoff and scheduling work; it cannot demonstrate multi-leaf decomposition speedup.

**Table R128.2. The complete same-E2 two-Seed support observations (seconds).** A positive MS2 saving means MB takes longer. Directions use unrounded complete certification time and certification priority.

| Known role | Seed | MB T_cert | MS2 T_cert | MS2 saving (s) | MB/MS2 direction |
| --- | --- | --- | --- | --- | --- |
| SC-C15-S | 0 | 41.554 | 33.427 | 8.127 | Lose |
| SC-C15-S | 1 | 35.497 | 35.737 | -0.241 | Win |
| SC-B20-S | 0 | 1066.781 | 991.422 | 75.359 | Lose |
| SC-B20-S | 1 | 965.849 | 680.009 | 285.841 | Lose |

MS2 deletes only three-station support cover/conditional-handling rows. Pair rows, ordered supply, enumeration order and the shared 50000 cap remain; the three roles' 1120, 2660 and 21420 candidates do not bind that cap. K3's endpoint and certification risks remain visible in Table R128.1 and the complete endpoint authority. Deleting rows need not improve MIP work monotonically, and the same native Seed does not force identical search paths. Fixed modeling/Start cost and actual MIP work are reported separately rather than attributing every elapsed-time difference to strengthening. Two Seed observations on known roles do not establish general statistical stability.

All three Seed0 MB arms actually pay one root LP, two child LPs and one terminal MIP; only K1 adds one child-bound-target MIP. No NEXT call or split occurs. Each MD-R pays exactly its root LP and root MIP. At K2 Seed0, MB/MS2 native MIP seconds are 1063.046/988.337, work is 2204.035/1952.267, and nodes are 65227/70275. Model generation plus native read costs are 1.100/0.807 seconds; Start checks/submission cost 0.0057/0.0055 seconds. At K2 Seed1, MB/MS2 native MIP seconds are 962.110/676.970, work is 1974.645/1320.987, and nodes are 55838/51800. Model generation plus native read costs are 1.106/0.809 seconds; Start checks/submission cost 0.0065/0.0056 seconds. Thus the K2 difference mainly accompanies changed MIP work rather than fixed row-writing cost; even the node-count direction differs between Seeds. The observed MB/MS2 root LP bounds agree within 1e-12 on every role/Seed. This finite root observation does not prove global redundancy of the deleted rows. Native Runtime is nested solver work, not certification time. Missing compact modeling subclocks remain explicitly unavailable rather than inferred from the clock remainder.

The complete core comparisons are:

| Comparison, core Seed0 | Typed statuses | Directions |
| --- | --- | --- |
| MB/P | both certified: 1; left only certified: 1; both open: 1 | Win: 2; UNDETERMINED: 1 |
| MB/MD-R | both certified: 2; both open: 1 | Lose: 1; Win: 1; UNDETERMINED: 1 |
| MB/MS2 | both certified: 2; both open: 1 | Lose: 2; UNDETERMINED: 1 |
| MD-R/P | both certified: 1; left only certified: 1; both open: 1 | Win: 2; UNDETERMINED: 1 |
| MS2/P | both certified: 1; left only certified: 1; both open: 1 | Win: 2; UNDETERMINED: 1 |

The default compact benchmark is newly paid in E2 at Seed0. No old E1 P time is borrowed for the additional support observations. The earlier six-configuration training choice q2 and its adverse held-out PT result remain in Section 6.7: PT certifies 0/3 versus default P's 1/3 in that separate E1 study. Round128 adds no tuning, tiny rerun, evaluation input or longer window, and does not establish superiority over the strongest possible tuned compact baseline. Artificial boundary fixtures are separately identified qualification work.

The bounded stage decision is `BOUNDED_SIMPLIFICATION_SIGNAL`. Certification risk remains unresolved on K3: all four core methods are qualified open there, so neither a certification loss nor uniform simplification safety is established. K1 is mixed across Seeds: MS2 saves 8.127 seconds at Seed0 but is 0.241 seconds slower at Seed1. Against that retained mixed evidence, K2 supplies the bounded repeated signal: both methods certify at each Seed, and MS2 saves 75.359 seconds at Seed0 (7.1%) and 285.841 seconds at Seed1 (29.6%). Those are two matched observations on one known role, not population evidence. MD-R establishes a legal control, not a performance victory: it is 0.883 seconds faster than MB on K1, 0.556 seconds slower on K2, and both are open on K3; no MB split occurs. That stage retains two MB/P Wins and one BOTH_OPEN comparison, with no claimed advantage over the strongest possible tuned compact baseline. At that stage, the K2 support signal warranted one future uniform confirmation design and full M-B remained the paper method. Section 6.9 records that completed R129 selection; Section 6.10 adopts S2 and gives the distinct current attribution study.

The historical Round128 next-priority recommendation, subsequently executed in Section 6.9, was substantive review of one then-unexecuted uniform simplification confirmation design: fix a single candidate that removes triple support for every evaluated case while retaining the frozen H, representation, pair support, ordered supply, C_G, controller, numerical policy and default parameters. Any later authorization should freeze its matched certification-first panel before execution, retain every open or adverse result, independently pay complete methods, and forbid role-specific switching or retuning. No such confirmation, adoption, additional Seed/input or longer window is executed in Round128. Until that decision, retain frozen M-B / GI-TBC, P-GRB as the primary benchmark and the historical ENS-C default; restrict the D claim to the actual probing/target/scheduling exposure and do not claim multi-leaf speedup.

### 6.9 Prospective confirmation of a uniform pair-support candidate (Round129)

This section preserves the R129 selection-time record: the four inputs were new at that stage, MS2 was a candidate, and the five conditions passed. Section 6.10 adopts that version and treats the reused roles as known attribution diagnostics. The E2 numbers, raw-field meanings and original selection criteria below retain their historical identities.

Round128 supplied a bounded development signal on known K2/SC-B20-S, while retaining the K1 timing reversal and open K3. Round129 is a separately preregistered finite confirmation of a single already implemented candidate. MS2 omits three-station support on every input and retains the full frozen H, R, pair support, ordered supply, C_G, controller and numerical policy. No MD-R variant is run and no MD-R pseudo-row suppression is applied to MB/MS2. P remains the original independently paid cold compact Gurobi baseline. All thirty arms use the original same E2 PE and Gurobi 13.0.2 DLL; the only varied native parameter is the prespecified Seed0/1.

The method remains a tailored branch-and-cut framework with Gini-interval decomposition. Its project strengthening is generated statically for each actual scoped model; Gurobi performs the native branching, presolve and native cut generation. The framework name or abbreviation supplies no separate novelty claim.

The four new problems are UC-C15-S (CITI, compact/r1, shortage, V15/M2, Q=[30,30], T=3600, cap600), UC-B20-B (CABI, regional/r2, balanced, V20/M2, Q=[20,40], T=7200, cap1200), UC-C20-U (CITI, regional/r1, surplus, V20/M2, Q=[30,30], T=7200, cap1200), and UC-B30-S (CABI, compact/r2, shortage, V30/M3, Q=[25,25,25], T=7200, cap1200). The known PB-C20-B protection input (V20/M2, Q=[30,30], T=3600, cap900) is reported separately and cannot supply a prospective gain. These are draws from two existing source tables, not new cities, IID samples or a full factorial design. Seeds add observations of the same problems.

The recipe, dependencies, all ten method orders, caps and five candidate rules were committed before once-only offline generation. Original R126/R122/R109/R57 anchor, tie, target, inventory, weight, depot and travel-time rules are retained. No H/LP/MIP or difficulty/reachability filter selected the data. All lawful station overlap is retained. Shortage arithmetic supplies positive necessary objective floors of 12/275 and 464877/2500000 for UC-C15-S and UC-B30-S respectively, excluding the depot; these decimal-data checks are not injected into any model, Start or reported native lower bound. Balanced/surplus outcomes remain regardless of zero objectives or backend exposure.

Each method independently pays its complete H/admission/model/native/online-output workflow under the original complete deadline, shutdown reserve and numerical settings. No solution, U, Start, basis, tree or cache is shared. The opposite Seed reverses each role's method order. Thirty arms form ten matched groups and thirty typed shared-data comparisons (MS2/P, MS2/MB, MB/P), not thirty independent trials. The new layer contains 24 arms/eight groups/24 comparisons; protection contains six/two/six.

**Table R129.1. Every fixed complete-method observation (seconds).** C denotes a qualified certificate and its complete T_cert=T_produce. O denotes a qualified open result and observed T_produce in parentheses, with T_cert=null. U would identify unqualified evidence. The last two rows are the known protection role.

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

**Table R129.2. New-input certification counts, keeping Seeds separate (denominator four per Seed).**

| Seed | P certified | MB certified | MS2 certified |
| --- | --- | --- | --- |
| 0 | 1 | 2 | 2 |
| 1 | 1 | 2 | 2 |

The numbers of new problems certified at both Seeds are P: 1, MB: 2, MS2: 2. At Seed0 the P-certified/method-open counts are MB: 0, MS2: 0; at Seed1 they are MB: 0, MS2: 0. Full per-observation U, qualified L, raw signed gap, all three clocks and every reverse comparison remain in the accompanying arms/pairs authorities and Supplement S. Open endpoints are not certification Wins, and open times are not replaced by caps.

**Table R129.3. All matched MS2/MB directions, including the separate protection role.** Savings are T_MB-T_MS2 only when both certify; N/A carries no unobserved speed ratio.

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

Component attribution is conditional on actual complete H/actions/fleet, initial U and root scope, native settings, and duplicate-preserving full matrix/column/type/bound/objective equality after the triple deletion. Every actual root is checked after its own H. Subsequent legitimate own-UB trajectories can differ. Missing roots, incomplete H or unmatched scopes restrict the observation to a complete-method comparison. The all-candidate counts (1120, 2660, 2660, 13485 and 2660) are below the original shared cap50000, so this panel does not reassign a binding enumeration budget. Actual cover/conditional counts and split/target, LP/MIP work/nodes, model/Start and witness-availability diagnostics are retained in the mechanism evidence. An absent split neither invalidates completeness nor demonstrates multi-leaf speedup. No new D control effect was measured in R129; the final pair-only outer-control comparison is reported separately in Section 6.10.

All ten matched MB/MS2 observations have the same complete H actions and fleets, initial U, root scope and settings. After triple deletion, the remaining rows and all columns, types, bounds and objective match exactly. The actual triple cover/conditional counts removed at each Seed are 0/910 (UC-C15-S), 2204/76 (UC-B20-B), 0/2280 (UC-C20-U), 3969/8211 (UC-B30-S), and 0/2280 (PB-C20-B). UC-B20-B naturally has three splits in each MB and MS2 arm at both Seeds; every other MB/MS2 arm has zero splits. This new exposure coexists with the historical R128 no-split observations. Without its own D control, R129 did not identify a net decomposition speed benefit; the distinct final-version control is in Section 6.10. At UC-C20-U Seed0, MB and MS2 respectively use 698.099 and 551.181 native MIP seconds, 1412.023 and 1058.789 work units, and 49499 and 54557 nodes. Model-generation plus native-read seconds are 1.145 and 0.850. At UC-C20-U Seed1, MB and MS2 respectively use 629.024 and 478.057 native MIP seconds, 1272.487 and 911.262 work units, and 41225 and 45006 nodes. Model-generation plus native-read seconds are 1.150 and 0.849. The C20 saving accompanies lower MIP time/work despite more MS2 nodes at both Seeds; fixed row-writing/read savings are about 0.3 seconds. All observed matched root LP bounds agree within 1e-12. This finite agreement does not prove global redundancy of triple rows. Native costs remain nested explanatory measurements rather than T_cert.

UC-C15-S and UC-B30-S remain open for all three methods at both Seeds. UC-B30-S has an open-endpoint reversal: MS2 and MB U are respectively 0.381251 and 0.429057 at Seed0 but 0.429057 and 0.365930 at Seed1. UC-C15-S Seed1 also has slightly worse MS2 U than MB. Both-open comparisons remain UNDETERMINED with no certification ratio or Win. The three tiny negative signed gaps and all fifteen Seed1 raw top-level LB=0/certificate=false records are preserved. Qualified final endpoints use the original source/return/coverage and numerical policy; no raw field, LB or gap is clipped or rewritten.

In the new layer, MS2/P and MB/P each have two both-certified observations, two method-only certificates and four both-open observations. Their certification-time ratio geometric means (right/left) are 87.827903 and 81.425709 respectively, solely on UC-B20-B at the two Seeds. MS2/MB has four both-certified observations (UC-B20-B and UC-C20-U at both Seeds) and four both-open observations; its right/left geometric mean is 1.179515 on those four observations only. In protection, MS2/P and MB/P are method-only certified at both Seeds and have no ratio; MS2/MB is both-certified at both Seeds with a 1.224121 right/left geometric mean. These intersections do not represent the full panel.

For a fixed valid scope with identical domains and objective, deleting valid triple rows preserves the physical integer optimum and can only weaken or preserve the mathematical optimal LP lower bound. No theorem makes deletion faster. Native Runtime, work, nodes, root LP time, fewer rows or a smaller open gap do not replace complete certification time. Ratios and their geometric means are restricted to explicitly labelled both-certified intersections.

The fixed research decision magnitude requires a certified MS2 saving of at least max(10 seconds,10% of MB time), or MS2-only certification. A material time cost uses the symmetric faster-method reference; these labels do not alter strict unrounded Win/Lose or claim statistical significance. Advancement also requires no additional per-Seed certification loss or P-only risk, protection of every current MB certificate, no two-Seed large protection slowdown, one newly exposed role supporting MS2/MB materially at both Seeds, and one new role giving direct MS2/P certification Wins at both Seeds. Development K2, protection, subsecond directions and open gaps cannot substitute for the new signal.

| Fixed condition | Requirement | Satisfied |
| --- | --- | --- |
| 1 | Retain per-Seed and both-Seed new-problem certification counts relative to MB | True |
| 2 | Add no per-Seed P-certified/method-open risk relative to MB | True |
| 3 | Retain every protected MB certificate and avoid a large slowdown at both Seeds | True |
| 4 | One new input has eligible triple deletion and material MS2/MB support at both Seeds | True |
| 5 | One new input gives direct MS2/P certification Wins at both Seeds | True |

The finite scientific recommendation is `RECOMMEND_UNIFORM_MS2_AS_PAPER_CANDIDATE`. The five fixed conditions support recommending uniform MS2 as the single method candidate for the next paper revision. This was the recommendation at the R129 stage. R130 now adopts uniform MS2 as the sole method; historical full-M-B numbers retain their original labels. The exact mode mapping is original E2 `--round127-mode mb` to original E2 `--round127-mode ms2`; only three-station cover/conditional support is omitted uniformly. No old MB number is relabelled MS2. R130 resolves this version map by labelling earlier full-M-B tables as predecessor evidence and restricting current main-method performance to qualified actual MS2 observations. It does not relabel old results or rerun the larger historical panels. The exact evidence layers and input/Seed/program/clock identities are listed in paper_version_manifest.json and evidence_migration.csv. This small prospective panel does not establish V50/V60 safety. The frozen paper method, P benchmark, historical ENS-C default, R127 PT negative findings and all R128 reverse/open/no-split facts remain identifiable. No extra confirmation is automatically appended.

### 6.10 Fixed-version same-start and outer-control attribution (Round130)

Round129's five conditions passed before this study. The user now adopts **GI-TBC (uniform pair-support implementation, MS2)** as the sole proposed method, short ID **S2**. Its algorithm identity is the original E2 `--round127-mode ms2`: pair support is enabled uniformly and triple support is never emitted. H, representation, ordered supply, C_G, A/B, Gini control, numerical tolerances and default native parameters are unchanged. Historical full M-B measurements retain their three-station identity; ENS-C remains the repository default and is not the paper reproduction entry. This is a version adoption, not a third algorithm or another candidate-selection round.

The fixed panel contains UC-B20-B, UC-C20-U and UC-B30-S from R129, with their original input bytes, Q vectors and physical T=7200 seconds. These are deliberately known attribution roles: a previously splitting nonzero-certified role, a further nonzero-certified risk role, and an open shortage role. They are not unseen prospective validation inputs, independent replications of R129 or a difficulty-blind sample. Balanced, surplus and shortage refer to total inventory scenarios, not identical local station regimes. No input, Seed, parameter, tuning file or cap was added after outcomes.

Each method independently pays its complete workflow under the same 1200-second cap, original 30-second shutdown reserve, six-second native offset and two-second hard-stop offset. Threads=MIPThreads=1, affinity mask4, H_seed=20260626, per-group Gurobi Seed0/1, PresolveAuto, MIPFocus=0, Cuts=-1 and requested zero relative/absolute MIP gaps are retained. Each native call receives only the remaining complete deadline. Three problems, two Seeds and four methods give 24 serial arms in six matched groups. The five prespecified comparisons in each group yield 30 typed shared-data entries, not 30 independent trials. No arm uses another arm's fleet, upper bound, Start, basis, tree or cache.

For each role, the Seed1 method order reverses Seed0. This limited counterbalancing does not remove all host-load noise or turn two paths into a statistical robustness study.

PS uses the existing independently paid H-to-original-compact entry, not P-tuned. Its complete Start mapper checks every actual column/type/bound/row and the original objective, submits and reads back the full vector, and leaves the mathematical model unchanged. P stays cold. A Start that does not create a new native incumbent is not automatically invalid: native heuristics can already have an equally good or better solution. Actual submission/readback and native adoption are reported separately. H and mapping costs are included in PS production time.

The inherited verified-zero startup scope is retained for PS/S2/S2R. Such a qualified startup-zero outcome has no backend exposure and is not same-H backend attribution; no new zero shortcut is introduced. The normal nonzero PS path has one original-compact MIP. Every formal role here has nonzero own H.

S2R uses the off-by-default unique `s2-root` mode, retaining pair support and all valid root strengthening. Its own H defines the inclusive root

\[
 I_0=[0,\min\{U_0,(n-1)/n\}],\qquad F_{\rm model}\le U_0.
\]

It suppresses only the semantically identified interval-no-improver proof-closure row, validates its own full Start against actual original integer types before LP relaxation, pays one complete root LP, restores the integer types, and pays one root MIP with one submitted own Start. No child LP, NEXT/AM target, split, epoch or restart follows. Nonzero chains cannot skip a call merely through a relevance tolerance. Native TIME_LIMIT/INTERRUPTED remains open; a near-equal numerical bound does not replace the required complete native optimal-root return. An infeasible root despite its legal own witness is a consistency issue, not a shortcut certificate. All costs share the deadline.

For a physical solution, nonnegative penalties give G<=F and nonnegative ratios give G<=(n-1)/n. Thus every physical F<=U0 solution lies in the root; the cutoff complement cannot improve the own verified U0. A qualified root bound L combines with that complement as min(L,U0) by domain coverage. This identity does not excuse a bound contradicting its own legal witness. Equality of an analytic regional floor and cutoff excludes strict improvement only; a floor slightly below the cutoff retains its own value under the original numerical policy. The ordinary S2 proof shortcut is unchanged.

**Table R130.1. Every complete-method observation (seconds).** C is qualified T_cert=T_produce; O gives observed T_produce with T_cert=null. Open times are never replaced by caps.

| Known role / Seed | P | PS | S2 | S2R |
| --- | --- | --- | --- | --- |
| UC-B20-B / 0 | C 318.453 | C 237.274 | C 3.559 | C 1.398 |
| UC-B20-B / 1 | C 316.817 | C 127.117 | C 3.504 | C 1.586 |
| UC-C20-U / 0 | O (1170.579) | O (1170.713) | C 554.709 | C 556.836 |
| UC-C20-U / 1 | O (1170.511) | O (1170.560) | C 481.820 | C 480.939 |
| UC-B30-S / 0 | O (1171.180) | O (1170.428) | O (1170.759) | O (1170.433) |
| UC-B30-S / 1 | O (1170.437) | O (1170.680) | O (1170.448) | O (1170.396) |

**Table R130.2. All primary, same-start and outer-control directions.** Win/Lose uses unrounded certificate time or a one-sided qualified certificate. Both open is UNDETERMINED. The remaining two fixed comparison types and all exact differences are retained in Supplement S and pairs.csv.

| Known role / Seed | S2/P | S2/PS | S2/S2R |
| --- | --- | --- | --- |
| UC-B20-B / 0 | Win | Win | Lose |
| UC-B20-B / 1 | Win | Win | Lose |
| UC-C20-U / 0 | Win | Win | Win |
| UC-C20-U / 1 | Win | Win | Lose |
| UC-B30-S / 0 | UNDETERMINED | UNDETERMINED | UNDETERMINED |
| UC-B30-S / 1 | UNDETERMINED | UNDETERMINED | UNDETERMINED |

Actual complete-H/action/capacity-assigned fleet equality across all same-H comparisons is True. Actual effective-root identity for S2/S2R is True. The matrix checks retain duplicate rows and compare complete objectives, column order/types/bounds, settings and all remaining rows. If a normal S2 root contains the omitted semantic shortcut or its H/scope differs, that result is retained as a complete-method comparison with restricted attribution. Complete per-role facts are in actual_method_differences.json and same_H.csv.

At B20 Seed0, S2/PS/S2R complete certification costs are 3.559/237.274/1.398 seconds; S2 produces 3 natural splits and S2R none. At B20 Seed1, S2/PS/S2R complete certification costs are 3.504/127.117/1.586 seconds; S2 produces 3 natural splits and S2R none. The H witness already attains the eventual B20 objective, 0.5773330699702928, before proof. It is not itself an optimality certificate. The original R129 coverage example is kept separately and is never injected into a formal run. The new actual observations therefore separate a large backend/representation increment from any net contribution of the outer package; split counts alone cannot establish speedup.

UC-B20-B (same H backend): REPEATED_DIRECT_INCREMENT. UC-C20-U (same H backend): REPEATED_DIRECT_INCREMENT. UC-B30-S (same H backend): UNDETERMINED. UC-B20-B (outer control): CLOSE_AT_BOTH_SEEDS. UC-C20-U (outer control): CLOSE_AT_BOTH_SEEDS. UC-B30-S (outer control): UNDETERMINED.

The symmetric descriptive materiality rule is slower-faster >= max(10 seconds,0.10*faster), separate from strict Win/Lose and from one-sided certificates. It is not a statistical test or algorithm switch. Native LP/MIP seconds, Work, nodes, model/Start costs, target/split exposure, closure sources and first retained own final-U witnesses are explanatory measurements. Missing subclocks remain unknown; Work is not used as a stopping budget. Ratios and geometric means use only explicit both-certified intersections.

Both C20 Seed1 S2 and S2R retain the qualified signed gap U-L=-1.4988010832439613e-15, with L unchanged under the original signed 1e-7 numerical window. Original raw top-level claims remain distinct from qualified source/return/coverage endpoints. No bound clipping, new tolerance or rational-exactness claim is introduced. Cross-arm physical witnesses are checked only for contradictions and never transferred as free bounds or certificates.

**Table R130.3. Contribution interpretation matrix.**

| Comparison | Actual question | Scope boundary |
| --- | --- | --- |
| S2/P | complete adopted method versus cold compact | all integrated differences; primary benchmark |
| PS/P | net independently paid H and full Start integration | neither a free solution nor guaranteed improvement |
| S2/PS | same-H complete backend/representation/control increment | does not isolate an individual cut or threshold |
| S2/S2R | same effective root, exposed outer package | probing, targets, domain-dependent rows, scheduling and splits together |
| S2R/PS | same-H single-root strengthened representation versus original compact | representation, LP preprocessing and cutoff domain remain coupled |

Execution is **COMPLETE**. The finite claim decision is **`SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION`**. The adopted S2 has repeated direct same-H backend support: on B20 it saves 233.71554430003744 and 123.61303300003055 seconds against independently paid PS, and on C20 it certifies at both Seeds while PS remains open. The outer package has no repeated certificate or material time increment in this panel. B20 exposes three natural splits and one reached partial target at each Seed, but S2R certifies in 1.3975899000652134 and 1.5858365014428273 seconds versus S2 in 3.5585215999744833 and 3.5044260000577196. C20 has no split/target exposure; its S2/S2R differences are also time-close. All four both-certified S2/S2R observations are TIME_CLOSE; their strict three Lose and one Win directions remain. All four methods stay open on B30 at both Seeds. No repeated material reverse reference role or proof/identity problem is observed. Retain S2 as the sole paper method and narrow decomposition-speed claims to this limited evidence; no additional experiment is required or authorized. This does not reconsider R129's passed selection or combine per-instance winners. PS remains a useful reference without needing to dominate P. This panel supplies no new single-cut C_G or C_R ablation for final S2, no V50/V60 validation, and no population robustness claim. R127's adverse selected P-tuned result, R128's timing reversal/no-split facts, R129's open C15/B30 results and its Seed-dependent endpoint reversals remain visible. The fixed attribution study ends without additional experiments.

## 7. Extended endpoint evidence and the known long-window proof boundary

### 7.1 Earlier R122 prospective panel and measurement

The earlier R122 panel [@benchmark122] was fixed before its six new inputs were generated once. It uses two frozen station sources: CITI with 442 eligible physical stations from 443 original rows, and CABI with 865 stations. Source identities, station selections and overlap records remain in the input manifest. The sources provide geographic station information; inventory landscapes and targets are constructed by the declared recipe.

The recipe retains four-anchor/hash selection and tie rules, target fractions .44–.56, coordinates serialized to three decimal places, weights to six decimals with maximum normalization, a centroid depot, stock-total correction and the declared heterogeneous or homogeneous capacity vectors. No H, LP or MIP screening selected problems by difficulty. There was no outcome-driven redraw, salt change or best-of-replicate selection.

**Table 2. Six new Seed0 problems.** Stock labels describe the construction. Lambda is .15 and pickup/drop are 60/60 throughout.

<!-- DESIGN_START -->

| Role | Source | n/m | Geometry / inventory | Q | Physical T \(s\) | Cap \(s\) | sum weights | lambda sum weights |
|---|---|---|---|---|---|---|---|---|
| PB-C20-B | CITI | 20/2 | compact / balanced | [30, 30] | 3600 | 900 | 7.288265 | 1.09323975 |
| PB-B20-S | CABI | 20/2 | regional / shortage | [20, 40] | 7200 | 900 | 7.2840239999999996 | 1.0926035999999999 |
| PB-C35-U | CITI | 35/3 | regional / surplus | [20, 25, 30] | 10800 | 2400 | 11.590113000000001 | 1.7385169499999999 |
| PB-B35-B | CABI | 35/3 | compact / balanced | [25, 25, 25] | 7200 | 2400 | 14.720000000000001 | 2.2080000000000002 |
| PB-C50-S | CITI | 50/4 | compact / shortage | [30, 30, 30, 30] | 10800 | 3600 | 20.216045000000001 | 3.0324067500000003 |
| PB-B50-U | CABI | 50/4 | regional / surplus | [20, 25, 35, 40] | 18000 | 3600 | 22.597221000000001 | 3.38958315 |

<!-- DESIGN_END -->

Each new problem has four complete arms: cold P-GRB, ENS-C, M-B and MB-D1. Two additional fixed blocks repeat PB-B35-B and PB-C50-S with solver Seed1. Thus there are six new problems, eight method/Seed blocks, 32 arms and 48 directed pairs. The repeats are sensitivity observations on known inputs, not two new problems. Within a block all methods share the same physical input and production cap. Serial method order rotates across the planned blocks; the complete schedule is retained with the published design.

All methods use the same frozen executable and Gurobi 13.0.2 DLL, one native thread, one MIP thread, PresolveAuto, the stated Seed, FeasibilityTol/OptimalityTol \(10^{-6}\), IntFeasTol \(10^{-5}\), and requested MIPGap/MIPGapAbs zero. The evidence policy remains \(10^{-7}\). The common 30-second native reserve is part of the one process deadline. Larger caps can change a method's search path, so a prefix of a longer run is not assumed to reproduce a shorter run.

Production time \(T_{\rm produce}\) includes all own online startup, models, LP/MIP work, Starts, callbacks, cleanup and sealing. Post-seal verification is \(T_{\rm verify}\); \(T_{\rm total}\) is their sum. Cross-arm reconciliation is group cost, and nested native timers are not added again. A verification tail beyond the native reserve is not a producer timeout. We preserve original final output fleets as the primary U endpoints, even where a separately legal historical witness is slightly better.

The machine/software identity and full clocks are documented in Supplement S and the reproducibility notes. The comparison is within matched complete-method windows, rather than a mixture of historical executables, hardware states and caps. The finite nonfactorial design varies source, scale, geometry, stock, Q, T and aggregate weight together. It does not isolate their individual causal effects or estimate a population win probability.

### 7.2 Comparison and evidence tiers

The historical endpoint rule, retained only for these older tables, is certificate first. A candidate-only qualified certificate wins; a control-only certificate is a severe loss. When both certify, the time-materiality threshold is \(\max(30\text{ s},.10T_{\rm control})\). Severe certified regression additionally requires twice the control time and at least 120 seconds excess. Actual time ratios are meaningful only for two certified results.

For two open results let \(\mathrm{gap}=U-L\), \(a_U=\max(.001,.01|U_{\rm control}|)\), and \(a_{\rm gap}=\max(.001,.10|\mathrm{gap}_{\rm control}|)\). Material improvement in U or gap without opposing material deterioration is WIN; the reverse is LOSS; opposing changes are MIXED; otherwise TIE. Severe open regression requires both specified U and gap deteriorations, with thresholds \(\max(.001,.05|U_{\rm control}|)\) and \(\max(.005,.25|\mathrm{gap}_{\rm control}|)\). Missing necessary evidence remains UNEVALUABLE. These are experiment-selection/materiality labels, not statistical significance tests.

We distinguish nonzero numerical certification, an independent own-zero certificate, reliable open bounds, source-reduced evidence and missing evidence. The R122 panel has seven nonzero certified arms and 25 open arms; it has no zero certificate, source-reduced arm or missing arm. All seven certificates are at 20 stations. The Seed0 layer contains 24 arms; the Seed1 layer contains eight open arms. PB-B35-B Seed0 cold P uses the explicitly independent lower floor zero, rather than a positive native proof. The tiny positive Seed1 bound is retained.

### 7.3 All historical outcomes and adverse cases

**Table 3. All 32 published R122 arms.** N denotes a nonzero numerical certificate and O a reliable open result, including the stated independent floor. U/L and signed gap are role-specific; caps are production windows. Supplement S1 retains full precision and \(T_{\rm verify},T_{\rm total}\) for every row. The displayed tiny signed gaps are not clipped.

<!-- R122_START -->

| Role | Seed | Method | Cap \(s\) | U | L | Signed gap | Tier | T_produce \(s\) |
|---|---|---|---|---|---|---|---|---|
| PB-C20-B | 0 | P-GRB | 900 | 0.2246803118 | 0.1765783752 | 0.04810193667 | O | 872.58902 |
| PB-C20-B | 0 | ENS-C | 900 | 0.2246803118 | 0.2246803118 | -1.110223025e-16 | N | 430.55759 |
| PB-C20-B | 0 | M-B | 900 | 0.2246803118 | 0.2246803118 | 1.054711873e-15 | N | 395.85954 |
| PB-C20-B | 0 | MB-D1 | 900 | 0.2246803118 | 0.2246803118 | 2.498001805e-16 | N | 665.06878 |
| PB-B20-S | 0 | ENS-C | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 4.6224331 |
| PB-B20-S | 0 | M-B | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6319677 |
| PB-B20-S | 0 | MB-D1 | 900 | 0.8631523206 | 0.8631523206 | -2.220446049e-16 | N | 2.6983887 |
| PB-B20-S | 0 | P-GRB | 900 | 0.8631523206 | 0.8631523206 | 1.110223025e-16 | N | 116.03278 |
| PB-C35-U | 0 | M-B | 2400 | 0.1696364022 | 0.08395185429 | 0.0856845479 | O | 2372.5264 |
| PB-C35-U | 0 | MB-D1 | 2400 | 0.1793004366 | 0.08353399353 | 0.09576644305 | O | 2370.6204 |
| PB-C35-U | 0 | P-GRB | 2400 | 0.1747718876 | 0.05970290317 | 0.1150689844 | O | 2370.6162 |
| PB-C35-U | 0 | ENS-C | 2400 | 0.1642374878 | 0.08157539377 | 0.08266209402 | O | 2370.5989 |
| PB-B35-B | 0 | MB-D1 | 2400 | 0.2345814099 | 0.09200798362 | 0.1425734262 | O | 2372.4404 |
| PB-B35-B | 0 | P-GRB | 2400 | 0.3055557782 | 0 | 0.3055557782 | O | 2370.5561 |
| PB-B35-B | 0 | ENS-C | 2400 | 0.2465044704 | 0.132287968 | 0.1142165024 | O | 2370.5527 |
| PB-B35-B | 0 | M-B | 2400 | 0.2465044704 | 0.1276343018 | 0.1188701686 | O | 2371.7862 |
| PB-C50-S | 0 | MB-D1 | 3600 | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3572.8812 |
| PB-C50-S | 0 | M-B | 3600 | 0.3723417755 | 0.3568747399 | 0.01546703556 | O | 3570.5953 |
| PB-C50-S | 0 | ENS-C | 3600 | 0.3723417755 | 0.3579807999 | 0.01436097562 | O | 3571.8954 |
| PB-C50-S | 0 | P-GRB | 3600 | 0.4259500753 | 0.3492206958 | 0.07672937949 | O | 3583.0202 |
| PB-B50-U | 0 | P-GRB | 3600 | 1.176955759 | 0.06837938241 | 1.108576376 | O | 3572.991 |
| PB-B50-U | 0 | MB-D1 | 3600 | 0.677298419 | 0.4712348696 | 0.2060635494 | O | 3570.563 |
| PB-B50-U | 0 | M-B | 3600 | 0.6974735096 | 0.4553454 | 0.2421281096 | O | 3571.8624 |
| PB-B50-U | 0 | ENS-C | 3600 | 0.8325480152 | 0.4523603674 | 0.3801876478 | O | 3570.5731 |
| PB-B35-B | 1 | ENS-C | 2400 | 0.2345814099 | 0.1146410114 | 0.1199403984 | O | 2372.9734 |
| PB-B35-B | 1 | P-GRB | 2400 | 0.2797984344 | 2.027189664e-18 | 0.2797984344 | O | 2370.5117 |
| PB-B35-B | 1 | MB-D1 | 2400 | 0.2345814099 | 0.138322042 | 0.09625936783 | O | 2370.6168 |
| PB-B35-B | 1 | M-B | 2400 | 0.2465044704 | 0.0982245518 | 0.1482799186 | O | 2370.4896 |
| PB-C50-S | 1 | M-B | 3600 | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.6028 |
| PB-C50-S | 1 | ENS-C | 3600 | 0.3723417755 | 0.358161762 | 0.01418001348 | O | 3570.6597 |
| PB-C50-S | 1 | P-GRB | 3600 | 0.3917805586 | 0.3494508596 | 0.04232969893 | O | 3570.6723 |
| PB-C50-S | 1 | MB-D1 | 3600 | 0.3723417755 | 0.357008334 | 0.01533344153 | O | 3572.5642 |

<!-- R122_END -->

**Table 4. Directed-pair classifications by denominator.** All 48 individual records, including the nine LOSS/MIXED observations, are in Supplement S2.

<!-- PAIRS_START -->

| Seed | Denominator | Pair | WIN | LOSS | MIXED | TIE | UNEVALUABLE |
|---|---|---|---|---|---|---|---|
| 0 | 6 new problems | MB-D1/P-GRB | 5 | 0 | 1 | 0 | 0 |
| 0 | 6 new problems | M-B/P-GRB | 6 | 0 | 0 | 0 | 0 |
| 0 | 6 new problems | ENS-C/P-GRB | 6 | 0 | 0 | 0 | 0 |
| 0 | 6 new problems | MB-D1/M-B | 1 | 2 | 1 | 2 | 0 |
| 0 | 6 new problems | MB-D1/ENS-C | 1 | 2 | 1 | 2 | 0 |
| 0 | 6 new problems | M-B/ENS-C | 1 | 1 | 0 | 4 | 0 |
| 1 | 2 fixed repeats | MB-D1/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | M-B/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | ENS-C/P-GRB | 2 | 0 | 0 | 0 | 0 |
| 1 | 2 fixed repeats | MB-D1/M-B | 1 | 0 | 0 | 1 | 0 |
| 1 | 2 fixed repeats | MB-D1/ENS-C | 1 | 0 | 0 | 1 | 0 |
| 1 | 2 fixed repeats | M-B/ENS-C | 0 | 1 | 0 | 1 | 0 |

<!-- PAIRS_END -->

M-B/P and ENS-C/P each produce six WIN on the six new roles. These are the historical complete-endpoint rule results, which combine certification and open-endpoint comparisons. They do not mean that all six problems certified faster, and they are not the direct certification outcome of Section 6. The two fixed Seed1 repeats retain WIN against cold P for each integrated method, but add no independent problems. M-B versus ENS-C has one WIN, one LOSS and four TIE on new roles; over all eight blocks it has one WIN, two LOSS and five TIE. Thus the chosen paper reference does not dominate the unchanged default instance by instance.

On PB-C20-B, all methods have the same final physical value, approximately .2246803118. M-B, ENS-C and D1 certify, while cold P remains open. M-B takes 395.8595 production seconds and ENS-C 430.5576; their difference is below the declared materiality threshold. D1 takes 665.0688 seconds and loses both incremental certified-time comparisons. Cold P's open run supplies no ratio of times to optimality.

PB-B20-S gives the other certification case. All four methods certify approximately .8631523206. Cold P takes 116.0328 production seconds, compared with 2.6320 for M-B, 4.6224 for ENS-C and 2.6984 for D1. This case permits actual certified-time comparisons. The small integrated-method differences fall below the 30-second minimum materiality floor; the panel's TIE labels should not be mistaken for identical measured times.

The V35 cases expose tradeoffs. PB-C35-U is open for every method. M-B has better U and gap than cold P, yet loses to ENS-C because its final U and gap are worse at the material scale. D1/P is MIXED: its weaker physical endpoint accompanies a stronger lower endpoint and smaller gap. D1 loses to both M-B and ENS-C. These outcomes remain even though the complete integrated family improves over cold P.

On PB-B35-B Seed0, D1 has a better U than M-B and ENS-C but a sufficiently weaker lower bound and larger gap that both incremental pairs are MIXED. With Seed1, those two D1 comparisons become WIN, and M-B/ENS-C changes from TIE to LOSS. All remain open. These fixed repeats show meaningful sensitivity without authorizing selection of the better Seed.

PB-B50-U supplies the sole new-role material D1/M-B WIN: D1 improves both physical U and the lower endpoint relative to M-B, and also improves on ENS-C. It nevertheless remains open. PB-C50-S supplies common integrated gains without natural D1 installation at either Seed. Such an unexposed candidate result is still a valid complete-method observation; no extra probe is forced to manufacture mechanism exposure.

D1's five new-role exposures and its two V20 certificates do not satisfy the declared promotion requirement of at least two exposed new roles with an incremental M-B win or added certificate. Only PB-B50-U qualifies. The completed panel therefore retains the MIXED selection conclusion, with M-B as the existing paper reference and ENS-C as project default. D1 keeps research/ablation value. D0 is not a reserve selection, and the discontinued MB-PC development is not revived.

Historical evidence is used only to constrain attribution. Earlier paid-start/backend comparisons distinguish the value of an own feasible startup from backend representation changes; they do not justify assigning an integrated win to an unexposed row. Earlier D1 C2 Seed0 severe loss and later Seed1 gain, and the F2 D0 Seed reversal, remain separately scoped adverse observations. We do not combine their executables or windows with this panel to construct a formal acceleration factor.

The completed five-role historical paid-start layer is MIXED for both integrated methods against P-S, which pays the same complete H before the original compact backend. Some tailored results improve proof completion after matched startup, while other roles favor P-S. Rejected native positive bounds and surviving independent own-zero witnesses keep their separate evidence grades. That layer also spans different measurement policies and cannot yield a pooled exact speedup. The [finite attribution note](historical_attribution.md) identifies the concrete source reports and their limitations.

### 7.4 One known positive-objective long-window problem

The separate long-window study [@proof123] concerns PB-C50-S only, with 50 stations, four capacity-30 vehicles, physical \(T=10800\), solver Seed0, and three freshly paid 18000-second caps in the fixed order P-GRB, M-B, ENS-C. No previous route, bound, tree, basis or cutoff is loaded. The study adds zero independent problem samples and does not include D1.

Its station totals are \(\sum b_i=495\) and \(\sum D_i=562\). Empty departure and nonnegative return imply \(\sum Y_i\le495\); therefore \(\sum_i|Y_i-D_i|\ge67\). Positive lambda and weights give

\[
F\ge67\min_i(\lambda\omega_i/D_i)>0.
\tag{10}
\]

The prior exact-decimal explanation gives .24814831875, with a tighter inventory-only penalty floor .26064825 already documented. These are weaker than the published production bounds and are not injected into this method. Their purpose is to rule out an independent zero certificate for this role. No new inventory relaxation or route optimization is performed in preparing the paper.

**Table 5. One known-problem long-window study.** All three endpoints are reliable and open. No row is a time to optimality.

<!-- R123_START -->

| Method | Cap \(s\) | U | L | Signed gap | Certified | T_produce | T_verify | T_total |
|---|---|---|---|---|---|---|---|---|
| P-GRB | 18000 | 0.37764170855020796 | 0.35037793304081627 | 0.027263775509391686 | False | 17971.7112989 | 1.96611939999 | 17973.6774183 |
| M-B | 18000 | 0.3723417754990474 | 0.35801148555184259 | 0.014330289947204811 | False | 17970.5725766 | 40.964555 | 18011.5371316 |
| ENS-C | 18000 | 0.3723417754990474 | 0.35894366616771595 | 0.013398109331331454 | False | 17970.8751446 | 58.2420274 | 18029.117172 |

<!-- R123_END -->

Under the same fixed rule, M-B/P and ENS-C/P are WIN, and M-B/ENS-C is TIE. M-B improves U over cold P by .005299933051160555 and raises L by .00763355251102632; the signed gap decreases by .012933485562186875. ENS-C has the same final U as M-B and a .000932180615873357 higher L. The latter difference is below the pair's gap-materiality threshold. Arithmetic endpoint gains are not ratios of solver speed, and F* remains unknown.

M-B's final-quality fleet appears in the raw process record at 34.328 seconds; its qualified arm-availability upper time is 35.7173270817 seconds. No better own U is observed afterward. This does not establish that U is optimal, nor that all remaining work is pure proof. ENS-C has an early raw startup record at 34.312 seconds, but its clock-origin spread of 1.5845544376 seconds fails the predeclared one-second conversion check. Its four pre-end arm-clock checkpoints remain unknown. The sealed endpoint and separately measured QPC production/verification clocks remain qualified. We neither widen the guard nor compare those raw times as precise cross-method arm times.

The final coverage explains the outstanding proof rather than extrapolating from a plateau.

**Table 6. Actual final integrated-method covers.** “Empty” excludes improvement under the applicable cutoff; it does not assert unrestricted physical infeasibility.

<!-- COVER_START -->

| Method | Unit | True-G lower | True-G upper | Regional floor | State |
|---|---|---|---|---|---|
| M-B | L0.1 | 0.1861708877495237 | 0.3723417754990474 | 0.3723417754990474 | empty |
| M-B | L0.0.1 | 0.09308544387476185 | 0.1861708877495237 | 0.3723417754990474 | empty |
| M-B | L0.0.0.0 | 0 | 0.046542721937380925 | 0.35801148555184259 | open |
| M-B | L0.0.0.1 | 0.046542721937380925 | 0.09308544387476185 | 0.35882784229299913 | open |
| ENS-C | L0.1 | 0.1861708877495237 | 0.3723417754990474 | 0.3723417754990474 | empty |
| ENS-C | L0.0.1 | 0.09308544387476185 | 0.1861708877495237 | 0.3723417754990474 | empty |
| ENS-C | L0.0.0.0 | 0 | 0.046542721937380925 | 0.35894366616771595 | open |
| ENS-C | L0.0.0.1 | 0.046542721937380925 | 0.09308544387476185 | 0.36638496476834997 | open |

<!-- COVER_END -->

The low interval and its adjacent interval are

\[
\begin{aligned}
I_0&=[0,.046542721937380925],\\
I_1&=[.046542721937380925,.09308544387476185].
\end{aligned}
\]

Both remain unresolved. The final own \(G_{\rm true}=.050119584194518604\) lies in \(I_1\), so that fleet cannot provide an exact-g Start for \(I_0\). M-B makes seven LP and one MIP request; its \(I_0\) NEXT request uses about 17808.127 seconds. ENS-C makes nine LP and three MIP requests, including both interval targets and a subsequent low-interval terminal request. Child LP count and committed split count are different; counts do not establish retained native search trees or an internal cause of difficulty.

A fixed-endpoint counterfactual ledger illustrates why more than one obligation matters. Hold U and all other regional floors fixed. Raising only M-B's \(I_0\) floor to U leaves \(U-L_1=.013513933206048268\); closing only \(I_1\) leaves the global minimum at the old \(I_0\) floor. This follows from the union minimum in (9). It is not a prediction that a different leaf schedule would perform better, and does not justify launching another experiment.

All three normal long-window observations are complete, qualified open results. The finite study records a proof limit, not an execution failure. The longer cap ends here. There is no final certification-time ratio, linear remaining-time prediction or automatic extension until a certificate appears.

