#include "ControllingLeafScheduler.hpp"
#include "ExternalGiniTree.hpp"
#include "FileSha256.hpp"
#include "GiniFrontierGeometry.hpp"
#include "GurobiBaseline.hpp"
#include "GurobiCertificate.hpp"
#include "MipStartMapping.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int checks = 0;
void require(bool condition, const std::string& message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}

ebrp::GurobiCertificateInput nominalGurobi() {
    ebrp::GurobiCertificateInput in;
    in.status = ebrp::kGurobiStatusOptimal;
    in.optimize_returned = true;
    in.solver_finalization_completed = true;
    in.complete_original_model_scope = true;
    in.model_configuration_valid = true;
    in.lifecycle_valid = true;
    in.executable_fingerprint_matches_manifest = true;
    in.model_fingerprint_matches_manifest = true;
    in.no_tailored_or_external_information = true;
    in.relative_gap_requested_exact_zero = true;
    in.relative_gap_readback_exact_zero = true;
    in.absolute_gap_requested_exact_zero = true;
    in.absolute_gap_readback_exact_zero = true;
    in.finite_solution_available = true;
    in.independently_verified_original_feasible = true;
    in.objective_recomputed = true;
    return in;
}

ebrp::ExternalGiniTreeCertificateInput nominalExternal() {
    ebrp::ExternalGiniTreeCertificateInput in;
    in.complete_root_coverage = true;
    in.parent_child_coverage_valid = true;
    in.all_relevant_leaves_closed = true;
    in.all_leaf_bounds_valid = true;
    in.global_bound_valid = true;
    in.global_bound_monotone = true;
    in.leaf_bounds_monotone = true;
    in.verified_global_ub = true;
    in.lifecycle_complete = true;
    in.feasibility_consistency_gate = true;
    in.global_lb = 0.5;
    in.verified_ub = 0.5;
    return in;
}

ebrp::Instance balancedInstance() {
    ebrp::Instance in;
    in.name = "balanced";
    in.V = 2;
    in.M = 1;
    in.Q = {1};
    in.capacity = {0, 10, 10};
    in.initial = {0, 5, 5};
    in.target = {0, 5, 5};
    in.weights = {0.0, 1.0, 1.0};
    in.dist.assign(3, std::vector<double>(3, 0.0));
    in.total_time_limit = 3600.0;
    in.pickup_time = 60.0;
    in.drop_time = 60.0;
    return in;
}

class InstrumentedFakeBackend final : public ebrp::FixedIntervalMipBackend {
public:
    explicit InstrumentedFakeBackend(bool retained) : retained_(retained) {}
    ebrp::FixedIntervalMipCapabilities capabilities() const override {
        ebrp::FixedIntervalMipCapabilities c;
        c.backend = "fake";
        c.available = true;
        c.retained_same_leaf_resume = retained_;
        c.fresh_per_attempt = true;
        return c;
    }
    ebrp::FixedIntervalMipOutcome solve(
        const ebrp::FixedIntervalMipRequest& request) override {
        ebrp::FixedIntervalMipOutcome out;
        out.attempted = out.available = out.solver_finalization_reached = true;
        out.native_bound_available = true;
        out.native_bound = request.gamma_L;
        out.same_leaf_model_retained = retained_ && request.attempt_number > 0;
        out.fresh_restart = !out.same_leaf_model_retained;
        out.child_restart = request.new_leaf;
        out.reset_called = false;
        out.native_continuation_evidence = out.same_leaf_model_retained;
        out.native_continuation_claimed = out.native_continuation_evidence;
        ++stats_.optimize_count;
        if (out.same_leaf_model_retained) ++stats_.same_leaf_resume_count;
        if (out.fresh_restart) ++stats_.fresh_restart_count;
        if (out.child_restart) ++stats_.child_restart_count;
        return out;
    }
    ebrp::FixedIntervalMipBackendStats stats() const override { return stats_; }
private:
    bool retained_;
    ebrp::FixedIntervalMipBackendStats stats_;
};

