#include "GiniAdaptiveParametric.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <set>

namespace ebrp {
namespace {

bool finite(double value) { return std::isfinite(value); }

double scaledTolerance(double tolerance, double a, double b = 0.0) {
    return std::max(0.0, tolerance) *
        std::max({1.0, std::fabs(a), std::fabs(b)});
}

bool validInterval(const GiniIntervalGeometry& interval) {
    return finite(interval.lower) && finite(interval.upper) &&
        interval.upper > interval.lower;
}

double valueAt(const std::vector<ParametricAffineSegment>& segments,
               double point, double tolerance) {
    for (std::size_t index = 0; index < segments.size(); ++index) {
        const auto& segment = segments[index];
        const bool last = index + 1 == segments.size();
        if (point >= segment.lower - tolerance &&
            (point < segment.upper + tolerance || last))
            return evaluateParametricSegment(segment, point);
    }
    return std::numeric_limits<double>::quiet_NaN();
}

const ParametricAffineSegment* segmentAt(
        const std::vector<ParametricAffineSegment>& segments,
        double point, double tolerance) {
    for (std::size_t index = 0; index < segments.size(); ++index) {
        const auto& segment = segments[index];
        const bool last = index + 1 == segments.size();
        if (point >= segment.lower - tolerance &&
            (point < segment.upper + tolerance || last)) return &segment;
    }
    return nullptr;
}

double minValue(const ParametricPointInput& input, double point) {
    const double left = valueAt(
        input.left, point, input.certificate_tolerance);
    const double right = valueAt(
        input.right, point, input.certificate_tolerance);
    return input.frontier_capped
        ? std::min({left, right, input.frontier_target})
        : std::min(left, right);
}

bool restrictAffineAtLeast(double intercept, double slope, double threshold,
                           double tolerance, double& lower, double& upper) {
    const double slope_tolerance = scaledTolerance(
        tolerance, intercept, threshold);
    if (std::fabs(slope) <= slope_tolerance)
        return intercept + slope * 0.5 * (lower + upper) >=
            threshold - slope_tolerance;
    const double crossing = (threshold - intercept) / slope;
    if (slope > 0.0) lower = std::max(lower, crossing);
    else upper = std::min(upper, crossing);
    return lower <= upper + tolerance;
}

} // namespace

GammaSumResult evaluateGammaSum(const GammaSumInput& input) {
    GammaSumResult result;
    const double eps = std::max(0.0, input.certificate_tolerance);
    if (!validInterval(input.parent) || !validInterval(input.left) ||
        !validInterval(input.right) ||
        !exactIntervalCoverage(input.parent, {input.left, input.right}, eps) ||
        !finite(input.envelope_lower_bound) ||
        (!finite(input.left_lower_bound) &&
         input.left_lower_bound != std::numeric_limits<double>::infinity()) ||
        (!finite(input.right_lower_bound) &&
         input.right_lower_bound != std::numeric_limits<double>::infinity()) ||
        !finite(input.frontier_target) ||
        !finite(input.root_normalization) ||
        input.root_normalization <= 0.0) {
        result.reason = "invalid_gamma_sum_input";
        return result;
    }
    const double parent_width = input.parent.upper - input.parent.lower;
    const double left_width = input.left.upper - input.left.lower;
    const double right_width = input.right.upper - input.right.lower;
    result.parent_mass = parent_width * std::max(
        0.0, input.frontier_target - input.envelope_lower_bound);
    result.split_mass =
        left_width * std::max(
            0.0, input.frontier_target - input.left_lower_bound) +
        right_width * std::max(
            0.0, input.frontier_target - input.right_lower_bound);
    result.gamma_sum =
        (result.parent_mass - result.split_mass) /
        input.root_normalization;
    result.epsilon_gamma = eps / std::max(input.root_normalization, eps);
    result.valid = finite(result.gamma_sum) && finite(result.epsilon_gamma);
    result.reason = result.valid ? "valid_frontier_residual_mass_reduction"
                                 : "nonfinite_gamma_sum";
    return result;
}

AdaptiveTimingDecision evaluateAdaptiveTimingDecision(
        const AdaptiveTimingInput& input) {
    AdaptiveTimingDecision result;
    const double eps = std::max(0.0, input.certificate_tolerance);
    const bool scalars_valid =
        finite(input.D_R43) && finite(input.F) &&
        finite(input.M_root) && finite(input.H) &&
        finite(input.Gamma_sum) && finite(input.epsilon_gamma) &&
        finite(input.rho_D) && finite(input.rho_F) &&
        finite(input.rho_M) && finite(input.rho_H) &&
        finite(input.rho_gamma) && input.epsilon_gamma >= 0.0 &&
        input.rho_D >= 0.0 && input.rho_D <= 1.0 &&
        input.rho_F >= 0.0 && input.rho_F <= 1.0 &&
        input.rho_M >= 0.0 && input.rho_M <= 1.0 &&
        input.rho_H >= 0.0 && input.rho_H <= 1.0 &&
        input.rho_gamma >= 0.0;
    if (!scalars_valid) {
        result.reason = "invalid_adaptive_timing_input";
        return result;
    }
    result.genuinely_adaptive_family = input.family != "no-adaptive";
    if (input.family == "old-c6") {
        result.split = input.old_c6_split;
        result.reason = "exact_old_c6_decision";
    } else if (input.family == "d-r43") {
        result.split = input.D_R43 >= input.rho_D - eps;
        result.reason = "corrected_d_r43_threshold";
    } else if (input.family == "veto-f") {
        result.split = input.old_c6_split && input.F >= input.rho_F - eps;
        result.reason = "old_c6_and_frontier_veto";
    } else if (input.family == "f") {
        result.split = input.F >= input.rho_F - eps;
        result.reason = "frontier_score_threshold";
    } else if (input.family == "f-mroot") {
        result.split = input.F >= input.rho_F - eps &&
            input.M_root >= input.rho_M - eps;
        result.reason = "frontier_and_root_mass_thresholds";
    } else if (input.family == "h") {
        result.split = input.H >= input.rho_H - eps;
        result.reason = "combined_h_threshold";
    } else if (input.family == "mroot") {
        result.split = input.M_root >= input.rho_M - eps;
        result.reason = "root_mass_threshold";
    } else if (input.family == "gamma-positive") {
        result.split = input.Gamma_sum > input.epsilon_gamma;
        result.reason = "gamma_sum_strictly_positive";
    } else if (input.family == "gamma-threshold") {
        result.split = input.Gamma_sum >= input.rho_gamma - eps;
        result.reason = "gamma_sum_frozen_threshold";
    } else if (input.family == "gamma-veto") {
        result.split = input.old_c6_split &&
            input.Gamma_sum >= input.rho_gamma - eps;
        result.reason = "old_c6_and_gamma_veto";
    } else if (input.family == "decisive-gamma") {
        result.split = input.decisive_frontier &&
            input.Gamma_sum > input.epsilon_gamma;
        result.reason = "decisive_frontier_and_positive_gamma";
    } else if (input.family == "no-adaptive") {
        result.split = false;
        result.genuinely_adaptive_family = false;
        result.reason = "ineligible_no_adaptive_reference";
    } else {
        result.reason = "unknown_adaptive_timing_family";
        return result;
    }
    result.valid = true;
    result.action = result.split ? "split" : "retain";
    return result;
}

GiniIntervalGeometry parametricBasisSensitivityInterval(
        const ParametricBasisSensitivity& sensitivity) {
    if (!finite(sensitivity.rhs) ||
        !finite(sensitivity.allowable_decrease) ||
        !finite(sensitivity.allowable_increase) ||
        sensitivity.allowable_decrease < 0.0 ||
        sensitivity.allowable_increase < 0.0) return {};
    return {sensitivity.rhs - sensitivity.allowable_decrease,
            sensitivity.rhs + sensitivity.allowable_increase};
}

double canonicalRightParametricCoefficient(double g_coefficient) {
    return -g_coefficient;
}

double canonicalRightParametricRhs(double split_point) {
    return -split_point;
}

double affineParametricValue(double base_value, double dual_slope,
                             double rhs, double base_rhs) {
    return base_value + dual_slope * (rhs - base_rhs);
}

double evaluateParametricSegment(
        const ParametricAffineSegment& segment, double point) {
    return segment.intercept + segment.slope * point;
}

ParametricValueFunctionAudit auditParametricValueFunction(
        const std::vector<ParametricAffineSegment>& segments,
        const GiniIntervalGeometry& domain,
        bool nonincreasing,
        double tolerance) {
    ParametricValueFunctionAudit audit;
    if (!validInterval(domain) || segments.empty() || tolerance < 0.0) {
        audit.reason = "invalid_value_function_input";
        return audit;
    }
    audit.finite = true;
    double expected = domain.lower;
    double previous_upper_value = 0.0;
    bool have_previous = false;
    for (const auto& segment : segments) {
        if (!finite(segment.lower) || !finite(segment.upper) ||
            !finite(segment.intercept) || !finite(segment.slope) ||
            segment.upper <= segment.lower ||
            std::fabs(segment.lower - expected) >
                scaledTolerance(tolerance, segment.lower, expected)) {
            audit.finite = false;
            audit.reason = "nonfinite_or_noncovering_segment";
            return audit;
        }
        const double low = evaluateParametricSegment(segment, segment.lower);
        const double high = evaluateParametricSegment(segment, segment.upper);
        if (!finite(low) || !finite(high)) {
            audit.finite = false;
            audit.reason = "nonfinite_segment_value";
            return audit;
        }
        const double directional = nonincreasing
            ? high - low : low - high;
        audit.maximum_monotonicity_residual = std::max(
            audit.maximum_monotonicity_residual, directional);
        if (have_previous) {
            const double jump = std::fabs(low - previous_upper_value);
            audit.maximum_endpoint_jump = std::max(
                audit.maximum_endpoint_jump, jump);
        }
        previous_upper_value = high;
        have_previous = true;
        expected = segment.upper;
    }
    audit.exact_coverage = std::fabs(expected - domain.upper) <=
        scaledTolerance(tolerance, expected, domain.upper);
    audit.monotone = audit.maximum_monotonicity_residual <=
        scaledTolerance(tolerance, previous_upper_value) &&
        audit.maximum_endpoint_jump <=
        scaledTolerance(tolerance, previous_upper_value);
    audit.valid = audit.finite && audit.exact_coverage && audit.monotone;
    audit.reason = audit.valid ? "certified_piecewise_affine_value_function"
        : (!audit.exact_coverage ? "value_function_coverage_failure"
                                : "value_function_monotonicity_failure");
    return audit;
}

std::vector<ParametricAffineSegment> mergeParametricSegments(
        const std::vector<ParametricAffineSegment>& segments,
        double tolerance) {
    std::vector<ParametricAffineSegment> merged;
    for (const auto& segment : segments) {
        if (!validInterval({segment.lower, segment.upper}) ||
            !finite(segment.intercept) || !finite(segment.slope)) continue;
        if (!merged.empty()) {
            auto& previous = merged.back();
            const bool adjacent = std::fabs(previous.upper - segment.lower) <=
                scaledTolerance(tolerance, previous.upper, segment.lower);
            const bool same_affine =
                std::fabs(previous.slope - segment.slope) <=
                    scaledTolerance(tolerance, previous.slope, segment.slope) &&
                std::fabs(previous.intercept - segment.intercept) <=
                    scaledTolerance(tolerance, previous.intercept,
                                    segment.intercept);
            if (adjacent && same_affine) {
                previous.upper = segment.upper;
                previous.degenerate = previous.degenerate || segment.degenerate;
                if (previous.basis_hash != segment.basis_hash)
                    previous.basis_hash = "merged-equivalent-bases";
                continue;
            }
        }
        merged.push_back(segment);
    }
    return merged;
}

ParametricPointResult selectParametricMaxMinPoint(
        const ParametricPointInput& input) {
    ParametricPointResult result;
    result.midpoint = 0.5 * (input.admissible.lower + input.admissible.upper);
    const auto left_audit = auditParametricValueFunction(
        input.left, input.admissible, true, input.certificate_tolerance);
    const auto right_audit = auditParametricValueFunction(
        input.right, input.admissible, false, input.certificate_tolerance);
    if (!left_audit.valid || !right_audit.valid ||
        (input.frontier_capped && !finite(input.frontier_target))) {
        result.reason = "certified_parametric_point_unavailable_retain_parent";
        return result;
    }
    std::set<double> boundary_set = {
        input.admissible.lower, input.admissible.upper};
    for (const auto& segment : input.left) {
        boundary_set.insert(segment.lower); boundary_set.insert(segment.upper);
    }
    for (const auto& segment : input.right) {
        boundary_set.insert(segment.lower); boundary_set.insert(segment.upper);
    }
    std::vector<double> boundaries(boundary_set.begin(), boundary_set.end());
    std::vector<double> candidates = boundaries;
    for (std::size_t index = 0; index + 1 < boundaries.size(); ++index) {
        const double lower = boundaries[index];
        const double upper = boundaries[index + 1];
        if (upper <= lower) continue;
        const double probe = 0.5 * (lower + upper);
        const auto* left = segmentAt(
            input.left, probe, input.certificate_tolerance);
        const auto* right = segmentAt(
            input.right, probe, input.certificate_tolerance);
        if (!left || !right) continue;
        const double slope = left->slope - right->slope;
        if (std::fabs(slope) > 1e-15) {
            const double crossing =
                (right->intercept - left->intercept) / slope;
            if (crossing > lower && crossing < upper)
                candidates.push_back(crossing);
        }
    }
    result.max_min_value = -std::numeric_limits<double>::infinity();
    for (double candidate : candidates) {
        const double value = minValue(input, candidate);
        if (!finite(value)) {
            result.reason = "nonfinite_parametric_max_min_value";
            return result;
        }
        result.max_min_value = std::max(result.max_min_value, value);
    }
    const double exact_tolerance = std::max(
        1e-12, 16.0 * std::numeric_limits<double>::epsilon() *
        std::max(1.0, std::fabs(result.max_min_value)));
    bool found = false;
    double maximizer_lower = std::numeric_limits<double>::infinity();
    double maximizer_upper = -std::numeric_limits<double>::infinity();
    for (std::size_t index = 0; index + 1 < boundaries.size(); ++index) {
        double lower = boundaries[index];
        double upper = boundaries[index + 1];
        if (upper <= lower) continue;
        const double probe = 0.5 * (lower + upper);
        const auto* left = segmentAt(input.left, probe, input.certificate_tolerance);
        const auto* right = segmentAt(input.right, probe, input.certificate_tolerance);
        if (!left || !right) continue;
        if (!restrictAffineAtLeast(left->intercept, left->slope,
                                   result.max_min_value, exact_tolerance,
                                   lower, upper) ||
            !restrictAffineAtLeast(right->intercept, right->slope,
                                   result.max_min_value, exact_tolerance,
                                   lower, upper)) continue;
        if (input.frontier_capped &&
            input.frontier_target < result.max_min_value - exact_tolerance)
            continue;
        lower = std::max(lower, boundaries[index]);
        upper = std::min(upper, boundaries[index + 1]);
        if (lower <= upper + exact_tolerance) {
            found = true;
            maximizer_lower = std::min(maximizer_lower, lower);
            maximizer_upper = std::max(maximizer_upper, upper);
        }
    }
    if (!found) {
        for (double candidate : candidates) {
            if (std::fabs(minValue(input, candidate) - result.max_min_value) <=
                exact_tolerance) {
                found = true;
                maximizer_lower = std::min(maximizer_lower, candidate);
                maximizer_upper = std::max(maximizer_upper, candidate);
            }
        }
    }
    if (!found || !finite(maximizer_lower) || !finite(maximizer_upper)) {
        result.reason = "parametric_maximizer_not_certified";
        return result;
    }
    result.maximizer_lower = std::max(
        input.admissible.lower, maximizer_lower);
    result.maximizer_upper = std::min(
        input.admissible.upper, maximizer_upper);
    result.selected_point = 0.5 *
        (result.maximizer_lower + result.maximizer_upper);
    result.plateau = result.maximizer_upper - result.maximizer_lower >
        exact_tolerance;
    result.boundary =
        std::fabs(result.selected_point - input.admissible.lower) <=
            exact_tolerance ||
        std::fabs(result.selected_point - input.admissible.upper) <=
            exact_tolerance;
    result.certified = result.selected_point >= input.admissible.lower &&
        result.selected_point <= input.admissible.upper;
    result.reason = result.certified
        ? (input.frontier_capped ? "certified_fpmm_plateau_midpoint"
                                 : "certified_pmm_plateau_midpoint")
        : "selected_parametric_point_outside_admissible_range";
    return result;
}

ParametricRootAudit auditParametricRootSamples(
        std::vector<ParametricRootSample> samples,
        double tolerance) {
    ParametricRootAudit audit;
    if (samples.empty() || tolerance < 0.0) {
        audit.reason = "empty_or_invalid_root_sample_set";
        return audit;
    }
    std::sort(samples.begin(), samples.end(),
              [](const auto& a, const auto& b) { return a.point < b.point; });
    audit.both_child_coverage = true;
    for (const auto& sample : samples) {
        if (!finite(sample.point) || !sample.left_optimal ||
            !sample.right_optimal ||
            (!sample.left_infeasible && !finite(sample.left_value)) ||
            (!sample.right_infeasible && !finite(sample.right_value))) {
            audit.both_child_coverage = false;
            audit.reason = "incomplete_parametric_child_lp";
            return audit;
        }
    }
    for (std::size_t index = 1; index < samples.size(); ++index) {
        const double previous_left = samples[index - 1].left_infeasible
            ? std::numeric_limits<double>::infinity()
            : samples[index - 1].left_value;
        const double current_left = samples[index].left_infeasible
            ? std::numeric_limits<double>::infinity()
            : samples[index].left_value;
        const double previous_right = samples[index - 1].right_infeasible
            ? std::numeric_limits<double>::infinity()
            : samples[index - 1].right_value;
        const double current_right = samples[index].right_infeasible
            ? std::numeric_limits<double>::infinity()
            : samples[index].right_value;
        if (finite(previous_left) && finite(current_left))
            audit.left_monotonicity_residual = std::max(
                audit.left_monotonicity_residual,
                current_left - previous_left);
        if (finite(previous_right) && finite(current_right))
            audit.right_monotonicity_residual = std::max(
                audit.right_monotonicity_residual,
                previous_right - current_right);
    }
    audit.valid = audit.both_child_coverage &&
        audit.left_monotonicity_residual <= tolerance &&
        audit.right_monotonicity_residual <= tolerance;
    audit.reason = audit.valid ? "certified_monotone_root_samples"
        : "parametric_root_monotonicity_failure";
    return audit;
}

} // namespace ebrp
