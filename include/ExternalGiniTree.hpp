#pragma once

#include "FixedIntervalMipBackend.hpp"

namespace ebrp {

struct ExternalCplexLeafStatusInput {
    int native_status_code = 0;
    bool exact_zero_gap_roundtrip = false;
    bool solver_finalization_reached = false;
    bool lifecycle_complete = false;
    bool model_fingerprint_matches = false;
    bool verified_witness_contradicts_infeasibility = false;
};

struct ExternalCplexLeafStatusDecision {
    bool native_status_supported = false;
    bool exact_optimal = false;
    bool tolerance_optimal = false;
    bool optimal_unscaled_infeasibilities = false;
    bool infeasible = false;
    bool interrupted = false;
    bool may_close_leaf = false;
    bool feasibility_consistency_gate = true;
    std::string status_class = "unsupported";
    std::string rejection_reason = "unsupported_native_status";
};

ExternalCplexLeafStatusDecision evaluateExternalCplexLeafStatus(
    const ExternalCplexLeafStatusInput& input);

struct ImmutableLeafArtifactContract {
    std::string leaf_id;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double cutoff = 0.0;
    std::filesystem::path path;
    std::string sha256;
    std::string model_scope;
    std::string row_signature;
};

bool immutableLeafArtifactReusable(
    const ImmutableLeafArtifactContract& cached,
    const ImmutableLeafArtifactContract& requested,
    std::string* rejection_reason = nullptr);

struct ExternalGiniTreeCertificateInput {
    bool complete_root_coverage = false;
    bool parent_child_coverage_valid = false;
    bool all_relevant_leaves_closed = false;
    bool all_leaf_bounds_valid = false;
    bool global_bound_valid = false;
    bool global_bound_monotone = false;
    bool leaf_bounds_monotone = false;
    bool verified_global_ub = false;
    bool lifecycle_complete = false;
    bool feasibility_consistency_gate = false;
    double global_lb = 0.0;
    double verified_ub = 0.0;
    double tolerance = 1e-7;
};

struct ExternalGiniTreeCertificateDecision {
    bool certified = false;
    std::string certificate_class = "certificate_rejected";
    std::string rejection_reason = "not_evaluated";
};

ExternalGiniTreeCertificateDecision evaluateExternalGiniTreeCertificate(
    const ExternalGiniTreeCertificateInput& input);

SolveResult solveExternalGiniTree(const Instance& instance,
                                  const SolveOptions& options,
                                  const SolveResult& verified_seed,
                                  double root_gamma_L,
                                  double root_gamma_U);

} // namespace ebrp
