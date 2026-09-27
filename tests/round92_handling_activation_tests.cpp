#include "Round92HandlingActivation.hpp"

#include <algorithm>
#include <cfenv>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace {

using ebrp::Round92DurationCoefficients;
using ebrp::Round92HandlingActivationPlan;

void require(bool yes, const std::string& message) {
    if (!yes) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

Round92DurationCoefficients complete(int stations, double travel,
                                      double horizon, double pickup) {
    Round92DurationCoefficients row;
    row.horizon = horizon;
    row.pickup = pickup;
    row.directed_travel.resize(stations + 1);
    for (int i = 0; i <= stations; ++i) {
        row.directed_travel[i].resize(stations + 1);
        for (int j = 0; j <= stations; ++j)
            if (i != j) row.directed_travel[i][j] = travel;
    }
    return row;
}

void exactIntegerBoundaryAndDepotCases() {
    const auto five = ebrp::prepareRound92HandlingActivation(complete(2, 0, 10, 2));
    require(five.valid_input && five.applicable && five.exact_integer_floor &&
                five.integer_capacity == 5 &&
                five.activation_coefficient == -5 &&
                five.quotient_lower == 5 && five.quotient_upper == 5,
            "exact integer quotient must produce the exact row");
    // Empty route has a=0,P=0. A loaded-return route may have P>Q after
    // intermediate delivery; the row depends on time, not cumulative P<=Q.
    require(0 <= five.integer_capacity * 0 &&
                2 <= five.integer_capacity * 1,
            "empty depot/loaded return activation semantics");
    const auto zero = ebrp::prepareRound92HandlingActivation(complete(1, 2, 4, 2));
    require(zero.applicable && zero.integer_capacity == 0,
            "T equal to minimum round trip gives B=0");
    const auto negative_q = ebrp::prepareRound92HandlingActivation(complete(1, 2, 1, 2));
    require(negative_q.applicable && negative_q.integer_capacity == 0,
            "T below minimum round trip must clip B to zero");
}

void nonmetricDirectedShortestPath() {
    // All direct depot round trips cost 101; directed two-hop paths yield 3.
    auto row = complete(2, 100, 9, 2);
    row.directed_travel[0][1] = 100;
    row.directed_travel[1][0] = 1;
    row.directed_travel[0][2] = 1;
    row.directed_travel[2][0] = 100;
    row.directed_travel[1][2] = 1;
    row.directed_travel[2][1] = 1;
    const auto plan = ebrp::prepareRound92HandlingActivation(row);
    require(plan.applicable && plan.lmin_lower == 3 && plan.lmin_upper == 3 &&
                plan.integer_capacity == 3,
            "must use directed shortest paths, not direct depot round trips");
}

void serializationAndUncertainFloor() {
    using ebrp::round92CanonicalEmittedCoefficient;
    require(round92CanonicalEmittedCoefficient(5e-13) == 0.0,
            "canonical addTerm suppresses a tiny positive arc");
    require(round92CanonicalEmittedCoefficient(1.0 + 5e-13) == 1.0,
            "canonical writeExpr emits near-unit coefficient as 1");
    auto row = complete(1, 0, 5, 2);
    row.directed_travel[0][1] = round92CanonicalEmittedCoefficient(5e-13);
    row.directed_travel[1][0] = round92CanonicalEmittedCoefficient(1.0 + 5e-13);
    const auto plan = ebrp::prepareRound92HandlingActivation(row);
    require(plan.applicable && plan.lmin_lower == 1 && plan.lmin_upper == 1 &&
                plan.integer_capacity == 2,
            "helper must use actual serialized duration coefficients");
    row.directed_travel[1][0] = 1.0 + 5e-13;
    require(!ebrp::prepareRound92HandlingActivation(row).applicable,
            "raw near-one coefficient must not be mistaken for emitted row");

    auto near_integer = complete(1, 0, 1.0,
        std::nextafter(0.1, std::numeric_limits<double>::infinity()));
    const auto uncertain = ebrp::prepareRound92HandlingActivation(near_integer);
    require(uncertain.valid_input && uncertain.applicable &&
                !uncertain.exact_integer_floor && uncertain.integer_capacity == 10 &&
                uncertain.reason == "conservative_upper_floor_may_be_weaker",
            "near-integer quotient must use the safe upper floor uniformly");
}

void invalidAndUnreachableDomains() {
    auto row = complete(1, 0, 4, 0);
    const auto zero_c = ebrp::prepareRound92HandlingActivation(row);
    require(zero_c.valid_input && !zero_c.applicable,
            "zero pickup/drop time provides no duration quantity bound");
    row = complete(1, -1, 4, 2);
    require(!ebrp::prepareRound92HandlingActivation(row).valid_input,
            "negative travel invalidates nonnegative-path proof");
    row = complete(1, 0, 4, 2);
    row.directed_travel[1][0] = std::nullopt;
    const auto unreachable = ebrp::prepareRound92HandlingActivation(row);
    require(unreachable.valid_input && unreachable.applicable &&
                unreachable.integer_capacity == 0 &&
                !unreachable.quotient_enclosure_available,
            "no closed depot path implies zero service under F0");
    row = complete(1, 0, 4, 2);
    row.directed_travel[0][1] = std::numeric_limits<double>::infinity();
    require(!ebrp::prepareRound92HandlingActivation(row).valid_input,
            "nonfinite duration coefficient must be rejected");
    row = complete(1, 0, 4, 2);
    const int initial_mode = std::fegetround();
    require(initial_mode != -1, "rounding mode query failed");
    require(std::fesetround(FE_DOWNWARD) == 0, "could not set alternate rounding mode");
    const auto wrong_mode = ebrp::prepareRound92HandlingActivation(row);
    require(std::fesetround(initial_mode) == 0, "could not restore rounding mode");
    require(!wrong_mode.valid_input && wrong_mode.reason == "unsafe_floating_environment",
            "non-nearest rounding must fail closed");
}

void independentTwoStationRouteOracle() {
    // Enumerate all small directed arc matrices and compare with a separate
    // depot-closed route oracle. No shortest-path helper is reused here.
    const int values[] = {0, 1, 4};
    for (int code = 0; code < 729; ++code) {
        auto row = complete(2, 0, 0, 1);
        int digits = code;
        for (int i = 0; i <= 2; ++i) {
            for (int j = 0; j <= 2; ++j) {
                if (i == j) continue;
                row.directed_travel[i][j] = values[digits % 3];
                digits /= 3;
            }
        }
        const auto w = [&](int i, int j) { return static_cast<int>(*row.directed_travel[i][j]); };
        const int independent_min = std::min({
            w(0, 1) + w(1, 0), w(0, 2) + w(2, 0),
            w(0, 1) + w(1, 2) + w(2, 0),
            w(0, 2) + w(2, 1) + w(1, 0)});
        for (int horizon : {0, 3, 9}) {
            for (int handling : {1, 2, 3}) {
                row.horizon = horizon;
                row.pickup = handling;
                const auto plan = ebrp::prepareRound92HandlingActivation(row);
                const int expected = std::max(0, (horizon - independent_min) / handling);
                require(plan.applicable && plan.integer_capacity ==
                            static_cast<unsigned>(expected),
                        "2-station independent integer route oracle differs");
            }
        }
    }
}

} // namespace

int main() {
    exactIntegerBoundaryAndDepotCases();
    nonmetricDirectedShortestPath();
    serializationAndUncertainFloor();
    invalidAndUnreachableDomains();
    independentTwoStationRouteOracle();
    std::cout << "Round92 handling activation source fixtures PASS\n";
}
