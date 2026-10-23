# Round132 independent internal review: preformal mathematics and identity

Review date: 2026-10-23 (Asia/Shanghai). Reviewer: the separate `independent_review` executor requested by G2. This is an internal review, not external reproduction.

Scope: read the user-supplied v2 task, the current C++ writer/factory/preset/Start source, R131 model and method manifests, R130 identity/argv/qualification materials, and one actual saved R130 S2R LP directly from its existing ZIP. No Optimize, H, compilation, native model construction, production edit, experiment-plan edit, or source edit was performed by this reviewer. Only this review file was created. Findings below distinguish analytic conclusions from finite matrix checks and qualification still required.

## Decision

The B3 ideal root and conditional full-interval arguments are sound for the stated canonical model. The active preset has the required H uses in the source examined. The B4 general lower/upper projection is sound, but its two-cutoff simplification requires retention of the P domain implied by MC. Actual saved coefficients require their own numerical treatment; neither argument warrants a strict rational-equivalence claim for the unmodified floating matrix.

No correctness defect in frozen S2 was established in this review. Three implementation/reporting traps must be addressed before C admission: do not discard MC-implied P restrictions; do not apply B3 to dormant extra H usages or node matrices; do not identify active model content from default-valued top-level result fields.

## B3: conditions and located source evidence

| Condition | Evidence examined | Assessment |
| --- | --- | --- |
| H continuous, no objective coefficient | `src/CplexBaseline.cpp:979-984`, `1112-1117` | Satisfied in this writer. |
| H box is c_i+c_j with c_i=C_i/D_i and r_i<=c_i | `src/CplexBaseline.cpp:938-940`, `981-983` | Satisfied as the ideal expression. Actual addition is rounded. |
| H absolute-value lower rows retained | `src/CplexBaseline.cpp:2330-2335` | Two signed rows for every pair. |
| Original epigraph uses H only through the full sum | `src/CplexBaseline.cpp:3150-3155` | Full sum with uniform coefficient -1. |
| Cap/floor retained | `src/IntervalRowFactory.cpp:561-575` | Full H sums, upper/lower respectively. |
| Three deletion families | `src/IntervalRowFactory.cpp:613-625`, `654-705` | `gini_pairwise_spread`, `low_gini_centering_band`, `variable_s_low_gini_centering`. Delete only these emissions. |
| Scalar and SP retained H usages | `src/IntervalRowFactory.cpp:720-733`, `798-808` | Uniform full-sum upper rows. |
| No additional active H couplings | `src/PaperK1AmSf.cpp:85-101` | Local/subset H centering, GS, disaggregated SP, and bucket extras are off in the canonical preset. |
| Shared factory is actually selected | `src/CplexBaseline.cpp:4554-4557`, `5211`, `6842` | Canonical interval exports and fixed-interval paths explicitly select it. |
| n=1 family skip | `src/IntervalRowFactory.cpp:613`, `654-655` | Both blocks require V>1. |

Extra H usages exist in source and invalidate an unrestricted source-wide theorem: local station sums at `src/CplexBaseline.cpp:2608-2632`, cross-subset sums at `2634-2708`, local-q rows at `2710-2724`, static segment disaggregation near `1464`, and optional GS rows near `3196`. They are dormant under the checked preset, not mathematically irrelevant. Record their actual resolved off status; a user may explicitly change options after a preset. Do not extend this review to a native node matrix containing local cuts.

Root proof: in the model without the three families, replace every H_ij by d_ij=|r_i-r_j|. This decreases every retained H sum and preserves all other variables; the alpha=0 floor remains nonnegativity. The retained total cap implies A<=n beta S; triangle inequality gives (n-1)d_ij<=A. Consequently the H-spread and variable-S rows hold, and S<=Sbar implies fixed centering. This preserves the complete non-H projection and objective, including remaining integrality domains. The argument also covers S=0; n=1 has no deleted family.

For alpha>0, H=d alone can violate the floor. The task's capacity/interpolation extension is valid: f(c)=sum min(c_i+c_j,t) is concave on the nonnegative C-simplex; a convex decomposition into C e_i gives f(c)>=(n-1)min(C,t). Hence the clipped box has capacity at least T*=max(A,n alpha S) after using the retained cap and the original H box. Interpolating from d to the clipped upper bounds realizes that total. The C=0, S=0, and zero-denominator interpolation cases are closed as stated. Retained H total upper bounds, including epigraph/scalar/SP with the other variables fixed, remain satisfied. This is an ideal algebraic result with the precise H-use conditions above.

