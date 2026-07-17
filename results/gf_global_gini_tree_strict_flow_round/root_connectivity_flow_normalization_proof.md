# Root connectivity-flow normalization proof

## Scope and notation

This note proves the route-preservation and dominance claims for the four
root-connectivity-flow variants implemented by
`include/ConnectivityFlow.hpp` and `src/ConnectivityFlow.cpp`. It is a
mathematical and deterministic-helper artifact, not a report of CPLEX solve
results. The companion `flow_projection_and_dominance_audit.csv` records the
mechanical test facts produced by
`build_round21/tests/ConnectivityFlowTests.exe` on 2026-07-16.

Let $N=\{1,\ldots,V\}$ be the stations and let 0 be the depot. Fix a vehicle
$k$; the vehicle subscript is suppressed below. The common original arc and
visit variables are $x_{ij}$ and $z_i$. On an integral elementary
depot-closed route,

\[
0=v_0,v_1,\ldots,v_s,v_{s+1}=0,
\qquad 0\le s\le V,
\]

the used route arcs have $x_{v_t v_{t+1}}=1$, the visited stations have
$z_{v_t}=1$ for $1\le t\le s$, and all other incident route arcs and
visits for this vehicle are zero. The all-zero assignment represents an
unused vehicle ($s=0$).

For F0, the flow equations are

\[
\sum_{j\ne i}f_{ji}-\sum_{j\ne i}f_{ij}=z_i
\quad(i\in N),
\qquad
\sum_{j\in N}f_{0j}-\sum_{i\in N}f_{i0}=\sum_{i\in N}z_i,
\]

with $0\le f_{ij}\le Vx_{ij}$ for every directed non-self arc. F1--F3
delete all $f_{i0}$ columns. Their depot equation is consequently

\[
\sum_{j\in N}f_{0j}=\sum_{i\in N}z_i.
\]

All statements below apply independently to each vehicle.

## F0 (`round20-current`): canonical lift and the circulation degree

Define the canonical flow on a used route by

\[
f_{v_t v_{t+1}}=s-t \quad(t=0,\ldots,s),
\]

and set every flow off the route to zero. In particular,
$f_{v_s0}=0$.

At station $v_t$, $1\le t\le s$, the incoming flow is
$s-(t-1)$ and the outgoing flow is $s-t$. Their difference is one,
which equals $z_{v_t}$. At an unvisited station both sides are zero. The
depot supplies $s-0=s=\sum_i z_i$. Finally, every canonical value lies in
$[0,s]\subseteq[0,V]$, so all F0 arc links hold. This proves that every
original integral route has an F0 lift.

The same fixed route exposes the avoidable degree of freedom. For a scalar
$c\ge0$, put

\[
f_{v_t v_{t+1}}=s-t+c \quad(t=0,\ldots,s).
\]

The added $c$ enters and leaves every station once, and it enters and
leaves the depot once, so none of the balance equations changes. The largest
flow is $s+c$ on the depot departure. Thus the whole family is feasible
whenever

\[
0\le c\le V-s.
\]

Conversely, on this fixed elementary route support, let
$q_t=f_{v_t v_{t+1}}$. The station recurrences
$q_{t-1}-q_t=1$ imply $q_t=s-t+q_s$. Hence every supported F0 flow has
the displayed form with $c=q_s\ge0$. The supported auxiliary face therefore
has exactly one depot-cycle circulation coordinate, with a nontrivial
interval when $0<s<V$. A full route ($s=V$) forces $c=0$ through the
departure upper bound, and an unused vehicle has no used cycle. Fractional
arc solutions can have additional cycle freedoms; this route proof neither
needs nor excludes them.

Positive return-to-depot flow is therefore unnecessary for every original
integral route, while F0 permits it whenever $c>0$ is available.

## F1 (`zero-return`): validity and removal of the depot-cycle coordinate

F1 eliminates every return-flow column $f_{i0}$, retains the station
balances, and uses the direct depot source equation. Give it the canonical
non-return values

