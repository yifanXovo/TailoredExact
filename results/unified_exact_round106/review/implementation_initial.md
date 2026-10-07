# Round106 independent initial implementation review

**Verdict: HOLD for formal performance.** Static review supports proceeding to charged native qualification. No R106 native callback/deadline qualification was represented as observed by this reviewer at this stage. Mathematics is independently accepted in `history_mathematics.md`; formal admission requires a separate frozen-source, PE/DLL-bound gate record.

Reviewed source identities:

| Source | SHA256 |
|---|---|
| `src/Round106Events.cpp` | `c8ad10f87de50557c60ffade40eeba5827f5c67d821cc7159f92b127e4f56fe0` |
| `src/Round106GurobiEvents.inc` | `a4dbeb1706f4a708f475e432de9112dc4218204325df311997db4867913a7187` |
| `src/Round105GurobiDecomposition.inc` | `bf6313e611acb370b2bfe4356c4715948abb2f3b3c8a5e9ff6d549ef848993ec` |
| `src/GurobiBaseline.cpp` | `141727685b374460e410784bb309fc10534e1ec561fc50361e9877fc974a1d28` |

The first static version raised five actionable issues. Subsequent source inspection confirms these repairs: (1) lower-bound promotion is staged until the final native reads pass and restored to zero in both internal and outer exception paths; (2) startup fleet identity is distinct from vector identity when counting the first new physical candidate; (3) callback-other timing excludes separately reported separation/audit and inner native intervals; (4) final native-bound qualification additionally restricts native status; (5) R106 explicitly rejects NUMERIC status and IIS API/numerical errors, while the inherited R105 switches remain off by default. These repairs require qualification of the corresponding compiled version.

The remaining reviewed flow has the intended architecture: one outer Optimize; independently owned inner environment; actual MIPSOL_SOL/OBJ/OBJBND; base-row/domain/integrality and unique-service mapping audit before learning; high epigraph values allowed, below-true-F values stopped; all-car arithmetic before new native oracles; separate local FEAS/INF caches keyed by physical mode; only raw, reliably violated rows sent via lazy, including repeated submission of old violated rows; compatible cross-car A rows retained in the pool until actually violated; complete verified route combinations alone create own physical UB; full canonical cbsolution mapping and per-fleet deduplication; UNKNOWN triggers safe termination; post-termination pending-candidate final bound is disallowed, while previously observed callback global bounds remain provisional until post-return numerical qualification. Errors prevent current-run promotion.

The installed header is Gurobi 13.0.2. The official [C callback documentation](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html) confirms that lazy calls themselves reject a current solution, previously added lazy rows can need resubmission, LazyConstraints must be set, and cbsolution can defer processing at MIPSOL. [Callback codes](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/callbacks.html) distinguish the new solution vector/objective from global objective bounds. These semantics support the static choices but do not demonstrate platform execution. Termination is a request, so the UNKNOWN final-bound exclusion is necessary.

Formal admission requires actual evidence of the current production PE/DLL/numeric contract; mathematical production A/B replay and legal Start retention; real MIPSOL snapshot auditing; high-epigraph acceptance and below-F/base/domain failure behavior; raw-only and repeated lazy behavior; full/core/struct strategy separation; FEAS witness/cbsolution mapping and finite progress; actual independent-environment nested solve; master/inner and, when invoked, IIS/core deadline cancellation with no calls begun after the deadline; and post-return numerical/bound gating. Same-engine re-solving of a retained model may qualify a path but is not independent model or performance reproduction. A future finite formal panel must use the admitted frozen version and can only claim tested scope.

Reviewer native starts, Optimize calls and IIS calls: zero.
