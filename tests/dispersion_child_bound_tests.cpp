#include "IntervalRowFactory.hpp"

#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::Instance instanceOf(int V) {
    ebrp::Instance instance;
    instance.V = V;
    instance.M = 1;
    instance.target.assign(static_cast<std::size_t>(V + 1), 10);
    instance.target[0] = 0;
    instance.weights.assign(static_cast<std::size_t>(V + 1), 1.0);
    instance.weights[0] = 0.0;
    return instance;
}

ebrp::IntervalDomainSummary domainOf(
    const ebrp::Instance& instance,
    const std::vector<int>& lower,
    const std::vector<int>& upper) {
    ebrp::IntervalDomainSummary domain;
    domain.y_lower = lower;
    domain.y_upper = upper;
    domain.e_lower.assign(static_cast<std::size_t>(instance.V + 1), 0.0);
    domain.e_upper.assign(static_cast<std::size_t>(instance.V + 1), 0.0);
    for (int i = 1; i <= instance.V; ++i) {
        const double target = instance.target[i];
        const double lo = lower[i] / target;
        const double hi = upper[i] / target;
        domain.s_lower += lo;
        domain.s_upper += hi;
        domain.e_lower[i] = lo > 1.0 ? lo - 1.0
            : (hi < 1.0 ? 1.0 - hi : 0.0);
        domain.e_upper[i] = std::max(std::fabs(lo - 1.0),
                                     std::fabs(hi - 1.0));
    }
    return domain;
}

ebrp::ChildDomainEstimate estimate(
    ebrp::Instance instance,
    ebrp::IntervalDomainSummary domain,
    double L,
    double lambda = 0.15,
    double parent = 0.0) {
    ebrp::SolveOptions options;
    options.lambda = lambda;
    return ebrp::computeDispersionCoupledChildEstimate(
        instance, options, domain, L, parent);
}

void testHandCalculation() {
    auto instance = instanceOf(3);
    instance.weights = {0.0, 1.0, 2.0, 3.0};
    auto domain = domainOf(instance, {0, 0, 0, 0}, {0, 20, 20, 20});
    domain.s_lower = 3.0;
    domain.e_lower = {0.0, 0.0, 0.0, 0.0};
    domain.e_upper = {0.0, 1.0, 1.0, 1.0};
    const auto out = estimate(instance, domain, 0.1);
    require(out.valid, out.failure_reason);
    require(out.required_deviation <= 0.45 &&
            out.required_deviation > 0.449999999999,
            "aggregate deviation calculation");
    require(out.dispersion_penalty_lower <= 0.45 &&
            out.dispersion_penalty_lower > 0.449999999999,
            "continuous knapsack calculation");
    require(out.domain_estimate <= 0.1675 &&
            out.domain_estimate > 0.167499999999,
            "hand objective bound");
}

void testDegenerateAndZeroCases() {
    auto one = instanceOf(1);
    auto one_domain = domainOf(one, {0, 5}, {0, 15});
    require(estimate(one, one_domain, 0.2, 0.15, 0.3).final_estimate == 0.3,
            "V=1 must retain parent");
    auto instance = instanceOf(3);
    auto domain = domainOf(instance, {0, 8, 9, 10}, {0, 12, 11, 10});
    require(estimate(instance, domain, 0.2, 0.0).valid,
            "lambda zero rejected");
    require(estimate(instance, domain, 0.0).valid, "L zero rejected");
    domain.s_lower = 0.0;
    require(estimate(instance, domain, 0.2).valid, "S lower zero rejected");
}

void testWeightsAndTies() {
    auto instance = instanceOf(3);
    auto domain = domainOf(instance, {0, 0, 0, 0}, {0, 20, 20, 20});
    domain.s_lower = 3.0;
    domain.e_lower = {0.0, 0.0, 0.0, 0.0};
    domain.e_upper = {0.0, 1.0, 1.0, 1.0};
    instance.weights = {0.0, 0.0, 2.0, 3.0};
    require(estimate(instance, domain, 0.1).dispersion_penalty_lower == 0.0,
            "zero-weight capacity not filled first");
    instance.weights = {0.0, 2.0, 1.0, 3.0};
    const auto arbitrary = estimate(instance, domain, 0.1);
    require(arbitrary.dispersion_penalty_lower <= 0.45,
            "weights were not sorted");
    instance.weights = {0.0, 1.0, 1.0, 1.0};
    const auto first = estimate(instance, domain, 0.1);
    const auto second = estimate(instance, domain, 0.1);
    require(first.domain_estimate == second.domain_estimate,
            "tie handling is nondeterministic");
}

