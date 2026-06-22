#include "Pricing.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <functional>
#include <limits>
#include <numeric>
#include <sstream>
#include <unordered_map>
#include <vector>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

std::string lowerCopy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return value;
}

double dualVisitCost(const PricingDuals& duals, int station) {
    return station < static_cast<int>(duals.visit_cost.size())
        ? duals.visit_cost[station] : 0.0;
}

double dualOperationCost(const PricingDuals& duals, int station) {
    return station < static_cast<int>(duals.operation_cost.size())
        ? duals.operation_cost[station] : 0.0;
}

double pathPairCost(const PricingDuals& duals, const std::vector<char>& used) {
    double cost = 0.0;
    for (const auto& entry : duals.pair_cost) {
        const int a = entry.first.first;
        const int b = entry.first.second;
        if (a > 0 && b > 0 &&
            a < static_cast<int>(used.size()) &&
            b < static_cast<int>(used.size()) &&
            used[a] && used[b]) {
            cost += entry.second;
        }
    }
    return cost;
}

double pathSubsetRowCost(const PricingDuals& duals, const std::vector<char>& used) {
    double cost = 0.0;
    for (const auto& entry : duals.subset_row_cost) {
        int count = 0;
        for (int station : entry.first) {
            if (station > 0 && station < static_cast<int>(used.size()) &&
                used[station]) {
                ++count;
            }
        }
        cost += static_cast<double>(count / 2) * entry.second;
    }
    return cost;
}

PricingResult runScalableNgDssrPricing(const Instance& instance,
                                       int vehicle,
                                       const PricingDuals& duals,
                                       const PricingOptions& options,
                                       Clock::time_point start);

class ExactPricer {
public:
    ExactPricer(const Instance& instance,
                int vehicle,
                const PricingDuals& duals,
                const PricingOptions& options,
                Clock::time_point start)
        : instance_(instance),
          vehicle_(vehicle),
          duals_(duals),
          options_(options),
          start_(start),
          q_(instance.V + 1, 0) {
        result_.best_reduced_cost = std::numeric_limits<double>::infinity();
        buildRequiredComponents();
        precomputeSupportDurationCuts();
        nonnegative_costs_ = duals_.constant >= -1e-12 &&
            duals_.travel_cost >= -1e-12 && duals_.pickup_cost >= -1e-12;
        for (int i = 1; i <= instance_.V && nonnegative_costs_; ++i) {
            if (stationVisitCost(i) < -1e-12) nonnegative_costs_ = false;
            if (std::fabs(stationOperationCost(i)) > 1e-12) nonnegative_costs_ = false;
        }
        for (const auto& entry : duals_.pair_cost) {
            if (entry.second < -1e-12) nonnegative_costs_ = false;
        }
        for (const auto& entry : duals_.subset_row_cost) {
            if (entry.second < -1e-12) nonnegative_costs_ = false;
        }
    }

    PricingResult run() {
        std::string engine = lowerCopy(options_.pricing_engine);
        if (engine.empty() || engine == "auto") {
            engine = instance_.V > 30 ? "hybrid" : "exact-label";
        }
        if (engine == "ng-dssr" || engine == "hybrid") {
            return runScalableNgDssrPricing(instance_, vehicle_, duals_, options_, start_);
        }
        result_.pricing_engine = "exact-label";
        result_.column_tracks = lowerCopy(options_.column_tracks);
        if (result_.column_tracks.empty() || result_.column_tracks == "auto") {
            result_.column_tracks = "elementary-only";
        }
        result_.rmp_column_space = lowerCopy(options_.rmp_column_space);
        if (result_.rmp_column_space.empty() || result_.rmp_column_space == "auto") {
            result_.rmp_column_space = "elementary";
        }
        result_.relaxed_rmp_enabled = options_.relaxed_columns_in_rmp ||
            result_.rmp_column_space == "ng-relaxed" ||
            result_.rmp_column_space == "two-track";
        if (instance_.V > 30) {
            result_.complete = false;
            result_.dssr_stop_reason =
                "unsupported_for_large_instance_exact_label_requires_dynamic_or_hybrid_pricing";
            result_.pricing_engine = "exact-label";
            result_.pricing_closure_status = "unsupported_for_large_instance";
            result_.best_reduced_cost = 0.0;
            return result_;
        }
        if (vehicle_ < 0 || vehicle_ >= instance_.M) {
            result_.complete = false;
            result_.pricing_closure_status = "invalid_vehicle";
            return result_;
        }
        if (useLabelSettingPricing()) {
            runLabelSettingPricing();
            if (!result_.complete) return result_;
            if (!result_.has_column) result_.best_reduced_cost = 0.0;
            result_.has_negative_column = result_.has_column &&
                result_.best_reduced_cost < -options_.negative_tolerance;
            result_.best_new_reduced_cost = result_.best_reduced_cost;
            result_.negative_new_projection_count =
                result_.has_negative_column ? 1 : 0;
            result_.pricing_closure_status = result_.has_negative_column
                ? "negative_columns_remaining" : "exact_no_negative";
            result_.elementary_columns_generated = result_.generated_columns;
            result_.elementary_columns_inserted =
                static_cast<long long>(result_.negative_columns.size());
            result_.elementary_pricing_closed =
                result_.complete && !result_.has_negative_column;
            result_.dssr_exact_elementary_closed = result_.elementary_pricing_closed;
            return result_;
        }
        for (int first = 1; first <= instance_.V; ++first) {
            if (shouldStop()) break;
            if (!stationAllowed(first)) continue;
            const double travel = instance_.dist[0][first];
            if (travel + instance_.dist[first][0] > instance_.total_time_limit + 1e-9) continue;
            path_.push_back(first);
            routeDfs(1 << (first - 1), first, travel);
            path_.pop_back();
        }
        if (!result_.has_column) result_.best_reduced_cost = 0.0;
        result_.has_negative_column = result_.has_column &&
            result_.best_reduced_cost < -options_.negative_tolerance;
        result_.best_new_reduced_cost = result_.best_reduced_cost;
        result_.negative_new_projection_count =
            result_.has_negative_column ? 1 : 0;
        result_.pricing_closure_status = result_.has_negative_column
            ? "negative_columns_remaining" : "exact_no_negative";
        result_.elementary_columns_generated = result_.generated_columns;
        result_.elementary_columns_inserted =
            static_cast<long long>(result_.negative_columns.size());
        result_.elementary_pricing_closed =
            result_.complete && !result_.has_negative_column;
        result_.dssr_exact_elementary_closed = result_.elementary_pricing_closed;
        return result_;
    }

private:
    struct OpLabel {
        double cost = std::numeric_limits<double>::infinity();
        int prev_load = -1;
        int prev_pickup = -1;
        int q = 0;
    };

    struct RouteLabel {
        int mask = 0;
        int last = 0;
        int load = 0;
        int pickup = 0;
        int parent = -1;
        int station = 0;
        int q = 0;
        double travel = 0.0;
        double cost = 0.0;
        bool active = true;
    };

    const Instance& instance_;
    int vehicle_;
    const PricingDuals& duals_;
    const PricingOptions& options_;
    Clock::time_point start_;
    std::vector<int> path_;
    std::vector<int> q_;
    PricingResult result_;
    bool nonnegative_costs_ = false;
    std::vector<int> required_closure_mask_;
    std::unordered_map<long long, double> completion_travel_cache_;
    std::vector<std::pair<double, int>> negative_label_candidates_;
    std::vector<std::vector<double>> metric_dist_;
    std::vector<int> forbidden_support_masks_;

