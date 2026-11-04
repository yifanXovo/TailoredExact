# Independent implementation review: reference oracle and LP controls

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).
Read-only code review; no additional Optimize, enumeration, DP or compilation.
Reviewed `round152_math.py`, `round152_oracle.py`, `round152_qualify.py`,
`round152_lp.py`, `round152_projection.py`, `round152_prepare.py`, and their
relevant inherited arithmetic/LP helpers. Read the saved qualification result.

**Initial disposition: conditional admission.** The mathematical model and
signs are sound on the intended input domain. Before expensive pricing,
address the three bounded qualification items below. These are localized
oracle admission checks, not reasons to repeat valid AP LPs or rebuild the
production executable. The main implementer was notified immediately.

## 1. Findings requiring a targeted change before long pricing

1. `solve_bin` accepts every finite `ObjBound` except when status is
   INFEASIBLE or INF_OR_UNBD. This includes NUMERIC and other unqualified
   solver outcomes. A finite number plus a numerical guard does not itself
   qualify a bound after a numerical failure. Use an explicit accepted
   status policy for ordinary completed/limited solves, record its outcome,
   and use only the hard-total DP fallback for rejected statuses. Keep
   proven-empty qualification separate. The same policy should be observable
   in the saved result, so the complete-cover aggregator cannot mistake a
   rejected return for a new proof. No such failed result has been observed
   in the small-domain results read here; this is a concrete reachable code
   path, not a withdrawal of the existing successful observations.

2. The oracle's MPS readback checks variables but not its constraints.
   Validity depends on the actual ratio rows, inventory and one-hot links,
   hard resource and bin bounds, and the outward surrogate/Gini-cap rows.
   Reuse the existing complete `semantics` comparison before and after MPS
   import, including row coefficients, RHS, sense, objective constant and
   objective sense. The LP-appending helper already does this for retained
   rows and separately reads back every new row. The reference oracle needs
   the same bounded readback, not a new transport framework.

3. `qualification/result.json` verifies individual `solve_bin` returns
   against exact enumeration, but the qualification code never calls
   `price`. Therefore its actual zero-component aggregation, unresolved-bin
   fallback retention, and refinement-parent lower-bound inheritance have
   not been exercised. Add one small deterministic aggregation fixture;
   mocked `solve_bin` outputs can cover these logic paths without additional
   Native calls. Assert that the final global lower bound is the minimum
   over every active component, including unvisited and rejected-return
   components and the separate zero state. A no-call/call-limit case is
   useful here and sufficient; a large new engineering matrix is not needed.

## 2. Mathematical and implementation checks that pass

- `h_exact` uses exact rational interpretations of actual binary64 c and
  already weighted omega. `evaluate` computes true A, S, G and phi and checks
  support membership, hard integer total bounds and G<=gamma_U. It does not
  impose the invalid physical G>=gamma_L condition.
- `fallback` minimizes the exact unary cost h-pi over HARD integer totals
  and adds gamma_L. It may ignore G/bin restrictions as a relaxation. A
  negative result is retained. Its inventory supplies a pricing upper only
  after the full true-domain check.
- Positive S coverage starts below the minimum possible positive supported
  ratio and a safe continuous resource lower bound, and ends at a safe
  resource-box upper bound. Adjacent bins share their actual binary64
  endpoint. The all-zero state is separately evaluated with gamma_L included.
- The bin MILP has the correct one-hot integrality, total inventory, ratio
  and absolute-difference semantics. Rounding n*u and n*gamma_U upward
  relaxes their respective inequalities because q and S are nonnegative.
  Downward unary-objective coefficients and the exact readback compensation
  do not overstate a lower bound. The reported denominator epsilon is the
  ideal-bin approximation error, separate from objective/numerical guards
  and the Native MIP gap.
- Inventory incumbents are rounded to integer Y and reevaluated using exact
  true-domain arithmetic. A candidate need not belong to the same numerical
  bin to be a valid GLOBAL pricing upper; it must belong to the full oracle
  domain, which is checked. No such incumbent is advertised as a physical
  routing upper bound.
- The aggregator retains a DP lower for every unprocessed bin. Its lower
  update takes max(previous,new), and splitting copies the parent lower to
  both children. That is valid for their true objective even when their
  smaller denominator surrogate differs. Only qualified empty bins may be
  removed. The structural logic is correct by inspection; item 3 requests
  actual path coverage, not a redesign.
- AP's omitted tiny nonnegative RHS contributions only weaken its row.
  GD's conditional denominators have the right monotonic directions. The
  four stock product rows have the correct gamma_L/gamma_U and Bminus/B
  pairings. TC/TC2 coefficients are rounded downward, including signed
  coefficients; deleting tiny negative RHS terms receives the necessary
  per-station intercept compensation. Both old TC and TC2 are retained.
- The complete LP insertion routine preserves every old row, variable bound,
  type, objective and constant; the model remains continuous and all its
  old auxiliaries remain free. The reported AP values are saved numerical
  optima under the inherited policy, not rational certificates.

## 3. Scope and interpretation notes

The inherited `scope_from_model` checks one-hot selectors, the ratio and
epigraph rows, G bounds, resource rows and actual objective units. It does
not explicitly assert each Y=sum_y y*s_iy link, although these links are
present in the known retained exporter. A direct link assertion is a small
useful scope-contract improvement when using this parser as the authority
for a new epigraph oracle. It does not require new optimization.

