#include "Round93CoQuantityDescent.hpp"

#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
using Integer = std::int64_t;
constexpr double kStrictImprovement = 1e-12;

void requireInput(const Instance& in, const std::vector<RoutePlan>& routes,
                  double lambda) {
    if (in.V < 1 || in.V == std::numeric_limits<int>::max() || in.M < 1)
        throw std::invalid_argument("Round93 co-line invalid instance dimensions");
    const auto size = static_cast<std::size_t>(in.V + 1);
    if (!std::isfinite(lambda) ||
        !std::isfinite(in.total_time_limit) ||
        !std::isfinite(in.pickup_time) || !std::isfinite(in.drop_time) ||
        in.pickup_time < 0 || in.drop_time < 0 ||
        in.Q.size() != static_cast<std::size_t>(in.M) ||
        in.initial.size() != size || in.capacity.size() != size ||
        in.target.size() != size || in.weights.size() != size ||
        in.dist.size() != size || routes.size() != static_cast<std::size_t>(in.M))
        throw std::invalid_argument("Round93 co-line invalid instance or route dimensions");
    for (int q : in.Q)
        if (q < 0) throw std::invalid_argument("Round93 co-line negative vehicle capacity");
    for (int i = 0; i <= in.V; ++i) {
        if (in.dist[i].size() != size)
            throw std::invalid_argument("Round93 co-line distance dimensions");
        for (double d : in.dist[i])
            if (!std::isfinite(d) || d < 0)
                throw std::invalid_argument("Round93 co-line nonfinite or negative travel");
        if (i && (in.target[i] <= 0 || in.capacity[i] < 0 ||
                  in.initial[i] < 0 || in.initial[i] > in.capacity[i] ||
                  !std::isfinite(in.weights[i])))
            throw std::invalid_argument("Round93 co-line invalid stock, target or weight");
    }
    std::vector<bool> seen_vehicle(in.M, false), seen_station(size, false);
    for (const auto& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= in.M ||
            seen_vehicle[route.vehicle] || route.nodes.size() < 2 ||
            route.nodes.front() != 0 || route.nodes.back() != 0 ||
            route.operations.size() + 2 != route.nodes.size())
            throw std::invalid_argument("Round93 co-line invalid depot route or vehicle");
        seen_vehicle[route.vehicle] = true;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            if (station <= 0 || station > in.V || seen_station[station])
                throw std::invalid_argument("Round93 co-line duplicate or illegal station");
            seen_station[station] = true;
            if (std::count_if(route.operations.begin(), route.operations.end(),
                [station](const StopOperation& op) { return op.station == station; }) != 1)
                throw std::invalid_argument("Round93 co-line operation mismatch");
        }
    }
    if (std::find(seen_vehicle.begin(), seen_vehicle.end(), false) != seen_vehicle.end())
        throw std::invalid_argument("Round93 co-line missing vehicle route");
}

bool expired(const SolveOptions* whole_run, Round93CoQuantityStats& stats) {
    if (whole_run && processWorkDeadlineReached(*whole_run))
        stats.deadline_reached = true;
    return stats.deadline_reached;
}

// Evaluator uses int accumulators for route load and pickup/drop totals.
// Refuse an arithmetic domain where those additions could overflow before
// calling it; this is a fail-closed boundary, not a change to its tolerance.
bool evaluatorIntegerDomain(const Instance& in, const std::vector<RoutePlan>& routes) {
    const Integer limit = std::numeric_limits<int>::max();
    for (const auto& route : routes) {
        Integer pickups = 0, drops = 0, load = 0;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            const auto op = std::find_if(route.operations.begin(), route.operations.end(),
                [station](const StopOperation& candidate) { return candidate.station == station; });
            if (op == route.operations.end()) return false;
            if (op->pickup < 0 || op->drop < 0 ||
                (op->pickup > 0 && op->drop > 0) ||
                (op->pickup == 0 && op->drop == 0)) return false;
            const Integer final_inventory = Integer(in.initial[station]) -
                op->pickup + op->drop;
            if (final_inventory < -limit || final_inventory > limit) return false;
            pickups += op->pickup; drops += op->drop;
            load += Integer(op->pickup) - op->drop;
            if (pickups < 0 || pickups > limit || drops < 0 || drops > limit ||
                load < -limit || load > limit) return false;
        }
    }
    return true;
}

