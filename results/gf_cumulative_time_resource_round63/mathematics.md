# Cumulative final-route resource: validity, projection and implementation

The objective, S=0 convention, parser/weights and every original physical row
are unchanged. For vehicle k, define a_i=sum_h tau_hi*x_hi+c*p_i with
c=c_pick+c_drop. The resource is prepaid final-duration accounting, not the
physical arrival clock. It therefore does not assert any time-window property.
All physical coefficients use the common original T and original directed arcs;
capacity Q_k still restricts every load prefix, never total route pickup.

## Integer embedding

On an elementary route 0,i1,...,im,0 set f_0i1=0. On each outgoing arc from
it put the sum of all original travel through arrival at it plus c times all
pickup through it. Consecutive differences equal a_it. Unused f are zero.
The remaining travel contains arc (it,j) and a j-to-depot path and is at least
tau_it,j+dbar_j0. Remaining pickup cost is nonnegative. Thus
f_it,j <= T-tau_it,j-dbar_j0. If this RHS is negative, that used arc cannot
occur on a feasible route; replacing it by max(0,RHS) is a safe relaxation,
without deleting any x arc. A loaded return has the same accounting. Multiple
pickup/drop blocks can make sum p exceed Q_k and still satisfy every f row.
An empty route has f=0. With all travel/handling zero, f=0 also embeds any
original feasible route; the original connectivity rows remain essential.
Directed shortest paths permit intermediate stations, including every other
supplier or receiver. Nothing in the argument removes stations outside W.
Heterogeneous Q has no effect on this accounting proof.

## Projection and reverse implication

Sum station balances over W. Internal f cancels, leaving
sum_W a = f(delta+(W))-f(delta-(W)) <= sum_delta+(W) B_ij*x_ij.
For a fixed nonnegative point define source arcs s->i of capacity a_i,
station arcs i->j of capacity B_ij*x_ij, and depot 0 as sink. A source-side
cut with stations W has capacity A-sum_W a+sum_delta+(W) Bx. Therefore
A-mincut equals the maximum violation over *all* W (including empty W).
If every subset inequality holds, maxflow saturates all source arcs. Its
station-arc flow is the required f and has precisely the station balances
and arc upper bounds. Conversely any such f satisfies every subset row.
This establishes exact continuous projection for these coefficients; it is
standard flow-cut duality, not a claim of a new maximum-flow theorem.

The explicit model eliminates the fixed-zero depot outgoing f columns,
retains all return f columns, and adds M*V*V nonnegative continuous variables,
M*V station balances and M*V*V upper-link rows. No base row or x arc is removed.
The projected model adds no variables. A finite interrupted closure is only
a subset of the full projection; an objective match alone is weaker than
showing the final point has no violated subset row.

## Simple supports and historical relation

For W=N, if every potentially used return arc has tau_i0<=T, expanding B_i0
gives travel+c*pickup <= T*sum_i x_i0. The old compact duration row in
src/CplexBaseline.cpp is travel+c*pickup<=T, without the fractional activation
factor. All-set gains must therefore be attributed to this inexpensive
activation strengthening. If an impossible long return arc still exists in
the LP, the clipped B formula is retained rather than making that simplification.
For W={i}, a_i<=sum_j B_ij*x_ij is a local fractional service/travel coupling.
The `simple` arm adds exactly these M*(V+1) rows. Genuine multi-station proper
supports may additionally connect resource produced across long fractional
paths to their available exits. Compare their violation after simple closure.

Existing connectivity flow routes visit mass, not accumulated original travel
and pickup cost. Neither a variable count nor common use of network flows
proves a containment relation. The zero-cost boundary shows that the new
block cannot replace connectivity. Existing inventory-route inequalities use
signed net inventory and capacity-weighted routing arcs; pickup resources
do not cancel at a later delivery and have a time coefficient rather than Q.
Historical pair/triple support-duration covers use selected visits and their
minimal travel/service; they are retained. The removed exhaustive historical
subset-duration block is not restored. Any empirical extra strength must be
shown in the actual F0 region, with the old blocks present, not inferred from
the family names. No equivalence of replacing any of those blocks is claimed.

