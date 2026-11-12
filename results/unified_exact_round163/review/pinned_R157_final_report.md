# Physical realization of near-optimal inventories

The best RX35 objective-invariant six-member inventory family is impossible under the original 6300-second fleet limit. NB35 remains UNKNOWN. These are original physical-scope conclusions, not new complete-algorithm runs. The bounded propagation study below separates the family proof from any global original-objective lower.

## Original objects and preselection

All calls use the exact R156 E+ root scopes, original inputs and physical parameters. Coefficient classes compare the actual binary c and omega exactly; H already contains lambda. The best and second distinct families were selected before any route results. RX35 has 6 and 20 members; NB35 has 1 and 21. All Native solves use Seed0/Threads1. No original-T routing solve is made for K20: its historical physical lower already excludes its low-price inventory offline, whereas its first LP does not justify an early online free gate.

| Role | Inventory lower | Best saved inventory price | Inherited physical U | Inherited physical proof L |
|---|---:|---:|---:|---:|
| N-B35-S | 0.3959564087240911 | 0.39604654895666136 | 0.45029150326287798 | 0.3959564087240911 |
| R-X35-S-T2 | 0.23605210290745571 | 0.23612171136420015 | 0.29966940073640169 | 0.23605210290745571 |

The inherited endpoints are fixed accepted evidence. This round does not rename them as fresh E+ arms. Input/source/member references and the reused interpreter/DLL/PE identities are in reuse_index.json and source_manifest.json.

## Free-fleet physical queries and resource explanation

The full interface fixes only the permitted inventory states, retaining all vehicle assignments, route order, pickups/deliveries and prefix loads. Vehicles leave empty; depot placeholder inventory supplies nothing. Heterogeneous Q, one nonzero one-direction station service, loaded return and charged unloading retain original semantics. Arc-flow loads and ordering potentials give the same integer fleet projection.

At4096 nodes the fixed best-inventory calls return UNKNOWN without a route: RX35 costs 1507.1708263999317 outer seconds (Work 3174.113950665848), NB35 costs 1285.9010457000695 (Work 2612.915696198856). UNKNOWN changes no physical bound. NB35 is a singleton, so its fixed and family queries are identical and are not duplicated.

A free-assignment necessary resource model covers every member of RX35's best family. Its qualified Native required-time lower is 6300.62843442681969; subtracting margin0.063 leaves6300.56543442681959, still strictly above 6300. All6 members, including the fixed original, are therefore impossible. The resource call costs 181.39043179992586 outer seconds, 1320 nodes and Work 264.6189244769806. Comparing this cost to the fixed full-fleet call compares formulations; it does not isolate an effect of symmetry freedom.

The explanation is per-vehicle pickup/delivery balance, handling and exact-downward-rounded one/two/three-station tour bounds. Every member preserves the initial total inventory, forcing zero vehicle returns and P_k=D_k. Largest individual service7 is below min Q20, so the individual assignment-capacity filter is inactive. Exact route order and prefix loads are unnecessary for this exclusion. The separate aggregate metric-tour/handling lower 17793.65053263172 is below 3T=18900 and cannot exclude this family.

NB35's resource call instead has guarded time lower 6993.96882192581234<7200 at 4096 nodes. Its relaxed upper 7245.92316320239843 is not a true fleet-time upper. It remains UNKNOWN after 217.8038693999406 outer seconds and Work 312.7224270801549.

Solver-free complete load-feasible fleets at relaxed time limits are independently checked by the existing R107 physical reader. They supply true T* uppers only; none fits the original time limit. The resulting intervals are in reports/physical_scope_intervals.csv. They must not be confused with the smaller resource-relaxation uppers.

## Whole-domain deepening and bounded propagation

The main deepening appends those necessary resource conditions to the unchanged original normalized RN inventory formulation across all original supported inventories. An actual full-matrix lift validates the projection. A known valid original inventory lower is a legal helper row; a checked physical route is an unfixed MIP start and a legal upper of the strengthened domain. The excluded old best inventory is not reused as an upper. Original-J inventory hints select levels only.

The first cold call is stopped after 256.5245488001965 seconds to add the available prior lower and physical-route start. The revised call is stopped after 4099.307925999863 seconds: at least 774 displayed nodes appear in the sealed log (the earlier report of 773 was an earlier observation), its reported global bound remains at the prior floor, and per-node cost rises. Optimize did not return, so neither a final NodeCount nor final Work is available. This is an explicit early reallocation before the proposed1024-node checkpoint, not exhaustion of 16384 nodes or6 hours. Both failed exit receipts, PID/birth identity, logs, models and exact executed source bytes are retained and charged. No final Work, new bound or infeasibility proof is inferred from these unfinished logs.

