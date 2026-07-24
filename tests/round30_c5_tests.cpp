#include "PaperExternalGiniTree.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::PaperLpResult optimal(double bound) {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.optimal = true;
    result.bound_available = true;
    result.lower_bound = bound;
    return result;
}

ebrp::PaperLpResult infeasible() {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.infeasible = true;
    return result;
}

} // namespace

int main() {
    constexpr double tolerance = 1e-7;
    constexpr double rho = 0.01;

    const auto empty = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, infeasible(), optimal(12.0), rho, tolerance);
    require(empty.valid && empty.split_immediately,
            "complete child infeasibility must split immediately");
    require(empty.child_infeasibility_trigger,
            "child-infeasibility trigger missing");

    // A 2% disjunction gain relative to the remaining proof gap reaches rho.
    const auto large = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, optimal(10.2), optimal(10.3), rho, tolerance);
    require(large.valid && large.split_immediately,
            "normalized gain above rho did not split immediately");
    require(!large.run_parent_bound_target_phase,
            "large gain incorrectly launched parent target");

    // A 0.5% gain is positive but small: the exact child cover remains
    // speculative until the certified parent native bound reaches 10.05.
    const auto small = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, optimal(10.05), optimal(10.08), rho, tolerance);
    require(small.valid && !small.split_immediately,
            "small positive gain incorrectly split immediately");
    require(small.run_parent_bound_target_phase,
            "small positive gain did not request a native bound target");
    require(std::fabs(small.parent_native_bound_target - 10.05) < 1e-12,
            "parent native target is not the child disjunction bound");
    require(std::fabs(small.normalized_disjunction_gain - 0.005) < 1e-12,
            "normalized gain is incorrect");

    const auto zero = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, optimal(10.0), optimal(10.0 + 0.5e-7),
        rho, tolerance);
    require(zero.valid && zero.decline_split_and_solve_parent,
            "no-gain split must retain the exact parent");
    require(!zero.run_parent_bound_target_phase,
            "no-gain split launched a vacuous target");

    ebrp::PaperLpResult incomplete;
    const auto invalid = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, incomplete, optimal(11.0), rho, tolerance);
    require(!invalid.valid, "incomplete child LP entered a C5 decision");

    const auto repeat = ebrp::evaluateC5BoundTargetSplitDecision(
        10.0, 20.0, optimal(10.05), optimal(10.08), rho, tolerance);
    require(repeat.valid == small.valid &&
            repeat.run_parent_bound_target_phase ==
                small.run_parent_bound_target_phase &&
            repeat.parent_native_bound_target ==
                small.parent_native_bound_target &&
            repeat.reason == small.reason,
            "identical mathematical inputs changed the C5 decision");

    std::cout << "Round 30 C5 tests passed\n";
    return 0;
}
