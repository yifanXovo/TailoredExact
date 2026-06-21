#pragma once

#include "Instance.hpp"

#include <limits>
#include <string>
#include <vector>

namespace ebrp {

struct ResourceRelaxationBound {
    bool computed = false;
    int total_pickup_limit = 0;
    long long states_processed = 0;
    double penalty_lower_bound = 0.0;
    double objective_lower_bound = 0.0;
    std::string note;
};

struct GiniIntervalInventoryRelaxationBound {
    bool computed = false;
    bool infeasible = false;
    int total_pickup_limit = 0;
    double objective_lower_bound = 0.0;
    double gini_lower_bound = 0.0;
    double lambda_penalty_lower_bound = 0.0;
    double projection_objective_lower_bound = 0.0;
    double projection_penalty_lower_bound = 0.0;
    double projection_gini_lower_bound = 0.0;
    double projection_h_lower_bound = 0.0;
    double projection_s_upper_bound = 0.0;
    bool projection_bound_valid = false;
    bool projection_bound_fathomed = false;
    double projection_bound_time_seconds = 0.0;
    std::string projection_bound_scope = "global";
    double penalty_budget = 0.0;
    int domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    bool penalty_budget_fathomed = false;
    double penalty_tightening_time_seconds = 0.0;
    int movement_domains_tightened_count = 0;
    long long movement_domain_width_before = 0;
    long long movement_domain_width_after = 0;
    double movement_tightening_time_seconds = 0.0;
    int movement_unreachable_station_count = 0;
    long long route_mask_count_before_support_duration = 0;
    long long route_mask_count_after_support_duration = 0;
    long long route_masks_removed_by_support_duration = 0;
    double route_mask_support_duration_precompute_time_seconds = 0.0;
    int route_mask_support_duration_max_removed_subset_size = 0;
    bool route_mask_support_duration_pruning = false;
    std::vector<std::string> route_mask_support_duration_removed_examples;
    long long route_mask_operation_budget_cuts_added = 0;
    double route_mask_operation_budget_min = 0.0;
    double route_mask_operation_budget_avg = 0.0;
    double route_mask_operation_budget_max = 0.0;
    long long route_mask_operation_budget_tightened_masks = 0;
    long long route_mask_operation_budget_zero_masks = 0;
    double route_mask_operation_budget_precompute_time_seconds = 0.0;
    std::vector<std::string> route_mask_operation_budget_examples;
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
    bool pickup_drop_compat_flow_enabled = false;
    std::vector<std::string> pickup_drop_incompatible_examples;
    std::string status;
    std::string note;
};

struct InventoryRatioProjectionBound {
    bool valid = false;
    double P_lower_bound = 0.0;
    double H_lower_bound = 0.0;
    double S_upper_bound = 0.0;
    double G_lower_bound = 0.0;
    double objective_lower_bound = 0.0;
    std::string bound_scope = "global";
    std::vector<std::string> warnings;
};

struct PenaltyDomainTighteningResult {
    bool valid = false;
    bool fathomed_by_budget = false;
    double penalty_budget = 0.0;
    int domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    std::vector<std::string> warnings;
};

struct MovementReachabilityTighteningResult {
    bool valid = false;
    int domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    int unreachable_station_count = 0;
    double time_seconds = 0.0;
    std::vector<std::string> warnings;
};

ResourceRelaxationBound computeResourceRelaxationBound(const Instance& instance,
                                                       double lambda);

GiniIntervalInventoryRelaxationBound computeGiniIntervalInventoryRelaxationBound(
    const Instance& instance,
    double lambda,
    double gamma_floor,
    double gamma_cap,
    double time_limit_seconds = 5.0,
    double objective_cutoff = std::numeric_limits<double>::infinity(),
    int route_mask_max_v = 12,
    bool projection_bound_enabled = true,
    bool penalty_domain_tightening_enabled = true,
    bool movement_domain_tightening_enabled = true,
    bool route_mask_support_duration_pruning_enabled = true,
    bool pickup_drop_compat_flow_enabled = true,
    bool pickup_drop_transfer_cap_flow_enabled = true,
    bool route_mask_operation_budget_cuts_enabled = true);

InventoryRatioProjectionBound computeInventoryRatioProjectionBound(
    const Instance& instance,
    double lambda,
    const std::vector<int>& lower_inventory,
    const std::vector<int>& upper_inventory,
    double gamma_floor = -std::numeric_limits<double>::infinity(),
    const std::string& bound_scope = "global");

PenaltyDomainTighteningResult tightenInventoryIntervalsByPenaltyBudget(
    const Instance& instance,
    double lambda,
    double gamma_floor,
    double objective_cutoff,
    std::vector<int>& lower_inventory,
    std::vector<int>& upper_inventory);

MovementReachabilityTighteningResult tightenInventoryIntervalsByMovementReachability(
    const Instance& instance,
    std::vector<int>& lower_inventory,
    std::vector<int>& upper_inventory);

} // namespace ebrp
