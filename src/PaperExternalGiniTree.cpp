#include "PaperExternalGiniTree.hpp"

#include "CanonicalCompactModel.hpp"
#include "ConnectivityFlow.hpp"
#include "ControllingLeafScheduler.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"
#include "ProcessPhaseLedger.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <sstream>
#include <unordered_map>
#include <vector>

namespace ebrp {
namespace {

using PaperClock = std::chrono::steady_clock;

const std::vector<std::string> kPaperGlobalFamilies = {
    "inventory_conservation",
    "movement_reachability_domains",
    "visit_inventory_linking",
    "global_handling_capacity",
    "support_duration",
    "transfer_compat"
};

const std::vector<std::string> kPaperIntervalFamilies = {
    "direct_gini_cap_floor",
    "interval_tight_mccormick",
    "objective_estimator_cutoff",
    "penalty_lb_closure",
    "gini_spread",
    "required_movement",
    "low_gini_centering",
    "variable_s_centering",
    "sp_product_estimator"
};

std::string join(const std::vector<std::string>& values) {
    std::ostringstream out;
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) out << ';';
        out << values[index];
    }
    return out.str();
}

std::string joinDoubles(const std::vector<double>& values) {
    std::ostringstream out;
    out << std::setprecision(17);
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) out << ';';
        out << values[index];
    }
    return out.str();
}

std::string joinIntervals(
    const std::vector<GiniIntervalGeometry>& intervals) {
    std::ostringstream out;
    out << std::setprecision(17);
    for (std::size_t index = 0; index < intervals.size(); ++index) {
        if (index) out << ';';
        out << '[' << intervals[index].lower << ',' << intervals[index].upper
            << ']';
    }
    return out.str();
}

std::string csvField(const std::string& text) {
    std::string escaped;
    escaped.reserve(text.size() + 2);
    escaped.push_back('"');
    for (char ch : text) {
        if (ch == '"') escaped.push_back('"');
        escaped.push_back(ch);
    }
    escaped.push_back('"');
    return escaped;
}

struct PaperLeafRuntime {
    bool artifact_ready = false;
    CanonicalCompactModelArtifact artifact;
    bool lp_complete = false;
    PaperLpResult lp;
    bool terminal_mip_started = false;
    bool c5_partial_target_started = false;
    bool c5_partial_target_reached = false;
    bool c5_split_pending = false;
    double c5_native_target = 0.0;
    std::vector<ControllingLeaf> c5_pending_children;
    int c6_native_phase_count = 0;
    bool c6_frontier_milestone_reached = false;
    bool c6_children_ready = false;
    std::vector<ControllingLeaf> c6_cached_children;
};

constexpr double kRound30C5NormalizedSplitThreshold = 0.01;
constexpr double kRound31C6NormalizedSplitThreshold = 0.01;

bool round29C4FrozenOptionsValid(const SolveOptions& options,
                                std::string& reason) {
    if (options.external_gini_lifecycle !=
        "round29-same-leaf-in-memory-model") {
        reason = "c4_requires_round29_same_leaf_in_memory_model_lifecycle";
        return false;
    }
    if (options.primal_heuristic != "hga-tgbc" ||
        options.primal_heuristic_seed != 20260626u ||
        options.primal_heuristic_stop != "generation-stagnation" ||
        options.primal_heuristic_no_improve_generations != 2000 ||
        options.exact_phase_local_redecode_repair) {
        reason =
            "c4_requires_primary_generation_hga_seed20260626_stagnation2000_"
            "and_no_local_redecode";
        return false;
    }
    if (options.frontier_intervals != 4 ||
        !options.frontier_adaptive_split ||
        options.frontier_adaptive_max_depth != 8 ||
        std::fabs(options.frontier_adaptive_min_width - 1e-4) > 1e-12 ||
        options.frontier_adaptive_split_factor != 2) {
        reason = "c4_geometry_not_frozen_4_binary_depth8_width1e-4";
        return false;
    }
    if (options.global_gini_tree_child_estimate_mode != "parent-copy" ||
        options.global_gini_tree_row_attachment_mode !=
            "full-inherited-pack" ||
        options.global_gini_tree_row_timing_mode != "deferred" ||
        options.global_gini_tree_native_mip_start ||
        options.global_gini_tree_presolve != "off" ||
        options.global_gini_tree_search != "traditional") {
        reason = "c4_static_row_or_s0_f0_contract_mismatch";
        return false;
    }
    reason = "accepted_round29_c4_frozen_contract";
    return true;
}

bool round30C5FrozenOptionsValid(const SolveOptions& options,
                                std::string& reason) {
    if (options.external_gini_lifecycle !=
        "round30-same-leaf-bound-target") {
        reason = "c5_requires_round30_same_leaf_bound_target_lifecycle";
        return false;
    }
    if (options.primal_heuristic != "hga-tgbc" ||
        options.primal_heuristic_seed != 20260626u ||
        options.primal_heuristic_stop != "generation-stagnation" ||
        options.primal_heuristic_no_improve_generations != 2000 ||
        options.exact_phase_local_redecode_repair) {
        reason =
            "c5_requires_primary_generation_hga_seed20260626_stagnation2000_"
            "and_no_local_redecode";
        return false;
    }
    if (options.frontier_intervals != 4 ||
        !options.frontier_adaptive_split ||
        options.frontier_adaptive_max_depth != 8 ||
        std::fabs(options.frontier_adaptive_min_width - 1e-4) > 1e-12 ||
        options.frontier_adaptive_split_factor != 2) {
        reason = "c5_geometry_not_frozen_4_binary_depth8_width1e-4";
        return false;
    }
    if (options.global_gini_tree_child_estimate_mode != "parent-copy" ||
        options.global_gini_tree_row_attachment_mode !=
            "full-inherited-pack" ||
        options.global_gini_tree_row_timing_mode != "deferred" ||
        options.global_gini_tree_native_mip_start ||
        options.global_gini_tree_presolve != "off" ||
        options.global_gini_tree_search != "traditional") {
        reason = "c5_static_row_or_s0_f0_contract_mismatch";
        return false;
    }
    reason = "accepted_round30_c5_frozen_contract";
    return true;
}

bool round31C6FrozenOptionsValid(const SolveOptions& options,
                                std::string& reason) {
    if (options.external_gini_lifecycle !=
        "round31-open-native-bounded") {
        reason = "c6_requires_round31_open_native_bounded_lifecycle";
        return false;
    }
    const bool hga_full =
        options.round34_c6_startup_variant == "hga-full" &&
        options.primal_heuristic == "hga-tgbc" &&
        options.primal_heuristic_seed == 20260626u &&
        options.primal_heuristic_stop == "generation-stagnation" &&
        options.primal_heuristic_no_improve_generations == 2000;
    const bool hga_light =
        options.round34_c6_startup_variant == "hga-light-1000" &&
        options.primal_heuristic == "hga-tgbc" &&
        options.primal_heuristic_seed == 20260626u &&
        options.primal_heuristic_stop == "generation-stagnation" &&
        options.primal_heuristic_no_improve_generations == 1000;
    const bool simple_start =
        options.round34_c6_startup_variant == "simple-start" &&
        options.primal_heuristic == "greedy" &&
        options.primal_heuristic_seed == 20260626u &&
        options.primal_heuristic_no_improve_generations == 2000;
    if ((!hga_full && !hga_light && !simple_start) ||
        options.exact_phase_local_redecode_repair) {
        reason = "c6_startup_variant_contract_mismatch_or_local_redecode";
        return false;
    }
    const std::string& causal = options.round36_c6_causal_arm;
    const std::string& normalization =
        options.round36_c6_split_normalization;
    const bool causal_contract_valid =
        (causal == "off" && normalization == "proof") ||
        (causal == "hh" && hga_full && normalization == "proof") ||
        (causal == "ss" && simple_start && normalization == "proof") ||
        (causal == "bw-p" && hga_full && normalization == "proof") ||
        (causal == "bw-a" && hga_full && normalization == "anchor");
    if (!causal_contract_valid) {
        reason = "c6_round36_causal_arm_or_normalization_contract_mismatch";
        return false;
    }
    const std::string& geometry_policy =
        options.round37_c6_geometry_policy;
    const bool geometry_policy_valid = geometry_policy == "off" ||
        (geometry_policy == "pilot-weakest-prefine" && hga_full &&
         causal == "off" && normalization == "proof");
    if (!geometry_policy_valid) {
        reason = "c6_round37_geometry_policy_contract_mismatch";
        return false;
    }
    const std::string& frontier_policy =
        options.round38_c6_frontier_policy;
    const bool frontier_policy_valid = frontier_policy == "off" ||
        (frontier_policy == "pilot-next-frontier-complete" && hga_full &&
         causal == "off" && normalization == "proof" &&
         geometry_policy == "off");
    if (!frontier_policy_valid) {
        reason = "c6_round38_frontier_policy_contract_mismatch";
        return false;
    }
    if (options.frontier_intervals != 4 ||
        !options.frontier_adaptive_split ||
        options.frontier_adaptive_max_depth != 8 ||
        std::fabs(options.frontier_adaptive_min_width - 1e-4) > 1e-12 ||
        options.frontier_adaptive_split_factor != 2) {
        reason = "c6_geometry_not_frozen_4_binary_depth8_width1e-4";
        return false;
    }
    if (options.global_gini_tree_child_estimate_mode != "parent-copy" ||
        options.global_gini_tree_row_attachment_mode !=
            "full-inherited-pack" ||
        options.global_gini_tree_row_timing_mode != "deferred" ||
        options.global_gini_tree_native_mip_start ||
        options.global_gini_tree_presolve != "off" ||
        options.global_gini_tree_search != "traditional") {
        reason = "c6_static_row_or_s0_f0_contract_mismatch";
        return false;
    }
    reason = "accepted_round31_c6_frozen_exact_contract_with_" +
        options.round34_c6_startup_variant + "_round36_" + causal +
        "_round37_" + geometry_policy;
    return true;
}

void copyPaperBackendStats(SolveResult& result,
                           const FixedIntervalMipBackendStats& stats) {
    result.external_gini_tree_environment_count = stats.environment_count;
    result.external_gini_tree_model_count = stats.model_count;
    result.external_gini_tree_model_read_count = stats.model_read_count;
    result.external_gini_tree_optimize_count = stats.optimize_count;
    result.external_gini_tree_attempt_count = stats.optimize_count;
    result.external_gini_tree_lp_relaxation_count =
        stats.lp_relaxation_optimize_count;
    result.external_gini_tree_lp_optimize_count =
        stats.lp_relaxation_optimize_count;
    result.external_gini_tree_partial_mip_optimize_count =
        stats.partial_bound_target_mip_optimize_count;
    result.external_gini_tree_partial_mip_bound_event_count =
        stats.native_bound_event_count;
    result.external_gini_tree_partial_mip_target_reached_count =
        stats.native_bound_target_reached_count;
    result.external_gini_tree_terminal_mip_optimize_count =
        stats.terminal_mip_optimize_count;
    result.external_gini_tree_model_free_count = stats.model_free_count;
    result.external_gini_tree_environment_free_count =
        stats.environment_free_count;
    result.external_gini_tree_same_leaf_resume_count =
        stats.same_leaf_resume_count;
    result.external_gini_tree_fresh_restart_count = stats.fresh_restart_count;
    result.external_gini_tree_child_restart_count = stats.child_restart_count;
    result.external_gini_tree_reset_call_count = stats.reset_call_count;
    result.external_gini_tree_presolve_execution_count =
        stats.presolve_execution_count;
    result.external_gini_tree_root_relaxation_execution_count =
        stats.root_relaxation_execution_count;
    result.external_gini_tree_in_memory_model_reuse_count =
        stats.in_memory_model_reuse_count;
    result.external_gini_tree_explicit_leaf_model_discard_count =
        stats.explicit_leaf_model_discard_count;
    result.external_gini_tree_integer_domain_restore_count =
        stats.integer_domain_restore_count;
    result.external_gini_tree_basis_available_count =
        stats.basis_available_count;
    result.external_gini_tree_basis_mapped_count = stats.basis_mapped_count;
    result.external_gini_tree_basis_submitted_count =
        stats.basis_submitted_count;
    result.external_gini_tree_basis_accepted_count =
        stats.basis_accepted_count;
    result.external_gini_tree_basis_rejected_count =
        stats.basis_rejected_count;
    result.external_gini_tree_model_read_seconds =
        stats.cumulative_model_read_seconds;
    result.external_gini_tree_solver_seconds =
        stats.cumulative_solver_runtime_seconds;
    result.external_gini_tree_work = stats.cumulative_work;
    result.external_gini_tree_lp_work = stats.cumulative_lp_work;
    result.external_gini_tree_partial_mip_work =
        stats.cumulative_partial_bound_target_mip_work;
    result.external_gini_tree_terminal_mip_work =
        stats.cumulative_terminal_mip_work;
    result.external_gini_tree_nodes = stats.cumulative_nodes;
    result.external_gini_tree_simplex_iterations =
        stats.cumulative_simplex_iterations;
    result.external_gini_tree_barrier_iterations =
        stats.cumulative_barrier_iterations;
    result.external_gini_tree_peak_memory_gb = stats.peak_memory_gb;
}

} // namespace

PaperLpSplitDecision evaluatePaperLpSplitDecision(
    double parent_lower_bound,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double certificate_tolerance) {
    PaperLpSplitDecision decision;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if (!std::isfinite(parent_lower_bound)) {
        decision.reason = "nonfinite_parent_lp_bound";
        return decision;
    }
    auto validChild = [](const PaperLpResult& child) {
        return child.terminal_valid && (child.infeasible ||
            (child.optimal && child.bound_available &&
             std::isfinite(child.lower_bound)));
    };
    if (!validChild(left) || !validChild(right)) {
        decision.reason = "child_lp_not_terminal_valid";
        return decision;
    }
    decision.valid = true;
    decision.child_infeasibility_trigger = left.infeasible || right.infeasible;
    double post = std::numeric_limits<double>::infinity();
    if (!left.infeasible) post = std::min(post, left.lower_bound);
    if (!right.infeasible) post = std::min(post, right.lower_bound);
    decision.post_split_lower_bound = post;
    decision.strict_bound_improvement_trigger =
        std::isfinite(post) && post > parent_lower_bound + tolerance;
    decision.should_split = decision.child_infeasibility_trigger ||
        decision.strict_bound_improvement_trigger;
    decision.reason = decision.child_infeasibility_trigger
        ? "child_lp_infeasible"
        : (decision.strict_bound_improvement_trigger
            ? "strict_child_lp_bound_improvement"
            : "no_certified_one_level_lp_benefit");
    return decision;
}

