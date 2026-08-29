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
    // Round 52 default-off tailored user-cut/static ablation policy.
    std::string tailored_cut_policy = "off";
    int tailored_cut_support_rank = 0;
    // Round 53 diagnostic-only callback decomposition.  "off" preserves
    // every pre-Round-53 policy.  The c0--c5 values are uniform policies and
    // are never inferred from an instance or solve state.
    std::string round53_callback_mode = "off";
    // Round 54 default-off external root closure. It is a run-level research
    // policy and never changes the frozen F0-CLEAN alias.
    std::string inventory_route_root_closure = "off";
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
