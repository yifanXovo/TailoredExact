# Round63 — cumulative route duration and service projection

The bounded experimental campaign is complete. The cumulative-resource
implementation is valid and has isolated C2/D7 benefits, but its uniform
root candidate fails D4/C3 protection and C5 confirmation. Service projection
also fails C3 protection. All new mechanisms remain default off; the results
support a research prototype, not stable-mainline promotion.

## Baseline and interpretation

The new branch starts at Round62 PR #123 head
`71e955acad596acba2a9e74e738173113116d9f7`, not at main. Round62's principal
measured v3 implementation is `7936ed53951113297df07d2fb243954e2f784906`;
its measurements are historical context only. The original dirty workspace
at `4a9cbd0e3d43870e953b3a6678b343a9ac4fc25a` remains untouched.
See [restoration.json](restoration.json) for the checked identities and
[protocol.json](protocol.json) for the predeclared panel and gates.

All new mechanisms default off. The original objective, S=0 convention,
weights, empty departure, loaded return, capacity prefixes and final route
duration are retained. Total route pickup is not bounded by vehicle capacity.
Core resource arms disable threshold projections, candidate submission,
archive and PREFIX. Stable K1-H and official P-GRB keep their own inherited
startup contracts. Gurobi 13.0.2 uses one thread, Seed=0, Presolve=Auto and
zero requested relative/absolute MIP gaps. Numerical certificate tolerances
are unchanged; a strict certificate need not have a printed zero residual.

Service work A was measured on v3
`b1bde3eab6c6fb9c4e1c4575acbdfa9141a46eaf`; final resource work uses v4
`dc8d3e4a0ee3f63f0858b2c3b38a59a92cd1e783`. Earlier v1/v2 measurements remain
identified separately. No timing pair combines executable hashes. The actual
first-class K1 closure threshold is tau=0.08, K0=1; the legacy C6 metadata
rho=0.01 is a different compatibility field. Decision ledgers and parameter
readbacks, rather than that misleading generic field, establish the contract.

## A: finite service-projection qualification

Nine 600-second launches compare OFF, unchanged inventory projection and
unchanged service projection. D3/D4 use full Single-S; C3 uses full K1.

| Role | OFF | Inventory | Service | Service versus actual OFF |
| --- | ---: | ---: | ---: | --- |
| D3, certified wall seconds | 316.047 | 462.531 | 308.843 | Protected; 7.204 s / 2.28% gain is below both-gate qualification |
| D4, certified wall seconds | 90.140 | 55.109 | 78.547 | 11.593 s / 12.86% qualifying gain |
| C3, uncertified absolute gap | 0.098527844 | 0.105832492 | 0.110074793 | 0.011546949 / 11.72% material regression |

Service repairs the inventory arm's observed D3 slowdown in this lifecycle
and has real D4 value despite being slower than inventory there. It still
fails the uniform protection gate on C3. Keep it as a default-off research
option, not a promoted uniform candidate or a demonstrated combination.
Stop A at nine launches: an additional C2 success could not remove the C3
failure. Service confirmation and A+B combinations were deliberately not
opened. This does not rewrite Round62's failed historical qualification or
turn mathematical dominance into a speed guarantee.

## B: implemented cumulative resource and actual strength

[mathematics.md](mathematics.md) proves an integer embedding using accumulated
original travel and prepaid pickup-plus-drop cost, including pickup totals
above Q, loaded returns, heterogeneous Q and directed nonmetric costs.
It also proves the exact continuous projection of the explicit flow block
by all subset inequalities and standard maxflow/mincut duality. The numerical
implementation is a conservative relaxation using safely rounded physical
coefficients; candidate rows are verified on unmodified raw LP values.

The explicit extension adds M*V^2 continuous columns and M*(V^2+V) rows.
It retains every original physical block. Projected rows use only original
x/p variables and are global across intervals and incumbent epochs. The
existing connectivity flow transports visit mass, and inventory-route rows
use inventory/capacity quantities; neither constitutes this duration
accounting. The optional historical IR root closures are off in core F0.
The algebraic comparison and real optimal F0 witnesses distinguish these
claims without pretending to prove containment of every historical model.

