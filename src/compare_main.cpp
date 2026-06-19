#include "CplexBaseline.hpp"
#include "Parser.hpp"
#include "Result.hpp"
#include "TailoredExact.hpp"

#include <algorithm>
#include <cctype>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

void usage() {
    std::cerr
        << "Usage: ExactEBRPCompare --input <path> --lambda 0.15 --T 3600 "
        << "--threads <N> --time-limit <seconds> --out <csv_or_json> "
        << "[--bpc-workers <N>] [--pricing-threads <N>] "
        << "[--parallel-frontier true|false] [--parallel-nodes true|false] "
        << "[--frontier-relax-seconds <seconds>] [--route-mask-max-v <V>] "
        << "[--bpc-incumbent none|greedy|random|local|pool|pricing|portfolio|strong] [--bpc-incumbent-seconds <seconds>] [--bpc-incumbent-rounds <N>] "
        << "[--frontier-final-closure true|false] [--frontier-final-nodes <N>] "
        << "[--inventory-probe-max-v <V>] [--inventory-probe-seconds <seconds>]\n";
}

std::string requireValue(int& i, int argc, char** argv) {
    if (i + 1 >= argc) throw std::runtime_error(std::string("Missing value for ") + argv[i]);
    return argv[++i];
}

bool parseBoolValue(const std::string& s) {
    std::string v = s;
    std::transform(v.begin(), v.end(), v.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (v == "true" || v == "1" || v == "yes" || v == "on") return true;
    if (v == "false" || v == "0" || v == "no" || v == "off") return false;
    throw std::runtime_error("Expected boolean value, got: " + s);
}

ebrp::SolveOptions parseArgs(int argc, char** argv) {
    ebrp::SolveOptions opt;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--input") opt.input_path = requireValue(i, argc, argv);
        else if (arg == "--lambda") opt.lambda = std::stod(requireValue(i, argc, argv));
        else if (arg == "--T") opt.total_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--threads") opt.threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--bpc-workers") opt.bpc_workers = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--pricing-threads") opt.pricing_threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--parallel-frontier") opt.parallel_frontier = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--parallel-nodes") opt.parallel_nodes = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--time-limit") opt.solve_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-relax-seconds") opt.frontier_relax_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--route-mask-max-v") opt.route_mask_max_v = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--bpc-incumbent") opt.bpc_incumbent = requireValue(i, argc, argv);
        else if (arg == "--bpc-incumbent-seconds") opt.bpc_incumbent_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--bpc-incumbent-rounds") opt.bpc_incumbent_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-final-closure") opt.frontier_final_closure = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-final-nodes") opt.frontier_final_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--inventory-probe-max-v") opt.inventory_probe_max_v = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--inventory-probe-seconds") opt.inventory_probe_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--out") opt.out_path = requireValue(i, argc, argv);
        else if (arg == "--help" || arg == "-h") {
            usage();
            std::exit(0);
        } else {
            throw std::runtime_error("Unknown argument: " + arg);
        }
    }
    if (opt.input_path.empty()) throw std::runtime_error("--input is required");
    if (opt.threads <= 0) opt.threads = 1;
    if (opt.bpc_workers <= 0) opt.bpc_workers = std::max(1, opt.threads);
    if (opt.pricing_threads <= 0) opt.pricing_threads = 1;
    if (opt.route_mask_max_v < 0) opt.route_mask_max_v = 0;
    if (opt.bpc_incumbent_seconds < 0.0) opt.bpc_incumbent_seconds = 0.0;
    if (opt.bpc_incumbent_rounds < 1) opt.bpc_incumbent_rounds = 1;
    if (opt.frontier_final_nodes < 1) opt.frontier_final_nodes = 1;
    return opt;
}

std::string csvEscape(const std::string& s) {
    if (s.find_first_of(",\"\n\r") == std::string::npos) return s;
    std::string out = "\"";
    for (char c : s) {
        if (c == '"') out += "\"\"";
        else out.push_back(c);
    }
    out += '"';
    return out;
}

std::string joinNotes(const std::vector<std::string>& notes) {
    std::ostringstream out;
    for (std::size_t i = 0; i < notes.size(); ++i) {
        if (i) out << " | ";
        out << notes[i];
    }
    return out.str();
}

