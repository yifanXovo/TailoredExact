#pragma once

#include "Instance.hpp"
#include "Result.hpp"
#include <cstdint>
#include <vector>

namespace ebrp {
struct Round78BlockChoice {
    bool found = false;
    int source = -1, first = 0, last = 0, target = -1, leg = 0;
    // [first,last) are zero-based service positions, leg precedes target insertion.
    std::vector<double> duration_potential;
};
struct Round78BlockStats {
    std::uint64_t passes = 0, balanced_blocks = 0, placements = 0;
    std::uint64_t load_feasible = 0, feasible_placements = 0, improving_placements = 0;
    bool deadline_reached = false;
};
std::vector<double> round78DurationPotential(const Verification&);
Round78BlockChoice bestRound78BalancedRelocation(const Instance&,
    const std::vector<RoutePlan>&, double lambda, Round78BlockStats&,
    const SolveOptions* deadline = nullptr);
std::vector<RoutePlan> applyRound78BalancedRelocation(const std::vector<RoutePlan>&,
    const Round78BlockChoice&);
} // namespace ebrp
