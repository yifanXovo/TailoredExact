#pragma once

#include "Instance.hpp"

#include <map>
#include <string>
#include <vector>

namespace ebrp {

enum class IntervalRowScope {
    Global,
    IntervalLocal,
    IntervalBound,
    DiagnosticExcluded
};

std::string intervalRowScopeName(IntervalRowScope scope);

struct CanonicalLinearRow {
    std::string family;
    std::map<std::string, double> coefficients;
    char sense = 'L';
    double rhs = 0.0;
    bool depends_on_gamma_L = false;
    bool depends_on_gamma_U = false;
    IntervalRowScope scope = IntervalRowScope::IntervalLocal;
    std::string proof_tag;
    std::string signature;
};

struct CanonicalBoundChange {
    std::string family;
    std::string variable;
    char direction = 'L';
    double value = 0.0;
    bool depends_on_gamma_L = false;
    bool depends_on_gamma_U = false;
    IntervalRowScope scope = IntervalRowScope::IntervalBound;
    std::string proof_tag;
    std::string signature;
};

struct IntervalDomainSummary {
    std::vector<int> y_lower;
    std::vector<int> y_upper;
    std::vector<double> e_lower;
    std::vector<double> e_upper;
    double s_lower = 0.0;
    double s_upper = 0.0;
    double penalty_lower = 0.0;
    double penalty_upper = 0.0;
    double g_lower = 0.0;
    double g_upper = 1.0;
    bool domain_infeasible = false;
};

struct IntervalRowFamilyRegistryEntry {
    std::string family;
    IntervalRowScope scope = IntervalRowScope::DiagnosticExcluded;
    bool active = false;
    bool implemented = false;
    std::string proof_tag;
};

struct IntervalRowFactoryRequest {
    double gamma_L = 0.0;
    double gamma_U = 1.0;
    double verified_incumbent = 0.0;
    double incumbent_epsilon = 0.0;
    bool add_incumbent_row = true;
    bool strengthened = true;
};

struct IntervalRowFactoryResult {
    std::string factory_version = "round19_v2_projected_centering";
    IntervalDomainSummary domain;
    std::vector<CanonicalLinearRow> rows;
    std::vector<CanonicalBoundChange> bound_changes;
    std::vector<std::string> active_families;
    std::vector<std::string> unsupported_active_families;
    std::vector<IntervalRowFamilyRegistryEntry> family_registry;
    bool complete_round18_static_migration = false;
    std::string aggregate_signature;
};

IntervalRowFactoryResult buildRound18StaticIntervalRows(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalRowFactoryRequest& request);

std::string canonicalRowSignature(const CanonicalLinearRow& row);
std::string canonicalBoundSignature(const CanonicalBoundChange& bound);

} // namespace ebrp
