#include "HgaTgbcRunner.hpp"

#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Round60Candidates.hpp"
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

bool writeCandidateLedger(
    const std::filesystem::path& path,
    const std::vector<CandidateObservation>& observations) noexcept {
    if (path.empty()) return true;
    try {
        if (path.has_parent_path()) {
            std::filesystem::create_directories(path.parent_path());
        }
        std::ofstream out(path, std::ios::out | std::ios::trunc);
        if (!out) return false;
        out << "event,source,generation,source_elapsed_seconds,content_sha256,"
               "duplicate,verifier_passed,published,objective,"
               "verification_seconds,reason\n";
        out << std::setprecision(17);
        for (std::size_t index = 0; index < observations.size(); ++index) {
            const CandidateObservation& observation = observations[index];
            out << index << ',' << observation.source << ','
                << observation.generation << ','
                << observation.source_elapsed_seconds << ','
                << observation.content_sha256 << ',' << observation.duplicate
                << ',' << observation.verifier_passed << ','
                << observation.published << ',' << observation.objective << ','
                << observation.verification_seconds << ','
                << observation.reason << '\n';
        }
        return static_cast<bool>(out);
    } catch (...) {
        return false;
    }
}

} // namespace

HgaTgbcResult runHgaTgbcNative(const Instance& instance,
                               const HgaTgbcOptions& options) {
    const auto started = std::chrono::steady_clock::now();
    HgaTgbcResult out;
    out.stop_mode = options.stop_mode;
    const bool decoded_descent = options.stop_mode == "decoded-descent";
    if (decoded_descent && options.fixed_generations >= 0)
        throw std::runtime_error("Decoded descent cannot use a generation quota");
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
    ga.set_fixed_generations(options.fixed_generations);
    if (options.fixed_generations >= 0) {
        ga.set_absolute_deadline(started + std::chrono::seconds(
            std::max(1, options.max_time_seconds)));
    }
    ga.set_generation_stagnation_stop(
        options.stop_mode == "generation-stagnation");
    ga.set_decoded_descent_only(decoded_descent);
    ga.set_decoder_compaction_mode(1);
    ga.set_decode_cache_max_entries(200000);
    VerifiedCandidateStore published_candidates;
    if (options.publish_verified_improvements || options.stop_on_verified_zero) {
        ga.set_best_observer(
            [&](const std::vector<std::vector<int>>& sequences,
                const std::vector<int>& operations,
                double,
                long long generation) {
                const auto observer_started = std::chrono::steady_clock::now();
                const double event_seconds = std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - started).count();
                auto routes = routesFromHgaDecode(instance, sequences, operations);
                out.conversion_seconds += std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - observer_started).count();
                const bool published = published_candidates.consider(
                    instance, options.lambda, routes,
                    decoded_descent ? "decoded_descent_verified_improvement"
                        : (generation == 0 ? "hga_initial_population_best"
                                           : "hga_strict_improvement"),
                    options.candidate_model_identity, generation,
                    event_seconds, 0.0);
                // Same tolerance as main's existing F >= 0 certificate. The
                // observer sees a complete cached decode, never raw fitness.
                if (options.stop_on_verified_zero && published_candidates.hasBest() &&
                    published_candidates.best().objective >= 0.0 &&
                    published_candidates.best().objective <= 1e-12 &&
                    !out.verified_zero_stop) {
                    out.verified_zero_stop = true;
                    out.verified_zero_seconds = std::chrono::duration<double>(
                        std::chrono::steady_clock::now() - started).count();
                    ga.request_verified_stop();
                    if (options.process_options) recordProcessPhase(
                        *options.process_options, "round65_verified_zero", "certified",
                        "complete_cached_decode_independently_verified;F_ge_0");
                }
                if(published && out.first_nonempty_seconds<0 &&
                    std::any_of(routes.begin(),routes.end(),[](const RoutePlan& r) { return !r.operations.empty(); }))
                    out.first_nonempty_seconds=event_seconds;
                out.observer_seconds += std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - observer_started).count();
            });
    }
    if (options.process_options &&
        processDeadlineConfigured(*options.process_options)) {
        double remaining =
            processWorkRemainingSeconds(*options.process_options);
        if (options.fixed_generations >= 0) remaining = std::min(remaining,
            std::max(0.0, options.max_time_seconds - std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count()));
        ga.set_absolute_deadline(
            std::chrono::steady_clock::now() +
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(
                std::chrono::duration<double>(std::max(0.0, remaining))));
    }
    if (options.process_options) {
        recordProcessPhase(
            *options.process_options, "hga_start", "start",
            "label=" + options.phase_label +
            (decoded_descent ? ";finite_random_seed_decoded_descent"
                             : ";native_generation_stagnation_hga"));
    }
    ga.run();
    out.global_deadline_reached = ga.stopped_on_absolute_deadline();
    out.candidate_observer_failed =
        ga.best_observer_failed_and_disabled();
    if (out.candidate_observer_failed) {
        out.notes.push_back(
            decoded_descent
                ? "candidate observer failed and was disabled; decoded descent continued"
                : "optional HGA candidate observer failed and was disabled; the original HGA search continued");
    }
    if (options.process_options) {
        const std::string stop_status = out.global_deadline_reached ? "deadline_interrupted"
            : (decoded_descent && out.verified_zero_stop ? "certified_zero"
               : (decoded_descent && !ga.completed_decoded_descent() ? "incomplete" : "complete"));
        recordProcessPhase(
            *options.process_options,
            decoded_descent ? "decoded_descent_complete" : "hga_generation_loop_complete",
            stop_status,
            "label=" + options.phase_label +
            ";generations=" + std::to_string(ga.get_total_generations()) +
            ";no_improve=" +
            std::to_string(ga.get_generations_since_improvement()) +
            (decoded_descent ? ";completed_seeds=" + std::to_string(ga.get_descent_seeds_completed()) : ""));
    }

    out.total_generations = ga.get_total_generations();
    out.initialization_seconds = ga.get_initialization_seconds();
    out.decoder_seconds = ga.get_decoder_seconds();
    out.decoded_descent_complete = ga.completed_decoded_descent();
    out.decoded_descent_seeds_completed = ga.get_descent_seeds_completed();
    out.decoded_descent_passes = static_cast<long long>(ga.get_descent_passes().size());
    for (const auto& row : ga.get_descent_passes())
        out.decoded_descent_checks += static_cast<long long>(row.full_evaluations);
    out.hash_seconds = published_candidates.hash_seconds;
    out.copy_seconds = published_candidates.copy_seconds;
    if (options.fixed_generations >= 0) {
        out.fitness_history = ga.get_fitness_history();
        out.elapsed_history = ga.get_elapsed_history();
    }
    out.generations_since_improvement =
        ga.get_generations_since_improvement();
    out.objective_improvement_count = ga.get_objective_improvement_count();
    out.decoder_calls = ga.get_decoder_calls();
    out.final_fitness = ga.get_best_fitness();
    if (decoded_descent && !options.generation_log_path.empty()) {
        out.decoded_descent_log_path = options.generation_log_path.string() + ".descent.csv";
        try {
            if (out.decoded_descent_log_path.has_parent_path())
                std::filesystem::create_directories(out.decoded_descent_log_path.parent_path());
            std::ofstream trajectory(out.decoded_descent_log_path);
            trajectory << "seed,pass,neighbors,decoded_checks,accepted,exhausted,interrupted,"
                          "fitness_before,fitness_after,accepted_proxy_fitness,elapsed_seconds\n";
            trajectory << std::setprecision(17);
            for (const auto& row : ga.get_descent_passes()) {
                trajectory << row.seed << ',' << row.pass << ',' << row.neighbors << ','
                    << row.full_evaluations << ',' << row.accepted << ',' << row.exhausted << ','
                    << row.interrupted << ',' << row.fitness_before << ',' << row.fitness_after << ','
                    << row.accepted_proxy_fitness << ',' << row.elapsed_seconds << '\n';
            }
            if (!trajectory) throw std::runtime_error("Decoded descent trajectory write failed");
        } catch (...) {
            if (!options.retain_verified_on_log_failure) throw;
            out.candidate_evidence_persisted = false;
            out.notes.push_back("descent trajectory not persisted; verified memory retained");
        }
    }
    if (!decoded_descent) out.generation_log_path = options.generation_log_path;
    if (!decoded_descent && !options.generation_log_path.empty()) {
      try {
        if (options.generation_log_path.has_parent_path()) {
            std::filesystem::create_directories(
                options.generation_log_path.parent_path());
        }
        std::ofstream trajectory(options.generation_log_path,
                                 std::ios::out | std::ios::trunc);
        trajectory << "generation,elapsed_seconds,best_fitness,strict_improvement\n";
        const auto& fitness = ga.get_fitness_history();
        const auto& elapsed = ga.get_elapsed_history();
        const auto& improvements = ga.get_improvement_history();
        for (std::size_t index = 0; index < fitness.size(); ++index) {
            trajectory << index << ',' << std::setprecision(17)
                       << (index < elapsed.size() ? elapsed[index] : 0.0)
                       << ',' << fitness[index] << ','
                       << (index < improvements.size() && improvements[index]
                               ? "true" : "false") << '\n';
        }
        // Preserve the legacy silent stream-failure behavior when the new
        // retention/audit policy is off. Directory exceptions keep their
        // existing behavior through the catch below.
        if (!trajectory && options.retain_verified_on_log_failure)
            throw std::runtime_error("HGA trajectory write failed");
      } catch (...) {
        if (!options.retain_verified_on_log_failure) throw;
        out.candidate_evidence_persisted = false;
        out.notes.push_back("trajectory not persisted; verified memory retained");
      }
    }
    if (options.publish_verified_improvements || options.stop_on_verified_zero) {
        const auto ledger_started = std::chrono::steady_clock::now();
        const bool candidate_ledger_written = writeCandidateLedger(
            options.verified_candidate_log_path,
            published_candidates.observations());
        out.ledger_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - ledger_started).count();
        out.candidate_evidence_persisted = out.candidate_evidence_persisted &&
            candidate_ledger_written;
        out.candidate_observations = static_cast<long long>(
            published_candidates.observations().size());
        for (const CandidateObservation& observation :
                 published_candidates.observations()) {
            if (observation.verifier_passed) ++out.verified_candidate_count;
            if (observation.published) ++out.published_candidate_count;
            out.candidate_verification_seconds +=
                observation.verification_seconds;
        }
        if (!candidate_ledger_written) {
            out.candidate_observer_failed = true;
            if (!options.retain_verified_on_log_failure)
                out.published_candidate_count = 0;
            out.notes.push_back(options.retain_verified_on_log_failure
                ? "candidate ledger failed; independent memory retained; persistence audit invalid"
                : "optional HGA candidate ledger write failed; event publication was disabled and original HGA search retained");
        }
        if ((candidate_ledger_written || options.retain_verified_on_log_failure) &&
            published_candidates.hasBest()) {
            const VerifiedBrpCandidate& candidate = published_candidates.best();
            out.found = true;
            out.routes = candidate.routes;
            out.source_label = decoded_descent ? "decoded_descent_verified_event_publish"
                                              : "native_hga_tgbc_verified_event_publish";
            out.verified_objective = candidate.objective;
            out.retained_verified_event_candidate = true;
            out.retained_candidate_sha256 = candidate.content_sha256;
            std::ostringstream note;
            note << "retained independently verified "
                 << (decoded_descent ? "decoded-descent" : "HGA") << " event candidate="
                 << candidate.content_sha256
                 << ", objective=" << candidate.objective
                 << ", generation=" << candidate.generation;
            out.notes.push_back(note.str());
            out.wall_time_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count();
            return out;
        }
    }

    // PREFIX OFF extracts the same cached complete snapshot as ON, without
    // another stochastic/expensive decode. Used by the fixed-prefix diagnostic
    // and finite decoded descent; the legacy full HGA path is unchanged.
    if (options.fixed_generations >= 0 || decoded_descent) {
        auto routes = routesFromHgaDecode(instance, ga.get_best_solution(),
                                         ga.get_best_decoded_operations());
        VerifiedCandidateStore final_store;
        const std::string source = decoded_descent ? "decoded_descent_cached_best" : "prefix_cached_best";
        final_store.consider(instance, options.lambda, routes, source,
                             options.candidate_model_identity);
        if (final_store.hasBest()) {
            out.found = true;
            out.routes = final_store.best().routes;
            out.verified_objective = final_store.best().objective;
            out.retained_candidate_sha256 = final_store.best().content_sha256;
            out.source_label = source;
        }
        out.wall_time_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        return out;
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
