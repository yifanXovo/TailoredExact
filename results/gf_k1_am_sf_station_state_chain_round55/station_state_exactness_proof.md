# Station-state integer exactness

Fix station (i) and its propagated allowed domain
\(\mathcal Y_i=\{L_i,\ldots,U_i\}\).

**Forward map.**  Given any original integer solution, set
\(s_{iy}=1\) at its unique value (y=Y_i) and zero otherwise, and set
\(q_{iy}=G\) for that state and zero otherwise.  Selector sum, inventory,
perspective, G reconstruction, and product reconstruction all hold.  For VD-J,
the ratio equality gives (r_i=Y_i/D_i) and the penalty equality gives the
unique objective-minimal value (e_i=|Y_i/D_i-1|).

**Reverse map.**  Binary selectors summing to one select a unique allowed
value (y^*\).  Inventory reconstruction gives (Y_i=y^*\).  Perspective
bounds force every unselected (q_{iy}) to zero; G reconstruction then gives
\(q_{iy^*}=G\), so product reconstruction gives (Z_i=y^*G=Y_iG\).
The VD-J equalities similarly recover the exact ratio and minimum penalty.

The original absolute-value inequalities remain in VD-J.  Since (e_i) has a
nonnegative objective coefficient and no constraint requires a larger value,
the replacement preserves the original decision feasible projection and its
optimal objective while eliminating only nonminimal auxiliary penalty values.
All routing, inventory, visit, conservation, and certificate rows remain.

The domain is obtained from proved station propagation, not from V/M/Q or an
instance label.  Hence the formulation introduces no algorithmic dispatch.
