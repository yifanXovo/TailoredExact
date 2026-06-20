#include "Result.hpp"

#include <cmath>
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {

std::string jsonEscape(const std::string& s) {
    std::ostringstream out;
    for (char ch : s) {
        switch (ch) {
            case '\\': out << "\\\\"; break;
            case '"': out << "\\\""; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default: out << ch; break;
        }
    }
    return out.str();
}

template <class T>
void writeVector(std::ostringstream& out, const std::vector<T>& values) {
    out << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) out << ", ";
        out << values[i];
    }
    out << "]";
}

void writeStringVector(std::ostringstream& out, const std::vector<std::string>& values) {
    out << "[";
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) out << ", ";
        out << "\"" << jsonEscape(values[i]) << "\"";
    }
    out << "]";
}

void writeVerification(std::ostringstream& out, const Verification& v) {
    out << "{";
    out << "\"feasible\": " << (v.feasible ? "true" : "false") << ", ";
    out << "\"routes_start_end_depot\": " << (v.routes_start_end_depot ? "true" : "false") << ", ";
    out << "\"station_disjoint\": " << (v.station_disjoint ? "true" : "false") << ", ";
    out << "\"load_feasible\": " << (v.load_feasible ? "true" : "false") << ", ";
    out << "\"station_feasible\": " << (v.station_feasible ? "true" : "false") << ", ";
    out << "\"duration_feasible\": " << (v.duration_feasible ? "true" : "false") << ", ";
    out << "\"objective_matches\": " << (v.objective_matches ? "true" : "false") << ", ";
    out << "\"route_travel_time\": "; writeVector(out, v.route_travel_time); out << ", ";
    out << "\"route_operation_time\": "; writeVector(out, v.route_operation_time); out << ", ";
    out << "\"route_duration\": "; writeVector(out, v.route_duration); out << ", ";
    out << "\"final_inventories\": "; writeVector(out, v.final_inventory); out << ", ";
    out << "\"G\": " << v.G << ", ";
    out << "\"P\": " << v.P << ", ";
    out << "\"objective\": " << v.objective << ", ";
    out << "\"errors\": "; writeStringVector(out, v.errors);
    out << "}";
}

std::string lowerCopy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s;
}

std::string auditText(const SolveResult& result) {
    std::ostringstream out;
    out << result.method << "\n" << result.status << "\n" << result.certificate << "\n";
    for (const std::string& note : result.notes) out << note << "\n";
    return lowerCopy(out.str());
}

bool containsText(const std::string& haystack, const std::string& needle) {
    return lowerCopy(haystack).find(lowerCopy(needle)) != std::string::npos;
}

bool nearlyEqual(double a, double b, double tol = 1e-7) {
    return std::fabs(a - b) <= tol * std::max({1.0, std::fabs(a), std::fabs(b)});
}

} // namespace

ObjectiveParts computeObjectiveParts(const Instance& instance,
                                     const std::vector<int>& final_inventory,
                                     double lambda) {
    ObjectiveParts out;
    std::vector<double> r(instance.V + 1, 0.0);
    for (int i = 1; i <= instance.V; ++i) {
        r[i] = static_cast<double>(final_inventory[i]) / static_cast<double>(instance.target[i]);
        out.S += r[i];
        out.P += instance.weights[i] * std::fabs(r[i] - 1.0);
    }
    for (int i = 1; i <= instance.V; ++i) {
        for (int j = i + 1; j <= instance.V; ++j) {
            out.H += std::fabs(r[i] - r[j]);
        }
    }
    out.G = (out.S > 0.0) ? out.H / (static_cast<double>(instance.V) * out.S) : 0.0;
    out.objective = out.G + lambda * out.P;
    return out;
}

std::string inferMethodScope(const SolveResult& result) {
    const std::string method = lowerCopy(result.method);
    const std::string text = auditText(result);
    if (method == "gcap-frontier" || containsText(method, "full route-load bpc") ||
        containsText(method, "route-load bpc")) {
        return "original_bpc";
    }
    if (method == "tailored") {
        return "original_compact";
    }
    if (method == "cplex") {
        if (containsText(text, "original-style") || containsText(text, "plain")) {
            return "plain_cplex";
        }
        return "original_compact";
    }
    if (method == "gcap-cg" || method == "gcap-tree" || method == "master" ||
        containsText(method, "fixed-cap") || containsText(method, "gini-cap")) {
        return "subproblem";
    }
    if (method == "pricing" || method == "pricing-branch" || method == "cuts" ||
        method == "branching" || method == "cg" || method == "gcap-branch") {
        return "diagnostic";
    }
    if (containsText(text, "restricted path pool") || containsText(text, "restricted column")) {
        return "subproblem";
    }
    return "diagnostic";
}

