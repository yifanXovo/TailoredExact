#include "Branching.hpp"
#include "Bounds.hpp"
#include "ColumnPool.hpp"
#include "ColumnGeneration.hpp"
#include "CplexBaseline.hpp"
#include "Cuts.hpp"
#include "Evaluator.hpp"
#include "Master.hpp"
#include "Parser.hpp"
#include "Pricing.hpp"
#include "Result.hpp"
#include "TailoredExact.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cctype>
#include <cmath>
#include <exception>
#include <filesystem>
#include <fstream>
#include <functional>
#include <future>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

void usage() {
    std::cerr
        << "Usage: ExactEBRP --method tailored|cplex|pricing|pricing-branch|cuts|branching|master|cg|gcap-cg|gcap-branch|gcap-tree|gcap-frontier|dominance-test|support-pruning-test|route-mask-support-test|incumbent-import-test --input <path> "
        << "--lambda 0.15 --T 3600 --threads <N> --time-limit <seconds> "
        << "--log <logfile> --out <json> "
        << "[--bpc-workers <N>] [--pricing-threads <N>] [--parallel-frontier true|false] [--parallel-nodes true|false] "
        << "[--gini-cap <gamma>] [--gini-floor <gamma>] [--max-nodes <N>] [--frontier-intervals <N>] [--frontier-refine-splits <N>] "
        << "[--frontier-split-batch <N>] [--frontier-retry-passes <N>] [--frontier-retry-nodes <N>] "
        << "[--frontier-retry-reserve <seconds>] [--frontier-relax-seconds <seconds>] [--route-mask-max-v <V>] "
        << "[--bpc-incumbent none|greedy|random|local|pool|pricing|portfolio|strong|compact|compact-cplex] [--bpc-incumbent-seconds <seconds>] [--bpc-incumbent-rounds <N>] "
        << "[--frontier-final-closure true|false] [--frontier-final-nodes <N>] "
        << "[--gcap-warmstart seed|sparse|full] [--gcap-pricing-columns <N>] "
        << "[--column-dominance true|false] [--column-dominance-mode exact|pareto|off] "
        << "[--projection-bound true|false] [--penalty-domain-tightening true|false] "
        << "[--movement-domain-tightening true|false] [--movement-bound-audit true|false] "
        << "[--frontier-best-bound-scheduling true|false] [--frontier-relaxation-cache true|false] "
        << "[--frontier-column-cache true|false] [--frontier-focused-min-lb-retry true|false] "
        << "[--support-duration-pruning true|false] [--support-duration-max-subset-size <N>] "
        << "[--route-mask-support-duration-pruning true|false] [--support-feasibility-oracle true|false] "
        << "[--gcap-seed-cplex] [--gcap-seed-time-limit <seconds>] "
        << "[--incumbent-json <path>] [--incumbent-format auto|exact_result|route_json|csv] "
        << "[--hga-incumbent <path>] [--hga-incumbent-format auto|route_json|csv|legacy] "
        << "[--incumbent-source-name <name>] [--inventory-probe-max-v <V>] [--inventory-probe-seconds <seconds>]\n";
}

std::string requireValue(int& i, int argc, char** argv) {
    if (i + 1 >= argc) throw std::runtime_error(std::string("Missing value for ") + argv[i]);
    return argv[++i];
}

int parseWarmstartLevel(const std::string& value) {
    if (value == "none" || value == "off" || value == "seed" || value == "seed-only") return 0;
    if (value == "sparse" || value == "auto") return 1;
    if (value == "full" || value == "all") return 2;
    throw std::runtime_error("Unknown --gcap-warmstart value: " + value);
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
        if (arg == "--method") opt.method = requireValue(i, argc, argv);
        else if (arg == "--input") opt.input_path = requireValue(i, argc, argv);
        else if (arg == "--lambda") opt.lambda = std::stod(requireValue(i, argc, argv));
        else if (arg == "--T") opt.total_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--threads") opt.threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--bpc-workers") opt.bpc_workers = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--pricing-threads") opt.pricing_threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--parallel-frontier") opt.parallel_frontier = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--parallel-nodes") opt.parallel_nodes = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--time-limit") opt.solve_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--gini-cap") opt.gini_cap = std::stod(requireValue(i, argc, argv));
        else if (arg == "--gini-floor") opt.gini_floor = std::stod(requireValue(i, argc, argv));
        else if (arg == "--max-nodes") opt.max_branch_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-intervals") opt.frontier_intervals = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-refine-splits") opt.frontier_refine_splits = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-split-batch") opt.frontier_split_batch = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-retry-passes") opt.frontier_retry_passes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-retry-nodes") opt.frontier_retry_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-retry-reserve") opt.frontier_retry_reserve_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-relax-seconds") opt.frontier_relax_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--route-mask-max-v") opt.route_mask_max_v = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--bpc-incumbent") opt.bpc_incumbent = requireValue(i, argc, argv);
        else if (arg == "--bpc-incumbent-seconds") opt.bpc_incumbent_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--bpc-incumbent-rounds") opt.bpc_incumbent_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-final-closure") opt.frontier_final_closure = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-final-nodes") opt.frontier_final_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--gcap-warmstart") opt.gcap_warmstart_level = parseWarmstartLevel(requireValue(i, argc, argv));
        else if (arg == "--gcap-pricing-columns") opt.gcap_pricing_columns = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--column-dominance") opt.column_dominance = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--column-dominance-mode") opt.column_dominance_mode = requireValue(i, argc, argv);
        else if (arg == "--projection-bound") opt.projection_bound = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--penalty-domain-tightening") opt.penalty_domain_tightening = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--movement-domain-tightening") opt.movement_domain_tightening = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--movement-bound-audit") opt.movement_bound_audit = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-best-bound-scheduling") opt.frontier_best_bound_scheduling = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-relaxation-cache") opt.frontier_relaxation_cache = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-column-cache") opt.frontier_column_cache = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-min-lb-retry") opt.frontier_focused_min_lb_retry = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--support-duration-pruning") opt.support_duration_pruning = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--support-duration-max-subset-size") opt.support_duration_max_subset_size = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--route-mask-support-duration-pruning") opt.route_mask_support_duration_pruning = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--support-feasibility-oracle") opt.support_feasibility_oracle = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--gcap-seed-cplex") opt.gcap_seed_cplex = true;
        else if (arg == "--gcap-seed-time-limit") opt.gcap_seed_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--incumbent-json") opt.incumbent_json_path = requireValue(i, argc, argv);
        else if (arg == "--incumbent-format") opt.incumbent_format = requireValue(i, argc, argv);
        else if (arg == "--hga-incumbent") opt.hga_incumbent_path = requireValue(i, argc, argv);
        else if (arg == "--hga-incumbent-format") opt.hga_incumbent_format = requireValue(i, argc, argv);
        else if (arg == "--incumbent-source-name") opt.incumbent_source_name = requireValue(i, argc, argv);
        else if (arg == "--inventory-probe-max-v") opt.inventory_probe_max_v = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--inventory-probe-seconds") opt.inventory_probe_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--log") opt.log_path = requireValue(i, argc, argv);
        else if (arg == "--out") opt.out_path = requireValue(i, argc, argv);
        else if (arg == "--plain-baseline") opt.plain_baseline = true;
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
    if (opt.gcap_warmstart_level < 0) opt.gcap_warmstart_level = 0;
    if (opt.gcap_warmstart_level > 2) opt.gcap_warmstart_level = 2;
    if (opt.gcap_pricing_columns < 1) opt.gcap_pricing_columns = 1;
    std::string dominance_mode = opt.column_dominance_mode;
    std::transform(dominance_mode.begin(), dominance_mode.end(), dominance_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (dominance_mode == "off" || dominance_mode == "none" || dominance_mode == "false") {
        opt.column_dominance = false;
        opt.column_dominance_mode = "off";
    } else if (dominance_mode == "pareto") {
        opt.column_dominance_mode = "pareto";
    } else {
        opt.column_dominance_mode = "exact";
    }
    if (opt.frontier_retry_reserve_seconds < 0.0) opt.frontier_retry_reserve_seconds = 0.0;
    if (opt.frontier_relax_seconds == 0.0) opt.frontier_relax_seconds = -1.0;
    if (opt.route_mask_max_v < 0) opt.route_mask_max_v = 0;
    if (opt.support_duration_max_subset_size < 0) opt.support_duration_max_subset_size = 0;
    if (opt.bpc_incumbent_seconds < 0.0) opt.bpc_incumbent_seconds = 0.0;
    if (opt.bpc_incumbent_rounds < 1) opt.bpc_incumbent_rounds = 1;
    if (opt.frontier_final_nodes < 1) opt.frontier_final_nodes = 1;
    return opt;
}

std::size_t findMatchingJsonDelimiter(const std::string& text,
                                      std::size_t open_pos,
                                      char open_ch,
                                      char close_ch) {
    bool in_string = false;
    bool escaped = false;
    int depth = 0;
    for (std::size_t pos = open_pos; pos < text.size(); ++pos) {
        const char ch = text[pos];
        if (in_string) {
            if (escaped) {
                escaped = false;
            } else if (ch == '\\') {
                escaped = true;
            } else if (ch == '"') {
                in_string = false;
            }
            continue;
        }
        if (ch == '"') {
            in_string = true;
            continue;
        }
        if (ch == open_ch) {
            ++depth;
        } else if (ch == close_ch) {
            --depth;
            if (depth == 0) return pos;
        }
    }
    return std::string::npos;
}

std::string extractJsonArrayForKey(const std::string& text,
                                   const std::string& key,
                                   std::size_t offset = 0) {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key, offset);
    if (key_pos == std::string::npos) {
        throw std::runtime_error("JSON key not found: " + key);
    }
    const std::size_t open_pos = text.find('[', key_pos + quoted_key.size());
    if (open_pos == std::string::npos) {
        throw std::runtime_error("JSON array not found for key: " + key);
    }
    const std::size_t close_pos = findMatchingJsonDelimiter(text, open_pos, '[', ']');
    if (close_pos == std::string::npos) {
        throw std::runtime_error("Unclosed JSON array for key: " + key);
    }
    return text.substr(open_pos + 1, close_pos - open_pos - 1);
}

int extractJsonIntForKey(const std::string& text, const std::string& key, int default_value = 0) {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key);
    if (key_pos == std::string::npos) return default_value;
    const std::size_t colon_pos = text.find(':', key_pos + quoted_key.size());
    if (colon_pos == std::string::npos) return default_value;
    std::size_t value_pos = colon_pos + 1;
    while (value_pos < text.size() &&
           (text[value_pos] == ' ' || text[value_pos] == '\t' ||
            text[value_pos] == '\r' || text[value_pos] == '\n')) {
        ++value_pos;
    }
    return std::stoi(text.substr(value_pos));
}

std::vector<int> parseJsonIntList(std::string array_body) {
    for (char& ch : array_body) {
        if (!std::isdigit(static_cast<unsigned char>(ch)) && ch != '-') ch = ' ';
    }
    std::stringstream ss(array_body);
    std::vector<int> values;
    int value = 0;
    while (ss >> value) values.push_back(value);
    return values;
}

std::vector<ebrp::StopOperation> parseJsonOperations(const std::string& operations_body) {
    std::vector<ebrp::StopOperation> operations;
    std::size_t pos = 0;
    while (true) {
        const std::size_t open_pos = operations_body.find('{', pos);
        if (open_pos == std::string::npos) break;
        const std::size_t close_pos = findMatchingJsonDelimiter(operations_body, open_pos, '{', '}');
        if (close_pos == std::string::npos) {
            throw std::runtime_error("Unclosed operation object in incumbent JSON");
        }
        const std::string object = operations_body.substr(open_pos, close_pos - open_pos + 1);
        ebrp::StopOperation op;
        op.station = extractJsonIntForKey(object, "station");
        op.pickup = extractJsonIntForKey(object, "pickup");
        op.drop = extractJsonIntForKey(object, "drop");
        if (op.station > 0 || op.pickup > 0 || op.drop > 0) operations.push_back(op);
        pos = close_pos + 1;
    }
    return operations;
}

std::vector<ebrp::RoutePlan> loadRoutesFromResultJson(const std::string& path, int vehicle_count) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open incumbent JSON: " + path);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    const std::string text = buffer.str();
    const std::string routes_body = extractJsonArrayForKey(text, "routes");

    std::vector<ebrp::RoutePlan> routes(std::max(0, vehicle_count));
    for (int k = 0; k < vehicle_count; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }

    std::size_t pos = 0;
    while (true) {
        const std::size_t open_pos = routes_body.find('{', pos);
        if (open_pos == std::string::npos) break;
        const std::size_t close_pos = findMatchingJsonDelimiter(routes_body, open_pos, '{', '}');
        if (close_pos == std::string::npos) {
            throw std::runtime_error("Unclosed route object in incumbent JSON");
        }
        const std::string object = routes_body.substr(open_pos, close_pos - open_pos + 1);
        ebrp::RoutePlan route;
        route.vehicle = extractJsonIntForKey(object, "vehicle", -1);
        if (route.vehicle < 0 || route.vehicle >= vehicle_count) {
            throw std::runtime_error("incumbent JSON route has invalid vehicle index");
        }
        route.nodes = parseJsonIntList(extractJsonArrayForKey(object, "nodes"));
        route.operations = parseJsonOperations(extractJsonArrayForKey(object, "operations"));
        routes[route.vehicle] = std::move(route);
        pos = close_pos + 1;
    }
    return routes;
}

std::vector<std::string> splitSimpleCsvLine(const std::string& line) {
    std::vector<std::string> cells;
    std::string cell;
    bool in_quotes = false;
    for (std::size_t pos = 0; pos < line.size(); ++pos) {
        const char ch = line[pos];
        if (ch == '"') {
            in_quotes = !in_quotes;
        } else if (ch == ',' && !in_quotes) {
            cells.push_back(cell);
            cell.clear();
        } else {
            cell.push_back(ch);
        }
    }
    cells.push_back(cell);
    for (std::string& value : cells) {
        while (!value.empty() &&
               std::isspace(static_cast<unsigned char>(value.front()))) {
            value.erase(value.begin());
        }
        while (!value.empty() &&
               std::isspace(static_cast<unsigned char>(value.back()))) {
            value.pop_back();
        }
    }
    return cells;
}

std::vector<ebrp::RoutePlan> loadRoutesFromCsv(const std::string& path,
                                               int vehicle_count) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open incumbent CSV: " + path);
    struct Row {
        int vehicle = -1;
        int order = 0;
        int station = 0;
        int pickup = 0;
        int drop = 0;
    };
    std::vector<Row> rows;
    std::string line;
    bool saw_header = false;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        const std::vector<std::string> cells = splitSimpleCsvLine(line);
        if (cells.size() < 5) continue;
        if (!saw_header) {
            saw_header = true;
            std::string first = cells[0];
            std::transform(first.begin(), first.end(), first.begin(),
                           [](unsigned char c) {
                               return static_cast<char>(std::tolower(c));
                           });
            if (first.find("vehicle") != std::string::npos) continue;
        }
        Row row;
        row.vehicle = std::stoi(cells[0]);
        row.order = std::stoi(cells[1]);
        row.station = std::stoi(cells[2]);
        row.pickup = std::stoi(cells[3]);
        row.drop = std::stoi(cells[4]);
        if (row.vehicle < 0 || row.vehicle >= vehicle_count) {
            throw std::runtime_error("incumbent CSV row has invalid vehicle index");
        }
        rows.push_back(row);
    }
    std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) {
        if (a.vehicle != b.vehicle) return a.vehicle < b.vehicle;
        return a.order < b.order;
    });
    std::vector<ebrp::RoutePlan> routes(std::max(0, vehicle_count));
    for (int k = 0; k < vehicle_count; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0};
    }
    for (const Row& row : rows) {
        if (row.station <= 0) continue;
        ebrp::RoutePlan& route = routes[row.vehicle];
        route.nodes.push_back(row.station);
        ebrp::StopOperation op;
        op.station = row.station;
        op.pickup = row.pickup;
        op.drop = row.drop;
        route.operations.push_back(op);
    }
    for (int k = 0; k < vehicle_count; ++k) {
        if (routes[k].nodes.empty()) routes[k].nodes.push_back(0);
        if (routes[k].nodes.back() != 0) routes[k].nodes.push_back(0);
        if (routes[k].nodes.size() == 1) routes[k].nodes.push_back(0);
    }
    return routes;
}

std::vector<ebrp::RoutePlan> loadIncumbentRoutesByFormat(
    const std::string& path,
    const std::string& format,
    int vehicle_count) {
    std::string fmt = format.empty() ? "auto" : format;
    std::transform(fmt.begin(), fmt.end(), fmt.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    if (fmt == "auto") {
        std::filesystem::path p(path);
        std::string ext = p.extension().string();
        std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) {
            return static_cast<char>(std::tolower(c));
        });
        fmt = (ext == ".csv") ? "csv" : "route_json";
    }
    if (fmt == "exact_result" || fmt == "route_json" || fmt == "json") {
        return loadRoutesFromResultJson(path, vehicle_count);
    }
    if (fmt == "csv") {
        return loadRoutesFromCsv(path, vehicle_count);
    }
    if (fmt == "legacy") {
        throw std::runtime_error("legacy HGA incumbent format is not implemented; use route_json or csv schema");
    }
    throw std::runtime_error("unsupported incumbent format: " + format);
}

ebrp::SolveResult solvePricingDiagnostic(const ebrp::Instance& instance,
                                         const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::PricingDuals duals;
    duals.travel_cost = 1.0;
    duals.pickup_cost = instance.pickup_time + instance.drop_time;
    ebrp::PricingOptions pricing_opt;
    pricing_opt.time_limit_seconds = opt.solve_time_limit;
    pricing_opt.support_duration_pruning = opt.support_duration_pruning;
    pricing_opt.support_duration_max_subset_size =
        opt.support_duration_max_subset_size;

    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pricing";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Pricing diagnostic minimizes route duration over one exact route-load column with nonnegative reduced-cost pruning.");

    ebrp::PricingResult best;
    best.best_reduced_cost = std::numeric_limits<double>::infinity();
    for (int k = 0; k < instance.M; ++k) {
        ebrp::PricingResult priced = ebrp::priceRouteLoadColumnExact(
            instance, k, duals, pricing_opt, start);
        result.nodes += priced.route_states + priced.operation_states;
        result.columns += priced.generated_columns;
        result.pricing_calls += 1;
        result.support_duration_cuts_generated +=
            priced.support_duration_cuts_generated;
        result.support_duration_pruned_labels +=
            priced.support_duration_pruned_labels;
        result.support_duration_pruned_columns +=
            priced.support_duration_pruned_columns;
        result.support_duration_strong_cuts_generated +=
            priced.support_duration_strong_cuts_generated;
        result.support_duration_strong_pruned_labels +=
            priced.support_duration_strong_pruned_labels;
        result.support_duration_strong_pruned_columns +=
            priced.support_duration_strong_pruned_columns;
        result.support_duration_max_subset_size =
            std::max(result.support_duration_max_subset_size,
                     priced.support_duration_max_subset_size);
        result.support_duration_precompute_time_seconds +=
            priced.support_duration_precompute_time_seconds;
        std::ostringstream note;
        note << "vehicle " << k
             << " pricing_complete=" << (priced.complete ? "true" : "false")
             << ", columns=" << priced.generated_columns
             << ", route_states=" << priced.route_states
             << ", operation_states=" << priced.operation_states
             << ", support_duration_cuts=" << priced.support_duration_cuts_generated
             << ", support_duration_pruned_labels="
             << priced.support_duration_pruned_labels
             << ", best_reduced_cost=" << priced.best_reduced_cost;
        result.notes.push_back(note.str());
        if (!priced.complete) result.status = "time_limit";
        if (priced.has_column &&
            (!best.has_column || priced.best_reduced_cost < best.best_reduced_cost - 1e-12)) {
            best = std::move(priced);
        }
    }

    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    if (!result.status.empty() && result.status == "time_limit") {
        result.certificate = "not certified; pricing diagnostic did not complete for every vehicle";
        return result;
    }
    if (!best.has_column) {
        result.status = "infeasible";
        result.certificate = "pricing completed but found no nonempty feasible route-load column";
        return result;
    }

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    ebrp::RoutePlan route;
    route.vehicle = best.best_column.vehicle;
    route.nodes.push_back(0);
    for (int station : best.best_column.path) {
        route.nodes.push_back(station);
        ebrp::StopOperation op;
        op.station = station;
        if (best.best_column.q[station] > 0) op.pickup = best.best_column.q[station];
        if (best.best_column.q[station] < 0) op.drop = -best.best_column.q[station];
        if (op.pickup > 0 || op.drop > 0) route.operations.push_back(op);
    }
    route.nodes.push_back(0);
    routes[best.best_column.vehicle] = std::move(route);

    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.lower_bound = best.best_column.reduced_cost;
    result.upper_bound = best.best_column.reduced_cost;
    result.gap = 0.0;
    result.status = result.verification.feasible ? "pricing_complete" : "verification_failed";
    result.certificate = result.verification.feasible
        ? "exact one-vehicle route-load pricing diagnostic completed for all vehicles; objective fields report verified EBRP value for the selected diagnostic route, lower/upper bound report pricing reduced cost"
        : "pricing diagnostic route failed independent verifier";
    return result;
}

bool columnContainsBoth(const ebrp::RouteLoadColumn& column, int first, int second) {
    return (column.mask & (1 << (first - 1))) && (column.mask & (1 << (second - 1)));
}

bool columnContainsExactlyOne(const ebrp::RouteLoadColumn& column, int first, int second) {
    const bool has_first = (column.mask & (1 << (first - 1))) != 0;
    const bool has_second = (column.mask & (1 << (second - 1))) != 0;
    return has_first != has_second;
}

ebrp::RoutePlan routeFromColumn(const ebrp::RouteLoadColumn& column) {
    ebrp::RoutePlan route;
    route.vehicle = column.vehicle;
    route.nodes.push_back(0);
    for (int station : column.path) {
        route.nodes.push_back(station);
        ebrp::StopOperation op;
        op.station = station;
        if (column.q[station] > 0) op.pickup = column.q[station];
        if (column.q[station] < 0) op.drop = -column.q[station];
        if (op.pickup > 0 || op.drop > 0) route.operations.push_back(op);
    }
    route.nodes.push_back(0);
    return route;
}

std::vector<ebrp::RoutePlan> emptyRouteSet(const ebrp::Instance& instance) {
    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    return routes;
}

bool columnFromRoute(const ebrp::Instance& instance,
                     const ebrp::RoutePlan& route,
                     ebrp::RouteLoadColumn& column) {
    if (route.vehicle < 0 || route.vehicle >= instance.M) return false;
    if (route.nodes.size() < 2 || route.nodes.front() != 0 || route.nodes.back() != 0) {
        return false;
    }
    column = ebrp::RouteLoadColumn{};
    column.vehicle = route.vehicle;
    column.q.assign(instance.V + 1, 0);
    std::unordered_set<int> seen;
    for (std::size_t pos = 1; pos + 1 < route.nodes.size(); ++pos) {
        const int station = route.nodes[pos];
        if (station <= 0 || station > instance.V) return false;
        if (!seen.insert(station).second) return false;
        column.path.push_back(station);
        column.mask |= 1 << (station - 1);
    }
    for (const ebrp::StopOperation& op : route.operations) {
        if (op.station <= 0 || op.station > instance.V) return false;
        if (!seen.count(op.station)) return false;
        if (op.pickup < 0 || op.drop < 0 || (op.pickup > 0 && op.drop > 0)) return false;
        column.q[op.station] += op.pickup;
        column.q[op.station] -= op.drop;
        column.pickup += op.pickup;
    }
    for (std::size_t pos = 0; pos + 1 < route.nodes.size(); ++pos) {
        const int a = route.nodes[pos];
        const int b = route.nodes[pos + 1];
        if (a < 0 || a > instance.V || b < 0 || b > instance.V) return false;
        column.travel += instance.dist[a][b];
    }
    column.duration = column.travel +
        (instance.pickup_time + instance.drop_time) * column.pickup;
    column.reduced_cost = column.duration;
    return column.mask != 0 && column.pickup > 0 &&
           column.duration <= instance.total_time_limit + 1e-7;
}

std::string incumbentColumnKey(const ebrp::RouteLoadColumn& column) {
    std::ostringstream out;
    out << column.vehicle << "|" << column.mask << "|";
    for (int station : column.path) out << station << ".";
    out << "|";
    for (int i = 1; i < static_cast<int>(column.q.size()); ++i) {
        if (column.q[i] != 0) out << i << ":" << column.q[i] << ".";
    }
    return out.str();
}

struct BpcOwnedIncumbentResult {
    bool found = false;
    ebrp::Verification verification;
    std::vector<ebrp::RoutePlan> routes;
    long long pricing_calls = 0;
    long long generated_columns = 0;
    long long columns_generated_raw = 0;
    long long columns_after_dominance = 0;
    long long columns_dominated = 0;
    double dominance_time_seconds = 0.0;
    long long route_states = 0;
    long long operation_states = 0;
    long long master_states = 0;
    std::vector<std::string> notes;
};

double objectiveForInventory(const ebrp::Instance& instance,
                             const std::vector<int>& y,
                             double lambda) {
    return ebrp::computeObjectiveParts(instance, y, lambda).objective;
}

