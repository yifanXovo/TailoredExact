# Penalty information returned to the state-product block

The intervention propagates an already implied scalar bound. It does not discover a new scalar penalty inequality. Let the actual Native objective be `g + sum omega_i e_i`, with the coefficients already including lambda, objective constant zero, `e_i >= |c_i Y_i - 1|`, and the current arm's verified cutoff U0. The continuous inventory relaxation is `ell_i <= Y_i <= u_i`, `Bminus <= sum Y_i <= B`; its boxes come from the same initial root support. Routing, integrality and holes in support are relaxed. Every old LP inventory projection and every integer improving completion lies in this set.

Write p* for its minimum weighted absolute deviation. For any nonnegative finite mu,nu,

```
d(mu,nu) = mu Bminus - nu B
           + sum_i min_{ell_i <= y <= u_i}
               {omega_i |c_i y - 1| + (nu-mu)y} <= p*.
```

Each station minimum is attained at an endpoint or the exact kink 1/c_i when it lies in the box. Starting at the clipped individual kinks, allocating a shortage or surplus by increasing omega_i c_i gives an exact continuous resource optimum. Production uses that greedy allocation only to choose a finite binary64 multiplier; sorting accuracy cannot invalidate weak duality. Production then encloses the dual expression with outward binary64 intervals. The kink is evaluated with an enclosure of 1/c_i and exact zero absolute penalty. A possibly extra kink candidate weakens the minimum. Set `p_lower=max(0,d_lower)`, and `beta=min(gamma_U_root,up(U0-p_lower))`. The diagnostic Fraction oracle independently verifies exact primal=dual for the resource relaxation, and that the production lower value is no greater than the exact dual at its actual multipliers.

The weighted coefficients are read from the actual formal objective, never multiplied by lambda again. Tiny positive objective coefficients below 1e-12 are omitted in the floor to weaken it safely. Production requires ordinary positive transported c_i. The actual physical input hash, inventory totals, objective coefficients and root support are frozen and checked on inheritance. A negative beta is a scope/arithmetic failure, not silently clipped to zero.

The original cutoff and penalty rows imply `g<=U0-p_lower`, even at a fractional LP point where g need not majorize the physical nonlinear Gini expression. Consequently `g<=beta` alone is redundant in exact mathematics. For an integer one-hot completion the old product block has

```
sum_y s_iy = 1,
sum_y t_iy = g,
gamma_L s_iy <= t_iy <= gamma_U s_iy,
t_iy = g s_iy at integer s.
```

PF adds `t_iy-beta s_iy<=0` for every current state whenever the old upper gamma_U is larger. Summing gives g<=beta; subtracting the other states' upper rows gives `t_iy>=g-beta(1-s_iy)`. This complete-block equivalence requires the whole submitted group or old rows already dominating it. No complementary lower facets or columns are needed. If beta is smaller than Native's tiny-coefficient threshold, the entire new group is omitted rather than dropping a negative selector coefficient. The delivered ordinary-domain matrices submit every intended row without tiny omissions.

Every integer completion satisfying the old cutoff has g<=beta and t=gs, so PF preserves it, including feasible nonminimal g/e completions. Such completions must also satisfy all existing auxiliary rows and bounds: in the fixed qualification fixture W_SP fixes the minimal e completion, so only g is made nonminimal there. Other actual writer fixtures qualify both nonminimal g and e with the compatible W_SP extension. This is a fixture requirement, not a change to production Starts.

The root beta is frozen. A compatible child inherits it only under narrower support, nonexpanding gamma interval, same input/objective/resource units and a nonincreasing cutoff. An old child upper already below beta needs no extra rows. A child with gamma_L>beta has an empty cutoff improving set; the original closed proof cover and infeasibility machinery remain responsible for it. The physical original problem is not declared infeasible, and no epsilon gap is introduced.

## Strictness and limits of the claim

For one station with two states and old interval [0,1], let beta=.6, s=(.5,.5), g=.5 and t=(.4,.1). The old mass and product-sum rows and the scalar bound all hold, but `.4>.6*.5`. Thus a redundant scalar bound can strengthen its product expression. For the full model, PF is a subset of the old LP with the same objective, so its exact minimization value cannot decrease. Neither inclusion nor old-point separation alone proves a strict optimal-value increase, or a faster MIP.

This is ordinary bound propagation and product convexification. The project-specific result is the computable weighted BRP resource floor, the observed propagation gap in the current VD-P formulation, the actual submitted-matrix verification, and its measured complete-search consequences. It is not a new general convexification theorem or a claim to an OR-level outcome by arithmetic alone.

The R148 D strong child LP values also delimit the AM interpretation: K35 `.545266780934=.383728302362+.161538478571` and RB35 `.313861187073=.222744904476+.091116282597` equal that child's G lower endpoint plus the global continuous penalty floor. Left/right asymmetry alone therefore does not establish new nontrivial conditional information lost by AM. This study propagates the floor into the product expression and retains the original root/midpoint geometry; it does not claim to recover an unmeasured AM split benefit.

## Production lifecycle

The default-off flag is `--round149-penalty-feedback on|off`. In `ensureArtifact`, normal own H precedes the first canonical root; the existing GD block is embedded once, then PF is appended before backend construction or the first Optimize. Original bytes remain immutable; final SHA and GD expected rows are registered together. No pre-PF root is solved, no extra root LP is introduced, and no new source oracle is called. Later normal artifact generations may inherit the frozen root beta, but do not recompute it or change AM scheduling geometry. Full-run overhead includes arithmetic, construction, audit readback, presolve and branch/search changes.

The production source commit, new executable hash, wrapper commit, fixed science commit and delivery head are separate identities. R137 remains the stable default; R147 D remains its previously limited candidate. Shared-S and STOCK are off throughout this intervention.
