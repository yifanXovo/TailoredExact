#pragma once

#include <string>
#include <vector>

namespace ebrp {

struct GiniIntervalGeometry {
    double lower = 0.0;
    double upper = 0.0;
};

// Round 40 coarse-start policies alter only the initial exact cover and
// whether the existing complete-child refinement logic may run. They do not
// inspect instance metadata, solver effort, time, or historical outcomes.
struct Round40CoarseStartGeometry {
    bool valid = false;
    bool adaptive_refinement = false;
    std::vector<GiniIntervalGeometry> initial_intervals;
    std::string reason = "not_evaluated";
};

Round40CoarseStartGeometry makeRound40CoarseStartGeometry(
    double proof_lower,
    double proof_upper,
    int frozen_initial_interval_count,
    const std::string& policy,
    double tolerance);

// Round 40 incumbent-stable geometry. The full hierarchy is rooted at the
// problem-derived mathematical Gini maximum. A proof incumbent activates
// only the intersecting prefix and may truncate its last cell. The selected
// level is the finest dyadic level with at most the frozen target number of
// active cells. Thus a stronger incumbent either preserves the level or moves
// to a nested refinement; it never slides an internal boundary.
struct Round40NestedDyadicGeometry {
    bool valid = false;
    double proof_lower = 0.0;
    double proof_upper = 0.0;
    double stable_root_upper = 0.0;
    int dyadic_level = 0;
    long long global_cell_count = 1;
    std::vector<GiniIntervalGeometry> active_anchor_cells;
    std::vector<GiniIntervalGeometry> active_intervals;
    std::vector<long long> active_global_cell_indices;
    int truncated_active_interval_count = 0;
    std::string reason = "not_evaluated";
};

Round40NestedDyadicGeometry makeRound40NestedDyadicGeometry(
    double proof_lower,
    double proof_upper,
    double stable_root_upper,
    int target_active_interval_count,
    double tolerance);

// Checks the policy's promised stability relation for two verified cutoffs
// on the same root: every weaker-UB internal boundary still relevant below
// the stronger cutoff must occur in the stronger geometry.
bool round40NestedBoundaryPreservation(
    const Round40NestedDyadicGeometry& weaker,
    const Round40NestedDyadicGeometry& stronger,
    double tolerance,
    std::string* reason = nullptr);

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
