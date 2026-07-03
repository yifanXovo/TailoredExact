#include "TailoredBCCallbacks.hpp"

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
    cap.callbacks_available = false;
    std::ostringstream why;
    why << "callback_unavailable: current ExactEBRP CPLEX integration writes LP files "
        << "and invokes cplex.exe command files; the executable is built with the "
        << "repository MinGW/g++ path and is not linked against the CPLEX Concert/C API. "
        << "headers_found=" << (cap.concert_headers_found ? "true" : "false")
        << ", c_api_headers_found=" << (cap.cplex_c_api_headers_found ? "true" : "false")
        << ", msvc_env_available=" << (cap.msvc_toolchain_available ? "true" : "false")
        << ". Rows using paper-gf-tailored-bc are therefore labelled static_fallback "
        << "unless a future MSVC/CPLEX-linked callback target is added.";
    cap.fail_reason = why.str();
    return cap;
}

} // namespace ebrp
