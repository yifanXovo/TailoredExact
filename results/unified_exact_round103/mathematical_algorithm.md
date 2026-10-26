# Round103 resource-hull method

The research domain is the **actual R102 conservative floating resource
predicate**, not a nominal real-arithmetic surrogate. Every original station
can be skipped or receive one integer, one-direction nonzero service. Its
pickup/drop maxima are min(initial,Q) and min(capacity-initial,Q). Total
drop cannot exceed total pickup at the final state. Intermediate D>P and
cumulative P>Q remain allowed. The maximum safely rounded singleton round
trip plus safely rounded handling cP must fit the outward horizon. The
necessary service plans are not physical routes and supply no route UB.

For physical coordinate widths s=(pickup cap,drop cap,1), after checking
zero widths, the normalized infinity distance to the full convex hull is

    min ||s^-1(v-sum lambda*r)||_infinity
    = max {w*v-h(w): sum s*abs(w)<=1}.

The finite-column primal has lower rows sum(r/s)lambda+t>=v/s, upper rows
sum(r/s)lambda-t<=v/s, and mass one. Its dual direction is the sum of the
two row multipliers divided by s. A finite-column distance is an **upper**
bound on the full-hull distance. Its positive value is never an outside
certificate. Valid positive raw lambdas are normalized mathematically as
exact(raw)/sum exact(raw); they are rational, not necessarily dyadic.

Python diagnostics validate combinations with exact binary-rational
arithmetic. Production encloses that same mathematical normalization with
outward interval sums, products and division. INSIDE means an explicit
combination has verified normalized residual <=1e-8. It does not assert
strict rational equality at the original floating point or exclude all
smaller-scale separations.

Dual directions are safely normalized, quantized to integer weights at
2^bits (bits=max(30,ceil(log2(4*sum(s)/1e-8))), at most48), and repriced on
the complete necessary domain. The nearest-dyadic error envelope is bounded
using the global physical widths. The actual cut uses only the repriced
dyadic direction, so no approximate continuous support replaces its RHS.
The DP support value is an exact integer maximum under the declared
predicate and arithmetic range. A returned legal plan only attains that
maximum; its feasibility alone would provide a support lower bound.

OUTSIDE requires downward-enclosed signed activity minus the safely
represented full-support RHS to exceed the declared normalized tolerance.
UNKNOWN preserves combinations, valid bounds and attempts when precision,
resource limits, duplicate columns or incomplete LP optimization prevent
closure. Structural limits are4096 service columns, resource dimension2048,
and67,108,864 traceback cells. Internal verification, contract, API and
persistence failures propagate as durable failures, rather than UNKNOWN.

The witness DP retains all stations and stores signed operation traceback
at each station layer; final winners bind resource quantities, travel
level and optional mask. Independent enumeration covers1728 signed base
and552 signed three-anchor cases. Injected-master fixtures separately
check restricted-distance misuse, explicit membership, signed separation,
fixed widths, duplicate UNKNOWN, incomplete master and invalid contract.
These fixtures do not substitute for actual Gurobi/native qualification.

## Same-scope capability

The full old objective LP is reoptimized after adding only certified
global rows. An optimal current point with an explicit member combination
for every vehicle closes the convexification within the declared member
tolerance. Incomplete iterations retain only the valid outer LP lower
bound. A finite-column restriction of that objective LP instead supplies
a numerical feasible **upper witness** on the hull objective. It is never
an original BRP lower bound, and its plans never certify a route incumbent.

## Unique-access boundary

If v_k belongs to each H_k and sum_k z_ki<=1, for any w_k and mu_i>=0,
support domination gives h_k(w_k-E_k^T mu)>=(w_k-E_k^T mu)*v_k. Summing
and adding sum_i mu_i yields at least
sum_k w_k*v_k + sum_i mu_i(1-sum_k z_ki)>=sum_k w_k*v_k.
Thus this Lagrangian recombination of the existing linear unique-access
row cannot exclude that point. It may improve finite-direction search;
the statement does not address the stronger joint integer vehicle hull.

## One investigated domain strengthening

For a fixed set of at most three anchors, the directed shortest-path
closure gives a safe minimum closed tour through each selected anchor
subset. A physical route visiting that subset induces an anchor order;
shortest-path lower bounds and outward-rounded additions are no larger
than its travel. Taking the maximum of this bound and the singleton bound,
then adding total handling, therefore remains necessary. The mask DP has
at most eight times the base states and retains all external supplier and
receiver stations. Its domain is contained in the base domain and still
contains every physical single-vehicle projection.

Anchors are selected from actual paid combinations by weighted positive
resource deficit, preferring smaller then lexicographic sets on ties.
Selection is heuristic; every exclusion and support is certified anew.
Discarding a particular mixture plan does not discard the original point:
the point must be classified again, and may remix to INSIDE. Python and
C++ floating selection can differ at near ties, without changing validity.
The inherited pair/triple support rows account only for their supported
pickup service; the investigated mask condition counts all-station handling.
Actual full-matrix point separation is still required to claim increment.

## Production candidate

The selected candidate uses the **base** domain and a single pre-MIP pass
for each new qualified canonical terminal or partial-target model. It
reads and audits the complete original typed matrix, copies it with only
types relaxed, obtains a self-paid standard LP optimum, and classifies
each vehicle. It writes at most one reliable OUTSIDE row per vehicle.
It neither imports the diagnostic closure rows nor implements full-hull
closure at the root or tree. All auxiliary Optimize and DP attempts are
logged before execution. The only temporal interruption is the complete
algorithm's remaining global deadline.

Rows receive exact power-of-two scaling. Reliable scaled violation must
exceed ten times the unchanged official FeasibilityTol. Original LP bytes
are preserved and17-digit row text is inserted before Bounds. Before any
MIP, readback compares all original names/order/types/bounds/objective,
constant/sense, original rows and coefficients, and exact new coefficients
and RHS. The resulting canonical SHA and row signature replace the native
identity. Cache reuse binds original SHA, leaf, scope, row signature,
gamma interval, cutoff, input SHA and mode. An old retained model is
discarded only on identity change before starting the new MIP. Formal
Start mapping checks every original/new row. Shadow pays the same pass
but writes no rows. There is no callback Optimize, PreCrush change,
per-cut search interruption, internal timer or Work dispatch rule.

Preparation cost is included in whole-process receipts and native-event
replay clocks. Official MIP Threads1, Seed0, PresolveAuto, zero gaps and
original certificate tolerances remain unchanged. Auxiliary distance LPs
use numerical precision1e-9 in their own disposable environments; primal
or dual solver attributes alone do not certify an emitted row or member.
