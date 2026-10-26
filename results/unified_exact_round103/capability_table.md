# Necessary-domain capability (before complete-solve evaluation)

Every row below uses a retained full original-column point and its actual
canonical matrix. The same declared floating resource predicate is used
for support and member-plan checks. These are necessary service plans,
not feasible physical routes.

|Role/point|Full-domain classification by vehicle|Interpretation|
|---|---|---|
|F2 raw|OUTSIDE, OUTSIDE|Reliable signed dyadic rows; positive control|
|F2 first native|INSIDE, OUTSIDE|Explicit membership on one car; native processing still leaves an increment on the other|
|C2 raw|OUTSIDE, OUTSIDE, OUTSIDE|Finite-direction zero hits were not full-hull membership|
|C2 first native|OUTSIDE, OUTSIDE, OUTSIDE|Same distinction at the actual native point|
|F5 raw|OUTSIDE, OUTSIDE, OUTSIDE, OUTSIDE|Finite-direction zero hits were not full-hull membership|
|F5 first native|OUTSIDE, OUTSIDE, OUTSIDE, OUTSIDE|Real full-vector separation remains possible|
|N2 raw|OUTSIDE, OUTSIDE, OUTSIDE|Activation role has complete-domain separation|
|N2 first native|OUTSIDE, INSIDE, INSIDE|Explicit combinations distinguish vehicle-specific ability|

No incomplete callback column slice is treated as a full point. All initial results remain under
their original exclusive labels, including the failed first C2-native
reader and its fresh-label correction.

|Same original LP scope|L0|Literal finite LJ|Base hull capability|Three-anchor capability|
|---|---:|---:|---|---|
|C2|0.16123605049876005|same|Closed within1e-8, same objective|Closed within1e-8, same objective|
|F5|0.24416944802555995|0.24416944802753696|Outer LB0.244169448027537; numerical full-model upper witness0.24416944802753704|Outer LB0.24416944802753954; upper witness0.24416944802753704|
|F2|0.528625649465355|0.5286753357380306|Closed within1e-8 at0.638005040404497|Not pursued|

LJ literal weights/RHS for all three roles were separately repriced on the
actual current C++ domain in same_domain02; all18 vehicle support values
match the inherited values. C2's base closure used133 rows and79 outer LP
calls; its enhanced closure used85 rows and50 outer LP calls. F2's base
closure used827 rows and456 outer LP calls. These diagnostic closure rows
are not imported into the production mechanism.

F5's original base outer approximation stops UNKNOWN on a duplicate/no-new
row. Recovery preserves car3's normalized combination residual upper
1.2846489191563578e-8, above1e-8; it is not relabeled INSIDE. Separately
paid finite-column restrictions preserve explicit rational combinations
and check the full original matrix. Their numerical residuals are
1.4552e-11(base) and2.5739e-10(enhanced). The tiny enhanced signed bracket
inversion of about2.5e-15 is retained as numerical LP uncertainty. These
are qualified numerical objective brackets, not strict rational primal
and dual optimality certificates.

Actual three-anchor point reclassification gives C2 OUTSIDE/INSIDE/OUTSIDE
and F5 OUTSIDE on all four vehicles. The C2 INSIDE outcome demonstrates
why excluding one old mixture is insufficient. The stronger domain has
real projection increment but no useful objective improvement on these
two decisive models. Its additional mask/certificate cost rejects it for
the production candidate. F2's base-domain improvement, by contrast,
justifies testing a unified low-cost pre-MIP separation pass.

Capability conclusions and complete native certification/time conclusions
are separate. Full-hull LP strength does not predict that one production
pass will recreate it, nor that either will beat the original Gurobi engine.

Independent exact rechecking found that historical diagnostic floating
display fields named verified_distance_upper were nearest-rounded from
Fraction and can be smaller than the exact residual by half an ULP.
INSIDE decisions used exact Fraction comparisons and remain valid. Do not
treat those historical display fields as strict upper certificates; use
the retained rational combinations and independent exact residuals. The
diagnostic writer now emits an outward-rounded upper plus its exact
rational value. Existing evidence is preserved. Production C++ interval
enclosures were already outward-rounded and are unchanged.
