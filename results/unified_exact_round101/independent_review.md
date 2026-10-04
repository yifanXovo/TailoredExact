# Independent read-only final review

Reviewer: the single user-authorized agent `/root/final_review`. This records its final source-and-evidence review, including its original finding and subsequent inspection of the execution team's separate correction. No additional review agent was used. The reviewer did not edit files, compile, rerun native search, call Optimize, or start B&B. This is not a full bitwise performance reproduction.

## Conclusion and corrected finding

The review supports retaining Round101 as a mathematically qualified experimental component, with the default remaining OFF. The evidence does not support adopting FLEET-ROOT as M-B or promoting it over original ENS-C. One actionable P2 failure-propagation issue was found in measured v6; the separately recorded correction resolves the inspected paths. No further actionable issue was identified within this review's scope.

In measured source `8d6a497aa47d475436626b20bc573188d96e9e99`, fleet callback and summary-write failures invalidate normal returned outcomes, but do not publish failure to NEJ1. A stopped evidence reader could consequently accept committed bounds without learning of the fatal error. The callback also lacked containment for unknown exceptions. All26 measured fleet summaries have empty failure fields, and the two actual interrupted arms are P and ENS/OFF; no measured occurrence was found affecting the retained comparisons.

The reviewer inspected the correction through `c811a06a5423faaa7b909500bb8c1491f6d28da3`. The shared failure helper records a journal failure, disables publication, marks fleet failure, and preserves returned-outcome rejection. The callback contains standard and unknown exceptions and requests termination. Contract and summary streams are explicitly flushed, closed, and checked.

The correction's source, test, and four binary hashes match its manifest. The reviewer independently checked all24 raw fault/control receipts for sequence, timestamps, payload length, SHA, and newline completion. Each of the five failure cases has a globally eligible prior bound of .1, followed by a failure receipt and no later event. Running the unchanged R86 reader in read-only mode rejects all five complete failed streams with `journal_failure`; the healthy control accepts .25. Retained execution receipts report53 actual callback/summary fault checks, existing5376 fleet fixtures, and28 journal checks passing with zero Optimize.

This closes the finding for the tested paths. Tests use the actual private callback and summary writer with fake API functions; they do not qualify a real Gurobi search or complete storage loss. A historical prefix cannot anticipate a later failure, and a failure that cannot itself be persisted remains a journal-storage limitation. Correction PE `76ac0d20898d88949b01e945283f2b71a7981b5ace55963a6b7083f131d11a1b` is an **unmeasured correctness fix**, with no performance credit. Current and archived measured v6 PEs both remain `99b18e8a7e08edc4d379f85938f9e43f92431824148d64baf20b8169083cb918`.

## Mathematical and actual-model validity

Event inequalities are justified as necessary conditions for the audited original integer model. Original binary selectors, inventory balance, unique service, direction, and quantity links establish each threshold event's carrying vehicle and minimum quantity. Events use distinct stations; duplicate-station contributions are rejected.

Outside suppliers, receivers, and visits remain legal. Nonnegative directed shortest-path closure permits routes through outside stations; the subset argument does not require a direct route through only selected events. Empty departure and nonnegative return load imply total pickup is at least total delivery. Handling therefore has necessary lower bound `c*max(P_A,D_A)`. Cumulative pickup may exceed Q; Q limits load and individual operations, not total pickup over the route. Loaded return remains legal.

Directed closure and Held-Karp use conservative lower arithmetic. Only a strict finite lower bound exceeding the safe horizon excludes a subset. Unsupported arithmetic retains possibilities. These are necessary-system ranks, not route-feasibility certificates. The small DP is complete within its declared support limit and covers assignments across every vehicle. A successful complete greedy assignment merely establishes rank equal to support size; greedy failure excludes nothing. The scalable rank is an upper bound from conservative directional cardinalities and a complete event-to-vehicle/direction-slot matching. Relaxations can weaken a cut without excluding valid assignments.

The reviewer checked imported coefficients, types, prerequisite rows and their connection to physical premises. Its independent F2 LP-expression parser matched all9269 actual exported rows against the typed matrix. It independently checked1088 prerequisite rows used by the retained contract: selector links, inventory balance, service/direction/quantity constraints, depot/station flow, MTZ, final net pickup and complete duration support. The export has1567 binary and140 other integer variables among3488 columns. Contract handling coefficient and horizon are conservative relative to the export. This goes beyond verifying a matrix hash.

Native integration uses `GRBcbcut` only at optimal MIPNODEs, with PreCrush1 read back. LP relaxation handling remains separate. Raw original-column activity supplies reliable violation; candidate ordering and heuristic masses do not certify it. Per-call remapping and cache identity include the immutable numeric and original-column contract. Cache eviction recomputes; repeated API submissions are not permanent native retention.

## Independent retained proof calculations

The reviewer used its own exact-dyadic closure, Held-Karp and assignment recurrence, without importing the execution team's proof verifier. For each vehicle it reconstructed allowed subsets and formed attainable disjoint coverage sets: `R_0={0}` and `R_v={u union s : u in R_(v-1), s in A_v, u intersect s=empty}`. Maximum covered cardinality within each mask reproduced the saved DP layers.

From the actual F2 SUBMIT native stream:

| Actual record | Support | Rank | DP entries checked | Exact raw activity |
|---|---:|---:|---:|---:|
| Root pickup, node0 | 9 | 2 | 1536 | 5.182300799890994 |
| Delivery, node11 | 9 | 2 | 1536 | 2.0478798650246355 |
| Mixed, node36749 | 8 | 6 | 768 | 6.066369511559355 |

