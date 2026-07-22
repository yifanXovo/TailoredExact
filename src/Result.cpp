#include "Result.hpp"

#include <cmath>
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
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

double finiteOrZero(double value) {
    return std::isfinite(value) ? value : 0.0;
}

void writeOptionalDouble(std::ostringstream& out,
                         bool available,
                         double value) {
    if (available && std::isfinite(value)) out << value;
    else out << "null";
}

void writeVerification(std::ostringstream& out, const Verification& v) {
    out << "{";
    out << "\"feasible\": " << (v.feasible ? "true" : "false") << ", ";
    out << "\"original_solution_feasible\": "
        << (v.original_solution_feasible ? "true" : "false") << ", ";
    out << "\"original_objective_recomputed\": "
        << (v.original_objective_recomputed ? "true" : "false") << ", ";
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
    if (result.frontier_execution_mode == "global-gini-tree" ||
        result.frontier_execution_mode == "external-gini-tree") {
        return "original_compact";
    }
    if (method == "gcap-frontier" &&
        (result.algorithm_preset == "paper-gf-compact-bc" ||
         result.algorithm_preset == "paper-gf-tailored-bc")) {
        return "original_compact";
    }
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
    if (method == "gurobi") return "plain_gurobi";
    if (method == "gcap-cg" || method == "gcap-tree" || method == "master" ||
        containsText(method, "fixed-cap") || containsText(method, "gini-cap")) {
        return "subproblem";
    }
    if (method == "pricing" || method == "pricing-branch" || method == "cuts" ||
        method == "branching" || method == "cg" || method == "gcap-branch" ||
        method == "support-pruning-test" ||
        method == "route-mask-support-test" ||
        method == "route-mask-operation-budget-test" ||
        method == "adaptive-frontier-split-test" ||
        method == "pricing-closure-audit-test" ||
        method == "resume-state-test" ||
        method == "pricing-verifier-test" ||
        method == "iterative-closure-test" ||
        method == "certificate-basis-test" ||
        method == "option-consistency-test" ||
        method == "station-set-test" ||
        method == "ng-dssr-pricing-test" ||
        method == "dssr-exactness-test" ||
        method == "dual-stabilization-test" ||
        method == "external-incumbent-test" ||
        method == "large-instance-mode-test" ||
        method == "incumbent-import-test" ||
        method == "route-pool-incumbent-test" ||
        method == "pickup-drop-compat-flow-test" ||
        method == "pickup-drop-transfer-cap-test") {
        return "diagnostic";
    }
    if (containsText(text, "restricted path pool") || containsText(text, "restricted column")) {
        return "subproblem";
    }
    return "diagnostic";
}

bool inferSolvesOriginalObjective(const SolveResult& result) {
    const std::string scope = inferMethodScope(result);
    return scope == "original_bpc" || scope == "original_compact" ||
           scope == "plain_cplex" || scope == "plain_gurobi";
}

bool inferIsBpc(const SolveResult& result) {
    const std::string method = lowerCopy(result.method);
    if (result.frontier_execution_mode == "global-gini-tree" ||
        result.frontier_execution_mode == "external-gini-tree") return false;
    if (method == "gcap-frontier" &&
        (result.algorithm_preset == "paper-gf-compact-bc" ||
         result.algorithm_preset == "paper-gf-tailored-bc")) {
        return false;
    }
    return method == "gcap-frontier" || containsText(method, "full route-load bpc");
}