std::vector<RoutePlan> materialize(const std::vector<RoutePlan>& routes,
                                   int a, int b, Integer t) {
    if (a <= 0 || b <= a || t == 0)
        throw std::invalid_argument("Round93 co-line empty or unordered change");
    auto out = routes;
    int changed = 0;
    for (auto& route : out) {
        for (auto& op : route.operations) {
            if (op.station != a && op.station != b) continue;
            const Integer signed_before = Integer(op.pickup) - op.drop;
            const Integer signed_after = signed_before - t;
            if (signed_after < -Integer(std::numeric_limits<int>::max()) ||
                signed_after > Integer(std::numeric_limits<int>::max()))
                throw std::overflow_error("Round93 co-line signed operation exceeds int");
            op.pickup = static_cast<int>(std::max<Integer>(0, signed_after));
            op.drop = static_cast<int>(std::max<Integer>(0, -signed_after));
            if (signed_after == 0)
                route.nodes.erase(std::remove(route.nodes.begin(), route.nodes.end(), op.station),
                                  route.nodes.end());
            ++changed;
        }
        route.operations.erase(std::remove_if(route.operations.begin(), route.operations.end(),
            [](const StopOperation& op) { return op.pickup == 0 && op.drop == 0; }),
            route.operations.end());
    }
    if (changed != 2)
        throw std::invalid_argument("Round93 co-line station absent or repeated");
    return out;
}

std::string rejectReason(const Verification& checked) {
    std::string reason;
    auto add = [&](const char* label) {
        if (!reason.empty()) reason += '|';
        reason += label;
    };
    if (!checked.routes_start_end_depot || !checked.station_disjoint) add("route");
    if (!checked.load_feasible) add("load");
    if (!checked.station_feasible) add("stock_or_operation");
    if (!checked.duration_feasible) add("duration");
    if (!checked.original_objective_recomputed) add("nonfinite_objective");
    if (!checked.errors.empty() && reason.empty()) add("verifier_errors");
    if (reason.empty() && !checked.feasible) add("other_physical");
    return reason;
}
} // namespace

Verification verifyRound93StartingWitness(
    const Instance& in, const std::vector<RoutePlan>& routes, double lambda) {
    requireInput(in, routes, lambda);
    if (!evaluatorIntegerDomain(in, routes))
        throw std::invalid_argument("Round93 co-line starting witness exceeds Evaluator int domain");
    const auto checked = verifySolution(in, routes, lambda);
    if (!checked.feasible || !checked.errors.empty() ||
        !checked.original_objective_recomputed)
        throw std::invalid_argument("Round93 co-line invalid original physical witness");
    return checked;
}

