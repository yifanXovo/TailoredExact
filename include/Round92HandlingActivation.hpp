#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ebrp {

// Mirrors CplexBaseline's addTerm/writeExpr representation for a coefficient
// that occurs exactly once in a row. Integrators must use this SAME value
// both in the original duration row and in the Round92 proof input.
// Reject negative/nonfinite physical inputs before calling it.
double round92CanonicalEmittedCoefficient(double value);

struct Round92DurationCoefficients {
    double horizon = 0.0;  // Actual duration-row RHS after max_digits10 output.
    double pickup = 0.0;   // Same coefficient on every p_{k,i} in that row.
    // [0..V][0..V]. nullopt means arc column absent; present zero is a real
    // allowed arc whose duration term was suppressed by canonical formatting.
    // Diagonal entries must be nullopt. All vehicle rows may share this data.
    std::vector<std::vector<std::optional<double>>> directed_travel;
};

struct Round92HandlingActivationPlan {
    bool valid_input = false;
    bool applicable = false;
    std::string reason;
    std::uint64_t integer_capacity = 0; // Safe upper-floor B, <=2^53.
    double activation_coefficient = 0.0; // -B in P_k-B*a_k <= 0.
    bool exact_integer_floor = false; // Lower and upper quotient floors agree.
    bool quotient_enclosure_available = false; // False for no closed route.
    double lmin_lower = 0.0;
    double lmin_upper = 0.0;
    double quotient_lower = 0.0;
    double quotient_upper = 0.0;
    int allowed_directed_arcs = 0;
    double preparation_wall_seconds = 0.0;
};

// Owned by one external-tree run; never shared between processes or solves.
// The key compares every emitted binary64 coefficient and arc-presence bit.
struct Round92HandlingActivationCache {
    static constexpr std::uint32_t kProofVersion = 1;
    std::uint32_t version = kProofVersion;
    bool ready = false;
    Round92DurationCoefficients key;
    Round92HandlingActivationPlan plan;
    std::uint64_t hits = 0;
    std::uint64_t misses = 0;
};

bool round92SameDurationKey(const Round92DurationCoefficients& a,
                            const Round92DurationCoefficients& b);

// O((V+1)^3), allocation-only; does not read an LP or invoke a solver.
// Invalid domains return !valid_input. A valid c=0 gives !applicable: the
// duration row has no service bound. With no closed station path, F0 and the
// depot/visit links imply P=0, and the plan emits B=0. The caller MUST have
// checked that the arc support is the actual original x-column support.
// A successful plan proves true P<=B*a using the quotient's outward UPPER
// bound. B may be weaker than the exact floor by an amount determined by the
// quotient enclosure; exact_integer_floor says when both floors certify
// equality. No instance-specific branch is taken.
Round92HandlingActivationPlan prepareRound92HandlingActivation(
    const Round92DurationCoefficients& actual_duration_row);

} // namespace ebrp
