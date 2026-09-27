#include "GiniFrontierGeometry.hpp"

#include <algorithm>
#include <cmath>

namespace ebrp {

PilotWeakestGiniCellSelection selectPilotWeakestGiniCell(
    const std::vector<PilotGiniCellAssessment>& cells,
    double tolerance) {
    PilotWeakestGiniCellSelection selection;
    const double tol = std::max(0.0, tolerance);
    for (const PilotGiniCellAssessment& cell : cells) {
        const bool eligible = cell.structurally_open && cell.lp_complete &&
            cell.lp_optimal && cell.lp_bound_available &&
            std::isfinite(cell.interval.lower) &&
            std::isfinite(cell.interval.upper) &&
            std::isfinite(cell.lp_lower_bound) &&
            std::isfinite(cell.verified_cutoff) &&
            cell.interval.upper > cell.interval.lower + tol &&
            cell.lp_lower_bound < cell.verified_cutoff - tol;
        if (!eligible) continue;
        ++selection.eligible_cell_count;
        const bool weaker = !selection.valid ||
            cell.lp_lower_bound < selection.lp_lower_bound - tol;
        const bool bound_tie = selection.valid &&
            std::fabs(cell.lp_lower_bound - selection.lp_lower_bound) <= tol;
        const bool structural_precedes = bound_tie &&
            (cell.interval.lower < selection.interval.lower - tol ||
             (std::fabs(cell.interval.lower - selection.interval.lower) <= tol &&
              (cell.interval.upper < selection.interval.upper - tol ||
               (std::fabs(cell.interval.upper - selection.interval.upper) <= tol &&
                cell.leaf_id < selection.leaf_id))));
        if (!weaker && !structural_precedes) continue;
        selection.valid = true;
        selection.leaf_id = cell.leaf_id;
        selection.interval = cell.interval;
        selection.lp_lower_bound = cell.lp_lower_bound;
    }
    selection.reason = selection.valid
        ? "weakest_complete_initial_lp_bound_structural_ties"
        : "no_open_complete_optimal_initial_lp_cell";
    return selection;
}

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

Round40CoarseStartGeometry makeRound40CoarseStartGeometry(
    double proof_lower,
    double proof_upper,
    int frozen_initial_interval_count,
    const std::string& policy,
    double tolerance) {
    Round40CoarseStartGeometry result;
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(proof_lower) || !std::isfinite(proof_upper) ||
        proof_lower < -tol || proof_upper < proof_lower - tol ||
        frozen_initial_interval_count < 1) {
        result.reason = "invalid_round40_coarse_start_inputs";
        return result;
    }
    int interval_count = frozen_initial_interval_count;
    if (policy == "off") {
        result.adaptive_refinement = true;
    } else if (policy == "k1-single") {
        interval_count = 1;
        result.adaptive_refinement = false;
    } else if (policy == "k1-adaptive" ||
               policy == "k1-adaptive-decisive") {
        interval_count = 1;
        result.adaptive_refinement = true;
    } else {
        result.reason = "unknown_round40_coarse_start_policy";
        return result;
    }
    result.initial_intervals = makeLegacyFrontierIntervals(
        proof_lower, proof_upper, interval_count);
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            {proof_lower, proof_upper}, result.initial_intervals, tol,
            &coverage_reason)) {
        result.reason = "round40_initial_coverage_failed:" + coverage_reason;
        return result;
    }
    result.valid = true;
    result.reason = policy == "off"
        ? "frozen_k4_exact_cover"
        : (policy == "k1-single"
            ? "single_complete_strict_improver_interval_no_refinement"
            : (policy == "k1-adaptive"
                ? "single_complete_root_with_exact_child_evidence_refinement"
                : "single_complete_root_with_decisive_exact_child_refinement"));
    return result;
}

