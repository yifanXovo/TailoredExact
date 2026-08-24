#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "HgaTgbcRunner.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;
constexpr double kEvidenceFinalizationReserveSeconds = 2.0;

struct Arguments {
    std::filesystem::path executable;
    std::string mode = "solve";
    std::string state_id;
    std::filesystem::path input;
    std::filesystem::path artifact_dir;
    std::string policy = "interval-mip-v0";
    std::string gurobi_home;
    double gamma_lower = 0.0;
    double gamma_upper = 0.0;
    double cutoff = 0.0;
    double expected_cutoff = -1.0;
    double process_cap_seconds = 300.0;
    double route_time_limit = 2850.0;
    double pickup_time = 60.0;
    double drop_time = 60.0;
};

std::string jsonEscape(const std::string& value) {
    std::ostringstream out;
    for (unsigned char ch : value) {
        switch (ch) {
        case '\\': out << "\\\\"; break;
        case '"': out << "\\\""; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (ch < 0x20) {
                out << "\\u" << std::hex << std::setw(4)
                    << std::setfill('0') << static_cast<int>(ch)
                    << std::dec << std::setfill(' ');
            } else {
                out << static_cast<char>(ch);
            }
        }
    }
    return out.str();
}

std::string csvField(const std::string& value) {
    std::string out = "\"";
    for (char ch : value) {
        if (ch == '"') out.push_back('"');
        out.push_back(ch);
    }
    out.push_back('"');
    return out;
}

std::string boolJson(bool value) { return value ? "true" : "false"; }

double elapsed(const Clock::time_point& started) {
    return std::chrono::duration<double>(Clock::now() - started).count();
}

Arguments parseArguments(int argc, char** argv) {
    Arguments out;
    out.executable = std::filesystem::absolute(argv[0]);
    auto value = [&](int& index) -> std::string {
        if (++index >= argc) throw std::runtime_error("missing option value");
        return argv[index];
    };
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--mode") out.mode = value(i);
        else if (arg == "--state-id") out.state_id = value(i);
        else if (arg == "--input") out.input = value(i);
        else if (arg == "--artifact-dir") out.artifact_dir = value(i);
        else if (arg == "--policy") out.policy = value(i);
        else if (arg == "--gurobi-home") out.gurobi_home = value(i);
        else if (arg == "--gamma-lower") out.gamma_lower = std::stod(value(i));
        else if (arg == "--gamma-upper") out.gamma_upper = std::stod(value(i));
        else if (arg == "--cutoff") out.cutoff = std::stod(value(i));
        else if (arg == "--expected-cutoff") out.expected_cutoff = std::stod(value(i));
        else if (arg == "--process-cap") out.process_cap_seconds = std::stod(value(i));
        else if (arg == "--T") out.route_time_limit = std::stod(value(i));
        else if (arg == "--pickup-time") out.pickup_time = std::stod(value(i));
        else if (arg == "--drop-time") out.drop_time = std::stod(value(i));
        else throw std::runtime_error("unsupported option: " + arg);
    }
    if (out.mode != "solve" && out.mode != "build" &&
        out.mode != "resolve-cutoff") {
        throw std::runtime_error("unsupported mode");
    }
    if (out.state_id.empty() || out.input.empty() || out.artifact_dir.empty()) {
        throw std::runtime_error("state-id, input, and artifact-dir are required");
    }
    if (!(out.process_cap_seconds > 0.0) || out.process_cap_seconds > 1800.0) {
        throw std::runtime_error("process cap must be in (0,1800]");
    }
    if (out.mode != "resolve-cutoff" &&
        (!(out.gamma_lower >= 0.0) ||
         !(out.gamma_upper >= out.gamma_lower) || !std::isfinite(out.cutoff))) {
        throw std::runtime_error("invalid interval or cutoff");
    }
    return out;
}

