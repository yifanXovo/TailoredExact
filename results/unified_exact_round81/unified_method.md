# BDS-C: one frozen complete method

This is a source-grounded consolidation of the method already frozen in R78,
not a new candidate, parameter change, qualification or performance result.
Production source: `4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e`.
Preset: `research-round78-vds-balanced-descent`.
Executable: `build/round78/v1/ExactEBRP.exe`, SHA256
`3fae847a75c3c9d07d8f5f0444daeafb73559865e6bffb816746802b9e2f43ab`.
R81 keeps that identity; its final report must separately establish outcomes.

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
Construct one verified physical route set by joint insertion.
Initialize 24 fixed-seed random route/separator orders; append the constructive
  order as the 25th seed without consuming another random draw.
Fully decode each seed and perform strict guided decoded descent on each.
Retain the best independently verified physical witness, including construction.
On that witness alternate strict physical closure and neutral balanced blocks:
  close insertion/quantity neighborhoods;
  if no balanced block strictly improves the sorted duration tuple, finish;
  adopt the best fully verified balanced block and repeat.
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

Transfer the same integer operations and require exact same Y and computed F.
Choose the lexicographically smallest feasible vector of all M route durations
sorted descending, strictly below the current vector; break exact ties by
source, block endpoints, target and leg. The exact lexicographic comparison
does not skip an earlier tiny increase. Full physical verification and tuple
agreement guard adoption. Then repeat strict closure. Each accepted transition
strictly decreases `(computed F, sorted durations)` over a finite state set;
joint exhaustion is not BRP optimality or a polynomial runtime guarantee.

The outer witness store still requires F improvement>1e-10. A neutral-only
trajectory or smaller strict gain may therefore leave the prior physical route
as the actual native Start. R80 E8 exhibits this distinction. The duration
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
R78-R80 evidence supports exposed roles; R81 tests replication/long protection.
Diverse unadapted confirmation remains necessary before overall acceptance.

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
|Balanced blocks/composition|R78 `mathematics.md`; `src/Round78BalancedRelocation.cpp`|
|Actual rather than intended mechanisms|R78-R80 mechanism audits; R81 audit pending at document creation|

This consolidation was prepared through source/document reads during the
original serial R81 campaign. It runs no extra optimizer, test or heavy audit,
opens no confirmation input, and changes no production byte.
