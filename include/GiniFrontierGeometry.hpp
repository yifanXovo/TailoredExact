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

} // namespace ebrp
