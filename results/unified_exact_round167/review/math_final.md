# Independent mathematical and model review

Reviewer: `/root/math_review`, an actual independent child agent. Date:
2026-11-15 (Asia/Shanghai). This is a read-only review of the scientific
objects, implementation, emitted matrices and the current concise paper
versions. No Optimize, production run, model mutation or implementation edit
was performed by this reviewer. The independent checker is an offline row
reader, not an optimization core or replacement modeling driver.

## Decision and one requested correction

The conditional counterexample, enhanced projection theorem, arbitrary
partial-bit statement, integer exactness and scoped full-model containment
are correct. The actual two-flow representation implements their object.
There is no mathematical obstacle to retaining D167 as an offline research
prototype. This does not establish a full BRP hull, complete-controller
integration, Native search cause or complete algorithm acceleration.

One P3 mathematical wording correction was requested at Appendix A.11,
the paragraph beginning "The complete-model conclusion requires":
"coefficients have O(d) bits" must refer to **integer path costs**, not
arbitrary-precision Gini endpoints. With rational endpoint encoding length
L the description bound is O(r*d*(d+L)), as already correctly stated in
the full research note. The correction affects the complexity description,
not a model, diagnostic position, objective or Optimize. Final disposition
and the exact corrected-section hash are recorded in `math_final.json`.
The corrected integer-cost/endpoint-precision sentence has now been read
back in the actual appendix, and the final body and appendix explicitly
define D(F) before their conditional claims. Final decision: **PASS, no
unresolved mathematical/model findings**.

## Independent mathematical derivation

For alpha<beta the transformation
f_alpha=(beta*f-q)/(beta-alpha),
f_beta=(q-alpha*f)/(beta-alpha) is an invertible linear transformation
between the implemented f/q variables and two nonnegative conserved flows.
Their nonnegative source masses sum to one. Acyclic path decomposition
therefore supplies convex combinations of legal stock/code points at alpha
and beta; the same edge costs reconstruct Y, M, V, Z, delta and w. Conversely
the unique stock path with f=1,q=g extends every graph point and convexity
extends its hull. This proves E(D), not merely a product projection. When
alpha=beta=a the edge bounds give q=a*f, avoiding every division by zero.

Every successful path contains exactly one edge of every bit level. Fixing
a zero digit kills all one-edges by nonnegative unit mass; fixing a one
digit kills all zero-edges. The q bounds kill the same edges in the weighted
flow. Thus every endpoint decomposition uses precisely compatible paths.
No incompatible path can be restored by recombining service pieces because
their internal nodes remain disjoint. Empty D(F), complete invalid codes,
singleton/zero-capacity domains and complete bit fixing follow from the
same argument. With integer delta the injective code selects one stock and
one path; conservation then makes q=g*f on that path. The inherited unique
one-way service and integer inventory balance premises give the original
physical quantities. No assertion of full routing ideality is needed.

For each conditional physical graph point, interpolate at the same g
between the legal extremes of its donor or receiver part, retaining b
when legal. This proves the at-most-five-support H(D(F)) statement even
with holes. It does not prove a five-state E(D(F)) representation: a
particular 0/1 code is an extreme point of the code cube, so it cannot be
obtained from different legal codes merely because Y can be interpolated.
The DAG retains exactly the information that this physical interpolation
can discard.

To extend an E(D) point to C166, compress only its physical state mixture
to the legal affine-piece endpoints, at each term's own g. Keep delta/w
from the **original** mixture for the separate bit layer. Convexity of its
global and interval product inequalities and linear reconstruction prove
enhanced containment while preserving those digit coordinates. Identical
partial fixing consequently preserves the physical inclusion. Projecting
all digits away before fixing gives the shared H(D) projection. This does
not imply equal behavior after arbitrary stock inequalities or narrower
g restrictions; the explicit counterexamples to such claims in section 5
of the note are valid.

## Actual-code and serialized-row checks

I read `Round167ConditionalState.hpp`, `round167_research.cpp`, the relevant
state/absolute-bit branches in `CplexBaseline.cpp`, interval row handling,
the original shared-state proof and current research controls. Tightness
states are independent of a chosen stock; graph construction never
enumerates stocks. Bounds are 2+r*(1+4d) nodes and r*(8d+5) edges. All
bits are read, including C=0's declared bit. The INT_MAX singleton guard
prevents b+1 overflow. Source and sink are genuinely distinct and an empty
graph cannot carry unit mass. Sink conservation is the only omitted row in
each flow, and is implied separately by incidence-column sums.

R_abs changes the source state's binary selectors to continuous variables
and adds absolute delta/w links; integer delta supplies the new integer
state selection. D167 deletes the source state/product columns and their
rows, then emits the same-edge f/q system. There is no old independent
product layer in D167. The Start mapping uses unit path f and g-weighted q,
so narrow or fixed Gini widths cause no endpoint-weight amplification.
The driver actually relaxes every integer type in a pure LP and restores
the exact original type vector. The S=0 test fixes physical Y in a tiny
MIP; it is not misrepresented as a rebuilt conditional LP hull.

