#pragma once

#include "Result.hpp"

#include <filesystem>
#include <string>
#include <unordered_map>

namespace ebrp {

struct TailoredBCCplexApiProbe {
    bool dll_found = false;
    bool required_symbols_found = false;
    bool callbacks_available = false;
    std::string dll_path;
    std::string fail_reason;
};

struct TailoredBCCplexApiSolveResult {
    bool attempted = false;
    bool available = false;
    bool solved = false;
    int return_code = -1;
    int status_code = 0;
    std::string status;
    std::string fail_reason;
    double objective = 0.0;
    double best_bound = 0.0;
    long long node_count = 0;
    long long relaxation_callback_calls = 0;
    long long candidate_callback_calls = 0;
    long long branch_callback_calls = 0;
    long long progress_callback_calls = 0;
    long long user_cuts_added = 0;
    long long lazy_rejections = 0;
    long long incumbents_seen = 0;
    long long incumbents_verified = 0;
    long long incumbents_rejected = 0;
    long long gini_branches_created = 0;
    long long branch_priorities_applied = 0;
    std::string branch_priority_status;
    std::unordered_map<std::string, double> values;
};

TailoredBCCplexApiProbe probeTailoredBCCplexApi();

TailoredBCCplexApiSolveResult solveLpWithTailoredBCCplexApi(
    const std::filesystem::path& lp_path,
    double time_limit_seconds,
    int threads,
    double gamma_L,
    double gamma_U,
    bool add_redundant_gini_user_cut,
    bool enable_candidate_validation,
    bool enable_gini_branching,
    bool enable_branch_priorities,
    double gini_branch_min_width);

} // namespace ebrp
