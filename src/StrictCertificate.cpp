#include "StrictCertificate.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>

namespace ebrp {
namespace {

std::string lowerText(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
        [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return value;
}

bool contains(const std::string& text, const std::string& token) {
    return text.find(token) != std::string::npos;
}

double nonnegativeGap(double upper, double lower) {
    return std::max(0.0, upper - lower);
}

double reportingRelativeGap(double absolute_gap, double upper) {
    return absolute_gap / std::max(1.0, std::fabs(upper));
}

double cplexRelativeGap(double absolute_gap, double upper) {
    return absolute_gap / (1e-10 + std::fabs(upper));
}

double projectRelativeGap(double absolute_gap, double upper) {
    return std::fabs(upper) > 1e-12
        ? absolute_gap / std::fabs(upper)
        : (absolute_gap == 0.0 ? 0.0
                               : std::numeric_limits<double>::infinity());
}

} // namespace

bool cplexMipStatusTextConsistent(int status_code,
                                  const std::string& status_text) {
    const std::string text = lowerText(status_text);
    if (text.empty()) return false;
    switch (status_code) {
    case kCplexMipOptimal:
        return contains(text, "optimal") &&
               !contains(text, "tolerance") &&
               !contains(text, "infeas");
    case kCplexMipOptimalTolerance:
        return contains(text, "optimal") && contains(text, "tolerance");
    case kCplexMipInfeasible:
        return contains(text, "infeas") && !contains(text, "time");
    case kCplexMipTimeLimitFeasible:
        return contains(text, "time") && contains(text, "limit") &&
               !contains(text, "no integer");
    case kCplexMipTimeLimitNoIncumbent:
        return contains(text, "time") && contains(text, "limit") &&
               (contains(text, "no integer") || contains(text, "infeas"));
    case kCplexMipOptimalUnscaledInfeasibilities:
        return contains(text, "optimal") && contains(text, "infeas");
    default:
        return false;
    }
}

bool strictGapParametersValid(const StrictCertificateInput& input) {
    const StrictGapParameterRecord& rel = input.relative_gap;
    const StrictGapParameterRecord& abs = input.absolute_gap;
    return rel.parameter_id == kCplexRelativeMipGapParam &&
           abs.parameter_id == kCplexAbsoluteMipGapParam &&
           rel.requested == 0.0 && abs.requested == 0.0 &&
           rel.setter_return_code == 0 && abs.setter_return_code == 0 &&
           rel.getter_return_code == 0 && abs.getter_return_code == 0 &&
           rel.effective == 0.0 && abs.effective == 0.0;
}

StrictCertificateDecision classifyStrictCertificate(
    const StrictCertificateInput& input) {
    StrictCertificateDecision out;
    const double unavailable = std::numeric_limits<double>::quiet_NaN();
    out.native_absolute_gap = unavailable;
    out.native_signed_bound_residual = unavailable;
    out.native_relative_gap = unavailable;
    out.native_cplex_denominator_relative_gap = unavailable;
    out.verified_absolute_gap = unavailable;
    out.verified_signed_bound_residual = unavailable;
    out.verified_relative_gap = unavailable;
    out.verified_project_relative_gap = unavailable;
    out.native_vs_recomputed_objective_residual = unavailable;
    out.native_model_scope = input.native_model_scope;
    out.status_code_text_consistent = cplexMipStatusTextConsistent(
        input.native_status_code, input.native_status_text);
    out.gap_parameters_valid = strictGapParametersValid(input);
    out.model_correctness_verified = input.model_correctness_verified &&
        input.model_correctness_gate_version ==
            "round22-engineering-model-v1";
    out.native_objective_valid = input.native_objective_return_code == 0 &&
        input.native_objective_available && std::isfinite(input.native_objective) &&
        std::fabs(input.native_objective) < kCplexInfinityBound;
    out.native_best_bound_valid = input.native_best_bound_return_code == 0 &&
        input.native_best_bound_available &&
        std::isfinite(input.native_best_bound) &&
        std::fabs(input.native_best_bound) < kCplexInfinityBound;
    out.native_cplex_relative_gap_valid =
        input.native_cplex_relative_gap_return_code == 0 &&
        input.native_cplex_relative_gap_available &&
        std::isfinite(input.native_cplex_relative_gap) &&
        input.native_cplex_relative_gap >= 0.0 &&
        input.native_cplex_relative_gap < kCplexInfinityBound;

    if (out.native_best_bound_valid && out.native_objective_valid) {
        out.native_gap_available = true;
        out.native_signed_bound_residual =
            input.native_objective - input.native_best_bound;
        out.native_bound_inversion =
            input.native_best_bound > input.native_objective;
        out.native_absolute_gap = nonnegativeGap(
            input.native_objective, input.native_best_bound);
        out.native_relative_gap = reportingRelativeGap(
            out.native_absolute_gap, input.native_objective);
        out.native_cplex_denominator_relative_gap = cplexRelativeGap(
            out.native_absolute_gap, input.native_objective);
    }
    if (out.native_best_bound_valid &&
        input.verified_upper_bound_available &&
        std::isfinite(input.verified_upper_bound) &&
        std::fabs(input.verified_upper_bound) < kCplexInfinityBound) {
        out.verified_gap_available = true;
        out.verified_signed_bound_residual =
            input.verified_upper_bound - input.native_best_bound;
        out.verified_bound_inversion =
            input.native_best_bound > input.verified_upper_bound;
        out.verified_absolute_gap = nonnegativeGap(
            input.verified_upper_bound, input.native_best_bound);
        out.verified_relative_gap = reportingRelativeGap(
            out.verified_absolute_gap, input.verified_upper_bound);
        out.verified_project_relative_gap = projectRelativeGap(
            out.verified_absolute_gap, input.verified_upper_bound);
        // This is deliberately exact floating-point equality, not a project
        // tolerance or a display-rounded comparison.
        out.bound_equality_closed =
            input.native_best_bound == input.verified_upper_bound &&
            input.bound_equality_proof_conditions_passed &&
            !input.bound_equality_proof_module.empty();
    }
    if (out.native_objective_valid &&
        input.verified_upper_bound_available &&
        std::isfinite(input.verified_upper_bound)) {
        out.mapping_residual_available = true;
        out.native_vs_recomputed_objective_residual =
            input.verified_upper_bound - input.native_objective;
        const double diagnostic_scale = std::max({
            1.0, std::fabs(input.verified_upper_bound),
            std::fabs(input.native_objective)});
        out.mapping_residual_classification =
            std::fabs(out.native_vs_recomputed_objective_residual) <=
                    1e-9 * diagnostic_scale
                ? "mapping_residual_nominal"
                : "mapping_residual_warning";
    }

    if (!out.status_code_text_consistent) {
        out.certificate_class = "certificate_rejected";
        out.rejection_reason = "native_status_code_text_inconsistent";
        return out;
    }
    if (!out.gap_parameters_valid) {
        out.certificate_class = "certificate_rejected";
        out.rejection_reason = "strict_gap_parameter_round_trip_failed";
        return out;
    }
    if (!input.solver_finalization_reached || !input.lifecycle_complete) {
        out.certificate_class = "certificate_rejected";
        out.rejection_reason = "native_finalization_or_lifecycle_incomplete";
        return out;
    }
    if (!input.native_model_configuration_valid) {
        out.certificate_class = "certificate_rejected";
        out.rejection_reason = "native_model_configuration_invalid";
        return out;
    }
    if (input.native_status_code == kCplexMipInfeasible) {
        if (input.verified_feasible_witness_available &&
            input.verified_witness_satisfies_native_model) {
            out.certificate_class = "certificate_rejected";
            out.rejection_reason =
                "verified_feasible_witness_contradicts_native_infeasibility";
            out.feasibility_consistency_gate_passed = false;
            return out;
        }
        if (input.native_model_scope == "original_problem") {
            out.certificate_class = "original_problem_infeasible";
            out.infeasibility_scope = "original_problem";
        } else if (input.native_model_scope == "improving_range") {
            out.certificate_class = "improving_range_infeasible";
            out.infeasibility_scope = "improving_range";
        } else if (input.native_model_scope == "incumbent_cutoff_model") {
            out.certificate_class = "cutoff_model_infeasible";
            out.infeasibility_scope = "incumbent_cutoff_model";
        } else if (input.native_model_scope == "fixed_gini_child") {
            out.certificate_class = "fixed_gini_child_infeasible";
            out.infeasibility_scope = "fixed_gini_child";
        } else if (input.native_model_scope ==
                   "strict_improvement_under_verified_incumbent") {
            out.certificate_class = "no_strict_improvement_under_valid_incumbent";
            out.infeasibility_scope =
                "strict_improvement_under_verified_incumbent";
        } else {
            out.certificate_class = "certificate_rejected";
            out.rejection_reason = "unknown_native_model_scope";
        }
        return out;
    }
    if (input.native_status_code == kCplexMipOptimalUnscaledInfeasibilities) {
        out.certificate_class = "certificate_rejected";
        out.rejection_reason = "optimal_with_unscaled_infeasibilities";
        return out;
    }
    if (input.native_status_code == kCplexMipOptimal) {
        if (!out.model_correctness_verified) {
            out.certificate_class = "certificate_rejected";
            out.rejection_reason = "model_correctness_gate_failed";
        } else if (!input.verifier_passed) {
            out.certificate_class = "certificate_rejected";
            out.rejection_reason = "exact_status_verifier_failed";
        } else {
            // Round 22 engineering exactness follows the native status of the
            // audited complete model.  Objective/bound/recomputation residuals
            // remain signed, full-precision diagnostics; they are not a second
            // bitwise MIP proof and cannot reject status 101 by themselves.
            out.certificate_class = "native_engineering_exact_optimal";
            out.strict_certified_original_problem = true;
        }
        return out;
    }
    if (input.native_status_code == kCplexMipOptimalTolerance) {
        out.certificate_class = "native_tolerance_optimal_only";
        out.rejection_reason =
            "status_102_is_not_engineering_exact_status_101";
        return out;
    }
    if (input.native_status_code == kCplexMipTimeLimitFeasible ||
        input.native_status_code == kCplexMipTimeLimitNoIncumbent) {
        if (out.native_best_bound_valid) {
            out.certificate_class = "time_limit_valid_bound";
        } else {
            out.certificate_class = "invalid_or_unavailable_bound";
            out.rejection_reason = input.native_best_bound_return_code == 0
                ? "native_best_bound_nonfinite_or_unavailable"
                : "CPXgetbestobjval_failed";
        }
        return out;
    }
    if (!out.native_best_bound_valid) {
        out.certificate_class = "invalid_or_unavailable_bound";
        out.rejection_reason = input.native_best_bound_return_code == 0
            ? "native_best_bound_nonfinite_or_unavailable"
            : "CPXgetbestobjval_failed";
        return out;
    }
    out.certificate_class = "invalid_or_unavailable_bound";
    out.rejection_reason = "unsupported_native_status";
    return out;
}

} // namespace ebrp
