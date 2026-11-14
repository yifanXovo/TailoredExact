# Exact compression of the shared inventory interface

## 1. Object and inherited representation

Fix a station, legal contiguous integer inventory domain D={l,...,u}, initial
inventory b, and 0<=alpha<=beta<=1 as in the actual Gini domain. Write m(y)=|b-y|,v(y)=1[y!=b], and

H=conv{(y,m(y),v(y),g,gy):y in D,g in [alpha,beta]}.

The common physical coordinates are (Y,M,V,G,Z), where M=sum_k(p_ki+d_ki)
and V=sum_k z_ki. These are expressions in the existing physical columns,
not new decision columns. Balance gives aggregate pickup=(M+b-Y)/2 and
aggregate drop=(M-b+Y)/2. The inherited VD-P block uses one selector s_y
and product q_y for each legal integer, sum s=1, sum y*s=Y, sum q=G,
sum y*q=Z, alpha*s<=q<=beta*s. B's two A/B equalities are
M=sum m(y)s_y and V+s_b=1 (with s_b absent if b is outside D).
After relaxing its binary selectors this is precisely H. No direction-state
equality or vehicle-state assignment is present in current m-binary B.

This is a *joint* projection. Independent correct product and service hulls
need not use the same inventory mixture. For example b=2,D={0,...,4},
Y=2,G=1/2,M=V=0,Z=2 belongs to their intersection: the service mixture
uses only y=2, while the product mixture uses half (0,0) and half (4,1).
In H, M=0 forces y=2 throughout and consequently Z=1. This explains the
already inherited B connection, without assigning it new priority here.

## 2. Breakpoint proposition and constructive proof

Let K={l,u} union ({b-1,b,b+1} intersect D), with duplicates removed.
Then |K|<=5 and H is unchanged if D is replaced by K in its definition.

Partition D into its nonempty donor piece D intersect (-infinity,b-1], the
singleton {b} if legal, and the receiver piece D intersect [b+1,infinity).
On each piece (y,m(y),v(y)) is affine. If legal y lies between legal endpoints
a<c of its piece, theta=(c-y)/(c-a) gives
(y,m(y),v(y),g,gy)=theta(a,m(a),v(a),g,ga)
 +(1-theta)(c,m(c),v(c),g,gc).
All piece endpoints belong to K. Singletons use weight one. This proves
that every old graph point has a new convex representation at the *same*
g. The reverse inclusion follows because every support endpoint is legal.
Applying these replacements to every term of an old convex combination
preserves all five common coordinates.

An explicit continuous extended representation is

sum_a t_a=1; Y=sum_a a*t_a; M=sum_a |b-a|*t_a;
V=sum_a 1[a!=b]*t_a; sum_a q_a=G; Z=sum_a a*q_a;
t_a>=0; alpha*t_a<=q_a<=beta*t_a.

For t_a>0 put g_a=q_a/t_a. These values are in [alpha,beta]; zero t forces
q=0. The equations are a convex combination of legal endpoint graph
points at g_a. Conversely collect convex weights and their weighted g
values to obtain t/q. Thus the displayed system projects exactly to H;
there is no SOS2/adjacency requirement on general hull mixtures.

If l<=b-2 and u>=b+2, all five supports are necessary among representations
that select generators from legal (Y,M,V) graph points. The V=1 face is the
quadrilateral with vertices (l,b-l),(b-1,1),(b+1,1),(u,u-b); its two side
segments have distinct slopes and all four endpoints are vertices. The
b point is the unique V=0 graph point. This limited necessity statement
does not bound arbitrary extended formulation complexity.

## 3. Why the separate exact product layer is essential

Continuous breakpoint weights plus integer Y do not enforce Z=GY. With
b=0,D={1,2,3},K={1,3},G=1/4,t_1=t_3=1/2,q_1=0,q_3=1/4, all breakpoint
constraints hold yet Y=2,Z=3/4, whereas GY=1/2. Making the t variables
binary instead removes the legitimate interior inventory Y=2.

