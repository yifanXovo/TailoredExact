#include "InventoryRouteCuts.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace ebrp {
namespace {

constexpr double kResidualTolerance = 1e-12;

struct FlowEdge {
    int to = 0;
    int reverse = 0;
    double capacity = 0.0;
};

class DeterministicDinic {
public:
    explicit DeterministicDinic(int nodes)
        : graph_(static_cast<std::size_t>(nodes)),
          level_(static_cast<std::size_t>(nodes)),
          next_(static_cast<std::size_t>(nodes)) {}

    void addArc(int from, int to, double capacity) {
        if (!(capacity >= 0.0) || !std::isfinite(capacity)) {
            throw std::runtime_error("invalid_mincut_capacity");
        }
        FlowEdge forward{to,
            static_cast<int>(graph_[static_cast<std::size_t>(to)].size()),
            capacity};
        FlowEdge reverse{from,
            static_cast<int>(graph_[static_cast<std::size_t>(from)].size()),
            0.0};
        graph_[static_cast<std::size_t>(from)].push_back(forward);
        graph_[static_cast<std::size_t>(to)].push_back(reverse);
    }

    double maxFlow(int source, int sink) {
        double total = 0.0;
        while (buildLevels(source, sink)) {
            std::fill(next_.begin(), next_.end(), 0);
            while (true) {
                const double sent = send(source, sink,
                    std::numeric_limits<double>::max() / 16.0);
                if (sent <= kResidualTolerance) break;
                total += sent;
            }
        }
        return total;
    }

    std::vector<bool> sourceSide(int source) const {
        std::vector<bool> seen(graph_.size(), false);
        std::queue<int> queue;
        seen[static_cast<std::size_t>(source)] = true;
        queue.push(source);
        while (!queue.empty()) {
            const int node = queue.front();
            queue.pop();
            for (const FlowEdge& edge : graph_[static_cast<std::size_t>(node)]) {
                if (edge.capacity <= kResidualTolerance ||
                    seen[static_cast<std::size_t>(edge.to)]) {
                    continue;
                }
                seen[static_cast<std::size_t>(edge.to)] = true;
                queue.push(edge.to);
            }
        }
        return seen;
    }

private:
    bool buildLevels(int source, int sink) {
        std::fill(level_.begin(), level_.end(), -1);
        std::queue<int> queue;
        level_[static_cast<std::size_t>(source)] = 0;
        queue.push(source);
        while (!queue.empty()) {
            const int node = queue.front();
            queue.pop();
            for (const FlowEdge& edge : graph_[static_cast<std::size_t>(node)]) {
                if (edge.capacity <= kResidualTolerance ||
                    level_[static_cast<std::size_t>(edge.to)] >= 0) {
                    continue;
                }
                level_[static_cast<std::size_t>(edge.to)] =
                    level_[static_cast<std::size_t>(node)] + 1;
                queue.push(edge.to);
            }
        }
        return level_[static_cast<std::size_t>(sink)] >= 0;
    }

    double send(int node, int sink, double available) {
        if (node == sink) return available;
        int& offset = next_[static_cast<std::size_t>(node)];
        while (offset < static_cast<int>(
                graph_[static_cast<std::size_t>(node)].size())) {
            FlowEdge& edge = graph_[static_cast<std::size_t>(node)][
                static_cast<std::size_t>(offset)];
            if (edge.capacity > kResidualTolerance &&
                level_[static_cast<std::size_t>(edge.to)] ==
                    level_[static_cast<std::size_t>(node)] + 1) {
                const double sent = send(
                    edge.to, sink, std::min(available, edge.capacity));
                if (sent > kResidualTolerance) {
                    edge.capacity -= sent;
                    graph_[static_cast<std::size_t>(edge.to)][
                        static_cast<std::size_t>(edge.reverse)].capacity += sent;
                    return sent;
                }
            }
            ++offset;
        }
        return 0.0;
    }

