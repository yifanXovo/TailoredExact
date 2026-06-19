#pragma once

#include "Column.hpp"
#include "Instance.hpp"
#include "Result.hpp"

#include <limits>
#include <vector>

namespace ebrp {

struct ColumnGenerationResult {
    bool complete = false;
    int iterations = 0;
    int required_i = 0;
    int required_j = 0;
    long long pricing_calls = 0;
    long long generated_columns = 0;
    long long route_states = 0;
    long long operation_states = 0;
    double lp_objective = 0.0;
    double best_pricing_reduced_cost = 0.0;
    std::vector<std::vector<RouteLoadColumn>> columns_by_vehicle;
    std::vector<std::string> notes;
};

struct GiniCapColumnGenerationResult {
    bool complete = false;
    bool infeasible = false;
    int iterations = 0;
    long long pricing_calls = 0;
    long long generated_columns = 0;
    long long route_states = 0;
    long long operation_states = 0;
    long long cuts_added = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    double gamma = 0.0;
    double gamma_floor = -1.0;
    double lp_lambda_penalty = 0.0;
    double fixed_cap_surrogate = 0.0;
    double best_pricing_reduced_cost = 0.0;
    std::vector<std::vector<RouteLoadColumn>> columns_by_vehicle;
    std::vector<RouteLoadColumn> flat_columns;
    std::vector<double> z_values;
    std::vector<double> y_values;
    std::vector<std::string> notes;
};

struct GiniCapBranchProbeResult {
    bool complete = false;
    bool root_complete = false;
    bool forbid_child_complete = false;
    bool require_child_complete = false;
    int station_i = 0;
    int station_j = 0;
    double together_value = 0.0;
    double root_bound = 0.0;
    double forbid_child_bound = 0.0;
    double require_child_bound = 0.0;
    long long pricing_calls = 0;
    long long generated_columns = 0;
    long long route_states = 0;
    long long operation_states = 0;
    std::vector<std::string> notes;
};

struct GiniCapTreeResult {
    bool complete = false;
    bool hit_time_limit = false;
    bool lower_bound_valid = true;
    int nodes_solved = 0;
    int integer_leaves = 0;
    int projected_leaves = 0;
    int branched_nodes = 0;
    int pruned_by_bound = 0;
    int open_nodes = 0;
    int max_depth = 0;
    long long pricing_calls = 0;
    long long generated_columns = 0;
    long long route_states = 0;
    long long operation_states = 0;
    long long cuts_added = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    double gamma = 0.0;
    double gamma_floor = -1.0;
    double resource_penalty_lower_bound = 0.0;
    double resource_objective_lower_bound = 0.0;
    int resource_total_pickup_limit = 0;
    bool has_integer_incumbent = false;
    double global_lower_bound = 0.0;
    double best_integer_surrogate = 0.0;
    int best_integer_columns = 0;
    std::string incumbent_source;
    ObjectiveParts best_integer_parts;
    std::vector<int> best_final_inventory;
    std::vector<RoutePlan> best_routes;
    std::vector<std::string> notes;
};

ColumnGenerationResult runCoverageColumnGenerationDiagnostic(
    const Instance& instance,
    double time_limit_seconds,
    int max_iterations = 8);

GiniCapColumnGenerationResult runGiniCapColumnGenerationDiagnostic(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations = 12);

GiniCapBranchProbeResult runGiniCapRyanFosterBranchProbe(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations = 12);

GiniCapTreeResult runGiniCapBranchPriceTreeDiagnostic(
    const Instance& instance,
    double lambda,
    double gamma,
    double gamma_floor,
    double time_limit_seconds,
    int max_iterations = 12,
    int max_nodes = 31,
    const std::vector<RoutePlan>* seed_routes = nullptr,
    bool use_combined_gini_lower_bound = false,
    double objective_cutoff = std::numeric_limits<double>::infinity(),
    int warmstart_level = 1,
    double early_stop_lower_bound = std::numeric_limits<double>::infinity(),
    int pricing_return_columns = 1);

} // namespace ebrp