Round40NestedDyadicGeometry makeRound40NestedDyadicGeometry(
    double proof_lower,
    double proof_upper,
    double stable_root_upper,
    int target_active_interval_count,
    double tolerance) {
    Round40NestedDyadicGeometry result;
    result.proof_lower = proof_lower;
    result.proof_upper = proof_upper;
    result.stable_root_upper = stable_root_upper;
    const double tol = std::max(0.0, tolerance);
    if (!std::isfinite(proof_lower) || !std::isfinite(proof_upper) ||
        !std::isfinite(stable_root_upper) ||
        target_active_interval_count < 1 || proof_lower < -tol ||
        std::fabs(proof_lower) > tol ||
        proof_upper < proof_lower - tol || stable_root_upper <= 0.0 ||
        proof_upper > stable_root_upper + tol) {
        result.reason = "invalid_round40_nested_dyadic_inputs";
        return result;
    }
    if (proof_upper <= proof_lower + tol) {
        result.active_anchor_cells.push_back({proof_lower, proof_upper});
        result.active_intervals.push_back({proof_lower, proof_upper});
        result.active_global_cell_indices.push_back(0);
        result.valid = true;
        result.reason = "empty_proof_range_single_degenerate_cell";
        return result;
    }

    auto activeCount = [&](long long global_count) {
        const double cell_width = stable_root_upper /
            static_cast<double>(global_count);
        long long count = static_cast<long long>(
            std::ceil(proof_upper / cell_width));
        count = std::max(1LL, std::min(global_count, count));
        while (count > 1 &&
               (static_cast<double>(count - 1) * cell_width >=
                proof_upper - tol)) {
            --count;
        }
        while (count < global_count &&
               static_cast<double>(count) * cell_width < proof_upper - tol) {
            ++count;
        }
        return count;
    };

    constexpr int kMaximumExactDyadicLevel = 52;
    while (result.dyadic_level < kMaximumExactDyadicLevel) {
        const long long next_global_count = result.global_cell_count * 2;
        if (activeCount(next_global_count) >
            static_cast<long long>(target_active_interval_count)) {
            break;
        }
        result.global_cell_count = next_global_count;
        ++result.dyadic_level;
    }

    const long long active_count = activeCount(result.global_cell_count);
    result.active_anchor_cells.reserve(
        static_cast<std::size_t>(active_count));
    result.active_intervals.reserve(static_cast<std::size_t>(active_count));
    result.active_global_cell_indices.reserve(
        static_cast<std::size_t>(active_count));
    for (long long index = 0; index < active_count; ++index) {
        const GiniIntervalGeometry anchor{
            stable_root_upper * static_cast<double>(index) /
                static_cast<double>(result.global_cell_count),
            index + 1 == result.global_cell_count
                ? stable_root_upper
                : stable_root_upper * static_cast<double>(index + 1) /
                    static_cast<double>(result.global_cell_count)};
        const GiniIntervalGeometry active{
            std::max(proof_lower, anchor.lower),
            std::min(proof_upper, anchor.upper)};
        if (active.upper < active.lower - tol) {
            result.reason = "round40_nested_dyadic_negative_active_cell";
            return result;
        }
        result.active_anchor_cells.push_back(anchor);
        result.active_intervals.push_back(active);
        result.active_global_cell_indices.push_back(index);
        if (std::fabs(active.lower - anchor.lower) > tol ||
            std::fabs(active.upper - anchor.upper) > tol) {
            ++result.truncated_active_interval_count;
        }
    }
    std::string coverage_reason;
    if (!exactIntervalCoverage(
            {proof_lower, proof_upper}, result.active_intervals, tol,
            &coverage_reason)) {
        result.reason = "round40_nested_dyadic_coverage_failed:" +
            coverage_reason;
        return result;
    }
    result.valid = true;
    result.reason = "stable_root_finest_dyadic_prefix_with_at_most_target_cells";
    return result;
}

