# Round127 preformal source review

Reviewed by a separate collaborating executor before formal evaluation. This is a focused source review, not third-party replication. The review ran no builds, native Optimize calls, or performance experiments and inspected no core performance outcomes.

Review basis: source commit `ea5491743` and the current added `scripts/round127_export.cpp`, `scripts/round127_qualify.py`, `scripts/round127_evidence.py`, and `scripts/round127_campaign.py`. The executor's reported S12 zero-Optimize matrix checks are supporting context; this reviewer did not rerun them.

**Latest source verdict:** the three initial findings below were corrected and the revised source was independently reread before E1 freeze. No unresolved source-level admission blocker was found in the reviewed paths. Native and complete-reader qualification remains pending; this verdict alone does not admit formal experiments.

**Subsequent mathematical boundary disposition:** [preformal_cutoff_boundary_review.md](preformal_cutoff_boundary_review.md) identifies the inherited numerical penalty-closure exception that prevents MD's stronger inclusive-root/own-U0-Start obligation. MD qualification is blocked under the unchanged row pack. This supersedes the earlier source-only disposition for MD admission; it does not establish a blanket block on the other retained numerical modes.

## Initial findings, subsequently resolved

1. **Optional root-point observation can terminate an otherwise valid run.** `src/GurobiBaseline.cpp:3611` writes the actual first L0 optimal LP point, but the new name-read and write failures at lines 3622 and 3625 throw exceptions. Goal section 9 explicitly treats an unavailable point as unknown and says this diagnostic adds no formal admission condition. Retain the solver outcome when this optional observation fails, record unavailable/partial status when possible, and ensure a partial file is never accepted as a complete point. This is an observation-path issue, not a defect in the mathematical model.

2. **The shared group builder applies a selected PRM to every E1 arm.** In `scripts/round127_campaign.py:35`, any non-null `config` is appended to every method in `methods`; the launch record likewise gives every arm the same configuration. In a core group containing P, PT, and M-B modes, this would tune P and send the P-only flag into the M-B validator. Bind the selected configuration to PT alone in mixed evaluation groups, retain q0 for P, and allow explicit configuration injection for the separately declared training P arm. The supplied smoke groups avoid this combination, but the builder is not ready to construct the required mixed core groups as written.

3. **Configured family labels still claim deleted rows are active.** `src/IntervalRowFactory.cpp:415` through `:446` registers support/transfer and C_G families with the original option flags. `registerFamily` adds these to `active_families`, which the writer copies to `enabled_families`. The actual MR/MG emissions are correctly masked, but these legacy labels will still list their deleted packs. Apply the emission masks to the registry's row-active fields, or explicitly label the legacy values as configured inherited options and derive exposure from actual rows. Keep the low-Gini option enabled for its retained domain calculation. This finding affects mechanism reporting; it does not invalidate the inspected deletion matrices.

## Accepted source properties

