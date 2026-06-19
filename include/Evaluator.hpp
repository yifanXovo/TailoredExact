#pragma once

#include "Result.hpp"

namespace ebrp {

Verification verifySolution(const Instance& instance,
                            const std::vector<RoutePlan>& routes,
                            double lambda,
                            double objective_tolerance = 1e-7);

} // namespace ebrp
