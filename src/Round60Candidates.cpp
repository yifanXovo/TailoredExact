#include "Round60Candidates.hpp"

#include "Evaluator.hpp"
#include "FileSha256.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>
#include <tuple>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

double secondsSince(const Clock::time_point& started) {
    return std::chrono::duration<double>(Clock::now() - started).count();
}

double affinity(const Round60ConstructionInput& input,
                int vehicle,
                int from,
                int station) {
    const std::string suffix = std::to_string(vehicle) + "_" +
        std::to_string(station);
    const auto visit = input.relaxation_values.find("z_" + suffix);
    const auto arc = input.relaxation_values.find(
        "x_" + std::to_string(vehicle) + "_" +
        std::to_string(from) + "_" + std::to_string(station));
    return (visit == input.relaxation_values.end() ? 0.0 : visit->second) +
        (arc == input.relaxation_values.end() ? 0.0 : arc->second);
}

struct RouteState {
    RoutePlan route;
    int load = 0;
    int total_pickup = 0;
    double travel = 0.0;
};

double appendedTravel(const Instance& instance,
                      const RouteState& state,
                      int station) {
    const int from = state.route.nodes.size() > 2
        ? state.route.nodes[state.route.nodes.size() - 2] : 0;
    return state.travel - instance.dist[from][0] +
        instance.dist[from][station] + instance.dist[station][0];
}

double routeDuration(const Instance& instance,
                     double travel,
                     int total_pickup) {
    return travel + (instance.pickup_time + instance.drop_time) *
        static_cast<double>(total_pickup);
}

void appendOperation(RouteState& state,
                     int station,
                     int pickup,
                     int drop,
                     double new_travel) {
    state.route.nodes.insert(state.route.nodes.end() - 1, station);
    state.route.operations.push_back({station, pickup, drop});
    state.load += pickup - drop;
    state.total_pickup += pickup;
    state.travel = new_travel;
}

std::vector<RoutePlan> materializeRoutes(
    const std::vector<RouteState>& states) {
    std::vector<RoutePlan> routes;
    for (const RouteState& state : states) {
        if (!state.route.operations.empty()) routes.push_back(state.route);
    }
    return routes;
}

} // namespace

std::string canonicalCandidateSerialization(
    const std::vector<RoutePlan>& routes) {
    std::vector<RoutePlan> ordered = routes;
    std::sort(ordered.begin(), ordered.end(),
              [](const RoutePlan& a, const RoutePlan& b) {
                  return a.vehicle < b.vehicle;
              });
    std::ostringstream out;
    for (const RoutePlan& route : ordered) {
        out << "v=" << route.vehicle << ";nodes=";
        for (int node : route.nodes) out << node << ',';
        out << ";ops=";
        std::vector<StopOperation> operations = route.operations;
        std::sort(operations.begin(), operations.end(),
                  [](const StopOperation& a, const StopOperation& b) {
                      return a.station < b.station;
                  });
        for (const StopOperation& operation : operations) {
            out << operation.station << ':' << operation.pickup << ':'
                << operation.drop << ',';
        }
        out << '|';
    }
    return out.str();
}

bool VerifiedCandidateStore::consider(
    const Instance& instance,
    double lambda,
    const std::vector<RoutePlan>& routes,
    const std::string& source,
    const std::string& model_identity,
    long long generation,
    double source_elapsed_seconds,
    double generation_seconds) {
    CandidateObservation observation;
    observation.source = source;
    observation.generation = generation;
    observation.source_elapsed_seconds = source_elapsed_seconds;
    const auto hash_started = Clock::now();
    observation.content_sha256 = textSha256(
        canonicalCandidateSerialization(routes));
    hash_seconds += secondsSince(hash_started);
    if (!seen_.insert(observation.content_sha256).second) {
        observation.duplicate = true;
        observation.reason = "duplicate_candidate_hash";
        observations_.push_back(std::move(observation));
        return false;
    }

    const auto verify_started = Clock::now();
    const Verification verification = verifySolution(instance, routes, lambda);
    observation.verification_seconds = secondsSince(verify_started);
    std::vector<bool> vehicle_seen(static_cast<std::size_t>(
        std::max(0, instance.M)), false);
    bool vehicle_layout_valid = routes.size() <=
        static_cast<std::size_t>(std::max(0, instance.M));
    for (const RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M ||
            vehicle_seen[static_cast<std::size_t>(route.vehicle)]) {
            vehicle_layout_valid = false;
            break;
        }
        vehicle_seen[static_cast<std::size_t>(route.vehicle)] = true;
    }
    observation.verifier_passed = vehicle_layout_valid &&
        verification.original_solution_feasible &&
        verification.original_objective_recomputed &&
        verification.errors.empty() && std::isfinite(verification.objective);
    observation.objective = verification.objective;
    if (!observation.verifier_passed) {
        observation.reason = vehicle_layout_valid
            ? "independent_original_verifier_failed"
            : "duplicate_or_invalid_vehicle_route_layout";
        observations_.push_back(std::move(observation));
        return false;
    }
    const double tolerance = 1e-10 * std::max(
        1.0, std::fabs(verification.objective));
    if (has_best_ && verification.objective >= best_.objective - tolerance) {
        observation.reason = "verified_but_not_strictly_better";
        observations_.push_back(std::move(observation));
        return false;
    }

    VerifiedBrpCandidate candidate;
    candidate.verified = true;
    candidate.source = source;
    candidate.content_sha256 = observation.content_sha256;
    candidate.model_identity = model_identity;
    candidate.generation = generation;
    candidate.source_elapsed_seconds = source_elapsed_seconds;
    candidate.generation_seconds = generation_seconds;
    candidate.verification_seconds = observation.verification_seconds;
    candidate.objective = verification.objective;
    candidate.G = verification.G;
    candidate.P = verification.P;
    const auto copy_started = Clock::now();
    candidate.routes = routes;
    candidate.final_inventory = verification.final_inventory;
    best_ = std::move(candidate);
    copy_seconds += secondsSince(copy_started);
    has_best_ = true;
    observation.published = true;
    observation.reason = "published_monotone_verified_upper_bound";
    observations_.push_back(std::move(observation));
    return true;
}

