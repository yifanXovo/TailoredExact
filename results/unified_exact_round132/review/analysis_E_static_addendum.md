# Round132 independent static addendum: analysis and E guards

Scope: source and small frozen-plan review only, during the serial D campaign. This is not final acceptance of experiment results. The reviewer did not run the analyzer, traverse arm raw files, enumerate E, construct/export a native model, call H/Optimize, compile, or load a solver DLL/PE.

Reviewed inputs:

| Input | SHA256 |
|---|---|
| `scripts/round132_analysis.py` | `e03c7f3cbadb2b063b532fe6e1bdbe0fb9cffd082967f02cdfdd9ff5f6f83b34` |
| `scripts/round132_joint.py` | `856e95e2753f2229ecbf9054dc0334093e612ba6c78ba5e7f576827cbf2812d5` |
| `E_experiment_plan.json` | `db2bc424d315ad770099d25d525b2736cfa0476569120006d7003cb49e6bb6d1` |
| `experiment_plan.json` | `f73f89ff1cc5ec2e2772a30e63b7c5d9b23d6a34362879d5cac1067c0e3f63ee` |
| `C_experiment_plan.json` | `91040549bf094368483faad90ebdf5eb2825202795fe14b241100b9a6b169fa5` |

## Static findings for the analysis adapter

1. **Pair source identity is not yet checked at the join.** At lines130–145, reconstructed arms and identity launches are joined by equal length and `zip`, then method and formal-membership labels are overwritten. The later inherited pair check establishes equality between the two joined arms' PE/DLL/input/Seed, but it does not establish equality with the frozen group/launch. A substituted same-input Seed0/Seed1 group could retain matching left/right identities and receive the other group's reporting Seed. The loader should bind the small plan/argv/execution-binding chain, group identity, and each arm's `(id,input_SHA,seed,destination,underlying method)` before assigning comparison labels. C additionally needs unique `comparison_method` for its three expressions. Hash indexes of the actual reconstructed and identity inputs should accompany derived tables.

2. **Invalid records cannot always reach `UNEVALUABLE`.** `signed_gap=a['U']-a['L']`, certificate-time assertions, and `physical()` occur before pair classification. Missing numerical endpoints or physical evidence can therefore abort the entire analysis rather than preserve the failed observation with a reason and mark its pairs `UNEVALUABLE`. Such an abort is safe against a false positive, but it is not a complete failure census. Do not rerun formal arms to repair their scientific outcome; retain the invalid observation and separate the failure from valid negative results.

3. **Final-mode completeness and cost closure need an explicit gate.** The current final-mode assertion checks60D,24C and64typed pairs. The accounting record deliberately excludes active, not-yet-closed fees. That convention is appropriate for partial progress but cannot by itself qualify final G1 accounting. The final verification/report step must require all expected production/qualification/E/repair fees closed, identify measured disjoint verification/delivery segments, and check category/global limits. The final entry should distinguish C/D completion from completion of the whole task.

The following static conventions are appropriate: candidate is the left arm and baseline is the right arm; the ratio is right certification time divided by left certification time only on the explicit both-certified intersection; one-sided certificates and both-open censoring retain separate classes; signed `U-L` is not clipped; repeated Seeds and shared controls are explicitly not independent samples. D has48typed comparisons and C16, for64total. K/X, problem, scale, attained zero/positive endpoint, and D layer-by-scale strata are present. The objective-class field explicitly describes the arm's attained physical objective rather than asserting an unproved optimum class.

The added cross-arm bound check is a consistency diagnostic. It does not transfer an incumbent, bound, or certificate into another arm. Raw trajectory sources are indexed without inventing common-time data. Canonical continuous LP bounds, native MIP initial root relaxation, and unavailable post-cut/Work fields remain separate. Native LP/MIP counters are taken from their respective ledgers; H-plus-admission time is a prefix measurement and is not added again to `T_produce`.

## Derived resource correction

The previous resource-table helper accumulated vehicle load in the serialized `operations` array order, although that array can be in station order. The reviewed helper now maps operations by station and traverses `route.nodes`; it checks each prefix against `[0,Q]` and checks the final inventory/returned-load conservation. This is the correct order for a route resource table. The existing independent physical reader already traversed the route when validating feasibility. This local derived-table correction therefore changes neither the native experiments nor their existing independent physical-feasibility evidence.

## E guard increment

`run()` now checks idle state and the frozen original assets, then writes `joint/identity.json` with actual asset, plan, runner and source identities before enumeration. This resolves E-F6's requested identity closure. An `INFEASIBLE` return at each event-control, support, original-objective, or full-joint stage now writes a contradiction and stops; a known empty-fleet embedding means such a return cannot be silently called a negative separation result. This makes E-F7's failure handling explicit.

These increments do not change the four micro universes, retained reference rows,64fixed normals,8event controls, objective comparisons, or budgets. The original finite E execution scope remains accepted. A finite failure to separate is not hull equivalence. Numerical candidates are not strict rational witnesses. Exact tiny joint threshold ranks are not identified with historical R101 necessary-resource ranks. Tiny results alone do not admit E2–4 for a real role with omitted outside supply/demand.

## Remaining final requirements

Execution evidence remains pending:84sealed current observations with their own identity/physical/model/Start/source-cover qualifications; independent reconstruction of64typed comparisons and stated denominators; complete C matrix/domain and own-H qualification chain; E's actual status, exhaustive universe/support verification and any strict full-matrix witness; closed category/global accounting including failed qualification attempts; manuscript/math/numerical distinctions, rendered PDF, authoritative current evidence identities, draft PR and the bounded public empty-root restoration. This addendum does not certify those future artifacts or any performance conclusion. The requested portable read-only checker will use the same entry for the later internal final review and the one bounded public recovery, with distinct invocation receipts and no solver execution.
