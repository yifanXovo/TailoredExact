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

        const auto frozen = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "off", tolerance);
        require(frozen.valid && frozen.adaptive_refinement &&
                    frozen.initial_intervals.size() == 4 &&
                    ebrp::exactIntervalCoverage(
                        {0.0, 0.8}, frozen.initial_intervals, tolerance),
                "default-off policy did not preserve frozen K=4 coverage");
        ++checks;

        const auto single = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "k1-single", tolerance);
        require(single.valid && !single.adaptive_refinement &&
                    single.initial_intervals.size() == 1 &&
                    std::fabs(single.initial_intervals[0].lower) < 1e-12 &&
                    std::fabs(single.initial_intervals[0].upper - 0.8) < 1e-12,
                "K=1 single did not create the complete proof interval");
        ++checks;

        const auto adaptive = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "k1-adaptive", tolerance);
        require(adaptive.valid && adaptive.adaptive_refinement &&
                    adaptive.initial_intervals.size() == 1 &&
                    std::fabs(adaptive.initial_intervals[0].lower -
                              single.initial_intervals[0].lower) < 1e-12 &&
                    std::fabs(adaptive.initial_intervals[0].upper -
                              single.initial_intervals[0].upper) < 1e-12,
                "adaptive K=1 changed the root geometry");
        ++checks;

        const auto children = ebrp::splitLegacyFrontierInterval(
            adaptive.initial_intervals[0].lower,
            adaptive.initial_intervals[0].upper, 2);
        require(children.size() == 2 &&
                    ebrp::exactIntervalCoverage(
                        adaptive.initial_intervals[0], children, tolerance),
                "adaptive K=1 midpoint children lost atomic coverage");
        ++checks;

        const auto decisive = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "k1-adaptive-decisive", tolerance);
        require(decisive.valid && decisive.adaptive_refinement &&
                    decisive.initial_intervals.size() == 1 &&
                    std::fabs(decisive.initial_intervals[0].upper - 0.8) < 1e-12,
                "decisive adaptive K=1 changed the complete root cover");
        ++checks;

        const auto repeated = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "k1-adaptive", tolerance);
        require(repeated.valid &&
                    repeated.initial_intervals.size() == 1 &&
                    std::fabs(repeated.initial_intervals[0].lower -
                              adaptive.initial_intervals[0].lower) < 1e-12 &&
                    std::fabs(repeated.initial_intervals[0].upper -
                              adaptive.initial_intervals[0].upper) < 1e-12 &&
                    repeated.reason == adaptive.reason,
                "coarse-start geometry is not deterministic");
        ++checks;

        const auto unknown = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "winner-lookup", tolerance);
        require(!unknown.valid && unknown.initial_intervals.empty(),
                "unknown/sample-specific policy did not fail closed");
        ++checks;

        const auto reversed = ebrp::makeRound40CoarseStartGeometry(
            0.8, 0.0, 4, "k1-single", tolerance);
        require(!reversed.valid,
                "negative-width proof range did not fail closed");
        ++checks;

        const auto shifted = ebrp::makeRound40CoarseStartGeometry(
            0.1, 0.7, 4, "k1-single", tolerance);
        require(shifted.valid && shifted.initial_intervals.size() == 1 &&
                    ebrp::exactIntervalCoverage(
                        {0.1, 0.7}, shifted.initial_intervals, tolerance),
                "K=1 did not preserve a nonzero proof lower endpoint");
        ++checks;

        require(checks == 9, "Round 40 coarse-start check count changed");
        std::cout << "Round40CoarseStartTests: 9 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round40CoarseStartTests failed: " << error.what()
                  << '\n';
        return 1;
    }
}
