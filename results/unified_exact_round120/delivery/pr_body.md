M-B already pays for the two initial root-child LPs, but their interval objective bounds are not explicitly available inside the subsequent native MIP. This experiment adds one ordinary binary selector and three static linear rows **before the first root integer Optimize**, using only that arm's returned OPTIMAL root proofs. MB-D1 retains the conditional floor; the necessary MB-D0 ablation uses the same selector, two links and common scalar floor. There is no new ordinary proof-crossing abort, external contraction, extra probe or Optimize request.

**Stage: ADVANCE_NATIVE_PROOF_DISJUNCTION_TO_CONFIRMATION.** This supports a fixed confirmation only. ENS-C remains default, both new flags are default-off, and R119 MB-PC remains stopped. This is a small native formulation experiment, not a claim of a generally superior single-tree architecture or new convexification theory.

### Complete current-build evidence

All eight core and all four admitted N40 positions completed once, in the frozen order and caps. All use PE `5471f9c199c016e26178e6fc83aba42e5d2e1ee797735d68a864dbada4c7cbba` and Gurobi 13.0.2 DLL `9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88`, Threads=1, Seed=0, PresolveAuto, original tolerances/evidence policy and self-paid full 24+1 H. No diagnostic or historical incumbent, bound or Start entered a formal arm.

| Role | P-GRB U / L | M-B U / L | MB-D0 U / L | MB-D1 U / L |
|---|---|---|---|---|
| F2 | .8659435203 / .7621151437, open | .8659435203 / .8659435175, certified | .8659435203 / .8659434978, certified | .8659435203 / .8659435203, certified |
| R98-C2 | .1983028486 / .1866225684, open | .1946348157 / .1906619659, open | .2159404830 / .1900472132, open | .2073016379 / .1895141275, open |
| N40-R1-S | .8837281542 / .3511463954, open | .7822196776 / .5736442340, open | .7884056617 / .5698623843, open | .7551659800 / .5693519797, open |

- F2: the same nonzero original-problem numerical certificate takes T_produce 208.145s for D1, 476.408s for D0 and 774.409s for M-B. These are one known-role comparisons, not universal acceleration rates. P remains open in its 1200s cap.
- C2: D1/D0 is WIN, but D1/M-B is **severe LOSS** and D1/P is nonsevere LOSS under the unchanged rules. D0 also loses severely to M-B and P. This risk is retained, not hidden by the F2 result.
- All seven predeclared core admission conditions hold, including actual D1 exposure, a conditional-information WIN, preserved M-B certificate count and no severe primary-P regression. The explicit gate permits this finite trade; no extra veto or post-result variant was introduced.
- N40: D1 wins the open U/gap comparisons against M-B, P and D0. Its L is lower than M-B's; the improvement does not close a V40 proof. N40 is a known difficult follow-up, not an independent sample. D0/M-B is TIE.
- Each role's complete six pairs, signed gaps, all three clocks, original/native/extended dimensions, H/LP/MIP/installation costs and every actual native request are in the scientific report and raw reconstruction. There is no E50, additional input/Seed/window, production revision, formal retry or D0 promotion.

### Mathematical and native qualification

The contract uses `min(returned LP bound, source proof cutoff)`, the unchanged 1e-7 evidence margin and conservative actual serialized endpoint sums. It includes the complete native linear objective and actual constant. A physical solution embeds with model g=true G and deterministic h; model g can otherwise be an epigraph completion. The new rows can remove virtual-g auxiliary completions, so they are pre-Optimize formulation rows, not callback user cuts or lazy constraints.

Both complete diagnostic LPs have equal D0/D1 original objective minima, yet their full D0 feasible primal points violate the actual D1 conditional row by .1036854724 (F2) and .0317618299 (C2). All original route/resource/inventory rows and bounds are retained and checked. This is full-LP nonredundancy, not an observed root-objective gain or a claim about the full BRP integer hull.

