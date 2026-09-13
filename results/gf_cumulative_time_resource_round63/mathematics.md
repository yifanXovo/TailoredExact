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
