#pragma once

#include "GiniEnvelopeRefinement.hpp"

#include <string>
#include <vector>

namespace ebrp {

// Solver-neutral Round 44 decision objects.  They deliberately contain no
// instance metadata or solver telemetry: every action is a deterministic
// function of certified bounds, interval geometry, facets, and frozen
// thresholds.
struct FrontierBoundEntry {
    std::string leaf_id;
    double lower_bound = 0.0;
    bool open = true;
};

struct NextFrontierTarget {
    bool valid = false;
    double current_global_lower_bound = 0.0;
    int frontier_multiplicity = 0;
    bool next_distinct_available = false;
    double next_distinct_bound = 0.0;
    double cutoff_target = 0.0;
    double target = 0.0;
    bool already_met = false;
    std::string source = "not_evaluated";
    std::string reason = "not_evaluated";
};

NextFrontierTarget computeNextFrontierTarget(
    const std::string& selected_leaf_id,
    double selected_lower_bound,
    const std::vector<FrontierBoundEntry>& open_leaves,
    double verified_upper_bound,
    double certificate_tolerance);

struct FrontierLookaheadStop {
    bool valid = false;
    bool refine = false;
    std::string reason = "not_evaluated";
};

FrontierLookaheadStop evaluateFrontierD2Stop(
    const GiniLookaheadBound& depth_one_cell,
    double frontier_target,
    int current_depth,
    int maximum_depth,
    double certificate_tolerance);

struct EnvelopeFacetSelection {
    bool valid = false;
    std::vector<GiniEnvelopeFacet> selected;
    std::vector<double> violations;
    int violated_count = 0;
    int active_index = -1;
    double epsilon_separation = 0.0;
    std::string policy = "none";
    std::string reason = "not_evaluated";
};

EnvelopeFacetSelection selectEnvelopeFacets(
    const std::vector<GiniEnvelopeFacet>& facets,
    const std::string& policy,
    double parent_lp_g,
    double parent_lp_objective,
    double certificate_tolerance);

struct FrontierTailScoresInput {
    GiniIntervalGeometry root;
    GiniIntervalGeometry current;
    double root_lower_bound = 0.0;
    double launch_upper_bound = 0.0;
    double current_lower_bound = 0.0;
    double strengthened_lower_bound = 0.0;
    double frontier_target = 0.0;
    double V_local = 0.0;
    double V_envelope = 0.0;
    double V_residual = 0.0;
    std::vector<GiniLookaheadBound> terminal_lookahead;
    double certificate_tolerance = 1e-7;
};

struct FrontierTailScores {
    bool valid = false;
    double M0 = 0.0;
    double L_D = 0.0;
    double D_R43 = 0.0;
    double P_profile = 0.0;
    double M_root = 0.0;
    double delta_F = 0.0;
    double F = 0.0;
    double H = 0.0;
    bool decisive_frontier = false;
    std::string reason = "not_evaluated";
};

FrontierTailScores evaluateFrontierTailScores(
    const FrontierTailScoresInput& input);

struct TailRefinementInput {
    std::string family = "no-adaptive";
    bool old_c6_split = false;
    bool old_c6_run_target = false;
    bool old_c6_exact_closure = false;
    double F = 0.0;
    double M_root = 0.0;
    double H = 0.0;
    bool decisive_frontier = false;
    double rho_F = 0.5;
    double rho_M = 0.0;
    double rho_H = 0.0;
    double certificate_tolerance = 1e-7;
};

struct TailRefinementDecision {
    bool valid = false;
    bool split = false;
    bool run_native_target = false;
    bool exact_closure = false;
    std::string old_c6_action = "invalid";
    std::string final_action = "invalid";
    std::string reason = "not_evaluated";
};

TailRefinementDecision evaluateTailRefinementDecision(
    const TailRefinementInput& input);

enum class ExplicitCutScope {
    Global,
    SourceInterval,
    BranchLocal
};

std::string explicitCutScopeName(ExplicitCutScope scope);

bool explicitCutMayPropagate(
    ExplicitCutScope scope,
    const GiniIntervalGeometry& source,
    const GiniIntervalGeometry& target,
    double certificate_tolerance,
    std::string* reason = nullptr);

std::string canonicalEnvelopeFacetSignature(
    const GiniEnvelopeFacet& facet,
    double normalization_tolerance = 1e-12);

struct CglpMultiplierCertificate {
    // Row-major A for P={x:A x >= b}.
    std::vector<std::vector<double>> A;
    std::vector<double> b;
    std::vector<double> g;
    double gamma = 0.0;
    std::vector<double> u_minus;
    std::vector<double> u_plus;
    double lambda_minus = 0.0;
    double lambda_plus = 0.0;
    std::vector<double> pi;
    double pi0 = 0.0;
};

struct CglpCertificateAudit {
    bool valid = false;
    double normalization = 0.0;
    double max_nonnegativity_violation = 0.0;
    double max_left_coefficient_residual = 0.0;
    double max_right_coefficient_residual = 0.0;
    double left_rhs_violation = 0.0;
    double right_rhs_violation = 0.0;
    std::string reason = "not_evaluated";
};

CglpCertificateAudit auditCglpMultiplierCertificate(
    const CglpMultiplierCertificate& certificate,
    double tolerance);

// Adjacent exact-cover intervals use the conventional [lower,upper) rule,
// with the complete root's last upper endpoint included.
bool verifiedMipStartInInterval(
    double exact_gini,
    const GiniIntervalGeometry& interval,
    bool include_upper_endpoint,
    double certificate_tolerance);

} // namespace ebrp
