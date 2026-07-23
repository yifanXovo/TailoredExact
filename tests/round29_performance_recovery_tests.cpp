#include "ExternalGiniTree.hpp"
#include "PaperExternalGiniTree.hpp"
#include "ProcessPhaseLedger.hpp"
#include "Result.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {

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

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

} // namespace

int main() {
    using namespace std::chrono;

    // The work deadline is derived from process entry, not solver entry.
    ebrp::SolveOptions deadline;
    deadline.process_start_time_valid = true;
    deadline.process_start_time = steady_clock::now() - milliseconds(1500);
    deadline.process_wall_time_limit = 3.0;
    deadline.solve_time_limit = 1000.0; // must not rebase the process deadline.
    deadline.process_shutdown_margin_seconds = 0.5;
    const double remaining = ebrp::processWorkRemainingSeconds(deadline);
    require(remaining > 0.8 && remaining < 1.2,
            "process-entry work deadline was rebased");
    deadline.process_start_time = steady_clock::now() - milliseconds(3100);
    require(ebrp::processWorkDeadlineReached(deadline),
            "expired process deadline was not observed");

    // C4 splits only on two complete child LPs plus infeasibility or a strict
    // post-split controlling-bound gain.
    const auto no_gain = ebrp::evaluatePaperLpSplitDecision(
        10.0, optimal(10.0), optimal(10.0 + 0.5e-7), 1e-7);
    require(no_gain.valid && !no_gain.should_split,
            "tolerance-level gain incorrectly split");
    const auto strict_gain = ebrp::evaluatePaperLpSplitDecision(
        10.0, optimal(10.1), optimal(10.2), 1e-7);
    require(strict_gain.valid && strict_gain.should_split,
            "strict child-bound gain did not split");
    require(strict_gain.strict_bound_improvement_trigger,
            "strict bound trigger missing");
    const auto empty_child = ebrp::evaluatePaperLpSplitDecision(
        10.0, infeasible(), optimal(10.0), 1e-7);
    require(empty_child.valid && empty_child.should_split,
            "child infeasibility did not split");
    require(empty_child.child_infeasibility_trigger,
            "child infeasibility trigger missing");
    ebrp::PaperLpResult incomplete;
    const auto invalid = ebrp::evaluatePaperLpSplitDecision(
        10.0, incomplete, optimal(11.0), 1e-7);
    require(!invalid.valid && !invalid.should_split,
            "incomplete child LP entered split decision");
    const auto deterministic_repeat = ebrp::evaluatePaperLpSplitDecision(
        10.0, optimal(10.1), optimal(10.2), 1e-7);
    require(
        deterministic_repeat.valid == strict_gain.valid &&
        deterministic_repeat.should_split == strict_gain.should_split &&
        deterministic_repeat.reason == strict_gain.reason,
        "identical mathematical evidence changed the split decision");

    // The engineering shutdown margin is not an input to the mathematical
    // predicate: changing deadline state cannot change a completed decision.
    deadline.process_shutdown_margin_seconds = 0.0;
    const auto margin_zero = ebrp::evaluatePaperLpSplitDecision(
        10.0, optimal(10.1), optimal(10.2), 1e-7);
    deadline.process_shutdown_margin_seconds = 2.5;
    const auto margin_nonzero = ebrp::evaluatePaperLpSplitDecision(
        10.0, optimal(10.1), optimal(10.2), 1e-7);
    require(margin_zero.should_split == margin_nonzero.should_split,
            "shutdown margin altered a mathematical split");

    ebrp::FixedIntervalMipOutcome terminal_optimal;
    terminal_optimal.attempted = true;
    terminal_optimal.available = true;
    terminal_optimal.solver_finalization_reached = true;
    terminal_optimal.model_fingerprint_matches_request = true;
    terminal_optimal.exact_zero_gap_roundtrip = true;
    terminal_optimal.feasibility_consistency_gate = true;
    terminal_optimal.terminal_mip = true;
    terminal_optimal.optimal = true;
    terminal_optimal.native_bound_available = true;
    const auto close_optimal =
        ebrp::evaluatePaperTerminalMipDecision(terminal_optimal);
    require(close_optimal.valid && close_optimal.close_leaf,
            "exact optimal parent MIP did not close its leaf");
    ebrp::FixedIntervalMipOutcome terminal_interrupted = terminal_optimal;
    terminal_interrupted.optimal = false;
    terminal_interrupted.native_bound_available = false;
    terminal_interrupted.interrupted = true;
    const auto leave_open =
        ebrp::evaluatePaperTerminalMipDecision(terminal_interrupted);
    require(leave_open.valid && leave_open.leave_open_and_stop &&
                !leave_open.close_leaf,
            "interrupted terminal MIP did not remain open");

    // A deadline or a verified incumbent alone cannot issue a strict external
    // certificate when coverage remains open.
    ebrp::ExternalGiniTreeCertificateInput certificate;
    certificate.complete_root_coverage = true;
    certificate.parent_child_coverage_valid = true;
    certificate.all_leaf_bounds_valid = true;
    certificate.global_bound_valid = true;
    certificate.global_bound_monotone = true;
    certificate.leaf_bounds_monotone = true;
    certificate.verified_global_ub = true;
    certificate.lifecycle_complete = true;
    certificate.feasibility_consistency_gate = true;
    certificate.global_lb = 5.0;
    certificate.verified_ub = 10.0;
    certificate.all_relevant_leaves_closed = false;
    const auto rejected =
        ebrp::evaluateExternalGiniTreeCertificate(certificate);
    require(!rejected.certified,
            "open coverage issued a strict certificate");

    // The explicit pre-exact fields round-trip through JSON without implying
    // an interval-tree bound.
    ebrp::SolveResult result;
    result.exact_phase_started = false;
    result.lower_bound = 0.0;
    result.conservative_lower_bound_source =
        "objective_nonnegative_G_plus_lambda_P";
    result.overall_deadline_started_at_process_entry = true;
    result.process_shutdown_margin_seconds = 5.0;
    const std::string json = ebrp::resultToJson(result);
    require(json.find("\"exact_phase_started\": false") != std::string::npos,
            "exact-phase flag did not serialize");
    require(
        json.find("\"overall_deadline_started_at_process_entry\": true") !=
            std::string::npos,
        "process-entry deadline flag did not serialize");
    require(json.find("objective_nonnegative_G_plus_lambda_P") !=
                std::string::npos,
            "conservative lower-bound source did not serialize");

    std::cout << "Round29PerformanceRecoveryTests: all checks passed\n";
    return 0;
}
