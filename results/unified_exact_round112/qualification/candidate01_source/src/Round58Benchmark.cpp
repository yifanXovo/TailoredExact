#include "Round58Benchmark.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace ebrp {

Round58GapMetrics computeRound58Gap(
    std::optional<double> valid_lower_bound,
    std::optional<double> verified_upper_bound) {
    Round58GapMetrics result;
    if (!valid_lower_bound || !verified_upper_bound ||
        !std::isfinite(*valid_lower_bound) ||
        !std::isfinite(*verified_upper_bound)) {
        return result;
    }
    result.computable = true;
    result.absolute_gap = std::max(0.0,
        *verified_upper_bound - *valid_lower_bound);
    result.relative_gap = result.absolute_gap /
        std::max(std::fabs(*verified_upper_bound), 1e-6);
    result.scaled_gap = result.absolute_gap /
        std::max(1.0, std::fabs(*verified_upper_bound));
    return result;
}

std::string round58FirstMethod(const std::string& scenario_sha256) {
    if (scenario_sha256.size() != 64) {
        throw std::invalid_argument("Round 58 scenario SHA-256 must have 64 hexadecimal digits");
    }
    const char first = scenario_sha256.front();
    int value = -1;
    if (first >= '0' && first <= '9') value = first - '0';
    if (first >= 'a' && first <= 'f') value = first - 'a' + 10;
    if (first >= 'A' && first <= 'F') value = first - 'A' + 10;
    if (value < 0) {
        throw std::invalid_argument("Round 58 scenario SHA-256 is not hexadecimal");
    }
    return value % 2 == 0 ? "k1_am_sf" : "pgrb";
}

Round58ScreenExtensionDecision decideRound58ScreenExtension(
    const Round58ScreenPairInput& input) {
    Round58ScreenExtensionDecision result;
    if (input.k1_certified && input.pgrb_certified) {
        result.action = "pair_complete";
        result.reason = "both_screen_arms_strictly_certified";
        return result;
    }
    if (!input.k1_certified && !input.pgrb_certified) {
        result.extend_k1_to_10800 = true;
        result.extend_pgrb_to_10800 = true;
        result.action = "both_extensions_required";
        result.reason = "neither_screen_arm_certified";
        return result;
    }
    if (input.k1_certified) {
        const bool near = input.pgrb_relative_gap &&
            *input.pgrb_relative_gap <= 0.10;
        const bool hard = input.k1_completion_seconds >= 2700.0;
        result.extend_pgrb_to_10800 = near || hard;
        result.action = result.extend_pgrb_to_10800
            ? "pgrb_extension_required"
            : "no_extension_due_to_large_remaining_gap";
        result.reason = near ? "uncertified_pgrb_screen_gap_at_most_0.10"
            : (hard ? "certified_k1_screen_time_at_least_2700"
                    : "one_certified_but_extension_gate_not_met");
        return result;
    }
    const bool near = input.k1_relative_gap &&
        *input.k1_relative_gap <= 0.10;
    const bool hard = input.pgrb_completion_seconds >= 2700.0;
    result.extend_k1_to_10800 = near || hard;
    result.action = result.extend_k1_to_10800
        ? "k1_extension_required"
        : "no_extension_due_to_large_remaining_gap";
    result.reason = near ? "uncertified_k1_screen_gap_at_most_0.10"
        : (hard ? "certified_pgrb_screen_time_at_least_2700"
                : "one_certified_but_extension_gate_not_met");
    return result;
}

Round58NearConvergenceDecision decideRound58NearConvergenceExtension(
    bool certified, std::optional<double> relative_gap,
    int completed_cap_seconds) {
    Round58NearConvergenceDecision result;
    if (certified) {
        result.reason = "already_strictly_certified";
        return result;
    }
    if (!relative_gap || !std::isfinite(*relative_gap)) {
        result.reason = "relative_gap_uncomputable";
        return result;
    }
    if (completed_cap_seconds == 10800) {
        if (*relative_gap <= 0.05) {
            result.extend = true;
            result.next_cap_seconds = 21600;
            result.reason = "10800_relative_gap_at_most_0.05";
        } else if (*relative_gap <= 0.10) {
            result.extend = true;
            result.next_cap_seconds = 16200;
            result.reason = "10800_relative_gap_between_0.05_and_0.10";
        } else {
            result.reason = "10800_relative_gap_above_0.10";
        }
        return result;
    }
    if (completed_cap_seconds == 16200) {
        if (*relative_gap <= 0.05) {
            result.extend = true;
            result.next_cap_seconds = 21600;
            result.reason = "16200_relative_gap_at_most_0.05";
        } else {
            result.reason = "16200_relative_gap_above_0.05";
        }
        return result;
    }
    result.reason = completed_cap_seconds >= 21600
        ? "absolute_21600_cap_reached"
        : "near_convergence_policy_not_applicable_at_this_cap";
    return result;
}

std::string classifyRound58Pair(
    bool k1_certified, bool pgrb_certified,
    std::optional<double> k1_common_relative_gap,
    std::optional<double> pgrb_common_relative_gap,
    double k1_exact_seconds, double pgrb_exact_seconds) {
    if (k1_certified && pgrb_certified) {
        constexpr double tolerance = 1e-9;
        if (k1_exact_seconds + tolerance < pgrb_exact_seconds) {
            return "both_certified_k1_faster";
        }
        if (pgrb_exact_seconds + tolerance < k1_exact_seconds) {
            return "both_certified_pgrb_faster";
        }
        return "both_certified_tie";
    }
    if (k1_certified) return "k1_only_certified";
    if (pgrb_certified) return "pgrb_only_certified";
    if (!k1_common_relative_gap || !pgrb_common_relative_gap ||
        !std::isfinite(*k1_common_relative_gap) ||
        !std::isfinite(*pgrb_common_relative_gap)) {
        return "invalid_or_uncomputable";
    }
    constexpr double tolerance = 1e-12;
    if (*k1_common_relative_gap + tolerance < *pgrb_common_relative_gap) {
        return "neither_certified_k1_better_bound";
    }
    if (*pgrb_common_relative_gap + tolerance < *k1_common_relative_gap) {
        return "neither_certified_pgrb_better_bound";
    }
    return "neither_certified_mixed_or_tie";
}

} // namespace ebrp

