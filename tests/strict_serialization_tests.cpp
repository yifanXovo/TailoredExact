#include "Result.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

std::string fullPrecision(double value) {
    std::ostringstream out;
    out << std::setprecision(std::numeric_limits<double>::max_digits10)
        << value;
    return out.str();
}

void testToleranceGapAndLowerBoundRemainRaw() {
    ebrp::SolveResult result;
    result.method = "cplex";
    result.status = "optimal"; // Deliberately false wrapper claim.
    result.objective = 0.75;
    result.upper_bound = 0.75;
    result.lower_bound = std::nextafter(0.75, 0.0);
    result.gap = (result.upper_bound - result.lower_bound) /
        std::fabs(result.upper_bound);
    result.native_mip_evidence_available = true;
    result.native_mip_status_code = 102;
    result.native_mip_status_text_available = true;
    result.native_mip_status_text = "integer optimal, tolerance";
    result.native_mip_best_bound_return_code = 0;
    result.native_mip_best_bound_available = true;
    result.native_mip_best_bound = result.lower_bound;
    result.native_mip_objective_return_code = 0;
    result.native_mip_objective_available = true;
    result.native_mip_objective = result.upper_bound;
    result.verified_incumbent_objective_available = true;
    result.verified_incumbent_objective = result.upper_bound;
    result.verified_incumbent_project_relative_gap_available = true;
    result.verified_incumbent_project_relative_gap = result.gap;
    result.strict_certificate_class = "native_tolerance_optimal_only";
    result.strict_certificate_rejection_reason =
        "tolerance_status_with_positive_retained_native_gap";
    result.strict_certified_original_problem = false;

    const std::string json = ebrp::resultToJson(result);
    require(json.find("\"status\": \"not_certified_incomplete_certificate\"") !=
                std::string::npos,
            "output guard did not reject false optimal status");
    require(json.find("\"lower_bound\": " +
                      fullPrecision(result.lower_bound)) != std::string::npos,
            "serialized lower bound was overwritten or rounded");
    require(json.find("\"native_mip_best_bound\": " +
                      fullPrecision(result.native_mip_best_bound)) !=
                std::string::npos,
            "raw native best bound lost full precision");
    require(json.find("\"gap\": " + fullPrecision(result.gap)) !=
                std::string::npos,
            "positive sub-display gap was changed");
    require(json.find("\"gap\": 0") == std::string::npos,
            "positive tolerance gap serialized as zero");
}

void testUnavailableValuesAreNull() {
    ebrp::SolveResult result;
    result.method = "cplex";
    result.status = "not_certified";
    result.native_mip_evidence_available = true;
    result.native_mip_objective_available = false;
    result.native_mip_best_bound_available = false;
    const std::string json = ebrp::resultToJson(result);
    require(json.find("\"native_mip_objective\": null") !=
                std::string::npos,
            "unavailable objective was fabricated as a number");
    require(json.find("\"native_mip_best_bound\": null") !=
                std::string::npos,
            "unavailable best bound was fabricated as a number");
    require(json.find("\"lower_bound\": null") != std::string::npos,
            "unavailable official lower bound was fabricated as a number");
    require(json.find("\"upper_bound\": null") != std::string::npos,
            "unavailable verified upper bound was fabricated as a number");
    require(json.find("\"gap\": null") != std::string::npos,
            "gap without a native lower bound was fabricated as zero");
}

void testStoredStrictFlagControlsCplexClaim() {
    ebrp::SolveResult result;
    result.method = "cplex";
    result.status = "optimal";
    result.strict_certificate_class = "native_engineering_exact_optimal";
    result.strict_certified_original_problem = true;
    require(ebrp::inferCertifiedOriginalProblem(result),
            "stored valid strict CPLEX flag was ignored");
    const std::string json = ebrp::resultToJson(result);
    require(json.find("\"status\": \"optimal\"") != std::string::npos,
            "valid strict status was guarded away");
}

void testMappingResidualAndRound22GatesRoundTrip() {
    ebrp::SolveResult result;
    result.method = "cplex";
    result.status = "optimal";
    result.strict_certificate_class = "native_engineering_exact_optimal";
    result.strict_certified_original_problem = true;
    result.verified_incumbent_objective_residual_available = true;
    result.verified_incumbent_objective_residual =
        std::nextafter(0.0, 1.0);
    result.objective_mapping_diagnostic = "mapping_residual_nominal";
    result.model_correctness_verified = true;
    result.model_correctness_audit_fingerprint = "0123456789abcdef";
    result.dense_progress_enabled = true;
    result.dense_progress_final_record_appended = true;
    result.dense_progress_flush_succeeded = true;
    const std::string json = ebrp::resultToJson(result);
    require(json.find("\"native_vs_recomputed_objective_residual\": " +
                      fullPrecision(
                          result.verified_incumbent_objective_residual)) !=
                std::string::npos,
            "mapping residual lost round-trip-safe precision");
    require(json.find("\"objective_mapping_diagnostic\": "
                      "\"mapping_residual_nominal\"") !=
                std::string::npos,
            "mapping diagnostic missing");
    require(json.find("\"model_correctness_verified\": true") !=
                std::string::npos,
            "model-correctness gate missing");
    require(json.find("\"dense_progress_final_record_appended\": true") !=
                std::string::npos,
            "dense finalization evidence missing");
}

} // namespace

int main() {
    try {
        testToleranceGapAndLowerBoundRemainRaw();
        testUnavailableValuesAreNull();
        testStoredStrictFlagControlsCplexClaim();
        testMappingResidualAndRound22GatesRoundTrip();
        std::cout << "StrictSerializationTests: 4 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "StrictSerializationTests failure: "
                  << error.what() << '\n';
        return 1;
    }
}
