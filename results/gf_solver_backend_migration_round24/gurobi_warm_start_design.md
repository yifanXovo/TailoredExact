# Verified Gurobi warm-start design

Warm starts are allowed only on newly created Gurobi interval models. Permitted sources are the same-run independently verified HGA-TGBC solution or an independently verified feasible solution found earlier in the same external-tree run. Plain CPLEX/Gurobi solutions and historical objective values are forbidden.

`MipStartMapping` canonicalizes interchangeable equal-capacity vehicles and maps every semantic and auxiliary variable required by the canonical model. Before `Start` is set, it verifies the original route solution and recomputed objective; interval membership including the shared endpoint rule; objective cutoff; all bounds, integrality, rows, auxiliary definitions, and variable coverage; and canonical vehicle-symmetry consistency. An invalid or incomplete candidate is not submitted.

Cold mode never sets any `Start` value. Warm mode changes no row, bound, objective, interval, split, scheduler decision, inherited LB, or process budget. A submitted start remains primal-only: it cannot close a leaf, certify feasibility without the verifier, or produce a lower bound. Native acceptance, rejection, or unknown disposition and mapping/processing time are separately audited.

The local license gate prevented runtime start submission and native acceptance measurement. Unit tests pass for a complete valid mapping, interval rejection, endpoint handling, invalid starts, cold isolation, auxiliary completeness, objective recomputation, and equal-capacity symmetry canonicalization.
