#include "ControllingLeafScheduler.hpp"
#include "HgaTgbcRunner.hpp"
#include "PaperExternalGiniTree.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int checks = 0;

void require(bool condition, const std::string& message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}
bool near(double left, double right) {
    return std::fabs(left - right) <= 1e-10;
}

ebrp::PaperLpResult optimalLp(double bound) {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.optimal = true;
    result.bound_available = true;
    result.lower_bound = bound;
    return result;
}

ebrp::PaperLpResult infeasibleLp() {
    ebrp::PaperLpResult result;
    result.terminal_valid = true;
    result.infeasible = true;
    return result;
}

ebrp::ControllingLeaf leaf(const std::string& id, double lower, double upper,
                           double bound, double cutoff = 1.0) {
    ebrp::ControllingLeaf result;
    result.id = id;
    result.gamma_L = lower;
    result.gamma_U = upper;
    result.base_lower_bound = bound;
    result.lower_bound = bound;
    result.lower_bound_sources = {"test_valid_bound"};
    result.cutoff = cutoff;
    return result;
}

ebrp::Instance deterministicHgaInstance() {
    ebrp::Instance instance;
    instance.name = "round27_deterministic_hga_toy";
    instance.V = 4;
    instance.M = 2;
    instance.Q = {3, 3};
    instance.capacity = {0, 10, 10, 10, 10};
    instance.initial = {0, 8, 2, 8, 2};
    instance.target = {0, 5, 5, 5, 5};
    instance.weights = {0.0, 1.0, 1.0, 1.0, 1.0};
    instance.min_ratio = {0.0, 0.5, 0.5, 0.5, 0.5};
    instance.points = {{0.0, 0.0}, {1.0, 0.0}, {2.0, 0.0},
                       {0.0, 1.0}, {0.0, 2.0}};
    instance.dist.assign(5, std::vector<double>(5, 0.0));
    for (int i = 0; i <= instance.V; ++i) {
        for (int j = 0; j <= instance.V; ++j) {
            const double dx = instance.points[i].first - instance.points[j].first;
            const double dy = instance.points[i].second - instance.points[j].second;
            instance.dist[i][j] = std::sqrt(dx * dx + dy * dy);
        }
    }
    instance.total_time_limit = 100.0;
    instance.pickup_time = 1.0;
    instance.drop_time = 1.0;
    return instance;
}

std::string readAll(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    std::ostringstream text;
    text << input.rdbuf();
    return text.str();
}

void splitDecisionChecks() {
    const double tolerance = 1e-7;
    auto no_gain = ebrp::evaluatePaperLpSplitDecision(
        0.5, optimalLp(0.5 + 0.5 * tolerance), optimalLp(0.8), tolerance);
    require(no_gain.valid && !no_gain.should_split,
            "sub-tolerance LP gain caused a split");

    auto strict = ebrp::evaluatePaperLpSplitDecision(
        0.5, optimalLp(0.5 + 2.0 * tolerance), optimalLp(0.7), tolerance);
    require(strict.valid && strict.should_split &&
                strict.strict_bound_improvement_trigger,
            "strict child LP gain did not split");

    auto infeasible = ebrp::evaluatePaperLpSplitDecision(
        0.5, infeasibleLp(), optimalLp(0.5), tolerance);
    require(infeasible.valid && infeasible.should_split &&
                infeasible.child_infeasibility_trigger,
            "infeasible child LP did not split");

    ebrp::PaperLpResult invalid;
    auto rejected = ebrp::evaluatePaperLpSplitDecision(
        0.5, invalid, optimalLp(0.7), tolerance);
    require(!rejected.valid && !rejected.should_split,
            "nonterminal child LP was used");
}