    std::vector<std::vector<FlowEdge>> graph_;
    std::vector<int> level_;
    std::vector<int> next_;
};

bool inbound(InventoryRouteCutKind kind) {
    return kind == InventoryRouteCutKind::MixedInbound ||
           kind == InventoryRouteCutKind::ProjectedInbound;
}

bool projected(InventoryRouteCutKind kind) {
    return kind == InventoryRouteCutKind::ProjectedInbound ||
           kind == InventoryRouteCutKind::ProjectedOutbound;
}

bool validState(const InventoryRouteLpState& state,
                InventoryRouteCutKind kind,
                std::string& reason) {
    const int V = state.station_count;
    if (V <= 0 || state.vehicle_capacities.empty() ||
        state.initial_inventory.size() != static_cast<std::size_t>(V + 1) ||
        state.final_inventory.size() != static_cast<std::size_t>(V + 1)) {
        reason = "inventory_route_state_dimension_mismatch";
        return false;
    }
    if (projected(kind) &&
        (state.final_inventory_lower.size() != static_cast<std::size_t>(V + 1) ||
         state.final_inventory_upper.size() != static_cast<std::size_t>(V + 1))) {
        reason = "projected_inventory_bounds_missing";
        return false;
    }
    for (int capacity : state.vehicle_capacities) {
        if (capacity <= 0) {
            reason = "invalid_vehicle_capacity";
            return false;
        }
    }
    for (int i = 0; i <= V; ++i) {
        if (!std::isfinite(state.initial_inventory[static_cast<std::size_t>(i)]) ||
            !std::isfinite(state.final_inventory[static_cast<std::size_t>(i)])) {
            reason = "nonfinite_inventory_value";
            return false;
        }
        if (projected(kind) &&
            (!std::isfinite(state.final_inventory_lower[static_cast<std::size_t>(i)]) ||
             !std::isfinite(state.final_inventory_upper[static_cast<std::size_t>(i)]) ||
             state.final_inventory_lower[static_cast<std::size_t>(i)] >
                 state.final_inventory_upper[static_cast<std::size_t>(i)] + 1e-9)) {
            reason = "invalid_projected_inventory_bound";
            return false;
        }
    }
    for (const auto& arc : state.route_arcs) {
        if (arc.vehicle < 0 || arc.vehicle >=
                static_cast<int>(state.vehicle_capacities.size()) ||
            arc.from < 0 || arc.from > V || arc.to < 0 || arc.to > V ||
            arc.from == arc.to || !std::isfinite(arc.value) ||
            arc.value < -1e-8) {
            reason = "invalid_route_arc_value";
            return false;
        }
    }
    reason = "none";
    return true;
}

std::vector<double> nodeWeights(const InventoryRouteLpState& state,
                                InventoryRouteCutKind kind) {
    std::vector<double> weights(static_cast<std::size_t>(state.station_count + 1));
    for (int i = 1; i <= state.station_count; ++i) {
        const std::size_t index = static_cast<std::size_t>(i);
        if (kind == InventoryRouteCutKind::MixedInbound) {
            weights[index] = state.final_inventory[index] -
                state.initial_inventory[index];
        } else if (kind == InventoryRouteCutKind::MixedOutbound) {
            weights[index] = state.initial_inventory[index] -
                state.final_inventory[index];
        } else if (kind == InventoryRouteCutKind::ProjectedInbound) {
            weights[index] = state.final_inventory_lower[index] -
                state.initial_inventory[index];
        } else {
            weights[index] = state.initial_inventory[index] -
                state.final_inventory_upper[index];
        }
    }
    return weights;
}

std::map<std::pair<int, int>, double> aggregateCapacities(
    const InventoryRouteLpState& state) {
    std::map<std::pair<int, int>, double> capacities;
    for (const auto& arc : state.route_arcs) {
        const double clipped = std::max(0.0, arc.value);
        capacities[{arc.from, arc.to}] +=
            static_cast<double>(state.vehicle_capacities[
                static_cast<std::size_t>(arc.vehicle)]) * clipped;
    }
    return capacities;
}

std::string xName(int k, int from, int to) {
    return "x_" + std::to_string(k) + "_" + std::to_string(from) +
        "_" + std::to_string(to);
}

void addCoefficient(std::map<std::string, double>& coefficients,
                    const std::string& variable,
                    double value) {
    if (std::fabs(value) <= 1e-14) return;
    coefficients[variable] += value;
    if (std::fabs(coefficients[variable]) <= 1e-14) {
        coefficients.erase(variable);
    }
}

std::string canonicalNumber(double value) {
    if (std::fabs(value) <= 5e-14) value = 0.0;
    std::ostringstream out;
    out << std::setprecision(17) << value;
    return out.str();
}

void buildRow(const InventoryRouteLpState& state, InventoryRouteCut& cut) {
    std::set<int> selected(cut.subset.begin(), cut.subset.end());
    std::map<std::string, double> coefficients;
    const bool is_inbound = inbound(cut.kind);
    const bool is_projected = projected(cut.kind);
    double inventory_sum = 0.0;
    for (int i : cut.subset) {
        const std::size_t index = static_cast<std::size_t>(i);
        if (!is_projected) {
            addCoefficient(coefficients, "Y_" + std::to_string(i),
                is_inbound ? 1.0 : -1.0);
            inventory_sum += state.initial_inventory[index];
        } else if (is_inbound) {
            inventory_sum += state.final_inventory_lower[index] -
                state.initial_inventory[index];
        } else {
            inventory_sum += state.initial_inventory[index] -
                state.final_inventory_upper[index];
        }
    }
    for (int k = 0; k < static_cast<int>(state.vehicle_capacities.size()); ++k) {
        const double Q = static_cast<double>(state.vehicle_capacities[
            static_cast<std::size_t>(k)]);
        for (int from = 0; from <= state.station_count; ++from) {
            for (int to = 0; to <= state.station_count; ++to) {
                if (from == to) continue;
                const bool from_in = selected.count(from) != 0;
                const bool to_in = selected.count(to) != 0;
                const bool boundary = is_inbound
                    ? (!from_in && to_in) : (from_in && !to_in);
                if (boundary) {
                    addCoefficient(coefficients, xName(k, from, to),
                        is_projected ? Q : -Q);
                }
            }
        }
    }
    cut.sense = is_projected ? '>' : '<';
    cut.rhs = is_projected
        ? std::max(0.0, inventory_sum)
        : (is_inbound ? inventory_sum : -inventory_sum);
    for (const auto& item : coefficients) {
        cut.row_coefficients.push_back({item.first, item.second});
    }
    std::ostringstream signature;
    signature << inventoryRouteCutKindName(cut.kind) << '|';
    for (std::size_t i = 0; i < cut.subset.size(); ++i) {
        if (i) signature << ',';
        signature << cut.subset[i];
    }
    signature << '|' << cut.sense << '|' << canonicalNumber(cut.rhs);
    for (const auto& coefficient : cut.row_coefficients) {
        signature << '|' << coefficient.variable_name << ':'
                  << canonicalNumber(coefficient.coefficient);
    }
    cut.canonical_signature = signature.str();
    cut.scope = is_projected ? "interval-local" : "global";
}

} // namespace

