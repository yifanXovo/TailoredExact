# Shared load and prepaid final-route duration

All original rows, objective, S=0 convention, one nonzero unidirectional service,
empty departure and possibly loaded return remain. Common T/handling and actual
vehicle-specific Q are read from the existing interface. No total-pickup cap.

The unchanged objective is `F=H/(n*S)+lambda*sum_i omega_i*abs(Y_i/D_i-1)`,
with `Y=b+sum_k(d-p)`, `S=sum_i Y_i/D_i`, and
`H=sum_(i<j) abs(Y_i/D_i-Y_j/D_j)`. The original S=0 handling remains in
the verifier. Route duration is original travel plus
`(pickup_time+drop_time)*sum_i p_ki`, including the prepaid unloading cost
of cargo returned to the depot. Capacity constrains every prefix load.

## Integer embedding and continuous containment

On route 0,i1,...,im,0, q on each outgoing station arc is the post-service load
L; all unused q and depot outgoing q are zero. Prefix feasibility gives
0<=q<=Q_k x. Differences are p-d and outgoing q sums to L. The original
L<=Qz row makes unvisited L zero. No depot balance forces return cargo to zero.
Summing q balances over W yields the familiar inventory/capacity cut families;
the new explicit lift also connects individual vehicle/node L. Optional historic
InventoryRouteCuts uses aggregate capacity sum_k Q_k x and net final-initial
inventory (or projected inventory domains). Core F0 enables none of its optional
root closures. We do not attribute familiar q flow to new coupling.

More explicitly, `InventoryRouteCuts.cpp::buildRow` generates, for a station
set W (depot outside W), the two global mixed rows

    sum(i in W) (Y_i-b_i) <= sum(k, (h,i) in delta-(W)) Q_k x_khi,
    sum(i in W) (b_i-Y_i) <= sum(k, (i,j) in delta+(W)) Q_k x_kij.

Its domain-projected forms replace the left side respectively by
`max(0,sum(Y_lower-b))` and `max(0,sum(b-Y_upper))`; their scope is the
interval/domain that justified those bounds. Summing the Round64 q balances
over W and k yields incoming q minus outgoing q equal to `sum(Y-b)`.
Nonnegativity and q capacities imply both mixed rows and hence their valid
domain-projected versions. This derivation does not cap cumulative route
pickup by Q. Round64 keeps vehicle-specific balances, exact outgoing-q/L
links and zero depot departures; it does not assert equivalence to the old
aggregate cut closure. The actual inherited F0 preset lists
`inventory_route_root_closure` as inactive and sets root cut rounds to zero.
The new arc sharing is an additional restriction after this familiar Q lift
and the independent T/B4 control have already been included.

Use prepareRound63Time once: s=max(1,T), cbar downward rounded
(pickup_time+drop_time)/s, taubar downward rounded original directed costs/s,
B_ij an upward rounded max(0,(T-tau_ij-shortest(j,0))/s). Shortest paths use
nonnegative directed costs with downward rounding. On the same route set
f_ij=sum(prefix arrival taubar)+cbar*sum(prefix pickup). Remaining travel is
at least the direct remaining arc plus a shortest path to depot, so f<=Bx.
Conservative coefficient rounding gives a safe relaxation of the physical
duration, whose original verifier remains authoritative.

Let h=f-cbar*q. Algebraically, with exactly the SAME stored cbar on both
sides, balance(h)=incoming taubar*x+cbar*d. Canonical h is prefix travel
plus cbar times cumulative deliveries, hence nonnegative. The upper bound is
h+cbar*q<=Bx. Conversely h>=0 with that balance reconstructs f=h+cbar*q and
all original time balances. This is an invertible auxiliary-variable transform;
no additional bound on h is introduced. The implementation uses f/q, avoiding
an extra h block. h remains an independently computed embedding check.

Zero handling makes arc sharing redundant (f>=0), and the implementation
omits these redundant rows. Positive or zero nonmetric/asymmetric arc costs,
heterogeneous Q, repeated capacity recycling and loaded return preserve every
argument. Resource zero does not replace connectivity. These are final-route
accounting identities, not arrival clocks or time windows.

Q=F0+q balances/capacities/L links; T=F0+time block;
SEP=F0+Q+T+cbar*L<=out(f); JOINT=SEP+cbar*q<=f.
Thus projection(JOINT) is contained in projection(SEP), and both in Q and T.
Q and T have no asserted dominance over one another. At a recorded original
point all columns of canonical F0 are pinned, including its own auxiliaries;
new q/f remain free. Only a valid feasible SEP control and strictly infeasible
JOINT establish exclusion. Testing a particular auxiliary assignment is weaker.

