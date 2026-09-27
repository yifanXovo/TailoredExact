#include "ControllingLeafScheduler.hpp"
#include "Instance.hpp"
#include "PaperExternalGiniTree.hpp"
#include "Result.hpp"

#include <cmath>
#include <iostream>
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

ebrp::ControllingLeaf leaf(const std::string& id, double lower, double upper,
                           double bound, const std::string& parent = {},
                           int depth = 0, int child_index = -1) {
    ebrp::ControllingLeaf value;
    value.id = id;
    value.gamma_L = lower;
    value.gamma_U = upper;
    value.parent_id = parent;
    value.split_depth = depth;
    value.child_index = child_index;
    value.base_lower_bound = bound;
    value.lower_bound = bound;
    value.cutoff = 20.0;
    return value;
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        constexpr double tau = 0.07915;
        int checks = 0;

        const auto basic = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(12.0), optimal(14.0), tau, tolerance, false);
        require(basic.valid && std::fabs(basic.g_left_raw - 0.2) < 1e-12 &&
                std::fabs(basic.g_right_raw - 0.4) < 1e-12,
                "raw gains incorrect");
        ++checks;
        require(std::fabs(basic.g_left - 0.2) < 1e-12 &&
                std::fabs(basic.g_right - 0.4) < 1e-12,
                "clipped gains incorrect");
        ++checks;
        require(std::fabs(basic.adaptive_eta - 0.2) < 1e-12,
                "eta incorrect");
        ++checks;
        require(std::fabs(basic.adaptive_mu - 0.3) < 1e-12 &&
                std::fabs(basic.adaptive_mass_score - 0.06) < 1e-12,
                "mu or S_AM incorrect");
        ++checks;
        require(std::fabs(basic.adaptive_rho - tau / 0.3) < 1e-12,
                "adaptive rho incorrect");
        ++checks;

        for (const auto& pair : {
                std::pair<double, double>{0.1, 0.8},
                {0.2, 0.4}, {0.5, 0.5}, {0.9, 1.0}}) {
            const auto decision = ebrp::evaluateC6AdaptiveMassSplitDecision(
                0.0, 1.0, optimal(pair.first), optimal(pair.second),
                tau, tolerance, false);
            require((decision.adaptive_mass_score >= tau) ==
                    (decision.adaptive_eta >= decision.adaptive_rho),
                    "score/adaptive-rho equivalence failed");
        }
        ++checks;

        const auto clipped = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(9.0), optimal(25.0), tau, tolerance, false);
        require(clipped.valid && clipped.g_left == 0.0 &&
                clipped.g_right == 1.0 && clipped.launch_exact_closure,
                "negative/above-incumbent clipping failed");
        ++checks;

        const double equality_gain = std::sqrt(tau);
        const auto equal = ebrp::evaluateC6AdaptiveMassSplitDecision(
            0.0, 1.0, optimal(equality_gain), optimal(equality_gain),
            tau, tolerance, false);
        require(equal.valid && equal.split_immediately,
                "equality at tau did not split");
        ++checks;

        const auto split = ebrp::evaluateC6AdaptiveMassSplitDecision(
            0.0, 1.0, optimal(0.4), optimal(0.5), tau, tolerance, false);
        require(split.split_immediately && !split.run_child_bound_target,
                "finite split action incorrect");
        ++checks;
        require(basic.run_child_bound_target &&
                std::fabs(basic.child_bound_target - 12.0) < 1e-12,
                "finite native target action incorrect");
        ++checks;
        const auto close = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(10.0), optimal(10.0 + 0.5e-7),
            tau, tolerance, false);
        require(close.launch_exact_closure && !close.split_immediately,
                "exact-parent closure action incorrect");
        ++checks;

        const auto am_both = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, infeasible(), infeasible(), tau, tolerance, false);
        const auto amc_both = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, infeasible(), infeasible(), tau, tolerance, true);
        require(am_both.split_immediately && amc_both.close_parent_infeasible,
                "both-child infeasibility behavior incorrect");
        ++checks;
        const auto left = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, infeasible(), optimal(12.0), tau, tolerance, true);
        require(left.contract_single_child && left.feasible_child_index == 1 &&
                left.infeasible_child_index == 0,
                "left-child contraction decision incorrect");
        ++checks;
        const auto right = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(12.0), infeasible(), tau, tolerance, true);
        require(right.contract_single_child && right.feasible_child_index == 0 &&
                right.infeasible_child_index == 1,
                "right-child contraction decision incorrect");
        ++checks;

        ebrp::PaperLpResult ambiguous;
        ambiguous.infeasible = true;
        const auto failed_closed = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, ambiguous, optimal(12.0), tau, tolerance, true);
        require(!failed_closed.valid && !failed_closed.contract_single_child,
                "ambiguous infeasibility did not fail closed");
        ++checks;

        ebrp::ControllingLeafScheduler left_scheduler(tolerance);
        require(left_scheduler.addLeaf(leaf("P", 0.0, 1.0, 10.0)),
                "left parent add failed");
        require(left_scheduler.contractLeafAtomically(
                    "P", leaf("R", 0.5, 1.0, 12.0, "P", 1, 1),
                    0.0, 0.5, true),
                "left atomic contraction failed");
        require(left_scheduler.leaves().size() == 2 &&
                left_scheduler.parentChildCoverageValid(),
                "left contraction coverage or one-child materialization failed");
        ++checks;

        ebrp::ControllingLeafScheduler right_scheduler(tolerance);
        require(right_scheduler.addLeaf(leaf("P", 0.0, 1.0, 10.0)),
                "right parent add failed");
        require(right_scheduler.contractLeafAtomically(
                    "P", leaf("L", 0.0, 0.5, 12.0, "P", 1, 0),
                    0.5, 1.0, true) &&
                right_scheduler.parentChildCoverageValid(),
                "right atomic contraction coverage failed");
        ++checks;
        require(right_scheduler.globalLowerBound() >= 12.0 - tolerance &&
                right_scheduler.leafBoundsMonotone() &&
                right_scheduler.globalBoundMonotone(),
                "contraction lower-bound monotonicity failed");
        ++checks;

        ebrp::ControllingLeafScheduler rejected(tolerance);
        require(rejected.addLeaf(leaf("P", 0.0, 1.0, 10.0)) &&
                !rejected.contractLeafAtomically(
                    "P", leaf("R", 0.5, 1.0, 12.0, "P", 1, 1),
                    0.0, 0.5, false) && rejected.leaves().size() == 1,
                "unverified contraction was not atomically rejected");
        ++checks;

        ebrp::SolveOptions k4;
        ebrp::SolveOptions k1;
        k4.round47_c6_adaptive_mass = "adaptive-mass";
        k1.round47_c6_adaptive_mass = "adaptive-mass";
        k1.round40_c6_coarse_start = "k1-adaptive";
        k4.round47_c6_adaptive_mass_tau = tau;
        k1.round47_c6_adaptive_mass_tau = tau;
        require(k4.round47_c6_adaptive_mass_tau ==
                    k1.round47_c6_adaptive_mass_tau,
                "K1/K4 common tau contract failed");
        ++checks;

        const auto am_one = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, infeasible(), optimal(12.0), tau, tolerance, false);
        require(am_one.split_immediately && !am_one.contract_single_child,
                "AM did not retain original infeasibility split");
        ++checks;
        const auto am_finite = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(12.0), optimal(14.0), tau, tolerance, false);
        const auto amc_finite = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(12.0), optimal(14.0), tau, tolerance, true);
        require(am_finite.reason == amc_finite.reason &&
                am_finite.split_immediately == amc_finite.split_immediately &&
                am_finite.run_child_bound_target ==
                    amc_finite.run_child_bound_target,
                "AMC differs from AM outside strict infeasibility");
        ++checks;

        require(k4.round47_c6_adaptive_mass == "adaptive-mass" &&
                k4.round43_envelope_refinement == "off" &&
                k4.round44_envelope_tail_repair == "off" &&
                k4.round45_adaptive_parametric_partition == "off",
                "Round 47 default-off/forbidden mechanism contract failed");
        ++checks;

        ebrp::SolveOptions historical;
        const auto old = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(10.1), optimal(10.2),
            historical.c6_normalized_split_threshold, tolerance);
        require(historical.round47_c6_adaptive_mass == "off" &&
                old.split_immediately &&
                old.reason == "current_normalized_child_gain_reaches_rho",
                "historical C6 semantics changed while Round 47 is off");
        ++checks;

        const auto invalid_tau = ebrp::evaluateC6AdaptiveMassSplitDecision(
            10.0, 20.0, optimal(12.0), optimal(14.0), 1.1,
            tolerance, false);
        require(!invalid_tau.valid, "invalid tau accepted");
        ++checks;

        ebrp::SolveResult serialized;
        serialized.round47_c6_adaptive_mass = "adaptive-mass-contraction";
        serialized.round47_c6_adaptive_mass_tau = tau;
        serialized.round47_c6_adaptive_mass_tau_explicit = true;
        serialized.round47_single_child_contraction_count = 3;
        const std::string json = ebrp::resultToJson(serialized);
        require(json.find("\"round47_c6_adaptive_mass\": "
                          "\"adaptive-mass-contraction\"") != std::string::npos &&
                json.find("\"round47_single_child_contraction_count\": 3") !=
                    std::string::npos,
                "Round 47 result serialization missing");
        ++checks;

        require(basic.adaptive_mass_enabled &&
                basic.adaptive_score_tolerance > 0.0,
                "scale-aware score tolerance missing");
        ++checks;
        require(basic.adaptive_mass_enabled &&
                !basic.child_infeasibility_trigger,
                "finite decision unexpectedly launched another query");
        ++checks;

        require(checks == 28, "Round 47 adaptive-mass check count changed");
        std::cout << "Round47AdaptiveMassTests: 28 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round47AdaptiveMassTests failed: " << error.what() << '\n';
        return 1;
    }
}
