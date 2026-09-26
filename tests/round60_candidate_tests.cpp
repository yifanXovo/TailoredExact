#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "HgaTgbcRunner.hpp"
#include "MipStartMapping.hpp"
#include "PaperK1AmSf.hpp"
#include "Round60Candidates.hpp"

#include <cmath>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::Instance candidateInstance() {
    ebrp::Instance instance;
    instance.name = "round60_unit_candidate";
    instance.V = 3;
    instance.M = 2;
    instance.Q = {1, 3};
    instance.capacity = {0, 5, 5, 5};
    instance.initial = {0, 4, 0, 2};
    instance.target = {0, 2, 2, 2};
    instance.weights = {0.0, 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0};
    instance.min_ratio = {0.0, 0.0, 0.0, 0.0};
    instance.dist = {
        {0.0, 1.0, 1.0, 1.0},
        {1.0, 0.0, 1.0, 1.0},
        {1.0, 1.0, 0.0, 1.0},
        {1.0, 1.0, 1.0, 0.0},
    };
    instance.pickup_time = 0.5;
    instance.drop_time = 0.5;
    instance.total_time_limit = 20.0;
    return instance;
}

ebrp::RoutePlan loadedReturnRoute() {
    ebrp::RoutePlan route;
    route.vehicle = 1;
    route.nodes = {0, 1, 0};
    route.operations = {{1, 2, 0}};
    return route;
}

ebrp::RoutePlan balancedRoute() {
    ebrp::RoutePlan route;
    route.vehicle = 1;
    route.nodes = {0, 1, 2, 0};
    route.operations = {{1, 2, 0}, {2, 0, 2}};
    return route;
}

void defaultAndIdentityChecks() {
    require(ebrp::textSha256("abc") ==
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            "candidate content hashing must use canonical SHA-256");
    const ebrp::SolveOptions defaults;
    const ebrp::FixedIntervalMipRequest request_defaults;
    require(!defaults.round60_hga_publish_verified,
            "HGA event publishing must default off");
    require(defaults.round60_candidate_mode == "off",
            "candidate injection must default off");
    require(request_defaults.round60_candidate_mode == "off" &&
            request_defaults.round60_fixed_inventory.empty(),
            "native research controls must default off");

    ebrp::SolveOptions shared;
    ebrp::configurePaperK1AmSfCanonicalF0(shared);
    ebrp::SolveOptions preset;
    ebrp::configurePaperK1AmSfOverrides(preset);
    require(shared.gini_spread_cuts == preset.gini_spread_cuts &&
            shared.required_movement_cuts ==
                preset.required_movement_cuts &&
            shared.global_handling_capacity_cuts ==
                preset.global_handling_capacity_cuts &&
            shared.low_gini_ratio_band_tightening ==
                preset.low_gini_ratio_band_tightening &&
            shared.transfer_subset_capacity_cuts ==
                preset.transfer_subset_capacity_cuts &&
            shared.compact_bc_direct_gini_rows ==
                preset.compact_bc_direct_gini_rows &&
            shared.compact_bc_tight_mccormick ==
                preset.compact_bc_tight_mccormick &&
            shared.compact_bc_inventory_conservation ==
                preset.compact_bc_inventory_conservation &&
            shared.compact_bc_movement_reachability_domains ==
                preset.compact_bc_movement_reachability_domains &&
            shared.compact_bc_visit_inventory_linking ==
                preset.compact_bc_visit_inventory_linking &&
            shared.compact_bc_objective_estimator_cutoff ==
                preset.compact_bc_objective_estimator_cutoff &&
            shared.compact_bc_penalty_lb_closure ==
                preset.compact_bc_penalty_lb_closure &&
            shared.compact_bc_pairwise_transfer_compatibility ==
                preset.compact_bc_pairwise_transfer_compatibility &&
            shared.interval_oracle_penalty_domain_tightening ==
                preset.interval_oracle_penalty_domain_tightening,
            "preset and fixed-state entry must share canonical F0 flags");
}

