#include "Round50IntervalMip.hpp"

#include <algorithm>
#include <cctype>

namespace ebrp {
namespace {

std::string lowerAscii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return value;
}

bool starts(const std::string& value, const char* prefix) {
    return value.rfind(prefix, 0) == 0;
}

} // namespace

Round50IntervalMipPolicy parseRound50IntervalMipPolicy(
    const std::string& requested) {
    Round50IntervalMipPolicy out;
    out.name = lowerAscii(requested);
    if (out.name == "v0" || out.name == "interval-mip-v0") {
        out.name = "interval-mip-v0";
        out.branching = Round50BranchingPolicy::Default;
    } else if (out.name == "b1" || out.name == "b1-primitive-first") {
        out.name = "b1-primitive-first";
        out.branching = Round50BranchingPolicy::PrimitiveFirst;
    } else if (out.name == "b2" || out.name == "b2-route-first") {
        out.name = "b2-route-first";
        out.branching = Round50BranchingPolicy::RouteFirst;
    } else if (out.name == "b3" || out.name == "b3-operation-first") {
        out.name = "b3-operation-first";
        out.branching = Round50BranchingPolicy::OperationFirst;
    } else if (out.name == "c1" || out.name == "c1-exact-dedup" ||
               out.name == "c1-exact-duplicate-elimination") {
        out.name = "c1-exact-duplicate-elimination";
        out.branching = Round50BranchingPolicy::Default;
        out.cut_formulation = "exact-duplicate-elimination";
    } else if (out.name == "s1" || out.name == "s1-route-start-order") {
        out.name = "s1-route-start-order";
        out.branching = Round50BranchingPolicy::Default;
        out.symmetry_numerical = "route-start-order";
    } else if (out.name == "s1r" ||
               out.name == "s1r-used-first-route-start-order") {
        out.name = "s1r-used-first-route-start-order";
        out.branching = Round50BranchingPolicy::Default;
        out.symmetry_numerical = "used-first-route-start-order";
    } else {
        out.failure_reason = "unsupported_round50_interval_mip_policy";
        return out;
    }
    out.valid = true;
    out.failure_reason = "none";
    return out;
}

Round50VariableFamily classifyRound50Variable(const std::string& name) {
    if (starts(name, "x_")) return Round50VariableFamily::RoutingArc;
    if (starts(name, "z_")) return Round50VariableFamily::VisitSelection;
    if (starts(name, "mode_") || starts(name, "op_mode_")) {
        return Round50VariableFamily::OperationMode;
    }
    if (starts(name, "p_")) return Round50VariableFamily::PickupQuantity;
    if (starts(name, "d_")) return Round50VariableFamily::DropQuantity;
    if (starts(name, "load_")) return Round50VariableFamily::VehicleLoad;
    // The canonical writer uses uppercase Y_ for original final inventory.
    // Accept lowercase as well for compatibility with older semantic fixtures.
    if (starts(name, "Y_") || starts(name, "y_")) {
        return Round50VariableFamily::FinalInventory;
    }
    return Round50VariableFamily::Auxiliary;
}

std::string round50VariableFamilyName(Round50VariableFamily family) {
    switch (family) {
    case Round50VariableFamily::RoutingArc: return "routing_arc";
    case Round50VariableFamily::VisitSelection: return "visit_selection";
    case Round50VariableFamily::OperationMode: return "operation_mode";
    case Round50VariableFamily::PickupQuantity: return "pickup_quantity";
    case Round50VariableFamily::DropQuantity: return "drop_quantity";
    case Round50VariableFamily::VehicleLoad: return "vehicle_load";
    case Round50VariableFamily::FinalInventory: return "final_inventory";
    case Round50VariableFamily::Auxiliary: return "auxiliary";
    }
    return "auxiliary";
}

bool round50PrimitiveFamily(Round50VariableFamily family) {
    return family != Round50VariableFamily::Auxiliary;
}

