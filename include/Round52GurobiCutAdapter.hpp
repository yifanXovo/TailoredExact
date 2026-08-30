#pragma once

#include "Round52TailoredCuts.hpp"

#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

namespace ebrp {

using Round52GurobiCbCutSubmitter = std::function<int(
    int, const int*, const double*, char, double)>;

struct Round52GurobiCutAdapterTelemetry {
    long long submissions = 0;
    long long successes = 0;
    long long failures = 0;
    long long mapping_failures = 0;
    long long local_scope_rejections = 0;
    long long exception_fallbacks = 0;
    int last_return_code = 0;
    std::string last_failure_reason = "none";
};

// Solver-semantic adapter with an injected GRBcbcut submitter.  It owns no
// separation mathematics and is independently unit-testable without a solver.
class Round52GurobiCutAdapter {
public:
    Round52GurobiCutAdapter(
        std::unordered_map<std::string, int> variable_indices,
        Round52GurobiCbCutSubmitter submitter);
    bool submit(const Round52CutCandidate& candidate) noexcept;
    const Round52GurobiCutAdapterTelemetry& telemetry() const {
        return telemetry_;
    }

private:
    std::unordered_map<std::string, int> variable_indices_;
    Round52GurobiCbCutSubmitter submitter_;
    Round52GurobiCutAdapterTelemetry telemetry_;
};

} // namespace ebrp
