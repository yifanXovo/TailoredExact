#include "Round50IntervalMip.hpp"
#include "Round51IntervalMip.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

template <class Fn>
void requireThrows(Fn fn, const std::string& message) {
    try {
        fn();
    } catch (const std::runtime_error&) {
        return;
    }
    throw std::runtime_error(message);
}

} // namespace

int main() {
    try {
        using namespace ebrp;
        require(round51SubsetDurationBigM(37.5) == 37.5,
                "positive TSP bound is the row-specific M");
        require(round51SubsetDurationBigM(-0.5e-9) == 0.0,
                "tiny negative roundoff maps to zero");
        requireThrows([] { round51SubsetDurationBigM(-2e-9); },
                      "negative TSP bound must fail closed");
        requireThrows([] {
            round51SubsetDurationBigM(
                std::numeric_limits<double>::infinity());
        }, "infinite TSP bound must fail closed");
        requireThrows([] {
            round51SubsetDurationBigM(
                std::numeric_limits<double>::quiet_NaN());
        }, "NaN TSP bound must fail closed");

        const auto row = round51SubsetDurationRowValues(37.5, 2850.0, 3);
        require(row.big_m == 37.5 && row.visit_coefficient == 37.5,
                "target visit coefficient equals M_S");
        require(std::fabs(row.rhs - (2850.0 - 37.5 + 3.0 * 37.5)) <
                    1e-12,
                "target RHS matches proved formula exactly");
        requireThrows([] {
            round51SubsetDurationRowValues(1.0, 2850.0, 0);
        }, "empty subsets cannot construct a target row");
        // Exhaust the two proof cases over representative subset sizes and
        // nonnegative tour bounds. For r>=1, the duration row gives lhs<=T;
        // for r=0, the intended subset row gives lhs<=T-tsp[S].
        for (int size = 1; size <= 12; ++size) {
            for (double tsp : {0.0, 1.0, 37.5, 2849.0, 4000.0}) {
                const auto values =
                    round51SubsetDurationRowValues(tsp, 2850.0, size);
                for (int absent = 0; absent <= size; ++absent) {
                    const double rhs_after_moving_visits =
                        2850.0 - tsp + values.big_m * absent;
                    const double implied_lhs_upper = absent == 0
                        ? 2850.0 - tsp : 2850.0;
                    require(implied_lhs_upper <=
                                rhs_after_moving_visits + 1e-12,
                            "exhaustive integer proof-case validity");
                }
            }
        }

        const auto historical =
            parseRound50IntervalMipPolicy("interval-mip-v0");
        const auto m1 =
            parseRound50IntervalMipPolicy("m1-tight-big-m-v0");
        const auto m1_alias =
            parseRound50IntervalMipPolicy("m1-v0-cardinality");
        const auto m1_s1 =
            parseRound50IntervalMipPolicy("m1-s1-route-start-order");
        const auto m1_s1r = parseRound50IntervalMipPolicy(
            "m1-s1r-used-first-route-start-order");
        require(historical.valid && historical.subset_duration_big_m ==
                    "historical-100000",
                "historical policy remains explicit and default-off");
        require(m1.valid && m1.name == "m1-tight-big-m-v0" &&
                    m1.branching == Round50BranchingPolicy::Default &&
                    m1.symmetry_numerical == "v0" &&
                    m1.subset_duration_big_m == "tight-tsp-lower-bound",
                "M1-v0 changes only the subset-duration M policy");
        require(m1_alias.valid && m1_alias.name == m1.name,
                "M1-v0 audit alias is deterministic");
        require(m1_s1.valid &&
                    m1_s1.symmetry_numerical == "route-start-order" &&
                    m1_s1.subset_duration_big_m ==
                        "tight-tsp-lower-bound",
                "M1-S1 composes only the frozen symmetry representative");
        require(m1_s1r.valid && m1_s1r.symmetry_numerical ==
                    "used-first-route-start-order" &&
                    m1_s1r.subset_duration_big_m ==
                        "tight-tsp-lower-bound",
                "M1-S1R composes only the frozen symmetry revision");

        std::cout << "Round51TightBigMTests passed\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Round51TightBigMTests failed: " << ex.what() << '\n';
        return 1;
    }
}
