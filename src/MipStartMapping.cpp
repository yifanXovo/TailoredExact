#include "MipStartMapping.hpp"

#include "Evaluator.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>
#include <set>
#include <unordered_map>

namespace ebrp {
namespace {

bool parseIndexedName(const std::string& name,
                      const std::string& prefix,
                      int expected,
                      std::vector<int>& indices) {
    if (name.rfind(prefix, 0) != 0) return false;
    indices.clear();
    const std::string rest = name.substr(prefix.size());
    std::size_t start = 0;
    while (start <= rest.size()) {
        const std::size_t end = rest.find('_', start);
        const std::string token = rest.substr(
            start, end == std::string::npos ? std::string::npos : end - start);
        if (token.empty() ||
            !std::all_of(token.begin(), token.end(), [](unsigned char ch) {
                return ch >= '0' && ch <= '9';
            })) {
            return false;
        }
        indices.push_back(std::stoi(token));
        if (end == std::string::npos) break;
        start = end + 1;
    }
    return static_cast<int>(indices.size()) == expected;
}

} // namespace

SolverNeutralMipStart mapVerifiedRoutesToCanonicalModel(
    const Instance& instance,
    const SolveOptions& options,
    const std::vector<RoutePlan>& routes,
    const std::string& source,
    double gamma_L,
    double gamma_U,
    double non_strict_cutoff,
    const SolverNeutralModelDomain& domain) {
    const auto started = std::chrono::steady_clock::now();
    SolverNeutralMipStart out;
    out.source = source;
    auto finish = [&](const std::string& reason) {
        out.failure_reason = reason;
        out.mapping_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        return out;
    };
    const std::size_t n = domain.names.size();
    if (n == 0 || domain.lower_bounds.size() != n ||
        domain.upper_bounds.size() != n || domain.variable_types.size() != n) {
        return finish("invalid_or_empty_model_domain");
    }
    if (!std::isfinite(gamma_L) || !std::isfinite(gamma_U) ||
        gamma_U < gamma_L - 1e-9 || !std::isfinite(non_strict_cutoff)) {
        return finish("invalid_interval_or_cutoff");
    }
    const Verification verification =
        verifySolution(instance, routes, options.lambda);
    out.candidate_independently_verified = true;
    out.original_problem_feasible =
        verification.original_solution_feasible && verification.errors.empty();
    out.objective_recomputed =
        verification.original_objective_recomputed &&
        std::isfinite(verification.objective);
    if (!out.original_problem_feasible || !out.objective_recomputed) {
        return finish("independent_original_verifier_failed");
    }
    out.objective = verification.objective;
    out.G = verification.G;
    out.P = verification.P;
    const ObjectiveParts objective_parts =
        computeObjectiveParts(instance, verification.final_inventory,
                              options.lambda);
    out.interval_membership_valid =
        out.G >= gamma_L - 1e-8 && out.G <= gamma_U + 1e-8;
    if (!out.interval_membership_valid) {
        return finish("verified_start_outside_static_gini_interval");
    }
    out.cutoff_valid = out.objective <= non_strict_cutoff +
        1e-8 * std::max({1.0, std::fabs(out.objective),
                         std::fabs(non_strict_cutoff)});
    if (!out.cutoff_valid) {
        return finish("verified_start_violates_non_strict_cutoff");
    }

    std::unordered_map<std::string, double> route_values;
    std::vector<int> final_inventory = instance.initial;
    std::set<int> used_vehicles;
    std::set<int> used_stations;
    for (const RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M ||
            !used_vehicles.insert(route.vehicle).second) {
            return finish("invalid_or_duplicate_route_vehicle");
        }
        if (route.nodes.size() < 2 || route.nodes.front() != 0 ||
            route.nodes.back() != 0) {
            return finish("route_not_depot_closed");
        }
        for (std::size_t position = 1; position < route.nodes.size(); ++position) {
            const int from = route.nodes[position - 1];
            const int to = route.nodes[position];
            if (from < 0 || from > instance.V || to < 0 ||
                to > instance.V || from == to) {
                return finish("invalid_start_arc");
            }
            const std::string base = std::to_string(route.vehicle) + "_" +
                std::to_string(from) + "_" + std::to_string(to);
            route_values["x_" + base] = 1.0;
            route_values["conn_" + base] =
                static_cast<double>(route.nodes.size() - 1 - position);
        }
        int load = 0;
        for (std::size_t position = 1;
             position + 1 < route.nodes.size(); ++position) {
            const int station = route.nodes[position];
            if (station <= 0 || station > instance.V ||
                !used_stations.insert(station).second) {
                return finish("invalid_or_duplicate_start_station");
            }
            const auto operation = std::find_if(
                route.operations.begin(), route.operations.end(),
                [&](const StopOperation& item) {
                    return item.station == station;
                });
            if (operation == route.operations.end() ||
                operation->pickup < 0 || operation->drop < 0 ||
                (operation->pickup > 0 && operation->drop > 0) ||
                (operation->pickup == 0 && operation->drop == 0)) {
                return finish("invalid_start_operation");
            }
            const std::string base = std::to_string(route.vehicle) + "_" +
                std::to_string(station);
            route_values["z_" + base] = 1.0;
            route_values["mode_" + base] =
                operation->pickup > 0 ? 1.0 : 0.0;
            route_values["p_" + base] = operation->pickup;
            route_values["d_" + base] = operation->drop;
            route_values["ord_" + base] = static_cast<double>(position);
            load += operation->pickup - operation->drop;
            if (load < 0 || load > instance.Q[route.vehicle]) {
                return finish("start_load_out_of_range");
            }
            route_values["load_" + base] = load;
            final_inventory[station] +=
                operation->drop - operation->pickup;
        }
    }
    // Validate the canonical used/unused ordering within every genuinely
    // interchangeable (equal-capacity) vehicle class.  Never relabel a route
    // across unequal capacities merely to manufacture a start.
    for (int lower = 0; lower < instance.M; ++lower) {
        for (int upper = lower + 1; upper < instance.M; ++upper) {
            if (instance.Q[lower] == instance.Q[upper] &&
                used_vehicles.count(lower) == 0 &&
                used_vehicles.count(upper) != 0) {
                return finish("noncanonical_equal_capacity_vehicle_symmetry");
            }
        }
    }
    out.vehicle_symmetry_canonicalization_valid = true;

