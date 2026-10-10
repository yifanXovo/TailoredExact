#include "Branching.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace ebrp {

RyanFosterBranchCandidate findRyanFosterBranchCandidate(
    int station_count,
    const std::vector<RouteLoadColumn>& columns,
    const std::vector<double>& z_values,
    double tolerance) {
    if (columns.size() != z_values.size()) {
        throw std::runtime_error("Ryan-Foster branching received mismatched columns/z vectors");
    }

    RyanFosterBranchCandidate best;
    for (int i = 1; i <= station_count; ++i) {
        for (int j = i + 1; j <= station_count; ++j) {
            const int bit_i = 1 << (i - 1);
            const int bit_j = 1 << (j - 1);
            double together = 0.0;
            std::vector<int> together_columns;
            for (int c = 0; c < static_cast<int>(columns.size()); ++c) {
                if ((columns[c].mask & bit_i) && (columns[c].mask & bit_j)) {
                    together += z_values[c];
                    together_columns.push_back(c);
                }
            }
            if (together <= tolerance || together >= 1.0 - tolerance) continue;
            const double score = std::min(together, 1.0 - together);
            if (!best.found ||
                score > best.fractional_score + 1e-12 ||
                (std::fabs(score - best.fractional_score) <= 1e-12 &&
                 together_columns.size() > best.together_column_indices.size())) {
                best.found = true;
                best.station_i = i;
                best.station_j = j;
                best.together_value = together;
                best.fractional_score = score;
                best.together_column_indices = std::move(together_columns);
            }
        }
    }
    return best;
}

} // namespace ebrp
