#include "ConnectivityFlow.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using ebrp::ConnectivityFlowProjection;
using ebrp::ConnectivityFlowVariant;
using Arc = std::pair<int, int>;
using ArcValues = std::map<Arc, double>;

constexpr double kTolerance = 1e-12;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

double value(const ArcValues& values, int from, int to) {
    const auto found = values.find({from, to});
    return found == values.end() ? 0.0 : found->second;
}

ArcValues projectionValues(const ConnectivityFlowProjection& projection) {
    ArcValues values;
    for (const auto& arc : projection.arc_values) {
        values[{arc.from, arc.to}] = arc.value;
    }
    return values;
}

std::set<int> visitedStations(const std::vector<int>& route) {
    std::set<int> visited;
    if (route.size() <= 1) return visited;
    for (std::size_t position = 1; position + 1 < route.size(); ++position) {
        visited.insert(route[position]);
    }
    return visited;
}

ArcValues routeArcValues(const std::vector<int>& route) {
    ArcValues x;
    for (std::size_t position = 1; position < route.size(); ++position) {
        const int from = route[position - 1];
        const int to = route[position];
        if (from != to) x[{from, to}] = 1.0;
    }
    return x;
}

bool assignmentFeasible(ConnectivityFlowVariant variant,
                        int station_count,
                        const std::vector<int>& route,
                        const ArcValues& flow) {
    if (variant == ConnectivityFlowVariant::Off) return flow.empty();
    const ArcValues x = routeArcValues(route);
    const std::set<int> visited = visitedStations(route);

    for (const auto& entry : flow) {
        if (!ebrp::hasConnectivityFlowColumn(
                variant, station_count, entry.first.first, entry.first.second) &&
            std::fabs(entry.second) > kTolerance) {
            return false;
        }
    }
    for (int from = 0; from <= station_count; ++from) {
        for (int to = 0; to <= station_count; ++to) {
            if (!ebrp::hasConnectivityFlowColumn(
                    variant, station_count, from, to)) {
                continue;
            }
            const double f = value(flow, from, to);
            const double arc = value(x, from, to);
            const auto upper = ebrp::connectivityFlowArcUpperBound(
                variant, station_count, from, to);
            if (!upper.has_value() || f < -kTolerance ||
                f > *upper * arc + kTolerance) {
                return false;
            }
            if (ebrp::connectivityFlowHasLowerLinks(variant) &&
                f + kTolerance < arc) {
                return false;
            }
        }
    }

    for (int station = 1; station <= station_count; ++station) {
        double balance = 0.0;
        for (int other = 0; other <= station_count; ++other) {
            if (other == station) continue;
            if (ebrp::hasConnectivityFlowColumn(
                    variant, station_count, other, station)) {
                balance += value(flow, other, station);
            }
            if (ebrp::hasConnectivityFlowColumn(
                    variant, station_count, station, other)) {
                balance -= value(flow, station, other);
            }
        }
        const double z = visited.count(station) != 0 ? 1.0 : 0.0;
        if (std::fabs(balance - z) > kTolerance) return false;
    }

    double depot_supply = 0.0;
    for (int station = 1; station <= station_count; ++station) {
        depot_supply += value(flow, 0, station);
        if (ebrp::connectivityFlowUsesReturnColumns(variant)) {
            depot_supply -= value(flow, station, 0);
        }
    }
    const double visit_count = static_cast<double>(visited.size());
    if (std::fabs(depot_supply - visit_count) > kTolerance) return false;

    if (ebrp::connectivityFlowHasStartCoupling(variant)) {
        for (int station = 1; station <= station_count; ++station) {
            const double f = value(flow, 0, station);
            const double departure = value(x, 0, station);
            if (f > visit_count + kTolerance) return false;
            if (f + kTolerance <
                    visit_count - station_count * (1.0 - departure)) {
                return false;
            }
        }
    }
    return true;
}

std::vector<std::vector<int>> elementaryRoutes(int station_count) {
    std::vector<std::vector<int>> routes{{0, 0}};
    std::vector<int> chosen;
    std::vector<bool> used(static_cast<std::size_t>(station_count + 1), false);
    for (int target = 1; target <= station_count; ++target) {
        std::function<void()> generate = [&]() {
            if (static_cast<int>(chosen.size()) == target) {
                std::vector<int> route{0};
                route.insert(route.end(), chosen.begin(), chosen.end());
                route.push_back(0);
                routes.push_back(std::move(route));
                return;
            }
            for (int station = 1; station <= station_count; ++station) {
                if (used[static_cast<std::size_t>(station)]) continue;
                used[static_cast<std::size_t>(station)] = true;
                chosen.push_back(station);
                generate();
                chosen.pop_back();
                used[static_cast<std::size_t>(station)] = false;
            }
        };
        generate();
    }
    return routes;
}

