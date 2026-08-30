#pragma once

#include <string>
#include <vector>

namespace ebrp {

enum class InventoryRouteCutKind {
    MixedInbound,
    MixedOutbound,
    ProjectedInbound,
    ProjectedOutbound,
};

struct InventoryRouteArcValue {
    int vehicle = 0;
    int from = 0;
    int to = 0;
    double value = 0.0;
};

struct InventoryRouteLpState {
    int station_count = 0;
    std::vector<int> vehicle_capacities;
    // All inventory vectors use the original model indexing: element zero is
    // the depot and stations are 1..station_count.
    std::vector<double> initial_inventory;
    std::vector<double> final_inventory;
    std::vector<double> final_inventory_lower;
    std::vector<double> final_inventory_upper;
    std::vector<InventoryRouteArcValue> route_arcs;
};

struct InventoryRouteRowCoefficient {
    std::string variable_name;
    double coefficient = 0.0;
};

struct InventoryRouteCut {
    InventoryRouteCutKind kind = InventoryRouteCutKind::MixedInbound;
    bool valid = false;
    bool violated = false;
    std::vector<int> subset;
    double raw_violation = 0.0;
    double scaled_violation = 0.0;
    double mincut_objective = 0.0;
    double direct_recomputed_objective = 0.0;
    std::vector<InventoryRouteRowCoefficient> row_coefficients;
    char sense = '<';
    double rhs = 0.0;
    std::string canonical_signature;
    std::string scope = "global";
    std::string failure_reason = "not_separated";
};

struct InventoryRouteSeparationResult {
    bool valid = false;
    InventoryRouteCut mixed_inbound;
    InventoryRouteCut mixed_outbound;
    InventoryRouteCut projected_inbound;
    InventoryRouteCut projected_outbound;
    std::string failure_reason = "not_separated";
};

std::string inventoryRouteCutKindName(InventoryRouteCutKind kind);

// Exact deterministic maximum-closure/min-cut separation. The tolerance is a
// frozen certificate-scale tolerance, never a fitted performance parameter.
InventoryRouteCut separateInventoryRouteCut(
    const InventoryRouteLpState& state,
    InventoryRouteCutKind kind,
    double certificate_tolerance = 1e-7);

InventoryRouteSeparationResult separateInventoryRouteCuts(
    const InventoryRouteLpState& state,
    double certificate_tolerance = 1e-7);

// Independently recompute the violation from the original Y and x values.
double recomputeInventoryRouteViolation(
    const InventoryRouteLpState& state,
    InventoryRouteCutKind kind,
    const std::vector<int>& subset);

} // namespace ebrp
