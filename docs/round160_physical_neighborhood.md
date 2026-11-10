# Joint physical neighborhoods for the original Gini objective

This optional bounded primal component retains stable GI-TBC/S2 and E+
RN16384/proof-only identities. The default-off switch
--round160-physical-neighborhood on opens one inlet after this arm's complete
own H and existing R83 processing, before scope/RN consumes the incumbent.
The local optimizer returns complete physical routes, never a global lower.
Measured results live in results/unified_exact_round160/.

## Parent-containing physical domain

Let X be a verified fleet with inventory Ybar, B the released stations and
O its full complement, including unvisited stations. Visits in B split
each ORIGINAL parent route into maximal nonempty outside runs. Removing B
does not merge runs separated by a removed visit. Runs retain car, internal
order and relative order. At most g additional true outside internal arcs
are cut before optimization. New ports are optional; the old adjacency
remains legal. Free nonzero stations may appear at any run boundary/depot
end and in any order in a gap. Activation, zero service, direction changes
and eligible ownership changes are open. Zero service has no visit/owner.
Outside stock/owners are fixed; old-car quantity net need not be conserved.
Empty cars remain available.

N_B(X) also retains the original legal stock supports, total-stock bounds,
and the parent-inclusive nonstrict original-J scope J<=J(X)+1e-8. Thus the
contraction statement below concerns this complete declared domain.

The domain fixes indivisible runs and is smaller than allowing insertion at
every outside arc. With a active released visits, there are at most a+M
runs, then at most a+M+g after extra cuts. The nondepot primitive count is
at most 2b+M+g, b=|B|; preprocessing/validation still depend on n.

For run A, delta_i=b_i-Ybar_i. Store endpoints, internal travel, pickups
P_A, drops D_A, Delta_A=sum delta_i and minimum/maximum m_A,M_A of all
cumulative delta prefixes including zero. Entry load L is feasible iff
-m_A<=L<=Q-M_A, and exit load is L+Delta_A. Concatenation satisfies

    Delta_AB = Delta_A+Delta_B
    m_AB = min(m_A,Delta_A+m_B)
    M_AB = max(M_A,Delta_A+M_B).

Run handling is tp*P_A+td*D_A. There is no run-end unloading. Empty
departure and return R=P-D imply full handling tp*P+td*(D+R)=(tp+td)*P.
Cumulative pickups may exceed Q.

The macro MIP has unique nonzero stock/owner service, mandatory fixed runs,
degree equations, arc loads in [0,Q] with zero departure load, load
conservation and run-entry inequalities. Continuous MTZ order excludes
even zero-net disconnected cycles and preserves relative run order.
An explicit depot bypass permits an empty car. Exact boundary travel plus
fixed internal travel and full handling must satisfy original T.

**Expansion.** Degree and MTZ give connected elementary depot paths.
Unique service excludes duplicate ownership and zero transit. From empty
departure, arc conservation propagates free operations and run exits;
entry inequalities certify every run prefix. Internal/boundary travel and
handling preserve full time. Expansion is physical and respects the declared
fixed runs, stock supports, capacities and owners.

**Contraction.** Any physical fleet in the declared domain contracts its
runs. Actual loads, selected stock/owners and path ranks satisfy all macro
constraints, including prefix, time and relative-order rows. This is a
route/operation correspondence; continuous auxiliary variables need not be
unique. Contracting the unchanged parent and reinserting its B visits in
their original gaps/order gives a complete Start. Optional ports can keep
their old arc. Therefore X belongs to N_B(X), contained in D_P(T).

## Localizing the complete original objective

Use bound binary64 c_i=1/D_i and alpha_i=lambda*weight_i. An imported RN
omega already includes lambda and must be used directly. The new code
binds alpha once from the original parser. The original validator's division
form agrees to the independently checked rounding precision. Over ALL O:

    S_O = sum_O c_j*Ybar_j
    A_O = sum_{j<k in O}|c_j*Ybar_j-c_k*Ybar_k|
    H_O = sum_O alpha_j*|c_j*Ybar_j-1|
    psi_i(y) = sum_O |c_i*y-c_j*Ybar_j|.

For S>0 the exact identity is

    J = [A_O+sum_B psi_i(Y_i)+sum_{i<j in B}|c_i*Y_i-c_j*Y_j|]
        / [n*(S_O+sum_B c_i*Y_i)]
        + H_O+sum_B alpha_i*|c_i*Y_i-1|.

