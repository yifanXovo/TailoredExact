# Round130 independent preformal review

Date: 22 October 2026, Asia/Shanghai. Reviewer: a separate collaborating executor explicitly requested under task Section 11. Review base: `ce70acd2fb3fa6b7d0033f0cbc74c2aab3113d73`.

**Decision: ACCEPT the frozen E3 and the fixed 24-arm formal plan.** No unresolved source, PS same-model/paid-H, S2R inclusive-root, returned-call, or budget blocker was found in the limited review described below. This permits the task owner's admission step for the exact binding below; it is not a formal performance result, an additional MS2 selection round, or a proof of every floating-point matrix.

| Reviewed identity | SHA256 |
|---|---|
| `execution_binding.json` | `284e93a2fc82f012edb81af488a0a34a9d16c1c334cbca2afbf40fd1acf8c355` |
| `E3_frozen.json` | `0fc64deef5e52c2db4a4d00ca50a69c56bc2aae2651be5bd8616ca7ad5a9506f` |
| E3 PE | `2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c` |
| Preserved E2 PE | `ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa` |
| Gurobi 13.0.2 DLL | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |
| `argv_freeze.json` | `860f22a5cb58f8d95edb0743cfe2054b424646b722ed8dc94463de5ab86640e0` |
| Final `round130_evidence.py` | `bfb6eb014b5f8e95c696a845a5a7df22bef073188c4b097d28a8e4e85d25b5c3` |
| `qualification/native_qualification.json` | `50da83389d72e12a48d9465fee85cc5073288075d09afea7fda9c32d69382494` |
| `qualification/zero_qualification.json` | `3bc192a365aebcf3717a7850afba036724303a85e8217aa981d3fb663ee36454` |
| `qualification/filename_identity_addendum.json` | `76c74ae2cc6fee31f666718eb748dfcec582fb4a4ef08bd58b5e07c00dc6937d` |

## Scope and independence

The reviewer read source, saved matrices, Start vectors, physical fleets, logs, clocks, manifests and fee receipts. The reviewer performed fresh standard-library arithmetic and direct full-file/row comparisons. The reviewer did not compile, load a solver, call Optimize, run a formal role, modify implementation, change parameters, or restore a historical campaign. The only reviewer-created file is this report. The main user-dirty checkout and Round129 checkout were not modified.

The actual PE/DLL files, all 217 current source-binding entries, the seven bound adapter entries, every group identity and all 24 final commands matched their frozen identities. These identity checks supplement the substantive checks below; hashes alone are not treated as a correctness proof.

## Source and mathematical contracts

The production diff is limited to `include/Round127Research.hpp` and the paid-Start branch of `src/GurobiBaseline.cpp`. `s2-root` is recognized by the M-B and inclusive-root predicates and excluded by the triple-support predicate. Thus the unchanged MD controller and all R128 repairs apply together. Ordinary `p`, `ms2`, full `mb`, and `md-r` retain their previous predicate outcomes. The PS addition only reads actual MIPFocus/Cuts/NumStart and writes a required receipt after the existing complete Start submission; it sets no new parameter and changes no row or objective.

Both the shared factory in `IntervalRowFactory.cpp` and fallback in `CplexBaseline.cpp` use the same narrowly scoped suppression of `interval_no_improver_domain_closure`. The genuine penalty floor, inventory/domain rows, objective cutoff, ordered supply, pair support, C_G and A/B remain. The common triple emitter is disabled for `ms2` and `s2-root`. The reviewer inspected the native pre-LP check before VType relaxation, original integer-type restoration, paid deadline deduction, one submitted MIP Start, forced nonzero two-call chain, and the final `L0` closed/`native_terminal_mip_optimal` requirement. TIME_LIMIT/INTERRUPTED cannot acquire S2R optimal closure merely from a near-closed bound; LP/MIP INFEASIBLE despite its own witness remains a consistency failure.

R125 Appendix A.1, A.3-A.4, A.5.3-A.5.4 and A.6-A.7 were read directly from Git. Together with the R128 inclusive-root contract, they support the required scope argument: nonnegative penalty gives true G <= F; nonnegative ratios give true G <= (n-1)/n; hence every physical F <= U0 point lies in the stated inclusive root. The cutoff complement supplies the U0 floor, giving min(L,U0) by coverage. This is not permission to clip a bound contradicting the legal own witness. Equality of the analytic floor and cutoff excludes strict improvement, not equal-cutoff feasibility; the near-1e-9 distinction and inherited 1e-7 numerical certificate policy remain explicit.

