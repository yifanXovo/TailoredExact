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
        << "[--bpc-incumbent none|greedy|random|local|pool|pricing|portfolio|strong|compact|compact-cplex] [--bpc-incumbent-seconds <seconds>] [--bpc-incumbent-rounds <N>] "
        << "[--frontier-final-closure true|false] [--frontier-final-nodes <N>] "
        << "[--column-dominance true|false] [--column-dominance-mode exact|pareto|off] "
        << "[--projection-bound true|false] [--penalty-domain-tightening true|false] "
        << "[--movement-domain-tightening true|false] [--movement-bound-audit true|false] "
        << "[--frontier-best-bound-scheduling true|false] [--frontier-relaxation-cache true|false] "
        << "[--frontier-column-cache true|false] [--frontier-focused-min-lb-retry true|false] "
        << "[--support-duration-pruning true|false] [--support-duration-max-subset-size <N>] "
        << "[--route-mask-support-duration-pruning true|false] [--support-feasibility-oracle true|false] "
        << "[--route-pool-incumbent true|false] [--pickup-drop-compat-flow true|false] "
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
        else if (arg == "--route-pool-incumbent") opt.route_pool_incumbent = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pickup-drop-compat-flow") opt.pickup_drop_compat_flow = parseBoolValue(requireValue(i, argc, argv));
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
    if (opt.support_duration_max_subset_size < 0) opt.support_duration_max_subset_size = 0;
    if (opt.bpc_incumbent_seconds < 0.0) opt.bpc_incumbent_seconds = 0.0;
    if (opt.bpc_incumbent_rounds < 1) opt.bpc_incumbent_rounds = 1;
    if (opt.frontier_final_nodes < 1) opt.frontier_final_nodes = 1;
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
        << result.gini_max_possible << ","
        << result.relevant_gini_upper_for_improvement << ","
        << result.covered_gini_upper_bound << ","
        << (result.frontier_covers_all_improving_gini_values ? "true" : "false") << ","
        << csvEscape(result.frontier_range_certificate_scope) << ","
        << result.columns_generated_raw << ","
        << result.columns_after_dominance << ","
        << result.columns_dominated << ","
        << result.pricing_columns_enumerated << ","
        << result.dominance_input_columns << ","
        << result.dominance_kept_columns << ","
        << result.dominance_removed_columns << ","
        << result.dominance_removed_existing_projection << ","
        << result.dominance_removed_candidate_projection << ","
        << result.rmp_columns_inserted << ","
        << result.rmp_columns_active << ","
        << result.dominance_time_seconds << ","
        << csvEscape(result.dominance_mode) << ","
        << (result.dominance_exact_safe ? "true" : "false") << ","
        << result.projection_bound_prunes << ","
        << result.projection_bound_time_seconds << ","
        << result.projection_bound_best_value << ","
        << csvEscape(result.projection_bound_scope) << ","
        << result.penalty_budget << ","
        << result.domains_tightened_count << ","
        << result.total_domain_width_before << ","
        << result.total_domain_width_after << ","
        << result.penalty_tightening_time_seconds << ","
        << result.pricing_negative_columns_found << ","
        << result.pricing_negative_columns_inserted << ","
        << result.pricing_negative_columns_dominated << ","
        << (result.pricing_completed_exactly ? "true" : "false") << ","
        << result.pricing_best_reduced_cost_any << ","
        << result.pricing_best_new_reduced_cost << ","
        << result.pricing_duplicate_negative_projections << ","
        << result.pricing_new_negative_projections << ","
        << (result.pricing_blocked_by_duplicate_projection ? "true" : "false") << ","
        << (result.pricing_closure_certified_exact ? "true" : "false") << ","
        << result.support_duration_cuts_generated << ","
        << result.support_duration_pruned_labels << ","
        << result.support_duration_pruned_columns << ","
        << csvEscape(result.support_duration_min_pickup_rule) << ","
        << result.support_duration_strong_cuts_generated << ","
        << result.support_duration_strong_pruned_labels << ","
        << result.support_duration_strong_pruned_columns << ","
        << result.support_duration_max_subset_size << ","
        << result.support_duration_precompute_time_seconds << ","
        << result.route_mask_count_before_support_duration << ","
        << result.route_mask_count_after_support_duration << ","
        << result.route_masks_removed_by_support_duration << ","
        << result.route_mask_support_duration_precompute_time_seconds << ","
        << result.route_mask_support_duration_max_removed_subset_size << ","
        << (result.route_mask_support_duration_pruning ? "true" : "false") << ","
        << result.movement_domains_tightened_count << ","
        << result.movement_domain_width_before << ","
        << result.movement_domain_width_after << ","
        << result.movement_tightening_time_seconds << ","
        << result.movement_unreachable_station_count << ","
        << result.relaxation_lb_no_movement << ","
        << result.relaxation_lb_with_movement << ","
        << result.relaxation_lb_used << ","
        << (result.movement_audit_enabled ? "true" : "false") << ","
        << result.movement_audit_intervals << ","
        << result.movement_audit_bound_improved_count << ","
        << result.movement_audit_bound_worse_count << ","
        << result.frontier_min_interval_lower_bound << ","
        << csvEscape(result.frontier_lower_bound_source) << ","
        << result.frontier_bound_fathomed_interval_count << ","
        << result.frontier_unprocessed_interval_count << ","
        << result.frontier_relax_cache_hits << ","
        << result.frontier_relax_cache_misses << ","
        << result.frontier_relax_cache_partial_hits << ","
        << result.frontier_relax_cache_recomputed << ","
        << result.frontier_relax_cache_best_bound_reused << ","
        << (result.cheap_prepass_enabled ? "true" : "false") << ","
        << csvEscape(result.interval_processing_order_initial) << ","
        << csvEscape(result.interval_processing_order_actual) << ","
        << result.interval_priority_rebuild_count << ","
        << result.intervals_skipped_by_cheap_bound << ","
        << csvEscape(result.incumbent_source) << ","
        << csvEscape(result.incumbent_source_detail) << ","
        << (result.incumbent_import_attempted ? "true" : "false") << ","
        << (result.incumbent_import_verified ? "true" : "false") << ","
        << result.incumbent_import_objective << ","
        << result.incumbent_generation_time_seconds << ","
        << csvEscape(result.incumbent_generation_method) << ","
        << (result.focused_retry_enabled ? "true" : "false") << ","
        << result.focused_retry_attempts << ","
        << result.focused_retry_intervals << ","
        << csvEscape(result.focused_retry_selected_interval_ids) << ","
        << csvEscape(result.focused_retry_lb_before) << ","
        << csvEscape(result.focused_retry_lb_after) << ","
        << result.focused_retry_lb_improvements << ","
        << csvEscape(result.focused_retry_open_nodes_before) << ","
        << csvEscape(result.focused_retry_open_nodes_after) << ","
        << result.focused_retry_seconds << ","
        << csvEscape(result.focused_retry_stopped_reason) << ","
        << result.route_pool_columns_raw << ","
        << result.route_pool_columns_after_dominance << ","
        << result.route_pool_columns_removed_by_dominance << ","
        << result.route_pool_incumbent_master_calls << ","
        << result.route_pool_incumbent_master_states << ","
        << result.route_pool_incumbent_master_time_seconds << ","
        << (result.route_pool_incumbent_found ? "true" : "false") << ","
        << result.route_pool_incumbent_objective << ","
        << (result.route_pool_incumbent_verified ? "true" : "false") << ","
        << csvEscape(result.route_pool_incumbent_source) << ","
        << result.interval_candidates_found << ","
        << result.interval_candidates_verified << ","
        << result.interval_candidates_accepted << ","
        << result.best_interval_candidate_objective << ","
        << csvEscape(result.best_interval_candidate_rejection_reason) << ","
        << result.pickup_drop_pairs_total << ","
        << result.pickup_drop_pairs_compatible << ","
        << result.pickup_drop_pairs_incompatible << ","
        << result.pickup_drop_compat_flow_variables << ","
        << result.pickup_drop_compat_flow_constraints << ","
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
        << "bound_time_seconds,route_mask_time_seconds,gini_max_possible,"
        << "relevant_gini_upper_for_improvement,covered_gini_upper_bound,"
        << "frontier_covers_all_improving_gini_values,frontier_range_certificate_scope,"
        << "columns_generated_raw,columns_after_dominance,"
        << "columns_dominated,pricing_columns_enumerated,dominance_input_columns,dominance_kept_columns,"
        << "dominance_removed_columns,dominance_removed_existing_projection,dominance_removed_candidate_projection,"
        << "rmp_columns_inserted,rmp_columns_active,dominance_time_seconds,dominance_mode,dominance_exact_safe,"
        << "projection_bound_prunes,projection_bound_time_seconds,projection_bound_best_value,"
        << "projection_bound_scope,penalty_budget,domains_tightened_count,total_domain_width_before,"
        << "total_domain_width_after,penalty_tightening_time_seconds,pricing_negative_columns_found,"
        << "pricing_negative_columns_inserted,pricing_negative_columns_dominated,pricing_completed_exactly,"
        << "pricing_best_reduced_cost_any,pricing_best_new_reduced_cost,pricing_duplicate_negative_projections,"
        << "pricing_new_negative_projections,pricing_blocked_by_duplicate_projection,pricing_closure_certified_exact,"
        << "support_duration_cuts_generated,support_duration_pruned_labels,"
        << "support_duration_pruned_columns,support_duration_min_pickup_rule,"
        << "support_duration_strong_cuts_generated,support_duration_strong_pruned_labels,"
        << "support_duration_strong_pruned_columns,support_duration_max_subset_size,"
        << "support_duration_precompute_time_seconds,"
        << "route_mask_count_before_support_duration,route_mask_count_after_support_duration,"
        << "route_masks_removed_by_support_duration,route_mask_support_duration_precompute_time_seconds,"
        << "route_mask_support_duration_max_removed_subset_size,route_mask_support_duration_pruning,"
        << "movement_domains_tightened_count,movement_domain_width_before,movement_domain_width_after,"
        << "movement_tightening_time_seconds,movement_unreachable_station_count,"
        << "relaxation_lb_no_movement,relaxation_lb_with_movement,relaxation_lb_used,"
        << "movement_audit_enabled,movement_audit_intervals,"
        << "movement_audit_bound_improved_count,movement_audit_bound_worse_count,"
        << "frontier_min_interval_lower_bound,frontier_lower_bound_source,"
        << "frontier_bound_fathomed_interval_count,frontier_unprocessed_interval_count,"
        << "frontier_relax_cache_hits,frontier_relax_cache_misses,"
        << "frontier_relax_cache_partial_hits,frontier_relax_cache_recomputed,"
        << "frontier_relax_cache_best_bound_reused,cheap_prepass_enabled,"
        << "interval_processing_order_initial,interval_processing_order_actual,"
        << "interval_priority_rebuild_count,intervals_skipped_by_cheap_bound,"
        << "incumbent_source,incumbent_source_detail,incumbent_import_attempted,incumbent_import_verified,"
        << "incumbent_import_objective,incumbent_generation_time_seconds,incumbent_generation_method,"
        << "focused_retry_enabled,focused_retry_attempts,focused_retry_intervals,"
        << "focused_retry_selected_interval_ids,focused_retry_lb_before,focused_retry_lb_after,"
        << "focused_retry_lb_improvements,focused_retry_open_nodes_before,focused_retry_open_nodes_after,"
        << "focused_retry_seconds,focused_retry_stopped_reason,"
        << "route_pool_columns_raw,route_pool_columns_after_dominance,route_pool_columns_removed_by_dominance,"
        << "route_pool_incumbent_master_calls,route_pool_incumbent_master_states,"
        << "route_pool_incumbent_master_time_seconds,route_pool_incumbent_found,"
        << "route_pool_incumbent_objective,route_pool_incumbent_verified,route_pool_incumbent_source,"
        << "interval_candidates_found,interval_candidates_verified,interval_candidates_accepted,"
        << "best_interval_candidate_objective,best_interval_candidate_rejection_reason,"
        << "pickup_drop_pairs_total,pickup_drop_pairs_compatible,pickup_drop_pairs_incompatible,"
        << "pickup_drop_compat_flow_variables,pickup_drop_compat_flow_constraints,"
        << "certified_original_problem,result_file,log_file,"
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
