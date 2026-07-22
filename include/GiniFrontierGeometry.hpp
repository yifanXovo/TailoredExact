#pragma once

#include <string>
#include <vector>

namespace ebrp {

struct GiniIntervalGeometry {
    double lower = 0.0;
    double upper = 0.0;
};

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
