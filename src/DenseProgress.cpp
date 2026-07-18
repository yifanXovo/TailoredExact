#include "DenseProgress.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>

namespace ebrp {
namespace {

std::string csvCell(const std::string& value) {
    if (value.find_first_of(",\"\n\r") == std::string::npos) return value;
    std::string out = "\"";
    for (char ch : value) out += ch == '"' ? "\"\"" : std::string(1, ch);
    out += '"';
    return out;
}

template <typename T>
void optional(std::ostream& out, bool available, T value) {
    if (available) out << value;
}

bool sameDouble(bool a_available, double a,
                bool b_available, double b) {
    if (a_available != b_available) return false;
    if (!a_available) return true;
    return a == b || (std::isnan(a) && std::isnan(b));
}

double relativeGap(double upper, double lower) {
    const double residual = std::max(0.0, upper - lower);
    return std::fabs(upper) > 1e-12
        ? residual / std::fabs(upper)
        : (residual == 0.0 ? 0.0
                           : std::numeric_limits<double>::infinity());
}

} // namespace

DenseProgressReadOnlyPolicy denseProgressReadOnlyPolicy() {
    return {};
}

double denseHeartbeatCadenceSeconds(double elapsed_seconds) {
    if (elapsed_seconds < 60.0) return 1.0;
    if (elapsed_seconds < 300.0) return 5.0;
    if (elapsed_seconds < 900.0) return 10.0;
    return 30.0;
}

std::vector<double> canonicalDenseCheckpointGrid(double horizon_seconds) {
    static const double grid[] = {
        1, 2, 5, 10, 15, 20, 30, 45,
        60, 90, 120, 180, 240, 300,
        450, 600, 750, 900,
        1200, 1500, 1800,
        2400, 3000, 3600
    };
    std::vector<double> out;
    for (double checkpoint : grid) {
        if (checkpoint <= horizon_seconds + 1e-9) out.push_back(checkpoint);
    }
    return out;
}

std::vector<DenseProgressCheckpoint> extractDenseProgressCheckpoints(
    const std::vector<DenseProgressEvent>& events,
    double horizon_seconds) {
    std::vector<DenseProgressCheckpoint> out;
    std::size_t next_event = 0;
    const DenseProgressEvent* latest = nullptr;
    for (double checkpoint : canonicalDenseCheckpointGrid(horizon_seconds)) {
        while (next_event < events.size() &&
               events[next_event].observation_time_seconds <=
                   checkpoint + 1e-12) {
            latest = &events[next_event++];
        }
        DenseProgressCheckpoint row;
        row.checkpoint_seconds = checkpoint;
        if (latest != nullptr) {
            row.observation_available = true;
            row.source_observation_time_seconds =
                latest->observation_time_seconds;
            row.observation_age_seconds = std::max(
                0.0, checkpoint - latest->observation_time_seconds);
            row.event = *latest;
            row.freshness = row.observation_age_seconds <=
                    denseHeartbeatCadenceSeconds(checkpoint) + 1e-9
                ? "fresh" : "stale";
        }
        out.push_back(std::move(row));
    }
    return out;
}

DenseProgressIntegrity auditDenseProgressEvents(
    const std::vector<DenseProgressEvent>& events) {
    DenseProgressIntegrity out;
    std::vector<std::string> errors;
    for (std::size_t index = 0; index < events.size(); ++index) {
        const DenseProgressEvent& event = events[index];
        if (index > 0) {
            const DenseProgressEvent& previous = events[index - 1];
            if (!(event.observation_time_seconds >
                  previous.observation_time_seconds)) {
                out.timestamps_strictly_increasing = false;
                errors.push_back("timestamp_not_strictly_increasing");
            }
            if (event.native_best_bound_available &&
                previous.native_best_bound_available &&
                event.native_best_bound < previous.native_best_bound) {
                out.lower_bound_nondecreasing = false;
                ++out.lower_bound_negative_step_count;
                out.lower_bound_max_negative_step = std::max(
                    out.lower_bound_max_negative_step,
                    previous.native_best_bound - event.native_best_bound);
            }
            if (event.native_incumbent_available &&
                previous.native_incumbent_available &&
                event.native_incumbent > previous.native_incumbent) {
                out.incumbent_nonincreasing = false;
                ++out.incumbent_positive_step_count;
                out.incumbent_max_positive_step = std::max(
                    out.incumbent_max_positive_step,
                    event.native_incumbent - previous.native_incumbent);
            }
            if (event.processed_nodes_available &&
                previous.processed_nodes_available &&
                event.processed_nodes < previous.processed_nodes) {
                out.node_counters_consistent = false;
                ++out.processed_nodes_negative_step_count;
                out.processed_nodes_max_negative_step = std::max(
                    out.processed_nodes_max_negative_step,
                    previous.processed_nodes - event.processed_nodes);
            }
        }
        if (event.retention_trigger == "solver_final" &&
            event.observation_source == "solver_final_native_api") {
            out.final_record_present = true;
        }
    }
    if (!out.final_record_present) errors.push_back("solver_final_missing");
    out.error_count = static_cast<long long>(errors.size());
    std::ostringstream joined;
    for (std::size_t index = 0; index < errors.size(); ++index) {
        if (index) joined << '|';
        joined << errors[index];
    }
    out.errors = joined.str();
    return out;
}

DenseProgressRecorder::DenseProgressRecorder(DenseProgressConfig config)
    : config_(std::move(config)), next_heartbeat_seconds_(0.0) {
    if (config_.maximum_retained_records == 0) {
        config_.maximum_retained_records = 1;
    }
    events_.reserve(std::min<std::size_t>(
        config_.maximum_retained_records, 4096));
}

void DenseProgressRecorder::noteCallbackInvocation(
    double instrumentation_seconds) {
    ++stats_.callback_invocation_count;
    if (std::isfinite(instrumentation_seconds) &&
        instrumentation_seconds > 0.0) {
        stats_.progress_callback_wall_seconds += instrumentation_seconds;
    }
}

bool DenseProgressRecorder::retainForChange(
    const DenseProgressSnapshot& snapshot,
    std::string& trigger) const {
    if (events_.empty()) {
        trigger = "first_native_observation";
        return true;
    }
    if (!sameDouble(snapshot.native_best_bound_available,
                    snapshot.native_best_bound,
                    last_bound_available_, last_bound_)) {
        trigger = "best_bound_change";
        return true;
    }
    if (!sameDouble(snapshot.native_incumbent_available,
                    snapshot.native_incumbent,
                    last_incumbent_available_, last_incumbent_)) {
        trigger = "incumbent_change";
        return true;
    }
    if (snapshot.processed_nodes_available != last_nodes_available_ ||
        (snapshot.processed_nodes_available &&
         std::llabs(snapshot.processed_nodes - last_nodes_) >=
             std::max<long long>(1, config_.material_node_delta))) {
        trigger = "material_processed_node_change";
        return true;
    }
    if (snapshot.open_nodes_available != last_open_nodes_available_ ||
        (snapshot.open_nodes_available &&
         std::llabs(snapshot.open_nodes - last_open_nodes_) >=
             std::max<long long>(1, config_.material_open_node_delta))) {
        trigger = "material_open_node_change";
        return true;
    }
    if (snapshot.native_solution_count_available !=
            last_solution_count_available_ ||
        (snapshot.native_solution_count_available &&
         snapshot.native_solution_count != last_solution_count_)) {
        trigger = "solution_count_change";
        return true;
    }
    if (snapshot.phase != last_phase_) {
        trigger = "solver_phase_change";
        return true;
    }
    if (snapshot.gini_branch_count != last_gini_branches_) {
        trigger = "gini_branch_count_change";
        return true;
    }
    if (snapshot.ordinary_branch_count != last_ordinary_branches_) {
        trigger = "ordinary_branch_count_change";
        return true;
    }
    return false;
}

void DenseProgressRecorder::updateMilestones(DenseProgressEvent& event) {
    if (event.native_best_bound_available &&
        (!last_bound_available_ || event.native_best_bound > last_bound_)) {
        last_lb_improvement_time_available_ = true;
        last_lb_improvement_time_ = event.observation_time_seconds;
    }
    if (event.native_incumbent_available &&
        !first_incumbent_time_available_) {
        first_incumbent_time_available_ = true;
        first_incumbent_time_ = event.observation_time_seconds;
    }
    if (event.gini_branch_count > 0 &&
        !first_gini_branch_time_available_) {
        first_gini_branch_time_available_ = true;
        first_gini_branch_time_ = event.observation_time_seconds;
    }
    if (event.ordinary_branch_count > 0 &&
        !first_ordinary_branch_time_available_) {
        first_ordinary_branch_time_available_ = true;
        first_ordinary_branch_time_ = event.observation_time_seconds;
    }
    if (event.processed_nodes_available && event.processed_nodes > 0 &&
        !root_completion_time_available_) {
        root_completion_time_available_ = true;
        root_completion_time_ = event.observation_time_seconds;
    }
    event.last_lower_bound_improvement_time_available =
        last_lb_improvement_time_available_;
    event.last_lower_bound_improvement_time = last_lb_improvement_time_;
    event.first_incumbent_time_available = first_incumbent_time_available_;
    event.first_incumbent_time = first_incumbent_time_;
    event.first_gini_branch_time_available = first_gini_branch_time_available_;
    event.first_gini_branch_time = first_gini_branch_time_;
    event.first_ordinary_branch_time_available =
        first_ordinary_branch_time_available_;
    event.first_ordinary_branch_time = first_ordinary_branch_time_;
    event.root_completion_time_available = root_completion_time_available_;
    event.root_completion_time = root_completion_time_;
}

bool DenseProgressRecorder::observe(const DenseProgressSnapshot& snapshot,
                                    bool force,
                                    const std::string& force_trigger) {
    if (!config_.enabled && !force) return false;
    std::string trigger;
    const bool changed = retainForChange(snapshot, trigger);
    const bool heartbeat =
        snapshot.observation_time_seconds + 1e-12 >= next_heartbeat_seconds_;
    if (!force && !changed && !heartbeat) return false;
    if (force) trigger = force_trigger.empty() ? "forced" : force_trigger;
    else if (heartbeat && changed) trigger += "+heartbeat";
    else if (heartbeat) trigger = "heartbeat";

    if (events_.size() >= config_.maximum_retained_records && !force) {
        ++stats_.dropped_record_count;
        return false;
    }

    DenseProgressEvent event;
    static_cast<DenseProgressSnapshot&>(event) = snapshot;
    if (!events_.empty() && event.observation_time_seconds <=
            events_.back().observation_time_seconds) {
        event.observation_time_seconds = std::nextafter(
            events_.back().observation_time_seconds,
            std::numeric_limits<double>::infinity());
    }
    event.retained_event_sequence =
        static_cast<long long>(events_.size()) + 1;
    event.scheduled_checkpoint_seconds = heartbeat
        ? next_heartbeat_seconds_ : event.observation_time_seconds;
    event.observation_age_seconds = std::max(
        0.0, event.observation_time_seconds -
                 event.scheduled_checkpoint_seconds);
    event.fresh_observation = event.observation_age_seconds <=
        denseHeartbeatCadenceSeconds(event.scheduled_checkpoint_seconds) +
            1e-9;
    event.retention_trigger = trigger;
    if (snapshot.native_best_bound_available &&
        snapshot.verified_upper_bound_available) {
        event.project_gap_available = true;
        event.project_gap = relativeGap(snapshot.verified_upper_bound,
                                       snapshot.native_best_bound);
    }
    if (snapshot.native_best_bound_available &&
        snapshot.native_incumbent_available) {
        event.native_cplex_gap_available = true;
        event.native_cplex_gap = relativeGap(snapshot.native_incumbent,
                                            snapshot.native_best_bound);
    }
    updateMilestones(event);
    events_.push_back(event);

    last_bound_available_ = snapshot.native_best_bound_available;
    last_bound_ = snapshot.native_best_bound;
    last_incumbent_available_ = snapshot.native_incumbent_available;
    last_incumbent_ = snapshot.native_incumbent;
    last_nodes_available_ = snapshot.processed_nodes_available;
    last_nodes_ = snapshot.processed_nodes;
    last_open_nodes_available_ = snapshot.open_nodes_available;
    last_open_nodes_ = snapshot.open_nodes;
    last_solution_count_available_ =
        snapshot.native_solution_count_available;
    last_solution_count_ = snapshot.native_solution_count;
    last_phase_ = snapshot.phase;
    last_gini_branches_ = snapshot.gini_branch_count;
    last_ordinary_branches_ = snapshot.ordinary_branch_count;

    if (heartbeat) {
        double next = next_heartbeat_seconds_;
        do {
            next += denseHeartbeatCadenceSeconds(next);
        } while (next <= snapshot.observation_time_seconds + 1e-12);
        next_heartbeat_seconds_ = next;
    }
    stats_.progress_record_count = static_cast<long long>(events_.size());
    stats_.peak_buffer_bytes = std::max(
        stats_.peak_buffer_bytes,
        events_.capacity() * sizeof(DenseProgressEvent));
    return true;
}

bool DenseProgressRecorder::appendSolverFinal(
    const DenseProgressSnapshot& snapshot) {
    if (final_seen_) return false;
    final_seen_ = true;
    DenseProgressSnapshot final = snapshot;
    final.callback_context = "finalization";
    final.observation_source = "solver_final_native_api";
    final.phase = "finalization";
    const bool retained = observe(final, true, "solver_final");
    stats_.final_record_appended = retained;
    return retained;
}

bool DenseProgressRecorder::flush() {
    const auto start = std::chrono::steady_clock::now();
    if (!config_.enabled || config_.raw_event_path.empty()) {
        stats_.flush_failure_reason = "dense_progress_disabled_or_path_empty";
        return false;
    }
    try {
        if (config_.raw_event_path.has_parent_path()) {
            std::filesystem::create_directories(
                config_.raw_event_path.parent_path());
        }
        std::ofstream out(config_.raw_event_path,
                          std::ios::out | std::ios::trunc);
        if (!out) {
            stats_.flush_failure_reason = "raw_event_stream_open_failed";
            return false;
        }
        out << std::setprecision(std::numeric_limits<double>::max_digits10);
        out << "run_id,algorithm,flow_variant,retained_event_sequence,"
               "callback_invocation_sequence,observation_time_seconds,"
               "scheduled_checkpoint_seconds,observation_age_seconds,"
               "fresh_observation,observation_source,callback_context,phase,"
               "native_deterministic_time,native_best_bound,native_incumbent,"
               "verified_same_run_ub,project_gap,native_cplex_gap,processed_nodes,"
               "open_nodes,native_solution_count,simplex_iterations,tree_memory_mb,"
               "gini_branch_count,ordinary_branch_count,current_open_gini_siblings,"
               "oldest_gini_sibling_delay_seconds,maximum_gini_sibling_delay_seconds,"
               "last_valid_lower_bound_improvement_time,first_incumbent_time,"
               "first_gini_branch_time,first_ordinary_branch_time,root_completion_time,"
               "model_rows,model_columns,model_nonzeros,executable_sha256,"
               "retention_trigger\n";
        for (const DenseProgressEvent& event : events_) {
            out << csvCell(config_.run_id) << ','
                << csvCell(config_.algorithm) << ','
                << csvCell(config_.flow_variant) << ','
                << event.retained_event_sequence << ','
                << event.callback_invocation_sequence << ','
                << event.observation_time_seconds << ','
                << event.scheduled_checkpoint_seconds << ','
                << event.observation_age_seconds << ','
                << (event.fresh_observation ? "true" : "false") << ','
                << csvCell(event.observation_source) << ','
                << csvCell(event.callback_context) << ','
                << csvCell(event.phase) << ',';
            optional(out, event.deterministic_time_available,
                     event.deterministic_time); out << ',';
            optional(out, event.native_best_bound_available,
                     event.native_best_bound); out << ',';
            optional(out, event.native_incumbent_available,
                     event.native_incumbent); out << ',';
            optional(out, event.verified_upper_bound_available,
                     event.verified_upper_bound); out << ',';
            optional(out, event.project_gap_available, event.project_gap);
            out << ',';
            optional(out, event.native_cplex_gap_available,
                     event.native_cplex_gap); out << ',';
            optional(out, event.processed_nodes_available,
                     event.processed_nodes); out << ',';
            optional(out, event.open_nodes_available, event.open_nodes);
            out << ',';
            optional(out, event.native_solution_count_available,
                     event.native_solution_count); out << ',';
            optional(out, event.simplex_iterations_available,
                     event.simplex_iterations); out << ',';
            optional(out, event.tree_memory_available,
                     event.tree_memory_mb); out << ','
                << event.gini_branch_count << ','
                << event.ordinary_branch_count << ','
                << event.current_open_gini_siblings << ',';
            optional(out, event.gini_sibling_delay_available,
                     event.oldest_gini_sibling_delay_seconds); out << ',';
            optional(out, event.gini_sibling_delay_available,
                     event.maximum_gini_sibling_delay_seconds); out << ',';
            optional(out,
                     event.last_lower_bound_improvement_time_available,
                     event.last_lower_bound_improvement_time); out << ',';
            optional(out, event.first_incumbent_time_available,
                     event.first_incumbent_time); out << ',';
            optional(out, event.first_gini_branch_time_available,
                     event.first_gini_branch_time); out << ',';
            optional(out, event.first_ordinary_branch_time_available,
                     event.first_ordinary_branch_time); out << ',';
            optional(out, event.root_completion_time_available,
                     event.root_completion_time); out << ','
                << config_.model_rows << ',' << config_.model_columns << ','
                << config_.model_nonzeros << ','
                << csvCell(config_.executable_sha256) << ','
                << csvCell(event.retention_trigger) << '\n';
        }
        out.close();
        if (!out) {
            stats_.flush_failure_reason = "raw_event_stream_write_failed";
            return false;
        }
        stats_.flush_succeeded = true;
        stats_.flush_failure_reason = "none";
    } catch (const std::exception& ex) {
        stats_.flush_failure_reason = ex.what();
        stats_.flush_succeeded = false;
    }
    stats_.serialization_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - start).count();
    return stats_.flush_succeeded;
}

} // namespace ebrp
