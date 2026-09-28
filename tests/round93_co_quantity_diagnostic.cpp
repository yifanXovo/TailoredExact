#include "Round93CoQuantityDescent.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "Parser.hpp"
#include "Round60Candidates.hpp"
#include "Round61Candidates.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {
namespace fs = std::filesystem;

std::string readText(const fs::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("cannot open witness JSON");
    std::ostringstream out; out << file.rdbuf();
    if (!file.good() && !file.eof()) throw std::runtime_error("witness read failed");
    return out.str();
}

std::size_t matching(const std::string& text, std::size_t begin, char open, char close) {
    if (begin >= text.size() || text[begin] != open)
        throw std::invalid_argument("witness JSON opening delimiter missing");
    int depth = 0; bool quoted = false, escape = false;
    for (std::size_t i = begin; i < text.size(); ++i) {
        const char ch = text[i];
        if (quoted) {
            if (escape) escape = false;
            else if (ch == '\\') escape = true;
            else if (ch == '"') quoted = false;
        } else if (ch == '"') quoted = true;
        else if (ch == open) ++depth;
        else if (ch == close && --depth == 0) return i;
    }
    throw std::invalid_argument("witness JSON unclosed delimiter");
}

std::size_t fieldValue(const std::string& object, const std::string& key) {
    const auto pos = object.find('"' + key + '"');
    if (pos == std::string::npos) throw std::invalid_argument("witness JSON field missing: " + key);
    const auto colon = object.find(':', pos + key.size() + 2);
    if (colon == std::string::npos) throw std::invalid_argument("witness JSON field lacks colon: " + key);
    return object.find_first_not_of(" \t\r\n", colon + 1);
}

std::string arrayField(const std::string& object, const std::string& key) {
    const auto begin = fieldValue(object, key);
    const auto end = matching(object, begin, '[', ']');
    return object.substr(begin, end - begin + 1);
}

int intField(const std::string& object, const std::string& key) {
    const auto begin = fieldValue(object, key);
    if (begin == std::string::npos) throw std::invalid_argument("witness JSON empty integer");
    std::size_t consumed = 0;
    const auto value = std::stoll(object.substr(begin), &consumed);
    const auto end = begin + consumed;
    if (end < object.size() && object[end] != ',' && object[end] != '}' &&
        !std::isspace(static_cast<unsigned char>(object[end])))
        throw std::invalid_argument("witness JSON noninteger field");
    if (value < std::numeric_limits<int>::min() || value > std::numeric_limits<int>::max())
        throw std::out_of_range("witness JSON integer outside int");
    return static_cast<int>(value);
}

std::vector<int> intArray(const std::string& text) {
    std::vector<int> out;
    std::size_t pos = 1;
    while (pos + 1 < text.size()) {
        pos = text.find_first_not_of(" \t\r\n,", pos);
        if (pos == std::string::npos || text[pos] == ']') break;
        std::size_t consumed = 0;
        const auto value = std::stoll(text.substr(pos), &consumed);
        if (value < std::numeric_limits<int>::min() || value > std::numeric_limits<int>::max())
            throw std::out_of_range("witness JSON array integer outside int");
        pos += consumed;
        if (pos < text.size() && text[pos] != ',' && text[pos] != ']' &&
            !std::isspace(static_cast<unsigned char>(text[pos])))
            throw std::invalid_argument("witness JSON malformed integer array");
        out.push_back(static_cast<int>(value));
    }
    return out;
}

