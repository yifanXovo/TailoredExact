# Round143: reciprocal-normalized Gini on stable GI-TBC

RN supplies real complementary LP information, but the two priority same-PE Seed0 pairs do not show a sufficient complete-method benefit. Retain the uniform lift as research-only and stop full expansion this round; stable R137 GI-TBC remains the paper mainline.

RN supplements the old shared-g products with a common reciprocal t, normalized inventory and normalized pair differences. It keeps the original integer route/inventory structure and original penalty. Its integer extension and continuous inclusion are exact on a proved positive-denominator scope. The separate research switch defaults off. Stable R137 remains available.

## Matched continuous objectives

All four new LPs are numerical optima under unchanged 1e-6 feasibility/optimality qualification, explicit Gurobi Seed 0, Threads 1 and affinity mask 4, run serially. The original complete objective, cutoff, support, g interval and old matrix are retained. BASE gains include physical inventory information used for t bounds; TC+stock controls still show information beyond that older resource/count combination.

| Role | Old expression | Old L | RN L | Gain |
| --- | --- | --- | --- | --- |
| K35 | base | 0.200177662 | 0.228090497 | 0.027912835 |
| K35 | tc_stock | 0.218088779 | 0.228090497 | 0.0100017179 |
| RX20-T1 | base | 0.331594316 | 0.389761616 | 0.0581672999 |
| RX20-T1 | tc_stock | 0.37755753 | 0.394121979 | 0.0165644487 |

| Role / expression | Old g | RN g | Old weighted P | RN weighted P |
| --- | --- | --- | --- | --- |
| K35/base | 0.0386391834 | 0.0665520184 | 0.161538479 | 0.161538479 |
| K35/tc_stock | 0.0565503004 | 0.0665520184 | 0.161538479 | 0.161538479 |
| RX20-T1/base | 0.100712705 | 0.17210734 | 0.230881611 | 0.217654276 |
| RX20-T1/tc_stock | 0.14667592 | 0.173850507 | 0.230881611 | 0.220271472 |

| Role / expression | Added rows | Added columns | Added nonzeros | Build / solve s |
| --- | --- | --- | --- | --- |
| K35/base | 2340 | 1170 | 7474 | 1.7644687 / 0.5281877 |
| K35/tc_stock | 2340 | 1170 | 7474 | 1.8504794 / 1.6446136 |
| RX20-T1/base | 708 | 354 | 2232 | 0.4122916 / 0.0574667999 |
| RX20-T1/tc_stock | 708 | 354 | 2232 | 0.4220257 / 0.0796056001 |

Actual denominator bounds, reciprocal endpoints, complete row/column/nonzero counts, Runtime/Work, all quality measures and actual source/solution hashes are in reports/LP.json and LP.csv. These reoptimized full-objective gains are separate from saved-point exclusions. Four diagnostic Optimize calls were sufficient; no RN x TC2 x CP grid was opened.

## Complete same-PE methods

Each method pays for its own H (separate fixed seed 20260626), root/lookahead, online validation and complete Native proof search. The stable carrier is M-B/VD-P, pair-only, AM=.08, depth 8, minimum width 1e-4, AP off; stock, TC/TC2, count disjunction and CP are off. Each entered role receives its original full cap. Diagnostic/historical solutions or bounds are never injected.

| Role | Method | U | Supported L | Relative gap | T cert s |
| --- | --- | --- | --- | --- | --- |
| K35 | stable-off | 0.692854359 | 0.557158766 | 0.195850096 | open |
| K35 | RN | 0.681258498 | 0.542931774 | 0.203045869 | open |
| RX20-T1 | stable-off | 0.64532503 | 0.64532503 | 3.44e-16 | 22.206689 |
| RX20-T1 | RN | 0.64532503 | 0.64532503 | 1.24e-09 | 23.4901348 |

| Role / method | Produce s | Verify s | Total s | Splits |
| --- | --- | --- | --- | --- |
| K35/stable-off | 2371.14246 | 4.1181738 | 2375.26063 | 0 |
| K35/RN | 2371.10851 | 6.0289586 | 2377.13747 | 0 |
| RX20-T1/stable-off | 22.206689 | 1.1920446 | 23.3987336 | 0 |
| RX20-T1/RN | 23.4901348 | 1.4364241 | 24.9265589 | 0 |

| Same-PE role | RN - off U | RN - off L | Produce delta s | Total delta s |
| --- | --- | --- | --- | --- |
| K35 | -0.0115958603 | -0.0142269917 | -0.033952195 | 1.87683261 |
| RX20-T1 | 0 | -7.97e-10 | 1.28344575 | 1.52782525 |

K35 is a real tradeoff: RN lowers verified U by 0.0115958602505 but also lowers supported L by 0.0142269916815. Its signed gap grows from 0.135695592698 to 0.138326724129, and relative gap grows from 0.195850096067 to 0.203045869458. Both remain qualified-open after the full 2400-second caps. Producer time is essentially unchanged; RN adds 1.91078480007 seconds of verification and 1.87683260511 seconds to complete total. RX20-T1 certifies the same verified physical objective 0.645325030386 with both methods; RN raises producer/certificate time from 22.2066890239 to 23.4901347759 seconds and total from 23.3987336238 to 24.9265588757 seconds. The 7.97e-10 returned-L difference is within the inherited numerical policy and is not a substantive mathematical loss or gain.

