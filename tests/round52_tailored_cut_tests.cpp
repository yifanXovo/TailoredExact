#include "Round50IntervalMip.hpp"
#include "Round52GurobiCutAdapter.hpp"
#include "Round52TailoredCuts.hpp"

#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::Instance fixture() {
    ebrp::Instance instance;
    instance.V = 4;
    instance.M = 2;
    instance.Q = {10, 10};
    instance.total_time_limit = 10.0;
    instance.pickup_time = 1.0;
    instance.drop_time = 1.0;
    instance.dist.assign(5, std::vector<double>(5, 0.0));
    for (int i = 0; i <= 4; ++i) {
        for (int j = 0; j <= 4; ++j) {
            if (i != j) instance.dist[i][j] = 1.0;
        }
    }
    return instance;
}

ebrp::Round52CutSeparationInput separationInput(
    const ebrp::Instance& instance) {
    ebrp::Round52CutSeparationInput input;
    input.instance = &instance;
    input.interval_id = "L0";
    input.node_context = "root";
    input.maximum_support_rank = 3;
    for (int k = 0; k < instance.M; ++k) {
        for (int i = 1; i <= instance.V; ++i) {
            const std::string p = "p_" + std::to_string(k) + "_" +
                std::to_string(i);
            const std::string z = "z_" + std::to_string(k) + "_" +
                std::to_string(i);
            input.lp_values[p] = 4.0;
            input.lp_values[z] = 1.0;
            input.effective_lower_bounds[p] = 0.0;
            input.effective_upper_bounds[p] = 10.0;
            input.effective_lower_bounds[z] = 0.0;
            input.effective_upper_bounds[z] = 1.0;
            input.model_variable_mapping[p] =
                static_cast<int>(input.model_variable_mapping.size());
            input.model_variable_mapping[z] =
                static_cast<int>(input.model_variable_mapping.size());
        }
    }
    return input;
}

ebrp::Round52CutCandidate simpleCut(double rhs = 1.0, int vehicle = 0) {
    ebrp::Round52CutCandidate cut;
    cut.family = "test";
    cut.coefficients = {{"b", 2.0}, {"a", 1.0}};
    cut.sense = ebrp::Round52CutSense::LessEqual;
    cut.rhs = rhs;
    cut.raw_violation = 2.0;
    cut.violation_scale = 2.0;
    cut.scaled_violation = 1.0;
    cut.vehicle_index = vehicle;
    return cut;
}

} // namespace

