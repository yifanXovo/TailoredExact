# Round128 independent preformal source review

Review date: 2026-10-21 (Asia/Shanghai). Reviewer: a separate collaborating executor, requested under task Sections 5 and 11. Base HEAD: `d0b96fe43f463994d11ee392eeaa2092916838a2`.

This review inspected the four initial MD-R edits, the reused MD controller and native Start/return implementation, the current scoped reader, and the already saved R127 boundary review/vectors. It performed no compilation, Optimize, performance experiment, production-code edit, or historical-carrier restoration. Native qualification and a real MD-R chain were pending at the initial pass and were subsequently reviewed below. Findings below describe the initial source snapshot; subsequent dispositions retain that record.

**Final limited disposition: PASS after corrections.** The source blockers below were resolved before formal sealing. The reviewer independently checked a final-identity nonzero native chain and own Start, three artificial native boundaries including `U0=3e-9`, the actual TIME_LIMIT open-return chain, and the three archived-scope initial-root comparisons. This is a bounded preformal MD-R review, not a completed formal panel or an all-history/all-rational-matrix proof. The chronology below preserves every initial finding and the failed prequalification observation.

## Initial disposition

The semantic row suppression is suitably narrow. The reused MD controller still has two reachable paths that can omit the required nonzero MD-R root MIP, including a path that can produce an inherited numerical certificate without that MIP. These are MD-R protocol qualification blockers, rather than demonstrated counterexamples to every inherited MB certificate. A separate check-order gap also requires resolution or explicit task-owner disposition before the revised mode is sealed.

### Finding 1: the shared scheduler can skip all native calls for a positive U0

`ControllingLeafScheduler.cpp:586-599` treats a root with `gamma_L=0` as irrelevant when `U0<=1e-7`, and treats an open root with lower bound within `1e-7` of the cutoff as closed for scheduling. `PaperExternalGiniTree.cpp:4682-4683` uses `everyRelevantLeafClosed()` as its loop condition. Thus for `1e-12<U0<=1e-7`, the initial MD-R root can bypass model construction, Start validation, LP and MIP, even though its objective is nonzero under the reader's startup-zero convention.

The reader's explicit startup-zero qualification is narrower: `round108_reader.py:359-362` requires `U<=ZERO_TOL`, where `ZERO_TOL=1e-12`, and no started native calls. The apparent zero branch in `main.cpp:13558` is after the external-tree branch has returned and therefore is not an independent guard for this C6 path. The Round43/44 zero-range special cases are disabled in the isolated MD-R protocol.

Minimal suggested resolution: only in MD-R, distinguish the retained startup-zero convention from the positive case that owes a chain. For that positive case, enter the loop until its sole root terminal MIP has actually run, and select the sole `L0` root directly instead of relying on the shared tolerance-filtered selectable set. Leave ordinary MB, MS2 and P unchanged. Preserve a zero-exposure report for the admitted startup-zero case; do not describe a general `1e-7` near-zero interval as exact zero.

### Finding 2: an LP-close/deadline return can certify without the owed MIP

The existing MD guard at `PaperExternalGiniTree.cpp:4789` correctly disables the immediate LP-fathom shortcut. Nevertheless, after a complete LP has raised the root bound to `U0-1e-7` or above, a deadline encountered before `:8966-8969` can stop the method before MIP launch. On finalization, the scheduler already reports every relevant leaf closed by its numerical bound predicate. The generic lifecycle equations at `:9383-9405` accept `Optimize=LP=1`, `terminal MIP=0`, and `terminal MIP leaves=0`; they do not require MD-R's second Optimize. The final certificate helper checks these generic flags and numerical gap closure, rather than the MD-R-specific chain obligation.

This is a concrete control-flow omission: even after fixing initial root selection, a complete LP alone can discharge the generic scheduler while MD-R still owes its MIP. It need not imply a mathematically invalid LP lower bound, but it violates the requested control definition and cannot be admitted as a completed formal MD-R observation.

Minimal suggested resolution: only for the nonzero MD-R case, require one completed root LP call and one actual root terminal MIP call, two total Optimize calls, no partial/child/target calls and no rebuild before admitting the lifecycle/certificate. Require the full own Start to have passed and actually been submitted. A deadline before the required MIP leaves the MD-R observation open/unqualified as appropriate; an LP-close condition is not a replacement for the owed call. Keep TIME_LIMIT/INTERRUPTED native statuses and qualified raw bounds distinct from OPTIMAL.

