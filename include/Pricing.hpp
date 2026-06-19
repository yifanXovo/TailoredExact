#pragma once

#include "Column.hpp"
#include "Instance.hpp"

#include <array>
#include <chrono>
#include <limits>
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
    std::vector<std::pair<int, int>> forbid_together_pairs;  // child branch sum containing both = 0
    std::vector<std::pair<int, int>> require_together_pairs; // columns may contain both or neither, not exactly one
    double stop_reduced_cost = -std::numeric_limits<double>::infinity();
    int max_returned_columns = 1;
    bool use_completion_lb_pruning = false;
};

struct PricingResult {
    bool complete = true;
    bool stopped_early_with_column = false;
    bool has_column = false;
    bool has_negative_column = false;
    long long route_states = 0;
    long long operation_states = 0;
    long long generated_columns = 0;
    double best_reduced_cost = 0.0;
    RouteLoadColumn best_column;
    std::vector<RouteLoadColumn> negative_columns;
};

PricingResult priceRouteLoadColumnExact(
    const Instance& instance,
    int vehicle,
    const PricingDuals& duals,
    const PricingOptions& options,
    std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now());

} // namespace ebrp