void storeAndConstructionChecks() {
    const ebrp::Instance instance = candidateInstance();
    constexpr double lambda = 0.15;
    ebrp::VerifiedCandidateStore store;
    require(store.consider(instance, lambda, {}, "empty", "F0"),
            "verified empty route must be publishable");
    require(!store.consider(instance, lambda, {}, "duplicate", "F0"),
            "candidate hash must suppress duplicate submission");
    require(store.observations().back().duplicate,
            "duplicate observation must be explicit");
    const auto loaded = loadedReturnRoute();
    const auto loaded_verification =
        ebrp::verifySolution(instance, {loaded}, lambda);
    require(loaded_verification.feasible &&
            std::fabs(loaded_verification.route_duration[1] - 4.0) <= 1e-12,
            "loaded depot return must pay both pickup and unload time");
    require(store.consider(instance, lambda, {loaded}, "loaded", "F0"),
            "strictly improving loaded-return witness must publish");
    const auto balanced = balancedRoute();
    require(store.consider(instance, lambda, {balanced}, "balanced", "F0"),
            "zero-objective witness must publish");
    require(std::fabs(store.best().objective) <= 1e-12 &&
            store.best().final_inventory == instance.target,
            "published witness and objective must remain one snapshot");
    ebrp::RoutePlan invalid = balanced;
    invalid.operations[0].pickup = 4;
    require(!store.consider(instance, lambda, {invalid}, "invalid", "F0"),
            "invalid route must never enter verified store");
    ebrp::RoutePlan duplicate_vehicle = loaded;
    duplicate_vehicle.nodes = {0, 3, 0};
    duplicate_vehicle.operations = {{3, 1, 0}};
    require(!store.consider(instance, lambda,
                            {loaded, duplicate_vehicle},
                            "duplicate-vehicle", "F0"),
            "two routes may not claim the same vehicle");

    ebrp::Round60ConstructionInput input;
    input.model_identity = "F0|root";
    input.desired_inventory = instance.target;
    input.maximum_evaluations = 64;
    input.maximum_stations = 3;
    input.relaxation_values["z_1_1"] = 1.0;
    input.relaxation_values["x_1_0_1"] = 1.0;
    const auto first =
        ebrp::constructRound60BrpCandidate(instance, lambda, input);
    const auto second =
        ebrp::constructRound60BrpCandidate(instance, lambda, input);
    require(first.generated && first.candidate.verified,
            "bounded BRP construction must produce verified witness");
    require(first.objective_evaluations <= input.maximum_evaluations,
            "construction work limit must be enforced");
    require(first.candidate.content_sha256 ==
                second.candidate.content_sha256 &&
            ebrp::canonicalCandidateSerialization(first.candidate.routes) ==
                ebrp::canonicalCandidateSerialization(second.candidate.routes),
            "construction must be deterministic");
    require(first.candidate.routes.size() == 1 &&
            first.candidate.routes.front().vehicle == 1,
            "LP affinity and heterogeneous capacity must select feasible vehicle");
    require(ebrp::verifySolution(
                instance, first.candidate.routes, lambda).feasible,
            "constructed route must pass independent verifier");

    ebrp::Instance deadline_limited = instance;
    deadline_limited.total_time_limit = 2.9;
    const auto stopped = ebrp::constructRound60BrpCandidate(
        deadline_limited, lambda, input);
    require(!stopped.generated,
            "time-incompatible operations must not be published");
}

