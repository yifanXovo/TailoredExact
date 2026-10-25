#include "GurobiCertificate.hpp"

#include <vector>

namespace ebrp {
namespace {

std::string join(const std::vector<std::string>& reasons) {
    std::string out;
    for (const std::string& reason : reasons) {
        if (!out.empty()) out += ";";
        out += reason;
    }
    return out.empty() ? "none" : out;
}

} // namespace

std::string gurobiStatusName(int status) {
    switch (status) {
    case kGurobiStatusLoaded: return "LOADED";
    case kGurobiStatusOptimal: return "OPTIMAL";
    case kGurobiStatusInfeasible: return "INFEASIBLE";
    case kGurobiStatusInfOrUnbd: return "INF_OR_UNBD";
    case kGurobiStatusUnbounded: return "UNBOUNDED";
    case kGurobiStatusCutoff: return "CUTOFF";
    case kGurobiStatusIterationLimit: return "ITERATION_LIMIT";
    case kGurobiStatusNodeLimit: return "NODE_LIMIT";
    case kGurobiStatusTimeLimit: return "TIME_LIMIT";
    case kGurobiStatusSolutionLimit: return "SOLUTION_LIMIT";
    case kGurobiStatusInterrupted: return "INTERRUPTED";
    case kGurobiStatusNumeric: return "NUMERIC";
    case kGurobiStatusSuboptimal: return "SUBOPTIMAL";
    case kGurobiStatusInProgress: return "INPROGRESS";
    case kGurobiStatusUserObjLimit: return "USER_OBJ_LIMIT";
    case kGurobiStatusWorkLimit: return "WORK_LIMIT";
    case kGurobiStatusMemLimit: return "MEM_LIMIT";
    default: return "UNKNOWN_STATUS_" + std::to_string(status);
    }
}

std::string gurobiStatusClass(int status) {
    if (status == kGurobiStatusOptimal) return "optimal";
    if (status == kGurobiStatusInfeasible) return "infeasible";
    if (status == kGurobiStatusTimeLimit || status == kGurobiStatusNodeLimit ||
        status == kGurobiStatusWorkLimit ||
        status == kGurobiStatusIterationLimit ||
        status == kGurobiStatusSolutionLimit ||
        status == kGurobiStatusMemLimit) {
        return "limit";
    }
    if (status == kGurobiStatusInterrupted) return "interrupted";
    if (status == kGurobiStatusInfOrUnbd ||
        status == kGurobiStatusUnbounded) {
        return "ambiguous_or_unbounded";
    }
    if (status == kGurobiStatusNumeric ||
        status == kGurobiStatusSuboptimal) {
        return "numeric_or_suboptimal";
    }
    return "unsupported";
}

GurobiCertificateDecision evaluateGurobiEngineeringExactCertificate(
    const GurobiCertificateInput& input) {
    GurobiCertificateDecision out;
    out.status_name = gurobiStatusName(input.status);
    out.status_class = gurobiStatusClass(input.status);
    out.native_model_scope = input.complete_original_model_scope
        ? "complete_original_compact_model" : "non_original_or_unverified_model";

    std::vector<std::string> common;
    if (!input.optimize_returned) common.push_back("optimize_did_not_return");
    if (!input.solver_finalization_completed) {
        common.push_back("solver_finalization_incomplete");
    }
    if (!input.complete_original_model_scope) {
        common.push_back("complete_original_model_scope_not_verified");
    }
    if (!input.model_configuration_valid) {
        common.push_back("native_model_configuration_invalid");
    }
    if (!input.lifecycle_valid) common.push_back("native_lifecycle_invalid");
    if (!input.executable_fingerprint_matches_manifest) {
        common.push_back("executable_fingerprint_mismatch");
    }
    if (!input.model_fingerprint_matches_manifest) {
        common.push_back("model_fingerprint_mismatch");
    }
    if (!input.no_tailored_or_external_information) {
        common.push_back("plain_information_isolation_failed");
    }
    if (!input.relative_gap_requested_exact_zero) {
        common.push_back("MIPGap_request_not_exact_zero");
    }
    if (!input.relative_gap_readback_exact_zero) {
        common.push_back("MIPGap_readback_not_exact_zero");
    }
    if (!input.absolute_gap_requested_exact_zero) {
        common.push_back("MIPGapAbs_request_not_exact_zero");
    }
    if (!input.absolute_gap_readback_exact_zero) {
        common.push_back("MIPGapAbs_readback_not_exact_zero");
    }

    if (input.status == kGurobiStatusOptimal) {
        if (!input.finite_solution_available) {
            common.push_back("finite_solution_unavailable");
        }
        if (!input.independently_verified_original_feasible) {
            common.push_back("independent_original_verifier_failed");
        }
        if (!input.objective_recomputed) {
            common.push_back("objective_recomputation_unavailable");
        }
        if (common.empty()) {
            out.strict_certified_original_problem = true;
            out.certificate_class = "engineering_exact_original_problem_optimal";
            out.rejection_reason = "none";
        } else {
            out.rejection_reason = join(common);
        }
        return out;
    }

    if (input.status == kGurobiStatusInfeasible) {
        out.infeasibility_scope = input.complete_original_model_scope
            ? "complete_original_compact_model" : "non_original_or_unverified_model";
        if (input.verified_feasible_witness_available) {
            out.feasibility_consistency_gate_passed = false;
            out.rejection_reason =
                "verified_feasible_witness_contradicts_native_infeasibility";
            return out;
        }
        if (common.empty()) {
            out.original_problem_infeasible_certified = true;
            out.certificate_class = "engineering_exact_original_problem_infeasible";
            out.rejection_reason = "none";
        } else {
            out.rejection_reason = join(common);
        }
        return out;
    }

    common.push_back("unsupported_strict_status:" + out.status_name);
    out.rejection_reason = join(common);
    return out;
}

} // namespace ebrp
