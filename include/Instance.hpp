#pragma once

#include <string>
#include <utility>
#include <vector>

namespace ebrp {

struct Instance {
    std::string path;
    std::string name;
    int V = 0;
    int M = 0;
    std::vector<int> Q;                 // size M
    std::vector<int> capacity;          // index 0 is depot
    std::vector<int> initial;           // index 0 is depot
    std::vector<int> target;            // index 0 is depot, station targets > 0
    std::vector<double> weights;        // index 0 is depot
    std::vector<double> min_ratio;      // index 0 is depot, parsed for compatibility
    std::vector<std::pair<double, double>> points;
    std::vector<std::vector<double>> dist;
    double total_time_limit = 3600.0;
    double pickup_time = 60.0;
    double drop_time = 60.0;
    std::string distance_convention;
};

struct SolveOptions {
    std::string method = "tailored";
    std::string input_path;
    std::string log_path;
    std::string out_path;
    double lambda = 0.15;
    double total_time_limit = 3600.0;
    double solve_time_limit = 1000.0;
    double pickup_time = 60.0;
    double drop_time = 60.0;
    int threads = 1;
    int bpc_workers = 1;
    int pricing_threads = 1;
    bool parallel_frontier = false;
    bool parallel_nodes = false;
    bool plain_baseline = false;
    bool gcap_seed_cplex = false;
    std::string bpc_incumbent = "none";
    double bpc_incumbent_seconds = 20.0;
    int bpc_incumbent_rounds = 12;
    std::string incumbent_json_path;
    std::string incumbent_format = "auto";
    std::string incumbent_source_name;
    double gcap_seed_time_limit = -1.0;
    double gini_cap = -1.0;
    double gini_floor = -1.0;
    int max_branch_nodes = 31;
    int frontier_intervals = 4;
    int frontier_refine_splits = 0;
    int frontier_split_batch = 0;
    int frontier_retry_passes = 2;
    int frontier_retry_nodes = -1;
    double frontier_retry_reserve_seconds = 0.0;
    double frontier_relax_seconds = -1.0;
    bool frontier_final_closure = false;
    int frontier_final_nodes = 1023;
    int route_mask_max_v = 12;
    int gcap_warmstart_level = 1; // 0=seed routes only, 1=sparse generic columns, 2=full generic columns
    int gcap_pricing_columns = 1;
    bool column_dominance = true;
    std::string column_dominance_mode = "exact";
    bool projection_bound = true;
    bool penalty_domain_tightening = true;
    bool movement_domain_tightening = true;
    bool movement_bound_audit = false;
    bool frontier_best_bound_scheduling = true;
    bool frontier_relaxation_cache = true;
    bool frontier_column_cache = false;
    bool frontier_focused_min_lb_retry = true;
    bool support_duration_pruning = true;
    bool route_mask_support_duration_pruning = true;
    bool support_feasibility_oracle = false;
    int support_duration_max_subset_size = 5;
    std::string hga_incumbent_path;
    std::string hga_incumbent_format = "auto";
    int inventory_probe_max_v = 7;
    double inventory_probe_seconds = -1.0;
};

} // namespace ebrp
