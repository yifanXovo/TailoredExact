#include "Round95FullBlockDescent.hpp"
#include "Round93CoQuantityDescent.hpp"
#include "Round76PhysicalClosure.hpp"
#include "Round83BlockExchange.hpp"
#include "Evaluator.hpp"
#include "PhysicalDurationTolerance.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace {
using namespace ebrp;
using Key = std::tuple<int, int, int, int>;
void require(bool ok, const char* why) {
    if (!ok) throw std::runtime_error(why);
}
bool near(double a, double b) { return std::fabs(a - b) < 1e-12; }

Instance micro() {
    Instance in;
    in.V = 2; in.M = 1; in.Q = {7};
    in.initial = {0, 2, 8}; in.capacity = {0, 8, 8};
    in.target = {0, 4, 8}; in.weights = {0, 1, 1};
    in.dist.assign(3, std::vector<double>(3, 0));
    in.total_time_limit = 1;
    in.pickup_time = 0; in.drop_time = 0;
    return in;
}

std::vector<RoutePlan> microRoutes() {
    return {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 6, 0}}}};
}

void metric(Instance& in, double distance = .01) {
    in.dist.assign(in.V + 1, std::vector<double>(in.V + 1, distance));
    for (int i = 0; i <= in.V; ++i) in.dist[i][i] = 0;
}

// Directly rebuild signed operations and walk new routes; this is deliberately
// independent of the prefix-band formulas used by the implementation.
bool directLoadFeasible(const Instance& in, const std::vector<RoutePlan>& routes,
                        int a, int b, int u, int v) {
    for (const auto& route : routes) {
        std::int64_t load = 0;
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int station = route.nodes[j];
            std::int64_t operation = 0;
            if (station == a || station == b) {
                operation = std::int64_t(in.initial[station]) - (station == a ? u : v);
            } else {
                const auto it = std::find_if(route.operations.begin(), route.operations.end(),
                    [station](const StopOperation& op) { return op.station == station; });
                require(it != route.operations.end(), "direct oracle operation missing");
                operation = std::int64_t(it->pickup) - it->drop;
            }
            if (operation == 0) continue; // zero node is deleted
            load += operation;
            if (load < 0 || load > in.Q[route.vehicle]) return false;
        }
    }
    return true;
}

struct Scan {
    Round95Stats stats;
    Round95Choice choice;
    std::vector<Round95PairDomain> pairs;
    std::vector<Round95InventoryInterval> intervals;
    std::map<Key, Round95Point> points;
};

Scan scan(const Instance& in, const std::vector<RoutePlan>& routes, double lambda = .15) {
    Scan out;
    Round95Observer observer;
    observer.pair = [&](const Round95PairDomain& p) { out.pairs.push_back(p); };
    observer.interval = [&](const Round95InventoryInterval& q) { out.intervals.push_back(q); };
    observer.point = [&](const Round95Point& p) {
        require(out.points.emplace(Key{p.first, p.second,
                                       p.inventory_first, p.inventory_second}, p).second,
                "duplicate full-block point");
    };
    out.choice = bestRound95FullBlockChange(in, routes, lambda, out.stats, nullptr, observer);
    return out;
}

