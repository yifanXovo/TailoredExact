#include "Round51IntervalMip.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace ebrp {

double round51SubsetDurationBigM(double tsp_bound, double tolerance) {
    if (!std::isfinite(tsp_bound)) {
        throw std::runtime_error(
            "round51_subset_duration_tsp_bound_nonfinite");
    }
    if (!std::isfinite(tolerance) || tolerance < 0.0) {
        throw std::runtime_error(
            "round51_subset_duration_tolerance_invalid");
    }
    if (tsp_bound < -tolerance) {
        throw std::runtime_error(
            "round51_subset_duration_tsp_bound_negative");
    }
    return std::max(0.0, tsp_bound);
}

Round51SubsetDurationRowValues round51SubsetDurationRowValues(
    double tsp_bound,
    double total_time_limit,
    int subset_cardinality,
    double tolerance) {
    if (!std::isfinite(total_time_limit)) {
        throw std::runtime_error(
            "round51_subset_duration_time_limit_nonfinite");
    }
    if (subset_cardinality <= 0) {
        throw std::runtime_error(
            "round51_subset_duration_cardinality_invalid");
    }
    Round51SubsetDurationRowValues out;
    out.tsp_bound = tsp_bound;
    out.big_m = round51SubsetDurationBigM(tsp_bound, tolerance);
    out.visit_coefficient = out.big_m;
    out.rhs = total_time_limit - tsp_bound +
        out.big_m * static_cast<double>(subset_cardinality);
    if (!std::isfinite(out.rhs) ||
        std::fabs(out.visit_coefficient - out.big_m) > tolerance ||
        std::fabs(out.rhs - (total_time_limit - tsp_bound +
            out.big_m * static_cast<double>(subset_cardinality))) >
                tolerance) {
        throw std::runtime_error(
            "round51_subset_duration_row_formula_mismatch");
    }
    return out;
}

} // namespace ebrp