void schedulerAndCoverageChecks() {
    ebrp::ControllingLeafScheduler scheduler(1e-7);
    require(scheduler.addLeaf(leaf("wide", 0.0, 1.0, 0.1)),
            "parent add failed");
    auto selection = scheduler.selectNextByBoundOnly();
    require(selection.available && selection.selected_leaf_id == "wide" &&
                selection.requested_quantum_seconds == 0.0 &&
                selection.next_attempt_number == 0,
            "paper best-bound selection resolved an attempt or quantum");

    auto left = leaf("wide.0", 0.0, 0.5, 0.3);
    left.parent_id = "wide";
    left.split_depth = 1;
    left.child_index = 0;
    auto right = leaf("wide.1", 0.5, 1.0, 0.4);
    right.parent_id = "wide";
    right.split_depth = 1;
    right.child_index = 1;
    require(scheduler.splitLeafAtomically("wide", {left, right}),
            "exact atomic split rejected");
    std::string reason;
    require(scheduler.parentChildCoverageValid(&reason),
            "parent/child coverage invalid");
    require(near(scheduler.globalLowerBound(), 0.3),
            "post-split global bound is not the minimum inherited child bound");
    require(scheduler.findLeaf("wide")->status ==
                ebrp::ControllingLeafStatus::Replaced,
            "parent replacement was not atomic");

    require(scheduler.setStatus("wide.0", ebrp::ControllingLeafStatus::Closed,
                                "native_terminal_mip_optimal"),
            "optimal terminal leaf did not close");
    require(near(scheduler.findLeaf("wide.0")->lower_bound, 0.3),
            "optimal terminal closure replaced its native bound by cutoff");
}

void terminalMipChecks() {
    ebrp::FixedIntervalMipOutcome optimal;
    optimal.attempted = optimal.available = true;
    optimal.solver_finalization_reached = true;
    optimal.model_fingerprint_matches_request = true;
    optimal.exact_zero_gap_roundtrip = true;
    optimal.feasibility_consistency_gate = true;
    optimal.terminal_mip = true;
    optimal.optimal = true;
    optimal.native_bound_available = true;
    optimal.native_bound = 0.4;
    auto close = ebrp::evaluatePaperTerminalMipDecision(optimal);
    require(close.valid && close.close_leaf && !close.leave_open_and_stop,
            "native optimal terminal MIP did not close once");

    auto interrupted = optimal;
    interrupted.optimal = false;
    interrupted.native_bound_available = true;
    interrupted.interrupted = true;
    auto stop = ebrp::evaluatePaperTerminalMipDecision(interrupted);
    require(stop.valid && !stop.close_leaf && stop.leave_open_and_stop,
            "global deadline interruption did not leave terminal leaf open");

    auto lp = optimal;
    lp.terminal_mip = false;
    lp.lp_relaxation = true;
    auto no_integer_certificate = ebrp::evaluatePaperTerminalMipDecision(lp);
    require(!no_integer_certificate.valid && !no_integer_certificate.close_leaf,
            "LP result was treated as an integer terminal certificate");
}

void deterministicGenerationStopChecks() {
    const std::filesystem::path first_path =
        "round27_hga_repeatability_first.csv";
    const std::filesystem::path second_path =
        "round27_hga_repeatability_second.csv";
    ebrp::HgaTgbcOptions options;
    options.seed = 20260626u;
    options.pop_size = 4;
    options.iterations = 1;
    options.stop_mode = "generation-stagnation";
    options.no_improve_generation_limit = 5;
    options.generation_log_path = first_path;
    const ebrp::Instance instance = deterministicHgaInstance();
    const ebrp::HgaTgbcResult first =
        ebrp::runHgaTgbcNative(instance, options);
    options.generation_log_path = second_path;
    const ebrp::HgaTgbcResult second =
        ebrp::runHgaTgbcNative(instance, options);
    require(first.stop_mode == "generation-stagnation" &&
                first.generations_since_improvement == 5 &&
                first.total_generations >= 5,
            "generation-stagnation rule did not terminate exactly");
    require(first.total_generations == second.total_generations &&
                first.objective_improvement_count ==
                    second.objective_improvement_count &&
                first.decoder_calls == second.decoder_calls &&
                near(first.final_fitness, second.final_fitness) &&
                near(first.verified_objective, second.verified_objective) &&
                first.found == second.found,
            "same-seed generation HGA telemetry is nondeterministic");
    require(readAll(first_path) == readAll(second_path),
            "same-seed HGA generation trajectories differ");
    std::filesystem::remove(first_path);
    std::filesystem::remove(second_path);
}

} // namespace

int main() {
    try {
        splitDecisionChecks();
        schedulerAndCoverageChecks();
        terminalMipChecks();
        deterministicGenerationStopChecks();
        std::cout << "Round27PaperSchedulingTests passed " << checks
                  << " checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round27PaperSchedulingTests failed after " << checks
                  << " checks: " << error.what() << '\n';
        return 1;
    }
}
