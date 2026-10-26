#include "StaticSegmentedGini.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>

namespace ebrp {
namespace {

bool within(double lhs, double rhs, double tolerance) {
    return std::fabs(lhs - rhs) <= tolerance;
}

std::string rowLhsSenseIdentity(const CanonicalLinearRow& row) {
    std::ostringstream out;
    out << row.sense << '|'
        << std::setprecision(std::numeric_limits<double>::max_digits10);
    for (const auto& term : row.coefficients) {
        out << term.first << '=' << term.second << ';';
    }
    return out.str();
}

std::string stableBlockIdentity(const StaticSegmentedBlockSpec& spec) {
    std::ostringstream material;
    material << std::setprecision(std::numeric_limits<double>::max_digits10)
             << spec.union_interval.lower << '|'
             << spec.union_interval.upper << '|'
             << spec.verified_incumbent << '|'
             << spec.incumbent_epsilon << '|'
             << spec.formulation_mode << '|'
             << spec.common_row_factoring << '|'
             << spec.hierarchical_selectors;
    for (std::size_t k = 0; k < spec.segments.size(); ++k) {
        material << '|' << spec.segments[k].lower << ':'
                 << spec.segments[k].upper << ':'
                 << spec.segment_rows[k].aggregate_signature << ':'
                 << spec.segment_feasible[k];
    }
    std::uint64_t hash = 1469598103934665603ull;
    for (const unsigned char ch : material.str()) {
        hash ^= ch;
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << "static-segmented-v1-" << std::hex << std::setfill('0')
        << std::setw(16) << hash;
    return out.str();
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

std::vector<GiniIntervalGeometry> makeEqualStaticSegments(
    double proof_lower,
    double proof_upper,
    int segment_count,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(proof_lower) || !std::isfinite(proof_upper) ||
        proof_lower < -tol || proof_upper < proof_lower - tol ||
        segment_count <= 0) {
        if (reason) *reason = "invalid_equal_static_segment_request";
        return {};
    }
    std::vector<GiniIntervalGeometry> segments;
    segments.reserve(static_cast<std::size_t>(segment_count));
    const double width = (proof_upper - proof_lower) / segment_count;
    for (int k = 0; k < segment_count; ++k) {
        const double lower = k == 0
            ? proof_lower : proof_lower + width * k;
        const double upper = k + 1 == segment_count
            ? proof_upper : proof_lower + width * (k + 1);
        segments.push_back({lower, upper});
    }
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            {proof_lower, proof_upper}, segments, tol, &coverage_reason)) {
        if (reason) *reason = "equal_static_segment_coverage_failed:" +
            coverage_reason;
        return {};
    }
    if (reason) *reason = "equal_static_segments_exact_cover";
    return segments;
}

StaticSegmentedBlockSpec makeStaticSegmentedBlockSpec(
    const Instance& instance,
    const SolveOptions& options,
    const GiniIntervalGeometry& union_interval,
    const std::vector<GiniIntervalGeometry>& segments,
    double verified_incumbent,
    double incumbent_epsilon,
    const std::string& formulation_mode,
    bool common_row_factoring,
    bool hierarchical_selectors,
    double tolerance) {
    StaticSegmentedBlockSpec result;
    result.union_interval = union_interval;
    result.segments = segments;
    result.verified_incumbent = verified_incumbent;
    result.incumbent_epsilon = incumbent_epsilon;
    result.formulation_mode = formulation_mode;
    result.common_row_factoring = common_row_factoring;
    result.hierarchical_selectors = hierarchical_selectors;
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(union_interval.lower) ||
        !std::isfinite(union_interval.upper) ||
        union_interval.lower < -tol ||
        union_interval.upper < union_interval.lower - tol ||
        !std::isfinite(verified_incumbent) ||
        !std::isfinite(incumbent_epsilon) || incumbent_epsilon < -tol ||
        segments.empty()) {
        result.reason = "invalid_static_segmented_block_inputs";
        return result;
    }
    if (formulation_mode != "st-k2-i" &&
        formulation_mode != "st-k2-p-core" &&
        formulation_mode != "st-k2-p-extended") {
        result.reason = "unsupported_static_segmented_block_mode";
        return result;
    }
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            union_interval, segments, tol, &coverage_reason)) {
        result.reason = "static_segmented_block_coverage_failed:" +
            coverage_reason;
        return result;
    }
    if (hierarchical_selectors && segments.size() != 4) {
        result.reason = "hierarchical_selectors_require_four_segments";
        return result;
    }
    result.segment_rows.reserve(segments.size());
    result.segment_feasible.reserve(segments.size());
    for (const GiniIntervalGeometry& segment : segments) {
        IntervalRowFactoryRequest request;
        request.gamma_L = segment.lower;
        request.gamma_U = segment.upper;
        request.verified_incumbent = verified_incumbent;
        request.incumbent_epsilon = incumbent_epsilon;
        request.add_incumbent_row = true;
        request.strengthened = true;
        IntervalRowFactoryResult rows = buildRound18StaticIntervalRows(
            instance, options, request);
        if (!rows.complete_round18_static_migration ||
            !rows.unsupported_active_families.empty()) {
            result.reason =
                "static_segmented_block_interval_factory_incomplete";
            return result;
        }
        result.segment_feasible.push_back(!rows.domain.domain_infeasible);
        result.segment_rows.push_back(std::move(rows));
    }
    if (std::none_of(result.segment_feasible.begin(),
                     result.segment_feasible.end(),
                     [](bool feasible) { return feasible; })) {
        result.reason = "all_static_segmented_block_segments_infeasible";
        return result;
    }
    result.valid = true;
    result.reason = "gap_free_static_segmented_block_materialized";
    result.deterministic_model_identity = stableBlockIdentity(result);
    return result;
}

