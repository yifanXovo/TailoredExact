# Independent mathematical and implementation review

Reviewer: actual spawned agent `/root/math_review` (an agent review, not a
human referee or a licensed replication). Review date: 13 November 2026,
Asia/Shanghai. Work was confined to the Round165 worktree. No solver,
Optimize call, production compilation, commercial runtime or new performance
measurement was used. The reviewer did not modify the manuscript.

Disposition: the current mathematical/algorithmic account is suitable for
internal review after two small textual corrections below. No change to a
historical numerical result, qualification decision or scientific conclusion
is required by either finding. The integrating author accepted both findings;
their final corrected lines should be read back once.

## Concrete findings

| Location in reviewed source | Finding and consequence | Required correction |
|---|---|---|
| `model_and_algorithm_appendices.md:177`, Lemma A1 | The listed assumptions cite (A2) and (A5), but the proof also uses inventory balance (A10). In the full model the balance is present, so the implication is correct; as a standalone statement its explicit premise list is incomplete. | Add (A10), or explicitly say “including inventory balance,” to the hypothesis. The A/B equalities are still unnecessary. |
| `model_and_algorithm_appendices.md:365`, A.5.6 | “The frozen implementation instead tested … and wrote an impossible row” can describe the current freeze as retaining the invalid pre-R133 shortcut, although the following paragraph and A.7 correctly describe its removal. The current measured factory retains only the valid penalty floor. | Identify that sentence as the historical pre-repair writer. Keep the original boundary/correction history and the valid inclusive-cutoff argument. |

There was no further mathematical or implementation blocker in the reviewed
scope. The main algorithm's proof-accounting view is supported by A.6;
Appendix B.4 explicitly distinguishes it from un-clipped raw scheduler
fields. It does not promise an unimplemented general online revocation engine.

## What was actually checked

The current body, full Appendix A/B, main Algorithm 1 and mathematical
companion were read. The generated 53-page manuscript PDF was opened with
pdfplumber: Algorithm 1 appears on page 7, Lemma A1 on page 31, cutoff
complement discussion on pages 6/38/43, and references begin on page 52.
This is a content/location check; the primary agent performs final visual QA.

| Object | Assessment and concrete implementation anchors |
|---|---|
| Original physical problem | A1–A11 preserve empty departure, one nonzero one-way service per station, every prefix load, loaded return and its unloading time. The identity `tp*pickup+td*(drop+return)=(tp+td)*pickup` is correct. Q is not a cumulative-pickup budget. The original depot fields supply no loading. |
| Shared states and integrality | A15 plus the A16 movement/visit equations has the main-text aggregate pickup/drop form once original inventory balance is used. `CplexBaseline.cpp:3010–3070` emits the shared reconstruction. Integer b/Y, unique assignment, binary direction and balance imply integer p/d, independently of A/B. No full-route hull claim follows. The isolated VD-P block's rectangle projection statement is correct. |
| Gini and objective embeddings | D>0, nonnegative ratios, S=0 convention, depot exclusion and nonnegative lambda/weights are explicit. Zero Gini allows common shortages. At a selected integer stock, Z=gY and the native numerator epigraph imply g≥true G; true-G membership provides a tight objective-preserving extension. Arbitrarily inflated auxiliary completions need not be retained by static interval rows. |
| Supply/support rows | The unit-matching argument and metric shortcutting prove A24. Nonzero integer service gives pickup≥ceil(|W|/2), with supplies allowed outside W. Both A27 branches have a valid deactivation proof. `Round127Research.hpp:38–39` disables triples for ms2/s2-root; the writer's pair/triple predicates and static factory agree with the paper. |
| Cutoff and cover | `min(qualified local bound, source cutoff)` is the correct unconditional regional floor; a covering union takes a minimum, same-domain independent information a maximum. Both midpoint children preserve the union including the boundary. The scheduler's atomic split validates lineage/endpoints/inheritance before replacing the parent (`ControllingLeafScheduler.cpp:211–293`). Invalid/incomplete or interrupted evidence does not remove unresolved coverage. |
| NEXT and AM | `PaperExternalGiniTree.cpp:898–944` checks noncontrolling requeue before the already-reached milestone, and chooses the next strict open-region bound. Lines 1083–1134 implement the stated normalized two-child score/tolerance, strict-child test and parent-MIP target. Requested targets are not credited as returned proof. Depth/width guards retain an exact parent continuation or OPEN at the deadline. |
| Source rejection and zero proof | `PaperExternalGiniTree.cpp:9610–9639` saves the abandoned scheduler, calls `abandonNativeSources`, clears runtime and returns a full-domain unresolved state with floor zero. It is a conservative global fallback, not dependency-wise online repair/resumption. `IndependentObjectiveProof.hpp:12–62` checks equal ratios and positive-weight target equalities in integer stock arithmetic and re-verifies the complete physical fleet. Near-zero floating F is insufficient. |
| H and termination | B.6–B.11 retain the actual order encoding, complete decoder, joint insertion, signed quantity changes, proxy ordering, neutral moves and tie limitations. The wrapper enforces the 24 random orders and cache limit 200000 (`HgaTgbcRunner.cpp:143–146`). Ideal finite-state descent and operational deadline termination are correctly distinguished from an exact floating-arithmetic monotonicity claim. H closure is not an optimality certificate. |
| E+ | The root helper's objective `max(gamma_L,trueG)+lambda*P` with trueG≤gamma_U retains the epigraph distinction. The first-root supported/total-stock domain and cutoff complement must preserve original physical embeddings. The current text confines the result to a qualified independent floor, keeps helper cost within the same deadline, and makes no physical-U, Native-row, AM-input or new-Seed robustness claim. |
| Mechanism boundary | §§6.2–6.4 retain the adverse root-only endpoints, row-deletion Seed reversals and inventory-versus-physical gap distinction. Strong complete B/P evidence is not split into additive component gains. These limits are scientific evidence, not a newly discovered R165 result. |

