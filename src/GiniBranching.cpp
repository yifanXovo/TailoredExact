#include "GiniBranching.hpp"

#include <algorithm>
#include <cmath>

namespace ebrp {

GiniBranchingSummary planGiniBranching(const SolveOptions& options,
                                       double gamma_L,
                                       double gamma_U) {
    GiniBranchingSummary out;
    std::string requested = options.tailored_bc_gini_branching;
    if (requested.empty()) requested = "off";
    out.mode = requested;
    const double width = gamma_U - gamma_L;
    if (!options.tailored_bc_enabled || requested == "off") {
        out.mode = "off";
        out.reason = "disabled";
        return out;
    }
    if (width < options.tailored_bc_gini_branch_min_width) {
        out.mode = "off";
        out.reason = "interval_below_min_width";
        return out;
    }
    if (requested == "auto") {
        out.mode = "branch_callback";
        out.priorities_assigned = 1;
        out.reason = "auto_prefers_callback_branching_when_callbacks_available";
        return out;
    }
    if (requested == "selector") {
        out.mode = "selector_binary";
        out.selector_variables = 1;
        out.priorities_assigned = 1;
        out.reason = "selector_binary_requested";
        return out;
    }
    if (requested == "outer-controller") {
        out.mode = "outer_controller";
        out.reason = "outer_controller_requested";
        return out;
    }
    if (requested == "callback") {
        out.mode = "branch_callback";
        out.reason = "callback_requested";
        return out;
    }
    out.mode = "off";
    out.reason = "unknown_mode";
    return out;
}

} // namespace ebrp
