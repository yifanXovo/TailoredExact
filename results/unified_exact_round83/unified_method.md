# ENS-C: one frozen complete method

This defines the one default-off R83 ENS-C candidate. Exact proof/model
components inherit BDS-C; the physical neutral controller uses the union below.
Production source: `4496078f25c0cdad1cf7a5c39835fd23121e8978`.
Preset: `research-round83-vds-equal-net-exchange`.
Executable: `build/round83/v1/ExactEBRP.exe`, SHA256
`25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`.
All62 qualification tests and165 native calls pass. Correctness, design and
full performance remain distinct; the R83 report must establish measured effects.

## Problem and applicability

For integer final inventory `Y_i=b_i+sum_k(d_ki-p_ki)`, use
`r_i=Y_i/D_i`, `S=sum_i r_i`, `H=sum_(i<j)|r_i-r_j|` and
`F=H/(V*S)+lambda*sum_i w_i|r_i-1|`. The original convention is `G=0` when
`S=0`. The input parser's station set, positive targets and weight scaling are
retained. Every visited station has exactly one nonzero, one-way integer
operation, and station visits are disjoint between routes.

Vehicles leave empty; all load prefixes lie in `[0,Q_k]`. A loaded return is
legal and its final unloading is paid. Thus original route duration is
`travel+c_pick*pickup+c_drop*station_drop+c_drop*return_load`, equivalently
`travel+(c_pick+c_drop)*pickup`, with the supported common mathematical `T`.
Capacity bounds prefix load, not cumulative pickup. Station inventory need not
be conserved: vehicles may remove bikes to the depot.

The complete strengthened preset requires symmetric metric travel and the
inherited nonnegative-penalty assumptions. Its explicit metric guard runs
before startup. Tests of an isolated neighborhood on nonmetric distances do
not qualify all retained model strengthening for that broader input class.

## Complete algorithm

```text
Start the one process clock; parse and check the original problem.
Whenever the implemented verified-zero check closes against F>=0, end early.
Construct one verified physical route set by joint insertion.
Initialize 24 fixed-seed random route/separator orders; append the constructive
  order as the 25th seed without consuming another random draw.
Fully decode each seed and perform strict guided decoded descent on each.
Retain the best independently verified physical witness, including construction.
On that witness alternate strict closure and the union of neutral moves:
  close insertion/quantity neighborhoods;
  enumerate balanced relocations and equal-net exchanges of served blocks;
  if none strictly improves the complete sorted duration tuple, finish;
  adopt the best fully verified union move and repeat.
Pass an objective-improving witness through the unchanged outer handoff rule.
If a verified numerical zero closes against F>=0, return its certificate.
Otherwise establish the complete Gini interval cover and its valid bounds.
While proof obligations remain:
  choose a controlling obligation and apply the inherited mathematical
    frontier/child-bound tests, midpoint split, or exact parent closure;
  before each needed complete native MIP, map and check one eligible current
    verified witness as a full Start;
  update bounds only within their certified scopes and maintain full coverage;
  accept original-problem U only after physical/objective verification.
Return a numerical certificate only when the original proof contract closes.
At the sole global deadline end the whole run with its qualified U/L.
```

Every step, including failed probes, model construction, Start validation,
event persistence and exit, consumes the same process budget. Native MIP can
stop at a valid mathematical target, after which the controller retains the
proof obligation and bound. Multiple charged native invocations are possible;
this is not a claim of one uninterrupted Optimize call or preserved search
tree. There is no component seconds/Work allocation, history-based dispatch,
per-instance preset choice or imported archived witness.

## Startup and physical improvement

Joint insertion enumerates legal unvisited single pickups, single drops and
equal pickup/drop pairs, vehicles, ordered insertion legs and feasible positive
integer amounts. For a fixed station/amount choice, it retains the least-travel
feasible placement and ranks original objective gain per added duration, with
its deterministic convention for nonpositive added duration. Full verification
guards adoption. The resulting witness is retained even if subsequent greedy
decoding of its route order gives a worse objective.