    std::vector<double> ratio(static_cast<std::size_t>(instance.V + 1), 0.0);
    std::vector<double> deviation(
        static_cast<std::size_t>(instance.V + 1), 0.0);
    for (int station = 1; station <= instance.V; ++station) {
        ratio[station] = static_cast<double>(final_inventory[station]) /
            instance.target[station];
        deviation[station] = std::fabs(ratio[station] - 1.0);
    }
    const double ratio_min = instance.V > 0
        ? *std::min_element(ratio.begin() + 1, ratio.end()) : 0.0;
    const double ratio_max = instance.V > 0
        ? *std::max_element(ratio.begin() + 1, ratio.end()) : 0.0;
    std::vector<int> indices;
    auto routeFamily = [&](const std::string& name) {
        return parseIndexedName(name, "x_", 3, indices) ||
            parseIndexedName(name, "z_", 2, indices) ||
            parseIndexedName(name, "mode_", 2, indices) ||
            parseIndexedName(name, "p_", 2, indices) ||
            parseIndexedName(name, "d_", 2, indices) ||
            parseIndexedName(name, "load_", 2, indices) ||
            parseIndexedName(name, "ord_", 2, indices) ||
            parseIndexedName(name, "conn_", 3, indices);
    };
    out.values.assign(n, 0.0);
    for (std::size_t column = 0; column < n; ++column) {
        const std::string& name = domain.names[column];
        double value = 0.0;
        const auto direct = route_values.find(name);
        if (direct != route_values.end()) {
            value = direct->second;
        } else if (routeFamily(name)) {
            value = 0.0;
        } else if (name == "G") {
            value = out.G;
        } else if (name == "r_min") {
            value = ratio_min;
        } else if (name == "r_max") {
            value = ratio_max;
        } else if (name == "W_SP") {
            value = objective_parts.S * objective_parts.P;
        } else if (parseIndexedName(name, "Y_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = final_inventory[indices[0]];
        } else if (parseIndexedName(name, "r_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = ratio[indices[0]];
        } else if (parseIndexedName(name, "e_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = deviation[indices[0]];
        } else if (parseIndexedName(name, "h_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 1 && indices[1] <= instance.V) {
            value = std::fabs(ratio[indices[0]] - ratio[indices[1]]);
        } else if (parseIndexedName(name, "bit_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 0 && indices[1] < 63) {
            value = (final_inventory[indices[0]] >> indices[1]) & 1;
        } else if (parseIndexedName(name, "prod_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 0 && indices[1] < 63) {
            value = out.G *
                ((final_inventory[indices[0]] >> indices[1]) & 1);
        } else if (parseIndexedName(name, "zprod_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = out.G * final_inventory[indices[0]];
        } else {
            return finish("unsupported_complete_start_column:" + name);
        }
        if (!std::isfinite(value)) {
            return finish("nonfinite_start_value:" + name);
        }
        out.values[column] = value;
    }
    out.all_semantic_columns_mapped = true;
    out.no_unsupported_columns = true;
    out.bounds_valid = true;
    out.integrality_valid = true;
    for (std::size_t column = 0; column < n; ++column) {
        const double value = out.values[column];
        if (value < domain.lower_bounds[column] - 1e-7 ||
            value > domain.upper_bounds[column] + 1e-7) {
            out.bounds_valid = false;
            return finish("start_bound_violation:" + domain.names[column]);
        }
        const char type = domain.variable_types[column];
        if ((type == 'B' || type == 'I' || type == 'N') &&
            std::fabs(value - std::round(value)) > 1e-7) {
            out.integrality_valid = false;
            return finish("start_integrality_violation:" +
                          domain.names[column]);
        }
    }
    // Interval rows are generated by the shared valid-row factory and add no
    // independent semantic variable family.  A verified original solution
    // with mapped exact auxiliaries, in-range G, and a satisfied non-strict
    // cutoff therefore satisfies their proved validity preconditions.
    out.static_interval_rows_valid_by_factory_semantics = true;
    out.complete = true;
    return finish("none");
}

} // namespace ebrp
