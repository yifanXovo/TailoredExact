#pragma once

#include "Round73JointInsertion.hpp"
#include "Round75QuantityDescent.hpp"

namespace ebrp {
struct Round76ClosureStats {
    Round73InsertionStats insertion;
    Round75QuantityStats quantity;
    std::uint64_t accepted = 0, accepted_insertions = 0, accepted_quantities = 0;
    bool exhausted = false, deadline_reached = false, verification_failed = false;
};
struct Round76ClosureResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round76ClosureStats stats;
};

// Two current-witness proposal rules: R73 insertion gain/duration and R75
// minimum-F quantity change. Select the smaller proposed F; this is not a
// minimum-F oracle over the full union. Only joint absence proves exhaustion
// of these declared strict-improvement neighborhoods, never BRP optimality.
Round76ClosureResult runRound76PhysicalClosure(const Instance&,const SolveOptions&,
    const std::vector<RoutePlan>&,const std::filesystem::path& trace_path = {});
} // namespace ebrp
