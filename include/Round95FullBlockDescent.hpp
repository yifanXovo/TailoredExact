#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace ebrp {

struct Round95Band {
    bool present = false;
    std::int64_t low = 0, high = 0;
    std::uint64_t prefixes = 0;
};

struct Round95PairDomain {
    std::uint64_t pass = 0;
    int first = 0, second = 0;
    int old_first = 0, old_second = 0;
    int capacity_first = 0, capacity_second = 0;
    std::uint64_t rectangle_points = 0;
    Round95Band band10, band01, band11;
};

struct Round95InventoryInterval {
    std::uint64_t pass = 0;
    int first = 0, second = 0;
    int inventory_first = 0;
    int low_second = 0, high_second = -1; // empty if low > high
    std::uint64_t surviving_points = 0; // excludes unchanged pair
};

struct Round95Point {
    std::uint64_t pass = 0;
    int first = 0, second = 0;
    int inventory_first = 0, inventory_second = 0;
    bool physical_checked = false, feasible = false;
    bool load_feasible = false, station_feasible = false, duration_feasible = false;
    bool objective_recomputed = false;
    double objective = 0, G = 0, P = 0;
    std::string rejection_reason;
};

struct Round95Observer {
    std::function<void(const Round95PairDomain&)> pair;
    std::function<void(const Round95InventoryInterval&)> interval;
    std::function<void(const Round95Point&)> point;
};

struct Round95Choice {
    bool found = false;
    int first = 0, second = 0;
    int inventory_first = 0, inventory_second = 0;
    double objective = 0;
};

struct Round95Stats {
    std::uint64_t passes = 0, station_pairs = 0, rectangle_points = 0;
    std::uint64_t load_pruned = 0, candidate_points = 0;
    std::uint64_t evaluator_points = 0, feasible_points = 0;
    std::uint64_t duration_rejections = 0, station_rejections = 0;
    std::uint64_t integer_domain_rejections = 0, other_physical_rejections = 0;
    std::uint64_t nonfinite_rejections = 0, accepted = 0, deleted_stops = 0;
    std::uint64_t sign_flips = 0;
    bool deadline_reached = false, exhausted = false, verification_failed = false;
    std::string rejection_reason;
};

struct Round95Result {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round95Stats stats;
    std::vector<Round95Choice> accepted_choices;
};

// The sole entry for externally supplied starting witnesses. Validates route
// structure and Evaluator's int arithmetic domain before calling Evaluator.
Verification verifyRound95StartingWitness(
    const Instance&, const std::vector<RoutePlan>&, double lambda);

// Exact complete capacity-rectangle scan for every pair of served stations.
// The prefix bands omit only load-infeasible points; every remaining point is
// evaluated by the unchanged original Evaluator. An interrupted scan returns
// no choice, so no partial best can be committed or called exhausted.
Round95Choice bestRound95FullBlockChange(
    const Instance&, const std::vector<RoutePlan>&, double lambda,
    Round95Stats&, const SolveOptions* whole_run = nullptr,
    const Round95Observer& observer = {});

std::vector<RoutePlan> applyRound95FullBlockChange(
    const Instance&, const std::vector<RoutePlan>&, const Round95Choice&);

// Isolated diagnostic descent: no R73/R75/R83, HGA, or production preset.
Round95Result runRound95FullBlockDescent(
    const Instance&, const SolveOptions&, const std::vector<RoutePlan>&,
    const Round95Observer& observer = {});

} // namespace ebrp