The extra seed preserves the constructed vehicle assignment and station order.
Unvisited IDs are appended in ascending order to the vehicle minimizing current
physical-duration-plus-append-travel proxy, ties by vehicle index. These tail
orders are not unverified service operations. The full deterministic decoder
assigns operations. The original 24 random seeds are initialized first using
seed20260626; all25 use the same decoder and guided neighborhood.

The actual decoder is `nGreedyLU_RA_compact_full` (compaction mode1). It runs
the deterministic greedy procedure, removes zero-operation stations from the
active prefix when present, and fully decodes the compacted route order once
more, retaining the better objective. The wrapper's legacy `iterations=10`
is passed as `max_iter` but explicitly ignored by this function, as are
`IterNum` and `r_avg_start`; it is not an operative ten-pass rule. The cache
holds at most200000 decoded orders and clears on reaching that size. Cache
eviction changes recomputation cost, not the search neighborhood or stopping
rule. These details describe existing source, with no parameter change.
The old `tryRouteExactNeighborhood` and `tryPairExactNeighborhood` immediately
return false and are not called by the active `runFromCurrentState` loop.
Their unreachable local-oracle seconds/node caps are not live ENS-C rules.
The active loop uses constructive seeding, interval, local-composite,
paired-interval, residual-unit and pair-flow improvements.

Decoded descent uses first strict improvement in proxy-ordered candidates.
Same-route moves reposition selected supply/demand or unused stations around
the executed route's supply/demand anchors. Cross-route moves consider the
first unused supply and demand in each tail at compatible target anchors.
This is a restricted, explicitly generated neighborhood, not all relocations.
The proxy orders candidates; a failed pass fully decodes every generated
candidate. It does not reject a candidate merely because its proxy is poor.
Accept only decoded fitness improvement greater than1e-12. Finite route/order
states and strict deterministic improvement preclude cycles. No evolutionary
generation loop runs in this preset, despite legacy HGA field names.

Strict physical closure compares the insertion proposal with the minimum-F
legal single-station or opposite two-station quantity proposal and chooses the
lower proposed F, exact ties favoring insertion. Quantity changes can cross
vehicles, change sign or delete a zero-operation station. Materialize and
reverify every adoption, require gain>1e-12 and prediction agreement<=1e-10.
This selection is not a minimum-F oracle over the union: insertion has its own
gain/duration ranking. An exhausted full pass certifies only that the declared
neighborhoods contain no strict improving move at that tolerance.

For a served route write `s_j=p_j-d_j` and prefix `L_j=sum_(h<=j)s_h`. A
contiguous block `(a,b]` is balanced when `L_a=L_b`. At a target leg carrying
load `l`, require `0<=l+min_(a<=j<=b)(L_j-L_a)` and
`l+max_(a<=j<=b)(L_j-L_a)<=Q_target`. Enumerate all such blocks, all other
vehicles including unused ones and every target leg; preserve block order.
Recompute both routes' travel and handling. Removing a balanced block leaves
source prefixes outside the block and later target prefixes unchanged. A
negative relative prefix can require a positive target entry load.

Also enumerate pairs of nonempty contiguous blocks on distinct vehicles,
canonically source<target, whose signed net loads are equal (possibly nonzero).
Retain each block's order and integer operations. Both outside-block prefixes
and terminal loads stay unchanged. At each recipient's original entry load,
check the incoming block's minimum and maximum relative prefix against that
recipient's actual Q, then recompute both original full travel/handling times.
All stations retain the same operation, so exact Y and computed F are unchanged.
No metric shortcut is used inside the neutral operator; the inherited exact
model's separate metric guard still limits the complete method's applicability.

Choose the minimum feasible descending sorted M-duration tuple over both move
families, strictly below the current tuple. On equal tuple, balanced relocation
precedes exchange; then order by source,first,last,target,target_first,target_last.
Indices are zero-based service offsets and half-open intervals; a relocation's
target interval is empty at its leg. Equal-net exchanges include net-zero pairs,
while the relocation family still includes unused targets and source deletion.
The exact tuple comparison never overlooks an earlier tiny increase. Fully
original-verify each adoption, requiring exact Y/F and tuple agreement, then
repeat strict closure. Finite states and strict (computed F,tuple) decrease
justify termination, not BRP optimality, polynomial time or faster native proof.
On two empty-return routes, one-way transfer with net delta would produce
terminal loads -delta,+delta; only delta0 is feasible. Equal-net two-way exchange
expands the neighborhood without requiring empty returns in the original problem.