void checkCoverage(const Instance& in, const std::vector<RoutePlan>& routes) {
    const auto baseline = verifyRound95StartingWitness(in, routes, .15);
    const auto result = scan(in, routes);
    std::vector<int> served;
    for (const auto& route : routes)
        for (const auto& op : route.operations) served.push_back(op.station);
    std::sort(served.begin(), served.end());
    std::set<Key> expected;
    std::uint64_t rectangle = 0;
    for (std::size_t i = 0; i < served.size(); ++i)
        for (std::size_t j = i + 1; j < served.size(); ++j) {
            const int a = served[i], b = served[j];
            rectangle += (std::uint64_t(in.capacity[a]) + 1) *
                         (std::uint64_t(in.capacity[b]) + 1) - 1;
            for (int u = 0; u <= in.capacity[a]; ++u)
                for (int v = 0; v <= in.capacity[b]; ++v) {
                    if (u == baseline.final_inventory[a] &&
                        v == baseline.final_inventory[b]) continue;
                    if (directLoadFeasible(in, routes, a, b, u, v))
                        expected.emplace(a, b, u, v);
                }
        }
    std::set<Key> actual;
    for (const auto& [key, point] : result.points) {
        require(point.physical_checked && point.load_feasible,
                "band survivor was not checked or load-feasible");
        actual.insert(key);
    }
    require(actual == expected, "prefix bands differ from direct rebuilt route loads");
    require(result.stats.rectangle_points == rectangle &&
            result.stats.load_pruned + actual.size() == rectangle &&
            result.stats.candidate_points == actual.size() &&
            result.stats.evaluator_points == actual.size(),
            "rectangle / pruned / Evaluator counts do not reconcile");
    std::uint64_t interval_count = 0;
    for (const auto& interval : result.intervals)
        interval_count += interval.surviving_points;
    require(interval_count == actual.size(), "published intervals omit a surviving point");
}

const Round95Point& point(const Scan& result, int a, int b, int u, int v) {
    const auto it = result.points.find({a, b, u, v});
    require(it != result.points.end(), "expected candidate was load-pruned");
    return it->second;
}

void strongMicro() {
    const auto in = micro();
    const auto routes = microRoutes();
    const auto start = verifyRound95StartingWitness(in, routes, .15);
    require(near(start.objective, .225) && start.final_inventory[1] == 1 &&
            start.final_inventory[2] == 2, "strong micro baseline F");
    SolveOptions options; options.lambda = .15;
    const auto old = runRound76PhysicalClosure(in, options, routes);
    require(old.stats.exhausted && old.stats.accepted == 0,
            "strong micro is old R73/R75 closure stop");
    const auto neutral = runRound83ExchangeDescent(in, options, routes);
    require(neutral.exhausted && neutral.neutral == 0 &&
            neutral.insertions == 0 && neutral.quantities == 0,
            "strong micro is old R83 stop");
    Round93CoQuantityStats co_stats;
    const auto co = bestRound93CoQuantityChange(in, routes, .15, co_stats);
    require(!co.found && co_stats.integer_points == 7,
            "strong micro has no R93 co-line improvement");
    const auto result = scan(in, routes);
    require(result.choice.found && result.choice.first == 1 &&
            result.choice.second == 2 && result.choice.inventory_first == 2 &&
            result.choice.inventory_second == 4 && near(result.choice.objective, .15),
            "full two-station block finds unique strict best");
    require(result.pairs.size() == 1 && result.pairs[0].rectangle_points == 80 &&
            result.pairs[0].band10.present && result.pairs[0].band10.low == -6 &&
            result.pairs[0].band10.high == 1 && result.pairs[0].band11.present &&
            result.pairs[0].band11.low == 0 && result.pairs[0].band11.high == 7 &&
            !result.pairs[0].band01.present, "strong micro exact prefix bands");
    const auto changed = applyRound95FullBlockChange(in, routes, result.choice);
    const auto checked = verifyRound95StartingWitness(in, changed, .15);
    require(changed[0].nodes == std::vector<int>({0, 2, 0}) &&
            changed[0].operations.size() == 1 &&
            changed[0].operations[0].pickup == 4 && near(checked.objective, .15),
            "zero operation and node deleted with exact original F");
    const auto descent = runRound95FullBlockDescent(in, options, routes);
    require(descent.stats.accepted == 1 && descent.stats.exhausted &&
            !descent.stats.deadline_reached && near(descent.verification.objective, .15),
            "full-block descent terminates with verified improvement");
    checkCoverage(in, routes);

    auto positive = micro(); metric(positive);
    positive.pickup_time = positive.drop_time = .01;
    const auto positive_start = verifyRound95StartingWitness(positive, routes, .15);
    require(std::fabs(positive_start.route_duration[0] - .17) < 1e-12,
            "loaded-return handling included at positive baseline");
    const auto positive_old = runRound76PhysicalClosure(positive, options, routes);
    const auto positive_neutral = runRound83ExchangeDescent(positive, options, routes);
    Round93CoQuantityStats positive_co_stats;
    const auto positive_co = bestRound93CoQuantityChange(
        positive, routes, .15, positive_co_stats);
    require(positive_old.stats.exhausted && positive_old.stats.accepted == 0 &&
            positive_neutral.exhausted && positive_neutral.neutral == 0 &&
            positive_neutral.insertions == 0 && positive_neutral.quantities == 0 &&
            !positive_co.found,
            "positive metric micro also stops old closure and R93 line");
    const auto positive_scan = scan(positive, routes);
    require(positive_scan.choice.found && positive_scan.choice.inventory_first == 2 &&
            positive_scan.choice.inventory_second == 4,
            "positive metric / handling variant retains exact best");
    const auto positive_changed = applyRound95FullBlockChange(
        positive, routes, positive_scan.choice);
    const auto positive_end = verifyRound95StartingWitness(
        positive, positive_changed, .15);
    require(std::fabs(positive_end.route_duration[0] - .1) < 1e-12,
            "deleted stop travel and loaded return recomputed");
}