void writeMethodRow(std::ostringstream& out,
                    const ebrp::SolveResult& result,
                    const ebrp::SolveResult& paired,
                    double certified_speedup) {
    out << csvEscape(result.instance_name) << ","
        << csvEscape(result.method) << ","
        << csvEscape(ebrp::inferMethodScope(result)) << ","
        << (ebrp::inferSolvesOriginalObjective(result) ? "true" : "false") << ","
        << (ebrp::inferIsBpc(result) ? "true" : "false") << ","
        << csvEscape(ebrp::inferCertificateType(result)) << ","
        << csvEscape(result.status) << ","
        << result.objective << ","
        << result.lower_bound << ","
        << result.upper_bound << ","
        << result.gap << ","
        << result.runtime_seconds << ","
        << (result.wall_time_seconds > 0.0 ? result.wall_time_seconds : result.runtime_seconds) << ","
        << (result.aggregate_worker_time_seconds > 0.0
            ? result.aggregate_worker_time_seconds
            : result.pricing_time_seconds + result.master_time_seconds + result.bound_time_seconds) << ","
        << csvEscape(ebrp::inferStopReason(result)) << ","
        << (ebrp::inferVerifierPassed(result) ? "true" : "false") << ","
        << result.unresolved_intervals << ","
        << result.invalid_bound_intervals << ","
        << result.pricing_closed_nodes << ","
        << result.open_nodes << ","
        << result.columns << ","
        << result.nodes << ","
        << result.pricing_calls << ","
        << result.cuts_added << ","
        << result.bpc_workers << ","
        << result.pricing_threads << ","
        << (result.parallel_frontier ? "true" : "false") << ","
        << (result.parallel_nodes ? "true" : "false") << ","
        << result.parallel_tasks << ","
        << result.pricing_time_seconds << ","
        << result.master_time_seconds << ","
        << result.bound_time_seconds << ","
        << result.route_mask_time_seconds << ","
        << (ebrp::inferCertifiedOriginalProblem(result) ? "true" : "false") << ","
        << csvEscape(result.result_file) << ","
        << csvEscape(result.log_file) << ","
        << csvEscape(paired.method) << ","
        << csvEscape(paired.status) << ","
        << paired.gap << ","
        << paired.runtime_seconds << ",";
    if (certified_speedup > 0.0) out << certified_speedup;
    out << "," << csvEscape(joinNotes(result.notes)) << "\n";
}

std::string comparisonCsv(const std::vector<std::pair<ebrp::SolveResult, ebrp::SolveResult>>& rows) {
    std::ostringstream out;
    out << std::setprecision(12);
    out << "instance,method,method_scope,solves_original_objective,is_bpc,certificate_type,"
        << "status,objective,lower_bound,upper_bound,gap,runtime_seconds,wall_time_seconds,"
        << "aggregate_worker_time_seconds,stop_reason,"
        << "verifier_passed,unresolved_intervals,invalid_bound_intervals,pricing_closed_nodes,"
        << "open_nodes,columns,nodes,pricing_calls,cuts_added,bpc_workers,pricing_threads,"
        << "parallel_frontier,parallel_nodes,parallel_tasks,pricing_time_seconds,master_time_seconds,"
        << "bound_time_seconds,route_mask_time_seconds,certified_original_problem,result_file,log_file,"
        << "paired_method,paired_status,paired_gap,paired_runtime_seconds,"
        << "certified_optimal_speedup,notes\n";
    for (const auto& row : rows) {
        const auto& t = row.first;
        const auto& c = row.second;
        const bool strict_speedup =
            ebrp::inferCertifiedOriginalProblem(t) &&
            ebrp::inferCertifiedOriginalProblem(c);
        const double speedup = (strict_speedup && t.runtime_seconds > 0.0 && c.runtime_seconds > 0.0)
            ? c.runtime_seconds / t.runtime_seconds : 0.0;
        writeMethodRow(out, t, c, speedup);
        writeMethodRow(out, c, t, speedup > 0.0 ? 1.0 / speedup : 0.0);
    }
    return out.str();
}

} // namespace

int main(int argc, char** argv) {
    try {
        ebrp::SolveOptions opt = parseArgs(argc, argv);
        std::vector<std::filesystem::path> files = ebrp::collectInputFiles(opt.input_path);
        std::vector<std::pair<ebrp::SolveResult, ebrp::SolveResult>> rows;
        for (const auto& file : files) {
            ebrp::Instance instance = ebrp::parseInstanceFile(
                file, opt.total_time_limit, opt.pickup_time, opt.drop_time);
            ebrp::SolveOptions tailored_opt = opt;
            tailored_opt.method = "tailored";
            tailored_opt.log_path.clear();
            ebrp::SolveResult tailored = ebrp::solveTailoredExact(instance, tailored_opt);
            ebrp::SolveOptions cplex_opt = opt;
            cplex_opt.method = "cplex";
            cplex_opt.plain_baseline = true;
            cplex_opt.log_path.clear();
            ebrp::SolveResult cplex = ebrp::solveCplexBaseline(instance, cplex_opt);
            tailored.result_file = opt.out_path;
            cplex.result_file = opt.out_path;
            if (tailored.log_file.empty()) tailored.log_file = tailored_opt.log_path;
            if (cplex.log_file.empty()) cplex.log_file = cplex_opt.log_path;
            std::cout << instance.name << " tailored=" << tailored.status
                      << " cplex=" << cplex.status << "\n";
            rows.push_back({std::move(tailored), std::move(cplex)});
        }
        std::string output = comparisonCsv(rows);
        if (!opt.out_path.empty()) ebrp::writeTextFile(opt.out_path, output);
        else std::cout << output;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ExactEBRPCompare error: " << e.what() << "\n";
        usage();
        return 1;
    }
}
