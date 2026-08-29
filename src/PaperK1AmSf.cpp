#include "PaperK1AmSf.hpp"

namespace ebrp {

bool isPaperK1AmSfPresetOrAlias(const std::string& lower_name) {
    return lower_name == "paper-k1-am-sf" || lower_name == "k1-am-f0" ||
           lower_name == "paper-k1-am-f0";
}

void configurePaperK1AmSfOverrides(SolveOptions& opt) {
    opt.algorithm_preset = "paper-k1-am-sf";
    opt.k1_am_sf_controller_enabled = true;
    opt.initial_gini_interval_count = 1;
    opt.split_point_rule = "midpoint";
    opt.split_score_rule = "balanced-normalized-closure";
    opt.split_threshold = 0.08;
    opt.maximum_split_depth = 8;
    opt.minimum_interval_width = 1e-4;
    opt.split_factor = 2;
    opt.child_infeasibility_policy = "exact";
    opt.native_target_policy = "existing-k1-am-sf";
    opt.exact_parent_closure = true;
    opt.tailored_bc_enabled = true;
    opt.tailored_bc_mode = "static";
    opt.tailored_bc_callback_cut_profile = "off";
    opt.compact_bc_root_cut_rounds = 0;
    opt.compact_bc_dynamic_cut_families = "none";
    opt.compact_bc_cut_profile = "balanced";
    opt.compact_bc_low_gini_strengthening = "safe";
    opt.compact_bc_denominator_bound_mode = "tight";
    opt.compact_bc_objective_estimator_mode = "adaptive";
    opt.compact_bc_domain_propagation_mode = "iterative";
    opt.compact_bc_domain_propagation_rounds = 2;
    opt.compact_bc_support_duration_cuts = true;
    opt.compact_bc_support_cut_max_size = 3;
    opt.compact_bc_support_cut_max_subsets = 50000;
    opt.compact_bc_variable_s_centering = true;
    opt.compact_bc_sp_product_estimator = "paper-safe";
    opt.compact_bc_sp_product_bounds = "tight";
    opt.compact_bc_s_range_refinement = "off";
    opt.tailored_bc_branching_priority = "off";
    opt.tailored_bc_gini_branching = "off";
    opt.tailored_bc_gini_subset_envelope = false;
    opt.tailored_bc_low_gini_l1_centering = false;
    opt.tailored_bc_local_centering = false;
    opt.tailored_bc_subset_cross_h_centering = false;
    opt.tailored_bc_local_q_centering = false;
    opt.tailored_bc_subset_inventory_imbalance = false;
    opt.tailored_bc_transfer_cutset = false;
    opt.tailored_bc_gs_product_coupling = false;
    opt.tailored_bc_disaggregated_sp_estimator = false;
    opt.tailored_bc_bucket_ratio_domain_tightening = false;
    opt.tailored_bc_bucket_subset_ratio_domain = false;
    opt.tailored_bc_bucket_integer_inventory_domain = false;
    opt.tailored_bc_bucket_required_movement = false;
    opt.tailored_bc_bucket_required_visit = false;
    opt.tailored_bc_s_bucket_ledger = "off";
    opt.global_gini_tree_presolve = "off";
    opt.global_gini_tree_search = "traditional";
    opt.global_gini_tree_child_estimate_mode = "parent-copy";
    opt.global_gini_tree_row_attachment_mode = "full-inherited-pack";
    opt.global_gini_tree_row_timing_mode = "deferred";
    opt.global_gini_tree_native_mip_start = false;
    opt.global_gini_tree_root_connectivity_flow = true;
    opt.global_gini_tree_root_connectivity_flow_variant = "round20-current";
    opt.frontier_execution_mode = "external-gini-tree";
    opt.external_gini_backend = "gurobi";
    opt.external_gini_lifecycle = "round31-open-native-bounded";
    opt.external_gini_scheduling = "round31-nonblocking-native-bound";
    opt.external_gini_warm_start = false;
    opt.external_gini_interval_mip_policy =
        "interval-mip-core-no-exhaustive-subset-duration";
    opt.exact_phase_local_redecode_repair = false;
    opt.primal_heuristic = "hga-tgbc";
    opt.primal_heuristic_seed = 20260626u;
    opt.primal_heuristic_stop = "generation-stagnation";
    opt.primal_heuristic_no_improve_generations = 2000;
    opt.round34_c6_startup_variant = "hga-full";
    opt.round43_envelope_refinement = "off";
    // The historical fields below are neutral compatibility adapters.  The
    // first-class controller above is the only source of paper-mainline K1
    // geometry and split decisions.
    opt.frontier_intervals = 4;
    opt.frontier_adaptive_split = true;
    opt.frontier_adaptive_max_depth = 8;
    opt.frontier_adaptive_min_width = 1e-4;
    opt.frontier_adaptive_split_factor = 2;
    opt.round43_initial_k0 = 4;
    opt.round43_lookahead_depth = 1;
    opt.round43_rho = 0.1;
    opt.round43_score = "d";
    opt.round43_envelope_mode = "single";
    opt.round43_width_measure = "g-mccormick-unit";
    opt.round43_lifted_cuts = "off";
    opt.round43_frontier_consolidation = "off";
    opt.round40_c6_coarse_start = "off";
    opt.c6_normalized_split_threshold = 0.01;
    opt.c6_normalized_split_threshold_explicit = true;
    opt.round44_envelope_tail_repair = "off";
    opt.round44_rank1_cuts = "off";
    opt.round44_mip_starts = "off";
    opt.round44_frontier_consolidation = "off";
    opt.round45_adaptive_parametric_partition = "off";
    opt.round45_point_rule = "midpoint";
    opt.round47_c6_adaptive_mass = "off";
    opt.round47_c6_adaptive_mass_tau = 0.07915;
    opt.round47_c6_adaptive_mass_tau_explicit = false;
    opt.round48_k1_amf = "off";
    opt.round49_k1_am_rc = "off";
}

const std::vector<std::string>& paperK1AmSfActiveFamilies() {
    static const std::vector<std::string> families = {
        "gini_interval_bounds",
        "direct_gini_cap_floor",
        "interval_tight_g_times_binary_mccormick_hull",
        "final_inventory_penalty_domains",
        "movement_reachability_domains",
        "inventory_conservation",
        "visit_inventory_linking",
        "verified_incumbent_objective_row",
        "objective_lower_estimator",
        "penalty_lower_bound_closure",
        "sp_product_mccormick_rows",
        "sp_product_objective_estimator",
        "pair_support_duration_cover",
        "triple_support_duration_cover",
        "connectivity_flow_formulation",
        "iterative_domain_propagation",
        "tight_denominator_bounds",
    };
    return families;
}

const std::vector<std::string>& paperK1AmSfInactiveFamilies() {
    static const std::vector<std::string> families = {
        "exhaustive_subset_duration_block",
        "gini_spread_cuts",
        "required_movement_cuts",
        "transfer_cutset_cuts",
        "subset_inventory_cuts",
        "dynamic_support_duration_callback",
        "tailored_dynamic_user_cuts",
        "inventory_route_root_closure",
        "custom_branching_priorities",
        "symmetry_research",
    };
    return families;
}

} // namespace ebrp
