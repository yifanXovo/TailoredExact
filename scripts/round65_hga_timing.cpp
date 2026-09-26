// Observational harness linked to the already frozen v5 core archive.
// No optimizer, changed genetic operator, alternative constructor or native start.
#include "Round61Candidates.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "ProcessPhaseLedger.hpp"
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

int main(int argc, char** argv) {
    const auto began = std::chrono::steady_clock::now();
    try {
        if (argc != 7) throw std::runtime_error("input T pickup drop lambda output required");
        const std::filesystem::path output = argv[6];
        std::filesystem::create_directories(output / "external");
        ebrp::SolveOptions process;
        process.process_start_time = began;
        process.process_start_time_valid = true;
        process.process_wall_time_limit = 120;
        process.process_shutdown_margin_seconds = 3;
        process.process_phase_ledger_path = (output / "phases.csv").string();
        ebrp::recordProcessPhase(process, "process_entry", "start");
        const double lambda = std::stod(argv[5]);
        if (!std::isfinite(lambda) || lambda < 0) throw std::runtime_error("lambda must be finite and nonnegative");
        const auto in = ebrp::parseInstanceFile(argv[1], std::stod(argv[2]),
            std::stod(argv[3]), std::stod(argv[4]));
        for (double weight : in.weights)
            if (!std::isfinite(weight) || weight < 0) throw std::runtime_error("nonnegative finite weights required");
        ebrp::HgaTgbcOptions options;
        options.lambda = lambda;
        options.seed = 20260626u;
        options.pop_size = 24;
        options.iterations = 10;
        options.stop_mode = "generation-stagnation";
        options.no_improve_generation_limit = 2000;
        options.process_options = &process;
        options.publish_verified_improvements = true;
        options.retain_verified_on_log_failure = true;
        options.stop_on_verified_zero = true;
        options.candidate_model_identity = "research-round65-k1-h|original_problem";
        options.generation_log_path = output / "hga.csv";
        options.verified_candidate_log_path = output / "hga_events.csv";
        ebrp::recordProcessPhase(process, "hga_start", "start");
        const auto hga = ebrp::runHgaTgbcNative(in, options);
        const double returned = ebrp::processElapsedSeconds(process);
        ebrp::recordProcessPhase(process, "hga_timing_return");
        ebrp::VerifiedCandidateStore store;
        store.consider(in, lambda, hga.routes, "round65_hga_timing", "original_problem");
        if (!hga.found || !store.hasBest()) throw std::runtime_error("no verified HGA witness");
        const auto& witness = store.best();
        const bool zero = hga.verified_zero_stop && witness.objective >= 0 && witness.objective <= 1e-12;
        const auto path = output / "external/initial_witness.json";
        ebrp::writeRound61Witness(path, in, lambda, witness);
        std::ifstream input(path);
        std::ostringstream payload; payload << input.rdbuf();
        const auto json = payload.str();
        if (json.empty() || json.front() != '{') throw std::runtime_error("witness serialization failed");
        ebrp::recordProcessPhase(process, "final_result_serialization_start", "start");
        std::ofstream result(output / "result.json"); result << std::setprecision(17);
        result << "{\"status\":\"" << (zero ? "optimal" : "hga_timing_no_certificate")
               << "\",\"diagnostic_scope\":\"hga_timing_only_no_optimizer\",\"upper_bound\":" << witness.objective
               << ",\"lower_bound\":0,\"strict_certified_original_problem\":" << (zero ? "true" : "false")
               << ",\"strict_certificate_class\":\"" << (zero ? "verified_zero_nonnegative_objective" : "none") << '"'
               << ",\"incumbent_generation_time_seconds\":" << hga.wall_time_seconds
               << ",\"hga_total_generations\":" << hga.total_generations
               << ",\"hga_decoder_calls\":" << hga.decoder_calls << ',' << json.substr(1);
        result.close();
        std::ofstream timing(output / "hga_timing.json"); timing << std::setprecision(17);
        timing << "{\"optimizer_calls\":0,\"generation\":" << hga.total_generations
               << ",\"decoder_calls\":" << hga.decoder_calls
               << ",\"initialization_seconds\":" << hga.initialization_seconds
               << ",\"decoder_seconds\":" << hga.decoder_seconds
               << ",\"observer_seconds\":" << hga.observer_seconds
               << ",\"cached_route_conversion_seconds\":" << hga.conversion_seconds
               << ",\"hash_seconds\":" << hga.hash_seconds
               << ",\"copy_seconds\":" << hga.copy_seconds
               << ",\"verification_seconds\":" << hga.candidate_verification_seconds
               << ",\"ledger_seconds\":" << hga.ledger_seconds
               << ",\"zero_certificate_HGA_seconds\":" << hga.verified_zero_seconds
               << ",\"HGA_seconds\":" << hga.wall_time_seconds
               << ",\"HGA_return_process_seconds\":" << returned
               << ",\"evidence_persisted\":" << (hga.candidate_evidence_persisted ? "true" : "false")
               << ",\"published_candidates\":" << hga.published_candidate_count
               << ",\"timers_are_nested_not_additive\":true}\n";
        timing.close();
        ebrp::recordProcessPhase(process, "final_result_serialization_complete");
        ebrp::recordProcessPhase(process, "process_exit");
        std::cout << "Frozen-core HGA timing complete; optimizer calls 0\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
