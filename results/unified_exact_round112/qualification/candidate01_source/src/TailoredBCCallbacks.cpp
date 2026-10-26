#include "TailoredBCCallbacks.hpp"

#include "TailoredBCCplexApi.hpp"

#include <cstdlib>
#include <filesystem>
#include <sstream>

namespace ebrp {

namespace {

bool fileExists(const char* path) {
    return path != nullptr && std::filesystem::exists(path);
}

} // namespace

TailoredBCCapability inspectTailoredBCCallbacks() {
    TailoredBCCapability cap;
    const char* concert_header =
        "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/include/ilcplex/ilocplex.h";
    const char* c_api_header =
        "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/include/ilcplex/cplex.h";
    cap.concert_headers_found = fileExists(concert_header);
    cap.cplex_c_api_headers_found = fileExists(c_api_header);

    const char* visual_studio = std::getenv("VSCMD_VER");
    const char* msvc_tools = std::getenv("VCToolsInstallDir");
    cap.msvc_toolchain_available =
        (visual_studio != nullptr && *visual_studio != '\0') ||
        (msvc_tools != nullptr && *msvc_tools != '\0');

    cap.command_file_runner = true;
    TailoredBCCplexApiProbe api_probe = probeTailoredBCCplexApi();
    cap.callbacks_available = api_probe.callbacks_available;
    if (cap.callbacks_available) {
        cap.fail_reason =
            "none: cplex2211.dll loaded dynamically and generic callback symbols are available";
        return cap;
    }
    std::ostringstream why;
    why << "callback_unavailable: current ExactEBRP can still invoke command-file CPLEX, "
        << "but the dynamic CPLEX callback API probe failed. "
        << "headers_found=" << (cap.concert_headers_found ? "true" : "false")
        << ", c_api_headers_found=" << (cap.cplex_c_api_headers_found ? "true" : "false")
        << ", msvc_env_available=" << (cap.msvc_toolchain_available ? "true" : "false")
        << ", dll_path=" << api_probe.dll_path
        << ", dll_found=" << (api_probe.dll_found ? "true" : "false")
        << ", symbols_found=" << (api_probe.required_symbols_found ? "true" : "false")
        << ", probe_reason=" << api_probe.fail_reason
        << ". Rows using paper-gf-tailored-bc are labelled static_fallback only if "
        << "this probe remains unavailable.";
    cap.fail_reason = why.str();
    return cap;
}

} // namespace ebrp