StaticCommonRowFactoringPlan makeStaticCommonRowFactoringPlan(
    const std::vector<IntervalRowFactoryResult>& segment_rows,
    const std::set<std::string>& excluded_families) {
    StaticCommonRowFactoringPlan result;
    if (segment_rows.empty()) {
        result.reason = "empty_static_row_factoring_input";
        return result;
    }
    result.residual_rows.resize(segment_rows.size());
    struct LocatedRow {
        std::size_t segment = 0;
        CanonicalLinearRow row;
    };
    std::map<std::string, std::vector<LocatedRow>> groups;
    for (std::size_t k = 0; k < segment_rows.size(); ++k) {
        for (const CanonicalLinearRow& row : segment_rows[k].rows) {
            if (row.scope != IntervalRowScope::IntervalLocal ||
                excluded_families.count(row.family)) {
                continue;
            }
            ++result.input_rows;
            groups[rowLhsSenseIdentity(row)].push_back({k, row});
        }
    }
    for (const auto& entry : groups) {
        const std::vector<LocatedRow>& rows = entry.second;
        std::vector<int> occurrences(segment_rows.size(), 0);
        for (const LocatedRow& located : rows) {
            ++occurrences[located.segment];
        }
        const bool exactly_one_per_segment =
            rows.size() == segment_rows.size() &&
            std::all_of(occurrences.begin(), occurrences.end(),
                        [](int count) { return count == 1; });
        if (!exactly_one_per_segment) {
            for (const LocatedRow& located : rows) {
                result.residual_rows[located.segment].push_back(located.row);
                ++result.indicator_rows_retained;
            }
            continue;
        }
        std::vector<CanonicalLinearRow> ordered(segment_rows.size());
        for (const LocatedRow& located : rows) {
            ordered[located.segment] = located.row;
        }
        const bool identical_rhs = std::all_of(
            ordered.begin() + 1, ordered.end(),
            [&](const CanonicalLinearRow& row) {
                return row.rhs == ordered.front().rhs;
            });
        if (identical_rhs) {
            result.unconditional_rows.push_back(ordered.front());
            ++result.unconditional_rows_written;
        } else {
            StaticSelectorWeightedRow weighted;
            weighted.prototype = ordered.front();
            for (const CanonicalLinearRow& row : ordered) {
                weighted.rhs_by_segment.push_back(row.rhs);
            }
            result.selector_weighted_rows.push_back(std::move(weighted));
            ++result.selector_weighted_rows_written;
        }
        result.indicator_rows_removed +=
            static_cast<long long>(segment_rows.size());
    }
    result.valid = true;
    result.reason = "exact_full_cover_common_row_factoring_plan";
    return result;
}

bool staticSelectorBlockValid(
    const std::vector<double>& selectors,
    const std::vector<bool>& segment_feasible,
    const std::vector<double>& hierarchical_halves,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    auto reject = [&](const std::string& why) {
        if (reason) *reason = why;
        return false;
    };
    if (selectors.empty() || selectors.size() != segment_feasible.size()) {
        return reject("selector_feasibility_cardinality_mismatch");
    }
    double sum = 0.0;
    for (std::size_t k = 0; k < selectors.size(); ++k) {
        if (!std::isfinite(selectors[k]) || selectors[k] < -tol ||
            selectors[k] > 1.0 + tol) {
            return reject("selector_domain_violation");
        }
        if (!segment_feasible[k] && selectors[k] > tol) {
            return reject("infeasible_segment_selected");
        }
        sum += selectors[k];
    }
    if (!within(sum, 1.0, tol)) {
        return reject("selector_exclusivity_violation");
    }
    if (!hierarchical_halves.empty()) {
        if (selectors.size() != 4 || hierarchical_halves.size() != 2) {
            return reject("hierarchical_selector_cardinality_mismatch");
        }
        if (!within(hierarchical_halves[0] + hierarchical_halves[1],
                    1.0, tol) ||
            !within(hierarchical_halves[0], selectors[0] + selectors[1],
                    tol) ||
            !within(hierarchical_halves[1], selectors[2] + selectors[3],
                    tol)) {
            return reject("hierarchical_selector_link_violation");
        }
    }
    if (reason) *reason = "valid_static_selector_block";
    return true;
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