bool inferSolvesOriginalObjective(const SolveResult& result) {
    const std::string scope = inferMethodScope(result);
    return scope == "original_bpc" || scope == "original_compact" || scope == "plain_cplex";
}

bool inferIsBpc(const SolveResult& result) {
    const std::string method = lowerCopy(result.method);
    return method == "gcap-frontier" || containsText(method, "full route-load bpc");
}

std::string inferCertificateType(const SolveResult& result) {
    const std::string method = lowerCopy(result.method);
    const std::string text = auditText(result);
    if (method == "gcap-frontier") {
        return result.status == "optimal"
            ? "full_gini_frontier_route_load_bpc"
            : "incomplete_gini_frontier_route_load_bpc";
    }
    if (method == "tailored") {
        if (containsText(text, "strengthened compact exact fallback")) {
            return "compact_strengthened_fallback";
        }
        if (containsText(text, "all feasible route-load columns")) {
            return "complete_route_load_enumeration_master";
        }
        if (containsText(text, "inventory-route search") ||
            containsText(text, "final-inventory vectors")) {
            return "inventory_route_search";
        }
        return "tailored_portfolio_incomplete";
    }
    if (method == "cplex") {
        if (containsText(text, "original-style") || containsText(text, "plain")) {
            return "plain_cplex_compact_mip";
        }
        if (containsText(text, "strengthened")) {
            return "strengthened_compact_cplex_mip";
        }
        return "compact_cplex_mip";
    }
    if (method == "gcap-cg") return "fixed_gini_cap_root_column_generation";
    if (method == "gcap-tree") {
        return containsText(text, "interval")
            ? "fixed_gini_interval_branch_price_tree"
            : "fixed_gini_cap_branch_price_tree";
    }
    if (method == "gcap-branch") return "fixed_gini_cap_one_level_ryan_foster_probe";
    if (method == "master") return "restricted_column_pool_master";
    if (method == "pricing") return "route_load_pricing_oracle";
    if (method == "pricing-branch") return "route_load_pricing_branch_probe";
    if (method == "cuts") return "cut_separation_diagnostic";
    if (method == "branching") return "branching_candidate_diagnostic";
    if (method == "cg") return "coverage_column_generation_diagnostic";
    if (containsText(text, "restricted path pool")) return "restricted_path_pool";
    return "none";
}

std::string inferStopReason(const SolveResult& result) {
    const std::string text = auditText(result);
    if (result.status == "optimal") return "optimality_proven";
    if (containsText(result.status, "verification_failed")) return "verification_failed";
    if (containsText(result.status, "error")) return "error";
    if (containsText(result.status, "unsupported")) return "unsupported";
    if (containsText(result.status, "invalid")) return "invalid_input";
    if (containsText(result.status, "time") || containsText(text, "time limit")) return "time_limit";
    if (containsText(result.status, "no_incumbent")) return "no_incumbent";
    if (containsText(result.status, "not_closed")) return "not_closed";
    if (containsText(result.status, "not_certified")) return "not_certified";
    if (containsText(result.status, "bound_complete")) return "bound_complete_not_global";
    if (containsText(result.status, "complete")) return "subproblem_complete";
    return result.status.empty() ? "unknown" : result.status;
}

bool inferVerifierPassed(const SolveResult& result) {
    return result.verification.feasible &&
           result.verification.objective_matches &&
           result.verification.errors.empty();
}

bool inferCertifiedOriginalProblem(const SolveResult& result) {
    if (result.status != "optimal") return false;
    if (!inferSolvesOriginalObjective(result)) return false;
    if (!inferVerifierPassed(result)) return false;
    if (result.gap > 1e-7) return false;
    if (!nearlyEqual(result.lower_bound, result.upper_bound)) return false;
    if (!nearlyEqual(result.objective, result.upper_bound)) return false;
    if (inferIsBpc(result)) {
        if (result.unresolved_intervals != 0 || result.invalid_bound_intervals != 0) return false;
        if (result.pricing_closed_nodes <= 0 && result.objective > 1e-12) return false;
    }
    return true;
}