const std::array<ConnectivityFlowVariant, 5> kVariants = {
    ConnectivityFlowVariant::Off,
    ConnectivityFlowVariant::Round20Current,
    ConnectivityFlowVariant::ZeroReturn,
    ConnectivityFlowVariant::Normalized,
    ConnectivityFlowVariant::NormalizedStartCoupled,
};

void testVariantParsingAndResolution() {
    const std::array<std::pair<const char*, ConnectivityFlowVariant>, 9> cases = {{
        {"off", ConnectivityFlowVariant::Off},
        {"round20-current", ConnectivityFlowVariant::Round20Current},
        {"zero-return", ConnectivityFlowVariant::ZeroReturn},
        {"normalized", ConnectivityFlowVariant::Normalized},
        {"normalized-start-coupled",
         ConnectivityFlowVariant::NormalizedStartCoupled},
        {"F0", ConnectivityFlowVariant::Round20Current},
        {"f1", ConnectivityFlowVariant::ZeroReturn},
        {"F2", ConnectivityFlowVariant::Normalized},
        {"f3", ConnectivityFlowVariant::NormalizedStartCoupled},
    }};
    for (const auto& item : cases) {
        ConnectivityFlowVariant parsed = ConnectivityFlowVariant::Off;
        std::string failure;
        require(ebrp::parseConnectivityFlowVariant(
                    item.first, parsed, &failure),
                std::string("failed to parse ") + item.first);
        require(parsed == item.second && failure.empty(),
                std::string("wrong parsed variant for ") + item.first);
        require(std::string(ebrp::connectivityFlowVariantName(parsed)) !=
                    "invalid",
                "parsed variant has no canonical name");
    }
    ConnectivityFlowVariant ignored = ConnectivityFlowVariant::Off;
    std::string failure;
    require(!ebrp::parseConnectivityFlowVariant(
                "instance-specific", ignored, &failure) && !failure.empty(),
            "unknown variants must fail closed");

    auto resolution = ebrp::resolveConnectivityFlowVariant(false, "");
    require(resolution.valid && resolution.variant == ConnectivityFlowVariant::Off &&
                resolution.used_legacy_switch,
            "legacy false must preserve no-flow semantics");
    resolution = ebrp::resolveConnectivityFlowVariant(true, "");
    require(resolution.valid &&
                resolution.variant == ConnectivityFlowVariant::Round20Current &&
                resolution.resolved == "round20-current",
            "legacy true must reproduce F0");
    resolution = ebrp::resolveConnectivityFlowVariant(false, "normalized");
    require(resolution.valid &&
                resolution.variant == ConnectivityFlowVariant::Normalized &&
                !resolution.used_legacy_switch,
            "explicit F2 did not resolve");
    resolution = ebrp::resolveConnectivityFlowVariant(true, "zero-return");
    require(!resolution.valid && !resolution.failure_reason.empty(),
            "conflicting legacy and explicit variants must fail closed");
}

void testColumnTopologyAndBounds() {
    for (int v = 1; v <= 4; ++v) {
        require(!ebrp::hasConnectivityFlowColumn(
                    ConnectivityFlowVariant::Off, v, 0, 1),
                "off variant unexpectedly has a column");
        for (int i = 1; i <= v; ++i) {
            require(ebrp::hasConnectivityFlowColumn(
                        ConnectivityFlowVariant::Round20Current, v, i, 0),
                    "F0 return column missing");
            for (ConnectivityFlowVariant variant : {
                     ConnectivityFlowVariant::ZeroReturn,
                     ConnectivityFlowVariant::Normalized,
                     ConnectivityFlowVariant::NormalizedStartCoupled}) {
                require(!ebrp::hasConnectivityFlowColumn(variant, v, i, 0),
                        "normalized variant retained a return column");
                require(ebrp::hasConnectivityFlowColumn(variant, v, 0, i),
                        "normalized variant lost a departure column");
            }
        }
        for (int i = 1; i <= v; ++i) {
            for (int j = 1; j <= v; ++j) {
                if (i == j) continue;
                const auto f1 = ebrp::connectivityFlowArcUpperBound(
                    ConnectivityFlowVariant::ZeroReturn, v, i, j);
                const auto f2 = ebrp::connectivityFlowArcUpperBound(
                    ConnectivityFlowVariant::Normalized, v, i, j);
                require(f1.has_value() && std::fabs(*f1 - v) < kTolerance,
                        "F1 internal upper bound changed from V");
                require(f2.has_value() && std::fabs(*f2 - (v - 1)) < kTolerance,
                        "F2 internal upper bound is not V-1");
            }
        }
    }
}

