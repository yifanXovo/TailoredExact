#include "Round49K1RC.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>

namespace ebrp {
namespace {

bool allDigits(const std::string& value) {
    return !value.empty() && std::all_of(
        value.begin(), value.end(), [](unsigned char ch) {
            return ch >= '0' && ch <= '9';
        });
}

bool indexed(const std::string& value, const std::string& prefix,
             int index_count) {
    if (value.rfind(prefix, 0) != 0) return false;
    std::string suffix = value.substr(prefix.size());
    for (int index = 0; index < index_count; ++index) {
        const std::size_t separator = suffix.find('_');
        const std::string token = separator == std::string::npos
            ? suffix : suffix.substr(0, separator);
        if (!allDigits(token)) return false;
        if (index + 1 == index_count) return separator == std::string::npos;
        if (separator == std::string::npos) return false;
        suffix = suffix.substr(separator + 1);
    }
    return false;
}

double numericalTolerance(double certificate_tolerance,
                          std::initializer_list<double> values) {
    double scale = 1.0;
    for (double value : values) {
        if (std::isfinite(value)) scale = std::max(scale, std::fabs(value));
    }
    return certificate_tolerance +
        64.0 * std::numeric_limits<double>::epsilon() * scale;
}

std::string fnvHash(const std::string& value) {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char ch : value) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << hash;
    return out.str();
}

std::string action(const C6CurrentSplitDecision& decision) {
    if (decision.split_immediately) return "split";
    if (decision.run_child_bound_target) return "native-target";
    if (decision.launch_exact_closure) return "exact-close";
    return "retain";
}

using EvidenceMap = std::map<std::string, FixedIntervalLpVariableEvidence>;

bool evidenceMap(const PaperLpResult& state, EvidenceMap& out,
                 std::string& reason) {
    if (!state.terminal_valid || !state.optimal || state.infeasible ||
        !state.bound_available || !state.primal_values_available ||
        !state.reduced_costs_available || !state.basis_status_available ||
        !state.primal_dual_evidence_available || state.objective_sense != 1 ||
        state.model_fingerprint.empty() || !std::isfinite(state.lower_bound) ||
        !std::isfinite(state.verified_cutoff)) {
        reason = "invalid_or_incomplete_lp_primal_dual_state";
        return false;
    }
    for (const auto& item : state.primal_dual_variables) {
        if (round49PrimitiveIntegerFamily(item.name).empty()) continue;
        if (item.original_type != 'B' && item.original_type != 'I') {
            reason = "primitive_variable_not_original_integer:" + item.name;
            return false;
        }
        if (!std::isfinite(item.lower_bound) ||
            !std::isfinite(item.upper_bound) ||
            !std::isfinite(item.primal_value) ||
            !std::isfinite(item.reduced_cost) ||
            !out.emplace(item.name, item).second) {
            reason = "invalid_or_duplicate_primitive_variable:" + item.name;
            return false;
        }
    }
    if (out.empty()) {
        reason = "empty_primitive_integer_registry_mapping";
        return false;
    }
    return true;
}

bool deriveStateDomain(const FixedIntervalLpVariableEvidence& item,
                       double lp_objective, double verified_incumbent,
                       double certificate_tolerance,
                       Round49RCStateDomain& out,
                       std::string& reason) {
    const double epsilon = numericalTolerance(certificate_tolerance,
        {lp_objective, verified_incumbent, item.lower_bound,
         item.upper_bound, item.primal_value, item.reduced_cost});
    const double lower_rounded = std::ceil(item.lower_bound - epsilon);
    const double upper_rounded = std::floor(item.upper_bound + epsilon);
    if (!std::isfinite(lower_rounded) || !std::isfinite(upper_rounded) ||
        lower_rounded < static_cast<double>(std::numeric_limits<int>::min()) ||
        upper_rounded > static_cast<double>(std::numeric_limits<int>::max()) ||
        lower_rounded > upper_rounded) {
        reason = "empty_or_unrepresentable_effective_integer_domain:" +
            item.name;
        return false;
    }
    out.effective_lower = static_cast<int>(lower_rounded);
    out.effective_upper = static_cast<int>(upper_rounded);
    out.rc_lower = out.effective_lower;
    out.rc_upper = out.effective_upper;
    out.effective_count = static_cast<long long>(out.effective_upper) -
        out.effective_lower + 1;
    out.primal_value = item.primal_value;
    out.reduced_cost = item.reduced_cost;
    out.variable_basis_status = item.variable_basis_status;
    out.reason = "effective_domain_retained";
    const double strict_cutoff = verified_incumbent - certificate_tolerance;
    const double delta = std::max(strict_cutoff - lp_objective, 0.0);
    if (item.variable_basis_status == -1 &&
        std::fabs(item.primal_value - item.lower_bound) <= epsilon &&
        item.reduced_cost > epsilon) {
        const double raw_steps = std::floor(
            (delta + epsilon) / item.reduced_cost);
        const long long steps = std::max(0LL, static_cast<long long>(
            std::min(raw_steps,
                static_cast<double>(std::numeric_limits<int>::max()))));
        out.rc_upper = static_cast<int>(std::min<long long>(
            out.effective_upper,
            static_cast<long long>(out.effective_lower) + steps));
        out.reason = "positive_reduced_cost_at_lower_bound";
    } else if (item.variable_basis_status == -2 &&
               std::fabs(item.primal_value - item.upper_bound) <= epsilon &&
               item.reduced_cost < -epsilon) {
        const double raw_steps = std::floor(
            (delta + epsilon) / (-item.reduced_cost));
        const long long steps = std::max(0LL, static_cast<long long>(
            std::min(raw_steps,
                static_cast<double>(std::numeric_limits<int>::max()))));
        out.rc_lower = static_cast<int>(std::max<long long>(
            out.effective_lower,
            static_cast<long long>(out.effective_upper) - steps));
        out.reason = "negative_reduced_cost_at_upper_bound";
    }
    if (out.rc_lower > out.rc_upper) {
        reason = "empty_rc_integer_domain:" + item.name;
        return false;
    }
    out.rc_count = static_cast<long long>(out.rc_upper) - out.rc_lower + 1;
    return true;
}

Round49RCSummary summarize(
        const std::vector<Round49RCVariableDomain>& variables,
        char state) {
    Round49RCSummary out;
    double d_sum = 0.0;
    double log_num = 0.0;
    double log_den = 0.0;
    long long nonfixed = 0;
    for (const auto& variable : variables) {
        if (variable.parent.effective_count <= 1) continue;
        const Round49RCStateDomain& domain = state == 'P'
            ? variable.parent : (state == 'L' ? variable.left : variable.right);
        ++nonfixed;
        out.residual_count += domain.rc_count - 1;
        out.base_residual_count += variable.parent.effective_count - 1;
        d_sum += static_cast<double>(domain.rc_count - 1) /
            static_cast<double>(std::max(1LL,
                variable.parent.effective_count - 1));
        log_num += std::log(static_cast<double>(std::max(1LL, domain.rc_count)));
        log_den += std::log(static_cast<double>(
            std::max(1LL, variable.parent.effective_count)));
        if (domain.rc_count == 1) ++out.fixed_count;
        if (domain.rc_count < domain.effective_count) ++out.tightened_count;
    }
    if (nonfixed > 0) out.D = d_sum / static_cast<double>(nonfixed);
    out.H = log_num / std::max(log_den,
        std::numeric_limits<double>::epsilon());
    return out;
}

} // namespace

