#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "Parser.hpp"

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace {

std::string csv(const std::string& value) {
    std::string out = "\"";
    for (char ch : value) {
        if (ch == '"') out.push_back('"');
        out.push_back(ch);
    }
    out.push_back('"');
    return out;
}

struct StateSpec {
    std::string label;
    std::filesystem::path model;
};

} // namespace

int main(int argc, char** argv) {
    if (argc != 9) {
        std::cerr << "usage: Round49RCOfflineExtract INSTANCE INCUMBENT "
                     "PARENT.lp LEFT.lp RIGHT.lp OUTPUT.csv GUROBI_HOME "
                     "PROCESS_CAP_SECONDS\n";
        return 2;
    }
    const std::filesystem::path instance_path = argv[1];
    const double incumbent = std::stod(argv[2]);
    const std::vector<StateSpec> states = {
        {"P", argv[3]}, {"L", argv[4]}, {"R", argv[5]}};
    const std::filesystem::path output_path = argv[6];
    const std::string gurobi_home = argv[7];
    const double process_cap = std::min(1800.0, std::stod(argv[8]));
    if (!(process_cap > 0.0)) return 2;

    const ebrp::Instance instance = ebrp::parseInstanceFile(
        instance_path, 3600.0, 60.0, 60.0);
    ebrp::SolveOptions options;
    options.gurobi_home = gurobi_home;
    options.gurobi_threads = 1;
    options.gurobi_seed = 0;
    options.gurobi_presolve = -1;
    options.log_path = (output_path.parent_path() /
        (output_path.stem().string() + ".backend.log")).string();
    std::unique_ptr<ebrp::FixedIntervalMipBackend> backend =
        ebrp::makeGurobiFixedIntervalBackend(instance, options);
    if (!backend || !backend->capabilities().available) {
        std::cerr << "Gurobi backend unavailable: "
                  << (backend ? backend->capabilities().failure_reason
                              : "null backend") << '\n';
        return 3;
    }

    std::filesystem::create_directories(output_path.parent_path());
    std::ofstream output(output_path);
    if (!output) return 4;
    output << "state,model_path,model_sha256,verified_cutoff,lp_objective,"
              "optimal,terminal_valid,primal_values_available,"
              "reduced_costs_available,basis_status_available,"
              "primal_dual_evidence_available,objective_sense,native_status,"
              "variable,original_type,lower_bound,upper_bound,primal_value,"
              "reduced_cost,variable_basis_status\n";
    output << std::setprecision(17);

    const auto started = std::chrono::steady_clock::now();
    bool all_valid = true;
    for (const StateSpec& state : states) {
        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        const double remaining = process_cap - elapsed;
        if (!(remaining > 0.0)) return 5;
        ebrp::FixedIntervalMipRequest request;
        request.solve_kind = ebrp::FixedIntervalSolveKind::PaperLpRelaxation;
        request.leaf_id = "round49_offline_" + state.label;
        request.verified_cutoff = incumbent;
        request.global_deadline_remaining_seconds = remaining;
        request.new_leaf = true;
        request.canonical_model_path = state.model;
        request.canonical_model_fingerprint = ebrp::fileSha256(state.model);
        request.native_log_path = output_path.parent_path() /
            (output_path.stem().string() + "_" + state.label +
             ".gurobi.log");
        request.capture_lp_primal_dual_evidence = true;
        const ebrp::FixedIntervalMipOutcome outcome = backend->solve(request);
        all_valid = all_valid && outcome.lp_terminal_valid && outcome.optimal &&
            outcome.lp_primal_dual_evidence_available;
        for (const auto& variable :
             outcome.lp_primal_dual_variable_evidence) {
            output << csv(state.label) << ',' << csv(state.model.string())
                   << ',' << csv(request.canonical_model_fingerprint) << ','
                   << incumbent << ',' << outcome.lp_objective_value << ','
                   << outcome.optimal << ',' << outcome.lp_terminal_valid << ','
                   << outcome.lp_primal_values_available << ','
                   << outcome.lp_reduced_costs_available << ','
                   << outcome.lp_basis_status_available << ','
                   << outcome.lp_primal_dual_evidence_available << ','
                   << outcome.lp_objective_sense << ','
                   << csv(outcome.native_status) << ','
                   << csv(variable.name) << ',' << variable.original_type << ','
                   << variable.lower_bound << ',' << variable.upper_bound << ','
                   << variable.primal_value << ',' << variable.reduced_cost
                   << ',' << variable.variable_basis_status << '\n';
        }
        if (outcome.lp_primal_dual_variable_evidence.empty()) {
            std::cerr << state.label << ": " << outcome.failure_reason << '\n';
        }
    }
    backend->release();
    const auto stats = backend->stats();
    std::cout << "offline_lp_solves=" << stats.lp_relaxation_optimize_count
              << ";all_valid=" << all_valid
              << ";output=" << output_path.string() << '\n';
    return all_valid ? 0 : 6;
}
