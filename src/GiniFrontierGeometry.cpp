#include "GiniFrontierGeometry.hpp"

#include <algorithm>
#include <cmath>

namespace ebrp {

std::string cplexReplicaSplitPhaseName(CplexReplicaSplitPhase phase) {
    switch (phase) {
    case CplexReplicaSplitPhase::InitialPartition:
        return "initial_partition";
    case CplexReplicaSplitPhase::AdaptiveRefinement:
        return "adaptive_refinement";
    case CplexReplicaSplitPhase::Terminal:
        return "terminal";
    }
    return "terminal";
}

std::vector<GiniIntervalGeometry> makeLegacyFrontierIntervals(
    double lower,
    double upper,
    int interval_count) {
    const int count = std::max(1, interval_count);
    std::vector<GiniIntervalGeometry> intervals;
    intervals.reserve(static_cast<std::size_t>(count));
    for (int index = 0; index < count; ++index) {
        const double frac0 = static_cast<double>(index) / count;
        const double frac1 = static_cast<double>(index + 1) / count;
        intervals.push_back({
            lower + (upper - lower) * frac0,
            index + 1 == count ? upper : lower + (upper - lower) * frac1
        });
    }
    return intervals;
}

AnchorGridDecomposition makeProofRelevantAnchorGrid(
    double proof_lower,
    double proof_upper,
    double anchor_grid_upper,
    int interval_count,
    double tolerance) {
    AnchorGridDecomposition result;
    result.proof_lower = proof_lower;
    result.proof_upper = proof_upper;
    result.anchor_grid_upper = anchor_grid_upper;
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(proof_lower) || !std::isfinite(proof_upper) ||
        !std::isfinite(anchor_grid_upper) || interval_count < 1 ||
        proof_lower < -tol || proof_upper < proof_lower - tol ||
        anchor_grid_upper < -tol) {
        result.reason = "invalid_anchor_grid_inputs";
        return result;
    }
    if (anchor_grid_upper + tol < proof_upper) {
        result.reason = "unsafe_anchor_grid_does_not_cover_proof_range";
        return result;
    }

    result.anchor_cells = makeLegacyFrontierIntervals(
        0.0, anchor_grid_upper, interval_count);
    result.anchor_endpoints.reserve(
        static_cast<std::size_t>(interval_count + 1));
    result.anchor_endpoints.push_back(0.0);
    for (const GiniIntervalGeometry& cell : result.anchor_cells) {
        result.anchor_endpoints.push_back(cell.upper);
    }
    for (std::size_t index = 0; index < result.anchor_cells.size(); ++index) {
        const GiniIntervalGeometry& cell = result.anchor_cells[index];
        const GiniIntervalGeometry active{
            std::max(cell.lower, proof_lower),
            std::min(cell.upper, proof_upper)
        };
        if (active.upper <= active.lower + tol) continue;
        result.active_intervals.push_back(active);
        result.active_anchor_cell_indices.push_back(static_cast<int>(index));
        if (std::fabs(active.lower - cell.lower) > tol ||
            std::fabs(active.upper - cell.upper) > tol) {
            ++result.truncated_active_interval_count;
        }
    }
    if (result.active_intervals.empty()) {
        result.reason = proof_upper <= proof_lower + tol
            ? "empty_proof_range"
            : "anchor_intersection_produced_no_active_intervals";
        return result;
    }
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            {proof_lower, proof_upper}, result.active_intervals, tol,
            &coverage_reason)) {
        result.reason = "active_anchor_intersection_coverage_failed:" +
            coverage_reason;
        return result;
    }
    result.valid = true;
    result.reason = "safe_exact_proof_relevant_anchor_grid";
    return result;
}

bool legacyAdaptiveSplitEligible(double lower,
                                 double upper,
                                 int depth,
                                 int max_depth,
                                 double min_width) {
    return depth < std::max(0, max_depth) &&
           upper - lower > min_width + 1e-12;
}

