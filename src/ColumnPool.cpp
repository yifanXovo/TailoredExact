#include "ColumnPool.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <sstream>
#include <unordered_map>
#include <utility>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

bool pathLexLess(const std::vector<int>& lhs, const std::vector<int>& rhs) {
    return std::lexicographical_compare(lhs.begin(), lhs.end(), rhs.begin(), rhs.end());
}

bool exactRepresentativeBetter(const RouteLoadColumn& candidate,
                               const RouteLoadColumn& incumbent) {
    if (candidate.duration < incumbent.duration - 1e-12) return true;
    if (candidate.duration > incumbent.duration + 1e-12) return false;
    if (candidate.travel < incumbent.travel - 1e-12) return true;
    if (candidate.travel > incumbent.travel + 1e-12) return false;
    return pathLexLess(candidate.path, incumbent.path);
}

bool paretoDominates(const RouteLoadColumn& lhs, const RouteLoadColumn& rhs) {
    const bool le_duration = lhs.duration <= rhs.duration + 1e-12;
    const bool le_travel = lhs.travel <= rhs.travel + 1e-12;
    const bool le_reduced = lhs.reduced_cost <= rhs.reduced_cost + 1e-12;
    const bool strict = lhs.duration < rhs.duration - 1e-12 ||
                        lhs.travel < rhs.travel - 1e-12 ||
                        lhs.reduced_cost < rhs.reduced_cost - 1e-12;
    return le_duration && le_travel && le_reduced && strict;
}

bool samePathDependentValues(const RouteLoadColumn& lhs, const RouteLoadColumn& rhs) {
    return std::fabs(lhs.duration - rhs.duration) <= 1e-12 &&
           std::fabs(lhs.travel - rhs.travel) <= 1e-12 &&
           std::fabs(lhs.reduced_cost - rhs.reduced_cost) <= 1e-12;
}

} // namespace