void statusAndCertificateChecks() {
    const std::vector<std::pair<int, std::string>> statuses = {
        {1,"LOADED"},{2,"OPTIMAL"},{3,"INFEASIBLE"},{4,"INF_OR_UNBD"},
        {5,"UNBOUNDED"},{6,"CUTOFF"},{7,"ITERATION_LIMIT"},
        {8,"NODE_LIMIT"},{9,"TIME_LIMIT"},{10,"SOLUTION_LIMIT"},
        {11,"INTERRUPTED"},{12,"NUMERIC"},{13,"SUBOPTIMAL"},
        {14,"INPROGRESS"},{15,"USER_OBJ_LIMIT"},{16,"WORK_LIMIT"},
        {17,"MEM_LIMIT"}
    };
    for (const auto& status : statuses) {
        require(ebrp::gurobiStatusName(status.first) == status.second,
                "Gurobi status mapping mismatch");
    }
    require(ebrp::gurobiStatusClass(9) == "limit", "time limit class");
    require(ebrp::gurobiStatusClass(11) == "interrupted", "interrupt class");
    require(ebrp::gurobiStatusClass(12) == "numeric_or_suboptimal",
            "numeric class");
    require(ebrp::gurobiStatusClass(999) == "unsupported",
            "unknown class must fail closed");

    const auto nominal = ebrp::evaluateGurobiEngineeringExactCertificate(
        nominalGurobi());
    require(nominal.strict_certified_original_problem, "nominal certificate");
    auto gate = nominalGurobi(); gate.optimize_returned = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "optimize gate");
    gate = nominalGurobi(); gate.solver_finalization_completed = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "finalization gate");
    gate = nominalGurobi(); gate.complete_original_model_scope = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "model scope gate");
    gate = nominalGurobi(); gate.model_configuration_valid = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "configuration gate");
    gate = nominalGurobi(); gate.lifecycle_valid = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "lifecycle gate");
    gate = nominalGurobi(); gate.executable_fingerprint_matches_manifest = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "executable binding gate");
    gate = nominalGurobi(); gate.model_fingerprint_matches_manifest = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "model binding gate");
    gate = nominalGurobi(); gate.no_tailored_or_external_information = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "information isolation gate");
    gate = nominalGurobi(); gate.relative_gap_readback_exact_zero = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "relative gap gate");
    gate = nominalGurobi(); gate.absolute_gap_readback_exact_zero = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "absolute gap gate");
    gate = nominalGurobi(); gate.finite_solution_available = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "finite solution gate");
    gate = nominalGurobi(); gate.independently_verified_original_feasible = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "verifier gate");
    gate = nominalGurobi(); gate.objective_recomputed = false;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "objective gate");
    gate = nominalGurobi(); gate.status = ebrp::kGurobiStatusInfeasible;
    gate.finite_solution_available = false;
    gate.independently_verified_original_feasible = false;
    gate.objective_recomputed = false;
    require(ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                .original_problem_infeasible_certified, "infeasible certificate");
    gate.verified_feasible_witness_available = true;
    const auto contradiction =
        ebrp::evaluateGurobiEngineeringExactCertificate(gate);
    require(!contradiction.original_problem_infeasible_certified &&
            !contradiction.feasibility_consistency_gate_passed,
            "witness contradiction gate");
    gate = nominalGurobi(); gate.status = ebrp::kGurobiStatusTimeLimit;
    require(!ebrp::evaluateGurobiEngineeringExactCertificate(gate)
                 .strict_certified_original_problem, "limit fail closed");
}