std::vector<ebrp::RoutePlan> loadWitness(const fs::path& path, int vehicles) {
    const auto text = readText(path);
    const auto array = arrayField(text, "routes");
    std::vector<ebrp::RoutePlan> routes(static_cast<std::size_t>(vehicles));
    std::vector<bool> seen(static_cast<std::size_t>(vehicles), false);
    for (int k = 0; k < vehicles; ++k) routes[k] = {k, {0, 0}, {}};
    std::size_t pos = 1;
    while ((pos = array.find('{', pos)) != std::string::npos) {
        const auto end = matching(array, pos, '{', '}');
        const auto body = array.substr(pos, end - pos + 1);
        const int vehicle = intField(body, "vehicle");
        if (vehicle < 0 || vehicle >= vehicles || seen[vehicle])
            throw std::invalid_argument("witness duplicate/invalid vehicle");
        seen[vehicle] = true;
        ebrp::RoutePlan route;
        route.vehicle = vehicle;
        route.nodes = intArray(arrayField(body, "nodes"));
        const auto operations = arrayField(body, "operations");
        std::size_t op_pos = 1;
        while (true) {
            op_pos = operations.find_first_not_of(" \t\r\n,", op_pos);
            if (op_pos == std::string::npos || operations[op_pos] == ']') break;
            if (operations[op_pos] == '{') {
                const auto op_end = matching(operations, op_pos, '{', '}');
                const auto op = operations.substr(op_pos, op_end - op_pos + 1);
                route.operations.push_back({intField(op, "station"),
                                            intField(op, "pickup"), intField(op, "drop")});
                op_pos = op_end + 1;
            } else if (operations[op_pos] == '[') {
                const auto op_end = matching(operations, op_pos, '[', ']');
                const auto triple = intArray(operations.substr(op_pos, op_end - op_pos + 1));
                if (triple.size() != 3)
                    throw std::invalid_argument("witness operation array is not a triple");
                route.operations.push_back({triple[0], triple[1], triple[2]});
                op_pos = op_end + 1;
            } else throw std::invalid_argument("witness operation must be object or triple");
        }
        routes[vehicle] = std::move(route);
        pos = end + 1;
    }
    if (std::find(seen.begin(), seen.end(), false) != seen.end())
        throw std::invalid_argument("witness omits a vehicle route");
    return routes;
}

std::string quoted(const std::string& value) {
    std::string out = "\"";
    for (unsigned char ch : value) {
        if (ch == '"' || ch == '\\') out.push_back('\\');
        if (ch < 32) throw std::invalid_argument("control character in JSON field");
        out.push_back(static_cast<char>(ch));
    }
    out.push_back('"'); return out;
}

void requireFinite(double x, const char* name) {
    if (!std::isfinite(x)) throw std::invalid_argument(std::string("nonfinite ") + name);
}
} // namespace