Round93CoQuantityChoice bestRound93CoQuantityChange(
    const Instance& in, const std::vector<RoutePlan>& routes, double lambda,
    Round93CoQuantityStats& stats, const SolveOptions* whole_run,
    const Round93PointObserver& observer) {
    const auto baseline = verifyRound93StartingWitness(in, routes, lambda);
    ++stats.passes;
    Round93CoQuantityChoice best;
    if (expired(whole_run, stats)) return {};
    std::vector<int> stations;
    for (const auto& route : routes)
        for (const auto& op : route.operations) stations.push_back(op.station);
    std::sort(stations.begin(), stations.end());
    for (std::size_t ia = 0; ia < stations.size(); ++ia) {
        const int a = stations[ia];
        for (std::size_t ib = ia + 1; ib < stations.size(); ++ib) {
            if (expired(whole_run, stats)) return {};
            const int b = stations[ib];
            ++stats.station_pairs;
            const Integer lo = std::max(-Integer(baseline.final_inventory[a]),
                                        -Integer(baseline.final_inventory[b]));
            const Integer hi = std::min(Integer(in.capacity[a]) - baseline.final_inventory[a],
                                        Integer(in.capacity[b]) - baseline.final_inventory[b]);
            for (Integer t = lo; t <= hi; ++t) {
                if (t == 0) continue;
                if (expired(whole_run, stats)) return {};
                ++stats.integer_points;
                const auto candidate = materialize(routes, a, b, t);
                Round93CoQuantityPoint point;
                point.pass = stats.passes;
                point.first = a; point.second = b; point.delta = t;
                point.inventory_first = static_cast<int>(Integer(baseline.final_inventory[a]) + t);
                point.inventory_second = static_cast<int>(Integer(baseline.final_inventory[b]) + t);
                if (!evaluatorIntegerDomain(in, candidate)) {
                    point.rejection_reason = "evaluator_integer_domain";
                    ++stats.integer_domain_rejections;
                    if (observer) observer(point);
                    stats.verification_failed = true;
                    stats.rejection_reason = "candidate_exceeds_original_Evaluator_int_domain";
                    return {};
                }
                const auto checked = verifySolution(in, candidate, lambda);
                point.physical_checked = true;
                point.feasible = checked.feasible && checked.errors.empty();
                point.load_feasible = checked.load_feasible;
                point.station_feasible = checked.station_feasible;
                point.duration_feasible = checked.duration_feasible;
                point.objective_recomputed = checked.original_objective_recomputed;
                point.objective = checked.objective; point.G = checked.G; point.P = checked.P;
                if (!point.feasible) {
                    point.rejection_reason = rejectReason(checked);
                    stats.load_rejections += !checked.load_feasible;
                    stats.station_rejections += !checked.station_feasible;
                    stats.duration_rejections += !checked.duration_feasible;
                    stats.nonfinite_rejections += !checked.original_objective_recomputed;
                    stats.other_physical_rejections +=
                        checked.feasible == false && checked.load_feasible &&
                        checked.station_feasible && checked.duration_feasible &&
                        checked.original_objective_recomputed;
                } else {
                    ++stats.feasible_points;
                    if (!(baseline.objective - checked.objective > kStrictImprovement))
                        point.rejection_reason = "no_strict_original_F_improvement";
                    else {
                        const Round93CoQuantityChoice choice{true, a, b, t, checked.objective};
                        if (!best.found || choice.objective < best.objective ||
                            (choice.objective == best.objective &&
                             std::tie(a, b, t) <
                             std::tie(best.first, best.second, best.delta))) best = choice;
                    }
                }
                if (observer) observer(point);
            }
        }
    }
    // An observer or the final verification may cross the whole-run deadline.
    // The caller must not accept a best point from a now-interrupted pass.
    if (expired(whole_run, stats)) return {};
    return best;
}

std::vector<RoutePlan> applyRound93CoQuantityChange(
    const std::vector<RoutePlan>& routes, const Round93CoQuantityChoice& choice) {
    if (!choice.found)
        throw std::invalid_argument("Round93 co-line cannot apply absent choice");
    return materialize(routes, choice.first, choice.second, choice.delta);
}

Round93CoQuantityResult runRound93CoQuantityDescent(
    const Instance& in, const SolveOptions& options,
    const std::vector<RoutePlan>& routes, const Round93PointObserver& observer) {
    Round93CoQuantityResult out;
    out.routes = routes;
    out.verification = verifyRound93StartingWitness(in, routes, options.lambda);
    for (;;) {
        const auto choice = bestRound93CoQuantityChange(
            in, out.routes, options.lambda, out.stats, &options, observer);
        if (out.stats.deadline_reached) break;
        if (out.stats.verification_failed) break;
        if (!choice.found) { out.stats.exhausted = true; break; }
        auto candidate = applyRound93CoQuantityChange(out.routes, choice);
        if (!evaluatorIntegerDomain(in, candidate)) {
            out.stats.verification_failed = true;
            out.stats.rejection_reason = "accepted_choice_evaluator_integer_domain";
            break;
        }
        auto checked = verifySolution(in, candidate, options.lambda);
        if (!checked.feasible || !checked.errors.empty() ||
            !checked.original_objective_recomputed ||
            checked.objective != choice.objective ||
            !(out.verification.objective - checked.objective > kStrictImprovement)) {
            out.stats.verification_failed = true;
            out.stats.rejection_reason = "accepted_choice_physical_or_original_F_recheck_failed";
            break;
        }
        if (expired(&options, out.stats)) break;
        for (const auto& route : out.routes)
            for (const auto& op : route.operations)
                if (op.station == choice.first || op.station == choice.second) {
                    const Integer old_signed = Integer(op.pickup) - op.drop;
                    const Integer next_signed = old_signed - choice.delta;
                    out.stats.deleted_stops += next_signed == 0;
                    out.stats.sign_flips +=
                        (old_signed > 0 && next_signed < 0) ||
                        (old_signed < 0 && next_signed > 0);
                }
        ++out.stats.accepted;
        out.accepted_choices.push_back(choice);
        out.routes = std::move(candidate);
        out.verification = std::move(checked);
    }
    return out;
}
} // namespace ebrp
