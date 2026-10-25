#pragma once
#include "PhysicalWitnessValidation.hpp"
#include <cmath>
#include <cstdint>
#include <exception>

namespace ebrp {
// Exact stock arithmetic establishes F(x)=0. A small floating objective alone
// never establishes this predicate. The nonnegative floor covers the original
// physical feasible set and has no dependency on a native model or bound.
inline bool exactZeroInventoryObjective(const Instance& in, double lambda,
                                       const std::vector<int>& y) {
    if (in.V <= 0 || !std::isfinite(lambda) || lambda < 0 ||
        y.size() != static_cast<std::size_t>(in.V + 1) ||
        in.target.size() != y.size() || in.weights.size() != y.size()) return false;
    for (int i = 1; i <= in.V; ++i) {
        if (in.target[i] <= 0 || y[i] < 0 || !std::isfinite(in.weights[i]) ||
            in.weights[i] < 0) return false;
        // Nonnegative int products fit in signed int64. Equal ratios imply
        // A=0, including the all-zero S=0 case.
        if (std::int64_t(y[i]) * in.target[1] !=
            std::int64_t(y[1]) * in.target[i]) return false;
        if (lambda > 0 && in.weights[i] > 0 && y[i] != in.target[i]) return false;
    }
    return true;
}

inline bool applyIndependentZeroCertificate(const Instance& in, double lambda,
                                           SolveResult& result, bool outer = false) {
    const auto& previous = result.verification;
    if (!previous.original_solution_feasible || !previous.original_objective_recomputed ||
        !previous.errors.empty() || !exactZeroInventoryObjective(in, lambda, previous.final_inventory))
        return false;
    Verification checked;
    try {
        // Includes exactly one record per vehicle, integer overflow, station,
        // prefix capacity, returned load/unloading and duration checks.
        checked = verifyCompletePhysicalStartingWitness(in, result.routes, lambda);
    } catch (const std::exception&) { return false; }
    if (!exactZeroInventoryObjective(in, lambda, checked.final_inventory) ||
        checked.objective != 0.0) return false;
    result.verification = checked;
    result.final_inventory = checked.final_inventory;
    result.objective = 0.0;
    result.G = checked.G;
    result.P = checked.P;
    result.lower_bound = result.upper_bound = result.final_UB = result.gap = 0.0;
    result.strict_certified_original_problem = true;
    result.strict_certificate_policy_version = "independent-objective-zero-v1";
    result.strict_certificate_class = "independent_zero_nonnegative_floor";
    result.strict_certificate_rejection_reason = "none";
    result.strict_lower_bound_source = "independent_full_domain_nonnegative_floor";
    result.feasibility_consistency_gate_passed = true;
    result.verified_incumbent_objective_available = true;
    result.verified_incumbent_objective = 0.0;
    result.verified_incumbent_original_problem_feasible = true;
    result.status = "independent_zero_optimal";
    result.certificate = "Own complete physical fleet has exact zero inventory objective; "
                         "independent full-domain F>=0 proves optimality. Native qualification is unchanged.";
    if (outer) {
        result.external_gini_tree_strict_certified = true;
        result.external_gini_tree_certificate_class = result.strict_certificate_class;
        result.external_gini_tree_certificate_rejection_reason = "none";
        result.external_gini_tree_global_lower_bound = 0.0;
        result.external_gini_tree_verified_upper_bound = 0.0;
    }
    return true;
}
} // namespace ebrp