void testTheoreticalCounts() {
    const auto f0 = ebrp::connectivityFlowTheoreticalCounts(
        ConnectivityFlowVariant::Round20Current, 20, 3);
    const auto f1 = ebrp::connectivityFlowTheoreticalCounts(
        ConnectivityFlowVariant::ZeroReturn, 20, 3);
    const auto f2 = ebrp::connectivityFlowTheoreticalCounts(
        ConnectivityFlowVariant::Normalized, 20, 3);
    const auto f3 = ebrp::connectivityFlowTheoreticalCounts(
        ConnectivityFlowVariant::NormalizedStartCoupled, 20, 3);
    require(f0.valid && f0.columns == 1260 && f0.total_rows == 1323 &&
                f0.total_nonzeros == 5160,
            "wrong V20/M3 F0 counts");
    require(f1.valid && f1.columns == 1200 && f1.total_rows == 1263 &&
                f1.total_nonzeros == 4920,
            "wrong V20/M3 F1 counts");
    require(f2.valid && f2.columns == 1200 && f2.total_rows == 2463 &&
                f2.total_nonzeros == 7320,
            "wrong V20/M3 F2 counts");
    require(f3.valid && f3.columns == 1200 && f3.total_rows == 2583 &&
                f3.total_nonzeros == 9900 &&
                f3.start_upper_rows == 60 && f3.start_lower_rows == 60,
            "wrong V20/M3 F3 counts");

    for (int v = 1; v <= 4; ++v) {
        for (int m = 1; m <= 3; ++m) {
            for (ConnectivityFlowVariant variant : kVariants) {
                const auto counts = ebrp::connectivityFlowTheoreticalCounts(
                    variant, v, m);
                require(counts.valid, "valid dimensions rejected by counter");
                long long columns = 0;
                for (int k = 0; k < m; ++k) {
                    (void)k;
                    for (int i = 0; i <= v; ++i) {
                        for (int j = 0; j <= v; ++j) {
                            if (ebrp::hasConnectivityFlowColumn(
                                    variant, v, i, j)) {
                                ++columns;
                            }
                        }
                    }
                }
                require(counts.columns == columns,
                        "theoretical column count differs from topology");
                require(counts.total_rows == counts.upper_link_rows +
                            counts.lower_link_rows +
                            counts.station_balance_rows +
                            counts.depot_balance_rows +
                            counts.start_upper_rows + counts.start_lower_rows,
                        "row-family counts do not sum to total");
            }
        }
    }
    require(!ebrp::connectivityFlowTheoreticalCounts(
                 ConnectivityFlowVariant::Normalized, 0, 1).valid,
            "zero stations must fail count construction");
}

void testExhaustiveCanonicalProjection() {
    const std::array<std::size_t, 5> expected_route_counts = {0, 2, 5, 16, 65};
    for (int v = 1; v <= 4; ++v) {
        const auto routes = elementaryRoutes(v);
        require(routes.size() == expected_route_counts[static_cast<std::size_t>(v)],
                "elementary route enumeration is incomplete");
        for (const auto& route : routes) {
            const int s = static_cast<int>(visitedStations(route).size());
            for (ConnectivityFlowVariant variant : kVariants) {
                const ConnectivityFlowProjection projection =
                    ebrp::buildCanonicalConnectivityFlowProjection(
                        variant, v, route);
                require(projection.valid &&
                            projection.visited_station_count == s,
                        "canonical route projection failed");
                const ArcValues flow = projectionValues(projection);
                require(assignmentFeasible(variant, v, route, flow),
                        "canonical projection violates its formulation");
                if (variant == ConnectivityFlowVariant::Off) {
                    require(flow.empty(), "off projection created flow values");
                    continue;
                }
                for (int position = 0; position < s; ++position) {
                    require(std::fabs(value(
                                flow, route[static_cast<std::size_t>(position)],
                                route[static_cast<std::size_t>(position + 1)]) -
                                (s - position)) < kTolerance,
                            "canonical remaining-visit flow is incorrect");
                }
                if (s > 0) {
                    const int last = route[static_cast<std::size_t>(s)];
                    require(std::fabs(value(flow, last, 0)) < kTolerance,
                            "canonical return flow is not zero");
                }
            }
        }
    }
}