Round60ConstructionResult constructRound60BrpCandidate(
    const Instance& instance,
    double lambda,
    const Round60ConstructionInput& input) {
    const auto started = Clock::now();
    Round60ConstructionResult out;
    if (instance.V <= 0 || instance.M <= 0 ||
        input.desired_inventory.size() !=
            static_cast<std::size_t>(instance.V + 1) ||
        input.maximum_evaluations <= 0 || input.maximum_stations <= 0) {
        out.reason = "invalid_construction_input";
        out.generation_seconds = secondsSince(started);
        return out;
    }

    std::vector<int> desired = input.desired_inventory;
    for (int station = 1; station <= instance.V; ++station) {
        desired[station] = std::max(
            0, std::min(instance.capacity[station], desired[station]));
    }
    std::vector<int> inventory = instance.initial;
    std::vector<RouteState> states(static_cast<std::size_t>(instance.M));
    for (int vehicle = 0; vehicle < instance.M; ++vehicle) {
        states[static_cast<std::size_t>(vehicle)].route.vehicle = vehicle;
        states[static_cast<std::size_t>(vehicle)].route.nodes = {0, 0};
    }
    std::set<int> used_stations;
    double incumbent = computeObjectiveParts(instance, inventory, lambda).objective;

    struct Move {
        bool valid = false;
        int vehicle = -1;
        int station = -1;
        int pickup = 0;
        int drop = 0;
        double objective = std::numeric_limits<double>::infinity();
        double affinity = 0.0;
        double travel = 0.0;
        double travel_increment = 0.0;
    };

    int accepted_stations = 0;
    while (out.objective_evaluations < input.maximum_evaluations &&
           accepted_stations < input.maximum_stations) {
        Move best;
        for (int vehicle = 0; vehicle < instance.M; ++vehicle) {
            const RouteState& state = states[static_cast<std::size_t>(vehicle)];
            const int from = state.route.nodes.size() > 2
                ? state.route.nodes[state.route.nodes.size() - 2] : 0;
            for (int station = 1; station <= instance.V; ++station) {
                if (used_stations.count(station)) continue;
                const int difference = desired[station] - inventory[station];
                if (difference == 0) continue;
                const bool pickup_direction = difference < 0;
                const int maximum_amount = pickup_direction
                    ? std::min(-difference,
                               instance.Q[vehicle] - state.load)
                    : std::min(difference, state.load);
                if (maximum_amount <= 0) continue;
                const double travel = appendedTravel(instance, state, station);
                for (int amount = 1; amount <= maximum_amount; ++amount) {
                    if (out.objective_evaluations >=
                        input.maximum_evaluations) break;
                    const int new_pickup = pickup_direction ? amount : 0;
                    if (routeDuration(instance, travel,
                                      state.total_pickup + new_pickup) >
                        instance.total_time_limit + 1e-9) {
                        continue;
                    }
                    std::vector<int> candidate_inventory = inventory;
                    candidate_inventory[station] +=
                        pickup_direction ? -amount : amount;
                    const double objective = computeObjectiveParts(
                        instance, candidate_inventory, lambda).objective;
                    ++out.objective_evaluations;
                    const double candidate_affinity = affinity(
                        input, vehicle, from, station);
                    const auto key = std::make_tuple(
                        objective, -candidate_affinity,
                        travel - state.travel, vehicle, station, amount);
                    const auto best_key = std::make_tuple(
                        best.objective, -best.affinity,
                        best.travel_increment, best.vehicle,
                        best.station, best.pickup + best.drop);
                    if (!best.valid || key < best_key) {
                        best.valid = true;
                        best.vehicle = vehicle;
                        best.station = station;
                        best.pickup = pickup_direction ? amount : 0;
                        best.drop = pickup_direction ? 0 : amount;
                        best.objective = objective;
                        best.affinity = candidate_affinity;
                        best.travel = travel;
                        best.travel_increment = travel - state.travel;
                    }
                }
            }
        }
        const double improve_tolerance = 1e-10 *
            std::max(1.0, std::fabs(incumbent));
        if (!best.valid || best.objective >= incumbent - improve_tolerance) {
            break;
        }
        RouteState& chosen = states[static_cast<std::size_t>(best.vehicle)];
        appendOperation(chosen, best.station, best.pickup, best.drop,
                        best.travel);
        inventory[best.station] += best.drop - best.pickup;
        used_stations.insert(best.station);
        incumbent = best.objective;
        ++accepted_stations;
    }

    if (used_stations.empty()) {
        out.reason = "no_strictly_improving_feasible_operation";
        out.generation_seconds = secondsSince(started);
        return out;
    }
    const std::vector<RoutePlan> routes = materializeRoutes(states);
    VerifiedCandidateStore store;
    const double generation_seconds = secondsSince(started);
    store.consider(instance, lambda, routes, input.source,
                   input.model_identity, -1, generation_seconds,
                   generation_seconds);
    if (!store.hasBest()) {
        out.reason = store.observations().empty()
            ? "candidate_store_rejected_without_observation"
            : store.observations().back().reason;
        out.generation_seconds = secondsSince(started);
        return out;
    }
    out.generated = true;
    out.reason = "verified_problem_specific_candidate";
    out.candidate = store.best();
    out.generation_seconds = secondsSince(started);
    out.candidate.generation_seconds = out.generation_seconds;
    return out;
}

