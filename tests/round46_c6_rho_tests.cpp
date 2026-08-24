#include "GiniFrontierGeometry.hpp"
#include "Instance.hpp"
#include "PaperExternalGiniTree.hpp"
#include "Result.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::PaperLpResult optimal(double bound) {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.optimal = true;
    result.bound_available = true;
    result.lower_bound = bound;
    return result;
}

ebrp::PaperLpResult infeasible() {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.infeasible = true;
    return result;
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        int checks = 0;

        ebrp::SolveOptions implicit;
        require(std::fabs(implicit.c6_normalized_split_threshold - 0.01) <
                    1e-15 &&
                !implicit.c6_normalized_split_threshold_explicit,
                "implicit C6 rho is not the historical 0.01 default");
        ++checks;

        ebrp::SolveOptions explicit001 = implicit;
        explicit001.c6_normalized_split_threshold = 0.01;
        explicit001.c6_normalized_split_threshold_explicit = true;
        require(explicit001.c6_normalized_split_threshold_explicit &&
                explicit001.c6_normalized_split_threshold ==
                    implicit.c6_normalized_split_threshold,
                "explicit rho=0.01 did not preserve the default value");
        ++checks;

        const auto implicit_decision = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(10.1), optimal(10.2),
            implicit.c6_normalized_split_threshold, tolerance);
        const auto explicit_decision = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(10.1), optimal(10.2),
            explicit001.c6_normalized_split_threshold, tolerance);
        require(implicit_decision.valid && explicit_decision.valid &&
                implicit_decision.split_immediately ==
                    explicit_decision.split_immediately &&
                implicit_decision.run_child_bound_target ==
                    explicit_decision.run_child_bound_target &&
                implicit_decision.launch_exact_closure ==
                    explicit_decision.launch_exact_closure &&
                implicit_decision.reason == explicit_decision.reason,
                "implicit/explicit rho=0.01 decisions differ");
        ++checks;

        const auto equal = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(11.2), optimal(11.4), 0.12, tolerance);
        require(equal.valid && equal.split_immediately &&
                std::fabs(equal.normalized_disjunction_gain - 0.12) < 1e-12,
                "gain equal to rho did not split");
        ++checks;

        const auto below = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(11.19), optimal(11.4), 0.12, tolerance);
        require(below.valid && below.run_child_bound_target &&
                !below.split_immediately,
                "positive gain below rho did not use native target");
        ++checks;

        const auto above = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(11.3), optimal(11.4), 0.12, tolerance);
        require(above.valid && above.split_immediately,
                "gain above rho did not split");
        ++checks;

        for (double rho : {0.01, 0.12, 0.15, 0.20, 0.50, 1.0}) {
            const auto child_empty = ebrp::evaluateC6CurrentSplitDecision(
                10.0, 20.0, infeasible(), optimal(11.0), rho, tolerance);
            require(child_empty.valid && child_empty.split_immediately &&
                    child_empty.child_infeasibility_trigger,
                    "child infeasibility became rho-dependent");
        }
        ++checks;

        require(below.run_child_bound_target &&
                std::fabs(below.child_bound_target - 11.19) < 1e-12,
                "native-bound-target did not retain the child post-bound");
        ++checks;

        const auto no_gain = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(10.0), optimal(10.0 + 0.5e-7),
            0.50, tolerance);
        require(no_gain.valid && no_gain.launch_exact_closure &&
                !no_gain.split_immediately &&
                !no_gain.run_child_bound_target,
                "no-gain parent did not take exact closure");
        ++checks;

        ebrp::SolveOptions k4 = implicit;
        ebrp::SolveOptions k1 = implicit;
        k1.round40_c6_coarse_start = "k1-adaptive";
        k4.c6_normalized_split_threshold = 0.15;
        k1.c6_normalized_split_threshold = 0.15;
        const auto k4_decision = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(11.4), optimal(11.5),
            k4.c6_normalized_split_threshold, tolerance);
        const auto k1_decision = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(11.4), optimal(11.5),
            k1.c6_normalized_split_threshold, tolerance);
        require(k4_decision.reason == k1_decision.reason &&
                k4_decision.split_immediately ==
                    k1_decision.split_immediately,
                "K1 and K4 did not read the same C6 rho");
        ++checks;

        const auto k4_geometry = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "off", tolerance);
        const auto k1_geometry = ebrp::makeRound40CoarseStartGeometry(
            0.0, 0.8, 4, "k1-adaptive", tolerance);
        require(k4_geometry.valid && k1_geometry.valid &&
                k4_geometry.initial_intervals.size() == 4 &&
                k1_geometry.initial_intervals.size() == 1 &&
                k4_geometry.adaptive_refinement &&
                k1_geometry.adaptive_refinement,
                "K1/K4 differ in more than the intended initialization");
        ++checks;

        require(implicit.round43_envelope_refinement == "off" &&
                implicit.round44_envelope_tail_repair == "off" &&
                implicit.round45_adaptive_parametric_partition == "off" &&
                implicit.round45_point_rule == "midpoint" &&
                implicit.round44_rank1_cuts == "off" &&
                implicit.round44_mip_starts == "off" &&
                implicit.round44_frontier_consolidation == "off",
                "later-round mechanisms are not default-off");
        ++checks;

        ebrp::SolveResult serialized;
        serialized.c6_normalized_split_threshold = 0.15;
        serialized.c6_normalized_split_threshold_explicit = true;
        serialized.c6_normalized_split_threshold_source = "explicit";
        const std::string json = ebrp::resultToJson(serialized);
        std::ostringstream serialized_rho;
        serialized_rho
            << std::setprecision(std::numeric_limits<double>::max_digits10)
            << serialized.c6_normalized_split_threshold;
        require(json.find("\"c6_normalized_split_threshold\": " +
                    serialized_rho.str()) !=
                    std::string::npos &&
                json.find("\"c6_normalized_split_threshold_explicit\": true") !=
                    std::string::npos &&
                json.find("\"c6_normalized_split_threshold_source\": \"explicit\"") !=
                    std::string::npos,
                "result JSON omitted Round 46 rho identity");
        ++checks;

        for (double endpoint : {0.0, 1.0}) {
            const auto valid_endpoint = ebrp::evaluateC6CurrentSplitDecision(
                10.0, 20.0, optimal(11.0), optimal(11.1), endpoint,
                tolerance);
            require(valid_endpoint.valid,
                    "valid endpoint rho was rejected");
        }
        for (double invalid : {-0.01, 1.01}) {
            const auto rejected = ebrp::evaluateC6CurrentSplitDecision(
                10.0, 20.0, optimal(11.0), optimal(11.1), invalid,
                tolerance);
            require(!rejected.valid,
                    "out-of-range rho was accepted");
        }
        ++checks;

        const auto children = ebrp::splitLegacyFrontierInterval(
            k1_geometry.initial_intervals[0].lower,
            k1_geometry.initial_intervals[0].upper, 2);
        require(ebrp::exactIntervalCoverage(
                    k1_geometry.initial_intervals[0], children, tolerance),
                "rho parameterization changed atomic midpoint coverage");
        ++checks;

        require(checks == 15, "Round 46 C6 rho check count changed");
        std::cout << "Round46C6RhoTests: 15 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round46C6RhoTests failed: " << error.what() << '\n';
        return 1;
    }
}
