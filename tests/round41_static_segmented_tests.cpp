#include "Instance.hpp"
#include "StaticSegmentedGini.hpp"

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
        constexpr double tolerance = 1e-9;
        int checks = 0;

        const auto geometry =
            ebrp::makeRound41StaticK2Geometry(0.0, 0.8, tolerance);
        require(geometry.valid && geometry.segments.size() == 2 &&
                    std::fabs(geometry.midpoint - 0.4) < tolerance &&
                    ebrp::exactIntervalCoverage(
                        {0.0, 0.8}, geometry.segments, tolerance),
                "static K2 is not an exact deterministic midpoint cover");
        ++checks;

        const auto repeated =
            ebrp::makeRound41StaticK2Geometry(0.0, 0.8, tolerance);
        require(repeated.valid && repeated.reason == geometry.reason &&
                    repeated.midpoint == geometry.midpoint,
                "static K2 geometry is not deterministic");
        ++checks;

        require(!ebrp::makeRound41StaticK2Geometry(
                        0.8, 0.0, tolerance).valid,
                "reversed static K2 range did not fail closed");
        ++checks;

        for (int selector = 0; selector <= 1; ++selector) {
            for (int bit = 0; bit <= 1; ++bit) {
                const double segment_g = selector ? 0.55 : 0.0;
                require(ebrp::round41PerspectiveProductBlockValid(
                            0.4, 0.8, selector, bit, 0.55, segment_g,
                            selector * bit, segment_g * bit, tolerance),
                        "integral perspective truth table failed");
            }
        }
        ++checks;

        require(ebrp::round41PerspectiveProductBlockValid(
                    0.0, 0.4, 0.5, 0.5, 0.3, 0.15, 0.25, 0.075,
                    tolerance),
                "valid fractional perspective point was rejected");
        ++checks;

        require(!ebrp::round41PerspectiveProductBlockValid(
                    0.0, 0.4, 1.0, 1.0, 0.3, 0.3, 1.0, 0.2,
                    tolerance),
                "incorrect integral perspective product was accepted");
        ++checks;

        require(ebrp::round41SelectedContinuousBlockValid(
                    0.0, 10.0, 2.0, 8.0, 0.0, 7.0, 0.0,
                    tolerance) &&
                    ebrp::round41SelectedContinuousBlockValid(
                        0.0, 10.0, 2.0, 8.0, 1.0, 7.0, 7.0,
                        tolerance),
                "selected continuous integral endpoints failed");
        ++checks;

        require(ebrp::round41SelectedContinuousBlockValid(
                    0.0, 10.0, 2.0, 8.0, 0.5, 5.0, 2.5,
                    tolerance),
                "valid fractional selected-continuous point was rejected");
        ++checks;

        require(!ebrp::round41SelectedContinuousBlockValid(
                    0.0, 10.0, 2.0, 8.0, 1.0, 7.0, 6.0,
                    tolerance),
                "active selected-continuous copy need not equal original");
        ++checks;

        const ebrp::SolveOptions defaults;
        require(defaults.round41_static_segmented_gini == "off" &&
                    defaults.round41_static_segmented_solve == "mip",
                "Round 41 options are not default-off");
        ++checks;

        require(checks == 10, "Round 41 static test count changed");
        std::cout << "Round41StaticSegmentedTests: 10 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round41StaticSegmentedTests failed: " << error.what()
                  << '\n';
        return 1;
    }
}
