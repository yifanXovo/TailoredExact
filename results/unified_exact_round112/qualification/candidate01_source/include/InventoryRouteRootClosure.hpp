#pragma once

#include "FixedIntervalMipBackend.hpp"
#include "InventoryRouteCuts.hpp"

#include <string>
#include <vector>

namespace ebrp {

enum class InventoryRouteClosureVariant {
    MixedFull,
    MixedProjectedFull,
    MixedOnePass,
    Invalid,
};

struct InventoryRouteClosureRound {
    int round = 0;
    bool lp_valid = false;
    bool lp_infeasible = false;
    double lp_objective = 0.0;
    double lp_work = 0.0;
    double lp_runtime_seconds = 0.0;
    double lp_simplex_iterations = 0.0;
    InventoryRouteSeparationResult separation;
    long long cuts_generated = 0;
    long long cuts_added = 0;
    long long duplicate_rejections = 0;
    long long dominated_rejections = 0;
    long long nonviolated_rejections = 0;
    std::string status;
};

struct InventoryRouteRootClosureResult {
    bool attempted = false;
    bool valid = false;
    bool converged = false;
    bool infeasible = false;
    bool fallback_required = false;
    std::string variant;
    std::string failure_reason = "not_attempted";
    double initial_lp_objective = 0.0;
    double final_lp_objective = 0.0;
    double cumulative_lp_work = 0.0;
    double cumulative_lp_runtime_seconds = 0.0;
    double cumulative_lp_simplex_iterations = 0.0;
    double model_read_seconds = 0.0;
    long long cuts_generated = 0;
    long long cuts_added = 0;
    long long duplicate_rejections = 0;
    long long dominated_rejections = 0;
    long long nonviolated_rejections = 0;
    std::vector<InventoryRouteCut> accepted_cuts;
    std::vector<InventoryRouteClosureRound> rounds;
};

InventoryRouteClosureVariant parseInventoryRouteClosureVariant(
    const std::string& value);
std::string inventoryRouteClosureVariantName(
    InventoryRouteClosureVariant variant);

FixedIntervalMipRequest::AdditionalLinearRow inventoryRouteBackendRow(
    const InventoryRouteCut& cut,
    int ordinal);

// Run exact external root closure. Every LP is a fresh read of the immutable
// canonical model plus the complete accepted cut pool. No MIP callback,
// PreCrush setting, branching override, elapsed-time stopping rule, or
// instance dispatch is used.
InventoryRouteRootClosureResult runInventoryRouteRootClosure(
    FixedIntervalMipBackend& backend,
    const Instance& instance,
    const FixedIntervalMipRequest& base_request,
    InventoryRouteClosureVariant variant,
    double certificate_tolerance = 1e-7);

} // namespace ebrp
