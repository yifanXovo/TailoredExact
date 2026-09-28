#include "Round93CoQuantityDescent.hpp"
#include "Round75QuantityDescent.hpp"
#include "Round76PhysicalClosure.hpp"
#include "Round83BlockExchange.hpp"
#include "Evaluator.hpp"
#include "PhysicalDurationTolerance.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <tuple>

namespace {
using namespace ebrp;
void require(bool ok, const char* reason) { if (!ok) throw std::runtime_error(reason); }

Instance witness() {
    Instance in;
    in.V = 2; in.M = 1; in.Q = {5};
    in.initial = {0, 3, 6}; in.capacity = {0, 6, 6};
    in.target = {0, 4, 4}; in.weights = {0, 1, 1};
    in.dist.assign(3, std::vector<double>(3, 0));
    in.total_time_limit = 1;
    in.pickup_time = 0; in.drop_time = 0;
    return in;
}

std::vector<RoutePlan> start() {
    return {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 4, 0}}}};
}

void metric(Instance& in, double d = .01) {
    in.dist.assign(in.V + 1, std::vector<double>(in.V + 1, d));
    for (int i = 0; i <= in.V; ++i) in.dist[i][i] = 0;
}

Round93CoQuantityPoint at(const Instance& in, const std::vector<RoutePlan>& routes,
                           double lambda, int a, int b, std::int64_t t) {
    Round93CoQuantityStats stats;
    Round93CoQuantityPoint found;
    bool seen = false;
    bestRound93CoQuantityChange(in, routes, lambda, stats, nullptr,
        [&](const Round93CoQuantityPoint& point) {
            if (point.first == a && point.second == b && point.delta == t) {
                require(!seen, "duplicate line point");
                found = point; seen = true;
            }
        });
    require(seen, "expected line point missing");
    return found;
}

