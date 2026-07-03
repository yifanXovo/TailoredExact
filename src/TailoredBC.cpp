#include "TailoredBC.hpp"

#include "TailoredBCCallbacks.hpp"
#include "GiniBranching.hpp"

#include <algorithm>

namespace ebrp {

TailoredBCCapability inspectTailoredBCCapability() {
    return inspectTailoredBCCallbacks();
}

void populateTailoredBCResultFields(const SolveOptions& options,
                                    SolveResult& result) {
    const bool requested =
        options.tailored_bc_enabled ||
        options.algorithm_preset == "paper-gf-tailored-bc";
    result.tailored_bc_enabled = requested;
    if (!requested) {
        result.tailored_bc_mode = "off";
        result.tailored_bc_source_class =
            result.method == "cplex" ? "benchmark_only" : "off";
        return;
    }

    TailoredBCCapability cap = inspectTailoredBCCapability();
    result.tailored_bc_callback_available = cap.callbacks_available;
    result.tailored_bc_callback_fail_reason =
        cap.callbacks_available ? "none" : cap.fail_reason;

    if (cap.callbacks_available && options.tailored_bc_mode != "static") {
        result.tailored_bc_mode = "callback";
        result.tailored_bc_user_cut_callback_enabled = true;
        result.tailored_bc_lazy_callback_enabled = true;
        result.tailored_bc_incumbent_callback_enabled = true;
        result.tailored_bc_branch_callback_enabled =
            options.tailored_bc_gini_branching == "callback" ||
            options.tailored_bc_gini_branching == "auto";
        result.tailored_bc_node_separation_enabled = true;
        result.tailored_bc_root_separation_enabled = true;
    } else {
        result.tailored_bc_mode =
            options.tailored_bc_mode == "outer_gini_controller"
                ? "outer_gini_controller"
                : "static_fallback";
        result.tailored_bc_user_cut_callback_enabled = false;
        result.tailored_bc_lazy_callback_enabled = false;
        result.tailored_bc_incumbent_callback_enabled = false;
        result.tailored_bc_branch_callback_enabled = false;
        result.tailored_bc_node_separation_enabled = false;
        result.tailored_bc_root_separation_enabled =
            options.compact_bc_root_cut_rounds > 0;
    }

    GiniBranchingSummary branch = planGiniBranching(
        options,
        result.interval_exact_cutoff_gamma_L,
        result.interval_exact_cutoff_gamma_U);
    result.tailored_bc_gini_branch_mode = branch.mode;
    result.tailored_bc_gini_selector_variables = branch.selector_variables;
    result.tailored_bc_branch_priority_enabled =
        options.tailored_bc_branching_priority != "off";
    result.tailored_bc_branching_priorities_summary =
        "mode=" + options.tailored_bc_branching_priority +
        ";gini_branch=" + branch.mode +
        ";priorities=" + std::to_string(branch.priorities_assigned) +
        ";reason=" + branch.reason;
    result.tailored_bc_support_duration_cover_mode =
        options.tailored_bc_support_duration_cover_mode;
    result.tailored_bc_source_class = tailoredBCSourceClass(result);
}

std::string tailoredBCSourceClass(const SolveResult& result) {
    if (result.method == "cplex") return "benchmark_only";
    if (!result.tailored_bc_enabled) {
        return result.status == "optimal" ? "relaxation_only" : "diagnostic";
    }
    if (result.tailored_bc_mode == "callback" &&
        (result.status == "optimal" || result.status == "interval_closed")) {
        return "tailored_bc_certified";
    }
    if (result.tailored_bc_mode == "callback") {
        return "tailored_bc_assisted_noncertified";
    }
    if (result.tailored_bc_mode == "static_fallback" ||
        result.tailored_bc_mode == "outer_gini_controller") {
        return "static_fallback";
    }
    return "diagnostic";
}

} // namespace ebrp