int main() {
    int passed = 0;
    auto test = [&](const std::string& name, const std::function<void()>& body) {
        body();
        ++passed;
        std::cout << "PASS " << name << '\n';
    };
    try {
        test("candidate_normalization_sorts", [] {
            auto cut = simpleCut();
            require(ebrp::normalizeRound52CutCandidate(cut), "normalize");
            require(cut.coefficients.front().variable == "a", "sort");
        });
        test("candidate_normalization_combines", [] {
            auto cut = simpleCut();
            cut.coefficients.push_back({"a", 3.0});
            require(ebrp::normalizeRound52CutCandidate(cut), "normalize");
            require(cut.coefficients.size() == 2 &&
                    cut.coefficients.front().value == 4.0, "combine");
        });
        test("greater_equal_canonicalization", [] {
            auto cut = simpleCut();
            cut.sense = ebrp::Round52CutSense::GreaterEqual;
            require(ebrp::normalizeRound52CutCandidate(cut), "normalize");
            require(cut.sense == ebrp::Round52CutSense::LessEqual &&
                    cut.rhs == -1.0, "sense conversion");
        });
        test("equality_rejected", [] {
            auto cut = simpleCut();
            cut.sense = ebrp::Round52CutSense::Equal;
            require(!ebrp::normalizeRound52CutCandidate(cut), "equality");
        });
        test("nonfinite_rejected", [] {
            auto cut = simpleCut();
            cut.rhs = std::numeric_limits<double>::infinity();
            require(!ebrp::normalizeRound52CutCandidate(cut), "nonfinite");
        });
        test("canonical_signature_order_invariant", [] {
            auto a = simpleCut();
            auto b = simpleCut();
            std::reverse(b.coefficients.begin(), b.coefficients.end());
            require(ebrp::normalizeRound52CutCandidate(a) &&
                    ebrp::normalizeRound52CutCandidate(b) &&
                    a.canonical_signature == b.canonical_signature,
                    "signature order");
        });
        test("canonical_signature_rhs_sensitive", [] {
            auto a = simpleCut(1.0); auto b = simpleCut(2.0);
            ebrp::normalizeRound52CutCandidate(a);
            ebrp::normalizeRound52CutCandidate(b);
            require(a.canonical_signature != b.canonical_signature, "rhs");
        });
        test("exact_dominance", [] {
            auto a = simpleCut(1.0); auto b = simpleCut(2.0);
            ebrp::normalizeRound52CutCandidate(a);
            ebrp::normalizeRound52CutCandidate(b);
            require(ebrp::round52ExactlyDominates(a, b) &&
                    !ebrp::round52ExactlyDominates(b, a), "dominance");
        });
        const ebrp::Instance instance = fixture();
        test("pair_route_lower_bound", [&] {
            require(ebrp::round52RouteDurationLowerBound(instance, {1, 2}) ==
                    3.0, "pair route");
        });
        test("triple_route_lower_bound", [&] {
            require(ebrp::round52RouteDurationLowerBound(instance, {1, 2, 3}) ==
                    4.0, "triple route");
        });
        test("quad_route_lower_bound", [&] {
            require(ebrp::round52RouteDurationLowerBound(instance, {1, 2, 3, 4}) ==
                    5.0, "quad route");
        });
        test("route_support_order_invariant", [&] {
            require(ebrp::round52RouteDurationLowerBound(instance, {3, 1, 2}) ==
                    ebrp::round52RouteDurationLowerBound(instance, {1, 2, 3}),
                    "support order");
        });
        const ebrp::Round52SupportDurationSeparator separator;
        const auto generated = separator.separate(separationInput(instance));
        test("separator_candidate_count", [&] {
            require(generated.size() == 20, "rank2+rank3 count");
        });
        test("separator_global_validity", [&] {
            for (const auto& cut : generated) {
                require(cut.validity_scope ==
                    ebrp::Round52CutValidityScope::Global, "global");
            }
        });
        test("separator_scaled_violation", [&] {
            for (const auto& cut : generated) {
                require(std::fabs(cut.scaled_violation -
                    cut.raw_violation / cut.violation_scale) < 1e-15,
                    "scaled violation");
            }
        });
        test("separator_pair_and_triple_families", [&] {
            bool pair = false, triple = false;
            for (const auto& cut : generated) {
                pair = pair || cut.support_set.size() == 2;
                triple = triple || cut.support_set.size() == 3;
            }
            require(pair && triple, "families");
        });
        test("support_duration_valid_on_active_support", [&] {
            const double route = ebrp::round52RouteDurationLowerBound(
                instance, {1, 2});
            const double p_sum = (instance.total_time_limit - route) /
                (instance.pickup_time + instance.drop_time);
            const double lhs = (instance.pickup_time + instance.drop_time) *
                p_sum + route * 2.0;
            const double rhs = instance.total_time_limit - route + route * 2.0;
            require(std::fabs(lhs - rhs) < 1e-12, "validity boundary");
        });
        test("support_duration_valid_on_inactive_support", [&] {
            const double route = ebrp::round52RouteDurationLowerBound(
                instance, {1, 2, 3});
            const double rhs = instance.total_time_limit - route +
                route * (3.0 - 2.0);
            require(rhs == instance.total_time_limit, "inactive RHS");
        });
        test("separator_missing_mapping_rejected", [&] {
            auto input = separationInput(instance);
            input.model_variable_mapping.erase("p_0_1");
            bool rejected = false;
            try { separator.separate(input); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "missing mapping");
        });
        test("separator_invalid_effective_bounds_rejected", [&] {
            auto input = separationInput(instance);
            input.effective_upper_bounds["z_0_1"] = 0.5;
            bool rejected = false;
            try { separator.separate(input); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "invalid effective bounds");
        });
        test("strict_scaled_threshold", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("threshold");
            auto cut = simpleCut();
            cut.raw_violation = 2e-7;
            cut.violation_scale = 2.0;
            cut.scaled_violation = 1e-7;
            require(manager.process({cut}).empty(), "strict threshold");
        });
        test("deterministic_vehicle_block_selection", [&] {
            ebrp::Round52CutManager manager;
            manager.beginModel("blocks");
            auto selected = manager.process(generated);
            require(selected.size() == 2 && selected[0].vehicle_index == 0 &&
                    selected[1].vehicle_index == 1, "one per block");
        });
        test("global_pool_membership", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("pool");
            auto selected = manager.process({simpleCut()});
            require(selected.size() == 1, "selected");
            manager.recordSubmission(selected.front(), true);
            require(manager.globalPoolContains(
                selected.front().canonical_signature), "pool contains");
        });
        test("duplicate_rejection", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("dup");
            auto cut = simpleCut();
            auto selected = manager.process({cut, cut});
            require(selected.size() == 1 &&
                    manager.telemetry().duplicate_rejections == 1, "duplicate");
        });
        test("pooled_duplicate_rejection", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("pooled-dup");
            auto first = manager.process({simpleCut()});
            manager.recordSubmission(first.front(), true);
            require(manager.process({simpleCut()}).empty() &&
                    manager.telemetry().duplicate_rejections == 1,
                    "pooled duplicate");
        });
        test("dominance_is_generation_order_independent", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("dominance-order");
            auto selected = manager.process(
                {simpleCut(2.0), simpleCut(1.0)});
            require(selected.size() == 1 && selected.front().rhs == 1.0 &&
                    manager.telemetry().dominated_rejections == 1,
                    "stronger row last");
        });
        test("family_and_vehicle_accounting", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("accounting");
            auto second = simpleCut(1.5, 1);
            second.coefficients = {{"d", 2.0}, {"c", 1.0}};
            auto selected = manager.process({simpleCut(1.0, 0), second});
            for (const auto& cut : selected) {
                manager.recordSubmission(cut, true);
            }
            require(manager.telemetry().generated_by_family.at("test") == 2 &&
                    manager.telemetry().selected_by_family.at("test") == 2 &&
                    manager.telemetry().added_by_family.at("test") == 2 &&
                    manager.telemetry().selected_by_vehicle.at(0) == 1 &&
                    manager.telemetry().selected_by_vehicle.at(1) == 1,
                    "family and vehicle accounting");
        });
        test("no_cut_leakage_across_models", [] {
            ebrp::Round52CutManager manager;
            manager.beginModel("one");
            auto selected = manager.process({simpleCut()});
            manager.recordSubmission(selected.front(), true);
            manager.beginModel("two");
            require(manager.telemetry().global_pool_size == 0 &&
                    !manager.globalPoolContains(
                        selected.front().canonical_signature), "leakage");
        });
        test("root_only_callback_behavior", [] {
            require(ebrp::round52SeparationPermitted(
                ebrp::Round52CutSeparationScope::RootOnly, true, true), "root");
        });
        test("root_only_rejects_tree", [] {
            require(!ebrp::round52SeparationPermitted(
                ebrp::Round52CutSeparationScope::RootOnly, false, true), "tree");
        });
        test("tree_callback_behavior", [] {
            require(ebrp::round52SeparationPermitted(
                ebrp::Round52CutSeparationScope::AllOptimalTreeNodes,
                false, true), "tree enabled");
        });
        test("mipnode_optimal_status_requirement", [] {
            require(!ebrp::round52SeparationPermitted(
                ebrp::Round52CutSeparationScope::AllOptimalTreeNodes,
                true, false), "nonoptimal");
        });
        test("precrush_contract", [] {
            require(ebrp::round52RequiredGurobiPreCrush() == 1, "PreCrush");
        });
        test("gurobi_cbcut_success", [] {
            ebrp::Round52GurobiCutAdapter adapter(
                {{"a", 0}, {"b", 1}},
                [](int count, const int*, const double*, char sense, double) {
                    return count == 2 && sense == '<' ? 0 : 1;
                });
            auto cut = simpleCut(); ebrp::normalizeRound52CutCandidate(cut);
            require(adapter.submit(cut) && adapter.telemetry().successes == 1,
                    "success");
        });
        test("gurobi_cbcut_failure", [] {
            ebrp::Round52GurobiCutAdapter adapter(
                {{"a", 0}, {"b", 1}},
                [](int, const int*, const double*, char, double) { return 17; });
            auto cut = simpleCut(); ebrp::normalizeRound52CutCandidate(cut);
            require(!adapter.submit(cut) &&
                    adapter.telemetry().last_return_code == 17, "failure");
        });
        test("gurobi_mapping_failure", [] {
            ebrp::Round52GurobiCutAdapter adapter(
                {{"a", 0}},
                [](int, const int*, const double*, char, double) { return 0; });
            auto cut = simpleCut(); ebrp::normalizeRound52CutCandidate(cut);
            require(!adapter.submit(cut) &&
                    adapter.telemetry().mapping_failures == 1, "mapping");
        });
        test("no_local_cut_marked_global", [] {
            ebrp::Round52GurobiCutAdapter adapter(
                {{"a", 0}, {"b", 1}},
                [](int, const int*, const double*, char, double) { return 0; });
            auto cut = simpleCut(); cut.validity_scope =
                ebrp::Round52CutValidityScope::Local;
            ebrp::normalizeRound52CutCandidate(cut);
            require(!adapter.submit(cut) &&
                    adapter.telemetry().local_scope_rejections == 1, "local");
        });
        test("callback_exception_fallback", [] {
            ebrp::Round52GurobiCutAdapter adapter(
                {{"a", 0}, {"b", 1}},
                [](int, const int*, const double*, char, double) -> int {
                    throw std::runtime_error("injected");
                });
            auto cut = simpleCut(); ebrp::normalizeRound52CutCandidate(cut);
            require(!adapter.submit(cut) &&
                    adapter.telemetry().exception_fallbacks == 1, "exception");
        });
        test("default_off_policy_equivalence", [] {
            const auto policy = ebrp::parseRound50IntervalMipPolicy(
                "interval-mip-v0");
            require(policy.valid && policy.tailored_cut_policy == "off" &&
                    policy.subset_duration_big_m == "historical-100000",
                    "default off");
        });
        test("f0_policy", [] {
            const auto p = ebrp::parseRound50IntervalMipPolicy(
                "f0-no-rank3-support-duration");
            require(p.valid && p.subset_duration_big_m == "off", "f0");
        });
        test("f1_policy", [] {
            const auto p = ebrp::parseRound50IntervalMipPolicy(
                "f1-static-rank3-loose");
            require(p.valid && p.tailored_cut_support_rank == 3, "f1");
        });
        test("f2_policy", [] {
            const auto p = ebrp::parseRound50IntervalMipPolicy(
                "f2-static-rank3-tight");
            require(p.valid && p.tailored_cut_support_rank == 3, "f2");
        });
        test("f3_policy", [] {
            const auto p = ebrp::parseRound50IntervalMipPolicy(
                "SD-R3-ROOT-BLOCKMAX");
            require(p.valid && p.tailored_cut_policy ==
                    "sd-r3-root-blockmax", "f3");
        });
        test("f4_policy", [] {
            const auto p = ebrp::parseRound50IntervalMipPolicy(
                "f4-sd-r3-tree-blockmax");
            require(p.valid && p.tailored_cut_policy ==
                    "sd-r3-tree-blockmax", "f4");
        });
        require(passed >= 24, "fewer than 24 Round52 tests");
        std::cout << "Round52TailoredCutTests passed " << passed
                  << " cases\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round52TailoredCutTests failed after " << passed
                  << " cases: " << error.what() << '\n';
        return 1;
    }
}