The outer witness store still requires F improvement>1e-10. A neutral-only
trajectory or smaller strict gain may therefore leave the prior physical route
as the actual native Start. R83 E8 startup and full runs preserve this distinction. The duration
proxy is a design rationale, not a speed theorem. Explicit verification failure
retains the previous valid witness and fails experimental acceptance.

## Exact model, cover and native Start

The interval model retains the original compact route/operation variables,
node prefix loads, inventory and time constraints, and the inherited valid F0
strengthening. The principal representation change is VD-P's one-hot inventory
state product. For each proved integer inventory domain `y in [L_i,U_i]`, use

```text
s_iy binary, sum_y s_iy=1, Y_i=sum_y y*s_iy
gamma_L*s_iy <= q_iy <= gamma_U*s_iy
sum_y q_iy=G, Z_i=sum_y y*q_iy
```

At the selected state `y=Y_i`, reconstruction gives `q_iy=G`, hence `Z_i=G*Y_i`.
Conversely every allowed original integer inventory/product point has this
extension. This is exact for that block conditional on valid domain/interval
propagation; it does not claim the complete route-coupled LP is an integer hull.
VD-P retains the original penalty epigraph; it does not add VD-J's penalty
equalities or R67's logarithmic code variables. ARC/LOG/QDS-X and later
experimental resource policies are not inherited merely because their code
remains in the repository.

The retained static F0 pack includes interval/product bounds, valid inventory
and movement domains, conservation and visit linking, incumbent/penalty lower
estimators, denominator/SP-product strengthening, pair/triple support-duration
families, connectivity flow, required movement, handling capacity and transfer
compatibility. The preset uses two propagation rounds, support size at most3
and at most50000 generated subsets. These are fixed strengthening-size rules;
omitting additional valid cuts does not remove any necessary proof obligation.
No exhaustive subset-duration block, dynamic user-cut callback or custom
branching priority is enabled. Actual generated rows depend on the input;
an enabled family name alone is not evidence of activity.

AM begins with one complete relevant Gini interval. A verified U and
nonnegative penalty justify incumbent domain restriction. The scheduler keeps
all necessary obligations, using valid leaf bounds to form the global lower
bound; a midpoint replacement is an atomic full two-child cover. Valid empty
child proofs close only their own regions. A logical depth/width limit sends
an unresolved region to complete MIP, never drops it.

For parent bound B, verified U and two terminal valid child LP bounds b0,b1,
let `gap=max(U-B,max(certificate_tolerance,1e-12))`,
`g_j=clip((b_j-B)/gap,0,1)`, `eta=min(g0,g1)`, `mu=(g0+g1)/2`.
The active split score is `eta*mu`; the threshold is0.08 with the implemented
scale-aware numerical comparison. Child infeasibility triggers the inherited
two-child split/empty-region handling. Otherwise no strict child-disjunction
gain leads to exact parent closure; sufficient score splits immediately;
smaller positive gain runs the parent to target `min(b0,b1)` and requeues it
without forcing a split. Frontier targets likewise come from another relevant
leaf's valid bound. Target attainment is mathematical evidence, not elapsed time.
K0=1, midpoint, depth8 and width1e-4 are uniform. Legacy output fields such as
`frontier_intervals=4` or `c6_normalized_split_threshold=0.01` are compatibility
values, not these first-class AM decisions.

Before each required MIP clear explicit Starts, normalize only interchangeable
equal-Q vehicle labels and independently reverify the current paid witness.
If it is incompatible with the current interval/non-strict cutoff, skip that
Start while retaining the complete obligation. Otherwise map every actual
column, including selectors, products and auxiliaries; check bounds, types,
linear rows and objective, submit one vector and read all values back. Supplied,
read-back, native-loaded and observed MIPSOL incumbent are distinct evidence.
A Start restricts no search domain and supplies no lower-bound certificate.