void boundaryCases() {
    const double lambda = .15;
    const auto in = witness();
    // Positive travel and handling exercise the final-depot unload term.
    auto positive = witness(); metric(positive);
    positive.pickup_time = positive.drop_time = .01;
    const auto positive_base = verifyRound93StartingWitness(positive, start(), lambda);
    require(std::fabs(positive_base.route_duration[0] - .13) < 1e-12,
            "positive handling baseline duration");
    Round93CoQuantityStats ps;
    const auto pchoice = bestRound93CoQuantityChange(positive, start(), lambda, ps);
    require(pchoice.found && pchoice.delta == 1 &&
            std::fabs(pchoice.objective - .075) < 1e-12,
            "positive travel/handling co choice");
    const auto pv = verifyRound93StartingWitness(
        positive, applyRound93CoQuantityChange(start(), pchoice), lambda);
    require(std::fabs(pv.route_duration[0] - .08) < 1e-12,
            "zero-stop deletion and loaded return recomputed");

    // The original S=0 convention is G=0, with no fractional division.
    auto zero = witness();
    zero.initial = {0, 1, 1}; zero.capacity = {0, 2, 2};
    zero.target = {0, 1, 1}; zero.Q = {2};
    const std::vector<RoutePlan> zroutes =
        {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 1, 0}}}};
    const auto zbase = verifyRound93StartingWitness(zero, zroutes, lambda);
    require(zbase.G == 0 && std::fabs(zbase.objective - .3) < 1e-12,
            "zero mass uses original G convention");
    const auto zpoint = at(zero, zroutes, lambda, 1, 2, 1);
    require(zpoint.physical_checked && zpoint.feasible && zpoint.objective == 0,
            "zero mass line reaches zero original F");

    auto hetero = witness(); metric(hetero);
    hetero.initial = {0, 3, 3}; hetero.capacity = {0, 5, 5};
    hetero.target = {0, 2, 4}; hetero.weights = {0, 2, 1};
    hetero.Q = {3}; hetero.pickup_time = hetero.drop_time = .01;
    const auto hbase = verifyRound93StartingWitness(hetero, zroutes, lambda);
    require(std::fabs(hbase.objective - 29.0 / 120.0) < 1e-12,
            "heterogeneous target and weighted L1 original F");
    const auto hpoint = at(hetero, zroutes, lambda, 1, 2, 1);
    require(hpoint.physical_checked && hpoint.feasible &&
            hpoint.inventory_first == 3 && hpoint.inventory_second == 3,
            "heterogeneous co point verified");

    auto cross = witness(); metric(cross);
    cross.M = 2; cross.Q = {1, 1}; cross.initial = {0, 2, 2};
    cross.capacity = {0, 3, 3}; cross.target = {0, 2, 2};
    cross.pickup_time = cross.drop_time = .01;
    const std::vector<RoutePlan> cross_routes = {
        {0, {0, 1, 0}, {{1, 1, 0}}}, {1, {0, 2, 0}, {{2, 1, 0}}}};
    const auto cbase = verifyRound93StartingWitness(cross, cross_routes, lambda);
    require(cbase.route_duration.size() == 2 &&
            std::fabs(cbase.route_duration[0] - .04) < 1e-12 &&
            std::fabs(cbase.route_duration[1] - .04) < 1e-12,
            "cross-vehicle loaded returns counted separately");
    const auto cpoint = at(cross, cross_routes, lambda, 1, 2, 1);
    require(cpoint.physical_checked && cpoint.feasible && cpoint.objective == 0,
            "cross-vehicle co point verified");

    auto flip = witness();
    flip.V = 3; flip.initial = {0, 3, 2, 2};
    flip.capacity = {0, 3, 4, 4}; flip.target = {0, 3, 2, 2};
    flip.weights = {0, 1, 1, 1}; flip.Q = {5}; metric(flip);
    flip.pickup_time = flip.drop_time = .01;
    const std::vector<RoutePlan> flip_routes =
        {{0, {0, 1, 2, 3, 0}, {{1, 3, 0}, {2, 1, 0}, {3, 1, 0}}}};
    const auto fpoint = at(flip, flip_routes, lambda, 2, 3, 2);
    require(fpoint.physical_checked && fpoint.feasible &&
            fpoint.inventory_first == 3 && fpoint.inventory_second == 3,
            "simultaneous pickup-to-drop sign flips physical");
    const auto flipped = applyRound93CoQuantityChange(flip_routes,
        {true, 2, 3, 2, fpoint.objective});
    require(flipped[0].operations[1].drop == 1 &&
            flipped[0].operations[2].drop == 1,
            "both changed operations are drops");

    auto nonmetric = witness();
    nonmetric.initial = {0, 2, 2}; nonmetric.capacity = {0, 3, 3};
    nonmetric.target = {0, 2, 2}; nonmetric.Q = {3};
    nonmetric.total_time_limit = 10;
    nonmetric.dist = {{0, 1, 100}, {1, 0, 1}, {1, 1, 0}};
    const std::vector<RoutePlan> nonmetric_routes =
        {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 2, 0}}}};
    const auto nbase = verifyRound93StartingWitness(nonmetric, nonmetric_routes, lambda);
    require(nbase.route_travel_time[0] == 3,
            "nonmetric route starts with short travel");
    const auto npoint = at(nonmetric, nonmetric_routes, lambda, 1, 2, 1);
    require(npoint.physical_checked && !npoint.feasible &&
            !npoint.duration_feasible && npoint.rejection_reason == "duration",
            "deleting zero station can raise nonmetric travel to 101");

    auto horizon = witness();
    horizon.initial = {0, 2, 2}; horizon.capacity = {0, 3, 3};
    horizon.target = {0, 2, 2}; horizon.Q = {4};
    horizon.total_time_limit = 0;
    const std::vector<RoutePlan> horizon_routes = zroutes;
    horizon.pickup_time = horizon.drop_time = 1.0 / 80000000.0;
    const auto equal = at(horizon, horizon_routes, lambda, 1, 2, -1);
    require(equal.physical_checked && equal.feasible,
            "rational T+1e-7 equality is admitted by binary64 Evaluator");
    horizon.pickup_time = horizon.drop_time = 3.0 / 200000000.0;
    const auto exceeded = at(horizon, horizon_routes, lambda, 1, 2, -1);
    require(exceeded.physical_checked && !exceeded.feasible &&
            exceeded.rejection_reason == "duration",
            "handling just above T+1e-7 rejected");

    // Here division by four and multiplication by four are exact binary
    // exponent changes, isolating the Evaluator's actual binary64 comparison.
    const double bound = kPhysicalDurationTolerance;
    horizon.drop_time = 0;
    for (int direction : {-1, 0, 1}) {
        const double requested = direction < 0
            ? std::nextafter(bound, 0.0)
            : direction > 0 ? std::nextafter(bound, std::numeric_limits<double>::infinity())
                            : bound;
        horizon.pickup_time = requested / 4.0;
        const auto point = at(horizon, horizon_routes, lambda, 1, 2, -1);
        require(point.physical_checked && point.feasible == (direction <= 0),
                "binary64 nextafter duration acceptance boundary");
    }

    // Malformed route and int-accumulator overflow are refused before the
    // original Evaluator could read them unsafely.
    auto malformed = start();
    malformed[0].nodes[2] = 1;
    bool refused = false;
    try { (void)verifyRound93StartingWitness(in, malformed, lambda); }
    catch (const std::exception&) { refused = true; }
    require(refused, "duplicate station rejected before Evaluator");
    auto huge = witness();
    huge.initial = {0, std::numeric_limits<int>::max(), std::numeric_limits<int>::max()};
    huge.capacity = huge.initial; huge.target = {0, 1, 1};
    huge.Q = {std::numeric_limits<int>::max()};
    const int maxint = std::numeric_limits<int>::max();
    const std::vector<RoutePlan> overflow =
        {{0, {0, 1, 2, 0}, {{1, maxint, 0}, {2, maxint, 0}}}};
    refused = false;
    try { (void)verifyRound93StartingWitness(huge, overflow, lambda); }
    catch (const std::exception&) { refused = true; }
    require(refused, "int route accumulation overflow refused before Evaluator");
}
} // namespace

