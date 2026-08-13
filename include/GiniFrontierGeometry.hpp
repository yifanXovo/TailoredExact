#pragma once

#include <string>
#include <vector>

namespace ebrp {

struct GiniIntervalGeometry {
    double lower = 0.0;
    double upper = 0.0;
};

// Solver-neutral input to the Round 37 exploratory pilot.  The policy may
// inspect only complete initial-cell LP bounds and the frozen Gini geometry.
// Runtime, node counts, instance metadata, scenario labels, and historical
// outcomes are intentionally absent.
struct PilotGiniCellAssessment {
    std::string leaf_id;
    GiniIntervalGeometry interval;
    bool structurally_open = false;
    bool lp_complete = false;
    bool lp_optimal = false;
    bool lp_bound_available = false;
    double lp_lower_bound = 0.0;
    double verified_cutoff = 0.0;
};

struct PilotWeakestGiniCellSelection {
    bool valid = false;
    std::string leaf_id;
    GiniIntervalGeometry interval;
    double lp_lower_bound = 0.0;
    int eligible_cell_count = 0;
    std::string reason = "not_evaluated";
};

// Select the weakest proof-relevant initial cell by complete valid LP bound.
// Bounds equal within tolerance are ordered structurally by lower endpoint,
// upper endpoint, then leaf id.
PilotWeakestGiniCellSelection selectPilotWeakestGiniCell(
    const std::vector<PilotGiniCellAssessment>& cells,
    double tolerance);

// Round 38 solver-neutral global-frontier pilot.  It accepts only a unique
// controlling complete initial LP cell with an available next strict frontier.
// The input deliberately contains no clock, effort, instance, or outcome data.
struct PilotGlobalFrontierSelection {
    bool valid = false;
    bool unique_controlling_cell = false;
    bool next_strict_frontier_available = false;
    std::string leaf_id;
    GiniIntervalGeometry interval;
    double controlling_lower_bound = 0.0;
    double next_strict_frontier = 0.0;
    int eligible_cell_count = 0;
    int frontier_plateau_size = 0;
    std::vector<double> sorted_open_bounds;
    std::string reason = "not_evaluated";
};

PilotGlobalFrontierSelection selectPilotGlobalFrontierCell(
    const std::vector<PilotGiniCellAssessment>& cells,
    double tolerance);

struct PilotFrontierChildBound {
    bool terminal_valid = false;
    bool optimal = false;
    bool infeasible = false;
    bool bound_available = false;
    double lower_bound = 0.0;
};

struct PilotGlobalFrontierLiftDecision {
    bool valid = false;
    bool split_immediately = false;
    bool completes_next_strict_frontier = false;
    double b_plus = 0.0;
    double delta_local = 0.0;
    double hypothetical_global_bound = 0.0;
    double delta_global = 0.0;
    double frontier_completion = 0.0;
    std::vector<double> hypothetical_sorted_open_bounds;
    std::string reason = "not_evaluated";
};

PilotGlobalFrontierLiftDecision evaluatePilotGlobalFrontierLift(
    const PilotGlobalFrontierSelection& selection,
    const PilotFrontierChildBound& left,
    const PilotFrontierChildBound& right,
    double tolerance);

// A launch-frozen anchor grid and its intersection with the proof-relevant
// Gini range.  Anchor cells are geometry only: proof cutoffs and certificates
// continue to use an independently verified proof incumbent.
struct AnchorGridDecomposition {
    bool valid = false;
    double proof_lower = 0.0;
    double proof_upper = 0.0;
    double anchor_grid_upper = 0.0;
    std::vector<double> anchor_endpoints;
    std::vector<GiniIntervalGeometry> anchor_cells;
    std::vector<GiniIntervalGeometry> active_intervals;
    std::vector<int> active_anchor_cell_indices;
    int truncated_active_interval_count = 0;
    std::string reason = "not_evaluated";
};

AnchorGridDecomposition makeProofRelevantAnchorGrid(
    double proof_lower,
    double proof_upper,
    double anchor_grid_upper,
    int interval_count,
    double tolerance);

// The Round 36 startup pair freezes a proof incumbent and a (possibly wider)
// decomposition anchor.  A subsequently verified, stronger proof incumbent is
// safe: it only shrinks the proof-relevant range covered by the frozen anchor.
bool round36ProofAnchorLaunchContractValid(
    bool startup_pair_verified,
    double recorded_startup_proof,
    double current_verified_proof,
    double decomposition_anchor,
    double tolerance);

enum class CplexReplicaSplitPhase {
    InitialPartition,
    AdaptiveRefinement,
    Terminal
};

std::string cplexReplicaSplitPhaseName(CplexReplicaSplitPhase phase);

// Solver-neutral statement of the accepted S0/F0 structural Gini rule.  The
// decision depends only on the root geometry and structural depth; LP values,
// solver effort, elapsed time, attempts, and instance metadata are absent by
// construction.
struct CplexReplicaStructuralSplit {
    bool eligible = false;
    CplexReplicaSplitPhase phase = CplexReplicaSplitPhase::Terminal;
    double split_point = 0.0;
    int initial_partition_depth = 0;
    int adaptive_depth = 0;
    std::string reason = "not_evaluated";
};

CplexReplicaStructuralSplit evaluateCplexReplicaStructuralSplit(
    double root_lower,
    double root_upper,
    double leaf_lower,
    double leaf_upper,
    int gini_depth,
    int initial_interval_count,
    int adaptive_max_depth,
    double adaptive_min_width,
    int split_factor);

std::vector<GiniIntervalGeometry> makeLegacyFrontierIntervals(
    double lower,
    double upper,
    int interval_count);

bool legacyAdaptiveSplitEligible(double lower,
                                 double upper,
                                 int depth,
                                 int max_depth,
                                 double min_width);

std::vector<GiniIntervalGeometry> splitLegacyFrontierInterval(
    double lower,
    double upper,
    int split_factor);

bool exactIntervalCoverage(const GiniIntervalGeometry& parent,
                           const std::vector<GiniIntervalGeometry>& children,
                           double tolerance,
                           std::string* reason = nullptr);

// CPLEX may tighten a node's local G bounds after valid cuts are installed.
// Such a contraction preserves every row inherited from the wider interval;
// an expansion does not and must therefore fail closed.
bool validNestedIntervalContraction(
    const GiniIntervalGeometry& inherited,
    const GiniIntervalGeometry& observed,
    double tolerance,
    std::string* reason = nullptr);

} // namespace ebrp
