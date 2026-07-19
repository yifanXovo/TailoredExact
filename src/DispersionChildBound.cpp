#include "IntervalRowFactory.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <utility>
#include <vector>

namespace ebrp {
namespace {

double roundDownToDouble(long double value) {
    if (!std::isfinite(value)) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    const double converted = static_cast<double>(value);
    if (!std::isfinite(converted)) {
        return std::numeric_limits<double>::quiet_NaN();
    }
    if (static_cast<long double>(converted) > value) {
        return std::nextafter(converted,
                              -std::numeric_limits<double>::infinity());
    }
    return converted;
}

} // namespace

ChildDomainEstimate computeDispersionCoupledChildEstimate(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalDomainSummary& domain,
    double child_gamma_lower,
    double parent_relaxation) {
    ChildDomainEstimate out;
    out.parent_relaxation = parent_relaxation;
    out.gamma_floor_component = child_gamma_lower;
    out.station_deviation_lower.assign(
        static_cast<std::size_t>(std::max(0, instance.V) + 1), 0.0);
    out.station_weighted_deviation_lower.assign(
        static_cast<std::size_t>(std::max(0, instance.V) + 1), 0.0);
    out.validation_status = "dispersion_coupled_validation_started";

    if (!std::isfinite(parent_relaxation)) {
        out.failure_reason = "parent_relaxation_not_finite";
        return out;
    }
    if (!std::isfinite(options.lambda) || options.lambda < 0.0) {
        out.failure_reason = "lambda_not_finite_nonnegative";
        return out;
    }
    if (!std::isfinite(child_gamma_lower) || child_gamma_lower < 0.0) {
        out.failure_reason = "child_gamma_lower_not_finite_nonnegative";
        return out;
    }
    if (!std::isfinite(domain.s_lower) || domain.s_lower < 0.0) {
        out.failure_reason = "s_lower_not_finite_nonnegative";
        return out;
    }
    if (domain.domain_infeasible) {
        out.failure_reason =
            "factory_domain_infeasible_without_exact_pruning_gate";
        return out;
    }
    if (instance.V <= 1) {
        out.domain_estimate = parent_relaxation;
        out.final_estimate = parent_relaxation;
        out.validation_status = "vehicle_count_at_most_one_parent_fallback";
        out.valid = true;
        return out;
    }
    if (instance.weights.size() <= static_cast<std::size_t>(instance.V) ||
        domain.e_lower.size() <= static_cast<std::size_t>(instance.V) ||
        domain.e_upper.size() <= static_cast<std::size_t>(instance.V)) {
        out.failure_reason = "dispersion_domain_vector_size_mismatch";
        return out;
    }

    std::vector<std::pair<long double, int>> order;
    order.reserve(static_cast<std::size_t>(instance.V));
    std::vector<long double> lower(static_cast<std::size_t>(instance.V + 1));
    std::vector<long double> upper(static_cast<std::size_t>(instance.V + 1));
    long double lower_sum = 0.0L;
    long double upper_sum = 0.0L;
    long double phi = 0.0L;
    for (int station = 1; station <= instance.V; ++station) {
        const double weight = instance.weights[station];
        const double e_lower = domain.e_lower[station];
        const double e_upper = domain.e_upper[station];
        if (!std::isfinite(weight) || weight < 0.0) {
            out.failure_reason = "station_weight_not_finite_nonnegative:" +
                std::to_string(station);
            return out;
        }
        if (!std::isfinite(e_lower) || !std::isfinite(e_upper) ||
            e_lower < 0.0 || e_upper < e_lower) {
            out.failure_reason = "inconsistent_deviation_domain:" +
                std::to_string(station);
            return out;
        }
        lower[station] = static_cast<long double>(e_lower);
        upper[station] = static_cast<long double>(e_upper);
        lower_sum += lower[station];
        upper_sum += upper[station];
        phi += static_cast<long double>(weight) * lower[station];
        order.emplace_back(static_cast<long double>(weight), station);
        out.station_deviation_lower[station] = e_lower;
        out.station_weighted_deviation_lower[station] = weight * e_lower;
    }
    std::sort(order.begin(), order.end(),
        [](const auto& lhs, const auto& rhs) {
            return lhs.first < rhs.first ||
                (lhs.first == rhs.first && lhs.second < rhs.second);
        });

    const long double V = static_cast<long double>(instance.V);
    long double required = V * static_cast<long double>(child_gamma_lower) *
        static_cast<long double>(domain.s_lower) / (V - 1.0L);
    // A smaller right-hand side is conservative if the product/division was
    // rounded upward by the host long-double implementation.
    required = std::nextafter(required,
                              -std::numeric_limits<long double>::infinity());
    required = std::max(0.0L, required);
    out.s_lower = domain.s_lower;
    out.required_deviation = roundDownToDouble(required);
    out.deviation_lower_sum = roundDownToDouble(lower_sum);
    out.deviation_upper_sum = roundDownToDouble(upper_sum);

    if (required > upper_sum) {
        out.domain_contradiction_observed = true;
        out.domain_estimate = parent_relaxation;
        out.final_estimate = parent_relaxation;
        out.validation_status =
            "deviation_domain_contradiction_parent_fallback";
        out.valid = true;
        return out;
    }
    long double remaining = std::max(0.0L, required - lower_sum);
    for (const auto& [weight, station] : order) {
        const long double addition = std::min(
            remaining, upper[station] - lower[station]);
        phi += weight * addition;
        remaining -= addition;
        if (remaining <= 0.0L) break;
    }
    if (remaining > 0.0L) {
        out.failure_reason = "continuous_knapsack_fill_incomplete";
        return out;
    }

    const long double domain_estimate =
        static_cast<long double>(child_gamma_lower) +
        static_cast<long double>(options.lambda) * phi;
    out.dispersion_penalty_lower = roundDownToDouble(phi);
    out.weighted_penalty_lower = out.dispersion_penalty_lower;
    out.domain_estimate = roundDownToDouble(domain_estimate);
    if (!std::isfinite(out.domain_estimate)) {
        out.failure_reason = "dispersion_estimate_not_finite";
        return out;
    }
    out.final_estimate = std::max(parent_relaxation, out.domain_estimate);
    out.lift_over_parent = out.final_estimate - parent_relaxation;
    out.dispersion_bound_used = out.domain_estimate > parent_relaxation;
    out.validation_status = "proved_dispersion_lower_bound";
    out.valid = std::isfinite(out.final_estimate) &&
        out.final_estimate >= parent_relaxation;
    if (!out.valid) out.failure_reason = "final_estimate_invalid";
    return out;
}

} // namespace ebrp