Allocated r_min/r_max have only bounds in the shared path (`src/CplexBaseline.cpp:933-935`; factory `659-665`). A candidate that only deletes rows should keep these columns and bounds. Their unused status does not authorize broad removal of other model objects or a different domain generator.

## Finite check of an actual frozen S2R matrix

Carrier read in memory without extraction:

- ZIP: `E:/codes/ExactEBRP-work/worktrees/round130/results/unified_exact_round130/artifacts/qualification_closed_fees.zip`.
- Member: `results/unified_exact_round130/qualification/native_S12_S0/raw/04_S12_S0_R1_S2R/external/models/L0_epoch_0_generation_1.lp`.
- Member SHA256: `c10d3aef0eac8d501b32be9a349cd9c7a45483debd545f2a6405ff9d42fae7f2` (matches the saved model contract).
- Member size: 283657 bytes; 2752 named rows, 1388 columns in the saved contract.
- 66 H bounds; 198 single-H rows (132 signed absolute lower rows and 66 spread rows); five rows contain all 66 H columns with uniform full-sum coefficient. No partial multi-H sum was found. Neither H nor W appears in the objective. W appears in exactly five constraint rows and its own box.

This checks one saved actual root and corroborates the source audit. It does not independently qualify every future root, interval, export, or Start.

Exact decimal parsing of the serialized H boxes and serialized r upper bounds found 41 of 66 H upper bounds unequal to the exact sum of the two serialized r upper bounds. Examples of U_ij-(c_i+c_j): h_10_11 = -1e-16, h_1_10 = +2e-16, h_1_11 = -3e-16, h_1_12 = -2e-16. These are exact comparisons of finite decimal coefficients, not counterexamples to projection equivalence. They establish that literal additivity cannot simply be asserted for this actual matrix.

The writer uses `max_digits10` at `src/CplexBaseline.cpp:224-226,1110`, but decimal round-trip precision does not undo binary additions/multiplications. The factory also merges and removes coefficients with 1e-14 tests (`src/IntervalRowFactory.cpp:35-42`); variable-S rows merge the ratio-difference and common-S coefficients. Fixed centering computes its bound by floating sum/product/division (`657-658`). These details can produce inward rounding. Keep the ideal theorem separate from actual-matrix residual checks and any explicitly documented outward research correction. Frozen D assets must stay unchanged.

## B4: W domain, source usage and complete elimination

W is declared continuous at `src/CplexBaseline.cpp:998-1009`, with lower bound max(0,s_l p_l) and upper bound max(lower,s_u p_u). Objective construction at `1112-1117` excludes W. In the active shared path it occurs in the four MC rows and SP cutoff only (`src/IntervalRowFactory.cpp:770-809`). The fallback has the same role (`src/CplexBaseline.cpp:3289-3329`). The existing Start mapper assigns physical S*P at `src/MipStartMapping.cpp:240-241`.

The domain caveat is real in the current implementation:

1. Domain extrema p_l,p_u are computed from tightened inventory ranges (`src/IntervalRowFactory.cpp:523-540`; fallback `src/CplexBaseline.cpp:640-660`).
2. Native e_i still has its original capacity-based upper bound (`src/CplexBaseline.cpp:940`). Budget rows may additionally limit individual e, but they do not in general equal tightened-domain e maxima (`src/IntervalRowFactory.cpp:755-766`).
3. VD-P does not equate e with the state penalty mixture: that equation is emitted only for VD-J (`src/CplexBaseline.cpp:3081-3088`). Therefore P here must remain the native epigraph expression, not P_true.

For lambda>0, the proposed general projection with all L_j<=U_k (nine compatibility rows) and all Hsum+n lambda L_j<=ncS (three cutoff rows) is necessary and sufficient. Choose W=max_j L_j for sufficiency. Constant tautologies may be removed only after checking the actual constants. This projection does not need a presupposed explicit rectangle.

