#include "ControllingLeafScheduler.hpp"
#include "ExternalGiniTree.hpp"
#include "GiniFrontierGeometry.hpp"
#include "PaperExternalGiniTree.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int checks = 0;

void require(bool condition, const std::string& message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}

ebrp::ControllingLeaf leaf(const std::string& id,
                           double lower,
                           double upper,
                           double bound,
                           int depth = 0) {
    ebrp::ControllingLeaf out;
    out.id = id;
    out.gamma_L = lower;
    out.gamma_U = upper;
    out.base_lower_bound = bound;
    out.lower_bound = bound;
    out.lower_bound_sources = {"test_valid_bound"};
    out.cutoff = 1.0;
    out.split_depth = depth;
    return out;
}

void geometryChecks() {
    const auto root = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.8, 0, 4, 8, 1e-4, 2);
    require(root.eligible, "root must split");
    require(root.phase == ebrp::CplexReplicaSplitPhase::InitialPartition,
            "root must use initial partition phase");
    require(std::fabs(root.split_point - 0.4) < 1e-12,
            "root split must be median initial breakpoint");
    require(root.initial_partition_depth == 2,
            "four initial leaves require two binary levels");
    require(root.adaptive_depth == 0,
            "root adaptive depth is clamped to zero");

    const auto left = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.4, 1, 4, 8, 1e-4, 2);
    const auto right = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.4, 0.8, 1, 4, 8, 1e-4, 2);
    require(left.eligible && right.eligible,
            "both initial children must split");
    require(std::fabs(left.split_point - 0.2) < 1e-12,
            "left initial breakpoint must match equal partition");
    require(std::fabs(right.split_point - 0.6) < 1e-12,
            "right initial breakpoint must match equal partition");

    const auto adaptive = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.2, 2, 4, 8, 1e-4, 2);
    require(adaptive.eligible, "initial leaf must enter adaptive phase");
    require(adaptive.phase == ebrp::CplexReplicaSplitPhase::AdaptiveRefinement,
            "phase must be adaptive after initial partition");
    require(std::fabs(adaptive.split_point - 0.1) < 1e-12,
            "adaptive geometry must be midpoint");
    require(adaptive.adaptive_depth == 0,
            "adaptive depth starts after initial partition depth");

    const auto max_depth = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.2, 10, 4, 8, 1e-4, 2);
    require(!max_depth.eligible, "depth ten must be structurally terminal");
    require(max_depth.reason == "terminal_max_adaptive_depth",
            "terminal depth reason must be explicit");
    const auto narrow = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.0001, 2, 4, 8, 1e-4, 2);
    require(!narrow.eligible, "minimum-width leaf must be terminal");
    require(narrow.reason == "terminal_minimum_interval_width",
            "terminal width reason must be explicit");
    const auto wrong_factor = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, 0.0, 0.2, 2, 4, 8, 1e-4, 3);
    require(!wrong_factor.eligible, "nonbinary adaptive factor must fail closed");
    require(wrong_factor.reason ==
                "accepted_contract_requires_binary_split_factor",
            "nonbinary failure reason must name contract");
    const auto invalid = ebrp::evaluateCplexReplicaStructuralSplit(
        0.0, 0.8, -0.1, 0.2, 2, 4, 8, 1e-4, 2);
    require(!invalid.eligible && invalid.reason ==
                "invalid_structural_geometry",
            "out-of-root interval must fail closed");

    const std::vector<ebrp::GiniIntervalGeometry> exact = {
        {0.0, 0.2}, {0.2, 0.4}};
    std::string reason;
    require(ebrp::exactIntervalCoverage({0.0, 0.4}, exact, 1e-12, &reason),
            "touching children must exactly cover parent");
    require(reason == "exact_coverage", "coverage proof must be explicit");
    require(!ebrp::exactIntervalCoverage(
                {0.0, 0.4}, {{0.0, 0.19}, {0.2, 0.4}}, 1e-12, &reason),
            "coverage gap must be rejected");
}

