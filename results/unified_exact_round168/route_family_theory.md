# Complete route families and numerical target certificates

This note defines the domain actually constructed by
`src/round168_route_family.cpp`. It inherits the R96 fixed-order diagnostic;
the implementation and the present archive evidence are new, not the idea
of optimizing quantities on a route. The isolated tool never contributes
a bound or incumbent to GI-TBC/B. C166/D167 are absent.

## Physical domain and nesting

Inputs, normalized weights, positive targets d_i, capacities C_i, initial
stocks b_i, vehicle capacities Q_k, mathematical T, pickup/drop seconds
and lambda are fixed. Every vehicle leaves empty, follows a depot tour,
serves any station at most once in the whole fleet with a positive
one-way integer operation, and can return loaded, paying its unloading.
Empty tours are (0,0). A canonical fleet has exactly one route per vehicle;
missing empty records are filled and duplicate vehicle records are rejected.

For a verified parent p, pi_k is its ordered nonzero service sequence,
E_k its set, and E their union. Outside E, Y_i=b_i and there is no visit.
Inside E, Y_i can be any integer in [0,C_i]. Y_i=b_i deletes the service;
otherwise pickup=max(b_i-Y_i,0) and drop=max(Y_i-b_i,0). Signs, net vehicle
quantities, terminal loads and old travel are not fixed.

F_order retains original owner and a subsequence of each pi_k. F_owner
retains owner but permits every ordering of the retained E_k. F_eligible
permits every assignment of retained E to original vehicles and every
ordering. Thus F_order is contained in F_owner, which is contained in
F_eligible, which is contained in the original full physical problem.
The parent is in all three. Containment follows by retaining the old
assignment/order when a restriction is released, including empty routes.
Vehicle labels index input capacities. A *whole* fleet may be relabeled
only by a permutation preserving every relevant vehicle attribute; here
Q is vehicle dependent, while T and operation times are common inputs.
Relabeling itself is not evidence of an ownership change. Deduplication
need not quotient every vehicle symmetry. The actual nine ordered parents
have distinct identities even before symmetry quotienting.

## Shared global objective

For every station, binary s_iy chooses exactly one legal stock: all
0..C_i for i in E and the singleton b_i outside E. No old child bound,
stock contraction, incumbent row or target cutoff is imported. Let
r_i=sum_y (y/d_i)s_iy. The continuous G domain is the full original [0,1].
For each s, q_iy has 0<=q<=s, q<=G, q>=G+s-1, with sum_y q_iy=G.
At integer s this gives q_iy=G*s_iy. Continuous e_i>=r_i-1 and
e_i>=1-r_i represent target deviations. For every i<j, h_ij>=r_i-r_j
and h_ij>=r_j-r_i. The single global row is

    sum_{i<j} h_ij <= n sum_i sum_y (y/d_i) q_iy.

The minimized objective is G+lambda*sum_i w_i e_i, using the actual
normalized input weights and lambda. If S=sum r_i>0, the row implies
G>=sum_{i<j}|r_i-r_j|/(nS). If S=0, all stocks are zero, h=0 is feasible
and the minimum G is zero, as in the original evaluator. Since lambda
and weights are nonnegative, epigraph slack can only increase the model
objective. Every physical fleet has an extension with true G and exact
absolute deviations attaining its physical F. Every integer model point
decodes to a physical fleet with F no larger than its model objective;
slack epigraph points need not equal true F. Consequently the *minimum*
is exactly the family minimum, and no epigraph artifact can create a
false low bound or false low feasible physical objective. Inventories
on different vehicles share all Gini pairs and the denominator. The
problem is not decomposed into separate vehicle objectives.

## Service and routing block

For each allowed (k,i), binary z_ki selects a visit, and p_ki,d_ki are
nonnegative continuous quantities. Their bounds are b_i z_ki and
(C_i-b_i)z_ki. Across allowed vehicles impose

    sum_k z_ki = 1-s_i,b_i,
    sum_k p_ki = sum_y max(b_i-y,0)s_iy,
    sum_k d_ki = sum_y max(y-b_i,0)s_iy.

Only the original owner has columns in order/owner; all original vehicles
have columns in eligible. At integer s,z, there is exactly one served
owner iff Y differs from b. All quantities are then the selected integer
one-way operation, despite their continuous declaration. There is no
simultaneous pickup/drop and no phantom zero service.

Each vehicle uses separate source and sink copies of the depot. The
source has one selected outgoing arc and the sink one incoming arc. Each
eligible station has incoming and outgoing degree z_ki. The source-to-sink
bypass is the empty route, with zero physical travel. Every selected
non-bypass arc carries the *original* distance of its endpoints, treating
both depot copies as physical node 0.

For order, arcs follow the strict order of pi_k, including every possible
skip arc between retained stations. This acyclic degree system describes
exactly one compressed subsequence route; disconnected directed cycles
cannot occur. For each original prefix impose

    0 <= sum_prefix (p_ki-d_ki) <= Q_k.

Deleting a station changes neither prefix net load nor legality. Prefix
constraints therefore enforce every retained visit's true load, including
the terminal load, and impose no old terminal load equality.

For owner/eligible, every distinct allowed station pair is an arc. A rank
variable t_ki satisfies z_ki<=t_ki<=m_k z_ki, and for each station arc
(i,j), t_kj-t_ki >= 1-(m_k+1)(1-x_kij). This forbids a cycle disconnected
from the source. Degree plus acyclicity leaves one path to the sink and
no extraneous served component. With m_k=0 only the empty bypass remains.
Arc loads obey 0<=l_kij<=Q_k x_kij, with every source arc's load fixed
to zero. At each station, outgoing load minus incoming load equals
p_ki-d_ki. Along the unique path these are the exact physical prefix
loads; the sink receives the legal terminal load without forcing it zero.
No total-pickup<=Q constraint is imposed.

