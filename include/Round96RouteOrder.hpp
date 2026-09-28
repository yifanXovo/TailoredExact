#pragma once
#include "Round83BlockExchange.hpp"

namespace ebrp {
struct Round96OrderStats {
    std::uint64_t passes=0, proposals=0, load_feasible=0, duration_feasible=0;
    std::uint64_t accepted=0, old_neutral=0, insertions=0, quantities=0;
    bool exhausted=false, deadline=false, verification_failed=false, zero=false;
};
struct Round96OrderResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round96OrderStats stats;
};
// Original R83 closure, then complete same-route two-block order/orientation
// proposals. Neutral moves preserve inventory and strictly lower the original
// sorted duration tuple. No internal resource budget or optimization engine.
Round96OrderResult runRound96RouteOrder(const Instance&, const SolveOptions&,
    const std::vector<RoutePlan>&, const std::filesystem::path& trace = {});
} // namespace ebrp
