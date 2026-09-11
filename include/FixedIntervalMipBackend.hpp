#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace ebrp {

enum class FixedIntervalSolveKind {
    LegacyMipQuantum,
    PaperLpRelaxation,
    PaperPartialBoundTargetMip,
    PaperTerminalMip
};

struct FixedIntervalNativeBoundEvent {
    double solver_runtime_seconds = 0.0;
    double work = 0.0;
    double native_bound = 0.0;
    bool native_bound_available = false;
    double native_incumbent = 0.0;
    bool native_incumbent_available = false;
    double processed_nodes = 0.0;
    double open_nodes = 0.0;
    int native_phase = 0;
    bool bound_improved = false;
    bool target_reached = false;
};

struct FixedIntervalCandidateEvent {
    long long event_sequence = 0;
    int callback_where = 0;
    std::string trigger;
    std::string source;
    std::string content_sha256;
    std::string mode = "off";
    std::string status = "not_attempted";
    bool generated = false;
    bool independently_verified = false;
    bool strictly_improves_frozen_cutoff = false;
    bool mapping_complete = false;
    bool bounds_valid = false;
    bool integrality_valid = false;
    bool linear_constraints_checked = false;
    bool linear_constraints_valid = false;
    long long linear_rows_checked = 0;
    long long violated_linear_rows = 0;
    double maximum_linear_violation = 0.0;
    bool submitted = false;
    int submission_return_code = -1;
    bool native_objective_returned = false;
    double native_objective = 0.0;
    std::string acceptance = "not_submitted";
    int objective_evaluations = 0;
    double callback_elapsed_seconds = 0.0;
    double generation_seconds = 0.0;
    double verification_seconds = 0.0;
    double mapping_seconds = 0.0;
    double residual_check_seconds = 0.0;
    double total_seconds = 0.0;
    double candidate_objective = 0.0;
};

struct FixedIntervalMipCapabilities {
    std::string backend;
    bool available = false;
    bool retained_same_leaf_resume = false;
    bool fresh_per_attempt = true;
    bool verified_complete_mip_start = false;
    bool native_continuation_evidence = false;
    bool exact_zero_gap_roundtrip = false;
    std::string failure_reason;
};

