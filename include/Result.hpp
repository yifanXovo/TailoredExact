#pragma once

#include "Instance.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct StopOperation {
    int station = 0;
    int pickup = 0;
    int drop = 0;
};

struct RoutePlan {
    int vehicle = 0;
    std::vector<int> nodes;             // includes depot at start and end
    std::vector<StopOperation> operations;
};

struct Verification {
    bool feasible = false;
    bool routes_start_end_depot = false;
    bool station_disjoint = false;
    bool load_feasible = false;
    bool station_feasible = false;
    bool duration_feasible = false;
    bool objective_matches = false;
    std::vector<double> route_travel_time;
    std::vector<double> route_operation_time;
    std::vector<double> route_duration;
    std::vector<int> final_inventory;
    double G = 0.0;
    double P = 0.0;
    double objective = 0.0;
    std::vector<std::string> errors;
};

struct SolveResult {
    std::string instance_name;
    std::string input_path;
    std::string result_file;
    std::string log_file;
    std::string method;
    std::string status;
    std::string certificate;
    double objective = 0.0;
    double G = 0.0;
    double P = 0.0;
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double gap = 0.0;
    double runtime_seconds = 0.0;
    double wall_time_seconds = 0.0;
    double aggregate_worker_time_seconds = 0.0;
    long long nodes = 0;
    long long columns = 0;
    long long pricing_calls = 0;
    long long cuts_added = 0;
    long long pricing_closed_nodes = 0;
    long long open_nodes = 0;
    int unresolved_intervals = 0;
    int invalid_bound_intervals = 0;
    int bpc_workers = 1;
    int pricing_threads = 1;
    bool parallel_frontier = false;
    bool parallel_nodes = false;
    long long parallel_tasks = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    double bound_time_seconds = 0.0;
    double route_mask_time_seconds = 0.0;
    double gini_max_possible = 0.0;
    double relevant_gini_upper_for_improvement = 0.0;
    double covered_gini_upper_bound = 0.0;
    bool frontier_covers_all_improving_gini_values = false;
    std::string frontier_range_certificate_scope = "not_frontier";
    long long columns_generated_raw = 0;
    long long columns_after_dominance = 0;
    long long columns_dominated = 0;
    long long pricing_columns_enumerated = 0;
    long long dominance_input_columns = 0;
    long long dominance_kept_columns = 0;
    long long dominance_removed_columns = 0;
    long long dominance_removed_existing_projection = 0;
    long long dominance_removed_candidate_projection = 0;
    long long rmp_columns_inserted = 0;
    long long rmp_columns_active = 0;
    double dominance_time_seconds = 0.0;
    std::string dominance_mode = "exact";
    bool dominance_exact_safe = true;
    long long projection_bound_prunes = 0;
    double projection_bound_time_seconds = 0.0;
    double projection_bound_best_value = 0.0;
    std::string projection_bound_scope = "global";
    double penalty_budget = 0.0;
    long long domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    double penalty_tightening_time_seconds = 0.0;
    long long pricing_negative_columns_found = 0;
    long long pricing_negative_columns_inserted = 0;
    long long pricing_negative_columns_dominated = 0;
    bool pricing_completed_exactly = true;
    double pricing_best_reduced_cost_any = 0.0;
    double pricing_best_new_reduced_cost = 0.0;
    long long pricing_duplicate_negative_projections = 0;
    long long pricing_new_negative_projections = 0;
    bool pricing_blocked_by_duplicate_projection = false;
    bool pricing_closure_certified_exact = true;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    std::string support_duration_min_pickup_rule = "ceil_half_support";
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
    long long route_mask_count_before_support_duration = 0;
    long long route_mask_count_after_support_duration = 0;
    long long route_masks_removed_by_support_duration = 0;
    double route_mask_support_duration_precompute_time_seconds = 0.0;
    int route_mask_support_duration_max_removed_subset_size = 0;
    bool route_mask_support_duration_pruning = true;
    long long movement_domains_tightened_count = 0;
    long long movement_domain_width_before = 0;
    long long movement_domain_width_after = 0;
    double movement_tightening_time_seconds = 0.0;
    long long movement_unreachable_station_count = 0;
    double relaxation_lb_no_movement = 0.0;
    double relaxation_lb_with_movement = 0.0;
    double relaxation_lb_used = 0.0;
    bool movement_audit_enabled = false;
    long long movement_audit_intervals = 0;
    long long movement_audit_bound_improved_count = 0;
    long long movement_audit_bound_worse_count = 0;
    int frontier_relevant_intervals = 0;
    double frontier_min_interval_lower_bound = 0.0;
    std::string frontier_lower_bound_source;
    int frontier_unprocessed_interval_count = 0;
    int frontier_bound_fathomed_interval_count = 0;
    int frontier_tree_closed_interval_count = 0;
    std::string frontier_scheduling_mode;
    long long frontier_relax_cache_hits = 0;
    long long frontier_relax_cache_misses = 0;
    long long frontier_relax_cache_partial_hits = 0;
    long long frontier_relax_cache_recomputed = 0;
    long long frontier_relax_cache_best_bound_reused = 0;
    double frontier_relax_cache_time_saved_estimate = 0.0;
    std::string interval_processing_order;
    bool cheap_prepass_enabled = false;
    std::string interval_processing_order_initial;
    std::string interval_processing_order_actual;
    long long interval_priority_rebuild_count = 0;
    long long intervals_skipped_by_cheap_bound = 0;
    long long frontier_cache_hits = 0;
    long long frontier_cache_columns_loaded = 0;
    long long frontier_cache_columns_inserted = 0;
    double frontier_cache_time_seconds = 0.0;
    std::string incumbent_source;
    std::string incumbent_source_detail;
    bool incumbent_import_attempted = false;
    bool incumbent_import_verified = false;
    double incumbent_import_objective = 0.0;
    double incumbent_import_G = 0.0;
    double incumbent_import_P = 0.0;
    double incumbent_generation_time_seconds = 0.0;
    std::string incumbent_generation_method;
    long long incumbent_candidates_tested = 0;
    long long incumbent_candidates_verified = 0;
    long long incumbent_candidates_rejected = 0;
    std::string incumbent_best_source;
    double incumbent_best_objective = 0.0;
    double incumbent_best_G = 0.0;
    double incumbent_best_P = 0.0;
    double incumbent_best_runtime = 0.0;
    std::string incumbent_selection_reason;
    std::vector<std::string> incumbent_import_errors;
    bool focused_retry_enabled = false;
    int focused_retry_attempts = 0;
    int focused_retry_intervals = 0;
    std::string focused_retry_selected_interval_ids;
    std::string focused_retry_lb_before;
    std::string focused_retry_lb_after;
    int focused_retry_lb_improvements = 0;
    std::string focused_retry_open_nodes_before;
    std::string focused_retry_open_nodes_after;
    double focused_retry_seconds = 0.0;
    std::string focused_retry_stopped_reason;
    long long route_pool_columns_raw = 0;
    long long route_pool_columns_after_dominance = 0;
    long long route_pool_columns_removed_by_dominance = 0;
    long long route_pool_columns_exported_from_tree = 0;
    long long route_pool_columns_exported_from_pricing = 0;
    long long route_pool_columns_exported_from_warmstart = 0;
    long long route_pool_columns_exported_from_integer_leaves = 0;
    long long route_pool_columns_dropped_by_cap = 0;
    long long route_pool_incumbent_master_calls = 0;
    long long route_pool_incumbent_master_states = 0;
    double route_pool_incumbent_master_time_seconds = 0.0;
    bool route_pool_incumbent_found = false;
    double route_pool_incumbent_objective = 0.0;
    double route_pool_incumbent_G = 0.0;
    double route_pool_incumbent_P = 0.0;
    bool route_pool_incumbent_verified = false;
    std::string route_pool_incumbent_source;
    long long interval_candidates_found = 0;
    long long interval_candidates_verified = 0;
    long long interval_candidates_accepted = 0;
    long long interval_candidates_rejected = 0;
    double best_interval_candidate_objective = 0.0;
    std::string best_interval_candidate_rejection_reason;
    bool focused_intensification_enabled = false;
    int focused_intensification_passes = 0;
    int focused_intensification_intervals = 0;
    int focused_intensification_relax_calls = 0;
    int focused_intensification_tree_calls = 0;
    std::string focused_intensification_lb_before;
    std::string focused_intensification_lb_after;
    int focused_intensification_lb_improvements = 0;
    double focused_intensification_time_seconds = 0.0;
    std::string focused_intensification_stop_reason;
    long long pickup_drop_pairs_total = 0;
    long long pickup_drop_pairs_compatible = 0;
    long long pickup_drop_pairs_incompatible = 0;
    long long pickup_drop_pairs_capacity_limited = 0;
    double pickup_drop_transfer_cap_min = 0.0;
    double pickup_drop_transfer_cap_avg = 0.0;
    double pickup_drop_transfer_cap_max = 0.0;
    long long pickup_drop_transfer_cap_variables = 0;
    long long pickup_drop_transfer_cap_constraints = 0;
    double pickup_drop_transfer_cap_time_seconds = 0.0;
    long long pickup_drop_compat_flow_variables = 0;
    long long pickup_drop_compat_flow_constraints = 0;
    double pickup_drop_compat_flow_time_seconds = 0.0;
    std::string progress_log_path;
    std::vector<RoutePlan> routes;
    std::vector<int> final_inventory;
    Verification verification;
    std::vector<std::string> notes;
};

struct ObjectiveParts {
    double G = 0.0;
    double P = 0.0;
    double objective = 0.0;
    double S = 0.0;
    double H = 0.0;
};

ObjectiveParts computeObjectiveParts(const Instance& instance,
                                     const std::vector<int>& final_inventory,
                                     double lambda);

std::string resultToJson(const SolveResult& result);
std::string resultsToJson(const std::vector<SolveResult>& results);
void writeTextFile(const std::string& path, const std::string& text);

std::string inferMethodScope(const SolveResult& result);
bool inferSolvesOriginalObjective(const SolveResult& result);
bool inferIsBpc(const SolveResult& result);
std::string inferCertificateType(const SolveResult& result);
std::string inferStopReason(const SolveResult& result);
bool inferVerifierPassed(const SolveResult& result);
bool inferCertifiedOriginalProblem(const SolveResult& result);

} // namespace ebrp
