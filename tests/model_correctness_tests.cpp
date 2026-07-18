#include "ModelCorrectness.hpp"

#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::ModelCorrectnessInput completeInput() {
    ebrp::ModelCorrectnessInput in;
    in.executable_sha256 = std::string(64, 'a');
    in.source_commit_sha = std::string(40, 'b');
    in.model_writer_fingerprint = "writer-v1";
    in.objective_definition_fingerprint = "objective-v1";
    in.row_family_inventory = "all-original|all-static|selected-flow";
    in.callback_row_inventory = "all-local-interval-rows";
    in.variable_domain_inventory = "domains-v1";
    in.production_option_manifest_sha256 = std::string(64, 'c');
    in.algorithm_arm = "S0";
    in.flow_variant = "round20-current";
    in.objective_is_g_plus_lambda_p = true;
    in.station_inventory_and_capacity_complete = true;
    in.pickup_drop_and_vehicle_load_complete = true;
    in.route_degree_and_vehicle_use_complete = true;
    in.station_disjointness_complete = true;
    in.duration_and_operation_time_complete = true;
    in.gini_linearization_complete = true;
    in.improving_gini_range_complete = true;
    in.migrated_static_row_families_complete = true;
    in.selected_flow_rows_complete = true;
    in.callback_interval_rows_complete = true;
    in.variable_domains_complete = true;
    in.no_auxiliary_objective_terms = true;
    in.no_restricted_routes_or_incomplete_fallback = true;
    in.no_instance_dependent_option_resolution = true;
    in.production_options_match_manifest = true;
    in.one_model_lifecycle_design = true;
    return in;
}

void testCompleteGatePasses() {
    const auto out = ebrp::evaluateModelCorrectness(completeInput());
    require(out.verified, "complete model gate failed");
    require(out.failure_reason == "none", "complete failure reason");
}

void testProvenanceIsMandatory() {
    auto in = completeInput();
    in.executable_sha256.clear();
    const auto out = ebrp::evaluateModelCorrectness(in);
    require(!out.verified, "missing executable provenance accepted");
    require(out.failure_reason.find("executable_sha256") !=
                std::string::npos,
            "missing executable failure hidden");
}

void testEveryModelFamilyIsMandatory() {
    auto in = completeInput();
    in.duration_and_operation_time_complete = false;
    in.callback_interval_rows_complete = false;
    const auto out = ebrp::evaluateModelCorrectness(in);
    require(!out.verified, "missing model rows accepted");
    require(out.failed_checks.size() == 2,
            "missing model row failures not enumerated");
}

void testProductionUniformityIsMandatory() {
    auto in = completeInput();
    in.no_instance_dependent_option_resolution = false;
    in.production_options_match_manifest = false;
    const auto out = ebrp::evaluateModelCorrectness(in);
    require(!out.verified, "instance dispatch accepted");
    require(out.failure_reason.find(
                "no_instance_dependent_option_resolution") !=
                std::string::npos,
            "uniformity failure hidden");
}

void testAuditFingerprintIsDeterministicAndSensitive() {
    auto in = completeInput();
    const auto first = ebrp::evaluateModelCorrectness(in);
    const auto second = ebrp::evaluateModelCorrectness(in);
    require(first.audit_fingerprint == second.audit_fingerprint,
            "model audit fingerprint nondeterministic");
    in.flow_variant = "normalized-start-coupled";
    const auto changed = ebrp::evaluateModelCorrectness(in);
    require(first.audit_fingerprint != changed.audit_fingerprint,
            "flow variant absent from model audit fingerprint");
}

} // namespace

int main() {
    try {
        testCompleteGatePasses();
        testProvenanceIsMandatory();
        testEveryModelFamilyIsMandatory();
        testProductionUniformityIsMandatory();
        testAuditFingerprintIsDeterministicAndSensitive();
        std::cout << "ModelCorrectnessTests: 5 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ModelCorrectnessTests failure: " << error.what()
                  << '\n';
        return 1;
    }
}
