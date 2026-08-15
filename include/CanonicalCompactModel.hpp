#pragma once

#include "Instance.hpp"
#include "Result.hpp"
#include "GiniFrontierGeometry.hpp"

#include <filesystem>
#include <string>
#include <unordered_map>

namespace ebrp {

// Solver-neutral request for the one deterministic compact-model writer.
// Both CPLEX and Gurobi consume the artifact produced by this request; no
// backend owns an independent mathematical model definition.
struct CanonicalCompactModelSpec {
    bool strengthened = false;
    bool interval_restricted = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    bool add_verified_incumbent_row = false;
    double verified_incumbent = 0.0;
    double incumbent_epsilon = 0.0;
    // Round 41 default-off static single-tree segmentation. Supported values
    // are off, st-k2-i, st-k2-p-core, and st-k2-p-extended. All segment
    // variables and rows are written deterministically before optimize.
    std::string static_segmented_gini = "off";
    // Empty preserves the historical Round 41 equal-midpoint K2 geometry.
    // Nonempty is an explicit ordered gap-free cover of [gamma_L,gamma_U].
    std::vector<GiniIntervalGeometry> static_segments;
    bool static_common_row_factoring = false;
    bool static_hierarchical_selectors = false;
    std::string static_model_identity;
};

struct CanonicalCompactModelArtifact {
    bool written = false;
    std::filesystem::path path;
    std::string sha256;
    std::string row_signature;
    long long rows = 0;
    long long columns = 0;
    long long nonzeros = 0;
    bool strengthened = false;
    bool interval_restricted = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    bool verified_incumbent_row = false;
    std::string static_segmented_gini = "off";
    long long static_segment_count = 0;
    long long static_selector_variables = 0;
    long long static_perspective_variables = 0;
    long long static_extended_variables = 0;
    long long static_indicator_rows = 0;
    long long static_linear_rows = 0;
    long long static_factored_unconditional_rows = 0;
    long long static_factored_weighted_rhs_rows = 0;
    long long static_factored_indicator_rows_removed = 0;
    long long static_hierarchical_selector_variables = 0;
    std::string static_family_encoding;
    std::string objective_definition =
        "min_G_plus_lambda_weighted_absolute_satisfaction_deviation";
    std::string model_scope = "complete_original_compact_milp";
    std::string failure_reason;
};

CanonicalCompactModelArtifact writeCanonicalCompactModel(
    const Instance& instance,
    const SolveOptions& options,
    const std::filesystem::path& path,
    const CanonicalCompactModelSpec& spec);

std::vector<RoutePlan> reconstructCanonicalCompactRoutes(
    const Instance& instance,
    const std::unordered_map<std::string, double>& named_values);

} // namespace ebrp
