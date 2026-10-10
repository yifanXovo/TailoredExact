#include "PhysicalWitnessValidation.hpp"
#include "Evaluator.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>

namespace ebrp {
namespace {
using Integer = std::int64_t;
void requireInput(const Instance& in, const std::vector<RoutePlan>& routes,
                  double lambda) {
    if (in.V < 1 || in.V == std::numeric_limits<int>::max() || in.M < 1)
        throw std::invalid_argument("Round95 invalid instance dimensions");
    const auto size = static_cast<std::size_t>(in.V + 1);
    if (!std::isfinite(lambda) || !std::isfinite(in.total_time_limit) ||
        !std::isfinite(in.pickup_time) || !std::isfinite(in.drop_time) ||
        in.pickup_time < 0 || in.drop_time < 0 ||
        in.Q.size() != static_cast<std::size_t>(in.M) ||
        in.initial.size() != size || in.capacity.size() != size ||
        in.target.size() != size || in.weights.size() != size ||
        in.dist.size() != size || routes.size() != static_cast<std::size_t>(in.M))
        throw std::invalid_argument("Round95 invalid instance or route dimensions");
    for (int q : in.Q)
        if (q < 0) throw std::invalid_argument("Round95 negative vehicle capacity");
    for (int i = 0; i <= in.V; ++i) {
        if (in.dist[i].size() != size)
            throw std::invalid_argument("Round95 distance dimensions");
        for (double d : in.dist[i])
            if (!std::isfinite(d) || d < 0)
                throw std::invalid_argument("Round95 nonfinite or negative travel");
        if (i && (in.target[i] <= 0 || in.capacity[i] < 0 ||
                  in.initial[i] < 0 || in.initial[i] > in.capacity[i] ||
                  !std::isfinite(in.weights[i])))
            throw std::invalid_argument("Round95 invalid stock, target or weight");
    }
    std::vector<bool> seen_vehicle(in.M, false), seen_station(size, false);
    for (const auto& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= in.M ||
            seen_vehicle[route.vehicle] || route.nodes.size() < 2 ||
            route.nodes.front() != 0 || route.nodes.back() != 0 ||
            route.operations.size() + 2 != route.nodes.size())
            throw std::invalid_argument("Round95 invalid depot route or vehicle");
        seen_vehicle[route.vehicle] = true;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            if (station <= 0 || station > in.V || seen_station[station])
                throw std::invalid_argument("Round95 duplicate or illegal station");
            seen_station[station] = true;
            if (std::count_if(route.operations.begin(), route.operations.end(),
                [station](const StopOperation& op) { return op.station == station; }) != 1)
                throw std::invalid_argument("Round95 operation mismatch");
        }
    }
    if (std::find(seen_vehicle.begin(), seen_vehicle.end(), false) != seen_vehicle.end())
        throw std::invalid_argument("Round95 missing vehicle route");
}

} // namespace

bool physicalOperationsFitEvaluatorIntegerDomain(const Instance& in, const std::vector<RoutePlan>& routes) {
    const Integer limit = std::numeric_limits<int>::max();
    for (const auto& route : routes) {
        Integer pickups = 0, drops = 0, load = 0;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            const auto op = std::find_if(route.operations.begin(), route.operations.end(),
                [station](const StopOperation& candidate) { return candidate.station == station; });
            if (op == route.operations.end() || op->pickup < 0 || op->drop < 0 ||
                (op->pickup > 0 && op->drop > 0) ||
                (op->pickup == 0 && op->drop == 0)) return false;
            const Integer final_inventory = Integer(in.initial[station]) -
                op->pickup + op->drop;
            if (final_inventory < -limit || final_inventory > limit) return false;
            pickups += op->pickup; drops += op->drop;
            load += Integer(op->pickup) - op->drop;
            if (pickups > limit || drops > limit ||
                load < -limit || load > limit) return false;
        }
    }
    return true;
}

Verification verifyCompletePhysicalStartingWitness(
    const Instance& in, const std::vector<RoutePlan>& routes, double lambda) {
    requireInput(in, routes, lambda);
    if (!physicalOperationsFitEvaluatorIntegerDomain(in, routes))
        throw std::invalid_argument("Round95 starting witness exceeds Evaluator int domain");
    const auto checked = verifySolution(in, routes, lambda);
    if (!checked.feasible || !checked.errors.empty() ||
        !checked.original_objective_recomputed)
        throw std::invalid_argument("Round95 invalid original physical witness");
    return checked;
}

} // namespace ebrp
