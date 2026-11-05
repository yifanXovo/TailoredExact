# Target integer pricing and proof placement

This uses the complete R153 free routing relaxation Q and its entire
hard-resource inventory domain R. The declared c_i and potentials are the
actual binary64 values, interpreted as exact rationals for transport and
verification. All original station states, Bminus<=sum Y<=B and the physical
Gini cap remain. No price upper is a physical routing incumbent.

## Inherited object and contribution boundary

For fixed marginals s, the expected unary penalty H(s)=sum h_i(y)s_iy is
independent of the chosen common legal inventory distribution. Hence the
minimum expected total objective decomposes as Theta(s)=H(s)+Gamma(s), with
Gamma minimizing expected f(Y)=max(gamma_L,G(Y)). This H is mathematical
unary penalty; the separately paid own-H is the complete startup heuristic.
R153 established compatible common stock distributions for all three actual
reference marginals, so incompatibility or observed penalty slack is not
the explanation used here. The inherited exact41/1080,169-row strict example
is a fixed-marginal comparison against its stated reference, not a strict
complete-routing witness. Its old global-floor gap does not transfer.

Parametric fractional programming, McCormick products, Dantzig–Wolfe column
generation and a bound ledger are established tools. See
[Dinkelbach (1967), On Nonlinear Fractional Programming](https://doi.org/10.1287/mnsc.13.7.492).
Its publisher record also attributes the fractional/parametric connection
to Jagannathan. We use a finite integer residual identity and interruptible
MILP lower bounds; no smooth convergence rate or unfinished old Dinkelbach
benchmark is invoked. The new experiment is this specific signed-state
original-coordinate residual and its use for actual hull proof thresholds.
The independent historical review records PR58's exact-S toy, existing
SP/cross-multiplied estimators and the prior R104/139/144/145 placements.

## Exact positive-stock residual

For S=sum c_iY_i>0, A=sum_{i<j}|c_iY_i-c_jY_j|,
G=A/(nS), D=sum d_i(Y_i), beta>=0 and p=beta*f+D,

    R_tau(Y)=S[p(Y)-tau]
            =max{S(beta*gamma_L+D-tau), beta*A/n+S(D-tau)}.

The positive branch uses safe0<l<=S<=u. A legal all-zero inventory is
separate, with p(0)=beta*gamma_L+sum d_i(0). Beta=0 removes no resource or
Gupper constraint. The residual q is free below zero.

For complete one-hot x_iy, introduce z_iy=S*x_iy with all four inequalities

    l*x <= z <= u*x,
    S-u*(1-x) <= z <= S-l*(1-x),

and each station's sum_y z_iy=S. The model explicitly defines Y_i=sum y*x,
r_i=c_iY_i, S=sum r_i. Factoring r avoids an extra rounding of c_i*y.
At integer x these force z=S*x, and W=sum d*z=S*D. Absolute-value variables
a_ij>=±(r_i-r_j), A=sum a, preserve A<=n*gamma_U*S. For any legal inventory,
its minimal absolute-value extension is feasible. A larger auxiliary A can
only increase the second residual branch because beta>=0. It cannot create
a lower objective than the true integer residual. A nonminimal completion
is therefore no authority for a true inventory price.

The epigraph is q>=W+(beta*gamma_L-tau)S and
q>=beta*A/n+W-tau*S. The additional resource product
Bminus*S<=sum y*z_iy<=B*S is valid at every integer inventory.

## State product versus aggregate McCormick

Let a_i=min_y d_i(y), b_i=max_y d_i(y), a=sum a_i, b=sum b_i and
D=sum d_i(y)x_iy. Nonnegative z-lx, with station sum S-l, gives
a(S-l)<=W-lD<=b(S-l). Likewise ux-z has station sum u-S, giving
a(u-S)<=uD-W<=b(u-S). These are all four McCormick inequalities for
W=S*D over [l,u]×[a,b], including arbitrary signed d.

Strictness of this product block is witnessed by Y1∈{1,2,3},Y2=1,c=(1,1),
d1=(0,1,2),d2=0. At the one-hot Y1=2 point, S=3,D=1, the Cartesian
aggregate rectangle [2,4]×[0,2] allows W=2; the state lift forces W=3.

This is neither a complete-Q nor a normalized-RN dominance theorem. Hard-total
DP can tighten D beyond the Cartesian range, and those aggregate products
are not automatically implied. For Y1,Y2∈{0,1},Y1+Y2=1,c=(1,2),d_i(y)=y,
take x_i1=.5,S=1.5,z_i1=.5,z_i0=1 at each station. The basic state products
are feasible with W=1; the exact hard total forces D=1 and W=S=1.5 in the
tighter aggregate product. The total-product row excludes this example.
It does not prove that total-product rows imply every possible DP tightening.

The targeted stronger implementation conditions the same safe denominator
bounds on x_iy=1 and x_iy=0. Its complement product is S-z_iy=S(1-x_iy).
These are necessary consequences, not a smaller selected support. It also
computes hard-total DP min/max of the actual written centered state costs
and retains their four aggregate McCormick rows. Signed D and W are free.
The exact coefficient/RHS transport below keeps every original integer
extension. This is one targeted response to the observed weak root LP.

## Actual coefficient and Native error transport

Choose station midpoint anchors a_i and centered costs dtilde=d-a_i.
For a power-of-two residual scale k, the two epigraphs use

    q >= sum (dtilde/k)*z + ((sum a_i+beta*gamma_L-tau)/k)*S,
    q >= sum (dtilde/k)*z + ((sum a_i-tau)/k)*S + (beta/(n*k))*A.

Every nonexact coefficient on nonnegative z,S,A is written downward.
Thus the actual written RHS is no greater than the exact residual/k;
minimizing its integer epigraph is a necessary relaxation. The physical
Gupper coefficient is written upward. The scale, actual coefficients,
signed one-hot errors and station anchors are saved in call.json. q alone
has objective coefficient1. No ordinary price guard is copied into a
residual objective.

The declared residual-unit Native guard is

    guard_scaled=1e-6*(1+u*sum_i max_y |written centered cost_i(y)|
                      +u*max(|written S_floor|,|written S_G|)
                      +(n*gamma_U*u)*|written A coefficient|).

The qualified original residual lower is k*(ObjBound-guard_scaled), prior
to price conversion. This retains the accepted Native numerical policy;
it is a guarded Native certificate, not an exact rational MIP solve.
Finite small domains check all actual rows, both bound signs, signed
nonzero state-rounding errors, beta=0, zero/positive branches and a
nonminimal A extension. Unknown or unreturned calls contribute no new bound.

For the DP-tight cost products, Dhat=sum written_cost*x and
What=sum written_cost*z use the identical actual coefficients. DP computes
their exact hard-total cost bounds; the written lower a and upper b are
outward. McCormick rows have exact binary64 slope/endpoint coefficients
and outward RHS -slope*endpoint. This avoids hidden rounded cost products.
The failed initial S_L=0 applicability interpretation is retained as a real
qualification failure and corrected; it is not a Native infeasibility proof.

## Price recovery, target reuse and fixed-direction ceiling

If ell is a qualified residual lower on the entire positive branch, then

    m_plus >= tau + ell/u if ell>=0,
    m_plus >= tau + ell/l if ell<0.

For each inventory p=tau+R_tau/S. With ell>=0, division by S<=u gives
ell/S>=ell/u; with ell<0, S>=l gives ell/S>=ell/l. The sign branch is
essential. A legal zero price is combined by minimum, then whole-domain
DP and earlier same-direction qualified prices by maximum. A weaker new
form never lowers the retained price bound.

For the exact same R,beta,d, R_tau'=R_tau-(tau'-tau)S, so a saved lower
transports as ell_tau-max{(tau'-tau)l,(tau'-tau)u}. This lower is preserved
explicitly; a new Native call need not return a stronger raw bound.
The exact beta identity, exact tau and exact signed d are saved and checked.
Every returned Y is independently evaluated at the original p/resources/
true G before it becomes an upper or a column. q and the auxiliary
completion do not determine that price.