int main(int argc, char** argv) {
    const auto started = std::chrono::steady_clock::now();
    try {
        fs::path input, witness, out;
        double T = std::numeric_limits<double>::quiet_NaN();
        double pickup = std::numeric_limits<double>::quiet_NaN();
        double drop = std::numeric_limits<double>::quiet_NaN();
        double lambda = std::numeric_limits<double>::quiet_NaN();
        double whole_seconds = 0;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            auto value = [&]() {
                if (++i >= argc) throw std::invalid_argument("missing diagnostic argument value");
                return std::string(argv[i]);
            };
            if (arg == "--input") input = value();
            else if (arg == "--witness") witness = value();
            else if (arg == "--out-dir") out = value();
            else if (arg == "--T") T = std::stod(value());
            else if (arg == "--pickup-time") pickup = std::stod(value());
            else if (arg == "--drop-time") drop = std::stod(value());
            else if (arg == "--lambda") lambda = std::stod(value());
            else if (arg == "--whole-run-seconds") whole_seconds = std::stod(value());
            else throw std::invalid_argument("unknown diagnostic argument: " + arg);
        }
        if (input.empty() || witness.empty() || out.empty())
            throw std::invalid_argument("diagnostic requires input, witness and out-dir");
        requireFinite(T, "T"); requireFinite(pickup, "pickup time");
        requireFinite(drop, "drop time"); requireFinite(lambda, "lambda");
        requireFinite(whole_seconds, "whole-run seconds");
        if (pickup < 0 || drop < 0 || whole_seconds < 0)
            throw std::invalid_argument("negative duration parameter or whole-run cap");
        if (fs::exists(out)) throw std::invalid_argument("diagnostic out-dir must be new");
        const auto input_sha = ebrp::fileSha256(input);
        const auto witness_sha = ebrp::fileSha256(witness);
        auto in = ebrp::parseInstanceFile(input, T, pickup, drop);
        auto routes = loadWitness(witness, in.M);
        const auto initial = ebrp::verifyRound93StartingWitness(in, routes, lambda);
        fs::create_directories(out);
        std::ofstream points(out / "points.jsonl");
        points << std::setprecision(17);
        if (!points) throw std::runtime_error("cannot create point receipt");
        const auto observer = [&](const ebrp::Round93CoQuantityPoint& p) {
            points << "{\"pass\":" << p.pass << ",\"a\":" << p.first
                   << ",\"b\":" << p.second << ",\"t\":" << p.delta
                   << ",\"Y_a\":" << p.inventory_first
                   << ",\"Y_b\":" << p.inventory_second
                   << ",\"physical_checked\":" << (p.physical_checked ? "true" : "false")
                   << ",\"feasible\":" << (p.feasible ? "true" : "false")
                   << ",\"load_feasible\":" << (p.load_feasible ? "true" : "false")
                   << ",\"station_feasible\":" << (p.station_feasible ? "true" : "false")
                   << ",\"duration_feasible\":" << (p.duration_feasible ? "true" : "false")
                   << ",\"objective_recomputed\":" << (p.objective_recomputed ? "true" : "false")
                   << ",\"reason\":" << quoted(p.rejection_reason);
            if (p.objective_recomputed)
                points << ",\"F\":" << p.objective << ",\"G\":" << p.G
                       << ",\"P\":" << p.P;
            points << "}\n";
            points.flush();
            if (!points) throw std::runtime_error("point receipt write failed");
        };
        ebrp::SolveOptions options;
        options.lambda = lambda;
        if (whole_seconds > 0) {
            options.process_start_time_valid = true;
            options.process_start_time = started;
            options.process_wall_time_limit = whole_seconds;
            options.process_shutdown_margin_seconds = 0;
        }
        const auto result = ebrp::runRound93CoQuantityDescent(in, options, routes, observer);
        std::ofstream acceptances(out / "acceptances.jsonl");
        acceptances << std::setprecision(17);
        for (std::size_t i = 0; i < result.accepted_choices.size(); ++i) {
            const auto& c = result.accepted_choices[i];
            acceptances << "{\"pass\":" << (i + 1) << ",\"a\":" << c.first
                        << ",\"b\":" << c.second << ",\"t\":" << c.delta
                        << ",\"F\":" << c.objective << "}\n";
        }
        acceptances.flush();
        if (!acceptances) throw std::runtime_error("acceptance receipt write failed");
        ebrp::VerifiedCandidateStore store;
        if (!store.consider(in, lambda, result.routes, "round93_co_line_offline", "original_problem"))
            throw std::runtime_error("final co-line witness could not be independently verified");
        ebrp::writeRound61Witness(out / "final_witness.json", in, lambda, store.best());
        const double wall = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        std::ofstream summary(out / "summary.json");
        summary << std::setprecision(17)
                << "{\"input_sha256\":" << quoted(input_sha)
                << ",\"witness_sha256\":" << quoted(witness_sha)
                << ",\"V\":" << in.V << ",\"M\":" << in.M
                << ",\"T\":" << T << ",\"pickup_time\":" << pickup
                << ",\"drop_time\":" << drop << ",\"lambda\":" << lambda
                << ",\"whole_run_seconds\":" << whole_seconds
                << ",\"wall_seconds\":" << wall
                << ",\"initial_F\":" << initial.objective
                << ",\"initial_G\":" << initial.G << ",\"initial_P\":" << initial.P
                << ",\"final_F\":" << result.verification.objective
                << ",\"final_G\":" << result.verification.G
                << ",\"final_P\":" << result.verification.P
                << ",\"passes\":" << result.stats.passes
                << ",\"station_pairs\":" << result.stats.station_pairs
                << ",\"integer_points\":" << result.stats.integer_points
                << ",\"feasible_points\":" << result.stats.feasible_points
                << ",\"load_rejections\":" << result.stats.load_rejections
                << ",\"station_rejections\":" << result.stats.station_rejections
                << ",\"duration_rejections\":" << result.stats.duration_rejections
                << ",\"integer_domain_rejections\":" << result.stats.integer_domain_rejections
                << ",\"other_physical_rejections\":" << result.stats.other_physical_rejections
                << ",\"nonfinite_rejections\":" << result.stats.nonfinite_rejections
                << ",\"accepted\":" << result.stats.accepted
                << ",\"deleted_stops\":" << result.stats.deleted_stops
                << ",\"sign_flips\":" << result.stats.sign_flips
                << ",\"exhausted\":" << (result.stats.exhausted ? "true" : "false")
                << ",\"deadline\":" << (result.stats.deadline_reached ? "true" : "false")
                << ",\"verification_failed\":" << (result.stats.verification_failed ? "true" : "false")
                << ",\"rejection_reason\":" << quoted(result.stats.rejection_reason)
                << "}\n";
        summary.flush();
        if (!summary) throw std::runtime_error("summary receipt write failed");
        std::cout << "Round93 co-line receipt: " << (out / "summary.json").string() << '\n';
    } catch (const std::exception& e) {
        std::cerr << "Round93 co-line diagnostic rejected: " << e.what() << '\n';
        return 1;
    }
}