struct FixedIntervalMipRequest {
    FixedIntervalSolveKind solve_kind =
        FixedIntervalSolveKind::LegacyMipQuantum;
    std::string leaf_id;
    int attempt_number = 0;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double verified_cutoff = 0.0;
    double time_limit_seconds = 0.0;
    // For paper solves this is the remaining global experiment deadline. It
    // may only interrupt the complete external algorithm, never schedule a
    // different leaf or cause a retry.
    double global_deadline_remaining_seconds = 0.0;
    bool new_leaf = true;
    bool warm_start_enabled = false;
    std::filesystem::path canonical_model_path;
    std::string canonical_model_fingerprint;
    std::string canonical_model_scope;
    std::string canonical_row_signature;
    std::filesystem::path native_log_path;
    std::vector<RoutePlan> verified_start_routes;
    std::string verified_start_source;
    // Round 29 C4 keeps a leaf model only within that leaf's exact lifecycle.
    // This is model-object reuse, not native-tree or LP-basis reuse.
    bool incremental_model_reuse_enabled = false;
    bool retain_model_after_solve = false;
    // Round 30 C5 may terminate a native MIP only when a backend-certified
    // dual bound reaches this mathematical target. No time, Work, node,
    // solution, or attempt quantity participates in the target.
    bool native_bound_target_enabled = false;
    double native_bound_target = 0.0;
    double native_bound_target_tolerance = 1e-7;
    bool capture_native_bound_events = false;
    // Round 49 diagnostic/candidate modes may consume the primal/dual state
    // produced by this already-required LP solve.  This flag only copies
    // attributes after Optimize; it never launches another solve.
    bool capture_lp_primal_dual_evidence = false;
    // Round 50 uniform run-level backend policy.  It is never inferred from
    // the instance, dimensions, panel, solver progress, or machine state.
    std::string interval_mip_policy = "interval-mip-v0";
    // Round 51 A1 disposable child-LP probes. Overrides are applied only to
    // the freshly read model owned by this solve call and are read back before
    // Optimize. The immutable canonical LP artifact is never rewritten.
    struct VariableBoundOverride {
        std::string variable_name;
        bool lower_bound_enabled = false;
        double lower_bound = 0.0;
        bool upper_bound_enabled = false;
        double upper_bound = 0.0;
    };
    std::vector<VariableBoundOverride> variable_bound_overrides;
    // Round 51 A1 terminal sparse priorities. The backend assigns zero to all
    // variables and these exact positive values to the named originals.
    struct BranchPriorityOverride {
        std::string variable_name;
        int priority = 0;
    };
    std::vector<BranchPriorityOverride> branch_priority_overrides;
    // Round 54 external root closure rows. These are deterministic, already
    // validated inventory-route cuts added to a freshly read model before
    // either the LP relaxation or terminal MIP. The canonical artifact itself
    // is immutable and its fingerprint remains the request identity.
    struct AdditionalLinearRow {
        std::string row_name;
        std::vector<std::string> variable_names;
        std::vector<double> coefficients;
        char sense = '<';
        double rhs = 0.0;
        std::string canonical_signature;
        std::string scope = "global";
    };
    std::vector<AdditionalLinearRow> additional_linear_rows;
    // Default-off Round59: only already-proved integer-redundant rows.
    bool round59_additional_rows_user_pool = false;
    int round59_mip_focus = -1;
    std::filesystem::path round59_node_samples_path;
    // Round 60 default-off candidate construction and native injection.
    std::string round60_candidate_mode = "off"; // off|dry|inject
    int round60_candidate_maximum_evaluations = 512;
    int round60_candidate_maximum_stations = 16;
    std::filesystem::path round60_candidate_log_path;
    // Fixed-inventory diagnostic only. Empty means unrestricted.
    std::vector<int> round60_fixed_inventory;
};

struct FixedIntervalBranchPriorityEvidence {
    std::string variable_name;
    std::string semantic_family;
    char variable_type = 'C';
    int assigned_priority = 0;
};

struct FixedIntervalCutFamilyEvidence {
    std::string family;
    long long count = 0;
};

struct FixedIntervalLpVariableEvidence {
    std::string name;
    char original_type = 'C';
    double lower_bound = 0.0;
    double upper_bound = 0.0;
    double primal_value = 0.0;
    double reduced_cost = 0.0;
    int variable_basis_status = 0;
};

struct FixedIntervalLpConstraintEvidence {
    std::string name;
    double slack = 0.0;
    double dual_multiplier = 0.0;
    int constraint_basis_status = 0;
};

