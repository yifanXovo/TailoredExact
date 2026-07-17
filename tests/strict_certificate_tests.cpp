#include "StrictCertificate.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

#if __has_include(<ilcplex/cpxconst.h>)
// IBM's Windows headers model CPXSIZE for the MSVC ABI; MinGW has a
// different `long` width.  Disable only that unrelated ABI typedef check so
// this header-level constants audit can compare the installed status/parameter
// macros without linking to CPLEX.
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

StrictCertificateInput exactInput() {
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
    require(ebrp::kCplexInfinityBound == 1.0e20,
            "CPLEX infinity threshold");
#if EXACT_EBRP_HAS_INSTALLED_CPLEX_HEADER
    require(ebrp::kCplexMipOptimal == CPXMIP_OPTIMAL,
            "installed exact status mapping");
    require(ebrp::kCplexMipOptimalTolerance == CPXMIP_OPTIMAL_TOL,
            "installed tolerance status mapping");
    require(ebrp::kCplexMipInfeasible == CPXMIP_INFEASIBLE,
            "installed infeasible status mapping");
    require(ebrp::kCplexMipTimeLimitFeasible == CPXMIP_TIME_LIM_FEAS,
            "installed feasible time-limit mapping");
    require(ebrp::kCplexMipTimeLimitNoIncumbent == CPXMIP_TIME_LIM_INFEAS,
            "installed no-incumbent time-limit mapping");
    require(ebrp::kCplexMipOptimalUnscaledInfeasibilities ==
                CPXMIP_OPTIMAL_INFEAS,
            "installed unscaled-infeasibilities mapping");
    require(ebrp::kCplexRelativeMipGapParam ==
                CPXPARAM_MIP_Tolerances_MIPGap,
            "installed relative gap parameter mapping");
    require(ebrp::kCplexAbsoluteMipGapParam ==
                CPXPARAM_MIP_Tolerances_AbsMIPGap,
            "installed absolute gap parameter mapping");
    require(ebrp::kCplexInfinityBound == CPX_INFBOUND,
            "installed infinity-bound mapping");
#endif
}

void testStrictPositiveAndRawRetention() {
    const StrictCertificateInput in = exactInput();
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.strict_certified_original_problem, "exact strict closure");
    require(out.certificate_class == "native_exact_optimal", "exact class");
    require(out.native_best_bound_valid, "raw bound valid");
    require(out.verified_absolute_gap == 0.0, "zero raw gap");
    require(in.native_best_bound == 0.75, "input raw LB unchanged");
}

void testExactStatusRetainedGapAndInversionRejected() {
    auto positive = exactInput();
    positive.native_best_bound = 0.749999999999;
    auto out = ebrp::classifyStrictCertificate(positive);
    require(!out.strict_certified_original_problem,
            "positive-gap status 101 was called strict");
    require(out.rejection_reason ==
                "exact_status_positive_native_gap_or_bound_inversion",
            "positive native gap rejection reason");

    auto observed_positive = exactInput();
    observed_positive.native_cplex_relative_gap = 1e-12;
    out = ebrp::classifyStrictCertificate(observed_positive);
    require(out.rejection_reason ==
                "exact_status_native_cplex_gap_not_zero",
            "positive CPXgetmiprelgap observation was called strict");

    auto verified_positive = exactInput();
    verified_positive.verified_upper_bound =
        std::nextafter(0.75, 1.0);
    out = ebrp::classifyStrictCertificate(verified_positive);
    require(out.rejection_reason ==
                "exact_status_native_bound_not_equal_verified_upper_bound",
            "positive verified gap was called strict");

    auto inversion = exactInput();
    inversion.verified_upper_bound = std::nextafter(0.75, 0.0);
    out = ebrp::classifyStrictCertificate(inversion);
    require(out.verified_bound_inversion,
            "signed native-bound/verified-UB inversion was hidden");
    require(out.rejection_reason ==
                "exact_status_native_bound_not_equal_verified_upper_bound",
            "bound inversion was called strict");
}

void testTolerancePositiveGapRejected() {
    auto in = exactInput();
    in.native_status_code = ebrp::kCplexMipOptimalTolerance;
    in.native_status_text = "integer optimal, tolerance";
    in.native_best_bound = 0.7499995;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(!out.strict_certified_original_problem, "tolerance not strict");
    require(out.certificate_class == "native_tolerance_optimal_only",
            "tolerance class");
    require(out.verified_absolute_gap > 0.0, "positive retained gap");
}

void testTimeLimitPositiveGapRejected() {
    auto in = exactInput();
    in.native_status_code = ebrp::kCplexMipTimeLimitFeasible;
    in.native_status_text = "time limit exceeded";
    in.native_best_bound = 0.5;
    const auto out = ebrp::classifyStrictCertificate(in);
    require(!out.strict_certified_original_problem, "time limit not strict");
    require(out.certificate_class == "time_limit_valid_bound",
            "time-limit valid-bound class");
}

void testMissingAndFailedBestBound() {
    auto missing = exactInput();
    missing.native_best_bound_available = false;
    auto out = ebrp::classifyStrictCertificate(missing);
    require(out.certificate_class == "invalid_or_unavailable_bound",
            "missing bound rejected");
    auto failed = exactInput();
    failed.native_best_bound_return_code = 1217;
    out = ebrp::classifyStrictCertificate(failed);
    require(out.rejection_reason == "CPXgetbestobjval_failed",
            "failed bound API retained");
    auto infinite_proxy = exactInput();
    infinite_proxy.native_best_bound = -1.0e75;
    out = ebrp::classifyStrictCertificate(infinite_proxy);
    require(out.certificate_class == "invalid_or_unavailable_bound",
            "CPLEX no-information infinite proxy accepted as a bound");
}

