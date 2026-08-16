#include "PaperExternalGiniTree.hpp"

#include "CanonicalCompactModel.hpp"
#include "ConnectivityFlow.hpp"
#include "ControllingLeafScheduler.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"
#include "GiniEnvelopeRefinement.hpp"
#include "ProcessPhaseLedger.hpp"
#include "StaticSegmentedGini.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <set>
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

std::string joinLongLongs(const std::vector<long long>& values) {
    std::ostringstream out;
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
    bool terminal_ready = false;
    bool c5_partial_target_started = false;
    bool c5_partial_target_reached = false;
    bool c5_split_pending = false;
    double c5_native_target = 0.0;
    std::vector<ControllingLeaf> c5_pending_children;
    int c6_native_phase_count = 0;
    bool c6_frontier_milestone_reached = false;
    bool c6_children_ready = false;
    std::vector<ControllingLeaf> c6_cached_children;
    std::vector<GiniEnvelopeFacet> round43_inherited_facets;
    bool round43_lp_g_available = false;
    double round43_lp_g = 0.0;
    bool round43_lp_objective_available = false;
    double round43_lp_objective = 0.0;
    double round43_lp_work = 0.0;
};

long long round43WidthComponentCount(const Instance& instance) {
    long long count = 1; // the G interval itself
    for (int i = 1; i <= instance.V; ++i) {
        int bits = 1;
        while (((1LL << bits) - 1) < instance.capacity[i]) ++bits;
        count += bits; // one G-times-inventory-bit McCormick range per bit
    }
    return count;
}

double round43WidthMeasure(
        const GiniIntervalGeometry& interval,
        const GiniIntervalGeometry& root,
        long long component_count) {
    const double root_width = root.upper - root.lower;
    if (!(interval.upper > interval.lower) || !(root_width > 0.0) ||
        component_count <= 0) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    return static_cast<double>(component_count) *
        (interval.upper - interval.lower) / root_width;
}

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
    const std::string& coarse_start = options.round40_c6_coarse_start;
    const bool coarse_start_valid = coarse_start == "off" ||
        coarse_start == "k1-single" || coarse_start == "k1-adaptive" ||
        coarse_start == "k1-adaptive-decisive";
    if (!coarse_start_valid) {
        reason = "c6_round40_coarse_start_policy_unknown";
        return false;
    }
    if (coarse_start != "off" &&
        (!hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" ||
         options.round40_c6_ub_geometry != "off" ||
         options.round41_static_segmented_gini != "off" ||
         options.gurobi_presolve != -1)) {
        reason = "c6_round40_coarse_start_contract_mismatch";
        return false;
    }
    const std::string& ub_geometry = options.round40_c6_ub_geometry;
    if (ub_geometry != "off" && ub_geometry != "nested-dyadic-k4") {
        reason = "c6_round40_ub_geometry_policy_unknown";
        return false;
    }
    if (ub_geometry != "off" &&
        (!hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" || coarse_start != "off" ||
         options.round41_static_segmented_gini != "off" ||
         options.gurobi_presolve != -1)) {
        reason = "c6_round40_ub_geometry_contract_mismatch";
        return false;
    }
    const std::string& static_segmented =
        options.round41_static_segmented_gini;
    const std::string& root_reference =
        options.round41_root_reference_interval;
    const bool static_segmented_valid = static_segmented == "off" ||
        static_segmented == "st-k2-i" ||
        static_segmented == "st-k2-p-core" ||
        static_segmented == "st-k2-p-extended";
    if (!static_segmented_valid) {
        reason = "c6_round41_static_segmented_policy_unknown";
        return false;
    }
    if (static_segmented != "off" &&
        (!hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" || coarse_start != "off" ||
         ub_geometry != "off" || options.gurobi_presolve != -1 ||
         (options.round41_static_segmented_solve != "mip" &&
          options.round41_static_segmented_solve != "root-lp"))) {
        reason = "c6_round41_static_segmented_contract_mismatch";
        return false;
    }
    const bool root_reference_valid = root_reference == "off" ||
        root_reference == "k1" || root_reference == "left" ||
        root_reference == "right";
    if (!root_reference_valid) {
        reason = "c6_round41_root_reference_policy_unknown";
        return false;
    }
    if (root_reference != "off" &&
        (!hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" || coarse_start != "off" ||
         ub_geometry != "off" || static_segmented != "off" ||
         options.gurobi_presolve != -1)) {
        reason = "c6_round41_root_reference_contract_mismatch";
        return false;
    }
    const std::set<std::string> round42_static_arms = {
        "off", "st-k4-p-core", "st-k4-p-core-hierarchical",
        "st-k4-p-core-factored", "external-k2-left",
        "external-k2-right", "paired-k4-lower", "paired-k4-upper",
        "paired-k4-lower-factored", "paired-k4-upper-factored",
    };
    const std::string& round42_static =
        options.round42_static_architecture;
    const std::string& round42_siblings =
        options.round42_terminal_sibling_coalescing;
    if (!round42_static_arms.count(round42_static) ||
        (options.round42_static_solve != "mip" &&
         options.round42_static_solve != "root-lp") ||
        (round42_siblings != "off" && round42_siblings != "core" &&
         round42_siblings != "core-factored")) {
        reason = "c6_round42_architecture_policy_unknown";
        return false;
    }
    const bool round42_any = round42_static != "off" ||
        round42_siblings != "off";
    if (round42_any &&
        (!hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" || coarse_start != "off" ||
         ub_geometry != "off" || static_segmented != "off" ||
         root_reference != "off" || options.gurobi_presolve != -1 ||
         (round42_static != "off" && round42_siblings != "off"))) {
        reason = "c6_round42_architecture_contract_mismatch";
        return false;
    }
    const bool round43_active =
        options.round43_envelope_refinement != "off";
    if (round43_active &&
        (options.round43_envelope_refinement != "atlas" &&
         options.round43_envelope_refinement != "algorithm")) {
        reason = "round43_execution_mode_unknown";
        return false;
    }
    if (round43_active &&
        ((options.round43_initial_k0 != 1 &&
          options.round43_initial_k0 != 4) ||
         (options.round43_lookahead_depth != 1 &&
          options.round43_lookahead_depth != 2) ||
         !std::isfinite(options.round43_rho) ||
         options.round43_rho < 0.0 || options.round43_rho > 1.0 ||
         options.round43_width_measure != "g-mccormick-unit" ||
         options.round43_lifted_cuts != "off" ||
         options.round43_frontier_consolidation != "off" ||
         !hga_full || causal != "off" || normalization != "proof" ||
         geometry_policy != "off" || coarse_start != "off" ||
         ub_geometry != "off" || static_segmented != "off" ||
         root_reference != "off" || round42_any ||
         options.gurobi_presolve != -1)) {
        reason = "round43_unified_envelope_contract_mismatch";
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
        "_round37_" + geometry_policy + "_round40_" + coarse_start +
        "_ub_geometry_" + ub_geometry + "_round41_" + static_segmented +
        "_root_reference_" + root_reference + "_round42_static_" +
        round42_static + "_siblings_" + round42_siblings +
        "_round43_" + options.round43_envelope_refinement;
    return true;
}

