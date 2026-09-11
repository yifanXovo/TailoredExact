#include "Round52TailoredCuts.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {

std::string pName(int vehicle, int station) {
    return "p_" + std::to_string(vehicle) + "_" +
        std::to_string(station);
}

std::string zName(int vehicle, int station) {
    return "z_" + std::to_string(vehicle) + "_" +
        std::to_string(station);
}

std::string exactDouble(double value) {
    std::ostringstream out;
    out << std::hexfloat << value;
    return out.str();
}

void setReason(std::string* reason, const std::string& value) {
    if (reason) *reason = value;
}

void supportsRecursive(int next, int station_count, int remaining,
                       std::vector<int>& current,
                       std::vector<std::vector<int>>& out) {
    if (remaining == 0) {
        out.push_back(current);
        return;
    }
    for (int station = next;
         station <= station_count - remaining + 1; ++station) {
        current.push_back(station);
        supportsRecursive(station + 1, station_count, remaining - 1,
                          current, out);
        current.pop_back();
    }
}

double valueOf(const std::unordered_map<std::string, double>& values,
               const std::string& name) {
    const auto found = values.find(name);
    if (found == values.end() || !std::isfinite(found->second)) {
        throw std::runtime_error("round52_separator_variable_missing:" + name);
    }
    return found->second;
}

} // namespace

double round52RouteDurationLowerBound(
    const Instance& instance, std::vector<int> support) {
    if (support.size() < 2 || support.size() > 4 ||
        instance.V <= 0 ||
        instance.dist.size() != static_cast<std::size_t>(instance.V + 1)) {
        throw std::runtime_error("round52_route_support_invalid");
    }
    std::sort(support.begin(), support.end());
    if (std::adjacent_find(support.begin(), support.end()) != support.end() ||
        support.front() < 1 || support.back() > instance.V) {
        throw std::runtime_error("round52_route_support_station_invalid");
    }
    double best = std::numeric_limits<double>::infinity();
    do {
        double duration = instance.dist[0][static_cast<std::size_t>(support[0])];
        for (std::size_t index = 1; index < support.size(); ++index) {
            duration += instance.dist[static_cast<std::size_t>(support[index - 1])]
                                     [static_cast<std::size_t>(support[index])];
        }
        duration += instance.dist[static_cast<std::size_t>(support.back())][0];
        if (!std::isfinite(duration) || duration < 0.0) {
            throw std::runtime_error("round52_route_duration_invalid");
        }
        best = std::min(best, duration);
    } while (std::next_permutation(support.begin(), support.end()));
    if (!std::isfinite(best)) {
        throw std::runtime_error("round52_route_duration_unavailable");
    }
    return best;
}

bool round52SeparationPermitted(
    Round52CutSeparationScope scope, bool root_node,
    bool optimal_relaxation) {
    if (!optimal_relaxation) return false;
    return scope == Round52CutSeparationScope::AllOptimalTreeNodes ||
        root_node;
}

