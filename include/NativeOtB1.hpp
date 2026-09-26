#pragma once

#include <string>
#include <vector>

namespace ebrp {

// This module has no solver dependency. All numbers in an audited model are
// the binary64 values read back from the canonical LP, not source fractions.
struct NativeOtB1LinearModel {
    std::vector<std::string> names;
    std::vector<char> types;
    std::vector<double> lower_bounds;
    std::vector<double> upper_bounds;
    std::vector<int> row_starts;
    std::vector<int> column_indices;
    std::vector<double> coefficients;
    std::vector<char> senses;
    std::vector<double> rhs;
};

struct NativeOtB1State {
    int column = -1;
    int inventory = 0;
    double nominal_support = 0.0;
    double support_error_upper = 0.0;
};

struct NativeOtB1Station {
    int station = 0;
    std::vector<NativeOtB1State> states;
};

struct NativeOtB1Pair {
    int first_station = 0;
    int second_station = 0;
    int h_column = -1;
    std::vector<int> first_columns;
    std::vector<int> second_columns;
    std::vector<int> first_knot;
    std::vector<int> second_knot;
    std::vector<double> knots;
    double support_error_upper = 0.0;
};

struct NativeOtB1Prepared {
    bool valid = false;
    std::string reason;
    int original_columns = 0;
    int audited_rows = 0;
    int audited_stations = 0;
    std::vector<NativeOtB1Station> stations;
    std::vector<NativeOtB1Pair> pairs;
};

struct NativeOtB1Cut {
    enum class Status { InvalidPoint, ArithmeticSkip, NotViolated, Reliable };
    Status status = Status::ArithmeticSkip;
    std::string reason;
    int first_station = 0;
    int second_station = 0;
    std::vector<int> indices;
    std::vector<double> coefficients;
    char sense = '>';
    double rhs = 0.0;
    double support_error_upper = 0.0;
    double coefficient_error_upper = 0.0;
    double activity_upper = 0.0;
    double reliable_violation_lower = 0.0;
};

NativeOtB1Prepared prepareNativeOtB1(const NativeOtB1LinearModel& model,
                                     int station_count);
NativeOtB1Cut separateNativeOtB1(const NativeOtB1Pair& pair,
                                 const std::vector<double>& original_point,
                                 double feasibility_tolerance);

} // namespace ebrp