C5BoundTargetSplitDecision evaluateC5BoundTargetSplitDecision(
    double parent_lower_bound,
    double verified_upper_bound,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double normalized_split_threshold,
    double certificate_tolerance) {
    C5BoundTargetSplitDecision decision;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if (!std::isfinite(parent_lower_bound) ||
        !std::isfinite(verified_upper_bound) ||
        verified_upper_bound + tolerance < parent_lower_bound ||
        !std::isfinite(normalized_split_threshold) ||
        normalized_split_threshold <= 0.0 ||
        normalized_split_threshold >= 1.0) {
        decision.reason = "invalid_c5_bound_target_inputs";
        return decision;
    }
    auto validChild = [](const PaperLpResult& child) {
        return child.terminal_valid && (child.infeasible ||
            (child.optimal && child.bound_available &&
             std::isfinite(child.lower_bound)));
    };
    if (!validChild(left) || !validChild(right)) {
        decision.reason = "child_lp_not_terminal_valid";
        return decision;
    }
    decision.valid = true;
    decision.child_infeasibility_trigger = left.infeasible || right.infeasible;
    double post = std::numeric_limits<double>::infinity();
    if (!left.infeasible) post = std::min(post, left.lower_bound);
    if (!right.infeasible) post = std::min(post, right.lower_bound);
    decision.post_split_lower_bound = post;
    if (decision.child_infeasibility_trigger) {
        decision.split_immediately = true;
        decision.normalized_disjunction_gain =
            std::numeric_limits<double>::infinity();
        decision.reason = "complete_child_lp_infeasibility";
        return decision;
    }
    const double gain = post - parent_lower_bound;
    if (gain <= tolerance) {
        decision.decline_split_and_solve_parent = true;
        decision.reason = "no_strict_child_disjunction_gain";
        return decision;
    }
    const double proof_gap = std::max(
        verified_upper_bound - parent_lower_bound,
        std::max(tolerance, 1e-12));
    decision.normalized_disjunction_gain = gain / proof_gap;
    if (decision.normalized_disjunction_gain + 1e-15 >=
        normalized_split_threshold) {
        decision.split_immediately = true;
        decision.reason = "normalized_child_disjunction_gain_reaches_rho";
    } else {
        decision.run_parent_bound_target_phase = true;
        decision.parent_native_bound_target = post;
        decision.reason =
            "small_positive_disjunction_gain_requires_parent_native_target";
    }
    return decision;
}

C6FrontierDecision evaluateC6FrontierDecision(
    double current_leaf_bound,
    const std::vector<double>& other_relevant_leaf_bounds,
    double certificate_tolerance,
    bool frontier_milestone_already_reached) {
    C6FrontierDecision decision;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if (!std::isfinite(current_leaf_bound)) {
        decision.reason = "nonfinite_current_leaf_bound";
        return decision;
    }
    double next_strict_bound = std::numeric_limits<double>::infinity();
    for (double bound : other_relevant_leaf_bounds) {
        if (!std::isfinite(bound)) {
            decision.reason = "nonfinite_other_relevant_leaf_bound";
            return decision;
        }
        if (bound + tolerance < current_leaf_bound) {
            decision.valid = true;
            decision.requeue_without_native = true;
            decision.reason = "selected_leaf_no_longer_controlling";
            return decision;
        }
        if (bound > current_leaf_bound + tolerance) {
            next_strict_bound = std::min(next_strict_bound, bound);
        }
    }
    decision.valid = true;
    if (frontier_milestone_already_reached) {
        decision.allow_child_lookahead = true;
        decision.reason =
            "frontier_milestone_already_reached_lazy_child_recheck";
        return decision;
    }
    if (std::isfinite(next_strict_bound)) {
        decision.run_native_target = true;
        decision.native_bound_target = next_strict_bound;
        decision.reason = "next_strict_frontier_bound_target";
    } else {
        decision.allow_child_lookahead = true;
        decision.reason =
            other_relevant_leaf_bounds.empty()
                ? "single_relevant_leaf_no_frontier_target"
                : "lowest_frontier_plateau_has_no_higher_target";
    }
    return decision;
}

C6CurrentSplitDecision evaluateC6CurrentSplitDecision(
    double current_parent_bound,
    double verified_upper_bound,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double normalized_split_threshold,
    double certificate_tolerance) {
    return evaluateC6CurrentSplitDecision(
        current_parent_bound, verified_upper_bound, verified_upper_bound,
        "proof", left, right, normalized_split_threshold,
        certificate_tolerance);
}

C6CurrentSplitDecision evaluateC6CurrentSplitDecision(
    double current_parent_bound,
    double proof_upper_bound,
    double anchor_upper_bound,
    const std::string& normalization_source,
    const PaperLpResult& left,
    const PaperLpResult& right,
    double normalized_split_threshold,
    double certificate_tolerance) {
    C6CurrentSplitDecision decision;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if ((normalization_source != "proof" &&
         normalization_source != "anchor") ||
        !std::isfinite(proof_upper_bound) ||
        !std::isfinite(anchor_upper_bound) ||
        anchor_upper_bound + tolerance < proof_upper_bound) {
        decision.reason = "invalid_c6_normalization_configuration";
        return decision;
    }
    const double normalization_upper_bound =
        normalization_source == "anchor"
            ? anchor_upper_bound : proof_upper_bound;
    const C5BoundTargetSplitDecision base =
        evaluateC5BoundTargetSplitDecision(
            current_parent_bound, normalization_upper_bound, left, right,
            normalized_split_threshold, certificate_tolerance);
    if (!base.valid) {
        decision.reason = "invalid_current_split_inputs:" + base.reason;
        return decision;
    }
    decision.valid = true;
    decision.child_infeasibility_trigger =
        base.child_infeasibility_trigger;
    decision.post_split_lower_bound = base.post_split_lower_bound;
    decision.normalized_disjunction_gain =
        base.normalized_disjunction_gain;
    decision.b_plus = base.post_split_lower_bound;
    decision.normalization_source = normalization_source;
    decision.normalization_upper_bound = normalization_upper_bound;
    if (base.child_infeasibility_trigger) {
        decision.eta_proof = std::numeric_limits<double>::infinity();
        decision.eta_anchor = std::numeric_limits<double>::infinity();
    } else {
        const double gain = std::max(
            0.0, base.post_split_lower_bound - current_parent_bound);
        decision.eta_proof = gain / std::max(
            1e-7, proof_upper_bound - current_parent_bound);
        decision.eta_anchor = gain / std::max(
            1e-7, anchor_upper_bound - current_parent_bound);
    }
    if (base.split_immediately) {
        decision.split_immediately = true;
        decision.reason = base.child_infeasibility_trigger
            ? "current_complete_child_infeasibility"
            : "current_normalized_child_gain_reaches_rho";
    } else if (base.run_parent_bound_target_phase) {
        decision.run_child_bound_target = true;
        decision.child_bound_target = base.parent_native_bound_target;
        decision.reason = "current_small_child_gain_target";
    } else if (base.decline_split_and_solve_parent) {
        decision.launch_exact_closure = true;
        decision.reason = "current_child_gain_not_strict";
    } else {
        decision.valid = false;
        decision.reason = "unclassified_current_split_decision";
    }
    return decision;
}

PaperTerminalMipDecision evaluatePaperTerminalMipDecision(
    const FixedIntervalMipOutcome& outcome) {
    PaperTerminalMipDecision decision;
    if (!outcome.attempted || !outcome.available ||
        !outcome.solver_finalization_reached ||
        !outcome.model_fingerprint_matches_request ||
        !outcome.exact_zero_gap_roundtrip ||
        !outcome.feasibility_consistency_gate || !outcome.terminal_mip) {
        decision.reason = "terminal_mip_engineering_gate_failed";
        return decision;
    }
    if (outcome.optimal && !outcome.native_bound_available) {
        decision.reason = "optimal_terminal_mip_missing_native_bound";
        return decision;
    }
    if (outcome.optimal || outcome.infeasible) {
        decision.valid = true;
        decision.close_leaf = true;
        decision.reason = outcome.infeasible
            ? "native_terminal_mip_infeasible"
            : "native_terminal_mip_optimal";
        return decision;
    }
    if (outcome.interrupted) {
        decision.valid = true;
        decision.leave_open_and_stop = true;
        decision.reason = "global_deadline_interrupted_terminal_mip";
        return decision;
    }
    decision.reason = "unsupported_terminal_mip_status";
    return decision;
}

