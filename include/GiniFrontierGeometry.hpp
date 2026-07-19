#pragma once

#include <string>
#include <vector>

namespace ebrp {

struct GiniIntervalGeometry {
    double lower = 0.0;
    double upper = 0.0;
};

std::vector<GiniIntervalGeometry> makeLegacyFrontierIntervals(
    double lower,
    double upper,
    int interval_count);

bool legacyAdaptiveSplitEligible(double lower,
                                 double upper,
                                 int depth,
                                 int max_depth,
                                 double min_width);

std::vector<GiniIntervalGeometry> splitLegacyFrontierInterval(
    double lower,
    double upper,
    int split_factor);

bool exactIntervalCoverage(const GiniIntervalGeometry& parent,
                           const std::vector<GiniIntervalGeometry>& children,
                           double tolerance,
                           std::string* reason = nullptr);

// CPLEX may tighten a node's local G bounds after valid cuts are installed.
// Such a contraction preserves every row inherited from the wider interval;
// an expansion does not and must therefore fail closed.
bool validNestedIntervalContraction(
    const GiniIntervalGeometry& inherited,
    const GiniIntervalGeometry& observed,
    double tolerance,
    std::string* reason = nullptr);

} // namespace ebrp
