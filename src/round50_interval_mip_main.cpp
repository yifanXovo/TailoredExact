#include "CanonicalCompactModel.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "HgaTgbcRunner.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"
#include "Round51IntervalMip.hpp"
#include "Round59Research.hpp"

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
    std::string round59_cuts = "off";
    bool round59_empty_state = false;
    bool round59_compact = false;
    bool round59_current_f0 = false;
    std::string round59_original_compact_sha256;
    bool round59_monitor = false;
    int round59_focus = -1;
    std::string round60_candidate_mode = "off";
    int round60_candidate_maximum_evaluations = 512;
    int round60_candidate_maximum_stations = 16;
    std::vector<int> round60_fixed_inventory;
    double gamma_lower = 0.0;
    double gamma_upper = 0.0;
    double cutoff = 0.0;
    double expected_cutoff = -1.0;
    double process_cap_seconds = 300.0;
    double route_time_limit = 2850.0;
    double pickup_time = 60.0;
    double drop_time = 60.0;
};

struct AdaptiveProbeRecord {
    ebrp::Round51AdaptiveCandidate candidate;
    std::string direction;
    double imposed_bound = 0.0;
    ebrp::Round51ProbeStatus status = ebrp::Round51ProbeStatus::Invalid;
    double child_objective = 0.0;
    ebrp::FixedIntervalMipOutcome outcome;
};

