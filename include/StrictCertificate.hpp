#pragma once

#include <string>

namespace ebrp {

constexpr int kCplexMipOptimal = 101;
constexpr int kCplexMipOptimalTolerance = 102;
constexpr int kCplexMipInfeasible = 103;
constexpr int kCplexMipTimeLimitFeasible = 107;
constexpr int kCplexMipTimeLimitNoIncumbent = 108;
constexpr int kCplexMipOptimalUnscaledInfeasibilities = 115;
constexpr int kCplexRelativeMipGapParam = 2009;
constexpr int kCplexAbsoluteMipGapParam = 2008;
constexpr double kCplexInfinityBound = 1.0e20;

struct StrictGapParameterRecord {
    int parameter_id = 0;
    double requested = 0.0;
    int setter_return_code = -1;
    int getter_return_code = -1;
    double effective = 0.0;
};

struct StrictCertificateInput {
    int native_status_code = 0;
    std::string native_status_text;
    int native_objective_return_code = -1;
    bool native_objective_available = false;
    double native_objective = 0.0;
    int native_best_bound_return_code = -1;
    bool native_best_bound_available = false;
    double native_best_bound = 0.0;
    int native_cplex_relative_gap_return_code = -1;
    bool native_cplex_relative_gap_available = false;
    double native_cplex_relative_gap = 0.0;
    bool verified_upper_bound_available = false;
    double verified_upper_bound = 0.0;
    bool verifier_passed = false;
    bool solver_finalization_reached = false;
    bool lifecycle_complete = false;
    bool bound_equality_proof_conditions_passed = false;
    std::string bound_equality_proof_module;
    bool independent_exact_certificate_conditions_passed = false;
    std::string independent_exact_certificate_module;
    StrictGapParameterRecord relative_gap;
    StrictGapParameterRecord absolute_gap;
};

struct StrictCertificateDecision {
    std::string certificate_class = "invalid_or_unavailable_bound";
    std::string rejection_reason;
    bool strict_certified_original_problem = false;
    bool status_code_text_consistent = false;
    bool gap_parameters_valid = false;
    bool native_objective_valid = false;
    bool native_best_bound_valid = false;
    bool native_cplex_relative_gap_valid = false;
    bool bound_equality_closed = false;
    bool native_gap_available = false;
    bool verified_gap_available = false;
    double native_signed_bound_residual = 0.0;
    bool native_bound_inversion = false;
    double native_absolute_gap = 0.0;
    double native_relative_gap = 0.0;
    double native_cplex_denominator_relative_gap = 0.0;
    double verified_signed_bound_residual = 0.0;
    bool verified_bound_inversion = false;
    double verified_absolute_gap = 0.0;
    double verified_relative_gap = 0.0;
    double verified_project_relative_gap = 0.0;
};

bool cplexMipStatusTextConsistent(int status_code,
                                  const std::string& status_text);
bool strictGapParametersValid(const StrictCertificateInput& input);
StrictCertificateDecision classifyStrictCertificate(
    const StrictCertificateInput& input);

} // namespace ebrp
