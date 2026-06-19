#include "Evaluator.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <unordered_set>

namespace ebrp {
namespace {

void addError(Verification& v, const std::string& text) {
    v.errors.push_back(text);
}

const StopOperation* findOperation(const RoutePlan& route, int station) {
    for (const auto& op : route.operations) {
        if (op.station == station) return &op;
    }
    return nullptr;
}

} // namespace

Verification verifySolution(const Instance& instance,
                            const std::vector<RoutePlan>& routes,
                            double lambda,
                            double objective_tolerance) {
    Verification v;
    v.routes_start_end_depot = true;
    v.station_disjoint = true;
    v.load_feasible = true;
    v.station_feasible = true;
    v.duration_feasible = true;
    v.final_inventory = instance.initial;

    std::vector<int> station_seen(instance.V + 1, 0);
    v.route_travel_time.assign(instance.M, 0.0);
    v.route_operation_time.assign(instance.M, 0.0);
    v.route_duration.assign(instance.M, 0.0);

    for (const RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M) {
            v.routes_start_end_depot = false;
            addError(v, "Route has invalid vehicle index");
            continue;
        }
        if (route.nodes.size() < 2 || route.nodes.front() != 0 || route.nodes.back() != 0) {
            v.routes_start_end_depot = false;
            addError(v, "Route does not start and end at depot");
        }

        std::unordered_set<int> route_stations;
        double travel = 0.0;
        for (std::size_t i = 1; i < route.nodes.size(); ++i) {
            const int a = route.nodes[i - 1];
            const int b = route.nodes[i];
            if (a < 0 || a > instance.V || b < 0 || b > instance.V) {
                v.routes_start_end_depot = false;
                addError(v, "Route contains node outside instance range");
                continue;
            }
            travel += instance.dist[a][b];
            if (b != 0) {
                if (!route_stations.insert(b).second) {
                    v.station_disjoint = false;
                    addError(v, "Route repeats station " + std::to_string(b));
                }
                station_seen[b]++;
            }
        }

        int load = 0;
        int total_pick = 0;
        int total_station_drop = 0;
        for (std::size_t idx = 1; idx + 1 < route.nodes.size(); ++idx) {
            const int station = route.nodes[idx];
            const StopOperation* op = findOperation(route, station);
            if (op == nullptr) {
                v.station_feasible = false;
                addError(v, "Visited station has no operation: " + std::to_string(station));
                continue;
            }
            if (op->pickup < 0 || op->drop < 0 || (op->pickup > 0 && op->drop > 0) ||
                (op->pickup == 0 && op->drop == 0)) {
                v.station_feasible = false;
                addError(v, "Invalid operation at station " + std::to_string(station));
            }
            load += op->pickup;
            load -= op->drop;
            total_pick += op->pickup;
            total_station_drop += op->drop;
            if (load < 0 || load > instance.Q[route.vehicle]) {
                v.load_feasible = false;
                addError(v, "Vehicle load infeasible on vehicle " + std::to_string(route.vehicle));
            }
            v.final_inventory[station] -= op->pickup;
            v.final_inventory[station] += op->drop;
        }

        for (const auto& op : route.operations) {
            if (op.station <= 0 || op.station > instance.V || !route_stations.count(op.station)) {
                v.station_feasible = false;
                addError(v, "Operation listed for unvisited station " + std::to_string(op.station));
            }
        }

        const int depot_unload = load;
        if (depot_unload < 0) {
            v.load_feasible = false;
            addError(v, "Negative final vehicle load");
        }
        const double operation_time = instance.pickup_time * total_pick
            + instance.drop_time * total_station_drop
            + instance.drop_time * depot_unload;
        const double duration = travel + operation_time;
        v.route_travel_time[route.vehicle] = travel;
        v.route_operation_time[route.vehicle] = operation_time;
        v.route_duration[route.vehicle] = duration;
        if (duration > instance.total_time_limit + 1e-7) {
            v.duration_feasible = false;
            addError(v, "Route duration exceeds T on vehicle " + std::to_string(route.vehicle));
        }
    }

    for (int i = 1; i <= instance.V; ++i) {
        if (station_seen[i] > 1) {
            v.station_disjoint = false;
            addError(v, "Station served by multiple vehicles: " + std::to_string(i));
        }
        if (v.final_inventory[i] < 0 || v.final_inventory[i] > instance.capacity[i]) {
            v.station_feasible = false;
            addError(v, "Final inventory outside capacity at station " + std::to_string(i));
        }
    }

    ObjectiveParts parts = computeObjectiveParts(instance, v.final_inventory, lambda);
    v.G = parts.G;
    v.P = parts.P;
    v.objective = parts.objective;
    v.objective_matches = std::isfinite(v.objective);
    if (!v.objective_matches || std::fabs(v.objective - parts.objective) > objective_tolerance) {
        v.objective_matches = false;
    }

    v.feasible = v.routes_start_end_depot && v.station_disjoint && v.load_feasible
        && v.station_feasible && v.duration_feasible && v.objective_matches;
    return v;
}

} // namespace ebrp