The optional historical IR1/IR2/IR3 root closures are **off** in this round's
core F0. Their formulas, not their optional execution, are the comparison
above. A concrete algebraic separation of the flow families is useful:
take four stations, zero travel, c=1, T=1, Q=2 and x=1/2 on the cycle
0,1,2,3,4,0 (zero on every other arc). Set p1=p3=d2=d4=1/2.
Initial inventories (2,0,2,0), final inventories (3/2,1/2,3/2,1/2) and
domains [0,2] satisfy inventory balance. Load flow is 1/2 on arcs 1->2
and 3->4 and zero otherwise, below Q*x=1. Summing this load balance over
any W proves every mixed inbound/outbound IR inequality. Their projected
versions using these physical domains are weaker. Visit flow can send 2 from
depot and consume 1/2 per station: arc amounts 2,3/2,1,1/2,0, within 4*x=2.
Global duration
is c*sum p=1=T and singleton resource rows hold, but the whole-set resource
row requires 1<=T*x40=1/2 and is violated. Thus those load/visit-flow and
inventory-route families do not by themselves imply cumulative duration.
This is an algebraic family comparison, not a claim that every other F0 row
or the nonlinear objective has been checked on this toy point. The actual
optimal F0 LP witnesses and the proper-subset violations after the simple
arm establish the separately measured incremental strength in the real model.

## Numerical implementation and scope

The code validates nonnegative finite original travel/handling/T. Shortest
paths use downward-rounded nonnegative sums. All final rows are normalized
by max(1,T). Travel and handling supply coefficients round down; B capacities
round up after conservative shortest-path subtraction, using long-double
intermediate subtraction. Consequently the implemented resource is a tiny
safe relaxation of the exact physical formula. Its own explicit/projection
equivalence is exact algebraically. No floor-rounded integer capacities or
distance surrogates replace the original route validator.

The graph search clips only raw x/p in [-1e-8,0] to zero and rejects larger
negative or nonfinite values. Deterministic Dinic uses its inherited 1e-12
residual tolerance. It finds a candidate support; the submitted row's activity
is recomputed in long double from the *unmodified* original LP values, with
the original stored coefficients. A normalized violation must exceed 1e-7.
Graph A-C is not used as a substitute for that recomputation. With tiny
negative LP values, the clipped graph optimum is not claimed to equal the
raw maximum; exhaustive comparisons use nonnegative fractional points.

Identity binds V, M, every original directed cost, T, handling, Q, initial
stocks and station capacities. Canonical coefficients and support are
regenerated before acceptance. Local scope, changed coefficients, a stale
identity or a repeated signature is rejected. Supports are sorted. No
cross-support dominance or sparsity optimality is asserted.

## Bounded execution

The shared deterministic Dinic implementation is extracted unchanged from
InventoryRouteCuts.cpp. Each query makes at most M graphs of V+2 nodes and
V+V^2 forward arcs. Native separation acts only at optimal MIPNODE relaxations:
at most 16 root queries, then deterministic first eligible tree node and
subsequent spacing of 64 processed nodes, 64 queries total, 256 rows per native
model. Exhausted budgets return before reading the vector or constructing a
graph. All K1 native calls have their own recorded lifecycle and bounded work.
There is no optimizer inside this callback.

OFF keeps canonical bytes and parameters; precrush sets only PreCrush=1;
dry and cuts both use that same parameter and separation schedule. Dry keeps
selected evidence but does not call cbcut. API success records submission,
not solver adoption. Root, subsequent cut passes, tree samples, Work and
endpoints must establish any effects. Exceptions disable this optional
separator; all required original rows remain. The LP diagnostic runs at most
67 optimizations per shared 120-300 second cap (F0, explicit, simple, at most
64 closure reoptimizations), recording each launch before optimize. The
native flow micro has at most 24 LP calls under its shared cap. These are
charged batches, not production-speed claims.

