#include "Round75QuantityDescent.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round61Candidates.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
using Integer = std::int64_t;
constexpr double improvement = 1e-12;
constexpr double physical_tolerance = 1e-7;

bool expired(const SolveOptions* options, Round75QuantityStats& stats) {
    if (options && processWorkDeadlineReached(*options)) stats.deadline_reached = true;
    return stats.deadline_reached;
}

void requireInput(const Instance& in, const std::vector<RoutePlan>& routes, double lambda) {
    const auto size = static_cast<std::size_t>(in.V + 1);
    if (in.V < 1 || in.M < 1 || in.Q.size() != static_cast<std::size_t>(in.M) ||
        in.initial.size() != size || in.capacity.size() != size ||
        in.target.size() != size || in.weights.size() != size || in.dist.size() != size ||
        !std::isfinite(lambda) || !std::isfinite(in.total_time_limit) ||
        !std::isfinite(in.pickup_time) || !std::isfinite(in.drop_time) ||
        in.pickup_time < 0 || in.drop_time < 0)
        throw std::invalid_argument("Quantity descent requires a valid original instance");
    for (int i = 0; i <= in.V; ++i) {
        if (in.dist[i].size() != size || (i && (in.target[i] <= 0 ||
            in.capacity[i] < 0 || in.initial[i] < 0 || in.initial[i] > in.capacity[i] ||
            !std::isfinite(in.weights[i]))))
            throw std::invalid_argument("Quantity descent dimension/stock/target mismatch");
        for (double d : in.dist[i]) if (!std::isfinite(d) || d < 0)
            throw std::invalid_argument("Quantity descent requires finite nonnegative travel");
    }
    for (int q : in.Q) if (q < 0) throw std::invalid_argument("Negative vehicle capacity");
    std::vector<bool> seen_vehicle(in.M, false), seen_station(size, false);
    for (const auto& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= in.M || seen_vehicle[route.vehicle] ||
            route.nodes.size() < 2 || route.nodes.front() != 0 || route.nodes.back() != 0)
            throw std::invalid_argument("Quantity descent requires one depot route per vehicle");
        seen_vehicle[route.vehicle] = true;
        if (route.operations.size() + 2 != route.nodes.size())
            throw std::invalid_argument("Quantity descent requires one operation per visit");
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
            const int i = route.nodes[j];
            if (i <= 0 || i > in.V || seen_station[i])
                throw std::invalid_argument("Quantity descent requires unique legal stations");
            seen_station[i] = true;
            if (std::count_if(route.operations.begin(), route.operations.end(),
                [i](const StopOperation& op) { return op.station == i; }) != 1)
                throw std::invalid_argument("Quantity descent duplicate/missing operation");
        }
    }
}

struct State {
    const RoutePlan* route = nullptr;
    std::vector<Integer> load;
    Integer pickups = 0, drops = 0;
    double travel = 0;
};

// Same exact two-inventory algebra as R61/R73, with long-double accumulation
// and full recomputation near cancellation. No clipped negative Gini value.
struct ObjectiveDelta {
    const Instance& in;
    const std::vector<int>& y;
    double lambda;
    std::vector<long double> r;
    long double S = 0, H = 0, P = 0;
    ObjectiveDelta(const Instance& instance, const std::vector<int>& inventory, double weight)
        : in(instance), y(inventory), lambda(weight), r(in.V + 1) {
        for (int i = 1; i <= in.V; ++i) {
            r[i] = static_cast<long double>(y[i]) / in.target[i];
            S += r[i]; P += in.weights[i] * std::fabs(r[i] - 1);
            for (int j = 1; j < i; ++j) H += std::fabs(r[i] - r[j]);
        }
    }
    double changed(int a, int b, Integer t) const {
        const long double ra = r[a] - static_cast<long double>(t) / in.target[a];
        const long double rb = b ? r[b] + static_cast<long double>(t) / in.target[b] : 0;
        long double s = S + ra - r[a], h = H;
        long double p = P + in.weights[a] * (std::fabs(ra - 1) - std::fabs(r[a] - 1));
        if (b) {
            s += rb - r[b];
            h += std::fabs(ra - rb) - std::fabs(r[a] - r[b]);
            p += in.weights[b] * (std::fabs(rb - 1) - std::fabs(r[b] - 1));
        }
        for (int i = 1; i <= in.V; ++i) if (i != a && i != b) {
            h += std::fabs(ra - r[i]) - std::fabs(r[a] - r[i]);
            if (b) h += std::fabs(rb - r[i]) - std::fabs(r[b] - r[i]);
        }
        if (s < 1e-12L || h < 1e-12L) {
            auto next = y;
            next[a] = static_cast<int>(Integer(y[a]) - t);
            if (b) next[b] = static_cast<int>(Integer(y[b]) + t);
            return computeObjectiveParts(in, next, lambda).objective;
        }
        return static_cast<double>(h / (in.V * s) + lambda * p);
    }
};
} // namespace