C166 therefore also retains the existing absolute inventory layer:
Y=sum_h 2^h B_h, Z=sum_h 2^h W_h, B_h binary, W_h=G*B_h.
Its four exact interval inequalities are
W_h>=alpha*B_h, W_h<=beta*B_h,
W_h>=G-beta*(1-B_h), W_h<=G-alpha*(1-B_h).
The implementation keeps P's three additional global [0,1] product rows
as well as the four factory interval rows; redundant rows are not removed.
The bit count is d=max(1,ceil(log2(C+1))), inherited from absolute capacity.

Every old integer physical solution extends by its absolute bits, exact
products and same-g interpolation on the appropriate legal piece. It keeps
every original physical column, G and original objective. Conversely C166
has the unchanged integer inventories, binary route/visit/direction,
unique service, quantity limits and balance. Those physical constraints
imply nonzero one-way integer pickup/drop quantities: at most one vehicle
serves the station, its active direction leaves one quantity zero, and
their difference is the integer b-Y. The bit layer gives exact Z=GY.
Set old s_Y=1,q_Y=G to recover an old VD-P solution with identical common
columns. Hence the integer physical projection and original objective are
equal. Arbitrary model G need not equal the true physical Gini for this
representation equivalence; the inherited true-G embedding/coverage proof
establishes the complete method's correctness.

## 4. Raw LP projection and full-model embedding

The relaxed bit extension is convex and contains an extension of every
legal true (Y,G,GY) graph point. Its (Y,G,Z) projection consequently contains
the projection of H. The breakpoint and bit auxiliary variables are
disjoint and share only (Y,G,Z). Every point of H therefore has a bit
extension, and their intersection still projects to H in (Y,M,V,G,Z).
More explicitly, if a hull point has endpoint weights t_a and products
q_a, let B_h(a) be the h-th absolute bit of legal endpoint a. The relaxed
bit variables can be chosen as Bbar_h=sum_a B_h(a)t_a and
Wbar_h=sum_a B_h(a)q_a. Each summand comes from a legal endpoint graph
point with g_a=q_a/t_a; convexity gives all inherited interval and global
bit-product inequalities, including zero-weight terms. Binary expansion
gives sum_h 2^h Bbar_h=Y and sum_h 2^h Wbar_h=Z. This lift makes the
containment constructive; it does not require the bit map itself to be
affine in inventory.
This proves equality with B's *original* LP projection. It does not imply
ideality of the new combined extension, equal bounds after bit/selector
branching, or equal presolve/native-cut/search trajectories.

For a global LP, intersect the local extensions with any common system R
whose rows/objective use the deleted s/q only through the declared
interface. Equal projected local sets imply equal projection after this
intersection; choose the independent local auxiliary extensions station
by station. This embedding condition is essential.

Actual B source verification:

* VD-P emits mass/Y/G/Z/M/V reconstruction only. The ratio and absolute
  penalty reconstruction expressions are computed but emitted only in VD-J.
  B retains r=Y/target and the original two-sided e epigraph. Its target
  kink therefore is not part of the deleted-state interface.
* H, S, weighted e objective, Gini rows, interval/cutoff bounds, all physical
  service/resource rows, SCF/MTZ and pair-only valid rows use existing common
  or route columns. These remain unchanged.
* The factory generates bit product rows; old VD modes skip them, C166
  explicitly does not. Root/child/target/terminal canonical specs inherit
  the named representation policy and bind the actual matrix SHA/signature.
* AP, VD-J, linked direction, theta, threshold/CDF/count, RN and historical
  event/resource/decomposition extensions have other interfaces or unproved
  integration. They are off and unsupported combinations fail explicitly.
  No old proof source or opaque native state is reused across matrices.

The full LP conclusion precedes solver-generated cuts. It is neither the
full routing convex hull nor the original integer-objective epigraph hull;
the known positive-objective inventory/route gaps remain possible.