For positive handling, with V stations and M vehicles, Q adds MV^2 continuous
columns and M(V^2+2V) rows; T adds MV^2 columns and M(V^2+V) rows. SEP adds
2MV^2 columns and M(2V^2+4V) rows. JOINT has the same columns as SEP and
M(3V^2+4V) added rows. Fixed-zero departure columns are eliminated and return
columns remain. D7 therefore adds 10,000 q columns, or 20,000 q/f columns;
JOINT adds 10,000 sharing rows beyond SEP. These are pre-presolve increments,
not predicted runtime gains. Actual native/presolved dimensions and costs are
reported separately. Zero handling omits both vacuous B4 and sharing rows.

## A bounded local separating example, before optimizer measurements

This compares resource blocks, not yet every F0 row. One vehicle, Q=1,
T=10, c=1, arcs 0->1=1, 1->2=.9, 1->0=.1, 2->0=.9.
Travel tau12=9.9, other used costs zero. p1=.5, d2=.4,
L1=.5, L2=0. SEP completion: q12=.4, q10=.1, q20=0;
normalized f12=0, f10=.05, f20=.891. It satisfies station balances,
capacities and node aggregate lower bounds. JOINT implies
cbar*L1 <= sum_j min(cbar*Q,B_1j)*x_1j = .019 < .05,
so no reallocation can repair this point. Safe rounding changes neither strict
inequality. This provides a compact independently checkable separation proof
and illustrates why B4 node sums cannot settle the arc allocation question.
Some other F0 rows may exclude this example: real target-LP evidence is separate.

## Projection evidence and scope

For fixed physical data write the auxiliary feasibility system A z <= b(v),
with equalities represented as two signed rows and nonnegative auxiliary z.
A Farkas vector y>=0 with y^T A>=0 implies y^T b(v)>=0 for feasible v.
If y^T b(v0)<0, it excludes v0. For free variables the corresponding dual
column residual must be zero. Finite lower/upper bounds must enter the system;
no bound term may be silently dropped. Normalize by a positive norm, verify
all signs, column residuals and raw-point violation; bind coefficients to
physical identity and to any diagnostic pin/cutoff premises. A solver status
alone is not a submitted cut. No shared-network single-commodity mincut
equivalence or complete projection separator is asserted.

Current production experiment is static explicit formulation, with no Farkas
cut submission. The local inequality above has a direct nonnegative derivation
from arc q/Q, shared and time capacities plus out(q)=L; it is globally physical,
independent of objective interval/cutoff. If a projection execution is later
chosen its certificate implementation must be separately tested and recorded.

## Bounded full auxiliary dual diagnostic (after the initial target matrix)

The independent diagnostic constructs only q/f resource variables, with
Q/time capacities, q/f balances, q-to-L links and B4 in both controls; JOINT
adds arc sharing. Original F0 values appear solely as affine right-hand sides.
Two optimizations share one process cap. Both use diagnostic InfUnbdInfo=1 and
DualReductions=0; production settings do not change. SEP must be feasible.

For the actual resource model all q have finite global upper Q_k and all f
have finite global upper B_ij (because physical x is binary). These are redundant
also on the original continuous x domain [0,1]. Given a normalized Gurobi
Farkas multiplier vector, retain free equality multipliers and project inequality
multipliers onto the nonnegative half-line. Recompute the entire combination;
do not reuse the old reported proof after changing multipliers. Put a=y^T A.
The valid original-variable row is

    y^T b(v) >= beta = sum_z min(0,a_z * upper_z).

This accounts for ALL negative column residuals through finite physical bounds;
it never pretends a slightly negative a_z is nonnegative or silently drops
bound terms. Recompute coefficients/activity with long-double accumulation and
independently with Python math.fsum. Require agreement and strict raw violation
above 1e-7, alongside feasible SEP/control residual checks. Export raw and
normalized multipliers, every matrix/RHS term, column sums, finite-bound
corrections, original-variable row, physical identity and raw-point checksum.
These are numerical-supported projection certificates and are not submitted
to native search. They are not certificates of original objective optimality.

The sign convention and bound contribution follow the official
[Gurobi FarkasDual/FarkasProof definition](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/constraintlinear.html#attrfarkasdual).
The required diagnostic flag is documented under
[InfUnbdInfo](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter.InfUnbdInfo).
