# Round 22 final report

## Outcome

Round 22 adopts the engineering-exact CPLEX certificate policy, replaces sparse root-to-final progress with dense supported read-only CPLEX trajectories, and completes the frozen serial S0/S1/plain protocol. All 81 official rows completed. The single stable paper mainline remains **S0/F0 `round20-current`**; S1/F3 remains an exact optional research variant.

The production executable is bound to source commit `71c5c420e087ae9783e5382fa821012b02ddd32c` and SHA-256 `b3fecef84dce8d6a2323d25a7877d5f16d14aa5f1fb644ae642bf636a229ee62`. The Round 22 branch is based on live `main` commit `f123418f9ae50c7bd5d09616757cd56d18cb3906`.

## Validation inventory

- Stage 0: 11/11 mechanical gates passed. Seven C++ executables passed 86 test groups; Round 20 Python regression passed 6 groups; Round 22 runner integrity passed 5 groups; the static audit passed 21 checks; and the migration audit covered 13 Round 21 status-101 rows.
- Stage 1: 9/9 official live trajectory rows and all 6 matched logging-on/off overhead pairs completed.
- Stage 2: 24/24 existing-suite 900-second rows completed.
- Stage 3: 24/24 existing-suite 1,800-second rows completed.
- Stage 4: 18/18 preregistered held-out 900-second rows completed.
- Stage 5: all 6 preregistered conditional 3,600-second rows completed. The selector chose existing `high_imbalance_seed3202` and held-out `high_imbalance_seed4201`; V12_M2 did not meet its implementation-issue trigger.
- Official solver outcomes: 11 status 101, 2 status 103, 25 status 107, and 43 status 108. These map to 11 engineering-exact certificates, 2 native infeasible outcomes, and 68 valid time-limit bound outcomes. There were no execution failures or interrupted official rows and no status-102 outcomes.

## Required questions

### 1. What is the exact Round 22 engineering certificate definition?

A row is strict only when exact-zero relative and absolute CPLEX MIP gaps were requested, successfully set, successfully read back, and effectively equal zero; native status is exactly 101 with consistent `integer optimal solution` text; the versioned complete-original-model gate passes; the independently reconstructed solution passes the original feasibility verifier; and the one-environment/one-problem/one-read/one-`CPXmipopt` lifecycle and native finalization succeed. The policy identifier is `round22-engineering-exact-v1`; the model gate is `round22-engineering-model-v1`.

### 2. Why is bitwise equality no longer a certificate gate?

CPLEX status 101 on the audited complete model, under exact-zero requested/read-back gaps, establishes the commercial-solver engineering certificate. `CPXgetobjval`, `CPXgetbestobjval`, and an independent floating reconstruction are separate computations and can differ in their final binary digits. Requiring bitwise equality added an unrelated floating representation test, not an additional MIP proof. Signed residuals remain fully preserved and classified diagnostically.

### 3. Why do status 102 and time limits remain non-strict?

Status 102 is native tolerance-optimal only; no displayed zero or user epsilon can turn it into status 101. Status 107 and 108 are time-limit outcomes and retain only their valid native lower-bound evidence. Status 115 remains rejected. Round 22 changes the status-101 mapping-residual rule only; it does not promote any other native status.

### 4. Were relative and absolute gaps zero and read back in every official run?

Yes. All 81 official raw JSONs record zero requested and effective relative gaps, zero requested and effective absolute gaps, successful setters/getters, and `native_mip_strict_gap_parameters_valid=true`.

### 5. Did every strict row use status 101?

Yes. All 11 strict rows have native status 101 and consistent text; zero non-101 rows are strict.

### 6. Did every strict row pass model correctness and independent feasibility verification?

Yes. All 11 did. More broadly, all 81 official rows passed the versioned model gate, lifecycle checks, and independent feasibility verification of the retained same-run UB.

### 7. Which Round 21 status-101 rejections become strict under the corrected semantics?

Six historical rejections were caused only by the old equality rule: Stage-1 V12_M2/F0; Stage-2 V12_M1/F3; Stage-2 V12_M2/F0 and F3; and Stage-4 V12_M2/F0 and F3. Their residuals range from `-3.3306690738754696e-16` to `5.773159728050814e-15`. The no-rerun audit classifies them as engineering-exact candidates, not retroactively strict, because their old executable has no Round 22 versioned model-correctness binding. Fresh Round 22 status-101 reruns with the new gate are strict. No historical JSON was changed.

### 8. Did any historical status-102 row change class incorrectly?

No. The migration and regression gates retain every historical status-102 row as tolerance-only. There were no status-102 rows in the 81 official Round 22 runs.

### 9. Are native objective, native LB, and recomputed objective still preserved separately?

Yes. Their availability flags, return codes, round-trip-safe values, three signed pairwise residuals, inversion flags, native gaps, independently verified UB gaps, parameter records, and lifecycle evidence remain separate. No native lower bound is replaced by an incumbent and no top-level gap is forced to zero from status text.

### 10. How large are the mapping residuals?

