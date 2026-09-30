#pragma once
#include "Instance.hpp"
#include "Result.hpp"

namespace ebrp {
// Caller has already checked route/station structure. No overflow in the
// existing int-based Evaluator may be hidden by a physically feasible prefix.
bool physicalOperationsFitEvaluatorIntegerDomain(const Instance&, const std::vector<RoutePlan>&);
// Complete starting witness: exactly one route record for each vehicle,
// including empty routes. Retains the established R95 checks and tolerances.
Verification verifyCompletePhysicalStartingWitness(const Instance&, const std::vector<RoutePlan>&, double lambda);
} // namespace ebrp