std::vector<Round52CutCandidate> Round52SupportDurationSeparator::separate(
    const Round52CutSeparationInput& input) const {
    if (!input.instance || !input.optimal_relaxation ||
        input.maximum_support_rank < 2 || input.maximum_support_rank > 4 ||
        !std::isfinite(input.certificate_tolerance) ||
        input.certificate_tolerance < 0.0) {
        throw std::runtime_error("round52_separator_input_invalid");
    }
    const Instance& instance = *input.instance;
    const double handling = instance.pickup_time + instance.drop_time;
    if (!std::isfinite(handling) || handling < 0.0 ||
        !std::isfinite(instance.total_time_limit)) {
        throw std::runtime_error("round52_separator_problem_data_invalid");
    }
    std::vector<Round52CutCandidate> cuts;
    for (int rank = 2; rank <= input.maximum_support_rank; ++rank) {
        std::vector<std::vector<int>> supports;
        std::vector<int> current;
        supportsRecursive(1, instance.V, rank, current, supports);
        for (int vehicle = 0; vehicle < instance.M; ++vehicle) {
            for (const auto& support : supports) {
                Round52CutCandidate cut;
                cut.family = "support-duration-rank-" +
                    std::to_string(rank);
                cut.validity_scope = Round52CutValidityScope::Global;
                cut.sense = Round52CutSense::LessEqual;
                cut.generating_interval = input.interval_id;
                cut.generating_context = input.node_context;
                cut.support_set = support;
                cut.vehicle_index = vehicle;
                const double route = round52RouteDurationLowerBound(
                    instance, support);
                cut.rhs = instance.total_time_limit - route +
                    route * static_cast<double>(rank);
                double lhs = 0.0;
                double scale_terms = 0.0;
                for (int station : support) {
                    const std::string p = pName(vehicle, station);
                    const std::string z = zName(vehicle, station);
                    if (input.model_variable_mapping.find(p) ==
                            input.model_variable_mapping.end() ||
                        input.model_variable_mapping.find(z) ==
                            input.model_variable_mapping.end()) {
                        throw std::runtime_error(
                            "round52_separator_model_mapping_missing");
                    }
                    const double p_value = valueOf(input.lp_values, p);
                    const double z_value = valueOf(input.lp_values, z);
                    // Bounds are consumed and validated even though this
                    // globally valid family does not need them for lifting.
                    const double p_lb = valueOf(
                        input.effective_lower_bounds, p);
                    const double p_ub = valueOf(
                        input.effective_upper_bounds, p);
                    const double z_lb = valueOf(
                        input.effective_lower_bounds, z);
                    const double z_ub = valueOf(
                        input.effective_upper_bounds, z);
                    if (p_lb > p_ub || z_lb > z_ub ||
                        p_value < p_lb - input.certificate_tolerance ||
                        p_value > p_ub + input.certificate_tolerance ||
                        z_value < z_lb - input.certificate_tolerance ||
                        z_value > z_ub + input.certificate_tolerance) {
                        throw std::runtime_error(
                            "round52_separator_effective_bounds_invalid");
                    }
                    cut.coefficients.push_back({p, handling});
                    cut.coefficients.push_back({z, route});
                    lhs += handling * p_value + route * z_value;
                    scale_terms += std::fabs(handling) *
                        std::max(1.0, std::fabs(p_value));
                    scale_terms += std::fabs(route) *
                        std::max(1.0, std::fabs(z_value));
                }
                cut.raw_violation = lhs - cut.rhs;
                cut.violation_scale = std::max({
                    1.0, std::fabs(cut.rhs), scale_terms});
                cut.scaled_violation =
                    cut.raw_violation / cut.violation_scale;
                std::ostringstream metadata;
                metadata << "tau_route=" << std::setprecision(17) << route
                         << ";handling=" << handling
                         << ";rank=" << rank
                         << ";route_lb=exact_depot_permutation";
                cut.derivation_metadata = metadata.str();
                cuts.push_back(std::move(cut));
            }
        }
    }
    return cuts;
}