\[
f_{v_t v_{t+1}}=s-t \quad(t=0,\ldots,s-1).
\]

The preceding station calculations still hold: at the last station the
omitted return has the canonical value zero. The depot departure is $s$, so
the direct source equation also holds. The F1 upper bound remains $Vx$, and
all values are at most $s\le V$. Hence F1 preserves every original route.

Moreover, the fixed-route flow is now unique. The last station balance gives
$q_{s-1}=1$; working backwards through
$q_{t-1}-q_t=1$ gives $q_t=s-t$, including $q_0=s$. Adding a common
positive constant only to the retained route arcs would violate both the
last-station balance and the direct depot equation. Thus F1 removes precisely
the F0 depot-cycle circulation coordinate. It does not claim to eliminate
every possible circulation on a fractional multi-arc support.

Every F1 auxiliary solution embeds in F0 by adding all deleted return-flow
columns at zero. The F0 station and depot equations then reduce exactly to
the F1 equations.

## F2 (`normalized`): nonzero lower links and tighter internal upper links

F2 starts from F1 and imposes, for every flow arc whose head is a station,

\[
f_{ij}\ge x_{ij}.
\]

It uses the universal upper bounds

\[
f_{0j}\le Vx_{0j},
\qquad
f_{ij}\le (V-1)x_{ij}
\quad(i\in N,\ j\in N,\ i\ne j).
\]

For a canonical route, every used non-return arc has index
$0\le t\le s-1$ and value $s-t\ge1=x_{v_t v_{t+1}}$, proving every
lower link. The first depot arc has value $s\le V$. An internal used arc
has $t\ge1$, so

\[
s-t\le s-1\le V-1.
\]

Unused arcs have both $x=0$ and $f=0$. Thus every original integral
route has an F2 canonical lift. Since F2 only adds lower links and tightens
some upper links relative to F1, every F2 solution satisfies F1.

The relevant edge cases are valid without exceptions:

- **$V=1$:** there are no internal station-to-station arcs. The one-station
  route has $f_{01}=1=V$, and its return flow is absent.
- **Unused vehicle:** $s=0$, all $x,z,f$ are zero, and every balance and
  link is satisfied.
- **One-station route:** $s=1$, the sole flow is $f_{0v_1}=1$; the return
  has no column.
- **Full route:** $s=V$, the departure reaches its valid upper bound $V$,
  while the first internal arc carries $V-1$ and all later internal arcs
  carry less.

## F3 (`normalized-start-coupled`): linear start coupling

Let $n=\sum_{i\in N}z_i$; the implementation substitutes this sum directly
and introduces no product and no separate $n$ column. F3 adds, for each
depot departure $0\to j$,

\[
f_{0j}\le n,
\qquad
f_{0j}\ge n-V(1-x_{0j}).
\]

On an integral used route, $n=s$, exactly one departure arc is used, and
its canonical flow is $s$. Both rows for that arc hold at equality. For an
unused departure, $f_{0j}=x_{0j}=0$, and the lower right-hand side is
$s-V\le0$; the upper row is also valid. For an unused vehicle, $n=0$
and every departure flow is zero. This covers $V=1$, one-station, and
full-route cases as well.

These are linear valid inequalities, so every original integral route has an
F3 canonical lift and every F3 solution satisfies F2. Given the direct depot
equation and flow nonnegativity, the individual upper row $f_{0j}\le n$ is
already implied; it is retained as an explicit, auditable coupling. The
lower row can restrict fractional start patterns. Whether its additional rows
produce useful relaxation strength or only extra solve work is an empirical
question and is not inferred from this proof.

## Dominance and projection statement

After zero-extending deleted return columns where necessary, the auxiliary
feasible sets obey

\[
Q_{F3}\subseteq Q_{F2}\subseteq Q_{F1}\hookrightarrow Q_{F0},
\]

