#pragma once

#include "Instance.hpp"

#include <string>

namespace ebrp {

enum class Round50BranchingPolicy {
    Default,
    PrimitiveFirst,
    RouteFirst,
    OperationFirst,
    Invalid,
};

enum class Round50VariableFamily {
    RoutingArc,
    VisitSelection,
    OperationMode,
    PickupQuantity,
    DropQuantity,
    VehicleLoad,
    FinalInventory,
    Auxiliary,
};

struct Round50IntervalMipPolicy {
    bool valid = false;
    std::string name;
    Round50BranchingPolicy branching = Round50BranchingPolicy::Invalid;
    std::string cut_formulation = "v0";
    std::string symmetry_numerical = "v0";
    std::string model_reuse = "v0";
    // Explicit default-off Round 51 formulation switch. Historical Round 50
    // policy names retain the fixed 100000 coefficient byte-for-byte.
    std::string subset_duration_big_m = "historical-100000";
    std::string adaptive_branching = "off";
    std::string failure_reason;
};

Round50IntervalMipPolicy parseRound50IntervalMipPolicy(
    const std::string& name);

Round50VariableFamily classifyRound50Variable(const std::string& name);
std::string round50VariableFamilyName(Round50VariableFamily family);
bool round50PrimitiveFamily(Round50VariableFamily family);
int round50BranchPriority(Round50BranchingPolicy policy,
                          Round50VariableFamily family);

// C1 may omit the mode-link row only when its transfer coefficient is zero,
// because the already-emitted visit-link row is then byte-identical.
bool round50OmitDuplicateModeLink(int transfer_upper_bound,
                                  bool exact_dedup_enabled);

// Freeze the current complete fixed-interval formulation independently of
// main-program preset expansion.  All Round 50 policies share these options;
// policy-specific changes are applied separately and uniformly.
void configureRound50IntervalMipV0(SolveOptions& options);

} // namespace ebrp