std::string round49PrimitiveIntegerFamily(const std::string& variable) {
    if (indexed(variable, "x_", 3)) return "routing_arc";
    if (indexed(variable, "z_", 2)) return "visit_selection";
    if (indexed(variable, "mode_", 2)) return "operation_mode";
    if (indexed(variable, "p_", 2)) return "pickup_quantity";
    if (indexed(variable, "d_", 2)) return "drop_quantity";
    if (indexed(variable, "load_", 2)) return "vehicle_load";
    if (indexed(variable, "Y_", 1)) return "final_inventory";
    return "";
}

Round49RCDomainProfile buildRound49RCDomainProfile(
        const PaperLpResult& parent,
        const PaperLpResult& left,
        const PaperLpResult& right,
        double verified_incumbent,
        double certificate_tolerance) {
    Round49RCDomainProfile out;
    out.verified_incumbent = verified_incumbent;
    out.parent_lp_bound = parent.lower_bound;
    out.left_lp_bound = left.lower_bound;
    out.right_lp_bound = right.lower_bound;
    out.parent_model_fingerprint = parent.model_fingerprint;
    out.left_model_fingerprint = left.model_fingerprint;
    out.right_model_fingerprint = right.model_fingerprint;
    if (!std::isfinite(verified_incumbent) ||
        !std::isfinite(certificate_tolerance) || certificate_tolerance < 0.0) {
        out.failure_reason = "invalid_incumbent_or_certificate_tolerance";
        return out;
    }
    const double epoch_tolerance = numericalTolerance(certificate_tolerance,
        {verified_incumbent, parent.verified_cutoff,
         left.verified_cutoff, right.verified_cutoff});
    if (std::fabs(parent.verified_cutoff - verified_incumbent) > epoch_tolerance ||
        std::fabs(left.verified_cutoff - verified_incumbent) > epoch_tolerance ||
        std::fabs(right.verified_cutoff - verified_incumbent) > epoch_tolerance) {
        out.failure_reason = "stale_incumbent_cutoff_epoch";
        return out;
    }
    EvidenceMap p, l, r;
    if (!evidenceMap(parent, p, out.failure_reason) ||
        !evidenceMap(left, l, out.failure_reason) ||
        !evidenceMap(right, r, out.failure_reason)) {
        return out;
    }
    if (p.size() != l.size() || p.size() != r.size()) {
        out.failure_reason = "primitive_variable_mapping_size_mismatch";
        return out;
    }
    for (const auto& entry : p) {
        const auto li = l.find(entry.first);
        const auto ri = r.find(entry.first);
        if (li == l.end() || ri == r.end()) {
            out.failure_reason = "primitive_variable_identity_mismatch:" +
                entry.first;
            return out;
        }
        Round49RCVariableDomain variable;
        variable.variable = entry.first;
        variable.family = round49PrimitiveIntegerFamily(entry.first);
        if (!deriveStateDomain(entry.second, parent.lower_bound,
                verified_incumbent, certificate_tolerance,
                variable.parent, out.failure_reason) ||
            !deriveStateDomain(li->second, left.lower_bound,
                verified_incumbent, certificate_tolerance,
                variable.left, out.failure_reason) ||
            !deriveStateDomain(ri->second, right.lower_bound,
                verified_incumbent, certificate_tolerance,
                variable.right, out.failure_reason)) {
            return out;
        }
        variable.exact_child_disjoint =
            variable.left.rc_upper < variable.right.rc_lower ||
            variable.right.rc_upper < variable.left.rc_lower;
        if (variable.exact_child_disjoint) ++out.disjoint_domain_count;
        ++out.family_counts[variable.family];
        out.variables.push_back(variable);
    }
    out.primitive_variable_count = static_cast<long long>(out.variables.size());
    out.rc_valid_variable_count = out.primitive_variable_count;
    out.nonfixed_parent_variable_count = std::count_if(
        out.variables.begin(), out.variables.end(), [](const auto& variable) {
            return variable.parent.effective_count > 1;
        });
    if (out.nonfixed_parent_variable_count == 0) {
        out.failure_reason = "no_nonfixed_parent_primitive_variable";
        return out;
    }
    out.parent = summarize(out.variables, 'P');
    out.left = summarize(out.variables, 'L');
    out.right = summarize(out.variables, 'R');
    out.valid = std::isfinite(out.parent.D) && std::isfinite(out.left.D) &&
        std::isfinite(out.right.D) && std::isfinite(out.parent.H) &&
        std::isfinite(out.left.H) && std::isfinite(out.right.H);
    out.failure_reason = out.valid ? "none" : "nonfinite_domain_summary";
    return out;
}