void variedPhysicalCases() {
    auto reverse = micro();
    const std::vector<RoutePlan> reverse_routes =
        {{0, {0, 2, 1, 0}, {{2, 6, 0}, {1, 1, 0}}}};
    const auto reverse_scan = scan(reverse, reverse_routes);
    require(reverse_scan.pairs.size() == 1 &&
            !reverse_scan.pairs[0].band10.present &&
            reverse_scan.pairs[0].band01.present &&
            reverse_scan.pairs[0].band01.low == -1 &&
            reverse_scan.pairs[0].band01.high == 6 &&
            reverse_scan.pairs[0].band11.present,
            "reverse order uses 01 and 11 bands");
    checkCoverage(reverse, reverse_routes);

    auto cross = micro(); metric(cross);
    cross.M = 2; cross.Q = {1, 1};
    cross.initial = {0, 2, 2}; cross.capacity = {0, 3, 3};
    cross.target = {0, 2, 2};
    cross.pickup_time = cross.drop_time = .01;
    const std::vector<RoutePlan> cross_routes = {
        {0, {0, 1, 0}, {{1, 1, 0}}},
        {1, {0, 2, 0}, {{2, 1, 0}}}};
    const auto cross_start = verifyRound95StartingWitness(cross, cross_routes, .15);
    require(cross_start.route_duration.size() == 2 &&
            std::fabs(cross_start.route_duration[0] - .04) < 1e-12 &&
            std::fabs(cross_start.route_duration[1] - .04) < 1e-12,
            "cross-vehicle loaded returns remain separate");
    const auto cross_scan = scan(cross, cross_routes);
    require(cross_scan.pairs.size() == 1 &&
            cross_scan.pairs[0].band10.present &&
            cross_scan.pairs[0].band01.present &&
            !cross_scan.pairs[0].band11.present,
            "cross-vehicle bands contain no 11 prefix");
    checkCoverage(cross, cross_routes);

    auto zero = micro();
    zero.initial = {0, 1, 1}; zero.capacity = {0, 2, 2};
    zero.target = {0, 1, 1}; zero.Q = {2};
    const std::vector<RoutePlan> zero_routes =
        {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 1, 0}}}};
    const auto zero_start = verifyRound95StartingWitness(zero, zero_routes, .15);
    require(zero_start.G == 0 && near(zero_start.objective, .3),
            "S=0 uses original G=0 convention");
    const auto zero_scan = scan(zero, zero_routes);
    const auto& empty = point(zero_scan, 1, 2, 1, 1);
    require(empty.feasible && empty.objective == 0,
            "both zero operations delete to an empty route");
    checkCoverage(zero, zero_routes);

    auto hetero = micro();
    hetero.initial = {0, 3, 3}; hetero.capacity = {0, 5, 5};
    hetero.target = {0, 2, 4}; hetero.weights = {0, 2, 1};
    hetero.Q = {3};
    const auto hbase = verifyRound95StartingWitness(hetero, zero_routes, .15);
    require(std::fabs(hbase.objective - 29.0 / 120.0) < 1e-12,
            "heterogeneous targets and weighted L1 baseline");
    checkCoverage(hetero, zero_routes);

    auto flip = micro();
    flip.V = 3; flip.initial = {0, 3, 2, 2};
    flip.capacity = {0, 3, 4, 4}; flip.target = {0, 3, 2, 2};
    flip.weights = {0, 1, 1, 1}; flip.Q = {5}; metric(flip);
    const std::vector<RoutePlan> flip_routes =
        {{0, {0, 1, 2, 3, 0}, {{1, 3, 0}, {2, 1, 0}, {3, 1, 0}}}};
    const auto flip_scan = scan(flip, flip_routes);
    require(point(flip_scan, 2, 3, 3, 4).feasible,
            "two independent pickup-to-drop sign flips are feasible");
    const auto flipped = applyRound95FullBlockChange(
        flip, flip_routes, {true, 2, 3, 3, 4, 0});
    require(flipped[0].operations[1].drop == 1 &&
            flipped[0].operations[2].drop == 2,
            "independent signed operations reconstructed exactly");
    checkCoverage(flip, flip_routes);

    auto nonmetric = micro();
    nonmetric.initial = {0, 2, 2}; nonmetric.capacity = {0, 3, 3};
    nonmetric.target = {0, 2, 2}; nonmetric.Q = {3};
    nonmetric.total_time_limit = 10;
    nonmetric.dist = {{0, 1, 100}, {1, 0, 1}, {1, 1, 0}};
    const std::vector<RoutePlan> nonmetric_routes =
        {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 2, 0}}}};
    const auto nonmetric_scan = scan(nonmetric, nonmetric_routes);
    const auto& nonmetric_point = point(nonmetric_scan, 1, 2, 2, 1);
    require(nonmetric_point.physical_checked && !nonmetric_point.feasible &&
            !nonmetric_point.duration_feasible &&
            nonmetric_point.rejection_reason == "duration",
            "deleting zero station can raise nonmetric travel from 3 to 101");
    checkCoverage(nonmetric, nonmetric_routes);

    auto boundary = micro();
    boundary.initial = {0, 2, 2}; boundary.capacity = {0, 3, 3};
    boundary.target = {0, 2, 2}; boundary.Q = {4};
    boundary.total_time_limit = 0;
    for (int direction : {-1, 0, 1}) {
        const double requested = direction < 0
            ? std::nextafter(kPhysicalDurationTolerance, 0.0)
            : direction > 0
                ? std::nextafter(kPhysicalDurationTolerance,
                                 std::numeric_limits<double>::infinity())
                : kPhysicalDurationTolerance;
        // Four pickups plus four units unloaded at return: eight exact
        // binary64-scaled handling units in the tested candidate.
        boundary.pickup_time = boundary.drop_time = requested / 8.0;
        const auto boundary_scan = scan(boundary, zero_routes);
        const auto& candidate = point(boundary_scan, 1, 2, 0, 0);
        require(candidate.physical_checked &&
                candidate.feasible == (direction <= 0),
                "binary64 nextafter T+1e-7 boundary retained by Evaluator");
    }
}