### Finding 3: the complete own-Start check currently follows the root LP

Task Section 4.2 orders full own-U0 model mapping/checking before the LP. The reused implementation enables `request.round68_verified_start` only for non-LP requests (`PaperExternalGiniTree.cpp:3658-3668`). Complete native-column, type, bound, row and original-objective validation occurs in `GurobiBaseline.cpp:653-758` immediately before the MIP. Therefore the current actual sequence is LP, restore integer domain, validate/submit own Start, MIP. The qualification exporter can precheck fixed artificial vectors, but cannot establish that every formal arm's actual own H witness was checked against its actual root before its LP.

This ordering does not by itself demonstrate a false result: a failed eligible mapping stops the MIP. It is still a mismatch with the user's specified per-arm order. A repair should add only a paid MD-R read-only precheck on the actual root, with no added Optimize or change to ordinary modes.

### Start eligibility is an assertion, not merely absence of an exception

`prepareRound68Start` deliberately returns successfully without submitting a Start for an out-of-interval or above-cutoff candidate (`GurobiBaseline.cpp:703-706`). This behavior serves ordinary restricted leaves. The revised MD-R full own root has a stronger obligation: its own U0 witness must be eligible. Qualification must assert complete mapping, original physical feasibility and objective, all-column bounds/types, all-row residuals, objective equality, submitted vector and native readback. A skipped/ineligible own Start must fail MD-R qualification; the generic function returning `true` is insufficient. The implementing executor has been informed and intends to enforce actual submission in qualification.

## Parts supported by the inspected source

- `round128InclusiveRoot()` is true only for explicit `md-r`; controls default to `off`. `round127Md()` reuses the existing controller defenses. The ordinary mode predicates retain their prior outcomes.
- Both the shared factory and fallback writer guard only the named `interval_no_improver_domain_closure` emission. `P>=penalty_lower`, its domain computation, inventory domains, incumbent row and the R/C_R/C_G families remain in the inspected blocks. The suppression uses semantic scope, not a matrix row number or removal of all constant rows.
- At `PaperExternalGiniTree.cpp:1854-1859` the reused controller requires `I0=[0,min(U0,(n-1)/n)]`; `:3071-3073` requires exactly that one complete root. Canonical construction uses the own verified cutoff with epsilon zero. The terminal request fixes its cutoff to the original own U0 (`:9006-9007`).
- Existing MD guards reject root LP or MIP INFEASIBLE despite the promised own witness (`:4758-4762`, `:9108-9111`), disable the immediate LP-fathom path (`:4789`), NEXT/frontier targets (`:6514`) and child/adaptive split eligibility (`:6606`), and refuse a changed model epoch (`:3871-3874`). The actual formal chain must still verify zero exposure to all forbidden paths.
- Round68's eligible Start path reads the native domain and full linear matrix, independently verifies physical routes, validates rows with the inherited tolerance, recomputes the native objective, submits every column, reads the full vector back and persists it. The backend restores original integer VTypes after LP. The current reader separately retains raw signed endpoint gaps and checks proof provenance/coverage; it does not silently clip an inconsistent endpoint to U.
- The terminal decision function distinguishes OPTIMAL/INFEASIBLE from interrupted returns. An interrupted native call is not renamed OPTIMAL by that classifier. The MD-R-specific lifecycle omission described above must nevertheless be fixed.

## Mathematical boundary contract

For a physical true-G interval I and cutoff c, assume the verified domain argument supports `F>=L_a=a+lambda*P_lower` for every physical point in I with `F<=c`. On that subset the floor is L_a; on its cutoff complement the floor is c. These two sets cover the full physical interval, giving `B_I=min(L_a,c)`. This is scope completion, not a repair for contradictory numerical bounds. If a verified witness in the purported subset contradicts the asserted floor, its source/premises must be investigated first.

| Domain floor | Exact conclusion |
| --- | --- |
| L_a > c | The non-strict cutoff subset is empty, subject to the witness-consistency check. |
| L_a = c | Equal-c physical solutions can remain; only strict improvement is excluded. |
| c-1e-9 <= L_a < c | The supported lower bound is L_a. The inherited sentinel predicate fires, but does not prove exact emptiness or exclusion of arbitrarily small improvement. |
| L_a < c-1e-9 | The inherited sentinel predicate does not fire; the ordinary valid floor remains L_a. |

