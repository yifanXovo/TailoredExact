# Conditional resource information in state products

All statements use the actual saved binary64 coefficients interpreted as exact
rationals. The physical objective is unchanged. Write

\[
p(Y)=\sum_i h_i(Y_i),\qquad h_i(y)=\omega_i|c_i y-1|,
\quad P_e=\sum_i\omega_i e_i\ge p(Y),\quad g+P_e\le U_0.
\]

The weights \(\omega_i\) already contain lambda. They are read from the actual
objective, and are never multiplied by lambda a second time. The necessary
resource relaxation is
\(\mathcal R_0=\{Y:\ell_i\le Y_i\le u_i,\ B^-\le\sum_iY_i\le B\}\).
Routing, integer restrictions and holes in support are relaxed. Every old
integer improving completion and old LP inventory projection lies in this set.

## A fixed dual and its conditional cost difference

Reuse exactly the nonnegative binary64 \(\mu,\nu\) saved by R149, and put
\(a=\nu-\mu\). Define

\[
m_i=\min_{\ell_i\le z\le u_i}\{h_i(z)+az\},\qquad
d=\mu B^- -\nu B+\sum_i m_i.
\]

The Lagrangian resource term is nonpositive on \(\mathcal R_0\), hence
\(d\le\min_{\mathcal R_0}p(Y)\). Each station minimum needs only the two
endpoints and the kink \(1/c_i\) if present. For \(c_i=0\) there is no kink;
the penalty is constant and the affine part has an endpoint minimum. Zero
weight and fixed boxes also require no optimization call.

For a supported state \(Y_i=y\), define

\[
\delta_i(y)=h_i(y)+ay-m_i\ge0,\qquad
d_{iy}=\mu B^- -\nu B+\sum_{j\ne i}m_j+h_i(y)+ay=d+\delta_i(y).
\]

On that conditional resource set, weak duality gives
\(d\le d_{iy}\le p^*_{iy}\), where \(p^*_{iy}\) is the conditional resource
minimum. An empty conditional set has no improving completion and does not
invalidate the bound. The construction uses one fixed dual, with no per-state
LP, reallocation, source solve or dynamic incumbent rebuild. Exact prefix and
suffix sums give all leave-one-out terms in linear time after the minima are
available, so total arithmetic is \(O(n+\sum_i|\mathcal Y_i|)\).

The implementation does **not** subtract independently rounded lower bounds.
It computes each minimum and leave-one-out expression exactly as a Python
Fraction, then transports the completed bound in the required direction.

## Conditional upper facets and completion validity

Keep R149's safe global \(\underline p_0\) and uniform \(\beta_0\). Set

\[
\underline p_{iy}=\max\{\underline p_0,0,\operatorname{down}(d_{iy})\},\qquad
\beta_{iy}=\min\{\beta_0,\operatorname{up}(U_0-\underline p_{iy})\}.
\]

Append, without deleting any PF row,

\[
t_{iy}\le\beta_{iy}s_{iy}.
\]

An unselected integer state has \(s_{iy}=t_{iy}=0\). A selected state has
\(Y_i=y\) and \(t_{iy}=g\); the old cutoff and penalty epigraph give
\(g\le U_0-\underline p_{iy}\). Thus every integer completion satisfying the
old cutoff survives, including feasible nonminimal g/e completions. The proof
does not require g to equal the minimum physical Gini value. Other auxiliary
rows and bounds still have to hold for any proposed completion.

A conditional \(\beta_{iy}<\gamma_L\) identifies an empty state branch in the
improving domain. A negative conditional beta is legitimate and can be kept
in a signed row or the entire strengthening can safely be omitted. It does
not imply that the whole physical instance is infeasible; own-H may choose a
different state. Taking \(\min_y\beta_{iy}\) as a global g bound is invalid.
No such negative/empty-branch boundary occurs in the three entered matrices.

For one station, the simplex, product sum and bounds

\[
s_y\ge0,\quad\sum_y s_y=1,\quad\sum_y t_y=g,\qquad
\gamma_L s_y\le t_y\le\beta_y s_y
\]

describe the convex hull of that station's state disjunction. For positive
mass let \(g_y=t_y/s_y\in[\gamma_L,\beta_y]\); mixing those branch points
recovers the original point. Zero mass forces zero product and empty branches
receive zero mass. This is a local state/product hull. It is not the full BRP,
cross-station resource, integer-objective or routing hull. Keeping all old
rows gives a mathematical subset of the PF relaxation, but neither strict
block inclusion nor separation of an old optimum forces a strict objective
increment or better finite search.

## AP and CPF address different extended coordinates

R135 AP strengthens the penalty epigraph by the selector-weighted costs.
For support \(y\in\{1,2\}\), \(h(y)=.4|y-1|\), \(U_0=.8\),
\(\gamma_L=0\), \(\beta_0=.8\), the point
\(s=(.5,.5),Y=1.5,g=.4,t=(0,.4),P_e=.2\) satisfies AP, the cutoff and
uniform PF. The conditional \(\beta_2=.4\) requires \(t_2\le.2\), which
cuts the point. This proves AP does not imply CPF in the isolated block with
t retained. It is not a full BRP feasible point or a general AP/CPF ordering.
With the same \((s,g,P_e,Y)\), choosing \(t=(.2,.2)\) meets CPF. The complete
matched LP, with every variable free, therefore decides whether there is
optimization value beyond mere product redistribution.

## Actual transport and finite evidence

`round150_math.py` computes the minima and complete leave-one-out expression
exactly, rounds the penalty downward and beta upward, and omits a row when
it does not tighten old beta. A nonzero beta with magnitude below1e-12 causes
the entire new row to be omitted, rather than dropping only the selector
coefficient. Exact zero can use the valid one-term row. Every entered beta
is positive and ordinary in magnitude. Slightly tighter exact global d can
also tighten a delta=0 state compared with the conservative saved floor;
the actual row group is recorded rather than counted as an idealized subset.

The submitted groups contain451/902,539/1078 and143/286 rows/nonzeros for
K20,K35,RX20. Pure Fraction construction takes about.0116,.0124,.0037s;
complete matrix construction and readback are separately measured. The old
PF points have15,34,8 violations with maxima.019306833244,.003655840423,
.051858032938. Those maxima measure separation, not optimized objective gain.
The matched new LPs, old-point residuals, solutions, duals and full quality
records are in `LP_report.md` and the indexed diagnostic carrier.

R120–122 used solved subdomain/conditional F bounds; R146 GD uses state
conditions for the total ratio denominator S; R131 primarily contracts
domains; R149 feeds one global penalty floor into every product. CPF feeds
the same resource dual's state cost difference into each state product. These
use standard weak duality, conditioning, bound propagation and disjunctive
convexification. The contribution is the problem-specific expression relation,
cheap valid construction and measured evidence, without a claim of a new
general convexification theory or literature priority.
