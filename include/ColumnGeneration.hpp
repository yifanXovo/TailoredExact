#pragma once

#include "Column.hpp"
#include "Instance.hpp"
#include "Pricing.hpp"
#include "Result.hpp"

#include <limits>
#include <string>
#include <vector>

namespace ebrp {

struct ColumnGenerationResult {
    bool complete = false;
    int iterations = 0;
    int required_i = 0;
    int required_j = 0;
    long long pricing_calls = 0;
    long long generated_columns = 0;
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
    std::string pricing_closure_status = "not_run";
    double pricing_remaining_negative_rc = 0.0;
    long long pricing_exact_verification_calls = 0;
    double pricing_exact_verification_time_seconds = 0.0;
    std::string bpc_pricing_engine_requested = "exact-label";
    std::string bpc_pricing_engine_used = "exact-label";
    long long bpc_pricing_engine_fallbacks = 0;
    long long bpc_nodes_using_ng_dssr = 0;
    long long bpc_nodes_using_exact_label = 0;
    long long bpc_nodes_using_hybrid = 0;
    long long bpc_nodes_exactly_priced = 0;
    long long bpc_nodes_dssr_incomplete = 0;
    long long bpc_nodes_final_verifier_called = 0;
    long long bpc_nodes_final_verifier_completed = 0;
    int ng_size = 0;
    std::string ng_neighborhood_mode = "nearest";
    long long ng_memory_total = 0;
    long long dssr_memory_total_initial = 0;
    long long dssr_memory_total_final = 0;
    int dssr_rounds = 0;
    long long dssr_memory_expansions = 0;
    long long dssr_repeated_station_events = 0;
    long long dssr_relaxed_negative_routes = 0;
    long long dssr_non_elementary_routes = 0;
    long long dssr_elementary_columns_found = 0;
    bool dssr_no_negative_relaxed_route = false;
    bool dssr_exact_closure_proved = false;
    double dssr_final_exact_verification_time = 0.0;
    double dssr_time_seconds = 0.0;
    std::string dssr_stop_reason;
    std::string cg_stabilization_mode = "none";
    long long cg_dual_center_updates = 0;
    double cg_dual_oscillation_metric = 0.0;
    long long cg_stabilized_pricing_calls = 0;
    long long cg_true_pricing_calls = 0;
    long long cg_stabilization_columns_found = 0;
    long long cg_true_pricing_columns_found = 0;
    long long cg_true_negative_columns_inserted = 0;
    long long cg_stabilization_false_negatives = 0;
    double cg_stabilization_time_seconds = 0.0;
    double cg_final_true_pricing_rc = 0.0;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
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
    std::string pricing_closure_status = "not_run";
    double pricing_remaining_negative_rc = 0.0;
    long long pricing_exact_verification_calls = 0;
    double pricing_exact_verification_time_seconds = 0.0;
    std::string bpc_pricing_engine_requested = "exact-label";
    std::string bpc_pricing_engine_used = "exact-label";
    long long bpc_pricing_engine_fallbacks = 0;
    long long bpc_nodes_using_ng_dssr = 0;
    long long bpc_nodes_using_exact_label = 0;
    long long bpc_nodes_using_hybrid = 0;
    long long bpc_nodes_exactly_priced = 0;
    long long bpc_nodes_dssr_incomplete = 0;
    long long bpc_nodes_final_verifier_called = 0;
    long long bpc_nodes_final_verifier_completed = 0;
    int ng_size = 0;
    std::string ng_neighborhood_mode = "nearest";
    long long ng_memory_total = 0;
    long long dssr_memory_total_initial = 0;
    long long dssr_memory_total_final = 0;
    int dssr_rounds = 0;
    long long dssr_memory_expansions = 0;
    long long dssr_repeated_station_events = 0;
    long long dssr_relaxed_negative_routes = 0;
    long long dssr_non_elementary_routes = 0;
    long long dssr_elementary_columns_found = 0;
    bool dssr_no_negative_relaxed_route = false;
    bool dssr_exact_closure_proved = false;
    double dssr_final_exact_verification_time = 0.0;
    double dssr_time_seconds = 0.0;
    std::string dssr_stop_reason;
    std::string cg_stabilization_mode = "none";
    long long cg_dual_center_updates = 0;
    double cg_dual_oscillation_metric = 0.0;
    long long cg_stabilized_pricing_calls = 0;
    long long cg_true_pricing_calls = 0;
    long long cg_stabilization_columns_found = 0;
    long long cg_true_pricing_columns_found = 0;
    long long cg_true_negative_columns_inserted = 0;
    long long cg_stabilization_false_negatives = 0;
    double cg_stabilization_time_seconds = 0.0;
    double cg_final_true_pricing_rc = 0.0;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
    long long route_states = 0;
    long long operation_states = 0;
    long long cuts_added = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    long long projection_bound_prunes = 0;
    double projection_bound_time_seconds = 0.0;
    double projection_bound_best_value = 0.0;
    std::string projection_bound_scope = "global";
    double penalty_budget = 0.0;
    long long domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    double penalty_tightening_time_seconds = 0.0;
    long long movement_domains_tightened_count = 0;
    long long movement_domain_width_before = 0;
    long long movement_domain_width_after = 0;
    double movement_tightening_time_seconds = 0.0;
    long long movement_unreachable_station_count = 0;
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
    std::string pricing_closure_status = "not_run";
    double pricing_remaining_negative_rc = 0.0;
    long long pricing_exact_verification_calls = 0;
    double pricing_exact_verification_time_seconds = 0.0;
    std::string bpc_pricing_engine_requested = "exact-label";
    std::string bpc_pricing_engine_used = "exact-label";
    long long bpc_pricing_engine_fallbacks = 0;
    long long bpc_nodes_using_ng_dssr = 0;
    long long bpc_nodes_using_exact_label = 0;
    long long bpc_nodes_using_hybrid = 0;
    long long bpc_nodes_exactly_priced = 0;
    long long bpc_nodes_dssr_incomplete = 0;
    long long bpc_nodes_final_verifier_called = 0;
    long long bpc_nodes_final_verifier_completed = 0;
    int ng_size = 0;
    std::string ng_neighborhood_mode = "nearest";
    long long ng_memory_total = 0;
    long long dssr_memory_total_initial = 0;
    long long dssr_memory_total_final = 0;
    int dssr_rounds = 0;
    long long dssr_memory_expansions = 0;
    long long dssr_repeated_station_events = 0;
    long long dssr_relaxed_negative_routes = 0;
    long long dssr_non_elementary_routes = 0;
    long long dssr_elementary_columns_found = 0;
    bool dssr_no_negative_relaxed_route = false;
    bool dssr_exact_closure_proved = false;
    double dssr_final_exact_verification_time = 0.0;
    double dssr_time_seconds = 0.0;
    std::string dssr_stop_reason;
    std::string cg_stabilization_mode = "none";
    long long cg_dual_center_updates = 0;
    double cg_dual_oscillation_metric = 0.0;
    long long cg_stabilized_pricing_calls = 0;
    long long cg_true_pricing_calls = 0;
    long long cg_stabilization_columns_found = 0;
    long long cg_true_pricing_columns_found = 0;
    long long cg_true_negative_columns_inserted = 0;
    long long cg_stabilization_false_negatives = 0;
    double cg_stabilization_time_seconds = 0.0;
    double cg_final_true_pricing_rc = 0.0;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
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
    std::string pricing_closure_status = "not_run";
    double pricing_remaining_negative_rc = 0.0;
    long long pricing_exact_verification_calls = 0;
    double pricing_exact_verification_time_seconds = 0.0;
    std::string bpc_pricing_engine_requested = "exact-label";
    std::string bpc_pricing_engine_used = "exact-label";
    long long bpc_pricing_engine_fallbacks = 0;
    long long bpc_nodes_using_ng_dssr = 0;
    long long bpc_nodes_using_exact_label = 0;
    long long bpc_nodes_using_hybrid = 0;
    long long bpc_nodes_exactly_priced = 0;
    long long bpc_nodes_dssr_incomplete = 0;
    long long bpc_nodes_final_verifier_called = 0;
    long long bpc_nodes_final_verifier_completed = 0;
    int ng_size = 0;
    std::string ng_neighborhood_mode = "nearest";
    long long ng_memory_total = 0;
    long long dssr_memory_total_initial = 0;
    long long dssr_memory_total_final = 0;
    int dssr_rounds = 0;
    long long dssr_memory_expansions = 0;
    long long dssr_repeated_station_events = 0;
    long long dssr_relaxed_negative_routes = 0;
    long long dssr_non_elementary_routes = 0;
    long long dssr_elementary_columns_found = 0;
    bool dssr_no_negative_relaxed_route = false;
    bool dssr_exact_closure_proved = false;
    double dssr_final_exact_verification_time = 0.0;
    double dssr_time_seconds = 0.0;
    std::string dssr_stop_reason;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
    long long route_states = 0;
    long long operation_states = 0;
    long long cuts_added = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    long long projection_bound_prunes = 0;
    double projection_bound_time_seconds = 0.0;
    double projection_bound_best_value = 0.0;
    std::string projection_bound_scope = "global";
    double penalty_budget = 0.0;
    long long domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    double penalty_tightening_time_seconds = 0.0;
    long long movement_domains_tightened_count = 0;
    long long movement_domain_width_before = 0;
    long long movement_domain_width_after = 0;
    double movement_tightening_time_seconds = 0.0;
    long long movement_unreachable_station_count = 0;
    double gamma = 0.0;
    double gamma_floor = -1.0;
    double resource_penalty_lower_bound = 0.0;
    double resource_objective_lower_bound = 0.0;
    int resource_total_pickup_limit = 0;
    long long inventory_branch_candidates = 0;
    long long inventory_branch_nodes_created = 0;
    int inventory_branch_station = 0;
    double inventory_branch_value = 0.0;
    int inventory_branch_left_bound = 0;
    int inventory_branch_right_bound = 0;
    long long inventory_branch_pruned_nodes = 0;
    int inventory_branch_max_depth = 0;
    long long operation_mode_branch_candidates = 0;
    long long operation_mode_branch_nodes_created = 0;
    int operation_mode_branch_station = 0;
    std::string operation_mode_branch_type;
    long long operation_mode_branch_pruned_columns = 0;
    long long operation_mode_branch_pruned_labels = 0;
    std::string branch_selection_mode = "auto";
    long long strong_branching_calls = 0;
    long long strong_branching_candidates_tested = 0;
    double strong_branching_time_seconds = 0.0;
    std::string selected_branch_type;
    double selected_branch_score = 0.0;
    double selected_branch_child_lb_left = 0.0;
    double selected_branch_child_lb_right = 0.0;
    long long branch_nodes_by_type_ryan_foster = 0;
    long long branch_nodes_by_type_inventory = 0;
    long long branch_nodes_by_type_operation_mode = 0;
    std::string closure_mode = "auto";
    int closure_cg_iterations = 0;
    long long closure_columns_added = 0;
    long long closure_pricing_calls = 0;
    bool closure_final_exact_pricing_run = false;
    double closure_final_best_reduced_cost = 0.0;
    bool closure_pricing_closed = false;
    double closure_time_seconds = 0.0;
    std::string closure_stop_reason;
    std::string cg_stabilization_mode = "none";
    long long cg_stabilized_pricing_calls = 0;
    long long cg_true_pricing_calls = 0;
    long long cg_stabilization_columns_found = 0;
    long long cg_true_pricing_columns_found = 0;
    long long cg_dual_center_updates = 0;
    double cg_dual_oscillation_metric = 0.0;
    long long cg_true_negative_columns_inserted = 0;
    long long cg_stabilization_false_negatives = 0;
    double cg_stabilization_time_seconds = 0.0;
    double cg_final_true_pricing_rc = 0.0;
    bool has_integer_incumbent = false;
    double global_lower_bound = 0.0;
    double best_integer_surrogate = 0.0;
    int best_integer_columns = 0;
    std::string incumbent_source;
    ObjectiveParts best_integer_parts;
    std::vector<int> best_final_inventory;
    std::vector<RoutePlan> best_routes;
    std::vector<std::vector<RouteLoadColumn>> columns_by_vehicle;
    std::vector<RouteLoadColumn> flat_columns;
    std::vector<RouteLoadColumn> priced_columns_added;
    std::vector<RouteLoadColumn> warm_start_columns;
    std::vector<RouteLoadColumn> integer_leaf_columns;
    long long columns_exported_from_tree = 0;
    long long columns_exported_from_pricing = 0;
    long long columns_exported_from_warmstart = 0;
    long long columns_exported_from_integer_leaves = 0;
    std::vector<std::string> notes;
};

ColumnGenerationResult runCoverageColumnGenerationDiagnostic(
    const Instance& instance,
    double time_limit_seconds,
    int max_iterations = 8,
    const PricingOptions& pricing_options = PricingOptions{});

GiniCapColumnGenerationResult runGiniCapColumnGenerationDiagnostic(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations = 12,
    bool support_duration_pruning_enabled = true,
    int support_duration_max_subset_size = 5,
    const PricingOptions& pricing_options = PricingOptions{});

GiniCapBranchProbeResult runGiniCapRyanFosterBranchProbe(
    const Instance& instance,
    double lambda,
    double gamma,
    double time_limit_seconds,
    int max_iterations = 12,
    bool support_duration_pruning_enabled = true,
    int support_duration_max_subset_size = 5,
    const PricingOptions& pricing_options = PricingOptions{});

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
    int pricing_return_columns = 1,
    bool column_dominance_enabled = true,
    const std::string& column_dominance_mode = "exact",
    bool projection_bound_enabled = true,
    bool penalty_domain_tightening_enabled = true,
    bool movement_domain_tightening_enabled = true,
    bool support_duration_pruning_enabled = true,
    int support_duration_max_subset_size = 5,
    bool branch_inventory_enabled = true,
    double branch_inventory_priority = 1.0,
    bool branch_operation_mode_enabled = true,
    const std::string& branch_selection_mode = "auto",
    int strong_branching_candidates = 3,
    double strong_branching_time_seconds = 0.0,
    bool reliability_branching_enabled = false,
    const PricingOptions& pricing_options = PricingOptions{});

} // namespace ebrp
