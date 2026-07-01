#pragma once

#include "Column.hpp"
#include "Instance.hpp"

#include <array>
#include <chrono>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace ebrp {

struct PricingDuals {
    double constant = 0.0;
    std::vector<double> visit_cost;      // index 1..V, added once if station is visited
    std::vector<double> operation_cost;  // index 1..V, multiplied by q_i
    std::vector<std::pair<std::pair<int, int>, double>> pair_cost; // added if both stations are in the column
    std::vector<std::pair<std::vector<int>, double>> subset_row_cost; // coefficient floor(|column intersect S|/2)
    double travel_cost = 0.0;
    double pickup_cost = 0.0;
};

struct PricingOptions {
    double time_limit_seconds = 0.0;     // <=0 means no pricing time limit
    double negative_tolerance = 1e-9;
    int allowed_station_mask = 0;        // 0 means all stations allowed; otherwise station bitmask
    int forbidden_station_mask = 0;
    int forbid_pickup_station_mask = 0;
    int forbid_drop_station_mask = 0;
    std::vector<std::pair<int, int>> forbid_together_pairs;  // child branch sum containing both = 0
    std::vector<std::pair<int, int>> require_together_pairs; // columns may contain both or neither, not exactly one
    double stop_reduced_cost = -std::numeric_limits<double>::infinity();
    int max_returned_columns = 1;
    bool use_completion_lb_pruning = false;
    bool support_duration_pruning = true;
    int support_duration_max_subset_size = 5;
    std::string pricing_dominance_mode = "safe";
    std::string pricing_completion_bound = "basic";
    bool pricing_completion_bound_audit = false;
    std::string pricing_decomposition = "auto";
    bool pricing_load_dp_cache = false;
    std::string pricing_route_skeleton_mode = "standard";
    bool pricing_route_skeleton_cache = false;
    bool pricing_load_dp_dominance = true;
    bool pricing_operation_dp_dominance = true;
    std::string pricing_engine = "exact-label";
    int ng_size = 12;
    std::string ng_neighborhood_mode = "nearest";
    int dssr_max_rounds = 4;
    int dssr_expand_per_round = 4;
    double dssr_time_limit = 30.0;
    bool dssr_final_exact = true;
    std::string cg_dual_stabilization = "none";
    double cg_dual_smoothing_alpha = 0.7;
    double cg_dual_box_radius = 1.0;
    std::string column_tracks = "elementary-only";
    bool relaxed_columns_in_rmp = false;
    int relaxed_columns_max_per_pricing = 8;
    std::string rmp_column_space = "elementary";
    bool allow_non_elementary_relaxed_columns = true;
    bool relaxed_projection_strict = true;
    bool ng_relaxed_closure = false;
    double ng_relaxed_closure_time = 30.0;
    long long ng_relaxed_max_labels = 0;
    std::string ng_relaxed_pricing_checkpoint;
    std::string ng_relaxed_pricing_resume;
    bool relaxed_rmp_cg = false;
    int relaxed_rmp_cg_columns_per_iteration = 8;
    bool dssr_close_relaxed_pricing = false;
    double dssr_relaxed_closure_time = 30.0;
    long long dssr_relaxed_closure_max_labels = 0;
    std::string dssr_relaxed_closure_checkpoint;
};

