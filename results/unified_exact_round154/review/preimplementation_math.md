# Round154 preimplementation independent mathematics review

Reviewer: `/root/review_round154`, independent of the main residual and
production implementation. Date: 2026-11-05 (Asia/Shanghai).

Disposition: **ACCEPT_THE_MATHEMATICAL_DESIGN; IMPLEMENTATION_AND_EXPERIMENT_ADMISSION_PENDING**.
The C2--C4 identities, the stated product-block comparison and the scoped
proof-floor opportunity are sound under their stated assumptions. This
review does not qualify uninspected new source, a compiled executable, a
solver return or a full experimental panel.

This pass read the adopted goal, WORKSPACE_POLICY, the actual R153 pricing
and denominator interfaces, the existing own-root helper integration, the
R153 mathematical account, fixed-marginal exact-example account, final
review and endpoint/complete-pair evidence, and the finite historical
sources listed below. It ran no Optimize, Native model load, enumeration,
compilation, primal replay or performance experiment. Git/text/hash reads
are ordinary small metadata inspection. All review output stays under
ExactEBRP-work; old trees, raw evidence and user changes remain protected.

## 1. Exact residual and extension argument

For a legal inventory Y with S=sum c_i Y_i>0 and beta>=0,

    S[p(Y)-tau]
      = max{ S(beta gamma_L + D(Y)-tau),
             (beta/n) A_true(Y)+S(D(Y)-tau) }.

This follows by multiplying the positive denominator into
beta*max(gamma_L,A_true/(n*S))+D-tau. It needs neither continuous
fractional-programming convergence nor an exact solution of every
parameterized MIP. The nonnegative beta assumption matters: it is what
lets the max and the absolute-value epigraph have the stated orientation.

With binary one-hot x and positive l<=S<=u, the four product inequalities
force z_iy=0 at x_iy=0 and z_iy=S at x_iy=1. Therefore W=sum d_iy z_iy
equals S*D for arbitrary signed d. The station sum z=S follows at integer
x and strengthens the continuous model; it must not replace the four
individual inequalities. The two q lower rows admit q=R_tau(Y) with the
minimal a_ij=abs(c_iY_i-c_jY_j).

For an arbitrary feasible lifted integer point, a_ij>=the true absolute
difference, hence A_aux>=A_true. Since beta>=0, its q cannot lie below the
true residual for the selected inventory. Conversely, every true legal
positive inventory admits its minimal extension, which also satisfies
A_aux<=n gamma_U S. Thus the ideal model has exactly the intended integer
minimum. A nonminimal A can produce a larger residual objective; it is not
a true price value. The qualification needs an explicit nonminimal
completion case and must recompute original price from Y.

The q variable must be free below zero. A default nonnegative lower bound
would destroy equivalence whenever tau is above a feasible price. When
beta=0, the physical Gupper and hard-resource rows remain necessary:
projection directions are still over the same constrained inventory
domain. Omitting those rows would not test the specified oracle.

Positive c and nonnegative inventory give S=0 exactly at the all-zero stock
in these interfaces. A legal zero stock has price beta*gamma_L+sum d_i(0)
and stays outside the division/product positive branch. If positive
inventory is impossible, the zero-only handling needs no fabricated
positive bound. An infeasible/unknown Native status is not by itself a
qualified proof of positive-branch emptiness under the inherited policy.

## 2. Product block and its precise comparison

For each station, z-lx>=0 and ux-z>=0 have sums S-l and u-S, respectively.
Let a_i=min d_i(y) and b_i=max d_i(y). Multiplying each nonnegative mass by
its cost gives

    a_i(S-l) <= sum_y d_iy(z_iy-lx_iy) <= b_i(S-l),
    a_i(u-S) <= sum_y d_iy(ux_iy-z_iy) <= b_i(u-S).

Summing stations yields the four aggregate McCormick inequalities stated
in C3 for the Cartesian cost interval [sum a_i,sum b_i]. This proof never
requires positive costs.

The strictness witness is correct: Y1=2,Y2=1 gives S=3,D=1.
The rectangle [2,4]x[0,2] permits W=2, whereas the binary one-hot lift
forces W=3. This is strictness of the product representation relative to
that rectangle, not a complete-Q dominance theorem.