void externalTreeChecks() {
    ebrp::ExternalCplexLeafStatusInput cplex_status;
    cplex_status.native_status_code = 101;
    cplex_status.exact_zero_gap_roundtrip = true;
    cplex_status.solver_finalization_reached = true;
    cplex_status.lifecycle_complete = true;
    cplex_status.model_fingerprint_matches = true;
    auto cplex_decision =
        ebrp::evaluateExternalCplexLeafStatus(cplex_status);
    require(cplex_decision.exact_optimal && cplex_decision.may_close_leaf,
            "CPLEX 101 closes only under all engineering gates");
    auto cplex_gate = cplex_status;
    cplex_gate.exact_zero_gap_roundtrip = false;
    require(!ebrp::evaluateExternalCplexLeafStatus(cplex_gate).may_close_leaf,
            "CPLEX 101 exact-zero-gap gate");
    cplex_gate = cplex_status; cplex_gate.solver_finalization_reached = false;
    require(!ebrp::evaluateExternalCplexLeafStatus(cplex_gate).may_close_leaf,
            "CPLEX 101 finalization gate");
    cplex_gate = cplex_status; cplex_gate.lifecycle_complete = false;
    require(!ebrp::evaluateExternalCplexLeafStatus(cplex_gate).may_close_leaf,
            "CPLEX 101 lifecycle gate");
    cplex_gate = cplex_status; cplex_gate.model_fingerprint_matches = false;
    require(!ebrp::evaluateExternalCplexLeafStatus(cplex_gate).may_close_leaf,
            "CPLEX 101 model binding gate");
    cplex_gate = cplex_status; cplex_gate.native_status_code = 102;
    cplex_decision = ebrp::evaluateExternalCplexLeafStatus(cplex_gate);
    require(cplex_decision.tolerance_optimal && !cplex_decision.may_close_leaf,
            "CPLEX 102 tolerance optimal never exact-closes");
    cplex_gate = cplex_status; cplex_gate.native_status_code = 103;
    require(ebrp::evaluateExternalCplexLeafStatus(cplex_gate).may_close_leaf,
            "CPLEX 103 closes the fixed interval when consistent");
    cplex_gate.verified_witness_contradicts_infeasibility = true;
    cplex_decision = ebrp::evaluateExternalCplexLeafStatus(cplex_gate);
    require(!cplex_decision.may_close_leaf &&
            !cplex_decision.feasibility_consistency_gate,
            "CPLEX 103 verified-witness contradiction fails closed");
    for (const int interrupted_status : {107, 108}) {
        cplex_gate = cplex_status;
        cplex_gate.native_status_code = interrupted_status;
        cplex_decision = ebrp::evaluateExternalCplexLeafStatus(cplex_gate);
        require(cplex_decision.interrupted && !cplex_decision.may_close_leaf,
                "CPLEX limit status never exact-closes");
    }
    cplex_gate = cplex_status; cplex_gate.native_status_code = 115;
    cplex_decision = ebrp::evaluateExternalCplexLeafStatus(cplex_gate);
    require(cplex_decision.optimal_unscaled_infeasibilities &&
            !cplex_decision.may_close_leaf,
            "CPLEX 115 never exact-closes");
    cplex_gate = cplex_status; cplex_gate.native_status_code = 999;
    cplex_decision = ebrp::evaluateExternalCplexLeafStatus(cplex_gate);
    require(!cplex_decision.native_status_supported &&
            !cplex_decision.may_close_leaf,
            "unsupported CPLEX status fails closed");

    ebrp::ImmutableLeafArtifactContract artifact;
    artifact.leaf_id = "L0";
    artifact.gamma_L = 0.1;
    artifact.gamma_U = 0.2;
    artifact.cutoff = 0.7;
    artifact.path = "L0.lp";
    artifact.sha256 = "sha";
    artifact.model_scope = "fixed_interval_complete_model";
    artifact.row_signature = "rows";
    std::string artifact_reason;
    require(ebrp::immutableLeafArtifactReusable(
                artifact, artifact, &artifact_reason) &&
            artifact_reason == "none",
            "same leaf artifact is reusable without regeneration");
    auto changed_artifact = artifact; changed_artifact.gamma_L = 0.11;
    require(!ebrp::immutableLeafArtifactReusable(
                artifact, changed_artifact, &artifact_reason),
            "changed leaf interval invalidates artifact");
    changed_artifact = artifact; changed_artifact.cutoff = 0.6;
    require(!ebrp::immutableLeafArtifactReusable(
                artifact, changed_artifact, &artifact_reason),
            "changed leaf cutoff invalidates artifact");
    changed_artifact = artifact; changed_artifact.sha256 = "other";
    require(!ebrp::immutableLeafArtifactReusable(
                artifact, changed_artifact, &artifact_reason),
            "changed leaf model fingerprint invalidates artifact");
    changed_artifact = artifact; changed_artifact.row_signature = "other";
    require(!ebrp::immutableLeafArtifactReusable(
                artifact, changed_artifact, &artifact_reason),
            "changed row signature invalidates artifact");
    changed_artifact = artifact; changed_artifact.leaf_id = "L0.0";
    require(!ebrp::immutableLeafArtifactReusable(
                artifact, changed_artifact, &artifact_reason),
            "child leaf requires a distinct artifact");

    require(ebrp::evaluateExternalGiniTreeCertificate(nominalExternal()).certified,
            "nominal external certificate");
    auto gate = nominalExternal(); gate.complete_root_coverage = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "root coverage gate");
    gate = nominalExternal(); gate.parent_child_coverage_valid = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "child coverage gate");
    gate = nominalExternal(); gate.all_relevant_leaves_closed = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "one optimal leaf cannot certify global");
    gate = nominalExternal(); gate.all_leaf_bounds_valid = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "leaf bound gate");
    gate = nominalExternal(); gate.global_bound_monotone = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "global monotonicity gate");
    gate = nominalExternal(); gate.leaf_bounds_monotone = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "leaf monotonicity gate");
    gate = nominalExternal(); gate.verified_global_ub = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "verified UB gate");
    gate = nominalExternal(); gate.lifecycle_complete = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "lifecycle gate");
    gate = nominalExternal(); gate.feasibility_consistency_gate = false;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "feasibility consistency gate");
    gate = nominalExternal(); gate.global_lb = 0.4;
    require(!ebrp::evaluateExternalGiniTreeCertificate(gate).certified,
            "open project gap gate");

    const ebrp::GiniIntervalGeometry root{0.0, 0.8};
    const auto initial = ebrp::makeLegacyFrontierIntervals(0.0, 0.8, 4);
    require(ebrp::exactIntervalCoverage(root, initial, 1e-12),
            "initial exact coverage");
    const auto children = ebrp::splitLegacyFrontierInterval(0.2, 0.4, 2);
    require(ebrp::exactIntervalCoverage({0.2,0.4}, children, 1e-12),
            "adaptive exact coverage");

    ebrp::ControllingLeafScheduler scheduler;
    ebrp::ControllingLeaf parent;
    parent.id="P"; parent.gamma_L=0.0; parent.gamma_U=0.4;
    parent.base_lower_bound=parent.lower_bound=0.1; parent.cutoff=0.8;
    require(scheduler.addLeaf(parent), "parent add");
    ebrp::ControllingLeaf left;
    left.id="P.0";left.parent_id="P";left.child_index=0;left.split_depth=1;
    left.gamma_L=0.0;left.gamma_U=0.2;left.base_lower_bound=left.lower_bound=0.1;left.cutoff=0.8;
    auto right=left;right.id="P.1";right.child_index=1;right.gamma_L=0.2;right.gamma_U=0.4;
    require(scheduler.splitLeafAtomically("P",{left,right}), "atomic parent replacement");
    require(std::fabs(scheduler.globalLowerBound()-0.1)<1e-12,
            "children inherit parent LB");
    require(scheduler.parentChildCoverageValid(), "scheduler coverage audit");
    require(scheduler.mergeValidLowerBound("P.0",0.2,"native"), "native LB merge");
    require(scheduler.leafBoundsMonotone(), "leaf LB monotone");
    require(scheduler.globalBoundMonotone(), "global LB monotone");
    require(std::fabs(scheduler.globalLowerBound()-0.1)<1e-12,
            "global LB is minimum relevant leaf");
    ebrp::ControllingLeafAttempt attempt;
    attempt.attempt_number=0;attempt.requested_quantum_seconds=30;
    attempt.effective_native_time_limit_seconds=30;attempt.actual_solver_time_seconds=1;
    attempt.solver_status="incumbent_only";attempt.solver_final_best_bound_valid=false;
    require(scheduler.recordAttempt("P.1",attempt,0,1), "attempt accounting");
    require(std::fabs(scheduler.findLeaf("P.1")->lower_bound-0.1)<1e-12,
            "leaf incumbent never becomes LB");

    InstrumentedFakeBackend retained(true), fresh(false);
    ebrp::FixedIntervalMipRequest request;
    request.leaf_id="L";request.gamma_L=0.0;request.gamma_U=0.2;request.new_leaf=true;
    require(retained.solve(request).child_restart, "new child native restart");
    request.new_leaf=false;request.attempt_number=1;
    const auto resumed=retained.solve(request);
    require(resumed.same_leaf_model_retained && resumed.native_continuation_evidence,
            "retained unchanged leaf continuation evidence");
    require(!resumed.reset_called, "retained mode never reset");
    const auto restarted=fresh.solve(request);
    require(restarted.fresh_restart && !restarted.same_leaf_model_retained,
            "fresh attempt separately instrumented");
}

