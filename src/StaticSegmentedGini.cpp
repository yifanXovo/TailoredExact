#include "StaticSegmentedGini.hpp"

#include <algorithm>
#include <cmath>

namespace ebrp {
namespace {

bool within(double lhs, double rhs, double tolerance) {
    return std::fabs(lhs - rhs) <= tolerance;
}

} // namespace

Round41StaticK2Geometry makeRound41StaticK2Geometry(
    double proof_lower,
    double proof_upper,
    double tolerance) {
    Round41StaticK2Geometry result;
    result.proof_lower = proof_lower;
    result.proof_upper = proof_upper;
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(proof_lower) || !std::isfinite(proof_upper) ||
        proof_lower < -tol || proof_upper < proof_lower - tol) {
        result.reason = "invalid_round41_static_k2_range";
        return result;
    }
    result.midpoint = proof_lower + 0.5 * (proof_upper - proof_lower);
    result.segments = {
        {proof_lower, result.midpoint},
        {result.midpoint, proof_upper},
    };
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            {proof_lower, proof_upper}, result.segments, tol,
            &coverage_reason)) {
        result.reason = "round41_static_k2_coverage_failed:" + coverage_reason;
        return result;
    }
    result.valid = true;
    result.reason = "two_equal_midpoint_segments_exactly_cover_proof_range";
    return result;
}

bool round41PerspectiveProductBlockValid(
    double segment_lower,
    double segment_upper,
    double selector,
    double bit,
    double global_g,
    double segment_g,
    double activation,
    double product,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    auto reject = [&](const std::string& why) {
        if (reason) *reason = why;
        return false;
    };
    if (!std::isfinite(segment_lower) || !std::isfinite(segment_upper) ||
        segment_upper < segment_lower - tol ||
        !std::isfinite(selector) || !std::isfinite(bit) ||
        !std::isfinite(global_g) || !std::isfinite(segment_g) ||
        !std::isfinite(activation) || !std::isfinite(product)) {
        return reject("nonfinite_or_reversed_perspective_input");
    }
    if (selector < -tol || selector > 1.0 + tol ||
        bit < -tol || bit > 1.0 + tol) {
        return reject("binary_relaxation_domain_violation");
    }
    if (segment_g < segment_lower * selector - tol ||
        segment_g > segment_upper * selector + tol) {
        return reject("selected_g_bound_violation");
    }
    if (activation < -tol || activation > selector + tol ||
        activation > bit + tol ||
        activation < selector + bit - 1.0 - tol) {
        return reject("selector_bit_linearization_violation");
    }
    if (product < segment_lower * activation - tol ||
        product > segment_upper * activation + tol ||
        product < segment_g - segment_upper * (selector - activation) - tol ||
        product > segment_g - segment_lower * (selector - activation) + tol) {
        return reject("perspective_product_envelope_violation");
    }
    const bool integral_selector = within(selector, 0.0, tol) ||
        within(selector, 1.0, tol);
    const bool integral_bit = within(bit, 0.0, tol) ||
        within(bit, 1.0, tol);
    if (integral_selector && integral_bit) {
        const double expected_activation = selector * bit;
        const double expected_product = segment_g * bit;
        if (!within(activation, expected_activation, tol)) {
            return reject("integral_activation_not_selector_times_bit");
        }
        if (!within(product, expected_product, tol)) {
            return reject("integral_product_not_selected_g_times_bit");
        }
        if (within(selector, 1.0, tol) &&
            !within(segment_g, global_g, tol)) {
            return reject("selected_segment_g_not_global_g");
        }
    }
    if (reason) *reason = "valid_round41_perspective_product_block";
    return true;
}

bool round41SelectedContinuousBlockValid(
    double global_lower,
    double global_upper,
    double selected_lower,
    double selected_upper,
    double selector,
    double original,
    double selected,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    auto reject = [&](const std::string& why) {
        if (reason) *reason = why;
        return false;
    };
    if (!std::isfinite(global_lower) || !std::isfinite(global_upper) ||
        !std::isfinite(selected_lower) || !std::isfinite(selected_upper) ||
        !std::isfinite(selector) || !std::isfinite(original) ||
        !std::isfinite(selected) || global_upper < global_lower - tol ||
        selected_upper < selected_lower - tol ||
        selected_lower < global_lower - tol ||
        selected_upper > global_upper + tol) {
        return reject("invalid_selected_continuous_inputs");
    }
    if (selector < -tol || selector > 1.0 + tol ||
        original < global_lower - tol || original > global_upper + tol ||
        selected < selected_lower * selector - tol ||
        selected > selected_upper * selector + tol ||
        selected < original - global_upper * (1.0 - selector) - tol ||
        selected > original - global_lower * (1.0 - selector) + tol) {
        return reject("selected_continuous_envelope_violation");
    }
    if (within(selector, 0.0, tol) && !within(selected, 0.0, tol)) {
        return reject("inactive_selected_value_nonzero");
    }
    if (within(selector, 1.0, tol) && !within(selected, original, tol)) {
        return reject("active_selected_value_not_original");
    }
    if (reason) *reason = "valid_round41_selected_continuous_block";
    return true;
}

} // namespace ebrp
