#include "Round78BalancedRelocation.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <tuple>

namespace ebrp {
namespace {
using Integer = std::int64_t;
struct State {
    std::vector<int> nodes;
    std::vector<Integer> load;
    Integer pickup = 0, drop = 0;
};
bool expired(const SolveOptions* deadline, Round78BlockStats& stats) {
    if (deadline && processWorkDeadlineReached(*deadline)) stats.deadline_reached = true;
    return stats.deadline_reached;
}
double duration(const Instance& in, const std::vector<int>& service,
                Integer pickup, Integer drop) {
    // An empty resulting route is omitted by the materializer.
    if (service.empty()) return 0;
    double travel = 0; int previous = 0;
    for (int node : service) { travel += in.dist[previous][node]; previous = node; }
    travel += in.dist[previous][0];
    const double handling = in.pickup_time * pickup + in.drop_time * drop +
        in.drop_time * (pickup - drop);
    return travel + handling; // same accumulation/grouping as the original verifier
}
auto key(const Round78BlockChoice& c) {
    return std::tie(c.source, c.first, c.last, c.target, c.leg);
}
} // namespace

std::vector<double> round78DurationPotential(const Verification& v) {
    auto d = v.route_duration;
    for (double x : d) if (!std::isfinite(x))
        throw std::invalid_argument("Nonfinite route duration potential");
    std::sort(d.begin(), d.end(), std::greater<double>());
    return d;
}

Round78BlockChoice bestRound78BalancedRelocation(const Instance& in,
    const std::vector<RoutePlan>& routes, double lambda, Round78BlockStats& stats,
    const SolveOptions* deadline) {
    const auto size = static_cast<std::size_t>(in.V + 1);
    if (in.V < 1 || in.M < 1 || in.Q.size() != static_cast<std::size_t>(in.M) ||
        in.initial.size() != size || in.capacity.size() != size ||
        in.target.size() != size || in.weights.size() != size || in.dist.size() != size ||
        !std::isfinite(lambda) || !std::isfinite(in.total_time_limit) ||
        !std::isfinite(in.pickup_time) || !std::isfinite(in.drop_time) ||
        in.pickup_time < 0 || in.drop_time < 0)
        throw std::invalid_argument("Balanced relocation requires a valid original instance");
    for (int i = 0; i <= in.V; ++i) {
        if (in.dist[i].size() != size || (i && (in.target[i] <= 0 ||
            in.initial[i] < 0 || in.initial[i] > in.capacity[i] || !std::isfinite(in.weights[i]))))
            throw std::invalid_argument("Balanced relocation dimension/stock mismatch");
        for (double x : in.dist[i]) if (!std::isfinite(x) || x < 0)
            throw std::invalid_argument("Balanced relocation requires finite nonnegative travel");
    }
    for (int q : in.Q) if (q < 0) throw std::invalid_argument("Negative vehicle capacity");
    std::vector<State> states(in.M);
    std::vector<Integer> signed_op(size, 0), pickup(size, 0), drop(size, 0);
    std::vector<bool> seen_vehicle(in.M, false), seen_station(size, false);
    for (const auto& r : routes) {
        if (r.vehicle < 0 || r.vehicle >= in.M || seen_vehicle[r.vehicle] ||
            r.nodes.size() < 2 || r.nodes.front() != 0 || r.nodes.back() != 0 ||
            r.operations.size() + 2 != r.nodes.size())
            throw std::invalid_argument("Balanced relocation malformed route");
        seen_vehicle[r.vehicle] = true;
        auto& s = states[r.vehicle];
        for (std::size_t j = 1; j + 1 < r.nodes.size(); ++j) {
            const int i = r.nodes[j];
            if (i <= 0 || i > in.V || seen_station[i])
                throw std::invalid_argument("Balanced relocation repeated/invalid station");
            seen_station[i] = true;
            auto it = std::find_if(r.operations.begin(), r.operations.end(),
                [i](const StopOperation& op) { return op.station == i; });
            if (it == r.operations.end() || std::count_if(r.operations.begin(), r.operations.end(),
                [i](const StopOperation& op) { return op.station == i; }) != 1)
                throw std::invalid_argument("Balanced relocation missing/duplicate operation");
            pickup[i] = it->pickup; drop[i] = it->drop; signed_op[i] = pickup[i] - drop[i];
            s.nodes.push_back(i); s.pickup += pickup[i]; s.drop += drop[i];
        }
    }
    const auto verified = verifySolution(in, routes, lambda);
    if (!verified.feasible || !verified.errors.empty() || !verified.original_objective_recomputed)
        throw std::invalid_argument("Balanced relocation refuses an invalid physical witness");
    const auto current = round78DurationPotential(verified);
    for (auto& s : states) {
        s.load.push_back(0);
        for (int node : s.nodes) s.load.push_back(s.load.back() + signed_op[node]);
    }
    ++stats.passes;
    Round78BlockChoice best;
    if (expired(deadline, stats)) return best;
    for (int source = 0; source < in.M; ++source) {
        const auto& a = states[source];
        for (int first = 0; first < static_cast<int>(a.nodes.size()); ++first) {
            Integer min_relative = 0, max_relative = 0, block_pickup = 0, block_drop = 0;
            for (int last = first + 1; last <= static_cast<int>(a.nodes.size()); ++last) {
                if (expired(deadline, stats)) return best;
                const int node = a.nodes[last - 1];
                block_pickup += pickup[node]; block_drop += drop[node];
                min_relative = std::min(min_relative, a.load[last] - a.load[first]);
                max_relative = std::max(max_relative, a.load[last] - a.load[first]);
                if (a.load[last] != a.load[first]) continue;
                ++stats.balanced_blocks;
                auto shortened = a.nodes;
                shortened.erase(shortened.begin() + first, shortened.begin() + last);
                const double source_duration = duration(in, shortened,
                    a.pickup - block_pickup, a.drop - block_drop);
                for (int target = 0; target < in.M; ++target) if (target != source) {
                    const auto& b = states[target];
                    for (int leg = 0; leg <= static_cast<int>(b.nodes.size()); ++leg) {
                        if (expired(deadline, stats)) return best;
                        ++stats.placements;
                        if (b.load[leg] + min_relative < 0 ||
                            b.load[leg] + max_relative > in.Q[target]) continue;
                        ++stats.load_feasible;
                        auto enlarged = b.nodes;
                        enlarged.insert(enlarged.begin() + leg, a.nodes.begin() + first, a.nodes.begin() + last);
                        const double target_duration = duration(in, enlarged,
                            b.pickup + block_pickup, b.drop + block_drop);
                        if (!std::isfinite(source_duration) || !std::isfinite(target_duration) ||
                            source_duration > in.total_time_limit + 1e-7 ||
                            target_duration > in.total_time_limit + 1e-7) continue;
                        ++stats.feasible_placements;
                        auto potential = verified.route_duration;
                        potential[source] = source_duration; potential[target] = target_duration;
                        std::sort(potential.begin(), potential.end(), std::greater<double>());
                        // Exact finite tuple order: never skip a tiny earlier increase.
                        if (!(potential < current)) continue;
                        ++stats.improving_placements;
                        Round78BlockChoice c{true, source, first, last, target, leg, potential};
                        if (!best.found || potential < best.duration_potential ||
                            (potential == best.duration_potential && key(c) < key(best))) best = std::move(c);
                    }
                }
            }
        }
    }
    return best;
}

std::vector<RoutePlan> applyRound78BalancedRelocation(const std::vector<RoutePlan>& routes,
    const Round78BlockChoice& c) {
    if (!c.found || c.source < 0 || c.target < 0 || c.source == c.target ||
        c.first < 0 || c.last <= c.first || c.leg < 0)
        throw std::invalid_argument("Invalid balanced relocation choice");
    auto out = routes;
    auto source = std::find_if(out.begin(), out.end(), [&](const RoutePlan& r) { return r.vehicle == c.source; });
    if (source == out.end() || c.last > static_cast<int>(source->nodes.size()) - 2)
        throw std::invalid_argument("Balanced source interval outside route");
    std::vector<int> block(source->nodes.begin() + c.first + 1, source->nodes.begin() + c.last + 1);
    std::vector<StopOperation> operations;
    Integer net = 0;
    for (int i : block) {
        auto op = std::find_if(source->operations.begin(), source->operations.end(),
            [i](const StopOperation& x) { return x.station == i; });
        if (op == source->operations.end()) throw std::invalid_argument("Missing block operation");
        operations.push_back(*op); net += Integer(op->pickup) - op->drop;
    }
    if (net) throw std::invalid_argument("Relocated block is not balanced");
    source->nodes.erase(source->nodes.begin() + c.first + 1, source->nodes.begin() + c.last + 1);
    source->operations.erase(std::remove_if(source->operations.begin(), source->operations.end(),
        [&](const StopOperation& x) { return std::find(block.begin(), block.end(), x.station) != block.end(); }),
        source->operations.end());
    if (source->operations.empty()) out.erase(source);
    auto target = std::find_if(out.begin(), out.end(), [&](const RoutePlan& r) { return r.vehicle == c.target; });
    if (target == out.end()) {
        out.push_back(RoutePlan{c.target, {0, 0}, {}}); target = out.end() - 1;
    }
    if (c.leg > static_cast<int>(target->nodes.size()) - 2)
        throw std::invalid_argument("Balanced target leg outside route");
    target->nodes.insert(target->nodes.begin() + c.leg + 1, block.begin(), block.end());
    target->operations.insert(target->operations.end(), operations.begin(), operations.end());
    std::sort(out.begin(), out.end(), [](const RoutePlan& a, const RoutePlan& b) { return a.vehicle < b.vehicle; });
    return out;
}
} // namespace ebrp
