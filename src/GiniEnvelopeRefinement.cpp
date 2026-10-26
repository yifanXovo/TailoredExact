#include "GiniEnvelopeRefinement.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <utility>

namespace ebrp {
namespace {

bool finite(double value) {
    return std::isfinite(value);
}

double scaleTolerance(double tolerance, double first, double second = 0.0) {
    return std::max(0.0, tolerance) *
        std::max({1.0, std::fabs(first), std::fabs(second)});
}

bool sameEndpoint(double first, double second, double tolerance) {
    return std::fabs(first - second) <=
        scaleTolerance(tolerance, first, second);
}

bool validInterval(const GiniIntervalGeometry& interval) {
    return finite(interval.lower) && finite(interval.upper) &&
        interval.upper > interval.lower;
}

bool lookaheadCoverageValid(const GiniEnvelopeInput& input,
                            std::string& reason) {
    if (!validInterval(input.parent) || input.lookahead.empty()) {
        reason = "invalid_or_empty_parent_profile";
        return false;
    }
    if (!sameEndpoint(input.lookahead.front().interval.lower,
                      input.parent.lower, input.certificate_tolerance) ||
        !sameEndpoint(input.lookahead.back().interval.upper,
                      input.parent.upper, input.certificate_tolerance)) {
        reason = "lookahead_does_not_contact_parent_endpoints";
        return false;
    }
    for (std::size_t index = 0; index < input.lookahead.size(); ++index) {
        const GiniLookaheadBound& cell = input.lookahead[index];
        if (!validInterval(cell.interval)) {
            reason = "invalid_lookahead_interval";
            return false;
        }
        if (index && !sameEndpoint(
                input.lookahead[index - 1].interval.upper,
                cell.interval.lower, input.certificate_tolerance)) {
            reason = "lookahead_gap_or_overlap";
            return false;
        }
        if (!cell.terminal_valid || (!cell.infeasible &&
            (!cell.optimal || !cell.bound_available ||
             !finite(cell.lower_bound)))) {
            reason = "lookahead_status_not_complete_valid_lp";
            return false;
        }
    }
    reason = "complete_gap_free_lookahead_profile";
    return true;
}

struct Point {
    double x = 0.0;
    double y = 0.0;
};

bool duplicateFacet(const GiniEnvelopeFacet& first,
                    const GiniEnvelopeFacet& second,
                    const GiniIntervalGeometry& parent,
                    double tolerance) {
    return sameEndpoint(evaluateGiniEnvelopeFacet(first, parent.lower),
                        evaluateGiniEnvelopeFacet(second, parent.lower),
                        tolerance) &&
        sameEndpoint(evaluateGiniEnvelopeFacet(first, parent.upper),
                     evaluateGiniEnvelopeFacet(second, parent.upper),
                     tolerance);
}

std::vector<double> facetArrangementPoints(
        const std::vector<GiniEnvelopeFacet>& facets,
        const GiniIntervalGeometry& interval) {
    std::vector<double> points = {interval.lower, interval.upper};
    for (std::size_t first = 0; first < facets.size(); ++first) {
        for (std::size_t second = first + 1; second < facets.size(); ++second) {
            const double denominator = facets[first].beta - facets[second].beta;
            const double slope_scale = std::max(
                {1.0, std::fabs(facets[first].beta),
                 std::fabs(facets[second].beta)});
            if (std::fabs(denominator) <=
                64.0 * std::numeric_limits<double>::epsilon() * slope_scale) {
                continue;
            }
            const double crossing =
                (facets[second].alpha - facets[first].alpha) / denominator;
            if (crossing > interval.lower && crossing < interval.upper &&
                finite(crossing)) {
                points.push_back(crossing);
            }
        }
    }
    std::sort(points.begin(), points.end());
    const double coordinate_epsilon =
        64.0 * std::numeric_limits<double>::epsilon() *
        std::max({1.0, std::fabs(interval.lower), std::fabs(interval.upper)});
    points.erase(std::unique(points.begin(), points.end(),
        [coordinate_epsilon](double first, double second) {
            return std::fabs(first - second) <= coordinate_epsilon;
        }), points.end());
    return points;
}

bool dominatedByOthers(std::size_t candidate,
                       const std::vector<GiniEnvelopeFacet>& facets,
                       const GiniIntervalGeometry& parent,
                       double tolerance) {
    if (facets.size() <= 1) return false;
    const std::vector<double> arrangement =
        facetArrangementPoints(facets, parent);
    std::vector<double> probes = arrangement;
    for (std::size_t index = 1; index < arrangement.size(); ++index) {
        probes.push_back(0.5 * (arrangement[index - 1] + arrangement[index]));
    }
    for (double point : probes) {
        const double candidate_value =
            evaluateGiniEnvelopeFacet(facets[candidate], point);
        double other_maximum = -std::numeric_limits<double>::infinity();
        for (std::size_t index = 0; index < facets.size(); ++index) {
            if (index == candidate) continue;
            other_maximum = std::max(
                other_maximum, evaluateGiniEnvelopeFacet(facets[index], point));
        }
        if (candidate_value > other_maximum +
            scaleTolerance(tolerance, candidate_value, other_maximum)) {
            return false;
        }
    }
    return true;
}

double integrateFacetMaximum(const std::vector<GiniEnvelopeFacet>& facets,
                             const GiniIntervalGeometry& parent) {
    const std::vector<double> points = facetArrangementPoints(facets, parent);
    long double integral = 0.0L;
    for (std::size_t index = 1; index < points.size(); ++index) {
        const double left = points[index - 1];
        const double right = points[index];
        if (!(right > left)) continue;
        const double midpoint = 0.5 * (left + right);
        const GiniEnvelopeFacet* active = nullptr;
        double active_value = -std::numeric_limits<double>::infinity();
        for (const GiniEnvelopeFacet& facet : facets) {
            const double value = evaluateGiniEnvelopeFacet(facet, midpoint);
            if (value > active_value) {
                active_value = value;
                active = &facet;
            }
        }
        if (!active) return std::numeric_limits<double>::quiet_NaN();
        // Trapezoidal integration is exact for an affine facet.  Evaluating
        // both endpoints in long double avoids the alpha/beta cancellation
        // that the expanded antiderivative suffers on very narrow domains.
        const long double left_value =
            static_cast<long double>(active->alpha) +
            static_cast<long double>(active->beta) * left;
        const long double right_value =
            static_cast<long double>(active->alpha) +
            static_cast<long double>(active->beta) * right;
        integral += 0.5L * (left_value + right_value) *
            static_cast<long double>(right - left);
    }
    return static_cast<double>(integral);
}

} // namespace

double evaluateGiniEnvelopeFacet(const GiniEnvelopeFacet& facet, double g) {
    return facet.alpha + facet.beta * g;
}

bool validFinalEnvelopeLeafBound(double lower_bound, bool infeasible) {
    if (finite(lower_bound)) return true;
    return infeasible && std::isinf(lower_bound) && lower_bound > 0.0;
}

GiniEnvelopeResult constructGiniLowerBoundEnvelope(
        const GiniEnvelopeInput& input) {
    GiniEnvelopeResult result;
    const double tolerance = std::max(0.0, input.certificate_tolerance);
    if (!finite(input.parent_lower_bound) ||
        !finite(input.verified_upper_bound) ||
        input.parent_lower_bound > input.verified_upper_bound +
            scaleTolerance(tolerance, input.parent_lower_bound,
                           input.verified_upper_bound)) {
        result.status = "invalid_parent_bound_or_verified_incumbent";
        return result;
    }
    std::string coverage_reason;
    if (!lookaheadCoverageValid(input, coverage_reason)) {
        result.status = coverage_reason;
        return result;
    }

    result.clipped_bounds.reserve(input.lookahead.size());
    for (const GiniLookaheadBound& cell : input.lookahead) {
        const double raw = cell.infeasible
            ? input.verified_upper_bound : cell.lower_bound;
        result.clipped_bounds.push_back(std::min(
            input.verified_upper_bound,
            std::max(input.parent_lower_bound, raw)));
    }

    std::vector<Point> points;
    points.reserve(input.lookahead.size() + 1);
    points.push_back({input.parent.lower, result.clipped_bounds.front()});
    for (std::size_t index = 1; index < input.lookahead.size(); ++index) {
        points.push_back({
            input.lookahead[index].interval.lower,
            std::min(result.clipped_bounds[index - 1],
                     result.clipped_bounds[index])});
    }
    points.push_back({input.parent.upper, result.clipped_bounds.back()});

    std::vector<Point> hull;
    hull.reserve(points.size());
    const double width = input.parent.upper - input.parent.lower;
    const double slope_tolerance = tolerance / std::max(
        width, std::numeric_limits<double>::min());
    for (const Point& point : points) {
        while (hull.size() >= 2) {
            const Point& first = hull[hull.size() - 2];
            const Point& second = hull[hull.size() - 1];
            const double first_slope =
                (second.y - first.y) / (second.x - first.x);
            const double second_slope =
                (point.y - second.y) / (point.x - second.x);
            if (second_slope > first_slope + slope_tolerance) break;
            hull.pop_back();
        }
        hull.push_back(point);
    }

    std::vector<GiniEnvelopeFacet> generated;
    generated.push_back({
        input.parent_lower_bound, 0.0,
        input.parent.lower, input.parent.upper, true,
        "constant_parent_lower_bound"});
    for (std::size_t index = 1; index < hull.size(); ++index) {
        const Point& left = hull[index - 1];
        const Point& right = hull[index];
        const double beta = (right.y - left.y) / (right.x - left.x);
        generated.push_back({
            left.y - beta * left.x, beta,
            input.parent.lower, input.parent.upper, false,
            "lower_convex_hull_supporting_line"});
    }
    result.generated_facet_count = static_cast<long long>(generated.size());

    // An affine support line on a very narrow interval can have a large
    // slope.  Storing alpha and beta separately then loses a few ulps to
    // cancellation in alpha + beta * G.  Move only the intercept downward,
    // to the greatest representable value that passes every endpoint audit.
    // This keeps the model row conservative without treating a representable
    // dyadic interval as geometrically invalid.
    for (GiniEnvelopeFacet& facet : generated) {
        if (facet.constant_parent_candidate) continue;
        const double original_alpha = facet.alpha;
        long double conservative_alpha =
            static_cast<long double>(facet.alpha);
        for (std::size_t cell_index = 0;
             cell_index < input.lookahead.size(); ++cell_index) {
            for (double endpoint : {
                    input.lookahead[cell_index].interval.lower,
                    input.lookahead[cell_index].interval.upper}) {
                conservative_alpha = std::min(
                    conservative_alpha,
                    static_cast<long double>(result.clipped_bounds[cell_index]) -
                        static_cast<long double>(facet.beta) * endpoint);
            }
        }
        facet.alpha = static_cast<double>(conservative_alpha);
        if (facet.alpha > conservative_alpha) {
            facet.alpha = std::nextafter(
                facet.alpha, -std::numeric_limits<double>::infinity());
        }
        bool valid = false;
        for (int adjustment = 0; adjustment < 8; ++adjustment) {
            if (giniEnvelopeFacetValidOnProfile(
                    facet, input, result.clipped_bounds)) {
                valid = true;
                break;
            }
            facet.alpha = std::nextafter(
                facet.alpha, -std::numeric_limits<double>::infinity());
        }
        if (!valid) {
            facet.construction = "numerically_rejected_supporting_line";
            ++result.numerically_rejected_facet_count;
        } else if (facet.alpha != original_alpha) {
            facet.construction =
                "lower_convex_hull_supporting_line_conservative_rounding";
            ++result.numerically_adjusted_facet_count;
        }
    }
    generated.erase(std::remove_if(generated.begin(), generated.end(),
        [](const GiniEnvelopeFacet& facet) {
            return facet.construction ==
                "numerically_rejected_supporting_line";
        }), generated.end());

    std::vector<GiniEnvelopeFacet> unique;
    for (const GiniEnvelopeFacet& facet : generated) {
        bool duplicate = false;
        for (const GiniEnvelopeFacet& accepted : unique) {
            if (duplicateFacet(facet, accepted, input.parent, tolerance)) {
                duplicate = true;
                break;
            }
        }
        if (duplicate) {
            ++result.duplicate_facet_count;
        } else {
            unique.push_back(facet);
        }
    }

    for (std::size_t index = 0; index < unique.size(); ++index) {
        if (dominatedByOthers(index, unique, input.parent, tolerance)) {
            ++result.dominated_facet_count;
        } else {
            result.facets.push_back(unique[index]);
        }
    }
    if (result.facets.empty()) {
        result.status = "all_facets_removed";
        return result;
    }
    result.accepted_facet_count = static_cast<long long>(result.facets.size());

    for (const GiniEnvelopeFacet& facet : result.facets) {
        double maximum_violation = 0.0;
        std::string reason;
        if (!giniEnvelopeFacetValidOnProfile(
                facet, input, result.clipped_bounds,
                &maximum_violation, &reason)) {
            result.status = "invalid_facet:" + reason;
            result.max_endpoint_violation = std::max(
                result.max_endpoint_violation, maximum_violation);
            return result;
        }
        result.max_endpoint_violation = std::max(
            result.max_endpoint_violation, maximum_violation);
    }

    long double local = 0.0L;
    for (std::size_t index = 0; index < input.lookahead.size(); ++index) {
        local += static_cast<long double>(
            input.lookahead[index].interval.upper -
            input.lookahead[index].interval.lower) *
            static_cast<long double>(
                result.clipped_bounds[index] - input.parent_lower_bound);
    }
    result.V_local = static_cast<double>(local);
    const double envelope_integral = integrateFacetMaximum(
        result.facets, input.parent);
    result.V_envelope = envelope_integral -
        input.parent_lower_bound * width;
    result.V_residual = result.V_local - result.V_envelope;
    const double volume_tolerance = std::max(
        std::numeric_limits<double>::epsilon(),
        tolerance * width * std::max({
            1.0, std::fabs(input.parent_lower_bound),
            std::fabs(input.verified_upper_bound)}));
    if (result.V_local < 0.0 && result.V_local >= -volume_tolerance) {
        result.V_local = 0.0;
    }
    if (result.V_envelope < 0.0 &&
        result.V_envelope >= -volume_tolerance) {
        result.V_envelope = 0.0;
    }
    if (result.V_residual < 0.0 &&
        result.V_residual >= -volume_tolerance) {
        result.V_residual = 0.0;
    }
    result.integral_identity_residual = std::fabs(
        result.V_local - result.V_envelope - result.V_residual);
    if (!finite(result.V_local) || !finite(result.V_envelope) ||
        !finite(result.V_residual) || result.V_local < -volume_tolerance ||
        result.V_envelope < -volume_tolerance ||
        result.V_residual < -volume_tolerance ||
        result.integral_identity_residual > volume_tolerance) {
        result.status = "envelope_integral_audit_failed";
        return result;
    }
    result.tau_d = result.V_envelope /
        std::max(result.V_local, tolerance);
    const double denominator = width * std::max(
        input.verified_upper_bound - input.parent_lower_bound, tolerance);
    result.D_d = result.V_residual / denominator;
    if (result.D_d < 0.0 && result.D_d >= -tolerance) result.D_d = 0.0;
    if (result.D_d > 1.0 && result.D_d <= 1.0 + tolerance) result.D_d = 1.0;
    if (!finite(result.tau_d) || !finite(result.D_d) ||
        result.D_d < -tolerance || result.D_d > 1.0 + tolerance) {
        result.status = "normalized_measure_range_audit_failed";
        return result;
    }
    result.valid = true;
    result.status = "valid_greatest_convex_minorant";
    return result;
}

bool giniEnvelopeFacetValidOnProfile(
        const GiniEnvelopeFacet& facet,
        const GiniEnvelopeInput& input,
        const std::vector<double>& clipped_bounds,
        double* maximum_violation,
        std::string* reason) {
    if (maximum_violation) *maximum_violation = 0.0;
    if (!finite(facet.alpha) || !finite(facet.beta) ||
        clipped_bounds.size() != input.lookahead.size()) {
        if (reason) *reason = "invalid_facet_or_profile_size";
        return false;
    }
    double observed = 0.0;
    for (std::size_t index = 0; index < input.lookahead.size(); ++index) {
        for (double endpoint : {input.lookahead[index].interval.lower,
                                input.lookahead[index].interval.upper}) {
            const double violation =
                evaluateGiniEnvelopeFacet(facet, endpoint) -
                clipped_bounds[index];
            observed = std::max(observed, violation);
            if (violation > scaleTolerance(
                    input.certificate_tolerance,
                    evaluateGiniEnvelopeFacet(facet, endpoint),
                    clipped_bounds[index])) {
                if (maximum_violation) *maximum_violation = observed;
                if (reason) *reason = "facet_exceeds_cell_endpoint_bound";
                return false;
            }
        }
    }
    if (maximum_violation) *maximum_violation = observed;
    if (reason) *reason = "facet_valid_at_every_cell_endpoint";
    return true;
}

std::vector<GiniIntervalGeometry> makeEnvelopeInitialPartition(
        const GiniIntervalGeometry& root, int K0) {
    if (!validInterval(root) || K0 <= 0) return {};
    std::vector<GiniIntervalGeometry> result;
    result.reserve(static_cast<std::size_t>(K0));
    const double width = root.upper - root.lower;
    for (int index = 0; index < K0; ++index) {
        const double lower = index == 0 ? root.lower
            : root.lower + width * static_cast<double>(index) /
                static_cast<double>(K0);
        const double upper = index + 1 == K0 ? root.upper
            : root.lower + width * static_cast<double>(index + 1) /
                static_cast<double>(K0);
        result.push_back({lower, upper});
    }
    return result;
}

std::vector<GiniIntervalGeometry> makeDyadicLookaheadPartition(
        const GiniIntervalGeometry& parent, int depth) {
    if (!validInterval(parent) || depth < 0 || depth > 20) return {};
    const int count = 1 << depth;
    return makeEnvelopeInitialPartition(parent, count);
}

AggregatedLookaheadBound aggregateLookaheadBoundForInterval(
        const GiniIntervalGeometry& target,
        double inherited_parent_bound,
        const std::vector<GiniLookaheadBound>& lookahead,
        double certificate_tolerance) {
    AggregatedLookaheadBound result;
    if (!validInterval(target) || !finite(inherited_parent_bound) ||
        lookahead.empty()) {
        result.reason = "invalid_aggregate_input";
        return result;
    }
    double minimum = std::numeric_limits<double>::infinity();
    bool every_infeasible = true;
    double covered_lower = target.lower;
    for (const GiniLookaheadBound& cell : lookahead) {
        const bool nested =
            cell.interval.lower >= target.lower -
                scaleTolerance(certificate_tolerance, target.lower) &&
            cell.interval.upper <= target.upper +
                scaleTolerance(certificate_tolerance, target.upper);
        if (!nested) continue;
        if (!cell.terminal_valid || (!cell.infeasible &&
            (!cell.optimal || !cell.bound_available ||
             !finite(cell.lower_bound)))) {
            result.reason = "aggregate_contains_invalid_lookahead_cell";
            return result;
        }
        if (!sameEndpoint(cell.interval.lower, covered_lower,
                          certificate_tolerance)) {
            result.reason = "aggregate_lookahead_gap_or_overlap";
            return result;
        }
        covered_lower = cell.interval.upper;
        ++result.contributing_cell_count;
        if (!cell.infeasible) {
            every_infeasible = false;
            minimum = std::min(minimum, cell.lower_bound);
        }
    }
    if (!result.contributing_cell_count ||
        !sameEndpoint(covered_lower, target.upper, certificate_tolerance)) {
        result.reason = "aggregate_target_not_exactly_covered";
        return result;
    }
    result.valid = true;
    result.infeasible = every_infeasible;
    result.lower_bound = every_infeasible
        ? std::numeric_limits<double>::infinity()
        : std::max(inherited_parent_bound, minimum);
    result.reason = every_infeasible
        ? "all_contributing_cells_infeasible"
        : "minimum_complete_descendant_lp_bound_reused";
    return result;
}

bool validEnvelopeFacetScope(
        const GiniEnvelopeFacet& facet,
        const GiniIntervalGeometry& target,
        double certificate_tolerance,
        std::string* reason) {
    const bool valid = validInterval(target) &&
        target.lower >= facet.source_lower -
            scaleTolerance(certificate_tolerance, facet.source_lower) &&
        target.upper <= facet.source_upper +
            scaleTolerance(certificate_tolerance, facet.source_upper);
    if (reason) *reason = valid
        ? "target_domain_nested_in_facet_source_interval"
        : "facet_scope_not_valid_for_target_domain";
    return valid;
}

FormulationContractionResult evaluateFormulationContraction(
        const FormulationContractionInput& input) {
    FormulationContractionResult result;
    if (!validInterval(input.parent) || !finite(input.parent_A) ||
        input.parent_A <= std::max(0.0, input.epsilon_width) ||
        input.lookahead_intervals.empty() ||
        input.lookahead_intervals.size() != input.lookahead_A.size()) {
        result.reason = "invalid_contraction_input";
        return result;
    }
    const double parent_width = input.parent.upper - input.parent.lower;
    double covered = input.parent.lower;
    long double weighted = 0.0L;
    for (std::size_t index = 0;
         index < input.lookahead_intervals.size(); ++index) {
        const GiniIntervalGeometry& cell = input.lookahead_intervals[index];
        if (!validInterval(cell) || !finite(input.lookahead_A[index]) ||
            input.lookahead_A[index] < 0.0 ||
            !sameEndpoint(cell.lower, covered, input.epsilon_width)) {
            result.reason = "invalid_contraction_cell";
            return result;
        }
        covered = cell.upper;
        weighted += static_cast<long double>(cell.upper - cell.lower) *
            static_cast<long double>(input.lookahead_A[index]);
    }
    if (!sameEndpoint(covered, input.parent.upper, input.epsilon_width)) {
        result.reason = "contraction_cells_do_not_cover_parent";
        return result;
    }
    result.weighted_child_A = static_cast<double>(weighted);
    result.C_d = 1.0 - result.weighted_child_A /
        (parent_width * input.parent_A);
    const double tolerance = std::max(1e-12, input.epsilon_width);
    if (result.C_d < 0.0 && result.C_d >= -tolerance) result.C_d = 0.0;
    if (result.C_d > 1.0 && result.C_d <= 1.0 + tolerance) result.C_d = 1.0;
    if (!finite(result.C_d) || result.C_d < -tolerance ||
        result.C_d > 1.0 + tolerance) {
        result.reason = "contraction_out_of_range";
        return result;
    }
    result.valid = true;
    result.reason = "valid_solver_independent_formulation_contraction";
    return result;
}

EnvelopeRefinementDecision evaluateEnvelopeRefinementDecision(
        double D_d,
        double C_d,
        const std::string& score_mode,
        double rho,
        double certificate_tolerance) {
    EnvelopeRefinementDecision result;
    result.score_mode = score_mode;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if (!finite(D_d) || !finite(rho) || D_d < -tolerance ||
        D_d > 1.0 + tolerance || rho < 0.0 || rho > 1.0) {
        result.reason = "invalid_refinement_score_input";
        return result;
    }
    if (score_mode == "d") {
        result.score = std::max(0.0, std::min(1.0, D_d));
    } else if (score_mode == "max-d-c") {
        if (!finite(C_d) || C_d < -tolerance || C_d > 1.0 + tolerance) {
            result.reason = "invalid_contraction_score_input";
            return result;
        }
        result.score = std::max(
            std::max(0.0, std::min(1.0, D_d)),
            std::max(0.0, std::min(1.0, C_d)));
    } else {
        result.reason = "unsupported_refinement_score_mode";
        return result;
    }
    result.valid = true;
    result.split = result.score >= rho;
    result.reason = result.split
        ? "score_greater_than_or_equal_to_frozen_rho"
        : "score_strictly_below_frozen_rho";
    return result;
}

} // namespace ebrp