void deadlineAndDomain() {
    const auto in = micro();
    const auto routes = microRoutes();
    SolveOptions expired; expired.lambda = .15;
    expired.process_start_time_valid = true;
    expired.process_start_time = std::chrono::steady_clock::now() -
        std::chrono::seconds(5);
    expired.process_wall_time_limit = 1;
    expired.process_shutdown_margin_seconds = 0;
    const auto stopped = runRound95FullBlockDescent(in, expired, routes);
    require(stopped.stats.deadline_reached && !stopped.stats.exhausted &&
            stopped.stats.accepted == 0 && near(stopped.verification.objective, .225),
            "expired shared deadline retains old verified witness");

    SolveOptions mid; mid.lambda = .15;
    Round95Stats midstats;
    bool saw_best = false;
    Round95Observer observer;
    observer.point = [&](const Round95Point& p) {
        if (p.inventory_first == 2 && p.inventory_second == 4 && p.feasible) {
            saw_best = true;
            mid.process_start_time_valid = true;
            mid.process_start_time = std::chrono::steady_clock::now() -
                std::chrono::seconds(5);
            mid.process_wall_time_limit = 1;
            mid.process_shutdown_margin_seconds = 0;
        }
    };
    const auto partial = bestRound95FullBlockChange(
        in, routes, .15, midstats, &mid, observer);
    require(saw_best && !partial.found && midstats.deadline_reached &&
            !midstats.exhausted, "midscan deadline discards partial best");
    SolveOptions midrun; midrun.lambda = .15;
    Round95Observer run_observer;
    run_observer.point = [&](const Round95Point& p) {
        if (p.inventory_first == 2 && p.inventory_second == 4 && p.feasible) {
            midrun.process_start_time_valid = true;
            midrun.process_start_time = std::chrono::steady_clock::now() -
                std::chrono::seconds(5);
            midrun.process_wall_time_limit = 1;
            midrun.process_shutdown_margin_seconds = 0;
        }
    };
    const auto interrupted = runRound95FullBlockDescent(in, midrun, routes,
                                                        run_observer);
    require(interrupted.stats.deadline_reached && !interrupted.stats.exhausted &&
            interrupted.stats.accepted == 0 &&
            near(interrupted.verification.objective, .225),
            "midscan run cannot commit earlier best");

    auto malformed = routes;
    malformed[0].nodes[2] = 1;
    bool refused = false;
    try { (void)verifyRound95StartingWitness(in, malformed, .15); }
    catch (const std::exception&) { refused = true; }
    require(refused, "malformed witness refused before original Evaluator");

    const int maxint = std::numeric_limits<int>::max();
    auto huge = micro();
    huge.V = 3; huge.initial = {0, maxint, 0, 1};
    huge.capacity = {0, maxint, maxint, 1};
    huge.target = {0, 1, 1, 1}; huge.weights = {0, 1, 1, 1};
    huge.Q = {maxint}; huge.dist.assign(4, std::vector<double>(4, 0));
    const std::vector<RoutePlan> huge_routes =
        {{0, {0, 1, 2, 3, 0},
             {{1, maxint - 1, 0}, {2, 0, maxint - 1}, {3, 1, 0}}}};
    (void)verifyRound95StartingWitness(huge, huge_routes, .15);
    Round95Stats stats;
    const auto choice = bestRound95FullBlockChange(
        huge, huge_routes, .15, stats);
    require(!choice.found && stats.verification_failed &&
            !stats.exhausted && stats.integer_domain_rejections == 1 &&
            stats.rejection_reason == "candidate_exceeds_original_Evaluator_int_domain",
            "candidate accumulator overflow fails closed without exhaustion");

    // Finite input parameters can still overflow original F for a changed
    // inventory. Such a point is unknown, never evidence of exhaustion.
    auto nonfinite = micro();
    nonfinite.initial = {0, 2, 2};
    nonfinite.capacity = {0, 2, 2};
    nonfinite.target = {0, 1, 1};
    nonfinite.weights = {0, std::numeric_limits<double>::max(), 1};
    nonfinite.Q = {3};
    const std::vector<RoutePlan> nonfinite_routes =
        {{0, {0, 1, 2, 0}, {{1, 1, 0}, {2, 1, 0}}}};
    (void)verifyRound95StartingWitness(nonfinite, nonfinite_routes, 2);
    Round95Stats nonfinite_stats;
    const auto nonfinite_choice = bestRound95FullBlockChange(
        nonfinite, nonfinite_routes, 2, nonfinite_stats);
    require(!nonfinite_choice.found && nonfinite_stats.verification_failed &&
            !nonfinite_stats.exhausted && nonfinite_stats.nonfinite_rejections == 1 &&
            nonfinite_stats.rejection_reason == "candidate_nonfinite_original_F",
            "nonfinite original F fails closed without false exhaustion");
}
} // namespace

int main() {
    try {
        strongMicro();
        variedPhysicalCases();
        deadlineAndDomain();
        std::cout << "Round95 full-block source qualification ready\n";
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
