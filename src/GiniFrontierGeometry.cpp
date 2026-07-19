#include "GiniFrontierGeometry.hpp"

#include <algorithm>
#include <cmath>

namespace ebrp {

std::vector<GiniIntervalGeometry> makeLegacyFrontierIntervals(
    double lower,
    double upper,
    int interval_count) {
    const int count = std::max(1, interval_count);
    std::vector<GiniIntervalGeometry> intervals;
    intervals.reserve(static_cast<std::size_t>(count));
    for (int index = 0; index < count; ++index) {
        const double frac0 = static_cast<double>(index) / count;
        const double frac1 = static_cast<double>(index + 1) / count;
        intervals.push_back({
            lower + (upper - lower) * frac0,
            index + 1 == count ? upper : lower + (upper - lower) * frac1
        });
    }
    return intervals;
}

bool legacyAdaptiveSplitEligible(double lower,
                                 double upper,
                                 int depth,
                                 int max_depth,
                                 double min_width) {
    return depth < std::max(0, max_depth) &&
           upper - lower > min_width + 1e-12;
}

std::vector<GiniIntervalGeometry> splitLegacyFrontierInterval(
    double lower,
    double upper,
    int split_factor) {
    return makeLegacyFrontierIntervals(lower, upper, std::max(2, split_factor));
}

bool exactIntervalCoverage(const GiniIntervalGeometry& parent,
                           const std::vector<GiniIntervalGeometry>& children,
                           double tolerance,
                           std::string* reason) {
    if (children.empty()) {
        if (reason) *reason = "no_children";
        return false;
    }
    const double tol = std::max(0.0, tolerance);
    if (std::fabs(children.front().lower - parent.lower) > tol) {
        if (reason) *reason = "first_child_lower_mismatch";
        return false;
    }
    if (std::fabs(children.back().upper - parent.upper) > tol) {
        if (reason) *reason = "last_child_upper_mismatch";
        return false;
    }
    for (std::size_t index = 0; index < children.size(); ++index) {
        if (children[index].upper < children[index].lower - tol) {
            if (reason) *reason = "negative_child_width";
            return false;
        }
        if (index > 0 && std::fabs(children[index - 1].upper -
                                  children[index].lower) > tol) {
            if (reason) *reason = "child_boundary_gap_or_overlap_mismatch";
            return false;
        }
    }
    if (reason) *reason = "exact_coverage";
    return true;
}

bool validNestedIntervalContraction(
    const GiniIntervalGeometry& inherited,
    const GiniIntervalGeometry& observed,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(inherited.lower) || !std::isfinite(inherited.upper) ||
        !std::isfinite(observed.lower) || !std::isfinite(observed.upper)) {
        if (reason) *reason = "nonfinite_interval_endpoint";
        return false;
    }
    if (inherited.upper < inherited.lower - tol ||
        observed.upper < observed.lower - tol) {
        if (reason) *reason = "negative_interval_width";
        return false;
    }
    if (observed.lower < inherited.lower - tol) {
        if (reason) *reason = "observed_lower_expands_inherited_interval";
        return false;
    }
    if (observed.upper > inherited.upper + tol) {
        if (reason) *reason = "observed_upper_expands_inherited_interval";
        return false;
    }
    if (reason) *reason = "valid_nested_interval_contraction";
    return true;
}

} // namespace ebrp
