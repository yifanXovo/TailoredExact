#pragma once

#include "Instance.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct StopOperation {
    int station = 0;
    int pickup = 0;
    int drop = 0;
};

struct RoutePlan {
    int vehicle = 0;
    std::vector<int> nodes;             // includes depot at start and end
    std::vector<StopOperation> operations;
};

struct Verification {
    bool feasible = false;
    bool routes_start_end_depot = false;
    bool station_disjoint = false;
    bool load_feasible = false;
    bool station_feasible = false;
    bool duration_feasible = false;
    bool objective_matches = false;
    std::vector<double> route_travel_time;
    std::vector<double> route_operation_time;
    std::vector<double> route_duration;
    std::vector<int> final_inventory;
    double G = 0.0;
    double P = 0.0;
    double objective = 0.0;
    std::vector<std::string> errors;
};

struct SolveResult {
    std::string instance_name;
    std::string input_path;
    std::string result_file;
    std::string log_file;
    std::string method;
    std::string status;
    std::string certificate;
    double objective = 0.0;
    double G = 0.0;
    double P = 0.0;
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double gap = 0.0;
    double runtime_seconds = 0.0;
    double wall_time_seconds = 0.0;
    double aggregate_worker_time_seconds = 0.0;
    long long nodes = 0;
    long long columns = 0;
    long long pricing_calls = 0;
    long long cuts_added = 0;
    long long pricing_closed_nodes = 0;
    long long open_nodes = 0;
    int unresolved_intervals = 0;
    int invalid_bound_intervals = 0;
    int bpc_workers = 1;
    int pricing_threads = 1;
    bool parallel_frontier = false;
    bool parallel_nodes = false;
    long long parallel_tasks = 0;
    double pricing_time_seconds = 0.0;
    double master_time_seconds = 0.0;
    double bound_time_seconds = 0.0;
    double route_mask_time_seconds = 0.0;
    long long columns_generated_raw = 0;
    long long columns_after_dominance = 0;
    long long columns_dominated = 0;
    double dominance_time_seconds = 0.0;
    std::string dominance_mode = "exact";
    bool dominance_exact_safe = true;
    long long projection_bound_prunes = 0;
    double projection_bound_time_seconds = 0.0;
    double projection_bound_best_value = 0.0;
    std::string projection_bound_scope = "global";
    double penalty_budget = 0.0;
    long long domains_tightened_count = 0;
    long long total_domain_width_before = 0;
    long long total_domain_width_after = 0;
    double penalty_tightening_time_seconds = 0.0;
    long long pricing_negative_columns_found = 0;
    long long pricing_negative_columns_inserted = 0;
    long long pricing_negative_columns_dominated = 0;
    bool pricing_completed_exactly = true;
    long long frontier_cache_hits = 0;
    long long frontier_cache_columns_loaded = 0;
    long long frontier_cache_columns_inserted = 0;
    double frontier_cache_time_seconds = 0.0;
    std::vector<RoutePlan> routes;
    std::vector<int> final_inventory;
    Verification verification;
    std::vector<std::string> notes;
};

struct ObjectiveParts {
    double G = 0.0;
    double P = 0.0;
    double objective = 0.0;
    double S = 0.0;
    double H = 0.0;
};

ObjectiveParts computeObjectiveParts(const Instance& instance,
                                     const std::vector<int>& final_inventory,
                                     double lambda);

std::string resultToJson(const SolveResult& result);
std::string resultsToJson(const std::vector<SolveResult>& results);
void writeTextFile(const std::string& path, const std::string& text);

std::string inferMethodScope(const SolveResult& result);
bool inferSolvesOriginalObjective(const SolveResult& result);
bool inferIsBpc(const SolveResult& result);
std::string inferCertificateType(const SolveResult& result);
std::string inferStopReason(const SolveResult& result);
bool inferVerifierPassed(const SolveResult& result);
bool inferCertifiedOriginalProblem(const SolveResult& result);

} // namespace ebrp