void writeCommand(const Arguments& args, const std::filesystem::path& path) {
    std::ofstream out(path);
    out << std::setprecision(17)
        << "{\n  \"schema\": \"round50-fixed-interval-command-v1\",\n"
        << "  \"executable_path\": \"" << jsonEscape(args.executable.generic_string()) << "\",\n"
        << "  \"executable_sha256\": \"" << ebrp::fileSha256(args.executable) << "\",\n"
        << "  \"mode\": \"" << jsonEscape(args.mode) << "\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"input\": \"" << jsonEscape(args.input.generic_string()) << "\",\n"
        << "  \"artifact_dir\": \"" << jsonEscape(args.artifact_dir.generic_string()) << "\",\n"
        << "  \"policy\": \"" << jsonEscape(args.policy) << "\",\n"
        << "  \"gamma_lower\": " << args.gamma_lower << ",\n"
        << "  \"gamma_upper\": " << args.gamma_upper << ",\n"
        << "  \"verified_cutoff\": " << args.cutoff << ",\n"
        << "  \"route_time_limit\": " << args.route_time_limit << ",\n"
        << "  \"pickup_time\": " << args.pickup_time << ",\n"
        << "  \"drop_time\": " << args.drop_time << ",\n"
        << "  \"process_cap_seconds\": " << args.process_cap_seconds << ",\n"
        << "  \"evidence_finalization_reserve_seconds\": "
        << kEvidenceFinalizationReserveSeconds << ",\n"
        << "  \"solver\": {\"Presolve\": \"Auto\", \"Seed\": 0, \"Threads\": 1, \"MIPGap\": 0, \"MIPGapAbs\": 0},\n"
        << "  \"known_optimum_injection\": false,\n"
        << "  \"archive_winner_injection\": false\n}\n";
}

void writeArtifactManifest(const std::filesystem::path& dir) {
    const auto output = dir / "artifact_manifest.csv";
    std::vector<std::filesystem::path> files;
    for (const auto& item : std::filesystem::recursive_directory_iterator(dir)) {
        if (!item.is_regular_file() || item.path() == output) continue;
        files.push_back(item.path());
    }
    std::sort(files.begin(), files.end());
    std::ofstream out(output);
    out << "path,sha256,size_bytes,storage_class\n";
    for (const auto& file : files) {
        const std::string relative =
            std::filesystem::relative(file, dir).generic_string();
        const bool raw = file.extension() == ".lp" ||
            file.extension() == ".log";
        out << csvField(relative) << ',' << ebrp::fileSha256(file) << ','
            << std::filesystem::file_size(file) << ','
            << (raw ? "local_raw" : "compact") << '\n';
    }
}

void writeCompletion(const std::filesystem::path& dir,
                     const Arguments& args,
                     const std::string& status,
                     bool exact,
                     bool evidence_complete,
                     double process_seconds) {
    std::ofstream out(dir / "completion_marker.json");
    out << std::setprecision(17)
        << "{\n  \"schema\": \"round50-fixed-interval-completion-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"policy\": \"" << jsonEscape(args.policy) << "\",\n"
        << "  \"status\": \"" << jsonEscape(status) << "\",\n"
        << "  \"exact\": " << boolJson(exact) << ",\n"
        << "  \"evidence_complete\": " << boolJson(evidence_complete) << ",\n"
        << "  \"process_seconds\": " << process_seconds << ",\n"
        << "  \"process_cap_seconds\": " << args.process_cap_seconds << ",\n"
        << "  \"cap_respected\": "
        << boolJson(process_seconds <= args.process_cap_seconds + 0.05) << "\n}\n";
}

