#include "GiniEnvelopeTailRepair.hpp"
#include "GiniFrontierGeometry.hpp"

#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

void near(double actual, double expected, double tolerance,
          const std::string& message) {
    if (std::fabs(actual - expected) > tolerance)
        throw std::runtime_error(message);
}

ebrp::GiniLookaheadBound lp(double a, double b, double lower) {
    ebrp::GiniLookaheadBound cell;
    cell.interval = {a, b};
    cell.terminal_valid = true;
    cell.optimal = true;
    cell.bound_available = true;
    cell.lower_bound = lower;
    return cell;
}

ebrp::GiniLookaheadBound empty(double a, double b) {
    auto cell = lp(a, b, 0.0);
    cell.optimal = false;
    cell.bound_available = false;
    cell.infeasible = true;
    return cell;
}

} // namespace

int main() {
    try {
        int checks = 0;

        ebrp::FrontierTailScoresInput score;
        score.root = {0.0, 2.0};
        score.current = {0.0, 0.5};
        score.root_lower_bound = 1.0;
        score.launch_upper_bound = 5.0;
        score.current_lower_bound = 2.0;
        score.strengthened_lower_bound = 2.5;
        score.frontier_target = 3.0;
        score.V_local = 0.6;
        score.V_envelope = 0.4;
        score.V_residual = 0.2;
        score.terminal_lookahead = {lp(0.0, 0.25, 3.0),
                                    lp(0.25, 0.5, 3.5)};
        score.certificate_tolerance = 1e-9;
        const auto scores = ebrp::evaluateFrontierTailScores(score);
        require(scores.valid, "score tuple must be valid");
        near(scores.D_R43, 0.2 / (0.5 * 3.0), 1e-12,
             "corrected Round 43 D formula");
        ++checks;
        near(scores.P_profile, 1.0 / 3.0, 1e-12,
             "D and profile residual fraction must remain distinct");
        require(std::fabs(scores.D_R43 - scores.P_profile) > 0.1,
                "D_R43 must not be conflated with P_profile");
        ++checks;
        near(scores.M0, 8.0, 1e-12, "fixed root normalization");
        near(scores.M_root, 0.025, 1e-12,
             "root-normalized residual mass");
        ++checks;
        near(scores.F, 1.0, 1e-12, "frontier score");
        near(scores.H, 0.025, 1e-12, "combined conservative score");
        require(scores.decisive_frontier,
                "terminal disjunction reaches target while envelope does not");
        ++checks;

        const std::vector<ebrp::FrontierBoundEntry> leaves = {
            {"a", 1.0, true}, {"b", 1.0 + 5e-9, true},
            {"c", 1.5, true}, {"closed", 1.2, false}};
        const auto target = ebrp::computeNextFrontierTarget(
            "a", 1.0, leaves, 2.0, 1e-7);
        require(target.valid && target.frontier_multiplicity == 2 &&
                target.next_distinct_available,
                "tied frontier multiplicity and next distinct bound");
        near(target.target, 1.5, 1e-12, "next frontier target");
        ++checks;
        const auto cutoff = ebrp::computeNextFrontierTarget(
            "a", 1.0, {{"a", 1.0, true}, {"b", 1.0, true}},
            1.4, 1e-7);
        require(cutoff.valid && !cutoff.next_distinct_available &&
                cutoff.source == "verified-incumbent-cutoff",
                "all-tied frontier must use incumbent cutoff");
        ++checks;

        const auto d1 = ebrp::makeDyadicLookaheadPartition({0.0, 1.0}, 1);
        require(d1.size() == 2 &&
                ebrp::exactIntervalCoverage({0.0, 1.0}, d1, 1e-12),
                "fixed-d1 complete cover");
        ++checks;
        const std::vector<ebrp::GiniIntervalGeometry> nonuniform = {
            {0.0, 0.25}, {0.25, 0.5}, {0.5, 1.0}};
        require(ebrp::exactIntervalCoverage(
                    {0.0, 1.0}, nonuniform, 1e-12),
                "frontier-d2 nonuniform complete cover");
        ++checks;
        const auto refine = ebrp::evaluateFrontierD2Stop(
            lp(0.0, 0.5, 2.0), 3.0, 1, 2, 1e-7);
        const auto reached = ebrp::evaluateFrontierD2Stop(
            lp(0.5, 1.0, 3.0), 3.0, 1, 2, 1e-7);
        const auto infeasible = ebrp::evaluateFrontierD2Stop(
            empty(0.5, 1.0), 3.0, 1, 2, 1e-7);
        require(refine.valid && refine.refine && reached.valid &&
                !reached.refine && infeasible.valid && !infeasible.refine,
                "adaptive lookahead stopping is bound/status only");
        ++checks;

        std::vector<ebrp::GiniEnvelopeFacet> facets(3);
        facets[0].alpha = 1.0;
        facets[1].alpha = 2.0;
        facets[2].alpha = 1.5;
        facets[2].beta = 1.0;
        const auto active = ebrp::selectEnvelopeFacets(
            facets, "active-one", 1.0, 2.0, 1e-7);
        require(active.valid && active.active_index == 2 &&
                active.selected.size() == 1,
                "active-one chooses the maximum violated facet");
        ++checks;
        const auto violated = ebrp::selectEnvelopeFacets(
            facets, "violated", 1.0, 1.75, 1e-7);
        require(violated.valid && violated.violated_count == 2 &&
                violated.selected.size() == 2,
                "violated policy selects every separated facet");
        ++checks;

        std::string scope_reason;
        require(!ebrp::explicitCutMayPropagate(
                    ebrp::ExplicitCutScope::SourceInterval,
                    {0.0, 1.0}, {0.0, 0.5}, 1e-9, &scope_reason) == false,
                "source-interval facet may inherit to nested child");
        require(!ebrp::explicitCutMayPropagate(
                    ebrp::ExplicitCutScope::SourceInterval,
                    {0.0, 1.0}, {-0.1, 0.5}, 1e-9, &scope_reason),
                "parent-only/out-of-domain propagation must fail closed");
        ++checks;
        require(!ebrp::explicitCutMayPropagate(
                    ebrp::ExplicitCutScope::BranchLocal,
                    {0.0, 1.0}, {0.1, 0.2}, 1e-9, &scope_reason) &&
                ebrp::explicitCutMayPropagate(
                    ebrp::ExplicitCutScope::Global,
                    {0.0, 1.0}, {-1.0, 2.0}, 1e-9, &scope_reason),
                "cut-scope inheritance policy");
        ++checks;

        ebrp::TailRefinementInput decision;
        decision.family = "c6-overlay";
        decision.old_c6_split = true;
        const auto overlay = ebrp::evaluateTailRefinementDecision(decision);
        require(overlay.valid && overlay.split &&
                overlay.old_c6_action == overlay.final_action,
                "unchanged C6 overlay preserves old split action");
        ++checks;
        decision.family = "veto";
        decision.old_c6_split = false;
        decision.F = 1.0;
        const auto veto = ebrp::evaluateTailRefinementDecision(decision);
        require(veto.valid && !veto.split,
                "veto-only never adds a split");
        ++checks;
        decision.family = "veto-promotion";
        decision.decisive_frontier = true;
        decision.M_root = 0.2;
        decision.rho_M = 0.1;
        const auto promotion = ebrp::evaluateTailRefinementDecision(decision);
        require(promotion.valid && promotion.split,
                "decisive promotion requires frontier and root mass");
        decision.decisive_frontier = false;
        require(!ebrp::evaluateTailRefinementDecision(decision).split,
                "promotion fails without decisive frontier");
        ++checks;

        require(ebrp::exactIntervalCoverage(
                    {0.0, 1.0}, {{0.0, 0.5}, {0.5, 1.0}}, 1e-12),
                "atomic child geometry covers its parent exactly");
        ++checks;
        require(ebrp::validFinalEnvelopeLeafBound(
                    std::numeric_limits<double>::infinity(), true) &&
                !ebrp::validFinalEnvelopeLeafBound(
                    std::numeric_limits<double>::infinity(), false),
                "+infinity is valid only for an infeasible Empty leaf");
        ++checks;

        ebrp::CglpMultiplierCertificate cglp;
        cglp.A = {{1.0}, {-1.0}};
        cglp.b = {0.0, -1.0};
        cglp.g = {1.0};
        cglp.gamma = 0.5;
        cglp.u_minus = {0.25, 0.0};
        cglp.u_plus = {0.0, 0.25};
        cglp.lambda_minus = 0.25;
        cglp.lambda_plus = 0.25;
        cglp.pi = {0.0};
        cglp.pi0 = -0.125;
        const auto audit = ebrp::auditCglpMultiplierCertificate(cglp, 1e-9);
        require(audit.valid, "rank-1 CGLP multiplier certificate validity");
        cglp.pi0 = 0.1;
        require(!ebrp::auditCglpMultiplierCertificate(cglp, 1e-9).valid,
                "invalid CGLP RHS must be rejected");
        ++checks;

        require(ebrp::verifiedMipStartInInterval(
                    0.5, {0.0, 0.5}, true, 1e-9) &&
                !ebrp::verifiedMipStartInInterval(
                    0.5, {0.0, 0.5}, false, 1e-9) &&
                ebrp::verifiedMipStartInInterval(
                    0.5, {0.5, 1.0}, false, 1e-9),
                "verified MIP-start interval membership and endpoints");
        ++checks;

        const auto all_empty = ebrp::evaluateFrontierTailScores({
            {0.0, 1.0}, {0.0, 1.0}, 0.0, 1.0, 0.0, 0.0, 0.5,
            0.0, 0.0, 0.0, {empty(0.0, 0.5), empty(0.5, 1.0)}, 1e-9});
        require(all_empty.valid && std::isinf(all_empty.L_D) &&
                all_empty.decisive_frontier,
                "all-infeasible profile has infinite disjunction bound");
        ++checks;

        std::cout << "Round44EnvelopeTailRepairTests: " << checks
                  << " checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round44EnvelopeTailRepairTests failed: "
                  << error.what() << '\n';
        return 1;
    }
}
