#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct SolverNeutralModelDomain {
    std::vector<std::string> names;
    std::vector<double> lower_bounds;
    std::vector<double> upper_bounds;
    std::vector<char> variable_types;
};

struct SolverNeutralMipStart {
    bool candidate_independently_verified = false;
    bool original_problem_feasible = false;
    bool objective_recomputed = false;
    bool interval_membership_valid = false;
    bool vehicle_symmetry_canonicalization_valid = false;
    bool all_semantic_columns_mapped = false;
    bool no_unsupported_columns = false;
    bool bounds_valid = false;
    bool integrality_valid = false;
    bool static_interval_rows_valid_by_factory_semantics = false;
    bool cutoff_valid = false;
    bool complete = false;
    std::string source;
    std::string failure_reason = "not_evaluated";
    double objective = 0.0;
    double G = 0.0;
    double P = 0.0;
    double mapping_seconds = 0.0;
    std::vector<double> values;
};

SolverNeutralMipStart mapVerifiedRoutesToCanonicalModel(
    const Instance& instance,
    const SolveOptions& options,
    const std::vector<RoutePlan>& routes,
    const std::string& source,
    double gamma_L,
    double gamma_U,
    double non_strict_cutoff,
    const SolverNeutralModelDomain& domain);

} // namespace ebrp
