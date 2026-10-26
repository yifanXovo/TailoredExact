#pragma once

#include "Round50IntervalMip.hpp"

#include <string>
#include <utility>
#include <vector>

namespace ebrp {

constexpr double kRound51SubsetDurationTolerance = 1e-9;

struct Round51SubsetDurationRowValues {
    double tsp_bound = 0.0;
    double big_m = 0.0;
    double visit_coefficient = 0.0;
    double rhs = 0.0;
};

// Validates the analytic subset-tour lower bound and returns
// M_S=max(0,tsp[S]). Values below -tolerance and all nonfinite values fail
// closed; a tiny negative roundoff value is mapped to zero.
double round51SubsetDurationBigM(
    double tsp_bound,
    double tolerance = kRound51SubsetDurationTolerance);

// Constructs both Big-M-dependent parts of
//   c sum p_i + M_S sum z_i <= T - tsp[S] + M_S |S|.
// Keeping the coefficient and RHS construction together makes the emitted
// row auditable against the validity proof.
Round51SubsetDurationRowValues round51SubsetDurationRowValues(
    double tsp_bound,
    double total_time_limit,
    int subset_cardinality,
    double tolerance = kRound51SubsetDurationTolerance);

struct Round51RootVariable {
    std::string name;
    char original_type = 'C';
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double root_value = 0.0;
};

struct Round51AdaptiveCandidate {
    std::string name;
    Round50VariableFamily family = Round50VariableFamily::Auxiliary;
    char original_type = 'C';
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double root_value = 0.0;
    double fractionality = 0.0;
    double down_upper_bound = 0.0;
    double up_lower_bound = 0.0;
    int pool_order = -1;
};

enum class Round51ProbeStatus { Optimal, Infeasible, Invalid };

struct Round51ProbeDirection {
    Round51ProbeStatus status = Round51ProbeStatus::Invalid;
    double child_objective = 0.0;
};

struct Round51ScoredCandidate {
    Round51AdaptiveCandidate candidate;
    Round51ProbeDirection down;
    Round51ProbeDirection up;
    bool valid = false;
    double delta_down = 0.0;
    double delta_up = 0.0;
    double score = 0.0;
};

struct Round51PrioritySelection {
    bool fallback_to_default = true;
    std::string fallback_reason = "not_evaluated";
    std::vector<Round51ScoredCandidate> ranked_valid_candidates;
    std::vector<std::pair<std::string, int>> priorities;
};

double round51Fractionality(double value);
std::vector<Round51AdaptiveCandidate> round51AdaptiveCandidatePool(
    const std::vector<Round51RootVariable>& variables,
    double integrality_tolerance = 1e-6);
Round51ScoredCandidate round51ScoreAdaptiveCandidate(
    const Round51AdaptiveCandidate& candidate,
    const Round51ProbeDirection& down,
    const Round51ProbeDirection& up,
    double root_objective,
    double verified_cutoff);
Round51PrioritySelection round51SelectSparsePriorities(
    std::vector<Round51ScoredCandidate> scored,
    double improvement_tolerance = 1e-12);
// The sole Round 51 adaptive revision: retain the identical pool, probes,
// ranking, validity, and fallback rules, but prioritize only the best
// already-probed candidate at tier 1.
Round51PrioritySelection round51SelectTopOnePriority(
    std::vector<Round51ScoredCandidate> scored,
    double improvement_tolerance = 1e-12);
std::string round51ProbeStatusName(Round51ProbeStatus status);
double round51AdaptiveTotal(double root_value,
                            const std::vector<double>& probe_values,
                            double terminal_value);

} // namespace ebrp