std::string resultToJson(const SolveResult& result) {
    std::ostringstream out;
    out << std::setprecision(12);
    const double wall_time = result.wall_time_seconds > 0.0
        ? result.wall_time_seconds : result.runtime_seconds;
    const double aggregate_worker_time = result.aggregate_worker_time_seconds > 0.0
        ? result.aggregate_worker_time_seconds
        : (result.pricing_time_seconds + result.master_time_seconds +
           result.bound_time_seconds);
    out << "{\n";
    out << "  \"instance_name\": \"" << jsonEscape(result.instance_name) << "\",\n";
    out << "  \"input_path\": \"" << jsonEscape(result.input_path) << "\",\n";
    out << "  \"result_file\": \"" << jsonEscape(result.result_file) << "\",\n";
    out << "  \"log_file\": \"" << jsonEscape(result.log_file) << "\",\n";
    out << "  \"method\": \"" << jsonEscape(result.method) << "\",\n";
    out << "  \"method_scope\": \"" << jsonEscape(inferMethodScope(result)) << "\",\n";
    out << "  \"solves_original_objective\": "
        << (inferSolvesOriginalObjective(result) ? "true" : "false") << ",\n";
    out << "  \"is_bpc\": " << (inferIsBpc(result) ? "true" : "false") << ",\n";
    out << "  \"certificate_type\": \"" << jsonEscape(inferCertificateType(result)) << "\",\n";
    out << "  \"status\": \"" << jsonEscape(result.status) << "\",\n";
    out << "  \"certificate\": \"" << jsonEscape(result.certificate) << "\",\n";
    out << "  \"objective\": " << result.objective << ",\n";
    out << "  \"G\": " << result.G << ",\n";
    out << "  \"P\": " << result.P << ",\n";
    out << "  \"lower_bound\": " << result.lower_bound << ",\n";
    out << "  \"upper_bound\": " << result.upper_bound << ",\n";
    out << "  \"gap\": " << result.gap << ",\n";
    out << "  \"runtime_seconds\": " << result.runtime_seconds << ",\n";
    out << "  \"wall_time_seconds\": " << wall_time << ",\n";
    out << "  \"aggregate_worker_time_seconds\": " << aggregate_worker_time << ",\n";
    out << "  \"stop_reason\": \"" << jsonEscape(inferStopReason(result)) << "\",\n";
    out << "  \"verifier_passed\": " << (inferVerifierPassed(result) ? "true" : "false") << ",\n";
    out << "  \"unresolved_intervals\": " << result.unresolved_intervals << ",\n";
    out << "  \"invalid_bound_intervals\": " << result.invalid_bound_intervals << ",\n";
    out << "  \"pricing_closed_nodes\": " << result.pricing_closed_nodes << ",\n";
    out << "  \"open_nodes\": " << result.open_nodes << ",\n";
    out << "  \"certified_original_problem\": "
        << (inferCertifiedOriginalProblem(result) ? "true" : "false") << ",\n";
    out << "  \"nodes\": " << result.nodes << ",\n";
    out << "  \"columns\": " << result.columns << ",\n";
    out << "  \"pricing_calls\": " << result.pricing_calls << ",\n";
    out << "  \"cuts_added\": " << result.cuts_added << ",\n";
    out << "  \"bpc_workers\": " << result.bpc_workers << ",\n";
    out << "  \"pricing_threads\": " << result.pricing_threads << ",\n";
    out << "  \"parallel_frontier\": " << (result.parallel_frontier ? "true" : "false") << ",\n";
    out << "  \"parallel_nodes\": " << (result.parallel_nodes ? "true" : "false") << ",\n";
    out << "  \"parallel_tasks\": " << result.parallel_tasks << ",\n";
    out << "  \"pricing_time_seconds\": " << result.pricing_time_seconds << ",\n";
    out << "  \"master_time_seconds\": " << result.master_time_seconds << ",\n";
    out << "  \"bound_time_seconds\": " << result.bound_time_seconds << ",\n";
    out << "  \"route_mask_time_seconds\": " << result.route_mask_time_seconds << ",\n";
    out << "  \"columns_generated_raw\": " << result.columns_generated_raw << ",\n";
    out << "  \"columns_after_dominance\": " << result.columns_after_dominance << ",\n";
    out << "  \"columns_dominated\": " << result.columns_dominated << ",\n";
    out << "  \"dominance_time_seconds\": " << result.dominance_time_seconds << ",\n";
    out << "  \"dominance_mode\": \"" << jsonEscape(result.dominance_mode) << "\",\n";
    out << "  \"dominance_exact_safe\": "
        << (result.dominance_exact_safe ? "true" : "false") << ",\n";
    out << "  \"projection_bound_prunes\": " << result.projection_bound_prunes << ",\n";
    out << "  \"projection_bound_time_seconds\": " << result.projection_bound_time_seconds << ",\n";
    out << "  \"projection_bound_best_value\": " << result.projection_bound_best_value << ",\n";
    out << "  \"projection_bound_scope\": \"" << jsonEscape(result.projection_bound_scope) << "\",\n";
    out << "  \"penalty_budget\": " << result.penalty_budget << ",\n";
    out << "  \"domains_tightened_count\": " << result.domains_tightened_count << ",\n";
    out << "  \"total_domain_width_before\": " << result.total_domain_width_before << ",\n";
    out << "  \"total_domain_width_after\": " << result.total_domain_width_after << ",\n";
    out << "  \"penalty_tightening_time_seconds\": " << result.penalty_tightening_time_seconds << ",\n";
    out << "  \"pricing_negative_columns_found\": " << result.pricing_negative_columns_found << ",\n";
    out << "  \"pricing_negative_columns_inserted\": " << result.pricing_negative_columns_inserted << ",\n";
    out << "  \"pricing_negative_columns_dominated\": " << result.pricing_negative_columns_dominated << ",\n";
    out << "  \"pricing_completed_exactly\": "
        << (result.pricing_completed_exactly ? "true" : "false") << ",\n";
    out << "  \"frontier_cache_hits\": " << result.frontier_cache_hits << ",\n";
    out << "  \"frontier_cache_columns_loaded\": " << result.frontier_cache_columns_loaded << ",\n";
    out << "  \"frontier_cache_columns_inserted\": " << result.frontier_cache_columns_inserted << ",\n";
    out << "  \"frontier_cache_time_seconds\": " << result.frontier_cache_time_seconds << ",\n";
    out << "  \"final_inventories\": "; writeVector(out, result.final_inventory); out << ",\n";
    out << "  \"routes\": [";
    for (std::size_t r = 0; r < result.routes.size(); ++r) {
        if (r) out << ", ";
        const RoutePlan& route = result.routes[r];
        out << "{\"vehicle\": " << route.vehicle << ", \"nodes\": ";
        writeVector(out, route.nodes);
        out << ", \"operations\": [";
        for (std::size_t i = 0; i < route.operations.size(); ++i) {
            if (i) out << ", ";
            const StopOperation& op = route.operations[i];
            out << "{\"station\": " << op.station
                << ", \"pickup\": " << op.pickup
                << ", \"drop\": " << op.drop << "}";
        }
        out << "]}";
    }
    out << "],\n";
    out << "  \"station_operations\": [";
    bool first = true;
    for (const auto& route : result.routes) {
        for (const auto& op : route.operations) {
            if (!first) out << ", ";
            first = false;
            out << "{\"vehicle\": " << route.vehicle
                << ", \"station\": " << op.station
                << ", \"pickup\": " << op.pickup
                << ", \"drop\": " << op.drop << "}";
        }
    }
    out << "],\n";
    out << "  \"verification\": ";
    writeVerification(out, result.verification);
    out << ",\n";
    out << "  \"notes\": "; writeStringVector(out, result.notes); out << "\n";
    out << "}\n";
    return out.str();
}

std::string resultsToJson(const std::vector<SolveResult>& results) {
    if (results.size() == 1) return resultToJson(results.front());
    std::ostringstream out;
    out << "[\n";
    for (std::size_t i = 0; i < results.size(); ++i) {
        if (i) out << ",\n";
        out << resultToJson(results[i]);
    }
    out << "]\n";
    return out.str();
}

void writeTextFile(const std::string& path, const std::string& text) {
    if (path.empty()) return;
    std::filesystem::path p(path);
    if (p.has_parent_path()) std::filesystem::create_directories(p.parent_path());
    std::ofstream out(path);
    if (!out) throw std::runtime_error("Cannot write file: " + path);
    out << text;
}

} // namespace ebrp