## 5. Degeneracy, generalization and exact failure boundary

The construction covers l=u, b inside/outside the domain, one-sided domains,
b=0/C, alpha=beta (including zero), and tightened intervals excluding b.
No singleton interpolation divides by zero. An empty legal domain remains
infeasible: the original propagated domain flag and its explicit
contradiction row are retained even when storage bounds reset to [0,C].

More generally, let a finite integer state be externally visible only
through y,gy and functions psi(y) affine on each common legal integer
piece. Keep the legal endpoints of every common piece. The same proof
preserves the joint continuous convex hull; continuous support depends on
piece count, not domain cardinality. Exact integer encoding still costs
O(log C). This is a concrete corollary of standard disjunctive reasoning.

Holes require extra care: for legal {1,3},b=0, relaxed support plus absolute
integer Y also admits Y=2 unless the hole is separately enforced. Never
fill illegal integers. Additional functions need their own common pieces:
with b=5,D=[0,10], the old K={0,4,5,6,10} fails to reconstruct an exact
state penalty |Y-2| at Y=2, since every retained penalty value is positive.
It needs the target breakpoint if such an equality is part of the interface.
These are actual applicability failures, not numerical tolerances.

## 6. Scale, attribution and actual cost question

Exclude unchanged physical columns/rows. Put N=u-l+1,k=|K|,d as above and
M_f=number of vehicles. B has 2N auxiliary columns, N binary selectors,
and 2N+6 rows. The implemented C166 has 2k+2d columns, d binaries, and
2k+8+7d rows, using P's inherited 3+4 product inequalities.

For exact nonzero counts, define A(S)=|{a in S:a!=0}|,
D(S)=|{a in S:a!=b}|, I_alpha=1[alpha!=0],I_beta=1[beta!=0].
B's state block has N*(5+I_alpha+I_beta)+2*A(D)+3+3*M_f nonzeros.
C166's emitted hull block has k*(4+I_alpha+I_beta)+2*A(K)+2*D(K)+3+3*M_f;
its separate bit block adds d*(15+2*I_alpha+2*I_beta)+2.
These symbolic counts assume nonzero coefficients exceed the inherited
writer omission threshold; actual native counts are the experiment's
authority. C166 uses V=sum v(a)t_a rather than B's V+s_b=1, accounting
for the different visit-row sparsity. Fewer columns/binaries need not
mean fewer rows or faster MIP. Build, root, nodes/Work and full paid costs
are measured rather than inferred from these formulas.

McCormick, Gupte et al. (2013, DOI10.1137/110836183), and Köppe et al.
(2008, DOI10.1016/j.disopt.2006.12.003) retain product/value-disjunction
attribution. Vielma's author manuscript Definition1, Proposition1 and
Corollary1 formalize ideal embeddings; Definition2 concerns a stronger
restricted formulation-complexity notion than our five-generator result.
Huchette-Vielma's author manuscript Section2, Definition1/Proposition1
uses simplex-face/embedding constructions for piecewise-linear graphs.
Its continuous PWL starting point does not directly remove the discrete
visit jump; the legal donor/singleton/receiver proof above supplies that
step. These tools are not claimed as new. The result established here is
the identified joint inventory/movement/visit/product object, its exact
small-support replacement, explicit interface boundary and complete-model
C++ integration, followed by the prescribed finite cost comparison.

Primary author versions read on2026-11-14:
[Vielma](https://juan-pablo-vielma.github.io/publications/Embedding-Formulations-and-Complexity.pdf),
[Huchette-Vielma](https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf).
Published identifiers verified against publisher records: Vielma,
Management Science64(10),4721-4734 (2018; online2017); Huchette-Vielma,
Operations Research71(5),1835-1856 (2023; online2022). The latter DOI's
2019 component denotes neither its online nor volume publication year.
Independent preformal review: review/math_preformal.md. Final native
qualification and actual cost evidence are separate from this proof.
