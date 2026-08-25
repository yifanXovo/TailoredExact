#include "GiniEnvelopeRefinement.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void near(double actual, double expected, double tolerance,
          const std::string& message) {
    if (std::fabs(actual - expected) > tolerance) {
        throw std::runtime_error(message + ": actual=" +
            std::to_string(actual) + " expected=" +
            std::to_string(expected));
    }
}

ebrp::GiniLookaheadBound optimal(double lower, double upper, double bound) {
    ebrp::GiniLookaheadBound cell;
    cell.interval = {lower, upper};
    cell.terminal_valid = true;
    cell.optimal = true;
    cell.bound_available = true;
    cell.lower_bound = bound;
    return cell;
}

ebrp::GiniLookaheadBound infeasible(double lower, double upper) {
    ebrp::GiniLookaheadBound cell;
    cell.interval = {lower, upper};
    cell.terminal_valid = true;
    cell.infeasible = true;
    return cell;
}

ebrp::GiniEnvelopeInput profile(
        const std::vector<ebrp::GiniLookaheadBound>& cells,
        double parent_bound = 1.0,
        double verified_upper_bound = 5.0,
        double lower = 0.0,
        double upper = 1.0,
        double tolerance = 1e-9) {
    ebrp::GiniEnvelopeInput input;
    input.parent = {lower, upper};
    input.parent_lower_bound = parent_bound;
    input.verified_upper_bound = verified_upper_bound;
    input.lookahead = cells;
    input.certificate_tolerance = tolerance;
    return input;
}

} // namespace

