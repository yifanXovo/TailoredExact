#include "ExternalGiniTree.hpp"

#include "CanonicalCompactModel.hpp"
#include "ControllingLeafScheduler.hpp"
#include "ConnectivityFlow.hpp"
#include "CplexBaseline.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"
#include "ProcessPhaseLedger.hpp"
#include "StrictCertificate.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <limits>
#include <memory>
#include <sstream>
#include <unordered_map>
#include <utility>

namespace ebrp {
namespace {

using Clock = std::chrono::steady_clock;

std::string csvEscape(const std::string& value) {
    if (value.find_first_of(",\"\r\n") == std::string::npos) return value;
    std::string out = "\"";
    for (char ch : value) out += ch == '"' ? "\"\"" : std::string(1, ch);
    out += '"';
    return out;
}

struct NativePhaseLogEvidence {
    bool presolve_time_available = false;
    double presolve_seconds = 0.0;
    bool root_time_available = false;
    double root_seconds = 0.0;
};

NativePhaseLogEvidence inspectCplexNativePhaseLog(
        const std::filesystem::path& path) {
    NativePhaseLogEvidence evidence;
    std::ifstream stream(path);
    if (!stream) return evidence;
    const std::string text((std::istreambuf_iterator<char>(stream)),
                           std::istreambuf_iterator<char>());
    auto sumReportedSeconds = [&text](const std::string& marker,
                                      bool& available) {
        double total = 0.0;
        std::size_t cursor = 0;
        while ((cursor = text.find(marker, cursor)) != std::string::npos) {
            cursor += marker.size();
            try {
                std::size_t consumed = 0;
                const double seconds = std::stod(text.substr(cursor), &consumed);
                if (std::isfinite(seconds) && seconds >= 0.0) {
                    total += seconds;
                    available = true;
                }
                cursor += std::max<std::size_t>(consumed, 1);
            } catch (const std::exception&) {
                ++cursor;
            }
        }
        return total;
    };
    evidence.presolve_seconds = sumReportedSeconds(
        "Presolve time = ", evidence.presolve_time_available);
    evidence.root_seconds = sumReportedSeconds(
        "Root relaxation solution time = ", evidence.root_time_available);
    return evidence;
}

class CplexFixedIntervalBackend final : public FixedIntervalMipBackend {
public:
    CplexFixedIntervalBackend(const Instance& instance,
                              const SolveOptions& options)
        : instance_(instance), options_(options) {}

    FixedIntervalMipCapabilities capabilities() const override {
        FixedIntervalMipCapabilities out;
        out.backend = "cplex";
        out.available = true;
        // This adapter intentionally uses a fresh callable-library lifecycle.
        // It makes no unsupported continuation claim.
        out.retained_same_leaf_resume = false;
        out.fresh_per_attempt = true;
        out.verified_complete_mip_start = false;
        out.native_continuation_evidence = false;
        out.exact_zero_gap_roundtrip = true;
        out.failure_reason = "none";
        return out;
    }

    FixedIntervalMipOutcome solve(
        const FixedIntervalMipRequest& request) override {
        FixedIntervalMipOutcome out;
        out.attempted = true;
        if (request.solve_kind != FixedIntervalSolveKind::LegacyMipQuantum) {
            out.failure_reason = "paper_lp_event_path_requires_gurobi";
            return out;
        }
        out.available = true;
        out.presolve_time_status =
            "unavailable_cplex_callable_library_has_no_safe_phase_timer";
        out.root_time_status =
            "unavailable_cplex_callable_library_has_no_safe_phase_timer";
        out.fresh_restart = true;
        out.child_restart = request.new_leaf;
        ++stats_.fresh_restart_count;
        if (request.new_leaf) ++stats_.child_restart_count;

        SolveOptions local = options_;
        local.interval_exact_cutoff_oracle = "compact-mip";
        local.interval_exact_oracle_mode = "objective-bound";
        local.interval_oracle_objective_cutoff_row = true;
        local.interval_exact_cutoff_gamma_L = request.gamma_L;
        local.interval_exact_cutoff_gamma_U = request.gamma_U;
        local.interval_exact_cutoff_UB = request.verified_cutoff;
        local.interval_exact_cutoff_epsilon = 0.0;
        local.interval_exact_cutoff_time_limit = request.time_limit_seconds;
        local.solve_time_limit = request.time_limit_seconds;
        local.compact_bc_time_limit = request.time_limit_seconds;
        local.interval_exact_cutoff_export_lp =
            request.canonical_model_path.string();
        local.plain_baseline = false;
        local.tailored_bc_enabled = true;
        local.tailored_bc_mode = "static";
        local.tailored_bc_mode_explicit = true;
        local.tailored_bc_gini_branching = "off";
        local.tailored_bc_branching_priority = "off";
        local.compact_bc_threads = 1;
        local.mip_threads = 1;
        local.threads = 1;
        local.cplex_threads = 1;
        local.round24_external_exact_zero_gap = true;
        local.round24_external_reuse_immutable_lp = true;
        local.round24_external_expected_lp_sha256 =
            request.canonical_model_fingerprint;
        local.log_path = request.native_log_path.string();
        out.native_log_path = local.log_path;

        const auto began = Clock::now();
        const SolveResult solved = solveIntervalExactCutoffOracle(instance_, local);
        out.solver_runtime_seconds = solved.interval_exact_cutoff_runtime_seconds;
        if (!(out.solver_runtime_seconds >= 0.0)) {
            out.solver_runtime_seconds =
                std::chrono::duration<double>(Clock::now() - began).count();
        }
        ++stats_.environment_count;
        ++stats_.model_count;
        ++stats_.model_read_count;
        ++stats_.optimize_count;
        ++stats_.model_free_count;
        ++stats_.environment_free_count;
        stats_.cumulative_solver_runtime_seconds += out.solver_runtime_seconds;
        stats_.cumulative_nodes += static_cast<double>(solved.nodes);
        const NativePhaseLogEvidence phase_evidence =
            inspectCplexNativePhaseLog(request.native_log_path);
        out.presolve_time_available = phase_evidence.presolve_time_available;
        out.presolve_time_seconds = phase_evidence.presolve_seconds;
        out.presolve_time_status = out.presolve_time_available
            ? "available_from_cplex_native_log"
            : "unavailable_cplex_native_log_did_not_report_phase_timer";
        out.root_time_available = phase_evidence.root_time_available;
        out.root_time_seconds = phase_evidence.root_seconds;
        out.root_time_status = out.root_time_available
            ? "available_from_cplex_native_log"
            : "unavailable_cplex_native_log_did_not_report_phase_timer";
        out.presolve_rerun_observed = out.presolve_time_available;
        out.root_relaxation_rerun_observed = out.root_time_available;
        if (out.presolve_rerun_observed) ++stats_.presolve_execution_count;
        if (out.root_relaxation_rerun_observed) {
            ++stats_.root_relaxation_execution_count;
        }

        out.solver_finalization_reached =
            solved.interval_exact_cutoff_native_status_available &&
            solved.interval_exact_cutoff_native_lifecycle_valid;
        out.native_status = solved.interval_exact_cutoff_solver_status;
        out.native_status_code =
            solved.interval_exact_cutoff_native_status_code;
        out.optimize_return_code = solved.process_return_code;
        out.exact_zero_gap_roundtrip =
            solved.compact_bc_native_exact_zero_gaps_valid;
        out.model_fingerprint_matches_request =
            fileSha256(request.canonical_model_path) ==
            request.canonical_model_fingerprint;
        bool witness_contradicts_infeasibility = false;
        if (!request.verified_start_routes.empty()) {
            const Verification witness = verifySolution(
                instance_, request.verified_start_routes, options_.lambda);
            witness_contradicts_infeasibility =
                witness.original_solution_feasible &&
                witness.original_objective_recomputed &&
                witness.errors.empty() &&
                witness.G >= request.gamma_L - 1e-9 &&
                witness.G <= request.gamma_U + 1e-9 &&
                witness.objective <= request.verified_cutoff + 1e-9;
        }
        ExternalCplexLeafStatusInput status_input;
        status_input.native_status_code = out.native_status_code;
        status_input.exact_zero_gap_roundtrip =
            out.exact_zero_gap_roundtrip;
        status_input.solver_finalization_reached =
            out.solver_finalization_reached;
        status_input.lifecycle_complete =
            solved.interval_exact_cutoff_native_lifecycle_valid;
        status_input.model_fingerprint_matches =
            out.model_fingerprint_matches_request;
        status_input.verified_witness_contradicts_infeasibility =
            witness_contradicts_infeasibility;
        const ExternalCplexLeafStatusDecision status_decision =
            evaluateExternalCplexLeafStatus(status_input);
        out.native_status_supported = status_decision.native_status_supported;
        out.native_exact_optimal = status_decision.exact_optimal;
        out.native_tolerance_optimal = status_decision.tolerance_optimal;
        out.native_optimal_unscaled_infeasibilities =
            status_decision.optimal_unscaled_infeasibilities;
        out.optimal = status_decision.exact_optimal &&
            status_decision.may_close_leaf;
        out.infeasible = status_decision.infeasible &&
            status_decision.may_close_leaf &&
            solved.interval_exact_cutoff_proven_infeasible &&
            !solved.interval_exact_cutoff_feasible_improving;
        out.interrupted = status_decision.interrupted;
        out.feasibility_consistency_gate =
            status_decision.feasibility_consistency_gate;
        out.native_bound_available = solved.interval_oracle_can_merge_bound &&
            std::isfinite(solved.lower_bound) &&
            out.model_fingerprint_matches_request &&
            solved.interval_exact_cutoff_native_lifecycle_valid;
        out.native_bound = solved.lower_bound;
        out.nodes = static_cast<double>(solved.nodes);
        if (!solved.routes.empty()) {
            const Verification verification =
                verifySolution(instance_, solved.routes, options_.lambda);
            out.incumbent_independently_verified =
                verification.original_solution_feasible &&
                verification.original_objective_recomputed &&
                verification.errors.empty();
            if (out.incumbent_independently_verified) {
                out.incumbent_available = true;
                out.incumbent_objective = verification.objective;
                out.incumbent_routes = solved.routes;
            }
        }
        if (!out.solver_finalization_reached ||
            !out.exact_zero_gap_roundtrip ||
            !out.model_fingerprint_matches_request ||
            !out.feasibility_consistency_gate) {
            std::ostringstream reason;
            reason << "cplex_external_gate:finalized="
                   << out.solver_finalization_reached
                   << ";exact_zero_gaps=" << out.exact_zero_gap_roundtrip
                   << ";model_match=" << out.model_fingerprint_matches_request
                   << ";feasibility_consistency="
                   << out.feasibility_consistency_gate
                   << ";native_status_code=" << out.native_status_code
                   << ";status_class=" << status_decision.status_class
                   << ";status=" << solved.status;
            out.failure_reason = reason.str();
        } else {
            out.failure_reason = "none";
        }
        return out;
    }

