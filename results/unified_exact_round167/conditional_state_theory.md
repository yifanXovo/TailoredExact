# Conditional joint stock information

## 1. Objects and a strict loss in the independent code layer

Let D=[l,u] intersect Z, 0<=l<=u<=C, b in [0,C] intersect Z,
0<=alpha<=beta<=1, d=max(1,bit_width(C)), and let c(y) be the d-bit
absolute base-2 code, indexed from the least significant bit 0. Put
m(y)=|b-y|, v(y)=1[y!=b], X=(Y,M,V,g,Z). Define

    H(D)=conv{(y,m(y),v(y),g,gy):y in D,g in [alpha,beta]},
    E(D)=conv{(y,m(y),v(y),g,gy,c(y),g*c(y)):y in D,g in [alpha,beta]}.

The enhanced coordinates are delta=c(y), w=g*c(y). R_abs has continuous
s_y,q_y, sum s=1, sum q=g, alpha*s_y<=q_y<=beta*s_y,
Y=sum y*s_y, M=sum m(y)*s_y, V=sum v(y)*s_y, Z=sum y*q_y,
delta_h=sum c_h(y)*s_y, w_h=sum c_h(y)*q_y. For positive s_y,
q_y/s_y is a legal g; zero s forces q=0. These are exactly the convex
combinations defining E(D), with the reverse obtained by aggregation.

**Strict witness.** Take D=0..4,b=2,[alpha,beta]=[0,1/2],delta_0=1.
The true conditional domain is {1,3}, so M=V=1 in its hull. In C166 use
t_2=1,q_2=1/4 and all other support weights zero. This gives
Y=2,M=V=0,g=1/4,Z=1/2. Set delta=(1,1/2,0), w=(1/4,1/8,0).
Mass/Y/M/V/g/Z reconstruction and q bounds all hold. Binary reconstruction
gives 1+2*(1/2)=2 and 1/4+2*(1/8)=1/2. The three global inequalities are
w<=g,w<=delta,w>=g+delta-1. The interval inequalities are
0<=w<=delta/2, w>=g-(1-delta)/2, w<=g. For h=0 they require w_0=1/4;
for h=1 they allow [0,1/4], containing 1/8; for h=2 they require 0.
All column bounds hold. Thus the independent code layer loses common
service mixture information after fixing a digit. C166 remains integer
correct and preserves H(D) before conditioning. This witness says nothing
about which branch domains Gurobi visited in the historical X20 run.

**Physical support lemma, including holes.** For a partial bit assignment F,
let D(F)={y in D:c_h(y)=a_h for h in F}. In each nonempty donor part y<b
retain its minimum and maximum legal members; similarly for the receiver
part y>b; retain b if legal. There are at most five supports. On either
side (y,m(y),v(y)) is affine, so any legal interior member is a convex
combination of its side's legal extremes at the same g. The product gy
is affine in y at that same g. Replacing each graph term this way proves
the supports generate H(D(F)); the reverse follows from legality. Missing
interior members cause no problem for this physical convex hull. They do
matter for integer membership, and for E(D(F)): the digit map need not be
affine between these extremes. This lemma does not compress E to five states.

## 2. One fixed graph, with explicit constants

Split D into donor [l,min(u,b-1)], singleton {b} when legal, and receiver
[max(l,b+1),u], omitting empty parts. Let r<=3 be their count. Each part
has an independent entry from a common source and no intermediate sharing
with another part. Within [a,z] read every absolute bit MSB to LSB. A
layer state records whether the prefix is still equal to the lower prefix
and to the upper prefix. From each reachable state try 0 then 1; reject a
digit below the lower digit when lower-tight, or above the upper digit when
upper-tight. The next tightness flags remain true exactly on equality.
After d digits, connect every reached terminal state to the common sink.
No stock enumeration is used to construct the graph.

Induction on prefix length proves that the reachable states describe
exactly the prefixes extendible into [a,z]. The same tightness flags imply
the same legal suffix choices. Every legal y selects exactly one entry
and one edge at each bit, hence a unique complete path. Conversely every
successful path spells a stock in its own interval, hence in D. There
are no skipped bit levels, spurious stock paths or cycles. Forward-reached
states always have a feasible suffix, so no additional pruning is needed.

With n_G nodes and a_G edges, the implemented unsimplified construction has

    n_G <= 2+r*(1+4d),      a_G <= r*(8d+5).

There is one entry per part, at most four states per subsequent layer,
at most eight digit edges per layer, and at most four terminal edges per
part. The bounds are conservative. For fixed r they are O(log(C+1)); for
C=0 interpret this as O(1+log(C+1)), since d=1. Arbitrary holed input sets
and arbitrary state-dependent functions need not have fixed r. Partial
digit masks are handled on this same graph without enumerating holes.

Let A have +1 at each edge tail and -1 at its head, e have source +1 and
sink -1. Set a_Y=2^h on a bit-one edge and 0 otherwise. For a donor entry
set a_M=b and on its bit edges a_M=-a_Y. For a receiver entry set a_M=-b
and on its bit edges a_M=a_Y. Singleton M costs are zero. Set a_V=1 on
donor/receiver entries, 0 elsewhere. Signed arc M costs sum to |b-y| on
each path. Entry and terminal edges have no bit index.