bool decodeBestLoadFeasibleRouteForOperations(
    const ebrp::Instance& instance,
    int vehicle,
    const std::vector<int>& q,
    ebrp::RoutePlan& route) {
    route = ebrp::RoutePlan{};
    route.vehicle = vehicle;
    route.nodes = {0, 0};
    route.operations.clear();
    if (vehicle < 0 || vehicle >= instance.M) return false;
    const int qcap = instance.Q[vehicle];
    if (qcap < 0) return false;

    std::vector<int> stations;
    int pickup_total = 0;
    for (int i = 1; i <= instance.V; ++i) {
        if (i >= static_cast<int>(q.size()) || q[i] == 0) continue;
        stations.push_back(i);
        if (q[i] > 0) pickup_total += q[i];
    }
    if (stations.empty()) return true;
    if (pickup_total > qcap) return false;

    const int n = static_cast<int>(stations.size());
    if (n > 20) return false;
    const int full = (1 << n) - 1;
    const int loads = qcap + 1;
    const double inf = std::numeric_limits<double>::infinity();
    const std::size_t state_count =
        static_cast<std::size_t>(1 << n) * static_cast<std::size_t>(n) *
        static_cast<std::size_t>(loads);
    std::vector<double> dp(state_count, inf);
    std::vector<int> parent_state(state_count, -1);
    std::vector<int> parent_load(state_count, -1);

    auto index = [&](int mask, int last_idx, int load) -> std::size_t {
        return (static_cast<std::size_t>(mask) * static_cast<std::size_t>(n)
            + static_cast<std::size_t>(last_idx)) * static_cast<std::size_t>(loads)
            + static_cast<std::size_t>(load);
    };
    auto applyOp = [&](int load, int station, int& next_load) {
        next_load = load + q[station];
        return next_load >= 0 && next_load <= qcap;
    };

    for (int idx = 0; idx < n; ++idx) {
        int next_load = 0;
        if (!applyOp(0, stations[idx], next_load)) continue;
        const int mask = 1 << idx;
        dp[index(mask, idx, next_load)] = instance.dist[0][stations[idx]];
    }

    for (int mask = 1; mask <= full; ++mask) {
        for (int last = 0; last < n; ++last) {
            if ((mask & (1 << last)) == 0) continue;
            for (int load = 0; load <= qcap; ++load) {
                const std::size_t cur_idx = index(mask, last, load);
                const double cur = dp[cur_idx];
                if (!std::isfinite(cur)) continue;
                for (int next = 0; next < n; ++next) {
                    if (mask & (1 << next)) continue;
                    int next_load = 0;
                    if (!applyOp(load, stations[next], next_load)) continue;
                    const int next_mask = mask | (1 << next);
                    const std::size_t nxt_idx = index(next_mask, next, next_load);
                    const double value = cur + instance.dist[stations[last]][stations[next]];
                    if (value + 1e-9 < dp[nxt_idx]) {
                        dp[nxt_idx] = value;
                        parent_state[nxt_idx] = last;
                        parent_load[nxt_idx] = load;
                    }
                }
            }
        }
    }

    double best_travel = inf;
    int best_last = -1;
    int best_load = -1;
    for (int last = 0; last < n; ++last) {
        for (int load = 0; load <= qcap; ++load) {
            const double travel = dp[index(full, last, load)];
            if (!std::isfinite(travel)) continue;
            const double closed = travel + instance.dist[stations[last]][0];
            if (closed + 1e-9 < best_travel) {
                best_travel = closed;
                best_last = last;
                best_load = load;
            }
        }
    }
    if (best_last < 0) return false;
    const double duration = best_travel +
        (instance.pickup_time + instance.drop_time) * pickup_total;
    if (duration > instance.total_time_limit + 1e-7) return false;

    std::vector<int> reversed;
    int mask = full;
    int last = best_last;
    int load = best_load;
    while (last >= 0) {
        reversed.push_back(stations[last]);
        const std::size_t idx = index(mask, last, load);
        const int prev_last = parent_state[idx];
        const int prev_load = parent_load[idx];
        mask ^= (1 << last);
        last = prev_last;
        load = prev_load;
    }
    std::reverse(reversed.begin(), reversed.end());

    route.nodes.clear();
    route.nodes.push_back(0);
    for (int station : reversed) {
        route.nodes.push_back(station);
        ebrp::StopOperation op;
        op.station = station;
        if (q[station] > 0) op.pickup = q[station];
        if (q[station] < 0) op.drop = -q[station];
        if (op.pickup > 0 || op.drop > 0) route.operations.push_back(op);
    }
    route.nodes.push_back(0);
    return true;
}

std::vector<std::vector<int>> qMatrixFromRoutes(const ebrp::Instance& instance,
                                                const std::vector<ebrp::RoutePlan>& routes) {
    std::vector<std::vector<int>> q_by_vehicle(
        instance.M, std::vector<int>(instance.V + 1, 0));
    for (const ebrp::RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M) continue;
        for (const ebrp::StopOperation& op : route.operations) {
            if (op.station <= 0 || op.station > instance.V) continue;
            q_by_vehicle[route.vehicle][op.station] += op.pickup;
            q_by_vehicle[route.vehicle][op.station] -= op.drop;
        }
    }
    return q_by_vehicle;
}

bool buildRoutesFromQMatrix(const ebrp::Instance& instance,
                            const std::vector<std::vector<int>>& q_by_vehicle,
                            std::vector<ebrp::RoutePlan>& routes) {
    if (static_cast<int>(q_by_vehicle.size()) != instance.M) return false;
    routes = emptyRouteSet(instance);
    std::vector<int> owner(instance.V + 1, -1);
    for (int k = 0; k < instance.M; ++k) {
        if (static_cast<int>(q_by_vehicle[k].size()) <= instance.V) return false;
        for (int i = 1; i <= instance.V; ++i) {
            if (q_by_vehicle[k][i] == 0) continue;
            if (owner[i] >= 0) return false;
            owner[i] = k;
        }
        ebrp::RoutePlan route;
        if (!decodeBestLoadFeasibleRouteForOperations(instance, k, q_by_vehicle[k], route)) {
            return false;
        }
        routes[k] = std::move(route);
    }
    return true;
}

std::vector<int> incumbentQuantityCandidates(const ebrp::Instance& instance,
                                             int station,
                                             int current_q) {
    const int min_q = instance.initial[station] - instance.capacity[station];
    const int max_q = instance.initial[station];
    std::vector<int> values;
    auto add = [&](int value) {
        value = std::max(min_q, std::min(max_q, value));
        values.push_back(value);
    };
    add(0);
    add(current_q);
    for (int delta : {1, 2, 3, 5, 8, 13}) {
        add(current_q + delta);
        add(current_q - delta);
    }
    const int target_q = instance.initial[station] - instance.target[station];
    for (int delta = -4; delta <= 4; ++delta) add(target_q + delta);
    add(min_q);
    add(max_q);
    if (instance.V <= 10 && max_q - min_q <= 80) {
        for (int value = min_q; value <= max_q; ++value) add(value);
    }
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
    return values;
}

std::vector<ebrp::RoutePlan> improveIncumbentByLocalSearch(
    const ebrp::Instance& instance,
    double lambda,
    const std::vector<ebrp::RoutePlan>& start_routes,
    int max_passes,
    const std::function<bool()>& timedOut,
    long long& tested_moves,
    std::vector<std::string>& notes,
    const std::string& label) {
    std::vector<std::vector<int>> q_by_vehicle =
        qMatrixFromRoutes(instance, start_routes);
    std::vector<ebrp::RoutePlan> current_routes;
    if (!buildRoutesFromQMatrix(instance, q_by_vehicle, current_routes)) {
        current_routes = emptyRouteSet(instance);
        q_by_vehicle.assign(instance.M, std::vector<int>(instance.V + 1, 0));
    }
    ebrp::Verification current =
        ebrp::verifySolution(instance, current_routes, lambda);
    if (!current.feasible) {
        current_routes = emptyRouteSet(instance);
        q_by_vehicle.assign(instance.M, std::vector<int>(instance.V + 1, 0));
        current = ebrp::verifySolution(instance, current_routes, lambda);
    }

    for (int pass = 0; pass < max_passes && !timedOut(); ++pass) {
        bool improved = false;
        std::vector<std::vector<int>> best_q = q_by_vehicle;
        std::vector<ebrp::RoutePlan> best_routes = current_routes;
        ebrp::Verification best = current;

        for (int station = 1; station <= instance.V && !timedOut(); ++station) {
            int owner = -1;
            int current_q = 0;
            for (int k = 0; k < instance.M; ++k) {
                if (q_by_vehicle[k][station] != 0) {
                    owner = k;
                    current_q = q_by_vehicle[k][station];
                }
            }
            const std::vector<int> q_values =
                incumbentQuantityCandidates(instance, station, current_q);
            for (int new_owner = -1; new_owner < instance.M && !timedOut(); ++new_owner) {
                for (int q_value : q_values) {
                    if (new_owner < 0 && q_value != 0) continue;
                    if (new_owner >= 0 && q_value == 0) continue;
                    if (new_owner == owner && q_value == current_q) continue;
                    std::vector<std::vector<int>> trial_q = q_by_vehicle;
                    for (int k = 0; k < instance.M; ++k) trial_q[k][station] = 0;
                    if (new_owner >= 0) trial_q[new_owner][station] = q_value;
                    std::vector<ebrp::RoutePlan> trial_routes;
                    ++tested_moves;
                    if (!buildRoutesFromQMatrix(instance, trial_q, trial_routes)) continue;
                    ebrp::Verification trial =
                        ebrp::verifySolution(instance, trial_routes, lambda);
                    if (!trial.feasible) continue;
                    if (trial.objective < best.objective - 1e-10) {
                        best = trial;
                        best_q = std::move(trial_q);
                        best_routes = std::move(trial_routes);
                        improved = true;
                    }
                }
            }
        }

        if (!improved) {
            if (instance.V <= 16) {
                auto stationState = [&](int station) {
                    std::pair<int, int> state{-1, 0};
                    for (int k = 0; k < instance.M; ++k) {
                        if (q_by_vehicle[k][station] != 0) {
                            state = {k, q_by_vehicle[k][station]};
                            break;
                        }
                    }
                    return state;
                };
                auto testPairTrial = [&](const std::vector<std::vector<int>>& trial_q) {
                    std::vector<ebrp::RoutePlan> trial_routes;
                    ++tested_moves;
                    if (!buildRoutesFromQMatrix(instance, trial_q, trial_routes)) return;
                    ebrp::Verification trial =
                        ebrp::verifySolution(instance, trial_routes, lambda);
                    if (!trial.feasible) return;
                    if (trial.objective < best.objective - 1e-10) {
                        best = trial;
                        best_q = trial_q;
                        best_routes = std::move(trial_routes);
                        improved = true;
                    }
                };
                for (int a = 1; a <= instance.V && !timedOut(); ++a) {
                    const auto state_a = stationState(a);
                    for (int b = a + 1; b <= instance.V && !timedOut(); ++b) {
                        const auto state_b = stationState(b);
                        if (state_a.first < 0 && state_b.first < 0) continue;

                        std::vector<std::vector<int>> swap_all = q_by_vehicle;
                        for (int k = 0; k < instance.M; ++k) {
                            swap_all[k][a] = 0;
                            swap_all[k][b] = 0;
                        }
                        if (state_b.first >= 0) swap_all[state_b.first][a] = state_b.second;
                        if (state_a.first >= 0) swap_all[state_a.first][b] = state_a.second;
                        testPairTrial(swap_all);

                        if (state_a.first >= 0 && state_b.first >= 0 &&
                            state_a.first != state_b.first) {
                            std::vector<std::vector<int>> swap_owner = q_by_vehicle;
                            swap_owner[state_a.first][a] = 0;
                            swap_owner[state_b.first][b] = 0;
                            swap_owner[state_b.first][a] = state_a.second;
                            swap_owner[state_a.first][b] = state_b.second;
                            testPairTrial(swap_owner);
                        }
                    }
                }
            }
        }

        if (!improved) {
            std::ostringstream note;
            note << "BPC-owned local search " << label
                 << " pass=" << pass
                 << " no improving relocate/resize/swap move, objective="
                 << current.objective;
            notes.push_back(note.str());
            break;
        }
        q_by_vehicle = std::move(best_q);
        current_routes = std::move(best_routes);
        current = best;
        std::ostringstream note;
        note << "BPC-owned local search " << label
             << " pass=" << pass
             << " improved objective=" << current.objective
             << ", G=" << current.G
             << ", P=" << current.P;
        notes.push_back(note.str());
    }
    return current_routes;
}

ebrp::RoutePlan greedyOneRouteIncumbentColumn(
    const ebrp::Instance& instance,
    int vehicle,
    double lambda,
    std::vector<int>& y,
    int& global_mask,
    int mode) {
    ebrp::RoutePlan route;
    route.vehicle = vehicle;
    route.nodes.push_back(0);

    const double cunit = instance.pickup_time + instance.drop_time;
    const int qcap = instance.Q[vehicle];
    int load = 0;
    int pickup_total = 0;
    int last = 0;
    double travel_without_return = 0.0;
    int route_mask = 0;

    while (true) {
        const double current_obj = objectiveForInventory(instance, y, lambda);
        struct Candidate {
            bool found = false;
            int station = 0;
            int quantity = 0;
            bool pickup = false;
            double score = -1e100;
            double benefit = 0.0;
            double next_travel_without_return = 0.0;
        } best;

        for (int station = 1; station <= instance.V; ++station) {
            const int bit = 1 << (station - 1);
            if ((global_mask & bit) || (route_mask & bit)) continue;
            const double next_travel_without_return =
                travel_without_return + instance.dist[last][station];
            const double next_return_travel =
                next_travel_without_return + instance.dist[station][0];

            const int max_pick = std::min(y[station], qcap - load);
            for (int p = 1; p <= max_pick; ++p) {
                const double duration = next_return_travel + cunit * (pickup_total + p);
                if (duration > instance.total_time_limit + 1e-7) break;
                std::vector<int> y2 = y;
                y2[station] -= p;
                const double benefit = current_obj - objectiveForInventory(instance, y2, lambda);
                if (benefit <= 1e-10) continue;
                const double current_return =
                    travel_without_return + instance.dist[last][0] + cunit * pickup_total;
                const double added = std::max(1.0, duration - current_return);
                double score = benefit / added;
                if (mode == 1) score = benefit;
                if (mode == 2) score = benefit / std::max(1.0, instance.dist[last][station]);
                if (score > best.score + 1e-12) {
                    best = {true, station, p, true, score, benefit,
                            next_travel_without_return};
                }
            }

            const int max_drop = std::min(instance.capacity[station] - y[station], load);
            for (int d = 1; d <= max_drop; ++d) {
                const double duration = next_return_travel + cunit * pickup_total;
                if (duration > instance.total_time_limit + 1e-7) break;
                std::vector<int> y2 = y;
                y2[station] += d;
                const double benefit = current_obj - objectiveForInventory(instance, y2, lambda);
                if (benefit <= 1e-10) continue;
                const double current_return =
                    travel_without_return + instance.dist[last][0] + cunit * pickup_total;
                const double added = std::max(1.0, duration - current_return);
                double score = benefit / added;
                if (mode == 1) score = benefit;
                if (mode == 2) score = benefit / std::max(1.0, instance.dist[last][station]);
                if (score > best.score + 1e-12) {
                    best = {true, station, d, false, score, benefit,
                            next_travel_without_return};
                }
            }
        }

        if (!best.found) break;
        route.nodes.push_back(best.station);
        ebrp::StopOperation op;
        op.station = best.station;
        if (best.pickup) {
            op.pickup = best.quantity;
            y[best.station] -= best.quantity;
            load += best.quantity;
            pickup_total += best.quantity;
        } else {
            op.drop = best.quantity;
            y[best.station] += best.quantity;
            load -= best.quantity;
        }
        route.operations.push_back(op);
        travel_without_return = best.next_travel_without_return;
        last = best.station;
        route_mask |= 1 << (best.station - 1);
        global_mask |= 1 << (best.station - 1);
    }

    route.nodes.push_back(0);
    if (route.nodes.size() == 2) route.operations.clear();
    return route;
}

std::vector<ebrp::RoutePlan> buildGreedyIncumbentRoutes(const ebrp::Instance& instance,
                                                        double lambda,
                                                        int mode) {
    std::vector<ebrp::RoutePlan> routes = emptyRouteSet(instance);
    std::vector<int> y = instance.initial;
    int used_mask = 0;
    for (int k = 0; k < instance.M; ++k) {
        ebrp::RoutePlan route =
            greedyOneRouteIncumbentColumn(instance, k, lambda, y, used_mask, mode);
        routes[k] = std::move(route);
    }
    return routes;
}

std::vector<ebrp::RoutePlan> buildRandomizedGreedyIncumbentRoutes(
    const ebrp::Instance& instance,
    double lambda,
    unsigned seed) {
    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> jitter(0.85, 1.15);
    std::vector<ebrp::RoutePlan> routes = emptyRouteSet(instance);
    std::vector<int> y = instance.initial;
    int global_mask = 0;
    std::vector<int> vehicle_order(instance.M);
    for (int k = 0; k < instance.M; ++k) vehicle_order[k] = k;
    std::shuffle(vehicle_order.begin(), vehicle_order.end(), rng);

    const double cunit = instance.pickup_time + instance.drop_time;
    for (int vehicle : vehicle_order) {
        ebrp::RoutePlan route;
        route.vehicle = vehicle;
        route.nodes.push_back(0);
        const int qcap = instance.Q[vehicle];
        int load = 0;
        int pickup_total = 0;
        int last = 0;
        double travel_without_return = 0.0;
        int route_mask = 0;

        while (true) {
            const double current_obj = objectiveForInventory(instance, y, lambda);
            struct Candidate {
                int station = 0;
                int quantity = 0;
                bool pickup = false;
                double score = -1e100;
                double next_travel_without_return = 0.0;
            };
            std::vector<Candidate> candidates;
            for (int station = 1; station <= instance.V; ++station) {
                const int bit = 1 << (station - 1);
                if ((global_mask & bit) || (route_mask & bit)) continue;
                const double next_travel_without_return =
                    travel_without_return + instance.dist[last][station];
                const double next_return_travel =
                    next_travel_without_return + instance.dist[station][0];
                const double current_return =
                    travel_without_return + instance.dist[last][0] +
                    cunit * pickup_total;

                auto consider = [&](int quantity, bool pickup) {
                    if (quantity <= 0) return;
                    const int next_pickup_total =
                        pickup ? pickup_total + quantity : pickup_total;
                    const double duration =
                        next_return_travel + cunit * next_pickup_total;
                    if (duration > instance.total_time_limit + 1e-7) return;
                    std::vector<int> y2 = y;
                    if (pickup) y2[station] -= quantity;
                    else y2[station] += quantity;
                    if (y2[station] < 0 || y2[station] > instance.capacity[station]) return;
                    const double benefit =
                        current_obj - objectiveForInventory(instance, y2, lambda);
                    if (benefit <= 1e-10) return;
                    const double added = std::max(1.0, duration - current_return);
                    const double score = (benefit / added) * jitter(rng);
                    candidates.push_back(
                        Candidate{station, quantity, pickup, score,
                                  next_travel_without_return});
                };

                const int max_pick = std::min(y[station], qcap - load);
                if (max_pick > 0) {
                    const int target_pick =
                        std::max(1, std::min(max_pick, y[station] - instance.target[station]));
                    consider(target_pick, true);
                    consider(max_pick, true);
                    consider(1, true);
                }
                const int max_drop = std::min(instance.capacity[station] - y[station], load);
                if (max_drop > 0) {
                    const int target_drop =
                        std::max(1, std::min(max_drop, instance.target[station] - y[station]));
                    consider(target_drop, false);
                    consider(max_drop, false);
                    consider(1, false);
                }
            }
            if (candidates.empty()) break;
            std::sort(candidates.begin(), candidates.end(),
                      [](const Candidate& a, const Candidate& b) {
                          return a.score > b.score;
                      });
            const int take = std::min<int>(4, candidates.size());
            std::uniform_int_distribution<int> pick_idx(0, take - 1);
            const Candidate chosen = candidates[pick_idx(rng)];
            route.nodes.push_back(chosen.station);
            ebrp::StopOperation op;
            op.station = chosen.station;
            if (chosen.pickup) {
                op.pickup = chosen.quantity;
                y[chosen.station] -= chosen.quantity;
                load += chosen.quantity;
                pickup_total += chosen.quantity;
            } else {
                op.drop = chosen.quantity;
                y[chosen.station] += chosen.quantity;
                load -= chosen.quantity;
            }
            route.operations.push_back(op);
            travel_without_return = chosen.next_travel_without_return;
            last = chosen.station;
            route_mask |= 1 << (chosen.station - 1);
            global_mask |= 1 << (chosen.station - 1);
        }
        route.nodes.push_back(0);
        routes[vehicle] = std::move(route);
    }
    return routes;
}

ebrp::PricingDuals buildObjectiveGradientDuals(const ebrp::Instance& instance,
                                               const std::vector<int>& y,
                                               double lambda,
                                               double travel_cost) {
    ebrp::PricingDuals duals;
    duals.travel_cost = travel_cost;
    duals.pickup_cost = 0.0;
    duals.visit_cost.assign(instance.V + 1, 0.0);
    duals.operation_cost.assign(instance.V + 1, 0.0);
    const double base = objectiveForInventory(instance, y, lambda);
    for (int i = 1; i <= instance.V; ++i) {
        double pick_delta = std::numeric_limits<double>::infinity();
        double drop_delta = std::numeric_limits<double>::infinity();
        if (y[i] > 0) {
            std::vector<int> yp = y;
            --yp[i];
            pick_delta = objectiveForInventory(instance, yp, lambda) - base;
        }
        if (y[i] < instance.capacity[i]) {
            std::vector<int> yd = y;
            ++yd[i];
            drop_delta = objectiveForInventory(instance, yd, lambda) - base;
        }
        if (std::isfinite(pick_delta) && pick_delta < -1e-12 &&
            (!std::isfinite(drop_delta) || pick_delta <= drop_delta)) {
            duals.operation_cost[i] = pick_delta;
        } else if (std::isfinite(drop_delta) && drop_delta < -1e-12) {
            duals.operation_cost[i] = -drop_delta;
        } else if (std::isfinite(pick_delta) && std::isfinite(drop_delta)) {
            duals.operation_cost[i] = 0.5 * (pick_delta - drop_delta);
        }
        duals.visit_cost[i] = 1e-6;
    }
    return duals;
}

int topGradientStationMask(const ebrp::PricingDuals& duals, int V, int limit) {
    std::vector<std::pair<double, int>> ranked;
    for (int i = 1; i <= V; ++i) {
        const double score = (i < static_cast<int>(duals.operation_cost.size()))
            ? std::fabs(duals.operation_cost[i]) : 0.0;
        ranked.push_back({-score, i});
    }
    std::sort(ranked.begin(), ranked.end());
    int mask = 0;
    const int take = std::min(limit, static_cast<int>(ranked.size()));
    for (int pos = 0; pos < take; ++pos) {
        if (-ranked[pos].first <= 1e-12) continue;
        mask |= 1 << (ranked[pos].second - 1);
    }
    return mask;
}

void addIncumbentColumn(std::vector<std::vector<ebrp::RouteLoadColumn>>& pool,
                        std::vector<std::unordered_set<std::string>>& seen,
                        const ebrp::RouteLoadColumn& column) {
    if (column.vehicle < 0 || column.vehicle >= static_cast<int>(pool.size())) return;
    if (column.mask == 0) return;
    if (column.q.empty()) return;
    const std::string key = incumbentColumnKey(column);
    if (seen[column.vehicle].insert(key).second) {
        pool[column.vehicle].push_back(column);
    }
}