Round75QuantityChoice bestRound75QuantityChange(const Instance& in,
    const std::vector<RoutePlan>& routes, double lambda, Round75QuantityStats& stats,
    const SolveOptions* deadline) {
    requireInput(in, routes, lambda);
    const auto verified = verifySolution(in, routes, lambda);
    if (!verified.feasible || !verified.errors.empty())
        throw std::invalid_argument("Quantity descent refuses an invalid physical witness");
    ++stats.passes;
    Round75QuantityChoice best;
    if (expired(deadline, stats)) return best;
    std::vector<Integer> operation(in.V + 1, 0);
    std::vector<int> owner(in.V + 1, -1), stations;
    std::vector<State> states;
    for (const auto& route : routes) {
        State state; state.route = &route;
        state.travel = verified.route_travel_time[route.vehicle];
        state.load.assign(route.nodes.size(), 0);
        for (const auto& op : route.operations) {
            operation[op.station] = Integer(op.pickup) - op.drop;
            owner[op.station] = static_cast<int>(states.size());
            stations.push_back(op.station);
            state.pickups += op.pickup; state.drops += op.drop;
        }
        for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j)
            state.load[j] = state.load[j - 1] + operation[route.nodes[j]];
        states.push_back(std::move(state));
    }
    std::sort(stations.begin(), stations.end());
    const ObjectiveDelta objective(in, verified.final_inventory, lambda);
    for (std::size_t ia = 0; ia < stations.size(); ++ia) {
        const int a = stations[ia];
        // b=0 gives a single move, followed by each unordered pair once.
        for (std::size_t ib = ia; ib < stations.size(); ++ib) {
            if (expired(deadline, stats)) return best;
            const int b = ib == ia ? 0 : stations[ib];
            Integer low = Integer(in.initial[a]) - in.capacity[a] - operation[a];
            Integer high = Integer(in.initial[a]) - operation[a];
            if (b) {
                low = std::max(low, operation[b] - in.initial[b]);
                high = std::min(high, operation[b] - in.initial[b] + in.capacity[b]);
            }
            const int sa = owner[a], sb = b ? owner[b] : -1;
            auto constrain = [&](const State& state) {
                int coefficient = 0;
                const auto& route = *state.route;
                for (std::size_t j = 1; j + 1 < route.nodes.size(); ++j) {
                    if (route.nodes[j] == a) ++coefficient;
                    if (route.nodes[j] == b) --coefficient;
                    const Integer load = state.load[j], Q = in.Q[route.vehicle];
                    if (coefficient == 1) {
                        low = std::max(low, -load); high = std::min(high, Q - load);
                    } else if (coefficient == -1) {
                        low = std::max(low, load - Q); high = std::min(high, load);
                    }
                }
            };
            constrain(states[sa]);
            if (sb >= 0 && sb != sa) constrain(states[sb]);
            for (Integer t = low; t <= high; ++t) {
                if (!t) continue;
                if (expired(deadline, stats)) return best;
                if (b) ++stats.pair_candidates; else ++stats.single_candidates;
                const Integer na = operation[a] + t, nb = b ? operation[b] - t : 0;
                auto durationFeasible = [&](int state_index) {
                    const State& state = states[state_index];
                    const auto& route = *state.route;
                    Integer pickups = state.pickups, drops = state.drops;
                    auto update = [&](int i, Integer value) {
                        if (i && owner[i] == state_index) {
                            pickups += std::max(Integer(0), value) - std::max(Integer(0), operation[i]);
                            drops += std::max(Integer(0), -value) - std::max(Integer(0), -operation[i]);
                        }
                    };
                    update(a, na); update(b, nb);
                    double travel = state.travel;
                    if ((!na && owner[a] == state_index) ||
                        (b && !nb && owner[b] == state_index)) {
                        travel = 0; int previous = 0;
                        for (std::size_t j = 1; j < route.nodes.size(); ++j) {
                            const int node = route.nodes[j];
                            if ((node == a && !na) || (node == b && b && !nb)) continue;
                            travel += in.dist[previous][node]; previous = node;
                        }
                    }
                    // Original handling expression, including final depot unload.
                    const double duration = travel + in.pickup_time * pickups +
                        in.drop_time * drops + in.drop_time * (pickups - drops);
                    return duration <= in.total_time_limit + physical_tolerance;
                };
                if (!durationFeasible(sa) ||
                    (sb >= 0 && sb != sa && !durationFeasible(sb))) continue;
                ++stats.feasible_candidates; ++stats.objective_evaluations;
                const double value = objective.changed(a, b, t);
                if (!std::isfinite(value) || !(verified.objective - value > improvement)) continue;
                Round75QuantityChoice choice{true, a, b, t, value};
                if (!best.found || value < best.objective ||
                    (value == best.objective && std::tie(a, b, t) <
                        std::tie(best.first, best.second, best.delta))) best = choice;
            }
        }
    }
    return best;
}