## Numerical and empirical contract

Gurobi13.0.2, Threads1, Seed0, PresolveAuto and zero requested MIP gaps are
unchanged; FeasibilityTol1e-6, IntFeasTol1e-5 and OptimalityTol1e-6 remain.
The physical route-time threshold and frontier certificate tolerance are1e-7;
the verified nonnegative zero stop uses1e-12. Original objective recomputation,
bound scope, complete coverage and normal finalization remain necessary.
These are numerical certificates, not an implemented strict rational proof.
Signed tiny gaps are retained; an inconsistent large L>U is not clipped away.

The method's contributions are the selected exact inventory representation,
verified native integration, finite startup and physical plateau-crossing
composition as one measured algorithm. Generic disjunctions, multistart,
insertion, quantity changes and relocation are not claimed as new theory.
Correctness, design rationale and measured performance must remain separate.
R79-R81 support BDS-C on exposed roles; R82 preserves five fresh gains and a
consequential U6 confirmation loss. Those positive outcomes do not validate
ENS-C automatically. R83 is development; new unadapted confirmation and long
protection remain necessary before overall acceptance.

## Source and evidence map

|Part|Frozen source / existing proof|
|---|---|
|Preset inheritance and actual startup order|`src/main.cpp`, `applyAlgorithmPreset`, `runPaperPrimalHeuristic`|
|Active F0/AM settings and metric guard|`src/PaperK1AmSf.cpp`|
|AM score, target transitions, full cover|`src/PaperExternalGiniTree.cpp`, `src/ControllingLeafScheduler.cpp`|
|Original objective/physical semantics|`src/Result.cpp`, `src/Evaluator.cpp`, `src/Parser.cpp`|
|VD-P correspondence|R55 `station_state_exactness_proof.md`; R68 `mathematics.md`|
|Start integration|R68 `algorithm.md`/`mathematics.md`; `src/MipStartMapping.cpp`, `src/GurobiBaseline.cpp`|
|25 seeds and finite decoded descent|`src/HgaTgbcRunner.cpp`, `include/hga_tgbc/HybridGA.h`; R70/R71 mathematics; R73 seed revision plan|
|Strict physical closure|R76 `mathematics.md`; `src/Round76PhysicalClosure.cpp`|
|Balanced relocation|R78 `mathematics.md`; `src/Round78BalancedRelocation.cpp`|
|Equal-net exchange and union composition|R83 `mathematics.md`; `src/Round83BlockExchange.cpp`|
|Actual rather than intended mechanisms|R83 diagnostic/startup audits and completed full campaign mechanism audit|

This description reuses the R81 source-grounded definition for unchanged
components and explicitly replaces the physical neutral controller. Its
preparation during the R83 serial campaign runs no additional experiment.

## R83 evidence and scope boundaries

The fixed-BDS-final diagnostic and actual ENS startup are different paths.
ENS applies its union immediately after the common decoded witness, not after
a complete BDS run. U6 actual startup improves to.173039905739, whereas its
fixed-final diagnostic ends at.178390957548; D7 actual.291448973504 is worse
than its diagnostic.271177227019. Formal endpoints must use their own current-run
witness and all paid work. No favorable archived diagnostic route is imported.

The inherited eight-oracle structural check plus original physical replay
separate correctness from performance. The offline reader's dropped untouched
empty-route representation is fixed in round83_audit_v2.py; original native
D7 startup is re-audited without rerun, and all old failed metadata remains.
This reader change does not change the algorithm or its numerical tolerances.
Every future use of a prior confirmation role in design changes that role to
development for the revision. New unadapted confirmation is still required.

The closed R83 screen has13 valid normal runs and50 Optimize calls. All actual
Start/cover/physical audits pass. U6 ENS improves P gap13.5852% and retains
88.4470% of current K1 advantage, with worse U and stronger L. This development
result does not remove the long-protection and unadapted-confirmation requirements.