bool round40NestedBoundaryPreservation(
    const Round40NestedDyadicGeometry& weaker,
    const Round40NestedDyadicGeometry& stronger,
    double tolerance,
    std::string* reason) {
    const double tol = std::max(0.0, tolerance);
    auto reject = [&](const std::string& why) {
        if (reason) *reason = why;
        return false;
    };
    if (!weaker.valid || !stronger.valid) {
        return reject("invalid_nested_geometry");
    }
    if (std::fabs(weaker.stable_root_upper -
                  stronger.stable_root_upper) > tol) {
        return reject("stable_root_changed");
    }
    if (stronger.proof_upper > weaker.proof_upper + tol) {
        return reject("second_cutoff_is_not_stronger");
    }
    if (stronger.dyadic_level < weaker.dyadic_level) {
        return reject("stronger_cutoff_coarsened_dyadic_level");
    }
    std::vector<double> stronger_endpoints;
    stronger_endpoints.reserve(stronger.active_intervals.size() + 1);
    if (!stronger.active_intervals.empty()) {
        stronger_endpoints.push_back(stronger.active_intervals.front().lower);
        for (const GiniIntervalGeometry& cell : stronger.active_intervals) {
            stronger_endpoints.push_back(cell.upper);
        }
    }
    for (std::size_t index = 0;
         index + 1 < weaker.active_intervals.size(); ++index) {
        const double boundary = weaker.active_intervals[index].upper;
        if (boundary > stronger.proof_upper + tol) continue;
        const bool preserved = std::any_of(
            stronger_endpoints.begin(), stronger_endpoints.end(),
            [&](double endpoint) {
                return std::fabs(endpoint - boundary) <= tol;
            });
        if (!preserved) return reject("relevant_internal_boundary_redrawn");
    }
    if (reason) *reason = "all_relevant_internal_boundaries_preserved";
    return true;
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

bool round36ProofAnchorLaunchContractValid(
    bool startup_pair_verified,
    double recorded_startup_proof,
    double current_verified_proof,
    double decomposition_anchor,
    double tolerance) {
    if (!startup_pair_verified ||
        !std::isfinite(recorded_startup_proof) ||
        !std::isfinite(current_verified_proof) ||
        !std::isfinite(decomposition_anchor) ||
        recorded_startup_proof <= 0.0 || current_verified_proof <= 0.0 ||
        decomposition_anchor <= 0.0) {
        return false;
    }
    const double scaled_tolerance = std::max(0.0, tolerance) * std::max({
        1.0,
        std::fabs(recorded_startup_proof),
        std::fabs(current_verified_proof),
        std::fabs(decomposition_anchor)
    });
    return current_verified_proof <=
               recorded_startup_proof + scaled_tolerance &&
           decomposition_anchor + scaled_tolerance >=
               recorded_startup_proof &&
           decomposition_anchor + scaled_tolerance >=
               current_verified_proof;
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

Round90LpGSplitGeometry selectRound90LpGSplitGeometry(
    double lower,
    double upper,
    bool current_optimal_parent_g_available,
    double parent_g) {
    Round90LpGSplitGeometry choice;
    if (!std::isfinite(lower) || !std::isfinite(upper) || !(lower < upper)) {
        choice.reason = "invalid_parent_interval";
        return choice;
    }
    const auto midpoint_children = splitLegacyFrontierInterval(lower, upper, 2);
    if (midpoint_children.size() == 2)
        choice.midpoint = midpoint_children[0].upper;
    choice.used_parent_g = current_optimal_parent_g_available &&
        std::isfinite(parent_g) && lower < parent_g && parent_g < upper;
    if (!choice.used_parent_g && midpoint_children.size() != 2) {
        choice.reason = "invalid_legacy_midpoint_geometry";
        return choice;
    }
    choice.split_point = choice.used_parent_g ? parent_g : choice.midpoint;
    choice.children = choice.used_parent_g
        ? std::vector<GiniIntervalGeometry>{{lower, choice.split_point},
                                            {choice.split_point, upper}}
        : midpoint_children;
    if (!std::isfinite(choice.split_point) ||
        !(lower < choice.split_point && choice.split_point < upper) ||
        choice.children[0].lower != lower ||
        choice.children[0].upper != choice.split_point ||
        choice.children[1].lower != choice.split_point ||
        choice.children[1].upper != upper) {
        choice.children.clear();
        choice.reason = "malformed_child_geometry";
        return choice;
    }
    choice.valid = true;
    choice.reason = choice.used_parent_g
        ? "current_optimal_parent_g_strict_interior"
        : "legacy_midpoint_fallback";
    return choice;
}

bool validRound90LpGCachedChild(
    const Round90LpGCachedChildIdentity& cached,
    const std::string& expected_id,
    const std::string& expected_parent_id,
    int expected_child_index,
    int expected_split_depth,
    const GiniIntervalGeometry& expected_interval,
    long long current_incumbent_epoch,
    std::string* reason) {
    if (cached.id != expected_id ||
        cached.parent_id != expected_parent_id ||
        cached.child_index != expected_child_index ||
        cached.split_depth != expected_split_depth) {
        if (reason) *reason = "child_tree_identity_mismatch";
        return false;
    }
    const auto same_interval = [&](const GiniIntervalGeometry& interval) {
        return interval.lower == expected_interval.lower &&
               interval.upper == expected_interval.upper;
    };
    if (!std::isfinite(expected_interval.lower) ||
        !std::isfinite(expected_interval.upper) ||
        !(expected_interval.lower < expected_interval.upper) ||
        !same_interval(cached.leaf_interval) ||
        !same_interval(cached.artifact_interval) ||
        !same_interval(cached.lp_interval)) {
        if (reason) *reason = "child_interval_identity_mismatch";
        return false;
    }
    if (!cached.artifact_ready || !cached.artifact_written ||
        !cached.lp_complete || !cached.lp_terminal_valid ||
        !(cached.lp_optimal || cached.lp_infeasible) ||
        cached.artifact_epoch != current_incumbent_epoch ||
        cached.lp_epoch != current_incumbent_epoch) {
        if (reason) *reason = "child_epoch_or_lp_status_mismatch";
        return false;
    }
    if (cached.artifact_sha256.empty() ||
        cached.artifact_sha256 != cached.lp_artifact_sha256 ||
        cached.artifact_sha256 != cached.observed_file_sha256) {
        if (reason) *reason = "child_canonical_sha256_mismatch";
        return false;
    }
    if (reason) *reason = "cached_child_identity_verified";
    return true;
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
