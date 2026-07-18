#pragma once

#include "Result.hpp"
#include "StrictCertificate.hpp"
#include "DenseProgress.hpp"

#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>

namespace ebrp {

struct NativeMipEvidence {
    int mipopt_return_code = -1;
    int status_code = 0;
    std::string status_text;
    int objective_return_code = -1;
    bool objective_available = false;
    double objective = 0.0;
    int best_bound_return_code = -1;
    bool best_bound_available = false;
    double best_bound = 0.0;
    int mip_relative_gap_return_code = -1;
    bool mip_relative_gap_available = false;
    double mip_relative_gap = 0.0;
    StrictGapParameterRecord relative_gap{
        kCplexRelativeMipGapParam, 0.0, -1, -1, 0.0};
    StrictGapParameterRecord absolute_gap{
        kCplexAbsoluteMipGapParam, 0.0, -1, -1, 0.0};
    bool strict_gap_configuration_valid = false;
    bool solve_returned = false;
    bool evidence_capture_complete = false;
    int free_problem_return_code = -1;
    int close_environment_return_code = -1;
};

struct PlainCplexApiSolveResult {
    bool attempted = false;
    bool available = false;
    bool solved = false;
    std::string fail_reason;
    NativeMipEvidence native;
    long long node_count = 0;
    long long open_node_count = 0;
    long long simplex_iterations = 0;
    int native_solution_count = 0;
    int model_columns = 0;
    int model_rows = 0;
    long long model_nonzeros = 0;
    long long environment_count = 0;
    long long problem_count = 0;
    long long model_read_count = 0;
    long long mipopt_count = 0;
    long long freeprob_count = 0;
    long long close_count = 0;
    bool lifecycle_valid = false;
    int threads_requested = 1;
    int threads_set_return_code = -1;
    int threads_get_return_code = -1;
    int threads_effective = 0;
    int presolve_requested = 1;
    int presolve_set_return_code = -1;
    int presolve_get_return_code = -1;
    int presolve_effective = 0;
    int search_requested = 1;
    int search_set_return_code = -1;
    int search_get_return_code = -1;
    int search_effective = 0;
    int node_select_requested = 1;
    int node_select_set_return_code = -1;
    int node_select_get_return_code = -1;
    int node_select_effective = 0;
    int time_limit_parameter_id = 1039;
    double time_limit_requested = 0.0;
    int time_limit_set_return_code = -1;
    int time_limit_get_return_code = -1;
    double time_limit_effective = 0.0;
    bool native_cuts_default = true;
    std::string log_path;
    int log_set_return_code = -1;
    std::string native_cut_counts;
    std::string model_writer_fingerprint;
    std::string variable_domain_fingerprint;
    DenseProgressStats dense_progress;
    std::string dense_progress_raw_event_path;
    bool dense_progress_read_only_contract = false;
    std::unordered_map<std::string, double> values;
};

struct TailoredBCCplexApiProbe {
    bool dll_found = false;
    bool required_symbols_found = false;
    bool callbacks_available = false;
    std::string dll_path;
    std::string fail_reason;
};

struct TailoredBCNativeCheckpointConfig {
    bool enabled = false;
    std::filesystem::path path;
    std::string run_id;
    std::string instance_hash;
    std::string model_fingerprint;
    std::string formulation_profile;
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
    int native_mip_gap_param_id = 0;
    double native_mip_gap = 0.0;
    int native_mip_gap_set_rc = 0;
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
    double callback_vector_route_cutset_violation_sum = 0.0;
    long long callback_vector_route_cutset_cuts_size_2 = 0;
    long long callback_vector_route_cutset_cuts_size_3 = 0;
    long long callback_vector_route_cutset_cuts_size_4 = 0;
    long long callback_vector_route_cutset_cuts_size_5 = 0;
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

struct GlobalGiniTreeApiSolveResult {
    bool attempted = false;
    bool available = false;
    bool solved = false;
    int return_code = -1;
    int status_code = 0;
    std::string status;
    std::string fail_reason;
    NativeMipEvidence native;
    int model_columns = 0;
    int model_rows = 0;
    long long model_nonzeros = 0;
    double objective = 0.0;
    double best_bound = 0.0;
    bool best_bound_available = false;
    long long node_count = 0;
    long long environment_count = 0;
    long long problem_count = 0;
    long long model_read_count = 0;
    long long mipopt_count = 0;
    long long freeprob_count = 0;
    long long close_count = 0;
    long long interval_oracle_count = 0;
    long long child_process_count = 0;
    long long branch_callback_calls = 0;
    long long relaxation_callback_calls = 0;
    long long candidate_callback_calls = 0;
    long long progress_callback_calls = 0;
    long long gini_branch_nodes = 0;
    long long gini_children_created = 0;
    long long gini_branch_generations = 0;
    long long ordinary_branch_fallbacks = 0;
    long long nonoptimal_relaxation_fallbacks = 0;
    long long local_rows_attached = 0;
    long long local_bound_changes_attached = 0;
    long long local_row_failures = 0;
    long long column_mapping_failures = 0;
    long long coverage_failures = 0;
    long long child_estimate_failures = 0;
    long long local_bound_api_failures = 0;
    long long node_info_api_failures = 0;
    long long callback_failures = 0;
    long long post_row_reoptimizations = 0;
    long long post_row_reoptimization_failures = 0;
    long long theoretical_full_rows = 0;
    long long theoretical_full_bounds = 0;
    long long exact_duplicate_rows_omitted = 0;
    long long identical_bounds_omitted = 0;
    long long dominance_omissions = 0;
    long long delta_rows_attached = 0;
    long long delta_bounds_attached = 0;
    long long ordinary_branches_before_terminal_gini = 0;
    long long ordinary_branches_after_terminal_gini = 0;
    long long sibling_first_process_count = 0;
    long long sibling_equal_estimate_pairs = 0;
    long long sibling_discriminated_pairs = 0;
    long long native_simplex_iterations = 0;
    long long native_open_nodes = 0;
    long long native_solution_pool_count = 0;
    double first_gini_branch_time = -1.0;
    double row_factory_seconds = 0.0;
    double callback_packing_seconds = 0.0;
    double local_row_api_seconds = 0.0;
    int threads_requested = 1;
    int threads_set_rc = -1;
    int threads_get_rc = -1;
    int presolve_requested = 1;
    int presolve_set_rc = -1;
    int presolve_get_rc = -1;
    int presolve_effective = 1;
    int search_requested = 2;
    int search_set_rc = -1;
    int search_get_rc = -1;
    int search_effective = 2;
    int node_select_requested = 1;
    int node_select_set_rc = -1;
    int node_select_get_rc = -1;
    int node_select_effective = 1;
    int heuristics_get_rc = -1;
    int heuristics_effective = 0;
    int probing_get_rc = -1;
    int probing_effective = 0;
    int threads_effective = 1;
    bool native_cuts_default = true;
    int log_set_rc = -1;
    int native_time_limit_set_rc = -1;
    int native_time_limit_get_rc = -1;
    double native_time_limit_requested = 0.0;
    double native_time_limit_seconds = 0.0;
    double native_time_limit_effective = 0.0;
    bool solver_finalization_reached = false;
    bool callback_abort_used = false;
    bool recursive_branching_complete = false;
    bool row_migration_complete = false;
    bool sibling_isolation_by_construction = false;
    bool root_coverage_valid = false;
    bool branch_coverage_valid = false;
    bool lifecycle_valid = false;
    bool global_bound_monotone = true;
    bool no_time_quantum = true;
    bool no_instance_special_case = true;
    bool native_mip_start_attempted = false;
    bool native_mip_start_mapping_complete = false;
    bool native_mip_start_submitted = false;
    bool native_mip_start_stored = false;
    bool native_mip_start_accepted = false;
    int native_mip_start_return_code = -1;
    int native_mip_start_stored_count = 0;
    std::string native_mip_start_failure_reason;
    std::string child_estimate_mode;
    std::string row_attachment_mode;
    std::string row_timing_mode;
    std::string native_cut_counts;
    std::string row_factory_version;
    std::string root_model_fingerprint;
    std::string objective_fingerprint;
    std::string variable_domain_fingerprint;
    std::string row_family_inventory;
    std::string callback_row_inventory;
    std::string root_row_signature;
    std::string node_trace_path;
    std::string bound_trace_path;
    std::string manifest_path;
    std::string post_row_trace_path;
    std::string topology_trace_path;
    std::string sibling_trace_path;
    std::string row_delta_trace_path;
    std::string memory_trace_path;
    std::string mip_start_audit_path;
    DenseProgressStats dense_progress;
    std::string dense_progress_raw_event_path;
    bool dense_progress_read_only_contract = false;
    std::unordered_map<std::string, double> values;
};

TailoredBCCplexApiProbe probeTailoredBCCplexApi();

PlainCplexApiSolveResult solvePlainCplexWithStrictApi(
    const std::filesystem::path& lp_path,
    double time_limit_seconds,
    int threads,
    const std::filesystem::path& log_path = {},
    const DenseProgressConfig& dense_progress = {});

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
    int vector_route_cutset_max_size,
    int vector_route_cutset_max_cuts,
    double vector_route_cutset_min_violation,
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
    double progress_interval_seconds = 0.0,
    bool register_callbacks = true,
    const TailoredBCNativeCheckpointConfig& native_checkpoint = {});

GlobalGiniTreeApiSolveResult solveGlobalGiniTreeWithTailoredBCCplexApi(
    const std::filesystem::path& root_lp_path,
    const Instance& instance,
    const SolveOptions& options,
    double root_gamma_L,
    double root_gamma_U,
    double verified_incumbent,
    const std::vector<RoutePlan>& verified_routes,
    double time_limit_seconds,
    int threads,
    const std::filesystem::path& node_trace_path,
    const std::filesystem::path& bound_trace_path,
    const std::filesystem::path& manifest_path);

} // namespace ebrp