where the hook is the F1-to-F0 zero-return embedding. Dropping every flow
column maps F0 to the no-flow formulation. Accordingly, their fractional
projections onto common original variables can only become tighter in the
order

\[
P_{F3}\subseteq P_{F2}\subseteq P_{F1}\subseteq P_{F0}\subseteq P_{off}.
\]

No strict inclusion is asserted for every $V$ or every instance. For
integral elementary routes the projection is identical for off, F0, F1, F2,
and F3, because the canonical construction supplies a lift in every case and
the flow variables do not alter the original objective. Therefore adding any
of F0--F3 cannot remove an original integral route or change the exact
original optimum, provided the production writer implements precisely these
rows and leaves the common original model unchanged.

## Exact extension sizes

The following counts cover only the connectivity-flow extension. $M$ is
the number of vehicles. Bounds are implemented as explicit arc-linking rows,
as reflected by the helper counter. Every entry in the table is **per
vehicle**; multiply it by $M$.

| variant | flow columns | upper-link rows | lower-link rows | station rows | depot rows | start rows | total rows | nonzeros |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F0 | $V(V+1)$ | $V(V+1)$ | 0 | $V$ | 1 | 0 | $(V+1)^2$ | $4V^2+6V$ |
| F1 | $V^2$ | $V^2$ | 0 | $V$ | 1 | 0 | $V^2+V+1$ | $4V^2+2V$ |
| F2 | $V^2$ | $V^2$ | $V^2$ | $V$ | 1 | 0 | $2V^2+V+1$ | $6V^2+2V$ |
| F3 | $V^2$ | $V^2$ | $V^2$ | $V$ | 1 | $2V$ | $2V^2+3V+1$ | $8V^2+5V$ |

For the nonzero derivation, every upper or lower link has two nonzeros. An F0
station row has $2V+1$, while an F1--F3 station row has $2V$. The F0
depot row has $3V$, while the direct F1--F3 depot row has $2V$. Each F3
start upper row has $V+1$ and each start lower row has $V+2$ nonzeros.

As a numerical cross-check, for $V=20,M=3$ the exact extension counts are:

| variant | columns | rows | nonzeros |
|---|---:|---:|---:|
| F0 | 1,260 | 1,323 | 5,160 |
| F1 | 1,200 | 1,263 | 4,920 |
| F2 | 1,200 | 2,463 | 7,320 |
| F3 | 1,200 | 2,583 | 9,900 |

Thus F1 removes $MV$ columns and $MV$ upper-link rows from F0. F2 keeps
the smaller F1 column set but adds $MV^2$ lower-link rows. F3 adds another
$2MV$ rows and $M(2V^2+3V)$ nonzeros to F2.

## Deterministic projection audit

The helper test exhaustively generated every elementary depot-closed route
for $V=1,2,3,4$, including the unused route. The route counts were

\[
1+\sum_{s=1}^{V}\frac{V!}{(V-s)!}=2,5,16,65,
\]

respectively. It checked the canonical F0--F3 lift, station and depot
balances, all applicable lower and upper links, return-column topology, edge
cases, the zero-extension dominance chain, and the F0 circulation examples.
It also checked the symbolic counts against direct column enumeration for
$V=1,\ldots,4$ and $M=1,2,3$. The executable reported
`ConnectivityFlowTests: 6 groups passed`. The CSV records these facts
explicitly and labels them as mechanical tests rather than solver results.

A targeted scan of only `include/ConnectivityFlow.hpp` and
`src/ConnectivityFlow.cpp` found no seed, named-instance, V12/V20,
route-mask, route-pool, or scale-tier token. The helper uses only $V$, $M$,
arc endpoints, and the explicit variant.

## Visit-count bound decision

No tighter unified $H_k<V$ was derived or used. In particular, this round
does not use route-mask enumeration, restricted route pools, heuristic route
failures, instance names, scale classes, or vehicle/station-count-specific
activation to tighten the flow bounds. F2 and F3 retain the universally valid
$V$ departure bound and $V-1$ internal bound proved above.
