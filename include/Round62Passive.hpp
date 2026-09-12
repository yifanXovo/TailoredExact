#pragma once
#include "ControllingLeafScheduler.hpp"
#include <limits>

namespace ebrp {
// Immutable at native-call launch. No callback can mutate the control ledger.
struct Round62CoverageSnapshot {
    std::vector<ControllingLeaf> leaves;
    std::string active_leaf, model_identity;
    long long epoch = 0, request_epoch = 0;
    double control_ub = 0, archive_ub = 0, request_cutoff = 0;
    double root_lower = 0, root_upper = 0, tolerance = 1e-7;
    bool root_coverage = false, tree_coverage = false, archive_verified = false;
};
struct Round62PassiveDecision {
    bool valid = false, certified = false;
    double lower_bound = 0, usable_ub = 0;
    std::string reason = "not_evaluated";
};
Round62PassiveDecision evaluateRound62Passive(const Round62CoverageSnapshot&,
    double active_native_bound = std::numeric_limits<double>::quiet_NaN());
bool round62PassiveMode(const std::string&);
} // namespace ebrp
