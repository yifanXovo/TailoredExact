#pragma once

#include "Instance.hpp"

#include <string>

namespace ebrp {

// Process-wide Round 29 clock helpers. The time point is injected by main at
// process entry and copied unchanged through every SolveOptions derivative.
double processElapsedSeconds(const SolveOptions& options);
double processDeadlineRemainingSeconds(const SolveOptions& options);
double processWorkRemainingSeconds(const SolveOptions& options);
bool processDeadlineConfigured(const SolveOptions& options);
bool processWorkDeadlineReached(const SolveOptions& options);

// Append one independently flushed CSV record. Missing records are never
// inferred after a crash or external watchdog termination.
void recordProcessPhase(const SolveOptions& options,
                        const std::string& event,
                        const std::string& status = "complete",
                        const std::string& detail = "");

} // namespace ebrp