bool normalizeRound52CutCandidate(
    Round52CutCandidate& candidate, std::string* reason) {
    if (candidate.family.empty() || !std::isfinite(candidate.rhs) ||
        !std::isfinite(candidate.raw_violation) ||
        !std::isfinite(candidate.scaled_violation) ||
        !std::isfinite(candidate.violation_scale) ||
        candidate.violation_scale < 1.0 || candidate.coefficients.empty()) {
        setReason(reason, "invalid_scalar_or_empty_family");
        return false;
    }
    if (candidate.sense == Round52CutSense::Equal) {
        setReason(reason, "equality_user_cut_not_supported");
        return false;
    }
    std::map<std::string, double> combined;
    for (const auto& coefficient : candidate.coefficients) {
        if (coefficient.variable.empty() ||
            !std::isfinite(coefficient.value)) {
            setReason(reason, "invalid_sparse_coefficient");
            return false;
        }
        combined[coefficient.variable] += coefficient.value;
    }
    candidate.coefficients.clear();
    for (const auto& item : combined) {
        if (item.second != 0.0) {
            candidate.coefficients.push_back({item.first, item.second});
        }
    }
    if (candidate.coefficients.empty()) {
        setReason(reason, "zero_row");
        return false;
    }
    if (candidate.sense == Round52CutSense::GreaterEqual) {
        for (auto& coefficient : candidate.coefficients) {
            coefficient.value = -coefficient.value;
        }
        candidate.rhs = -candidate.rhs;
        candidate.sense = Round52CutSense::LessEqual;
    }
    double normalization = 0.0;
    for (const auto& coefficient : candidate.coefficients) {
        normalization = std::max(normalization, std::fabs(coefficient.value));
    }
    if (!(normalization > 0.0) || !std::isfinite(normalization)) {
        setReason(reason, "normalization_invalid");
        return false;
    }
    std::ostringstream lhs;
    lhs << "<=|";
    for (const auto& coefficient : candidate.coefficients) {
        lhs << coefficient.variable << ':'
            << exactDouble(coefficient.value / normalization) << ';';
    }
    candidate.canonical_lhs_signature = lhs.str();
    candidate.canonical_signature = candidate.canonical_lhs_signature +
        "rhs:" + exactDouble(candidate.rhs / normalization);
    setReason(reason, "none");
    return true;
}

bool round52ExactlyDominates(const Round52CutCandidate& dominating,
                             const Round52CutCandidate& dominated) {
    if (dominating.sense != Round52CutSense::LessEqual ||
        dominated.sense != Round52CutSense::LessEqual ||
        dominating.canonical_lhs_signature.empty() ||
        dominating.canonical_lhs_signature !=
            dominated.canonical_lhs_signature ||
        dominating.coefficients.size() != dominated.coefficients.size()) {
        return false;
    }
    double left_scale = 0.0;
    double right_scale = 0.0;
    for (const auto& value : dominating.coefficients) {
        left_scale = std::max(left_scale, std::fabs(value.value));
    }
    for (const auto& value : dominated.coefficients) {
        right_scale = std::max(right_scale, std::fabs(value.value));
    }
    if (!(left_scale > 0.0) || !(right_scale > 0.0)) return false;
    return dominating.rhs / left_scale <= dominated.rhs / right_scale;
}

Round52CutManager::Round52CutManager(Round52CutManagerConfig config)
    : config_(config) {
    if (!std::isfinite(config_.certificate_tolerance) ||
        config_.certificate_tolerance < 0.0) {
        throw std::runtime_error("round52_cut_manager_tolerance_invalid");
    }
}

void Round52CutManager::beginModel(const std::string& model_identity) {
    if (model_identity.empty()) {
        throw std::runtime_error("round52_cut_model_identity_empty");
    }
    if (model_identity_ != model_identity) {
        global_pool_.clear();
        telemetry_ = {};
        model_identity_ = model_identity;
    }
}