The largest absolute official residual is `1.1661410836971697e-08`. Two plain V12_M2 time-limit rows are explicit warnings: `1.1661410836971697e-08` at 900 seconds and `4.13899103879345e-09` at 1,800 seconds. Strict-row residuals are at most `5.773159728050814e-15`; the selected Stage-5 strict S0 row has `6.661338147750939e-16`.

### 11. Did any mapping residual indicate a genuine model anomaly?

No confirmed model anomaly was found. The two larger residuals are visible warning diagnostics on non-strict plain time-limit incumbents; both rows pass complete-model and independent feasibility audits, and neither affects a native lower bound or upgrades a certificate. They remain flagged for numerical follow-up rather than hidden or treated as proof failure.

### 12. Does the new callback produce fresh observations throughout the tree?

Yes. Tailored uses a documented read-only snapshot at the beginning of the RELAXATION context because combined GLOBAL/LOCAL progress did not provide a dense Tailored stream. Plain uses supported GLOBAL/LOCAL progress. Static checks prove Tailored capture precedes any cut, branch, candidate, or other mutation. The Stage-1 native-horizon gate requires at least 20 native events, at least 8 eligible common checkpoints, and at least 80% freshness; every live row passed.

### 13. How many scheduled checkpoints are fresh, stale, or unavailable?

Across all 81 official rows there are 1,315 fresh, 188 explicitly stale, and 0 not-observed checkpoints, plus 81 solver-final rows. That is 87.49% fresh among 1,503 scheduled checkpoints. By arm, plain has 492 fresh/9 stale, S0 410/91, and S1 413/88. Stale rows retain observation age and source; no future event fills an earlier checkpoint.

### 14. Does plain CPLEX now have an authoritative intermediate trajectory?

Yes. Plain contributes 1,129,330 of the 1,667,782 official raw events, uses the same full-precision schema and checkpoint extractor, and has an explicit solver-final endpoint matched to JSON in every row. Rounded console output is not used as the authoritative bound source.

### 15. What is the measured instrumentation overhead?

All six matched pairs completed. Dense callback instrumentation itself ranges from 0.0178189% to 1.5813108% of solver wall time, with median 0.0231251%; the maximum retained buffer is 15,728,640 bytes. The maximum matched dense-on minus dense-off delta is 0.3431689% in runner wall time and 0.3432550% in solver runtime. No API violation or search mutation occurred, and all official arms ran with dense collection enabled.

### 16. At what times do F0 and F3 overtake one another, if observed?

The common-fresh analysis observes 47 leader-change intervals and never interpolates an exact crossing. The full list is in `flow_overtake_intervals.csv`. In the selected existing 3,600-second case, S1 moves ahead in `(2,10]` seconds and S0 retakes the lead in `(15,20]` seconds before S0 certifies. In the selected held-out case, S1 moves ahead in `(2,15]` seconds and finishes with the better lower bound. Frequent early and later reversals across the fixed grids confirm that neither flow dominates pointwise.

### 17. Does dense trajectory evidence change the Round 21 interpretation?

It makes the interpretation substantially better grounded but does not justify F3 promotion. The old sparse evidence could hide alternating leaders and long stalls; the dense stream shows mixed AUC, 47 observed crossings, and very long sibling delays. It supports a common scheduling bottleneck rather than a simple claim that one flow is uniformly stronger.

Raw native values are not repaired or clamped. Supported callback snapshots contain native lower-bound and occasional incumbent reversals across contexts: 65 rows have at least one lower-bound reversal, with 9,510 negative steps, while timestamps and node counters remain structurally consistent. These reversals are retained as diagnostics under the documented monotonicity erratum, not silently normalized into a false monotone trajectory. All 81 structural audits still pass because endpoint identity, timestamp ordering, source integrity, serialization, and finalization are the authoritative integrity checks.

### 18. How many existing-suite instances does S1 improve or regress relative to S0?

At 900 seconds S1 improves 3 and regresses 5. At 1,800 seconds it again improves 3 and regresses 5. The selected existing 3,600-second comparison is a regression. Across existing horizon comparisons, the total is 6 improvements and 11 regressions.

### 19. How many held-out instances does S1 improve or regress relative to S0?

At 900 seconds S1 improves 2, regresses 3, and has 1 unavailable pair. On the selected 3,600-second held-out case it improves. Across held-out horizon comparisons, the total is 3 improvements, 3 regressions, and 1 unavailable.

### 20. Which method has better area-under-bound-progress performance?

Neither is uniformly better. Of 24 production-horizon S0/S1 AUC comparisons, S0 wins 14 and S1 wins 10. S1's mean advantage is small and positive on the existing matrices (`+0.0006179` at 900 seconds and `+0.0014260` at 1,800 seconds), but negative on the held-out 900-second matrix (`-0.0050715`). S0 wins the selected existing long run by `0.0047473`; S1 wins the selected held-out long run by `0.0041488`.

### 21. Which method has more strict certificates?

Across all official rows, S0 has 5, S1 has 4, and plain has 2. At each full existing matrix S0 and S1 tie 2-2; the additional S0 certificate comes from the preregistered existing 3,600-second case. Neither Tailored method certifies a held-out row.

