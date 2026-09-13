#pragma once
#include "Round63TimeResource.hpp"
#include "Result.hpp"

namespace ebrp {
// Static, global physical extension: every enabled row belongs to both LP
// and MIP canonical models. No callback, restart, cutoff or start policy.
bool validRound64SharedMode(const std::string& mode);
void appendRound64SharedModel(const Instance&, const std::filesystem::path&,
                             const std::string& mode);
// Called only after the original route verifier. Includes q/f/h even when
// some families are absent from the target model; no optimizer is involved.
std::map<std::string,double> round64RouteResourceValues(
    const Instance&, const std::vector<RoutePlan>&);
} // namespace ebrp
