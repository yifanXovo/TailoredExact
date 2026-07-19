#pragma once

#include "Instance.hpp"

#include <map>
#include <set>
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

struct ChildDomainEstimate {
    double parent_relaxation = 0.0;
    double gamma_floor_component = 0.0;
    std::vector<double> station_deviation_lower;
    std::vector<double> station_weighted_deviation_lower;
    double weighted_penalty_lower = 0.0;
    double domain_estimate = 0.0;
    double final_estimate = 0.0;
    double lift_over_parent = 0.0;
    double s_lower = 0.0;
    double required_deviation = 0.0;
    double deviation_lower_sum = 0.0;
    double deviation_upper_sum = 0.0;
    double dispersion_penalty_lower = 0.0;
    bool dispersion_bound_used = false;
    bool domain_contradiction_observed = false;
    std::string validation_status = "not_dispersion_coupled";
    bool valid = false;
    std::string failure_reason;
};

struct CanonicalInheritanceState {
    std::map<std::string, CanonicalLinearRow> rows_by_signature;
    std::map<std::string, CanonicalBoundChange> bounds_by_signature;
    std::map<std::string, CanonicalBoundChange> effective_bounds_by_key;
    bool valid = true;
    std::string failure_reason;
};

struct ExactIncrementalDelta {
    std::vector<CanonicalLinearRow> rows_to_attach;
    std::vector<CanonicalBoundChange> bounds_to_attach;
    long long theoretical_full_rows = 0;
    long long theoretical_full_bounds = 0;
    long long inherited_rows = 0;
    long long inherited_bounds = 0;
    long long exact_duplicate_rows_omitted = 0;
    long long identical_bounds_omitted = 0;
    long long dominance_omissions = 0;
    bool valid = true;
    std::string failure_reason;
};

IntervalRowFactoryResult buildRound18StaticIntervalRows(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalRowFactoryRequest& request);

ChildDomainEstimate computeChildDomainEstimate(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalDomainSummary& domain,
    double child_gamma_lower,
    double parent_relaxation);

ChildDomainEstimate computeDispersionCoupledChildEstimate(
    const Instance& instance,
    const SolveOptions& options,
    const IntervalDomainSummary& domain,
    double child_gamma_lower,
    double parent_relaxation);

CanonicalInheritanceState makeCanonicalInheritanceState(
    const IntervalRowFactoryResult& rows);

bool mergeCanonicalInheritanceState(
    CanonicalInheritanceState& inherited,
    const std::vector<CanonicalLinearRow>& rows,
    const std::vector<CanonicalBoundChange>& bounds,
    std::string* failure_reason = nullptr);

ExactIncrementalDelta computeExactIncrementalDelta(
    const CanonicalInheritanceState& inherited,
    const IntervalRowFactoryResult& child);

std::string canonicalRowSignature(const CanonicalLinearRow& row);
std::string canonicalBoundSignature(const CanonicalBoundChange& bound);

} // namespace ebrp
