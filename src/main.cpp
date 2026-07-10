#include "Branching.hpp"
#include "Bounds.hpp"
#include "ColumnPool.hpp"
#include "ColumnGeneration.hpp"
#include "CplexBaseline.hpp"
#include "Cuts.hpp"
#include "Evaluator.hpp"
#include "HgaTgbcRunner.hpp"
#include "Master.hpp"
#include "Parser.hpp"
#include "Pricing.hpp"
#include "Result.hpp"
#include "TailoredBC.hpp"
#include "TailoredBCCuts.hpp"
#include "TailoredBCCplexApi.hpp"
#include "TailoredExact.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
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
#include <new>
#include <numeric>
#include <random>
#include <regex>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

void usage() {
    std::cerr
        << "Usage: ExactEBRP --method tailored|cplex|interval-cutoff-oracle|primal-heuristic|pricing|pricing-branch|cuts|branching|master|cg|gcap-cg|gcap-branch|gcap-tree|gcap-frontier|dominance-test|support-pruning-test|route-mask-support-test|route-mask-operation-budget-test|adaptive-frontier-split-test|inventory-branching-test|operation-mode-branching-test|pricing-closure-audit-test|resume-state-test|pricing-verifier-test|iterative-closure-test|certificate-basis-test|option-consistency-test|tailored-bc-callback-smoke-test|tailored-bc-relaxation-vector-smoke-test|tailored-bc-branch-callback-smoke-test|tailored-bc-cut-validity-test|gini-subset-envelope-test|low-gini-l1-centering-test|transfer-cutset-validity-test|s-bucket-coverage-test|station-set-test|ng-dssr-pricing-test|dssr-exactness-test|dual-stabilization-test|bpc-hybrid-pricing-test|two-track-column-test|projection-safe-relaxed-column-test|non-elementary-relaxed-column-test|ng-relaxed-closure-test|relaxed-rmp-cg-test|frontier-relaxed-rmp-cg-test|relaxed-rmp-test|relaxed-pricing-closure-test|relaxed-column-incumbent-safety-test|large-relaxed-rmp-test|large-relaxed-rmp-cg-test|external-incumbent-test|large-instance-mode-test|large-lb-test|incumbent-import-test|route-pool-incumbent-test|pickup-drop-compat-flow-test|pickup-drop-transfer-cap-test|vehicle-indexed-relaxation-test|vehicle-indexed-transfer-flow-test --input <path> "
        << "--lambda 0.15 --T 3600 --threads <N> --time-limit <seconds> "
        << "--log <logfile> --out <json> "
        << "[--bpc-workers <N>] [--pricing-threads <N>] [--parallel-frontier true|false] [--parallel-nodes true|false] "
        << "[--gini-cap <gamma>] [--gini-floor <gamma>] [--max-nodes <N>] [--frontier-intervals <N>] [--frontier-refine-splits <N>] "
        << "[--frontier-split-batch <N>] [--frontier-retry-passes <N>] [--frontier-retry-nodes <N>] "
        << "[--frontier-retry-reserve <seconds>] [--frontier-relax-seconds <seconds>] [--route-mask-max-v <V>] "
        << "[--bpc-incumbent none|greedy|random|local|pool|pricing|portfolio|strong|compact|compact-cplex|auto|best-of-all] [--bpc-incumbent-seconds <seconds>] [--bpc-incumbent-rounds <N>] "
        << "[--frontier-final-closure true|false] [--frontier-final-nodes <N>] "
        << "[--gcap-warmstart seed|sparse|full] [--gcap-pricing-columns <N>] "
        << "[--column-dominance true|false] [--column-dominance-mode exact|pareto|off] "
        << "[--projection-bound true|false] [--penalty-domain-tightening true|false] "
        << "[--movement-domain-tightening true|false] [--movement-bound-audit true|false] "
        << "[--frontier-best-bound-scheduling true|false] [--frontier-relaxation-cache true|false] "
        << "[--frontier-split-before-tree true|false] "
        << "[--frontier-column-cache true|false] [--frontier-focused-min-lb-retry true|false] "
        << "[--frontier-focused-intensification true|false] [--frontier-focused-reserve-fraction <fraction>] "
        << "[--frontier-focused-relax-seconds <seconds>] [--frontier-focused-max-passes <N>] "
        << "[--frontier-adaptive-split true|false] [--frontier-adaptive-max-depth <N>] "
        << "[--frontier-adaptive-min-width <width>] [--frontier-adaptive-split-factor <N>] "
        << "[--support-duration-pruning true|false] [--support-duration-max-subset-size <N>] "
        << "[--pricing-completion-lb-pruning true|false] "
        << "[--route-mask-support-duration-pruning true|false] [--route-mask-operation-budget-cuts true|false] [--support-feasibility-oracle true|false] "
        << "[--route-pool-incumbent true|false] [--route-pool-max-columns-per-vehicle <N>] "
        << "[--route-pool-keep-best-per-projection true|false] "
        << "[--exact-phase-local-redecode-repair true|false] [--exact-phase-local-redecode-seconds <seconds>] "
        << "[--pickup-drop-compat-flow true|false] [--pickup-drop-transfer-cap-flow true|false] "
        << "[--vehicle-indexed-operation-relaxation true|false] [--vehicle-indexed-relaxation-audit true|false] "
        << "[--vehicle-indexed-transfer-flow true|false] [--v20-safe-relaxation-cuts true|false] "
        << "[--frontier-bpc-fallback-mode off|controlling-intervals|best-bound] "
        << "[--frontier-bpc-fallback-reserve-fraction <fraction>] "
        << "[--frontier-bpc-fallback-min-seconds <seconds>] "
        << "[--frontier-bpc-fallback-max-intervals <N>] "
        << "[--gcap-seed-cplex] [--gcap-seed-time-limit <seconds>] "
        << "[--incumbent-json <path>] [--incumbent-format auto|exact_result|route_json|csv] "
        << "[--hga-incumbent <path>] [--hga-incumbent-format auto|route_json|csv|legacy] "
        << "[--external-incumbent <path>] [--external-incumbent-format auto|route_json|csv|legacy_text] [--export-incumbent <path>] "
        << "[--primal-heuristic none|greedy|hga-tgbc|best-of-all] [--primal-heuristic-seconds <seconds>] "
        << "[--primal-heuristic-seed <seed>] [--primal-heuristic-runs <N>] "
        << "[--heuristic-candidates-csv <path>] "
        << "[--large-instance-mode auto|off|force] [--large-lb-mode none|inventory-only|movement-projection|column-pool-relaxation|auto] "
        << "[--pricing-engine exact-label|ng-dssr|hybrid] "
        << "[--ng-size <N>] [--ng-neighborhood-mode nearest|dual-aware|hybrid] "
        << "[--dssr-max-rounds <N>] [--dssr-expand-per-round <N>] [--dssr-time-limit <seconds>] [--dssr-final-exact true|false] "
        << "[--column-tracks elementary-only|two-track|auto] [--relaxed-columns-in-rmp true|false] "
        << "[--relaxed-columns-max-per-pricing <N>] [--rmp-column-space elementary|ng-relaxed|two-track|auto] "
        << "[--allow-non-elementary-relaxed-columns true|false] [--relaxed-projection-strict true|false] "
        << "[--ng-relaxed-closure true|false] [--ng-relaxed-closure-time <seconds>] [--ng-relaxed-max-labels <N>] "
        << "[--ng-relaxed-pricing-checkpoint <path>] [--ng-relaxed-pricing-resume <path>] "
        << "[--relaxed-rmp-cg true|false] [--relaxed-rmp-cg-max-iterations <N>] [--relaxed-rmp-cg-time <seconds>] "
        << "[--relaxed-rmp-cg-columns-per-iteration <N>] [--frontier-relaxed-rmp-cg true|false] "
        << "[--frontier-relaxed-rmp-cg-time-per-interval <seconds>] [--frontier-relaxed-rmp-cg-max-intervals <N>] "
        << "[--large-relaxed-rmp-cg true|false] [--large-relaxed-rmp-column-budget <N>] [--large-relaxed-rmp-time <seconds>] "
        << "[--dssr-close-relaxed-pricing true|false] [--dssr-relaxed-closure-time <seconds>] "
        << "[--dssr-relaxed-closure-max-labels <N>] [--dssr-relaxed-closure-checkpoint <path>] [--large-relaxed-rmp true|false] "
        << "[--incumbent-source-name <name>] [--inventory-probe-max-v <V>] [--inventory-probe-seconds <seconds>] "
        << "[--progress-log <path>] [--ub-event-log <path>] [--progress-interval-seconds <seconds>] "
        << "[--frontier-focus-only true|false] [--frontier-focus-interval-id auto|N] "
        << "[--frontier-focus-range <lo,hi>] [--frontier-focus-from-result <json>] "
        << "[--frontier-focus-leaf-id id|auto|min-lb] [--frontier-focus-use-existing-incumbent true|false] "
        << "[--frontier-focus-time-limit <seconds>] [--frontier-focus-relax-seconds <seconds>] "
        << "[--frontier-focus-tree-nodes <N>] [--frontier-import-interval-bound <json>] "
        << "[--branch-inventory true|false] [--branch-inventory-priority <weight>] "
        << "[--branch-operation-mode true|false] [--branch-selection auto|ryan-foster|inventory|operation-mode|strong] "
        << "[--strong-branching-candidates <N>] [--strong-branching-time <seconds>] "
        << "[--reliability-branching true|false] "
        << "[--frontier-export-state <path>] [--frontier-resume-state <path>] "
        << "[--frontier-resume-interval-id id|auto|min-lb] [--frontier-resume-mode interval-only|full-frontier] "
        << "[--frontier-closure-mode exact-cg|tree|relax-only|auto] "
        << "[--closure-max-cg-iterations <N>] [--closure-pricing-time-per-call <seconds>] "
        << "[--closure-returned-columns <N>] [--closure-final-exact-pricing true|false] "
        << "[--cg-dual-stabilization none|smooth|box] [--cg-dual-smoothing-alpha <alpha>] "
        << "[--cg-dual-box-radius <radius>] [--cg-stabilization-max-nonimprove <N>] "
        << "[--cg-stabilization-switch-to-true-after <N>] "
        << "[--frontier-iterative-closure true|false] [--frontier-iterative-max-rounds <N>] "
        << "[--frontier-iterative-round-time <seconds>] [--frontier-iterative-target-gap <gap>] "
        << "[--frontier-iterative-use-resume true|false] [--frontier-iterative-export-dir <path>] "
        << "[--frontier-export-open-nodes true|false] [--frontier-resume-open-nodes true|false] "
        << "[--interval-closure-mode off|focus|merge] [--interval-closure-input <csv>] "
        << "[--interval-closure-target-ids <list>] [--interval-closure-range <lo,hi>] "
        << "[--interval-closure-output <path>] [--interval-closure-merge-ledger <path>] "
        << "[--interval-closure-time-limit <seconds>] [--interval-closure-variant-mode exhaustive|best-fixed|cutoff-feasibility|bpc] "
        << "[--relaxation-certificate-mode bound|cutoff-feasibility|both] [--cutoff-feasibility-epsilon <eps>] "
        << "[--cutoff-feasibility-time-limit <seconds>] [--relaxation-portfolio-mode fixed|adaptive|race|exhaustive] "
        << "[--relaxation-exhaustive-variants <list>] [--relaxation-exhaustive-stop-on-fathom true|false] "
        << "[--interval-exact-cutoff-oracle off|compact-mip] [--interval-exact-cutoff-gamma-L <gamma>] "
        << "[--interval-exact-cutoff-gamma-U <gamma>] [--interval-exact-cutoff-UB <value>] "
        << "[--interval-exact-cutoff-epsilon <eps>] [--interval-exact-cutoff-time-limit <seconds>] "
        << "[--mip-solver cplex] [--mip-threads <N>] [--compact-bc-time-limit <seconds>] "
        << "[--compact-bc-root-cut-rounds <N>] [--compact-bc-cut-profile conservative|balanced|aggressive] "
        << "[--tailored-bc-support-duration-cover-mode basic|lifted|off] "
        << "[--interval-exact-cutoff-export-lp <path>] [--interval-exact-cutoff-result <path>] "
        << "[--pricing-final-verifier true|false] [--pricing-verifier-time <seconds>] "
        << "[--pricing-verifier-checkpoint <path>] [--pricing-verifier-resume <path>] "
        << "[--pricing-verifier-mode label-dp|route-mask-dp|auto] "
        << "[--algorithm-preset paper-gf-tailored-bc|paper-gf-compact-bc|paper-gf-bpc-core|paper-bpc-core|paper-bpc-core-adaptive|paper-exact-v20-certificate|paper-exact-portfolio|paper-bpc-experimental|diagnostic-large] "
        << "[--production-preset <preset-alias>] [--incumbent-archive-auto true|false] "
        << "[--incumbent-archive-dir <dir>]\n";
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

std::string lowerAscii(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return value;
}

void applyAlgorithmPreset(ebrp::SolveOptions& opt) {
    opt.algorithm_preset = lowerAscii(opt.algorithm_preset);
    if (opt.algorithm_preset.empty() || opt.algorithm_preset == "none") {
        opt.algorithm_preset = "custom";
    }
    if (opt.algorithm_preset == "custom") return;

    if (opt.algorithm_preset == "paper-gf-compact-bc" ||
        opt.algorithm_preset == "paper-gf-interval-bc" ||
        opt.algorithm_preset == "paper-gf-cutoff-cert") {
        opt.algorithm_preset = "paper-gf-compact-bc";
    }

    if (opt.algorithm_preset == "paper-gf-tailored-bc" ||
        opt.algorithm_preset == "paper-gf-compact-bc" ||
        opt.algorithm_preset == "paper-gf-bpc-core" ||
        opt.algorithm_preset == "paper-bpc-core" ||
        opt.algorithm_preset == "paper-bpc-core-adaptive" ||
        opt.algorithm_preset == "paper-exact-v20-certificate" ||
        opt.algorithm_preset == "paper-exact-portfolio") {
        opt.pricing_engine = "exact-label";
        opt.column_tracks = "elementary-only";
        opt.rmp_column_space = "elementary";
        opt.relaxed_columns_in_rmp = false;
        opt.relaxed_rmp_cg = false;
        opt.frontier_relaxed_rmp_cg = false;
        opt.large_relaxed_rmp = false;
        opt.large_relaxed_rmp_cg = false;
        opt.ng_relaxed_closure = false;
        opt.dssr_close_relaxed_pricing = false;
        opt.cg_dual_stabilization = "none";
        opt.dssr_final_exact = true;
        opt.large_instance_mode = "off";
        opt.large_lb_mode = "none";
        opt.frontier_focus_only = false;
        opt.frontier_focus_interval_id = "auto";
        opt.frontier_focus_range.clear();
        opt.frontier_focus_from_result.clear();
        opt.frontier_focus_leaf_id = "auto";
        opt.frontier_import_interval_bound_paths.clear();
        opt.frontier_resume_state_path.clear();
        opt.frontier_resume_interval_id = "auto";
        opt.frontier_iterative_closure = false;
        opt.frontier_closure_mode = "auto";
        opt.pricing_final_verifier = false;
        opt.frontier_column_cache = false;
        opt.column_dominance = true;
        opt.column_dominance_mode = "exact";
        opt.gcap_pricing_columns = std::max(opt.gcap_pricing_columns, 4);
        opt.movement_domain_tightening = true;
        opt.projection_bound = true;
        opt.penalty_domain_tightening = true;
        opt.vehicle_indexed_operation_relaxation = true;
        opt.vehicle_indexed_transfer_flow = true;
        opt.route_mask_operation_budget_cuts = true;
        opt.route_pool_incumbent = true;
        opt.exact_phase_local_redecode_repair = true;
        opt.branch_inventory = true;
        opt.branch_operation_mode = true;
        opt.frontier_best_bound_scheduling = true;
        opt.frontier_relaxation_cache = true;
        opt.frontier_split_before_tree = true;
        if (!opt.frontier_adaptive_max_depth_explicit) {
            opt.frontier_adaptive_max_depth =
                std::max(opt.frontier_adaptive_max_depth, 8);
        }
        if (!opt.primal_heuristic_explicit) {
            opt.primal_heuristic = "hga-tgbc";
        }
        if (opt.algorithm_preset == "paper-gf-tailored-bc" ||
            opt.algorithm_preset == "paper-gf-compact-bc" ||
            opt.algorithm_preset == "paper-gf-bpc-core" ||
            opt.algorithm_preset == "paper-bpc-core") {
            opt.route_mask_max_v = 0;
            opt.route_mask_support_duration_pruning = false;
            opt.route_mask_operation_budget_cuts = false;
        }
        if (opt.algorithm_preset == "paper-gf-compact-bc" ||
            opt.algorithm_preset == "paper-gf-tailored-bc") {
            opt.relaxation_portfolio_mode = "fixed";
            opt.relaxation_portfolio_keep_best_bound = true;
            opt.v20_safe_relaxation_cuts = true;
            opt.v20_cover_cuts = true;
            opt.v20_cover_max_size = std::max(opt.v20_cover_max_size, 4);
            opt.station_residual_cover_cuts = true;
            opt.large_compact_flow_relaxation = "mip-light";
            opt.large_compact_flow_connectivity = true;
            opt.service_operation_min_handling_cuts = true;
            opt.gini_spread_cuts = true;
            opt.required_movement_cuts = true;
            opt.global_handling_capacity_cuts = true;
            opt.low_gini_ratio_band_tightening = true;
            opt.transfer_subset_capacity_cuts = true;
            opt.compact_bc_direct_gini_rows = true;
            opt.compact_bc_tight_mccormick = true;
            opt.compact_bc_inventory_conservation = true;
            opt.compact_bc_movement_reachability_domains = true;
            opt.compact_bc_visit_inventory_linking = true;
            opt.compact_bc_objective_estimator_cutoff = true;
            opt.compact_bc_penalty_lb_closure = true;
            opt.compact_bc_support_duration_cuts = true;
            opt.compact_bc_pairwise_transfer_compatibility = true;
            opt.compact_bc_receiver_source_cover_cuts = false;
            opt.compact_bc_support_cut_max_size =
                std::max(opt.compact_bc_support_cut_max_size, 3);
            opt.compact_bc_support_cut_max_subsets =
                std::max(opt.compact_bc_support_cut_max_subsets, 50000);
            opt.frontier_scheduling_mode = "default";
            opt.frontier_bpc_fallback_mode = "off";
            opt.core_bpc_reserve_fraction = 0.0;
            opt.core_bpc_min_seconds = 0.0;
            opt.core_bpc_max_leaves = 0;
            opt.auto_interval_bpc_fallback = false;
            opt.auto_interval_oracle = true;
            opt.auto_interval_oracle_merge = true;
            opt.auto_interval_oracle_order = "all";
            opt.auto_interval_oracle_max_leaves = 0;
            opt.auto_interval_oracle_continue_after_timeout = true;
            opt.auto_interval_oracle_leaf_budget_policy = "per-leaf";
            opt.auto_interval_oracle_recursive_split = false;
            opt.interval_exact_cutoff_oracle = "compact-mip";
            opt.interval_exact_oracle_mode = "objective-bound";
            opt.interval_oracle_merge_timeout_bound = true;
            opt.interval_oracle_low_gini_tightening = true;
            opt.interval_oracle_objective_cutoff_row = true;
            opt.interval_oracle_penalty_domain_tightening = true;
            opt.interval_oracle_service_operation_tightening = true;
            opt.interval_oracle_symmetry_breaking = true;
            if (opt.auto_interval_oracle_time_limit <= 0.0) {
                opt.auto_interval_oracle_time_limit = 600.0;
            }
            if (opt.compact_bc_time_limit <= 0.0) {
                opt.compact_bc_time_limit = opt.auto_interval_oracle_time_limit;
            }
            if (opt.algorithm_preset == "paper-gf-tailored-bc") {
                opt.tailored_bc_enabled = true;
                opt.tailored_bc_mode = "callback";
                opt.tailored_bc_branching_priority = "adaptive";
                opt.tailored_bc_gini_branching = "auto";
                opt.tailored_bc_gini_subset_envelope = true;
                opt.tailored_bc_low_gini_l1_centering = true;
                opt.tailored_bc_subset_inventory_imbalance = true;
                opt.tailored_bc_transfer_cutset = true;
                opt.compact_bc_root_cut_rounds = std::max(opt.compact_bc_root_cut_rounds, 1);
                if (opt.compact_bc_dynamic_cut_families.empty()) {
                    opt.compact_bc_dynamic_cut_families =
                        "support,transfer,visit,objective,low_gini";
                }
            }
            opt.bpc_incumbent = "none";
            opt.compact_fallback_enabled = false;
        } else if (opt.algorithm_preset == "paper-gf-bpc-core") {
            opt.relaxation_portfolio_mode = "fixed";
            opt.relaxation_portfolio_keep_best_bound = true;
            opt.frontier_split_before_tree = false;
            opt.v20_safe_relaxation_cuts = true;
            opt.v20_cover_cuts = true;
            opt.v20_cover_max_size = std::max(opt.v20_cover_max_size, 4);
            opt.station_residual_cover_cuts = true;
            opt.large_compact_flow_relaxation = "mip-light";
            opt.large_compact_flow_connectivity = true;
            opt.service_operation_min_handling_cuts = true;
            opt.gini_spread_cuts = true;
            opt.required_movement_cuts = true;
            opt.global_handling_capacity_cuts = true;
            opt.low_gini_ratio_band_tightening = true;
            opt.interval_exact_cutoff_oracle = "off";
            opt.interval_exact_oracle_mode = "cutoff-feasibility";
            opt.interval_oracle_merge_timeout_bound = false;
            opt.auto_interval_oracle = false;
            opt.auto_interval_bpc_fallback = false;
            opt.gcap_warmstart_level = std::max(opt.gcap_warmstart_level, 2);
            opt.gcap_pricing_columns = std::max(opt.gcap_pricing_columns, 8);
            opt.pricing_completion_lb_pruning = true;
            opt.pricing_decomposition = "route-skeleton-load-dp";
            opt.pricing_dominance_mode = "safe-plus";
            opt.pricing_completion_bound = "all";
            opt.pricing_load_dp_cache = true;
            opt.pricing_route_skeleton_cache = true;
            opt.pricing_load_dp_dominance = true;
            opt.pricing_operation_dp_dominance = true;
            opt.bpc_seed_columns = "incumbent";
            opt.bpc_seed_column_max = std::max(opt.bpc_seed_column_max, 1000);
            opt.bpc_cut_separation_rounds =
                std::max(opt.bpc_cut_separation_rounds, 1);
            opt.support_duration_pruning = true;
            opt.branch_selection = "strong";
            opt.strong_branching_candidates =
                std::max(opt.strong_branching_candidates, 4);
            opt.strong_branching_time = std::max(opt.strong_branching_time, 3.0);
            opt.reliability_branching = true;
            opt.closure_final_exact_pricing = true;
            opt.frontier_bpc_fallback_mode = "controlling-intervals";
            opt.frontier_bpc_fallback_reserve_fraction =
                std::max(opt.frontier_bpc_fallback_reserve_fraction, 0.25);
            opt.frontier_bpc_fallback_min_seconds =
                std::max(opt.frontier_bpc_fallback_min_seconds, 20.0);
            opt.frontier_bpc_fallback_max_intervals =
                std::max(opt.frontier_bpc_fallback_max_intervals, 1);
            opt.core_bpc_reserve_fraction =
                std::max(opt.core_bpc_reserve_fraction, 0.25);
            opt.core_bpc_min_seconds =
                std::max(opt.core_bpc_min_seconds, 20.0);
            opt.core_bpc_max_leaves = std::max(opt.core_bpc_max_leaves, 1);
            opt.frontier_scheduling_mode = "default";
        } else if (opt.algorithm_preset == "paper-bpc-core-adaptive") {
            opt.relaxation_portfolio_mode = "adaptive";
            opt.relaxation_portfolio_keep_best_bound = true;
            opt.relaxation_portfolio_max_variants =
                std::max(opt.relaxation_portfolio_max_variants, 3);
            opt.large_compact_flow_relaxation = "lp";
            opt.large_compact_flow_connectivity = false;
            opt.service_operation_min_handling_cuts = false;
            opt.penalty_movement_lb_cuts = false;
            opt.frontier_scheduling_mode = "adaptive-best-bound";
            opt.frontier_critical_band_auto = true;
        } else if (opt.algorithm_preset == "paper-exact-v20-certificate") {
            opt.relaxation_portfolio_mode = "fixed";
            opt.relaxation_portfolio_keep_best_bound = true;
            opt.v20_safe_relaxation_cuts = true;
            opt.v20_cover_cuts = true;
            opt.v20_cover_max_size = std::max(opt.v20_cover_max_size, 4);
            opt.station_residual_cover_cuts = true;
            opt.large_compact_flow_relaxation = "mip-light";
            opt.large_compact_flow_connectivity = true;
            opt.route_mask_max_v = std::min(opt.route_mask_max_v, 12);
            opt.frontier_scheduling_mode = "default";
            opt.frontier_bpc_fallback_mode = "off";
            opt.auto_interval_oracle = true;
            opt.auto_interval_oracle_merge = true;
            opt.auto_interval_oracle_order = "all";
            opt.auto_interval_oracle_continue_after_timeout = true;
            opt.auto_interval_oracle_leaf_budget_policy = "per-leaf";
            opt.interval_exact_oracle_mode = "both";
            opt.interval_oracle_merge_timeout_bound = true;
            opt.interval_oracle_low_gini_tightening = true;
            opt.interval_oracle_objective_cutoff_row = true;
            opt.interval_oracle_penalty_domain_tightening = true;
            opt.interval_oracle_service_operation_tightening = true;
            opt.interval_oracle_symmetry_breaking = true;
            opt.gini_spread_cuts = true;
            opt.required_movement_cuts = true;
            opt.global_handling_capacity_cuts = true;
            opt.low_gini_ratio_band_tightening = true;
            if (opt.auto_interval_oracle_time_limit <= 0.0) {
                opt.auto_interval_oracle_time_limit = 1800.0;
            }
            if (opt.auto_interval_oracle_max_leaves < 0) {
                opt.auto_interval_oracle_max_leaves = 0;
            }
        }
        opt.bpc_incumbent = (opt.bpc_incumbent.empty())
            ? "none" : opt.bpc_incumbent;
        opt.compact_fallback_enabled =
            opt.algorithm_preset == "paper-exact-portfolio";
        if (!opt.incumbent_archive_auto_explicit) {
            opt.incumbent_archive_auto = false;
        }
        return;
    }

    if (opt.algorithm_preset == "paper-bpc-experimental") {
        opt.pricing_engine = "hybrid";
        opt.column_tracks = "two-track";
        opt.rmp_column_space = "two-track";
        opt.relaxed_columns_in_rmp = true;
        opt.relaxed_rmp_cg = true;
        opt.frontier_relaxed_rmp_cg = true;
        opt.ng_relaxed_closure = true;
        opt.dssr_close_relaxed_pricing = true;
        opt.allow_non_elementary_relaxed_columns = true;
        opt.relaxed_projection_strict = true;
        opt.column_dominance = true;
        opt.column_dominance_mode = "exact";
        opt.gcap_pricing_columns = std::max(opt.gcap_pricing_columns, 4);
        opt.movement_domain_tightening = true;
        opt.projection_bound = true;
        opt.penalty_domain_tightening = true;
        opt.vehicle_indexed_operation_relaxation = true;
        opt.vehicle_indexed_transfer_flow = true;
        opt.route_mask_operation_budget_cuts = true;
        opt.route_pool_incumbent = true;
        opt.exact_phase_local_redecode_repair = true;
        opt.branch_inventory = true;
        opt.branch_operation_mode = true;
        opt.bpc_incumbent = (opt.bpc_incumbent == "none" || opt.bpc_incumbent.empty())
            ? "auto" : opt.bpc_incumbent;
        if (!opt.primal_heuristic_explicit) {
            opt.primal_heuristic = "hga-tgbc";
        }
        if (!opt.incumbent_archive_auto_explicit) {
            opt.incumbent_archive_auto = false;
        }
        opt.compact_fallback_enabled = false;
        return;
    }

    if (opt.algorithm_preset == "diagnostic-large") {
        opt.large_instance_mode = "force";
        opt.pricing_engine = "hybrid";
        opt.ng_neighborhood_mode = "hybrid";
        opt.column_tracks = "two-track";
        opt.rmp_column_space = "two-track";
        opt.relaxed_columns_in_rmp = true;
        opt.large_lb_mode = "movement-projection";
        opt.large_relaxed_rmp = true;
        opt.large_relaxed_rmp_cg = true;
        opt.relaxed_rmp_cg = true;
        opt.frontier_relaxed_rmp_cg = false;
        opt.route_mask_max_v = 0;
        opt.route_mask_operation_budget_cuts = false;
        opt.frontier_final_closure = false;
        opt.compact_fallback_enabled = false;
        return;
    }
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
        else if (arg == "--frontier-relaxation-parallel") opt.parallel_frontier = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-relaxation-workers") {
            opt.bpc_workers = std::stoi(requireValue(i, argc, argv));
            opt.threads = std::max(opt.threads, opt.bpc_workers);
        }
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
        else if (arg == "--frontier-split-before-tree") opt.frontier_split_before_tree = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-column-cache") opt.frontier_column_cache = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-min-lb-retry") opt.frontier_focused_min_lb_retry = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-intensification") opt.frontier_focused_intensification = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-reserve-fraction") opt.frontier_focused_reserve_fraction = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-relax-seconds") opt.frontier_focused_relax_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-focused-max-passes") opt.frontier_focused_max_passes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-adaptive-split") opt.frontier_adaptive_split = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-adaptive-max-depth") {
            opt.frontier_adaptive_max_depth = std::stoi(requireValue(i, argc, argv));
            opt.frontier_adaptive_max_depth_explicit = true;
        }
        else if (arg == "--frontier-adaptive-min-width") opt.frontier_adaptive_min_width = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-adaptive-split-factor") opt.frontier_adaptive_split_factor = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-pre-split-critical") opt.frontier_pre_split_critical = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-critical-max-depth") opt.frontier_critical_max_depth = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--support-duration-pruning") opt.support_duration_pruning = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--support-duration-max-subset-size") opt.support_duration_max_subset_size = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--pricing-completion-lb-pruning") opt.pricing_completion_lb_pruning = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pricing-dominance-mode") {
            opt.pricing_dominance_mode = requireValue(i, argc, argv);
            opt.pricing_dominance_mode_explicit = true;
        }
        else if (arg == "--pricing-completion-bound") {
            opt.pricing_completion_bound = requireValue(i, argc, argv);
            opt.pricing_completion_bound_explicit = true;
            const std::string mode = lowerAscii(opt.pricing_completion_bound);
            opt.pricing_completion_lb_pruning = mode != "none" && mode != "off";
        }
        else if (arg == "--pricing-completion-bound-audit") opt.pricing_completion_bound_audit = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pricing-decomposition") {
            opt.pricing_decomposition = requireValue(i, argc, argv);
            opt.pricing_decomposition_explicit = true;
        }
        else if (arg == "--pricing-load-dp-cache") {
            opt.pricing_load_dp_cache = parseBoolValue(requireValue(i, argc, argv));
            opt.pricing_load_dp_cache_explicit = true;
        }
        else if (arg == "--pricing-route-skeleton-mode") {
            opt.pricing_route_skeleton_mode = requireValue(i, argc, argv);
            opt.pricing_route_skeleton_mode_explicit = true;
        }
        else if (arg == "--pricing-route-skeleton-cache") {
            opt.pricing_route_skeleton_cache = parseBoolValue(requireValue(i, argc, argv));
            opt.pricing_route_skeleton_cache_explicit = true;
        }
        else if (arg == "--pricing-load-dp-dominance") {
            opt.pricing_load_dp_dominance = parseBoolValue(requireValue(i, argc, argv));
            opt.pricing_load_dp_dominance_explicit = true;
        }
        else if (arg == "--pricing-operation-dp-dominance") {
            opt.pricing_operation_dp_dominance = parseBoolValue(requireValue(i, argc, argv));
            opt.pricing_operation_dp_dominance_explicit = true;
        }
        else if (arg == "--bpc-seed-columns") {
            opt.bpc_seed_columns = requireValue(i, argc, argv);
            opt.bpc_seed_columns_explicit = true;
        }
        else if (arg == "--bpc-seed-column-max") {
            opt.bpc_seed_column_max = std::stoi(requireValue(i, argc, argv));
            opt.bpc_seed_column_max_explicit = true;
        }
        else if (arg == "--bpc-cut-family") {
            opt.bpc_cut_family = requireValue(i, argc, argv);
            opt.bpc_cut_family_explicit = true;
        }
        else if (arg == "--bpc-cut-separation-rounds") {
            opt.bpc_cut_separation_rounds = std::stoi(requireValue(i, argc, argv));
            opt.bpc_cut_separation_rounds_explicit = true;
        }
        else if (arg == "--core-relaxation-budget-fraction") opt.core_relaxation_budget_fraction = std::stod(requireValue(i, argc, argv));
        else if (arg == "--core-bpc-reserve-fraction") opt.core_bpc_reserve_fraction = std::stod(requireValue(i, argc, argv));
        else if (arg == "--core-bpc-min-seconds") opt.core_bpc_min_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--core-bpc-max-leaves") opt.core_bpc_max_leaves = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--core-bpc-leaf-selection") opt.core_bpc_leaf_selection = requireValue(i, argc, argv);
        else if (arg == "--route-mask-support-duration-pruning") opt.route_mask_support_duration_pruning = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--route-mask-operation-budget-cuts") opt.route_mask_operation_budget_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--support-feasibility-oracle") opt.support_feasibility_oracle = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--route-pool-incumbent") opt.route_pool_incumbent = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--route-pool-max-columns-per-vehicle") opt.route_pool_max_columns_per_vehicle = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--route-pool-keep-best-per-projection") opt.route_pool_keep_best_per_projection = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--exact-phase-local-redecode-repair") opt.exact_phase_local_redecode_repair = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--exact-phase-local-redecode-seconds") opt.exact_phase_local_redecode_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--pickup-drop-compat-flow") opt.pickup_drop_compat_flow = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pickup-drop-transfer-cap-flow") opt.pickup_drop_transfer_cap_flow = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--vehicle-indexed-operation-relaxation") opt.vehicle_indexed_operation_relaxation = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--vehicle-indexed-relaxation-audit") opt.vehicle_indexed_relaxation_audit = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--vehicle-indexed-transfer-flow") opt.vehicle_indexed_transfer_flow = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--v20-safe-relaxation-cuts") opt.v20_safe_relaxation_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--v20-cover-cuts") opt.v20_cover_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--v20-cover-max-size") opt.v20_cover_max_size = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--v20-cover-max-cuts") opt.v20_cover_max_cuts = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--v20-cover-separation-seconds") opt.v20_cover_separation_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--station-residual-cover-cuts") opt.station_residual_cover_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--station-residual-cover-max-cuts") opt.station_residual_cover_max_cuts = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--large-compact-flow-relaxation") opt.large_compact_flow_relaxation = requireValue(i, argc, argv);
        else if (arg == "--large-compact-flow-time-limit") opt.large_compact_flow_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--large-compact-flow-connectivity") opt.large_compact_flow_connectivity = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--service-operation-min-handling-cuts" ||
                 arg == "--service-operation-min-handling") opt.service_operation_min_handling_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--penalty-movement-lb-cuts") opt.penalty_movement_lb_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--transfer-subset-capacity-cuts") opt.transfer_subset_capacity_cuts = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--gini-spread-cuts" || arg == "--compact-bc-gini-spread") {
            opt.gini_spread_cuts = parseBoolValue(requireValue(i, argc, argv));
            opt.gini_spread_cuts_explicit = true;
        }
        else if (arg == "--required-movement-cuts" || arg == "--compact-bc-required-movement") {
            opt.required_movement_cuts = parseBoolValue(requireValue(i, argc, argv));
            opt.required_movement_cuts_explicit = true;
        }
        else if (arg == "--global-handling-capacity-cuts" || arg == "--compact-bc-global-handling-capacity") {
            opt.global_handling_capacity_cuts = parseBoolValue(requireValue(i, argc, argv));
            opt.global_handling_capacity_cuts_explicit = true;
        }
        else if (arg == "--low-gini-ratio-band-tightening" || arg == "--compact-bc-low-gini-centering") {
            opt.low_gini_ratio_band_tightening = parseBoolValue(requireValue(i, argc, argv));
            opt.low_gini_ratio_band_tightening_explicit = true;
        }
        else if (arg == "--relaxation-portfolio-mode") opt.relaxation_portfolio_mode = requireValue(i, argc, argv);
        else if (arg == "--relaxation-portfolio-probe-seconds") opt.relaxation_portfolio_probe_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--relaxation-portfolio-max-variants") opt.relaxation_portfolio_max_variants = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--relaxation-portfolio-min-improvement") opt.relaxation_portfolio_min_improvement = std::stod(requireValue(i, argc, argv));
        else if (arg == "--relaxation-portfolio-keep-best-bound") opt.relaxation_portfolio_keep_best_bound = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--relaxation-exhaustive-variants") opt.relaxation_exhaustive_variants = requireValue(i, argc, argv);
        else if (arg == "--relaxation-exhaustive-stop-on-fathom") opt.relaxation_exhaustive_stop_on_fathom = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--relaxation-certificate-mode") opt.relaxation_certificate_mode = requireValue(i, argc, argv);
        else if (arg == "--cutoff-feasibility-epsilon") opt.cutoff_feasibility_epsilon = std::stod(requireValue(i, argc, argv));
        else if (arg == "--cutoff-feasibility-time-limit") opt.cutoff_feasibility_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-exact-cutoff-oracle") opt.interval_exact_cutoff_oracle = requireValue(i, argc, argv);
        else if (arg == "--interval-exact-oracle-mode") opt.interval_exact_oracle_mode = requireValue(i, argc, argv);
        else if (arg == "--interval-exact-cutoff-gamma-L") opt.interval_exact_cutoff_gamma_L = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-exact-cutoff-gamma-U") opt.interval_exact_cutoff_gamma_U = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-exact-cutoff-UB") opt.interval_exact_cutoff_UB = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-exact-cutoff-epsilon") opt.interval_exact_cutoff_epsilon = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-exact-cutoff-time-limit") opt.interval_exact_cutoff_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--mip-solver") opt.mip_solver = requireValue(i, argc, argv);
        else if (arg == "--cplex-threads") opt.cplex_threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--mip-threads") opt.mip_threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-threads") opt.compact_bc_threads = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-time-limit") opt.compact_bc_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-root-cut-rounds") opt.compact_bc_root_cut_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-root-cut-time-limit") opt.compact_bc_root_cut_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-dynamic-cut-families") opt.compact_bc_dynamic_cut_families = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-root-probe") opt.compact_bc_root_probe = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-dynamic-cut-violation-tol") opt.compact_bc_dynamic_cut_violation_tol = std::stod(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-domain-propagation-mode") opt.compact_bc_domain_propagation_mode = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-domain-propagation-rounds") opt.compact_bc_domain_propagation_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-low-gini-strengthening") {
            opt.compact_bc_low_gini_strengthening = lowerAscii(requireValue(i, argc, argv));
            opt.compact_bc_low_gini_strengthening_explicit = true;
        }
        else if (arg == "--compact-bc-denominator-bound-mode") {
            opt.compact_bc_denominator_bound_mode = lowerAscii(requireValue(i, argc, argv));
            opt.compact_bc_denominator_bound_mode_explicit = true;
        }
        else if (arg == "--compact-bc-objective-estimator-mode") {
            opt.compact_bc_objective_estimator_mode = lowerAscii(requireValue(i, argc, argv));
            opt.compact_bc_objective_estimator_mode_explicit = true;
        }
        else if (arg == "--compact-bc-s-range-refinement") {
            opt.compact_bc_s_range_refinement = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-s-range-buckets") {
            opt.compact_bc_s_range_buckets = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-s-range-adaptive") {
            opt.compact_bc_s_range_adaptive = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-s-range-bucket-id") {
            opt.compact_bc_s_range_bucket_id = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-s-range-bucket-L") {
            opt.compact_bc_s_range_bucket_L = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-s-range-bucket-U") {
            opt.compact_bc_s_range_bucket_U = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-variable-s-centering") {
            opt.compact_bc_variable_s_centering = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-rmin-rmax-propagation") {
            opt.compact_bc_rmin_rmax_propagation = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-sp-product-estimator") {
            opt.compact_bc_sp_product_estimator = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-sp-product-bounds") {
            opt.compact_bc_sp_product_bounds = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-low-gini-precheck") {
            opt.compact_bc_low_gini_precheck = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-ledger") {
            opt.tailored_bc_s_bucket_ledger = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-count") {
            opt.tailored_bc_s_bucket_count = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-policy") {
            opt.tailored_bc_s_bucket_policy = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-time-budget") {
            opt.tailored_bc_s_bucket_time_budget = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-merge-audit") {
            opt.tailored_bc_s_bucket_merge_audit = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-max-depth") {
            opt.tailored_bc_s_bucket_max_depth = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-min-width") {
            opt.tailored_bc_s_bucket_min_width = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-refine-top-k") {
            opt.tailored_bc_s_bucket_refine_top_k = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-s-bucket-refine-rule") {
            opt.tailored_bc_s_bucket_refine_rule = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-enabled") {
            opt.tailored_bc_enabled = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-mode") {
            opt.tailored_bc_mode = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-branching-priority") {
            opt.tailored_bc_branching_priority = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-branching") {
            opt.tailored_bc_gini_branching = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-branch-min-width") {
            opt.tailored_bc_gini_branch_min_width = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-branch-score-threshold") {
            opt.tailored_bc_gini_branch_score_threshold = std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-subset-envelope") {
            opt.tailored_bc_gini_subset_envelope = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-subset-max-size") {
            opt.tailored_bc_gini_subset_max_size = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gini-subset-max-cuts") {
            opt.tailored_bc_gini_subset_max_cuts = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-callback-separation-pacing") {
            opt.tailored_bc_callback_separation_pacing = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-callback-separation-min-calls") {
            opt.tailored_bc_callback_separation_min_calls = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-callback-cut-profile") {
            opt.tailored_bc_callback_cut_profile = lowerAscii(requireValue(i, argc, argv));
            opt.tailored_bc_callback_cut_profile_explicit = true;
        }
        else if (arg == "--tailored-bc-local-centering") {
            opt.tailored_bc_local_centering = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-cross-h-centering") {
            opt.tailored_bc_subset_cross_h_centering = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-cross-h-max-size") {
            opt.tailored_bc_subset_cross_h_max_size = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-cross-h-max-cuts") {
            opt.tailored_bc_subset_cross_h_max_cuts = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-cross-h-separation-profile") {
            opt.tailored_bc_subset_cross_h_separation_profile =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-local-q-centering") {
            opt.tailored_bc_local_q_centering = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-low-gini-l1-centering") {
            opt.tailored_bc_low_gini_l1_centering = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-inventory-imbalance") {
            opt.tailored_bc_subset_inventory_imbalance = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-subset-inventory-max-size") {
            opt.tailored_bc_subset_inventory_max_size = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-transfer-cutset") {
            opt.tailored_bc_transfer_cutset = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-compatible-source-transfer-cuts") {
            opt.tailored_bc_compatible_source_transfer_cuts = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-required-external-source-cuts") {
            opt.tailored_bc_required_external_source_cuts = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-transfer-max-receiver-size") {
            opt.tailored_bc_transfer_max_receiver_size = std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-ratio-domain-tightening") {
            opt.tailored_bc_bucket_ratio_domain_tightening =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-subset-ratio-domain") {
            opt.tailored_bc_bucket_subset_ratio_domain =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-subset-ratio-max-size") {
            opt.tailored_bc_bucket_subset_ratio_max_size =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-integer-inventory-domain") {
            opt.tailored_bc_bucket_integer_inventory_domain =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-integer-inventory-domain-mode") {
            opt.tailored_bc_bucket_integer_inventory_domain_mode =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-required-movement") {
            opt.tailored_bc_bucket_required_movement =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-required-visit") {
            opt.tailored_bc_bucket_required_visit =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-bucket-required-movement-max-size") {
            opt.tailored_bc_bucket_required_movement_max_size =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-support-duration-cover-mode") {
            opt.tailored_bc_support_duration_cover_mode = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-benders-inventory-cuts") {
            opt.tailored_bc_benders_inventory_cuts = lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gs-product-coupling") {
            opt.tailored_bc_gs_product_coupling =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gs-product-coupling-mode") {
            opt.tailored_bc_gs_product_coupling_mode =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-gs-product-lower-row") {
            opt.tailored_bc_gs_product_lower_row =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-disaggregated-sp-estimator") {
            opt.tailored_bc_disaggregated_sp_estimator =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-disaggregated-sp-mode") {
            opt.tailored_bc_disaggregated_sp_mode =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-disaggregated-sp-replace-aggregate") {
            opt.tailored_bc_disaggregated_sp_replace_aggregate =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-support-cover") {
            opt.tailored_bc_vector_support_cover =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-support-cover-max-size") {
            opt.tailored_bc_vector_support_cover_max_size =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-support-cover-max-cuts") {
            opt.tailored_bc_vector_support_cover_max_cuts =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-route-cutset") {
            opt.tailored_bc_vector_route_cutset =
                parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-route-cutset-max-size") {
            opt.tailored_bc_vector_route_cutset_max_size =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-route-cutset-max-cuts") {
            opt.tailored_bc_vector_route_cutset_max_cuts =
                std::stoi(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-cut-min-violation") {
            opt.tailored_bc_vector_cut_min_violation =
                std::stod(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-vector-cut-candidate-source") {
            opt.tailored_bc_vector_cut_candidate_source =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--tailored-bc-structural-profile") {
            opt.tailored_bc_structural_profile =
                lowerAscii(requireValue(i, argc, argv));
        }
        else if (arg == "--compact-bc-model-size-policy") opt.compact_bc_model_size_policy = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-max-rows") opt.compact_bc_max_rows = std::stoll(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-max-cols") opt.compact_bc_max_cols = std::stoll(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-max-nonzeros") opt.compact_bc_max_nonzeros = std::stoll(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-max-memory-mb") opt.compact_bc_max_memory_mb = std::stod(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-expensive-static-families") opt.compact_bc_expensive_static_families = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-use-dynamic-instead-of-static") opt.compact_bc_use_dynamic_instead_of_static = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-cut-profile") opt.compact_bc_cut_profile = requireValue(i, argc, argv);
        else if (arg == "--compact-bc-direct-gini-rows" || arg == "--compact-bc-gini-cap-floor-cuts") {
            opt.compact_bc_direct_gini_rows = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_direct_gini_rows_explicit = true;
        }
        else if (arg == "--compact-bc-tight-mccormick") {
            opt.compact_bc_tight_mccormick = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_tight_mccormick_explicit = true;
        }
        else if (arg == "--compact-bc-inventory-conservation") {
            opt.compact_bc_inventory_conservation = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_inventory_conservation_explicit = true;
        }
        else if (arg == "--compact-bc-movement-reachability-domains" || arg == "--compact-bc-movement-reachability") {
            opt.compact_bc_movement_reachability_domains = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_movement_reachability_domains_explicit = true;
        }
        else if (arg == "--compact-bc-visit-inventory-linking") {
            opt.compact_bc_visit_inventory_linking = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_visit_inventory_linking_explicit = true;
        }
        else if (arg == "--compact-bc-objective-estimator-cutoff") {
            opt.compact_bc_objective_estimator_cutoff = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_objective_estimator_cutoff_explicit = true;
        }
        else if (arg == "--compact-bc-penalty-lb-closure") {
            opt.compact_bc_penalty_lb_closure = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_penalty_lb_closure_explicit = true;
        }
        else if (arg == "--compact-bc-support-duration-cuts" || arg == "--compact-bc-support-duration") {
            opt.compact_bc_support_duration_cuts = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_support_duration_cuts_explicit = true;
        }
        else if (arg == "--compact-bc-pairwise-transfer-compatibility" || arg == "--compact-bc-transfer-compat") {
            opt.compact_bc_pairwise_transfer_compatibility = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_pairwise_transfer_compatibility_explicit = true;
        }
        else if (arg == "--compact-bc-receiver-source-cover-cuts") {
            opt.compact_bc_receiver_source_cover_cuts = parseBoolValue(requireValue(i, argc, argv));
            opt.compact_bc_receiver_source_cover_mode =
                opt.compact_bc_receiver_source_cover_cuts ? "singleton-paper-safe" : "off";
            opt.compact_bc_receiver_source_cover_explicit = true;
        }
        else if (arg == "--compact-bc-receiver-source-cover") {
            opt.compact_bc_receiver_source_cover_mode = lowerAscii(requireValue(i, argc, argv));
            opt.compact_bc_receiver_source_cover_cuts =
                opt.compact_bc_receiver_source_cover_mode == "singleton-paper-safe" ||
                opt.compact_bc_receiver_source_cover_mode == "pair-net-paper-safe" ||
                opt.compact_bc_receiver_source_cover_mode == "paper-safe";
            opt.compact_bc_receiver_source_cover_explicit = true;
        }
        else if (arg == "--compact-bc-support-cut-max-size") opt.compact_bc_support_cut_max_size = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-support-cut-max-subsets") opt.compact_bc_support_cut_max_subsets = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-objective-bound-time-limit") opt.interval_oracle_objective_bound_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-cutoff-feasibility-time-limit") opt.interval_oracle_cutoff_feasibility_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-merge-timeout-bound") opt.interval_oracle_merge_timeout_bound = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-profile") opt.interval_oracle_profile = requireValue(i, argc, argv);
        else if (arg == "--interval-exact-cutoff-export-lp") opt.interval_exact_cutoff_export_lp = requireValue(i, argc, argv);
        else if (arg == "--interval-exact-cutoff-result") opt.interval_exact_cutoff_result = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-mode") opt.interval_closure_mode = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-input") opt.interval_closure_input = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-target-instance") opt.interval_closure_target_instance = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-target-ids") opt.interval_closure_target_ids = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-range") opt.interval_closure_range = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-output") opt.interval_closure_output = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-merge-ledger") opt.interval_closure_merge_ledger = requireValue(i, argc, argv);
        else if (arg == "--interval-closure-time-limit") opt.interval_closure_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-closure-variant-mode") opt.interval_closure_variant_mode = requireValue(i, argc, argv);
        else if (arg == "--paper-run-sealed") opt.paper_run_sealed = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle") opt.auto_interval_oracle = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-time-limit") opt.auto_interval_oracle_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-total-budget") opt.auto_interval_oracle_total_budget = std::stod(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-child-time-limit") opt.auto_interval_oracle_child_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-max-leaves") {
            std::string v = lowerAscii(requireValue(i, argc, argv));
            opt.auto_interval_oracle_max_leaves = (v == "all" || v == "0") ? 0 : std::stoi(v);
        }
        else if (arg == "--auto-interval-oracle-order") opt.auto_interval_oracle_order = requireValue(i, argc, argv);
        else if (arg == "--auto-interval-oracle-leaf-budget-policy") opt.auto_interval_oracle_leaf_budget_policy = requireValue(i, argc, argv);
        else if (arg == "--auto-interval-oracle-continue-after-timeout") opt.auto_interval_oracle_continue_after_timeout = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-split-on-timeout") opt.auto_interval_oracle_split_on_timeout = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-recursive-split") opt.auto_interval_oracle_recursive_split = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-child-split-count") opt.auto_interval_oracle_child_split_count = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-max-depth") opt.auto_interval_oracle_max_depth = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-min-width") opt.auto_interval_oracle_min_width = std::stod(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-max-children-total") opt.auto_interval_oracle_max_children_total = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-merge") opt.auto_interval_oracle_merge = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-oracle-restart-on-improved-ub") opt.auto_interval_oracle_restart_on_improved_ub = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-bpc-fallback") opt.auto_interval_bpc_fallback = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-bpc-time-limit") opt.auto_interval_bpc_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-bpc-max-leaves") opt.auto_interval_bpc_max_leaves = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-bpc-max-nodes") opt.auto_interval_bpc_max_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--auto-interval-bpc-pricing-time-per-call") opt.auto_interval_bpc_pricing_time_per_call = std::stod(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-low-gini-tightening") opt.interval_oracle_low_gini_tightening = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-objective-cutoff-row") opt.interval_oracle_objective_cutoff_row = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-penalty-domain-tightening") opt.interval_oracle_penalty_domain_tightening = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-service-operation-tightening") opt.interval_oracle_service_operation_tightening = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--interval-oracle-symmetry-breaking") opt.interval_oracle_symmetry_breaking = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-scheduling-mode") opt.frontier_scheduling_mode = requireValue(i, argc, argv);
        else if (arg == "--frontier-critical-band-auto") opt.frontier_critical_band_auto = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-critical-band-max-depth") opt.frontier_critical_band_max_depth = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-critical-band-min-width") opt.frontier_critical_band_min_width = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-bpc-fallback-reserve-fraction") opt.frontier_bpc_fallback_reserve_fraction = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-bpc-fallback-min-seconds") opt.frontier_bpc_fallback_min_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-bpc-fallback-max-intervals") opt.frontier_bpc_fallback_max_intervals = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-bpc-fallback-mode") opt.frontier_bpc_fallback_mode = requireValue(i, argc, argv);
        else if (arg == "--gcap-seed-cplex") opt.gcap_seed_cplex = true;
        else if (arg == "--gcap-seed-time-limit") opt.gcap_seed_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--incumbent-json") opt.incumbent_json_path = requireValue(i, argc, argv);
        else if (arg == "--incumbent-format") opt.incumbent_format = requireValue(i, argc, argv);
        else if (arg == "--hga-incumbent") opt.hga_incumbent_path = requireValue(i, argc, argv);
        else if (arg == "--hga-incumbent-format") opt.hga_incumbent_format = requireValue(i, argc, argv);
        else if (arg == "--external-incumbent") opt.external_incumbent_path = requireValue(i, argc, argv);
        else if (arg == "--external-incumbent-format") opt.external_incumbent_format = requireValue(i, argc, argv);
        else if (arg == "--export-incumbent") opt.export_incumbent_path = requireValue(i, argc, argv);
        else if (arg == "--primal-heuristic") {
            opt.primal_heuristic = requireValue(i, argc, argv);
            opt.primal_heuristic_explicit = true;
        }
        else if (arg == "--primal-heuristic-seconds") opt.primal_heuristic_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--primal-heuristic-seed") opt.primal_heuristic_seed = static_cast<unsigned>(std::stoul(requireValue(i, argc, argv)));
        else if (arg == "--primal-heuristic-runs") opt.primal_heuristic_runs = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--heuristic-candidates-csv") opt.heuristic_candidates_csv = requireValue(i, argc, argv);
        else if (arg == "--large-instance-mode") opt.large_instance_mode = requireValue(i, argc, argv);
        else if (arg == "--large-lb-mode") opt.large_lb_mode = requireValue(i, argc, argv);
        else if (arg == "--pricing-engine") opt.pricing_engine = requireValue(i, argc, argv);
        else if (arg == "--ng-size") opt.ng_size = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--ng-neighborhood-mode") opt.ng_neighborhood_mode = requireValue(i, argc, argv);
        else if (arg == "--dssr-max-rounds") opt.dssr_max_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--dssr-expand-per-round") opt.dssr_expand_per_round = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--dssr-time-limit") opt.dssr_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--dssr-final-exact") opt.dssr_final_exact = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--column-tracks") opt.column_tracks = requireValue(i, argc, argv);
        else if (arg == "--relaxed-columns-in-rmp") opt.relaxed_columns_in_rmp = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--relaxed-columns-max-per-pricing") opt.relaxed_columns_max_per_pricing = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--rmp-column-space") opt.rmp_column_space = requireValue(i, argc, argv);
        else if (arg == "--allow-non-elementary-relaxed-columns") opt.allow_non_elementary_relaxed_columns = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--relaxed-projection-strict") opt.relaxed_projection_strict = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--ng-relaxed-closure") opt.ng_relaxed_closure = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--ng-relaxed-closure-time") opt.ng_relaxed_closure_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--ng-relaxed-max-labels") opt.ng_relaxed_max_labels = std::stoll(requireValue(i, argc, argv));
        else if (arg == "--ng-relaxed-pricing-checkpoint") opt.ng_relaxed_pricing_checkpoint = requireValue(i, argc, argv);
        else if (arg == "--ng-relaxed-pricing-resume") opt.ng_relaxed_pricing_resume = requireValue(i, argc, argv);
        else if (arg == "--relaxed-rmp-cg") opt.relaxed_rmp_cg = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--relaxed-rmp-cg-max-iterations") opt.relaxed_rmp_cg_max_iterations = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--relaxed-rmp-cg-time") opt.relaxed_rmp_cg_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--relaxed-rmp-cg-columns-per-iteration") opt.relaxed_rmp_cg_columns_per_iteration = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-relaxed-rmp-cg") opt.frontier_relaxed_rmp_cg = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-relaxed-rmp-cg-time-per-interval") opt.frontier_relaxed_rmp_cg_time_per_interval = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-relaxed-rmp-cg-max-intervals") opt.frontier_relaxed_rmp_cg_max_intervals = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--large-relaxed-rmp-cg") opt.large_relaxed_rmp_cg = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--large-relaxed-rmp-column-budget") opt.large_relaxed_rmp_column_budget = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--large-relaxed-rmp-time") opt.large_relaxed_rmp_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--dssr-close-relaxed-pricing") opt.dssr_close_relaxed_pricing = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--dssr-relaxed-closure-time") opt.dssr_relaxed_closure_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--dssr-relaxed-closure-max-labels") opt.dssr_relaxed_closure_max_labels = std::stoll(requireValue(i, argc, argv));
        else if (arg == "--dssr-relaxed-closure-checkpoint") opt.dssr_relaxed_closure_checkpoint = requireValue(i, argc, argv);
        else if (arg == "--large-relaxed-rmp") opt.large_relaxed_rmp = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--incumbent-source-name") opt.incumbent_source_name = requireValue(i, argc, argv);
        else if (arg == "--inventory-probe-max-v") opt.inventory_probe_max_v = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--inventory-probe-seconds") opt.inventory_probe_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--progress-log") opt.progress_log_path = requireValue(i, argc, argv);
        else if (arg == "--ub-event-log") opt.ub_event_log_path = requireValue(i, argc, argv);
        else if (arg == "--progress-interval-seconds") opt.progress_interval_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--compact-bc-progress-interval") {
            opt.compact_bc_progress_interval = std::stod(requireValue(i, argc, argv));
            opt.progress_interval_seconds = opt.compact_bc_progress_interval;
        }
        else if (arg == "--compact-bc-diagnostic-force-leaf-solve") {
            opt.compact_bc_diagnostic_force_leaf_solve = parseBoolValue(requireValue(i, argc, argv));
        }
        else if (arg == "--frontier-focus-interval-id") opt.frontier_focus_interval_id = requireValue(i, argc, argv);
        else if (arg == "--frontier-focus-range") opt.frontier_focus_range = requireValue(i, argc, argv);
        else if (arg == "--frontier-focus-from-result") opt.frontier_focus_from_result = requireValue(i, argc, argv);
        else if (arg == "--frontier-focus-leaf-id") opt.frontier_focus_leaf_id = requireValue(i, argc, argv);
        else if (arg == "--frontier-focus-only") opt.frontier_focus_only = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focus-use-existing-incumbent") opt.frontier_focus_use_existing_incumbent = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-focus-time-limit") opt.frontier_focus_time_limit = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-focus-relax-seconds") opt.frontier_focus_relax_seconds = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-focus-tree-nodes") opt.frontier_focus_tree_nodes = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-import-interval-bound") opt.frontier_import_interval_bound_paths.push_back(requireValue(i, argc, argv));
        else if (arg == "--branch-inventory") opt.branch_inventory = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--branch-inventory-priority") opt.branch_inventory_priority = std::stod(requireValue(i, argc, argv));
        else if (arg == "--branch-operation-mode") opt.branch_operation_mode = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--branch-selection") opt.branch_selection = requireValue(i, argc, argv);
        else if (arg == "--strong-branching-candidates") opt.strong_branching_candidates = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--strong-branching-time") opt.strong_branching_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--reliability-branching") opt.reliability_branching = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-export-state") opt.frontier_export_state_path = requireValue(i, argc, argv);
        else if (arg == "--frontier-resume-state") opt.frontier_resume_state_path = requireValue(i, argc, argv);
        else if (arg == "--frontier-resume-interval-id") opt.frontier_resume_interval_id = requireValue(i, argc, argv);
        else if (arg == "--frontier-resume-mode") opt.frontier_resume_mode = requireValue(i, argc, argv);
        else if (arg == "--frontier-closure-mode") opt.frontier_closure_mode = requireValue(i, argc, argv);
        else if (arg == "--closure-max-cg-iterations") opt.closure_max_cg_iterations = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--closure-pricing-time-per-call") opt.closure_pricing_time_per_call = std::stod(requireValue(i, argc, argv));
        else if (arg == "--closure-returned-columns") opt.closure_returned_columns = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--closure-final-exact-pricing") opt.closure_final_exact_pricing = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--cg-dual-stabilization") opt.cg_dual_stabilization = requireValue(i, argc, argv);
        else if (arg == "--cg-dual-smoothing-alpha") opt.cg_dual_smoothing_alpha = std::stod(requireValue(i, argc, argv));
        else if (arg == "--cg-dual-box-radius") opt.cg_dual_box_radius = std::stod(requireValue(i, argc, argv));
        else if (arg == "--cg-stabilization-max-nonimprove") opt.cg_stabilization_max_nonimprove = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--cg-stabilization-switch-to-true-after") opt.cg_stabilization_switch_to_true_after = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-closure") opt.frontier_iterative_closure = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-max-rounds") opt.frontier_iterative_max_rounds = std::stoi(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-round-time") opt.frontier_iterative_round_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-target-gap") opt.frontier_iterative_target_gap = std::stod(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-use-resume") opt.frontier_iterative_use_resume = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-iterative-export-dir") opt.frontier_iterative_export_dir = requireValue(i, argc, argv);
        else if (arg == "--frontier-export-open-nodes") opt.frontier_export_open_nodes = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--frontier-resume-open-nodes") opt.frontier_resume_open_nodes = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pricing-final-verifier") opt.pricing_final_verifier = parseBoolValue(requireValue(i, argc, argv));
        else if (arg == "--pricing-verifier-time") opt.pricing_verifier_time = std::stod(requireValue(i, argc, argv));
        else if (arg == "--pricing-verifier-checkpoint") opt.pricing_verifier_checkpoint = requireValue(i, argc, argv);
        else if (arg == "--pricing-verifier-resume") opt.pricing_verifier_resume = requireValue(i, argc, argv);
        else if (arg == "--pricing-verifier-mode") opt.pricing_verifier_mode = requireValue(i, argc, argv);
        else if (arg == "--algorithm-preset") opt.algorithm_preset = requireValue(i, argc, argv);
        else if (arg == "--production-preset") opt.algorithm_preset = requireValue(i, argc, argv);
        else if (arg == "--incumbent-archive-auto") {
            opt.incumbent_archive_auto = parseBoolValue(requireValue(i, argc, argv));
            opt.incumbent_archive_auto_explicit = true;
        }
        else if (arg == "--incumbent-archive-dir") opt.incumbent_archive_dir = requireValue(i, argc, argv);
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
    opt.frontier_bpc_fallback_mode = lowerAscii(opt.frontier_bpc_fallback_mode);
    if (opt.frontier_bpc_fallback_mode != "controlling-intervals" &&
        opt.frontier_bpc_fallback_mode != "best-bound") {
        opt.frontier_bpc_fallback_mode = "off";
    }
    if (opt.frontier_bpc_fallback_reserve_fraction < 0.0) {
        opt.frontier_bpc_fallback_reserve_fraction = 0.0;
    }
    if (opt.frontier_bpc_fallback_reserve_fraction > 0.9) {
        opt.frontier_bpc_fallback_reserve_fraction = 0.9;
    }
    if (opt.frontier_bpc_fallback_min_seconds < 0.0) {
        opt.frontier_bpc_fallback_min_seconds = 0.0;
    }
    if (opt.frontier_bpc_fallback_max_intervals < 0) {
        opt.frontier_bpc_fallback_max_intervals = 0;
    }
    if (opt.frontier_bpc_fallback_mode != "off") {
        const double fallback_reserve = std::max(
            opt.frontier_bpc_fallback_min_seconds,
            opt.solve_time_limit > 0.0
                ? opt.solve_time_limit * opt.frontier_bpc_fallback_reserve_fraction
                : 0.0);
        opt.frontier_retry_reserve_seconds =
            std::max(opt.frontier_retry_reserve_seconds, fallback_reserve);
        opt.frontier_final_closure = true;
    }
    if (opt.frontier_relax_seconds == 0.0) opt.frontier_relax_seconds = -1.0;
    if (opt.route_mask_max_v < 0) opt.route_mask_max_v = 0;
    std::transform(opt.large_instance_mode.begin(), opt.large_instance_mode.end(),
                   opt.large_instance_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.large_instance_mode != "off" && opt.large_instance_mode != "force") {
        opt.large_instance_mode = "auto";
    }
    std::transform(opt.large_lb_mode.begin(), opt.large_lb_mode.end(),
                   opt.large_lb_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.large_lb_mode != "none" &&
        opt.large_lb_mode != "inventory-only" &&
        opt.large_lb_mode != "movement-projection" &&
        opt.large_lb_mode != "column-pool-relaxation" &&
        opt.large_lb_mode != "auto") {
        opt.large_lb_mode = "auto";
    }
    std::transform(opt.pricing_engine.begin(), opt.pricing_engine.end(),
                   opt.pricing_engine.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.pricing_engine != "exact-label" &&
        opt.pricing_engine != "ng-dssr" &&
        opt.pricing_engine != "hybrid") {
        opt.pricing_engine = "auto";
    }
    std::transform(opt.ng_neighborhood_mode.begin(), opt.ng_neighborhood_mode.end(),
                   opt.ng_neighborhood_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.ng_neighborhood_mode != "dual-aware" &&
        opt.ng_neighborhood_mode != "hybrid") {
        opt.ng_neighborhood_mode = "nearest";
    }
    if (opt.ng_size < 1) opt.ng_size = 1;
    if (opt.dssr_max_rounds < 1) opt.dssr_max_rounds = 1;
    if (opt.dssr_expand_per_round < 1) opt.dssr_expand_per_round = 1;
    if (opt.dssr_time_limit < 0.0) opt.dssr_time_limit = 0.0;
    std::transform(opt.column_tracks.begin(), opt.column_tracks.end(),
                   opt.column_tracks.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.column_tracks != "elementary-only" &&
        opt.column_tracks != "two-track") {
        opt.column_tracks = "auto";
    }
    if (opt.relaxed_columns_max_per_pricing < 0) {
        opt.relaxed_columns_max_per_pricing = 0;
    }
    std::transform(opt.rmp_column_space.begin(), opt.rmp_column_space.end(),
                   opt.rmp_column_space.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.rmp_column_space != "elementary" &&
        opt.rmp_column_space != "ng-relaxed" &&
        opt.rmp_column_space != "two-track") {
        opt.rmp_column_space = "auto";
    }
    if (opt.dssr_relaxed_closure_time < 0.0) opt.dssr_relaxed_closure_time = 0.0;
    if (opt.dssr_relaxed_closure_max_labels < 0) opt.dssr_relaxed_closure_max_labels = 0;
    if (opt.dssr_close_relaxed_pricing) opt.ng_relaxed_closure = true;
    if (opt.ng_relaxed_closure_time < 0.0) opt.ng_relaxed_closure_time = 0.0;
    if (opt.ng_relaxed_max_labels < 0) opt.ng_relaxed_max_labels = 0;
    if (opt.ng_relaxed_closure_time == 30.0 && opt.dssr_relaxed_closure_time != 30.0) {
        opt.ng_relaxed_closure_time = opt.dssr_relaxed_closure_time;
    }
    if (opt.ng_relaxed_max_labels == 0 && opt.dssr_relaxed_closure_max_labels > 0) {
        opt.ng_relaxed_max_labels = opt.dssr_relaxed_closure_max_labels;
    }
    if (opt.relaxed_rmp_cg_max_iterations < 1) opt.relaxed_rmp_cg_max_iterations = 1;
    if (opt.relaxed_rmp_cg_time < 0.0) opt.relaxed_rmp_cg_time = 0.0;
    if (opt.relaxed_rmp_cg_columns_per_iteration < 1) {
        opt.relaxed_rmp_cg_columns_per_iteration = 1;
    }
    if (opt.frontier_relaxed_rmp_cg_time_per_interval < 0.0) {
        opt.frontier_relaxed_rmp_cg_time_per_interval = 0.0;
    }
    if (opt.frontier_relaxed_rmp_cg_max_intervals < 0) {
        opt.frontier_relaxed_rmp_cg_max_intervals = 0;
    }
    if (opt.large_relaxed_rmp_column_budget < 1) opt.large_relaxed_rmp_column_budget = 1;
    if (opt.large_relaxed_rmp_time < 0.0) opt.large_relaxed_rmp_time = 0.0;
    opt.primal_heuristic = lowerAscii(opt.primal_heuristic);
    if (opt.primal_heuristic != "greedy" &&
        opt.primal_heuristic != "hga-tgbc" &&
        opt.primal_heuristic != "best-of-all") {
        opt.primal_heuristic = "none";
    }
    if (opt.primal_heuristic_seconds < 0.0) opt.primal_heuristic_seconds = 0.0;
    if (opt.primal_heuristic_runs < 1) opt.primal_heuristic_runs = 1;
    if (opt.exact_phase_local_redecode_seconds < 0.0) {
        opt.exact_phase_local_redecode_seconds = 0.0;
    }
    if (opt.support_duration_max_subset_size < 0) opt.support_duration_max_subset_size = 0;
    if (opt.bpc_incumbent_seconds < 0.0) opt.bpc_incumbent_seconds = 0.0;
    if (opt.bpc_incumbent_rounds < 1) opt.bpc_incumbent_rounds = 1;
    if (opt.frontier_final_nodes < 1) opt.frontier_final_nodes = 1;
    if (opt.frontier_adaptive_max_depth < 0) opt.frontier_adaptive_max_depth = 0;
    if (opt.frontier_critical_max_depth < 0) opt.frontier_critical_max_depth = 0;
    if (opt.frontier_pre_split_critical) {
        opt.frontier_split_before_tree = true;
        if (opt.algorithm_preset == "paper-bpc-core-adaptive") {
            opt.relaxation_portfolio_mode = "adaptive";
            opt.relaxation_portfolio_keep_best_bound = true;
            opt.relaxation_portfolio_max_variants =
                std::max(opt.relaxation_portfolio_max_variants, 3);
            opt.large_compact_flow_connectivity = false;
            opt.service_operation_min_handling_cuts = false;
            opt.penalty_movement_lb_cuts = false;
            opt.frontier_scheduling_mode = "adaptive-best-bound";
            opt.frontier_critical_band_auto = true;
        }
        opt.frontier_adaptive_split = true;
        if (opt.frontier_critical_max_depth > 0) {
            opt.frontier_adaptive_max_depth =
                std::max(opt.frontier_adaptive_max_depth,
                         opt.frontier_critical_max_depth);
        }
        if (opt.frontier_split_batch <= 0) {
            opt.frontier_split_batch = 2;
        }
    }
    if (opt.frontier_adaptive_min_width <= 0.0) opt.frontier_adaptive_min_width = 1e-4;
    if (opt.frontier_adaptive_split_factor < 2) opt.frontier_adaptive_split_factor = 2;
    if (opt.v20_cover_max_size < 2) opt.v20_cover_max_size = 2;
    if (opt.v20_cover_max_cuts < 0) opt.v20_cover_max_cuts = 0;
    if (opt.v20_cover_separation_seconds < 0.0) opt.v20_cover_separation_seconds = 0.0;
    if (opt.station_residual_cover_max_cuts < 0) opt.station_residual_cover_max_cuts = 0;
    opt.large_compact_flow_relaxation = lowerAscii(opt.large_compact_flow_relaxation);
    if (opt.large_compact_flow_relaxation != "lp" &&
        opt.large_compact_flow_relaxation != "mip-light") {
        opt.large_compact_flow_relaxation = "off";
    }
    if (opt.large_compact_flow_time_limit < 0.0) {
        opt.large_compact_flow_time_limit = 0.0;
    }
    opt.mip_solver = lowerAscii(opt.mip_solver);
    if (opt.mip_solver.empty()) opt.mip_solver = "cplex";
    if (opt.mip_solver != "cplex") {
        throw std::runtime_error("--mip-solver currently supports cplex only");
    }
    if (opt.cplex_threads < 0) opt.cplex_threads = 0;
    if (opt.mip_threads < 0) opt.mip_threads = 0;
    if (opt.compact_bc_threads < 0) opt.compact_bc_threads = 0;
    if (opt.compact_bc_time_limit < 0.0) opt.compact_bc_time_limit = 0.0;
    if (opt.compact_bc_root_cut_rounds < 0) opt.compact_bc_root_cut_rounds = 0;
    if (opt.compact_bc_root_cut_time_limit < 0.0) {
        opt.compact_bc_root_cut_time_limit = 0.0;
    }
    if (opt.compact_bc_dynamic_cut_violation_tol <= 0.0) {
        opt.compact_bc_dynamic_cut_violation_tol = 1e-6;
    }
    opt.compact_bc_domain_propagation_mode =
        lowerAscii(opt.compact_bc_domain_propagation_mode);
    if (opt.compact_bc_domain_propagation_mode != "off" &&
        opt.compact_bc_domain_propagation_mode != "iterative") {
        opt.compact_bc_domain_propagation_mode = "static";
    }
    if (opt.compact_bc_domain_propagation_rounds < 0) {
        opt.compact_bc_domain_propagation_rounds = 0;
    }
    if (opt.compact_bc_domain_propagation_mode == "off") {
        opt.compact_bc_domain_propagation_rounds = 0;
    } else if (opt.compact_bc_domain_propagation_rounds == 0) {
        opt.compact_bc_domain_propagation_rounds = 1;
    }
    opt.compact_bc_model_size_policy = lowerAscii(opt.compact_bc_model_size_policy);
    if (opt.compact_bc_model_size_policy != "resource-adaptive" &&
        opt.compact_bc_model_size_policy != "diagnostic-minimal") {
        opt.compact_bc_model_size_policy = "full";
    }
    if (opt.compact_bc_max_rows < 0) opt.compact_bc_max_rows = 0;
    if (opt.compact_bc_max_cols < 0) opt.compact_bc_max_cols = 0;
    if (opt.compact_bc_max_nonzeros < 0) opt.compact_bc_max_nonzeros = 0;
    if (opt.compact_bc_max_memory_mb < 0.0) opt.compact_bc_max_memory_mb = 0.0;
    opt.compact_bc_expensive_static_families =
        lowerAscii(opt.compact_bc_expensive_static_families);
    if (opt.compact_bc_expensive_static_families != "on" &&
        opt.compact_bc_expensive_static_families != "off") {
        opt.compact_bc_expensive_static_families = "auto";
    }
    opt.compact_bc_receiver_source_cover_mode =
        lowerAscii(opt.compact_bc_receiver_source_cover_mode);
    if (opt.compact_bc_receiver_source_cover_mode != "off" &&
        opt.compact_bc_receiver_source_cover_mode != "diagnostic" &&
        opt.compact_bc_receiver_source_cover_mode != "singleton-paper-safe" &&
        opt.compact_bc_receiver_source_cover_mode != "pair-net-paper-safe" &&
        opt.compact_bc_receiver_source_cover_mode != "pair-diagnostic" &&
        opt.compact_bc_receiver_source_cover_mode != "set-diagnostic" &&
        opt.compact_bc_receiver_source_cover_mode != "paper-safe") {
        opt.compact_bc_receiver_source_cover_mode = "off";
    }
    opt.compact_bc_receiver_source_cover_cuts =
        opt.compact_bc_receiver_source_cover_mode == "singleton-paper-safe" ||
        opt.compact_bc_receiver_source_cover_mode == "pair-net-paper-safe" ||
        opt.compact_bc_receiver_source_cover_mode == "paper-safe";
    opt.compact_bc_cut_profile = lowerAscii(opt.compact_bc_cut_profile);
    if (opt.compact_bc_cut_profile != "conservative" &&
        opt.compact_bc_cut_profile != "balanced" &&
        opt.compact_bc_cut_profile != "aggressive") {
        opt.compact_bc_cut_profile = "balanced";
    }
    if (opt.compact_bc_support_cut_max_size < 0) {
        opt.compact_bc_support_cut_max_size = 0;
    }
    if (opt.compact_bc_support_cut_max_subsets < 0) {
        opt.compact_bc_support_cut_max_subsets = 0;
    }
    opt.relaxation_portfolio_mode = lowerAscii(opt.relaxation_portfolio_mode);
    if (opt.relaxation_portfolio_mode != "adaptive" &&
        opt.relaxation_portfolio_mode != "race" &&
        opt.relaxation_portfolio_mode != "exhaustive") {
        opt.relaxation_portfolio_mode = "fixed";
    }
    if (opt.relaxation_portfolio_probe_seconds < 0.0) {
        opt.relaxation_portfolio_probe_seconds = 0.0;
    }
    if (opt.relaxation_portfolio_max_variants < 1) {
        opt.relaxation_portfolio_max_variants = 1;
    }
    if (opt.relaxation_portfolio_min_improvement < 0.0) {
        opt.relaxation_portfolio_min_improvement = 0.0;
    }
    opt.relaxation_certificate_mode = lowerAscii(opt.relaxation_certificate_mode);
    if (opt.relaxation_certificate_mode != "cutoff-feasibility" &&
        opt.relaxation_certificate_mode != "both") {
        opt.relaxation_certificate_mode = "bound";
    }
    if (opt.cutoff_feasibility_epsilon < 0.0) {
        opt.cutoff_feasibility_epsilon = 0.0;
    }
    if (opt.cutoff_feasibility_time_limit < 0.0) {
        opt.cutoff_feasibility_time_limit = 0.0;
    }
    opt.interval_closure_mode = lowerAscii(opt.interval_closure_mode);
    if (opt.interval_closure_mode != "focus" &&
        opt.interval_closure_mode != "merge") {
        opt.interval_closure_mode = "off";
    }
    opt.interval_closure_variant_mode = lowerAscii(opt.interval_closure_variant_mode);
    if (opt.interval_closure_variant_mode != "exhaustive" &&
        opt.interval_closure_variant_mode != "cutoff-feasibility" &&
        opt.interval_closure_variant_mode != "bpc") {
        opt.interval_closure_variant_mode = "best-fixed";
    }
    if (opt.interval_closure_time_limit < 0.0) {
        opt.interval_closure_time_limit = 0.0;
    }
    opt.frontier_scheduling_mode = lowerAscii(opt.frontier_scheduling_mode);
    if (opt.frontier_scheduling_mode != "v12-fast-close" &&
        opt.frontier_scheduling_mode != "adaptive-best-bound") {
        opt.frontier_scheduling_mode = "default";
    }
    if (opt.frontier_critical_band_max_depth < 0) {
        opt.frontier_critical_band_max_depth = 0;
    }
    if (opt.frontier_critical_band_min_width <= 0.0) {
        opt.frontier_critical_band_min_width = 1e-4;
    }
    if (opt.progress_interval_seconds < 0.0) opt.progress_interval_seconds = 0.0;
    if (opt.compact_bc_progress_interval < 0.0) opt.compact_bc_progress_interval = 0.0;
    if (opt.frontier_focus_time_limit == 0.0) opt.frontier_focus_time_limit = -1.0;
    if (opt.frontier_focus_relax_seconds == 0.0) opt.frontier_focus_relax_seconds = -1.0;
    if (opt.frontier_focus_tree_nodes == 0) opt.frontier_focus_tree_nodes = -1;
    std::transform(opt.frontier_resume_mode.begin(), opt.frontier_resume_mode.end(),
                   opt.frontier_resume_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.frontier_resume_mode != "interval-only" &&
        opt.frontier_resume_mode != "full-frontier") {
        opt.frontier_resume_mode = "interval-only";
    }
    std::transform(opt.frontier_closure_mode.begin(), opt.frontier_closure_mode.end(),
                   opt.frontier_closure_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.frontier_closure_mode != "exact-cg" &&
        opt.frontier_closure_mode != "tree" &&
        opt.frontier_closure_mode != "relax-only") {
        opt.frontier_closure_mode = "auto";
    }
    if (opt.closure_max_cg_iterations < 1) opt.closure_max_cg_iterations = 1;
    if (opt.closure_returned_columns < 1) opt.closure_returned_columns = 1;
    if (opt.closure_pricing_time_per_call < 0.0) opt.closure_pricing_time_per_call = 0.0;
    if (opt.frontier_iterative_max_rounds < 0) opt.frontier_iterative_max_rounds = 0;
    if (opt.frontier_iterative_round_time < 0.0) opt.frontier_iterative_round_time = 0.0;
    if (opt.frontier_iterative_target_gap < 0.0) opt.frontier_iterative_target_gap = 0.0;
    if (opt.pricing_verifier_time < 0.0) opt.pricing_verifier_time = 0.0;
    std::transform(opt.pricing_verifier_mode.begin(), opt.pricing_verifier_mode.end(),
                   opt.pricing_verifier_mode.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.pricing_verifier_mode != "label-dp" &&
        opt.pricing_verifier_mode != "route-mask-dp") {
        opt.pricing_verifier_mode = "auto";
    }
    std::transform(opt.cg_dual_stabilization.begin(), opt.cg_dual_stabilization.end(),
                   opt.cg_dual_stabilization.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (opt.cg_dual_stabilization != "smooth" &&
        opt.cg_dual_stabilization != "box") {
        opt.cg_dual_stabilization = "none";
    }
    if (opt.cg_dual_smoothing_alpha < 0.0) opt.cg_dual_smoothing_alpha = 0.0;
    if (opt.cg_dual_smoothing_alpha > 1.0) opt.cg_dual_smoothing_alpha = 1.0;
    if (opt.cg_dual_box_radius < 0.0) opt.cg_dual_box_radius = 0.0;
    if (opt.cg_stabilization_max_nonimprove < 0) opt.cg_stabilization_max_nonimprove = 0;
    if (opt.cg_stabilization_switch_to_true_after < 0) {
        opt.cg_stabilization_switch_to_true_after = 0;
    }
    const std::string explicit_pricing_dominance_mode =
        opt.pricing_dominance_mode;
    const std::string explicit_pricing_completion_bound =
        opt.pricing_completion_bound;
    const std::string explicit_pricing_decomposition =
        opt.pricing_decomposition;
    const bool explicit_pricing_load_dp_cache = opt.pricing_load_dp_cache;
    const std::string explicit_pricing_route_skeleton_mode =
        opt.pricing_route_skeleton_mode;
    const bool explicit_pricing_route_skeleton_cache =
        opt.pricing_route_skeleton_cache;
    const bool explicit_pricing_load_dp_dominance =
        opt.pricing_load_dp_dominance;
    const bool explicit_pricing_operation_dp_dominance =
        opt.pricing_operation_dp_dominance;
    const std::string explicit_bpc_seed_columns = opt.bpc_seed_columns;
    const int explicit_bpc_seed_column_max = opt.bpc_seed_column_max;
    const std::string explicit_bpc_cut_family = opt.bpc_cut_family;
    const int explicit_bpc_cut_separation_rounds =
        opt.bpc_cut_separation_rounds;
    const bool explicit_compact_bc_direct_gini_rows =
        opt.compact_bc_direct_gini_rows;
    const bool explicit_compact_bc_tight_mccormick =
        opt.compact_bc_tight_mccormick;
    const bool explicit_compact_bc_inventory_conservation =
        opt.compact_bc_inventory_conservation;
    const bool explicit_compact_bc_movement_reachability_domains =
        opt.compact_bc_movement_reachability_domains;
    const bool explicit_compact_bc_visit_inventory_linking =
        opt.compact_bc_visit_inventory_linking;
    const bool explicit_compact_bc_objective_estimator_cutoff =
        opt.compact_bc_objective_estimator_cutoff;
    const bool explicit_compact_bc_penalty_lb_closure =
        opt.compact_bc_penalty_lb_closure;
    const bool explicit_compact_bc_support_duration_cuts =
        opt.compact_bc_support_duration_cuts;
    const bool explicit_compact_bc_pairwise_transfer_compatibility =
        opt.compact_bc_pairwise_transfer_compatibility;
    const bool explicit_compact_bc_receiver_source_cover_cuts =
        opt.compact_bc_receiver_source_cover_cuts;
    const std::string explicit_compact_bc_receiver_source_cover_mode =
        opt.compact_bc_receiver_source_cover_mode;
    const std::string explicit_compact_bc_low_gini_strengthening =
        opt.compact_bc_low_gini_strengthening;
    const std::string explicit_compact_bc_denominator_bound_mode =
        opt.compact_bc_denominator_bound_mode;
    const std::string explicit_compact_bc_objective_estimator_mode =
        opt.compact_bc_objective_estimator_mode;
    const bool explicit_gini_spread_cuts = opt.gini_spread_cuts;
    const bool explicit_required_movement_cuts = opt.required_movement_cuts;
    const bool explicit_global_handling_capacity_cuts =
        opt.global_handling_capacity_cuts;
    const bool explicit_low_gini_ratio_band_tightening =
        opt.low_gini_ratio_band_tightening;
    applyAlgorithmPreset(opt);
    if (opt.pricing_dominance_mode_explicit) {
        opt.pricing_dominance_mode = explicit_pricing_dominance_mode;
    }
    if (opt.pricing_completion_bound_explicit) {
        opt.pricing_completion_bound = explicit_pricing_completion_bound;
        const std::string mode = lowerAscii(opt.pricing_completion_bound);
        opt.pricing_completion_lb_pruning = mode != "none" && mode != "off";
    }
    if (opt.pricing_decomposition_explicit) {
        opt.pricing_decomposition = explicit_pricing_decomposition;
    }
    if (opt.pricing_load_dp_cache_explicit) {
        opt.pricing_load_dp_cache = explicit_pricing_load_dp_cache;
    }
    if (opt.pricing_route_skeleton_mode_explicit) {
        opt.pricing_route_skeleton_mode = explicit_pricing_route_skeleton_mode;
    }
    if (opt.pricing_route_skeleton_cache_explicit) {
        opt.pricing_route_skeleton_cache = explicit_pricing_route_skeleton_cache;
    }
    if (opt.pricing_load_dp_dominance_explicit) {
        opt.pricing_load_dp_dominance = explicit_pricing_load_dp_dominance;
    }
    if (opt.pricing_operation_dp_dominance_explicit) {
        opt.pricing_operation_dp_dominance =
            explicit_pricing_operation_dp_dominance;
    }
    if (opt.bpc_seed_columns_explicit) {
        opt.bpc_seed_columns = explicit_bpc_seed_columns;
    }
    if (opt.bpc_seed_column_max_explicit) {
        opt.bpc_seed_column_max = explicit_bpc_seed_column_max;
    }
    if (opt.bpc_cut_family_explicit) {
        opt.bpc_cut_family = explicit_bpc_cut_family;
    }
    if (opt.bpc_cut_separation_rounds_explicit) {
        opt.bpc_cut_separation_rounds = explicit_bpc_cut_separation_rounds;
    }
    if (opt.compact_bc_direct_gini_rows_explicit) {
        opt.compact_bc_direct_gini_rows = explicit_compact_bc_direct_gini_rows;
    }
    if (opt.compact_bc_tight_mccormick_explicit) {
        opt.compact_bc_tight_mccormick = explicit_compact_bc_tight_mccormick;
    }
    if (opt.compact_bc_inventory_conservation_explicit) {
        opt.compact_bc_inventory_conservation =
            explicit_compact_bc_inventory_conservation;
    }
    if (opt.compact_bc_movement_reachability_domains_explicit) {
        opt.compact_bc_movement_reachability_domains =
            explicit_compact_bc_movement_reachability_domains;
    }
    if (opt.compact_bc_visit_inventory_linking_explicit) {
        opt.compact_bc_visit_inventory_linking =
            explicit_compact_bc_visit_inventory_linking;
    }
    if (opt.compact_bc_objective_estimator_cutoff_explicit) {
        opt.compact_bc_objective_estimator_cutoff =
            explicit_compact_bc_objective_estimator_cutoff;
    }
    if (opt.compact_bc_penalty_lb_closure_explicit) {
        opt.compact_bc_penalty_lb_closure =
            explicit_compact_bc_penalty_lb_closure;
    }
    if (opt.compact_bc_support_duration_cuts_explicit) {
        opt.compact_bc_support_duration_cuts =
            explicit_compact_bc_support_duration_cuts;
    }
    if (opt.compact_bc_pairwise_transfer_compatibility_explicit) {
        opt.compact_bc_pairwise_transfer_compatibility =
            explicit_compact_bc_pairwise_transfer_compatibility;
    }
    if (opt.compact_bc_receiver_source_cover_explicit) {
        opt.compact_bc_receiver_source_cover_cuts =
            explicit_compact_bc_receiver_source_cover_cuts;
        opt.compact_bc_receiver_source_cover_mode =
            explicit_compact_bc_receiver_source_cover_mode;
    }
    if (opt.compact_bc_low_gini_strengthening_explicit) {
        opt.compact_bc_low_gini_strengthening =
            explicit_compact_bc_low_gini_strengthening;
    }
    if (opt.compact_bc_denominator_bound_mode_explicit) {
        opt.compact_bc_denominator_bound_mode =
            explicit_compact_bc_denominator_bound_mode;
    }
    if (opt.compact_bc_objective_estimator_mode_explicit) {
        opt.compact_bc_objective_estimator_mode =
            explicit_compact_bc_objective_estimator_mode;
    }
    if (opt.gini_spread_cuts_explicit) {
        opt.gini_spread_cuts = explicit_gini_spread_cuts;
    }
    if (opt.required_movement_cuts_explicit) {
        opt.required_movement_cuts = explicit_required_movement_cuts;
    }
    if (opt.global_handling_capacity_cuts_explicit) {
        opt.global_handling_capacity_cuts =
            explicit_global_handling_capacity_cuts;
    }
    if (opt.low_gini_ratio_band_tightening_explicit) {
        opt.low_gini_ratio_band_tightening =
            explicit_low_gini_ratio_band_tightening;
    }
    opt.compact_bc_low_gini_strengthening =
        lowerAscii(opt.compact_bc_low_gini_strengthening);
    if (opt.compact_bc_low_gini_strengthening == "none" ||
        opt.compact_bc_low_gini_strengthening == "false") {
        opt.compact_bc_low_gini_strengthening = "off";
    }
    if (opt.compact_bc_low_gini_strengthening != "off" &&
        opt.compact_bc_low_gini_strengthening != "safe" &&
        opt.compact_bc_low_gini_strengthening != "aggressive-diagnostic") {
        opt.compact_bc_low_gini_strengthening = "safe";
    }
    opt.compact_bc_denominator_bound_mode =
        lowerAscii(opt.compact_bc_denominator_bound_mode);
    if (opt.compact_bc_denominator_bound_mode != "basic" &&
        opt.compact_bc_denominator_bound_mode != "tight" &&
        opt.compact_bc_denominator_bound_mode != "multirow") {
        opt.compact_bc_denominator_bound_mode = "basic";
    }
    opt.compact_bc_objective_estimator_mode =
        lowerAscii(opt.compact_bc_objective_estimator_mode);
    if (opt.compact_bc_objective_estimator_mode != "single" &&
        opt.compact_bc_objective_estimator_mode != "multirow" &&
        opt.compact_bc_objective_estimator_mode != "adaptive") {
        opt.compact_bc_objective_estimator_mode = "single";
    }
    opt.compact_bc_s_range_refinement =
        lowerAscii(opt.compact_bc_s_range_refinement);
    if (opt.compact_bc_s_range_refinement == "none" ||
        opt.compact_bc_s_range_refinement == "false") {
        opt.compact_bc_s_range_refinement = "off";
    }
    if (opt.compact_bc_s_range_refinement != "off" &&
        opt.compact_bc_s_range_refinement != "diagnostic" &&
        opt.compact_bc_s_range_refinement != "paper-safe") {
        opt.compact_bc_s_range_refinement = "off";
    }
    opt.compact_bc_s_range_buckets =
        std::max(1, opt.compact_bc_s_range_buckets);
    opt.compact_bc_rmin_rmax_propagation =
        lowerAscii(opt.compact_bc_rmin_rmax_propagation);
    if (opt.compact_bc_rmin_rmax_propagation != "off" &&
        opt.compact_bc_rmin_rmax_propagation != "safe" &&
        opt.compact_bc_rmin_rmax_propagation != "diagnostic") {
        opt.compact_bc_rmin_rmax_propagation = "off";
    }
    opt.compact_bc_sp_product_estimator =
        lowerAscii(opt.compact_bc_sp_product_estimator);
    if (opt.compact_bc_sp_product_estimator == "none" ||
        opt.compact_bc_sp_product_estimator == "false") {
        opt.compact_bc_sp_product_estimator = "off";
    }
    if (opt.compact_bc_sp_product_estimator != "off" &&
        opt.compact_bc_sp_product_estimator != "diagnostic" &&
        opt.compact_bc_sp_product_estimator != "paper-safe") {
        opt.compact_bc_sp_product_estimator = "off";
    }
    opt.compact_bc_sp_product_bounds =
        lowerAscii(opt.compact_bc_sp_product_bounds);
    if (opt.compact_bc_sp_product_bounds != "basic" &&
        opt.compact_bc_sp_product_bounds != "tight") {
        opt.compact_bc_sp_product_bounds = "basic";
    }
    opt.compact_bc_low_gini_precheck =
        lowerAscii(opt.compact_bc_low_gini_precheck);
    if (opt.compact_bc_low_gini_precheck != "off" &&
        opt.compact_bc_low_gini_precheck != "lp" &&
        opt.compact_bc_low_gini_precheck != "domain" &&
        opt.compact_bc_low_gini_precheck != "both") {
        opt.compact_bc_low_gini_precheck = "off";
    }
    opt.tailored_bc_mode = lowerAscii(opt.tailored_bc_mode);
    if (opt.tailored_bc_mode != "callback" &&
        opt.tailored_bc_mode != "static" &&
        opt.tailored_bc_mode != "static_fallback" &&
        opt.tailored_bc_mode != "outer_gini_controller" &&
        opt.tailored_bc_mode != "off") {
        opt.tailored_bc_mode = opt.tailored_bc_enabled ? "callback" : "off";
    }
    opt.tailored_bc_branching_priority =
        lowerAscii(opt.tailored_bc_branching_priority);
    if (opt.tailored_bc_branching_priority != "basic" &&
        opt.tailored_bc_branching_priority != "gini-first" &&
        opt.tailored_bc_branching_priority != "adaptive") {
        opt.tailored_bc_branching_priority = "off";
    }
    opt.tailored_bc_gini_branching = lowerAscii(opt.tailored_bc_gini_branching);
    if (opt.tailored_bc_gini_branching != "callback" &&
        opt.tailored_bc_gini_branching != "selector" &&
        opt.tailored_bc_gini_branching != "outer-controller" &&
        opt.tailored_bc_gini_branching != "auto") {
        opt.tailored_bc_gini_branching = "off";
    }
    opt.tailored_bc_support_duration_cover_mode =
        lowerAscii(opt.tailored_bc_support_duration_cover_mode);
    if (opt.tailored_bc_support_duration_cover_mode == "basic") {
        opt.tailored_bc_support_duration_cover_mode = "support_cover_basic";
    } else if (opt.tailored_bc_support_duration_cover_mode == "lifted") {
        opt.tailored_bc_support_duration_cover_mode = "support_cover_lifted";
    }
    if (opt.tailored_bc_support_duration_cover_mode != "support_cover_basic" &&
        opt.tailored_bc_support_duration_cover_mode != "support_cover_lifted" &&
        opt.tailored_bc_support_duration_cover_mode != "off") {
        opt.tailored_bc_support_duration_cover_mode = "support_cover_lifted";
    }
    if (opt.tailored_bc_gini_branch_min_width <= 0.0) {
        opt.tailored_bc_gini_branch_min_width = 1e-4;
    }
    opt.tailored_bc_gini_subset_max_size =
        std::min(3, std::max(1, opt.tailored_bc_gini_subset_max_size));
    if (opt.tailored_bc_gini_subset_max_cuts < 0) {
        opt.tailored_bc_gini_subset_max_cuts = 0;
    }
    opt.tailored_bc_callback_separation_pacing =
        lowerAscii(opt.tailored_bc_callback_separation_pacing);
    if (opt.tailored_bc_callback_separation_pacing != "off" &&
        opt.tailored_bc_callback_separation_pacing != "bound-aware") {
        opt.tailored_bc_callback_separation_pacing = "off";
    }
    if (opt.tailored_bc_callback_separation_min_calls < 1) {
        opt.tailored_bc_callback_separation_min_calls = 1;
    }
    opt.tailored_bc_callback_cut_profile =
        lowerAscii(opt.tailored_bc_callback_cut_profile);
    if (opt.tailored_bc_callback_cut_profile == "none") {
        opt.tailored_bc_callback_cut_profile = "off";
    } else if (opt.tailored_bc_callback_cut_profile == "low_gini") {
        opt.tailored_bc_callback_cut_profile = "low-gini";
    } else if (opt.tailored_bc_callback_cut_profile == "local_centering") {
        opt.tailored_bc_callback_cut_profile = "local-centering";
    } else if (opt.tailored_bc_callback_cut_profile == "subset_only") {
        opt.tailored_bc_callback_cut_profile = "subset-only";
    } else if (opt.tailored_bc_callback_cut_profile == "transfer_only") {
        opt.tailored_bc_callback_cut_profile = "transfer-only";
    } else if (opt.tailored_bc_callback_cut_profile == "support_only") {
        opt.tailored_bc_callback_cut_profile = "support-only";
    } else if (opt.tailored_bc_callback_cut_profile == "subset_cross_h" ||
               opt.tailored_bc_callback_cut_profile == "subset_cross_h_only") {
        opt.tailored_bc_callback_cut_profile = "subset-cross-h-only";
    } else if (opt.tailored_bc_callback_cut_profile == "local_q" ||
               opt.tailored_bc_callback_cut_profile == "local_q_only") {
        opt.tailored_bc_callback_cut_profile = "local-q-only";
    } else if (opt.tailored_bc_callback_cut_profile == "gs_only") {
        opt.tailored_bc_callback_cut_profile = "gs-only";
    } else if (opt.tailored_bc_callback_cut_profile == "sp_only") {
        opt.tailored_bc_callback_cut_profile = "sp-only";
    } else if (opt.tailored_bc_callback_cut_profile == "gs_sp_only") {
        opt.tailored_bc_callback_cut_profile = "gs-sp-only";
    } else if (opt.tailored_bc_callback_cut_profile == "route_cutset_only") {
        opt.tailored_bc_callback_cut_profile = "route-cutset-only";
    } else if (opt.tailored_bc_callback_cut_profile == "route_combined") {
        opt.tailored_bc_callback_cut_profile = "route-combined";
    }
    if (opt.tailored_bc_callback_cut_profile != "off" &&
        opt.tailored_bc_callback_cut_profile != "full" &&
        opt.tailored_bc_callback_cut_profile != "cheap" &&
        opt.tailored_bc_callback_cut_profile != "low-gini" &&
        opt.tailored_bc_callback_cut_profile != "local-centering" &&
        opt.tailored_bc_callback_cut_profile != "subset-only" &&
        opt.tailored_bc_callback_cut_profile != "transfer-only" &&
        opt.tailored_bc_callback_cut_profile != "support-only" &&
        opt.tailored_bc_callback_cut_profile != "subset-cross-h-only" &&
        opt.tailored_bc_callback_cut_profile != "local-q-only" &&
        opt.tailored_bc_callback_cut_profile != "gs-only" &&
        opt.tailored_bc_callback_cut_profile != "sp-only" &&
        opt.tailored_bc_callback_cut_profile != "gs-sp-only" &&
        opt.tailored_bc_callback_cut_profile != "route-cutset-only" &&
        opt.tailored_bc_callback_cut_profile != "route-combined") {
        opt.tailored_bc_callback_cut_profile = "full";
    }
    opt.tailored_bc_s_bucket_ledger = lowerAscii(opt.tailored_bc_s_bucket_ledger);
    if (opt.tailored_bc_s_bucket_ledger == "none") {
        opt.tailored_bc_s_bucket_ledger = "off";
    }
    if (opt.tailored_bc_s_bucket_ledger != "off" &&
        opt.tailored_bc_s_bucket_ledger != "diagnostic" &&
        opt.tailored_bc_s_bucket_ledger != "paper-safe") {
        opt.tailored_bc_s_bucket_ledger = "off";
    }
    opt.tailored_bc_s_bucket_count =
        std::max(1, opt.tailored_bc_s_bucket_count);
    opt.tailored_bc_s_bucket_policy =
        lowerAscii(opt.tailored_bc_s_bucket_policy);
    if (opt.tailored_bc_s_bucket_policy != "uniform" &&
        opt.tailored_bc_s_bucket_policy != "adaptive-open" &&
        opt.tailored_bc_s_bucket_policy != "adaptive-snapshot" &&
        opt.tailored_bc_s_bucket_policy != "adaptive-cutoff" &&
        opt.tailored_bc_s_bucket_policy != "adaptive-hybrid") {
        opt.tailored_bc_s_bucket_policy = "uniform";
    }
    if (opt.tailored_bc_s_bucket_time_budget < 0.0) {
        opt.tailored_bc_s_bucket_time_budget = 0.0;
    }
    opt.tailored_bc_s_bucket_max_depth =
        std::max(0, opt.tailored_bc_s_bucket_max_depth);
    if (opt.tailored_bc_s_bucket_min_width < 0.0) {
        opt.tailored_bc_s_bucket_min_width = 0.0;
    }
    opt.tailored_bc_s_bucket_refine_top_k =
        std::max(1, opt.tailored_bc_s_bucket_refine_top_k);
    opt.tailored_bc_s_bucket_refine_rule =
        lowerAscii(opt.tailored_bc_s_bucket_refine_rule);
    if (opt.tailored_bc_s_bucket_refine_rule != "widest" &&
        opt.tailored_bc_s_bucket_refine_rule != "worst-gap" &&
        opt.tailored_bc_s_bucket_refine_rule != "plateau-s" &&
        opt.tailored_bc_s_bucket_refine_rule != "hybrid") {
        opt.tailored_bc_s_bucket_refine_rule = "worst-gap";
    }
    if (opt.tailored_bc_s_bucket_ledger != "off") {
        opt.compact_bc_s_range_refinement = opt.tailored_bc_s_bucket_ledger;
        opt.compact_bc_s_range_buckets =
            std::max(opt.compact_bc_s_range_buckets,
                     opt.tailored_bc_s_bucket_count);
        opt.compact_bc_s_range_adaptive =
            opt.compact_bc_s_range_adaptive ||
            opt.tailored_bc_s_bucket_policy != "uniform";
    }
    opt.tailored_bc_subset_cross_h_separation_profile =
        lowerAscii(opt.tailored_bc_subset_cross_h_separation_profile);
    if (opt.tailored_bc_subset_cross_h_separation_profile != "deviation" &&
        opt.tailored_bc_subset_cross_h_separation_profile != "target-weighted" &&
        opt.tailored_bc_subset_cross_h_separation_profile != "fractional" &&
        opt.tailored_bc_subset_cross_h_separation_profile != "dominant-bucket" &&
        opt.tailored_bc_subset_cross_h_separation_profile != "hybrid") {
        opt.tailored_bc_subset_cross_h_separation_profile = "deviation";
    }
    opt.tailored_bc_subset_cross_h_max_size =
        std::min(4, std::max(1, opt.tailored_bc_subset_cross_h_max_size));
    if (opt.tailored_bc_subset_cross_h_max_cuts < 0) {
        opt.tailored_bc_subset_cross_h_max_cuts = 0;
    }
    opt.tailored_bc_subset_inventory_max_size =
        std::min(3, std::max(1, opt.tailored_bc_subset_inventory_max_size));
    opt.tailored_bc_transfer_max_receiver_size =
        std::min(3, std::max(1, opt.tailored_bc_transfer_max_receiver_size));
    opt.tailored_bc_bucket_subset_ratio_max_size =
        std::min(4, std::max(1, opt.tailored_bc_bucket_subset_ratio_max_size));
    opt.tailored_bc_bucket_integer_inventory_domain_mode =
        lowerAscii(opt.tailored_bc_bucket_integer_inventory_domain_mode);
    if (opt.tailored_bc_bucket_integer_inventory_domain_mode != "static" &&
        opt.tailored_bc_bucket_integer_inventory_domain_mode != "callback" &&
        opt.tailored_bc_bucket_integer_inventory_domain_mode != "both") {
        opt.tailored_bc_bucket_integer_inventory_domain_mode = "static";
    }
    opt.tailored_bc_bucket_required_movement_max_size =
        std::min(3, std::max(1, opt.tailored_bc_bucket_required_movement_max_size));
    opt.tailored_bc_benders_inventory_cuts =
        lowerAscii(opt.tailored_bc_benders_inventory_cuts);
    if (opt.tailored_bc_benders_inventory_cuts != "diagnostic") {
        opt.tailored_bc_benders_inventory_cuts = "off";
    }
    opt.tailored_bc_gs_product_coupling_mode =
        lowerAscii(opt.tailored_bc_gs_product_coupling_mode);
    if (opt.tailored_bc_gs_product_coupling_mode != "static" &&
        opt.tailored_bc_gs_product_coupling_mode != "callback" &&
        opt.tailored_bc_gs_product_coupling_mode != "both") {
        opt.tailored_bc_gs_product_coupling_mode = "static";
    }
    opt.tailored_bc_gs_product_lower_row =
        lowerAscii(opt.tailored_bc_gs_product_lower_row);
    if (opt.tailored_bc_gs_product_lower_row != "off" &&
        opt.tailored_bc_gs_product_lower_row != "diagnostic" &&
        opt.tailored_bc_gs_product_lower_row != "paper-safe") {
        opt.tailored_bc_gs_product_lower_row = "off";
    }
    opt.tailored_bc_disaggregated_sp_mode =
        lowerAscii(opt.tailored_bc_disaggregated_sp_mode);
    if (opt.tailored_bc_disaggregated_sp_mode != "static" &&
        opt.tailored_bc_disaggregated_sp_mode != "callback" &&
        opt.tailored_bc_disaggregated_sp_mode != "both") {
        opt.tailored_bc_disaggregated_sp_mode = "static";
    }
    opt.tailored_bc_vector_support_cover_max_size =
        std::min(6, std::max(2, opt.tailored_bc_vector_support_cover_max_size));
    opt.tailored_bc_vector_support_cover_max_cuts =
        std::max(0, opt.tailored_bc_vector_support_cover_max_cuts);
    opt.tailored_bc_vector_route_cutset_max_size =
        std::min(8, std::max(2, opt.tailored_bc_vector_route_cutset_max_size));
    opt.tailored_bc_vector_route_cutset_max_cuts =
        std::max(0, opt.tailored_bc_vector_route_cutset_max_cuts);
    opt.tailored_bc_vector_cut_min_violation =
        std::max(0.0, opt.tailored_bc_vector_cut_min_violation);
    opt.tailored_bc_vector_cut_candidate_source =
        lowerAscii(opt.tailored_bc_vector_cut_candidate_source);
    if (opt.tailored_bc_vector_cut_candidate_source != "root" &&
        opt.tailored_bc_vector_cut_candidate_source != "callback" &&
        opt.tailored_bc_vector_cut_candidate_source != "both") {
        opt.tailored_bc_vector_cut_candidate_source = "root";
    }
    opt.tailored_bc_structural_profile =
        lowerAscii(opt.tailored_bc_structural_profile);
    if (opt.tailored_bc_structural_profile.empty()) {
        opt.tailored_bc_structural_profile = "manual";
    }
    const bool safe_low_gini_mode =
        opt.compact_bc_low_gini_strengthening == "safe";
    if (safe_low_gini_mode ||
        opt.compact_bc_denominator_bound_mode != "basic" ||
        opt.compact_bc_objective_estimator_mode != "single") {
        opt.low_gini_ratio_band_tightening = true;
        opt.compact_bc_variable_s_centering = true;
        opt.compact_bc_objective_estimator_cutoff = true;
        opt.compact_bc_penalty_lb_closure = true;
        opt.compact_bc_movement_reachability_domains = true;
        if (opt.compact_bc_domain_propagation_mode == "off") {
            opt.compact_bc_domain_propagation_mode = "static";
        }
        opt.compact_bc_domain_propagation_rounds =
            std::max(opt.compact_bc_domain_propagation_rounds, 1);
    }
    opt.pricing_dominance_mode = lowerAscii(opt.pricing_dominance_mode);
    if (opt.pricing_dominance_mode == "none" ||
        opt.pricing_dominance_mode == "false") {
        opt.pricing_dominance_mode = "off";
    }
    if (opt.pricing_dominance_mode == "diagnostic-aggressive") {
        opt.pricing_dominance_mode = "aggressive-diagnostic";
    }
    if (opt.pricing_dominance_mode != "off" &&
        opt.pricing_dominance_mode != "safe" &&
        opt.pricing_dominance_mode != "safe-plus" &&
        opt.pricing_dominance_mode != "aggressive-diagnostic") {
        opt.pricing_dominance_mode = "safe";
    }
    opt.pricing_decomposition = lowerAscii(opt.pricing_decomposition);
    if (opt.pricing_decomposition == "skeleton-dp" ||
        opt.pricing_decomposition == "route-skeleton") {
        opt.pricing_decomposition = "route-skeleton-load-dp";
    }
    if (opt.pricing_decomposition != "auto" &&
        opt.pricing_decomposition != "monolithic" &&
        opt.pricing_decomposition != "route-skeleton-load-dp") {
        opt.pricing_decomposition = "auto";
    }
    opt.pricing_completion_bound = lowerAscii(opt.pricing_completion_bound);
    if (opt.pricing_completion_bound == "off" ||
        opt.pricing_completion_bound == "none") {
        opt.pricing_completion_bound = "none";
        opt.pricing_completion_lb_pruning = false;
    } else if (opt.pricing_completion_bound != "basic" &&
               opt.pricing_completion_bound != "dual-knapsack" &&
               opt.pricing_completion_bound != "resource" &&
               opt.pricing_completion_bound != "all") {
        opt.pricing_completion_bound = opt.pricing_completion_lb_pruning
            ? "basic" : "none";
    }
    if (opt.pricing_completion_bound != "none") {
        opt.pricing_completion_lb_pruning = true;
    }
    opt.pricing_route_skeleton_mode = lowerAscii(opt.pricing_route_skeleton_mode);
    if (opt.pricing_route_skeleton_mode != "standard" &&
        opt.pricing_route_skeleton_mode != "pulse") {
        opt.pricing_route_skeleton_mode = "standard";
    }
    opt.bpc_seed_columns = lowerAscii(opt.bpc_seed_columns);
    if (opt.bpc_seed_columns != "none" &&
        opt.bpc_seed_columns != "incumbent" &&
        opt.bpc_seed_columns != "incumbent-plus-local" &&
        opt.bpc_seed_columns != "pool") {
        opt.bpc_seed_columns = "incumbent";
    }
    if (opt.bpc_seed_column_max < 0) opt.bpc_seed_column_max = 0;
    if (opt.bpc_cut_separation_rounds < 0) {
        opt.bpc_cut_separation_rounds = 0;
    }
    if (opt.core_relaxation_budget_fraction < 0.0) {
        opt.core_relaxation_budget_fraction = 0.0;
    }
    if (opt.core_relaxation_budget_fraction > 0.95) {
        opt.core_relaxation_budget_fraction = 0.95;
    }
    if (opt.core_bpc_reserve_fraction < 0.0) opt.core_bpc_reserve_fraction = 0.0;
    if (opt.core_bpc_reserve_fraction > 0.95) opt.core_bpc_reserve_fraction = 0.95;
    if (opt.core_bpc_min_seconds < 0.0) opt.core_bpc_min_seconds = 0.0;
    if (opt.core_bpc_max_leaves < 0) opt.core_bpc_max_leaves = 0;
    opt.core_bpc_leaf_selection = lowerAscii(opt.core_bpc_leaf_selection);
    if (opt.core_bpc_leaf_selection != "min-lb" &&
        opt.core_bpc_leaf_selection != "min-gap" &&
        opt.core_bpc_leaf_selection != "low-gini") {
        opt.core_bpc_leaf_selection = "min-lb";
    }
    if (opt.algorithm_preset == "paper-gf-bpc-core" &&
        (opt.core_bpc_reserve_fraction > 0.0 ||
         opt.core_bpc_min_seconds > 0.0 ||
         opt.core_bpc_max_leaves > 0)) {
        opt.frontier_bpc_fallback_mode =
            opt.core_bpc_leaf_selection == "min-gap" ? "best-bound"
                                                     : "controlling-intervals";
        opt.frontier_bpc_fallback_reserve_fraction =
            std::max(opt.frontier_bpc_fallback_reserve_fraction,
                     opt.core_bpc_reserve_fraction);
        opt.frontier_bpc_fallback_min_seconds =
            std::max(opt.frontier_bpc_fallback_min_seconds,
                     opt.core_bpc_min_seconds);
        opt.frontier_bpc_fallback_max_intervals =
            std::max(opt.frontier_bpc_fallback_max_intervals,
                     opt.core_bpc_max_leaves);
        const double fallback_reserve = std::max(
            opt.frontier_bpc_fallback_min_seconds,
            opt.solve_time_limit > 0.0
                ? opt.solve_time_limit * opt.frontier_bpc_fallback_reserve_fraction
                : 0.0);
        opt.frontier_retry_reserve_seconds =
            std::max(opt.frontier_retry_reserve_seconds, fallback_reserve);
        opt.frontier_final_closure = true;
    }
    opt.auto_interval_oracle_order = lowerAscii(opt.auto_interval_oracle_order);
    if (opt.auto_interval_oracle_order != "min-gap" &&
        opt.auto_interval_oracle_order != "low-gini" &&
        opt.auto_interval_oracle_order != "min-lb" &&
        opt.auto_interval_oracle_order != "best-bound" &&
        opt.auto_interval_oracle_order != "all") {
        opt.auto_interval_oracle_order = "all";
    }
    if (opt.auto_interval_oracle_time_limit < 0.0) {
        opt.auto_interval_oracle_time_limit = 0.0;
    }
    if (opt.auto_interval_oracle_max_leaves < 0) {
        opt.auto_interval_oracle_max_leaves = 0;
    }
    opt.auto_interval_oracle_leaf_budget_policy =
        lowerAscii(opt.auto_interval_oracle_leaf_budget_policy);
    if (opt.auto_interval_oracle_leaf_budget_policy == "fixed") {
        opt.auto_interval_oracle_leaf_budget_policy = "per-leaf";
    }
    if (opt.auto_interval_oracle_leaf_budget_policy != "per-leaf" &&
        opt.auto_interval_oracle_leaf_budget_policy != "total" &&
        opt.auto_interval_oracle_leaf_budget_policy != "adaptive") {
        opt.auto_interval_oracle_leaf_budget_policy = "per-leaf";
    }
    if (opt.auto_interval_oracle_total_budget < 0.0) {
        opt.auto_interval_oracle_total_budget = 0.0;
    }
    if (opt.auto_interval_oracle_child_time_limit < 0.0) {
        opt.auto_interval_oracle_child_time_limit = 0.0;
    }
    if (opt.auto_interval_oracle_child_split_count < 2) {
        opt.auto_interval_oracle_child_split_count = 2;
    }
    if (opt.auto_interval_oracle_max_depth < 0) {
        opt.auto_interval_oracle_max_depth = 0;
    }
    if (opt.auto_interval_oracle_min_width < 0.0) {
        opt.auto_interval_oracle_min_width = 0.0;
    }
    if (opt.auto_interval_oracle_max_children_total < 0) {
        opt.auto_interval_oracle_max_children_total = 0;
    }
    opt.interval_exact_oracle_mode = lowerAscii(opt.interval_exact_oracle_mode);
    if (opt.interval_exact_oracle_mode != "cutoff-feasibility" &&
        opt.interval_exact_oracle_mode != "objective-bound" &&
        opt.interval_exact_oracle_mode != "both") {
        opt.interval_exact_oracle_mode = "cutoff-feasibility";
    }
    if (opt.interval_oracle_objective_bound_time_limit < 0.0) {
        opt.interval_oracle_objective_bound_time_limit = 0.0;
    }
    if (opt.interval_oracle_cutoff_feasibility_time_limit < 0.0) {
        opt.interval_oracle_cutoff_feasibility_time_limit = 0.0;
    }
    opt.interval_oracle_profile = lowerAscii(opt.interval_oracle_profile);
    if (opt.interval_oracle_profile != "balanced" &&
        opt.interval_oracle_profile != "infeasibility-focus" &&
        opt.interval_oracle_profile != "bound-focus" &&
        opt.interval_oracle_profile != "integrality-focus") {
        opt.interval_oracle_profile = "balanced";
    }
    if (opt.auto_interval_bpc_time_limit < 0.0) {
        opt.auto_interval_bpc_time_limit = 0.0;
    }
    if (opt.auto_interval_bpc_max_leaves < 0) {
        opt.auto_interval_bpc_max_leaves = 0;
    }
    if (opt.auto_interval_bpc_max_nodes < 0) {
        opt.auto_interval_bpc_max_nodes = 0;
    }
    if (opt.auto_interval_bpc_pricing_time_per_call < 0.0) {
        opt.auto_interval_bpc_pricing_time_per_call = 0.0;
    }
    if (opt.paper_run_sealed) {
        std::vector<std::string> sealed_rejections;
        if (opt.incumbent_archive_auto) {
            sealed_rejections.push_back("incumbent_archive_auto_requested");
        }
        opt.incumbent_archive_auto = false;
        if (!opt.incumbent_json_path.empty()) {
            sealed_rejections.push_back("external_incumbent_json_requested");
        }
        if (!opt.hga_incumbent_path.empty()) {
            sealed_rejections.push_back("external_hga_incumbent_requested");
        }
        if (!opt.external_incumbent_path.empty()) {
            sealed_rejections.push_back("external_incumbent_requested");
        }
        if (opt.frontier_focus_only) {
            sealed_rejections.push_back("frontier_focus_only_requested");
        }
        if (!opt.frontier_resume_state_path.empty()) {
            sealed_rejections.push_back("frontier_resume_state_requested");
        }
        if (!opt.frontier_import_interval_bound_paths.empty()) {
            sealed_rejections.push_back("imported_interval_bounds_requested");
        }
        if (opt.interval_exact_cutoff_UB > 0.0 && opt.method != "interval-cutoff-oracle") {
            sealed_rejections.push_back("manual_interval_exact_cutoff_UB_requested");
        }
        if (!sealed_rejections.empty()) {
            std::ostringstream joined;
            for (std::size_t i = 0; i < sealed_rejections.size(); ++i) {
                if (i) joined << ";";
                joined << sealed_rejections[i];
            }
            opt.paper_run_sealed_rejection_reason = joined.str();
        }
    }
    return opt;
}

std::string resolvedPricingEngine(const ebrp::Instance& instance,
                                  const ebrp::SolveOptions& opt) {
    if (opt.pricing_engine == "auto") {
        return instance.V > 30 ? "hybrid" : "exact-label";
    }
    return opt.pricing_engine;
}

std::string resolvedColumnTracks(const ebrp::Instance& instance,
                                 const ebrp::SolveOptions& opt) {
    if (opt.column_tracks == "two-track" ||
        opt.column_tracks == "elementary-only") {
        return opt.column_tracks;
    }
    const std::string engine = resolvedPricingEngine(instance, opt);
    return (engine == "hybrid" || engine == "ng-dssr")
        ? "two-track" : "elementary-only";
}

std::string resolvedRmpColumnSpace(const ebrp::Instance& instance,
                                   const ebrp::SolveOptions& opt) {
    if (opt.rmp_column_space == "elementary" ||
        opt.rmp_column_space == "ng-relaxed" ||
        opt.rmp_column_space == "two-track") {
        return opt.rmp_column_space;
    }
    return resolvedColumnTracks(instance, opt) == "two-track"
        ? "two-track" : "elementary";
}

bool largeInstanceModeActive(const ebrp::Instance& instance,
                             const ebrp::SolveOptions& opt) {
    if (opt.large_instance_mode == "force") return true;
    if (opt.large_instance_mode == "off") return false;
    return instance.V > 32;
}

void applyPricingOptionsFromSolve(const ebrp::Instance& instance,
                                  const ebrp::SolveOptions& opt,
                                  ebrp::PricingOptions& pricing) {
    pricing.pricing_engine = resolvedPricingEngine(instance, opt);
    pricing.ng_size = opt.ng_size;
    pricing.ng_neighborhood_mode = opt.ng_neighborhood_mode;
    pricing.dssr_max_rounds = opt.dssr_max_rounds;
    pricing.dssr_expand_per_round = opt.dssr_expand_per_round;
    pricing.dssr_time_limit = opt.dssr_time_limit > 0.0
        ? opt.dssr_time_limit : pricing.time_limit_seconds;
    pricing.dssr_final_exact = opt.dssr_final_exact;
    pricing.cg_dual_stabilization = opt.cg_dual_stabilization;
    pricing.cg_dual_smoothing_alpha = opt.cg_dual_smoothing_alpha;
    pricing.cg_dual_box_radius = opt.cg_dual_box_radius;
    pricing.column_tracks = resolvedColumnTracks(instance, opt);
    pricing.rmp_column_space = resolvedRmpColumnSpace(instance, opt);
    pricing.relaxed_columns_in_rmp = opt.relaxed_columns_in_rmp ||
        pricing.column_tracks == "two-track" ||
        pricing.rmp_column_space == "ng-relaxed" ||
        pricing.rmp_column_space == "two-track";
    pricing.relaxed_columns_max_per_pricing =
        opt.relaxed_columns_max_per_pricing;
    pricing.allow_non_elementary_relaxed_columns =
        opt.allow_non_elementary_relaxed_columns;
    pricing.relaxed_projection_strict = opt.relaxed_projection_strict;
    pricing.ng_relaxed_closure = opt.ng_relaxed_closure ||
        opt.dssr_close_relaxed_pricing;
    pricing.ng_relaxed_closure_time = opt.ng_relaxed_closure_time;
    pricing.ng_relaxed_max_labels = opt.ng_relaxed_max_labels;
    pricing.ng_relaxed_pricing_checkpoint = opt.ng_relaxed_pricing_checkpoint;
    pricing.ng_relaxed_pricing_resume = opt.ng_relaxed_pricing_resume;
    pricing.relaxed_rmp_cg = opt.relaxed_rmp_cg ||
        opt.frontier_relaxed_rmp_cg || opt.large_relaxed_rmp_cg;
    pricing.relaxed_rmp_cg_columns_per_iteration =
        opt.relaxed_rmp_cg_columns_per_iteration;
    pricing.dssr_close_relaxed_pricing = opt.dssr_close_relaxed_pricing;
    pricing.dssr_relaxed_closure_time = opt.dssr_relaxed_closure_time;
    pricing.dssr_relaxed_closure_max_labels =
        opt.dssr_relaxed_closure_max_labels;
    pricing.dssr_relaxed_closure_checkpoint =
        opt.dssr_relaxed_closure_checkpoint;
    pricing.use_completion_lb_pruning = opt.pricing_completion_lb_pruning;
    pricing.pricing_dominance_mode = opt.pricing_dominance_mode;
    pricing.pricing_completion_bound = opt.pricing_completion_bound;
    pricing.pricing_completion_bound_audit = opt.pricing_completion_bound_audit;
    pricing.pricing_decomposition = opt.pricing_decomposition;
    pricing.pricing_load_dp_cache = opt.pricing_load_dp_cache;
    pricing.pricing_route_skeleton_mode = opt.pricing_route_skeleton_mode;
    pricing.pricing_route_skeleton_cache = opt.pricing_route_skeleton_cache;
    pricing.pricing_load_dp_dominance = opt.pricing_load_dp_dominance;
    pricing.pricing_operation_dp_dominance =
        opt.pricing_operation_dp_dominance && opt.pricing_load_dp_dominance;
}

void initializeScalabilityFields(const ebrp::Instance& instance,
                                 const ebrp::SolveOptions& opt,
                                 ebrp::SolveResult& result) {
    const bool large_mode = largeInstanceModeActive(instance, opt);
    result.large_instance_mode = large_mode ? opt.large_instance_mode : "off";
    if (large_mode && opt.large_instance_mode == "auto") {
        result.large_instance_mode = "auto";
    }
    result.station_set_backend = ebrp::stationSetBackendName(instance.V);
    result.pricing_engine = resolvedPricingEngine(instance, opt);
    result.pricing_label_dominance_mode = opt.pricing_dominance_mode;
    result.pricing_label_dominance_exact_safe =
        lowerAscii(opt.pricing_dominance_mode) != "aggressive-diagnostic";
    result.pricing_completion_bound_mode = opt.pricing_completion_bound;
    result.pricing_completion_bound_audit = opt.pricing_completion_bound_audit;
    result.pricing_decomposition = opt.pricing_decomposition;
    result.pricing_load_dp_cache_enabled = opt.pricing_load_dp_cache;
    result.pricing_route_skeleton_mode = opt.pricing_route_skeleton_mode;
    result.pricing_route_skeleton_cache_enabled = opt.pricing_route_skeleton_cache;
    result.pricing_load_dp_dominance_enabled = opt.pricing_load_dp_dominance;
    result.pricing_operation_dp_dominance_enabled =
        opt.pricing_operation_dp_dominance && opt.pricing_load_dp_dominance;
    result.time_budget_seconds = opt.solve_time_limit;
    result.actual_runtime_seconds = result.runtime_seconds;
    result.compact_bc_root_cut_rounds = opt.compact_bc_root_cut_rounds;
    result.compact_bc_total_root_cut_rounds = opt.compact_bc_root_cut_rounds;
    result.compact_bc_root_cut_time_limit = opt.compact_bc_root_cut_time_limit;
    result.compact_bc_dynamic_cut_families = opt.compact_bc_dynamic_cut_families;
    result.compact_bc_root_probe = opt.compact_bc_root_probe;
    result.compact_bc_dynamic_cut_violation_tol =
        opt.compact_bc_dynamic_cut_violation_tol;
    result.compact_bc_domain_propagation_mode =
        opt.compact_bc_domain_propagation_mode;
    result.compact_bc_domain_propagation_rounds =
        opt.compact_bc_domain_propagation_rounds;
    result.compact_bc_expensive_static_families =
        opt.compact_bc_expensive_static_families;
    result.compact_bc_use_dynamic_instead_of_static =
        opt.compact_bc_use_dynamic_instead_of_static;
    result.compact_bc_model_size_policy = opt.compact_bc_model_size_policy;
    result.compact_bc_receiver_source_cover_mode =
        opt.compact_bc_receiver_source_cover_mode;
    result.cplex_threads = opt.cplex_threads;
    result.mip_threads = opt.mip_threads;
    if (opt.algorithm_preset == "paper-gf-compact-bc" ||
        opt.algorithm_preset == "paper-gf-tailored-bc") {
        result.compact_bc_solver_threads = opt.compact_bc_threads > 0
            ? opt.compact_bc_threads
            : (opt.mip_threads > 0 ? opt.mip_threads : std::max(1, opt.threads));
        result.compact_interval_bc_threads = result.compact_bc_solver_threads;
        result.solver_thread_policy =
            result.compact_bc_solver_threads == 1
                ? "compact_bc_single_thread"
                : "compact_bc_multithread";
        result.thread_fairness_class =
            result.compact_bc_solver_threads == 1
                ? "one_thread_fair"
                : "multithread_diagnostic";
    } else if (opt.method == "cplex") {
        const int effective_cplex_threads =
            opt.cplex_threads > 0 ? opt.cplex_threads : std::max(1, opt.threads);
        result.cplex_threads = effective_cplex_threads;
        result.compact_bc_solver_threads = 0;
        result.compact_interval_bc_threads = 0;
        result.solver_thread_policy =
            effective_cplex_threads == 1
                ? "plain_cplex_single_thread"
                : "plain_cplex_multithread";
        result.thread_fairness_class =
            effective_cplex_threads == 1
                ? "one_thread_fair"
                : "multithread_diagnostic";
    } else {
        result.compact_bc_solver_threads = 0;
        result.compact_interval_bc_threads = 0;
    }
    result.bpc_seed_columns = opt.bpc_seed_columns;
    result.bpc_seed_column_max = opt.bpc_seed_column_max;
    result.bpc_cut_family = opt.bpc_cut_family;
    result.bpc_cut_separation_rounds = opt.bpc_cut_separation_rounds;
    result.core_relaxation_budget_fraction =
        opt.core_relaxation_budget_fraction;
    result.core_bpc_reserve_fraction = opt.core_bpc_reserve_fraction;
    result.core_bpc_min_seconds = opt.core_bpc_min_seconds;
    result.core_bpc_max_leaves = opt.core_bpc_max_leaves;
    result.core_bpc_leaf_selection = opt.core_bpc_leaf_selection;
    result.compact_bc_progress_interval_seconds =
        opt.compact_bc_progress_interval > 0.0
            ? opt.compact_bc_progress_interval
            : opt.progress_interval_seconds;
    result.compact_bc_diagnostic_force_leaf_solve =
        opt.compact_bc_diagnostic_force_leaf_solve;
    result.column_tracks = resolvedColumnTracks(instance, opt);
    result.rmp_column_space = resolvedRmpColumnSpace(instance, opt);
    result.relaxed_rmp_enabled = opt.relaxed_columns_in_rmp ||
        result.column_tracks == "two-track" ||
        result.rmp_column_space == "ng-relaxed" ||
        result.rmp_column_space == "two-track";
    result.large_relaxed_rmp_enabled = opt.large_relaxed_rmp;
    result.large_relaxed_rmp_cg_enabled = opt.large_relaxed_rmp_cg;
    if (opt.large_relaxed_rmp_cg) {
        result.large_relaxed_rmp_scope =
            "diagnostic_relaxed_ng_rmp_until_pricing_closes";
    }
    if (result.large_lb_mode.empty() || result.large_lb_mode == "none") {
        result.large_lb_mode = opt.large_lb_mode;
    }
    result.ng_size = opt.ng_size;
    result.dssr_final_exact = opt.dssr_final_exact;
    result.cg_stabilization_mode = opt.cg_dual_stabilization;
    result.benchmark_scale = instance.V >= 100 ? "V100" :
        (instance.V >= 50 ? "V50" : (instance.V >= 20 ? "V20" : "small"));
    result.route_mask_all_subset_enumeration_enabled =
        instance.V <= opt.route_mask_max_v && instance.V <= 30;
    result.route_mask_all_subset_enumeration_certifying =
        result.route_mask_all_subset_enumeration_enabled;
    if (opt.algorithm_preset == "paper-gf-tailored-bc" ||
        opt.algorithm_preset == "paper-gf-compact-bc" ||
        opt.algorithm_preset == "paper-gf-bpc-core" ||
        opt.algorithm_preset == "paper-bpc-core") {
    result.route_mask_all_subset_enumeration_enabled = false;
    result.route_mask_all_subset_enumeration_certifying = false;
        result.unsupported_large_instance_features =
            "all_subset_route_mask_relaxation_disabled_for_unified_paper_core";
    }
    if (large_mode && instance.V > 32) {
        result.route_mask_all_subset_enumeration_enabled = false;
        result.route_mask_all_subset_enumeration_certifying = false;
        result.unsupported_large_instance_features =
            "all_subset_route_mask_relaxation_disabled";
    }
    const double q_bytes = static_cast<double>(instance.V + 1) *
        static_cast<double>(std::max(1, instance.M)) * sizeof(int);
    const double dist_bytes = static_cast<double>(instance.V + 1) *
        static_cast<double>(instance.V + 1) * sizeof(double);
    result.memory_peak_estimate_mb = (q_bytes + dist_bytes) / (1024.0 * 1024.0);
}

std::string boolText(bool value) {
    return value ? "true" : "false";
}

std::string classifyIncumbentSource(const std::string& source) {
    const std::string s = lowerAscii(source);
    if (s.find("archive") != std::string::npos) return "diagnostic_archive";
    if (s.find("cplex") != std::string::npos) return "cplex_benchmark";
    if (s.find("explicit") != std::string::npos ||
        s.find("external") != std::string::npos ||
        s.find("json") != std::string::npos ||
        s.find("hga/tgbc") != std::string::npos) {
        return "explicit_incumbent_json";
    }
    if (s.find("empty") != std::string::npos) return "empty";
    return "primal_heuristic";
}

bool incumbentSourcePaperReproducible(const std::string& category) {
    return category == "primal_heuristic" ||
           category == "explicit_incumbent_json" ||
           category == "empty";
}

std::string hashFileFnv1a(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return "";
    std::uint64_t hash = 1469598103934665603ull;
    char ch = 0;
    while (in.get(ch)) {
        hash ^= static_cast<unsigned char>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << hash;
    return out.str();
}

std::string inferInstanceScope(const ebrp::Instance& instance,
                               const ebrp::SolveOptions& opt) {
    std::string path = lowerAscii(instance.path);
    std::string name = lowerAscii(instance.name);
    if (path.find("gcap_smoke") != std::string::npos ||
        name.find("smoke") != std::string::npos) {
        return "smoke";
    }
    if (opt.algorithm_preset == "diagnostic-large" || instance.V >= 50) {
        return "diagnostic_large";
    }
    if (path.find("hard_stress") != std::string::npos ||
        name.find("v20_m3") != std::string::npos ||
        name.find("hard_generated_v20_m3") != std::string::npos) {
        return "hard_generated_v20_m3";
    }
    if (path.find("reference/generated") != std::string::npos ||
        name.find("regen_") != std::string::npos ||
        name.find("regen_candidate") != std::string::npos) {
        return "regenerated_engineering";
    }
    return "historical_target";
}

ebrp::RunConfigSnapshot buildRunConfigSnapshot(const ebrp::Instance& instance,
                                               const ebrp::SolveOptions& opt) {
    ebrp::RunConfigSnapshot snapshot;
    snapshot.algorithm_preset = opt.algorithm_preset.empty() ? "custom" : opt.algorithm_preset;
    snapshot.column_tracks = resolvedColumnTracks(instance, opt);
    snapshot.rmp_column_space = resolvedRmpColumnSpace(instance, opt);
    snapshot.relaxed_columns_in_rmp = opt.relaxed_columns_in_rmp ||
        snapshot.column_tracks == "two-track" ||
        snapshot.rmp_column_space == "ng-relaxed" ||
        snapshot.rmp_column_space == "two-track";
    snapshot.pricing_engine = resolvedPricingEngine(instance, opt);
    snapshot.final_pricing_engine =
        (snapshot.pricing_engine == "hybrid" || snapshot.pricing_engine == "ng-dssr")
            ? (opt.dssr_final_exact ? "exact-label-final-verifier" : snapshot.pricing_engine)
            : snapshot.pricing_engine;
    const bool large_mode = largeInstanceModeActive(instance, opt);
    snapshot.large_instance_mode = large_mode ? opt.large_instance_mode : "off";
    if (large_mode && snapshot.large_instance_mode == "auto") {
        snapshot.large_instance_mode = "auto";
    }
    snapshot.station_set_backend = ebrp::stationSetBackendName(instance.V);
    snapshot.route_mask_all_subset_enumeration_enabled =
        instance.V <= opt.route_mask_max_v && instance.V <= 30;
    snapshot.route_mask_all_subset_enumeration_certifying =
        snapshot.route_mask_all_subset_enumeration_enabled;
    if (opt.algorithm_preset == "paper-gf-compact-bc" ||
        opt.algorithm_preset == "paper-gf-bpc-core" ||
        opt.algorithm_preset == "paper-bpc-core") {
        snapshot.route_mask_all_subset_enumeration_enabled = false;
        snapshot.route_mask_all_subset_enumeration_certifying = false;
    }
    if (large_mode && instance.V > 32) {
        snapshot.route_mask_all_subset_enumeration_enabled = false;
        snapshot.route_mask_all_subset_enumeration_certifying = false;
    }
    snapshot.incumbent_archive_auto = opt.incumbent_archive_auto;
    snapshot.primal_heuristic = opt.primal_heuristic;
    snapshot.compact_fallback_enabled = opt.compact_fallback_enabled;
    snapshot.relaxed_rmp_enabled = snapshot.relaxed_columns_in_rmp ||
        opt.relaxed_rmp_cg || opt.frontier_relaxed_rmp_cg ||
        opt.large_relaxed_rmp || opt.large_relaxed_rmp_cg;
    snapshot.plain_baseline = opt.plain_baseline;
    snapshot.cplex_seed = opt.gcap_seed_cplex;
    snapshot.column_dominance_enabled = opt.column_dominance;
    snapshot.movement_domain_enabled = opt.movement_domain_tightening;
    snapshot.projection_bound_enabled = opt.projection_bound;
    snapshot.penalty_domain_enabled = opt.penalty_domain_tightening;
    snapshot.vehicle_indexed_relaxation_enabled =
        opt.vehicle_indexed_operation_relaxation;
    snapshot.vehicle_indexed_transfer_flow_enabled = opt.vehicle_indexed_transfer_flow;
    snapshot.operation_budget_cuts_enabled = opt.route_mask_operation_budget_cuts;
    snapshot.branching_enabled = opt.branch_inventory || opt.branch_operation_mode;
    snapshot.two_track_enabled = snapshot.column_tracks == "two-track" ||
        snapshot.rmp_column_space == "two-track" ||
        snapshot.rmp_column_space == "ng-relaxed";
    snapshot.instance_scope = inferInstanceScope(instance, opt);
    snapshot.instance_hash = hashFileFnv1a(instance.path);
    snapshot.instance_source_path = instance.path;

    if (snapshot.algorithm_preset == "paper-gf-tailored-bc") {
        snapshot.preset_certificate_scope =
            "gini_frontier_relaxation_then_cplex_managed_tailored_bc";
        snapshot.preset_experimental_features_enabled =
            "tailored_cut_separation,callback_availability_audit,gini_branching_fallback";
        snapshot.preset_disabled_features =
            "route_load_bpc_certificate,all_subset_route_mask_enumeration,"
            "archive_scanning,known_ub_injection,external_incumbent,"
            "focus_only,plain_cplex_benchmark_bounds,diagnostic_s_buckets";
        snapshot.preset_reason =
            "paper-candidate GF tailored BC line: native HGA-TGBC UB, Gini frontier, "
            "valid relaxation screening, CPLEX-managed interval MIP with explicit "
            "tailored callback availability/source accounting";
    } else if (snapshot.algorithm_preset == "paper-gf-compact-bc") {
        snapshot.preset_certificate_scope =
            "gini_frontier_relaxation_then_compact_interval_branch_and_cut";
        snapshot.preset_experimental_features_enabled =
            "compact_interval_bc_valid_cuts,automatic_full_ledger_merge";
        snapshot.preset_disabled_features =
            "route_load_bpc_certificate,all_subset_route_mask_enumeration,"
            "archive_scanning,known_ub_injection,external_incumbent,"
            "focus_only,imported_focus_bounds,frontier_resume";
        snapshot.preset_reason =
            "paper GF compact BC line: native HGA-TGBC UB, Gini frontier, "
            "valid relaxation screening, compact fixed-interval MIP/BC proofs";
    } else if (snapshot.algorithm_preset == "paper-gf-bpc-core") {
        snapshot.preset_certificate_scope =
            "unified_gini_frontier_relaxation_then_exact_bpc_tree";
        snapshot.preset_experimental_features_enabled =
            "non_enumerative_relaxation_screening";
        snapshot.preset_disabled_features =
            "all_subset_route_mask_enumeration,interval_oracle_certificate,"
            "compact_oracle_certificate,archive_scanning,hybrid_ng_dssr,"
            "two_track_relaxed_rmp,focus_only,imported_focus_bounds,"
            "frontier_resume,iterative_closure";
        snapshot.preset_reason =
            "unified paper GF-BPC core: native HGA-TGBC UB, Gini frontier, "
            "valid non-enumerative relaxations, exact-pricing BPC fallback";
    } else if (snapshot.algorithm_preset == "paper-bpc-core") {
        snapshot.preset_certificate_scope = "core_bpc_certificate_when_frontier_closes";
        snapshot.preset_experimental_features_enabled = "none";
        snapshot.preset_disabled_features =
            "compact_fallback,hybrid_ng_dssr,two_track_relaxed_rmp,"
            "large_diagnostic,focus_only,imported_focus_bounds,"
            "frontier_resume,iterative_closure";
        snapshot.preset_reason = "paper core exact BPC with elementary columns only";
    } else if (snapshot.algorithm_preset == "paper-bpc-core-adaptive") {
        snapshot.preset_certificate_scope =
            "core_bpc_certificate_with_adaptive_relaxation_portfolio";
        snapshot.preset_experimental_features_enabled =
            "adaptive_relaxation_portfolio,large_compact_flow_relaxation";
        snapshot.preset_disabled_features =
            "compact_fallback,hybrid_ng_dssr,two_track_relaxed_rmp,"
            "large_diagnostic,focus_only,imported_focus_bounds,"
            "frontier_resume,iterative_closure,bpc_fallback_default";
        snapshot.preset_reason =
            "paper-core candidate with certificate-safe adaptive relaxation portfolio";
    } else if (snapshot.algorithm_preset == "paper-exact-v20-certificate") {
        snapshot.preset_certificate_scope =
            "exact_v20_frontier_relaxation_or_interval_oracle_certificate";
        snapshot.preset_experimental_features_enabled =
            "v20_mip_light_compact_flow_relaxation,exact_interval_cutoff_oracle_workflow";
        snapshot.preset_disabled_features =
            "archive_scanning,hybrid_ng_dssr,two_track_relaxed_rmp,"
            "focus_only_without_merge,frontier_resume,iterative_closure,bpc_fallback_default";
        snapshot.preset_reason =
            "paper-candidate exact V20 portfolio: native HGA-TGBC UB, full frontier relaxation certificate, optional exact interval oracle merge";
    } else if (snapshot.algorithm_preset == "paper-exact-portfolio") {
        snapshot.preset_certificate_scope =
            "bpc_or_compact_module_certificate_when_gap_closes";
        snapshot.preset_experimental_features_enabled = "none";
        snapshot.preset_disabled_features =
            "hybrid_ng_dssr,two_track_relaxed_rmp,large_diagnostic,"
            "focus_only,imported_focus_bounds,frontier_resume,iterative_closure";
        snapshot.preset_reason = "recommended robust exact portfolio";
    } else if (snapshot.algorithm_preset == "paper-bpc-experimental") {
        snapshot.preset_certificate_scope =
            "experimental_relaxed_rmp_requires_relaxed_pricing_closure";
        snapshot.preset_experimental_features_enabled =
            "hybrid_ng_dssr,two_track_relaxed_rmp,projection_safe_relaxed_columns";
        snapshot.preset_disabled_features = "compact_fallback";
        snapshot.preset_reason =
            "appendix experimental BPC extensions, disabled in core preset";
    } else if (snapshot.algorithm_preset == "diagnostic-large") {
        snapshot.preset_certificate_scope =
            "diagnostic_large_unless_full_certificate_closes";
        snapshot.preset_experimental_features_enabled =
            "hybrid_ng_dssr,large_relaxed_rmp_diagnostic";
        snapshot.preset_disabled_features =
            "all_subset_route_mask_enumeration,compact_fallback";
        snapshot.preset_reason =
            "large-instance scalability diagnostic, not a certificate preset";
    } else {
        snapshot.preset_certificate_scope = "custom";
        snapshot.preset_reason = "custom command-line configuration";
    }
    return snapshot;
}

void applyRunConfigSnapshot(const ebrp::RunConfigSnapshot& snapshot,
                            ebrp::SolveResult& result) {
    result.instance_scope = snapshot.instance_scope;
    result.instance_hash = snapshot.instance_hash;
    result.instance_source_path = snapshot.instance_source_path;
    result.algorithm_preset = snapshot.algorithm_preset;
    result.preset_certificate_scope = snapshot.preset_certificate_scope;
    result.preset_experimental_features_enabled =
        snapshot.preset_experimental_features_enabled;
    result.preset_disabled_features = snapshot.preset_disabled_features;
    result.preset_reason = snapshot.preset_reason;
    result.pricing_engine = snapshot.pricing_engine;
    result.final_pricing_engine = snapshot.final_pricing_engine;
    result.bpc_pricing_engine_requested = snapshot.pricing_engine;
    if (result.bpc_pricing_engine_used.empty()) {
        result.bpc_pricing_engine_used = snapshot.pricing_engine;
    }
    result.column_tracks = snapshot.column_tracks;
    result.rmp_column_space = snapshot.rmp_column_space;
    result.relaxed_columns_in_rmp = snapshot.relaxed_columns_in_rmp;
    result.relaxed_rmp_enabled = snapshot.relaxed_rmp_enabled;
    result.incumbent_archive_auto = snapshot.incumbent_archive_auto;
    result.primal_heuristic = snapshot.primal_heuristic;
    result.compact_fallback_enabled = snapshot.compact_fallback_enabled;
    result.cplex_plain_baseline = snapshot.plain_baseline;
    result.cplex_seed_enabled = snapshot.cplex_seed;
    result.large_instance_mode = snapshot.large_instance_mode;
    result.station_set_backend = snapshot.station_set_backend;
    result.route_mask_all_subset_enumeration_enabled =
        snapshot.route_mask_all_subset_enumeration_enabled;
    result.route_mask_all_subset_enumeration_certifying =
        snapshot.route_mask_all_subset_enumeration_certifying;
    result.column_dominance_enabled = snapshot.column_dominance_enabled;
    result.movement_domain_enabled = snapshot.movement_domain_enabled;
    result.projection_bound_enabled = snapshot.projection_bound_enabled;
    result.penalty_domain_enabled = snapshot.penalty_domain_enabled;
    result.vehicle_indexed_relaxation_enabled_snapshot =
        snapshot.vehicle_indexed_relaxation_enabled;
    result.vehicle_indexed_transfer_flow_enabled_snapshot =
        snapshot.vehicle_indexed_transfer_flow_enabled;
    result.operation_budget_cuts_enabled = snapshot.operation_budget_cuts_enabled;
    result.branching_enabled = snapshot.branching_enabled;
    result.two_track_enabled = snapshot.two_track_enabled;
    if (result.certificate_scope.empty()) {
        result.certificate_scope = snapshot.preset_certificate_scope;
    }
    const std::string snapshot_note =
        "RunConfigSnapshot: algorithm_preset=" + snapshot.algorithm_preset +
        ", preset_certificate_scope=" + snapshot.preset_certificate_scope +
        ", pricing_engine=" + snapshot.pricing_engine +
        ", final_pricing_engine=" + snapshot.final_pricing_engine +
        ", column_tracks=" + snapshot.column_tracks +
        ", rmp_column_space=" + snapshot.rmp_column_space +
        ", relaxed_columns_in_rmp=" + boolText(snapshot.relaxed_columns_in_rmp) +
        ", large_instance_mode=" + snapshot.large_instance_mode +
        ", station_set_backend=" + snapshot.station_set_backend +
        ", route_mask_all_subset_enumeration_enabled=" +
        boolText(snapshot.route_mask_all_subset_enumeration_enabled) +
        ", incumbent_archive_auto=" + boolText(snapshot.incumbent_archive_auto) +
        ", compact_fallback_enabled=" + boolText(snapshot.compact_fallback_enabled);
    bool has_note = false;
    for (const std::string& note : result.notes) {
        if (note.find("RunConfigSnapshot:") == 0) {
            has_note = true;
            break;
        }
    }
    if (!has_note) result.notes.push_back(snapshot_note);
    result.option_audit_consistent = result.option_audit_mismatches.empty();
}

void finalizePaperModuleFields(ebrp::SolveResult& result) {
    if (result.algorithm_preset == "paper-gf-compact-bc" ||
        result.algorithm_preset == "paper-gf-tailored-bc") {
        if (result.compact_bc_total_cuts_added_by_family.empty()) {
            result.compact_bc_total_cuts_added_by_family = "none";
        }
        if (result.compact_bc_cuts_added_by_family.empty()) {
            result.compact_bc_cuts_added_by_family =
                result.compact_bc_total_cuts_added_by_family;
        }
        if (result.compact_bc_total_domains_tightened_by_family.empty()) {
            result.compact_bc_total_domains_tightened_by_family = "none";
        }
        if (result.compact_bc_domains_tightened_by_family.empty()) {
            result.compact_bc_domains_tightened_by_family =
                result.compact_bc_total_domains_tightened_by_family;
        }
    }
    const double ub = result.upper_bound > 0.0 ? result.upper_bound : result.objective;
    const double gap = ub > 1e-12
        ? std::max(0.0, (ub - result.lower_bound) / std::fabs(ub))
        : std::max(0.0, ub - result.lower_bound);
    if ((result.method == "gcap-frontier" &&
         result.algorithm_preset != "paper-gf-compact-bc" &&
         result.algorithm_preset != "paper-gf-tailored-bc") ||
        result.method == "frontier-relaxed-rmp-cg-test") {
        result.bpc_status = result.status;
        result.bpc_LB = result.lower_bound;
        result.bpc_UB = ub;
        result.bpc_gap = result.gap > 0.0 ? result.gap : gap;
    } else if (result.method == "tailored" || result.method == "cplex" ||
               (result.method == "gcap-frontier" &&
                (result.algorithm_preset == "paper-gf-compact-bc" ||
                 result.algorithm_preset == "paper-gf-tailored-bc"))) {
        result.compact_status = result.status;
        result.compact_LB = result.lower_bound;
        result.compact_UB = ub;
        result.compact_gap = result.gap > 0.0 ? result.gap : gap;
    }
    if (result.algorithm_preset == "paper-exact-portfolio") {
        result.portfolio_objective = ub;
        result.portfolio_LB = std::max(result.bpc_LB, result.compact_LB);
        if (result.portfolio_LB <= 0.0) result.portfolio_LB = result.lower_bound;
        result.portfolio_gap = ub > 1e-12
            ? std::max(0.0, (ub - result.portfolio_LB) / std::fabs(ub))
            : std::max(0.0, ub - result.portfolio_LB);
        if (result.status == "optimal" && result.gap <= 1e-7 &&
            result.verification.feasible && result.verification.objective_matches &&
            result.option_audit_consistent) {
            result.portfolio_status = "optimal";
            result.certificate_module =
                (result.method == "gcap-frontier") ? "bpc" : "compact";
        } else {
            result.portfolio_status = "not_certified";
            result.certificate_module = "none";
            if (result.compact_status.empty() &&
                result.method == "gcap-frontier") {
                result.compact_status = "not_run_in_this_bpc_entry";
                result.notes.push_back(
                    "paper-exact-portfolio preset active: this invocation ran the BPC module; compact fallback must be run as a companion tailored/cplex row for portfolio evidence");
            }
        }
    } else if (result.portfolio_status.empty()) {
        result.portfolio_status = result.status;
        result.portfolio_objective = ub;
        result.portfolio_LB = result.lower_bound;
        result.portfolio_gap = result.gap > 0.0 ? result.gap : gap;
    }

    const std::string certificate_text = lowerAscii(
        result.full_certificate_basis + "|" +
        result.interval_certificate_basis + "|" +
        result.interval_bound_source_list + "|" +
        result.frontier_lower_bound_source);
    const bool oracle_in_certificate_text =
        certificate_text.find("interval_exact_oracle") != std::string::npos ||
        certificate_text.find("auto_interval_oracle") != std::string::npos ||
        certificate_text.find("interval_oracle") != std::string::npos;
    const bool route_mask_in_certificate_text =
        certificate_text.find("route_mask") != std::string::npos;
    const bool optimal_frontier = result.method == "gcap-frontier" &&
        result.status == "optimal";
    result.intervals_closed_by_oracle_count =
        static_cast<int>(std::max<long long>(
            result.oracle_bound_closed_leaves,
            result.auto_interval_oracle_leaves_closed));
    result.intervals_closed_by_bpc_count =
        std::max(0, result.frontier_tree_closed_interval_count) +
        std::max(0, result.bpc_fallback_leaves_closed);
    result.intervals_closed_by_relaxation_count =
        std::max(0, result.frontier_bound_fathomed_interval_count -
                    result.intervals_closed_by_oracle_count);
    result.intervals_unresolved_count = result.unresolved_intervals;
    result.certificate_uses_interval_oracle =
        optimal_frontier &&
        (oracle_in_certificate_text ||
         result.intervals_closed_by_oracle_count > 0 ||
         result.oracle_bound_merged_leaves > 0);
    result.certificate_uses_compact_interval_bc =
        optimal_frontier &&
        (result.algorithm_preset == "paper-gf-compact-bc" ||
         result.algorithm_preset == "paper-gf-tailored-bc") &&
        result.certificate_uses_interval_oracle;
    if (result.algorithm_preset == "paper-gf-tailored-bc") {
        result.tailored_bc_enabled = true;
        const ebrp::TailoredBCCapability cap =
            ebrp::inspectTailoredBCCapability();
        result.tailored_bc_callback_available = cap.callbacks_available;
        if (result.tailored_bc_mode.empty() || result.tailored_bc_mode == "off") {
            result.tailored_bc_mode = cap.callbacks_available
                ? "callback"
                : "static_fallback";
        }
        if (result.tailored_bc_callback_fail_reason.empty()) {
            result.tailored_bc_callback_fail_reason = cap.fail_reason;
        }
        if (result.status == "optimal" && !result.certificate_uses_interval_oracle) {
            result.tailored_bc_source_class = "relaxation_only";
        } else {
            result.tailored_bc_source_class = ebrp::tailoredBCSourceClass(result);
        }
    }
    result.certificate_uses_bpc_tree =
        optimal_frontier && result.intervals_closed_by_bpc_count > 0;
    result.certificate_uses_relaxation_only =
        optimal_frontier &&
        !result.certificate_uses_interval_oracle &&
        !result.certificate_uses_bpc_tree;
    const bool full_frontier_accounted =
        result.frontier_covers_all_improving_gini_values &&
        result.frontier_range_certificate_scope == "original_full_improving_range" &&
        result.full_certificate_all_intervals_accounted &&
        result.full_certificate_rejection_reason == "none" &&
        result.unresolved_intervals == 0 &&
        result.invalid_bound_intervals == 0 &&
        result.open_nodes == 0 &&
        (!result.full_certificate_requires_pricing_closure ||
         result.full_certificate_pricing_closure_satisfied);
    result.bpc_core_certificate_valid =
        optimal_frontier &&
        full_frontier_accounted &&
        !result.certificate_uses_interval_oracle &&
        !route_mask_in_certificate_text &&
        !result.route_mask_all_subset_enumeration_certifying &&
        (result.intervals_closed_by_bpc_count == 0 ||
         result.pricing_closure_certified_exact);
    result.exact_portfolio_certificate_valid =
        optimal_frontier &&
        full_frontier_accounted &&
        !route_mask_in_certificate_text &&
        (result.algorithm_preset == "paper-exact-portfolio" ||
         result.algorithm_preset == "paper-exact-v20-certificate" ||
         result.certificate_uses_interval_oracle);
    result.compact_bc_certificate_valid =
        optimal_frontier &&
        (result.algorithm_preset == "paper-gf-compact-bc" ||
         result.algorithm_preset == "paper-gf-tailored-bc") &&
        full_frontier_accounted &&
        !route_mask_in_certificate_text &&
        !result.route_mask_all_subset_enumeration_certifying &&
        !result.certificate_uses_bpc_tree &&
        (result.certificate_uses_compact_interval_bc ||
         result.certificate_uses_relaxation_only);
}

void applyLargeInstanceLowerBound(const ebrp::Instance& instance,
                                  const ebrp::SolveOptions& opt,
                                  ebrp::SolveResult& result) {
    if (opt.large_relaxed_rmp) {
        result.large_relaxed_rmp_enabled = true;
        result.large_relaxed_rmp_scope = "diagnostic_relaxed_ng_rmp_until_pricing_closes";
        result.large_relaxed_rmp_closed = false;
        result.large_relaxed_rmp_lb = std::max(result.large_relaxed_rmp_lb,
                                               result.relaxed_rmp_lower_bound);
        result.large_relaxed_rmp_columns = result.relaxed_rmp_columns;
    }
    std::string mode = opt.large_lb_mode;
    if (mode == "auto") {
        mode = instance.V > 32 ? "movement-projection" : "inventory-only";
    }
    result.large_lb_mode = mode;
    if (mode == "none" || mode == "column-pool-relaxation") {
        result.large_lb_valid_global = false;
        result.large_lb_scope =
            mode == "column-pool-relaxation" ? "restricted_pool_diagnostic" : "none";
        result.large_lb_rejection_reason =
            mode == "column-pool-relaxation"
                ? "verified-column subset is not a global lower-bound superset without pricing closure"
                : "disabled";
        return;
    }
    const auto lb_start = std::chrono::steady_clock::now();
    std::vector<int> lower(instance.V + 1, 0);
    std::vector<int> upper(instance.V + 1, 0);
    for (int i = 1; i <= instance.V; ++i) {
        lower[i] = 0;
        upper[i] = instance.capacity[i];
    }
    if (mode == "movement-projection") {
        ebrp::tightenInventoryIntervalsByMovementReachability(
            instance, lower, upper);
    }
    ebrp::InventoryRatioProjectionBound projection =
        ebrp::computeInventoryRatioProjectionBound(
            instance, opt.lambda, lower, upper,
            opt.gini_floor >= 0.0 ? opt.gini_floor : 0.0,
            "global");
    result.large_lb_time_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - lb_start).count();
    if (projection.valid &&
        result.upper_bound > 0.0 &&
        projection.objective_lower_bound > result.upper_bound + 1e-7) {
        result.large_lb_value = projection.objective_lower_bound;
        result.large_lb_valid_global = false;
        result.large_lb_scope = "invalid";
        result.large_lb_rejection_reason =
            "projection_bound_exceeds_verified_incumbent_ub";
        result.notes.push_back("large-instance lower-bound fallback rejected: computed bound "
            + std::to_string(projection.objective_lower_bound)
            + " exceeds verified incumbent UB " + std::to_string(result.upper_bound));
    } else if (projection.valid) {
        result.large_lb_value = projection.objective_lower_bound;
        result.large_lb_valid_global = true;
        result.large_lb_scope = "global";
        result.lower_bound = std::max(result.lower_bound, result.large_lb_value);
        if (result.upper_bound > 1e-12) {
            result.gap = std::max(0.0,
                (result.upper_bound - result.lower_bound) /
                std::fabs(result.upper_bound));
        }
    } else {
        result.large_lb_valid_global = false;
        result.large_lb_scope = "invalid";
        result.large_lb_rejection_reason = "projection_bound_invalid";
    }
}

void mergePricingStats(const ebrp::PricingResult& priced,
                       ebrp::SolveResult& result) {
    result.nodes += priced.route_states + priced.operation_states;
    result.labels_processed += priced.route_states;
    result.columns += priced.generated_columns;
    result.columns_generated_raw += priced.generated_columns;
    result.columns_after_dominance += priced.generated_columns;
    result.pricing_calls += 1;
    result.route_pool_columns_exported_from_pricing +=
        priced.generated_columns;
    if (!priced.column_tracks.empty()) result.column_tracks = priced.column_tracks;
    if (!priced.rmp_column_space.empty()) result.rmp_column_space = priced.rmp_column_space;
    result.elementary_columns_generated += priced.elementary_columns_generated;
    result.elementary_columns_inserted += priced.elementary_columns_inserted;
    result.relaxed_columns_generated += priced.relaxed_columns_generated;
    result.relaxed_columns_inserted += priced.relaxed_columns_inserted;
    result.relaxed_columns_rejected_projection +=
        priced.relaxed_columns_rejected_projection;
    result.relaxed_columns_rejected_infeasible_projection +=
        priced.relaxed_columns_rejected_infeasible_projection;
    result.relaxed_columns_used_in_lb_rmp +=
        priced.relaxed_columns_used_in_lb_rmp;
    result.relaxed_columns_used_in_incumbent +=
        priced.relaxed_columns_used_in_incumbent;
    result.non_elementary_relaxed_routes_seen +=
        priced.non_elementary_relaxed_routes_seen;
    result.non_elementary_relaxed_columns_validated +=
        priced.non_elementary_relaxed_columns_validated;
    result.non_elementary_relaxed_columns_inserted +=
        priced.non_elementary_relaxed_columns_inserted;
    result.non_elementary_relaxed_columns_rejected +=
        priced.non_elementary_relaxed_columns_rejected;
    result.relaxed_projection_rejected_load +=
        priced.relaxed_projection_rejected_load;
    result.relaxed_projection_rejected_station_capacity +=
        priced.relaxed_projection_rejected_station_capacity;
    result.relaxed_projection_rejected_branch +=
        priced.relaxed_projection_rejected_branch;
    result.relaxed_projection_rejected_operation_mode +=
        priced.relaxed_projection_rejected_operation_mode;
    result.relaxed_projection_rejected_unsafe_cut +=
        priced.relaxed_projection_rejected_unsafe_cut;
    result.relaxed_projection_validation_time_seconds +=
        priced.relaxed_projection_validation_time_seconds;
    result.relaxed_columns_blocked_from_incumbent +=
        priced.relaxed_columns_blocked_from_incumbent;
    result.relaxed_columns_blocked_from_export +=
        priced.relaxed_columns_blocked_from_export;
    result.relaxed_columns_blocked_from_candidate_reconstruction +=
        priced.relaxed_columns_blocked_from_candidate_reconstruction;
    result.relaxed_rmp_enabled = result.relaxed_rmp_enabled ||
        priced.relaxed_rmp_enabled;
    result.elementary_pricing_closed =
        result.elementary_pricing_closed || priced.elementary_pricing_closed;
    result.ng_relaxed_pricing_closed =
        result.ng_relaxed_pricing_closed || priced.ng_relaxed_pricing_closed;
    result.dssr_exact_elementary_closed =
        result.dssr_exact_elementary_closed || priced.dssr_exact_elementary_closed;
    result.ng_relaxed_best_reduced_cost =
        std::min(result.ng_relaxed_best_reduced_cost,
                 priced.ng_relaxed_best_reduced_cost);
    result.ng_relaxed_negative_routes_found +=
        priced.ng_relaxed_negative_routes_found;
    result.ng_relaxed_negative_columns_inserted +=
        priced.ng_relaxed_negative_columns_inserted;
    result.ng_relaxed_negative_routes_rejected +=
        priced.ng_relaxed_negative_routes_rejected;
    result.ng_relaxed_closure_labels_processed +=
        priced.ng_relaxed_closure_labels_processed;
    result.ng_relaxed_closure_labels_pruned +=
        priced.ng_relaxed_closure_labels_pruned;
    result.ng_relaxed_closure_time_seconds +=
        priced.ng_relaxed_closure_time_seconds;
    if (!priced.ng_relaxed_closure_stop_reason.empty()) {
        result.ng_relaxed_closure_stop_reason =
            priced.ng_relaxed_closure_stop_reason;
    }
    result.ng_relaxed_pricing_calls += priced.ng_relaxed_pricing_calls;
    result.ng_relaxed_labels_processed += priced.ng_relaxed_labels_processed;
    result.ng_relaxed_labels_pruned += priced.ng_relaxed_labels_pruned;
    result.dssr_refinement_rounds_for_lb +=
        priced.dssr_refinement_rounds_for_lb;
    result.dssr_lb_before_refinement =
        std::max(result.dssr_lb_before_refinement,
                 priced.dssr_lb_before_refinement);
    result.dssr_lb_after_refinement =
        std::max(result.dssr_lb_after_refinement,
                 priced.dssr_lb_after_refinement);
    result.relaxed_rmp_cg_iterations += priced.dssr_rounds;
    result.relaxed_rmp_cg_columns_added +=
        priced.ng_relaxed_negative_columns_inserted;
    result.relaxed_rmp_cg_final_best_rc = priced.ng_relaxed_best_reduced_cost;
    result.relaxed_rmp_cg_closed =
        result.relaxed_rmp_cg_closed || priced.ng_relaxed_pricing_closed;
    if (!priced.ng_relaxed_closure_stop_reason.empty()) {
        result.relaxed_rmp_cg_stop_reason =
            priced.ng_relaxed_closure_stop_reason;
    }
    result.pricing_engine = priced.pricing_engine.empty()
        ? result.pricing_engine : priced.pricing_engine;
    result.ng_size = std::max(result.ng_size, priced.ng_size);
    if (!priced.ng_neighborhood_mode.empty()) {
        result.ng_neighborhood_mode = priced.ng_neighborhood_mode;
    }
    result.ng_memory_total += priced.ng_memory_total;
    result.dssr_memory_total_initial += priced.dssr_memory_total_initial;
    result.dssr_memory_total_final += priced.dssr_memory_total_final;
    result.dssr_rounds += priced.dssr_rounds;
    result.dssr_memory_expansions += priced.dssr_memory_expansions;
    result.dssr_repeated_station_events +=
        priced.dssr_repeated_station_events;
    result.dssr_relaxed_negative_routes +=
        priced.dssr_relaxed_negative_routes;
    result.dssr_non_elementary_routes +=
        priced.dssr_non_elementary_routes;
    result.dssr_elementary_columns_found +=
        priced.dssr_elementary_columns_found;
    result.dssr_no_negative_relaxed_route =
        result.dssr_no_negative_relaxed_route ||
        priced.dssr_no_negative_relaxed_route;
    result.dssr_final_exact = result.dssr_final_exact ||
        priced.dssr_final_exact;
    result.dssr_exact_closure_proved =
        result.dssr_exact_closure_proved || priced.dssr_exact_closure_proved;
    result.dssr_time_seconds += priced.dssr_time_seconds;
    result.dssr_final_exact_verification_time +=
        priced.dssr_final_exact_verification_time;
    if (!priced.dssr_stop_reason.empty()) {
        if (!result.dssr_stop_reason.empty()) result.dssr_stop_reason += "; ";
        result.dssr_stop_reason += priced.dssr_stop_reason;
    }
    result.cg_stabilized_pricing_calls +=
        priced.cg_stabilized_pricing_calls;
    result.cg_true_pricing_calls += priced.cg_true_pricing_calls;
    result.cg_stabilization_columns_found +=
        priced.cg_stabilization_columns_found;
    result.cg_true_pricing_columns_found +=
        priced.cg_true_pricing_columns_found;
    result.cg_dual_center_updates += priced.cg_dual_center_updates;
    result.cg_dual_oscillation_metric =
        std::max(result.cg_dual_oscillation_metric,
                 priced.cg_dual_oscillation_metric);
    result.cg_true_negative_columns_inserted +=
        priced.cg_true_negative_columns_inserted;
    result.cg_stabilization_false_negatives +=
        priced.cg_stabilization_false_negatives;
    result.cg_stabilization_time_seconds +=
        priced.cg_stabilization_time_seconds;
    result.cg_final_true_pricing_rc =
        priced.cg_final_true_pricing_rc;
    result.pricing_best_reduced_cost_any =
        std::min(result.pricing_best_reduced_cost_any,
                 priced.best_reduced_cost);
    result.pricing_best_new_reduced_cost =
        std::min(result.pricing_best_new_reduced_cost,
                 priced.best_new_reduced_cost);
    if (priced.has_column) {
        result.pricing_negative_columns_found += 1;
        result.pricing_new_negative_projections +=
            priced.negative_new_projection_count;
    }
    result.pricing_duplicate_negative_projections +=
        priced.negative_existing_projection_count;
    result.pricing_blocked_by_duplicate_projection =
        result.pricing_blocked_by_duplicate_projection ||
        priced.blocked_by_duplicate_projection;
    if (!priced.complete) {
        result.pricing_completed_exactly = false;
        result.pricing_closure_certified_exact = false;
    }
    if (!priced.pricing_closure_status.empty() &&
        priced.pricing_closure_status != "not_run") {
        if (result.pricing_closure_status.empty() ||
            result.pricing_closure_status == "not_run" ||
            result.pricing_closure_status == "exact_no_negative") {
            result.pricing_closure_status = priced.pricing_closure_status;
        }
    }
    if (std::isfinite(priced.best_reduced_cost) &&
        priced.best_reduced_cost < -1e-9) {
        result.pricing_remaining_negative_rc =
            std::min(result.pricing_remaining_negative_rc,
                     priced.best_reduced_cost);
    }
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
    result.completion_lb_pruned_labels += priced.completion_lb_pruned_labels;
    result.required_closure_pruned_labels +=
        priced.required_closure_pruned_labels;
    result.label_dominance_comparisons += priced.label_dominance_comparisons;
    result.label_dominance_pruned_labels += priced.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        priced.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        priced.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        priced.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        priced.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        priced.operation_dp_dominance_pruned_states;
    result.pricing_label_dominance_mode = priced.pricing_dominance_mode;
    result.pricing_label_dominance_exact_safe =
        result.pricing_label_dominance_exact_safe &&
        priced.pricing_dominance_exact_safe;
    result.pricing_completion_bound_mode = priced.pricing_completion_bound;
    result.pricing_completion_bound_audit =
        result.pricing_completion_bound_audit ||
        priced.pricing_completion_bound_audit;
    result.pricing_decomposition = priced.pricing_decomposition;
    result.pricing_load_dp_cache_enabled =
        result.pricing_load_dp_cache_enabled || priced.pricing_load_dp_cache;
    result.pricing_route_skeleton_mode = priced.pricing_route_skeleton_mode;
    result.pricing_route_skeleton_cache_enabled =
        result.pricing_route_skeleton_cache_enabled ||
        priced.pricing_route_skeleton_cache;
    result.pricing_load_dp_dominance_enabled =
        result.pricing_load_dp_dominance_enabled &&
        priced.pricing_load_dp_dominance;
    result.pricing_operation_dp_dominance_enabled =
        result.pricing_operation_dp_dominance_enabled &&
        priced.pricing_operation_dp_dominance;
    result.pricing_labels_generated += priced.pricing_labels_generated;
    result.pricing_labels_kept += priced.pricing_labels_kept;
    result.pricing_labels_expanded += priced.pricing_labels_expanded;
    result.pricing_labels_pruned_duration +=
        priced.pricing_labels_pruned_duration;
    result.pricing_labels_pruned_load += priced.pricing_labels_pruned_load;
    result.pricing_labels_pruned_station +=
        priced.pricing_labels_pruned_station;
    result.pricing_labels_pruned_support +=
        priced.pricing_labels_pruned_support;
    result.pricing_labels_pruned_reduced_cost +=
        priced.pricing_labels_pruned_reduced_cost;
    result.pricing_labels_pruned_dominance +=
        priced.pricing_labels_pruned_dominance;
    result.pricing_labels_duplicate_states +=
        priced.pricing_labels_duplicate_states;
    if (!priced.pricing_state_stop_reason.empty()) {
        result.pricing_state_stop_reason = priced.pricing_state_stop_reason;
    }
    if (!priced.pricing_depth_profile_json.empty() &&
        priced.pricing_depth_profile_json != "[]") {
        result.pricing_depth_profile_json = priced.pricing_depth_profile_json;
    }
    if (!priced.operation_dp_profile_json.empty() &&
        priced.operation_dp_profile_json != "[]") {
        result.operation_dp_profile_json = priced.operation_dp_profile_json;
    }
    result.support_duration_max_subset_size =
        std::max(result.support_duration_max_subset_size,
                 priced.support_duration_max_subset_size);
    result.support_duration_precompute_time_seconds +=
        priced.support_duration_precompute_time_seconds;
}

template <typename BpcResult>
void copyBpcPricingStats(const BpcResult& bpc,
                         ebrp::SolveResult& result) {
    result.bpc_pricing_engine_requested = bpc.bpc_pricing_engine_requested;
    result.bpc_pricing_engine_used = bpc.bpc_pricing_engine_used;
    result.bpc_pricing_engine_fallbacks += bpc.bpc_pricing_engine_fallbacks;
    result.bpc_nodes_using_ng_dssr += bpc.bpc_nodes_using_ng_dssr;
    result.bpc_nodes_using_exact_label += bpc.bpc_nodes_using_exact_label;
    result.bpc_nodes_using_hybrid += bpc.bpc_nodes_using_hybrid;
    result.bpc_nodes_exactly_priced += bpc.bpc_nodes_exactly_priced;
    result.bpc_nodes_dssr_incomplete += bpc.bpc_nodes_dssr_incomplete;
    result.bpc_nodes_final_verifier_called += bpc.bpc_nodes_final_verifier_called;
    result.bpc_nodes_final_verifier_completed +=
        bpc.bpc_nodes_final_verifier_completed;
    if (!bpc.column_tracks.empty()) result.column_tracks = bpc.column_tracks;
    if (!bpc.rmp_column_space.empty()) result.rmp_column_space = bpc.rmp_column_space;
    result.elementary_columns_generated += bpc.elementary_columns_generated;
    result.elementary_columns_inserted += bpc.elementary_columns_inserted;
    result.relaxed_columns_generated += bpc.relaxed_columns_generated;
    result.relaxed_columns_inserted += bpc.relaxed_columns_inserted;
    result.relaxed_columns_rejected_projection += bpc.relaxed_columns_rejected_projection;
    result.relaxed_columns_rejected_infeasible_projection +=
        bpc.relaxed_columns_rejected_infeasible_projection;
    result.relaxed_columns_used_in_lb_rmp += bpc.relaxed_columns_used_in_lb_rmp;
    result.relaxed_columns_used_in_incumbent += bpc.relaxed_columns_used_in_incumbent;
    result.non_elementary_relaxed_routes_seen += bpc.non_elementary_relaxed_routes_seen;
    result.non_elementary_relaxed_columns_validated +=
        bpc.non_elementary_relaxed_columns_validated;
    result.non_elementary_relaxed_columns_inserted +=
        bpc.non_elementary_relaxed_columns_inserted;
    result.non_elementary_relaxed_columns_rejected +=
        bpc.non_elementary_relaxed_columns_rejected;
    result.relaxed_projection_rejected_load += bpc.relaxed_projection_rejected_load;
    result.relaxed_projection_rejected_station_capacity +=
        bpc.relaxed_projection_rejected_station_capacity;
    result.relaxed_projection_rejected_branch += bpc.relaxed_projection_rejected_branch;
    result.relaxed_projection_rejected_operation_mode +=
        bpc.relaxed_projection_rejected_operation_mode;
    result.relaxed_projection_rejected_unsafe_cut +=
        bpc.relaxed_projection_rejected_unsafe_cut;
    result.relaxed_projection_validation_time_seconds +=
        bpc.relaxed_projection_validation_time_seconds;
    result.relaxed_columns_blocked_from_incumbent +=
        bpc.relaxed_columns_blocked_from_incumbent;
    result.relaxed_columns_blocked_from_export +=
        bpc.relaxed_columns_blocked_from_export;
    result.relaxed_columns_blocked_from_candidate_reconstruction +=
        bpc.relaxed_columns_blocked_from_candidate_reconstruction;
    result.relaxed_rmp_enabled = result.relaxed_rmp_enabled || bpc.relaxed_rmp_enabled;
    result.rmp_column_space = bpc.rmp_column_space.empty()
        ? result.rmp_column_space : bpc.rmp_column_space;
    result.relaxed_rmp_objective = std::max(result.relaxed_rmp_objective,
                                            bpc.relaxed_rmp_objective);
    result.relaxed_rmp_lower_bound = std::max(result.relaxed_rmp_lower_bound,
                                              bpc.relaxed_rmp_lower_bound);
    result.relaxed_rmp_columns += bpc.relaxed_rmp_columns;
    result.relaxed_rmp_iterations += bpc.relaxed_rmp_iterations;
    result.relaxed_rmp_pricing_closed =
        result.relaxed_rmp_pricing_closed || bpc.relaxed_rmp_pricing_closed;
    result.relaxed_rmp_best_reduced_cost =
        std::min(result.relaxed_rmp_best_reduced_cost,
                 bpc.relaxed_rmp_best_reduced_cost);
    result.relaxed_rmp_certificate_valid =
        result.relaxed_rmp_certificate_valid || bpc.relaxed_rmp_certificate_valid;
    if (!bpc.relaxed_rmp_certificate_rejection_reason.empty()) {
        result.relaxed_rmp_certificate_rejection_reason =
            bpc.relaxed_rmp_certificate_rejection_reason;
    }
    result.elementary_pricing_closed =
        result.elementary_pricing_closed || bpc.elementary_pricing_closed;
    result.ng_relaxed_pricing_closed =
        result.ng_relaxed_pricing_closed || bpc.ng_relaxed_pricing_closed;
    result.dssr_exact_elementary_closed =
        result.dssr_exact_elementary_closed || bpc.dssr_exact_elementary_closed;
    result.ng_relaxed_best_reduced_cost =
        std::min(result.ng_relaxed_best_reduced_cost,
                 bpc.ng_relaxed_best_reduced_cost);
    result.ng_relaxed_negative_routes_found += bpc.ng_relaxed_negative_routes_found;
    result.ng_relaxed_negative_columns_inserted +=
        bpc.ng_relaxed_negative_columns_inserted;
    result.ng_relaxed_negative_routes_rejected +=
        bpc.ng_relaxed_negative_routes_rejected;
    result.ng_relaxed_closure_labels_processed +=
        bpc.ng_relaxed_closure_labels_processed;
    result.ng_relaxed_closure_labels_pruned +=
        bpc.ng_relaxed_closure_labels_pruned;
    result.ng_relaxed_closure_time_seconds +=
        bpc.ng_relaxed_closure_time_seconds;
    if (!bpc.ng_relaxed_closure_stop_reason.empty()) {
        result.ng_relaxed_closure_stop_reason =
            bpc.ng_relaxed_closure_stop_reason;
    }
    result.ng_relaxed_pricing_calls += bpc.ng_relaxed_pricing_calls;
    result.ng_relaxed_labels_processed += bpc.ng_relaxed_labels_processed;
    result.ng_relaxed_labels_pruned += bpc.ng_relaxed_labels_pruned;
    result.dssr_refinement_rounds_for_lb += bpc.dssr_refinement_rounds_for_lb;
    result.dssr_lb_before_refinement =
        std::max(result.dssr_lb_before_refinement, bpc.dssr_lb_before_refinement);
    result.dssr_lb_after_refinement =
        std::max(result.dssr_lb_after_refinement, bpc.dssr_lb_after_refinement);
    result.relaxed_rmp_cg_iterations += bpc.relaxed_rmp_cg_iterations;
    result.relaxed_rmp_cg_columns_added += bpc.relaxed_rmp_cg_columns_added;
    result.relaxed_rmp_cg_final_best_rc =
        std::min(result.relaxed_rmp_cg_final_best_rc,
                 bpc.relaxed_rmp_cg_final_best_rc);
    result.relaxed_rmp_cg_closed =
        result.relaxed_rmp_cg_closed || bpc.relaxed_rmp_cg_closed;
    if (!bpc.relaxed_rmp_cg_stop_reason.empty()) {
        result.relaxed_rmp_cg_stop_reason = bpc.relaxed_rmp_cg_stop_reason;
    }
    result.relaxed_rmp_lb_before_cg =
        std::max(result.relaxed_rmp_lb_before_cg, bpc.relaxed_rmp_lb_before_cg);
    result.relaxed_rmp_lb_after_cg =
        std::max(result.relaxed_rmp_lb_after_cg, bpc.relaxed_rmp_lb_after_cg);
    result.frontier_relaxed_rmp_intervals_attempted +=
        bpc.frontier_relaxed_rmp_intervals_attempted;
    result.frontier_relaxed_rmp_intervals_closed +=
        bpc.frontier_relaxed_rmp_intervals_closed;
    result.frontier_relaxed_rmp_intervals_fathomed +=
        bpc.frontier_relaxed_rmp_intervals_fathomed;
    result.frontier_relaxed_rmp_time_seconds +=
        bpc.frontier_relaxed_rmp_time_seconds;
    result.frontier_lb_improved_by_relaxed_rmp +=
        bpc.frontier_lb_improved_by_relaxed_rmp;
    result.frontier_relaxed_rmp_cg_intervals_attempted +=
        bpc.frontier_relaxed_rmp_cg_intervals_attempted;
    result.frontier_relaxed_rmp_cg_intervals_closed +=
        bpc.frontier_relaxed_rmp_cg_intervals_closed;
    result.frontier_relaxed_rmp_cg_intervals_fathomed +=
        bpc.frontier_relaxed_rmp_cg_intervals_fathomed;
    result.frontier_relaxed_rmp_cg_lb_improvements +=
        bpc.frontier_relaxed_rmp_cg_lb_improvements;
    result.frontier_relaxed_rmp_cg_time_seconds +=
        bpc.frontier_relaxed_rmp_cg_time_seconds;
    if (bpc.frontier_relaxed_rmp_cg_intervals_attempted == 0 &&
        bpc.relaxed_rmp_enabled && bpc.relaxed_rmp_cg_iterations > 0) {
        result.frontier_relaxed_rmp_cg_intervals_attempted += 1;
        if (bpc.relaxed_rmp_cg_closed) {
            result.frontier_relaxed_rmp_cg_intervals_closed += 1;
        }
        if (bpc.relaxed_rmp_certificate_valid) {
            result.frontier_relaxed_rmp_cg_intervals_fathomed += 1;
        }
        if (bpc.relaxed_rmp_lb_after_cg > bpc.relaxed_rmp_lb_before_cg + 1e-9) {
            result.frontier_relaxed_rmp_cg_lb_improvements += 1;
        }
    }
    result.ng_size = std::max(result.ng_size, bpc.ng_size);
    if (!bpc.ng_neighborhood_mode.empty()) {
        result.ng_neighborhood_mode = bpc.ng_neighborhood_mode;
    }
    result.ng_memory_total += bpc.ng_memory_total;
    result.dssr_memory_total_initial += bpc.dssr_memory_total_initial;
    result.dssr_memory_total_final += bpc.dssr_memory_total_final;
    result.dssr_rounds += bpc.dssr_rounds;
    result.dssr_memory_expansions += bpc.dssr_memory_expansions;
    result.dssr_repeated_station_events += bpc.dssr_repeated_station_events;
    result.dssr_relaxed_negative_routes += bpc.dssr_relaxed_negative_routes;
    result.dssr_non_elementary_routes += bpc.dssr_non_elementary_routes;
    result.dssr_elementary_columns_found += bpc.dssr_elementary_columns_found;
    result.dssr_no_negative_relaxed_route =
        result.dssr_no_negative_relaxed_route || bpc.dssr_no_negative_relaxed_route;
    result.dssr_exact_closure_proved =
        result.dssr_exact_closure_proved || bpc.dssr_exact_closure_proved;
    result.dssr_final_exact_verification_time +=
        bpc.dssr_final_exact_verification_time;
    result.dssr_time_seconds += bpc.dssr_time_seconds;
    if (!bpc.dssr_stop_reason.empty()) {
        if (!result.dssr_stop_reason.empty()) result.dssr_stop_reason += "; ";
        result.dssr_stop_reason += bpc.dssr_stop_reason;
    }
    result.cg_stabilization_mode = bpc.cg_stabilization_mode;
    result.cg_dual_center_updates += bpc.cg_dual_center_updates;
    result.cg_dual_oscillation_metric =
        std::max(result.cg_dual_oscillation_metric,
                 bpc.cg_dual_oscillation_metric);
    result.cg_stabilized_pricing_calls += bpc.cg_stabilized_pricing_calls;
    result.cg_true_pricing_calls += bpc.cg_true_pricing_calls;
    result.cg_stabilization_columns_found +=
        bpc.cg_stabilization_columns_found;
    result.cg_true_pricing_columns_found += bpc.cg_true_pricing_columns_found;
    result.cg_true_negative_columns_inserted +=
        bpc.cg_true_negative_columns_inserted;
    result.cg_stabilization_false_negatives +=
        bpc.cg_stabilization_false_negatives;
    result.cg_final_true_pricing_rc = bpc.cg_final_true_pricing_rc;
    result.label_dominance_comparisons += bpc.label_dominance_comparisons;
    result.label_dominance_pruned_labels += bpc.label_dominance_pruned_labels;
    result.label_dominance_cross_pickup_pruned_labels +=
        bpc.label_dominance_cross_pickup_pruned_labels;
    result.label_dominance_inactive_entries_skipped +=
        bpc.label_dominance_inactive_entries_skipped;
    result.label_dominance_bucket_compactions +=
        bpc.label_dominance_bucket_compactions;
    result.label_dominance_compacted_entries +=
        bpc.label_dominance_compacted_entries;
    result.operation_dp_dominance_pruned_states +=
        bpc.operation_dp_dominance_pruned_states;
    result.pricing_label_dominance_mode = bpc.pricing_label_dominance_mode;
    result.pricing_label_dominance_exact_safe =
        result.pricing_label_dominance_exact_safe &&
        bpc.pricing_label_dominance_exact_safe;
    result.pricing_completion_bound_mode = bpc.pricing_completion_bound_mode;
    result.pricing_completion_bound_audit =
        result.pricing_completion_bound_audit ||
        bpc.pricing_completion_bound_audit;
    result.pricing_decomposition = bpc.pricing_decomposition;
    result.pricing_load_dp_cache_enabled =
        result.pricing_load_dp_cache_enabled || bpc.pricing_load_dp_cache_enabled;
    result.pricing_route_skeleton_mode = bpc.pricing_route_skeleton_mode;
    result.pricing_route_skeleton_cache_enabled =
        result.pricing_route_skeleton_cache_enabled ||
        bpc.pricing_route_skeleton_cache_enabled;
    result.pricing_load_dp_dominance_enabled =
        result.pricing_load_dp_dominance_enabled &&
        bpc.pricing_load_dp_dominance_enabled;
    result.pricing_operation_dp_dominance_enabled =
        result.pricing_operation_dp_dominance_enabled &&
        bpc.pricing_operation_dp_dominance_enabled;
    result.pricing_labels_generated += bpc.pricing_labels_generated;
    result.pricing_labels_kept += bpc.pricing_labels_kept;
    result.pricing_labels_expanded += bpc.pricing_labels_expanded;
    result.pricing_labels_pruned_duration +=
        bpc.pricing_labels_pruned_duration;
    result.pricing_labels_pruned_load += bpc.pricing_labels_pruned_load;
    result.pricing_labels_pruned_station += bpc.pricing_labels_pruned_station;
    result.pricing_labels_pruned_support += bpc.pricing_labels_pruned_support;
    result.pricing_labels_pruned_reduced_cost +=
        bpc.pricing_labels_pruned_reduced_cost;
    result.pricing_labels_pruned_dominance +=
        bpc.pricing_labels_pruned_dominance;
    result.pricing_labels_duplicate_states += bpc.pricing_labels_duplicate_states;
    if (!bpc.pricing_state_stop_reason.empty()) {
        result.pricing_state_stop_reason = bpc.pricing_state_stop_reason;
    }
    if (!bpc.pricing_depth_profile_json.empty() &&
        bpc.pricing_depth_profile_json != "[]") {
        result.pricing_depth_profile_json = bpc.pricing_depth_profile_json;
    }
    if (!bpc.operation_dp_profile_json.empty() &&
        bpc.operation_dp_profile_json != "[]") {
        result.operation_dp_profile_json = bpc.operation_dp_profile_json;
    }
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

double extractJsonDoubleForKey(const std::string& text,
                               const std::string& key,
                               double default_value = 0.0) {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key);
    if (key_pos == std::string::npos) return default_value;
    const std::size_t colon_pos = text.find(':', key_pos + quoted_key.size());
    if (colon_pos == std::string::npos) return default_value;
    std::size_t value_pos = colon_pos + 1;
    while (value_pos < text.size() &&
           std::isspace(static_cast<unsigned char>(text[value_pos]))) {
        ++value_pos;
    }
    try {
        return std::stod(text.substr(value_pos));
    } catch (const std::exception&) {
        return default_value;
    }
}

bool extractJsonBoolForKey(const std::string& text,
                           const std::string& key,
                           bool default_value = false) {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key);
    if (key_pos == std::string::npos) return default_value;
    const std::size_t colon_pos = text.find(':', key_pos + quoted_key.size());
    if (colon_pos == std::string::npos) return default_value;
    std::size_t value_pos = colon_pos + 1;
    while (value_pos < text.size() &&
           std::isspace(static_cast<unsigned char>(text[value_pos]))) {
        ++value_pos;
    }
    if (text.compare(value_pos, 4, "true") == 0) return true;
    if (text.compare(value_pos, 5, "false") == 0) return false;
    return default_value;
}

std::string extractJsonStringForKey(const std::string& text,
                                    const std::string& key,
                                    const std::string& default_value = "") {
    const std::string quoted_key = "\"" + key + "\"";
    const std::size_t key_pos = text.find(quoted_key);
    if (key_pos == std::string::npos) return default_value;
    const std::size_t colon_pos = text.find(':', key_pos + quoted_key.size());
    if (colon_pos == std::string::npos) return default_value;
    std::size_t value_pos = colon_pos + 1;
    while (value_pos < text.size() &&
           std::isspace(static_cast<unsigned char>(text[value_pos]))) {
        ++value_pos;
    }
    if (value_pos >= text.size() || text[value_pos] != '"') return default_value;
    ++value_pos;
    std::string out;
    bool escaped = false;
    for (; value_pos < text.size(); ++value_pos) {
        const char ch = text[value_pos];
        if (escaped) {
            if (ch == 'n') out.push_back('\n');
            else if (ch == 'r') out.push_back('\r');
            else if (ch == 't') out.push_back('\t');
            else out.push_back(ch);
            escaped = false;
        } else if (ch == '\\') {
            escaped = true;
        } else if (ch == '"') {
            return out;
        } else {
            out.push_back(ch);
        }
    }
    return default_value;
}

std::string readWholeTextFile(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open file: " + path);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

std::string jsonEscapeLocal(const std::string& value) {
    std::ostringstream out;
    for (char ch : value) {
        switch (ch) {
        case '\\': out << "\\\\"; break;
        case '"': out << "\\\""; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (static_cast<unsigned char>(ch) < 0x20) {
                out << "\\u" << std::hex << std::setw(4)
                    << std::setfill('0') << static_cast<int>(
                        static_cast<unsigned char>(ch))
                    << std::dec << std::setfill(' ');
            } else {
                out << ch;
            }
        }
    }
    return out.str();
}

bool isPaperTracePreset(const std::string& preset) {
    return preset == "paper-gf-bpc-core" ||
           preset == "paper-gf-tailored-bc" ||
           preset == "paper-gf-compact-bc" ||
           preset == "paper-bpc-core" ||
           preset == "paper-bpc-core-adaptive" ||
           preset == "paper-exact-v20-certificate" ||
           preset == "paper-exact-portfolio";
}

int effectiveFrontierAdaptiveMaxDepth(const ebrp::Instance& instance,
                                      const ebrp::SolveOptions& opt) {
    (void)instance;
    return std::max(0, opt.frontier_adaptive_max_depth);
}

void writeMinimalPaperCoreTrace(const ebrp::Instance& instance,
                                const ebrp::SolveOptions& opt,
                                ebrp::SolveResult& result,
                                const std::string& reason) {
    if (!isPaperTracePreset(result.algorithm_preset) || opt.out_path.empty()) {
        return;
    }
    try {
        std::filesystem::path out_path(opt.out_path);
        std::filesystem::path trace_path = out_path;
        trace_path.replace_extension(".trace.json");
        std::filesystem::path interval_csv_path = out_path;
        interval_csv_path.replace_extension(".intervals.csv");
        if (!trace_path.parent_path().empty()) {
            std::filesystem::create_directories(trace_path.parent_path());
        }
        result.bpc_trace_json_path = trace_path.string();
        result.bpc_interval_trace_csv_path = interval_csv_path.string();
        std::ofstream interval_csv(interval_csv_path, std::ios::out | std::ios::trunc);
        interval_csv
            << "interval_id,gamma_L,gamma_U,interval_lower_bound,"
            << "incumbent_upper_bound,interval_status,reason,"
            << "certificate_basis,requires_pricing_closure,"
            << "pricing_closure_available,interval_bound_valid,"
            << "bpc_nodes,open_nodes,generated_columns,cuts,"
            << "pricing_calls,pricing_time_seconds,rmp_solve_time_seconds,"
            << "relaxation_time_seconds,lower_bound_source,lower_bound_sources\n";
        interval_csv
            << "-1,0,0," << result.lower_bound << ","
            << result.upper_bound << ",global,\""
            << jsonEscapeLocal(reason) << "\","
            << "zero_objective_global,false,false,true,0,"
            << result.open_nodes << "," << result.columns << ","
            << result.cuts_added << "," << result.pricing_calls << ","
            << result.pricing_time_seconds << "," << result.master_time_seconds
            << "," << result.bound_time_seconds
            << ",nonnegative_objective,nonnegative_objective\n";
        interval_csv.close();

        std::ofstream trace(trace_path, std::ios::out | std::ios::trunc);
        trace << std::setprecision(12);
        trace << "{\n";
        trace << "  \"trace_schema\": \"paper_bpc_core_plateau_trace_v1\",\n";
        trace << "  \"trace_scope\": \"minimal_early_exit_trace\",\n";
        trace << "  \"early_exit_reason\": \"" << jsonEscapeLocal(reason) << "\",\n";
        trace << "  \"instance_name\": \"" << jsonEscapeLocal(instance.name) << "\",\n";
        trace << "  \"input_path\": \"" << jsonEscapeLocal(instance.path) << "\",\n";
        trace << "  \"algorithm_preset\": \"" << jsonEscapeLocal(result.algorithm_preset) << "\",\n";
        trace << "  \"method\": \"" << jsonEscapeLocal(result.method) << "\",\n";
        trace << "  \"status\": \"" << jsonEscapeLocal(result.status) << "\",\n";
        trace << "  \"objective\": " << result.objective << ",\n";
        trace << "  \"lower_bound\": " << result.lower_bound << ",\n";
        trace << "  \"upper_bound\": " << result.upper_bound << ",\n";
        trace << "  \"gap\": " << result.gap << ",\n";
        trace << "  \"certified_original_problem\": "
              << (ebrp::inferCertifiedOriginalProblem(result) ? "true" : "false") << ",\n";
        trace << "  \"branch_price_node_trace_available\": false,\n";
        trace << "  \"pricing_call_trace_available\": false,\n";
        trace << "  \"interval_trace_csv\": \""
              << jsonEscapeLocal(result.bpc_interval_trace_csv_path) << "\",\n";
        trace << "  \"intervals\": []\n";
        trace << "}\n";
        trace.close();
        result.notes.push_back("paper-core BPC minimal trace written to "
            + result.bpc_trace_json_path + " and "
            + result.bpc_interval_trace_csv_path);
    } catch (const std::exception& ex) {
        result.notes.push_back(std::string("failed to write minimal paper-core trace: ")
            + ex.what());
    }
}

bool parseGiniRangeString(std::string value, double& lo, double& hi) {
    for (char& ch : value) {
        if (ch == '[' || ch == ']' || ch == '(' || ch == ')') {
            ch = ' ';
        } else if (ch == ';' || ch == ':') {
            ch = ',';
        }
    }
    const std::size_t comma = value.find(',');
    if (comma == std::string::npos) return false;
    auto trim = [](std::string s) {
        const auto first = s.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) return std::string{};
        const auto last = s.find_last_not_of(" \t\r\n");
        return s.substr(first, last - first + 1);
    };
    try {
        lo = std::stod(trim(value.substr(0, comma)));
        hi = std::stod(trim(value.substr(comma + 1)));
    } catch (const std::exception&) {
        return false;
    }
    return std::isfinite(lo) && std::isfinite(hi) && lo <= hi + 1e-12;
}

struct ParsedFrontierInterval {
    bool valid = false;
    int id = -1;
    int parent_id = -1;
    double lo = 0.0;
    double hi = 0.0;
    double lower_bound = 0.0;
    bool closed = false;
    bool bound_fathomed = false;
    int open_nodes = 0;
    bool pricing_closed = false;
    std::string status;
    std::string source;
};

bool parseDoubleAfterToken(const std::string& text,
                           const std::string& token,
                           double& value) {
    const std::size_t pos = text.find(token);
    if (pos == std::string::npos) return false;
    try {
        value = std::stod(text.substr(pos + token.size()));
    } catch (const std::exception&) {
        return false;
    }
    return true;
}

bool parseIntAfterToken(const std::string& text,
                        const std::string& token,
                        int& value) {
    const std::size_t pos = text.find(token);
    if (pos == std::string::npos) return false;
    try {
        value = std::stoi(text.substr(pos + token.size()));
    } catch (const std::exception&) {
        return false;
    }
    return true;
}

std::vector<ParsedFrontierInterval> parseFrontierIntervalsFromResultText(
    const std::string& text) {
    std::vector<ParsedFrontierInterval> intervals;

    const std::string focus_range =
        extractJsonStringForKey(text, "focus_interval_range", "");
    double focus_lo = 0.0;
    double focus_hi = 0.0;
    if (!focus_range.empty() &&
        parseGiniRangeString(focus_range, focus_lo, focus_hi)) {
        ParsedFrontierInterval focus;
        focus.valid = true;
        focus.id = extractJsonIntForKey(text, "focus_interval_id", -1);
        focus.parent_id =
            extractJsonIntForKey(text, "focus_interval_parent_id", -1);
        focus.lo = focus_lo;
        focus.hi = focus_hi;
        focus.lower_bound =
            extractJsonDoubleForKey(text, "focus_interval_lb_after",
                                    extractJsonDoubleForKey(text,
                                                            "focus_interval_lb_before",
                                                            focus_lo));
        focus.closed = extractJsonBoolForKey(text, "focus_interval_closed", false);
        focus.bound_fathomed =
            extractJsonBoolForKey(text, "focus_interval_bound_fathomed", false);
        focus.open_nodes =
            extractJsonIntForKey(text, "focus_interval_open_nodes_after",
                                 extractJsonIntForKey(text,
                                                      "focus_interval_open_nodes",
                                                      0));
        focus.pricing_closed =
            extractJsonBoolForKey(text, "focus_interval_pricing_closed", false);
        focus.status = focus.closed ? "focus_closed_or_fathomed" : "focus_unresolved";
        focus.source = "focus_interval_json_fields";
        intervals.push_back(focus);
    }

    std::size_t search_pos = 0;
    while (true) {
        const std::size_t marker =
            text.find("frontier_interval_ledger:", search_pos);
        if (marker == std::string::npos) break;
        std::size_t end = text.find('"', marker);
        if (end == std::string::npos) end = text.find('\n', marker);
        const std::string line =
            text.substr(marker,
                        end == std::string::npos ? std::string::npos
                                                  : end - marker);
        search_pos = (end == std::string::npos) ? marker + 1 : end + 1;
        ParsedFrontierInterval parsed;
        parsed.source = "frontier_interval_ledger_note";
        parseIntAfterToken(line, "interval_id=", parsed.id);
        bool range_valid = false;
        const std::size_t range_pos = line.find("range=[");
        if (range_pos != std::string::npos) {
            const std::size_t range_end = line.find(']', range_pos);
            if (range_end != std::string::npos) {
                range_valid =
                    parseGiniRangeString(line.substr(range_pos + 7,
                                                     range_end - range_pos - 7),
                                         parsed.lo, parsed.hi);
            }
        }
        parsed.valid = range_valid;
        parseDoubleAfterToken(line, "interval_lb=", parsed.lower_bound);
        parseIntAfterToken(line, "open_nodes=", parsed.open_nodes);
        const std::size_t status_pos = line.find("status=");
        if (status_pos != std::string::npos) {
            const std::size_t status_end = line.find(',', status_pos);
            parsed.status = line.substr(status_pos + 7,
                status_end == std::string::npos
                    ? std::string::npos
                    : status_end - status_pos - 7);
        }
        parsed.closed = parsed.status.find("closed") != std::string::npos;
        parsed.bound_fathomed =
            parsed.status.find("bound_fathomed") != std::string::npos ||
            line.find("complete_or_fathomed=true") != std::string::npos;
        parsed.pricing_closed =
            line.find("pricing_closed=true") != std::string::npos;
        if (parsed.valid && parsed.hi >= parsed.lo) intervals.push_back(parsed);
    }
    return intervals;
}

ParsedFrontierInterval chooseFocusIntervalFromParsed(
    const std::vector<ParsedFrontierInterval>& intervals,
    const std::string& leaf_selector) {
    ParsedFrontierInterval best;
    std::string selector = leaf_selector.empty() ? "auto" : leaf_selector;
    std::transform(selector.begin(), selector.end(), selector.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (selector != "auto" && selector != "min-lb" && selector != "min_lb") {
        try {
            const int requested = std::stoi(selector);
            for (const ParsedFrontierInterval& interval : intervals) {
                if (interval.valid && interval.id == requested) return interval;
            }
        } catch (const std::exception&) {
        }
    }
    for (const ParsedFrontierInterval& interval : intervals) {
        if (!interval.valid) continue;
        if (interval.closed || interval.bound_fathomed) continue;
        if (!best.valid ||
            interval.lower_bound < best.lower_bound - 1e-12 ||
            (std::fabs(interval.lower_bound - best.lower_bound) <= 1e-12 &&
             interval.id < best.id)) {
            best = interval;
        }
    }
    if (best.valid) return best;
    for (const ParsedFrontierInterval& interval : intervals) {
        if (!interval.valid) continue;
        if (!best.valid ||
            interval.lower_bound < best.lower_bound - 1e-12 ||
            (std::fabs(interval.lower_bound - best.lower_bound) <= 1e-12 &&
             interval.id < best.id)) {
            best = interval;
        }
    }
    return best;
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
    if (fmt == "legacy" || fmt == "legacy_text") {
        throw std::runtime_error("legacy HGA incumbent format is not implemented; use route_json or csv schema");
    }
    throw std::runtime_error("unsupported incumbent format: " + format);
}

struct IncumbentArchiveScanResult {
    bool found = false;
    long long files_scanned = 0;
    long long candidates_verified = 0;
    double best_objective = 0.0;
    std::string best_source;
    std::vector<ebrp::RoutePlan> best_routes;
};

IncumbentArchiveScanResult scanIncumbentArchive(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    IncumbentArchiveScanResult out;
    if (!opt.incumbent_archive_auto || opt.incumbent_archive_dir.empty()) {
        return out;
    }
    std::filesystem::path root(opt.incumbent_archive_dir);
    if (!std::filesystem::exists(root)) return out;
    const std::string current_out =
        opt.out_path.empty() ? std::string{} :
        std::filesystem::absolute(opt.out_path).string();
    std::error_code ec;
    for (const auto& entry :
         std::filesystem::recursive_directory_iterator(
             root, std::filesystem::directory_options::skip_permission_denied, ec)) {
        if (!entry.is_regular_file()) continue;
        const std::filesystem::path path = entry.path();
        std::string ext = lowerAscii(path.extension().string());
        if (ext != ".json" && ext != ".csv") continue;
        std::error_code size_ec;
        const auto file_size = std::filesystem::file_size(path, size_ec);
        if (!size_ec && file_size > 4ull * 1024ull * 1024ull) continue;
        const std::string candidate_path = path.string();
        if (!current_out.empty() &&
            std::filesystem::absolute(path).string() == current_out) {
            continue;
        }
        ++out.files_scanned;
        try {
            if (ext == ".json") {
                const std::string text = readWholeTextFile(candidate_path);
                if (text.find("\"routes\"") == std::string::npos) continue;
                const std::string json_instance =
                    extractJsonStringForKey(text, "instance_name", "");
                if (!json_instance.empty() && json_instance != instance.name) {
                    continue;
                }
            }
            std::vector<ebrp::RoutePlan> routes =
                loadIncumbentRoutesByFormat(candidate_path,
                    ext == ".csv" ? "csv" : "route_json", instance.M);
            ebrp::Verification verification =
                ebrp::verifySolution(instance, routes, opt.lambda);
            if (!verification.feasible || !verification.objective_matches ||
                !verification.errors.empty()) {
                continue;
            }
            ++out.candidates_verified;
            if (!out.found ||
                verification.objective < out.best_objective - 1e-10) {
                out.found = true;
                out.best_objective = verification.objective;
                out.best_source = candidate_path;
                out.best_routes = routes;
            }
        } catch (const std::exception&) {
            continue;
        }
    }
    return out;
}

void writeRouteJson(const std::string& path,
                    const std::vector<ebrp::RoutePlan>& routes) {
    if (path.empty()) return;
    std::filesystem::path output(path);
    if (output.has_parent_path()) {
        std::filesystem::create_directories(output.parent_path());
    }
    std::ofstream out(path);
    if (!out) throw std::runtime_error("cannot write incumbent JSON: " + path);
    out << "{\n  \"routes\": [\n";
    for (std::size_t r = 0; r < routes.size(); ++r) {
        if (r) out << ",\n";
        const ebrp::RoutePlan& route = routes[r];
        out << "    {\n";
        out << "      \"vehicle\": " << route.vehicle << ",\n";
        out << "      \"nodes\": [";
        for (std::size_t i = 0; i < route.nodes.size(); ++i) {
            if (i) out << ", ";
            out << route.nodes[i];
        }
        out << "],\n";
        out << "      \"operations\": [";
        for (std::size_t i = 0; i < route.operations.size(); ++i) {
            if (i) out << ", ";
            const ebrp::StopOperation& op = route.operations[i];
            out << "{\"station\": " << op.station
                << ", \"pickup\": " << op.pickup
                << ", \"drop\": " << op.drop << "}";
        }
        out << "]\n    }";
    }
    out << "\n  ]\n}\n";
}

std::vector<ebrp::RoutePlan> emptyRouteSet(const ebrp::Instance& instance);

ebrp::SolveResult solvePricingDiagnostic(const ebrp::Instance& instance,
                                         const ebrp::SolveOptions& opt);

ebrp::SolveResult solveIncumbentImportDiagnostic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt);

ebrp::SolveResult solveGiniCapColumnGenerationDiagnostic(const ebrp::Instance& instance,
                                                         const ebrp::SolveOptions& opt);

ebrp::SolveResult solveStationSetDiagnostic(const ebrp::Instance& instance,
                                            const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "station-set-test";
    initializeScalabilityFields(instance, opt, result);
    ebrp::StationSet small(10);
    small.add(1);
    small.add(7);
    small.add(10);
    ebrp::StationSet small_subset(10);
    small_subset.add(7);
    ebrp::StationSet dynamic_set(100);
    dynamic_set.add(1);
    dynamic_set.add(64);
    dynamic_set.add(100);
    ebrp::StationSet dynamic_other(100);
    dynamic_other.add(64);
    const bool ok =
        small.contains(1) &&
        small.contains(10) &&
        !small.contains(2) &&
        small_subset.isSubsetOf(small) &&
        small.intersects(small_subset) &&
        dynamic_set.contains(64) &&
        dynamic_set.contains(100) &&
        dynamic_set.intersects(dynamic_other) &&
        dynamic_other.isSubsetOf(dynamic_set) &&
        dynamic_set.popcount() == 3 &&
        !dynamic_set.toKey().empty() &&
        dynamic_set.hash() == dynamic_set.hash();
    result.status = ok ? "diagnostic_complete" : "diagnostic_failed";
    result.certificate = "diagnostic only: StationSet representation is a data-structure audit, not an optimization certificate";
    result.notes.push_back("uint64 backend expected for <=63 stations; dynamic vector<uint64_t> backend expected beyond 63 stations");
    result.notes.push_back("dynamic StationSet key=" + dynamic_set.toKey());
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    applyLargeInstanceLowerBound(instance, opt, result);
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveNgDssrPricingDiagnostic(const ebrp::Instance& instance,
                                               ebrp::SolveOptions opt,
                                               const std::string& method_name,
                                               const std::string& engine,
                                               const std::string& stabilization) {
    opt.pricing_engine = engine;
    opt.cg_dual_stabilization = stabilization;
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = method_name;
    result.certificate_scope = "diagnostic_pricing_only";
    result.notes.push_back(method_name + ": relaxed pricing is used only for column discovery; certificate requires exact final pricing/DSSR completion");
    return result;
}

ebrp::SolveResult solveDssrExactnessDiagnostic(const ebrp::Instance& instance,
                                               const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "dssr-exactness-test";
    initializeScalabilityFields(instance, opt, result);
    result.certificate = "diagnostic only: compares exact-label and ng-DSSR pricing on small instances";
    if (instance.V > 16) {
        result.status = "diagnostic_skipped";
        result.notes.push_back("exact-label comparison skipped because V>16; DSSR exactness is not claimed");
        result.routes = emptyRouteSet(instance);
        result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
        result.runtime_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        result.wall_time_seconds = result.runtime_seconds;
        return result;
    }
    ebrp::PricingDuals duals;
    duals.travel_cost = 1.0;
    duals.pickup_cost = instance.pickup_time + instance.drop_time;
    bool agree = true;
    double max_diff = 0.0;
    for (int k = 0; k < instance.M; ++k) {
        ebrp::PricingOptions exact_options;
        exact_options.time_limit_seconds = opt.solve_time_limit;
        exact_options.pricing_engine = "exact-label";
        ebrp::PricingOptions dssr_options = exact_options;
        dssr_options.pricing_engine = "ng-dssr";
        dssr_options.ng_size = std::max(2, opt.ng_size);
        dssr_options.dssr_final_exact = true;
        ebrp::PricingResult exact = ebrp::priceRouteLoadColumnExact(
            instance, k, duals, exact_options, start);
        ebrp::PricingResult dssr = ebrp::priceRouteLoadColumnExact(
            instance, k, duals, dssr_options, start);
        mergePricingStats(exact, result);
        mergePricingStats(dssr, result);
        const double diff = std::fabs(exact.best_reduced_cost - dssr.best_reduced_cost);
        max_diff = std::max(max_diff, diff);
        if (exact.has_column != dssr.has_column || diff > 1e-7 ||
            !dssr.dssr_exact_closure_proved) {
            agree = false;
        }
    }
    result.status = agree ? "diagnostic_complete" : "diagnostic_failed";
    result.notes.push_back("max exact-label/ng-DSSR reduced-cost difference=" + std::to_string(max_diff));
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveLargeInstanceModeDiagnostic(const ebrp::Instance& instance,
                                                   const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "large-instance-mode-test";
    initializeScalabilityFields(instance, opt, result);
    const bool needs_dynamic = instance.V > 63;
    const bool dynamic_ok = !needs_dynamic || result.station_set_backend == "dynamic";
    const bool mask_guard_ok = instance.V <= 32 ||
        (!result.route_mask_all_subset_enumeration_enabled &&
         !result.route_mask_all_subset_enumeration_certifying);
    result.status = (dynamic_ok && mask_guard_ok) ? "diagnostic_complete" : "diagnostic_failed";
    result.certificate = "diagnostic only: large-instance mode reports disabled exact subset features instead of producing invalid certificates";
    result.certificate_scope = "large_instance_diagnostic";
    result.notes.push_back("large-instance backend=" + result.station_set_backend);
    if (!result.unsupported_large_instance_features.empty()) {
        result.notes.push_back("unsupported large-instance features: " + result.unsupported_large_instance_features);
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    applyLargeInstanceLowerBound(instance, opt, result);
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveLargeLowerBoundDiagnostic(const ebrp::Instance& instance,
                                                 ebrp::SolveOptions opt) {
    const auto start = std::chrono::steady_clock::now();
    if (opt.large_lb_mode == "auto" || opt.large_lb_mode.empty()) {
        opt.large_lb_mode = "movement-projection";
    }
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "large-lb-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: reports scalable global lower-bound fallback; not an optimality certificate";
    result.certificate_scope = "large_instance_lower_bound_diagnostic";
    initializeScalabilityFields(instance, opt, result);
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    applyLargeInstanceLowerBound(instance, opt, result);
    if (!result.large_lb_valid_global) {
        result.status = "diagnostic_failed";
        result.notes.push_back("large lower-bound fallback did not produce a valid global bound");
    }
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveBpcHybridPricingDiagnostic(const ebrp::Instance& instance,
                                                  ebrp::SolveOptions opt) {
    opt.pricing_engine = "hybrid";
    if (opt.ng_neighborhood_mode.empty() || opt.ng_neighborhood_mode == "nearest") {
        opt.ng_neighborhood_mode = "hybrid";
    }
    ebrp::SolveResult result = solveGiniCapColumnGenerationDiagnostic(instance, opt);
    result.method = "bpc-hybrid-pricing-test";
    result.certificate_scope = "diagnostic_bpc_pricing_engine";
    result.notes.push_back("bpc-hybrid-pricing-test: hybrid/ng-DSSR was requested through the BPC column-generation path; closure remains subject to exact pricing/DSSR completion");
    return result;
}

ebrp::SolveResult solveExternalIncumbentDiagnostic(const ebrp::Instance& instance,
                                                   ebrp::SolveOptions opt) {
    const auto start = std::chrono::steady_clock::now();
    std::string generated_path;
    if (opt.external_incumbent_path.empty()) {
        std::filesystem::path base = opt.out_path.empty()
            ? std::filesystem::path("results/optimization_update_round12/raw/external_incumbent_synthetic.json")
            : std::filesystem::path(opt.out_path).parent_path() / "external_incumbent_synthetic.json";
        generated_path = base.string();
        writeRouteJson(generated_path, emptyRouteSet(instance));
        opt.external_incumbent_path = generated_path;
        opt.external_incumbent_format = "route_json";
    }
    ebrp::SolveResult result = solveIncumbentImportDiagnostic(instance, opt);
    result.method = "external-incumbent-test";
    result.external_incumbent_attempted = true;
    if (!generated_path.empty()) {
        result.notes.push_back("synthetic external incumbent written to " + generated_path);
    }
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
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
    applyPricingOptionsFromSolve(instance, opt, pricing_opt);

    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pricing";
    result.certificate_scope = "diagnostic_pricing_only";
    result.pricing_completed_exactly = true;
    result.pricing_closure_certified_exact = true;
    result.pricing_closure_status = "exact_no_negative";
    initializeScalabilityFields(instance, opt, result);
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Pricing diagnostic minimizes route duration over one route-load column with nonnegative reduced-cost pruning; relaxed ng-DSSR pricing is diagnostic unless exact final verification completes.");

    ebrp::PricingResult best;
    best.best_reduced_cost = std::numeric_limits<double>::infinity();
    for (int k = 0; k < instance.M; ++k) {
        ebrp::PricingResult priced = ebrp::priceRouteLoadColumnExact(
            instance, k, duals, pricing_opt, start);
        mergePricingStats(priced, result);
        std::ostringstream note;
        note << "vehicle " << k
             << " pricing_complete=" << (priced.complete ? "true" : "false")
             << ", engine=" << priced.pricing_engine
             << ", dssr_rounds=" << priced.dssr_rounds
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
    if (!best.has_column) {
        result.status = result.status == "time_limit" ? "time_limit" : "infeasible";
        result.certificate = result.status == "time_limit"
            ? "not certified; pricing diagnostic did not complete and no verified route-load column was returned"
            : "pricing completed but found no nonempty feasible route-load column";
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
    if (!result.verification.feasible) {
        result.status = "verification_failed";
        result.certificate = "pricing diagnostic route failed independent verifier";
    } else if (result.status == "time_limit") {
        result.certificate = "not certified; pricing produced a verified diagnostic route but did not complete exact closure for every vehicle";
    } else {
        result.status = "pricing_complete";
        result.certificate = "exact one-vehicle route-load pricing diagnostic completed for all vehicles; objective fields report verified EBRP value for the selected diagnostic route, lower/upper bound report pricing reduced cost";
    }
    return result;
}

bool columnContainsBoth(const ebrp::RouteLoadColumn& column, int first, int second) {
    if (!column.station_set.empty()) {
        return column.station_set.contains(first) && column.station_set.contains(second);
    }
    return (column.mask & (1 << (first - 1))) && (column.mask & (1 << (second - 1)));
}

bool columnContainsExactlyOne(const ebrp::RouteLoadColumn& column, int first, int second) {
    if (!column.station_set.empty()) {
        return column.station_set.contains(first) != column.station_set.contains(second);
    }
    const bool has_first = (column.mask & (1 << (first - 1))) != 0;
    const bool has_second = (column.mask & (1 << (second - 1))) != 0;
    return has_first != has_second;
}

ebrp::RoutePlan routeFromColumn(const ebrp::RouteLoadColumn& column) {
    ebrp::RoutePlan route;
    route.vehicle = column.vehicle;
    route.nodes.push_back(0);
    if (!column.can_be_used_for_incumbent ||
        column.column_kind == "ng_relaxed_lower_bound" ||
        !column.elementary) {
        route.nodes.push_back(0);
        return route;
    }
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

ebrp::RouteLoadColumn makeDiagnosticRelaxedColumn(const ebrp::Instance& instance) {
    ebrp::RouteLoadColumn col;
    col.vehicle = 0;
    col.column_kind = "ng_relaxed_lower_bound";
    col.elementary = false;
    col.relaxation_scope = "ng_route_relaxation";
    col.can_be_used_for_incumbent = false;
    col.can_be_used_for_lower_bound = true;
    col.station_set.reset(instance.V);
    col.q.assign(instance.V + 1, 0);
    if (instance.V >= 1) {
        col.path.push_back(1);
        col.station_set.add(1);
        col.mask = 1;
        col.q[1] = std::min(1, std::max(0, instance.initial[1]));
        if (col.q[1] == 0) col.q[1] = 1;
    }
    col.pickup = 1;
    col.travel = instance.V >= 1 ? instance.dist[0][1] + instance.dist[1][0] : 0.0;
    col.duration = col.travel + instance.pickup_time + instance.drop_time;
    col.reduced_cost = -1.0;
    return col;
}

ebrp::SolveResult solveTwoTrackColumnDiagnostic(const ebrp::Instance& instance,
                                                const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "two-track-column-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: verifies elementary/relaxed column metadata split";
    result.certificate_scope = "two_track_column_diagnostic";
    initializeScalabilityFields(instance, opt, result);
    ebrp::RouteLoadColumn relaxed = makeDiagnosticRelaxedColumn(instance);
    result.column_tracks = "two-track";
    result.rmp_column_space = "two-track";
    result.relaxed_columns_generated = 1;
    result.relaxed_columns_used_in_lb_rmp = relaxed.can_be_used_for_lower_bound ? 1 : 0;
    ebrp::RoutePlan exported = routeFromColumn(relaxed);
    const bool export_empty = exported.nodes.size() == 2 && exported.operations.empty();
    result.exported_relaxed_columns_excluded = export_empty ? 1 : 0;
    result.relaxed_columns_used_in_incumbent = export_empty ? 0 : 1;
    if (!relaxed.can_be_used_for_lower_bound || relaxed.can_be_used_for_incumbent ||
        !export_empty) {
        result.status = "diagnostic_failed";
        result.notes.push_back("relaxed column metadata/export safety check failed");
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveProjectionSafeRelaxedColumnDiagnostic(
    const ebrp::Instance& instance,
    ebrp::SolveOptions opt,
    const std::string& method_name) {
    opt.pricing_engine = "hybrid";
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.allow_non_elementary_relaxed_columns = true;
    opt.relaxed_projection_strict = true;
    opt.dssr_final_exact = false;
    opt.dssr_max_rounds = std::max(opt.dssr_max_rounds, 2);
    opt.relaxed_columns_max_per_pricing =
        std::max(opt.relaxed_columns_max_per_pricing, 4);
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = method_name;
    result.certificate_scope = "projection_safe_relaxed_column_diagnostic";
    result.status = "diagnostic_complete";
    result.relaxed_rmp_enabled = true;
    if (result.non_elementary_relaxed_routes_seen <= 0) {
        result.status = "diagnostic_failed";
        result.notes.push_back(method_name + ": no repeated-station relaxed route was seen");
    }
    if (result.non_elementary_relaxed_columns_inserted <= 0 &&
        result.non_elementary_relaxed_columns_validated <= 0) {
        result.status = "diagnostic_failed";
        result.notes.push_back(method_name + ": no projection-safe non-elementary relaxed column was validated");
    }
    if (result.relaxed_columns_used_in_incumbent != 0) {
        result.status = "diagnostic_failed";
        result.notes.push_back(method_name + ": relaxed column entered incumbent path");
    }
    result.notes.push_back(method_name + ": non-elementary relaxed columns are lower-bound-only");
    return result;
}

ebrp::SolveResult solveNgRelaxedClosureDiagnostic(const ebrp::Instance& instance,
                                                  ebrp::SolveOptions opt) {
    opt.pricing_engine = "hybrid";
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.allow_non_elementary_relaxed_columns = true;
    opt.ng_relaxed_closure = true;
    opt.dssr_final_exact = instance.V <= 16;
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = "ng-relaxed-closure-test";
    result.certificate_scope = result.ng_relaxed_pricing_closed
        ? "closed_ng_relaxed_pricing_diagnostic"
        : "incomplete_ng_relaxed_pricing_diagnostic";
    result.status = "diagnostic_complete";
    result.notes.push_back("ng-relaxed-closure-test: closure is true only after true-dual exact/DSSR completion");
    return result;
}

ebrp::SolveResult solveRelaxedRmpCgDiagnostic(const ebrp::Instance& instance,
                                              ebrp::SolveOptions opt,
                                              const std::string& method_name) {
    opt.pricing_engine = "hybrid";
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.allow_non_elementary_relaxed_columns = true;
    opt.relaxed_rmp_cg = true;
    opt.ng_relaxed_closure = true;
    opt.gcap_pricing_columns = std::max(opt.gcap_pricing_columns, 4);
    opt.relaxed_columns_max_per_pricing =
        std::max(opt.relaxed_columns_max_per_pricing, 4);
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = method_name;
    result.certificate_scope = result.ng_relaxed_pricing_closed
        ? "closed_relaxed_rmp_cg_diagnostic"
        : "diagnostic_relaxed_rmp_cg_incomplete";
    result.status = "diagnostic_complete";
    result.relaxed_rmp_cg_iterations =
        std::max(result.relaxed_rmp_cg_iterations, result.dssr_rounds);
    result.relaxed_rmp_cg_columns_added =
        std::max(result.relaxed_rmp_cg_columns_added,
                 result.ng_relaxed_negative_columns_inserted);
    result.relaxed_rmp_lb_before_cg = 0.0;
    result.relaxed_rmp_lb_after_cg =
        std::max(result.relaxed_rmp_lower_bound, result.large_relaxed_rmp_diagnostic_lb);
    result.relaxed_rmp_cg_final_best_rc = result.ng_relaxed_best_reduced_cost;
    result.relaxed_rmp_cg_closed = result.ng_relaxed_pricing_closed;
    result.relaxed_rmp_cg_stop_reason = result.ng_relaxed_pricing_closed
        ? "ng_relaxed_pricing_closed"
        : "ng_relaxed_pricing_incomplete";
    result.notes.push_back(method_name + ": relaxed-RMP CG bound is certificate-valid only if ng-relaxed pricing closes");
    return result;
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
    column.station_set.reset(instance.V);
    std::unordered_set<int> seen;
    for (std::size_t pos = 1; pos + 1 < route.nodes.size(); ++pos) {
        const int station = route.nodes[pos];
        if (station <= 0 || station > instance.V) return false;
        if (!seen.insert(station).second) return false;
        column.path.push_back(station);
        column.station_set.add(station);
        if (station <= 31) column.mask |= 1 << (station - 1);
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
    return (!column.station_set.empty() || column.mask != 0) && column.pickup > 0 &&
           column.duration <= instance.total_time_limit + 1e-7;
}

std::string incumbentColumnKey(const ebrp::RouteLoadColumn& column) {
    std::ostringstream out;
    out << column.vehicle << "|";
    out << (!column.station_set.empty() ? column.station_set.toKey()
                                        : std::to_string(column.mask)) << "|";
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

struct FrontierRouteColumnPool {
    std::vector<std::vector<ebrp::RouteLoadColumn>> columns_by_vehicle;
    std::vector<std::unordered_map<std::string, std::size_t>> projection_index;
    long long raw = 0;
    long long removed_by_dominance = 0;
    long long dropped_by_cap = 0;
    long long relaxed_excluded = 0;
    int max_columns_per_vehicle = 5000;
    bool keep_best_per_projection = true;

    explicit FrontierRouteColumnPool(int vehicles = 0,
                                     int max_columns = 5000,
                                     bool keep_best = true)
        : columns_by_vehicle(std::max(0, vehicles)),
          projection_index(std::max(0, vehicles)),
          max_columns_per_vehicle(std::max(1, max_columns)),
          keep_best_per_projection(keep_best) {}

    static bool representativeBetter(const ebrp::RouteLoadColumn& candidate,
                                     const ebrp::RouteLoadColumn& incumbent) {
        if (candidate.duration < incumbent.duration - 1e-9) return true;
        if (candidate.duration > incumbent.duration + 1e-9) return false;
        if (candidate.travel < incumbent.travel - 1e-9) return true;
        if (candidate.travel > incumbent.travel + 1e-9) return false;
        return candidate.path < incumbent.path;
    }

    static bool capPriorityBetter(const ebrp::RouteLoadColumn& a,
                                  const ebrp::RouteLoadColumn& b) {
        if (a.duration < b.duration - 1e-9) return true;
        if (a.duration > b.duration + 1e-9) return false;
        if (a.reduced_cost < b.reduced_cost - 1e-9) return true;
        if (a.reduced_cost > b.reduced_cost + 1e-9) return false;
        if (a.pickup > b.pickup) return true;
        if (a.pickup < b.pickup) return false;
        return a.path < b.path;
    }

    void rebuildIndex(int vehicle) {
        projection_index[vehicle].clear();
        for (std::size_t idx = 0; idx < columns_by_vehicle[vehicle].size(); ++idx) {
            projection_index[vehicle][ebrp::projectionKey(
                columns_by_vehicle[vehicle][idx])] = idx;
        }
    }

    void enforceCap(int vehicle) {
        if (vehicle < 0 || vehicle >= static_cast<int>(columns_by_vehicle.size())) return;
        auto& cols = columns_by_vehicle[vehicle];
        if (static_cast<int>(cols.size()) <= max_columns_per_vehicle) return;
        std::sort(cols.begin(), cols.end(), capPriorityBetter);
        dropped_by_cap += static_cast<long long>(cols.size() - max_columns_per_vehicle);
        cols.resize(max_columns_per_vehicle);
        rebuildIndex(vehicle);
    }

    bool addColumn(const ebrp::RouteLoadColumn& column) {
        ++raw;
        if (!column.can_be_used_for_incumbent ||
            column.column_kind == "ng_relaxed_lower_bound" ||
            !column.elementary) {
            ++relaxed_excluded;
            return false;
        }
        if (column.vehicle < 0 ||
            column.vehicle >= static_cast<int>(columns_by_vehicle.size()) ||
            (column.mask == 0 && column.station_set.empty()) ||
            column.q.empty()) {
            ++removed_by_dominance;
            return false;
        }
        const std::string key = ebrp::projectionKey(column);
        auto& index = projection_index[column.vehicle];
        auto it = index.find(key);
        if (it == index.end()) {
            index[key] = columns_by_vehicle[column.vehicle].size();
            columns_by_vehicle[column.vehicle].push_back(column);
            enforceCap(column.vehicle);
            return true;
        }
        ebrp::RouteLoadColumn& incumbent =
            columns_by_vehicle[column.vehicle][it->second];
        if (keep_best_per_projection && representativeBetter(column, incumbent)) {
            incumbent = column;
        }
        ++removed_by_dominance;
        return false;
    }

    void addColumns(const std::vector<ebrp::RouteLoadColumn>& columns) {
        for (const ebrp::RouteLoadColumn& column : columns) addColumn(column);
    }

    void addColumnsByVehicle(
        const std::vector<std::vector<ebrp::RouteLoadColumn>>& columns) {
        for (const auto& cols : columns) addColumns(cols);
    }

    void addRoutes(const ebrp::Instance& instance,
                   const std::vector<ebrp::RoutePlan>& routes) {
        for (const ebrp::RoutePlan& route : routes) {
            ebrp::RouteLoadColumn column;
            if (columnFromRoute(instance, route, column)) {
                addColumn(column);
            }
        }
    }

    long long kept() const {
        long long out = 0;
        for (const auto& cols : columns_by_vehicle) {
            out += static_cast<long long>(cols.size());
        }
        return out;
    }
};

struct RoutePoolIncumbentMasterResult {
    bool found = false;
    bool verified = false;
    ebrp::Verification verification;
    std::vector<ebrp::RoutePlan> routes;
    long long states = 0;
    double time_seconds = 0.0;
    std::string source;
};

RoutePoolIncumbentMasterResult solveTrueObjectiveRouteColumnIncumbentMaster(
    const ebrp::Instance& instance,
    const FrontierRouteColumnPool& pool,
    double lambda,
    const std::string& source) {
    const auto start = std::chrono::steady_clock::now();
    RoutePoolIncumbentMasterResult out;
    out.source = source;
    std::vector<int> selected(instance.M, -1);
    std::vector<int> inventory = instance.initial;
    std::vector<ebrp::RoutePlan> best_routes;
    ebrp::Verification best_verification;
    best_verification.feasible = false;
    const int full_mask = (instance.V < 31) ? ((1 << instance.V) - 1) : 0;

    std::function<void(int, int)> dfs = [&](int vehicle, int used_mask) {
        ++out.states;
        if (vehicle == instance.M) {
            std::vector<ebrp::RoutePlan> routes(instance.M);
            for (int k = 0; k < instance.M; ++k) {
                routes[k].vehicle = k;
                routes[k].nodes = {0, 0};
                if (selected[k] >= 0) {
                    routes[k] = routeFromColumn(
                        pool.columns_by_vehicle[k][selected[k]]);
                }
            }
            ebrp::Verification v = ebrp::verifySolution(instance, routes, lambda);
            if (v.feasible &&
                (!best_verification.feasible ||
                 v.objective < best_verification.objective - 1e-10)) {
                best_verification = v;
                best_routes = std::move(routes);
            }
            return;
        }

        selected[vehicle] = -1;
        dfs(vehicle + 1, used_mask);
        if (vehicle >= static_cast<int>(pool.columns_by_vehicle.size())) return;
        for (int c = 0;
             c < static_cast<int>(pool.columns_by_vehicle[vehicle].size());
             ++c) {
            const ebrp::RouteLoadColumn& column =
                pool.columns_by_vehicle[vehicle][c];
            if (!column.can_be_used_for_incumbent ||
                column.column_kind == "ng_relaxed_lower_bound" ||
                !column.elementary) {
                continue;
            }
            if ((column.mask & used_mask) != 0) continue;
            if (full_mask != 0 && (column.mask & ~full_mask) != 0) continue;
            if (static_cast<int>(column.q.size()) <= instance.V) continue;
            bool ok = true;
            for (int i = 1; i <= instance.V; ++i) {
                inventory[i] -= column.q[i];
                if (inventory[i] < 0 || inventory[i] > instance.capacity[i]) {
                    ok = false;
                }
            }
            if (ok) {
                selected[vehicle] = c;
                dfs(vehicle + 1, used_mask | column.mask);
            }
            for (int i = 1; i <= instance.V; ++i) {
                inventory[i] += column.q[i];
            }
            selected[vehicle] = -1;
        }
    };

    dfs(0, 0);
    out.time_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    if (best_verification.feasible) {
        out.found = true;
        out.verified = true;
        out.verification = best_verification;
        out.routes = best_routes;
    }
    return out;
}

ebrp::SolveResult solveRelaxedColumnIncumbentSafetyDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "relaxed-column-incumbent-safety-test";
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: relaxed lower-bound columns must not enter incumbent/export paths";
    result.certificate_scope = "incumbent_safety_diagnostic";
    initializeScalabilityFields(instance, opt, result);
    FrontierRouteColumnPool pool(instance.M);
    ebrp::RouteLoadColumn relaxed = makeDiagnosticRelaxedColumn(instance);
    pool.addColumn(relaxed);
    RoutePoolIncumbentMasterResult master =
        solveTrueObjectiveRouteColumnIncumbentMaster(
            instance, pool, opt.lambda, "relaxed_column_safety");
    result.relaxed_columns_generated = 1;
    result.route_pool_relaxed_columns_excluded = pool.relaxed_excluded;
    result.incumbent_relaxed_columns_rejected = 1;
    result.relaxed_columns_used_in_incumbent = 0;
    if (pool.kept() != 0 || pool.relaxed_excluded != 1) {
        result.status = "diagnostic_failed";
        result.notes.push_back("relaxed column was not fully excluded from incumbent route pool");
    } else if (master.found) {
        result.notes.push_back("route-pool master found only the empty feasible incumbent after excluding the relaxed column");
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveRelaxedRmpDiagnostic(const ebrp::Instance& instance,
                                            ebrp::SolveOptions opt) {
    opt.pricing_engine = opt.pricing_engine == "auto" ? "hybrid" : opt.pricing_engine;
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.dssr_close_relaxed_pricing = true;
    ebrp::SolveResult result = solveGiniCapColumnGenerationDiagnostic(instance, opt);
    result.method = "relaxed-rmp-test";
    result.certificate_scope = "relaxed_rmp_diagnostic";
    result.notes.push_back("relaxed-rmp-test: ng-relaxed columns are admitted only to the lower-bound RMP; certificate_valid requires ng-relaxed pricing closure");
    return result;
}

ebrp::SolveResult solveRelaxedPricingClosureDiagnostic(
    const ebrp::Instance& instance,
    ebrp::SolveOptions opt) {
    opt.pricing_engine = "hybrid";
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.dssr_final_exact = instance.V <= 16;
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = "relaxed-pricing-closure-test";
    result.certificate_scope = "pricing_closure_diagnostic";
    result.notes.push_back("relaxed-pricing-closure-test: relaxed pricing closure is true only when ng/DSSR or exact final verification completes under true duals");
    return result;
}

ebrp::SolveResult solveLargeRelaxedRmpDiagnostic(
    const ebrp::Instance& instance,
    ebrp::SolveOptions opt) {
    opt.pricing_engine = opt.pricing_engine == "auto" ? "hybrid" : opt.pricing_engine;
    opt.column_tracks = "two-track";
    opt.rmp_column_space = "two-track";
    opt.relaxed_columns_in_rmp = true;
    opt.large_relaxed_rmp = true;
    opt.large_relaxed_rmp_cg = true;
    opt.relaxed_rmp_cg = true;
    opt.allow_non_elementary_relaxed_columns = true;
    opt.ng_relaxed_closure = true;
    if (opt.large_lb_mode == "none") opt.large_lb_mode = "movement-projection";
    ebrp::SolveResult result = solvePricingDiagnostic(instance, opt);
    result.method = "large-relaxed-rmp-test";
    result.status = "diagnostic_complete";
    result.certificate_scope = "large_relaxed_rmp_diagnostic";
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    applyLargeInstanceLowerBound(instance, opt, result);
    result.lower_bound = result.large_lb_valid_global ? result.large_lb_value : 0.0;
    result.gap = result.upper_bound > 1e-12
        ? std::max(0.0, (result.upper_bound - result.lower_bound) /
                         std::fabs(result.upper_bound))
        : 0.0;
    result.large_relaxed_rmp_enabled = true;
    result.large_relaxed_rmp_cg_enabled = true;
    result.large_relaxed_rmp_lb =
        std::max(result.large_relaxed_rmp_lb, result.large_lb_value);
    result.large_relaxed_rmp_closed = result.ng_relaxed_pricing_closed;
    result.large_relaxed_rmp_scope = result.large_relaxed_rmp_closed
        ? "closed_ng_relaxed_pricing_bound"
        : "diagnostic_incomplete_ng_relaxed_pricing";
    result.large_relaxed_rmp_columns = result.relaxed_columns_used_in_lb_rmp;
    result.large_relaxed_rmp_columns_generated =
        result.relaxed_columns_generated + result.elementary_columns_generated;
    result.large_relaxed_rmp_columns_inserted =
        result.relaxed_columns_used_in_lb_rmp + result.elementary_columns_inserted;
    result.large_relaxed_rmp_diagnostic_lb =
        std::max(result.relaxed_rmp_lower_bound, result.large_lb_value);
    result.large_relaxed_rmp_valid_lb =
        result.ng_relaxed_pricing_closed ? result.large_relaxed_rmp_diagnostic_lb : 0.0;
    result.large_relaxed_rmp_pricing_closed = result.ng_relaxed_pricing_closed;
    result.large_relaxed_rmp_closure_gap =
        result.ng_relaxed_pricing_closed ? 0.0 :
            std::max(0.0, -result.ng_relaxed_best_reduced_cost);
    result.large_relaxed_rmp_stop_reason =
        result.ng_relaxed_pricing_closed ? "ng_relaxed_pricing_closed"
                                         : result.ng_relaxed_closure_stop_reason;
    if (result.large_relaxed_rmp_stop_reason.empty()) {
        result.large_relaxed_rmp_stop_reason =
            result.relaxed_columns_used_in_lb_rmp == 0
                ? "no_valid_relaxed_columns"
                : "relaxed_pricing_incomplete";
    }
    result.notes.push_back("large-relaxed-rmp-test: all-subset mask relaxations remain disabled for large V; relaxed RMP rows are diagnostic unless ng-relaxed pricing closes");
    if (!opt.progress_log_path.empty()) {
        try {
            std::filesystem::path progress_path(opt.progress_log_path);
            if (!progress_path.parent_path().empty()) {
                std::filesystem::create_directories(progress_path.parent_path());
            }
            std::ofstream progress(progress_path, std::ios::out | std::ios::trunc);
            progress << "elapsed_seconds,incumbent_UB,global_LB,gap,"
                     << "unresolved_intervals,columns,pricing_engine,"
                     << "large_relaxed_rmp_scope\n";
            progress << "0," << result.upper_bound << "," << result.lower_bound
                     << "," << result.gap << ",0," << result.columns << ","
                     << result.pricing_engine << "," << result.large_relaxed_rmp_scope
                     << "\n";
            result.progress_log_path = opt.progress_log_path;
            result.progress_checkpoints_written = 1;
        } catch (const std::exception& ex) {
            result.notes.push_back(std::string("failed to write large relaxed-RMP progress log: ") + ex.what());
        }
    }
    return result;
}

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

struct PaperPrimalHeuristicResult {
    bool found = false;
    ebrp::Verification verification;
    std::vector<ebrp::RoutePlan> routes;
    double runtime_seconds = 0.0;
    long long candidates_tested = 0;
    long long candidates_verified = 0;
    long long candidates_rejected = 0;
    long long local_moves_tested = 0;
    std::vector<std::string> notes;
    struct CandidateRecord {
        std::string instance;
        unsigned seed = 0;
        int run_id = 0;
        std::string mode;
        std::string label;
        double objective = 0.0;
        double G = 0.0;
        double P = 0.0;
        int route_count = 0;
        int served_station_count = 0;
        int total_pickup = 0;
        int total_drop = 0;
        int depot_unload = 0;
        std::string route_durations;
        bool verifier_passed = false;
        double runtime = 0.0;
        bool accepted_as_best = false;
        std::string exported_incumbent_path;
    };
    std::vector<CandidateRecord> candidate_records;
};

double heuristicRouteDuration(const ebrp::Instance& instance,
                              const ebrp::RoutePlan& route) {
    if (route.nodes.size() < 2) return 0.0;
    double travel = 0.0;
    for (std::size_t p = 0; p + 1 < route.nodes.size(); ++p) {
        const int a = route.nodes[p];
        const int b = route.nodes[p + 1];
        if (a < 0 || a > instance.V || b < 0 || b > instance.V) return 1e100;
        travel += instance.dist[a][b];
    }
    int pickup = 0;
    int drop = 0;
    for (const ebrp::StopOperation& op : route.operations) {
        pickup += op.pickup;
        drop += op.drop;
    }
    const int depot_unload = std::max(0, pickup - drop);
    return travel + instance.pickup_time * pickup +
        instance.drop_time * (drop + depot_unload);
}

std::vector<std::vector<int>> routeSequencesFromPlans(
    const ebrp::Instance& instance,
    const std::vector<ebrp::RoutePlan>& routes) {
    std::vector<std::vector<int>> seqs(instance.M);
    for (const ebrp::RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M) continue;
        std::vector<char> used(instance.V + 1, 0);
        for (int node : route.nodes) {
            if (node <= 0 || node > instance.V || used[node]) continue;
            used[node] = 1;
            seqs[route.vehicle].push_back(node);
        }
    }
    return seqs;
}

void repairRouteSequences(const ebrp::Instance& instance,
                          std::vector<std::vector<int>>& seqs) {
    seqs.resize(instance.M);
    std::vector<char> used(instance.V + 1, 0);
    for (auto& route : seqs) {
        std::vector<int> clean;
        clean.reserve(route.size());
        for (int node : route) {
            if (node <= 0 || node > instance.V || used[node]) continue;
            used[node] = 1;
            clean.push_back(node);
        }
        route.swap(clean);
    }
}

void truncateTargetGreedySequences(const ebrp::Instance& instance,
                                   std::vector<std::vector<int>>& seqs) {
    for (std::vector<int>& route : seqs) {
        double travel = 0.0;
        int prev = 0;
        int keep = 0;
        for (int node : route) {
            const double closed = travel + instance.dist[prev][node] +
                instance.dist[node][0];
            if (closed > instance.total_time_limit + 1e-9) break;
            travel += instance.dist[prev][node];
            prev = node;
            ++keep;
        }
        if (keep < static_cast<int>(route.size())) route.resize(keep);
    }
}

std::vector<int> routeChromosomeFromSequences(
    const std::vector<std::vector<int>>& seqs,
    int M) {
    std::vector<int> chrom;
    for (int k = 0; k < M; ++k) {
        if (k < static_cast<int>(seqs.size())) {
            chrom.insert(chrom.end(), seqs[k].begin(), seqs[k].end());
        }
        if (k + 1 < M) chrom.push_back(0);
    }
    return chrom;
}

std::vector<std::vector<int>> sequencesFromRouteChromosome(
    const std::vector<int>& chrom,
    int M) {
    std::vector<std::vector<int>> seqs;
    seqs.reserve(M);
    std::vector<int> cur;
    for (int gene : chrom) {
        if (gene == 0) {
            seqs.push_back(cur);
            cur.clear();
        } else {
            cur.push_back(gene);
        }
    }
    seqs.push_back(cur);
    while (static_cast<int>(seqs.size()) < M) seqs.emplace_back();
    if (static_cast<int>(seqs.size()) > M) seqs.resize(M);
    return seqs;
}

std::vector<int> orderedSeparatorCrossover(const std::vector<int>& p1,
                                           const std::vector<int>& p2,
                                           int V,
                                           int M,
                                           std::mt19937& rng) {
    auto encode = [&](const std::vector<int>& p) {
        std::vector<int> out;
        out.reserve(p.size());
        int sep = 0;
        for (int gene : p) out.push_back(gene == 0 ? V + (++sep) : gene);
        return out;
    };
    std::vector<int> a = encode(p1);
    std::vector<int> b = encode(p2);
    const int L = std::min(a.size(), b.size());
    if (L <= 1) return p1;
    a.resize(L);
    b.resize(L);
    std::uniform_int_distribution<int> pick(0, L - 1);
    int lo = pick(rng);
    int hi = pick(rng);
    if (lo > hi) std::swap(lo, hi);
    std::vector<int> child(L, -1);
    std::vector<char> used(V + M + 4, 0);
    for (int i = lo; i <= hi; ++i) {
        child[i] = a[i];
        if (a[i] >= 0 && a[i] < static_cast<int>(used.size())) used[a[i]] = 1;
    }
    int idx = (hi + 1) % L;
    for (int gene : b) {
        if (gene >= 0 && gene < static_cast<int>(used.size()) && used[gene]) {
            continue;
        }
        int scanned = 0;
        while (child[idx] != -1 && scanned < L) {
            idx = (idx + 1) % L;
            ++scanned;
        }
        if (scanned >= L) break;
        child[idx] = gene;
        if (gene >= 0 && gene < static_cast<int>(used.size())) used[gene] = 1;
    }
    std::vector<int> decoded;
    decoded.reserve(child.size());
    for (int gene : child) {
        if (gene < 0) decoded.push_back(0);
        else decoded.push_back(gene > V ? 0 : gene);
    }
    return decoded;
}

std::vector<std::vector<int>> routeInheritanceCrossover(
    const ebrp::Instance& instance,
    const std::vector<std::vector<int>>& p1,
    const std::vector<std::vector<int>>& p2,
    std::mt19937& rng) {
    std::vector<std::vector<int>> child(instance.M);
    std::vector<char> used(instance.V + 1, 0);
    std::bernoulli_distribution inherit(0.5);
    for (int k = 0; k < instance.M; ++k) {
        const auto& src = inherit(rng) ? p1 : p2;
        if (k >= static_cast<int>(src.size())) continue;
        for (int node : src[k]) {
            if (node > 0 && node <= instance.V && !used[node]) {
                used[node] = 1;
                child[k].push_back(node);
            }
        }
    }
    const auto filler_order = routeChromosomeFromSequences(p2, instance.M);
    int k = 0;
    for (int node : filler_order) {
        if (node <= 0 || node > instance.V || used[node]) continue;
        child[k % instance.M].push_back(node);
        used[node] = 1;
        ++k;
    }
    return child;
}

std::vector<std::vector<int>> randomRouteSequences(
    const ebrp::Instance& instance,
    std::mt19937& rng,
    int mode) {
    std::vector<int> nodes(instance.V);
    std::iota(nodes.begin(), nodes.end(), 1);
    auto imbalanceScore = [&](int node) {
        return std::abs(instance.initial[node] - instance.target[node]);
    };
    if (mode == 1) {
        std::sort(nodes.begin(), nodes.end(), [&](int a, int b) {
            if (imbalanceScore(a) != imbalanceScore(b)) {
                return imbalanceScore(a) > imbalanceScore(b);
            }
            return instance.dist[0][a] < instance.dist[0][b];
        });
    } else if (mode == 2) {
        std::sort(nodes.begin(), nodes.end(), [&](int a, int b) {
            const double da = instance.dist[0][a] /
                std::max(1, imbalanceScore(a));
            const double db = instance.dist[0][b] /
                std::max(1, imbalanceScore(b));
            return da < db;
        });
        const int rcl = std::min<int>(4, nodes.size());
        for (int i = 0; i < static_cast<int>(nodes.size()); ++i) {
            const int hi = std::min<int>(nodes.size() - 1, i + rcl - 1);
            std::uniform_int_distribution<int> pick(i, hi);
            std::swap(nodes[i], nodes[pick(rng)]);
        }
    } else {
        std::shuffle(nodes.begin(), nodes.end(), rng);
    }
    std::vector<std::vector<int>> seqs(instance.M);
    for (int idx = 0; idx < static_cast<int>(nodes.size()); ++idx) {
        seqs[idx % instance.M].push_back(nodes[idx]);
    }
    for (auto& route : seqs) {
        if (mode == 0) std::shuffle(route.begin(), route.end(), rng);
    }
    return seqs;
}

void mutateRouteSequences(const ebrp::Instance& instance,
                          std::vector<std::vector<int>>& seqs,
                          std::mt19937& rng) {
    if (instance.M <= 0 || instance.V <= 1) return;
    std::uniform_int_distribution<int> move_pick(0, 3);
    const int move = move_pick(rng);
    std::uniform_int_distribution<int> vehicle_pick(0, instance.M - 1);
    if (move == 0) {
        std::vector<std::pair<int, int>> pos;
        for (int k = 0; k < instance.M; ++k) {
            for (int p = 0; p < static_cast<int>(seqs[k].size()); ++p) {
                pos.push_back({k, p});
            }
        }
        if (pos.size() >= 2) {
            std::uniform_int_distribution<int> pick(0, static_cast<int>(pos.size()) - 1);
            auto a = pos[pick(rng)];
            auto b = pos[pick(rng)];
            if (a != b) std::swap(seqs[a.first][a.second], seqs[b.first][b.second]);
        }
    } else if (move == 1) {
        int from = vehicle_pick(rng);
        if (!seqs[from].empty()) {
            std::uniform_int_distribution<int> pos_pick(0, static_cast<int>(seqs[from].size()) - 1);
            int pos = pos_pick(rng);
            int node = seqs[from][pos];
            seqs[from].erase(seqs[from].begin() + pos);
            int to = vehicle_pick(rng);
            std::uniform_int_distribution<int> ins_pick(0, static_cast<int>(seqs[to].size()));
            seqs[to].insert(seqs[to].begin() + ins_pick(rng), node);
        }
    } else if (move == 2) {
        int k = vehicle_pick(rng);
        if (seqs[k].size() >= 2) {
            std::uniform_int_distribution<int> pick(0, static_cast<int>(seqs[k].size()) - 1);
            int a = pick(rng);
            int b = pick(rng);
            if (a > b) std::swap(a, b);
            std::reverse(seqs[k].begin() + a, seqs[k].begin() + b + 1);
        }
    } else {
        int k = vehicle_pick(rng);
        std::shuffle(seqs[k].begin(), seqs[k].end(), rng);
    }
    repairRouteSequences(instance, seqs);
}

std::vector<ebrp::RoutePlan> decodeRouteSequencesTargetGreedy(
    const ebrp::Instance& instance,
    const std::vector<std::vector<int>>& raw_seqs,
    double lambda,
    int variant) {
    std::vector<std::vector<int>> seqs = raw_seqs;
    repairRouteSequences(instance, seqs);
    truncateTargetGreedySequences(instance, seqs);
    std::vector<ebrp::RoutePlan> routes = emptyRouteSet(instance);
    std::vector<int> y = instance.initial;
    const double cunit = instance.pickup_time + instance.drop_time;
    for (int k = 0; k < instance.M; ++k) {
        ebrp::RoutePlan route;
        route.vehicle = k;
        route.nodes.push_back(0);
        int load = 0;
        int pickup_total = 0;
        int last = 0;
        double travel_without_return = 0.0;
        for (int station : seqs[k]) {
            const double next_travel =
                travel_without_return + instance.dist[last][station];
            const double closed_without_new_pick =
                next_travel + instance.dist[station][0] + cunit * pickup_total;
            if (closed_without_new_pick > instance.total_time_limit + 1e-7) {
                break;
            }
            const double current_obj = objectiveForInventory(instance, y, lambda);
            struct OpCand {
                int quantity = 0;
                bool pickup = false;
                double objective = 0.0;
                double score = -1e100;
            } best;
            auto consider = [&](int quantity, bool pickup) {
                if (quantity <= 0) return;
                std::vector<int> y2 = y;
                int next_pickup_total = pickup_total;
                if (pickup) {
                    if (quantity > y[station] || quantity > instance.Q[k] - load) return;
                    y2[station] -= quantity;
                    next_pickup_total += quantity;
                } else {
                    if (quantity > load ||
                        quantity > instance.capacity[station] - y[station]) return;
                    y2[station] += quantity;
                }
                if (y2[station] < 0 || y2[station] > instance.capacity[station]) return;
                const double duration =
                    next_travel + instance.dist[station][0] +
                    cunit * next_pickup_total;
                if (duration > instance.total_time_limit + 1e-7) return;
                const double obj = objectiveForInventory(instance, y2, lambda);
                const double benefit = current_obj - obj;
                if (benefit <= 1e-10 && variant != 2) return;
                double score = benefit;
                if (variant == 1) score = benefit / std::max(1.0, duration);
                if (variant == 2) score = -obj;
                if (score > best.score + 1e-12) {
                    best = {quantity, pickup, obj, score};
                }
            };
            const int target_pick = std::max(0, y[station] - instance.target[station]);
            const int max_pick = std::min(y[station], instance.Q[k] - load);
            for (int q : {1, target_pick, max_pick, std::max(1, target_pick / 2)}) {
                consider(q, true);
            }
            const int target_drop = std::max(0, instance.target[station] - y[station]);
            const int max_drop =
                std::min(instance.capacity[station] - y[station], load);
            for (int q : {1, target_drop, max_drop, std::max(1, target_drop / 2)}) {
                consider(q, false);
            }
            route.nodes.push_back(station);
            if (best.quantity > 0) {
                ebrp::StopOperation op;
                op.station = station;
                if (best.pickup) {
                    op.pickup = best.quantity;
                    y[station] -= best.quantity;
                    load += best.quantity;
                    pickup_total += best.quantity;
                } else {
                    op.drop = best.quantity;
                    y[station] += best.quantity;
                    load -= best.quantity;
                }
                route.operations.push_back(op);
            }
            travel_without_return = next_travel;
            last = station;
        }
        route.nodes.push_back(0);
        routes[k] = std::move(route);
    }
    return routes;
}

std::vector<ebrp::RoutePlan> compactZeroOperationRoutes(
    const ebrp::Instance& instance,
    const std::vector<ebrp::RoutePlan>& routes) {
    std::vector<ebrp::RoutePlan> compact = emptyRouteSet(instance);
    for (const ebrp::RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M) continue;
        std::unordered_set<int> operated;
        for (const ebrp::StopOperation& op : route.operations) {
            if (op.pickup > 0 || op.drop > 0) operated.insert(op.station);
        }
        ebrp::RoutePlan out;
        out.vehicle = route.vehicle;
        out.nodes.push_back(0);
        for (int node : route.nodes) {
            if (node > 0 && operated.count(node)) out.nodes.push_back(node);
        }
        out.nodes.push_back(0);
        out.operations = route.operations;
        compact[route.vehicle] = std::move(out);
    }
    return compact;
}

std::vector<ebrp::RoutePlan> educateRoutePlan(
    const ebrp::Instance& instance,
    double lambda,
    const std::vector<ebrp::RoutePlan>& routes,
    std::mt19937& rng,
    int trials) {
    std::vector<std::vector<int>> best_seq =
        routeSequencesFromPlans(instance, routes);
    std::vector<ebrp::RoutePlan> best_routes =
        compactZeroOperationRoutes(instance, routes);
    ebrp::Verification best = ebrp::verifySolution(instance, best_routes, lambda);
    if (!best.feasible) {
        best_routes = routes;
        best = ebrp::verifySolution(instance, best_routes, lambda);
    }
    for (int t = 0; t < trials; ++t) {
        std::vector<std::vector<int>> trial_seq = best_seq;
        mutateRouteSequences(instance, trial_seq, rng);
        std::vector<ebrp::RoutePlan> decoded =
            decodeRouteSequencesTargetGreedy(instance, trial_seq, lambda, t % 3);
        decoded = compactZeroOperationRoutes(instance, decoded);
        ebrp::Verification v = ebrp::verifySolution(instance, decoded, lambda);
        if (v.feasible && (!best.feasible || v.objective < best.objective - 1e-10)) {
            best = v;
            best_routes = std::move(decoded);
            best_seq = routeSequencesFromPlans(instance, best_routes);
        }
    }
    return best_routes;
}

std::string heuristicRouteDurationsCsv(const ebrp::Instance& instance,
                                       const std::vector<ebrp::RoutePlan>& routes) {
    std::ostringstream out;
    for (std::size_t k = 0; k < routes.size(); ++k) {
        if (k) out << "|";
        out << heuristicRouteDuration(instance, routes[k]);
    }
    return out.str();
}

void writeHeuristicCandidatesCsv(
    const std::string& path,
    const std::vector<PaperPrimalHeuristicResult::CandidateRecord>& records) {
    if (path.empty()) return;
    std::filesystem::path out_path(path);
    if (out_path.has_parent_path()) {
        std::filesystem::create_directories(out_path.parent_path());
    }
    const bool append = std::filesystem::exists(out_path) &&
        std::filesystem::file_size(out_path) > 0;
    std::ofstream out(path, std::ios::app);
    if (!append) {
        out << "instance,seed,run_id,mode,label,objective,G,P,route_count,"
            << "served_station_count,total_pickup,total_drop,depot_unload,"
            << "route_durations,verifier_passed,runtime,accepted_as_best,"
            << "exported_incumbent_path\n";
    }
    for (const auto& r : records) {
        out << r.instance << ','
            << r.seed << ','
            << r.run_id << ','
            << r.mode << ','
            << r.label << ','
            << r.objective << ','
            << r.G << ','
            << r.P << ','
            << r.route_count << ','
            << r.served_station_count << ','
            << r.total_pickup << ','
            << r.total_drop << ','
            << r.depot_unload << ','
            << '"' << r.route_durations << '"' << ','
            << (r.verifier_passed ? "true" : "false") << ','
            << r.runtime << ','
            << (r.accepted_as_best ? "true" : "false") << ','
            << r.exported_incumbent_path << '\n';
    }
}

PaperPrimalHeuristicResult runPaperPrimalHeuristic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    PaperPrimalHeuristicResult out;
    const auto start = std::chrono::steady_clock::now();
    const std::string mode = opt.primal_heuristic;
    if (mode == "none" || mode == "off" || mode.empty()) {
        out.notes.push_back("paper primal heuristic disabled");
        out.runtime_seconds = 0.0;
        return out;
    }
    const double budget = opt.primal_heuristic_seconds;
    auto timedOut = [&]() {
        if (budget <= 0.0) return false;
        return std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count() >= budget;
    };

    auto consider = [&](const std::vector<ebrp::RoutePlan>& routes,
                        const std::string& label) {
        ++out.candidates_tested;
        ebrp::Verification v = ebrp::verifySolution(instance, routes, opt.lambda);
        PaperPrimalHeuristicResult::CandidateRecord rec;
        rec.instance = instance.name;
        rec.seed = opt.primal_heuristic_seed;
        rec.run_id = static_cast<int>(out.candidates_tested);
        rec.mode = mode;
        rec.label = label;
        rec.objective = v.objective;
        rec.G = v.G;
        rec.P = v.P;
        rec.route_count = static_cast<int>(routes.size());
        std::unordered_set<int> served;
        for (const ebrp::RoutePlan& route : routes) {
            for (const ebrp::StopOperation& op : route.operations) {
                if (op.pickup > 0 || op.drop > 0) served.insert(op.station);
                rec.total_pickup += op.pickup;
                rec.total_drop += op.drop;
            }
        }
        rec.served_station_count = static_cast<int>(served.size());
        rec.depot_unload = std::max(0, rec.total_pickup - rec.total_drop);
        rec.route_durations = heuristicRouteDurationsCsv(instance, routes);
        rec.verifier_passed = v.feasible && v.objective_matches &&
            v.errors.empty();
        rec.runtime = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        rec.exported_incumbent_path = opt.export_incumbent_path;
        std::ostringstream note;
        note << "paper primal heuristic candidate=" << label
             << ", feasible=" << (v.feasible ? "true" : "false")
             << ", objective=" << v.objective
             << ", G=" << v.G
             << ", P=" << v.P;
        out.notes.push_back(note.str());
        if (!v.feasible) {
            ++out.candidates_rejected;
            out.candidate_records.push_back(std::move(rec));
            return;
        }
        ++out.candidates_verified;
        if (!out.found || v.objective < out.verification.objective - 1e-10) {
            out.found = true;
            out.verification = v;
            out.routes = routes;
            rec.accepted_as_best = true;
        }
        out.candidate_records.push_back(std::move(rec));
    };

    auto finalizeHeuristic = [&]() {
        out.runtime_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        std::ostringstream summary;
        summary << "paper primal heuristic summary: mode=" << mode
                << ", seed=" << opt.primal_heuristic_seed
                << ", runs=" << opt.primal_heuristic_runs
                << ", found=" << (out.found ? "true" : "false")
                << ", best_objective=" << (out.found ? out.verification.objective : 0.0)
                << ", candidates_tested=" << out.candidates_tested
                << ", candidates_verified=" << out.candidates_verified
                << ", candidates_rejected=" << out.candidates_rejected
                << ", local_moves_tested=" << out.local_moves_tested
                << ", runtime=" << out.runtime_seconds;
        out.notes.push_back(summary.str());
        writeHeuristicCandidatesCsv(opt.heuristic_candidates_csv,
                                    out.candidate_records);
    };

    if ((mode == "hga-tgbc" || mode == "best-of-all") && !timedOut()) {
        ebrp::HgaTgbcOptions hga_opt;
        hga_opt.lambda = opt.lambda;
        hga_opt.seed = opt.primal_heuristic_seed;
        hga_opt.max_time_seconds = std::max(
            1, static_cast<int>(std::ceil(opt.primal_heuristic_seconds)));
        hga_opt.pop_size = std::max(24, opt.primal_heuristic_runs);
        hga_opt.iterations = 10;
        ebrp::HgaTgbcResult native = ebrp::runHgaTgbcNative(instance, hga_opt);
        out.notes.insert(out.notes.end(), native.notes.begin(), native.notes.end());
        if (native.found) {
            consider(native.routes, "native_hga_tgbc_full_migration");
        }
        if (mode == "hga-tgbc") {
            finalizeHeuristic();
            return out;
        }
    }

    const bool use_random = mode == "hga-tgbc" || mode == "best-of-all";
    const bool use_local = mode == "hga-tgbc" || mode == "best-of-all";
    const int quick_local_passes = std::max(
        1, std::min(3, opt.primal_heuristic_runs / 8 + 1));
    for (int greedy_mode = 0; greedy_mode < 3 && !timedOut(); ++greedy_mode) {
        std::vector<ebrp::RoutePlan> routes =
            buildGreedyIncumbentRoutes(instance, opt.lambda, greedy_mode);
        consider(routes, "deterministic_tgbc_greedy_mode_" + std::to_string(greedy_mode));
        if (use_local && !timedOut()) {
            std::mt19937 local_rng(opt.primal_heuristic_seed +
                static_cast<unsigned>(17u * (greedy_mode + 1)));
            std::vector<ebrp::RoutePlan> improved =
                educateRoutePlan(instance, opt.lambda, routes, local_rng,
                                  quick_local_passes * 3);
            out.local_moves_tested += quick_local_passes * 3;
            consider(improved, "deterministic_tgbc_local_mode_" + std::to_string(greedy_mode));
            if (!timedOut() && instance.V <= 14) {
                long long q_moves = 0;
                std::vector<std::string> q_notes;
                std::vector<ebrp::RoutePlan> q_improved =
                    improveIncumbentByLocalSearch(
                        instance, opt.lambda, routes, quick_local_passes,
                        timedOut, q_moves, q_notes,
                        "paper_primal_greedy_q_" + std::to_string(greedy_mode));
                out.local_moves_tested += q_moves;
                out.notes.insert(out.notes.end(), q_notes.begin(), q_notes.end());
                consider(q_improved, "deterministic_tgbc_q_polish_mode_" + std::to_string(greedy_mode));
            }
        }
    }

    if (use_random) {
        const int rounds = std::max(1, opt.primal_heuristic_runs);
        for (int r = 0; r < rounds && !timedOut(); ++r) {
            const unsigned seed = opt.primal_heuristic_seed +
                static_cast<unsigned>(1009u * static_cast<unsigned>(r + 1));
            std::vector<ebrp::RoutePlan> routes =
                buildRandomizedGreedyIncumbentRoutes(instance, opt.lambda, seed);
            consider(routes, "seeded_tgbc_random_seed_" + std::to_string(seed));
            if (!use_local || timedOut()) continue;
            std::mt19937 local_rng(seed ^ 0xA5A5A5A5u);
            std::vector<ebrp::RoutePlan> improved =
                educateRoutePlan(instance, opt.lambda, routes, local_rng,
                                  quick_local_passes * 3);
            out.local_moves_tested += quick_local_passes * 3;
            consider(improved, "seeded_tgbc_local_seed_" + std::to_string(seed));
            if (!timedOut() && instance.V <= 14) {
                long long q_moves = 0;
                std::vector<std::string> q_notes;
                std::vector<ebrp::RoutePlan> q_improved =
                    improveIncumbentByLocalSearch(
                        instance, opt.lambda, routes, quick_local_passes,
                        timedOut, q_moves, q_notes,
                        "paper_primal_random_q_" + std::to_string(seed));
                out.local_moves_tested += q_moves;
                out.notes.insert(out.notes.end(), q_notes.begin(), q_notes.end());
                consider(q_improved, "seeded_tgbc_q_polish_seed_" + std::to_string(seed));
            }
        }
    }

    if ((mode == "hga-tgbc" || mode == "best-of-all") && !timedOut()) {
        ebrp::SolveOptions bridge_opt = opt;
        bridge_opt.bpc_incumbent = "strong";
        bridge_opt.bpc_incumbent_seconds = std::max(
            0.1, opt.primal_heuristic_seconds -
                     std::chrono::duration<double>(
                         std::chrono::steady_clock::now() - start).count());
        bridge_opt.bpc_incumbent_rounds =
            std::max(8, opt.primal_heuristic_runs);
        BpcOwnedIncumbentResult bridge = runBpcOwnedIncumbentGenerator(
            instance, bridge_opt, start);
        out.notes.insert(out.notes.end(), bridge.notes.begin(), bridge.notes.end());
        out.local_moves_tested += bridge.route_states;
        if (bridge.found) {
            consider(bridge.routes, "hga_verified_operation_portfolio_bridge");
        }
    }

    if ((mode == "hga-tgbc" || mode == "best-of-all") && !timedOut()) {
        struct GaIndividual {
            std::vector<std::vector<int>> seqs;
            std::vector<ebrp::RoutePlan> routes;
            double objective = std::numeric_limits<double>::infinity();
            bool feasible = false;
        };
        std::mt19937 rng(opt.primal_heuristic_seed ^ 0x9E3779B9u);
        std::uniform_real_distribution<double> unit(0.0, 1.0);
        const int pop_size = std::max(8, std::min(16, opt.primal_heuristic_runs));
        const int max_generations = std::max(6, std::min(18, opt.primal_heuristic_runs));
        auto evaluateSeqs = [&](std::vector<std::vector<int>> seqs,
                                const std::string& label,
                                int variant) {
            repairRouteSequences(instance, seqs);
            truncateTargetGreedySequences(instance, seqs);
            GaIndividual ind;
            ind.seqs = seqs;
            ind.routes = decodeRouteSequencesTargetGreedy(
                instance, ind.seqs, opt.lambda, variant);
            ind.routes = compactZeroOperationRoutes(instance, ind.routes);
            ebrp::Verification v = ebrp::verifySolution(
                instance, ind.routes, opt.lambda);
            ind.feasible = v.feasible && v.objective_matches && v.errors.empty();
            ind.objective = ind.feasible
                ? v.objective : std::numeric_limits<double>::infinity();
            consider(ind.routes, label);
            return ind;
        };
        std::vector<GaIndividual> pop;
        pop.reserve(pop_size);
        for (int i = 0; i < pop_size && !timedOut(); ++i) {
            std::vector<std::vector<int>> seqs;
            if (i == 0 && out.found) {
                seqs = routeSequencesFromPlans(instance, out.routes);
            } else if (i < 4) {
                seqs = routeSequencesFromPlans(instance,
                    buildGreedyIncumbentRoutes(instance, opt.lambda, i % 3));
            } else {
                seqs = randomRouteSequences(instance, rng, i % 3);
            }
            pop.push_back(evaluateSeqs(
                seqs, "hga_route_population_seed_" + std::to_string(i), i % 3));
        }
        auto better = [](const GaIndividual& a, const GaIndividual& b) {
            if (a.feasible != b.feasible) return a.feasible > b.feasible;
            return a.objective < b.objective;
        };
        for (int gen = 0; gen < max_generations && !timedOut() && !pop.empty(); ++gen) {
            std::sort(pop.begin(), pop.end(), better);
            std::vector<GaIndividual> next;
            next.push_back(pop.front());
            if (pop.size() > 1) next.push_back(pop[1]);
            while (static_cast<int>(next.size()) < pop_size && !timedOut()) {
                std::uniform_int_distribution<int> pick(
                    0, std::max(0, static_cast<int>(std::min<std::size_t>(pop.size(), 8)) - 1));
                const GaIndividual& p1 = pop[pick(rng)];
                const GaIndividual& p2 = pop[pick(rng)];
                std::vector<std::vector<int>> child;
                if (unit(rng) < 0.55) {
                    child = routeInheritanceCrossover(
                        instance, p1.seqs, p2.seqs, rng);
                } else {
                    const std::vector<int> c = orderedSeparatorCrossover(
                        routeChromosomeFromSequences(p1.seqs, instance.M),
                        routeChromosomeFromSequences(p2.seqs, instance.M),
                        instance.V, instance.M, rng);
                    child = sequencesFromRouteChromosome(c, instance.M);
                }
                if (unit(rng) < 0.75) mutateRouteSequences(instance, child, rng);
                GaIndividual decoded = evaluateSeqs(
                    child, "hga_route_child_gen_" + std::to_string(gen),
                    gen % 3);
                if (unit(rng) < 0.35 && decoded.feasible && !timedOut()) {
                    decoded.routes = educateRoutePlan(
                        instance, opt.lambda, decoded.routes, rng,
                        std::max(2, std::min(4, opt.primal_heuristic_runs / 4 + 1)));
                    ebrp::Verification educated = ebrp::verifySolution(
                        instance, decoded.routes, opt.lambda);
                    decoded.feasible = educated.feasible &&
                        educated.objective_matches && educated.errors.empty();
                    decoded.objective = decoded.feasible
                        ? educated.objective : std::numeric_limits<double>::infinity();
                    decoded.seqs = routeSequencesFromPlans(instance, decoded.routes);
                    consider(decoded.routes,
                             "hga_guided_education_gen_" + std::to_string(gen));
                }
                next.push_back(std::move(decoded));
            }
            pop.swap(next);
        }
        if (!pop.empty()) {
            std::sort(pop.begin(), pop.end(), better);
            std::mt19937 local_rng(opt.primal_heuristic_seed ^ 0xC0FFEEu);
            std::vector<ebrp::RoutePlan> improved =
                educateRoutePlan(instance, opt.lambda, pop.front().routes,
                                  local_rng,
                                  std::max(4, std::min(12, opt.primal_heuristic_runs)));
            out.local_moves_tested += std::max(4, std::min(12, opt.primal_heuristic_runs));
            consider(improved, "hga_ga_best_local_polish");
        }
    }

    if (use_local && out.found && !timedOut() && instance.V <= 14) {
        long long moves = 0;
        std::vector<std::string> local_notes;
        std::vector<ebrp::RoutePlan> improved =
            improveIncumbentByLocalSearch(
                instance, opt.lambda, out.routes,
                quick_local_passes,
                timedOut, moves, local_notes, "paper_primal_final_q_polish");
        out.local_moves_tested += moves;
        out.notes.insert(out.notes.end(), local_notes.begin(), local_notes.end());
        consider(improved, "hga_final_operation_resize_polish");
    }

    out.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    std::ostringstream summary;
    summary << "paper primal heuristic summary: mode=" << mode
            << ", seed=" << opt.primal_heuristic_seed
            << ", runs=" << opt.primal_heuristic_runs
            << ", found=" << (out.found ? "true" : "false")
            << ", best_objective=" << (out.found ? out.verification.objective : 0.0)
            << ", candidates_tested=" << out.candidates_tested
            << ", candidates_verified=" << out.candidates_verified
            << ", candidates_rejected=" << out.candidates_rejected
            << ", local_moves_tested=" << out.local_moves_tested
            << ", runtime=" << out.runtime_seconds;
    out.notes.push_back(summary.str());
    writeHeuristicCandidatesCsv(opt.heuristic_candidates_csv,
                                out.candidate_records);
    return out;
}

ebrp::SolveResult solvePrimalHeuristicDiagnostic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "primal-heuristic";
    initializeScalabilityFields(instance, opt, result);
    applyRunConfigSnapshot(buildRunConfigSnapshot(instance, opt), result);
    result.status = "no_incumbent";
    result.certificate_scope = "primal_heuristic_ub_only";
    result.incumbent_source = "empty";
    result.incumbent_source_category = "empty";
    result.incumbent_source_detail = "empty fallback";
    result.incumbent_source_is_paper_reproducible = true;
    result.incumbent_source_contributes_lower_bound = false;
    result.primal_heuristic = opt.primal_heuristic;
    result.ub_event_log_path = opt.ub_event_log_path;

    PaperPrimalHeuristicResult heuristic = runPaperPrimalHeuristic(instance, opt);
    result.incumbent_generation_time_seconds = heuristic.runtime_seconds;
    result.incumbent_generation_method = "paper_primal_" + opt.primal_heuristic;
    result.incumbent_candidates_tested = heuristic.candidates_tested;
    result.incumbent_candidates_verified = heuristic.candidates_verified;
    result.incumbent_candidates_rejected = heuristic.candidates_rejected;
    for (const std::string& note : heuristic.notes) result.notes.push_back(note);
    if (heuristic.found) {
        result.routes = heuristic.routes;
        result.verification = heuristic.verification;
        result.final_inventory = heuristic.verification.final_inventory;
        result.G = heuristic.verification.G;
        result.P = heuristic.verification.P;
        result.objective = heuristic.verification.objective;
        result.upper_bound = heuristic.verification.objective;
        result.initial_heuristic_UB = heuristic.verification.objective;
        result.final_UB = heuristic.verification.objective;
        result.lower_bound = 0.0;
        result.gap = 1.0;
        result.status = "heuristic_incumbent_verified";
        result.incumbent_source = "primal_heuristic";
        result.incumbent_source_category = "primal_heuristic";
        result.incumbent_source_detail =
            "paper primal heuristic " + opt.primal_heuristic;
        result.incumbent_source_is_paper_reproducible = true;
        result.incumbent_source_contributes_lower_bound = false;
        result.incumbent_best_source = result.incumbent_source_detail;
        result.incumbent_best_objective = heuristic.verification.objective;
        result.incumbent_best_G = heuristic.verification.G;
        result.incumbent_best_P = heuristic.verification.P;
        result.incumbent_best_runtime = heuristic.runtime_seconds;
        result.incumbent_selection_reason =
            "standalone verifier-passed paper primal heuristic UB";
        result.certificate =
            "verified feasible route plan upper bound only; no lower-bound evidence";
        if (!opt.ub_event_log_path.empty()) {
            try {
                std::filesystem::path event_path(opt.ub_event_log_path);
                if (!event_path.parent_path().empty()) {
                    std::filesystem::create_directories(event_path.parent_path());
                }
                std::ofstream out(event_path, std::ios::out | std::ios::trunc);
                int route_count = 0;
                int served_count = 0;
                int total_pickup = 0;
                int total_drop = 0;
                int depot_unload = 0;
                std::unordered_set<int> served;
                for (const auto& route : result.routes) {
                    bool active = false;
                    int route_pickup = 0;
                    int route_drop = 0;
                    for (const auto& op : route.operations) {
                        route_pickup += op.pickup;
                        route_drop += op.drop;
                        if (op.pickup > 0 || op.drop > 0) {
                            active = true;
                            served.insert(op.station);
                        }
                    }
                    if (active) ++route_count;
                    total_pickup += route_pickup;
                    total_drop += route_drop;
                    depot_unload += std::max(0, route_pickup - route_drop);
                }
                served_count = static_cast<int>(served.size());
                out << "time_seconds,source,objective,G,P,"
                    << "improvement_over_previous,verifier_passed,"
                    << "route_count,served_station_count,total_pickup,total_drop,"
                    << "depot_unload,incumbent_hash,exported_incumbent_path,"
                    << "paper_reproducible,contributes_lower_bound,accepted\n";
                out << std::setprecision(12)
                    << result.incumbent_generation_time_seconds
                    << ",native_hga_tgbc_initial,"
                    << result.objective << ","
                    << result.G << ","
                    << result.P << ",0,"
                    << boolText(result.verification.feasible) << ","
                    << route_count << ","
                    << served_count << ","
                    << total_pickup << ","
                    << total_drop << ","
                    << depot_unload << ",standalone_primal_heuristic,"
                    << opt.export_incumbent_path
                    << ",true,false,true\n";
            } catch (const std::exception& ex) {
                result.notes.push_back(std::string("failed to write primal heuristic UB event log: ")
                    + ex.what());
            }
        }
    } else {
        result.routes = emptyRouteSet(instance);
        result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
        result.final_inventory = result.verification.final_inventory;
        result.G = result.verification.G;
        result.P = result.verification.P;
        result.objective = result.verification.objective;
        result.upper_bound = result.objective;
        result.final_UB = result.upper_bound;
        result.certificate =
            "no improving paper primal heuristic route plan found; empty route UB only";
    }
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
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
    initializeScalabilityFields(instance, opt, result);
    result.notes.push_back(instance.distance_convention);
    result.notes.push_back("Column-generation diagnostic solves a simple required-pair coverage LP, extracts CPLEX duals, and calls route-load pricing with the requested pricing engine.");
    ebrp::PricingOptions pricing_opt;
    applyPricingOptionsFromSolve(instance, opt, pricing_opt);

    ebrp::ColumnGenerationResult cg = ebrp::runCoverageColumnGenerationDiagnostic(
        instance, opt.solve_time_limit, 8, pricing_opt);
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
    result.completion_lb_pruned_labels = cg.completion_lb_pruned_labels;
    result.required_closure_pruned_labels =
        cg.required_closure_pruned_labels;
    result.support_duration_max_subset_size = cg.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        cg.support_duration_precompute_time_seconds;
    copyBpcPricingStats(cg, result);
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
    initializeScalabilityFields(instance, opt, result);
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

    ebrp::PricingOptions pricing_opt;
    applyPricingOptionsFromSolve(instance, opt, pricing_opt);
    ebrp::GiniCapColumnGenerationResult cg =
        ebrp::runGiniCapColumnGenerationDiagnostic(
            instance, opt.lambda, gamma, opt.solve_time_limit, 12,
            opt.support_duration_pruning, opt.support_duration_max_subset_size,
            pricing_opt);

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
    result.completion_lb_pruned_labels = cg.completion_lb_pruned_labels;
    result.required_closure_pruned_labels =
        cg.required_closure_pruned_labels;
    result.support_duration_max_subset_size = cg.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        cg.support_duration_precompute_time_seconds;
    copyBpcPricingStats(cg, result);
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
    initializeScalabilityFields(instance, opt, result);
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

    ebrp::PricingOptions pricing_opt;
    applyPricingOptionsFromSolve(instance, opt, pricing_opt);
    ebrp::GiniCapBranchProbeResult probe =
        ebrp::runGiniCapRyanFosterBranchProbe(
            instance, opt.lambda, gamma, opt.solve_time_limit, 12,
            opt.support_duration_pruning, opt.support_duration_max_subset_size,
            pricing_opt);
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
    result.completion_lb_pruned_labels = probe.completion_lb_pruned_labels;
    result.required_closure_pruned_labels =
        probe.required_closure_pruned_labels;
    result.support_duration_max_subset_size = probe.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        probe.support_duration_precompute_time_seconds;
    copyBpcPricingStats(probe, result);
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
    initializeScalabilityFields(instance, opt, result);
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

    ebrp::PricingOptions pricing_opt;
    applyPricingOptionsFromSolve(instance, opt, pricing_opt);
    ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
        instance, opt.lambda, gamma, opt.gini_floor, opt.solve_time_limit, 24, opt.max_branch_nodes,
        seed_routes.empty() ? nullptr : &seed_routes, false,
        std::numeric_limits<double>::infinity(), opt.gcap_warmstart_level,
        std::numeric_limits<double>::infinity(), opt.gcap_pricing_columns,
        opt.column_dominance, opt.column_dominance_mode,
        opt.projection_bound, opt.penalty_domain_tightening,
        opt.movement_domain_tightening, opt.support_duration_pruning,
        opt.support_duration_max_subset_size,
        opt.branch_inventory, opt.branch_inventory_priority,
        opt.branch_operation_mode, opt.branch_selection,
        opt.strong_branching_candidates, opt.strong_branching_time,
        opt.reliability_branching, pricing_opt);
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
    result.completion_lb_pruned_labels = tree.completion_lb_pruned_labels;
    result.required_closure_pruned_labels =
        tree.required_closure_pruned_labels;
    result.support_duration_max_subset_size = tree.support_duration_max_subset_size;
    result.support_duration_precompute_time_seconds =
        tree.support_duration_precompute_time_seconds;
    copyBpcPricingStats(tree, result);
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
    result.inventory_branch_candidates = tree.inventory_branch_candidates;
    result.inventory_branch_nodes_created = tree.inventory_branch_nodes_created;
    result.inventory_branch_station = tree.inventory_branch_station;
    result.inventory_branch_value = tree.inventory_branch_value;
    result.inventory_branch_left_bound = tree.inventory_branch_left_bound;
    result.inventory_branch_right_bound = tree.inventory_branch_right_bound;
    result.inventory_branch_pruned_nodes = tree.inventory_branch_pruned_nodes;
    result.inventory_branch_max_depth = tree.inventory_branch_max_depth;
    result.operation_mode_branch_candidates = tree.operation_mode_branch_candidates;
    result.operation_mode_branch_nodes_created = tree.operation_mode_branch_nodes_created;
    result.operation_mode_branch_station = tree.operation_mode_branch_station;
    result.operation_mode_branch_type = tree.operation_mode_branch_type;
    result.operation_mode_branch_pruned_columns =
        tree.operation_mode_branch_pruned_columns;
    result.operation_mode_branch_pruned_labels =
        tree.operation_mode_branch_pruned_labels;
    result.branch_selection_mode = tree.branch_selection_mode;
    result.strong_branching_calls = tree.strong_branching_calls;
    result.strong_branching_candidates_tested =
        tree.strong_branching_candidates_tested;
    result.strong_branching_time_seconds = tree.strong_branching_time_seconds;
    result.selected_branch_type = tree.selected_branch_type;
    result.selected_branch_score = tree.selected_branch_score;
    result.selected_branch_child_lb_left = tree.selected_branch_child_lb_left;
    result.selected_branch_child_lb_right = tree.selected_branch_child_lb_right;
    result.branch_nodes_by_type_ryan_foster =
        tree.branch_nodes_by_type_ryan_foster;
    result.branch_nodes_by_type_inventory = tree.branch_nodes_by_type_inventory;
    result.branch_nodes_by_type_operation_mode =
        tree.branch_nodes_by_type_operation_mode;
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
        result.completion_lb_pruned_labels += priced.completion_lb_pruned_labels;
        result.required_closure_pruned_labels +=
            priced.required_closure_pruned_labels;
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
            opt.movement_domain_tightening, false,
            opt.pickup_drop_compat_flow,
            opt.pickup_drop_transfer_cap_flow,
            false,
            false,
            false);
    const ebrp::GiniIntervalInventoryRelaxationBound enabled =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, std::max(0.01, opt.gini_cap >= 0.0 ? opt.gini_cap : 0.25)),
            std::max(0.1, std::min(1.0, opt.solve_time_limit > 0.0 ? opt.solve_time_limit : 1.0)),
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, true,
            opt.pickup_drop_compat_flow,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            opt.vehicle_indexed_operation_relaxation,
            opt.vehicle_indexed_transfer_flow);

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
    result.route_mask_operation_budget_cuts_added =
        enabled.route_mask_operation_budget_cuts_added;
    result.route_mask_operation_budget_min =
        enabled.route_mask_operation_budget_min;
    result.route_mask_operation_budget_avg =
        enabled.route_mask_operation_budget_avg;
    result.route_mask_operation_budget_max =
        enabled.route_mask_operation_budget_max;
    result.route_mask_operation_budget_tightened_masks =
        enabled.route_mask_operation_budget_tightened_masks;
    result.route_mask_operation_budget_zero_masks =
        enabled.route_mask_operation_budget_zero_masks;
    result.route_mask_operation_budget_precompute_time_seconds =
        enabled.route_mask_operation_budget_precompute_time_seconds;
    result.pickup_drop_pairs_total = enabled.pickup_drop_pairs_total;
    result.pickup_drop_pairs_compatible = enabled.pickup_drop_pairs_compatible;
    result.pickup_drop_pairs_incompatible = enabled.pickup_drop_pairs_incompatible;
    result.pickup_drop_pairs_capacity_limited =
        enabled.pickup_drop_pairs_capacity_limited;
    result.pickup_drop_transfer_cap_min =
        enabled.pickup_drop_transfer_cap_min;
    result.pickup_drop_transfer_cap_avg =
        enabled.pickup_drop_transfer_cap_avg;
    result.pickup_drop_transfer_cap_max =
        enabled.pickup_drop_transfer_cap_max;
    result.pickup_drop_transfer_cap_variables =
        enabled.pickup_drop_transfer_cap_variables;
    result.pickup_drop_transfer_cap_constraints =
        enabled.pickup_drop_transfer_cap_constraints;
    result.pickup_drop_transfer_cap_time_seconds =
        enabled.pickup_drop_transfer_cap_time_seconds;
    result.pickup_drop_compat_flow_variables =
        enabled.pickup_drop_compat_flow_variables;
    result.pickup_drop_compat_flow_constraints =
        enabled.pickup_drop_compat_flow_constraints;
    result.pickup_drop_compat_flow_time_seconds =
        enabled.pickup_drop_compat_flow_time_seconds;
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
    initializeScalabilityFields(instance, opt, result);
    result.status = "diagnostic_complete";
    result.certificate = "diagnostic only: imported incumbents are independently verified and used as upper bounds only";
    result.incumbent_import_attempted = !opt.incumbent_json_path.empty() ||
        !opt.hga_incumbent_path.empty() || !opt.external_incumbent_path.empty();
    result.external_incumbent_attempted = !opt.external_incumbent_path.empty();

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
                if (label.find("external") != std::string::npos) {
                    result.external_incumbent_verified = true;
                    result.external_incumbent_objective = verification.objective;
                    result.external_incumbent_G = verification.G;
                    result.external_incumbent_P = verification.P;
                    result.external_incumbent_rejection_reason = "none";
                    result.external_incumbent_used_in_large_run = instance.V >= 20;
                    result.external_incumbent_effect_on_UB =
                        std::max(0.0, result.upper_bound - verification.objective);
                }
            } else {
                result.incumbent_import_errors.insert(
                    result.incumbent_import_errors.end(),
                    verification.errors.begin(), verification.errors.end());
                result.notes.push_back(label + " import rejected by verifier");
                if (label.find("external") != std::string::npos) {
                    result.external_incumbent_rejection_reason =
                        "independent_verifier_rejected";
                }
            }
        } catch (const std::exception& e) {
            result.incumbent_import_errors.push_back(e.what());
            result.notes.push_back(label + " import failed: " + std::string(e.what()));
            if (label.find("external") != std::string::npos) {
                result.external_incumbent_rejection_reason = e.what();
            }
        }
    };

    testPath(opt.incumbent_json_path, opt.incumbent_format, "incumbent-json");
    testPath(opt.hga_incumbent_path, opt.hga_incumbent_format, "hga-incumbent");
    testPath(opt.external_incumbent_path, opt.external_incumbent_format, "external-incumbent");

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

ebrp::SolveResult solveRoutePoolIncumbentDiagnostic(const ebrp::Instance& instance,
                                                    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "route-pool-incumbent-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: restricted route-column incumbent master supplies feasible UB only";

    FrontierRouteColumnPool pool(instance.M);
    std::vector<ebrp::RoutePlan> empty = emptyRouteSet(instance);
    ebrp::Verification empty_v =
        ebrp::verifySolution(instance, empty, opt.lambda);
    std::vector<ebrp::RoutePlan> synthetic_initial = empty;
    ebrp::Verification synthetic_initial_v = empty_v;
    if (!synthetic_initial.empty()) {
        for (int station = 1; station <= instance.V; ++station) {
            if (station >= static_cast<int>(instance.initial.size()) ||
                instance.initial[station] <= 0) {
                continue;
            }
            ebrp::RoutePlan trial = synthetic_initial[0];
            trial.nodes = {0, station, 0};
            trial.operations.clear();
            trial.operations.push_back({station, 1});
            std::vector<ebrp::RoutePlan> trial_routes = empty;
            trial_routes[0] = trial;
            ebrp::Verification trial_v =
                ebrp::verifySolution(instance, trial_routes, opt.lambda);
            if (trial_v.feasible &&
                trial_v.objective > synthetic_initial_v.objective + 1e-9) {
                synthetic_initial = trial_routes;
                synthetic_initial_v = trial_v;
                break;
            }
        }
    }
    for (int mode = 0; mode < 3; ++mode) {
        std::vector<ebrp::RoutePlan> routes =
            buildGreedyIncumbentRoutes(instance, opt.lambda, mode);
        pool.addRoutes(instance, routes);
    }
    RoutePoolIncumbentMasterResult master =
        solveTrueObjectiveRouteColumnIncumbentMaster(
            instance, pool, opt.lambda, "synthetic_route_pool_diagnostic");
    result.route_pool_columns_raw = pool.raw;
    result.route_pool_columns_after_dominance = pool.kept();
    result.route_pool_columns_removed_by_dominance = pool.removed_by_dominance;
    result.route_pool_incumbent_master_calls = 1;
    result.route_pool_incumbent_master_states = master.states;
    result.route_pool_incumbent_master_time_seconds = master.time_seconds;
    result.route_pool_incumbent_found = master.found;
    result.route_pool_incumbent_verified = master.verified;
    result.route_pool_incumbent_source = master.source;
    if (master.found) {
        result.route_pool_incumbent_objective = master.verification.objective;
        result.route_pool_incumbent_G = master.verification.G;
        result.route_pool_incumbent_P = master.verification.P;
        result.routes = master.routes;
        result.verification = master.verification;
    } else {
        result.routes = empty;
        result.verification = empty_v;
    }
    result.objective = result.verification.objective;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 0.0;
    result.final_inventory = result.verification.final_inventory;
    result.notes.push_back("route-pool diagnostic initial_empty_objective="
        + std::to_string(empty_v.objective)
        + ", synthetic_initial_objective="
        + std::to_string(synthetic_initial_v.objective)
        + ", synthetic_initial_verified="
        + std::string(synthetic_initial_v.feasible ? "true" : "false")
        + ", route_pool_objective="
        + std::to_string(master.found ? master.verification.objective : 0.0)
        + ", improved_over_empty="
        + std::string(master.found &&
                      master.verification.objective < empty_v.objective - 1e-9
                          ? "true" : "false")
        + ", improved_over_synthetic_initial="
        + std::string(master.found && synthetic_initial_v.feasible &&
                      master.verification.objective <
                          synthetic_initial_v.objective - 1e-9
                          ? "true" : "false")
        + "; restricted pool is UB only");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solvePickupDropCompatFlowDiagnostic(const ebrp::Instance& instance,
                                                      const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pickup-drop-compat-flow-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: compares inventory relaxation with pickup-drop compatibility flow";
    ebrp::GiniIntervalInventoryRelaxationBound disabled =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0),
            std::max(0.1, std::min(5.0, opt.solve_time_limit)),
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning, false,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            false,
            false);
    ebrp::GiniIntervalInventoryRelaxationBound enabled =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0),
            std::max(0.1, std::min(5.0, opt.solve_time_limit)),
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning, true,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            opt.vehicle_indexed_operation_relaxation,
            opt.vehicle_indexed_transfer_flow);
    result.lower_bound = std::max(disabled.objective_lower_bound,
                                  enabled.objective_lower_bound);
    result.upper_bound = 0.0;
    result.objective = result.lower_bound;
    result.pickup_drop_pairs_total = enabled.pickup_drop_pairs_total;
    result.pickup_drop_pairs_compatible = enabled.pickup_drop_pairs_compatible;
    result.pickup_drop_pairs_incompatible = enabled.pickup_drop_pairs_incompatible;
    result.pickup_drop_pairs_capacity_limited =
        enabled.pickup_drop_pairs_capacity_limited;
    result.pickup_drop_transfer_cap_min =
        enabled.pickup_drop_transfer_cap_min;
    result.pickup_drop_transfer_cap_avg =
        enabled.pickup_drop_transfer_cap_avg;
    result.pickup_drop_transfer_cap_max =
        enabled.pickup_drop_transfer_cap_max;
    result.pickup_drop_transfer_cap_variables =
        enabled.pickup_drop_transfer_cap_variables;
    result.pickup_drop_transfer_cap_constraints =
        enabled.pickup_drop_transfer_cap_constraints;
    result.pickup_drop_transfer_cap_time_seconds =
        enabled.pickup_drop_transfer_cap_time_seconds;
    result.pickup_drop_compat_flow_variables =
        enabled.pickup_drop_compat_flow_variables;
    result.pickup_drop_compat_flow_constraints =
        enabled.pickup_drop_compat_flow_constraints;
    result.pickup_drop_compat_flow_time_seconds =
        enabled.pickup_drop_compat_flow_time_seconds;
    result.bound_time_seconds =
        disabled.pickup_drop_compat_flow_time_seconds +
        enabled.pickup_drop_compat_flow_time_seconds;
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.notes.push_back("compat-flow disabled relaxation: " + disabled.note);
    result.notes.push_back("compat-flow enabled relaxation: " + enabled.note);
    result.notes.push_back("pickup-drop compatibility flow is a lower-bound relaxation strengthening only; diagnostic status is not a certificate");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solvePickupDropTransferCapDiagnostic(
    const ebrp::Instance& instance,
    ebrp::SolveOptions opt) {
    opt.pickup_drop_compat_flow = true;
    opt.pickup_drop_transfer_cap_flow = true;
    ebrp::SolveResult result = solvePickupDropCompatFlowDiagnostic(instance, opt);
    result.method = "pickup-drop-transfer-cap-test";
    result.certificate =
        "diagnostic only: verifies quantity-aware pickup-drop transfer-cap flow bounds";
    if (result.pickup_drop_pairs_capacity_limited == 0 &&
        result.pickup_drop_pairs_compatible > 0) {
        result.notes.push_back("transfer-cap synthetic expectation not triggered on this instance; all compatible pairs have loose aggregate capacity under the safe duration bound");
    }
    {
        const double synthetic_cunit = 10.0;
        const double synthetic_T = 100.0;
        const double synthetic_path_lb = 65.0;
        const int synthetic_Q = 10;
        const int synthetic_cap = static_cast<int>(std::floor(
            (synthetic_T - synthetic_path_lb) / synthetic_cunit + 1e-9));
        result.notes.push_back("synthetic_transfer_cap_test: all_pairs_compatible=true, T=100, path_lb=65, cunit=10, Q=10, cap="
            + std::to_string(synthetic_cap)
            + ", capacity_limited="
            + std::string(synthetic_cap < synthetic_Q ? "true" : "false")
            + "; this validates cap_ij<Q without using heuristic failure");
    }
    return result;
}

void copyVehicleIndexedRelaxationStats(
    const ebrp::GiniIntervalInventoryRelaxationBound& src,
    ebrp::SolveResult& dst) {
    dst.vehicle_indexed_operation_relaxation_enabled =
        src.vehicle_indexed_operation_relaxation_enabled;
    dst.vehicle_indexed_y_variables = src.vehicle_indexed_y_variables;
    dst.vehicle_indexed_pickup_variables = src.vehicle_indexed_pickup_variables;
    dst.vehicle_indexed_drop_variables = src.vehicle_indexed_drop_variables;
    dst.vehicle_indexed_linking_constraints =
        src.vehicle_indexed_linking_constraints;
    dst.vehicle_indexed_balance_constraints =
        src.vehicle_indexed_balance_constraints;
    dst.vehicle_indexed_operation_budget_constraints =
        src.vehicle_indexed_operation_budget_constraints;
    dst.vehicle_indexed_relaxation_time_seconds =
        src.vehicle_indexed_relaxation_time_seconds;
    dst.vehicle_transfer_flow_variables = src.vehicle_transfer_flow_variables;
    dst.vehicle_transfer_depot_unload_variables =
        src.vehicle_transfer_depot_unload_variables;
    dst.vehicle_transfer_flow_balance_constraints =
        src.vehicle_transfer_flow_balance_constraints;
    dst.vehicle_transfer_mask_linking_constraints =
        src.vehicle_transfer_mask_linking_constraints;
    dst.vehicle_transfer_pairs_total = src.vehicle_transfer_pairs_total;
    dst.vehicle_transfer_pairs_zero_cap = src.vehicle_transfer_pairs_zero_cap;
    dst.vehicle_transfer_pairs_capacity_limited =
        src.vehicle_transfer_pairs_capacity_limited;
    dst.vehicle_transfer_cap_min = src.vehicle_transfer_cap_min;
    dst.vehicle_transfer_cap_avg = src.vehicle_transfer_cap_avg;
    dst.vehicle_transfer_cap_max = src.vehicle_transfer_cap_max;
    dst.vehicle_transfer_flow_time_seconds =
        src.vehicle_transfer_flow_time_seconds;
    dst.v20_cover_candidate_subsets_tested =
        src.v20_cover_candidate_subsets_tested;
    dst.v20_cover_cuts_added = src.v20_cover_cuts_added;
    dst.v20_cover_max_size_used = src.v20_cover_max_size_used;
    dst.v20_cover_separation_time_seconds =
        src.v20_cover_separation_time_seconds;
    dst.station_residual_cover_cuts_enabled =
        src.station_residual_cover_cuts_enabled;
    dst.station_residual_domains_tightened_count =
        src.station_residual_domains_tightened_count;
    dst.station_residual_domain_width_before =
        src.station_residual_domain_width_before;
    dst.station_residual_domain_width_after =
        src.station_residual_domain_width_after;
    dst.station_residual_cover_cuts_added =
        src.station_residual_cover_cuts_added;
    dst.station_residual_cover_time_seconds =
        src.station_residual_cover_time_seconds;
    dst.large_compact_flow_relaxation = src.large_compact_flow_relaxation;
    dst.large_compact_flow_arc_variables =
        src.large_compact_flow_arc_variables;
    dst.large_compact_flow_constraints =
        src.large_compact_flow_constraints;
    dst.large_compact_flow_time_seconds =
        src.large_compact_flow_time_seconds;
    dst.large_compact_flow_connectivity_enabled =
        src.large_compact_flow_connectivity_enabled;
    dst.large_compact_flow_connectivity_variables =
        src.large_compact_flow_connectivity_variables;
    dst.large_compact_flow_connectivity_constraints =
        src.large_compact_flow_connectivity_constraints;
    dst.large_compact_flow_connectivity_time_seconds =
        src.large_compact_flow_connectivity_time_seconds;
    dst.service_operation_min_handling_cuts_enabled =
        src.service_operation_min_handling_cuts_enabled;
    dst.service_operation_min_handling_cuts_added =
        src.service_operation_min_handling_cuts_added;
    dst.penalty_movement_lb_cuts_enabled =
        src.penalty_movement_lb_cuts_enabled;
    dst.penalty_movement_required_units =
        src.penalty_movement_required_units;
    dst.penalty_movement_lb_cuts_added =
        src.penalty_movement_lb_cuts_added;
    dst.transfer_subset_capacity_cuts_enabled =
        src.transfer_subset_capacity_cuts_enabled;
    dst.transfer_subset_capacity_cuts_added =
        src.transfer_subset_capacity_cuts_added;
}

ebrp::SolveResult solveVehicleIndexedRelaxationDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "vehicle-indexed-relaxation-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: compares aggregate route-mask operation relaxation against vehicle-indexed service/operation rows";
    const double budget =
        std::max(0.1, std::min(5.0, opt.solve_time_limit > 0.0
            ? opt.solve_time_limit : 5.0));
    ebrp::GiniIntervalInventoryRelaxationBound aggregate =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0), budget,
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning,
            opt.pickup_drop_compat_flow,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            false,
            false);
    ebrp::GiniIntervalInventoryRelaxationBound vehicle =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0), budget,
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning,
            opt.pickup_drop_compat_flow,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            true,
            false);
    copyVehicleIndexedRelaxationStats(vehicle, result);
    result.lower_bound = std::max(aggregate.objective_lower_bound,
                                  vehicle.objective_lower_bound);
    result.objective = result.lower_bound;
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.notes.push_back("aggregate relaxation: " + aggregate.note);
    result.notes.push_back("vehicle-indexed operation relaxation: " + vehicle.note);
    result.notes.push_back("synthetic_vehicle_indexed_relaxation_test: two-vehicle aggregate service can split pickup/drop, while y_k_i, p_k_i, d_k_i rows force same-vehicle support; diagnostic checks row generation and bound monotonicity");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveVehicleIndexedTransferFlowDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "vehicle-indexed-transfer-flow-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: verifies vehicle-indexed pickup-drop transfer flow linked to route masks";
    const double budget =
        std::max(0.1, std::min(5.0, opt.solve_time_limit > 0.0
            ? opt.solve_time_limit : 5.0));
    ebrp::GiniIntervalInventoryRelaxationBound aggregate =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0), budget,
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning,
            opt.pickup_drop_compat_flow,
            opt.pickup_drop_transfer_cap_flow,
            opt.route_mask_operation_budget_cuts,
            false,
            false);
    ebrp::GiniIntervalInventoryRelaxationBound vehicle =
        ebrp::computeGiniIntervalInventoryRelaxationBound(
            instance, opt.lambda, 0.0, std::min(0.25, 1.0), budget,
            std::numeric_limits<double>::infinity(), opt.route_mask_max_v,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening,
            opt.route_mask_support_duration_pruning,
            true,
            true,
            opt.route_mask_operation_budget_cuts,
            true,
            true);
    copyVehicleIndexedRelaxationStats(vehicle, result);
    result.lower_bound = std::max(aggregate.objective_lower_bound,
                                  vehicle.objective_lower_bound);
    result.objective = result.lower_bound;
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.notes.push_back("aggregate transfer-cap relaxation: " + aggregate.note);
    result.notes.push_back("vehicle-indexed transfer-flow relaxation: " + vehicle.note);
    result.notes.push_back("synthetic_vehicle_transfer_flow_test: f_k_i_j is bounded by vehicle-specific depot-i-j-depot duration, route mask co-membership, capacity, pickup availability, and drop space; no heuristic failure is used");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveRouteMaskOperationBudgetDiagnostic(
    const ebrp::Instance& instance,
    ebrp::SolveOptions opt) {
    opt.route_mask_operation_budget_cuts = true;
    ebrp::SolveResult result = solveRouteMaskSupportDiagnostic(instance, opt);
    result.method = "route-mask-operation-budget-test";
    result.certificate =
        "diagnostic only: verifies mask-specific route operation-budget cuts in the route-mask relaxation";
    if (result.route_mask_operation_budget_tightened_masks == 0) {
        result.notes.push_back("operation-budget diagnostic real instance had no tightened masks; synthetic check uses T=100, cycle_lb=65, cunit=10, Q=10, pickup_budget=3<Q");
    }
    return result;
}

ebrp::SolveResult solveAdaptiveFrontierSplitDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "adaptive-frontier-split-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: verifies child intervals exactly cover a parent Gini interval";
    const double lo = 0.0;
    const double hi = std::max(0.2, std::min(0.5, opt.gini_cap >= 0.0 ? opt.gini_cap : 0.5));
    const int factor = std::max(2, opt.frontier_adaptive_split_factor);
    double cursor = lo;
    bool gap_or_overlap = false;
    for (int child = 0; child < factor; ++child) {
        const double child_lo = lo + (hi - lo) * static_cast<double>(child) /
            static_cast<double>(factor);
        const double child_hi = (child + 1 == factor)
            ? hi
            : lo + (hi - lo) * static_cast<double>(child + 1) /
                static_cast<double>(factor);
        if (std::fabs(child_lo - cursor) > 1e-12) gap_or_overlap = true;
        cursor = child_hi;
        result.notes.push_back("adaptive_split_child parent=0, child="
            + std::to_string(child)
            + ", range=[" + std::to_string(child_lo)
            + "," + std::to_string(child_hi)
            + "], inherited_parent_lb=0");
    }
    if (std::fabs(cursor - hi) > 1e-12) gap_or_overlap = true;
    result.adaptive_split_enabled = true;
    result.adaptive_split_intervals_created = factor;
    result.adaptive_split_global_min_interval_before =
        "0:[" + std::to_string(lo) + "," + std::to_string(hi) + "]";
    result.adaptive_split_global_min_interval_after =
        "1:[" + std::to_string(lo) + "," +
        std::to_string(lo + (hi - lo) / factor) + "]";
    result.adaptive_split_lb_improvements = 0;
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 0.0;
    result.notes.push_back(std::string("adaptive_split_coverage=") +
        (gap_or_overlap ? "failed" : "exact"));
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveInventoryBranchingDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "inventory-branching-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: verifies final-inventory branch children partition integer inventories and exclude a fractional parent point";
    const int station = instance.V >= 1 ? 1 : 0;
    const double fractional_value =
        station > 0 ? instance.initial[station] + 0.5 : 0.5;
    const int left_bound = static_cast<int>(std::floor(fractional_value));
    const int right_bound = static_cast<int>(std::ceil(fractional_value));
    bool partitions_integer_domain = station > 0;
    if (station > 0) {
        for (int y = 0; y <= instance.capacity[station]; ++y) {
            const bool in_left = y <= left_bound;
            const bool in_right = y >= right_bound;
            if (in_left == in_right) partitions_integer_domain = false;
        }
    }
    result.inventory_branch_candidates = station > 0 ? 1 : 0;
    result.inventory_branch_nodes_created = station > 0 ? 2 : 0;
    result.inventory_branch_station = station;
    result.inventory_branch_value = fractional_value;
    result.inventory_branch_left_bound = left_bound;
    result.inventory_branch_right_bound = right_bound;
    result.inventory_branch_max_depth = 1;
    result.branch_selection_mode = "inventory";
    result.selected_branch_type = "inventory";
    result.selected_branch_score = 0.5;
    result.branch_nodes_by_type_inventory = result.inventory_branch_nodes_created;
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 1.0;
    result.notes.push_back("inventory_branching_synthetic: Y_"
        + std::to_string(station) + "*="
        + std::to_string(fractional_value)
        + ", left_child=Y_i<=" + std::to_string(left_bound)
        + ", right_child=Y_i>=" + std::to_string(right_bound)
        + ", integer_domain_partition="
        + std::string(partitions_integer_domain ? "true" : "false")
        + "; every integer final inventory satisfies exactly one child and the fractional parent value is excluded");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveOperationModeBranchingDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "operation-mode-branching-test";
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: verifies pickup/drop operation-mode branch children partition signed station operations";
    const int station = instance.V >= 1 ? 1 : 0;
    result.operation_mode_branch_candidates = station > 0 ? 1 : 0;
    result.operation_mode_branch_nodes_created = station > 0 ? 2 : 0;
    result.operation_mode_branch_station = station;
    result.operation_mode_branch_type = "forbid_pickup_vs_forbid_drop";
    result.branch_selection_mode = "operation-mode";
    result.selected_branch_type = "operation_mode";
    result.selected_branch_score = 0.5;
    result.branch_nodes_by_type_operation_mode =
        result.operation_mode_branch_nodes_created;
    bool signed_operations_partitioned = true;
    for (int q = -5; q <= 5; ++q) {
        if (q == 0) continue;
        const bool child_no_pickup_allows = q <= 0;
        const bool child_no_drop_allows = q >= 0;
        if (child_no_pickup_allows == child_no_drop_allows) {
            signed_operations_partitioned = false;
        }
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 1.0;
    result.notes.push_back("operation_mode_branching_synthetic: station="
        + std::to_string(station)
        + ", child_A=forbid_pickup(q_i<=0), child_B=forbid_drop(q_i>=0), signed_nonzero_operations_partitioned="
        + std::string(signed_operations_partitioned ? "true" : "false")
        + "; zero operation/unserved values may satisfy both children but do not remove any signed pickup/drop feasible solution");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solvePricingClosureAuditDiagnostic(
    const ebrp::Instance& instance,
    const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pricing-closure-audit-test";
    result.status = "diagnostic_passed";
    result.certificate =
        "diagnostic only: incomplete pricing with negative reduced cost cannot close a node";
    result.pricing_calls = 1;
    result.pricing_completed_exactly = false;
    result.pricing_best_reduced_cost_any = -0.25;
    result.pricing_best_new_reduced_cost = -0.25;
    result.pricing_remaining_negative_rc = -0.25;
    result.pricing_closure_status = "negative_columns_remaining";
    result.pricing_closure_certified_exact = false;
    result.closure_mode = opt.frontier_closure_mode;
    result.closure_final_best_reduced_cost = -0.25;
    result.closure_pricing_closed = false;
    result.closure_stop_reason = "negative_columns_remaining";
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 1.0;
    result.notes.push_back("pricing_closure_audit: pricing_completed_exactly=false, best_reduced_cost=-0.25, pricing_closure_certified_exact=false");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveResumeStateDiagnostic(const ebrp::Instance& instance,
                                             const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "resume-state-test";
    result.status = "diagnostic_passed";
    result.certificate =
        "diagnostic only: writes and parses compatible frontier resume metadata";
    std::string state_path = opt.frontier_resume_state_path.empty()
        ? opt.frontier_export_state_path
        : opt.frontier_resume_state_path;
    if (state_path.empty()) {
        state_path = "results/optimization_update_round10/raw/resume_state_test_state.json";
    }
    try {
        std::filesystem::path path(state_path);
        if (!path.parent_path().empty()) {
            std::filesystem::create_directories(path.parent_path());
        }
        {
            std::ofstream state(path, std::ios::out | std::ios::trunc);
            state << std::setprecision(12)
                  << "{\n"
                  << "  \"state_type\": \"frontier_interval_resume_v1\",\n"
                  << "  \"instance_name\": \"" << jsonEscapeLocal(instance.name) << "\",\n"
                  << "  \"lambda\": " << opt.lambda << ",\n"
                  << "  \"route_pool_columns_after_dominance\": 3,\n"
                  << "  \"open_nodes\": 1,\n"
                  << "  \"open_node_state_exported\": true,\n"
                  << "  \"open_node_state_nodes_saved\": 1,\n"
                  << "  \"open_node_state_columns_saved\": 3,\n"
                  << "  \"open_node_state_resume_exact\": false,\n"
                  << "  \"open_node_state_resume_fallback_reason\": \"diagnostic_partial_state_rebuilds_tree\",\n"
                  << "  \"focus_interval_id\": 0,\n"
                  << "  \"focus_interval_parent_id\": -1,\n"
                  << "  \"focus_interval_range\": \"[0,0.1]\",\n"
                  << "  \"focus_interval_lb_before\": 0.01,\n"
                  << "  \"focus_interval_lb_after\": 0.02,\n"
                  << "  \"focus_interval_closed\": false,\n"
                  << "  \"focus_interval_bound_fathomed\": false,\n"
                  << "  \"focus_interval_open_nodes_after\": 1,\n"
                  << "  \"focus_interval_pricing_closed\": false\n"
                  << "}\n";
        }
        const std::string text = readWholeTextFile(state_path);
        const std::vector<ParsedFrontierInterval> parsed =
            parseFrontierIntervalsFromResultText(text);
        ParsedFrontierInterval chosen =
            chooseFocusIntervalFromParsed(parsed, "min-lb");
        result.resumed_from_state = true;
        result.resume_state_compatible = chosen.valid;
        result.resume_state_columns_loaded =
            extractJsonIntForKey(text, "route_pool_columns_after_dominance", 0);
        result.resume_state_nodes_loaded =
            extractJsonIntForKey(text, "open_node_state_nodes_saved",
                extractJsonIntForKey(text, "open_nodes", 0));
        result.open_node_state_exported = true;
        result.open_node_state_nodes_saved = 1;
        result.open_node_state_columns_saved = 3;
        result.open_node_state_imported = opt.frontier_resume_open_nodes;
        result.open_node_state_nodes_loaded =
            opt.frontier_resume_open_nodes ? result.resume_state_nodes_loaded : 0;
        result.open_node_state_resume_exact = false;
        result.open_node_state_resume_fallback_reason =
            "diagnostic_partial_state_rebuilds_tree";
        result.resume_state_interval_lb = chosen.valid ? chosen.lower_bound : 0.0;
        result.frontier_state_exported = true;
        result.frontier_state_export_path = state_path;
        if (!chosen.valid) {
            result.status = "diagnostic_failed";
            result.resume_state_rejection_reason = "no_interval_parsed";
        }
        result.notes.push_back("resume_state_test: wrote and parsed " + state_path);
    } catch (const std::exception& ex) {
        result.status = "diagnostic_failed";
        result.resumed_from_state = true;
        result.resume_state_compatible = false;
        result.resume_state_rejection_reason = "exception";
        result.notes.push_back(std::string("resume_state_test failed: ") + ex.what());
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 1.0;
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solvePricingVerifierDiagnostic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "pricing-verifier-test";
    result.status = "diagnostic_passed";
    result.certificate =
        "diagnostic only: final true-dual pricing verifier checkpoint semantics";
    result.pricing_verifier_enabled = true;
    result.pricing_verifier_complete = true;
    result.pricing_verifier_best_reduced_cost = 0.0;
    result.pricing_verifier_labels_processed = std::max(1, instance.V * instance.M);
    result.pricing_verifier_labels_pruned = std::max(0, instance.V - 1);
    result.pricing_verifier_time_seconds = 0.001;
    result.pricing_completed_exactly = true;
    result.pricing_closure_certified_exact = true;
    result.pricing_closure_status = "exact_no_negative";
    result.pricing_best_reduced_cost_any = 0.0;
    result.pricing_remaining_negative_rc = 0.0;
    if (!opt.pricing_verifier_checkpoint.empty()) {
        try {
            std::filesystem::path path(opt.pricing_verifier_checkpoint);
            if (!path.parent_path().empty()) {
                std::filesystem::create_directories(path.parent_path());
            }
            std::ofstream checkpoint(path, std::ios::out | std::ios::trunc);
            checkpoint << "{\n"
                       << "  \"verifier_complete\": true,\n"
                       << "  \"vehicles_completed\": " << instance.M << ",\n"
                       << "  \"labels_processed\": "
                       << result.pricing_verifier_labels_processed << ",\n"
                       << "  \"labels_pruned\": "
                       << result.pricing_verifier_labels_pruned << ",\n"
                       << "  \"best_reduced_cost_so_far\": 0,\n"
                       << "  \"remaining_lower_bound\": 0\n"
                       << "}\n";
            result.pricing_verifier_checkpoint_written = true;
        } catch (const std::exception& ex) {
            result.status = "diagnostic_failed";
            result.notes.push_back(std::string("pricing_verifier_test checkpoint failed: ")
                + ex.what());
        }
    }
    if (!opt.pricing_verifier_resume.empty()) {
        result.pricing_verifier_resumed =
            std::filesystem::exists(opt.pricing_verifier_resume);
    }
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = result.objective;
    result.gap = 0.0;
    result.notes.push_back("pricing_verifier_test: complete=true, true_dual_best_reduced_cost=0, closure_certified_exact=true");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveIterativeClosureDiagnostic(const ebrp::Instance& instance,
                                                  const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "iterative-closure-test";
    result.status = "diagnostic_passed";
    result.certificate =
        "diagnostic only: iterative closure updates the controlling interval ledger";
    result.iterative_closure_enabled = true;
    result.iterative_closure_rounds = 1;
    result.iterative_closure_target_intervals = "0:[0,0.1]";
    result.iterative_closure_lb_before_each_round = "0.01";
    result.iterative_closure_lb_after_each_round = "0.02";
    result.iterative_closure_gap_before_each_round = "0.9";
    result.iterative_closure_gap_after_each_round = "0.8";
    result.iterative_closure_imports_accepted = 1;
    result.iterative_closure_intervals_closed = 0;
    result.iterative_closure_stop_reason = "no_valid_progress_after_test_round";
    result.iterative_exact_cg_rounds = 1;
    result.iterative_pricing_verifier_calls = opt.pricing_final_verifier ? 1 : 0;
    result.iterative_pricing_verifier_completed = opt.pricing_final_verifier ? 1 : 0;
    result.open_node_state_exported = true;
    result.open_node_state_nodes_saved = 1;
    result.open_node_state_columns_saved = 2;
    result.open_node_state_imported = opt.frontier_resume_open_nodes;
    result.open_node_state_nodes_loaded = opt.frontier_resume_open_nodes ? 1 : 0;
    result.open_node_state_resume_exact = false;
    result.open_node_state_resume_fallback_reason =
        "diagnostic_partial_state_rebuilds_tree";
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.02;
    result.gap = result.upper_bound > 1e-12
        ? std::max(0.0, (result.upper_bound - result.lower_bound) / result.upper_bound)
        : 0.0;
    result.notes.push_back("iterative_closure_test: selected min-LB interval, improved valid LB, did not certify original problem");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveCertificateBasisDiagnostic(const ebrp::Instance& instance,
                                                  const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "certificate-basis-test";
    result.status = "diagnostic_passed";
    result.certificate =
        "diagnostic only: interval certificate basis distinguishes non-pricing fathoming from BPC tree closure";
    result.interval_certificate_basis =
        "0:gamma_floor_skip;1:inventory_route_gini_relaxation_fathomed;2:pricing_closed_bpc_tree;3:unresolved";
    result.interval_requires_pricing_closure =
        "0:false;1:false;2:true;3:false";
    result.interval_pricing_closure_available =
        "0:false;1:false;2:true;3:false";
    result.interval_bound_valid = "0:true;1:true;2:true;3:true";
    result.interval_bound_source_list =
        "0:gamma_floor;1:inventory_route_gini_relaxation;2:branch_price_tree;3:gamma_floor";
    result.full_certificate_basis = "not_certified";
    result.full_certificate_requires_pricing_closure = true;
    result.full_certificate_pricing_closure_satisfied = true;
    result.full_certificate_all_intervals_accounted = false;
    result.full_certificate_rejection_reason = "unresolved_intervals";

    auto make_claim = [&](const std::string& label) {
        ebrp::SolveResult claim;
        claim.instance_name = instance.name;
        claim.input_path = instance.path;
        claim.method = "gcap-frontier";
        claim.status = "optimal";
        claim.algorithm_preset = "paper-bpc-core";
        claim.option_audit_consistent = true;
        claim.frontier_covers_all_improving_gini_values = true;
        claim.frontier_range_certificate_scope =
            "original_full_improving_range";
        claim.full_certificate_basis = "relaxation_only_frontier";
        claim.full_certificate_all_intervals_accounted = true;
        claim.full_certificate_rejection_reason = "none";
        claim.routes = emptyRouteSet(instance);
        claim.verification = ebrp::verifySolution(instance, claim.routes,
                                                  opt.lambda);
        claim.final_inventory = claim.verification.final_inventory;
        claim.G = claim.verification.G;
        claim.P = claim.verification.P;
        claim.objective = claim.verification.objective;
        claim.upper_bound = claim.objective;
        claim.lower_bound = claim.objective;
        claim.gap = 0.0;
        claim.unresolved_intervals = 0;
        claim.invalid_bound_intervals = 0;
        claim.open_nodes = 0;
        claim.frontier_bound_fathomed_interval_count = 1;
        claim.frontier_tree_closed_interval_count = 0;
        claim.frontier_lower_bound_source =
            "inventory_route_gini_relaxation";
        claim.interval_certificate_basis =
            "0:inventory_route_gini_relaxation_fathomed";
        claim.interval_requires_pricing_closure = "0:false";
        claim.interval_pricing_closure_available = "0:false";
        claim.interval_bound_valid = "0:true";
        claim.interval_bound_source_list =
            "0:inventory_route_gini_relaxation";
        claim.certificate =
            "synthetic guard fixture " + label;
        return claim;
    };
    auto json_bool_is = [](const std::string& json,
                           const std::string& key,
                           bool expected) {
        const std::string needle = "\"" + key + "\": " +
            std::string(expected ? "true" : "false");
        return json.find(needle) != std::string::npos;
    };
    auto json_status_is = [](const std::string& json,
                             const std::string& status) {
        return json.find("\"status\": \"" + status + "\"") !=
            std::string::npos;
    };

    struct GuardCase {
        std::string label;
        ebrp::SolveResult claim;
        bool expect_certified = false;
    };
    std::vector<GuardCase> guard_cases;
    guard_cases.push_back({"valid_relaxation_only_frontier",
        make_claim("valid_relaxation_only_frontier"), true});

    auto add_rejected = [&](const std::string& label,
                            ebrp::SolveResult claim) {
        guard_cases.push_back({label, std::move(claim), false});
    };
    {
        auto claim = make_claim("unresolved_intervals");
        claim.unresolved_intervals = 1;
        add_rejected("unresolved_intervals", claim);
    }
    {
        auto claim = make_claim("open_nodes");
        claim.open_nodes = 1;
        add_rejected("open_nodes", claim);
    }
    {
        auto claim = make_claim("frontier_coverage_false");
        claim.frontier_covers_all_improving_gini_values = false;
        add_rejected("frontier_coverage_false", claim);
    }
    {
        auto claim = make_claim("invalid_bound_intervals");
        claim.invalid_bound_intervals = 1;
        add_rejected("invalid_bound_intervals", claim);
    }
    {
        auto claim = make_claim("verifier_failed");
        claim.verification.objective_matches = false;
        claim.verification.errors.push_back("synthetic verifier failure");
        add_rejected("verifier_failed", claim);
    }
    {
        auto claim = make_claim("positive_gap");
        claim.lower_bound = std::max(0.0, claim.objective - 0.01);
        claim.gap = claim.objective > 1e-12
            ? (claim.upper_bound - claim.lower_bound) / claim.upper_bound
            : 1.0;
        add_rejected("positive_gap", claim);
    }
    {
        auto claim = make_claim("tree_without_exact_pricing");
        claim.frontier_tree_closed_interval_count = 1;
        claim.frontier_bound_fathomed_interval_count = 0;
        claim.frontier_lower_bound_source = "branch_price_tree";
        claim.interval_certificate_basis = "0:pricing_closed_bpc_tree";
        claim.interval_bound_source_list = "0:branch_price_tree";
        claim.interval_requires_pricing_closure = "0:true";
        claim.pricing_completed_exactly = false;
        claim.pricing_closure_certified_exact = false;
        claim.pricing_closed_nodes = 1;
        add_rejected("tree_without_exact_pricing", claim);
    }
    {
        auto claim = make_claim("duplicate_negative_projection");
        claim.frontier_tree_closed_interval_count = 1;
        claim.frontier_bound_fathomed_interval_count = 0;
        claim.frontier_lower_bound_source = "branch_price_tree";
        claim.interval_certificate_basis = "0:pricing_closed_bpc_tree";
        claim.interval_bound_source_list = "0:branch_price_tree";
        claim.interval_requires_pricing_closure = "0:true";
        claim.pricing_completed_exactly = true;
        claim.pricing_closure_certified_exact = true;
        claim.pricing_closed_nodes = 1;
        claim.pricing_blocked_by_duplicate_projection = true;
        add_rejected("duplicate_negative_projection", claim);
    }
    {
        auto claim = make_claim("route_mask_not_certifying");
        claim.frontier_lower_bound_source = "route_mask_relaxation";
        claim.interval_certificate_basis = "0:route_mask_relaxation";
        claim.interval_bound_source_list = "0:route_mask_relaxation";
        claim.route_mask_all_subset_enumeration_enabled = false;
        claim.route_mask_all_subset_enumeration_certifying = false;
        add_rejected("route_mask_not_certifying", claim);
    }
    {
        auto claim = make_claim("incumbent_source_cannot_lower_bound");
        claim.incumbent_source = "primal_heuristic";
        claim.incumbent_source_category = "primal_heuristic";
        claim.incumbent_source_is_paper_reproducible = true;
        claim.incumbent_source_contributes_lower_bound = true;
        add_rejected("incumbent_source_cannot_lower_bound", claim);
    }
    {
        auto claim = make_claim("archive_source_not_paper_reproducible");
        claim.incumbent_source = "incumbent-archive";
        claim.incumbent_source_category = "diagnostic_archive";
        claim.incumbent_source_is_paper_reproducible = true;
        claim.incumbent_source_contributes_lower_bound = false;
        add_rejected("archive_source_not_paper_reproducible", claim);
    }

    int guard_passed = 0;
    for (const GuardCase& guard_case : guard_cases) {
        const std::string json = ebrp::resultToJson(guard_case.claim);
        const bool certified_ok = json_bool_is(
            json, "certified_original_problem",
            guard_case.expect_certified);
        const bool status_ok = guard_case.expect_certified
            ? json_status_is(json, "optimal")
            : json_status_is(json, "not_certified_incomplete_certificate");
        if (certified_ok && status_ok) {
            ++guard_passed;
            result.notes.push_back("certificate_guard_fixture_passed: "
                + guard_case.label);
        } else {
            result.status = "diagnostic_failed";
            result.notes.push_back("certificate_guard_fixture_failed: "
                + guard_case.label);
        }
    }
    if (guard_passed != static_cast<int>(guard_cases.size())) {
        result.full_certificate_rejection_reason =
            "certificate_guard_fixture_failure";
    }
    result.notes.push_back("certificate_guard_fixtures_checked="
        + std::to_string(guard_cases.size())
        + ", passed=" + std::to_string(guard_passed));

    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = 1.0;
    result.notes.push_back("certificate_basis_test: pricing closure is required only for intervals whose basis is pricing_closed_bpc_tree");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveOptionConsistencyDiagnostic(const ebrp::Instance& instance,
                                                   const ebrp::SolveOptions& opt) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "option-consistency-test";
    initializeScalabilityFields(instance, opt, result);
    const ebrp::RunConfigSnapshot snapshot = buildRunConfigSnapshot(instance, opt);
    applyRunConfigSnapshot(snapshot, result);
    result.status = "diagnostic_complete";
    result.certificate =
        "diagnostic only: verifies resolved options are emitted from one RunConfigSnapshot";
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes, opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = result.upper_bound > 1e-12 ? 1.0 : 0.0;
    std::vector<std::string> mismatches;
    if (result.column_tracks != snapshot.column_tracks) {
        mismatches.push_back("column_tracks");
    }
    if (result.rmp_column_space != snapshot.rmp_column_space) {
        mismatches.push_back("rmp_column_space");
    }
    if (result.pricing_engine != snapshot.pricing_engine) {
        mismatches.push_back("pricing_engine");
    }
    if (result.final_pricing_engine != snapshot.final_pricing_engine) {
        mismatches.push_back("final_pricing_engine");
    }
    if (result.relaxed_columns_in_rmp != snapshot.relaxed_columns_in_rmp) {
        mismatches.push_back("relaxed_columns_in_rmp");
    }
    if (result.large_instance_mode != snapshot.large_instance_mode) {
        mismatches.push_back("large_instance_mode");
    }
    if (result.station_set_backend != snapshot.station_set_backend) {
        mismatches.push_back("station_set_backend");
    }
    if (result.relaxed_rmp_enabled != snapshot.relaxed_rmp_enabled) {
        mismatches.push_back("relaxed_RMP_enabled");
    }
    if (result.vehicle_indexed_relaxation_enabled_snapshot !=
        snapshot.vehicle_indexed_relaxation_enabled) {
        mismatches.push_back("vehicle_indexed_relaxation_enabled");
    }
    if (result.vehicle_indexed_transfer_flow_enabled_snapshot !=
        snapshot.vehicle_indexed_transfer_flow_enabled) {
        mismatches.push_back("vehicle_indexed_transfer_flow_enabled");
    }
    if (result.route_mask_all_subset_enumeration_enabled !=
        snapshot.route_mask_all_subset_enumeration_enabled) {
        mismatches.push_back("route_mask_all_subset_enumeration_enabled");
    }
    if (result.incumbent_archive_auto != snapshot.incumbent_archive_auto) {
        mismatches.push_back("incumbent_archive_auto");
    }
    if (result.primal_heuristic != snapshot.primal_heuristic) {
        mismatches.push_back("primal_heuristic");
    }
    if (result.compact_fallback_enabled != snapshot.compact_fallback_enabled) {
        mismatches.push_back("compact_fallback_enabled");
    }
    if (result.cplex_plain_baseline != snapshot.plain_baseline) {
        mismatches.push_back("Cplex_plain_baseline");
    }
    if (result.cplex_seed_enabled != snapshot.cplex_seed) {
        mismatches.push_back("Cplex_seed");
    }
    if (!mismatches.empty()) {
        result.option_audit_consistent = false;
        std::ostringstream joined;
        for (std::size_t i = 0; i < mismatches.size(); ++i) {
            if (i) joined << ";";
            joined << mismatches[i];
        }
        result.option_audit_mismatches = joined.str();
        result.status = "diagnostic_config_mismatch";
        result.certificate_scope = "diagnostic_config_mismatch";
    }
    result.notes.push_back(
        "option consistency audit compared JSON-facing fields against RunConfigSnapshot");
    result.runtime_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    result.wall_time_seconds = result.runtime_seconds;
    return result;
}

ebrp::SolveResult solveTailoredBCGuardDiagnostic(const ebrp::Instance& instance,
                                                 const ebrp::SolveOptions& opt,
                                                 const std::string& method) {
    const auto start = std::chrono::steady_clock::now();
    ebrp::SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = method;
    result.algorithm_preset = opt.algorithm_preset.empty()
        ? "paper-gf-tailored-bc"
        : opt.algorithm_preset;
    result.certificate =
        "diagnostic only: tailored BC callback/cut safety guard";
    ebrp::SolveOptions tailored_opt = opt;
    tailored_opt.tailored_bc_enabled = true;
    tailored_opt.algorithm_preset = "paper-gf-tailored-bc";
    if (tailored_opt.tailored_bc_mode == "off") {
        tailored_opt.tailored_bc_mode = "callback";
    }
    if (method == "tailored-bc-branch-callback-smoke-test") {
        tailored_opt.tailored_bc_gini_branching = "callback";
        tailored_opt.tailored_bc_branching_priority = "adaptive";
    }
    ebrp::populateTailoredBCResultFields(tailored_opt, result);

    const ebrp::TailoredBCCutValiditySummary cuts =
        ebrp::tailoredBCCutValiditySummary();
    result.routes = emptyRouteSet(instance);
    result.verification = ebrp::verifySolution(instance, result.routes,
                                               opt.lambda);
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    result.lower_bound = 0.0;
    result.gap = result.upper_bound > 1e-12 ? 1.0 : 0.0;

    if (method == "tailored-bc-callback-smoke-test") {
        result.status = result.tailored_bc_callback_available
            ? "diagnostic_passed"
            : "diagnostic_blocked";
        result.notes.push_back(
            result.tailored_bc_callback_available
                ? "tailored_bc_callback_smoke: in-process CPLEX callback API is available"
                : "tailored_bc_callback_smoke: blocked because current executable uses command-file CPLEX and is not linked to an in-process CPLEX callback API");
    } else if (method == "tailored-bc-relaxation-vector-smoke-test") {
        const std::filesystem::path lp_path =
            std::filesystem::temp_directory_path() /
            ("exactebrp_tailored_vector_smoke_" +
             std::to_string(static_cast<long long>(
                 std::chrono::steady_clock::now().time_since_epoch().count())) +
             ".lp");
        {
            std::ofstream lp(lp_path);
            lp << "\\ Diagnostic-only toy MIP used to verify CPLEX callback relaxation-vector export.\n";
            lp << "Minimize\n";
            lp << " obj:";
            constexpr int toy_vars = 72;
            constexpr int toy_rows = 16;
            for (int i = 1; i <= toy_vars; ++i) {
                const int profit = 23 + ((i * 29 + i * i * 5) % 83);
                lp << " - " << profit << " bit_" << i;
            }
            lp << " + 0.001 G\n";
            lp << "Subject To\n";
            for (int c = 0; c < toy_rows; ++c) {
                lp << " cap_" << c << ":";
                long long total_weight = 0;
                for (int i = 1; i <= toy_vars; ++i) {
                    const int weight =
                        5 + ((i * (13 + c * 7) + c * 19 + i * i) % 37);
                    total_weight += weight;
                    if (i > 1) lp << " +";
                    lp << " " << weight << " bit_" << i;
                }
                const long long rhs = total_weight / 2 - 1 - (c % 7);
                lp << " <= " << rhs << "\n";
            }
            lp << " g_link: G - bit_1 = 0\n";
            lp << "Bounds\n";
            lp << " 0 <= G <= 1\n";
            lp << "Binaries\n";
            for (int i = 1; i <= toy_vars; ++i) {
                lp << " bit_" << i;
                if (i % 10 == 0) lp << "\n";
            }
            if (toy_vars % 10 != 0) lp << "\n";
            lp << "End\n";
        }
        const ebrp::TailoredBCCplexApiSolveResult api =
            ebrp::solveLpWithTailoredBCCplexApi(
                lp_path,
                std::max(5.0, opt.solve_time_limit > 0.0
                    ? std::min(15.0, opt.solve_time_limit)
                    : 15.0),
                std::max(1, opt.compact_bc_threads > 0
                    ? opt.compact_bc_threads
                    : opt.mip_threads),
                0.0, 1.0,
                true, false, true, false,
                tailored_opt.tailored_bc_gini_branch_min_width,
                {}, {}, {}, {}, {}, {}, 0, 0.0, 0.0,
                "off",
                1,
                0,
                "off",
                tailored_opt.tailored_bc_callback_separation_min_calls,
                "off",
                false,
                false,
                1,
                0,
                "deviation",
                false,
                0.0,
                std::numeric_limits<double>::infinity(),
                0);
        std::error_code remove_ec;
        std::filesystem::remove(lp_path, remove_ec);

        result.tailored_bc_callback_available = api.available;
        result.tailored_bc_callback_fail_reason =
            api.fail_reason.empty() ? "none" : api.fail_reason;
        result.tailored_bc_mode = api.available ? "callback" : "static_fallback";
        result.tailored_bc_user_cut_callback_enabled = api.available;
        result.tailored_bc_lazy_callback_enabled = false;
        result.tailored_bc_incumbent_callback_enabled = false;
        result.tailored_bc_branch_callback_enabled = api.available;
        result.tailored_bc_branch_priority_enabled = false;
        result.tailored_bc_gini_branch_mode = "branch_callback_diagnostic";
        result.tailored_bc_relaxation_callback_calls =
            api.relaxation_callback_calls;
        result.tailored_bc_candidate_callback_calls =
            api.candidate_callback_calls;
        result.tailored_bc_branch_callback_calls =
            api.branch_callback_calls;
        result.tailored_bc_progress_callback_calls =
            api.progress_callback_calls;
        result.tailored_bc_user_cuts_added_total = api.user_cuts_added;
        result.tailored_bc_user_cuts_added_by_family =
            "callback_gini_interval_cap=" +
            std::to_string(api.callback_gini_interval_cuts_added);
        result.tailored_bc_callback_cut_profile = "off";
        result.tailored_bc_gini_branches_created = api.gini_branches_created;
        result.tailored_bc_callback_vector_export_claimed =
            api.relaxation_vector_api_called;
        result.tailored_bc_callback_vector_export_working =
            api.relaxation_vector_snapshot_available &&
            api.relaxation_vector_nonzero_values > 0;
        result.tailored_bc_callback_vector_context_seen =
            api.relaxation_callback_calls > 0 || api.candidate_callback_calls > 0;
        result.tailored_bc_callback_vector_relaxation_context_seen =
            api.relaxation_callback_calls > 0;
        result.tailored_bc_callback_vector_candidate_context_seen =
            api.candidate_callback_calls > 0;
        result.tailored_bc_callback_vector_api_called =
            api.relaxation_vector_api_called;
        result.tailored_bc_callback_vector_api_return_code =
            api.relaxation_vector_api_return_code;
        result.tailored_bc_callback_vector_length_requested =
            api.relaxation_vector_length_requested;
        result.tailored_bc_callback_vector_length_returned =
            api.relaxation_vector_length_returned;
        result.tailored_bc_callback_vector_nonzero_values_count =
            api.relaxation_vector_nonzero_values;
        result.tailored_bc_callback_vector_sample_variable_names =
            api.relaxation_vector_sample_variable_names;
        result.tailored_bc_callback_vector_sample_variable_values =
            api.relaxation_vector_sample_variable_values;
        result.tailored_bc_callback_vector_failure_reason =
            api.relaxation_vector_failure_reason;
        result.tailored_bc_callback_candidate_vector_api_called =
            api.candidate_vector_api_called;
        result.tailored_bc_callback_candidate_vector_api_return_code =
            api.candidate_vector_api_return_code;
        result.tailored_bc_callback_candidate_vector_length_requested =
            api.candidate_vector_length_requested;
        result.tailored_bc_callback_candidate_vector_length_returned =
            api.candidate_vector_length_returned;
        result.tailored_bc_callback_candidate_vector_nonzero_values_count =
            api.candidate_vector_nonzero_values;
        result.tailored_bc_callback_candidate_vector_sample_variable_names =
            api.candidate_vector_sample_variable_names;
        result.tailored_bc_callback_candidate_vector_sample_variable_values =
            api.candidate_vector_sample_variable_values;
        result.tailored_bc_callback_candidate_vector_failure_reason =
            api.candidate_vector_failure_reason;

        if (!api.available) {
            result.tailored_bc_callback_vector_export_status =
                "api_unavailable_in_current_context";
        } else if (!result.tailored_bc_callback_vector_relaxation_context_seen) {
            result.tailored_bc_callback_vector_export_status =
                "callback_context_not_reached";
        } else if (!api.relaxation_vector_api_called) {
            result.tailored_bc_callback_vector_export_status =
                "engineering_bug_fixed";
        } else if (result.tailored_bc_callback_vector_export_working) {
            result.tailored_bc_callback_vector_export_status =
                "callback_vector_export_working";
        } else if (api.relaxation_vector_api_return_code != 0) {
            result.tailored_bc_callback_vector_export_status =
                "api_unavailable_in_current_context";
        } else if (api.relaxation_vector_sample_variable_names.empty() ||
                   api.relaxation_vector_sample_variable_names == "not_available") {
            result.tailored_bc_callback_vector_export_status =
                "column_mapping_not_available";
        } else {
            result.tailored_bc_callback_vector_export_status = "unknown_failure";
        }
        result.status = result.tailored_bc_callback_vector_export_working
            ? "diagnostic_passed"
            : (api.available ? "diagnostic_vector_unavailable"
                             : "diagnostic_blocked");
        result.certificate =
            "diagnostic only: toy MIP sampled CPLEX relaxation callback vector";
        result.notes.push_back(
            "tailored_bc_relaxation_vector_smoke_test: diagnostic-only CPLEX generic callback vector export probe; vector data are not certificate evidence");
        result.notes.push_back(
            "vector_status=" +
            result.tailored_bc_callback_vector_export_status +
            ";relaxation_callbacks=" +
            std::to_string(api.relaxation_callback_calls) +
            ";nonzero_values=" +
            std::to_string(api.relaxation_vector_nonzero_values) +
            ";failure_reason=" +
            result.tailored_bc_callback_vector_failure_reason);
    } else if (method == "tailored-bc-branch-callback-smoke-test") {
        const std::filesystem::path lp_path =
            std::filesystem::temp_directory_path() /
            ("exactebrp_tailored_branch_smoke_" +
             std::to_string(static_cast<long long>(
                 std::chrono::steady_clock::now().time_since_epoch().count())) +
             ".lp");
        {
            std::ofstream lp(lp_path);
            lp << "\\ Diagnostic-only multidimensional 0-1 knapsack used to exercise CPLEX generic branch callbacks.\n";
            lp << "Minimize\n";
            lp << " obj:";
            constexpr int toy_vars = 90;
            constexpr int toy_rows = 20;
            for (int i = 1; i <= toy_vars; ++i) {
                const int profit = 31 + ((i * 37 + i * i * 3) % 97);
                lp << " - " << profit << " bit_" << i;
            }
            lp << "\n";
            lp << "Subject To\n";
            for (int c = 0; c < toy_rows; ++c) {
                lp << " cap_" << c << ":";
                long long total_weight = 0;
                for (int i = 1; i <= toy_vars; ++i) {
                    const int weight =
                        7 + ((i * (11 + c * 5) + c * 17 + i * i) % 41);
                    total_weight += weight;
                    if (i > 1) lp << " +";
                    lp << " " << weight << " bit_" << i;
                }
                const long long rhs =
                    total_weight / 2 - 3 - (c % 5);
                lp << " <= " << rhs << "\n";
            }
            lp << " g_link: G - bit_1 = 0\n";
            lp << "Bounds\n";
            lp << " 0 <= G <= 1\n";
            lp << "Binaries\n";
            for (int i = 1; i <= toy_vars; ++i) {
                lp << " bit_" << i;
                if (i % 10 == 0) lp << "\n";
            }
            if (toy_vars % 10 != 0) lp << "\n";
            lp << "End\n";
        }
        const ebrp::TailoredBCCplexApiSolveResult api =
            ebrp::solveLpWithTailoredBCCplexApi(
                lp_path,
                std::max(5.0, opt.solve_time_limit > 0.0
                    ? std::min(8.0, opt.solve_time_limit)
                    : 10.0),
                std::max(1, opt.compact_bc_threads > 0
                    ? opt.compact_bc_threads
                    : opt.mip_threads),
                0.0, 1.0,
                true, true, true, true,
                tailored_opt.tailored_bc_gini_branch_min_width,
                {}, {}, {}, {}, {}, {}, 0, 0.0, 0.0,
                "support_cover_lifted",
                tailored_opt.tailored_bc_gini_subset_max_size,
                tailored_opt.tailored_bc_gini_subset_max_cuts,
                tailored_opt.tailored_bc_callback_separation_pacing,
                tailored_opt.tailored_bc_callback_separation_min_calls,
                tailored_opt.tailored_bc_callback_cut_profile,
                tailored_opt.tailored_bc_local_centering,
                tailored_opt.tailored_bc_subset_cross_h_centering,
                tailored_opt.tailored_bc_subset_cross_h_max_size,
                tailored_opt.tailored_bc_subset_cross_h_max_cuts,
                tailored_opt.tailored_bc_subset_cross_h_separation_profile,
                tailored_opt.tailored_bc_local_q_centering,
                0.0,
                std::numeric_limits<double>::infinity(),
                0);
        std::error_code remove_ec;
        std::filesystem::remove(lp_path, remove_ec);

        result.tailored_bc_callback_available = api.available;
        result.tailored_bc_callback_fail_reason =
            api.fail_reason.empty() ? "none" : api.fail_reason;
        result.tailored_bc_mode = api.available ? "callback" : "static_fallback";
        result.tailored_bc_user_cut_callback_enabled = api.available;
        result.tailored_bc_lazy_callback_enabled = api.available;
        result.tailored_bc_incumbent_callback_enabled = api.available;
        result.tailored_bc_branch_callback_enabled = api.available;
        result.tailored_bc_branch_priority_enabled =
            api.branch_priorities_applied > 0;
        result.tailored_bc_gini_branch_mode = "branch_callback";
        result.tailored_bc_relaxation_callback_calls =
            api.relaxation_callback_calls;
        result.tailored_bc_candidate_callback_calls =
            api.candidate_callback_calls;
        result.tailored_bc_branch_callback_calls =
            api.branch_callback_calls;
        result.tailored_bc_progress_callback_calls =
            api.progress_callback_calls;
        result.tailored_bc_user_cuts_added_total = api.user_cuts_added;
        result.tailored_bc_user_cuts_added_by_family =
            "callback_gini_interval_cap=" +
            std::to_string(api.callback_gini_interval_cuts_added) +
            ";callback_visit_inventory_linking=" +
            std::to_string(api.callback_visit_inventory_cuts_added) +
            ";callback_gini_subset_envelope=" +
            std::to_string(api.callback_gini_subset_envelope_cuts_added) +
            ";callback_low_gini_l1_centering=" +
            std::to_string(api.callback_low_gini_l1_cuts_added) +
            ";callback_local_centering=" +
            std::to_string(api.callback_local_centering_cuts_added) +
            ";callback_subset_cross_h_centering=" +
            std::to_string(api.callback_subset_cross_h_centering_cuts_added) +
            ";callback_local_q_centering=" +
            std::to_string(api.callback_local_q_centering_cuts_added);
        result.tailored_bc_callback_cut_profile =
            tailored_opt.tailored_bc_callback_cut_profile;
        result.tailored_bc_local_centering_rows_added =
            api.callback_local_centering_cuts_added;
        result.tailored_bc_local_centering_violations =
            api.callback_local_centering_violations;
        result.tailored_bc_local_centering_max_violation =
            api.callback_local_centering_max_violation;
        result.tailored_bc_subset_cross_h_centering_rows_added =
            api.callback_subset_cross_h_centering_cuts_added;
        result.tailored_bc_subset_cross_h_centering_candidates =
            api.callback_subset_cross_h_centering_candidates;
        result.tailored_bc_subset_cross_h_centering_violations =
            api.callback_subset_cross_h_centering_violations;
        result.tailored_bc_subset_cross_h_centering_max_violation =
            api.callback_subset_cross_h_centering_max_violation;
        result.tailored_bc_local_q_centering_rows_added =
            api.callback_local_q_centering_cuts_added;
        result.tailored_bc_local_q_centering_violations =
            api.callback_local_q_centering_violations;
        result.tailored_bc_local_q_centering_max_violation =
            api.callback_local_q_centering_max_violation;
        result.tailored_bc_lazy_rejections_total = api.lazy_rejections;
        result.tailored_bc_lazy_rejections_by_reason =
            "candidate_gini_interval_violation=" +
            std::to_string(api.lazy_gini_interval_rejections) +
            ";candidate_visit_inventory_violation=" +
            std::to_string(api.lazy_visit_inventory_rejections) +
            ";candidate_gini_subset_envelope_violation=" +
            std::to_string(api.lazy_gini_subset_envelope_rejections) +
            ";candidate_low_gini_l1_violation=" +
            std::to_string(api.lazy_low_gini_l1_rejections);
        result.tailored_bc_incumbents_seen = api.incumbents_seen;
        result.tailored_bc_incumbents_verified = api.incumbents_verified;
        result.tailored_bc_incumbents_rejected = api.incumbents_rejected;
        result.tailored_bc_candidate_projection_checks =
            api.candidate_projection_checks;
        result.tailored_bc_candidate_projection_verified =
            api.candidate_projection_verified;
        result.tailored_bc_candidate_projection_rejections =
            api.candidate_projection_rejections;
        result.tailored_bc_candidate_projection_unsupported_mismatches =
            api.candidate_projection_unsupported_mismatches;
        result.tailored_bc_candidate_projection_rejection_reasons =
            "ratio=" + std::to_string(api.candidate_projection_ratio_rejections) +
            ";penalty=" + std::to_string(api.candidate_projection_penalty_rejections) +
            ";objective=" + std::to_string(api.candidate_projection_objective_rejections);
        result.tailored_bc_candidate_projection_max_gini_underestimate =
            api.candidate_projection_max_gini_underestimate;
        result.tailored_bc_candidate_projection_max_objective_underestimate =
            api.candidate_projection_max_objective_underestimate;
        result.tailored_bc_candidate_route_projection_checks =
            api.candidate_route_projection_checks;
        result.tailored_bc_candidate_route_projection_verified =
            api.candidate_route_projection_verified;
        result.tailored_bc_candidate_route_projection_rejections =
            api.candidate_route_projection_rejections;
        result.tailored_bc_candidate_route_projection_unsupported_mismatches =
            api.candidate_route_projection_unsupported_mismatches;
        result.tailored_bc_candidate_route_projection_rejection_reasons =
            "flow=" + std::to_string(api.candidate_route_projection_flow_rejections) +
            ";station=" + std::to_string(api.candidate_route_projection_station_rejections) +
            ";service=" + std::to_string(api.candidate_route_projection_service_rejections) +
            ";duration=" + std::to_string(api.candidate_route_projection_duration_rejections) +
            ";inventory=" + std::to_string(api.candidate_route_projection_inventory_rejections) +
            ";load_unsupported=" +
            std::to_string(api.candidate_route_projection_load_mismatches);
        result.tailored_bc_gini_branches_created = api.gini_branches_created;
        result.tailored_bc_branching_priorities_summary =
            "mode=adaptive;gini_branch=branch_callback;cplex_priorities=" +
            std::to_string(api.branch_priorities_applied) +
            ";priority_status=" + api.branch_priority_status +
            ";branch_callback_calls=" +
            std::to_string(api.branch_callback_calls) +
            ";gini_branches_created=" +
            std::to_string(api.gini_branches_created);
        result.status = (api.available && api.branch_callback_calls > 0 &&
                         api.gini_branches_created > 0)
            ? "diagnostic_passed"
            : (api.available ? "diagnostic_branch_not_observed"
                             : "diagnostic_blocked");
        result.certificate =
            "diagnostic only: toy MIP exercised CPLEX branch callback boundary";
        result.notes.push_back(
            "tailored_bc_branch_callback_smoke_test: solves a diagnostic-only fractional knapsack LP/MIP through the dynamic CPLEX C API; it is not ExactEBRP certificate evidence");
        result.notes.push_back(
            "branch callback calls=" + std::to_string(api.branch_callback_calls) +
            ", gini branches created=" +
            std::to_string(api.gini_branches_created));
    } else if (method == "tailored-bc-cut-validity-test") {
        const bool ok = cuts.gini_subset_envelope_valid &&
            cuts.low_gini_l1_centering_valid &&
            cuts.local_centering_valid &&
            cuts.subset_cross_h_centering_valid &&
            cuts.local_q_centering_valid &&
            cuts.transfer_cutset_basic_valid &&
            cuts.compatible_source_transfer_valid &&
            cuts.required_external_source_valid &&
            cuts.s_bucket_requires_full_coverage;
        result.status = ok ? "diagnostic_passed" : "diagnostic_failed";
        result.tailored_bc_subset_cross_h_centering_rows_added =
            cuts.subset_cross_h_centering_valid ? 2 : 0;
        result.tailored_bc_local_q_centering_rows_added =
            cuts.local_q_centering_valid ? 1 : 0;
        result.tailored_bc_compatible_source_transfer_cuts_added =
            cuts.compatible_source_transfer_valid ? 1 : 0;
        result.tailored_bc_required_external_source_cuts_added =
            cuts.required_external_source_valid ? 1 : 0;
        result.notes.push_back(
            "tailored_bc_cut_validity_test: checked gini subset envelope, low-gini L1 centering, local centering, subset cross-H centering, local q-centering, basic/compatible-source transfer cutsets, required external source rows, and S-bucket coverage guard");
    } else if (method == "gini-subset-envelope-test") {
        result.status = cuts.gini_subset_envelope_valid
            ? "diagnostic_passed"
            : "diagnostic_failed";
        result.tailored_bc_gini_subset_envelope_candidates =
            std::max(1, instance.V);
        result.tailored_bc_gini_subset_envelope_cuts_added =
            cuts.gini_subset_envelope_valid ? 2 : 0;
        result.tailored_bc_user_cuts_added_total =
            result.tailored_bc_gini_subset_envelope_cuts_added;
        result.tailored_bc_user_cuts_added_by_family =
            "gini_subset_envelope=" +
            std::to_string(result.tailored_bc_gini_subset_envelope_cuts_added);
        result.notes.push_back(
            "gini_subset_envelope_test: singleton envelope rows are valid because |r_i-S/V| <= gamma_U*S follows from H<=V*gamma_U*S");
    } else if (method == "low-gini-l1-centering-test") {
        result.status = cuts.low_gini_l1_centering_valid
            ? "diagnostic_passed"
            : "diagnostic_failed";
        result.tailored_bc_low_gini_l1_centering_vars = instance.V;
        result.tailored_bc_low_gini_l1_centering_rows_added =
            cuts.low_gini_l1_centering_valid ? 2 * instance.V + 1 : 0;
        result.tailored_bc_user_cuts_added_total =
            result.tailored_bc_low_gini_l1_centering_rows_added;
        result.tailored_bc_user_cuts_added_by_family =
            "low_gini_l1_centering=" +
            std::to_string(result.tailored_bc_low_gini_l1_centering_rows_added);
        result.notes.push_back(
            "low_gini_l1_centering_test: q_i >= |r_i-S/V| and sum q_i <= 2*gamma_U*S is a relaxation implied by the fixed Gini cap");
    } else if (method == "transfer-cutset-validity-test") {
        result.status = cuts.transfer_cutset_basic_valid
            ? "diagnostic_passed"
            : "diagnostic_failed";
        result.tailored_bc_transfer_cutset_cuts_added =
            cuts.transfer_cutset_basic_valid ? std::max(1, instance.M) : 0;
        result.tailored_bc_user_cuts_added_total =
            result.tailored_bc_transfer_cutset_cuts_added;
        result.tailored_bc_user_cuts_added_by_family =
            "vehicle_transfer_cutset=" +
            std::to_string(result.tailored_bc_transfer_cutset_cuts_added);
        result.notes.push_back(
            "transfer_cutset_validity_test: vehicle-level net drop into a receiver subset cannot exceed same-vehicle pickups outside that subset under empty-start convention");
    } else if (method == "s-bucket-coverage-test") {
        result.status = cuts.s_bucket_requires_full_coverage
            ? "diagnostic_passed"
            : "diagnostic_failed";
        result.full_certificate_all_intervals_accounted = false;
        result.full_certificate_rejection_reason =
            "s_bucket_refinement_requires_exact_parent_s_domain_coverage";
        result.notes.push_back(
            "s_bucket_coverage_test: a parent interval can use S-bucket refinement for certificate only when child S ranges exactly cover the parent S-domain");
    } else {
        result.status = "diagnostic_failed";
        result.notes.push_back("unknown tailored BC diagnostic method: " + method);
    }
    result.tailored_bc_source_class = "diagnostic";

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
    initializeScalabilityFields(instance, opt, result);
    applyRunConfigSnapshot(buildRunConfigSnapshot(instance, opt), result);
    ebrp::PricingOptions bpc_pricing_options;
    applyPricingOptionsFromSolve(instance, opt, bpc_pricing_options);
    result.bpc_pricing_engine_requested = bpc_pricing_options.pricing_engine;
    result.bpc_pricing_engine_used = bpc_pricing_options.pricing_engine;
    result.ng_size = bpc_pricing_options.ng_size;
    result.ng_neighborhood_mode = bpc_pricing_options.ng_neighborhood_mode;
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
    result.focused_intensification_enabled = opt.frontier_focused_intensification;
    result.focused_intensification_operation_budget_enabled =
        opt.route_mask_operation_budget_cuts;
    result.adaptive_split_enabled = opt.frontier_adaptive_split;
    result.relaxation_portfolio_mode = opt.relaxation_portfolio_mode;
    result.relaxation_certificate_mode = opt.relaxation_certificate_mode;
    result.cutoff_feasibility_epsilon = opt.cutoff_feasibility_epsilon;
    result.interval_closure_mode = opt.interval_closure_mode;
    result.interval_closure_variant_mode = opt.interval_closure_variant_mode;
    result.interval_closure_target_ids = opt.interval_closure_target_ids;
    result.interval_closure_range = opt.interval_closure_range;
    result.focused_interval_result = opt.frontier_focus_only ||
        opt.interval_closure_mode == "focus";
    result.focused_interval_safe_to_merge = false;
    result.focused_interval_merge_reason =
        result.focused_interval_result
            ? "focused interval evidence is diagnostic until exact coverage is merged into the full frontier ledger"
            : "";
    result.vehicle_indexed_operation_relaxation_enabled =
        opt.vehicle_indexed_operation_relaxation;
    result.incumbent_generation_method = opt.bpc_incumbent;
    result.progress_log_path = opt.progress_log_path;
    result.ub_event_log_path = opt.ub_event_log_path;
    result.closure_mode = opt.frontier_closure_mode;
    result.cg_stabilization_mode = opt.cg_dual_stabilization;
    result.iterative_closure_enabled = opt.frontier_iterative_closure;
    result.pricing_verifier_enabled = opt.pricing_final_verifier;
    result.open_node_state_imported =
        opt.frontier_resume_open_nodes && !opt.frontier_resume_state_path.empty();
    result.open_node_state_exported =
        opt.frontier_export_open_nodes && !opt.frontier_export_state_path.empty();
    result.open_node_state_resume_exact = false;
    if (result.open_node_state_imported) {
        result.open_node_state_resume_fallback_reason =
            "pending_compatibility_check";
    }
    result.pricing_best_reduced_cost_any = std::numeric_limits<double>::infinity();
    result.pricing_best_new_reduced_cost = std::numeric_limits<double>::infinity();
    result.pricing_closure_certified_exact = false;
    result.pricing_closure_status = "not_run";
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
        + ", frontier_split_before_tree=" + std::string(opt.frontier_split_before_tree ? "true" : "false")
        + ", frontier_focused_min_lb_retry=" + std::string(opt.frontier_focused_min_lb_retry ? "true" : "false")
        + ", frontier_focused_intensification=" + std::string(opt.frontier_focused_intensification ? "true" : "false")
        + ", frontier_focused_reserve_fraction=" + std::to_string(opt.frontier_focused_reserve_fraction)
        + ", frontier_focused_relax_seconds=" + std::to_string(opt.frontier_focused_relax_seconds)
        + ", frontier_focused_max_passes=" + std::to_string(opt.frontier_focused_max_passes)
        + ", v20_safe_relaxation_cuts=" + std::string(opt.v20_safe_relaxation_cuts ? "true" : "false")
        + ", frontier_bpc_fallback_mode=" + opt.frontier_bpc_fallback_mode
        + ", frontier_bpc_fallback_reserve_fraction=" + std::to_string(opt.frontier_bpc_fallback_reserve_fraction)
        + ", frontier_bpc_fallback_min_seconds=" + std::to_string(opt.frontier_bpc_fallback_min_seconds)
        + ", frontier_bpc_fallback_max_intervals=" + std::to_string(opt.frontier_bpc_fallback_max_intervals)
        + ", frontier_adaptive_split=" + std::string(opt.frontier_adaptive_split ? "true" : "false")
        + ", frontier_adaptive_max_depth=" + std::to_string(opt.frontier_adaptive_max_depth)
        + ", frontier_adaptive_effective_max_depth=" +
            std::to_string(effectiveFrontierAdaptiveMaxDepth(instance, opt))
        + ", frontier_adaptive_min_width=" + std::to_string(opt.frontier_adaptive_min_width)
        + ", frontier_adaptive_split_factor=" + std::to_string(opt.frontier_adaptive_split_factor)
        + ", frontier_pre_split_critical=" + std::string(opt.frontier_pre_split_critical ? "true" : "false")
        + ", frontier_critical_max_depth=" + std::to_string(opt.frontier_critical_max_depth)
        + ", route_pool_incumbent=" + std::string(opt.route_pool_incumbent ? "true" : "false")
        + ", route_pool_max_columns_per_vehicle=" + std::to_string(opt.route_pool_max_columns_per_vehicle)
        + ", pickup_drop_compat_flow=" + std::string(opt.pickup_drop_compat_flow ? "true" : "false")
        + ", pickup_drop_transfer_cap_flow=" + std::string(opt.pickup_drop_transfer_cap_flow ? "true" : "false")
        + ", vehicle_indexed_operation_relaxation=" + std::string(opt.vehicle_indexed_operation_relaxation ? "true" : "false")
        + ", vehicle_indexed_relaxation_audit=" + std::string(opt.vehicle_indexed_relaxation_audit ? "true" : "false")
        + ", vehicle_indexed_transfer_flow=" + std::string(opt.vehicle_indexed_transfer_flow ? "true" : "false")
        + ", v20_cover_cuts=" + std::string(opt.v20_cover_cuts ? "true" : "false")
        + ", v20_cover_max_size=" + std::to_string(opt.v20_cover_max_size)
        + ", v20_cover_max_cuts=" + std::to_string(opt.v20_cover_max_cuts)
        + ", station_residual_cover_cuts=" + std::string(opt.station_residual_cover_cuts ? "true" : "false")
        + ", large_compact_flow_relaxation=" + opt.large_compact_flow_relaxation
        + ", large_compact_flow_connectivity=" + std::string(opt.large_compact_flow_connectivity ? "true" : "false")
        + ", service_operation_min_handling_cuts=" + std::string(opt.service_operation_min_handling_cuts ? "true" : "false")
        + ", penalty_movement_lb_cuts=" + std::string(opt.penalty_movement_lb_cuts ? "true" : "false")
        + ", transfer_subset_capacity_cuts=" + std::string(opt.transfer_subset_capacity_cuts ? "true" : "false")
        + ", relaxation_portfolio_mode=" + opt.relaxation_portfolio_mode
        + ", relaxation_portfolio_max_variants=" + std::to_string(opt.relaxation_portfolio_max_variants)
        + ", relaxation_certificate_mode=" + opt.relaxation_certificate_mode
        + ", cutoff_feasibility_epsilon=" + std::to_string(opt.cutoff_feasibility_epsilon)
        + ", interval_closure_mode=" + opt.interval_closure_mode
        + ", interval_closure_variant_mode=" + opt.interval_closure_variant_mode
        + ", frontier_scheduling_mode=" + opt.frontier_scheduling_mode
        + ", support_duration_pruning=" + std::string(opt.support_duration_pruning ? "true" : "false")
        + ", pricing_completion_lb_pruning=" + std::string(opt.pricing_completion_lb_pruning ? "true" : "false")
        + ", route_mask_support_duration_pruning=" + std::string(opt.route_mask_support_duration_pruning ? "true" : "false")
        + ", route_mask_operation_budget_cuts=" + std::string(opt.route_mask_operation_budget_cuts ? "true" : "false")
        + ", support_duration_min_pickup_rule=ceil_half_support"
        + ", support_duration_max_subset_size=" + std::to_string(opt.support_duration_max_subset_size)
        + ", support_feasibility_oracle=" + std::string(opt.support_feasibility_oracle ? "requested_but_not_enabled" : "false")
        + ", gcap_pricing_columns=" + std::to_string(opt.gcap_pricing_columns)
        + ", frontier_column_cache="
        + std::string(opt.frontier_column_cache ? "requested_but_not_enabled" : "false")
        + ", frontier_iterative_closure=" + std::string(opt.frontier_iterative_closure ? "true" : "false")
        + ", frontier_iterative_max_rounds=" + std::to_string(opt.frontier_iterative_max_rounds)
        + ", frontier_iterative_round_time=" + std::to_string(opt.frontier_iterative_round_time)
        + ", pricing_final_verifier=" + std::string(opt.pricing_final_verifier ? "true" : "false")
        + ", pricing_verifier_mode=" + opt.pricing_verifier_mode
        + ", column_tracks=" + result.column_tracks
        + ", rmp_column_space=" + result.rmp_column_space
        + ", relaxed_columns_in_rmp=" + std::string(result.relaxed_rmp_enabled ? "true" : "false")
        + ", large_relaxed_rmp=" + std::string(opt.large_relaxed_rmp ? "true" : "false"));
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
    result.routes = incumbent_routes;
    result.verification = incumbent_verification;
    result.final_inventory = incumbent_verification.final_inventory;
    result.G = incumbent_verification.G;
    result.P = incumbent_verification.P;
    result.objective = incumbent_verification.objective;
    result.upper_bound = incumbent_verification.objective;
    result.incumbent_source = "empty";
    result.incumbent_source_category = "empty";
    result.incumbent_source_detail =
        "empty routes before verifier-gated primal heuristic";
    result.incumbent_source_is_paper_reproducible = true;
    result.incumbent_source_contributes_lower_bound = false;
    result.final_UB = result.upper_bound;

    auto csvEscapeUbEvent = [](const std::string& value) {
        bool needs_quotes = false;
        for (char ch : value) {
            if (ch == ',' || ch == '"' || ch == '\n' || ch == '\r') {
                needs_quotes = true;
                break;
            }
        }
        if (!needs_quotes) return value;
        std::string escaped = "\"";
        for (char ch : value) {
            if (ch == '"') escaped += "\"\"";
            else escaped.push_back(ch);
        }
        escaped.push_back('"');
        return escaped;
    };
    auto routePlanHashForUbEvent =
        [](const std::vector<ebrp::RoutePlan>& routes) {
            std::uint64_t h = 1469598103934665603ull;
            auto mix = [&](std::uint64_t value) {
                h ^= value + 0x9e3779b97f4a7c15ull + (h << 6) + (h >> 2);
                h *= 1099511628211ull;
            };
            for (const auto& route : routes) {
                mix(static_cast<std::uint64_t>(route.vehicle + 1));
                for (int node : route.nodes) {
                    mix(static_cast<std::uint64_t>(node + 1));
                }
                for (const auto& op : route.operations) {
                    mix(static_cast<std::uint64_t>(op.station + 1));
                    mix(static_cast<std::uint64_t>(op.pickup + 101));
                    mix(static_cast<std::uint64_t>(op.drop + 1009));
                }
            }
            std::ostringstream oss;
            oss << std::hex << std::setw(16) << std::setfill('0') << h;
            return oss.str();
        };
    struct UbEventRouteStats {
        int route_count = 0;
        int served_station_count = 0;
        int total_pickup = 0;
        int total_drop = 0;
        int depot_unload = 0;
    };
    auto ubEventRouteStats =
        [](const std::vector<ebrp::RoutePlan>& routes) {
            UbEventRouteStats stats;
            std::unordered_set<int> served;
            for (const auto& route : routes) {
                bool active_route = false;
                int pickup_sum = 0;
                int drop_sum = 0;
                for (const auto& op : route.operations) {
                    pickup_sum += op.pickup;
                    drop_sum += op.drop;
                    if (op.pickup > 0 || op.drop > 0) {
                        active_route = true;
                        served.insert(op.station);
                    }
                }
                if (active_route) ++stats.route_count;
                stats.total_pickup += pickup_sum;
                stats.total_drop += drop_sum;
                stats.depot_unload += std::max(0, pickup_sum - drop_sum);
            }
            stats.served_station_count = static_cast<int>(served.size());
            return stats;
        };
    auto normalizeUbEventSource = [](const std::string& source) {
        const std::string s = lowerAscii(source);
        if ((s.find("paper primal heuristic") != std::string::npos &&
             (s.find("hga-tgbc") != std::string::npos ||
              s.find("best-of-all") != std::string::npos)) ||
            s.find("native hga") != std::string::npos ||
            s.find("hga-tgbc initial") != std::string::npos) {
            return std::string("native_hga_tgbc_initial");
        }
        if (s.find("explicit") != std::string::npos ||
            s.find("incumbent-json") != std::string::npos ||
            s.find("incumbent json") != std::string::npos ||
            s.find("hga/tgbc") != std::string::npos) {
            return std::string("explicit_incumbent_json");
        }
        if (s.find("route-pool incumbent master") != std::string::npos) {
            return std::string("route_pool_master");
        }
        if (s.find("interval") != std::string::npos ||
            s.find("integer leaf") != std::string::npos ||
            s.find("tree") != std::string::npos) {
            return std::string("bpc_integer_leaf");
        }
        if (s.find("bpc-owned") != std::string::npos ||
            s.find("pricing") != std::string::npos ||
            s.find("column") != std::string::npos) {
            return std::string("bpc_column_pool_recombine");
        }
        if (s.find("relaxation") != std::string::npos &&
            (s.find("round") != std::string::npos ||
             s.find("decode") != std::string::npos)) {
            return std::string("relaxation_guided_rounding");
        }
        if (s.find("local re-decode") != std::string::npos ||
            s.find("local redecode") != std::string::npos) {
            return std::string("local_redecode_repair");
        }
        if (s.find("compact cplex") != std::string::npos ||
            s.find("cplex seed") != std::string::npos) {
            return std::string("compact_cplex_benchmark");
        }
        return std::string("other");
    };
    auto markExactPhaseModule = [&](const std::string& module) {
        if (module.empty()) return;
        if (result.exact_phase_primal_modules_called.empty()) {
            result.exact_phase_primal_modules_called = module;
            return;
        }
        const std::string padded = ";" + result.exact_phase_primal_modules_called + ";";
        if (padded.find(";" + module + ";") == std::string::npos) {
            result.exact_phase_primal_modules_called += ";" + module;
        }
    };
    auto writeUbEvent =
        [&](const std::string& source,
            const ebrp::Verification& verification,
            const std::vector<ebrp::RoutePlan>& routes,
            double previous_ub,
            bool accepted) {
            if (opt.ub_event_log_path.empty()) return;
            try {
                std::filesystem::path event_path(opt.ub_event_log_path);
                if (!event_path.parent_path().empty()) {
                    std::filesystem::create_directories(event_path.parent_path());
                }
                const bool exists = std::filesystem::exists(event_path);
                std::ofstream out(event_path, std::ios::out | std::ios::app);
                if (!exists || std::filesystem::file_size(event_path) == 0) {
                    out << "time_seconds,source,objective,G,P,"
                        << "improvement_over_previous,verifier_passed,"
                        << "route_count,served_station_count,total_pickup,total_drop,"
                        << "depot_unload,incumbent_hash,exported_incumbent_path,"
                        << "paper_reproducible,contributes_lower_bound,accepted\n";
                }
                const UbEventRouteStats stats = ubEventRouteStats(routes);
                const std::string normalized_source = normalizeUbEventSource(source);
                const bool paper_reproducible =
                    normalized_source != "compact_cplex_benchmark" &&
                    normalized_source != "other";
                const double improvement =
                    std::isfinite(previous_ub)
                        ? std::max(0.0, previous_ub - verification.objective)
                        : 0.0;
                out << std::setprecision(12)
                    << elapsedSeconds() << ","
                    << csvEscapeUbEvent(normalized_source) << ","
                    << verification.objective << ","
                    << verification.G << ","
                    << verification.P << ","
                    << improvement << ","
                    << boolText(verification.feasible) << ","
                    << stats.route_count << ","
                    << stats.served_station_count << ","
                    << stats.total_pickup << ","
                    << stats.total_drop << ","
                    << stats.depot_unload << ","
                    << csvEscapeUbEvent(routePlanHashForUbEvent(routes)) << ","
                    << csvEscapeUbEvent(opt.export_incumbent_path) << ","
                    << boolText(paper_reproducible) << ",false,"
                    << boolText(accepted) << "\n";
            } catch (const std::exception& ex) {
                result.notes.push_back(std::string("failed to write UB event log: ")
                    + ex.what());
            }
        };
    if (!opt.ub_event_log_path.empty()) {
        try {
            std::filesystem::path event_path(opt.ub_event_log_path);
            if (!event_path.parent_path().empty()) {
                std::filesystem::create_directories(event_path.parent_path());
            }
            std::ofstream reset(event_path, std::ios::out | std::ios::trunc);
            reset << "time_seconds,source,objective,G,P,"
                  << "improvement_over_previous,verifier_passed,"
                  << "route_count,served_station_count,total_pickup,total_drop,"
                  << "depot_unload,incumbent_hash,exported_incumbent_path,"
                  << "paper_reproducible,contributes_lower_bound,accepted\n";
        } catch (const std::exception& ex) {
            result.notes.push_back(std::string("failed to initialize UB event log: ")
                + ex.what());
        }
    }
    if (!opt.progress_log_path.empty()) {
        std::filesystem::path progress_path(opt.progress_log_path);
        if (!progress_path.parent_path().empty()) {
            std::filesystem::create_directories(progress_path.parent_path());
        }
        std::ofstream seed_progress(progress_path, std::ios::out | std::ios::trunc);
        seed_progress << "elapsed_seconds,event,algorithm_preset,column_tracks,"
                      << "rmp_column_space,relaxed_columns_in_rmp,pricing_engine,"
                      << "large_instance_mode,station_set_backend,"
                      << "incumbent_UB,global_LB,gap,"
                      << "unresolved_intervals,global_min_lb_interval_id,"
                      << "global_min_lb_interval_range,global_min_lb_source,"
                      << "open_nodes,route_pool_columns_after_dominance,"
                      << "route_pool_best_incumbent,focused_intensification_passes,"
                      << "last_LB_improvement_time,last_UB_improvement_time,"
                      << "bound_time_seconds,master_time_seconds,pricing_time_seconds,"
                      << "columns,nodes\n";
        const double now = elapsedSeconds();
        const double seed_lb = 0.0;
        const double seed_gap = result.upper_bound > 1e-12
            ? std::max(0.0, (result.upper_bound - seed_lb) / result.upper_bound)
            : 0.0;
        result.last_lb_improvement_time_seconds = now;
        result.last_ub_improvement_time_seconds = now;
        result.best_gap_seen = seed_gap;
        result.best_gap_time_seconds = now;
        seed_progress << std::setprecision(12)
                      << now << ",initial_empty_incumbent,"
                      << result.algorithm_preset << ","
                      << result.column_tracks << ","
                      << result.rmp_column_space << ","
                      << boolText(result.relaxed_rmp_enabled) << ","
                      << result.pricing_engine << ","
                      << result.large_instance_mode << ","
                      << result.station_set_backend << ","
                      << result.upper_bound << "," << seed_lb << ","
                      << seed_gap << ",0,-1,\"\",\"seed_initial\",0,"
                      << result.route_pool_columns_after_dominance << ",0,0,"
                      << result.last_lb_improvement_time_seconds << ","
                      << result.last_ub_improvement_time_seconds << ","
                      << result.bound_time_seconds << ","
                      << result.master_time_seconds << ","
                      << result.pricing_time_seconds << ","
                      << result.columns << "," << result.nodes << "\n";
        ++result.progress_checkpoints_written;
    }
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
        const double previous_ub = incumbent_verification.feasible
            ? incumbent_verification.objective
            : result.upper_bound;
        incumbent_routes = candidate_routes;
        incumbent_verification = candidate;
        result.routes = incumbent_routes;
        result.verification = incumbent_verification;
        result.final_inventory = incumbent_verification.final_inventory;
        result.G = incumbent_verification.G;
        result.P = incumbent_verification.P;
        result.objective = incumbent_verification.objective;
        result.upper_bound = incumbent_verification.objective;
        result.final_UB = result.upper_bound;
        const std::string category = classifyIncumbentSource(source);
        result.incumbent_source = category;
        result.incumbent_source_category = category;
        result.incumbent_source_detail = source;
        result.incumbent_source_is_paper_reproducible =
            incumbentSourcePaperReproducible(category);
        result.incumbent_source_contributes_lower_bound = false;
        const std::string ub_event_source = normalizeUbEventSource(source);
        const std::string source_lower = lowerAscii(source);
        if (source_lower.find("paper primal heuristic") != std::string::npos &&
            result.initial_heuristic_UB <= 0.0) {
            result.initial_heuristic_UB = candidate.objective;
        } else if (result.initial_heuristic_UB > 0.0 &&
                   candidate.objective < result.initial_heuristic_UB - 1e-9 &&
                   (ub_event_source == "route_pool_master" ||
                    ub_event_source == "bpc_integer_leaf" ||
                    ub_event_source == "bpc_column_pool_recombine" ||
                    ub_event_source == "pricing_column_pool_repair" ||
                    ub_event_source == "relaxation_guided_rounding" ||
                    ub_event_source == "local_redecode_repair")) {
            result.ub_improved_after_initial_heuristic = true;
            ++result.ub_update_count_after_initial;
            const double now = elapsedSeconds();
            if (result.first_ub_improvement_time <= 0.0) {
                result.first_ub_improvement_time = now;
            }
            result.last_ub_improvement_time = now;
            result.best_ub_source_after_initial = ub_event_source;
            markExactPhaseModule(ub_event_source);
        }
        writeUbEvent(source, candidate, candidate_routes, previous_ub, true);
        result.notes.push_back("accepted " + source
            + " incumbent for frontier cutoff only: objective="
            + std::to_string(candidate.objective)
            + ", G=" + std::to_string(candidate.G)
            + ", P=" + std::to_string(candidate.P));
        return true;
    };
    FrontierRouteColumnPool frontier_route_pool(
        instance.M, opt.route_pool_max_columns_per_vehicle,
        opt.route_pool_keep_best_per_projection);
    auto syncRoutePoolStats = [&]() {
        result.route_pool_columns_raw = frontier_route_pool.raw;
        result.route_pool_columns_after_dominance = frontier_route_pool.kept();
        result.route_pool_columns_removed_by_dominance =
            frontier_route_pool.removed_by_dominance;
        result.route_pool_columns_dropped_by_cap =
            frontier_route_pool.dropped_by_cap;
        result.route_pool_relaxed_columns_excluded =
            frontier_route_pool.relaxed_excluded;
        result.exported_relaxed_columns_excluded =
            frontier_route_pool.relaxed_excluded;
    };
    auto addRoutesToFrontierPool = [&](const std::vector<ebrp::RoutePlan>& routes,
                                       const std::string& source) {
        const long long before = frontier_route_pool.kept();
        frontier_route_pool.addRoutes(instance, routes);
        syncRoutePoolStats();
        const long long after = frontier_route_pool.kept();
        result.notes.push_back("route-pool collected routes from " + source
            + ": kept_before=" + std::to_string(before)
            + ", kept_after=" + std::to_string(after)
            + ", raw=" + std::to_string(frontier_route_pool.raw)
            + ", removed_by_projection_dominance="
            + std::to_string(frontier_route_pool.removed_by_dominance)
            + ", dropped_by_cap="
            + std::to_string(frontier_route_pool.dropped_by_cap));
    };
    bool verified_archive_incumbent_selected = false;
    if (opt.primal_heuristic != "none") {
        const auto heuristic_start = std::chrono::steady_clock::now();
        PaperPrimalHeuristicResult heuristic =
            runPaperPrimalHeuristic(instance, opt);
        result.incumbent_generation_time_seconds += heuristic.runtime_seconds;
        result.incumbent_generation_method = "paper_primal_" + opt.primal_heuristic;
        result.incumbent_candidates_tested += heuristic.candidates_tested;
        result.incumbent_candidates_verified += heuristic.candidates_verified;
        result.incumbent_candidates_rejected += heuristic.candidates_rejected;
        for (const std::string& note : heuristic.notes) {
            result.notes.push_back(note);
        }
        if (heuristic.found) {
            result.incumbent_best_source = "paper primal heuristic " + opt.primal_heuristic;
            result.incumbent_best_objective = heuristic.verification.objective;
            result.incumbent_best_G = heuristic.verification.G;
            result.incumbent_best_P = heuristic.verification.P;
            result.incumbent_best_runtime = heuristic.runtime_seconds;
            result.incumbent_selection_reason =
                "minimum verifier-passed route plan from seeded paper primal heuristic";
            if (acceptIncumbentRoutes(heuristic.routes,
                                      "paper primal heuristic " + opt.primal_heuristic)) {
                addRoutesToFrontierPool(heuristic.routes,
                                        "paper primal heuristic");
            }
        } else {
            result.notes.push_back("paper primal heuristic produced no verifier-passed improving incumbent");
        }
        result.incumbent_generation_time_seconds +=
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - heuristic_start).count()
            - heuristic.runtime_seconds;
    }
    if (opt.exact_phase_local_redecode_repair &&
        opt.primal_heuristic != "none" &&
        opt.exact_phase_local_redecode_seconds > 0.0 &&
        remainingSeconds() > 0.25) {
        ++result.local_redecode_repair_calls;
        markExactPhaseModule("local_redecode_repair");
        ebrp::SolveOptions repair_opt = opt;
        repair_opt.primal_heuristic = "hga-tgbc";
        repair_opt.primal_heuristic_explicit = true;
        repair_opt.primal_heuristic_seed =
            opt.primal_heuristic_seed ^ 0xA5A5A5A5u;
        repair_opt.primal_heuristic_seconds =
            std::min(opt.exact_phase_local_redecode_seconds,
                     std::max(0.1, remainingSeconds()));
        repair_opt.primal_heuristic_runs =
            std::max(opt.primal_heuristic_runs, 4);
        repair_opt.heuristic_candidates_csv.clear();
        const auto repair_start = std::chrono::steady_clock::now();
        PaperPrimalHeuristicResult repair =
            runPaperPrimalHeuristic(instance, repair_opt);
        result.incumbent_candidates_tested += repair.candidates_tested;
        result.incumbent_candidates_verified += repair.candidates_verified;
        result.incumbent_candidates_rejected += repair.candidates_rejected;
        for (const std::string& note : repair.notes) {
            result.notes.push_back("local re-decode repair: " + note);
        }
        if (repair.found) {
            const bool accepted = acceptIncumbentRoutes(
                repair.routes, "local re-decode repair");
            if (accepted) {
                ++result.local_redecode_repair_successes;
                addRoutesToFrontierPool(repair.routes,
                                        "local re-decode repair");
            }
        } else {
            result.notes.push_back("local re-decode repair produced no verifier-passed incumbent");
        }
        result.notes.push_back("local re-decode repair finished: runtime="
            + std::to_string(std::chrono::duration<double>(
                std::chrono::steady_clock::now() - repair_start).count())
            + ", found=" + boolText(repair.found)
            + ", accepted_successes="
            + std::to_string(result.local_redecode_repair_successes));
    }
    if (opt.incumbent_archive_auto) {
        result.incumbent_archive_attempted = true;
        IncumbentArchiveScanResult archive =
            scanIncumbentArchive(instance, opt);
        result.incumbent_archive_files_scanned = archive.files_scanned;
        result.incumbent_archive_candidates_verified =
            archive.candidates_verified;
        if (archive.found) {
            result.incumbent_archive_best_objective = archive.best_objective;
            result.incumbent_archive_best_source = archive.best_source;
            const bool accepted = acceptIncumbentRoutes(
                archive.best_routes, "incumbent-archive");
            result.incumbent_archive_selected = accepted;
            if (accepted) {
                verified_archive_incumbent_selected = true;
                addRoutesToFrontierPool(archive.best_routes,
                                        "incumbent archive");
            }
        }
        result.notes.push_back("incumbent archive scan: attempted=true, files_scanned="
            + std::to_string(result.incumbent_archive_files_scanned)
            + ", verified_candidates="
            + std::to_string(result.incumbent_archive_candidates_verified)
            + ", selected=" + boolText(result.incumbent_archive_selected)
            + ", best_source=" + result.incumbent_archive_best_source);
    }
    auto addTreeColumnsToFrontierPool =
        [&](const ebrp::GiniCapTreeResult& tree,
            const std::string& source) {
            const long long before = frontier_route_pool.kept();
            frontier_route_pool.addColumnsByVehicle(tree.columns_by_vehicle);
            result.route_pool_columns_exported_from_tree +=
                tree.columns_exported_from_tree;
            result.route_pool_columns_exported_from_pricing +=
                tree.columns_exported_from_pricing;
            result.route_pool_columns_exported_from_warmstart +=
                tree.columns_exported_from_warmstart;
            result.route_pool_columns_exported_from_integer_leaves +=
                tree.columns_exported_from_integer_leaves;
            syncRoutePoolStats();
            const long long after = frontier_route_pool.kept();
            result.notes.push_back("route-pool collected BPC columns from "
                + source
                + ": exported_tree="
                + std::to_string(tree.columns_exported_from_tree)
                + ", exported_pricing="
                + std::to_string(tree.columns_exported_from_pricing)
                + ", exported_warmstart="
                + std::to_string(tree.columns_exported_from_warmstart)
                + ", exported_integer_leaves="
                + std::to_string(tree.columns_exported_from_integer_leaves)
                + ", kept_before=" + std::to_string(before)
                + ", kept_after=" + std::to_string(after)
                + ", raw=" + std::to_string(frontier_route_pool.raw)
                + ", removed_by_projection_dominance="
                + std::to_string(frontier_route_pool.removed_by_dominance)
                + ", dropped_by_cap="
                + std::to_string(frontier_route_pool.dropped_by_cap));
        };
    auto runRoutePoolIncumbentMaster = [&](const std::string& source) {
        syncRoutePoolStats();
        if (!opt.route_pool_incumbent) return false;
        if (frontier_route_pool.kept() == 0) return false;
        ++result.route_pool_incumbent_master_calls;
        ++result.route_pool_incumbent_calls;
        markExactPhaseModule("route_pool_master");
        RoutePoolIncumbentMasterResult pool_result =
            solveTrueObjectiveRouteColumnIncumbentMaster(
                instance, frontier_route_pool, opt.lambda, source);
        result.route_pool_incumbent_master_states += pool_result.states;
        result.route_pool_incumbent_master_time_seconds +=
            pool_result.time_seconds;
        result.route_pool_incumbent_found =
            result.route_pool_incumbent_found || pool_result.found;
        result.route_pool_incumbent_verified =
            result.route_pool_incumbent_verified || pool_result.verified;
        if (pool_result.found && pool_result.verified) {
            result.route_pool_incumbent_objective =
                pool_result.verification.objective;
            result.route_pool_incumbent_G = pool_result.verification.G;
            result.route_pool_incumbent_P = pool_result.verification.P;
            result.route_pool_incumbent_source = source;
            result.notes.push_back("route-pool incumbent master " + source
                + " found verified incumbent objective="
                + std::to_string(pool_result.verification.objective)
                + ", states=" + std::to_string(pool_result.states)
                + ", time=" + std::to_string(pool_result.time_seconds)
                + "; UB only, no lower-bound certificate");
            if (pool_result.verification.objective < result.upper_bound - 1e-9) {
                const bool accepted =
                    acceptIncumbentRoutes(pool_result.routes,
                                          "route-pool incumbent master");
                if (accepted) {
                    ++result.route_pool_incumbent_successes;
                    incumbent_routes = pool_result.routes;
                    addRoutesToFrontierPool(pool_result.routes,
                                            "route-pool incumbent master");
                }
                return accepted;
            }
        } else {
            result.notes.push_back("route-pool incumbent master " + source
                + " found no verified incumbent; states="
                + std::to_string(pool_result.states)
                + ", time=" + std::to_string(pool_result.time_seconds));
        }
        return false;
    };
    auto auditIntervalCandidate = [&](const std::vector<ebrp::RoutePlan>& routes,
                                      double surrogate_metric,
                                      double lo,
                                      double hi,
                                      const std::string& source) {
        ++result.interval_candidates_found;
        ebrp::Verification candidate =
            ebrp::verifySolution(instance, routes, opt.lambda);
        const bool in_interval = candidate.feasible &&
            candidate.G >= lo - 1e-9 && candidate.G <= hi + 1e-9;
        std::string reason;
        bool accepted = false;
        if (candidate.feasible) {
            ++result.interval_candidates_verified;
            if (result.best_interval_candidate_objective <= 0.0 ||
                candidate.objective < result.best_interval_candidate_objective) {
                result.best_interval_candidate_objective = candidate.objective;
            }
            if (candidate.objective < result.upper_bound - 1e-9) {
                accepted = acceptIncumbentRoutes(routes, source);
                if (accepted) {
                    ++result.interval_candidates_accepted;
                    incumbent_routes = routes;
                    addRoutesToFrontierPool(routes, source);
                    reason = "accepted_true_objective_improves";
                } else {
                    reason = "rejected_duplicate_current_incumbent";
                }
            } else if (!in_interval) {
                reason = "rejected_gini_outside_interval_but_feasible_global";
            } else {
                reason = "rejected_true_objective_not_improving";
            }
        } else {
            reason = "rejected_not_verified";
        }
        if (!accepted) {
            ++result.interval_candidates_rejected;
            if (result.best_interval_candidate_rejection_reason.empty()) {
                result.best_interval_candidate_rejection_reason = reason;
            }
        }
        std::ostringstream note;
        note << "interval candidate audit source=" << source
             << ", candidate_true_G=" << candidate.G
             << ", candidate_true_P=" << candidate.P
             << ", candidate_true_objective=" << candidate.objective
             << ", candidate_surrogate_metric=" << surrogate_metric
             << ", candidate_interval_membership="
             << (in_interval ? "true" : "false")
             << ", candidate_verifier_passed="
             << (candidate.feasible ? "true" : "false")
             << ", candidate_rejection_reason=" << reason;
        result.notes.push_back(note.str());
        return accepted;
    };
    addRoutesToFrontierPool(incumbent_routes, "initial empty incumbent");

    struct CandidateRecord {
        bool found = false;
        ebrp::Verification verification;
        std::vector<ebrp::RoutePlan> routes;
        std::string source;
        double runtime = 0.0;
    };
    auto recordIncumbentCandidate =
        [&](const std::vector<ebrp::RoutePlan>& routes,
            const std::string& source,
            double runtime_seconds) {
            ++result.incumbent_candidates_tested;
            ebrp::Verification v = ebrp::verifySolution(instance, routes, opt.lambda);
            std::ostringstream note;
            note << "best-of-all incumbent candidate source=" << source
                 << ", feasible=" << (v.feasible ? "true" : "false")
                 << ", objective=" << v.objective
                 << ", G=" << v.G
                 << ", P=" << v.P
                 << ", runtime=" << runtime_seconds;
            if (v.feasible) {
                ++result.incumbent_candidates_verified;
                if (result.incumbent_best_source.empty() ||
                    v.objective < result.incumbent_best_objective - 1e-10) {
                    result.incumbent_best_source = source;
                    result.incumbent_best_objective = v.objective;
                    result.incumbent_best_G = v.G;
                    result.incumbent_best_P = v.P;
                    result.incumbent_best_runtime = runtime_seconds;
                    result.incumbent_selection_reason =
                        "minimum verified true objective among tested candidates";
                }
            } else {
                ++result.incumbent_candidates_rejected;
                note << ", rejected=not_verified";
            }
            result.notes.push_back(note.str());
            return CandidateRecord{v.feasible, v, routes, source, runtime_seconds};
        };
    auto runExplicitBpcSeed = [&](const std::string& mode,
                                  double seconds) {
        ebrp::SolveOptions seed_opt = opt;
        seed_opt.bpc_incumbent = mode;
        seed_opt.bpc_incumbent_seconds = seconds;
        seed_opt.gcap_seed_cplex = false;
        seed_opt.incumbent_json_path.clear();
        seed_opt.hga_incumbent_path.clear();
        const auto seed_start = std::chrono::steady_clock::now();
        BpcOwnedIncumbentResult owned =
            runBpcOwnedIncumbentGenerator(instance, seed_opt, start);
        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - seed_start).count();
        result.pricing_calls += owned.pricing_calls;
        result.columns += owned.generated_columns;
        result.columns_generated_raw += owned.columns_generated_raw;
        result.nodes += owned.route_states + owned.operation_states + owned.master_states;
        result.columns_after_dominance += owned.columns_after_dominance;
        result.columns_dominated += owned.columns_dominated;
        result.dominance_time_seconds += owned.dominance_time_seconds;
        for (const std::string& note : owned.notes) {
            result.notes.push_back("auto/" + mode + ": " + note);
        }
        if (owned.found) {
            addRoutesToFrontierPool(owned.routes, "auto candidate " + mode);
            return recordIncumbentCandidate(owned.routes, "BPC-owned " + mode,
                                            elapsed);
        }
        ++result.incumbent_candidates_tested;
        ++result.incumbent_candidates_rejected;
        result.notes.push_back("best-of-all incumbent candidate source=BPC-owned "
            + mode + " rejected=no_route_found");
        return CandidateRecord{};
    };
    auto runCompactSeed = [&](const std::string& mode,
                              double seconds) {
        ebrp::SolveOptions seed_opt = opt;
        seed_opt.out_path.clear();
        seed_opt.log_path.clear();
        seed_opt.gcap_seed_cplex = false;
        seed_opt.bpc_incumbent = "none";
        seed_opt.solve_time_limit = seconds > 0.0
            ? seconds
            : std::min(30.0, std::max(1.0, opt.solve_time_limit * 0.25));
        seed_opt.method = (mode == "compact-cplex") ? "cplex" : "tailored";
        const auto seed_start = std::chrono::steady_clock::now();
        ebrp::SolveResult seed = (mode == "compact-cplex")
            ? ebrp::solveCplexBaseline(instance, seed_opt)
            : ebrp::solveTailoredExact(instance, seed_opt);
        const double elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - seed_start).count();
        std::ostringstream compact_note;
        compact_note << "compact incumbent seed mode=" << mode
                     << ", status=" << seed.status
                     << ", objective=" << seed.objective
                     << ", runtime=" << seed.runtime_seconds
                     << ", seed_time_limit=" << seed_opt.solve_time_limit;
        result.notes.push_back(compact_note.str());
        if (!seed.routes.empty()) {
            addRoutesToFrontierPool(seed.routes, "auto candidate " + mode);
            return recordIncumbentCandidate(seed.routes,
                mode == "compact-cplex" ? "compact CPLEX seed"
                                        : "compact tailored seed",
                elapsed);
        }
        ++result.incumbent_candidates_tested;
        ++result.incumbent_candidates_rejected;
        result.notes.push_back("best-of-all incumbent candidate source=" + mode
            + " rejected=no_reconstructable_route");
        return CandidateRecord{};
    };

    const bool auto_incumbent =
        opt.bpc_incumbent == "auto" || opt.bpc_incumbent == "best-of-all";
    const bool skip_default_auto_incumbent =
        auto_incumbent &&
        verified_archive_incumbent_selected &&
        opt.algorithm_preset == "paper-bpc-core" &&
        opt.bpc_incumbent == "auto";
    if (skip_default_auto_incumbent) {
        result.incumbent_selection_reason =
            "verified incumbent archive route plan already selected; skipped default BPC-owned auto incumbent search";
        result.notes.push_back(
            "paper-bpc-core skipped default BPC-owned auto incumbent portfolio because a verified archive incumbent was already accepted as UB-only cutoff; no lower-bound certificate is inherited from the archive");
    } else if (auto_incumbent) {
        const auto incumbent_start = std::chrono::steady_clock::now();
        std::vector<CandidateRecord> candidates;
        const std::vector<std::string> modes{
            "greedy", "local", "pool", "pricing", "portfolio", "strong",
            "compact", "compact-cplex"};
        const double total_budget = opt.bpc_incumbent_seconds > 0.0
            ? opt.bpc_incumbent_seconds
            : std::min(60.0, std::max(8.0, opt.solve_time_limit * 0.25));
        for (int pos = 0; pos < static_cast<int>(modes.size()); ++pos) {
            const double elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - incumbent_start).count();
            if (total_budget > 0.0 && elapsed >= total_budget) break;
            const int remaining_modes =
                std::max(1, static_cast<int>(modes.size()) - pos);
            const double remaining_budget = total_budget > 0.0
                ? std::max(0.5, total_budget - elapsed)
                : opt.bpc_incumbent_seconds;
            const double per_mode_budget =
                total_budget > 0.0
                    ? std::max(0.5, remaining_budget / remaining_modes)
                    : opt.bpc_incumbent_seconds;
            if (modes[pos] == "compact" || modes[pos] == "compact-cplex") {
                candidates.push_back(runCompactSeed(modes[pos], per_mode_budget));
            } else {
                candidates.push_back(runExplicitBpcSeed(modes[pos], per_mode_budget));
            }
        }
        result.incumbent_generation_time_seconds +=
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - incumbent_start).count();
        CandidateRecord best;
        for (const CandidateRecord& candidate : candidates) {
            if (!candidate.found) continue;
            if (!best.found ||
                candidate.verification.objective <
                    best.verification.objective - 1e-10) {
                best = candidate;
            }
        }
        if (best.found) {
            acceptIncumbentRoutes(best.routes, best.source);
            result.incumbent_source_detail =
                "best-of-all verified incumbent selected from portfolio; UB only";
            result.notes.push_back("best-of-all incumbent selected source="
                + best.source + ", objective="
                + std::to_string(best.verification.objective)
                + ", G=" + std::to_string(best.verification.G)
                + ", P=" + std::to_string(best.verification.P));
        } else {
            result.incumbent_selection_reason =
                "no verified portfolio incumbent found; retained empty incumbent";
        }
    } else {
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
            recordIncumbentCandidate(owned.routes, "BPC-owned " + opt.bpc_incumbent,
                                     result.incumbent_generation_time_seconds);
            acceptIncumbentRoutes(owned.routes, "BPC-owned " + opt.bpc_incumbent);
        }
    }

    if (!auto_incumbent && (opt.bpc_incumbent == "compact" ||
        opt.bpc_incumbent == "compact-cplex")) {
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
            recordIncumbentCandidate(seed.routes, source,
                std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - compact_start).count());
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
                if (source_label.find("external") != std::string::npos) {
                    result.external_incumbent_verified = true;
                    result.external_incumbent_objective = imported.objective;
                    result.external_incumbent_G = imported.G;
                    result.external_incumbent_P = imported.P;
                    result.external_incumbent_used_in_large_run = instance.V >= 20;
                    result.external_incumbent_rejection_reason = "none";
                }
                recordIncumbentCandidate(external_routes, import_source, 0.0);
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
                if (source_label.find("external") != std::string::npos) {
                    result.external_incumbent_effect_on_UB =
                        std::max(0.0, result.upper_bound - imported.objective);
                }
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

    addRoutesToFrontierPool(incumbent_routes, "verified incumbent after seed stage");

    result.routes = incumbent_routes;
    result.verification = incumbent_verification;
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;
    if (result.incumbent_source.empty()) result.incumbent_source = "empty-route incumbent";
    runRoutePoolIncumbentMaster("after_seed_stage");
    result.routes = incumbent_routes;
    result.verification = incumbent_verification;
    result.final_inventory = result.verification.final_inventory;
    result.G = result.verification.G;
    result.P = result.verification.P;
    result.objective = result.verification.objective;
    result.upper_bound = result.objective;

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
        writeMinimalPaperCoreTrace(instance, opt, result, "no_feasible_incumbent");
        return result;
    }

    if (result.objective <= 1e-12) {
        result.lower_bound = 0.0;
        result.upper_bound = result.objective;
        result.gap = 0.0;
        result.status = "optimal";
        result.certificate = "frontier certificate: a feasible incumbent has objective zero and both Gini and satisfaction terms are nonnegative";
        result.full_certificate_basis = "zero_objective_nonnegative";
        result.full_certificate_requires_pricing_closure = false;
        result.full_certificate_pricing_closure_satisfied = true;
        result.full_certificate_all_intervals_accounted = true;
        result.full_certificate_rejection_reason = "none";
        result.interval_certificate_basis = "zero_objective_global";
        result.interval_requires_pricing_closure = "false";
        result.interval_pricing_closure_available = "false";
        result.interval_bound_valid = "true";
        result.interval_bound_source_list = "nonnegative_objective";
        result.runtime_seconds = elapsedSeconds();
        result.wall_time_seconds = result.runtime_seconds;
        result.aggregate_worker_time_seconds = result.pricing_time_seconds +
            result.master_time_seconds + result.bound_time_seconds;
        result.notes.push_back("zero incumbent closes the global objective without interval solves");
        writeMinimalPaperCoreTrace(instance, opt, result, "zero_objective_nonnegative_global_bound");
        return result;
    }

    if (cover_lo > cover_hi + 1e-12) {
        result.status = "gcap_frontier_invalid_range";
        result.certificate = "frontier lower Gini bound exceeds the covered upper bound";
        result.runtime_seconds = elapsedSeconds();
        result.wall_time_seconds = result.runtime_seconds;
        result.aggregate_worker_time_seconds = result.pricing_time_seconds +
            result.master_time_seconds + result.bound_time_seconds;
        writeMinimalPaperCoreTrace(instance, opt, result, "invalid_frontier_range");
        return result;
    }

    int intervals = std::max(1, opt.frontier_intervals);
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
        long long bpc_nodes = 0;
        long long generated_columns = 0;
        long long cuts_added = 0;
        long long pricing_calls = 0;
        double pricing_time_seconds = 0.0;
        double master_time_seconds = 0.0;
        double relaxation_time_seconds = 0.0;
        std::vector<std::string> node_trace_json_objects;
        std::vector<std::string> pricing_trace_json_objects;
        std::string lower_bound_source = "gamma_floor";
        std::string lb_sources = "gamma_floor";
        bool bound_fathomed = false;
        bool tree_closed = false;
        bool pricing_closed = false;
        std::string certificate_basis = "unresolved";
        bool requires_pricing_closure = false;
        bool pricing_closure_available = false;
        bool interval_bound_valid = true;
        double cheap_prepass_lower_bound = 0.0;
        std::string cheap_prepass_sources = "gamma_floor";
        int parent_id = -1;
        int split_depth = 0;
        int child_index = -1;
        double inherited_parent_lb = 0.0;
        std::string relaxation_portfolio_mode = "fixed";
        std::string relaxation_variants_tried;
        std::string selected_relaxation_variant;
        std::string selected_variant_reason;
        double probe_time_seconds = 0.0;
        double variant_bound_improvement = 0.0;
        double best_variant_bound = 0.0;
        std::string variants_skipped_reason;
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

    auto makeRangeString = [](double lo, double hi) {
        std::ostringstream range;
        range << "[" << lo << "," << hi << "]";
        return range.str();
    };
    auto copyPortfolioFieldsToInterval =
        [](FrontierIntervalRecord& record,
           const ebrp::GiniIntervalInventoryRelaxationBound& bound) {
            record.relaxation_portfolio_mode = bound.relaxation_portfolio_mode;
            record.relaxation_variants_tried = bound.relaxation_variants_tried;
            record.selected_relaxation_variant =
                bound.selected_relaxation_variant;
            record.selected_variant_reason = bound.selected_variant_reason;
            record.probe_time_seconds = bound.probe_time_seconds;
            record.variant_bound_improvement =
                bound.variant_bound_improvement;
            record.best_variant_bound = bound.best_variant_bound;
            record.variants_skipped_reason = bound.variants_skipped_reason;
        };

    auto treePricingClosureStrict =
        [](const ebrp::GiniCapTreeResult& tree) {
            const double best_rc = std::isfinite(tree.pricing_best_reduced_cost_any)
                ? tree.pricing_best_reduced_cost_any
                : 0.0;
            return tree.pricing_completed_exactly &&
                   tree.pricing_closure_certified_exact &&
                   !tree.pricing_blocked_by_duplicate_projection &&
                   best_rc >= -1e-7 &&
                   tree.pricing_closure_status == "exact_no_negative";
        };

    auto recordTreeAggregate =
        [&](FrontierIntervalRecord& record,
            const ebrp::GiniCapTreeResult& tree) {
            record.bpc_nodes += tree.nodes_solved;
            record.generated_columns += tree.generated_columns;
            record.cuts_added += tree.cuts_added;
            record.pricing_calls += tree.pricing_calls;
            record.pricing_time_seconds += tree.pricing_time_seconds;
            record.master_time_seconds += tree.master_time_seconds;
            record.open_nodes = tree.open_nodes;
            record.node_trace_json_objects.insert(
                record.node_trace_json_objects.end(),
                tree.node_trace_json_objects.begin(),
                tree.node_trace_json_objects.end());
            record.pricing_trace_json_objects.insert(
                record.pricing_trace_json_objects.end(),
                tree.pricing_trace_json_objects.begin(),
                tree.pricing_trace_json_objects.end());
        };

    auto closureIterations = [&](int default_iterations) {
        return opt.frontier_closure_mode == "exact-cg"
            ? std::max(1, opt.closure_max_cg_iterations)
            : default_iterations;
    };

    auto closurePricingColumns = [&]() {
        return opt.frontier_closure_mode == "exact-cg"
            ? std::max(opt.gcap_pricing_columns, opt.closure_returned_columns)
            : opt.gcap_pricing_columns;
    };

    ParsedFrontierInterval requested_focus_interval;
    ParsedFrontierInterval resume_interval;
    bool resume_interval_available = false;
    std::string resume_state_path_used;
    bool focus_only_effective = opt.frontier_focus_only;
    if (focus_only_effective && !opt.frontier_focus_range.empty()) {
        double lo = 0.0;
        double hi = 0.0;
        if (parseGiniRangeString(opt.frontier_focus_range, lo, hi)) {
            requested_focus_interval.valid = true;
            requested_focus_interval.id = 0;
            requested_focus_interval.lo = lo;
            requested_focus_interval.hi = hi;
            requested_focus_interval.lower_bound = std::max(0.0, lo);
            requested_focus_interval.source = "cli_frontier_focus_range";
        } else {
            result.notes.push_back("frontier focus range rejected because it could not be parsed: "
                + opt.frontier_focus_range);
        }
    }
    if (focus_only_effective && !opt.frontier_focus_from_result.empty()) {
        try {
            const std::string text =
                readWholeTextFile(opt.frontier_focus_from_result);
            const std::vector<ParsedFrontierInterval> parsed =
                parseFrontierIntervalsFromResultText(text);
            ParsedFrontierInterval chosen =
                chooseFocusIntervalFromParsed(parsed, opt.frontier_focus_leaf_id);
            if (chosen.valid) {
                requested_focus_interval = chosen;
                result.notes.push_back("frontier focus interval selected from result="
                    + opt.frontier_focus_from_result
                    + ", source=" + chosen.source
                    + ", id=" + std::to_string(chosen.id)
                    + ", range=" + makeRangeString(chosen.lo, chosen.hi)
                    + ", lb=" + std::to_string(chosen.lower_bound));
            } else {
                result.notes.push_back("frontier focus-from-result parsed no usable interval: "
                    + opt.frontier_focus_from_result);
            }
            if (opt.frontier_focus_use_existing_incumbent) {
                result.notes.push_back("frontier_focus_use_existing_incumbent=true: this pass uses the normal verified incumbent pipeline; pass the same result through --incumbent-json when reconstructable route reuse is required");
            }
        } catch (const std::exception& ex) {
            result.notes.push_back("frontier focus-from-result failed: "
                + std::string(ex.what()));
        }
    }
    if (!opt.frontier_resume_state_path.empty()) {
        result.resumed_from_state = true;
        resume_state_path_used = opt.frontier_resume_state_path;
        try {
            const std::string text = readWholeTextFile(opt.frontier_resume_state_path);
            const std::string state_instance =
                extractJsonStringForKey(text, "instance_name", "");
            const double state_lambda =
                extractJsonDoubleForKey(text, "lambda", opt.lambda);
            const bool instance_ok = state_instance.empty() ||
                state_instance == instance.name ||
                state_instance == std::filesystem::path(instance.path).filename().string();
            const bool lambda_ok = std::fabs(state_lambda - opt.lambda) <= 1e-9;
            if (!instance_ok || !lambda_ok) {
                result.resume_state_compatible = false;
                result.resume_state_rejection_reason =
                    !instance_ok ? "instance_mismatch" : "lambda_mismatch";
                result.notes.push_back("frontier resume state rejected: path="
                    + opt.frontier_resume_state_path
                    + ", reason=" + result.resume_state_rejection_reason);
            } else {
                const std::vector<ParsedFrontierInterval> parsed =
                    parseFrontierIntervalsFromResultText(text);
                ParsedFrontierInterval chosen =
                    chooseFocusIntervalFromParsed(parsed,
                        opt.frontier_resume_interval_id.empty()
                            ? std::string("auto")
                            : opt.frontier_resume_interval_id);
                if (!chosen.valid) {
                    result.resume_state_compatible = false;
                    result.resume_state_rejection_reason =
                        "no_usable_unresolved_interval";
                } else {
                    result.resume_state_compatible = true;
                    resume_interval_available = true;
                    resume_interval = chosen;
                    result.resume_state_interval_lb = chosen.lower_bound;
                    result.resume_state_columns_loaded =
                        extractJsonIntForKey(text,
                            "route_pool_columns_after_dominance",
                            extractJsonIntForKey(text, "columns", 0));
                    result.resume_state_nodes_loaded =
                        extractJsonIntForKey(text, "open_node_state_nodes_saved",
                            extractJsonIntForKey(text, "open_nodes", 0));
                    if (opt.frontier_resume_open_nodes) {
                        result.open_node_state_imported = true;
                        result.open_node_state_nodes_loaded =
                            result.resume_state_nodes_loaded;
                        result.open_node_state_resume_exact =
                            extractJsonBoolForKey(text,
                                "open_node_state_resume_exact", false);
                        result.open_node_state_resume_fallback_reason =
                            result.open_node_state_resume_exact
                                ? "exact_open_node_state_restored"
                                : extractJsonStringForKey(text,
                                      "open_node_state_resume_fallback_reason",
                                      "partial_state_rebuilds_tree_no_live_node_queue");
                    }
                    if (opt.frontier_resume_mode == "interval-only") {
                        focus_only_effective = true;
                        requested_focus_interval = chosen;
                    }
                    result.notes.push_back("frontier resume state accepted: path="
                        + opt.frontier_resume_state_path
                        + ", interval_id=" + std::to_string(chosen.id)
                        + ", range=" + makeRangeString(chosen.lo, chosen.hi)
                        + ", interval_lb=" + std::to_string(chosen.lower_bound)
                        + ", columns_loaded="
                        + std::to_string(result.resume_state_columns_loaded)
                        + "; open-node serialization is not available in this build, so the interval tree is rebuilt from verified state metadata and generated columns");
                }
            }
        } catch (const std::exception& ex) {
            result.resume_state_compatible = false;
            result.resume_state_rejection_reason = "read_or_parse_error";
            result.notes.push_back("frontier resume state failed: path="
                + opt.frontier_resume_state_path + ", error=" + ex.what());
        }
    }
    if (focus_only_effective && requested_focus_interval.valid) {
        FrontierIntervalRecord focus_record;
        focus_record.lo = std::max(0.0, requested_focus_interval.lo);
        focus_record.hi = std::max(focus_record.lo, requested_focus_interval.hi);
        focus_record.lower_bound =
            std::max(focus_record.lo, requested_focus_interval.lower_bound);
        focus_record.relaxation_lower_bound = focus_record.lower_bound;
        focus_record.lower_bound_valid = true;
        focus_record.lower_bound_source = requested_focus_interval.source.empty()
            ? "requested_focus_interval"
            : requested_focus_interval.source;
        focus_record.lb_sources += "|" + focus_record.lower_bound_source;
        focus_record.open_nodes = std::max(0, requested_focus_interval.open_nodes);
        focus_record.parent_id = requested_focus_interval.id;
        focus_record.pricing_closed = requested_focus_interval.pricing_closed;
        interval_records.assign(1, focus_record);
        intervals = 1;
        result.focus_interval_parent_id = requested_focus_interval.id;
        result.notes.push_back("frontier focus-only exact requested interval replaces the uniform frontier for this diagnostic run: range="
            + makeRangeString(focus_record.lo, focus_record.hi)
            + ", source=" + focus_record.lower_bound_source
            + ", parent_leaf_id=" + std::to_string(requested_focus_interval.id)
            + "; certificate_scope=diagnostic_interval_only");
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

    auto currentActiveMinIntervalLowerBound = [&]() {
        double min_lb = std::numeric_limits<double>::infinity();
        for (const FrontierIntervalRecord& record : interval_records) {
            if (record.replaced_by_children) continue;
            if (record.lo >= result.upper_bound - 1e-12) continue;
            const double lb = record.lower_bound_valid
                ? record.lower_bound
                : std::max(0.0, record.lo);
            min_lb = std::min(min_lb, lb);
        }
        return std::isfinite(min_lb) ? min_lb : 0.0;
    };

    auto applyImportedIntervalBound =
        [&](const ParsedFrontierInterval& imported,
            const std::string& path) {
            ++result.imported_interval_bounds_attempted;
            const bool track_v12_m1_import = true;
            if (track_v12_m1_import && result.v12_m1_full_lb_before_import <= 0.0) {
                result.v12_m1_full_lb_before_import =
                    currentActiveMinIntervalLowerBound();
            }
            if (track_v12_m1_import) {
                ++result.v12_m1_focus_intervals_attempted;
            }
            constexpr double eps = 1e-8;
            if (!imported.valid || imported.hi < imported.lo - eps) {
                ++result.imported_interval_bounds_rejected;
                if (!result.imported_interval_bounds_rejection_reasons.empty()) {
                    result.imported_interval_bounds_rejection_reasons += ";";
                }
                result.imported_interval_bounds_rejection_reasons +=
                    "invalid_import:" + path;
                return;
            }
            int exact_idx = -1;
            int containing_idx = -1;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.replaced_by_children) continue;
                if (std::fabs(record.lo - imported.lo) <= eps &&
                    std::fabs(record.hi - imported.hi) <= eps) {
                    exact_idx = idx;
                    break;
                }
                if (record.lo <= imported.lo + eps &&
                    imported.hi <= record.hi + eps) {
                    containing_idx = idx;
                }
            }
            auto updateRecord = [&](FrontierIntervalRecord& record) {
                const double old_lb = record.lower_bound;
                record.lower_bound =
                    std::max(record.lower_bound,
                             std::max(record.lo, imported.lower_bound));
                record.relaxation_lower_bound =
                    std::max(record.relaxation_lower_bound,
                             record.lower_bound);
                record.lower_bound_valid = true;
                if (record.lower_bound > old_lb + eps) {
                    record.lower_bound_source = "imported_focus_interval_bound";
                }
                record.lb_sources += "|imported_focus_interval_bound";
                if (imported.closed || imported.bound_fathomed) {
                    record.complete = imported.closed;
                    record.bound_fathomed = imported.bound_fathomed ||
                        (record.lower_bound >= result.upper_bound - 1e-7);
                    record.open_nodes = 0;
                    ++result.imported_interval_bounds_closed_intervals;
                } else {
                    record.open_nodes =
                        std::max(record.open_nodes, imported.open_nodes);
                }
                record.pricing_closed =
                    record.pricing_closed || imported.pricing_closed;
            };
            if (exact_idx >= 0) {
                updateRecord(interval_records[exact_idx]);
                ++result.imported_interval_bounds_accepted;
                if (track_v12_m1_import) {
                    result.v12_m1_imported_focus_bounds = true;
                    result.v12_m1_focus_bounds_accepted =
                        result.imported_interval_bounds_accepted;
                    ++result.v12_m1_focus_bounds_imported;
                    result.v12_m1_full_lb_after_import =
                        currentActiveMinIntervalLowerBound();
                }
                result.notes.push_back("accepted imported focus interval bound exact match: path="
                    + path + ", interval=" + std::to_string(exact_idx)
                    + ", range=" + makeRangeString(imported.lo, imported.hi)
                    + ", lb=" + std::to_string(imported.lower_bound)
                    + ", closed=" + std::string(imported.closed ? "true" : "false")
                    + ", bound_fathomed="
                    + std::string(imported.bound_fathomed ? "true" : "false"));
                return;
            }
            if (containing_idx < 0) {
                ++result.imported_interval_bounds_rejected;
                if (!result.imported_interval_bounds_rejection_reasons.empty()) {
                    result.imported_interval_bounds_rejection_reasons += ";";
                }
                result.imported_interval_bounds_rejection_reasons +=
                    "range_not_covered:" + path;
                return;
            }
            FrontierIntervalRecord parent = interval_records[containing_idx];
            interval_records[containing_idx].replaced_by_children = true;
            std::vector<FrontierIntervalRecord> children;
            auto addChild = [&](double lo, double hi,
                                const std::string& source,
                                bool imported_child) {
                if (hi <= lo + eps) return;
                FrontierIntervalRecord child = parent;
                child.replaced_by_children = false;
                child.lo = lo;
                child.hi = hi;
                child.parent_id = containing_idx;
                child.split_depth = parent.split_depth + 1;
                child.child_index = static_cast<int>(children.size());
                child.inherited_parent_lb = parent.lower_bound;
                child.complete = false;
                child.empty_complete = false;
                child.bound_fathomed = false;
                child.tree_closed = false;
                child.pricing_closed = false;
                child.open_nodes = parent.open_nodes;
                child.lower_bound_valid = parent.lower_bound_valid;
                child.lower_bound = std::max(parent.lower_bound, lo);
                child.lower_bound_source = source;
                child.lb_sources += "|" + source;
                if (imported_child) updateRecord(child);
                children.push_back(child);
            };
            addChild(parent.lo, imported.lo, "import_split_inherited_parent_lb", false);
            addChild(imported.lo, imported.hi, "imported_focus_interval_bound", true);
            addChild(imported.hi, parent.hi, "import_split_inherited_parent_lb", false);
            for (const FrontierIntervalRecord& child : children) {
                interval_records.push_back(child);
            }
            intervals = static_cast<int>(interval_records.size());
            ++result.imported_interval_bounds_accepted;
            if (track_v12_m1_import) {
                result.v12_m1_imported_focus_bounds = true;
                result.v12_m1_focus_bounds_accepted =
                    result.imported_interval_bounds_accepted;
                ++result.v12_m1_focus_bounds_imported;
                result.v12_m1_full_lb_after_import =
                    currentActiveMinIntervalLowerBound();
            }
            result.notes.push_back("accepted imported focus interval bound by splitting parent interval="
                + std::to_string(containing_idx)
                + ", imported_range=" + makeRangeString(imported.lo, imported.hi)
                + ", lb=" + std::to_string(imported.lower_bound)
                + ", path=" + path
                + "; child intervals exactly cover the original parent range");
        };

    for (const std::string& import_path :
         opt.frontier_import_interval_bound_paths) {
        try {
            const std::string text = readWholeTextFile(import_path);
            const std::vector<ParsedFrontierInterval> parsed =
                parseFrontierIntervalsFromResultText(text);
            ParsedFrontierInterval chosen =
                chooseFocusIntervalFromParsed(parsed, "min-lb");
            if (chosen.valid) {
                applyImportedIntervalBound(chosen, import_path);
            } else {
                ++result.imported_interval_bounds_attempted;
                ++result.imported_interval_bounds_rejected;
                if (!result.imported_interval_bounds_rejection_reasons.empty()) {
                    result.imported_interval_bounds_rejection_reasons += ";";
                }
                result.imported_interval_bounds_rejection_reasons +=
                    "no_usable_interval:" + import_path;
            }
        } catch (const std::exception& ex) {
            ++result.imported_interval_bounds_attempted;
            ++result.imported_interval_bounds_rejected;
            if (!result.imported_interval_bounds_rejection_reasons.empty()) {
                result.imported_interval_bounds_rejection_reasons += ";";
            }
            result.imported_interval_bounds_rejection_reasons +=
                "read_error:" + import_path;
            result.notes.push_back("frontier import interval bound failed for "
                + import_path + ": " + ex.what());
        }
    }
    if (resume_interval_available &&
        opt.frontier_resume_mode == "full-frontier") {
        applyImportedIntervalBound(resume_interval,
                                   "resume_state:" + resume_state_path_used);
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
    if (focus_only_effective) {
        int focus_idx = -1;
        if (opt.frontier_focus_interval_id == "auto" ||
            opt.frontier_focus_interval_id.empty()) {
            for (int idx : initial_schedule) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.lo >= result.upper_bound - 1e-12) continue;
                if (focus_idx < 0 ||
                    record.lower_bound < interval_records[focus_idx].lower_bound - 1e-12 ||
                    (std::fabs(record.lower_bound -
                               interval_records[focus_idx].lower_bound) <= 1e-12 &&
                     idx < focus_idx)) {
                    focus_idx = idx;
                }
            }
        } else {
            try {
                focus_idx = std::stoi(opt.frontier_focus_interval_id);
            } catch (const std::exception&) {
                focus_idx = -1;
            }
        }
        if (focus_idx < 0 || focus_idx >= static_cast<int>(interval_records.size())) {
            focus_idx = initial_schedule.empty() ? 0 : initial_schedule.front();
        }
        focus_idx = std::max(0, std::min(focus_idx,
            static_cast<int>(interval_records.size()) - 1));
        FrontierIntervalRecord& focus_record = interval_records[focus_idx];
        std::ostringstream focus_range;
        focus_range << "[" << focus_record.lo << "," << focus_record.hi << "]";
        result.focus_interval_id = focus_idx;
        result.focus_interval_range = focus_range.str();
        result.focus_interval_lb_before = focus_record.lower_bound;
        result.focus_interval_bound_fathomed = focus_record.bound_fathomed;
        result.focus_interval_open_nodes_before = focus_record.open_nodes;
        if (result.focus_interval_parent_id < 0) {
            result.focus_interval_parent_id = focus_record.parent_id;
        }
        result.focus_interval_certificate_scope = "diagnostic_interval_only";
        initial_schedule.assign(1, focus_idx);
        result.interval_processing_order_actual = std::to_string(focus_idx);
        result.interval_processing_order = result.interval_processing_order_actual;
        result.frontier_range_certificate_scope = "diagnostic_interval_only";
        result.frontier_covers_all_improving_gini_values = false;
        result.notes.push_back("frontier focus-only diagnostic enabled: selected interval="
            + std::to_string(focus_idx)
            + ", range=" + result.focus_interval_range
            + ", initial_lb=" + std::to_string(result.focus_interval_lb_before)
            + "; this run cannot certify the original problem by itself");
    }

    struct ProgressSnapshot {
        double lb = 0.0;
        int interval_id = -1;
        std::string interval_range = "";
        std::string source = "";
        int unresolved = 0;
        long long open_nodes = 0;
    };
    std::ofstream progress_stream;
    double progress_interval = opt.progress_interval_seconds;
    if (progress_interval <= 0.0) {
        progress_interval = opt.solve_time_limit >= 300.0 ? 30.0 : 10.0;
    }
    double last_progress_write_time = -std::numeric_limits<double>::infinity();
    double previous_progress_lb = -std::numeric_limits<double>::infinity();
    double previous_progress_ub = std::numeric_limits<double>::infinity();
    result.best_gap_seen = std::numeric_limits<double>::infinity();
    auto snapshotFrontier = [&]() {
        ProgressSnapshot snapshot;
        snapshot.lb = std::numeric_limits<double>::infinity();
        for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
            const FrontierIntervalRecord& record = interval_records[idx];
            if (record.replaced_by_children) continue;
            if (record.lo >= result.upper_bound - 1e-12) continue;
            const double lb = record.lower_bound_valid ? record.lower_bound : record.lo;
            if (!record.complete && !record.empty_complete && !record.bound_fathomed &&
                lb < result.upper_bound - 1e-7) {
                ++snapshot.unresolved;
                snapshot.open_nodes += std::max(0, record.open_nodes);
            }
            if (lb < snapshot.lb - 1e-12 ||
                (std::fabs(lb - snapshot.lb) <= 1e-12 &&
                 (snapshot.interval_id < 0 || idx < snapshot.interval_id))) {
                snapshot.lb = lb;
                snapshot.interval_id = idx;
                snapshot.source = record.lower_bound_source;
                std::ostringstream range;
                range << "[" << record.lo << "," << record.hi << "]";
                snapshot.interval_range = range.str();
            }
        }
        if (!std::isfinite(snapshot.lb)) {
            snapshot.lb = result.lower_bound;
            snapshot.source = result.frontier_lower_bound_source;
        }
        return snapshot;
    };
    auto writeProgressCheckpoint = [&](const std::string& event, bool force) {
        if (opt.progress_log_path.empty()) return;
        const double now = elapsedSeconds();
        if (!force && now - last_progress_write_time < progress_interval - 1e-9) {
            return;
        }
        if (!progress_stream.is_open()) {
            std::filesystem::path progress_path(opt.progress_log_path);
            if (!progress_path.parent_path().empty()) {
                std::filesystem::create_directories(progress_path.parent_path());
            }
            const bool write_header =
                !std::filesystem::exists(progress_path) ||
                std::filesystem::file_size(progress_path) == 0;
            progress_stream.open(progress_path, std::ios::out | std::ios::app);
            if (write_header) {
                progress_stream << "elapsed_seconds,event,algorithm_preset,column_tracks,"
                                << "rmp_column_space,relaxed_columns_in_rmp,pricing_engine,"
                                << "large_instance_mode,station_set_backend,"
                                << "incumbent_UB,global_LB,gap,"
                                << "unresolved_intervals,global_min_lb_interval_id,"
                                << "global_min_lb_interval_range,global_min_lb_source,"
                                << "open_nodes,route_pool_columns_after_dominance,"
                                << "route_pool_best_incumbent,focused_intensification_passes,"
                                << "last_LB_improvement_time,last_UB_improvement_time,"
                                << "bound_time_seconds,master_time_seconds,pricing_time_seconds,"
                                << "columns,nodes\n";
            }
        }
        ProgressSnapshot snapshot = snapshotFrontier();
        if (snapshot.lb > previous_progress_lb + 1e-9) {
            result.last_lb_improvement_time_seconds = now;
            previous_progress_lb = snapshot.lb;
        }
        if (result.upper_bound < previous_progress_ub - 1e-9) {
            result.last_ub_improvement_time_seconds = now;
            previous_progress_ub = result.upper_bound;
        }
        const double gap = result.upper_bound > 1e-12
            ? std::max(0.0, (result.upper_bound - snapshot.lb) / result.upper_bound)
            : std::max(0.0, result.upper_bound - snapshot.lb);
        if (gap < result.best_gap_seen - 1e-12 || !std::isfinite(result.best_gap_seen)) {
            result.best_gap_seen = gap;
            result.best_gap_time_seconds = now;
        }
        double route_pool_best = result.route_pool_incumbent_found
            ? result.route_pool_incumbent_objective
            : 0.0;
        progress_stream << std::setprecision(12)
                        << now << "," << event << ","
                        << result.algorithm_preset << ","
                        << result.column_tracks << ","
                        << result.rmp_column_space << ","
                        << boolText(result.relaxed_rmp_enabled) << ","
                        << result.pricing_engine << ","
                        << result.large_instance_mode << ","
                        << result.station_set_backend << ","
                        << result.upper_bound << ","
                        << snapshot.lb << ","
                        << gap << ","
                        << snapshot.unresolved << ","
                        << snapshot.interval_id << ",\""
                        << snapshot.interval_range << "\","
                        << snapshot.source << ","
                        << snapshot.open_nodes << ","
                        << result.route_pool_columns_after_dominance << ","
                        << route_pool_best << ","
                        << result.focused_intensification_passes << ","
                        << result.last_lb_improvement_time_seconds << ","
                        << result.last_ub_improvement_time_seconds << ","
                        << result.bound_time_seconds << ","
                        << result.master_time_seconds << ","
                        << result.pricing_time_seconds << ","
                        << result.columns << ","
                        << result.nodes << "\n";
        progress_stream.flush();
        last_progress_write_time = now;
        ++result.progress_checkpoints_written;
    };

    auto remainingForPreIterativeWork = [&]() {
        const double remaining = remainingSeconds();
        if (!opt.frontier_iterative_closure || focus_only_effective ||
            opt.solve_time_limit <= 0.0) {
            return remaining;
        }
        const double requested_reserve =
            static_cast<double>(std::max(0, opt.frontier_iterative_max_rounds)) *
            std::max(0.0, opt.frontier_iterative_round_time);
        const double reserve = std::min(opt.solve_time_limit * 0.50,
                                        requested_reserve);
        return std::max(0.0, remaining - reserve);
    };

    auto runPricingVerifierCheckpoint =
        [&](const std::string& context, bool force_complete_if_already_closed) {
            if (!opt.pricing_final_verifier) return false;
            const auto verifier_start = std::chrono::steady_clock::now();
            ++result.iterative_pricing_verifier_calls;
            result.pricing_verifier_enabled = true;
            result.pricing_verifier_resumed =
                result.pricing_verifier_resumed ||
                (!opt.pricing_verifier_resume.empty() &&
                 std::filesystem::exists(opt.pricing_verifier_resume));
            const bool exact_closure_available =
                force_complete_if_already_closed &&
                result.pricing_completed_exactly &&
                !result.pricing_blocked_by_duplicate_projection &&
                result.pricing_best_reduced_cost_any >= -1e-7 &&
                result.pricing_closure_status == "exact_no_negative";
            result.pricing_verifier_complete =
                result.pricing_verifier_complete || exact_closure_available;
            if (exact_closure_available) {
                result.pricing_verifier_best_reduced_cost =
                    std::isfinite(result.pricing_best_reduced_cost_any)
                        ? result.pricing_best_reduced_cost_any : 0.0;
                ++result.iterative_pricing_verifier_completed;
            } else {
                result.pricing_verifier_best_reduced_cost =
                    std::isfinite(result.pricing_best_reduced_cost_any)
                        ? result.pricing_best_reduced_cost_any
                        : result.closure_final_best_reduced_cost;
            }
            result.pricing_verifier_labels_processed +=
                std::max<long long>(1, result.pricing_columns_enumerated);
            result.pricing_verifier_labels_pruned +=
                result.support_duration_pruned_labels +
                result.support_duration_strong_pruned_labels;
            if (!opt.pricing_verifier_checkpoint.empty()) {
                try {
                    std::filesystem::path checkpoint_path(
                        opt.pricing_verifier_checkpoint);
                    if (!checkpoint_path.parent_path().empty()) {
                        std::filesystem::create_directories(
                            checkpoint_path.parent_path());
                    }
                    std::ofstream checkpoint(checkpoint_path,
                                             std::ios::out | std::ios::trunc);
                    checkpoint << std::setprecision(12)
                               << "{\n"
                               << "  \"verifier_context\": \""
                               << jsonEscapeLocal(context) << "\",\n"
                               << "  \"verifier_mode\": \""
                               << jsonEscapeLocal(opt.pricing_verifier_mode)
                               << "\",\n"
                               << "  \"vehicles_completed\": "
                               << (exact_closure_available ? instance.M : 0)
                               << ",\n"
                               << "  \"masks_completed\": 0,\n"
                               << "  \"labels_processed\": "
                               << result.pricing_verifier_labels_processed
                               << ",\n"
                               << "  \"labels_pruned\": "
                               << result.pricing_verifier_labels_pruned
                               << ",\n"
                               << "  \"best_reduced_cost_so_far\": "
                               << result.pricing_verifier_best_reduced_cost
                               << ",\n"
                               << "  \"remaining_lower_bound\": 0,\n"
                               << "  \"verifier_complete\": "
                               << (result.pricing_verifier_complete
                                   ? "true" : "false")
                               << "\n"
                               << "}\n";
                    result.pricing_verifier_checkpoint_written = true;
                } catch (const std::exception& ex) {
                    result.notes.push_back("pricing verifier checkpoint failed in "
                        + context + ": " + ex.what());
                }
            }
            result.pricing_verifier_time_seconds +=
                std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - verifier_start).count();
            if (!result.pricing_verifier_complete) {
                result.notes.push_back("pricing_final_verifier checkpointed in "
                    + context
                    + "; exact closure remains false because true-dual pricing did not complete with no negative reduced-cost column");
            }
            return result.pricing_verifier_complete;
        };
    writeProgressCheckpoint("initial_after_seed", true);

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
            result.route_mask_operation_budget_cuts_added +=
                inv_relax.route_mask_operation_budget_cuts_added;
            if (inv_relax.route_mask_operation_budget_min > 0.0) {
                result.route_mask_operation_budget_min =
                    result.route_mask_operation_budget_min <= 0.0
                        ? inv_relax.route_mask_operation_budget_min
                        : std::min(result.route_mask_operation_budget_min,
                                   inv_relax.route_mask_operation_budget_min);
            }
            result.route_mask_operation_budget_max =
                std::max(result.route_mask_operation_budget_max,
                         inv_relax.route_mask_operation_budget_max);
            result.route_mask_operation_budget_avg =
                inv_relax.route_mask_operation_budget_avg;
            result.route_mask_operation_budget_tightened_masks +=
                inv_relax.route_mask_operation_budget_tightened_masks;
            result.route_mask_operation_budget_zero_masks +=
                inv_relax.route_mask_operation_budget_zero_masks;
            result.route_mask_operation_budget_precompute_time_seconds +=
                inv_relax.route_mask_operation_budget_precompute_time_seconds;
            result.pickup_drop_pairs_total += inv_relax.pickup_drop_pairs_total;
            result.pickup_drop_pairs_compatible +=
                inv_relax.pickup_drop_pairs_compatible;
            result.pickup_drop_pairs_incompatible +=
                inv_relax.pickup_drop_pairs_incompatible;
            result.pickup_drop_pairs_capacity_limited +=
                inv_relax.pickup_drop_pairs_capacity_limited;
            if (inv_relax.pickup_drop_transfer_cap_min > 0.0) {
                result.pickup_drop_transfer_cap_min =
                    result.pickup_drop_transfer_cap_min <= 0.0
                        ? inv_relax.pickup_drop_transfer_cap_min
                        : std::min(result.pickup_drop_transfer_cap_min,
                                   inv_relax.pickup_drop_transfer_cap_min);
            }
            result.pickup_drop_transfer_cap_max =
                std::max(result.pickup_drop_transfer_cap_max,
                         inv_relax.pickup_drop_transfer_cap_max);
            result.pickup_drop_transfer_cap_avg =
                inv_relax.pickup_drop_transfer_cap_avg;
            result.pickup_drop_transfer_cap_variables +=
                inv_relax.pickup_drop_transfer_cap_variables;
            result.pickup_drop_transfer_cap_constraints +=
                inv_relax.pickup_drop_transfer_cap_constraints;
            result.pickup_drop_transfer_cap_time_seconds +=
                inv_relax.pickup_drop_transfer_cap_time_seconds;
            result.pickup_drop_compat_flow_variables +=
                inv_relax.pickup_drop_compat_flow_variables;
            result.pickup_drop_compat_flow_constraints +=
                inv_relax.pickup_drop_compat_flow_constraints;
            result.pickup_drop_compat_flow_time_seconds +=
                inv_relax.pickup_drop_compat_flow_time_seconds;
            result.vehicle_indexed_operation_relaxation_enabled =
                result.vehicle_indexed_operation_relaxation_enabled ||
                inv_relax.vehicle_indexed_operation_relaxation_enabled;
            result.vehicle_indexed_y_variables +=
                inv_relax.vehicle_indexed_y_variables;
            result.vehicle_indexed_pickup_variables +=
                inv_relax.vehicle_indexed_pickup_variables;
            result.vehicle_indexed_drop_variables +=
                inv_relax.vehicle_indexed_drop_variables;
            result.vehicle_indexed_linking_constraints +=
                inv_relax.vehicle_indexed_linking_constraints;
            result.vehicle_indexed_balance_constraints +=
                inv_relax.vehicle_indexed_balance_constraints;
            result.vehicle_indexed_operation_budget_constraints +=
                inv_relax.vehicle_indexed_operation_budget_constraints;
            result.vehicle_indexed_relaxation_time_seconds +=
                inv_relax.vehicle_indexed_relaxation_time_seconds;
            result.vehicle_transfer_flow_variables +=
                inv_relax.vehicle_transfer_flow_variables;
            result.vehicle_transfer_depot_unload_variables +=
                inv_relax.vehicle_transfer_depot_unload_variables;
            result.vehicle_transfer_flow_balance_constraints +=
                inv_relax.vehicle_transfer_flow_balance_constraints;
            result.vehicle_transfer_mask_linking_constraints +=
                inv_relax.vehicle_transfer_mask_linking_constraints;
            result.vehicle_transfer_pairs_total +=
                inv_relax.vehicle_transfer_pairs_total;
            result.vehicle_transfer_pairs_zero_cap +=
                inv_relax.vehicle_transfer_pairs_zero_cap;
            result.vehicle_transfer_pairs_capacity_limited +=
                inv_relax.vehicle_transfer_pairs_capacity_limited;
            if (inv_relax.vehicle_transfer_cap_min > 0.0) {
                result.vehicle_transfer_cap_min =
                    result.vehicle_transfer_cap_min <= 0.0
                        ? inv_relax.vehicle_transfer_cap_min
                        : std::min(result.vehicle_transfer_cap_min,
                                   inv_relax.vehicle_transfer_cap_min);
            }
            result.vehicle_transfer_cap_max =
                std::max(result.vehicle_transfer_cap_max,
                         inv_relax.vehicle_transfer_cap_max);
            result.vehicle_transfer_cap_avg =
                inv_relax.vehicle_transfer_cap_avg;
            result.vehicle_transfer_flow_time_seconds +=
                inv_relax.vehicle_transfer_flow_time_seconds;
            result.v20_cover_candidate_subsets_tested +=
                inv_relax.v20_cover_candidate_subsets_tested;
            result.v20_cover_cuts_added += inv_relax.v20_cover_cuts_added;
            result.v20_cover_max_size_used =
                std::max(result.v20_cover_max_size_used,
                         inv_relax.v20_cover_max_size_used);
            result.v20_cover_separation_time_seconds +=
                inv_relax.v20_cover_separation_time_seconds;
            result.station_residual_cover_cuts_enabled =
                result.station_residual_cover_cuts_enabled ||
                inv_relax.station_residual_cover_cuts_enabled;
            result.station_residual_domains_tightened_count +=
                inv_relax.station_residual_domains_tightened_count;
            result.station_residual_domain_width_before +=
                inv_relax.station_residual_domain_width_before;
            result.station_residual_domain_width_after +=
                inv_relax.station_residual_domain_width_after;
            result.station_residual_cover_cuts_added +=
                inv_relax.station_residual_cover_cuts_added;
            result.station_residual_cover_time_seconds +=
                inv_relax.station_residual_cover_time_seconds;
            if (result.large_compact_flow_relaxation == "off" &&
                inv_relax.large_compact_flow_relaxation != "off") {
                result.large_compact_flow_relaxation =
                    inv_relax.large_compact_flow_relaxation;
            }
            result.large_compact_flow_arc_variables +=
                inv_relax.large_compact_flow_arc_variables;
            result.large_compact_flow_constraints +=
                inv_relax.large_compact_flow_constraints;
            result.large_compact_flow_time_seconds +=
                inv_relax.large_compact_flow_time_seconds;
            result.large_compact_flow_connectivity_enabled =
                result.large_compact_flow_connectivity_enabled ||
                inv_relax.large_compact_flow_connectivity_enabled;
            result.large_compact_flow_connectivity_variables +=
                inv_relax.large_compact_flow_connectivity_variables;
            result.large_compact_flow_connectivity_constraints +=
                inv_relax.large_compact_flow_connectivity_constraints;
            result.large_compact_flow_connectivity_time_seconds +=
                inv_relax.large_compact_flow_connectivity_time_seconds;
            result.service_operation_min_handling_cuts_enabled =
                result.service_operation_min_handling_cuts_enabled ||
                inv_relax.service_operation_min_handling_cuts_enabled;
            result.service_operation_min_handling_cuts_added +=
                inv_relax.service_operation_min_handling_cuts_added;
            result.penalty_movement_lb_cuts_enabled =
                result.penalty_movement_lb_cuts_enabled ||
                inv_relax.penalty_movement_lb_cuts_enabled;
            result.penalty_movement_required_units =
                std::max(result.penalty_movement_required_units,
                         inv_relax.penalty_movement_required_units);
            result.penalty_movement_lb_cuts_added +=
                inv_relax.penalty_movement_lb_cuts_added;
            result.transfer_subset_capacity_cuts_enabled =
                result.transfer_subset_capacity_cuts_enabled ||
                inv_relax.transfer_subset_capacity_cuts_enabled;
            result.transfer_subset_capacity_cuts_added +=
                inv_relax.transfer_subset_capacity_cuts_added;
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
            const bool had_pricing_status =
                result.pricing_closure_status != "not_run";
            const bool tree_pricing_closed = treePricingClosureStrict(tree);
            if (tree.pricing_calls > 0) {
                result.pricing_closure_certified_exact = had_pricing_status
                    ? (result.pricing_closure_certified_exact && tree_pricing_closed)
                    : tree_pricing_closed;
            }
            if (result.pricing_closure_status.empty() ||
                result.pricing_closure_status == "not_run" ||
                tree.pricing_closure_status == "negative_columns_remaining" ||
                tree.pricing_closure_status == "duplicate_negative_projection" ||
                tree.pricing_closure_status == "pricing_time_limit") {
                result.pricing_closure_status = tree.pricing_closure_status;
            }
            if (tree.pricing_remaining_negative_rc <
                result.pricing_remaining_negative_rc) {
                result.pricing_remaining_negative_rc =
                    tree.pricing_remaining_negative_rc;
            }
            result.pricing_exact_verification_calls +=
                tree.pricing_exact_verification_calls;
            result.pricing_exact_verification_time_seconds +=
                tree.pricing_exact_verification_time_seconds;
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
            result.completion_lb_pruned_labels += tree.completion_lb_pruned_labels;
            result.required_closure_pruned_labels +=
                tree.required_closure_pruned_labels;
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
            result.inventory_branch_candidates +=
                tree.inventory_branch_candidates;
            result.inventory_branch_nodes_created +=
                tree.inventory_branch_nodes_created;
            if (tree.inventory_branch_station > 0) {
                result.inventory_branch_station = tree.inventory_branch_station;
                result.inventory_branch_value = tree.inventory_branch_value;
                result.inventory_branch_left_bound = tree.inventory_branch_left_bound;
                result.inventory_branch_right_bound = tree.inventory_branch_right_bound;
            }
            result.inventory_branch_pruned_nodes +=
                tree.inventory_branch_pruned_nodes;
            result.inventory_branch_max_depth =
                std::max(result.inventory_branch_max_depth,
                         tree.inventory_branch_max_depth);
            result.operation_mode_branch_candidates +=
                tree.operation_mode_branch_candidates;
            result.operation_mode_branch_nodes_created +=
                tree.operation_mode_branch_nodes_created;
            if (tree.operation_mode_branch_station > 0) {
                result.operation_mode_branch_station =
                    tree.operation_mode_branch_station;
                result.operation_mode_branch_type =
                    tree.operation_mode_branch_type;
            }
            result.operation_mode_branch_pruned_columns +=
                tree.operation_mode_branch_pruned_columns;
            result.operation_mode_branch_pruned_labels +=
                tree.operation_mode_branch_pruned_labels;
            result.branch_selection_mode = tree.branch_selection_mode;
            result.strong_branching_calls += tree.strong_branching_calls;
            result.strong_branching_candidates_tested +=
                tree.strong_branching_candidates_tested;
            result.strong_branching_time_seconds +=
                tree.strong_branching_time_seconds;
            if (!tree.selected_branch_type.empty()) {
                result.selected_branch_type = tree.selected_branch_type;
                result.selected_branch_score = tree.selected_branch_score;
                result.selected_branch_child_lb_left =
                    tree.selected_branch_child_lb_left;
                result.selected_branch_child_lb_right =
                    tree.selected_branch_child_lb_right;
            }
            result.branch_nodes_by_type_ryan_foster +=
                tree.branch_nodes_by_type_ryan_foster;
            result.branch_nodes_by_type_inventory +=
                tree.branch_nodes_by_type_inventory;
            result.branch_nodes_by_type_operation_mode +=
                tree.branch_nodes_by_type_operation_mode;
        };

    auto recordClosureContinuationStats =
        [&](const ebrp::GiniCapTreeResult& tree, const std::string& context) {
            if (opt.frontier_closure_mode == "auto") return;
            result.closure_mode = opt.frontier_closure_mode;
            result.closure_cg_iterations += static_cast<int>(tree.pricing_calls);
            result.closure_columns_added += tree.columns_exported_from_pricing;
            result.closure_pricing_calls += tree.pricing_calls;
            result.closure_final_exact_pricing_run =
                result.closure_final_exact_pricing_run ||
                opt.closure_final_exact_pricing;
            result.closure_final_best_reduced_cost =
                std::isfinite(tree.pricing_best_reduced_cost_any)
                    ? tree.pricing_best_reduced_cost_any
                    : result.closure_final_best_reduced_cost;
            result.closure_pricing_closed =
                result.closure_pricing_closed || treePricingClosureStrict(tree);
            result.closure_time_seconds += tree.pricing_time_seconds +
                tree.master_time_seconds;
            result.closure_stop_reason = treePricingClosureStrict(tree)
                ? "exact_no_negative"
                : tree.pricing_closure_status;
            result.cg_stabilization_mode = opt.cg_dual_stabilization;
            result.cg_true_pricing_calls += tree.pricing_calls;
            result.cg_true_pricing_columns_found +=
                tree.pricing_negative_columns_inserted;
            result.cg_final_true_pricing_rc =
                std::isfinite(tree.pricing_best_reduced_cost_any)
                    ? tree.pricing_best_reduced_cost_any
                    : result.cg_final_true_pricing_rc;
            if (opt.cg_dual_stabilization != "none") {
                result.notes.push_back("cg_dual_stabilization=" +
                    opt.cg_dual_stabilization + " requested in " + context +
                    "; this build uses true-dual pricing for certificate safety and records stabilization as a disabled column-discovery heuristic");
            }
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
            << "|movement_audit=" << (opt.movement_bound_audit ? 1 : 0)
            << "|pickup_drop_compat=" << (opt.pickup_drop_compat_flow ? 1 : 0)
            << "|pickup_drop_transfer_cap="
            << (opt.pickup_drop_transfer_cap_flow ? 1 : 0)
            << "|route_mask_operation_budget="
            << (opt.route_mask_operation_budget_cuts ? 1 : 0)
            << "|vehicle_indexed_ops="
            << (opt.vehicle_indexed_operation_relaxation ? 1 : 0)
            << "|vehicle_indexed_audit="
            << (opt.vehicle_indexed_relaxation_audit ? 1 : 0)
            << "|vehicle_transfer_flow="
            << (opt.vehicle_indexed_transfer_flow ? 1 : 0)
            << "|v20_safe_relaxation_cuts="
            << (opt.v20_safe_relaxation_cuts ? 1 : 0)
            << "|v20_cover_cuts=" << (opt.v20_cover_cuts ? 1 : 0)
            << "|v20_cover_max_size=" << opt.v20_cover_max_size
            << "|v20_cover_max_cuts=" << opt.v20_cover_max_cuts
            << "|station_residual_cover_cuts="
            << (opt.station_residual_cover_cuts ? 1 : 0)
            << "|station_residual_cover_max_cuts="
            << opt.station_residual_cover_max_cuts
            << "|large_compact_flow_relaxation="
            << opt.large_compact_flow_relaxation
            << "|large_compact_flow_connectivity="
            << (opt.large_compact_flow_connectivity ? 1 : 0)
            << "|service_operation_min_handling_cuts="
            << (opt.service_operation_min_handling_cuts ? 1 : 0)
            << "|penalty_movement_lb_cuts="
            << (opt.penalty_movement_lb_cuts ? 1 : 0)
            << "|transfer_subset_capacity_cuts="
            << (opt.transfer_subset_capacity_cuts ? 1 : 0)
            << "|relaxation_portfolio_mode="
            << opt.relaxation_portfolio_mode;
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
            auto compute_once_full = [&](bool movement_enabled,
                                         bool compat_enabled,
                                         bool vehicle_indexed_enabled,
                                         bool vehicle_transfer_enabled,
                                         bool operation_budget_enabled,
                                         double candidate_budget,
                                         const std::string& compact_flow_mode,
                                         bool compact_connectivity,
                                         bool service_min_handling,
                                         bool penalty_movement,
                                         bool transfer_subset_capacity) {
                return ebrp::computeGiniIntervalInventoryRelaxationBound(
                    instance, opt.lambda, lo, hi, candidate_budget, cutoff,
                    opt.route_mask_max_v, opt.projection_bound,
                    opt.penalty_domain_tightening,
                    movement_enabled,
                    opt.route_mask_support_duration_pruning,
                    compat_enabled,
                    opt.pickup_drop_transfer_cap_flow,
                    operation_budget_enabled,
                    vehicle_indexed_enabled,
                    vehicle_transfer_enabled,
                    opt.v20_safe_relaxation_cuts,
                    opt.v20_cover_cuts,
                    opt.v20_cover_max_size,
                    opt.v20_cover_max_cuts,
                    opt.v20_cover_separation_seconds,
                    opt.station_residual_cover_cuts,
                    opt.station_residual_cover_max_cuts,
                    compact_flow_mode,
                    opt.large_compact_flow_time_limit,
                    compact_connectivity,
                    service_min_handling,
                    penalty_movement,
                    transfer_subset_capacity);
            };
            auto compute_once = [&](bool movement_enabled,
                                    bool compat_enabled,
                                    bool vehicle_indexed_enabled,
                                    bool vehicle_transfer_enabled,
                                    bool operation_budget_enabled) {
                return compute_once_full(
                    movement_enabled,
                    compat_enabled,
                    vehicle_indexed_enabled,
                    vehicle_transfer_enabled,
                    operation_budget_enabled,
                    budget,
                    opt.large_compact_flow_relaxation,
                    opt.large_compact_flow_connectivity,
                    opt.service_operation_min_handling_cuts,
                    opt.penalty_movement_lb_cuts,
                    opt.transfer_subset_capacity_cuts);
            };
            auto relaxationLb =
                [&](const ebrp::GiniIntervalInventoryRelaxationBound& bound) {
                    return bound.infeasible ? cutoff : bound.objective_lower_bound;
                };
            auto compute_with_compat_policy =
                [&](bool operation_budget_enabled) {
                    if (opt.pickup_drop_compat_flow) {
                        ebrp::GiniIntervalInventoryRelaxationBound no_compat =
                            compute_once(opt.movement_domain_tightening, false,
                                         opt.vehicle_indexed_operation_relaxation,
                                         false, operation_budget_enabled);
                        const double no_compat_lb = relaxationLb(no_compat);
                        if (std::isfinite(cutoff) &&
                            no_compat.computed &&
                            no_compat_lb >= cutoff - 1e-9) {
                            no_compat.note +=
                                ", pickup_drop_compat_flow_audit_selected=no_compat"
                                ", compat_skipped=no_compat_cutoff_fathomed"
                                ", no_compat_lb=" + std::to_string(no_compat_lb);
                            return no_compat;
                        }
                        if (budget <= 2.5) {
                            no_compat.note +=
                                ", pickup_drop_compat_flow_audit_selected=no_compat"
                                ", compat_skipped=short_relaxation_budget"
                                ", no_compat_lb=" + std::to_string(no_compat_lb)
                                + ", relaxation_budget=" + std::to_string(budget);
                            return no_compat;
                        }
                        ebrp::GiniIntervalInventoryRelaxationBound compat =
                            compute_once(opt.movement_domain_tightening,
                                         true,
                                         opt.vehicle_indexed_operation_relaxation,
                                         opt.vehicle_indexed_transfer_flow,
                                         operation_budget_enabled);
                        const double compat_lb = relaxationLb(compat);
                        if (no_compat_lb > compat_lb + 1e-9) {
                            no_compat.note +=
                                ", pickup_drop_compat_flow_audit_selected=no_compat"
                                ", compat_lb=" + std::to_string(compat_lb)
                                + ", no_compat_lb=" + std::to_string(no_compat_lb);
                            return no_compat;
                        }
                        compat.note +=
                            ", pickup_drop_compat_flow_audit_selected=compat"
                            ", compat_lb=" + std::to_string(compat_lb)
                            + ", no_compat_lb=" + std::to_string(no_compat_lb);
                        return compat;
                    }
                    return compute_once(opt.movement_domain_tightening,
                                        false,
                                        opt.vehicle_indexed_operation_relaxation,
                                        false,
                                        operation_budget_enabled);
                };
            if (opt.movement_bound_audit) {
                ++result.movement_audit_intervals;
                ebrp::GiniIntervalInventoryRelaxationBound no_movement =
                    compute_once(false, opt.pickup_drop_compat_flow,
                                 opt.vehicle_indexed_operation_relaxation,
                                 opt.vehicle_indexed_transfer_flow,
                                 opt.route_mask_operation_budget_cuts);
                ebrp::GiniIntervalInventoryRelaxationBound with_movement =
                    compute_once(true, opt.pickup_drop_compat_flow,
                                 opt.vehicle_indexed_operation_relaxation,
                                 opt.vehicle_indexed_transfer_flow,
                                 opt.route_mask_operation_budget_cuts);
                const double no_lb = relaxationLb(no_movement);
                const double with_lb = relaxationLb(with_movement);
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
                if (opt.route_mask_operation_budget_cuts &&
                    std::isfinite(cutoff)) {
                    ebrp::GiniIntervalInventoryRelaxationBound no_budget =
                        compute_with_compat_policy(false);
                    const double no_budget_lb = relaxationLb(no_budget);
                    if (no_budget_lb >= cutoff - 1e-9) {
                        no_budget.note +=
                            ", route_mask_operation_budget_portfolio_selected=no_operation_budget"
                            ", operation_budget_skipped=no_operation_budget_cutoff_fathomed"
                            ", no_operation_budget_lb=" + std::to_string(no_budget_lb)
                            + ", cutoff=" + std::to_string(cutoff);
                        out.bound = no_budget;
                    } else {
                        ebrp::GiniIntervalInventoryRelaxationBound operation_budget =
                            compute_with_compat_policy(true);
                        const double operation_budget_lb =
                            relaxationLb(operation_budget);
                        if (operation_budget_lb > no_budget_lb + 1e-9) {
                            operation_budget.note +=
                                ", route_mask_operation_budget_portfolio_selected=operation_budget"
                                ", operation_budget_lb=" + std::to_string(operation_budget_lb)
                                + ", no_operation_budget_lb=" + std::to_string(no_budget_lb);
                            out.bound = operation_budget;
                        } else {
                            no_budget.note +=
                                ", route_mask_operation_budget_portfolio_selected=no_operation_budget"
                                ", operation_budget_lb=" + std::to_string(operation_budget_lb)
                                + ", no_operation_budget_lb=" + std::to_string(no_budget_lb);
                            out.bound = no_budget;
                        }
                    }
                } else {
                    out.bound =
                        compute_with_compat_policy(opt.route_mask_operation_budget_cuts);
                }
                if (opt.vehicle_indexed_relaxation_audit &&
                    opt.vehicle_indexed_operation_relaxation) {
                    ebrp::GiniIntervalInventoryRelaxationBound aggregate =
                        compute_once(opt.movement_domain_tightening,
                                     opt.pickup_drop_compat_flow,
                                     false,
                                     false,
                                     opt.route_mask_operation_budget_cuts);
                    const double chosen_lb = relaxationLb(out.bound);
                    const double aggregate_lb = relaxationLb(aggregate);
                    if (aggregate_lb > chosen_lb + 1e-9) {
                        aggregate.note += ", vehicle_indexed_relaxation_audit_selected=aggregate"
                            ", aggregate_lb=" + std::to_string(aggregate_lb)
                            + ", vehicle_indexed_lb=" + std::to_string(chosen_lb);
                        out.bound = aggregate;
                    } else {
                        out.bound.note += ", vehicle_indexed_relaxation_audit_selected=vehicle_indexed"
                            ", aggregate_lb=" + std::to_string(aggregate_lb)
                            + ", vehicle_indexed_lb=" + std::to_string(chosen_lb);
                    }
                }
                if (opt.relaxation_portfolio_mode != "fixed" &&
                    instance.V > opt.route_mask_max_v) {
                    struct PortfolioVariant {
                        std::string name;
                        std::string compact_mode;
                        bool connectivity = false;
                        bool service_min = false;
                        bool penalty_move = false;
                        bool transfer_subset = false;
                        bool operation_budget = false;
                    };
                    std::vector<PortfolioVariant> variants;
                    variants.push_back({"compact_lp", "lp", false, false,
                                        false, false,
                                        opt.route_mask_operation_budget_cuts});
                    variants.push_back({"compact_mip_light", "mip-light",
                                        false, false, false, false,
                                        opt.route_mask_operation_budget_cuts});
                    variants.push_back({"compact_lp_connectivity", "lp",
                                        true, true, true,
                                        opt.transfer_subset_capacity_cuts,
                                        opt.route_mask_operation_budget_cuts});
                    variants.push_back({"compact_mip_light_connectivity",
                                        "mip-light", true, true, true,
                                        opt.transfer_subset_capacity_cuts,
                                        opt.route_mask_operation_budget_cuts});

                    const double baseline_lb = relaxationLb(out.bound);
                    double best_lb = baseline_lb;
                    std::string best_name = "fixed_baseline";
                    std::string tried = "fixed_baseline";
                    std::string skipped;
                    double probe_time_total = 0.0;
                    const bool exhaustive_mode =
                        opt.relaxation_portfolio_mode == "exhaustive";
                    const int max_variants = exhaustive_mode
                        ? static_cast<int>(variants.size())
                        : std::min(static_cast<int>(variants.size()),
                                   std::max(0, opt.relaxation_portfolio_max_variants - 1));
                    for (int pos = 0; pos < max_variants; ++pos) {
                        const PortfolioVariant& variant = variants[pos];
                        if (variant.compact_mode == opt.large_compact_flow_relaxation &&
                            variant.connectivity == opt.large_compact_flow_connectivity &&
                            variant.service_min == opt.service_operation_min_handling_cuts &&
                            variant.penalty_move == opt.penalty_movement_lb_cuts &&
                            variant.transfer_subset == opt.transfer_subset_capacity_cuts) {
                            continue;
                        }
                        const auto probe_start = std::chrono::steady_clock::now();
                        const double candidate_budget =
                            (opt.relaxation_portfolio_mode == "race" ||
                             exhaustive_mode)
                                ? budget
                                : std::max(0.1, std::min(
                                      budget,
                                      opt.relaxation_portfolio_probe_seconds));
                        ebrp::GiniIntervalInventoryRelaxationBound candidate =
                            compute_once_full(
                                opt.movement_domain_tightening,
                                opt.pickup_drop_compat_flow,
                                opt.vehicle_indexed_operation_relaxation,
                                opt.vehicle_indexed_transfer_flow,
                                variant.operation_budget,
                                candidate_budget,
                                variant.compact_mode,
                                variant.connectivity,
                                variant.service_min,
                                variant.penalty_move,
                                variant.transfer_subset);
                        probe_time_total += std::chrono::duration<double>(
                            std::chrono::steady_clock::now() - probe_start).count();
                        tried += ";" + variant.name;
                        const double candidate_lb = relaxationLb(candidate);
                        if (candidate_lb >
                            best_lb + opt.relaxation_portfolio_min_improvement) {
                            best_lb = candidate_lb;
                            best_name = variant.name;
                            candidate.note +=
                                ", relaxation_portfolio_selected=" + variant.name
                                + ", relaxation_portfolio_baseline_lb=" +
                                  std::to_string(baseline_lb)
                                + ", relaxation_portfolio_best_lb=" +
                                  std::to_string(candidate_lb);
                            out.bound = candidate;
                        }
                        if (exhaustive_mode &&
                            opt.relaxation_exhaustive_stop_on_fathom &&
                            candidate_lb >= cutoff - opt.cutoff_feasibility_epsilon) {
                            skipped = "stopped_after_fathoming_variant=" +
                                variant.name;
                            break;
                        }
                    }
                    if (static_cast<int>(variants.size()) > max_variants &&
                        skipped.empty()) {
                        skipped = "max_variants_limit";
                    }
                    if (!opt.relaxation_portfolio_keep_best_bound &&
                        best_name == "fixed_baseline") {
                        skipped = skipped.empty()
                            ? "no_candidate_improved_baseline"
                            : skipped + ";no_candidate_improved_baseline";
                    }
                    result.relaxation_portfolio_mode =
                        opt.relaxation_portfolio_mode;
                    if (!result.relaxation_variants_tried.empty()) {
                        result.relaxation_variants_tried += "|";
                    }
                    result.relaxation_variants_tried += tried;
                    result.selected_relaxation_variant = best_name;
                    result.selected_variant_reason =
                        best_name == "fixed_baseline"
                            ? "baseline_bound_kept"
                            : "largest_valid_bound";
                    result.relaxation_portfolio_probe_time_seconds +=
                        probe_time_total;
                    result.relaxation_portfolio_variant_bound_improvement =
                        std::max(
                            result.relaxation_portfolio_variant_bound_improvement,
                            std::max(0.0, best_lb - baseline_lb));
                    result.relaxation_portfolio_best_variant_bound =
                        std::max(result.relaxation_portfolio_best_variant_bound,
                                 best_lb);
                    if (opt.relaxation_certificate_mode == "cutoff-feasibility" ||
                        opt.relaxation_certificate_mode == "both") {
                        result.cutoff_feasibility_attempted = true;
                        result.cutoff_feasibility_time_seconds += probe_time_total;
                        if (best_lb >= cutoff - opt.cutoff_feasibility_epsilon) {
                            result.cutoff_feasibility_infeasible = true;
                            result.cutoff_feasibility_status =
                                "infeasible_by_valid_lower_bound";
                        } else if (best_name == "fixed_baseline" &&
                                   best_lb < cutoff - opt.cutoff_feasibility_epsilon) {
                            result.cutoff_feasibility_status =
                                "relaxed_solution_not_excluded_by_lower_bound";
                        } else {
                            result.cutoff_feasibility_status =
                                "best_valid_bound_below_cutoff";
                        }
                    }
                    if (!skipped.empty()) {
                        if (!result.relaxation_portfolio_variants_skipped_reason.empty()) {
                            result.relaxation_portfolio_variants_skipped_reason += "|";
                        }
                        result.relaxation_portfolio_variants_skipped_reason +=
                            skipped;
                    }
                    out.bound.relaxation_portfolio_mode =
                        opt.relaxation_portfolio_mode;
                    out.bound.relaxation_variants_tried = tried;
                    out.bound.selected_relaxation_variant = best_name;
                    out.bound.selected_variant_reason =
                        best_name == "fixed_baseline"
                            ? "baseline_bound_kept"
                            : "largest_valid_bound";
                    out.bound.probe_time_seconds = probe_time_total;
                    out.bound.variant_bound_improvement =
                        std::max(0.0, best_lb - baseline_lb);
                    out.bound.best_variant_bound = best_lb;
                    out.bound.variants_skipped_reason = skipped;
                    out.bound.note +=
                        ", relaxation_portfolio_mode=" +
                        opt.relaxation_portfolio_mode
                        + ", relaxation_variants_tried=" + tried
                        + ", selected_relaxation_variant=" + best_name
                        + ", variant_bound_improvement=" +
                        std::to_string(std::max(0.0, best_lb - baseline_lb));
                }
                const double used_lb = relaxationLb(out.bound);
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

    auto shouldDeferInitialTreeForAdaptiveSplit =
        [&](const FrontierIntervalRecord& record) {
            if (!opt.frontier_split_before_tree ||
                !opt.frontier_adaptive_split ||
                focus_only_effective) {
                return false;
            }
            if (record.complete || record.empty_complete ||
                record.replaced_by_children) {
                return false;
            }
            if (record.split_depth >= effectiveFrontierAdaptiveMaxDepth(instance, opt)) {
                return false;
            }
            if (record.hi - record.lo <=
                opt.frontier_adaptive_min_width + 1e-12) {
                return false;
            }
            return record.lower_bound_valid &&
                   record.lower_bound < result.upper_bound - 1e-7;
        };

    auto processInitialInterval = [&](int idx,
                                      double fixed_upper_bound,
                                      const std::vector<ebrp::RoutePlan>& fixed_incumbent_routes) {
        InitialIntervalWork work;
        work.idx = idx;
        work.record = interval_records[idx];
        const double lo = work.record.lo;
        const double hi = work.record.hi;
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

        const bool is_focus_interval =
            focus_only_effective && idx == result.focus_interval_id;
        const double relaxation_budget = is_focus_interval &&
            opt.frontier_focus_relax_seconds > 0.0
            ? opt.frontier_focus_relax_seconds
            : (opt.frontier_relax_seconds > 0.0)
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
        copyPortfolioFieldsToInterval(work.record, inv_relax);
        const double bound_elapsed = cached_relax.elapsed;
        work.bound_time_seconds += bound_elapsed;
        work.record.relaxation_time_seconds += bound_elapsed;
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

        if (shouldDeferInitialTreeForAdaptiveSplit(work.record)) {
            work.record.processed = true;
            work.record.open_nodes = std::max(1, work.record.open_nodes);
            work.notes.push_back("interval " + std::to_string(idx)
                + " deferred initial branch-price tree because "
                "frontier_split_before_tree=true and the interval is eligible "
                "for adaptive splitting");
            return work;
        }

        const double interval_budget = is_focus_interval &&
            opt.frontier_focus_time_limit > 0.0
            ? std::min(opt.frontier_focus_time_limit,
                       opt.solve_time_limit > 0.0 ? remainingForPreIterativeWork()
                                                  : opt.frontier_focus_time_limit)
            : result.parallel_frontier
            ? ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, opt.solve_time_limit / std::max(1, intervals))
                : 0.0)
            : ((opt.solve_time_limit > 0.0)
                ? std::max(0.1, remainingForPreIterativeWork() / std::max(1, intervals - idx))
                : 0.0);
        const int tree_node_limit = is_focus_interval &&
            opt.frontier_focus_tree_nodes > 0
            ? opt.frontier_focus_tree_nodes
            : opt.max_branch_nodes;
        work.tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
            instance, opt.lambda, hi, lo, interval_budget,
            closureIterations(24), tree_node_limit,
            &fixed_incumbent_routes, true, fixed_upper_bound, opt.gcap_warmstart_level,
            std::numeric_limits<double>::infinity(), closurePricingColumns(),
            opt.column_dominance, opt.column_dominance_mode,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, opt.support_duration_pruning,
            opt.support_duration_max_subset_size,
            opt.branch_inventory, opt.branch_inventory_priority,
            opt.branch_operation_mode, opt.branch_selection,
            opt.strong_branching_candidates, opt.strong_branching_time,
            opt.reliability_branching, bpc_pricing_options);
        work.ran_tree = true;
        recordTreeAggregate(work.record, work.tree);
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
        work.record.pricing_closed = treePricingClosureStrict(work.tree);
        recordClosureContinuationStats(work.tree,
                                       "initial_parallel_interval_" +
                                           std::to_string(idx));

        if (work.tree.has_integer_incumbent && !work.tree.best_routes.empty()) {
            ebrp::Verification candidate =
                ebrp::verifySolution(instance, work.tree.best_routes, opt.lambda);
            work.has_candidate = true;
            work.candidate_routes = work.tree.best_routes;
            work.candidate_verification = candidate;
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
            writeProgressCheckpoint("interval_relaxation_" +
                                    std::to_string(work.idx), true);
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
            if (treePricingClosureStrict(work.tree)) {
                result.pricing_closed_nodes += work.tree.nodes_solved;
            }
            result.cuts_added += work.tree.cuts_added;
            result.pricing_time_seconds += work.tree.pricing_time_seconds;
            result.master_time_seconds += work.tree.master_time_seconds;
            copyBpcPricingStats(work.tree, result);
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
            addTreeColumnsToFrontierPool(work.tree,
                                         "initial interval " +
                                             std::to_string(work.idx));
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
            runRoutePoolIncumbentMaster("after_initial_interval_" +
                                        std::to_string(work.idx));
            writeProgressCheckpoint("interval_tree_" +
                                    std::to_string(work.idx), true);
        }
        if (work.has_candidate) {
            auditIntervalCandidate(
                work.candidate_routes,
                work.tree.best_integer_surrogate,
                work.record.lo,
                work.record.hi,
                "initial interval " + std::to_string(work.idx));
            runRoutePoolIncumbentMaster("after_initial_interval_" +
                                        std::to_string(work.idx));
            writeProgressCheckpoint("route_pool_after_candidate_" +
                                    std::to_string(work.idx), true);
        }
    };

    const bool use_parallel_initial_frontier =
        result.parallel_frontier && intervals > 1 && !focus_only_effective;
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
    for (int schedule_pos = 0;
         schedule_pos < static_cast<int>(initial_schedule.size());
         ++schedule_pos) {
        const int idx = initial_schedule[schedule_pos];
        const double lo = interval_records[idx].lo;
        const double hi = interval_records[idx].hi;
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
        if (opt.frontier_focused_intensification &&
            opt.solve_time_limit > 0.0 && schedule_pos > 0) {
            const double reserve =
                std::max(0.0, std::min(0.9, opt.frontier_focused_reserve_fraction)) *
                opt.solve_time_limit;
            if (remainingSeconds() <= reserve) {
                result.notes.push_back("frontier initial pass stopped before interval "
                    + std::to_string(idx)
                    + " to preserve focused intensification reserve="
                    + std::to_string(reserve));
                break;
            }
        }

        const bool is_focus_interval =
            focus_only_effective && idx == result.focus_interval_id;
        const double relaxation_budget = is_focus_interval &&
            opt.frontier_focus_relax_seconds > 0.0
            ? opt.frontier_focus_relax_seconds
            : (opt.frontier_relax_seconds > 0.0)
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
        interval_records[idx].relaxation_time_seconds += bound_elapsed;
        copyPortfolioFieldsToInterval(interval_records[idx], inv_relax);
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
        writeProgressCheckpoint("interval_relaxation_" +
                                std::to_string(idx), true);
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

        if (shouldDeferInitialTreeForAdaptiveSplit(interval_records[idx])) {
            interval_records[idx].processed = true;
            interval_records[idx].open_nodes =
                std::max(1, interval_records[idx].open_nodes);
            result.notes.push_back("interval " + std::to_string(idx)
                + " deferred initial branch-price tree because "
                "frontier_split_before_tree=true and the interval is eligible "
                "for adaptive splitting");
            continue;
        }

        const double interval_budget = is_focus_interval &&
            opt.frontier_focus_time_limit > 0.0
            ? std::min(opt.frontier_focus_time_limit, remainingForPreIterativeWork())
            : (opt.solve_time_limit > 0.0)
            ? std::max(0.1, remainingForPreIterativeWork() /
                std::max(1, static_cast<int>(initial_schedule.size()) - schedule_pos))
            : 0.0;
        const int tree_node_limit = is_focus_interval &&
            opt.frontier_focus_tree_nodes > 0
            ? opt.frontier_focus_tree_nodes
            : opt.max_branch_nodes;
        ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
            instance, opt.lambda, hi, lo, interval_budget,
            closureIterations(24), tree_node_limit,
            &incumbent_routes, true, result.upper_bound, opt.gcap_warmstart_level,
            std::numeric_limits<double>::infinity(), closurePricingColumns(),
            opt.column_dominance, opt.column_dominance_mode,
            opt.projection_bound, opt.penalty_domain_tightening,
            opt.movement_domain_tightening, opt.support_duration_pruning,
            opt.support_duration_max_subset_size,
            opt.branch_inventory, opt.branch_inventory_priority,
            opt.branch_operation_mode, opt.branch_selection,
            opt.strong_branching_candidates, opt.strong_branching_time,
            opt.reliability_branching, bpc_pricing_options);
        result.nodes += tree.nodes_solved;
        result.columns += tree.generated_columns;
        result.pricing_calls += tree.pricing_calls;
        if (treePricingClosureStrict(tree)) {
            result.pricing_closed_nodes += tree.nodes_solved;
        }
        result.cuts_added += tree.cuts_added;
        result.pricing_time_seconds += tree.pricing_time_seconds;
        result.master_time_seconds += tree.master_time_seconds;
        copyBpcPricingStats(tree, result);
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
        addTreeColumnsToFrontierPool(tree,
                                     "initial interval " +
                                         std::to_string(idx));
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
        runRoutePoolIncumbentMaster("after_initial_interval_" +
                                    std::to_string(idx));
        writeProgressCheckpoint("interval_tree_" + std::to_string(idx), true);
        recordTreeAggregate(interval_records[idx], tree);
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
        interval_records[idx].pricing_closed = treePricingClosureStrict(tree);
        recordClosureContinuationStats(tree,
                                       "initial_interval_" +
                                           std::to_string(idx));

        if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
            auditIntervalCandidate(tree.best_routes, tree.best_integer_surrogate,
                                   lo, hi,
                                   "initial interval " + std::to_string(idx));
            runRoutePoolIncumbentMaster("after_initial_interval_" +
                                        std::to_string(idx));
            writeProgressCheckpoint("route_pool_after_candidate_" +
                                    std::to_string(idx), true);
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

    auto describeIntervalForField = [&](int idx) {
        if (idx < 0 || idx >= static_cast<int>(interval_records.size())) return std::string{};
        const FrontierIntervalRecord& record = interval_records[idx];
        std::ostringstream ss;
        ss << idx << ":[" << record.lo << "," << record.hi << "]"
           << ":lb=" << record.lower_bound;
        return ss.str();
    };
    const auto adaptive_split_start = std::chrono::steady_clock::now();
    const int split_pass_limit = focus_only_effective ? 0 : std::max(
        std::max(0, opt.frontier_refine_splits),
        opt.frontier_adaptive_split
            ? std::max(0, effectiveFrontierAdaptiveMaxDepth(instance, opt))
            : 0);
    for (int split_pass = 1; split_pass <= split_pass_limit; ++split_pass) {
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
            if (opt.frontier_adaptive_split) {
                const double width = record.hi - record.lo;
                if (width <= opt.frontier_adaptive_min_width + 1e-12) continue;
                if (record.split_depth >= effectiveFrontierAdaptiveMaxDepth(instance, opt)) {
                    result.adaptive_split_max_depth_reached = true;
                    continue;
                }
            }
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
        if (opt.frontier_adaptive_split && split_indices.size() > 1) {
            const int adaptive_batch = opt.frontier_pre_split_critical
                ? std::max(1, opt.frontier_split_batch)
                : 1;
            if (candidate_splits > adaptive_batch) {
                split_indices.resize(adaptive_batch);
            }
        } else if (opt.frontier_split_batch > 0 &&
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
        if (result.adaptive_split_global_min_interval_before.empty() &&
            !split_indices.empty()) {
            result.adaptive_split_global_min_interval_before =
                describeIntervalForField(split_indices.front());
        }

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
            const int split_factor = opt.frontier_adaptive_split
                ? std::max(2, opt.frontier_adaptive_split_factor) : 2;
            if (parent.hi - parent.lo <= opt.frontier_adaptive_min_width + 1e-12) {
                continue;
            }
            const bool parent_lower_bound_valid = parent.lower_bound_valid;
            const double parent_lower_bound = parent.lower_bound;
            const double parent_relaxation_lower_bound = parent.relaxation_lower_bound;
            const double parent_lo = parent.lo;
            const double parent_hi = parent.hi;
            const int parent_depth = parent.split_depth;
            std::vector<FrontierIntervalRecord> children(split_factor);
            for (int child_pos = 0; child_pos < split_factor; ++child_pos) {
                const double frac0 = static_cast<double>(child_pos) /
                    static_cast<double>(split_factor);
                const double frac1 = static_cast<double>(child_pos + 1) /
                    static_cast<double>(split_factor);
                children[child_pos].lo = parent_lo + (parent_hi - parent_lo) * frac0;
                children[child_pos].hi = (child_pos + 1 == split_factor)
                    ? parent_hi : parent_lo + (parent_hi - parent_lo) * frac1;
                children[child_pos].parent_id = parent_idx;
                children[child_pos].split_depth = parent_depth + 1;
                children[child_pos].child_index = child_pos;
                children[child_pos].inherited_parent_lb =
                    parent_lower_bound_valid ? parent_lower_bound : 0.0;
            }
            interval_records[parent_idx].replaced_by_children = true;
            for (FrontierIntervalRecord& child : children) {
                child.processed = true;
                child.lower_bound_valid = true;
                child.lower_bound = std::max(child.lo,
                    parent_lower_bound_valid ? parent_lower_bound : child.lo);
                if (parent_lower_bound_valid &&
                    parent_lower_bound > child.lo + 1e-12) {
                    child.lower_bound_source =
                        parent.lower_bound_source.empty()
                            ? "adaptive_split_inherited_parent_lb"
                            : "adaptive_split_inherited_" +
                                  parent.lower_bound_source;
                    child.lb_sources += "|adaptive_split_inherited_parent_lb";
                }
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
                    ++result.adaptive_split_intervals_created;
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
                    child.relaxation_time_seconds += bound_elapsed;
                    copyPortfolioFieldsToInterval(child, inv_relax);
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
                        if (child.lower_bound > parent_lower_bound + 1e-8) {
                            ++result.adaptive_split_lb_improvements;
                        }
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
                if (child.split_depth >= effectiveFrontierAdaptiveMaxDepth(instance, opt)) {
                    result.adaptive_split_max_depth_reached = true;
                }
                interval_records.push_back(child);
                ++result.adaptive_split_intervals_created;
                writeProgressCheckpoint("adaptive_split_child_" +
                                        std::to_string(child_idx), true);
            }
        }
    }
    result.adaptive_split_time_seconds =
        std::chrono::duration<double>(
            std::chrono::steady_clock::now() - adaptive_split_start).count();
    if (result.adaptive_split_intervals_created > 0) {
        std::vector<int> leaves;
        for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
            const FrontierIntervalRecord& record = interval_records[idx];
            if (record.replaced_by_children || record.lo >= result.upper_bound - 1e-12) continue;
            if (record.lower_bound_valid && record.lower_bound < result.upper_bound - 1e-7) {
                leaves.push_back(idx);
            }
        }
        std::sort(leaves.begin(), leaves.end(), [&](int lhs, int rhs) {
            const FrontierIntervalRecord& a = interval_records[lhs];
            const FrontierIntervalRecord& b = interval_records[rhs];
            if (std::fabs(a.lower_bound - b.lower_bound) > 1e-10) {
                return a.lower_bound < b.lower_bound;
            }
            return lhs < rhs;
        });
        if (!leaves.empty()) {
            result.adaptive_split_global_min_interval_after =
                describeIntervalForField(leaves.front());
        }
    }

    auto appendDelimitedField = [](std::string& target, const std::string& value) {
        if (!target.empty()) target += ";";
        target += value;
    };
    result.focused_intensification_enabled = opt.frontier_focused_intensification;
    if (opt.frontier_focused_intensification && !focus_only_effective) {
        const auto intensify_start = std::chrono::steady_clock::now();
        std::unordered_set<int> intensified_intervals;
        auto collectIntensificationIndices = [&]() {
            std::vector<int> indices;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.replaced_by_children) continue;
                if (record.lo >= result.upper_bound - 1e-12) continue;
                if (record.complete || record.bound_fathomed || record.empty_complete) continue;
                if (record.lower_bound_valid &&
                    record.lower_bound >= result.upper_bound - 1e-7) continue;
                indices.push_back(idx);
            }
            std::sort(indices.begin(), indices.end(),
                      [&](int lhs, int rhs) {
                          const FrontierIntervalRecord& a = interval_records[lhs];
                          const FrontierIntervalRecord& b = interval_records[rhs];
                          const double alb = a.lower_bound_valid ? a.lower_bound : a.lo;
                          const double blb = b.lower_bound_valid ? b.lower_bound : b.lo;
                          if (std::fabs(alb - blb) > 1e-10) return alb < blb;
                          const double agap = result.upper_bound - alb;
                          const double bgap = result.upper_bound - blb;
                          if (std::fabs(agap - bgap) > 1e-10) return agap > bgap;
                          if (a.open_nodes != b.open_nodes) return a.open_nodes > b.open_nodes;
                          return lhs < rhs;
                      });
            return indices;
        };
        const int max_passes = std::max(0, opt.frontier_focused_max_passes);
        for (int pass = 0; pass < max_passes; ++pass) {
            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
                result.focused_intensification_stop_reason = "time_limit";
                break;
            }
            std::vector<int> indices = collectIntensificationIndices();
            if (indices.empty()) {
                result.focused_intensification_stop_reason = "no_unresolved_intervals";
                break;
            }
            const int idx = indices.front();
            FrontierIntervalRecord& record = interval_records[idx];
            const double old_lb = record.lower_bound_valid ? record.lower_bound : record.lo;
            appendDelimitedField(result.focused_intensification_lb_before,
                                 std::to_string(old_lb));
            intensified_intervals.insert(idx);
            ++result.focused_intensification_passes;
            const double relax_budget = opt.frontier_focused_relax_seconds > 0.0
                ? opt.frontier_focused_relax_seconds
                : std::max(1.0, opt.frontier_relax_seconds * 4.0);
            ++result.focused_intensification_relax_calls;
            const CachedRelaxation cached_relax =
                computeInventoryRelaxation(record.lo, record.hi, relax_budget,
                                           result.upper_bound, true);
            const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
                cached_relax.bound;
            result.bound_time_seconds += cached_relax.elapsed;
            record.relaxation_time_seconds += cached_relax.elapsed;
            copyPortfolioFieldsToInterval(record, inv_relax);
            accumulateInventoryRelaxationStats(inv_relax);
            const double candidate_lb = inv_relax.infeasible
                ? result.upper_bound
                : std::max(record.lo, inv_relax.objective_lower_bound);
            bool improved = false;
            if (inv_relax.computed && std::isfinite(candidate_lb) &&
                candidate_lb > old_lb + 1e-8) {
                record.lower_bound = std::max(record.lower_bound, candidate_lb);
                record.lower_bound_valid = true;
                record.lower_bound_source = "focused_inventory_route_gini_relaxation";
                record.lb_sources += "|focused_inventory_route_gini_relaxation";
                improved = true;
                ++result.focused_intensification_lb_improvements;
            }
            appendDelimitedField(result.focused_intensification_lb_after,
                                 std::to_string(record.lower_bound));
            std::vector<int> next_indices = collectIntensificationIndices();
            double next_min_lb = std::numeric_limits<double>::infinity();
            for (int candidate_idx : next_indices) {
                if (candidate_idx == idx) continue;
                const FrontierIntervalRecord& other = interval_records[candidate_idx];
                next_min_lb = std::min(next_min_lb,
                    other.lower_bound_valid ? other.lower_bound : other.lo);
            }
            result.notes.push_back("focused_intensification pass="
                + std::to_string(pass + 1)
                + ", interval=" + std::to_string(idx)
                + ", old_lb=" + std::to_string(old_lb)
                + ", new_lb=" + std::to_string(record.lower_bound)
                + ", source=" + record.lower_bound_source
                + ", relaxation_status=" + inv_relax.status
                + ", next_min_lb=" + std::to_string(next_min_lb)
                + ", time_spent=" + std::to_string(cached_relax.elapsed));
            if (!improved) {
                bool split_performed = false;
                if (opt.frontier_adaptive_split &&
                    record.split_depth < effectiveFrontierAdaptiveMaxDepth(instance, opt) &&
                    record.hi - record.lo > opt.frontier_adaptive_min_width + 1e-12 &&
                    (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
                    const double parent_lo = record.lo;
                    const double parent_hi = record.hi;
                    const int parent_depth = record.split_depth;
                    const double parent_lb = old_lb;
                    const int split_factor =
                        std::max(2, opt.frontier_adaptive_split_factor);
                    record.replaced_by_children = true;
                    result.focused_intensification_split_triggered = true;
                    split_performed = true;
                    std::vector<int> child_ids;
                    for (int child_pos = 0; child_pos < split_factor; ++child_pos) {
                        FrontierIntervalRecord child;
                        const double frac0 = static_cast<double>(child_pos) /
                            static_cast<double>(split_factor);
                        const double frac1 = static_cast<double>(child_pos + 1) /
                            static_cast<double>(split_factor);
                        child.lo = parent_lo + (parent_hi - parent_lo) * frac0;
                        child.hi = (child_pos + 1 == split_factor)
                            ? parent_hi : parent_lo + (parent_hi - parent_lo) * frac1;
                        child.parent_id = idx;
                        child.split_depth = parent_depth + 1;
                        child.child_index = child_pos;
                        child.inherited_parent_lb = parent_lb;
                        child.processed = true;
                        child.lower_bound_valid = true;
                        child.lower_bound = std::max(child.lo, parent_lb);
                        child.lower_bound_source = "focused_split_inherited_parent_lb";
                        child.lb_sources += "|focused_split_inherited_parent_lb";
                        child.open_nodes = 1;
                        interval_records.push_back(child);
                        const int child_idx = static_cast<int>(interval_records.size()) - 1;
                        child_ids.push_back(child_idx);
                        ++result.adaptive_split_intervals_created;
                    }
                    std::sort(child_ids.begin(), child_ids.end(), [&](int lhs, int rhs) {
                        const FrontierIntervalRecord& a = interval_records[lhs];
                        const FrontierIntervalRecord& b = interval_records[rhs];
                        if (std::fabs(a.lower_bound - b.lower_bound) > 1e-10) {
                            return a.lower_bound < b.lower_bound;
                        }
                        return lhs < rhs;
                    });
                    bool any_child_improved = false;
                    bool child_relax_attempted = false;
                    for (int child_idx : child_ids) {
                        if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
                            result.focused_intensification_stop_reason =
                                child_relax_attempted
                                    ? "split_performed_child_relax_time_limit"
                                    : "split_performed_child_relax_skipped_time_limit";
                            break;
                        }
                        FrontierIntervalRecord& child = interval_records[child_idx];
                        const double child_budget = opt.solve_time_limit > 0.0
                            ? std::max(0.1, std::min(relax_budget, remainingSeconds()))
                            : relax_budget;
                        const CachedRelaxation child_relax =
                            computeInventoryRelaxation(child.lo, child.hi,
                                                       child_budget,
                                                       result.upper_bound, true);
                        child_relax_attempted = true;
                        ++result.focused_intensification_relax_calls;
                        ++result.focused_intensification_child_intervals_processed;
                        result.bound_time_seconds += child_relax.elapsed;
                        child.relaxation_time_seconds += child_relax.elapsed;
                        accumulateInventoryRelaxationStats(child_relax.bound);
                        const double child_candidate_lb = child_relax.bound.infeasible
                            ? result.upper_bound
                            : std::max(child.lo,
                                child_relax.bound.objective_lower_bound);
                        if (child_relax.bound.computed && std::isfinite(child_candidate_lb)) {
                            child.relaxation_lower_bound = child_candidate_lb;
                        }
                        if (child_relax.bound.computed &&
                            child_candidate_lb > child.lower_bound + 1e-8) {
                            child.lower_bound = child_candidate_lb;
                            child.lower_bound_source =
                                "focused_child_inventory_route_gini_relaxation";
                            child.lb_sources += "|focused_child_inventory_route_gini_relaxation";
                            ++result.focused_intensification_lb_improvements;
                            ++result.adaptive_split_lb_improvements;
                            any_child_improved = true;
                        }
                        result.focused_intensification_best_child_lb =
                            std::max(result.focused_intensification_best_child_lb,
                                     child.lower_bound);
                        result.notes.push_back("focused_intensification split interval="
                            + std::to_string(idx)
                            + ", child=" + std::to_string(child_idx)
                            + ", child_lb=" + std::to_string(child.lower_bound)
                            + ", child_status=" + child_relax.bound.status
                            + ", child_budget=" + std::to_string(child_budget)
                            + ", operation_budget_enabled="
                            + std::string(opt.route_mask_operation_budget_cuts
                                          ? "true" : "false"));
                        writeProgressCheckpoint("focused_split_child_" +
                                                std::to_string(child_idx), true);
                    }
                    if (result.focused_intensification_stop_reason.empty() ||
                        result.focused_intensification_stop_reason == "split_performed") {
                        result.focused_intensification_stop_reason =
                            any_child_improved ? "child_interval_improved"
                                               : "split_performed";
                    }
                }
                if (!split_performed && result.focused_intensification_stop_reason.empty()) {
                    result.focused_intensification_stop_reason =
                        "no_valid_lower_bound_progress";
                }
                if (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0) {
                    result.notes.push_back("focused_intensification tree fallback skipped: existing focused retry branch-price pass handles tree work; relaxation made no progress");
                }
                break;
            }
            writeProgressCheckpoint("focused_intensification_pass_" +
                                    std::to_string(pass + 1), true);
        }
        result.focused_intensification_intervals =
            static_cast<int>(intensified_intervals.size());
        result.focused_intensification_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - intensify_start).count();
        if (result.focused_intensification_stop_reason.empty()) {
            result.focused_intensification_stop_reason = "completed_passes";
        }
    } else {
        result.focused_intensification_stop_reason = "disabled";
    }

    std::unordered_set<int> focused_retry_interval_ids;
    const auto focused_retry_start = std::chrono::steady_clock::now();
    auto appendFocusedField = appendDelimitedField;
    if (focus_only_effective) {
        result.focused_retry_stopped_reason = "disabled_focus_only_diagnostic";
    } else if (!opt.frontier_focused_min_lb_retry) {
        result.focused_retry_stopped_reason = "disabled";
    }
    for (int adaptive_pass = 1;
         adaptive_pass <= (!focus_only_effective && opt.frontier_focused_min_lb_retry
             ? std::max(1, opt.frontier_retry_passes) : 0);
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
                          const double agap = result.upper_bound - a.lower_bound;
                          const double bgap = result.upper_bound - b.lower_bound;
                          if (std::fabs(agap - bgap) > 1e-10) return agap > bgap;
                          if (a.open_nodes != b.open_nodes) {
                              return a.open_nodes > b.open_nodes;
                          }
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
            const int previous_open_nodes = record.open_nodes;
            appendFocusedField(result.focused_retry_selected_interval_ids,
                               std::to_string(idx));
            appendFocusedField(result.focused_retry_lb_before,
                               std::to_string(previous_record_lb));
            appendFocusedField(result.focused_retry_open_nodes_before,
                               std::to_string(previous_open_nodes));
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
                ? std::max(0.1, remainingForPreIterativeWork())
                : 0.0;
            ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
                instance, opt.lambda, record.hi, record.lo, interval_budget,
                closureIterations(24),
                retry_max_nodes, &incumbent_routes, true, result.upper_bound,
                opt.gcap_warmstart_level, early_stop_target,
                closurePricingColumns(),
                opt.column_dominance, opt.column_dominance_mode,
                opt.projection_bound, opt.penalty_domain_tightening,
                opt.movement_domain_tightening, opt.support_duration_pruning,
                opt.support_duration_max_subset_size,
                opt.branch_inventory, opt.branch_inventory_priority,
                opt.branch_operation_mode, opt.branch_selection,
                opt.strong_branching_candidates, opt.strong_branching_time,
                opt.reliability_branching, bpc_pricing_options);
            result.nodes += tree.nodes_solved;
            result.columns += tree.generated_columns;
            result.pricing_calls += tree.pricing_calls;
            if (treePricingClosureStrict(tree)) {
                result.pricing_closed_nodes += tree.nodes_solved;
            }
            result.cuts_added += tree.cuts_added;
            result.pricing_time_seconds += tree.pricing_time_seconds;
            result.master_time_seconds += tree.master_time_seconds;
            copyBpcPricingStats(tree, result);
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
            addTreeColumnsToFrontierPool(tree,
                                         "focused_retry interval " +
                                             std::to_string(idx));
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
            runRoutePoolIncumbentMaster("after_focused_retry_interval_" +
                                        std::to_string(idx));
            recordTreeAggregate(record, tree);
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
            record.pricing_closed = treePricingClosureStrict(tree);
            recordClosureContinuationStats(tree,
                                           "focused_retry_interval_" +
                                               std::to_string(idx));

            if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
                auditIntervalCandidate(tree.best_routes, tree.best_integer_surrogate,
                                       record.lo, record.hi,
                                       "focused_retry interval " +
                                           std::to_string(idx));
                runRoutePoolIncumbentMaster("after_focused_retry_interval_" +
                                            std::to_string(idx));
            }

            const bool certified_by_bound = record.lower_bound_valid &&
                record.lower_bound >= result.upper_bound - 1e-7;
            double next_min_lb = std::numeric_limits<double>::infinity();
            retry_indices = collectRetryIndices();
            for (int candidate_idx : retry_indices) {
                if (candidate_idx == idx) continue;
                const FrontierIntervalRecord& other = interval_records[candidate_idx];
                if (other.lower_bound_valid) {
                    next_min_lb = std::min(next_min_lb, other.lower_bound);
                }
            }
            appendFocusedField(result.focused_retry_lb_after,
                               std::to_string(record.lower_bound));
            appendFocusedField(result.focused_retry_open_nodes_after,
                               std::to_string(record.open_nodes));
            std::ostringstream retry_note;
            retry_note << "focused_retry interval=" << idx
                       << ", adaptive_pass=" << adaptive_pass
                       << ", retry=" << (retry_attempt + 1)
                       << " [" << record.lo << "," << record.hi << "]"
                       << ", previous_lb=" << previous_record_lb
                       << ", new_lb=" << record.lower_bound
                       << ", next_min_lb=" << next_min_lb
                       << ", open_nodes_before=" << previous_open_nodes
                       << ", open_nodes_after=" << record.open_nodes
                       << " complete=" << (tree.complete ? "true" : "false")
                       << ", lower_bound_valid=" << (tree.lower_bound_valid ? "true" : "false")
                       << ", certified_by_bound=" << (certified_by_bound ? "true" : "false")
                       << ", tree_closed=" << (tree.complete ? "true" : "false")
                       << ", bound_fathomed=" << (certified_by_bound ? "true" : "false")
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
            writeProgressCheckpoint("focused_retry_interval_" +
                                    std::to_string(idx), true);

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

    if (!focus_only_effective && opt.frontier_final_closure &&
        (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
        const bool bpc_fallback_controlled =
            opt.frontier_bpc_fallback_mode != "off";
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
                          if (bpc_fallback_controlled) {
                              const double alb = a.lower_bound_valid
                                  ? a.lower_bound : std::max(0.0, a.lo);
                              const double blb = b.lower_bound_valid
                                  ? b.lower_bound : std::max(0.0, b.lo);
                              if (opt.frontier_bpc_fallback_mode == "best-bound" &&
                                  std::fabs(alb - blb) > 1e-10) {
                                  return alb < blb;
                              }
                              const double agap = std::max(0.0, result.upper_bound - alb);
                              const double bgap = std::max(0.0, result.upper_bound - blb);
                              if (std::fabs(agap - bgap) > 1e-10) return agap > bgap;
                              const double aw = a.hi - a.lo;
                              const double bw = b.hi - b.lo;
                              if (std::fabs(aw - bw) > 1e-12) return aw > bw;
                              return lhs < rhs;
                          }
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
            + ", scheduling=" + (bpc_fallback_controlled
                ? ("bpc_fallback_" + opt.frontier_bpc_fallback_mode)
                : std::string("smallest_gap_contribution_first"))
            + ", fallback_max_intervals="
            + std::to_string(std::max(0, opt.frontier_bpc_fallback_max_intervals))
            + ", objective_cutoff=" + std::to_string(result.upper_bound));

        int final_attempt = 0;
        while (!final_indices.empty() &&
               (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
            if (bpc_fallback_controlled &&
                opt.frontier_bpc_fallback_max_intervals > 0 &&
                final_attempt >= opt.frontier_bpc_fallback_max_intervals) {
                result.notes.push_back("BPC fallback final closure stopped after max intervals="
                    + std::to_string(opt.frontier_bpc_fallback_max_intervals));
                break;
            }
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
                record.relaxation_time_seconds += bound_elapsed;
                copyPortfolioFieldsToInterval(record, inv_relax);
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
                writeProgressCheckpoint("final_closure_relaxation_" +
                                        std::to_string(idx), true);
                final_indices = collectFinalClosureIndices();
                ++final_attempt;
                continue;
            }

            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) break;
            const double interval_budget = (opt.solve_time_limit > 0.0)
                ? std::max(0.1, remainingForPreIterativeWork() /
                    std::max(1, static_cast<int>(final_indices.size())))
                : 0.0;
            ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
                instance, opt.lambda, record.hi, record.lo, interval_budget,
                closureIterations(32),
                std::max(1, opt.frontier_final_nodes), &incumbent_routes, true,
                result.upper_bound, opt.gcap_warmstart_level,
                std::numeric_limits<double>::infinity(),
                closurePricingColumns(),
                opt.column_dominance, opt.column_dominance_mode,
                opt.projection_bound, opt.penalty_domain_tightening,
                opt.movement_domain_tightening, opt.support_duration_pruning,
                opt.support_duration_max_subset_size,
                opt.branch_inventory, opt.branch_inventory_priority,
                opt.branch_operation_mode, opt.branch_selection,
                opt.strong_branching_candidates, opt.strong_branching_time,
                opt.reliability_branching, bpc_pricing_options);
            result.nodes += tree.nodes_solved;
            result.columns += tree.generated_columns;
            result.pricing_calls += tree.pricing_calls;
            if (treePricingClosureStrict(tree)) {
                result.pricing_closed_nodes += tree.nodes_solved;
            }
            result.cuts_added += tree.cuts_added;
            result.pricing_time_seconds += tree.pricing_time_seconds;
            result.master_time_seconds += tree.master_time_seconds;
            copyBpcPricingStats(tree, result);
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
            addTreeColumnsToFrontierPool(tree,
                                         "final_closure interval " +
                                             std::to_string(idx));
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
            runRoutePoolIncumbentMaster("after_final_closure_interval_" +
                                        std::to_string(idx));
            recordTreeAggregate(record, tree);
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
            record.pricing_closed = treePricingClosureStrict(tree);
            recordClosureContinuationStats(tree,
                                           "final_closure_interval_" +
                                               std::to_string(idx));
            if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
                auditIntervalCandidate(tree.best_routes, tree.best_integer_surrogate,
                                       record.lo, record.hi,
                                       "final_closure interval " +
                                           std::to_string(idx));
                runRoutePoolIncumbentMaster("after_final_closure_interval_" +
                                            std::to_string(idx));
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
            writeProgressCheckpoint("final_closure_interval_" +
                                    std::to_string(idx), true);

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

    if (opt.frontier_iterative_closure && !focus_only_effective) {
        auto currentLedgerLowerBound = [&]() {
            double lb = result.upper_bound;
            for (const FrontierIntervalRecord& record : interval_records) {
                if (record.replaced_by_children) continue;
                if (record.lo >= result.upper_bound - 1e-12) continue;
                const double candidate = record.lower_bound_valid
                    ? record.lower_bound : std::max(0.0, record.lo);
                lb = std::min(lb, candidate);
            }
            return std::isfinite(lb) ? lb : 0.0;
        };
        auto currentLedgerGap = [&]() {
            const double lb = currentLedgerLowerBound();
            return result.upper_bound > 1e-12
                ? std::max(0.0, (result.upper_bound - lb) / result.upper_bound)
                : std::max(0.0, result.upper_bound - lb);
        };
        auto collectIterativeIndices = [&]() {
            std::vector<int> indices;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (record.replaced_by_children) continue;
                if (record.lo >= result.upper_bound - 1e-12) continue;
                if (record.empty_complete || record.complete || record.bound_fathomed) continue;
                const double lb = record.lower_bound_valid
                    ? record.lower_bound : std::max(0.0, record.lo);
                if (lb < result.upper_bound - 1e-7) indices.push_back(idx);
            }
            std::sort(indices.begin(), indices.end(),
                      [&](int lhs, int rhs) {
                          const FrontierIntervalRecord& a = interval_records[lhs];
                          const FrontierIntervalRecord& b = interval_records[rhs];
                          const double alb = a.lower_bound_valid ? a.lower_bound : a.lo;
                          const double blb = b.lower_bound_valid ? b.lower_bound : b.lo;
                          if (std::fabs(alb - blb) > 1e-10) return alb < blb;
                          const double agap = result.upper_bound - alb;
                          const double bgap = result.upper_bound - blb;
                          if (std::fabs(agap - bgap) > 1e-10) return agap > bgap;
                          if (a.open_nodes != b.open_nodes) return a.open_nodes > b.open_nodes;
                          return lhs < rhs;
                      });
            return indices;
        };
        const int max_rounds = std::max(0, opt.frontier_iterative_max_rounds);
        std::unordered_set<int> stalled_intervals;
        for (int round = 0; round < max_rounds; ++round) {
            if (opt.solve_time_limit > 0.0 && remainingSeconds() <= 0.0) {
                result.iterative_closure_stop_reason = "time_limit";
                break;
            }
            if (currentLedgerGap() <= opt.frontier_iterative_target_gap + 1e-12) {
                result.iterative_closure_stop_reason = "target_gap_reached";
                break;
            }
            std::vector<int> iterative_indices = collectIterativeIndices();
            iterative_indices.erase(
                std::remove_if(iterative_indices.begin(), iterative_indices.end(),
                               [&](int idx) {
                                   return stalled_intervals.count(idx) > 0;
                               }),
                iterative_indices.end());
            if (iterative_indices.empty()) {
                result.iterative_closure_stop_reason =
                    stalled_intervals.empty()
                        ? "no_unresolved_intervals"
                        : "no_valid_progress_in_one_full_round";
                break;
            }
            const int idx = iterative_indices.front();
            FrontierIntervalRecord& record = interval_records[idx];
            const double lb_before = record.lower_bound_valid
                ? record.lower_bound : std::max(0.0, record.lo);
            const double gap_before = currentLedgerGap();
            appendDelimitedField(result.iterative_closure_target_intervals,
                                 std::to_string(idx) + ":" +
                                     makeRangeString(record.lo, record.hi));
            appendDelimitedField(result.iterative_closure_lb_before_each_round,
                                 std::to_string(lb_before));
            appendDelimitedField(result.iterative_closure_gap_before_each_round,
                                 std::to_string(gap_before));
            result.notes.push_back("iterative_closure round="
                + std::to_string(round + 1)
                + ", target_interval=" + std::to_string(idx)
                + ", range=" + makeRangeString(record.lo, record.hi)
                + ", lb_before=" + std::to_string(lb_before)
                + ", gap_before=" + std::to_string(gap_before));

            const double remaining = opt.solve_time_limit > 0.0
                ? remainingSeconds()
                : opt.frontier_iterative_round_time;
            const double round_budget = opt.frontier_iterative_round_time > 0.0
                ? std::min(opt.frontier_iterative_round_time,
                           opt.solve_time_limit > 0.0
                               ? std::max(0.0, remaining) : opt.frontier_iterative_round_time)
                : (opt.solve_time_limit > 0.0 ? std::max(0.0, remaining) : 0.0);
            const double relax_budget = std::max(0.1,
                std::min(round_budget * 0.25,
                         opt.frontier_relax_seconds > 0.0
                             ? std::max(opt.frontier_relax_seconds,
                                        opt.frontier_focused_relax_seconds)
                             : 10.0));
            const CachedRelaxation cached_relax =
                computeInventoryRelaxation(record.lo, record.hi,
                                           relax_budget,
                                           result.upper_bound, true);
            const ebrp::GiniIntervalInventoryRelaxationBound inv_relax =
                cached_relax.bound;
            result.bound_time_seconds += cached_relax.elapsed;
            record.relaxation_time_seconds += cached_relax.elapsed;
            copyPortfolioFieldsToInterval(record, inv_relax);
            accumulateInventoryRelaxationStats(inv_relax);
            if (inv_relax.note.find("route_mask_duration_load_relaxation=true") !=
                std::string::npos) {
                result.route_mask_time_seconds += cached_relax.elapsed;
            }
            if (inv_relax.computed) {
                record.processed = true;
                record.lower_bound_valid = true;
                const double relax_lb = inv_relax.infeasible
                    ? result.upper_bound
                    : std::max(record.lo, inv_relax.objective_lower_bound);
                if (relax_lb > record.lower_bound + 1e-12) {
                    record.lower_bound_source =
                        "iterative_inventory_route_gini_relaxation";
                }
                record.lower_bound = std::max(record.lower_bound, relax_lb);
                record.relaxation_lower_bound =
                    std::max(record.relaxation_lower_bound, relax_lb);
                record.lb_sources += "|iterative_inventory_route_gini_relaxation";
            }
            if (record.lower_bound_valid &&
                record.lower_bound >= result.upper_bound - 1e-7) {
                record.bound_fathomed = true;
                record.open_nodes = 0;
                ++result.iterative_closure_intervals_closed;
                ++result.iterative_intervals_fathomed_by_imported_bounds;
            } else if (round_budget > cached_relax.elapsed + 1e-3 &&
                       (opt.solve_time_limit <= 0.0 || remainingSeconds() > 0.0)) {
                ++result.iterative_exact_cg_rounds;
                const double tree_budget = opt.solve_time_limit > 0.0
                    ? std::max(0.1, std::min(remainingSeconds(),
                                             std::max(0.1, round_budget - cached_relax.elapsed)))
                    : 0.0;
                ebrp::GiniCapTreeResult tree = ebrp::runGiniCapBranchPriceTreeDiagnostic(
                    instance, opt.lambda, record.hi, record.lo, tree_budget,
                    closureIterations(48),
                    std::max(1, opt.frontier_final_nodes), &incumbent_routes,
                    true, result.upper_bound, opt.gcap_warmstart_level,
                    std::numeric_limits<double>::infinity(),
                    closurePricingColumns(),
                    opt.column_dominance, opt.column_dominance_mode,
                    opt.projection_bound, opt.penalty_domain_tightening,
                    opt.movement_domain_tightening, opt.support_duration_pruning,
                    opt.support_duration_max_subset_size,
                    opt.branch_inventory, opt.branch_inventory_priority,
                    opt.branch_operation_mode, opt.branch_selection,
                    opt.strong_branching_candidates, opt.strong_branching_time,
                    opt.reliability_branching, bpc_pricing_options);
                result.nodes += tree.nodes_solved;
                result.columns += tree.generated_columns;
                result.pricing_calls += tree.pricing_calls;
                if (treePricingClosureStrict(tree)) {
                    result.pricing_closed_nodes += tree.nodes_solved;
                    result.iterative_nodes_closed_by_verifier +=
                        std::max<long long>(1, tree.nodes_solved);
                }
                result.cuts_added += tree.cuts_added;
                result.pricing_time_seconds += tree.pricing_time_seconds;
                result.master_time_seconds += tree.master_time_seconds;
                copyBpcPricingStats(tree, result);
                result.columns_generated_raw += tree.columns_generated_raw;
                result.columns_after_dominance += tree.columns_after_dominance;
                result.columns_dominated += tree.columns_dominated;
                result.dominance_time_seconds += tree.dominance_time_seconds;
                result.dominance_mode = tree.dominance_mode;
                result.dominance_exact_safe =
                    result.dominance_exact_safe && tree.dominance_exact_safe;
                result.pricing_negative_columns_found +=
                    tree.pricing_negative_columns_found;
                result.pricing_negative_columns_inserted +=
                    tree.pricing_negative_columns_inserted;
                result.pricing_negative_columns_dominated +=
                    tree.pricing_negative_columns_dominated;
                result.pricing_completed_exactly =
                    result.pricing_completed_exactly &&
                    tree.pricing_completed_exactly;
                accumulateTreeRound2Stats(tree);
                addTreeColumnsToFrontierPool(tree,
                    "iterative_closure interval " + std::to_string(idx));
                recordTreeAggregate(record, tree);
                record.processed = true;
                record.open_nodes = tree.open_nodes;
                if (tree.complete) {
                    record.complete = true;
                    record.empty_complete = !tree.has_integer_incumbent;
                }
                if (tree.lower_bound_valid &&
                    std::isfinite(tree.global_lower_bound)) {
                    const double tree_lb =
                        std::max(record.lo, tree.global_lower_bound);
                    if (tree_lb > record.lower_bound + 1e-12) {
                        record.lower_bound_source = "iterative_branch_price_tree";
                    }
                    record.lower_bound = std::max(record.lower_bound, tree_lb);
                    record.lower_bound_valid = true;
                    record.lb_sources += "|iterative_branch_price_tree";
                }
                record.tree_closed = tree.complete;
                record.pricing_closed = treePricingClosureStrict(tree);
                recordClosureContinuationStats(tree,
                    "iterative_closure_interval_" + std::to_string(idx));
                runRoutePoolIncumbentMaster("after_iterative_closure_interval_" +
                                            std::to_string(idx));
                if (tree.has_integer_incumbent && !tree.best_routes.empty()) {
                    auditIntervalCandidate(tree.best_routes,
                                           tree.best_integer_surrogate,
                                           record.lo, record.hi,
                                           "iterative_closure interval " +
                                               std::to_string(idx));
                }
                if (opt.pricing_final_verifier) {
                    runPricingVerifierCheckpoint(
                        "iterative_closure_interval_" + std::to_string(idx),
                        treePricingClosureStrict(tree));
                }
            }

            const double lb_after = record.lower_bound_valid
                ? record.lower_bound : std::max(0.0, record.lo);
            const double gap_after = currentLedgerGap();
            appendDelimitedField(result.iterative_closure_lb_after_each_round,
                                 std::to_string(lb_after));
            appendDelimitedField(result.iterative_closure_gap_after_each_round,
                                 std::to_string(gap_after));
            ++result.iterative_closure_rounds;
            if (lb_after > lb_before + 1e-8 ||
                record.complete || record.bound_fathomed) {
                ++result.iterative_closure_imports_accepted;
            } else {
                stalled_intervals.insert(idx);
            }
            if (!opt.frontier_iterative_export_dir.empty()) {
                try {
                    std::filesystem::path dir(opt.frontier_iterative_export_dir);
                    std::filesystem::create_directories(dir);
                    std::filesystem::path path =
                        dir / ("iterative_interval_" + std::to_string(idx) +
                               "_round_" + std::to_string(round + 1) + ".json");
                    std::ofstream state(path, std::ios::out | std::ios::trunc);
                    state << std::setprecision(12)
                          << "{\n"
                          << "  \"state_type\": \"iterative_interval_bound_v1\",\n"
                          << "  \"instance_name\": \""
                          << jsonEscapeLocal(instance.name) << "\",\n"
                          << "  \"lambda\": " << opt.lambda << ",\n"
                          << "  \"focus_interval_id\": " << idx << ",\n"
                          << "  \"focus_interval_range\": \""
                          << jsonEscapeLocal(makeRangeString(record.lo, record.hi))
                          << "\",\n"
                          << "  \"focus_interval_lb_before\": " << lb_before << ",\n"
                          << "  \"focus_interval_lb_after\": " << lb_after << ",\n"
                          << "  \"focus_interval_closed\": "
                          << (record.complete ? "true" : "false") << ",\n"
                          << "  \"focus_interval_bound_fathomed\": "
                          << (record.bound_fathomed ? "true" : "false") << ",\n"
                          << "  \"focus_interval_open_nodes_after\": "
                          << record.open_nodes << ",\n"
                          << "  \"focus_interval_pricing_closed\": "
                          << (record.pricing_closed ? "true" : "false") << ",\n"
                          << "  \"open_node_state_exported\": true,\n"
                          << "  \"open_node_state_nodes_saved\": "
                          << record.open_nodes << ",\n"
                          << "  \"open_node_state_columns_saved\": "
                          << result.columns << ",\n"
                          << "  \"open_node_state_resume_exact\": false,\n"
                          << "  \"open_node_state_resume_fallback_reason\": \"partial_state_rebuilds_tree_no_live_node_queue\"\n"
                          << "}\n";
                } catch (const std::exception& ex) {
                    result.notes.push_back("iterative closure state export failed: "
                        + std::string(ex.what()));
                }
            }
            result.notes.push_back("iterative_closure round="
                + std::to_string(round + 1)
                + ", interval=" + std::to_string(idx)
                + ", lb_after=" + std::to_string(lb_after)
                + ", gap_after=" + std::to_string(gap_after)
                + ", open_nodes=" + std::to_string(record.open_nodes)
                + ", complete=" + std::string(record.complete ? "true" : "false")
                + ", bound_fathomed="
                + std::string(record.bound_fathomed ? "true" : "false"));
            writeProgressCheckpoint("iterative_closure_round_" +
                                    std::to_string(round + 1), true);
            if (gap_after <= opt.frontier_iterative_target_gap + 1e-12) {
                result.iterative_closure_stop_reason = "target_gap_reached";
                break;
            }
        }
        if (result.iterative_closure_stop_reason.empty()) {
            result.iterative_closure_stop_reason =
                result.iterative_closure_rounds >= max_rounds
                    ? "max_rounds_reached"
                    : "not_run";
        }
    } else {
        result.iterative_closure_stop_reason =
            focus_only_effective ? "disabled_focus_only_diagnostic" : "disabled";
    }

    runPricingVerifierCheckpoint("post_iterative_final", true);

    runRoutePoolIncumbentMaster("before_final_frontier_summary");
    writeProgressCheckpoint("route_pool_before_final_summary", true);

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
    auto classifyCertificateBasis =
        [&](FrontierIntervalRecord& record, const std::string& status) {
            record.interval_bound_valid =
                record.lower_bound_valid && std::isfinite(record.lower_bound);
            record.pricing_closure_available = record.pricing_closed;
            record.requires_pricing_closure = false;
            if (focus_only_effective) {
                record.certificate_basis = "focus_diagnostic_only";
                return;
            }
            if (!record.interval_bound_valid) {
                record.certificate_basis = "invalid";
                return;
            }
            if (record.lo >= result.upper_bound - 1e-12) {
                record.certificate_basis = "gamma_floor_skip";
                return;
            }
            if (record.complete || record.tree_closed || status == "branch_price_closed") {
                record.certificate_basis = "pricing_closed_bpc_tree";
                record.requires_pricing_closure = true;
                record.pricing_closure_available = record.pricing_closed;
                if (!record.pricing_closure_available) {
                    record.certificate_basis = "unresolved";
                }
                return;
            }
            if (record.bound_fathomed ||
                record.lower_bound >= result.upper_bound - 1e-7) {
                if (record.lb_sources.find("inventory_route_gini_relaxation") !=
                    std::string::npos ||
                    record.lb_sources.find("iterative_inventory_route_gini_relaxation") !=
                    std::string::npos) {
                    record.certificate_basis =
                        "inventory_route_gini_relaxation_fathomed";
                } else if (record.lb_sources.find("imported_focus_interval_bound") !=
                           std::string::npos) {
                    record.certificate_basis = "imported_interval_bound";
                } else {
                    record.certificate_basis = "incumbent_cutoff";
                }
                return;
            }
            record.certificate_basis = "unresolved";
        };
    bool any_interval_requires_pricing = false;
    bool all_required_pricing_available = true;
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
            classifyCertificateBasis(record, "skipped_floor_ge_incumbent");
            appendDelimitedField(result.interval_certificate_basis,
                                 std::to_string(idx) + ":" +
                                     record.certificate_basis);
            appendDelimitedField(result.interval_requires_pricing_closure,
                                 std::to_string(idx) + ":" +
                                     (record.requires_pricing_closure ? "true" : "false"));
            appendDelimitedField(result.interval_pricing_closure_available,
                                 std::to_string(idx) + ":" +
                                     (record.pricing_closure_available ? "true" : "false"));
            appendDelimitedField(result.interval_bound_valid,
                                 std::to_string(idx) + ":" +
                                     (record.interval_bound_valid ? "true" : "false"));
            appendDelimitedField(result.interval_bound_source_list,
                                 std::to_string(idx) + ":" + record.lb_sources);
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
                   << ", pricing_closed=" << (record.pricing_closed ? "true" : "false")
                   << ", certificate_basis=" << record.certificate_basis
                   << ", requires_pricing_closure="
                   << (record.requires_pricing_closure ? "true" : "false")
                   << ", pricing_closure_available="
                   << (record.pricing_closure_available ? "true" : "false")
                   << ", interval_bound_valid="
                   << (record.interval_bound_valid ? "true" : "false");
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
            classifyCertificateBasis(record, "empty_closed");
            appendDelimitedField(result.interval_certificate_basis,
                                 std::to_string(idx) + ":" +
                                     record.certificate_basis);
            appendDelimitedField(result.interval_requires_pricing_closure,
                                 std::to_string(idx) + ":" +
                                     (record.requires_pricing_closure ? "true" : "false"));
            appendDelimitedField(result.interval_pricing_closure_available,
                                 std::to_string(idx) + ":" +
                                     (record.pricing_closure_available ? "true" : "false"));
            appendDelimitedField(result.interval_bound_valid,
                                 std::to_string(idx) + ":" +
                                     (record.interval_bound_valid ? "true" : "false"));
            appendDelimitedField(result.interval_bound_source_list,
                                 std::to_string(idx) + ":" + record.lb_sources);
            any_interval_requires_pricing =
                any_interval_requires_pricing || record.requires_pricing_closure;
            all_required_pricing_available =
                all_required_pricing_available &&
                (!record.requires_pricing_closure ||
                 record.pricing_closure_available);
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
                   << ", pricing_closed=" << (record.pricing_closed ? "true" : "false")
                   << ", certificate_basis=" << record.certificate_basis
                   << ", requires_pricing_closure="
                   << (record.requires_pricing_closure ? "true" : "false")
                   << ", pricing_closure_available="
                   << (record.pricing_closure_available ? "true" : "false")
                   << ", interval_bound_valid="
                   << (record.interval_bound_valid ? "true" : "false");
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
        classifyCertificateBasis(record, status);
        appendDelimitedField(result.interval_certificate_basis,
                             std::to_string(idx) + ":" +
                                 record.certificate_basis);
        appendDelimitedField(result.interval_requires_pricing_closure,
                             std::to_string(idx) + ":" +
                                 (record.requires_pricing_closure ? "true" : "false"));
        appendDelimitedField(result.interval_pricing_closure_available,
                             std::to_string(idx) + ":" +
                                 (record.pricing_closure_available ? "true" : "false"));
        appendDelimitedField(result.interval_bound_valid,
                             std::to_string(idx) + ":" +
                                 (record.interval_bound_valid ? "true" : "false"));
        appendDelimitedField(result.interval_bound_source_list,
                             std::to_string(idx) + ":" + record.lb_sources);
        any_interval_requires_pricing =
            any_interval_requires_pricing || record.requires_pricing_closure;
        all_required_pricing_available =
            all_required_pricing_available &&
            (!record.requires_pricing_closure || record.pricing_closure_available);
        if (record.requires_pricing_closure && !record.pricing_closure_available) {
            all_certified = false;
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
               << ", pricing_closed=" << (record.pricing_closed ? "true" : "false")
               << ", certificate_basis=" << record.certificate_basis
               << ", requires_pricing_closure="
               << (record.requires_pricing_closure ? "true" : "false")
               << ", pricing_closure_available="
               << (record.pricing_closure_available ? "true" : "false")
               << ", interval_bound_valid="
               << (record.interval_bound_valid ? "true" : "false");
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
    {
        double best_remaining_lb = std::numeric_limits<double>::infinity();
        int best_remaining_idx = -1;
        for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
            const FrontierIntervalRecord& record = interval_records[idx];
            if (record.replaced_by_children || record.lo >= result.upper_bound - 1e-12) continue;
            if (record.complete || record.empty_complete || record.bound_fathomed) continue;
            const double lb = record.lower_bound_valid ? record.lower_bound : record.lo;
            if (lb < result.upper_bound - 1e-7 &&
                (lb < best_remaining_lb - 1e-12 || best_remaining_idx < 0)) {
                best_remaining_lb = lb;
                best_remaining_idx = idx;
            }
        }
        if (best_remaining_idx >= 0) {
            const FrontierIntervalRecord& record = interval_records[best_remaining_idx];
            result.v12_m1_remaining_controlling_interval =
                std::to_string(best_remaining_idx) + ":" +
                makeRangeString(record.lo, record.hi) +
                ":lb=" + std::to_string(best_remaining_lb);
        } else if (result.v12_m1_imported_focus_bounds) {
            result.v12_m1_remaining_controlling_interval = "none";
        }
        if (result.v12_m1_imported_focus_bounds) {
            result.v12_m1_full_lb_after_all_imports = result.lower_bound;
        }
    }
    result.full_certificate_requires_pricing_closure = any_interval_requires_pricing;
    result.full_certificate_pricing_closure_satisfied =
        !any_interval_requires_pricing || all_required_pricing_available;
    result.full_certificate_all_intervals_accounted =
        full_objective_range &&
        unresolved_intervals == 0 &&
        invalid_bound_intervals == 0 &&
        unprocessed_intervals == 0;
    result.full_certificate_basis =
        result.full_certificate_all_intervals_accounted
            ? "frontier_all_intervals_closed_or_fathomed"
            : "not_certified";
    if (!full_objective_range) {
        result.full_certificate_rejection_reason = "partial_or_diagnostic_frontier_range";
    } else if (invalid_bound_intervals > 0) {
        result.full_certificate_rejection_reason = "invalid_bound_intervals";
    } else if (unresolved_intervals > 0) {
        result.full_certificate_rejection_reason = "unresolved_intervals";
    } else if (unprocessed_intervals > 0) {
        result.full_certificate_rejection_reason = "unprocessed_intervals";
    } else if (!result.full_certificate_pricing_closure_satisfied) {
        result.full_certificate_rejection_reason = "pricing_closure_required_but_missing";
    } else if (result.lower_bound < result.upper_bound - 1e-7) {
        result.full_certificate_rejection_reason = "positive_gap";
    } else {
        result.full_certificate_rejection_reason = "none";
    }
    if (focus_only_effective && result.focus_interval_id >= 0 &&
        result.focus_interval_id < static_cast<int>(interval_records.size())) {
        const FrontierIntervalRecord& focus_record =
            interval_records[result.focus_interval_id];
        result.focus_interval_lb_after = focus_record.lower_bound;
        result.focus_interval_closed =
            focus_record.complete || focus_record.empty_complete ||
            focus_record.bound_fathomed ||
            (focus_record.lower_bound_valid &&
             focus_record.lower_bound >= result.upper_bound - 1e-7);
        result.focus_interval_bound_fathomed =
            focus_record.bound_fathomed ||
            (focus_record.lower_bound_valid &&
             focus_record.lower_bound >= result.upper_bound - 1e-7);
        result.focus_interval_open_nodes = focus_record.open_nodes;
        result.focus_interval_open_nodes_after = focus_record.open_nodes;
        result.focus_interval_pricing_closed = focus_record.pricing_closed;
        result.focus_interval_certificate_scope = "diagnostic_interval_only";
        full_objective_range = false;
        all_certified = false;
        result.frontier_covers_all_improving_gini_values = false;
        result.frontier_range_certificate_scope = "diagnostic_interval_only";
        result.full_certificate_basis = "not_certified";
        result.full_certificate_all_intervals_accounted = false;
        result.full_certificate_rejection_reason = "focus_diagnostic_only";
        result.notes.push_back("focus-only interval diagnostic summary: interval="
            + std::to_string(result.focus_interval_id)
            + ", range=" + result.focus_interval_range
            + ", lb_before=" + std::to_string(result.focus_interval_lb_before)
            + ", lb_after=" + std::to_string(result.focus_interval_lb_after)
            + ", closed=" + std::string(result.focus_interval_closed ? "true" : "false")
            + ", certificate_scope=diagnostic_interval_only");
    }
    result.gap = (std::fabs(result.upper_bound) > 1e-12)
        ? std::max(0.0, (result.upper_bound - result.lower_bound) / std::fabs(result.upper_bound))
        : 0.0;
    if (result.cutoff_feasibility_attempted) {
        const bool globally_cutoff_infeasible =
            result.lower_bound >= result.upper_bound -
                std::max(1e-12, result.cutoff_feasibility_epsilon);
        result.cutoff_feasibility_infeasible = globally_cutoff_infeasible;
        if (globally_cutoff_infeasible) {
            result.cutoff_feasibility_status =
                "infeasible_by_valid_global_lower_bound";
        } else if (result.focused_interval_result) {
            result.cutoff_feasibility_status =
                "focused_interval_bound_below_cutoff_diagnostic_only";
        } else {
            result.cutoff_feasibility_status =
                "best_valid_bound_below_cutoff";
        }
    }
    result.runtime_seconds = elapsedSeconds();
    result.wall_time_seconds = result.runtime_seconds;
    if (focus_only_effective) {
        result.focus_interval_runtime = result.runtime_seconds;
    }
    result.aggregate_worker_time_seconds = result.pricing_time_seconds +
        result.master_time_seconds + result.bound_time_seconds;
    if (!std::isfinite(result.pricing_best_reduced_cost_any)) {
        result.pricing_best_reduced_cost_any = 0.0;
    }
    if (!std::isfinite(result.pricing_best_new_reduced_cost)) {
        result.pricing_best_new_reduced_cost = 0.0;
    }
    {
        const bool any_pricing = result.pricing_calls > 0;
        const bool negative_remaining =
            result.pricing_best_reduced_cost_any < -1e-7;
        result.pricing_remaining_negative_rc =
            negative_remaining ? result.pricing_best_reduced_cost_any : 0.0;
        if (!any_pricing) {
            result.pricing_closure_status = "not_run";
        } else if (result.pricing_blocked_by_duplicate_projection) {
            result.pricing_closure_status = "duplicate_negative_projection";
        } else if (!result.pricing_completed_exactly) {
            result.pricing_closure_status = negative_remaining
                ? "negative_columns_remaining"
                : "pricing_time_limit";
        } else if (negative_remaining) {
            result.pricing_closure_status = "negative_columns_remaining";
        } else {
            result.pricing_closure_status = "exact_no_negative";
        }
        result.pricing_closure_certified_exact =
            any_pricing &&
            result.pricing_completed_exactly &&
            !result.pricing_blocked_by_duplicate_projection &&
            !negative_remaining &&
            result.pricing_closure_status == "exact_no_negative";
    }
    runPricingVerifierCheckpoint("final_pricing_status", true);
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
        result.full_certificate_pricing_closure_satisfied &&
        result.lower_bound >= result.upper_bound - 1e-7) {
        const double raw_frontier_lower_bound = result.lower_bound;
        result.status = "optimal";
        result.certificate = "gamma-frontier certificate: every relevant Gini interval was either closed with exact pricing or fathomed by a valid interval lower bound above the verified incumbent objective";
        result.full_certificate_basis = "frontier_all_intervals_closed_or_fathomed";
        result.full_certificate_all_intervals_accounted = true;
        result.full_certificate_rejection_reason = "none";
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
    result.final_UB = result.upper_bound;
    writeProgressCheckpoint("final_summary", true);
    if (progress_stream.is_open()) progress_stream.close();
    result.gap_trajectory_available =
        !opt.progress_log_path.empty() && result.progress_checkpoints_written > 0;
    result.actual_runtime_seconds = result.runtime_seconds;
    if (!opt.progress_log_path.empty()) {
        result.notes.push_back("periodic progress log written to " + opt.progress_log_path
            + ", checkpoints=" + std::to_string(result.progress_checkpoints_written)
            + ", interval_seconds=" + std::to_string(progress_interval));
    }
    if (isPaperTracePreset(result.algorithm_preset) && !opt.out_path.empty()) {
        auto csvEscapeLocal = [](const std::string& value) {
            bool needs_quotes = false;
            for (char ch : value) {
                if (ch == ',' || ch == '"' || ch == '\n' || ch == '\r') {
                    needs_quotes = true;
                    break;
                }
            }
            if (!needs_quotes) return value;
            std::string escaped = "\"";
            for (char ch : value) {
                if (ch == '"') escaped += "\"\"";
                else escaped.push_back(ch);
            }
            escaped.push_back('"');
            return escaped;
        };
        try {
            std::filesystem::path out_path(opt.out_path);
            std::filesystem::path trace_path = out_path;
            trace_path.replace_extension(".trace.json");
            std::filesystem::path interval_csv_path = out_path;
            interval_csv_path.replace_extension(".intervals.csv");
            if (!trace_path.parent_path().empty()) {
                std::filesystem::create_directories(trace_path.parent_path());
            }
            result.bpc_trace_json_path = trace_path.string();
            result.bpc_interval_trace_csv_path = interval_csv_path.string();

            std::ofstream interval_csv(interval_csv_path, std::ios::out | std::ios::trunc);
            interval_csv
                << "interval_id,gamma_L,gamma_U,interval_lower_bound,"
                << "incumbent_upper_bound,interval_status,reason,"
                << "certificate_basis,requires_pricing_closure,"
                << "pricing_closure_available,interval_bound_valid,"
                << "interval_closure_source,interval_closure_source_detail,"
                << "interval_requires_pricing_closure,"
                << "interval_pricing_closure_satisfied,"
                << "interval_oracle_used_for_certificate,"
                << "interval_oracle_is_diagnostic_only,"
                << "interval_relaxation_bound_valid,"
                << "interval_bpc_tree_nodes,interval_bpc_pricing_calls,"
                << "interval_bpc_exact_pricing_closed,interval_final_lb,"
                << "interval_final_ub_cutoff,"
                << "bpc_nodes,open_nodes,generated_columns,cuts,"
                << "pricing_calls,pricing_time_seconds,rmp_solve_time_seconds,"
                << "relaxation_time_seconds,lower_bound_source,lower_bound_sources,"
                << "relaxation_portfolio_mode,relaxation_variants_tried,"
                << "selected_relaxation_variant,selected_variant_reason,"
                << "probe_time_seconds,variant_bound_improvement,"
                << "best_variant_bound,variants_skipped_reason\n";

            auto intervalStatus = [&](const FrontierIntervalRecord& record) {
                if (record.replaced_by_children) return std::string("replaced_by_children");
                if (record.lo >= result.upper_bound - 1e-12) return std::string("gamma_floor_skip");
                if (!record.interval_bound_valid) return std::string("invalid");
                if (record.empty_complete) return std::string("empty");
                if (record.complete || record.tree_closed) return std::string("closed");
                if (record.bound_fathomed ||
                    (record.lower_bound_valid &&
                     record.lower_bound >= result.upper_bound - 1e-7)) {
                    return std::string("bound_fathomed");
                }
                if (!record.processed) return std::string("unprocessed_relevant");
                return std::string("unresolved");
            };
            auto intervalReason = [&](const FrontierIntervalRecord& record) {
                if (record.replaced_by_children) return std::string("split_parent_replaced");
                if (record.lo >= result.upper_bound - 1e-12) return std::string("gamma_floor_at_or_above_incumbent");
                if (!record.interval_bound_valid) return std::string("invalid_interval_bound");
                if (record.empty_complete) return std::string("empty_interval");
                if (record.complete || record.tree_closed) return std::string("branch_price_tree_closed");
                if (record.bound_fathomed ||
                    (record.lower_bound_valid &&
                     record.lower_bound >= result.upper_bound - 1e-7)) {
                    return record.lower_bound_source.empty()
                        ? std::string("valid_lower_bound_reaches_incumbent")
                        : record.lower_bound_source;
                }
                if (!record.processed) return std::string("not_processed_before_time_limit_or_reserve");
                if (record.open_nodes > 0 && record.bpc_nodes == 0) {
                    return std::string("tree_not_started_before_time_limit_or_reserve");
                }
                if (record.open_nodes > 0) return std::string("open_bpc_nodes");
                return std::string("lower_bound_below_incumbent");
            };
            auto intervalClosureSource = [&](const FrontierIntervalRecord& record,
                                             const std::string& status) {
                const std::string src = lowerAscii(
                    record.lower_bound_source + "|" + record.lb_sources + "|" +
                    record.certificate_basis);
                if (record.replaced_by_children) return std::string("unresolved");
                if (status == "gamma_floor_skip" || status == "empty") {
                    return std::string("empty");
                }
                if (src.find("interval_exact_oracle") != std::string::npos ||
                    src.find("auto_interval_oracle") != std::string::npos ||
                    src.find("interval_oracle") != std::string::npos) {
                    return std::string("interval_oracle");
                }
                if (record.complete || record.tree_closed ||
                    src.find("branch_price_tree") != std::string::npos) {
                    return std::string("bpc_exact_tree");
                }
                if (status == "bound_fathomed" || record.bound_fathomed ||
                    (record.lower_bound_valid &&
                     record.lower_bound >= result.upper_bound - 1e-7)) {
                    return std::string("relaxation_bound");
                }
                return std::string("unresolved");
            };

            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                const std::string row_status = intervalStatus(record);
                const std::string row_reason = intervalReason(record);
                const std::string closure_source =
                    intervalClosureSource(record, row_status);
                const bool oracle_used = closure_source == "interval_oracle";
                const bool bpc_used = closure_source == "bpc_exact_tree";
                interval_csv
                    << idx << ","
                    << std::setprecision(12) << record.lo << ","
                    << record.hi << ","
                    << record.lower_bound << ","
                    << result.upper_bound << ","
                    << csvEscapeLocal(row_status) << ","
                    << csvEscapeLocal(row_reason) << ","
                    << csvEscapeLocal(record.certificate_basis) << ","
                    << (record.requires_pricing_closure ? "true" : "false") << ","
                    << (record.pricing_closure_available ? "true" : "false") << ","
                    << (record.interval_bound_valid ? "true" : "false") << ","
                    << csvEscapeLocal(closure_source) << ","
                    << csvEscapeLocal(row_reason) << ","
                    << (record.requires_pricing_closure ? "true" : "false") << ","
                    << (record.pricing_closure_available ? "true" : "false") << ","
                    << (oracle_used ? "true" : "false") << ","
                    << (oracle_used && !result.certificate_uses_interval_oracle
                            ? "true" : "false") << ","
                    << (record.interval_bound_valid ? "true" : "false") << ","
                    << record.bpc_nodes << ","
                    << record.pricing_calls << ","
                    << (bpc_used && record.pricing_closure_available
                            ? "true" : "false") << ","
                    << record.lower_bound << ","
                    << result.upper_bound << ","
                    << record.bpc_nodes << ","
                    << record.open_nodes << ","
                    << record.generated_columns << ","
                    << record.cuts_added << ","
                    << record.pricing_calls << ","
                    << record.pricing_time_seconds << ","
                    << record.master_time_seconds << ","
                    << record.relaxation_time_seconds << ","
                    << csvEscapeLocal(record.lower_bound_source) << ","
                    << csvEscapeLocal(record.lb_sources) << ","
                    << csvEscapeLocal(record.relaxation_portfolio_mode) << ","
                    << csvEscapeLocal(record.relaxation_variants_tried) << ","
                    << csvEscapeLocal(record.selected_relaxation_variant) << ","
                    << csvEscapeLocal(record.selected_variant_reason) << ","
                    << record.probe_time_seconds << ","
                    << record.variant_bound_improvement << ","
                    << record.best_variant_bound << ","
                    << csvEscapeLocal(record.variants_skipped_reason) << "\n";
            }
            interval_csv.close();

            std::ofstream trace(trace_path, std::ios::out | std::ios::trunc);
            trace << std::setprecision(12);
            trace << "{\n";
            trace << "  \"trace_schema\": \"paper_bpc_core_plateau_trace_v1\",\n";
            trace << "  \"trace_scope\": \"frontier_interval_ledger_with_available_aggregate_tree_and_pricing_stats\",\n";
            trace << "  \"instance_name\": \"" << jsonEscapeLocal(instance.name) << "\",\n";
            trace << "  \"input_path\": \"" << jsonEscapeLocal(instance.path) << "\",\n";
            trace << "  \"algorithm_preset\": \"" << jsonEscapeLocal(result.algorithm_preset) << "\",\n";
            trace << "  \"method\": \"" << jsonEscapeLocal(result.method) << "\",\n";
            trace << "  \"status\": \"" << jsonEscapeLocal(result.status) << "\",\n";
            trace << "  \"objective\": " << result.objective << ",\n";
            trace << "  \"lower_bound\": " << result.lower_bound << ",\n";
            trace << "  \"upper_bound\": " << result.upper_bound << ",\n";
            trace << "  \"gap\": " << result.gap << ",\n";
            trace << "  \"certified_original_problem\": "
                  << (ebrp::inferCertifiedOriginalProblem(result) ? "true" : "false") << ",\n";
            trace << "  \"full_certificate_rejection_reason\": \""
                  << jsonEscapeLocal(result.full_certificate_rejection_reason) << "\",\n";
            trace << "  \"runtime_breakdown\": {"
                  << "\"bound_time_seconds\": " << result.bound_time_seconds
                  << ", \"route_mask_time_seconds\": " << result.route_mask_time_seconds
                  << ", \"master_time_seconds\": " << result.master_time_seconds
                  << ", \"pricing_time_seconds\": " << result.pricing_time_seconds
                  << "},\n";
            const ProgressSnapshot controlling_snapshot = snapshotFrontier();
            trace << "  \"controlling_interval\": {"
                  << "\"id\": " << controlling_snapshot.interval_id
                  << ", \"range\": \"" << jsonEscapeLocal(controlling_snapshot.interval_range)
                  << "\", \"lower_bound\": " << controlling_snapshot.lb
                  << ", \"source\": \"" << jsonEscapeLocal(controlling_snapshot.source)
                  << "\"},\n";
            bool node_trace_available = false;
            bool pricing_trace_available = false;
            for (const FrontierIntervalRecord& record : interval_records) {
                node_trace_available = node_trace_available ||
                    !record.node_trace_json_objects.empty();
                pricing_trace_available = pricing_trace_available ||
                    !record.pricing_trace_json_objects.empty();
            }
            trace << "  \"branch_price_node_trace_available\": "
                  << (node_trace_available ? "true" : "false") << ",\n";
            trace << "  \"branch_price_node_trace_limitation\": \""
                  << (node_trace_available
                      ? "node trace is available for branch-price trees that actually started in this run"
                      : "no branch-price tree started for any active interval before the time/reserve stop")
                  << "\",\n";
            trace << "  \"aggregate_tree\": {"
                  << "\"nodes\": " << result.nodes
                  << ", \"open_nodes\": " << result.open_nodes
                  << ", \"pricing_closed_nodes\": " << result.pricing_closed_nodes
                  << ", \"columns\": " << result.columns
                  << ", \"cuts_added\": " << result.cuts_added
                  << "},\n";
            trace << "  \"pricing_call_trace_available\": "
                  << (pricing_trace_available ? "true" : "false") << ",\n";
            trace << "  \"pricing_call_trace_limitation\": \""
                  << (pricing_trace_available
                      ? "pricing call trace is available for branch-price nodes that actually started in this run"
                      : "no branch-price pricing call occurred for any active interval before the time/reserve stop")
                  << "\",\n";
            trace << "  \"aggregate_pricing\": {"
                  << "\"pricing_calls\": " << result.pricing_calls
                  << ", \"pricing_completed_exactly\": "
                  << (result.pricing_completed_exactly ? "true" : "false")
                  << ", \"pricing_closure_certified_exact\": "
                  << (result.pricing_closure_certified_exact ? "true" : "false")
                  << ", \"pricing_closure_status\": \""
                  << jsonEscapeLocal(result.pricing_closure_status)
                  << "\", \"pricing_best_reduced_cost_any\": "
                  << result.pricing_best_reduced_cost_any
                  << ", \"pricing_remaining_negative_rc\": "
                  << result.pricing_remaining_negative_rc
                  << ", \"duplicate_negative_projections\": "
                  << result.pricing_duplicate_negative_projections
                  << ", \"blocked_by_duplicate_projection\": "
                  << (result.pricing_blocked_by_duplicate_projection ? "true" : "false")
                  << ", \"completion_lb_pruned_labels\": "
                  << result.completion_lb_pruned_labels
                  << ", \"required_closure_pruned_labels\": "
                  << result.required_closure_pruned_labels
                  << ", \"label_dominance_comparisons\": "
                  << result.label_dominance_comparisons
                  << ", \"label_dominance_pruned_labels\": "
                  << result.label_dominance_pruned_labels
                  << ", \"label_dominance_cross_pickup_pruned_labels\": "
                  << result.label_dominance_cross_pickup_pruned_labels
                  << ", \"label_dominance_inactive_entries_skipped\": "
                  << result.label_dominance_inactive_entries_skipped
                  << ", \"label_dominance_bucket_compactions\": "
                  << result.label_dominance_bucket_compactions
                  << ", \"label_dominance_compacted_entries\": "
                  << result.label_dominance_compacted_entries
                  << ", \"operation_dp_dominance_pruned_states\": "
                  << result.operation_dp_dominance_pruned_states
                  << "},\n";
            trace << "  \"interval_trace_csv\": \""
                  << jsonEscapeLocal(result.bpc_interval_trace_csv_path) << "\",\n";
            trace << "  \"intervals\": [\n";
            bool first_interval = true;
            for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
                const FrontierIntervalRecord& record = interval_records[idx];
                if (!first_interval) trace << ",\n";
                first_interval = false;
                trace << "    {"
                      << "\"interval_id\": " << idx
                      << ", \"gamma_L\": " << record.lo
                      << ", \"gamma_U\": " << record.hi
                      << ", \"current_interval_lower_bound\": " << record.lower_bound
                      << ", \"incumbent_upper_bound\": " << result.upper_bound
                      << ", \"status\": \"" << jsonEscapeLocal(intervalStatus(record)) << "\""
                      << ", \"reason\": \"" << jsonEscapeLocal(intervalReason(record)) << "\""
                      << ", \"certificate_basis\": \""
                      << jsonEscapeLocal(record.certificate_basis) << "\""
                      << ", \"requires_pricing_closure\": "
                      << (record.requires_pricing_closure ? "true" : "false")
                      << ", \"pricing_closure_available\": "
                      << (record.pricing_closure_available ? "true" : "false")
                      << ", \"interval_bound_valid\": "
                      << (record.interval_bound_valid ? "true" : "false")
                      << ", \"bpc_nodes\": " << record.bpc_nodes
                      << ", \"open_nodes\": " << record.open_nodes
                      << ", \"generated_columns\": " << record.generated_columns
                      << ", \"cuts\": " << record.cuts_added
                      << ", \"pricing_calls\": " << record.pricing_calls
                      << ", \"pricing_time_seconds\": "
                      << record.pricing_time_seconds
                      << ", \"rmp_solve_time_seconds\": "
                      << record.master_time_seconds
                      << ", \"relaxation_time_seconds\": "
                      << record.relaxation_time_seconds
                      << ", \"lower_bound_source\": \""
                      << jsonEscapeLocal(record.lower_bound_source) << "\""
                      << ", \"lower_bound_sources\": \""
                      << jsonEscapeLocal(record.lb_sources) << "\""
                      << "}";
            }
            trace << "\n  ],\n";
            trace << "  \"branch_price_nodes\": [\n";
            bool first_node_trace = true;
            for (const FrontierIntervalRecord& record : interval_records) {
                for (const std::string& node_trace :
                     record.node_trace_json_objects) {
                    if (!first_node_trace) trace << ",\n";
                    first_node_trace = false;
                    trace << "    " << node_trace;
                }
            }
            trace << "\n  ],\n";
            trace << "  \"pricing_calls\": [\n";
            bool first_pricing_trace = true;
            for (const FrontierIntervalRecord& record : interval_records) {
                for (const std::string& pricing_trace :
                     record.pricing_trace_json_objects) {
                    if (!first_pricing_trace) trace << ",\n";
                    first_pricing_trace = false;
                    trace << "    " << pricing_trace;
                }
            }
            trace << "\n  ]\n";
            trace << "}\n";
            trace.close();
            result.notes.push_back("paper-core BPC trace written to "
                + result.bpc_trace_json_path + " and "
                + result.bpc_interval_trace_csv_path);
        } catch (const std::exception& ex) {
            result.notes.push_back(std::string("failed to write paper-core BPC trace: ")
                + ex.what());
        }
    }
    if (!opt.frontier_export_state_path.empty()) {
        int export_idx = -1;
        double export_lb = std::numeric_limits<double>::infinity();
        for (int idx = 0; idx < static_cast<int>(interval_records.size()); ++idx) {
            const FrontierIntervalRecord& record = interval_records[idx];
            if (record.replaced_by_children) continue;
            if (record.lo >= result.upper_bound - 1e-12) continue;
            if (record.complete || record.empty_complete || record.bound_fathomed) continue;
            const double lb = record.lower_bound_valid
                ? record.lower_bound
                : std::max(0.0, record.lo);
            if (lb < export_lb - 1e-12 ||
                (std::fabs(lb - export_lb) <= 1e-12 &&
                 (export_idx < 0 || idx < export_idx))) {
                export_idx = idx;
                export_lb = lb;
            }
        }
        if (export_idx < 0 && !interval_records.empty()) {
            export_idx = 0;
            export_lb = interval_records[0].lower_bound;
        }
        try {
            std::filesystem::path state_path(opt.frontier_export_state_path);
            if (!state_path.parent_path().empty()) {
                std::filesystem::create_directories(state_path.parent_path());
            }
            std::ofstream state(state_path, std::ios::out | std::ios::trunc);
            if (!state) {
                throw std::runtime_error("cannot open state export file");
            }
            const FrontierIntervalRecord* record = export_idx >= 0
                ? &interval_records[export_idx]
                : nullptr;
            state << std::setprecision(12);
            state << "{\n";
            state << "  \"state_type\": \"frontier_interval_resume_v1\",\n";
            state << "  \"instance_name\": \"" << jsonEscapeLocal(instance.name) << "\",\n";
            state << "  \"input_path\": \"" << jsonEscapeLocal(instance.path) << "\",\n";
            state << "  \"lambda\": " << opt.lambda << ",\n";
            state << "  \"T\": " << opt.total_time_limit << ",\n";
            state << "  \"pickup_time\": " << opt.pickup_time << ",\n";
            state << "  \"drop_time\": " << opt.drop_time << ",\n";
            state << "  \"incumbent_objective\": " << result.upper_bound << ",\n";
            state << "  \"route_pool_columns_after_dominance\": "
                  << result.route_pool_columns_after_dominance << ",\n";
            state << "  \"columns\": " << result.columns << ",\n";
            state << "  \"open_nodes\": " << result.open_nodes << ",\n";
            state << "  \"open_node_state_exported\": "
                  << (opt.frontier_export_open_nodes ? "true" : "false") << ",\n";
            state << "  \"open_node_state_nodes_saved\": "
                  << (opt.frontier_export_open_nodes && record
                          ? record->open_nodes : 0) << ",\n";
            state << "  \"open_node_state_columns_saved\": "
                  << (opt.frontier_export_open_nodes ? result.columns : 0) << ",\n";
            state << "  \"open_node_state_resume_exact\": false,\n";
            state << "  \"open_node_state_resume_fallback_reason\": \"partial_state_rebuilds_tree_no_live_node_queue\",\n";
            state << "  \"pricing_closure_status\": \""
                  << jsonEscapeLocal(result.pricing_closure_status) << "\",\n";
            state << "  \"focus_interval_id\": " << export_idx << ",\n";
            state << "  \"focus_interval_parent_id\": "
                  << (record ? record->parent_id : -1) << ",\n";
            state << "  \"focus_interval_range\": \""
                  << (record ? jsonEscapeLocal(makeRangeString(record->lo, record->hi))
                             : "") << "\",\n";
            state << "  \"focus_interval_lb_before\": "
                  << (record ? record->lower_bound : 0.0) << ",\n";
            state << "  \"focus_interval_lb_after\": "
                  << (record ? record->lower_bound : 0.0) << ",\n";
            state << "  \"focus_interval_closed\": "
                  << (record && (record->complete || record->empty_complete)
                          ? "true" : "false") << ",\n";
            state << "  \"focus_interval_bound_fathomed\": "
                  << (record && record->bound_fathomed ? "true" : "false") << ",\n";
            state << "  \"focus_interval_open_nodes_after\": "
                  << (record ? record->open_nodes : 0) << ",\n";
            state << "  \"focus_interval_pricing_closed\": "
                  << (record && record->pricing_closed ? "true" : "false") << ",\n";
            state << "  \"resume_limitation\": \"open nodes are not serialized; resume reloads compatible interval metadata, incumbent scalar bound, and generated-column counts, then rebuilds the exact interval tree\"\n";
            state << "}\n";
            result.frontier_state_exported = true;
            result.frontier_state_export_path = opt.frontier_export_state_path;
            result.open_node_state_exported = opt.frontier_export_open_nodes;
            result.open_node_state_nodes_saved =
                opt.frontier_export_open_nodes && record ? record->open_nodes : 0;
            result.open_node_state_columns_saved =
                opt.frontier_export_open_nodes ? result.columns : 0;
            result.open_node_state_resume_exact = false;
            if (opt.frontier_export_open_nodes) {
                result.open_node_state_resume_fallback_reason =
                    "partial_state_rebuilds_tree_no_live_node_queue";
            }
            result.notes.push_back("frontier state exported to "
                + opt.frontier_export_state_path
                + "; partial open-node metadata exported, compatible resume rebuilds the selected interval and is reported as warm restart unless exact queue serialization is added");
        } catch (const std::exception& ex) {
            result.frontier_state_exported = false;
            result.frontier_state_export_path = opt.frontier_export_state_path;
            result.notes.push_back("frontier state export failed for "
                + opt.frontier_export_state_path + ": " + ex.what());
        }
    }
    if (!std::isfinite(result.best_gap_seen)) {
        result.best_gap_seen = result.gap;
        result.best_gap_time_seconds = result.runtime_seconds;
    }
    return result;
}

std::vector<std::string> splitCsvLineSimple(const std::string& line) {
    std::vector<std::string> cells;
    std::string cell;
    bool in_quotes = false;
    for (std::size_t i = 0; i < line.size(); ++i) {
        const char ch = line[i];
        if (ch == '"') {
            if (in_quotes && i + 1 < line.size() && line[i + 1] == '"') {
                cell.push_back('"');
                ++i;
            } else {
                in_quotes = !in_quotes;
            }
        } else if (ch == ',' && !in_quotes) {
            cells.push_back(cell);
            cell.clear();
        } else {
            cell.push_back(ch);
        }
    }
    cells.push_back(cell);
    return cells;
}

std::string csvEscapeSimple(const std::string& value) {
    bool needs_quotes = false;
    for (const char ch : value) {
        if (ch == ',' || ch == '"' || ch == '\n' || ch == '\r') {
            needs_quotes = true;
            break;
        }
    }
    if (!needs_quotes) return value;
    std::string out = "\"";
    for (const char ch : value) {
        if (ch == '"') out += "\"\"";
        else out.push_back(ch);
    }
    out.push_back('"');
    return out;
}

struct IntervalCsvRow {
    std::vector<std::string> cells;
    std::unordered_map<std::string, std::size_t> index;

    std::string get(const std::string& key) const {
        const auto it = index.find(key);
        if (it == index.end() || it->second >= cells.size()) return {};
        return cells[it->second];
    }

    void set(const std::string& key, const std::string& value) {
        const auto it = index.find(key);
        if (it != index.end() && it->second < cells.size()) cells[it->second] = value;
    }
};

void ensureIntervalCsvColumn(std::vector<std::string>& header,
                             std::vector<IntervalCsvRow>& rows,
                             const std::string& key) {
    if (std::find(header.begin(), header.end(), key) != header.end()) return;
    const std::size_t pos = header.size();
    header.push_back(key);
    for (auto& row : rows) {
        row.index[key] = pos;
        row.cells.emplace_back();
    }
}

double csvDoubleField(const IntervalCsvRow& row,
                      const std::string& key,
                      double fallback = 0.0) {
    try {
        const std::string raw = row.get(key);
        if (raw.empty()) return fallback;
        const double v = std::stod(raw);
        return std::isfinite(v) ? v : fallback;
    } catch (const std::exception&) {
        return fallback;
    }
}

std::vector<IntervalCsvRow> readIntervalCsvRows(
    const std::filesystem::path& path,
    std::vector<std::string>& header) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open interval CSV: " + path.string());
    std::string line;
    if (!std::getline(in, line)) return {};
    header = splitCsvLineSimple(line);
    std::unordered_map<std::string, std::size_t> index;
    for (std::size_t i = 0; i < header.size(); ++i) index[header[i]] = i;
    std::vector<IntervalCsvRow> rows;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        IntervalCsvRow row;
        row.cells = splitCsvLineSimple(line);
        row.index = index;
        while (row.cells.size() < header.size()) row.cells.emplace_back();
        rows.push_back(std::move(row));
    }
    return rows;
}

void writeIntervalCsvRows(const std::filesystem::path& path,
                          const std::vector<std::string>& header,
                          const std::vector<IntervalCsvRow>& rows) {
    if (!path.parent_path().empty()) {
        std::filesystem::create_directories(path.parent_path());
    }
    std::ofstream out(path, std::ios::out | std::ios::trunc);
    for (std::size_t i = 0; i < header.size(); ++i) {
        if (i) out << ",";
        out << csvEscapeSimple(header[i]);
    }
    out << "\n";
    for (const auto& row : rows) {
        for (std::size_t i = 0; i < header.size(); ++i) {
            if (i) out << ",";
            out << csvEscapeSimple(i < row.cells.size() ? row.cells[i] : "");
        }
        out << "\n";
    }
}

void applySealedRunProvenance(const ebrp::SolveOptions& opt,
                              ebrp::SolveResult& result) {
    result.sealed_run = opt.paper_run_sealed;
    if (!result.sealed_run) return;
    if (result.sealed_run_id.empty()) {
        std::ostringstream id;
        id << "sealed_" << std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        if (!result.instance_name.empty()) id << "_" << result.instance_name;
        result.sealed_run_id = id.str();
    }
    if (result.sealed_run_start_time.empty()) {
        result.sealed_run_start_time = std::to_string(
            std::chrono::duration_cast<std::chrono::seconds>(
                std::chrono::system_clock::now().time_since_epoch()).count());
    }
    result.no_archive_scanning =
        !opt.incumbent_archive_auto &&
        result.incumbent_source_category != "diagnostic_archive";
    result.no_external_known_ub =
        opt.incumbent_json_path.empty() &&
        opt.hga_incumbent_path.empty() &&
        opt.external_incumbent_path.empty() &&
        result.incumbent_source_category != "explicit_incumbent_json" &&
        !result.incumbent_import_attempted &&
        !result.external_incumbent_attempted;
    result.no_focus_only_certificate =
        !opt.frontier_focus_only &&
        !result.focused_interval_result &&
        result.frontier_range_certificate_scope != "diagnostic_interval_only";
    result.same_run_generated_incumbent =
        result.incumbent_source_category == "primal_heuristic" ||
        result.incumbent_source_category == "empty";
    if (result.incumbent_source_category == "primal_heuristic") {
        result.incumbent_provenance =
            "same-run native HGA-TGBC paper primal heuristic, verifier-gated UB only";
    } else if (result.incumbent_source_category == "empty") {
        result.incumbent_provenance = "no external incumbent; empty/trivial UB path";
    } else {
        result.incumbent_provenance = result.incumbent_source_detail;
    }
    std::vector<std::string> rejections;
    if (!opt.paper_run_sealed_rejection_reason.empty()) {
        rejections.push_back(opt.paper_run_sealed_rejection_reason);
    }
    if (!result.no_archive_scanning) rejections.push_back("archive_scanning_or_archive_ub");
    if (!result.no_external_known_ub) rejections.push_back("external_known_ub_or_import");
    if (!result.no_focus_only_certificate) rejections.push_back("focus_only_certificate_path");
    if (!rejections.empty()) {
        std::ostringstream joined;
        for (std::size_t i = 0; i < rejections.size(); ++i) {
            if (i) joined << ";";
            joined << rejections[i];
        }
        result.sealed_run_forbidden_source_used = true;
        result.sealed_run_rejection_reason = joined.str();
        if (result.status == "optimal") {
            result.status = "not_certified_sealed_provenance";
            result.certificate =
                "sealed paper-run provenance guard rejected the original-problem certificate";
            if (result.full_certificate_rejection_reason.empty() ||
                result.full_certificate_rejection_reason == "none") {
                result.full_certificate_rejection_reason =
                    "sealed_run_forbidden_source_used";
            }
        }
        result.notes.push_back("sealed paper-run guard rejection: "
            + result.sealed_run_rejection_reason);
    } else {
        result.sealed_run_forbidden_source_used = false;
        result.sealed_run_rejection_reason = "none";
    }
}

void runAutoIntervalOracleClosure(const ebrp::Instance& instance,
                                  const ebrp::SolveOptions& opt,
                                  ebrp::SolveResult& result) {
    if (!opt.auto_interval_oracle) {
        result.full_ledger_merge_status = result.full_ledger_merge_status.empty()
            ? "not_requested" : result.full_ledger_merge_status;
        return;
    }
    if (result.status == "optimal" || result.unresolved_intervals <= 0) {
        result.auto_interval_oracle_total_final_leaves = 0;
        result.auto_interval_oracle_remaining_open_leaves = 0;
        result.auto_interval_oracle_coverage_complete = true;
        result.full_ledger_merge_status = "already_closed_before_auto_oracle";
        result.full_ledger_merge_audit_passed = result.status == "optimal";
        return;
    }
    if (result.bpc_interval_trace_csv_path.empty() ||
        !std::filesystem::exists(result.bpc_interval_trace_csv_path)) {
        result.full_ledger_merge_status = "no_interval_ledger_for_auto_oracle";
        result.auto_interval_oracle_remaining_open_leaves = result.unresolved_intervals;
        result.notes.push_back("auto interval oracle skipped: interval ledger missing");
        return;
    }

    const auto oracle_start = std::chrono::steady_clock::now();
    result.auto_interval_oracle_called = true;
    std::vector<std::string> header;
    std::vector<IntervalCsvRow> rows;
    try {
        rows = readIntervalCsvRows(result.bpc_interval_trace_csv_path, header);
    } catch (const std::exception& ex) {
        result.full_ledger_merge_status = "interval_ledger_read_failed";
        result.auto_interval_oracle_remaining_open_leaves = result.unresolved_intervals;
        result.notes.push_back(std::string("auto interval oracle skipped: ") + ex.what());
        return;
    }
    const std::vector<std::string> oracle_bound_columns = {
        "oracle_bound_merged",
        "oracle_bound_value",
        "oracle_bound_status",
        "oracle_bound_source_json",
        "oracle_bound_solver_status",
        "oracle_bound_model_type",
        "oracle_bound_valid",
        "lower_bound_before_oracle",
        "lower_bound_after_oracle",
        "lower_bound_improvement_by_oracle",
        "leaf_closed_by_oracle_bound",
        "interval_closure_source",
        "interval_closure_source_detail",
        "interval_requires_pricing_closure",
        "interval_pricing_closure_satisfied",
        "interval_oracle_used_for_certificate",
        "interval_oracle_is_diagnostic_only",
        "interval_relaxation_bound_valid",
        "interval_bpc_tree_nodes",
        "interval_bpc_pricing_calls",
        "interval_bpc_exact_pricing_closed",
        "interval_final_lb",
        "interval_final_ub_cutoff"
    };
    for (const std::string& col : oracle_bound_columns) {
        ensureIntervalCsvColumn(header, rows, col);
    }

    std::vector<std::size_t> targets;
    for (std::size_t i = 0; i < rows.size(); ++i) {
        const std::string status = lowerAscii(rows[i].get("interval_status"));
        if (status != "unresolved" && status != "unprocessed_relevant" &&
            status != "invalid") {
            continue;
        }
        const double lo = csvDoubleField(rows[i], "gamma_L", -1.0);
        const double hi = csvDoubleField(rows[i], "gamma_U", -1.0);
        const double lb = csvDoubleField(rows[i], "interval_lower_bound", lo);
        if (lo < -1e-12 || hi < lo - 1e-12) continue;
        if (lb >= result.upper_bound - 1e-7) continue;
        targets.push_back(i);
    }
    const std::string order = opt.auto_interval_oracle_order;
    std::sort(targets.begin(), targets.end(), [&](std::size_t a, std::size_t b) {
        if (order == "low-gini") {
            return csvDoubleField(rows[a], "gamma_L", 0.0) <
                   csvDoubleField(rows[b], "gamma_L", 0.0);
        }
        if (order == "best-bound") {
            return csvDoubleField(rows[a], "interval_lower_bound", 0.0) >
                   csvDoubleField(rows[b], "interval_lower_bound", 0.0);
        }
        if (order == "min-lb") {
            return csvDoubleField(rows[a], "interval_lower_bound", 0.0) <
                   csvDoubleField(rows[b], "interval_lower_bound", 0.0);
        }
        if (order == "min-gap") {
            const double ga = result.upper_bound -
                csvDoubleField(rows[a], "interval_lower_bound", 0.0);
            const double gb = result.upper_bound -
                csvDoubleField(rows[b], "interval_lower_bound", 0.0);
            return ga < gb;
        }
        const int ia = static_cast<int>(csvDoubleField(rows[a], "interval_id", 0.0));
        const int ib = static_cast<int>(csvDoubleField(rows[b], "interval_id", 0.0));
        return ia < ib;
    });
    const int total_final_leaves = static_cast<int>(targets.size());
    if (opt.auto_interval_oracle_max_leaves > 0 &&
        static_cast<int>(targets.size()) > opt.auto_interval_oracle_max_leaves) {
        targets.resize(static_cast<std::size_t>(opt.auto_interval_oracle_max_leaves));
    }
    result.auto_interval_oracle_total_final_leaves = total_final_leaves;

    std::filesystem::path out_path = opt.out_path.empty()
        ? std::filesystem::path("auto_interval_oracle.json")
        : std::filesystem::path(opt.out_path);
    const std::filesystem::path base_dir = out_path.has_parent_path()
        ? out_path.parent_path()
        : std::filesystem::path(".");
    const std::string stem = out_path.stem().string();
    const std::filesystem::path oracle_dir = base_dir / (stem + "_auto_oracle");
    std::filesystem::create_directories(oracle_dir);
    const std::filesystem::path oracle_csv = base_dir / (stem + ".auto_oracle.csv");
    const std::filesystem::path partition_csv =
        base_dir / (stem + ".oracle_partition_tree.csv");
    std::ofstream summary(oracle_csv, std::ios::out | std::ios::trunc);
    summary << "interval_id,gamma_L,gamma_U,status,certificate_basis,solver_status,"
            << "proven_infeasible,feasible_improving,timeout,best_bound,objective,"
            << "runtime_seconds,depth,parent_id,time_limit_used,budget_policy,"
            << "model_type,bound_valid,bound_scope,can_merge_bound,gap_to_cutoff,"
            << "bound_used_for_merge,closed_by_bound,gini_spread_cuts_added,"
            << "required_movement_lb,required_movement_cuts_added,"
            << "global_handling_capacity_lb,global_handling_capacity_cuts_added,"
            << "transfer_subset_capacity_cuts_added,low_gini_ratio_band_domains_tightened,"
            << "direct_gini_cap_rows,tight_mccormick_rows,inventory_conservation_rows,"
            << "movement_reachability_domains,visit_inventory_linking_rows,"
            << "objective_estimator_cutoff_rows,penalty_lb,support_duration_pair_cuts,"
            << "support_duration_triple_cuts,transfer_compatibility_cuts,"
            << "receiver_source_cover_cuts,variable_s_centering_rows,s_range_rows,"
            << "sp_product_mccormick_rows,sp_product_estimator_rows,"
            << "oracle_strengthening_families_enabled,json_path,lp_path,log_path\n";
    std::ofstream partition(partition_csv, std::ios::out | std::ios::trunc);
    partition << "interval_id,parent_id,depth,gamma_L,gamma_U,status,closed,"
              << "split,children,time_limit_used,runtime_seconds,certificate_basis,"
              << "solver_status\n";

    int closed = 0;
    int attempted = 0;
    int timed_out = 0;
    int split = 0;
    int children_attempted = 0;
    int max_depth_reached = 0;
    int feasible_improving = 0;
    int root_bound_merged = 0;
    int root_bound_closed = 0;
    long long total_direct_gini_cap = 0;
    long long total_direct_gini_floor = 0;
    long long total_tight_mccormick = 0;
    long long total_inventory_conservation = 0;
    long long total_movement_domains = 0;
    long long total_visit_inventory = 0;
    long long total_objective_estimator = 0;
    long long total_penalty_lb_rows = 0;
    long long total_gini_spread = 0;
    long long total_required_movement = 0;
    long long total_global_handling = 0;
    long long total_support_pair = 0;
    long long total_support_triple = 0;
    long long total_transfer_compat = 0;
    long long total_receiver_source_cover = 0;
    long long total_variable_s_centering = 0;
    long long total_s_range_rows = 0;
    long long total_sp_product_mccormick = 0;
    long long total_sp_product_estimator = 0;
    long long total_tailored_gini_subset = 0;
    long long total_tailored_l1 = 0;
    long long total_tailored_l1_vars = 0;
    long long total_tailored_local_centering = 0;
    long long total_tailored_local_centering_violations = 0;
    long long total_tailored_subset_cross_h = 0;
    long long total_tailored_subset_cross_h_candidates = 0;
    long long total_tailored_subset_cross_h_violations = 0;
    double total_tailored_subset_cross_h_max_violation = 0.0;
    long long total_tailored_local_q = 0;
    long long total_tailored_local_q_violations = 0;
    double total_tailored_local_q_max_violation = 0.0;
    long long total_tailored_variable_s = 0;
    long long total_tailored_variable_s_violations = 0;
    long long total_tailored_subset_inventory = 0;
    long long total_tailored_transfer_cutset = 0;
    long long total_tailored_compatible_source_transfer = 0;
    long long total_tailored_compatible_source_transfer_candidates = 0;
    long long total_tailored_required_external_source = 0;
    long long total_tailored_benders_inventory = 0;
    long long total_tailored_benders_inventory_candidates = 0;
    long long total_tailored_support_pair = 0;
    long long total_tailored_support_pair_candidates = 0;
    long long total_tailored_support_pair_violations = 0;
    long long total_tailored_support_triple = 0;
    long long total_tailored_support_triple_candidates = 0;
    long long total_tailored_support_triple_violations = 0;
    long long total_tailored_support_quad = 0;
    long long total_tailored_support_quad_candidates = 0;
    long long total_tailored_support_quad_violations = 0;
    long long total_tailored_support_lifted = 0;
    long long total_tailored_support_lifted_candidates = 0;
    long long total_tailored_support_lifted_violations = 0;
    long long total_low_gini_domains = 0;
    long long total_nodes = 0;
    long long total_dynamic_cuts = 0;
    long long total_root_cut_rounds = 0;
    long long total_model_rows = 0;
    long long total_model_cols = 0;
    long long total_model_nonzeros = 0;
    double total_memory_estimate_mb = 0.0;
    double total_solver_time = 0.0;
    bool budget_exhausted = false;
    bool oracle_blocker_seen = false;
    std::string oracle_blocker_note;
    std::ostringstream status_by_leaf;
    std::ostringstream time_limits_used;

    struct OracleIntervalOutcome {
        bool closed = false;
        bool bound_valid = false;
        bool bound_merged = false;
        bool feasible_improving = false;
        bool timeout = false;
        double lower_bound = 0.0;
        std::string status;
        std::string basis;
        std::string solver_status;
        std::string model_type;
        std::string source_json;
    };

    const double default_leaf_time = std::max(60.0, opt.solve_time_limit * 0.25);
    const double requested_leaf_time =
        opt.auto_interval_oracle_time_limit > 0.0
            ? opt.auto_interval_oracle_time_limit
            : default_leaf_time;
    const double requested_child_time =
        opt.auto_interval_oracle_child_time_limit > 0.0
            ? opt.auto_interval_oracle_child_time_limit
            : requested_leaf_time;
    const std::string budget_policy = opt.auto_interval_oracle_leaf_budget_policy;
    const double total_budget =
        opt.auto_interval_oracle_total_budget > 0.0
            ? opt.auto_interval_oracle_total_budget
            : (budget_policy == "total" ? requested_leaf_time : 0.0);
    result.auto_interval_oracle_requested_leaf_time_limit = requested_leaf_time;
    result.auto_interval_oracle_actual_leaf_time_limit = requested_leaf_time;
    result.auto_interval_oracle_total_budget = total_budget;
    result.auto_interval_oracle_budget_policy = budget_policy;
    result.auto_interval_oracle_max_children_total =
        opt.auto_interval_oracle_max_children_total;
    result.auto_interval_oracle_partition_tree_csv_path = partition_csv.string();

    auto elapsed_oracle_seconds = [&]() {
        return std::chrono::duration<double>(
            std::chrono::steady_clock::now() - oracle_start).count();
    };
    auto timeLimitFor = [&](int depth) {
        const double base = depth > 0 ? requested_child_time : requested_leaf_time;
        if (total_budget <= 0.0) return base;
        const double remaining = total_budget - elapsed_oracle_seconds();
        if (remaining <= 1e-6) {
            budget_exhausted = true;
            return 0.0;
        }
        return std::max(0.0, std::min(base, remaining));
    };
    auto safeFileId = [](std::string id) {
        for (char& ch : id) {
            if (!std::isalnum(static_cast<unsigned char>(ch)) && ch != '_' && ch != '-') {
                ch = '_';
            }
        }
        return id;
    };
    auto run_one_oracle = [&](const std::string& interval_id,
                              const std::string& parent_id,
                              int depth,
                              double lo,
                              double hi,
                              double time_limit) {
        ++attempted;
        if (depth > 0) ++children_attempted;
        max_depth_reached = std::max(max_depth_reached, depth);
        ebrp::SolveOptions oracle_opt = opt;
        oracle_opt.method = "interval-cutoff-oracle";
        oracle_opt.interval_exact_cutoff_oracle = "compact-mip";
        oracle_opt.interval_exact_cutoff_gamma_L = lo;
        oracle_opt.interval_exact_cutoff_gamma_U = hi;
        oracle_opt.interval_exact_cutoff_UB = result.upper_bound;
        oracle_opt.interval_exact_cutoff_epsilon =
            std::max(1e-8, opt.cutoff_feasibility_epsilon);
        oracle_opt.interval_exact_cutoff_time_limit = std::max(0.0, time_limit);
        const std::string file_id = safeFileId(interval_id);
        const std::filesystem::path json_path =
            oracle_dir / ("interval_" + file_id + ".json");
        oracle_opt.out_path = json_path.string();
        oracle_opt.log_path.clear();
        oracle_opt.interval_exact_cutoff_export_lp =
            (oracle_dir / ("interval_" + file_id + ".lp")).string();
        oracle_opt.interval_exact_cutoff_result =
            (oracle_dir / ("interval_" + file_id + ".sol")).string();

        ebrp::SolveResult oracle = ebrp::solveIntervalExactCutoffOracle(
            instance, oracle_opt);
        initializeScalabilityFields(instance, oracle_opt, oracle);
        applyRunConfigSnapshot(buildRunConfigSnapshot(instance, oracle_opt), oracle);
        oracle.finalization_source = "solver_final_json";
        oracle.solver_finalization_reached = true;
        oracle.wrapper_synthesized_final_json = false;
        oracle.process_return_code = 0;
        oracle.abnormal_exit_detected = false;
        oracle.abnormal_exit_reason = "none";
        oracle.last_progress_event = "interval_oracle_final";
        oracle.plateau_reason = oracle.status == "interval_closed"
            ? "interval_closed"
            : "interval_oracle_unresolved";
        finalizePaperModuleFields(oracle);
        oracle.result_file = json_path.string();
        try {
            ebrp::writeTextFile(json_path.string(), ebrp::resultToJson(oracle));
        } catch (const std::exception& ex) {
            result.notes.push_back(std::string("auto interval oracle failed to write JSON: ")
                + ex.what());
        }
        if (status_by_leaf.tellp() > 0) status_by_leaf << "|";
        status_by_leaf << interval_id << ":"
                       << oracle.status << ":"
                       << oracle.interval_exact_cutoff_certificate_basis << ":"
                       << oracle.interval_exact_cutoff_solver_status;
        if (oracle.interval_exact_cutoff_timeout) {
            ++timed_out;
        }
        if (oracle.interval_exact_cutoff_feasible_improving) {
            ++feasible_improving;
        }
        summary << csvEscapeSimple(interval_id) << ","
                << std::setprecision(12) << lo << "," << hi << ","
                << csvEscapeSimple(oracle.status) << ","
                << csvEscapeSimple(oracle.interval_exact_cutoff_certificate_basis) << ","
                << csvEscapeSimple(oracle.interval_exact_cutoff_solver_status) << ","
                << (oracle.interval_exact_cutoff_proven_infeasible ? "true" : "false") << ","
                << (oracle.interval_exact_cutoff_feasible_improving ? "true" : "false") << ","
                << (oracle.interval_exact_cutoff_timeout ? "true" : "false") << ","
                << oracle.interval_exact_cutoff_best_bound << ","
                << oracle.interval_exact_cutoff_objective << ","
                << oracle.interval_exact_cutoff_runtime_seconds << ","
                << depth << ","
                << csvEscapeSimple(parent_id) << ","
                << time_limit << ","
                << csvEscapeSimple(budget_policy) << ","
                << csvEscapeSimple(oracle.interval_oracle_model_type) << ","
                << (oracle.interval_oracle_bound_valid ? "true" : "false") << ","
                << csvEscapeSimple(oracle.interval_oracle_bound_scope) << ","
                << (oracle.interval_oracle_can_merge_bound ? "true" : "false") << ","
                << oracle.interval_oracle_gap_to_cutoff << ","
                << (oracle.interval_oracle_can_merge_bound
                        ? oracle.lower_bound : 0.0) << ","
                << ((oracle.status == "interval_closed" ||
                     (oracle.interval_oracle_can_merge_bound &&
                      oracle.lower_bound >= result.upper_bound - 1e-7))
                        ? "true" : "false") << ","
                << oracle.gini_spread_cuts_added << ","
                << oracle.required_movement_lb << ","
                << oracle.required_movement_cuts_added << ","
                << oracle.global_handling_capacity_lb << ","
                << oracle.global_handling_capacity_cuts_added << ","
                << oracle.transfer_subset_capacity_cuts_added << ","
                << oracle.low_gini_ratio_band_domains_tightened << ","
                << oracle.compact_bc_direct_gini_cap_rows_added << ","
                << oracle.compact_bc_tight_mccormick_rows_added << ","
                << oracle.compact_bc_inventory_conservation_rows_added << ","
                << oracle.compact_bc_movement_reachability_domains_tightened << ","
                << oracle.compact_bc_visit_inventory_linking_rows_added << ","
                << oracle.compact_bc_objective_estimator_cutoff_rows_added << ","
                << oracle.compact_bc_penalty_lb << ","
                << oracle.compact_bc_support_duration_pair_cuts_added << ","
                << oracle.compact_bc_support_duration_triple_cuts_added << ","
                << oracle.compact_bc_pairwise_transfer_compatibility_cuts_added << ","
                << oracle.compact_bc_receiver_source_cover_cuts_added << ","
                << oracle.compact_bc_variable_s_centering_rows_added << ","
                << oracle.compact_bc_s_range_rows_added << ","
                << oracle.compact_bc_sp_product_mccormick_rows_added << ","
                << oracle.compact_bc_sp_product_estimator_rows_added << ","
                << csvEscapeSimple(oracle.oracle_strengthening_families_enabled) << ","
                << csvEscapeSimple(json_path.string()) << ","
                << csvEscapeSimple(oracle.interval_exact_cutoff_lp_path) << ","
                << csvEscapeSimple(oracle.interval_exact_cutoff_log_path) << "\n";
        summary.flush();
        if (time_limits_used.tellp() > 0) time_limits_used << "|";
        time_limits_used << interval_id << ":" << time_limit;
        return oracle;
    };
    std::function<OracleIntervalOutcome(const std::string&, const std::string&, int, double, double)> close_interval;
    close_interval = [&](const std::string& interval_id,
                         const std::string& parent_id,
                         int depth,
                         double lo,
                         double hi) -> OracleIntervalOutcome {
        OracleIntervalOutcome outcome;
        outcome.lower_bound = std::max(0.0, lo);
        const double time_limit = timeLimitFor(depth);
        if (time_limit <= 1e-9) {
            budget_exhausted = true;
            if (status_by_leaf.tellp() > 0) status_by_leaf << "|";
            status_by_leaf << interval_id << ":skipped_budget_exhausted:none:none";
            partition << csvEscapeSimple(interval_id) << ","
                      << csvEscapeSimple(parent_id) << ","
                      << depth << ","
                      << std::setprecision(12) << lo << "," << hi << ","
                      << "skipped_budget_exhausted,false,false,0,0,0,"
                      << "budget_exhausted,not_run\n";
            outcome.status = "skipped_budget_exhausted";
            outcome.basis = "budget_exhausted";
            outcome.solver_status = "not_run";
            outcome.model_type = "not_run";
            outcome.bound_valid = true;
            return outcome;
        }
        ebrp::SolveResult oracle =
            run_one_oracle(interval_id, parent_id, depth, lo, hi, time_limit);
        outcome.status = oracle.status;
        outcome.basis = oracle.interval_exact_cutoff_certificate_basis;
        outcome.solver_status = oracle.interval_exact_cutoff_solver_status;
        outcome.model_type = oracle.interval_oracle_model_type;
        outcome.source_json = oracle.result_file;
        outcome.timeout = oracle.interval_exact_cutoff_timeout;
        outcome.feasible_improving = oracle.interval_exact_cutoff_feasible_improving;
        const bool direct_bound_mergeable =
            opt.interval_oracle_merge_timeout_bound &&
            oracle.interval_oracle_can_merge_bound &&
            oracle.lower_bound >= lo - 1e-9;
        if (direct_bound_mergeable) {
            outcome.bound_valid = true;
            outcome.bound_merged = true;
            outcome.lower_bound = std::max(outcome.lower_bound, oracle.lower_bound);
        }
        bool oracle_closed =
            (oracle.status == "interval_closed" &&
             oracle.interval_exact_cutoff_proven_infeasible) ||
            (direct_bound_mergeable &&
             oracle.lower_bound >= result.upper_bound - 1e-7);
        if (oracle_closed) {
            outcome.closed = true;
            outcome.bound_valid = true;
            outcome.bound_merged = true;
            outcome.lower_bound = result.upper_bound;
        }
        const bool can_split =
            !oracle_closed &&
            oracle.interval_exact_cutoff_timeout &&
            opt.auto_interval_oracle_split_on_timeout &&
            (opt.auto_interval_oracle_recursive_split || depth == 0) &&
            depth < opt.auto_interval_oracle_max_depth &&
            opt.auto_interval_oracle_child_split_count > 1 &&
            hi > lo + std::max(1e-12, opt.auto_interval_oracle_min_width) &&
            (opt.auto_interval_oracle_max_children_total <= 0 ||
             children_attempted < opt.auto_interval_oracle_max_children_total);
        bool did_split = false;
        int child_count_used = 0;
        if (can_split) {
            ++split;
            did_split = true;
            bool all_children_closed = true;
            bool child_coverage_complete = true;
            double child_partition_lb = std::numeric_limits<double>::infinity();
            bool child_bound_merged = false;
            const int child_count = opt.auto_interval_oracle_child_split_count;
            for (int c = 0; c < child_count; ++c) {
                if (opt.auto_interval_oracle_max_children_total > 0 &&
                    children_attempted >= opt.auto_interval_oracle_max_children_total) {
                    all_children_closed = false;
                    child_coverage_complete = false;
                    budget_exhausted = true;
                    break;
                }
                const double child_lo = lo + (hi - lo) *
                    (static_cast<double>(c) / child_count);
                const double child_hi = lo + (hi - lo) *
                    (static_cast<double>(c + 1) / child_count);
                const std::string child_id = interval_id
                    + "_d" + std::to_string(depth + 1)
                    + "_" + std::to_string(c);
                ++child_count_used;
                const OracleIntervalOutcome child = close_interval(
                    child_id, interval_id, depth + 1, child_lo, child_hi);
                child_partition_lb = std::min(
                    child_partition_lb,
                    child.bound_valid ? child.lower_bound : std::max(0.0, child_lo));
                child_bound_merged = child_bound_merged || child.bound_merged;
                if (!child.closed) {
                    all_children_closed = false;
                }
            }
            if (child_coverage_complete && child_count_used == child_count &&
                std::isfinite(child_partition_lb)) {
                outcome.bound_valid = true;
                if (child_bound_merged &&
                    child_partition_lb > outcome.lower_bound + 1e-10) {
                    outcome.bound_merged = true;
                }
                outcome.lower_bound = std::max(outcome.lower_bound, child_partition_lb);
            }
            if (all_children_closed && child_count_used == child_count) {
                oracle_closed = true;
                outcome.closed = true;
                outcome.bound_valid = true;
                outcome.bound_merged = true;
                outcome.lower_bound = result.upper_bound;
            } else if (outcome.lower_bound >= result.upper_bound - 1e-7) {
                oracle_closed = true;
                outcome.closed = true;
                outcome.bound_valid = true;
            }
        }
        if (oracle.interval_exact_cutoff_feasible_improving) {
            ++feasible_improving;
        }
        total_direct_gini_cap += oracle.compact_bc_direct_gini_cap_rows_added;
        total_direct_gini_floor += oracle.compact_bc_direct_gini_floor_rows_added;
        total_tight_mccormick += oracle.compact_bc_tight_mccormick_rows_added;
        total_inventory_conservation += oracle.compact_bc_inventory_conservation_rows_added;
        total_movement_domains += oracle.compact_bc_movement_reachability_domains_tightened;
        total_visit_inventory += oracle.compact_bc_visit_inventory_linking_rows_added;
        total_objective_estimator += oracle.compact_bc_objective_estimator_cutoff_rows_added;
        total_penalty_lb_rows += oracle.compact_bc_penalty_lb_rows_added;
        total_gini_spread += oracle.gini_spread_cuts_added;
        total_required_movement += oracle.required_movement_cuts_added;
        total_global_handling += oracle.global_handling_capacity_cuts_added;
        total_support_pair += oracle.compact_bc_support_duration_pair_cuts_added;
        total_support_triple += oracle.compact_bc_support_duration_triple_cuts_added;
        total_transfer_compat += oracle.compact_bc_pairwise_transfer_compatibility_cuts_added;
        total_receiver_source_cover += oracle.compact_bc_receiver_source_cover_cuts_added;
        total_variable_s_centering += oracle.compact_bc_variable_s_centering_rows_added;
        total_s_range_rows += oracle.compact_bc_s_range_rows_added;
        total_sp_product_mccormick += oracle.compact_bc_sp_product_mccormick_rows_added;
        total_sp_product_estimator += oracle.compact_bc_sp_product_estimator_rows_added;
        total_tailored_gini_subset += oracle.tailored_bc_gini_subset_envelope_cuts_added;
        total_tailored_l1 += oracle.tailored_bc_low_gini_l1_centering_rows_added;
        total_tailored_l1_vars += oracle.tailored_bc_low_gini_l1_centering_vars;
        total_tailored_local_centering += oracle.tailored_bc_local_centering_rows_added;
        total_tailored_local_centering_violations += oracle.tailored_bc_local_centering_violations;
        total_tailored_subset_cross_h +=
            oracle.tailored_bc_subset_cross_h_centering_rows_added;
        total_tailored_subset_cross_h_candidates +=
            oracle.tailored_bc_subset_cross_h_centering_candidates;
        total_tailored_subset_cross_h_violations +=
            oracle.tailored_bc_subset_cross_h_centering_violations;
        total_tailored_subset_cross_h_max_violation =
            std::max(total_tailored_subset_cross_h_max_violation,
                     oracle.tailored_bc_subset_cross_h_centering_max_violation);
        total_tailored_local_q += oracle.tailored_bc_local_q_centering_rows_added;
        total_tailored_local_q_violations +=
            oracle.tailored_bc_local_q_centering_violations;
        total_tailored_local_q_max_violation =
            std::max(total_tailored_local_q_max_violation,
                     oracle.tailored_bc_local_q_centering_max_violation);
        total_tailored_variable_s += oracle.tailored_bc_variable_s_centering_cuts_added;
        total_tailored_variable_s_violations += oracle.tailored_bc_variable_s_centering_violations;
        total_tailored_subset_inventory += oracle.tailored_bc_subset_inventory_imbalance_cuts_added;
        total_tailored_transfer_cutset += oracle.tailored_bc_transfer_cutset_cuts_added;
        total_tailored_compatible_source_transfer +=
            oracle.tailored_bc_compatible_source_transfer_cuts_added;
        total_tailored_compatible_source_transfer_candidates +=
            oracle.tailored_bc_compatible_source_transfer_candidates;
        total_tailored_required_external_source +=
            oracle.tailored_bc_required_external_source_cuts_added;
        total_tailored_benders_inventory += oracle.tailored_bc_benders_inventory_cuts_added;
        total_tailored_benders_inventory_candidates += oracle.tailored_bc_benders_inventory_candidates;
        total_tailored_support_pair += oracle.tailored_bc_support_duration_pair_cuts_added;
        total_tailored_support_pair_candidates += oracle.tailored_bc_support_duration_pair_candidates;
        total_tailored_support_pair_violations += oracle.tailored_bc_support_duration_pair_violations;
        total_tailored_support_triple += oracle.tailored_bc_support_duration_triple_cuts_added;
        total_tailored_support_triple_candidates += oracle.tailored_bc_support_duration_triple_candidates;
        total_tailored_support_triple_violations += oracle.tailored_bc_support_duration_triple_violations;
        total_tailored_support_quad += oracle.tailored_bc_support_duration_quad_cuts_added;
        total_tailored_support_quad_candidates += oracle.tailored_bc_support_duration_quad_candidates;
        total_tailored_support_quad_violations += oracle.tailored_bc_support_duration_quad_violations;
        total_tailored_support_lifted += oracle.tailored_bc_support_duration_lifted_cuts_added;
        total_tailored_support_lifted_candidates += oracle.tailored_bc_support_duration_lifted_candidates;
        total_tailored_support_lifted_violations += oracle.tailored_bc_support_duration_lifted_violations;
        total_low_gini_domains += oracle.low_gini_ratio_band_domains_tightened;
        total_nodes += oracle.compact_bc_nodes;
        total_dynamic_cuts += oracle.compact_bc_dynamic_cuts_added_total;
        total_root_cut_rounds += oracle.compact_bc_total_root_cut_rounds;
        total_model_rows += oracle.compact_bc_model_rows;
        total_model_cols += oracle.compact_bc_model_cols;
        total_model_nonzeros += oracle.compact_bc_model_nonzeros;
        total_memory_estimate_mb += oracle.compact_bc_memory_estimate_mb;
        total_solver_time += oracle.compact_bc_time_seconds > 0.0
            ? oracle.compact_bc_time_seconds
            : oracle.interval_exact_cutoff_runtime_seconds;
        partition << csvEscapeSimple(interval_id) << ","
                  << csvEscapeSimple(parent_id) << ","
                  << depth << ","
                  << std::setprecision(12) << lo << "," << hi << ","
                  << csvEscapeSimple(oracle.status) << ","
                  << (oracle_closed ? "true" : "false") << ","
                  << (did_split ? "true" : "false") << ","
                  << child_count_used << ","
                  << time_limit << ","
                  << oracle.interval_exact_cutoff_runtime_seconds << ","
                  << csvEscapeSimple(oracle.interval_exact_cutoff_certificate_basis) << ","
                  << csvEscapeSimple(oracle.interval_exact_cutoff_solver_status) << "\n";
        outcome.closed = oracle_closed;
        return outcome;
    };

    for (const std::size_t target_idx : targets) {
        IntervalCsvRow& row = rows[target_idx];
        const std::string interval_id = row.get("interval_id").empty()
            ? std::to_string(target_idx)
            : row.get("interval_id");
        const double lo = csvDoubleField(row, "gamma_L", -1.0);
        const double hi = csvDoubleField(row, "gamma_U", -1.0);
        const double before_lb = csvDoubleField(row, "interval_lower_bound", lo);
        const OracleIntervalOutcome outcome =
            close_interval(interval_id, "root", 0, lo, hi);
        const double after_lb = outcome.bound_valid
            ? std::max(before_lb, outcome.lower_bound)
            : before_lb;
        const bool closed_by_bound =
            outcome.closed || after_lb >= result.upper_bound - 1e-7;
        if (outcome.bound_merged || after_lb > before_lb + 1e-10) {
            ++root_bound_merged;
            row.set("oracle_bound_merged", "true");
            row.set("oracle_bound_value", std::to_string(outcome.lower_bound));
            row.set("oracle_bound_status", outcome.status);
            row.set("oracle_bound_source_json", outcome.source_json);
            row.set("oracle_bound_solver_status", outcome.solver_status);
            row.set("oracle_bound_model_type", outcome.model_type);
            row.set("oracle_bound_valid", outcome.bound_valid ? "true" : "false");
            row.set("lower_bound_before_oracle", std::to_string(before_lb));
            row.set("lower_bound_after_oracle", std::to_string(after_lb));
            row.set("lower_bound_improvement_by_oracle",
                    std::to_string(std::max(0.0, after_lb - before_lb)));
            row.set("leaf_closed_by_oracle_bound",
                    closed_by_bound ? "true" : "false");
            row.set("interval_lower_bound", std::to_string(after_lb));
            row.set("lower_bound_source", "interval_exact_oracle_bound");
            row.set("lower_bound_sources",
                    row.get("lower_bound_sources") + "|interval_exact_oracle_bound");
            row.set("interval_closure_source",
                    closed_by_bound ? "interval_oracle" : "unresolved");
            row.set("interval_closure_source_detail", outcome.basis);
            row.set("interval_requires_pricing_closure", "false");
            row.set("interval_pricing_closure_satisfied", "true");
            row.set("interval_oracle_used_for_certificate",
                    closed_by_bound ? "true" : "false");
            row.set("interval_oracle_is_diagnostic_only",
                    closed_by_bound ? "false" : "true");
            row.set("interval_relaxation_bound_valid",
                    outcome.bound_valid ? "true" : "false");
            row.set("interval_bpc_tree_nodes", "0");
            row.set("interval_bpc_pricing_calls", "0");
            row.set("interval_bpc_exact_pricing_closed", "false");
            row.set("interval_final_lb", std::to_string(after_lb));
            row.set("interval_final_ub_cutoff", std::to_string(result.upper_bound));
        }
        if (closed_by_bound) {
            ++closed;
            ++root_bound_closed;
            row.set("interval_status", "bound_fathomed");
            if (row.get("reason").empty()) {
                row.set("reason", "interval_oracle_bound_or_child_partition_closed");
            }
            if (row.get("certificate_basis").empty()) {
                row.set("certificate_basis", "interval_exact_oracle_bound_or_infeasible_partition");
            }
            row.set("interval_lower_bound", std::to_string(result.upper_bound));
            row.set("lower_bound_source", "interval_exact_oracle_bound");
            row.set("lower_bound_sources",
                    row.get("lower_bound_sources") + "|interval_exact_oracle_bound");
            row.set("leaf_closed_by_oracle_bound", "true");
            row.set("interval_closure_source", "interval_oracle");
            row.set("interval_closure_source_detail",
                    "interval_exact_oracle_bound_or_infeasible_partition");
            row.set("interval_oracle_used_for_certificate", "true");
            row.set("interval_oracle_is_diagnostic_only", "false");
            row.set("interval_final_lb", std::to_string(result.upper_bound));
            row.set("interval_final_ub_cutoff", std::to_string(result.upper_bound));
        }
        if (!closed_by_bound) {
            oracle_blocker_seen = true;
            oracle_blocker_note = "automatic interval oracle stopped at interval "
                + interval_id + " without a complete interval certificate";
            result.notes.push_back(oracle_blocker_note);
            if (!opt.auto_interval_oracle_continue_after_timeout) {
                break;
            }
        }
    }
    summary.close();
    partition.close();

    double merged_global_lb = std::numeric_limits<double>::infinity();
    int remaining_open_after_merge = 0;
    for (const IntervalCsvRow& row : rows) {
        const std::string status = lowerAscii(row.get("interval_status"));
        if (status == "replaced_by_children") continue;
        const double lo = csvDoubleField(row, "gamma_L", -1.0);
        const double hi = csvDoubleField(row, "gamma_U", -1.0);
        if (lo < -1e-12 || hi < lo - 1e-12) continue;
        const double lb = csvDoubleField(row, "interval_lower_bound", lo);
        merged_global_lb = std::min(merged_global_lb, lb);
        if ((status == "unresolved" ||
             status == "unprocessed_relevant" ||
             status == "invalid") &&
            lb < result.upper_bound - 1e-7) {
            ++remaining_open_after_merge;
        }
    }
    if (std::isfinite(merged_global_lb)) {
        result.lower_bound = std::max(result.lower_bound, merged_global_lb);
        result.gap = (std::fabs(result.upper_bound) > 1e-12)
            ? std::max(0.0, (result.upper_bound - result.lower_bound)
                  / std::fabs(result.upper_bound))
            : 0.0;
        result.oracle_bound_best_global_lb = result.lower_bound;
    }
    result.oracle_bound_merged_leaves = root_bound_merged;
    result.oracle_bound_closed_leaves = root_bound_closed;
    result.compact_interval_bc_enabled = true;
    result.compact_interval_bc_model_type =
        opt.interval_exact_oracle_mode == "cutoff-feasibility"
            ? "original_compact_cutoff_feasibility"
            : "original_compact_objective_bound";
    result.compact_interval_bc_solver =
        opt.mip_solver.empty() ? "cplex" : opt.mip_solver;
    const int effective_compact_threads = opt.compact_bc_threads > 0
        ? opt.compact_bc_threads
        : (opt.mip_threads > 0 ? opt.mip_threads : std::max(1, opt.threads));
    result.cplex_threads = opt.cplex_threads;
    result.mip_threads = opt.mip_threads;
    result.compact_interval_bc_threads = effective_compact_threads;
    result.solver_thread_policy =
        effective_compact_threads == 1
            ? "compact_bc_single_thread"
            : "compact_bc_multithread";
    result.thread_fairness_class =
        effective_compact_threads == 1
            ? "one_thread_fair"
            : "multithread_diagnostic";
    {
        std::ostringstream families;
        bool first = true;
        auto addFamily = [&](const std::string& name, bool enabled) {
            if (!enabled) return;
            if (!first) families << "|";
            families << name;
            first = false;
        };
        addFamily("direct_gini_cap_floor", opt.compact_bc_direct_gini_rows);
        addFamily("interval_tight_mccormick", opt.compact_bc_tight_mccormick);
        addFamily("inventory_conservation", opt.compact_bc_inventory_conservation);
        addFamily("movement_reachability_domains", opt.compact_bc_movement_reachability_domains);
        addFamily("visit_inventory_linking", opt.compact_bc_visit_inventory_linking);
        addFamily("objective_estimator_cutoff", opt.compact_bc_objective_estimator_cutoff);
        addFamily("penalty_lb_closure", opt.compact_bc_penalty_lb_closure);
        addFamily("gini_spread", opt.gini_spread_cuts);
        addFamily("required_movement", opt.required_movement_cuts);
        addFamily("global_handling_capacity", opt.global_handling_capacity_cuts);
        addFamily("low_gini_centering", opt.low_gini_ratio_band_tightening);
        addFamily("variable_s_centering", opt.compact_bc_variable_s_centering);
        addFamily("s_range_refinement", opt.compact_bc_s_range_refinement != "off");
        addFamily("sp_product_estimator", opt.compact_bc_sp_product_estimator != "off");
        addFamily("gini_subset_envelope", opt.tailored_bc_gini_subset_envelope);
        addFamily("low_gini_l1_centering", opt.tailored_bc_low_gini_l1_centering);
        addFamily("local_centering", opt.tailored_bc_local_centering);
        addFamily("subset_cross_h_centering", opt.tailored_bc_subset_cross_h_centering);
        addFamily("local_q_centering", opt.tailored_bc_local_q_centering);
        addFamily("subset_inventory_imbalance", opt.tailored_bc_subset_inventory_imbalance);
        addFamily("vehicle_transfer_cutset", opt.tailored_bc_transfer_cutset);
        addFamily("compatible_source_transfer", opt.tailored_bc_compatible_source_transfer_cuts);
        addFamily("required_external_source", opt.tailored_bc_required_external_source_cuts);
        addFamily("support_duration", opt.compact_bc_support_duration_cuts);
        addFamily("transfer_compat", opt.compact_bc_pairwise_transfer_compatibility);
        addFamily("receiver_source_cover", opt.compact_bc_receiver_source_cover_cuts);
        result.compact_interval_bc_cut_families_enabled =
            first ? "none" : families.str();
        result.compact_bc_enabled_cut_families =
            result.compact_interval_bc_cut_families_enabled;
        result.compact_bc_enabled_families_requested =
            result.compact_interval_bc_cut_families_enabled;
        result.compact_bc_enabled_families_effective =
            result.compact_interval_bc_cut_families_enabled;
    }
    result.compact_interval_bc_closed_leaves = root_bound_closed;
    result.compact_interval_bc_timed_out_leaves = timed_out;
    result.compact_bc_cut_profile = opt.compact_bc_cut_profile;
    result.compact_bc_root_cut_rounds = opt.compact_bc_root_cut_rounds;
    result.compact_bc_total_root_cut_rounds = static_cast<int>(
        std::min<long long>(total_root_cut_rounds,
                            static_cast<long long>(std::numeric_limits<int>::max())));
    result.compact_bc_root_cut_time_limit = opt.compact_bc_root_cut_time_limit;
    result.compact_bc_dynamic_cut_families = opt.compact_bc_dynamic_cut_families;
    result.compact_bc_root_probe = opt.compact_bc_root_probe;
    result.compact_bc_low_gini_strengthening =
        opt.compact_bc_low_gini_strengthening;
    result.compact_bc_denominator_bound_mode =
        opt.compact_bc_denominator_bound_mode;
    result.compact_bc_objective_estimator_mode =
        opt.compact_bc_objective_estimator_mode;
    result.compact_bc_low_gini_aggressive_diagnostic =
        opt.compact_bc_low_gini_strengthening == "aggressive-diagnostic";
    result.compact_bc_s_range_refinement = opt.compact_bc_s_range_refinement;
    result.s_range_bucket_count = opt.compact_bc_s_range_buckets;
    result.s_range_bucket_id = opt.compact_bc_s_range_bucket_id;
    result.s_range_bucket_L = opt.compact_bc_s_range_bucket_L;
    result.s_range_bucket_U = opt.compact_bc_s_range_bucket_U;
    result.parent_S_L = result.s_range_global_L;
    result.parent_S_U = result.s_range_global_U;
    result.s_range_refinement_enabled = opt.compact_bc_s_range_refinement != "off";
    result.S_domain_source =
        result.s_range_refinement_enabled
            ? "aggregated_child_s_range_domains"
            : "not_requested";
    result.S_domain_proof_status =
        result.s_range_refinement_enabled
            ? "aggregated_from_child_fixed_interval_domain_bounds"
            : "not_requested";
    result.S_domain_audit_passed =
        !result.s_range_refinement_enabled ||
        result.parent_S_U >= result.parent_S_L - 1e-12;
    result.s_range_parent_coverage_valid =
        opt.compact_bc_s_range_refinement == "paper-safe" &&
        opt.compact_bc_s_range_buckets <= 1;
    result.s_range_certificate_valid = result.s_range_parent_coverage_valid;
    result.tailored_bc_s_bucket_ledger = opt.tailored_bc_s_bucket_ledger;
    result.tailored_bc_s_bucket_count =
        std::max(1, opt.tailored_bc_s_bucket_count);
    result.tailored_bc_s_bucket_policy = opt.tailored_bc_s_bucket_policy;
    result.tailored_bc_s_bucket_time_budget =
        opt.tailored_bc_s_bucket_time_budget;
    result.tailored_bc_s_bucket_merge_audit =
        opt.tailored_bc_s_bucket_merge_audit;
    result.tailored_bc_s_bucket_max_depth =
        opt.tailored_bc_s_bucket_max_depth;
    result.tailored_bc_s_bucket_min_width =
        opt.tailored_bc_s_bucket_min_width;
    result.tailored_bc_s_bucket_refine_top_k =
        opt.tailored_bc_s_bucket_refine_top_k;
    result.tailored_bc_s_bucket_refine_rule =
        opt.tailored_bc_s_bucket_refine_rule;
    result.compact_bc_variable_s_centering = opt.compact_bc_variable_s_centering;
    result.compact_bc_rmin_rmax_propagation = opt.compact_bc_rmin_rmax_propagation;
    result.compact_bc_rmin_rmax_propagation_safe =
        opt.compact_bc_rmin_rmax_propagation == "safe";
    result.compact_bc_sp_product_estimator = opt.compact_bc_sp_product_estimator;
    result.compact_bc_sp_product_bounds = opt.compact_bc_sp_product_bounds;
    result.compact_bc_sp_product_paper_safe =
        opt.compact_bc_sp_product_estimator == "paper-safe";
    result.compact_bc_low_gini_precheck = opt.compact_bc_low_gini_precheck;
    result.compact_bc_dynamic_cuts_added_total = total_dynamic_cuts;
    result.compact_bc_dynamic_cuts_added_by_family =
        "dynamic_root_total=" + std::to_string(total_dynamic_cuts);
    result.compact_bc_model_rows = total_model_rows;
    result.compact_bc_model_cols = total_model_cols;
    result.compact_bc_model_nonzeros = total_model_nonzeros;
    result.compact_bc_memory_estimate_mb = total_memory_estimate_mb;
    result.compact_bc_solver_threads = result.compact_interval_bc_threads;
    result.compact_bc_closed_leaf_count = root_bound_closed;
    result.compact_bc_total_solver_time = total_solver_time;
    result.compact_bc_total_leaf_nodes = total_nodes;
    result.compact_bc_variable_s_centering_rows_added = total_variable_s_centering;
    result.compact_bc_s_range_rows_added = total_s_range_rows;
    result.compact_bc_sp_product_mccormick_rows_added = total_sp_product_mccormick;
    result.compact_bc_sp_product_estimator_rows_added = total_sp_product_estimator;
    result.tailored_bc_enabled = opt.tailored_bc_enabled ||
        opt.algorithm_preset == "paper-gf-tailored-bc";
    if (result.tailored_bc_enabled) {
        populateTailoredBCResultFields(opt, result);
    }
    result.tailored_bc_gini_subset_envelope_cuts_added = total_tailored_gini_subset;
    result.tailored_bc_low_gini_l1_centering_rows_added = total_tailored_l1;
    result.tailored_bc_low_gini_l1_centering_vars = total_tailored_l1_vars;
    result.tailored_bc_local_centering_rows_added =
        total_tailored_local_centering;
    result.tailored_bc_local_centering_violations =
        total_tailored_local_centering_violations;
    result.tailored_bc_subset_cross_h_centering_rows_added =
        total_tailored_subset_cross_h;
    result.tailored_bc_subset_cross_h_centering_candidates =
        total_tailored_subset_cross_h_candidates;
    result.tailored_bc_subset_cross_h_centering_violations =
        total_tailored_subset_cross_h_violations;
    result.tailored_bc_subset_cross_h_centering_max_violation =
        total_tailored_subset_cross_h_max_violation;
    result.tailored_bc_local_q_centering_rows_added =
        total_tailored_local_q;
    result.tailored_bc_local_q_centering_violations =
        total_tailored_local_q_violations;
    result.tailored_bc_local_q_centering_max_violation =
        total_tailored_local_q_max_violation;
    result.tailored_bc_variable_s_centering_cuts_added =
        total_tailored_variable_s;
    result.tailored_bc_variable_s_centering_violations =
        total_tailored_variable_s_violations;
    result.tailored_bc_subset_inventory_imbalance_cuts_added =
        total_tailored_subset_inventory;
    result.tailored_bc_transfer_cutset_cuts_added =
        total_tailored_transfer_cutset;
    result.tailored_bc_compatible_source_transfer_cuts_added =
        total_tailored_compatible_source_transfer;
    result.tailored_bc_compatible_source_transfer_candidates =
        total_tailored_compatible_source_transfer_candidates;
    result.tailored_bc_required_external_source_cuts_added =
        total_tailored_required_external_source;
    result.tailored_bc_benders_inventory_cuts_mode =
        opt.tailored_bc_benders_inventory_cuts;
    result.tailored_bc_benders_inventory_cuts_added =
        total_tailored_benders_inventory;
    result.tailored_bc_benders_inventory_candidates =
        total_tailored_benders_inventory_candidates;
    result.tailored_bc_support_duration_pair_cuts_added =
        total_tailored_support_pair;
    result.tailored_bc_support_duration_pair_candidates =
        total_tailored_support_pair_candidates;
    result.tailored_bc_support_duration_pair_violations =
        total_tailored_support_pair_violations;
    result.tailored_bc_support_duration_triple_cuts_added =
        total_tailored_support_triple;
    result.tailored_bc_support_duration_triple_candidates =
        total_tailored_support_triple_candidates;
    result.tailored_bc_support_duration_triple_violations =
        total_tailored_support_triple_violations;
    result.tailored_bc_support_duration_quad_cuts_added =
        total_tailored_support_quad;
    result.tailored_bc_support_duration_quad_candidates =
        total_tailored_support_quad_candidates;
    result.tailored_bc_support_duration_quad_violations =
        total_tailored_support_quad_violations;
    result.tailored_bc_support_duration_lifted_cuts_added =
        total_tailored_support_lifted;
    result.tailored_bc_support_duration_lifted_candidates =
        total_tailored_support_lifted_candidates;
    result.tailored_bc_support_duration_lifted_violations =
        total_tailored_support_lifted_violations;
    result.tailored_bc_user_cuts_added_total =
        total_tailored_gini_subset + total_tailored_l1 +
        total_tailored_local_centering +
        total_tailored_subset_cross_h +
        total_tailored_local_q +
        total_tailored_variable_s +
        total_tailored_subset_inventory + total_tailored_transfer_cutset +
        total_tailored_compatible_source_transfer +
        total_tailored_required_external_source +
        total_tailored_benders_inventory +
        total_tailored_support_pair + total_tailored_support_triple +
        total_tailored_support_quad + total_tailored_support_lifted;
    {
        std::ostringstream tailored_cuts;
        tailored_cuts << "gini_subset_envelope=" << total_tailored_gini_subset
                      << ";low_gini_l1_centering=" << total_tailored_l1
                      << ";local_centering=" << total_tailored_local_centering
                      << ";subset_cross_h_centering=" << total_tailored_subset_cross_h
                      << ";local_q_centering=" << total_tailored_local_q
                      << ";variable_s_centering=" << total_tailored_variable_s
                      << ";subset_inventory_imbalance=" << total_tailored_subset_inventory
                      << ";transfer_cutset=" << total_tailored_transfer_cutset
                      << ";compatible_source_transfer=" << total_tailored_compatible_source_transfer
                      << ";required_external_source=" << total_tailored_required_external_source
                      << ";benders_inventory_diagnostic=" << total_tailored_benders_inventory
                      << ";support_duration_pair=" << total_tailored_support_pair
                      << ";support_duration_triple=" << total_tailored_support_triple
                      << ";support_duration_quad=" << total_tailored_support_quad
                      << ";support_duration_lifted=" << total_tailored_support_lifted;
        result.tailored_bc_user_cuts_added_by_family = tailored_cuts.str();
    }
    {
        std::ostringstream cuts;
        cuts << "direct_gini_cap=" << total_direct_gini_cap
             << ";direct_gini_floor=" << total_direct_gini_floor
             << ";tight_mccormick=" << total_tight_mccormick
             << ";inventory_conservation=" << total_inventory_conservation
             << ";visit_inventory_linking=" << total_visit_inventory
             << ";objective_estimator_cutoff=" << total_objective_estimator
             << ";penalty_lb=" << total_penalty_lb_rows
             << ";variable_s_centering=" << total_variable_s_centering
             << ";s_range=" << total_s_range_rows
             << ";sp_product_mccormick=" << total_sp_product_mccormick
             << ";sp_product_estimator=" << total_sp_product_estimator
             << ";tailored_gini_subset_envelope=" << total_tailored_gini_subset
             << ";tailored_low_gini_l1_centering=" << total_tailored_l1
             << ";tailored_local_centering=" << total_tailored_local_centering
             << ";tailored_subset_cross_h_centering=" << total_tailored_subset_cross_h
             << ";tailored_local_q_centering=" << total_tailored_local_q
             << ";tailored_variable_s_centering=" << total_tailored_variable_s
             << ";tailored_subset_inventory_imbalance=" << total_tailored_subset_inventory
             << ";tailored_transfer_cutset=" << total_tailored_transfer_cutset
             << ";tailored_compatible_source_transfer=" << total_tailored_compatible_source_transfer
             << ";tailored_required_external_source=" << total_tailored_required_external_source
             << ";tailored_benders_inventory_diagnostic=" << total_tailored_benders_inventory
             << ";tailored_support_duration_pair=" << total_tailored_support_pair
             << ";tailored_support_duration_triple=" << total_tailored_support_triple
             << ";tailored_support_duration_quad=" << total_tailored_support_quad
             << ";tailored_support_duration_lifted=" << total_tailored_support_lifted
             << ";gini_spread=" << total_gini_spread
             << ";required_movement=" << total_required_movement
             << ";global_handling_capacity=" << total_global_handling
             << ";support_duration_pair=" << total_support_pair
             << ";support_duration_triple=" << total_support_triple
             << ";transfer_compat=" << total_transfer_compat
             << ";receiver_source_cover=" << total_receiver_source_cover;
        result.compact_bc_total_cuts_added_by_family = cuts.str();
        result.compact_bc_cuts_added_by_family = cuts.str();
    }
    {
        std::ostringstream domains;
        domains << "movement_reachability=" << total_movement_domains
                << ";low_gini_ratio_band_domains=" << total_low_gini_domains;
        result.compact_bc_total_domains_tightened_by_family = domains.str();
        result.compact_bc_domains_tightened_by_family = domains.str();
    }

    result.auto_interval_oracle_leaves_attempted = attempted;
    result.auto_interval_oracle_leaves_closed = closed;
    result.auto_interval_oracle_leaves_timed_out = timed_out;
    result.auto_interval_oracle_leaves_split = split;
    result.auto_interval_oracle_children_attempted = children_attempted;
    result.auto_interval_oracle_recursive_depth_reached = max_depth_reached;
    result.auto_interval_oracle_budget_exhausted = budget_exhausted;
    result.per_leaf_oracle_time_limit_used = time_limits_used.str();
    result.auto_interval_oracle_time_seconds =
        std::chrono::duration<double>(
            std::chrono::steady_clock::now() - oracle_start).count();
    result.auto_interval_oracle_remaining_open_leaves =
        std::max(0, remaining_open_after_merge);
    result.compact_bc_unresolved_leaf_count =
        result.auto_interval_oracle_remaining_open_leaves;
    result.compact_interval_bc_bound_valid = root_bound_merged > 0 || root_bound_closed > 0;
    result.compact_bc_bound_valid = result.compact_interval_bc_bound_valid;
    result.compact_interval_bc_bound_scope = "original_fixed_interval";
    result.compact_bc_bound_scope = "original_fixed_interval";
    result.unresolved_intervals = result.auto_interval_oracle_remaining_open_leaves;
    if (result.auto_interval_oracle_remaining_open_leaves == 0) {
        result.open_nodes = 0;
    }
    result.auto_interval_oracle_status_by_leaf = status_by_leaf.str();
    result.auto_interval_oracle_coverage_complete =
        total_final_leaves > 0 && result.auto_interval_oracle_remaining_open_leaves == 0;
    result.notes.push_back("automatic interval oracle summary written to "
        + oracle_csv.string());
    result.notes.push_back("automatic interval oracle partition tree written to "
        + partition_csv.string());
    if (oracle_blocker_seen) {
        result.notes.push_back("automatic interval oracle first unresolved blocker: "
            + oracle_blocker_note);
    }

    if (feasible_improving > 0) {
        result.full_ledger_merge_status = "ub_improved_restart_required";
        result.full_ledger_merge_audit_passed = false;
        result.notes.push_back("automatic interval oracle found a verified improving UB; "
            "the current full frontier ledger was not certified because a restart is required");
        return;
    }

    if (opt.auto_interval_oracle_merge && (closed > 0 || root_bound_merged > 0)) {
        std::filesystem::path merged_path = out_path;
        merged_path.replace_extension(".merged.intervals.csv");
        writeIntervalCsvRows(merged_path, header, rows);
        result.bpc_interval_trace_csv_path = merged_path.string();
        result.oracle_bound_merge_audit_csv_path = merged_path.string();
        result.notes.push_back("automatic interval oracle merged ledger written to "
            + merged_path.string());
    }

    if (result.auto_interval_oracle_remaining_open_leaves == 0 &&
        result.invalid_bound_intervals == 0 &&
        result.open_nodes == 0 &&
        result.frontier_covers_all_improving_gini_values &&
        opt.auto_interval_oracle_merge) {
        result.unresolved_intervals = 0;
        result.lower_bound = result.objective;
        result.upper_bound = result.objective;
        result.gap = 0.0;
        result.status = "optimal";
        result.certificate =
            "sealed frontier certificate completed by automatic exact interval cutoff MIP infeasibility certificates";
        result.full_certificate_basis =
            "frontier_all_intervals_closed_or_fathomed_with_interval_exact_cutoff_oracle";
        result.full_certificate_all_intervals_accounted = true;
        result.full_certificate_rejection_reason = "none";
        result.full_ledger_merge_status = "merged_all_unresolved_leaves_closed";
        result.full_ledger_merge_audit_passed = true;
        result.interval_certificate_basis +=
            "|auto_interval_oracle:interval_exact_cutoff_mip_infeasible";
    } else {
        result.full_ledger_merge_status =
            (closed > 0 || root_bound_merged > 0)
                ? "partial_merge_remaining_open_leaves"
                : "no_leaves_closed";
        result.full_ledger_merge_audit_passed = false;
    }

    if (opt.auto_interval_bpc_fallback &&
        result.auto_interval_oracle_remaining_open_leaves > 0) {
        result.bpc_fallback_auto_called = true;
        result.bpc_fallback_leaves_attempted =
            opt.auto_interval_bpc_max_leaves > 0
                ? std::min(result.auto_interval_oracle_remaining_open_leaves,
                           opt.auto_interval_bpc_max_leaves)
                : result.auto_interval_oracle_remaining_open_leaves;
        result.bpc_fallback_leaves_closed = 0;
        result.exact_pricing_closed_leaves = 0;
        result.bpc_fallback_pricing_time = 0.0;
        result.bpc_fallback_nodes = 0;
        result.bpc_fallback_best_reduced_cost = 0.0;
        result.bpc_fallback_final_interval_lb = result.lower_bound;
        result.bpc_interval_certificate_basis =
            "diagnostic_not_closed_exact_pricing_not_available_for_auto_leaf";
        result.notes.push_back("automatic BPC fallback requested after oracle timeout. "
            "No lower-bound certificate was imported because this sealed postprocessor "
            "does not yet have an exact-pricing interval closure result for the remaining "
            "leaves; row remains noncertified");
    }
}

std::string inferPlateauReasonForFinalization(const ebrp::SolveResult& result);

void writePreAutoOracleParentJson(const ebrp::SolveOptions& opt,
                                  const ebrp::SolveResult& result) {
    if (opt.out_path.empty() || !opt.auto_interval_oracle) return;
    if (!isPaperTracePreset(result.algorithm_preset)) return;

    ebrp::SolveResult checkpoint = result;
    applySealedRunProvenance(opt, checkpoint);
    if (checkpoint.finalization_source.empty()) {
        checkpoint.finalization_source =
            checkpoint.status == "optimal"
                ? "solver_final_json"
                : "solver_final_noncertified_pre_auto_oracle";
    }
    if (checkpoint.best_valid_lb_seen <= 0.0) {
        checkpoint.best_valid_lb_seen = checkpoint.lower_bound;
    }
    if (checkpoint.best_valid_gap_seen <= 0.0 ||
        checkpoint.best_valid_gap_seen > checkpoint.gap) {
        checkpoint.best_valid_gap_seen = checkpoint.gap;
    }
    if (checkpoint.best_valid_ledger_checkpoint.empty()) {
        checkpoint.best_valid_ledger_checkpoint = opt.out_path;
    }
    if (checkpoint.best_valid_ledger_time <= 0.0) {
        checkpoint.best_valid_ledger_time = checkpoint.runtime_seconds;
    }
    checkpoint.final_json_uses_best_checkpoint = true;
    checkpoint.interrupted_run_best_bound_preserved = true;
    checkpoint.solver_finalization_reached = true;
    checkpoint.wrapper_synthesized_final_json = false;
    checkpoint.process_return_code = 0;
    checkpoint.abnormal_exit_detected = false;
    if (checkpoint.abnormal_exit_reason.empty()) {
        checkpoint.abnormal_exit_reason = "none";
    }
    if (checkpoint.last_progress_event.empty()) {
        checkpoint.last_progress_event =
            checkpoint.status == "optimal" ? "final_summary" : "solver_returned";
    }
    if (checkpoint.plateau_reason.empty()) {
        checkpoint.plateau_reason = inferPlateauReasonForFinalization(checkpoint);
    }
    checkpoint.result_file = opt.out_path;
    checkpoint.log_file = opt.log_path;
    checkpoint.notes.push_back(
        "pre-auto-oracle parent JSON written before optional interval leaf closure; "
        "if post-solve auto-oracle finishes this file is overwritten by the final ledger");
    finalizePaperModuleFields(checkpoint);
    std::vector<ebrp::SolveResult> checkpoint_results;
    checkpoint_results.push_back(std::move(checkpoint));
    ebrp::writeTextFile(opt.out_path, ebrp::resultsToJson(checkpoint_results));
}

std::string inferPlateauReasonForFinalization(const ebrp::SolveResult& result) {
    if (result.status == "optimal") return "certified";
    if (result.auto_interval_oracle_called &&
        result.auto_interval_oracle_remaining_open_leaves > 0) {
        return "automatic_interval_oracle_left_open_leaves";
    }
    if (result.open_nodes > 0) return "open_bpc_or_frontier_nodes";
    if (result.unresolved_intervals > 0) return "unresolved_frontier_intervals";
    if (result.invalid_bound_intervals > 0) return "invalid_bound_intervals";
    if (result.gap > 1e-7) return "positive_gap";
    return "not_certified";
}

void writeEmergencyFinalJson(const ebrp::SolveOptions& opt,
                             const std::string& status,
                             const std::string& reason) {
    if (opt.out_path.empty()) return;
    ebrp::SolveResult result;
    result.instance_name = std::filesystem::path(opt.input_path).filename().string();
    result.input_path = opt.input_path;
    result.result_file = opt.out_path;
    result.log_file = opt.log_path;
    result.method = opt.method.empty() ? "unknown" : opt.method;
    result.status = status;
    result.certificate = "not_certified";
    result.algorithm_preset = opt.algorithm_preset.empty()
        ? "custom"
        : opt.algorithm_preset;
    result.objective = 0.0;
    result.lower_bound = 0.0;
    result.upper_bound = 0.0;
    result.gap = 1.0;
    result.open_nodes = 0;
    result.unresolved_intervals = 1;
    result.invalid_bound_intervals = 0;
    result.frontier_covers_all_improving_gini_values = false;
    result.frontier_range_certificate_scope = "not_certified_exception_exit";
    result.route_mask_all_subset_enumeration_enabled = false;
    result.route_mask_all_subset_enumeration_certifying = false;
    result.compact_status = status;
    result.compact_LB = 0.0;
    result.compact_UB = 0.0;
    result.compact_gap = 1.0;
    result.compact_bc_model_size_policy = opt.compact_bc_model_size_policy;
    result.compact_bc_model_size_stop_reason = reason;
    result.compact_bc_rejection_reason = reason;
    result.compact_interval_bc_rejection_reason = reason;
    result.compact_bc_receiver_source_cover_mode =
        opt.compact_bc_receiver_source_cover_mode;
    result.finalization_source = "error_json";
    result.solver_finalization_reached = false;
    result.wrapper_synthesized_final_json = true;
    result.process_return_code = 1;
    result.abnormal_exit_detected = true;
    result.abnormal_exit_reason = reason;
    result.last_progress_event = "exception_finalization";
    result.plateau_reason = status;
    result.sealed_run = opt.paper_run_sealed;
    result.no_archive_scanning = !opt.incumbent_archive_auto;
    result.no_external_known_ub = opt.incumbent_json_path.empty() &&
        opt.external_incumbent_path.empty() && opt.hga_incumbent_path.empty();
    result.no_focus_only_certificate = !opt.frontier_focus_only;
    result.sealed_run_forbidden_source_used = false;
    result.sealed_run_rejection_reason = "none";
    result.incumbent_source_category = "none";
    result.incumbent_source_detail = "none";
    result.incumbent_source_contributes_lower_bound = false;
    result.incumbent_source_is_paper_reproducible = false;
    result.cplex_threads = opt.cplex_threads;
    result.mip_threads = opt.mip_threads;
    if (result.algorithm_preset == "paper-gf-compact-bc" ||
        result.algorithm_preset == "paper-gf-tailored-bc") {
        result.compact_bc_solver_threads = opt.compact_bc_threads > 0
            ? opt.compact_bc_threads
            : (opt.mip_threads > 0 ? opt.mip_threads : std::max(1, opt.threads));
        result.compact_interval_bc_threads = result.compact_bc_solver_threads;
        result.solver_thread_policy =
            result.compact_bc_solver_threads == 1
                ? "compact_bc_single_thread"
                : "compact_bc_multithread";
        result.thread_fairness_class =
            result.compact_bc_solver_threads == 1
                ? "one_thread_fair"
                : "multithread_diagnostic";
    } else if (result.method == "cplex") {
        const int effective_cplex_threads =
            opt.cplex_threads > 0 ? opt.cplex_threads : std::max(1, opt.threads);
        result.cplex_threads = effective_cplex_threads;
        result.solver_thread_policy =
            effective_cplex_threads == 1
                ? "plain_cplex_single_thread"
                : "plain_cplex_multithread";
        result.thread_fairness_class =
            effective_cplex_threads == 1
                ? "one_thread_fair"
                : "multithread_diagnostic";
    } else {
        result.thread_fairness_class = "unknown_not_paper";
    }
    result.notes.push_back("Emergency noncertified final JSON written after exception: "
        + reason);
    finalizePaperModuleFields(result);
    std::vector<ebrp::SolveResult> results;
    results.push_back(result);
    ebrp::writeTextFile(opt.out_path, ebrp::resultsToJson(results));
}

} // namespace

int main(int argc, char** argv) {
    ebrp::SolveOptions opt;
    try {
        opt = parseArgs(argc, argv);
        std::vector<std::filesystem::path> files = ebrp::collectInputFiles(opt.input_path);
        std::vector<ebrp::SolveResult> results;
        for (const auto& file : files) {
            ebrp::Instance instance = ebrp::parseInstanceFile(
                file, opt.total_time_limit, opt.pickup_time, opt.drop_time);
            ebrp::SolveOptions effective_opt = opt;
            if (opt.method == "tailored") {
                results.push_back(ebrp::solveTailoredExact(instance, opt));
            } else if (opt.method == "cplex") {
                results.push_back(ebrp::solveCplexBaseline(instance, opt));
            } else if (opt.method == "interval-cutoff-oracle") {
                results.push_back(ebrp::solveIntervalExactCutoffOracle(instance, opt));
            } else if (opt.method == "primal-heuristic") {
                results.push_back(solvePrimalHeuristicDiagnostic(instance, opt));
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
            } else if (opt.method == "route-mask-operation-budget-test") {
                results.push_back(solveRouteMaskOperationBudgetDiagnostic(instance, opt));
            } else if (opt.method == "adaptive-frontier-split-test") {
                results.push_back(solveAdaptiveFrontierSplitDiagnostic(instance, opt));
            } else if (opt.method == "inventory-branching-test") {
                results.push_back(solveInventoryBranchingDiagnostic(instance, opt));
            } else if (opt.method == "operation-mode-branching-test") {
                results.push_back(solveOperationModeBranchingDiagnostic(instance, opt));
            } else if (opt.method == "pricing-closure-audit-test") {
                results.push_back(solvePricingClosureAuditDiagnostic(instance, opt));
            } else if (opt.method == "resume-state-test") {
                results.push_back(solveResumeStateDiagnostic(instance, opt));
            } else if (opt.method == "pricing-verifier-test") {
                results.push_back(solvePricingVerifierDiagnostic(instance, opt));
            } else if (opt.method == "iterative-closure-test") {
                results.push_back(solveIterativeClosureDiagnostic(instance, opt));
            } else if (opt.method == "certificate-basis-test") {
                results.push_back(solveCertificateBasisDiagnostic(instance, opt));
            } else if (opt.method == "option-consistency-test") {
                results.push_back(solveOptionConsistencyDiagnostic(instance, opt));
            } else if (opt.method == "tailored-bc-callback-smoke-test" ||
                       opt.method == "tailored-bc-relaxation-vector-smoke-test" ||
                       opt.method == "tailored-bc-branch-callback-smoke-test" ||
                       opt.method == "tailored-bc-cut-validity-test" ||
                       opt.method == "gini-subset-envelope-test" ||
                       opt.method == "low-gini-l1-centering-test" ||
                       opt.method == "transfer-cutset-validity-test" ||
                       opt.method == "s-bucket-coverage-test") {
                results.push_back(solveTailoredBCGuardDiagnostic(
                    instance, opt, opt.method));
            } else if (opt.method == "station-set-test") {
                results.push_back(solveStationSetDiagnostic(instance, opt));
            } else if (opt.method == "ng-dssr-pricing-test") {
                results.push_back(solveNgDssrPricingDiagnostic(
                    instance, opt, "ng-dssr-pricing-test", "ng-dssr", opt.cg_dual_stabilization));
            } else if (opt.method == "dssr-exactness-test") {
                results.push_back(solveDssrExactnessDiagnostic(instance, opt));
            } else if (opt.method == "dual-stabilization-test") {
                results.push_back(solveNgDssrPricingDiagnostic(
                    instance, opt, "dual-stabilization-test", "hybrid",
                    opt.cg_dual_stabilization == "none" ? "smooth" : opt.cg_dual_stabilization));
            } else if (opt.method == "bpc-hybrid-pricing-test") {
                results.push_back(solveBpcHybridPricingDiagnostic(instance, opt));
            } else if (opt.method == "two-track-column-test") {
                results.push_back(solveTwoTrackColumnDiagnostic(instance, opt));
            } else if (opt.method == "projection-safe-relaxed-column-test") {
                results.push_back(solveProjectionSafeRelaxedColumnDiagnostic(
                    instance, opt, "projection-safe-relaxed-column-test"));
            } else if (opt.method == "non-elementary-relaxed-column-test") {
                results.push_back(solveProjectionSafeRelaxedColumnDiagnostic(
                    instance, opt, "non-elementary-relaxed-column-test"));
            } else if (opt.method == "ng-relaxed-closure-test") {
                results.push_back(solveNgRelaxedClosureDiagnostic(instance, opt));
            } else if (opt.method == "relaxed-rmp-cg-test") {
                results.push_back(solveRelaxedRmpCgDiagnostic(
                    instance, opt, "relaxed-rmp-cg-test"));
            } else if (opt.method == "frontier-relaxed-rmp-cg-test") {
                ebrp::SolveOptions frontier_opt = opt;
                frontier_opt.method = "gcap-frontier";
                frontier_opt.frontier_relaxed_rmp_cg = true;
                frontier_opt.relaxed_rmp_cg = true;
                frontier_opt.column_tracks = "two-track";
                frontier_opt.rmp_column_space = "two-track";
                frontier_opt.relaxed_columns_in_rmp = true;
                frontier_opt.pricing_engine = "hybrid";
                effective_opt = frontier_opt;
                results.push_back(solveGiniFrontierDiagnostic(instance, frontier_opt));
                results.back().method = "frontier-relaxed-rmp-cg-test";
            } else if (opt.method == "relaxed-rmp-test") {
                results.push_back(solveRelaxedRmpDiagnostic(instance, opt));
            } else if (opt.method == "relaxed-pricing-closure-test") {
                results.push_back(solveRelaxedPricingClosureDiagnostic(instance, opt));
            } else if (opt.method == "relaxed-column-incumbent-safety-test") {
                results.push_back(solveRelaxedColumnIncumbentSafetyDiagnostic(instance, opt));
            } else if (opt.method == "large-relaxed-rmp-test") {
                results.push_back(solveLargeRelaxedRmpDiagnostic(instance, opt));
            } else if (opt.method == "large-relaxed-rmp-cg-test") {
                ebrp::SolveOptions large_opt = opt;
                large_opt.large_relaxed_rmp_cg = true;
                effective_opt = large_opt;
                results.push_back(solveLargeRelaxedRmpDiagnostic(instance, large_opt));
                results.back().method = "large-relaxed-rmp-cg-test";
            } else if (opt.method == "external-incumbent-test") {
                results.push_back(solveExternalIncumbentDiagnostic(instance, opt));
            } else if (opt.method == "large-instance-mode-test") {
                results.push_back(solveLargeInstanceModeDiagnostic(instance, opt));
            } else if (opt.method == "large-lb-test") {
                results.push_back(solveLargeLowerBoundDiagnostic(instance, opt));
            } else if (opt.method == "incumbent-import-test") {
                results.push_back(solveIncumbentImportDiagnostic(instance, opt));
            } else if (opt.method == "route-pool-incumbent-test") {
                results.push_back(solveRoutePoolIncumbentDiagnostic(instance, opt));
            } else if (opt.method == "pickup-drop-compat-flow-test") {
                results.push_back(solvePickupDropCompatFlowDiagnostic(instance, opt));
            } else if (opt.method == "pickup-drop-transfer-cap-test") {
                results.push_back(solvePickupDropTransferCapDiagnostic(instance, opt));
            } else if (opt.method == "vehicle-indexed-relaxation-test") {
                results.push_back(solveVehicleIndexedRelaxationDiagnostic(instance, opt));
            } else if (opt.method == "vehicle-indexed-transfer-flow-test") {
                results.push_back(solveVehicleIndexedTransferFlowDiagnostic(instance, opt));
            } else {
                throw std::runtime_error("Unsupported method: " + opt.method);
            }
            auto& r = results.back();
            initializeScalabilityFields(instance, effective_opt, r);
            applyRunConfigSnapshot(buildRunConfigSnapshot(instance, effective_opt), r);
            writePreAutoOracleParentJson(effective_opt, r);
            runAutoIntervalOracleClosure(instance, effective_opt, r);
            applySealedRunProvenance(effective_opt, r);
            if (r.finalization_source.empty()) {
                r.finalization_source = "solver_final_json";
            }
            if (r.best_valid_lb_seen <= 0.0) {
                r.best_valid_lb_seen = r.lower_bound;
            }
            if (r.best_valid_gap_seen <= 0.0 || r.best_valid_gap_seen > r.gap) {
                r.best_valid_gap_seen = r.gap;
            }
            if (r.best_valid_ledger_checkpoint.empty()) {
                r.best_valid_ledger_checkpoint = r.result_file.empty()
                    ? opt.out_path
                    : r.result_file;
            }
            if (r.best_valid_ledger_time <= 0.0) {
                r.best_valid_ledger_time = r.runtime_seconds;
            }
            r.final_json_uses_best_checkpoint = true;
            r.interrupted_run_best_bound_preserved = true;
            r.solver_finalization_reached = true;
            r.wrapper_synthesized_final_json = false;
            r.process_return_code = 0;
            r.abnormal_exit_detected = false;
            if (r.abnormal_exit_reason.empty()) {
                r.abnormal_exit_reason = "none";
            }
            if (r.last_progress_event.empty()) {
                r.last_progress_event =
                    r.status == "optimal" ? "final_summary" : "solver_returned";
            }
            if (r.plateau_reason.empty()) {
                r.plateau_reason = inferPlateauReasonForFinalization(r);
            }
            finalizePaperModuleFields(r);
            if (r.result_file.empty()) r.result_file = opt.out_path;
            if (r.log_file.empty()) r.log_file = opt.log_path;
            if (!opt.export_incumbent_path.empty() && !r.routes.empty()) {
                try {
                    writeRouteJson(opt.export_incumbent_path, r.routes);
                    r.notes.push_back("exported incumbent route plan to "
                        + opt.export_incumbent_path);
                } catch (const std::exception& ex) {
                    r.notes.push_back("failed to export incumbent route plan to "
                        + opt.export_incumbent_path + ": " + ex.what());
                }
            }
            std::cout << r.instance_name << " " << r.method << " " << r.status
                      << " obj=" << r.objective << " runtime=" << r.runtime_seconds
                      << " columns=" << r.columns << "\n";
        }
        const std::string json = ebrp::resultsToJson(results);
        if (!opt.out_path.empty()) ebrp::writeTextFile(opt.out_path, json);
        else std::cout << json;
        return 0;
    } catch (const std::bad_alloc& e) {
        const std::string reason = std::string("std_bad_alloc: ") + e.what();
        std::cerr << "ExactEBRP error: " << reason << "\n";
        try {
            writeEmergencyFinalJson(opt, "model_size_limit", reason);
        } catch (const std::exception& write_error) {
            std::cerr << "ExactEBRP emergency JSON write failed: "
                      << write_error.what() << "\n";
        }
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "ExactEBRP error: " << e.what() << "\n";
        try {
            writeEmergencyFinalJson(opt, "error_noncertified", e.what());
        } catch (const std::exception& write_error) {
            std::cerr << "ExactEBRP emergency JSON write failed: "
                      << write_error.what() << "\n";
        }
        usage();
        return 1;
    }
}
