#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <filesystem>
#include <string>
#include <vector>

namespace ebrp {

struct HgaTgbcOptions {
    double lambda = 0.15;
    unsigned seed = 20260626u;
    int pop_size = 24;
    double crossover_rate = 0.85;
    double crossover_mix_ratio = 0.65;
    double mutation_rate = 0.30;
    int max_time_seconds = 60;
    int iterations = 10;
    int no_improve_generation_limit = 2000;
    std::string stop_mode = "legacy-time";
    std::filesystem::path generation_log_path;
    std::string phase_label = "primary_hga";
    const SolveOptions* process_options = nullptr;
    bool publish_verified_improvements = false;
    std::filesystem::path verified_candidate_log_path;
    std::string candidate_model_identity = "original_problem";
    // Round 61 only: initialization plus exactly this many generations.
    // Negative leaves every historical stopping/extraction rule unchanged.
    int fixed_generations = -1;
    bool retain_verified_on_log_failure = false;
    bool stop_on_verified_zero = false;
};

struct HgaTgbcResult {
    bool found = false;
    std::vector<RoutePlan> routes;
    std::string source_label;
    std::vector<std::string> notes;
    std::string stop_mode = "legacy-time";
    long long total_generations = 0;
    long long generations_since_improvement = 0;
    long long objective_improvement_count = 0;
    long long decoder_calls = 0;
    double final_fitness = 0.0;
    double verified_objective = 0.0;
    double wall_time_seconds = 0.0;
    bool global_deadline_reached = false;
    bool retained_verified_event_candidate = false;
    bool candidate_observer_failed = false;
    long long candidate_observations = 0;
    long long verified_candidate_count = 0;
    long long published_candidate_count = 0;
    double candidate_verification_seconds = 0.0;
    std::string retained_candidate_sha256;
    std::filesystem::path generation_log_path;
    bool candidate_evidence_persisted = true;
    bool verified_zero_stop = false;
    double verified_zero_seconds = -1.0;
    double initialization_seconds = 0.0;
    double decoder_seconds = 0.0;
    double observer_seconds = 0.0;
    double conversion_seconds = 0.0;
    double hash_seconds = 0.0;
    double copy_seconds = 0.0;
    double ledger_seconds = 0.0;
    double first_nonempty_seconds = -1.0;
    std::vector<double> fitness_history;
    std::vector<double> elapsed_history;
};

HgaTgbcResult runHgaTgbcNative(const Instance& instance,
                               const HgaTgbcOptions& options);

} // namespace ebrp