    void buildRequiredComponents() {
        if (instance_.V > 30) {
            required_closure_mask_.assign(instance_.V + 1, 0);
            return;
        }
        std::vector<int> parent(instance_.V + 1);
        for (int i = 0; i <= instance_.V; ++i) parent[i] = i;
        std::function<int(int)> findRoot = [&](int x) {
            while (parent[x] != x) {
                parent[x] = parent[parent[x]];
                x = parent[x];
            }
            return x;
        };
        auto unite = [&](int a, int b) {
            if (a < 1 || a > instance_.V || b < 1 || b > instance_.V) return;
            a = findRoot(a);
            b = findRoot(b);
            if (a != b) parent[b] = a;
        };
        for (const auto& pair : options_.require_together_pairs) {
            unite(pair.first, pair.second);
        }
        std::vector<int> component_mask(instance_.V + 1, 0);
        for (int station = 1; station <= instance_.V; ++station) {
            component_mask[findRoot(station)] |= (1 << (station - 1));
        }
        required_closure_mask_.assign(instance_.V + 1, 0);
        for (int station = 1; station <= instance_.V; ++station) {
            required_closure_mask_[station] = component_mask[findRoot(station)];
        }
    }

    bool shouldStop() {
        if (result_.stopped_early_with_column) return true;
        if (!result_.complete) return true;
        if (options_.time_limit_seconds <= 0.0) return false;
        const double elapsed = std::chrono::duration<double>(Clock::now() - start_).count();
        if (elapsed >= options_.time_limit_seconds) {
            result_.complete = false;
            result_.pricing_closure_status = "pricing_time_limit";
            return true;
        }
        return false;
    }

    double stationVisitCost(int station) const {
        return (station < static_cast<int>(duals_.visit_cost.size()))
            ? duals_.visit_cost[station] : 0.0;
    }

    double stationOperationCost(int station) const {
        return (station < static_cast<int>(duals_.operation_cost.size()))
            ? duals_.operation_cost[station] : 0.0;
    }

    double pairCost(int mask) const {
        double cost = 0.0;
        for (const auto& entry : duals_.pair_cost) {
            if (hasStation(mask, entry.first.first) &&
                hasStation(mask, entry.first.second)) {
                cost += entry.second;
            }
        }
        return cost;
    }

    double subsetRowCost(int mask) const {
        double cost = 0.0;
        for (const auto& entry : duals_.subset_row_cost) {
            int count = 0;
            for (int station : entry.first) {
                if (hasStation(mask, station)) ++count;
            }
            const int coefficient = count / 2;
            if (coefficient > 0) cost += static_cast<double>(coefficient) * entry.second;
        }
        return cost;
    }

    static bool hasStation(int mask, int station) {
        return station > 0 && (mask & (1 << (station - 1)));
    }

    bool stationAllowed(int station) const {
        const int bit = 1 << (station - 1);
        if (options_.forbidden_station_mask & bit) return false;
        return options_.allowed_station_mask == 0 ||
            (options_.allowed_station_mask & bit);
    }

    long long labelKey(int mask, int last, int load, int pickup) const {
        const long long v = static_cast<long long>(instance_.V + 1);
        const long long q = static_cast<long long>(instance_.Q[vehicle_] + 1);
        const int pickup_budget = maxPickupBudget();
        const long long b = static_cast<long long>(pickup_budget + 1);
        return (((static_cast<long long>(mask) * v + last) * q + load) * b + pickup);
    }

    int maxPickupBudget() const {
        const double cunit = instance_.pickup_time + instance_.drop_time;
        if (cunit <= 1e-12) return 0;
        return static_cast<int>(std::floor(instance_.total_time_limit / cunit + 1e-9));
    }

    bool useLabelSettingPricing() const {
        if (instance_.V <= 0 || instance_.V > 16) return false;
        if (vehicle_ < 0 || vehicle_ >= instance_.M) return false;
        if (instance_.Q[vehicle_] > 80) return false;
        return maxPickupBudget() <= 120;
    }

    bool violatesForbiddenTogether(int mask) const {
        for (const auto& pair : options_.forbid_together_pairs) {
            if (hasStation(mask, pair.first) && hasStation(mask, pair.second)) return true;
        }
        return false;
    }

    bool satisfiesRequiredTogether(int mask) const {
        for (const auto& pair : options_.require_together_pairs) {
            const bool first = hasStation(mask, pair.first);
            const bool second = hasStation(mask, pair.second);
            if (first != second) return false;
        }
        return true;
    }

    int requiredClosureMask(int mask) const {
        int closure = mask;
        for (int station = 1; station <= instance_.V; ++station) {
            if (hasStation(mask, station)) closure |= required_closure_mask_[station];
        }
        return closure;
    }

    bool branchClosureImpossible(int mask) const {
        if (mask == 0) return false;
        const int full_mask = (1 << instance_.V) - 1;
        const int closure = requiredClosureMask(mask) & full_mask;
        if ((closure & options_.forbidden_station_mask) != 0) return true;
        if (options_.allowed_station_mask != 0 &&
            (closure & (~options_.allowed_station_mask & full_mask)) != 0) {
            return true;
        }
        return violatesForbiddenTogether(closure);
    }

    int fullStationMask() const {
        return (1 << instance_.V) - 1;
    }

    int allowedCompletionMask() const {
        const int full_mask = fullStationMask();
        int allowed = options_.allowed_station_mask == 0
            ? full_mask
            : (options_.allowed_station_mask & full_mask);
        allowed &= ~options_.forbidden_station_mask;
        return allowed;
    }

    static int popcount(int mask) {
        int count = 0;
        while (mask != 0) {
            mask &= (mask - 1);
            ++count;
        }
        return count;
    }

    void precomputeMetricClosure() {
        metric_dist_ = instance_.dist;
        const int n = instance_.V + 1;
        if (static_cast<int>(metric_dist_.size()) < n) return;
        for (int k = 0; k < n; ++k) {
            for (int i = 0; i < n; ++i) {
                if (static_cast<int>(metric_dist_[i].size()) < n) continue;
                for (int j = 0; j < n; ++j) {
                    if (metric_dist_[i][k] + metric_dist_[k][j] <
                        metric_dist_[i][j] - 1e-12) {
                        metric_dist_[i][j] =
                            metric_dist_[i][k] + metric_dist_[k][j];
                    }
                }
            }
        }
    }

    double supportCycleLowerBound(int mask) const {
        if (mask == 0) return 0.0;
        std::vector<int> stations;
        for (int station = 1; station <= instance_.V; ++station) {
            if (mask & (1 << (station - 1))) stations.push_back(station);
        }
        const int m = static_cast<int>(stations.size());
        if (m == 0) return 0.0;
        const int state_count = 1 << m;
        std::vector<std::vector<double>> dp(
            state_count, std::vector<double>(m, std::numeric_limits<double>::infinity()));
        for (int i = 0; i < m; ++i) {
            dp[1 << i][i] = metric_dist_[0][stations[i]];
        }
        for (int state = 1; state < state_count; ++state) {
            for (int last = 0; last < m; ++last) {
                const double cur = dp[state][last];
                if (!std::isfinite(cur)) continue;
                for (int next = 0; next < m; ++next) {
                    if (state & (1 << next)) continue;
                    const int next_state = state | (1 << next);
                    dp[next_state][next] = std::min(
                        dp[next_state][next],
                        cur + metric_dist_[stations[last]][stations[next]]);
                }
            }
        }
        const int full = state_count - 1;
        double best = std::numeric_limits<double>::infinity();
        for (int last = 0; last < m; ++last) {
            best = std::min(best, dp[full][last] + metric_dist_[stations[last]][0]);
        }
        return best;
    }

