#include "ModelCorrectness.hpp"

#include <cctype>
#include <cstdint>
#include <iomanip>
#include <sstream>

namespace ebrp {
namespace {

std::string fnvFingerprint(const std::string& value) {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char ch : value) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << hash;
    return out.str();
}

bool isLowerHex(const std::string& value, std::size_t minimum,
                std::size_t maximum) {
    if (value.size() < minimum || value.size() > maximum) return false;
    for (unsigned char ch : value) {
        if (!std::isdigit(ch) && !(ch >= 'a' && ch <= 'f')) return false;
    }
    return true;
}

void check(ModelCorrectnessDecision& out, bool condition,
           const char* name) {
    if (!condition) out.failed_checks.emplace_back(name);
}

} // namespace

bool isLowerHexSha256(const std::string& value) {
    return isLowerHex(value, 64, 64);
}

bool isGitCommitId(const std::string& value) {
    return isLowerHex(value, 40, 64);
}

ModelCorrectnessDecision evaluateModelCorrectness(
    const ModelCorrectnessInput& input) {
    ModelCorrectnessDecision out;
    out.gate_version = input.gate_version;

    check(out, input.gate_version == kRound22ModelCorrectnessGateVersion,
          "gate_version");
    check(out, isLowerHexSha256(input.executable_sha256),
          "executable_sha256");
    check(out, isGitCommitId(input.source_commit_sha), "source_commit_sha");
    check(out, !input.model_writer_fingerprint.empty() &&
                   input.model_writer_fingerprint != "unavailable",
          "model_writer_fingerprint");
    check(out, !input.objective_definition_fingerprint.empty() &&
                   input.objective_definition_fingerprint != "unavailable",
          "objective_definition_fingerprint");
    check(out, !input.row_family_inventory.empty(), "row_family_inventory");
    check(out, !input.callback_row_inventory.empty(),
          "callback_row_inventory");
    check(out, !input.variable_domain_inventory.empty(),
          "variable_domain_inventory");
    check(out, isLowerHexSha256(input.production_option_manifest_sha256),
          "production_option_manifest_sha256");
    check(out, !input.algorithm_arm.empty(), "algorithm_arm");
    check(out, !input.flow_variant.empty(), "flow_variant");

    check(out, input.objective_is_g_plus_lambda_p,
          "objective_is_g_plus_lambda_p");
    check(out, input.station_inventory_and_capacity_complete,
          "station_inventory_and_capacity_complete");
    check(out, input.pickup_drop_and_vehicle_load_complete,
          "pickup_drop_and_vehicle_load_complete");
    check(out, input.route_degree_and_vehicle_use_complete,
          "route_degree_and_vehicle_use_complete");
    check(out, input.station_disjointness_complete,
          "station_disjointness_complete");
    check(out, input.duration_and_operation_time_complete,
          "duration_and_operation_time_complete");
    check(out, input.gini_linearization_complete,
          "gini_linearization_complete");
    check(out, input.improving_gini_range_complete,
          "improving_gini_range_complete");
    check(out, input.migrated_static_row_families_complete,
          "migrated_static_row_families_complete");
    check(out, input.selected_flow_rows_complete,
          "selected_flow_rows_complete");
    check(out, input.callback_interval_rows_complete,
          "callback_interval_rows_complete");
    check(out, input.variable_domains_complete,
          "variable_domains_complete");
    check(out, input.no_auxiliary_objective_terms,
          "no_auxiliary_objective_terms");
    check(out, input.no_restricted_routes_or_incomplete_fallback,
          "no_restricted_routes_or_incomplete_fallback");
    check(out, input.no_instance_dependent_option_resolution,
          "no_instance_dependent_option_resolution");
    check(out, input.production_options_match_manifest,
          "production_options_match_manifest");
    check(out, input.one_model_lifecycle_design,
          "one_model_lifecycle_design");

    std::ostringstream canonical;
    canonical << input.gate_version << '|' << input.executable_sha256 << '|'
              << input.source_commit_sha << '|'
              << input.model_writer_fingerprint << '|'
              << input.objective_definition_fingerprint << '|'
              << input.row_family_inventory << '|'
              << input.callback_row_inventory << '|'
              << input.variable_domain_inventory << '|'
              << input.production_option_manifest_sha256 << '|'
              << input.algorithm_arm << '|' << input.flow_variant;
    for (const std::string& failure : out.failed_checks) {
        canonical << "|FAIL:" << failure;
    }
    out.audit_fingerprint = fnvFingerprint(canonical.str());
    out.verified = out.failed_checks.empty();
    if (out.verified) {
        out.failure_reason = "none";
    } else {
        std::ostringstream failures;
        for (std::size_t i = 0; i < out.failed_checks.size(); ++i) {
            if (i) failures << '|';
            failures << out.failed_checks[i];
        }
        out.failure_reason = failures.str();
    }
    return out;
}

} // namespace ebrp
