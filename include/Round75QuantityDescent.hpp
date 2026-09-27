#pragma once

#include "Instance.hpp"
#include "Result.hpp"
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace ebrp {
struct Round75QuantityChoice {
    bool found = false;
    int first = 0;
    int second = 0; // zero means a single signed-operation change
    std::int64_t delta = 0; // s_first += delta, s_second -= delta
    double objective = 0;
};
struct Round75QuantityStats {
    std::uint64_t passes = 0, single_candidates = 0, pair_candidates = 0;
    std::uint64_t feasible_candidates = 0, objective_evaluations = 0;
    std::uint64_t accepted = 0, single_moves = 0, pair_moves = 0;
    std::uint64_t cross_vehicle_moves = 0, sign_flips = 0, removed_stops = 0;
    bool deadline_reached = false, exhausted = false, verification_failed = false;
    std::string rejection_reason;
};
struct Round75QuantityResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round75QuantityStats stats;
};

// Only currently served nodes; same fixed relative order and vehicle assignment.
// All legal integer single/pair quantities are considered, including sign flips
// and deletion of zero operations. This neighborhood never restricts the MIP.
Round75QuantityChoice bestRound75QuantityChange(const Instance&,
    const std::vector<RoutePlan>&, double lambda, Round75QuantityStats&,
    const SolveOptions* deadline = nullptr);
std::vector<RoutePlan> applyRound75QuantityChange(const std::vector<RoutePlan>&,
    const Round75QuantityChoice&);
Round75QuantityResult runRound75QuantityDescent(const Instance&,
    const SolveOptions&, const std::vector<RoutePlan>&,
    const std::filesystem::path& trace_path = {});
} // namespace ebrp
