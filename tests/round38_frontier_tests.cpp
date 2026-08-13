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

ebrp::PilotFrontierChildBound child(double bound) {
    ebrp::PilotFrontierChildBound value;
    value.terminal_valid = true;
    value.optimal = true;
    value.bound_available = true;
    value.lower_bound = bound;
    return value;
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        int checks = 0;
        const std::vector<ebrp::PilotGiniCellAssessment> panel = {
            cell("L0", 0.0, 0.2, 3.0),
            cell("L1", 0.2, 0.4, 1.5),
            cell("L2", 0.4, 0.6, 2.0),
            cell("L3", 0.6, 0.8, 4.0),
        };
        const auto selection = ebrp::selectPilotGlobalFrontierCell(
            panel, tolerance);
        require(selection.valid && selection.unique_controlling_cell &&
                    selection.leaf_id == "L1" &&
                    std::fabs(selection.next_strict_frontier - 2.0) < 1e-12 &&
                    selection.frontier_plateau_size == 1,
                "unique controlling cell or strict frontier was wrong");
        ++checks;

        const auto complete = ebrp::evaluatePilotGlobalFrontierLift(
            selection, child(2.1), child(2.4), tolerance);
        require(complete.valid && complete.split_immediately &&
                    complete.completes_next_strict_frontier &&
                    std::fabs(complete.b_plus - 2.1) < 1e-12 &&
                    std::fabs(complete.delta_global - 0.5) < 1e-12,
                "frontier-completing children were not accepted");
        ++checks;

        const auto incomplete = ebrp::evaluatePilotGlobalFrontierLift(
            selection, child(1.8), child(2.4), tolerance);
        require(incomplete.valid && !incomplete.split_immediately &&
                    !incomplete.completes_next_strict_frontier &&
                    std::fabs(incomplete.delta_local - 0.3) < 1e-12 &&
                    std::fabs(incomplete.delta_global - 0.3) < 1e-12,
                "non-completing local lift was not rejected");
        ++checks;

        auto tied_panel = panel;
        tied_panel[2].lp_lower_bound = 1.5 + 0.5 * tolerance;
        const auto tied = ebrp::selectPilotGlobalFrontierCell(
            tied_panel, tolerance);
        require(!tied.valid && tied.frontier_plateau_size == 2 &&
                    tied.reason == "minimum_bound_frontier_not_unique",
                "minimum plateau did not fail closed");
        ++checks;

        const std::vector<ebrp::PilotGiniCellAssessment> singleton = {
            cell("L0", 0.0, 0.2, 1.5)
        };
        const auto no_frontier = ebrp::selectPilotGlobalFrontierCell(
            singleton, tolerance);
        require(!no_frontier.valid &&
                    no_frontier.unique_controlling_cell &&
                    !no_frontier.next_strict_frontier_available,
                "missing next strict frontier did not fail closed");
        ++checks;

        auto infeasible = child(0.0);
        infeasible.optimal = false;
        infeasible.bound_available = false;
        infeasible.infeasible = true;
        const auto one_infeasible = ebrp::evaluatePilotGlobalFrontierLift(
            selection, infeasible, child(2.2), tolerance);
        require(one_infeasible.valid && one_infeasible.split_immediately &&
                    std::fabs(one_infeasible.b_plus - 2.2) < 1e-12,
                "valid infeasible child was not treated as infinite bound");
        ++checks;

        std::cout << "Round 38 frontier tests passed: " << checks << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round 38 frontier tests failed: " << error.what()
                  << '\n';
        return 1;
    }
}