The only new implementation is

    Af=e, Aq=g*e, f>=0, alpha*f<=q<=beta*f, alpha<=g<=beta,
    Y=a_Y'f, M=a_M'f, V=a_V'f, Z=a_Y'q,
    delta_h=sum(bit-h-one edges) f_e, w_h=sum(bit-h-one edges) q_e.

Both flows conserve at every internal node. The code omits only the sink
equation in each flow: all incidence columns sum to zero, so the omitted
equation follows by summing the others. It adds valid f<=1 and q<=beta
bounds; acyclicity and unit total mass already imply them. No second q
allocation or independent product mechanism reconstructs Z.

Excluding unchanged physical columns, this block has 2a_G+2d columns,
d binary declarations, 2(n_G-1)+2a_G+4+2d rows. If t_G is the number of
terminal edges, j_Y counts nonzero Y-cost edges, j_M/j_V count nonzero
M/V costs, and K is vehicle count, its exact nonzero formula is

    6a_G+a_G*(1[alpha!=0]+1[beta!=0])-2t_G
      +4j_Y+j_M+j_V+3+3K+2d.

This includes source-g balance, interface links, all explicit code/w columns
and both perspective rows per edge; bounds are excluded. Degenerate old
state equations containing no state coefficient may remain as unchanged
physical equalities, in addition to the new block. Actual complete-matrix
counts are authoritative. R_abs adds 2N+2d columns and 2N+6+2d rows with
N=u-l+1, using B's short visit equation; C166 retains its existing
2k+2d columns and 2k+8+7d rows. All three use the same absolute d bits.
Coefficient magnitudes are at most C for the new graph costs, so integer
encoding length is O(log(C+1)). Including rational alpha/beta encoding of
length L, the total description length is O(r*d*(d+L)); O(r*d) refers to
nodes/edges/variables/rows/nonzeros, not unit-cost representation of large
coefficients. The implementation uses signed 64-bit costs and integer bit
width, avoiding floating logarithms and overflow at int capacity boundaries.

## 3. Enhanced projection theorem

**Theorem.** The graph formulation projects to E(D) in (X,delta,w), exactly
as R_abs, including alpha=beta. Its restriction to any partial assignment
of the declared absolute bits projects to E(D(F)); the physical projection
is H(D(F)). Empty D(F) is infeasible.

**Proof for alpha<beta.** Define the following two nonnegative flows only
for the proof; the implementation never divides by the interval width:

    f^alpha=(beta*f-q)/(beta-alpha),
    f^beta=(q-alpha*f)/(beta-alpha).

They conserve at internal nodes, with source masses
t_alpha=(beta-g)/(beta-alpha), t_beta=(g-alpha)/(beta-alpha), respectively.
These masses are nonnegative, sum to 1, and q=alpha*f^alpha+beta*f^beta,
f=f^alpha+f^beta. A nonnegative flow on a finite acyclic graph is a
nonnegative sum of complete source-sink paths: follow positive edges to
the sink, subtract the minimum edge flow, and repeat. Each subtraction
zeros an edge; no positive flow cycle or disconnected positive component
can remain. Decompose the two endpoint flows this way. The combined path
weights sum to one. The link equations become the corresponding convex
combination of legal (y,m(y),v(y),alpha,alpha*y,c(y),alpha*c(y)) and beta
points. Hence their projection lies in E(D).

For the reverse, a legal graph point uses f=1 and q=g on its unique path,
zero elsewhere. It satisfies both balances, all bounds and every link.
Convex combinations remain feasible because all the equations and bounds
are linear in the extended variables, including g. This constructs an
extension of every point in E(D).

**Fixed endpoint case.** If alpha=beta=a, edge bounds imply q=a*f,
and g=a follows from the source balances (or its own bound). Decompose
the unit f flow into paths. The links give exactly convex combinations
of the legal points at g=a. The same reverse construction applies. This
includes a=0 and has no singular endpoint calculation.

**Partial assignments.** Every complete path crosses every bit layer once,
so total f on all bit-h edges is one. If delta_h=0, nonnegativity forces
every bit-h-one edge to zero. If delta_h=1, total mass forces every zero
edge at that level to zero. Since 0<=q<=beta*f, q also vanishes there.
The endpoint path decompositions can therefore use only compatible paths.
Their stocks are exactly D(F) by path bijection. Conversely all such
paths satisfy the fixed bits. If D(F) is empty, no unit compatible flow
exists. All bits fixed, singleton domains, C=0 and empty conditions are
covered by this argument. Projection onto X gives the stated H hull.
Equivalently in R_abs a fixed 0/1 delta eliminates incompatible s_y by
nonnegativity and total mass, and then q_y=0; fixing delta or zeroing those
s/q is identical. Intersecting only with min/max of a holed set is weaker.

## 4. Integer correctness and the C166 comparison

