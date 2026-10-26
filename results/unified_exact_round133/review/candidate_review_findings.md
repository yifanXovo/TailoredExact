# Candidate review findings before D admission

This file records implementation-review findings as they arise. It is not
an admission decision; the final source, build and reader hashes must be
reviewed separately after all corrections and required tests.

| Finding | Required correction and current review scope |
|---|---|
| Missing finite native bound was replaced by a synthetic zero in a scope check, allowing native INFEASIBLE to retain closure status | Separate scope, bound and infeasibility predicates. The implementation now has `localScope`, `localBound`, `localInfeasibility` and a raw infeasible event. Final frozen review remains required. |
| A later witness could refute an earlier INFEASIBLE call with no recorded finite bound, while the observer only rescanned historical finite maxima | Store an explicit per-call infeasibility claim and recheck it for every later verified witness. The implementation now includes that latch; a targeted late-witness fixture is required. |
| C6 target return closed on native OPTIMAL before reaching the terminal physical-gap logic | Reuse the same physical-gap-open predicate in the actual C6 early-return path. The implementation now checks it before closure, retaining an explicit open reason without fabricating a deadline. |
| An intermediate C6 edit referred to an out-of-scope terminal-decision variable | Replace the duplicate edit with the common target/terminal gap predicate before build. This was a development finding, not a native experiment failure. |
| Adding a string to `NativeEvidenceScope` changed the embedded `FixedIntervalMipRequest` layout despite reuse of older objects | Primary implementer plans to retain the original scope/request layout, encode the controlled qualification reason inside existing settings JSON, and verify old/new ABI sizes/offsets. No D admission before the actual ABI evidence. |
| Qualified conditional native values were still being offered as unconditional region lower bounds | Check raw counterexamples first, then apply the proved cutoff complement `min(b,c)` only for a cut model. Preserve raw values independently. Trace `min(U)` is not a substitute for this local mathematical contract. |
| Old global-cover evaluators expanded physical witness membership by the objective margin while new local qualification did not | Make the new producer and future-reader physical-domain predicates agree; do not change historical readers or fill a cover gap by tolerance. |
| The reader initially converted INFEASIBLE only to the valid finite cutoff floor | Independently adjudicate the stronger infeasibility source against all same-run witnesses, including later and sealed-return witnesses. A legal floor cannot hide a contradicted infeasibility source. |
| The future reader initially stored native quality records without independently recomputing the producer's known-violation rejection condition | Recompute the same LP/MIP/solution-count conditions and retain unavailable attributes as unknown. Parameter/local/global claims require independent reconciliation, not mere trust in source booleans. |
| Schema1 gained fields and postreturn event kinds | Require explicit new policy/version semantics and tests for interrupted/missing tails, duplicate/lost/out-of-order events and content identity. Preserve Optimize-return and final qualified-evidence time separately. |
| The inherited MS2 factory can emit a proof-only constant infeasibility row when its analytic no-improver floor reaches the cutoff | `IntervalRowFactory.cpp` emits `0<=-1` with tag `interval_no_improver_domain_closure`; `Round127Research.hpp` explicitly distinguishes this from a row valid on the inclusive `F<=c` set. A native INFEASIBLE observation from this intentionally empty model is not automatically a numerical contradiction if an objective-boundary witness exists. The analytic floor, the model's actual embedding scope and the native status must have distinct provenance. This semantic issue was identified after the provisional source-only review and must be resolved or explicitly retained as a D-admission blocker. D24's proved feasible matrix and C03's inclusive S2R matrix do not contain this issue. |

Changes found during development do not establish failures in historical
performance arms. Original R132 bytes, source identities and formal
denominators remain fixed. Native diagnostic reruns, if any, have their own
new identity and costs and cannot overwrite those observations.

The earlier `pre_freeze_static_review.json` was explicitly provisional. It
predates the last proof-only closure observation above and must not be used
as a final statement that the inclusive-domain embedding has been verified.