The hard-total counterexample is also correct. With l=1,u=2,
x_i1=x_i0=1/2,S=3/2,z_i1=1/2,z_i0=1 at each of two stations,
all four product inequalities and station mass equalities hold.
D=1 but W=1, although the true hard-total domain fixes D=1 and a tightened
aggregate product requires W=S=3/2. The exact total-product row requires
sum y*z=S here and excludes the point. Therefore the lift alone does not
imply aggregate McCormick rows using arbitrary tighter DP-derived cost
bounds. The implementation may retain such rows or total-product rows
when useful, while preserving this limitation in the paper.

The two total-product inequalities are valid because at integer x,
sum y*z=S*sum Y and S>0. This is a targeted strengthening of an observed
relaxation defect; it does not remove a legal inventory.

## 3. Interrupted bounds, signed conversion and parameter transport

Let ell be a qualified residual lower after all residual-unit losses.
For every positive stock, R_tau(Y)>=ell.

- If ell>=0, ell/S>=ell/u, so m_+>=tau+ell/u.
- If ell<0, ell/S>=ell/l, so m_+>=tau+ell/l.

The sign test must use the already qualified ell. Using u for a negative
ell would give an unsafe stronger price bound; using l for a positive ell
would likewise be unsafe. The safe binary64 bounds need l no greater
than the true positive minimum and u no less than the true maximum.
This is consistent with the R152 s_bounds contract read in this review.

If zero is legal, take the minimum with its exact price before comparing
against a full-domain DP lower or a previously qualified same-direction
lower. A positive-branch bound alone cannot be maximized with a whole-domain
bound and declared whole-domain without this minimum. Existing information
is retained by maximum; unsupported or missing calls contribute no new
bound. An exact DP attaining stock can settle the price only if it is
legal in the full Gupper/resource domain.

For identical R,beta,d and delta=tau'-tau,

    R_tau'(Y)=R_tau(Y)-delta*S(Y)
              >=ell_tau-max(delta*l,delta*u).

The max expression handles either sign of delta. Parameter transport is a
separate preserved certificate; another call's raw lower need not exceed
it. Transport must bind actual coefficients and the same support/resources/
Gini range, rather than only a human-readable role or target label.

Station anchoring d_i=a_i+tilde_d_i is exact when its accumulated term
(sum a_i-tau)*S is retained. It reduces cost cancellation but does not
license dropping signed small terms or carrying an RN price guard into
residual units. For a rounded model, the lower-bound proof needs a valid
extension for every legal true inventory and a paid upper bound on any
adverse difference between the written residual objective and true
R_tau(Y), plus the declared Native numerical allowance. Merely rounding
q objective coefficient 1 is insufficient: signed epigraph coefficients,
S/A representation, Gupper and product bounds all affect this extension.

A straightforward way to avoid an extra c_i*y rounding interpretation is
to retain explicit Y_i=sum integer-y*x_iy and use declared binary64 c_i
as the coefficient of Y_i. Any alternative is acceptable if its actual
coefficient errors are transported in the safe direction. The new
qualification must inspect the written coefficients/rows and prove its
chosen correction, with the guard restored in residual units before the
sign-dependent division. This is a finite new-interface task, not a
request to reopen all R134 numerical qualification.

## 4. Fixed-certificate targets and nonclaims

A same-direction price lower gives

    L_direction=C_Q+min(a_K,L_price).

To prove zeta by that certificate, tau=zeta-C_Q is necessary and
zeta<=C_Q+a_K must hold. Any true legal stock supplies price upper U_price,
so the direction's maximum possible contribution is bounded above by
C_Q+min(a_K,U_price). If that number is below zeta, more optimization of
that exact direction cannot prove the target. A stock below tau refutes
the fixed target and provides a column; it does not refute the full hull
or exclude a useful combination of supports.

The finite R153 evidence already motivates different choices:

| Domain/direction | Saved conclusion relevant to Round154 |
| --- | --- |
| K35 near_optimal_zero_pool/iter00010 | Expanded-pool true-price upper equals a_K in the saved exact screen; fixed ceiling about .2873260533 lies within 1.1e-7 of retained RMP upper. R153's later same-direction price lower .0700384222 still leaves substantial proving work. |
| NC20 level_zero_continued/iter00008 | Fixed ceiling about .1833229562, only 1.11e-6 above retained hull lower .1833218485; extending it cannot resolve the current .00663 hull interval. |
| NC20 old near_optimal_zero_pool/iter00016 | Enlarged pool already contradicts its column constraints; its ceiling is about .18544776. A fresh direction must be checked against all current columns. |
| NC20 post_primal_level last direction | Individual ceiling about .1862095006 permits some improvement, but cannot alone reach the retained full RMP upper .1899568006. |

These values are inherited evidence, not new Round154 measurements.
The selected task table must freeze actual Q/scope/beta/d/C_Q/a_K, current
pool screening, tau, initial true-stock information and costs before new
matched prices. Different directions cannot be spliced into a monotone
same-price convergence trace. A full RMP primal upper remains distinct
from a finite-support relaxation upper and a physical routing incumbent.

## 5. Independent proof-floor placement

The old helper prices beta=1,d=h on the current canonical stock domain.
Any physical solution of that domain has formal G>=max(gamma_L,G_true)
and penalty epigraph at least H, so a qualified inventory minimum lower
is a valid lower on the formal total objective. This mathematical fact
does not require writing the floor into Native.

A first-artifact floor is only local until its coverage is established.
The current ensureArtifact calls the R153 hook on the first built leaf;
the fact c.generated is true does not itself establish root coverage.
A valid E implementation must bind that source to the complete intended
root L0 interval, or restrict its consumption to explicitly covered
leaves. Current round127Md requires one complete initial root and supplies
a useful existing coverage check, but the E path must actually require
and record the relevant condition, not assume the method name implies it.

For a source valid only within F<=U0, the complementary region satisfies
F>=U0. Therefore min(U0,ell) is a whole-domain lower once the root Gini
coverage and outside-root strict-improver exclusion are accounted for.
A descendant may inherit only with the same data/ratio/objective/resource
identity, contained station supports, narrowed Gini interval and compatible
cutoff; the R153 checks are reusable. If coverage is partial, combine by

    min over frontier leaves j of max(L_native,j,ell_covered,j),

leaving uncovered leaves at their original lower and retaining the old
closed-region/coverage policy. A local constant must not be applied as an
unconditional global max.

Proof consumption must remain separate from search scoring: no Native
floor row, unchanged native/LP parent and child lower inputs for AM and
priority, and a separate scoped source used for admissible pruning,
global termination and reported supported L. The production review must
trace those actual uses, including any routine whose name says
globalLowerBound but whose value also enters AM normalization. Replacing
all parent/child bounds by max(bound,ell) before AM would defeat the stated
single-factor placement experiment even though those bounds are valid.

Source rejection must retain the stable B information; no unsupported
helper response, stale cutoff or mismatched source can upgrade the proof.
The new algorithm still pays its own H and helper construction/validation,
and valid proof pruning or the paid wall-time loss can change search
trajectories. Equal semantic own-H output is not shared/free H; B and E
need not have identical wall-clock search paths.

Saved R153 complete pairs show only NB35's own floor .3959564087 exceeds
its B terminal L .3893106016. K35 and RB35's floor values are below their B
terminal lowers, while NC20's is essentially zero. This supports keeping
all four predeclared roles as cost/search controls without promising
terminal-L gains in every role. The NB35 opportunity max(old B_L,old floor)
is not an E result or a free new algorithm gap.

## 6. Finite historical exclusion and attribution

