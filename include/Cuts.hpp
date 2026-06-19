#pragma once

#include "Column.hpp"

#include <array>
#include <vector>

namespace ebrp {

struct ThreeSubsetRowCut {
    std::array<int, 3> stations{};
    double lhs = 0.0;
    double rhs = 1.0;
    double violation = 0.0;
    std::vector<int> column_indices;
};

struct SubsetRowCut {
    std::vector<int> stations;
    int rhs = 0;
    double lhs = 0.0;
    double violation = 0.0;
    std::vector<int> column_indices;
};

std::vector<ThreeSubsetRowCut> separateThreeSubsetRowCuts(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance = 1e-9,
    int max_cuts = 100);

std::vector<SubsetRowCut> separateSubsetRowCuts(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    const std::vector<int>& odd_subset_sizes,
    double tolerance = 1e-9,
    int max_cuts = 100);

} // namespace ebrp