    FixedIntervalMipBackendStats stats() const override { return stats_; }

private:
    const Instance& instance_;
    SolveOptions options_;
    FixedIntervalMipBackendStats stats_;
};

void copyBackendStats(SolveResult& result,
                      const FixedIntervalMipBackendStats& stats) {
    result.external_gini_tree_environment_count = stats.environment_count;
    result.external_gini_tree_model_count = stats.model_count;
    result.external_gini_tree_model_read_count = stats.model_read_count;
    result.external_gini_tree_optimize_count = stats.optimize_count;
    result.external_gini_tree_model_free_count = stats.model_free_count;
    result.external_gini_tree_environment_free_count = stats.environment_free_count;
    result.external_gini_tree_same_leaf_resume_count = stats.same_leaf_resume_count;
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
    result.external_gini_tree_model_build_seconds =
        stats.cumulative_model_build_seconds;
    result.external_gini_tree_model_read_seconds =
        stats.cumulative_model_read_seconds;
    result.external_gini_tree_solver_seconds =
        stats.cumulative_solver_runtime_seconds;
    result.external_gini_tree_work = stats.cumulative_work;
    result.external_gini_tree_nodes = stats.cumulative_nodes;
    result.external_gini_tree_simplex_iterations =
        stats.cumulative_simplex_iterations;
    result.external_gini_tree_barrier_iterations =
        stats.cumulative_barrier_iterations;
    result.external_gini_tree_peak_memory_gb = stats.peak_memory_gb;
}

} // namespace

std::unique_ptr<FixedIntervalMipBackend> makeCplexFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options) {
    return std::make_unique<CplexFixedIntervalBackend>(instance, options);
}

ExternalCplexLeafStatusDecision evaluateExternalCplexLeafStatus(
    const ExternalCplexLeafStatusInput& input) {
    ExternalCplexLeafStatusDecision out;
    const bool common_gate = input.solver_finalization_reached &&
        input.lifecycle_complete && input.model_fingerprint_matches;
    switch (input.native_status_code) {
    case kCplexMipOptimal:
        out.native_status_supported = true;
        out.exact_optimal = true;
        out.status_class = "native_exact_optimal";
        out.may_close_leaf = common_gate &&
            input.exact_zero_gap_roundtrip;
        out.rejection_reason = out.may_close_leaf ? "none" :
            "exact_optimal_engineering_gate_failed";
        break;
    case kCplexMipOptimalTolerance:
        out.native_status_supported = true;
        out.tolerance_optimal = true;
        out.status_class = "native_tolerance_optimal";
        out.rejection_reason = "tolerance_optimal_not_exact";
        break;
    case kCplexMipInfeasible:
        out.native_status_supported = true;
        out.infeasible = true;
        out.status_class = "native_fixed_interval_cutoff_infeasible";
        out.feasibility_consistency_gate =
            !input.verified_witness_contradicts_infeasibility;
        out.may_close_leaf = common_gate &&
            out.feasibility_consistency_gate;
        out.rejection_reason = out.may_close_leaf ? "none" :
            (out.feasibility_consistency_gate
                ? "infeasible_engineering_gate_failed"
                : "verified_witness_contradicts_fixed_interval_infeasibility");
        break;
    case kCplexMipTimeLimitFeasible:
        out.native_status_supported = true;
        out.interrupted = true;
        out.status_class = "native_time_limit_with_incumbent";
        out.rejection_reason = "time_limit_not_exact";
        break;
    case kCplexMipTimeLimitNoIncumbent:
        out.native_status_supported = true;
        out.interrupted = true;
        out.status_class = "native_time_limit_without_incumbent";
        out.rejection_reason = "time_limit_not_exact";
        break;
    case kCplexMipOptimalUnscaledInfeasibilities:
        out.native_status_supported = true;
        out.optimal_unscaled_infeasibilities = true;
        out.status_class = "native_optimal_unscaled_infeasibilities";
        out.rejection_reason = "unscaled_infeasibilities_not_exact";
        break;
    default:
        out.status_class = "unsupported_native_status";
        out.rejection_reason = "unsupported_native_status_code:" +
            std::to_string(input.native_status_code);
        break;
    }
    return out;
}