Qualification includes independent complete tiny physical enumeration, 18 actual full-matrix embeddings, source-cutoff/boundary/rounding cases, LP-to-MIP type restoration, complete Start submission/readback including same-SHA distinct states, one real C++ chain with three original LPs plus one extended MIP certifying nonzero 1.2, and six final-PE H100 CLI positions. All full H comparisons agree. Every formal D0/D1 arm installs one root selector and completes its original target/terminal requests using the extended identity. h fixing/branching and whole-tree retention remain unknown; a MIPSOL objective sample alone is not evidence of acceptance or cutoff propagation.

The R119 original-core zero-Optimize physical-tail supplement passes in R120 while retaining the original failed R119 test. The first new qualification failed a synthetic LP-text objective-offset expectation. Its raw files and charge remain; corrected actual ObjCon/API/MPS qualification then passed with the production PE unchanged. Natural production ObjCon is zero; the synthetic MPS offset test is not a claim that the failed bare LP-text offset round-trip worked.

### Review, budget and recovery scope

The run uses **31/40 conservative starts and 32358.098362/48000 outer seconds**; qualification uses **16/16 and 817.811069/3600**. Failed starts and necessary supervision/verification are charged, with nested native time counted once. Compilation, pure mathematics and publication/recovery are separately scoped engineering receipts; human time is unknown.

A separately spawned executor (`/root/round120_extra_review`) wrote a new stdlib-only implementation and actually checked complete tiny physical enumeration, full LP/MPS matrices and primal vectors, full Starts, exact serialized endpoint sums, all 18 classifications/severities, all clocks and closed fees. It found no blocking defect within that saved-data/source scope. Its 19.2215583s pure audit plus a 0.0604467s tiny MPS recheck used zero Optimize/new native starts. The failed LP-text fixture, C2 severe M-B loss, all-open N40 and unknown native h fixing remain explicit. This is not independent third-party native reproduction; prior inspection/implementation time is unmeasured and human time unknown. Detailed review receipts are outside the scientific carrier.

The scientific carrier at `75c4839f3b85f67f8eeb6c4700e0452d5204dd51` passed actual staged and full decompressed-member scans. One actual Git archive and one initially empty restore verified all 52,267 member hashes. The original comparison runner completed group01, then incorrectly compared in-memory H tuples with stored JSON arrays; its failed attempt and cost scope are retained. A separately published post-recovery receipt recipe preserves that output and completes groups02/03 in the same restored root using the unchanged frozen reader/helpers. Every stored JSON field in all 12 arms/18 pairs, complete H, Starts, proofs and the seven admission conditions agrees after only absolute root-prefix normalization. No field is removed, no second export occurs, and no native PE/DLL or original-evidence fallback is used. The recipe is explicitly outside the scientific carrier; `safe_restore.md` documents this distinction and the reproducible command.

The separate executor also independently repeated the complete typed stored-JSON comparison and admission arithmetic, finding zero field differences. It identified six derived event-contract sidecars refreshed by the unchanged reader with restored-root paths; 132 other compared sidecars, including all 12 call-log views, remain byte-identical. Initial unpack hash equality is not a claim of every expanded file remaining byte-identical after reconstruction. An append-only scope clarification qualifies the original receipt's broad evidence-unchanged boolean, retaining the executed receipt/recipe SHA. The open-path and module-origin checks use a runtime installation prefix and are not an OS sandbox.

The scientific carrier contains necessary safe current raw files, source and finite named schema/history authorities. It excludes PE/DLL, licenses, credentials, cookies, runtime HTML and earlier campaigns/carriers. Actual staged bytes and complete decompressed carrier members are scanned. Later review, Git export/empty-root recovery and remote publication receipts are separate from the scientific payload they examine; this does not attest all Git history or an independent native reproduction.

Scientific report: [complete current-build results](https://github.com/yifanXovo/TailoredExact/blob/75c4839f3b85f67f8eeb6c4700e0452d5204dd51/results/unified_exact_round120/final_report.md).

Stacked on the verified R119 research branch/PR181. Draft only; no merge or default change.
