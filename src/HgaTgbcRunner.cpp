#include "HgaTgbcRunner.hpp"

#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include "hga_tgbc/GreedyMethods.h"
#include "hga_tgbc/HybridGA.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
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
    const auto started = std::chrono::steady_clock::now();
    HgaTgbcResult out;
    out.stop_mode = options.stop_mode;
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
    ga.set_generation_stagnation_stop(
        options.stop_mode == "generation-stagnation");
    ga.set_decoder_compaction_mode(1);
    ga.set_decode_cache_max_entries(200000);
    if (options.process_options &&
        processDeadlineConfigured(*options.process_options)) {
        const double remaining =
            processWorkRemainingSeconds(*options.process_options);
        ga.set_absolute_deadline(
            std::chrono::steady_clock::now() +
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                std::chrono::duration<double>(std::max(0.0, remaining))));
    }
    if (options.process_options) {
        recordProcessPhase(
            *options.process_options, "hga_start", "start",
            "label=" + options.phase_label +
            ";native_generation_stagnation_hga");
    }
    ga.run();
    out.global_deadline_reached = ga.stopped_on_absolute_deadline();
    if (options.process_options) {
        recordProcessPhase(
            *options.process_options, "hga_generation_loop_complete",
            out.global_deadline_reached ? "deadline_interrupted" : "complete",
            "label=" + options.phase_label +
            ";generations=" + std::to_string(ga.get_total_generations()) +
            ";no_improve=" +
            std::to_string(ga.get_generations_since_improvement()));
    }

    out.total_generations = ga.get_total_generations();
    out.generations_since_improvement =
        ga.get_generations_since_improvement();
    out.objective_improvement_count = ga.get_objective_improvement_count();
    out.decoder_calls = ga.get_decoder_calls();
    out.final_fitness = ga.get_best_fitness();
    out.generation_log_path = options.generation_log_path;
    if (!options.generation_log_path.empty()) {
        if (options.generation_log_path.has_parent_path()) {
            std::filesystem::create_directories(
                options.generation_log_path.parent_path());
        }
        std::ofstream trajectory(options.generation_log_path,
                                 std::ios::out | std::ios::trunc);
        trajectory << "generation,best_fitness,strict_improvement\n";
        const auto& fitness = ga.get_fitness_history();
        const auto& improvements = ga.get_improvement_history();
        for (std::size_t index = 0; index < fitness.size(); ++index) {
            trajectory << index << ',' << std::setprecision(17)
                       << fitness[index] << ','
                       << (index < improvements.size() && improvements[index]
                               ? "true" : "false") << '\n';
        }
    }

    if (options.process_options) {
        recordProcessPhase(*options.process_options,
                           "hga_best_solution_extraction_start", "start",
                           "label=" + options.phase_label);
    }
    std::vector<std::vector<int>> best_sequences = ga.get_best_solution();
    if (options.process_options) {
        recordProcessPhase(*options.process_options,
                           "hga_best_solution_extraction_complete",
                           "complete", "label=" + options.phase_label);
    }
    if (options.process_options &&
        processWorkDeadlineReached(*options.process_options)) {
        recordProcessPhase(*options.process_options, "hga_route_decoding",
                           "skipped_deadline",
                           "label=" + options.phase_label +
                           ";no decoded candidate or verification claim");
        out.global_deadline_reached = true;
        out.wall_time_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        return out;
    }
    if (options.process_options) {
        recordProcessPhase(*options.process_options,
                           "hga_route_decoding_start", "start",
                           "label=" + options.phase_label);
    }
    SolutionResult_ORO decoded = nGreedyLU_RA_compact_full(
        1, instance.V, instance.M, instance.total_time_limit,
        best_sequences, instance.Q, instance.initial, instance.capacity,
        instance.target, instance.dist, std::max(1, options.iterations), -1.0,
        instance.weights, instance.min_ratio, options.lambda, 1.0, nullptr);
    if (options.process_options) {
        recordProcessPhase(*options.process_options,
                           "hga_route_decoding_complete", "complete",
                           "label=" + options.phase_label);
    }

    std::vector<RoutePlan> routes =
        routesFromHgaDecode(instance, best_sequences, decoded.Y_Oper_best);
    if (options.process_options) {
        recordProcessPhase(*options.process_options,
                           "independent_hga_verification_start", "start",
                           "label=" + options.phase_label);
    }
    Verification verification = verifySolution(instance, routes, options.lambda);
    if (options.process_options) {
        recordProcessPhase(
            *options.process_options, "independent_hga_verification_complete",
            processWorkDeadlineReached(*options.process_options)
                ? "completed_at_or_after_work_deadline" : "complete",
            "label=" + options.phase_label + ";feasible=" +
                (verification.feasible ? "true" : "false"));
    }
    if (verification.feasible && verification.objective_matches &&
        verification.errors.empty()) {
        out.found = true;
        out.routes = std::move(routes);
        out.source_label = "native_hga_tgbc";
        out.verified_objective = verification.objective;
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
    out.wall_time_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started).count();
    return out;
}

} // namespace ebrp
