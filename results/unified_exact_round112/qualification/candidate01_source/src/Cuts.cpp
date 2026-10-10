#include "Cuts.hpp"

#include <algorithm>
#include <functional>
#include <stdexcept>

namespace ebrp {
namespace {

int subsetRowCoefficient(int mask, const std::vector<int>& stations) {
    int count = 0;
    for (int station : stations) {
        if (mask & (1 << (station - 1))) ++count;
    }
    return count / 2;
}

void generateCombinations(int station_count,
                          int target_size,
                          int next_station,
                          std::vector<int>& current,
                          const std::function<void(const std::vector<int>&)>& visit) {
    if (static_cast<int>(current.size()) == target_size) {
        visit(current);
        return;
    }
    for (int station = next_station; station <= station_count; ++station) {
        if (static_cast<int>(current.size()) + (station_count - station + 1) < target_size) break;
        current.push_back(station);
        generateCombinations(station_count, target_size, station + 1, current, visit);
        current.pop_back();
    }
}

} // namespace

std::vector<ThreeSubsetRowCut> separateThreeSubsetRowCuts(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance,
    int max_cuts) {
    if (columns.size() != z_values.size()) {
        throw std::runtime_error("3-subset-row separator received mismatched columns/z vectors");
    }

    std::vector<ThreeSubsetRowCut> cuts;
    for (int a = 1; a <= station_count; ++a) {
        for (int b = a + 1; b <= station_count; ++b) {
            for (int c = b + 1; c <= station_count; ++c) {
                ThreeSubsetRowCut cut;
                cut.stations = {a, b, c};
                for (int idx = 0; idx < static_cast<int>(columns.size()); ++idx) {
                    const int mask = columns[idx].mask;
                    int count = 0;
                    if (mask & (1 << (a - 1))) ++count;
                    if (mask & (1 << (b - 1))) ++count;
                    if (mask & (1 << (c - 1))) ++count;
                    const int coefficient = count / 2;
                    if (coefficient > 0) {
                        cut.lhs += coefficient * z_values[idx];
                        cut.column_indices.push_back(idx);
                    }
                }
                cut.violation = cut.lhs - cut.rhs;
                if (cut.violation > tolerance) cuts.push_back(std::move(cut));
            }
        }
    }

    std::sort(cuts.begin(), cuts.end(), [](const ThreeSubsetRowCut& left,
                                           const ThreeSubsetRowCut& right) {
        return left.violation > right.violation;
    });
    if (max_cuts >= 0 && static_cast<int>(cuts.size()) > max_cuts) {
        cuts.resize(max_cuts);
    }
    return cuts;
}

std::vector<SubsetRowCut> separateSubsetRowCuts(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    const std::vector<int>& odd_subset_sizes,
    double tolerance,
    int max_cuts) {
    if (columns.size() != z_values.size()) {
        throw std::runtime_error("subset-row separator received mismatched columns/z vectors");
    }

    std::vector<SubsetRowCut> cuts;
    std::vector<int> subset;
    for (int requested_size : odd_subset_sizes) {
        if (requested_size < 3 || requested_size > station_count || requested_size % 2 == 0) {
            continue;
        }
        generateCombinations(station_count, requested_size, 1, subset,
            [&](const std::vector<int>& stations) {
                SubsetRowCut cut;
                cut.stations = stations;
                cut.rhs = requested_size / 2;
                for (int idx = 0; idx < static_cast<int>(columns.size()); ++idx) {
                    const int coeff = subsetRowCoefficient(columns[idx].mask, stations);
                    if (coeff > 0) {
                        cut.lhs += static_cast<double>(coeff) * z_values[idx];
                        cut.column_indices.push_back(idx);
                    }
                }
                cut.violation = cut.lhs - static_cast<double>(cut.rhs);
                if (cut.violation > tolerance) cuts.push_back(std::move(cut));
            });
    }

    std::sort(cuts.begin(), cuts.end(), [](const SubsetRowCut& left,
                                           const SubsetRowCut& right) {
        return left.violation > right.violation;
    });
    if (max_cuts >= 0 && static_cast<int>(cuts.size()) > max_cuts) {
        cuts.resize(max_cuts);
    }
    return cuts;
}

} // namespace ebrp
