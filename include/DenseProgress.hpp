#pragma once

#include <cstddef>
#include <filesystem>
#include <limits>
#include <string>
#include <vector>

namespace ebrp {

struct DenseProgressReadOnlyPolicy {
    bool may_add_rows = false;
    bool may_branch = false;
    bool may_reject_candidate = false;
    bool may_abort = false;
    bool may_change_parameters = false;
    bool may_call_auxiliary_optimizer = false;
};

struct DenseProgressConfig {
    bool enabled = false;
    std::filesystem::path raw_event_path;
    std::string run_id;
    std::string algorithm;
    std::string flow_variant;
    std::string executable_sha256;
    long long model_rows = 0;
    long long model_columns = 0;
    long long model_nonzeros = 0;
    bool verified_upper_bound_available = false;
    double verified_upper_bound = 0.0;
    std::size_t maximum_retained_records = 500000;
    long long material_node_delta = 100;
    long long material_open_node_delta = 100;
};

struct DenseProgressSnapshot {
    double observation_time_seconds = 0.0;
    bool deterministic_time_available = false;
    double deterministic_time = 0.0;
    long long callback_invocation_sequence = 0;
    std::string callback_context = "global_progress";
    std::string observation_source = "native_generic_callback";
    std::string phase = "unavailable";
    bool native_best_bound_available = false;
    double native_best_bound = 0.0;
    bool native_incumbent_available = false;
    double native_incumbent = 0.0;
    bool verified_upper_bound_available = false;
    double verified_upper_bound = 0.0;
    bool processed_nodes_available = false;
    long long processed_nodes = 0;
    bool open_nodes_available = false;
    long long open_nodes = 0;
    bool native_solution_count_available = false;
    long long native_solution_count = 0;
    bool simplex_iterations_available = false;
    long long simplex_iterations = 0;
    bool tree_memory_available = false;
    double tree_memory_mb = 0.0;
    long long gini_branch_count = 0;
    long long ordinary_branch_count = 0;
    long long current_open_gini_siblings = 0;
    bool gini_sibling_delay_available = false;
    double oldest_gini_sibling_delay_seconds = 0.0;
    double maximum_gini_sibling_delay_seconds = 0.0;
};

struct DenseProgressEvent : DenseProgressSnapshot {
    long long retained_event_sequence = 0;
    double scheduled_checkpoint_seconds = 0.0;
    double observation_age_seconds = 0.0;
    bool fresh_observation = false;
    std::string retention_trigger;
    bool project_gap_available = false;
    double project_gap = 0.0;
    bool native_cplex_gap_available = false;
    double native_cplex_gap = 0.0;
    bool last_lower_bound_improvement_time_available = false;
    double last_lower_bound_improvement_time = 0.0;
    bool first_incumbent_time_available = false;
    double first_incumbent_time = 0.0;
    bool first_gini_branch_time_available = false;
    double first_gini_branch_time = 0.0;
    bool first_ordinary_branch_time_available = false;
    double first_ordinary_branch_time = 0.0;
    bool root_completion_time_available = false;
    double root_completion_time = 0.0;
};

struct DenseProgressCheckpoint {
    double checkpoint_seconds = 0.0;
    bool observation_available = false;
    std::string freshness = "not_observed";
    double source_observation_time_seconds = 0.0;
    double observation_age_seconds = 0.0;
    DenseProgressEvent event;
};

struct DenseProgressStats {
    long long callback_invocation_count = 0;
    long long progress_record_count = 0;
    long long dropped_record_count = 0;
    double progress_callback_wall_seconds = 0.0;
    double serialization_seconds = 0.0;
    std::size_t peak_buffer_bytes = 0;
    bool final_record_appended = false;
    bool flush_succeeded = false;
    std::string flush_failure_reason = "not_flushed";
};

struct DenseProgressIntegrity {
    bool timestamps_strictly_increasing = true;
    bool lower_bound_nondecreasing = true;
    bool incumbent_nonincreasing = true;
    bool node_counters_consistent = true;
    bool final_record_present = false;
    long long error_count = 0;
    std::string errors;
};

DenseProgressReadOnlyPolicy denseProgressReadOnlyPolicy();
double denseHeartbeatCadenceSeconds(double elapsed_seconds);
std::vector<double> canonicalDenseCheckpointGrid(double horizon_seconds);
std::vector<DenseProgressCheckpoint> extractDenseProgressCheckpoints(
    const std::vector<DenseProgressEvent>& events,
    double horizon_seconds);
DenseProgressIntegrity auditDenseProgressEvents(
    const std::vector<DenseProgressEvent>& events,
    double lower_bound_api_noise_tolerance = 1e-7);

class DenseProgressRecorder {
public:
    explicit DenseProgressRecorder(DenseProgressConfig config);

    void noteCallbackInvocation(double instrumentation_seconds);
    bool observe(const DenseProgressSnapshot& snapshot, bool force = false,
                 const std::string& force_trigger = {});
    bool appendSolverFinal(const DenseProgressSnapshot& snapshot);
    bool flush();

    const DenseProgressConfig& config() const { return config_; }
    const std::vector<DenseProgressEvent>& events() const { return events_; }
    const DenseProgressStats& stats() const { return stats_; }

private:
    bool retainForChange(const DenseProgressSnapshot& snapshot,
                         std::string& trigger) const;
    void updateMilestones(DenseProgressEvent& event);

    DenseProgressConfig config_;
    DenseProgressStats stats_;
    std::vector<DenseProgressEvent> events_;
    double next_heartbeat_seconds_ = 0.0;
    bool final_seen_ = false;
    bool last_bound_available_ = false;
    double last_bound_ = -std::numeric_limits<double>::infinity();
    bool last_incumbent_available_ = false;
    double last_incumbent_ = std::numeric_limits<double>::infinity();
    bool last_nodes_available_ = false;
    long long last_nodes_ = 0;
    bool last_open_nodes_available_ = false;
    long long last_open_nodes_ = 0;
    bool last_solution_count_available_ = false;
    long long last_solution_count_ = 0;
    std::string last_phase_;
    long long last_gini_branches_ = 0;
    long long last_ordinary_branches_ = 0;
    bool last_lb_improvement_time_available_ = false;
    double last_lb_improvement_time_ = 0.0;
    bool first_incumbent_time_available_ = false;
    double first_incumbent_time_ = 0.0;
    bool first_gini_branch_time_available_ = false;
    double first_gini_branch_time_ = 0.0;
    bool first_ordinary_branch_time_available_ = false;
    double first_ordinary_branch_time_ = 0.0;
    bool root_completion_time_available_ = false;
    double root_completion_time_ = 0.0;
};

} // namespace ebrp