std::string inventoryRouteCutKindName(InventoryRouteCutKind kind) {
    switch (kind) {
    case InventoryRouteCutKind::MixedInbound: return "IR-IN";
    case InventoryRouteCutKind::MixedOutbound: return "IR-OUT";
    case InventoryRouteCutKind::ProjectedInbound: return "IR-PROJ-IN";
    case InventoryRouteCutKind::ProjectedOutbound: return "IR-PROJ-OUT";
    }
    return "IR-UNKNOWN";
}

double recomputeInventoryRouteViolation(
    const InventoryRouteLpState& state,
    InventoryRouteCutKind kind,
    const std::vector<int>& subset) {
    const std::vector<double> weights = nodeWeights(state, kind);
    std::set<int> selected(subset.begin(), subset.end());
    double value = 0.0;
    for (int station : subset) {
        if (station <= 0 || station > state.station_count) {
            return std::numeric_limits<double>::quiet_NaN();
        }
        value += weights[static_cast<std::size_t>(station)];
    }
    const bool is_inbound = inbound(kind);
    for (const auto& arc : state.route_arcs) {
        const bool from_in = selected.count(arc.from) != 0;
        const bool to_in = selected.count(arc.to) != 0;
        const bool boundary = is_inbound
            ? (!from_in && to_in) : (from_in && !to_in);
        if (boundary) {
            value -= static_cast<double>(state.vehicle_capacities[
                static_cast<std::size_t>(arc.vehicle)]) *
                std::max(0.0, arc.value);
        }
    }
    return value;
}