Open T_cert is null, never the cap. Native returned ObjVal/ObjBoundC and externally merged supported L are separately retained. Root LP, AM decisions, outer splits, terminal nodes/Work and full Native logs explain observed outcomes without equating LP strength with search speed. One Seed does not identify a runtime distribution or attribute every difference directly to a new row.

All four formal positions have zero outer splits. Actual complete root bounds repeat the matched diagnostic improvements, but final Native cut/search behavior is different. K35 terminal nodes decrease from 16825 to 10779 while Work increases from 4691.00560053 to 4999.12908278. RX20-T1 nodes decrease from 2621 to 1620 while Work increases from 29.5418051573 to 34.9746070207. These are descriptive full-method effects, not a proof that fewer nodes mean less computation or that a specific added row caused every difference. Same-PE methods have matching complete own-H semantics and fleets; their full Native/H/Start/quality/lifecycle evidence is qualified.

## Qualifications, boundaries and cost

The three-station exact subblock separates 1/3 from 5/12; the four-station fixed-denominator example allows RN g=0 while retained TC+stock requires 1/4. RN is complementary and is not claimed to dominate the old count information or provide the complete integer objective hull. The original R140 carrier supplied twelve fixed-point checks with zero Optimize: six exclusions and six same-old-point extensions. The separately named offline ZIP was absent; reconstructed rank/eta certificates have their own identities and sometimes stronger bounds. They are not retroactively labeled as the missing old certificate bytes.

Production qualification includes exact dyadic full-scope bounds with directed conversion before reciprocal, actual c_i, zero-lower-bound omission, fixed-S and positive-S fixtures, nonminimal epigraph extensions, complete old/new Start values, preservation of the physical-G Start-domain rule, and actual Native reads of all new rows/coefficients/column types/bounds. K35 RN-off equals the inherited complete BASE matrix. All four affected units were recompiled; hybrid object/archive lineage and actual PE/DLL hashes are saved. Two new diagnostic failures occurred before Optimize, were repaired under new labels, and remain charged. Small offline constructor/search failures are separately recorded.

The conservative new experimental charge is **4880.559825 seconds (1.355711 hours)** of the 28800-second ceiling. This is the complete outer including qualification, failures and mandatory postverification, charged once. Nested H/LP/MIP/Work are nonadditive details. Build time is separately 37.893495 seconds; exact offline reconstruction, writing, independent review, PDF and public I/O are separate. Interactive editing/review does not receive invented timing precision.

The decision is RESEARCH_ONLY_STOP_FULL_EXPANSION_THIS_ROUND. Qualification and integer equivalence pass; nonpromotion follows the observed complete-method tradeoff and lack of proof-clock benefit, not a correctness failure. The code remains a separate uniform default-off research option. The tested result is not that RN is mathematically redundant, generally slower, or incapable of benefiting an untested instance.

No formal K20/RB35-T2 pair, optional K15/RX35-T2 pair or Seed1 is entered. K20 cap90 remains health-only; its saved-root extension is not a complete performance prediction. Other roles could characterize additional behavior, but there is no specific pending adoption/stop decision that their measurement would change after the priority hard-role support-bound regression and the second role's proof-clock result. Seed1 would not erase the retained adverse Seed0 result or establish a runtime distribution. Reopening requires a concrete new mechanism or decision-changing evidence, rather than a missing table. Stopping occurs with substantial budget remaining.

## Reproduction and delivery identity

Actual production source is `85bd2304866942fd5b397970c5ef4099bb1b73fb`; PE SHA256 is `eaa6dc5d0091a1f3a38a0374aeccab28e94bff94606339c62b385b48cb7d44b1`. DLL SHA256 is `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`. The carrier is stable R137 plus uniform RN, not R138-R142 mechanism stacking. Source/PE/helper/input/parameter matrices and actual returned calls are bound separately from later report metadata. The research entry is `scripts/paper_s2_rn.py`, profile `config/gi_tbc_rn_round143.json`, with `--rn on|off`; it expands only unless `--run` is explicit. `RESUME.md` describes safe continuation and the no-repeat rule.

The mathematical/history/literature note and independent reviews separate four evidence levels: standard construction and integer equivalence, strict subblock/saved-point relations, reoptimized LP gains, and complete algorithm performance. Existing R88/R133/R138/R140 results and Charnes-Cooper, Yue et al. and Chen-Hooker antecedents retain their identities. No new general fractional-programming principle or higher-journal claim follows.

The formal stable GI-TBC manuscript is retained. The increment and full reports retain all entered favorable/adverse positions; missing configurations are not inferred. Fixed-science carriers, anonymous public byte/member recovery and bounded current-round cleanup have separate receipts. All new assets stay under ExactEBRP-work, protecting the original user tree and old rounds. No merge or force push is authorized.