ColumnDominanceMode parseColumnDominanceMode(const std::string& value) {
    std::string lower = value;
    std::transform(lower.begin(), lower.end(), lower.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (lower == "off" || lower == "false" || lower == "none") {
        return ColumnDominanceMode::Off;
    }
    if (lower == "exact" || lower == "true" || lower == "on") {
        return ColumnDominanceMode::Exact;
    }
    if (lower == "pareto") {
        return ColumnDominanceMode::Pareto;
    }
    return ColumnDominanceMode::Exact;
}

std::string columnDominanceModeName(ColumnDominanceMode mode) {
    switch (mode) {
        case ColumnDominanceMode::Off: return "off";
        case ColumnDominanceMode::Exact: return "exact";
        case ColumnDominanceMode::Pareto: return "pareto";
    }
    return "exact";
}

std::string projectionKey(const RouteLoadColumn& column) {
    std::ostringstream key;
    key << column.vehicle << "|" << column.mask << "|";
    for (int value : column.q) key << value << ",";
    return key.str();
}

ColumnDominanceOptions normalizeColumnDominanceOptions(ColumnDominanceOptions options) {
    if (!options.enabled || options.mode == ColumnDominanceMode::Off) {
        options.enabled = false;
        options.mode = ColumnDominanceMode::Off;
        return options;
    }
    if (options.mode == ColumnDominanceMode::Exact && !options.exact_safe) {
        options.mode = ColumnDominanceMode::Pareto;
    }
    return options;
}

void applyColumnDominance(std::vector<RouteLoadColumn>& columns,
                          ColumnDominanceOptions options,
                          ColumnDominanceStats& stats) {
    const auto start = Clock::now();
    const long long input_count = static_cast<long long>(columns.size());
    stats.columns_generated_raw += input_count;
    stats.dominance_input_columns += input_count;
    options = normalizeColumnDominanceOptions(options);
    stats.dominance_mode = columnDominanceModeName(options.mode);
    stats.dominance_exact_safe = options.exact_safe;

    if (!options.enabled || columns.size() <= 1) {
        const long long kept_count = static_cast<long long>(columns.size());
        stats.columns_after_dominance += kept_count;
        stats.dominance_kept_columns += kept_count;
        stats.dominance_time_seconds +=
            std::chrono::duration<double>(Clock::now() - start).count();
        return;
    }

    if (options.mode == ColumnDominanceMode::Exact) {
        std::unordered_map<std::string, std::size_t> best_index;
        std::vector<RouteLoadColumn> kept;
        kept.reserve(columns.size());
        for (RouteLoadColumn& column : columns) {
            const std::string key = projectionKey(column);
            auto it = best_index.find(key);
            if (it == best_index.end()) {
                best_index.emplace(key, kept.size());
                kept.push_back(std::move(column));
                continue;
            }
            RouteLoadColumn& incumbent = kept[it->second];
            if (exactRepresentativeBetter(column, incumbent)) {
                incumbent = std::move(column);
            }
            ++stats.columns_dominated;
            ++stats.dominance_removed_candidate_projection;
        }
        columns = std::move(kept);
    } else {
        std::unordered_map<std::string, std::vector<RouteLoadColumn>> buckets;
        buckets.reserve(columns.size());
        for (RouteLoadColumn& column : columns) {
            buckets[projectionKey(column)].push_back(std::move(column));
        }
        std::vector<RouteLoadColumn> kept;
        kept.reserve(columns.size());
        for (auto& item : buckets) {
            std::vector<RouteLoadColumn>& bucket = item.second;
            std::vector<char> dominated(bucket.size(), 0);
            for (std::size_t i = 0; i < bucket.size(); ++i) {
                if (dominated[i]) continue;
                for (std::size_t j = 0; j < bucket.size(); ++j) {
                    if (i == j || dominated[i]) continue;
                    if (paretoDominates(bucket[j], bucket[i]) ||
                        (samePathDependentValues(bucket[j], bucket[i]) &&
                         exactRepresentativeBetter(bucket[j], bucket[i]))) {
                        dominated[i] = 1;
                    }
                }
            }
            for (std::size_t i = 0; i < bucket.size(); ++i) {
                if (dominated[i]) {
                    ++stats.columns_dominated;
                    ++stats.dominance_removed_candidate_projection;
                } else {
                    kept.push_back(std::move(bucket[i]));
                }
            }
        }
        columns = std::move(kept);
    }

    const long long kept_count = static_cast<long long>(columns.size());
    stats.columns_after_dominance += kept_count;
    stats.dominance_kept_columns += kept_count;
    stats.dominance_removed_columns += std::max(0LL, input_count - kept_count);
    stats.dominance_time_seconds +=
        std::chrono::duration<double>(Clock::now() - start).count();
}

std::vector<RouteLoadColumn> filterNewColumnsByDominance(
    const std::vector<RouteLoadColumn>& existing,
    std::vector<RouteLoadColumn> candidates,
    ColumnDominanceOptions options,
    ColumnDominanceStats& stats) {
    const auto start = Clock::now();
    options = normalizeColumnDominanceOptions(options);
    stats.dominance_mode = columnDominanceModeName(options.mode);
    stats.dominance_exact_safe = options.exact_safe;
    const long long input_count = static_cast<long long>(candidates.size());
    stats.columns_generated_raw += input_count;
    stats.dominance_input_columns += input_count;

    if (!options.enabled || candidates.empty()) {
        const long long kept_count = static_cast<long long>(candidates.size());
        stats.columns_after_dominance += kept_count;
        stats.dominance_kept_columns += kept_count;
        stats.dominance_time_seconds +=
            std::chrono::duration<double>(Clock::now() - start).count();
        return candidates;
    }

    std::vector<RouteLoadColumn> candidate_frontier = std::move(candidates);
    ColumnDominanceStats candidate_stats;
    applyColumnDominance(candidate_frontier, options, candidate_stats);
    stats.columns_dominated += candidate_stats.columns_dominated;
    stats.dominance_removed_candidate_projection +=
        candidate_stats.dominance_removed_candidate_projection;

    std::unordered_map<std::string, std::vector<const RouteLoadColumn*>> existing_by_key;
    existing_by_key.reserve(existing.size());
    for (const RouteLoadColumn& column : existing) {
        existing_by_key[projectionKey(column)].push_back(&column);
    }

    std::vector<RouteLoadColumn> filtered;
    filtered.reserve(candidate_frontier.size());
    for (RouteLoadColumn& column : candidate_frontier) {
        bool from_existing_projection = false;
        const std::string key = projectionKey(column);
        auto it = existing_by_key.find(key);
        if (it != existing_by_key.end()) {
            for (const RouteLoadColumn* existing_column : it->second) {
                if (options.mode == ColumnDominanceMode::Exact ||
                    paretoDominates(*existing_column, column) ||
                    samePathDependentValues(*existing_column, column)) {
                    from_existing_projection = true;
                    break;
                }
            }
        }
        if (from_existing_projection) {
            ++stats.columns_dominated;
            ++stats.dominance_removed_existing_projection;
            continue;
        }
        filtered.push_back(std::move(column));
    }
    const long long kept_count = static_cast<long long>(filtered.size());
    stats.columns_after_dominance += kept_count;
    stats.dominance_kept_columns += kept_count;
    stats.dominance_removed_columns += std::max(0LL, input_count - kept_count);
    stats.dominance_time_seconds +=
        std::chrono::duration<double>(Clock::now() - start).count();
    return filtered;
}

void mergeColumnDominanceStats(ColumnDominanceStats& total,
                               const ColumnDominanceStats& add) {
    total.columns_generated_raw += add.columns_generated_raw;
    total.columns_after_dominance += add.columns_after_dominance;
    total.columns_dominated += add.columns_dominated;
    total.dominance_input_columns += add.dominance_input_columns;
    total.dominance_kept_columns += add.dominance_kept_columns;
    total.dominance_removed_columns += add.dominance_removed_columns;
    total.dominance_removed_existing_projection +=
        add.dominance_removed_existing_projection;
    total.dominance_removed_candidate_projection +=
        add.dominance_removed_candidate_projection;
    total.dominance_time_seconds += add.dominance_time_seconds;
    total.dominance_mode = add.dominance_mode;
    total.dominance_exact_safe = total.dominance_exact_safe && add.dominance_exact_safe;
}

} // namespace ebrp