| Role | F0 objective LP | Simple rows | Explicit flow | Bounded closure | Closed? |
| --- | ---: | ---: | ---: | ---: | --- |
| D3 | 0.020550011 | 0.020550011 | 0.020550011 | 0.020550011 | Yes |
| D4 | 0.093948255 | 0.256875851 | 0.262943554 | 0.262943554 | Yes |
| D6 | 0.125691831 | 0.125691831 | 0.125691831 | 0.125691831 | Yes |
| D7 | 0.175143185 | 0.175143185 | 0.175143185 | 0.175143185 | No; 120 s cap |

The W=N special case strengthens the old duration row with fractional
vehicle activation; singleton rows give local resource coupling. They
explain most, but not all, of D4's objective improvement. D6/D7 also have
violated multi-station proper subsets after the simple rows: D6 includes
supports of 16 and 18 stations; D7 includes 31, 8 and 16. Thus long-T
feasible-region strength exists even though the tested long-T objective
LP bounds do not rise. This does not establish proof-tail acceleration.

The closed D3/D4/D6 points pass raw nonnegativity and residual checks, with
zero final selected raw violation. D7 uses 36 optimizations, 148 maxflows
and 106 accepted rows in 117.437 seconds and still has a substantial
residual violation. It is an interrupted subset relaxation, not a completed
projection-equivalence computation. [strength_tables.md](strength_tables.md)
and the independent audit contain support/activity and cost details.

## Execution alternatives and reasons for stopping

The shared deterministic Dinic code was extracted from the existing
inventory-route implementation. Dynamic separation is bounded to 64
queries and 256 submitted rows per MIP, at most 16 root queries and then
one eligible tree sample per 64 nodes. Each query uses at most one graph
and support per vehicle; no optimizer runs inside the callback. Raw vectors
are read only while the budget remains. API success is submission evidence,
not an independently observed count of adopted cuts. D4 reports 57 successful
submissions and an aggregate native `User: 23` summary; those counts differ.
D7's native summary omits that category, so its adopted count is recorded as
unavailable rather than inferred from the 40 API successes.

The 120-second OFF/PreCrush-only/dry/real-cut isolation gives no robust net
gain. On D7, PreCrush-only and dry have identical endpoints, while real cuts
worsen the absolute gap from 0.311120909 to 0.364258002. The diagnostic repeat
locates a raw x=-2.51524e-8 below the frozen -1e-8 graph-input guard after 40
successful submissions. The optional separator stops safely; original rows
remain. The guard was not relaxed. On D4, dynamic cuts certify in 95.890 s
versus OFF's 90.125 s, below the material-regression gate but without gain.
Therefore this dynamic execution is not advanced to full confirmation.

The root variant observes the first required optimal LP and selects at most
M global rows once. It adds them only to MIPs and does no LP closure.
The fixed harness pays an extra preparation LP; full algorithms reuse their
already required LP. Root and root-dry both read fresh canonical models per
native call to keep static MIP rows out of later LPs. Their comparison
isolates row insertion from that common lifecycle change. The v2 full-K1
micro exposed a retained-model row guard failure; it is charged and excluded.
The v3 fix passes a full-K1 micro with three LP calls and one MIP, without
changing PreCrush or invoking extra optimizers.

Long D4 protection on v4 certifies OFF/explicit/root in
90.141/136.469/121.391 seconds. Explicit and root regress by 51.4% and 34.7%
against actual OFF. Their correct integration therefore does not qualify
either for promotion, regardless of any later development or confirmation
gain. A uniform candidate still completes the prescribed diagnostic
full-K1 and confirmation work.
The three D4 root supports have sizes 8, 7 and 8 out of 12 stations: the
regression also occurs with genuine proper subsets, not only simple cases.

The alternative B4 adds valid carried-load lower bounds
`(c/scale)*load_ki <= sum_j f_kij` to the explicit extension. This couples
the existing post-service load to accumulated pickup resource, using M*V
extra rows and no further variables. The simple mincut equivalence is not
claimed for these added node-throughput requirements. On D6 and D7, four
LP calls each find no objective gain, no violation at the explicit optimum,
and feasibility of both pinned old-variable explicit/coupled controls.
Independent residual and pin checks pass. A same-v4 D7 120-second MIP pair
worsens gap from 0.169525735 to 0.582633885, predominantly through primal
quality. Stop B4 after these diagnostics; no full-K1 or confirmation benefit
is claimed. This is a tested alternative, not just an interface or proposal.

