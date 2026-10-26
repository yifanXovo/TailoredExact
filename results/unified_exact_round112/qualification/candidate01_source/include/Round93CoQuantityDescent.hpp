#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace ebrp {

// The two currently visited stations change final inventory by the SAME
// integer t. This is distinct from Round75's opposite-sign equal transfer.
struct Round93CoQuantityChoice {
    bool found = false;
    int first = 0;
    int second = 0;
    std::int64_t delta = 0; // Y_first += delta, Y_second += delta
    double objective = 0;
};

struct Round93CoQuantityPoint {
    std::uint64_t pass = 0;
    int first = 0, second = 0;
    std::int64_t delta = 0;
    int inventory_first = 0, inventory_second = 0;
    bool physical_checked = false;
    bool feasible = false;
    bool load_feasible = false, station_feasible = false, duration_feasible = false;
    bool objective_recomputed = false;
    double objective = 0, G = 0, P = 0;
    std::string rejection_reason;
};
using Round93PointObserver = std::function<void(const Round93CoQuantityPoint&)>;

// The only diagnostic entry for an external witness: validates structure and
// Evaluator's int arithmetic domain before invoking the original Evaluator.
Verification verifyRound93StartingWitness(
    const Instance&, const std::vector<RoutePlan>&, double lambda);

struct Round93CoQuantityStats {
    std::uint64_t passes = 0, station_pairs = 0, integer_points = 0;
    std::uint64_t feasible_points = 0, load_rejections = 0;
    std::uint64_t station_rejections = 0, duration_rejections = 0;
    std::uint64_t integer_domain_rejections = 0;
    std::uint64_t other_physical_rejections = 0, nonfinite_rejections = 0;
    std::uint64_t accepted = 0, deleted_stops = 0, sign_flips = 0;
    bool deadline_reached = false, exhausted = false, verification_failed = false;
    std::string rejection_reason;
};

struct Round93CoQuantityResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round93CoQuantityStats stats;
    std::vector<Round93CoQuantityChoice> accepted_choices;
};

// Full integer line for each unordered pair of visited stations. Each point
// is materialized and checked by the original Evaluator. A deadline aborts
// the scan without claiming exhaustion or accepting a partial-scan best.
Round93CoQuantityChoice bestRound93CoQuantityChange(
    const Instance&, const std::vector<RoutePlan>&, double lambda,
    Round93CoQuantityStats&, const SolveOptions* whole_run = nullptr,
    const Round93PointObserver& observer = {});

std::vector<RoutePlan> applyRound93CoQuantityChange(
    const std::vector<RoutePlan>&, const Round93CoQuantityChoice&);

// Isolated co-line descent. It does not run R73/R75/R83 closure and is not
// wired into any production algorithm preset.
Round93CoQuantityResult runRound93CoQuantityDescent(
    const Instance&, const SolveOptions&, const std::vector<RoutePlan>&,
    const Round93PointObserver& observer = {});

} // namespace ebrp