Seven selected active files were byte-compared with measured C++ commit
`e920b92e199e825ec89a2932f701861ff158e0d4`: CplexBaseline.cpp,
IntervalRowFactory.cpp, PaperExternalGiniTree.cpp, ControllingLeafScheduler.cpp,
HgaTgbcRunner.cpp, MipStartMapping.cpp and IndependentObjectiveProof.hpp all
match exactly. `git diff e920… HEAD -- src include config` reports only the
additional Round160 stub. This does not claim the two entire source trees
are identical. R137's older measured source/PE, historical line-pointer
snapshot, later e920/PE and current document source identities are separately
identified; prose editing cannot change which executable produced old data.

## Scope and remaining scientific limits

This is an algebraic and selected-code audit, not a formal proof assistant
check or a line-by-line independent reimplementation of the entire C++ core.
It does not independently requalify every historical Native call or reproduce
commercial runtime measurements. Ordinary positive-objective certificates
remain numerical under the explicitly stated tolerance/source policy.

The mathematical roles are defensible, but do not establish a new general
product-hull theorem or an independent outer-scheduling performance gain.
Current root-only controls leave that incremental architecture value open.
The finite evidence supports discussing the integrated exact method as a
research contribution; it supplies no acceptance prediction or requirement
to run another favorable experiment.

## Post-correction closure

Targeted readback completed at 2026-11-12T20:44:45Z (13 November locally).
Appendix source line 177 now explicitly includes inventory balance (A10),
and line 365 identifies the historical pre-repair writer and the corrected
current writer. Both corrections are also present in the actual final
manuscript PDF: A1/inventory balance on page 31 and the pre-repair/current
writer distinction on page 36. The final manuscript has 52 pages. Both
findings are closed; mathematical/implementation disposition is **PASS**
within the scope above. No solver, compilation or repeated historical audit
was performed for this closure.

Final identities read back:

- Complete appendix source SHA256: `5c36c8ee9fcc819f6ac41adbb7e91d517bbbd51e1fd2b654193d7671c2d987b6`.
- Main source SHA256: `eaed6620eafb6e85619480e556562a9dfd58447dec0bc0224c884500a54e1dbf`.
- Assembled Markdown SHA256: `ac744776fa17a6049dbf75c764aac17dc7a74f0eaad1b2f69664d7947aa0ca37`.
- Actual manuscript PDF SHA256: `3b24cdd828e666cb491dcb7a421889fdc4623eb05a2fe6b7a9087d290957dc71`.
