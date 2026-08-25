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

        const auto a1 = parseRound50IntervalMipPolicy(
            "a1-root-sparse-2x2");
        require(a1.valid && a1.branching ==
                    Round50BranchingPolicy::Default &&
                    a1.symmetry_numerical == "v0" &&
                    a1.subset_duration_big_m ==
                        "tight-tsp-lower-bound" &&
                    a1.adaptive_branching == "root-sparse-2x2",
                "A1 composes only M1-v0 and root sparse branching");

        std::vector<Round51RootVariable> root_variables = {
            {"x_0_1_2", 'B', 0.0, 1.0, 0.5},
            {"x_0_1_3", 'B', 0.0, 1.0, 0.5},
            {"x_0_1_4", 'B', 0.0, 1.0, 0.5},
            {"z_0_1", 'B', 0.0, 1.0, 0.5},
            {"p_0_1", 'I', 0.0, 10.0, 3.25},
            {"d_0_1", 'I', 0.0, 10.0, 4.5},
            {"ord_0_1", 'I', 0.0, 10.0, 2.5},
            {"z_0_2", 'C', 0.0, 1.0, 0.5},
            {"p_0_2", 'I', 2.0, 2.0, 2.0},
            {"d_0_2", 'I', 0.0, 10.0, 4.0},
        };
        const auto pool = round51AdaptiveCandidatePool(root_variables);
        require(pool.size() == 4, "A1 pool uses the frozen budget four");
        require(pool[0].name == "x_0_1_2" &&
                    pool[1].name == "x_0_1_3" &&
                    pool[2].name == "z_0_1" &&
                    pool[3].name == "d_0_1",
                "A1 pool tie-break and family cap are deterministic");
        require(pool[0].family == Round50VariableFamily::RoutingArc &&
                    pool[2].family ==
                        Round50VariableFamily::VisitSelection &&
                    pool[3].family ==
                        Round50VariableFamily::DropQuantity,
                "A1 semantic family classification is canonical");
        require(pool[3].down_upper_bound == 4.0 &&
                    pool[3].up_lower_bound == 5.0,
                "general-integer child bounds use floor and ceil");

        Round51ProbeDirection infeasible;
        infeasible.status = Round51ProbeStatus::Infeasible;
        Round51ProbeDirection optimal;
        optimal.status = Round51ProbeStatus::Optimal;
        optimal.child_objective = 15.0;
        const auto scored = round51ScoreAdaptiveCandidate(
            pool[0], infeasible, optimal, 10.0, 20.0);
        require(scored.valid && scored.delta_down == 10.0 &&
                    scored.delta_up == 5.0 &&
                    std::fabs(scored.score - 50.0) < 1e-12,
                "child infeasibility and optimal-bound scoring");

        Round51ProbeDirection invalid;
        invalid.status = Round51ProbeStatus::Invalid;
        const auto invalid_score = round51ScoreAdaptiveCandidate(
            pool[1], invalid, optimal, 10.0, 20.0);
        auto fallback = round51SelectSparsePriorities({invalid_score});
        require(fallback.fallback_to_default &&
                    fallback.fallback_reason ==
                        "no_candidate_with_two_valid_probes",
                "invalid probes fall back to default branching");

        auto first = scored;
        auto second = scored;
        auto third = scored;
        first.candidate.pool_order = 0;
        second.candidate.pool_order = 1;
        third.candidate.pool_order = 2;
        first.candidate.name = "x_first";
        second.candidate.name = "z_second";
        third.candidate.name = "p_third";
        const auto selected = round51SelectSparsePriorities(
            {third, second, first});
        require(!selected.fallback_to_default &&
                    selected.priorities.size() == 2 &&
                    selected.priorities[0] ==
                        std::make_pair(std::string("x_first"), 2) &&
                    selected.priorities[1] ==
                        std::make_pair(std::string("z_second"), 1),
                "score ties use pool order and assign at most two priorities");
        Round51ProbeDirection no_gain = optimal;
        no_gain.child_objective = 10.0;
        const auto zero_score = round51ScoreAdaptiveCandidate(
            pool[0], no_gain, no_gain, 10.0, 20.0);
        fallback = round51SelectSparsePriorities({zero_score});
        require(fallback.fallback_to_default &&
                    fallback.fallback_reason ==
                        "all_valid_candidates_zero_improvement",
                "zero bound improvement falls back to default branching");
        require(std::fabs(round51AdaptiveTotal(
                    1.0, {2.0, 3.0, 4.0}, 5.0) - 15.0) < 1e-12,
                "end-to-end overhead accounting sums every phase");
        requireThrows([] {
            round51AdaptiveTotal(1.0, {-1.0}, 2.0);
        }, "invalid adaptive accounting fails closed");

        std::cout << "Round51TightBigMTests passed\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Round51TightBigMTests failed: " << ex.what() << '\n';
        return 1;
    }
}
