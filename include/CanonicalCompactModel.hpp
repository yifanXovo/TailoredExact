#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <filesystem>
#include <string>
#include <unordered_map>

namespace ebrp {

// Solver-neutral request for the one deterministic compact-model writer.
// Both CPLEX and Gurobi consume the artifact produced by this request; no
// backend owns an independent mathematical model definition.
struct CanonicalCompactModelSpec {
    bool strengthened = false;
    bool interval_restricted = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    bool add_verified_incumbent_row = false;
    double verified_incumbent = 0.0;
    double incumbent_epsilon = 0.0;
};

struct CanonicalCompactModelArtifact {
    bool written = false;
    std::filesystem::path path;
    std::string sha256;
    std::string row_signature;
    long long rows = 0;
    long long columns = 0;
    long long nonzeros = 0;
    bool strengthened = false;
    bool interval_restricted = false;
    double gamma_L = 0.0;
    double gamma_U = 0.0;
    bool verified_incumbent_row = false;
    std::string objective_definition =
        "min_G_plus_lambda_weighted_absolute_satisfaction_deviation";
    std::string model_scope = "complete_original_compact_milp";
    std::string failure_reason;
};

CanonicalCompactModelArtifact writeCanonicalCompactModel(
    const Instance& instance,
    const SolveOptions& options,
    const std::filesystem::path& path,
    const CanonicalCompactModelSpec& spec);

std::vector<RoutePlan> reconstructCanonicalCompactRoutes(
    const Instance& instance,
    const std::unordered_map<std::string, double>& named_values);

} // namespace ebrp
