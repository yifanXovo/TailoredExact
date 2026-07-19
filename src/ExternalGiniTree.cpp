#include "ExternalGiniTree.hpp"

#include "CanonicalCompactModel.hpp"
#include "ControllingLeafScheduler.hpp"
#include "CplexBaseline.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <memory>
#include <sstream>

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
        out.available = true;
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
        if (request.canonical_model_path.has_parent_path()) {
            const auto dir = request.canonical_model_path.parent_path();
            local.log_path = (dir / (request.leaf_id + "_attempt_" +
                std::to_string(request.attempt_number) + ".cplex.log")).string();
        }

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

        out.solver_finalization_reached =
            !solved.interval_exact_cutoff_solver_status.empty();
        out.native_status = solved.interval_exact_cutoff_solver_status;
        out.optimize_return_code = solved.process_return_code;
        out.optimal = out.native_status.find("optimal") != std::string::npos;
        out.infeasible = solved.interval_exact_cutoff_proven_infeasible &&
            !solved.interval_exact_cutoff_feasible_improving;
        out.interrupted = solved.interval_exact_cutoff_timeout ||
            solved.status == "interval_unresolved_timeout";
        out.native_bound_available = solved.interval_oracle_can_merge_bound &&
            std::isfinite(solved.lower_bound);
        out.native_bound = solved.lower_bound;
        out.nodes = static_cast<double>(solved.nodes);
        out.exact_zero_gap_roundtrip =
            solved.compact_bc_native_exact_zero_gaps_valid;
        out.model_fingerprint_matches_request =
            fileSha256(request.canonical_model_path) ==
            request.canonical_model_fingerprint;
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
            !out.model_fingerprint_matches_request) {
            std::ostringstream reason;
            reason << "cplex_external_gate:finalized="
                   << out.solver_finalization_reached
                   << ";exact_zero_gaps=" << out.exact_zero_gap_roundtrip
                   << ";model_match=" << out.model_fingerprint_matches_request
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
    result.external_gini_tree_root_gamma_L = root_gamma_L;
    result.external_gini_tree_root_gamma_U = root_gamma_U;
    result.external_gini_tree_verified_upper_bound = verified_seed.objective;
    result.strict_certified_original_problem = false;
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason = "external_tree_not_finalized";
    result.certificate = "External global-Gini tree not finalized.";
    result.status = "external_gini_tree_running";

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
    const auto event_path = artifact_dir / "external_tree_events.csv";
    const auto leaf_path = artifact_dir / "external_leaf_ledger.csv";
    const auto lifecycle_path = artifact_dir / "leaf_model_lifecycle.csv";
    const auto optimize_path = artifact_dir / "optimize_call_ledger.csv";
    const auto warm_path = artifact_dir / "gurobi_warm_start_audit.csv";
    result.external_gini_tree_event_trace_path = event_path.string();
    result.external_gini_tree_leaf_ledger_path = leaf_path.string();
    result.external_gini_tree_lifecycle_path = lifecycle_path.string();
    result.external_gini_tree_optimize_ledger_path = optimize_path.string();
    result.external_gini_tree_warm_start_audit_path = warm_path.string();
    std::ofstream events(event_path), lifecycle(lifecycle_path), optimize(optimize_path), warm(warm_path);
    events << "elapsed_seconds,event,leaf_id,gamma_L,gamma_U,attempt,native_status,native_bound,native_bound_available,incumbent,incumbent_available,global_lb,verified_ub,open_leaf_count,failure_reason\n";
    lifecycle << "leaf_id,attempt,new_leaf,same_leaf_retained,fresh_restart,child_restart,reset_called,continuation_claimed,continuation_evidence,model_fingerprint_match\n";
    optimize << "leaf_id,attempt,time_limit_seconds,solver_runtime_seconds,work,nodes,simplex_iterations,barrier_iterations,optimize_return_code\n";
    warm << "leaf_id,attempt,candidate_available,mapping_complete,submitted,status,mapping_seconds\n";

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
    double controller_model_build_seconds = 0.0;
    std::vector<RoutePlan> best_routes = verified_seed.routes;
    std::string best_source = "same_run_verified_hga";
    const double reserve = ControllingLeafScheduler::finalizationReserveSeconds(
        options.solve_time_limit);
    bool hard_failure = !result.external_gini_tree_failure_reason.empty();
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
            break;
        }
        const ControllingLeaf* selected = scheduler.findLeaf(selection.selected_leaf_id);
        if (!selected) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = "selected_leaf_missing";
            break;
        }

        // The adaptive rule is deterministic and backend-neutral: after two
        // unresolved attempts, split at the shared uniform geometry points.
        if (selected->exact_solver_attempt_count >= 2 &&
            legacyAdaptiveSplitEligible(
                selected->gamma_L, selected->gamma_U, selected->split_depth,
                options.frontier_adaptive_max_depth,
                options.frontier_adaptive_min_width)) {
            const auto geometry = splitLegacyFrontierInterval(
                selected->gamma_L, selected->gamma_U,
                options.frontier_adaptive_split_factor);
            std::vector<ControllingLeaf> children;
            children.reserve(geometry.size());
            for (std::size_t index = 0; index < geometry.size(); ++index) {
                ControllingLeaf child;
                child.id = selected->id + "." + std::to_string(index);
                child.parent_id = selected->id;
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
            if (!scheduler.splitLeafAtomically(selected->id, children, &reason)) {
                hard_failure = true;
                result.external_gini_tree_failure_reason =
                    "atomic_split_failed:" + reason;
            } else {
                ++result.external_gini_tree_split_count;
                events << std::setprecision(17) << elapsed() << ",split,"
                       << selected->id << ',' << selected->gamma_L << ','
                       << selected->gamma_U
                       << ",-1,not_run,0,false,0,false,"
                       << scheduler.globalLowerBound() << ',' << verified_ub
                       << ',' << scheduler.controllingSet().size() << ",none\n";
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
        const auto build_started = Clock::now();
        const CanonicalCompactModelArtifact model = writeCanonicalCompactModel(
            instance, options, model_path, model_spec);
        const double build_seconds = std::chrono::duration<double>(
            Clock::now() - build_started).count();
        controller_model_build_seconds += build_seconds;
        if (!model.written) {
            hard_failure = true;
            result.external_gini_tree_failure_reason =
                "static_leaf_model_build_failed:" + model.failure_reason;
            break;
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
        request.verified_start_routes = best_routes;
        request.verified_start_source = best_source;
        const double attempt_start = elapsed();
        FixedIntervalMipOutcome outcome = backend->solve(request);
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
        }
        if (outcome.incumbent_available &&
            outcome.incumbent_independently_verified &&
            outcome.incumbent_objective < verified_ub - 1e-9) {
            verified_ub = outcome.incumbent_objective;
            best_routes = outcome.incumbent_routes;
            best_source = options.external_gini_backend + "_verified_leaf";
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
            !outcome.model_fingerprint_matches_request) {
            hard_failure = true;
            result.external_gini_tree_failure_reason = outcome.failure_reason.empty()
                ? "backend_evidence_gate_failed" : outcome.failure_reason;
        }
        const ControllingLeaf* recorded = scheduler.findLeaf(selected->id);
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
                  << outcome.native_continuation_claimed << ','
                  << outcome.native_continuation_evidence << ','
                  << outcome.model_fingerprint_matches_request << '\n';
        optimize << selected->id << ',' << request.attempt_number << ','
                 << request.time_limit_seconds << ','
                 << outcome.solver_runtime_seconds << ',' << outcome.work << ','
                 << outcome.nodes << ',' << outcome.simplex_iterations << ','
                 << outcome.barrier_iterations << ','
                 << outcome.optimize_return_code << '\n';
        warm << selected->id << ',' << request.attempt_number << ','
             << outcome.warm_start_candidate_available << ','
             << outcome.warm_start_mapping_complete << ','
             << outcome.warm_start_submitted << ','
             << csvEscape(outcome.warm_start_status) << ','
             << outcome.warm_start_mapping_seconds << '\n';
        (void)recorded;
    }

    events.flush(); lifecycle.flush(); optimize.flush(); warm.flush();
    std::ofstream leaves(leaf_path);
    leaves << "leaf_id,parent_id,depth,child_index,gamma_L,gamma_U,status,base_lb,final_lb,cutoff,attempts,parent_replaced,closure_source\n";
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
               << '\n';
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
    result.external_gini_tree_feasibility_consistency_gate =
        result.verification.original_solution_feasible &&
        result.verification.original_objective_recomputed &&
        result.verification.errors.empty();
    copyBackendStats(result, backend->stats());
    result.external_gini_tree_model_build_seconds +=
        controller_model_build_seconds;
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
