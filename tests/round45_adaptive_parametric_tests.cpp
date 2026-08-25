#include "GiniAdaptiveParametric.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

void near(double actual, double expected, double tolerance,
          const std::string& message) {
    if (std::fabs(actual - expected) > tolerance)
        throw std::runtime_error(message);
}

ebrp::ParametricAffineSegment seg(
        double lo, double hi, double intercept, double slope,
        const std::string& basis = "basis") {
    return {lo, hi, intercept, slope, basis, false};
}

} // namespace

int main() {
    try {
        int checks = 0;
        const auto gamma = ebrp::evaluateGammaSum({
            {0.0, 1.0}, {0.0, 0.5}, {0.5, 1.0},
            1.0, 1.5, 1.25, 2.0, 4.0, 1e-7});
        require(gamma.valid, "Gamma_sum input must be valid");
        near(gamma.parent_mass, 1.0, 1e-12, "parent residual mass");
        near(gamma.split_mass, 0.625, 1e-12, "split residual mass");
        near(gamma.gamma_sum, 0.09375, 1e-12, "Gamma_sum formula");
        ++checks;

        ebrp::AdaptiveTimingInput timing;
        timing.family = "gamma-positive";
        timing.Gamma_sum = gamma.gamma_sum;
        timing.epsilon_gamma = gamma.epsilon_gamma;
        require(ebrp::evaluateAdaptiveTimingDecision(timing).split,
                "positive Gamma must split");
        timing.Gamma_sum = -0.01;
        require(!ebrp::evaluateAdaptiveTimingDecision(timing).split,
                "negative Gamma must retain");
        timing.family = "no-adaptive";
        const auto noadaptive = ebrp::evaluateAdaptiveTimingDecision(timing);
        require(noadaptive.valid && !noadaptive.genuinely_adaptive_family,
                "no-adaptive is ineligible for adaptive promotion");
        ++checks;

        const auto sensitivity = ebrp::parametricBasisSensitivityInterval(
            {2.0, 0.5, 0.75});
        near(sensitivity.lower, 1.5, 1e-12, "basis sensitivity lower");
        near(sensitivity.upper, 2.75, 1e-12, "basis sensitivity upper");
        near(ebrp::affineParametricValue(4.0, -2.0, 2.5, 2.0),
             3.0, 1e-12, "stable-basis affine value");
        ++checks;

        near(ebrp::canonicalRightParametricCoefficient(3.0), -3.0,
             1e-12, "right row coefficient sign");
        near(ebrp::canonicalRightParametricRhs(0.4), -0.4,
             1e-12, "right row RHS sign");
        ++checks;

        const std::vector<ebrp::ParametricAffineSegment> left = {
            seg(0.1, 0.5, 3.0, -1.0, "L0"),
            seg(0.5, 0.9, 2.75, -0.5, "L1")};
        const std::vector<ebrp::ParametricAffineSegment> right = {
            seg(0.1, 0.5, 1.0, 1.0, "R0"),
            seg(0.5, 0.9, 1.25, 0.5, "R1")};
        require(ebrp::auditParametricValueFunction(
                    left, {0.1, 0.9}, true, 1e-10).valid,
                "left value function monotonicity and breakpoint transition");
        require(ebrp::auditParametricValueFunction(
                    right, {0.1, 0.9}, false, 1e-10).valid,
                "right value function monotonicity and breakpoint transition");
        ++checks;

        const auto merged = ebrp::mergeParametricSegments({
            seg(0.0, 0.25, 1.0, -1.0, "a"),
            seg(0.25, 0.5, 1.0, -1.0, "duplicate"),
            {0.5, 0.5, 0.5, -1.0, "degenerate", true}}, 1e-12);
        require(merged.size() == 1 && merged.front().upper == 0.5,
                "duplicate segments merge and zero-width degeneracy drops");
        ++checks;

        const auto crossing = ebrp::selectParametricMaxMinPoint({
            {0.0, 1.0}, {seg(0.0, 1.0, 2.0, -1.0)},
            {seg(0.0, 1.0, 0.0, 1.0)}, false, 0.0, 1e-10});
        require(crossing.certified, "unique crossing must certify");
        near(crossing.selected_point, 1.0, 1e-9,
             "unique max-min crossing at admissible boundary");
        ++checks;

        const auto nonmid = ebrp::selectParametricMaxMinPoint({
            {0.1, 0.9}, {seg(0.1, 0.9, 2.0, -1.0)},
            {seg(0.1, 0.9, -0.2, 2.0)}, false, 0.0, 1e-10});
        require(nonmid.certified, "nonmidpoint PMM must certify");
        near(nonmid.selected_point, 2.2 / 3.0, 1e-9,
             "PMM differs from midpoint");
        ++checks;

        const auto symmetric = ebrp::selectParametricMaxMinPoint({
            {0.1, 0.9}, {seg(0.1, 0.9, 1.0, -1.0)},
            {seg(0.1, 0.9, 0.0, 1.0)}, false, 0.0, 1e-10});
        near(symmetric.selected_point, 0.5, 1e-9,
             "PMM equals midpoint under symmetry");
        ++checks;

        const auto fpmm = ebrp::selectParametricMaxMinPoint({
            {0.1, 0.9}, {seg(0.1, 0.9, 1.0, -1.0)},
            {seg(0.1, 0.9, 0.0, 1.0)}, true, 0.3, 1e-10});
        require(fpmm.certified && fpmm.plateau,
                "FPMM target clipping creates a plateau");
        near(fpmm.selected_point, 0.5, 1e-9,
             "deterministic plateau midpoint tie-break");
        ++checks;

        const auto bad_coverage = ebrp::selectParametricMaxMinPoint({
            {0.1, 0.9}, {seg(0.1, 0.4, 1.0, -1.0)},
            {seg(0.1, 0.9, 0.0, 1.0)}, false, 0.0, 1e-10});
        require(!bad_coverage.certified &&
                bad_coverage.reason ==
                    "certified_parametric_point_unavailable_retain_parent",
                "uncertified parametric point fails closed to retain");
        ++checks;

        std::vector<ebrp::ParametricRootSample> samples = {
            {0.2, 2.0, 1.0, false, false, true, true},
            {0.5, 1.5, 1.5, false, false, true, true},
            {0.8, 1.0, 2.0, false, false, true, true}};
        require(ebrp::auditParametricRootSamples(samples, 1e-10).valid,
                "both-child monotone root-solver coverage");
        samples[1].right_optimal = false;
        require(!ebrp::auditParametricRootSamples(samples, 1e-10).valid,
                "incomplete right child fails closed");
        ++checks;

        const double infinity = std::numeric_limits<double>::infinity();
        const std::vector<ebrp::ParametricRootSample> endpoint_infeasible = {
            {0.2, infinity, 1.0, true, false, true, true},
            {0.5, 1.5, 1.5, false, false, true, true},
            {0.8, 1.0, infinity, false, true, true, true}};
        require(ebrp::auditParametricRootSamples(
                    endpoint_infeasible, 1e-10).valid,
                "certified infeasible left and right endpoints use +infinity");
        ++checks;

        const std::vector<ebrp::GiniIntervalGeometry> nonmidpoint_cover = {
            {0.0, nonmid.selected_point}, {nonmid.selected_point, 1.0}};
        require(ebrp::exactIntervalCoverage(
                    {0.0, 1.0}, nonmidpoint_cover, 1e-10) &&
                nonmid.selected_point >= 0.1 &&
                nonmid.selected_point <= 0.9,
                "minimum width and exact nonmidpoint interval coverage");
        ++checks;

        std::cout << "Round45AdaptiveParametricTests: " << checks
                  << " checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round45AdaptiveParametricTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}