### 22. Which method reaches strict certificates sooner?

S0 is faster in every same-instance S0/S1 strict pair. At 900 seconds, V12_M1 takes 124.1571 seconds for S0 versus 128.0750 for S1, and V12_M2 takes 280.4388 versus 741.9025. At 1,800 seconds, V12_M1 takes 122.7270 versus 129.3034, and V12_M2 281.0980 versus 731.6978. Plain certifies only V12_M1, at about 619-620 seconds. S0 alone certifies the selected existing long-run case at 3,285.8835 seconds.

### 23. Does either Tailored method consistently outperform plain CPLEX?

Not in every row and every metric, so no uniform dominance claim is made. Tailored has greater strict coverage and typically much stronger V20 lower-bound closure, while plain often supplies a native incumbent and exposes a much larger event stream. The honest conclusion is that Tailored is the stronger exact paper line for these matrices, not that it pointwise dominates plain CPLEX under every observable.

### 24. Is F3 now sufficiently stable to become the single default?

No. Existing regressions exceed improvements, held-out regressions do not fall below improvements, there are more than one material regression, and S1 has one fewer total strict certificate. This fails the frozen broad-non-regression rule. F3 remains research-only.

### 25. What exact production settings define the current stable mainline?

One persistent global Gini tree; F0 `round20-current`; parent-copy child estimates; full inherited row pack; deferred child rows; native MIP start off; one CPLEX environment/problem/model read/`CPXmipopt`; one native deadline with reserve; one thread; presolve on; traditional search; native best-bound selection; default cuts, probing, and heuristics; exact-zero relative and absolute gaps with readback; and dense read-only progress enabled. The same sealed resolution is used on every instance.

### 26. Does any source path select algorithms by V, M, name, seed, or instance family?

No. The 21-check static audit covers numeric V/M thresholds near dispatch, names, seeds, paths, labels, toy-oracle reachability, flow resolution, plain-to-Tailored information channels, production option identity, and callback mutation ordering. S0 is always F0 and S1 is always F3; external toy enumeration is test-only.

### 27. What is the strongest remaining convergence bottleneck?

Gini-sibling starvation is the strongest common measured signal. Production Tailored traces contain 11,422 observed sibling first-process delays; 443 exceed 300 seconds, 66 exceed 900 seconds, and the maximum is 2,940.0933434 seconds on Stage-5 `high_imbalance_seed3202`/S0. Large residual queues and late bound stagnation coexist with these delays. The evidence is stronger for a scheduling bottleneck than for an F0-versus-F3-only formulation explanation.

### 28. What should the next round address?

Address a common, starvation-resistant Gini-sibling scheduling mechanism first. Preregister one scheduling rule, apply it identically to F0 and F3, retain parent-copy/full-pack/deferred semantics, and rerun a small discriminating subset before any full matrix. Basis reuse and new formulation cuts should be secondary experiments after scheduling is isolated; an instance dispatcher is not an acceptable response.

## Separate conclusions

**Certificate correctness.** The policy now follows engineering-exact commercial-MIP semantics without weakening any native-status, zero-gap, model, verifier, or lifecycle gate. Eleven fresh rows are strict, no non-101 row is strict, and historical evidence remains immutable.

**Trajectory quality.** All 81 trajectories have strict timestamps, unmodified full-precision values, solver-final records, matching JSON endpoints, canonical non-future checkpoints, and zero structural errors. Freshness is explicit rather than fabricated. Native context-to-context reversals are visible diagnostics and covered by retained errata.

**Existing-suite performance.** S1 is mixed and regresses more often than it improves at both full horizons. S0 is faster on every shared strict case and uniquely closes the selected existing long run.

**Held-out performance.** S1 improves two and regresses three at 900 seconds, then wins the selected long-run lower-bound comparison. This is promising but not robust enough for promotion.

**Stable-mainline selection.** S0/F0 remains the sole stable mainline. S1/F3 is exact and valid but research-only. No portfolio or dispatcher is introduced.

**Remaining scientific risk.** Dense read-only snapshots expose native cross-context nonmonotonicity and severe sibling delays. Conclusions about exact crossing times or a globally monotone callback LB would be invalid; conclusions use observed intervals, raw values, final native bounds, and structural integrity instead.

## Evidence and publication notes

The package retains every official command, environment/provenance record, raw JSON, native and console log, complete native run artifacts, raw dense stream, canonical trajectory, verifier/certificate result, and every excluded or superseded attempt. Four corrected pre-production evidence generations are retained under `attempts/` with explicit freshness, integrity, monotonicity, and pre-refreeze errata. Large text streams and models are stored as deterministic gzip files; `evidence_package_manifest.csv` preserves original and stored paths, byte counts, SHA-256 values, compression status, and verified round-trip identity. The final package contains 2,971 stored artifacts, including 398 gzip archives, totaling 1,038,035,307 bytes. Its largest artifact is the 21,459,528-byte compressed pre-monotonicity V12_M1 plain trajectory, safely below GitHub's 100 MB hard limit.
