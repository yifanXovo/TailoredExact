# One fixed original inventory objective

The saved root scope supplies complete station supports, hard unweighted
total limits, original binary64 ratio coefficients c_i, gamma bounds and
the legal zero branch. S=sum c_i Y_i is weighted. The target is always
phi=max(gamma_L,A/(nS))+H, H=sum omega_i |c_iY_i-1|, beta=1,d=h.
The coefficients already contain the original normalization/lambda; no
extra lambda is applied. H>=0 does not make its centered Native costs
nonnegative.

For positive l<=S<=u and target tau, R_tau=S(phi-tau) has two linear
epigraph branches after exact state products Sx are introduced. A qualified
residual lower ell yields phi>=tau+ell/u for ell>=0 and phi>=tau+ell/l
otherwise. Evaluate zero exactly and combine by minimum, then retain any
previous lower for this same full original objective by maximum.
All returned stocks are independently evaluated in original coordinates.
A true phi<tau improves this very objective's inventory upper. Proof of
phi>=tau or such a counterexample resolves the corresponding midpoint;
finite node termination can remain undecided.

The sole new strengthening uses an actually checked inventory upper U.
Every original optimum has H<=U-gamma_L, and the upper's own witness is
retained. For centered scaled true D*=(H-A0)/sigma and actual Native state
coefficients a_iy, e+=sum_i max(0,max_y(a_iy-(h_i(y)-anchor_i)/sigma)).
Thus Dhat<= (U-gamma_L-A0)/sigma+e+ throughout that preserved domain.
The written upper b is rounded up and intersected with the exact actual-cost
hard-total DP upper. The old DP lower a is retained. Four inherited aggregate
McCormick rows for W=S Dhat use l,u,a,b, with outward RHS products. There is
no extra state-deletion variant or phi-cutoff variant.

The actual Native D definition is read before the cost DP and cap; W and
both epigraphs use those same actual coefficients. The additional epigraph
error is bounded one-sided in scaled residual units, including any observed
S/A coefficient omission. The inherited R134/R154 numerical guard is paid
in full in addition. Only then is ell converted into a restricted phi lower.
Restore a full-domain lower by min(U, restricted_phi_lower), combine zero,
and retain the inherited full lower. We do NOT equate the restricted and
unrestricted residual minima. An unexpected status retains safe information.

All these rows belong only to an independent inventory optimization. Its
upper is not a physical BRP incumbent and never deletes BRP stocks/routes.
The E consumer continues to receive only a qualified original-domain scalar
lower. The Native BRP model, AM, ordering and splitting are outside this
round's algorithmic change.

The independent arithmetic reader enumerates small legal domains, including
zero, signed centered costs, negative q and actual omitted coefficients;
it lifts every preserved stock into all actual Native rows exactly and
reconstructs base-plus-delta matrices. These are separate-reader checks by
the same agent, not a nonimplementer-agent review. The measured RX35 model
and saved inventories also require actual readback before final claims.

Parameterization retains classical attribution to Dinkelbach (1967),
https://doi.org/10.1287/mnsc.13.7.492. McCormick, bisection and the inherited
state-product formulation are not claimed as new general theory.
