#include "GurobiCertificate.hpp"
#include "InventoryRouteCuts.hpp"
#include "InventoryRouteRootClosure.hpp"
#include "PaperK1AmSf.hpp"
#include "Round50IntervalMip.hpp"
#include "Round53CallbackIsolation.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

bool contains(const std::vector<std::string>& values,
              const std::string& value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

ebrp::InventoryRouteLpState stateWithArcLevel(double level) {
    ebrp::InventoryRouteLpState state;
    state.station_count = 2;
    state.vehicle_capacities = {4};
    state.initial_inventory = {0, 4, 0};
    state.final_inventory = {0, 0, 4};
    state.final_inventory_lower = state.final_inventory;
    state.final_inventory_upper = state.final_inventory;
    for (int from = 0; from <= 2; ++from) {
        for (int to = 0; to <= 2; ++to) {
            if (from == to) continue;
            double value = 0.0;
            if ((from == 0 && to == 1) || (from == 1 && to == 2) ||
                (from == 2 && to == 0)) value = level;
            state.route_arcs.push_back({0, from, to, value});
        }
    }
    return state;
}

ebrp::FixedIntervalMipOutcome fakeLpOutcome(double level, double work) {
    const auto state = stateWithArcLevel(level);
    ebrp::FixedIntervalMipOutcome out;
    out.attempted = true;
    out.available = true;
    out.solver_finalization_reached = true;
    out.optimal = true;
    out.lp_relaxation = true;
    out.lp_terminal_valid = true;
    out.native_bound_available = true;
    out.native_bound = level;
    out.lp_objective_value_available = true;
    out.lp_objective_value = level;
    out.lp_primal_dual_evidence_available = true;
    out.model_fingerprint_matches_request = true;
    out.exact_zero_gap_roundtrip = true;
    out.additional_linear_rows_valid = true;
    out.work = work;
    out.solver_runtime_seconds = work / 10.0;
    out.simplex_iterations = work * 2.0;
    out.model_read_seconds = 0.01;
    for (int i = 1; i <= 2; ++i) {
        ebrp::FixedIntervalLpVariableEvidence variable;
        variable.name = "Y_" + std::to_string(i);
        variable.original_type = 'I';
        variable.lower_bound = state.final_inventory_lower[
            static_cast<std::size_t>(i)];
        variable.upper_bound = state.final_inventory_upper[
            static_cast<std::size_t>(i)];
        variable.primal_value = state.final_inventory[
            static_cast<std::size_t>(i)];
        out.lp_primal_dual_variable_evidence.push_back(variable);
    }
    for (const auto& arc : state.route_arcs) {
        ebrp::FixedIntervalLpVariableEvidence variable;
        variable.name = "x_0_" + std::to_string(arc.from) + "_" +
            std::to_string(arc.to);
        variable.original_type = 'B';
        variable.lower_bound = 0.0;
        variable.upper_bound = 1.0;
        variable.primal_value = arc.value;
        out.lp_primal_dual_variable_evidence.push_back(variable);
    }
    return out;
}

class FakeBackend final : public ebrp::FixedIntervalMipBackend {
public:
    std::vector<ebrp::FixedIntervalMipOutcome> outcomes;
    std::vector<ebrp::FixedIntervalMipRequest> requests;
    std::size_t next = 0;

    ebrp::FixedIntervalMipCapabilities capabilities() const override {
        ebrp::FixedIntervalMipCapabilities out;
        out.available = true;
        out.backend = "fake";
        return out;
    }
    ebrp::FixedIntervalMipOutcome solve(
        const ebrp::FixedIntervalMipRequest& request) override {
        requests.push_back(request);
        if (next >= outcomes.size()) {
            ebrp::FixedIntervalMipOutcome invalid;
            invalid.failure_reason = "fake_outcome_exhausted";
            return invalid;
        }
        return outcomes[next++];
    }
    ebrp::FixedIntervalMipBackendStats stats() const override { return {}; }
};

std::string readText(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    std::ostringstream out;
    out << in.rdbuf();
    return out.str();
}

std::size_t countToken(const std::string& text, const std::string& token) {
    std::size_t count = 0;
    std::size_t position = 0;
    while ((position = text.find(token, position)) != std::string::npos) {
        ++count;
        position += token.size();
    }
    return count;
}

} // namespace

