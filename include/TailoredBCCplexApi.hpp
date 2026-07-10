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
    bool relaxation_vector_snapshot_available = false;
    bool relaxation_vector_api_called = false;
    int relaxation_vector_api_return_code = -1;
    int relaxation_vector_length_requested = 0;
    int relaxation_vector_length_returned = 0;
    long long relaxation_vector_nonzero_values = 0;
    double relaxation_vector_objective = 0.0;
    std::string relaxation_vector_sample_variable_names;
    std::string relaxation_vector_sample_variable_values;
    std::string relaxation_vector_full_variable_names;
    std::string relaxation_vector_full_variable_values;
    std::string relaxation_vector_failure_reason;
    bool candidate_vector_snapshot_available = false;
    bool candidate_vector_api_called = false;
    int candidate_vector_api_return_code = -1;
    int candidate_vector_length_requested = 0;
    int candidate_vector_length_returned = 0;
    long long candidate_vector_nonzero_values = 0;
    double candidate_vector_objective = 0.0;
    std::string candidate_vector_sample_variable_names;
    std::string candidate_vector_sample_variable_values;
    std::string candidate_vector_full_variable_names;
    std::string candidate_vector_full_variable_values;
    std::string candidate_vector_failure_reason;
    bool best_bound_available = false;
    std::string best_bound_fail_reason;
    bool checkpoint_log_written = false;
    long long checkpoint_rows_written = 0;
    double last_checkpoint_time = 0.0;
    bool callback_wall_time_abort = false;
    int native_time_limit_param_id = 0;
    double native_time_limit_seconds = 0.0;
    int native_time_limit_set_rc = 0;
    long long callback_abort_requests = 0;
    int terminate_set_rc = 0;
    bool terminate_triggered = false;
    double terminate_after_seconds = 0.0;
    bool checkpoint_best_bound_available = false;
    double checkpoint_best_bound = 0.0;
    bool checkpoint_incumbent_available = false;
    double checkpoint_incumbent = 0.0;
    long long checkpoint_node_count = 0;
    long long user_cuts_added = 0;
    long long callback_gini_interval_cuts_added = 0;
    long long callback_visit_inventory_cuts_added = 0;
    long long callback_gini_subset_envelope_cuts_added = 0;
    long long callback_gini_subset_envelope_candidates = 0;
    long long callback_gini_subset_envelope_violations = 0;
    double callback_gini_subset_envelope_max_violation = 0.0;
    long long callback_expensive_separation_calls = 0;
    long long callback_expensive_separation_skips = 0;
    long long callback_low_gini_l1_cuts_added = 0;
    long long callback_low_gini_l1_violations = 0;
    long long callback_local_centering_cuts_added = 0;
    long long callback_local_centering_violations = 0;
    double callback_local_centering_max_violation = 0.0;
    long long callback_subset_cross_h_centering_cuts_added = 0;
    long long callback_subset_cross_h_centering_candidates = 0;
    long long callback_subset_cross_h_centering_violations = 0;
    double callback_subset_cross_h_centering_max_violation = 0.0;
    long long callback_local_q_centering_cuts_added = 0;
    long long callback_local_q_centering_violations = 0;
    double callback_local_q_centering_max_violation = 0.0;
    long long callback_gs_product_cuts_added = 0;
    long long callback_gs_product_violations = 0;
    double callback_gs_product_max_violation = 0.0;
    long long callback_disagg_sp_cuts_added = 0;
    long long callback_disagg_sp_violations = 0;
    double callback_disagg_sp_max_violation = 0.0;
    long long callback_vector_route_cutset_cuts_added = 0;
    long long callback_vector_route_cutset_candidates = 0;
    long long callback_vector_route_cutset_violations = 0;
    double callback_vector_route_cutset_max_violation = 0.0;
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
    const std::string& separation_pacing,
    int separation_min_relaxation_calls,
    const std::string& callback_cut_profile,
    bool enable_local_centering,
    bool enable_subset_cross_h_centering,
    int subset_cross_h_max_size,
    int subset_cross_h_max_cuts,
    const std::string& subset_cross_h_separation_profile,
    bool enable_local_q_centering,
    double lambda,
    double cutoff_value,
    int vehicle_count,
    const std::filesystem::path& progress_log_path = {},
    double progress_interval_seconds = 0.0);

} // namespace ebrp
