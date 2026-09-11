#include "Round52GurobiCutAdapter.hpp"

#include <stdexcept>
#include <utility>

namespace ebrp {

Round52GurobiCutAdapter::Round52GurobiCutAdapter(
    std::unordered_map<std::string, int> variable_indices,
    Round52GurobiCbCutSubmitter submitter)
    : variable_indices_(std::move(variable_indices)),
      submitter_(std::move(submitter)) {}

bool Round52GurobiCutAdapter::submit(
    const Round52CutCandidate& candidate) noexcept {
    ++telemetry_.submissions;
    try {
        if (candidate.validity_scope != Round52CutValidityScope::Global) {
            ++telemetry_.failures;
            ++telemetry_.local_scope_rejections;
            telemetry_.last_failure_reason = "local_cut_not_globally_valid";
            return false;
        }
        if (!submitter_ || candidate.coefficients.empty() ||
            candidate.sense == Round52CutSense::Equal) {
            ++telemetry_.failures;
            telemetry_.last_failure_reason = "invalid_submission_request";
            return false;
        }
        std::vector<int> indices;
        std::vector<double> values;
        indices.reserve(candidate.coefficients.size());
        values.reserve(candidate.coefficients.size());
        for (const auto& coefficient : candidate.coefficients) {
            const auto found = variable_indices_.find(coefficient.variable);
            if (found == variable_indices_.end()) {
                ++telemetry_.failures;
                ++telemetry_.mapping_failures;
                telemetry_.last_failure_reason =
                    "cut_variable_mapping_missing:" + coefficient.variable;
                return false;
            }
            indices.push_back(found->second);
            values.push_back(coefficient.value);
        }
        const char sense = candidate.sense == Round52CutSense::LessEqual
            ? '<' : '>';
        const int rc = submitter_(static_cast<int>(indices.size()),
                                  indices.data(), values.data(), sense,
                                  candidate.rhs);
        telemetry_.last_return_code = rc;
        if (rc != 0) {
            ++telemetry_.failures;
            telemetry_.last_failure_reason =
                "GRBcbcut_return_code:" + std::to_string(rc);
            return false;
        }
        ++telemetry_.successes;
        telemetry_.last_failure_reason = "none";
        return true;
    } catch (const std::exception& error) {
        ++telemetry_.failures;
        ++telemetry_.exception_fallbacks;
        telemetry_.last_failure_reason =
            std::string("callback_exception:") + error.what();
        return false;
    } catch (...) {
        ++telemetry_.failures;
        ++telemetry_.exception_fallbacks;
        telemetry_.last_failure_reason = "callback_unknown_exception";
        return false;
    }
}

} // namespace ebrp
