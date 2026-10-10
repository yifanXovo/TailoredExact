#pragma once

#include <optional>
#include <string>

namespace ebrp {

struct Round58GapMetrics {
    bool computable = false;
    double absolute_gap = 0.0;
    double relative_gap = 0.0;
    double scaled_gap = 0.0;
};

Round58GapMetrics computeRound58Gap(
    std::optional<double> valid_lower_bound,
    std::optional<double> verified_upper_bound);

std::string round58FirstMethod(const std::string& scenario_sha256);

struct Round58ScreenPairInput {
    bool k1_certified = false;
    bool pgrb_certified = false;
    double k1_completion_seconds = 0.0;
    double pgrb_completion_seconds = 0.0;
    std::optional<double> k1_relative_gap;
    std::optional<double> pgrb_relative_gap;
};

struct Round58ScreenExtensionDecision {
    bool extend_k1_to_10800 = false;
    bool extend_pgrb_to_10800 = false;
    std::string action;
    std::string reason;
};

Round58ScreenExtensionDecision decideRound58ScreenExtension(
    const Round58ScreenPairInput& input);

struct Round58NearConvergenceDecision {
    bool extend = false;
    int next_cap_seconds = 0;
    std::string reason;
};

Round58NearConvergenceDecision decideRound58NearConvergenceExtension(
    bool certified, std::optional<double> relative_gap,
    int completed_cap_seconds);

std::string classifyRound58Pair(
    bool k1_certified, bool pgrb_certified,
    std::optional<double> k1_common_relative_gap,
    std::optional<double> pgrb_common_relative_gap,
    double k1_exact_seconds = 0.0, double pgrb_exact_seconds = 0.0);

} // namespace ebrp

