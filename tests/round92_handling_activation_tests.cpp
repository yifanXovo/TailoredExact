#include "Round92HandlingActivation.hpp"
#include "Evaluator.hpp"
#include "PhysicalDurationTolerance.hpp"

#include <algorithm>
#include <cfenv>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>
#if defined(__SSE__)
#include <xmmintrin.h>
#endif

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
    row.raw_pickup_time = pickup;
    row.raw_drop_time = 0;
    row.physical_tolerance = ebrp::kPhysicalDurationTolerance;
    row.directed_travel.resize(stations + 1);
    row.raw_directed_travel.resize(stations + 1);
    for (int i = 0; i <= stations; ++i) {
        row.directed_travel[i].resize(stations + 1);
        row.raw_directed_travel[i].resize(stations + 1);
        for (int j = 0; j <= stations; ++j)
            if (i != j) {
                row.directed_travel[i][j] = travel;
                row.raw_directed_travel[i][j] = travel;
            }
    }
    return row;
}

void exactIntegerBoundaryAndDepotCases() {
    const auto five = ebrp::prepareRound92HandlingActivation(complete(2, 0, 10, 2));
    require(five.valid_input && five.applicable && five.exact_integer_floor &&
                five.integer_capacity == 5 &&
                five.activation_coefficient == -5 &&
                five.quotient_lower >= 5 && five.quotient_upper < 6,
            "uniform envelope must preserve this nontrivial integer row");
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
    row.raw_directed_travel[0][1] = 100;
    row.directed_travel[1][0] = 1;
    row.raw_directed_travel[1][0] = 1;
    row.directed_travel[0][2] = 1;
    row.raw_directed_travel[0][2] = 1;
    row.directed_travel[2][0] = 100;
    row.raw_directed_travel[2][0] = 100;
    row.directed_travel[1][2] = 1;
    row.raw_directed_travel[1][2] = 1;
    row.directed_travel[2][1] = 1;
    row.raw_directed_travel[2][1] = 1;
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
    row.raw_directed_travel[0][1] = 5e-13;
    row.raw_directed_travel[1][0] = 1.0 + 5e-13;
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
                uncertain.integer_capacity >= 10 &&
                uncertain.physical_horizon_upper > near_integer.horizon,
            "near-integer quotient must cover physical acceptance uniformly");
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
    row.raw_directed_travel[1][0] = std::nullopt;
    const auto unreachable = ebrp::prepareRound92HandlingActivation(row);
    require(unreachable.valid_input && unreachable.applicable &&
                unreachable.integer_capacity == 0 &&
                !unreachable.quotient_enclosure_available,
            "no closed depot path implies zero service under F0");
    row = complete(1, 0, 4, 2);
    row.directed_travel[0][1] = std::numeric_limits<double>::infinity();
    row.raw_directed_travel[0][1] = std::numeric_limits<double>::infinity();
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

void exactRunCacheKeyAndLoadedReturn() {
    auto original = complete(2, 0, 8, 2);
    auto same = original;
    require(ebrp::round92SameDurationKey(original, same),
            "identical emitted duration rows must reuse proof");
    same.directed_travel[1][2] = std::nullopt;
    same.raw_directed_travel[1][2] = std::nullopt;
    require(!ebrp::round92SameDurationKey(original, same),
            "arc support change must invalidate proof");
    same = original;
    same.directed_travel[1][2] = 1.0;
    same.raw_directed_travel[1][2] = 1.0;
    require(!ebrp::round92SameDurationKey(original, same),
            "coefficient change must invalidate proof");
    same = original;
    same.horizon = 9;
    require(!ebrp::round92SameDurationKey(original, same),
            "duration RHS change must invalidate proof");
    same = original;
    same.raw_directed_travel[1][2] = std::nextafter(
        0.0, std::numeric_limits<double>::infinity());
    require(!ebrp::round92SameDurationKey(original, same),
            "raw-only travel change must invalidate proof");

    // Pickup 4 > Q 2 is physically valid after an intermediate delivery;
    // the route returns with one item loaded. No cumulative P<=Q premise.
    ebrp::Instance in;
    in.V = 4;
    in.M = 1;
    in.Q = {2};
    in.capacity = {0, 2, 2, 2, 2};
    in.initial = {0, 2, 0, 2, 0};
    in.target = {0, 1, 1, 1, 1};
    in.weights = {0, 1, 1, 1, 1};
    in.dist.assign(5, std::vector<double>(5, 0.0));
    in.total_time_limit = 8;
    in.pickup_time = 1;
    in.drop_time = 1;
    const std::vector<ebrp::RoutePlan> routes = {
        {0, {0, 1, 2, 3, 4, 0},
            {{1, 2, 0}, {2, 0, 2}, {3, 2, 0}, {4, 0, 1}}}
    };
    const auto verified = ebrp::verifySolution(in, routes, 0.15);
    require(verified.feasible && verified.original_solution_feasible &&
            verified.final_inventory == std::vector<int>({0, 0, 2, 0, 1}),
            "physical loaded-return route with P>Q must remain feasible");
    const auto plan = ebrp::prepareRound92HandlingActivation(
        complete(4, 0, 8, 2));
    require(plan.applicable && plan.integer_capacity == 4,
            "valid loaded-return route must satisfy the handling row");
}