BpcOwnedIncumbentResult runBpcOwnedIncumbentGenerator(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt,
    std::chrono::steady_clock::time_point frontier_start) {
    BpcOwnedIncumbentResult out;
    const std::string mode = opt.bpc_incumbent;
    if (mode == "none" || mode == "off" || mode.empty()) {
        out.notes.push_back("BPC-owned incumbent generator disabled");
        return out;
    }

    const auto gen_start = std::chrono::steady_clock::now();
    const double gen_limit = opt.bpc_incumbent_seconds;
    auto timedOut = [&]() {
        if (gen_limit <= 0.0) return false;
        return std::chrono::duration<double>(
            std::chrono::steady_clock::now() - gen_start).count() >= gen_limit;
    };

    std::vector<std::vector<ebrp::RouteLoadColumn>> pool(instance.M);
    std::vector<std::unordered_set<std::string>> seen(instance.M);

    auto considerRoutes = [&](const std::vector<ebrp::RoutePlan>& routes,
                              const std::string& source) {
        ebrp::Verification v = ebrp::verifySolution(instance, routes, opt.lambda);
        std::ostringstream note;
        note << "BPC-owned incumbent candidate " << source
             << " feasible=" << (v.feasible ? "true" : "false")
             << ", objective=" << v.objective
             << ", G=" << v.G
             << ", P=" << v.P;
        out.notes.push_back(note.str());
        if (v.feasible && (!out.found ||
                           v.objective < out.verification.objective - 1e-10)) {
            out.found = true;
            out.verification = v;
            out.routes = routes;
        }
        for (const ebrp::RoutePlan& route : routes) {
            ebrp::RouteLoadColumn col;
            if (columnFromRoute(instance, route, col)) {
                addIncumbentColumn(pool, seen, col);
            }
        }
    };

    const bool wants_greedy =
        mode == "greedy" || mode == "random" || mode == "local" ||
        mode == "pool" || mode == "portfolio" || mode == "strong";
    const bool wants_random =
        mode == "random" || mode == "portfolio" || mode == "strong";
    const bool wants_local =
        mode == "random" || mode == "local" || mode == "pool" ||
        mode == "portfolio" || mode == "strong";
    const bool wants_pricing =
        mode == "pricing" || mode == "portfolio";

    if (wants_greedy) {
        for (int greedy_mode = 0; greedy_mode < 3 && !timedOut(); ++greedy_mode) {
            considerRoutes(buildGreedyIncumbentRoutes(instance, opt.lambda, greedy_mode),
                           "greedy_mode_" + std::to_string(greedy_mode));
            for (int k = 0; k < instance.M; ++k) {
                std::vector<ebrp::RoutePlan> routes = emptyRouteSet(instance);
                std::vector<int> y = instance.initial;
                int used_mask = 0;
                routes[k] = greedyOneRouteIncumbentColumn(
                    instance, k, opt.lambda, y, used_mask, greedy_mode);
                ebrp::RouteLoadColumn col;
                if (columnFromRoute(instance, routes[k], col)) {
                    addIncumbentColumn(pool, seen, col);
                    std::ostringstream note;
                    note << "BPC-owned single-route greedy column mode=" << greedy_mode
                         << ", vehicle=" << k
                         << ", mask=" << col.mask
                         << ", pickup=" << col.pickup
                         << ", duration=" << col.duration;
                    out.notes.push_back(note.str());
                }
            }
        }
    }

    if (wants_random && !timedOut()) {
        const int random_rounds = std::max(4, opt.bpc_incumbent_rounds);
        for (int r = 0; r < random_rounds && !timedOut(); ++r) {
            const unsigned seed = 0xEBB000u + static_cast<unsigned>(9973 * (r + 1));
            considerRoutes(buildRandomizedGreedyIncumbentRoutes(
                               instance, opt.lambda, seed),
                           "random_greedy_seed_" + std::to_string(seed));
        }
    }

    if (wants_local && !timedOut()) {
        long long tested_moves = 0;
        std::vector<std::vector<ebrp::RoutePlan>> starts;
        starts.push_back(emptyRouteSet(instance));
        for (int greedy_mode = 0; greedy_mode < 3; ++greedy_mode) {
            starts.push_back(buildGreedyIncumbentRoutes(instance, opt.lambda, greedy_mode));
        }
        if (wants_random) {
            const int random_starts =
                std::max(1, std::min(6, opt.bpc_incumbent_rounds));
            for (int r = 0; r < random_starts; ++r) {
                const unsigned seed = 0xEBB000u +
                    static_cast<unsigned>(9973 * (r + 1));
                starts.push_back(buildRandomizedGreedyIncumbentRoutes(
                    instance, opt.lambda, seed));
            }
        }
        if (out.found) starts.push_back(out.routes);
        const int max_starts = std::max(1, std::min<int>(
            static_cast<int>(starts.size()), opt.bpc_incumbent_rounds));
        for (int s = 0; s < max_starts && !timedOut(); ++s) {
            std::vector<ebrp::RoutePlan> improved =
                improveIncumbentByLocalSearch(
                    instance, opt.lambda, starts[s],
                    std::max(2, opt.bpc_incumbent_rounds),
                    timedOut, tested_moves, out.notes,
                    "start_" + std::to_string(s));
            considerRoutes(improved, "local_search_start_" + std::to_string(s));
        }
        out.route_states += tested_moves;
        std::ostringstream note;
        note << "BPC-owned local search summary: starts=" << max_starts
             << ", tested_moves=" << tested_moves;
        out.notes.push_back(note.str());
    }

    if (wants_pricing && !timedOut()) {
        std::vector<std::vector<int>> y_refs;
        y_refs.push_back(instance.initial);
        if (out.found && !out.verification.final_inventory.empty()) {
            y_refs.push_back(out.verification.final_inventory);
        }
        const std::vector<double> travel_costs{0.0, 1e-6, 1e-5, 3e-5, 1e-4};
        int rounds = 0;
        for (const std::vector<int>& y_ref : y_refs) {
            for (double travel_cost : travel_costs) {
                if (timedOut() || rounds >= opt.bpc_incumbent_rounds) break;
                ebrp::PricingDuals duals =
                    buildObjectiveGradientDuals(instance, y_ref, opt.lambda, travel_cost);
                std::vector<int> allowed_masks;
                const int top6 = topGradientStationMask(duals, instance.V, std::min(6, instance.V));
                const int top8 = topGradientStationMask(duals, instance.V, std::min(8, instance.V));
                if (top6 != 0) allowed_masks.push_back(top6);
                if (top8 != 0 && top8 != top6) allowed_masks.push_back(top8);
                allowed_masks.push_back(0);
                for (int allowed_mask : allowed_masks) {
                    if (timedOut()) break;
                    for (int k = 0; k < instance.M && !timedOut(); ++k) {
                        ebrp::PricingOptions pricing_opt;
                        pricing_opt.time_limit_seconds = gen_limit;
                        pricing_opt.max_returned_columns =
                            (mode == "pool" || mode == "portfolio" || mode == "strong")
                            ? 8 : 1;
                        pricing_opt.use_completion_lb_pruning = true;
                        pricing_opt.allowed_station_mask = allowed_mask;
                        pricing_opt.support_duration_pruning =
                            opt.support_duration_pruning;
                        pricing_opt.support_duration_max_subset_size =
                            opt.support_duration_max_subset_size;
                        ebrp::PricingResult priced = ebrp::priceRouteLoadColumnExact(
                            instance, k, duals, pricing_opt, gen_start);
                        ++out.pricing_calls;
                        out.generated_columns += priced.generated_columns;
                        out.route_states += priced.route_states;
                        out.operation_states += priced.operation_states;
                        if (priced.has_column) {
                            addIncumbentColumn(pool, seen, priced.best_column);
                        }
                        for (const ebrp::RouteLoadColumn& column : priced.negative_columns) {
                            addIncumbentColumn(pool, seen, column);
                        }
                        std::ostringstream note;
                        note << "BPC-owned pricing incumbent round=" << rounds
                             << ", vehicle=" << k
                             << ", allowed_mask=" << allowed_mask
                             << ", complete=" << (priced.complete ? "true" : "false")
                             << ", has_column=" << (priced.has_column ? "true" : "false")
                             << ", returned_columns="
                             << (priced.negative_columns.empty()
                                 ? (priced.has_column ? 1 : 0)
                                 : static_cast<int>(priced.negative_columns.size()))
                             << ", best_score=" << priced.best_reduced_cost
                             << ", generated_columns=" << priced.generated_columns;
                        out.notes.push_back(note.str());
                    }
                }
                ++rounds;
            }
        }
    }

    if (opt.column_dominance) {
        ebrp::ColumnDominanceOptions dominance_options;
        dominance_options.enabled = true;
        dominance_options.mode = ebrp::parseColumnDominanceMode(opt.column_dominance_mode);
        dominance_options.exact_safe = true;
        dominance_options = ebrp::normalizeColumnDominanceOptions(dominance_options);
        for (auto& cols : pool) {
            ebrp::ColumnDominanceStats stats;
            ebrp::applyColumnDominance(cols, dominance_options, stats);
            out.columns_generated_raw += stats.columns_generated_raw;
            out.columns_after_dominance += stats.columns_after_dominance;
            out.columns_dominated += stats.columns_dominated;
            out.dominance_time_seconds += stats.dominance_time_seconds;
        }
        out.notes.push_back("BPC-owned route-column incumbent pool dominance applied: mode="
            + opt.column_dominance_mode
            + ", columns_dominated=" + std::to_string(out.columns_dominated));
    }

    std::vector<int> selected(instance.M, -1);
    std::vector<int> y = instance.initial;
    std::vector<ebrp::RoutePlan> best_routes = out.found ? out.routes : emptyRouteSet(instance);
    ebrp::Verification best_verification = out.found
        ? out.verification : ebrp::verifySolution(instance, best_routes, opt.lambda);
    const int full_mask = (instance.V < 31) ? ((1 << instance.V) - 1) : 0;

    std::function<void(int, int)> dfs = [&](int vehicle, int used_mask) {
        ++out.master_states;
        if (vehicle == instance.M) {
            std::vector<ebrp::RoutePlan> routes = emptyRouteSet(instance);
            for (int k = 0; k < instance.M; ++k) {
                if (selected[k] >= 0) routes[k] = routeFromColumn(pool[k][selected[k]]);
            }
            ebrp::Verification v = ebrp::verifySolution(instance, routes, opt.lambda);
            if (v.feasible && (!best_verification.feasible ||
                               v.objective < best_verification.objective - 1e-10)) {
                best_verification = v;
                best_routes = std::move(routes);
            }
            return;
        }

        selected[vehicle] = -1;
        dfs(vehicle + 1, used_mask);
        for (int c = 0; c < static_cast<int>(pool[vehicle].size()); ++c) {
            const ebrp::RouteLoadColumn& col = pool[vehicle][c];
            if (static_cast<int>(col.q.size()) <= instance.V) continue;
            if ((col.mask & used_mask) != 0) continue;
            if (full_mask != 0 && (col.mask & ~full_mask) != 0) continue;
            bool ok = true;
            for (int i = 1; i <= instance.V; ++i) {
                y[i] -= col.q[i];
                if (y[i] < 0 || y[i] > instance.capacity[i]) ok = false;
            }
            if (ok) {
                selected[vehicle] = c;
                dfs(vehicle + 1, used_mask | col.mask);
            }
            for (int i = 1; i <= instance.V; ++i) y[i] += col.q[i];
            selected[vehicle] = -1;
        }
    };
    dfs(0, 0);

    if (best_verification.feasible) {
        out.found = true;
        out.verification = best_verification;
        out.routes = best_routes;
    }

    std::ostringstream summary;
    summary << "BPC-owned incumbent generator summary: mode=" << mode
            << ", found=" << (out.found ? "true" : "false")
            << ", objective=" << (out.found ? out.verification.objective : 0.0)
            << ", G=" << (out.found ? out.verification.G : 0.0)
            << ", P=" << (out.found ? out.verification.P : 0.0)
            << ", pool_columns=";
    long long pool_count = 0;
    for (const auto& cols : pool) pool_count += static_cast<long long>(cols.size());
    summary << pool_count
            << ", pricing_calls=" << out.pricing_calls
            << ", pricing_generated_columns=" << out.generated_columns
            << ", master_states=" << out.master_states
            << ", runtime=" << std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - gen_start).count();
    out.notes.push_back(summary.str());
    (void)frontier_start;
    return out;
}

bool makeTwoPickupColumn(const ebrp::Instance& instance,
                         int vehicle,
                         int first,
                         int second,
                         ebrp::RouteLoadColumn& column);

ebrp::SolveResult solveBranchPricingDiagnostic(const ebrp::Instance& instance,
                                               const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pricing-branch";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Restricted pricing diagnostic enforces Ryan-Foster together=0 and together=1 child-node rules.");

    int first = 0;
    int second = 0;
    ebrp::RouteLoadColumn pair_column;
    for (int a = 1; a <= instance.V && first == 0; ++a) {
        for (int b = a + 1; b <= instance.V && first == 0; ++b) {
            if (makeTwoPickupColumn(instance, 0, a, b, pair_column)) {
                first = a;
                second = b;
            }
        }
    }

    if (first == 0) {
        result.status = "restricted_pricing_infeasible";
        result.certificate = "diagnostic could not find a feasible two-station branch pair";
        result.runtime_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        return result;
    }

    ebrp::PricingDuals duals;
    duals.travel_cost = 1.0;
    duals.pickup_cost = instance.pickup_time + instance.drop_time;
    duals.visit_cost.assign(instance.V + 1, 100000.0);
    duals.visit_cost[first] = 0.0;
    duals.visit_cost[second] = 0.0;

    ebrp::PricingOptions require_options;
    require_options.time_limit_seconds = opt.solve_time_limit;
    require_options.require_together_pairs.push_back({first, second});
    ebrp::PricingOptions forbid_options;
    forbid_options.time_limit_seconds = opt.solve_time_limit;
    forbid_options.forbid_together_pairs.push_back({first, second});

    ebrp::PricingResult require_result = ebrp::priceRouteLoadColumnExact(
        instance, 0, duals, require_options, start);
    ebrp::PricingResult forbid_result = ebrp::priceRouteLoadColumnExact(
        instance, 0, duals, forbid_options, start);

    result.pricing_calls = 2;
    result.nodes = require_result.route_states + require_result.operation_states
        + forbid_result.route_states + forbid_result.operation_states;
    result.columns = require_result.generated_columns + forbid_result.generated_columns;

    const bool require_ok = require_result.complete && require_result.has_column &&
        columnContainsBoth(require_result.best_column, first, second);
    const bool forbid_ok = forbid_result.complete && forbid_result.has_column &&
        !columnContainsBoth(forbid_result.best_column, first, second);
    const bool forbid_exactly_one = forbid_result.has_column &&
        columnContainsExactlyOne(forbid_result.best_column, first, second);

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    if (require_result.has_column) {
        routes[require_result.best_column.vehicle] = routeFromColumn(require_result.best_column);
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    if (require_result.has_column && forbid_result.has_column) {
        result.lower_bound = std::min(require_result.best_reduced_cost, forbid_result.best_reduced_cost);
        result.upper_bound = std::max(require_result.best_reduced_cost, forbid_result.best_reduced_cost);
    }

    std::ostringstream pair_note;
    pair_note << "branch pair=(" << first << "," << second << ")";
    result.notes.push_back(pair_note.str());
    std::ostringstream require_note;
    require_note << "require_together complete=" << (require_result.complete ? "true" : "false")
                 << ", has_column=" << (require_result.has_column ? "true" : "false")
                 << ", contains_both=" << (require_ok ? "true" : "false")
                 << ", best_reduced_cost=" << require_result.best_reduced_cost
                 << ", generated_columns=" << require_result.generated_columns;
    result.notes.push_back(require_note.str());
    std::ostringstream forbid_note;
    forbid_note << "forbid_together complete=" << (forbid_result.complete ? "true" : "false")
                << ", has_column=" << (forbid_result.has_column ? "true" : "false")
                << ", contains_both=" << (forbid_result.has_column && columnContainsBoth(forbid_result.best_column, first, second) ? "true" : "false")
                << ", contains_exactly_one=" << (forbid_exactly_one ? "true" : "false")
                << ", best_reduced_cost=" << forbid_result.best_reduced_cost
                << ", generated_columns=" << forbid_result.generated_columns;
    result.notes.push_back(forbid_note.str());

    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    if (require_ok && forbid_ok && result.verification.feasible) {
        result.status = "restricted_pricing_complete";
        result.certificate = "exact pricing completed under both Ryan-Foster child restrictions; require branch produced a column containing both stations and forbid branch produced a column not containing both";
    } else {
        result.status = "restricted_pricing_failed";
        result.certificate = "restricted pricing diagnostic failed one or more child-node checks";
    }
    return result;
}

bool makeTwoPickupColumn(const ebrp::Instance& instance,
                         int vehicle,
                         int first,
                         int second,
                         ebrp::RouteLoadColumn& column) {
    if (vehicle < 0 || vehicle >= instance.M) return false;
    if (first == second || first <= 0 || second <= 0 ||
        first > instance.V || second > instance.V) {
        return false;
    }
    if (instance.Q[vehicle] < 2) return false;
    if (instance.initial[first] <= 0 || instance.initial[second] <= 0) return false;
    const double travel = instance.dist[0][first] + instance.dist[first][second]
        + instance.dist[second][0];
    const int pickup = 2;
    const double duration = travel + (instance.pickup_time + instance.drop_time) * pickup;
    if (duration > instance.total_time_limit + 1e-9) return false;

    column = ebrp::RouteLoadColumn{};
    column.vehicle = vehicle;
    column.mask = (1 << (first - 1)) | (1 << (second - 1));
    column.path = {first, second};
    column.q.assign(instance.V + 1, 0);
    column.q[first] = 1;
    column.q[second] = 1;
    column.pickup = pickup;
    column.travel = travel;
    column.duration = duration;
    column.reduced_cost = duration;
    return true;
}

ebrp::SolveResult solveCutsDiagnostic(const ebrp::Instance& instance,
                                      const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "cuts";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("3-subset-row cut diagnostic builds a feasible fractional pair-column triangle with z=0.5 on each pair.");

    std::array<int, 3> triple{0, 0, 0};
    std::vector<ebrp::RouteLoadColumn> columns;
    for (int a = 1; a <= instance.V && columns.empty(); ++a) {
        for (int b = a + 1; b <= instance.V && columns.empty(); ++b) {
            for (int c = b + 1; c <= instance.V && columns.empty(); ++c) {
                ebrp::RouteLoadColumn ab, ac, bc;
                if (makeTwoPickupColumn(instance, 0, a, b, ab) &&
                    makeTwoPickupColumn(instance, 0, a, c, ac) &&
                    makeTwoPickupColumn(instance, 0, b, c, bc)) {
                    triple = {a, b, c};
                    columns = {ab, ac, bc};
                }
            }
        }
    }

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.lower_bound = result.objective;
    result.upper_bound = result.objective;

    if (columns.empty()) {
        result.status = "cuts_diagnostic_infeasible";
        result.certificate = "diagnostic could not build a feasible three-pair pickup-column triangle on this instance";
        result.runtime_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        return result;
    }

    const std::vector<double> z_values(columns.size(), 0.5);
    const std::vector<ebrp::ThreeSubsetRowCut> cuts =
        ebrp::separateThreeSubsetRowCuts(instance.V, columns, z_values, 1e-9, 10);
    result.columns = static_cast<long long>(columns.size());
    result.cuts_added = static_cast<long long>(cuts.size());
    result.nodes = static_cast<long long>(instance.V) * (instance.V - 1) * (instance.V - 2) / 6;
    result.status = cuts.empty() ? "cuts_diagnostic_no_violation" : "cuts_diagnostic_complete";
    result.certificate = cuts.empty()
        ? "3-subset-row separator completed but found no violated cut in diagnostic pool"
        : "3-subset-row separator found violated cuts in diagnostic fractional column pool; this is a separator test, not an EBRP optimality certificate";

    std::ostringstream tri_note;
    tri_note << "diagnostic triple=(" << triple[0] << "," << triple[1] << "," << triple[2]
             << "), fractional z=0.5 on pair columns, generated_columns=" << columns.size();
    result.notes.push_back(tri_note.str());
    for (int idx = 0; idx < static_cast<int>(cuts.size()); ++idx) {
        const auto& cut = cuts[idx];
        std::ostringstream note;
        note << "cut " << idx << " stations=(" << cut.stations[0] << ","
             << cut.stations[1] << "," << cut.stations[2] << ") lhs="
             << cut.lhs << " rhs=" << cut.rhs << " violation=" << cut.violation;
        result.notes.push_back(note.str());
    }

    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    return result;
}

ebrp::SolveResult solveBranchingDiagnostic(const ebrp::Instance& instance,
                                           const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "branching";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Ryan-Foster diagnostic builds feasible pair columns and selects a fractional co-route station pair.");

    std::vector<ebrp::RouteLoadColumn> columns;
    std::array<int, 3> triple{0, 0, 0};
    for (int a = 1; a <= instance.V && columns.empty(); ++a) {
        for (int b = a + 1; b <= instance.V && columns.empty(); ++b) {
            for (int c = b + 1; c <= instance.V && columns.empty(); ++c) {
                ebrp::RouteLoadColumn ab, ac;
                if (makeTwoPickupColumn(instance, 0, a, b, ab) &&
                    makeTwoPickupColumn(instance, 0, a, c, ac)) {
                    triple = {a, b, c};
                    columns = {ab, ac};
                }
            }
        }
    }

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.lower_bound = result.objective;
    result.upper_bound = result.objective;

    if (columns.empty()) {
        result.status = "branching_diagnostic_infeasible";
        result.certificate = "diagnostic could not build feasible pair columns on this instance";
        result.runtime_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        return result;
    }

    const std::vector<double> z_values(columns.size(), 0.5);
    const ebrp::RyanFosterBranchCandidate candidate =
        ebrp::findRyanFosterBranchCandidate(instance.V, columns, z_values, 1e-9);

    result.columns = static_cast<long long>(columns.size());
    result.nodes = static_cast<long long>(instance.V) * (instance.V - 1) / 2;
    if (!candidate.found) {
        result.status = "branching_diagnostic_no_candidate";
        result.certificate = "Ryan-Foster scanner completed but found no fractional co-route pair";
    } else {
        result.status = "branching_diagnostic_complete";
        result.certificate = "Ryan-Foster scanner found a fractional co-route pair; child branches are sum_together=0 and sum_together=1. This is a branching diagnostic, not an EBRP optimality certificate.";
        std::ostringstream note;
        note << "diagnostic triple=(" << triple[0] << "," << triple[1] << "," << triple[2]
             << "), z=0.5 on columns {" << triple[0] << "," << triple[1]
             << "} and {" << triple[0] << "," << triple[2] << "}";
        result.notes.push_back(note.str());
        std::ostringstream branch_note;
        branch_note << "candidate pair=(" << candidate.station_i << ","
                    << candidate.station_j << "), together_value="
                    << candidate.together_value << ", fractional_score="
                    << candidate.fractional_score << ", together_columns="
                    << candidate.together_column_indices.size()
                    << ", branches: together=0 / together=1";
        result.notes.push_back(branch_note.str());
    }
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    return result;
}

std::vector<std::vector<ebrp::RouteLoadColumn>> buildOneStopPickupPool(
    const ebrp::Instance& instance) {
    std::vector<std::vector<ebrp::RouteLoadColumn>> pool(instance.M);
    const double cunit = instance.pickup_time + instance.drop_time;
    for (int k = 0; k < instance.M; ++k) {
        for (int station = 1; station <= instance.V; ++station) {
            const double travel = instance.dist[0][station] + instance.dist[station][0];
            const int max_pickup = std::min({
                instance.initial[station],
                instance.Q[k],
                static_cast<int>(std::floor((instance.total_time_limit - travel) / cunit + 1e-9))
            });
            for (int pickup = 1; pickup <= max_pickup; ++pickup) {
                ebrp::RouteLoadColumn col;
                col.vehicle = k;
                col.mask = 1 << (station - 1);
                col.path = {station};
                col.q.assign(instance.V + 1, 0);
                col.q[station] = pickup;
                col.pickup = pickup;
                col.travel = travel;
                col.duration = travel + cunit * pickup;
                col.reduced_cost = col.duration;
                pool[k].push_back(std::move(col));
            }
        }
    }
    return pool;
}

ebrp::SolveResult solveMasterDiagnostic(const ebrp::Instance& instance,
                                        const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "master";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Restricted master diagnostic solves the exact integer set-packing master over all feasible one-stop pickup columns.");

    std::vector<std::vector<ebrp::RouteLoadColumn>> pool = buildOneStopPickupPool(instance);
    for (int k = 0; k < instance.M; ++k) {
        result.columns += static_cast<long long>(pool[k].size());
        std::ostringstream note;
        note << "vehicle " << k << " one_stop_pickup_columns=" << pool[k].size();
        result.notes.push_back(note.str());
    }

    ebrp::RestrictedMasterResult master = ebrp::solveRestrictedMasterExact(
        instance, pool, opt.lambda, opt.solve_time_limit, start);
    result.nodes = master.states_processed;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    if (!master.complete) {
        result.status = "time_limit";
        result.certificate = "not certified; restricted one-stop column master did not finish";
        return result;
    }
    if (!master.has_solution) {
        result.status = "infeasible";
        result.certificate = "restricted one-stop column master completed but found no state";
        return result;
    }

    result.routes = std::move(master.routes);
    result.final_inventory = master.best_final_inventory;
    result.G = master.best_parts.G;
    result.P = master.best_parts.P;
    result.objective = master.best_parts.objective;
    result.lower_bound = result.objective;
    result.upper_bound = result.objective;
    result.gap = 0.0;
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.status = result.verification.feasible ? "restricted_master_complete" : "verification_failed";
    result.certificate = result.verification.feasible
        ? "exact integer restricted master solved over the supplied one-stop pickup column pool; this is a pool-optimal certificate, not a full-column global EBRP certificate"
        : "restricted master selected routes failed independent verification";
    std::ostringstream chosen;
    chosen << "selected_columns_by_vehicle=";
    for (int k = 0; k < static_cast<int>(master.selected_column_by_vehicle.size()); ++k) {
        if (k) chosen << ",";
        chosen << master.selected_column_by_vehicle[k];
    }
    result.notes.push_back(chosen.str());
    return result;
}

ebrp::SolveResult solveColumnGenerationDiagnostic(const ebrp::Instance& instance,
                                                  const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "cg";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Column-generation diagnostic solves a simple required-pair coverage LP, extracts CPLEX duals, and calls exact route-load pricing.");

    ebrp::ColumnGenerationResult cg = ebrp::runCoverageColumnGenerationDiagnostic(
        instance, opt.solve_time_limit, 8);
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.columns = cg.generated_columns;
    result.pricing_calls = cg.pricing_calls;
    result.nodes = cg.route_states + cg.operation_states;
    result.support_duration_cuts_generated = cg.support_duration_cuts_generated;
    result.support_duration_pruned_labels = cg.support_duration_pruned_labels;
    result.support_duration_pruned_columns = cg.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated =
        cg.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels =
        cg.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns =
        cg.support_duration_strong_pruned_columns;
    result.support_duration_max_subset_size = cg.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        cg.support_duration_precompute_time_seconds;
    result.objective = cg.lp_objective;
    result.lower_bound = cg.lp_objective;
    result.upper_bound = cg.lp_objective;
    result.gap = 0.0;
    result.notes.insert(result.notes.end(), cg.notes.begin(), cg.notes.end());
    std::ostringstream summary;
    summary << "required_pair=(" << cg.required_i << "," << cg.required_j
            << "), iterations=" << cg.iterations
            << ", best_pricing_reduced_cost=" << cg.best_pricing_reduced_cost;
    result.notes.push_back(summary.str());

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;

    if (cg.complete) {
        result.status = "cg_root_complete";
        result.certificate = "coverage LP column-generation diagnostic closed: CPLEX solved each restricted LP and exact pricing found no negative reduced-cost route-load column for the diagnostic coverage model. This is not an EBRP optimality certificate.";
    } else {
        result.status = "cg_not_closed";
        result.certificate = "coverage LP column-generation diagnostic did not close";
    }
    return result;
}