SolveResult solvePaperExternalGiniTree(const Instance& instance,
                                       const SolveOptions& options,
                                       const SolveResult& verified_seed,
                                       double root_gamma_L,
                                       double root_gamma_U) {
    const auto started = PaperClock::now();
    auto elapsedTelemetry = [&]() {
        return std::chrono::duration<double>(
            PaperClock::now() - started).count();
    };
    auto globalDeadlineRemaining = [&]() {
        if (processDeadlineConfigured(options)) {
            return processWorkRemainingSeconds(options);
        }
        return options.solve_time_limit > 0.0
            ? options.solve_time_limit - elapsedTelemetry()
            : std::numeric_limits<double>::max();
    };

    const bool c4_incremental =
        options.external_gini_scheduling ==
            "round29-bound-gain-incremental";
    const bool c5_bound_target =
        options.external_gini_scheduling ==
            "round30-dual-bound-target";
    const bool c6_nonblocking =
        options.external_gini_scheduling ==
            "round31-nonblocking-native-bound";
    const bool round37_pilot_prefine = c6_nonblocking &&
        options.round37_c6_geometry_policy == "pilot-weakest-prefine";
    const bool round38_frontier_pilot = c6_nonblocking &&
        options.round38_c6_frontier_policy ==
            "pilot-next-frontier-complete";
    const bool round36_causal = c6_nonblocking &&
        options.round36_c6_causal_arm != "off";
    const double proof_incumbent_launch = verified_seed.objective;
    const double decomposition_anchor_launch = round36_causal
        ? verified_seed.round36_decomposition_anchor_launch
        : proof_incumbent_launch;
    const double gini_max_possible = instance.V > 0
        ? static_cast<double>(instance.V - 1) /
            static_cast<double>(instance.V)
        : 1.0;
    const double anchor_grid_upper = std::min(
        decomposition_anchor_launch, gini_max_possible);
    const AnchorGridDecomposition causal_grid = round36_causal
        ? makeProofRelevantAnchorGrid(
              root_gamma_L, root_gamma_U, anchor_grid_upper,
              options.frontier_intervals, 1e-7)
        : AnchorGridDecomposition{};
    const bool incremental_model_reuse =
        c4_incremental || c5_bound_target || c6_nonblocking;
    SolveResult result = verified_seed;
    result.exact_phase_started = true;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "external-gini-tree";
    result.certificate_scope = "original_global_gini_external_tree";
    result.external_gini_tree_attempted = true;
    result.external_gini_tree_backend = options.external_gini_backend;
    result.external_gini_tree_lifecycle = c6_nonblocking
        ? "round31-open-native-bounded"
        : (c5_bound_target
            ? "round30-same-leaf-bound-target"
        : (c4_incremental
            ? "round29-same-leaf-in-memory-model"
            : "fresh-per-paper-event"));
    result.external_gini_tree_scheduling =
        options.external_gini_scheduling;
    result.external_gini_tree_startup_variant = c6_nonblocking
        ? options.round34_c6_startup_variant : "not_applicable";
    result.round36_c6_causal_arm = options.round36_c6_causal_arm;
    result.round36_c6_split_normalization =
        options.round36_c6_split_normalization;
    result.round37_c6_geometry_policy =
        options.round37_c6_geometry_policy;
    result.round38_c6_frontier_policy =
        options.round38_c6_frontier_policy;
    result.round36_proof_incumbent_launch = proof_incumbent_launch;
    result.round36_decomposition_anchor_launch =
        decomposition_anchor_launch;
    result.round36_anchor_safety_valid = !round36_causal ||
        decomposition_anchor_launch + 1e-7 >= proof_incumbent_launch;
    result.external_gini_tree_root_gamma_L = root_gamma_L;
    result.external_gini_tree_root_gamma_U = root_gamma_U;
    result.external_gini_tree_proof_relevant_gamma_upper = root_gamma_U;
    result.external_gini_tree_anchor_grid_gamma_upper = anchor_grid_upper;
    result.external_gini_tree_verified_upper_bound = verified_seed.objective;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason = "paper_tree_not_finalized";
    result.status = c6_nonblocking
        ? "round31_c6_external_gini_tree_running"
        : (c5_bound_target
            ? "round30_c5_external_gini_tree_running"
        : (c4_incremental
            ? "round29_c4_external_gini_tree_running"
            : "paper_external_gini_tree_running"));
    if (incremental_model_reuse) {
        result.external_gini_tree_algorithm_arm = c6_nonblocking
            ? (round37_pilot_prefine
                ? "R37-PILOT-WEAKEST-PREFINE"
                : (round36_causal
                ? "R36-" + options.round36_c6_causal_arm
                : "C6-CANDIDATE"))
            : (c5_bound_target ? "C5-CANDIDATE" : "C4-CANDIDATE");
        result.external_gini_tree_global_row_family_count =
            static_cast<long long>(kPaperGlobalFamilies.size());
        result.external_gini_tree_interval_row_family_count =
            static_cast<long long>(kPaperIntervalFamilies.size());
        result.external_gini_tree_global_row_families =
            join(kPaperGlobalFamilies);
        result.external_gini_tree_interval_row_families =
            join(kPaperIntervalFamilies);
        result.external_gini_tree_child_lookahead_required =
            !c6_nonblocking || round37_pilot_prefine;
        result.external_gini_tree_structural_split_unconditional = false;
        result.external_gini_tree_internal_budget_scheduling = false;
        result.external_gini_tree_native_tree_reuse_claimed = false;
        result.external_gini_tree_warm_start_enabled = false;
        result.external_gini_tree_selector_variable_count = 0;
        result.external_gini_tree_contract_initial_interval_count = 4;
        result.external_gini_tree_contract_adaptive_max_depth = 8;
        result.external_gini_tree_contract_split_factor = 2;
        result.external_gini_tree_contract_minimum_width = 1e-4;
        result.external_gini_tree_certificate_tolerance = 1e-7;
        result.external_gini_tree_best_bound_tie_rule =
            "lower_bound,lower_endpoint,upper_endpoint,leaf_id";
        result.external_gini_tree_implementation_boundary = c6_nonblocking
            ? (round37_pilot_prefine
              ? "complete all four initial LPs; select the weakest open cell "
                "by LP bound with structural geometry ties; perform exactly "
                "one complete-child midpoint pre-refinement; then resume the "
                "unchanged C6 strict-frontier, target, split, and closure path"
              : "complete parent LP then parameter-free next-strict-frontier "
              "native-bound targets; lazy complete child LPs only at the "
              "highest active frontier plateau; current rho split rule; "
              "target attainment retains and requeues the open parent; "
              "same-leaf model object only; no LP basis or native-tree "
              "continuation claim")
            : (c5_bound_target
            ? "complete parent/child LPs plus normalized disjunction rule; "
              "small positive gains trigger a backend-certified parent "
              "native-bound target before delayed atomic split; same-leaf "
              "model object only; no LP basis or native-tree continuation claim"
            : "complete parent and child LP benefit rule with same-leaf "
              "in-memory Gurobi model retention; integer domain restored "
              "before exact parent MIP; no LP basis or native tree reuse claim");
    }

    const bool seed_valid =
        verified_seed.verification.original_solution_feasible &&
        verified_seed.verification.original_objective_recomputed &&
        verified_seed.verification.errors.empty() &&
        std::isfinite(verified_seed.objective);
    std::string c4_contract_reason;
    const bool c4_contract_valid = !c4_incremental ||
        round29C4FrozenOptionsValid(options, c4_contract_reason);
    std::string c5_contract_reason;
    const bool c5_contract_valid = !c5_bound_target ||
        round30C5FrozenOptionsValid(options, c5_contract_reason);
    std::string c6_contract_reason;
    const bool c6_contract_valid = !c6_nonblocking ||
        round31C6FrozenOptionsValid(options, c6_contract_reason);
    const bool round36_seed_contract_valid = !round36_causal ||
        (round36ProofAnchorLaunchContractValid(
             verified_seed.round36_anchor_safety_valid,
             verified_seed.round36_proof_incumbent_launch,
             proof_incumbent_launch,
             decomposition_anchor_launch,
             1e-7) &&
         causal_grid.valid);
    if (!seed_valid || options.external_gini_backend != "gurobi" ||
        options.external_gini_warm_start || root_gamma_L < -1e-12 ||
        root_gamma_U < root_gamma_L - 1e-12 ||
        !verified_seed.frontier_covers_all_improving_gini_values ||
        !c4_contract_valid || !c5_contract_valid ||
        !c6_contract_valid || !round36_seed_contract_valid) {
        result.status = "paper_external_gini_tree_invalid_configuration";
        result.external_gini_tree_failure_reason = !seed_valid
            ? "same_run_seed_not_verified"
            : (options.external_gini_backend != "gurobi"
                ? "paper_lp_event_path_requires_gurobi"
                : (options.external_gini_warm_start
                    ? "paper_lp_event_path_forbids_warm_start"
                    : (!c4_contract_valid
                        ? c4_contract_reason
                        : (!c5_contract_valid
                            ? c5_contract_reason
                            : (!c6_contract_valid
                                ? c6_contract_reason
                                : (!round36_seed_contract_valid
                                    ? "round36_unsafe_or_unverified_anchor_grid"
                                    : "incomplete_or_invalid_root_range"))))));
        return result;
    }

    const ConnectivityFlowVariantResolution flow_resolution =
        resolveConnectivityFlowVariant(
            options.global_gini_tree_root_connectivity_flow,
            options.global_gini_tree_root_connectivity_flow_variant);
    const ConnectivityFlowCounts flow_counts = flow_resolution.valid
        ? connectivityFlowTheoreticalCounts(
              flow_resolution.variant, instance.V, instance.M)
        : ConnectivityFlowCounts{};
    if (!flow_resolution.valid || !flow_counts.valid ||
        (incremental_model_reuse &&
         flow_resolution.resolved != "round20-current")) {
        result.status = "paper_external_gini_tree_invalid_connectivity";
        result.external_gini_tree_failure_reason = !flow_resolution.valid
            ? flow_resolution.failure_reason
            : (!flow_counts.valid
                ? flow_counts.failure_reason
                : (c6_nonblocking
                    ? "c6_requires_f0_round20_current_connectivity"
                    : (c5_bound_target
                    ? "c5_requires_f0_round20_current_connectivity"
                    : "c4_requires_f0_round20_current_connectivity")));
        return result;
    }
    result.global_gini_tree_root_connectivity_flow_variant_requested =
        flow_resolution.requested;
    result.global_gini_tree_root_connectivity_flow_variant_resolved =
        flow_resolution.resolved;
    result.global_gini_tree_connectivity_flow_columns = flow_counts.columns;
    result.global_gini_tree_connectivity_flow_total_rows =
        flow_counts.total_rows;
    result.global_gini_tree_connectivity_flow_total_nonzeros =
        flow_counts.total_nonzeros;
    recordProcessPhase(
        options, "connectivity_flow_preparation_complete", "complete",
        "variant=" + flow_resolution.resolved);

    std::unique_ptr<FixedIntervalMipBackend> backend =
        makeGurobiFixedIntervalBackend(instance, options);
    recordProcessPhase(
        options, "external_backend_creation", backend ? "complete" : "failed",
        std::string("backend=gurobi;arm=") +
            (c6_nonblocking
                ? "C6-CANDIDATE"
                : (c5_bound_target
                ? "C5-CANDIDATE"
                : (c4_incremental ? "C4-CANDIDATE" : "C2-PAPER"))));
    if (!backend) {
        result.status = "paper_external_gini_tree_backend_invalid";
        result.external_gini_tree_failure_reason = "gurobi_backend_factory_failed";
        return result;
    }
    const FixedIntervalMipCapabilities capabilities = backend->capabilities();
    result.external_gini_tree_available = capabilities.available;
    if (!capabilities.available) {
        result.status = "paper_external_gini_tree_backend_unavailable";
        result.external_gini_tree_failure_reason = capabilities.failure_reason;
        return result;
    }

    const auto stamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        PaperClock::now().time_since_epoch()).count();
    const std::filesystem::path artifact_dir =
        options.external_gini_artifact_dir.empty()
            ? std::filesystem::path("results") / "paper_external_gini_work" /
                (std::filesystem::path(instance.name).stem().string() + "_" +
                 std::to_string(stamp))
            : std::filesystem::path(options.external_gini_artifact_dir);
    std::filesystem::create_directories(artifact_dir / "models");
    std::filesystem::create_directories(artifact_dir / "native_logs");
    recordProcessPhase(
        options, "external_artifact_directory_creation", "complete",
        artifact_dir.string());
    const auto event_path = artifact_dir / "paper_tree_events.csv";
    const auto leaf_path = artifact_dir / "paper_leaf_ledger.csv";
    const auto optimize_path = artifact_dir / "paper_optimize_ledger.csv";
    const auto lp_path = artifact_dir / "lp_status_ledger.csv";
    const auto bounds_path = artifact_dir / "parent_child_bound_ledger.csv";
    const auto split_path = artifact_dir / "split_decision_ledger.csv";
    const auto global_bound_path = artifact_dir / "global_bound_trace.csv";
    const auto native_target_path =
        artifact_dir / "native_target_ledger.csv";
    const auto initial_decomposition_path =
        artifact_dir / "initial_decomposition_ledger.csv";
    result.external_gini_tree_event_trace_path = event_path.string();
    result.external_gini_tree_leaf_ledger_path = leaf_path.string();
    result.external_gini_tree_optimize_ledger_path = optimize_path.string();
    result.external_gini_tree_lp_status_ledger_path = lp_path.string();
    result.external_gini_tree_parent_child_bound_ledger_path =
        bounds_path.string();
    result.external_gini_tree_split_decision_ledger_path = split_path.string();
    result.external_gini_tree_global_bound_trace_path =
        global_bound_path.string();
    result.external_gini_tree_native_target_ledger_path =
        native_target_path.string();
    result.external_gini_tree_initial_decomposition_ledger_path =
        initial_decomposition_path.string();
    std::ofstream events(event_path), optimize(optimize_path), lp_ledger(lp_path),
        bound_ledger(bounds_path), split_ledger(split_path),
        global_trace(global_bound_path), native_targets(native_target_path),
        initial_decomposition(initial_decomposition_path);
    // These ledgers are evidence, not presentation-only logs.  Preserve the
    // full round-trip precision of every double from the first row onward so
    // aggregate Work, bounds, targets, and timestamps can be reconstructed
    // without the default iostream six-significant-digit loss.
    events << std::setprecision(17);
    optimize << std::setprecision(17);
    lp_ledger << std::setprecision(17);
    bound_ledger << std::setprecision(17);
    split_ledger << std::setprecision(17);
    global_trace << std::setprecision(17);
    native_targets << std::setprecision(17);
    initial_decomposition << std::setprecision(17);
    events << "telemetry_seconds,event,leaf_id,gamma_L,gamma_U,status,global_lb,verified_ub,detail\n";
    optimize << "leaf_id,solve_kind,native_status,optimize_return_code,global_deadline_remaining_at_launch,solver_runtime,work,nodes,simplex_iterations,barrier_iterations,memory_gb,model_sha256,in_memory_model_reused,integer_domain_restored,basis_reuse_status,native_log\n";
    lp_ledger << "leaf_id,parent_id,depth,gamma_L,gamma_U,terminal_valid,optimal,infeasible,bound_available,lower_bound,native_status,work,telemetry_seconds\n";
    bound_ledger << "parent_id,parent_lp_bound,left_id,left_lp_bound,left_infeasible,right_id,right_lp_bound,right_infeasible,post_split_bound,tolerance,decision\n";
    split_ledger << "parent_id,eligible,decision_valid,split,"
                    "child_infeasibility_trigger,strict_bound_trigger,"
                    "normalized_disjunction_gain,parent_native_bound_target,"
                    "target_phase_required,reason,b_plus,eta_proof,eta_anchor,"
                    "normalization_source,normalization_upper_bound\n";
    global_trace
        << "process_elapsed_seconds,exact_phase_elapsed_seconds,event_type,"
           "active_leaf,active_leaf_valid_lower_bound,"
           "other_open_leaf_min_valid_lower_bound,"
           "valid_global_lower_bound,verified_global_upper_bound,"
           "open_relevant_leaf_count,closed_relevant_leaf_count,event_source\n";
    native_targets
        << "phase_index,leaf_id,target_kind,current_bound,target_bound,"
           "other_open_min_bound,verified_cutoff,status,native_status,"
           "native_bound,target_reached,exact_closure,requeued,"
           "solver_runtime,work,nodes,event_source\n";
    initial_decomposition
        << "anchor_cell_index,anchor_lower,anchor_upper,active,active_lower,"
           "active_upper,truncated_by_proof_range,U_proof_launch,"
           "U_anchor_launch,proof_range_lower,proof_range_upper,"
           "normalization_source\n";
    events.flush();
    optimize.flush();
    lp_ledger.flush();
    bound_ledger.flush();
    split_ledger.flush();
    global_trace.flush();
    native_targets.flush();
    initial_decomposition.flush();
    recordProcessPhase(options, "first_tree_ledger_opened", "complete",
                       event_path.string());

    ControllingLeafScheduler scheduler(1e-7);
    const std::vector<GiniIntervalGeometry> initial = round36_causal
        ? causal_grid.active_intervals
        : makeLegacyFrontierIntervals(
              root_gamma_L, root_gamma_U, options.frontier_intervals);
    const std::vector<GiniIntervalGeometry> audit_anchor_cells =
        round36_causal
            ? causal_grid.anchor_cells
            : makeLegacyFrontierIntervals(
                  root_gamma_L, root_gamma_U, options.frontier_intervals);
    std::vector<double> audit_anchor_endpoints;
    if (round36_causal) {
        audit_anchor_endpoints = causal_grid.anchor_endpoints;
    } else if (!audit_anchor_cells.empty()) {
        audit_anchor_endpoints.push_back(audit_anchor_cells.front().lower);
        for (const GiniIntervalGeometry& cell : audit_anchor_cells) {
            audit_anchor_endpoints.push_back(cell.upper);
        }
    }
    result.external_gini_tree_anchor_grid_endpoints =
        joinDoubles(audit_anchor_endpoints);
    result.external_gini_tree_active_initial_intervals =
        joinIntervals(initial);
    result.external_gini_tree_truncated_initial_interval_count =
        round36_causal
            ? causal_grid.truncated_active_interval_count : 0;
    for (std::size_t cell_index = 0;
         cell_index < audit_anchor_cells.size(); ++cell_index) {
        bool active = false;
        GiniIntervalGeometry active_interval;
        if (round36_causal) {
            for (std::size_t active_index = 0;
                 active_index < causal_grid.active_anchor_cell_indices.size();
                 ++active_index) {
                if (causal_grid.active_anchor_cell_indices[active_index] ==
                    static_cast<int>(cell_index)) {
                    active = true;
                    active_interval = causal_grid.active_intervals[active_index];
                    break;
                }
            }
        } else {
            active = true;
            active_interval = audit_anchor_cells[cell_index];
        }
        const bool truncated = active &&
            (std::fabs(active_interval.lower -
                       audit_anchor_cells[cell_index].lower) >
                 scheduler.certificateTolerance() ||
             std::fabs(active_interval.upper -
                       audit_anchor_cells[cell_index].upper) >
                 scheduler.certificateTolerance());
        initial_decomposition << std::setprecision(17) << cell_index << ','
            << audit_anchor_cells[cell_index].lower << ','
            << audit_anchor_cells[cell_index].upper << ',' << active << ',';
        if (active) {
            initial_decomposition << active_interval.lower << ','
                                  << active_interval.upper;
        } else {
            initial_decomposition << ',';
        }
        initial_decomposition << ',' << truncated << ','
            << proof_incumbent_launch << ',' << decomposition_anchor_launch
            << ',' << root_gamma_L << ',' << root_gamma_U << ','
            << csvField(options.round36_c6_split_normalization) << '\n';
    }
    initial_decomposition.flush();
    result.external_gini_tree_initial_leaf_count =
        static_cast<long long>(initial.size());
    result.external_gini_tree_root_coverage_valid = exactIntervalCoverage(
        {root_gamma_L, root_gamma_U}, initial,
        scheduler.certificateTolerance());
    bool hard_failure = !result.external_gini_tree_root_coverage_valid;
    bool global_deadline_stop = false;
    if (hard_failure) {
        result.external_gini_tree_failure_reason = "initial_interval_coverage_failed";
    }
    for (std::size_t index = 0; index < initial.size() && !hard_failure;
         ++index) {
        ControllingLeaf leaf;
        leaf.id = "L" + std::to_string(index);
        leaf.gamma_L = initial[index].lower;
        leaf.gamma_U = initial[index].upper;
        leaf.base_lower_bound = leaf.gamma_L;
        leaf.lower_bound = leaf.gamma_L;
        leaf.lower_bound_sources = {"objective_nonnegative_penalty_G_floor"};
        leaf.cutoff = verified_seed.objective;
        std::string reason;
        if (!scheduler.addLeaf(leaf, &reason)) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "initial_leaf_add_failed:" + reason;
        }
    }

    std::unordered_map<std::string, PaperLeafRuntime> runtime;
    double verified_ub = verified_seed.objective;
    std::vector<RoutePlan> best_routes = verified_seed.routes;
    double total_model_build_seconds = 0.0;
    double last_global_lb_improvement = -1.0;
    bool first_model_build_recorded = false;
    bool first_tree_event_recorded = false;
    bool first_lp_launch_recorded = false;
    double last_trace_global_bound =
        scheduler.globalLowerBound();

    auto relevantCounts = [&scheduler]() {
        std::pair<long long, long long> counts{0, 0};
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.status == ControllingLeafStatus::Replaced ||
                leaf.parent_replaced ||
                leaf.gamma_L >=
                    leaf.cutoff - scheduler.certificateTolerance()) {
                continue;
            }
            const bool open =
                (leaf.status == ControllingLeafStatus::Open ||
                 leaf.status == ControllingLeafStatus::Invalid) &&
                leaf.lower_bound <
                    leaf.cutoff - scheduler.certificateTolerance();
            if (open) {
                ++counts.first;
            } else {
                ++counts.second;
            }
        }
        return counts;
    };
    auto otherRelevantMinimum = [&scheduler](
            const std::string& active_leaf) {
        double minimum = std::numeric_limits<double>::infinity();
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.id == active_leaf ||
                leaf.status == ControllingLeafStatus::Replaced ||
                leaf.parent_replaced ||
                leaf.gamma_L >=
                    leaf.cutoff - scheduler.certificateTolerance() ||
                !((leaf.status == ControllingLeafStatus::Open ||
                   leaf.status == ControllingLeafStatus::Invalid) &&
                  leaf.lower_bound <
                    leaf.cutoff - scheduler.certificateTolerance())) {
                continue;
            }
            minimum = std::min(minimum, leaf.lower_bound);
        }
        return minimum;
    };
    auto otherRelevantBounds = [&scheduler](
            const std::string& active_leaf) {
        std::vector<double> bounds;
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.id == active_leaf ||
                leaf.status == ControllingLeafStatus::Replaced ||
                leaf.parent_replaced ||
                leaf.gamma_L >=
                    leaf.cutoff - scheduler.certificateTolerance() ||
                !((leaf.status == ControllingLeafStatus::Open ||
                   leaf.status == ControllingLeafStatus::Invalid) &&
                  leaf.lower_bound <
                    leaf.cutoff - scheduler.certificateTolerance())) {
                continue;
            }
            bounds.push_back(leaf.lower_bound);
        }
        return bounds;
    };
    auto writeGlobalTrace = [&](double process_seconds,
                                double exact_seconds,
                                const std::string& event_type,
                                const std::string& active_leaf,
                                double active_bound,
                                double other_bound,
                                const std::string& source) {
        double global_bound = std::min(active_bound, other_bound);
        if (!std::isfinite(global_bound)) {
            global_bound = scheduler.globalLowerBound();
        }
        // A native callback can prove that the active leaf cannot improve the
        // already verified incumbent before the scheduler records the leaf's
        // closure.  The callback bound remains a valid leaf bound, but it is
        // not the global bound: the closed branch containing the incumbent is
        // still a candidate for the global optimum.  Include that candidate
        // in this telemetry-only aggregation so the exported certificate
        // trace cannot transiently rise above the verified optimum and then
        // fall when the leaf closure is recorded.
        global_bound = std::min(global_bound, verified_ub);
        const auto counts = relevantCounts();
        global_trace << std::setprecision(17) << process_seconds << ','
                     << exact_seconds << ',' << csvField(event_type) << ','
                     << csvField(active_leaf) << ',';
        if (std::isfinite(active_bound)) global_trace << active_bound;
        global_trace << ',';
        if (std::isfinite(other_bound)) global_trace << other_bound;
        global_trace << ',' << global_bound << ',' << verified_ub << ','
                     << counts.first << ',' << counts.second << ','
                     << csvField(source) << '\n';
        global_trace.flush();
        if (std::isfinite(global_bound)) {
            last_trace_global_bound =
                std::max(last_trace_global_bound, global_bound);
        }
    };
    {
        const double initial_bound = scheduler.globalLowerBound();
        writeGlobalTrace(
            processElapsedSeconds(options), elapsedTelemetry(),
            "exact_tree_initialization", "", initial_bound,
            std::numeric_limits<double>::infinity(),
            "initial_exact_interval_cover");
    }

    auto stopAtDeadline = [&]() {
        if (!global_deadline_stop) {
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "interruption", "", scheduler.globalLowerBound(),
                std::numeric_limits<double>::infinity(),
                "overall_process_deadline_open_coverage");
        }
        global_deadline_stop = true;
        ++result.external_gini_tree_global_deadline_interruption_count;
        result.external_gini_tree_failure_reason = "overall_global_deadline";
    };

    auto ensureArtifact = [&](const ControllingLeaf& leaf,
                              PaperLeafRuntime& state) -> bool {
        if (state.artifact_ready) {
            if (std::filesystem::exists(state.artifact.path) &&
                fileSha256(state.artifact.path) == state.artifact.sha256) {
                ++result.external_gini_tree_canonical_artifact_cache_hit_count;
                return true;
            }
            ++result.external_gini_tree_canonical_artifact_invalidation_count;
            result.external_gini_tree_failure_reason =
                "paper_immutable_artifact_changed:" + leaf.id;
            return false;
        }
        if (globalDeadlineRemaining() <= 0.0) {
            stopAtDeadline();
            return false;
        }
        CanonicalCompactModelSpec spec;
        spec.strengthened = true;
        spec.interval_restricted = true;
        spec.gamma_L = leaf.gamma_L;
        spec.gamma_U = leaf.gamma_U;
        spec.add_verified_incumbent_row = true;
        spec.verified_incumbent = verified_seed.objective;
        spec.incumbent_epsilon = 0.0;
        const auto build_started = PaperClock::now();
        if (!first_model_build_recorded) {
            recordProcessPhase(
                options, "root_canonical_model_construction_start", "start",
                "leaf=" + leaf.id);
            recordProcessPhase(
                options, "first_interval_model_build", "start",
                "leaf=" + leaf.id);
        }
        state.artifact = writeCanonicalCompactModel(
            instance, options, artifact_dir / "models" / (leaf.id + ".lp"),
            spec);
        const double build_seconds = std::chrono::duration<double>(
            PaperClock::now() - build_started).count();
        total_model_build_seconds += build_seconds;
        ++result.external_gini_tree_canonical_artifact_generation_count;
        if (!first_model_build_recorded) {
            recordProcessPhase(
                options, "static_row_factory_preparation_complete",
                state.artifact.written ? "complete" : "failed",
                "canonical strengthened interval row factory");
            recordProcessPhase(
                options, "root_canonical_model_construction_complete",
                state.artifact.written ? "complete" : "failed",
                "leaf=" + leaf.id);
            recordProcessPhase(
                options, "first_interval_model_build_complete",
                state.artifact.written ? "complete" : "failed",
                "leaf=" + leaf.id);
            first_model_build_recorded = true;
        }
        state.artifact_ready = state.artifact.written;
        if (!state.artifact_ready) {
            result.external_gini_tree_failure_reason =
                "paper_static_leaf_model_build_failed:" +
                state.artifact.failure_reason;
        }
        return state.artifact_ready;
    };

    auto solveLp = [&](const ControllingLeaf& leaf,
                       PaperLeafRuntime& state) -> bool {
        if (state.lp_complete) return true;
        if (!ensureArtifact(leaf, state)) return false;
        const double remaining = globalDeadlineRemaining();
        if (remaining <= 0.0) {
            stopAtDeadline();
            return false;
        }
        FixedIntervalMipRequest request;
        request.solve_kind = FixedIntervalSolveKind::PaperLpRelaxation;
        request.leaf_id = leaf.id;
        request.gamma_L = leaf.gamma_L;
        request.gamma_U = leaf.gamma_U;
        request.verified_cutoff = verified_seed.objective;
        request.global_deadline_remaining_seconds = remaining;
        request.new_leaf = true;
        request.warm_start_enabled = false;
        request.canonical_model_path = state.artifact.path;
        request.canonical_model_fingerprint = state.artifact.sha256;
        request.canonical_model_scope = state.artifact.model_scope;
        request.canonical_row_signature = state.artifact.row_signature;
        request.native_log_path = artifact_dir / "native_logs" /
            (leaf.id + "_lp.gurobi.log");
        request.incremental_model_reuse_enabled = incremental_model_reuse;
        request.retain_model_after_solve = incremental_model_reuse;
        if (!first_lp_launch_recorded) {
            recordProcessPhase(
                options, "first_lp_optimize_launch", "start",
                "leaf=" + leaf.id);
            first_lp_launch_recorded = true;
        }
        const FixedIntervalMipOutcome outcome = backend->solve(request);
        optimize << leaf.id << ",LP," << csvField(outcome.native_status) << ','
                 << outcome.optimize_return_code << ',' << remaining << ','
                 << outcome.solver_runtime_seconds << ',' << outcome.work << ','
                 << outcome.nodes << ',' << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ',' << outcome.memory_gb << ','
                 << state.artifact.sha256 << ','
                 << outcome.in_memory_model_reused << ','
                 << outcome.integer_domain_restored << ','
                 << csvField(outcome.basis_reuse_status) << ','
                 << csvField(outcome.native_log_path) << '\n';
        if (outcome.interrupted) {
            stopAtDeadline();
            return false;
        }
        state.lp.terminal_valid = outcome.lp_terminal_valid &&
            outcome.exact_zero_gap_roundtrip &&
            outcome.model_fingerprint_matches_request &&
            outcome.feasibility_consistency_gate;
        state.lp.optimal = outcome.optimal;
        state.lp.infeasible = outcome.infeasible;
        state.lp.bound_available = outcome.native_bound_available;
        state.lp.lower_bound = outcome.native_bound;
        state.lp_complete = state.lp.terminal_valid;
        lp_ledger << leaf.id << ',' << csvField(leaf.parent_id) << ','
                  << leaf.split_depth << ',' << std::setprecision(17)
                  << leaf.gamma_L << ',' << leaf.gamma_U << ','
                  << state.lp.terminal_valid << ',' << state.lp.optimal << ','
                  << state.lp.infeasible << ',' << state.lp.bound_available
                  << ',' << state.lp.lower_bound << ','
                  << csvField(outcome.native_status) << ',' << outcome.work
                  << ',' << elapsedTelemetry() << '\n';
        if (!state.lp_complete) {
            result.external_gini_tree_failure_reason = outcome.failure_reason == "none"
                ? "lp_relaxation_not_terminal_valid:" + leaf.id
                : outcome.failure_reason;
            return false;
        }
        if (state.lp.optimal) {
            std::string reason;
            if (!scheduler.mergeValidLowerBound(
                    leaf.id, state.lp.lower_bound,
                    "optimal_complete_lp_relaxation", &reason)) {
                result.external_gini_tree_failure_reason =
                    "paper_lp_bound_merge_failed:" + reason;
                return false;
            }
        }
        events << elapsedTelemetry() << ",lp_complete," << leaf.id << ','
               << leaf.gamma_L << ',' << leaf.gamma_U << ','
               << (state.lp.infeasible ? "infeasible" : "optimal") << ','
               << scheduler.globalLowerBound() << ',' << verified_ub << ','
               << csvField("complete_lp_relaxation") << '\n';
        const ControllingLeaf* traced_leaf = scheduler.findLeaf(leaf.id);
        const double traced_bound = traced_leaf
            ? traced_leaf->lower_bound : leaf.lower_bound;
        writeGlobalTrace(
            processElapsedSeconds(options), elapsedTelemetry(),
            "parent_lp_completion", leaf.id, traced_bound,
            otherRelevantMinimum(leaf.id),
            state.lp.infeasible
                ? "complete_parent_lp_infeasible"
                : "complete_parent_lp_optimal");
        return true;
    };

    enum class C6TargetDisposition {
        Requeued,
        Closed,
        Deadline,
        Failed
    };
    auto runC6NativeTarget = [&](
            const ControllingLeaf& bounded,
            PaperLeafRuntime& state,
            double target,
            const std::string& target_kind,
            const std::string& event_source) {
        if (!std::isfinite(target) ||
            target <= bounded.lower_bound +
                scheduler.certificateTolerance()) {
            result.external_gini_tree_failure_reason =
                "c6_invalid_nonincreasing_native_target:" + bounded.id;
            return C6TargetDisposition::Failed;
        }
        const double remaining = globalDeadlineRemaining();
        if (remaining <= 0.0) {
            stopAtDeadline();
            return C6TargetDisposition::Deadline;
        }
        ++state.c6_native_phase_count;
        const int phase_index = state.c6_native_phase_count;
        if (target_kind == "next_leaf") {
            ++result.external_gini_tree_next_leaf_target_phase_count;
            ++result.external_gini_tree_child_lookahead_avoided_count;
        } else {
            ++result.external_gini_tree_child_bound_target_phase_count;
        }
        FixedIntervalMipRequest request;
        request.solve_kind =
            FixedIntervalSolveKind::PaperPartialBoundTargetMip;
        request.leaf_id = bounded.id;
        request.gamma_L = bounded.gamma_L;
        request.gamma_U = bounded.gamma_U;
        request.verified_cutoff = verified_ub;
        request.global_deadline_remaining_seconds = remaining;
        request.new_leaf = false;
        request.warm_start_enabled = false;
        request.canonical_model_path = state.artifact.path;
        request.canonical_model_fingerprint = state.artifact.sha256;
        request.canonical_model_scope = state.artifact.model_scope;
        request.canonical_row_signature = state.artifact.row_signature;
        request.native_log_path = artifact_dir / "native_logs" /
            (bounded.id + "_c6_" + std::to_string(phase_index) + "_" +
             target_kind + "_target_mip.gurobi.log");
        request.incremental_model_reuse_enabled = true;
        request.retain_model_after_solve = true;
        request.native_bound_target_enabled = true;
        request.native_bound_target = target;
        request.native_bound_target_tolerance =
            scheduler.certificateTolerance();
        request.capture_native_bound_events = true;
        const double process_launch = processElapsedSeconds(options);
        const double exact_launch = elapsedTelemetry();
        const double other_bound =
            otherRelevantMinimum(bounded.id);
        const FixedIntervalMipOutcome outcome = backend->solve(request);
        optimize << bounded.id << ','
                 << (target_kind == "next_leaf"
                        ? "NEXT_LEAF_TARGET_MIP"
                        : "CHILD_BOUND_TARGET_MIP")
                 << ',' << csvField(outcome.native_status) << ','
                 << outcome.optimize_return_code << ',' << remaining << ','
                 << outcome.solver_runtime_seconds << ',' << outcome.work
                 << ',' << outcome.nodes << ',' << outcome.simplex_iterations
                 << ',' << outcome.barrier_iterations << ','
                 << outcome.memory_gb << ',' << state.artifact.sha256 << ','
                 << outcome.in_memory_model_reused << ','
                 << outcome.integer_domain_restored << ','
                 << csvField(outcome.basis_reuse_status) << ','
                 << csvField(outcome.native_log_path) << '\n';
        for (const FixedIntervalNativeBoundEvent& native_event :
                outcome.native_bound_events) {
            if (!native_event.native_bound_available ||
                (!native_event.bound_improved &&
                 !native_event.target_reached)) {
                continue;
            }
            writeGlobalTrace(
                process_launch + native_event.solver_runtime_seconds,
                exact_launch + native_event.solver_runtime_seconds,
                native_event.target_reached
                    ? (target_kind == "next_leaf"
                        ? "next_leaf_native_bound_target"
                        : "child_native_bound_target")
                    : (native_event.processed_nodes <= 0.0
                        ? "native_root_processing_bound"
                        : "partial_native_mip_bound_improvement"),
                bounded.id,
                std::max(
                    bounded.lower_bound, native_event.native_bound),
                other_bound,
                "gurobi_cb_mip_objbnd_valid_native_bound");
        }
        const bool engineering_valid =
            outcome.attempted && outcome.available &&
            outcome.solver_finalization_reached &&
            outcome.model_fingerprint_matches_request &&
            outcome.exact_zero_gap_roundtrip &&
            outcome.feasibility_consistency_gate &&
            outcome.partial_bound_target_mip;
        if (!engineering_valid) {
            result.external_gini_tree_failure_reason =
                "c6_native_target_engineering_gate_failed:" +
                outcome.failure_reason;
            native_targets << phase_index << ',' << bounded.id << ','
                           << target_kind << ',' << bounded.lower_bound << ','
                           << target << ',' << other_bound << ','
                           << verified_ub << ",engineering_invalid,"
                           << csvField(outcome.native_status) << ','
                           << outcome.native_bound << ",0,0,0,"
                           << outcome.solver_runtime_seconds << ','
                           << outcome.work << ',' << outcome.nodes << ','
                           << csvField(event_source) << '\n';
            return C6TargetDisposition::Failed;
        }
        if (outcome.native_bound_available) {
            std::string reason;
            if (!scheduler.mergeValidLowerBound(
                    bounded.id, outcome.native_bound,
                    target_kind == "next_leaf"
                        ? "valid_next_leaf_target_native_bound"
                        : "valid_child_target_native_bound",
                    &reason)) {
                result.external_gini_tree_failure_reason =
                    "c6_native_target_bound_merge_failed:" + reason;
                return C6TargetDisposition::Failed;
            }
        }
        if (outcome.incumbent_available &&
            outcome.incumbent_independently_verified &&
            outcome.incumbent_objective < verified_ub - 1e-9) {
            verified_ub = outcome.incumbent_objective;
            best_routes = outcome.incumbent_routes;
            std::string cutoff_reason;
            if (!scheduler.tightenVerifiedCutoff(
                    verified_ub, &cutoff_reason)) {
                result.external_gini_tree_failure_reason =
                    "c6_verified_cutoff_tightening_failed:" + cutoff_reason;
                return C6TargetDisposition::Failed;
            }
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "incumbent_improvement", bounded.id,
                scheduler.findLeaf(bounded.id)
                    ? scheduler.findLeaf(bounded.id)->lower_bound
                    : bounded.lower_bound,
                otherRelevantMinimum(bounded.id),
                "independently_verified_c6_partial_mip_incumbent");
        }
        if (outcome.optimal || outcome.infeasible) {
            std::string reason;
            const ControllingLeafStatus close_status =
                outcome.infeasible
                    ? ControllingLeafStatus::Empty
                    : ControllingLeafStatus::Closed;
            if (!scheduler.setStatus(
                    bounded.id, close_status,
                    outcome.infeasible
                        ? "c6_native_target_phase_infeasible"
                        : "c6_native_target_phase_optimal",
                    &reason)) {
                result.external_gini_tree_failure_reason =
                    "c6_native_target_closure_failed:" + reason;
                return C6TargetDisposition::Failed;
            }
            backend->discardLeaf(bounded.id);
            for (const ControllingLeaf& child :
                    state.c6_cached_children) {
                backend->discardLeaf(child.id);
            }
            native_targets << phase_index << ',' << bounded.id << ','
                           << target_kind << ',' << bounded.lower_bound << ','
                           << target << ',' << other_bound << ','
                           << verified_ub << ",exact_closure,"
                           << csvField(outcome.native_status) << ','
                           << outcome.native_bound << ','
                           << outcome.native_bound_target_reached
                           << ",1,0," << outcome.solver_runtime_seconds << ','
                           << outcome.work << ',' << outcome.nodes << ','
                           << csvField(event_source) << '\n';
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                outcome.infeasible
                    ? "infeasible_closure"
                    : "terminal_mip_closure",
                bounded.id, std::numeric_limits<double>::infinity(),
                scheduler.globalLowerBound(),
                "c6_native_target_phase_exact_closure");
            return C6TargetDisposition::Closed;
        }
        if (outcome.native_bound_target_reached &&
            outcome.native_bound_target_termination_requested &&
            outcome.native_bound_available &&
            outcome.native_bound +
                scheduler.certificateTolerance() >= target) {
            if (target_kind == "next_leaf") {
                ++result.external_gini_tree_next_leaf_target_reached_count;
                state.c6_frontier_milestone_reached = true;
            } else {
                ++result.external_gini_tree_child_bound_target_reached_count;
                ++result.external_gini_tree_forced_split_avoided_count;
            }
            ++result.external_gini_tree_native_requeue_count;
            const ControllingLeaf* strengthened =
                scheduler.findLeaf(bounded.id);
            native_targets << phase_index << ',' << bounded.id << ','
                           << target_kind << ',' << bounded.lower_bound << ','
                           << target << ',' << other_bound << ','
                           << verified_ub << ",target_reached_requeue,"
                           << csvField(outcome.native_status) << ','
                           << outcome.native_bound << ",1,0,1,"
                           << outcome.solver_runtime_seconds << ','
                           << outcome.work << ',' << outcome.nodes << ','
                           << csvField(event_source) << '\n';
            events << elapsedTelemetry()
                   << ",native_bound_target_reached," << bounded.id << ','
                   << bounded.gamma_L << ',' << bounded.gamma_U << ",open,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField(event_source) << '\n';
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                target_kind == "next_leaf"
                    ? "next_leaf_native_bound_target"
                    : "child_native_bound_target",
                bounded.id,
                strengthened ? strengthened->lower_bound
                             : outcome.native_bound,
                otherRelevantMinimum(bounded.id),
                event_source);
            return C6TargetDisposition::Requeued;
        }
        if (outcome.interrupted) {
            native_targets << phase_index << ',' << bounded.id << ','
                           << target_kind << ',' << bounded.lower_bound << ','
                           << target << ',' << other_bound << ','
                           << verified_ub << ",deadline_open,"
                           << csvField(outcome.native_status) << ','
                           << outcome.native_bound << ",0,0,0,"
                           << outcome.solver_runtime_seconds << ','
                           << outcome.work << ',' << outcome.nodes << ','
                           << csvField(event_source) << '\n';
            stopAtDeadline();
            return C6TargetDisposition::Deadline;
        }
        result.external_gini_tree_failure_reason =
            "c6_native_target_status_invalid:" + outcome.native_status;
        return C6TargetDisposition::Failed;
    };

    PilotWeakestGiniCellSelection round37_pilot_selection;
    PilotGlobalFrontierSelection round38_pilot_selection;
    bool round37_pilot_prefinement_pending = false;
    bool round38_frontier_pilot_pending = false;
    if ((round37_pilot_prefine || round38_frontier_pilot) &&
        !hard_failure) {
        std::vector<PilotGiniCellAssessment> assessments;
        assessments.reserve(initial.size());
        for (std::size_t index = 0;
             index < initial.size() && !hard_failure; ++index) {
            const std::string leaf_id = "L" + std::to_string(index);
            const ControllingLeaf* leaf_ptr = scheduler.findLeaf(leaf_id);
            if (!leaf_ptr) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round37_pilot_initial_leaf_missing:" + leaf_id;
                break;
            }
            const ControllingLeaf leaf = *leaf_ptr;
            PaperLeafRuntime& state = runtime[leaf_id];
            if (!solveLp(leaf, state)) {
                if (!global_deadline_stop) hard_failure = true;
                break;
            }
            if (round37_pilot_prefine) {
                ++result.round37_pilot_initial_lp_count;
            } else {
                ++result.round38_pilot_initial_lp_count;
            }
            if (state.lp.infeasible) {
                const std::string source = round37_pilot_prefine
                    ? "round37_pilot_complete_initial_lp_infeasible"
                    : "round38_pilot_complete_initial_lp_infeasible";
                std::string reason;
                if (!scheduler.setStatus(
                        leaf_id, ControllingLeafStatus::Empty,
                        source, &reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        (round37_pilot_prefine
                            ? "round37_pilot_infeasible_closure_failed:"
                            : "round38_pilot_infeasible_closure_failed:") +
                        reason;
                    break;
                }
                backend->discardLeaf(leaf_id);
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "infeasible_closure", leaf_id,
                    std::numeric_limits<double>::infinity(),
                    scheduler.globalLowerBound(),
                    source);
            }
        }
        const long long pilot_initial_lp_count = round37_pilot_prefine
            ? result.round37_pilot_initial_lp_count
            : result.round38_pilot_initial_lp_count;
        const bool all_initial_lps_complete =
            !hard_failure && !global_deadline_stop &&
            pilot_initial_lp_count ==
                static_cast<long long>(initial.size());
        if (round37_pilot_prefine) {
            result.round37_pilot_all_initial_lps_complete =
                all_initial_lps_complete;
        } else {
            result.round38_pilot_all_initial_lps_complete =
                all_initial_lps_complete;
        }
        if (all_initial_lps_complete) {
            for (std::size_t index = 0; index < initial.size(); ++index) {
                const std::string leaf_id = "L" + std::to_string(index);
                const ControllingLeaf* leaf = scheduler.findLeaf(leaf_id);
                const PaperLeafRuntime& state = runtime[leaf_id];
                PilotGiniCellAssessment assessment;
                assessment.leaf_id = leaf_id;
                assessment.interval = initial[index];
                assessment.structurally_open = leaf &&
                    (leaf->status == ControllingLeafStatus::Open ||
                     leaf->status == ControllingLeafStatus::Invalid) &&
                    !leaf->parent_replaced;
                assessment.lp_complete = state.lp_complete;
                assessment.lp_optimal = state.lp.optimal;
                assessment.lp_bound_available = state.lp.bound_available;
                assessment.lp_lower_bound = state.lp.lower_bound;
                assessment.verified_cutoff = verified_ub;
                assessments.push_back(assessment);
            }
            if (round37_pilot_prefine) {
                round37_pilot_selection = selectPilotWeakestGiniCell(
                    assessments, scheduler.certificateTolerance());
                result.round37_pilot_eligible_cell_count =
                    round37_pilot_selection.eligible_cell_count;
            } else {
                round38_pilot_selection = selectPilotGlobalFrontierCell(
                    assessments, scheduler.certificateTolerance());
                result.round38_pilot_eligible_cell_count =
                    round38_pilot_selection.eligible_cell_count;
                result.round38_pilot_frontier_plateau_size =
                    round38_pilot_selection.frontier_plateau_size;
                result.round38_pilot_unique_controlling_cell =
                    round38_pilot_selection.unique_controlling_cell;
                result.round38_pilot_next_strict_frontier_available =
                    round38_pilot_selection.next_strict_frontier_available;
                result.round38_pilot_next_strict_frontier =
                    round38_pilot_selection.next_strict_frontier;
                result.round38_pilot_sorted_initial_bounds =
                    joinDoubles(round38_pilot_selection.sorted_open_bounds);
                result.round38_pilot_decision_reason =
                    round38_pilot_selection.reason;
            }
            if (round37_pilot_prefine &&
                round37_pilot_selection.valid) {
                result.round37_pilot_weakest_leaf_id =
                    round37_pilot_selection.leaf_id;
                result.round37_pilot_weakest_lower_bound =
                    round37_pilot_selection.lp_lower_bound;
                result.round37_pilot_weakest_gamma_L =
                    round37_pilot_selection.interval.lower;
                result.round37_pilot_weakest_gamma_U =
                    round37_pilot_selection.interval.upper;
                round37_pilot_prefinement_pending = true;
                events << elapsedTelemetry() << ",round37_pilot_selection,"
                       << round37_pilot_selection.leaf_id << ','
                       << round37_pilot_selection.interval.lower << ','
                       << round37_pilot_selection.interval.upper << ",open,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(round37_pilot_selection.reason)
                       << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "round37_pilot_selection",
                    round37_pilot_selection.leaf_id,
                    round37_pilot_selection.lp_lower_bound,
                    otherRelevantMinimum(round37_pilot_selection.leaf_id),
                    round37_pilot_selection.reason);
            } else if (round38_frontier_pilot &&
                       round38_pilot_selection.valid) {
                result.round38_pilot_selected_leaf_id =
                    round38_pilot_selection.leaf_id;
                result.round38_pilot_selected_lower_bound =
                    round38_pilot_selection.controlling_lower_bound;
                result.round38_pilot_selected_gamma_L =
                    round38_pilot_selection.interval.lower;
                result.round38_pilot_selected_gamma_U =
                    round38_pilot_selection.interval.upper;
                round38_frontier_pilot_pending = true;
                events << elapsedTelemetry() << ",round38_pilot_selection,"
                       << round38_pilot_selection.leaf_id << ','
                       << round38_pilot_selection.interval.lower << ','
                       << round38_pilot_selection.interval.upper << ",open,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(round38_pilot_selection.reason)
                       << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "round38_pilot_selection",
                    round38_pilot_selection.leaf_id,
                    round38_pilot_selection.controlling_lower_bound,
                    round38_pilot_selection.next_strict_frontier,
                    round38_pilot_selection.reason);
            }
        }
    }

    while (!hard_failure && !global_deadline_stop &&
           !scheduler.everyRelevantLeafClosed()) {
        if (!first_tree_event_recorded) {
            recordProcessPhase(
                options, "first_external_tree_event", "start",
                "scheduler_select_next");
            first_tree_event_recorded = true;
        }
        if (globalDeadlineRemaining() <= 0.0) {
            stopAtDeadline();
            break;
        }
        const double global_before = scheduler.globalLowerBound();
        const ControllingLeafSelection selection =
            scheduler.selectNextByBoundOnly();
        if (!selection.available) break;
        const ControllingLeaf* selected_ptr =
            scheduler.findLeaf(selection.selected_leaf_id);
        if (!selected_ptr) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = "paper_selected_leaf_missing";
            break;
        }
        const ControllingLeaf selected = *selected_ptr;
        PaperLeafRuntime& selected_state = runtime[selected.id];
        if (!solveLp(selected, selected_state)) {
            if (!global_deadline_stop) hard_failure = true;
            break;
        }
        if (selected_state.lp.infeasible) {
            std::string reason;
            if (!scheduler.setStatus(selected.id, ControllingLeafStatus::Empty,
                    "complete_parent_lp_infeasible", &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "paper_lp_infeasible_closure_failed:" + reason;
            }
            if (incremental_model_reuse) backend->discardLeaf(selected.id);
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "infeasible_closure", selected.id,
                std::numeric_limits<double>::infinity(),
                scheduler.globalLowerBound(),
                "complete_parent_lp_infeasible");
            continue;
        }

        const ControllingLeaf* bounded_ptr = scheduler.findLeaf(selected.id);
        if (!bounded_ptr) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "paper_parent_missing_after_lp";
            break;
        }
        const ControllingLeaf bounded = *bounded_ptr;
        if (incremental_model_reuse &&
            bounded.lower_bound >=
                bounded.cutoff - scheduler.certificateTolerance()) {
            std::string reason;
            if (!scheduler.setStatus(
                    bounded.id, ControllingLeafStatus::Fathomed,
                    "complete_lp_bound_cannot_improve_verified_incumbent",
                    &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round29_c4_lp_fathom_failed:" + reason;
                break;
            }
            ++result.external_gini_tree_lp_pruned_leaf_count;
            backend->discardLeaf(bounded.id);
            events << elapsedTelemetry() << ",lp_bound_prune," << bounded.id
                   << ',' << bounded.gamma_L << ',' << bounded.gamma_U
                   << ",fathomed," << scheduler.globalLowerBound() << ','
                   << verified_ub << ','
                   << csvField(
                          "complete_lp_bound_ge_verified_cutoff_minus_tolerance")
                   << '\n';
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "lp_cutoff_pruning", bounded.id,
                std::numeric_limits<double>::infinity(),
                scheduler.globalLowerBound(),
                "complete_lp_bound_vs_verified_incumbent");
            continue;
        }
        const bool round37_force_prefinement =
            round37_pilot_prefinement_pending &&
            bounded.id == round37_pilot_selection.leaf_id;
        const bool round38_force_frontier_evaluation =
            round38_frontier_pilot_pending &&
            bounded.id == round38_pilot_selection.leaf_id;
        if (c6_nonblocking && !round37_force_prefinement &&
            !round38_force_frontier_evaluation) {
            const C6FrontierDecision frontier =
                evaluateC6FrontierDecision(
                    bounded.lower_bound,
                    otherRelevantBounds(bounded.id),
                    scheduler.certificateTolerance(),
                    selected_state.c6_frontier_milestone_reached);
            if (!frontier.valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "c6_frontier_decision_invalid:" + frontier.reason;
                break;
            }
            if (frontier.requeue_without_native) {
                ++result.external_gini_tree_parent_lp_requeue_count;
                ++result.external_gini_tree_child_lookahead_avoided_count;
                events << elapsedTelemetry() << ",parent_lp_requeue,"
                       << bounded.id << ',' << bounded.gamma_L << ','
                       << bounded.gamma_U << ",open,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(frontier.reason) << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "parent_lp_requeue", bounded.id, bounded.lower_bound,
                    otherRelevantMinimum(bounded.id),
                    "c6_selected_leaf_no_longer_controlling");
                continue;
            }
            if (frontier.run_native_target) {
                const C6TargetDisposition disposition =
                    runC6NativeTarget(
                        bounded, selected_state,
                        frontier.native_bound_target, "next_leaf",
                        "c6_next_strict_frontier_bound_reached_requeue");
                if (disposition == C6TargetDisposition::Failed) {
                    hard_failure = true;
                    break;
                }
                if (disposition == C6TargetDisposition::Deadline) break;
                continue;
            }
            if (!frontier.allow_child_lookahead) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "c6_frontier_decision_has_no_action";
                break;
            }
        }
        if (c5_bound_target && selected_state.c5_split_pending) {
            std::string reason;
            if (!scheduler.splitLeafAtomically(
                    bounded.id, selected_state.c5_pending_children, &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "c5_delayed_atomic_split_failed:" + reason;
                break;
            }
            ++result.external_gini_tree_split_count;
            backend->discardLeaf(bounded.id);
            for (const ControllingLeaf& child :
                    selected_state.c5_pending_children) {
                if (runtime[child.id].lp.infeasible) {
                    if (!scheduler.setStatus(
                            child.id, ControllingLeafStatus::Empty,
                            "complete_child_lp_infeasible", &reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "c5_delayed_infeasible_child_closure_failed:" +
                            reason;
                        break;
                    }
                    backend->discardLeaf(child.id);
                }
            }
            if (hard_failure) break;
            selected_state.c5_split_pending = false;
            events << elapsedTelemetry() << ",atomic_split," << bounded.id
                   << ',' << bounded.gamma_L << ',' << bounded.gamma_U
                   << ",replaced," << scheduler.globalLowerBound() << ','
                   << verified_ub << ','
                   << csvField(
                          "c5_parent_native_target_reached_delayed_split")
                   << '\n';
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "split", bounded.id,
                std::numeric_limits<double>::infinity(),
                scheduler.globalLowerBound(),
                "c5_parent_native_target_reached_delayed_atomic_split");
            continue;
        }
        const bool eligible = legacyAdaptiveSplitEligible(
            bounded.gamma_L, bounded.gamma_U, bounded.split_depth,
            options.frontier_adaptive_max_depth,
            options.frontier_adaptive_min_width);
        bool split_parent = false;
        if (eligible) {
            const auto geometry = splitLegacyFrontierInterval(
                bounded.gamma_L, bounded.gamma_U,
                options.frontier_adaptive_split_factor);
            if (geometry.size() != 2 || !exactIntervalCoverage(
                    {bounded.gamma_L, bounded.gamma_U}, geometry,
                    scheduler.certificateTolerance())) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "paper_midpoint_child_coverage_failed";
                break;
            }
            std::vector<ControllingLeaf> children;
            children.reserve(2);
            for (std::size_t index = 0; index < geometry.size(); ++index) {
                ControllingLeaf child;
                child.id = bounded.id + "." + std::to_string(index);
                child.parent_id = bounded.id;
                child.child_index = static_cast<int>(index);
                child.split_depth = bounded.split_depth + 1;
                child.gamma_L = geometry[index].lower;
                child.gamma_U = geometry[index].upper;
                child.base_lower_bound = bounded.lower_bound;
                child.lower_bound = bounded.lower_bound;
                child.lower_bound_sources = {"inherited_parent_lp_bound"};
                child.cutoff = bounded.cutoff;
                children.push_back(child);
            }
            const bool reuse_c6_children =
                c6_nonblocking && selected_state.c6_children_ready;
            if (reuse_c6_children) {
                if (selected_state.c6_cached_children.size() != 2) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "c6_cached_child_count_invalid:" + bounded.id;
                    break;
                }
                children = selected_state.c6_cached_children;
                for (ControllingLeaf& child : children) {
                    child.base_lower_bound = std::max(
                        child.base_lower_bound, bounded.lower_bound);
                    child.lower_bound = std::max(
                        child.lower_bound, bounded.lower_bound);
                    child.cutoff = bounded.cutoff;
                    child.lower_bound_sources.push_back(
                        "inherited_requeued_parent_native_bound");
                }
                ++result.external_gini_tree_child_lookahead_reuse_count;
                events << elapsedTelemetry() << ",child_lp_reuse,"
                       << bounded.id << ',' << bounded.gamma_L << ','
                       << bounded.gamma_U << ",open,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(
                              "c6_cached_complete_child_lp_pair_reused")
                       << '\n';
            }
            // Child LPs are structural lookahead events. They are evaluated
            // completely before the scheduler sees either child, preserving
            // atomic parent replacement.
            if (!reuse_c6_children) for (ControllingLeaf& child : children) {
                std::string add_reason;
                ControllingLeafScheduler isolated(
                    scheduler.certificateTolerance());
                if (!isolated.addLeaf(child, &add_reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "paper_child_precheck_failed:" + add_reason;
                    break;
                }
                // solveLp merges into the supplied scheduler, so evaluate a
                // child copy directly here and defer the inherited merge until
                // the atomic split below.
                PaperLeafRuntime& child_state = runtime[child.id];
                if (!ensureArtifact(child, child_state)) break;
                const double remaining = globalDeadlineRemaining();
                if (remaining <= 0.0) {
                    stopAtDeadline();
                    break;
                }
                FixedIntervalMipRequest request;
                request.solve_kind = FixedIntervalSolveKind::PaperLpRelaxation;
                request.leaf_id = child.id;
                request.gamma_L = child.gamma_L;
                request.gamma_U = child.gamma_U;
                request.verified_cutoff =
                    c6_nonblocking ? verified_ub : verified_seed.objective;
                request.global_deadline_remaining_seconds = remaining;
                request.new_leaf = true;
                request.canonical_model_path = child_state.artifact.path;
                request.canonical_model_fingerprint = child_state.artifact.sha256;
                request.canonical_model_scope = child_state.artifact.model_scope;
                request.canonical_row_signature = child_state.artifact.row_signature;
                request.native_log_path = artifact_dir / "native_logs" /
                    (child.id + "_lp.gurobi.log");
                request.incremental_model_reuse_enabled =
                    incremental_model_reuse;
                request.retain_model_after_solve =
                    incremental_model_reuse;
                const FixedIntervalMipOutcome outcome = backend->solve(request);
                optimize << child.id << ",LP," << csvField(outcome.native_status)
                         << ',' << outcome.optimize_return_code << ',' << remaining
                         << ',' << outcome.solver_runtime_seconds << ','
                         << outcome.work << ',' << outcome.nodes << ','
                         << outcome.simplex_iterations << ','
                         << outcome.barrier_iterations << ',' << outcome.memory_gb
                         << ',' << child_state.artifact.sha256 << ','
                         << outcome.in_memory_model_reused << ','
                         << outcome.integer_domain_restored << ','
                         << csvField(outcome.basis_reuse_status) << ','
                         << csvField(outcome.native_log_path) << '\n';
                if (outcome.interrupted) {
                    stopAtDeadline();
                    break;
                }
                child_state.lp.terminal_valid = outcome.lp_terminal_valid &&
                    outcome.exact_zero_gap_roundtrip &&
                    outcome.model_fingerprint_matches_request &&
                    outcome.feasibility_consistency_gate;
                child_state.lp.optimal = outcome.optimal;
                child_state.lp.infeasible = outcome.infeasible;
                child_state.lp.bound_available = outcome.native_bound_available;
                child_state.lp.lower_bound = outcome.native_bound;
                child_state.lp_complete = child_state.lp.terminal_valid;
                lp_ledger << child.id << ',' << csvField(child.parent_id) << ','
                          << child.split_depth << ',' << child.gamma_L << ','
                          << child.gamma_U << ',' << child_state.lp.terminal_valid
                          << ',' << child_state.lp.optimal << ','
                          << child_state.lp.infeasible << ','
                          << child_state.lp.bound_available << ','
                          << child_state.lp.lower_bound << ','
                          << csvField(outcome.native_status) << ',' << outcome.work
                          << ',' << elapsedTelemetry() << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "child_lp_completion", child.id,
                    child_state.lp.infeasible
                        ? std::numeric_limits<double>::infinity()
                        : std::max(
                            bounded.lower_bound, child_state.lp.lower_bound),
                    scheduler.globalLowerBound(),
                    child_state.lp.infeasible
                        ? "complete_speculative_child_lp_infeasible"
                        : "complete_speculative_child_lp_optimal");
                if (!child_state.lp_complete) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        outcome.failure_reason == "none"
                            ? "child_lp_not_terminal_valid:" + child.id
                            : outcome.failure_reason;
                    break;
                }
                if (child_state.lp.optimal) {
                    child.base_lower_bound = std::max(
                        bounded.lower_bound, child_state.lp.lower_bound);
                    child.lower_bound = child.base_lower_bound;
                    child.lower_bound_sources.push_back(
                        "optimal_complete_child_lp_relaxation");
                }
            }
            if (hard_failure || global_deadline_stop) break;
            if (c6_nonblocking && !reuse_c6_children) {
                selected_state.c6_children_ready = true;
                selected_state.c6_cached_children = children;
            }
            const PaperLpSplitDecision split = evaluatePaperLpSplitDecision(
                bounded.lower_bound, runtime[children[0].id].lp,
                runtime[children[1].id].lp,
                scheduler.certificateTolerance());
            const C5BoundTargetSplitDecision c5_split = c5_bound_target
                ? evaluateC5BoundTargetSplitDecision(
                      bounded.lower_bound, verified_ub,
                      runtime[children[0].id].lp,
                      runtime[children[1].id].lp,
                      kRound30C5NormalizedSplitThreshold,
                      scheduler.certificateTolerance())
                : C5BoundTargetSplitDecision{};
            const C6CurrentSplitDecision c6_split = c6_nonblocking
                ? (round36_causal
                    ? evaluateC6CurrentSplitDecision(
                          bounded.lower_bound, verified_ub,
                          decomposition_anchor_launch,
                          options.round36_c6_split_normalization,
                          runtime[children[0].id].lp,
                          runtime[children[1].id].lp,
                          kRound31C6NormalizedSplitThreshold,
                          scheduler.certificateTolerance())
                    : evaluateC6CurrentSplitDecision(
                          bounded.lower_bound, verified_ub,
                          runtime[children[0].id].lp,
                          runtime[children[1].id].lp,
                          kRound31C6NormalizedSplitThreshold,
                          scheduler.certificateTolerance()))
                : C6CurrentSplitDecision{};
            PilotGlobalFrontierLiftDecision round38_split;
            if (round38_force_frontier_evaluation) {
                const PaperLpResult& left_lp =
                    runtime[children[0].id].lp;
                const PaperLpResult& right_lp =
                    runtime[children[1].id].lp;
                const PilotFrontierChildBound left{
                    left_lp.terminal_valid, left_lp.optimal,
                    left_lp.infeasible, left_lp.bound_available,
                    left_lp.lower_bound};
                const PilotFrontierChildBound right{
                    right_lp.terminal_valid, right_lp.optimal,
                    right_lp.infeasible, right_lp.bound_available,
                    right_lp.lower_bound};
                round38_split = evaluatePilotGlobalFrontierLift(
                    round38_pilot_selection, left, right,
                    scheduler.certificateTolerance());
                result.round38_pilot_children_evaluated = true;
                result.round38_pilot_left_child_infeasible =
                    left.infeasible;
                result.round38_pilot_right_child_infeasible =
                    right.infeasible;
                result.round38_pilot_left_child_bound =
                    left.infeasible ? 0.0 : left.lower_bound;
                result.round38_pilot_right_child_bound =
                    right.infeasible ? 0.0 : right.lower_bound;
                result.round38_pilot_b_plus_infinite =
                    !std::isfinite(round38_split.b_plus);
                result.round38_pilot_b_plus =
                    std::isfinite(round38_split.b_plus)
                        ? round38_split.b_plus : 0.0;
                result.round38_pilot_delta_local =
                    std::isfinite(round38_split.delta_local)
                        ? round38_split.delta_local : 0.0;
                result.round38_pilot_hypothetical_global_bound =
                    round38_split.hypothetical_global_bound;
                result.round38_pilot_delta_global =
                    round38_split.delta_global;
                result.round38_pilot_frontier_completion =
                    round38_split.frontier_completion;
                result.round38_pilot_completes_next_strict_frontier =
                    round38_split.completes_next_strict_frontier;
                result.round38_pilot_sorted_post_bounds =
                    joinDoubles(
                        round38_split.hypothetical_sorted_open_bounds);
                result.round38_pilot_decision_reason =
                    round38_split.reason;
            }
            const bool decision_valid =
                round38_force_frontier_evaluation
                    ? round38_split.valid
                    : (round37_force_prefinement
                    ? c6_split.valid
                    : (c6_nonblocking
                    ? c6_split.valid
                    : (c5_bound_target ? c5_split.valid : split.valid)));
            const bool split_immediately =
                round38_force_frontier_evaluation
                    ? round38_split.split_immediately
                    : (round37_force_prefinement ||
                       (c6_nonblocking
                    ? c6_split.split_immediately
                    : (c5_bound_target ? c5_split.split_immediately
                                       : split.should_split)));
            const bool child_infeasibility_trigger =
                c6_nonblocking
                    ? c6_split.child_infeasibility_trigger
                    : (c5_bound_target
                        ? c5_split.child_infeasibility_trigger
                        : split.child_infeasibility_trigger);
            const double post_split_bound =
                round38_force_frontier_evaluation
                    ? round38_split.b_plus
                    : (c6_nonblocking
                    ? c6_split.post_split_lower_bound
                    : (c5_bound_target ? c5_split.post_split_lower_bound
                                       : split.post_split_lower_bound));
            const std::string split_reason =
                round38_force_frontier_evaluation
                    ? round38_split.reason
                    : (round37_force_prefinement
                    ? "round37_pilot_weakest_midpoint_prefinement"
                    : (c6_nonblocking
                    ? c6_split.reason
                    : (c5_bound_target ? c5_split.reason : split.reason)));
            bound_ledger << bounded.id << ',' << bounded.lower_bound << ','
                         << children[0].id << ','
                         << runtime[children[0].id].lp.lower_bound << ','
                         << runtime[children[0].id].lp.infeasible << ','
                         << children[1].id << ','
                         << runtime[children[1].id].lp.lower_bound << ','
                         << runtime[children[1].id].lp.infeasible << ','
                         << post_split_bound << ','
                         << scheduler.certificateTolerance() << ','
                         << csvField(split_reason) << '\n';
            split_ledger << bounded.id << ",true," << decision_valid << ','
                         << split_immediately << ','
                         << child_infeasibility_trigger << ','
                         << (!c5_bound_target && !c6_nonblocking &&
                             split.strict_bound_improvement_trigger)
                         << ',';
            if (c6_nonblocking &&
                std::isfinite(c6_split.normalized_disjunction_gain)) {
                split_ledger << c6_split.normalized_disjunction_gain;
            } else if (c5_bound_target &&
                       std::isfinite(
                           c5_split.normalized_disjunction_gain)) {
                split_ledger << c5_split.normalized_disjunction_gain;
            }
            split_ledger << ',';
            if (c6_nonblocking &&
                c6_split.run_child_bound_target) {
                split_ledger << c6_split.child_bound_target;
            } else if (c5_bound_target &&
                       c5_split.run_parent_bound_target_phase) {
                split_ledger << c5_split.parent_native_bound_target;
            }
            split_ledger << ','
                         << ((c6_nonblocking &&
                              c6_split.run_child_bound_target) ||
                             (c5_bound_target &&
                              c5_split.run_parent_bound_target_phase))
                         << ',' << csvField(split_reason) << ',';
            if (c6_nonblocking && std::isfinite(c6_split.b_plus)) {
                split_ledger << c6_split.b_plus;
            }
            split_ledger << ',';
            if (c6_nonblocking && std::isfinite(c6_split.eta_proof)) {
                split_ledger << c6_split.eta_proof;
            }
            split_ledger << ',';
            if (c6_nonblocking && std::isfinite(c6_split.eta_anchor)) {
                split_ledger << c6_split.eta_anchor;
            }
            split_ledger << ',';
            if (c6_nonblocking) {
                split_ledger << csvField(c6_split.normalization_source)
                             << ',' << c6_split.normalization_upper_bound;
            } else {
                split_ledger << ',';
            }
            split_ledger << '\n';
            if (!decision_valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "paper_split_decision_invalid:" + split_reason;
                break;
            }
            if (split_immediately) {
                std::string reason;
                if (!scheduler.splitLeafAtomically(
                        bounded.id, children, &reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "paper_atomic_split_failed:" + reason;
                    break;
                }
                ++result.external_gini_tree_split_count;
                if (round37_force_prefinement) {
                    round37_pilot_prefinement_pending = false;
                    result.round37_pilot_prefinement_performed = true;
                    ++result.round37_pilot_prefinement_count;
                }
                if (round38_force_frontier_evaluation) {
                    round38_frontier_pilot_pending = false;
                    result.round38_pilot_refinement_performed = true;
                    ++result.round38_pilot_refinement_count;
                }
                if (incremental_model_reuse) {
                    backend->discardLeaf(bounded.id);
                }
                for (const ControllingLeaf& child : children) {
                    if (runtime[child.id].lp.infeasible) {
                        if (!scheduler.setStatus(
                                child.id, ControllingLeafStatus::Empty,
                                "complete_child_lp_infeasible", &reason)) {
                            hard_failure = true;
                            result.external_gini_tree_failure_reason =
                                "paper_infeasible_child_closure_failed:" + reason;
                            break;
                        }
                        if (incremental_model_reuse) {
                            backend->discardLeaf(child.id);
                        }
                    }
                }
                events << elapsedTelemetry() << ",atomic_split," << bounded.id
                       << ',' << bounded.gamma_L << ',' << bounded.gamma_U
                       << ",replaced," << scheduler.globalLowerBound() << ','
                       << verified_ub << ',' << csvField(split_reason) << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "split", bounded.id,
                    std::numeric_limits<double>::infinity(),
                    scheduler.globalLowerBound(),
                    c6_nonblocking
                        ? (round38_force_frontier_evaluation
                            ? "round38_next_frontier_completing_refinement"
                            : (round37_force_prefinement
                            ? "round37_pilot_weakest_midpoint_prefinement"
                            : "c6_current_gain_atomic_split"))
                        : (c5_bound_target
                            ? "c5_immediate_atomic_split"
                            : "c4_atomic_split"));
                if (c6_nonblocking) {
                    selected_state.c6_children_ready = false;
                    selected_state.c6_cached_children.clear();
                }
                split_parent = true;
            } else if (round38_force_frontier_evaluation) {
                round38_frontier_pilot_pending = false;
                ++result.round38_pilot_rejection_count;
                backend->discardLeaf(children[0].id);
                backend->discardLeaf(children[1].id);
                selected_state.c6_children_ready = false;
                selected_state.c6_cached_children.clear();
                events << elapsedTelemetry()
                       << ",round38_frontier_refinement_rejected,"
                       << bounded.id << ',' << bounded.gamma_L << ','
                       << bounded.gamma_U << ",open,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(round38_split.reason) << '\n';
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "round38_frontier_refinement_rejected",
                    bounded.id, bounded.lower_bound,
                    round38_pilot_selection.next_strict_frontier,
                    round38_split.reason);
                const C6TargetDisposition disposition =
                    runC6NativeTarget(
                        bounded, selected_state,
                        round38_pilot_selection.next_strict_frontier,
                        "next_leaf",
                        "round38_rejected_pilot_resume_c6_next_frontier");
                if (disposition == C6TargetDisposition::Failed) {
                    hard_failure = true;
                    break;
                }
                if (disposition == C6TargetDisposition::Deadline) break;
                split_parent = true;
            } else if (c6_nonblocking &&
                       c6_split.run_child_bound_target) {
                const C6TargetDisposition disposition =
                    runC6NativeTarget(
                        bounded, selected_state,
                        c6_split.child_bound_target,
                        "child_disjunction",
                        "c6_child_bound_reached_parent_requeued_no_forced_split");
                if (disposition == C6TargetDisposition::Failed) {
                    hard_failure = true;
                    break;
                }
                if (disposition == C6TargetDisposition::Deadline) break;
                split_parent = true;
            } else if (c5_bound_target &&
                       c5_split.run_parent_bound_target_phase) {
                const double remaining = globalDeadlineRemaining();
                if (remaining <= 0.0) {
                    stopAtDeadline();
                    break;
                }
                selected_state.c5_partial_target_started = true;
                selected_state.c5_native_target =
                    c5_split.parent_native_bound_target;
                FixedIntervalMipRequest request;
                request.solve_kind =
                    FixedIntervalSolveKind::PaperPartialBoundTargetMip;
                request.leaf_id = bounded.id;
                request.gamma_L = bounded.gamma_L;
                request.gamma_U = bounded.gamma_U;
                request.verified_cutoff = verified_seed.objective;
                request.global_deadline_remaining_seconds = remaining;
                request.new_leaf = false;
                request.warm_start_enabled = false;
                request.canonical_model_path =
                    selected_state.artifact.path;
                request.canonical_model_fingerprint =
                    selected_state.artifact.sha256;
                request.canonical_model_scope =
                    selected_state.artifact.model_scope;
                request.canonical_row_signature =
                    selected_state.artifact.row_signature;
                request.native_log_path = artifact_dir / "native_logs" /
                    (bounded.id + "_partial_target_mip.gurobi.log");
                request.incremental_model_reuse_enabled = true;
                request.retain_model_after_solve = true;
                request.native_bound_target_enabled = true;
                request.native_bound_target =
                    c5_split.parent_native_bound_target;
                request.native_bound_target_tolerance =
                    scheduler.certificateTolerance();
                request.capture_native_bound_events = true;
                const double process_launch =
                    processElapsedSeconds(options);
                const double exact_launch = elapsedTelemetry();
                const double other_bound =
                    otherRelevantMinimum(bounded.id);
                const FixedIntervalMipOutcome outcome =
                    backend->solve(request);
                optimize << bounded.id << ",PARTIAL_MIP_TARGET,"
                         << csvField(outcome.native_status) << ','
                         << outcome.optimize_return_code << ',' << remaining
                         << ',' << outcome.solver_runtime_seconds << ','
                         << outcome.work << ',' << outcome.nodes << ','
                         << outcome.simplex_iterations << ','
                         << outcome.barrier_iterations << ','
                         << outcome.memory_gb << ','
                         << selected_state.artifact.sha256 << ','
                         << outcome.in_memory_model_reused << ','
                         << outcome.integer_domain_restored << ','
                         << csvField(outcome.basis_reuse_status) << ','
                         << csvField(outcome.native_log_path) << '\n';
                for (const FixedIntervalNativeBoundEvent& native_event :
                        outcome.native_bound_events) {
                    if (!native_event.native_bound_available ||
                        (!native_event.bound_improved &&
                         !native_event.target_reached)) {
                        continue;
                    }
                    writeGlobalTrace(
                        process_launch +
                            native_event.solver_runtime_seconds,
                        exact_launch +
                            native_event.solver_runtime_seconds,
                        native_event.target_reached
                            ? "partial_native_bound_target"
                            : (native_event.processed_nodes <= 0.0
                                ? "native_root_processing_bound"
                                : "partial_native_mip_bound_improvement"),
                        bounded.id,
                        std::max(
                            bounded.lower_bound,
                            native_event.native_bound),
                        other_bound,
                        "gurobi_cb_mip_objbnd_valid_native_bound");
                }
                const bool engineering_valid =
                    outcome.attempted && outcome.available &&
                    outcome.solver_finalization_reached &&
                    outcome.model_fingerprint_matches_request &&
                    outcome.exact_zero_gap_roundtrip &&
                    outcome.feasibility_consistency_gate &&
                    outcome.partial_bound_target_mip;
                if (!engineering_valid) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "c5_partial_bound_target_engineering_gate_failed:" +
                        outcome.failure_reason;
                    break;
                }
                if (outcome.native_bound_available) {
                    std::string reason;
                    if (!scheduler.mergeValidLowerBound(
                            bounded.id, outcome.native_bound,
                            "valid_partial_native_mip_bound", &reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "c5_partial_native_bound_merge_failed:" + reason;
                        break;
                    }
                }
                if (outcome.incumbent_available &&
                    outcome.incumbent_independently_verified &&
                    outcome.incumbent_objective < verified_ub - 1e-9) {
                    verified_ub = outcome.incumbent_objective;
                    best_routes = outcome.incumbent_routes;
                    const ControllingLeaf* improved_leaf =
                        scheduler.findLeaf(bounded.id);
                    writeGlobalTrace(
                        processElapsedSeconds(options), elapsedTelemetry(),
                        "incumbent_improvement", bounded.id,
                        improved_leaf ? improved_leaf->lower_bound
                                      : bounded.lower_bound,
                        otherRelevantMinimum(bounded.id),
                        "independently_verified_partial_mip_incumbent");
                }
                if (outcome.optimal || outcome.infeasible) {
                    std::string reason;
                    const ControllingLeafStatus close_status =
                        outcome.infeasible
                            ? ControllingLeafStatus::Empty
                            : ControllingLeafStatus::Closed;
                    if (!scheduler.setStatus(
                            bounded.id, close_status,
                            outcome.infeasible
                                ? "c5_partial_phase_native_infeasible"
                                : "c5_partial_phase_native_optimal",
                            &reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "c5_partial_phase_closure_failed:" + reason;
                        break;
                    }
                    backend->discardLeaf(bounded.id);
                    backend->discardLeaf(children[0].id);
                    backend->discardLeaf(children[1].id);
                    writeGlobalTrace(
                        processElapsedSeconds(options), elapsedTelemetry(),
                        outcome.infeasible
                            ? "infeasible_closure"
                            : "terminal_mip_closure",
                        bounded.id,
                        std::numeric_limits<double>::infinity(),
                        scheduler.globalLowerBound(),
                        "c5_partial_phase_exact_native_closure");
                    split_parent = true;
                } else if (outcome.native_bound_target_reached &&
                           outcome.native_bound_target_termination_requested &&
                           outcome.native_bound_available &&
                           outcome.native_bound +
                                scheduler.certificateTolerance() >=
                                c5_split.parent_native_bound_target) {
                    const ControllingLeaf* strengthened =
                        scheduler.findLeaf(bounded.id);
                    if (!strengthened) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "c5_strengthened_parent_missing";
                        break;
                    }
                    for (ControllingLeaf& child : children) {
                        child.base_lower_bound = std::max(
                            child.base_lower_bound,
                            strengthened->lower_bound);
                        child.lower_bound = std::max(
                            child.lower_bound,
                            strengthened->lower_bound);
                        child.lower_bound_sources.push_back(
                            "inherited_parent_partial_native_bound");
                    }
                    selected_state.c5_partial_target_reached = true;
                    selected_state.c5_split_pending = true;
                    selected_state.c5_pending_children = children;
                    events << elapsedTelemetry()
                           << ",partial_native_bound_target_reached,"
                           << bounded.id << ',' << bounded.gamma_L << ','
                           << bounded.gamma_U << ",open,"
                           << scheduler.globalLowerBound() << ','
                           << verified_ub << ','
                           << csvField(
                                  "backend_certified_parent_bound_requeued")
                           << '\n';
                    writeGlobalTrace(
                        processElapsedSeconds(options), elapsedTelemetry(),
                        "partial_native_bound_target", bounded.id,
                        strengthened->lower_bound,
                        otherRelevantMinimum(bounded.id),
                        "c5_target_reached_parent_requeued_before_split");
                    split_parent = true;
                } else if (outcome.interrupted) {
                    stopAtDeadline();
                    break;
                } else {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "c5_partial_bound_target_status_invalid:" +
                        outcome.native_status;
                    break;
                }
            } else if (incremental_model_reuse) {
                ++result.external_gini_tree_declined_split_count;
                backend->discardLeaf(children[0].id);
                backend->discardLeaf(children[1].id);
                if (c6_nonblocking) {
                    selected_state.c6_children_ready = false;
                    selected_state.c6_cached_children.clear();
                }
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "declined_split", bounded.id, bounded.lower_bound,
                    otherRelevantMinimum(bounded.id),
                    c6_nonblocking
                        ? "c6_current_child_gain_not_strict_exact_closure"
                        : (c5_bound_target
                            ? "c5_no_strict_child_disjunction_gain"
                            : "c4_no_certified_one_level_lp_benefit"));
            }
        } else {
            split_ledger << bounded.id
                         << ",false,true,false,false,false,,,false,"
                         << csvField("structurally_terminal")
                         << ",,,,,\n";
        }
        if (hard_failure || global_deadline_stop || split_parent) continue;

        PaperLeafRuntime& terminal_state = runtime[bounded.id];
        if (terminal_state.terminal_mip_started) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "paper_same_leaf_terminal_mip_restart:" + bounded.id;
            break;
        }
        const double remaining = globalDeadlineRemaining();
        if (remaining <= 0.0) {
            stopAtDeadline();
            break;
        }
        // Classify a terminal-MIP leaf only when its one permitted native
        // optimize call is actually launched.  Reaching the global deadline
        // between the LP decision and this point leaves the leaf open without
        // creating a phantom optimize/lifecycle event.
        terminal_state.terminal_mip_started = true;
        ++result.external_gini_tree_terminal_mip_leaf_count;
        if (c6_nonblocking) {
            ++result.external_gini_tree_exact_closure_launch_count;
        }
        FixedIntervalMipRequest request;
        request.solve_kind = FixedIntervalSolveKind::PaperTerminalMip;
        request.leaf_id = bounded.id;
        request.gamma_L = bounded.gamma_L;
        request.gamma_U = bounded.gamma_U;
        request.verified_cutoff =
            c6_nonblocking ? verified_ub : verified_seed.objective;
        request.global_deadline_remaining_seconds = remaining;
        request.new_leaf = true;
        request.warm_start_enabled = false;
        request.canonical_model_path = terminal_state.artifact.path;
        request.canonical_model_fingerprint = terminal_state.artifact.sha256;
        request.canonical_model_scope = terminal_state.artifact.model_scope;
        request.canonical_row_signature = terminal_state.artifact.row_signature;
        request.native_log_path = artifact_dir / "native_logs" /
            (bounded.id + "_terminal_mip.gurobi.log");
        request.verified_start_routes.clear();
        request.incremental_model_reuse_enabled = incremental_model_reuse;
        request.retain_model_after_solve = false;
        request.capture_native_bound_events = true;
        const double terminal_process_launch =
            processElapsedSeconds(options);
        const double terminal_exact_launch = elapsedTelemetry();
        const double terminal_other_bound =
            otherRelevantMinimum(bounded.id);
        const FixedIntervalMipOutcome outcome = backend->solve(request);
        optimize << bounded.id << ",MIP," << csvField(outcome.native_status)
                 << ',' << outcome.optimize_return_code << ',' << remaining
                 << ',' << outcome.solver_runtime_seconds << ',' << outcome.work
                 << ',' << outcome.nodes << ',' << outcome.simplex_iterations
                 << ',' << outcome.barrier_iterations << ',' << outcome.memory_gb
                 << ',' << terminal_state.artifact.sha256 << ','
                 << outcome.in_memory_model_reused << ','
                 << outcome.integer_domain_restored << ','
                 << csvField(outcome.basis_reuse_status) << ','
                 << csvField(outcome.native_log_path) << '\n';
        for (const FixedIntervalNativeBoundEvent& native_event :
                outcome.native_bound_events) {
            if (!native_event.native_bound_available ||
                !native_event.bound_improved) {
                continue;
            }
            writeGlobalTrace(
                terminal_process_launch +
                    native_event.solver_runtime_seconds,
                terminal_exact_launch +
                    native_event.solver_runtime_seconds,
                native_event.processed_nodes <= 0.0
                    ? "native_root_processing_bound"
                    : "terminal_mip_bound_improvement",
                bounded.id,
                std::max(
                    bounded.lower_bound, native_event.native_bound),
                terminal_other_bound,
                "gurobi_cb_mip_objbnd_valid_native_bound");
        }
        const PaperTerminalMipDecision terminal =
            evaluatePaperTerminalMipDecision(outcome);
        if (!terminal.valid) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = terminal.reason + ":" +
                (outcome.failure_reason.empty() ? "none" : outcome.failure_reason);
            break;
        }
        if (outcome.native_bound_available) {
            std::string reason;
            if (!scheduler.mergeValidLowerBound(
                    bounded.id, outcome.native_bound,
                    "native_terminal_mip_bound", &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "paper_terminal_bound_merge_failed:" + reason;
                break;
            }
        }
        if (outcome.incumbent_available &&
            outcome.incumbent_independently_verified &&
            outcome.incumbent_objective < verified_ub - 1e-9) {
            verified_ub = outcome.incumbent_objective;
            best_routes = outcome.incumbent_routes;
            if (c6_nonblocking) {
                std::string cutoff_reason;
                if (!scheduler.tightenVerifiedCutoff(
                        verified_ub, &cutoff_reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "c6_terminal_verified_cutoff_tightening_failed:" +
                        cutoff_reason;
                    break;
                }
            }
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "incumbent_improvement", bounded.id,
                scheduler.findLeaf(bounded.id)
                    ? scheduler.findLeaf(bounded.id)->lower_bound
                    : bounded.lower_bound,
                otherRelevantMinimum(bounded.id),
                "independently_verified_native_incumbent");
        }
        if (terminal.leave_open_and_stop) {
            writeGlobalTrace(
                processElapsedSeconds(options), elapsedTelemetry(),
                "interruption", bounded.id,
                scheduler.findLeaf(bounded.id)
                    ? scheduler.findLeaf(bounded.id)->lower_bound
                    : bounded.lower_bound,
                otherRelevantMinimum(bounded.id),
                "overall_process_deadline_terminal_mip");
            stopAtDeadline();
            break;
        }
        std::string close_reason;
        const ControllingLeafStatus close_status = outcome.infeasible
            ? ControllingLeafStatus::Empty : ControllingLeafStatus::Closed;
        if (!scheduler.setStatus(
                bounded.id, close_status, terminal.reason, &close_reason)) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "paper_terminal_leaf_closure_failed:" + close_reason;
            break;
        }
        events << elapsedTelemetry() << ",terminal_mip_complete," << bounded.id
               << ',' << bounded.gamma_L << ',' << bounded.gamma_U << ','
               << csvField(outcome.native_status) << ','
               << scheduler.globalLowerBound() << ',' << verified_ub << ','
               << csvField(terminal.reason) << '\n';
        writeGlobalTrace(
            processElapsedSeconds(options), elapsedTelemetry(),
            outcome.infeasible
                ? "infeasible_closure"
                : "terminal_mip_closure",
            bounded.id, std::numeric_limits<double>::infinity(),
            scheduler.globalLowerBound(), terminal.reason);
        if (scheduler.globalLowerBound() > global_before +
                scheduler.certificateTolerance()) {
            last_global_lb_improvement = elapsedTelemetry();
        }
    }

    std::ofstream leaves(leaf_path);
    leaves << "leaf_id,parent_id,depth,child_index,gamma_L,gamma_U,"
              "base_lower_bound,lower_bound,status,lp_complete,lp_optimal,"
              "lp_infeasible,lp_bound,terminal_mip_started,"
              "c6_native_phase_count,c6_frontier_milestone_reached,"
              "c6_children_ready,closure_source,"
              "lower_bound_sources\n";
    long long final_count = 0;
    long long open_count = 0;
    long long closed_count = 0;
    bool all_bounds_valid = true;
    for (const ControllingLeaf& leaf : scheduler.leaves()) {
        const auto state_it = runtime.find(leaf.id);
        const PaperLeafRuntime* state = state_it == runtime.end()
            ? nullptr : &state_it->second;
        std::ostringstream sources;
        for (std::size_t index = 0; index < leaf.lower_bound_sources.size();
             ++index) {
            if (index) sources << ';';
            sources << leaf.lower_bound_sources[index];
        }
        leaves << leaf.id << ',' << csvField(leaf.parent_id) << ','
               << leaf.split_depth << ',' << leaf.child_index << ','
               << std::setprecision(17) << leaf.gamma_L << ',' << leaf.gamma_U
               << ',' << leaf.base_lower_bound << ',' << leaf.lower_bound << ','
               << controllingLeafStatusName(leaf.status) << ','
               << (state && state->lp_complete) << ','
               << (state && state->lp.optimal) << ','
               << (state && state->lp.infeasible) << ','
               << (state ? state->lp.lower_bound : 0.0) << ','
               << (state && state->terminal_mip_started) << ','
               << (state ? state->c6_native_phase_count : 0) << ','
               << (state && state->c6_frontier_milestone_reached) << ','
               << (state && state->c6_children_ready) << ','
               << csvField(leaf.closure_source) << ','
               << csvField(sources.str()) << '\n';
        if (leaf.status == ControllingLeafStatus::Replaced ||
            leaf.parent_replaced) continue;
        ++final_count;
        all_bounds_valid = all_bounds_valid && std::isfinite(leaf.lower_bound);
        if (leaf.status == ControllingLeafStatus::Open ||
            leaf.status == ControllingLeafStatus::Invalid) {
            ++open_count;
        } else {
            ++closed_count;
        }
    }

    std::string coverage_reason;
    result.external_gini_tree_parent_child_coverage_valid =
        scheduler.parentChildCoverageValid(&coverage_reason);
    result.external_gini_tree_all_relevant_leaves_closed =
        scheduler.everyRelevantLeafClosed();
    result.external_gini_tree_all_leaf_bounds_valid = all_bounds_valid;
    result.external_gini_tree_leaf_bounds_monotone =
        scheduler.leafBoundsMonotone();
    result.external_gini_tree_global_bound_monotone =
        scheduler.globalBoundMonotone();
    result.external_gini_tree_global_lower_bound = scheduler.globalLowerBound();
    result.external_gini_tree_verified_upper_bound = verified_ub;
    result.external_gini_tree_final_leaf_count = final_count;
    result.external_gini_tree_open_leaf_count = open_count;
    result.external_gini_tree_closed_leaf_count = closed_count;
    result.lower_bound = scheduler.globalLowerBound();
    result.upper_bound = verified_ub;
    result.routes = best_routes;
    result.verification = verifySolution(instance, best_routes, options.lambda);
    result.objective = result.verification.objective;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.final_inventory = result.verification.final_inventory;
    result.gap = std::fabs(verified_ub) > 1e-12
        ? std::max(0.0, (verified_ub - result.lower_bound) /
                         std::fabs(verified_ub))
        : 0.0;
    result.external_gini_tree_feasibility_consistency_gate =
        result.verification.original_solution_feasible &&
        result.verification.original_objective_recomputed &&
        result.verification.errors.empty();
    writeGlobalTrace(
        processElapsedSeconds(options), elapsedTelemetry(),
        "finalization", "", result.lower_bound,
        std::numeric_limits<double>::infinity(),
        hard_failure
            ? "hard_failure_final_valid_bound"
            : (global_deadline_stop
                ? "graceful_deadline_final_valid_bound"
                : "completed_exact_tree_final_bound"));
    backend->release();
    copyPaperBackendStats(result, backend->stats());
    result.external_gini_tree_model_build_seconds += total_model_build_seconds;
    result.external_gini_tree_canonical_artifact_generation_seconds =
        total_model_build_seconds;
    result.external_gini_tree_final_stagnation_seconds =
        last_global_lb_improvement >= 0.0
            ? std::max(0.0, elapsedTelemetry() - last_global_lb_improvement)
            : elapsedTelemetry();
    result.external_gini_tree_lifecycle_complete = !hard_failure &&
        result.external_gini_tree_optimize_count ==
            result.external_gini_tree_lp_optimize_count +
            result.external_gini_tree_partial_mip_optimize_count +
            result.external_gini_tree_terminal_mip_optimize_count &&
        result.external_gini_tree_terminal_mip_leaf_count ==
            result.external_gini_tree_terminal_mip_optimize_count &&
        result.external_gini_tree_model_count ==
            result.external_gini_tree_model_free_count &&
        result.external_gini_tree_environment_count ==
            result.external_gini_tree_environment_free_count &&
        (incremental_model_reuse
            ? result.external_gini_tree_same_leaf_resume_count ==
                result.external_gini_tree_in_memory_model_reuse_count
            : result.external_gini_tree_same_leaf_resume_count == 0) &&
        (!incremental_model_reuse ||
            result.external_gini_tree_integer_domain_restore_count ==
                result.external_gini_tree_lp_optimize_count) &&
        result.external_gini_tree_fresh_restart_count == 0 &&
        result.external_gini_tree_child_restart_count == 0 &&
        result.external_gini_tree_reset_call_count == 0;

    ExternalGiniTreeCertificateInput certificate_input;
    certificate_input.complete_root_coverage =
        result.external_gini_tree_root_coverage_valid;
    certificate_input.parent_child_coverage_valid =
        result.external_gini_tree_parent_child_coverage_valid;
    certificate_input.all_relevant_leaves_closed =
        result.external_gini_tree_all_relevant_leaves_closed;
    certificate_input.all_leaf_bounds_valid = all_bounds_valid;
    certificate_input.global_bound_valid = std::isfinite(result.lower_bound);
    certificate_input.global_bound_monotone =
        result.external_gini_tree_global_bound_monotone;
    certificate_input.leaf_bounds_monotone =
        result.external_gini_tree_leaf_bounds_monotone;
    certificate_input.verified_global_ub =
        result.external_gini_tree_feasibility_consistency_gate;
    certificate_input.lifecycle_complete =
        result.external_gini_tree_lifecycle_complete;
    certificate_input.feasibility_consistency_gate =
        result.external_gini_tree_feasibility_consistency_gate;
    certificate_input.global_lb = result.lower_bound;
    certificate_input.verified_ub = verified_ub;
    certificate_input.tolerance = scheduler.certificateTolerance();
    const ExternalGiniTreeCertificateDecision certificate =
        evaluateExternalGiniTreeCertificate(certificate_input);
    result.external_gini_tree_strict_certified = certificate.certified;
    result.external_gini_tree_certificate_class = certificate.certificate_class;
    result.external_gini_tree_certificate_rejection_reason =
        certificate.rejection_reason;
    result.strict_certified_original_problem = certificate.certified;
    result.strict_certificate_class = certificate.certificate_class;
    result.strict_certificate_rejection_reason = certificate.rejection_reason;
    result.strict_lower_bound_source =
        c6_nonblocking
            ? "minimum_valid_inherited_lp_open_native_target_or_exact_mip_"
              "bound_over_round31_c6_leaves"
            : (c5_bound_target
                ? "minimum_valid_inherited_lp_partial_native_or_exact_mip_"
                  "bound_over_round30_c5_leaves"
                : "minimum_valid_inherited_lp_or_terminal_mip_bound_over_"
                  "paper_leaves");
    result.status = certificate.certified
        ? "optimal"
        : (hard_failure
            ? (c6_nonblocking
                ? "round31_c6_external_gini_tree_failed"
                : (c5_bound_target
                    ? "round30_c5_external_gini_tree_failed"
                    : (c4_incremental
                        ? "round29_c4_external_gini_tree_failed"
                        : "paper_external_gini_tree_failed")))
            : (global_deadline_stop
                ? (c6_nonblocking
                    ? "round31_c6_external_gini_tree_time_limit"
                    : (c5_bound_target
                        ? "round30_c5_external_gini_tree_time_limit"
                        : (c4_incremental
                            ? "round29_c4_external_gini_tree_time_limit"
                            : "paper_external_gini_tree_time_limit")))
                : (c6_nonblocking
                    ? "round31_c6_external_gini_tree_not_certified"
                    : (c5_bound_target
                        ? "round30_c5_external_gini_tree_not_certified"
                        : (c4_incremental
                            ? "round29_c4_external_gini_tree_not_certified"
                            : "paper_external_gini_tree_not_certified")))));
    result.certificate = certificate.certified
        ? (c6_nonblocking
            ? "Round 31 C6 engineering-exact certificate: complete range and "
              "atomic coverage, parameter-free strict-frontier native-bound "
              "targets, lazy current-bound child decisions, open-parent "
              "requeue without forced delayed splits, exact closures, "
              "monotone valid bounds, symmetric model lifecycle, and "
              "independently verified global incumbent."
            : (c5_bound_target
                ? "Round 30 C5 engineering-exact certificate: complete range "
                  "and atomic coverage, complete parent/child LP decisions, "
                  "validity-gated mathematical parent native-bound targets, "
                  "exact remaining MIPs, monotone valid bounds, symmetric "
                  "model lifecycle, and independently verified global "
                  "incumbent."
                : (c4_incremental
                    ? "Round 29 C4 engineering-exact certificate: complete "
                      "range and atomic coverage, complete parent/child LP "
                      "benefit decisions, exact unsplit-parent terminal MIPs, "
                      "monotone valid bounds, same-leaf model lifecycle "
                      "symmetry, and independently verified global incumbent."
                    : "Round 27 engineering-exact paper external-tree "
                      "certificate: exact interval coverage, complete optimal "
                      "LP event decisions, exactly-once terminal MIPs, every "
                      "relevant leaf closed, monotone valid bounds, completed "
                      "no-restart lifecycle, and independently verified "
                      "global incumbent.")))
        : "Paper external-tree strict certificate rejected: " +
            certificate.rejection_reason;
    if (result.external_gini_tree_failure_reason.empty()) {
        result.external_gini_tree_failure_reason = "none";
    }
    result.runtime_seconds = elapsedTelemetry();
    result.wall_time_seconds = result.runtime_seconds;
    result.actual_runtime_seconds = result.runtime_seconds;
    result.graceful_deadline_finalization = global_deadline_stop &&
        !hard_failure;
    return result;
}

} // namespace ebrp
