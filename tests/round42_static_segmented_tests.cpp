#include "ControllingLeafScheduler.hpp"
#include "Instance.hpp"
#include "StaticSegmentedGini.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::CanonicalLinearRow row(
    const std::string& family,
    const std::string& variable,
    char sense,
    double rhs) {
    ebrp::CanonicalLinearRow out;
    out.family = family;
    out.coefficients[variable] = 1.0;
    out.sense = sense;
    out.rhs = rhs;
    out.scope = ebrp::IntervalRowScope::IntervalLocal;
    return out;
}

ebrp::ControllingLeaf siblingLeaf(
    const std::string& id,
    const std::string& parent,
    int child_index,
    double lower,
    double upper,
    double bound) {
    ebrp::ControllingLeaf out;
    out.id = id;
    out.parent_id = parent;
    out.child_index = child_index;
    out.split_depth = 2;
    out.gamma_L = lower;
    out.gamma_U = upper;
    out.base_lower_bound = bound;
    out.lower_bound = bound;
    out.lower_bound_sources = {"test_bound"};
    out.cutoff = 1.0;
    return out;
}

} // namespace

int main() {
    try {
        constexpr double tolerance = 1e-9;
        int checks = 0;

        std::string reason;
        const auto k4 = ebrp::makeEqualStaticSegments(
            0.0, 0.8, 4, tolerance, &reason);
        require(k4.size() == 4 &&
                    std::fabs(k4[1].upper - 0.4) < tolerance &&
                    ebrp::exactIntervalCoverage({0.0, 0.8}, k4, tolerance),
                "equal K4 is not an exact cover");
        ++checks;

        const std::vector<ebrp::GiniIntervalGeometry> unequal = {
            {0.1, 0.2}, {0.2, 0.55}, {0.55, 0.7}};
        require(ebrp::exactIntervalCoverage(
                    {0.1, 0.7}, unequal, tolerance),
                "non-equal adaptive sibling cover was rejected");
        ++checks;

        const std::vector<ebrp::GiniIntervalGeometry> lower_pair = {
            k4[0], k4[1]};
        const std::vector<ebrp::GiniIntervalGeometry> upper_pair = {
            k4[2], k4[3]};
        require(ebrp::exactIntervalCoverage(
                    {0.0, 0.4}, lower_pair, tolerance) &&
                    ebrp::exactIntervalCoverage(
                        {0.4, 0.8}, upper_pair, tolerance) &&
                    std::fabs(lower_pair.back().upper -
                              upper_pair.front().lower) < tolerance,
                "paired K4 blocks do not preserve complete coverage");
        ++checks;

        const std::vector<ebrp::GiniIntervalGeometry> gap = {
            {0.1, 0.2}, {0.21, 0.7}};
        require(!ebrp::exactIntervalCoverage(
                    {0.1, 0.7}, gap, tolerance),
                "gapped arbitrary cover was accepted");
        ++checks;

        require(ebrp::staticSelectorBlockValid(
                    {0.0, 1.0}, {true, true}, {}, tolerance) &&
                    !ebrp::staticSelectorBlockValid(
                        {1.0, 1.0}, {true, true}, {}, tolerance),
                "K2 selector exclusivity failed");
        ++checks;

        require(ebrp::staticSelectorBlockValid(
                    {0.0, 0.0, 1.0, 0.0},
                    {true, true, true, true}, {0.0, 1.0}, tolerance) &&
                    !ebrp::staticSelectorBlockValid(
                        {0.0, 0.0, 1.0, 0.0},
                        {true, true, true, true}, {1.0, 0.0}, tolerance),
                "hierarchical K4 links are not equivalent to flat leaves");
        ++checks;

        require(!ebrp::staticSelectorBlockValid(
                    {0.0, 1.0}, {true, false}, {}, tolerance),
                "infeasible segment selector was not fixed to zero");
        ++checks;

        std::vector<ebrp::IntervalRowFactoryResult> packs(2);
        packs[0].rows = {
            row("weighted", "x", 'L', 2.0),
            row("common", "y", 'G', 1.0),
            row("residual", "only_left", 'L', 4.0),
            row("excluded", "q", 'L', 5.0),
        };
        packs[1].rows = {
            row("weighted", "x", 'L', 3.0),
            row("common", "y", 'G', 1.0),
            row("excluded", "q", 'L', 6.0),
        };
        const auto factoring = ebrp::makeStaticCommonRowFactoringPlan(
            packs, {"excluded"});
        require(factoring.valid && factoring.input_rows == 5 &&
                    factoring.unconditional_rows_written == 1 &&
                    factoring.selector_weighted_rows_written == 1 &&
                    factoring.indicator_rows_retained == 1 &&
                    factoring.indicator_rows_removed == 4,
                "common-row factoring classification failed");
        ++checks;

        require(factoring.selector_weighted_rows[0].rhs_by_segment ==
                    std::vector<double>({2.0, 3.0}),
                "selector-weighted RHS ordering is not deterministic");
        ++checks;

        for (int segment = 0; segment < 4; ++segment) {
            for (int bit = 0; bit <= 1; ++bit) {
                const double lower = k4[segment].lower;
                const double upper = k4[segment].upper;
                const double g = 0.5 * (lower + upper);
                require(ebrp::round41PerspectiveProductBlockValid(
                            lower, upper, 1.0, bit, g, g, bit,
                            g * bit, tolerance),
                        "arbitrary-K perspective truth table failed");
            }
        }
        ++checks;

        const ebrp::SolveOptions defaults;
        require(defaults.round42_static_architecture == "off" &&
                    defaults.round42_static_solve == "mip" &&
                    defaults.round42_terminal_sibling_coalescing == "off",
                "Round 42 controls are not default-off");
        ++checks;

        ebrp::ControllingLeafScheduler fallback_scheduler(1e-7);
        auto fallback_left = siblingLeaf(
            "p.0", "p", 0, 0.1, 0.3, 0.15);
        auto fallback_right = siblingLeaf(
            "p.1", "p", 1, 0.3, 0.7, 0.2);
        require(fallback_scheduler.addLeaf(fallback_left) &&
                    fallback_scheduler.addLeaf(fallback_right) &&
                    fallback_scheduler.areExactLiveSiblings("p.0", "p.1"),
                "exact adaptive sibling identity was rejected");
        ++checks;

        require(fallback_scheduler.setStatus(
                    "p.0", ebrp::ControllingLeafStatus::TerminalReady,
                    "test_terminal_ready") &&
                    fallback_scheduler.setStatus(
                        "p.1", ebrp::ControllingLeafStatus::TerminalReady,
                        "test_terminal_ready"),
                "terminal-ready sibling transition failed");
        auto invalid_union = siblingLeaf(
            "p.union.invalid", "p_union", -1, 0.1, 0.69, 0.15);
        invalid_union.status = ebrp::ControllingLeafStatus::Open;
        std::string fallback_reason;
        require(!fallback_scheduler.coalesceSiblingLeavesAtomically(
                    "p.0", "p.1", invalid_union, &fallback_reason) &&
                    fallback_scheduler.findLeaf("p.0")->status ==
                        ebrp::ControllingLeafStatus::TerminalReady &&
                    fallback_scheduler.findLeaf("p.1")->status ==
                        ebrp::ControllingLeafStatus::TerminalReady &&
                    !fallback_scheduler.findLeaf("p.union.invalid"),
                "failed union validation did not preserve original leaves");
        ++checks;

        const double before_union = fallback_scheduler.globalLowerBound();
        auto valid_union = siblingLeaf(
            "p.union", "p_union", -1, 0.1, 0.7, 0.15);
        valid_union.status = ebrp::ControllingLeafStatus::Open;
        require(fallback_scheduler.coalesceSiblingLeavesAtomically(
                    "p.0", "p.1", valid_union) &&
                    std::fabs(fallback_scheduler.globalLowerBound() -
                              before_union) < tolerance,
                "atomic sibling replacement changed the valid global bound");
        ++checks;

        std::string coverage_reason;
        require(fallback_scheduler.parentChildCoverageValid(
                    &coverage_reason) &&
                    fallback_scheduler.findLeaf("p.0")->status ==
                        ebrp::ControllingLeafStatus::Coalesced &&
                    fallback_scheduler.findLeaf("p.1")->status ==
                        ebrp::ControllingLeafStatus::Coalesced &&
                    fallback_scheduler.findLeaf("p.union") &&
                    fallback_scheduler.findLeaf("p.union")
                            ->coverage_member_ids.size() == 2,
                "atomic sibling-to-block coverage lifecycle is invalid");
        ++checks;

        require(fallback_scheduler.mergeValidLowerBound(
                    "p.union", 0.4, "native_union_bound") &&
                    std::fabs(fallback_scheduler.findLeaf("p.union")
                                  ->lower_bound - 0.4) < tolerance &&
                    std::fabs(fallback_scheduler.findLeaf("p.0")
                                  ->lower_bound - 0.15) < tolerance &&
                    std::fabs(fallback_scheduler.findLeaf("p.1")
                                  ->lower_bound - 0.2) < tolerance,
                "unresolved union bound leaked into original children");
        ++checks;

        require(checks == 16, "Round 42 static test count changed");
        std::cout << "Round42StaticSegmentedTests: 16 checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round42StaticSegmentedTests failed: " << error.what()
                  << '\n';
        return 1;
    }
}
