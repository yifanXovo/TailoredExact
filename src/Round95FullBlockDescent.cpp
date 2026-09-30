#include "Round95FullBlockDescent.hpp"

#include "Evaluator.hpp"
#include "PhysicalWitnessValidation.hpp"
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

void addCount(std::uint64_t& dst, std::uint64_t increment) {
    if (increment > std::numeric_limits<std::uint64_t>::max() - dst)
        throw std::overflow_error("Round95 diagnostic count overflow");
    dst += increment;
}

bool expired(const SolveOptions* whole_run, Round95Stats& stats) {
    if (whole_run && processWorkDeadlineReached(*whole_run))
        stats.deadline_reached = true;
    return stats.deadline_reached;
}

void appendBand(Round95Band& band, Integer load, Integer capacity) {
    const Integer low = load - capacity, high = load;
    if (!band.present) {
        band.present = true;
        band.low = low;
        band.high = high;
    } else {
        band.low = std::max(band.low, low);
        band.high = std::min(band.high, high);
    }
    addCount(band.prefixes, 1);
}

Round95PairDomain loadDomain(const Instance& in,
    const std::vector<RoutePlan>& routes, const Verification& baseline,
    std::uint64_t pass, int a, int b) {
    Round95PairDomain domain;
    domain.pass = pass;
    domain.first = a; domain.second = b;
    domain.old_first = baseline.final_inventory[a];
    domain.old_second = baseline.final_inventory[b];
    domain.capacity_first = in.capacity[a];
    domain.capacity_second = in.capacity[b];
    domain.rectangle_points =
        (std::uint64_t(in.capacity[a]) + 1) * (std::uint64_t(in.capacity[b]) + 1) - 1;
    for (const auto& route : routes) {
        Integer load = 0;
        bool passed_a = false, passed_b = false;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            const auto op = std::find_if(route.operations.begin(), route.operations.end(),
                [station](const StopOperation& candidate) { return candidate.station == station; });
            // Baseline structure and int domain have already been validated.
            load += Integer(op->pickup) - op->drop;
            passed_a |= station == a;
            passed_b |= station == b;
            if (passed_a && passed_b) appendBand(domain.band11, load, in.Q[route.vehicle]);
            else if (passed_a) appendBand(domain.band10, load, in.Q[route.vehicle]);
            else if (passed_b) appendBand(domain.band01, load, in.Q[route.vehicle]);
        }
    }
    return domain;
}

Round95InventoryInterval inventoryInterval(const Round95PairDomain& domain, int u) {
    Round95InventoryInterval out;
    out.pass = domain.pass;
    out.first = domain.first; out.second = domain.second;
    out.inventory_first = u;
    const Integer da = Integer(u) - domain.old_first;
    Integer low = 0, high = domain.capacity_second;
    if (domain.band10.present &&
        (da < domain.band10.low || da > domain.band10.high)) high = -1;
    if (domain.band01.present) {
        low = std::max(low, Integer(domain.old_second) + domain.band01.low);
        high = std::min(high, Integer(domain.old_second) + domain.band01.high);
    }
    if (domain.band11.present) {
        low = std::max(low, Integer(domain.old_second) + domain.band11.low - da);
        high = std::min(high, Integer(domain.old_second) + domain.band11.high - da);
    }
    // Clamp only the published empty interval. Every nonempty endpoint is a
    // valid int inventory from [0, C_b].
    if (low > high) {
        out.low_second = 0; out.high_second = -1;
    } else {
        out.low_second = static_cast<int>(low);
        out.high_second = static_cast<int>(high);
        out.surviving_points = static_cast<std::uint64_t>(high - low + 1);
        if (u == domain.old_first && low <= domain.old_second &&
            domain.old_second <= high) --out.surviving_points;
    }
    return out;
}

