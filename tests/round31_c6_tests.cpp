#include "ControllingLeafScheduler.hpp"
#include "ExternalGiniTree.hpp"
#include "GiniFrontierGeometry.hpp"
#include "PaperExternalGiniTree.hpp"

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

ebrp::PaperLpResult optimal(double bound) {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.optimal = true;
    result.bound_available = true;
    result.lower_bound = bound;
    return result;
}

ebrp::ControllingLeaf leaf(const std::string& id, double lower_bound) {
    ebrp::ControllingLeaf value;
    value.id = id;
    value.gamma_L = 0.0;
    value.gamma_U = 1.0;
    value.base_lower_bound = lower_bound;
    value.lower_bound = lower_bound;
    value.cutoff = 100.0;
    value.lower_bound_sources = {"test_valid_bound"};
    return value;
}

ebrp::FixedIntervalMipOutcome terminalBase() {
    ebrp::FixedIntervalMipOutcome outcome;
    outcome.attempted = true;
    outcome.available = true;
    outcome.solver_finalization_reached = true;
    outcome.model_fingerprint_matches_request = true;
    outcome.exact_zero_gap_roundtrip = true;
    outcome.feasibility_consistency_gate = true;
    outcome.terminal_mip = true;
    return outcome;
}

} // namespace

int main() {
    constexpr double tolerance = 1e-7;
    constexpr double rho = 0.01;
    int cases = 0;

    // 1. A complete LP-bounded leaf with a higher external frontier receives
    // a mathematical native-bound target.
    const auto lp_bounded = ebrp::evaluateC6FrontierDecision(
        10.0, {12.0}, tolerance);
    require(lp_bounded.valid && lp_bounded.run_native_target,
            "1 OPEN_LP_BOUNDED did not request native progression");
    ++cases;

    // 2. The smallest strictly higher frontier level is the next
    // OPEN_NATIVE_BOUNDED milestone.
    const auto native_bounded = ebrp::evaluateC6FrontierDecision(
        10.0, {15.0, 12.0, 14.0}, tolerance);
    require(native_bounded.run_native_target &&
                std::fabs(native_bounded.native_bound_target - 12.0) < 1e-12,
            "2 next native milestone is not the minimum strict level");
    ++cases;

    // 3. Bounds tied within certificate tolerance are ignored when choosing
    // the next strictly higher target.
    const auto next_controlling = ebrp::evaluateC6FrontierDecision(
        10.0, {10.0 + 0.5e-7, 11.0}, tolerance);
    require(next_controlling.run_native_target &&
                std::fabs(next_controlling.native_bound_target - 11.0) <
                    1e-12,
            "3 tied level displaced the next-controlling target");
    ++cases;

    // 4. A sole relevant leaf has no artificial milestone and may perform
    // lazy child lookahead followed by exact closure.
    const auto single = ebrp::evaluateC6FrontierDecision(
        10.0, {}, tolerance);
    require(single.valid && single.allow_child_lookahead &&
                !single.run_native_target,
            "4 single leaf created a vacuous target");
    ++cases;

    // 5. A lowest-bound plateau likewise has no strictly higher milestone.
    const auto tied = ebrp::evaluateC6FrontierDecision(
        10.0, {10.0, 10.0 + 0.5e-7}, tolerance);
    require(tied.valid && tied.allow_child_lookahead,
            "5 tied frontier did not enter lazy lookahead");
    ++cases;

    // 6. After a launch-frozen target is merged, the strengthened leaf is
    // requeued when another relevant leaf is now strictly lower.
    const auto reached = ebrp::evaluateC6FrontierDecision(
        12.0, {10.0, 14.0}, tolerance, true);
    require(reached.valid && reached.requeue_without_native,
            "6 target attainment did not yield scheduler requeue");
    const auto reached_reselected = ebrp::evaluateC6FrontierDecision(
        12.0, {12.0, 14.0}, tolerance, true);
    require(reached_reselected.allow_child_lookahead &&
                !reached_reselected.run_native_target,
            "6 completed frontier milestone was repeated");
    ++cases;

    // 7. Catching the cached child bound removes its current strict gain;
    // there is no mandatory delayed split.
    const auto caught_child = ebrp::evaluateC6CurrentSplitDecision(
        10.05, 20.0, optimal(10.05), optimal(10.08), rho, tolerance);
    require(caught_child.valid && caught_child.launch_exact_closure &&
                !caught_child.split_immediately,
            "7 caught child target forced a delayed split");
    ++cases;

    // 8. A current normalized disjunction gain at rho still splits.
    const auto split = ebrp::evaluateC6CurrentSplitDecision(
        10.0, 20.0, optimal(10.1), optimal(10.2), rho, tolerance);
    require(split.valid && split.split_immediately,
            "8 sufficient current child gain did not split");
    ++cases;

    // 9. A no-gain parent never receives a zero/vanishing native target; at
    // the top plateau it proceeds to the eventual exact-closure state.
    const auto no_gain = ebrp::evaluateC6CurrentSplitDecision(
        10.0, 20.0, optimal(10.0), optimal(10.0 + 0.5e-7),
        rho, tolerance);
    require(no_gain.valid && no_gain.launch_exact_closure &&
                !no_gain.run_child_bound_target,
            "9 no-gain state launched a vacuous target");
    ++cases;

    // 10. Exact optimality is an exact closure.
    auto optimal_terminal = terminalBase();
    optimal_terminal.optimal = true;
    optimal_terminal.native_bound_available = true;
    const auto exact_close =
        ebrp::evaluatePaperTerminalMipDecision(optimal_terminal);
    require(exact_close.valid && exact_close.close_leaf,
            "10 exact optimality did not close");
    ++cases;

    // 11. Parent-first and child-first mathematical predicates are
    // deterministic and compatible at the same completed evidence state.
    const auto parent_first = ebrp::evaluateC6FrontierDecision(
        10.0, {11.0}, tolerance);
    const auto child_first = ebrp::evaluateC6CurrentSplitDecision(
        10.0, 20.0, optimal(10.05), optimal(10.08), rho, tolerance);
    require(parent_first.run_native_target &&
                child_first.run_child_bound_target,
            "11 parent/child decision paths are mechanically invalid");
    ++cases;

    // 12. Parent-first lookahead is lazy: a finite higher frontier target
    // cannot simultaneously authorize child lookahead.
    require(parent_first.run_native_target &&
                !parent_first.allow_child_lookahead,
            "12 child lookahead was not avoided before frontier target");
    ++cases;

    // 13. Interruption never closes a partially processed leaf.
    auto interrupted = terminalBase();
    interrupted.interrupted = true;
    interrupted.native_bound_available = true;
    const auto open =
        ebrp::evaluatePaperTerminalMipDecision(interrupted);
    require(open.valid && open.leave_open_and_stop && !open.close_leaf,
            "13 interrupted native processing closed a leaf");
    ++cases;

    // 14. Atomic binary replacement preserves exact interval coverage.
    const auto geometry = ebrp::splitLegacyFrontierInterval(0.0, 1.0, 2);
    require(geometry.size() == 2 &&
                ebrp::exactIntervalCoverage({0.0, 1.0}, geometry, tolerance),
            "14 binary split lost exact coverage");
    ++cases;

    // 15. A merged native bound is valid, monotone, and inherited by the
    // scheduler's relevant leaf.
    ebrp::ControllingLeafScheduler scheduler(tolerance);
    std::string reason;
    require(scheduler.addLeaf(leaf("I", 10.0), &reason),
            "15 test leaf add failed");
    require(scheduler.mergeValidLowerBound(
                "I", 12.0, "valid_native_target_bound", &reason),
            "15 native bound merge failed");
    require(std::fabs(scheduler.findLeaf("I")->lower_bound - 12.0) < 1e-12,
            "15 merged native bound was not inherited");
    ++cases;

    // 16. A validity-gated partial status is not accepted as terminal
    // closure evidence.
    auto partial = terminalBase();
    partial.terminal_mip = false;
    partial.partial_bound_target_mip = true;
    partial.native_bound_target_reached = true;
    partial.native_bound_available = true;
    const auto partial_close =
        ebrp::evaluatePaperTerminalMipDecision(partial);
    require(!partial_close.valid && !partial_close.close_leaf,
            "16 partial target status was used as exact closure");
    ++cases;

    // 17. The global lower bound remains the minimum over relevant leaves.
    require(scheduler.addLeaf(leaf("J", 11.0), &reason),
            "17 second leaf add failed");
    require(std::fabs(scheduler.globalLowerBound() - 11.0) < 1e-12,
            "17 global lower bound is not the relevant-leaf minimum");
    ++cases;

    // 18. Invalid/nonfinite frontier input fails closed, ensuring a trace
    // cannot silently omit an undefined mathematical transition.
    const auto invalid = ebrp::evaluateC6FrontierDecision(
        10.0, {std::numeric_limits<double>::infinity()}, tolerance);
    require(!invalid.valid &&
                invalid.reason == "nonfinite_other_relevant_leaf_bound",
            "18 nonfinite transition did not fail closed");
    ++cases;

    require(cases == 18, "Round 31 state-machine case count changed");
    std::cout << "Round31C6Tests: 18 state-machine checks passed\n";
    return 0;
}