int round50BranchPriority(Round50BranchingPolicy policy,
                          Round50VariableFamily family) {
    if (policy == Round50BranchingPolicy::Default) return 0;
    if (policy == Round50BranchingPolicy::PrimitiveFirst) {
        return round50PrimitiveFamily(family) ? 2 : 1;
    }
    if (policy == Round50BranchingPolicy::RouteFirst) {
        switch (family) {
        case Round50VariableFamily::RoutingArc: return 5;
        case Round50VariableFamily::VisitSelection:
        case Round50VariableFamily::OperationMode: return 4;
        case Round50VariableFamily::PickupQuantity:
        case Round50VariableFamily::DropQuantity: return 3;
        case Round50VariableFamily::VehicleLoad:
        case Round50VariableFamily::FinalInventory: return 2;
        case Round50VariableFamily::Auxiliary: return 1;
        }
    }
    if (policy == Round50BranchingPolicy::OperationFirst) {
        switch (family) {
        case Round50VariableFamily::VisitSelection:
        case Round50VariableFamily::OperationMode: return 5;
        case Round50VariableFamily::RoutingArc: return 4;
        case Round50VariableFamily::PickupQuantity:
        case Round50VariableFamily::DropQuantity: return 3;
        case Round50VariableFamily::VehicleLoad:
        case Round50VariableFamily::FinalInventory: return 2;
        case Round50VariableFamily::Auxiliary: return 1;
        }
    }
    return -1;
}

bool round50OmitDuplicateModeLink(int transfer_upper_bound,
                                  bool exact_dedup_enabled) {
    return exact_dedup_enabled && transfer_upper_bound == 0;
}

void configureRound50IntervalMipV0(SolveOptions& options) {
    options.lambda = 0.15;
    options.threads = 1;
    options.mip_threads = 1;
    options.cplex_threads = 1;
    options.compact_bc_threads = 1;
    options.gurobi_threads = 1;
    options.gurobi_seed = 0;
    options.gurobi_presolve = -1;
    options.tailored_bc_enabled = true;
    options.tailored_bc_mode = "static";
    options.tailored_bc_callback_cut_profile = "off";
    options.compact_bc_root_cut_rounds = 0;
    options.compact_bc_dynamic_cut_families = "none";
    options.compact_bc_cut_profile = "balanced";
    options.compact_bc_low_gini_strengthening = "safe";
    options.compact_bc_denominator_bound_mode = "tight";
    options.compact_bc_objective_estimator_mode = "adaptive";
    options.compact_bc_domain_propagation_mode = "iterative";
    options.compact_bc_domain_propagation_rounds = 2;
    options.compact_bc_variable_s_centering = true;
    options.compact_bc_sp_product_estimator = "paper-safe";
    options.compact_bc_sp_product_bounds = "tight";
    options.compact_bc_s_range_refinement = "off";
    options.tailored_bc_branching_priority = "off";
    options.tailored_bc_gini_branching = "off";
    options.tailored_bc_gini_subset_envelope = false;
    options.tailored_bc_low_gini_l1_centering = false;
    options.tailored_bc_local_centering = false;
    options.tailored_bc_subset_cross_h_centering = false;
    options.tailored_bc_local_q_centering = false;
    options.tailored_bc_subset_inventory_imbalance = false;
    options.tailored_bc_transfer_cutset = false;
    options.tailored_bc_gs_product_coupling = false;
    options.tailored_bc_disaggregated_sp_estimator = false;
    options.tailored_bc_bucket_ratio_domain_tightening = false;
    options.tailored_bc_bucket_subset_ratio_domain = false;
    options.tailored_bc_bucket_integer_inventory_domain = false;
    options.tailored_bc_bucket_required_movement = false;
    options.tailored_bc_bucket_required_visit = false;
    options.global_gini_tree_root_connectivity_flow = true;
    options.global_gini_tree_root_connectivity_flow_variant =
        "round20-current";
    options.interval_row_factory_round19 = true;
    options.incumbent_archive_auto = false;
}

} // namespace ebrp
