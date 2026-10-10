#include "ReplicaExternalGiniTree.hpp"

#include "CanonicalCompactModel.hpp"
#include "ConnectivityFlow.hpp"
#include "ControllingLeafScheduler.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"
#include "IntervalRowFactory.hpp"
#include "PaperExternalGiniTree.hpp"
#include "ProcessPhaseLedger.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <unordered_map>
#include <vector>

namespace ebrp {
namespace {

using ReplicaClock = std::chrono::steady_clock;

constexpr int kInitialIntervalCount = 4;
constexpr int kAdaptiveMaximumDepth = 8;
constexpr int kSplitFactor = 2;
constexpr double kMinimumWidth = 1e-4;
constexpr double kCertificateTolerance = 1e-7;

const std::vector<std::string> kGlobalFamilies = {
    "inventory_conservation",
    "movement_reachability_domains",
    "visit_inventory_linking",
    "global_handling_capacity",
    "support_duration",
    "transfer_compat"
};

const std::vector<std::string> kIntervalFamilies = {
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

std::string csvField(const std::string& value) {
    std::string escaped;
    escaped.reserve(value.size() + 2);
    escaped.push_back('"');
    for (const char ch : value) {
        if (ch == '"') escaped.push_back('"');
        escaped.push_back(ch);
    }
    escaped.push_back('"');
    return escaped;
}

std::string join(const std::vector<std::string>& values) {
    std::ostringstream out;
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) out << ';';
        out << values[index];
    }
    return out.str();
}

struct ReplicaLeafRuntime {
    bool artifact_ready = false;
    CanonicalCompactModelArtifact artifact;
    std::string factory_signature;
    bool lp_complete = false;
    PaperLpResult lp;
    std::string lp_native_status = "not_run";
    bool terminal_mip_started = false;
    std::string terminal_native_status = "not_run";
};

void copyBackendStats(SolveResult& result,
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
    result.external_gini_tree_confirmed_continuation_count =
        stats.confirmed_continuation_count;
    result.external_gini_tree_partial_state_reuse_count =
        stats.partial_state_reuse_count;
    result.external_gini_tree_observed_fresh_restart_count =
        stats.observed_fresh_restart_count;
    result.external_gini_tree_ambiguous_retained_state_count =
        stats.ambiguous_retained_state_count;
    result.external_gini_tree_presolve_execution_count =
        stats.presolve_execution_count;
    result.external_gini_tree_root_relaxation_execution_count =
        stats.root_relaxation_execution_count;
    result.external_gini_tree_warm_start_candidate_count =
        stats.warm_start_candidate_count;
    result.external_gini_tree_warm_start_complete_count =
        stats.warm_start_complete_count;
    result.external_gini_tree_warm_start_submitted_count =
        stats.warm_start_submitted_count;
    result.external_gini_tree_warm_start_accepted_count =
        stats.warm_start_accepted_count;
    result.external_gini_tree_warm_start_rejected_count =
        stats.warm_start_rejected_count;
    result.external_gini_tree_warm_start_unknown_count =
        stats.warm_start_unknown_count;
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

bool exactFamilyContract(const IntervalRowFactoryResult& rows,
                         std::string& reason) {
    if (!rows.complete_round18_static_migration ||
        !rows.unsupported_active_families.empty()) {
        reason = "row_factory_has_unsupported_active_family";
        return false;
    }
    std::map<std::string, const IntervalRowFamilyRegistryEntry*> registry;
    for (const auto& entry : rows.family_registry) {
        registry[entry.family] = &entry;
    }
    auto check = [&](const std::vector<std::string>& expected,
                     IntervalRowScope scope) {
        for (const std::string& family : expected) {
            const auto found = registry.find(family);
            if (found == registry.end() || !found->second->active ||
                !found->second->implemented || found->second->scope != scope ||
                found->second->proof_tag.empty()) {
                reason = "missing_or_invalid_required_row_family:" + family;
                return false;
            }
        }
        return true;
    };
    if (!check(kGlobalFamilies, IntervalRowScope::Global) ||
        !check(kIntervalFamilies, IntervalRowScope::IntervalLocal)) {
        return false;
    }
    reason = "accepted_six_global_nine_interval_families";
    return true;
}

bool replicaStructuralOptionsValid(const SolveOptions& options,
                                   std::string& reason) {
    if (options.primal_heuristic != "hga-tgbc" ||
        options.primal_heuristic_seed != 20260626u ||
        options.primal_heuristic_stop != "generation-stagnation" ||
        options.primal_heuristic_no_improve_generations != 2000) {
        reason = "cplex_replica_requires_frozen_generation_hga_seed20260626_stagnation2000";
        return false;
    }
    const bool exact_geometry = options.frontier_intervals ==
            kInitialIntervalCount &&
        options.frontier_adaptive_split &&
        options.frontier_adaptive_max_depth == kAdaptiveMaximumDepth &&
        std::fabs(options.frontier_adaptive_min_width - kMinimumWidth) <=
            1e-12 &&
        options.frontier_adaptive_split_factor == kSplitFactor;
    if (!exact_geometry) {
        reason = "cplex_replica_geometry_not_frozen_4_binary_depth8_width1e-4";
        return false;
    }
    if (options.global_gini_tree_child_estimate_mode != "parent-copy" ||
        options.global_gini_tree_row_attachment_mode !=
            "full-inherited-pack" ||
        options.global_gini_tree_row_timing_mode != "deferred" ||
        options.global_gini_tree_native_mip_start ||
        options.global_gini_tree_presolve != "off" ||
        options.global_gini_tree_search != "traditional") {
        reason = "cplex_replica_s0_structural_contract_mismatch";
        return false;
    }
    reason = "accepted_corrected_s0_structural_contract";
    return true;
}

} // namespace

SolveResult solveReplicaExternalGiniTree(const Instance& instance,
                                         const SolveOptions& options,
                                         const SolveResult& verified_seed,
                                         double root_gamma_L,
                                         double root_gamma_U) {
    const auto started = ReplicaClock::now();
    auto elapsed = [&]() {
        return std::chrono::duration<double>(ReplicaClock::now() - started)
            .count();
    };
    auto remaining = [&]() {
        if (processDeadlineConfigured(options)) {
            return processWorkRemainingSeconds(options);
        }
        return options.solve_time_limit > 0.0
            ? options.solve_time_limit - elapsed()
            : std::numeric_limits<double>::max();
    };

    SolveResult result = verified_seed;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "external-gini-tree";
    result.certificate_scope = "original_global_gini_external_tree";
    result.external_gini_tree_attempted = true;
    result.external_gini_tree_backend = options.external_gini_backend;
    result.external_gini_tree_lifecycle = "fresh-per-replica-event";
    result.external_gini_tree_scheduling = "cplex-algorithm-replica";
    result.external_gini_tree_root_gamma_L = root_gamma_L;
    result.external_gini_tree_root_gamma_U = root_gamma_U;
    result.external_gini_tree_verified_upper_bound = verified_seed.objective;
    result.external_gini_tree_contract_initial_interval_count =
        kInitialIntervalCount;
    result.external_gini_tree_scheduler_initial_leaf_count = 1;
    result.external_gini_tree_initial_leaf_count = kInitialIntervalCount;
    result.external_gini_tree_global_row_family_count =
        static_cast<long long>(kGlobalFamilies.size());
    result.external_gini_tree_interval_row_family_count =
        static_cast<long long>(kIntervalFamilies.size());
    result.external_gini_tree_selector_variable_count = 0;
    result.external_gini_tree_contract_split_factor = kSplitFactor;
    result.external_gini_tree_contract_adaptive_max_depth =
        kAdaptiveMaximumDepth;
    result.external_gini_tree_contract_minimum_width = kMinimumWidth;
    result.external_gini_tree_certificate_tolerance =
        kCertificateTolerance;
    result.external_gini_tree_algorithm_arm = "C3-REPLICA";
    result.external_gini_tree_global_row_families = join(kGlobalFamilies);
    result.external_gini_tree_interval_row_families = join(kIntervalFamilies);
    result.external_gini_tree_best_bound_tie_rule =
        "lower_bound,smaller_width,greater_depth,lower_endpoint,upper_endpoint,leaf_id";
    result.external_gini_tree_implementation_boundary =
        "external_structural_gini_tree_with_fresh_gurobi_model_per_complete_lp_or_terminal_mip_event;native_bases_cuts_pseudocosts_and_node_queues_not_shared";
    result.external_gini_tree_structural_split_unconditional = true;
    result.external_gini_tree_child_lookahead_required = false;
    result.external_gini_tree_internal_budget_scheduling = false;
    result.external_gini_tree_native_tree_reuse_claimed = false;
    result.external_gini_tree_warm_start_enabled = false;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason = "replica_tree_not_finalized";
    result.status = "cplex_replica_external_gini_tree_running";
    result.exact_phase_started = true;

    const bool seed_valid =
        verified_seed.verification.original_solution_feasible &&
        verified_seed.verification.original_objective_recomputed &&
        verified_seed.verification.errors.empty() &&
        std::isfinite(verified_seed.objective);
    std::string structural_reason;
    const bool structural_valid =
        replicaStructuralOptionsValid(options, structural_reason);
    if (!seed_valid || options.external_gini_backend != "gurobi" ||
        options.external_gini_warm_start || root_gamma_L < -1e-12 ||
        root_gamma_U < root_gamma_L - 1e-12 ||
        !verified_seed.frontier_covers_all_improving_gini_values ||
        !structural_valid) {
        result.status = "cplex_replica_external_gini_tree_invalid_configuration";
        result.external_gini_tree_failure_reason = !seed_valid
            ? "same_run_seed_not_verified"
            : (options.external_gini_backend != "gurobi"
                ? "cplex_replica_requires_gurobi"
                : (options.external_gini_warm_start
                    ? "cplex_replica_forbids_warm_start"
                    : (!structural_valid ? structural_reason
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
        flow_resolution.resolved != "round20-current") {
        result.status = "cplex_replica_external_gini_tree_invalid_connectivity";
        result.external_gini_tree_failure_reason = !flow_resolution.valid
            ? flow_resolution.failure_reason
            : (!flow_counts.valid ? flow_counts.failure_reason
                                  : "cplex_replica_requires_f0_round20_current");
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

    IntervalRowFactoryRequest root_rows_request;
    root_rows_request.gamma_L = root_gamma_L;
    root_rows_request.gamma_U = root_gamma_U;
    root_rows_request.verified_incumbent = verified_seed.objective;
    root_rows_request.incumbent_epsilon = 0.0;
    root_rows_request.add_incumbent_row = true;
    root_rows_request.strengthened = true;
    const IntervalRowFactoryResult root_rows =
        buildRound18StaticIntervalRows(instance, options, root_rows_request);
    std::string row_contract_reason;
    if (!exactFamilyContract(root_rows, row_contract_reason)) {
        result.status = "cplex_replica_external_gini_tree_invalid_rows";
        result.external_gini_tree_failure_reason = row_contract_reason;
        return result;
    }
    result.external_gini_tree_row_factory_version = root_rows.factory_version;
    recordProcessPhase(
        options, "static_row_factory_preparation_complete", "complete",
        "factory=" + root_rows.factory_version);

    std::unique_ptr<FixedIntervalMipBackend> backend =
        makeGurobiFixedIntervalBackend(instance, options);
    recordProcessPhase(
        options, "external_backend_creation", backend ? "complete" : "failed",
        "backend=gurobi;arm=C3-REPLICA");
    if (!backend) {
        result.status = "cplex_replica_external_gini_tree_backend_invalid";
        result.external_gini_tree_failure_reason =
            "gurobi_backend_factory_failed";
        return result;
    }
    const FixedIntervalMipCapabilities capabilities = backend->capabilities();
    result.external_gini_tree_available = capabilities.available;
    if (!capabilities.available || !capabilities.fresh_per_attempt ||
        !capabilities.exact_zero_gap_roundtrip) {
        result.status = "cplex_replica_external_gini_tree_backend_unavailable";
        result.external_gini_tree_failure_reason = capabilities.available
            ? "gurobi_backend_missing_fresh_exact_event_capability"
            : capabilities.failure_reason;
        return result;
    }

    const auto stamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        ReplicaClock::now().time_since_epoch()).count();
    const std::filesystem::path artifact_dir =
        options.external_gini_artifact_dir.empty()
            ? std::filesystem::path("results") /
                "cplex_replica_external_gini_work" /
                (std::filesystem::path(instance.name).stem().string() + "_" +
                 std::to_string(stamp))
            : std::filesystem::path(options.external_gini_artifact_dir);
    std::filesystem::create_directories(artifact_dir / "models");
    std::filesystem::create_directories(artifact_dir / "native_logs");
    recordProcessPhase(
        options, "external_artifact_directory_creation", "complete",
        artifact_dir.string());

    const auto event_path = artifact_dir / "replica_tree_events.csv";
    const auto leaf_path = artifact_dir / "replica_leaf_ledger.csv";
    const auto optimize_path = artifact_dir / "replica_optimize_ledger.csv";
    const auto lp_path = artifact_dir / "lp_status_ledger.csv";
    const auto split_path = artifact_dir / "structural_split_ledger.csv";
    const auto coverage_path = artifact_dir / "coverage_ledger.csv";
    const auto inheritance_path = artifact_dir / "bound_inheritance_ledger.csv";
    const auto row_path = artifact_dir / "row_signature_ledger.csv";
    const auto global_bound_path = artifact_dir / "global_bound_trace.csv";
    result.external_gini_tree_event_trace_path = event_path.string();
    result.external_gini_tree_leaf_ledger_path = leaf_path.string();
    result.external_gini_tree_optimize_ledger_path = optimize_path.string();
    result.external_gini_tree_lp_status_ledger_path = lp_path.string();
    result.external_gini_tree_split_decision_ledger_path = split_path.string();
    result.external_gini_tree_coverage_ledger_path = coverage_path.string();
    result.external_gini_tree_bound_inheritance_ledger_path =
        inheritance_path.string();
    result.external_gini_tree_row_signature_ledger_path = row_path.string();
    result.external_gini_tree_global_bound_trace_path =
        global_bound_path.string();

    std::ofstream events(event_path), optimize(optimize_path),
        lp_ledger(lp_path), split_ledger(split_path),
        coverage_ledger(coverage_path), inheritance_ledger(inheritance_path),
        row_ledger(row_path), global_bound_ledger(global_bound_path);
    events << "telemetry_seconds,event,leaf_id,gamma_L,gamma_U,status,global_lb,verified_ub,detail\n";
    optimize << "leaf_id,solve_kind,native_status,optimize_return_code,global_deadline_remaining_at_launch,solver_runtime,work,nodes,simplex_iterations,barrier_iterations,memory_gb,presolve_observed,root_relaxation_observed,model_sha256,row_signature,native_log\n";
    lp_ledger << "leaf_id,parent_id,depth,gamma_L,gamma_U,terminal_valid,optimal,infeasible,bound_available,lower_bound,native_status,work,iterations,telemetry_seconds\n";
    split_ledger << "parent_id,depth,phase,eligible,split_point,unconditional,child_lookahead_required,reason\n";
    coverage_ledger << "parent_id,parent_L,parent_U,left_id,left_L,left_U,right_id,right_L,right_U,exact_coverage,atomic_replacement,tolerance\n";
    inheritance_ledger << "parent_id,parent_bound,child_id,child_inherited_bound,inheritance_valid,source\n";
    row_ledger << "leaf_id,gamma_L,gamma_U,factory_version,factory_signature,canonical_row_signature,model_sha256,global_family_count,interval_family_count,selector_variable_count,contract_valid\n";
    global_bound_ledger << "telemetry_seconds,event,leaf_id,global_lb,verified_ub\n";
    events.flush();
    optimize.flush();
    lp_ledger.flush();
    split_ledger.flush();
    coverage_ledger.flush();
    inheritance_ledger.flush();
    row_ledger.flush();
    global_bound_ledger.flush();
    recordProcessPhase(options, "first_tree_ledger_opened", "complete",
                       event_path.string());

    ControllingLeafScheduler scheduler(kCertificateTolerance);
    ControllingLeaf root;
    root.id = "R";
    root.gamma_L = root_gamma_L;
    root.gamma_U = root_gamma_U;
    root.base_lower_bound = root_gamma_L;
    root.lower_bound = root_gamma_L;
    root.lower_bound_sources = {
        "objective_nonnegative_penalty_and_root_gini_floor"};
    root.cutoff = verified_seed.objective;
    std::string scheduler_reason;
    bool hard_failure = !scheduler.addLeaf(root, &scheduler_reason);
    bool deadline_stop = false;
    result.external_gini_tree_root_coverage_valid =
        !hard_failure && exactIntervalCoverage(
            {root_gamma_L, root_gamma_U}, {{root_gamma_L, root_gamma_U}},
            scheduler.certificateTolerance());
    if (!result.external_gini_tree_root_coverage_valid) {
        hard_failure = true;
        result.external_gini_tree_failure_reason = hard_failure
            ? "initial_root_add_or_coverage_failed:" + scheduler_reason
            : "initial_root_coverage_failed";
    }
    coverage_ledger << "ROOT," << std::setprecision(17) << root_gamma_L << ','
                    << root_gamma_U << ",R," << root_gamma_L << ','
                    << root_gamma_U << ",NA,0,0,"
                    << result.external_gini_tree_root_coverage_valid
                    << ",true," << scheduler.certificateTolerance() << '\n';
    global_bound_ledger << elapsed() << ",initialize,R,"
                        << scheduler.globalLowerBound() << ','
                        << verified_seed.objective << '\n';

    std::unordered_map<std::string, ReplicaLeafRuntime> runtime;
    double verified_ub = verified_seed.objective;
    std::vector<RoutePlan> best_routes = verified_seed.routes;
    double total_model_build_seconds = 0.0;
    bool first_model_build_recorded = false;
    bool first_tree_event_recorded = false;
    bool first_lp_launch_recorded = false;
    double last_global_lb_improvement = -1.0;

    auto stopAtDeadline = [&]() {
        if (!deadline_stop) {
            deadline_stop = true;
            ++result.external_gini_tree_global_deadline_interruption_count;
            result.external_gini_tree_failure_reason =
                "overall_global_deadline";
        }
    };

    auto ensureArtifact = [&](const ControllingLeaf& leaf,
                              ReplicaLeafRuntime& state) -> bool {
        if (state.artifact_ready) {
            if (std::filesystem::exists(state.artifact.path) &&
                fileSha256(state.artifact.path) == state.artifact.sha256) {
                ++result.external_gini_tree_canonical_artifact_cache_hit_count;
                return true;
            }
            ++result.external_gini_tree_canonical_artifact_invalidation_count;
            result.external_gini_tree_failure_reason =
                "replica_immutable_artifact_changed:" + leaf.id;
            return false;
        }
        if (remaining() <= 0.0) {
            stopAtDeadline();
            return false;
        }
        IntervalRowFactoryRequest row_request;
        row_request.gamma_L = leaf.gamma_L;
        row_request.gamma_U = leaf.gamma_U;
        row_request.verified_incumbent = verified_seed.objective;
        row_request.incumbent_epsilon = 0.0;
        row_request.add_incumbent_row = true;
        row_request.strengthened = true;
        const IntervalRowFactoryResult rows =
            buildRound18StaticIntervalRows(instance, options, row_request);
        std::string contract_reason;
        if (!exactFamilyContract(rows, contract_reason)) {
            result.external_gini_tree_failure_reason =
                "replica_leaf_row_contract_failed:" + leaf.id + ':' +
                contract_reason;
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
        const auto build_started = ReplicaClock::now();
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
            ReplicaClock::now() - build_started).count();
        total_model_build_seconds += build_seconds;
        ++result.external_gini_tree_canonical_artifact_generation_count;
        if (!first_model_build_recorded) {
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
        state.factory_signature = rows.aggregate_signature;
        state.artifact_ready = state.artifact.written;
        row_ledger << leaf.id << ',' << std::setprecision(17) << leaf.gamma_L
                   << ',' << leaf.gamma_U << ',' << rows.factory_version << ','
                   << rows.aggregate_signature << ','
                   << state.artifact.row_signature << ','
                   << state.artifact.sha256 << ',' << kGlobalFamilies.size()
                   << ',' << kIntervalFamilies.size() << ",0,"
                   << state.artifact_ready << '\n';
        if (!state.artifact_ready) {
            result.external_gini_tree_failure_reason =
                "replica_static_interval_model_build_failed:" +
                state.artifact.failure_reason;
        }
        return state.artifact_ready;
    };

    auto recordOptimize = [&](const ControllingLeaf& leaf,
                              const char* kind,
                              double launch_remaining,
                              const ReplicaLeafRuntime& state,
                              const FixedIntervalMipOutcome& outcome) {
        optimize << leaf.id << ',' << kind << ','
                 << csvField(outcome.native_status) << ','
                 << outcome.optimize_return_code << ',' << launch_remaining
                 << ',' << outcome.solver_runtime_seconds << ','
                 << outcome.work << ',' << outcome.nodes << ','
                 << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ',' << outcome.memory_gb
                 << ',' << outcome.presolve_rerun_observed << ','
                 << outcome.root_relaxation_rerun_observed << ','
                 << state.artifact.sha256 << ','
                 << state.artifact.row_signature << ','
                 << csvField(outcome.native_log_path) << '\n';
    };

    while (!hard_failure && !deadline_stop &&
           !scheduler.everyRelevantLeafClosed()) {
        if (!first_tree_event_recorded) {
            recordProcessPhase(
                options, "first_external_tree_event", "start",
                "scheduler_select_next");
            first_tree_event_recorded = true;
        }
        if (remaining() <= 0.0) {
            stopAtDeadline();
            break;
        }
        const double global_before = scheduler.globalLowerBound();
        const ControllingLeafSelection selection =
            scheduler.selectNextCplexReplica();
        if (!selection.available) break;
        const ControllingLeaf* selected_ptr =
            scheduler.findLeaf(selection.selected_leaf_id);
        if (!selected_ptr) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_selected_leaf_missing";
            break;
        }
        const ControllingLeaf selected = *selected_ptr;
        ReplicaLeafRuntime& state = runtime[selected.id];
        if (state.lp_complete) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_open_leaf_lp_reselected:" + selected.id;
            break;
        }
        if (!ensureArtifact(selected, state)) {
            if (!deadline_stop) hard_failure = true;
            break;
        }
        const double lp_remaining = remaining();
        if (lp_remaining <= 0.0) {
            stopAtDeadline();
            break;
        }
        FixedIntervalMipRequest lp_request;
        lp_request.solve_kind = FixedIntervalSolveKind::PaperLpRelaxation;
        lp_request.leaf_id = selected.id;
        lp_request.gamma_L = selected.gamma_L;
        lp_request.gamma_U = selected.gamma_U;
        lp_request.verified_cutoff = verified_seed.objective;
        lp_request.global_deadline_remaining_seconds = lp_remaining;
        lp_request.new_leaf = true;
        lp_request.warm_start_enabled = false;
        lp_request.canonical_model_path = state.artifact.path;
        lp_request.canonical_model_fingerprint = state.artifact.sha256;
        lp_request.canonical_model_scope = state.artifact.model_scope;
        lp_request.canonical_row_signature = state.artifact.row_signature;
        lp_request.native_log_path = artifact_dir / "native_logs" /
            (selected.id + "_lp.gurobi.log");
        lp_request.verified_start_routes = best_routes;
        lp_request.verified_start_source = "same_run_verified_incumbent_gate_only";
        if (!first_lp_launch_recorded) {
            recordProcessPhase(
                options, "first_lp_optimize_launch", "start",
                "leaf=" + selected.id);
            first_lp_launch_recorded = true;
        }
        const FixedIntervalMipOutcome lp_outcome = backend->solve(lp_request);
        state.lp_native_status = lp_outcome.native_status;
        recordOptimize(selected, "LP", lp_remaining, state, lp_outcome);
        if (lp_outcome.interrupted) {
            events << elapsed() << ",lp_interrupted," << selected.id << ','
                   << selected.gamma_L << ',' << selected.gamma_U << ",open,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField("overall_deadline") << '\n';
            stopAtDeadline();
            break;
        }
        state.lp.terminal_valid = lp_outcome.attempted &&
            lp_outcome.available && lp_outcome.solver_finalization_reached &&
            lp_outcome.lp_terminal_valid &&
            lp_outcome.exact_zero_gap_roundtrip &&
            lp_outcome.model_fingerprint_matches_request &&
            lp_outcome.feasibility_consistency_gate;
        state.lp.optimal = lp_outcome.optimal;
        state.lp.infeasible = lp_outcome.infeasible;
        state.lp.bound_available = lp_outcome.native_bound_available;
        state.lp.lower_bound = lp_outcome.native_bound;
        state.lp_complete = state.lp.terminal_valid;
        lp_ledger << selected.id << ',' << csvField(selected.parent_id) << ','
                  << selected.split_depth << ',' << std::setprecision(17)
                  << selected.gamma_L << ',' << selected.gamma_U << ','
                  << state.lp.terminal_valid << ',' << state.lp.optimal << ','
                  << state.lp.infeasible << ',' << state.lp.bound_available
                  << ',' << state.lp.lower_bound << ','
                  << csvField(lp_outcome.native_status) << ','
                  << lp_outcome.work << ',' << lp_outcome.simplex_iterations
                  << ',' << elapsed() << '\n';
        if (!state.lp_complete ||
            (!state.lp.infeasible &&
             (!state.lp.optimal || !state.lp.bound_available ||
              !std::isfinite(state.lp.lower_bound)))) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                lp_outcome.failure_reason == "none"
                ? "replica_lp_not_complete_terminal_valid:" + selected.id
                : lp_outcome.failure_reason;
            break;
        }
        if (state.lp.infeasible) {
            ++result.external_gini_tree_lp_infeasible_leaf_count;
            if (!scheduler.setStatus(
                    selected.id, ControllingLeafStatus::Empty,
                    "complete_interval_lp_infeasible", &scheduler_reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_lp_infeasible_closure_failed:" +
                    scheduler_reason;
                break;
            }
            events << elapsed() << ",lp_infeasible," << selected.id << ','
                   << selected.gamma_L << ',' << selected.gamma_U << ",empty,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField("complete_interval_lp_infeasible") << '\n';
            global_bound_ledger << elapsed() << ",lp_infeasible,"
                                << selected.id << ','
                                << scheduler.globalLowerBound() << ','
                                << verified_ub << '\n';
            continue;
        }
        if (!scheduler.mergeValidLowerBound(
                selected.id, state.lp.lower_bound,
                "complete_optimal_interval_lp_bound", &scheduler_reason)) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_lp_bound_merge_failed:" + scheduler_reason;
            break;
        }
        const ControllingLeaf* bounded_ptr = scheduler.findLeaf(selected.id);
        if (!bounded_ptr) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_leaf_missing_after_lp";
            break;
        }
        const ControllingLeaf bounded = *bounded_ptr;
        events << elapsed() << ",lp_complete," << bounded.id << ','
               << bounded.gamma_L << ',' << bounded.gamma_U << ",open,"
               << scheduler.globalLowerBound() << ',' << verified_ub << ','
               << csvField("complete_optimal_interval_lp_bound") << '\n';
        global_bound_ledger << elapsed() << ",lp_complete," << bounded.id
                            << ',' << scheduler.globalLowerBound() << ','
                            << verified_ub << '\n';

        if (bounded.lower_bound >=
            bounded.cutoff - scheduler.certificateTolerance()) {
            ++result.external_gini_tree_lp_pruned_leaf_count;
            if (!scheduler.setStatus(
                    bounded.id, ControllingLeafStatus::Fathomed,
                    "complete_lp_bound_cannot_improve_verified_incumbent",
                    &scheduler_reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_lp_fathom_failed:" + scheduler_reason;
                break;
            }
            events << elapsed() << ",lp_bound_prune," << bounded.id << ','
                   << bounded.gamma_L << ',' << bounded.gamma_U
                   << ",fathomed," << scheduler.globalLowerBound() << ','
                   << verified_ub << ','
                   << csvField("lp_bound_ge_verified_cutoff_minus_tolerance")
                   << '\n';
            continue;
        }

        const CplexReplicaStructuralSplit structural =
            evaluateCplexReplicaStructuralSplit(
                root_gamma_L, root_gamma_U, bounded.gamma_L,
                bounded.gamma_U, bounded.split_depth,
                kInitialIntervalCount, kAdaptiveMaximumDepth,
                kMinimumWidth, kSplitFactor);
        split_ledger << bounded.id << ',' << bounded.split_depth << ','
                     << cplexReplicaSplitPhaseName(structural.phase) << ','
                     << structural.eligible << ',' << std::setprecision(17)
                     << structural.split_point << ','
                     << structural.eligible << ",false,"
                     << csvField(structural.reason) << '\n';
        if (structural.eligible) {
            const std::vector<GiniIntervalGeometry> geometry = {
                {bounded.gamma_L, structural.split_point},
                {structural.split_point, bounded.gamma_U}};
            std::string coverage_reason;
            const bool exact_coverage = exactIntervalCoverage(
                {bounded.gamma_L, bounded.gamma_U}, geometry,
                scheduler.certificateTolerance(), &coverage_reason);
            if (!exact_coverage) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_structural_child_coverage_failed:" +
                    coverage_reason;
                break;
            }
            std::vector<ControllingLeaf> children;
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
                child.lower_bound_sources = {
                    "inherited_complete_parent_lp_bound"};
                child.cutoff = bounded.cutoff;
                children.push_back(child);
            }
            if (!scheduler.splitLeafAtomically(
                    bounded.id, children, &scheduler_reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_atomic_split_failed:" + scheduler_reason;
                break;
            }
            ++result.external_gini_tree_split_count;
            ++result.external_gini_tree_unconditional_structural_split_count;
            ++result.external_gini_tree_replaced_parent_count;
            result.external_gini_tree_max_observed_depth = std::max(
                result.external_gini_tree_max_observed_depth,
                static_cast<long long>(bounded.split_depth + 1));
            coverage_ledger << bounded.id << ',' << bounded.gamma_L << ','
                            << bounded.gamma_U << ',' << children[0].id << ','
                            << children[0].gamma_L << ','
                            << children[0].gamma_U << ',' << children[1].id
                            << ',' << children[1].gamma_L << ','
                            << children[1].gamma_U << ",true,true,"
                            << scheduler.certificateTolerance() << '\n';
            for (const ControllingLeaf& child : children) {
                inheritance_ledger << bounded.id << ','
                                   << bounded.lower_bound << ',' << child.id
                                   << ',' << child.lower_bound << ",true,"
                                   << csvField(
                                          "inherited_complete_parent_lp_bound")
                                   << '\n';
            }
            events << elapsed() << ",atomic_unconditional_split,"
                   << bounded.id << ',' << bounded.gamma_L << ','
                   << bounded.gamma_U << ",replaced,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField(cplexReplicaSplitPhaseName(structural.phase))
                   << '\n';
            global_bound_ledger << elapsed() << ",atomic_split,"
                                << bounded.id << ','
                                << scheduler.globalLowerBound() << ','
                                << verified_ub << '\n';
            continue;
        }

        if (state.terminal_mip_started) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_same_leaf_terminal_mip_restart:" + bounded.id;
            break;
        }
        const double mip_remaining = remaining();
        if (mip_remaining <= 0.0) {
            stopAtDeadline();
            break;
        }
        state.terminal_mip_started = true;
        ++result.external_gini_tree_terminal_mip_leaf_count;
        FixedIntervalMipRequest mip_request;
        mip_request.solve_kind = FixedIntervalSolveKind::PaperTerminalMip;
        mip_request.leaf_id = bounded.id;
        mip_request.gamma_L = bounded.gamma_L;
        mip_request.gamma_U = bounded.gamma_U;
        mip_request.verified_cutoff = verified_seed.objective;
        mip_request.global_deadline_remaining_seconds = mip_remaining;
        mip_request.new_leaf = true;
        mip_request.warm_start_enabled = false;
        mip_request.canonical_model_path = state.artifact.path;
        mip_request.canonical_model_fingerprint = state.artifact.sha256;
        mip_request.canonical_model_scope = state.artifact.model_scope;
        mip_request.canonical_row_signature = state.artifact.row_signature;
        mip_request.native_log_path = artifact_dir / "native_logs" /
            (bounded.id + "_terminal_mip.gurobi.log");
        mip_request.verified_start_routes = best_routes;
        mip_request.verified_start_source =
            "same_run_verified_incumbent_gate_only_not_warm_start";
        const FixedIntervalMipOutcome mip_outcome = backend->solve(mip_request);
        state.terminal_native_status = mip_outcome.native_status;
        recordOptimize(bounded, "MIP", mip_remaining, state, mip_outcome);
        const PaperTerminalMipDecision terminal =
            evaluatePaperTerminalMipDecision(mip_outcome);
        if (!terminal.valid) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = terminal.reason + ':' +
                (mip_outcome.failure_reason.empty()
                    ? "none" : mip_outcome.failure_reason);
            break;
        }
        if (mip_outcome.native_bound_available) {
            if (!scheduler.mergeValidLowerBound(
                    bounded.id, mip_outcome.native_bound,
                    "native_exact_terminal_mip_bound", &scheduler_reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_terminal_bound_merge_failed:" + scheduler_reason;
                break;
            }
        }
        if (mip_outcome.incumbent_available &&
            mip_outcome.incumbent_independently_verified &&
            mip_outcome.incumbent_objective < verified_ub - 1e-9) {
            verified_ub = mip_outcome.incumbent_objective;
            best_routes = mip_outcome.incumbent_routes;
            if (!scheduler.tightenVerifiedCutoff(
                    verified_ub, &scheduler_reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "replica_verified_cutoff_tightening_failed:" +
                    scheduler_reason;
                break;
            }
            std::vector<std::string> newly_prunable;
            for (const ControllingLeaf& candidate : scheduler.leaves()) {
                if (candidate.id != bounded.id &&
                    (candidate.status == ControllingLeafStatus::Open ||
                     candidate.status == ControllingLeafStatus::Invalid) &&
                    candidate.lower_bound >= verified_ub -
                        scheduler.certificateTolerance()) {
                    newly_prunable.push_back(candidate.id);
                }
            }
            for (const std::string& leaf_id : newly_prunable) {
                if (!scheduler.setStatus(
                        leaf_id, ControllingLeafStatus::Fathomed,
                        "inherited_or_complete_lp_bound_cannot_improve_tightened_verified_incumbent",
                        &scheduler_reason)) {
                    hard_failure = true;
                    result.external_gini_tree_failure_reason =
                        "replica_tightened_cutoff_fathom_failed:" +
                        scheduler_reason;
                    break;
                }
                ++result.external_gini_tree_lp_pruned_leaf_count;
                events << elapsed() << ",tightened_cutoff_bound_prune,"
                       << leaf_id << ",0,0,fathomed,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << csvField(
                              "valid_inherited_or_complete_lp_bound") << '\n';
            }
            if (hard_failure) break;
            events << elapsed() << ",verified_incumbent_improvement,"
                   << bounded.id << ',' << bounded.gamma_L << ','
                   << bounded.gamma_U << ",verified,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField("independently_verified_terminal_mip_incumbent")
                   << '\n';
        }
        if (terminal.leave_open_and_stop) {
            events << elapsed() << ",terminal_mip_interrupted,"
                   << bounded.id << ',' << bounded.gamma_L << ','
                   << bounded.gamma_U << ",open,"
                   << scheduler.globalLowerBound() << ',' << verified_ub << ','
                   << csvField("overall_deadline") << '\n';
            stopAtDeadline();
            break;
        }
        const ControllingLeafStatus close_status = mip_outcome.infeasible
            ? ControllingLeafStatus::Empty : ControllingLeafStatus::Closed;
        if (!scheduler.setStatus(
                bounded.id, close_status, terminal.reason,
                &scheduler_reason)) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "replica_terminal_leaf_closure_failed:" + scheduler_reason;
            break;
        }
        events << elapsed() << ",terminal_mip_complete," << bounded.id << ','
               << bounded.gamma_L << ',' << bounded.gamma_U << ','
               << controllingLeafStatusName(close_status) << ','
               << scheduler.globalLowerBound() << ',' << verified_ub << ','
               << csvField(terminal.reason) << '\n';
        global_bound_ledger << elapsed() << ",terminal_mip_complete,"
                            << bounded.id << ','
                            << scheduler.globalLowerBound() << ','
                            << verified_ub << '\n';
        if (scheduler.globalLowerBound() >
            global_before + scheduler.certificateTolerance()) {
            last_global_lb_improvement = elapsed();
        }
    }

    std::ofstream leaves(leaf_path);
    leaves << "leaf_id,parent_id,child_index,depth,gamma_L,gamma_U,base_lower_bound,current_lower_bound,cutoff,status,lp_complete,lp_optimal,lp_infeasible,lp_bound,lp_native_status,terminal_mip_started,terminal_native_status,closure_source,model_sha256,row_signature,parent_child_coverage_valid,parent_replaced,lower_bound_sources\n";
    long long final_count = 0;
    long long open_count = 0;
    long long closed_count = 0;
    bool all_bounds_valid = true;
    for (const ControllingLeaf& leaf : scheduler.leaves()) {
        const auto found = runtime.find(leaf.id);
        const ReplicaLeafRuntime* state = found == runtime.end()
            ? nullptr : &found->second;
        leaves << leaf.id << ',' << csvField(leaf.parent_id) << ','
               << leaf.child_index << ',' << leaf.split_depth << ','
               << std::setprecision(17) << leaf.gamma_L << ',' << leaf.gamma_U
               << ',' << leaf.base_lower_bound << ',' << leaf.lower_bound << ','
               << leaf.cutoff << ',' << controllingLeafStatusName(leaf.status)
               << ',' << (state && state->lp_complete) << ','
               << (state && state->lp.optimal) << ','
               << (state && state->lp.infeasible) << ','
               << (state ? state->lp.lower_bound : 0.0) << ','
               << csvField(state ? state->lp_native_status : "not_run") << ','
               << (state && state->terminal_mip_started) << ','
               << csvField(state ? state->terminal_native_status : "not_run")
               << ',' << csvField(leaf.closure_source) << ','
               << (state ? state->artifact.sha256 : "") << ','
               << (state ? state->artifact.row_signature : "") << ','
               << leaf.parent_child_coverage_valid << ','
               << leaf.parent_replaced << ','
               << csvField(join(leaf.lower_bound_sources)) << '\n';
        if (leaf.status == ControllingLeafStatus::Replaced ||
            leaf.parent_replaced) {
            continue;
        }
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
    result.external_gini_tree_global_lower_bound =
        scheduler.globalLowerBound();
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
        result.verification.errors.empty() &&
        std::fabs(result.objective - verified_ub) <= 1e-7;

    backend->release();
    copyBackendStats(result, backend->stats());
    result.external_gini_tree_model_build_seconds += total_model_build_seconds;
    result.external_gini_tree_canonical_artifact_generation_seconds =
        total_model_build_seconds;
    result.external_gini_tree_final_stagnation_seconds =
        last_global_lb_improvement >= 0.0
        ? std::max(0.0, elapsed() - last_global_lb_improvement)
        : elapsed();
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
        result.external_gini_tree_same_leaf_resume_count == 0 &&
        result.external_gini_tree_fresh_restart_count == 0 &&
        result.external_gini_tree_child_restart_count == 0 &&
        result.external_gini_tree_reset_call_count == 0 &&
        result.external_gini_tree_warm_start_submitted_count == 0;

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
        "minimum_valid_inherited_complete_lp_or_exact_terminal_mip_bound_over_nonreplaced_replica_leaves";
    result.status = certificate.certified
        ? "optimal"
        : (hard_failure ? "cplex_replica_external_gini_tree_failed"
                        : (deadline_stop
                            ? "cplex_replica_external_gini_tree_time_limit"
                            : "cplex_replica_external_gini_tree_not_certified"));
    result.certificate = certificate.certified
        ? "Round 28 engineering-exact CPLEX-algorithm-replica certificate: complete improving-range coverage, unconditional accepted S0 structural splits, inherited complete-LP bounds, exact terminal interval MIPs, every relevant leaf closed, lifecycle symmetry, and an independently verified global incumbent."
        : "CPLEX-algorithm-replica strict certificate rejected: " +
            certificate.rejection_reason;
    if (result.external_gini_tree_failure_reason.empty()) {
        result.external_gini_tree_failure_reason = "none";
    }
    result.runtime_seconds = elapsed();
    result.wall_time_seconds = result.runtime_seconds;
    result.actual_runtime_seconds = result.runtime_seconds;
    result.graceful_deadline_finalization = deadline_stop && !hard_failure;
    return result;
}

} // namespace ebrp
