#include "Round92HandlingActivation.hpp"

#include <algorithm>
#include <chrono>
#include <cfenv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <utility>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__)
#error "Round92 outward binary64 proof cannot be compiled with fast-math"
#endif

namespace ebrp {
namespace {

constexpr double kWriterZeroTolerance = 1e-12;
constexpr double kExactSmallInteger = 4503599627370496.0; // 2^52.
constexpr double kLargestExactInteger = 9007199254740992.0; // 2^53.

struct Interval {
    double lower = 0.0;
    double upper = 0.0;
    bool reachable = false;
};

bool smallInteger(double x) {
    return std::isfinite(x) && std::fabs(x) <= kExactSmallInteger &&
           std::trunc(x) == x;
}

bool exactIntegerSum(double a, double b, double& result) {
    if (!smallInteger(a) || !smallInteger(b)) return false;
    const double sum = a + b;
    if (!smallInteger(sum)) return false;
    result = sum; // Exact signed integer arithmetic below 2^52.
    return true;
}

double outwardSum(double a, double b, bool upward) {
    double exact = 0.0;
    if (exactIntegerSum(a, b, exact)) return exact;
    const double rounded = a + b;
    if (!std::isfinite(rounded)) return std::numeric_limits<double>::quiet_NaN();
    const double enclosure = std::nextafter(
        rounded, upward ? std::numeric_limits<double>::infinity()
                        : -std::numeric_limits<double>::infinity());
    // Path weights are nonnegative. This also avoids spurious negative cycles
    // when an exact zero sum rounds to a signed subnormal enclosure.
    return std::max(0.0, enclosure);
}

double outwardDifference(double a, double b, bool upward) {
    double exact = 0.0;
    if (exactIntegerSum(a, -b, exact)) return exact;
    const double rounded = a - b;
    if (!std::isfinite(rounded)) return std::numeric_limits<double>::quiet_NaN();
    return std::nextafter(
        rounded, upward ? std::numeric_limits<double>::infinity()
                        : -std::numeric_limits<double>::infinity());
}

double outwardQuotient(double numerator, double denominator, bool upward) {
    if (smallInteger(numerator) && smallInteger(denominator) && denominator > 0) {
        const auto n = static_cast<std::int64_t>(numerator);
        const auto d = static_cast<std::int64_t>(denominator);
        if (d != 0 && n % d == 0) return static_cast<double>(n / d);
    }
    const double rounded = numerator / denominator;
    if (!std::isfinite(rounded)) return std::numeric_limits<double>::quiet_NaN();
    return std::nextafter(
        rounded, upward ? std::numeric_limits<double>::infinity()
                        : -std::numeric_limits<double>::infinity());
}

Round92HandlingActivationPlan refused(std::string reason,
                                      double elapsed,
                                      int arcs,
                                      bool valid_input = false) {
    Round92HandlingActivationPlan plan;
    plan.valid_input = valid_input;
    plan.reason = std::move(reason);
    plan.preparation_wall_seconds = elapsed;
    plan.allowed_directed_arcs = arcs;
    return plan;
}

bool safeFloatingEnvironment() {
    if (!std::numeric_limits<double>::is_iec559 ||
        sizeof(double) != sizeof(std::uint64_t) ||
        std::fegetround() != FE_TONEAREST) return false;
    // Volatile operands force both operations to execute at runtime. FTZ
    // would erase the subnormal product; DAZ would erase the subnormal input.
    volatile double normal = std::numeric_limits<double>::min();
    volatile double half = 0.5;
    volatile double subnormal = std::numeric_limits<double>::denorm_min();
    const double product = normal * half;
    const double sum = subnormal + subnormal;
    std::uint64_t product_bits = 0, sum_bits = 0;
    std::memcpy(&product_bits, &product, sizeof(double));
    std::memcpy(&sum_bits, &sum, sizeof(double));
    return product_bits == (std::uint64_t{1} << 51) && sum_bits == 2;
}

} // namespace

double round92CanonicalEmittedCoefficient(double value) {
    if (!std::isfinite(value)) return std::numeric_limits<double>::quiet_NaN();
    if (std::fabs(value) <= kWriterZeroTolerance) return 0.0;
    if (std::fabs(std::fabs(value) - 1.0) <= kWriterZeroTolerance)
        return std::copysign(1.0, value);
    return value;
}

Round92HandlingActivationPlan prepareRound92HandlingActivation(
    const Round92DurationCoefficients& row) {
    const auto begun = std::chrono::steady_clock::now();
    const auto elapsed = [&] {
        return std::chrono::duration<double>(
            std::chrono::steady_clock::now() - begun).count();
    };
    int arcs = 0;
    if (!safeFloatingEnvironment())
        return refused("unsafe_floating_environment", elapsed(), arcs);
    if (!std::isfinite(row.horizon) || row.horizon < 0)
        return refused("invalid_duration_rhs", elapsed(), arcs);
    if (!std::isfinite(row.pickup) || row.pickup < 0 ||
        round92CanonicalEmittedCoefficient(row.pickup) != row.pickup)
        return refused("invalid_or_noncanonical_pickup_coefficient", elapsed(), arcs);
    const auto n = row.directed_travel.size();
    if (n < 2 || n > static_cast<std::size_t>(std::numeric_limits<int>::max()))
        return refused("invalid_station_count", elapsed(), arcs);
    for (std::size_t i = 0; i < n; ++i) {
        if (row.directed_travel[i].size() != n)
            return refused("invalid_arc_matrix_shape", elapsed(), arcs);
        for (std::size_t j = 0; j < n; ++j) {
            const auto& value = row.directed_travel[i][j];
            if (i == j && value.has_value())
                return refused("diagonal_arc_present", elapsed(), arcs);
            if (!value.has_value()) continue;
            if (!std::isfinite(*value) || *value < 0 ||
                round92CanonicalEmittedCoefficient(*value) != *value)
                return refused("invalid_or_noncanonical_travel_coefficient", elapsed(), arcs);
            ++arcs;
        }
    }
    if (row.pickup == 0)
        return refused("zero_handling_has_no_duration_quantity_bound",
                       elapsed(), arcs, true);
    std::vector<std::vector<Interval>> d(n, std::vector<Interval>(n));
    for (std::size_t i = 0; i < n; ++i) {
        d[i][i] = {0, 0, true};
        for (std::size_t j = 0; j < n; ++j) {
            if (i != j && row.directed_travel[i][j].has_value()) {
                const double x = *row.directed_travel[i][j];
                d[i][j] = {x, x, true};
            }
        }
    }
    for (std::size_t middle = 0; middle < n; ++middle) {
        for (std::size_t i = 0; i < n; ++i) {
            for (std::size_t j = 0; j < n; ++j) {
                if (!d[i][middle].reachable || !d[middle][j].reachable) continue;
                const double lo = outwardSum(
                    d[i][middle].lower, d[middle][j].lower, false);
                const double hi = outwardSum(
                    d[i][middle].upper, d[middle][j].upper, true);
                if (!std::isfinite(lo) || !std::isfinite(hi))
                    return refused("nonfinite_shortest_path_enclosure", elapsed(), arcs);
                if (!d[i][j].reachable) d[i][j] = {lo, hi, true};
                else {
                    d[i][j].lower = std::min(d[i][j].lower, lo);
                    d[i][j].upper = std::min(d[i][j].upper, hi);
                }
            }
        }
    }
    Interval minimum;
    for (std::size_t i = 1; i < n; ++i) {
        if (!d[0][i].reachable || !d[i][0].reachable) continue;
        const double lo = outwardSum(d[0][i].lower, d[i][0].lower, false);
        const double hi = outwardSum(d[0][i].upper, d[i][0].upper, true);
        if (!std::isfinite(lo) || !std::isfinite(hi))
            return refused("nonfinite_return_travel_enclosure", elapsed(), arcs);
        if (!minimum.reachable) minimum = {lo, hi, true};
        else {
            minimum.lower = std::min(minimum.lower, lo);
            minimum.upper = std::min(minimum.upper, hi);
        }
    }
    if (!minimum.reachable) {
        Round92HandlingActivationPlan plan;
        plan.valid_input = true;
        plan.applicable = true;
        plan.reason = "no_depot_closed_station_path_implies_zero_pickup_under_F0";
        plan.integer_capacity = 0;
        plan.activation_coefficient = 0;
        plan.allowed_directed_arcs = arcs;
        plan.preparation_wall_seconds = elapsed();
        return plan;
    }
    const double numerator_lo = outwardDifference(row.horizon, minimum.upper, false);
    const double numerator_hi = outwardDifference(row.horizon, minimum.lower, true);
    const double quotient_lo = outwardQuotient(numerator_lo, row.pickup, false);
    const double quotient_hi = outwardQuotient(numerator_hi, row.pickup, true);
    if (!std::isfinite(quotient_lo) || !std::isfinite(quotient_hi) ||
        quotient_lo > quotient_hi)
        return refused("nonfinite_or_reversed_quotient_enclosure", elapsed(), arcs);
    const double floor_lo = std::max(0.0, std::floor(quotient_lo));
    const double floor_hi = std::max(0.0, std::floor(quotient_hi));
    if (floor_hi > kLargestExactInteger)
        return refused("integer_coefficient_not_exact_binary64", elapsed(), arcs);
    Round92HandlingActivationPlan plan;
    plan.valid_input = true;
    plan.applicable = true;
    plan.reason = floor_lo == floor_hi
        ? "exact_integer_floor_certified_by_outward_enclosure"
        : "conservative_upper_floor_may_be_weaker";
    plan.integer_capacity = static_cast<std::uint64_t>(floor_hi);
    plan.activation_coefficient = -static_cast<double>(plan.integer_capacity);
    plan.exact_integer_floor = floor_lo == floor_hi;
    plan.quotient_enclosure_available = true;
    plan.lmin_lower = minimum.lower;
    plan.lmin_upper = minimum.upper;
    plan.quotient_lower = quotient_lo;
    plan.quotient_upper = quotient_hi;
    plan.allowed_directed_arcs = arcs;
    plan.preparation_wall_seconds = elapsed();
    return plan;
}

} // namespace ebrp