The v2 `root` execution observes only the first optimal required LP, builds
one graph per vehicle and retains at most M global rows. It performs no LP
closure. `root-dry` uses the same observation and recording without insertion.
Full algorithms reuse an LP already required by their control; the fixed
MIP harness pays and records one extra preparation LP. Subsequent MIPs add
the cached rows as ordinary static constraints, retaining the original
canonical model and recording the actual native insertion count. No callback
or PreCrush change is involved. LPs themselves remain unmodified, so an
improved integer search is not an improved outer-LP bound by construction.
Global physical scope permits reuse across intervals and incumbent epochs.
Failure or an invalid LP lifecycle clears the optional pool. Root setup and
the paid preparation LP are included in process wall/Work accounting.
In v3 both root and root-dry read a fresh canonical model for each native
call; retained-model reuse is disabled for these two research modes. This
prevents MIP-only rows from contaminating a later LP or being appended twice.
It adds model-read cost and discards retained native model/search state
between calls, without forcing extra optimizer calls. The dry control
isolates this entire lifecycle policy, not just file-reading overhead.
The unchanged outer controller can still make different subsequent calls
when the native evidence or incumbent changes.

## Carried-load strengthening of the explicit extension

Let load_ki be the existing post-service node load, zero at an unvisited
station by load_ki<=Q_k*z_ki. Empty departure and nonnegative deliveries give
load_ki<=sum of prior/current pickups. On the unique outgoing used arc the
canonical f embedding is accumulated downward-rounded travel plus the same
downward-rounded c/scale times those pickups. Therefore the additional row
`(c/scale)*load_ki - sum_j f_kij <= 0` is valid for every original route
embedding, including loaded return and total pickup greater than Q_k. This
uses M*V extra rows, no extra variables beyond explicit time flow. c=0 rows
are redundant and omitted. The `coupled` research mode retains all base rows.

This is a lower bound on node throughput in the resource network. The earlier
ordinary mincut equivalence covers the original explicit extension, not
these additional lower bounds. No separator for their complete projection is
claimed. A violated added row at one explicit f solution only proves a change
in extended space. To test projection at a recorded old-variable point, leave
all f variables free and solve the pinned explicit/coupled feasibility pair;
require the explicit control to remain feasible before interpreting any
coupled infeasibility. These diagnostic bounds never enter a global certificate.

Native API scope and the presolve isolation follow Gurobi's
[GRBcbcut documentation](https://docs.gurobi.com/projects/optimizer/en/current/reference/c/callback.html#c.GRBcbcut)
and [PreCrush parameter](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter.PreCrush).

## Service-projection work package A

The Round62 generator, physical domains, threshold weakening, caps and rows
are inherited unchanged. Its service row dominates the inventory row because
inventory balance adds a nonnegative opposite-direction service term to each
inventory projection term. This does not imply objective LP or MIP superiority.
Round63's predeclared qualification is relative to real OFF protection and
confirmation, not to the fastest historical research arm on every instance.
This new criterion never retroactively changes the Round62 failed gate.

## A concrete untested continuation

One remaining structural hypothesis is to share resource capacity with an
arc-disaggregated carried-load flow q, rather than only the tested aggregate
node-load lower bound. On a legal route, q is post-service load on the used
outgoing arc, q_0i=0, q<=Q*x and out(q)-in(q)=p-d. With the same normalized
handling coefficient cbar, define h=f-cbar*q. The canonical embedding gives
h>=0 and out(h)-in(h)=incoming-travel+cbar*d. The existing time upper bound
then becomes the shared capacity h+cbar*q<=B*x. This identity respects
loaded return and repeated capacity recycling.

Current F0 uses node-load variables; this proposal would require a separate
arc-load lift and cannot be described as simply reusing an existing q block.
A q-only lift is a familiar inventory/capacity-flow strengthening, not a new
contribution by itself; the proposed increment is its shared time capacity.
A future comparison must first isolate the q-only lift from the shared
capacity rows and use pinned old-variable feasibility controls. B4's zero
node-aggregate violations do not establish whether this finer sharing is
stronger. No implementation, complete projection separator, target-LP gain
or MIP benefit for this continuation is claimed in Round63.