void testRequiredDeviationRegions() {
    auto instance = instanceOf(3);
    auto domain = domainOf(instance, {0, 8, 8, 8}, {0, 12, 12, 12});
    const auto below = estimate(instance, domain, 0.0);
    require(below.valid && below.required_deviation == 0.0,
            "D below lower sum");
    const auto inside = estimate(instance, domain, 0.1);
    require(inside.valid && !inside.domain_contradiction_observed,
            "D inside deviation range");
    domain.s_lower = 4.0 / 3.0;
    domain.e_upper = {0.0, 0.1, 0.1, 0.1};
    const auto at_upper = estimate(instance, domain, 0.15);
    require(at_upper.valid && !at_upper.domain_contradiction_observed,
            "D at upper limit");
    const auto above = estimate(instance, domain, 0.2, 0.15, 0.07);
    require(above.valid && above.domain_contradiction_observed &&
            above.final_estimate == 0.07,
            "D above upper must retain parent without pruning");
}

void testInvalidInputsFailClosed() {
    auto instance = instanceOf(3);
    auto domain = domainOf(instance, {0, 8, 8, 8}, {0, 12, 12, 12});
    auto inconsistent = domain;
    inconsistent.e_upper[2] = -1.0;
    require(!estimate(instance, inconsistent, 0.1).valid,
            "inconsistent domain accepted");
    auto nonfinite = domain;
    nonfinite.s_lower = std::numeric_limits<double>::infinity();
    require(!estimate(instance, nonfinite, 0.1).valid,
            "nonfinite domain accepted");
    instance.weights[1] = -1.0;
    require(!estimate(instance, domain, 0.1).valid,
            "negative weight accepted");
    instance.weights[1] = 1.0;
    require(!estimate(instance, domain, 0.1, -0.1).valid,
            "negative lambda accepted");
}

double exactObjective(const ebrp::Instance& instance,
                      const std::vector<int>& y,
                      double lambda,
                      double* gini) {
    std::vector<double> ratios(static_cast<std::size_t>(instance.V + 1));
    double S = 0.0;
    double P = 0.0;
    for (int i = 1; i <= instance.V; ++i) {
        ratios[i] = static_cast<double>(y[i]) / instance.target[i];
        S += ratios[i];
        P += instance.weights[i] * std::fabs(ratios[i] - 1.0);
    }
    double H = 0.0;
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            H += std::fabs(ratios[i] - ratios[j]);
        }
    }
    *gini = S > 0.0 ? H / (instance.V * S) : 0.0;
    return *gini + lambda * P;
}

void testExhaustiveToyOptima() {
    for (int pattern = 0; pattern < 8; ++pattern) {
        auto instance = instanceOf(3);
        instance.target = {0, 2, 3, 4};
        instance.weights = {0.0, pattern % 2 ? 0.0 : 1.0,
                            1.0 + (pattern % 3), 2.5};
        std::vector<int> lower = {0, pattern % 2, 1, 2};
        std::vector<int> upper = {0, 4, 5, 6};
        auto domain = domainOf(instance, lower, upper);
        const double L = 0.025 * pattern;
        const auto out = estimate(instance, domain, L, 0.15, -0.01);
        require(out.valid, "toy bound invalid: " + out.failure_reason);
        double optimum = std::numeric_limits<double>::infinity();
        for (int a = lower[1]; a <= upper[1]; ++a) {
            for (int b = lower[2]; b <= upper[2]; ++b) {
                for (int c = lower[3]; c <= upper[3]; ++c) {
                    const std::vector<int> y = {0, a, b, c};
                    double G = 0.0;
                    const double objective = exactObjective(
                        instance, y, 0.15, &G);
                    if (G + 1e-15 >= L) optimum = std::min(optimum, objective);
                }
            }
        }
        if (std::isfinite(optimum)) {
            require(out.final_estimate <= optimum + 1e-15,
                    "candidate estimate exceeds exhaustive child optimum");
        } else {
            require(out.domain_contradiction_observed ||
                    out.final_estimate <= 0.0,
                    "empty toy child caused unproved estimate");
        }
        require(out.final_estimate >= -0.01,
                "candidate estimate below parent");
    }
}

void testOutwardRounding() {
    auto instance = instanceOf(3);
    instance.weights = {0.0, 0.1, 0.2, 0.3};
    auto domain = domainOf(instance, {0, 0, 0, 0}, {0, 20, 20, 20});
    domain.s_lower = 1.0 / 3.0;
    domain.e_lower = {0.0, 0.0, 0.0, 0.0};
    domain.e_upper = {0.0, 1.0, 1.0, 1.0};
    const double L = 0.1;
    const auto out = estimate(instance, domain, L, 0.15);
    const long double D = 3.0L * static_cast<long double>(L) *
        static_cast<long double>(domain.s_lower) / 2.0L;
    const long double mathematical = static_cast<long double>(L) +
        0.15L * 0.1L * D;
    require(static_cast<long double>(out.domain_estimate) <= mathematical,
            "floating conversion rounded the proved bound upward");
}

} // namespace

int main() {
    try {
        testHandCalculation();
        testDegenerateAndZeroCases();
        testWeightsAndTies();
        testRequiredDeviationRegions();
        testInvalidInputsFailClosed();
        testExhaustiveToyOptima();
        testOutwardRounding();
        std::cout << "DispersionChildBoundTests: 20 requirements passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "DispersionChildBoundTests failure: " << error.what()
                  << '\n';
        return 1;
    }
}
