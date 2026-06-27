#include "HgaTgbcRunner.hpp"

#include "Evaluator.hpp"
#include "hga_tgbc/GreedyMethods.h"
#include "hga_tgbc/HybridGA.h"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace ebrp {
namespace {

InstanceData toHgaInstance(const Instance& instance) {
    InstanceData out;
    out.V = instance.V;
    out.M = instance.M;
    out.Q = instance.Q;
    out.s = instance.initial;
    out.c = instance.capacity;
    out.Target = instance.target;
    out.weights = instance.weights;
    out.min_ratio = instance.min_ratio;
    out.dist = instance.dist;
    out.total_time_limit = instance.total_time_limit;
    out.load_time_unit = instance.pickup_time;
    out.unload_time_unit = instance.drop_time;
    out.MAX_tour_Len = static_cast<int>(std::ceil(instance.total_time_limit));
    return out;
}

std::vector<RoutePlan> routesFromHgaDecode(
    const Instance& instance,
    const std::vector<std::vector<int>>& route_sequences,
    const std::vector<int>& station_ops) {
    std::vector<RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        if (k < static_cast<int>(route_sequences.size())) {
            for (int station : route_sequences[k]) {
                if (station <= 0 || station > instance.V) continue;
                int op_value = 0;
                if (station - 1 < static_cast<int>(station_ops.size())) {
                    op_value = station_ops[station - 1];
                }
                if (op_value == 0) continue;
                route.nodes.push_back(station);
                StopOperation op;
                op.station = station;
                if (op_value > 0) op.pickup = op_value;
                if (op_value < 0) op.drop = -op_value;
                route.operations.push_back(op);
            }
        }
        route.nodes.push_back(0);
        routes[k] = std::move(route);
    }
    return routes;
}

} // namespace

HgaTgbcResult runHgaTgbcNative(const Instance& instance,
                               const HgaTgbcOptions& options) {
    HgaTgbcResult out;
    InstanceData hga_instance = toHgaInstance(instance);

    set_greedy_time_units(instance.pickup_time, instance.drop_time);
    set_greedy_objective_params(options.lambda, 1.0);
    set_greedy_route_stats(false);

    HybridGA_HGS<> ga(hga_instance,
                      options.pop_size,
                      options.crossover_rate,
                      options.crossover_mix_ratio,
                      options.mutation_rate,
                      std::max(1, options.max_time_seconds),
                      4,
                      std::max(1, options.max_time_seconds + 1),
                      std::max(1, options.iterations),
                      options.lambda,
                      1.0,
                      options.no_improve_generation_limit);
    ga.set_seed(options.seed);
    ga.set_decoder_compaction_mode(1);
    ga.set_decode_cache_max_entries(200000);
    ga.run();

    std::vector<std::vector<int>> best_sequences = ga.get_best_solution();
    SolutionResult_ORO decoded = nGreedyLU_RA_compact_full(
        1, instance.V, instance.M, instance.total_time_limit,
        best_sequences, instance.Q, instance.initial, instance.capacity,
        instance.target, instance.dist, std::max(1, options.iterations), -1.0,
        instance.weights, instance.min_ratio, options.lambda, 1.0, nullptr);

    std::vector<RoutePlan> routes =
        routesFromHgaDecode(instance, best_sequences, decoded.Y_Oper_best);
    Verification verification = verifySolution(instance, routes, options.lambda);
    if (verification.feasible && verification.objective_matches &&
        verification.errors.empty()) {
        out.found = true;
        out.routes = std::move(routes);
        out.source_label = "native_hga_tgbc";
        std::ostringstream note;
        note << "native HGA-TGBC decoded route plan verified objective="
             << verification.objective
             << ", hga_fitness=" << ga.get_best_fitness()
             << ", decoder_objective_value=" << decoded.objective_value;
        out.notes.push_back(note.str());
    } else {
        std::ostringstream note;
        note << "native HGA-TGBC candidate rejected by verifier";
        for (const std::string& error : verification.errors) {
            note << "; " << error;
        }
        out.notes.push_back(note.str());
    }
    return out;
}

} // namespace ebrp