- The new control state defaults to `off`, uses no `SolveOptions`/`SolveResult` ABI additions, and introduces no instance-name, size, Seed, or time based mode selection. The P/PT and M-B modes reuse the original writers and backend paths.
- C_R gates cover exactly the static ordered supply rows at `src/CplexBaseline.cpp:1729` and pair/triple support block at `:2050`. MS2 gates the existing triple loop at `:2099`. The writer's per-model shared 50,000 candidate budget and vehicle/pairs/triples order are preserved. Singleton reachability, global handling, conservation, and other transfer rows remain untouched.
- C_G uses semantic emission gates in both entry paths: the shared factory at `src/IntervalRowFactory.cpp:613`, `:654`, `:720`, and `:769`; and fallback writer at `src/CplexBaseline.cpp:2928`, `:2942`, `:3273`, and the existing `add_sp_product_estimator` gate. Dedicated `r_min`, `r_max`, and `W_SP` creation is masked. The original y/e/S/P derived domains are calculated with unchanged option flags, and direct Gini cap/floor, exact state products, required movement, penalty closure, and deviation bounds are retained.
- Complete Start mapping enumerates actual model columns in `src/MipStartMapping.cpp`; absence of W_SP or the centering extrema therefore creates no artificial missing-column requirement. Existing remaining-row, bound, type, and objective checks are preserved.
- MD checks the complete own-U0 root domain and the singleton initial interval. It retains the original root LP, bypasses the LP-only pruning branch, NEXT, and adaptive child LP/split gates, then reaches the common one-call terminal MIP with no native bound target. The terminal request retains U0 and own Start. Root LP/MIP infeasibility is treated as a consistency fault.
- MD's unchanged `ensureArtifact` epoch invalidation is dormant on its admitted path: the root LP does not improve the outer physical incumbent; candidate/closure/proof observers are excluded by the inherited M-B isolation validators and new Round127 validator; the sole terminal MIP hands off an improved witness only after return, then closes or stops open. No path returns to a new root build. The inherited backend restores original integer VTypes after the retained root LP. Native smoke must still confirm one LP, one MIP, zero children/targets/splits, and one root artifact for a nonzero admitted case.
- P parameter injection occurs after preset processing and before model import. The subsequent authoritative model-environment receipt reads MIPFocus/Cuts and confirms zero Start count. The cold compact model construction remains unchanged. No requested gap or numerical tolerance is relaxed.
- The inherited Seed0-only raw journal prerequisite is intentionally unchanged. The added `round127_evidence.py` extends the existing R122 actual-Seed returned-model proof to Seeds 2/3, checks the actual settings and source tree, and preserves the raw false prerequisite and unavailable callback-global claims. It recovers only successfully returned calls after complete model/Start/type/physical/scope checks. This resolves the earlier source-level Seed warning conditional on the complete reader/native smoke passing; it is not an online callback promotion.
- Saving the actual root LP point uses the original model's native names/X after the existing optimal LP call and introduces no extra Optimize. The saved W-free MG point must later be tested by an interval intersection for W_SP extension, not by choosing an arbitrary W value.

## Remaining qualification boundaries

The source review does not complete the full qualification. Required native smoke, full H completion/action identity, legal witness/edge-case mapping, final parameter readback, and E1 seal remain the implementing executor's recorded checks. The existing support pair/triple counters combine cover and conditional branches; the actual row classifier or equivalent independent reconstruction must supply the requested cover/conditional exposure split. Raw scoped bounds and signed gaps must remain available even when cutoff-complement/global reporting uses a smaller qualified bound.

Verdict at this review snapshot: **targeted changes and qualification still pending**. No CR/CG deletion or MD full-root coverage defect was found on the admitted frozen M-B path. Resolve findings 1 and 2 before freezing E1 or constructing mixed core groups; resolve finding 3 before reporting mechanism exposure. Normal positive, negative, and open results do not authorize changing these modes after the final seal.

## Correction review before E1 freeze

The implementing executor addressed all three findings before starting E1 smoke or training. This reviewer independently inspected the resulting source changes, without building or calling Optimize:

- Root-point capture catches optional I/O/name failures and records a separate `complete` status when available. An incomplete or absent status must make the explanatory point unknown. The solver's mathematical outcome is preserved.
- `prepare_group` now binds the selected PRM only to PT, or to the explicitly named training group. Its per-arm configuration record follows that choice. P in a mixed core group retains q0, and M-B modes receive no P-only parameter argument.
- The factory's row registry now applies C_R/C_G emission masks while leaving all domain flags and derivation unchanged. Removed packs are no longer reported as active rows by that registry.
- MD additionally rejects an unexpected static-root epoch change before the inherited artifact invalidation/rebuild path. This is a fail-closed guard; the admitted one-LP/one-MIP path still has no such epoch transition before its MIP call.

The executor reported an E0 S12 Seed1 P/MB smoke and full reader pass. That is the executor's qualification result, not a native run independently performed by this reviewer, and its elapsed time supplies no performance conclusion.

Reviewed corrected source SHA256 identities:

| Path | SHA256 |
|---|---|
| `include/Round127Research.hpp` | `72ed37206d7387c4bc9ea8ff4abc4eb6bdd4669842424ee4592ea3dd6bbd562b` |
| `src/CplexBaseline.cpp` | `07a6897827acc9a86323fa2a89f4a0cbaf8124f27dab54ad8d3f03afc8367186` |
| `src/IntervalRowFactory.cpp` | `5e2390770f07073233c4e32572769268f6240d0c0e30300a57a9beaa54f33660` |
| `src/PaperExternalGiniTree.cpp` | `776965ae7e023bbc3745d5984737aeb6e637aa12819dfc7aadd5673ce89057c1` |
| `src/GurobiBaseline.cpp` | `2146269f7bb085bfad2ca2bce73cff0460f8f2354a5226da59b8524ebfd1b4ab` |
| `src/main.cpp` | `a520f5ccc2fab9ad990827db3c8a8a7fd1db938a2cbea81e2c8ed1038600664e` |
| `scripts/round127_campaign.py` | `e6e2166f5bf811b9ad3d003b824d968a8a5af534dbb1f75025239d081474b9d8` |
| `scripts/round127_evidence.py` | `94f961eed9d0397c370ee8c44a8162abf861388cf2a5a1eb1237b0c4296ab4c8` |

Current disposition: **source review passed; native/full-reader qualification pending**. No performance inference, third-party replication claim, or rational proof of every native matrix is made.

## Finite gate evidence review

The separate reviewer subsequently read `qualification/admission_summary.json`, `qualification/zero_optimize.json`, all 52 compact boundary-vector records, `review/performance_admission.json`, the E0/E1/PT smoke qualification fields, the actual PT parameter receipt, and the S12 MD two-call ledger. No new native call was requested or run by this reviewer.

The evidence supports **qualified methods P, PT, MB, MR, MG, MS2; blocked method MD**. Exact duplicate-preserving deletion checks cover S12 root/left/right and C2 root, with further C2 MG child checks. The actual same-H S12 root differences have the prescribed families and preserve remaining objective/types/bounds/rows. Complete H actions, final inventory, and fleet agree with the retained E0 control in the finite replay. All nine E0/E1/PT smoke arms have successful complete-reader qualification and no source reduction. PT's Seed2 q4 receipt reads MIPFocus=2, Cuts=2, NumStart=0 from the model environment. MD's functional S12 ledger is exactly root LP then root MIP on the same L0 model SHA with original VTypes restored; this does not override its mathematical block.

There are 48 clean boundary records and four preserved violations, all on the expected T60 equal-cutoff impossible row; the longer S=0, shared midpoint, loaded-return, homogeneous/heterogeneous, and cumulative-pickup examples are clean. The expected closure exception remains disclosed and production/closure are unchanged.

Artifact identities checked at this gate: admission summary `08b4b81982a72a9b9d7761ec8e246a6dba8200983f72917e64b765e7ef716eb3`, zero-Optimize summary `aaf052b8279d0b300804bcdceac37fb14bd19ca50e99239e8edda7ddcab6665b`, and boundary vectors `e97faadc8760ce4d414f221b23c3ee497f1d3851e73d60dfec4d7a61244b3e92`. The actual E1 PE hashes to `d668236e9396b2e12f02bb65d9819b98762d2a35aad1b186d352d234dae756c9`; the DLL matches the original frozen identity.

The revised reconstruction source correctly reconciles each physical representation-labelled M-B arm's own call IDs against the saved witnesses separately; cross-arm witnesses can refute a claim but supply no free bound or solution. Aggregate claim labels are changed to actual methods only for reporting. At this read, the cached `smoke_E1/reconstructed.json` still used the older aggregate labels and needed read-only regeneration, and the frozen manifest still inherited `final_qualification_pending=true`. These are metadata closeouts, with no new native run or model change required. Refresh the review/frozen/admission digest chain after this note is saved. No qualification runtime is a formal performance result.