The saved R127 zero-Optimize vectors independently expose the equality failure of the old inclusive-root claim: V2/M1, zero initial stock, D=(1,1), Q=1, handling 60+60, T=60 gives S=0, G=0, P=2, F=U0=0.3. All four saved full/deletion variants map the empty physical fleet to all ordinary rows and violate one empty `0<=-1` row by 1. Their T=3600 controls have no violations. Those saved records were read, not regenerated. An MD-R qualification must now show that the actual equality model differs only by removal of that semantic row, while retaining its penalty lower bound. Decimal/floating comparisons near 1e-9 must be reported separately from exact rational claims.

## Finite read-only R127 impact check

The three already present R127 core MB directories each retain exactly three canonical models: their actual `L0` root and two probed child scopes. All nine file SHA256 values matched at least one row of their own saved `paper_optimize_ledger.csv`. The exact empty sentinel encoding observed in the artificial witness model is `c10: 0 G <= -1`; no such impossible zero row was present in any of the nine actual core MB matrices. This check restored nothing and started no solver.

| R127 role | Actual initial root SHA256 | Actual calls linked to root | Sentinel count, root plus two probed scopes |
| --- | --- | ---: | ---: |
| SC-C15-S | f5eb565e62369104017af87ad255aac727f8e6a34ca5b4f90021f8738b5692a2 | 3 | 0 |
| SC-B20-S | c84eb99911a5ebb9ef50a9f94a3b36e4af87b3b45f39e81321f40d43896f8e75 | 2 | 0 |
| PB-B35-B | 3630a5d78472aba33dfab28437b3e530f70bc06d0a0db0d039a84b418e276dea | 2 | 0 |

The saved leaf ledgers show terminal-MIP-optimal closure of L0 for the first two roles and an open L0 after TIME_LIMIT for PB-B35-B. Their saved sources list the actual LP/native bounds; no sentinel-based infeasible closure was observed. This supports the narrow statement that these three saved MB runs did not rely on the disputed row. It is neither an all-history matrix requalification nor a global proof of validity for other runs.

## Required subsequent limited checks

Before sealing: resolve Findings 1-3, rerun only the authorized finite qualification if needed, inspect actual L<c/equality/L>c/near-threshold and incompatible-Start results, and confirm normal MB/P/MS2 semantic bridge equality. Then review one real nonzero MD-R LP+MIP chain, full actual own Start, original/returned scope, unchanged cutoff and integer restoration, two Optimize calls, no child/NEXT/AM/rebuild, and the final signed-gap/physical/coverage gate. This report does not yet certify those missing runtime facts or any formal performance result.

## Second source pass and additional return-status finding

The implementer added MD-R-only nonzero-chain selection and final call-count/Start requirements, and a `validation_only` option on the reused native mapper. The actual pre-LP check is correctly placed after capturing the original VTypes and before setting all columns continuous. It reads/checks the original full matrix, native domains and original objective, records the physical mapped vector and phase, and submits no LP Start. The ordinary Start submission path retains its default behavior. MD-R treats an ineligible own Start as a failure.

This pass caught a first-access exception in the revised loop: `runtime.at("L0")` was evaluated before the empty runtime map contained L0 on the tiny-positive-U0 path. The implementer added `runtime.try_emplace("L0")` only for the owed MD-R chain. It also caught that newly added pre-LP matrix-validation work was not subtracted from the LP native TimeLimit. The implementer extended the existing final native deadline/readback block to MD-R LP calls, deducting all backend preparation from the supplied remaining time. Both limited source corrections have been inspected. They change no ordinary MB/MS2/P control condition.

However, a further explicit MD-R return-status gate is necessary before sealing. After a real terminal MIP returns TIME_LIMIT or INTERRUPTED, `terminal.leave_open_and_stop` breaks with L0 still Open. A near-closed LP/native bound can nevertheless make the generic scheduler report all relevant leaves closed, and the new two-call lifecycle can be complete. The final status assignment gives `certificate.certified` priority over `global_deadline_stop`, producing `status="optimal"` despite that terminal return. The user's revised control explicitly forbids treating those native statuses as optimal.