`round152_projection.py` is an exact hard-total network formulation with a
numerical LP and a recovered numerical mixture. Its source marginals are
clipped/truncated and normalized; the maximum adjustment is recorded, and
the mixture reconstruction is checked. Thus a successful result is a
numerically qualified nearby joint-distribution witness, not a rational
identity with arbitrary raw floating marginal entries. Any claim that a
new row's significant gap is objective information should include this
adjustment/reconstruction uncertainty (weighted by that row's potentials
if material), and should require every recovered column to satisfy the
true Gini-domain condition. The `full_oracle_projection_feasible` flag
correctly adds this condition; `resource_projection_feasible` alone does not.

The direction-nonseparating stop currently permits `upper <= threshold +
1e-9`. This is a numerical equality convention, not a strict exact proof
when the small difference is positive. Report such equality using the
declared numerical policy, or use a conservative nonseparation margin.
There is no reason to chase sub-tolerance differences with extra solves.

The projection result's `seconds` field is taken before path decomposition.
The outer metered process still charges the whole computation correctly;
do not label that early field as the complete projection/verification cost.
Updating it after decomposition would make the diagnostic field clearer.

## 4. Qualification observations and limits

The four purposeful cases contain 81, 12, 9 and 1 enumerated inventory
vectors. They exercise signed potentials, negative pricing lower bounds,
zero inventory, nonminimal completion, heterogeneous coefficients, empty
positive bins, positive coverage, individual MIP lower directions and
true upper witnesses. Exact changed-potential transport and the explicit
child-to-parent counterexample are appropriate. The loaded numerical bounds
are deliberately not called rational optimality certificates.

These cases do not yet establish strictness beyond AP/GD/count, efficiency
on real domains, or complete algorithm gain. They should remain semantic
qualification evidence. The proposed real strong-reference sequence is
appropriate; do not infer a production candidate from qualification alone.

## 5. Fee and edit boundary

This review used only text reads and manual reasoning. New experimental
computation, Optimize/DP/enumeration/compiler calls: zero. Only this review
file was written by the reviewer. The main implementation and all raw
qualification results were left unchanged.

## 6. Follow-up readback of the localized repair

The reviewer read the revised oracle after the implementer's notification.
It now compares complete pre/post-import semantics, restores a proposed
Start onto the actually optimized imported model, and accepts finite lower
bounds only for OPTIMAL or TIME_LIMIT. Other statuses retain no new lower;
the aggregator keeps its previous/DP lower. Results explicitly record this
qualification policy. Findings 1 and 2 are closed by static inspection.
Finding 3 is subsequently closed by reading `qualification_aggregate_v2/result.json`
and `round152_oracle_checks.py`. No-call, partial cover, refinement, positive
coverage and zero-component containment pass. One actual tiny Native call
also exercises the repaired complete-matrix readback and status policy.
The initial equality assertion's replacement by exact lower/upper
containment changes the fixture, not the oracle algorithm. The earlier
failed fixture remains evidence. The staged offline oracle admission is
now **ACCEPTED** within the stated numerical policy.

## 7. Review of active-state pricing with complementary DP lifting

The proposed focused revision is mathematically admissible. Let A_i be a
nonempty active subset of the original support. Partition the full oracle
domain into R_A (all selected states active) and R_notA (at least one
selected state inactive). For any finite full-support potential pi,

    alpha_full(pi) = min(alpha_A(pi), alpha_notA(pi)).

Use a qualified active-domain bin lower L_A, and solve the unary hard-total
DP with an additional Boolean state recording whether an inactive choice
has occurred. The DP objective is the same exact h-pi and its final Boolean
must be true. It relaxes G/bin restrictions, so gamma_L plus its optimum is
a valid L_notA. Therefore min(L_A,L_notA) is a full-domain lower and gives
a valid support on the original parent. If the complement is proved empty
by the exact total DP, its contribution is +infinity. If the active domain
is empty, it needs its own valid emptiness conclusion; neither side may
silently disappear because a solver failed.

With pi=h+psi and inactive psi=-M, decreasing inactive psi leaves the
active pricing problem unchanged and makes every complementary inventory's
price nondecreasing. The candidate M=1+n*radius is not an automatic proof
that the complement is dominated. The actual complementary DP lower must
reach the desired intercept; otherwise the minimum still limits the row.
This gives a deterministic mathematical lifting/stop criterion and avoids
the forbidden unqualified child-to-parent transport.

If s is an exact nonnegative one-hot marginal vector and every excluded
state has exactly zero marginal mass, every joint distribution realizing s
uses only active states. Its exact epigraph value therefore equals the
active-domain value. A dual row from that face still needs the complement
argument before use in the unrestricted LP. For a numerical source point,
small positive and negative entries may be truncated only in discovery;
do not claim exact face equality for those raw entries. Record the original
mass removed, any negative mass, the normalization change, and the weighted
potential activity uncertainty. In particular a negative selector times a
large negative lifted potential can create spurious apparent separation.
Evaluate the final row against all original selector coordinates and retain
its transport/margin qualification. Reoptimizing the complete LP with every
original state variable free supplies the independent actual-strength test.

This revision may reduce oracle complexity without changing the research
object. It is not R105-style route decomposition: both branches are only
pricing relaxations for a row in the existing original full model, and no
inventory candidate is promoted to a physical routing incumbent.