int main() {
    try {
        int covered = 0;
        auto cover = [&](bool condition, const std::string& name) {
            require(condition, name);
            ++covered;
        };

        ebrp::SolveOptions preset;
        ebrp::configurePaperK1AmSfOverrides(preset);
        cover(preset.algorithm_preset == "paper-k1-am-sf" &&
              preset.frontier_execution_mode == "external-gini-tree",
              "1 preset parsing semantics");
        ebrp::SolveOptions alias_a, alias_b;
        cover(ebrp::isPaperK1AmSfPresetOrAlias("k1-am-f0") &&
              ebrp::isPaperK1AmSfPresetOrAlias("paper-k1-am-f0"),
              "2 legacy aliases accepted");
        ebrp::configurePaperK1AmSfOverrides(alias_a);
        ebrp::configurePaperK1AmSfOverrides(alias_b);
        cover(alias_a.algorithm_preset == alias_b.algorithm_preset &&
              alias_a.external_gini_interval_mip_policy ==
                  alias_b.external_gini_interval_mip_policy,
              "3 alias equivalence");
        cover(preset.k1_am_sf_controller_enabled &&
              preset.split_threshold == 0.08,
              "4 tau exact roundtrip");
        const auto f0 = ebrp::parseRound50IntervalMipPolicy(
            "interval-mip-core-no-exhaustive-subset-duration");
        cover(f0.valid && f0.subset_duration_big_m == "off",
              "5 F0 exhaustive rows omitted");
        cover(contains(ebrp::paperK1AmSfActiveFamilies(),
                       "connectivity_flow_formulation") &&
              contains(ebrp::paperK1AmSfActiveFamilies(),
                       "sp_product_objective_estimator"),
              "6 active family registry");
        cover(contains(ebrp::paperK1AmSfInactiveFamilies(),
                       "inventory_route_root_closure") &&
              !contains(ebrp::paperK1AmSfActiveFamilies(),
                        "inventory_route_root_closure"),
              "7 inactive family exclusion");

        const std::filesystem::path source = EXACT_EBRP_SOURCE_DIR;
        const std::filesystem::path fingerprint_manifest = source /
            "results/gf_k1_am_sf_inventory_route_round54/"
            "round53_pgrb_certificate_correction/"
            "round53_pgrb_expected_fingerprints.json";
        const std::string fingerprints = readText(fingerprint_manifest);
        cover(countToken(fingerprints,
                         "expected_gurobi_model_fingerprint") == 12,
              "8 P-GRB expected fingerprint binding");
        ebrp::GurobiCertificateInput certificate;
        certificate.status = ebrp::kGurobiStatusOptimal;
        certificate.optimize_returned = true;
        certificate.solver_finalization_completed = true;
        certificate.complete_original_model_scope = true;
        certificate.model_configuration_valid = true;
        certificate.lifecycle_valid = true;
        certificate.executable_fingerprint_matches_manifest = true;
        certificate.model_fingerprint_matches_manifest = false;
        certificate.no_tailored_or_external_information = true;
        certificate.relative_gap_requested_exact_zero = true;
        certificate.relative_gap_readback_exact_zero = true;
        certificate.absolute_gap_requested_exact_zero = true;
        certificate.absolute_gap_readback_exact_zero = true;
        certificate.finite_solution_available = true;
        certificate.independently_verified_original_feasible = true;
        certificate.objective_recomputed = true;
        const auto rejected =
            ebrp::evaluateGurobiEngineeringExactCertificate(certificate);
        cover(!rejected.strict_certified_original_problem &&
              rejected.rejection_reason.find("model_fingerprint_mismatch") !=
                  std::string::npos,
              "9 fingerprint mismatch rejection");

        const auto integer_state = stateWithArcLevel(1.0);
        const auto in_valid = ebrp::separateInventoryRouteCut(
            integer_state, ebrp::InventoryRouteCutKind::MixedInbound);
        cover(in_valid.valid && !in_valid.violated,
              "10 IR-IN integer validity");
        const auto out_valid = ebrp::separateInventoryRouteCut(
            integer_state, ebrp::InventoryRouteCutKind::MixedOutbound);
        cover(out_valid.valid && !out_valid.violated,
              "11 IR-OUT integer validity");
        const auto projected_valid = ebrp::separateInventoryRouteCut(
            integer_state, ebrp::InventoryRouteCutKind::ProjectedInbound);
        cover(projected_valid.valid && !projected_valid.violated,
              "12 projected cut validity");

        auto heterogeneous = stateWithArcLevel(0.0);
        heterogeneous.vehicle_capacities = {2, 5};
        heterogeneous.route_arcs.clear();
        for (int k = 0; k < 2; ++k) {
            for (int from = 0; from <= 2; ++from) {
                for (int to = 0; to <= 2; ++to) {
                    if (from == to) continue;
                    const double value = (from == 1 && to == 2)
                        ? (k == 0 ? 0.5 : 0.2) : 0.0;
                    heterogeneous.route_arcs.push_back({k, from, to, value});
                }
            }
        }
        const double hetero_violation = ebrp::recomputeInventoryRouteViolation(
            heterogeneous, ebrp::InventoryRouteCutKind::MixedInbound, {2});
        cover(std::fabs(hetero_violation - 2.0) <= 1e-12,
              "13 heterogeneous capacities");

        auto empty_state = stateWithArcLevel(0.0);
        empty_state.final_inventory = empty_state.initial_inventory;
        empty_state.final_inventory_lower = empty_state.final_inventory;
        empty_state.final_inventory_upper = empty_state.final_inventory;
        const auto empty_cut = ebrp::separateInventoryRouteCut(
            empty_state, ebrp::InventoryRouteCutKind::MixedInbound);
        cover(empty_cut.valid && empty_cut.subset.empty() && !empty_cut.violated,
              "14 empty subset no-cut result");
        auto full_state = stateWithArcLevel(0.0);
        full_state.initial_inventory = {0, 0, 0};
        full_state.final_inventory = {0, 2, 2};
        full_state.final_inventory_lower = full_state.final_inventory;
        full_state.final_inventory_upper = full_state.final_inventory;
        const auto full_cut = ebrp::separateInventoryRouteCut(
            full_state, ebrp::InventoryRouteCutKind::MixedInbound);
        cover(full_cut.valid && full_cut.subset == std::vector<int>({1, 2}),
              "15 full station subset supported");

        const auto fractional = stateWithArcLevel(0.25);
        const auto in_cut = ebrp::separateInventoryRouteCut(
            fractional, ebrp::InventoryRouteCutKind::MixedInbound);
        const auto out_cut = ebrp::separateInventoryRouteCut(
            fractional, ebrp::InventoryRouteCutKind::MixedOutbound);
        cover(in_cut.valid &&
              std::fabs(in_cut.mincut_objective -
                        in_cut.direct_recomputed_objective) <= 1e-12,
              "16 exact min-cut reconstruction");
        cover(in_cut.subset == std::vector<int>({2}) &&
              out_cut.subset == std::vector<int>({1}),
              "17 inbound outbound orientation");
        const auto in_cut_again = ebrp::separateInventoryRouteCut(
            fractional, ebrp::InventoryRouteCutKind::MixedInbound);
        cover(in_cut.subset == in_cut_again.subset &&
              in_cut.canonical_signature == in_cut_again.canonical_signature,
              "18 deterministic tie behavior");
        cover(std::fabs(ebrp::recomputeInventoryRouteViolation(
                  fractional, in_cut.kind, in_cut.subset) -
                  in_cut.raw_violation) <= 1e-12,
              "19 direct violation recomputation");
        cover(!in_cut.canonical_signature.empty() &&
              in_cut.canonical_signature.find("IR-IN") == 0,
              "20 canonical cut signature");
        std::set<std::string> signatures;
        cover(signatures.insert(in_cut.canonical_signature).second &&
              !signatures.insert(in_cut.canonical_signature).second,
              "21 duplicate rejection");
        const auto projected_cut = ebrp::separateInventoryRouteCut(
            fractional, ebrp::InventoryRouteCutKind::ProjectedInbound);
        cover(projected_cut.subset == in_cut.subset &&
              projected_cut.raw_violation == in_cut.raw_violation,
              "22 mixed projected dominance identity");

        ebrp::Instance instance;
        instance.V = 2;
        instance.M = 1;
        instance.Q = {4};
        instance.initial = {0, 4, 0};
        FakeBackend backend;
        backend.outcomes = {fakeLpOutcome(0.25, 2.0),
                            fakeLpOutcome(1.0, 3.0)};
        ebrp::FixedIntervalMipRequest request;
        request.leaf_id = "test";
        request.canonical_model_fingerprint = "model";
        request.global_deadline_remaining_seconds = 100.0;
        const auto closure = ebrp::runInventoryRouteRootClosure(
            backend, instance, request,
            ebrp::InventoryRouteClosureVariant::MixedFull);
        cover(closure.valid && closure.converged && closure.rounds.size() == 2,
              "23 finite root closure termination");
        cover(backend.requests[0].capture_lp_primal_dual_evidence &&
              !backend.requests[0].incremental_model_reuse_enabled &&
              backend.requests[1].additional_linear_rows.size() == 2,
              "24 integer type restoration by fresh rebuild contract");
        const auto ir1 = ebrp::parseRound50IntervalMipPolicy("ir1");
        cover(!ebrp::round53CallbackMipNodeEnabled(ir1) &&
              !ebrp::round53CallbackSubmissionEnabled(ir1),
              "25 terminal callback off");
        cover(!ebrp::round53CallbackPreCrushEnabled(ir1),
              "26 terminal PreCrush default");
        cover(std::fabs(closure.cumulative_lp_work - 5.0) <= 1e-12 &&
              std::fabs(closure.cumulative_lp_runtime_seconds - 0.5) <= 1e-12,
              "27 closure overhead accounting");
        cover(backend.requests[0].global_deadline_remaining_seconds >=
                  backend.requests[1].global_deadline_remaining_seconds,
              "27b closure propagates remaining process allowance");
        FakeBackend bad_backend;
        auto invalid = fakeLpOutcome(0.25, 1.0);
        invalid.lp_primal_dual_evidence_available = false;
        bad_backend.outcomes = {invalid};
        const auto bad_closure = ebrp::runInventoryRouteRootClosure(
            bad_backend, instance, request,
            ebrp::InventoryRouteClosureVariant::MixedFull);
        cover(!bad_closure.valid && bad_closure.fallback_required,
              "28 F0 fallback after invalid closure");
        cover(backend.requests[0].additional_linear_rows.empty() &&
              backend.requests[1].leaf_id != backend.requests[0].leaf_id,
              "29 no cut leakage between intervals");
        cover(ebrp::parseRound50IntervalMipPolicy("ir1").name ==
                  ebrp::parseRound50IntervalMipPolicy("IR1").name &&
              ir1.branching == ebrp::Round50BranchingPolicy::Default,
              "30 no instance size time dispatch");
        cover(preset.initial_gini_interval_count == 1 &&
              preset.split_point_rule == "midpoint" &&
              preset.split_score_rule == "balanced-normalized-closure" &&
              preset.round40_c6_coarse_start == "off" &&
              preset.round47_c6_adaptive_mass == "off" &&
              preset.round45_point_rule == "midpoint" &&
              preset.round48_k1_amf == "off" &&
              preset.round49_k1_am_rc == "off",
              "31 K1 controller equivalence");
        cover(ir1.subset_duration_big_m == f0.subset_duration_big_m &&
              ir1.round53_callback_mode == f0.round53_callback_mode &&
              ir1.branching == f0.branching,
              "32 strict certificate invariance");
        cover(in_cut.sense == '<' && out_cut.sense == '<' &&
              projected_cut.sense == '>',
              "33 row orientation readback contract");
        cover(closure.accepted_cuts.size() == 2 &&
              closure.duplicate_rejections == 0,
              "34 complete accepted cut pool");

        std::cout << "Round54MainlineAndInventoryRouteTests passed "
                  << covered << " checks\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Round54MainlineAndInventoryRouteTests failed: "
                  << ex.what() << '\n';
        return 1;
    }
}
