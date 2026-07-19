#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <string>

namespace ebrp {

struct GurobiRuntimeProbe {
    bool build_enabled = false;
    bool runtime_library_found = false;
    bool required_symbols_found = false;
    bool license_available = false;
    std::string installation_root;
    std::string library_path;
    std::string header_version;
    std::string runtime_version;
    int license_return_code = -1;
    std::string failure_reason;
};

bool gurobiBackendBuildEnabled();
GurobiRuntimeProbe probeGurobiRuntime(const SolveOptions& options);
SolveResult solveGurobiBaseline(const Instance& instance,
                                const SolveOptions& options);

} // namespace ebrp
