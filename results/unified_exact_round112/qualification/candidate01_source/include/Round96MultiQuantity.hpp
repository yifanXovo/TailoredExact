#pragma once
#include "Instance.hpp"
#include "Result.hpp"
#include <cstdint>
#include <vector>
namespace ebrp {
struct Round96MultiStats {
    std::uint64_t passes=0, directions=0, points=0, physical=0, accepted=0;
    bool exhausted=false, deadline=false;
};
struct Round96MultiResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round96MultiStats stats;
    std::vector<std::vector<int>> accepted_inventories;
};
// Uniform complete integer rays on same-route 3/4-station sets, not full blocks.
// Only the common whole-run deadline may interrupt an otherwise exhaustive pass.
Round96MultiResult runRound96MultiQuantity(const Instance&,const SolveOptions&,
                                         const std::vector<RoutePlan>&);
}