    bool containsKnownForbiddenSupport(int mask) const {
        for (int forbidden : forbidden_support_masks_) {
            if ((mask & forbidden) == forbidden) return true;
        }
        return false;
    }

    void precomputeSupportDurationCuts() {
        const auto cut_start = Clock::now();
        const int max_subset = std::max(0, std::min(options_.support_duration_max_subset_size,
                                                    instance_.V));
        result_.support_duration_max_subset_size = max_subset;
        if (!options_.support_duration_pruning || instance_.V <= 0 ||
            instance_.V > 16 || max_subset <= 0) {
            result_.support_duration_precompute_time_seconds =
                std::chrono::duration<double>(Clock::now() - cut_start).count();
            return;
        }
        precomputeMetricClosure();
        if (static_cast<int>(metric_dist_.size()) < instance_.V + 1) return;
        const double cunit = instance_.pickup_time + instance_.drop_time;
        const double operation_unit = std::max(0.0, cunit);
        const int full = (1 << instance_.V) - 1;
        for (int mask = 1; mask <= full; ++mask) {
            const int support_size = popcount(mask);
            if (support_size > max_subset) continue;
            if (containsKnownForbiddenSupport(mask)) continue;
            const double cycle_lb = supportCycleLowerBound(mask);
            const int min_pickups = (support_size + 1) / 2;
            const double support_duration_lb = cycle_lb +
                operation_unit * static_cast<double>(min_pickups);
            if (support_duration_lb > instance_.total_time_limit + 1e-9) {
                forbidden_support_masks_.push_back(mask);
            }
        }
        result_.support_duration_cuts_generated =
            static_cast<long long>(forbidden_support_masks_.size());
        result_.support_duration_min_pickup_rule = "ceil_half_support";
        result_.support_duration_strong_cuts_generated =
            result_.support_duration_cuts_generated;
        result_.support_duration_precompute_time_seconds =
            std::chrono::duration<double>(Clock::now() - cut_start).count();
    }

    bool violatesSupportDurationPruning(int mask) const {
        if (forbidden_support_masks_.empty()) return false;
        return containsKnownForbiddenSupport(mask);
    }

    double completionReducedCostLowerBound(const RouteLabel& label) {
        double lb = duals_.constant + label.cost;
        const int closure = requiredClosureMask(label.mask) & fullStationMask();
        const int allowed = allowedCompletionMask() | label.mask;
        const int missing_required = closure & ~label.mask;
        const int remaining_optional = allowed & ~closure;

        if (label.last > 0) {
            if (duals_.travel_cost >= 0.0) {
                lb += duals_.travel_cost *
                    minAdditionalTravelThroughMissing(label.last, missing_required);
            } else {
                const double cunit = instance_.pickup_time + instance_.drop_time;
                const double max_additional_travel = std::max(
                    0.0,
                    instance_.total_time_limit - cunit * label.pickup - label.travel);
                lb += duals_.travel_cost * max_additional_travel;
            }
        }

        for (int station = 1; station <= instance_.V; ++station) {
            const int bit = 1 << (station - 1);
            if (label.mask & bit) continue;
            if ((missing_required & bit) != 0) {
                lb += stationVisitCost(station);
            } else if ((remaining_optional & bit) != 0) {
                lb += std::min(0.0, stationVisitCost(station));
            }
        }

        const int pickup_remaining = std::max(0, maxPickupBudget() - label.pickup);
        for (int station = 1; station <= instance_.V; ++station) {
            const int bit = 1 << (station - 1);
            if (label.mask & bit) continue;
            if ((allowed & bit) == 0) continue;
            const double pickup_coeff = duals_.pickup_cost + stationOperationCost(station);
            if (pickup_coeff < 0.0) {
                const int max_pick = std::min({
                    instance_.initial[station],
                    instance_.Q[vehicle_],
                    pickup_remaining
                });
                lb += pickup_coeff * static_cast<double>(std::max(0, max_pick));
            }
            const double drop_coeff = -stationOperationCost(station);
            if (drop_coeff < 0.0) {
                const int max_drop = std::min(
                    instance_.capacity[station] - instance_.initial[station],
                    instance_.Q[vehicle_]);
                lb += drop_coeff * static_cast<double>(std::max(0, max_drop));
            }
        }

        for (const auto& entry : duals_.pair_cost) {
            const int first_bit = 1 << (entry.first.first - 1);
            const int second_bit = 1 << (entry.first.second - 1);
            const bool unavoidable =
                (closure & first_bit) != 0 && (closure & second_bit) != 0;
            if (unavoidable) {
                lb += entry.second;
                continue;
            }
            const bool possible =
                ((allowed & first_bit) != 0) && ((allowed & second_bit) != 0);
            if (possible && entry.second < 0.0) lb += entry.second;
        }

        for (const auto& entry : duals_.subset_row_cost) {
            int unavoidable = 0;
            int possible = 0;
            for (int station : entry.first) {
                if (station < 1 || station > instance_.V) continue;
                const int bit = 1 << (station - 1);
                if (closure & bit) ++unavoidable;
                if (allowed & bit) ++possible;
            }
            if (entry.second >= 0.0) {
                lb += static_cast<double>(unavoidable / 2) * entry.second;
            } else {
                lb += static_cast<double>(possible / 2) * entry.second;
            }
        }

        return lb;
    }

    double minAdditionalTravelThroughMissing(int last, int missing_mask) {
        if (missing_mask == 0) return instance_.dist[last][0];
        const long long key =
            (static_cast<long long>(missing_mask) << 6) | static_cast<long long>(last);
        auto cached = completion_travel_cache_.find(key);
        if (cached != completion_travel_cache_.end()) return cached->second;
        double best = std::numeric_limits<double>::infinity();
        for (int station = 1; station <= instance_.V; ++station) {
            const int bit = 1 << (station - 1);
            if ((missing_mask & bit) == 0) continue;
            best = std::min(best, instance_.dist[last][station]
                + minAdditionalTravelThroughMissing(station, missing_mask ^ bit));
        }
        completion_travel_cache_[key] = best;
        return best;
    }

    double requiredClosureTravelLowerBound(int mask, int last, double travel) {
        if (mask == 0 || last <= 0) return travel;
        const int closure = requiredClosureMask(mask);
        const int missing = closure & ~mask;
        return travel + minAdditionalTravelThroughMissing(last, missing);
    }

    bool labelDominates(const RouteLabel& a, const RouteLabel& b) const {
        return a.cost <= b.cost + 1e-12 && a.travel <= b.travel + 1e-9;
    }

    bool insertLabel(std::vector<RouteLabel>& labels,
                     std::unordered_map<long long, std::vector<int>>& buckets,
                     std::vector<std::vector<long long>>& keys_by_mask,
                     RouteLabel label) {
        const long long key = labelKey(label.mask, label.last, label.load, label.pickup);
        auto [it, inserted] = buckets.emplace(key, std::vector<int>{});
        std::vector<int>& bucket = it->second;
        for (int idx : bucket) {
            if (!labels[idx].active) continue;
            if (labelDominates(labels[idx], label)) return false;
        }
        for (int idx : bucket) {
            if (!labels[idx].active) continue;
            if (labelDominates(label, labels[idx])) labels[idx].active = false;
        }
        const int label_idx = static_cast<int>(labels.size());
        labels.push_back(label);
        bucket.push_back(label_idx);
        if (inserted) keys_by_mask[label.mask].push_back(key);
        return true;
    }