CplexReplicaStructuralSplit evaluateCplexReplicaStructuralSplit(
    double root_lower,
    double root_upper,
    double leaf_lower,
    double leaf_upper,
    int gini_depth,
    int initial_interval_count,
    int adaptive_max_depth,
    double adaptive_min_width,
    int split_factor) {
    CplexReplicaStructuralSplit decision;
    if (!std::isfinite(root_lower) || !std::isfinite(root_upper) ||
        !std::isfinite(leaf_lower) || !std::isfinite(leaf_upper) ||
        root_upper < root_lower - 1e-12 ||
        leaf_upper < leaf_lower - 1e-12 ||
        leaf_lower < root_lower - 1e-10 ||
        leaf_upper > root_upper + 1e-10 || gini_depth < 0) {
        decision.reason = "invalid_structural_geometry";
        return decision;
    }
    const int initial_count = std::max(1, initial_interval_count);
    const std::vector<GiniIntervalGeometry> initial =
        makeLegacyFrontierIntervals(root_lower, root_upper, initial_count);
    std::vector<double> interior;
    for (std::size_t index = 0; index + 1 < initial.size(); ++index) {
        const double breakpoint = initial[index].upper;
        if (breakpoint > leaf_lower + 1e-10 &&
            breakpoint < leaf_upper - 1e-10) {
            interior.push_back(breakpoint);
        }
    }
    int initial_depth = 0;
    for (int leaves = 1; leaves < initial_count; leaves *= 2) {
        ++initial_depth;
    }
    decision.initial_partition_depth = initial_depth;
    decision.adaptive_depth = std::max(0, gini_depth - initial_depth);
    if (!interior.empty()) {
        decision.eligible = true;
        decision.phase = CplexReplicaSplitPhase::InitialPartition;
        decision.split_point = interior[interior.size() / 2];
        decision.reason = "accepted_initial_partition_breakpoint";
        return decision;
    }
    if (split_factor != 2) {
        decision.reason = "accepted_contract_requires_binary_split_factor";
        return decision;
    }
    if (!legacyAdaptiveSplitEligible(
            leaf_lower, leaf_upper, decision.adaptive_depth,
            adaptive_max_depth, adaptive_min_width)) {
        decision.reason = decision.adaptive_depth >=
                std::max(0, adaptive_max_depth)
            ? "terminal_max_adaptive_depth"
            : "terminal_minimum_interval_width";
        return decision;
    }
    const std::vector<GiniIntervalGeometry> children =
        splitLegacyFrontierInterval(leaf_lower, leaf_upper, split_factor);
    if (children.size() != 2 ||
        children.front().upper <= leaf_lower + 1e-12 ||
        children.front().upper >= leaf_upper - 1e-12) {
        decision.reason = "invalid_binary_split_geometry";
        return decision;
    }
    decision.eligible = true;
    decision.phase = CplexReplicaSplitPhase::AdaptiveRefinement;
    decision.split_point = children.front().upper;
    decision.reason = "accepted_unconditional_adaptive_midpoint";
    return decision;
}

std::vector<GiniIntervalGeometry> splitLegacyFrontierInterval(
    double lower,
    double upper,
    int split_factor) {
    return makeLegacyFrontierIntervals(lower, upper, std::max(2, split_factor));
}

bool exactIntervalCoverage(const GiniIntervalGeometry& parent,
                           const std::vector<GiniIntervalGeometry>& children,
                           double tolerance,
                           std::string* reason) {
    if (children.empty()) {
        if (reason) *reason = "no_children";
        return false;
    }
    const double tol = std::max(0.0, tolerance);
    if (std::fabs(children.front().lower - parent.lower) > tol) {
        if (reason) *reason = "first_child_lower_mismatch";
        return false;
    }
    if (std::fabs(children.back().upper - parent.upper) > tol) {
        if (reason) *reason = "last_child_upper_mismatch";
        return false;
    }
    for (std::size_t index = 0; index < children.size(); ++index) {
        if (children[index].upper < children[index].lower - tol) {
            if (reason) *reason = "negative_child_width";
            return false;
        }
        if (index > 0 && std::fabs(children[index - 1].upper -
                                  children[index].lower) > tol) {
            if (reason) *reason = "child_boundary_gap_or_overlap_mismatch";
            return false;
        }
    }
    if (reason) *reason = "exact_coverage";
    return true;
}

bool validNestedIntervalContraction(
    const GiniIntervalGeometry& inherited,
    const GiniIntervalGeometry& observed,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(inherited.lower) || !std::isfinite(inherited.upper) ||
        !std::isfinite(observed.lower) || !std::isfinite(observed.upper)) {
        if (reason) *reason = "nonfinite_interval_endpoint";
        return false;
    }
    if (inherited.upper < inherited.lower - tol ||
        observed.upper < observed.lower - tol) {
        if (reason) *reason = "negative_interval_width";
        return false;
    }
    if (observed.lower < inherited.lower - tol) {
        if (reason) *reason = "observed_lower_expands_inherited_interval";
        return false;
    }
    if (observed.upper > inherited.upper + tol) {
        if (reason) *reason = "observed_upper_expands_inherited_interval";
        return false;
    }
    if (reason) *reason = "valid_nested_interval_contraction";
    return true;
}

} // namespace ebrp
