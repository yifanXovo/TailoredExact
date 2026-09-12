#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace ebrp {

struct VerifiedBrpCandidate {
    bool verified = false;
    std::string source;
    std::string content_sha256;
    std::string model_identity;
    long long generation = -1;
    double source_elapsed_seconds = 0.0;
    double generation_seconds = 0.0;
    double verification_seconds = 0.0;
    double objective = 0.0;
    double G = 0.0;
    double P = 0.0;
    std::vector<RoutePlan> routes;
    std::vector<int> final_inventory;
};

struct CandidateObservation {
    std::string source;
    std::string content_sha256;
    long long generation = -1;
    bool duplicate = false;
    bool verifier_passed = false;
    bool published = false;
    std::string reason;
    double source_elapsed_seconds = 0.0;
    double verification_seconds = 0.0;
    double objective = 0.0;
};

class VerifiedCandidateStore {
public:
    // Timings are disjoint store work; verifier time stays in observations.
    double hash_seconds = 0.0;
    double copy_seconds = 0.0;
    bool consider(const Instance& instance,
                  double lambda,
                  const std::vector<RoutePlan>& routes,
                  const std::string& source,
                  const std::string& model_identity,
                  long long generation = -1,
                  double source_elapsed_seconds = 0.0,
                  double generation_seconds = 0.0);

    bool hasBest() const { return has_best_; }
    const VerifiedBrpCandidate& best() const { return best_; }
    const std::vector<CandidateObservation>& observations() const {
        return observations_;
    }

private:
    bool has_best_ = false;
    VerifiedBrpCandidate best_;
    std::unordered_set<std::string> seen_;
    std::vector<CandidateObservation> observations_;
};

std::string canonicalCandidateSerialization(
    const std::vector<RoutePlan>& routes);

struct Round60ConstructionInput {
    std::string source = "round60_data_target_greedy";
    std::string model_identity;
    std::vector<int> desired_inventory;
    std::unordered_map<std::string, double> relaxation_values;
    int maximum_evaluations = 512;
    int maximum_stations = 16;
};

struct Round60ConstructionResult {
    bool generated = false;
    std::string reason = "not_attempted";
    int objective_evaluations = 0;
    int accepted_stations = 0;
    double first_nonempty_seconds = -1.0;
    std::string termination_reason;
    double generation_seconds = 0.0;
    VerifiedBrpCandidate candidate;
};

Round60ConstructionResult constructRound60BrpCandidate(
    const Instance& instance,
    double lambda,
    const Round60ConstructionInput& input);

struct SolverNeutralLinearModel {
    int variable_count = 0;
    std::vector<int> row_starts;
    std::vector<int> column_indices;
    std::vector<double> coefficients;
    std::vector<char> senses;
    std::vector<double> rhs;
};

struct CandidateLinearResidual {
    bool checked = false;
    bool valid = false;
    long long checked_rows = 0;
    long long violated_rows = 0;
    double maximum_violation = 0.0;
    std::string failure_reason = "not_checked";
};

CandidateLinearResidual validateCandidateLinearResidual(
    const SolverNeutralLinearModel& model,
    const std::vector<double>& values,
    double tolerance = 1e-7);

} // namespace ebrp