std::vector<RoutePlan> materialize(const Instance& in,
    const std::vector<RoutePlan>& routes, int a, int b, int u, int v) {
    if (a <= 0 || b <= a || b > in.V || u < 0 || v < 0 ||
        u > in.capacity[a] || v > in.capacity[b])
        throw std::invalid_argument("Round95 invalid inventory change");
    auto out = routes;
    int changed = 0;
    for (auto& route : out) {
        for (auto& op : route.operations) {
            if (op.station != a && op.station != b) continue;
            const int inventory = op.station == a ? u : v;
            const Integer signed_after = Integer(in.initial[op.station]) - inventory;
            const Integer limit = std::numeric_limits<int>::max();
            if (signed_after < -limit || signed_after > limit)
                throw std::overflow_error("Round95 signed operation exceeds int");
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
        throw std::invalid_argument("Round95 station absent or repeated");
    return out;
}

std::string rejectReason(const Verification& checked) {
    std::string reason;
    auto add = [&](const char* value) {
        if (!reason.empty()) reason += '|';
        reason += value;
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

Verification verifyRound95StartingWitness(
    const Instance& in, const std::vector<RoutePlan>& routes, double lambda) {
    return verifyCompletePhysicalStartingWitness(in, routes, lambda);
}

Round95Choice bestRound95FullBlockChange(
    const Instance& in, const std::vector<RoutePlan>& routes, double lambda,
    Round95Stats& stats, const SolveOptions* whole_run,
    const Round95Observer& observer) {
    const auto baseline = verifyRound95StartingWitness(in, routes, lambda);
    addCount(stats.passes, 1);
    Round95Choice best;
    if (expired(whole_run, stats)) return {};
    std::vector<int> stations;
    for (const auto& route : routes)
        for (const auto& op : route.operations) stations.push_back(op.station);
    std::sort(stations.begin(), stations.end());
    for (std::size_t ia = 0; ia < stations.size(); ++ia) {
        for (std::size_t ib = ia + 1; ib < stations.size(); ++ib) {
            if (expired(whole_run, stats)) return {};
            const int a = stations[ia], b = stations[ib];
            const auto domain = loadDomain(in, routes, baseline, stats.passes, a, b);
            addCount(stats.station_pairs, 1);
            addCount(stats.rectangle_points, domain.rectangle_points);
            if (observer.pair) observer.pair(domain);
            if (expired(whole_run, stats)) return {};
            for (Integer next_u = 0; next_u <= in.capacity[a]; ++next_u) {
                if (expired(whole_run, stats)) return {};
                const int u = static_cast<int>(next_u);
                const auto interval = inventoryInterval(domain, u);
                addCount(stats.load_pruned,
                         static_cast<std::uint64_t>(in.capacity[b]) + 1 -
                         (u == baseline.final_inventory[a] ? 1 : 0) -
                         interval.surviving_points);
                if (observer.interval) observer.interval(interval);
                if (expired(whole_run, stats)) return {};
                for (Integer next_v = interval.low_second;
                     next_v <= interval.high_second; ++next_v) {
                    if (u == baseline.final_inventory[a] &&
                        next_v == baseline.final_inventory[b]) continue;
                    if (expired(whole_run, stats)) return {};
                    const int v = static_cast<int>(next_v);
                    addCount(stats.candidate_points, 1);
                    Round95Point point;
                    point.pass = stats.passes; point.first = a; point.second = b;
                    point.inventory_first = u; point.inventory_second = v;
                    const auto candidate = materialize(in, routes, a, b, u, v);
                    if (!physicalOperationsFitEvaluatorIntegerDomain(in, candidate)) {
                        point.rejection_reason = "evaluator_integer_domain";
                        addCount(stats.integer_domain_rejections, 1);
                        if (observer.point) observer.point(point);
                        stats.verification_failed = true;
                        stats.rejection_reason = "candidate_exceeds_original_Evaluator_int_domain";
                        return {};
                    }
                    addCount(stats.evaluator_points, 1);
                    const auto checked = verifySolution(in, candidate, lambda);
                    point.physical_checked = true;
                    point.feasible = checked.feasible && checked.errors.empty();
                    point.load_feasible = checked.load_feasible;
                    point.station_feasible = checked.station_feasible;
                    point.duration_feasible = checked.duration_feasible;
                    point.objective_recomputed = checked.original_objective_recomputed;
                    point.objective = checked.objective;
                    point.G = checked.G; point.P = checked.P;
                    if (!point.objective_recomputed) {
                        point.rejection_reason = "nonfinite_original_F";
                        addCount(stats.nonfinite_rejections, 1);
                        if (observer.point) observer.point(point);
                        stats.verification_failed = true;
                        stats.rejection_reason = "candidate_nonfinite_original_F";
                        return {};
                    }
                    if (!point.feasible) {
                        point.rejection_reason = rejectReason(checked);
                        stats.duration_rejections += !checked.duration_feasible;
                        stats.station_rejections += !checked.station_feasible;
                        stats.other_physical_rejections +=
                            !checked.feasible && checked.load_feasible &&
                            checked.station_feasible && checked.duration_feasible &&
                            checked.original_objective_recomputed;
                    } else {
                        addCount(stats.feasible_points, 1);
                        if (!(baseline.objective - checked.objective > kStrictImprovement))
                            point.rejection_reason = "no_strict_original_F_improvement";
                        else {
                            const Round95Choice choice{true, a, b, u, v, checked.objective};
                            if (!best.found || choice.objective < best.objective ||
                                (choice.objective == best.objective &&
                                 std::tie(a, b, u, v) <
                                 std::tie(best.first, best.second,
                                          best.inventory_first, best.inventory_second)))
                                best = choice;
                        }
                    }
                    if (observer.point) observer.point(point);
                    if (expired(whole_run, stats)) return {};
                }
            }
        }
    }
    if (expired(whole_run, stats)) return {};
    return best;
}

std::vector<RoutePlan> applyRound95FullBlockChange(
    const Instance& in, const std::vector<RoutePlan>& routes,
    const Round95Choice& choice) {
    if (!choice.found)
        throw std::invalid_argument("Round95 cannot apply absent choice");
    return materialize(in, routes, choice.first, choice.second,
                       choice.inventory_first, choice.inventory_second);
}

Round95Result runRound95FullBlockDescent(
    const Instance& in, const SolveOptions& options,
    const std::vector<RoutePlan>& routes, const Round95Observer& observer) {
    Round95Result out;
    out.routes = routes;
    out.verification = verifyRound95StartingWitness(in, routes, options.lambda);
    for (;;) {
        const auto choice = bestRound95FullBlockChange(
            in, out.routes, options.lambda, out.stats, &options, observer);
        if (expired(&options, out.stats)) break;
        if (out.stats.deadline_reached || out.stats.verification_failed) break;
        if (!choice.found) { out.stats.exhausted = true; break; }
        auto candidate = applyRound95FullBlockChange(in, out.routes, choice);
        if (!physicalOperationsFitEvaluatorIntegerDomain(in, candidate)) {
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
                    const Integer before = Integer(op.pickup) - op.drop;
                    const int inventory = op.station == choice.first
                        ? choice.inventory_first : choice.inventory_second;
                    const Integer after = Integer(in.initial[op.station]) - inventory;
                    out.stats.deleted_stops += after == 0;
                    out.stats.sign_flips +=
                        (before > 0 && after < 0) || (before < 0 && after > 0);
                }
        addCount(out.stats.accepted, 1);
        out.accepted_choices.push_back(choice);
        out.routes = std::move(candidate);
        out.verification = std::move(checked);
    }
    return out;
}
} // namespace ebrp
