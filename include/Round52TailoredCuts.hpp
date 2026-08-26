#pragma once

#include "Instance.hpp"

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

namespace ebrp {

enum class Round52CutValidityScope { Global, Local };
enum class Round52CutSense { LessEqual, GreaterEqual, Equal };
enum class Round52CutSeparationScope { RootOnly, AllOptimalTreeNodes };
enum class Round52CutSelectionRule { VehicleBlockMaximum, ParetoUndominated };

struct Round52SparseCoefficient {
    std::string variable;
    double value = 0.0;
};

struct Round52CutCandidate {
    std::string family;
    Round52CutValidityScope validity_scope =
        Round52CutValidityScope::Global;
    std::vector<Round52SparseCoefficient> coefficients;
    Round52CutSense sense = Round52CutSense::LessEqual;
    double rhs = 0.0;
    double raw_violation = 0.0;
    double scaled_violation = 0.0;
    double violation_scale = 1.0;
    std::string canonical_signature;
    std::string canonical_lhs_signature;
    std::string generating_interval;
    std::string generating_context;
    std::vector<int> support_set;
    int vehicle_index = -1;
    std::string derivation_metadata;
};

struct Round52CutSeparationInput {
    const Instance* instance = nullptr;
    std::unordered_map<std::string, double> lp_values;
    std::unordered_map<std::string, double> effective_lower_bounds;
    std::unordered_map<std::string, double> effective_upper_bounds;
    std::unordered_map<std::string, int> model_variable_mapping;
    std::string interval_id;
    std::string node_context;
    bool root_node = true;
    bool optimal_relaxation = true;
    int maximum_support_rank = 3;
    double certificate_tolerance = 1e-7;
};

class Round52CutSeparator {
public:
    virtual ~Round52CutSeparator() = default;
    virtual std::vector<Round52CutCandidate> separate(
        const Round52CutSeparationInput& input) const = 0;
};

class Round52SupportDurationSeparator final : public Round52CutSeparator {
public:
    std::vector<Round52CutCandidate> separate(
        const Round52CutSeparationInput& input) const override;
};

// Exact depot-to-depot route-duration lower bound for a canonical support.
// Ranks 2--4 are enumerated exactly; station order and input order do not
// affect the result.
double round52RouteDurationLowerBound(
    const Instance& instance, std::vector<int> support);
bool round52SeparationPermitted(
    Round52CutSeparationScope scope, bool root_node,
    bool optimal_relaxation);
constexpr int round52RequiredGurobiPreCrush() { return 1; }

bool normalizeRound52CutCandidate(
    Round52CutCandidate& candidate, std::string* reason = nullptr);
bool round52ExactlyDominates(const Round52CutCandidate& dominating,
                             const Round52CutCandidate& dominated);

struct Round52CutManagerConfig {
    Round52CutSelectionRule selection_rule =
        Round52CutSelectionRule::VehicleBlockMaximum;
    double certificate_tolerance = 1e-7;
};

struct Round52CutManagerTelemetry {
    long long generated = 0;
    long long nonviolated_rejections = 0;
    long long invalid_rejections = 0;
    long long duplicate_rejections = 0;
    long long dominated_rejections = 0;
    long long violated = 0;
    long long selected = 0;
    long long submission_attempts = 0;
    long long added = 0;
    long long submission_failures = 0;
    long long callback_failures = 0;
    long long callback_calls = 0;
    long long root_callback_calls = 0;
    long long tree_callback_calls = 0;
    std::size_t global_pool_size = 0;
    std::unordered_map<std::string, long long> generated_by_family;
    std::unordered_map<std::string, long long> violated_by_family;
    std::unordered_map<std::string, long long> selected_by_family;
    std::unordered_map<std::string, long long> added_by_family;
    std::unordered_map<int, long long> selected_by_vehicle;
};

class Round52CutManager {
public:
    explicit Round52CutManager(Round52CutManagerConfig config = {});
    void beginModel(const std::string& model_identity);
    std::vector<Round52CutCandidate> process(
        std::vector<Round52CutCandidate> candidates);
    void recordSubmission(const Round52CutCandidate& candidate, bool added);
    bool globalPoolContains(const std::string& canonical_signature) const;
    void recordCallback(bool root);
    void recordCallbackFailure();
    const Round52CutManagerTelemetry& telemetry() const { return telemetry_; }
    const std::string& modelIdentity() const { return model_identity_; }

private:
    Round52CutManagerConfig config_;
    std::string model_identity_;
    std::unordered_map<std::string, Round52CutCandidate> global_pool_;
    Round52CutManagerTelemetry telemetry_;
};

std::string round52CutSenseName(Round52CutSense sense);
std::string round52CutScopeName(Round52CutValidityScope scope);

} // namespace ebrp
