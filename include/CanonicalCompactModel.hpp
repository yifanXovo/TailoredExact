#pragma once

#include "Instance.hpp"
#include "Result.hpp"
#include "GiniFrontierGeometry.hpp"
#include "GiniEnvelopeRefinement.hpp"

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
    // Round 50 C1: omit only a second copy of an already-emitted core row
    // when a zero transfer bound makes the visit and mode links identical.
    // Default false preserves every historical model byte-for-byte.
    bool exact_duplicate_row_elimination = false;
    // Round 50 S1 default-off exact vehicle-label representative rule.
    // "v0-cardinality" preserves the historical rule; "route-start-order"
    // sorts identical-vehicle route labels by depot-start station index.
    std::string round50_symmetry_policy = "v0-cardinality";
    // Round 51 M1. Only "tight-tsp-lower-bound" changes the exhaustive
    // Historical exhaustive V<=12 rows plus Round 52 rank-2/rank-3 static
    // ablations. The historical default remains byte-preserving.
    std::string round51_subset_duration_big_m = "historical-100000";
    std::string static_model_identity;
    // Valid affine lower bounds h(G)=alpha+beta*G whose source interval
    // contains this model's interval.  The writer emits h(G) <= objective.
    std::vector<GiniEnvelopeFacet> objective_gini_envelope_facets;
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
    bool exact_duplicate_row_elimination = false;
    long long exact_duplicate_rows_omitted = 0;
    std::string round50_symmetry_policy = "v0-cardinality";
    long long round50_symmetry_rows = 0;
    std::string round51_subset_duration_big_m = "historical-100000";
    long long round51_subset_duration_rows = 0;
    long long round51_subset_duration_first_row_id = -1;
    long long round51_subset_duration_last_row_id = -1;
    double round51_subset_duration_min_m = 0.0;
    double round51_subset_duration_max_m = 0.0;
    bool round51_historical_m_may_be_unsafe = false;
    long long objective_gini_envelope_rows = 0;
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
