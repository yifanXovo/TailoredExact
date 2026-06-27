#pragma once

#include "Instance.hpp"
#include "Result.hpp"

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
};

struct HgaTgbcResult {
    bool found = false;
    std::vector<RoutePlan> routes;
    std::string source_label;
    std::vector<std::string> notes;
};

HgaTgbcResult runHgaTgbcNative(const Instance& instance,
                               const HgaTgbcOptions& options);

} // namespace ebrp