When every delta is integer, all positive path mass spells the same d-bit
code, hence the same legal y. Path uniqueness makes f a unit path flow;
q=g*f follows along that path from source and internal conservation.
Consequently M=m(y),V=v(y),Z=g*y,w=g*c(y). Conversely every legal y,g
has the unit path extension above. Thus the integer stock/product/service
object is exact. R_abs has the same property with continuous s/q and
integer delta; retaining B's binary s would change the comparison object
and is expressly not done.

In the full physical model keep all original stock, route, assignment,
direction, quantity and load types, inventory balance, at-most-one service,
nonzero operation bounds and one-way service logic. These imply that the
sole active pickup or drop equals the integer b-Y; unassigned vehicles
have zero quantity. This is the inherited implicit-service-integrality
argument, not a new route hull. A physical fleet maps to its true g,
Y,M,V,Z,delta,w and unit f/q paths, preserving every outside row and the
original objective epigraph. Conversely a D167 integer physical solution
has exact local products and all old physical restrictions; assigning
old s_Y=1,q_Y=g gives a B extension with the same outside variables and
objective. The original true-G epigraph/coverage reasoning is still
needed to relate arbitrary model g to the physical objective. This
offline entry does not claim a verified complete-controller integration.

For any point in E(D), choose its full state mixture. Compress each
physical graph term to legal donor/singleton/receiver endpoints at the
same g, obtaining the C166 t/q block with the same X. Independently keep
delta and w from the original state mixture. Every legal state has exact
bit products satisfying C166's interval and global product inequalities;
convexity preserves them, as well as Y/Z bit reconstruction. Thus this
enhanced E point has a C166 extension. The argument keeps the prescribed
delta,w; it does not incorrectly recompute them from compressed supports.
Therefore after any identical bit fixing,

    proj_X(D167)=proj_X(R_abs)=H(D(F)) subseteq proj_X(C166|F),

and the witness in section 1 makes containment strict locally. With no
bit fixing, projecting out all digit coordinates gives H(D) for all three.

Embedding these statements in the full LP is valid when every outside
constraint uses the removed variables only through Y,M,V,g,Z and the
declared digit interface. Actual frozen B emits only state mass/Y/g/Z/M/V
reconstruction and state perspective rows. Its r=Y/target relation,
two-sided e epigraph, H and S, original objective, SCF/MTZ, service/time,
cutoff, ordered supply and effective pair support rows use retained
physical columns. `IntervalRowFactory.cpp`'s bit product rows are skipped
for the B VD-P source; D167 does not add them back as an independent
mechanism. C166 remains the unchanged writer version with those rows.
No state-penalty equality, linked direction, AP/count/CDF/theta/RN/VD-J
is enabled or accepted by the isolated new entry. Before/after common
row/domain/objective exports check these actual interface claims. The
global LP inclusion follows by intersecting with the same outside system;
strict local inclusion need not change the outside system's objective.

## 5. Sharp scope limits and attribution

This is local ideality with the specified digit interface, not full BRP
ideality and not conditioning on every Native branching row. For example,
in D=0..3,b=0,g=0, adding Y<=1 to the old hull admits half y=0 and half
y=2, giving Y=1,V=1/2. Rebuilding the integer domain 0..1 would require
V=1 at Y=1. Likewise merely adding g=1/2 to the old [0,1] hull of stocks
{0,1} permits the mixture (y,g)=(0,1),(1,0), giving Y=g=1/2,Z=0; rebuilding
at alpha=beta=1/2 forces Z=1/4. A new mathematical interval/domain needs
its actual bounds in the network; an offline canonical child is not a
captured Native node. The conditional bit guarantee retains the original
graph's legality, not arbitrary unencoded holes or new state functions.

Behle (2007), section 4.1, Theorem 4.1 provides the established path-flow
and level-equation projection result. Balas (2005), section 5, Theorem 5.1
provides disjunctive convexification; our endpoint-flow proof specializes
that tool. The fixed-width interval digit automaton, binary encoding and
endpoint mixing are standard. Huchette and Vielma's author manuscript
section 3.2 already separates root strength from effective branching.
Muldoon, Adams and Sherali (2013) treat ideal bounded base-2 and lexicographic
representations; only their publisher abstract/introduction was available
here, not a theorem-by-theorem full-text novelty check. Our narrow project
increment is the joint stock/movement/visit/product/code object, its exact
partial-bit relation, the concrete compact two-flow implementation and
the fixed real-frame diagnostic. It supplies no general OR breakthrough
or causal explanation of the historical C166 Native slowdown.

Primary versions and actual reading ranges are in `literature_memo.md`;
implementation checks and objective/size/cost results are separate from
this general proof in `qualification.json` and the complete positions table.

**Prototype preparation boundary.** The graph compiler itself works directly
from interval bounds and tightness flags in O(r*d), with no inventory
enumeration; the large-capacity solver-free checks exercise precisely that
compiler. The current standalone diagnostic driver first obtains the common
physical model from the unchanged B canonical writer, then removes its
one-hot block. That temporary carrier, file/import and deletion pipeline
retains O(|D|) state-dependent preparation/storage costs. The final D167
representation is logarithmic, but the entire writer pipeline and peak
memory have not been made logarithmic. No such end-to-end construction
claim or complete-controller integration is established by this prototype.