int resolveCutoff(const ebrp::Instance& instance,
                  const Arguments& args,
                  const Clock::time_point& started) {
    ebrp::SolveOptions process_options;
    ebrp::configureRound50IntervalMipV0(process_options);
    process_options.process_wall_time_limit = args.process_cap_seconds;
    process_options.primal_heuristic_seed = 20260626u;
    process_options.primal_heuristic_stop = "generation-stagnation";
    process_options.primal_heuristic_no_improve_generations = 2000;
    ebrp::HgaTgbcOptions hga;
    hga.lambda = 0.15;
    hga.seed = 20260626u;
    hga.pop_size = 24;
    hga.iterations = 10;
    hga.stop_mode = "generation-stagnation";
    hga.no_improve_generation_limit = 2000;
    hga.generation_log_path = args.artifact_dir / "hga_generations.csv";
    hga.phase_label = "round50_fixed_state_cutoff_reconstruction";
    hga.process_options = &process_options;
    const ebrp::HgaTgbcResult result = ebrp::runHgaTgbcNative(instance, hga);
    const ebrp::Verification verification =
        ebrp::verifySolution(instance, result.routes, 0.15);
    const bool verified = result.found &&
        verification.original_solution_feasible &&
        verification.original_objective_recomputed &&
        verification.errors.empty() &&
        std::fabs(verification.objective - result.verified_objective) <=
            1e-7 * std::max(1.0, std::fabs(verification.objective));
    const bool expected_matches = args.expected_cutoff < 0.0 ||
        std::fabs(verification.objective - args.expected_cutoff) <=
            1e-7 * std::max(1.0, std::fabs(args.expected_cutoff));
    std::ofstream out(args.artifact_dir / "cutoff_resolution.json");
    out << std::setprecision(17)
        << "{\n  \"schema\": \"round50-cutoff-resolution-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"input_sha256\": \"" << ebrp::fileSha256(args.input) << "\",\n"
        << "  \"route_time_limit\": " << args.route_time_limit << ",\n"
        << "  \"pickup_time\": " << args.pickup_time << ",\n"
        << "  \"drop_time\": " << args.drop_time << ",\n"
        << "  \"seed\": 20260626,\n"
        << "  \"stop_mode\": \"generation-stagnation\",\n"
        << "  \"no_improve_generations\": 2000,\n"
        << "  \"found\": " << boolJson(result.found) << ",\n"
        << "  \"verified\": " << boolJson(verified) << ",\n"
        << "  \"verified_objective\": " << verification.objective << ",\n"
        << "  \"verified_G\": " << verification.G << ",\n"
        << "  \"verified_P\": " << verification.P << ",\n"
        << "  \"expected_cutoff_supplied\": " << boolJson(args.expected_cutoff >= 0.0) << ",\n"
        << "  \"expected_cutoff\": " << args.expected_cutoff << ",\n"
        << "  \"expected_cutoff_matches\": " << boolJson(expected_matches) << ",\n"
        << "  \"route_count\": " << result.routes.size() << ",\n"
        << "  \"wall_time_seconds\": " << result.wall_time_seconds << ",\n"
        << "  \"known_optimum_used\": false,\n"
        << "  \"archive_winner_used\": false\n}\n";
    out.close();
    writeArtifactManifest(args.artifact_dir);
    const bool complete = verified && expected_matches;
    writeCompletion(args.artifact_dir, args,
                    complete ? "cutoff_resolved" : "cutoff_resolution_failed",
                    false, complete, elapsed(started));
    return complete ? 0 : 4;
}