std::vector<Round52CutCandidate> Round52CutManager::process(
    std::vector<Round52CutCandidate> candidates) {
    if (model_identity_.empty()) {
        throw std::runtime_error("round52_cut_manager_model_not_started");
    }
    telemetry_.generated += static_cast<long long>(candidates.size());
    std::vector<Round52CutCandidate> eligible;
    std::set<std::string> batch_signatures;
    for (auto& candidate : candidates) {
        ++telemetry_.generated_by_family[candidate.family];
        std::string reason;
        if (!normalizeRound52CutCandidate(candidate, &reason)) {
            ++telemetry_.invalid_rejections;
            continue;
        }
        if (!(candidate.raw_violation >
              config_.certificate_tolerance * candidate.violation_scale)) {
            ++telemetry_.nonviolated_rejections;
            continue;
        }
        ++telemetry_.violated;
        ++telemetry_.violated_by_family[candidate.family];
        if (global_pool_.find(candidate.canonical_signature) !=
                global_pool_.end() ||
            !batch_signatures.insert(candidate.canonical_signature).second) {
            ++telemetry_.duplicate_rejections;
            continue;
        }
        bool dominated = false;
        for (const auto& pool_item : global_pool_) {
            if (round52ExactlyDominates(pool_item.second, candidate)) {
                dominated = true;
                break;
            }
        }
        if (dominated) {
            ++telemetry_.dominated_rejections;
            continue;
        }
        eligible.push_back(std::move(candidate));
    }
    std::vector<Round52CutCandidate> undominated;
    undominated.reserve(eligible.size());
    for (std::size_t index = 0; index < eligible.size(); ++index) {
        bool dominated = false;
        for (std::size_t other = 0; other < eligible.size(); ++other) {
            if (index != other &&
                round52ExactlyDominates(eligible[other], eligible[index])) {
                dominated = true;
                break;
            }
        }
        if (dominated) {
            ++telemetry_.dominated_rejections;
        } else {
            undominated.push_back(std::move(eligible[index]));
        }
    }
    eligible = std::move(undominated);
    std::sort(eligible.begin(), eligible.end(),
        [](const Round52CutCandidate& left,
           const Round52CutCandidate& right) {
            if (left.vehicle_index != right.vehicle_index) {
                return left.vehicle_index < right.vehicle_index;
            }
            if (left.scaled_violation != right.scaled_violation) {
                return left.scaled_violation > right.scaled_violation;
            }
            return left.canonical_signature < right.canonical_signature;
        });
    std::vector<Round52CutCandidate> selected;
    if (config_.selection_rule ==
            Round52CutSelectionRule::VehicleBlockMaximum) {
        std::set<int> vehicles;
        for (auto& candidate : eligible) {
            if (vehicles.insert(candidate.vehicle_index).second) {
                selected.push_back(std::move(candidate));
            }
        }
    } else {
        selected = std::move(eligible);
    }
    telemetry_.selected += static_cast<long long>(selected.size());
    for (const auto& candidate : selected) {
        ++telemetry_.selected_by_family[candidate.family];
        ++telemetry_.selected_by_vehicle[candidate.vehicle_index];
    }
    return selected;
}

void Round52CutManager::recordSubmission(
    const Round52CutCandidate& candidate, bool added) {
    ++telemetry_.submission_attempts;
    if (added) {
        ++telemetry_.added;
        ++telemetry_.added_by_family[candidate.family];
        global_pool_[candidate.canonical_signature] = candidate;
    } else {
        ++telemetry_.submission_failures;
    }
    telemetry_.global_pool_size = global_pool_.size();
}

void Round52CutManager::recordDryRunSelection(
    const Round52CutCandidate& candidate) {
    global_pool_[candidate.canonical_signature] = candidate;
    telemetry_.global_pool_size = global_pool_.size();
}

bool Round52CutManager::globalPoolContains(
    const std::string& canonical_signature) const {
    return global_pool_.find(canonical_signature) != global_pool_.end();
}

void Round52CutManager::recordCallback(bool root) {
    ++telemetry_.callback_calls;
    if (root) ++telemetry_.root_callback_calls;
    else ++telemetry_.tree_callback_calls;
}

void Round52CutManager::recordCallbackFailure() {
    ++telemetry_.callback_failures;
}

std::string round52CutSenseName(Round52CutSense sense) {
    if (sense == Round52CutSense::LessEqual) return "<=";
    if (sense == Round52CutSense::GreaterEqual) return ">=";
    return "=";
}

std::string round52CutScopeName(Round52CutValidityScope scope) {
    return scope == Round52CutValidityScope::Global ? "global" : "local";
}

} // namespace ebrp