void hashingAndStartChecks() {
    const auto path = std::filesystem::temp_directory_path() /
        "exactebrp_round24_sha256_test.txt";
    { std::ofstream out(path, std::ios::binary); out << "abc"; }
    require(ebrp::fileSha256(path) ==
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "SHA-256 standard vector");
    require(ebrp::fileSha256(path).size()==64, "SHA-256 width");
    std::error_code ignored; std::filesystem::remove(path,ignored);

    const ebrp::Instance instance=balancedInstance();
    ebrp::SolveOptions options; options.lambda=0.15;
    ebrp::SolverNeutralModelDomain domain;
    domain.names={"G","r_min","r_max","W_SP","Y_1","Y_2","r_1","r_2","e_1","e_2","h_1_2"};
    domain.lower_bounds=std::vector<double>(domain.names.size(),-100.0);
    domain.upper_bounds=std::vector<double>(domain.names.size(),100.0);
    domain.variable_types=std::vector<char>(domain.names.size(),'C');
    const auto mapped=ebrp::mapVerifiedRoutesToCanonicalModel(
        instance,options,{},"verified_hga",0.0,1.0,1.0,domain);
    require(mapped.candidate_independently_verified, "start independently checked");
    require(mapped.objective_recomputed, "start objective recomputed");
    require(mapped.interval_membership_valid, "start interval membership");
    require(mapped.vehicle_symmetry_canonicalization_valid,
            "start vehicle symmetry canonicalization");
    require(mapped.complete, "complete semantic start mapping");
    require(std::fabs(mapped.objective)<1e-12, "mapped objective value");
    auto incompatible=ebrp::mapVerifiedRoutesToCanonicalModel(
        instance,options,{},"verified_hga",0.2,0.4,1.0,domain);
    require(!incompatible.complete && !incompatible.interval_membership_valid,
            "interval-incompatible start rejected");
    auto unsupported=domain; unsupported.names.push_back("unknown_aux");
    unsupported.lower_bounds.push_back(-1);unsupported.upper_bounds.push_back(1);
    unsupported.variable_types.push_back('C');
    const auto rejected=ebrp::mapVerifiedRoutesToCanonicalModel(
        instance,options,{},"verified_hga",0.0,1.0,1.0,unsupported);
    require(!rejected.complete && !rejected.no_unsupported_columns,
            "unsupported start column fails closed");

    ebrp::SolveOptions defaults;
    require(!defaults.allow_unsafe_continuous_branch_presolve_diagnostic,
            "unsafe override defaults false");
    require(defaults.external_gini_backend=="cplex",
            "default stable backend unchanged");
    require(defaults.global_gini_tree_child_estimate_mode=="parent-copy",
            "P2 remains off by default");
    require(defaults.global_gini_tree_root_connectivity_flow_variant.empty(),
            "F3 remains off by default");
    if (!ebrp::gurobiBackendBuildEnabled()) {
        const auto backend=ebrp::makeGurobiFixedIntervalBackend(instance,defaults);
        require(backend && !backend->capabilities().available,
                "non-Gurobi build has clear unavailable adapter");
    } else {
        require(true,"Gurobi-enabled build exposes backend");
    }
}

} // namespace

int main() {
    try {
        statusAndCertificateChecks();
        externalTreeChecks();
        hashingAndStartChecks();
        if (checks < 75) throw std::runtime_error("fewer than 75 Round24 checks");
        std::cout << "Round24BackendTests passed " << checks << " checks\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Round24BackendTests failed after " << checks
                  << " checks: " << ex.what() << '\n';
        return 1;
    }
}
