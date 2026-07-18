#include "StrictCertificate.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

#if __has_include(<ilcplex/cpxconst.h>)
#define CPXSIZE_BITS_TEST_DISABLE
#include <ilcplex/cpxconst.h>
#undef CPXSIZE_BITS_TEST_DISABLE
#define EXACT_EBRP_HAS_INSTALLED_CPLEX_HEADER 1
#else
#define EXACT_EBRP_HAS_INSTALLED_CPLEX_HEADER 0
#endif

namespace {

using ebrp::StrictCertificateInput;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

StrictCertificateInput engineeringExactInput() {
    StrictCertificateInput in;
    in.native_status_code = ebrp::kCplexMipOptimal;
    in.native_status_text = "integer optimal solution";
    in.native_objective_return_code = 0;
    in.native_objective_available = true;
    in.native_objective = 0.75;
    in.native_best_bound_return_code = 0;
    in.native_best_bound_available = true;
    in.native_best_bound = 0.75;
    in.native_cplex_relative_gap_return_code = 0;
    in.native_cplex_relative_gap_available = true;
    in.native_cplex_relative_gap = 0.0;
    in.verified_upper_bound_available = true;
    in.verified_upper_bound = 0.75;
    in.verifier_passed = true;
    in.model_correctness_verified = true;
    in.model_correctness_gate_version = "round22-engineering-model-v1";
    in.solver_finalization_reached = true;
    in.lifecycle_complete = true;
    in.relative_gap = {ebrp::kCplexRelativeMipGapParam, 0.0, 0, 0, 0.0};
    in.absolute_gap = {ebrp::kCplexAbsoluteMipGapParam, 0.0, 0, 0, 0.0};
    return in;
}

void testInstalledStatusMapping() {
    require(ebrp::kCplexMipOptimal == 101, "exact status id");
    require(ebrp::kCplexMipOptimalTolerance == 102, "tolerance status id");
    require(ebrp::kCplexMipInfeasible == 103, "infeasible status id");
    require(ebrp::kCplexMipTimeLimitFeasible == 107, "time feasible id");
    require(ebrp::kCplexMipTimeLimitNoIncumbent == 108,
            "time no-incumbent id");
    require(ebrp::kCplexMipOptimalUnscaledInfeasibilities == 115,
            "unscaled-infeasibilities id");
    require(ebrp::kCplexRelativeMipGapParam == 2009, "relative gap id");
    require(ebrp::kCplexAbsoluteMipGapParam == 2008, "absolute gap id");
#if EXACT_EBRP_HAS_INSTALLED_CPLEX_HEADER
    require(ebrp::kCplexMipOptimal == CPXMIP_OPTIMAL,
            "installed exact status mapping");
    require(ebrp::kCplexMipOptimalTolerance == CPXMIP_OPTIMAL_TOL,
            "installed tolerance status mapping");
    require(ebrp::kCplexMipTimeLimitFeasible == CPXMIP_TIME_LIM_FEAS,
            "installed time-limit mapping");
    require(ebrp::kCplexMipTimeLimitNoIncumbent == CPXMIP_TIME_LIM_INFEAS,
            "installed no-incumbent mapping");
    require(ebrp::kCplexRelativeMipGapParam ==
                CPXPARAM_MIP_Tolerances_MIPGap,
            "installed relative parameter mapping");
    require(ebrp::kCplexAbsoluteMipGapParam ==
                CPXPARAM_MIP_Tolerances_AbsMIPGap,
            "installed absolute parameter mapping");
#endif
}

void testNominalPositiveMappingTailPasses() {
    auto in = engineeringExactInput();
    in.verified_upper_bound = in.native_objective + 1e-15;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.strict_certified_original_problem,
            "positive 1e-15 mapping tail rejected status 101");
    require(out.certificate_class ==
                "native_engineering_exact_optimal",
            "engineering exact class");
    require(out.mapping_residual_classification ==
                "mapping_residual_nominal",
            "positive tail diagnostic");
}

void testNominalNegativeMappingTailPasses() {
    auto in = engineeringExactInput();
    in.verified_upper_bound = in.native_objective - 1e-16;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.strict_certified_original_problem,
            "negative 1e-16 mapping tail rejected status 101");
    require(out.native_vs_recomputed_objective_residual < 0.0,
            "signed negative mapping residual lost");
}

void testStatus102NeverStrict() {
    auto in = engineeringExactInput();
    in.native_status_code = ebrp::kCplexMipOptimalTolerance;
    in.native_status_text = "integer optimal, tolerance";
    in.bound_equality_proof_conditions_passed = true;
    in.bound_equality_proof_module = "diagnostic_equality";
    const auto out = ebrp::classifyStrictCertificate(in);
    require(!out.strict_certified_original_problem, "status 102 upgraded");
    require(out.certificate_class == "native_tolerance_optimal_only",
            "status 102 class");
}

void testStatus107NeverStrict() {
    auto in = engineeringExactInput();
    in.native_status_code = ebrp::kCplexMipTimeLimitFeasible;
    in.native_status_text = "time limit exceeded";
    const auto out = ebrp::classifyStrictCertificate(in);
    require(!out.strict_certified_original_problem, "status 107 upgraded");
    require(out.certificate_class == "time_limit_valid_bound",
            "status 107 bound class");
}

