#pragma once
#include "CanonicalCompactModel.hpp"
#include "MipStartMapping.hpp"
#include <filesystem>

namespace ebrp {
// Explicit process-local research entry. Defaults never affect production.
struct Round161Controls {
    bool active = false;
    double development_node_limit = -1;
};
inline Round161Controls& round161() { static Round161Controls c; return c; }
struct Round161Artifact {
    std::string sha256, row_signature;
    double s_lower=0, s_upper=0, t_lower=0, t_upper=0;
    bool zero_possible=false, zero_only=false;
};
// Read the actual canonical matrix, register old objective columns and delete
// their complete row-consumer closure. All other rows/columns are unchanged.
Round161Artifact replaceRound161Objective(const Instance&, const std::filesystem::path& old_lp,
    const std::filesystem::path& output, bool rn, double gamma_upper,
    bool penalty_envelope=false, double cutoff=0);
SolverNeutralModelDomain round161Domain(const std::filesystem::path&);
double round161StartResidual(const std::filesystem::path&, const std::vector<double>&);
}