All3840 saved DP entries matched. Exact activities exceed saved conservative activity bounds and RHS by more than the required1e-5 margin. Threshold membership, distinct stations, original columns, coefficients, ranks and raw activities were checked. Positive-node samples ensure this was not confined to root evidence.

The reviewer also independently reconstructed a real root scalable record with12 delivery events at quantity13. Its residual-BFS maximum-flow calculation reproduced rank2 and slots `[0,1,0,1]`; exact singleton travel minimum873.0816319884569 exceeds the recorded lower bound. All75 original selector columns map correctly, with unit coefficients and exact raw activity3.3592521772698176.

For F5's38-event pickup set with rank16, it independently checked all703 physical pairs. Each permits pickups12 and12, prefix loads12 and24 and loaded return24 within Q30; worst duration5733.160159236933s is below7200. This supports the stated distinction from an all-pairs-incompatible clique certificate for that particular set. It does not establish historical cutoff/G feasibility, general projection dominance or dominance over native cuts.

The diagnostic bank establishes selector-vector nonredundancy. Its16 LP calls show reliable violations and row-activity excesses, but no material original-objective LP improvement. All four reextension calls succeed after freeing selectors and `state_g` companions. Common-coordinate projection improvement is unproved.

## Interrupted recovery

The original V30 ENS audit/raw summary remain FAILED, with no normal `result.json` and an Optimize CSV containing only its header. Recovery is a separate read-only derivation.

The reviewer independently checked all368 NEJ1 receipts,786 preserved-file hashes and the original six-row summary prefix. It reconstructed97 physical witnesses, including geometry, loads, inventory, unique stations, integral operations and objectives. It independently replayed all261 global native bounds with live-leaf matching, contiguous G coverage, witnessed cutoff, contradiction checks and the `F>=G` tail argument.

Actual logs, typed models, parameters and source distinguish three LP calls from two MIP calls; filenames alone were not evidence. Call4 is a returned child-bound-target MIP and call5 an unreturned terminal MIP. Their scope/model prerequisites support the recovered complete-domain bound. The reviewer reproduced U=.27382141472368104, L=.2307541028332916, signed gap=.043067311890389454. The endpoint remains **uncertified**. Missing Work, nodes, final status and solver finalization are not reconstructed.

Recovery/continuation preserve frozen original helpers, source, binary, parameters, inputs and failed raw artifacts. Only original never-started commands7--9 were admitted prospectively; admission precedes launch and all three later pass original audits. Confirmation inputs were generated once without redraw. F5 P also retains its registered hard-stop, committed-only, uncertified status.

## Performance conclusions and clocks

Adverse results are retained and support leaving the option OFF:

| Comparison | Checked conclusion |
|---|---|
| F2 tree SUBMIT | Loses ENS certificate within its cap; extensive submission is not a speed benefit. |
| Fresh final-source F2 ROOT | 858.500s versus ENS572.078s: approximately50.1% slower, severe regression. |
| V20 ROOT | 266.640s versus ENS217.375s: approximately22.7% slower. |
| C2 development | ENS/ROOT weakness against P persists. |
| N2 development | ROOT improves budget U/gap against ENS; development signal, P retains stronger gap. |
| F5 | No material final ENS improvement; earlier1790s ROOT gap approximately107.7% larger. |
| V30 confirmation | ROOT U approximately2.0% worse, gap14.4% larger than ENS. |
| V50 confirmation | ROOT U approximately25.3% worse, gap95.0% larger than ENS. |

Both-unproved eventual certification-time ordering remains unknown. Reports avoid family-wide impossibility extrapolation.

The reviewer reconstructed all205 covered checkpoint entries directly from same-run committed observations and conservative availability times or completed certification. All19 uncovered entries retain missing endpoints. Common cap-minus10 checkpoints, certification carry and comparison rules do not interpolate after unproved exit or splice arms. Offline R100 reporting/clock adaptations do not alter original frontier/certificate semantics. Numerical certificates retain the old contract/full normal-completion boundary. Exact-dyadic replay does not make them rational optimality certificates or exact engine discovery times.

API successes, event/rank proof keys, literal coefficient/RHS rows and native User counts remain separate. F2 tree SUBMIT has8077 API successes,6247 saved proof keys/literal rows and5552 native User cuts; these are not interchangeable measures of useful cuts.

## Protection, accounting and retained evidence

Source and CLI/config checks preserve OFF defaults, original ENS-C and original P no-Start behavior. All eight P arms retain byte-identical original compact-reference LPs. `PaperExternalGiniTree.cpp` is unchanged relative to R100; no stacking, case dispatch, internal time/Work/restart policy or controller/frontier redesign is introduced.

The reviewer independently reconciled45 unique conservatively charged starts and69575.05679539999s within72/80000, with no reservations or incomplete processes. Cost ledger137 internal Optimize calls comprises117 formal calls,16 diagnostic LP and4 reextension calls. Engineering checks are separate.

It verified147 compact-copy bindings, retained native sample bindings, protected-file hashes and early source-recovery identities. Indexed original native streams contain13339 records:13243 small-DP and96 scalable. Execution-team summaries report11563 distinct contract/proof replays and281912 row-inventory checks across1433 witness records. The reviewer inspected those summaries; it does **not** claim independent repetition of that entire population.

Reviewed artifacts include the requested reports/freeze/recovery manifests, complete results/clocks, proof/physical/integrity summaries, retained native contracts/certificates, actual exports/logs, integration source, recovery/reporting scripts and separate correction diff/fault artifacts.

Native01's early measured PE remains missing. Exact recovered source/prospectively recorded identity do not replace that binary; no rebuilt substitute is claimed. Larger original matrices, streams, logs and builds remain locally indexed. Compact evidence alone is not a complete performance-reproduction package. Storage and reproduction limits remain explicit in the delivery.