CandidateLinearResidual validateCandidateLinearResidual(
    const SolverNeutralLinearModel& model,
    const std::vector<double>& values,
    double tolerance) {
    CandidateLinearResidual out;
    out.checked = true;
    const std::size_t rows = model.senses.size();
    if (model.variable_count < 0 ||
        values.size() != static_cast<std::size_t>(model.variable_count) ||
        model.rhs.size() != rows ||
        model.row_starts.size() != rows + 1 ||
        model.column_indices.size() != model.coefficients.size() ||
        model.row_starts.empty() || model.row_starts.front() != 0 ||
        model.row_starts.back() !=
            static_cast<int>(model.column_indices.size()) ||
        !std::isfinite(tolerance) || tolerance < 0.0) {
        out.failure_reason = "invalid_linear_model_or_candidate_dimensions";
        return out;
    }
    out.checked_rows = static_cast<long long>(rows);
    for (std::size_t row = 0; row < rows; ++row) {
        const int begin = model.row_starts[row];
        const int end = model.row_starts[row + 1];
        if (begin < 0 || end < begin ||
            end > static_cast<int>(model.column_indices.size()) ||
            !std::isfinite(model.rhs[row])) {
            out.failure_reason = "invalid_linear_row_encoding";
            return out;
        }
        double activity = 0.0;
        for (int offset = begin; offset < end; ++offset) {
            const int column = model.column_indices[
                static_cast<std::size_t>(offset)];
            const double coefficient = model.coefficients[
                static_cast<std::size_t>(offset)];
            if (column < 0 || column >= model.variable_count ||
                !std::isfinite(coefficient) ||
                !std::isfinite(values[static_cast<std::size_t>(column)])) {
                out.failure_reason = "invalid_linear_coefficient_or_value";
                return out;
            }
            activity += coefficient * values[static_cast<std::size_t>(column)];
        }
        double violation = 0.0;
        if (model.senses[row] == '<') {
            violation = activity - model.rhs[row];
        } else if (model.senses[row] == '>') {
            violation = model.rhs[row] - activity;
        } else if (model.senses[row] == '=') {
            violation = std::fabs(activity - model.rhs[row]);
        } else {
            out.failure_reason = "invalid_linear_row_sense";
            return out;
        }
        const double scaled_tolerance = tolerance * std::max(
            {1.0, std::fabs(activity), std::fabs(model.rhs[row])});
        if (violation > scaled_tolerance) {
            ++out.violated_rows;
            out.maximum_violation = std::max(out.maximum_violation, violation);
        }
    }
    out.valid = out.violated_rows == 0;
    out.failure_reason = out.valid ? "none" : "linear_constraint_violation";
    return out;
}

} // namespace ebrp