K1AMRCDecision evaluateK1AMRCDecision(
        const C6CurrentSplitDecision& adaptive_mass,
        const Round49RCDomainProfile& profile,
        const std::string& rule,
        double certificate_tolerance) {
    K1AMRCDecision out;
    out.rule = rule;
    out.profile_valid = profile.valid;
    out.fallback_to_am = !profile.valid;
    out.fallback_reason = profile.valid ? "none" : profile.failure_reason;
    out.am_action = action(adaptive_mass);
    out.am_split = adaptive_mass.split_immediately;
    const bool d_rule = rule == "d-rcd" || rule == "d-rcds";
    const bool h_rule = rule == "h-rcd" || rule == "h-rcds";
    const bool separation_enabled = rule == "d-rcds" || rule == "h-rcds";
    if (!adaptive_mass.valid || !adaptive_mass.adaptive_mass_enabled ||
        (!d_rule && !h_rule) || !std::isfinite(certificate_tolerance) ||
        certificate_tolerance < 0.0) {
        out.reason = "invalid_rc_decision_inputs";
        return out;
    }
    out.summary = d_rule ? "D" : "H";
    out.parent_summary = d_rule ? profile.parent.D : profile.parent.H;
    out.left_summary = d_rule ? profile.left.D : profile.left.H;
    out.right_summary = d_rule ? profile.right.D : profile.right.H;
    out.numerical_tolerance = numericalTolerance(certificate_tolerance,
        {out.parent_summary, out.left_summary, out.right_summary});
    out.exact_domain_count_margin =
        static_cast<double>(profile.parent.residual_count) - 0.5 *
        static_cast<double>(profile.left.residual_count +
                            profile.right.residual_count);
    out.dominance = profile.valid &&
        out.left_summary <= out.parent_summary + out.numerical_tolerance &&
        out.right_summary <= out.parent_summary + out.numerical_tolerance;
    out.strict_mean_improvement = profile.valid &&
        0.5 * (out.left_summary + out.right_summary) <
            out.parent_summary - out.numerical_tolerance;
    out.exact_separation = profile.valid &&
        profile.disjoint_domain_count > 0;
    const bool rcd = out.dominance && out.strict_mean_improvement;
    const bool rcds = separation_enabled && out.dominance &&
        out.exact_separation;
    out.rescue_activated = !out.am_split && profile.valid && (rcd || rcds);
    out.final_action = out.am_split || out.rescue_activated
        ? "split" : out.am_action;
    if (out.am_split) {
        out.reason = "existing_am_split_preserved";
    } else if (!profile.valid) {
        out.reason = "invalid_rc_profile_exact_am_fallback";
    } else if (rcd) {
        out.reason = out.summary + "_reduced_cost_domain_dominance";
    } else if (rcds) {
        out.reason = out.summary +
            "_dominance_exact_child_domain_separation";
    } else {
        out.reason = out.summary + "_no_parameter_free_rc_rescue";
    }
    out.valid = true;
    std::ostringstream identity;
    identity << std::setprecision(17) << kRound49RCProfileVersion << '|'
        << rule << '|' << profile.verified_incumbent << '|'
        << profile.parent_lp_bound << '|' << profile.left_lp_bound << '|'
        << profile.right_lp_bound << '|'
        << profile.parent_model_fingerprint << '|'
        << profile.left_model_fingerprint << '|'
        << profile.right_model_fingerprint << '|'
        << out.parent_summary << '|' << out.left_summary << '|'
        << out.right_summary << '|' << profile.primitive_variable_count << '|'
        << profile.parent.residual_count << '|' << profile.left.residual_count
        << '|' << profile.right.residual_count << '|'
        << profile.disjoint_domain_count << '|' << out.am_action << '|'
        << out.final_action << '|' << out.reason;
    for (const Round49RCVariableDomain& variable : profile.variables) {
        identity << '|' << variable.variable << ':' << variable.family
            << ':' << variable.parent.effective_lower
            << ':' << variable.parent.effective_upper
            << ':' << variable.parent.rc_lower << ':' << variable.parent.rc_upper
            << ':' << variable.parent.primal_value
            << ':' << variable.parent.reduced_cost
            << ':' << variable.parent.variable_basis_status
            << ':' << variable.left.effective_lower
            << ':' << variable.left.effective_upper
            << ':' << variable.left.rc_lower << ':' << variable.left.rc_upper
            << ':' << variable.left.primal_value
            << ':' << variable.left.reduced_cost
            << ':' << variable.left.variable_basis_status
            << ':' << variable.right.effective_lower
            << ':' << variable.right.effective_upper
            << ':' << variable.right.rc_lower << ':' << variable.right.rc_upper
            << ':' << variable.right.primal_value
            << ':' << variable.right.reduced_cost
            << ':' << variable.right.variable_basis_status
            << ':' << variable.exact_child_disjoint;
    }
    out.decision_hash = fnvHash(identity.str());
    return out;
}

void applyK1AMRCDecision(C6CurrentSplitDecision& adaptive_mass,
                         const K1AMRCDecision& decision) {
    if (!decision.valid || !decision.rescue_activated) return;
    adaptive_mass.split_immediately = true;
    adaptive_mass.run_child_bound_target = false;
    adaptive_mass.launch_exact_closure = false;
    adaptive_mass.contract_single_child = false;
    adaptive_mass.close_parent_infeasible = false;
    adaptive_mass.reason = "round49_rc_rescue:" + decision.reason;
}

} // namespace ebrp