void writeStateIdentity(const ebrp::Instance& instance,
                        const Arguments& args,
                        const ebrp::CanonicalCompactModelArtifact& artifact) {
    std::ofstream out(args.artifact_dir / "state_identity.json");
    out << std::setprecision(17)
        << "{\n  \"schema\": \"round50-fixed-state-identity-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"instance\": \"" << jsonEscape(instance.name) << "\",\n"
        << "  \"input_sha256\": \"" << ebrp::fileSha256(args.input) << "\",\n"
        << "  \"route_time_limit\": " << args.route_time_limit << ",\n"
        << "  \"pickup_time\": " << args.pickup_time << ",\n"
        << "  \"drop_time\": " << args.drop_time << ",\n"
        << "  \"gamma_lower\": " << args.gamma_lower << ",\n"
        << "  \"gamma_upper\": " << args.gamma_upper << ",\n"
        << "  \"verified_cutoff\": " << args.cutoff << ",\n"
        << "  \"objective_sense\": \"minimize\",\n"
        << "  \"complete_objective\": \"G+0.15*weighted_absolute_satisfaction_deviation\",\n"
        << "  \"model_fingerprint\": \"" << artifact.sha256 << "\",\n"
        << "  \"row_bound_signature\": \"" << artifact.row_signature << "\",\n"
        << "  \"formulation_profile\": \""
        << (artifact.exact_duplicate_row_elimination
                ? "Interval-MIP-v0-paper-safe+C1-exact-duplicate-elimination"
                : "Interval-MIP-v0-paper-safe") << "\",\n"
        << "  \"exact_duplicate_row_elimination\": "
        << boolJson(artifact.exact_duplicate_row_elimination) << ",\n"
        << "  \"exact_duplicate_rows_omitted\": "
        << artifact.exact_duplicate_rows_omitted << ",\n"
        << "  \"round50_symmetry_policy\": \""
        << jsonEscape(artifact.round50_symmetry_policy) << "\",\n"
        << "  \"round50_symmetry_rows\": "
        << artifact.round50_symmetry_rows << "\n}\n";
    std::ofstream model(args.artifact_dir / "model_fingerprint.json");
    model << "{\n  \"schema\": \"round50-model-fingerprint-v1\",\n"
          << "  \"sha256\": \"" << artifact.sha256 << "\",\n"
          << "  \"row_signature\": \"" << artifact.row_signature << "\",\n"
          << "  \"scope\": \"" << jsonEscape(artifact.model_scope) << "\",\n"
          << "  \"rows\": " << artifact.rows << ",\n"
          << "  \"columns\": " << artifact.columns << ",\n"
          << "  \"nonzeros\": " << artifact.nonzeros << ",\n"
          << "  \"exact_duplicate_row_elimination\": "
          << boolJson(artifact.exact_duplicate_row_elimination) << ",\n"
          << "  \"exact_duplicate_rows_omitted\": "
          << artifact.exact_duplicate_rows_omitted << ",\n"
          << "  \"round50_symmetry_policy\": \""
          << jsonEscape(artifact.round50_symmetry_policy) << "\",\n"
          << "  \"round50_symmetry_rows\": "
          << artifact.round50_symmetry_rows << "\n}\n";
}

void writeStaticLedgers(const Arguments& args,
                        const ebrp::CanonicalCompactModelArtifact& artifact) {
    std::ofstream size(args.artifact_dir / "formulation_size_ledger.csv");
    size << "state_id,policy,original_rows,original_columns,original_nonzeros,model_scope,exact_duplicate_row_elimination,exact_duplicate_rows_omitted,round50_symmetry_policy,round50_symmetry_rows\n"
         << csvField(args.state_id) << ',' << csvField(args.policy) << ','
         << artifact.rows << ',' << artifact.columns << ','
         << artifact.nonzeros << ',' << csvField(artifact.model_scope) << ','
         << artifact.exact_duplicate_row_elimination << ','
         << artifact.exact_duplicate_rows_omitted << ','
         << csvField(artifact.round50_symmetry_policy) << ','
         << artifact.round50_symmetry_rows << '\n';
}

