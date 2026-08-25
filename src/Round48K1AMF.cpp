#include "Round48K1AMF.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <limits>
#include <set>
#include <sstream>

namespace ebrp {
namespace {

using BoundMap = std::map<std::string, std::pair<double, double>>;

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

std::string trim(const std::string& value) {
    const std::size_t first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return "";
    return value.substr(first, value.find_last_not_of(" \t\r\n") - first + 1);
}

bool readBounds(const std::filesystem::path& path, BoundMap& bounds,
                std::string& reason) {
    std::ifstream input(path);
    if (!input) {
        reason = "canonical_model_open_failed:" + path.string();
        return false;
    }
    bool in_bounds = false;
    std::string raw;
    while (std::getline(input, raw)) {
        const std::string line = trim(raw);
        if (line == "Bounds") {
            in_bounds = true;
            continue;
        }
        if (in_bounds &&
            (line == "Binaries" || line == "Generals" || line == "End")) {
            break;
        }
        if (!in_bounds || line.empty()) continue;
        std::istringstream parsed(line);
        double lower = 0.0, upper = 0.0;
        std::string lower_op, variable, upper_op, trailing;
        if (!(parsed >> lower >> lower_op >> variable >> upper_op >> upper) ||
            (parsed >> trailing) || lower_op != "<=" || upper_op != "<=") {
            reason = "unsupported_canonical_bound_line:" + line;
            return false;
        }
        if (!bounds.emplace(variable, std::make_pair(lower, upper)).second) {
            reason = "duplicate_canonical_variable_bound:" + variable;
            return false;
        }
    }
    if (!in_bounds || bounds.empty()) {
        reason = "canonical_bounds_section_missing_or_empty:" + path.string();
        return false;
    }
    return true;
}

double clipped(double value) {
    return std::min(1.0, std::max(0.0, value));
}

double widthTolerance(double lower, double upper,
                      double certificate_tolerance) {
    const double scale = std::max({1.0, std::fabs(lower), std::fabs(upper)});
    return std::max(certificate_tolerance,
        32.0 * std::numeric_limits<double>::epsilon() * scale);
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

} // namespace

std::string round48AMFEligibleFamily(const std::string& variable) {
    if (indexed(variable, "Y_", 1)) return "final_inventory";
    if (indexed(variable, "r_", 1)) return "station_ratio";
    if (indexed(variable, "e_", 1)) return "absolute_deviation";
    if (indexed(variable, "h_", 2)) return "pairwise_ratio_difference";
    if (indexed(variable, "bit_", 2)) return "inventory_bit";
    if (indexed(variable, "prod_", 2)) return "gini_inventory_product";
    if (indexed(variable, "p_", 2)) return "pickup_movement";
    if (indexed(variable, "d_", 2)) return "drop_movement";
    if (variable == "W_SP") return "ratio_penalty_product";
    return "";
}

AMFFormulationProfile buildRound48AMFFormulationProfile(
        const std::filesystem::path& parent_model,
        const std::filesystem::path& left_model,
        const std::filesystem::path& right_model,
        double certificate_tolerance) {
    AMFFormulationProfile out;
    if (!std::isfinite(certificate_tolerance) || certificate_tolerance < 0.0) {
        out.failure_reason = "invalid_certificate_tolerance";
        return out;
    }
    BoundMap parent, left, right;
    if (!readBounds(parent_model, parent, out.failure_reason) ||
        !readBounds(left_model, left, out.failure_reason) ||
        !readBounds(right_model, right, out.failure_reason)) {
        return out;
    }
    std::set<std::string> candidates;
    for (const auto& item : parent) candidates.insert(item.first);
    for (const auto& item : left) candidates.insert(item.first);
    for (const auto& item : right) candidates.insert(item.first);
    for (const std::string& variable : candidates) {
        if (variable == "G" || variable.rfind("segment_G_", 0) == 0) {
            ++out.excluded_gini_variable_count;
            continue;
        }
        const std::string family = round48AMFEligibleFamily(variable);
        if (family.empty()) continue;
        const auto p = parent.find(variable);
        const auto l = left.find(variable);
        const auto r = right.find(variable);
        if (p == parent.end() || l == left.end() || r == right.end()) {
            ++out.invalid_variable_count;
            if (out.failure_reason == "not_evaluated") {
                out.failure_reason = "incomplete_effective_bounds:" + variable;
            }
            continue;
        }
        const double p_lower = p->second.first;
        const double p_upper = p->second.second;
        const double l_lower = l->second.first;
        const double l_upper = l->second.second;
        const double r_lower = r->second.first;
        const double r_upper = r->second.second;
        if (!std::isfinite(p_lower) || !std::isfinite(p_upper) ||
            !std::isfinite(l_lower) || !std::isfinite(l_upper) ||
            !std::isfinite(r_lower) || !std::isfinite(r_upper)) {
            ++out.invalid_variable_count;
            if (out.failure_reason == "not_evaluated") {
                out.failure_reason = "nonfinite_effective_bounds:" + variable;
            }
            continue;
        }
        const double p_width = p_upper - p_lower;
        const double l_width = l_upper - l_lower;
        const double r_width = r_upper - r_lower;
        const double tolerance = widthTolerance(
            p_lower, p_upper, certificate_tolerance);
        if (p_width <= tolerance) continue;
        const bool left_nonmonotone = l_lower < p_lower - tolerance ||
            l_upper > p_upper + tolerance || l_width > p_width + tolerance;
        const bool right_nonmonotone = r_lower < p_lower - tolerance ||
            r_upper > p_upper + tolerance || r_width > p_width + tolerance;
        if (left_nonmonotone || right_nonmonotone ||
            l_width < -tolerance || r_width < -tolerance) {
            ++out.invalid_variable_count;
            if (out.failure_reason == "not_evaluated") {
                out.failure_reason = "nonmonotone_child_domain:" + variable;
            }
            continue;
        }
        AMFVariableContraction item;
        item.variable = variable;
        item.family = family;
        item.parent_lower = p_lower;
        item.parent_upper = p_upper;
        item.parent_width = p_width;
        item.width_tolerance = tolerance;
        item.left_lower = l_lower;
        item.left_upper = l_upper;
        item.left_width = std::max(0.0, l_width);
        item.c_left = clipped(1.0 - item.left_width / p_width);
        item.right_lower = r_lower;
        item.right_upper = r_upper;
        item.right_width = std::max(0.0, r_width);
        item.c_right = clipped(1.0 - item.right_width / p_width);
        item.fixed_left = item.left_width <= tolerance;
        item.fixed_right = item.right_width <= tolerance;
        out.variables.push_back(item);
        ++out.family_counts[family];
    }
    out.eligible_variable_count = static_cast<long long>(out.variables.size());
    out.valid = out.invalid_variable_count == 0;
    if (!out.valid) {
        out.phi_left = 0.0;
        out.phi_right = 0.0;
        return out;
    }
    out.failure_reason = "none";
    if (out.variables.empty()) return out;
    out.left_min_contraction = 1.0;
    out.right_min_contraction = 1.0;
    for (const AMFVariableContraction& item : out.variables) {
        out.phi_left += item.c_left;
        out.phi_right += item.c_right;
        out.left_min_contraction = std::min(
            out.left_min_contraction, item.c_left);
        out.left_max_contraction = std::max(
            out.left_max_contraction, item.c_left);
        out.right_min_contraction = std::min(
            out.right_min_contraction, item.c_right);
        out.right_max_contraction = std::max(
            out.right_max_contraction, item.c_right);
        out.fixed_left_count += item.fixed_left ? 1 : 0;
        out.fixed_right_count += item.fixed_right ? 1 : 0;
    }
    out.phi_left /= static_cast<double>(out.variables.size());
    out.phi_right /= static_cast<double>(out.variables.size());
    out.left_mean_contraction = out.phi_left;
    out.right_mean_contraction = out.phi_right;
    return out;
}

K1AMFDecision evaluateK1AMFDecision(
        const C6CurrentSplitDecision& adaptive_mass,
        const AMFFormulationProfile& profile,
        double tau) {
    K1AMFDecision out;
    out.tau = tau;
    out.profile_valid = profile.valid;
    out.fallback_to_am = !profile.valid;
    out.fallback_reason = profile.valid ? "none" : profile.failure_reason;
    out.g_left = adaptive_mass.g_left;
    out.g_right = adaptive_mass.g_right;
    out.eta = adaptive_mass.adaptive_eta;
    out.mu = adaptive_mass.adaptive_mu;
    out.s_am = adaptive_mass.adaptive_mass_score;
    out.score_tolerance = adaptive_mass.adaptive_score_tolerance;
    out.am_split = adaptive_mass.split_immediately;
    out.am_action = action(adaptive_mass);
    if (!adaptive_mass.valid || !adaptive_mass.adaptive_mass_enabled ||
        !std::isfinite(tau) || tau < 0.0 || tau > 1.0 ||
        !std::isfinite(out.g_left) || !std::isfinite(out.g_right) ||
        !std::isfinite(out.mu) || !std::isfinite(out.s_am) ||
        !std::isfinite(out.score_tolerance)) {
        out.reason = "invalid_amf_inputs";
        return out;
    }
    out.phi_left = profile.valid ? profile.phi_left : 0.0;
    out.phi_right = profile.valid ? profile.phi_right : 0.0;
    if (!std::isfinite(out.phi_left) || !std::isfinite(out.phi_right) ||
        out.phi_left < 0.0 || out.phi_left > 1.0 ||
        out.phi_right < 0.0 || out.phi_right > 1.0) {
        out.profile_valid = false;
        out.fallback_to_am = true;
        out.fallback_reason = "nonfinite_or_out_of_range_phi";
        out.phi_left = out.phi_right = 0.0;
    }
    out.gtilde_left = out.g_left + out.phi_left *
        std::max(out.g_right - out.g_left, 0.0);
    out.gtilde_right = out.g_right + out.phi_right *
        std::max(out.g_left - out.g_right, 0.0);
    out.eta_hat = std::min(out.gtilde_left, out.gtilde_right);
    out.s_amf = out.mu * out.eta_hat;
    out.amf_split = out.s_amf + out.score_tolerance >= tau;
    if (adaptive_mass.child_infeasibility_trigger) {
        out.amf_split = adaptive_mass.split_immediately;
    }
    out.rescue_activated = !out.am_split && out.amf_split;
    out.amf_action = out.amf_split ? "split" : out.am_action;
    out.reason = out.fallback_to_am
        ? "amf_invalid_profile_exact_am_fallback"
        : (out.rescue_activated
            ? "amf_formulation_credit_reaches_tau"
            : (out.amf_split
                ? "amf_or_am_score_reaches_tau"
                : "amf_score_below_tau_preserve_am_lifecycle"));
    const double max_gain = std::max(out.g_left, out.g_right);
    const double tolerance = 1e-12;
    out.valid = std::isfinite(out.gtilde_left) &&
        std::isfinite(out.gtilde_right) && std::isfinite(out.eta_hat) &&
        std::isfinite(out.s_amf) &&
        out.eta_hat + tolerance >= out.eta &&
        out.eta_hat <= max_gain + tolerance &&
        out.s_amf + tolerance >= out.s_am;
    if (!out.valid) out.reason = "amf_mathematical_invariant_failed";
    std::ostringstream identity;
    identity << std::setprecision(17) << kRound48AMFProfileVersion << '|'
        << out.g_left << '|' << out.g_right << '|' << out.mu << '|'
        << out.phi_left << '|' << out.phi_right << '|' << out.eta_hat << '|'
        << out.s_amf << '|' << out.tau << '|' << out.score_tolerance << '|'
        << out.am_action << '|' << out.amf_action << '|'
        << out.profile_valid << '|' << out.fallback_reason;
    out.decision_hash = fnvHash(identity.str());
    return out;
}

void applyK1AMFDecision(C6CurrentSplitDecision& adaptive_mass,
                        const K1AMFDecision& amf) {
    if (!amf.valid || !amf.rescue_activated) return;
    adaptive_mass.split_immediately = true;
    adaptive_mass.run_child_bound_target = false;
    adaptive_mass.launch_exact_closure = false;
    adaptive_mass.reason = amf.reason;
}

} // namespace ebrp