ebrp::SolveResult solveGiniCapColumnGenerationDiagnostic(const ebrp::Instance& instance,
                                                         const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gcap-cg";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Fixed-Gini-cap EBRP column-generation diagnostic solves the continuous root master with inventory, ratios, satisfaction penalty, pairwise Gini numerator rows, and H <= V*gamma*S.");

    std::vector<int> initial_inventory = instance.initial;
    const ebrp::ObjectiveParts initial_parts =
        ebrp::computeObjectiveParts(instance, initial_inventory, opt.lambda);
    double gamma = opt.gini_cap;
    if (gamma < 0.0) {
        gamma = initial_parts.G + 1e-9;
        std::ostringstream note;
        note << "no --gini-cap supplied; using empty-solution gamma="
             << gamma << " from initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    } else {
        std::ostringstream note;
        note << "using supplied gamma=" << gamma
             << "; empty-solution initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    }

    ebrp::GiniCapColumnGenerationResult cg =
        ebrp::runGiniCapColumnGenerationDiagnostic(
            instance, opt.lambda, gamma, opt.solve_time_limit, 12,
            opt.support_duration_pruning, opt.support_duration_max_subset_size);

    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.columns = cg.generated_columns;
    result.pricing_calls = cg.pricing_calls;
    result.nodes = cg.route_states + cg.operation_states;
    result.columns_generated_raw = cg.columns_generated_raw;
    result.columns_after_dominance = cg.columns_after_dominance;
    result.columns_dominated = cg.columns_dominated;
    result.pricing_columns_enumerated = cg.pricing_columns_enumerated;
    result.dominance_input_columns = cg.dominance_input_columns;
    result.dominance_kept_columns = cg.dominance_kept_columns;
    result.dominance_removed_columns = cg.dominance_removed_columns;
    result.dominance_removed_existing_projection =
        cg.dominance_removed_existing_projection;
    result.dominance_removed_candidate_projection =
        cg.dominance_removed_candidate_projection;
    result.rmp_columns_inserted = cg.rmp_columns_inserted;
    result.rmp_columns_active = cg.rmp_columns_active;
    result.dominance_time_seconds = cg.dominance_time_seconds;
    result.dominance_mode = cg.dominance_mode;
    result.dominance_exact_safe = cg.dominance_exact_safe;
    result.pricing_negative_columns_found = cg.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted = cg.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated = cg.pricing_negative_columns_dominated;
    result.pricing_completed_exactly = cg.pricing_completed_exactly;
    result.pricing_best_reduced_cost_any = cg.pricing_best_reduced_cost_any;
    result.pricing_best_new_reduced_cost = cg.pricing_best_new_reduced_cost;
    result.pricing_duplicate_negative_projections =
        cg.pricing_duplicate_negative_projections;
    result.pricing_new_negative_projections = cg.pricing_new_negative_projections;
    result.pricing_blocked_by_duplicate_projection =
        cg.pricing_blocked_by_duplicate_projection;
    result.pricing_closure_certified_exact = cg.pricing_closure_certified_exact;
    result.support_duration_cuts_generated = cg.support_duration_cuts_generated;
    result.support_duration_pruned_labels = cg.support_duration_pruned_labels;
    result.support_duration_pruned_columns = cg.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated =
        cg.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels =
        cg.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns =
        cg.support_duration_strong_pruned_columns;
    result.support_duration_max_subset_size = cg.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        cg.support_duration_precompute_time_seconds;
    result.lower_bound = cg.complete ? cg.fixed_cap_surrogate : std::max(0.0, gamma);
    result.upper_bound = cg.fixed_cap_surrogate;
    result.gap = 0.0;
    result.notes.insert(result.notes.end(), cg.notes.begin(), cg.notes.end());
    std::ostringstream summary;
    summary << "gamma=" << cg.gamma
            << ", iterations=" << cg.iterations
            << ", lp_lambda_penalty=" << cg.lp_lambda_penalty
            << ", gamma_plus_lambda_penalty=" << cg.fixed_cap_surrogate
            << ", best_pricing_reduced_cost=" << cg.best_pricing_reduced_cost;
    result.notes.push_back(summary.str());

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;

    if (cg.complete) {
        result.gap = 0.0;
        result.status = "gcap_cg_root_complete";
        result.certificate = "fixed-Gini-cap continuous root LP closed: CPLEX solved each restricted master and exact route-load pricing found no negative reduced-cost column. This is an LP relaxation certificate for the fixed-cap master, not an integer EBRP optimality certificate.";
    } else {
        result.gap = (std::fabs(result.upper_bound) > 1e-12)
            ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
            : 1.0;
        result.status = "gcap_cg_not_closed";
        result.certificate = "fixed-Gini-cap root column generation did not close; do not treat this as an optimality certificate";
    }
    return result;
}

ebrp::SolveResult solveGiniCapBranchProbeDiagnostic(const ebrp::Instance& instance,
                                                    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gcap-branch";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Fixed-Gini-cap Ryan-Foster branch probe closes the root LP, selects one fractional co-route pair, and attempts to close both child root LPs.");

    const ebrp::ObjectiveParts initial_parts =
        ebrp::computeObjectiveParts(instance, instance.initial, opt.lambda);
    double gamma = opt.gini_cap;
    if (gamma < 0.0) {
        gamma = initial_parts.G + 1e-9;
        std::ostringstream note;
        note << "no --gini-cap supplied; using empty-solution gamma="
             << gamma << " from initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    } else {
        std::ostringstream note;
        note << "using supplied gamma=" << gamma
             << "; empty-solution initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    }

    ebrp::GiniCapBranchProbeResult probe =
        ebrp::runGiniCapRyanFosterBranchProbe(
            instance, opt.lambda, gamma, opt.solve_time_limit, 12,
            opt.support_duration_pruning, opt.support_duration_max_subset_size);
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.columns = probe.generated_columns;
    result.pricing_calls = probe.pricing_calls;
    result.nodes = probe.route_states + probe.operation_states;
    result.columns_generated_raw = probe.columns_generated_raw;
    result.columns_after_dominance = probe.columns_after_dominance;
    result.columns_dominated = probe.columns_dominated;
    result.dominance_time_seconds = probe.dominance_time_seconds;
    result.dominance_mode = probe.dominance_mode;
    result.dominance_exact_safe = probe.dominance_exact_safe;
    result.pricing_negative_columns_found = probe.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted = probe.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated = probe.pricing_negative_columns_dominated;
    result.pricing_completed_exactly = probe.pricing_completed_exactly;
    result.support_duration_cuts_generated = probe.support_duration_cuts_generated;
    result.support_duration_pruned_labels = probe.support_duration_pruned_labels;
    result.support_duration_pruned_columns = probe.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated =
        probe.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels =
        probe.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns =
        probe.support_duration_strong_pruned_columns;
    result.support_duration_max_subset_size = probe.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        probe.support_duration_precompute_time_seconds;
    result.lower_bound = probe.root_bound;
    if (probe.forbid_child_complete && probe.require_child_complete) {
        result.lower_bound = std::min(probe.forbid_child_bound, probe.require_child_bound);
    }
    result.notes.insert(result.notes.end(), probe.notes.begin(), probe.notes.end());
    std::ostringstream summary;
    summary << "root_complete=" << (probe.root_complete ? "true" : "false")
            << ", branch_pair=(" << probe.station_i << "," << probe.station_j << ")"
            << ", together_value=" << probe.together_value
            << ", forbid_child_complete=" << (probe.forbid_child_complete ? "true" : "false")
            << ", require_child_complete=" << (probe.require_child_complete ? "true" : "false")
            << ", root_bound=" << probe.root_bound
            << ", forbid_bound=" << probe.forbid_child_bound
            << ", require_bound=" << probe.require_child_bound;
    result.notes.push_back(summary.str());

    std::vector<ebrp::RoutePlan> routes(instance.M);
    for (int k = 0; k < instance.M; ++k) {
        routes[k].vehicle = k;
        routes[k].nodes = {0, 0};
    }
    result.routes = std::move(routes);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.gap = (std::fabs(result.upper_bound) > 1e-12)
        ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
        : 1.0;

    if (probe.complete) {
        result.status = "gcap_branch_probe_complete";
        result.certificate = "one-level fixed-Gini-cap Ryan-Foster branch probe closed root and both child LP/pricing relaxations. This is not a full integer branch-price tree certificate.";
    } else {
        result.status = "gcap_branch_probe_not_closed";
        result.certificate = "one-level fixed-Gini-cap Ryan-Foster branch probe did not close root and both child LP/pricing relaxations";
    }
    return result;
}

ebrp::SolveResult solveGiniCapTreeDiagnostic(const ebrp::Instance& instance,
                                             const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gcap-tree";
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back(opt.gini_floor >= 0.0
        ? "Fixed-Gini-interval branch-price tree diagnostic runs an open-node Ryan-Foster tree with exact pricing at each solved node. Reported lower bound is the valid interval metric gamma_floor+lambda*P."
        : "Fixed-Gini-cap branch-price tree diagnostic runs an open-node Ryan-Foster tree with exact pricing at each solved node. Reported lower bound is for the fixed-cap surrogate gamma+lambda*P.");

    const ebrp::ObjectiveParts initial_parts =
        ebrp::computeObjectiveParts(instance, instance.initial, opt.lambda);
    double gamma = opt.gini_cap;
    if (gamma < 0.0) {
        gamma = initial_parts.G + 1e-9;
        std::ostringstream note;
        note << "no --gini-cap supplied; using empty-solution gamma="
             << gamma << " from initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    } else {
        std::ostringstream note;
        note << "using supplied gamma=" << gamma
             << "; empty-solution initial G=" << initial_parts.G;
        result.notes.push_back(note.str());
    }
    if (opt.gini_floor >= 0.0) {
        std::ostringstream note;
        note << "using supplied gini floor=" << opt.gini_floor
             << "; interval lower-bound metric is floor+lambda*P";
        result.notes.push_back(note.str());
        if (opt.gini_floor > gamma + 1e-12) {
            result.status = "invalid_gini_interval";
            result.certificate = "--gini-floor must be <= --gini-cap";
            result.runtime_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - start).count();
            return result;
        }
    }

    std::vector<ebrp::RoutePlan> seed_routes;
    if (opt.gcap_seed_cplex) {
        ebrp::SolveOptions seed_opt = opt;
        seed_opt.method = "cplex";
        seed_opt.plain_baseline = false;
        seed_opt.out_path.clear();
        if (!seed_opt.log_path.empty()) seed_opt.log_path += ".gcap_seed_cplex.log";
        ebrp::SolveResult seed = ebrp::solveCplexBaseline(instance, seed_opt);
        std::ostringstream seed_note;
        seed_note << "gcap CPLEX seed status=" << seed.status
                  << ", objective=" << seed.objective
                  << ", G=" << seed.G
                  << ", P=" << seed.P
                  << ", runtime=" << seed.runtime_seconds;
        result.notes.push_back(seed_note.str());
        if (seed.verification.feasible &&
            seed.G <= gamma + 1e-9 &&
            (opt.gini_floor < 0.0 || seed.G >= opt.gini_floor - 1e-9)) {
            seed_routes = seed.routes;
            result.notes.push_back("using CPLEX seed routes as fixed-cap branch-price warm start");
        } else {
            result.notes.push_back("CPLEX seed routes were not feasible for the supplied fixed Gini cap");
        }
    }

    ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
        instance, opt.lambda, gamma, opt.gini_floor, opt.solve_time_limit, 24, opt.max_branch_nodes,
        seed_routes.empty() ? nullptr : &seed_routes, false,
        std::numeric_limits<double>::infinity(), opt.gcap_warmstart_level,
        std::numeric_limits<double>::infinity(), opt.gcap_pricing_columns,
        opt.column_dominance, opt.column_dominance_mode,
        opt.projection_bound, opt.penalty_domain_tightening,
        opt.movement_domain_tightening, opt.support_duration_pruning,
        opt.support_duration_max_subset_size);
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.columns = tree.generated_columns;
    result.pricing_calls = tree.pricing_calls;
    result.nodes = tree.nodes_solved;
    result.pricing_time_seconds = tree.pricing_time_seconds;
    result.master_time_seconds = tree.master_time_seconds;
    result.columns_generated_raw = tree.columns_generated_raw;
    result.columns_after_dominance = tree.columns_after_dominance;
    result.columns_dominated = tree.columns_dominated;
    result.pricing_columns_enumerated = tree.pricing_columns_enumerated;
    result.dominance_input_columns = tree.dominance_input_columns;
    result.dominance_kept_columns = tree.dominance_kept_columns;
    result.dominance_removed_columns = tree.dominance_removed_columns;
    result.dominance_removed_existing_projection =
        tree.dominance_removed_existing_projection;
    result.dominance_removed_candidate_projection =
        tree.dominance_removed_candidate_projection;
    result.rmp_columns_inserted = tree.rmp_columns_inserted;
    result.rmp_columns_active = tree.rmp_columns_active;
    result.dominance_time_seconds = tree.dominance_time_seconds;
    result.dominance_mode = tree.dominance_mode;
    result.dominance_exact_safe = tree.dominance_exact_safe;
    result.pricing_negative_columns_found = tree.pricing_negative_columns_found;
    result.pricing_negative_columns_inserted = tree.pricing_negative_columns_inserted;
    result.pricing_negative_columns_dominated = tree.pricing_negative_columns_dominated;
    result.pricing_completed_exactly = tree.pricing_completed_exactly;
    result.pricing_best_reduced_cost_any = tree.pricing_best_reduced_cost_any;
    result.pricing_best_new_reduced_cost = tree.pricing_best_new_reduced_cost;
    result.pricing_duplicate_negative_projections =
        tree.pricing_duplicate_negative_projections;
    result.pricing_new_negative_projections = tree.pricing_new_negative_projections;
    result.pricing_blocked_by_duplicate_projection =
        tree.pricing_blocked_by_duplicate_projection;
    result.pricing_closure_certified_exact = tree.pricing_closure_certified_exact;
    result.support_duration_cuts_generated = tree.support_duration_cuts_generated;
    result.support_duration_pruned_labels = tree.support_duration_pruned_labels;
    result.support_duration_pruned_columns = tree.support_duration_pruned_columns;
    result.support_duration_strong_cuts_generated =
        tree.support_duration_strong_cuts_generated;
    result.support_duration_strong_pruned_labels =
        tree.support_duration_strong_pruned_labels;
    result.support_duration_strong_pruned_columns =
        tree.support_duration_strong_pruned_columns;
    result.support_duration_max_subset_size = tree.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        tree.support_duration_precompute_time_seconds;
    result.projection_bound_prunes = tree.projection_bound_prunes;
    result.projection_bound_time_seconds = tree.projection_bound_time_seconds;
    result.projection_bound_best_value = tree.projection_bound_best_value;
    result.projection_bound_scope = tree.projection_bound_scope;
    result.penalty_budget = tree.penalty_budget;
    result.domains_tightened_count = tree.domains_tightened_count;
    result.total_domain_width_before = tree.total_domain_width_before;
    result.total_domain_width_after = tree.total_domain_width_after;
    result.penalty_tightening_time_seconds = tree.penalty_tightening_time_seconds;
    result.movement_domains_tightened_count = tree.movement_domains_tightened_count;
    result.movement_domain_width_before = tree.movement_domain_width_before;
    result.movement_domain_width_after = tree.movement_domain_width_after;
    result.movement_tightening_time_seconds = tree.movement_tightening_time_seconds;
    result.movement_unreachable_station_count = tree.movement_unreachable_station_count;
    result.pricing_closed_nodes = tree.nodes_solved -
        (tree.complete ? 0 : std::min(1, tree.nodes_solved));
    result.open_nodes = tree.open_nodes;
    result.cuts_added = tree.cuts_added;
    result.lower_bound = (opt.gini_floor >= 0.0)
        ? std::max(opt.gini_floor, tree.global_lower_bound)
        : tree.global_lower_bound;
    result.notes.insert(result.notes.end(), tree.notes.begin(), tree.notes.end());
    std::ostringstream summary;
    summary << "tree_complete=" << (tree.complete ? "true" : "false")
            << ", nodes_solved=" << tree.nodes_solved
            << ", branched_nodes=" << tree.branched_nodes
            << ", pruned_by_bound=" << tree.pruned_by_bound
            << ", integer_leaves=" << tree.integer_leaves
            << ", projected_leaves=" << tree.projected_leaves
            << ", cuts_added=" << tree.cuts_added
            << ", open_nodes=" << tree.open_nodes
            << ", max_depth=" << tree.max_depth
            << ", lower_bound_valid=" << (tree.lower_bound_valid ? "true" : "false")
            << ", has_integer_incumbent=" << (tree.has_integer_incumbent ? "true" : "false")
            << ", global_lower_bound=" << tree.global_lower_bound
            << ", resource_objective_lb=" << tree.resource_objective_lower_bound
            << ", resource_penalty_lb=" << tree.resource_penalty_lower_bound
            << ", best_integer_surrogate=" << tree.best_integer_surrogate
            << ", best_integer_columns=" << tree.best_integer_columns
            << ", incumbent_source=" << tree.incumbent_source;
    result.notes.push_back(summary.str());
    std::ostringstream states;
    states << "pricing_route_states=" << tree.route_states
           << ", pricing_operation_states=" << tree.operation_states
           << "; nodes field reports branch-price tree nodes for this diagnostic";
    result.notes.push_back(states.str());

    if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
        result.routes = tree.best_routes;
    } else {
        std::vector<ebrp::RoutePlan> routes(instance.M);
        for (int k = 0; k < instance.M; ++k) {
            routes[k].vehicle = k;
            routes[k].nodes = {0, 0};
        }
        result.routes = std::move(routes);
        result.notes.push_back("no fixed-cap route-integer incumbent was available; reported routes are the empty-route placeholder for verifier completeness.");
    }
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = tree.has_integer_incumbent ? tree.best_integer_surrogate : 0.0;
    result.gap = (std::isfinite(result.upper_bound) && std::fabs(result.upper_bound) > 1e-12)
        ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
        : 1.0;
    result.notes.push_back(opt.gini_floor >= 0.0
        ? "objective/G/P are independently verified for the reconstructed routes; lower_bound includes the valid interval floor G>=gamma_floor and any branch-price bound. It is still an interval lower-bound metric, not a full EBRP objective certificate by itself."
        : "objective/G/P are independently verified for the reconstructed routes; lower_bound/upper_bound/gap are fixed-Gini-cap surrogate values, not full EBRP objective bounds.");

    if (tree.complete) {
        if (!tree.has_integer_incumbent) {
            if (opt.gini_floor >= 0.0) {
                result.status = "gcap_interval_bound_complete";
                result.certificate = "fixed-Gini-interval branch-price tree exhausted all open diagnostic nodes with exact pricing and produced a valid interval lower bound, but found no route-integer incumbent in the requested interval.";
            } else {
                result.status = "gcap_tree_fixed_cap_infeasible";
                result.certificate = "fixed-Gini-cap branch-price tree exhausted all open diagnostic nodes with exact pricing and found no route-integer solution satisfying the supplied cap.";
            }
        } else if (tree.projected_leaves > 0) {
            result.status = "gcap_tree_projected_complete";
            result.certificate = "fixed-Gini-cap branch-price diagnostic exhausted all open nodes with exact pricing, but at least one projected leaf could not be reconstructed as an integer route selection. This is not a full integer route certificate.";
        } else {
            result.status = "gcap_tree_complete";
            result.certificate = opt.gini_floor >= 0.0
                ? "fixed-Gini-interval branch-price tree exhausted all open diagnostic nodes with exact pricing and reconstructed route-integer incumbents. This certifies the interval lower-bound metric floor+lambda*P only; a full EBRP certificate requires covering all relevant gamma intervals."
                : "fixed-Gini-cap branch-price tree exhausted all open diagnostic nodes with exact pricing and reconstructed route-integer incumbents. This certifies the fixed-cap surrogate tree only, not the full EBRP objective over all gamma values.";
        }
    } else {
        result.status = tree.hit_time_limit ? "gcap_tree_time_limit" : "gcap_tree_not_closed";
        result.certificate = "fixed-Gini-cap branch-price tree did not exhaust all open nodes; do not treat this as an optimality certificate";
    }
    return result;
}

ebrp::SolveResult solveDominanceDiagnostic(const ebrp::Instance& instance,
                                           const ebrp::SolveOptions& opt) {
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "dominance-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: tests column projection dominance and duplicate projection filtering counters";
    ebrp::ColumnDominanceOptions options;
    options.enabled = opt.column_dominance;
    options.mode = ebrp::parseColumnDominanceMode(opt.column_dominance_mode);
    options.exact_safe = true;
    options = ebrp::normalizeColumnDominanceOptions(options);
    result.dominance_mode = ebrp::columnDominanceModeName(options.mode);
    result.dominance_exact_safe = options.exact_safe;

    auto makeColumn = [&](int vehicle, int mask, std::vector<int> q,
                          std::vector<int> path, double duration,
                          double travel, double rc) {
        ebrp::RouteLoadColumn col;
        col.vehicle = vehicle;
        col.mask = mask;
        col.q.assign(instance.V + 1, 0);
        for (int i = 1; i <= instance.V && i < static_cast<int>(q.size()); ++i) {
            col.q[i] = q[i];
            if (q[i] > 0) col.pickup += q[i];
        }
        col.path = std::move(path);
        col.duration = duration;
        col.travel = travel;
        col.reduced_cost = rc;
        return col;
    };

    const int mask12 = (instance.V >= 2) ? 0x3 : 0x1;
    std::vector<int> q_same(instance.V + 1, 0);
    if (instance.V >= 1) q_same[1] = 1;
    if (instance.V >= 2) q_same[2] = -1;
    std::vector<int> q_diff = q_same;
    if (instance.V >= 1) q_diff[1] = 2;

    std::vector<ebrp::RouteLoadColumn> columns;
    columns.push_back(makeColumn(0, mask12, q_same, {1, 2}, 10.0, 8.0, -2.0));
    columns.push_back(makeColumn(0, mask12, q_same, {2, 1}, 12.0, 7.0, -3.0));
    columns.push_back(makeColumn(0, mask12, q_diff, {1, 2}, 9.0, 7.0, -1.0));
    columns.push_back(makeColumn(0, 0x1, q_same, {1}, 6.0, 4.0, -1.5));
    ebrp::ColumnDominanceStats stats;
    ebrp::applyColumnDominance(columns, options, stats);

    std::vector<ebrp::RouteLoadColumn> existing;
    existing.push_back(makeColumn(0, mask12, q_same, {1, 2}, 10.0, 8.0, -2.0));
    std::vector<ebrp::RouteLoadColumn> candidates;
    candidates.push_back(makeColumn(0, mask12, q_same, {2, 1}, 11.0, 7.0, -3.0));
    candidates.push_back(makeColumn(0, mask12, q_diff, {1, 2}, 8.0, 6.0, -4.0));
    ebrp::ColumnDominanceStats filter_stats;
    std::vector<ebrp::RouteLoadColumn> filtered =
        ebrp::filterNewColumnsByDominance(existing, std::move(candidates),
                                          options, filter_stats);

    result.columns_generated_raw = stats.columns_generated_raw +
        filter_stats.columns_generated_raw;
    result.columns_after_dominance = stats.columns_after_dominance +
        filter_stats.columns_after_dominance;
    result.columns_dominated = stats.columns_dominated + filter_stats.columns_dominated;
    result.dominance_input_columns = stats.dominance_input_columns +
        filter_stats.dominance_input_columns;
    result.dominance_kept_columns = stats.dominance_kept_columns +
        filter_stats.dominance_kept_columns;
    result.dominance_removed_columns = stats.dominance_removed_columns +
        filter_stats.dominance_removed_columns;
    result.dominance_removed_existing_projection =
        stats.dominance_removed_existing_projection +
        filter_stats.dominance_removed_existing_projection;
    result.dominance_removed_candidate_projection =
        stats.dominance_removed_candidate_projection +
        filter_stats.dominance_removed_candidate_projection;
    result.dominance_time_seconds = stats.dominance_time_seconds +
        filter_stats.dominance_time_seconds;
    result.pricing_negative_columns_found = 2;
    result.pricing_negative_columns_inserted =
        static_cast<long long>(filtered.size());
    result.pricing_duplicate_negative_projections =
        filter_stats.dominance_removed_existing_projection;
    result.pricing_new_negative_projections =
        static_cast<long long>(filtered.size());
    result.pricing_blocked_by_duplicate_projection = filtered.empty();
    result.pricing_closure_certified_exact = !filtered.empty();
    result.pricing_completed_exactly = !filtered.empty();
    result.notes.push_back("dominance diagnostic: exact duplicate input columns removed="
        + std::to_string(stats.dominance_removed_candidate_projection)
        + ", existing projection removals="
        + std::to_string(filter_stats.dominance_removed_existing_projection)
        + ", filtered_new_columns=" + std::to_string(filtered.size()));
    const bool ok = (stats.dominance_input_columns == 4 &&
                     stats.dominance_kept_columns == 3 &&
                     stats.dominance_removed_candidate_projection == 1 &&
                     filter_stats.dominance_removed_existing_projection == 1 &&
                     filtered.size() == 1);
    if (!ok) {
        result.status = "diagnostic_failed";
        result.certificate = "diagnostic failed: dominance/filtering counters did not match expected artificial pool behavior";
    }
    result.routes.assign(instance.M, {});
    for (int k = 0; k < instance.M; ++k) {
        result.routes[k].vehicle = k;
        result.routes[k].nodes = {0, 0};
    }
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.lower_bound = 0.0;
    result.upper_bound = result.objective;
    result.runtime_seconds = 0.0;
    result.wall_time_seconds = 0.0;
    return result;
}