void mappingAndResidualChecks() {
    const ebrp::Instance instance = candidateInstance();
    ebrp::SolveOptions options;
    options.lambda = 0.15;
    ebrp::SolverNeutralModelDomain domain;
    domain.names = {"G", "r_min", "r_max", "W_SP", "Y_1", "Y_2",
                    "Y_3", "r_1", "r_2", "r_3", "e_1", "e_2",
                    "e_3", "h_1_2", "h_1_3", "h_2_3"};
    domain.lower_bounds.assign(domain.names.size(), -100.0);
    domain.upper_bounds.assign(domain.names.size(), 100.0);
    domain.variable_types.assign(domain.names.size(), 'C');
    const auto route = balancedRoute();
    const auto mapped = ebrp::mapVerifiedRoutesToCanonicalModel(
        instance, options, {route}, "round60", 0.0, 1.0, 1.0, domain);
    require(mapped.complete && mapped.bounds_valid &&
            mapped.integrality_valid,
            "verified route must map to complete supported semantic domain");
    const auto interval_rejected = ebrp::mapVerifiedRoutesToCanonicalModel(
        instance, options, {loadedReturnRoute()}, "round60", 0.0, 0.0,
        1.0, domain);
    require(!interval_rejected.complete &&
            !interval_rejected.interval_membership_valid,
            "interval-incompatible route must fail closed");
    const auto cutoff_rejected = ebrp::mapVerifiedRoutesToCanonicalModel(
        instance, options, {}, "round60", 0.0, 1.0, -1.0, domain);
    require(!cutoff_rejected.complete && !cutoff_rejected.cutoff_valid,
            "non-strict F<=U cutoff must reject only genuine violations");

    ebrp::SolverNeutralLinearModel linear;
    linear.variable_count = 2;
    linear.row_starts = {0, 2, 3, 4};
    linear.column_indices = {0, 1, 0, 1};
    linear.coefficients = {1.0, 1.0, 1.0, 1.0};
    linear.senses = {'=', '<', '>'};
    linear.rhs = {3.0, 2.0, 1.0};
    const auto valid = ebrp::validateCandidateLinearResidual(
        linear, {2.0, 1.0});
    require(valid.checked && valid.valid && valid.checked_rows == 3 &&
            valid.violated_rows == 0,
            "equality and inequality residuals must validate");
    const auto invalid = ebrp::validateCandidateLinearResidual(
        linear, {2.5, 0.25});
    require(invalid.checked && !invalid.valid &&
            invalid.violated_rows == 3 &&
            invalid.maximum_violation > 0.0,
            "all violated current-MIP rows must be counted");
}

void hgaPublicationChecks() {
    const ebrp::Instance instance = candidateInstance();
    ebrp::HgaTgbcOptions original;
    original.lambda = 0.15;
    original.seed = 20260626u;
    original.pop_size = 4;
    original.iterations = 1;
    original.max_time_seconds = 30;
    original.stop_mode = "generation-stagnation";
    original.no_improve_generation_limit = 2;
    const auto without_observer =
        ebrp::runHgaTgbcNative(instance, original);
    ebrp::HgaTgbcOptions publishing = original;
    publishing.publish_verified_improvements = true;
    const auto with_observer =
        ebrp::runHgaTgbcNative(instance, publishing);
    require(with_observer.total_generations ==
                without_observer.total_generations &&
            with_observer.decoder_calls == without_observer.decoder_calls &&
            std::fabs(with_observer.final_fitness -
                      without_observer.final_fitness) <= 1e-12,
            "candidate observation must not consume RNG or change logical HGA prefix");
    require(with_observer.retained_verified_event_candidate &&
            with_observer.published_candidate_count > 0 &&
            !with_observer.candidate_observer_failed,
            "HGA improvements must publish verified snapshots");

    const std::filesystem::path log_blocker =
        std::filesystem::temp_directory_path() /
        ("round60_candidate_log_parent_is_file_" + std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count()));
    {
        std::ofstream marker(log_blocker, std::ios::trunc);
        marker << "not a directory";
    }
    ebrp::HgaTgbcOptions logging_failure = publishing;
    logging_failure.verified_candidate_log_path =
        log_blocker / "candidate.csv";
    const auto fallback =
        ebrp::runHgaTgbcNative(instance, logging_failure);
    std::filesystem::remove(log_blocker);
    require(fallback.candidate_observer_failed &&
            !fallback.retained_verified_event_candidate &&
            std::fabs(fallback.final_fitness -
                      without_observer.final_fitness) <= 1e-12,
            "candidate log failure must disable publication without "
            "changing the underlying HGA search");

    ebrp::SolveOptions expired_process;
    expired_process.process_start_time = std::chrono::steady_clock::now();
    expired_process.process_start_time_valid = true;
    expired_process.process_wall_time_limit = 1e-6;
    expired_process.process_shutdown_margin_seconds = 0.0;
    ebrp::HgaTgbcOptions deadline = original;
    deadline.no_improve_generation_limit = 20;
    deadline.process_options = &expired_process;
    deadline.publish_verified_improvements = true;
    const auto retained = ebrp::runHgaTgbcNative(instance, deadline);
    require(retained.global_deadline_reached && retained.found &&
            retained.retained_verified_event_candidate,
            "deadline interruption must return latest verified event snapshot");
}

} // namespace

int main() {
    try {
        defaultAndIdentityChecks();
        storeAndConstructionChecks();
        mappingAndResidualChecks();
        hgaPublicationChecks();
        std::cout << "Round 60 verified-candidate checks passed.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Round 60 candidate test failure: "
                  << error.what() << '\n';
        return 1;
    }
}