| Source actually inspected | Established prior scope; Round154 distinction |
| --- | --- |
| PR58 fixed ff381ac9da9b56be730dc4768455e861187e5c13, alternative_formulation_rejection_notes.csv / equivalence_test.csv and script excerpts | Exact-S enumeration/selector/parametric cutoff passed a V4 direct-algebra toy with 63 denominator values. Larger route exact-S paths stopped on incomplete/too-large coverage. Dinkelbach iterations were rejected because finite exact termination certificates were unimplemented. This is not measured failure of the new state-product residual oracle. |
| Current IntervalRowFactory.cpp, objective_lower_estimator_cutoff and sp_product_objective_estimator_paper_safe; CplexBaseline.cpp existing SP block declarations | Denominator multiplication, SP products and McCormick incumbent estimators predate this round. The new experimental object is arbitrary signed state-price residual minimization with interrupted whole-domain lower certificates and useful hull targets. |
| R133 joint_objective_gap_note.md | Prior integer/joint structure and balancing distinctions are retained. The old note has explicit service-coordinate and loaded-matrix scope; it is not overwritten by the new product-block comparison. |
| R153 mathematical_analysis.md and review/exact_strict_example.md | Theta=H+Gamma; the 169-row/68-bound fixed-marginal inventory example has reference optimum 59/288, Theta=1049/4320 and gap 41/1080. This is not a complete routing strict example; the old global-floor gap does not transfer. |
| R104 mathematical_algorithm.md at aa1d0e5b268cf95442b3713b2af8fc505974f6c2, relevant SHADOW/ACTIVE excerpt; R144 inherited account | SHADOW submitted no new rows or bounds, and no auxiliary LP bound was used as formal global LB/cutoff. ACTIVE's full-method regression and auxiliary cost remain prior adverse evidence. E actively consumes a qualified external proof lower, a different placement experiment. |
| R139 placement guide; R144 and R145 guides/math | R139 changes LP versus MIP information and therefore search/AM. R144/145 project rows into formal Native matrices. Their finite regressions and costs remain; they do not already test proof-ledger-only consumption with an unchanged formal matrix. |
| R153 final review, K35/NC20 endpoint reviews and paid post-primal two-step review | The accepted study includes long same-direction prices, denominator partition, CDF, integer flow, changed potentials, large legal pools, support replay and final refresh. It is not a few short trials and is not reopened as a default variant grid. |

Standard parameter residuals retain their Dinkelbach attribution, and the
Cartesian product comparison is ordinary McCormick/RLT reasoning. No new
generic theorem, normalized-RN LP dominance, unconditional speedup or
complete-method gain follows from the mathematics alone.

## 7. Finite next gate

Before expensive residual prices, independently review the actual written
model/coefficient transport, bounded small-domain enumeration result,
signed/zero/beta0/negative-q/nonminimal-A checks, both conversion signs,
cross-tau retained certificate, and selected target table.

Before full B/E/J runs, independently review the exact E compiled path,
source rejection/coverage checks, same-domain Native matrix identity with B,
actual AM/priority inputs, legal stopping, matched PE/helper/source chain
and frozen nine-position panel. The prescribed windows sum to 19200 s:
NB35 B/E/J at 2400 each; K35 and RB35 B/E at 2400; NC20 B/E at 1200.
Each arm has independent own H and source. This review does not admit those
runs yet.

Final review will assess saved new data, costs and failures, scope/version
bindings, actual claims and required final free-Q support replay/RMP refresh.
Successful mathematical qualification is compatible with a negative finite
performance conclusion, while a promising mechanism needs the substantial
targeted deepening requested by the goal.

## Read-evidence identities

- Adopted task source SHA256:
  6d42d706fc675a32c8ad1e3157f7e192925b3fac82de0532599b7909a61ab990.
- WORKSPACE_POLICY SHA256:
  3812091c415a87116472e56f7f9c598c36ee485a654383d15e8b03fca69c042d.
- R153 mathematical_analysis.md SHA256:
  de25e9ffab2f15fcadd7aa94b6c693a9f6ae41522e92b310e9fa6a4aa164fac7.
- R153 review/exact_strict_example.md SHA256:
  60424934ccc64d86f158c06c2777c0c3a3d6ef9f23f4d0ee1f3ff67ef500e8c9.
- R153 reports/complete_pairs.json SHA256:
  b20932570f4256587d181acd275a169e7e2e0ac5c0ea5950bcad172aa684e5d2.

No new implementation source hash is listed as admitted by this
preimplementation review.