    void recordNegativeLabelCandidate(double reduced_cost, int label_idx) {
        const int limit = std::max(1, options_.max_returned_columns);
        if (limit <= 1) return;
        if (reduced_cost >= -options_.negative_tolerance) return;
        negative_label_candidates_.push_back({reduced_cost, label_idx});
        std::sort(negative_label_candidates_.begin(), negative_label_candidates_.end(),
                  [](const auto& a, const auto& b) {
                      if (std::fabs(a.first - b.first) > 1e-12) return a.first < b.first;
                      return a.second < b.second;
                  });
        if (static_cast<int>(negative_label_candidates_.size()) > limit) {
            negative_label_candidates_.resize(limit);
        }
    }

    bool considerClosedLabel(const RouteLabel& label, int label_idx) {
        if (label.mask == 0 || label.last <= 0) return false;
        if (violatesSupportDurationPruning(label.mask)) {
            ++result_.support_duration_pruned_columns;
            ++result_.support_duration_strong_pruned_columns;
            return false;
        }
        if (!satisfiesRequiredTogether(label.mask)) return false;
        const double route_travel = label.travel + instance_.dist[label.last][0];
        const double cunit = instance_.pickup_time + instance_.drop_time;
        const double duration = route_travel + cunit * label.pickup;
        if (duration > instance_.total_time_limit + 1e-9) return false;
        const double rc = duals_.constant
            + label.cost
            + duals_.travel_cost * instance_.dist[label.last][0]
            + pairCost(label.mask)
            + subsetRowCost(label.mask);
        ++result_.generated_columns;
        recordNegativeLabelCandidate(rc, label_idx);
        bool improved = false;
        if (!result_.has_column || rc < result_.best_reduced_cost - 1e-12) {
            result_.has_column = true;
            result_.best_reduced_cost = rc;
            result_.best_column.vehicle = vehicle_;
            result_.best_column.mask = label.mask;
            result_.best_column.pickup = label.pickup;
            result_.best_column.travel = route_travel;
            result_.best_column.duration = duration;
            result_.best_column.reduced_cost = rc;
            improved = true;
        }
        if (std::isfinite(options_.stop_reduced_cost) &&
            result_.has_column &&
            result_.best_reduced_cost < options_.stop_reduced_cost - 1e-12) {
            result_.stopped_early_with_column = true;
            result_.complete = false;
        }
        return improved;
    }

    RouteLoadColumn buildColumnFromLabel(const std::vector<RouteLabel>& labels,
                                         int label_idx,
                                         double reduced_cost) {
        RouteLoadColumn column;
        if (label_idx < 0 || label_idx >= static_cast<int>(labels.size())) return column;
        const RouteLabel& final_label = labels[label_idx];
        std::vector<int> reversed_path;
        std::vector<int> q(instance_.V + 1, 0);
        for (int idx = label_idx; idx >= 0; idx = labels[idx].parent) {
            const RouteLabel& label = labels[idx];
            if (label.station > 0) {
                reversed_path.push_back(label.station);
                q[label.station] = label.q;
            }
        }
        std::reverse(reversed_path.begin(), reversed_path.end());
        column.vehicle = vehicle_;
        column.mask = final_label.mask;
        column.station_set = StationSet::fromMask(instance_.V, final_label.mask);
        column.path = std::move(reversed_path);
        column.q = std::move(q);
        column.pickup = final_label.pickup;
        column.travel = final_label.travel + instance_.dist[final_label.last][0];
        column.duration = column.travel +
            (instance_.pickup_time + instance_.drop_time) * final_label.pickup;
        column.reduced_cost = reduced_cost;
        return column;
    }

    void reconstructBestLabelColumn(const std::vector<RouteLabel>& labels, int best_idx) {
        if (best_idx < 0 || best_idx >= static_cast<int>(labels.size())) return;
        RouteLoadColumn column =
            buildColumnFromLabel(labels, best_idx, result_.best_reduced_cost);
        result_.best_column.path = std::move(column.path);
        result_.best_column.q = std::move(column.q);
    }

    void reconstructNegativeLabelColumns(const std::vector<RouteLabel>& labels) {
        result_.negative_columns.clear();
        for (const auto& candidate : negative_label_candidates_) {
            RouteLoadColumn column =
                buildColumnFromLabel(labels, candidate.second, candidate.first);
            if (column.mask != 0) result_.negative_columns.push_back(std::move(column));
        }
    }

