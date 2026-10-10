#pragma once

#include "Column.hpp"

#include <vector>

namespace ebrp {

struct RyanFosterBranchCandidate {
    bool found = false;
    int station_i = 0;
    int station_j = 0;
    double together_value = 0.0;
    double fractional_score = 0.0;
    std::vector<int> together_column_indices;
};

RyanFosterBranchCandidate findRyanFosterBranchCandidate(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance = 1e-9);

} // namespace ebrp
