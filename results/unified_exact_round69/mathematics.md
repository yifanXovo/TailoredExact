# Existing-witness integration: correctness and limits

Retain Round67 VD-P's exact integer-state formulation and the original route,
operation, prefix-load, time and objective semantics. This stage changes no
constraint or variable domain. A complete Start is an initial primal candidate
for Gurobi's full MIP engine; it excludes no feasible solution or proof region.
The inherited metric/nonnegative-penalty applicability conditions still apply.

Given the currently best verified route-operation witness, remove empty routes
and relabel only equal-capacity vehicles by nonincreasing served count (stable
original labels break ties). With common T and common handling coefficients,
these vehicles are interchangeable. Route order, operations, inventory and
objective are unchanged; independent verification checks this correspondence.
No route is reassigned across unequal capacities.

For each actual inventory-state column at station i, set s_(i,y)=1 exactly when
y=Y_i, otherwise0; set q_(i,y)=G*s_(i,y). Set every original auxiliary from its
route/inventory definition, including Z_i=G*Y_i, deviations and pairwise
absolute differences. Existing common-column mapping is reused. The full
point is eligible only in its current Gini interval and non-strict cutoff.
Actual bounds, integer types, all linear rows and objective are checked before
submission. This numerical check supplements the algebraic map and physical
verifier; it is not a rational certificate or proof of all retained cuts on
arbitrary nonmetric inputs.

An ineligible current witness is simply not a candidate in that interval.
The interval remains in the normal full proof cover. An accepted Start cannot
make an invalid LB valid; global LB still comes from the complete frontier and
qualified native bounds. Supplied, read back, loaded by the native solver and
observed as an incumbent are distinct evidence states. No runtime or general
speedup theorem follows from primal feasibility.

The only time bound is the unchanged experiment-wide deadline. Model reading,
normalization, mapping, residual checks, telemetry, native optimization and
finalization all consume it. A refreshed native allowance represents the same
deadline and ends the whole algorithm on expiry; it never selects another
module or restarts an unfinished proof service.

Separate shared serialization correction: an empty LP left-hand side is written
as `0 G`, with the existing G column, instead of the invalid bare-constant form.
This preserves the intended exact zero expression, including infeasible constant
rows. All arms use this correction; it is not a Start constraint or performance
claim. The finite previous-stage artifact audit is recorded in preflight.md.
