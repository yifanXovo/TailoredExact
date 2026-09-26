#include "NativeOtB1.hpp"

#include <algorithm>
#include <cfenv>
#include <cmath>
#include <cstddef>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#if defined(__SSE__) || defined(_M_X64)
#include <xmmintrin.h>
#endif

namespace ebrp {
namespace {

struct Interval {
    double lower = 0.0;
    double upper = 0.0;
};

double down(double x) {
    return std::nextafter(x, -std::numeric_limits<double>::infinity());
}
double up(double x) {
    return std::nextafter(x, std::numeric_limits<double>::infinity());
}
bool finite(const Interval& x) {
    return std::isfinite(x.lower) && std::isfinite(x.upper);
}
Interval roundedProduct(double a, double b) {
    if (a == 0.0 || b == 0.0) return {};
    const double rounded = a * b;
    return {down(rounded), up(rounded)};
}
Interval roundedDifference(double a, double b) {
    if (a == b) return {};
    const double rounded = a - b;
    return {down(rounded), up(rounded)};
}
Interval add(Interval a, Interval b) {
    if (a.lower == 0.0 && a.upper == 0.0) return b;
    if (b.lower == 0.0 && b.upper == 0.0) return a;
    return {down(a.lower + b.lower), up(a.upper + b.upper)};
}
Interval negate(Interval a) { return {-a.upper, -a.lower}; }
double addUpper(double a, double b) {
    if (a == 0.0) return b;
    if (b == 0.0) return a;
    return up(a + b);
}
double upperDistance(double a, double b) {
    if (a == b) return 0.0;
    return up(std::fabs(a - b));
}
double upperError(double selected, Interval enclosing) {
    return std::max(upperDistance(selected, enclosing.lower),
                    upperDistance(selected, enclosing.upper));
}
bool arithmeticReady() {
    volatile double first = std::numeric_limits<double>::denorm_min();
    volatile double second = std::numeric_limits<double>::denorm_min();
    volatile double sum = first + second;
    const bool runtime_denorm =
        sum == 2.0 * std::numeric_limits<double>::denorm_min();
#if defined(__SSE__) || defined(_M_X64)
    // MXCSR bit 15 is FTZ; bit 6 is DAZ. Both defeat nextafter enclosures.
    const bool sse_denorm = (_mm_getcsr() & 0x8040u) == 0;
#else
    const bool sse_denorm = true;
#endif
    return std::numeric_limits<double>::is_iec559 &&
        std::numeric_limits<double>::has_denorm == std::denorm_present &&
        std::fegetround() == FE_TONEAREST &&
        runtime_denorm && sse_denorm;
}
bool completeShape(const NativeOtB1LinearModel& m) {
    const std::size_t n = m.names.size(), rows = m.senses.size();
    if (n == 0 || m.types.size() != n || m.lower_bounds.size() != n ||
        m.upper_bounds.size() != n || m.rhs.size() != rows ||
        m.row_starts.size() != rows + 1 || m.row_starts.front() != 0 ||
        m.row_starts.back() != static_cast<int>(m.coefficients.size()) ||
        m.column_indices.size() != m.coefficients.size()) return false;
    for (std::size_t r = 0; r < rows; ++r) {
        if (m.row_starts[r] > m.row_starts[r + 1] ||
            !std::isfinite(m.rhs[r])) return false;
    }
    for (std::size_t k = 0; k < m.coefficients.size(); ++k)
        if (m.column_indices[k] < 0 ||
            m.column_indices[k] >= static_cast<int>(n) ||
            !std::isfinite(m.coefficients[k])) return false;
    return true;
}
bool matchesRow(const NativeOtB1LinearModel& m, std::size_t row,
                char sense, double rhs, const std::map<int, double>& expected) {
    if (m.senses[row] != sense || m.rhs[row] != rhs ||
        m.row_starts[row + 1] - m.row_starts[row] !=
            static_cast<int>(expected.size())) return false;
    std::set<int> seen;
    for (int k = m.row_starts[row]; k < m.row_starts[row + 1]; ++k) {
        const auto found = expected.find(m.column_indices[k]);
        if (found == expected.end() || found->second != m.coefficients[k])
            return false;
        if (!seen.insert(m.column_indices[k]).second) return false;
    }
    return seen.size() == expected.size();
}
int findRow(const NativeOtB1LinearModel& m, const std::vector<int>& candidates,
            char sense, double rhs,
            const std::map<int, double>& terms) {
    int found = -1;
    for (int row : candidates) {
        if (matchesRow(m, static_cast<std::size_t>(row), sense, rhs, terms)) {
            if (found >= 0) return -2;
            found = row;
        }
    }
    return found;
}
bool parseStateName(const std::string& name, int station, int& inventory) {
    const std::string prefix = "state_" + std::to_string(station) + "_";
    if (name.compare(0, prefix.size(), prefix) != 0) return false;
    const std::string value = name.substr(prefix.size());
    if (value.empty() || value.size() > 10) return false;
    for (char c : value) if (c < '0' || c > '9') return false;
    try {
        const long long parsed = std::stoll(value);
        if (parsed > std::numeric_limits<int>::max()) return false;
        inventory = static_cast<int>(parsed);
        return true;
    } catch (...) { return false; }
}
int requiredColumn(const std::map<std::string, int>& columns,
                   const std::string& name) {
    const auto found = columns.find(name);
    if (found == columns.end()) throw std::runtime_error("missing_column:" + name);
    return found->second;
}
void requireRow(const NativeOtB1LinearModel& model,
                const std::unordered_map<int, std::vector<int>>& row_index,
                int anchor, char sense, double rhs,
                const std::map<int, double>& terms, const std::string& label,
                int& count) {
    const auto candidates = row_index.find(anchor);
    if (candidates == row_index.end() ||
        findRow(model, candidates->second, sense, rhs, terms) < 0)
        throw std::runtime_error("missing_or_ambiguous_row:" + label);
    ++count;
}
} // namespace

NativeOtB1Prepared prepareNativeOtB1(const NativeOtB1LinearModel& model,
                                     int station_count) {
    NativeOtB1Prepared prepared;
    prepared.original_columns = static_cast<int>(model.names.size());
    try {
        if (!arithmeticReady()) throw std::runtime_error("binary64_arithmetic_environment_invalid");
        if (station_count < 2 || !completeShape(model))
            throw std::runtime_error("invalid_model_shape");
        std::map<std::string, int> columns;
        for (std::size_t col = 0; col < model.names.size(); ++col) {
            if (model.names[col].empty() ||
                !columns.emplace(model.names[col], static_cast<int>(col)).second)
                throw std::runtime_error("duplicate_or_empty_column_name");
            if (std::isnan(model.lower_bounds[col]) ||
                std::isnan(model.upper_bounds[col]) ||
                model.lower_bounds[col] > model.upper_bounds[col])
                throw std::runtime_error("invalid_column_bounds");
        }
        // Index only columns needed to recognize the few structural rows.
        // A full scan for every h pair would revisit a large canonical LP
        // hundreds of times before the first native Optimize.
        std::unordered_map<int, std::vector<int>> row_index;
        for (std::size_t col = 0; col < model.names.size(); ++col) {
            const auto& name = model.names[col];
            if (name == "G" || name.rfind("Y_", 0) == 0 ||
                name.rfind("r_", 0) == 0 || name.rfind("h_", 0) == 0 ||
                (name.rfind("state_", 0) == 0 &&
                 name.rfind("state_g_", 0) != 0 &&
                 name.rfind("state_code_", 0) != 0))
                row_index.emplace(static_cast<int>(col), std::vector<int>{});
        }
        for (std::size_t row_number = 0; row_number < model.senses.size();
             ++row_number) {
            for (int k = model.row_starts[row_number];
                 k < model.row_starts[row_number+1]; ++k) {
                const auto found = row_index.find(model.column_indices[k]);
                if (found != row_index.end() &&
                    (found->second.empty() ||
                     found->second.back() != static_cast<int>(row_number)))
                    found->second.push_back(static_cast<int>(row_number));
            }
        }
        const int g_column = requiredColumn(columns, "G");
        if (model.types[g_column] != 'C')
            throw std::runtime_error("G_column_type_invalid");
        prepared.stations.reserve(static_cast<std::size_t>(station_count));
        for (int station = 1; station <= station_count; ++station) {
            const int y_col = requiredColumn(columns, "Y_" + std::to_string(station));
            const int r_col = requiredColumn(columns, "r_" + std::to_string(station));
            if (model.types[y_col] != 'I' || model.types[r_col] != 'C' ||
                !std::isfinite(model.lower_bounds[r_col]) ||
                !std::isfinite(model.upper_bounds[r_col]))
                throw std::runtime_error("y_or_r_domain_invalid");
            std::map<int, int> inventory_columns;
            for (std::size_t col = 0; col < model.names.size(); ++col) {
                int inventory = 0;
                if (parseStateName(model.names[col], station, inventory)) {
                    if (!inventory_columns.emplace(inventory, static_cast<int>(col)).second ||
                        model.types[col] != 'B' ||
                        model.lower_bounds[col] < 0.0 ||
                        model.upper_bounds[col] > 1.0)
                        throw std::runtime_error("state_selector_domain_invalid");
                }
            }
            if (inventory_columns.empty()) throw std::runtime_error("state_support_empty");
            const int first = inventory_columns.begin()->first;
            const int last = inventory_columns.rbegin()->first;
            if (last - first + 1 != static_cast<int>(inventory_columns.size()) ||
                model.lower_bounds[y_col] < first ||
                model.upper_bounds[y_col] > last)
                throw std::runtime_error("state_support_incomplete");
            std::map<int, double> onehot, inventory_row, g_row;
            inventory_row.emplace(y_col, 1.0);
            g_row.emplace(g_column, -1.0);
            NativeOtB1Station output;
            output.station = station;
            for (const auto& [inventory, state_col] : inventory_columns) {
                const int q_col = requiredColumn(columns, "state_g_" +
                    std::to_string(station) + "_" + std::to_string(inventory));
                if (model.types[q_col] != 'C' ||
                    !std::isfinite(model.lower_bounds[q_col]) ||
                    !std::isfinite(model.upper_bounds[q_col]))
                    throw std::runtime_error("state_g_domain_invalid");
                onehot.emplace(state_col, 1.0);
                if (inventory != 0)
                    inventory_row.emplace(state_col, -static_cast<double>(inventory));
                g_row.emplace(q_col, 1.0);
                output.states.push_back({state_col, inventory, 0.0, 0.0});
            }
            requireRow(model, row_index, output.states.front().column,
                '=', 1.0, onehot, "onehot_"+
                std::to_string(station), prepared.audited_rows);
            requireRow(model, row_index, y_col,
                '=', 0.0, inventory_row, "inventory_link_"+
                std::to_string(station), prepared.audited_rows);
            requireRow(model, row_index, g_column,
                '=', 0.0, g_row, "G_link_"+
                std::to_string(station), prepared.audited_rows);
            double alpha = 0.0;
            int r_rows = 0;
            for (int indexed_row : row_index.at(r_col)) {
                const std::size_t row = static_cast<std::size_t>(indexed_row);
                if (model.senses[row] != '=' || model.rhs[row] != 0.0 ||
                    model.row_starts[row + 1] - model.row_starts[row] != 2)
                    continue;
                bool has_r = false, has_y = false;
                double y_coefficient = 0.0;
                for (int k = model.row_starts[row]; k < model.row_starts[row + 1]; ++k) {
                    if (model.column_indices[k] == r_col && model.coefficients[k] == 1.0)
                        has_r = true;
                    if (model.column_indices[k] == y_col) {
                        has_y = true;
                        y_coefficient = model.coefficients[k];
                    }
                }
                if (has_r && has_y && y_coefficient < 0.0) {
                    alpha = -y_coefficient;
                    ++r_rows;
                }
            }
            if (r_rows != 1 || !std::isfinite(alpha))
                throw std::runtime_error("r_y_reconstruction_missing_or_ambiguous");
            ++prepared.audited_rows;
            for (auto& state : output.states) {
                const Interval product = roundedProduct(
                    alpha, static_cast<double>(state.inventory));
                state.nominal_support = alpha * static_cast<double>(state.inventory);
                state.support_error_upper =
                    upperError(state.nominal_support, product);
                if (!finite(product) || !std::isfinite(state.nominal_support) ||
                    !std::isfinite(state.support_error_upper))
                    throw std::runtime_error("support_product_interval_invalid");
            }
            prepared.stations.push_back(std::move(output));
        }
        prepared.audited_stations = station_count;
        for (int first = 1; first <= station_count; ++first) {
            for (int second = first + 1; second <= station_count; ++second) {
                const int h_col = requiredColumn(columns, "h_"+
                    std::to_string(first)+"_"+std::to_string(second));
                const int r_first = requiredColumn(columns, "r_"+std::to_string(first));
                const int r_second = requiredColumn(columns, "r_"+std::to_string(second));
                if (model.types[h_col] != 'C' ||
                    !std::isfinite(model.lower_bounds[h_col]) ||
                    model.lower_bounds[h_col] < 0.0)
                    throw std::runtime_error("h_domain_invalid");
                requireRow(model, row_index, h_col, '>', 0.0,
                    {{h_col, 1.0}, {r_first, -1.0}, {r_second, 1.0}},
                    "h_positive_"+std::to_string(first)+"_"+std::to_string(second),
                    prepared.audited_rows);
                requireRow(model, row_index, h_col, '>', 0.0,
                    {{h_col, 1.0}, {r_first, 1.0}, {r_second, -1.0}},
                    "h_negative_"+std::to_string(first)+"_"+std::to_string(second),
                    prepared.audited_rows);
                NativeOtB1Pair pair;
                pair.first_station = first;
                pair.second_station = second;
                pair.h_column = h_col;
                const auto& lhs = prepared.stations[static_cast<std::size_t>(first-1)].states;
                const auto& rhs = prepared.stations[static_cast<std::size_t>(second-1)].states;
                double first_error = 0.0, second_error = 0.0;
                for (const auto& state : lhs) {
                    pair.knots.push_back(state.nominal_support);
                    pair.first_columns.push_back(state.column);
                    first_error = std::max(first_error, state.support_error_upper);
                }
                for (const auto& state : rhs) {
                    pair.knots.push_back(state.nominal_support);
                    pair.second_columns.push_back(state.column);
                    second_error = std::max(second_error, state.support_error_upper);
                }
                pair.support_error_upper = addUpper(first_error, second_error);
                std::sort(pair.knots.begin(), pair.knots.end());
                pair.knots.erase(std::unique(pair.knots.begin(), pair.knots.end()),
                                 pair.knots.end());
                for (const auto& state : lhs)
                    pair.first_knot.push_back(static_cast<int>(
                        std::lower_bound(pair.knots.begin(), pair.knots.end(),
                                         state.nominal_support)-pair.knots.begin()));
                for (const auto& state : rhs)
                    pair.second_knot.push_back(static_cast<int>(
                        std::lower_bound(pair.knots.begin(), pair.knots.end(),
                                         state.nominal_support)-pair.knots.begin()));
                if (!std::isfinite(pair.support_error_upper))
                    throw std::runtime_error("support_error_overflow");
                prepared.pairs.push_back(std::move(pair));
            }
        }
        prepared.valid = true;
        prepared.reason = "audited_two_link_vdp_model";
    } catch (const std::exception& error) {
        prepared.valid = false;
        prepared.reason = error.what();
        prepared.stations.clear();
        prepared.pairs.clear();
    }
    return prepared;
}

NativeOtB1Cut separateNativeOtB1(const NativeOtB1Pair& pair,
                                 const std::vector<double>& point,
                                 double tolerance) {
    NativeOtB1Cut cut;
    cut.first_station = pair.first_station;
    cut.second_station = pair.second_station;
    try {
        if (!arithmeticReady() || !std::isfinite(tolerance) || tolerance < 0.0 ||
            pair.h_column < 0 ||
            static_cast<std::size_t>(pair.h_column) >= point.size() ||
            pair.first_columns.size() != pair.first_knot.size() ||
            pair.second_columns.size() != pair.second_knot.size() ||
            !std::isfinite(pair.support_error_upper))
            throw std::runtime_error("pair_or_arithmetic_environment_invalid");
        for (int col : pair.first_columns)
            if (col < 0 || static_cast<std::size_t>(col) >= point.size() ||
                !std::isfinite(point[static_cast<std::size_t>(col)]))
                throw std::runtime_error("nonfinite_first_selector");
        for (int col : pair.second_columns)
            if (col < 0 || static_cast<std::size_t>(col) >= point.size() ||
                !std::isfinite(point[static_cast<std::size_t>(col)]))
                throw std::runtime_error("nonfinite_second_selector");
        if (!std::isfinite(point[static_cast<std::size_t>(pair.h_column)]))
            throw std::runtime_error("nonfinite_h");
        if (pair.knots.size() < 2) {
            cut.status = NativeOtB1Cut::Status::NotViolated;
            cut.reason = "single_merged_knot";
            return cut;
        }
        const std::size_t intervals = pair.knots.size() - 1;
        std::vector<double> mass_i(pair.knots.size(), 0.0),
            mass_j(pair.knots.size(), 0.0), signs(intervals, 1.0);
        for (std::size_t n = 0; n < pair.first_columns.size(); ++n)
            mass_i[static_cast<std::size_t>(pair.first_knot[n])] +=
                point[static_cast<std::size_t>(pair.first_columns[n])];
        for (std::size_t n = 0; n < pair.second_columns.size(); ++n)
            mass_j[static_cast<std::size_t>(pair.second_knot[n])] +=
                point[static_cast<std::size_t>(pair.second_columns[n])];
        double cdf_difference = 0.0;
        for (std::size_t k = 0; k < intervals; ++k) {
            cdf_difference += mass_i[k] - mass_j[k];
            if (!std::isfinite(cdf_difference))
                throw std::runtime_error("nonfinite_cdf");
            signs[k] = cdf_difference >= 0.0 ? 1.0 : -1.0;
        }
        std::vector<Interval> suffix_intervals(pair.knots.size());
        std::vector<double> suffix_nominal(pair.knots.size(), 0.0);
        for (std::size_t reverse = intervals; reverse > 0; --reverse) {
            const std::size_t k = reverse - 1;
            Interval width = roundedDifference(pair.knots[k+1], pair.knots[k]);
            if (!finite(width) || width.upper <= 0.0)
                throw std::runtime_error("invalid_knot_width");
            if (signs[k] < 0.0) width = negate(width);
            suffix_intervals[k] = add(suffix_intervals[k+1], width);
            suffix_nominal[k] = suffix_nominal[k+1] +
                signs[k] * (pair.knots[k+1] - pair.knots[k]);
            if (!finite(suffix_intervals[k]) || !std::isfinite(suffix_nominal[k]))
                throw std::runtime_error("suffix_interval_overflow");
        }
        std::vector<std::pair<int, double>> entries;
        entries.reserve(1 + pair.first_columns.size() + pair.second_columns.size());
        entries.emplace_back(pair.h_column, 1.0);
        double first_error = 0.0, second_error = 0.0;
        for (std::size_t n = 0; n < pair.first_columns.size(); ++n) {
            const std::size_t k = static_cast<std::size_t>(pair.first_knot[n]);
            entries.emplace_back(pair.first_columns[n], -suffix_nominal[k]);
            first_error = std::max(first_error,
                upperError(suffix_nominal[k], suffix_intervals[k]));
        }
        for (std::size_t n = 0; n < pair.second_columns.size(); ++n) {
            const std::size_t k = static_cast<std::size_t>(pair.second_knot[n]);
            entries.emplace_back(pair.second_columns[n], suffix_nominal[k]);
            second_error = std::max(second_error,
                upperError(suffix_nominal[k], suffix_intervals[k]));
        }
        cut.support_error_upper = pair.support_error_upper;
        cut.coefficient_error_upper = addUpper(first_error, second_error);
        const double delta = addUpper(cut.support_error_upper,
                                      cut.coefficient_error_upper);
        if (!std::isfinite(delta))
            throw std::runtime_error("validity_error_overflow");
        cut.rhs = delta == 0.0 ? 0.0 : down(-delta);
        std::sort(entries.begin(), entries.end(),
                  [](const auto& a, const auto& b) { return a.first < b.first; });
        Interval activity;
        for (const auto& [index, coefficient] : entries) {
            if (!std::isfinite(coefficient) ||
                index < 0 || static_cast<std::size_t>(index) >= point.size() ||
                !std::isfinite(point[static_cast<std::size_t>(index)]))
                throw std::runtime_error("cut_or_point_nonfinite");
            cut.indices.push_back(index);
            cut.coefficients.push_back(coefficient);
            activity = add(activity,
                roundedProduct(coefficient, point[static_cast<std::size_t>(index)]));
            if (!finite(activity))
                throw std::runtime_error("activity_interval_overflow");
        }
        cut.activity_upper = activity.upper;
        const double gap = cut.rhs - cut.activity_upper;
        if (!std::isfinite(gap))
            throw std::runtime_error("violation_gap_nonfinite");
        cut.reliable_violation_lower = down(gap);
        cut.status = cut.reliable_violation_lower > tolerance
            ? NativeOtB1Cut::Status::Reliable
            : NativeOtB1Cut::Status::NotViolated;
        cut.reason = cut.status == NativeOtB1Cut::Status::Reliable
            ? "reliably_violated" : "not_reliably_violated";
    } catch (const std::exception& error) {
        cut.status = NativeOtB1Cut::Status::ArithmeticSkip;
        cut.reason = error.what();
        cut.indices.clear();
        cut.coefficients.clear();
    }
    return cut;
}

} // namespace ebrp
