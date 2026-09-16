#pragma once
#include "Round78BalancedRelocation.hpp"

namespace ebrp {
struct Round83Choice {
    bool found = false;
    int kind = 0; // 0: balanced relocation; 1: equal-net nonempty exchange
    int source = -1, first = 0, last = 0, target = -1, target_first = 0, target_last = 0;
    std::vector<double> duration_potential;
};
struct Round83Stats {
    Round78BlockStats relocation;
    std::uint64_t equal_net_pairs = 0, load_feasible = 0, feasible = 0, improving = 0;
    bool deadline = false;
};
Round83Choice bestRound83Neutral(const Instance&, const std::vector<RoutePlan>&,
    double lambda, Round83Stats&, const SolveOptions* deadline = nullptr);
std::vector<RoutePlan> applyRound83Neutral(const std::vector<RoutePlan>&, const Round83Choice&);
struct Round83Result : Round78BalancedDescentResult {
    std::uint64_t exchanges = 0, relocations = 0, equal_net_pairs = 0;
};
Round83Result runRound83ExchangeDescent(const Instance&, const SolveOptions&,
    const std::vector<RoutePlan>&, const std::filesystem::path& trace = {});
} // namespace ebrp
