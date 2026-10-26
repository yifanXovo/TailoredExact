# Round130 final independent review

Decision: **PASS**, within the finite internal evidence review described below. The second complete checker run verified all 24 sealed formal arms and independently recomputed all 30 typed comparisons against the corrected author analysis. There are no remaining blockers within this scope. This review does not reopen the Round129 selection or adoption decision.

The reviewer only changed the independent checker and reviewer outputs. No heuristic, Optimize call, compilation, formal arm, or native retry was run by this final review. The checker imports established read-only physical, complete-Start, model, source/return/cover readers, but does not import the Round130 analysis or decision implementation as the authority for comparisons. Its NOT_READY gate prevents substantive result replay until the fixed 24 arms and required author analysis outputs are complete. The run used the existing outer meter serially.

The first complete run found a real reporting defect: the frozen qualifier's shape-based row-family classifier counted cross-vehicle station-uniqueness rows as same-vehicle pair covers. Complete model and row-multiset checks remained valid; this was a support-family count error. The parent corrected only the later analysis-local classification using the Round129 same-vehicle rule, retained the original qualifier, native evidence and first failed review, and documented the changes in `review/support_count_correction/addendum.json` and `.md`. For S12, historical shared/fallback pair-cover counts changed from 12 to 0, with 132 conditional rows unchanged. Formal B20 now has 320 pair-cover plus 60 conditional rows, C20 has 0 plus 380, and B30 remains 1305 total. The original zero-qualification JSON SHA remains `3bc192a365aebcf3717a7850afba036724303a85e8217aa981d3fb663ee36454`. No model, native result, parameter, clock, bound, or certificate changed. The correction's first exclusive-create failure and its successful recovery were retained by the parent. The reviewer then repeated the entire 24-arm/30-comparison check; the PASS is not a partial count-only rerun.

All 24 complete final fleets were physically replayed using the established read-only evaluator, including nonempty fleets. For example, B20 Seed0 P has two vehicles with capacities 20 and 40, a maximum route duration of 7121.276242513246 seconds, and replayed F = 0.5773330699702928, G = 0.17083306997029268 and penalty = 2.7100000000000004. The checker read all 18 paid-H flows, checked each arm's own evidence and the six same-H/effective-root groups, and confirmed full P/PS compact model and fixed-parameter equality. It checked 18 distinct actual model hashes. Witnesses from the eight qualified, physically verified arms for each input were used only to revoke a contradictory global lower bound above their minimum own upper bound plus the existing 1e-7 tolerance. No upper bound, lower bound, certificate, or time was transferred between arms; no contradiction was found.

All six PS complete Starts were checked against the original full models, including submitted/readback values. Maximum residuals were at most 1.9761969838327786e-14. Seed1's raw journal prerequisites remain false while the computed returned-call scope is true; the raw and computed layers are explicitly separate in the receipt. The original equality between computed endpoint certification and the raw strict endpoint flag remains enforced. B20 PS is certified at both Seeds; C20 and B30 PS remain open. Supplying a Start is not treated as proof that the native solver adopted its incumbent.

All six S2R arms have one pre-LP check with original variable types restored, one submitted full Start, equal complete pre-LP/submitted/readback vectors, one root LP and one root MIP, and the qualified inclusive same root. There is no child, NEXT, partial return, split, or rebuild in this control. Both native calls must be OPTIMAL for native completion: B20 and C20 satisfy this at both Seeds; each B30 root MIP is TIME_LIMIT and remains open. C20 Seed1 S2 and S2R retain the signed U-L value -1.4988010832439613e-15 within the original window; lower bounds were not clipped.

Actual S2 split coverage was checked where exposed: each B20 Seed has three committed atomic splits, with two-child geometry, common endpoints, chronological source/return records and final coverage checked. The semantic `0 <= -1` rows were checked against their actual domain/cutoff and weighted penalty-floor premises, retaining the signed comparison to the cutoff and distinguishing strict, equality and near-equality cases. C20 and B30 expose no actual split/target run, so they do not support an empirical split-exposure claim. The measured treatment is the whole outer package; these data do not isolate a gain from the split formula alone.