struct FixedIntervalMipOutcome {
    bool attempted = false;
    bool available = false;
    bool solver_finalization_reached = false;
    bool optimal = false;
    bool native_exact_optimal = false;
    bool native_tolerance_optimal = false;
    bool native_optimal_unscaled_infeasibilities = false;
    bool native_status_supported = false;
    bool lp_relaxation = false;
    bool lp_terminal_valid = false;
    bool terminal_mip = false;
    bool partial_bound_target_mip = false;
    bool infeasible = false;
    bool interrupted = false;
    bool native_bound_available = false;
    double native_bound = 0.0;
    bool native_bound_target_reached = false;
    bool native_bound_target_termination_requested = false;
    double native_bound_target = 0.0;
    std::vector<FixedIntervalNativeBoundEvent> native_bound_events;
    bool incumbent_available = false;
    bool incumbent_independently_verified = false;
    double incumbent_objective = 0.0;
    std::vector<RoutePlan> incumbent_routes;
    std::string native_status;
    int native_status_code = 0;
    int optimize_return_code = -1;
    double solver_runtime_seconds = 0.0;
    double work = 0.0;
    double nodes = 0.0;
    double simplex_iterations = 0.0;
    double barrier_iterations = 0.0;
    double memory_gb = 0.0;
    double model_build_seconds = 0.0;
    double model_read_seconds = 0.0;
    long long model_variable_count = 0;
    long long model_linear_constraint_count = 0;
    long long model_nonzero_count = 0;
    long long model_binary_variable_count = 0;
    long long model_integer_variable_count = 0;
    long long model_continuous_variable_count = 0;
    long long model_general_constraint_count = 0;
    bool presolved_model_size_available = false;
    long long presolved_row_count = 0;
    long long presolved_column_count = 0;
    long long presolved_nonzero_count = 0;
    bool lp_solution_diagnostics_available = false;
    bool lp_g_value_available = false;
    double lp_g_value = 0.0;
    bool lp_objective_value_available = false;
    double lp_objective_value = 0.0;
    bool lp_primal_values_available = false;
    bool lp_reduced_costs_available = false;
    bool lp_basis_status_available = false;
    bool lp_primal_dual_evidence_available = false;
    int lp_objective_sense = 0;
    double lp_verified_cutoff = 0.0;
    std::string lp_model_fingerprint;
    std::vector<FixedIntervalLpVariableEvidence>
        lp_primal_dual_variable_evidence;
    bool lp_constraint_slacks_available = false;
    bool lp_constraint_duals_available = false;
    bool lp_constraint_basis_status_available = false;
    bool lp_constraint_evidence_available = false;
    std::vector<FixedIntervalLpConstraintEvidence>
        lp_primal_dual_constraint_evidence;
    double route_binary_fractionality = 0.0;
    double visit_binary_fractionality = 0.0;
    double inventory_bit_fractionality = 0.0;
    double selector_binary_fractionality = 0.0;
    double mccormick_ambiguity = 0.0;
    double segmented_mccormick_ambiguity = 0.0;
    bool presolve_time_available = false;
    double presolve_time_seconds = 0.0;
    std::string presolve_time_status = "unavailable";
    bool root_time_available = false;
    double root_time_seconds = 0.0;
    std::string root_time_status = "unavailable";
    bool open_nodes_available = false;
    double open_nodes = 0.0;
    bool native_cut_count_available = false;
    long long native_cut_count = 0;
    bool exact_zero_gap_roundtrip = false;
    bool model_fingerprint_matches_request = false;
    bool feasibility_consistency_gate = true;
    bool same_leaf_model_retained = false;
    bool fresh_restart = false;
    bool child_restart = false;
    bool reset_called = false;
    bool native_continuation_claimed = false;
    bool native_continuation_evidence = false;
    bool native_model_modified = false;
    bool presolve_rerun_observed = false;
    bool root_relaxation_rerun_observed = false;
    bool incumbent_state_reused = false;
    bool in_memory_model_reused = false;
    bool integer_domain_restored = false;
    std::string basis_reuse_status = "not_requested";
    std::string retained_state_classification = "not_applicable";
    std::string native_log_path;
    double cumulative_runtime = 0.0;
    double cumulative_work = 0.0;
    double cumulative_nodes = 0.0;
    double cumulative_simplex_iterations = 0.0;
    double cumulative_barrier_iterations = 0.0;
    bool warm_start_candidate_available = false;
    bool warm_start_mapping_complete = false;
    bool warm_start_submitted = false;
    std::string warm_start_status = "not_requested";
    double warm_start_mapping_seconds = 0.0;
    std::string failure_reason;
    std::string interval_mip_policy = "interval-mip-v0";
    bool branch_priority_assignment_attempted = false;
    bool branch_priority_assignment_valid = false;
    long long branch_priority_assigned_count = 0;
    std::string branch_priority_assignment_status = "not_requested";
    std::vector<FixedIntervalBranchPriorityEvidence>
        branch_priority_evidence;
    long long branch_priority_zero_readback_count = 0;
    bool variable_bound_override_attempted = false;
    bool variable_bound_override_readback_valid = false;
    long long variable_bound_override_count = 0;
    std::string variable_bound_override_status = "not_requested";
    std::vector<FixedIntervalCutFamilyEvidence> root_cut_family_evidence;
    bool additional_linear_rows_attempted = false;
    bool additional_linear_rows_valid = false;
    long long additional_linear_rows_added = 0;
    std::string additional_linear_row_signatures;
    std::string additional_linear_rows_status = "not_requested";
    std::string tailored_cut_policy = "off";
    std::string round53_callback_mode = "off";
    long long round53_mipnode_calls = 0;
    long long round53_mipnode_status_reads = 0;
    long long round53_relaxation_vector_reads = 0;
    long long round53_separator_calls = 0;
    long long round53_cut_submission_calls = 0;
    double round53_callback_overhead_seconds = 0.0;
    bool tailored_cut_callback_active = false;
    bool tailored_cut_callback_disabled_after_failure = false;
    bool gurobi_cbcut_symbol_loaded = false;
    bool gurobi_cblazy_symbol_loaded = false;
    int gurobi_precrush_requested = -1;
    int gurobi_precrush_set_return_code = -1;
    int gurobi_precrush_get_return_code = -1;
    int gurobi_precrush_effective = -1;
    bool gurobi_precrush_roundtrip_valid = false;
    long long tailored_cut_callback_calls = 0;
    long long tailored_cut_root_callback_calls = 0;
    long long tailored_cut_tree_callback_calls = 0;
    long long tailored_cut_nonoptimal_mipnode_callbacks = 0;
    long long tailored_cut_relaxation_vector_failures = 0;
    long long tailored_cuts_generated = 0;
    long long tailored_cuts_violated = 0;
    long long tailored_cuts_selected = 0;
    long long tailored_cuts_added = 0;
    long long tailored_cut_duplicate_rejections = 0;
    long long tailored_cut_dominated_rejections = 0;
    long long tailored_cut_nonviolated_rejections = 0;
    long long tailored_cut_invalid_rejections = 0;
    long long tailored_cut_submission_failures = 0;
    long long tailored_cut_callback_failures = 0;
    long long tailored_cut_pool_size = 0;
    double tailored_cut_callback_overhead_seconds = 0.0;
    bool numerical_ranges_available = false;
    double minimum_matrix_coefficient = 0.0;
    double maximum_matrix_coefficient = 0.0;
    double minimum_objective_coefficient = 0.0;
    double maximum_objective_coefficient = 0.0;
    double minimum_variable_bound = 0.0;
    double maximum_variable_bound = 0.0;
    double minimum_rhs = 0.0;
    double maximum_rhs = 0.0;
    bool root_relaxation_bound_available = false;
    double root_relaxation_bound = 0.0;
    bool final_root_cut_bound_available = false;
    double final_root_cut_bound = 0.0;
    double root_work = 0.0;
    double root_runtime_seconds = 0.0;
    double root_simplex_iterations = 0.0;
    double first_incumbent_work = -1.0;
    double first_incumbent_runtime_seconds = -1.0;
    bool gurobi_cbsolution_symbol_loaded = false;
    std::string round60_candidate_mode = "off";
    bool round60_candidate_callback_active = false;
    bool round60_candidate_disabled_after_failure = false;
    long long round60_candidate_triggers = 0;
    long long round60_candidates_generated = 0;
    long long round60_candidates_verified = 0;
    long long round60_candidates_mapped = 0;
    long long round60_candidates_submitted = 0;
    long long round60_candidates_confirmed_accepted = 0;
    long long round60_candidates_acceptance_unknown = 0;
    double round60_best_generated_objective = 0.0;
    bool round60_best_generated_objective_available = false;
    double round60_candidate_overhead_seconds = 0.0;
    std::vector<FixedIntervalCandidateEvent> round60_candidate_events;
};

