#pragma once

#include "GiniFrontierGeometry.hpp"

#include <string>
#include <vector>

namespace ebrp {

struct GammaSumInput {
    GiniIntervalGeometry parent;
    GiniIntervalGeometry left;
    GiniIntervalGeometry right;
    double envelope_lower_bound = 0.0;
    double left_lower_bound = 0.0;
    double right_lower_bound = 0.0;
    double frontier_target = 0.0;
    double root_normalization = 0.0;
    double certificate_tolerance = 1e-7;
};

struct GammaSumResult {
    bool valid = false;
    double parent_mass = 0.0;
    double split_mass = 0.0;
    double gamma_sum = 0.0;
    double epsilon_gamma = 0.0;
    std::string reason = "not_evaluated";
};

GammaSumResult evaluateGammaSum(const GammaSumInput& input);

struct AdaptiveTimingInput {
    std::string family = "gamma-positive";
    bool old_c6_split = false;
    double D_R43 = 0.0;
    double F = 0.0;
    double M_root = 0.0;
    double H = 0.0;
    double Gamma_sum = 0.0;
    double epsilon_gamma = 0.0;
    bool decisive_frontier = false;
    double rho_D = 0.10;
    double rho_F = 0.50;
    double rho_M = 0.0;
    double rho_H = 0.0;
    double rho_gamma = 0.0;
    double certificate_tolerance = 1e-7;
};

struct AdaptiveTimingDecision {
    bool valid = false;
    bool split = false;
    bool genuinely_adaptive_family = false;
    std::string action = "invalid";
    std::string reason = "not_evaluated";
};

AdaptiveTimingDecision evaluateAdaptiveTimingDecision(
    const AdaptiveTimingInput& input);

struct ParametricBasisSensitivity {
    double rhs = 0.0;
    double allowable_decrease = 0.0;
    double allowable_increase = 0.0;
};

GiniIntervalGeometry parametricBasisSensitivityInterval(
    const ParametricBasisSensitivity& sensitivity);

double canonicalRightParametricCoefficient(double g_coefficient);
double canonicalRightParametricRhs(double split_point);
double affineParametricValue(double base_value, double dual_slope,
                             double rhs, double base_rhs);

struct ParametricAffineSegment {
    double lower = 0.0;
    double upper = 0.0;
    double intercept = 0.0;
    double slope = 0.0;
    std::string basis_hash;
    bool degenerate = false;
};

double evaluateParametricSegment(
    const ParametricAffineSegment& segment, double point);

struct ParametricValueFunctionAudit {
    bool valid = false;
    bool exact_coverage = false;
    bool monotone = false;
    bool finite = false;
    double maximum_monotonicity_residual = 0.0;
    double maximum_endpoint_jump = 0.0;
    std::string reason = "not_evaluated";
};

ParametricValueFunctionAudit auditParametricValueFunction(
    const std::vector<ParametricAffineSegment>& segments,
    const GiniIntervalGeometry& domain,
    bool nonincreasing,
    double tolerance);

std::vector<ParametricAffineSegment> mergeParametricSegments(
    const std::vector<ParametricAffineSegment>& segments,
    double tolerance);

struct ParametricPointInput {
    GiniIntervalGeometry admissible;
    std::vector<ParametricAffineSegment> left;
    std::vector<ParametricAffineSegment> right;
    bool frontier_capped = false;
    double frontier_target = 0.0;
    double certificate_tolerance = 1e-7;
};

struct ParametricPointResult {
    bool certified = false;
    double selected_point = 0.0;
    double midpoint = 0.0;
    double maximizer_lower = 0.0;
    double maximizer_upper = 0.0;
    double max_min_value = 0.0;
    bool plateau = false;
    bool boundary = false;
    std::string tie_break = "plateau-midpoint";
    std::string reason = "not_evaluated";
};

ParametricPointResult selectParametricMaxMinPoint(
    const ParametricPointInput& input);

struct ParametricRootSample {
    double point = 0.0;
    double left_value = 0.0;
    double right_value = 0.0;
    bool left_infeasible = false;
    bool right_infeasible = false;
    bool left_optimal = true;
    bool right_optimal = true;
};

struct ParametricRootAudit {
    bool valid = false;
    bool both_child_coverage = false;
    double left_monotonicity_residual = 0.0;
    double right_monotonicity_residual = 0.0;
    std::string reason = "not_evaluated";
};

ParametricRootAudit auditParametricRootSamples(
    std::vector<ParametricRootSample> samples,
    double tolerance);

} // namespace ebrp