void copyPaperBackendStats(SolveResult& result,
                           const FixedIntervalMipBackendStats& stats) {
    result.gurobi_threads_requested = stats.threads_requested;
    result.gurobi_threads_set_return_code = stats.threads_set_return_code;
    result.gurobi_threads_get_return_code = stats.threads_get_return_code;
    result.gurobi_threads_effective = stats.threads_effective;
    result.gurobi_presolve_requested = stats.presolve_requested;
    result.gurobi_presolve_set_return_code = stats.presolve_set_return_code;
    result.gurobi_presolve_get_return_code = stats.presolve_get_return_code;
    result.gurobi_presolve_effective = stats.presolve_effective;
    result.gurobi_seed_requested = stats.seed_requested;
    result.gurobi_seed_set_return_code = stats.seed_set_return_code;
    result.gurobi_seed_get_return_code = stats.seed_get_return_code;
    result.gurobi_seed_effective = stats.seed_effective;
    result.gurobi_mip_gap_requested = stats.mip_gap_requested;
    result.gurobi_mip_gap_set_return_code = stats.mip_gap_set_return_code;
    result.gurobi_mip_gap_get_return_code = stats.mip_gap_get_return_code;
    result.gurobi_mip_gap_effective = stats.mip_gap_effective;
    result.gurobi_mip_gap_abs_requested = stats.mip_gap_abs_requested;
    result.gurobi_mip_gap_abs_set_return_code =
        stats.mip_gap_abs_set_return_code;
    result.gurobi_mip_gap_abs_get_return_code =
        stats.mip_gap_abs_get_return_code;
    result.gurobi_mip_gap_abs_effective = stats.mip_gap_abs_effective;
    result.external_gini_tree_backend_parameter_roundtrip_valid =
        stats.parameter_roundtrip_valid;
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

SolveResult solveRound41RootReference(
    const Instance& instance,
    const SolveOptions& options,
    const SolveResult& verified_seed,
    double root_gamma_L,
    double root_gamma_U,
    SolveResult result,
    std::unique_ptr<FixedIntervalMipBackend> backend,
    const std::filesystem::path& artifact_dir) {
    const Round41StaticK2Geometry geometry =
        makeRound41StaticK2Geometry(root_gamma_L, root_gamma_U, 1e-9);
    result.method = "round41-fixed-interval-root-reference";
    result.frontier_execution_mode = "fixed-interval-root-reference";
    result.certificate_scope = "diagnostic_lp_only";
    result.external_gini_tree_attempted = false;
    result.round41_root_reference_interval =
        options.round41_root_reference_interval;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason =
        "diagnostic_root_lp_never_issues_original_problem_certificate";
    result.external_gini_tree_algorithm_arm =
        "R41-ROOT-REFERENCE-" +
        options.round41_root_reference_interval;
    if (!geometry.valid || !backend || !backend->capabilities().available) {
        result.status = "round41_root_reference_invalid_or_unavailable";
        result.round41_static_failure_reason = !geometry.valid
            ? geometry.reason : (backend
                ? backend->capabilities().failure_reason
                : "gurobi_backend_factory_failed");
        return result;
    }

    GiniIntervalGeometry interval{root_gamma_L, root_gamma_U};
    if (options.round41_root_reference_interval == "left") {
        interval = geometry.segments[0];
    } else if (options.round41_root_reference_interval == "right") {
        interval = geometry.segments[1];
    }
    result.round41_static_segmented_gamma_lower = interval.lower;
    result.round41_static_segmented_gamma_upper = interval.upper;
    result.round41_static_segmented_midpoint = geometry.midpoint;
    result.round41_static_segmented_intervals = joinIntervals({interval});

    CanonicalCompactModelSpec spec;
    spec.strengthened = true;
    spec.interval_restricted = true;
    spec.gamma_L = interval.lower;
    spec.gamma_U = interval.upper;
    spec.add_verified_incumbent_row = true;
    spec.verified_incumbent = verified_seed.objective;
    spec.incumbent_epsilon = 0.0;
    const std::filesystem::path model_path = artifact_dir / "models" /
        ("root-reference-" + options.round41_root_reference_interval + ".lp");
    const auto build_started = PaperClock::now();
    const CanonicalCompactModelArtifact artifact =
        writeCanonicalCompactModel(instance, options, model_path, spec);
    result.round41_static_model_build_seconds =
        std::chrono::duration<double>(
            PaperClock::now() - build_started).count();
    result.round41_static_segmented_model_path = artifact.path.string();
    result.round41_static_segmented_model_sha256 = artifact.sha256;
    result.round41_static_segmented_model_scope = artifact.model_scope;
    if (!artifact.written) {
        result.status = "round41_root_reference_model_build_failed";
        result.round41_static_failure_reason = artifact.failure_reason;
        backend->release();
        copyPaperBackendStats(result, backend->stats());
        return result;
    }

    double remaining = processDeadlineConfigured(options)
        ? processWorkRemainingSeconds(options) : options.solve_time_limit;
    if (!(remaining > 0.0)) {
        result.status = "round41_root_reference_global_deadline";
        result.round41_static_failure_reason = "no_root_lp_time_remaining";
        backend->release();
        copyPaperBackendStats(result, backend->stats());
        return result;
    }
    FixedIntervalMipRequest request;
    request.solve_kind = FixedIntervalSolveKind::PaperLpRelaxation;
    request.leaf_id = "round41_root_reference_" +
        options.round41_root_reference_interval;
    request.gamma_L = interval.lower;
    request.gamma_U = interval.upper;
    request.verified_cutoff = verified_seed.objective;
    request.global_deadline_remaining_seconds = remaining;
    request.new_leaf = true;
    request.warm_start_enabled = false;
    request.canonical_model_path = artifact.path;
    request.canonical_model_fingerprint = artifact.sha256;
    request.canonical_model_scope = artifact.model_scope;
    request.canonical_row_signature = artifact.row_signature;
    request.native_log_path = artifact_dir / "native_logs" /
        ("root-reference-" + options.round41_root_reference_interval +
         ".gurobi.log");
    request.incremental_model_reuse_enabled = false;
    request.retain_model_after_solve = false;
    const FixedIntervalMipOutcome outcome = backend->solve(request);
    backend->release();
    const FixedIntervalMipBackendStats stats = backend->stats();
    copyPaperBackendStats(result, stats);

    result.round41_static_model_read_seconds = outcome.model_read_seconds;
    result.round41_static_model_variables = outcome.model_variable_count;
    result.round41_static_model_linear_constraints =
        outcome.model_linear_constraint_count;
    result.round41_static_model_nonzeros = outcome.model_nonzero_count;
    result.round41_static_model_binary_variables =
        outcome.model_binary_variable_count;
    result.round41_static_model_integer_variables =
        outcome.model_integer_variable_count;
    result.round41_static_model_continuous_variables =
        outcome.model_continuous_variable_count;
    result.round41_static_model_general_constraints =
        outcome.model_general_constraint_count;
    result.round41_static_presolved_size_available =
        outcome.presolved_model_size_available;
    result.round41_static_presolved_rows = outcome.presolved_row_count;
    result.round41_static_presolved_columns = outcome.presolved_column_count;
    result.round41_static_presolved_nonzeros = outcome.presolved_nonzero_count;
    result.round41_static_optimize_count = stats.optimize_count;
    result.round41_static_root_lp_bound_available =
        outcome.lp_relaxation && outcome.native_bound_available;
    result.round41_static_root_lp_bound = outcome.native_bound;
    result.round41_static_lp_diagnostics_available =
        outcome.lp_solution_diagnostics_available;
    result.round41_static_route_binary_fractionality =
        outcome.route_binary_fractionality;
    result.round41_static_visit_binary_fractionality =
        outcome.visit_binary_fractionality;
    result.round41_static_inventory_bit_fractionality =
        outcome.inventory_bit_fractionality;
    result.round41_static_mccormick_ambiguity = outcome.mccormick_ambiguity;
    result.round41_static_solver_runtime_seconds =
        outcome.solver_runtime_seconds;
    result.round41_static_solver_work = outcome.work;
    result.round41_static_solver_nodes = outcome.nodes;
    result.round41_static_peak_memory_gb = outcome.memory_gb;
    result.round41_static_native_status = outcome.native_status;
    result.round41_static_native_status_code = outcome.native_status_code;
    result.round41_static_native_bound_available =
        outcome.native_bound_available;
    result.round41_static_native_bound = outcome.native_bound;
    result.round41_static_parameter_roundtrip_valid =
        stats.parameter_roundtrip_valid && outcome.exact_zero_gap_roundtrip;
    result.round41_static_segmented_technical_feasible =
        outcome.attempted && outcome.available &&
        outcome.solver_finalization_reached &&
        outcome.model_fingerprint_matches_request &&
        outcome.lp_terminal_valid && outcome.native_bound_available &&
        outcome.lp_solution_diagnostics_available &&
        result.round41_static_parameter_roundtrip_valid;
    result.routes = verified_seed.routes;
    result.verification = verifySolution(
        instance, result.routes, options.lambda);
    result.objective = result.verification.objective;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.final_inventory = result.verification.final_inventory;
    result.lower_bound = outcome.native_bound_available
        ? outcome.native_bound : 0.0;
    result.upper_bound = verified_seed.objective;
    result.gap = std::max(
        0.0, (result.upper_bound - result.lower_bound) /
            std::max(1e-12, std::fabs(result.upper_bound)));
    result.round41_static_original_verifier_passed =
        result.verification.original_solution_feasible &&
        result.verification.original_objective_recomputed &&
        result.verification.errors.empty();
    result.status = result.round41_static_segmented_technical_feasible
        ? "round41_root_reference_complete"
        : "round41_root_reference_failed";
    result.round41_static_failure_reason =
        result.round41_static_segmented_technical_feasible
            ? "none" : (outcome.failure_reason.empty()
                ? "root_reference_gate_failed" : outcome.failure_reason);
    return result;
}

SolveResult solveStaticSegmentedGini(
    const Instance& instance,
    const SolveOptions& options,
    const SolveResult& verified_seed,
    double root_gamma_L,
    double root_gamma_U,
    SolveResult result,
    std::unique_ptr<FixedIntervalMipBackend> backend,
    const std::filesystem::path& artifact_dir) {
    const auto started = PaperClock::now();
    const bool round42 = options.round42_static_architecture != "off";
    const std::string architecture = round42
        ? options.round42_static_architecture
        : options.round41_static_segmented_gini;
    const std::string solve_mode = round42
        ? options.round42_static_solve
        : options.round41_static_segmented_solve;
    std::string geometry_reason;
    std::vector<GiniIntervalGeometry> segments;
    GiniIntervalGeometry block_union{root_gamma_L, root_gamma_U};
    bool common_row_factoring = false;
    bool hierarchical_selectors = false;
    bool full_global_cover = true;
    if (round42) {
        const std::vector<GiniIntervalGeometry> quarters =
            makeEqualStaticSegments(
                root_gamma_L, root_gamma_U, 4, 1e-9,
                &geometry_reason);
        if (!quarters.empty()) {
            if (architecture == "st-k4-p-core" ||
                architecture == "st-k4-p-core-hierarchical" ||
                architecture == "st-k4-p-core-factored") {
                segments = quarters;
                hierarchical_selectors = architecture ==
                    "st-k4-p-core-hierarchical";
                common_row_factoring = architecture ==
                    "st-k4-p-core-factored";
            } else if (architecture == "external-k2-left") {
                block_union = {quarters[0].lower, quarters[1].upper};
                segments = {block_union};
                full_global_cover = false;
            } else if (architecture == "external-k2-right") {
                block_union = {quarters[2].lower, quarters[3].upper};
                segments = {block_union};
                full_global_cover = false;
            } else if (architecture == "paired-k4-lower" ||
                       architecture == "paired-k4-lower-factored") {
                block_union = {quarters[0].lower, quarters[1].upper};
                segments = {quarters[0], quarters[1]};
                full_global_cover = false;
                common_row_factoring = architecture ==
                    "paired-k4-lower-factored";
            } else if (architecture == "paired-k4-upper" ||
                       architecture == "paired-k4-upper-factored") {
                block_union = {quarters[2].lower, quarters[3].upper};
                segments = {quarters[2], quarters[3]};
                full_global_cover = false;
                common_row_factoring = architecture ==
                    "paired-k4-upper-factored";
            }
        }
    } else {
        segments = makeEqualStaticSegments(
            root_gamma_L, root_gamma_U, 2, 1e-9, &geometry_reason);
    }
    SolveOptions block_options = options;
    block_options.interval_row_factory_round19 = true;
    const StaticSegmentedBlockSpec block_spec =
        makeStaticSegmentedBlockSpec(
            instance, block_options, block_union, segments,
            verified_seed.objective, 0.0,
            round42 ? "st-k2-p-core" : architecture,
            common_row_factoring, hierarchical_selectors, 1e-9);
    result.method = round42
        ? "round42-static-segmented-block"
        : "round41-static-segmented-gini";
    result.frontier_execution_mode = "static-single-tree-segmented";
    result.certificate_scope = full_global_cover
        ? "original_global_static_segmented_mip"
        : "exact_static_segmented_subrange_block";
    result.external_gini_tree_attempted = false;
    result.round41_static_segmented_attempted = true;
    result.round41_static_segmented_gini = round42
        ? "st-k2-p-core" : architecture;
    result.round41_static_segmented_solve = solve_mode;
    result.round41_static_segmented_gamma_lower = block_union.lower;
    result.round41_static_segmented_gamma_upper = block_union.upper;
    result.round41_static_segmented_midpoint =
        block_union.lower + 0.5 * (block_union.upper - block_union.lower);
    result.round41_static_segmented_intervals = joinIntervals(segments);
    result.round41_static_segmented_coverage_valid = block_spec.valid &&
        exactIntervalCoverage(
            block_union, segments, 1e-9);
    result.external_gini_tree_algorithm_arm = round42
        ? "R42-" + architecture
        : (architecture == "st-k2-i"
            ? "R41-ST-K2-I"
            : (architecture == "st-k2-p-core"
                ? "R41-ST-K2-P-CORE"
                : "R41-ST-K2-P-EXTENDED"));
    result.external_gini_tree_implementation_boundary =
        "one deterministic canonical static K2 model; every selector, "
        "indicator, perspective auxiliary, and strengthening row is present "
        "before optimize; no callback-created nodes or model mutation";
    result.external_gini_tree_selector_variable_count =
        static_cast<long long>(segments.size());
    result.external_gini_tree_contract_initial_interval_count =
        static_cast<long long>(segments.size());
    result.external_gini_tree_active_initial_intervals =
        result.round41_static_segmented_intervals;
    result.external_gini_tree_root_coverage_valid =
        result.round41_static_segmented_coverage_valid;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason =
        "round41_static_segmented_not_finalized";
    result.round42_static_architecture = options.round42_static_architecture;
    result.round42_static_solve = options.round42_static_solve;
    result.round42_static_attempted = round42;
    result.round42_block_full_global_cover = round42 && full_global_cover;
    result.round42_block_union_lower = block_union.lower;
    result.round42_block_union_upper = block_union.upper;
    result.round42_block_intervals = joinIntervals(segments);
    result.round42_common_row_factoring = common_row_factoring;
    result.round42_hierarchical_selectors = hierarchical_selectors;
    result.round42_static_model_identity =
        block_spec.deterministic_model_identity;
    if (!block_spec.valid ||
        !result.round41_static_segmented_coverage_valid) {
        result.status = "round41_static_segmented_invalid_geometry";
        result.round41_static_failure_reason = block_spec.valid
            ? geometry_reason : block_spec.reason;
        return result;
    }
    if (!backend || !backend->capabilities().available) {
        result.status = "round41_static_segmented_backend_unavailable";
        result.round41_static_failure_reason = backend
            ? backend->capabilities().failure_reason
            : "gurobi_backend_factory_failed";
        return result;
    }

    CanonicalCompactModelSpec spec;
    spec.strengthened = true;
    spec.interval_restricted = true;
    spec.gamma_L = block_union.lower;
    spec.gamma_U = block_union.upper;
    spec.add_verified_incumbent_row = true;
    spec.verified_incumbent = verified_seed.objective;
    spec.incumbent_epsilon = 0.0;
    spec.static_segmented_gini = round42
        ? "st-k2-p-core" : architecture;
    spec.static_segments = segments;
    spec.static_common_row_factoring = common_row_factoring;
    spec.static_hierarchical_selectors = hierarchical_selectors;
    spec.static_model_identity = block_spec.deterministic_model_identity;
    const std::filesystem::path model_path = artifact_dir / "models" /
        (architecture + ".lp");
    const auto build_started = PaperClock::now();
    const CanonicalCompactModelArtifact artifact =
        writeCanonicalCompactModel(instance, options, model_path, spec);
    result.round41_static_model_build_seconds =
        std::chrono::duration<double>(
            PaperClock::now() - build_started).count();
    result.round41_static_segmented_model_path = artifact.path.string();
    result.round41_static_segmented_model_sha256 = artifact.sha256;
    result.round41_static_segmented_model_scope = artifact.model_scope;
    result.round41_static_segmented_family_encoding =
        artifact.static_family_encoding;
    result.round41_static_segment_count = artifact.static_segment_count;
    result.round41_static_selector_variables =
        artifact.static_selector_variables;
    result.round41_static_perspective_variables =
        artifact.static_perspective_variables;
    result.round41_static_extended_variables =
        artifact.static_extended_variables;
    result.round41_static_indicator_rows = artifact.static_indicator_rows;
    result.round41_static_linear_rows = artifact.static_linear_rows;
    result.round42_factored_unconditional_rows =
        artifact.static_factored_unconditional_rows;
    result.round42_factored_weighted_rhs_rows =
        artifact.static_factored_weighted_rhs_rows;
    result.round42_factored_indicator_rows_removed =
        artifact.static_factored_indicator_rows_removed;
    result.round42_hierarchical_selector_variables =
        artifact.static_hierarchical_selector_variables;
    if (!artifact.written) {
        result.status = "round41_static_segmented_model_build_failed";
        result.round41_static_failure_reason = artifact.failure_reason;
        backend->release();
        copyPaperBackendStats(result, backend->stats());
        return result;
    }

    double remaining = options.solve_time_limit;
    if (processDeadlineConfigured(options)) {
        remaining = processWorkRemainingSeconds(options);
    }
    if (!(remaining > 0.0)) {
        result.status = "round41_static_segmented_global_deadline";
        result.round41_static_failure_reason =
            "no_exact_phase_time_remaining";
        backend->release();
        copyPaperBackendStats(result, backend->stats());
        return result;
    }
    FixedIntervalMipRequest request;
    request.solve_kind = solve_mode == "root-lp"
        ? FixedIntervalSolveKind::PaperLpRelaxation
        : FixedIntervalSolveKind::PaperTerminalMip;
    request.leaf_id = round42 ? "round42_" + architecture
                              : "round41_static_k2";
    request.gamma_L = block_union.lower;
    request.gamma_U = block_union.upper;
    request.verified_cutoff = verified_seed.objective;
    request.global_deadline_remaining_seconds = remaining;
    request.new_leaf = true;
    request.warm_start_enabled = false;
    request.canonical_model_path = artifact.path;
    request.canonical_model_fingerprint = artifact.sha256;
    request.canonical_model_scope = artifact.model_scope;
    request.canonical_row_signature = artifact.row_signature;
    request.native_log_path = artifact_dir / "native_logs" /
        (architecture + "_" + solve_mode + ".gurobi.log");
    request.incremental_model_reuse_enabled = false;
    request.retain_model_after_solve = false;
    request.capture_native_bound_events = true;
    const FixedIntervalMipOutcome outcome = backend->solve(request);
    backend->release();
    const FixedIntervalMipBackendStats backend_stats = backend->stats();
    copyPaperBackendStats(result, backend_stats);

    result.round41_static_model_read_seconds = outcome.model_read_seconds;
    result.round41_static_model_variables = outcome.model_variable_count;
    result.round41_static_model_linear_constraints =
        outcome.model_linear_constraint_count;
    result.round41_static_model_nonzeros = outcome.model_nonzero_count;
    result.round41_static_model_binary_variables =
        outcome.model_binary_variable_count;
    result.round41_static_model_integer_variables =
        outcome.model_integer_variable_count;
    result.round41_static_model_continuous_variables =
        outcome.model_continuous_variable_count;
    result.round41_static_model_general_constraints =
        outcome.model_general_constraint_count;
    result.round41_static_presolved_size_available =
        outcome.presolved_model_size_available;
    result.round41_static_presolved_rows = outcome.presolved_row_count;
    result.round41_static_presolved_columns = outcome.presolved_column_count;
    result.round41_static_presolved_nonzeros = outcome.presolved_nonzero_count;
    result.round41_static_optimize_count = backend_stats.optimize_count;
    result.round41_static_integer_proof_job_count =
        backend_stats.terminal_mip_optimize_count;
    result.round41_static_one_native_mip_job =
        solve_mode == "mip" &&
        backend_stats.optimize_count == 1 &&
        backend_stats.terminal_mip_optimize_count == 1 &&
        backend_stats.lp_relaxation_optimize_count == 0 &&
        backend_stats.model_count == 1 &&
        backend_stats.model_free_count == 1 &&
        backend_stats.environment_count == 1 &&
        backend_stats.environment_free_count == 1;
    result.round41_static_root_lp_bound_available =
        outcome.lp_relaxation && outcome.native_bound_available;
    result.round41_static_root_lp_bound = outcome.native_bound;
    result.round41_static_lp_diagnostics_available =
        outcome.lp_solution_diagnostics_available;
    result.round41_static_route_binary_fractionality =
        outcome.route_binary_fractionality;
    result.round41_static_visit_binary_fractionality =
        outcome.visit_binary_fractionality;
    result.round41_static_inventory_bit_fractionality =
        outcome.inventory_bit_fractionality;
    result.round41_static_selector_binary_fractionality =
        outcome.selector_binary_fractionality;
    result.round41_static_mccormick_ambiguity =
        outcome.mccormick_ambiguity;
    result.round41_static_segmented_mccormick_ambiguity =
        outcome.segmented_mccormick_ambiguity;
    result.round41_static_solver_runtime_seconds =
        outcome.solver_runtime_seconds;
    result.round41_static_solver_work = outcome.work;
    result.round41_static_solver_nodes = outcome.nodes;
    result.round41_static_peak_memory_gb = outcome.memory_gb;
    result.round41_static_native_status = outcome.native_status;
    result.round41_static_native_status_code = outcome.native_status_code;
    result.round41_static_native_bound_available =
        outcome.native_bound_available;
    result.round41_static_native_bound = outcome.native_bound;
    result.round41_static_parameter_roundtrip_valid =
        backend_stats.parameter_roundtrip_valid &&
        outcome.exact_zero_gap_roundtrip;
    result.round41_static_segmented_technical_feasible =
        outcome.attempted && outcome.available &&
        outcome.solver_finalization_reached &&
        outcome.model_fingerprint_matches_request &&
        result.round41_static_parameter_roundtrip_valid;

    std::vector<RoutePlan> best_routes = verified_seed.routes;
    double verified_upper = verified_seed.objective;
    if (outcome.incumbent_available &&
        outcome.incumbent_independently_verified &&
        outcome.incumbent_objective < verified_upper + 1e-9) {
        best_routes = outcome.incumbent_routes;
        verified_upper = std::min(verified_upper, outcome.incumbent_objective);
    }
    result.routes = best_routes;
    result.verification = verifySolution(instance, best_routes, options.lambda);
    result.objective = result.verification.objective;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.final_inventory = result.verification.final_inventory;
    result.lower_bound = outcome.native_bound_available
        ? outcome.native_bound : 0.0;
    result.upper_bound = verified_upper;
    result.external_gini_tree_global_lower_bound = result.lower_bound;
    result.external_gini_tree_verified_upper_bound = verified_upper;
    result.gap = std::fabs(verified_upper) > 1e-12
        ? std::max(0.0, (verified_upper - result.lower_bound) /
                         std::fabs(verified_upper))
        : std::max(0.0, verified_upper - result.lower_bound);
    result.round41_static_original_verifier_passed =
        result.verification.original_solution_feasible &&
        result.verification.original_objective_recomputed &&
        result.verification.errors.empty();

    if (solve_mode == "root-lp") {
        const bool valid_root_lp =
            result.round41_static_segmented_technical_feasible &&
            outcome.lp_terminal_valid && outcome.native_bound_available &&
            outcome.lp_solution_diagnostics_available;
        result.status = valid_root_lp
            ? "round41_static_segmented_root_lp_complete"
            : "round41_static_segmented_root_lp_failed";
        result.round41_static_failure_reason = valid_root_lp
            ? "none" : (outcome.failure_reason.empty()
                ? "root_lp_gate_failed" : outcome.failure_reason);
        result.strict_certificate_rejection_reason =
            "diagnostic_root_lp_never_issues_original_problem_certificate";
    } else {
        const bool exact_infeasible =
            result.round41_static_segmented_technical_feasible &&
            result.round41_static_one_native_mip_job && outcome.infeasible;
        const bool exact_feasible =
            result.round41_static_segmented_technical_feasible &&
            result.round41_static_one_native_mip_job &&
            outcome.native_exact_optimal && outcome.native_bound_available &&
            result.round41_static_original_verifier_passed &&
            std::fabs(outcome.native_bound - result.objective) <=
                1e-7 * std::max(1.0, std::fabs(result.objective));
        const bool exact_native = exact_infeasible || exact_feasible;
        result.round41_static_strict_certificate = exact_native;
        result.round42_block_strict_certificate = round42 && exact_native;
        result.strict_certified_original_problem =
            exact_feasible && full_global_cover;
        result.strict_certificate_class = exact_feasible && full_global_cover
            ? "strict_original_problem_certificate"
            : (exact_native
                ? (exact_infeasible
                    ? "strict_exact_infeasible_subrange_block_certificate"
                    : "strict_exact_subrange_block_certificate")
                            : "certificate_rejected");
        result.strict_certificate_rejection_reason = exact_native
            ? (full_global_cover ? "none"
                                 : "subrange_block_not_global_certificate")
            : (outcome.interrupted
                ? "round41_static_segmented_time_limit"
                : "round41_static_segmented_exactness_gate_failed");
        result.status = exact_native
            ? "optimal"
            : (outcome.interrupted
                ? "round41_static_segmented_time_limit"
                : "round41_static_segmented_failed");
        result.round41_static_failure_reason = exact_native
            ? "none" : (outcome.failure_reason.empty()
                ? result.strict_certificate_rejection_reason
                : outcome.failure_reason);
    }
    (void)started;
    return result;
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
    const bool round36_causal = c6_nonblocking &&
        options.round36_c6_causal_arm != "off";
    const bool round40_coarse_start = c6_nonblocking &&
        options.round40_c6_coarse_start != "off";
    const bool round40_nested_dyadic = c6_nonblocking &&
        options.round40_c6_ub_geometry == "nested-dyadic-k4";
    const bool round41_static_segmented = c6_nonblocking &&
        options.round41_static_segmented_gini != "off";
    const bool round41_root_reference = c6_nonblocking &&
        options.round41_root_reference_interval != "off";
    const bool round42_static_segmented = c6_nonblocking &&
        options.round42_static_architecture != "off";
    const bool round42_sibling_coalescing = c6_nonblocking &&
        options.round42_terminal_sibling_coalescing != "off";
    const bool round43_active = c6_nonblocking &&
        options.round43_envelope_refinement != "off";
    const bool round43_atlas = round43_active &&
        options.round43_envelope_refinement == "atlas";
    const double proof_incumbent_launch = verified_seed.objective;
    const double decomposition_anchor_launch = round36_causal
        ? verified_seed.round36_decomposition_anchor_launch
        : proof_incumbent_launch;
    const double gini_max_possible = instance.V > 0
        ? static_cast<double>(instance.V - 1) /
            static_cast<double>(instance.V)
        : 1.0;
    const double anchor_grid_upper = round40_nested_dyadic
        ? gini_max_possible
        : std::min(decomposition_anchor_launch, gini_max_possible);
    const AnchorGridDecomposition causal_grid = round36_causal
        ? makeProofRelevantAnchorGrid(
              root_gamma_L, root_gamma_U, anchor_grid_upper,
              options.frontier_intervals, 1e-7)
        : AnchorGridDecomposition{};
    const Round40CoarseStartGeometry round40_geometry =
        round40_coarse_start
            ? makeRound40CoarseStartGeometry(
                  root_gamma_L, root_gamma_U, options.frontier_intervals,
                  options.round40_c6_coarse_start, 1e-7)
            : Round40CoarseStartGeometry{};
    const Round40NestedDyadicGeometry round40_ub_geometry =
        round40_nested_dyadic
            ? makeRound40NestedDyadicGeometry(
                  root_gamma_L, root_gamma_U, gini_max_possible,
                  options.frontier_intervals, 1e-7)
            : Round40NestedDyadicGeometry{};
    const bool incremental_model_reuse =
        c4_incremental || c5_bound_target || c6_nonblocking;
    SolveResult result = verified_seed;
    result.exact_phase_started = true;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "external-gini-tree";
    result.certificate_scope = "original_global_gini_external_tree";
    result.external_gini_tree_attempted = true;
    result.external_gini_tree_backend = options.external_gini_backend;
    result.external_gini_tree_lifecycle = round42_sibling_coalescing
        ? "round42-c6-terminal-sibling-block"
        : (round43_active
        ? "round43-unified-envelope-refinement"
        : (c6_nonblocking
        ? "round31-open-native-bounded"
        : (c5_bound_target
            ? "round30-same-leaf-bound-target"
        : (c4_incremental
            ? "round29-same-leaf-in-memory-model"
            : "fresh-per-paper-event"))));
    result.external_gini_tree_scheduling =
        options.external_gini_scheduling;
    result.external_gini_tree_startup_variant = c6_nonblocking
        ? options.round34_c6_startup_variant : "not_applicable";
    result.round36_c6_causal_arm = options.round36_c6_causal_arm;
    result.round36_c6_split_normalization =
        options.round36_c6_split_normalization;
    result.round37_c6_geometry_policy =
        options.round37_c6_geometry_policy;
    result.round40_c6_coarse_start = options.round40_c6_coarse_start;
    result.round40_c6_ub_geometry = options.round40_c6_ub_geometry;
    result.round42_terminal_sibling_coalescing =
        options.round42_terminal_sibling_coalescing;
    result.round40_c6_nested_dyadic_level =
        round40_ub_geometry.dyadic_level;
    result.round40_c6_nested_dyadic_global_cell_count =
        round40_ub_geometry.global_cell_count;
    result.round40_c6_nested_dyadic_reason = round40_ub_geometry.reason;
    result.round41_static_segmented_gini =
        options.round41_static_segmented_gini;
    result.round41_static_segmented_solve =
        options.round41_static_segmented_solve;
    result.round41_root_reference_interval =
        options.round41_root_reference_interval;
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
            ? (round43_active
                ? "R43-A(K0=" +
                    std::to_string(options.round43_initial_k0) + ",d=" +
                    std::to_string(options.round43_lookahead_depth) +
                    ",rho=" + std::to_string(options.round43_rho) + ")"
                : (round42_sibling_coalescing
                ? (options.round42_terminal_sibling_coalescing ==
                        "core-factored"
                    ? "R42-C6-TERMINAL-SIBLING-CORE-FACTORED"
                    : "R42-C6-TERMINAL-SIBLING-CORE")
                : (round40_coarse_start
                ? (options.round40_c6_coarse_start == "k1-single"
                    ? "R40-K1-SINGLE"
                    : (options.round40_c6_coarse_start == "k1-adaptive"
                        ? "R40-K1-ADAPTIVE"
                        : "R40-K1-ADAPTIVE-DECISIVE"))
                : (round40_nested_dyadic
                ? "R40-NESTED-DYADIC-K4"
                : (round37_pilot_prefine
                ? "R37-PILOT-WEAKEST-PREFINE"
                : (round36_causal
                ? "R36-" + options.round36_c6_causal_arm
                : "C6-CANDIDATE"))))))
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
            !c6_nonblocking || round37_pilot_prefine ||
            (round40_coarse_start &&
             options.round40_c6_coarse_start != "k1-single");
        result.external_gini_tree_structural_split_unconditional = false;
        result.external_gini_tree_internal_budget_scheduling = false;
        result.external_gini_tree_native_tree_reuse_claimed = false;
        result.external_gini_tree_warm_start_enabled = false;
        result.external_gini_tree_selector_variable_count = 0;
        result.external_gini_tree_contract_initial_interval_count =
            round43_active ? options.round43_initial_k0
            : (round40_coarse_start ? 1
            : (round40_nested_dyadic
                ? static_cast<long long>(
                    round40_ub_geometry.active_intervals.size())
                : 4));
        result.external_gini_tree_contract_adaptive_max_depth = 8;
        result.external_gini_tree_contract_split_factor = 2;
        result.external_gini_tree_contract_minimum_width = 1e-4;
        result.external_gini_tree_certificate_tolerance = 1e-7;
        result.external_gini_tree_best_bound_tie_rule =
            "lower_bound,lower_endpoint,upper_endpoint,leaf_id";
        result.external_gini_tree_implementation_boundary = c6_nonblocking
            ? (round42_sibling_coalescing
              ? "unchanged C6 K4 launch, LP census, strict-frontier targets, "
                "requeues, child lookahead, adaptive splits, and verified "
                "incumbent semantics; when exact live siblings both reach "
                "the true integer terminal stage, atomically replace them "
                "by one exact static segmented Core block; incomplete blocks "
                "remain one union coverage object and build/validation "
                "failure restores the original leaves"
              : (round40_coarse_start
              ? (options.round40_c6_coarse_start == "k1-single"
                ? "one complete strict-improver Gini interval; complete root "
                  "LP followed by one exact terminal MIP; no midpoint child "
                  "lookahead or independent interval proof fragmentation"
                : (options.round40_c6_coarse_start == "k1-adaptive"
                ? "one complete strict-improver root interval; existing "
                  "complete midpoint-child LP evidence and rho=0.01 split "
                  "logic recursively create an exact nested partition; "
                  "declined refinement closes the coarser parent exactly"
                : "one complete strict-improver root interval; complete "
                  "midpoint-child LP evidence refines only for child "
                  "infeasibility or a disjunction bound reaching the verified "
                  "cutoff; all nondecisive evidence closes the coarser parent "
                  "exactly without a gain threshold"))
              : (round40_nested_dyadic
              ? "the verified incumbent only truncates the active prefix of "
                "a deterministic dyadic hierarchy rooted at the mathematical "
                "Gini maximum; choose the finest level with at most frozen "
                "K=4 active cells; preserve the unchanged C6 scheduler, "
                "rho split rule, atomic coverage, and exact closures"
              : (round37_pilot_prefine
              ? "complete all four initial LPs; select the weakest open cell "
                "by LP bound with structural geometry ties; perform exactly "
                "one complete-child midpoint pre-refinement; then resume the "
                "unchanged C6 strict-frontier, target, split, and closure path"
              : "complete parent LP then parameter-free next-strict-frontier "
              "native-bound targets; lazy complete child LPs only at the "
              "highest active frontier plateau; current rho split rule; "
              "target attainment retains and requeues the open parent; "
              "same-leaf model object only; no LP basis or native-tree "
              "continuation claim"))))
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
    const bool round40_geometry_valid = !round40_coarse_start ||
        round40_geometry.valid;
    const bool round40_ub_geometry_valid = !round40_nested_dyadic ||
        round40_ub_geometry.valid;
    if (!seed_valid || options.external_gini_backend != "gurobi" ||
        options.external_gini_warm_start || root_gamma_L < -1e-12 ||
        root_gamma_U < root_gamma_L - 1e-12 ||
        !verified_seed.frontier_covers_all_improving_gini_values ||
        !c4_contract_valid || !c5_contract_valid ||
        !c6_contract_valid || !round36_seed_contract_valid ||
        !round40_geometry_valid || !round40_ub_geometry_valid) {
        result.status = "paper_external_gini_tree_invalid_configuration";
        if (!seed_valid) {
            result.external_gini_tree_failure_reason =
                "same_run_seed_not_verified";
        } else if (options.external_gini_backend != "gurobi") {
            result.external_gini_tree_failure_reason =
                "paper_lp_event_path_requires_gurobi";
        } else if (options.external_gini_warm_start) {
            result.external_gini_tree_failure_reason =
                "paper_lp_event_path_forbids_warm_start";
        } else if (!c4_contract_valid) {
            result.external_gini_tree_failure_reason = c4_contract_reason;
        } else if (!c5_contract_valid) {
            result.external_gini_tree_failure_reason = c5_contract_reason;
        } else if (!c6_contract_valid) {
            result.external_gini_tree_failure_reason = c6_contract_reason;
        } else if (!round36_seed_contract_valid) {
            result.external_gini_tree_failure_reason =
                "round36_unsafe_or_unverified_anchor_grid";
        } else if (!round40_geometry_valid) {
            result.external_gini_tree_failure_reason =
                "round40_invalid_coarse_start_geometry";
        } else if (!round40_ub_geometry_valid) {
            result.external_gini_tree_failure_reason =
                "round40_invalid_nested_dyadic_geometry";
        } else {
            result.external_gini_tree_failure_reason =
                "incomplete_or_invalid_root_range";
        }
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
    if (round43_active &&
        root_gamma_U <= root_gamma_L + 1e-12 &&
        verified_seed.objective <= 1e-7) {
        std::ofstream zero_range(
            artifact_dir / "round43_zero_range_classification.csv");
        zero_range << std::setprecision(17)
            << "K0,d,rho,execution,root_lower,root_upper,verified_objective,"
               "classification\n"
            << options.round43_initial_k0 << ','
            << options.round43_lookahead_depth << ','
            << options.round43_rho << ','
            << csvField(options.round43_envelope_refinement) << ','
            << root_gamma_L << ',' << root_gamma_U << ','
            << verified_seed.objective << ','
            << csvField("vacuous_no_strict_improver_range_nonnegative_"
                        "objective_and_verified_zero_incumbent") << '\n';
        zero_range.flush();
        backend->release();
        copyPaperBackendStats(result, backend->stats());
        result.external_gini_tree_root_coverage_valid = true;
        result.external_gini_tree_parent_child_coverage_valid = true;
        result.external_gini_tree_all_relevant_leaves_closed = true;
        result.external_gini_tree_all_leaf_bounds_valid = true;
        result.external_gini_tree_leaf_bounds_monotone = true;
        result.external_gini_tree_global_bound_monotone = true;
        result.external_gini_tree_global_lower_bound = verified_seed.objective;
        result.external_gini_tree_verified_upper_bound =
            verified_seed.objective;
        result.external_gini_tree_initial_leaf_count = 0;
        result.external_gini_tree_final_leaf_count = 0;
        result.external_gini_tree_open_leaf_count = 0;
        result.external_gini_tree_closed_leaf_count = 0;
        result.lower_bound = verified_seed.objective;
        result.upper_bound = verified_seed.objective;
        result.gap = 0.0;
        result.external_gini_tree_feasibility_consistency_gate = true;
        result.external_gini_tree_lifecycle_complete =
            result.external_gini_tree_model_count ==
                result.external_gini_tree_model_free_count &&
            result.external_gini_tree_environment_count ==
                result.external_gini_tree_environment_free_count;
        const bool certified = !round43_atlas &&
            result.external_gini_tree_lifecycle_complete;
        result.external_gini_tree_strict_certified = certified;
        result.strict_certified_original_problem = certified;
        result.external_gini_tree_certificate_class = certified
            ? "strict_original_problem_certificate"
            : "diagnostic_structural_atlas_only";
        result.strict_certificate_class =
            result.external_gini_tree_certificate_class;
        result.external_gini_tree_certificate_rejection_reason = certified
            ? "none"
            : "round43_atlas_has_vacuous_zero_width_proof_range";
        result.strict_certificate_rejection_reason =
            result.external_gini_tree_certificate_rejection_reason;
        result.external_gini_tree_failure_reason = "none";
        result.status = round43_atlas
            ? "round43_structural_atlas_vacuous_zero_range"
            : "optimal";
        result.certificate = certified
            ? "Round 43 zero-range certificate: a verified objective-zero "
              "incumbent meets the global nonnegative objective lower bound."
            : "Round 43 structural atlas is vacuous because the verified "
              "strict-improver range has zero width.";
        result.runtime_seconds = elapsedTelemetry();
        result.wall_time_seconds = result.runtime_seconds;
        result.actual_runtime_seconds = result.runtime_seconds;
        return result;
    }
    if (round41_static_segmented || round42_static_segmented) {
        return solveStaticSegmentedGini(
            instance, options, verified_seed, root_gamma_L, root_gamma_U,
            std::move(result), std::move(backend), artifact_dir);
    }
    if (round41_root_reference) {
        return solveRound41RootReference(
            instance, options, verified_seed, root_gamma_L, root_gamma_U,
            std::move(result), std::move(backend), artifact_dir);
    }
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
    const auto sibling_coverage_path =
        artifact_dir / "round42_sibling_coverage_ledger.csv";
    const auto round43_atlas_path =
        artifact_dir / "round43_structural_atlas.csv";
    const auto round43_envelope_path =
        artifact_dir / "round43_envelope_ledger.csv";
    const auto round43_facet_path =
        artifact_dir / "round43_facet_ledger.csv";
    const auto round43_reuse_path =
        artifact_dir / "round43_lookahead_reuse_ledger.csv";
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
    if (round42_sibling_coalescing) {
        result.round42_sibling_coverage_ledger_path =
            sibling_coverage_path.string();
    }
    std::ofstream events(event_path), optimize(optimize_path), lp_ledger(lp_path),
        bound_ledger(bounds_path), split_ledger(split_path),
        global_trace(global_bound_path), native_targets(native_target_path),
        initial_decomposition(initial_decomposition_path);
    std::ofstream sibling_coverage;
    std::ofstream round43_atlas_ledger, round43_envelope_ledger,
        round43_facet_ledger, round43_reuse_ledger;
    if (round42_sibling_coalescing) {
        sibling_coverage.open(sibling_coverage_path);
    }
    if (round43_active) {
        round43_atlas_ledger.open(round43_atlas_path);
        round43_envelope_ledger.open(round43_envelope_path);
        round43_facet_ledger.open(round43_facet_path);
        round43_reuse_ledger.open(round43_reuse_path);
    }
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
    if (round42_sibling_coalescing) {
        sibling_coverage << std::setprecision(17);
    }
    if (round43_active) {
        round43_atlas_ledger << std::setprecision(17);
        round43_envelope_ledger << std::setprecision(17);
        round43_facet_ledger << std::setprecision(17);
        round43_reuse_ledger << std::setprecision(17);
    }
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
    if (round42_sibling_coalescing) {
        sibling_coverage
            << "event_index,pair_key,left_leaf_id,right_leaf_id,parent_id,"
               "left_lower,left_upper,right_lower,right_upper,block_id,"
               "block_lower,block_upper,common_row_factoring,decision,"
               "model_identity,model_sha256,model_rows,model_columns,"
               "model_nonzeros,indicator_rows,selectors,perspective_variables,"
               "native_status,native_bound_available,native_bound,"
               "block_lower_bound,exact_closure,unresolved_union,"
               "incumbent_updated,atomic_coverage_event,fallback,detail\n";
    }
    if (round43_active) {
        round43_atlas_ledger
            << "parent_id,parent_depth,K0,d,rho,score_mode,envelope_mode,"
               "parent_lower,parent_upper,parent_lp_bound,parent_lp_G,"
               "parent_lp_objective,parent_A,weighted_descendant_A,C_d,"
               "C_d_constant,lookahead_cells,lookahead_bounds,"
               "lookahead_infeasible,lookahead_work,total_lp_work,"
               "Vlocal,Venvelope,Vresidual,tau_d,D_d,old_score,score,"
               "split,reason\n";
        round43_envelope_ledger
            << "parent_id,iteration,envelope_mode,valid,status,"
               "generated_facets,duplicate_facets,dominated_facets,"
               "numerically_adjusted,numerically_rejected,accepted_facets,"
               "Vlocal,Venvelope,Vresidual,tau_d,D_d,"
               "integral_identity_residual,max_endpoint_violation\n";
        round43_facet_ledger
            << "parent_id,iteration,facet_index,alpha,beta,source_lower,"
               "source_upper,constant_candidate,construction,accepted,"
               "propagated,reason\n";
        round43_reuse_ledger
            << "parent_id,lookahead_id,target_child_id,domain_match,row_match,"
               "reused,runtime_credit,work_credit,reason\n";
    }
    events.flush();
    optimize.flush();
    lp_ledger.flush();
    bound_ledger.flush();
    split_ledger.flush();
    global_trace.flush();
    native_targets.flush();
    initial_decomposition.flush();
    if (round42_sibling_coalescing) sibling_coverage.flush();
    if (round43_active) {
        round43_atlas_ledger.flush();
        round43_envelope_ledger.flush();
        round43_facet_ledger.flush();
        round43_reuse_ledger.flush();
    }
    recordProcessPhase(options, "first_tree_ledger_opened", "complete",
                       event_path.string());

    ControllingLeafScheduler scheduler(1e-7);
    const std::vector<GiniIntervalGeometry> initial = round43_active
        ? makeEnvelopeInitialPartition(
              {root_gamma_L, root_gamma_U}, options.round43_initial_k0)
        : (round40_coarse_start
        ? round40_geometry.initial_intervals
        : (round40_nested_dyadic
            ? round40_ub_geometry.active_intervals
        : (round36_causal
            ? causal_grid.active_intervals
            : makeLegacyFrontierIntervals(
                  root_gamma_L, root_gamma_U, options.frontier_intervals))));
    const std::vector<GiniIntervalGeometry> audit_anchor_cells =
        round43_active
            ? initial
            : (round40_coarse_start
            ? round40_geometry.initial_intervals
            : (round40_nested_dyadic
            ? round40_ub_geometry.active_anchor_cells
            : (round36_causal
            ? causal_grid.anchor_cells
            : makeLegacyFrontierIntervals(
                  root_gamma_L, root_gamma_U, options.frontier_intervals))));
    std::vector<long long> audit_anchor_cell_indices;
    if (round40_nested_dyadic) {
        audit_anchor_cell_indices =
            round40_ub_geometry.active_global_cell_indices;
    } else {
        audit_anchor_cell_indices.reserve(audit_anchor_cells.size());
        for (std::size_t index = 0; index < audit_anchor_cells.size(); ++index) {
            audit_anchor_cell_indices.push_back(
                static_cast<long long>(index));
        }
    }
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
    result.external_gini_tree_anchor_grid_cell_indices =
        joinLongLongs(audit_anchor_cell_indices);
    result.external_gini_tree_active_initial_intervals =
        joinIntervals(initial);
    result.external_gini_tree_truncated_initial_interval_count =
        round40_nested_dyadic
            ? round40_ub_geometry.truncated_active_interval_count
            : (round36_causal
                ? causal_grid.truncated_active_interval_count : 0);
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
        } else if (round40_nested_dyadic) {
            active = cell_index < round40_ub_geometry.active_intervals.size();
            if (active) {
                active_interval =
                    round40_ub_geometry.active_intervals[cell_index];
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
        const long long recorded_cell_index =
            cell_index < audit_anchor_cell_indices.size()
                ? audit_anchor_cell_indices[cell_index]
                : static_cast<long long>(cell_index);
        initial_decomposition << std::setprecision(17)
            << recorded_cell_index << ','
            << audit_anchor_cells[cell_index].lower << ','
            << audit_anchor_cells[cell_index].upper << ',' << active << ',';
        if (active) {
            initial_decomposition << active_interval.lower << ','
                                  << active_interval.upper;
        } else {
            initial_decomposition << ',';
        }
        initial_decomposition << ',' << truncated << ','
            << proof_incumbent_launch << ','
            << (round40_nested_dyadic
                ? gini_max_possible : decomposition_anchor_launch)
            << ',' << root_gamma_L << ',' << root_gamma_U << ','
            << csvField(round40_nested_dyadic
                ? "round40-nested-dyadic-proof"
                : options.round36_c6_split_normalization) << '\n';
    }
    initial_decomposition.flush();
    result.external_gini_tree_initial_leaf_count =
        static_cast<long long>(initial.size());
    result.external_gini_tree_scheduler_initial_leaf_count =
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
        if (round42_sibling_coalescing) {
            leaf.parent_id = "R42_INITIAL_PAIR_" +
                std::to_string(index / 2);
            leaf.child_index = static_cast<int>(index % 2);
        }
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
    std::set<std::string> round42_sibling_pairs_seen;
    std::set<std::string> round42_sibling_pairs_disabled;
    long long round42_sibling_event_index = 0;

    auto siblingPairKey = [](const std::string& first,
                             const std::string& second) {
        return first < second ? first + "|" + second
                              : second + "|" + first;
    };

    auto isSchedulableRelevant = [&scheduler](const ControllingLeaf& leaf) {
        return leaf.status != ControllingLeafStatus::Replaced &&
            leaf.status != ControllingLeafStatus::Coalesced &&
            !leaf.parent_replaced &&
            leaf.gamma_L < leaf.cutoff - scheduler.certificateTolerance() &&
            (leaf.status == ControllingLeafStatus::Open ||
             leaf.status == ControllingLeafStatus::Invalid) &&
            leaf.lower_bound <
                leaf.cutoff - scheduler.certificateTolerance();
    };
    auto writeSiblingCoverage = [&] (
            const std::string& pair_key,
            const ControllingLeaf& left,
            const ControllingLeaf& right,
            const std::string& block_id,
            bool common_row_factoring,
            const std::string& decision,
            const StaticSegmentedBlockSpec* block_spec,
            const CanonicalCompactModelArtifact* artifact,
            const FixedIntervalMipOutcome* outcome,
            double block_lower_bound,
            bool exact_closure,
            bool unresolved_union,
            bool incumbent_updated,
            bool atomic_event,
            bool fallback,
            const std::string& detail) {
        if (!round42_sibling_coalescing) return;
        sibling_coverage << ++round42_sibling_event_index << ','
            << csvField(pair_key) << ',' << csvField(left.id) << ','
            << csvField(right.id) << ',' << csvField(left.parent_id) << ','
            << left.gamma_L << ',' << left.gamma_U << ','
            << right.gamma_L << ',' << right.gamma_U << ','
            << csvField(block_id) << ',' << left.gamma_L << ','
            << right.gamma_U << ',' << common_row_factoring << ','
            << csvField(decision) << ','
            << csvField(block_spec
                ? block_spec->deterministic_model_identity : "") << ','
            << csvField(artifact ? artifact->sha256 : "") << ','
            << (artifact ? artifact->rows : 0) << ','
            << (artifact ? artifact->columns : 0) << ','
            << (artifact ? artifact->nonzeros : 0) << ','
            << (artifact ? artifact->static_indicator_rows : 0) << ','
            << (artifact ? artifact->static_selector_variables : 0) << ','
            << (artifact ? artifact->static_perspective_variables : 0) << ','
            << csvField(outcome ? outcome->native_status : "") << ','
            << (outcome && outcome->native_bound_available) << ',';
        if (outcome && outcome->native_bound_available) {
            sibling_coverage << outcome->native_bound;
        }
        sibling_coverage << ',' << block_lower_bound << ',' << exact_closure
            << ',' << unresolved_union << ',' << incumbent_updated << ','
            << atomic_event << ',' << fallback << ',' << csvField(detail)
            << '\n';
        sibling_coverage.flush();
    };
    auto relevantCounts = [&scheduler]() {
        std::pair<long long, long long> counts{0, 0};
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.status == ControllingLeafStatus::Replaced ||
                leaf.status == ControllingLeafStatus::Coalesced ||
                leaf.parent_replaced ||
                leaf.gamma_L >=
                    leaf.cutoff - scheduler.certificateTolerance()) {
                continue;
            }
            const bool open =
                (leaf.status == ControllingLeafStatus::Open ||
                 leaf.status == ControllingLeafStatus::Invalid ||
                 leaf.status == ControllingLeafStatus::TerminalReady) &&
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
    auto otherRelevantMinimum = [&scheduler, &isSchedulableRelevant](
            const std::string& active_leaf) {
        double minimum = std::numeric_limits<double>::infinity();
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.id == active_leaf || !isSchedulableRelevant(leaf)) {
                continue;
            }
            minimum = std::min(minimum, leaf.lower_bound);
        }
        return minimum;
    };
    auto otherRelevantBounds = [&isSchedulableRelevant, &scheduler](
            const std::string& active_leaf) {
        std::vector<double> bounds;
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.id == active_leaf || !isSchedulableRelevant(leaf)) {
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
        if (round43_active) {
            spec.objective_gini_envelope_facets =
                state.round43_inherited_facets;
        }
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
        state.round43_lp_g_available = outcome.lp_g_value_available;
        state.round43_lp_g = outcome.lp_g_value;
        state.round43_lp_objective_available =
            outcome.lp_objective_value_available;
        state.round43_lp_objective = outcome.lp_objective_value;
        state.round43_lp_work = outcome.work;
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

    auto solveSpeculativeLp = [&](const ControllingLeaf& leaf,
                                  PaperLeafRuntime& state,
                                  const std::string& event_source) -> bool {
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
        request.verified_cutoff = verified_ub;
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
        const FixedIntervalMipOutcome outcome = backend->solve(request);
        optimize << leaf.id << ",LP," << csvField(outcome.native_status)
                 << ',' << outcome.optimize_return_code << ',' << remaining
                 << ',' << outcome.solver_runtime_seconds << ','
                 << outcome.work << ',' << outcome.nodes << ','
                 << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ',' << outcome.memory_gb
                 << ',' << state.artifact.sha256 << ','
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
        state.round43_lp_g_available = outcome.lp_g_value_available;
        state.round43_lp_g = outcome.lp_g_value;
        state.round43_lp_objective_available =
            outcome.lp_objective_value_available;
        state.round43_lp_objective = outcome.lp_objective_value;
        state.round43_lp_work = outcome.work;
        lp_ledger << leaf.id << ',' << csvField(leaf.parent_id) << ','
                  << leaf.split_depth << ',' << leaf.gamma_L << ','
                  << leaf.gamma_U << ',' << state.lp.terminal_valid << ','
                  << state.lp.optimal << ',' << state.lp.infeasible << ','
                  << state.lp.bound_available << ',' << state.lp.lower_bound
                  << ',' << csvField(outcome.native_status) << ','
                  << outcome.work << ',' << elapsedTelemetry() << '\n';
        writeGlobalTrace(
            processElapsedSeconds(options), elapsedTelemetry(),
            "child_lp_completion", leaf.id,
            state.lp.infeasible
                ? std::numeric_limits<double>::infinity()
                : state.lp.lower_bound,
            scheduler.globalLowerBound(), event_source);
        if (!state.lp_complete) {
            result.external_gini_tree_failure_reason =
                outcome.failure_reason == "none"
                    ? "round43_lookahead_lp_not_terminal_valid:" + leaf.id
                    : outcome.failure_reason;
            return false;
        }
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
    bool round37_pilot_prefinement_pending = false;
    if (round37_pilot_prefine && !hard_failure) {
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
            ++result.round37_pilot_initial_lp_count;
            if (state.lp.infeasible) {
                std::string reason;
                if (!scheduler.setStatus(
                        leaf_id, ControllingLeafStatus::Empty,
                        "round37_pilot_complete_initial_lp_infeasible",
                        &reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "round37_pilot_infeasible_closure_failed:" + reason;
                    break;
                }
                backend->discardLeaf(leaf_id);
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsedTelemetry(),
                    "infeasible_closure", leaf_id,
                    std::numeric_limits<double>::infinity(),
                    scheduler.globalLowerBound(),
                    "round37_pilot_complete_initial_lp_infeasible");
            }
        }
        result.round37_pilot_all_initial_lps_complete =
            !hard_failure && !global_deadline_stop &&
            result.round37_pilot_initial_lp_count ==
                static_cast<long long>(initial.size());
        if (result.round37_pilot_all_initial_lps_complete) {
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
            round37_pilot_selection = selectPilotWeakestGiniCell(
                assessments, scheduler.certificateTolerance());
            result.round37_pilot_eligible_cell_count =
                round37_pilot_selection.eligible_cell_count;
            if (round37_pilot_selection.valid) {
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
        if (!selection.available) {
            // A terminal-ready leaf is deliberately removed from the normal
            // C6 queue while its exact sibling progresses.  If no selectable
            // work remains, deterministically requeue one such leaf.  This is
            // the fail-closed path for a singleton whose sibling was pruned,
            // closed, or otherwise ceased to be live.
            const ControllingLeaf* pending = nullptr;
            if (round42_sibling_coalescing) {
                for (const ControllingLeaf& leaf : scheduler.leaves()) {
                    if (leaf.status != ControllingLeafStatus::TerminalReady ||
                        leaf.parent_replaced ||
                        leaf.lower_bound >= leaf.cutoff -
                            scheduler.certificateTolerance()) {
                        continue;
                    }
                    if (!pending || leaf.id < pending->id) pending = &leaf;
                }
            }
            if (pending) {
                const std::string pending_id = pending->id;
                const double pending_lower = pending->gamma_L;
                const double pending_upper = pending->gamma_U;
                std::string reason;
                if (!scheduler.setStatus(
                        pending_id, ControllingLeafStatus::Open, "", &reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "round42_terminal_ready_requeue_failed:" + reason;
                    break;
                }
                events << elapsedTelemetry()
                       << ",round42_terminal_ready_requeue," << pending_id
                       << ',' << pending_lower << ',' << pending_upper
                       << ",open," << scheduler.globalLowerBound() << ','
                       << verified_ub << ','
                       << csvField("sibling_no_longer_selectable_fail_closed")
                       << '\n';
                continue;
            }
            break;
        }
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
        if (round43_active) {
            const GiniIntervalGeometry parent_geometry{
                bounded.gamma_L, bounded.gamma_U};
            const std::vector<GiniIntervalGeometry> lookahead_geometry =
                makeDyadicLookaheadPartition(
                    parent_geometry, options.round43_lookahead_depth);
            if (lookahead_geometry.size() !=
                    static_cast<std::size_t>(
                        1 << options.round43_lookahead_depth) ||
                !exactIntervalCoverage(
                    parent_geometry, lookahead_geometry,
                    scheduler.certificateTolerance())) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round43_lookahead_geometry_invalid:" + bounded.id;
                break;
            }

            std::vector<GiniLookaheadBound> lookahead_profile;
            std::vector<std::string> lookahead_ids;
            std::vector<double> lookahead_work;
            std::ostringstream lookahead_bounds_text;
            std::ostringstream lookahead_infeasible_text;
            double total_lookahead_work = 0.0;
            lookahead_profile.reserve(lookahead_geometry.size());
            for (std::size_t index = 0;
                 index < lookahead_geometry.size(); ++index) {
                const std::string lookahead_id =
                    options.round43_lookahead_depth == 1
                        ? bounded.id + "." + std::to_string(index)
                        : bounded.id + ".look" +
                            std::to_string(options.round43_lookahead_depth) +
                            "." + std::to_string(index);
                lookahead_ids.push_back(lookahead_id);
                ControllingLeaf cell;
                cell.id = lookahead_id;
                cell.parent_id = bounded.id;
                cell.child_index = static_cast<int>(index);
                cell.split_depth = bounded.split_depth +
                    options.round43_lookahead_depth;
                cell.gamma_L = lookahead_geometry[index].lower;
                cell.gamma_U = lookahead_geometry[index].upper;
                cell.base_lower_bound = bounded.lower_bound;
                cell.lower_bound = bounded.lower_bound;
                cell.lower_bound_sources = {
                    "round43_inherited_parent_lp_bound"};
                cell.cutoff = bounded.cutoff;
                PaperLeafRuntime& cell_state = runtime[cell.id];
                cell_state.round43_inherited_facets =
                    selected_state.round43_inherited_facets;
                if (!solveSpeculativeLp(
                        cell, cell_state,
                        "round43_complete_speculative_lookahead_lp")) {
                    if (!global_deadline_stop) hard_failure = true;
                    break;
                }
                GiniLookaheadBound profile_cell;
                profile_cell.interval = lookahead_geometry[index];
                profile_cell.terminal_valid = cell_state.lp.terminal_valid;
                profile_cell.optimal = cell_state.lp.optimal;
                profile_cell.infeasible = cell_state.lp.infeasible;
                profile_cell.bound_available =
                    cell_state.lp.bound_available;
                profile_cell.lower_bound = cell_state.lp.lower_bound;
                lookahead_profile.push_back(profile_cell);
                lookahead_work.push_back(cell_state.round43_lp_work);
                total_lookahead_work += cell_state.round43_lp_work;
                if (index) {
                    lookahead_bounds_text << ';';
                    lookahead_infeasible_text << ';';
                }
                if (cell_state.lp.bound_available) {
                    lookahead_bounds_text << cell_state.lp.lower_bound;
                }
                lookahead_infeasible_text << cell_state.lp.infeasible;
            }
            if (hard_failure || global_deadline_stop) break;

            GiniEnvelopeInput envelope_input;
            envelope_input.parent = parent_geometry;
            envelope_input.parent_lower_bound =
                selected_state.lp.lower_bound;
            envelope_input.verified_upper_bound = verified_ub;
            envelope_input.lookahead = lookahead_profile;
            envelope_input.certificate_tolerance =
                scheduler.certificateTolerance();
            const GiniEnvelopeResult envelope =
                constructGiniLowerBoundEnvelope(envelope_input);
            if (!envelope.valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round43_envelope_invalid:" + bounded.id + ":" +
                    envelope.status;
                break;
            }

            const long long width_components =
                round43WidthComponentCount(instance);
            FormulationContractionInput contraction_input;
            contraction_input.parent = parent_geometry;
            contraction_input.parent_A = round43WidthMeasure(
                parent_geometry, {root_gamma_L, root_gamma_U},
                width_components);
            contraction_input.lookahead_intervals = lookahead_geometry;
            for (const GiniIntervalGeometry& cell : lookahead_geometry) {
                contraction_input.lookahead_A.push_back(
                    round43WidthMeasure(
                        cell, {root_gamma_L, root_gamma_U},
                        width_components));
            }
            contraction_input.epsilon_width = 1e-12;
            const FormulationContractionResult contraction =
                evaluateFormulationContraction(contraction_input);
            if (!contraction.valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round43_contraction_invalid:" + bounded.id + ":" +
                    contraction.reason;
                break;
            }
            const double expected_contraction = 1.0 -
                1.0 / static_cast<double>(
                    1 << options.round43_lookahead_depth);
            const bool contraction_constant =
                std::fabs(contraction.C_d - expected_contraction) <= 1e-10;

            double post_disjunction_bound =
                std::numeric_limits<double>::infinity();
            for (double clipped : envelope.clipped_bounds) {
                post_disjunction_bound = std::min(
                    post_disjunction_bound, clipped);
            }
            const double old_denominator = std::max(
                verified_ub - selected_state.lp.lower_bound,
                scheduler.certificateTolerance());
            const double old_score = std::max(0.0, std::min(
                1.0, (post_disjunction_bound -
                    selected_state.lp.lower_bound) / old_denominator));

            EnvelopeRefinementDecision refinement;
            if (options.round43_score == "no-adaptive") {
                refinement.valid = true;
                refinement.split = false;
                refinement.score = 0.0;
                refinement.score_mode = "no-adaptive";
                refinement.reason = "round43_frozen_no_adaptive_split";
            } else if (options.round43_score == "old") {
                refinement.valid = true;
                refinement.score = old_score;
                refinement.score_mode = "old";
                refinement.split = old_score >= options.round43_rho;
                refinement.reason = refinement.split
                    ? "old_score_greater_than_or_equal_to_frozen_rho"
                    : "old_score_strictly_below_frozen_rho";
            } else {
                refinement = evaluateEnvelopeRefinementDecision(
                    envelope.D_d, contraction.C_d,
                    options.round43_score, options.round43_rho,
                    scheduler.certificateTolerance());
            }
            if (!refinement.valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "round43_refinement_decision_invalid:" + bounded.id +
                    ":" + refinement.reason;
                break;
            }

            std::vector<GiniEnvelopeFacet> current_facets;
            if (options.round43_envelope_mode == "constant") {
                current_facets.push_back({
                    post_disjunction_bound, 0.0,
                    parent_geometry.lower, parent_geometry.upper, true,
                    "round43_constant_descendant_bound"});
            } else if (options.round43_envelope_mode == "single") {
                current_facets = envelope.facets;
            }
            auto appendUniqueFacet = [&](std::vector<GiniEnvelopeFacet>& target,
                                         const GiniEnvelopeFacet& candidate) {
                for (const GiniEnvelopeFacet& existing : target) {
                    const double lower_difference = std::fabs(
                        evaluateGiniEnvelopeFacet(existing,
                            parent_geometry.lower) -
                        evaluateGiniEnvelopeFacet(candidate,
                            parent_geometry.lower));
                    const double upper_difference = std::fabs(
                        evaluateGiniEnvelopeFacet(existing,
                            parent_geometry.upper) -
                        evaluateGiniEnvelopeFacet(candidate,
                            parent_geometry.upper));
                    if (lower_difference <=
                            scheduler.certificateTolerance() &&
                        upper_difference <=
                            scheduler.certificateTolerance()) {
                        return false;
                    }
                }
                target.push_back(candidate);
                return true;
            };
            std::vector<GiniEnvelopeFacet> propagated_facets =
                selected_state.round43_inherited_facets;
            for (const GiniEnvelopeFacet& facet : current_facets) {
                appendUniqueFacet(propagated_facets, facet);
            }

            if (options.round43_envelope_mode == "iterated" &&
                !round43_atlas) {
                GiniEnvelopeResult fixed_point_envelope = envelope;
                bool fixed_point_reached = false;
                bool current_g_available =
                    selected_state.round43_lp_g_available;
                bool current_objective_available =
                    selected_state.round43_lp_objective_available;
                double current_g = selected_state.round43_lp_g;
                double current_objective =
                    selected_state.round43_lp_objective;
                long long iteration = 0;
                while (!fixed_point_reached && !hard_failure &&
                       !global_deadline_stop) {
                    if (globalDeadlineRemaining() <= 0.0) {
                        stopAtDeadline();
                        break;
                    }
                    ++iteration;
                    if (!current_g_available ||
                        !current_objective_available) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round43_iterated_parent_lp_solution_unavailable:" +
                            bounded.id;
                        break;
                    }
                    std::vector<GiniEnvelopeFacet> violated_new_facets;
                    for (std::size_t facet_index = 0;
                         facet_index < fixed_point_envelope.facets.size();
                         ++facet_index) {
                        const GiniEnvelopeFacet& facet =
                            fixed_point_envelope.facets[facet_index];
                        const double facet_value =
                            evaluateGiniEnvelopeFacet(facet, current_g);
                        const double violation =
                            facet_value - current_objective;
                        const double violation_tolerance =
                            scheduler.certificateTolerance() *
                            std::max({1.0, std::fabs(facet_value),
                                      std::fabs(current_objective)});
                        bool accepted = false;
                        if (violation > violation_tolerance) {
                            accepted = appendUniqueFacet(
                                propagated_facets, facet);
                            if (accepted) {
                                current_facets.push_back(facet);
                                violated_new_facets.push_back(facet);
                            }
                        }
                        round43_facet_ledger << bounded.id << ','
                            << iteration << ',' << facet_index << ','
                            << facet.alpha << ',' << facet.beta << ','
                            << facet.source_lower << ',' << facet.source_upper
                            << ',' << facet.constant_parent_candidate << ','
                            << csvField(facet.construction) << ','
                            << accepted << ',' << accepted << ','
                            << csvField(accepted
                                ? "violated_at_current_parent_lp_and_unique"
                                : (violation > violation_tolerance
                                    ? "violated_but_duplicate_existing_facet"
                                    : "not_violated_at_current_parent_lp"))
                            << '\n';
                    }
                    if (violated_new_facets.empty()) {
                        fixed_point_reached = true;
                        break;
                    }

                    ControllingLeaf fixed_parent = bounded;
                    fixed_parent.id = bounded.id + ".fp_parent." +
                        std::to_string(iteration);
                    PaperLeafRuntime& fixed_parent_state =
                        runtime[fixed_parent.id];
                    fixed_parent_state.round43_inherited_facets =
                        propagated_facets;
                    if (!solveSpeculativeLp(
                            fixed_parent, fixed_parent_state,
                            "round43_iterated_strengthened_parent_lp")) {
                        if (!global_deadline_stop) hard_failure = true;
                        break;
                    }
                    if (fixed_parent_state.lp.infeasible) {
                        backend->discardLeaf(fixed_parent.id);
                        runtime.erase(fixed_parent.id);
                        fixed_point_reached = true;
                        break;
                    }
                    if (fixed_parent_state.lp.optimal) {
                        std::string merge_reason;
                        if (!scheduler.mergeValidLowerBound(
                                bounded.id,
                                fixed_parent_state.lp.lower_bound,
                                "round43_iterated_strengthened_parent_lp",
                                &merge_reason)) {
                            hard_failure = true;
                            result.external_gini_tree_failure_reason =
                                "round43_iterated_parent_bound_merge_failed:" +
                                merge_reason;
                            break;
                        }
                    }
                    current_g_available =
                        fixed_parent_state.round43_lp_g_available;
                    current_objective_available =
                        fixed_parent_state.round43_lp_objective_available;
                    current_g = fixed_parent_state.round43_lp_g;
                    current_objective =
                        fixed_parent_state.round43_lp_objective;

                    std::vector<GiniLookaheadBound> fixed_profile;
                    for (std::size_t cell_index = 0;
                         cell_index < lookahead_geometry.size(); ++cell_index) {
                        ControllingLeaf fixed_cell;
                        fixed_cell.id = bounded.id + ".fp" +
                            std::to_string(iteration) + ".look." +
                            std::to_string(cell_index);
                        fixed_cell.parent_id = bounded.id;
                        fixed_cell.split_depth = bounded.split_depth +
                            options.round43_lookahead_depth;
                        fixed_cell.child_index =
                            static_cast<int>(cell_index);
                        fixed_cell.gamma_L =
                            lookahead_geometry[cell_index].lower;
                        fixed_cell.gamma_U =
                            lookahead_geometry[cell_index].upper;
                        fixed_cell.base_lower_bound =
                            fixed_parent_state.lp.lower_bound;
                        fixed_cell.lower_bound = fixed_cell.base_lower_bound;
                        fixed_cell.cutoff = bounded.cutoff;
                        PaperLeafRuntime& fixed_cell_state =
                            runtime[fixed_cell.id];
                        fixed_cell_state.round43_inherited_facets =
                            propagated_facets;
                        if (!solveSpeculativeLp(
                                fixed_cell, fixed_cell_state,
                                "round43_iterated_strengthened_lookahead_lp")) {
                            if (!global_deadline_stop) hard_failure = true;
                            break;
                        }
                        fixed_profile.push_back({
                            lookahead_geometry[cell_index],
                            fixed_cell_state.lp.terminal_valid,
                            fixed_cell_state.lp.optimal,
                            fixed_cell_state.lp.infeasible,
                            fixed_cell_state.lp.bound_available,
                            fixed_cell_state.lp.lower_bound});
                    }
                    if (hard_failure || global_deadline_stop) break;
                    GiniEnvelopeInput fixed_input;
                    fixed_input.parent = parent_geometry;
                    fixed_input.parent_lower_bound =
                        fixed_parent_state.lp.lower_bound;
                    fixed_input.verified_upper_bound = verified_ub;
                    fixed_input.lookahead = fixed_profile;
                    fixed_input.certificate_tolerance =
                        scheduler.certificateTolerance();
                    fixed_point_envelope =
                        constructGiniLowerBoundEnvelope(fixed_input);
                    round43_envelope_ledger << bounded.id << ','
                        << iteration << ','
                        << csvField(options.round43_envelope_mode) << ','
                        << fixed_point_envelope.valid << ','
                        << csvField(fixed_point_envelope.status) << ','
                        << fixed_point_envelope.generated_facet_count << ','
                        << fixed_point_envelope.duplicate_facet_count << ','
                        << fixed_point_envelope.dominated_facet_count << ','
                        << fixed_point_envelope.
                            numerically_adjusted_facet_count << ','
                        << fixed_point_envelope.
                            numerically_rejected_facet_count << ','
                        << fixed_point_envelope.accepted_facet_count << ','
                        << fixed_point_envelope.V_local << ','
                        << fixed_point_envelope.V_envelope << ','
                        << fixed_point_envelope.V_residual << ','
                        << fixed_point_envelope.tau_d << ','
                        << fixed_point_envelope.D_d << ','
                        << fixed_point_envelope.integral_identity_residual
                        << ',' << fixed_point_envelope.max_endpoint_violation
                        << '\n';
                    backend->discardLeaf(fixed_parent.id);
                    runtime.erase(fixed_parent.id);
                    for (std::size_t cell_index = 0;
                         cell_index < lookahead_geometry.size(); ++cell_index) {
                        const std::string fixed_cell_id = bounded.id + ".fp" +
                            std::to_string(iteration) + ".look." +
                            std::to_string(cell_index);
                        backend->discardLeaf(fixed_cell_id);
                        runtime.erase(fixed_cell_id);
                    }
                    if (!fixed_point_envelope.valid) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round43_iterated_envelope_invalid:" +
                            bounded.id + ":" + fixed_point_envelope.status;
                        break;
                    }
                }
                if (hard_failure || global_deadline_stop) break;
            }

            round43_envelope_ledger << bounded.id << ",0,"
                << csvField(options.round43_envelope_mode) << ','
                << envelope.valid << ',' << csvField(envelope.status) << ','
                << envelope.generated_facet_count << ','
                << envelope.duplicate_facet_count << ','
                << envelope.dominated_facet_count << ','
                << envelope.numerically_adjusted_facet_count << ','
                << envelope.numerically_rejected_facet_count << ','
                << envelope.accepted_facet_count << ','
                << envelope.V_local << ',' << envelope.V_envelope << ','
                << envelope.V_residual << ',' << envelope.tau_d << ','
                << envelope.D_d << ','
                << envelope.integral_identity_residual << ','
                << envelope.max_endpoint_violation << '\n';
            if (options.round43_envelope_mode != "iterated")
            for (std::size_t facet_index = 0;
                 facet_index < current_facets.size(); ++facet_index) {
                const GiniEnvelopeFacet& facet =
                    current_facets[facet_index];
                round43_facet_ledger << bounded.id << ",0,"
                    << facet_index << ',' << facet.alpha << ',' << facet.beta
                    << ',' << facet.source_lower << ',' << facet.source_upper
                    << ',' << facet.constant_parent_candidate << ','
                    << csvField(facet.construction)
                    << ",true,true,accepted_by_frozen_envelope_mode\n";
            }
            round43_atlas_ledger << bounded.id << ',' << bounded.split_depth
                << ',' << options.round43_initial_k0 << ','
                << options.round43_lookahead_depth << ','
                << options.round43_rho << ','
                << csvField(options.round43_score) << ','
                << csvField(options.round43_envelope_mode) << ','
                << parent_geometry.lower << ',' << parent_geometry.upper
                << ',' << selected_state.lp.lower_bound << ',';
            if (selected_state.round43_lp_g_available) {
                round43_atlas_ledger << selected_state.round43_lp_g;
            }
            round43_atlas_ledger << ',';
            if (selected_state.round43_lp_objective_available) {
                round43_atlas_ledger <<
                    selected_state.round43_lp_objective;
            }
            round43_atlas_ledger << ',' << contraction_input.parent_A << ','
                << contraction.weighted_child_A << ',' << contraction.C_d
                << ',' << contraction_constant << ','
                << csvField(joinIntervals(lookahead_geometry)) << ','
                << csvField(lookahead_bounds_text.str()) << ','
                << csvField(lookahead_infeasible_text.str()) << ','
                << csvField(joinDoubles(lookahead_work)) << ','
                << (selected_state.round43_lp_work + total_lookahead_work)
                << ',' << envelope.V_local << ',' << envelope.V_envelope
                << ',' << envelope.V_residual << ',' << envelope.tau_d
                << ',' << envelope.D_d << ',' << old_score << ','
                << refinement.score << ',' << refinement.split << ','
                << csvField(refinement.reason) << '\n';
            round43_atlas_ledger.flush();
            round43_envelope_ledger.flush();
            round43_facet_ledger.flush();

            if (round43_atlas) {
                for (const std::string& lookahead_id : lookahead_ids) {
                    backend->discardLeaf(lookahead_id);
                }
                backend->discardLeaf(bounded.id);
                std::string atlas_reason;
                if (!scheduler.setStatus(
                        bounded.id, ControllingLeafStatus::Closed,
                        "round43_diagnostic_atlas_only", &atlas_reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "round43_atlas_status_failed:" + atlas_reason;
                    break;
                }
                continue;
            }

            const std::vector<GiniIntervalGeometry> child_geometry =
                makeEnvelopeInitialPartition(parent_geometry, 2);
            const bool midpoint_splittable = child_geometry.size() == 2 &&
                child_geometry[0].upper > child_geometry[0].lower &&
                child_geometry[1].upper > child_geometry[1].lower &&
                exactIntervalCoverage(
                    parent_geometry, child_geometry,
                    scheduler.certificateTolerance());
            if (refinement.split && midpoint_splittable) {
                std::vector<ControllingLeaf> children;
                children.reserve(2);
                std::vector<AggregatedLookaheadBound> child_bounds;
                for (std::size_t index = 0; index < 2; ++index) {
                    const AggregatedLookaheadBound aggregated =
                        aggregateLookaheadBoundForInterval(
                            child_geometry[index], bounded.lower_bound,
                            lookahead_profile,
                            scheduler.certificateTolerance());
                    if (!aggregated.valid) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round43_child_bound_aggregation_failed:" +
                            bounded.id + ":" + aggregated.reason;
                        break;
                    }
                    child_bounds.push_back(aggregated);
                    ControllingLeaf child;
                    child.id = bounded.id + "." + std::to_string(index);
                    child.parent_id = bounded.id;
                    child.child_index = static_cast<int>(index);
                    child.split_depth = bounded.split_depth + 1;
                    child.gamma_L = child_geometry[index].lower;
                    child.gamma_U = child_geometry[index].upper;
                    child.base_lower_bound = aggregated.lower_bound;
                    child.lower_bound = aggregated.lower_bound;
                    child.lower_bound_sources = {
                        "round43_complete_lookahead_partition_bound"};
                    child.cutoff = bounded.cutoff;
                    children.push_back(child);
                }
                if (hard_failure) break;
                const bool exact_row_match =
                    options.round43_lookahead_depth == 1 &&
                    current_facets.empty();
                for (std::size_t index = 0;
                     index < lookahead_ids.size(); ++index) {
                    const std::string target_child = index < 2
                        ? bounded.id + "." + std::to_string(index) : "";
                    const bool domain_match =
                        options.round43_lookahead_depth == 1 && index < 2;
                    const bool reused = domain_match && exact_row_match;
                    round43_reuse_ledger << bounded.id << ','
                        << csvField(lookahead_ids[index]) << ','
                        << csvField(target_child) << ',' << domain_match << ','
                        << exact_row_match << ',' << reused << ','
                        << (reused ? 1 : 0) << ','
                        << (reused ? lookahead_work[index] : 0.0) << ','
                        << csvField(reused
                            ? "exact_domain_and_inherited_row_signature_match"
                            : (domain_match
                                ? "new_parent_envelope_changes_child_rows"
                                : "depth_d_cell_is_not_immediate_child"))
                        << '\n';
                    if (!reused) {
                        backend->discardLeaf(lookahead_ids[index]);
                        runtime.erase(lookahead_ids[index]);
                    }
                }
                for (ControllingLeaf& child : children) {
                    PaperLeafRuntime& child_state = runtime[child.id];
                    if (!exact_row_match) {
                        child_state = PaperLeafRuntime{};
                    }
                    child_state.round43_inherited_facets =
                        propagated_facets;
                }
                std::string split_reason;
                if (!scheduler.splitLeafAtomically(
                        bounded.id, children, &split_reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "round43_atomic_split_failed:" + split_reason;
                    break;
                }
                ++result.external_gini_tree_split_count;
                backend->discardLeaf(bounded.id);
                for (std::size_t index = 0; index < children.size(); ++index) {
                    if (!child_bounds[index].infeasible) continue;
                    std::string close_reason;
                    if (!scheduler.setStatus(
                            children[index].id,
                            ControllingLeafStatus::Empty,
                            "round43_complete_lookahead_partition_infeasible",
                            &close_reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round43_infeasible_child_close_failed:" +
                            close_reason;
                        break;
                    }
                    backend->discardLeaf(children[index].id);
                }
                events << elapsedTelemetry() << ",round43_atomic_split,"
                    << bounded.id << ',' << bounded.gamma_L << ','
                    << bounded.gamma_U << ",replaced,"
                    << scheduler.globalLowerBound() << ',' << verified_ub
                    << ',' << csvField(refinement.reason) << '\n';
                round43_reuse_ledger.flush();
                continue;
            }

            ++result.external_gini_tree_declined_split_count;
            for (const std::string& lookahead_id : lookahead_ids) {
                backend->discardLeaf(lookahead_id);
                runtime.erase(lookahead_id);
            }
            if (!current_facets.empty()) {
                backend->discardLeaf(bounded.id);
                selected_state.artifact_ready = false;
                selected_state.artifact = CanonicalCompactModelArtifact{};
                selected_state.round43_inherited_facets =
                    propagated_facets;
                if (!ensureArtifact(bounded, selected_state)) {
                    if (!global_deadline_stop) hard_failure = true;
                    break;
                }
            }
            events << elapsedTelemetry()
                << ",round43_exact_parent_selected," << bounded.id << ','
                << bounded.gamma_L << ',' << bounded.gamma_U << ",open,"
                << scheduler.globalLowerBound() << ',' << verified_ub << ','
                << csvField(refinement.split && !midpoint_splittable
                    ? "numeric_midpoint_terminal_exact_parent"
                    : refinement.reason) << '\n';
        }

        const bool round37_force_prefinement =
            round37_pilot_prefinement_pending &&
            bounded.id == round37_pilot_selection.leaf_id;
        if (c6_nonblocking && !round43_active &&
            !round37_force_prefinement) {
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
        const bool eligible = !round43_active &&
            ((!round40_coarse_start ||
             round40_geometry.adaptive_refinement) &&
            legacyAdaptiveSplitEligible(
                bounded.gamma_L, bounded.gamma_U, bounded.split_depth,
                options.frontier_adaptive_max_depth,
                options.frontier_adaptive_min_width));
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
            C6CurrentSplitDecision c6_split = c6_nonblocking
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
            if (c6_nonblocking &&
                options.round40_c6_coarse_start ==
                    "k1-adaptive-decisive" &&
                c6_split.valid) {
                const bool decisive_child_evidence =
                    c6_split.child_infeasibility_trigger ||
                    c6_split.post_split_lower_bound >=
                        verified_ub - scheduler.certificateTolerance();
                c6_split.split_immediately = decisive_child_evidence;
                c6_split.run_child_bound_target = false;
                c6_split.launch_exact_closure = !decisive_child_evidence;
                c6_split.reason = decisive_child_evidence
                    ? "round40_decisive_child_infeasibility_or_cutoff_split"
                    : "round40_nondecisive_child_evidence_close_parent";
            }
            const bool decision_valid =
                round37_force_prefinement
                    ? c6_split.valid
                    : (c6_nonblocking
                    ? c6_split.valid
                    : (c5_bound_target ? c5_split.valid : split.valid));
            const bool split_immediately =
                round37_force_prefinement ||
                (c6_nonblocking
                    ? c6_split.split_immediately
                    : (c5_bound_target ? c5_split.split_immediately
                                       : split.should_split));
            const bool child_infeasibility_trigger =
                c6_nonblocking
                    ? c6_split.child_infeasibility_trigger
                    : (c5_bound_target
                        ? c5_split.child_infeasibility_trigger
                        : split.child_infeasibility_trigger);
            const double post_split_bound =
                c6_nonblocking
                    ? c6_split.post_split_lower_bound
                    : (c5_bound_target ? c5_split.post_split_lower_bound
                                       : split.post_split_lower_bound);
            const std::string split_reason =
                round37_force_prefinement
                    ? "round37_pilot_weakest_midpoint_prefinement"
                    : (c6_nonblocking
                    ? c6_split.reason
                    : (c5_bound_target ? c5_split.reason : split.reason));
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
                        ? (round37_force_prefinement
                            ? "round37_pilot_weakest_midpoint_prefinement"
                            : "c6_current_gain_atomic_split")
                        : (c5_bound_target
                            ? "c5_immediate_atomic_split"
                            : "c4_atomic_split"));
                if (c6_nonblocking) {
                    selected_state.c6_children_ready = false;
                    selected_state.c6_cached_children.clear();
                }
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
        terminal_state.terminal_ready = true;
        if (round42_sibling_coalescing) {
            const ControllingLeaf* sibling_ptr = nullptr;
            for (const ControllingLeaf& candidate : scheduler.leaves()) {
                if (candidate.id == bounded.id) continue;
                std::string sibling_reason;
                if (!scheduler.areExactLiveSiblings(
                        bounded.id, candidate.id, &sibling_reason)) {
                    continue;
                }
                if (!sibling_ptr || candidate.id < sibling_ptr->id) {
                    sibling_ptr = &candidate;
                }
            }
            if (sibling_ptr) {
                const ControllingLeaf sibling = *sibling_ptr;
                const ControllingLeaf left =
                    bounded.gamma_L <= sibling.gamma_L ? bounded : sibling;
                const ControllingLeaf right =
                    bounded.gamma_L <= sibling.gamma_L ? sibling : bounded;
                const std::string pair_key =
                    siblingPairKey(left.id, right.id);
                if (round42_sibling_pairs_seen.insert(pair_key).second) {
                    ++result.round42_sibling_pairs_considered;
                }
                if (!round42_sibling_pairs_disabled.count(pair_key) &&
                    sibling.status != ControllingLeafStatus::TerminalReady) {
                    std::string ready_reason;
                    if (!scheduler.setStatus(
                            bounded.id, ControllingLeafStatus::TerminalReady,
                            "round42_waiting_for_exact_live_sibling",
                            &ready_reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round42_terminal_ready_transition_failed:" +
                            ready_reason;
                        break;
                    }
                    writeSiblingCoverage(
                        pair_key, left, right, "",
                        options.round42_terminal_sibling_coalescing ==
                            "core-factored",
                        "waiting_for_sibling", nullptr, nullptr, nullptr,
                        std::min(left.lower_bound, right.lower_bound),
                        false, false, false, false, false,
                        "first_exact_sibling_reached_true_terminal_stage");
                    events << elapsedTelemetry()
                           << ",round42_terminal_sibling_wait," << bounded.id
                           << ',' << bounded.gamma_L << ',' << bounded.gamma_U
                           << ",terminal_ready,"
                           << scheduler.globalLowerBound() << ',' << verified_ub
                           << ',' << csvField(pair_key) << '\n';
                    continue;
                }
                if (!round42_sibling_pairs_disabled.count(pair_key) &&
                    sibling.status == ControllingLeafStatus::TerminalReady) {
                    std::string ready_reason;
                    if (!scheduler.setStatus(
                            bounded.id, ControllingLeafStatus::TerminalReady,
                            "round42_exact_live_sibling_pair_ready",
                            &ready_reason)) {
                        hard_failure = true;
                        result.external_gini_tree_failure_reason =
                            "round42_pair_ready_transition_failed:" +
                            ready_reason;
                        break;
                    }

                    const bool common_row_factoring =
                        options.round42_terminal_sibling_coalescing ==
                            "core-factored";
                    const std::string block_id =
                        "R42B_" + left.id + "__" + right.id;
                    const GiniIntervalGeometry union_interval{
                        left.gamma_L, right.gamma_U};
                    const std::vector<GiniIntervalGeometry> block_segments = {
                        {left.gamma_L, left.gamma_U},
                        {right.gamma_L, right.gamma_U}};
                    SolveOptions block_options = options;
                    block_options.interval_row_factory_round19 = true;
                    const StaticSegmentedBlockSpec block_spec =
                        makeStaticSegmentedBlockSpec(
                            instance, block_options, union_interval,
                            block_segments, verified_ub, 0.0,
                            "st-k2-p-core", common_row_factoring, false,
                            scheduler.certificateTolerance());
                    CanonicalCompactModelSpec block_model_spec;
                    block_model_spec.strengthened = true;
                    block_model_spec.interval_restricted = true;
                    block_model_spec.gamma_L = union_interval.lower;
                    block_model_spec.gamma_U = union_interval.upper;
                    block_model_spec.add_verified_incumbent_row = true;
                    block_model_spec.verified_incumbent = verified_ub;
                    block_model_spec.incumbent_epsilon = 0.0;
                    block_model_spec.static_segmented_gini = "st-k2-p-core";
                    block_model_spec.static_segments = block_segments;
                    block_model_spec.static_common_row_factoring =
                        common_row_factoring;
                    block_model_spec.static_model_identity =
                        block_spec.deterministic_model_identity;
                    const std::filesystem::path block_model_path =
                        artifact_dir / "models" / (block_id + ".lp");
                    const auto block_build_started = PaperClock::now();
                    CanonicalCompactModelArtifact block_artifact;
                    if (block_spec.valid) {
                        block_artifact = writeCanonicalCompactModel(
                            instance, block_options, block_model_path,
                            block_model_spec);
                        ++result.external_gini_tree_canonical_artifact_generation_count;
                    }
                    const double block_build_seconds =
                        std::chrono::duration<double>(
                            PaperClock::now() - block_build_started).count();
                    total_model_build_seconds += block_build_seconds;

                    auto reopenOriginalSiblings = [&]() {
                        std::string left_reason;
                        std::string right_reason;
                        const bool left_ok = scheduler.setStatus(
                            left.id, ControllingLeafStatus::Open, "",
                            &left_reason);
                        const bool right_ok = scheduler.setStatus(
                            right.id, ControllingLeafStatus::Open, "",
                            &right_reason);
                        runtime[left.id].terminal_ready = false;
                        runtime[right.id].terminal_ready = false;
                        if (!left_ok || !right_ok) {
                            hard_failure = true;
                            result.external_gini_tree_failure_reason =
                                "round42_fail_closed_reopen_failed:" +
                                left_reason + ":" + right_reason;
                        }
                    };

                    if (!block_spec.valid || !block_artifact.written) {
                        ++result.round42_sibling_fallback_events;
                        round42_sibling_pairs_disabled.insert(pair_key);
                        reopenOriginalSiblings();
                        writeSiblingCoverage(
                            pair_key, left, right, block_id,
                            common_row_factoring, "model_build_fallback",
                            &block_spec, &block_artifact, nullptr,
                            std::min(left.lower_bound, right.lower_bound),
                            false, false, false, false, true,
                            block_spec.valid
                                ? block_artifact.failure_reason
                                : block_spec.reason);
                        if (hard_failure) break;
                    } else {
                        const double block_remaining = globalDeadlineRemaining();
                        if (block_remaining <= 0.0) {
                            reopenOriginalSiblings();
                            if (!hard_failure) stopAtDeadline();
                            break;
                        }
                        FixedIntervalMipRequest block_request;
                        block_request.solve_kind =
                            FixedIntervalSolveKind::PaperTerminalMip;
                        block_request.leaf_id = block_id;
                        block_request.gamma_L = union_interval.lower;
                        block_request.gamma_U = union_interval.upper;
                        block_request.verified_cutoff = verified_ub;
                        block_request.global_deadline_remaining_seconds =
                            block_remaining;
                        block_request.new_leaf = true;
                        block_request.warm_start_enabled = false;
                        block_request.canonical_model_path =
                            block_artifact.path;
                        block_request.canonical_model_fingerprint =
                            block_artifact.sha256;
                        block_request.canonical_model_scope =
                            block_artifact.model_scope;
                        block_request.canonical_row_signature =
                            block_artifact.row_signature;
                        block_request.native_log_path =
                            artifact_dir / "native_logs" /
                            (block_id + "_terminal_mip.gurobi.log");
                        block_request.incremental_model_reuse_enabled = false;
                        block_request.retain_model_after_solve = false;
                        block_request.capture_native_bound_events = true;
                        const double block_process_launch =
                            processElapsedSeconds(options);
                        const double block_exact_launch = elapsedTelemetry();
                        const double block_other_bound = std::min(
                            otherRelevantMinimum(left.id),
                            otherRelevantMinimum(right.id));
                        ++result.external_gini_tree_terminal_mip_leaf_count;
                        ++result.external_gini_tree_exact_closure_launch_count;
                        ++result.round42_sibling_block_optimize_count;
                        const FixedIntervalMipOutcome block_outcome =
                            backend->solve(block_request);
                        optimize << block_id << ",MIP_BLOCK,"
                            << csvField(block_outcome.native_status) << ','
                            << block_outcome.optimize_return_code << ','
                            << block_remaining << ','
                            << block_outcome.solver_runtime_seconds << ','
                            << block_outcome.work << ',' << block_outcome.nodes
                            << ',' << block_outcome.simplex_iterations << ','
                            << block_outcome.barrier_iterations << ','
                            << block_outcome.memory_gb << ','
                            << block_artifact.sha256 << ','
                            << block_outcome.in_memory_model_reused << ','
                            << block_outcome.integer_domain_restored << ','
                            << csvField(block_outcome.basis_reuse_status) << ','
                            << csvField(block_outcome.native_log_path) << '\n';
                        for (const FixedIntervalNativeBoundEvent& native_event :
                                block_outcome.native_bound_events) {
                            if (!native_event.native_bound_available ||
                                !native_event.bound_improved) continue;
                            writeGlobalTrace(
                                block_process_launch +
                                    native_event.solver_runtime_seconds,
                                block_exact_launch +
                                    native_event.solver_runtime_seconds,
                                native_event.processed_nodes <= 0.0
                                    ? "round42_sibling_root_bound"
                                    : "round42_sibling_bound_improvement",
                                block_id,
                                std::max(
                                    std::min(left.lower_bound,
                                             right.lower_bound),
                                    native_event.native_bound),
                                block_other_bound,
                                "gurobi_cb_union_mip_objbnd_valid_bound");
                        }
                        const PaperTerminalMipDecision block_terminal =
                            evaluatePaperTerminalMipDecision(block_outcome);
                        if (!block_terminal.valid) {
                            ++result.round42_sibling_fallback_events;
                            round42_sibling_pairs_disabled.insert(pair_key);
                            reopenOriginalSiblings();
                            writeSiblingCoverage(
                                pair_key, left, right, block_id,
                                common_row_factoring,
                                "validation_fallback", &block_spec,
                                &block_artifact, &block_outcome,
                                std::min(left.lower_bound, right.lower_bound),
                                false, false, false, false, true,
                                block_terminal.reason + ":" +
                                    block_outcome.failure_reason);
                            if (hard_failure) break;
                        } else {
                            ControllingLeaf union_block;
                            union_block.id = block_id;
                            union_block.gamma_L = union_interval.lower;
                            union_block.gamma_U = union_interval.upper;
                            union_block.parent_id =
                                left.parent_id + "_R42_UNION";
                            union_block.split_depth = left.split_depth;
                            union_block.child_index = -1;
                            union_block.base_lower_bound = std::min(
                                left.base_lower_bound,
                                right.base_lower_bound);
                            union_block.lower_bound = std::min(
                                left.lower_bound, right.lower_bound);
                            union_block.lower_bound_sources = {
                                "minimum_original_sibling_valid_bound"};
                            union_block.cutoff =
                                std::min(left.cutoff, right.cutoff);
                            union_block.status = ControllingLeafStatus::Open;
                            std::string coalesce_reason;
                            if (!scheduler.coalesceSiblingLeavesAtomically(
                                    left.id, right.id, union_block,
                                    &coalesce_reason)) {
                                ++result.round42_sibling_fallback_events;
                                round42_sibling_pairs_disabled.insert(pair_key);
                                reopenOriginalSiblings();
                                writeSiblingCoverage(
                                    pair_key, left, right, block_id,
                                    common_row_factoring,
                                    "atomic_replacement_fallback",
                                    &block_spec, &block_artifact,
                                    &block_outcome, union_block.lower_bound,
                                    false, false, false, false, true,
                                    coalesce_reason);
                                if (hard_failure) break;
                            } else {
                                ++result.round42_sibling_pairs_coalesced;
                                result.round42_sibling_replaced_leaf_count += 2;
                                ++result.round42_sibling_atomic_coverage_events;
                                PaperLeafRuntime& block_state = runtime[block_id];
                                block_state.artifact_ready = true;
                                block_state.artifact = block_artifact;
                                block_state.lp_complete = true;
                                block_state.terminal_ready = true;
                                block_state.terminal_mip_started = true;
                                backend->discardLeaf(left.id);
                                backend->discardLeaf(right.id);
                                if (block_outcome.native_bound_available) {
                                    std::string merge_reason;
                                    if (!scheduler.mergeValidLowerBound(
                                            block_id,
                                            block_outcome.native_bound,
                                            "native_terminal_sibling_union_bound",
                                            &merge_reason)) {
                                        hard_failure = true;
                                        result.external_gini_tree_failure_reason =
                                            "round42_union_bound_merge_failed:" +
                                            merge_reason;
                                        break;
                                    }
                                }
                                bool incumbent_updated = false;
                                if (block_outcome.incumbent_available &&
                                    block_outcome.incumbent_independently_verified &&
                                    block_outcome.incumbent_objective <
                                        verified_ub - 1e-9) {
                                    verified_ub =
                                        block_outcome.incumbent_objective;
                                    best_routes = block_outcome.incumbent_routes;
                                    std::string cutoff_reason;
                                    if (!scheduler.tightenVerifiedCutoff(
                                            verified_ub, &cutoff_reason)) {
                                        hard_failure = true;
                                        result.external_gini_tree_failure_reason =
                                            "round42_union_cutoff_tightening_failed:" +
                                            cutoff_reason;
                                        break;
                                    }
                                    incumbent_updated = true;
                                    writeGlobalTrace(
                                        processElapsedSeconds(options),
                                        elapsedTelemetry(),
                                        "incumbent_improvement", block_id,
                                        scheduler.findLeaf(block_id)
                                            ? scheduler.findLeaf(block_id)->lower_bound
                                            : union_block.lower_bound,
                                        otherRelevantMinimum(block_id),
                                        "independently_verified_sibling_union_incumbent");
                                }
                                const bool unresolved_union =
                                    block_terminal.leave_open_and_stop;
                                bool exact_closure = false;
                                if (unresolved_union) {
                                    ++result.round42_sibling_unresolved_union_count;
                                } else {
                                    const ControllingLeafStatus block_status =
                                        block_outcome.infeasible
                                            ? ControllingLeafStatus::Empty
                                            : ControllingLeafStatus::Closed;
                                    std::string close_reason;
                                    if (!scheduler.setStatus(
                                            block_id, block_status,
                                            block_terminal.reason,
                                            &close_reason)) {
                                        hard_failure = true;
                                        result.external_gini_tree_failure_reason =
                                            "round42_union_closure_failed:" +
                                            close_reason;
                                        break;
                                    }
                                    exact_closure = true;
                                }
                                const ControllingLeaf* final_block =
                                    scheduler.findLeaf(block_id);
                                const double final_block_bound = final_block
                                    ? final_block->lower_bound
                                    : union_block.lower_bound;
                                writeSiblingCoverage(
                                    pair_key, left, right, block_id,
                                    common_row_factoring,
                                    unresolved_union
                                        ? "unresolved_union_retained"
                                        : "atomic_exact_closure",
                                    &block_spec, &block_artifact,
                                    &block_outcome, final_block_bound,
                                    exact_closure, unresolved_union,
                                    incumbent_updated, true, false,
                                    block_terminal.reason);
                                events << elapsedTelemetry()
                                    << ",round42_terminal_sibling_block,"
                                    << block_id << ',' << union_interval.lower
                                    << ',' << union_interval.upper << ','
                                    << csvField(block_outcome.native_status)
                                    << ',' << scheduler.globalLowerBound() << ','
                                    << verified_ub << ','
                                    << csvField(block_terminal.reason) << '\n';
                                writeGlobalTrace(
                                    processElapsedSeconds(options),
                                    elapsedTelemetry(),
                                    unresolved_union
                                        ? "interruption"
                                        : (block_outcome.infeasible
                                            ? "infeasible_closure"
                                            : "terminal_sibling_union_closure"),
                                    block_id,
                                    unresolved_union
                                        ? final_block_bound
                                        : std::numeric_limits<double>::infinity(),
                                    scheduler.globalLowerBound(),
                                    block_terminal.reason);
                                if (scheduler.globalLowerBound() >
                                        global_before +
                                            scheduler.certificateTolerance()) {
                                    last_global_lb_improvement =
                                        elapsedTelemetry();
                                }
                                if (unresolved_union) {
                                    stopAtDeadline();
                                    break;
                                }
                                continue;
                            }
                        }
                    }
                }
            }
        }
        if (hard_failure || global_deadline_stop) break;
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
              "terminal_ready,coalesced_block_id,coverage_member_ids,"
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
               << (state && state->terminal_ready) << ','
               << csvField(leaf.coalesced_block_id) << ','
               << csvField(join(leaf.coverage_member_ids)) << ','
               << (state ? state->c6_native_phase_count : 0) << ','
               << (state && state->c6_frontier_milestone_reached) << ','
               << (state && state->c6_children_ready) << ','
               << csvField(leaf.closure_source) << ','
               << csvField(sources.str()) << '\n';
        if (leaf.status == ControllingLeafStatus::Replaced ||
            leaf.status == ControllingLeafStatus::Coalesced ||
            leaf.parent_replaced) continue;
        ++final_count;
        all_bounds_valid = all_bounds_valid &&
            validFinalEnvelopeLeafBound(
                leaf.lower_bound,
                leaf.status == ControllingLeafStatus::Empty);
        if (leaf.status == ControllingLeafStatus::Open ||
            leaf.status == ControllingLeafStatus::Invalid ||
            leaf.status == ControllingLeafStatus::TerminalReady) {
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
        round43_active
            ? "minimum_valid_inherited_parent_lp_complete_depth_d_"
              "lookahead_partition_or_exact_envelope_parent_mip_bound_over_"
              "round43_nested_coverage"
        : (round42_sibling_coalescing
            ? "minimum_valid_inherited_lp_open_native_target_exact_mip_or_"
              "unresolved_sibling_union_bound_over_round42_coverage_objects"
        : (c6_nonblocking
            ? "minimum_valid_inherited_lp_open_native_target_or_exact_mip_"
              "bound_over_round31_c6_leaves"
            : (c5_bound_target
                ? "minimum_valid_inherited_lp_partial_native_or_exact_mip_"
                  "bound_over_round30_c5_leaves"
                : "minimum_valid_inherited_lp_or_terminal_mip_bound_over_"
                  "paper_leaves")));
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
        ? (round43_active
            ? "Round 43 unified envelope-refinement certificate: complete "
              "K0 initial coverage, complete depth-d LP profiles, "
              "validity-audited affine lower-envelope inheritance only to "
              "nested descendants, atomic midpoint refinement, exact "
              "unsplit-parent MIPs, monotone valid bounds, symmetric model "
              "lifecycle, and an independently verified global incumbent."
        : (round42_sibling_coalescing
            ? "Round 42 C6 terminal-sibling certificate: unchanged C6 "
              "pre-terminal decisions, exact sibling identity, atomic "
              "sibling-to-union coverage replacement, union-only native "
              "bounds, exact segmented block closures, monotone valid "
              "bounds, symmetric model lifecycle, and an independently "
              "verified global incumbent."
        : (c6_nonblocking
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
                      "global incumbent.")))))
        : "Paper external-tree strict certificate rejected: " +
            certificate.rejection_reason;
    if (round43_atlas) {
        result.external_gini_tree_strict_certified = false;
        result.external_gini_tree_certificate_class =
            "diagnostic_structural_atlas_only";
        result.external_gini_tree_certificate_rejection_reason =
            "round43_atlas_intentionally_omits_exact_parent_closures";
        result.strict_certified_original_problem = false;
        result.strict_certificate_class =
            "diagnostic_structural_atlas_only";
        result.strict_certificate_rejection_reason =
            "round43_atlas_intentionally_omits_exact_parent_closures";
        result.status = "round43_structural_atlas_complete";
        result.certificate =
            "Round 43 structural atlas only; no exact certificate claimed.";
    }
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
