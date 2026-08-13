#include "GiniFrontierGeometry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

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

namespace {

bool eligiblePilotCell(const PilotGiniCellAssessment& cell, double tolerance) {
    return cell.structurally_open && cell.lp_complete && cell.lp_optimal &&
        cell.lp_bound_available && std::isfinite(cell.interval.lower) &&
        std::isfinite(cell.interval.upper) &&
        std::isfinite(cell.lp_lower_bound) &&
        std::isfinite(cell.verified_cutoff) &&
        cell.interval.upper > cell.interval.lower + tolerance &&
        cell.lp_lower_bound < cell.verified_cutoff - tolerance;
}

bool validPilotChild(const PilotFrontierChildBound& child) {
    return child.terminal_valid &&
        (child.infeasible ||
         (child.optimal && child.bound_available &&
          std::isfinite(child.lower_bound)));
}

double effectivePilotChildBound(const PilotFrontierChildBound& child) {
    return child.infeasible
        ? std::numeric_limits<double>::infinity()
        : child.lower_bound;
}

} // namespace

PilotGlobalFrontierSelection selectPilotGlobalFrontierCell(
    const std::vector<PilotGiniCellAssessment>& cells,
    double tolerance) {
    PilotGlobalFrontierSelection selection;
    const double tol = std::max(0.0, tolerance);
    std::vector<const PilotGiniCellAssessment*> eligible;
    for (const PilotGiniCellAssessment& cell : cells) {
        if (eligiblePilotCell(cell, tol)) eligible.push_back(&cell);
    }
    selection.eligible_cell_count = static_cast<int>(eligible.size());
    if (eligible.empty()) {
        selection.reason = "no_open_complete_optimal_initial_lp_cell";
        return selection;
    }
    std::sort(
        eligible.begin(), eligible.end(),
        [](const PilotGiniCellAssessment* left,
           const PilotGiniCellAssessment* right) {
            if (left->lp_lower_bound != right->lp_lower_bound) {
                return left->lp_lower_bound < right->lp_lower_bound;
            }
            if (left->interval.lower != right->interval.lower) {
                return left->interval.lower < right->interval.lower;
            }
            if (left->interval.upper != right->interval.upper) {
                return left->interval.upper < right->interval.upper;
            }
            return left->leaf_id < right->leaf_id;
        });
    selection.sorted_open_bounds.reserve(eligible.size());
    for (const PilotGiniCellAssessment* cell : eligible) {
        selection.sorted_open_bounds.push_back(cell->lp_lower_bound);
    }
    const PilotGiniCellAssessment& controlling = *eligible.front();
    selection.leaf_id = controlling.leaf_id;
    selection.interval = controlling.interval;
    selection.controlling_lower_bound = controlling.lp_lower_bound;
    selection.frontier_plateau_size = static_cast<int>(std::count_if(
        eligible.begin(), eligible.end(),
        [&](const PilotGiniCellAssessment* cell) {
            return std::fabs(cell->lp_lower_bound -
                             controlling.lp_lower_bound) <= tol;
        }));
    selection.unique_controlling_cell =
        selection.frontier_plateau_size == 1;
    if (!selection.unique_controlling_cell) {
        selection.reason = "minimum_bound_frontier_not_unique";
        return selection;
    }
    for (const PilotGiniCellAssessment* cell : eligible) {
        if (cell->lp_lower_bound >
            controlling.lp_lower_bound + tol) {
            selection.next_strict_frontier = cell->lp_lower_bound;
            selection.next_strict_frontier_available = true;
            break;
        }
    }
    if (!selection.next_strict_frontier_available) {
        selection.reason = "no_next_strict_open_leaf_frontier";
        return selection;
    }
    selection.valid = true;
    selection.reason = "unique_controlling_initial_cell_with_strict_frontier";
    return selection;
}

PilotGlobalFrontierLiftDecision evaluatePilotGlobalFrontierLift(
    const PilotGlobalFrontierSelection& selection,
    const PilotFrontierChildBound& left,
    const PilotFrontierChildBound& right,
    double tolerance) {
    PilotGlobalFrontierLiftDecision decision;
    const double tol = std::max(0.0, tolerance);
    if (!selection.valid || !selection.unique_controlling_cell ||
        !selection.next_strict_frontier_available ||
        !std::isfinite(selection.controlling_lower_bound) ||
        !std::isfinite(selection.next_strict_frontier) ||
        selection.next_strict_frontier <=
            selection.controlling_lower_bound + tol) {
        decision.reason = "invalid_global_frontier_selection";
        return decision;
    }
    if (!validPilotChild(left) || !validPilotChild(right)) {
        decision.reason = "child_lp_not_complete_valid_bound_or_infeasible";
        return decision;
    }
    const double left_bound = effectivePilotChildBound(left);
    const double right_bound = effectivePilotChildBound(right);
    decision.b_plus = std::min(left_bound, right_bound);
    decision.delta_local =
        decision.b_plus - selection.controlling_lower_bound;
    decision.hypothetical_global_bound =
        std::min(decision.b_plus, selection.next_strict_frontier);
    decision.delta_global = decision.hypothetical_global_bound -
        selection.controlling_lower_bound;
    decision.frontier_completion = decision.delta_global;
    decision.completes_next_strict_frontier =
        decision.b_plus + tol >= selection.next_strict_frontier;
    decision.split_immediately =
        decision.completes_next_strict_frontier;
    decision.hypothetical_sorted_open_bounds =
        selection.sorted_open_bounds;
    if (!decision.hypothetical_sorted_open_bounds.empty()) {
        decision.hypothetical_sorted_open_bounds.erase(
            decision.hypothetical_sorted_open_bounds.begin());
    }
    decision.hypothetical_sorted_open_bounds.push_back(left_bound);
    decision.hypothetical_sorted_open_bounds.push_back(right_bound);
    std::sort(decision.hypothetical_sorted_open_bounds.begin(),
              decision.hypothetical_sorted_open_bounds.end());
    decision.valid = true;
    decision.reason = decision.split_immediately
        ? "midpoint_children_complete_next_strict_frontier"
        : "midpoint_children_do_not_complete_next_strict_frontier";
    return decision;
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