void testNoRoundingToZero() {
    auto in = exactInput();
    in.native_status_code = ebrp::kCplexMipOptimalTolerance;
    in.native_status_text = "integer optimal, tolerance";
    in.native_best_bound = std::nextafter(0.75, 0.0);
    const auto out = ebrp::classifyStrictCertificate(in);
    require(out.verified_absolute_gap > 0.0, "sub-display gap retained");
    require(!out.bound_equality_closed, "display rounding is not equality");
    require(!out.strict_certified_original_problem, "rounded gap not strict");
}

void testVerifierLifecycleAndStatusMismatch() {
    auto verifier = exactInput();
    verifier.verifier_passed = false;
    auto out = ebrp::classifyStrictCertificate(verifier);
    require(out.certificate_class == "certificate_rejected",
            "exact verifier failure rejected");
    auto lifecycle = exactInput();
    lifecycle.lifecycle_complete = false;
    out = ebrp::classifyStrictCertificate(lifecycle);
    require(out.rejection_reason == "native_finalization_or_lifecycle_incomplete",
            "lifecycle failure rejected");
    auto mismatch = exactInput();
    mismatch.native_status_text = "integer optimal, tolerance";
    out = ebrp::classifyStrictCertificate(mismatch);
    require(out.rejection_reason == "native_status_code_text_inconsistent",
            "code/text mismatch rejected");
    auto missing_verified = exactInput();
    missing_verified.verified_upper_bound_available = false;
    out = ebrp::classifyStrictCertificate(missing_verified);
    require(out.rejection_reason ==
                "exact_status_verified_upper_bound_unavailable",
            "exact status without retained verified UB rejected");

    auto unscaled = exactInput();
    unscaled.native_status_code =
        ebrp::kCplexMipOptimalUnscaledInfeasibilities;
    unscaled.native_status_text =
        "integer optimal solution with unscaled infeasibilities";
    unscaled.independent_exact_certificate_conditions_passed = true;
    unscaled.independent_exact_certificate_module = "toy_exact_module";
    out = ebrp::classifyStrictCertificate(unscaled);
    require(out.rejection_reason ==
                "optimal_with_unscaled_infeasibilities",
            "status 115 cannot be upgraded by another proof route");
}

void testGapRoundTripFailures() {
    auto relative = exactInput();
    relative.relative_gap.effective = 1e-4;
    auto out = ebrp::classifyStrictCertificate(relative);
    require(out.rejection_reason == "strict_gap_parameter_round_trip_failed",
            "relative mismatch rejected");
    auto absolute = exactInput();
    absolute.absolute_gap.effective = 1e-6;
    out = ebrp::classifyStrictCertificate(absolute);
    require(out.rejection_reason == "strict_gap_parameter_round_trip_failed",
            "absolute mismatch rejected");
    auto missing_native_gap = exactInput();
    missing_native_gap.native_cplex_relative_gap_available = false;
    missing_native_gap.native_cplex_relative_gap_return_code = 1217;
    out = ebrp::classifyStrictCertificate(missing_native_gap);
    require(out.rejection_reason ==
                "native_mip_relative_gap_unavailable_for_strict_certificate",
            "failed native MIP-gap retrieval did not reject exact claim");
}

void testExactBoundEqualityAndIndependentCertificate() {
    auto equality = exactInput();
    equality.native_status_code = ebrp::kCplexMipOptimalTolerance;
    equality.native_status_text = "integer optimal, tolerance";
    auto unproved = ebrp::classifyStrictCertificate(equality);
    require(!unproved.strict_certified_original_problem,
            "unproved floating equality does not close");
    equality.bound_equality_proof_conditions_passed = true;
    equality.bound_equality_proof_module = "toy_exact_rational_equality";
    const auto closed = ebrp::classifyStrictCertificate(equality);
    require(closed.strict_certified_original_problem, "proved equality closes");
    require(closed.certificate_class == "native_bound_equality_closed",
            "bound equality class");

    auto independent = exactInput();
    independent.native_status_code = ebrp::kCplexMipTimeLimitFeasible;
    independent.native_status_text = "time limit exceeded";
    independent.native_best_bound = 0.4;
    independent.independent_exact_certificate_conditions_passed = true;
    independent.independent_exact_certificate_module = "toy_exact_module";
    const auto proved = ebrp::classifyStrictCertificate(independent);
    require(proved.strict_certified_original_problem,
            "independent exact proof closes");
    require(proved.certificate_class == "independent_exact_certificate",
            "independent class");
}

} // namespace

int main() {
    try {
        testInstalledStatusMapping();
        testStrictPositiveAndRawRetention();
        testExactStatusRetainedGapAndInversionRejected();
        testTolerancePositiveGapRejected();
        testTimeLimitPositiveGapRejected();
        testMissingAndFailedBestBound();
        testNoRoundingToZero();
        testVerifierLifecycleAndStatusMismatch();
        testGapRoundTripFailures();
        testExactBoundEqualityAndIndependentCertificate();
        std::cout << "StrictCertificateTests: 10 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "StrictCertificateTests failure: " << error.what() << '\n';
        return 1;
    }
}