bool immutableLeafArtifactReusable(
    const ImmutableLeafArtifactContract& cached,
    const ImmutableLeafArtifactContract& requested,
    std::string* rejection_reason) {
    auto reject = [&](const std::string& reason) {
        if (rejection_reason) *rejection_reason = reason;
        return false;
    };
    if (cached.leaf_id != requested.leaf_id) return reject("leaf_id_changed");
    if (std::fabs(cached.gamma_L - requested.gamma_L) > 1e-12) {
        return reject("gamma_L_changed");
    }
    if (std::fabs(cached.gamma_U - requested.gamma_U) > 1e-12) {
        return reject("gamma_U_changed");
    }
    if (std::fabs(cached.cutoff - requested.cutoff) > 1e-12) {
        return reject("cutoff_changed");
    }
    if (cached.path != requested.path) return reject("path_changed");
    if (cached.sha256.empty() || cached.sha256 != requested.sha256) {
        return reject("sha256_changed_or_empty");
    }
    if (cached.model_scope.empty() ||
        cached.model_scope != requested.model_scope) {
        return reject("model_scope_changed_or_empty");
    }
    if (cached.row_signature.empty() ||
        cached.row_signature != requested.row_signature) {
        return reject("row_signature_changed_or_empty");
    }
    if (rejection_reason) *rejection_reason = "none";
    return true;
}

ExternalGiniTreeCertificateDecision evaluateExternalGiniTreeCertificate(
    const ExternalGiniTreeCertificateInput& input) {
    ExternalGiniTreeCertificateDecision out;
    auto reject = [&](const std::string& reason) {
        out.rejection_reason = reason;
        return out;
    };
    if (!input.complete_root_coverage) return reject("incomplete_root_coverage");
    if (!input.parent_child_coverage_valid) return reject("invalid_parent_child_coverage");
    if (!input.all_relevant_leaves_closed) return reject("relevant_leaf_open");
    if (!input.all_leaf_bounds_valid) return reject("invalid_or_unavailable_leaf_bound");
    if (!input.global_bound_valid || !std::isfinite(input.global_lb)) {
        return reject("invalid_global_lower_bound");
    }
    if (!input.global_bound_monotone || !input.leaf_bounds_monotone) {
        return reject("nonmonotone_bound_history");
    }
    if (!input.verified_global_ub || !std::isfinite(input.verified_ub)) {
        return reject("unverified_global_upper_bound");
    }
    if (!input.lifecycle_complete) return reject("incomplete_external_lifecycle");
    if (!input.feasibility_consistency_gate) {
        return reject("external_feasibility_consistency_gate_failed");
    }
    if (input.global_lb + std::max(0.0, input.tolerance) < input.verified_ub) {
        return reject("global_bound_gap_not_closed");
    }
    out.certified = true;
    out.certificate_class = "engineering_exact_original_problem_optimal";
    out.rejection_reason = "none";
    return out;
}

bool externalLeafReadyForAdaptiveSplit(
        int completed_attempts,
        int split_after_attempts,
        double gamma_L,
        double gamma_U,
        int split_depth,
        int max_depth,
        double min_width) {
    return split_after_attempts >= 1 &&
        completed_attempts >= split_after_attempts &&
        legacyAdaptiveSplitEligible(
            gamma_L, gamma_U, split_depth, max_depth, min_width);
}

