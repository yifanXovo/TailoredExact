#include "GiniFrontierGeometry.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::PilotGiniCellAssessment cell(const std::string& id,
                                   double lower,
                                   double upper,
                                   double bound) {
    ebrp::PilotGiniCellAssessment value;
    value.leaf_id = id;
    value.interval = {lower, upper};
    value.structurally_open = true;
    value.lp_complete = true;
    value.lp_optimal = true;
    value.lp_bound_available = true;
    value.lp_lower_bound = bound;
    value.verified_cutoff = 10.0;
    return value;
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        int checks = 0;

        std::vector<ebrp::PilotGiniCellAssessment> panel = {
            cell("L0", 0.0, 0.2, 3.0),
            cell("L1", 0.2, 0.4, 1.5),
            cell("L2", 0.4, 0.6, 2.0),
            cell("L3", 0.6, 0.8, 4.0),
        };
        const auto weakest = ebrp::selectPilotWeakestGiniCell(
            panel, tolerance);
        require(weakest.valid && weakest.leaf_id == "L1" &&
                    weakest.eligible_cell_count == 4 &&
                    std::fabs(weakest.lp_lower_bound - 1.5) < 1e-12,
                "pilot did not select the weakest complete LP cell");
        ++checks;

        panel[0].lp_lower_bound = 1.5 + 0.5 * tolerance;
        const auto structural_tie = ebrp::selectPilotWeakestGiniCell(
            panel, tolerance);
        require(structural_tie.valid && structural_tie.leaf_id == "L0",
                "LP-bound tolerance tie did not use lower Gini endpoint");
        ++checks;

        panel[0].lp_complete = false;
        panel[1].lp_optimal = false;
        panel[2].lp_bound_available = false;
        panel[3].lp_lower_bound = panel[3].verified_cutoff;
        const auto rejected = ebrp::selectPilotWeakestGiniCell(
            panel, tolerance);
        require(!rejected.valid && rejected.eligible_cell_count == 0,
                "pilot accepted an incomplete, invalid, or cutoff LP cell");
        ++checks;

        const ebrp::GiniIntervalGeometry parent{0.2, 0.4};
        const auto children = ebrp::splitLegacyFrontierInterval(
            parent.lower, parent.upper, 2);
        std::string coverage_reason;
        require(children.size() == 2 &&
                    ebrp::exactIntervalCoverage(
                        parent, children, tolerance, &coverage_reason) &&
                    std::fabs(children.front().upper - 0.3) < 1e-12,
                "pilot midpoint children did not exactly cover their parent");
        ++checks;

        std::cout << "Round 37 geometry tests passed: " << checks << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round 37 geometry tests failed: " << error.what()
                  << '\n';
        return 1;
    }
}