ebrp::SolveResult solveSupportPruningDiagnostic(const ebrp::Instance& instance,
                                                const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::PricingDuals duals;
    duals.travel_cost = 1.0;
    duals.pickup_cost = instance.pickup_time + instance.drop_time;
    ebrp::PricingOptions pricing_opt;
    pricing_opt.time_limit_seconds = opt.solve_time_limit;
    pricing_opt.support_duration_pruning = true;
    pricing_opt.support_duration_max_subset_size =
        opt.support_duration_max_subset_size;

    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "support-pruning-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: support-duration pruning precomputes exact-safe impossible station supports for pricing";
    result.support_duration_max_subset_size =
        opt.support_duration_max_subset_size;
    for (int k = 0; k < instance.M; ++k) {
        ebrp::PricingResult priced = ebrp::priceRouteLoadColumnExact(
            instance, k, duals, pricing_opt, start);
        ++result.pricing_calls;
        result.nodes += priced.route_states + priced.operation_states;
        result.columns += priced.generated_columns;
        result.support_duration_cuts_generated +=
            priced.support_duration_cuts_generated;
        result.support_duration_pruned_labels +=
            priced.support_duration_pruned_labels;
        result.support_duration_pruned_columns +=
            priced.support_duration_pruned_columns;
        result.support_duration_strong_cuts_generated +=
            priced.support_duration_strong_cuts_generated;
        result.support_duration_strong_pruned_labels +=
            priced.support_duration_strong_pruned_labels;
        result.support_duration_strong_pruned_columns +=
            priced.support_duration_strong_pruned_columns;
        result.support_duration_precompute_time_seconds +=
            priced.support_duration_precompute_time_seconds;
        result.support_duration_max_subset_size =
            std::max(result.support_duration_max_subset_size,
                     priced.support_duration_max_subset_size);
        if (!priced.complete) result.status = "time_limit";
    }
    std::ostringstream note;
    note << "support-duration pruning diagnostic: cuts_generated="
         << result.support_duration_cuts_generated
         << ", strong_cuts_generated="
         << result.support_duration_strong_cuts_generated
         << ", pruned_labels=" << result.support_duration_pruned_labels
         << ", pruned_columns=" << result.support_duration_pruned_columns
         << ", max_subset_size=" << result.support_duration_max_subset_size;
    result.notes.push_back(note.str());
    {
        const int synthetic_v = 4;
        const double synthetic_route_limit = 180.0;
        const double synthetic_cunit = 120.0;
        int old_rule_cuts = 0;
        int strong_rule_cuts = 0;
        for (int mask = 1; mask < (1 << synthetic_v); ++mask) {
            int support_size = 0;
            int x = mask;
            while (x != 0) {
                x &= (x - 1);
                ++support_size;
            }
            if (support_size > 3) continue;
            const double cycle_lb = 0.0;
            if (cycle_lb + synthetic_cunit > synthetic_route_limit + 1e-9) {
                ++old_rule_cuts;
            }
            const int min_pickups = (support_size + 1) / 2;
            if (cycle_lb + synthetic_cunit * min_pickups >
                synthetic_route_limit + 1e-9) {
                ++strong_rule_cuts;
            }
        }
        std::ostringstream synthetic_note;
        synthetic_note << "synthetic ceil-half support diagnostic: V=4,"
                       << " route_limit=" << synthetic_route_limit
                       << ", operation_unit=" << synthetic_cunit
                       << ", max_subset_size=3"
                       << ", old_one_operation_cuts=" << old_rule_cuts
                       << ", strong_ceil_half_cuts=" << strong_rule_cuts
                       << "; expected old=0 and strong>0";
        result.notes.push_back(synthetic_note.str());
    }
    result.routes.assign(instance.M, {});
    for (int k = 0; k < instance.M; ++k) {
        result.routes[k].vehicle = k;
        result.routes[k].nodes = {0, 0};
    }
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.lower_bound = 0.0;
    result.upper_bound = result.objective;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveRouteMaskSupportDiagnostic(const ebrp::Instance& instance,
                                                  const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "route-mask-support-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: route-mask support-duration pruning removes route-mask relaxation variables that cannot represent any feasible route-load column";
    result.support_duration_min_pickup_rule = "ceil_half_support";
    result.route_mask_support_duration_pruning = true;

    const ebrp::GiniIntervalInventoryRelaxationBound disabled =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, std::max(0.01, opt.gini_cap >= 0.0 ? opt.gini_cap : 0.25)),
            std::max(0.1, std::min(1.0, opt.solve_time_limit > 0.0 ? opt.solve_time_limit : 1.0)),
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, false);
    const ebrp::GiniIntervalInventoryRelaxationBound enabled =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, std::max(0.01, opt.gini_cap >= 0.0 ? opt.gini_cap : 0.25)),
            std::max(0.1, std::min(1.0, opt.solve_time_limit > 0.0 ? opt.solve_time_limit : 1.0)),
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, true);

    result.route_mask_count_before_support_duration =
        enabled.route_mask_count_before_support_duration;
    result.route_mask_count_after_support_duration =
        enabled.route_mask_count_after_support_duration;
    result.route_masks_removed_by_support_duration =
        enabled.route_masks_removed_by_support_duration;
    result.route_mask_support_duration_precompute_time_seconds =
        enabled.route_mask_support_duration_precompute_time_seconds;
    result.route_mask_support_duration_max_removed_subset_size =
        enabled.route_mask_support_duration_max_removed_subset_size;
    result.bound_time_seconds = disabled.route_mask_support_duration_precompute_time_seconds +
        enabled.route_mask_support_duration_precompute_time_seconds;
    result.lower_bound = enabled.computed ? enabled.objective_lower_bound : 0.0;
    result.upper_bound = result.lower_bound;
    result.notes.push_back("route-mask support disabled note: " + disabled.note);
    result.notes.push_back("route-mask support enabled note: " + enabled.note);
    for (const std::string& example :
         enabled.route_mask_support_duration_removed_examples) {
        result.notes.push_back("route-mask support removed example: " + example);
    }
    result.notes.push_back("synthetic route-mask support diagnostic: with zero travel, route_limit=180, operation_unit=120, any 3-station support has old_one_operation_lb=120<=180 but strong_ceil_half_lb=240>180, so at least one mask is removed by the strengthened rule");
    result.routes.assign(instance.M, {});
    for (int k = 0; k < instance.M; ++k) {
        result.routes[k].vehicle = k;
        result.routes[k].nodes = {0, 0};
    }
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveIncumbentImportDiagnostic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "incumbent-import-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: imported incumbents are independently verified and used as upper bounds only";
    result.incumbent_import_attempted = !opt.incumbent_json_path.empty() ||
        !opt.hga_incumbent_path.empty();

    auto testPath = [&](const std::string& path,
                        const std::string& format,
                        const std::string& label) {
        if (path.empty()) return;
        try {
            std::vector<ebrp::RoutePlan> routes =
                loadIncumbentRoutesByFormat(path, format, instance.M);
            ebrp::Verification verification =
                ebrp::verifySolution(instance, routes, opt.lambda);
            if (verification.feasible && verification.objective_matches &&
                verification.errors.empty()) {
                result.incumbent_import_verified = true;
                result.incumbent_import_objective = verification.objective;
                result.incumbent_import_G = verification.G;
                result.incumbent_import_P = verification.P;
                result.routes = routes;
                result.verification = verification;
                result.final_inventory = verification.final_inventory;
                result.G = verification.G;
                result.P = verification.P;
                result.objective = verification.objective;
                result.upper_bound = verification.objective;
                result.incumbent_source = label;
                result.incumbent_source_detail =
                    "verified imported incumbent; diagnostic UB only";
                result.notes.push_back(label + " import verified");
            } else {
                result.incumbent_import_errors.insert(
                    result.incumbent_import_errors.end(),
                    verification.errors.begin(), verification.errors.end());
                result.notes.push_back(label + " import rejected by verifier");
            }
        } catch (const std::exception& e) {
            result.incumbent_import_errors.push_back(e.what());
            result.notes.push_back(label + " import failed: " + std::string(e.what()));
        }
    };

    testPath(opt.incumbent_json_path, opt.incumbent_format, "incumbent-json");
    testPath(opt.hga_incumbent_path, opt.hga_incumbent_format, "hga-incumbent");

    std::vector<ebrp::RoutePlan> malformed = emptyRouteSet(instance);
    if (!malformed.empty() && instance.V >= 1) {
        malformed[0].nodes = {0, 1, 0};
        malformed[0].operations.clear();
    }
    ebrp::Verification malformed_check =
        ebrp::verifySolution(instance, malformed, opt.lambda);
    if (malformed_check.feasible) {
        result.status = "diagnostic_failed";
        result.notes.push_back("malformed incumbent unexpectedly passed verifier");
    } else {
        result.notes.push_back("malformed incumbent rejection verified");
    }
    if (result.routes.empty()) {
        result.routes = emptyRouteSet(instance);
        result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
        result.final_inventory = result.verification.final_inventory;
        result.G = result.verification.G;
        result.P = result.verification.P;
        result.objective = result.verification.objective;
        result.upper_bound = result.objective;
    }
    result.lower_bound = 0.0;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveGiniFrontierDiagnostic(const ebrp::Instance& instance,
                                              const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gcap-frontier";
    result.bpc_workers = std::max(1, opt.bpc_workers);
    result.pricing_threads = std::max(1, opt.pricing_threads);
    result.parallel_frontier = opt.parallel_frontier && result.bpc_workers > 1;
    result.parallel_nodes = false;
    result.dominance_mode = opt.column_dominance ? opt.column_dominance_mode : "off";
    result.dominance_exact_safe = opt.column_dominance_mode != "pareto";
    result.projection_bound_scope = "global";
    result.movement_audit_enabled = opt.movement_bound_audit;
    result.support_duration_max_subset_size = opt.support_duration_max_subset_size;
    result.support_duration_min_pickup_rule = "ceil_half_support";
    result.route_mask_support_duration_pruning =
        opt.route_mask_support_duration_pruning;
    result.focused_retry_enabled = opt.frontier_focused_min_lb_retry;
    result.incumbent_generation_method = opt.bpc_incumbent;
    result.pricing_best_reduced_cost_any = std::numeric_limits<double>::infinity();
    result.pricing_best_new_reduced_cost = std::numeric_limits<double>::infinity();
    result.pricing_closure_certified_exact = true;
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Gamma-frontier diagnostic covers Gini intervals with fixed-Gini interval branch-price trees. It reports optimal only if every relevant interval is closed or bound-fathomed and the aggregated lower bound reaches the incumbent. Each interval also uses the valid trivial bound objective>=G>=interval_floor and a final-inventory pickup/route/Gini relaxation bound when it solves.");
    result.notes.push_back("Optimization flags: column_dominance="
        + std::string(opt.column_dominance ? "true" : "false")
        + ", column_dominance_mode=" + result.dominance_mode
        + ", projection_bound=" + std::string(opt.projection_bound ? "true" : "false")
        + ", penalty_domain_tightening=" + std::string(opt.penalty_domain_tightening ? "true" : "false")
        + ", movement_domain_tightening=" + std::string(opt.movement_domain_tightening ? "true" : "false")
        + ", movement_bound_audit=" + std::string(opt.movement_bound_audit ? "true" : "false")
        + ", frontier_best_bound_scheduling=" + std::string(opt.frontier_best_bound_scheduling ? "true" : "false")
        + ", frontier_relaxation_cache=" + std::string(opt.frontier_relaxation_cache ? "true" : "false")
        + ", frontier_focused_min_lb_retry=" + std::string(opt.frontier_focused_min_lb_retry ? "true" : "false")
        + ", support_duration_pruning=" + std::string(opt.support_duration_pruning ? "true" : "false")
        + ", route_mask_support_duration_pruning=" + std::string(opt.route_mask_support_duration_pruning ? "true" : "false")
        + ", support_duration_min_pickup_rule=ceil_half_support"
        + ", support_duration_max_subset_size=" + std::to_string(opt.support_duration_max_subset_size)
        + ", support_feasibility_oracle=" + std::string(opt.support_feasibility_oracle ? "requested_but_not_enabled" : "false")
        + ", gcap_pricing_columns=" + std::to_string(opt.gcap_pricing_columns)
        + ", frontier_column_cache="
        + std::string(opt.frontier_column_cache ? "requested_but_not_enabled" : "false"));
    {
        const unsigned hw = std::thread::hardware_concurrency();
        std::ostringstream thread_note;
        thread_note << "BPC thread policy: requested_threads=" << opt.threads
                    << ", bpc_workers=" << result.bpc_workers
                    << ", pricing_threads=" << result.pricing_threads
                    << ", parallel_frontier="
                    << (result.parallel_frontier ? "true" : "false")
                    << ", parallel_nodes=false"
                    << ", hardware_concurrency=" << hw
                    << "; restricted-master CPLEX and inventory-bound CPLEX calls use one internal thread each";
        if (opt.parallel_nodes) {
            thread_note << "; --parallel-nodes was requested but branch-node parallelism is disabled in this build";
        }
        if (hw > 0 && result.parallel_frontier &&
            result.bpc_workers * result.pricing_threads > static_cast<int>(hw)) {
            thread_note << "; oversubscription_warning=true";
        }
        result.notes.push_back(thread_note.str());
    }

    auto elapsedSeconds = [&]() {
        return std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
    };
    auto remainingSeconds = [&]() {
        if (opt.solve_time_limit <= 0.0) return 0.0;
        return std::max(0.0, opt.solve_time_limit - elapsedSeconds());
    };
    auto emptyRoutes = [&]() {
        std::vector<ebrp::RoutePlan> routes(instance.M);
        for (int k = 0; k < instance.M; ++k) {
            routes[k].vehicle = k;
            routes[k].nodes = {0, 0};
        }
        return routes;
    };

    std::vector<ebrp::RoutePlan> incumbent_routes = emptyRoutes();
    ebrp::Verification incumbent_verification =
        ebrp::verifySolution(instance, incumbent_routes, opt.lambda);
    auto acceptIncumbentRoutes = [&](const std::vector<ebrp::RoutePlan>& candidate_routes,
                                     const std::string& source) {
        ebrp::Verification candidate =
            ebrp::verifySolution(instance, candidate_routes, opt.lambda);
        if (!candidate.feasible) {
            result.notes.push_back("discarded " + source
                + " incumbent: independent verifier rejected the routes");
            return false;
        }
        if (incumbent_verification.feasible &&
            candidate.objective >= incumbent_verification.objective - 1e-9) {
            result.notes.push_back("discarded " + source
                + " incumbent: verified objective=" + std::to_string(candidate.objective)
                + " did not improve current incumbent=" +
                std::to_string(incumbent_verification.objective));
            return false;
        }
        incumbent_routes = candidate_routes;
        incumbent_verification = candidate;
        result.incumbent_source = source;
        result.notes.push_back("accepted " + source
            + " incumbent for frontier cutoff only: objective="
            + std::to_string(candidate.objective)
            + ", G=" + std::to_string(candidate.G)
            + ", P=" + std::to_string(candidate.P));
        return true;
    };

    {
        const auto incumbent_start = std::chrono::steady_clock::now();
        BpcOwnedIncumbentResult owned =
            runBpcOwnedIncumbentGenerator(instance, opt, start);
        result.incumbent_generation_time_seconds +=
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - incumbent_start).count();
        result.pricing_calls += owned.pricing_calls;
        result.columns += owned.generated_columns;
        result.columns_generated_raw += owned.columns_generated_raw;
        result.nodes += owned.route_states + owned.operation_states + owned.master_states;
        result.columns_after_dominance += owned.columns_after_dominance;
        result.columns_dominated += owned.columns_dominated;
        result.dominance_time_seconds += owned.dominance_time_seconds;
        for (const std::string& note : owned.notes) result.notes.push_back(note);
        if (owned.found) {
            acceptIncumbentRoutes(owned.routes, "BPC-owned " + opt.bpc_incumbent);
        }
    }

    if (opt.bpc_incumbent == "compact" ||
        opt.bpc_incumbent == "compact-cplex") {
        const auto compact_start = std::chrono::steady_clock::now();
        ebrp::SolveOptions seed_opt = opt;
        seed_opt.out_path.clear();
        seed_opt.log_path.clear();
        seed_opt.solve_time_limit = opt.bpc_incumbent_seconds > 0.0
            ? opt.bpc_incumbent_seconds
            : std::min(30.0, std::max(1.0, opt.solve_time_limit * 0.25));
        ebrp::SolveResult seed;
        if (opt.bpc_incumbent == "compact-cplex") {
            seed_opt.method = "cplex";
            seed = ebrp::solveCplexBaseline(instance, seed_opt);
        } else {
            seed_opt.method = "tailored";
            seed = ebrp::solveTailoredExact(instance, seed_opt);
        }
        result.incumbent_generation_time_seconds +=
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - compact_start).count();
        std::ostringstream compact_note;
        compact_note << "compact incumbent seed mode=" << opt.bpc_incumbent
                     << ", status=" << seed.status
                     << ", objective=" << seed.objective
                     << ", runtime=" << seed.runtime_seconds
                     << ", seed_time_limit=" << seed_opt.solve_time_limit;
        result.notes.push_back(compact_note.str());
        if (!seed.routes.empty()) {
            const std::string source = opt.bpc_incumbent == "compact-cplex"
                ? "compact CPLEX seed"
                : "compact tailored seed";
            if (acceptIncumbentRoutes(seed.routes, source)) {
                result.incumbent_source_detail =
                    "verified UB imported from " + opt.bpc_incumbent +
                    " seed; not lower-bound evidence";
            }
        } else {
            result.notes.push_back("compact incumbent seed produced no route plan to verify");
        }
    }

    auto tryImportIncumbent = [&](const std::string& path,
                                  const std::string& format,
                                  const std::string& source_label) {
        if (path.empty()) return;
        result.incumbent_import_attempted = true;
        const std::string import_source = opt.incumbent_source_name.empty()
            ? source_label
            : opt.incumbent_source_name;
        try {
            const std::vector<ebrp::RoutePlan> external_routes =
                loadIncumbentRoutesByFormat(path, format, instance.M);
            ebrp::Verification imported =
                ebrp::verifySolution(instance, external_routes, opt.lambda);
            const bool imported_verified = imported.feasible &&
                imported.objective_matches && imported.errors.empty();
            if (imported_verified) {
                result.incumbent_import_verified = true;
                result.incumbent_import_objective = imported.objective;
                result.incumbent_import_G = imported.G;
                result.incumbent_import_P = imported.P;
            } else {
                result.incumbent_import_errors.insert(
                    result.incumbent_import_errors.end(),
                    imported.errors.begin(), imported.errors.end());
            }
            const bool accepted = acceptIncumbentRoutes(external_routes, import_source);
            if (accepted) {
                result.incumbent_source_detail =
                    "verified imported incumbent from " + path +
                    " using format=" + format +
                    "; UB only, no lower-bound certificate inherited";
                result.notes.push_back("external incumbent is used only as a feasible route warm start/cutoff; no lower-bound certificate is inherited from "
                    + path);
            }
        } catch (const std::exception& e) {
            result.incumbent_import_errors.push_back(e.what());
            result.notes.push_back(std::string("could not load external incumbent: ") + e.what());
        }
    };
    tryImportIncumbent(opt.incumbent_json_path, opt.incumbent_format,
                       "external " + opt.incumbent_format + " incumbent");
    tryImportIncumbent(opt.hga_incumbent_path, opt.hga_incumbent_format,
                       "HGA/TGBC " + opt.hga_incumbent_format + " incumbent");
    if (opt.gcap_seed_cplex) {
        ebrp::SolveOptions seed_opt = opt;
        seed_opt.method = "cplex";
        seed_opt.plain_baseline = false;
        seed_opt.out_path.clear();
        if (opt.gcap_seed_time_limit > 0.0) {
            seed_opt.solve_time_limit = opt.gcap_seed_time_limit;
            if (opt.solve_time_limit > 0.0) {
                seed_opt.solve_time_limit = std::min(seed_opt.solve_time_limit,
                                                     opt.solve_time_limit);
            }
        } else {
            seed_opt.solve_time_limit = (opt.solve_time_limit > 0.0)
                ? std::max(1.0, std::min(30.0, opt.solve_time_limit * 0.25))
                : opt.solve_time_limit;
        }
        if (!seed_opt.log_path.empty()) seed_opt.log_path += ".frontier_seed_cplex.log";
        ebrp::SolveResult seed = ebrp::solveCplexBaseline(instance, seed_opt);
        std::ostringstream seed_note;
        seed_note << "frontier CPLEX seed status=" << seed.status
                  << ", objective=" << seed.objective
                  << ", G=" << seed.G
                  << ", P=" << seed.P
                  << ", runtime=" << seed.runtime_seconds
                  << ", seed_time_limit=" << seed_opt.solve_time_limit;
        result.notes.push_back(seed_note.str());
        acceptIncumbentRoutes(seed.routes, "CPLEX seed");
    }

    result.routes = incumbent_routes;
    result.verification = incumbent_verification;
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    if (result.incumbent_source.empty()) result.incumbent_source = "empty-route incumbent";

    const double gini_max_possible = (instance.V > 0)
        ? static_cast<double>(instance.V - 1) / static_cast<double>(instance.V) : 1.0;
    const double relevant_gini_upper_for_improvement =
        std::min(result.upper_bound, gini_max_possible);
    const double cover_lo = std::max(0.0, opt.gini_floor);
    const bool user_gini_cap_truncates =
        opt.gini_cap >= 0.0 &&
        opt.gini_cap < relevant_gini_upper_for_improvement - 1e-12;
    const double cover_hi = std::min({
        relevant_gini_upper_for_improvement,
        opt.gini_cap >= 0.0 ? opt.gini_cap : gini_max_possible
    });
    result.gini_max_possible = gini_max_possible;
    result.relevant_gini_upper_for_improvement =
        relevant_gini_upper_for_improvement;
    result.covered_gini_upper_bound = cover_hi;
    result.frontier_covers_all_improving_gini_values =
        cover_lo <= 1e-12 &&
        cover_hi >= relevant_gini_upper_for_improvement - 1e-12 &&
        !user_gini_cap_truncates;
    result.frontier_range_certificate_scope =
        result.frontier_covers_all_improving_gini_values
            ? "original_full_improving_range"
            : (user_gini_cap_truncates ? "capped_diagnostic" : "partial_range");

    if (!result.verification.feasible) {
        result.status = "gcap_frontier_no_incumbent";
        result.certificate = "frontier diagnostic could not obtain a feasible incumbent";
        result.runtime_seconds = elapsedSeconds();
        result.wall_time_seconds = result.runtime_seconds;
        result.aggregate_worker_time_seconds = result.pricing_time_seconds +
            result.master_time_seconds + result.bound_time_seconds;
        return result;
    }

    if (result.objective <= 1e-12) {
        result.lower_bound = 0.0;
        result.upper_bound = result.objective;
        result.gap = 0.0;
        result.status = "optimal";
        result.certificate = "frontier certificate: a feasible incumbent has objective zero and both Gini and satisfaction terms are nonnegative";
        result.runtime_seconds = elapsedSeconds();
        result.wall_time_seconds = result.runtime_seconds;
        result.aggregate_worker_time_seconds = result.pricing_time_seconds +
            result.master_time_seconds + result.bound_time_seconds;
        result.notes.push_back("zero incumbent closes the global objective without interval solves");
        return result;
    }

    if (cover_lo > cover_hi + 1e-12) {
        result.status = "gcap_frontier_invalid_range";
        result.certificate = "frontier lower Gini bound exceeds the covered upper bound";
        result.runtime_seconds = elapsedSeconds();
        result.wall_time_seconds = result.runtime_seconds;
        result.aggregate_worker_time_seconds = result.pricing_time_seconds +
            result.master_time_seconds + result.bound_time_seconds;
        return result;
    }

    const int intervals = std::max(1, opt.frontier_intervals);
    struct FrontierIntervalRecord {
        bool processed = false;
        bool skipped = false;
        bool complete = false;
        bool lower_bound_valid = false;
        bool empty_complete = false;
        bool replaced_by_children = false;
        double lo = 0.0;
        double hi = 0.0;
        double lower_bound = 0.0;
        double relaxation_lower_bound = 0.0;
        int open_nodes = 0;
        std::string lower_bound_source = "gamma_floor";
        std::string lb_sources = "gamma_floor";
        bool bound_fathomed = false;
        bool tree_closed = false;
        bool pricing_closed = false;
        double cheap_prepass_lower_bound = 0.0;
        std::string cheap_prepass_sources = "gamma_floor";
    };
    std::vector<FrontierIntervalRecord> interval_records(intervals);
    const bool initial_full_objective_range =
        result.frontier_covers_all_improving_gini_values;
    std::ostringstream cover_note;
    cover_note << "frontier cover range=[" << cover_lo << "," << cover_hi
               << "], intervals=" << intervals
               << ", incumbent_objective=" << result.objective
               << ", incumbent_G=" << result.G
               << ", gini_max_possible=" << gini_max_possible
               << ", relevant_gini_upper_for_improvement="
               << relevant_gini_upper_for_improvement
               << ", frontier_covers_all_improving_gini_values="
               << (initial_full_objective_range ? "true" : "false")
               << ", range_scope=" << result.frontier_range_certificate_scope;
    result.notes.push_back(cover_note.str());
    for (int idx = 0; idx < intervals; ++idx) {
        const double frac0 = static_cast<double>(idx) / intervals;
        const double frac1 = static_cast<double>(idx + 1) / intervals;
        interval_records[idx].lo = cover_lo + (cover_hi - cover_lo) * frac0;
        interval_records[idx].hi = (idx + 1 == intervals)
            ? cover_hi : cover_lo + (cover_hi - cover_lo) * frac1;
        interval_records[idx].lower_bound = std::max(0.0, interval_records[idx].lo);
        interval_records[idx].lower_bound_valid = true;
    }
    result.cheap_prepass_enabled = opt.frontier_best_bound_scheduling ||
        opt.projection_bound || opt.movement_domain_tightening ||
        opt.penalty_domain_tightening;
    if (result.cheap_prepass_enabled) {
        for (int idx = 0; idx < intervals; ++idx) {
            FrontierIntervalRecord& record = interval_records[idx];
            std::vector<int> inv_lb(instance.V + 1, 0);
            std::vector<int> inv_ub(instance.V + 1, 0);
            for (int station = 1; station <= instance.V; ++station) {
                inv_ub[station] = instance.capacity[station];
            }
            if (opt.movement_domain_tightening) {
                ebrp::MovementReachabilityTighteningResult move =
                    ebrp::tightenInventoryIntervalsByMovementReachability(
                        instance, inv_lb, inv_ub);
                record.cheap_prepass_sources += "|movement_domain";
                result.movement_tightening_time_seconds += move.time_seconds;
                result.movement_domains_tightened_count += move.domains_tightened_count;
                result.movement_domain_width_before += move.total_domain_width_before;
                result.movement_domain_width_after += move.total_domain_width_after;
                result.movement_unreachable_station_count += move.unreachable_station_count;
            }
            if (opt.penalty_domain_tightening) {
                ebrp::PenaltyDomainTighteningResult tighten =
                    ebrp::tightenInventoryIntervalsByPenaltyBudget(
                        instance, opt.lambda, record.lo, result.upper_bound,
                        inv_lb, inv_ub);
                record.cheap_prepass_sources += "|penalty_domain";
                result.penalty_budget = tighten.penalty_budget;
                result.domains_tightened_count += tighten.domains_tightened_count;
                result.total_domain_width_before += tighten.total_domain_width_before;
                result.total_domain_width_after += tighten.total_domain_width_after;
                if (tighten.fathomed_by_budget) {
                    record.lower_bound = result.upper_bound;
                    record.lower_bound_source = "cheap_penalty_budget";
                    record.lb_sources += "|cheap_penalty_budget";
                }
            }
            if (opt.projection_bound) {
                const auto projection_start = std::chrono::steady_clock::now();
                ebrp::InventoryRatioProjectionBound projection =
                    ebrp::computeInventoryRatioProjectionBound(
                        instance, opt.lambda, inv_lb, inv_ub, record.lo,
                        "global");
                result.projection_bound_time_seconds +=
                    std::chrono::duration<double>(
                        std::chrono::steady_clock::now() - projection_start).count();
                record.cheap_prepass_sources += "|projection_bound";
                if (projection.valid &&
                    projection.objective_lower_bound > record.lower_bound + 1e-12) {
                    record.lower_bound = projection.objective_lower_bound;
                    record.lower_bound_source = "cheap_projection_bound";
                    record.lb_sources += "|cheap_projection_bound";
                    result.projection_bound_best_value =
                        std::max(result.projection_bound_best_value,
                                 projection.objective_lower_bound);
                    result.projection_bound_scope = projection.bound_scope;
                }
            }
            record.cheap_prepass_lower_bound = record.lower_bound;
            if (record.lower_bound >= result.upper_bound - 1e-7) {
                ++result.intervals_skipped_by_cheap_bound;
            }
        }
    }
    std::vector<int> initial_schedule(intervals);
    for (int idx = 0; idx < intervals; ++idx) initial_schedule[idx] = idx;
    if (opt.frontier_best_bound_scheduling) {
        std::sort(initial_schedule.begin(), initial_schedule.end(),
                  [&](int lhs, int rhs) {
                      const FrontierIntervalRecord& a = interval_records[lhs];
                      const FrontierIntervalRecord& b = interval_records[rhs];
                      if (std::fabs(a.lower_bound - b.lower_bound) > 1e-12) {
                          return a.lower_bound < b.lower_bound;
                      }
                      const double amid = 0.5 * (a.lo + a.hi);
                      const double bmid = 0.5 * (b.lo + b.hi);
                      const double ad = std::fabs(amid - result.G);
                      const double bd = std::fabs(bmid - result.G);
                      if (std::fabs(ad - bd) > 1e-12) return ad < bd;
                      return lhs < rhs;
                  });
        result.frontier_scheduling_mode = "best_bound_lower_bound_then_incumbent_gini";
    } else {
        result.frontier_scheduling_mode = "interval_index";
    }
    {
        std::ostringstream order;
        for (int pos = 0; pos < static_cast<int>(initial_schedule.size()); ++pos) {
            if (pos > 0) order << ";";
            order << initial_schedule[pos];
        }
        result.interval_processing_order = order.str();
        result.interval_processing_order_initial = order.str();
        result.interval_processing_order_actual = order.str();
    }

    struct InitialIntervalWork {
        int idx = 0;
        FrontierIntervalRecord record;
        ebrp::GiniCapTreeResult tree;
        ebrp::GiniIntervalInventoryRelaxationBound relaxation_stats;
        bool ran_tree = false;
        bool has_relaxation_stats = false;
        bool has_candidate = false;
        ebrp::Verification candidate_verification;
        std::vector<ebrp::RoutePlan> candidate_routes;
        std::vector<std::string> notes;
        double bound_time_seconds = 0.0;
    };

    auto accumulateInventoryRelaxationStats =
        [&](const ebrp::GiniIntervalInventoryRelaxationBound& inv_relax) {
            if (inv_relax.projection_bound_valid) {
                result.projection_bound_best_value =
                    std::max(result.projection_bound_best_value,
                             inv_relax.projection_objective_lower_bound);
                result.projection_bound_scope = inv_relax.projection_bound_scope;
            }
            result.projection_bound_time_seconds +=
                inv_relax.projection_bound_time_seconds;
            if (inv_relax.projection_bound_fathomed) {
                ++result.projection_bound_prunes;
            }
            if (std::isfinite(inv_relax.penalty_budget)) {
                result.penalty_budget = inv_relax.penalty_budget;
            }
            result.domains_tightened_count += inv_relax.domains_tightened_count;
            result.total_domain_width_before += inv_relax.total_domain_width_before;
            result.total_domain_width_after += inv_relax.total_domain_width_after;
            result.penalty_tightening_time_seconds +=
                inv_relax.penalty_tightening_time_seconds;
            result.movement_domains_tightened_count +=
                inv_relax.movement_domains_tightened_count;
            result.movement_domain_width_before +=
                inv_relax.movement_domain_width_before;
            result.movement_domain_width_after +=
                inv_relax.movement_domain_width_after;
            result.movement_tightening_time_seconds +=
                inv_relax.movement_tightening_time_seconds;
            result.movement_unreachable_station_count +=
                inv_relax.movement_unreachable_station_count;
            result.route_mask_count_before_support_duration +=
                inv_relax.route_mask_count_before_support_duration;
            result.route_mask_count_after_support_duration +=
                inv_relax.route_mask_count_after_support_duration;
            result.route_masks_removed_by_support_duration +=
                inv_relax.route_masks_removed_by_support_duration;
            result.route_mask_support_duration_precompute_time_seconds +=
                inv_relax.route_mask_support_duration_precompute_time_seconds;
            result.route_mask_support_duration_max_removed_subset_size =
                std::max(result.route_mask_support_duration_max_removed_subset_size,
                         inv_relax.route_mask_support_duration_max_removed_subset_size);
        };

    auto accumulateTreeRound2Stats =
        [&](const ebrp::GiniCapTreeResult& tree) {
            result.pricing_columns_enumerated += tree.pricing_columns_enumerated;
            result.dominance_input_columns += tree.dominance_input_columns;
            result.dominance_kept_columns += tree.dominance_kept_columns;
            result.dominance_removed_columns += tree.dominance_removed_columns;
            result.dominance_removed_existing_projection +=
                tree.dominance_removed_existing_projection;
            result.dominance_removed_candidate_projection +=
                tree.dominance_removed_candidate_projection;
            result.rmp_columns_inserted += tree.rmp_columns_inserted;
            result.rmp_columns_active += tree.rmp_columns_active;
            result.pricing_best_reduced_cost_any =
                std::min(result.pricing_best_reduced_cost_any,
                         tree.pricing_best_reduced_cost_any);
            result.pricing_best_new_reduced_cost =
                std::min(result.pricing_best_new_reduced_cost,
                         tree.pricing_best_new_reduced_cost);
            result.pricing_duplicate_negative_projections +=
                tree.pricing_duplicate_negative_projections;
            result.pricing_new_negative_projections +=
                tree.pricing_new_negative_projections;
            result.pricing_blocked_by_duplicate_projection =
                result.pricing_blocked_by_duplicate_projection ||
                tree.pricing_blocked_by_duplicate_projection;
            result.pricing_closure_certified_exact =
                result.pricing_closure_certified_exact &&
                tree.pricing_closure_certified_exact;
            result.support_duration_cuts_generated +=
                tree.support_duration_cuts_generated;
            result.support_duration_pruned_labels +=
                tree.support_duration_pruned_labels;
            result.support_duration_pruned_columns +=
                tree.support_duration_pruned_columns;
            result.support_duration_strong_cuts_generated +=
                tree.support_duration_strong_cuts_generated;
            result.support_duration_strong_pruned_labels +=
                tree.support_duration_strong_pruned_labels;
            result.support_duration_strong_pruned_columns +=
                tree.support_duration_strong_pruned_columns;
            result.support_duration_max_subset_size =
                std::max(result.support_duration_max_subset_size,
                         tree.support_duration_max_subset_size);
            result.support_duration_precompute_time_seconds +=
                tree.support_duration_precompute_time_seconds;
            result.movement_domains_tightened_count +=
                tree.movement_domains_tightened_count;
            result.movement_domain_width_before +=
                tree.movement_domain_width_before;
            result.movement_domain_width_after +=
                tree.movement_domain_width_after;
            result.movement_tightening_time_seconds +=
                tree.movement_tightening_time_seconds;
            result.movement_unreachable_station_count +=
                tree.movement_unreachable_station_count;
        };

    struct CachedRelaxation {
        ebrp::GiniIntervalInventoryRelaxationBound bound;
        double elapsed = 0.0;
        double budget = 0.0;
    };
    std::unordered_map<std::string, CachedRelaxation> relaxation_cache;
    auto relaxationCacheKey = [&](double lo, double hi, double cutoff) {
        std::ostringstream key;
        key << instance.name << "|lambda=" << opt.lambda
            << "|lo=" << std::setprecision(17) << lo
            << "|hi=" << std::setprecision(17) << hi
            << "|cutoff=" << std::setprecision(17) << cutoff
            << "|route_mask_max_v=" << opt.route_mask_max_v
            << "|projection=" << (opt.projection_bound ? 1 : 0)
            << "|penalty=" << (opt.penalty_domain_tightening ? 1 : 0)
            << "|movement=" << (opt.movement_domain_tightening ? 1 : 0)
            << "|movement_audit=" << (opt.movement_bound_audit ? 1 : 0);
        return key.str();
    };
    auto computeInventoryRelaxation =
        [&](double lo, double hi, double budget, double cutoff,
            bool allow_cache) {
            const bool cache_enabled =
                opt.frontier_relaxation_cache && allow_cache &&
                !result.parallel_frontier;
            const std::string key = cache_enabled
                ? relaxationCacheKey(lo, hi, cutoff) : std::string{};
            if (cache_enabled) {
                auto it = relaxation_cache.find(key);
                if (it != relaxation_cache.end()) {
                    if (budget <= it->second.budget + 1e-9) {
                        ++result.frontier_relax_cache_hits;
                        result.frontier_relax_cache_time_saved_estimate += it->second.elapsed;
                        result.notes.push_back("frontier relaxation cache hit for interval ["
                            + std::to_string(lo) + "," + std::to_string(hi) + "]");
                        return it->second;
                    }
                    ++result.frontier_relax_cache_partial_hits;
                    result.notes.push_back("frontier relaxation cache partial hit for interval ["
                        + std::to_string(lo) + "," + std::to_string(hi)
                        + "]; recomputing with larger budget");
                } else {
                    ++result.frontier_relax_cache_misses;
                }
            }
            const auto bound_start = std::chrono::steady_clock::now();
            CachedRelaxation out;
            auto compute_once = [&](bool movement_enabled) {
                return ebrp::computeGiniIntervalInventoryRelaxationBound(
                    instance, opt.lambda, lo, hi, budget, cutoff,
                    opt.route_mask_max_v, opt.projection_bound,
                    opt.penalty_domain_tightening,
                    movement_enabled,
                    opt.route_mask_support_duration_pruning);
            };
            if (opt.movement_bound_audit) {
                ++result.movement_audit_intervals;
                ebrp::GiniIntervalInventoryRelaxationBound no_movement =
                    compute_once(false);
                ebrp::GiniIntervalInventoryRelaxationBound with_movement =
                    compute_once(true);
                const double no_lb = no_movement.infeasible
                    ? cutoff : no_movement.objective_lower_bound;
                const double with_lb = with_movement.infeasible
                    ? cutoff : with_movement.objective_lower_bound;
                result.relaxation_lb_no_movement =
                    std::max(result.relaxation_lb_no_movement, no_lb);
                result.relaxation_lb_with_movement =
                    std::max(result.relaxation_lb_with_movement, with_lb);
                if (with_lb > no_lb + 1e-9) {
                    ++result.movement_audit_bound_improved_count;
                    out.bound = with_movement;
                    out.bound.note += ", movement_audit_selected=with_movement"
                        ", relaxation_lb_no_movement=" + std::to_string(no_lb)
                        + ", relaxation_lb_with_movement=" + std::to_string(with_lb);
                } else {
                    if (with_lb < no_lb - 1e-9) {
                        ++result.movement_audit_bound_worse_count;
                    }
                    out.bound = no_movement;
                    out.bound.note += ", movement_audit_selected=no_movement"
                        ", relaxation_lb_no_movement=" + std::to_string(no_lb)
                        + ", relaxation_lb_with_movement=" + std::to_string(with_lb);
                }
                result.relaxation_lb_used =
                    std::max(result.relaxation_lb_used,
                             std::max(no_lb, with_lb));
            } else {
                out.bound = compute_once(opt.movement_domain_tightening);
                const double used_lb = out.bound.infeasible
                    ? cutoff : out.bound.objective_lower_bound;
                result.relaxation_lb_used =
                    std::max(result.relaxation_lb_used, used_lb);
                if (opt.movement_domain_tightening) {
                    result.relaxation_lb_with_movement =
                        std::max(result.relaxation_lb_with_movement, used_lb);
                } else {
                    result.relaxation_lb_no_movement =
                        std::max(result.relaxation_lb_no_movement, used_lb);
                }
            }
            out.elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - bound_start).count();
            out.budget = budget;
            if (cache_enabled) {
                auto it = relaxation_cache.find(key);
                if (it != relaxation_cache.end()) {
                    ++result.frontier_relax_cache_recomputed;
                    const double old_lb = it->second.bound.infeasible
                        ? cutoff : it->second.bound.objective_lower_bound;
                    const double new_lb = out.bound.infeasible
                        ? cutoff : out.bound.objective_lower_bound;
                    if (old_lb > new_lb + 1e-9) {
                        out.bound = it->second.bound;
                        ++result.frontier_relax_cache_best_bound_reused;
                    }
                    it->second = out;
                } else {
                    relaxation_cache.emplace(key, out);
                }
            }
            return out;
        };

    auto processInitialInterval = [&](int idx,
                                      double fixed_upper_bound,
                                      const std::vector<ebrp::RoutePlan>& fixed_incumbent_routes) {
        InitialIntervalWork work;
        work.idx = idx;
        const double frac0 = static_cast<double>(idx) / intervals;
        const double frac1 = static_cast<double>(idx + 1) / intervals;
        const double lo = cover_lo + (cover_hi - cover_lo) * frac0;
        const double hi = (idx + 1 == intervals)
            ? cover_hi : cover_lo + (cover_hi - cover_lo) * frac1;
        work.record = interval_records[idx];
        work.record.lo = lo;
        work.record.hi = hi;
        work.record.lower_bound =
            std::max(work.record.lower_bound, std::max(0.0, lo));
        work.record.lower_bound_valid = true;
        if (lo >= fixed_upper_bound - 1e-12) {
            work.record.processed = true;
            work.record.skipped = true;
            work.record.complete = true;
            work.record.lower_bound_valid = true;
            work.record.lower_bound = lo;
            work.notes.push_back("interval " + std::to_string(idx)
                + " skipped because floor >= incumbent objective");
            return work;
        }
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
            work.notes.push_back("frontier time limit reached before interval "
                + std::to_string(idx));
            return work;
        }

        const double relaxation_budget = (opt.frontier_relax_seconds > 0.0)
            ? opt.frontier_relax_seconds
            : ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, std::min(5.0, remainingSeconds() * 0.10))
                : 5.0);
        const CachedRelaxation cached_relax =
            computeInventoryRelaxation(lo, hi, relaxation_budget,
                                       fixed_upper_bound, false);
        const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
            cached_relax.bound;
        work.relaxation_stats = inv_relax;
        work.has_relaxation_stats = true;
        const double bound_elapsed = cached_relax.elapsed;
        work.bound_time_seconds += bound_elapsed;
        if (inv_relax.computed) {
            work.record.processed = true;
            work.record.relaxation_lower_bound = inv_relax.infeasible
                ? fixed_upper_bound
                : inv_relax.objective_lower_bound;
            work.record.lower_bound_valid = true;
            if (work.record.relaxation_lower_bound >
                work.record.lower_bound + 1e-12) {
                work.record.lower_bound_source = "inventory_route_gini_relaxation";
            }
            work.record.lb_sources += "|inventory_route_gini_relaxation";
            work.record.lower_bound =
                std::max(work.record.lower_bound,
                         work.record.relaxation_lower_bound);
        }
        work.notes.push_back("interval " + std::to_string(idx)
            + " inventory relaxation: " + inv_relax.note
            + ", bound_time=" + std::to_string(bound_elapsed));
        if (work.record.lower_bound >= fixed_upper_bound - 1e-7) {
            work.record.processed = true;
            work.record.complete = false;
            work.notes.push_back("interval " + std::to_string(idx)
                + " bound-fathomed by final-inventory relaxation before branch-price tree");
            return work;
        }
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
            work.notes.push_back("frontier time limit reached after interval relaxation "
                + std::to_string(idx));
            return work;
        }

        const double interval_budget = result.parallel_frontier
            ? ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, opt.solve_time_limit / std::max(1, intervals))
                : 0.0)
            : ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, remainingSeconds() / std::max(1, intervals - idx))
                : 0.0);
        work.tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
            instance, opt.lambda, hi, lo, interval_budget, 24, opt.max_branch_nodes,
            &fixed_incumbent_routes, true, fixed_upper_bound, opt.gcap_warmstart_level,
            std::numeric_limits<double>::infinity(), opt.gcap_pricing_columns,
            opt.column_dominance, opt.column_dominance_mode,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, opt.support_duration_pruning,
            opt.support_duration_max_subset_size);
        work.ran_tree = true;
        work.record.processed = true;
        work.record.complete = work.tree.complete;
        work.record.lower_bound_valid = true;
        work.record.empty_complete = work.tree.complete && !work.tree.has_integer_incumbent;
        const double tree_interval_lb = work.tree.lower_bound_valid
            ? std::max(lo, work.tree.global_lower_bound)
            : lo;
        if (tree_interval_lb > work.record.lower_bound + 1e-12) {
            work.record.lower_bound_source = "branch_price_tree";
        }
        work.record.lower_bound =
            std::max(work.record.lower_bound, tree_interval_lb);
        work.record.open_nodes = work.tree.open_nodes;
        work.record.lb_sources += "|branch_price_tree";
        work.record.tree_closed = work.tree.complete;
        work.record.pricing_closed = work.tree.pricing_closure_certified_exact;

        if (work.tree.has_integer_incumbent && !work.tree.best_routes.empty()) {
            ebrp::Verification candidate =
                ebrp::verifySolution(instance, work.tree.best_routes, opt.lambda);
            if (candidate.feasible && candidate.objective < fixed_upper_bound - 1e-9) {
                work.has_candidate = true;
                work.candidate_routes = work.tree.best_routes;
                work.candidate_verification = candidate;
            }
        }

        const bool certified_by_bound = work.record.lower_bound_valid &&
            work.record.lower_bound >= fixed_upper_bound - 1e-7;
        std::ostringstream note;
        note << "interval " << idx
             << " [" << lo << "," << hi << "]"
             << " complete=" << (work.tree.complete ? "true" : "false")
             << ", lower_bound_valid=" << (work.tree.lower_bound_valid ? "true" : "false")
             << ", certified_by_bound=" << (certified_by_bound ? "true" : "false")
             << ", empty_interval=" << (work.record.empty_complete ? "true" : "false")
             << ", has_incumbent=" << (work.tree.has_integer_incumbent ? "true" : "false")
             << ", tree_lb=" << work.tree.global_lower_bound
             << ", interval_lb=" << work.record.lower_bound
             << ", inventory_relax_lb=" << work.record.relaxation_lower_bound
             << ", resource_lb=" << work.tree.resource_objective_lower_bound
             << ", incumbent_metric=" << work.tree.best_integer_surrogate
             << ", incumbent_cutoff=" << fixed_upper_bound
             << ", nodes=" << work.tree.nodes_solved
             << ", columns=" << work.tree.generated_columns
             << ", pricing_calls=" << work.tree.pricing_calls
             << ", pricing_time=" << work.tree.pricing_time_seconds
             << ", master_time=" << work.tree.master_time_seconds
             << ", bound_time=" << work.bound_time_seconds
             << ", cuts_added=" << work.tree.cuts_added
             << ", open_nodes=" << work.tree.open_nodes;
        work.notes.push_back(note.str());
        return work;
    };

    auto applyInitialIntervalWork = [&](const InitialIntervalWork& work) {
        interval_records[work.idx] = work.record;
        result.bound_time_seconds += work.bound_time_seconds;
        if (work.has_relaxation_stats) {
            accumulateInventoryRelaxationStats(work.relaxation_stats);
        }
        for (const std::string& note : work.notes) {
            if (note.find("route_mask_duration_load_relaxation=true") !=
                std::string::npos) {
                result.route_mask_time_seconds += work.bound_time_seconds;
                break;
            }
        }
        for (const std::string& note : work.notes) result.notes.push_back(note);
        if (work.ran_tree) {
            result.nodes += work.tree.nodes_solved;
            result.columns += work.tree.generated_columns;
            result.pricing_calls += work.tree.pricing_calls;
            result.pricing_closed_nodes += work.tree.nodes_solved -
                (work.tree.complete ? 0 : std::min(1, work.tree.nodes_solved));
            result.cuts_added += work.tree.cuts_added;
            result.pricing_time_seconds += work.tree.pricing_time_seconds;
            result.master_time_seconds += work.tree.master_time_seconds;
            result.columns_generated_raw += work.tree.columns_generated_raw;
            result.columns_after_dominance += work.tree.columns_after_dominance;
            result.columns_dominated += work.tree.columns_dominated;
            result.dominance_time_seconds += work.tree.dominance_time_seconds;
            result.dominance_mode = work.tree.dominance_mode;
            result.dominance_exact_safe =
                result.dominance_exact_safe && work.tree.dominance_exact_safe;
            result.pricing_negative_columns_found +=
                work.tree.pricing_negative_columns_found;
            result.pricing_negative_columns_inserted +=
                work.tree.pricing_negative_columns_inserted;
            result.pricing_negative_columns_dominated +=
                work.tree.pricing_negative_columns_dominated;
            result.pricing_completed_exactly =
                result.pricing_completed_exactly && work.tree.pricing_completed_exactly;
            accumulateTreeRound2Stats(work.tree);
            result.projection_bound_prunes += work.tree.projection_bound_prunes;
            result.projection_bound_time_seconds += work.tree.projection_bound_time_seconds;
            result.projection_bound_best_value =
                std::max(result.projection_bound_best_value,
                         work.tree.projection_bound_best_value);
            result.projection_bound_scope = work.tree.projection_bound_scope;
            result.domains_tightened_count += work.tree.domains_tightened_count;
            result.total_domain_width_before += work.tree.total_domain_width_before;
            result.total_domain_width_after += work.tree.total_domain_width_after;
            result.penalty_tightening_time_seconds +=
                work.tree.penalty_tightening_time_seconds;
            if (std::isfinite(work.tree.penalty_budget)) {
                result.penalty_budget = work.tree.penalty_budget;
            }
        }
        if (work.has_candidate &&
            work.candidate_verification.feasible &&
            work.candidate_verification.objective < result.upper_bound - 1e-9) {
            result.routes = work.candidate_routes;
            result.verification = work.candidate_verification;
            result.final_inventory = work.candidate_verification.final_inventory;
            result.G = work.candidate_verification.G;
            result.P = work.candidate_verification.P;
            result.objective = work.candidate_verification.objective;
            result.upper_bound = work.candidate_verification.objective;
            incumbent_routes = work.candidate_routes;
            result.notes.push_back("frontier found improved incumbent in interval "
                + std::to_string(work.idx)
                + ", objective=" + std::to_string(work.candidate_verification.objective));
        }
    };

    const bool use_parallel_initial_frontier =
        result.parallel_frontier && intervals > 1;
    if (use_parallel_initial_frontier) {
        const int worker_count = std::min(result.bpc_workers, intervals);
        result.parallel_tasks += intervals;
        std::vector<int> schedule = initial_schedule;
        result.notes.push_back("parallel frontier initial interval pass enabled: workers="
            + std::to_string(worker_count)
            + ", tasks=" + std::to_string(intervals)
            + ", scheduling=" + result.frontier_scheduling_mode
            + ", shared_incumbent_updates=after_join");
        const double fixed_upper_bound = result.upper_bound;
        const std::vector<ebrp::RoutePlan> fixed_incumbent_routes = incumbent_routes;
        std::atomic<int> next_task{0};
        std::vector<std::future<std::vector<InitialIntervalWork>>> futures;
        for (int worker = 0; worker < worker_count; ++worker) {
            futures.push_back(std::async(std::launch::async,
                [&, fixed_upper_bound, fixed_incumbent_routes]() {
                    std::vector<InitialIntervalWork> local;
                    while (true) {
                        const int pos = next_task.fetch_add(1);
                        if (pos >= static_cast<int>(schedule.size())) break;
                        const int idx = schedule[pos];
                        local.push_back(processInitialInterval(
                            idx, fixed_upper_bound, fixed_incumbent_routes));
                    }
                    return local;
                }));
        }
        std::vector<InitialIntervalWork> works;
        for (auto& future : futures) {
            std::vector<InitialIntervalWork> local = future.get();
            works.insert(works.end(), local.begin(), local.end());
        }
        std::sort(works.begin(), works.end(),
                  [](const InitialIntervalWork& a, const InitialIntervalWork& b) {
                      return a.idx < b.idx;
                  });
        for (const InitialIntervalWork& work : works) {
            applyInitialIntervalWork(work);
        }
    }

    if (!use_parallel_initial_frontier) {
    for (int schedule_pos = 0; schedule_pos < intervals; ++schedule_pos) {
        const int idx = initial_schedule[schedule_pos];
        const double frac0 = static_cast<double>(idx) / intervals;
        const double frac1 = static_cast<double>(idx + 1) / intervals;
        const double lo = cover_lo + (cover_hi - cover_lo) * frac0;
        const double hi = (idx + 1 == intervals)
            ? cover_hi : cover_lo + (cover_hi - cover_lo) * frac1;
        interval_records[idx].lo = lo;
        interval_records[idx].hi = hi;
        if (lo >= result.upper_bound - 1e-12) {
            interval_records[idx].processed = true;
            interval_records[idx].skipped = true;
            interval_records[idx].complete = true;
            interval_records[idx].lower_bound_valid = true;
            interval_records[idx].lower_bound = lo;
            result.notes.push_back("interval " + std::to_string(idx)
                + " skipped because floor >= incumbent objective");
            continue;
        }
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
            result.notes.push_back("frontier time limit reached before interval "
                + std::to_string(idx));
            break;
        }

        const double relaxation_budget = (opt.frontier_relax_seconds > 0.0)
            ? opt.frontier_relax_seconds
            : ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, std::min(5.0, remainingSeconds() * 0.10))
                : 5.0);
        const CachedRelaxation cached_relax =
            computeInventoryRelaxation(lo, hi, relaxation_budget,
                                       result.upper_bound, true);
        const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
            cached_relax.bound;
        const double bound_elapsed = cached_relax.elapsed;
        result.bound_time_seconds += bound_elapsed;
        accumulateInventoryRelaxationStats(inv_relax);
        if (inv_relax.note.find("route_mask_duration_load_relaxation=true") !=
            std::string::npos) {
            result.route_mask_time_seconds += bound_elapsed;
        }
        if (inv_relax.computed) {
            interval_records[idx].processed = true;
            interval_records[idx].relaxation_lower_bound = inv_relax.infeasible
                ? result.upper_bound
                : inv_relax.objective_lower_bound;
            interval_records[idx].lower_bound_valid = true;
            if (interval_records[idx].relaxation_lower_bound >
                interval_records[idx].lower_bound + 1e-12) {
                interval_records[idx].lower_bound_source =
                    "inventory_route_gini_relaxation";
            }
            interval_records[idx].lb_sources += "|inventory_route_gini_relaxation";
            interval_records[idx].lower_bound =
                std::max(interval_records[idx].lower_bound,
                         interval_records[idx].relaxation_lower_bound);
        }
        result.notes.push_back("interval " + std::to_string(idx)
            + " inventory relaxation: " + inv_relax.note
            + ", bound_time=" + std::to_string(bound_elapsed));
        if (interval_records[idx].lower_bound >= result.upper_bound - 1e-7) {
            interval_records[idx].processed = true;
            interval_records[idx].complete = false;
            result.notes.push_back("interval " + std::to_string(idx)
                + " bound-fathomed by final-inventory relaxation before branch-price tree");
            continue;
        }
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
            result.notes.push_back("frontier time limit reached after interval relaxation "
                + std::to_string(idx));
            break;
        }

        const double interval_budget = (opt.solve_time_limit > 0.0)
            ? std::max(0.1, remainingSeconds() /
                std::max(1, intervals - schedule_pos))
            : 0.0;
        ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
            instance, opt.lambda, hi, lo, interval_budget, 24, opt.max_branch_nodes,
            &incumbent_routes, true, result.upper_bound, opt.gcap_warmstart_level,
            std::numeric_limits<double>::infinity(), opt.gcap_pricing_columns,
            opt.column_dominance, opt.column_dominance_mode,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, opt.support_duration_pruning,
            opt.support_duration_max_subset_size);
        result.nodes += tree.nodes_solved;
        result.columns += tree.generated_columns;
        result.pricing_calls += tree.pricing_calls;
        result.pricing_closed_nodes += tree.nodes_solved -
            (tree.complete ? 0 : std::min(1, tree.nodes_solved));
        result.cuts_added += tree.cuts_added;
        result.pricing_time_seconds += tree.pricing_time_seconds;
        result.master_time_seconds += tree.master_time_seconds;
        result.columns_generated_raw += tree.columns_generated_raw;
        result.columns_after_dominance += tree.columns_after_dominance;
        result.columns_dominated += tree.columns_dominated;
        result.dominance_time_seconds += tree.dominance_time_seconds;
        result.dominance_mode = tree.dominance_mode;
        result.dominance_exact_safe =
            result.dominance_exact_safe && tree.dominance_exact_safe;
        result.pricing_negative_columns_found += tree.pricing_negative_columns_found;
        result.pricing_negative_columns_inserted += tree.pricing_negative_columns_inserted;
        result.pricing_negative_columns_dominated += tree.pricing_negative_columns_dominated;
        result.pricing_completed_exactly =
            result.pricing_completed_exactly && tree.pricing_completed_exactly;
        accumulateTreeRound2Stats(tree);
        result.projection_bound_prunes += tree.projection_bound_prunes;
        result.projection_bound_time_seconds += tree.projection_bound_time_seconds;
        result.projection_bound_best_value =
            std::max(result.projection_bound_best_value,
                     tree.projection_bound_best_value);
        result.projection_bound_scope = tree.projection_bound_scope;
        result.domains_tightened_count += tree.domains_tightened_count;
        result.total_domain_width_before += tree.total_domain_width_before;
        result.total_domain_width_after += tree.total_domain_width_after;
        result.penalty_tightening_time_seconds +=
            tree.penalty_tightening_time_seconds;
        if (std::isfinite(tree.penalty_budget)) result.penalty_budget = tree.penalty_budget;
        interval_records[idx].processed = true;
        interval_records[idx].complete = tree.complete;
        interval_records[idx].lower_bound_valid = true;
        interval_records[idx].empty_complete = tree.complete && !tree.has_integer_incumbent;
        const double tree_interval_lb = tree.lower_bound_valid
            ? std::max(lo, tree.global_lower_bound)
            : lo;
        if (tree_interval_lb > interval_records[idx].lower_bound + 1e-12) {
            interval_records[idx].lower_bound_source = "branch_price_tree";
        }
        interval_records[idx].lower_bound =
            std::max(interval_records[idx].lower_bound, tree_interval_lb);
        interval_records[idx].open_nodes = tree.open_nodes;
        interval_records[idx].lb_sources += "|branch_price_tree";
        interval_records[idx].tree_closed = tree.complete;
        interval_records[idx].pricing_closed = tree.pricing_closure_certified_exact;

        if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
            ebrp::Verification candidate =
                ebrp::verifySolution(instance, tree.best_routes, opt.lambda);
            if (candidate.feasible &&
                candidate.objective < result.upper_bound - 1e-9) {
                result.routes = tree.best_routes;
                result.verification = candidate;
                result.final_inventory = candidate.final_inventory;
                result.G = candidate.G;
                result.P = candidate.P;
                result.objective = candidate.objective;
                result.upper_bound = candidate.objective;
                result.notes.push_back("frontier found improved incumbent in interval "
                    + std::to_string(idx)
                    + ", objective=" + std::to_string(candidate.objective));
            }
        }

        const bool certified_by_bound = interval_records[idx].lower_bound_valid &&
            interval_records[idx].lower_bound >= result.upper_bound - 1e-7;
        std::ostringstream note;
        note << "interval " << idx
             << " [" << lo << "," << hi << "]"
             << " complete=" << (tree.complete ? "true" : "false")
             << ", lower_bound_valid=" << (tree.lower_bound_valid ? "true" : "false")
             << ", certified_by_bound=" << (certified_by_bound ? "true" : "false")
             << ", empty_interval=" << (interval_records[idx].empty_complete ? "true" : "false")
             << ", has_incumbent=" << (tree.has_integer_incumbent ? "true" : "false")
             << ", tree_lb=" << tree.global_lower_bound
             << ", interval_lb=" << interval_records[idx].lower_bound
             << ", inventory_relax_lb=" << interval_records[idx].relaxation_lower_bound
             << ", resource_lb=" << tree.resource_objective_lower_bound
             << ", incumbent_metric=" << tree.best_integer_surrogate
             << ", incumbent_cutoff=" << result.upper_bound
             << ", nodes=" << tree.nodes_solved
             << ", columns=" << tree.generated_columns
             << ", pricing_calls=" << tree.pricing_calls
             << ", pricing_time=" << tree.pricing_time_seconds
             << ", master_time=" << tree.master_time_seconds
             << ", bound_time=" << bound_elapsed
             << ", cuts_added=" << tree.cuts_added
             << ", open_nodes=" << tree.open_nodes;
        result.notes.push_back(note.str());
    }
    }

    for (int split_pass = 1; split_pass <= std::max(0, opt.frontier_refine_splits); ++split_pass) {
        if (opt.solve_time_limit > 0.0 &&
            opt.frontier_retry_reserve_seconds > 0.0 &&
            remainingSeconds() <= opt.frontier_retry_reserve_seconds) {
            result.notes.push_back("adaptive frontier split pass "
                + std::to_string(split_pass)
                + " skipped to preserve retry reserve of "
                + std::to_string(opt.frontier_retry_reserve_seconds)
                + " seconds");
            break;
        }
        std::vector<int> split_indices;
        for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
            const FrontierIntervalRecord& record = interval_records[idx];
            if (record.replaced_by_children) continue;
            if (record.lo >= result.upper_bound - 1e-12) continue;
            if (record.empty_complete || record.complete) continue;
            if (record.lower_bound_valid && record.lower_bound < result.upper_bound - 1e-7) {
                split_indices.push_back(idx);
            }
        }
        std::sort(split_indices.begin(), split_indices.end(),
                  [&](int lhs, int rhs) {
                      const FrontierIntervalRecord& a = interval_records[lhs];
                      const FrontierIntervalRecord& b = interval_records[rhs];
                      if (std::fabs(a.lower_bound - b.lower_bound) > 1e-10) {
                          return a.lower_bound < b.lower_bound;
                      }
                      const double aw = a.hi - a.lo;
                      const double bw = b.hi - b.lo;
                      if (std::fabs(aw - bw) > 1e-12) return aw > bw;
                      return lhs < rhs;
                  });
        const int candidate_splits = static_cast<int>(split_indices.size());
        if (opt.frontier_split_batch > 0 &&
            candidate_splits > opt.frontier_split_batch) {
            split_indices.resize(opt.frontier_split_batch);
        }
        if (split_indices.empty()) break;
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) break;
        if (opt.solve_time_limit > 0.0 &&
            opt.frontier_retry_reserve_seconds > 0.0 &&
            remainingSeconds() <= opt.frontier_retry_reserve_seconds) {
            result.notes.push_back("adaptive frontier split pass "
                + std::to_string(split_pass)
                + " stopped before splitting to preserve retry reserve of "
                + std::to_string(opt.frontier_retry_reserve_seconds)
                + " seconds");
            break;
        }

        result.notes.push_back("adaptive frontier split pass " + std::to_string(split_pass)
            + " splitting " + std::to_string(split_indices.size())
            + " of " + std::to_string(candidate_splits)
            + " unresolved interval(s) by lowest current lower bound"
            + (opt.frontier_split_batch > 0
                ? ", split_batch=" + std::to_string(opt.frontier_split_batch)
                : ", split_batch=all"));

        for (int parent_idx : split_indices) {
            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
                result.notes.push_back("frontier time limit reached during adaptive split pass "
                    + std::to_string(split_pass));
                break;
            }
            if (opt.solve_time_limit > 0.0 &&
                opt.frontier_retry_reserve_seconds > 0.0 &&
                remainingSeconds() <= opt.frontier_retry_reserve_seconds) {
                result.notes.push_back("adaptive frontier split pass "
                    + std::to_string(split_pass)
                    + " stopped mid-pass to preserve retry reserve of "
                    + std::to_string(opt.frontier_retry_reserve_seconds)
                    + " seconds");
                break;
            }
            if (parent_idx < 0 || parent_idx >= static_cast<int>(interval_records.size())) continue;
            FrontierIntervalRecord& parent = interval_records[parent_idx];
            if (parent.replaced_by_children || parent.complete || parent.empty_complete) continue;
            const double mid = 0.5 * (parent.lo + parent.hi);
            if (!(mid > parent.lo + 1e-12 && mid < parent.hi - 1e-12)) continue;
            const bool parent_lower_bound_valid = parent.lower_bound_valid;
            const double parent_lower_bound = parent.lower_bound;
            const double parent_relaxation_lower_bound = parent.relaxation_lower_bound;

            std::array<FrontierIntervalRecord, 2> children;
            children[0].lo = parent.lo;
            children[0].hi = mid;
            children[1].lo = mid;
            children[1].hi = parent.hi;
            interval_records[parent_idx].replaced_by_children = true;
            for (FrontierIntervalRecord& child : children) {
                child.processed = true;
                child.lower_bound_valid = true;
                child.lower_bound = std::max(child.lo,
                    parent_lower_bound_valid ? parent_lower_bound : child.lo);
                child.relaxation_lower_bound = parent_relaxation_lower_bound;

                const int child_idx = static_cast<int>(interval_records.size());
                if (child.lo >= result.upper_bound - 1e-12) {
                    child.skipped = true;
                    child.complete = true;
                    child.lower_bound = child.lo;
                    result.notes.push_back("adaptive split pass " + std::to_string(split_pass)
                        + " child interval " + std::to_string(child_idx)
                        + " skipped because floor >= incumbent objective");
                    interval_records.push_back(child);
                    continue;
                }

                if (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0) {
                    const double relaxation_budget = (opt.frontier_relax_seconds > 0.0)
                        ? opt.frontier_relax_seconds
                        : ((opt.solve_time_limit > 0.0)
                            ? std::max(0.1, std::min(5.0, remainingSeconds() * 0.10))
                            : 5.0);
                    const CachedRelaxation cached_relax =
                        computeInventoryRelaxation(child.lo, child.hi,
                                                   relaxation_budget,
                                                   result.upper_bound, true);
                    const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
                        cached_relax.bound;
                    const double bound_elapsed = cached_relax.elapsed;
                    result.bound_time_seconds += bound_elapsed;
                    accumulateInventoryRelaxationStats(inv_relax);
                    if (inv_relax.note.find("route_mask_duration_load_relaxation=true") !=
                        std::string::npos) {
                        result.route_mask_time_seconds += bound_elapsed;
                    }
                    if (inv_relax.computed) {
                        child.relaxation_lower_bound = inv_relax.infeasible
                            ? result.upper_bound
                            : inv_relax.objective_lower_bound;
                        if (child.relaxation_lower_bound >
                            child.lower_bound + 1e-12) {
                            child.lower_bound_source =
                                "inventory_route_gini_relaxation";
                        }
                        child.lb_sources += "|inventory_route_gini_relaxation";
                        child.lower_bound =
                            std::max(child.lower_bound, child.relaxation_lower_bound);
                    }
                    result.notes.push_back("adaptive split pass " + std::to_string(split_pass)
                        + " child interval " + std::to_string(child_idx)
                        + " inventory relaxation: " + inv_relax.note
                        + ", bound_time=" + std::to_string(bound_elapsed));
                } else {
                    result.notes.push_back("adaptive split pass " + std::to_string(split_pass)
                        + " child interval " + std::to_string(child_idx)
                        + " inherited parent lower bound without relaxation because time expired");
                }

                if (child.lower_bound >= result.upper_bound - 1e-7) {
                    result.notes.push_back("adaptive split pass " + std::to_string(split_pass)
                        + " child interval " + std::to_string(child_idx)
                        + " bound-fathomed by inherited/relaxation lower bound");
                } else {
                    child.open_nodes = 1;
                }
                interval_records.push_back(child);
            }
        }
    }

    std::unordered_set<int> focused_retry_interval_ids;
    const auto focused_retry_start = std::chrono::steady_clock::now();
    if (!opt.frontier_focused_min_lb_retry) {
        result.focused_retry_stopped_reason = "disabled";
    }
    for (int adaptive_pass = 1;
         adaptive_pass <= (opt.frontier_focused_min_lb_retry
             ? std::max(0, opt.frontier_retry_passes) : 0);
         ++adaptive_pass) {
        auto collectRetryIndices = [&]() {
            std::vector<int> indices;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.replaced_by_children) continue;
                if (record.lo >= result.upper_bound - 1e-12) continue;
                if (!record.processed || !record.lower_bound_valid) {
                    indices.push_back(idx);
                    continue;
                }
                if (record.empty_complete || record.complete) continue;
                if (record.lower_bound < result.upper_bound - 1e-7) {
                    indices.push_back(idx);
                }
            }
            std::sort(indices.begin(), indices.end(),
                      [&](int lhs, int rhs) {
                          const FrontierIntervalRecord& a = interval_records[lhs];
                          const FrontierIntervalRecord& b = interval_records[rhs];
                          if (a.lower_bound_valid != b.lower_bound_valid) {
                              return !a.lower_bound_valid;
                          }
                          if (a.lower_bound_valid && b.lower_bound_valid &&
                              std::fabs(a.lower_bound - b.lower_bound) > 1e-10) {
                              return a.lower_bound < b.lower_bound;
                          }
                          const double aw = a.hi - a.lo;
                          const double bw = b.hi - b.lo;
                          if (std::fabs(aw - bw) > 1e-12) return aw > bw;
                          return lhs < rhs;
                      });
            return indices;
        };

        std::vector<int> retry_indices = collectRetryIndices();
        if (retry_indices.empty()) {
            result.focused_retry_stopped_reason = "no_unresolved_intervals";
            break;
        }
        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
            result.focused_retry_stopped_reason = "time_limit_before_retry";
            break;
        }

        const int retry_max_nodes = opt.frontier_retry_nodes > 0
            ? opt.frontier_retry_nodes
            : std::max({
                opt.max_branch_nodes,
                255,
                opt.max_branch_nodes * 4 + 3
            });
        result.notes.push_back("adaptive frontier pass " + std::to_string(adaptive_pass)
            + " retrying " + std::to_string(retry_indices.size())
            + " unresolved interval(s), retry_max_nodes="
            + std::to_string(retry_max_nodes)
            + ", retry_passes=" + std::to_string(std::max(0, opt.frontier_retry_passes))
            + ", scheduling=dynamic_lowest_valid_lower_bound_first"
            + ", time_budget=one_best_bound_interval_at_a_time");

        int retry_attempt = 0;
        const int max_dynamic_attempts =
            std::max(1, static_cast<int>(interval_records.size()) * 3);
        std::vector<int> deferred_until_next_pass(interval_records.size(), 0);
        while (retry_attempt < max_dynamic_attempts) {
            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
                result.notes.push_back("frontier time limit reached during adaptive pass "
                    + std::to_string(adaptive_pass));
                result.focused_retry_stopped_reason = "time_limit";
                break;
            }
            retry_indices = collectRetryIndices();
            retry_indices.erase(
                std::remove_if(retry_indices.begin(), retry_indices.end(),
                               [&](int idx) {
                                   return idx >= 0 &&
                                          idx < static_cast<int>(deferred_until_next_pass.size()) &&
                                          deferred_until_next_pass[idx] == adaptive_pass;
                               }),
                retry_indices.end());
            if (retry_indices.empty()) {
                result.focused_retry_stopped_reason = "all_candidates_deferred_or_closed";
                break;
            }

            const int idx = retry_indices.front();
            ++result.focused_retry_attempts;
            focused_retry_interval_ids.insert(idx);
            FrontierIntervalRecord& record = interval_records[idx];
            const double previous_record_lb = record.lower_bound;
            double early_stop_target = std::numeric_limits<double>::infinity();
            for (int later_pos = 1;
                 later_pos < static_cast<int>(retry_indices.size()); ++later_pos) {
                const FrontierIntervalRecord& later =
                    interval_records[retry_indices[later_pos]];
                if (!later.lower_bound_valid || !std::isfinite(later.lower_bound)) {
                    early_stop_target = 0.0;
                    break;
                }
                early_stop_target = std::min(early_stop_target, later.lower_bound);
            }
            if (!std::isfinite(early_stop_target) ||
                !record.lower_bound_valid ||
                early_stop_target <= record.lower_bound + 1e-9 ||
                early_stop_target >= result.upper_bound - 1e-7) {
                early_stop_target = std::numeric_limits<double>::infinity();
            }
            const double interval_budget = (opt.solve_time_limit > 0.0)
                ? std::max(0.1, remainingSeconds())
                : 0.0;
            ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
                instance, opt.lambda, record.hi, record.lo, interval_budget, 24,
                retry_max_nodes, &incumbent_routes, true, result.upper_bound,
                opt.gcap_warmstart_level, early_stop_target, opt.gcap_pricing_columns,
                opt.column_dominance, opt.column_dominance_mode,
                opt.projection_bound, opt.penalty_domain_tightening,
                opt.movement_domain_tightening, opt.support_duration_pruning,
                opt.support_duration_max_subset_size);
            result.nodes += tree.nodes_solved;
            result.columns += tree.generated_columns;
            result.pricing_calls += tree.pricing_calls;
            result.pricing_closed_nodes += tree.nodes_solved -
                (tree.complete ? 0 : std::min(1, tree.nodes_solved));
            result.cuts_added += tree.cuts_added;
            result.pricing_time_seconds += tree.pricing_time_seconds;
            result.master_time_seconds += tree.master_time_seconds;
            result.columns_generated_raw += tree.columns_generated_raw;
            result.columns_after_dominance += tree.columns_after_dominance;
            result.columns_dominated += tree.columns_dominated;
            result.dominance_time_seconds += tree.dominance_time_seconds;
            result.dominance_mode = tree.dominance_mode;
            result.dominance_exact_safe =
                result.dominance_exact_safe && tree.dominance_exact_safe;
            result.pricing_negative_columns_found += tree.pricing_negative_columns_found;
            result.pricing_negative_columns_inserted += tree.pricing_negative_columns_inserted;
            result.pricing_negative_columns_dominated += tree.pricing_negative_columns_dominated;
            result.pricing_completed_exactly =
                result.pricing_completed_exactly && tree.pricing_completed_exactly;
            accumulateTreeRound2Stats(tree);
            result.projection_bound_prunes += tree.projection_bound_prunes;
            result.projection_bound_time_seconds += tree.projection_bound_time_seconds;
            result.projection_bound_best_value =
                std::max(result.projection_bound_best_value,
                         tree.projection_bound_best_value);
            result.projection_bound_scope = tree.projection_bound_scope;
            result.domains_tightened_count += tree.domains_tightened_count;
            result.total_domain_width_before += tree.total_domain_width_before;
            result.total_domain_width_after += tree.total_domain_width_after;
            result.penalty_tightening_time_seconds +=
                tree.penalty_tightening_time_seconds;
            if (std::isfinite(tree.penalty_budget)) result.penalty_budget = tree.penalty_budget;
            record.processed = true;
            record.open_nodes = tree.open_nodes;
            if (tree.complete) {
                record.complete = true;
                record.empty_complete = !tree.has_integer_incumbent;
            }
            const double interval_lb = (tree.lower_bound_valid && std::isfinite(tree.global_lower_bound))
                ? std::max(record.lo, tree.global_lower_bound)
                : record.lo;
            if (std::isfinite(interval_lb)) {
                if (interval_lb > record.lower_bound + 1e-12) {
                    record.lower_bound_source = "branch_price_tree";
                }
                record.lower_bound = record.lower_bound_valid
                    ? std::max(record.lower_bound, interval_lb)
                    : interval_lb;
                record.lower_bound_valid = true;
                record.lb_sources += "|branch_price_tree";
            }
            record.tree_closed = tree.complete;
            record.pricing_closed = tree.pricing_closure_certified_exact;

            if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
                ebrp::Verification candidate =
                    ebrp::verifySolution(instance, tree.best_routes, opt.lambda);
                if (candidate.feasible &&
                    candidate.objective < result.upper_bound - 1e-9) {
                    result.routes = tree.best_routes;
                    result.verification = candidate;
                    result.final_inventory = candidate.final_inventory;
                    result.G = candidate.G;
                    result.P = candidate.P;
                    result.objective = candidate.objective;
                    result.upper_bound = candidate.objective;
                    incumbent_routes = tree.best_routes;
                    result.notes.push_back("adaptive frontier pass "
                        + std::to_string(adaptive_pass)
                        + " found improved incumbent in interval "
                        + std::to_string(idx)
                        + ", objective=" + std::to_string(candidate.objective));
                }
            }

            const bool certified_by_bound = record.lower_bound_valid &&
                record.lower_bound >= result.upper_bound - 1e-7;
            std::ostringstream retry_note;
            retry_note << "adaptive pass " << adaptive_pass
                       << " retry " << (retry_attempt + 1)
                       << " interval " << idx
                       << " [" << record.lo << "," << record.hi << "]"
                       << " complete=" << (tree.complete ? "true" : "false")
                       << ", lower_bound_valid=" << (tree.lower_bound_valid ? "true" : "false")
                       << ", certified_by_bound=" << (certified_by_bound ? "true" : "false")
                       << ", empty_interval=" << (record.empty_complete ? "true" : "false")
                       << ", has_incumbent=" << (tree.has_integer_incumbent ? "true" : "false")
                       << ", tree_lb=" << tree.global_lower_bound
                       << ", interval_lb=" << record.lower_bound
                       << ", inventory_relax_lb=" << record.relaxation_lower_bound
                       << ", resource_lb=" << tree.resource_objective_lower_bound
                       << ", incumbent_cutoff=" << result.upper_bound
                       << ", early_stop_target=" << early_stop_target
                       << ", nodes=" << tree.nodes_solved
                       << ", columns=" << tree.generated_columns
                       << ", pricing_calls=" << tree.pricing_calls
                       << ", pricing_time=" << tree.pricing_time_seconds
                       << ", master_time=" << tree.master_time_seconds
                       << ", bound_time=0"
                       << ", cuts_added=" << tree.cuts_added
                       << ", open_nodes=" << tree.open_nodes;
            result.notes.push_back(retry_note.str());

            const bool made_progress =
                tree.complete ||
                (record.lower_bound_valid && std::isfinite(record.lower_bound) &&
                 record.lower_bound > previous_record_lb + 1e-8);
            if (made_progress) {
                ++result.focused_retry_lb_improvements;
            }
            if (!made_progress && idx >= 0 &&
                idx < static_cast<int>(deferred_until_next_pass.size())) {
                deferred_until_next_pass[idx] = adaptive_pass;
                result.notes.push_back("adaptive pass "
                    + std::to_string(adaptive_pass)
                    + " defers interval " + std::to_string(idx)
                    + " for the remainder of this pass because retry made no valid lower-bound progress");
                result.focused_retry_stopped_reason = "no_valid_lower_bound_progress";
                break;
            }
            ++retry_attempt;
        }
    }
    if (opt.frontier_focused_min_lb_retry) {
        result.focused_retry_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - focused_retry_start).count();
        result.focused_retry_intervals =
            static_cast<int>(focused_retry_interval_ids.size());
        if (result.focused_retry_stopped_reason.empty()) {
            result.focused_retry_stopped_reason = "completed_retry_passes";
        }
    }

    if (opt.frontier_final_closure &&
        (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
        std::vector<char> final_deferred(interval_records.size(), 0);
        auto collectFinalClosureIndices = [&]() {
            std::vector<int> indices;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                if (idx < static_cast<int>(final_deferred.size()) && final_deferred[idx]) {
                    continue;
                }
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.replaced_by_children) continue;
                if (record.lo >= result.upper_bound - 1e-12) continue;
                if (record.empty_complete || record.complete) continue;
                if (!record.processed || !record.lower_bound_valid ||
                    record.lower_bound < result.upper_bound - 1e-7) {
                    indices.push_back(idx);
                }
            }
            std::sort(indices.begin(), indices.end(),
                      [&](int lhs, int rhs) {
                          const FrontierIntervalRecord& a = interval_records[lhs];
                          const FrontierIntervalRecord& b = interval_records[rhs];
                          const double agap = a.lower_bound_valid
                              ? std::max(0.0, result.upper_bound - a.lower_bound)
                              : std::numeric_limits<double>::infinity();
                          const double bgap = b.lower_bound_valid
                              ? std::max(0.0, result.upper_bound - b.lower_bound)
                              : std::numeric_limits<double>::infinity();
                          if (std::fabs(agap - bgap) > 1e-10) return agap < bgap;
                          const double aw = a.hi - a.lo;
                          const double bw = b.hi - b.lo;
                          if (std::fabs(aw - bw) > 1e-12) return aw < bw;
                          return lhs < rhs;
                      });
            return indices;
        };

        std::vector<int> final_indices = collectFinalClosureIndices();
        result.notes.push_back("final closure phase enabled: intervals="
            + std::to_string(final_indices.size())
            + ", max_nodes=" + std::to_string(std::max(1, opt.frontier_final_nodes))
            + ", scheduling=smallest_gap_contribution_first"
            + ", objective_cutoff=" + std::to_string(result.upper_bound));

        int final_attempt = 0;
        while (!final_indices.empty() &&
               (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
            const int idx = final_indices.front();
            if (idx < 0 || idx >= static_cast<int>(interval_records.size())) break;
            FrontierIntervalRecord& record = interval_records[idx];
            const double previous_lb = record.lower_bound;
            const double gap_contribution = record.lower_bound_valid
                ? std::max(0.0, result.upper_bound - record.lower_bound)
                : std::numeric_limits<double>::infinity();
            result.notes.push_back("final closure attempt " + std::to_string(final_attempt + 1)
                + " interval " + std::to_string(idx)
                + " [" + std::to_string(record.lo) + "," + std::to_string(record.hi) + "]"
                + ", current_lb=" + std::to_string(record.lower_bound)
                + ", incumbent_cutoff=" + std::to_string(result.upper_bound)
                + ", gap_contribution=" + std::to_string(gap_contribution));

            if (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0) {
                const double relaxation_budget = (opt.frontier_relax_seconds > 0.0)
                    ? opt.frontier_relax_seconds
                    : ((opt.solve_time_limit > 0.0)
                        ? std::max(0.1, std::min(10.0, remainingSeconds() * 0.15))
                        : 10.0);
                const CachedRelaxation cached_relax =
                    computeInventoryRelaxation(record.lo, record.hi,
                                               relaxation_budget,
                                               result.upper_bound, true);
                const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
                    cached_relax.bound;
                const double bound_elapsed = cached_relax.elapsed;
                result.bound_time_seconds += bound_elapsed;
                accumulateInventoryRelaxationStats(inv_relax);
                if (inv_relax.note.find("route_mask_duration_load_relaxation=true") !=
                    std::string::npos) {
                    result.route_mask_time_seconds += bound_elapsed;
                }
                if (inv_relax.computed) {
                    record.processed = true;
                    record.lower_bound_valid = true;
                    record.relaxation_lower_bound = inv_relax.infeasible
                        ? result.upper_bound
                        : std::max(record.relaxation_lower_bound,
                                   inv_relax.objective_lower_bound);
                    if (record.relaxation_lower_bound >
                        record.lower_bound + 1e-12) {
                        record.lower_bound_source =
                            "inventory_route_gini_relaxation";
                    }
                    record.lb_sources += "|inventory_route_gini_relaxation";
                    record.lower_bound =
                        std::max(record.lower_bound, record.relaxation_lower_bound);
                }
                result.notes.push_back("final closure interval "
                    + std::to_string(idx)
                    + " inventory relaxation: " + inv_relax.note
                    + ", bound_time=" + std::to_string(bound_elapsed));
            }

            if (record.lower_bound_valid &&
                record.lower_bound >= result.upper_bound - 1e-7) {
                result.notes.push_back("final closure interval "
                    + std::to_string(idx)
                    + " bound-fathomed by refreshed inventory/route/Gini relaxation");
                final_indices = collectFinalClosureIndices();
                ++final_attempt;
                continue;
            }

            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) break;
            const double interval_budget = (opt.solve_time_limit > 0.0)
                ? std::max(0.1, remainingSeconds() /
                    std::max(1, static_cast<int>(final_indices.size())))
                : 0.0;
            ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
                instance, opt.lambda, record.hi, record.lo, interval_budget, 32,
                std::max(1, opt.frontier_final_nodes), &incumbent_routes, true,
                result.upper_bound, opt.gcap_warmstart_level,
                std::numeric_limits<double>::infinity(), opt.gcap_pricing_columns,
                opt.column_dominance, opt.column_dominance_mode,
                opt.projection_bound, opt.penalty_domain_tightening,
                opt.movement_domain_tightening, opt.support_duration_pruning,
                opt.support_duration_max_subset_size);
            result.nodes += tree.nodes_solved;
            result.columns += tree.generated_columns;
            result.pricing_calls += tree.pricing_calls;
            result.pricing_closed_nodes += tree.nodes_solved -
                (tree.complete ? 0 : std::min(1, tree.nodes_solved));
            result.cuts_added += tree.cuts_added;
            result.pricing_time_seconds += tree.pricing_time_seconds;
            result.master_time_seconds += tree.master_time_seconds;
            result.columns_generated_raw += tree.columns_generated_raw;
            result.columns_after_dominance += tree.columns_after_dominance;
            result.columns_dominated += tree.columns_dominated;
            result.dominance_time_seconds += tree.dominance_time_seconds;
            result.dominance_mode = tree.dominance_mode;
            result.dominance_exact_safe =
                result.dominance_exact_safe && tree.dominance_exact_safe;
            result.pricing_negative_columns_found += tree.pricing_negative_columns_found;
            result.pricing_negative_columns_inserted += tree.pricing_negative_columns_inserted;
            result.pricing_negative_columns_dominated += tree.pricing_negative_columns_dominated;
            result.pricing_completed_exactly =
                result.pricing_completed_exactly && tree.pricing_completed_exactly;
            accumulateTreeRound2Stats(tree);
            result.projection_bound_prunes += tree.projection_bound_prunes;
            result.projection_bound_time_seconds += tree.projection_bound_time_seconds;
            result.projection_bound_best_value =
                std::max(result.projection_bound_best_value,
                         tree.projection_bound_best_value);
            result.projection_bound_scope = tree.projection_bound_scope;
            result.domains_tightened_count += tree.domains_tightened_count;
            result.total_domain_width_before += tree.total_domain_width_before;
            result.total_domain_width_after += tree.total_domain_width_after;
            result.penalty_tightening_time_seconds +=
                tree.penalty_tightening_time_seconds;
            if (std::isfinite(tree.penalty_budget)) result.penalty_budget = tree.penalty_budget;
            record.processed = true;
            record.open_nodes = tree.open_nodes;
            if (tree.complete) {
                record.complete = true;
                record.empty_complete = !tree.has_integer_incumbent;
            }
            if (tree.lower_bound_valid && std::isfinite(tree.global_lower_bound)) {
                record.lower_bound_valid = true;
                const double candidate_lb =
                    std::max(record.lo, tree.global_lower_bound);
                if (candidate_lb > record.lower_bound + 1e-12) {
                    record.lower_bound_source = "branch_price_tree";
                }
                record.lower_bound =
                    std::max(record.lower_bound, candidate_lb);
                record.lb_sources += "|branch_price_tree";
            }
            record.tree_closed = tree.complete;
            record.pricing_closed = tree.pricing_closure_certified_exact;
            if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
                ebrp::Verification candidate =
                    ebrp::verifySolution(instance, tree.best_routes, opt.lambda);
                if (candidate.feasible &&
                    candidate.objective < result.upper_bound - 1e-9) {
                    result.routes = tree.best_routes;
                    result.verification = candidate;
                    result.final_inventory = candidate.final_inventory;
                    result.G = candidate.G;
                    result.P = candidate.P;
                    result.objective = candidate.objective;
                    result.upper_bound = candidate.objective;
                    incumbent_routes = tree.best_routes;
                    result.notes.push_back("final closure found improved BPC incumbent in interval "
                        + std::to_string(idx)
                        + ", objective=" + std::to_string(candidate.objective));
                }
            }
            const bool certified_by_bound = record.lower_bound_valid &&
                record.lower_bound >= result.upper_bound - 1e-7;
            std::ostringstream note;
            note << "final closure interval " << idx
                 << " [" << record.lo << "," << record.hi << "]"
                 << " complete=" << (tree.complete ? "true" : "false")
                 << ", lower_bound_valid=" << (tree.lower_bound_valid ? "true" : "false")
                 << ", certified_by_bound=" << (certified_by_bound ? "true" : "false")
                 << ", tree_lb=" << tree.global_lower_bound
                 << ", previous_lb=" << previous_lb
                 << ", interval_lb=" << record.lower_bound
                 << ", incumbent_cutoff=" << result.upper_bound
                 << ", nodes=" << tree.nodes_solved
                 << ", open_nodes=" << tree.open_nodes
                 << ", columns=" << tree.generated_columns
                 << ", pricing_calls=" << tree.pricing_calls
                 << ", pricing_time=" << tree.pricing_time_seconds
                 << ", master_time=" << tree.master_time_seconds
                 << ", cuts_added=" << tree.cuts_added
                 << ", reason_if_open="
                 << (certified_by_bound || tree.complete
                     ? "closed_or_fathomed"
                     : "exact branch-price tree still open below incumbent cutoff");
            result.notes.push_back(note.str());

            const bool made_progress =
                tree.complete ||
                certified_by_bound ||
                (record.lower_bound_valid && std::isfinite(record.lower_bound) &&
                 record.lower_bound > previous_lb + 1e-8);
            if (!made_progress && idx >= 0 &&
                idx < static_cast<int>(final_deferred.size())) {
                final_deferred[idx] = 1;
                result.notes.push_back("final closure defers interval "
                    + std::to_string(idx)
                    + " because the focused branch-price pass made no valid lower-bound progress");
            }

            final_indices = collectFinalClosureIndices();
            ++final_attempt;
        }
    }

    bool all_certified = true;
    bool full_objective_range = result.frontier_covers_all_improving_gini_values;
    int closed_intervals = 0;
    int bound_certified_intervals = 0;
    int skipped_intervals = 0;
    int unresolved_intervals = 0;
    int invalid_bound_intervals = 0;
    int relevant_intervals = 0;
    int unprocessed_intervals = 0;
    long long final_open_nodes = 0;
    double global_lb = result.upper_bound; // G >= incumbent objective cannot improve the incumbent.
    std::string global_lb_source = "incumbent_cutoff";
    for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
        FrontierIntervalRecord& record = interval_records[idx];
        if (record.replaced_by_children) continue;
        if (!record.lower_bound_valid || !std::isfinite(record.lower_bound)) {
            record.lower_bound = std::max(0.0, record.lo);
            record.lower_bound_valid = true;
            record.lower_bound_source = "gamma_floor";
        }
        if (record.processed && record.complete && record.lower_bound_valid) {
            ++closed_intervals;
        } else if (record.processed && record.lower_bound_valid &&
                   record.lower_bound >= result.upper_bound - 1e-7) {
            ++bound_certified_intervals;
            record.bound_fathomed = true;
        }
        if (record.lo >= result.upper_bound - 1e-12) {
            if (!record.processed) ++skipped_intervals;
            std::ostringstream ledger;
            ledger << "frontier_interval_ledger: interval_id=" << idx
                   << ", range=[" << record.lo << "," << record.hi << "]"
                   << ", status=skipped_floor_ge_incumbent"
                   << ", interval_lb=" << record.lower_bound
                   << ", cheap_prepass_lb=" << record.cheap_prepass_lower_bound
                   << ", cheap_sources=" << record.cheap_prepass_sources
                   << ", lb_sources=" << record.lb_sources
                   << ", complete_or_fathomed=true"
                   << ", open_nodes=" << record.open_nodes
                   << ", pricing_closed=" << (record.pricing_closed ? "true" : "false");
            result.notes.push_back(ledger.str());
            continue;
        }
        ++relevant_intervals;
        if (!record.processed) {
            all_certified = false;
            ++unresolved_intervals;
            ++unprocessed_intervals;
        }
        if (record.empty_complete) {
            std::ostringstream ledger;
            ledger << "frontier_interval_ledger: interval_id=" << idx
                   << ", range=[" << record.lo << "," << record.hi << "]"
                   << ", status=empty_closed"
                   << ", interval_lb=" << record.lower_bound
                   << ", cheap_prepass_lb=" << record.cheap_prepass_lower_bound
                   << ", cheap_sources=" << record.cheap_prepass_sources
                   << ", lb_sources=" << record.lb_sources
                   << ", complete_or_fathomed=true"
                   << ", open_nodes=" << record.open_nodes
                   << ", pricing_closed=" << (record.pricing_closed ? "true" : "false");
            result.notes.push_back(ledger.str());
            continue;
        }
        if (record.lower_bound_valid && std::isfinite(record.lower_bound)) {
            if (record.lower_bound < global_lb) {
                global_lb = record.lower_bound;
                global_lb_source = record.lower_bound_source;
            }
        } else {
            all_certified = false;
            ++invalid_bound_intervals;
            continue;
        }
        if (!record.complete && record.lower_bound < result.upper_bound - 1e-7) {
            all_certified = false;
            if (record.processed) ++unresolved_intervals;
            final_open_nodes += record.open_nodes;
        }
        std::string status = "unresolved";
        if (record.complete) status = "branch_price_closed";
        else if (record.bound_fathomed ||
                 record.lower_bound >= result.upper_bound - 1e-7) {
            status = "bound_fathomed";
        } else if (!record.processed) {
            status = "unprocessed_relevant";
        }
        std::ostringstream ledger;
        ledger << "frontier_interval_ledger: interval_id=" << idx
               << ", range=[" << record.lo << "," << record.hi << "]"
               << ", status=" << status
               << ", interval_lb=" << record.lower_bound
               << ", cheap_prepass_lb=" << record.cheap_prepass_lower_bound
               << ", cheap_sources=" << record.cheap_prepass_sources
               << ", lb_source=" << record.lower_bound_source
               << ", lb_sources=" << record.lb_sources
               << ", complete_or_fathomed="
               << ((record.complete || record.bound_fathomed ||
                    record.lower_bound >= result.upper_bound - 1e-7) ? "true" : "false")
               << ", open_nodes=" << record.open_nodes
               << ", pricing_closed=" << (record.pricing_closed ? "true" : "false");
        result.notes.push_back(ledger.str());
    }
    result.unresolved_intervals = unresolved_intervals;
    result.invalid_bound_intervals = invalid_bound_intervals;
    result.open_nodes = final_open_nodes;
    result.lower_bound = std::isfinite(global_lb) ? global_lb : 0.0;
    result.frontier_relevant_intervals = relevant_intervals;
    result.frontier_min_interval_lower_bound = result.lower_bound;
    result.frontier_lower_bound_source = global_lb_source;
    result.frontier_unprocessed_interval_count = unprocessed_intervals;
    result.frontier_bound_fathomed_interval_count = bound_certified_intervals;
    result.frontier_tree_closed_interval_count = closed_intervals;
    result.gap = (std::fabs(result.upper_bound) > 1e-12)
        ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
        : 0.0;
    result.runtime_seconds = elapsedSeconds();
    result.wall_time_seconds = result.runtime_seconds;
    result.aggregate_worker_time_seconds = result.pricing_time_seconds +
        result.master_time_seconds + result.bound_time_seconds;
    if (!std::isfinite(result.pricing_best_reduced_cost_any)) {
        result.pricing_best_reduced_cost_any = 0.0;
    }
    if (!std::isfinite(result.pricing_best_new_reduced_cost)) {
        result.pricing_best_new_reduced_cost = 0.0;
    }
    std::ostringstream certification_note;
    certification_note << "frontier certification summary: closed_intervals=" << closed_intervals
                       << ", bound_certified_intervals=" << bound_certified_intervals
                       << ", skipped_intervals=" << skipped_intervals
                       << ", relevant_intervals=" << relevant_intervals
                       << ", frontier_min_interval_lower_bound=" << result.lower_bound
                       << ", frontier_lower_bound_source=" << global_lb_source
                       << ", unresolved_intervals=" << unresolved_intervals
                       << ", invalid_bound_intervals=" << invalid_bound_intervals
                       << ", final_full_objective_range="
                       << (full_objective_range ? "true" : "false")
                       << ", frontier_range_certificate_scope="
                       << result.frontier_range_certificate_scope
                       << ", relevant_gini_upper_for_improvement="
                       << result.relevant_gini_upper_for_improvement
                       << ", covered_gini_upper_bound="
                       << result.covered_gini_upper_bound;
    result.notes.push_back(certification_note.str());

    if (all_certified && full_objective_range &&
        result.lower_bound >= result.upper_bound - 1e-7) {
        const double raw_frontier_lower_bound = result.lower_bound;
        result.status = "optimal";
        result.certificate = "gamma-frontier certificate: every relevant Gini interval was either closed with exact pricing or fathomed by a valid interval lower bound above the verified incumbent objective";
        result.notes.push_back("certified frontier lower bound before tolerance normalization="
            + std::to_string(raw_frontier_lower_bound)
            + ", certificate_tolerance=1e-7");
        result.lower_bound = result.objective;
        result.upper_bound = result.objective;
        result.gap = 0.0;
    } else if (all_certified) {
        result.status = "gcap_frontier_bound_complete";
        result.certificate = full_objective_range
            ? "gamma-frontier diagnostic certified every requested interval, but the aggregated lower bound does not prove the incumbent globally optimal"
            : "gamma-frontier diagnostic certified only a capped or partial Gini range; this is not an original-problem optimality certificate";
    } else {
        result.status = "gcap_frontier_not_closed";
        result.certificate = "gamma-frontier diagnostic still has relevant intervals that are neither closed nor fathomed by a valid lower bound; do not treat as an optimality certificate";
    }
    return result;
}

} // namespace

