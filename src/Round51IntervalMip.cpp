#include "Round51IntervalMip.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <map>

namespace ebrp {

double round51SubsetDurationBigM(double tsp_bound, double tolerance) {
    if (!std::isfinite(tsp_bound)) {
        throw std::runtime_error(
            "round51_subset_duration_tsp_bound_nonfinite");
    }
    if (!std::isfinite(tolerance) || tolerance < 0.0) {
        throw std::runtime_error(
            "round51_subset_duration_tolerance_invalid");
    }
    if (tsp_bound < -tolerance) {
        throw std::runtime_error(
            "round51_subset_duration_tsp_bound_negative");
    }
    return std::max(0.0, tsp_bound);
}

Round51SubsetDurationRowValues round51SubsetDurationRowValues(
    double tsp_bound,
    double total_time_limit,
    int subset_cardinality,
    double tolerance) {
    if (!std::isfinite(total_time_limit)) {
        throw std::runtime_error(
            "round51_subset_duration_time_limit_nonfinite");
    }
    if (subset_cardinality <= 0) {
        throw std::runtime_error(
            "round51_subset_duration_cardinality_invalid");
    }
    Round51SubsetDurationRowValues out;
    out.tsp_bound = tsp_bound;
    out.big_m = round51SubsetDurationBigM(tsp_bound, tolerance);
    out.visit_coefficient = out.big_m;
    out.rhs = total_time_limit - tsp_bound +
        out.big_m * static_cast<double>(subset_cardinality);
    if (!std::isfinite(out.rhs) ||
        std::fabs(out.visit_coefficient - out.big_m) > tolerance ||
        std::fabs(out.rhs - (total_time_limit - tsp_bound +
            out.big_m * static_cast<double>(subset_cardinality))) >
                tolerance) {
        throw std::runtime_error(
            "round51_subset_duration_row_formula_mismatch");
    }
    return out;
}

double round51Fractionality(double value) {
    if (!std::isfinite(value)) {
        throw std::runtime_error("round51_root_value_nonfinite");
    }
    return std::min(value - std::floor(value),
                    std::ceil(value) - value);
}

std::vector<Round51AdaptiveCandidate> round51AdaptiveCandidatePool(
    const std::vector<Round51RootVariable>& variables,
    double integrality_tolerance) {
    if (!std::isfinite(integrality_tolerance) ||
        integrality_tolerance < 0.0) {
        throw std::runtime_error(
            "round51_integrality_tolerance_invalid");
    }
    std::vector<Round51AdaptiveCandidate> eligible;
    for (const Round51RootVariable& variable : variables) {
        if (variable.original_type != 'B' && variable.original_type != 'I') {
            continue;
        }
        if (variable.name.empty() ||
            !std::isfinite(variable.lower_bound) ||
            !std::isfinite(variable.upper_bound) ||
            !std::isfinite(variable.root_value)) {
            throw std::runtime_error(
                "round51_root_variable_metadata_invalid");
        }
        if (variable.upper_bound - variable.lower_bound <= 1e-12) continue;
        const Round50VariableFamily family =
            classifyRound50Variable(variable.name);
        if (family == Round50VariableFamily::Auxiliary) continue;
        const double fractionality = round51Fractionality(variable.root_value);
        if (fractionality <= integrality_tolerance) continue;
        const double down = std::floor(variable.root_value);
        const double up = std::ceil(variable.root_value);
        if (down < variable.lower_bound - integrality_tolerance ||
            up > variable.upper_bound + integrality_tolerance) {
            throw std::runtime_error(
                "round51_fractional_root_value_outside_domain");
        }
        Round51AdaptiveCandidate candidate;
        candidate.name = variable.name;
        candidate.family = family;
        candidate.original_type = variable.original_type;
        candidate.lower_bound = variable.lower_bound;
        candidate.upper_bound = variable.upper_bound;
        candidate.root_value = variable.root_value;
        candidate.fractionality = fractionality;
        candidate.down_upper_bound = down;
        candidate.up_lower_bound = up;
        eligible.push_back(std::move(candidate));
    }
    std::sort(eligible.begin(), eligible.end(),
        [](const Round51AdaptiveCandidate& left,
           const Round51AdaptiveCandidate& right) {
            if (left.fractionality != right.fractionality) {
                return left.fractionality > right.fractionality;
            }
            if (left.family != right.family) {
                return static_cast<int>(left.family) <
                    static_cast<int>(right.family);
            }
            return left.name < right.name;
        });
    std::map<Round50VariableFamily, int> family_counts;
    std::vector<Round51AdaptiveCandidate> pool;
    for (Round51AdaptiveCandidate candidate : eligible) {
        if (family_counts[candidate.family] >= 2) continue;
        ++family_counts[candidate.family];
        candidate.pool_order = static_cast<int>(pool.size());
        pool.push_back(std::move(candidate));
        if (pool.size() == 4) break;
    }
    return pool;
}

Round51ScoredCandidate round51ScoreAdaptiveCandidate(
    const Round51AdaptiveCandidate& candidate,
    const Round51ProbeDirection& down,
    const Round51ProbeDirection& up,
    double root_objective,
    double verified_cutoff) {
    if (!std::isfinite(root_objective) || !std::isfinite(verified_cutoff)) {
        throw std::runtime_error("round51_probe_objective_input_nonfinite");
    }
    const double gap = std::max(verified_cutoff - root_objective, 1e-9);
    auto delta = [&](const Round51ProbeDirection& probe,
                     bool& valid) {
        if (probe.status == Round51ProbeStatus::Infeasible) return gap;
        if (probe.status != Round51ProbeStatus::Optimal ||
            !std::isfinite(probe.child_objective)) {
            valid = false;
            return 0.0;
        }
        return std::max(0.0, std::min(
            gap, probe.child_objective - root_objective));
    };
    Round51ScoredCandidate out;
    out.candidate = candidate;
    out.down = down;
    out.up = up;
    out.valid = true;
    out.delta_down = delta(down, out.valid);
    out.delta_up = delta(up, out.valid);
    if (out.valid) {
        out.score = std::max(out.delta_down, 1e-7) *
            std::max(out.delta_up, 1e-7);
    }
    return out;
}

Round51PrioritySelection round51SelectSparsePriorities(
    std::vector<Round51ScoredCandidate> scored,
    double improvement_tolerance) {
    if (!std::isfinite(improvement_tolerance) ||
        improvement_tolerance < 0.0) {
        throw std::runtime_error(
            "round51_improvement_tolerance_invalid");
    }
    Round51PrioritySelection out;
    for (Round51ScoredCandidate& candidate : scored) {
        if (candidate.valid) {
            out.ranked_valid_candidates.push_back(std::move(candidate));
        }
    }
    if (out.ranked_valid_candidates.empty()) {
        out.fallback_reason = "no_candidate_with_two_valid_probes";
        return out;
    }
    std::sort(out.ranked_valid_candidates.begin(),
        out.ranked_valid_candidates.end(),
        [](const Round51ScoredCandidate& left,
           const Round51ScoredCandidate& right) {
            if (left.score != right.score) return left.score > right.score;
            return left.candidate.pool_order < right.candidate.pool_order;
        });
    bool positive = false;
    for (const Round51ScoredCandidate& candidate :
            out.ranked_valid_candidates) {
        positive = positive ||
            candidate.delta_down > improvement_tolerance ||
            candidate.delta_up > improvement_tolerance;
    }
    if (!positive) {
        out.fallback_reason = "all_valid_candidates_zero_improvement";
        return out;
    }
    out.fallback_to_default = false;
    out.fallback_reason = "none";
    const std::size_t count = std::min<std::size_t>(
        2, out.ranked_valid_candidates.size());
    for (std::size_t index = 0; index < count; ++index) {
        out.priorities.push_back({
            out.ranked_valid_candidates[index].candidate.name,
            index == 0 ? 2 : 1});
    }
    return out;
}

Round51PrioritySelection round51SelectTopOnePriority(
    std::vector<Round51ScoredCandidate> scored,
    double improvement_tolerance) {
    Round51PrioritySelection out = round51SelectSparsePriorities(
        std::move(scored), improvement_tolerance);
    if (!out.fallback_to_default) {
        if (out.priorities.empty()) {
            throw std::runtime_error(
                "round51_top_one_selection_missing_best_candidate");
        }
        out.priorities.resize(1);
        out.priorities.front().second = 1;
    }
    return out;
}

std::string round51ProbeStatusName(Round51ProbeStatus status) {
    switch (status) {
    case Round51ProbeStatus::Optimal: return "optimal";
    case Round51ProbeStatus::Infeasible: return "infeasible";
    case Round51ProbeStatus::Invalid: return "invalid";
    }
    return "invalid";
}

double round51AdaptiveTotal(double root_value,
                            const std::vector<double>& probe_values,
                            double terminal_value) {
    if (!std::isfinite(root_value) || root_value < 0.0 ||
        !std::isfinite(terminal_value) || terminal_value < 0.0) {
        throw std::runtime_error("round51_adaptive_accounting_invalid");
    }
    double total = root_value + terminal_value;
    for (double value : probe_values) {
        if (!std::isfinite(value) || value < 0.0) {
            throw std::runtime_error("round51_adaptive_accounting_invalid");
        }
        total += value;
    }
    return total;
}

} // namespace ebrp
