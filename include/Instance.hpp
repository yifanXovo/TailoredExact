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
    bool frontier_focused_intensification = true;
    double frontier_focused_reserve_fraction = 0.25;
    double frontier_focused_relax_seconds = 5.0;
    int frontier_focused_max_passes = 2;
    bool frontier_adaptive_split = true;
    int frontier_adaptive_max_depth = 3;
    double frontier_adaptive_min_width = 1e-4;
    int frontier_adaptive_split_factor = 2;
    bool route_pool_incumbent = true;
    int route_pool_max_columns_per_vehicle = 5000;
    bool route_pool_keep_best_per_projection = true;
    bool pickup_drop_compat_flow = true;
    bool pickup_drop_transfer_cap_flow = true;
    bool vehicle_indexed_operation_relaxation = true;
    bool vehicle_indexed_relaxation_audit = false;
    bool vehicle_indexed_transfer_flow = true;
    bool support_duration_pruning = true;
    bool route_mask_support_duration_pruning = true;
    bool route_mask_operation_budget_cuts = true;
    bool support_feasibility_oracle = false;
    int support_duration_max_subset_size = 5;
    std::string hga_incumbent_path;
    std::string hga_incumbent_format = "auto";
    std::string external_incumbent_path;
    std::string external_incumbent_format = "auto";
    std::string export_incumbent_path;
    std::string large_instance_mode = "auto";
    std::string pricing_engine = "auto";
    std::string large_lb_mode = "auto";
    std::string column_tracks = "auto";
    bool relaxed_columns_in_rmp = false;
    int relaxed_columns_max_per_pricing = 8;
    std::string rmp_column_space = "auto";
    bool dssr_close_relaxed_pricing = false;
    double dssr_relaxed_closure_time = 30.0;
    long long dssr_relaxed_closure_max_labels = 0;
    std::string dssr_relaxed_closure_checkpoint;
    bool large_relaxed_rmp = false;
    int ng_size = 12;
    std::string ng_neighborhood_mode = "nearest";
    int dssr_max_rounds = 4;
    int dssr_expand_per_round = 4;
    double dssr_time_limit = 30.0;
    bool dssr_final_exact = true;
    double cg_dual_box_radius = 1.0;
    int cg_stabilization_max_nonimprove = 3;
    std::string progress_log_path;
    double progress_interval_seconds = 0.0;
    std::string frontier_focus_interval_id = "auto";
    std::string frontier_focus_range;
    std::string frontier_focus_from_result;
    std::string frontier_focus_leaf_id = "auto";
    bool frontier_focus_only = false;
    bool frontier_focus_use_existing_incumbent = true;
    double frontier_focus_time_limit = -1.0;
    double frontier_focus_relax_seconds = -1.0;
    int frontier_focus_tree_nodes = -1;
    std::vector<std::string> frontier_import_interval_bound_paths;
    bool branch_inventory = true;
    double branch_inventory_priority = 1.0;
    bool branch_operation_mode = true;
    std::string branch_selection = "auto";
    int strong_branching_candidates = 3;
    double strong_branching_time = 0.0;
    bool reliability_branching = false;
    std::string frontier_export_state_path;
    std::string frontier_resume_state_path;
    std::string frontier_resume_interval_id = "auto";
    std::string frontier_resume_mode = "interval-only";
    std::string frontier_closure_mode = "auto";
    int closure_max_cg_iterations = 24;
    double closure_pricing_time_per_call = 0.0;
    int closure_returned_columns = 4;
    bool closure_final_exact_pricing = true;
    std::string cg_dual_stabilization = "none";
    double cg_dual_smoothing_alpha = 0.7;
    int cg_stabilization_switch_to_true_after = 8;
    bool frontier_iterative_closure = false;
    int frontier_iterative_max_rounds = 2;
    double frontier_iterative_round_time = 60.0;
    double frontier_iterative_target_gap = 0.0;
    bool frontier_iterative_use_resume = true;
    std::string frontier_iterative_export_dir;
    bool frontier_export_open_nodes = true;
    bool frontier_resume_open_nodes = true;
    bool pricing_final_verifier = false;
    double pricing_verifier_time = 30.0;
    std::string pricing_verifier_checkpoint;
    std::string pricing_verifier_resume;
    std::string pricing_verifier_mode = "auto";
    int inventory_probe_max_v = 7;
    double inventory_probe_seconds = -1.0;
};

} // namespace ebrp
