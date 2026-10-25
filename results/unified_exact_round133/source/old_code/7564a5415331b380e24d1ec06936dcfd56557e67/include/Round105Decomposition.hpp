#pragma once
#include "Instance.hpp"
#include "Result.hpp"
#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace ebrp {
// A signed local operation: positive pickup, negative delivery, zero absent.
struct Round105Pattern {
    int vehicle = 0;
    std::vector<int> operation; // all original stations, including absent ones
};
struct Round105Conflict {
    std::map<std::string, double> coefficients;
    double rhs = 0;
    std::vector<int> assumptions; // whole semantic groups, original station IDs
    int positive_groups = 0;
    int negative_groups = 0;
};
enum class Round105OracleStatus { Feasible, ProvedInfeasible, Unknown, Error };
struct Round105OracleResult {
    Round105OracleStatus status = Round105OracleStatus::Unknown;
    RoutePlan route;
    std::vector<int> core;
    bool core_confirmed = false;
    std::string reason;
};
void round105ValidatePattern(const Instance&, const Round105Pattern&);
Round105Conflict round105Conflict(const Instance&, const Round105Pattern&,
                                  const std::vector<int>& assumptions);
// All-station physical template. Only named assumption rows depend on pattern.
void round105WriteOracle(const Instance&, const Round105Pattern&,
                        const std::vector<int>& assumptions,
                        const std::filesystem::path&);
std::string round105PatternKey(const Instance&, const Round105Pattern&);
SolveResult solveRound105Decomposition(const Instance&, const SolveOptions&,
                                      const SolveResult& verified_seed);
Round105OracleResult solveRound105OracleDiagnostic(
    const Instance&, const SolveOptions&, const Round105Pattern&,
    const std::filesystem::path&, bool core);
} // namespace ebrp