void schedulerChecks() {
    {
        ebrp::ControllingLeafScheduler scheduler(1e-7);
        require(scheduler.addLeaf(leaf("wide", 0.0, 0.4, 0.1)),
                "wide leaf add");
        require(scheduler.addLeaf(leaf("narrow", 0.4, 0.6, 0.1)),
                "narrow leaf add");
        require(scheduler.selectNextCplexReplica().selected_leaf_id == "narrow",
                "smaller width wins equal-bound tie");
    }
    {
        ebrp::ControllingLeafScheduler scheduler(1e-7);
        require(scheduler.addLeaf(leaf("shallow", 0.0, 0.2, 0.1, 2)),
                "shallow leaf add");
        require(scheduler.addLeaf(leaf("deep", 0.2, 0.4, 0.1, 5)),
                "deep leaf add");
        require(scheduler.selectNextCplexReplica().selected_leaf_id == "deep",
                "greater depth wins equal-width tie");
    }
    {
        ebrp::ControllingLeafScheduler scheduler(1e-7);
        auto expensive = leaf("low", 0.0, 0.2, 0.2);
        expensive.exact_solver_attempt_count = 99;
        expensive.cumulative_solver_time_seconds = 9999.0;
        auto cheap = leaf("high", 0.2, 0.4, 0.3);
        require(scheduler.addLeaf(expensive), "effort-heavy leaf add");
        require(scheduler.addLeaf(cheap), "effort-light leaf add");
        require(scheduler.selectNextCplexReplica().selected_leaf_id == "low",
                "mathematical bound dominates all effort state");
    }
    {
        ebrp::ControllingLeafScheduler scheduler(1e-7);
        require(scheduler.addLeaf(leaf("b", 0.0, 0.2, 0.1, 2)),
                "ID b add");
        require(scheduler.addLeaf(leaf("a", 0.0, 0.2, 0.1, 2)),
                "ID a add");
        require(scheduler.selectNextCplexReplica().selected_leaf_id == "a",
                "leaf ID is deterministic final tie breaker");
    }
    {
        ebrp::ControllingLeafScheduler scheduler(1e-7);
        auto parent = leaf("R", 0.0, 0.8, 0.25);
        require(scheduler.addLeaf(parent), "parent add");
        auto left = leaf("R.0", 0.0, 0.4, 0.25, 1);
        auto right = leaf("R.1", 0.4, 0.8, 0.25, 1);
        left.parent_id = right.parent_id = "R";
        left.child_index = 0;
        right.child_index = 1;
        std::string reason;
        require(scheduler.splitLeafAtomically("R", {left, right}, &reason),
                "atomic exact split must succeed");
        require(reason == "accepted_exact_child_coverage",
                "atomic split proof must be explicit");
        require(scheduler.findLeaf("R")->status ==
                    ebrp::ControllingLeafStatus::Replaced,
                "parent must be replaced");
        require(scheduler.findLeaf("R.0")->lower_bound == 0.25 &&
                    scheduler.findLeaf("R.1")->lower_bound == 0.25,
                "children must inherit parent bound");
        require(std::fabs(scheduler.globalLowerBound() - 0.25) < 1e-12,
                "atomic replacement preserves global bound");
        require(scheduler.parentChildCoverageValid(&reason),
                "scheduler coverage audit must pass");
        require(scheduler.mergeValidLowerBound(
                    "R.0", 0.4, "complete_lp", &reason),
                "valid LP bound merge must succeed");
        require(scheduler.leafBoundsMonotone(),
                "leaf bound history must remain monotone");
        require(scheduler.globalBoundMonotone(),
                "global bound history must remain monotone");
        require(scheduler.tightenVerifiedCutoff(0.5, &reason),
                "verified cutoff may tighten");
        require(!scheduler.tightenVerifiedCutoff(0.6, &reason),
                "verified cutoff may never weaken");
    }
}

void certificateAndTerminalChecks() {
    ebrp::ExternalGiniTreeCertificateInput input;
    input.complete_root_coverage = true;
    input.parent_child_coverage_valid = true;
    input.all_relevant_leaves_closed = true;
    input.all_leaf_bounds_valid = true;
    input.global_bound_valid = true;
    input.global_bound_monotone = true;
    input.leaf_bounds_monotone = true;
    input.verified_global_ub = true;
    input.lifecycle_complete = true;
    input.feasibility_consistency_gate = true;
    input.global_lb = 0.5;
    input.verified_ub = 0.5;
    input.tolerance = 1e-7;
    require(ebrp::evaluateExternalGiniTreeCertificate(input).certified,
            "all exact gates and equal bounds must certify");
    input.all_relevant_leaves_closed = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(input).certified,
            "open relevant leaf must reject certificate");
    input.all_relevant_leaves_closed = true;
    input.global_lb = 0.49;
    require(!ebrp::evaluateExternalGiniTreeCertificate(input).certified,
            "positive strict gap must reject certificate");
    input.global_lb = 0.5;
    input.lifecycle_complete = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(input).certified,
            "incomplete lifecycle must reject certificate");

    ebrp::FixedIntervalMipOutcome optimal;
    optimal.attempted = true;
    optimal.available = true;
    optimal.solver_finalization_reached = true;
    optimal.model_fingerprint_matches_request = true;
    optimal.exact_zero_gap_roundtrip = true;
    optimal.feasibility_consistency_gate = true;
    optimal.terminal_mip = true;
    optimal.optimal = true;
    optimal.native_bound_available = true;
    const auto close = ebrp::evaluatePaperTerminalMipDecision(optimal);
    require(close.valid && close.close_leaf,
            "native optimal terminal MIP may close leaf");
    optimal.optimal = false;
    optimal.interrupted = true;
    const auto stop = ebrp::evaluatePaperTerminalMipDecision(optimal);
    require(stop.valid && stop.leave_open_and_stop && !stop.close_leaf,
            "global interruption leaves terminal leaf open and stops");
    optimal.interrupted = false;
    const auto unsupported = ebrp::evaluatePaperTerminalMipDecision(optimal);
    require(!unsupported.valid,
            "unsupported terminal status must fail closed");
}

} // namespace

int main() {
    try {
        geometryChecks();
        schedulerChecks();
        certificateAndTerminalChecks();
        require(checks >= 40, "Round 28 regression gate requires 40 checks");
        std::cout << "ROUND28_CHECKS=" << checks << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round 28 replica regression failure after " << checks
                  << " checks: " << error.what() << "\n";
        return 1;
    }
}
