#pragma once

#include "GiniFrontierGeometry.hpp"
#include "IntervalRowFactory.hpp"

#include <set>
#include <string>
#include <vector>

namespace ebrp {

struct Round41StaticK2Geometry {
    bool valid = false;
    double proof_lower = 0.0;
    double proof_upper = 0.0;
    double midpoint = 0.0;
    std::vector<GiniIntervalGeometry> segments;
    std::string reason = "not_evaluated";
};

Round41StaticK2Geometry makeRound41StaticK2Geometry(
    double proof_lower,
    double proof_upper,
    double tolerance);

// Solver-neutral description of one static segmented proof block.  The
// ordered row-factory results are materialized before a backend reads the
// canonical model, so no solver callback participates in segment creation.
struct StaticSegmentedBlockSpec {
    bool valid = false;
    GiniIntervalGeometry union_interval;
    std::vector<GiniIntervalGeometry> segments;
    std::vector<IntervalRowFactoryResult> segment_rows;
    std::vector<bool> segment_feasible;
    double verified_incumbent = 0.0;
    double incumbent_epsilon = 0.0;
    std::string formulation_mode = "st-k2-p-core";
    bool common_row_factoring = false;
    bool hierarchical_selectors = false;
    std::string deterministic_model_identity;
    std::string reason = "not_evaluated";
};

StaticSegmentedBlockSpec makeStaticSegmentedBlockSpec(
    const Instance& instance,
    const SolveOptions& options,
    const GiniIntervalGeometry& union_interval,
    const std::vector<GiniIntervalGeometry>& segments,
    double verified_incumbent,
    double incumbent_epsilon,
    const std::string& formulation_mode,
    bool common_row_factoring,
    bool hierarchical_selectors,
    double tolerance);

std::vector<GiniIntervalGeometry> makeEqualStaticSegments(
    double proof_lower,
    double proof_upper,
    int segment_count,
    double tolerance,
    std::string* reason = nullptr);

struct StaticSelectorWeightedRow {
    CanonicalLinearRow prototype;
    std::vector<double> rhs_by_segment;
};

struct StaticCommonRowFactoringPlan {
    bool valid = false;
    std::vector<CanonicalLinearRow> unconditional_rows;
    std::vector<StaticSelectorWeightedRow> selector_weighted_rows;
    std::vector<std::vector<CanonicalLinearRow>> residual_rows;
    long long input_rows = 0;
    long long unconditional_rows_written = 0;
    long long selector_weighted_rows_written = 0;
    long long indicator_rows_retained = 0;
    long long indicator_rows_removed = 0;
    std::string reason = "not_evaluated";
};

// Factor only row patterns that occur exactly once in every segment.  Equal
// rows become one unconditional row; a shared LHS/sense with segment-varying
// RHS becomes one exact selector-weighted linear row.  All other rows remain
// conditional, so this transformation is exact at integral one-hot selectors.
StaticCommonRowFactoringPlan makeStaticCommonRowFactoringPlan(
    const std::vector<IntervalRowFactoryResult>& segment_rows,
    const std::set<std::string>& excluded_families = {});

bool staticSelectorBlockValid(
    const std::vector<double>& selectors,
    const std::vector<bool>& segment_feasible,
    const std::vector<double>& hierarchical_halves,
    double tolerance,
    std::string* reason = nullptr);

// Returns whether (z, b, G, Gk, w, q) satisfies the complete linear
// perspective block used for one segment and q = G*b at integral z,b.
bool round41PerspectiveProductBlockValid(
    double segment_lower,
    double segment_upper,
    double selector,
    double bit,
    double global_g,
    double segment_g,
    double activation,
    double product,
    double tolerance,
    std::string* reason = nullptr);

// Safe scalar binary-product block y = z*x for x in [global_lower,
// global_upper], with selected-domain tightening y in
// [selected_lower*z,selected_upper*z].
bool round41SelectedContinuousBlockValid(
    double global_lower,
    double global_upper,
    double selected_lower,
    double selected_upper,
    double selector,
    double original,
    double selected,
    double tolerance,
    std::string* reason = nullptr);

} // namespace ebrp
