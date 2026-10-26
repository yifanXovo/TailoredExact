#pragma once

#include <string>
#include <vector>

namespace ebrp {

constexpr const char* kRound22ModelCorrectnessGateVersion =
    "round22-engineering-model-v1";

struct ModelCorrectnessInput {
    std::string gate_version = kRound22ModelCorrectnessGateVersion;
    std::string executable_sha256;
    std::string source_commit_sha;
    std::string model_writer_fingerprint;
    std::string objective_definition_fingerprint;
    std::string row_family_inventory;
    std::string callback_row_inventory;
    std::string variable_domain_inventory;
    std::string production_option_manifest_sha256;
    std::string algorithm_arm;
    std::string flow_variant;

    bool objective_is_g_plus_lambda_p = false;
    bool station_inventory_and_capacity_complete = false;
    bool pickup_drop_and_vehicle_load_complete = false;
    bool route_degree_and_vehicle_use_complete = false;
    bool station_disjointness_complete = false;
    bool duration_and_operation_time_complete = false;
    bool gini_linearization_complete = false;
    bool improving_gini_range_complete = false;
    bool migrated_static_row_families_complete = false;
    bool selected_flow_rows_complete = false;
    bool callback_interval_rows_complete = false;
    bool variable_domains_complete = false;
    bool no_auxiliary_objective_terms = false;
    bool no_restricted_routes_or_incomplete_fallback = false;
    bool no_instance_dependent_option_resolution = false;
    bool production_options_match_manifest = false;
    bool one_model_lifecycle_design = false;
};

struct ModelCorrectnessDecision {
    bool verified = false;
    std::string gate_version = kRound22ModelCorrectnessGateVersion;
    std::string audit_fingerprint;
    std::string failure_reason = "not_evaluated";
    std::vector<std::string> failed_checks;
};

bool isLowerHexSha256(const std::string& value);
bool isGitCommitId(const std::string& value);
ModelCorrectnessDecision evaluateModelCorrectness(
    const ModelCorrectnessInput& input);

} // namespace ebrp