void testStatus108NeverStrict() {
    auto in = engineeringExactInput();
    in.native_status_code = ebrp::kCplexMipTimeLimitNoIncumbent;
    in.native_status_text =
        "time limit exceeded, no integer solution";
    in.native_objective_available = false;
    in.native_objective_return_code = 1217;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(!out.strict_certified_original_problem, "status 108 upgraded");
    require(out.certificate_class == "time_limit_valid_bound",
            "status 108 bound class");
}

void testStatus115Rejected() {
    auto in = engineeringExactInput();
    in.native_status_code =
        ebrp::kCplexMipOptimalUnscaledInfeasibilities;
    in.native_status_text =
        "integer optimal solution with unscaled infeasibilities";
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.rejection_reason ==
                "optimal_with_unscaled_infeasibilities",
            "status 115 was not rejected");
}

void testRelativeGapRoundTripRejects() {
    auto in = engineeringExactInput();
    in.relative_gap.effective = 1e-9;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.rejection_reason ==
                "strict_gap_parameter_round_trip_failed",
            "nonzero relative parameter accepted");
}

void testAbsoluteGapRoundTripRejects() {
    auto in = engineeringExactInput();
    in.absolute_gap.requested = 1e-9;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.rejection_reason ==
                "strict_gap_parameter_round_trip_failed",
            "nonzero absolute parameter accepted");
}

void testSetterGetterFailuresReject() {
    auto setter = engineeringExactInput();
    setter.relative_gap.setter_return_code = 1016;
    require(ebrp::classifyStrictCertificate(setter).rejection_reason ==
                "strict_gap_parameter_round_trip_failed",
            "setter failure accepted");
    auto getter = engineeringExactInput();
    getter.absolute_gap.getter_return_code = 1016;
    require(ebrp::classifyStrictCertificate(getter).rejection_reason ==
                "strict_gap_parameter_round_trip_failed",
            "getter failure accepted");
}

void testLifecycleFailureRejects() {
    auto in = engineeringExactInput();
    in.lifecycle_complete = false;
    require(ebrp::classifyStrictCertificate(in).rejection_reason ==
                "native_finalization_or_lifecycle_incomplete",
            "lifecycle failure accepted");
}

void testModelCorrectnessFailureRejects() {
    auto in = engineeringExactInput();
    in.model_correctness_verified = false;
    require(ebrp::classifyStrictCertificate(in).rejection_reason ==
                "model_correctness_gate_failed",
            "model correctness failure accepted");
}

void testVerifierFailureRejects() {
    auto in = engineeringExactInput();
    in.verifier_passed = false;
    require(ebrp::classifyStrictCertificate(in).rejection_reason ==
                "exact_status_verifier_failed",
            "verifier failure accepted");
}

void testNativeLowerBoundNeverOverwritten() {
    auto in = engineeringExactInput();
    in.native_best_bound = 0.70;
    in.verified_upper_bound = 0.75;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.strict_certified_original_problem,
            "diagnostic bound residual rejected status 101");
    require(in.native_best_bound == 0.70,
            "classifier overwrote native lower bound");
    require(std::fabs(out.verified_signed_bound_residual - 0.05) < 1e-15,
            "signed retained bound residual changed");
}

void testMappingResidualRetainedNotGate() {
    auto in = engineeringExactInput();
    in.native_objective = 0.75;
    in.verified_upper_bound = std::nextafter(0.75, 1.0);
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.mapping_residual_available, "mapping residual unavailable");
    require(out.native_vs_recomputed_objective_residual > 0.0,
            "mapping residual sign lost");
    require(out.strict_certified_original_problem,
            "last-bit residual used as bitwise gate");
}

void testLargeMappingAnomalyVisible() {
    auto in = engineeringExactInput();
    in.verified_upper_bound = 0.751;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.mapping_residual_classification ==
                "mapping_residual_warning",
            "large mapping anomaly hidden");
    require(out.native_vs_recomputed_objective_residual > 0.0009,
            "large signed residual not retained");
    require(out.strict_certified_original_problem,
            "diagnostic warning invented a seventh certificate gate");
}

void testObservedNativeGapIsDiagnostic() {
    auto in = engineeringExactInput();
    in.native_cplex_relative_gap = 1e-15;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.strict_certified_original_problem,
            "CPXgetmiprelgap tail replaced status-101 semantics");
    require(out.native_cplex_relative_gap_valid,
            "native gap diagnostic was discarded");
}

void testStatusTextMismatchRejects() {
    auto in = engineeringExactInput();
    in.native_status_text = "integer optimal, tolerance";
    require(ebrp::classifyStrictCertificate(in).rejection_reason ==
                "native_status_code_text_inconsistent",
            "status code/text mismatch accepted");
}

} // namespace

int main() {
    try {
        testInstalledStatusMapping();
        testNominalPositiveMappingTailPasses();
        testNominalNegativeMappingTailPasses();
        testStatus102NeverStrict();
        testStatus107NeverStrict();
        testStatus108NeverStrict();
        testStatus115Rejected();
        testRelativeGapRoundTripRejects();
        testAbsoluteGapRoundTripRejects();
        testSetterGetterFailuresReject();
        testLifecycleFailureRejects();
        testModelCorrectnessFailureRejects();
        testVerifierFailureRejects();
        testNativeLowerBoundNeverOverwritten();
        testMappingResidualRetainedNotGate();
        testLargeMappingAnomalyVisible();
        testObservedNativeGapIsDiagnostic();
        testStatusTextMismatchRejects();
        std::cout << "StrictCertificateTests: 18 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "StrictCertificateTests failure: " << error.what()
                  << '\n';
        return 1;
    }
}