struct AdaptiveExecution {
    bool active = false;
    bool root_valid = false;
    bool root_infeasible = false;
    bool root_closes_state = false;
    bool terminal_model_fresh = false;
    bool lifecycle_valid = false;
    bool priority_readback_valid = false;
    bool priority_retry_used = false;
    std::string fallback_reason = "not_applicable";
    ebrp::FixedIntervalMipOutcome root;
    std::vector<ebrp::Round51AdaptiveCandidate> pool;
    std::vector<AdaptiveProbeRecord> probes;
    std::vector<ebrp::Round51ScoredCandidate> scored;
    ebrp::Round51PrioritySelection selection;
    std::vector<ebrp::FixedIntervalMipOutcome> terminal_attempts;
    double root_work = 0.0;
    double probe_work = 0.0;
    double terminal_work = 0.0;
    double total_work = 0.0;
    double root_solver_time = 0.0;
    double probe_solver_time = 0.0;
    double terminal_solver_time = 0.0;
    double total_solver_time = 0.0;
    double total_model_read_time = 0.0;
    double total_simplex_iterations = 0.0;
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

std::vector<int> parseIntegerList(const std::string& text) {
    std::vector<int> values;
    std::size_t start = 0;
    while (start <= text.size()) {
        const std::size_t end = text.find(',', start);
        const std::string token = text.substr(
            start, end == std::string::npos ? std::string::npos : end - start);
        if (token.empty()) throw std::runtime_error("empty integer-list item");
        values.push_back(std::stoi(token));
        if (end == std::string::npos) break;
        start = end + 1;
    }
    return values;
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
        else if (arg == "--round59-cuts") out.round59_cuts = value(i);
        else if (arg == "--round59-empty-state") out.round59_empty_state = true;
        else if (arg == "--round59-compact") out.round59_compact = true;
        else if (arg == "--round59-current-f0") out.round59_current_f0 = true;
        else if (arg == "--round59-original-compact-sha256") out.round59_original_compact_sha256 = value(i);
        else if (arg == "--round59-monitor") out.round59_monitor = true;
        else if (arg == "--round59-primal-focus") out.round59_focus = 1;
        else if (arg == "--round59-bound-focus") out.round59_focus = 3;
        else if (arg == "--round60-candidate-mode") out.round60_candidate_mode = value(i);
        else if (arg == "--round60-candidate-max-evaluations") out.round60_candidate_maximum_evaluations = std::stoi(value(i));
        else if (arg == "--round60-candidate-max-stations") out.round60_candidate_maximum_stations = std::stoi(value(i));
        else if (arg == "--round60-fixed-inventory") out.round60_fixed_inventory = parseIntegerList(value(i));
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
        out.mode != "lp" &&
        out.mode != "resolve-cutoff") {
        throw std::runtime_error("unsupported mode");
    }
    if (out.state_id.empty() || out.input.empty() || out.artifact_dir.empty()) {
        throw std::runtime_error("state-id, input, and artifact-dir are required");
    }
    if (!(out.process_cap_seconds > 0.0) || out.process_cap_seconds > 7200.0) {
        throw std::runtime_error("process cap must be in (0,7200]");
    }
    if (out.mode != "resolve-cutoff" &&
        (!(out.gamma_lower >= 0.0) ||
         !(out.gamma_upper >= out.gamma_lower) || !std::isfinite(out.cutoff))) {
        throw std::runtime_error("invalid interval or cutoff");
    }
    if (out.round59_cuts != "off" && out.round59_cuts != "static" && out.round59_cuts != "pool")
        throw std::runtime_error("invalid Round59 cut execution mode");
    if (out.round60_candidate_mode != "off" &&
        out.round60_candidate_mode != "dry" &&
        out.round60_candidate_mode != "inject") {
        throw std::runtime_error("invalid Round60 candidate mode");
    }
    if (out.round60_candidate_maximum_evaluations <= 0 ||
        out.round60_candidate_maximum_evaluations > 10000 ||
        out.round60_candidate_maximum_stations <= 0 ||
        out.round60_candidate_maximum_stations > 100) {
        throw std::runtime_error("invalid Round60 candidate work bound");
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
        << "  \"round59_cut_execution\": \"" << args.round59_cuts << "\",\n"
        << "  \"round59_empty_state\": " << boolJson(args.round59_empty_state) << ",\n"
        << "  \"round59_compact\": " << boolJson(args.round59_compact) << ",\n"
        << "  \"round59_monitor\": " << boolJson(args.round59_monitor) << ",\n"
        << "  \"round59_mip_focus\": " << args.round59_focus << ",\n"
        << "  \"round60_candidate_mode\": \""
        << args.round60_candidate_mode << "\",\n"
        << "  \"round60_candidate_maximum_evaluations\": "
        << args.round60_candidate_maximum_evaluations << ",\n"
        << "  \"round60_candidate_maximum_stations\": "
        << args.round60_candidate_maximum_stations << ",\n"
        << "  \"round60_fixed_inventory_size\": "
        << args.round60_fixed_inventory.size() << ",\n"
        << "  \"explicit_cutoff_epsilon\": 0,\n"
        << "  \"gamma_lower\": " << args.gamma_lower << ",\n"
        << "  \"gamma_upper\": " << args.gamma_upper << ",\n"
        << "  \"verified_cutoff\": " << args.cutoff << ",\n"
        << "  \"expected_cutoff\": " << args.expected_cutoff << ",\n"
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
        << (artifact.sparse_family_removal ==
                "triple-support-duration-cover" &&
            artifact.station_state_formulation == "vd-p"
                ? "Interval-MIP-F0-CLEAN+VD-P+SF-R1"
                : (artifact.sparse_family_removal ==
                    "triple-support-duration-cover"
                ? "Interval-MIP-F0-CLEAN+SF-R1"
                : (artifact.station_state_formulation == "aggregate-mc4"
                ? "Interval-MIP-F0-CLEAN+SF-MC4"
                : (artifact.station_state_formulation == "vd-p"
                ? "Interval-MIP-F0-CLEAN+VD-P"
                : (artifact.station_state_formulation == "vd-j"
                ? "Interval-MIP-F0-CLEAN+VD-J"
                : (artifact.round51_subset_duration_big_m ==
                    "tight-tsp-lower-bound"
                ? "Interval-MIP-v0-paper-safe+M1-tight-subset-duration-big-m"
                : (artifact.exact_duplicate_row_elimination
                ? "Interval-MIP-v0-paper-safe+C1-exact-duplicate-elimination"
                : "Interval-MIP-v0-paper-safe"))))))) << "\",\n"
        << "  \"exact_duplicate_row_elimination\": "
        << boolJson(artifact.exact_duplicate_row_elimination) << ",\n"
        << "  \"exact_duplicate_rows_omitted\": "
        << artifact.exact_duplicate_rows_omitted << ",\n"
        << "  \"round50_symmetry_policy\": \""
        << jsonEscape(artifact.round50_symmetry_policy) << "\",\n"
        << "  \"round50_symmetry_rows\": "
        << artifact.round50_symmetry_rows << ",\n"
        << "  \"round51_subset_duration_big_m\": \""
        << jsonEscape(artifact.round51_subset_duration_big_m) << "\",\n"
        << "  \"round51_subset_duration_rows\": "
        << artifact.round51_subset_duration_rows << ",\n"
        << "  \"round51_subset_duration_first_row_id\": "
        << artifact.round51_subset_duration_first_row_id << ",\n"
        << "  \"round51_subset_duration_last_row_id\": "
        << artifact.round51_subset_duration_last_row_id << ",\n"
        << "  \"round51_subset_duration_min_m\": "
        << artifact.round51_subset_duration_min_m << ",\n"
        << "  \"round51_subset_duration_max_m\": "
        << artifact.round51_subset_duration_max_m << ",\n"
        << "  \"round51_historical_m_may_be_unsafe\": "
        << boolJson(artifact.round51_historical_m_may_be_unsafe)
        << ",\n  \"station_state_formulation\": \""
        << jsonEscape(artifact.station_state_formulation) << "\",\n"
        << "  \"sparse_family_removal\": \""
        << jsonEscape(artifact.sparse_family_removal) << "\",\n"
        << "  \"station_state_selector_variables\": "
        << artifact.station_state_selector_variables << ",\n"
        << "  \"station_state_perspective_variables\": "
        << artifact.station_state_perspective_variables << ",\n"
        << "  \"aggregate_mccormick_rows\": "
        << artifact.aggregate_mccormick_rows << ",\n"
        << "  \"support_duration_pair_rows\": "
        << artifact.support_duration_pair_rows << ",\n"
        << "  \"support_duration_triple_rows\": "
        << artifact.support_duration_triple_rows
        << "\n}\n";
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
          << artifact.round50_symmetry_rows << ",\n"
          << "  \"round51_subset_duration_big_m\": \""
          << jsonEscape(artifact.round51_subset_duration_big_m) << "\",\n"
          << "  \"round51_subset_duration_rows\": "
          << artifact.round51_subset_duration_rows << ",\n"
          << "  \"round51_subset_duration_first_row_id\": "
          << artifact.round51_subset_duration_first_row_id << ",\n"
          << "  \"round51_subset_duration_last_row_id\": "
          << artifact.round51_subset_duration_last_row_id << ",\n"
          << "  \"round51_subset_duration_min_m\": "
          << artifact.round51_subset_duration_min_m << ",\n"
          << "  \"round51_subset_duration_max_m\": "
          << artifact.round51_subset_duration_max_m << ",\n"
          << "  \"round51_historical_m_may_be_unsafe\": "
          << boolJson(artifact.round51_historical_m_may_be_unsafe)
          << ",\n  \"station_state_formulation\": \""
          << jsonEscape(artifact.station_state_formulation) << "\",\n"
          << "  \"sparse_family_removal\": \""
          << jsonEscape(artifact.sparse_family_removal) << "\",\n"
          << "  \"station_state_selector_variables\": "
          << artifact.station_state_selector_variables << ",\n"
          << "  \"station_state_perspective_variables\": "
          << artifact.station_state_perspective_variables << ",\n"
          << "  \"aggregate_mccormick_rows\": "
          << artifact.aggregate_mccormick_rows << ",\n"
          << "  \"support_duration_pair_rows\": "
          << artifact.support_duration_pair_rows << ",\n"
          << "  \"support_duration_triple_rows\": "
          << artifact.support_duration_triple_rows
          << "\n}\n";
}

void writeStaticLedgers(const Arguments& args,
                        const ebrp::CanonicalCompactModelArtifact& artifact) {
    std::ofstream size(args.artifact_dir / "formulation_size_ledger.csv");
    size << "state_id,policy,original_rows,original_columns,original_nonzeros,model_scope,exact_duplicate_row_elimination,exact_duplicate_rows_omitted,round50_symmetry_policy,round50_symmetry_rows,round51_subset_duration_big_m,round51_subset_duration_rows,round51_subset_duration_first_row_id,round51_subset_duration_last_row_id,round51_subset_duration_min_m,round51_subset_duration_max_m,historical_m_may_be_unsafe,station_state_formulation,sparse_family_removal,station_state_selector_variables,station_state_perspective_variables,aggregate_mccormick_rows,support_duration_pair_rows,support_duration_triple_rows\n"
         << csvField(args.state_id) << ',' << csvField(args.policy) << ','
         << artifact.rows << ',' << artifact.columns << ','
         << artifact.nonzeros << ',' << csvField(artifact.model_scope) << ','
         << artifact.exact_duplicate_row_elimination << ','
         << artifact.exact_duplicate_rows_omitted << ','
         << csvField(artifact.round50_symmetry_policy) << ','
         << artifact.round50_symmetry_rows << ','
         << csvField(artifact.round51_subset_duration_big_m) << ','
         << artifact.round51_subset_duration_rows << ','
         << artifact.round51_subset_duration_first_row_id << ','
         << artifact.round51_subset_duration_last_row_id << ','
         << artifact.round51_subset_duration_min_m << ','
         << artifact.round51_subset_duration_max_m << ','
         << artifact.round51_historical_m_may_be_unsafe << ','
         << csvField(artifact.station_state_formulation) << ','
         << csvField(artifact.sparse_family_removal) << ','
         << artifact.station_state_selector_variables << ','
         << artifact.station_state_perspective_variables << ','
         << artifact.aggregate_mccormick_rows << ','
         << artifact.support_duration_pair_rows << ','
         << artifact.support_duration_triple_rows << '\n';
}

void writeAdaptiveLedgers(
    const Arguments& args,
    const AdaptiveExecution& adaptive,
    const ebrp::FixedIntervalMipOutcome& terminal,
    double process_seconds) {
    if (!adaptive.active) return;
    std::map<std::string, ebrp::Round51ScoredCandidate> scored;
    for (const auto& item : adaptive.scored) {
        scored[item.candidate.name] = item;
    }
    std::ofstream probes(
        args.artifact_dir / "adaptive_branching_probe_evidence.csv");
    probes << "state_id,policy,candidate_pool_order,variable_name,semantic_family,original_type,root_value,fractionality,direction,imposed_bound,probe_status,child_objective,delta,score,work,solver_time_seconds,model_read_seconds,model_fingerprint_match,bound_override_readback_valid,fresh_disposable_model,failure_reason\n";
    probes << std::setprecision(17);
    for (const AdaptiveProbeRecord& record : adaptive.probes) {
        const auto found = scored.find(record.candidate.name);
        double delta = 0.0, score = 0.0;
        if (found != scored.end()) {
            delta = record.direction == "down"
                ? found->second.delta_down : found->second.delta_up;
            score = found->second.score;
        }
        probes << csvField(args.state_id) << ',' << csvField(args.policy)
               << ',' << record.candidate.pool_order << ','
               << csvField(record.candidate.name) << ','
               << csvField(ebrp::round50VariableFamilyName(
                      record.candidate.family)) << ','
               << record.candidate.original_type << ','
               << record.candidate.root_value << ','
               << record.candidate.fractionality << ','
               << record.direction << ',' << record.imposed_bound << ','
               << ebrp::round51ProbeStatusName(record.status) << ','
               << record.child_objective << ',' << delta << ',' << score
               << ',' << record.outcome.work << ','
               << record.outcome.solver_runtime_seconds << ','
               << record.outcome.model_read_seconds << ','
               << record.outcome.model_fingerprint_matches_request << ','
               << record.outcome.variable_bound_override_readback_valid
               << ',' << (!record.outcome.in_memory_model_reused) << ','
               << csvField(record.outcome.failure_reason) << '\n';
    }

    std::map<std::string, int> assigned;
    for (const auto& item : adaptive.selection.priorities) {
        assigned[item.first] = item.second;
    }
    std::map<std::string, int> observed;
    for (const auto& item : terminal.branch_priority_evidence) {
        observed[item.variable_name] = item.assigned_priority;
    }
    std::ofstream priority(
        args.artifact_dir /
            "adaptive_branching_priority_assignment_audit.csv");
    priority << "state_id,policy,fallback_to_default,fallback_reason,variable_name,semantic_family,pool_order,score,delta_down,delta_up,requested_priority,observed_priority,exact_readback,zero_priority_readback_count,terminal_model_fresh,assignment_status\n";
    priority << std::setprecision(17);
    if (assigned.empty()) {
        priority << csvField(args.state_id) << ',' << csvField(args.policy)
                 << ",1," << csvField(adaptive.fallback_reason)
                 << ",none,none,-1,0,0,0,0,0,1,"
                 << terminal.branch_priority_zero_readback_count << ','
                 << adaptive.terminal_model_fresh << ','
                 << csvField(terminal.branch_priority_assignment_status)
                 << '\n';
    }
    for (const auto& item : adaptive.selection.ranked_valid_candidates) {
        const auto requested = assigned.find(item.candidate.name);
        if (requested == assigned.end()) continue;
        const int seen = observed.count(item.candidate.name)
            ? observed[item.candidate.name] : 0;
        priority << csvField(args.state_id) << ',' << csvField(args.policy)
                 << ",0,none," << csvField(item.candidate.name) << ','
                 << csvField(ebrp::round50VariableFamilyName(
                        item.candidate.family)) << ','
                 << item.candidate.pool_order << ',' << item.score << ','
                 << item.delta_down << ',' << item.delta_up << ','
                 << requested->second << ',' << seen << ','
                 << (seen == requested->second) << ','
                 << terminal.branch_priority_zero_readback_count << ','
                 << adaptive.terminal_model_fresh << ','
                 << csvField(terminal.branch_priority_assignment_status)
                 << '\n';
    }

    std::ofstream overhead(
        args.artifact_dir / "adaptive_branching_overhead_ledger.csv");
    overhead << "state_id,policy,root_lp_work,child_probe_work,terminal_mip_work,total_work,root_lp_solver_time,child_probe_solver_time,terminal_mip_solver_time,total_solver_time,total_process_time,root_model_reads,probe_model_reads,terminal_model_reads,candidate_count,probe_count,priority_count,priority_retry_used,fallback_reason,lifecycle_valid\n"
             << std::setprecision(17) << csvField(args.state_id) << ','
             << csvField(args.policy) << ',' << adaptive.root_work << ','
             << adaptive.probe_work << ',' << adaptive.terminal_work << ','
             << adaptive.total_work << ',' << adaptive.root_solver_time
             << ',' << adaptive.probe_solver_time << ','
             << adaptive.terminal_solver_time << ','
             << adaptive.total_solver_time << ',' << process_seconds << ",1,"
             << adaptive.probes.size() << ','
             << adaptive.terminal_attempts.size() << ','
             << adaptive.pool.size() << ',' << adaptive.probes.size() << ','
             << adaptive.selection.priorities.size() << ','
             << adaptive.priority_retry_used << ','
             << csvField(adaptive.fallback_reason) << ','
             << adaptive.lifecycle_valid << '\n';
}

bool writeLpEvidence(
    const Arguments& args,
    const ebrp::CanonicalCompactModelArtifact& artifact,
    const ebrp::FixedIntervalMipOutcome& outcome,
    double process_seconds) {
    const bool valid = outcome.attempted && outcome.available &&
        outcome.lp_terminal_valid && outcome.optimal &&
        outcome.lp_objective_value_available &&
        outcome.lp_primal_dual_evidence_available &&
        outcome.lp_constraint_evidence_available &&
        outcome.model_fingerprint_matches_request;
    std::ofstream result(args.artifact_dir / "lp_result.json");
    result << std::setprecision(17)
        << "{\n  \"schema\": \"round53-plain-lp-result-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"policy\": \"" << jsonEscape(args.policy) << "\",\n"
        << "  \"valid\": " << boolJson(valid) << ",\n"
        << "  \"native_status\": \""
        << jsonEscape(outcome.native_status) << "\",\n"
        << "  \"objective_available\": "
        << boolJson(outcome.lp_objective_value_available) << ",\n"
        << "  \"objective\": " << outcome.lp_objective_value << ",\n"
        << "  \"work\": " << outcome.work << ",\n"
        << "  \"solver_time_seconds\": "
        << outcome.solver_runtime_seconds << ",\n"
        << "  \"process_time_seconds\": " << process_seconds << ",\n"
        << "  \"simplex_iterations\": "
        << outcome.simplex_iterations << ",\n"
        << "  \"presolved_model_size_available\": "
        << boolJson(outcome.presolved_model_size_available) << ",\n"
        << "  \"presolved_rows\": " << outcome.presolved_row_count << ",\n"
        << "  \"presolved_columns\": "
        << outcome.presolved_column_count << ",\n"
        << "  \"presolved_nonzeros\": "
        << outcome.presolved_nonzero_count << ",\n"
        << "  \"constraint_evidence_available\": "
        << boolJson(outcome.lp_constraint_evidence_available) << ",\n"
        << "  \"constraint_evidence_count\": "
        << outcome.lp_primal_dual_constraint_evidence.size() << ",\n"
        << "  \"model_sha256\": \"" << artifact.sha256 << "\",\n"
        << "  \"failure_reason\": \""
        << jsonEscape(outcome.failure_reason) << "\"\n}\n";

    std::ofstream constraints(
        args.artifact_dir / "lp_constraint_evidence.csv");
    constraints << "state_id,policy,row_index,row_name,slack,dual_multiplier,constraint_basis_status\n"
                << std::setprecision(17);
    for (std::size_t index = 0;
         index < outcome.lp_primal_dual_constraint_evidence.size();
         ++index) {
        const auto& item =
            outcome.lp_primal_dual_constraint_evidence[index];
        constraints << csvField(args.state_id) << ','
                    << csvField(args.policy) << ',' << index << ','
                    << csvField(item.name) << ',' << item.slack << ','
                    << item.dual_multiplier << ','
                    << item.constraint_basis_status << '\n';
    }

    std::ofstream variables(
        args.artifact_dir / "lp_variable_evidence.csv");
    variables << "state_id,policy,column_index,variable_name,original_type,lower_bound,upper_bound,primal_value,reduced_cost,variable_basis_status\n"
              << std::setprecision(17);
    for (std::size_t index = 0;
         index < outcome.lp_primal_dual_variable_evidence.size(); ++index) {
        const auto& item = outcome.lp_primal_dual_variable_evidence[index];
        variables << csvField(args.state_id) << ','
                  << csvField(args.policy) << ',' << index << ','
                  << csvField(item.name) << ',' << item.original_type << ','
                  << item.lower_bound << ',' << item.upper_bound << ','
                  << item.primal_value << ',' << item.reduced_cost << ','
                  << item.variable_basis_status << '\n';
    }
    return valid;
}

void writeSolveEvidence(const Arguments& args,
                        const ebrp::CanonicalCompactModelArtifact& artifact,
                        const ebrp::FixedIntervalMipOutcome& outcome,
                        const ebrp::FixedIntervalMipBackendStats& stats,
                        double process_seconds,
                        const AdaptiveExecution* adaptive = nullptr) {
    const bool tailored_cut_infrastructure =
        !outcome.tailored_cut_callback_active ||
        (outcome.gurobi_cbcut_symbol_loaded &&
         outcome.gurobi_precrush_roundtrip_valid &&
         !outcome.tailored_cut_callback_disabled_after_failure &&
         outcome.tailored_cut_relaxation_vector_failures == 0 &&
         outcome.tailored_cut_submission_failures == 0 &&
         outcome.tailored_cut_callback_failures == 0);
    const bool engineering = outcome.attempted && outcome.available &&
        outcome.solver_finalization_reached &&
        outcome.model_fingerprint_matches_request &&
        outcome.exact_zero_gap_roundtrip &&
        outcome.feasibility_consistency_gate &&
        outcome.branch_priority_assignment_valid &&
        tailored_cut_infrastructure &&
        (!adaptive || !adaptive->active || adaptive->lifecycle_valid);
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

    const double official_work = adaptive && adaptive->active
        ? adaptive->total_work : outcome.work;
    const double official_solver_time = adaptive && adaptive->active
        ? adaptive->total_solver_time : outcome.solver_runtime_seconds;
    const double official_model_read_time = adaptive && adaptive->active
        ? adaptive->total_model_read_time : outcome.model_read_seconds;
    const double official_simplex_iterations = adaptive && adaptive->active
        ? adaptive->total_simplex_iterations : outcome.simplex_iterations;
    std::ofstream result(args.artifact_dir / "result.json");
    result << std::setprecision(17)
        << "{\n  \"schema\": \"round50-fixed-interval-result-v1\",\n"
        << "  \"round59_cut_execution\": \"" << args.round59_cuts << "\",\n"
        << "  \"round59_added_rows_status\": \"" << jsonEscape(outcome.additional_linear_rows_status) << "\",\n"
        << "  \"round59_added_rows_count\": " << outcome.additional_linear_rows_added << ",\n"
        << "  \"round59_mip_focus\": " << args.round59_focus << ",\n"
        << "  \"round60_candidate_mode\": \""
        << jsonEscape(outcome.round60_candidate_mode) << "\",\n"
        << "  \"round60_candidate_callback_active\": "
        << boolJson(outcome.round60_candidate_callback_active) << ",\n"
        << "  \"round60_candidate_disabled_after_failure\": "
        << boolJson(outcome.round60_candidate_disabled_after_failure) << ",\n"
        << "  \"round60_candidate_triggers\": "
        << outcome.round60_candidate_triggers << ",\n"
        << "  \"round60_candidates_generated\": "
        << outcome.round60_candidates_generated << ",\n"
        << "  \"round60_candidates_verified\": "
        << outcome.round60_candidates_verified << ",\n"
        << "  \"round60_candidates_mapped\": "
        << outcome.round60_candidates_mapped << ",\n"
        << "  \"round60_candidates_submitted\": "
        << outcome.round60_candidates_submitted << ",\n"
        << "  \"round60_candidates_confirmed_accepted\": "
        << outcome.round60_candidates_confirmed_accepted << ",\n"
        << "  \"round60_candidates_acceptance_unknown\": "
        << outcome.round60_candidates_acceptance_unknown << ",\n"
        << "  \"round60_best_generated_objective_available\": "
        << boolJson(outcome.round60_best_generated_objective_available)
        << ",\n"
        << "  \"round60_best_generated_objective\": "
        << outcome.round60_best_generated_objective << ",\n"
        << "  \"round60_candidate_overhead_seconds\": "
        << outcome.round60_candidate_overhead_seconds << ",\n"
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
        << "  \"work\": " << official_work << ",\n"
        << "  \"solver_time_seconds\": " << official_solver_time << ",\n"
        << "  \"process_time_seconds\": " << process_seconds << ",\n"
        << "  \"nodes\": " << outcome.nodes << ",\n"
        << "  \"simplex_iterations\": " << official_simplex_iterations << ",\n"
        << "  \"average_iterations_per_node\": "
        << (outcome.nodes > 0.0 ? official_simplex_iterations / outcome.nodes : 0.0) << ",\n"
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
        << "  \"model_read_seconds\": " << official_model_read_time << ",\n"
        << "  \"adaptive_branching\": "
        << boolJson(adaptive && adaptive->active) << ",\n"
        << "  \"adaptive_root_lp_work\": "
        << (adaptive && adaptive->active ? adaptive->root_work : 0.0)
        << ",\n  \"adaptive_child_probe_work\": "
        << (adaptive && adaptive->active ? adaptive->probe_work : 0.0)
        << ",\n  \"adaptive_terminal_mip_work\": "
        << (adaptive && adaptive->active ? adaptive->terminal_work : outcome.work)
        << ",\n  \"adaptive_total_work\": " << official_work
        << ",\n  \"adaptive_fallback_reason\": \""
        << jsonEscape(adaptive && adaptive->active
              ? adaptive->fallback_reason : "not_applicable") << "\",\n"
        << "  \"tailored_cut_policy\": \""
        << jsonEscape(outcome.tailored_cut_policy) << "\",\n"
        << "  \"round53_callback_mode\": \""
        << jsonEscape(outcome.round53_callback_mode) << "\",\n"
        << "  \"round53_mipnode_calls\": "
        << outcome.round53_mipnode_calls << ",\n"
        << "  \"round53_mipnode_status_reads\": "
        << outcome.round53_mipnode_status_reads << ",\n"
        << "  \"round53_relaxation_vector_reads\": "
        << outcome.round53_relaxation_vector_reads << ",\n"
        << "  \"round53_separator_calls\": "
        << outcome.round53_separator_calls << ",\n"
        << "  \"round53_cut_submission_calls\": "
        << outcome.round53_cut_submission_calls << ",\n"
        << "  \"round53_callback_overhead_seconds\": "
        << outcome.round53_callback_overhead_seconds << ",\n"
        << "  \"tailored_cut_callback_active\": "
        << boolJson(outcome.tailored_cut_callback_active) << ",\n"
        << "  \"tailored_cut_infrastructure_gate\": "
        << boolJson(tailored_cut_infrastructure) << ",\n"
        << "  \"gurobi_cbcut_symbol_loaded\": "
        << boolJson(outcome.gurobi_cbcut_symbol_loaded) << ",\n"
        << "  \"gurobi_cblazy_symbol_loaded\": "
        << boolJson(outcome.gurobi_cblazy_symbol_loaded) << ",\n"
        << "  \"gurobi_precrush_requested\": "
        << outcome.gurobi_precrush_requested << ",\n"
        << "  \"gurobi_precrush_effective\": "
        << outcome.gurobi_precrush_effective << ",\n"
        << "  \"gurobi_precrush_roundtrip_valid\": "
        << boolJson(outcome.gurobi_precrush_roundtrip_valid) << ",\n"
        << "  \"tailored_cut_callback_disabled_after_failure\": "
        << boolJson(outcome.tailored_cut_callback_disabled_after_failure)
        << ",\n"
        << "  \"tailored_cut_callback_calls\": "
        << outcome.tailored_cut_callback_calls << ",\n"
        << "  \"tailored_cut_root_callback_calls\": "
        << outcome.tailored_cut_root_callback_calls << ",\n"
        << "  \"tailored_cut_tree_callback_calls\": "
        << outcome.tailored_cut_tree_callback_calls << ",\n"
        << "  \"tailored_cut_nonoptimal_mipnode_callbacks\": "
        << outcome.tailored_cut_nonoptimal_mipnode_callbacks << ",\n"
        << "  \"tailored_cut_relaxation_vector_failures\": "
        << outcome.tailored_cut_relaxation_vector_failures << ",\n"
        << "  \"tailored_cuts_generated\": "
        << outcome.tailored_cuts_generated << ",\n"
        << "  \"tailored_cuts_violated\": "
        << outcome.tailored_cuts_violated << ",\n"
        << "  \"tailored_cuts_selected\": "
        << outcome.tailored_cuts_selected << ",\n"
        << "  \"tailored_cuts_added\": "
        << outcome.tailored_cuts_added << ",\n"
        << "  \"tailored_cut_duplicate_rejections\": "
        << outcome.tailored_cut_duplicate_rejections << ",\n"
        << "  \"tailored_cut_dominated_rejections\": "
        << outcome.tailored_cut_dominated_rejections << ",\n"
        << "  \"tailored_cut_nonviolated_rejections\": "
        << outcome.tailored_cut_nonviolated_rejections << ",\n"
        << "  \"tailored_cut_invalid_rejections\": "
        << outcome.tailored_cut_invalid_rejections << ",\n"
        << "  \"tailored_cut_submission_failures\": "
        << outcome.tailored_cut_submission_failures << ",\n"
        << "  \"tailored_cut_callback_failures\": "
        << outcome.tailored_cut_callback_failures << ",\n"
        << "  \"tailored_cut_pool_size\": "
        << outcome.tailored_cut_pool_size << ",\n"
        << "  \"tailored_cut_callback_overhead_seconds\": "
        << outcome.tailored_cut_callback_overhead_seconds << ",\n"
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
    if (outcome.round53_callback_mode == "c4-separator-dry-run") {
        cuts << csvField(args.state_id) << ',' << csvField(args.policy)
             << ",support-duration-dry-run-selections,"
             << outcome.tailored_cuts_selected << ",callback_diagnostic\n";
    } else if (outcome.tailored_cut_callback_active) {
        cuts << csvField(args.state_id) << ',' << csvField(args.policy)
             << ",support-duration-user-cuts,"
             << outcome.tailored_cuts_added << ",GRBcbcut\n";
    } else if (artifact.round51_subset_duration_rows > 0) {
        cuts << csvField(args.state_id) << ',' << csvField(args.policy)
             << ",support-duration-static-rows,"
             << artifact.round51_subset_duration_rows
             << ",canonical_model\n";
    }

    std::ofstream lifecycle(
        args.artifact_dir / "cut_lifecycle_ledger.csv");
    lifecycle << "state_id,policy,tailored_cut_policy,round53_callback_mode,callback_active,cbcut_symbol_loaded,cblazy_symbol_loaded,precrush_requested,precrush_effective,precrush_roundtrip_valid,mipnode_calls,mipnode_status_reads,relaxation_vector_reads,separator_calls,cut_submission_calls,callback_disabled_after_failure,callback_calls,root_callback_calls,tree_callback_calls,nonoptimal_mipnode_callbacks,relaxation_vector_failures,generated,violated,selected,added,duplicate_rejections,dominated_rejections,nonviolated_rejections,invalid_rejections,submission_failures,callback_failures,global_pool_size,callback_overhead_seconds,infrastructure_gate\n"
              << std::setprecision(17) << csvField(args.state_id) << ','
              << csvField(args.policy) << ','
              << csvField(outcome.tailored_cut_policy) << ','
              << csvField(outcome.round53_callback_mode) << ','
              << outcome.tailored_cut_callback_active << ','
              << outcome.gurobi_cbcut_symbol_loaded << ','
              << outcome.gurobi_cblazy_symbol_loaded << ','
              << outcome.gurobi_precrush_requested << ','
              << outcome.gurobi_precrush_effective << ','
              << outcome.gurobi_precrush_roundtrip_valid << ','
              << outcome.round53_mipnode_calls << ','
              << outcome.round53_mipnode_status_reads << ','
              << outcome.round53_relaxation_vector_reads << ','
              << outcome.round53_separator_calls << ','
              << outcome.round53_cut_submission_calls << ','
              << outcome.tailored_cut_callback_disabled_after_failure << ','
              << outcome.tailored_cut_callback_calls << ','
              << outcome.tailored_cut_root_callback_calls << ','
              << outcome.tailored_cut_tree_callback_calls << ','
              << outcome.tailored_cut_nonoptimal_mipnode_callbacks << ','
              << outcome.tailored_cut_relaxation_vector_failures << ','
              << outcome.tailored_cuts_generated << ','
              << outcome.tailored_cuts_violated << ','
              << outcome.tailored_cuts_selected << ','
              << outcome.tailored_cuts_added << ','
              << outcome.tailored_cut_duplicate_rejections << ','
              << outcome.tailored_cut_dominated_rejections << ','
              << outcome.tailored_cut_nonviolated_rejections << ','
              << outcome.tailored_cut_invalid_rejections << ','
              << outcome.tailored_cut_submission_failures << ','
              << outcome.tailored_cut_callback_failures << ','
              << outcome.tailored_cut_pool_size << ','
              << outcome.tailored_cut_callback_overhead_seconds << ','
              << tailored_cut_infrastructure << '\n';

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
        Arguments args = parseArguments(argc, argv);
        const ebrp::Round50IntervalMipPolicy policy =
            ebrp::parseRound50IntervalMipPolicy(args.policy);
        if (!policy.valid) throw std::runtime_error(policy.failure_reason);
        std::filesystem::create_directories(args.artifact_dir);
        writeCommand(args, args.artifact_dir / "command.json");
        const ebrp::Instance instance = ebrp::parseInstanceFile(
            args.input, args.route_time_limit, args.pickup_time,
            args.drop_time);
        if (args.round59_empty_state) {
            const auto verified = ebrp::verifySolution(instance, {}, 0.15);
            if (!verified.feasible || !verified.original_objective_recomputed || !verified.errors.empty())
                throw std::runtime_error("Round59 diagnostic empty incumbent invalid");
            args.cutoff = verified.objective;
            args.gamma_lower = 0;
            args.gamma_upper = std::min(verified.objective, 1.0-1.0/instance.V);
            writeCommand(args, args.artifact_dir / "command.json");
        }
        if (args.mode == "resolve-cutoff") {
            return resolveCutoff(instance, args, started);
        }

        ebrp::SolveOptions options;
        ebrp::configureRound50IntervalMipV0(options);
        if (args.round59_current_f0) ebrp::configureRound59CurrentF0(options);
        if (!args.round59_original_compact_sha256.empty()) options = ebrp::SolveOptions{};
        options.gurobi_home = args.gurobi_home;
        options.solve_time_limit = args.process_cap_seconds;
        options.process_wall_time_limit = args.process_cap_seconds;
        options.log_path =
            (args.artifact_dir / "backend_environment.log").string();
        ebrp::CanonicalCompactModelSpec spec;
        spec.strengthened = !args.round59_compact;
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
                ? "route-start-order"
                : (policy.symmetry_numerical ==
                       "used-first-route-start-order"
                    ? "used-first-route-start-order"
                    : "v0-cardinality");
        spec.round51_subset_duration_big_m =
            policy.subset_duration_big_m;
        spec.station_state_formulation = policy.station_state_formulation;
        spec.sparse_family_removal = policy.sparse_family_removal;
        const auto build_started = Clock::now();
        if (!args.round59_original_compact_sha256.empty()) {
            // Bind the unrestricted origin byte-for-byte to the official
            // P-GRB export before adding only the interval and cutoff.
            ebrp::CanonicalCompactModelSpec plain;
            const auto origin = ebrp::writeCanonicalCompactModel(
                instance, options, args.artifact_dir / "original_compact_origin.lp", plain);
            if (!origin.written || origin.sha256 != args.round59_original_compact_sha256)
                throw std::runtime_error("Round59 original compact origin SHA256 mismatch");
            spec.strengthened = false;
            spec.round51_subset_duration_big_m = plain.round51_subset_duration_big_m;
        }
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
                "cut_family_ledger.csv", "cut_lifecycle_ledger.csv",
                "numerical_quality_ledger.csv",
                "model_reuse_ledger.csv", "certificate_ledger.csv"};
            for (const std::string& name : empty_ledgers) {
                std::ofstream(args.artifact_dir / name) << "build_only\n";
            }
            writeArtifactManifest(args.artifact_dir);
            writeCompletion(args.artifact_dir, args, "model_built", false,
                            true, elapsed(started));
            return 0;
        }

        const double initial_remaining = args.process_cap_seconds -
            elapsed(started) - kEvidenceFinalizationReserveSeconds;
        if (!(initial_remaining > 0.01)) {
            throw std::runtime_error("process cap exhausted before optimize");
        }
        std::unique_ptr<ebrp::FixedIntervalMipBackend> backend =
            ebrp::makeGurobiFixedIntervalBackend(instance, options);
        if (!backend || !backend->capabilities().available) {
            throw std::runtime_error(backend
                ? backend->capabilities().failure_reason
                : "gurobi backend factory failed");
        }
        auto remaining = [&]() {
            return args.process_cap_seconds - elapsed(started) -
                kEvidenceFinalizationReserveSeconds;
        };
        auto makeRequest = [&](ebrp::FixedIntervalSolveKind kind,
                               const std::string& leaf,
                               const std::string& log_name) {
            ebrp::FixedIntervalMipRequest request;
            request.solve_kind = kind;
            request.leaf_id = leaf;
            request.gamma_L = args.gamma_lower;
            request.gamma_U = args.gamma_upper;
            request.verified_cutoff = args.cutoff;
            request.global_deadline_remaining_seconds =
                std::max(0.001, remaining());
            request.new_leaf = true;
            request.warm_start_enabled = false;
            request.canonical_model_path = artifact.path;
            request.canonical_model_fingerprint = artifact.sha256;
            request.canonical_model_scope = artifact.model_scope;
            request.canonical_row_signature = artifact.row_signature;
            request.native_log_path = args.artifact_dir / log_name;
            request.incremental_model_reuse_enabled = false;
            request.retain_model_after_solve = false;
            request.capture_native_bound_events =
                kind == ebrp::FixedIntervalSolveKind::PaperTerminalMip;
            request.interval_mip_policy = policy.name;
            if (args.round59_cuts != "off") {
                request.additional_linear_rows = ebrp::round59PairDurationRows(instance);
                std::ofstream rows(args.artifact_dir / "round59_additional_rows.csv");
                rows << std::setprecision(17) << "row,variable,coefficient,rhs,scope\n";
                for (const auto& row : request.additional_linear_rows)
                    for (std::size_t i=0; i<row.variable_names.size(); ++i)
                        rows << row.row_name << ',' << row.variable_names[i] << ','
                             << row.coefficients[i] << ',' << row.rhs << ',' << row.scope << '\n';
                if (!rows) throw std::runtime_error("Round59 row ledger write failed");
            }
            request.round59_additional_rows_user_pool = args.round59_cuts == "pool";
            request.round59_mip_focus = args.round59_focus;
            if (args.round59_monitor)
                request.round59_node_samples_path = args.artifact_dir / "node_samples.csv";
            request.round60_candidate_mode = args.round60_candidate_mode;
            request.round60_candidate_maximum_evaluations =
                args.round60_candidate_maximum_evaluations;
            request.round60_candidate_maximum_stations =
                args.round60_candidate_maximum_stations;
            request.round60_candidate_log_path =
                args.artifact_dir / "round60_candidate_events.csv";
            request.round60_fixed_inventory = args.round60_fixed_inventory;
            return request;
        };

        if (args.mode == "lp") {
            auto lp_request = makeRequest(
                ebrp::FixedIntervalSolveKind::PaperLpRelaxation,
                args.state_id + "__plain_lp", "plain_lp_gurobi.log");
            lp_request.capture_lp_primal_dual_evidence = true;
            ebrp::FixedIntervalMipOutcome lp_outcome =
                backend->solve(lp_request);
            lp_outcome.model_build_seconds = build_seconds;
            backend->release();
            const double process_seconds = elapsed(started);
            const bool valid = writeLpEvidence(
                args, artifact, lp_outcome, process_seconds);
            writeArtifactManifest(args.artifact_dir);
            writeCompletion(args.artifact_dir, args,
                            valid ? "lp_optimal" : "lp_failed",
                            false, valid, process_seconds);
            return valid ? 0 : 5;
        }

        AdaptiveExecution adaptive;
        ebrp::FixedIntervalMipOutcome outcome;
        if (policy.adaptive_branching == "root-sparse-2x2" ||
            policy.adaptive_branching == "root-sparse-top1") {
            adaptive.active = true;
            auto root_request = makeRequest(
                ebrp::FixedIntervalSolveKind::PaperLpRelaxation,
                args.state_id + "__a1_root", "a1_root_lp.log");
            root_request.capture_lp_primal_dual_evidence = true;
            adaptive.root = backend->solve(root_request);
            adaptive.root_work = adaptive.root.work;
            adaptive.root_solver_time =
                adaptive.root.solver_runtime_seconds;
            adaptive.total_model_read_time +=
                adaptive.root.model_read_seconds;
            adaptive.root_infeasible = adaptive.root.lp_terminal_valid &&
                adaptive.root.infeasible;
            adaptive.root_valid = adaptive.root.lp_terminal_valid &&
                adaptive.root.model_fingerprint_matches_request &&
                !adaptive.root.in_memory_model_reused &&
                (adaptive.root_infeasible ||
                 (adaptive.root.optimal &&
                  adaptive.root.lp_objective_value_available &&
                  adaptive.root.lp_primal_dual_evidence_available));
            adaptive.root_closes_state = adaptive.root_infeasible ||
                (adaptive.root_valid &&
                 adaptive.root.lp_objective_value >=
                    args.cutoff - 1e-7 * std::max(
                        1.0, std::fabs(args.cutoff)));

            if (!adaptive.root_valid) {
                adaptive.selection.fallback_to_default = true;
                adaptive.selection.fallback_reason = "root_lp_invalid";
            } else if (adaptive.root_closes_state) {
                adaptive.selection.fallback_to_default = true;
                adaptive.selection.fallback_reason =
                    adaptive.root_infeasible
                        ? "root_lp_infeasible" : "root_lp_closes_state";
            } else {
                std::vector<ebrp::Round51RootVariable> variables;
                variables.reserve(
                    adaptive.root.lp_primal_dual_variable_evidence.size());
                for (const auto& item :
                        adaptive.root.lp_primal_dual_variable_evidence) {
                    ebrp::Round51RootVariable variable;
                    variable.name = item.name;
                    variable.original_type = item.original_type;
                    variable.lower_bound = item.lower_bound;
                    variable.upper_bound = item.upper_bound;
                    variable.root_value = item.primal_value;
                    variables.push_back(std::move(variable));
                }
                adaptive.pool =
                    ebrp::round51AdaptiveCandidatePool(variables);
                if (adaptive.pool.empty()) {
                    adaptive.selection.fallback_to_default = true;
                    adaptive.selection.fallback_reason =
                        "no_eligible_fractional_variable";
                } else {
                    for (const auto& candidate : adaptive.pool) {
                        ebrp::Round51ProbeDirection directions[2];
                        for (int direction = 0; direction < 2; ++direction) {
                            AdaptiveProbeRecord record;
                            record.candidate = candidate;
                            record.direction = direction == 0 ? "down" : "up";
                            record.imposed_bound = direction == 0
                                ? candidate.down_upper_bound
                                : candidate.up_lower_bound;
                            if (remaining() > 0.02) {
                                auto probe_request = makeRequest(
                                    ebrp::FixedIntervalSolveKind::PaperLpRelaxation,
                                    args.state_id + "__a1_probe_" +
                                        std::to_string(candidate.pool_order) +
                                        "_" + record.direction,
                                    "a1_probe_" +
                                        std::to_string(candidate.pool_order) +
                                        "_" + record.direction + ".log");
                                ebrp::FixedIntervalMipRequest::
                                    VariableBoundOverride bound;
                                bound.variable_name = candidate.name;
                                if (direction == 0) {
                                    bound.upper_bound_enabled = true;
                                    bound.upper_bound =
                                        candidate.down_upper_bound;
                                } else {
                                    bound.lower_bound_enabled = true;
                                    bound.lower_bound =
                                        candidate.up_lower_bound;
                                }
                                probe_request.variable_bound_overrides.push_back(
                                    std::move(bound));
                                record.outcome = backend->solve(probe_request);
                                adaptive.probe_work += record.outcome.work;
                                adaptive.probe_solver_time +=
                                    record.outcome.solver_runtime_seconds;
                                adaptive.total_model_read_time +=
                                    record.outcome.model_read_seconds;
                                if (record.outcome.lp_terminal_valid &&
                                    record.outcome.optimal &&
                                    record.outcome.lp_objective_value_available) {
                                    record.status =
                                        ebrp::Round51ProbeStatus::Optimal;
                                    record.child_objective =
                                        record.outcome.lp_objective_value;
                                } else if (
                                    record.outcome.lp_terminal_valid &&
                                    record.outcome.infeasible) {
                                    record.status =
                                        ebrp::Round51ProbeStatus::Infeasible;
                                }
                            } else {
                                record.outcome.failure_reason =
                                    "process_cap_exhausted_before_probe";
                            }
                            directions[direction].status = record.status;
                            directions[direction].child_objective =
                                record.child_objective;
                            adaptive.probes.push_back(std::move(record));
                        }
                        adaptive.scored.push_back(
                            ebrp::round51ScoreAdaptiveCandidate(
                                candidate, directions[0], directions[1],
                                adaptive.root.lp_objective_value,
                                args.cutoff));
                    }
                    adaptive.selection =
                        policy.adaptive_branching == "root-sparse-top1"
                        ? ebrp::round51SelectTopOnePriority(adaptive.scored)
                        : ebrp::round51SelectSparsePriorities(adaptive.scored);
                }
            }
            adaptive.fallback_reason =
                adaptive.selection.fallback_reason;

            auto terminal_request = makeRequest(
                ebrp::FixedIntervalSolveKind::PaperTerminalMip,
                args.state_id + "__a1_terminal", "native_gurobi.log");
            for (const auto& item : adaptive.selection.priorities) {
                ebrp::FixedIntervalMipRequest::BranchPriorityOverride value;
                value.variable_name = item.first;
                value.priority = item.second;
                terminal_request.branch_priority_overrides.push_back(
                    std::move(value));
            }
            outcome = backend->solve(terminal_request);
            adaptive.terminal_attempts.push_back(outcome);
            adaptive.terminal_work += outcome.work;
            adaptive.terminal_solver_time +=
                outcome.solver_runtime_seconds;
            adaptive.total_model_read_time += outcome.model_read_seconds;
            if (!adaptive.selection.priorities.empty() &&
                !outcome.branch_priority_assignment_valid) {
                adaptive.priority_retry_used = true;
                adaptive.selection.fallback_to_default = true;
                adaptive.selection.fallback_reason =
                    "priority_attribute_apply_or_readback_failed";
                adaptive.fallback_reason =
                    adaptive.selection.fallback_reason;
                if (remaining() > 0.02) {
                    auto fallback_request = makeRequest(
                        ebrp::FixedIntervalSolveKind::PaperTerminalMip,
                        args.state_id + "__a1_terminal_fallback",
                        "native_gurobi_fallback.log");
                    outcome = backend->solve(fallback_request);
                    adaptive.terminal_attempts.push_back(outcome);
                    adaptive.terminal_work += outcome.work;
                    adaptive.terminal_solver_time +=
                        outcome.solver_runtime_seconds;
                    adaptive.total_model_read_time +=
                        outcome.model_read_seconds;
                }
            }
            adaptive.priority_readback_valid =
                adaptive.priority_retry_used
                    ? outcome.branch_priority_assignment_valid
                    : (adaptive.selection.priorities.empty()
                    ? outcome.branch_priority_assignment_valid
                    : (outcome.branch_priority_assignment_valid &&
                       outcome.branch_priority_assigned_count ==
                           static_cast<long long>(
                               adaptive.selection.priorities.size()) &&
                       outcome.branch_priority_zero_readback_count ==
                           outcome.model_variable_count -
                           static_cast<long long>(
                               adaptive.selection.priorities.size())));
            adaptive.terminal_model_fresh =
                !outcome.in_memory_model_reused &&
                outcome.model_fingerprint_matches_request &&
                outcome.variable_bound_override_status == "not_requested";
            bool probes_clean = true;
            for (const auto& probe : adaptive.probes) {
                if (!probe.outcome.attempted) continue;
                probes_clean = probes_clean &&
                    probe.outcome.model_fingerprint_matches_request &&
                    probe.outcome.variable_bound_override_readback_valid &&
                    !probe.outcome.in_memory_model_reused;
            }
            adaptive.lifecycle_valid = adaptive.root_valid &&
                probes_clean && adaptive.terminal_model_fresh &&
                adaptive.priority_readback_valid;
            std::vector<double> probe_work_values;
            std::vector<double> probe_time_values;
            for (const auto& probe : adaptive.probes) {
                probe_work_values.push_back(probe.outcome.work);
                probe_time_values.push_back(
                    probe.outcome.solver_runtime_seconds);
            }
            adaptive.total_work = ebrp::round51AdaptiveTotal(
                adaptive.root_work, probe_work_values,
                adaptive.terminal_work);
            adaptive.total_solver_time = ebrp::round51AdaptiveTotal(
                adaptive.root_solver_time, probe_time_values,
                adaptive.terminal_solver_time);
            adaptive.total_simplex_iterations =
                adaptive.root.simplex_iterations;
            for (const auto& probe : adaptive.probes) {
                adaptive.total_simplex_iterations +=
                    probe.outcome.simplex_iterations;
            }
            for (const auto& terminal : adaptive.terminal_attempts) {
                adaptive.total_simplex_iterations +=
                    terminal.simplex_iterations;
            }
        } else {
            auto request = makeRequest(
                ebrp::FixedIntervalSolveKind::PaperTerminalMip,
                args.state_id, "native_gurobi.log");
            outcome = backend->solve(request);
        }
        outcome.model_build_seconds = build_seconds;
        backend->release();
        const ebrp::FixedIntervalMipBackendStats stats = backend->stats();
        const double process_seconds = elapsed(started);
        if (adaptive.active) {
            writeAdaptiveLedgers(
                args, adaptive, outcome, process_seconds);
        }
        writeSolveEvidence(
            args, artifact, outcome, stats, process_seconds,
            adaptive.active ? &adaptive : nullptr);
        writeArtifactManifest(args.artifact_dir);
        const bool engineering = outcome.attempted && outcome.available &&
            outcome.solver_finalization_reached &&
            outcome.model_fingerprint_matches_request &&
            outcome.exact_zero_gap_roundtrip &&
            outcome.feasibility_consistency_gate &&
            outcome.branch_priority_assignment_valid &&
            (!outcome.tailored_cut_callback_active ||
             (outcome.gurobi_cbcut_symbol_loaded &&
              outcome.gurobi_precrush_roundtrip_valid &&
              !outcome.tailored_cut_callback_disabled_after_failure &&
              outcome.tailored_cut_relaxation_vector_failures == 0 &&
              outcome.tailored_cut_submission_failures == 0 &&
              outcome.tailored_cut_callback_failures == 0)) &&
            (!adaptive.active || adaptive.lifecycle_valid);
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
