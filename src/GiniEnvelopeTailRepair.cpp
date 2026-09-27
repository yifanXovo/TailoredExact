#include "GiniEnvelopeTailRepair.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>

namespace ebrp {
namespace {

bool finite(double value) { return std::isfinite(value); }

double scaledTolerance(double tolerance, double a, double b = 0.0) {
    return std::max(0.0, tolerance) *
        std::max({1.0, std::fabs(a), std::fabs(b)});
}

bool validInterval(const GiniIntervalGeometry& interval) {
    return finite(interval.lower) && finite(interval.upper) &&
        interval.upper > interval.lower;
}

std::string oldAction(const TailRefinementInput& input) {
    if (input.old_c6_split) return "split";
    if (input.old_c6_run_target) return "native-target";
    if (input.old_c6_exact_closure) return "exact-closure";
    return "retain";
}

} // namespace

NextFrontierTarget computeNextFrontierTarget(
        const std::string& selected_leaf_id,
        double selected_lower_bound,
        const std::vector<FrontierBoundEntry>& open_leaves,
        double verified_upper_bound,
        double certificate_tolerance) {
    NextFrontierTarget result;
    const double tolerance = std::max(0.0, certificate_tolerance);
    if (selected_leaf_id.empty() || !finite(selected_lower_bound) ||
        !finite(verified_upper_bound) || open_leaves.empty()) {
        result.reason = "invalid_frontier_input";
        return result;
    }
    bool selected_found = false;
    result.current_global_lower_bound =
        std::numeric_limits<double>::infinity();
    result.next_distinct_bound = std::numeric_limits<double>::infinity();
    for (const FrontierBoundEntry& leaf : open_leaves) {
        if (!leaf.open) continue;
        if (leaf.leaf_id.empty() || !finite(leaf.lower_bound)) {
            result.reason = "invalid_open_leaf_bound";
            return result;
        }
        selected_found = selected_found || leaf.leaf_id == selected_leaf_id;
        result.current_global_lower_bound = std::min(
            result.current_global_lower_bound, leaf.lower_bound);
        if (std::fabs(leaf.lower_bound - selected_lower_bound) <=
            scaledTolerance(tolerance, leaf.lower_bound,
                            selected_lower_bound)) {
            ++result.frontier_multiplicity;
        }
        if (leaf.leaf_id != selected_leaf_id &&
            leaf.lower_bound > selected_lower_bound +
                scaledTolerance(tolerance, leaf.lower_bound,
                                selected_lower_bound)) {
            result.next_distinct_bound = std::min(
                result.next_distinct_bound, leaf.lower_bound);
        }
    }
    if (!selected_found || !finite(result.current_global_lower_bound)) {
        result.reason = "selected_leaf_not_in_open_cover";
        return result;
    }
    result.cutoff_target = verified_upper_bound - tolerance;
    result.next_distinct_available = finite(result.next_distinct_bound);
    result.target = result.next_distinct_available
        ? std::min(result.cutoff_target, result.next_distinct_bound)
        : result.cutoff_target;
    result.source = result.next_distinct_available &&
            result.next_distinct_bound <= result.cutoff_target
        ? "next-distinct-open-leaf-bound"
        : "verified-incumbent-cutoff";
    result.already_met = result.target <= selected_lower_bound +
        scaledTolerance(tolerance, result.target, selected_lower_bound);
    result.valid = finite(result.target);
    result.reason = result.valid ? "valid_next_frontier_target"
                                 : "nonfinite_frontier_target";
    return result;
}

FrontierLookaheadStop evaluateFrontierD2Stop(
        const GiniLookaheadBound& cell,
        double frontier_target,
        int current_depth,
        int maximum_depth,
        double certificate_tolerance) {
    FrontierLookaheadStop result;
    if (!validInterval(cell.interval) || !cell.terminal_valid ||
        !finite(frontier_target) || current_depth < 1 ||
        maximum_depth < current_depth) {
        result.reason = "invalid_lookahead_stop_input";
        return result;
    }
    result.valid = true;
    if (cell.infeasible) {
        result.reason = "lp_infeasible_stop";
    } else if (!cell.optimal || !cell.bound_available ||
               !finite(cell.lower_bound)) {
        result.valid = false;
        result.reason = "incomplete_depth_one_lp";
    } else if (cell.lower_bound >= frontier_target -
               scaledTolerance(certificate_tolerance, cell.lower_bound,
                               frontier_target)) {
        result.reason = "frontier_target_reached_stop";
    } else if (current_depth >= maximum_depth) {
        result.reason = "maximum_depth_stop";
    } else {
        result.refine = true;
        result.reason = "bound_below_frontier_refine_once";
    }
    return result;
}

EnvelopeFacetSelection selectEnvelopeFacets(
        const std::vector<GiniEnvelopeFacet>& facets,
        const std::string& policy,
        double parent_lp_g,
        double parent_lp_objective,
        double certificate_tolerance) {
    EnvelopeFacetSelection result;
    result.policy = policy;
    if (!finite(parent_lp_g) || !finite(parent_lp_objective) ||
        certificate_tolerance < 0.0 ||
        (policy != "none" && policy != "all" &&
         policy != "violated" && policy != "active-one")) {
        result.reason = "invalid_facet_selection_input";
        return result;
    }
    result.valid = true;
    result.violations.reserve(facets.size());
    double active_value = -std::numeric_limits<double>::infinity();
    for (std::size_t index = 0; index < facets.size(); ++index) {
        const double facet_value = evaluateGiniEnvelopeFacet(
            facets[index], parent_lp_g);
        const double epsilon = certificate_tolerance * std::max(
            {1.0, std::fabs(parent_lp_objective), std::fabs(facet_value)});
        result.epsilon_separation = std::max(
            result.epsilon_separation, epsilon);
        const double violation = facet_value - parent_lp_objective;
        result.violations.push_back(violation);
        if (violation > epsilon) ++result.violated_count;
        if (facet_value > active_value) {
            active_value = facet_value;
            result.active_index = static_cast<int>(index);
        }
    }
    if (policy == "all") {
        result.selected = facets;
    } else if (policy == "violated") {
        for (std::size_t index = 0; index < facets.size(); ++index) {
            const double value = evaluateGiniEnvelopeFacet(
                facets[index], parent_lp_g);
            const double epsilon = certificate_tolerance * std::max(
                {1.0, std::fabs(parent_lp_objective), std::fabs(value)});
            if (result.violations[index] > epsilon)
                result.selected.push_back(facets[index]);
        }
    } else if (policy == "active-one" && result.active_index >= 0) {
        const std::size_t index = static_cast<std::size_t>(result.active_index);
        const double value = evaluateGiniEnvelopeFacet(
            facets[index], parent_lp_g);
        const double epsilon = certificate_tolerance * std::max(
            {1.0, std::fabs(parent_lp_objective), std::fabs(value)});
        if (result.violations[index] > epsilon)
            result.selected.push_back(facets[index]);
    }
    result.reason = result.selected.empty()
        ? "no_facet_selected" : "facet_policy_applied";
    return result;
}

FrontierTailScores evaluateFrontierTailScores(
        const FrontierTailScoresInput& input) {
    FrontierTailScores result;
    const double eps = std::max(0.0, input.certificate_tolerance);
    if (!validInterval(input.root) || !validInterval(input.current) ||
        !finite(input.root_lower_bound) ||
        !finite(input.launch_upper_bound) ||
        !finite(input.current_lower_bound) ||
        !finite(input.strengthened_lower_bound) ||
        !finite(input.frontier_target) ||
        !finite(input.V_local) || !finite(input.V_envelope) ||
        !finite(input.V_residual) || input.terminal_lookahead.empty()) {
        result.reason = "invalid_score_input";
        return result;
    }
    const double root_width = input.root.upper - input.root.lower;
    const double current_width = input.current.upper - input.current.lower;
    result.M0 = root_width * std::max(
        input.launch_upper_bound - input.root_lower_bound, eps);
    if (!(result.M0 > 0.0) || current_width <= 0.0) {
        result.reason = "nonpositive_root_normalization";
        return result;
    }
    result.L_D = std::numeric_limits<double>::infinity();
    bool any_feasible = false;
    for (const GiniLookaheadBound& cell : input.terminal_lookahead) {
        if (!cell.terminal_valid) {
            result.reason = "incomplete_terminal_lookahead";
            return result;
        }
        if (cell.infeasible) continue;
        if (!cell.optimal || !cell.bound_available ||
            !finite(cell.lower_bound)) {
            result.reason = "invalid_terminal_lookahead_bound";
            return result;
        }
        any_feasible = true;
        result.L_D = std::min(result.L_D, cell.lower_bound);
    }
    if (!any_feasible)
        result.L_D = std::numeric_limits<double>::infinity();
    const double volume_eps = std::max(
        std::numeric_limits<double>::epsilon(),
        eps * current_width * std::max(
            {1.0, std::fabs(input.launch_upper_bound),
             std::fabs(input.current_lower_bound)}));
    result.D_R43 = input.V_residual /
        (current_width * std::max(
            input.launch_upper_bound - input.current_lower_bound, eps));
    result.P_profile = input.V_residual /
        std::max(input.V_local, volume_eps);
    result.M_root = input.V_residual / result.M0;
    const double capped_disjunction = std::min(
        result.L_D, input.frontier_target);
    const double capped_envelope = std::min(
        input.strengthened_lower_bound, input.frontier_target);
    result.delta_F = std::max(0.0,
        capped_disjunction - capped_envelope);
    if (input.frontier_target > input.strengthened_lower_bound +
        scaledTolerance(eps, input.frontier_target,
                        input.strengthened_lower_bound)) {
        result.F = result.delta_F / std::max(
            input.frontier_target - input.strengthened_lower_bound, eps);
    }
    result.F = std::max(0.0, std::min(1.0, result.F));
    result.M_root = std::max(0.0, std::min(1.0, result.M_root));
    result.H = result.F * result.M_root;
    result.decisive_frontier =
        result.L_D >= input.frontier_target -
            scaledTolerance(eps, result.L_D, input.frontier_target) &&
        input.strengthened_lower_bound < input.frontier_target -
            scaledTolerance(eps, input.strengthened_lower_bound,
                            input.frontier_target);
    const double identity_residual = std::fabs(
        input.V_local - input.V_envelope - input.V_residual);
    const double identity_tolerance = scaledTolerance(
        eps, input.V_local, input.V_envelope + input.V_residual);
    if (input.V_local < -identity_tolerance ||
        input.V_envelope < -identity_tolerance ||
        input.V_residual < -identity_tolerance ||
        identity_residual > identity_tolerance) {
        result.reason = "invalid_envelope_volume_identity";
        return result;
    }
    result.valid = true;
    result.reason = "valid_frontier_tail_scores";
    return result;
}

TailRefinementDecision evaluateTailRefinementDecision(
        const TailRefinementInput& input) {
    TailRefinementDecision result;
    result.old_c6_action = oldAction(input);
    const bool old_action_exclusive =
        static_cast<int>(input.old_c6_split) +
        static_cast<int>(input.old_c6_run_target) +
        static_cast<int>(input.old_c6_exact_closure) <= 1;
    if (!old_action_exclusive || !finite(input.F) ||
        !finite(input.M_root) || !finite(input.H) ||
        !finite(input.rho_F) || !finite(input.rho_M) ||
        !finite(input.rho_H) || input.F < 0.0 || input.F > 1.0 ||
        input.M_root < 0.0 || input.M_root > 1.0 ||
        input.H < 0.0 || input.H > 1.0) {
        result.reason = "invalid_refinement_input";
        return result;
    }
    const double eps = std::max(0.0, input.certificate_tolerance);
    const bool f = input.F + eps >= input.rho_F;
    const bool m = input.M_root + eps >= input.rho_M;
    const bool h = input.H + eps >= input.rho_H;
    if (input.family == "no-adaptive") {
        result.split = false;
    } else if (input.family == "c6-overlay") {
        result.split = input.old_c6_split;
    } else if (input.family == "veto") {
        result.split = input.old_c6_split && f;
    } else if (input.family == "veto-promotion") {
        result.split = input.old_c6_split ? f
            : input.decisive_frontier && m;
    } else if (input.family == "f") {
        result.split = f;
    } else if (input.family == "f-mroot") {
        result.split = f && m;
    } else if (input.family == "h") {
        result.split = h;
    } else if (input.family == "mroot") {
        result.split = m;
    } else {
        result.reason = "unknown_refinement_family";
        return result;
    }
    result.run_native_target = !result.split && input.old_c6_run_target;
    result.exact_closure = !result.split && !result.run_native_target &&
        (input.old_c6_exact_closure || input.family != "c6-overlay");
    result.final_action = result.split ? "split"
        : (result.run_native_target ? "native-target"
        : (result.exact_closure ? "exact-closure" : "retain"));
    result.valid = true;
    result.reason = "deterministic_bound_only_refinement_rule";
    return result;
}

std::string explicitCutScopeName(ExplicitCutScope scope) {
    switch (scope) {
    case ExplicitCutScope::Global: return "global";
    case ExplicitCutScope::SourceInterval: return "source-interval";
    case ExplicitCutScope::BranchLocal: return "branch-local";
    }
    return "unknown";
}

bool explicitCutMayPropagate(
        ExplicitCutScope scope,
        const GiniIntervalGeometry& source,
        const GiniIntervalGeometry& target,
        double certificate_tolerance,
        std::string* reason) {
    if (!validInterval(source) || !validInterval(target)) {
        if (reason) *reason = "invalid_cut_domain";
        return false;
    }
    if (scope == ExplicitCutScope::Global) {
        if (reason) *reason = "globally_valid_cut";
        return true;
    }
    if (scope == ExplicitCutScope::BranchLocal) {
        if (reason) *reason = "branch_local_cut_not_exportable";
        return false;
    }
    const bool nested = target.lower >= source.lower -
            scaledTolerance(certificate_tolerance, target.lower, source.lower) &&
        target.upper <= source.upper +
            scaledTolerance(certificate_tolerance, target.upper, source.upper);
    if (reason) *reason = nested
        ? "source_interval_cut_nested_descendant"
        : "target_outside_source_interval";
    return nested;
}

std::string canonicalEnvelopeFacetSignature(
        const GiniEnvelopeFacet& facet,
        double normalization_tolerance) {
    const double scale = std::max(
        {std::fabs(facet.alpha), std::fabs(facet.beta), 1.0});
    const double quantum = std::max(
        normalization_tolerance, std::numeric_limits<double>::epsilon());
    const auto quantize = [scale, quantum](double value) {
        return std::round(value / scale / quantum) * quantum;
    };
    std::ostringstream out;
    out << std::setprecision(17)
        << quantize(facet.alpha) << ':' << quantize(facet.beta) << ':'
        << facet.source_lower << ':' << facet.source_upper;
    return out.str();
}

CglpCertificateAudit auditCglpMultiplierCertificate(
        const CglpMultiplierCertificate& c,
        double tolerance) {
    CglpCertificateAudit result;
    const std::size_t rows = c.A.size();
    const std::size_t columns = c.g.size();
    if (!rows || !columns || c.b.size() != rows ||
        c.u_minus.size() != rows || c.u_plus.size() != rows ||
        c.pi.size() != columns || !finite(c.gamma) || !finite(c.pi0) ||
        !finite(c.lambda_minus) || !finite(c.lambda_plus)) {
        result.reason = "cglp_dimension_or_scalar_invalid";
        return result;
    }
    for (const auto& row : c.A) if (row.size() != columns) {
        result.reason = "cglp_matrix_not_rectangular";
        return result;
    }
    result.normalization = c.lambda_minus + c.lambda_plus;
    result.max_nonnegativity_violation = std::max(
        {0.0, -c.lambda_minus, -c.lambda_plus});
    for (std::size_t row = 0; row < rows; ++row) {
        if (!finite(c.b[row]) || !finite(c.u_minus[row]) ||
            !finite(c.u_plus[row])) {
            result.reason = "cglp_nonfinite_row";
            return result;
        }
        result.normalization += c.u_minus[row] + c.u_plus[row];
        result.max_nonnegativity_violation = std::max(
            {result.max_nonnegativity_violation,
             -c.u_minus[row], -c.u_plus[row]});
    }
    double left_rhs = -c.lambda_minus * c.gamma;
    double right_rhs = c.lambda_plus * c.gamma;
    for (std::size_t row = 0; row < rows; ++row) {
        left_rhs += c.b[row] * c.u_minus[row];
        right_rhs += c.b[row] * c.u_plus[row];
    }
    result.left_rhs_violation = std::max(0.0, c.pi0 - left_rhs);
    result.right_rhs_violation = std::max(0.0, c.pi0 - right_rhs);
    for (std::size_t column = 0; column < columns; ++column) {
        if (!finite(c.g[column]) || !finite(c.pi[column])) {
            result.reason = "cglp_nonfinite_column";
            return result;
        }
        double left = -c.lambda_minus * c.g[column];
        double right = c.lambda_plus * c.g[column];
        for (std::size_t row = 0; row < rows; ++row) {
            left += c.A[row][column] * c.u_minus[row];
            right += c.A[row][column] * c.u_plus[row];
        }
        result.max_left_coefficient_residual = std::max(
            result.max_left_coefficient_residual,
            std::fabs(c.pi[column] - left));
        result.max_right_coefficient_residual = std::max(
            result.max_right_coefficient_residual,
            std::fabs(c.pi[column] - right));
    }
    const double eps = std::max(0.0, tolerance);
    result.valid = result.max_nonnegativity_violation <= eps &&
        std::fabs(result.normalization - 1.0) <= eps &&
        result.max_left_coefficient_residual <= eps &&
        result.max_right_coefficient_residual <= eps &&
        result.left_rhs_violation <= eps &&
        result.right_rhs_violation <= eps;
    result.reason = result.valid ? "valid_rank1_multiplier_certificate"
                                 : "rank1_multiplier_audit_failed";
    return result;
}

bool verifiedMipStartInInterval(
        double exact_gini,
        const GiniIntervalGeometry& interval,
        bool include_upper_endpoint,
        double certificate_tolerance) {
    if (!finite(exact_gini) || !validInterval(interval)) return false;
    const double lower_eps = scaledTolerance(
        certificate_tolerance, exact_gini, interval.lower);
    const double upper_eps = scaledTolerance(
        certificate_tolerance, exact_gini, interval.upper);
    if (exact_gini < interval.lower - lower_eps) return false;
    return include_upper_endpoint
        ? exact_gini <= interval.upper + upper_eps
        : exact_gini < interval.upper - upper_eps;
}

} // namespace ebrp