The real PS entry in `main.cpp` clones the original compact options only for its separately paid H, explicitly reapplies the Round83 preset, saves its own H witness, and passes it to the original compact backend. PS uses mode off and the Round112 flag. It does not combine incompatible old mode flags, borrow S2's H, or receive interval rows/cutoff/domain tightening. H/model/Start work consumes its own absolute deadline. A smaller remaining native TimeLimit after paid H is part of that common budget, not a solver-parameter tuning change.

## Zero-Optimize and actual native evidence

The reviewer directly compared complete E2/E3 small S12 and medium R98-C2 model sections and actual native columns/rows/metadata for `p` and `ms2`. They are equal. The added same-byte, renamed S12 input establishes filename independence as well as different output directories. Shared and fallback equality fixtures remove exactly the sole zero-impossible row; every other row, duplicate, column, bound, VType and objective is retained. S12 shared/fallback pair roots have no additional difference. Pair/order rows remain and triple rows are zero. On the actual paid-H S12 qualification, P/PS/reference compact LP files are byte-identical, and S2/S2R actual initial-root LP files are byte-identical.

The six qualification arms are training-only S12: P/PS/S2/S2R at Seed0 and PS/S2R at Seed1. The reviewer read their closed records and independently verified that all six producer seals still match every required file. Seed0 PS is a legitimate TIME_LIMIT open result; it was not replaced because it was slower. Seed1 PS returned native OPTIMAL. Both S2R arms have one L0 LP and one L0 MIP, successful returned OPTIMAL statuses, one immutable root model, restored integer types, one submitted Start, and native-optimal root closure. Their split, partial-MIP, child-restart, reset and model-invalidation counts are zero. The two raw signed gaps remain `1.4710455076283324e-15` and `5.551115123125783e-17`.

Fresh independent full-vector calculations on the actual Seed0 arms gave:

| Check | Columns | Rows | Maximum recomputed row residual |
|---|---:|---:|---:|
| PS original compact Start | 711 | 1539 | `2.220446049250313e-16` |
| S2R pre-LP / submitted / readback Start | 1388 | 2752 | `2.220446049250313e-16` |

Every vector entry, actual VType, bound and integer restriction was checked, with original objective recomputation. PS before/after native matrices agree completely. S2R pre-LP and submitted/readback vectors agree column by column. The reviewer wrote a separate simple LP-expression reader for the S2R residual calculation instead of calling the producing qualification function.

Independent physical replay of the own H gives F=`0.29907089418635313`, G=`0.13023309631835087`, P=`1.1255853191200151`, assigned capacities `[8,12]`, return loads `[2,0]`, and maximum duration `3547.7351804688205 < 3600`. The actual PS and S2R final fleets replay to F=`0.22524870597274982`, return loads `[0,1]`, and maximum duration `3599.9179714294573 < 3600`. Routes, unique service, inventory capacities, all load prefixes, empty departure and unloading on return were checked.

The reviewer also compared all five paid qualification H traces directly, removing only declared time/path/hash metadata. All 25 descent seeds complete without interruption in each arm; all semantic actions, closure/exchange records and capacity-labelled fleets agree, including across Seed0/1. This is stronger than comparing only U0. The inherited R112 empty-vehicle and loaded-return full Start witnesses were read directly from Git and independently rechecked over 1591 columns and 3689 rows each. Their maximum residuals are `4.440892098500626e-16` and `1.942890293094024e-16`; every vehicle-0 route/service/load/flow value is zero in the empty-vehicle witness. R130 does not claim that the general mapper is byte-identical to R112: its documented intervening R120 optional-column branch is absent from PS.

R128's S=0, equal-cutoff, tiny-positive-U0 and normal open-return evidence is inherited with its original three-station MD-R identity. Those are not claimed as new pair-root native runs. New S2R evidence above supplies the pair-only combination's actual full Start and two-call obligation.

## Reader review and resolved findings

