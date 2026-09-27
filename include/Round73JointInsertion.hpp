#pragma once

#include "Instance.hpp"
#include "Result.hpp"
#include <cstdint>
#include <filesystem>
#include <vector>

namespace ebrp {

struct Round73InsertionChoice {
    bool found = false;
    int vehicle = -1;
    int pickup = 0; // zero denotes a single drop
    int drop = 0;   // zero denotes a single pickup
    int quantity = 0;
    int pickup_leg = -1;
    int drop_leg = -1;
    double travel_delta = 0;
    double added_duration = 0;
    double objective = 0;
    double gain = 0;
};

struct Round73InsertionStats {
    std::uint64_t placements = 0;
    std::uint64_t quantity_evaluations = 0;
    int passes = 0;
    int accepted = 0;
    int pairs = 0;
    int single_pickups = 0;
    int single_drops = 0;
    bool deadline_reached = false;
    bool exhausted = false;
};

struct Round73InsertionResult {
    std::vector<RoutePlan> routes;
    Verification verification;
    Round73InsertionStats stats;
};

// Scope: new/unvisited stations only, unchanged operations at existing visits.
// Used separately by exhaustive structural tests; no solver or old witness read.
Round73InsertionChoice bestRound73Insertion(
    const Instance& instance, const std::vector<RoutePlan>& routes, double lambda,
    Round73InsertionStats& stats, const SolveOptions* deadline = nullptr);
std::vector<RoutePlan> applyRound73Insertion(
    const std::vector<RoutePlan>& routes, const Round73InsertionChoice& choice);
Round73InsertionResult runRound73JointInsertion(
    const Instance& instance, const SolveOptions& options,
    const std::filesystem::path& trace_path = {});

} // namespace ebrp
