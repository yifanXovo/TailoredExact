#pragma once
#include "Round106Events.hpp"

namespace ebrp {
// Paid offline qualifications/diagnosis only; production never calls these.
SolveResult round106Replay(const Instance&, const SolveOptions&,
    const std::filesystem::path& master, const std::filesystem::path& candidate,
    const std::filesystem::path& legal_start);
void round106AdapterContracts(const Instance&, const SolveOptions&,
    const std::filesystem::path& retained_master,
    const std::filesystem::path& inf_candidate,
    const std::filesystem::path& feas_candidate,
    const std::filesystem::path& legal_start);
std::string round106FixedFleet(const Instance&, const SolveOptions&,
    const std::vector<int>& inventory);
}