int main() {
    try {
        int checks = 0;
        const ebrp::GiniIntervalGeometry root{0.1, 0.9};
        const auto k1 = ebrp::makeEnvelopeInitialPartition(root, 1);
        require(k1.size() == 1 && k1.front().lower == root.lower &&
                k1.front().upper == root.upper,
                "K0=1 must preserve the complete root interval");
        ++checks;
        const auto k4 = ebrp::makeEnvelopeInitialPartition(root, 4);
        require(k4.size() == 4 &&
                ebrp::exactIntervalCoverage(root, k4, 1e-12),
                "K0=4 must be a complete equal-width cover");
        ++checks;
        const auto k1_d2 = ebrp::makeDyadicLookaheadPartition(k1.front(), 2);
        require(k1.size() == 1 && k1_d2.size() == 4,
                "K1 d=2 lookahead must not activate four initial leaves");
        ++checks;

        const auto constant = ebrp::constructGiniLowerBoundEnvelope(profile({
            optimal(0.0, 0.5, 2.0), optimal(0.5, 1.0, 2.0)}));
        require(constant.valid && constant.facets.size() == 1,
                "constant profile envelope must be one nonredundant facet");
        near(constant.V_local, 1.0, 1e-10, "constant V_local");
        near(constant.V_envelope, 1.0, 1e-10, "constant V_envelope");
        near(constant.V_residual, 0.0, 1e-10, "constant V_residual");
        near(constant.D_d, 0.0, 1e-10, "constant D");
        ++checks;

        const auto monotone = ebrp::constructGiniLowerBoundEnvelope(profile({
            optimal(0.0, 0.5, 2.0), optimal(0.5, 1.0, 3.0)}));
        require(monotone.valid && monotone.facets.size() == 2,
                "monotone profile must retain its two supporting facets");
        near(monotone.V_local, 1.5, 1e-10, "monotone V_local");
        near(monotone.V_envelope, 1.25, 1e-10,
             "monotone V_envelope");
        near(monotone.V_residual, 0.25, 1e-10,
             "monotone V_residual");
        near(monotone.D_d, 0.0625, 1e-10, "monotone D");
        ++checks;

        const auto nonmonotone = ebrp::constructGiniLowerBoundEnvelope(profile({
            optimal(0.0, 0.25, 3.0), optimal(0.25, 0.5, 2.0),
            optimal(0.5, 0.75, 2.0), optimal(0.75, 1.0, 3.0)}));
        require(nonmonotone.valid && nonmonotone.V_residual > 0.0,
                "nonmonotone profile must produce a valid residual");
        near(nonmonotone.V_local,
             nonmonotone.V_envelope + nonmonotone.V_residual, 1e-10,
             "integral identity");
        ++checks;

        const auto with_infeasible =
            ebrp::constructGiniLowerBoundEnvelope(profile({
                infeasible(0.0, 0.5), optimal(0.5, 1.0, 2.0)}));
        require(with_infeasible.valid &&
                with_infeasible.clipped_bounds.front() == 5.0,
                "infeasible descendants must be represented by verified U");
        ++checks;

        require(ebrp::validFinalEnvelopeLeafBound(
                    std::numeric_limits<double>::infinity(), true) &&
                !ebrp::validFinalEnvelopeLeafBound(
                    std::numeric_limits<double>::infinity(), false) &&
                !ebrp::validFinalEnvelopeLeafBound(
                    -std::numeric_limits<double>::infinity(), true) &&
                !ebrp::validFinalEnvelopeLeafBound(
                    std::numeric_limits<double>::quiet_NaN(), true) &&
                ebrp::validFinalEnvelopeLeafBound(0.0, false),
                "only an infeasible leaf may use a positive infinite bound");
        ++checks;

        const auto clipped = ebrp::constructGiniLowerBoundEnvelope(profile({
            optimal(0.0, 0.5, 9.0), optimal(0.5, 1.0, -4.0)}));
        require(clipped.valid && clipped.clipped_bounds[0] == 5.0 &&
                clipped.clipped_bounds[1] == 1.0,
                "descendant bounds must be clipped monotonically to [L_I,U]");
        ++checks;

        const auto narrow = ebrp::constructGiniLowerBoundEnvelope(profile({
            optimal(0.4, 0.4000000000005, 2.0),
            optimal(0.4000000000005, 0.400000000001, 2.5)},
            1.0, 5.0, 0.4, 0.400000000001, 1e-12));
        require(narrow.valid && narrow.D_d >= 0.0 && narrow.D_d <= 1.0,
                "very narrow interval must remain numerically valid: " +
                    narrow.status + " Vlocal=" +
                    std::to_string(narrow.V_local) + " Venvelope=" +
                    std::to_string(narrow.V_envelope) + " Vresidual=" +
                    std::to_string(narrow.V_residual));
        ++checks;

        for (const auto& facet : monotone.facets) {
            double violation = 0.0;
            std::string reason;
            require(ebrp::giniEnvelopeFacetValidOnProfile(
                        facet, profile({optimal(0.0, 0.5, 2.0),
                                        optimal(0.5, 1.0, 3.0)}),
                        monotone.clipped_bounds, &violation, &reason) &&
                    violation <= 1e-9,
                    "every accepted facet must satisfy all endpoint checks");
        }
        ++checks;

        ebrp::GiniEnvelopeFacet scoped;
        scoped.source_lower = 0.0;
        scoped.source_upper = 0.5;
        std::string scope_reason;
        require(ebrp::validEnvelopeFacetScope(
                    scoped, {0.1, 0.4}, 1e-9, &scope_reason) &&
                !ebrp::validEnvelopeFacetScope(
                    scoped, {0.4, 0.6}, 1e-9, &scope_reason),
                "interval-local facets must propagate only to nested domains");
        ++checks;

        const auto aggregated = ebrp::aggregateLookaheadBoundForInterval(
            {0.0, 0.5}, 1.0,
            {optimal(0.0, 0.25, 2.0), optimal(0.25, 0.5, 3.0),
             optimal(0.5, 0.75, 4.0), optimal(0.75, 1.0, 5.0)}, 1e-9);
        require(aggregated.valid && !aggregated.infeasible &&
                aggregated.contributing_cell_count == 2,
                "midpoint child must reuse exactly its descendant cells");
        near(aggregated.lower_bound, 2.0, 1e-12,
             "aggregate descendant lower bound");
        ++checks;

        ebrp::FormulationContractionInput contraction;
        contraction.parent = {0.0, 1.0};
        contraction.parent_A = 10.0;
        contraction.lookahead_intervals = {{0.0, 0.5}, {0.5, 1.0}};
        contraction.lookahead_A = {5.0, 5.0};
        const auto contracted =
            ebrp::evaluateFormulationContraction(contraction);
        require(contracted.valid, "contraction calculation must be valid");
        near(contracted.C_d, 0.5, 1e-12, "contraction value");
        contraction.lookahead_intervals = {
            {0.0, 0.25}, {0.25, 0.5}, {0.5, 0.75}, {0.75, 1.0}};
        contraction.lookahead_A = {2.5, 2.5, 2.5, 2.5};
        const auto contracted_d2 =
            ebrp::evaluateFormulationContraction(contraction);
        require(contracted_d2.valid,
                "depth-two contraction calculation must be valid");
        near(contracted_d2.C_d, 0.75, 1e-12,
             "depth-two contraction value");
        ++checks;

        const auto equality = ebrp::evaluateEnvelopeRefinementDecision(
            0.05, 0.0, "d", 0.05, 1e-7);
        require(equality.valid && equality.split,
                "score equality must midpoint split");
        const auto below = ebrp::evaluateEnvelopeRefinementDecision(
            0.049999, 0.0, "d", 0.05, 1e-7);
        require(below.valid && !below.split,
                "strictly sub-threshold score must retain parent");
        const auto secondary = ebrp::evaluateEnvelopeRefinementDecision(
            0.01, 0.08, "max-d-c", 0.05, 1e-7);
        require(secondary.valid && secondary.split &&
                secondary.score == 0.08,
                "secondary score is exactly max(D,C)");
        ++checks;

        const auto midpoint = ebrp::makeDyadicLookaheadPartition(root, 1);
        require(ebrp::exactIntervalCoverage(root, midpoint, 1e-12),
                "binary midpoint split must preserve exact coverage");
        ++checks;

        std::cout << "Round43EnvelopeRefinementTests: " << checks
                  << " checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round43EnvelopeRefinementTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}
