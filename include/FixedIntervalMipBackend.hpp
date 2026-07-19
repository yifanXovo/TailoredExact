#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace ebrp {

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
    std::string leaf_id;
    int attempt_number = 0;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double verified_cutoff = 0.0;
    double time_limit_seconds = 0.0;
    bool new_leaf = true;
    bool warm_start_enabled = false;
    std::filesystem::path canonical_model_path;
    std::string canonical_model_fingerprint;
    std::vector<RoutePlan> verified_start_routes;
    std::string verified_start_source;
};

struct FixedIntervalMipOutcome {
    bool attempted = false;
    bool available = false;
    bool solver_finalization_reached = false;
    bool optimal = false;
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
    bool exact_zero_gap_roundtrip = false;
    bool model_fingerprint_matches_request = false;
    bool same_leaf_model_retained = false;
    bool fresh_restart = false;
    bool child_restart = false;
    bool reset_called = false;
    bool native_continuation_claimed = false;
    bool native_continuation_evidence = false;
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
    long long model_free_count = 0;
    long long environment_free_count = 0;
    long long same_leaf_resume_count = 0;
    long long fresh_restart_count = 0;
    long long child_restart_count = 0;
    long long reset_call_count = 0;
    long long warm_start_candidate_count = 0;
    long long warm_start_complete_count = 0;
    long long warm_start_submitted_count = 0;
    long long warm_start_accepted_count = 0;
    long long warm_start_rejected_count = 0;
    long long warm_start_unknown_count = 0;
    double cumulative_model_build_seconds = 0.0;
    double cumulative_model_read_seconds = 0.0;
    double cumulative_solver_runtime_seconds = 0.0;
    double cumulative_work = 0.0;
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
    virtual FixedIntervalMipBackendStats stats() const = 0;
};

std::unique_ptr<FixedIntervalMipBackend> makeCplexFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);
std::unique_ptr<FixedIntervalMipBackend> makeGurobiFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);

} // namespace ebrp
