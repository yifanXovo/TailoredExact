#pragma once

#include "FixedIntervalMipBackend.hpp"

namespace ebrp {

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