## Full algorithms, frozen confirmation and references

Full K1 C2 supplies a nontrivial multi-call role: OFF/root-dry each make
three LPs, a target-bound interrupted MIP and a terminal MIP. Explicit/root
each make six LPs and those two MIP roles after native evidence triggers the
unchanged controller's re-evaluation. Thus actual totals are 5/8/5/8 calls
for OFF/explicit/root-dry/root; all costs remain in process wall and Work.
No structural split is forced.

| C2, 600 s cap | Process wall s | Strict original certificate | UB | LB | Absolute gap |
| --- | ---: | --- | ---: | ---: | ---: |
| OFF | 597.109 | No | 0.829963413 | 0.822454101 | 0.007509312 |
| Explicit | 597.063 | No | 0.830248486 | 0.810786705 | 0.019461781 |
| Root-dry | 552.454 | Yes | 0.829963413 | 0.829963413 | <3e-14 |
| Root | 485.719 | Yes | 0.829963413 | 0.829963413 | <3e-14 |

Root-dry demonstrates a certificate gain attributable to the fresh-model
lifecycle without inserted resource rows. Root adds two rows and saves a
further 66.735 seconds / 12.08% versus that control, passing the incremental
time gate. This is real C2 end-to-end evidence for both effects. It does not
erase D4's regression. The first target MIP's native root relaxation is
0.6064756 for OFF/root-dry, 0.6428263 for explicit and 0.6129122 for root:
the stronger initial explicit relaxation still yields a worse final gap.
All four final route witnesses and both prepared row pools independently pass.
Both C2 rows have eight-station proper supports out of 20 stations; support
size and large raw violation alone do not predict the contrasting D4/C2
performance.

| Full K1 D7, 600 s cap | UB | LB | Absolute gap | Gap improvement versus OFF |
| --- | ---: | ---: | ---: | ---: |
| OFF | 0.371894010 | 0.195569427 | 0.176324583 | — |
| Explicit | 0.306831813 | 0.196207888 | 0.110623926 | 37.26% |
| Root-dry | 0.371894010 | 0.195569427 | 0.176324583 | 0% |
| Root | 0.353840461 | 0.195661876 | 0.158178585 | 10.29% |

None certifies. Every arm makes three LPs and one terminal MIP, retaining
parent coverage when the unchanged adaptive rule declines refinement.
Both resource executions pass the gap-improvement gate on this long-route
role, predominantly through native primal quality. Explicit improves LB by
only 0.000638461 and root by 0.000092449. About 99% of each gap improvement
is from UB; these are not difficult-instance early-certification results.
The late OFF improvement also shows why the 120-second gains cannot simply
be extrapolated to a longer budget.

D7 root selects three genuine proper supports of sizes 34, 17 and 6, using
four maxflows and 0.018437 seconds of preparation. The final explicit/root
route witnesses each pick up 206 units and deliver 204, permitting a loaded
return; four capacities of 30 do not impose a total-pickup cap of 120.
Their maximum route durations are 17972.466/17937.569 seconds under T=18000.
Independent original-objective and route checks pass. The reserved D7
root-dry run finishes in 597.344 seconds with exactly the OFF endpoints,
isolating the root row gain in this single-MIP role. Both fresh-model modes
pay the same preparation and lifecycle policy.

The uniformly selected diagnostic candidate is **root**; see
[selected_candidate.json](selected_candidate.json). It has isolated full-K1
benefits in C2 and D7 with only M or fewer extra MIP rows, while explicit
worsens C2 and has a larger D4 time loss. Selection occurs after #52, before
C3 follow-up, and remains fixed regardless of C3/confirmation outcomes.
Its D4 failure already excludes default promotion. Stronger D7 performance
by explicit does not create a per-instance mode switch.

