#pragma once
#include "Round61Candidates.hpp"
#include "Round62Thresholds.hpp"

namespace ebrp {
struct Round61TimeRequest {
    // -1 releases a station; depot entry is ignored. Released stations remain
    // physically present and may supply/deliver bicycles under original rules.
    std::vector<int> inventory;
    bool lp = false;
    double process_cap_seconds = 120;
    std::filesystem::path directory;
    std::vector<Round62Event> threshold_events;
    bool threshold_decision = false;
    bool force_native = false; // explicit cost comparison after a cheap proof
};
struct Round61TimeResult {
    std::string classification = "unknown";
    int status = 0;
    bool lower_available = false, upper_verified = false;
    bool time_independent_infeasible = false, parameters_verified = false;
    bool threshold_stop_requested = false;
    double lower = 0, upper = 0, safe_duration_bound = 0;
    double seconds = 0, solver_seconds = 0, work = 0;
    VerifiedBrpCandidate witness;
};
double round61SafeDurationBound(const Instance&);
void writeRound61TimeModel(const Instance&,const Round61TimeRequest&);
Round61TimeResult solveRound61TimeOracle(const Instance&,double lambda,
    const Round61TimeRequest&);
// Exact little-endian inventory bits: coefficients and rhs of a no-good.
struct Round61NoGood { std::vector<std::string> names; std::vector<double> coefficients; double rhs=1; };
Round61NoGood round61InventoryNoGood(const Instance&,const std::vector<int>&);
}
