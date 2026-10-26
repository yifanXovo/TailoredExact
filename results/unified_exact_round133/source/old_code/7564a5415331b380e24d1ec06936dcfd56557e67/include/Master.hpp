#pragma once

#include "Column.hpp"
#include "Instance.hpp"
#include "Result.hpp"

#include <chrono>
#include <vector>

namespace ebrp {

struct RestrictedMasterResult {
    bool complete = true;
    bool has_solution = false;
    long long states_processed = 0;
    ObjectiveParts best_parts;
    std::vector<int> best_final_inventory;
    std::vector<int> selected_column_by_vehicle;
    std::vector<RoutePlan> routes;
};

RestrictedMasterResult solveRestrictedMasterExact(
    const Instance& instance,
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    double lambda,
    double time_limit_seconds = 0.0,
    std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now());

} // namespace ebrp