struct PricingResult {
    bool complete = true;
    bool stopped_early_with_column = false;
    bool has_column = false;
    bool has_negative_column = false;
    long long route_states = 0;
    long long operation_states = 0;
    long long generated_columns = 0;
    long long support_duration_cuts_generated = 0;
    long long support_duration_pruned_labels = 0;
    long long support_duration_pruned_columns = 0;
    std::string support_duration_min_pickup_rule = "ceil_half_support";
    long long support_duration_strong_cuts_generated = 0;
    long long support_duration_strong_pruned_labels = 0;
    long long support_duration_strong_pruned_columns = 0;
    long long completion_lb_pruned_labels = 0;
    long long required_closure_pruned_labels = 0;
    long long label_dominance_comparisons = 0;
    long long label_dominance_pruned_labels = 0;
    long long label_dominance_cross_pickup_pruned_labels = 0;
    long long label_dominance_inactive_entries_skipped = 0;
    long long label_dominance_bucket_compactions = 0;
    long long label_dominance_compacted_entries = 0;
    long long operation_dp_dominance_pruned_states = 0;
    std::string pricing_dominance_mode = "safe";
    bool pricing_dominance_exact_safe = true;
    std::string pricing_completion_bound = "basic";
    bool pricing_completion_bound_audit = false;
    std::string pricing_decomposition = "auto";
    bool pricing_load_dp_cache = false;
    std::string pricing_route_skeleton_mode = "standard";
    bool pricing_route_skeleton_cache = false;
    bool pricing_load_dp_dominance = true;
    bool pricing_operation_dp_dominance = true;
    long long pricing_labels_generated = 0;
    long long pricing_labels_kept = 0;
    long long pricing_labels_expanded = 0;
    long long pricing_labels_pruned_duration = 0;
    long long pricing_labels_pruned_load = 0;
    long long pricing_labels_pruned_station = 0;
    long long pricing_labels_pruned_support = 0;
    long long pricing_labels_pruned_reduced_cost = 0;
    long long pricing_labels_pruned_dominance = 0;
    long long pricing_labels_duplicate_states = 0;
    std::string pricing_state_stop_reason;
    std::string pricing_depth_profile_json = "[]";
    std::string operation_dp_profile_json = "[]";
    int support_duration_max_subset_size = 0;
    double support_duration_precompute_time_seconds = 0.0;
    double best_reduced_cost = 0.0;
    double best_new_reduced_cost = std::numeric_limits<double>::infinity();
    long long negative_existing_projection_count = 0;
    long long negative_new_projection_count = 0;
    bool blocked_by_duplicate_projection = false;
    std::string pricing_closure_status = "not_run";
    RouteLoadColumn best_column;
    std::vector<RouteLoadColumn> negative_columns;
    std::vector<RouteLoadColumn> relaxed_negative_columns;
    std::string column_tracks = "elementary-only";
    std::string rmp_column_space = "elementary";
    long long elementary_columns_generated = 0;
    long long elementary_columns_inserted = 0;
    long long relaxed_columns_generated = 0;
    long long relaxed_columns_inserted = 0;
    long long relaxed_columns_rejected_projection = 0;
    long long relaxed_columns_rejected_infeasible_projection = 0;
    long long relaxed_columns_used_in_lb_rmp = 0;
    long long relaxed_columns_used_in_incumbent = 0;
    long long non_elementary_relaxed_routes_seen = 0;
    long long non_elementary_relaxed_columns_validated = 0;
    long long non_elementary_relaxed_columns_inserted = 0;
    long long non_elementary_relaxed_columns_rejected = 0;
    long long relaxed_projection_rejected_load = 0;
    long long relaxed_projection_rejected_station_capacity = 0;
    long long relaxed_projection_rejected_branch = 0;
    long long relaxed_projection_rejected_operation_mode = 0;
    long long relaxed_projection_rejected_unsafe_cut = 0;
    double relaxed_projection_validation_time_seconds = 0.0;
    long long relaxed_columns_blocked_from_incumbent = 0;
    long long relaxed_columns_blocked_from_export = 0;
    long long relaxed_columns_blocked_from_candidate_reconstruction = 0;
    bool relaxed_rmp_enabled = false;
    bool elementary_pricing_closed = false;
    bool ng_relaxed_pricing_closed = false;
    bool dssr_exact_elementary_closed = false;
    long long ng_relaxed_pricing_calls = 0;
    double ng_relaxed_best_reduced_cost = 0.0;
    long long ng_relaxed_negative_routes_found = 0;
    long long ng_relaxed_negative_columns_inserted = 0;
    long long ng_relaxed_negative_routes_rejected = 0;
    long long ng_relaxed_closure_labels_processed = 0;
    long long ng_relaxed_closure_labels_pruned = 0;
    double ng_relaxed_closure_time_seconds = 0.0;
    std::string ng_relaxed_closure_stop_reason;
    long long ng_relaxed_labels_processed = 0;
    long long ng_relaxed_labels_pruned = 0;
    int dssr_refinement_rounds_for_lb = 0;
    double dssr_lb_before_refinement = 0.0;
    double dssr_lb_after_refinement = 0.0;
    std::string pricing_engine = "exact-label";
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
    bool dssr_final_exact = false;
    bool dssr_exact_closure_proved = false;
    double dssr_final_exact_verification_time = 0.0;
    double dssr_time_seconds = 0.0;
    std::string dssr_stop_reason;
    long long cg_stabilized_pricing_calls = 0;
    long long cg_true_pricing_calls = 0;
    long long cg_stabilization_columns_found = 0;
    long long cg_true_pricing_columns_found = 0;
    long long cg_dual_center_updates = 0;
    double cg_dual_oscillation_metric = 0.0;
    long long cg_true_negative_columns_inserted = 0;
    long long cg_stabilization_false_negatives = 0;
    double cg_final_true_pricing_rc = 0.0;
    double cg_stabilization_time_seconds = 0.0;
};

PricingResult priceRouteLoadColumnExact(
    const Instance& instance,
    int vehicle,
    const PricingDuals& duals,
    const PricingOptions& options,
    std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now());

} // namespace ebrp