    void runLabelSettingPricing() {
        const int pickup_budget = maxPickupBudget();
        const int q_capacity = instance_.Q[vehicle_];
        if (pickup_budget <= 0 || q_capacity <= 0) return;
        const int full_mask = (1 << instance_.V) - 1;
        std::vector<RouteLabel> labels;
        labels.reserve(1024);
        std::unordered_map<long long, std::vector<int>> buckets;
        buckets.reserve(4096);
        std::vector<std::vector<long long>> keys_by_mask(full_mask + 1);

        RouteLabel root;
        insertLabel(labels, buckets, keys_by_mask, root);
        int best_label_idx = -1;

        for (int mask = 0; mask <= full_mask; ++mask) {
            for (long long key : keys_by_mask[mask]) {
                auto it = buckets.find(key);
                if (it == buckets.end()) continue;
                const std::vector<int> bucket = it->second;
                for (int label_idx : bucket) {
                    if (shouldStop()) return;
                    if (label_idx < 0 || label_idx >= static_cast<int>(labels.size())) continue;
                    const RouteLabel label = labels[label_idx];
                    if (!label.active || label.mask != mask) continue;
                    if (branchClosureImpossible(label.mask)) continue;
                    if (violatesSupportDurationPruning(label.mask)) {
                        ++result_.support_duration_pruned_labels;
                        ++result_.support_duration_strong_pruned_labels;
                        continue;
                    }
                    ++result_.route_states;
                    if (options_.use_completion_lb_pruning &&
                        result_.has_column &&
                        completionReducedCostLowerBound(label) >=
                            result_.best_reduced_cost - 1e-12) {
                        continue;
                    }
                    if (label.last > 0) {
                        const double closure_travel_lb =
                            requiredClosureTravelLowerBound(label.mask, label.last, label.travel);
                        if (closure_travel_lb +
                                (instance_.pickup_time + instance_.drop_time) * label.pickup >
                                instance_.total_time_limit + 1e-9) {
                            continue;
                        }
                        if (considerClosedLabel(label, label_idx)) {
                            best_label_idx = label_idx;
                        }
                        if (result_.stopped_early_with_column) {
                            if (best_label_idx >= 0) {
                                reconstructBestLabelColumn(labels, best_label_idx);
                            }
                            reconstructNegativeLabelColumns(labels);
                            return;
                        }
                    }
                    for (int station = 1; station <= instance_.V; ++station) {
                        if (!stationAllowed(station)) continue;
                        const int bit = 1 << (station - 1);
                        if (label.mask & bit) continue;
                        const int next_mask = label.mask | bit;
                        if (violatesForbiddenTogether(next_mask)) continue;
                        if (branchClosureImpossible(next_mask)) continue;
                        if (violatesSupportDurationPruning(next_mask)) {
                            ++result_.support_duration_pruned_labels;
                            ++result_.support_duration_strong_pruned_labels;
                            continue;
                        }
                        const double next_travel = label.travel +
                            instance_.dist[label.last][station];
                        if (next_travel + instance_.dist[station][0] >
                                instance_.total_time_limit + 1e-9) {
                            continue;
                        }
                        const double closure_travel_lb =
                            requiredClosureTravelLowerBound(next_mask, station, next_travel);
                        const double station_cost = duals_.travel_cost *
                                instance_.dist[label.last][station]
                            + stationVisitCost(station);

                    const int max_pick = std::min({
                        instance_.initial[station],
                        q_capacity - label.load,
                        pickup_budget - label.pickup
                    });
                    if ((options_.forbid_pickup_station_mask & bit) == 0) {
                        for (int p = 1; p <= max_pick; ++p) {
                            const int next_pickup = label.pickup + p;
                            const double duration_lb = closure_travel_lb +
                                (instance_.pickup_time + instance_.drop_time) * next_pickup;
                            if (duration_lb > instance_.total_time_limit + 1e-9) break;
                            RouteLabel next;
                            next.mask = next_mask;
                            next.last = station;
                            next.load = label.load + p;
                            next.pickup = next_pickup;
                            next.parent = label_idx;
                            next.station = station;
                            next.q = p;
                            next.travel = next_travel;
                            next.cost = label.cost + station_cost
                                + (duals_.pickup_cost + stationOperationCost(station)) * p;
                            if (options_.use_completion_lb_pruning &&
                                result_.has_column &&
                                completionReducedCostLowerBound(next) >=
                                    result_.best_reduced_cost - 1e-12) {
                                continue;
                            }
                            insertLabel(labels, buckets, keys_by_mask, next);
                            ++result_.operation_states;
                        }
                    }

                    const int max_drop = std::min(
                        instance_.capacity[station] - instance_.initial[station],
                        label.load);
                    if ((options_.forbid_drop_station_mask & bit) == 0) {
                        for (int d = 1; d <= max_drop; ++d) {
                            const double duration_lb = closure_travel_lb +
                                (instance_.pickup_time + instance_.drop_time) * label.pickup;
                            if (duration_lb > instance_.total_time_limit + 1e-9) break;
                            RouteLabel next;
                            next.mask = next_mask;
                            next.last = station;
                            next.load = label.load - d;
                            next.pickup = label.pickup;
                            next.parent = label_idx;
                            next.station = station;
                            next.q = -d;
                            next.travel = next_travel;
                            next.cost = label.cost + station_cost
                                - stationOperationCost(station) * d;
                            if (options_.use_completion_lb_pruning &&
                                result_.has_column &&
                                completionReducedCostLowerBound(next) >=
                                    result_.best_reduced_cost - 1e-12) {
                                continue;
                            }
                            insertLabel(labels, buckets, keys_by_mask, next);
                            ++result_.operation_states;
                        }
                    }
                }
            }
        }
        }

        if (best_label_idx >= 0) reconstructBestLabelColumn(labels, best_label_idx);
        reconstructNegativeLabelColumns(labels);
    }

    void routeDfs(int mask, int last, double travel_without_return) {
        ++result_.route_states;
        if ((result_.route_states & 0x3fff) == 0 && shouldStop()) return;
        if (violatesForbiddenTogether(mask)) return;
        if (branchClosureImpossible(mask)) return;
        if (violatesSupportDurationPruning(mask)) {
            ++result_.support_duration_pruned_labels;
            ++result_.support_duration_strong_pruned_labels;
            return;
        }
        const double closure_travel_lb =
            requiredClosureTravelLowerBound(mask, last, travel_without_return);
        if (closure_travel_lb > instance_.total_time_limit + 1e-9) return;

        const double route_travel = travel_without_return + instance_.dist[last][0];
        if (nonnegative_costs_ && result_.has_column &&
            duals_.constant + duals_.travel_cost * route_travel >=
                result_.best_reduced_cost - 1e-12) {
            return;
        }
        if (route_travel <= instance_.total_time_limit + 1e-9 &&
            satisfiesRequiredTogether(mask)) {
            enumerateOperations(mask, route_travel);
        }

        for (int station = 1; station <= instance_.V; ++station) {
            const int bit = 1 << (station - 1);
            if (!stationAllowed(station)) continue;
            if (mask & bit) continue;
            const int next_mask = mask | bit;
            if (branchClosureImpossible(next_mask)) continue;
            if (violatesSupportDurationPruning(next_mask)) {
                ++result_.support_duration_pruned_labels;
                ++result_.support_duration_strong_pruned_labels;
                continue;
            }
            const double next_travel = travel_without_return + instance_.dist[last][station];
            if (next_travel + instance_.dist[station][0] > instance_.total_time_limit + 1e-9) {
                continue;
            }
            path_.push_back(station);
            routeDfs(next_mask, station, next_travel);
            path_.pop_back();
            if (!result_.complete) return;
        }
    }

    void enumerateOperations(int mask, double route_travel) {
        if (violatesSupportDurationPruning(mask)) {
            ++result_.support_duration_pruned_columns;
            ++result_.support_duration_strong_pruned_columns;
            return;
        }
        const double cunit = instance_.pickup_time + instance_.drop_time;
        const int pickup_budget = static_cast<int>(
            std::floor((instance_.total_time_limit - route_travel) / cunit + 1e-9));
        if (pickup_budget <= 0) return;
        if (nonnegative_costs_ && result_.has_column &&
            duals_.constant + duals_.travel_cost * route_travel +
                    duals_.pickup_cost >= result_.best_reduced_cost - 1e-12) {
            return;
        }
        priceOperationsByDp(mask, route_travel, pickup_budget);
    }

