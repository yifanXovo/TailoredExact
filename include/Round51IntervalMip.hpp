#pragma once

#include <string>

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

} // namespace ebrp
