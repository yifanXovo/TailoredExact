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