std::vector<RoutePlan> applyRound75QuantityChange(const std::vector<RoutePlan>& routes,
    const Round75QuantityChoice& choice) {
    if (!choice.found || choice.first <= 0 || choice.second < 0 ||
        choice.first == choice.second || !choice.delta)
        throw std::invalid_argument("Cannot apply an empty quantity change");
    auto out = routes;
    int changed = 0;
    for (auto& route : out) {
        for (auto& op : route.operations) {
            if (op.station != choice.first && op.station != choice.second) continue;
            const Integer value = Integer(op.pickup) - op.drop +
                (op.station == choice.first ? choice.delta : -choice.delta);
            if (value < -Integer(std::numeric_limits<int>::max()) ||
                value > std::numeric_limits<int>::max())
                throw std::invalid_argument("Quantity operation exceeds integer representation");
            op.pickup = static_cast<int>(std::max(Integer(0), value));
            op.drop = static_cast<int>(std::max(Integer(0), -value));
            ++changed;
            if (!value) route.nodes.erase(std::remove(route.nodes.begin(), route.nodes.end(), op.station), route.nodes.end());
        }
        route.operations.erase(std::remove_if(route.operations.begin(), route.operations.end(),
            [](const StopOperation& op) { return !op.pickup && !op.drop; }), route.operations.end());
    }
    if (changed != (choice.second ? 2 : 1))
        throw std::invalid_argument("Quantity change references an absent or repeated station");
    return out;
}

Round75QuantityResult runRound75QuantityDescent(const Instance& in,
    const SolveOptions& options, const std::vector<RoutePlan>& routes,
    const std::filesystem::path& trace_path) {
    requireInput(in, routes, options.lambda);
    Round75QuantityResult out; out.routes = routes;
    out.verification = verifySolution(in, routes, options.lambda);
    if (!out.verification.feasible || !out.verification.errors.empty())
        throw std::invalid_argument("Quantity descent initial physical verification failed");
    std::ofstream trace;
    auto snapshot = [&](const char* suffix) {
        if (trace_path.empty()) return;
        VerifiedCandidateStore store;
        if (!store.consider(in, options.lambda, out.routes, "round75_quantity", "original_problem"))
            throw std::runtime_error("Quantity descent snapshot verification failed");
        writeRound61Witness(trace_path.string() + suffix, in, options.lambda, store.best());
    };
    if (!trace_path.empty()) {
        if (trace_path.has_parent_path()) std::filesystem::create_directories(trace_path.parent_path());
        trace.open(trace_path);
        if (!trace) throw std::runtime_error("Cannot open quantity descent trace");
        trace << "step,process_seconds,first,second,delta,objective,G,P,passes,single_candidates,pair_candidates,feasible_candidates,status\n" << std::setprecision(17);
        snapshot(".initial.json");
    }
    auto write = [&](const Round75QuantityChoice& c, const char* status) {
        if (!trace.is_open()) return;
        trace << out.stats.accepted << ',' << processElapsedSeconds(options) << ',' << c.first << ',' << c.second << ','
            << c.delta << ',' << out.verification.objective << ',' << out.verification.G << ',' << out.verification.P << ','
            << out.stats.passes << ',' << out.stats.single_candidates << ',' << out.stats.pair_candidates << ','
            << out.stats.feasible_candidates << ',' << status << '\n';
        trace.flush(); if (!trace) throw std::runtime_error("Quantity descent trace write failed");
    };
    write({}, "initial_verified");
    for (;;) {
        const auto choice = bestRound75QuantityChange(in, out.routes, options.lambda, out.stats, &options);
        if (out.stats.deadline_reached) { write({}, "whole_run_deadline"); break; }
        if (!choice.found) { out.stats.exhausted = true; write({}, "neighborhood_exhausted"); break; }
        auto next = applyRound75QuantityChange(out.routes, choice);
        auto checked = verifySolution(in, next, options.lambda);
        if (!checked.feasible || !checked.errors.empty() || !checked.original_objective_recomputed ||
            std::fabs(checked.objective - choice.objective) > 1e-10 ||
            !(out.verification.objective - checked.objective > improvement)) {
            out.stats.verification_failed = true;
            out.stats.rejection_reason = "physical_or_objective_admission_failed_previous_witness_retained";
            write(choice, "verification_rejected"); break;
        }
        int vehicle_a = -1, vehicle_b = -1;
        for (const auto& route : out.routes) for (const auto& op : route.operations) {
            if (op.station != choice.first && op.station != choice.second) continue;
            const Integer before = Integer(op.pickup) - op.drop;
            const Integer after = before + (op.station == choice.first ? choice.delta : -choice.delta);
            if (!after) ++out.stats.removed_stops;
            if ((before > 0 && after < 0) || (before < 0 && after > 0)) ++out.stats.sign_flips;
            if (op.station == choice.first) vehicle_a = route.vehicle; else vehicle_b = route.vehicle;
        }
        ++out.stats.accepted;
        if (choice.second) { ++out.stats.pair_moves; if (vehicle_a != vehicle_b) ++out.stats.cross_vehicle_moves; }
        else ++out.stats.single_moves;
        out.routes = std::move(next); out.verification = std::move(checked);
        write(choice, "accepted_verified");
    }
    snapshot(".final.json");
    return out;
}
} // namespace ebrp
