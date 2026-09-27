#include "Round92HandlingActivation.hpp"
#include "Evaluator.hpp"
#include "Instance.hpp"
#include "PhysicalDurationTolerance.hpp"

#include <algorithm>
#include <chrono>
#include <cfenv>
#include <cfloat>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <utility>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__)
#error "Round92 outward binary64 proof cannot be compiled with fast-math"
#endif

static_assert(FLT_EVAL_METHOD == 0,
              "Round92 requires every Evaluator/proof operation to round to binary64");

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

bool sameBits(double x, double y) {
    std::uint64_t xb = 0, yb = 0;
    std::memcpy(&xb, &x, sizeof(x));
    std::memcpy(&yb, &y, sizeof(y));
    return xb == yb;
}

bool sameArcMatrix(const std::vector<std::vector<std::optional<double>>>& a,
                   const std::vector<std::vector<std::optional<double>>>& b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (a[i].size() != b[i].size()) return false;
        for (std::size_t j = 0; j < a[i].size(); ++j) {
            if (a[i][j].has_value() != b[i][j].has_value() ||
                (a[i][j] && !sameBits(*a[i][j], *b[i][j]))) return false;
        }
    }
    return true;
}

} // namespace

bool round92SameDurationKey(const Round92DurationCoefficients& a,
                            const Round92DurationCoefficients& b) {
    return sameBits(a.horizon, b.horizon) && sameBits(a.pickup, b.pickup) &&
           sameBits(a.raw_pickup_time, b.raw_pickup_time) &&
           sameBits(a.raw_drop_time, b.raw_drop_time) &&
           sameBits(a.physical_tolerance, b.physical_tolerance) &&
           a.evaluator_arithmetic_contract == b.evaluator_arithmetic_contract &&
           sameArcMatrix(a.directed_travel, b.directed_travel) &&
           sameArcMatrix(a.raw_directed_travel, b.raw_directed_travel);
}

void round92RequireProofEnvironment() {
    if (!safeFloatingEnvironment())
        throw std::runtime_error("round92_unsafe_floating_environment");
}

void round92RequireLawfulDomain(const Instance& instance) {
    if (instance.V < 1 ||
        instance.V > std::numeric_limits<int>::max() - 7 || instance.M < 1 ||
        instance.Q.size() != static_cast<std::size_t>(instance.M) ||
        instance.initial.size() != static_cast<std::size_t>(instance.V + 1) ||
        instance.capacity.size() != static_cast<std::size_t>(instance.V + 1) ||
        instance.target.size() != static_cast<std::size_t>(instance.V + 1) ||
        instance.weights.size() != static_cast<std::size_t>(instance.V + 1) ||
        instance.dist.size() != static_cast<std::size_t>(instance.V + 1) ||
        !std::isfinite(instance.total_time_limit) || instance.total_time_limit < 0 ||
        !std::isfinite(instance.pickup_time) || instance.pickup_time < 0 ||
        !std::isfinite(instance.drop_time) || instance.drop_time < 0)
        throw std::runtime_error("round92_invalid_physical_domain");
    int max_q = 0;
    for (int q : instance.Q) {
        if (q < 0) throw std::runtime_error("round92_negative_vehicle_capacity");
        max_q = std::max(max_q, q);
    }
    if (static_cast<std::uint64_t>(instance.V) *
            static_cast<std::uint64_t>(max_q) >
        static_cast<std::uint64_t>(std::numeric_limits<int>::max()))
        throw std::runtime_error("round92_evaluator_count_domain_exceeded");
    for (int i = 0; i <= instance.V; ++i) {
        if (instance.initial[i] < 0 || instance.capacity[i] < 0 ||
            instance.initial[i] > instance.capacity[i] ||
            instance.dist[i].size() != static_cast<std::size_t>(instance.V + 1))
            throw std::runtime_error("round92_invalid_inventory_or_arc_domain");
        if (i > 0 && (instance.target[i] <= 0 ||
                      !std::isfinite(instance.weights[i]) || instance.weights[i] < 0))
            throw std::runtime_error("round92_invalid_objective_domain");
        for (int j = 0; j <= instance.V; ++j)
            if (!std::isfinite(instance.dist[i][j]) || instance.dist[i][j] < 0)
                throw std::runtime_error("round92_invalid_raw_directed_travel");
    }
}