void testDominanceAndCirculation() {
    require(ebrp::connectivityFlowCanEmbedInto(
                ConnectivityFlowVariant::NormalizedStartCoupled,
                ConnectivityFlowVariant::Normalized) &&
                ebrp::connectivityFlowCanEmbedInto(
                    ConnectivityFlowVariant::Normalized,
                    ConnectivityFlowVariant::ZeroReturn) &&
                ebrp::connectivityFlowCanEmbedInto(
                    ConnectivityFlowVariant::ZeroReturn,
                    ConnectivityFlowVariant::Round20Current) &&
                !ebrp::connectivityFlowCanEmbedInto(
                    ConnectivityFlowVariant::Round20Current,
                    ConnectivityFlowVariant::Normalized),
            "variant dominance chain is incorrect");

    for (int v = 1; v <= 4; ++v) {
        for (const auto& route : elementaryRoutes(v)) {
            const int s = static_cast<int>(visitedStations(route).size());
            const ArcValues f3 = projectionValues(
                ebrp::buildCanonicalConnectivityFlowProjection(
                    ConnectivityFlowVariant::NormalizedStartCoupled, v, route));
            require(assignmentFeasible(
                        ConnectivityFlowVariant::Normalized, v, route, f3) &&
                        assignmentFeasible(
                            ConnectivityFlowVariant::ZeroReturn, v, route, f3) &&
                        assignmentFeasible(
                            ConnectivityFlowVariant::Round20Current, v, route, f3),
                    "F3 projection did not embed through F2/F1/F0");

            const ArcValues f2 = projectionValues(
                ebrp::buildCanonicalConnectivityFlowProjection(
                    ConnectivityFlowVariant::Normalized, v, route));
            require(assignmentFeasible(
                        ConnectivityFlowVariant::ZeroReturn, v, route, f2) &&
                        assignmentFeasible(
                            ConnectivityFlowVariant::Round20Current, v, route, f2),
                    "F2 projection did not embed through F1/F0");

            ArcValues f1 = projectionValues(
                ebrp::buildCanonicalConnectivityFlowProjection(
                    ConnectivityFlowVariant::ZeroReturn, v, route));
            require(assignmentFeasible(
                        ConnectivityFlowVariant::Round20Current, v, route, f1),
                    "F1 did not embed in F0 with zero return flow");

            if (s > 0 && s < v) {
                ArcValues circulated = projectionValues(
                    ebrp::buildCanonicalConnectivityFlowProjection(
                        ConnectivityFlowVariant::Round20Current, v, route));
                const double circulation = 0.5;
                for (std::size_t position = 1; position < route.size();
                     ++position) {
                    circulated[{route[position - 1], route[position]}] +=
                        circulation;
                }
                require(assignmentFeasible(
                            ConnectivityFlowVariant::Round20Current,
                            v, route, circulated),
                        "valid F0 depot-cycle circulation was rejected");
                const int last = route[static_cast<std::size_t>(s)];
                require(value(circulated, last, 0) > 0.0,
                        "F0 circulation did not create positive return flow");

                for (std::size_t position = 1; position + 1 < route.size();
                     ++position) {
                    f1[{route[position - 1], route[position]}] += circulation;
                }
                require(!assignmentFeasible(
                            ConnectivityFlowVariant::ZeroReturn, v, route, f1),
                        "F1 retained the F0 route-cycle degree of freedom");
            }
            if (s == v && s > 0) {
                ArcValues over = projectionValues(
                    ebrp::buildCanonicalConnectivityFlowProjection(
                        ConnectivityFlowVariant::Round20Current, v, route));
                for (std::size_t position = 1; position < route.size();
                     ++position) {
                    over[{route[position - 1], route[position]}] += 0.1;
                }
                require(!assignmentFeasible(
                            ConnectivityFlowVariant::Round20Current,
                            v, route, over),
                        "full route incorrectly admitted positive circulation");
            }
        }
    }
}

void testInvalidRoutesFailClosed() {
    for (ConnectivityFlowVariant variant : kVariants) {
        require(!ebrp::buildCanonicalConnectivityFlowProjection(
                     variant, 3, {}).valid,
                "empty route accepted");
        require(!ebrp::buildCanonicalConnectivityFlowProjection(
                     variant, 3, {1, 0}).valid,
                "non-depot start accepted");
        require(!ebrp::buildCanonicalConnectivityFlowProjection(
                     variant, 3, {0, 1}).valid,
                "non-depot end accepted");
        require(!ebrp::buildCanonicalConnectivityFlowProjection(
                     variant, 3, {0, 1, 1, 0}).valid,
                "non-elementary route accepted");
        require(!ebrp::buildCanonicalConnectivityFlowProjection(
                     variant, 3, {0, 4, 0}).valid,
                "out-of-range station accepted");
        require(ebrp::buildCanonicalConnectivityFlowProjection(
                    variant, 1, {0}).valid &&
                    ebrp::buildCanonicalConnectivityFlowProjection(
                        variant, 1, {0, 0}).valid,
                "unused vehicle representation rejected");
    }
}

} // namespace

int main() {
    try {
        testVariantParsingAndResolution();
        testColumnTopologyAndBounds();
        testTheoreticalCounts();
        testExhaustiveCanonicalProjection();
        testDominanceAndCirculation();
        testInvalidRoutesFailClosed();
        std::cout << "ConnectivityFlowTests: 6 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ConnectivityFlowTests failed: " << error.what() << '\n';
        return 1;
    }
}
