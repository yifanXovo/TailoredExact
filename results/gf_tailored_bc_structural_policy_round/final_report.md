# Structural Cut Activation Policy Round

Status: `fixed_interval_solved_route_callback_selected_old_cutoff_not_fathomed`.

## Fresh evidence boundary

1. **Were all comparisons based only on fresh rows from this round?** Yes. All 61 raw rows have `fresh_run=true`, package-local paths, a command hash, and a source commit. `audit_no_cross_round_result_mixing.py` audited 98 artifacts with zero failures. Previous rounds appear only in `historical_context.md`.

2. **Did vector parsing improve, and what remains unparsed?** Yes. The parser now explicitly classifies McCormick (`prod_*`, `zprod_*`), service-order (`ord_*`), low-Gini estimator (`q_l1_*`, `r_min`, `r_max`), bit, load, and current structural product variables. Across 128,698 parsed vector rows, `unknown_unparsed=0` (0%). Missing root snapshots remain unavailable rather than zero-filled.

## Mechanism results

3. **Which GS activation mode is best?** `gs_callback_upper_only`. It reached LB `0.0487383087046` at 1,200s, `0.0488223385636` at 3,600s, and the exact fixed-interval optimum `0.0491015319884` in `10,563.14s`. Static GS reached `0.0487233640003` at 1,200s and `0.0487638722254` at 3,600s. Static-plus-callback added no useful duplicate row. The diagnostic H lower row was numerically stronger at 1,200s but remains excluded.

4. **Did GS improve root or final bounds?** It improved the structural relaxation and final bound. The first static-tailored relaxation snapshot had `GSH_gap=0.00268613556`; static GS changed the sampled gap to `-0.000928334981`, consistent with enforcing `H <= V*W_GS`. Callback GS recorded the pre-cut snapshot and then added one violated global upper row. A matched numeric root-LP objective was unavailable for the hard models, so no unsupported root-objective claim is made. Final LB improved materially at 1,200s and 3,600s.

5. **Did disaggregated SP reduce SP gap or improve final LB?** It did not materially reduce the sampled product gap: aggregate `SP_gap=0.606482936461`, disaggregated `SP_gap=0.606482936456`. Additive SP nevertheless improved the 1,200s LB from `0.048388162834` to `0.0487233640003`, then plateaued through 3,600s. Replacing the aggregate estimator regressed at 300s (`0.0481673985699`) and did not dominate later. The existing valid e-domain bounds were already used; the `tight e` variant was therefore equivalent to additive SP.

6. **Did route cuts reduce fractionality or weaken the bound?** The callback snapshot is pre-separation, so a before/after fractionality reduction is not directly observable and is not claimed. Route-cutset callback inspected 898 candidates, added 46 cuts, and had maximum violation `1.90304988501`. It did not weaken any matched-budget bound: LB was `0.0487233640003` at 1,200s, best-in-set `0.0488356546044` at 3,600s, and the exact fixed-interval optimum at `7,502.81s`. Root-limited route rows added no useful violated rows and matched static.

## Selected policy

7. **Which structural profile is recommended?** `structural_route_limited`, implemented by `route_cutset_callback_limited`, is the dominant-bucket paper-safe candidate. It reached the same exact interval optimum as static in about 52.7% of static runtime and with fewer nodes (`635,246` versus `710,438`). `gs_callback_upper_only` is retained as the preferred GS policy. `auto-diagnostic` remains recommendation-only and is not a paper default by itself.

8. **Did any profile close the dominant bucket?** Not under the old-cutoff ledger semantics. All three very-long rows solved the fixed S-bucket interval to the same optimum near `0.0491015319884`, which is below the old cutoff `0.0491525526647`. Their status is therefore `interval_feasible_improving_ub`, not no-improver fathoming. The local fixed-interval optimum is exact, but it is not imported or propagated as a global UB in this round.

9. **Did any profile exceed the fresh static 14,400s baseline?** No in final LB: static, GS callback, and route callback all reached the same interval optimum within `1e-12`. Route callback reached it in `7,502.81s`, GS callback in `10,563.14s`, and static in `14,224.25s`, so the mechanisms substantially improved time-to-proof.

10. **Default, diagnostic, or disabled decisions:**

- Paper-default candidate for dominant low-Gini S buckets: limited callback route cutset.
- Paper-safe retained option: callback GS upper coupling.
- Paper-safe but not selected by long evidence: additive disaggregated SP and callback support cover.
- Not selected: root-limited support/route rows, GS+SP, and broad combined route profiles.
- Disabled by default: disaggregated SP replacement of the aggregate estimator.
- Diagnostic only: GS H lower/equality row and `auto-diagnostic` policy output.

## Safety and remaining work

11. **Did non-regression sanity checks pass?** Yes. `high_imbalance_seed3201_hard` and `tight_T_seed3102_hard` closed at 300s. `low_gini_2` remained honest and unresolved with LB `0.0489209015481` and gap-to-cutoff about `0.000231651117`.

12. **Were all new rows paper-safe?** All recommended GS upper, SP additive, support-cover, and directed cutset rows are paper-safe. The H lower-row run and auto-policy run are marked diagnostic and excluded from paper selection. Plain MIP is benchmark-only.

13. **Was any UB imported or was the full frontier rerun?** No. No fixed-interval solution was imported as a global UB, and no full-frontier run with an imported UB was performed.

14. **What exact weakness remains?** At short budgets, the dominant relaxation retains a large S-P McCormick gap, while GS and route connectivity improve search without eliminating that product weakness. At the long endpoint, the fixed interval itself is no longer unresolved: all selected models prove its local optimum. The remaining framework issue is a certificate-safe, same-run verifier-gated incumbent handoff and a new sealed full-frontier run; this round deliberately did not perform that propagation.

## Audit summary

- Certificate audit: 61 rows, 0 failures.
- Tailored callback audit: 61 rows, 0 failures.
- Summary, thread fairness, objective convention, and finalization audits: 61 rows each, 0 failures.
- GS, SP, and vector-route mechanism audits: 61 rows each, 0 failures.
- Paper-strict algorithm registry: 172 rows, 0 failures.
- Cross-round mixing: 98 artifacts, 0 failures.
- Vector parser/structural summary audits: 0 failures.
- No-instance-special-case audit: passed.

Recommended next step: implement and audit same-run verifier-gated incumbent propagation from a solved compact interval into the frontier controller, then launch a new sealed full-frontier run. Do not import this round's fixed-interval artifact as an external incumbent.