void writeSolveEvidence(const Arguments& args,
                        const ebrp::CanonicalCompactModelArtifact& artifact,
                        const ebrp::FixedIntervalMipOutcome& outcome,
                        const ebrp::FixedIntervalMipBackendStats& stats,
                        double process_seconds) {
    const bool engineering = outcome.attempted && outcome.available &&
        outcome.solver_finalization_reached &&
        outcome.model_fingerprint_matches_request &&
        outcome.exact_zero_gap_roundtrip &&
        outcome.feasibility_consistency_gate &&
        outcome.branch_priority_assignment_valid;
    const bool exact_infeasible = engineering && outcome.infeasible;
    const bool exact_feasible = engineering && outcome.native_exact_optimal &&
        outcome.native_bound_available && outcome.incumbent_available &&
        outcome.incumbent_independently_verified &&
        std::fabs(outcome.native_bound - outcome.incumbent_objective) <=
            1e-7 * std::max(1.0, std::fabs(outcome.incumbent_objective));
    const bool exact = exact_infeasible || exact_feasible;
    const std::string status = exact ? "exact" :
        (outcome.interrupted ? "capped" : "failed");
    const double lower = outcome.native_bound_available
        ? outcome.native_bound : 0.0;
    const bool verified_native_incumbent = outcome.incumbent_available &&
        outcome.incumbent_independently_verified &&
        std::isfinite(outcome.incumbent_objective);
    const double upper = verified_native_incumbent
        ? std::min(args.cutoff, outcome.incumbent_objective)
        : args.cutoff;
    const double gap = std::max(0.0, (upper - lower) /
        std::max(1e-12, std::fabs(upper)));

    std::ofstream result(args.artifact_dir / "result.json");
    result << std::setprecision(17)
        << "{\n  \"schema\": \"round50-fixed-interval-result-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"policy\": \"" << jsonEscape(args.policy) << "\",\n"
        << "  \"status\": \"" << status << "\",\n"
        << "  \"certificate\": " << boolJson(exact) << ",\n"
        << "  \"certificate_class\": \""
        << (exact_infeasible ? "strict_fixed_interval_cutoff_infeasible"
            : (exact_feasible ? "strict_fixed_interval_optimal"
               : "certificate_rejected")) << "\",\n"
        << "  \"false_certificate\": false,\n"
        << "  \"native_status\": \"" << jsonEscape(outcome.native_status) << "\",\n"
        << "  \"lower_bound\": " << lower << ",\n"
        << "  \"frozen_cutoff\": " << args.cutoff << ",\n"
        << "  \"final_incumbent_available\": "
        << boolJson(verified_native_incumbent) << ",\n"
        << "  \"final_incumbent\": "
        << (verified_native_incumbent ? outcome.incumbent_objective : args.cutoff)
        << ",\n"
        << "  \"verified_upper_bound\": " << upper << ",\n"
        << "  \"gap\": " << gap << ",\n"
        << "  \"work\": " << outcome.work << ",\n"
        << "  \"solver_time_seconds\": " << outcome.solver_runtime_seconds << ",\n"
        << "  \"process_time_seconds\": " << process_seconds << ",\n"
        << "  \"nodes\": " << outcome.nodes << ",\n"
        << "  \"simplex_iterations\": " << outcome.simplex_iterations << ",\n"
        << "  \"average_iterations_per_node\": "
        << (outcome.nodes > 0.0 ? outcome.simplex_iterations / outcome.nodes : 0.0) << ",\n"
        << "  \"peak_memory_gb\": " << outcome.memory_gb << ",\n"
        << "  \"root_relaxation_bound_available\": " << boolJson(outcome.root_relaxation_bound_available) << ",\n"
        << "  \"root_relaxation_bound\": " << outcome.root_relaxation_bound << ",\n"
        << "  \"final_root_cut_bound_available\": " << boolJson(outcome.final_root_cut_bound_available) << ",\n"
        << "  \"final_root_cut_bound\": " << outcome.final_root_cut_bound << ",\n"
        << "  \"root_work\": " << outcome.root_work << ",\n"
        << "  \"root_time_seconds\": " << outcome.root_runtime_seconds << ",\n"
        << "  \"root_simplex_iterations\": " << outcome.root_simplex_iterations << ",\n"
        << "  \"first_incumbent_work\": " << outcome.first_incumbent_work << ",\n"
        << "  \"first_incumbent_time_seconds\": " << outcome.first_incumbent_runtime_seconds << ",\n"
        << "  \"model_build_seconds\": " << outcome.model_build_seconds << ",\n"
        << "  \"model_read_seconds\": " << outcome.model_read_seconds << ",\n"
        << "  \"model_sha256\": \"" << artifact.sha256 << "\",\n"
        << "  \"engineering_gate\": " << boolJson(engineering) << ",\n"
        << "  \"failure_reason\": \"" << jsonEscape(outcome.failure_reason) << "\"\n}\n";

    std::ofstream progress(args.artifact_dir / "mip_progress.csv");
    progress << "event_index,time_seconds,work,best_bound,bound_available,incumbent,incumbent_available,processed_nodes,open_nodes,phase,bound_improved\n";
    progress << std::setprecision(17);
    for (std::size_t i = 0; i < outcome.native_bound_events.size(); ++i) {
        const auto& event = outcome.native_bound_events[i];
        progress << i << ',' << event.solver_runtime_seconds << ','
                 << event.work << ',' << event.native_bound << ','
                 << event.native_bound_available << ','
                 << event.native_incumbent << ','
                 << event.native_incumbent_available << ','
                 << event.processed_nodes << ',' << event.open_nodes << ','
                 << event.native_phase << ',' << event.bound_improved << '\n';
    }

    std::ofstream root(args.artifact_dir / "root_processing_ledger.csv");
    root << "state_id,policy,root_relaxation_bound_available,root_relaxation_bound,final_root_cut_bound_available,final_root_cut_bound,root_work,root_time_seconds,root_simplex_iterations,root_cut_count\n"
         << csvField(args.state_id) << ',' << csvField(args.policy) << ','
         << outcome.root_relaxation_bound_available << ','
         << outcome.root_relaxation_bound << ','
         << outcome.final_root_cut_bound_available << ','
         << outcome.final_root_cut_bound << ',' << outcome.root_work << ','
         << outcome.root_runtime_seconds << ','
         << outcome.root_simplex_iterations << ','
         << outcome.native_cut_count << '\n';

    std::ofstream presolve(args.artifact_dir / "presolve_ledger.csv");
    presolve << "state_id,policy,available,rows,columns,nonzeros,presolve_observed\n"
             << csvField(args.state_id) << ',' << csvField(args.policy) << ','
             << outcome.presolved_model_size_available << ','
             << outcome.presolved_row_count << ','
             << outcome.presolved_column_count << ','
             << outcome.presolved_nonzero_count << ','
             << outcome.presolve_rerun_observed << '\n';

    using BranchKey = std::tuple<std::string, int, char>;
    std::map<BranchKey, long long> branch_counts;
    for (const auto& item : outcome.branch_priority_evidence) {
        ++branch_counts[{item.semantic_family, item.assigned_priority,
                         item.variable_type}];
    }
    std::ofstream branching(args.artifact_dir / "branching_policy_ledger.csv");
    branching << "state_id,policy,semantic_family,priority,variable_type,variable_count,assignment_status\n";
    if (branch_counts.empty()) {
        branching << csvField(args.state_id) << ',' << csvField(args.policy)
                  << ",all,0,all,0,"
                  << csvField(outcome.branch_priority_assignment_status) << '\n';
    }
    for (const auto& item : branch_counts) {
        branching << csvField(args.state_id) << ',' << csvField(args.policy)
                  << ',' << csvField(std::get<0>(item.first)) << ','
                  << std::get<1>(item.first) << ','
                  << std::get<2>(item.first) << ',' << item.second << ','
                  << csvField(outcome.branch_priority_assignment_status) << '\n';
    }

    std::ofstream cuts(args.artifact_dir / "cut_family_ledger.csv");
    cuts << "state_id,policy,family,count,source\n";
    if (outcome.root_cut_family_evidence.empty()) {
        cuts << csvField(args.state_id) << ',' << csvField(args.policy)
             << ",none,0,native_log\n";
    }
    for (const auto& cut : outcome.root_cut_family_evidence) {
        cuts << csvField(args.state_id) << ',' << csvField(args.policy)
             << ',' << csvField(cut.family) << ',' << cut.count
             << ",native_log\n";
    }

    std::ofstream numerical(args.artifact_dir / "numerical_quality_ledger.csv");
    numerical << "state_id,policy,available,min_matrix,max_matrix,min_objective,max_objective,min_bound,max_bound,min_rhs,max_rhs\n"
              << csvField(args.state_id) << ',' << csvField(args.policy) << ','
              << outcome.numerical_ranges_available << ','
              << outcome.minimum_matrix_coefficient << ','
              << outcome.maximum_matrix_coefficient << ','
              << outcome.minimum_objective_coefficient << ','
              << outcome.maximum_objective_coefficient << ','
              << outcome.minimum_variable_bound << ','
              << outcome.maximum_variable_bound << ','
              << outcome.minimum_rhs << ',' << outcome.maximum_rhs << '\n';

    std::ofstream reuse(args.artifact_dir / "model_reuse_ledger.csv");
    reuse << "state_id,policy,model_count,model_read_count,optimize_count,in_memory_model_reused,integer_domain_restored,basis_reuse_status,mathematical_model_changed\n"
          << csvField(args.state_id) << ',' << csvField(args.policy) << ','
          << stats.model_count << ',' << stats.model_read_count << ','
          << stats.optimize_count << ',' << outcome.in_memory_model_reused
          << ',' << outcome.integer_domain_restored << ','
          << csvField(outcome.basis_reuse_status) << ",0\n";

    std::ofstream certificate(args.artifact_dir / "certificate_ledger.csv");
    certificate << "state_id,policy,status,strict_certificate,false_certificate,engineering_gate,model_fingerprint_match,zero_gap_roundtrip,feasibility_consistency,lower_bound,verified_upper_bound,gap\n"
                << csvField(args.state_id) << ',' << csvField(args.policy)
                << ',' << status << ',' << exact << ",0," << engineering
                << ',' << outcome.model_fingerprint_matches_request << ','
                << outcome.exact_zero_gap_roundtrip << ','
                << outcome.feasibility_consistency_gate << ',' << lower
                << ',' << upper << ',' << gap << '\n';
}

} // namespace