Original n remains; penalty is outside the normalization. One-hot x_iy,
t=1/S, w_iy=t*x_iy and rho_i=sum_y c_i*y*w_iy suffice. With valid positive
tl<=t<=tu, sum_y w_iy=t and tl*x_iy<=w_iy<=tu*x_iy enforce the integer
product. Enforce S_O*t+sum rho_i=1, a_ij>=±(rho_i-rho_j), and

    n*q >= A_O*t+sum_{i,y}psi_i(y)*w_iy+sum_{i<j in B}a_ij.

Minimize q+H_O+sum h_i(y)*x_iy, centering unary coefficients with a
recorded power-of-two scale. Recompute original J at every accepted
incumbent because its epigraph may be slack. Necessary total stock is
[max(0,sum b-sum Q),sum b]; supports retain original station capacities
and eligible operation sizes. The nonstrict parent-inclusive J scope is
parentJ+1e-8. Outside stock/support/total-stock bounds prove positive t
bounds. gamma_L=0 does not prove S>0. If all-zero stock is possible, an
independent fixed-zero physical branch uses G=0 without normalization;
the positive branch requires positive integer stock.

These are algebraic exactness statements. Native OPTIMAL concerns the
floating-point local model; this round claims no untransported exact-J
local optimum. Restricted bounds/infeasibility/no-improvement never enter
global proof. R133/R134 inclusive cutoff and zero repairs stay in the exact
engine. Model tolerances 1e-6 differ from original physical T tolerance
1e-7 and strict J acceptance 1e-10. Duration uses sqrt(dx*dx+dy*dy)/1.5.
Original-verifier rejection is an interface failure, never a physical upper.

## Frozen rule and actual complexity

Fix a pass queue of every station with more than one legal stock, sorted
by unconstrained single-stock original-J gain then ID. Keep zero-gain and
unvisited anchors; never reorder the remaining queue after improvement.
Alternate purely nearest geometric seats and best current marginal-gain
seats, skipping duplicates and tying by ID, to min(8,releasable) stations.
Rebuild runs/tables from the accepted parent after each improvement.

~~~text
X := original_verify(parent)
A := freeze_queue(all stations with legal stock variation, gain then ID)
for anchor in A:
    B := alternate_nearest_and_current_gain(anchor, X, min(8, releasable))
    ports := fixed_round_robin_minimum_insertion_cuts(X, B, total_g <= |B|)
    M := compact_full_J + mandatory_runs + joint_service + connected_load_time
    lift X into the complete MIP Start
    solve M with Seed0, Threads1 and the frozen node capacity
    on every strict improving stock incumbent:
        expand routes; recompute original J; original_verify
        save every accepted event and its time; retain the best valid fleet
    X := retained fleet (or unchanged X)
return X
~~~

For each outside internal arc, minimize true insertion increment over
free stations having some eligible nonzero operation on that car. Sort per
car by increment/endpoints and take the best unused cut in ascending-car
round-robin, globally capped at g<=b. Existing holes/depot gaps remain.
Solve joint quantity/owner/order from the complete Start with Seed0,
Threads1, MIPFocus1 and 512 nodes. Expand/original-verify strict improving
incumbents and save all accepted fleets. Finish one fixed anchor pass or
the existing whole-method deadline; original objective zero can terminate
by nonnegativity. No name/size/hardware dispatch or time-triggered switch.

For s_B=sum_B |support_i| and r_k available primitives on car k, the
objective uses O(s_B+b²) columns/rows; service/routes use
O(M*s_B+sum_k r_k²). Direct outside tables cost
O((n-b)²+(n-b)*s_B). Current marginal scoring evaluates
O(sum_i |support_i|) full O(n²) objectives. Source parsing, evidence writes
and original verification remain paid. NodeLimit does not bound root time
or imply polynomial complexity.

## Attribution and inference boundary

