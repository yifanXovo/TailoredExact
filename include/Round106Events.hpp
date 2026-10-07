#pragma once
#include "Round105Decomposition.hpp"
#include <array>
#include <cstdint>
#include <functional>

namespace ebrp {
struct Round106Travel {
    std::vector<std::vector<std::int64_t>> milliseconds;
};
struct Round106OrderProof {
    std::array<int,3> order{};
    std::array<long long,3> loads{};
    bool prefix_feasible = false;
    double travel_lower = 0;
    double duration_lower = 0;
};
struct Round106Certificate {
    std::string family; // A_MST | B_EXACT | B_THRESHOLD
    Round105Conflict row;
    int vehicle = 0;
    std::vector<int> support;
    std::vector<int> operations;
    long long pickup = 0, delivery = 0;
    double travel_lower = 0, handling_lower = 0, budget_margin = 0;
    std::vector<std::pair<int,int>> mst_edges;
    std::vector<Round106OrderProof> orders;
};
Round106Travel round106ConservativeTravel(const Instance&);
double round106Mst(const Round106Travel&, const std::vector<int>&,
                   std::vector<std::pair<int,int>>* edges = nullptr);
std::vector<Round106Certificate> round106Separate(
    const Instance&, const Round105Pattern&, const Round106Travel&,
    const std::function<bool()>& expired = {});
void round106WriteCertificate(const std::filesystem::path&,
                             const Round106Certificate&);
SolveResult solveRound106Events(const Instance&, const SolveOptions&,
                               const SolveResult& verified_seed);
} // namespace ebrp