int main(int argc, char** argv) {
    const auto started = Clock::now();
    try {
        const Arguments args = parseArguments(argc, argv);
        const ebrp::Round50IntervalMipPolicy policy =
            ebrp::parseRound50IntervalMipPolicy(args.policy);
        if (!policy.valid) throw std::runtime_error(policy.failure_reason);
        std::filesystem::create_directories(args.artifact_dir);
        writeCommand(args, args.artifact_dir / "command.json");
        const ebrp::Instance instance = ebrp::parseInstanceFile(
            args.input, args.route_time_limit, args.pickup_time,
            args.drop_time);
        if (args.mode == "resolve-cutoff") {
            return resolveCutoff(instance, args, started);
        }

        ebrp::SolveOptions options;
        ebrp::configureRound50IntervalMipV0(options);
        options.gurobi_home = args.gurobi_home;
        options.solve_time_limit = args.process_cap_seconds;
        options.process_wall_time_limit = args.process_cap_seconds;
        options.log_path =
            (args.artifact_dir / "backend_environment.log").string();
        ebrp::CanonicalCompactModelSpec spec;
        spec.strengthened = true;
        spec.interval_restricted = true;
        spec.gamma_L = args.gamma_lower;
        spec.gamma_U = args.gamma_upper;
        spec.add_verified_incumbent_row = true;
        spec.verified_incumbent = args.cutoff;
        spec.incumbent_epsilon = 0.0;
        spec.exact_duplicate_row_elimination =
            policy.cut_formulation == "exact-duplicate-elimination";
        spec.round50_symmetry_policy =
            policy.symmetry_numerical == "route-start-order"
                ? "route-start-order" : "v0-cardinality";
        const auto build_started = Clock::now();
        ebrp::CanonicalCompactModelArtifact artifact =
            ebrp::writeCanonicalCompactModel(
                instance, options, args.artifact_dir / "canonical_model.lp",
                spec);
        const double build_seconds = elapsed(build_started);
        if (!artifact.written) {
            throw std::runtime_error(
                "canonical model failed: " + artifact.failure_reason);
        }
        writeStateIdentity(instance, args, artifact);
        writeStaticLedgers(args, artifact);
        if (args.mode == "build") {
            std::ofstream mapping(args.artifact_dir /
                                  "original_variable_mapping.csv");
            mapping << "mapping_status,source\n"
                    << "deferred_to_native_registry,canonical_model.lp\n";
            const std::vector<std::string> empty_ledgers = {
                "mip_progress.csv", "root_processing_ledger.csv",
                "presolve_ledger.csv", "branching_policy_ledger.csv",
                "cut_family_ledger.csv", "numerical_quality_ledger.csv",
                "model_reuse_ledger.csv", "certificate_ledger.csv"};
            for (const std::string& name : empty_ledgers) {
                std::ofstream(args.artifact_dir / name) << "build_only\n";
            }
            writeArtifactManifest(args.artifact_dir);
            writeCompletion(args.artifact_dir, args, "model_built", false,
                            true, elapsed(started));
            return 0;
        }

        const double remaining = args.process_cap_seconds - elapsed(started) -
            kEvidenceFinalizationReserveSeconds;
        if (!(remaining > 0.01)) {
            throw std::runtime_error("process cap exhausted before optimize");
        }
        std::unique_ptr<ebrp::FixedIntervalMipBackend> backend =
            ebrp::makeGurobiFixedIntervalBackend(instance, options);
        if (!backend || !backend->capabilities().available) {
            throw std::runtime_error(backend
                ? backend->capabilities().failure_reason
                : "gurobi backend factory failed");
        }
        ebrp::FixedIntervalMipRequest request;
        request.solve_kind = ebrp::FixedIntervalSolveKind::PaperTerminalMip;
        request.leaf_id = args.state_id;
        request.gamma_L = args.gamma_lower;
        request.gamma_U = args.gamma_upper;
        request.verified_cutoff = args.cutoff;
        request.global_deadline_remaining_seconds = remaining;
        request.new_leaf = true;
        request.warm_start_enabled = false;
        request.canonical_model_path = artifact.path;
        request.canonical_model_fingerprint = artifact.sha256;
        request.canonical_model_scope = artifact.model_scope;
        request.canonical_row_signature = artifact.row_signature;
        request.native_log_path = args.artifact_dir / "native_gurobi.log";
        request.incremental_model_reuse_enabled = false;
        request.retain_model_after_solve = false;
        request.capture_native_bound_events = true;
        request.interval_mip_policy = policy.name;
        ebrp::FixedIntervalMipOutcome outcome = backend->solve(request);
        outcome.model_build_seconds = build_seconds;
        backend->release();
        const ebrp::FixedIntervalMipBackendStats stats = backend->stats();
        const double process_seconds = elapsed(started);
        writeSolveEvidence(args, artifact, outcome, stats, process_seconds);
        writeArtifactManifest(args.artifact_dir);
        const bool engineering = outcome.attempted && outcome.available &&
            outcome.solver_finalization_reached &&
            outcome.model_fingerprint_matches_request &&
            outcome.exact_zero_gap_roundtrip &&
            outcome.feasibility_consistency_gate &&
            outcome.branch_priority_assignment_valid;
        const bool exact = engineering && (outcome.infeasible ||
            (outcome.native_exact_optimal && outcome.native_bound_available &&
             outcome.incumbent_available &&
             outcome.incumbent_independently_verified &&
             std::fabs(outcome.native_bound - outcome.incumbent_objective) <=
                 1e-7 * std::max(
                     1.0, std::fabs(outcome.incumbent_objective))));
        const std::string status = exact ? "exact" :
            (outcome.interrupted ? "capped" : "failed");
        writeCompletion(args.artifact_dir, args, status, exact, engineering,
                        process_seconds);
        return engineering ? 0 : 5;
    } catch (const std::exception& ex) {
        std::cerr << "Round50IntervalMipExperiment: " << ex.what() << '\n';
        return 2;
    }
}