std::string inferCertificateType(const SolveResult& result) {
    const std::string method = lowerCopy(result.method);
    const std::string text = auditText(result);
    if (result.frontier_execution_mode == "global-gini-tree") {
        return result.status == "optimal"
            ? "global_gini_single_tree_compact_mip"
            : "incomplete_global_gini_single_tree_compact_mip";
    }
    if (result.frontier_execution_mode == "external-gini-tree") {
        return result.status == "optimal"
            ? "global_gini_external_static_mip_tree"
            : "incomplete_global_gini_external_static_mip_tree";
    }
    if (method == "gcap-frontier") {
        if (result.algorithm_preset == "paper-gf-tailored-bc") {
            return result.status == "optimal"
                ? "full_gini_frontier_cplex_managed_tailored_bc"
                : "incomplete_gini_frontier_cplex_managed_tailored_bc";
        }
        if (result.algorithm_preset == "paper-gf-compact-bc") {
            return result.status == "optimal"
                ? "full_gini_frontier_compact_interval_bc"
                : "incomplete_gini_frontier_compact_interval_bc";
        }
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
    if (method == "gurobi") return "plain_gurobi_compact_mip";
    if (method == "gcap-cg") return "fixed_gini_cap_root_column_generation";
    if (method == "gcap-tree") {
        return containsText(text, "interval")
            ? "fixed_gini_interval_branch_price_tree"
            : "fixed_gini_cap_branch_price_tree";
    }
    if (method == "gcap-branch") return "fixed_gini_cap_one_level_ryan_foster_probe";
    if (method == "master") return "restricted_column_pool_master";
    if (method == "pricing") return "route_load_pricing_oracle";
    if (method == "support-pruning-test") return "support_duration_pruning_diagnostic";
    if (method == "route-mask-support-test") return "route_mask_support_duration_diagnostic";
    if (method == "route-mask-operation-budget-test") return "route_mask_operation_budget_diagnostic";
    if (method == "adaptive-frontier-split-test") return "adaptive_frontier_split_diagnostic";
    if (method == "pricing-closure-audit-test") return "pricing_closure_audit_diagnostic";
    if (method == "resume-state-test") return "frontier_resume_state_diagnostic";
    if (method == "pricing-verifier-test") return "pricing_verifier_diagnostic";
    if (method == "iterative-closure-test") return "iterative_frontier_closure_diagnostic";
    if (method == "certificate-basis-test") return "certificate_basis_audit_diagnostic";
    if (method == "option-consistency-test") return "option_consistency_audit_diagnostic";
    if (method == "station-set-test") return "station_set_representation_diagnostic";
    if (method == "ng-dssr-pricing-test") return "ng_dssr_pricing_diagnostic";
    if (method == "dssr-exactness-test") return "dssr_exactness_diagnostic";
    if (method == "dual-stabilization-test") return "dual_stabilization_diagnostic";
    if (method == "external-incumbent-test") return "external_incumbent_diagnostic";
    if (method == "large-instance-mode-test") return "large_instance_mode_diagnostic";
    if (method == "incumbent-import-test") return "incumbent_import_verification_diagnostic";
    if (method == "route-pool-incumbent-test") return "route_pool_incumbent_diagnostic";
    if (method == "pickup-drop-compat-flow-test") return "pickup_drop_compat_flow_diagnostic";
    if (method == "pickup-drop-transfer-cap-test") return "pickup_drop_transfer_cap_diagnostic";
    if (method == "vehicle-indexed-relaxation-test") return "vehicle_indexed_relaxation_diagnostic";
    if (method == "vehicle-indexed-transfer-flow-test") return "vehicle_indexed_transfer_flow_diagnostic";
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
    return result.verification.original_solution_feasible &&
           result.verification.original_objective_recomputed &&
           result.verification.errors.empty();
}

bool inferCertifiedOriginalProblem(const SolveResult& result) {
    const bool uses_native_mip_strict_policy =
        lowerCopy(result.method) == "cplex" ||
        result.frontier_execution_mode == "global-gini-tree" ||
        result.frontier_execution_mode == "external-gini-tree" ||
        result.native_mip_evidence_available;
    if (uses_native_mip_strict_policy) {
        return result.strict_certified_original_problem;
    }
    if (result.status != "optimal") return false;
    if (!result.option_audit_consistent) return false;
    if (!inferSolvesOriginalObjective(result)) return false;
    if (!inferVerifierPassed(result)) return false;
    if (result.incumbent_source_contributes_lower_bound) return false;
    if (result.incumbent_source_category == "diagnostic_archive" &&
        result.incumbent_source_is_paper_reproducible) return false;
    if (result.sealed_run) {
        if (result.sealed_run_forbidden_source_used) return false;
        if (!result.no_archive_scanning) return false;
        if (!result.no_external_known_ub) return false;
        if (!result.no_focus_only_certificate) return false;
    }
    if (result.gap > 1e-7) return false;
    if (!nearlyEqual(result.lower_bound, result.upper_bound)) return false;
    if (!nearlyEqual(result.objective, result.upper_bound)) return false;
    if (result.frontier_execution_mode == "global-gini-tree") {
        return result.global_gini_tree_attempted &&
               result.global_gini_tree_solved &&
               result.global_gini_tree_solver_finalization_reached &&
               result.global_gini_tree_native_best_bound_available &&
               result.global_gini_tree_lifecycle_valid &&
               result.global_gini_tree_recursive_branching_complete &&
               result.global_gini_tree_row_migration_complete &&
               result.global_gini_tree_sibling_isolation_by_construction &&
               result.global_gini_tree_root_coverage_valid &&
               result.global_gini_tree_branch_coverage_valid &&
               result.global_gini_tree_incumbent_verified &&
               result.global_gini_tree_optimality_accepted &&
               result.global_gini_tree_environment_count == 1 &&
               result.global_gini_tree_problem_count == 1 &&
               result.global_gini_tree_model_read_count == 1 &&
               result.global_gini_tree_mipopt_count == 1 &&
               result.global_gini_tree_freeprob_count == 1 &&
               result.global_gini_tree_close_count == 1 &&
               result.global_gini_tree_interval_oracle_count == 0 &&
               result.global_gini_tree_child_process_count == 0;
    }
    if (result.frontier_execution_mode == "external-gini-tree") {
        return result.external_gini_tree_attempted &&
               result.external_gini_tree_available &&
               result.external_gini_tree_root_coverage_valid &&
               result.external_gini_tree_parent_child_coverage_valid &&
               result.external_gini_tree_all_relevant_leaves_closed &&
               result.external_gini_tree_all_leaf_bounds_valid &&
               result.external_gini_tree_leaf_bounds_monotone &&
               result.external_gini_tree_global_bound_monotone &&
               result.external_gini_tree_lifecycle_complete &&
               result.external_gini_tree_feasibility_consistency_gate &&
               result.external_gini_tree_strict_certified &&
               result.external_gini_tree_reset_call_count == 0 &&
               result.external_gini_tree_optimize_count ==
                   result.external_gini_tree_attempt_count;
    }
    if (result.algorithm_preset == "paper-gf-compact-bc" ||
        result.algorithm_preset == "paper-gf-tailored-bc") {
        if (result.method != "gcap-frontier") return false;
        if (result.unresolved_intervals != 0 || result.invalid_bound_intervals != 0) return false;
        if (result.open_nodes != 0) return false;
        if (!result.frontier_covers_all_improving_gini_values) return false;
        if (result.frontier_range_certificate_scope != "original_full_improving_range") return false;
        if (!result.full_certificate_all_intervals_accounted) return false;
        if (!result.full_certificate_rejection_reason.empty() &&
            result.full_certificate_rejection_reason != "none") return false;
        if (result.certificate_uses_bpc_tree || result.intervals_closed_by_bpc_count > 0) return false;
        if (result.route_mask_all_subset_enumeration_certifying) return false;
        if (!result.compact_bc_certificate_valid) return false;
    }
    if (inferIsBpc(result)) {
        if (result.unresolved_intervals != 0 || result.invalid_bound_intervals != 0) return false;
        if (result.open_nodes != 0) return false;
        if (!result.frontier_covers_all_improving_gini_values) return false;
        if (result.frontier_range_certificate_scope != "original_full_improving_range") {
            return false;
        }
        if (!result.full_certificate_basis.empty() &&
            result.full_certificate_basis == "not_certified") return false;
        if (!result.full_certificate_rejection_reason.empty() &&
            result.full_certificate_rejection_reason != "none") return false;
        if (result.full_certificate_requires_pricing_closure &&
            !result.full_certificate_pricing_closure_satisfied) return false;
        if (!result.full_certificate_basis.empty() &&
            !result.full_certificate_all_intervals_accounted) return false;
        const bool route_mask_based_certificate =
            containsText(result.frontier_lower_bound_source, "route_mask") ||
            containsText(result.interval_certificate_basis, "route_mask") ||
            containsText(result.interval_bound_source_list, "route_mask");
        if (result.algorithm_preset == "paper-gf-bpc-core" &&
            route_mask_based_certificate) {
            return false;
        }
        if (route_mask_based_certificate &&
            !result.route_mask_all_subset_enumeration_certifying) {
            return false;
        }
        if (result.algorithm_preset == "paper-gf-bpc-core") {
            if (result.certificate_uses_interval_oracle) return false;
            if (!result.bpc_core_certificate_valid) return false;
        }
        const bool branch_price_tree_used_for_certificate =
            result.frontier_tree_closed_interval_count > 0;
        if (result.objective > 1e-12 && branch_price_tree_used_for_certificate) {
            if (!result.pricing_completed_exactly || !result.pricing_closure_certified_exact) return false;
            if (result.pricing_blocked_by_duplicate_projection) return false;
            if (result.pricing_closed_nodes <= 0) return false;
        }
    }
    return true;
}

SolveResult guardOriginalOptimalityForOutput(const SolveResult& input) {
    SolveResult guarded = input;
    if (guarded.status == "optimal" &&
        inferSolvesOriginalObjective(guarded) &&
        !inferCertifiedOriginalProblem(guarded)) {
        guarded.status = "not_certified_incomplete_certificate";
        guarded.certificate =
            "guarded: original-problem optimality was not emitted because the "
            "full certificate audit failed";
        if (guarded.bpc_status == "optimal") {
            guarded.bpc_status = guarded.status;
        }
        if (guarded.portfolio_status == "optimal") {
            guarded.portfolio_status = "not_certified";
            guarded.certificate_module = "none";
        }
        if (guarded.full_certificate_rejection_reason.empty() ||
            guarded.full_certificate_rejection_reason == "none") {
            guarded.full_certificate_rejection_reason =
                "output_guard_rejected_incomplete_original_certificate";
        }
        guarded.notes.push_back(
            "certificate output guard changed status from optimal because "
            "certified_original_problem=false under the full audit");
    }
    return guarded;
}

std::string resultToJson(const SolveResult& input) {
    const SolveResult guarded_result = guardOriginalOptimalityForOutput(input);
    const SolveResult& result = guarded_result;
    std::ostringstream out;
    out << std::setprecision(std::numeric_limits<double>::max_digits10);
    const bool native_mip_output =
        lowerCopy(result.method) == "cplex" ||
        result.frontier_execution_mode == "global-gini-tree" ||
        result.native_mip_evidence_available;
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
    out << "  \"certificate_scope\": \"" << jsonEscape(result.certificate_scope) << "\",\n";
    out << "  \"instance_scope\": \"" << jsonEscape(result.instance_scope) << "\",\n";
    out << "  \"instance_hash\": \"" << jsonEscape(result.instance_hash) << "\",\n";
    out << "  \"instance_source_path\": \"" << jsonEscape(result.instance_source_path) << "\",\n";
    out << "  \"algorithm_preset\": \"" << jsonEscape(result.algorithm_preset) << "\",\n";
    out << "  \"preset_certificate_scope\": \"" << jsonEscape(result.preset_certificate_scope) << "\",\n";
    out << "  \"preset_experimental_features_enabled\": \""
        << jsonEscape(result.preset_experimental_features_enabled) << "\",\n";
    out << "  \"preset_disabled_features\": \""
        << jsonEscape(result.preset_disabled_features) << "\",\n";
    out << "  \"preset_reason\": \"" << jsonEscape(result.preset_reason) << "\",\n";
    out << "  \"option_audit_consistent\": "
        << (result.option_audit_consistent ? "true" : "false") << ",\n";
    out << "  \"option_audit_mismatches\": \""
        << jsonEscape(result.option_audit_mismatches) << "\",\n";
    out << "  \"incumbent_archive_attempted\": "
        << (result.incumbent_archive_attempted ? "true" : "false") << ",\n";
    out << "  \"incumbent_archive_files_scanned\": "
        << result.incumbent_archive_files_scanned << ",\n";
    out << "  \"incumbent_archive_candidates_verified\": "
        << result.incumbent_archive_candidates_verified << ",\n";
    out << "  \"incumbent_archive_best_objective\": "
        << result.incumbent_archive_best_objective << ",\n";
    out << "  \"incumbent_archive_best_source\": \""
        << jsonEscape(result.incumbent_archive_best_source) << "\",\n";
    out << "  \"incumbent_archive_selected\": "
        << (result.incumbent_archive_selected ? "true" : "false") << ",\n";
    out << "  \"bpc_status\": \"" << jsonEscape(result.bpc_status) << "\",\n";
    out << "  \"bpc_LB\": " << result.bpc_LB << ",\n";
    out << "  \"bpc_UB\": " << result.bpc_UB << ",\n";
    out << "  \"bpc_gap\": " << result.bpc_gap << ",\n";
    out << "  \"compact_status\": \"" << jsonEscape(result.compact_status) << "\",\n";
    out << "  \"compact_LB\": " << result.compact_LB << ",\n";
    out << "  \"compact_UB\": " << result.compact_UB << ",\n";
    out << "  \"compact_gap\": " << result.compact_gap << ",\n";
    out << "  \"portfolio_status\": \"" << jsonEscape(result.portfolio_status) << "\",\n";
    out << "  \"portfolio_objective\": " << result.portfolio_objective << ",\n";
    out << "  \"portfolio_LB\": " << result.portfolio_LB << ",\n";
    out << "  \"portfolio_gap\": " << result.portfolio_gap << ",\n";
    out << "  \"certificate_module\": \"" << jsonEscape(result.certificate_module) << "\",\n";
    out << "  \"column_dominance_enabled\": "
        << (result.column_dominance_enabled ? "true" : "false") << ",\n";
    out << "  \"movement_domain_enabled\": "
        << (result.movement_domain_enabled ? "true" : "false") << ",\n";
    out << "  \"projection_bound_enabled\": "
        << (result.projection_bound_enabled ? "true" : "false") << ",\n";
    out << "  \"penalty_domain_enabled\": "
        << (result.penalty_domain_enabled ? "true" : "false") << ",\n";
    out << "  \"vehicle_indexed_relaxation_enabled\": "
        << (result.vehicle_indexed_relaxation_enabled_snapshot ? "true" : "false") << ",\n";
    out << "  \"operation_budget_cuts_enabled\": "
        << (result.operation_budget_cuts_enabled ? "true" : "false") << ",\n";
    out << "  \"branching_enabled\": "
        << (result.branching_enabled ? "true" : "false") << ",\n";
    out << "  \"two_track_enabled\": "
        << (result.two_track_enabled ? "true" : "false") << ",\n";
    out << "  \"status\": \"" << jsonEscape(result.status) << "\",\n";
    out << "  \"certificate\": \"" << jsonEscape(result.certificate) << "\",\n";
    out << "  \"objective\": " << result.objective << ",\n";
    out << "  \"G\": " << result.G << ",\n";
    out << "  \"P\": " << result.P << ",\n";
    out << "  \"lower_bound\": ";
    writeOptionalDouble(out,
                        !native_mip_output ||
                            result.native_mip_best_bound_available,
                        result.lower_bound);
    out << ",\n";
    out << "  \"upper_bound\": ";
    writeOptionalDouble(out,
                        !native_mip_output ||
                            result.verified_incumbent_objective_available,
                        result.upper_bound);
    out << ",\n";
    out << "  \"gap\": ";
    writeOptionalDouble(out,
                        !native_mip_output ||
                            result.verified_incumbent_project_relative_gap_available,
                        result.gap);
    out << ",\n";
    out << "  \"native_mip_evidence_available\": "
        << (result.native_mip_evidence_available ? "true" : "false") << ",\n";
    out << "  \"native_mipopt_return_code\": "
        << result.native_mipopt_return_code << ",\n";
    out << "  \"native_mip_status_code\": "
        << result.native_mip_status_code << ",\n";
    out << "  \"native_mip_status_text_available\": "
        << (result.native_mip_status_text_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_status_text\": \""
        << jsonEscape(result.native_mip_status_text) << "\",\n";
    out << "  \"native_mip_status_class\": \""
        << jsonEscape(result.native_mip_status_class) << "\",\n";
    out << "  \"native_mip_status_code_text_consistent\": "
        << (result.native_mip_status_code_text_consistent ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_objective_return_code\": "
        << result.native_mip_objective_return_code << ",\n";
    out << "  \"native_mip_objective_available\": "
        << (result.native_mip_objective_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_objective\": ";
    writeOptionalDouble(out, result.native_mip_objective_available,
                        result.native_mip_objective);
    out << ",\n";
    out << "  \"native_mip_best_bound_return_code\": "
        << result.native_mip_best_bound_return_code << ",\n";
    out << "  \"native_mip_best_bound_available\": "
        << (result.native_mip_best_bound_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_best_bound\": ";
    writeOptionalDouble(out, result.native_mip_best_bound_available,
                        result.native_mip_best_bound);
    out << ",\n";
    out << "  \"verified_incumbent_objective_available\": "
        << (result.verified_incumbent_objective_available ? "true" : "false")
        << ",\n";
    out << "  \"verified_incumbent_objective\": ";
    writeOptionalDouble(out, result.verified_incumbent_objective_available,
                        result.verified_incumbent_objective);
    out << ",\n";
    out << "  \"verified_incumbent_original_problem_feasible\": "
        << (result.verified_incumbent_original_problem_feasible
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_objective_consistent\": "
        << (result.verified_incumbent_objective_consistent
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_objective_residual_available\": "
        << (result.verified_incumbent_objective_residual_available
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_objective_residual\": ";
    writeOptionalDouble(out,
                        result.verified_incumbent_objective_residual_available,
                        result.verified_incumbent_objective_residual);
    out << ",\n";
    out << "  \"native_vs_recomputed_objective_residual_available\": "
        << (result.verified_incumbent_objective_residual_available
                ? "true" : "false") << ",\n";
    out << "  \"native_vs_recomputed_objective_residual\": ";
    writeOptionalDouble(out,
                        result.verified_incumbent_objective_residual_available,
                        result.verified_incumbent_objective_residual);
    out << ",\n";
    out << "  \"objective_mapping_diagnostic\": \""
        << jsonEscape(result.objective_mapping_diagnostic) << "\",\n";

    out << "  \"model_correctness_verified\": "
        << (result.model_correctness_verified ? "true" : "false")
        << ",\n";
    out << "  \"model_correctness_gate_version\": \""
        << jsonEscape(result.model_correctness_gate_version) << "\",\n";
    out << "  \"model_correctness_failure_reason\": \""
        << jsonEscape(result.model_correctness_failure_reason) << "\",\n";
    out << "  \"model_correctness_audit_fingerprint\": \""
        << jsonEscape(result.model_correctness_audit_fingerprint) << "\",\n";
    out << "  \"model_correctness_executable_sha256\": \""
        << jsonEscape(result.model_correctness_executable_sha256) << "\",\n";
    out << "  \"model_correctness_source_commit_sha\": \""
        << jsonEscape(result.model_correctness_source_commit_sha) << "\",\n";
    out << "  \"model_correctness_model_writer_fingerprint\": \""
        << jsonEscape(result.model_correctness_model_writer_fingerprint)
        << "\",\n";
    out << "  \"model_correctness_objective_definition_fingerprint\": \""
        << jsonEscape(result.model_correctness_objective_definition_fingerprint)
        << "\",\n";
    out << "  \"model_correctness_row_family_inventory\": \""
        << jsonEscape(result.model_correctness_row_family_inventory)
        << "\",\n";
    out << "  \"model_correctness_callback_row_inventory\": \""
        << jsonEscape(result.model_correctness_callback_row_inventory)
        << "\",\n";
    out << "  \"model_correctness_variable_domain_inventory\": \""
        << jsonEscape(result.model_correctness_variable_domain_inventory)
        << "\",\n";
    out << "  \"model_correctness_production_option_manifest_sha256\": \""
        << jsonEscape(
               result.model_correctness_production_option_manifest_sha256)
        << "\",\n";
    out << "  \"model_correctness_algorithm_arm\": \""
        << jsonEscape(result.model_correctness_algorithm_arm) << "\",\n";
    out << "  \"model_correctness_flow_variant\": \""
        << jsonEscape(result.model_correctness_flow_variant) << "\",\n";

    out << "  \"native_mip_relative_gap_param_id\": "
        << result.native_mip_relative_gap_param_id << ",\n";
    out << "  \"native_mip_relative_gap_requested\": ";
    writeOptionalDouble(out, result.native_mip_evidence_available,
                        result.native_mip_relative_gap_requested);
    out << ",\n";
    out << "  \"native_mip_relative_gap_set_return_code\": "
        << result.native_mip_relative_gap_set_return_code << ",\n";
    out << "  \"native_mip_relative_gap_get_return_code\": "
        << result.native_mip_relative_gap_get_return_code << ",\n";
    out << "  \"native_mip_relative_gap_effective_available\": "
        << (result.native_mip_relative_gap_effective_available
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_relative_gap_effective\": ";
    writeOptionalDouble(out,
                        result.native_mip_relative_gap_effective_available,
                        result.native_mip_relative_gap_effective);
    out << ",\n";
    out << "  \"native_mip_absolute_gap_param_id\": "
        << result.native_mip_absolute_gap_param_id << ",\n";
    out << "  \"native_mip_absolute_gap_requested\": ";
    writeOptionalDouble(out, result.native_mip_evidence_available,
                        result.native_mip_absolute_gap_requested);
    out << ",\n";
    out << "  \"native_mip_absolute_gap_set_return_code\": "
        << result.native_mip_absolute_gap_set_return_code << ",\n";
    out << "  \"native_mip_absolute_gap_get_return_code\": "
        << result.native_mip_absolute_gap_get_return_code << ",\n";
    out << "  \"native_mip_absolute_gap_effective_available\": "
        << (result.native_mip_absolute_gap_effective_available
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_absolute_gap_effective\": ";
    writeOptionalDouble(out,
                        result.native_mip_absolute_gap_effective_available,
                        result.native_mip_absolute_gap_effective);
    out << ",\n";
    out << "  \"native_mip_strict_gap_parameters_valid\": "
        << (result.native_mip_strict_gap_parameters_valid
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_cplex_relative_gap_return_code\": "
        << result.native_mip_cplex_relative_gap_return_code << ",\n";
    out << "  \"native_mip_cplex_relative_gap_available\": "
        << (result.native_mip_cplex_relative_gap_available
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_cplex_relative_gap\": ";
    writeOptionalDouble(out, result.native_mip_cplex_relative_gap_available,
                        result.native_mip_cplex_relative_gap);
    out << ",\n";
    out << "  \"native_mip_absolute_gap_available\": "
        << (result.native_mip_absolute_gap_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_absolute_gap\": ";
    writeOptionalDouble(out, result.native_mip_absolute_gap_available,
                        result.native_mip_absolute_gap);
    out << ",\n";
    out << "  \"native_mip_signed_bound_residual_available\": "
        << (result.native_mip_signed_bound_residual_available
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_signed_bound_residual\": ";
    writeOptionalDouble(out,
                        result.native_mip_signed_bound_residual_available,
                        result.native_mip_signed_bound_residual);
    out << ",\n";
    out << "  \"native_mip_bound_inversion\": "
        << (result.native_mip_bound_inversion ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_relative_gap_available\": "
        << (result.native_mip_relative_gap_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_relative_gap\": ";
    writeOptionalDouble(out, result.native_mip_relative_gap_available,
                        result.native_mip_relative_gap);
    out << ",\n";
    out << "  \"verified_incumbent_absolute_gap_available\": "
        << (result.verified_incumbent_absolute_gap_available
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_absolute_gap\": ";
    writeOptionalDouble(out, result.verified_incumbent_absolute_gap_available,
                        result.verified_incumbent_absolute_gap);
    out << ",\n";
    out << "  \"verified_incumbent_signed_bound_residual_available\": "
        << (result.verified_incumbent_signed_bound_residual_available
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_signed_bound_residual\": ";
    writeOptionalDouble(
        out, result.verified_incumbent_signed_bound_residual_available,
        result.verified_incumbent_signed_bound_residual);
    out << ",\n";
    out << "  \"verified_incumbent_bound_inversion\": "
        << (result.verified_incumbent_bound_inversion ? "true" : "false")
        << ",\n";
    out << "  \"verified_incumbent_relative_gap_available\": "
        << (result.verified_incumbent_relative_gap_available
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_relative_gap\": ";
    writeOptionalDouble(out, result.verified_incumbent_relative_gap_available,
                        result.verified_incumbent_relative_gap);
    out << ",\n";
    out << "  \"verified_incumbent_project_relative_gap_available\": "
        << (result.verified_incumbent_project_relative_gap_available
                ? "true" : "false") << ",\n";
    out << "  \"verified_incumbent_project_relative_gap\": ";
    writeOptionalDouble(
        out, result.verified_incumbent_project_relative_gap_available,
        result.verified_incumbent_project_relative_gap);
    out << ",\n";

    out << "  \"native_mip_node_count_available\": "
        << (result.native_mip_node_count_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_node_count\": "
        << result.native_mip_node_count << ",\n";
    out << "  \"native_mip_open_node_count_available\": "
        << (result.native_mip_open_node_count_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_open_node_count\": "
        << result.native_mip_open_node_count << ",\n";
    out << "  \"native_mip_solution_count_available\": "
        << (result.native_mip_solution_count_available ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_solution_count\": "
        << result.native_mip_solution_count << ",\n";
    out << "  \"native_mip_threads_requested\": "
        << result.native_mip_threads_requested << ",\n";
    out << "  \"native_mip_threads_set_return_code\": "
        << result.native_mip_threads_set_return_code << ",\n";
    out << "  \"native_mip_threads_get_return_code\": "
        << result.native_mip_threads_get_return_code << ",\n";
    out << "  \"native_mip_threads_effective\": "
        << result.native_mip_threads_effective << ",\n";
    out << "  \"native_mip_presolve_requested\": "
        << result.native_mip_presolve_requested << ",\n";
    out << "  \"native_mip_presolve_set_return_code\": "
        << result.native_mip_presolve_set_return_code << ",\n";
    out << "  \"native_mip_presolve_get_return_code\": "
        << result.native_mip_presolve_get_return_code << ",\n";
    out << "  \"native_mip_presolve_effective\": "
        << result.native_mip_presolve_effective << ",\n";
    out << "  \"native_mip_search_requested\": "
        << result.native_mip_search_requested << ",\n";
    out << "  \"native_mip_search_set_return_code\": "
        << result.native_mip_search_set_return_code << ",\n";
    out << "  \"native_mip_search_get_return_code\": "
        << result.native_mip_search_get_return_code << ",\n";
    out << "  \"native_mip_search_effective\": "
        << result.native_mip_search_effective << ",\n";
    out << "  \"native_mip_node_select_requested\": "
        << result.native_mip_node_select_requested << ",\n";
    out << "  \"native_mip_node_select_set_return_code\": "
        << result.native_mip_node_select_set_return_code << ",\n";
    out << "  \"native_mip_node_select_get_return_code\": "
        << result.native_mip_node_select_get_return_code << ",\n";
    out << "  \"native_mip_node_select_effective\": "
        << result.native_mip_node_select_effective << ",\n";
    out << "  \"native_mip_time_limit_param_id\": "
        << result.native_mip_time_limit_param_id << ",\n";
    out << "  \"native_mip_time_limit_requested\": "
        << result.native_mip_time_limit_requested << ",\n";
    out << "  \"native_mip_time_limit_set_return_code\": "
        << result.native_mip_time_limit_set_return_code << ",\n";
    out << "  \"native_mip_time_limit_get_return_code\": "
        << result.native_mip_time_limit_get_return_code << ",\n";
    out << "  \"native_mip_time_limit_effective_available\": "
        << (result.native_mip_time_limit_effective_available
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_time_limit_effective\": ";
    writeOptionalDouble(out,
                        result.native_mip_time_limit_effective_available,
                        result.native_mip_time_limit_effective);
    out << ",\n";
    out << "  \"native_mip_finalization_state\": \""
        << jsonEscape(result.native_mip_finalization_state) << "\",\n";
    out << "  \"native_mip_solver_finalization_reached\": "
        << (result.native_mip_solver_finalization_reached
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_evidence_capture_complete\": "
        << (result.native_mip_evidence_capture_complete
                ? "true" : "false") << ",\n";
    out << "  \"native_mip_problem_freed\": "
        << (result.native_mip_problem_freed ? "true" : "false") << ",\n";
    out << "  \"native_mip_freeprob_return_code\": "
        << result.native_mip_freeprob_return_code << ",\n";
    out << "  \"native_mip_environment_closed\": "
        << (result.native_mip_environment_closed ? "true" : "false")
        << ",\n";
    out << "  \"native_mip_close_return_code\": "
        << result.native_mip_close_return_code << ",\n";
    out << "  \"native_mip_environment_count\": "
        << result.native_mip_environment_count << ",\n";
    out << "  \"native_mip_problem_count\": "
        << result.native_mip_problem_count << ",\n";
    out << "  \"native_mip_model_read_count\": "
        << result.native_mip_model_read_count << ",\n";
    out << "  \"native_mip_mipopt_count\": "
        << result.native_mip_mipopt_count << ",\n";
    out << "  \"native_mip_freeprob_count\": "
        << result.native_mip_freeprob_count << ",\n";
    out << "  \"native_mip_close_count\": "
        << result.native_mip_close_count << ",\n";
    out << "  \"native_mip_lifecycle_valid\": "
        << (result.native_mip_lifecycle_valid ? "true" : "false") << ",\n";

    out << "  \"strict_certificate_policy_version\": \""
        << jsonEscape(result.strict_certificate_policy_version) << "\",\n";
    out << "  \"strict_certificate_class\": \""
        << jsonEscape(result.strict_certificate_class) << "\",\n";
    out << "  \"strict_certificate_rejection_reason\": \""
        << jsonEscape(result.strict_certificate_rejection_reason) << "\",\n";
    out << "  \"strict_native_model_scope\": \""
        << jsonEscape(result.strict_native_model_scope) << "\",\n";
    out << "  \"strict_infeasibility_scope\": \""
        << jsonEscape(result.strict_infeasibility_scope) << "\",\n";
    out << "  \"feasibility_consistency_gate_passed\": "
        << (result.feasibility_consistency_gate_passed ? "true" : "false")
        << ",\n";
    out << "  \"strict_certified_original_problem\": "
        << (result.strict_certified_original_problem ? "true" : "false")
        << ",\n";
    out << "  \"strict_native_objective_valid\": "
        << (result.strict_native_objective_valid ? "true" : "false")
        << ",\n";
    out << "  \"strict_native_best_bound_valid\": "
        << (result.strict_native_best_bound_valid ? "true" : "false")
        << ",\n";
    out << "  \"strict_bound_equality_closed\": "
        << (result.strict_bound_equality_closed ? "true" : "false")
        << ",\n";
    out << "  \"strict_bound_equality_proof_module\": \""
        << jsonEscape(result.strict_bound_equality_proof_module) << "\",\n";
    out << "  \"strict_bound_equality_proof_conditions_satisfied\": "
        << (result.strict_bound_equality_proof_conditions_satisfied
                ? "true" : "false") << ",\n";
    out << "  \"strict_independent_exact_certificate_module\": \""
        << jsonEscape(result.strict_independent_exact_certificate_module)
        << "\",\n";
    out << "  \"strict_independent_exact_certificate_conditions_satisfied\": "
        << (result.strict_independent_exact_certificate_conditions_satisfied
                ? "true" : "false") << ",\n";
    out << "  \"strict_lower_bound_source\": \""
        << jsonEscape(result.strict_lower_bound_source) << "\",\n";
    out << "  \"strict_serialized_lower_bound_matches_native\": "
        << (result.strict_serialized_lower_bound_matches_native
                ? "true" : "false") << ",\n";
    out << "  \"strict_serialized_gap_consistent\": "
        << (result.strict_serialized_gap_consistent ? "true" : "false")
        << ",\n";

    out << "  \"dense_progress_enabled\": "
        << (result.dense_progress_enabled ? "true" : "false") << ",\n";
    out << "  \"dense_progress_raw_event_path\": \""
        << jsonEscape(result.dense_progress_raw_event_path) << "\",\n";
    out << "  \"dense_progress_checkpoint_path\": \""
        << jsonEscape(result.dense_progress_checkpoint_path) << "\",\n";
    out << "  \"dense_progress_schema_version\": \""
        << jsonEscape(result.dense_progress_schema_version) << "\",\n";
    out << "  \"dense_progress_callback_invocation_count\": "
        << result.dense_progress_callback_invocation_count << ",\n";
    out << "  \"dense_progress_record_count\": "
        << result.dense_progress_record_count << ",\n";
    out << "  \"dense_progress_dropped_record_count\": "
        << result.dense_progress_dropped_record_count << ",\n";
    out << "  \"dense_progress_callback_wall_seconds\": "
        << result.dense_progress_callback_wall_seconds << ",\n";
    out << "  \"dense_progress_serialization_seconds\": "
        << result.dense_progress_serialization_seconds << ",\n";
    out << "  \"dense_progress_peak_buffer_bytes\": "
        << result.dense_progress_peak_buffer_bytes << ",\n";
    out << "  \"dense_progress_instrumentation_wall_percent\": "
        << result.dense_progress_instrumentation_wall_percent << ",\n";
    out << "  \"dense_progress_final_record_appended\": "
        << (result.dense_progress_final_record_appended ? "true" : "false")
        << ",\n";
    out << "  \"dense_progress_flush_succeeded\": "
        << (result.dense_progress_flush_succeeded ? "true" : "false")
        << ",\n";
    out << "  \"dense_progress_flush_failure_reason\": \""
        << jsonEscape(result.dense_progress_flush_failure_reason) << "\",\n";
    out << "  \"dense_progress_read_only_contract\": "
        << (result.dense_progress_read_only_contract ? "true" : "false")
        << ",\n";

    out << "  \"gurobi_build_enabled\": "
        << (result.gurobi_build_enabled ? "true" : "false") << ",\n";
    out << "  \"gurobi_runtime_library_found\": "
        << (result.gurobi_runtime_library_found ? "true" : "false") << ",\n";
    out << "  \"gurobi_license_available\": "
        << (result.gurobi_license_available ? "true" : "false") << ",\n";
    out << "  \"gurobi_version\": \"" << jsonEscape(result.gurobi_version)
        << "\",\n";
    out << "  \"gurobi_header_version\": \""
        << jsonEscape(result.gurobi_header_version) << "\",\n";
    out << "  \"gurobi_native_library\": \""
        << jsonEscape(result.gurobi_native_library) << "\",\n";
    out << "  \"gurobi_installation_root\": \""
        << jsonEscape(result.gurobi_installation_root) << "\",\n";
    out << "  \"gurobi_failure_reason\": \""
        << jsonEscape(result.gurobi_failure_reason) << "\",\n";
    out << "  \"gurobi_optimize_return_code\": "
        << result.gurobi_optimize_return_code << ",\n";
    out << "  \"gurobi_status\": " << result.gurobi_status << ",\n";
    out << "  \"gurobi_status_text\": \""
        << jsonEscape(result.gurobi_status_text) << "\",\n";
    out << "  \"gurobi_solution_count\": "
        << result.gurobi_solution_count << ",\n";
    out << "  \"gurobi_obj_val_available\": "
        << (result.gurobi_obj_val_available ? "true" : "false") << ",\n";
    out << "  \"gurobi_obj_val\": " << result.gurobi_obj_val << ",\n";
    out << "  \"gurobi_obj_bound_available\": "
        << (result.gurobi_obj_bound_available ? "true" : "false") << ",\n";
    out << "  \"gurobi_obj_bound\": " << result.gurobi_obj_bound << ",\n";
    out << "  \"gurobi_obj_bound_c_available\": "
        << (result.gurobi_obj_bound_c_available ? "true" : "false") << ",\n";
    out << "  \"gurobi_obj_bound_c\": " << result.gurobi_obj_bound_c << ",\n";
    out << "  \"gurobi_mip_gap_available\": "
        << (result.gurobi_mip_gap_available ? "true" : "false") << ",\n";
    out << "  \"gurobi_mip_gap\": " << result.gurobi_mip_gap << ",\n";
    out << "  \"gurobi_runtime\": " << result.gurobi_runtime << ",\n";
    out << "  \"gurobi_work\": " << result.gurobi_work << ",\n";
    out << "  \"gurobi_node_count\": " << result.gurobi_node_count << ",\n";
    out << "  \"gurobi_iter_count\": " << result.gurobi_iter_count << ",\n";
    out << "  \"gurobi_bar_iter_count\": "
        << result.gurobi_bar_iter_count << ",\n";
    out << "  \"gurobi_model_fingerprint\": "
        << result.gurobi_model_fingerprint << ",\n";
    out << "  \"gurobi_num_vars\": " << result.gurobi_num_vars << ",\n";
    out << "  \"gurobi_num_constrs\": " << result.gurobi_num_constrs << ",\n";
    out << "  \"gurobi_num_nzs\": " << result.gurobi_num_nzs << ",\n";
    out << "  \"gurobi_num_bin_vars\": " << result.gurobi_num_bin_vars << ",\n";
    out << "  \"gurobi_num_int_vars\": " << result.gurobi_num_int_vars << ",\n";
    out << "  \"gurobi_num_cont_vars\": " << result.gurobi_num_cont_vars << ",\n";
    out << "  \"gurobi_objective_sense\": "
        << result.gurobi_objective_sense << ",\n";
    out << "  \"gurobi_native_domain_audit_passed\": "
        << (result.gurobi_native_domain_audit_passed ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_native_variable_names_match\": "
        << (result.gurobi_native_variable_names_match ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_native_variable_types_match\": "
        << (result.gurobi_native_variable_types_match ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_native_variable_bounds_match\": "
        << (result.gurobi_native_variable_bounds_match ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_native_objective_sense_match\": "
        << (result.gurobi_native_objective_sense_match ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_native_domain_audit_failure_reason\": \""
        << jsonEscape(result.gurobi_native_domain_audit_failure_reason)
        << "\",\n";
    out << "  \"gurobi_mem_used_gb\": " << result.gurobi_mem_used_gb << ",\n";
    out << "  \"gurobi_max_mem_used_gb\": "
        << result.gurobi_max_mem_used_gb << ",\n";
    out << "  \"gurobi_max_constraint_violation\": "
        << result.gurobi_max_constraint_violation << ",\n";
    out << "  \"gurobi_max_bound_violation\": "
        << result.gurobi_max_bound_violation << ",\n";
    out << "  \"gurobi_max_integrality_violation\": "
        << result.gurobi_max_integrality_violation << ",\n";
    out << "  \"gurobi_threads_requested\": "
        << result.gurobi_threads_requested << ",\n";
    out << "  \"gurobi_threads_set_return_code\": "
        << result.gurobi_threads_set_return_code << ",\n";
    out << "  \"gurobi_threads_get_return_code\": "
        << result.gurobi_threads_get_return_code << ",\n";
    out << "  \"gurobi_threads_effective\": "
        << result.gurobi_threads_effective << ",\n";
    out << "  \"gurobi_presolve_requested\": "
        << result.gurobi_presolve_requested << ",\n";
    out << "  \"gurobi_presolve_set_return_code\": "
        << result.gurobi_presolve_set_return_code << ",\n";
    out << "  \"gurobi_presolve_get_return_code\": "
        << result.gurobi_presolve_get_return_code << ",\n";
    out << "  \"gurobi_presolve_effective\": "
        << result.gurobi_presolve_effective << ",\n";
    out << "  \"gurobi_seed_requested\": "
        << result.gurobi_seed_requested << ",\n";
    out << "  \"gurobi_seed_set_return_code\": "
        << result.gurobi_seed_set_return_code << ",\n";
    out << "  \"gurobi_seed_get_return_code\": "
        << result.gurobi_seed_get_return_code << ",\n";
    out << "  \"gurobi_seed_effective\": "
        << result.gurobi_seed_effective << ",\n";
    out << "  \"gurobi_mip_gap_requested\": "
        << result.gurobi_mip_gap_requested << ",\n";
    out << "  \"gurobi_mip_gap_set_return_code\": "
        << result.gurobi_mip_gap_set_return_code << ",\n";
    out << "  \"gurobi_mip_gap_get_return_code\": "
        << result.gurobi_mip_gap_get_return_code << ",\n";
    out << "  \"gurobi_mip_gap_effective\": "
        << result.gurobi_mip_gap_effective << ",\n";
    out << "  \"gurobi_mip_gap_abs_requested\": "
        << result.gurobi_mip_gap_abs_requested << ",\n";
    out << "  \"gurobi_mip_gap_abs_set_return_code\": "
        << result.gurobi_mip_gap_abs_set_return_code << ",\n";
    out << "  \"gurobi_mip_gap_abs_get_return_code\": "
        << result.gurobi_mip_gap_abs_get_return_code << ",\n";
    out << "  \"gurobi_mip_gap_abs_effective\": "
        << result.gurobi_mip_gap_abs_effective << ",\n";
    out << "  \"gurobi_environment_creation_return_code\": "
        << result.gurobi_environment_creation_return_code << ",\n";
    out << "  \"gurobi_environment_count\": "
        << result.gurobi_environment_count << ",\n";
    out << "  \"gurobi_model_count\": " << result.gurobi_model_count << ",\n";
    out << "  \"gurobi_model_read_count\": "
        << result.gurobi_model_read_count << ",\n";
    out << "  \"gurobi_optimize_count\": "
        << result.gurobi_optimize_count << ",\n";
    out << "  \"gurobi_model_free_count\": "
        << result.gurobi_model_free_count << ",\n";
    out << "  \"gurobi_environment_free_count\": "
        << result.gurobi_environment_free_count << ",\n";
    out << "  \"gurobi_solver_finalization_reached\": "
        << (result.gurobi_solver_finalization_reached ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_lifecycle_valid\": "
        << (result.gurobi_lifecycle_valid ? "true" : "false") << ",\n";
    out << "  \"gurobi_canonical_model_sha256\": \""
        << jsonEscape(result.gurobi_canonical_model_sha256) << "\",\n";
    out << "  \"gurobi_progress_path\": \""
        << jsonEscape(result.gurobi_progress_path) << "\",\n";
    out << "  \"gurobi_progress_callback_invocations\": "
        << result.gurobi_progress_callback_invocations << ",\n";
    out << "  \"gurobi_progress_record_count\": "
        << result.gurobi_progress_record_count << ",\n";
    out << "  \"gurobi_first_incumbent_time\": "
        << result.gurobi_first_incumbent_time << ",\n";
    out << "  \"gurobi_last_lower_bound_improvement_time\": "
        << result.gurobi_last_lower_bound_improvement_time << ",\n";
    out << "  \"gurobi_progress_read_only_contract\": "
        << (result.gurobi_progress_read_only_contract ? "true" : "false")
        << ",\n";
    out << "  \"gurobi_exception_type\": \""
        << jsonEscape(result.gurobi_exception_type) << "\",\n";
    out << "  \"gurobi_exception_message\": \""
        << jsonEscape(result.gurobi_exception_message) << "\",\n";

    out << "  \"global_gini_tree_root_connectivity_flow_variant_requested\": \""
        << jsonEscape(
               result.global_gini_tree_root_connectivity_flow_variant_requested)
        << "\",\n";
    out << "  \"global_gini_tree_root_connectivity_flow_variant_resolved\": \""
        << jsonEscape(
               result.global_gini_tree_root_connectivity_flow_variant_resolved)
        << "\",\n";
    out << "  \"global_gini_tree_root_model_size_available\": "
        << (result.global_gini_tree_root_model_size_available
                ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_root_model_rows\": "
        << result.global_gini_tree_root_model_rows << ",\n";
    out << "  \"global_gini_tree_root_model_cols\": "
        << result.global_gini_tree_root_model_cols << ",\n";
    out << "  \"global_gini_tree_root_model_nonzeros\": "
        << result.global_gini_tree_root_model_nonzeros << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_columns\": "
        << result.global_gini_tree_connectivity_flow_columns << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_upper_link_rows\": "
        << result.global_gini_tree_connectivity_flow_upper_link_rows << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_lower_link_rows\": "
        << result.global_gini_tree_connectivity_flow_lower_link_rows << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_station_balance_rows\": "
        << result.global_gini_tree_connectivity_flow_station_balance_rows
        << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_depot_balance_rows\": "
        << result.global_gini_tree_connectivity_flow_depot_balance_rows
        << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_start_upper_rows\": "
        << result.global_gini_tree_connectivity_flow_start_upper_rows
        << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_start_lower_rows\": "
        << result.global_gini_tree_connectivity_flow_start_lower_rows
        << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_total_rows\": "
        << result.global_gini_tree_connectivity_flow_total_rows << ",\n";
    out << "  \"global_gini_tree_connectivity_flow_total_nonzeros\": "
        << result.global_gini_tree_connectivity_flow_total_nonzeros << ",\n";
    out << "  \"runtime_seconds\": " << result.runtime_seconds << ",\n";
    out << "  \"wall_time_seconds\": " << wall_time << ",\n";
    out << "  \"time_budget_seconds\": " << result.time_budget_seconds << ",\n";
    out << "  \"actual_runtime_seconds\": "
        << (result.actual_runtime_seconds > 0.0
                ? result.actual_runtime_seconds
                : result.runtime_seconds) << ",\n";
    out << "  \"aggregate_worker_time_seconds\": " << aggregate_worker_time << ",\n";
    out << "  \"stop_reason\": \"" << jsonEscape(inferStopReason(result)) << "\",\n";
    out << "  \"finalization_source\": \""
        << jsonEscape(result.finalization_source) << "\",\n";
    out << "  \"best_valid_lb_seen\": " << result.best_valid_lb_seen << ",\n";
    out << "  \"best_valid_gap_seen\": " << result.best_valid_gap_seen << ",\n";
    out << "  \"best_valid_ledger_checkpoint\": \""
        << jsonEscape(result.best_valid_ledger_checkpoint) << "\",\n";
    out << "  \"best_valid_ledger_time\": "
        << result.best_valid_ledger_time << ",\n";
    out << "  \"final_json_uses_best_checkpoint\": "
        << (result.final_json_uses_best_checkpoint ? "true" : "false") << ",\n";
    out << "  \"interrupted_run_best_bound_preserved\": "
        << (result.interrupted_run_best_bound_preserved ? "true" : "false") << ",\n";
    out << "  \"last_progress_event\": \""
        << jsonEscape(result.last_progress_event) << "\",\n";
    out << "  \"plateau_reason\": \""
        << jsonEscape(result.plateau_reason) << "\",\n";
    out << "  \"plateau_detected\": "
        << (result.plateau_detected ? "true" : "false") << ",\n";
    out << "  \"last_bound_improvement_time\": "
        << result.last_bound_improvement_time << ",\n";
    out << "  \"solver_finalization_reached\": "
        << (result.solver_finalization_reached ? "true" : "false") << ",\n";
    out << "  \"wrapper_synthesized_final_json\": "
        << (result.wrapper_synthesized_final_json ? "true" : "false") << ",\n";
    out << "  \"process_return_code\": " << result.process_return_code << ",\n";
    out << "  \"abnormal_exit_detected\": "
        << (result.abnormal_exit_detected ? "true" : "false") << ",\n";
    out << "  \"abnormal_exit_reason\": \""
        << jsonEscape(result.abnormal_exit_reason) << "\",\n";
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
    out << "  \"gini_max_possible\": " << result.gini_max_possible << ",\n";
    out << "  \"relevant_gini_upper_for_improvement\": "
        << result.relevant_gini_upper_for_improvement << ",\n";
    out << "  \"covered_gini_upper_bound\": " << result.covered_gini_upper_bound << ",\n";
    out << "  \"frontier_covers_all_improving_gini_values\": "
        << (result.frontier_covers_all_improving_gini_values ? "true" : "false") << ",\n";
    out << "  \"frontier_range_certificate_scope\": \""
        << jsonEscape(result.frontier_range_certificate_scope) << "\",\n";
    out << "  \"frontier_execution_mode\": \""
        << jsonEscape(result.frontier_execution_mode) << "\",\n";
    out << "  \"global_gini_tree_attempted\": "
        << (result.global_gini_tree_attempted ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_available\": "
        << (result.global_gini_tree_available ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_solved\": "
        << (result.global_gini_tree_solved ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_return_code\": "
        << result.global_gini_tree_return_code << ",\n";
    out << "  \"global_gini_tree_status_code\": "
        << result.global_gini_tree_status_code << ",\n";
    out << "  \"global_gini_tree_solver_status\": \""
        << jsonEscape(result.global_gini_tree_solver_status) << "\",\n";
    out << "  \"global_gini_tree_fail_reason\": \""
        << jsonEscape(result.global_gini_tree_fail_reason) << "\",\n";
    out << "  \"global_gini_tree_environment_count\": "
        << result.global_gini_tree_environment_count << ",\n";
    out << "  \"global_gini_tree_problem_count\": "
        << result.global_gini_tree_problem_count << ",\n";
    out << "  \"global_gini_tree_model_read_count\": "
        << result.global_gini_tree_model_read_count << ",\n";
    out << "  \"global_gini_tree_mipopt_count\": "
        << result.global_gini_tree_mipopt_count << ",\n";
    out << "  \"global_gini_tree_freeprob_count\": "
        << result.global_gini_tree_freeprob_count << ",\n";
    out << "  \"global_gini_tree_close_count\": "
        << result.global_gini_tree_close_count << ",\n";
    out << "  \"global_gini_tree_interval_oracle_count\": "
        << result.global_gini_tree_interval_oracle_count << ",\n";
    out << "  \"global_gini_tree_child_process_count\": "
        << result.global_gini_tree_child_process_count << ",\n";
    out << "  \"global_gini_tree_branch_callback_calls\": "
        << result.global_gini_tree_branch_callback_calls << ",\n";
    out << "  \"global_gini_tree_relaxation_callback_calls\": "
        << result.global_gini_tree_relaxation_callback_calls << ",\n";
    out << "  \"global_gini_tree_candidate_callback_calls\": "
        << result.global_gini_tree_candidate_callback_calls << ",\n";
    out << "  \"global_gini_tree_progress_callback_calls\": "
        << result.global_gini_tree_progress_callback_calls << ",\n";
    out << "  \"global_gini_tree_gini_branch_nodes\": "
        << result.global_gini_tree_gini_branch_nodes << ",\n";
    out << "  \"global_gini_tree_gini_children_created\": "
        << result.global_gini_tree_gini_children_created << ",\n";
    out << "  \"global_gini_tree_gini_branch_generations\": "
        << result.global_gini_tree_gini_branch_generations << ",\n";
    out << "  \"global_gini_tree_ordinary_branch_fallbacks\": "
        << result.global_gini_tree_ordinary_branch_fallbacks << ",\n";
    out << "  \"global_gini_tree_nonoptimal_relaxation_fallbacks\": "
        << result.global_gini_tree_nonoptimal_relaxation_fallbacks << ",\n";
    out << "  \"global_gini_tree_local_rows_attached\": "
        << result.global_gini_tree_local_rows_attached << ",\n";
    out << "  \"global_gini_tree_local_bound_changes_attached\": "
        << result.global_gini_tree_local_bound_changes_attached << ",\n";
    out << "  \"global_gini_tree_local_row_failures\": "
        << result.global_gini_tree_local_row_failures << ",\n";
    out << "  \"global_gini_tree_column_mapping_failures\": "
        << result.global_gini_tree_column_mapping_failures << ",\n";
    out << "  \"global_gini_tree_coverage_failures\": "
        << result.global_gini_tree_coverage_failures << ",\n";
    out << "  \"global_gini_tree_child_estimate_failures\": "
        << result.global_gini_tree_child_estimate_failures << ",\n";
    out << "  \"global_gini_tree_local_bound_api_failures\": "
        << result.global_gini_tree_local_bound_api_failures << ",\n";
    out << "  \"global_gini_tree_node_info_api_failures\": "
        << result.global_gini_tree_node_info_api_failures << ",\n";
    out << "  \"global_gini_tree_callback_failures\": "
        << result.global_gini_tree_callback_failures << ",\n";
    out << "  \"global_gini_tree_post_row_reoptimizations\": "
        << result.global_gini_tree_post_row_reoptimizations << ",\n";
    out << "  \"global_gini_tree_post_row_reoptimization_failures\": "
        << result.global_gini_tree_post_row_reoptimization_failures << ",\n";
    out << "  \"global_gini_tree_theoretical_full_rows\": "
        << result.global_gini_tree_theoretical_full_rows << ",\n";
    out << "  \"global_gini_tree_theoretical_full_bounds\": "
        << result.global_gini_tree_theoretical_full_bounds << ",\n";
    out << "  \"global_gini_tree_exact_duplicate_rows_omitted\": "
        << result.global_gini_tree_exact_duplicate_rows_omitted << ",\n";
    out << "  \"global_gini_tree_identical_bounds_omitted\": "
        << result.global_gini_tree_identical_bounds_omitted << ",\n";
    out << "  \"global_gini_tree_dominance_omissions\": "
        << result.global_gini_tree_dominance_omissions << ",\n";
    out << "  \"global_gini_tree_delta_rows_attached\": "
        << result.global_gini_tree_delta_rows_attached << ",\n";
    out << "  \"global_gini_tree_delta_bounds_attached\": "
        << result.global_gini_tree_delta_bounds_attached << ",\n";
    out << "  \"global_gini_tree_ordinary_branches_before_terminal_gini\": "
        << result.global_gini_tree_ordinary_branches_before_terminal_gini
        << ",\n";
    out << "  \"global_gini_tree_ordinary_branches_after_terminal_gini\": "
        << result.global_gini_tree_ordinary_branches_after_terminal_gini
        << ",\n";
    out << "  \"global_gini_tree_sibling_first_process_count\": "
        << result.global_gini_tree_sibling_first_process_count << ",\n";
    out << "  \"global_gini_tree_sibling_equal_estimate_pairs\": "
        << result.global_gini_tree_sibling_equal_estimate_pairs << ",\n";
    out << "  \"global_gini_tree_sibling_discriminated_pairs\": "
        << result.global_gini_tree_sibling_discriminated_pairs << ",\n";
    out << "  \"global_gini_tree_native_simplex_iterations\": "
        << result.global_gini_tree_native_simplex_iterations << ",\n";
    out << "  \"global_gini_tree_native_open_nodes\": "
        << result.global_gini_tree_native_open_nodes << ",\n";
    out << "  \"global_gini_tree_native_solution_pool_count\": "
        << result.global_gini_tree_native_solution_pool_count << ",\n";
    out << "  \"global_gini_tree_first_gini_branch_time\": "
        << result.global_gini_tree_first_gini_branch_time << ",\n";
    out << "  \"global_gini_tree_row_factory_seconds\": "
        << result.global_gini_tree_row_factory_seconds << ",\n";
    out << "  \"global_gini_tree_callback_packing_seconds\": "
        << result.global_gini_tree_callback_packing_seconds << ",\n";
    out << "  \"global_gini_tree_local_row_api_seconds\": "
        << result.global_gini_tree_local_row_api_seconds << ",\n";
    out << "  \"global_gini_tree_presolve_requested\": "
        << result.global_gini_tree_presolve_requested << ",\n";
    out << "  \"global_gini_tree_presolve_set_rc\": "
        << result.global_gini_tree_presolve_set_rc << ",\n";
    out << "  \"global_gini_tree_presolve_effective\": "
        << result.global_gini_tree_presolve_effective << ",\n";
    out << "  \"global_gini_tree_preprocessing_reduce_requested\": "
        << result.global_gini_tree_preprocessing_reduce_requested << ",\n";
    out << "  \"global_gini_tree_preprocessing_reduce_set_rc\": "
        << result.global_gini_tree_preprocessing_reduce_set_rc << ",\n";
    out << "  \"global_gini_tree_preprocessing_reduce_get_rc\": "
        << result.global_gini_tree_preprocessing_reduce_get_rc << ",\n";
    out << "  \"global_gini_tree_preprocessing_reduce_effective\": "
        << result.global_gini_tree_preprocessing_reduce_effective << ",\n";
    out << "  \"global_gini_tree_preprocessing_linear_requested\": "
        << result.global_gini_tree_preprocessing_linear_requested << ",\n";
    out << "  \"global_gini_tree_preprocessing_linear_set_rc\": "
        << result.global_gini_tree_preprocessing_linear_set_rc << ",\n";
    out << "  \"global_gini_tree_preprocessing_linear_get_rc\": "
        << result.global_gini_tree_preprocessing_linear_get_rc << ",\n";
    out << "  \"global_gini_tree_preprocessing_linear_effective\": "
        << result.global_gini_tree_preprocessing_linear_effective << ",\n";
    out << "  \"global_gini_tree_continuous_branch_presolve_valid\": "
        << (result.global_gini_tree_continuous_branch_presolve_valid
                ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_known_unsafe_presolve_diagnostic\": "
        << (result.global_gini_tree_known_unsafe_presolve_diagnostic
                ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_search_requested\": "
        << result.global_gini_tree_search_requested << ",\n";
    out << "  \"global_gini_tree_search_set_rc\": "
        << result.global_gini_tree_search_set_rc << ",\n";
    out << "  \"global_gini_tree_search_effective\": "
        << result.global_gini_tree_search_effective << ",\n";
    out << "  \"global_gini_tree_node_select_requested\": "
        << result.global_gini_tree_node_select_requested << ",\n";
    out << "  \"global_gini_tree_node_select_set_rc\": "
        << result.global_gini_tree_node_select_set_rc << ",\n";
    out << "  \"global_gini_tree_node_select_effective\": "
        << result.global_gini_tree_node_select_effective << ",\n";
    out << "  \"global_gini_tree_heuristics_effective\": "
        << result.global_gini_tree_heuristics_effective << ",\n";
    out << "  \"global_gini_tree_probing_effective\": "
        << result.global_gini_tree_probing_effective << ",\n";
    out << "  \"global_gini_tree_threads_effective\": "
        << result.global_gini_tree_threads_effective << ",\n";
    out << "  \"global_gini_tree_native_time_limit_set_rc\": "
        << result.global_gini_tree_native_time_limit_set_rc << ",\n";
    out << "  \"global_gini_tree_native_time_limit_seconds\": "
        << result.global_gini_tree_native_time_limit_seconds << ",\n";
    out << "  \"global_gini_tree_native_cuts_default\": "
        << (result.global_gini_tree_native_cuts_default ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_solver_finalization_reached\": "
        << (result.global_gini_tree_solver_finalization_reached ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_callback_abort_used\": "
        << (result.global_gini_tree_callback_abort_used ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_recursive_branching_complete\": "
        << (result.global_gini_tree_recursive_branching_complete ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_row_migration_complete\": "
        << (result.global_gini_tree_row_migration_complete ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_sibling_isolation_by_construction\": "
        << (result.global_gini_tree_sibling_isolation_by_construction ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_root_coverage_valid\": "
        << (result.global_gini_tree_root_coverage_valid ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_branch_coverage_valid\": "
        << (result.global_gini_tree_branch_coverage_valid ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_lifecycle_valid\": "
        << (result.global_gini_tree_lifecycle_valid ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_global_bound_monotone\": "
        << (result.global_gini_tree_global_bound_monotone ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_no_time_quantum\": "
        << (result.global_gini_tree_no_time_quantum ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_no_instance_special_case\": "
        << (result.global_gini_tree_no_instance_special_case ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_native_mip_start_attempted\": "
        << (result.global_gini_tree_native_mip_start_attempted ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_native_mip_start_mapping_complete\": "
        << (result.global_gini_tree_native_mip_start_mapping_complete ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_native_mip_start_submitted\": "
        << (result.global_gini_tree_native_mip_start_submitted ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_native_mip_start_stored\": "
        << (result.global_gini_tree_native_mip_start_stored ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_native_mip_start_accepted\": "
        << (result.global_gini_tree_native_mip_start_accepted ? "true" : "false")
        << ",\n";
    out << "  \"global_gini_tree_native_mip_start_return_code\": "
        << result.global_gini_tree_native_mip_start_return_code << ",\n";
    out << "  \"global_gini_tree_native_mip_start_stored_count\": "
        << result.global_gini_tree_native_mip_start_stored_count << ",\n";
    out << "  \"global_gini_tree_native_mip_start_failure_reason\": \""
        << jsonEscape(result.global_gini_tree_native_mip_start_failure_reason)
        << "\",\n";
    out << "  \"global_gini_tree_child_estimate_mode\": \""
        << jsonEscape(result.global_gini_tree_child_estimate_mode) << "\",\n";
    out << "  \"global_gini_tree_row_attachment_mode\": \""
        << jsonEscape(result.global_gini_tree_row_attachment_mode) << "\",\n";
    out << "  \"global_gini_tree_row_timing_mode\": \""
        << jsonEscape(result.global_gini_tree_row_timing_mode) << "\",\n";
    out << "  \"global_gini_tree_native_cut_counts\": \""
        << jsonEscape(result.global_gini_tree_native_cut_counts) << "\",\n";
    out << "  \"global_gini_tree_native_best_bound_available\": "
        << (result.global_gini_tree_native_best_bound_available ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_incumbent_verified\": "
        << (result.global_gini_tree_incumbent_verified ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_optimality_accepted\": "
        << (result.global_gini_tree_optimality_accepted ? "true" : "false") << ",\n";
    out << "  \"global_gini_tree_root_gamma_L\": "
        << result.global_gini_tree_root_gamma_L << ",\n";
    out << "  \"global_gini_tree_root_gamma_U\": "
        << result.global_gini_tree_root_gamma_U << ",\n";
    out << "  \"global_gini_tree_native_objective\": "
        << result.global_gini_tree_native_objective << ",\n";
    out << "  \"global_gini_tree_native_best_bound\": "
        << result.global_gini_tree_native_best_bound << ",\n";
    out << "  \"global_gini_tree_row_factory_version\": \""
        << jsonEscape(result.global_gini_tree_row_factory_version) << "\",\n";
    out << "  \"global_gini_tree_root_model_fingerprint\": \""
        << jsonEscape(result.global_gini_tree_root_model_fingerprint) << "\",\n";
    out << "  \"global_gini_tree_objective_fingerprint\": \""
        << jsonEscape(result.global_gini_tree_objective_fingerprint) << "\",\n";
    out << "  \"global_gini_tree_root_row_signature\": \""
        << jsonEscape(result.global_gini_tree_root_row_signature) << "\",\n";
    out << "  \"global_gini_tree_root_model_path\": \""
        << jsonEscape(result.global_gini_tree_root_model_path) << "\",\n";
    out << "  \"global_gini_tree_node_trace_path\": \""
        << jsonEscape(result.global_gini_tree_node_trace_path) << "\",\n";
    out << "  \"global_gini_tree_bound_trace_path\": \""
        << jsonEscape(result.global_gini_tree_bound_trace_path) << "\",\n";
    out << "  \"global_gini_tree_manifest_path\": \""
        << jsonEscape(result.global_gini_tree_manifest_path) << "\",\n";
    out << "  \"global_gini_tree_post_row_trace_path\": \""
        << jsonEscape(result.global_gini_tree_post_row_trace_path) << "\",\n";
    out << "  \"global_gini_tree_topology_trace_path\": \""
        << jsonEscape(result.global_gini_tree_topology_trace_path) << "\",\n";
    out << "  \"global_gini_tree_sibling_trace_path\": \""
        << jsonEscape(result.global_gini_tree_sibling_trace_path) << "\",\n";
    out << "  \"global_gini_tree_row_delta_trace_path\": \""
        << jsonEscape(result.global_gini_tree_row_delta_trace_path) << "\",\n";
    out << "  \"global_gini_tree_memory_trace_path\": \""
        << jsonEscape(result.global_gini_tree_memory_trace_path) << "\",\n";
    out << "  \"global_gini_tree_mip_start_audit_path\": \""
        << jsonEscape(result.global_gini_tree_mip_start_audit_path) << "\",\n";
    out << "  \"external_gini_tree_attempted\": "
        << (result.external_gini_tree_attempted ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_available\": "
        << (result.external_gini_tree_available ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_backend\": \""
        << jsonEscape(result.external_gini_tree_backend) << "\",\n";
    out << "  \"external_gini_tree_lifecycle\": \""
        << jsonEscape(result.external_gini_tree_lifecycle) << "\",\n";
    out << "  \"external_gini_tree_scheduling\": \""
        << jsonEscape(result.external_gini_tree_scheduling) << "\",\n";
    out << "  \"external_gini_tree_failure_reason\": \""
        << jsonEscape(result.external_gini_tree_failure_reason) << "\",\n";
    out << "  \"external_gini_tree_root_coverage_valid\": "
        << (result.external_gini_tree_root_coverage_valid ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_parent_child_coverage_valid\": "
        << (result.external_gini_tree_parent_child_coverage_valid ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_all_relevant_leaves_closed\": "
        << (result.external_gini_tree_all_relevant_leaves_closed ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_all_leaf_bounds_valid\": "
        << (result.external_gini_tree_all_leaf_bounds_valid ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_leaf_bounds_monotone\": "
        << (result.external_gini_tree_leaf_bounds_monotone ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_global_bound_monotone\": "
        << (result.external_gini_tree_global_bound_monotone ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_lifecycle_complete\": "
        << (result.external_gini_tree_lifecycle_complete ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_feasibility_consistency_gate\": "
        << (result.external_gini_tree_feasibility_consistency_gate ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_strict_certified\": "
        << (result.external_gini_tree_strict_certified ? "true" : "false") << ",\n";
    out << "  \"external_gini_tree_certificate_class\": \""
        << jsonEscape(result.external_gini_tree_certificate_class) << "\",\n";
    out << "  \"external_gini_tree_certificate_rejection_reason\": \""
        << jsonEscape(result.external_gini_tree_certificate_rejection_reason) << "\",\n";
    out << "  \"external_gini_tree_root_gamma_L\": "
        << result.external_gini_tree_root_gamma_L << ",\n";
    out << "  \"external_gini_tree_root_gamma_U\": "
        << result.external_gini_tree_root_gamma_U << ",\n";
    out << "  \"external_gini_tree_global_lower_bound\": "
        << result.external_gini_tree_global_lower_bound << ",\n";
    out << "  \"external_gini_tree_verified_upper_bound\": "
        << result.external_gini_tree_verified_upper_bound << ",\n";
#define WRITE_EXT_COUNT(name) \
    out << "  \"external_gini_tree_" #name "\": " \
        << result.external_gini_tree_##name << ",\n"
    WRITE_EXT_COUNT(initial_leaf_count);
    WRITE_EXT_COUNT(final_leaf_count);
    WRITE_EXT_COUNT(open_leaf_count);
    WRITE_EXT_COUNT(closed_leaf_count);
    WRITE_EXT_COUNT(split_after_attempts);
    WRITE_EXT_COUNT(split_count);
    WRITE_EXT_COUNT(attempt_count);
    WRITE_EXT_COUNT(environment_count);
    WRITE_EXT_COUNT(model_count);
    WRITE_EXT_COUNT(model_read_count);
    WRITE_EXT_COUNT(optimize_count);
    WRITE_EXT_COUNT(lp_relaxation_count);
    WRITE_EXT_COUNT(lp_optimize_count);
    WRITE_EXT_COUNT(terminal_mip_leaf_count);
    WRITE_EXT_COUNT(terminal_mip_optimize_count);
    WRITE_EXT_COUNT(global_deadline_interruption_count);
    WRITE_EXT_COUNT(model_free_count);
    WRITE_EXT_COUNT(environment_free_count);
    WRITE_EXT_COUNT(same_leaf_resume_count);
    WRITE_EXT_COUNT(fresh_restart_count);
    WRITE_EXT_COUNT(child_restart_count);
    WRITE_EXT_COUNT(reset_call_count);
    WRITE_EXT_COUNT(canonical_artifact_generation_count);
    WRITE_EXT_COUNT(canonical_artifact_cache_hit_count);
    WRITE_EXT_COUNT(canonical_artifact_invalidation_count);
    WRITE_EXT_COUNT(confirmed_continuation_count);
    WRITE_EXT_COUNT(partial_state_reuse_count);
    WRITE_EXT_COUNT(observed_fresh_restart_count);
    WRITE_EXT_COUNT(ambiguous_retained_state_count);
    WRITE_EXT_COUNT(presolve_execution_count);
    WRITE_EXT_COUNT(root_relaxation_execution_count);
    WRITE_EXT_COUNT(warm_start_candidate_count);
    WRITE_EXT_COUNT(warm_start_complete_count);
    WRITE_EXT_COUNT(warm_start_submitted_count);
    WRITE_EXT_COUNT(warm_start_accepted_count);
    WRITE_EXT_COUNT(warm_start_rejected_count);
    WRITE_EXT_COUNT(warm_start_unknown_count);
#undef WRITE_EXT_COUNT
#define WRITE_EXT_DOUBLE(name) \
    out << "  \"external_gini_tree_" #name "\": " \
        << result.external_gini_tree_##name << ",\n"
    WRITE_EXT_DOUBLE(model_build_seconds);
    WRITE_EXT_DOUBLE(canonical_artifact_generation_seconds);
    WRITE_EXT_DOUBLE(model_read_seconds);
    WRITE_EXT_DOUBLE(solver_seconds);
    WRITE_EXT_DOUBLE(work);
    WRITE_EXT_DOUBLE(lp_work);
    WRITE_EXT_DOUBLE(terminal_mip_work);
    WRITE_EXT_DOUBLE(nodes);
    WRITE_EXT_DOUBLE(simplex_iterations);
    WRITE_EXT_DOUBLE(barrier_iterations);
    WRITE_EXT_DOUBLE(peak_memory_gb);
    WRITE_EXT_DOUBLE(first_incumbent_time_seconds);
    WRITE_EXT_DOUBLE(last_incumbent_improvement_time_seconds);
    WRITE_EXT_DOUBLE(last_native_lb_improvement_time_seconds);
    WRITE_EXT_DOUBLE(last_global_lb_improvement_time_seconds);
    WRITE_EXT_DOUBLE(final_stagnation_seconds);
#undef WRITE_EXT_DOUBLE
#define WRITE_EXT_PATH(name) \
    out << "  \"external_gini_tree_" #name "\": \"" \
        << jsonEscape(result.external_gini_tree_##name) << "\",\n"
    WRITE_EXT_PATH(event_trace_path);
    WRITE_EXT_PATH(leaf_ledger_path);
    WRITE_EXT_PATH(lifecycle_path);
    WRITE_EXT_PATH(optimize_ledger_path);
    WRITE_EXT_PATH(warm_start_audit_path);
    WRITE_EXT_PATH(enhanced_attempt_trace_path);
    WRITE_EXT_PATH(lp_status_ledger_path);
    WRITE_EXT_PATH(parent_child_bound_ledger_path);
    WRITE_EXT_PATH(split_decision_ledger_path);
#undef WRITE_EXT_PATH
    out << "  \"columns_generated_raw\": " << result.columns_generated_raw << ",\n";
    out << "  \"columns_after_dominance\": " << result.columns_after_dominance << ",\n";
    out << "  \"columns_dominated\": " << result.columns_dominated << ",\n";
    out << "  \"pricing_columns_enumerated\": " << result.pricing_columns_enumerated << ",\n";
    out << "  \"dominance_input_columns\": " << result.dominance_input_columns << ",\n";
    out << "  \"dominance_kept_columns\": " << result.dominance_kept_columns << ",\n";
    out << "  \"dominance_removed_columns\": " << result.dominance_removed_columns << ",\n";
    out << "  \"dominance_removed_existing_projection\": "
        << result.dominance_removed_existing_projection << ",\n";
    out << "  \"dominance_removed_candidate_projection\": "
        << result.dominance_removed_candidate_projection << ",\n";
    out << "  \"rmp_columns_inserted\": " << result.rmp_columns_inserted << ",\n";
    out << "  \"rmp_columns_active\": " << result.rmp_columns_active << ",\n";
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
    out << "  \"pricing_best_reduced_cost_any\": "
        << finiteOrZero(result.pricing_best_reduced_cost_any) << ",\n";
    out << "  \"pricing_best_new_reduced_cost\": "
        << finiteOrZero(result.pricing_best_new_reduced_cost) << ",\n";
    out << "  \"pricing_duplicate_negative_projections\": "
        << result.pricing_duplicate_negative_projections << ",\n";
    out << "  \"pricing_new_negative_projections\": "
        << result.pricing_new_negative_projections << ",\n";
    out << "  \"pricing_blocked_by_duplicate_projection\": "
        << (result.pricing_blocked_by_duplicate_projection ? "true" : "false") << ",\n";
    out << "  \"pricing_closure_certified_exact\": "
        << (result.pricing_closure_certified_exact ? "true" : "false") << ",\n";
    out << "  \"pricing_closure_status\": \""
        << jsonEscape(result.pricing_closure_status) << "\",\n";
    out << "  \"pricing_remaining_negative_rc\": "
        << finiteOrZero(result.pricing_remaining_negative_rc) << ",\n";
    out << "  \"pricing_exact_verification_calls\": "
        << result.pricing_exact_verification_calls << ",\n";
    out << "  \"pricing_exact_verification_time_seconds\": "
        << result.pricing_exact_verification_time_seconds << ",\n";
    out << "  \"support_duration_cuts_generated\": "
        << result.support_duration_cuts_generated << ",\n";
    out << "  \"support_duration_pruned_labels\": "
        << result.support_duration_pruned_labels << ",\n";
    out << "  \"support_duration_pruned_columns\": "
        << result.support_duration_pruned_columns << ",\n";
    out << "  \"support_duration_min_pickup_rule\": \""
        << jsonEscape(result.support_duration_min_pickup_rule) << "\",\n";
    out << "  \"support_duration_strong_cuts_generated\": "
        << result.support_duration_strong_cuts_generated << ",\n";
    out << "  \"support_duration_strong_pruned_labels\": "
        << result.support_duration_strong_pruned_labels << ",\n";
    out << "  \"support_duration_strong_pruned_columns\": "
        << result.support_duration_strong_pruned_columns << ",\n";
    out << "  \"completion_lb_pruned_labels\": "
        << result.completion_lb_pruned_labels << ",\n";
    out << "  \"required_closure_pruned_labels\": "
        << result.required_closure_pruned_labels << ",\n";
    out << "  \"label_dominance_comparisons\": "
        << result.label_dominance_comparisons << ",\n";
    out << "  \"label_dominance_pruned_labels\": "
        << result.label_dominance_pruned_labels << ",\n";
    out << "  \"label_dominance_cross_pickup_pruned_labels\": "
        << result.label_dominance_cross_pickup_pruned_labels << ",\n";
    out << "  \"label_dominance_inactive_entries_skipped\": "
        << result.label_dominance_inactive_entries_skipped << ",\n";
    out << "  \"label_dominance_bucket_compactions\": "
        << result.label_dominance_bucket_compactions << ",\n";
    out << "  \"label_dominance_compacted_entries\": "
        << result.label_dominance_compacted_entries << ",\n";
    out << "  \"operation_dp_dominance_pruned_states\": "
        << result.operation_dp_dominance_pruned_states << ",\n";
    out << "  \"pricing_label_dominance_mode\": \""
        << jsonEscape(result.pricing_label_dominance_mode) << "\",\n";
    out << "  \"pricing_label_dominance_exact_safe\": "
        << (result.pricing_label_dominance_exact_safe ? "true" : "false") << ",\n";
    out << "  \"pricing_completion_bound_mode\": \""
        << jsonEscape(result.pricing_completion_bound_mode) << "\",\n";
    out << "  \"pricing_completion_bound_audit\": "
        << (result.pricing_completion_bound_audit ? "true" : "false") << ",\n";
    out << "  \"pricing_decomposition\": \""
        << jsonEscape(result.pricing_decomposition) << "\",\n";
    out << "  \"pricing_load_dp_cache_enabled\": "
        << (result.pricing_load_dp_cache_enabled ? "true" : "false") << ",\n";
    out << "  \"pricing_route_skeleton_mode\": \""
        << jsonEscape(result.pricing_route_skeleton_mode) << "\",\n";
    out << "  \"pricing_route_skeleton_cache_enabled\": "
        << (result.pricing_route_skeleton_cache_enabled ? "true" : "false") << ",\n";
    out << "  \"pricing_load_dp_dominance_enabled\": "
        << (result.pricing_load_dp_dominance_enabled ? "true" : "false") << ",\n";
    out << "  \"pricing_operation_dp_dominance_enabled\": "
        << (result.pricing_operation_dp_dominance_enabled ? "true" : "false") << ",\n";
    out << "  \"pricing_labels_generated\": "
        << result.pricing_labels_generated << ",\n";
    out << "  \"pricing_labels_kept\": "
        << result.pricing_labels_kept << ",\n";
    out << "  \"pricing_labels_expanded\": "
        << result.pricing_labels_expanded << ",\n";
    out << "  \"pricing_labels_pruned_duration\": "
        << result.pricing_labels_pruned_duration << ",\n";
    out << "  \"pricing_labels_pruned_load\": "
        << result.pricing_labels_pruned_load << ",\n";
    out << "  \"pricing_labels_pruned_station\": "
        << result.pricing_labels_pruned_station << ",\n";
    out << "  \"pricing_labels_pruned_support\": "
        << result.pricing_labels_pruned_support << ",\n";
    out << "  \"pricing_labels_pruned_reduced_cost\": "
        << result.pricing_labels_pruned_reduced_cost << ",\n";
    out << "  \"pricing_labels_pruned_dominance\": "
        << result.pricing_labels_pruned_dominance << ",\n";
    out << "  \"pricing_labels_duplicate_states\": "
        << result.pricing_labels_duplicate_states << ",\n";
    out << "  \"pricing_state_stop_reason\": \""
        << jsonEscape(result.pricing_state_stop_reason) << "\",\n";
    out << "  \"pricing_depth_profile\": "
        << (result.pricing_depth_profile_json.empty()
                ? std::string("[]") : result.pricing_depth_profile_json)
        << ",\n";
    out << "  \"operation_dp_profile\": "
        << (result.operation_dp_profile_json.empty()
                ? std::string("[]") : result.operation_dp_profile_json)
        << ",\n";
    out << "  \"bpc_seed_columns\": \""
        << jsonEscape(result.bpc_seed_columns) << "\",\n";
    out << "  \"bpc_seed_column_max\": "
        << result.bpc_seed_column_max << ",\n";
    out << "  \"bpc_cut_family\": \""
        << jsonEscape(result.bpc_cut_family) << "\",\n";
    out << "  \"bpc_cut_separation_rounds\": "
        << result.bpc_cut_separation_rounds << ",\n";
    out << "  \"core_relaxation_budget_fraction\": "
        << result.core_relaxation_budget_fraction << ",\n";
    out << "  \"core_bpc_reserve_fraction\": "
        << result.core_bpc_reserve_fraction << ",\n";
    out << "  \"core_bpc_min_seconds\": "
        << result.core_bpc_min_seconds << ",\n";
    out << "  \"core_bpc_max_leaves\": "
        << result.core_bpc_max_leaves << ",\n";
    out << "  \"core_bpc_leaf_selection\": \""
        << jsonEscape(result.core_bpc_leaf_selection) << "\",\n";
    out << "  \"support_duration_max_subset_size\": "
        << result.support_duration_max_subset_size << ",\n";
    out << "  \"support_duration_precompute_time_seconds\": "
        << result.support_duration_precompute_time_seconds << ",\n";
    out << "  \"large_instance_mode\": \""
        << jsonEscape(result.large_instance_mode) << "\",\n";
    out << "  \"station_set_backend\": \""
        << jsonEscape(result.station_set_backend) << "\",\n";
    out << "  \"unsupported_large_instance_features\": \""
        << jsonEscape(result.unsupported_large_instance_features) << "\",\n";
    out << "  \"route_mask_all_subset_enumeration_enabled\": "
        << (result.route_mask_all_subset_enumeration_enabled ? "true" : "false") << ",\n";
    out << "  \"route_mask_all_subset_enumeration_certifying\": "
        << (result.route_mask_all_subset_enumeration_certifying ? "true" : "false") << ",\n";
    out << "  \"vehicle_indexed_relaxation_enabled_snapshot\": "
        << (result.vehicle_indexed_relaxation_enabled_snapshot ? "true" : "false") << ",\n";
    out << "  \"vehicle_indexed_transfer_flow_enabled_snapshot\": "
        << (result.vehicle_indexed_transfer_flow_enabled_snapshot ? "true" : "false") << ",\n";
    out << "  \"benchmark_scale\": \""
        << jsonEscape(result.benchmark_scale) << "\",\n";
    out << "  \"memory_peak_estimate_mb\": "
        << result.memory_peak_estimate_mb << ",\n";
    out << "  \"labels_processed\": "
        << result.labels_processed << ",\n";
    out << "  \"pricing_engine\": \""
        << jsonEscape(result.pricing_engine) << "\",\n";
    out << "  \"final_pricing_engine\": \""
        << jsonEscape(result.final_pricing_engine) << "\",\n";
    out << "  \"column_tracks\": \""
        << jsonEscape(result.column_tracks) << "\",\n";
    out << "  \"relaxed_columns_in_rmp\": "
        << (result.relaxed_columns_in_rmp ? "true" : "false") << ",\n";
    out << "  \"incumbent_archive_auto\": "
        << (result.incumbent_archive_auto ? "true" : "false") << ",\n";
    out << "  \"compact_fallback_enabled\": "
        << (result.compact_fallback_enabled ? "true" : "false") << ",\n";
    out << "  \"cplex_plain_baseline\": "
        << (result.cplex_plain_baseline ? "true" : "false") << ",\n";
    out << "  \"cplex_seed_enabled\": "
        << (result.cplex_seed_enabled ? "true" : "false") << ",\n";
    out << "  \"elementary_columns_generated\": "
        << result.elementary_columns_generated << ",\n";
    out << "  \"elementary_columns_inserted\": "
        << result.elementary_columns_inserted << ",\n";
    out << "  \"relaxed_columns_generated\": "
        << result.relaxed_columns_generated << ",\n";
    out << "  \"relaxed_columns_inserted\": "
        << result.relaxed_columns_inserted << ",\n";
    out << "  \"relaxed_columns_rejected_projection\": "
        << result.relaxed_columns_rejected_projection << ",\n";
    out << "  \"relaxed_columns_rejected_infeasible_projection\": "
        << result.relaxed_columns_rejected_infeasible_projection << ",\n";
    out << "  \"relaxed_columns_used_in_lb_rmp\": "
        << result.relaxed_columns_used_in_lb_rmp << ",\n";
    out << "  \"relaxed_columns_used_in_incumbent\": "
        << result.relaxed_columns_used_in_incumbent << ",\n";
    out << "  \"non_elementary_relaxed_routes_seen\": "
        << result.non_elementary_relaxed_routes_seen << ",\n";
    out << "  \"non_elementary_relaxed_columns_validated\": "
        << result.non_elementary_relaxed_columns_validated << ",\n";
    out << "  \"non_elementary_relaxed_columns_inserted\": "
        << result.non_elementary_relaxed_columns_inserted << ",\n";
    out << "  \"non_elementary_relaxed_columns_rejected\": "
        << result.non_elementary_relaxed_columns_rejected << ",\n";
    out << "  \"relaxed_projection_rejected_load\": "
        << result.relaxed_projection_rejected_load << ",\n";
    out << "  \"relaxed_projection_rejected_station_capacity\": "
        << result.relaxed_projection_rejected_station_capacity << ",\n";
    out << "  \"relaxed_projection_rejected_branch\": "
        << result.relaxed_projection_rejected_branch << ",\n";
    out << "  \"relaxed_projection_rejected_operation_mode\": "
        << result.relaxed_projection_rejected_operation_mode << ",\n";
    out << "  \"relaxed_projection_rejected_unsafe_cut\": "
        << result.relaxed_projection_rejected_unsafe_cut << ",\n";
    out << "  \"relaxed_projection_validation_time_seconds\": "
        << result.relaxed_projection_validation_time_seconds << ",\n";
    out << "  \"relaxed_columns_blocked_from_incumbent\": "
        << result.relaxed_columns_blocked_from_incumbent << ",\n";
    out << "  \"relaxed_columns_blocked_from_export\": "
        << result.relaxed_columns_blocked_from_export << ",\n";
    out << "  \"relaxed_columns_blocked_from_candidate_reconstruction\": "
        << result.relaxed_columns_blocked_from_candidate_reconstruction << ",\n";
    out << "  \"rmp_column_space\": \""
        << jsonEscape(result.rmp_column_space) << "\",\n";
    out << "  \"relaxed_rmp_enabled\": "
        << (result.relaxed_rmp_enabled ? "true" : "false") << ",\n";
    out << "  \"relaxed_rmp_objective\": "
        << result.relaxed_rmp_objective << ",\n";
    out << "  \"relaxed_rmp_lower_bound\": "
        << result.relaxed_rmp_lower_bound << ",\n";
    out << "  \"relaxed_rmp_columns\": "
        << result.relaxed_rmp_columns << ",\n";
    out << "  \"relaxed_rmp_iterations\": "
        << result.relaxed_rmp_iterations << ",\n";
    out << "  \"relaxed_rmp_pricing_closed\": "
        << (result.relaxed_rmp_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"relaxed_rmp_best_reduced_cost\": "
        << finiteOrZero(result.relaxed_rmp_best_reduced_cost) << ",\n";
    out << "  \"relaxed_rmp_certificate_valid\": "
        << (result.relaxed_rmp_certificate_valid ? "true" : "false") << ",\n";
    out << "  \"relaxed_rmp_certificate_rejection_reason\": \""
        << jsonEscape(result.relaxed_rmp_certificate_rejection_reason) << "\",\n";
    out << "  \"elementary_pricing_closed\": "
        << (result.elementary_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"ng_relaxed_pricing_closed\": "
        << (result.ng_relaxed_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"dssr_exact_elementary_closed\": "
        << (result.dssr_exact_elementary_closed ? "true" : "false") << ",\n";
    out << "  \"ng_relaxed_best_reduced_cost\": "
        << finiteOrZero(result.ng_relaxed_best_reduced_cost) << ",\n";
    out << "  \"ng_relaxed_negative_routes_found\": "
        << result.ng_relaxed_negative_routes_found << ",\n";
    out << "  \"ng_relaxed_negative_columns_inserted\": "
        << result.ng_relaxed_negative_columns_inserted << ",\n";
    out << "  \"ng_relaxed_negative_routes_rejected\": "
        << result.ng_relaxed_negative_routes_rejected << ",\n";
    out << "  \"ng_relaxed_closure_labels_processed\": "
        << result.ng_relaxed_closure_labels_processed << ",\n";
    out << "  \"ng_relaxed_closure_labels_pruned\": "
        << result.ng_relaxed_closure_labels_pruned << ",\n";
    out << "  \"ng_relaxed_closure_time_seconds\": "
        << result.ng_relaxed_closure_time_seconds << ",\n";
    out << "  \"ng_relaxed_closure_stop_reason\": \""
        << jsonEscape(result.ng_relaxed_closure_stop_reason) << "\",\n";
    out << "  \"ng_relaxed_pricing_calls\": "
        << result.ng_relaxed_pricing_calls << ",\n";
    out << "  \"ng_relaxed_labels_processed\": "
        << result.ng_relaxed_labels_processed << ",\n";
    out << "  \"ng_relaxed_labels_pruned\": "
        << result.ng_relaxed_labels_pruned << ",\n";
    out << "  \"dssr_refinement_rounds_for_lb\": "
        << result.dssr_refinement_rounds_for_lb << ",\n";
    out << "  \"dssr_lb_before_refinement\": "
        << result.dssr_lb_before_refinement << ",\n";
    out << "  \"dssr_lb_after_refinement\": "
        << result.dssr_lb_after_refinement << ",\n";
    out << "  \"relaxed_rmp_cg_iterations\": "
        << result.relaxed_rmp_cg_iterations << ",\n";
    out << "  \"relaxed_rmp_cg_columns_added\": "
        << result.relaxed_rmp_cg_columns_added << ",\n";
    out << "  \"relaxed_rmp_cg_final_best_rc\": "
        << finiteOrZero(result.relaxed_rmp_cg_final_best_rc) << ",\n";
    out << "  \"relaxed_rmp_cg_closed\": "
        << (result.relaxed_rmp_cg_closed ? "true" : "false") << ",\n";
    out << "  \"relaxed_rmp_cg_stop_reason\": \""
        << jsonEscape(result.relaxed_rmp_cg_stop_reason) << "\",\n";
    out << "  \"relaxed_rmp_lb_before_cg\": "
        << result.relaxed_rmp_lb_before_cg << ",\n";
    out << "  \"relaxed_rmp_lb_after_cg\": "
        << result.relaxed_rmp_lb_after_cg << ",\n";
    out << "  \"frontier_relaxed_rmp_intervals_attempted\": "
        << result.frontier_relaxed_rmp_intervals_attempted << ",\n";
    out << "  \"frontier_relaxed_rmp_intervals_closed\": "
        << result.frontier_relaxed_rmp_intervals_closed << ",\n";
    out << "  \"frontier_relaxed_rmp_intervals_fathomed\": "
        << result.frontier_relaxed_rmp_intervals_fathomed << ",\n";
    out << "  \"frontier_relaxed_rmp_time_seconds\": "
        << result.frontier_relaxed_rmp_time_seconds << ",\n";
    out << "  \"frontier_lb_improved_by_relaxed_rmp\": "
        << result.frontier_lb_improved_by_relaxed_rmp << ",\n";
    out << "  \"frontier_relaxed_rmp_cg_intervals_attempted\": "
        << result.frontier_relaxed_rmp_cg_intervals_attempted << ",\n";
    out << "  \"frontier_relaxed_rmp_cg_intervals_closed\": "
        << result.frontier_relaxed_rmp_cg_intervals_closed << ",\n";
    out << "  \"frontier_relaxed_rmp_cg_intervals_fathomed\": "
        << result.frontier_relaxed_rmp_cg_intervals_fathomed << ",\n";
    out << "  \"frontier_relaxed_rmp_cg_lb_improvements\": "
        << result.frontier_relaxed_rmp_cg_lb_improvements << ",\n";
    out << "  \"frontier_relaxed_rmp_cg_time_seconds\": "
        << result.frontier_relaxed_rmp_cg_time_seconds << ",\n";
    out << "  \"incumbent_relaxed_columns_rejected\": "
        << result.incumbent_relaxed_columns_rejected << ",\n";
    out << "  \"route_pool_relaxed_columns_excluded\": "
        << result.route_pool_relaxed_columns_excluded << ",\n";
    out << "  \"exported_relaxed_columns_excluded\": "
        << result.exported_relaxed_columns_excluded << ",\n";
    out << "  \"large_relaxed_rmp_enabled\": "
        << (result.large_relaxed_rmp_enabled ? "true" : "false") << ",\n";
    out << "  \"large_relaxed_rmp_lb\": "
        << result.large_relaxed_rmp_lb << ",\n";
    out << "  \"large_relaxed_rmp_closed\": "
        << (result.large_relaxed_rmp_closed ? "true" : "false") << ",\n";
    out << "  \"large_relaxed_rmp_scope\": \""
        << jsonEscape(result.large_relaxed_rmp_scope) << "\",\n";
    out << "  \"large_relaxed_rmp_columns\": "
        << result.large_relaxed_rmp_columns << ",\n";
    out << "  \"large_relaxed_rmp_time_seconds\": "
        << result.large_relaxed_rmp_time_seconds << ",\n";
    out << "  \"large_relaxed_rmp_cg_enabled\": "
        << (result.large_relaxed_rmp_cg_enabled ? "true" : "false") << ",\n";
    out << "  \"large_relaxed_rmp_columns_generated\": "
        << result.large_relaxed_rmp_columns_generated << ",\n";
    out << "  \"large_relaxed_rmp_columns_inserted\": "
        << result.large_relaxed_rmp_columns_inserted << ",\n";
    out << "  \"large_relaxed_rmp_diagnostic_lb\": "
        << result.large_relaxed_rmp_diagnostic_lb << ",\n";
    out << "  \"large_relaxed_rmp_valid_lb\": "
        << result.large_relaxed_rmp_valid_lb << ",\n";
    out << "  \"large_relaxed_rmp_pricing_closed\": "
        << (result.large_relaxed_rmp_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"large_relaxed_rmp_closure_gap\": "
        << result.large_relaxed_rmp_closure_gap << ",\n";
    out << "  \"large_relaxed_rmp_stop_reason\": \""
        << jsonEscape(result.large_relaxed_rmp_stop_reason) << "\",\n";
    out << "  \"bpc_pricing_engine_requested\": \""
        << jsonEscape(result.bpc_pricing_engine_requested) << "\",\n";
    out << "  \"bpc_pricing_engine_used\": \""
        << jsonEscape(result.bpc_pricing_engine_used) << "\",\n";
    out << "  \"bpc_pricing_engine_fallbacks\": "
        << result.bpc_pricing_engine_fallbacks << ",\n";
    out << "  \"bpc_nodes_using_ng_dssr\": "
        << result.bpc_nodes_using_ng_dssr << ",\n";
    out << "  \"bpc_nodes_using_exact_label\": "
        << result.bpc_nodes_using_exact_label << ",\n";
    out << "  \"bpc_nodes_using_hybrid\": "
        << result.bpc_nodes_using_hybrid << ",\n";
    out << "  \"bpc_nodes_exactly_priced\": "
        << result.bpc_nodes_exactly_priced << ",\n";
    out << "  \"bpc_nodes_dssr_incomplete\": "
        << result.bpc_nodes_dssr_incomplete << ",\n";
    out << "  \"bpc_nodes_final_verifier_called\": "
        << result.bpc_nodes_final_verifier_called << ",\n";
    out << "  \"bpc_nodes_final_verifier_completed\": "
        << result.bpc_nodes_final_verifier_completed << ",\n";
    out << "  \"ng_size\": " << result.ng_size << ",\n";
    out << "  \"ng_neighborhood_mode\": \""
        << jsonEscape(result.ng_neighborhood_mode) << "\",\n";
    out << "  \"ng_memory_total\": " << result.ng_memory_total << ",\n";
    out << "  \"dssr_memory_total_initial\": "
        << result.dssr_memory_total_initial << ",\n";
    out << "  \"dssr_memory_total_final\": "
        << result.dssr_memory_total_final << ",\n";
    out << "  \"dssr_rounds\": " << result.dssr_rounds << ",\n";
    out << "  \"dssr_memory_expansions\": "
        << result.dssr_memory_expansions << ",\n";
    out << "  \"dssr_repeated_station_events\": "
        << result.dssr_repeated_station_events << ",\n";
    out << "  \"dssr_relaxed_negative_routes\": "
        << result.dssr_relaxed_negative_routes << ",\n";
    out << "  \"dssr_non_elementary_routes\": "
        << result.dssr_non_elementary_routes << ",\n";
    out << "  \"dssr_elementary_columns_found\": "
        << result.dssr_elementary_columns_found << ",\n";
    out << "  \"dssr_no_negative_relaxed_route\": "
        << (result.dssr_no_negative_relaxed_route ? "true" : "false") << ",\n";
    out << "  \"dssr_final_exact\": "
        << (result.dssr_final_exact ? "true" : "false") << ",\n";
    out << "  \"dssr_exact_closure_proved\": "
        << (result.dssr_exact_closure_proved ? "true" : "false") << ",\n";
    out << "  \"dssr_final_exact_verification_time\": "
        << result.dssr_final_exact_verification_time << ",\n";
    out << "  \"dssr_time_seconds\": "
        << result.dssr_time_seconds << ",\n";
    out << "  \"dssr_stop_reason\": \""
        << jsonEscape(result.dssr_stop_reason) << "\",\n";
    out << "  \"large_lb_mode\": \""
        << jsonEscape(result.large_lb_mode) << "\",\n";
    out << "  \"large_lb_value\": "
        << result.large_lb_value << ",\n";
    out << "  \"large_lb_valid_global\": "
        << (result.large_lb_valid_global ? "true" : "false") << ",\n";
    out << "  \"large_lb_scope\": \""
        << jsonEscape(result.large_lb_scope) << "\",\n";
    out << "  \"large_lb_time_seconds\": "
        << result.large_lb_time_seconds << ",\n";
    out << "  \"large_lb_rejection_reason\": \""
        << jsonEscape(result.large_lb_rejection_reason) << "\",\n";
    out << "  \"route_mask_count_before_support_duration\": "
        << result.route_mask_count_before_support_duration << ",\n";
    out << "  \"route_mask_count_after_support_duration\": "
        << result.route_mask_count_after_support_duration << ",\n";
    out << "  \"route_masks_removed_by_support_duration\": "
        << result.route_masks_removed_by_support_duration << ",\n";
    out << "  \"route_mask_support_duration_precompute_time_seconds\": "
        << result.route_mask_support_duration_precompute_time_seconds << ",\n";
    out << "  \"route_mask_support_duration_max_removed_subset_size\": "
        << result.route_mask_support_duration_max_removed_subset_size << ",\n";
    out << "  \"route_mask_support_duration_pruning\": "
        << (result.route_mask_support_duration_pruning ? "true" : "false") << ",\n";
    out << "  \"route_mask_operation_budget_cuts_added\": "
        << result.route_mask_operation_budget_cuts_added << ",\n";
    out << "  \"route_mask_operation_budget_min\": "
        << result.route_mask_operation_budget_min << ",\n";
    out << "  \"route_mask_operation_budget_avg\": "
        << result.route_mask_operation_budget_avg << ",\n";
    out << "  \"route_mask_operation_budget_max\": "
        << result.route_mask_operation_budget_max << ",\n";
    out << "  \"route_mask_operation_budget_tightened_masks\": "
        << result.route_mask_operation_budget_tightened_masks << ",\n";
    out << "  \"route_mask_operation_budget_zero_masks\": "
        << result.route_mask_operation_budget_zero_masks << ",\n";
    out << "  \"route_mask_operation_budget_precompute_time_seconds\": "
        << result.route_mask_operation_budget_precompute_time_seconds << ",\n";
    out << "  \"movement_domains_tightened_count\": "
        << result.movement_domains_tightened_count << ",\n";
    out << "  \"movement_domain_width_before\": "
        << result.movement_domain_width_before << ",\n";
    out << "  \"movement_domain_width_after\": "
        << result.movement_domain_width_after << ",\n";
    out << "  \"movement_tightening_time_seconds\": "
        << result.movement_tightening_time_seconds << ",\n";
    out << "  \"movement_unreachable_station_count\": "
        << result.movement_unreachable_station_count << ",\n";
    out << "  \"relaxation_lb_no_movement\": " << result.relaxation_lb_no_movement << ",\n";
    out << "  \"relaxation_lb_with_movement\": " << result.relaxation_lb_with_movement << ",\n";
    out << "  \"relaxation_lb_used\": " << result.relaxation_lb_used << ",\n";
    out << "  \"movement_audit_enabled\": "
        << (result.movement_audit_enabled ? "true" : "false") << ",\n";
    out << "  \"movement_audit_intervals\": " << result.movement_audit_intervals << ",\n";
    out << "  \"movement_audit_bound_improved_count\": "
        << result.movement_audit_bound_improved_count << ",\n";
    out << "  \"movement_audit_bound_worse_count\": "
        << result.movement_audit_bound_worse_count << ",\n";
    out << "  \"frontier_relevant_intervals\": " << result.frontier_relevant_intervals << ",\n";
    out << "  \"frontier_min_interval_lower_bound\": "
        << result.frontier_min_interval_lower_bound << ",\n";
    out << "  \"frontier_lower_bound_source\": \""
        << jsonEscape(result.frontier_lower_bound_source) << "\",\n";
    out << "  \"frontier_unprocessed_interval_count\": "
        << result.frontier_unprocessed_interval_count << ",\n";
    out << "  \"frontier_bound_fathomed_interval_count\": "
        << result.frontier_bound_fathomed_interval_count << ",\n";
    out << "  \"frontier_tree_closed_interval_count\": "
        << result.frontier_tree_closed_interval_count << ",\n";
    out << "  \"intervals_closed_by_relaxation_count\": "
        << result.intervals_closed_by_relaxation_count << ",\n";
    out << "  \"intervals_closed_by_bpc_count\": "
        << result.intervals_closed_by_bpc_count << ",\n";
    out << "  \"intervals_closed_by_oracle_count\": "
        << result.intervals_closed_by_oracle_count << ",\n";
    out << "  \"intervals_unresolved_count\": "
        << result.intervals_unresolved_count << ",\n";
    out << "  \"certificate_uses_interval_oracle\": "
        << (result.certificate_uses_interval_oracle ? "true" : "false") << ",\n";
    out << "  \"certificate_uses_bpc_tree\": "
        << (result.certificate_uses_bpc_tree ? "true" : "false") << ",\n";
    out << "  \"certificate_uses_relaxation_only\": "
        << (result.certificate_uses_relaxation_only ? "true" : "false") << ",\n";
    out << "  \"bpc_core_certificate_valid\": "
        << (result.bpc_core_certificate_valid ? "true" : "false") << ",\n";
    out << "  \"exact_portfolio_certificate_valid\": "
        << (result.exact_portfolio_certificate_valid ? "true" : "false") << ",\n";
    out << "  \"frontier_scheduling_mode\": \""
        << jsonEscape(result.frontier_scheduling_mode) << "\",\n";
    out << "  \"frontier_relax_cache_hits\": " << result.frontier_relax_cache_hits << ",\n";
    out << "  \"frontier_relax_cache_misses\": " << result.frontier_relax_cache_misses << ",\n";
    out << "  \"frontier_relax_cache_partial_hits\": "
        << result.frontier_relax_cache_partial_hits << ",\n";
    out << "  \"frontier_relax_cache_recomputed\": "
        << result.frontier_relax_cache_recomputed << ",\n";
    out << "  \"frontier_relax_cache_best_bound_reused\": "
        << result.frontier_relax_cache_best_bound_reused << ",\n";
    out << "  \"frontier_relax_cache_time_saved_estimate\": "
        << result.frontier_relax_cache_time_saved_estimate << ",\n";
    out << "  \"interval_processing_order\": \""
        << jsonEscape(result.interval_processing_order) << "\",\n";
    out << "  \"cheap_prepass_enabled\": "
        << (result.cheap_prepass_enabled ? "true" : "false") << ",\n";
    out << "  \"interval_processing_order_initial\": \""
        << jsonEscape(result.interval_processing_order_initial) << "\",\n";
    out << "  \"interval_processing_order_actual\": \""
        << jsonEscape(result.interval_processing_order_actual) << "\",\n";
    out << "  \"interval_priority_rebuild_count\": "
        << result.interval_priority_rebuild_count << ",\n";
    out << "  \"intervals_skipped_by_cheap_bound\": "
        << result.intervals_skipped_by_cheap_bound << ",\n";
    out << "  \"frontier_cache_hits\": " << result.frontier_cache_hits << ",\n";
    out << "  \"frontier_cache_columns_loaded\": " << result.frontier_cache_columns_loaded << ",\n";
    out << "  \"frontier_cache_columns_inserted\": " << result.frontier_cache_columns_inserted << ",\n";
    out << "  \"frontier_cache_time_seconds\": " << result.frontier_cache_time_seconds << ",\n";
    out << "  \"incumbent_source\": \"" << jsonEscape(result.incumbent_source) << "\",\n";
    out << "  \"incumbent_source_detail\": \""
        << jsonEscape(result.incumbent_source_detail) << "\",\n";
    out << "  \"incumbent_source_category\": \""
        << jsonEscape(result.incumbent_source_category) << "\",\n";
    out << "  \"incumbent_source_is_paper_reproducible\": "
        << (result.incumbent_source_is_paper_reproducible ? "true" : "false") << ",\n";
    out << "  \"incumbent_source_contributes_lower_bound\": "
        << (result.incumbent_source_contributes_lower_bound ? "true" : "false") << ",\n";
    out << "  \"primal_heuristic\": \""
        << jsonEscape(result.primal_heuristic) << "\",\n";
    out << "  \"hga_stop_mode\": \""
        << jsonEscape(result.hga_stop_mode) << "\",\n";
    out << "  \"hga_total_generations\": "
        << result.hga_total_generations << ",\n";
    out << "  \"hga_generations_since_improvement\": "
        << result.hga_generations_since_improvement << ",\n";
    out << "  \"hga_objective_improvement_count\": "
        << result.hga_objective_improvement_count << ",\n";
    out << "  \"hga_decoder_calls\": " << result.hga_decoder_calls << ",\n";
    out << "  \"hga_final_fitness\": " << result.hga_final_fitness << ",\n";
    out << "  \"hga_verified_objective\": "
        << result.hga_verified_objective << ",\n";
    out << "  \"hga_wall_time_seconds\": "
        << result.hga_wall_time_seconds << ",\n";
    out << "  \"hga_generation_log_path\": \""
        << jsonEscape(result.hga_generation_log_path) << "\",\n";
    out << "  \"incumbent_import_attempted\": "
        << (result.incumbent_import_attempted ? "true" : "false") << ",\n";
    out << "  \"incumbent_import_verified\": "
        << (result.incumbent_import_verified ? "true" : "false") << ",\n";
    out << "  \"incumbent_import_objective\": " << result.incumbent_import_objective << ",\n";
    out << "  \"incumbent_import_G\": " << result.incumbent_import_G << ",\n";
    out << "  \"incumbent_import_P\": " << result.incumbent_import_P << ",\n";
    out << "  \"external_incumbent_attempted\": "
        << (result.external_incumbent_attempted ? "true" : "false") << ",\n";
    out << "  \"external_incumbent_verified\": "
        << (result.external_incumbent_verified ? "true" : "false") << ",\n";
    out << "  \"external_incumbent_objective\": "
        << result.external_incumbent_objective << ",\n";
    out << "  \"external_incumbent_G\": "
        << result.external_incumbent_G << ",\n";
    out << "  \"external_incumbent_P\": "
        << result.external_incumbent_P << ",\n";
    out << "  \"external_incumbent_rejection_reason\": \""
        << jsonEscape(result.external_incumbent_rejection_reason) << "\",\n";
    out << "  \"incumbent_generation_time_seconds\": "
        << result.incumbent_generation_time_seconds << ",\n";
    out << "  \"incumbent_generation_method\": \""
        << jsonEscape(result.incumbent_generation_method) << "\",\n";
    out << "  \"incumbent_candidates_tested\": "
        << result.incumbent_candidates_tested << ",\n";
    out << "  \"incumbent_candidates_verified\": "
        << result.incumbent_candidates_verified << ",\n";
    out << "  \"incumbent_candidates_rejected\": "
        << result.incumbent_candidates_rejected << ",\n";
    out << "  \"incumbent_best_source\": \""
        << jsonEscape(result.incumbent_best_source) << "\",\n";
    out << "  \"incumbent_best_objective\": "
        << result.incumbent_best_objective << ",\n";
    out << "  \"incumbent_best_G\": " << result.incumbent_best_G << ",\n";
    out << "  \"incumbent_best_P\": " << result.incumbent_best_P << ",\n";
    out << "  \"incumbent_best_runtime\": "
        << result.incumbent_best_runtime << ",\n";
    out << "  \"incumbent_selection_reason\": \""
        << jsonEscape(result.incumbent_selection_reason) << "\",\n";
    out << "  \"incumbent_import_errors\": [";
    for (std::size_t i = 0; i < result.incumbent_import_errors.size(); ++i) {
        if (i) out << ", ";
        out << "\"" << jsonEscape(result.incumbent_import_errors[i]) << "\"";
    }
    out << "],\n";
    out << "  \"focused_retry_enabled\": "
        << (result.focused_retry_enabled ? "true" : "false") << ",\n";
    out << "  \"focused_retry_attempts\": " << result.focused_retry_attempts << ",\n";
    out << "  \"focused_retry_intervals\": " << result.focused_retry_intervals << ",\n";
    out << "  \"focused_retry_selected_interval_ids\": \""
        << jsonEscape(result.focused_retry_selected_interval_ids) << "\",\n";
    out << "  \"focused_retry_lb_before\": \""
        << jsonEscape(result.focused_retry_lb_before) << "\",\n";
    out << "  \"focused_retry_lb_after\": \""
        << jsonEscape(result.focused_retry_lb_after) << "\",\n";
    out << "  \"focused_retry_lb_improvements\": "
        << result.focused_retry_lb_improvements << ",\n";
    out << "  \"focused_retry_open_nodes_before\": \""
        << jsonEscape(result.focused_retry_open_nodes_before) << "\",\n";
    out << "  \"focused_retry_open_nodes_after\": \""
        << jsonEscape(result.focused_retry_open_nodes_after) << "\",\n";
    out << "  \"focused_retry_seconds\": " << result.focused_retry_seconds << ",\n";
    out << "  \"focused_retry_stopped_reason\": \""
        << jsonEscape(result.focused_retry_stopped_reason) << "\",\n";
    out << "  \"route_pool_columns_raw\": " << result.route_pool_columns_raw << ",\n";
    out << "  \"route_pool_columns_after_dominance\": "
        << result.route_pool_columns_after_dominance << ",\n";
    out << "  \"route_pool_columns_removed_by_dominance\": "
        << result.route_pool_columns_removed_by_dominance << ",\n";
    out << "  \"route_pool_columns_exported_from_tree\": "
        << result.route_pool_columns_exported_from_tree << ",\n";
    out << "  \"route_pool_columns_exported_from_pricing\": "
        << result.route_pool_columns_exported_from_pricing << ",\n";
    out << "  \"route_pool_columns_exported_from_warmstart\": "
        << result.route_pool_columns_exported_from_warmstart << ",\n";
    out << "  \"route_pool_columns_exported_from_integer_leaves\": "
        << result.route_pool_columns_exported_from_integer_leaves << ",\n";
    out << "  \"route_pool_columns_dropped_by_cap\": "
        << result.route_pool_columns_dropped_by_cap << ",\n";
    out << "  \"route_pool_incumbent_master_calls\": "
        << result.route_pool_incumbent_master_calls << ",\n";
    out << "  \"route_pool_incumbent_master_states\": "
        << result.route_pool_incumbent_master_states << ",\n";
    out << "  \"route_pool_incumbent_master_time_seconds\": "
        << result.route_pool_incumbent_master_time_seconds << ",\n";
    out << "  \"route_pool_incumbent_found\": "
        << (result.route_pool_incumbent_found ? "true" : "false") << ",\n";
    out << "  \"route_pool_incumbent_objective\": "
        << result.route_pool_incumbent_objective << ",\n";
    out << "  \"route_pool_incumbent_G\": " << result.route_pool_incumbent_G << ",\n";
    out << "  \"route_pool_incumbent_P\": " << result.route_pool_incumbent_P << ",\n";
    out << "  \"route_pool_incumbent_verified\": "
        << (result.route_pool_incumbent_verified ? "true" : "false") << ",\n";
    out << "  \"route_pool_incumbent_source\": \""
        << jsonEscape(result.route_pool_incumbent_source) << "\",\n";
    out << "  \"interval_candidates_found\": "
        << result.interval_candidates_found << ",\n";
    out << "  \"interval_candidates_verified\": "
        << result.interval_candidates_verified << ",\n";
    out << "  \"interval_candidates_accepted\": "
        << result.interval_candidates_accepted << ",\n";
    out << "  \"interval_candidates_rejected\": "
        << result.interval_candidates_rejected << ",\n";
    out << "  \"best_interval_candidate_objective\": "
        << result.best_interval_candidate_objective << ",\n";
    out << "  \"best_interval_candidate_rejection_reason\": \""
        << jsonEscape(result.best_interval_candidate_rejection_reason) << "\",\n";
    out << "  \"focused_intensification_enabled\": "
        << (result.focused_intensification_enabled ? "true" : "false") << ",\n";
    out << "  \"focused_intensification_passes\": "
        << result.focused_intensification_passes << ",\n";
    out << "  \"focused_intensification_intervals\": "
        << result.focused_intensification_intervals << ",\n";
    out << "  \"focused_intensification_relax_calls\": "
        << result.focused_intensification_relax_calls << ",\n";
    out << "  \"focused_intensification_tree_calls\": "
        << result.focused_intensification_tree_calls << ",\n";
    out << "  \"focused_intensification_lb_before\": \""
        << jsonEscape(result.focused_intensification_lb_before) << "\",\n";
    out << "  \"focused_intensification_lb_after\": \""
        << jsonEscape(result.focused_intensification_lb_after) << "\",\n";
    out << "  \"focused_intensification_lb_improvements\": "
        << result.focused_intensification_lb_improvements << ",\n";
    out << "  \"focused_intensification_time_seconds\": "
        << result.focused_intensification_time_seconds << ",\n";
    out << "  \"focused_intensification_stop_reason\": \""
        << jsonEscape(result.focused_intensification_stop_reason) << "\",\n";
    out << "  \"focused_intensification_split_triggered\": "
        << (result.focused_intensification_split_triggered ? "true" : "false") << ",\n";
    out << "  \"focused_intensification_operation_budget_enabled\": "
        << (result.focused_intensification_operation_budget_enabled ? "true" : "false") << ",\n";
    out << "  \"focused_intensification_child_intervals_processed\": "
        << result.focused_intensification_child_intervals_processed << ",\n";
    out << "  \"focused_intensification_best_child_lb\": "
        << result.focused_intensification_best_child_lb << ",\n";
    out << "  \"adaptive_split_enabled\": "
        << (result.adaptive_split_enabled ? "true" : "false") << ",\n";
    out << "  \"adaptive_split_intervals_created\": "
        << result.adaptive_split_intervals_created << ",\n";
    out << "  \"adaptive_split_max_depth_reached\": "
        << (result.adaptive_split_max_depth_reached ? "true" : "false") << ",\n";
    out << "  \"adaptive_split_global_min_interval_before\": \""
        << jsonEscape(result.adaptive_split_global_min_interval_before) << "\",\n";
    out << "  \"adaptive_split_global_min_interval_after\": \""
        << jsonEscape(result.adaptive_split_global_min_interval_after) << "\",\n";
    out << "  \"adaptive_split_lb_improvements\": "
        << result.adaptive_split_lb_improvements << ",\n";
    out << "  \"adaptive_split_time_seconds\": "
        << result.adaptive_split_time_seconds << ",\n";
    out << "  \"pickup_drop_pairs_total\": "
        << result.pickup_drop_pairs_total << ",\n";
    out << "  \"pickup_drop_pairs_compatible\": "
        << result.pickup_drop_pairs_compatible << ",\n";
    out << "  \"pickup_drop_pairs_incompatible\": "
        << result.pickup_drop_pairs_incompatible << ",\n";
    out << "  \"pickup_drop_pairs_capacity_limited\": "
        << result.pickup_drop_pairs_capacity_limited << ",\n";
    out << "  \"pickup_drop_transfer_cap_min\": "
        << result.pickup_drop_transfer_cap_min << ",\n";
    out << "  \"pickup_drop_transfer_cap_avg\": "
        << result.pickup_drop_transfer_cap_avg << ",\n";
    out << "  \"pickup_drop_transfer_cap_max\": "
        << result.pickup_drop_transfer_cap_max << ",\n";
    out << "  \"pickup_drop_transfer_cap_variables\": "
        << result.pickup_drop_transfer_cap_variables << ",\n";
    out << "  \"pickup_drop_transfer_cap_constraints\": "
        << result.pickup_drop_transfer_cap_constraints << ",\n";
    out << "  \"pickup_drop_transfer_cap_time_seconds\": "
        << result.pickup_drop_transfer_cap_time_seconds << ",\n";
    out << "  \"pickup_drop_compat_flow_variables\": "
        << result.pickup_drop_compat_flow_variables << ",\n";
    out << "  \"pickup_drop_compat_flow_constraints\": "
        << result.pickup_drop_compat_flow_constraints << ",\n";
    out << "  \"pickup_drop_compat_flow_time_seconds\": "
        << result.pickup_drop_compat_flow_time_seconds << ",\n";
    out << "  \"vehicle_indexed_operation_relaxation_enabled\": "
        << (result.vehicle_indexed_operation_relaxation_enabled ? "true" : "false") << ",\n";
    out << "  \"vehicle_indexed_y_variables\": "
        << result.vehicle_indexed_y_variables << ",\n";
    out << "  \"vehicle_indexed_pickup_variables\": "
        << result.vehicle_indexed_pickup_variables << ",\n";
    out << "  \"vehicle_indexed_drop_variables\": "
        << result.vehicle_indexed_drop_variables << ",\n";
    out << "  \"vehicle_indexed_linking_constraints\": "
        << result.vehicle_indexed_linking_constraints << ",\n";
    out << "  \"vehicle_indexed_balance_constraints\": "
        << result.vehicle_indexed_balance_constraints << ",\n";
    out << "  \"vehicle_indexed_operation_budget_constraints\": "
        << result.vehicle_indexed_operation_budget_constraints << ",\n";
    out << "  \"vehicle_indexed_relaxation_time_seconds\": "
        << result.vehicle_indexed_relaxation_time_seconds << ",\n";
    out << "  \"v20_cover_candidate_subsets_tested\": "
        << result.v20_cover_candidate_subsets_tested << ",\n";
    out << "  \"v20_cover_cuts_added\": "
        << result.v20_cover_cuts_added << ",\n";
    out << "  \"v20_cover_max_size_used\": "
        << result.v20_cover_max_size_used << ",\n";
    out << "  \"v20_cover_separation_time_seconds\": "
        << result.v20_cover_separation_time_seconds << ",\n";
    out << "  \"station_residual_cover_cuts_enabled\": "
        << (result.station_residual_cover_cuts_enabled ? "true" : "false") << ",\n";
    out << "  \"station_residual_domains_tightened_count\": "
        << result.station_residual_domains_tightened_count << ",\n";
    out << "  \"station_residual_domain_width_before\": "
        << result.station_residual_domain_width_before << ",\n";
    out << "  \"station_residual_domain_width_after\": "
        << result.station_residual_domain_width_after << ",\n";
    out << "  \"station_residual_cover_cuts_added\": "
        << result.station_residual_cover_cuts_added << ",\n";
    out << "  \"station_residual_cover_time_seconds\": "
        << result.station_residual_cover_time_seconds << ",\n";
    out << "  \"large_compact_flow_relaxation\": \""
        << jsonEscape(result.large_compact_flow_relaxation) << "\",\n";
    out << "  \"large_compact_flow_arc_variables\": "
        << result.large_compact_flow_arc_variables << ",\n";
    out << "  \"large_compact_flow_constraints\": "
        << result.large_compact_flow_constraints << ",\n";
    out << "  \"large_compact_flow_time_seconds\": "
        << result.large_compact_flow_time_seconds << ",\n";
    out << "  \"large_compact_flow_connectivity_enabled\": "
        << (result.large_compact_flow_connectivity_enabled ? "true" : "false") << ",\n";
    out << "  \"large_compact_flow_connectivity_variables\": "
        << result.large_compact_flow_connectivity_variables << ",\n";
    out << "  \"large_compact_flow_connectivity_constraints\": "
        << result.large_compact_flow_connectivity_constraints << ",\n";
    out << "  \"large_compact_flow_connectivity_time_seconds\": "
        << result.large_compact_flow_connectivity_time_seconds << ",\n";
    out << "  \"service_operation_min_handling_cuts_enabled\": "
        << (result.service_operation_min_handling_cuts_enabled ? "true" : "false") << ",\n";
    out << "  \"service_operation_min_handling_cuts_added\": "
        << result.service_operation_min_handling_cuts_added << ",\n";
    out << "  \"penalty_movement_lb_cuts_enabled\": "
        << (result.penalty_movement_lb_cuts_enabled ? "true" : "false") << ",\n";
    out << "  \"penalty_movement_required_units\": "
        << result.penalty_movement_required_units << ",\n";
    out << "  \"penalty_movement_lb_cuts_added\": "
        << result.penalty_movement_lb_cuts_added << ",\n";
    out << "  \"transfer_subset_capacity_cuts_enabled\": "
        << (result.transfer_subset_capacity_cuts_enabled ? "true" : "false") << ",\n";
    out << "  \"transfer_subset_capacity_cuts_added\": "
        << result.transfer_subset_capacity_cuts_added << ",\n";
    out << "  \"relaxation_portfolio_mode\": \""
        << jsonEscape(result.relaxation_portfolio_mode) << "\",\n";
    out << "  \"relaxation_variants_tried\": \""
        << jsonEscape(result.relaxation_variants_tried) << "\",\n";
    out << "  \"selected_relaxation_variant\": \""
        << jsonEscape(result.selected_relaxation_variant) << "\",\n";
    out << "  \"selected_variant_reason\": \""
        << jsonEscape(result.selected_variant_reason) << "\",\n";
    out << "  \"probe_time_seconds\": "
        << result.relaxation_portfolio_probe_time_seconds << ",\n";
    out << "  \"variant_bound_improvement\": "
        << result.relaxation_portfolio_variant_bound_improvement << ",\n";
    out << "  \"best_variant_bound\": "
        << result.relaxation_portfolio_best_variant_bound << ",\n";
    out << "  \"variants_skipped_reason\": \""
        << jsonEscape(result.relaxation_portfolio_variants_skipped_reason) << "\",\n";
    out << "  \"relaxation_certificate_mode\": \""
        << jsonEscape(result.relaxation_certificate_mode) << "\",\n";
    out << "  \"cutoff_feasibility_attempted\": "
        << (result.cutoff_feasibility_attempted ? "true" : "false") << ",\n";
    out << "  \"cutoff_feasibility_infeasible\": "
        << (result.cutoff_feasibility_infeasible ? "true" : "false") << ",\n";
    out << "  \"cutoff_feasibility_timed_out\": "
        << (result.cutoff_feasibility_timed_out ? "true" : "false") << ",\n";
    out << "  \"cutoff_feasibility_epsilon\": "
        << result.cutoff_feasibility_epsilon << ",\n";
    out << "  \"cutoff_feasibility_time_seconds\": "
        << result.cutoff_feasibility_time_seconds << ",\n";
    out << "  \"cutoff_feasibility_status\": \""
        << jsonEscape(result.cutoff_feasibility_status) << "\",\n";
    out << "  \"interval_exact_cutoff_oracle\": \""
        << jsonEscape(result.interval_exact_cutoff_oracle) << "\",\n";
    out << "  \"interval_exact_cutoff_attempted\": "
        << (result.interval_exact_cutoff_attempted ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_gamma_L\": "
        << result.interval_exact_cutoff_gamma_L << ",\n";
    out << "  \"interval_exact_cutoff_gamma_U\": "
        << result.interval_exact_cutoff_gamma_U << ",\n";
    out << "  \"interval_exact_cutoff_UB\": "
        << result.interval_exact_cutoff_UB << ",\n";
    out << "  \"interval_exact_cutoff_epsilon\": "
        << result.interval_exact_cutoff_epsilon << ",\n";
    out << "  \"interval_exact_cutoff_runtime_seconds\": "
        << result.interval_exact_cutoff_runtime_seconds << ",\n";
    out << "  \"interval_exact_cutoff_solver_status\": \""
        << jsonEscape(result.interval_exact_cutoff_solver_status) << "\",\n";
    out << "  \"interval_exact_cutoff_native_status_code\": "
        << result.interval_exact_cutoff_native_status_code << ",\n";
    out << "  \"interval_exact_cutoff_native_status_class\": \""
        << jsonEscape(result.interval_exact_cutoff_native_status_class)
        << "\",\n";
    out << "  \"interval_exact_cutoff_native_status_available\": "
        << (result.interval_exact_cutoff_native_status_available
                ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_native_exact_optimal\": "
        << (result.interval_exact_cutoff_native_exact_optimal
                ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_native_tolerance_optimal\": "
        << (result.interval_exact_cutoff_native_tolerance_optimal
                ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_native_optimal_unscaled_infeasibilities\": "
        << (result.interval_exact_cutoff_native_optimal_unscaled_infeasibilities
                ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_native_lifecycle_valid\": "
        << (result.interval_exact_cutoff_native_lifecycle_valid
                ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_certificate_basis\": \""
        << jsonEscape(result.interval_exact_cutoff_certificate_basis) << "\",\n";
    out << "  \"interval_exact_cutoff_proven_infeasible\": "
        << (result.interval_exact_cutoff_proven_infeasible ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_feasible_improving\": "
        << (result.interval_exact_cutoff_feasible_improving ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_timeout\": "
        << (result.interval_exact_cutoff_timeout ? "true" : "false") << ",\n";
    out << "  \"interval_exact_cutoff_best_bound\": "
        << result.interval_exact_cutoff_best_bound << ",\n";
    out << "  \"interval_exact_cutoff_objective\": "
        << result.interval_exact_cutoff_objective << ",\n";
    out << "  \"interval_exact_cutoff_gap\": "
        << result.interval_exact_cutoff_gap << ",\n";
    out << "  \"interval_exact_cutoff_nodes\": "
        << result.interval_exact_cutoff_nodes << ",\n";
    out << "  \"interval_exact_cutoff_lp_path\": \""
        << jsonEscape(result.interval_exact_cutoff_lp_path) << "\",\n";
    out << "  \"interval_exact_cutoff_solution_path\": \""
        << jsonEscape(result.interval_exact_cutoff_solution_path) << "\",\n";
    out << "  \"interval_exact_cutoff_log_path\": \""
        << jsonEscape(result.interval_exact_cutoff_log_path) << "\",\n";
    out << "  \"interval_exact_cutoff_scope\": \""
        << jsonEscape(result.interval_exact_cutoff_scope) << "\",\n";
    out << "  \"interval_oracle_model_type\": \""
        << jsonEscape(result.interval_oracle_model_type) << "\",\n";
    out << "  \"interval_oracle_bound_valid\": "
        << (result.interval_oracle_bound_valid ? "true" : "false") << ",\n";
    out << "  \"interval_oracle_bound_scope\": \""
        << jsonEscape(result.interval_oracle_bound_scope) << "\",\n";
    out << "  \"interval_oracle_objective_sense\": \""
        << jsonEscape(result.interval_oracle_objective_sense) << "\",\n";
    out << "  \"interval_oracle_has_objective_cutoff_row\": "
        << (result.interval_oracle_has_objective_cutoff_row ? "true" : "false") << ",\n";
    out << "  \"interval_oracle_has_gamma_interval_rows\": "
        << (result.interval_oracle_has_gamma_interval_rows ? "true" : "false") << ",\n";
    out << "  \"interval_oracle_solver_best_bound\": "
        << result.interval_oracle_solver_best_bound << ",\n";
    out << "  \"interval_oracle_solver_incumbent\": "
        << result.interval_oracle_solver_incumbent << ",\n";
    out << "  \"interval_oracle_gap_to_cutoff\": "
        << result.interval_oracle_gap_to_cutoff << ",\n";
    out << "  \"interval_oracle_can_merge_bound\": "
        << (result.interval_oracle_can_merge_bound ? "true" : "false") << ",\n";
    out << "  \"compact_interval_bc_enabled\": "
        << (result.compact_interval_bc_enabled ? "true" : "false") << ",\n";
    out << "  \"compact_bc_diagnostic_force_leaf_solve\": "
        << (result.compact_bc_diagnostic_force_leaf_solve ? "true" : "false") << ",\n";
    out << "  \"compact_interval_bc_model_type\": \""
        << jsonEscape(result.compact_interval_bc_model_type) << "\",\n";
    out << "  \"compact_interval_bc_solver\": \""
        << jsonEscape(result.compact_interval_bc_solver) << "\",\n";
    out << "  \"compact_interval_bc_threads\": "
        << result.compact_interval_bc_threads << ",\n";
    out << "  \"compact_interval_bc_cut_families_enabled\": \""
        << jsonEscape(result.compact_interval_bc_cut_families_enabled) << "\",\n";
    out << "  \"compact_interval_bc_bound_valid\": "
        << (result.compact_interval_bc_bound_valid ? "true" : "false") << ",\n";
    out << "  \"compact_interval_bc_bound_scope\": \""
        << jsonEscape(result.compact_interval_bc_bound_scope) << "\",\n";
    out << "  \"compact_interval_bc_closed_leaves\": "
        << result.compact_interval_bc_closed_leaves << ",\n";
    out << "  \"compact_interval_bc_timed_out_leaves\": "
        << result.compact_interval_bc_timed_out_leaves << ",\n";
    out << "  \"compact_interval_bc_rejection_reason\": \""
        << jsonEscape(result.compact_interval_bc_rejection_reason) << "\",\n";
    out << "  \"compact_bc_cut_profile\": \""
        << jsonEscape(result.compact_bc_cut_profile) << "\",\n";
    out << "  \"compact_bc_enabled_cut_families\": \""
        << jsonEscape(result.compact_bc_enabled_cut_families) << "\",\n";
    out << "  \"compact_bc_enabled_families_requested\": \""
        << jsonEscape(result.compact_bc_enabled_families_requested) << "\",\n";
    out << "  \"compact_bc_enabled_families_effective\": \""
        << jsonEscape(result.compact_bc_enabled_families_effective) << "\",\n";
    out << "  \"compact_bc_cuts_added_by_family\": \""
        << jsonEscape(result.compact_bc_cuts_added_by_family) << "\",\n";
    out << "  \"compact_bc_domains_tightened_by_family\": \""
        << jsonEscape(result.compact_bc_domains_tightened_by_family) << "\",\n";
    out << "  \"compact_bc_root_cut_rounds\": "
        << result.compact_bc_root_cut_rounds << ",\n";
    out << "  \"compact_bc_total_root_cut_rounds\": "
        << result.compact_bc_total_root_cut_rounds << ",\n";
    out << "  \"compact_bc_root_cut_time_limit\": "
        << result.compact_bc_root_cut_time_limit << ",\n";
    out << "  \"compact_bc_dynamic_cut_families\": \""
        << jsonEscape(result.compact_bc_dynamic_cut_families) << "\",\n";
    out << "  \"compact_bc_root_probe\": \""
        << jsonEscape(result.compact_bc_root_probe) << "\",\n";
    out << "  \"compact_bc_dynamic_cut_violation_tol\": "
        << result.compact_bc_dynamic_cut_violation_tol << ",\n";
    out << "  \"compact_bc_domain_propagation_mode\": \""
        << jsonEscape(result.compact_bc_domain_propagation_mode) << "\",\n";
    out << "  \"compact_bc_domain_propagation_rounds\": "
        << result.compact_bc_domain_propagation_rounds << ",\n";
    out << "  \"compact_bc_domain_propagation_rounds_completed\": "
        << result.compact_bc_domain_propagation_rounds_completed << ",\n";
    out << "  \"compact_bc_expensive_static_families\": \""
        << jsonEscape(result.compact_bc_expensive_static_families) << "\",\n";
    out << "  \"compact_bc_use_dynamic_instead_of_static\": "
        << (result.compact_bc_use_dynamic_instead_of_static ? "true" : "false") << ",\n";
    out << "  \"compact_bc_dynamic_cuts_added_by_family\": \""
        << jsonEscape(result.compact_bc_dynamic_cuts_added_by_family) << "\",\n";
    out << "  \"compact_bc_dynamic_max_violation_by_family\": \""
        << jsonEscape(result.compact_bc_dynamic_max_violation_by_family) << "\",\n";
    out << "  \"compact_bc_dynamic_cuts_added_total\": "
        << result.compact_bc_dynamic_cuts_added_total << ",\n";
    out << "  \"compact_bc_low_gini_strengthening\": \""
        << jsonEscape(result.compact_bc_low_gini_strengthening) << "\",\n";
    out << "  \"compact_bc_denominator_bound_mode\": \""
        << jsonEscape(result.compact_bc_denominator_bound_mode) << "\",\n";
    out << "  \"compact_bc_objective_estimator_mode\": \""
        << jsonEscape(result.compact_bc_objective_estimator_mode) << "\",\n";
    out << "  \"compact_bc_low_gini_aggressive_diagnostic\": "
        << (result.compact_bc_low_gini_aggressive_diagnostic ? "true" : "false") << ",\n";
    out << "  \"compact_bc_s_range_refinement\": \""
        << jsonEscape(result.compact_bc_s_range_refinement) << "\",\n";
    out << "  \"s_range_refinement_enabled\": "
        << (result.s_range_refinement_enabled ? "true" : "false") << ",\n";
    out << "  \"s_range_global_L\": " << result.s_range_global_L << ",\n";
    out << "  \"s_range_global_U\": " << result.s_range_global_U << ",\n";
    out << "  \"parent_S_L\": " << result.parent_S_L << ",\n";
    out << "  \"parent_S_U\": " << result.parent_S_U << ",\n";
    out << "  \"S_domain_source\": \""
        << jsonEscape(result.S_domain_source) << "\",\n";
    out << "  \"S_domain_proof_status\": \""
        << jsonEscape(result.S_domain_proof_status) << "\",\n";
    out << "  \"S_domain_audit_passed\": "
        << (result.S_domain_audit_passed ? "true" : "false") << ",\n";
    out << "  \"s_range_bucket_count\": " << result.s_range_bucket_count << ",\n";
    out << "  \"s_range_bucket_id\": " << result.s_range_bucket_id << ",\n";
    out << "  \"s_range_bucket_L\": " << result.s_range_bucket_L << ",\n";
    out << "  \"s_range_bucket_U\": " << result.s_range_bucket_U << ",\n";
    out << "  \"s_range_bucket_closed\": "
        << (result.s_range_bucket_closed ? "true" : "false") << ",\n";
    out << "  \"s_range_parent_coverage_valid\": "
        << (result.s_range_parent_coverage_valid ? "true" : "false") << ",\n";
    out << "  \"s_range_certificate_valid\": "
        << (result.s_range_certificate_valid ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_s_bucket_ledger\": \""
        << jsonEscape(result.tailored_bc_s_bucket_ledger) << "\",\n";
    out << "  \"tailored_bc_s_bucket_count\": "
        << result.tailored_bc_s_bucket_count << ",\n";
    out << "  \"tailored_bc_s_bucket_policy\": \""
        << jsonEscape(result.tailored_bc_s_bucket_policy) << "\",\n";
    out << "  \"tailored_bc_s_bucket_time_budget\": "
        << result.tailored_bc_s_bucket_time_budget << ",\n";
    out << "  \"tailored_bc_s_bucket_merge_audit\": "
        << (result.tailored_bc_s_bucket_merge_audit ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_s_bucket_max_depth\": "
        << result.tailored_bc_s_bucket_max_depth << ",\n";
    out << "  \"tailored_bc_s_bucket_min_width\": "
        << result.tailored_bc_s_bucket_min_width << ",\n";
    out << "  \"tailored_bc_s_bucket_refine_top_k\": "
        << result.tailored_bc_s_bucket_refine_top_k << ",\n";
    out << "  \"tailored_bc_s_bucket_refine_rule\": \""
        << jsonEscape(result.tailored_bc_s_bucket_refine_rule) << "\",\n";
    out << "  \"compact_bc_s_range_rows_added\": "
        << result.compact_bc_s_range_rows_added << ",\n";
    out << "  \"compact_bc_variable_s_centering\": "
        << (result.compact_bc_variable_s_centering ? "true" : "false") << ",\n";
    out << "  \"compact_bc_rmin_rmax_propagation\": \""
        << jsonEscape(result.compact_bc_rmin_rmax_propagation) << "\",\n";
    out << "  \"compact_bc_rmin_rmax_propagation_safe\": "
        << (result.compact_bc_rmin_rmax_propagation_safe ? "true" : "false") << ",\n";
    out << "  \"compact_bc_variable_s_centering_rows_added\": "
        << result.compact_bc_variable_s_centering_rows_added << ",\n";
    out << "  \"compact_bc_sp_product_estimator\": \""
        << jsonEscape(result.compact_bc_sp_product_estimator) << "\",\n";
    out << "  \"compact_bc_sp_product_bounds\": \""
        << jsonEscape(result.compact_bc_sp_product_bounds) << "\",\n";
    out << "  \"compact_bc_sp_product_paper_safe\": "
        << (result.compact_bc_sp_product_paper_safe ? "true" : "false") << ",\n";
    out << "  \"compact_bc_sp_product_mccormick_rows_added\": "
        << result.compact_bc_sp_product_mccormick_rows_added << ",\n";
    out << "  \"compact_bc_sp_product_estimator_rows_added\": "
        << result.compact_bc_sp_product_estimator_rows_added << ",\n";
    out << "  \"compact_bc_low_gini_precheck\": \""
        << jsonEscape(result.compact_bc_low_gini_precheck) << "\",\n";
    out << "  \"compact_bc_low_gini_precheck_status\": \""
        << jsonEscape(result.compact_bc_low_gini_precheck_status) << "\",\n";
    out << "  \"compact_bc_low_gini_precheck_closed\": "
        << (result.compact_bc_low_gini_precheck_closed ? "true" : "false") << ",\n";
    out << "  \"compact_bc_model_size_policy\": \""
        << jsonEscape(result.compact_bc_model_size_policy) << "\",\n";
    out << "  \"compact_bc_rows_estimated\": "
        << result.compact_bc_rows_estimated << ",\n";
    out << "  \"compact_bc_cols_estimated\": "
        << result.compact_bc_cols_estimated << ",\n";
    out << "  \"compact_bc_nonzeros_estimated\": "
        << result.compact_bc_nonzeros_estimated << ",\n";
    out << "  \"compact_bc_memory_estimate_mb\": "
        << result.compact_bc_memory_estimate_mb << ",\n";
    out << "  \"compact_bc_model_rows\": "
        << result.compact_bc_model_rows << ",\n";
    out << "  \"compact_bc_model_cols\": "
        << result.compact_bc_model_cols << ",\n";
    out << "  \"compact_bc_model_nonzeros\": "
        << result.compact_bc_model_nonzeros << ",\n";
    out << "  \"compact_bc_disabled_families_due_to_size\": \""
        << jsonEscape(result.compact_bc_disabled_families_due_to_size) << "\",\n";
    out << "  \"compact_bc_model_size_stop_reason\": \""
        << jsonEscape(result.compact_bc_model_size_stop_reason) << "\",\n";
    out << "  \"compact_bc_solver_threads\": "
        << result.compact_bc_solver_threads << ",\n";
    out << "  \"cplex_threads\": " << result.cplex_threads << ",\n";
    out << "  \"mip_threads\": " << result.mip_threads << ",\n";
    out << "  \"solver_thread_policy\": \""
        << jsonEscape(result.solver_thread_policy) << "\",\n";
    out << "  \"thread_fairness_class\": \""
        << jsonEscape(result.thread_fairness_class) << "\",\n";
    out << "  \"compact_bc_solver_status\": \""
        << jsonEscape(result.compact_bc_solver_status) << "\",\n";
    out << "  \"compact_bc_best_bound\": "
        << result.compact_bc_best_bound << ",\n";
    out << "  \"compact_bc_best_bound_available\": "
        << (result.compact_bc_best_bound_available ? "true" : "false") << ",\n";
    out << "  \"compact_bc_best_bound_fail_reason\": \""
        << jsonEscape(result.compact_bc_best_bound_fail_reason) << "\",\n";
    out << "  \"compact_bc_native_time_limit_param_id\": "
        << result.compact_bc_native_time_limit_param_id << ",\n";
    out << "  \"compact_bc_native_time_limit_seconds\": "
        << result.compact_bc_native_time_limit_seconds << ",\n";
    out << "  \"compact_bc_native_time_limit_set_rc\": "
        << result.compact_bc_native_time_limit_set_rc << ",\n";
    out << "  \"compact_bc_native_mip_gap_param_id\": "
        << result.compact_bc_native_mip_gap_param_id << ",\n";
    out << "  \"compact_bc_native_mip_gap\": "
        << result.compact_bc_native_mip_gap << ",\n";
    out << "  \"compact_bc_native_mip_gap_set_rc\": "
        << result.compact_bc_native_mip_gap_set_rc << ",\n";
    out << "  \"compact_bc_native_mip_gap_get_rc\": "
        << result.compact_bc_native_mip_gap_get_rc << ",\n";
    out << "  \"compact_bc_native_mip_gap_effective\": "
        << result.compact_bc_native_mip_gap_effective << ",\n";
    out << "  \"compact_bc_native_absolute_mip_gap_param_id\": "
        << result.compact_bc_native_absolute_mip_gap_param_id << ",\n";
    out << "  \"compact_bc_native_absolute_mip_gap\": "
        << result.compact_bc_native_absolute_mip_gap << ",\n";
    out << "  \"compact_bc_native_absolute_mip_gap_set_rc\": "
        << result.compact_bc_native_absolute_mip_gap_set_rc << ",\n";
    out << "  \"compact_bc_native_absolute_mip_gap_get_rc\": "
        << result.compact_bc_native_absolute_mip_gap_get_rc << ",\n";
    out << "  \"compact_bc_native_absolute_mip_gap_effective\": "
        << result.compact_bc_native_absolute_mip_gap_effective << ",\n";
    out << "  \"compact_bc_native_exact_zero_gaps_valid\": "
        << (result.compact_bc_native_exact_zero_gaps_valid
                ? "true" : "false") << ",\n";
    out << "  \"compact_bc_callback_abort_requests\": "
        << result.compact_bc_callback_abort_requests << ",\n";
    out << "  \"compact_bc_terminate_set_rc\": "
        << result.compact_bc_terminate_set_rc << ",\n";
    out << "  \"compact_bc_terminate_triggered\": "
        << (result.compact_bc_terminate_triggered ? "true" : "false") << ",\n";
    out << "  \"compact_bc_terminate_after_seconds\": "
        << result.compact_bc_terminate_after_seconds << ",\n";
    out << "  \"compact_bc_checkpoint_best_bound_available\": "
        << (result.compact_bc_checkpoint_best_bound_available ? "true" : "false") << ",\n";
    out << "  \"compact_bc_checkpoint_best_bound\": "
        << result.compact_bc_checkpoint_best_bound << ",\n";
    out << "  \"compact_bc_checkpoint_incumbent_available\": "
        << (result.compact_bc_checkpoint_incumbent_available ? "true" : "false") << ",\n";
    out << "  \"compact_bc_checkpoint_incumbent\": "
        << result.compact_bc_checkpoint_incumbent << ",\n";
    out << "  \"compact_bc_checkpoint_node_count\": "
        << result.compact_bc_checkpoint_node_count << ",\n";
    out << "  \"compact_bc_native_checkpoint_acceptance_status\": \""
        << jsonEscape(result.compact_bc_native_checkpoint_acceptance_status)
        << "\",\n";
    out << "  \"compact_bc_native_checkpoint_rejection_reason\": \""
        << jsonEscape(result.compact_bc_native_checkpoint_rejection_reason)
        << "\",\n";
    out << "  \"compact_bc_native_checkpoint_sequence\": "
        << result.compact_bc_native_checkpoint_sequence << ",\n";
    out << "  \"compact_bc_incumbent\": "
        << result.compact_bc_incumbent << ",\n";
    out << "  \"compact_bc_nodes\": "
        << result.compact_bc_nodes << ",\n";
    out << "  \"compact_bc_time_seconds\": "
        << result.compact_bc_time_seconds << ",\n";
    out << "  \"compact_bc_total_solver_time\": "
        << result.compact_bc_total_solver_time << ",\n";
    out << "  \"compact_bc_bound_valid\": "
        << (result.compact_bc_bound_valid ? "true" : "false") << ",\n";
    out << "  \"compact_bc_bound_scope\": \""
        << jsonEscape(result.compact_bc_bound_scope) << "\",\n";
    out << "  \"compact_bc_closed_leaf_count\": "
        << result.compact_bc_closed_leaf_count << ",\n";
    out << "  \"compact_bc_unresolved_leaf_count\": "
        << result.compact_bc_unresolved_leaf_count << ",\n";
    out << "  \"compact_bc_rejection_reason\": \""
        << jsonEscape(result.compact_bc_rejection_reason) << "\",\n";
    out << "  \"certificate_uses_compact_interval_bc\": "
        << (result.certificate_uses_compact_interval_bc ? "true" : "false") << ",\n";
    out << "  \"compact_bc_certificate_valid\": "
        << (result.compact_bc_certificate_valid ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_enabled\": "
        << (result.tailored_bc_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_mode\": \""
        << jsonEscape(result.tailored_bc_mode) << "\",\n";
    out << "  \"tailored_bc_callback_available\": "
        << (result.tailored_bc_callback_available ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_user_cut_callback_enabled\": "
        << (result.tailored_bc_user_cut_callback_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_lazy_callback_enabled\": "
        << (result.tailored_bc_lazy_callback_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_incumbent_callback_enabled\": "
        << (result.tailored_bc_incumbent_callback_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_branch_callback_enabled\": "
        << (result.tailored_bc_branch_callback_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_branch_priority_enabled\": "
        << (result.tailored_bc_branch_priority_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_gini_branch_mode\": \""
        << jsonEscape(result.tailored_bc_gini_branch_mode) << "\",\n";
    out << "  \"tailored_bc_node_separation_enabled\": "
        << (result.tailored_bc_node_separation_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_root_separation_enabled\": "
        << (result.tailored_bc_root_separation_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_user_cuts_added_total\": "
        << result.tailored_bc_user_cuts_added_total << ",\n";
    out << "  \"tailored_bc_user_cuts_added_by_family\": \""
        << jsonEscape(result.tailored_bc_user_cuts_added_by_family) << "\",\n";
    out << "  \"tailored_bc_relaxation_callback_calls\": "
        << result.tailored_bc_relaxation_callback_calls << ",\n";
    out << "  \"tailored_bc_candidate_callback_calls\": "
        << result.tailored_bc_candidate_callback_calls << ",\n";
    out << "  \"tailored_bc_branch_callback_calls\": "
        << result.tailored_bc_branch_callback_calls << ",\n";
    out << "  \"tailored_bc_progress_callback_calls\": "
        << result.tailored_bc_progress_callback_calls << ",\n";
    out << "  \"tailored_bc_callback_vector_export_claimed\": "
        << (result.tailored_bc_callback_vector_export_claimed ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_export_working\": "
        << (result.tailored_bc_callback_vector_export_working ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_export_status\": \""
        << jsonEscape(result.tailored_bc_callback_vector_export_status) << "\",\n";
    out << "  \"tailored_bc_callback_vector_context_seen\": "
        << (result.tailored_bc_callback_vector_context_seen ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_relaxation_context_seen\": "
        << (result.tailored_bc_callback_vector_relaxation_context_seen ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_candidate_context_seen\": "
        << (result.tailored_bc_callback_vector_candidate_context_seen ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_api_called\": "
        << (result.tailored_bc_callback_vector_api_called ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_vector_api_return_code\": "
        << result.tailored_bc_callback_vector_api_return_code << ",\n";
    out << "  \"tailored_bc_callback_vector_length_requested\": "
        << result.tailored_bc_callback_vector_length_requested << ",\n";
    out << "  \"tailored_bc_callback_vector_length_returned\": "
        << result.tailored_bc_callback_vector_length_returned << ",\n";
    out << "  \"tailored_bc_callback_vector_nonzero_values_count\": "
        << result.tailored_bc_callback_vector_nonzero_values_count << ",\n";
    out << "  \"tailored_bc_callback_vector_sample_variable_names\": \""
        << jsonEscape(result.tailored_bc_callback_vector_sample_variable_names) << "\",\n";
    out << "  \"tailored_bc_callback_vector_sample_variable_values\": \""
        << jsonEscape(result.tailored_bc_callback_vector_sample_variable_values) << "\",\n";
    out << "  \"tailored_bc_callback_vector_full_variable_names\": \""
        << jsonEscape(result.tailored_bc_callback_vector_full_variable_names) << "\",\n";
    out << "  \"tailored_bc_callback_vector_full_variable_values\": \""
        << jsonEscape(result.tailored_bc_callback_vector_full_variable_values) << "\",\n";
    out << "  \"tailored_bc_callback_vector_failure_reason\": \""
        << jsonEscape(result.tailored_bc_callback_vector_failure_reason) << "\",\n";
    out << "  \"tailored_bc_callback_candidate_vector_api_called\": "
        << (result.tailored_bc_callback_candidate_vector_api_called ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_callback_candidate_vector_api_return_code\": "
        << result.tailored_bc_callback_candidate_vector_api_return_code << ",\n";
    out << "  \"tailored_bc_callback_candidate_vector_length_requested\": "
        << result.tailored_bc_callback_candidate_vector_length_requested << ",\n";
    out << "  \"tailored_bc_callback_candidate_vector_length_returned\": "
        << result.tailored_bc_callback_candidate_vector_length_returned << ",\n";
    out << "  \"tailored_bc_callback_candidate_vector_nonzero_values_count\": "
        << result.tailored_bc_callback_candidate_vector_nonzero_values_count << ",\n";
    out << "  \"tailored_bc_callback_candidate_vector_sample_variable_names\": \""
        << jsonEscape(result.tailored_bc_callback_candidate_vector_sample_variable_names) << "\",\n";
    out << "  \"tailored_bc_callback_candidate_vector_sample_variable_values\": \""
        << jsonEscape(result.tailored_bc_callback_candidate_vector_sample_variable_values) << "\",\n";
    out << "  \"tailored_bc_callback_candidate_vector_full_variable_names\": \""
        << jsonEscape(result.tailored_bc_callback_candidate_vector_full_variable_names) << "\",\n";
    out << "  \"tailored_bc_callback_candidate_vector_full_variable_values\": \""
        << jsonEscape(result.tailored_bc_callback_candidate_vector_full_variable_values) << "\",\n";
    out << "  \"tailored_bc_callback_candidate_vector_failure_reason\": \""
        << jsonEscape(result.tailored_bc_callback_candidate_vector_failure_reason) << "\",\n";
    out << "  \"tailored_bc_lazy_rejections_total\": "
        << result.tailored_bc_lazy_rejections_total << ",\n";
    out << "  \"tailored_bc_lazy_rejections_by_reason\": \""
        << jsonEscape(result.tailored_bc_lazy_rejections_by_reason) << "\",\n";
    out << "  \"tailored_bc_incumbents_seen\": "
        << result.tailored_bc_incumbents_seen << ",\n";
    out << "  \"tailored_bc_incumbents_verified\": "
        << result.tailored_bc_incumbents_verified << ",\n";
    out << "  \"tailored_bc_incumbents_rejected\": "
        << result.tailored_bc_incumbents_rejected << ",\n";
    out << "  \"tailored_bc_candidate_projection_checks\": "
        << result.tailored_bc_candidate_projection_checks << ",\n";
    out << "  \"tailored_bc_candidate_projection_verified\": "
        << result.tailored_bc_candidate_projection_verified << ",\n";
    out << "  \"tailored_bc_candidate_projection_rejections\": "
        << result.tailored_bc_candidate_projection_rejections << ",\n";
    out << "  \"tailored_bc_candidate_projection_unsupported_mismatches\": "
        << result.tailored_bc_candidate_projection_unsupported_mismatches << ",\n";
    out << "  \"tailored_bc_candidate_projection_rejection_reasons\": \""
        << jsonEscape(result.tailored_bc_candidate_projection_rejection_reasons) << "\",\n";
    out << "  \"tailored_bc_candidate_projection_max_gini_underestimate\": "
        << result.tailored_bc_candidate_projection_max_gini_underestimate << ",\n";
    out << "  \"tailored_bc_candidate_projection_max_objective_underestimate\": "
        << result.tailored_bc_candidate_projection_max_objective_underestimate << ",\n";
    out << "  \"tailored_bc_candidate_route_projection_checks\": "
        << result.tailored_bc_candidate_route_projection_checks << ",\n";
    out << "  \"tailored_bc_candidate_route_projection_verified\": "
        << result.tailored_bc_candidate_route_projection_verified << ",\n";
    out << "  \"tailored_bc_candidate_route_projection_rejections\": "
        << result.tailored_bc_candidate_route_projection_rejections << ",\n";
    out << "  \"tailored_bc_candidate_route_projection_unsupported_mismatches\": "
        << result.tailored_bc_candidate_route_projection_unsupported_mismatches << ",\n";
    out << "  \"tailored_bc_candidate_route_projection_rejection_reasons\": \""
        << jsonEscape(result.tailored_bc_candidate_route_projection_rejection_reasons) << "\",\n";
    out << "  \"tailored_bc_branching_priorities_summary\": \""
        << jsonEscape(result.tailored_bc_branching_priorities_summary) << "\",\n";
    out << "  \"tailored_bc_gini_branches_created\": "
        << result.tailored_bc_gini_branches_created << ",\n";
    out << "  \"tailored_bc_gini_selector_variables\": "
        << result.tailored_bc_gini_selector_variables << ",\n";
    out << "  \"tailored_bc_callback_fail_reason\": \""
        << jsonEscape(result.tailored_bc_callback_fail_reason) << "\",\n";
    out << "  \"tailored_bc_source_class\": \""
        << jsonEscape(result.tailored_bc_source_class) << "\",\n";
    out << "  \"tailored_bc_gini_subset_envelope_candidates\": "
        << result.tailored_bc_gini_subset_envelope_candidates << ",\n";
    out << "  \"tailored_bc_gini_subset_envelope_violations\": "
        << result.tailored_bc_gini_subset_envelope_violations << ",\n";
    out << "  \"tailored_bc_gini_subset_envelope_cuts_added\": "
        << result.tailored_bc_gini_subset_envelope_cuts_added << ",\n";
    out << "  \"tailored_bc_max_gini_subset_violation\": "
        << result.tailored_bc_max_gini_subset_violation << ",\n";
    out << "  \"tailored_bc_callback_separation_pacing\": \""
        << jsonEscape(result.tailored_bc_callback_separation_pacing) << "\",\n";
    out << "  \"tailored_bc_callback_expensive_separation_calls\": "
        << result.tailored_bc_callback_expensive_separation_calls << ",\n";
    out << "  \"tailored_bc_callback_expensive_separation_skips\": "
        << result.tailored_bc_callback_expensive_separation_skips << ",\n";
    out << "  \"tailored_bc_callback_cut_profile\": \""
        << jsonEscape(result.tailored_bc_callback_cut_profile) << "\",\n";
    out << "  \"tailored_bc_low_gini_l1_centering_vars\": "
        << result.tailored_bc_low_gini_l1_centering_vars << ",\n";
    out << "  \"tailored_bc_low_gini_l1_centering_rows_added\": "
        << result.tailored_bc_low_gini_l1_centering_rows_added << ",\n";
    out << "  \"tailored_bc_low_gini_l1_centering_violations\": "
        << result.tailored_bc_low_gini_l1_centering_violations << ",\n";
    out << "  \"tailored_bc_local_centering_rows_added\": "
        << result.tailored_bc_local_centering_rows_added << ",\n";
    out << "  \"tailored_bc_local_centering_violations\": "
        << result.tailored_bc_local_centering_violations << ",\n";
    out << "  \"tailored_bc_local_centering_max_violation\": "
        << result.tailored_bc_local_centering_max_violation << ",\n";
    out << "  \"tailored_bc_subset_cross_h_centering_rows_added\": "
        << result.tailored_bc_subset_cross_h_centering_rows_added << ",\n";
    out << "  \"tailored_bc_subset_cross_h_centering_candidates\": "
        << result.tailored_bc_subset_cross_h_centering_candidates << ",\n";
    out << "  \"tailored_bc_subset_cross_h_centering_violations\": "
        << result.tailored_bc_subset_cross_h_centering_violations << ",\n";
    out << "  \"tailored_bc_subset_cross_h_centering_max_violation\": "
        << result.tailored_bc_subset_cross_h_centering_max_violation << ",\n";
    out << "  \"tailored_bc_subset_cross_h_separation_profile\": \""
        << jsonEscape(result.tailored_bc_subset_cross_h_separation_profile) << "\",\n";
    out << "  \"tailored_bc_local_q_centering_rows_added\": "
        << result.tailored_bc_local_q_centering_rows_added << ",\n";
    out << "  \"tailored_bc_local_q_centering_violations\": "
        << result.tailored_bc_local_q_centering_violations << ",\n";
    out << "  \"tailored_bc_local_q_centering_max_violation\": "
        << result.tailored_bc_local_q_centering_max_violation << ",\n";
    out << "  \"tailored_bc_variable_s_centering_cuts_added\": "
        << result.tailored_bc_variable_s_centering_cuts_added << ",\n";
    out << "  \"tailored_bc_variable_s_centering_violations\": "
        << result.tailored_bc_variable_s_centering_violations << ",\n";
    out << "  \"tailored_bc_subset_inventory_imbalance_cuts_added\": "
        << result.tailored_bc_subset_inventory_imbalance_cuts_added << ",\n";
    out << "  \"tailored_bc_subset_inventory_imbalance_candidates\": "
        << result.tailored_bc_subset_inventory_imbalance_candidates << ",\n";
    out << "  \"tailored_bc_subset_inventory_imbalance_violations\": "
        << result.tailored_bc_subset_inventory_imbalance_violations << ",\n";
    out << "  \"tailored_bc_bucket_ratio_domain_rows_added\": "
        << result.tailored_bc_bucket_ratio_domain_rows_added << ",\n";
    out << "  \"tailored_bc_bucket_ratio_domain_bounds_tightened\": "
        << result.tailored_bc_bucket_ratio_domain_bounds_tightened << ",\n";
    out << "  \"tailored_bc_bucket_ratio_domain_proof_status\": \""
        << jsonEscape(result.tailored_bc_bucket_ratio_domain_proof_status) << "\",\n";
    out << "  \"tailored_bc_bucket_subset_ratio_domain_cuts_added\": "
        << result.tailored_bc_bucket_subset_ratio_domain_cuts_added << ",\n";
    out << "  \"tailored_bc_bucket_subset_ratio_domain_candidates\": "
        << result.tailored_bc_bucket_subset_ratio_domain_candidates << ",\n";
    out << "  \"tailored_bc_bucket_subset_ratio_domain_violations\": "
        << result.tailored_bc_bucket_subset_ratio_domain_violations << ",\n";
    out << "  \"tailored_bc_bucket_subset_ratio_domain_max_violation\": "
        << result.tailored_bc_bucket_subset_ratio_domain_max_violation << ",\n";
    out << "  \"tailored_bc_bucket_subset_ratio_domain_max_size\": "
        << result.tailored_bc_bucket_subset_ratio_domain_max_size << ",\n";
    out << "  \"tailored_bc_bucket_h_cap_rows_added\": "
        << result.tailored_bc_bucket_h_cap_rows_added << ",\n";
    out << "  \"bucket_integer_inventory_bounds_tightened\": "
        << result.bucket_integer_inventory_bounds_tightened << ",\n";
    out << "  \"bucket_integer_inventory_rows_added\": "
        << result.bucket_integer_inventory_rows_added << ",\n";
    out << "  \"bucket_integer_inventory_lower_bounds_tightened\": "
        << result.bucket_integer_inventory_lower_bounds_tightened << ",\n";
    out << "  \"bucket_integer_inventory_upper_bounds_tightened\": "
        << result.bucket_integer_inventory_upper_bounds_tightened << ",\n";
    out << "  \"bucket_integer_inventory_domain_mode\": \""
        << jsonEscape(result.bucket_integer_inventory_domain_mode) << "\",\n";
    out << "  \"bucket_integer_inventory_domain_proof_status\": \""
        << jsonEscape(result.bucket_integer_inventory_domain_proof_status) << "\",\n";
    out << "  \"bucket_required_movement_rows_added\": "
        << result.bucket_required_movement_rows_added << ",\n";
    out << "  \"bucket_required_visit_rows_added\": "
        << result.bucket_required_visit_rows_added << ",\n";
    out << "  \"bucket_subset_required_movement_rows_added\": "
        << result.bucket_subset_required_movement_rows_added << ",\n";
    out << "  \"bucket_required_movement_violations\": "
        << result.bucket_required_movement_violations << ",\n";
    out << "  \"bucket_required_movement_max_violation\": "
        << result.bucket_required_movement_max_violation << ",\n";
    out << "  \"bucket_required_movement_max_size\": "
        << result.bucket_required_movement_max_size << ",\n";
    out << "  \"bucket_required_movement_proof_status\": \""
        << jsonEscape(result.bucket_required_movement_proof_status) << "\",\n";
    out << "  \"tailored_bc_transfer_cutset_cuts_added\": "
        << result.tailored_bc_transfer_cutset_cuts_added << ",\n";
    out << "  \"tailored_bc_transfer_cutset_candidates\": "
        << result.tailored_bc_transfer_cutset_candidates << ",\n";
    out << "  \"tailored_bc_transfer_cutset_violations\": "
        << result.tailored_bc_transfer_cutset_violations << ",\n";
    out << "  \"tailored_bc_compatible_source_transfer_cuts_added\": "
        << result.tailored_bc_compatible_source_transfer_cuts_added << ",\n";
    out << "  \"tailored_bc_compatible_source_transfer_candidates\": "
        << result.tailored_bc_compatible_source_transfer_candidates << ",\n";
    out << "  \"tailored_bc_required_external_source_cuts_added\": "
        << result.tailored_bc_required_external_source_cuts_added << ",\n";
    out << "  \"tailored_bc_support_duration_pair_cuts_added\": "
        << result.tailored_bc_support_duration_pair_cuts_added << ",\n";
    out << "  \"tailored_bc_support_duration_pair_candidates\": "
        << result.tailored_bc_support_duration_pair_candidates << ",\n";
    out << "  \"tailored_bc_support_duration_pair_violations\": "
        << result.tailored_bc_support_duration_pair_violations << ",\n";
    out << "  \"tailored_bc_support_duration_triple_cuts_added\": "
        << result.tailored_bc_support_duration_triple_cuts_added << ",\n";
    out << "  \"tailored_bc_support_duration_triple_candidates\": "
        << result.tailored_bc_support_duration_triple_candidates << ",\n";
    out << "  \"tailored_bc_support_duration_triple_violations\": "
        << result.tailored_bc_support_duration_triple_violations << ",\n";
    out << "  \"tailored_bc_support_duration_quad_cuts_added\": "
        << result.tailored_bc_support_duration_quad_cuts_added << ",\n";
    out << "  \"tailored_bc_support_duration_quad_candidates\": "
        << result.tailored_bc_support_duration_quad_candidates << ",\n";
    out << "  \"tailored_bc_support_duration_quad_violations\": "
        << result.tailored_bc_support_duration_quad_violations << ",\n";
    out << "  \"tailored_bc_support_duration_lifted_cuts_added\": "
        << result.tailored_bc_support_duration_lifted_cuts_added << ",\n";
    out << "  \"tailored_bc_support_duration_lifted_candidates\": "
        << result.tailored_bc_support_duration_lifted_candidates << ",\n";
    out << "  \"tailored_bc_support_duration_lifted_violations\": "
        << result.tailored_bc_support_duration_lifted_violations << ",\n";
    out << "  \"tailored_bc_support_duration_cover_mode\": \""
        << jsonEscape(result.tailored_bc_support_duration_cover_mode) << "\",\n";
    out << "  \"tailored_bc_benders_inventory_cuts_mode\": \""
        << jsonEscape(result.tailored_bc_benders_inventory_cuts_mode) << "\",\n";
    out << "  \"tailored_bc_benders_inventory_cuts_added\": "
        << result.tailored_bc_benders_inventory_cuts_added << ",\n";
    out << "  \"tailored_bc_benders_inventory_candidates\": "
        << result.tailored_bc_benders_inventory_candidates << ",\n";
    out << "  \"tailored_bc_gs_product_coupling_enabled\": "
        << (result.tailored_bc_gs_product_coupling_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_gs_product_coupling_mode\": \""
        << jsonEscape(result.tailored_bc_gs_product_coupling_mode) << "\",\n";
    out << "  \"tailored_bc_gs_product_lower_row\": \""
        << jsonEscape(result.tailored_bc_gs_product_lower_row) << "\",\n";
    out << "  \"gs_product_variable_added\": "
        << result.gs_product_variable_added << ",\n";
    out << "  \"gs_mccormick_rows_added\": "
        << result.gs_mccormick_rows_added << ",\n";
    out << "  \"gs_h_upper_rows_added\": "
        << result.gs_h_upper_rows_added << ",\n";
    out << "  \"gs_h_lower_rows_added\": "
        << result.gs_h_lower_rows_added << ",\n";
    out << "  \"gs_product_coupling_violations\": "
        << result.gs_product_coupling_violations << ",\n";
    out << "  \"gs_product_coupling_max_violation\": "
        << result.gs_product_coupling_max_violation << ",\n";
    out << "  \"gs_product_callback_rows_added\": "
        << result.gs_product_callback_rows_added << ",\n";
    out << "  \"gs_product_coupling_proof_status\": \""
        << jsonEscape(result.gs_product_coupling_proof_status) << "\",\n";
    out << "  \"tailored_bc_disaggregated_sp_estimator_enabled\": "
        << (result.tailored_bc_disaggregated_sp_estimator_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_disaggregated_sp_mode\": \""
        << jsonEscape(result.tailored_bc_disaggregated_sp_mode) << "\",\n";
    out << "  \"tailored_bc_disaggregated_sp_replace_aggregate\": "
        << (result.tailored_bc_disaggregated_sp_replace_aggregate ? "true" : "false") << ",\n";
    out << "  \"disagg_sp_variables_added\": "
        << result.disagg_sp_variables_added << ",\n";
    out << "  \"disagg_sp_mccormick_rows_added\": "
        << result.disagg_sp_mccormick_rows_added << ",\n";
    out << "  \"disagg_sp_estimator_rows_added\": "
        << result.disagg_sp_estimator_rows_added << ",\n";
    out << "  \"disagg_sp_violations\": "
        << result.disagg_sp_violations << ",\n";
    out << "  \"disagg_sp_max_violation\": "
        << result.disagg_sp_max_violation << ",\n";
    out << "  \"disagg_sp_callback_rows_added\": "
        << result.disagg_sp_callback_rows_added << ",\n";
    out << "  \"disagg_sp_root_gap_reduction\": "
        << result.disagg_sp_root_gap_reduction << ",\n";
    out << "  \"disagg_sp_proof_status\": \""
        << jsonEscape(result.disagg_sp_proof_status) << "\",\n";
    out << "  \"tailored_bc_vector_support_cover_enabled\": "
        << (result.tailored_bc_vector_support_cover_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_vector_support_cover_max_size\": "
        << result.tailored_bc_vector_support_cover_max_size << ",\n";
    out << "  \"tailored_bc_vector_support_cover_max_cuts\": "
        << result.tailored_bc_vector_support_cover_max_cuts << ",\n";
    out << "  \"tailored_bc_vector_route_cutset_enabled\": "
        << (result.tailored_bc_vector_route_cutset_enabled ? "true" : "false") << ",\n";
    out << "  \"tailored_bc_vector_route_cutset_max_size\": "
        << result.tailored_bc_vector_route_cutset_max_size << ",\n";
    out << "  \"tailored_bc_vector_route_cutset_max_cuts\": "
        << result.tailored_bc_vector_route_cutset_max_cuts << ",\n";
    out << "  \"tailored_bc_vector_cut_min_violation\": "
        << result.tailored_bc_vector_cut_min_violation << ",\n";
    out << "  \"tailored_bc_vector_cut_candidate_source\": \""
        << jsonEscape(result.tailored_bc_vector_cut_candidate_source) << "\",\n";
    out << "  \"vector_support_cover_candidates\": "
        << result.vector_support_cover_candidates << ",\n";
    out << "  \"vector_support_cover_cuts_added\": "
        << result.vector_support_cover_cuts_added << ",\n";
    out << "  \"vector_support_cover_max_violation\": "
        << result.vector_support_cover_max_violation << ",\n";
    out << "  \"vector_route_cutset_candidates\": "
        << result.vector_route_cutset_candidates << ",\n";
    out << "  \"vector_route_cutset_cuts_added\": "
        << result.vector_route_cutset_cuts_added << ",\n";
    out << "  \"vector_route_cutset_max_violation\": "
        << result.vector_route_cutset_max_violation << ",\n";
    out << "  \"vector_callback_support_cover_candidates\": "
        << result.vector_callback_support_cover_candidates << ",\n";
    out << "  \"vector_callback_support_cover_cuts_added\": "
        << result.vector_callback_support_cover_cuts_added << ",\n";
    out << "  \"vector_callback_route_cutset_candidates\": "
        << result.vector_callback_route_cutset_candidates << ",\n";
    out << "  \"vector_callback_route_cutset_cuts_added\": "
        << result.vector_callback_route_cutset_cuts_added << ",\n";
    out << "  \"vector_callback_support_cover_max_violation\": "
        << result.vector_callback_support_cover_max_violation << ",\n";
    out << "  \"vector_callback_route_cutset_max_violation\": "
        << result.vector_callback_route_cutset_max_violation << ",\n";
    out << "  \"vector_callback_route_cutset_violations\": "
        << result.vector_callback_route_cutset_violations << ",\n";
    out << "  \"vector_callback_route_cutset_violation_sum\": "
        << result.vector_callback_route_cutset_violation_sum << ",\n";
    out << "  \"vector_callback_route_cutset_average_violation\": "
        << result.vector_callback_route_cutset_average_violation << ",\n";
    out << "  \"vector_callback_route_cutset_cuts_size_2\": "
        << result.vector_callback_route_cutset_cuts_size_2 << ",\n";
    out << "  \"vector_callback_route_cutset_cuts_size_3\": "
        << result.vector_callback_route_cutset_cuts_size_3 << ",\n";
    out << "  \"vector_callback_route_cutset_cuts_size_4\": "
        << result.vector_callback_route_cutset_cuts_size_4 << ",\n";
    out << "  \"vector_callback_route_cutset_cuts_size_5\": "
        << result.vector_callback_route_cutset_cuts_size_5 << ",\n";
    out << "  \"tailored_bc_structural_profile\": \""
        << jsonEscape(result.tailored_bc_structural_profile) << "\",\n";
    out << "  \"vector_route_cuts_proof_status\": \""
        << jsonEscape(result.vector_route_cuts_proof_status) << "\",\n";
    out << "  \"gini_spread_cuts_added\": "
        << result.gini_spread_cuts_added << ",\n";
    out << "  \"compact_bc_direct_gini_cap_rows_added\": "
        << result.compact_bc_direct_gini_cap_rows_added << ",\n";
    out << "  \"compact_bc_direct_gini_floor_rows_added\": "
        << result.compact_bc_direct_gini_floor_rows_added << ",\n";
    out << "  \"compact_bc_tight_mccormick_rows_added\": "
        << result.compact_bc_tight_mccormick_rows_added << ",\n";
    out << "  \"compact_bc_inventory_conservation_rows_added\": "
        << result.compact_bc_inventory_conservation_rows_added << ",\n";
    out << "  \"compact_bc_movement_reachability_domains_tightened\": "
        << result.compact_bc_movement_reachability_domains_tightened << ",\n";
    out << "  \"compact_bc_visit_inventory_linking_rows_added\": "
        << result.compact_bc_visit_inventory_linking_rows_added << ",\n";
    out << "  \"compact_bc_objective_estimator_cutoff_rows_added\": "
        << result.compact_bc_objective_estimator_cutoff_rows_added << ",\n";
    out << "  \"compact_bc_penalty_lb\": "
        << result.compact_bc_penalty_lb << ",\n";
    out << "  \"compact_bc_penalty_lb_rows_added\": "
        << result.compact_bc_penalty_lb_rows_added << ",\n";
    out << "  \"compact_bc_low_gini_centering_rows_added\": "
        << result.compact_bc_low_gini_centering_rows_added << ",\n";
    out << "  \"compact_bc_support_duration_pair_cuts_added\": "
        << result.compact_bc_support_duration_pair_cuts_added << ",\n";
    out << "  \"compact_bc_support_duration_triple_cuts_added\": "
        << result.compact_bc_support_duration_triple_cuts_added << ",\n";
    out << "  \"compact_bc_pairwise_transfer_compatibility_cuts_added\": "
        << result.compact_bc_pairwise_transfer_compatibility_cuts_added << ",\n";
    out << "  \"compact_bc_receiver_source_cover_cuts_added\": "
        << result.compact_bc_receiver_source_cover_cuts_added << ",\n";
    out << "  \"compact_bc_receiver_source_cover_mode\": \""
        << jsonEscape(result.compact_bc_receiver_source_cover_mode) << "\",\n";
    out << "  \"compact_bc_total_cuts_added_by_family\": \""
        << jsonEscape(result.compact_bc_total_cuts_added_by_family) << "\",\n";
    out << "  \"compact_bc_total_domains_tightened_by_family\": \""
        << jsonEscape(result.compact_bc_total_domains_tightened_by_family) << "\",\n";
    out << "  \"compact_bc_total_leaf_nodes\": "
        << result.compact_bc_total_leaf_nodes << ",\n";
    out << "  \"ablation_variant_semantics\": \""
        << jsonEscape(result.ablation_variant_semantics) << "\",\n";
    out << "  \"required_movement_lb\": "
        << result.required_movement_lb << ",\n";
    out << "  \"required_movement_cuts_added\": "
        << result.required_movement_cuts_added << ",\n";
    out << "  \"global_handling_capacity_lb\": "
        << result.global_handling_capacity_lb << ",\n";
    out << "  \"global_handling_capacity_cuts_added\": "
        << result.global_handling_capacity_cuts_added << ",\n";
    out << "  \"low_gini_ratio_band_domains_tightened\": "
        << result.low_gini_ratio_band_domains_tightened << ",\n";
    out << "  \"oracle_strengthening_families_enabled\": \""
        << jsonEscape(result.oracle_strengthening_families_enabled) << "\",\n";
    out << "  \"oracle_strengthening_lb_improvement\": "
        << result.oracle_strengthening_lb_improvement << ",\n";
    out << "  \"oracle_bound_merged_leaves\": "
        << result.oracle_bound_merged_leaves << ",\n";
    out << "  \"oracle_bound_closed_leaves\": "
        << result.oracle_bound_closed_leaves << ",\n";
    out << "  \"oracle_bound_best_global_lb\": "
        << result.oracle_bound_best_global_lb << ",\n";
    out << "  \"oracle_bound_merge_audit_csv_path\": \""
        << jsonEscape(result.oracle_bound_merge_audit_csv_path) << "\",\n";
    out << "  \"interval_closure_mode\": \""
        << jsonEscape(result.interval_closure_mode) << "\",\n";
    out << "  \"interval_closure_variant_mode\": \""
        << jsonEscape(result.interval_closure_variant_mode) << "\",\n";
    out << "  \"interval_closure_target_ids\": \""
        << jsonEscape(result.interval_closure_target_ids) << "\",\n";
    out << "  \"interval_closure_range\": \""
        << jsonEscape(result.interval_closure_range) << "\",\n";
    out << "  \"focused_interval_result\": "
        << (result.focused_interval_result ? "true" : "false") << ",\n";
    out << "  \"focused_interval_safe_to_merge\": "
        << (result.focused_interval_safe_to_merge ? "true" : "false") << ",\n";
    out << "  \"focused_interval_merge_reason\": \""
        << jsonEscape(result.focused_interval_merge_reason) << "\",\n";
    out << "  \"sealed_run\": " << (result.sealed_run ? "true" : "false") << ",\n";
    out << "  \"sealed_run_id\": \"" << jsonEscape(result.sealed_run_id) << "\",\n";
    out << "  \"sealed_run_start_time\": \""
        << jsonEscape(result.sealed_run_start_time) << "\",\n";
    out << "  \"incumbent_provenance\": \""
        << jsonEscape(result.incumbent_provenance) << "\",\n";
    out << "  \"same_run_generated_incumbent\": "
        << (result.same_run_generated_incumbent ? "true" : "false") << ",\n";
    out << "  \"no_archive_scanning\": "
        << (result.no_archive_scanning ? "true" : "false") << ",\n";
    out << "  \"no_external_known_ub\": "
        << (result.no_external_known_ub ? "true" : "false") << ",\n";
    out << "  \"no_focus_only_certificate\": "
        << (result.no_focus_only_certificate ? "true" : "false") << ",\n";
    out << "  \"sealed_run_forbidden_source_used\": "
        << (result.sealed_run_forbidden_source_used ? "true" : "false") << ",\n";
    out << "  \"sealed_run_rejection_reason\": \""
        << jsonEscape(result.sealed_run_rejection_reason) << "\",\n";
    out << "  \"auto_interval_oracle_called\": "
        << (result.auto_interval_oracle_called ? "true" : "false") << ",\n";
    out << "  \"auto_interval_oracle_total_final_leaves\": "
        << result.auto_interval_oracle_total_final_leaves << ",\n";
    out << "  \"auto_interval_oracle_leaves_attempted\": "
        << result.auto_interval_oracle_leaves_attempted << ",\n";
    out << "  \"auto_interval_oracle_leaves_closed\": "
        << result.auto_interval_oracle_leaves_closed << ",\n";
    out << "  \"auto_interval_oracle_leaves_timed_out\": "
        << result.auto_interval_oracle_leaves_timed_out << ",\n";
    out << "  \"auto_interval_oracle_leaves_split\": "
        << result.auto_interval_oracle_leaves_split << ",\n";
    out << "  \"auto_interval_oracle_time_seconds\": "
        << result.auto_interval_oracle_time_seconds << ",\n";
    out << "  \"auto_interval_oracle_remaining_open_leaves\": "
        << result.auto_interval_oracle_remaining_open_leaves << ",\n";
    out << "  \"auto_interval_oracle_status_by_leaf\": \""
        << jsonEscape(result.auto_interval_oracle_status_by_leaf) << "\",\n";
    out << "  \"auto_interval_oracle_coverage_complete\": "
        << (result.auto_interval_oracle_coverage_complete ? "true" : "false") << ",\n";
    out << "  \"auto_interval_oracle_requested_leaf_time_limit\": "
        << result.auto_interval_oracle_requested_leaf_time_limit << ",\n";
    out << "  \"auto_interval_oracle_actual_leaf_time_limit\": "
        << result.auto_interval_oracle_actual_leaf_time_limit << ",\n";
    out << "  \"auto_interval_oracle_total_budget\": "
        << result.auto_interval_oracle_total_budget << ",\n";
    out << "  \"auto_interval_oracle_budget_policy\": \""
        << jsonEscape(result.auto_interval_oracle_budget_policy) << "\",\n";
    out << "  \"auto_interval_oracle_budget_policy_requested\": \""
        << jsonEscape(result.auto_interval_oracle_budget_policy_requested) << "\",\n";
    out << "  \"auto_interval_oracle_budget_policy_parsed\": \""
        << jsonEscape(result.auto_interval_oracle_budget_policy_parsed) << "\",\n";
    out << "  \"auto_interval_oracle_budget_policy_effective\": \""
        << jsonEscape(result.auto_interval_oracle_budget_policy_effective) << "\",\n";
    out << "  \"auto_interval_oracle_budget_policy_serialized\": \""
        << jsonEscape(result.auto_interval_oracle_budget_policy_serialized) << "\",\n";
    out << "  \"auto_interval_oracle_budget_policy_roundtrip_consistent\": "
        << (result.auto_interval_oracle_budget_policy_roundtrip_consistent
                ? "true" : "false") << ",\n";
    out << "  \"auto_interval_oracle_budget_exhausted\": "
        << (result.auto_interval_oracle_budget_exhausted ? "true" : "false") << ",\n";
    out << "  \"per_leaf_oracle_time_limit_used\": \""
        << jsonEscape(result.per_leaf_oracle_time_limit_used) << "\",\n";
    out << "  \"auto_interval_oracle_recursive_depth_reached\": "
        << result.auto_interval_oracle_recursive_depth_reached << ",\n";
    out << "  \"auto_interval_oracle_children_attempted\": "
        << result.auto_interval_oracle_children_attempted << ",\n";
    out << "  \"auto_interval_oracle_max_children_total\": "
        << result.auto_interval_oracle_max_children_total << ",\n";
    out << "  \"auto_interval_oracle_partition_tree_csv_path\": \""
        << jsonEscape(result.auto_interval_oracle_partition_tree_csv_path) << "\",\n";
    out << "  \"scheduler_mode\": \""
        << jsonEscape(result.scheduler_mode) << "\",\n";
    out << "  \"controlling_leaf_checkpoint_merge_enabled\": "
        << (result.controlling_leaf_checkpoint_merge_enabled ? "true" : "false")
        << ",\n";
    out << "  \"scheduler_decision_trace_path\": \""
        << jsonEscape(result.scheduler_decision_trace_path) << "\",\n";
    out << "  \"scheduler_leaf_allocation_path\": \""
        << jsonEscape(result.scheduler_leaf_allocation_path) << "\",\n";
    out << "  \"scheduler_global_bound_trajectory_path\": \""
        << jsonEscape(result.scheduler_global_bound_trajectory_path) << "\",\n";
    out << "  \"scheduler_invariants_passed\": "
        << (result.scheduler_invariants_passed ? "true" : "false") << ",\n";
    out << "  \"scheduler_invariant_failure\": \""
        << jsonEscape(result.scheduler_invariant_failure) << "\",\n";
    out << "  \"nominal_process_wall_budget_seconds\": "
        << result.nominal_process_wall_budget_seconds << ",\n";
    out << "  \"finalization_reserve_seconds\": "
        << result.finalization_reserve_seconds << ",\n";
    out << "  \"process_elapsed_before_auto_oracle_seconds\": "
        << result.process_elapsed_before_auto_oracle_seconds << ",\n";
    out << "  \"process_remaining_before_auto_oracle_seconds\": "
        << result.process_remaining_before_auto_oracle_seconds << ",\n";
    out << "  \"final_process_wall_time_seconds\": "
        << result.final_process_wall_time_seconds << ",\n";
    out << "  \"process_wall_time_overrun_seconds\": "
        << result.process_wall_time_overrun_seconds << ",\n";
    out << "  \"process_wall_time_comparable\": "
        << (result.process_wall_time_comparable ? "true" : "false") << ",\n";
    out << "  \"native_leaf_time_limit_param_id\": "
        << result.native_leaf_time_limit_param_id << ",\n";
    out << "  \"native_leaf_time_limit_set_rc\": "
        << result.native_leaf_time_limit_set_rc << ",\n";
    out << "  \"full_ledger_merge_status\": \""
        << jsonEscape(result.full_ledger_merge_status) << "\",\n";
    out << "  \"full_ledger_merge_audit_passed\": "
        << (result.full_ledger_merge_audit_passed ? "true" : "false") << ",\n";
    out << "  \"bpc_fallback_auto_called\": "
        << (result.bpc_fallback_auto_called ? "true" : "false") << ",\n";
    out << "  \"bpc_fallback_leaves_attempted\": "
        << result.bpc_fallback_leaves_attempted << ",\n";
    out << "  \"bpc_fallback_leaves_closed\": "
        << result.bpc_fallback_leaves_closed << ",\n";
    out << "  \"exact_pricing_closed_leaves\": "
        << result.exact_pricing_closed_leaves << ",\n";
    out << "  \"bpc_fallback_pricing_time\": "
        << result.bpc_fallback_pricing_time << ",\n";
    out << "  \"bpc_fallback_nodes\": " << result.bpc_fallback_nodes << ",\n";
    out << "  \"bpc_fallback_best_reduced_cost\": "
        << result.bpc_fallback_best_reduced_cost << ",\n";
    out << "  \"bpc_fallback_final_interval_lb\": "
        << result.bpc_fallback_final_interval_lb << ",\n";
    out << "  \"bpc_interval_certificate_basis\": \""
        << jsonEscape(result.bpc_interval_certificate_basis) << "\",\n";
    out << "  \"vehicle_transfer_flow_variables\": "
        << result.vehicle_transfer_flow_variables << ",\n";
    out << "  \"vehicle_transfer_depot_unload_variables\": "
        << result.vehicle_transfer_depot_unload_variables << ",\n";
    out << "  \"vehicle_transfer_flow_balance_constraints\": "
        << result.vehicle_transfer_flow_balance_constraints << ",\n";
    out << "  \"vehicle_transfer_mask_linking_constraints\": "
        << result.vehicle_transfer_mask_linking_constraints << ",\n";
    out << "  \"vehicle_transfer_pairs_total\": "
        << result.vehicle_transfer_pairs_total << ",\n";
    out << "  \"vehicle_transfer_pairs_zero_cap\": "
        << result.vehicle_transfer_pairs_zero_cap << ",\n";
    out << "  \"vehicle_transfer_pairs_capacity_limited\": "
        << result.vehicle_transfer_pairs_capacity_limited << ",\n";
    out << "  \"vehicle_transfer_cap_min\": "
        << result.vehicle_transfer_cap_min << ",\n";
    out << "  \"vehicle_transfer_cap_avg\": "
        << result.vehicle_transfer_cap_avg << ",\n";
    out << "  \"vehicle_transfer_cap_max\": "
        << result.vehicle_transfer_cap_max << ",\n";
    out << "  \"vehicle_transfer_flow_time_seconds\": "
        << result.vehicle_transfer_flow_time_seconds << ",\n";
    out << "  \"progress_log\": \""
        << jsonEscape(result.progress_log_path) << "\",\n";
    out << "  \"progress_checkpoints_written\": "
        << result.progress_checkpoints_written << ",\n";
    out << "  \"gap_trajectory_available\": "
        << (result.gap_trajectory_available ? "true" : "false") << ",\n";
    out << "  \"compact_bc_progress_interval_seconds\": "
        << result.compact_bc_progress_interval_seconds << ",\n";
    out << "  \"ub_event_log_path\": \""
        << jsonEscape(result.ub_event_log_path) << "\",\n";
    out << "  \"initial_heuristic_UB\": " << result.initial_heuristic_UB << ",\n";
    out << "  \"final_UB\": " << result.final_UB << ",\n";
    out << "  \"ub_improved_after_initial_heuristic\": "
        << (result.ub_improved_after_initial_heuristic ? "true" : "false") << ",\n";
    out << "  \"ub_update_count_after_initial\": "
        << result.ub_update_count_after_initial << ",\n";
    out << "  \"first_ub_improvement_time\": "
        << result.first_ub_improvement_time << ",\n";
    out << "  \"last_ub_improvement_time\": "
        << result.last_ub_improvement_time << ",\n";
    out << "  \"best_ub_source_after_initial\": \""
        << jsonEscape(result.best_ub_source_after_initial) << "\",\n";
    out << "  \"exact_phase_primal_modules_called\": \""
        << jsonEscape(result.exact_phase_primal_modules_called) << "\",\n";
    out << "  \"route_pool_incumbent_calls\": "
        << result.route_pool_incumbent_calls << ",\n";
    out << "  \"route_pool_incumbent_successes\": "
        << result.route_pool_incumbent_successes << ",\n";
    out << "  \"relaxation_guided_rounding_calls\": "
        << result.relaxation_guided_rounding_calls << ",\n";
    out << "  \"relaxation_guided_rounding_successes\": "
        << result.relaxation_guided_rounding_successes << ",\n";
    out << "  \"bpc_column_pool_repair_calls\": "
        << result.bpc_column_pool_repair_calls << ",\n";
    out << "  \"bpc_column_pool_repair_successes\": "
        << result.bpc_column_pool_repair_successes << ",\n";
    out << "  \"local_redecode_repair_calls\": "
        << result.local_redecode_repair_calls << ",\n";
    out << "  \"local_redecode_repair_successes\": "
        << result.local_redecode_repair_successes << ",\n";
    out << "  \"bpc_trace_json\": \""
        << jsonEscape(result.bpc_trace_json_path) << "\",\n";
    out << "  \"bpc_interval_trace_csv\": \""
        << jsonEscape(result.bpc_interval_trace_csv_path) << "\",\n";
    out << "  \"last_lb_improvement_time_seconds\": "
        << result.last_lb_improvement_time_seconds << ",\n";
    out << "  \"last_ub_improvement_time_seconds\": "
        << result.last_ub_improvement_time_seconds << ",\n";
    out << "  \"best_gap_seen\": " << result.best_gap_seen << ",\n";
    out << "  \"best_gap_time_seconds\": "
        << result.best_gap_time_seconds << ",\n";
    out << "  \"focus_interval_id\": " << result.focus_interval_id << ",\n";
    out << "  \"focus_interval_range\": \""
        << jsonEscape(result.focus_interval_range) << "\",\n";
    out << "  \"focus_interval_lb_before\": "
        << result.focus_interval_lb_before << ",\n";
    out << "  \"focus_interval_lb_after\": "
        << result.focus_interval_lb_after << ",\n";
    out << "  \"focus_interval_closed\": "
        << (result.focus_interval_closed ? "true" : "false") << ",\n";
    out << "  \"focus_interval_bound_fathomed\": "
        << (result.focus_interval_bound_fathomed ? "true" : "false") << ",\n";
    out << "  \"focus_interval_parent_id\": "
        << result.focus_interval_parent_id << ",\n";
    out << "  \"focus_interval_open_nodes_before\": "
        << result.focus_interval_open_nodes_before << ",\n";
    out << "  \"focus_interval_open_nodes_after\": "
        << result.focus_interval_open_nodes_after << ",\n";
    out << "  \"focus_interval_open_nodes\": "
        << result.focus_interval_open_nodes << ",\n";
    out << "  \"focus_interval_pricing_closed\": "
        << (result.focus_interval_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"focus_interval_runtime\": "
        << result.focus_interval_runtime << ",\n";
    out << "  \"focus_interval_certificate_scope\": \""
        << jsonEscape(result.focus_interval_certificate_scope) << "\",\n";
    out << "  \"imported_interval_bounds_attempted\": "
        << result.imported_interval_bounds_attempted << ",\n";
    out << "  \"imported_interval_bounds_accepted\": "
        << result.imported_interval_bounds_accepted << ",\n";
    out << "  \"imported_interval_bounds_rejected\": "
        << result.imported_interval_bounds_rejected << ",\n";
    out << "  \"imported_interval_bounds_closed_intervals\": "
        << result.imported_interval_bounds_closed_intervals << ",\n";
    out << "  \"imported_interval_bounds_rejection_reasons\": \""
        << jsonEscape(result.imported_interval_bounds_rejection_reasons) << "\",\n";
    out << "  \"resumed_from_state\": "
        << (result.resumed_from_state ? "true" : "false") << ",\n";
    out << "  \"resume_state_compatible\": "
        << (result.resume_state_compatible ? "true" : "false") << ",\n";
    out << "  \"resume_state_columns_loaded\": "
        << result.resume_state_columns_loaded << ",\n";
    out << "  \"resume_state_nodes_loaded\": "
        << result.resume_state_nodes_loaded << ",\n";
    out << "  \"resume_state_interval_lb\": "
        << result.resume_state_interval_lb << ",\n";
    out << "  \"resume_state_rejection_reason\": \""
        << jsonEscape(result.resume_state_rejection_reason) << "\",\n";
    out << "  \"frontier_state_exported\": "
        << (result.frontier_state_exported ? "true" : "false") << ",\n";
    out << "  \"frontier_state_export_path\": \""
        << jsonEscape(result.frontier_state_export_path) << "\",\n";
    out << "  \"closure_mode\": \"" << jsonEscape(result.closure_mode) << "\",\n";
    out << "  \"closure_cg_iterations\": "
        << result.closure_cg_iterations << ",\n";
    out << "  \"closure_columns_added\": "
        << result.closure_columns_added << ",\n";
    out << "  \"closure_pricing_calls\": "
        << result.closure_pricing_calls << ",\n";
    out << "  \"closure_final_exact_pricing_run\": "
        << (result.closure_final_exact_pricing_run ? "true" : "false") << ",\n";
    out << "  \"closure_final_best_reduced_cost\": "
        << finiteOrZero(result.closure_final_best_reduced_cost) << ",\n";
    out << "  \"closure_pricing_closed\": "
        << (result.closure_pricing_closed ? "true" : "false") << ",\n";
    out << "  \"closure_time_seconds\": "
        << result.closure_time_seconds << ",\n";
    out << "  \"closure_stop_reason\": \""
        << jsonEscape(result.closure_stop_reason) << "\",\n";
    out << "  \"cg_stabilization_mode\": \""
        << jsonEscape(result.cg_stabilization_mode) << "\",\n";
    out << "  \"cg_stabilized_pricing_calls\": "
        << result.cg_stabilized_pricing_calls << ",\n";
    out << "  \"cg_true_pricing_calls\": "
        << result.cg_true_pricing_calls << ",\n";
    out << "  \"cg_stabilization_columns_found\": "
        << result.cg_stabilization_columns_found << ",\n";
    out << "  \"cg_true_pricing_columns_found\": "
        << result.cg_true_pricing_columns_found << ",\n";
    out << "  \"cg_dual_center_updates\": "
        << result.cg_dual_center_updates << ",\n";
    out << "  \"cg_dual_oscillation_metric\": "
        << result.cg_dual_oscillation_metric << ",\n";
    out << "  \"cg_true_negative_columns_inserted\": "
        << result.cg_true_negative_columns_inserted << ",\n";
    out << "  \"cg_stabilization_false_negatives\": "
        << result.cg_stabilization_false_negatives << ",\n";
    out << "  \"cg_stabilization_time_seconds\": "
        << result.cg_stabilization_time_seconds << ",\n";
    out << "  \"cg_final_true_pricing_rc\": "
        << finiteOrZero(result.cg_final_true_pricing_rc) << ",\n";
    out << "  \"external_incumbent_used_in_large_run\": "
        << (result.external_incumbent_used_in_large_run ? "true" : "false") << ",\n";
    out << "  \"external_incumbent_used\": "
        << (result.external_incumbent_used ? "true" : "false") << ",\n";
    out << "  \"external_incumbent_effect_on_UB\": "
        << result.external_incumbent_effect_on_UB << ",\n";
    out << "  \"external_incumbent_improved_UB\": "
        << (result.external_incumbent_improved_UB ? "true" : "false") << ",\n";
    out << "  \"external_incumbent_effect_on_frontier_range\": "
        << result.external_incumbent_effect_on_frontier_range << ",\n";
    out << "  \"v12_m1_imported_focus_bounds\": "
        << (result.v12_m1_imported_focus_bounds ? "true" : "false") << ",\n";
    out << "  \"v12_m1_focus_bounds_accepted\": "
        << result.v12_m1_focus_bounds_accepted << ",\n";
    out << "  \"v12_m1_full_lb_before_import\": "
        << result.v12_m1_full_lb_before_import << ",\n";
    out << "  \"v12_m1_full_lb_after_import\": "
        << result.v12_m1_full_lb_after_import << ",\n";
    out << "  \"interval_certificate_basis\": \""
        << jsonEscape(result.interval_certificate_basis) << "\",\n";
    out << "  \"interval_requires_pricing_closure\": \""
        << jsonEscape(result.interval_requires_pricing_closure) << "\",\n";
    out << "  \"interval_pricing_closure_available\": \""
        << jsonEscape(result.interval_pricing_closure_available) << "\",\n";
    out << "  \"interval_bound_valid\": \""
        << jsonEscape(result.interval_bound_valid) << "\",\n";
    out << "  \"interval_bound_source_list\": \""
        << jsonEscape(result.interval_bound_source_list) << "\",\n";
    out << "  \"full_certificate_basis\": \""
        << jsonEscape(result.full_certificate_basis) << "\",\n";
    out << "  \"full_certificate_requires_pricing_closure\": "
        << (result.full_certificate_requires_pricing_closure ? "true" : "false") << ",\n";
    out << "  \"full_certificate_pricing_closure_satisfied\": "
        << (result.full_certificate_pricing_closure_satisfied ? "true" : "false") << ",\n";
    out << "  \"full_certificate_all_intervals_accounted\": "
        << (result.full_certificate_all_intervals_accounted ? "true" : "false") << ",\n";
    out << "  \"full_certificate_rejection_reason\": \""
        << jsonEscape(result.full_certificate_rejection_reason) << "\",\n";
    out << "  \"iterative_closure_enabled\": "
        << (result.iterative_closure_enabled ? "true" : "false") << ",\n";
    out << "  \"iterative_closure_rounds\": "
        << result.iterative_closure_rounds << ",\n";
    out << "  \"iterative_closure_target_intervals\": \""
        << jsonEscape(result.iterative_closure_target_intervals) << "\",\n";
    out << "  \"iterative_closure_lb_before_each_round\": \""
        << jsonEscape(result.iterative_closure_lb_before_each_round) << "\",\n";
    out << "  \"iterative_closure_lb_after_each_round\": \""
        << jsonEscape(result.iterative_closure_lb_after_each_round) << "\",\n";
    out << "  \"iterative_closure_gap_before_each_round\": \""
        << jsonEscape(result.iterative_closure_gap_before_each_round) << "\",\n";
    out << "  \"iterative_closure_gap_after_each_round\": \""
        << jsonEscape(result.iterative_closure_gap_after_each_round) << "\",\n";
    out << "  \"iterative_closure_imports_accepted\": "
        << result.iterative_closure_imports_accepted << ",\n";
    out << "  \"iterative_closure_intervals_closed\": "
        << result.iterative_closure_intervals_closed << ",\n";
    out << "  \"iterative_closure_stop_reason\": \""
        << jsonEscape(result.iterative_closure_stop_reason) << "\",\n";
    out << "  \"iterative_exact_cg_rounds\": "
        << result.iterative_exact_cg_rounds << ",\n";
    out << "  \"iterative_pricing_verifier_calls\": "
        << result.iterative_pricing_verifier_calls << ",\n";
    out << "  \"iterative_pricing_verifier_completed\": "
        << result.iterative_pricing_verifier_completed << ",\n";
    out << "  \"iterative_nodes_closed_by_verifier\": "
        << result.iterative_nodes_closed_by_verifier << ",\n";
    out << "  \"iterative_intervals_fathomed_by_imported_bounds\": "
        << result.iterative_intervals_fathomed_by_imported_bounds << ",\n";
    out << "  \"open_node_state_exported\": "
        << (result.open_node_state_exported ? "true" : "false") << ",\n";
    out << "  \"open_node_state_nodes_saved\": "
        << result.open_node_state_nodes_saved << ",\n";
    out << "  \"open_node_state_columns_saved\": "
        << result.open_node_state_columns_saved << ",\n";
    out << "  \"open_node_state_imported\": "
        << (result.open_node_state_imported ? "true" : "false") << ",\n";
    out << "  \"open_node_state_nodes_loaded\": "
        << result.open_node_state_nodes_loaded << ",\n";
    out << "  \"open_node_state_resume_exact\": "
        << (result.open_node_state_resume_exact ? "true" : "false") << ",\n";
    out << "  \"open_node_state_resume_fallback_reason\": \""
        << jsonEscape(result.open_node_state_resume_fallback_reason) << "\",\n";
    out << "  \"pricing_verifier_enabled\": "
        << (result.pricing_verifier_enabled ? "true" : "false") << ",\n";
    out << "  \"pricing_verifier_complete\": "
        << (result.pricing_verifier_complete ? "true" : "false") << ",\n";
    out << "  \"pricing_verifier_best_reduced_cost\": "
        << finiteOrZero(result.pricing_verifier_best_reduced_cost) << ",\n";
    out << "  \"pricing_verifier_labels_processed\": "
        << result.pricing_verifier_labels_processed << ",\n";
    out << "  \"pricing_verifier_labels_pruned\": "
        << result.pricing_verifier_labels_pruned << ",\n";
    out << "  \"pricing_verifier_checkpoint_written\": "
        << (result.pricing_verifier_checkpoint_written ? "true" : "false") << ",\n";
    out << "  \"pricing_verifier_resumed\": "
        << (result.pricing_verifier_resumed ? "true" : "false") << ",\n";
    out << "  \"pricing_verifier_time_seconds\": "
        << result.pricing_verifier_time_seconds << ",\n";
    out << "  \"v12_m1_focus_intervals_attempted\": "
        << result.v12_m1_focus_intervals_attempted << ",\n";
    out << "  \"v12_m1_focus_intervals_closed\": "
        << result.v12_m1_focus_intervals_closed << ",\n";
    out << "  \"v12_m1_focus_bounds_imported\": "
        << result.v12_m1_focus_bounds_imported << ",\n";
    out << "  \"v12_m1_full_lb_after_all_imports\": "
        << result.v12_m1_full_lb_after_all_imports << ",\n";
    out << "  \"v12_m1_remaining_controlling_interval\": \""
        << jsonEscape(result.v12_m1_remaining_controlling_interval) << "\",\n";
    out << "  \"inventory_branch_candidates\": "
        << result.inventory_branch_candidates << ",\n";
    out << "  \"inventory_branch_nodes_created\": "
        << result.inventory_branch_nodes_created << ",\n";
    out << "  \"inventory_branch_station\": "
        << result.inventory_branch_station << ",\n";
    out << "  \"inventory_branch_value\": "
        << result.inventory_branch_value << ",\n";
    out << "  \"inventory_branch_left_bound\": "
        << result.inventory_branch_left_bound << ",\n";
    out << "  \"inventory_branch_right_bound\": "
        << result.inventory_branch_right_bound << ",\n";
    out << "  \"inventory_branch_pruned_nodes\": "
        << result.inventory_branch_pruned_nodes << ",\n";
    out << "  \"inventory_branch_max_depth\": "
        << result.inventory_branch_max_depth << ",\n";
    out << "  \"operation_mode_branch_candidates\": "
        << result.operation_mode_branch_candidates << ",\n";
    out << "  \"operation_mode_branch_nodes_created\": "
        << result.operation_mode_branch_nodes_created << ",\n";
    out << "  \"operation_mode_branch_station\": "
        << result.operation_mode_branch_station << ",\n";
    out << "  \"operation_mode_branch_type\": \""
        << jsonEscape(result.operation_mode_branch_type) << "\",\n";
    out << "  \"operation_mode_branch_pruned_columns\": "
        << result.operation_mode_branch_pruned_columns << ",\n";
    out << "  \"operation_mode_branch_pruned_labels\": "
        << result.operation_mode_branch_pruned_labels << ",\n";
    out << "  \"branch_selection_mode\": \""
        << jsonEscape(result.branch_selection_mode) << "\",\n";
    out << "  \"strong_branching_calls\": "
        << result.strong_branching_calls << ",\n";
    out << "  \"strong_branching_candidates_tested\": "
        << result.strong_branching_candidates_tested << ",\n";
    out << "  \"strong_branching_time_seconds\": "
        << result.strong_branching_time_seconds << ",\n";
    out << "  \"selected_branch_type\": \""
        << jsonEscape(result.selected_branch_type) << "\",\n";
    out << "  \"selected_branch_score\": "
        << result.selected_branch_score << ",\n";
    out << "  \"selected_branch_child_lb_left\": "
        << result.selected_branch_child_lb_left << ",\n";
    out << "  \"selected_branch_child_lb_right\": "
        << result.selected_branch_child_lb_right << ",\n";
    out << "  \"branch_nodes_by_type_ryan_foster\": "
        << result.branch_nodes_by_type_ryan_foster << ",\n";
    out << "  \"branch_nodes_by_type_inventory\": "
        << result.branch_nodes_by_type_inventory << ",\n";
    out << "  \"branch_nodes_by_type_operation_mode\": "
        << result.branch_nodes_by_type_operation_mode << ",\n";
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
