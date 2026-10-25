#pragma once

#include <string>

namespace ebrp {

constexpr int kGurobiStatusLoaded = 1;
constexpr int kGurobiStatusOptimal = 2;
constexpr int kGurobiStatusInfeasible = 3;
constexpr int kGurobiStatusInfOrUnbd = 4;
constexpr int kGurobiStatusUnbounded = 5;
constexpr int kGurobiStatusCutoff = 6;
constexpr int kGurobiStatusIterationLimit = 7;
constexpr int kGurobiStatusNodeLimit = 8;
constexpr int kGurobiStatusTimeLimit = 9;
constexpr int kGurobiStatusSolutionLimit = 10;
constexpr int kGurobiStatusInterrupted = 11;
constexpr int kGurobiStatusNumeric = 12;
constexpr int kGurobiStatusSuboptimal = 13;
constexpr int kGurobiStatusInProgress = 14;
constexpr int kGurobiStatusUserObjLimit = 15;
constexpr int kGurobiStatusWorkLimit = 16;
constexpr int kGurobiStatusMemLimit = 17;

std::string gurobiStatusName(int status);
std::string gurobiStatusClass(int status);

struct GurobiCertificateInput {
    int status = 0;
    bool optimize_returned = false;
    bool solver_finalization_completed = false;
    bool complete_original_model_scope = false;
    bool model_configuration_valid = false;
    bool lifecycle_valid = false;
    bool executable_fingerprint_matches_manifest = false;
    bool model_fingerprint_matches_manifest = false;
    bool no_tailored_or_external_information = false;
    bool relative_gap_requested_exact_zero = false;
    bool relative_gap_readback_exact_zero = false;
    bool absolute_gap_requested_exact_zero = false;
    bool absolute_gap_readback_exact_zero = false;
    bool finite_solution_available = false;
    bool independently_verified_original_feasible = false;
    bool objective_recomputed = false;
    bool verified_feasible_witness_available = false;
};

struct GurobiCertificateDecision {
    std::string policy_version = "round24-gurobi-engineering-exact-v1";
    std::string status_name;
    std::string status_class;
    std::string certificate_class = "certificate_rejected";
    std::string rejection_reason = "not_evaluated";
    std::string native_model_scope = "unknown";
    std::string infeasibility_scope = "not_infeasible";
    bool strict_certified_original_problem = false;
    bool original_problem_infeasible_certified = false;
    bool feasibility_consistency_gate_passed = true;
};

GurobiCertificateDecision evaluateGurobiEngineeringExactCertificate(
    const GurobiCertificateInput& input);

} // namespace ebrp
