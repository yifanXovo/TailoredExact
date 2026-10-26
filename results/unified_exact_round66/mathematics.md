# Arc load replacement: scope and proof

The candidate retains the original station objective, route support, order,
visit/mode, single nonzero service, inventories, duration, symmetry and F0
interval/cutoff constraints. It replaces only the two node-load recurrence
inequalities for each depot-to-station and station-to-station arc. The retained
`load[k,i]` is continuous, and is defined by outgoing arc load. No old objective
assignment, input, tolerance or official P-GRB model is modified.

For each vehicle let q[i,j] be nonnegative load on station-origin arcs, including
return arcs. Depot-origin load is identically zero. Impose

    0 <= q[i,j] <= Q x[i,j]
    sum_j q[i,j] - sum_h q[h,i] = p[i] - d[i]
    load[i] = sum_j q[i,j].

There is no depot load-balance equality. In particular returns may carry load.
The per-route duration is travel + (c_pick+c_drop) sum_i p[i] <= T.
Capacity bounds individual prefixes, not cumulative pickup.

## Integer correspondence

Existing route degrees and order constraints produce elementary depot routes
(connectivity flow also remains). On an integer route, q on the only outgoing
arc is exactly the preceding load plus integer pickup minus delivery. Starting
from zero implies every prefix is integral and in [0,Q]. Conversely assign each
q to a legal original prefix and zero on unused arcs. All retained load names
have their original values. This proves correspondence on original route and
operation variables, including identical final inventory and objective, for
every supported input and every current interval/cutoff. It does not require
metric travel, equal capacities, positive handling, or empty return. The old
symmetry constraints retain precisely their existing representative scope.

## Continuous equivalence to the Q-plus control

Write A_i=sum_h q[h,i] and B_i=sum_j q[i,j]=load_i. For a station arc (i,j),
the shared q[i,j] cancels in A_j-B_i. The remaining incoming flow is at most
Q(z_j-x[i,j]); the remaining outgoing flow is at most Q(z_i-x[i,j]). Hence

    -Q(1-x[i,j]) <= load_j-load_i-p_j+d_j <= Q(1-x[i,j]).

Likewise A_i is nonnegative and at most Q(z_i-x[0,i]), implying both old
depot-first recurrences. Thus Q plus the old recurrences and Q without them
have the same continuous feasible region on all common coordinates. Relaxing
the derived load integrality changes no integer route projection. This is
an algebraic proof, not an inference from saved witnesses or equal root bounds.

## Size, rationale, and limits

Compared with historical F0, add M V^2 continuous q columns and M(V^2+2V)
flow rows; remove 2 M V^2 recurrence rows and M V integer declarations. Relative
to Q-plus the columns are unchanged and 2 M V^2 rows disappear. Final-load,
duration, order and connectivity rows stay present. Native presolve may already
remove some redundancy, and changing branching candidates can help or hurt.
The hypothesis concerns full native and end-to-end cost, not improved LP value
over Q-plus. No new theoretical inequality or general speed theorem is claimed.

The controller remains K1-AM with full paid HGA, legal event retention and
verified-zero termination. All Round65 credit/projection controls are off.
Only the common complete-run deadline is used; a timed-out component ends the
run. Gurobi remains the complete MIP engine, with the inherited mathematical
bound-target stops. Exactness means the existing numerical certificate contract,
not an unimplemented rational certificate.
