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
    std::filesystem::path generation_log_path;
};

HgaTgbcResult runHgaTgbcNative(const Instance& instance,
                               const HgaTgbcOptions& options);

} // namespace ebrp