    void priceOperationsByDp(int mask, double route_travel, int pickup_budget) {
        const int path_size = static_cast<int>(path_.size());
        const int q_capacity = instance_.Q[vehicle_];
        if (path_size <= 0 || q_capacity <= 0 || pickup_budget <= 0) return;

        const int budget = std::min(pickup_budget, std::max(0, pickup_budget));
        const int state_count = (path_size + 1) * (q_capacity + 1) * (budget + 1);
        std::vector<OpLabel> dp(static_cast<std::size_t>(state_count));
        auto idx = [&](int pos, int load, int pickup) {
            return (pos * (q_capacity + 1) + load) * (budget + 1) + pickup;
        };
        auto relax = [&](int pos,
                         int load,
                         int pickup,
                         int next_load,
                         int next_pickup,
                         int q,
                         double new_cost) {
            OpLabel& label = dp[static_cast<std::size_t>(
                idx(pos + 1, next_load, next_pickup))];
            if (new_cost < label.cost - 1e-12) {
                label.cost = new_cost;
                label.prev_load = load;
                label.prev_pickup = pickup;
                label.q = q;
            }
        };

        dp[static_cast<std::size_t>(idx(0, 0, 0))].cost = 0.0;
        for (int pos = 0; pos < path_size; ++pos) {
            const int station = path_[pos];
            const double op_cost = stationOperationCost(station);
            for (int load = 0; load <= q_capacity; ++load) {
                for (int pickup = 0; pickup <= budget; ++pickup) {
                    const OpLabel& label = dp[static_cast<std::size_t>(
                        idx(pos, load, pickup))];
                    if (!std::isfinite(label.cost)) continue;
                    ++result_.operation_states;
                    if ((result_.operation_states & 0x3fff) == 0 && shouldStop()) return;
                    if (nonnegative_costs_ && result_.has_column) {
                        const int min_extra_pickup = (pickup == 0) ? 1 : 0;
                        const double lb = duals_.constant
                            + duals_.travel_cost * route_travel
                            + label.cost
                            + duals_.pickup_cost * min_extra_pickup;
                        if (lb >= result_.best_reduced_cost - 1e-12) continue;
                    }

                    const int max_pick = std::min({
                        instance_.initial[station],
                        q_capacity - load,
                        budget - pickup
                    });
                    const int bit = 1 << (station - 1);
                    if ((options_.forbid_pickup_station_mask & bit) == 0) {
                        for (int p = 1; p <= max_pick; ++p) {
                            relax(pos, load, pickup, load + p, pickup + p, p,
                                  label.cost + duals_.pickup_cost * p + op_cost * p);
                        }
                    }

                    const int max_drop = std::min(
                        instance_.capacity[station] - instance_.initial[station], load);
                    if ((options_.forbid_drop_station_mask & bit) == 0) {
                        for (int d = 1; d <= max_drop; ++d) {
                            relax(pos, load, pickup, load - d, pickup, -d,
                                  label.cost - op_cost * d);
                        }
                    }
                }
            }
        }

        double best_op_cost = std::numeric_limits<double>::infinity();
        int best_load = -1;
        int best_pickup = -1;
        for (int load = 0; load <= q_capacity; ++load) {
            for (int pickup = 1; pickup <= budget; ++pickup) {
                const OpLabel& label = dp[static_cast<std::size_t>(
                    idx(path_size, load, pickup))];
                if (label.cost < best_op_cost - 1e-12) {
                    best_op_cost = label.cost;
                    best_load = load;
                    best_pickup = pickup;
                }
            }
        }
        if (best_load < 0) return;

        q_.assign(instance_.V + 1, 0);
        int load = best_load;
        int pickup = best_pickup;
        for (int pos = path_size; pos > 0; --pos) {
            const OpLabel& label = dp[static_cast<std::size_t>(idx(pos, load, pickup))];
            const int station = path_[pos - 1];
            q_[station] = label.q;
            load = label.prev_load;
            pickup = label.prev_pickup;
        }

        addBestColumnForPath(mask, route_travel, best_pickup, best_op_cost);
    }

    void addBestColumnForPath(int mask, double route_travel, int pickup, double operation_cost) {
        const double duration = route_travel +
            (instance_.pickup_time + instance_.drop_time) * pickup;
        if (duration > instance_.total_time_limit + 1e-9) return;

        double rc = duals_.constant + duals_.travel_cost * route_travel
            + operation_cost + pairCost(mask) + subsetRowCost(mask);
        for (int station : path_) {
            rc += stationVisitCost(station);
        }

        ++result_.generated_columns;
        if (!result_.has_column || rc < result_.best_reduced_cost - 1e-12) {
            result_.has_column = true;
            result_.best_reduced_cost = rc;
            result_.best_column.vehicle = vehicle_;
            result_.best_column.mask = mask;
            result_.best_column.station_set = StationSet::fromMask(instance_.V, mask);
            result_.best_column.path = path_;
            result_.best_column.q = q_;
            result_.best_column.pickup = pickup;
            result_.best_column.travel = route_travel;
            result_.best_column.duration = duration;
            result_.best_column.reduced_cost = rc;
        }
        if (std::isfinite(options_.stop_reduced_cost) &&
            result_.has_column &&
            result_.best_reduced_cost < options_.stop_reduced_cost - 1e-12) {
            result_.stopped_early_with_column = true;
            result_.complete = false;
        }
    }
};