int main(int argc, char** argv) {
    try {
        ebrp::SolveOptions opt = parseArgs(argc, argv);
        std::vector<std::filesystem::path> files = ebrp::collectInputFiles(opt.input_path);
        std::vector<ebrp::SolveResult> results;
        for (const auto& file : files) {
            ebrp::Instance instance = ebrp::parseInstanceFile(
                file, opt.total_time_limit, opt.pickup_time, opt.drop_time);
            if (opt.method == "tailored") {
                results.push_back(ebrp::solveTailoredExact(instance, opt));
            } else if (opt.method == "cplex") {
                results.push_back(ebrp::solveCplexBaseline(instance, opt));
            } else if (opt.method == "pricing") {
                results.push_back(solvePricingDiagnostic(instance, opt));
            } else if (opt.method == "pricing-branch") {
                results.push_back(solveBranchPricingDiagnostic(instance, opt));
            } else if (opt.method == "cuts") {
                results.push_back(solveCutsDiagnostic(instance, opt));
            } else if (opt.method == "branching") {
                results.push_back(solveBranchingDiagnostic(instance, opt));
            } else if (opt.method == "master") {
                results.push_back(solveMasterDiagnostic(instance, opt));
            } else if (opt.method == "cg") {
                results.push_back(solveColumnGenerationDiagnostic(instance, opt));
            } else if (opt.method == "gcap-cg") {
                results.push_back(solveGiniCapColumnGenerationDiagnostic(instance, opt));
            } else if (opt.method == "gcap-branch") {
                results.push_back(solveGiniCapBranchProbeDiagnostic(instance, opt));
            } else if (opt.method == "gcap-tree") {
                results.push_back(solveGiniCapTreeDiagnostic(instance, opt));
            } else if (opt.method == "gcap-frontier") {
                results.push_back(solveGiniFrontierDiagnostic(instance, opt));
            } else if (opt.method == "dominance-test") {
                results.push_back(solveDominanceDiagnostic(instance, opt));
            } else if (opt.method == "support-pruning-test") {
                results.push_back(solveSupportPruningDiagnostic(instance, opt));
            } else if (opt.method == "route-mask-support-test") {
                results.push_back(solveRouteMaskSupportDiagnostic(instance, opt));
            } else if (opt.method == "incumbent-import-test") {
                results.push_back(solveIncumbentImportDiagnostic(instance, opt));
            } else {
                throw std::runtime_error("Unsupported method: " + opt.method);
            }
            auto& r = results.back();
            if (r.result_file.empty()) r.result_file = opt.out_path;
            if (r.log_file.empty()) r.log_file = opt.log_path;
            std::cout << r.instance_name << " " << r.method << " " << r.status
                      << " obj=" << r.objective << " runtime=" << r.runtime_seconds
                      << " columns=" << r.columns << "\n";
        }
        const std::string json = ebrp::resultsToJson(results);
        if (!opt.out_path.empty()) ebrp::writeTextFile(opt.out_path, json);
        else std::cout << json;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ExactEBRP error: " << e.what() << "\n";
        usage();
        return 1;
    }
}