Verification round92AdmitWitness(const Instance& instance,
                                  const std::vector<RoutePlan>& routes,
                                  double lambda,
                                  std::optional<double> expected_objective) {
    round92RequireProofEnvironment();
    round92RequireLawfulDomain(instance);
    if (!std::isfinite(lambda) || lambda < 0)
        throw std::runtime_error("round92_invalid_objective_weight");
    if (expected_objective && !std::isfinite(*expected_objective))
        throw std::runtime_error("round92_nonfinite_reported_witness_objective");
    std::vector<bool> vehicle_seen(instance.M, false);
    std::vector<bool> station_seen(instance.V + 1, false);
    std::vector<std::int64_t> inventory(instance.initial.begin(), instance.initial.end());
    for (const RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M ||
            vehicle_seen[route.vehicle] || route.nodes.size() < 2 ||
            route.nodes.front() != 0 || route.nodes.back() != 0 ||
            route.nodes.size() > static_cast<std::size_t>(instance.V) + 2)
            throw std::runtime_error("round92_malformed_vehicle_tour");
        vehicle_seen[route.vehicle] = true;
        if (route.operations.size() != route.nodes.size() - 2)
            throw std::runtime_error("round92_operation_visit_mismatch");
        std::vector<const StopOperation*> operation_at(instance.V + 1, nullptr);
        for (const StopOperation& op : route.operations) {
            if (op.station <= 0 || op.station > instance.V ||
                operation_at[op.station] != nullptr)
                throw std::runtime_error("round92_extra_or_duplicate_operation");
            operation_at[op.station] = &op;
        }
        std::int64_t load = 0, picks = 0, drops = 0;
        for (std::size_t t = 1; t + 1 < route.nodes.size(); ++t) {
            const int station = route.nodes[t];
            if (station <= 0 || station > instance.V || station_seen[station])
                throw std::runtime_error("round92_repeated_or_invalid_station");
            station_seen[station] = true;
            const StopOperation* op = operation_at[station];
            if (!op || op->pickup < 0 || op->drop < 0 ||
                (op->pickup > 0) == (op->drop > 0))
                throw std::runtime_error("round92_invalid_visit_operation");
            picks += op->pickup;
            drops += op->drop;
            load += static_cast<std::int64_t>(op->pickup) - op->drop;
            inventory[station] += static_cast<std::int64_t>(op->drop) - op->pickup;
            if (load < 0 || load > instance.Q[route.vehicle] ||
                inventory[station] < 0 || inventory[station] > instance.capacity[station] ||
                picks > std::numeric_limits<int>::max() ||
                drops > std::numeric_limits<int>::max())
                throw std::runtime_error("round92_witness_count_or_load_out_of_domain");
        }
    }
    const Verification verification = verifySolution(instance, routes, lambda);
    if (!verification.feasible || !verification.original_solution_feasible ||
        !verification.original_objective_recomputed ||
        !verification.errors.empty() || !std::isfinite(verification.objective) ||
        (expected_objective &&
         std::fabs(verification.objective - *expected_objective) >
            1e-7 * std::max({1.0, std::fabs(verification.objective),
                             std::fabs(*expected_objective)})))
        throw std::runtime_error("round92_witness_physical_or_objective_mismatch");
    return verification;
}

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
    if (!sameBits(row.physical_tolerance, kPhysicalDurationTolerance) ||
        row.evaluator_arithmetic_contract != 2)
        return refused("physical_evaluator_contract_mismatch", elapsed(), arcs);
    if (!std::isfinite(row.pickup) || row.pickup < 0 ||
        round92CanonicalEmittedCoefficient(row.pickup) != row.pickup)
        return refused("invalid_or_noncanonical_pickup_coefficient", elapsed(), arcs);
    if (!std::isfinite(row.raw_pickup_time) || row.raw_pickup_time < 0 ||
        !std::isfinite(row.raw_drop_time) || row.raw_drop_time < 0 ||
        round92CanonicalEmittedCoefficient(
            row.raw_pickup_time + row.raw_drop_time) != row.pickup)
        return refused("raw_and_canonical_handling_mismatch", elapsed(), arcs);
    const auto n = row.directed_travel.size();
    if (n < 2 || n > static_cast<std::size_t>(std::numeric_limits<int>::max() - 7) ||
        row.raw_directed_travel.size() != n)
        return refused("invalid_station_count", elapsed(), arcs);
    for (std::size_t i = 0; i < n; ++i) {
        if (row.directed_travel[i].size() != n ||
            row.raw_directed_travel[i].size() != n)
            return refused("invalid_arc_matrix_shape", elapsed(), arcs);
        for (std::size_t j = 0; j < n; ++j) {
            const auto& value = row.directed_travel[i][j];
            const auto& raw = row.raw_directed_travel[i][j];
            if ((i == j && (value.has_value() || raw.has_value())) ||
                value.has_value() != raw.has_value())
                return refused("diagonal_arc_present", elapsed(), arcs);
            if (!value.has_value()) continue;
            if (!std::isfinite(*value) || *value < 0 ||
                !std::isfinite(*raw) || *raw < 0 ||
                round92CanonicalEmittedCoefficient(*raw) != *value)
                return refused("invalid_or_noncanonical_travel_coefficient", elapsed(), arcs);
            ++arcs;
        }
    }
    const double raw_service_lower = outwardSum(
        row.raw_pickup_time, row.raw_drop_time, false);
    const double service_lower = std::min(raw_service_lower, row.pickup);
    if (!std::isfinite(service_lower))
        return refused("nonfinite_lower_service_coefficient", elapsed(), arcs);
    if (service_lower == 0)
        return refused("zero_common_lower_service_has_no_quantity_bound",
                       elapsed(), arcs, true);
    // The exact physical duration may exceed the binary64 value accepted by
    // Evaluator. Bound its rounding loss using V+1 travel additions, three
    // products, two service additions and the final duration addition.
    constexpr double rho = 1.0 - 0x1p-53;
    constexpr double eta = std::numeric_limits<double>::denorm_min();
    const std::size_t station_count = n - 1;
    const std::size_t operations = std::max(station_count + 2, std::size_t{4});
    const double eta_budget = static_cast<double>(station_count + 7) * eta;
    const double comparison_hi = outwardSum(
        row.horizon, row.physical_tolerance, true);
    double physical_hi = outwardSum(comparison_hi, eta_budget, true);
    for (std::size_t step = 0; step < operations; ++step)
        physical_hi = outwardQuotient(physical_hi, rho, true);
    const double common_hi = std::max(row.horizon, physical_hi);
    if (!std::isfinite(physical_hi) || !std::isfinite(common_hi))
        return refused("nonfinite_physical_acceptance_horizon", elapsed(), arcs);
    std::vector<std::vector<Interval>> d(n, std::vector<Interval>(n));
    for (std::size_t i = 0; i < n; ++i) {
        d[i][i] = {0, 0, true};
        for (std::size_t j = 0; j < n; ++j) {
            if (i != j && row.directed_travel[i][j].has_value()) {
                const double x = std::min(*row.directed_travel[i][j],
                                          *row.raw_directed_travel[i][j]);
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
        plan.lower_service_coefficient = service_lower;
        plan.physical_horizon_upper = physical_hi;
        plan.common_horizon_upper = common_hi;
        plan.preparation_wall_seconds = elapsed();
        return plan;
    }
    const double numerator_lo = outwardDifference(common_hi, minimum.upper, false);
    const double numerator_hi = outwardDifference(common_hi, minimum.lower, true);
    const double quotient_lo = outwardQuotient(numerator_lo, service_lower, false);
    const double quotient_hi = outwardQuotient(numerator_hi, service_lower, true);
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
        ? "uniform_envelope_integer_floor_certified"
        : "uniform_envelope_upper_floor_conservative";
    plan.integer_capacity = static_cast<std::uint64_t>(floor_hi);
    plan.activation_coefficient = -static_cast<double>(plan.integer_capacity);
    plan.exact_integer_floor = floor_lo == floor_hi;
    plan.quotient_enclosure_available = true;
    plan.lmin_lower = minimum.lower;
    plan.lmin_upper = minimum.upper;
    plan.lower_service_coefficient = service_lower;
    plan.physical_horizon_upper = physical_hi;
    plan.common_horizon_upper = common_hi;
    plan.quotient_lower = quotient_lo;
    plan.quotient_upper = quotient_hi;
    plan.allowed_directed_arcs = arcs;
    plan.preparation_wall_seconds = elapsed();
    return plan;
}

} // namespace ebrp