If s_u>s_l, the same-plane MC pairs imply P>=p_l and P<=p_u. A two-cutoff implementation that removes the MC upper rows but omits these consequences changes the projection. The counterexample already in the task is valid: s_l=1,s_u=2,p_l=0,p_u=1,S=1,P=2 gives L2=3>U2=2, although sufficiently loose lower-plane cutoffs can hold. Recommended first implementation is the full projection from actual normalized row coefficients; reduce only with an explicit equivalence argument.

Degenerate cases:

- s_l=s_u=s0>0: MC forces W=s0 P; the actual W box then restricts P to [w_l/s0,w_u/s0]. Standard W bounds yield [p_l,p_u].
- s_l=s_u=0: MC forces W=0 but supplies no P upper bound. Do not invent P<=p_u. Compatibility also requires that the actual W box contain zero. Original g+lambda P<=c remains essential.
- lambda=0: if a W block exists, preserve its compatibility projection and the W-free SP consequence Hsum<=ncS. The current shared factory's `cutoff_active` requires lambda>1e-12 (`463-465`), so the active frozen .15 path must not be generalized to claim this block is emitted at zero lambda.
- Near-degenerate widths permitted by 1e-12 activation guards must be treated according to actual emitted coefficients, not divided away as an exact positive rectangle without a check.

The actual sampled S12 W rows are c348-c351 (MC) and c352 (SP); W box is [0,119.07461043858049]. SP's W coefficient is serialized as 1.7999999999999998, while coefficients on P's constituent e variables have independently rounded products. Thus symbolic factorization into an exact common S,P rectangle is not automatically an equality over decimal rationals. Eliminate from the actual row vectors, or explicitly report numerical equivalence under the inherited tolerance rather than claiming exact rational projection of arbitrary double matrices.

Preserve every W-free row and variable domain, especially g+lambda P<=c, scalar estimate, cap/floor, original e bounds, A/B, state products and routing structure. Build the same physical fleet Start over the remaining actual columns, check all bounds/types/rows and the objective, submit it, and read it back. A missing W column must be accepted by the mapping logic rather than required by an old audit.

## D frozen identity and experimental gate

The original E3 and DLL exist and were hashed read-only in this review:

| Asset | SHA256 |
| --- | --- |
| `E:/codes/ExactEBRP-work/build-cache/round130/ExactEBRP.exe` | `2df9e0e160ecbcbd35c4e83eb434344893f9a59beb59667f3681772b4ff66d6c` |
| `D:/gurobi1302/win64/bin/gurobi130.dll` | `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88` |

They match R130 E3_frozen and R131 paper_version_manifest. The five central files audited here (CplexBaseline, IntervalRowFactory, PaperK1AmSf, MipStartMapping, Round127Research) also match the corresponding R130 frozen source bindings. This is targeted source/asset checking, not a complete unchanged-tree assertion. The manifest source identity is 7564a5415331b380e24d1ec06936dcfd56557e67; R131 model_appendix line 6 still refers to historical 355eefd2 as its source-location snapshot. Refresh this provenance wording in the new authoritative manuscript rather than implying those SHAs identify the same complete source tree.

R130 authoritative frozen argv confirms:

- P: `--method gurobi --plain-baseline --round127-mode p`, cold original compact and no H/Start.
- PS: the original compact plus `--round112-ens-start-compact`, with no `--round127-mode`; its own full paid H and complete Start.
- S2: gcap-frontier, research-round83-vds-equal-net-exchange, `--round90-lp-g-split false`, `--round98-state-service m-binary`, exactly `--round127-mode ms2`.
- S2R (C only): exactly mode `s2-root`, pair support and inclusive root. `md` is not a substitute. `include/Round127Research.hpp` suppresses only the named no-improver sentinel for inclusive root.

An observed reporting trap: the R130 S2R top-level result.json carries default/off values such as compact_bc_sp_product_estimator=off and tailored_bc_mode=off while its actual saved root demonstrably has the W block and all three geometry families. Model content must be read from the actual matrix/internal scope and complete call records. This discrepancy by itself is not a model correctness defect.

Preformal D review should verify the following concrete artifacts before exposing any formal input to H/LP/MIP:

1. A frozen input-generation record that assigns every K role to CITI/CABI and selects X or its justified construction fallback; station selection, seeds, coordinate units, compact/regional rules, missing-field handling and each synthetic field are fixed. File hashes, actual T/Q, source station IDs and historical overlap must be explicit. New hashes alone do not establish unseen station sets or distributions. Shortage positivity uses sum b<sum D with positive weights/lambda; balanced/surplus zero outcomes remain in the panel.
2. Exactly 12 inputs, two native Seeds, 48 P/S2 plus the 12 preselected PS arms, with no extra arm for a shared comparison. PS inputs are 15-S,20-U,35-B in each layer. Freeze full launch order and S2/P, S2/PS, PS/P directions and denominators.
3. Caps 600/600/1200/1200/2400/2400 per layer role. D totals 84000 nominal seconds; C totals 32400, with both together at most 84 formal arms. Physical T is a distinct field. Remaining 3600 qualification, 10800 E, 4800 C3, 8400 repair allowances total 144000 seconds with the core caps; preserve actual fee categories without summing nested H/LP/MIP again.
4. Original numerical and deadline contract: lambda=.15; pickup=drop=60; H seed20260626; Threads=MIPThreads=1; affinity4 if inherited; MIPGap=MIPGapAbs=0; FeasibilityTol=OptimalityTol=1e-6; IntFeasTol=1e-5; Presolve=-1,MIPFocus=0,Cuts=-1; producer/native/hard-stop/shutdown offsets match R130/R131 (native cap-6, hard-stop cap-2, shutdown margin30) and each arm pays its own preparation.
5. Input/argv/PE/DLL/source-binding hashes are sealed before launch. D uses original E3/DLL; C uses its separately sealed research build and its own same-build baselines. Do not silently rebuild a missing frozen asset.
6. Actual return/call status, integer/physical witnesses, Start mapping/readback, scope coverage and valid global L are qualified before certification. A leaf optimal/infeasible return or a high local L alone is insufficient. A qualified startup-zero branch has no backend exposure.
7. Save signed U-L and the actual observation cutoff for open runs; T_cert is empty if open. Pair directions use exact unrounded producer certificate times and certificate asymmetry. Both open is UNDETERMINED, failed evidence UNEVALUABLE. Do not import the R130 descriptive materiality threshold as a direction rule.
8. Separate T_produce and non-native post-verification T_verify. Do not consume the fixed producer cap with retrospective independent checks. Across Seeds, aggregate by problem and show K/X, size and positive/zero-objective strata; 24 Seed observations are not 24 new problems. Own valid U/L only; cross-arm consistency checks must not transfer certificates.

## Required C admission record

Before C formal launches, review actual matrix differences for representative nonzero, zero-S, fixed-S, singleton-state, n=1/n=2, positive-alpha (if claimed), and heterogeneous-Q fixtures using finite existing tooling. This reviewer has not run those checks. The record should bind:

- Same-build baseline against frozen E3 S2/S2R semantics; exactly the three intended row deletions in geometry mode, or exactly W and its correct full projection in SP mode. Domain-generating flags, non-W rows, objective, column domains and H remain the same.
- Same physical Start mapped, validated, submitted and read back in each variant.
- Canonical continuous LP status/value/residual, explicitly distinct from MIP root processing; actual numerical tolerance and all deviations reported. Equal raw LP values support this finite check but do not prove projection equality.
- Actual H coefficient classification and bounds; full W usage inventory and normalized real row vectors; rounding policy. If exact rational matrix equivalence is not proved, use that narrower claim explicitly.
- Common log/trajectory policy fixed before the same-build three-way panel; unknown root/presolve fields remain unknown. No extra diagnostic optimization is passed off as a native formal root.

The four C roles are input-hash identities, not labels alone: SC-C15-B c0d5fc4eee62e1e454b8acde8b721640e410bf496593b14d4cbdb1ccf36f14ea; SC-B20-S 70ebad164c3da58c52d0ad7fce651a6f4d90f54323a939d6c109a17eaffb8b3c; UC-C20-U e4de3620f2eba0c9c91a18fddbc5db26700914c280e614c37d3c159417f61df5; PB-C35-U 67fa5712962980350c0b7be00abbcc4866af0fe376d0395b565ec082d36842e5. Source manifests supply their own T/Q and complete argv.

Disposition: analytic premises reviewed; original D asset identity verified in the stated targeted scope; C implementation/actual-matrix/Start admission remains to be reviewed after it exists. No finite coefficient check above is a global rational proof or external reproduction.