The subsequent same-v4 C3 protection pair (#53/#54) also fails the gate:
both arms finish without certification and with UB 0.817995541206. OFF has
LB 0.719467697316 / gap 0.098527843890; root has LB 0.712780695568 /
gap 0.105214845638. The 0.006687002 / 6.79% gap regression is material.
Three proper-support rows (22,17,17 stations) cost 0.008741 s to prepare,
so this result cannot be explained by graph construction consuming a large
fraction of the budget. Both original route witnesses and all row traces
pass independent checks. Root therefore has positive C2/D7 evidence and
negative D4/C3 protection evidence, rather than uniform qualification.

The complete development references use the same v4 build and 600-second
process caps. Official fingerprints match the original Round58 manifest;
Gurobi's hexadecimal log fingerprint and the API's signed 32-bit integer
are the same bit pattern, including D7's negative manifest value.

| Role / reference | Wall s | Certificate | UB | LB | Absolute gap |
| --- | ---: | --- | ---: | ---: | ---: |
| C2 P-GRB | 597.094 | No | 0.829963413 | 0.786523163 | 0.043440251 |
| C2 stable K1-H | 525.719 | Yes | 0.829963413 | 0.829963403 | 1.02221e-8 |
| D7 P-GRB | 597.079 | No | 0.290186246 | 0.196954927 | 0.093231319 |
| D7 stable K1-H | 597.109 | No | 0.215644075 | 0.195865016 | 0.019779059 |

C2 root certifies while P-GRB does not, and is 40 seconds / 7.61% faster than
stable K1-H. The latter is below the 10% relative time gate, so it is not a
qualified material speed gain against the stable method. C2 K1-H uses seven
native calls, including one infeasible child LP, and about 2.7 s of HGA.
D7 is much less favorable to the new mechanisms: both resource arms have
worse final gaps than both references. Stable K1-H's HGA takes about 543 s,
yet the ensuing six native calls and its much better UB yield the best gap
among these measured D7 methods. Thus the cold-arm resource gains do not
supersede the existing value of high-quality primal startup. No HGA/PASSIVE
plus-resource combination or warm-start proof-speed benefit is claimed.
All four reference route witnesses and native parameter records pass.

The [confirmation freeze](confirmation_freeze.json) was written after #58
and before the first C4 input build. It binds candidate, protocol, driver,
build and cap hashes. C4 completes before C5 opens. Both are previously
public, metadata-selected scenarios, not new sealed samples; neither
changes the selected mode or any runtime rule.

| Confirmation, T=18000, 600 s cap | OFF wall s | Root wall s | P-GRB wall s | Stable K1-H wall s |
| --- | ---: | ---: | ---: | ---: |
| C4, V20 balanced | 3.188 | 3.203 | 2.453 | 21.203 |
| C5, V50 surplus | 59.344 | 290.422 | 17.312 | 193.328 |

Every entry in this confirmation table certifies F=0. C4 protects
correctness and small setup cost but is not a difficult proof-tail test.
Both confirmation K1-H runs certify from a verified zero objective without a native optimize;
native parameter readback is therefore not applicable, not silently passed.
C5 gives a discriminating long-T result: root takes 231.078 s longer than
OFF, a material confirmation regression. Since the valid lower bound is
already zero, this is difficulty finding a zero-objective integer route,
not strengthening a nonzero proof bound. The original 600-second caps do
not require padding runs that certify early. C4 selects no resource rows;
C5 selects two. The independently checked C5 OFF zero-objective route
satisfies both added rows, with maximum normalized activity -0.957609347
against RHS zero. The optimal witness was not cut off. All eight confirmation
route witnesses pass. No rule is changed in response to confirmation.

## Verification, accounting and reproduction

All 40 solver-free CTests pass on the measured v4 source, including route
embedding, zero/empty boundaries, nonmetric directed travel, other stations,
prefix loads, all/single/proper supports, random fractional mincut versus
subset enumeration, physical identity, duplicate/scope rejection and default
off behavior. The first native micro's 24 LP feasibility checks verify
explicit-flow feasibility against the subset criterion. These are
correctness checks, not performance gains. The four native micro launches
include the failed v2 full-K1 attempt; none is hidden or free.

Every formal new route witness is independently recomputed against original
input/T/handling and objective conventions. Sparse cuts retain support,
physical identity, raw activity and final coefficients; large native points,
LPs and logs remain local with path/hash evidence. [measured_tables.md](measured_tables.md),
[runs.csv](runs.csv), [pairs.csv](pairs.csv), [optimizer_calls.csv](optimizer_calls.csv)
and [resource_lifecycle.csv](resource_lifecycle.csv) separate process wall,
native Work/status, diagnostics and certificate scope.
Final verification passes 59 original-route witnesses, 20 resource call
traces, 10 inherited threshold-proof records, 8 carried-load LP/control
records and all 262 strength-cut occurrences. The submitted-witness replay
also passes all 59 checks. Native parameter readbacks pass wherever native
calls occur; #62/#66 are explicitly not applicable because they use none.
The v4 source, executables, frozen 40-test log and all confirmation identities
are checked unchanged at campaign completion.

The first D4 explicit screen (#7) overlapped an independent LP audit and is
excluded from causal timing but still charged. The clean repeated #18
confirms its 120-second certificate loss. All later heavy audits, compilation
and Git work are separated from performance. Fresh longer runs are never
spliced onto shorter runs. Uncertified wall is budget use, not solution time.
Final accounting is **66/72 charged launches, 4/4 native micro launches,
278 actual optimizer calls and 971 recorded maxflow/separator calls**.
The latter counter includes guarded attempted calls; it is not a claim to
count Gurobi's internal graph routines or solver-free unit-test graphs.
All launches completed within their physical caps. There are 34 launches
with 600-second caps, 29 with 120-second caps and three native micro launches
with 20-second caps; no 1800/3600-second runs were needed. #7 and #27 remain
charged and excluded from performance. Six reserve launches are unused.
The informative 600-cap pairs include C3 regression, C2 multi-call execution,
D7 long routes and C5 confirmation; D4 has its separate protection pair.

[evidence_index.csv](evidence_index.csv) indexes 3,305 local files totaling
about 1.03 GB by path and SHA-256. Large raw files and binaries stay local;
sparse cut evidence and route witnesses are submitted. The
[native model table](native_model_shapes.csv) has 267 log records with actual
post-insertion matrix sizes and native root/user-cut summaries where present.
Build-only rows carry an explicit noncharged flag and cannot overwrite
charged per-run call counts; the final run table matches the call ledger.

Deliberately untested scope includes extra A/C2 or service confirmation,
A+B and resource-plus-HGA/PASSIVE combinations, full-K1/confirmation for
dynamic or carried-load-coupled execution, and full resource runs on D3/D6.
D7's finite LP closure did not close. These limits do not replace the
completed main-candidate K1, protection, references and two-confirmation
campaign, and no broader qualification is claimed.

Delivery targets the unchanged Round62 research branch at
71e955acad596acba2a9e74e738173113116d9f7. Final report/analysis packaging is
separate from the measured v4 native source; its commit is the new draft
PR head, not a replacement measurement build.

See [reproduce.md](reproduce.md) for build commands, measured source identities,
serial replay, independent verification and local evidence requirements.

## Next decision

Keep the valid prototypes default off. Service has a bounded positive
D3/D4 result and a full-K1 C3 failure; root has isolated full-K1 C2 and
long-T D7 gains but fails D4/C3 protection and C5 confirmation. Extra rows,
large violations and a stronger initial native relaxation are not reliable
selection criteria by themselves. C2's row-versus-lifecycle isolation is
useful evidence, not a universal fresh-model or cut-policy recommendation.

The next structural priority is **arcwise shared load/time capacity**:
test the unimplemented h+cbar*q<=B*x decomposition described in
[mathematics.md](mathematics.md), with a q-only control so familiar inventory
flow strength is not credited to the new coupling. B4's inactive aggregate
node-load rows leave this finer allocation question open. First require a
target-LP objective or pinned old-variable projection increment on long-T
points, then a bounded native comparison with the same model lifecycle.
This is a concrete research hypothesis, not a claimed Round63 result or a
promised improvement. It avoids responding to these mixed results with
instance-specific cut filters or a larger callback/threshold sweep.