PricingResult runScalableNgDssrPricing(const Instance& instance,
                                       int vehicle,
                                       const PricingDuals& duals,
                                       const PricingOptions& options,
                                       Clock::time_point start) {
    PricingResult result;
    result.pricing_engine = lowerCopy(options.pricing_engine);
    if (result.pricing_engine.empty() || result.pricing_engine == "auto") {
        result.pricing_engine = "hybrid";
    }
    result.column_tracks = lowerCopy(options.column_tracks);
    if (result.column_tracks.empty() || result.column_tracks == "auto") {
        result.column_tracks = "two-track";
    }
    result.rmp_column_space = lowerCopy(options.rmp_column_space);
    if (result.rmp_column_space.empty() || result.rmp_column_space == "auto") {
        result.rmp_column_space =
            result.column_tracks == "two-track" ? "two-track" : "elementary";
    }
    result.relaxed_rmp_enabled = options.relaxed_columns_in_rmp ||
        result.column_tracks == "two-track" ||
        result.rmp_column_space == "ng-relaxed" ||
        result.rmp_column_space == "two-track";
    result.ng_size = std::max(1, options.ng_size);
    result.ng_neighborhood_mode = lowerCopy(options.ng_neighborhood_mode);
    if (result.ng_neighborhood_mode.empty()) result.ng_neighborhood_mode = "nearest";
    result.dssr_final_exact = options.dssr_final_exact;
    const auto pricing_start = Clock::now();
    PricingDuals search_duals = duals;
    const std::string stabilization = lowerCopy(options.cg_dual_stabilization);
    auto scaleDualVector = [](std::vector<double>& values, double scale) {
        for (double& value : values) value *= scale;
    };
    if (stabilization == "smooth") {
        const double alpha = std::max(0.0, std::min(1.0, options.cg_dual_smoothing_alpha));
        search_duals.constant *= alpha;
        scaleDualVector(search_duals.visit_cost, alpha);
        scaleDualVector(search_duals.operation_cost, alpha);
        for (auto& entry : search_duals.pair_cost) entry.second *= alpha;
        for (auto& entry : search_duals.subset_row_cost) entry.second *= alpha;
        search_duals.travel_cost *= alpha;
        search_duals.pickup_cost *= alpha;
    } else if (stabilization == "box") {
        const double radius = std::max(0.0, options.cg_dual_box_radius);
        auto clamp = [radius](double value) {
            return std::max(-radius, std::min(radius, value));
        };
        search_duals.constant = clamp(search_duals.constant);
        for (double& value : search_duals.visit_cost) value = clamp(value);
        for (double& value : search_duals.operation_cost) value = clamp(value);
        for (auto& entry : search_duals.pair_cost) entry.second = clamp(entry.second);
        for (auto& entry : search_duals.subset_row_cost) entry.second = clamp(entry.second);
        search_duals.travel_cost = clamp(search_duals.travel_cost);
        search_duals.pickup_cost = clamp(search_duals.pickup_cost);
    }
    if (vehicle < 0 || vehicle >= instance.M || instance.V <= 0) {
        result.complete = false;
        result.dssr_stop_reason = "invalid_vehicle_or_empty_instance";
        result.pricing_closure_status = "invalid_vehicle";
        return result;
    }

    auto timedOut = [&]() {
        const double limit = options.dssr_time_limit > 0.0
            ? options.dssr_time_limit : options.time_limit_seconds;
        if (limit <= 0.0) return false;
        const double elapsed =
            std::chrono::duration<double>(Clock::now() - start).count();
        if (elapsed >= limit) {
            result.complete = false;
            result.dssr_stop_reason = "dssr_time_limit";
            result.pricing_closure_status = "pricing_time_limit";
            return true;
        }
        return false;
    };

    auto stationAllowedLarge = [&](int station) {
        if (station < 1 || station > instance.V) return false;
        if (station <= 31 && (options.forbidden_station_mask & (1 << (station - 1)))) {
            return false;
        }
        if (options.allowed_station_mask != 0) {
            if (station > 31) return false;
            if ((options.allowed_station_mask & (1 << (station - 1))) == 0) return false;
        }
        return true;
    };

    auto columnAllowedByBranchPairs = [&](const StationSet& set) {
        for (const auto& pair : options.forbid_together_pairs) {
            if (set.contains(pair.first) && set.contains(pair.second)) return false;
        }
        for (const auto& pair : options.require_together_pairs) {
            if (set.contains(pair.first) != set.contains(pair.second)) return false;
        }
        return true;
    };

    auto buildColumn = [&](const std::vector<int>& path,
                           RouteLoadColumn& column,
                           double& rc_out) {
        if (path.empty()) return false;
        std::vector<char> used(static_cast<std::size_t>(instance.V + 1), 0);
        StationSet set(instance.V);
        int mask = 0;
        double travel = instance.dist[0][path.front()];
        for (std::size_t pos = 0; pos < path.size(); ++pos) {
            const int station = path[pos];
            if (station < 1 || station > instance.V || used[station]) return false;
            used[station] = 1;
            set.add(station);
            if (station <= 31) mask |= 1 << (station - 1);
            if (pos > 0) travel += instance.dist[path[pos - 1]][station];
        }
        travel += instance.dist[path.back()][0];
        if (travel > instance.total_time_limit + 1e-9) return false;
        if (!columnAllowedByBranchPairs(set)) return false;

        const double cunit = instance.pickup_time + instance.drop_time;
        if (cunit <= 1e-12) return false;
        const int pickup_budget = static_cast<int>(
            std::floor((instance.total_time_limit - travel) / cunit + 1e-9));
        if (pickup_budget <= 0) return false;

        column = RouteLoadColumn{};
        column.vehicle = vehicle;
        column.column_kind = "elementary_feasible";
        column.elementary = true;
        column.relaxation_scope = "original_elementary";
        column.can_be_used_for_incumbent = true;
        column.can_be_used_for_lower_bound = true;
        column.mask = mask;
        column.station_set = set;
        column.path = path;
        column.q.assign(instance.V + 1, 0);
        column.travel = travel;

        int load = 0;
        int pickup = 0;
        bool has_operation = false;
        for (int station : path) {
            const int bit = station <= 31 ? (1 << (station - 1)) : 0;
            const double search_op = dualOperationCost(search_duals, station);
            const double pickup_coeff = search_duals.pickup_cost + search_op;
            const double drop_coeff = -search_op;
            const int pick_room = std::min({instance.initial[station],
                                            instance.Q[vehicle] - load,
                                            pickup_budget - pickup});
            const int drop_room = std::min(instance.capacity[station] - instance.initial[station],
                                           load);
            bool can_pick = pick_room > 0 &&
                (station > 31 || (options.forbid_pickup_station_mask & bit) == 0);
            bool can_drop = drop_room > 0 &&
                (station > 31 || (options.forbid_drop_station_mask & bit) == 0);
            if (can_drop && (!can_pick || drop_coeff < pickup_coeff - 1e-12)) {
                int amount = std::max(1, std::min(drop_room, instance.Q[vehicle]));
                column.q[station] = -amount;
                load -= amount;
                has_operation = true;
            } else if (can_pick) {
                int amount = std::max(1, std::min(pick_room, instance.Q[vehicle]));
                column.q[station] = amount;
                load += amount;
                pickup += amount;
                has_operation = true;
            }
        }
        if (!has_operation || pickup <= 0) return false;
        column.pickup = pickup;
        column.duration = travel + cunit * static_cast<double>(pickup);
        if (column.duration > instance.total_time_limit + 1e-9) return false;

        double rc = duals.constant + duals.travel_cost * travel;
        for (int station : path) {
            const int q = column.q[station];
            if (q > 0) {
                rc += (duals.pickup_cost + dualOperationCost(duals, station)) *
                    static_cast<double>(q);
            } else if (q < 0) {
                rc += (-dualOperationCost(duals, station)) *
                    static_cast<double>(-q);
            }
        }
        for (int station : path) rc += dualVisitCost(duals, station);
        rc += pathPairCost(duals, used) + pathSubsetRowCost(duals, used);
        column.reduced_cost = rc;
        rc_out = rc;
        return true;
    };

    auto relaxedLowerBoundCopy = [&](const RouteLoadColumn& elementary) {
        RouteLoadColumn relaxed = elementary;
        relaxed.column_kind = "ng_relaxed_lower_bound";
        relaxed.elementary = false;
        relaxed.relaxation_scope = "ng_route_relaxation";
        relaxed.can_be_used_for_incumbent = false;
        relaxed.can_be_used_for_lower_bound = true;
        relaxed.has_repeated_stations = false;
        relaxed.repeated_station_count = 0;
        return relaxed;
    };

    std::vector<std::pair<double, int>> ranked;
    ranked.reserve(static_cast<std::size_t>(instance.V));
    for (int station = 1; station <= instance.V; ++station) {
        if (!stationAllowedLarge(station)) continue;
        const double pickup_coeff = search_duals.pickup_cost + dualOperationCost(search_duals, station);
        const double drop_coeff = -dualOperationCost(search_duals, station);
        const double travel_score =
            instance.dist[0][station] + instance.dist[station][0];
        const double dual_score = dualVisitCost(search_duals, station) +
            std::min({0.0, pickup_coeff, drop_coeff});
        double score = travel_score;
        if (result.ng_neighborhood_mode == "dual-aware") {
            score = dual_score + 1e-6 * travel_score;
        } else if (result.ng_neighborhood_mode == "hybrid") {
            score = 0.5 * travel_score + dual_score;
        }
        ranked.push_back({score, station});
    }
    std::sort(ranked.begin(), ranked.end());
    const int seed_count = std::min<int>(
        static_cast<int>(ranked.size()),
        std::max(result.ng_size, std::min(instance.V, result.ng_size * 3)));
    const int max_rounds = std::max(1, options.dssr_max_rounds);
    const int max_path_len = std::max(1, std::min(instance.V, result.ng_size + 2));
    result.dssr_memory_total_initial =
        static_cast<long long>(instance.V) * result.ng_size;
    result.ng_memory_total = result.dssr_memory_total_initial;

    for (int round = 0; round < max_rounds; ++round) {
        ++result.dssr_rounds;
        const int local_ng = std::min(instance.V,
                                      result.ng_size + round * std::max(1, options.dssr_expand_per_round));
        if (round > 0) {
            result.dssr_memory_expansions += instance.V;
            result.dssr_repeated_station_events +=
                std::max<long long>(1, result.dssr_non_elementary_routes);
        }
        result.dssr_memory_total_final =
            static_cast<long long>(instance.V) * local_ng;
        for (int seed_pos = 0; seed_pos < seed_count; ++seed_pos) {
            if (timedOut()) {
                result.dssr_time_seconds =
                    std::chrono::duration<double>(Clock::now() - pricing_start).count();
                return result;
            }
            std::vector<int> path;
            path.reserve(static_cast<std::size_t>(max_path_len));
            std::vector<char> used(static_cast<std::size_t>(instance.V + 1), 0);
            int current = ranked[seed_pos].second;
            for (int step = 0; step < max_path_len; ++step) {
                if (used[current]) break;
                path.push_back(current);
                used[current] = 1;
                RouteLoadColumn candidate;
                double rc = 0.0;
                ++result.route_states;
                if (buildColumn(path, candidate, rc)) {
                    ++result.generated_columns;
                    ++result.elementary_columns_generated;
                    if (!result.has_column || rc < result.best_reduced_cost - 1e-12) {
                        result.has_column = true;
                        result.best_reduced_cost = rc;
                        result.best_column = candidate;
                    }
                    if (rc < -options.negative_tolerance) {
                        ++result.dssr_relaxed_negative_routes;
                        ++result.dssr_elementary_columns_found;
                        result.has_negative_column = true;
                        if (static_cast<int>(result.negative_columns.size()) <
                            std::max(1, options.max_returned_columns)) {
                            if (result.relaxed_rmp_enabled &&
                                static_cast<int>(result.relaxed_negative_columns.size()) <
                                    std::max(0, options.relaxed_columns_max_per_pricing)) {
                                RouteLoadColumn relaxed =
                                    relaxedLowerBoundCopy(candidate);
                                result.relaxed_negative_columns.push_back(relaxed);
                                result.negative_columns.push_back(relaxed);
                                ++result.relaxed_columns_generated;
                                ++result.relaxed_columns_inserted;
                                ++result.relaxed_columns_used_in_lb_rmp;
                            } else {
                                result.negative_columns.push_back(candidate);
                                ++result.elementary_columns_inserted;
                            }
                        }
                    }
                }
                int next_station = 0;
                double best_next = std::numeric_limits<double>::infinity();
                int considered = 0;
                int repeated_candidate = 0;
                for (const auto& entry : ranked) {
                    const int station = entry.second;
                    if (used[station]) {
                        if (repeated_candidate == 0) repeated_candidate = station;
                        continue;
                    }
                    const double neighborhood_penalty =
                        considered < local_ng ? 0.0 : 0.05 * considered;
                    const double dual_term =
                        (options.ng_neighborhood_mode == "dual-aware" ||
                         options.ng_neighborhood_mode == "hybrid")
                            ? entry.first : 0.0;
                    const double value = instance.dist[current][station] +
                        0.25 * (instance.dist[0][station] + instance.dist[station][0]) +
                        dual_term + neighborhood_penalty;
                    if (value < best_next) {
                        best_next = value;
                        next_station = station;
                    }
                    ++considered;
                    if (considered > std::max(local_ng * 4, 16)) break;
                }
                if (repeated_candidate != 0 && step >= local_ng) {
                    ++result.dssr_non_elementary_routes;
                    ++result.dssr_repeated_station_events;
                }
                if (next_station == 0) break;
                current = next_station;
            }
        }
        if (result.has_negative_column) break;
    }

    if (!result.has_column) result.best_reduced_cost = 0.0;
    result.dssr_no_negative_relaxed_route = !result.has_negative_column;
    result.complete = false;
    result.dssr_exact_closure_proved = false;
    result.dssr_stop_reason = result.has_negative_column
        ? "elementary_negative_column_found_final_exact_required"
        : "dssr_incomplete_final_exact_required";
    if ((result.pricing_engine == "ng-dssr" ||
         result.pricing_engine == "hybrid") &&
        instance.V <= 16 &&
        options.dssr_final_exact) {
        PricingOptions exact_options = options;
        exact_options.pricing_engine = "exact-label";
        const auto exact_start = Clock::now();
        PricingResult exact = ExactPricer(instance, vehicle, duals, exact_options, start).run();
        result.dssr_final_exact_verification_time +=
            std::chrono::duration<double>(Clock::now() - exact_start).count();
        result.cg_true_pricing_calls += 1;
        result.cg_true_pricing_columns_found += exact.has_negative_column ? 1 : 0;
        result.cg_final_true_pricing_rc = exact.best_reduced_cost;
        if (exact.complete) {
            result.complete = true;
            result.dssr_final_exact = true;
            result.dssr_exact_closure_proved = !exact.has_negative_column;
            result.dssr_stop_reason = exact.has_negative_column
                ? "exact_elementary_negative_column_found"
                : "exact_no_negative";
            if (!result.has_column || exact.best_reduced_cost < result.best_reduced_cost) {
                result.has_column = exact.has_column;
                result.best_reduced_cost = exact.best_reduced_cost;
                result.best_column = exact.best_column;
            }
            if (!exact.negative_columns.empty()) {
                result.negative_columns = exact.negative_columns;
                result.relaxed_negative_columns.clear();
            }
        }
        result.route_states += exact.route_states;
        result.operation_states += exact.operation_states;
        result.generated_columns += exact.generated_columns;
        result.elementary_columns_generated += exact.elementary_columns_generated;
        result.elementary_columns_inserted += exact.elementary_columns_inserted;
    }

    result.has_negative_column = result.has_column &&
        result.best_reduced_cost < -options.negative_tolerance;
    result.best_new_reduced_cost = result.best_reduced_cost;
    result.negative_new_projection_count =
        result.has_negative_column ? static_cast<long long>(result.negative_columns.size()) : 0;
    result.elementary_pricing_closed =
        result.complete && result.dssr_exact_closure_proved && !result.has_negative_column;
    result.dssr_exact_elementary_closed = result.elementary_pricing_closed;
    result.ng_relaxed_pricing_calls = result.dssr_rounds;
    result.ng_relaxed_best_reduced_cost = result.best_reduced_cost;
    result.ng_relaxed_labels_processed = result.route_states;
    result.ng_relaxed_labels_pruned =
        result.support_duration_pruned_labels +
        result.support_duration_strong_pruned_labels;
    result.dssr_refinement_rounds_for_lb = std::max(0, result.dssr_rounds - 1);
    result.dssr_lb_before_refinement = 0.0;
    result.dssr_lb_after_refinement = 0.0;
    result.ng_relaxed_pricing_closed =
        result.relaxed_rmp_enabled && result.complete &&
        result.dssr_exact_closure_proved && !result.has_negative_column;
    if (!result.relaxed_rmp_enabled) {
        result.ng_relaxed_pricing_closed = false;
    }
    result.pricing_closure_status =
        result.complete && result.dssr_exact_closure_proved && !result.has_negative_column
            ? "exact_no_negative"
            : (result.has_negative_column ? "negative_columns_remaining" : "dssr_incomplete");
    result.cg_stabilized_pricing_calls =
        stabilization == "none" ? 0 : result.dssr_rounds;
    result.cg_true_pricing_calls += stabilization == "none" ? result.dssr_rounds : 1;
    result.cg_stabilization_columns_found =
        stabilization == "none" ? 0 : result.dssr_elementary_columns_found;
    result.cg_true_pricing_columns_found +=
        stabilization == "none" ? result.dssr_elementary_columns_found : 0;
    result.cg_dual_center_updates =
        stabilization == "none" ? 0 : std::max(0, result.dssr_rounds - 1);
    result.cg_dual_oscillation_metric =
        std::fabs(duals.constant - search_duals.constant);
    result.cg_true_negative_columns_inserted =
        result.negative_new_projection_count;
    result.dssr_time_seconds =
        std::chrono::duration<double>(Clock::now() - pricing_start).count();
    result.cg_stabilization_time_seconds =
        stabilization == "none" ? 0.0 : result.dssr_time_seconds;
    return result;
}

} // namespace

PricingResult priceRouteLoadColumnExact(const Instance& instance,
                                        int vehicle,
                                        const PricingDuals& duals,
                                        const PricingOptions& options,
                                        Clock::time_point start) {
    ExactPricer pricer(instance, vehicle, duals, options, start);
    return pricer.run();
}

} // namespace ebrp
