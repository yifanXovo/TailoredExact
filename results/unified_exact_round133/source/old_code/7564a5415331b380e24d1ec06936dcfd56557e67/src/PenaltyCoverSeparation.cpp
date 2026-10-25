#include "PenaltyCoverSeparation.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <utility>

namespace ebrp {
namespace {

bool choiceOrder(const PenaltyStateChoice& left,
                 const PenaltyStateChoice& right) {
    if (left.station != right.station) return left.station < right.station;
    return left.state < right.state;
}

std::int64_t saturatedAdd(std::int64_t current, std::int64_t addition,
                          std::int64_t cover_threshold) {
    if (current >= cover_threshold || addition >= cover_threshold ||
        addition > cover_threshold - current) {
        return cover_threshold;
    }
    return current + addition;
}

struct DpNode {
    double objective = 0.0;
    std::vector<int> selected_choice_indices;
};

bool betterNode(const DpNode& left, const DpNode& right,
                const std::vector<PenaltyStateChoice>& choices) {
    constexpr double tolerance = 1e-15;
    if (left.objective < right.objective - tolerance) return true;
    if (left.objective > right.objective + tolerance) return false;
    std::vector<PenaltyStateChoice> left_choices;
    std::vector<PenaltyStateChoice> right_choices;
    for (int index : left.selected_choice_indices) {
        left_choices.push_back(choices[static_cast<std::size_t>(index)]);
    }
    for (int index : right.selected_choice_indices) {
        right_choices.push_back(choices[static_cast<std::size_t>(index)]);
    }
    return penaltyCoverSignature(left_choices) <
        penaltyCoverSignature(right_choices);
}

} // namespace

std::string penaltyCoverSignature(
        const std::vector<PenaltyStateChoice>& supplied_choices) {
    std::vector<PenaltyStateChoice> choices = supplied_choices;
    std::sort(choices.begin(), choices.end(), choiceOrder);
    std::ostringstream out;
    out << "PC";
    for (const PenaltyStateChoice& choice : choices) {
        out << '|' << choice.station << ':' << choice.state;
    }
    return out.str();
}

bool validatePenaltyCover(const PenaltyCover& cover, std::string* reason) {
    if (!cover.valid) {
        if (reason) *reason = "cover_not_marked_valid";
        return false;
    }
    std::set<int> stations;
    std::int64_t total = 0;
    for (const PenaltyStateChoice& choice : cover.choices) {
        if (choice.station < 0 || choice.state < 0 ||
            choice.cost_numerator < 0 ||
            !std::isfinite(choice.selector_value) ||
            choice.selector_value < -1e-12 ||
            choice.selector_value > 1.0 + 1e-12) {
            if (reason) *reason = "invalid_cover_choice";
            return false;
        }
        if (!stations.insert(choice.station).second) {
            if (reason) *reason = "multiple_states_from_one_station";
            return false;
        }
        if (choice.cost_numerator >
            std::numeric_limits<std::int64_t>::max() - total) {
            if (reason) *reason = "cover_cost_overflow";
            return false;
        }
        total += choice.cost_numerator;
    }
    if (total != cover.total_cost_numerator ||
        total <= cover.budget_numerator || !cover.strict_cover) {
        if (reason) *reason = "not_a_strict_cover";
        return false;
    }
    if (penaltyCoverSignature(cover.choices) !=
        cover.canonical_signature) {
        if (reason) *reason = "cover_signature_mismatch";
        return false;
    }
    if (reason) *reason = "valid_strict_multiple_choice_cover";
    return true;
}

PenaltyCover makeInclusionMinimalPenaltyCover(
        std::vector<PenaltyStateChoice> choices,
        std::int64_t budget_numerator,
        double violation_tolerance) {
    PenaltyCover out;
    out.budget_numerator = budget_numerator;
    if (budget_numerator < 0 ||
        !(violation_tolerance >= 0.0) ||
        !std::isfinite(violation_tolerance)) {
        out.reason = "invalid_budget_or_tolerance";
        return out;
    }
    std::sort(choices.begin(), choices.end(), choiceOrder);
    std::set<int> stations;
    std::int64_t total = 0;
    for (const PenaltyStateChoice& choice : choices) {
        if (choice.station < 0 || choice.state < 0 ||
            choice.cost_numerator < 0 ||
            !std::isfinite(choice.selector_value) ||
            choice.selector_value < -1e-12 ||
            choice.selector_value > 1.0 + 1e-12 ||
            !stations.insert(choice.station).second ||
            choice.cost_numerator >
                std::numeric_limits<std::int64_t>::max() - total) {
            out.reason = "invalid_multiple_choice_cover_input";
            return out;
        }
        total += choice.cost_numerator;
    }
    if (total <= budget_numerator) {
        out.reason = "candidate_is_not_a_strict_cover";
        return out;
    }

    // Removing a redundant member cannot weaken the cover violation:
    // both the left side and the right side decrease by one selector term,
    // changing the violation by 1-s >= 0.
    bool changed = true;
    while (changed) {
        changed = false;
        for (std::size_t index = 0; index < choices.size(); ++index) {
            if (total - choices[index].cost_numerator > budget_numerator) {
                total -= choices[index].cost_numerator;
                choices.erase(choices.begin() +
                              static_cast<std::ptrdiff_t>(index));
                changed = true;
                break;
            }
        }
    }

    out.valid = true;
    out.strict_cover = true;
    out.total_cost_numerator = total;
    out.choices = std::move(choices);
    out.canonical_signature = penaltyCoverSignature(out.choices);
    out.selector_lhs = 0.0;
    out.separation_objective = 0.0;
    for (const PenaltyStateChoice& choice : out.choices) {
        out.selector_lhs += choice.selector_value;
        out.separation_objective += 1.0 - choice.selector_value;
    }
    out.violation = out.selector_lhs -
        static_cast<double>(out.choices.size() - 1);
    out.violated = out.separation_objective < 1.0 - violation_tolerance;
    out.reason = out.violated
        ? "strict_violated_inclusion_minimal_cover"
        : "strict_nonviolated_inclusion_minimal_cover";
    return out;
}

PenaltyCoverSeparationResult separateExactMultipleChoicePenaltyCover(
        const PenaltyCoverSeparationInput& input) {
    PenaltyCoverSeparationResult out;
    if (input.budget_numerator < 0 ||
        input.budget_numerator ==
            std::numeric_limits<std::int64_t>::max() ||
        !(input.violation_tolerance >= 0.0) ||
        !std::isfinite(input.violation_tolerance)) {
        out.reason = "invalid_budget_or_tolerance";
        return out;
    }

    std::vector<PenaltyStateChoice> choices = input.choices;
    std::sort(choices.begin(), choices.end(), choiceOrder);
    std::map<int, std::vector<int>> by_station;
    std::set<std::pair<int, int>> identities;
    for (std::size_t index = 0; index < choices.size(); ++index) {
        const PenaltyStateChoice& choice = choices[index];
        if (choice.station < 0 || choice.state < 0 ||
            choice.cost_numerator < 0 ||
            !std::isfinite(choice.selector_value) ||
            choice.selector_value < -1e-12 ||
            choice.selector_value > 1.0 + 1e-12 ||
            !identities.insert({choice.station, choice.state}).second) {
            out.reason = "invalid_or_duplicate_station_state_choice";
            return out;
        }
        by_station[choice.station].push_back(static_cast<int>(index));
    }

    std::vector<std::map<int, int>> excluded_by_station;
    excluded_by_station.reserve(input.excluded_covers.size());
    for (const PenaltyCover& cover : input.excluded_covers) {
        std::string reason;
        if (!validatePenaltyCover(cover, &reason)) {
            out.reason = "invalid_excluded_cover:" + reason;
            return out;
        }
        std::map<int, int> mapping;
        for (const PenaltyStateChoice& choice : cover.choices) {
            mapping[choice.station] = choice.state;
        }
        excluded_by_station.push_back(std::move(mapping));
    }

    const std::int64_t threshold = input.budget_numerator + 1;
    using Key = std::pair<std::int64_t, std::string>;
    std::map<Key, DpNode> layer;
    layer[{0, std::string(input.excluded_covers.size(), '0')}] = DpNode{};
    out.dynamic_programming_states = 1;

    for (const auto& station_entry : by_station) {
        const int station = station_entry.first;
        std::vector<int> options = {-1}; // choose no state from this station
        options.insert(options.end(), station_entry.second.begin(),
                       station_entry.second.end());
        std::map<Key, DpNode> next;
        for (const auto& state_entry : layer) {
            for (int option : options) {
                ++out.dynamic_programming_transitions;
                const int selected_state = option < 0
                    ? std::numeric_limits<int>::min()
                    : choices[static_cast<std::size_t>(option)].state;
                const std::int64_t cost = option < 0 ? 0
                    : choices[static_cast<std::size_t>(option)].cost_numerator;
                Key key = state_entry.first;
                key.first = saturatedAdd(key.first, cost, threshold);
                for (std::size_t excluded = 0;
                     excluded < excluded_by_station.size(); ++excluded) {
                    const auto expected =
                        excluded_by_station[excluded].find(station);
                    if (expected != excluded_by_station[excluded].end() &&
                        selected_state != expected->second) {
                        key.second[excluded] = '1';
                    }
                }
                DpNode candidate = state_entry.second;
                if (option >= 0) {
                    candidate.objective += 1.0 -
                        choices[static_cast<std::size_t>(option)].selector_value;
                    candidate.selected_choice_indices.push_back(option);
                }
                const auto found = next.find(key);
                if (found == next.end() ||
                    betterNode(candidate, found->second, choices)) {
                    next[key] = std::move(candidate);
                }
            }
        }
        layer = std::move(next);
        out.dynamic_programming_states +=
            static_cast<long long>(layer.size());
    }

    const std::string all_excluded_missed(
        input.excluded_covers.size(), '1');
    const auto found = layer.find({threshold, all_excluded_missed});
    out.valid = true;
    if (found == layer.end()) {
        out.reason = "no_nonduplicate_strict_cover_exists";
        return out;
    }
    std::vector<PenaltyStateChoice> selected;
    for (int index : found->second.selected_choice_indices) {
        selected.push_back(choices[static_cast<std::size_t>(index)]);
    }
    out.cover = makeInclusionMinimalPenaltyCover(
        std::move(selected), input.budget_numerator,
        input.violation_tolerance);
    if (!out.cover.valid) {
        out.valid = false;
        out.reason = "dp_reconstruction_failed:" + out.cover.reason;
        return out;
    }
    out.cover_found = true;
    out.violated_cover_found = out.cover.violated;
    out.reason = out.cover.violated
        ? "exact_violated_cover_found"
        : "exact_best_cover_not_violated";
    return out;
}

} // namespace ebrp
