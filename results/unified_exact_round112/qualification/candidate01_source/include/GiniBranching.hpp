#pragma once

#include "Instance.hpp"

#include <string>

namespace ebrp {

struct GiniBranchingSummary {
    std::string mode = "off";
    int selector_variables = 0;
    int priorities_assigned = 0;
    std::string reason;
};

GiniBranchingSummary planGiniBranching(const SolveOptions& options,
                                       double gamma_L,
                                       double gamma_U);

} // namespace ebrp
