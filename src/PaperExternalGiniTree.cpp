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
};

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
    SolveResult result = verified_seed;
    result.exact_phase_started = true;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "external-gini-tree";
    result.certificate_scope = "original_global_gini_external_tree";
    result.external_gini_tree_attempted = true;
    result.external_gini_tree_backend = options.external_gini_backend;
    result.external_gini_tree_lifecycle = c4_incremental
        ? "round29-same-leaf-in-memory-model"
        : "fresh-per-paper-event";
    result.external_gini_tree_scheduling =
        options.external_gini_scheduling;
    result.external_gini_tree_root_gamma_L = root_gamma_L;
    result.external_gini_tree_root_gamma_U = root_gamma_U;
    result.external_gini_tree_verified_upper_bound = verified_seed.objective;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason = "paper_tree_not_finalized";
    result.status = c4_incremental
        ? "round29_c4_external_gini_tree_running"
        : "paper_external_gini_tree_running";
    if (c4_incremental) {
        result.external_gini_tree_algorithm_arm = "C4-CANDIDATE";
        result.external_gini_tree_global_row_family_count =
            static_cast<long long>(kPaperGlobalFamilies.size());
        result.external_gini_tree_interval_row_family_count =
            static_cast<long long>(kPaperIntervalFamilies.size());
        result.external_gini_tree_global_row_families =
            join(kPaperGlobalFamilies);
        result.external_gini_tree_interval_row_families =
            join(kPaperIntervalFamilies);
        result.external_gini_tree_child_lookahead_required = true;
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
        result.external_gini_tree_implementation_boundary =
            "complete parent and child LP benefit rule with same-leaf "
            "in-memory Gurobi model retention; integer domain restored "
            "before exact parent MIP; no LP basis or native tree reuse claim";
    }

    const bool seed_valid =
        verified_seed.verification.original_solution_feasible &&
        verified_seed.verification.original_objective_recomputed &&
        verified_seed.verification.errors.empty() &&
        std::isfinite(verified_seed.objective);
    std::string c4_contract_reason;
    const bool c4_contract_valid = !c4_incremental ||
        round29C4FrozenOptionsValid(options, c4_contract_reason);
    if (!seed_valid || options.external_gini_backend != "gurobi" ||
        options.external_gini_warm_start || root_gamma_L < -1e-12 ||
        root_gamma_U < root_gamma_L - 1e-12 ||
        !verified_seed.frontier_covers_all_improving_gini_values ||
        !c4_contract_valid) {
        result.status = "paper_external_gini_tree_invalid_configuration";
        result.external_gini_tree_failure_reason = !seed_valid
            ? "same_run_seed_not_verified"
            : (options.external_gini_backend != "gurobi"
                ? "paper_lp_event_path_requires_gurobi"
                : (options.external_gini_warm_start
                    ? "paper_lp_event_path_forbids_warm_start"
                    : (!c4_contract_valid
                        ? c4_contract_reason
                        : "incomplete_or_invalid_root_range")));
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
        (c4_incremental &&
         flow_resolution.resolved != "round20-current")) {
        result.status = "paper_external_gini_tree_invalid_connectivity";
        result.external_gini_tree_failure_reason = !flow_resolution.valid
            ? flow_resolution.failure_reason
            : (!flow_counts.valid
                ? flow_counts.failure_reason
                : "c4_requires_f0_round20_current_connectivity");
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
            (c4_incremental ? "C4-CANDIDATE" : "C2-PAPER"));
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
    result.external_gini_tree_event_trace_path = event_path.string();
    result.external_gini_tree_leaf_ledger_path = leaf_path.string();
    result.external_gini_tree_optimize_ledger_path = optimize_path.string();
    result.external_gini_tree_lp_status_ledger_path = lp_path.string();
    result.external_gini_tree_parent_child_bound_ledger_path =
        bounds_path.string();
    result.external_gini_tree_split_decision_ledger_path = split_path.string();
    std::ofstream events(event_path), optimize(optimize_path), lp_ledger(lp_path),
        bound_ledger(bounds_path), split_ledger(split_path);
    events << "telemetry_seconds,event,leaf_id,gamma_L,gamma_U,status,global_lb,verified_ub,detail\n";
    optimize << "leaf_id,solve_kind,native_status,optimize_return_code,global_deadline_remaining_at_launch,solver_runtime,work,nodes,simplex_iterations,barrier_iterations,memory_gb,model_sha256,in_memory_model_reused,integer_domain_restored,basis_reuse_status,native_log\n";
    lp_ledger << "leaf_id,parent_id,depth,gamma_L,gamma_U,terminal_valid,optimal,infeasible,bound_available,lower_bound,native_status,work,telemetry_seconds\n";
    bound_ledger << "parent_id,parent_lp_bound,left_id,left_lp_bound,left_infeasible,right_id,right_lp_bound,right_infeasible,post_split_bound,tolerance,decision\n";
    split_ledger << "parent_id,eligible,decision_valid,split,child_infeasibility_trigger,strict_bound_trigger,reason\n";
    events.flush();
    optimize.flush();
    lp_ledger.flush();
    bound_ledger.flush();
    split_ledger.flush();
    recordProcessPhase(options, "first_tree_ledger_opened", "complete",
                       event_path.string());

    ControllingLeafScheduler scheduler(1e-7);
    const auto initial = makeLegacyFrontierIntervals(
        root_gamma_L, root_gamma_U, options.frontier_intervals);
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

    auto stopAtDeadline = [&]() {
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
        request.incremental_model_reuse_enabled = c4_incremental;
        request.retain_model_after_solve = c4_incremental;
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
        return true;
    };

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
            if (c4_incremental) backend->discardLeaf(selected.id);
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
        if (c4_incremental &&
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
            // Child LPs are structural lookahead events. They are evaluated
            // completely before the scheduler sees either child, preserving
            // atomic parent replacement.
            for (ControllingLeaf& child : children) {
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
                request.verified_cutoff = verified_seed.objective;
                request.global_deadline_remaining_seconds = remaining;
                request.new_leaf = true;
                request.canonical_model_path = child_state.artifact.path;
                request.canonical_model_fingerprint = child_state.artifact.sha256;
                request.canonical_model_scope = child_state.artifact.model_scope;
                request.canonical_row_signature = child_state.artifact.row_signature;
                request.native_log_path = artifact_dir / "native_logs" /
                    (child.id + "_lp.gurobi.log");
                request.incremental_model_reuse_enabled = c4_incremental;
                request.retain_model_after_solve = c4_incremental;
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
            const PaperLpSplitDecision split = evaluatePaperLpSplitDecision(
                bounded.lower_bound, runtime[children[0].id].lp,
                runtime[children[1].id].lp,
                scheduler.certificateTolerance());
            bound_ledger << bounded.id << ',' << bounded.lower_bound << ','
                         << children[0].id << ','
                         << runtime[children[0].id].lp.lower_bound << ','
                         << runtime[children[0].id].lp.infeasible << ','
                         << children[1].id << ','
                         << runtime[children[1].id].lp.lower_bound << ','
                         << runtime[children[1].id].lp.infeasible << ','
                         << split.post_split_lower_bound << ','
                         << scheduler.certificateTolerance() << ','
                         << csvField(split.reason) << '\n';
            split_ledger << bounded.id << ",true," << split.valid << ','
                         << split.should_split << ','
                         << split.child_infeasibility_trigger << ','
                         << split.strict_bound_improvement_trigger << ','
                         << csvField(split.reason) << '\n';
            if (!split.valid) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "paper_split_decision_invalid:" + split.reason;
                break;
            }
            if (split.should_split) {
                std::string reason;
                if (!scheduler.splitLeafAtomically(
                        bounded.id, children, &reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "paper_atomic_split_failed:" + reason;
                    break;
                }
                ++result.external_gini_tree_split_count;
                if (c4_incremental) backend->discardLeaf(bounded.id);
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
                        if (c4_incremental) {
                            backend->discardLeaf(child.id);
                        }
                    }
                }
                events << elapsedTelemetry() << ",atomic_split," << bounded.id
                       << ',' << bounded.gamma_L << ',' << bounded.gamma_U
                       << ",replaced," << scheduler.globalLowerBound() << ','
                       << verified_ub << ',' << csvField(split.reason) << '\n';
                split_parent = true;
            } else if (c4_incremental) {
                ++result.external_gini_tree_declined_split_count;
                backend->discardLeaf(children[0].id);
                backend->discardLeaf(children[1].id);
            }
        } else {
            split_ledger << bounded.id
                         << ",false,true,false,false,false,"
                         << csvField("structurally_terminal") << '\n';
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
        FixedIntervalMipRequest request;
        request.solve_kind = FixedIntervalSolveKind::PaperTerminalMip;
        request.leaf_id = bounded.id;
        request.gamma_L = bounded.gamma_L;
        request.gamma_U = bounded.gamma_U;
        request.verified_cutoff = verified_seed.objective;
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
        request.incremental_model_reuse_enabled = c4_incremental;
        request.retain_model_after_solve = false;
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
        }
        if (terminal.leave_open_and_stop) {
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
        if (scheduler.globalLowerBound() > global_before +
                scheduler.certificateTolerance()) {
            last_global_lb_improvement = elapsedTelemetry();
        }
    }

    std::ofstream leaves(leaf_path);
    leaves << "leaf_id,parent_id,depth,child_index,gamma_L,gamma_U,base_lower_bound,lower_bound,status,lp_complete,lp_optimal,lp_infeasible,lp_bound,terminal_mip_started,closure_source,lower_bound_sources\n";
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
            result.external_gini_tree_terminal_mip_optimize_count &&
        result.external_gini_tree_terminal_mip_leaf_count ==
            result.external_gini_tree_terminal_mip_optimize_count &&
        result.external_gini_tree_model_count ==
            result.external_gini_tree_model_free_count &&
        result.external_gini_tree_environment_count ==
            result.external_gini_tree_environment_free_count &&
        (c4_incremental
            ? result.external_gini_tree_same_leaf_resume_count ==
                result.external_gini_tree_in_memory_model_reuse_count
            : result.external_gini_tree_same_leaf_resume_count == 0) &&
        (!c4_incremental ||
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
        "minimum_valid_inherited_lp_or_terminal_mip_bound_over_paper_leaves";
    result.status = certificate.certified
        ? "optimal"
        : (hard_failure
            ? (c4_incremental
                ? "round29_c4_external_gini_tree_failed"
                : "paper_external_gini_tree_failed")
            : (global_deadline_stop
                ? (c4_incremental
                    ? "round29_c4_external_gini_tree_time_limit"
                    : "paper_external_gini_tree_time_limit")
                : (c4_incremental
                    ? "round29_c4_external_gini_tree_not_certified"
                    : "paper_external_gini_tree_not_certified")));
    result.certificate = certificate.certified
        ? (c4_incremental
            ? "Round 29 C4 engineering-exact certificate: complete range and "
              "atomic coverage, complete parent/child LP benefit decisions, "
              "exact unsplit-parent terminal MIPs, monotone valid bounds, "
              "same-leaf model lifecycle symmetry, and independently "
              "verified global incumbent."
            : "Round 27 engineering-exact paper external-tree certificate: exact interval coverage, complete optimal LP event decisions, exactly-once terminal MIPs, every relevant leaf closed, monotone valid bounds, completed no-restart lifecycle, and independently verified global incumbent.")
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
