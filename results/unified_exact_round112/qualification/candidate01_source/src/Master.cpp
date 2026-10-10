#include "Master.hpp"

#include <algorithm>
#include <chrono>
#include <limits>
#include <string>
#include <unordered_map>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

struct MasterState {
    int mask = 0;
    std::vector<int> y;
    std::vector<int> selected;
};

void appendInt(std::string& key, int value) {
    for (int shift = 0; shift < 32; shift += 8) {
        key.push_back(static_cast<char>((static_cast<unsigned int>(value) >> shift) & 0xffU));
    }
}

std::string stateKey(int mask, const std::vector<int>& y, int V) {
    std::string key;
    key.reserve((V + 2) * sizeof(int));
    appendInt(key, mask);
    for (int i = 1; i <= V; ++i) appendInt(key, y[i]);
    return key;
}

bool deadlineReached(Clock::time_point start, double limit_seconds) {
    if (limit_seconds <= 0.0) return false;
    return std::chrono::duration<double>(Clock::now() - start).count() >= limit_seconds;
}

std::vector<RoutePlan> buildRoutes(
    const Instance& instance,
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    const std::vector<int>& selected) {
    std::vector<RoutePlan> routes;
    routes.reserve(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        const int col_idx = (k < static_cast<int>(selected.size())) ? selected[k] : -1;
        if (col_idx >= 0 && col_idx < static_cast<int>(columns_by_vehicle[k].size())) {
            const RouteLoadColumn& col = columns_by_vehicle[k][col_idx];
            for (int station : col.path) {
                route.nodes.push_back(station);
                StopOperation op;
                op.station = station;
                if (col.q[station] > 0) op.pickup = col.q[station];
                if (col.q[station] < 0) op.drop = -col.q[station];
                if (op.pickup > 0 || op.drop > 0) route.operations.push_back(op);
            }
        }
        route.nodes.push_back(0);
        routes.push_back(std::move(route));
    }
    return routes;
}

} // namespace

RestrictedMasterResult solveRestrictedMasterExact(
    const Instance& instance,
    const std::vector<std::vector<RouteLoadColumn>>& columns_by_vehicle,
    double lambda,
    double time_limit_seconds,
    Clock::time_point start) {
    RestrictedMasterResult out;
    out.best_parts.objective = std::numeric_limits<double>::infinity();
    if (static_cast<int>(columns_by_vehicle.size()) != instance.M) {
        out.complete = false;
        return out;
    }

    const int full_mask = (1 << instance.V) - 1;
    std::vector<MasterState> states;
    MasterState root;
    root.y = instance.initial;
    root.selected.assign(instance.M, -1);
    states.push_back(root);

    for (int k = 0; k < instance.M; ++k) {
        std::vector<std::vector<int>> buckets(1 << instance.V);
        for (int idx = 0; idx < static_cast<int>(columns_by_vehicle[k].size()); ++idx) {
            const int mask = columns_by_vehicle[k][idx].mask;
            if (mask > 0 && mask <= full_mask) buckets[mask].push_back(idx);
        }

        std::unordered_map<std::string, MasterState> next;
        next.reserve(states.size() * 2 + 1);
        for (const MasterState& state : states) {
            if ((out.states_processed & 0xffff) == 0 &&
                deadlineReached(start, time_limit_seconds)) {
                out.complete = false;
                return out;
            }
            MasterState skip = state;
            skip.selected[k] = -1;
            next.emplace(stateKey(skip.mask, skip.y, instance.V), std::move(skip));

            const int complement = full_mask ^ state.mask;
            for (int sub = complement; sub > 0; sub = (sub - 1) & complement) {
                const auto& bucket = buckets[sub];
                if (bucket.empty()) continue;
                for (int col_idx : bucket) {
                    const RouteLoadColumn& col = columns_by_vehicle[k][col_idx];
                    MasterState ns = state;
                    ns.mask |= col.mask;
                    ns.selected[k] = col_idx;
                    bool inventory_ok = true;
                    for (int i = 1; i <= instance.V; ++i) {
                        ns.y[i] -= col.q[i];
                        if (ns.y[i] < 0 || ns.y[i] > instance.capacity[i]) {
                            inventory_ok = false;
                            break;
                        }
                    }
                    if (!inventory_ok) continue;
                    std::string key = stateKey(ns.mask, ns.y, instance.V);
                    if (next.find(key) == next.end()) next.emplace(std::move(key), std::move(ns));
                    ++out.states_processed;
                }
            }
        }
        states.clear();
        states.reserve(next.size());
        for (auto& kv : next) states.push_back(std::move(kv.second));
    }

    for (const MasterState& state : states) {
        ObjectiveParts parts = computeObjectiveParts(instance, state.y, lambda);
        if (parts.objective < out.best_parts.objective - 1e-12) {
            out.best_parts = parts;
            out.best_final_inventory = state.y;
            out.selected_column_by_vehicle = state.selected;
            out.has_solution = true;
        }
    }
    if (out.has_solution) {
        out.routes = buildRoutes(instance, columns_by_vehicle, out.selected_column_by_vehicle);
    }
    return out;
}

} // namespace ebrp