The PS adapter verifies raw receipts, actual Seed/settings, complete original matrix, full Start, successful return and logs before projecting the returned-call prerequisite in memory. Original observations, commit files, raw Seed0-only `native_preconditions`, raw global-availability flags and signed bounds are not rewritten. The P-S log view retains the complete Start/matrix evidence when a post-Start fingerprint differs from the cold fingerprint. Native Start submission/readback is not treated as proof of a newly adopted incumbent. This agrees with the [Gurobi 13.0 Start attribute](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/attributes/variable.html#start) and [Gurobi's explanation of the no-new-incumbent message](https://support.gurobi.com/hc/en-us/articles/15185996954897-What-does-User-MIP-start-did-not-produce-a-new-incumbent-solution-mean).

The S2R identity reaches R128's complete-cover gate and its scoped near-closed open-return exception. The AST extraction selects exactly the original `endpoint` function and retains the inherited source/return/coverage/physical/numerical requirements. The interpretation of [OPTIMAL, TIME_LIMIT and INTERRUPTED](https://docs.gurobi.com/projects/optimizer/en/13.0/reference/numericcodes/statuscodes.html) is not broadened.

Three findings were resolved before this acceptance:

1. An initial PS Seed1 adapter incorrectly required the top-level raw strict certificate to be false. The actual sealed Seed1 PS returned OPTIMAL with raw strict certificate true while its journal prerequisite was false. The adapter now preserves the original computed-certificate/raw-certificate equality, including startup-zero, and only projects the verified returned-call journal scope. Its successful read-only recovery used the same sealed producer; the native solve was not repeated. The initial failed audit, subsequent exclusive-write recovery failure and their fees remain retained.
2. The initial bridge omitted an input-basename variation. The zero-Optimize filename addendum now supplies it; no formal role was screened and no native solve was added for that correction.
3. `E3_frozen.json` initially retained a build-time pending flag beside qualification-complete=true. Final pending=false and the rebound execution SHA above were checked. `E3_build.json` may retain its honest earlier build-time state.

One reviewer scratch arithmetic attempt exited before checking vectors because a local variable shadowed its JSON-reader name. It wrote no files or source and called no solver. The corrected read-only calculation completed all checks reported above.

## Prior evidence, argv and budget

The reviewer read the necessary Round129 goal, candidate decision, input manifest, arms/pairs, mechanism costs, actual differences and E2 identity. All five prior selection conditions passed; this review does not reopen that decision. The four-new-input per-Seed P/MB/MS2 certificate counts are 1/2/2; UC-C20-U retains both material savings. UC-C15-S and UC-B30-S remain open; B30's Seed1 adverse MS2 endpoint remains visible. The B20 record has own H already at the eventual objective `0.5773330699702928`, yet H is not its optimality proof; both methods/Seeds naturally execute three splits. Existing P-S mixed/reverse results from R112-R115 and the old R128 no-split control scope remain identifiable.

Every one of the 24 frozen commands was checked against the six prescribed role/Seed/order groups. P has exactly `p`, PS has only the paid Round112 entry with mode off, S2 exactly `ms2`, and S2R exactly `s2-root`. No overriding Round128 flag or P tuning file is present. The three source input hashes, cap=1200, native offset=6, reserve=30, hard-stop=1198, single threads, actual Seed and fixed presets agree. All formal arm destinations were still unstarted at this review. The run entry requires ACCEPT and the exact execution-binding SHA, checks bound adapters, reserves the remaining complete formal obligation plus 2400 seconds, and does not automatically retry an existing fee label.

At the reviewed closed-ledger snapshot, conservative paid outer time is `1156.0808230000548` seconds, remaining `38443.919176999945`. Build plus qualification receipts total `256.0808230000548` seconds, below 3600; there are no unclosed fee records. Nested H/LP/MIP seconds are not added. The remaining nominal formal obligation is 28800 seconds, so the stated reservation is covered. These are an as-of ledger calculation, not a prediction of final cost.

The remaining formal obligations are per-arm: pay and check its own complete H, verify actual own initial roots and semantic differences, preserve every open/reverse/no-split result and signed gap, and perform the separate delivery review after all 30 typed comparisons exist. No formal claim about backend or outer-control benefit is established by this preformal qualification.

## Principal first-hand material

- Production: `include/Round127Research.hpp`; `src/main.cpp`; `src/Round112CompactStart.inc`; `src/MipStartMapping.cpp`; `src/GurobiBaseline.cpp`; `src/PaperExternalGiniTree.cpp`; `src/CplexBaseline.cpp`; `src/IntervalRowFactory.cpp`; `src/Evaluator.cpp`; `src/Result.cpp`.
- Reader/runner: `scripts/round130_evidence.py`, `round130_campaign.py`, `round130_formal.py`, `round130_common.py`, `round130_native.py`, `round130_qualify.py`; the relevant R112/114/115/120/122/127/128 adapters; `round107_reader.py`, `round108_reader.py`, `round109_seed_scope.py`, `round109_seed_audit.py`, `round118_call_logs.py`, `read_round116.py`, `read_round118.py`, and `round114_claims.py`.
- Contracts/history: R125 mathematical appendix sections above; R128 `md_root_contract.md` and final preformal review; R112/R113 model-contract small tables; R112-R115 final reports and the two inherited full Start witnesses; R129 source material listed above.
- Current evidence: `qualification/zero_qualification.json`, `filename_identity_addendum.json`, `inherited_contracts.json`, `native_qualification.json`; actual `native_S12_S0` and `native_S12_S1` producers/Starts/models/logs/seals; final frozen source/PE/argv/binding and fee records.

This is a bounded independent preformal acceptance. There is no remaining required correction to the reviewed implementation or fixed plan.