Minimal MD-R-only resolution: require the actual L0 to be `Closed` with `closure_source="native_terminal_mip_optimal"` in the final all-relevant-closed/certificate input, in addition to the existing numerical/source/physical/lifecycle conditions. That closure is written only after the terminal classifier has passed attempted/available/finalization (return code zero), identity, parameter and feasibility gates and received OPTIMAL. INFEASIBLE remains a consistency fault. Synchronize this additional return contract in the read-only MD-R evidence adapter: the generic reader otherwise discharges an Open leaf solely from its near-closed bound and would incorrectly disagree with the revised open result. Preserve all raw returned bounds and signed gaps and leave the ordinary methods' policy unchanged.

The current prequalification exports report 16 artificial mapped-vector cases and six complete E1/E2 ordinary-mode semantic bridges. The reviewer inspected those reports and their producing source. Shared/fallback equality removes exactly one semantic sentinel while retaining all other duplicate-preserving rows/columns/types/bounds/objective; the illegal cutoff and out-of-scope vectors retain violations, and T3600 removes no row. These exports provide no native runtime result. At this point native qualification under the final revised source identity remains pending.

## Final source pass, pending final-identity native qualification

The implementer supplied final candidate PE SHA256 `ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa`. Its inspected source adds the explicit L0 `Closed` / `native_terminal_mip_optimal` final gate only for nonzero MD-R. The corresponding read-only evidence adapter tightens MD-R complete-cover closure to the same source, and permits an unresolved near-equal gap to remain open for MD-R. It neither changes the lower bound nor relaxes any ordinary method's reader. The inherited full reader still links the optimal closure to an actual successful returned MIP, native log, scope and model identity. TIME_LIMIT/INTERRUPTED retain an Open L0 and cannot pass the new MD-R gate solely from an LP or MIP bound within tolerance. No remaining source blocker was found in the bounded final pass.

A real prequalification S12 chain under the earlier candidate `5a045e692c5fab5d4368a5a0d3a5bf5cf77294ec7c9e7ba7bc9e949fbc119a82` exposed a bookkeeping failure: the new lifecycle gate read `result.external_gini_tree_warm_start_submitted_count`, but the shared stats copier had never populated that field. The actual full Start had been submitted; the result incorrectly retained zero and rejected its lifecycle. The implementer now copies actual backend Start counters only for MD-R. The earlier failed result and audit remain intact and are not a formal observation or a final-identity qualification.

The reviewer independently replayed that earlier S12 own H fleet using the established physical reader and recomputed its full mapped-vector residuals directly from the saved canonical matrix. Results: 1,388 columns, 3,192 rows, maximum row residual `2.220446049250313e-16`, all actual types/bounds/integer domains satisfied, and pre-LP mapped values identical column by column to the MIP submitted/readback vector. The physical fleet has `F=0.29907089418635313`, `G=0.13023309631835087`, `P=1.1255853191200151`, maximum duration `3547.7351804688205 < 3600`, and vehicle return loads `[2,0]`. Both actual calls use L0 and one model SHA, with `[0,U0]` true-G scope and fixed own-U0 cutoff; only the MIP has integer-native proof preconditions. These are bounded functional observations of preserved failed prequalification evidence, not an upgrade of its rejected result.

As an additional independent zero-Optimize comparison, the reviewer compared every saved LP text line after removing constraint labels: shared and fallback equality models become exactly equal after deleting their sole `0 G <= -1` row, and both T3600 model pairs are exactly equal without deleting any line. Native qualification under the final candidate identity and the tiny-positive-U0 guard remain to be checked.

## Final-candidate S12 native chain and own Start

The reviewer subsequently inspected `qualification/native_S12_E2_final/raw/04_S12_S0_R1_MD-R` without starting any native work. Its actual PE SHA256 is the final `ac96cfea...84234fa` above, and every saved source binding matched the current source file bytes. The chain uses one model, one root LP (OPTIMAL, return code zero), integer-domain restoration, and one root MIP (OPTIMAL, return code zero), with no partial MIP, child scope, target or rebuild. L0's final closure source is `native_terminal_mip_optimal`.

Independent replay of its actual own H fleet and full pre-LP / submitted / readback vectors again checked all 1,388 columns and 3,192 rows, original variable types, bounds and integer domains. The pre-LP and submitted/readback values are identical in every column; maximum independently recomputed matrix-row residual is `2.220446049250313e-16`. The physical own U0, duration and return loads agree with the values above. Both call scopes retain exactly `[0,U0]` and fixed own-U0 cutoff, and the integer proof preconditions belong to the actual returned MIP.