Subsequence concatenation and preprocessing are established in Vidal,
Crainic, Gendreau and Prins, EJOR234(3),658–673,
[DOI](https://doi.org/10.1016/j.ejor.2013.09.045),
[author report §3](https://www.cirrelt.ca/documentstravail/cirrelt-2013-22.pdf).
Aggregation, partially fixing routes and local decomposition are established
topics; see Santini, Schneider, Vidal and Vigo,
[Decomposition strategies for vehicle routing heuristics §3.2](https://optimization-online.org/wp-content/uploads/2021/03/Decomposition_Strategies_for_Vehicle_Routing_Heuristics.pdf).
These sources provide background, not performance evidence for R160.

R61 already jointly modeled physical quantity/owner/order for minimum time.
R76/R83 cover insertion, single/pair quantities, flips and equal-net
cross-car exchange. R96 already reordered then reoptimized quantities and
studied fixed-owner order. R159 jointly optimized resource stock/owner
without full travel/prefix feasibility in construction. R160 combines
original nonseparable Gini, signed service, heterogeneous owners and full
physical load/time in a small parent-containing domain.

Observed variable changes give scoped mechanism evidence, not proof that
every historical move sequence is unable to reach a new fleet. An
owner-fixed control restricts only previously served owners, leaving
unvisited activation/eligible owners equally open. Necessity requires a
qualified restricted lower above the joint physical upper; raw Native
bounds are insufficient. Complete self-paid results are needed for any
complete-method gain claim.

## Finite physical evidence and complete-method outcome

The intended pre-scope/RN own-H parents have J=.4246498451636405 (RX35)
and .5772179446388801 (NB35). A complete 35-anchor pass with b=8, total
g<=8 and 512 nodes per block obtains .4016200111731245 and
.4900715637577154, with 12/22 strictly improving, fully physical events.
Outer costs are 40.9668595/65.6695970 seconds. All quantity vectors,
eligible owners, complete routes and original-T checks are saved. These are
early-parent gains, above the historical late uppers .2996694007364017 and
.450291503262878; they are not new historical-best physical bounds.

RX/NB cover all 35 releasable anchors, 28/31 unique blocks and 36/42
unique extra vehicle-arc ports. Across 280 selected ports per source,
87.14%/85.0% repeat. Native statuses are 12/16 OPTIMAL and 23/19 NODE_LIMIT.
One uniform evidence-based revision to 2048 nodes raises OPTIMAL counts
to 18/22 but yields worse terminal J=.4186767011062194/.4951307115747831
at 100.3456037/148.8609335 seconds. More local work changes the sequence of
accepted parents, so it need not improve a bounded pass. No further grid is
run; the 512-node recipe is frozen for complete comparison.

In one NB joint event quantities at 7,11,12,16 and old served owners 12,16
change together with order on car0. Block-parent J=.5749270842499868 falls
to .5596946598780417; car nets change by [1,-1,0]. The matched old-owner-fixed
control, retaining unvisited activation/ownership freedom, finds
.573413506045513 in 0.8298238 seconds at 512 nodes. Its raw restricted
bound is not transported, so the observed difference does not prove owner
necessity. No claim about unreachability by all historical closure sequences
is made. Tiny exhaustive/locked-arc checks establish semantic equivalence,
not a compression-speed benchmark.

Eight fresh serial same-PE off/on arms pay all components from one total
production deadline, followed by separately charged verification. E+R runs
only after its own H/R83 and before scope/RN; no offline route or local lower
is loaded. Seed0/Threads1, own-H seed20260626 and the shared E+ helpers are
fixed. The resulting complete uppers and production time to certificate are:

|Role|E+ U|E+R U|E+ / E+R T_cert (s)|
|---|---:|---:|---:|
|RX35|.2996694007364017|.3750434752252407|open / open|
|NB35|.4502915032628780|.4540598501089633|open / open|
|K20|.7168065462777502|.7168065462777502|open / open|
|RX20T1|.6453250303858205|.6453250303858205|21.937043 / 36.606473|

The local online costs are 41.4654254,65.6103181,14.6207349,15.1338196
seconds respectively, with 35,35,20,20 calls and 12,22,0,5 accepted events.
RX20T1 T_total including verification rises from 23.829507 to 38.497449
seconds. Complete raw/proof lowers, gaps, cost components and call counts
are in results/unified_exact_round160/reports/complete.csv. A qualified
OPEN certificate state is distinct from an actual certificate.

This finite study supports a mathematically valid, physically productive
local construction but no complete-method U gain on the four roles, with
two worse endpoints and a fast-certificate delay. The interface remains
default off. These data do not establish global impossibility, general
performance, P-GRB superiority or independent confirmation. All local
bounds stay outside the global proof ledger.