InventoryRouteCut separateInventoryRouteCut(
    const InventoryRouteLpState& state,
    InventoryRouteCutKind kind,
    double certificate_tolerance) {
    InventoryRouteCut cut;
    cut.kind = kind;
    std::string reason;
    if (!(certificate_tolerance > 0.0) ||
        !std::isfinite(certificate_tolerance)) {
        cut.failure_reason = "invalid_certificate_tolerance";
        return cut;
    }
    if (!validState(state, kind, reason)) {
        cut.failure_reason = reason;
        return cut;
    }
    try {
        const int V = state.station_count;
        const int source = 0;
        const int sink = V + 1;
        DeterministicDinic flow(V + 2);
        const std::vector<double> weights = nodeWeights(state, kind);
        double positive_weight = 0.0;
        double scale = 1.0;
        for (int i = 1; i <= V; ++i) {
            const double weight = weights[static_cast<std::size_t>(i)];
            scale += std::fabs(weight);
            if (weight > 0.0) {
                flow.addArc(source, i, weight);
                positive_weight += weight;
            } else if (weight < 0.0) {
                flow.addArc(i, sink, -weight);
            }
        }
        const auto capacities = aggregateCapacities(state);
        const bool is_inbound = inbound(kind);
        for (const auto& item : capacities) {
            const int from = item.first.first;
            const int to = item.first.second;
            const double capacity = item.second;
            scale += capacity;
            if (capacity <= 0.0) continue;
            if (is_inbound) {
                // Selecting A on the source side must charge arcs entering A;
                // reverse station arcs and send depot-entry capacity to sink.
                if (from == 0 && to > 0) flow.addArc(to, sink, capacity);
                else if (from > 0 && to > 0) flow.addArc(to, from, capacity);
            } else {
                // The ordinary directed cut charges arcs leaving A.
                if (from > 0 && to == 0) flow.addArc(from, sink, capacity);
                else if (from > 0 && to > 0) flow.addArc(from, to, capacity);
            }
        }
        const double minimum_cut = flow.maxFlow(source, sink);
        const std::vector<bool> source_side = flow.sourceSide(source);
        for (int i = 1; i <= V; ++i) {
            if (source_side[static_cast<std::size_t>(i)]) cut.subset.push_back(i);
        }
        cut.mincut_objective = positive_weight - minimum_cut;
        cut.direct_recomputed_objective = recomputeInventoryRouteViolation(
            state, kind, cut.subset);
        const double reconstruction_tolerance = certificate_tolerance *
            std::max({1.0, std::fabs(cut.mincut_objective),
                      std::fabs(cut.direct_recomputed_objective)});
        if (!std::isfinite(cut.direct_recomputed_objective) ||
            std::fabs(cut.mincut_objective -
                      cut.direct_recomputed_objective) >
                reconstruction_tolerance) {
            cut.failure_reason = "mincut_direct_reconstruction_mismatch";
            return cut;
        }
        cut.raw_violation = cut.direct_recomputed_objective;
        cut.scaled_violation = cut.raw_violation / scale;
        cut.violated = !cut.subset.empty() &&
            cut.raw_violation > certificate_tolerance * scale;
        buildRow(state, cut);
        cut.valid = true;
        cut.failure_reason = "none";
        return cut;
    } catch (const std::exception& ex) {
        cut.failure_reason = ex.what();
        return cut;
    }
}

InventoryRouteSeparationResult separateInventoryRouteCuts(
    const InventoryRouteLpState& state,
    double certificate_tolerance) {
    InventoryRouteSeparationResult out;
    out.mixed_inbound = separateInventoryRouteCut(
        state, InventoryRouteCutKind::MixedInbound, certificate_tolerance);
    out.mixed_outbound = separateInventoryRouteCut(
        state, InventoryRouteCutKind::MixedOutbound, certificate_tolerance);
    out.projected_inbound = separateInventoryRouteCut(
        state, InventoryRouteCutKind::ProjectedInbound, certificate_tolerance);
    out.projected_outbound = separateInventoryRouteCut(
        state, InventoryRouteCutKind::ProjectedOutbound, certificate_tolerance);
    out.valid = out.mixed_inbound.valid && out.mixed_outbound.valid &&
        out.projected_inbound.valid && out.projected_outbound.valid;
    out.failure_reason = out.valid ? "none" :
        (!out.mixed_inbound.valid ? out.mixed_inbound.failure_reason :
         !out.mixed_outbound.valid ? out.mixed_outbound.failure_reason :
         !out.projected_inbound.valid ? out.projected_inbound.failure_reason :
         out.projected_outbound.failure_reason);
    return out;
}

} // namespace ebrp
