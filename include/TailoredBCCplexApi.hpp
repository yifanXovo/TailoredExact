#pragma once

#include "Result.hpp"

#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>

namespace ebrp {

struct TailoredBCCplexApiProbe {
    bool dll_found = false;
    bool required_symbols_found = false;
    bool callbacks_available = false;
    std::string dll_path;
    std::string fail_reason;
};

struct TailoredBCCplexApiSolveResult {
    bool attempted = false;
    bool available = false;
    bool solved = false;
    int return_code = -1;
    int status_code = 0;
    std::string status;
    std::string fail_reason;
    double objective = 0.0;
    double best_bound = 0.0;
    long long node_count = 0;
    long long relaxation_callback_calls = 0;
    long long candidate_callback_calls = 0;
    long long branch_callback_calls = 0;
    long long progress_callback_calls = 0;
    long long user_cuts_added = 0;
    long long callback_gini_interval_cuts_added = 0;
    long long callback_visit_inventory_cuts_added = 0;
    long long callback_gini_subset_envelope_cuts_added = 0;
    long long callback_gini_subset_envelope_candidates = 0;
    long long callback_gini_subset_envelope_violations = 0;
    double callback_gini_subset_envelope_max_violation = 0.0;
    long long callback_low_gini_l1_cuts_added = 0;
    long long callback_low_gini_l1_violations = 0;
    long long callback_variable_s_centering_cuts_added = 0;
    long long callback_variable_s_centering_violations = 0;
    long long callback_subset_inventory_imbalance_cuts_added = 0;
    long long callback_subset_inventory_imbalance_candidates = 0;
    long long callback_subset_inventory_imbalance_violations = 0;
    long long callback_transfer_cutset_cuts_added = 0;
    long long callback_transfer_cutset_candidates = 0;
    long long callback_transfer_cutset_violations = 0;
    long long callback_support_duration_pair_cuts_added = 0;
    long long callback_support_duration_pair_candidates = 0;
    long long callback_support_duration_pair_violations = 0;
    long long callback_support_duration_triple_cuts_added = 0;
    long long callback_support_duration_triple_candidates = 0;
    long long callback_support_duration_triple_violations = 0;
    long long callback_support_duration_quad_cuts_added = 0;
    long long callback_support_duration_quad_candidates = 0;
    long long callback_support_duration_quad_violations = 0;
    long long callback_support_duration_lifted_cuts_added = 0;
    long long callback_support_duration_lifted_candidates = 0;
    long long callback_support_duration_lifted_violations = 0;
    long long lazy_rejections = 0;
    long long lazy_gini_interval_rejections = 0;
    long long lazy_visit_inventory_rejections = 0;
    long long lazy_gini_subset_envelope_rejections = 0;
    long long lazy_low_gini_l1_rejections = 0;
    long long lazy_variable_s_centering_rejections = 0;
    long long lazy_subset_inventory_imbalance_rejections = 0;
    long long incumbents_seen = 0;
    long long incumbents_verified = 0;
    long long incumbents_rejected = 0;
    long long candidate_projection_checks = 0;
    long long candidate_projection_verified = 0;
    long long candidate_projection_rejections = 0;
    long long candidate_projection_unsupported_mismatches = 0;
    long long candidate_projection_ratio_rejections = 0;
    long long candidate_projection_penalty_rejections = 0;
    long long candidate_projection_objective_rejections = 0;
    double candidate_projection_max_gini_underestimate = 0.0;
    double candidate_projection_max_objective_underestimate = 0.0;
    long long candidate_route_projection_checks = 0;
    long long candidate_route_projection_verified = 0;
    long long candidate_route_projection_rejections = 0;
    long long candidate_route_projection_unsupported_mismatches = 0;
    long long candidate_route_projection_flow_rejections = 0;
    long long candidate_route_projection_station_rejections = 0;
    long long candidate_route_projection_service_rejections = 0;
    long long candidate_route_projection_duration_rejections = 0;
    long long candidate_route_projection_inventory_rejections = 0;
    long long candidate_route_projection_load_mismatches = 0;
    long long gini_branches_created = 0;
    long long branch_priorities_applied = 0;
    std::string branch_priority_status;
    std::unordered_map<std::string, double> values;
};

TailoredBCCplexApiProbe probeTailoredBCCplexApi();

TailoredBCCplexApiSolveResult solveLpWithTailoredBCCplexApi(
    const std::filesystem::path& lp_path,
    double time_limit_seconds,
    int threads,
    double gamma_L,
    double gamma_U,
    bool add_redundant_gini_user_cut,
    bool enable_candidate_validation,
    bool enable_gini_branching,
    bool enable_branch_priorities,
    double gini_branch_min_width,
    const std::vector<int>& station_initial,
    const std::vector<int>& station_capacity,
    const std::vector<int>& station_target,
    const std::vector<double>& station_weight,
    const std::vector<int>& vehicle_capacity,
    const std::vector<double>& distance_matrix,
    int node_count,
    double total_time_limit,
    double handling_unit,
    const std::string& support_duration_cover_mode,
    int gini_subset_max_size,
    int gini_subset_max_cuts,
    double lambda,
    double cutoff_value,
    int vehicle_count);

} // namespace ebrp
