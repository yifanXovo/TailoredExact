#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "Result.hpp"

namespace ebrp {

// Mirrors CplexBaseline's addTerm/writeExpr representation for a coefficient
// that occurs exactly once in a row. The writer uses this emitted value in
// its duration row; the Round92 proof also receives the original raw value.
// Reject negative/nonfinite physical inputs before calling it.
double round92CanonicalEmittedCoefficient(double value);

struct Round92DurationCoefficients {
    double horizon = 0.0;  // Actual duration-row RHS after max_digits10 output.
    double pickup = 0.0;   // Same coefficient on every p_{k,i} in that row.
    double raw_pickup_time = 0.0;
    double raw_drop_time = 0.0;
    double physical_tolerance = 0.0;
    std::uint32_t evaluator_arithmetic_contract = 2;
    // [0..V][0..V]. nullopt means arc column absent; present zero is a real
    // allowed arc whose duration term was suppressed by canonical formatting.
    // Diagonal entries must be nullopt. All vehicle rows may share this data.
    std::vector<std::vector<std::optional<double>>> directed_travel;
    // Same x-column support and indices as directed_travel, before writer
    // zero/unit normalization. The original Evaluator reads these values.
    std::vector<std::vector<std::optional<double>>> raw_directed_travel;
};

struct Round92HandlingActivationPlan {
    bool valid_input = false;
    bool applicable = false;
    std::string reason;
    std::uint64_t integer_capacity = 0; // Safe upper-floor B, <=2^53.
    double activation_coefficient = 0.0; // -B in P_k-B*a_k <= 0.
    // Equality certifies the deliberately conservative common-envelope floor,
    // not the strongest floor of either original physical or canonical model.
    bool exact_integer_floor = false;
    bool quotient_enclosure_available = false; // False for no closed route.
    double lmin_lower = 0.0;
    double lmin_upper = 0.0;
    double lower_service_coefficient = 0.0;
    double physical_horizon_upper = 0.0;
    double common_horizon_upper = 0.0;
    double quotient_lower = 0.0;
    double quotient_upper = 0.0;
    int allowed_directed_arcs = 0;
    double preparation_wall_seconds = 0.0;
};

// Owned by one external-tree run; never shared between processes or solves.
// The key compares every emitted binary64 coefficient and arc-presence bit.
struct Round92HandlingActivationCache {
    static constexpr std::uint32_t kProofVersion = 2;
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
// Invalid domains return !valid_input. A valid common lower c=0 gives
// !applicable: the duration row has no uniform service bound. With no closed
// station path, F0 and the
// depot/visit links imply P=0, and the plan emits B=0. The caller MUST have
// checked that the arc support is the actual original x-column support.
// A successful plan proves P<=B*a for both raw physical and emitted canonical
// tours using the quotient's outward UPPER bound. The quotient uses one
// common lower coefficient system and a horizon covering actual Evaluator
// acceptance. No instance-specific branch is taken.
Round92HandlingActivationPlan prepareRound92HandlingActivation(
    const Round92DurationCoefficients& actual_duration_row);

struct Instance;
void round92RequireProofEnvironment();
void round92RequireLawfulDomain(const Instance& instance);
// Throws on malformed/unsafe evidence. The returned objective, rather than
// any stale expected objective, is the only admitted upper bound.
Verification round92AdmitWitness(const Instance& instance,
                                  const std::vector<RoutePlan>& routes,
                                  double lambda,
                                  std::optional<double> expected_objective = std::nullopt);

} // namespace ebrp