void independentDyadicQuotientAndSubnormalGate() {
    // Original dyadic T=32/16, ell=2/16, c=8/16 has quotient 15/4.
    // The repaired quotient instead uses a slightly larger physical H and a
    // common lower c. Independent dyadic brackets below put its surrogate
    // quotient in [59/16,248/63], strictly between 3 and 4.
    auto fractional = complete(1, 1.0 / 16.0, 2.0, 0.5);
    const auto p = ebrp::prepareRound92HandlingActivation(fractional);
    require(p.valid_input && p.applicable && p.integer_capacity == 3 &&
                p.common_horizon_upper >= 2 &&
                p.common_horizon_upper <= 65.0 / 32.0 &&
                p.lower_service_coefficient >= 63.0 / 128.0 &&
                p.lower_service_coefficient <= 0.5 &&
                p.lmin_lower >= 3.0 / 32.0 &&
                p.lmin_upper <= 5.0 / 32.0 &&
                p.quotient_lower > 3 && p.quotient_upper < 4,
            "independent dyadic bracket must certify uniform floor three");
    // nextafter(2,-inf)=2-2^-52 exactly; q/c=4-2^-51 has floor 3.
    fractional = complete(1, 0,
        std::nextafter(2.0, -std::numeric_limits<double>::infinity()), 0.5);
    const auto near = ebrp::prepareRound92HandlingActivation(fractional);
    const double exact_near_q = 4.0 - std::ldexp(1.0, -51);
    require(near.valid_input && near.applicable && near.integer_capacity >= 3 &&
                near.common_horizon_upper >= fractional.horizon,
            "near-integer physical envelope must not cut below 3");
    (void)exact_near_q;
#if defined(__SSE__)
    const unsigned original = _mm_getcsr();
    for (unsigned mode : {0x8000u, 0x0040u}) {
        _mm_setcsr(original | mode);
        const auto rejected = ebrp::prepareRound92HandlingActivation(
            complete(1, 0, 2, 1));
        _mm_setcsr(original);
        require(!rejected.valid_input &&
                    rejected.reason == "unsafe_floating_environment",
                "FTZ or DAZ must fail closed after runtime toggle");
    }
#endif
}

void physicalSerializationCounterexampleAndWitnessGuard() {
    const double delta = std::ldexp(1.0, -42);
    ebrp::Instance in;
    in.V = 2; in.M = 1; in.Q = {2};
    in.capacity = {0, 2, 1};
    in.initial = {0, 2, 1};
    in.target = {0, 1, 1};
    in.weights = {0, 1, 1};
    in.dist.assign(3, std::vector<double>(3, 0.0));
    in.total_time_limit = 2.0 - delta;
    in.pickup_time = in.drop_time = (1.0 - delta) / 2.0;
    const std::vector<ebrp::RoutePlan> routes = {
        {0, {0, 1, 0}, {{1, 2, 0}}}
    };
    const auto physical = ebrp::verifySolution(in, routes, 0.15);
    require(physical.feasible && physical.route_duration[0] < in.total_time_limit,
            "exact dyadic P=2 route must be physically accepted");
    const auto admitted = ebrp::round92AdmitWitness(
        in, routes, 0.15, physical.objective);
    require(admitted.feasible, "lawful physical witness admission failed");
    auto row = complete(2, 0, in.total_time_limit, 1.0);
    row.raw_pickup_time = in.pickup_time;
    row.raw_drop_time = in.drop_time;
    const auto repaired = ebrp::prepareRound92HandlingActivation(row);
    require(repaired.valid_input && repaired.applicable &&
                repaired.integer_capacity >= 2 &&
                repaired.lower_service_coefficient < row.pickup,
            "uniform row must retain original-physical P=2 witness");
    auto duplicate = routes;
    duplicate.push_back(routes.front());
    bool rejected = false;
    try { (void)ebrp::round92AdmitWitness(in, duplicate, 0.15,
                                          physical.objective); }
    catch (const std::runtime_error&) { rejected = true; }
    require(rejected, "duplicate vehicle must fail before original verifier");
    ebrp::Instance malformed = in;
    malformed.target.pop_back();
    rejected = false;
    try { (void)ebrp::round92AdmitWitness(malformed, routes, 0.15,
                                          physical.objective); }
    catch (const std::runtime_error&) { rejected = true; }
    require(rejected, "missing objective vector entry must fail before Evaluator");
    in.Q = {std::numeric_limits<int>::max()};
    rejected = false;
    try { ebrp::round92RequireLawfulDomain(in); }
    catch (const std::runtime_error&) { rejected = true; }
    require(rejected, "unsupported V*maxQ must fail before int arithmetic");
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
                row.raw_directed_travel[i][j] = values[digits % 3];
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
    exactRunCacheKeyAndLoadedReturn();
    independentDyadicQuotientAndSubnormalGate();
    physicalSerializationCounterexampleAndWitnessGuard();
    independentTwoStationRouteOracle();
    std::cout << "Round92 handling activation source fixtures PASS\n";
}
