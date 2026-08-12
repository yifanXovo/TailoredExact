#include "GiniFrontierGeometry.hpp"
#include "PaperExternalGiniTree.hpp"

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

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-7;
        constexpr double rho = 0.01;
        int checks = 0;

        const auto baseline = ebrp::makeLegacyFrontierIntervals(0.0, 0.8, 4);
        const auto hh = ebrp::makeProofRelevantAnchorGrid(
            0.0, 0.8, 0.8, 4, tolerance);
        require(hh.valid && hh.active_intervals.size() == baseline.size(),
                "HH anchor grid did not preserve the four baseline cells");
        for (std::size_t index = 0; index < baseline.size(); ++index) {
            require(hh.active_intervals[index].lower == baseline[index].lower &&
                    hh.active_intervals[index].upper == baseline[index].upper,
                    "equal proof/anchor geometry is not baseline-equivalent");
        }
        ++checks;

        const auto wide = ebrp::makeProofRelevantAnchorGrid(
            0.0, 0.55, 0.8, 4, tolerance);
        require(wide.valid && wide.anchor_endpoints.size() == 5 &&
                wide.active_intervals.size() == 3 &&
                wide.truncated_active_interval_count == 1,
                "wide anchor grid did not expose one truncated active cell");
        require(std::fabs(wide.anchor_endpoints[1] - 0.2) < 1e-12 &&
                std::fabs(wide.anchor_endpoints[4] - 0.8) < 1e-12 &&
                std::fabs(wide.active_intervals.back().upper - 0.55) < 1e-12,
                "wide anchor endpoints or proof intersection are incorrect");
        require(ebrp::exactIntervalCoverage(
                    {0.0, 0.55}, wide.active_intervals, tolerance),
                "active wide-anchor cells lost proof-relevant coverage");
        ++checks;

        const auto unsafe = ebrp::makeProofRelevantAnchorGrid(
            0.0, 0.6, 0.5, 4, tolerance);
        require(!unsafe.valid &&
                    unsafe.reason ==
                        "unsafe_anchor_grid_does_not_cover_proof_range",
                "unsafe U_anchor < U_proof geometry was not rejected");
        ++checks;

        const auto improved_proof = ebrp::makeProofRelevantAnchorGrid(
            0.0, 0.42, 0.8, 4, tolerance);
        require(improved_proof.valid &&
                ebrp::exactIntervalCoverage(
                    {0.0, 0.42}, improved_proof.active_intervals, tolerance),
                "decreasing U_proof invalidated the fixed anchor cover");
        ++checks;

        require(ebrp::round36ProofAnchorLaunchContractValid(
                    true, 8.778082265416142, 8.778082265416142,
                    8.833146456637262, tolerance),
                "equal verified startup/current proof was rejected");
        require(ebrp::round36ProofAnchorLaunchContractValid(
                    true, 8.778082265416142, 8.773853723068965,
                    8.833146456637262, tolerance),
                "stronger current proof invalidated the safe frozen anchor");
        ++checks;

        require(!ebrp::round36ProofAnchorLaunchContractValid(
                    true, 8.778082265416142, 8.79,
                    8.833146456637262, tolerance),
                "weaker current proof was accepted as launch-safe");
        require(!ebrp::round36ProofAnchorLaunchContractValid(
                    true, 8.778082265416142, 8.77, 8.76, tolerance),
                "anchor below the recorded startup proof was accepted");
        require(!ebrp::round36ProofAnchorLaunchContractValid(
                    false, 8.778082265416142, 8.77,
                    8.833146456637262, tolerance),
                "unverified startup pair was accepted");
        ++checks;

        const auto legacy_decision = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, optimal(10.1), optimal(10.2), rho, tolerance);
        const auto explicit_proof = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, 20.0, "proof", optimal(10.1), optimal(10.2),
            rho, tolerance);
        require(legacy_decision.valid && explicit_proof.valid &&
                legacy_decision.split_immediately ==
                    explicit_proof.split_immediately &&
                legacy_decision.reason == explicit_proof.reason &&
                legacy_decision.normalized_disjunction_gain ==
                    explicit_proof.normalized_disjunction_gain,
                "explicit proof normalization changed the frozen C6 decision");
        ++checks;

        const auto proof_normalized = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, 30.0, "proof", optimal(10.15), optimal(10.2),
            rho, tolerance);
        const auto anchor_normalized = ebrp::evaluateC6CurrentSplitDecision(
            10.0, 20.0, 30.0, "anchor", optimal(10.15), optimal(10.2),
            rho, tolerance);
        require(proof_normalized.valid && anchor_normalized.valid &&
                std::fabs(proof_normalized.b_plus - 10.15) < 1e-12 &&
                std::fabs(proof_normalized.eta_proof - 0.015) < 1e-12 &&
                std::fabs(proof_normalized.eta_anchor - 0.0075) < 1e-12,
                "proof/anchor eta telemetry is incorrect");
        require(proof_normalized.split_immediately &&
                anchor_normalized.run_child_bound_target &&
                !anchor_normalized.split_immediately,
                "normalization selector did not isolate the intended decision");
        ++checks;

        const auto invalid_normalization =
            ebrp::evaluateC6CurrentSplitDecision(
                10.0, 20.0, 19.0, "anchor", optimal(10.2),
                optimal(10.3), rho, tolerance);
        require(!invalid_normalization.valid &&
                    invalid_normalization.reason ==
                        "invalid_c6_normalization_configuration",
                "split guidance accepted an unsafe anchor");
        ++checks;

        ebrp::FixedIntervalMipOutcome terminal;
        terminal.attempted = true;
        terminal.available = true;
        terminal.solver_finalization_reached = true;
        terminal.model_fingerprint_matches_request = true;
        terminal.exact_zero_gap_roundtrip = true;
        terminal.feasibility_consistency_gate = true;
        terminal.terminal_mip = true;
        terminal.optimal = true;
        terminal.native_bound_available = true;
        const auto closure = ebrp::evaluatePaperTerminalMipDecision(terminal);
        require(closure.valid && closure.close_leaf,
                "Round 36 controls changed exact terminal closure semantics");
        ++checks;

        require(checks == 10, "Round 36 causal check count changed");
        std::cout << "Round36CausalTests: 10 safety/equivalence checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round36CausalTests failed: " << error.what() << '\n';
        return 1;
    }
}
