# Round126 independent certification review

A separate executor re-read the actual evidence for all 12 formal arms and independently computed all six classifications and time comparisons. No solver, H, LP/MIP, route search, input generator or production mutation was run. The original evidence hashes were stable before and after this review.

The independently derived category counts are `{'BOTH_CERTIFIED': 3, 'MB_ONLY_CERTIFIED': 2, 'P_ONLY_CERTIFIED': 0, 'BOTH_OPEN': 1, 'UNEVALUABLE': 0}`. M-B certified 5/6 and cold P-GRB 3/6; all eight arm certificates are nonzero. The supported evidence classification is `LIMITED_DIRECT_CERTIFICATION_SUPPORT`.

| Problem | Independent class | M-B T_cert (s) | P T_cert (s) | P/M-B | Materiality | T_total P/M-B |
|---|---|---:|---:|---:|---|---:|
| SC-C15-S | BOTH_CERTIFIED | 41.562463900 | 464.293373107 | 11.170978078 | MB_FASTER | 11.010090249 |
| SC-B15-S | BOTH_CERTIFIED | 6.852653713 | 12.978682300 | 1.893964418 | TIME_CLOSE | 1.715227560 |
| SC-C15-B | BOTH_CERTIFIED | 44.081525100 | 243.923893864 | 5.533472204 | MB_FASTER | 5.417540690 |
| SC-B20-S | MB_ONLY_CERTIFIED | 1069.001713469 | null | null | qualitative only | null |
| SC-C20-S | BOTH_OPEN | null | null | null | qualitative only | null |
| SC-B20-U | MB_ONLY_CERTIFIED | 18.873570057 | null | null | qualitative only | null |

The both-certified subset is ['SC-C15-S', 'SC-B15-S', 'SC-C15-B'] (n=3): median speedup 5.533472204, geometric mean 4.892005267. This conditional subset is accompanied by two single-sided certifications and one both-open pair; caps never fill missing times.

## Actual checks and dependencies

Verified frozen PE/DLL SHA256, all 216 production bindings, all frozen helper hashes, six input identities, every seed/cap/command and physical parameter, each sealed producer/verification clock and closeout chain, 12 distinct process birth identities, and actual successful native return/lifecycle records. Independently replayed all 12 final fleets and matched Y, G, P and F to the inherited physical replay. Checked 54179 native claims against 466 saved physical witnesses within each input and actual true-G/cutoff scope.

Re-executed inherited read-only model contracts and all per-call log bindings, including actual M-B continuous-quantity/A-B rows and saved G/cutoff scopes, returned LP/MIP sources, chronological availability and complete final cover. Final L was separately aggregated from cold native readback or the raw relevant-leaf ledger. The complete audit `endpoint` was compared only after these computations; no top-level audit observation field supplies a final endpoint. All actual evidence classes were covered: eight CLEAN_NONZERO_CERTIFICATE and four RELIABLE_POSITIVE_LB_OPEN.

Groups 4 and 6 received a full re-read of both M-B and P-GRB dependencies, retained in the JSON call_details/model_contracts_reexecuted/final_leaf_records. Their P-GRB models are original cold compact matrices, with one successful TIME_LIMIT return each, positive own bounds and legal own fleets. Their M-B proof is an admitted full interval cover with the original positive final physical objective; neither is a startup-zero result.

For SC-B20-S, the independent final endpoints are M-B U=0.31538912105343897, L=0.3153891061850864, signed gap=1.4868352549157748e-8; P-GRB U=0.34024988028904835, L=0.20904961025549085, signed gap=0.1312002700335575. The M-B proof uses three returned OPTIMAL LP calls and the returned OPTIMAL terminal MIP on its saved true-G/cutoff scope; the P arm has its own cold TIME_LIMIT return. M-B's admitted raw lower bound remains below its final rounded terminal-log bound and was not replaced with U.

For SC-B20-U, the independent endpoints are M-B U=0.17376178911949686, L=0.17376178911949644; P-GRB U=0.22176908887700536, L=0.013396844392201526. Again all three M-B LP sources, the terminal MIP and the cold P return were re-read. The two zero-valued M-B LP relaxation optima are not original-problem zero certificates: the final original physical objective is positive.

The 32 returned actual native calls comprise 18 M-B OPTIMAL LPs, two INTERRUPTED child-bound-target MIPs, five OPTIMAL M-B terminal MIPs, one TIME_LIMIT M-B terminal MIP, and six cold MIPs (three OPTIMAL, three TIME_LIMIT). Interrupted target calls were checked as returned bound sources within their recorded scopes; their status was not promoted to a complete original certificate.

## Findings

- SC-C15-B cold P-GRB retains a signed gap of -1.734723475976807e-17, within the original 1e-7 policy; L was not clipped to U.
- SC-B15-S observed production speedup is below the 30-second materiality threshold and remains TIME_CLOSE despite a ratio above one.
- SC-B20-S and SC-B20-U are qualitative single-sided certification outcomes. Their P-GRB observations return normally before nominal cap; no cap-substituted speedup or lower bound is inferred.
- SC-C20-S remains BOTH_OPEN. Production duration orders M-B first while total duration orders P-GRB first; neither duration is a certification time.
- All eight certified arm endpoints have positive physical objectives; zero and startup-zero categories do not occur.
- No same-input, same-scope native-bound contradiction was found among the actual saved claims and physical witnesses checked.

## Execution and limits

`D:/msys64/ucrt64/bin/python.exe -B scripts/round126_run.py review_quant engineering 240 3600 scripts/round126_independent_audit.py`

Script SHA256: `c0e17fec42807f342111af90b2b882476b13080dd33c2ad2008417dbbdbf66b4`. The JSON records the exact reviewed file hashes, models, call scopes, terminal lines, fleet replay and clocks. Measured review child time before writing: 253.680844 seconds; final engineering charge is in `fees/review_quant/receipt.json` after controller closeout.

Post-exit closeout: the review child succeeded (exit 0). The actual outer charge was 253.9959458000376 seconds, 13.9959458000376 seconds beyond the initial 240-second declaration; `limit_exceeded=true` and the outer controller's reservation assertion (exit 1) are preserved. This successful review was not rerun. The parent authorized continuing the already-running pure review if needed; all actual seconds were charged, with zero native starts. Closed receipt SHA256: `c4b184c859ff12f01c295586d511dee640508a2c0e99e90da46d118bda07794a`.

- Established model/coverage mathematical predicates were re-executed from the saved raw assets; this is not a new independent formal proof of the model, cuts or floating-point solver.
- The physical check establishes legality and objective of recorded fleets only. It never searches for a new route, bound or certificate.
- The cross-arm source rejection search covers actually saved physically verified witnesses, and does not guarantee absence of all numerical or solver defects.
- Manuscript claims and final PDF layout are outside this quantitative reviewer scope and require the separate document review.
- This JSON is written before the parent fee controller observes this child exit; the matching review_quant receipt is the authoritative final task charge.
