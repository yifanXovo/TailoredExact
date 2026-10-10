#pragma once

#include "Instance.hpp"
#include "Result.hpp"

#include <string>

namespace ebrp {

struct TailoredBCCapability {
    bool concert_headers_found = false;
    bool cplex_c_api_headers_found = false;
    bool msvc_toolchain_available = false;
    bool command_file_runner = true;
    bool callbacks_available = false;
    std::string fail_reason;
};

TailoredBCCapability inspectTailoredBCCapability();

void populateTailoredBCResultFields(const SolveOptions& options,
                                    SolveResult& result);

std::string tailoredBCSourceClass(const SolveResult& result);

} // namespace ebrp
