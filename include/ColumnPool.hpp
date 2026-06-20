#pragma once

#include "Column.hpp"

#include <string>
#include <vector>

namespace ebrp {

enum class ColumnDominanceMode {
    Off,
    Exact,
    Pareto
};

struct ColumnDominanceOptions {
    bool enabled = true;
    ColumnDominanceMode mode = ColumnDominanceMode::Exact;
    bool exact_safe = true;
};

struct ColumnDominanceStats {
    long long columns_generated_raw = 0;
    long long columns_after_dominance = 0;
    long long columns_dominated = 0;
    long long dominance_input_columns = 0;
    long long dominance_kept_columns = 0;
    long long dominance_removed_columns = 0;
    long long dominance_removed_existing_projection = 0;
    long long dominance_removed_candidate_projection = 0;
    double dominance_time_seconds = 0.0;
    std::string dominance_mode = "exact";
    bool dominance_exact_safe = true;
};

ColumnDominanceMode parseColumnDominanceMode(const std::string& value);
std::string columnDominanceModeName(ColumnDominanceMode mode);

std::string projectionKey(const RouteLoadColumn& column);

ColumnDominanceOptions normalizeColumnDominanceOptions(ColumnDominanceOptions options);

void applyColumnDominance(std::vector<RouteLoadColumn>& columns,
                          ColumnDominanceOptions options,
                          ColumnDominanceStats& stats);

std::vector<RouteLoadColumn> filterNewColumnsByDominance(
    const std::vector<RouteLoadColumn>& existing,
    std::vector<RouteLoadColumn> candidates,
    ColumnDominanceOptions options,
    ColumnDominanceStats& stats);

void mergeColumnDominanceStats(ColumnDominanceStats& total,
                               const ColumnDominanceStats& add);

} // namespace ebrp
