#include "GurobiBaseline.hpp"
#include "FixedIntervalMipBackend.hpp"

#include <memory>

namespace ebrp {
namespace {

class UnavailableGurobiFixedIntervalBackend final
    : public FixedIntervalMipBackend {
public:
    FixedIntervalMipCapabilities capabilities() const override {
        FixedIntervalMipCapabilities out;
        out.backend = "gurobi";
        out.failure_reason = "gurobi_backend_not_enabled_at_build_time";
        return out;
    }
    FixedIntervalMipOutcome solve(const FixedIntervalMipRequest&) override {
        FixedIntervalMipOutcome out;
        out.attempted = true;
        out.failure_reason = "gurobi_backend_not_enabled_at_build_time";
        return out;
    }
    FixedIntervalMipBackendStats stats() const override { return {}; }
};

} // namespace

bool gurobiBackendBuildEnabled() {
    return false;
}

GurobiRuntimeProbe probeGurobiRuntime(const SolveOptions&) {
    GurobiRuntimeProbe probe;
    probe.failure_reason =
        "gurobi_backend_not_compiled_enable_EXACT_EBRP_ENABLE_GUROBI";
    return probe;
}

SolveResult solveGurobiBaseline(const Instance& instance,
                                const SolveOptions& options) {
    SolveResult result;
    result.instance_name = instance.name;
    result.input_path = instance.path;
    result.method = "gurobi";
    result.status = "backend_unavailable";
    result.certificate = "not_certified";
    result.time_budget_seconds = options.solve_time_limit;
    result.gurobi_build_enabled = false;
    result.gurobi_failure_reason =
        "gurobi_backend_not_compiled_enable_EXACT_EBRP_ENABLE_GUROBI";
    result.strict_certificate_policy_version =
        "round24-gurobi-engineering-exact-v1";
    result.strict_certificate_class = "certificate_rejected";
    result.strict_certificate_rejection_reason =
        result.gurobi_failure_reason;
    result.strict_certified_original_problem = false;
    return result;
}

std::unique_ptr<FixedIntervalMipBackend> makeGurobiFixedIntervalBackend(
    const Instance&, const SolveOptions&) {
    return std::make_unique<UnavailableGurobiFixedIntervalBackend>();
}

} // namespace ebrp
