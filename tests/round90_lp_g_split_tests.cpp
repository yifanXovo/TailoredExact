#include "GiniFrontierGeometry.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void testPointAndExactClosedCover() {
    const auto selected = ebrp::selectRound90LpGSplitGeometry(0.0, 1.0, true, 0.2);
    require(selected.valid && selected.used_parent_g &&
            selected.split_point == 0.2 && selected.children.size() == 2,
            "current optimal interior LP G should select the proposed point");
    require(selected.children[0].lower == 0.0 &&
            selected.children[0].upper == selected.split_point &&
            selected.children[1].lower == selected.split_point &&
            selected.children[1].upper == 1.0,
            "the two closed child intervals must share one exact endpoint");
    require(ebrp::exactIntervalCoverage({0.0, 1.0}, selected.children, 0.0),
            "exact parent coverage rejected");

    const double nearest = std::nextafter(1.0, 2.0);
    const auto edge = ebrp::selectRound90LpGSplitGeometry(
        1.0, 2.0, true, nearest);
    require(edge.valid && edge.used_parent_g && edge.split_point == nearest,
            "strict interior nextafter point must not face a balance cutoff");
    require(edge.children[0].upper == edge.children[1].lower,
            "near-endpoint child boundary changed its binary64 value");
}

void testFallbackAndMalformedGeometry() {
    const auto legacy = ebrp::splitLegacyFrontierInterval(0.0, 1.0, 2);
    for (const auto& fixture : {
             ebrp::selectRound90LpGSplitGeometry(0.0, 1.0, false, 0.2),
             ebrp::selectRound90LpGSplitGeometry(0.0, 1.0, true, 0.0),
             ebrp::selectRound90LpGSplitGeometry(0.0, 1.0, true, 1.0),
             ebrp::selectRound90LpGSplitGeometry(
                 0.0, 1.0, true, std::numeric_limits<double>::quiet_NaN())}) {
        require(fixture.valid && !fixture.used_parent_g &&
                fixture.children[0].lower == legacy[0].lower &&
                fixture.children[0].upper == legacy[0].upper &&
                fixture.children[1].lower == legacy[1].lower &&
                fixture.children[1].upper == legacy[1].upper,
                "unavailable, boundary or nonfinite G must preserve midpoint");
    }
    require(!ebrp::selectRound90LpGSplitGeometry(1.0, 1.0, true, 1.0).valid,
            "zero-width parent accepted");
    require(!ebrp::selectRound90LpGSplitGeometry(
                0.0, std::numeric_limits<double>::infinity(), true, 0.2).valid,
            "nonfinite parent accepted");
    const double adjacent = std::nextafter(1.0, 2.0);
    require(!ebrp::selectRound90LpGSplitGeometry(
                1.0, adjacent, false, 1.0).valid,
            "unrepresentable midpoint should fail closed");
    require(ebrp::legacyAdaptiveSplitEligible(0.0, 1.0, 7, 8, 1e-4) &&
            !ebrp::legacyAdaptiveSplitEligible(0.0, 1.0, 8, 8, 1e-4) &&
            !ebrp::legacyAdaptiveSplitEligible(0.0, 1e-4, 0, 8, 1e-4),
            "depth-eight and minimum-width terminal gates changed");
}

void testCachedChildRequiresCurrentModelAndGeometry() {
    ebrp::Round90LpGCachedChildIdentity child;
    child.id = "L0.0";
    child.parent_id = "L0";
    child.child_index = 0;
    child.split_depth = 1;
    child.leaf_interval = {0.0, 0.2};
    child.artifact_interval = child.leaf_interval;
    child.lp_interval = child.leaf_interval;
    child.artifact_epoch = 7;
    child.lp_epoch = 7;
    child.artifact_ready = true;
    child.artifact_written = true;
    child.lp_complete = true;
    child.lp_terminal_valid = true;
    child.lp_optimal = true;
    child.artifact_sha256 = "canonical-a";
    child.lp_artifact_sha256 = "canonical-a";
    child.observed_file_sha256 = "canonical-a";
    const ebrp::GiniIntervalGeometry expected{0.0, 0.2};
    const auto valid = [&](long long epoch) {
        return ebrp::validRound90LpGCachedChild(
            child, "L0.0", "L0", 0, 1, expected, epoch);
    };
    require(valid(7), "same-epoch identical child was not reusable");
    require(!valid(8), "new incumbent epoch reused old child LP");
    child.artifact_epoch = child.lp_epoch = 8;
    require(valid(8), "newly rebuilt child did not become reusable");
    child.leaf_interval.upper = 0.5;
    require(!valid(8), "different cached split point reused the old child");
    child.leaf_interval = expected;
    child.lp_interval.upper = 0.5;
    require(!valid(8), "old child LP domain was accepted");
    child.lp_interval = expected;
    child.observed_file_sha256 = "mutated-model";
    require(!valid(8), "changed canonical bytes were accepted");
    child.observed_file_sha256 = "canonical-a";
    child.lp_artifact_sha256 = "old-lp-model";
    require(!valid(8), "old LP model identity was accepted");
    child.lp_artifact_sha256 = "canonical-a";
    child.lp_terminal_valid = false;
    require(!valid(8), "incomplete child LP was accepted for bound reuse");
}

} // namespace

int main() {
    try {
        testPointAndExactClosedCover();
        testFallbackAndMalformedGeometry();
        testCachedChildRequiresCurrentModelAndGeometry();
        std::cout << "Round90LpGSplitTests: 3 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round90LpGSplitTests failed: " << error.what() << '\n';
        return 1;
    }
}