struct FixedIntervalMipBackendStats {
    int threads_requested = 1;
    int threads_set_return_code = -1;
    int threads_get_return_code = -1;
    int threads_effective = 0;
    int presolve_requested = -1;
    int presolve_set_return_code = -1;
    int presolve_get_return_code = -1;
    int presolve_effective = -2;
    int seed_requested = 0;
    int seed_set_return_code = -1;
    int seed_get_return_code = -1;
    int seed_effective = -1;
    double mip_gap_requested = 0.0;
    int mip_gap_set_return_code = -1;
    int mip_gap_get_return_code = -1;
    double mip_gap_effective = -1.0;
    double mip_gap_abs_requested = 0.0;
    int mip_gap_abs_set_return_code = -1;
    int mip_gap_abs_get_return_code = -1;
    double mip_gap_abs_effective = -1.0;
    bool parameter_roundtrip_valid = false;
    long long environment_count = 0;
    long long model_count = 0;
    long long model_read_count = 0;
    long long optimize_count = 0;
    long long lp_relaxation_optimize_count = 0;
    long long partial_bound_target_mip_optimize_count = 0;
    long long terminal_mip_optimize_count = 0;
    long long native_bound_event_count = 0;
    long long native_bound_target_reached_count = 0;
    long long model_free_count = 0;
    long long environment_free_count = 0;
    long long same_leaf_resume_count = 0;
    long long fresh_restart_count = 0;
    long long child_restart_count = 0;
    long long reset_call_count = 0;
    long long confirmed_continuation_count = 0;
    long long partial_state_reuse_count = 0;
    long long observed_fresh_restart_count = 0;
    long long ambiguous_retained_state_count = 0;
    long long presolve_execution_count = 0;
    long long root_relaxation_execution_count = 0;
    long long warm_start_candidate_count = 0;
    long long warm_start_complete_count = 0;
    long long warm_start_submitted_count = 0;
    long long warm_start_accepted_count = 0;
    long long warm_start_rejected_count = 0;
    long long warm_start_unknown_count = 0;
    long long in_memory_model_reuse_count = 0;
    long long explicit_leaf_model_discard_count = 0;
    long long integer_domain_restore_count = 0;
    long long basis_available_count = 0;
    long long basis_mapped_count = 0;
    long long basis_submitted_count = 0;
    long long basis_accepted_count = 0;
    long long basis_rejected_count = 0;
    double cumulative_model_build_seconds = 0.0;
    double cumulative_model_read_seconds = 0.0;
    double cumulative_solver_runtime_seconds = 0.0;
    double cumulative_work = 0.0;
    double cumulative_lp_work = 0.0;
    double cumulative_partial_bound_target_mip_work = 0.0;
    double cumulative_terminal_mip_work = 0.0;
    double cumulative_nodes = 0.0;
    double cumulative_simplex_iterations = 0.0;
    double cumulative_barrier_iterations = 0.0;
    double peak_memory_gb = 0.0;
};

class FixedIntervalMipBackend {
public:
    virtual ~FixedIntervalMipBackend() = default;
    virtual FixedIntervalMipCapabilities capabilities() const = 0;
    virtual FixedIntervalMipOutcome solve(
        const FixedIntervalMipRequest& request) = 0;
    virtual void discardLeaf(const std::string&) {}
    // Idempotently release native resources before the final statistics
    // snapshot when an evidence path must prove environment/model symmetry.
    virtual void release() {}
    virtual FixedIntervalMipBackendStats stats() const = 0;
};

std::unique_ptr<FixedIntervalMipBackend> makeCplexFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);
std::unique_ptr<FixedIntervalMipBackend> makeGurobiFixedIntervalBackend(
    const Instance& instance, const SolveOptions& options);

} // namespace ebrp
