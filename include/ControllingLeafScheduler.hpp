#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace ebrp {

enum class ControllingLeafStatus {
    Open,
    Closed,
    Fathomed,
    Empty,
    Invalid,
    Replaced
};

std::string controllingLeafStatusName(ControllingLeafStatus status);

struct ControllingLeafAttempt {
    int attempt_number = 0;
    double requested_quantum_seconds = 0.0;
    double effective_native_time_limit_seconds = 0.0;
    double actual_solver_time_seconds = 0.0;
    bool selected_while_controlling = false;
    std::string solver_status;
    double solver_final_best_bound = 0.0;
    bool solver_final_best_bound_valid = false;
    double checkpoint_best_bound = 0.0;
    bool checkpoint_best_bound_valid = false;
    std::string finalization_source;
};

struct ControllingLeaf {
    std::string id;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    std::string parent_id;
    int split_depth = 0;
    int child_index = -1;
    bool parent_child_coverage_valid = true;
    bool parent_replaced = false;
    double base_lower_bound = 0.0;
    double lower_bound = 0.0;
    std::vector<std::string> lower_bound_sources;
    ControllingLeafStatus status = ControllingLeafStatus::Open;
    double cutoff = 0.0;
    int exact_solver_attempt_count = 0;
    double cumulative_allocated_time_seconds = 0.0;
    double cumulative_solver_time_seconds = 0.0;
    double screening_time_seconds = 0.0;
    double time_while_controlling_seconds = 0.0;
    double time_while_noncontrolling_seconds = 0.0;
    double first_attempt_elapsed_seconds = -1.0;
    double last_attempt_elapsed_seconds = -1.0;
    double latest_solver_final_best_bound = 0.0;
    bool latest_solver_final_best_bound_valid = false;
    double latest_checkpoint_best_bound = 0.0;
    bool latest_checkpoint_best_bound_valid = false;
    std::uint64_t latest_checkpoint_sequence = 0;
    std::string latest_checkpoint_acceptance_status = "not_seen";
    std::string latest_checkpoint_rejection_reason = "not_seen";
    std::string latest_solver_final_status = "not_run";
    std::string closure_source;
    std::string instance_hash;
    std::string model_fingerprint;
    std::string formulation_profile;
    std::vector<ControllingLeafAttempt> attempts;
};

struct ControllingLeafSelection {
    bool available = false;
    std::string selected_leaf_id;
    std::vector<std::string> controlling_leaf_ids;
    std::vector<std::string> deterministic_tie_order;
    double global_lower_bound = 0.0;
    double competing_minimum_bound = 0.0;
    int tie_round = 0;
    int selection_position = -1;
    int next_attempt_number = 0;
    double requested_quantum_seconds = 0.0;
};

struct DeadlineLaunchDecision {
    bool launch_allowed = false;
    double requested_quantum_seconds = 0.0;
    double effective_native_time_limit_seconds = 0.0;
    double remaining_parent_time_seconds = 0.0;
    double finalization_reserve_seconds = 0.0;
    std::string rejection_reason;
};

class ControllingLeafScheduler {
public:
    explicit ControllingLeafScheduler(double certificate_tolerance = 1e-7);

    bool addLeaf(const ControllingLeaf& leaf, std::string* reason = nullptr);
    bool splitLeafAtomically(const std::string& parent_id,
                             const std::vector<ControllingLeaf>& children,
                             std::string* reason = nullptr);
    bool mergeValidLowerBound(const std::string& leaf_id,
                              double value,
                              const std::string& source,
                              std::string* reason = nullptr);
    bool setStatus(const std::string& leaf_id,
                   ControllingLeafStatus status,
                   const std::string& closure_source,
                   std::string* reason = nullptr);
    bool recordAttempt(const std::string& leaf_id,
                       const ControllingLeafAttempt& attempt,
                       double elapsed_start_seconds,
                       double elapsed_end_seconds,
                       std::string* reason = nullptr);

    const ControllingLeaf* findLeaf(const std::string& leaf_id) const;
    ControllingLeaf* findLeaf(const std::string& leaf_id);
    const std::vector<ControllingLeaf>& leaves() const;

    double globalLowerBound() const;
    std::vector<std::string> controllingSet() const;
    ControllingLeafSelection selectNext();
    bool everyRelevantLeafClosed() const;
    bool parentChildCoverageValid(std::string* reason = nullptr) const;
    bool leafBoundsMonotone() const;
    bool globalBoundMonotone() const;
    double certificateTolerance() const;

    static double requestedQuantumSeconds(int zero_based_attempt);
    static double finalizationReserveSeconds(double nominal_total_budget_seconds);
    static DeadlineLaunchDecision planLaunch(double requested_quantum_seconds,
                                             double remaining_parent_time_seconds,
                                             double reserve_seconds);

private:
    bool isRelevantFinalLeaf(const ControllingLeaf& leaf) const;
    bool isOpenRelevantLeaf(const ControllingLeaf& leaf) const;
    std::vector<std::string> orderedControllingSet(double* min_bound) const;
    void noteGlobalBound();

    double tolerance_ = 1e-7;
    std::vector<ControllingLeaf> leaves_;
    std::vector<double> global_bound_history_;
    bool leaf_bounds_monotone_ = true;
    bool global_bound_monotone_ = true;
    std::vector<std::string> active_tie_order_;
    double active_tie_bound_ = 0.0;
    std::size_t active_tie_cursor_ = 0;
    int active_tie_round_ = 0;
};

struct NativeCheckpointRecord {
    std::string run_id;
    std::uint64_t sequence = 0;
    std::string instance_hash;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double cutoff = 0.0;
    std::string objective_sense = "minimize";
    std::string model_fingerprint;
    std::string formulation_profile;
    int cplex_threads = 1;
    int native_time_limit_param_id = 1039;
    double native_time_limit_seconds = 0.0;
    int native_time_limit_set_rc = 0;
    double best_bound = 0.0;
    std::string bound_source = "cplex_native_best_bound";
    std::string model_type = "original_fixed_interval_compact_mip";
    bool original_objective_unchanged = true;
    bool complete = true;
    bool atomic_persistence_complete = true;
    bool forbidden_evidence_used = false;
};

struct NativeCheckpointExpectation {
    std::string run_id;
    std::uint64_t last_accepted_sequence = 0;
    std::string instance_hash;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    double cutoff = 0.0;
    std::string model_fingerprint;
    std::string formulation_profile;
    int cplex_threads = 1;
    int native_time_limit_param_id = 1039;
    double native_time_limit_seconds = 0.0;
};

struct NativeCheckpointValidation {
    bool accepted = false;
    std::string reason;
};

NativeCheckpointValidation validateNativeCheckpoint(
    const NativeCheckpointRecord& record,
    const NativeCheckpointExpectation& expected,
    double identity_tolerance = 1e-9);

bool writeNativeCheckpointAtomic(const std::filesystem::path& path,
                                 const NativeCheckpointRecord& record,
                                 std::string* reason = nullptr);

bool readNativeCheckpoint(const std::filesystem::path& path,
                          NativeCheckpointRecord& record,
                          std::string* reason = nullptr);

std::string stableFileFingerprint(const std::filesystem::path& path);

} // namespace ebrp
