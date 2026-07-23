#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace ebrp {

enum class FixedIntervalSolveKind {
    LegacyMipQuantum,
    PaperLpRelaxation,
    PaperTerminalMip
};

struct FixedIntervalMipCapabilities {
    std::string backend;
    bool available = false;
    bool retained_same_leaf_resume = false;
    bool fresh_per_attempt = true;
    bool verified_complete_mip_start = false;
    bool native_continuation_evidence = false;
    bool exact_zero_gap_roundtrip = false;
    std::string failure_reason;
};

struct FixedIntervalMipRequest {
    FixedIntervalSolveKind solve_kind =
        FixedIntervalSolveKind::LegacyMipQuantum;
    std::string leaf_id;
    int attempt_number = 0;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double verified_cutoff = 0.0;
    double time_limit_seconds = 0.0;
    // For paper solves this is the remaining global experiment deadline. It
    // may only interrupt the complete external algorithm, never schedule a
    // different leaf or cause a retry.
    double global_deadline_remaining_seconds = 0.0;
    bool new_leaf = true;
    bool warm_start_enabled = false;
    std::filesystem::path canonical_model_path;
    std::string canonical_model_fingerprint;
    std::string canonical_model_scope;
    std::string canonical_row_signature;
    std::filesystem::path native_log_path;
    std::vector<RoutePlan> verified_start_routes;
    std::string verified_start_source;
    // Round 29 C4 keeps a leaf model only within that leaf's exact lifecycle.
    // This is model-object reuse, not native-tree or LP-basis reuse.
    bool incremental_model_reuse_enabled = false;
    bool retain_model_after_solve = false;
};

struct FixedIntervalMipOutcome {
    bool attempted = false;
    bool available = false;
    bool solver_finalization_reached = false;
    bool optimal = false;
    bool native_exact_optimal = false;
    bool native_tolerance_optimal = false;
    bool native_optimal_unscaled_infeasibilities = false;
    bool native_status_supported = false;
    bool lp_relaxation = false;
    bool lp_terminal_valid = false;
    bool terminal_mip = false;
    bool infeasible = false;
    bool interrupted = false;
    bool native_bound_available = false;
    double native_bound = 0.0;
    bool incumbent_available = false;
    bool incumbent_independently_verified = false;
    double incumbent_objective = 0.0;
    std::vector<RoutePlan> incumbent_routes;
    std::string native_status;
    int native_status_code = 0;
    int optimize_return_code = -1;
    double solver_runtime_seconds = 0.0;
    double work = 0.0;
    double nodes = 0.0;
    double simplex_iterations = 0.0;
    double barrier_iterations = 0.0;
    double memory_gb = 0.0;
    double model_build_seconds = 0.0;
    double model_read_seconds = 0.0;
    bool presolve_time_available = false;
    double presolve_time_seconds = 0.0;
    std::string presolve_time_status = "unavailable";
    bool root_time_available = false;
    double root_time_seconds = 0.0;
    std::string root_time_status = "unavailable";
    bool open_nodes_available = false;
    double open_nodes = 0.0;
    bool native_cut_count_available = false;
    long long native_cut_count = 0;
    bool exact_zero_gap_roundtrip = false;
    bool model_fingerprint_matches_request = false;
    bool feasibility_consistency_gate = true;
    bool same_leaf_model_retained = false;
    bool fresh_restart = false;
    bool child_restart = false;
    bool reset_called = false;
    bool native_continuation_claimed = false;
    bool native_continuation_evidence = false;
    bool native_model_modified = false;
    bool presolve_rerun_observed = false;
    bool root_relaxation_rerun_observed = false;
    bool incumbent_state_reused = false;
    bool in_memory_model_reused = false;
    bool integer_domain_restored = false;
    std::string basis_reuse_status = "not_requested";
    std::string retained_state_classification = "not_applicable";
    std::string native_log_path;
    double cumulative_runtime = 0.0;
    double cumulative_work = 0.0;
    double cumulative_nodes = 0.0;
    double cumulative_simplex_iterations = 0.0;
    double cumulative_barrier_iterations = 0.0;
    bool warm_start_candidate_available = false;
    bool warm_start_mapping_complete = false;
    bool warm_start_submitted = false;
    std::string warm_start_status = "not_requested";
    double warm_start_mapping_seconds = 0.0;
    std::string failure_reason;
};

struct FixedIntervalMipBackendStats {
    long long environment_count = 0;
    long long model_count = 0;
    long long model_read_count = 0;
    long long optimize_count = 0;
    long long lp_relaxation_optimize_count = 0;
    long long terminal_mip_optimize_count = 0;
    long long model_free_count = 0;
    long long environment_free_count = 0;
    long long same_leaf_resume_count = 0;
    long long fresh_restart_count = 0;
    long long child_restart_count = 0;
    long long reset_call_count = 0;
    long long confirmed_continuation_count = 0;
    long long partial_state_reuse_count = 0;
    long long observed_fresh_restart_count = 0;
    long long ambiguous_retained_state_count = 0;
    long long presolve_execution_count = 0;
    long long root_relaxation_execution_count = 0;
    long long warm_start_candidate_count = 0;
    long long warm_start_complete_count = 0;
    long long warm_start_submitted_count = 0;
    long long warm_start_accepted_count = 0;
    long long warm_start_rejected_count = 0;
    long long warm_start_unknown_count = 0;
    long long in_memory_model_reuse_count = 0;
    long long explicit_leaf_model_discard_count = 0;
    long long integer_domain_restore_count = 0;
    long long basis_available_count = 0;
    long long basis_mapped_count = 0;
    long long basis_submitted_count = 0;
    long long basis_accepted_count = 0;
    long long basis_rejected_count = 0;
    double cumulative_model_build_seconds = 0.0;
    double cumulative_model_read_seconds = 0.0;
    double cumulative_solver_runtime_seconds = 0.0;
    double cumulative_work = 0.0;
    double cumulative_lp_work = 0.0;
    double cumulative_terminal_mip_work = 0.0;
    double cumulative_nodes = 0.0;
    double cumulative_simplex_iterations = 0.0;
    double cumulative_barrier_iterations = 0.0;
    double peak_memory_gb = 0.0;
};

class FixedIntervalMipBackend {
public:
    virtual ~FixedIntervalMipBackend() = default;
    virtual FixedIntervalMipCapabilities capabilities() const = 0;
    virtual FixedIntervalMipOutcome solve(
        const FixedIntervalMipRequest& request) = 0;
    virtual void discardLeaf(const std::string&) {}
    // Idempotently release native resources before the final statistics
    // snapshot when an evidence path must prove environment/model symmetry.
    virtual void release() {}
    virtual FixedIntervalMipBackendStats stats() const = 0;
};

std::unique_ptr<FixedIntervalMipBackend> makeCplexFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);
std::unique_ptr<FixedIntervalMipBackend> makeGurobiFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);

} // namespace ebrp