The preselected second RX35 family is then queried with the same4096-node/900-second necessary model. Actual result: RESOURCE_INFEAS, Native status 11, nodes 1141.0, Work 275.81886417406804, Native time lower 6300.45285949651, relaxed upper 6804.046366824461. A resource-feasible point would still require a separately checked full fleet. No fixed assignment failure is allowed to exclude the stock.

Exactly one finite batch excludes 26 member vectors in 2 fully proved families, followed by one original RN repricing. Each exact member no-good is sum_i x[i,Y_i]<=n-1. All untouched RN rows/columns/objective are identical; the prior qualified lower row is retained. Revalidation selects a nonexcluded stock with original price 0.23685400930608239 as the new-domain inventory upper. It is not a physical upper.

The returned qualified original-objective lower is 0.23605210290745571; the selected level 0.23648786033514127 is not excluded. Native status 8, nodes 16384.0, Work 437.27086304962415. All original physical inventories project into the retained pricing domain because the removed finite families have qualified original-T impossibility proofs. Coverage of the incumbent complement follows the inherited original root-scope rule.

Relative to the old E+ lower, this finite batch's maximum possible increment is 0.00080190639862665124, bounded by the checked retained inventory. This ceiling applies to the tested finite exclusion batch, not to every possible resource strengthening or route algorithm. The actual global increment is 0. A positive physical-versus-original-inventory separation is certified only to the extent max(0,new_L-old_U)=0.

## Complete candidate and stopping decision

Do not freeze a complete E+R candidate. The two preselected RX35 families have meaningful original-T resource impossibility proofs, but they supply no physical route. One finite 26-member exclusion/repricing batch returns at 16384 nodes with no global lower gain and does not exclude its selected level. The full-inventory resource diagnostic also stalls at the prior floor despite the valid prior lower and known-route start. The checked retained inventory caps this finite batch's possible increment at 0.0008019063986266512, about 1.26% of the inherited physical gap, whereas its two resource proofs plus repricing already cost 572.2466407998 outer seconds before qualifications. There is no demonstrated useful and plausibly affordable uniform mechanism for a fresh self-paid complete method. The conditional panel is therefore not started. Further route/global-level questions remain open; the 60-hour capacity is a ceiling, not a reason to repeat a stalled mechanism.

No complete E+R candidate is frozen and the conditional eight-arm panel is not started. There is no new C++ build, PE execution or complete-method performance claim. Stable GI-TBC/B remains the default; E/E+ retain their inherited research status. This finite outcome answers the physical-family question and exposes a global propagation bottleneck without importing offline stocks, routes or proofs into a nominally fresh complete method.

## Qualification, paper and reproducibility

New tests cover full actual positive-route lifts, 8 exhaustive tiny ordered-partition cases (heterogeneous capacities, loaded return/unload, zero and depot supply), exact family freedom, 64 tiny tour checks, metric shortcut and lazy subtour qualification, a tiny full-level resource gap, and actual forbidden/retained points in the saved finite-batch MPS matrices. Existing solver/physical policies are reused. Final review uses same-agent separate reconstruction routines; no separate human, subagent or independent timestamp is claimed.

The thematic manuscript connects integer-objective proof consumption to physical realization, states the invariance/projection/coverage arguments, gives the actual obstruction and unresolved outcomes, and preserves classical no-good/Benders attribution. docs/paper_review.md links it as a supplement to the maintained stable GI-TBC paper lineage. The PDF is rendered and visually reviewed page by page; the QA receipt records the actual check.

New-only indexed carriers retain models, solutions, logs, qualifications, exact source snapshots, fees and failures. Old inputs and large evidence are fixed commit/member/hash references and are not repacked or rerun. One anonymous fixed-commit public restore checks new byte sizes, hashes and members without Optimize or compilation. Its actual receipt, PR readback and zero-delete cleanup are delivery metadata recorded in RESUME, not assumed by this scientific report.

## Actual fees and limits

The closed scientific outer total at this report is 7969.8252387005 seconds (2.213840 hours), within the 216000-second capacity. Runtime, Work and helper/H costs nested inside those outers are not added twice. Later final verification fees, if any, remain authoritative in cost_report.json. Compilation, pure writing and public I/O are separate; initial tool-only metadata/worktree setup was not outer-metered and no estimate is fabricated.

All scientific outer intervals are serial. The ledger retains 3 failed children: two intentionally stopped diagnostics with no consumed proof and a 0.03179570008069277-second provenance-script syntax error. The latter was corrected before the successful provenance/AST closure check; it changes no scientific model or bound. Protected original/paper-current tracked dirty bytes are checked against the initial snapshot. No original history, user changes, old branch or active unrelated tree is deleted.
