#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace ebrp {

// Penalty coefficients and the budget are supplied in one proved exact
// integer scale.  The separator never converts floating-point penalty costs
// to integers, so a noncover cannot become a cover through rounding.
struct PenaltyStateChoice {
    int station = -1;
    int state = -1;
    std::int64_t cost_numerator = 0;
    double selector_value = 0.0;
};

struct PenaltyCover {
    bool valid = false;
    bool strict_cover = false;
    bool violated = false;
    std::int64_t budget_numerator = 0;
    std::int64_t total_cost_numerator = 0;
    double separation_objective = 0.0;
    double selector_lhs = 0.0;
    double violation = 0.0;
    std::vector<PenaltyStateChoice> choices;
    std::string canonical_signature;
    std::string reason = "not_evaluated";
};

struct PenaltyCoverSeparationInput {
    std::vector<PenaltyStateChoice> choices;
    std::int64_t budget_numerator = 0;
    double violation_tolerance = 1e-9;
    // Previously accepted inclusion-minimal covers.  The exact DP excludes
    // each cover and every strict superset of it.
    std::vector<PenaltyCover> excluded_covers;
};

struct PenaltyCoverSeparationResult {
    bool valid = false;
    bool cover_found = false;
    bool violated_cover_found = false;
    bool exact_integer_scaling = true;
    long long dynamic_programming_states = 0;
    long long dynamic_programming_transitions = 0;
    PenaltyCover cover;
    std::string reason = "not_evaluated";
};

std::string penaltyCoverSignature(
    const std::vector<PenaltyStateChoice>& choices);

bool validatePenaltyCover(const PenaltyCover& cover,
                          std::string* reason = nullptr);

PenaltyCover makeInclusionMinimalPenaltyCover(
    std::vector<PenaltyStateChoice> choices,
    std::int64_t budget_numerator,
    double violation_tolerance = 1e-9);

PenaltyCoverSeparationResult separateExactMultipleChoicePenaltyCover(
    const PenaltyCoverSeparationInput& input);

} // namespace ebrp