SolveResult solveExternalGiniTree(const Instance& instance,
                                  const SolveOptions& options,
                                  const SolveResult& verified_seed,
                                  double root_gamma_L,
                                  double root_gamma_U) {
    const auto started = Clock::now();
    auto elapsed = [&]() {
        return std::chrono::duration<double>(Clock::now() - started).count();
    };
    SolveResult result = verified_seed;
    result.method = "gcap-frontier";
    result.frontier_execution_mode = "external-gini-tree";
    result.certificate_scope = "original_global_gini_external_tree";
    result.external_gini_tree_attempted = true;
    result.external_gini_tree_backend = options.external_gini_backend;
    result.external_gini_tree_lifecycle = options.external_gini_lifecycle;
    result.external_gini_tree_scheduling = "legacy-quanta";
    result.external_gini_tree_root_gamma_L = root_gamma_L;
    result.external_gini_tree_root_gamma_U = root_gamma_U;
    result.external_gini_tree_verified_upper_bound = verified_seed.objective;
    result.external_gini_tree_split_after_attempts =
        options.external_gini_split_after_attempts;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason = "external_tree_not_finalized";
    result.certificate = "External global-Gini tree not finalized.";
    result.status = "external_gini_tree_running";

    const ConnectivityFlowVariantResolution flow_resolution =
        resolveConnectivityFlowVariant(
            options.global_gini_tree_root_connectivity_flow,
            options.global_gini_tree_root_connectivity_flow_variant);
    result.global_gini_tree_root_connectivity_flow_variant_requested =
        flow_resolution.requested.empty() ? "invalid" : flow_resolution.requested;
    result.global_gini_tree_root_connectivity_flow_variant_resolved =
        flow_resolution.valid ? flow_resolution.resolved : "invalid";
    const ConnectivityFlowCounts flow_counts = flow_resolution.valid
        ? connectivityFlowTheoreticalCounts(
              flow_resolution.variant, instance.V, instance.M)
        : ConnectivityFlowCounts{};
    if (!flow_resolution.valid || !flow_counts.valid) {
        result.status = "external_gini_tree_invalid_connectivity_flow_variant";
        result.external_gini_tree_failure_reason = flow_resolution.valid
            ? flow_counts.failure_reason : flow_resolution.failure_reason;
        result.runtime_seconds = elapsed();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    result.global_gini_tree_connectivity_flow_columns = flow_counts.columns;
    result.global_gini_tree_connectivity_flow_upper_link_rows =
        flow_counts.upper_link_rows;
    result.global_gini_tree_connectivity_flow_lower_link_rows =
        flow_counts.lower_link_rows;
    result.global_gini_tree_connectivity_flow_station_balance_rows =
        flow_counts.station_balance_rows;
    result.global_gini_tree_connectivity_flow_depot_balance_rows =
        flow_counts.depot_balance_rows;
    result.global_gini_tree_connectivity_flow_start_upper_rows =
        flow_counts.start_upper_rows;
    result.global_gini_tree_connectivity_flow_start_lower_rows =
        flow_counts.start_lower_rows;
    result.global_gini_tree_connectivity_flow_total_rows = flow_counts.total_rows;
    result.global_gini_tree_connectivity_flow_total_nonzeros =
        flow_counts.total_nonzeros;

    const bool verified_seed_valid = verified_seed.verification.original_solution_feasible &&
        verified_seed.verification.original_objective_recomputed &&
        verified_seed.verification.errors.empty() &&
        std::isfinite(verified_seed.objective);
    if (!verified_seed_valid || root_gamma_L < -1e-12 ||
        root_gamma_U < root_gamma_L - 1e-12 ||
        !verified_seed.frontier_covers_all_improving_gini_values) {
        result.status = "external_gini_tree_invalid_root";
        result.external_gini_tree_failure_reason = verified_seed_valid
            ? "incomplete_or_invalid_root_range" : "same_run_seed_not_verified";
        result.runtime_seconds = elapsed();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }

    std::unique_ptr<FixedIntervalMipBackend> backend;
    if (options.external_gini_backend == "gurobi") {
        backend = makeGurobiFixedIntervalBackend(instance, options);
    } else if (options.external_gini_backend == "cplex") {
        backend = makeCplexFixedIntervalBackend(instance, options);
    }
    if (!backend) {
        result.status = "external_gini_tree_backend_invalid";
        result.external_gini_tree_failure_reason = "unknown_external_backend";
        result.runtime_seconds = elapsed();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    const FixedIntervalMipCapabilities capabilities = backend->capabilities();
    result.external_gini_tree_available = capabilities.available;
    if (!capabilities.available) {
        result.status = "external_gini_tree_backend_unavailable";
        result.external_gini_tree_failure_reason = capabilities.failure_reason;
        copyBackendStats(result, backend->stats());
        result.runtime_seconds = elapsed();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    if (options.external_gini_lifecycle == "retained-per-leaf" &&
        options.external_gini_backend == "gurobi" &&
        !capabilities.retained_same_leaf_resume) {
        result.status = "external_gini_tree_resume_gate_failed";
        result.external_gini_tree_failure_reason =
            "retained_per_leaf_capability_unavailable";
        result.runtime_seconds = elapsed();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }

    const auto stamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        Clock::now().time_since_epoch()).count();
    const std::filesystem::path artifact_dir =
        options.external_gini_artifact_dir.empty()
            ? std::filesystem::path("results") / "external_gini_work" /
                (std::filesystem::path(instance.name).stem().string() + "_" +
                 options.external_gini_backend + "_" + std::to_string(stamp))
            : std::filesystem::path(options.external_gini_artifact_dir);
    std::filesystem::create_directories(artifact_dir / "models");
    std::filesystem::create_directories(artifact_dir / "native_logs");
    const auto event_path = artifact_dir / "external_tree_events.csv";
    const auto leaf_path = artifact_dir / "external_leaf_ledger.csv";
    const auto lifecycle_path = artifact_dir / "leaf_model_lifecycle.csv";
    const auto optimize_path = artifact_dir / "optimize_call_ledger.csv";
    const auto warm_path = artifact_dir / "gurobi_warm_start_audit.csv";
    const auto enhanced_path = artifact_dir / "enhanced_attempt_trace.csv";
    const auto global_bound_path = artifact_dir / "global_bound_trace.csv";
    result.external_gini_tree_event_trace_path = event_path.string();
    result.external_gini_tree_leaf_ledger_path = leaf_path.string();
    result.external_gini_tree_lifecycle_path = lifecycle_path.string();
    result.external_gini_tree_optimize_ledger_path = optimize_path.string();
    result.external_gini_tree_warm_start_audit_path = warm_path.string();
    result.external_gini_tree_enhanced_attempt_trace_path =
        enhanced_path.string();
    result.external_gini_tree_global_bound_trace_path =
        global_bound_path.string();
    std::ofstream events(event_path), lifecycle(lifecycle_path),
        optimize(optimize_path), warm(warm_path), enhanced(enhanced_path),
        global_trace(global_bound_path);
    events << "elapsed_seconds,event,leaf_id,gamma_L,gamma_U,attempt,native_status,native_bound,native_bound_available,incumbent,incumbent_available,global_lb,verified_ub,open_leaf_count,failure_reason\n";
    lifecycle << "leaf_id,attempt,new_leaf,same_leaf_retained,fresh_restart,child_restart,reset_called,model_modified,retained_state_classification,continuation_claimed,continuation_evidence,presolve_rerun,root_relaxation_rerun,incumbent_state_reused,model_fingerprint_match,native_log_path\n";
    optimize << "leaf_id,attempt,time_limit_seconds,solver_runtime_seconds,work,nodes,simplex_iterations,barrier_iterations,cumulative_runtime,cumulative_work,cumulative_nodes,cumulative_simplex_iterations,cumulative_barrier_iterations,optimize_return_code\n";
    warm << "leaf_id,attempt,candidate_available,mapping_complete,submitted,status,mapping_seconds\n";
    enhanced << "attempt_start_seconds,attempt_end_seconds,leaf_id,parent_id,depth,gamma_L,gamma_U,attempt,new_leaf,selected_while_controlling,controlling_leaves_before,controlling_leaves_after,open_leaves_before,closed_leaves_before,open_leaves_after,closed_leaves_after,allocated_time_seconds,solver_runtime_seconds,native_status,native_status_code,optimize_return_code,leaf_lb_before,native_bound,native_bound_available,leaf_lb_after,global_lb_before,global_lb_after,verified_ub_before,verified_ub_after,incumbent,incumbent_available,first_incumbent_time_seconds,last_incumbent_improvement_time_seconds,last_native_lb_improvement_time_seconds,last_global_lb_improvement_time_seconds,stagnation_seconds,work,nodes,open_nodes,open_nodes_available,simplex_iterations,barrier_iterations,memory_gb,model_rows,model_columns,model_nonzeros,interval_row_count,cutoff_row_count,artifact_generation_seconds,model_read_seconds,presolve_rerun,presolve_time_available,presolve_time_seconds,presolve_time_status,root_rerun,root_time_available,root_time_seconds,root_time_status,fresh_restart,child_restart,same_leaf_retained,retained_state_classification,warm_candidate,warm_mapping_complete,warm_submitted,warm_status,warm_mapping_seconds,split_count,cutoff,canonical_sha256,row_signature,native_cut_count_available,native_cut_count,model_path,native_log_path\n";
    global_trace
        << "process_elapsed_seconds,exact_phase_elapsed_seconds,event_type,"
           "active_leaf,active_leaf_valid_lower_bound,"
           "other_open_leaf_min_valid_lower_bound,"
           "valid_global_lower_bound,verified_global_upper_bound,"
           "open_relevant_leaf_count,closed_relevant_leaf_count,event_source\n";
    global_trace.flush();

    ControllingLeafScheduler scheduler(1e-7);
    const auto initial = makeLegacyFrontierIntervals(
        root_gamma_L, root_gamma_U, options.frontier_intervals);
    result.external_gini_tree_initial_leaf_count =
        static_cast<long long>(initial.size());
    result.external_gini_tree_root_coverage_valid = exactIntervalCoverage(
        {root_gamma_L, root_gamma_U}, initial, 1e-9);
    for (std::size_t i = 0; i < initial.size(); ++i) {
        ControllingLeaf leaf;
        leaf.id = "L" + std::to_string(i);
        leaf.gamma_L = initial[i].lower;
        leaf.gamma_U = initial[i].upper;
        leaf.base_lower_bound = leaf.gamma_L;
        leaf.lower_bound = leaf.gamma_L;
        leaf.lower_bound_sources = {"objective_nonnegative_penalty_G_floor"};
        leaf.cutoff = verified_seed.objective;
        std::string reason;
        if (!scheduler.addLeaf(leaf, &reason)) {
            result.external_gini_tree_failure_reason =
                "initial_leaf_add_failed:" + reason;
            result.status = "external_gini_tree_invalid_schedule";
            break;
        }
    }

    double verified_ub = verified_seed.objective;
    double first_incumbent_time = verified_seed.incumbent_best_runtime > 0.0
        ? verified_seed.incumbent_best_runtime
        : verified_seed.incumbent_generation_time_seconds;
    double last_incumbent_improvement_time = first_incumbent_time;
    double last_native_lb_improvement_time = -1.0;
    double last_global_lb_improvement_time = -1.0;
    double controller_model_build_seconds = 0.0;
    struct CachedLeafArtifact {
        CanonicalCompactModelArtifact model;
        double gamma_L = 0.0;
        double gamma_U = 0.0;
        double cutoff = 0.0;
        std::string model_scope;
        std::string row_signature;
        long long reuse_count = 0;
    };
    std::unordered_map<std::string, CachedLeafArtifact> artifact_cache;
    std::vector<RoutePlan> best_routes = verified_seed.routes;
    std::string best_source = "same_run_verified_hga";
    const double reserve = ControllingLeafScheduler::finalizationReserveSeconds(
        options.solve_time_limit);
    bool hard_failure = !result.external_gini_tree_failure_reason.empty();
    auto joinedLeafIds = [](const std::vector<std::string>& ids) {
        std::ostringstream out;
        for (std::size_t i = 0; i < ids.size(); ++i) {
            if (i) out << ';';
            out << ids[i];
        }
        return out.str();
    };
    auto leafCounts = [&scheduler]() {
        std::pair<long long, long long> counts{0, 0};
        for (const ControllingLeaf& leaf : scheduler.leaves()) {
            if (leaf.status == ControllingLeafStatus::Replaced ||
                leaf.parent_replaced) continue;
            if (leaf.status == ControllingLeafStatus::Open) ++counts.first;
            if (leaf.status == ControllingLeafStatus::Closed ||
                leaf.status == ControllingLeafStatus::Fathomed ||
                leaf.status == ControllingLeafStatus::Empty) ++counts.second;
        }
        return counts;
    };
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
            if (open) ++counts.first;
            else ++counts.second;
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
        const auto counts = relevantCounts();
        global_trace << std::setprecision(17) << process_seconds << ','
                     << exact_seconds << ',' << csvEscape(event_type) << ','
                     << csvEscape(active_leaf) << ',';
        if (std::isfinite(active_bound)) global_trace << active_bound;
        global_trace << ',';
        if (std::isfinite(other_bound)) global_trace << other_bound;
        global_trace << ',' << global_bound << ',' << verified_ub << ','
                     << counts.first << ',' << counts.second << ','
                     << csvEscape(source) << '\n';
        global_trace.flush();
    };
    writeGlobalTrace(
        processElapsedSeconds(options), elapsed(),
        "exact_tree_initialization", "", scheduler.globalLowerBound(),
        std::numeric_limits<double>::infinity(),
        "c0_exact_interval_cover");
    while (!hard_failure && !scheduler.everyRelevantLeafClosed()) {
        const double remaining = options.solve_time_limit > 0.0
            ? options.solve_time_limit - elapsed()
            : std::numeric_limits<double>::max();
        const ControllingLeafSelection selection = scheduler.selectNext();
        if (!selection.available) break;
        const DeadlineLaunchDecision launch = ControllingLeafScheduler::planLaunch(
            selection.requested_quantum_seconds, remaining, reserve);
        if (!launch.launch_allowed) {
            result.external_gini_tree_failure_reason =
                "budget_finalization:" + launch.rejection_reason;
            writeGlobalTrace(
                processElapsedSeconds(options), elapsed(), "interruption",
                selection.selected_leaf_id,
                scheduler.findLeaf(selection.selected_leaf_id)
                    ? scheduler.findLeaf(selection.selected_leaf_id)->lower_bound
                    : std::numeric_limits<double>::infinity(),
                otherRelevantMinimum(selection.selected_leaf_id),
                "unified_process_deadline_launch_guard");
            break;
        }
        const ControllingLeaf* selected = scheduler.findLeaf(selection.selected_leaf_id);
        if (!selected) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = "selected_leaf_missing";
            break;
        }

        // The adaptive rule is deterministic and backend-neutral.  C0 keeps
        // the historical threshold of two attempts; the Round 26 prototype
        // uses one uniformly to avoid a repeated fresh-root solve before the
        // same exact atomic partition.
        if (externalLeafReadyForAdaptiveSplit(
                selected->exact_solver_attempt_count,
                options.external_gini_split_after_attempts,
                selected->gamma_L, selected->gamma_U, selected->split_depth,
                options.frontier_adaptive_max_depth,
                options.frontier_adaptive_min_width)) {
            // splitLeafAtomically may grow the scheduler's leaf vector and
            // invalidate selected.  Preserve every value needed after the
            // mutation before handing the children to the scheduler.
            const std::string selected_id = selected->id;
            const double selected_gamma_L = selected->gamma_L;
            const double selected_gamma_U = selected->gamma_U;
            const auto geometry = splitLegacyFrontierInterval(
                selected_gamma_L, selected_gamma_U,
                options.frontier_adaptive_split_factor);
            std::vector<ControllingLeaf> children;
            children.reserve(geometry.size());
            for (std::size_t index = 0; index < geometry.size(); ++index) {
                ControllingLeaf child;
                child.id = selected->id + "." + std::to_string(index);
                child.parent_id = selected_id;
                child.child_index = static_cast<int>(index);
                child.split_depth = selected->split_depth + 1;
                child.gamma_L = geometry[index].lower;
                child.gamma_U = geometry[index].upper;
                child.base_lower_bound = selected->lower_bound;
                child.lower_bound = selected->lower_bound;
                child.lower_bound_sources = {"inherited_parent_bound"};
                child.cutoff = selected->cutoff;
                children.push_back(child);
            }
            std::string reason;
            if (!scheduler.splitLeafAtomically(selected_id, children, &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "atomic_split_failed:" + reason;
            } else {
                ++result.external_gini_tree_split_count;
                events << std::setprecision(17) << elapsed() << ",split,"
                       << selected_id << ',' << selected_gamma_L << ','
                       << selected_gamma_U
                       << ",-1,not_run,0,false,0,false,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << scheduler.controllingSet().size() << ",none\n";
                writeGlobalTrace(
                    processElapsedSeconds(options), elapsed(), "split",
                    selected_id, std::numeric_limits<double>::infinity(),
                    scheduler.globalLowerBound(),
                    "c0_attempt_triggered_atomic_split_diagnostic_only");
            }
            continue;
        }

        const bool new_leaf = selected->exact_solver_attempt_count == 0;
        const std::filesystem::path model_path = artifact_dir / "models" /
            (selected->id + ".lp");
        CanonicalCompactModelSpec model_spec;
        model_spec.strengthened = true;
        model_spec.interval_restricted = true;
        model_spec.gamma_L = selected->gamma_L;
        model_spec.gamma_U = selected->gamma_U;
        model_spec.add_verified_incumbent_row = true;
        model_spec.verified_incumbent = verified_seed.objective;
        model_spec.incumbent_epsilon = 0.0;
        CanonicalCompactModelArtifact model;
        double build_seconds = 0.0;
        auto cached = artifact_cache.find(selected->id);
        if (cached == artifact_cache.end()) {
            const auto build_started = Clock::now();
            model = writeCanonicalCompactModel(
                instance, options, model_path, model_spec);
            build_seconds = std::chrono::duration<double>(
                Clock::now() - build_started).count();
            controller_model_build_seconds += build_seconds;
            ++result.external_gini_tree_canonical_artifact_generation_count;
            if (!model.written) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "static_leaf_model_build_failed:" + model.failure_reason;
                break;
            }
            CachedLeafArtifact entry;
            entry.model = model;
            entry.gamma_L = selected->gamma_L;
            entry.gamma_U = selected->gamma_U;
            entry.cutoff = verified_seed.objective;
            entry.model_scope = model.model_scope;
            entry.row_signature = model.row_signature;
            cached = artifact_cache.emplace(selected->id, std::move(entry)).first;
        } else {
            ImmutableLeafArtifactContract cached_contract;
            cached_contract.leaf_id = selected->id;
            cached_contract.gamma_L = cached->second.gamma_L;
            cached_contract.gamma_U = cached->second.gamma_U;
            cached_contract.cutoff = cached->second.cutoff;
            cached_contract.path = cached->second.model.path;
            cached_contract.sha256 = cached->second.model.sha256;
            cached_contract.model_scope = cached->second.model_scope;
            cached_contract.row_signature = cached->second.row_signature;
            ImmutableLeafArtifactContract requested_contract;
            requested_contract.leaf_id = selected->id;
            requested_contract.gamma_L = selected->gamma_L;
            requested_contract.gamma_U = selected->gamma_U;
            requested_contract.cutoff = verified_seed.objective;
            requested_contract.path = model_path;
            requested_contract.sha256 = cached->second.model.sha256;
            requested_contract.model_scope =
                "complete_original_compact_milp_intersected_with_static_gini_interval";
            requested_contract.row_signature = cached->second.model.row_signature;
            std::string immutable_reason;
            const bool immutable_contract = immutableLeafArtifactReusable(
                cached_contract, requested_contract, &immutable_reason) &&
                std::filesystem::exists(cached->second.model.path) &&
                fileSha256(cached->second.model.path) ==
                    cached->second.model.sha256;
            if (!immutable_contract) {
                ++result.external_gini_tree_canonical_artifact_invalidation_count;
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "immutable_leaf_artifact_contract_changed:" + selected->id +
                    ":" + immutable_reason;
                break;
            }
            ++cached->second.reuse_count;
            ++result.external_gini_tree_canonical_artifact_cache_hit_count;
            model = cached->second.model;
        }
        FixedIntervalMipRequest request;
        request.leaf_id = selected->id;
        request.attempt_number = selected->exact_solver_attempt_count;
        request.gamma_L = selected->gamma_L;
        request.gamma_U = selected->gamma_U;
        request.verified_cutoff = verified_seed.objective;
        request.time_limit_seconds = launch.effective_native_time_limit_seconds;
        request.new_leaf = new_leaf;
        request.warm_start_enabled = options.external_gini_warm_start;
        request.canonical_model_path = model.path;
        request.canonical_model_fingerprint = model.sha256;
        request.canonical_model_scope = model.model_scope;
        request.canonical_row_signature = model.row_signature;
        request.native_log_path = artifact_dir / "native_logs" /
            (selected->id + "_attempt_" +
             std::to_string(request.attempt_number) + "." +
             options.external_gini_backend + ".log");
        request.verified_start_routes = best_routes;
        request.verified_start_source = best_source;
        request.capture_native_bound_events =
            options.external_gini_backend == "gurobi";
        const double attempt_start = elapsed();
        const double attempt_process_start =
            processElapsedSeconds(options);
        const double leaf_lb_before = selected->lower_bound;
        const double other_bound_before =
            otherRelevantMinimum(selected->id);
        const double global_lb_before = scheduler.globalLowerBound();
        const double verified_ub_before = verified_ub;
        const auto counts_before = leafCounts();
        const std::string parent_id = selected->parent_id;
        const int split_depth = selected->split_depth;
        const std::string controlling_before =
            joinedLeafIds(selection.controlling_leaf_ids);
        FixedIntervalMipOutcome outcome = backend->solve(request);
        const double attempt_end = elapsed();
        for (const FixedIntervalNativeBoundEvent& native_event :
                outcome.native_bound_events) {
            if (!native_event.native_bound_available ||
                !native_event.bound_improved) {
                continue;
            }
            writeGlobalTrace(
                attempt_process_start +
                    native_event.solver_runtime_seconds,
                attempt_start + native_event.solver_runtime_seconds,
                native_event.processed_nodes <= 0.0
                    ? "native_root_processing_bound"
                    : "partial_native_mip_bound_improvement",
                selected->id,
                std::max(leaf_lb_before, native_event.native_bound),
                other_bound_before,
                "gurobi_cb_mip_objbnd_valid_native_bound");
        }
        outcome.model_build_seconds += build_seconds;
        ++result.external_gini_tree_attempt_count;
        const bool selected_while_controlling =
            std::find(selection.controlling_leaf_ids.begin(),
                      selection.controlling_leaf_ids.end(), selected->id) !=
            selection.controlling_leaf_ids.end();
        ControllingLeafAttempt attempt;
        attempt.attempt_number = selected->exact_solver_attempt_count;
        attempt.requested_quantum_seconds = selection.requested_quantum_seconds;
        attempt.effective_native_time_limit_seconds =
            launch.effective_native_time_limit_seconds;
        attempt.actual_solver_time_seconds =
            std::max(0.0, outcome.solver_runtime_seconds);
        attempt.selected_while_controlling = selected_while_controlling;
        attempt.solver_status = outcome.native_status;
        attempt.solver_final_best_bound = outcome.native_bound;
        attempt.solver_final_best_bound_valid =
            outcome.native_bound_available && std::isfinite(outcome.native_bound);
        attempt.finalization_source = "backend_native_finalization";
        std::string accounting_reason;
        if (!scheduler.recordAttempt(selected->id, attempt, attempt_start,
                                     elapsed(), &accounting_reason)) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "attempt_accounting_failed:" + accounting_reason;
            break;
        }
        if (attempt.solver_final_best_bound_valid) {
            std::string reason;
            if (!scheduler.mergeValidLowerBound(
                    selected->id, outcome.native_bound,
                    options.external_gini_backend + "_native_exact_leaf_bound",
                    &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "native_bound_merge_failed:" + reason;
            }
            if (outcome.native_bound > leaf_lb_before + 1e-12) {
                last_native_lb_improvement_time = attempt_end;
            }
        }
        if (outcome.incumbent_available &&
            outcome.incumbent_independently_verified &&
            outcome.incumbent_objective < verified_ub - 1e-9) {
            verified_ub = outcome.incumbent_objective;
            best_routes = outcome.incumbent_routes;
            best_source = options.external_gini_backend + "_verified_leaf";
            if (first_incumbent_time < 0.0) first_incumbent_time = attempt_end;
            last_incumbent_improvement_time = attempt_end;
            writeGlobalTrace(
                processElapsedSeconds(options), attempt_end,
                "incumbent_improvement", selected->id,
                outcome.native_bound_available
                    ? std::max(leaf_lb_before, outcome.native_bound)
                    : leaf_lb_before,
                other_bound_before,
                options.external_gini_backend +
                    "_independently_verified_native_incumbent");
        }
        if (outcome.optimal || outcome.infeasible) {
            std::string reason;
            if (!scheduler.setStatus(selected->id, ControllingLeafStatus::Closed,
                    outcome.infeasible ? "native_static_leaf_infeasible" :
                                         "native_static_leaf_optimal",
                    &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "leaf_closure_failed:" + reason;
            }
        }
        if (!outcome.available || !outcome.solver_finalization_reached ||
            !outcome.exact_zero_gap_roundtrip ||
            !outcome.model_fingerprint_matches_request ||
            !outcome.feasibility_consistency_gate) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = outcome.failure_reason.empty()
                ? "backend_evidence_gate_failed" : outcome.failure_reason;
        }
        const ControllingLeaf* recorded = scheduler.findLeaf(selected->id);
        const double global_lb_after = scheduler.globalLowerBound();
        if (global_lb_after > global_lb_before + 1e-12) {
            last_global_lb_improvement_time = attempt_end;
        }
        const auto counts_after = leafCounts();
        const std::string controlling_after =
            joinedLeafIds(scheduler.controllingSet());
        const double leaf_lb_after = recorded ? recorded->lower_bound
                                              : leaf_lb_before;
        if (outcome.optimal || outcome.infeasible) {
            writeGlobalTrace(
                processElapsedSeconds(options), attempt_end,
                outcome.infeasible ? "infeasible_closure"
                                   : "terminal_mip_closure",
                selected->id, std::numeric_limits<double>::infinity(),
                otherRelevantMinimum(selected->id),
                options.external_gini_backend +
                    "_native_exact_leaf_finalization");
        } else if (outcome.native_bound_available) {
            writeGlobalTrace(
                processElapsedSeconds(options), attempt_end,
                "partial_native_mip_bound_improvement", selected->id,
                leaf_lb_after, otherRelevantMinimum(selected->id),
                options.external_gini_backend +
                    "_native_final_valid_dual_bound");
        }
        const double stagnation = last_global_lb_improvement_time >= 0.0
            ? std::max(0.0, attempt_end - last_global_lb_improvement_time)
            : attempt_end;
        events << std::setprecision(17) << elapsed() << ",attempt,"
               << selected->id << ',' << selected->gamma_L << ','
               << selected->gamma_U << ',' << request.attempt_number << ','
               << csvEscape(outcome.native_status) << ',' << outcome.native_bound
               << ',' << outcome.native_bound_available << ','
               << outcome.incumbent_objective << ',' << outcome.incumbent_available
               << ',' << scheduler.globalLowerBound() << ',' << verified_ub
               << ',' << scheduler.controllingSet().size() << ','
               << csvEscape(outcome.failure_reason) << '\n';
        lifecycle << selected->id << ',' << request.attempt_number << ','
                  << new_leaf << ',' << outcome.same_leaf_model_retained << ','
                  << outcome.fresh_restart << ',' << outcome.child_restart << ','
                  << outcome.reset_called << ','
                  << outcome.native_model_modified << ','
                  << csvEscape(outcome.retained_state_classification) << ','
                  << outcome.native_continuation_claimed << ','
                  << outcome.native_continuation_evidence << ','
                  << outcome.presolve_rerun_observed << ','
                  << outcome.root_relaxation_rerun_observed << ','
                  << outcome.incumbent_state_reused << ','
                  << outcome.model_fingerprint_matches_request << ','
                  << csvEscape(outcome.native_log_path) << '\n';
        optimize << selected->id << ',' << request.attempt_number << ','
                 << request.time_limit_seconds << ','
                 << outcome.solver_runtime_seconds << ',' << outcome.work << ','
                 << outcome.nodes << ',' << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ',' << outcome.cumulative_runtime
                 << ',' << outcome.cumulative_work << ','
                 << outcome.cumulative_nodes << ','
                 << outcome.cumulative_simplex_iterations << ','
                 << outcome.cumulative_barrier_iterations << ','
                 << outcome.optimize_return_code << '\n';
        warm << selected->id << ',' << request.attempt_number << ','
             << outcome.warm_start_candidate_available << ','
             << outcome.warm_start_mapping_complete << ','
             << outcome.warm_start_submitted << ','
             << csvEscape(outcome.warm_start_status) << ','
             << outcome.warm_start_mapping_seconds << '\n';
        enhanced << std::setprecision(17)
                 << attempt_start << ',' << attempt_end << ','
                 << selected->id << ',' << parent_id << ',' << split_depth << ','
                 << request.gamma_L << ',' << request.gamma_U << ','
                 << request.attempt_number << ',' << new_leaf << ','
                 << selected_while_controlling << ','
                 << csvEscape(controlling_before) << ','
                 << csvEscape(controlling_after) << ','
                 << counts_before.first << ',' << counts_before.second << ','
                 << counts_after.first << ',' << counts_after.second << ','
                 << request.time_limit_seconds << ','
                 << outcome.solver_runtime_seconds << ','
                 << csvEscape(outcome.native_status) << ','
                 << outcome.native_status_code << ','
                 << outcome.optimize_return_code << ','
                 << leaf_lb_before << ',' << outcome.native_bound << ','
                 << outcome.native_bound_available << ',' << leaf_lb_after << ','
                 << global_lb_before << ',' << global_lb_after << ','
                 << verified_ub_before << ',' << verified_ub << ','
                 << outcome.incumbent_objective << ','
                 << outcome.incumbent_available << ',' << first_incumbent_time
                 << ',' << last_incumbent_improvement_time << ','
                 << last_native_lb_improvement_time << ','
                 << last_global_lb_improvement_time << ',' << stagnation << ','
                 << outcome.work << ',' << outcome.nodes << ','
                 << outcome.open_nodes << ',' << outcome.open_nodes_available
                 << ',' << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ',' << outcome.memory_gb << ','
                 << model.rows << ',' << model.columns << ',' << model.nonzeros
                 << ',' << (model.interval_restricted ? 2 : 0) << ','
                 << (model.verified_incumbent_row ? 1 : 0) << ','
                 << build_seconds << ',' << outcome.model_read_seconds
                 << ',' << outcome.presolve_rerun_observed << ','
                 << outcome.presolve_time_available << ','
                 << outcome.presolve_time_seconds << ','
                 << csvEscape(outcome.presolve_time_status) << ','
                 << outcome.root_relaxation_rerun_observed << ','
                 << outcome.root_time_available << ',' << outcome.root_time_seconds
                 << ',' << csvEscape(outcome.root_time_status) << ','
                 << outcome.fresh_restart << ',' << outcome.child_restart << ','
                 << outcome.same_leaf_model_retained << ','
                 << csvEscape(outcome.retained_state_classification) << ','
                 << outcome.warm_start_candidate_available << ','
                 << outcome.warm_start_mapping_complete << ','
                 << outcome.warm_start_submitted << ','
                 << csvEscape(outcome.warm_start_status) << ','
                 << outcome.warm_start_mapping_seconds << ','
                 << result.external_gini_tree_split_count << ','
                 << request.verified_cutoff << ',' << model.sha256 << ','
                 << model.row_signature << ','
                 << outcome.native_cut_count_available << ','
                 << outcome.native_cut_count << ','
                 << csvEscape(model.path.string()) << ','
                 << csvEscape(outcome.native_log_path) << '\n';
        (void)recorded;
    }

    events.flush(); lifecycle.flush(); optimize.flush(); warm.flush();
    enhanced.flush();
    std::ofstream leaves(leaf_path);
    leaves << "leaf_id,parent_id,depth,child_index,gamma_L,gamma_U,status,base_lb,final_lb,cutoff,attempts,parent_replaced,closure_source,cumulative_allocated_time_seconds,cumulative_solver_time_seconds,time_while_controlling_seconds,time_while_noncontrolling_seconds,first_attempt_elapsed_seconds,last_attempt_elapsed_seconds,latest_solver_status,canonical_model_path,canonical_sha256,model_scope,row_signature,model_rows,model_columns,model_nonzeros,artifact_generations,artifact_reuses\n";
    long long final_count = 0, open_count = 0, closed_count = 0;
    bool all_bounds_valid = true;
    for (const ControllingLeaf& leaf : scheduler.leaves()) {
        leaves << std::setprecision(17) << leaf.id << ',' << leaf.parent_id << ','
               << leaf.split_depth << ',' << leaf.child_index << ','
               << leaf.gamma_L << ',' << leaf.gamma_U << ','
               << controllingLeafStatusName(leaf.status) << ','
               << leaf.base_lower_bound << ',' << leaf.lower_bound << ','
               << leaf.cutoff << ',' << leaf.exact_solver_attempt_count << ','
               << leaf.parent_replaced << ',' << csvEscape(leaf.closure_source)
               << ',' << leaf.cumulative_allocated_time_seconds
               << ',' << leaf.cumulative_solver_time_seconds
               << ',' << leaf.time_while_controlling_seconds
               << ',' << leaf.time_while_noncontrolling_seconds
               << ',' << leaf.first_attempt_elapsed_seconds
               << ',' << leaf.last_attempt_elapsed_seconds
               << ',' << csvEscape(leaf.latest_solver_final_status);
        const auto cached = artifact_cache.find(leaf.id);
        if (cached == artifact_cache.end()) {
            leaves << ",,,,,,,0,0\n";
        } else {
            leaves << ',' << csvEscape(cached->second.model.path.string())
                   << ',' << cached->second.model.sha256
                   << ',' << csvEscape(cached->second.model_scope)
                   << ',' << cached->second.row_signature
                   << ',' << cached->second.model.rows
                   << ',' << cached->second.model.columns
                   << ',' << cached->second.model.nonzeros
                   << ",1," << cached->second.reuse_count << '\n';
        }
        if (leaf.status == ControllingLeafStatus::Replaced ||
            leaf.parent_replaced) continue;
        ++final_count;
        all_bounds_valid = all_bounds_valid && std::isfinite(leaf.lower_bound);
        if (leaf.status == ControllingLeafStatus::Closed ||
            leaf.status == ControllingLeafStatus::Fathomed ||
            leaf.status == ControllingLeafStatus::Empty) ++closed_count;
        else ++open_count;
    }
    leaves.flush();

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
                         std::fabs(verified_ub)) : 0.0;
    writeGlobalTrace(
        processElapsedSeconds(options), elapsed(), "finalization", "",
        result.lower_bound, std::numeric_limits<double>::infinity(),
        hard_failure ? "c0_failed_finalization"
                     : (result.external_gini_tree_all_relevant_leaves_closed
                            ? "c0_exact_tree_complete"
                            : "c0_deadline_finalization_open_coverage"));
    global_trace.flush();
    result.external_gini_tree_feasibility_consistency_gate =
        result.verification.original_solution_feasible &&
        result.verification.original_objective_recomputed &&
        result.verification.errors.empty();
    copyBackendStats(result, backend->stats());
    result.external_gini_tree_model_build_seconds +=
        controller_model_build_seconds;
    result.external_gini_tree_canonical_artifact_generation_seconds =
        controller_model_build_seconds;
    result.external_gini_tree_first_incumbent_time_seconds =
        first_incumbent_time;
    result.external_gini_tree_last_incumbent_improvement_time_seconds =
        last_incumbent_improvement_time;
    result.external_gini_tree_last_native_lb_improvement_time_seconds =
        last_native_lb_improvement_time;
    result.external_gini_tree_last_global_lb_improvement_time_seconds =
        last_global_lb_improvement_time;
    result.external_gini_tree_final_stagnation_seconds =
        last_global_lb_improvement_time >= 0.0
            ? std::max(0.0, elapsed() - last_global_lb_improvement_time)
            : elapsed();
    // Model objects must be destroyed when the backend leaves scope.  The
    // stats visible here intentionally describe the active lifecycle; final
    // free counters are audited by the backend-specific destructor logs and
    // are not prerequisites while retained models remain live.
    result.external_gini_tree_lifecycle_complete =
        result.external_gini_tree_optimize_count ==
            result.external_gini_tree_attempt_count &&
        result.external_gini_tree_reset_call_count == 0 && !hard_failure;

    ExternalGiniTreeCertificateInput certificate_input;
    certificate_input.complete_root_coverage =
        result.external_gini_tree_root_coverage_valid;
    certificate_input.parent_child_coverage_valid =
        result.external_gini_tree_parent_child_coverage_valid;
    certificate_input.all_relevant_leaves_closed =
        result.external_gini_tree_all_relevant_leaves_closed;
    certificate_input.all_leaf_bounds_valid = all_bounds_valid;
    certificate_input.global_bound_valid =
        std::isfinite(result.external_gini_tree_global_lower_bound);
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
    certificate_input.global_lb = result.external_gini_tree_global_lower_bound;
    certificate_input.verified_ub = verified_ub;
    const ExternalGiniTreeCertificateDecision decision =
        evaluateExternalGiniTreeCertificate(certificate_input);
    result.external_gini_tree_strict_certified = decision.certified;
    result.external_gini_tree_certificate_class = decision.certificate_class;
    result.external_gini_tree_certificate_rejection_reason =
        decision.rejection_reason;
    result.strict_certified_original_problem = decision.certified;
    result.strict_certificate_class = decision.certificate_class;
    result.strict_certificate_rejection_reason = decision.rejection_reason;
    result.strict_lower_bound_source =
        "minimum_valid_native_or_inherited_bound_over_external_final_leaves";
    result.status = decision.certified ? "optimal" :
        (hard_failure ? "external_gini_tree_failed" :
                        "external_gini_tree_time_limit");
    result.certificate = decision.certified
        ? "Round 24 engineering-exact external-tree certificate: complete Gini coverage, every relevant static leaf closed, monotone native/inherited lower bounds, completed lifecycle, and an independently verified global incumbent."
        : "External-tree strict certificate rejected: " + decision.rejection_reason;
    if (result.external_gini_tree_failure_reason.empty()) {
        result.external_gini_tree_failure_reason = hard_failure
            ? "unspecified_backend_failure" : "none";
    }
    result.runtime_seconds = elapsed();
    result.wall_time_seconds = result.runtime_seconds;
    result.actual_runtime_seconds = result.runtime_seconds;
    return result;
}

} // namespace ebrp
