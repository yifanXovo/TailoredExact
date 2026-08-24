#include "GiniFrontierGeometry.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        int checks = 0;

        const auto weak = ebrp::makeRound40NestedDyadicGeometry(
            0.0, 0.504, 0.9, 4, tolerance);
        require(weak.valid && weak.dyadic_level == 2 &&
                    weak.global_cell_count == 4 &&
                    weak.active_intervals.size() == 3 &&
                    weak.active_anchor_cells.size() == 3 &&
                    weak.active_global_cell_indices.size() == 3 &&
                    weak.active_global_cell_indices.back() == 2 &&
                    weak.truncated_active_interval_count == 1 &&
                    ebrp::exactIntervalCoverage(
                        {0.0, 0.504}, weak.active_intervals, tolerance),
                "weak-UB dyadic prefix is not the expected exact cover");
        ++checks;

        require(std::fabs(weak.active_intervals[0].upper - 0.225) < 1e-12 &&
                    std::fabs(weak.active_intervals[1].upper - 0.45) < 1e-12 &&
                    std::fabs(weak.active_intervals[2].upper - 0.504) < 1e-12 &&
                    std::fabs(weak.active_anchor_cells[2].upper - 0.675) <
                        1e-12,
                "dyadic boundaries slid away from the stable root grid");
        ++checks;

        const auto same_level_stronger =
            ebrp::makeRound40NestedDyadicGeometry(
                0.0, 0.48, 0.9, 4, tolerance);
        std::string preservation_reason;
        require(same_level_stronger.valid &&
                    same_level_stronger.dyadic_level == weak.dyadic_level &&
                    ebrp::round40NestedBoundaryPreservation(
                        weak, same_level_stronger, tolerance,
                        &preservation_reason),
                "same-level stronger UB redrew a relevant boundary");
        ++checks;

        const auto refined_stronger = ebrp::makeRound40NestedDyadicGeometry(
            0.0, 0.44, 0.9, 4, tolerance);
        require(refined_stronger.valid && refined_stronger.dyadic_level == 3 &&
                    refined_stronger.global_cell_count == 8 &&
                    refined_stronger.active_intervals.size() == 4 &&
                    ebrp::round40NestedBoundaryPreservation(
                        weak, refined_stronger, tolerance,
                        &preservation_reason),
                "stronger UB refinement did not preserve old dyadic boundaries");
        ++checks;

        require(std::fabs(refined_stronger.active_intervals[1].upper -
                          0.225) < 1e-12,
                "refined hierarchy does not contain its coarser boundary");
        ++checks;

        const auto repeated = ebrp::makeRound40NestedDyadicGeometry(
            0.0, 0.504, 0.9, 4, tolerance);
        require(repeated.valid && repeated.dyadic_level == weak.dyadic_level &&
                    repeated.global_cell_count == weak.global_cell_count &&
                    repeated.active_intervals.size() ==
                        weak.active_intervals.size() &&
                    repeated.reason == weak.reason,
                "nested dyadic geometry is not deterministic");
        ++checks;

        const auto zero = ebrp::makeRound40NestedDyadicGeometry(
            0.0, 0.0, 0.9, 4, tolerance);
        require(zero.valid && zero.active_intervals.size() == 1 &&
                    ebrp::exactIntervalCoverage(
                        {0.0, 0.0}, zero.active_intervals, tolerance),
                "zero proof range lost its exact shortcut cover");
        ++checks;

        const auto unsafe_root = ebrp::makeRound40NestedDyadicGeometry(
            0.0, 0.91, 0.9, 4, tolerance);
        require(!unsafe_root.valid && unsafe_root.active_intervals.empty(),
                "stable root below proof cutoff did not fail closed");
        ++checks;

        const auto partial_range = ebrp::makeRound40NestedDyadicGeometry(
            0.1, 0.5, 0.9, 4, tolerance);
        require(!partial_range.valid,
                "nonzero proof lower endpoint bypassed full-range contract");
        ++checks;

        require(checks == 9, "Round 40 UB-geometry check count changed");
        std::cout << "Round40UbGeometryTests: 9 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round40UbGeometryTests failed: " << error.what()
                  << '\n';
        return 1;
    }
}