Certified counts are P/PS/S2/S2R = **2/2/4/4**, each out of six arms. The independently implemented material-time rule is symmetric: the slower-minus-faster difference must reach `max(10 seconds, 10% of the faster time)`. All five comparison types share the same six matched input/Seed groups (three inputs and two Seeds), not 30 independent trials. Win/Lose refers to the left method; TIME_CLOSE cases retain their strict ordering separately.

| Comparison | Win | Lose | Undetermined | Both certified | Other classes |
|---|---:|---:|---:|---:|---|
| S2 / P | 4 | 0 | 2 | 2 | Left-only certified 2; both open 2 |
| PS / P | 2 | 0 | 4 | 2 | Both open 4 |
| S2 / PS | 4 | 0 | 2 | 2 | Left-only certified 2; both open 2 |
| S2 / S2R | 1 | 3 | 2 | 4 | Both open 2 |
| S2R / PS | 4 | 0 | 2 | 2 | Left-only certified 2; both open 2 |

The four jointly certified S2/S2R comparisons are all TIME_CLOSE under that symmetric rule, despite strict ordering of three losses and one win. B20 and C20 show a repeated direct increment over the same-H compact backend at both Seeds; B30 is undetermined. No role shows repeated material outer-control gain, and no repeated reverse reference role was found. B20's outer comparison has actual split exposure; the C20 timing comparison does not. The independently recomputed axes match `SELECTED_MS2_WITH_SCOPED_OR_MIXED_ATTRIBUTION`. This is a scoped attribution result, without an unqualified empirical claim that outer splitting itself supplies a repeated speed gain.

The successful checker elapsed time was **158.76830920006614 seconds**; outer metering was **158.9047305000713 seconds**, exit 0. The first failed run took 162.03254719998222 checker seconds and 162.15818799997214 outer seconds, exit 1. Both `fees/final_independent_01` and `fees/final_independent_02` are closed; their combined outer charge is **321.06291850004345 seconds**. The previous evidence receipt is preserved as `final_independent_evidence.prior01.json`, with additional first-failure preservation under `review/support_count_correction/`. No failed cost was discarded.

This is an internal, finite replay of the supplied sealed evidence, reusing established read-only validators. The portable checker is prepared for a supplied recovery root and forbids fallback to the original root; this review did not perform a separate public empty-root recovery or third-party external replication. It is not a full rational proof, a review of all historical campaigns, a larger-instance extrapolation, or a final manuscript/PDF audit. Parent authoring and publication follow this report.

| Bound artifact | SHA-256 |
|---|---|
| `scripts/round130_portable_check.py` | `2f2f2343c375ed4617d071a96d428a8461275771cc82bd222769e7ab57e572da` |
| `review/final_independent_evidence.json` | `8dbe8ce7a3913e59fdf1d37f6c690eaf99e1e0fe7fffeed32b657edde237936b` |
| `execution_binding.json` | `284e93a2fc82f012edb81af488a0a34a9d16c1c334cbca2afbf40fd1acf8c355` |
| Frozen argv | `860f22a5cb58f8d95edb0743cfe2054b424646b722ed8dc94463de5ab86640e0` |
| Corrected scientific decision | `b05b7b0516ddafc279c2112043e6ee9126b82b8b032717bc255446c8d60aa490` |
| Frozen E3 metadata | `0fc64deef5e52c2db4a4d00ca50a69c56bc2aae2651be5bd8616ca7ad5a9506f` |
| E3 PE identity recorded in evidence | `2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c` |

Reviewer: independent executor `/root/preformal_review`; 2026-10-22. Machine-readable evidence is the accompanying PASS receipt. The PE bytes were not loaded or executed by this checker.