This final-identity result records one actual submitted Start, complete lifecycle, a passing full evidence audit and a qualified numerical certificate. Its raw final U is `0.22524870597274982`, raw final L is `0.22524870597274932`, and the retained signed gap is `4.996003610813204e-16`. It is a qualification observation, not formal performance evidence. Final-candidate artificial equality / T3600 / tiny-positive-U0 native observations remain pending at the time of this addition.

## Final finite qualification closeout

The reviewer subsequently checked all three artificial native chains under final PE `ac96cfea3e0ac109cda523b9a1e2458d98a7d552bf0542e2877c1379e84234fa`. Each has one actual model, OPTIMAL root LP followed by OPTIMAL root MIP with return codes zero, one complete submitted/readback Start, no split/partial MIP/rebuild, and a passing evidence audit. Direct recomputation of the actual pre-LP and submitted vectors checked every column/type/bound/integer domain and every saved row; all three maximum row residuals are zero.

| Final native qualification group | Own U0 | Columns / rows | Actual Optimize calls | Raw final L / U |
| --- | ---: | ---: | ---: | --- |
| native_zero_S_duration60 | 0.3 | 41 / 102 | 2 | 0.3 / 0.3 |
| native_zero_S_duration3600 | 0.3 | 45 / 105 | 2 | 0.3 / 0.3 |
| native_tiny_positive_U | 3e-9 | 41 / 102 | 2 | 0 / 3e-9 |

The tiny-positive case truly executed both calls despite being below the shared scheduler's `1e-7` relevance tolerance. Its raw signed gap remains `3e-9`; it was not rewritten to zero or an exact-c analytical bound. Its numerical certificate additionally has an actual OPTIMAL integer-root return. This covers the initially discovered loop omission while preserving the inherited numerical policy.

The actual open-return qualification is `qualification/native_R98-C2_MD_R_open_final/raw/01_R98-C2_S0_R1_MD-R`. Its final-identity ledger has one L0 LP (OPTIMAL, return code zero, integer domain restored) and one L0 MIP (TIME_LIMIT, return code zero), both on model SHA256 `a4145df15459f85c4e9414131cf0af2f4d913e9ae467fd6021ec520ebcff3973`. The native log explicitly reports `Time limit reached`. A complete own-U0 Start of `0.39162089674952894` was accepted, with 31,141 rows checked and zero recorded residual. L0 remains Open with no optimal closure source. The source result records complete two-call lifecycle but `all_relevant_leaves_closed=false` and `strict_certified_original_problem=false`; it preserves status `round31_c6_external_gini_tree_time_limit` and failure reason `overall_global_deadline`.

The full reader passes this open observation with `numbers_qualified=true`, `certificate_qualified=true`, `formal_protocol_qualified=true`, `certificate=false`, and `T_cert=null`. Its recomputed physical U is `0.2991105685991542`, raw L is `0.18876504408197672`, and signed gap is `0.11034552451717747`. T_produce is `60.77467417996377`, T_verify is `1.9711657000007108`, and T_total is `62.74583987996448`. The observation is explicitly nonformal qualification. This runtime smoke did not land inside the `1e-7` gap band; rejection of the hypothetical near-equal TIME_LIMIT/INTERRUPTED case is supported by the separately inspected source/reader optimal-closure gate, not claimed as an additional native observation. No INTERRUPTED smoke was started by this reviewer.

The final zero-Optimize role-root report labels its archived H scopes as qualification fixtures only. The reviewer independently hashed MB and MD-R LPs for all three roles: each pair is byte-identical, with the same three root hashes recorded in the R127 impact table above. Thus these fixture roots contain no sentinel and differ by no other matrix content. The associated MS2 report records deletion only of 910, 2,280 and 19,635 three-station rows respectively, no columns, and no other semantic difference; inspection of that report is not a claim that the reviewer independently replayed every MS2 deletion. The ordinary small/medium E1/final-E2 zero-Optimize bridge and actual Gurobi `13.0.2` readback are retained in `formal_role_root_differences.json` and `qualification/final_bridge/`.

**Bounded preformal conclusion:** no remaining MD-R blocker was found in the reviewed final source, inclusive-boundary differences, representative full Start/physical replay, actual complete root chain, or actual open-return contract. The implementer can proceed to its independent admission/seal step for this candidate. Formal arms must still pay their own full H and recheck their actual same-H / initial-U / root scope and differences after execution; archived fixture U values supply no formal Start or cutoff. All source revisions, the rejected prequalification result and their costs remain preserved. This review file is complete for preformal sealing and will not be altered after the seal.
