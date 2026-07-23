#pragma once

#include "ExternalGiniTree.hpp"

#include <string>

namespace ebrp {

struct PaperLpResult {
    bool terminal_valid = false;
    bool optimal = false;
    bool infeasible = false;
    bool bound_available = false;
    double lower_bound = 0.0;
};

struct PaperLpSplitDecision {
    bool valid = false;
    bool should_split = false;
    bool child_infeasibility_trigger = false;
    bool strict_bound_improvement_trigger = false;
    double post_split_lower_bound = 0.0;
    std::string reason = "not_evaluated";
};

PaperLpSplitDecision evaluatePaperLpSplitDecision(
    double parent_lower_bound,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double certificate_tolerance);

struct C5BoundTargetSplitDecision {
    bool valid = false;
    bool split_immediately = false;
    bool run_parent_bound_target_phase = false;
    bool decline_split_and_solve_parent = false;
    bool child_infeasibility_trigger = false;
    double post_split_lower_bound = 0.0;
    double normalized_disjunction_gain = 0.0;
    double parent_native_bound_target = 0.0;
    std::string reason = "not_evaluated";
};

C5BoundTargetSplitDecision evaluateC5BoundTargetSplitDecision(
    double parent_lower_bound,
    double verified_upper_bound,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double normalized_split_threshold,
    double certificate_tolerance);

struct PaperTerminalMipDecision {
    bool valid = false;
    bool close_leaf = false;
    bool leave_open_and_stop = false;
    std::string reason = "not_evaluated";
};

PaperTerminalMipDecision evaluatePaperTerminalMipDecision(
    const FixedIntervalMipOutcome& outcome);

SolveResult solvePaperExternalGiniTree(const Instance& instance,
                                       const SolveOptions& options,
                                       const SolveResult& verified_seed,
                                       double root_gamma_L,
                                       double root_gamma_U);

} // namespace ebrp