For a qualified Q residual C_Q and true-column intercept a_K, the lower is
C_Q+min(a_K,L_m). A desired hull value zeta needs price tau=zeta-C_Q and
zeta<=C_Q+a_K. A known true price upper U_m limits this individual
certificate to C_Q+min(a_K,U_m). It is not a full-hull upper and does not
exclude combined support effects. A real Y with price<tau rejects this
target and supplies a column; it does not refute the entire hull.

## External proof floor E

E pays the same own-H and current-root producer as R153 J: node limit4096,
original price absolute gap1e-4, Seed0/Threads1, no historical stock/price/
incumbent injection. J adds a total-objective Native row; E skips that row.
The formal Native model, cutoff, LP/native search bounds, AM evaluation
and priority order remain the B model and search inputs on the same domain.

The first artifact alone does not authorize a global floor. E binds its
source to L0, the single complete root Gini interval, current input,
coefficients, supports and cutoff U0. Existing descendant support/Gini/
cutoff checks remain. Its proof consumer copies the existing scheduler,
merges min(U0,ell) into covered final leaves, and computes

    L_proof=min_j max(L_j,ell_j).

Uncovered leaves keep their raw L_j. The U0 complement is necessary for a
source restricted to F<=U0: outside it, F>=U0 is already known. The proof
snapshot can legally close a domain whose bounds meet the own verified U;
this is checked before further search. The raw scheduler remains unchanged,
including the parent/child AM inputs. Source rejection or an absent source
preserves the old information, and a Native revocation keeps the old
fail/open disposition. Final proof leaves and the final trace name the
external source; raw per-leaf values are separately saved. The inherited
physical/H/Start/Native-quality/coverage checks are retained and only the
scoped proof collector learns this separately audited source.

## Stopping on the actual mathematical task

The target protocol leaves both pricing matrices intact. It sets the
residual Native best-bound stop to guard_scaled. For the normalized model,
it uses (tau-anchorSum)/scale+guard+coefficient_correction, rounded upward.
The final returned bound still pays its guard and conversion; a status
code alone never proves the target. A MIPSOL callback reads only the state
choices and reevaluates original resources, true G and exact p. Only a
legal stock with p<tau requests counterexample termination and enters the
true column pool. Nonminimal auxiliary completion is not its price.

The native mechanisms are standard
[BestBdStop](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameterbestbdstop)
and [Model.terminate](https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html#Model.terminate).
Their [return statuses](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html)
are interpreted only after Optimize returns. A finite USER_OBJ_LIMIT bound
uses the saved bound-stop plan. An INTERRUPTED bound is accepted only when
this call recorded its own independently valid counterexample; otherwise
it supplies no new Native lower. Legal zero inventory is still combined
by minimum, and all earlier same-direction information is retained.
This is mathematical stopping, with no elapsed-time component switch.
The generated function body and actual thresholds are saved per call.