All three scopes use

    sum_arcs travel_ij*x_kij + (tp+td)*sum_i p_ki <= T.

To justify the handling coefficient, empty departure gives terminal load
R_k=P_k-D_k. The actual station handling plus return unloading is
tp P_k + td D_k + td R_k = (tp+td)P_k. This uses the inherited uniform
per-unit pickup and drop seconds, including the same drop seconds at the
depot. It allows cumulative P_k>Q_k and loaded returns. With other depot
or station-specific handling rules this identity would require revision;
those rules are not silently accepted. Mathematical T is unchanged; only
the inherited 1e-7 physical acceptance tolerance is used in verification.

## Two-way construction and boundary cases

Given a family fleet, choose its stocks in s, its true G in q, exact
deviations/pairs, its unique owner in z, its operations in p,d, its actual
compressed arcs in x, and (for free order) its post-service loads in l and
route positions in t. The stock, degree, rank, prefix, load and time rows
all hold, with the original objective. The parent Start uses this
construction for *every actual column*, including zeros, then reads back
every matrix row, bound and integer type and reverse-decodes the vector.

Conversely integer s,z,x produce optional one-way integer service and a
single depot path per vehicle as above. Prefix or arc-load conservation
proves empty departure and every capacity bound. The time identity gives
the original loaded-return physical time. Outside E is fixed, all visits
are unique, and order/owner restrictions follow from missing columns/arcs.
Hence decoding is in the declared family. The global epigraph proof
ensures its physical objective is no larger than the model objective.
This covers S=0, no eligible station, an empty vehicle, one service,
pickup/drop flips, arbitrary deletions and exact load/time boundaries.

The independent C++ oracle enumerates every stock vector, every allowed
owner allocation and every allowed retained permutation in two frozen
four-station instances. Its feasibility arithmetic and long-double
objective evaluation do not read model columns or reuse the matrix
generator. Actual model row checks additionally embed each oracle optimum
and parent, plus structural-release witnesses in the larger admitting
scopes. The saved S=0 fleet is embedded in eligible; that cross-owner
fleet is not in order or owner. Rejection in a smaller scope is an
explicit structural membership gate before row mapping: absent owner
columns or absent reverse-order arcs preclude its embedding. The raw
mapping record's residual=-1 denotes "not mapped", not a row residual.
Six tiny MIPs must agree with their respective enumeration
optima before a substantive query. This is complete discrete enumeration
plus the declared floating numerical qualification, not a symbolic proof.

## Target verdicts, qualified bounds and propagation

The closed six-record B/P target pool is fixed separately for each of
three physical inputs. C++ rechecks every final fleet and uses their
minimum true F as tau. Freeze theta=tau+1e-7 before any new Optimize.
Tau is an attained archive value, not a known optimum. Native is fixed
to Threads1/Seed0, exact-zero relative and absolute requested gaps and
the inherited default tolerances 1e-6/1e-5/1e-6. No per-position tuning.

The saved physical parent always supplies U<=F_p. A finalized error-free
Native lower is accepted only on this complete restricted model, with
the actual model hash, original types and parameter identity, a finite
bound, an accepted status (2/9/11/15), no available-solution quality or
decoding failure, and raw bound<=physical U+1e-7. Solution row/bound/type
residuals and Native violations, when available, must be <=1e-7. The safe
lower is max(0,nextafter(raw_bound-1e-7,-infinity)). Without a qualified
finite Native lower the nonnegative objective still supplies L=0; the
raw Native field remains unchanged or null. This is an engineering
numerical policy, not a rational solver certificate.

HIT requires an actual family fleet passing the original checker with
F<=theta. A MIPSOL vector is independently physically decoded before
requesting an evidence stop; an unphysical candidate is ignored. EXCLUDED
requires final qualified L>theta. A tentative callback bound stop must
still pass the final gate. Otherwise the result is UNKNOWN, including an
improvement short of target or a 300s limit. A model/API/mapping failure is
an error, never silently converted into a scientific UNKNOWN. In a valid
model, failure to numerically accept a particular Native lower instead
leaves any independently valid physical U and mathematical L available,
with that rejection explicitly recorded and the result honestly UNKNOWN.

For j=order,owner,eligible, L_j<=v_j<=U_j<=F_p, while
v_order>=v_owner>=v_eligible>=F*_full. Larger-domain lower bounds may
strengthen subdomains; subdomain physical fleets may strengthen supersets.
The opposite directions are invalid. Raw and propagated fields and their
source positions are both saved; finite-time raw bounds need not be
numerically monotone. The order quantity potential is
[F_p-U_order,F_p-L_order]. The obstacle relative to theta is bounded by
[max(0,L_order-theta),max(0,U_order-theta)]. None is an original global
proof lower or a performance result.

An order exclusion with an owner HIT makes leaving the old relative
order necessary *within this old owner/eligible family* and unrestricted
reordering sufficient. An owner exclusion with an eligible HIT requires
some owner change within old E; the witness may also reorder and change
quantities. Eligible exclusion requires serving at least one station
outside old E in every target-reaching full solution. A smaller UNKNOWN
does not establish any structural necessity. These conclusions concern
the saved parent, not all possible algorithm states or independent inputs.
