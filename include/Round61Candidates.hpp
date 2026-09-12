#pragma once

#include "Round60Candidates.hpp"
#include "HgaTgbcRunner.hpp"
#include <chrono>
#include <filesystem>

namespace ebrp {

struct Round61CandidateSession {
    std::string mode = "off";
    VerifiedBrpCandidate archive;
    bool construction_attempted = false;
    bool evidence_persisted = true;
    std::string failure_reason;
    std::string source_snapshot_sha256;
    double construction_seconds = 0;
};

std::shared_ptr<Round61CandidateSession> prepareRound61Candidate(
    const Instance&, const SolveOptions&, const std::filesystem::path&);
std::vector<RoutePlan> normalizeRound61Routes(const Instance&, double lambda,
    const std::vector<RoutePlan>&);

// Exact O(n) evaluation for any one/two changed inventories (0 = no station).
ObjectiveParts round61Increment(const Instance&, const std::vector<int>&,
    const ObjectiveParts&, double lambda, int a, int da, int b, int db);

struct Round61BlockOptions {
    int maximum_rounds = 32;
    int pairs_per_round = 24;
    int singles_per_round = 8;
    int quantities_per_round = 2048;
    double safety_seconds = 20.0;
};

struct Round61CandidateTrace {
    int round = 0;
    long long evaluations = 0;
    double seconds = 0;
    double F = 0, G = 0, P = 0;
    int stations = 0, pickup = 0, drop = 0, blocks = 0;
    double maximum_duration = 0;
};

struct Round61BlockResult {
    VerifiedBrpCandidate candidate;
    std::vector<Round61CandidateTrace> trajectory;
    std::string stop_reason;
    long long cheap_pairs = 0, evaluated_pairs = 0, quantity_evaluations = 0;
    int completed_blocks = 0, accepted_singles = 0;
    double seconds = 0, scan_seconds = 0, evaluation_seconds = 0;
    double accept_seconds = 0, verification_seconds = 0;
};

Round61BlockResult constructRound61Block(const Instance&, double lambda,
    const Round61BlockOptions& = {});

// Revision 1: fixed route orders, simultaneous inventory/operation repair.
// Zero services are removed, every other station retains one service.
Round61BlockResult repairRound61Block(const Instance&, double lambda,
    const VerifiedBrpCandidate&, const Round61BlockOptions& = {});

HgaTgbcResult constructRound61Prefix(const Instance&, double lambda,
    const SolveOptions* process = nullptr, bool observer = true,
    const std::filesystem::path& directory = {});

void writeRound61Witness(const std::filesystem::path&, const Instance&,
    double lambda, const VerifiedBrpCandidate&);

} // namespace ebrp