int main() {
    try {
        const auto in = witness();
        const auto routes = start();
        const double lambda = .15;
        const auto initial = verifySolution(in, routes, lambda);
        require(initial.feasible && std::fabs(initial.objective - .15) < 1e-12,
                "micro starting witness");
        SolveOptions options; options.lambda = lambda;
        const auto closure = runRound76PhysicalClosure(in, options, routes);
        require(closure.stats.exhausted && closure.stats.accepted == 0,
                "old R73/R75 closure is exhausted");
        const auto old = runRound83ExchangeDescent(in, options, routes);
        require(old.exhausted && old.neutral == 0 && old.quantities == 0 && old.insertions == 0,
                "old R83 remains at the same physical witness");
        Round93CoQuantityStats scan;
        std::vector<std::tuple<int,int,std::int64_t,bool>> points;
        const auto best = bestRound93CoQuantityChange(in, routes, lambda, scan, nullptr,
            [&](const Round93CoQuantityPoint& p) {
                points.emplace_back(p.first, p.second, p.delta, p.feasible);
            });
        require(best.found && best.first == 1 && best.second == 2 && best.delta == 1 &&
                std::fabs(best.objective - .075) < 1e-12,
                "co-line finds the strict original-F descent");
        require(scan.integer_points == 6 && scan.feasible_points == 1 &&
                scan.load_rejections > 0, "all mathematical line points were checked");
        const auto changed = applyRound93CoQuantityChange(routes, best);
        const auto direct = verifySolution(in, changed, lambda);
        require(direct.feasible && direct.final_inventory[1] == 3 &&
                direct.final_inventory[2] == 3 &&
                changed[0].nodes == std::vector<int>({0, 2, 0}),
                "zero operation removed and original Evaluator agrees");
        const auto descent = runRound93CoQuantityDescent(in, options, routes);
        require(descent.stats.accepted == 1 && descent.stats.exhausted &&
                !descent.stats.deadline_reached &&
                std::fabs(descent.verification.objective - .075) < 1e-12,
                "finite co-line descent exhausted with legal witness");
        SolveOptions expired = options;
        expired.process_start_time_valid = true;
        expired.process_start_time = std::chrono::steady_clock::now() - std::chrono::seconds(5);
        expired.process_wall_time_limit = 1;
        expired.process_shutdown_margin_seconds = 0;
        const auto stopped = runRound93CoQuantityDescent(in, expired, routes);
        require(stopped.stats.deadline_reached && !stopped.stats.exhausted &&
                stopped.stats.accepted == 0 &&
                stopped.verification.objective == initial.objective,
                "whole-run deadline retains verified incumbent without false exhaustion");
        // Simulate the whole deadline crossing inside the observer immediately
        // after a good t=1 has been seen; partial-scan best must never leak.
        SolveOptions midscan = options;
        Round93CoQuantityStats midstats;
        bool saw_improvement = false;
        const auto partial = bestRound93CoQuantityChange(in, routes, lambda,
            midstats, &midscan, [&](const Round93CoQuantityPoint& p) {
                if (p.delta == 1 && p.feasible && p.objective < initial.objective) {
                    saw_improvement = true;
                    midscan.process_start_time_valid = true;
                    midscan.process_start_time =
                        std::chrono::steady_clock::now() - std::chrono::seconds(5);
                    midscan.process_wall_time_limit = 1;
                    midscan.process_shutdown_margin_seconds = 0;
                }
            });
        require(saw_improvement && !partial.found && midstats.deadline_reached,
                "midscan deadline discards earlier improving point");
        SolveOptions midrun = options;
        const auto interrupted = runRound93CoQuantityDescent(in, midrun, routes,
            [&](const Round93CoQuantityPoint& p) {
                if (p.delta == 1 && p.feasible && p.objective < initial.objective) {
                    midrun.process_start_time_valid = true;
                    midrun.process_start_time =
                        std::chrono::steady_clock::now() - std::chrono::seconds(5);
                    midrun.process_wall_time_limit = 1;
                    midrun.process_shutdown_margin_seconds = 0;
                }
            });
        require(interrupted.stats.deadline_reached && !interrupted.stats.exhausted &&
                interrupted.stats.accepted == 0 &&
                interrupted.verification.objective == initial.objective,
                "midscan whole-run cutoff retains original verified witness");
        boundaryCases();
        std::cout << "Round93 co-line micro qualification ready\n";
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n'; return 1;
    }
}