The isolated CLI has no AP/count/RN/CDF/theta/linked-direction/VD-J option
and rejects unknown/extra arguments. Its source B mode retains only the
declared state mass/Y/M/V/g/Z dependency. Existing e, H/S, objective,
SCF/MTZ, route, time, cutoff and active valid rows use retained physical
columns. The `common()` exports are useful physical-row readbacks, although
their filtering is not a proof for future feature combinations: the source
interface analysis is still required. No unsupported extension is silently
accepted in the fixed entry. The unchanged-B export receipt and empty
diffs of the four production source files agree with the frozen scope.

`math_checks.py` independently recovers each emitted network from the actual
mass-balance rows, reconstructs the weighted incidence, and follows those
arcs. It does not call or transliterate the constructor. The completed
check passes **623 station networks and 10851 complete paths** across all
D167 canonical/local/tiny positions. For each path it verifies legality,
uniqueness, every digit position, Y/M/V costs, Z's use of the same q costs,
delta/w edge incidence, edge envelopes, sink omission, and the exact
auxiliary row/nonzero formula. It also substitutes the prescribed exact
rational witness into **all 40 emitted L1 C166 rows**. All pass; M=V=0
contradicts the legitimate conditional stock set {1,3}, where both are one.

The exact nonzero formula is independently confirmed, including the source
G coefficient, both flows and omitted sink incidences. When embedding M/V
as sums of K vehicle columns, the formula explicitly includes 3K; the
logarithmic assertion describes the local fixed-dimensional interface as a
function of capacity. It does not bound global routing size by log C. The
integer-cost coefficient encoding and endpoint-precision qualification
above are necessary to distinguish nonzero count from bit complexity.

## Diagnostic and paper interpretation

The frozen 88 positions retain 72 canonical raw LPs, 12 local LPs and four
tiny MIPs. The recorded outcomes match the theorem's directions: R_abs and
D167 agree within 2.22e-16 over all 24 frame/scope triples; all eight F0
triples agree with C166; three of sixteen conditioned triples have strict
original-objective increases above 1e-7. The others are numerical matches,
not discarded failures. These are deterministic offline scopes, not
observations of visited Native nodes, and their conditional lowers do not
become full-domain global bounds. Local LP equality to the enumerated
reference is supporting implementation evidence; the independent general
proof and physical oracle remain distinct premises.

I additionally read the current body section 2.4, Appendix A.11, the new
mathematical companion passage, diagnostic interpretation and conclusions.
They accurately limit the conditional claim, retain alpha=beta and the
full-model interface, distinguish old LOG's y-l code from absolute y, and
do not ascribe C166's historical slowdown to an observed bit branch. The
appendix's full proof agrees with the research note, subject to the single
encoding-length wording correction above. The actual larger D167 matrices
and modest conditional increments support keeping this result at the
representation/diagnostic level; logarithmic asymptotics alone do not
establish a reason to launch full comparisons.

## Primary-source attribution actually checked

I independently opened the 98-page [Behle thesis](https://people.mpi-inf.mpg.de/alumni/d1/2019/behle/publications/behle_thesis.pdf)
and read section 4.1, including the flow constraints, level equations and
Theorem 4.1 proof on PDF pages 38-41. It supplies the established path-flow
projection tool. The joint stock/service/g-weighted application is the
project-specific part; generic network ideality is not new here.

I read section 5 and Theorem 5.1 of the 37-page
[Balas survey](https://www3.diism.unisi.it/~agnetis/projlift.pdf), PDF pages
17-18. Its scaled-polyhedron convexification covers the standard endpoint
disjunction used in the proof. The stock/code network proof supplies the
specific application and boundedness here avoids closure concerns.

I read the embedding/branching discussion, especially section 3.2 of the
45-page [Huchette-Vielma author manuscript](https://optimization-online.org/wp-content/uploads/2017/07/6148.pdf),
PDF pages 7-10. It explicitly studies branch-conditioned relaxation
strength and hereditary sharpness. Equal root strength and distinct useful
branching behavior therefore cannot be claimed as a new general insight.

For [Muldoon-Adams-Sherali](https://www.sciencedirect.com/science/article/abs/pii/S0167637712001290),
the direct page fetch was denied but the primary publisher search extraction
exposed its abstract, introduction and section snippets. I read those
accessible portions, confirming bounded base-2/lexicographic hull context.
I did not obtain or review the full article's theorems. Neither this review
nor the paper should claim full-text theorem-by-theorem novelty exclusion.

## Work accounting and remaining limits

No reviewer Optimize was performed. An inefficient first offline-reader
attempt repeatedly parsed a whole LP for each station; I terminated only
my identified `math_checks.py` process after about 150s (02:08:27 to
02:10:57 Asia/Shanghai), conservatively charged as 151s. A one-file parse
cache retained the same checks and the successful run took 13.1823629s.
This is a reader repair, not a producer failure or a repeated solve.
The JSON retains both the exact successful compute timer and the separate
conservative first-attempt allowance for the parent's aggregate fee.

General proofs are exact mathematics; the numerical LPs retain their
floating qualification policy. Local ideality applies to the declared
absolute bits, not every Native branch or changed interval. Arbitrary
holes/functions need another proved graph. The prototype is default off
and offline; existing B and C166 performance records and B's recommendation
are unchanged. These are disclosed scope limits, not unresolved theorem
or implementation defects.
