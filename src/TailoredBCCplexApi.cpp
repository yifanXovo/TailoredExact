#include "TailoredBCCplexApi.hpp"
#include "ControllingLeafScheduler.hpp"
#include "GiniFrontierGeometry.hpp"
#include "IntervalRowFactory.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

namespace ebrp {
namespace {

std::string fnvFingerprint(const std::string& text) {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char ch : text) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= 1099511628211ull;
    }
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << hash;
    return out.str();
}

std::string fileFingerprint(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return "unavailable";
    std::ostringstream bytes;
    bytes << input.rdbuf();
    return fnvFingerprint(bytes.str());
}

std::string originalObjectiveFingerprint(const Instance& instance,
                                         const SolveOptions& options) {
    std::ostringstream canonical;
    canonical << std::setprecision(17) << "min|G=1";
    for (int station = 1; station <= instance.V; ++station) {
        canonical << "|e_" << station << '='
                  << options.lambda * instance.weights[station];
    }
    return fnvFingerprint(canonical.str());
}

#ifdef _WIN32
using CPXINT = int;
using CPXLONG = long long;
struct cpxenv;
struct cpxlp;
struct cpxcallbackcontext;
using CPXENVptr = cpxenv*;
using CPXCENVptr = const cpxenv*;
using CPXLPptr = cpxlp*;
using CPXCLPptr = const cpxlp*;
using CPXCALLBACKCONTEXTptr = cpxcallbackcontext*;
using CPXCALLBACKINFO = int;
using CPXCALLBACKFUNC = int (__stdcall *)(CPXCALLBACKCONTEXTptr, CPXLONG, void*);

constexpr CPXLONG kContextCandidate = 0x0020;
constexpr CPXLONG kContextRelaxation = 0x0040;
constexpr CPXLONG kContextBranching = 0x0080;
constexpr CPXLONG kContextGlobalProgress = 0x0010;
constexpr CPXLONG kContextLocalProgress = 0x0008;
constexpr int kParamThreads = 1067;
constexpr int kParamTimeLimit = 1039;
constexpr int kParamMipGap = 2009;
constexpr int kParamAbsoluteMipGap = 2008;
constexpr int kParamScreenOutput = 1035;
constexpr int kParamMipDisplay = 2012;
constexpr int kParamPreprocessingPresolve = 1030;
constexpr int kParamMipStrategyHeuristicFreq = 2031;
constexpr int kParamMipStrategySearch = 2109;
constexpr int kParamMipStrategyNodeSelect = 2018;
constexpr int kParamMipStrategyProbe = 2042;
constexpr int kMipSearchTraditional = 1;
constexpr int kMipSearchDynamic = 2;
constexpr int kNodeSelectBestBound = 1;
constexpr int kLpStatusOptimal = 1;
constexpr int kLpStatusOptimalInfeasible = 5;
constexpr int kUseCutForce = 0;
constexpr CPXCALLBACKINFO kCallbackInfoNodeCount = 1;
constexpr CPXCALLBACKINFO kCallbackInfoIterationCount = 2;
constexpr CPXCALLBACKINFO kCallbackInfoBestSol = 3;
constexpr CPXCALLBACKINFO kCallbackInfoBestBnd = 4;
constexpr CPXCALLBACKINFO kCallbackInfoDeterministicTime = 8;
constexpr CPXCALLBACKINFO kCallbackInfoNodeUid = 9;
constexpr CPXCALLBACKINFO kCallbackInfoNodeDepth = 10;
constexpr CPXCALLBACKINFO kCallbackInfoNodesLeft = 14;

using CPXopenCPLEX_t = CPXENVptr (__stdcall *)(int*);
using CPXcloseCPLEX_t = int (__stdcall *)(CPXENVptr*);
using CPXcreateprob_t = CPXLPptr (__stdcall *)(CPXCENVptr, int*, const char*);
using CPXfreeprob_t = int (__stdcall *)(CPXCENVptr, CPXLPptr*);
using CPXreadcopyprob_t = int (__stdcall *)(CPXCENVptr, CPXLPptr, const char*, const char*);
using CPXsetintparam_t = int (__stdcall *)(CPXENVptr, int, CPXINT);
using CPXsetdblparam_t = int (__stdcall *)(CPXENVptr, int, double);
using CPXgetintparam_t = int (__stdcall *)(CPXCENVptr, int, CPXINT*);
using CPXgetdblparam_t = int (__stdcall *)(CPXCENVptr, int, double*);
using CPXsetlogfilename_t = int (__stdcall *)(CPXENVptr, const char*, const char*);
using CPXcallbacksetfunc_t = int (__stdcall *)(CPXENVptr, CPXLPptr, CPXLONG, CPXCALLBACKFUNC, void*);
using CPXmipopt_t = int (__stdcall *)(CPXCENVptr, CPXLPptr);
using CPXgetstat_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetstatstring_t = char* (__stdcall *)(CPXCENVptr, int, char*);
using CPXgetobjval_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*);
using CPXgetbestobjval_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*);
using CPXgetmiprelgap_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*);
using CPXgetnodecnt_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnodeleftcnt_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetmipitcnt_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetsolnpoolnumsolns_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnumcuts_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, int, int*);
using CPXaddmipstarts_t = int (__stdcall *)(CPXCENVptr, CPXLPptr, int, int,
    const int*, const int*, const double*, const int*, char**);
using CPXgetnummipstarts_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnumcols_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnumrows_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnumnz_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetx_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*, int, int);
using CPXgetcolname_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, char**, char*, int, int*, int, int);
using CPXgetlb_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*, int, int);
using CPXgetub_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*, int, int);
using CPXgetctype_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, char*, int, int);
using CPXcallbackaddusercuts_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, int, const double*, const char*, const int*, const int*, const double*, const int*, const int*);
using CPXcallbackcandidateispoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int*);
using CPXcallbackgetcandidatepoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int, double*);
using CPXcallbackgetrelaxationpoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int, double*);
using CPXcallbackgetrelaxationstatus_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int*, CPXLONG);
using CPXcallbackgetinfodbl_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, CPXCALLBACKINFO, double*);
using CPXcallbackgetinfolong_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, CPXCALLBACKINFO, CPXLONG*);
using CPXcallbackgetlocallb_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int);
using CPXcallbackgetlocalub_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int);
using CPXcallbackrejectcandidate_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, int, const double*, const char*, const int*, const int*, const double*);
using CPXcallbackmakebranch_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, const int*, const char*, const double*, int, int, const double*, const char*, const int*, const int*, const double*, double, int*);
using CPXcallbackabort_t = void (__stdcall *)(CPXCALLBACKCONTEXTptr);
using CPXcopyorder_t = int (__stdcall *)(CPXCENVptr, CPXLPptr, int, const int*, const int*, const int*);
using CPXsetterminate_t = int (__stdcall *)(CPXENVptr, volatile int*);

struct Api {
    HMODULE dll = nullptr;
    CPXopenCPLEX_t open = nullptr;
    CPXcloseCPLEX_t close = nullptr;
    CPXcreateprob_t createprob = nullptr;
    CPXfreeprob_t freeprob = nullptr;
    CPXreadcopyprob_t readcopyprob = nullptr;
    CPXsetintparam_t setintparam = nullptr;
    CPXsetdblparam_t setdblparam = nullptr;
    CPXgetintparam_t getintparam = nullptr;
    CPXgetdblparam_t getdblparam = nullptr;
    CPXsetlogfilename_t setlogfilename = nullptr;
    CPXcallbacksetfunc_t callbacksetfunc = nullptr;
    CPXmipopt_t mipopt = nullptr;
    CPXgetstat_t getstat = nullptr;
    CPXgetstatstring_t getstatstring = nullptr;
    CPXgetobjval_t getobjval = nullptr;
    CPXgetbestobjval_t getbestobjval = nullptr;
    CPXgetmiprelgap_t getmiprelgap = nullptr;
    CPXgetnodecnt_t getnodecnt = nullptr;
    CPXgetnodeleftcnt_t getnodeleftcnt = nullptr;
    CPXgetmipitcnt_t getmipitcnt = nullptr;
    CPXgetsolnpoolnumsolns_t getsolnpoolnumsolns = nullptr;
    CPXgetnumcuts_t getnumcuts = nullptr;
    CPXaddmipstarts_t addmipstarts = nullptr;
    CPXgetnummipstarts_t getnummipstarts = nullptr;
    CPXgetnumcols_t getnumcols = nullptr;
    CPXgetnumrows_t getnumrows = nullptr;
    CPXgetnumnz_t getnumnz = nullptr;
    CPXgetx_t getx = nullptr;
    CPXgetcolname_t getcolname = nullptr;
    CPXgetlb_t getlb = nullptr;
    CPXgetub_t getub = nullptr;
    CPXgetctype_t getctype = nullptr;
    CPXcallbackaddusercuts_t callbackaddusercuts = nullptr;
    CPXcallbackcandidateispoint_t callbackcandidateispoint = nullptr;
    CPXcallbackgetcandidatepoint_t callbackgetcandidatepoint = nullptr;
    CPXcallbackgetrelaxationpoint_t callbackgetrelaxationpoint = nullptr;
    CPXcallbackgetrelaxationstatus_t callbackgetrelaxationstatus = nullptr;
    CPXcallbackgetinfodbl_t callbackgetinfodbl = nullptr;
    CPXcallbackgetinfolong_t callbackgetinfolong = nullptr;
    CPXcallbackgetlocallb_t callbackgetlocallb = nullptr;
    CPXcallbackgetlocalub_t callbackgetlocalub = nullptr;
    CPXcallbackrejectcandidate_t callbackrejectcandidate = nullptr;
    CPXcallbackmakebranch_t callbackmakebranch = nullptr;
    CPXcallbackabort_t callbackabort = nullptr;
    CPXcopyorder_t copyorder = nullptr;
    CPXsetterminate_t setterminate = nullptr;
};

std::filesystem::path defaultCplexDllPath() {
    if (const char* bin = std::getenv("CPLEX_STUDIO_BINARIES2211")) {
        std::filesystem::path p = std::filesystem::path(bin) / "cplex2211.dll";
        if (std::filesystem::exists(p)) return p;
    }
    std::filesystem::path hard =
        "C:/Program Files/IBM/ILOG/CPLEX_Studio2211/cplex/bin/x64_win64/cplex2211.dll";
    if (std::filesystem::exists(hard)) return hard;
    return "cplex2211.dll";
}

template <typename Fn>
bool loadSymbol(Api& api, Fn& target, const char* name) {
    FARPROC proc = GetProcAddress(api.dll, name);
    if (!proc) return false;
    target = reinterpret_cast<Fn>(proc);
    return true;
}

bool loadApi(Api& api, std::string& fail_reason) {
    const std::filesystem::path dll_path = defaultCplexDllPath();
    api.dll = LoadLibraryW(dll_path.wstring().c_str());
    if (!api.dll) {
        fail_reason = "could_not_load_cplex2211_dll:" + dll_path.string();
        return false;
    }
    struct Required {
        const char* name;
        bool ok;
    };
    std::vector<Required> checks;
#define LOAD_REQ(member, symbol) do { \
        bool ok = loadSymbol(api, api.member, symbol); \
        checks.push_back({symbol, ok}); \
    } while (false)
    LOAD_REQ(open, "CPXopenCPLEX");
    LOAD_REQ(close, "CPXcloseCPLEX");
    LOAD_REQ(createprob, "CPXcreateprob");
    LOAD_REQ(freeprob, "CPXfreeprob");
    LOAD_REQ(readcopyprob, "CPXreadcopyprob");
    LOAD_REQ(setintparam, "CPXsetintparam");
    LOAD_REQ(setdblparam, "CPXsetdblparam");
    LOAD_REQ(getintparam, "CPXgetintparam");
    LOAD_REQ(getdblparam, "CPXgetdblparam");
    LOAD_REQ(setlogfilename, "CPXsetlogfilename");
    LOAD_REQ(callbacksetfunc, "CPXcallbacksetfunc");
    LOAD_REQ(mipopt, "CPXmipopt");
    LOAD_REQ(getstat, "CPXgetstat");
    LOAD_REQ(getstatstring, "CPXgetstatstring");
    LOAD_REQ(getobjval, "CPXgetobjval");
    LOAD_REQ(getbestobjval, "CPXgetbestobjval");
    LOAD_REQ(getmiprelgap, "CPXgetmiprelgap");
    LOAD_REQ(getnodecnt, "CPXgetnodecnt");
    LOAD_REQ(getnodeleftcnt, "CPXgetnodeleftcnt");
    LOAD_REQ(getmipitcnt, "CPXgetmipitcnt");
    LOAD_REQ(getsolnpoolnumsolns, "CPXgetsolnpoolnumsolns");
    LOAD_REQ(getnumcuts, "CPXgetnumcuts");
    LOAD_REQ(addmipstarts, "CPXaddmipstarts");
    LOAD_REQ(getnummipstarts, "CPXgetnummipstarts");
    LOAD_REQ(getnumcols, "CPXgetnumcols");
    LOAD_REQ(getnumrows, "CPXgetnumrows");
    LOAD_REQ(getnumnz, "CPXgetnumnz");
    LOAD_REQ(getx, "CPXgetx");
    LOAD_REQ(getcolname, "CPXgetcolname");
    LOAD_REQ(getlb, "CPXgetlb");
    LOAD_REQ(getub, "CPXgetub");
    LOAD_REQ(getctype, "CPXgetctype");
    LOAD_REQ(callbackaddusercuts, "CPXcallbackaddusercuts");
    LOAD_REQ(callbackcandidateispoint, "CPXcallbackcandidateispoint");
    LOAD_REQ(callbackgetcandidatepoint, "CPXcallbackgetcandidatepoint");
    LOAD_REQ(callbackgetrelaxationpoint, "CPXcallbackgetrelaxationpoint");
    LOAD_REQ(callbackgetrelaxationstatus, "CPXcallbackgetrelaxationstatus");
    LOAD_REQ(callbackgetinfodbl, "CPXcallbackgetinfodbl");
    LOAD_REQ(callbackgetinfolong, "CPXcallbackgetinfolong");
    LOAD_REQ(callbackgetlocallb, "CPXcallbackgetlocallb");
    LOAD_REQ(callbackgetlocalub, "CPXcallbackgetlocalub");
    LOAD_REQ(callbackrejectcandidate, "CPXcallbackrejectcandidate");
    LOAD_REQ(callbackmakebranch, "CPXcallbackmakebranch");
    LOAD_REQ(callbackabort, "CPXcallbackabort");
    LOAD_REQ(copyorder, "CPXcopyorder");
    LOAD_REQ(setterminate, "CPXsetterminate");
#undef LOAD_REQ
    std::ostringstream missing;
    for (const Required& req : checks) {
        if (!req.ok) {
            if (missing.tellp() > 0) missing << ",";
            missing << req.name;
        }
    }
    if (missing.tellp() > 0) {
        fail_reason = "missing_cplex_symbols:" + missing.str();
        FreeLibrary(api.dll);
        api.dll = nullptr;
        return false;
    }
    return true;
}

std::vector<std::string> getColumnNames(Api& api, CPXENVptr env, CPXLPptr lp, int ncols) {
    std::vector<std::string> names(ncols);
    int surplus = 0;
    int status = api.getcolname(env, lp, nullptr, nullptr, 0, &surplus, 0, ncols - 1);
    int space = std::max(1, -surplus + 1);
    std::vector<char> storage(static_cast<std::size_t>(space));
    std::vector<char*> name_ptrs(static_cast<std::size_t>(ncols), nullptr);
    status = api.getcolname(env, lp, name_ptrs.data(), storage.data(), space,
                            &surplus, 0, ncols - 1);
    if (status != 0) return names;
    for (int i = 0; i < ncols; ++i) {
        if (name_ptrs[static_cast<std::size_t>(i)]) {
            names[static_cast<std::size_t>(i)] =
                name_ptrs[static_cast<std::size_t>(i)];
        }
    }
    return names;
}

std::string variableDomainFingerprint(Api& api, CPXENVptr env, CPXLPptr lp,
                                      const std::vector<std::string>& names) {
    const int ncols = static_cast<int>(names.size());
    if (ncols <= 0) return "unavailable";
    std::vector<double> lower(static_cast<std::size_t>(ncols), 0.0);
    std::vector<double> upper(static_cast<std::size_t>(ncols), 0.0);
    std::vector<char> type(static_cast<std::size_t>(ncols), 'C');
    if (api.getlb(env, lp, lower.data(), 0, ncols - 1) != 0 ||
        api.getub(env, lp, upper.data(), 0, ncols - 1) != 0 ||
        api.getctype(env, lp, type.data(), 0, ncols - 1) != 0) {
        return "unavailable";
    }
    std::ostringstream canonical;
    canonical << std::setprecision(std::numeric_limits<double>::max_digits10);
    for (int column = 0; column < ncols; ++column) {
        canonical << names[static_cast<std::size_t>(column)] << ':'
                  << type[static_cast<std::size_t>(column)] << ':'
                  << lower[static_cast<std::size_t>(column)] << ':'
                  << upper[static_cast<std::size_t>(column)] << '|';
    }
    return fnvFingerprint(canonical.str());
}

bool configureStrictMipGaps(Api& api, CPXENVptr env,
                            NativeMipEvidence& evidence) {
    evidence.relative_gap.parameter_id = kParamMipGap;
    evidence.relative_gap.requested = 0.0;
    evidence.relative_gap.setter_return_code =
        api.setdblparam(env, kParamMipGap, 0.0);
    evidence.relative_gap.getter_return_code = api.getdblparam(
        env, kParamMipGap, &evidence.relative_gap.effective);
    evidence.absolute_gap.parameter_id = kParamAbsoluteMipGap;
    evidence.absolute_gap.requested = 0.0;
    evidence.absolute_gap.setter_return_code =
        api.setdblparam(env, kParamAbsoluteMipGap, 0.0);
    evidence.absolute_gap.getter_return_code = api.getdblparam(
        env, kParamAbsoluteMipGap, &evidence.absolute_gap.effective);
    evidence.strict_gap_configuration_valid =
        evidence.relative_gap.setter_return_code == 0 &&
        evidence.relative_gap.getter_return_code == 0 &&
        evidence.relative_gap.effective == 0.0 &&
        evidence.absolute_gap.setter_return_code == 0 &&
        evidence.absolute_gap.getter_return_code == 0 &&
        evidence.absolute_gap.effective == 0.0;
    return evidence.strict_gap_configuration_valid;
}

void captureNativeMipEvidence(Api& api, CPXENVptr env, CPXLPptr lp,
                              int mipopt_return_code,
                              NativeMipEvidence& evidence) {
    evidence.mipopt_return_code = mipopt_return_code;
    evidence.solve_returned = true;
    evidence.status_code = api.getstat(env, lp);
    char status_buffer[1024] = {0};
    if (api.getstatstring(env, evidence.status_code, status_buffer)) {
        evidence.status_text = status_buffer;
    } else {
        evidence.status_text =
            "status_code_" + std::to_string(evidence.status_code);
    }
    double objective = 0.0;
    evidence.objective_return_code = api.getobjval(env, lp, &objective);
    if (evidence.objective_return_code == 0 && std::isfinite(objective) &&
        std::fabs(objective) < kCplexInfinityBound) {
        evidence.objective = objective;
        evidence.objective_available = true;
    }
    double best_bound = 0.0;
    evidence.best_bound_return_code =
        api.getbestobjval(env, lp, &best_bound);
    if (evidence.best_bound_return_code == 0 && std::isfinite(best_bound) &&
        std::fabs(best_bound) < kCplexInfinityBound) {
        evidence.best_bound = best_bound;
        evidence.best_bound_available = true;
    }
    double mip_relative_gap = 0.0;
    evidence.mip_relative_gap_return_code =
        api.getmiprelgap(env, lp, &mip_relative_gap);
    if (evidence.mip_relative_gap_return_code == 0 &&
        std::isfinite(mip_relative_gap) &&
        std::fabs(mip_relative_gap) < kCplexInfinityBound) {
        evidence.mip_relative_gap = mip_relative_gap;
        evidence.mip_relative_gap_available = true;
    }
    const bool all_getters_attempted =
        evidence.objective_return_code != -1 &&
        evidence.best_bound_return_code != -1 &&
        evidence.mip_relative_gap_return_code != -1;
    const bool incumbent_and_gap_expected =
        evidence.status_code == kCplexMipOptimal ||
        evidence.status_code == kCplexMipOptimalTolerance ||
        evidence.status_code == kCplexMipTimeLimitFeasible ||
        evidence.status_code == kCplexMipOptimalUnscaledInfeasibilities;
    evidence.evidence_capture_complete = mipopt_return_code == 0 &&
        evidence.status_code != 0 && all_getters_attempted &&
        (!incumbent_and_gap_expected ||
         (evidence.objective_available && evidence.best_bound_available &&
          evidence.mip_relative_gap_available));
}

std::string collectNativeCutCounts(Api& api, CPXENVptr env, CPXLPptr lp) {
    const std::array<const char*, 22> cut_names = {
        "cover", "gub_cover", "flow_cover", "clique", "fractional",
        "mir", "flow_path", "disjunctive", "implied_bound", "zero_half",
        "multi_commodity_flow", "local_cover", "tightening",
        "objective_disjunctive", "lift_and_project", "user", "table",
        "solution_pool", "local_implied_bound", "bqp", "rlt", "benders"
    };
    std::ostringstream cuts;
    for (int type = 0; type < static_cast<int>(cut_names.size()); ++type) {
        int count = 0;
        if (api.getnumcuts(env, lp, type, &count) != 0) continue;
        if (cuts.tellp() > 0) cuts << '|';
        cuts << cut_names[static_cast<std::size_t>(type)] << '=' << count;
    }
    return cuts.str();
}

struct NativeMipStartMapping {
    bool complete = false;
    std::vector<double> values;
    std::string failure_reason;
};

bool parseIndexedName(const std::string& name,
                      const std::string& prefix,
                      int expected,
                      std::vector<int>& indices) {
    if (name.rfind(prefix, 0) != 0) return false;
    indices.clear();
    std::string rest = name.substr(prefix.size());
    std::size_t start = 0;
    while (start <= rest.size()) {
        const std::size_t end = rest.find('_', start);
        const std::string token = rest.substr(
            start, end == std::string::npos ? std::string::npos : end - start);
        if (token.empty() ||
            !std::all_of(token.begin(), token.end(), [](unsigned char ch) {
                return std::isdigit(ch) != 0;
            })) {
            return false;
        }
        indices.push_back(std::stoi(token));
        if (end == std::string::npos) break;
        start = end + 1;
    }
    return static_cast<int>(indices.size()) == expected;
}

NativeMipStartMapping buildVerifiedNativeMipStart(
    Api& api,
    CPXENVptr env,
    CPXLPptr lp,
    const Instance& instance,
    const SolveOptions& options,
    const std::vector<RoutePlan>& routes,
    double verified_incumbent,
    const std::vector<std::string>& names) {
    NativeMipStartMapping out;
    const int ncols = static_cast<int>(names.size());
    out.values.assign(static_cast<std::size_t>(ncols), 0.0);
    if (ncols <= 0) {
        out.failure_reason = "empty_model";
        return out;
    }
    std::unordered_map<std::string, double> route_values;
    std::vector<int> final_inventory = instance.initial;
    std::set<int> used_vehicles;
    std::set<int> used_stations;
    for (const RoutePlan& route : routes) {
        if (route.vehicle < 0 || route.vehicle >= instance.M ||
            !used_vehicles.insert(route.vehicle).second) {
            out.failure_reason = "invalid_or_duplicate_route_vehicle";
            return out;
        }
        if (route.nodes.size() < 2 || route.nodes.front() != 0 ||
            route.nodes.back() != 0) {
            out.failure_reason = "route_not_depot_closed";
            return out;
        }
        for (std::size_t pos = 1; pos < route.nodes.size(); ++pos) {
            const int from = route.nodes[pos - 1];
            const int to = route.nodes[pos];
            if (from < 0 || from > instance.V || to < 0 ||
                to > instance.V || from == to) {
                out.failure_reason = "invalid_mip_start_arc";
                return out;
            }
            route_values["x_" + std::to_string(route.vehicle) + "_" +
                std::to_string(from) + "_" + std::to_string(to)] = 1.0;
            route_values["conn_" + std::to_string(route.vehicle) + "_" +
                std::to_string(from) + "_" + std::to_string(to)] =
                static_cast<double>(route.nodes.size() - 1 - pos);
        }
        int load = 0;
        for (std::size_t pos = 1; pos + 1 < route.nodes.size(); ++pos) {
            const int station = route.nodes[pos];
            if (station <= 0 || station > instance.V ||
                !used_stations.insert(station).second) {
                out.failure_reason = "invalid_or_duplicate_mip_start_station";
                return out;
            }
            const auto operation = std::find_if(
                route.operations.begin(), route.operations.end(),
                [&](const StopOperation& item) { return item.station == station; });
            if (operation == route.operations.end() ||
                operation->pickup < 0 || operation->drop < 0 ||
                (operation->pickup > 0 && operation->drop > 0) ||
                (operation->pickup == 0 && operation->drop == 0)) {
                out.failure_reason = "invalid_mip_start_operation";
                return out;
            }
            const std::string base = std::to_string(route.vehicle) + "_" +
                std::to_string(station);
            route_values["z_" + base] = 1.0;
            route_values["mode_" + base] = operation->pickup > 0 ? 1.0 : 0.0;
            route_values["p_" + base] = operation->pickup;
            route_values["d_" + base] = operation->drop;
            route_values["ord_" + base] = static_cast<double>(pos);
            load += operation->pickup - operation->drop;
            if (load < 0 || load > instance.Q[route.vehicle]) {
                out.failure_reason = "mip_start_load_out_of_range";
                return out;
            }
            route_values["load_" + base] = load;
            final_inventory[station] +=
                operation->drop - operation->pickup;
        }
    }
    const ObjectiveParts parts = computeObjectiveParts(
        instance, final_inventory, options.lambda);
    if (!std::isfinite(parts.objective) ||
        std::fabs(parts.objective - verified_incumbent) >
            1e-7 * std::max({1.0, std::fabs(parts.objective),
                             std::fabs(verified_incumbent)})) {
        out.failure_reason = "mapped_objective_differs_from_verified_incumbent";
        return out;
    }
    std::vector<double> ratio(static_cast<std::size_t>(instance.V + 1), 0.0);
    std::vector<double> deviation(
        static_cast<std::size_t>(instance.V + 1), 0.0);
    for (int station = 1; station <= instance.V; ++station) {
        ratio[station] = static_cast<double>(final_inventory[station]) /
            instance.target[station];
        deviation[station] = std::fabs(ratio[station] - 1.0);
    }
    const double ratio_min = instance.V > 0
        ? *std::min_element(ratio.begin() + 1, ratio.end()) : 0.0;
    const double ratio_max = instance.V > 0
        ? *std::max_element(ratio.begin() + 1, ratio.end()) : 0.0;
    std::vector<int> indices;
    auto routeFamily = [&](const std::string& name) {
        return parseIndexedName(name, "x_", 3, indices) ||
            parseIndexedName(name, "z_", 2, indices) ||
            parseIndexedName(name, "mode_", 2, indices) ||
            parseIndexedName(name, "p_", 2, indices) ||
            parseIndexedName(name, "d_", 2, indices) ||
            parseIndexedName(name, "load_", 2, indices) ||
            parseIndexedName(name, "ord_", 2, indices) ||
            parseIndexedName(name, "conn_", 3, indices);
    };
    for (int column = 0; column < ncols; ++column) {
        const std::string& name = names[static_cast<std::size_t>(column)];
        double value = 0.0;
        const auto direct = route_values.find(name);
        if (direct != route_values.end()) {
            value = direct->second;
        } else if (routeFamily(name)) {
            value = 0.0;
        } else if (name == "G") {
            value = parts.G;
        } else if (name == "r_min") {
            value = ratio_min;
        } else if (name == "r_max") {
            value = ratio_max;
        } else if (name == "W_SP") {
            value = parts.S * parts.P;
        } else if (parseIndexedName(name, "Y_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = final_inventory[indices[0]];
        } else if (parseIndexedName(name, "r_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = ratio[indices[0]];
        } else if (parseIndexedName(name, "e_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = deviation[indices[0]];
        } else if (parseIndexedName(name, "h_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 1 && indices[1] <= instance.V) {
            value = std::fabs(ratio[indices[0]] - ratio[indices[1]]);
        } else if (parseIndexedName(name, "bit_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 0 && indices[1] < 63) {
            value = (final_inventory[indices[0]] >> indices[1]) & 1;
        } else if (parseIndexedName(name, "prod_", 2, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V &&
                   indices[1] >= 0 && indices[1] < 63) {
            value = parts.G *
                ((final_inventory[indices[0]] >> indices[1]) & 1);
        } else if (parseIndexedName(name, "zprod_", 1, indices) &&
                   indices[0] >= 1 && indices[0] <= instance.V) {
            value = parts.G * final_inventory[indices[0]];
        } else {
            out.failure_reason = "unsupported_complete_mip_start_column:" + name;
            return out;
        }
        if (!std::isfinite(value)) {
            out.failure_reason = "nonfinite_mip_start_value:" + name;
            return out;
        }
        out.values[static_cast<std::size_t>(column)] = value;
    }
    std::vector<double> lower(static_cast<std::size_t>(ncols), 0.0);
    std::vector<double> upper(static_cast<std::size_t>(ncols), 0.0);
    std::vector<char> ctype(static_cast<std::size_t>(ncols), 'C');
    if (api.getlb(env, lp, lower.data(), 0, ncols - 1) != 0 ||
        api.getub(env, lp, upper.data(), 0, ncols - 1) != 0 ||
        api.getctype(env, lp, ctype.data(), 0, ncols - 1) != 0) {
        out.failure_reason = "mip_start_domain_query_failed";
        return out;
    }
    for (int column = 0; column < ncols; ++column) {
        const double value = out.values[static_cast<std::size_t>(column)];
        if (value < lower[static_cast<std::size_t>(column)] - 1e-7 ||
            value > upper[static_cast<std::size_t>(column)] + 1e-7) {
            out.failure_reason = "mip_start_bound_violation:" +
                names[static_cast<std::size_t>(column)];
            return out;
        }
        const char type = ctype[static_cast<std::size_t>(column)];
        if ((type == 'B' || type == 'I' || type == 'N') &&
            std::fabs(value - std::round(value)) > 1e-7) {
            out.failure_reason = "mip_start_integrality_violation:" +
                names[static_cast<std::size_t>(column)];
            return out;
        }
    }
    out.complete = true;
    return out;
}

bool isPriorityTarget(const std::string& name) {
    return name.rfind("bit_", 0) == 0 ||
           name.rfind("z_", 0) == 0 ||
           name.rfind("mode_", 0) == 0;
}

int priorityForName(const std::string& name) {
    if (name.rfind("bit_", 0) == 0) return 100;
    if (name.rfind("z_", 0) == 0) return 80;
    if (name.rfind("mode_", 0) == 0) return 60;
    return 1;
}

long long applyBranchPriorities(Api& api,
                                CPXENVptr env,
                                CPXLPptr lp,
                                const std::vector<std::string>& names,
                                std::string& status) {
    std::vector<int> indices;
    std::vector<int> priorities;
    std::vector<int> directions;
    for (int i = 0; i < static_cast<int>(names.size()); ++i) {
        if (!isPriorityTarget(names[static_cast<std::size_t>(i)])) continue;
        indices.push_back(i);
        priorities.push_back(priorityForName(names[static_cast<std::size_t>(i)]));
        directions.push_back(0);
    }
    if (indices.empty()) {
        status = "no_binary_priority_targets_found";
        return 0;
    }
    const int rc = api.copyorder(env, lp, static_cast<int>(indices.size()),
                                 indices.data(), priorities.data(), directions.data());
    if (rc != 0) {
        status = "CPXcopyorder_failed:" + std::to_string(rc);
        return 0;
    }
    status = "applied";
    return static_cast<long long>(indices.size());
}

std::string yNameForStation(int station) {
    return "Y_" + std::to_string(station);
}

std::string rNameForStation(int station) {
    return "r_" + std::to_string(station);
}

std::string eNameForStation(int station) {
    return "e_" + std::to_string(station);
}

std::string qL1NameForStation(int station) {
    return "q_l1_" + std::to_string(station);
}

std::string hNameForPair(int a, int b) {
    if (a > b) std::swap(a, b);
    return "h_" + std::to_string(a) + "_" + std::to_string(b);
}

std::string zNameForVehicleStation(int vehicle, int station) {
    return "z_" + std::to_string(vehicle) + "_" + std::to_string(station);
}

std::string xNameForVehicleArc(int vehicle, int from, int to) {
    return "x_" + std::to_string(vehicle) + "_" +
        std::to_string(from) + "_" + std::to_string(to);
}

std::string pNameForVehicleStation(int vehicle, int station) {
    return "p_" + std::to_string(vehicle) + "_" + std::to_string(station);
}

std::string dNameForVehicleStation(int vehicle, int station) {
    return "d_" + std::to_string(vehicle) + "_" + std::to_string(station);
}

std::string loadNameForVehicleStation(int vehicle, int station) {
    return "load_" + std::to_string(vehicle) + "_" + std::to_string(station);
}

std::vector<int> buildNameToIndexLookup(const std::vector<std::string>& names,
                                        const std::string& target) {
    std::vector<int> indices;
    for (int i = 0; i < static_cast<int>(names.size()); ++i) {
        if (names[static_cast<std::size_t>(i)] == target) indices.push_back(i);
    }
    return indices;
}

struct CallbackState {
    Api* api = nullptr;
    int ncols = 0;
    std::vector<std::string> col_names;
    int g_col = -1;
    int w_gs_col = -1;
    int r_min_col = -1;
    int r_max_col = -1;
    std::vector<int> r_cols;
    std::vector<int> e_cols;
    std::vector<int> t_sp_cols;
    std::vector<int> q_l1_cols;
    std::vector<std::vector<int>> h_cols;
    std::vector<int> y_cols;
    std::vector<std::vector<int>> z_cols;
    std::vector<std::vector<std::vector<int>>> x_cols;
    std::vector<std::vector<int>> p_cols;
    std::vector<std::vector<int>> d_cols;
    std::vector<std::vector<int>> load_cols;
    std::vector<int> station_initial;
    std::vector<int> station_capacity;
    std::vector<int> station_target;
    std::vector<double> station_weight;
    std::vector<int> vehicle_capacity;
    std::vector<double> distance_matrix;
    int node_count = 0;
    double total_time_limit = 0.0;
    double handling_unit = 0.0;
    std::string support_duration_cover_mode = "support_cover_lifted";
    int gini_subset_max_size = 3;
    int gini_subset_max_cuts = 50000;
    int vector_route_cutset_max_size = 3;
    int vector_route_cutset_max_cuts = 50;
    double vector_route_cutset_min_violation = 1e-6;
    std::string separation_pacing = "off";
    int separation_min_relaxation_calls = 25;
    std::string callback_cut_profile = "full";
    bool enable_local_centering = false;
    double lambda = 0.0;
    double cutoff_value = std::numeric_limits<double>::infinity();
    double gamma_L = 0.0;
    double gamma_U = 1.0;
    bool add_gini_cut = false;
    bool validate_candidates = false;
    bool enable_gini_branch = false;
    double gini_branch_min_width = 1e-4;
    std::chrono::steady_clock::time_point wall_start =
        std::chrono::steady_clock::now();
    double wall_time_limit_seconds = 0.0;
    std::atomic<bool> wall_time_abort{false};
    std::atomic<long long> callback_abort_requests{0};
    std::atomic<bool> native_best_bound_available{false};
    std::atomic<double> native_best_bound{0.0};
    std::atomic<bool> native_incumbent_available{false};
    std::atomic<double> native_incumbent{0.0};
    std::atomic<long long> native_node_count{0};
    std::atomic<double> native_last_bound_improvement_time{0.0};
    std::atomic<long long> relaxation_calls{0};
    std::atomic<long long> candidate_calls{0};
    std::atomic<long long> branch_calls{0};
    std::atomic<long long> progress_calls{0};
    std::atomic<bool> relaxation_vector_sample_attempted{false};
    std::atomic<bool> relaxation_vector_snapshot_available{false};
    std::atomic<int> relaxation_vector_api_return_code{-1};
    std::atomic<int> relaxation_vector_length_requested{0};
    std::atomic<int> relaxation_vector_length_returned{0};
    std::atomic<long long> relaxation_vector_nonzero_values{0};
    std::atomic<double> relaxation_vector_objective{0.0};
    std::string relaxation_vector_sample_variable_names;
    std::string relaxation_vector_sample_variable_values;
    std::string relaxation_vector_full_variable_names;
    std::string relaxation_vector_full_variable_values;
    std::string relaxation_vector_failure_reason;
    std::atomic<bool> candidate_vector_sample_attempted{false};
    std::atomic<bool> candidate_vector_snapshot_available{false};
    std::atomic<int> candidate_vector_api_return_code{-1};
    std::atomic<int> candidate_vector_length_requested{0};
    std::atomic<int> candidate_vector_length_returned{0};
    std::atomic<long long> candidate_vector_nonzero_values{0};
    std::atomic<double> candidate_vector_objective{0.0};
    std::string candidate_vector_sample_variable_names;
    std::string candidate_vector_sample_variable_values;
    std::string candidate_vector_full_variable_names;
    std::string candidate_vector_full_variable_values;
    std::string candidate_vector_failure_reason;
    std::mutex vector_snapshot_mutex;
    std::atomic<long long> user_cuts_added{0};
    std::atomic<long long> gini_interval_cuts_added{0};
    std::atomic<long long> visit_inventory_cuts_added{0};
    std::atomic<long long> gini_subset_envelope_cuts_added{0};
    std::atomic<long long> gini_subset_envelope_candidates{0};
    std::atomic<long long> gini_subset_envelope_violations{0};
    std::atomic<double> gini_subset_envelope_max_violation{0.0};
    std::mutex gini_subset_envelope_mutex;
    std::set<std::string> gini_subset_envelope_cut_keys;
    std::atomic<long long> expensive_separation_calls{0};
    std::atomic<long long> expensive_separation_skips{0};
    std::atomic<long long> last_expensive_separation_call{0};
    std::atomic<double> last_expensive_separation_bound{
        -std::numeric_limits<double>::infinity()};
    std::atomic<long long> low_gini_l1_cuts_added{0};
    std::atomic<long long> low_gini_l1_violations{0};
    std::atomic<long long> local_centering_cuts_added{0};
    std::atomic<long long> local_centering_violations{0};
    std::atomic<double> local_centering_max_violation{0.0};
    std::mutex local_centering_mutex;
    std::set<std::string> local_centering_cut_keys;
    bool enable_subset_cross_h_centering = false;
    int subset_cross_h_max_size = 3;
    int subset_cross_h_max_cuts = 50000;
    std::string subset_cross_h_separation_profile = "deviation";
    std::atomic<long long> subset_cross_h_centering_cuts_added{0};
    std::atomic<long long> subset_cross_h_centering_candidates{0};
    std::atomic<long long> subset_cross_h_centering_violations{0};
    std::atomic<double> subset_cross_h_centering_max_violation{0.0};
    std::mutex subset_cross_h_centering_mutex;
    std::set<std::string> subset_cross_h_centering_cut_keys;
    bool enable_local_q_centering = false;
    std::atomic<long long> local_q_centering_cuts_added{0};
    std::atomic<long long> local_q_centering_violations{0};
    std::atomic<double> local_q_centering_max_violation{0.0};
    std::atomic<long long> gs_product_cuts_added{0};
    std::atomic<long long> gs_product_violations{0};
    std::atomic<double> gs_product_max_violation{0.0};
    std::atomic<bool> gs_product_cut_added{false};
    std::atomic<long long> disagg_sp_cuts_added{0};
    std::atomic<long long> disagg_sp_violations{0};
    std::atomic<double> disagg_sp_max_violation{0.0};
    std::atomic<bool> disagg_sp_cut_added{false};
    std::atomic<long long> vector_route_cutset_cuts_added{0};
    std::atomic<long long> vector_route_cutset_candidates{0};
    std::atomic<long long> vector_route_cutset_violations{0};
    std::atomic<double> vector_route_cutset_max_violation{0.0};
    std::atomic<double> vector_route_cutset_violation_sum{0.0};
    std::array<std::atomic<long long>, 6> vector_route_cutset_cuts_by_size{};
    std::atomic<bool> vector_route_cutset_separated{false};
    std::mutex vector_route_cutset_mutex;
    std::set<std::string> vector_route_cutset_keys;
    std::mutex local_q_centering_mutex;
    std::set<std::string> local_q_centering_cut_keys;
    std::atomic<long long> variable_s_centering_cuts_added{0};
    std::atomic<long long> variable_s_centering_violations{0};
    std::atomic<long long> subset_inventory_imbalance_cuts_added{0};
    std::atomic<long long> subset_inventory_imbalance_candidates{0};
    std::atomic<long long> subset_inventory_imbalance_violations{0};
    std::atomic<long long> transfer_cutset_cuts_added{0};
    std::atomic<long long> transfer_cutset_candidates{0};
    std::atomic<long long> transfer_cutset_violations{0};
    std::atomic<long long> support_duration_pair_cuts_added{0};
    std::atomic<long long> support_duration_pair_candidates{0};
    std::atomic<long long> support_duration_pair_violations{0};
    std::atomic<long long> support_duration_triple_cuts_added{0};
    std::atomic<long long> support_duration_triple_candidates{0};
    std::atomic<long long> support_duration_triple_violations{0};
    std::atomic<long long> support_duration_quad_cuts_added{0};
    std::atomic<long long> support_duration_quad_candidates{0};
    std::atomic<long long> support_duration_quad_violations{0};
    std::atomic<long long> support_duration_lifted_cuts_added{0};
    std::atomic<long long> support_duration_lifted_candidates{0};
    std::atomic<long long> support_duration_lifted_violations{0};
    std::atomic<long long> lazy_rejections{0};
    std::atomic<long long> lazy_gini_interval_rejections{0};
    std::atomic<long long> lazy_visit_inventory_rejections{0};
    std::atomic<long long> lazy_gini_subset_envelope_rejections{0};
    std::atomic<long long> lazy_low_gini_l1_rejections{0};
    std::atomic<long long> lazy_variable_s_centering_rejections{0};
    std::atomic<long long> lazy_subset_inventory_imbalance_rejections{0};
    std::atomic<long long> incumbents_seen{0};
    std::atomic<long long> incumbents_verified{0};
    std::atomic<long long> incumbents_rejected{0};
    std::atomic<long long> candidate_projection_checks{0};
    std::atomic<long long> candidate_projection_verified{0};
    std::atomic<long long> candidate_projection_rejections{0};
    std::atomic<long long> candidate_projection_unsupported_mismatches{0};
    std::atomic<long long> candidate_projection_ratio_rejections{0};
    std::atomic<long long> candidate_projection_penalty_rejections{0};
    std::atomic<long long> candidate_projection_objective_rejections{0};
    std::atomic<double> candidate_projection_max_gini_underestimate{0.0};
    std::atomic<double> candidate_projection_max_objective_underestimate{0.0};
    std::atomic<long long> candidate_route_projection_checks{0};
    std::atomic<long long> candidate_route_projection_verified{0};
    std::atomic<long long> candidate_route_projection_rejections{0};
    std::atomic<long long> candidate_route_projection_unsupported_mismatches{0};
    std::atomic<long long> candidate_route_projection_flow_rejections{0};
    std::atomic<long long> candidate_route_projection_station_rejections{0};
    std::atomic<long long> candidate_route_projection_service_rejections{0};
    std::atomic<long long> candidate_route_projection_duration_rejections{0};
    std::atomic<long long> candidate_route_projection_inventory_rejections{0};
    std::atomic<long long> candidate_route_projection_load_mismatches{0};
    std::atomic<long long> gini_branches_created{0};
    std::atomic<bool> gini_cut_added{false};
    std::atomic<bool> gini_branch_created{false};
    std::atomic<bool> subset_inventory_separated{false};
    std::atomic<bool> transfer_cutset_separated{false};
    std::atomic<bool> support_duration_separated{false};
};

void atomicMax(std::atomic<double>& target, double value) {
    if (!std::isfinite(value) || value <= 0.0) return;
    double current = target.load();
    while (value > current &&
           !target.compare_exchange_weak(current, value)) {
    }
}

void atomicAdd(std::atomic<double>& target, double value) {
    if (!std::isfinite(value)) return;
    double current = target.load();
    while (!target.compare_exchange_weak(current, current + value)) {
    }
}

void sampleCallbackVector(CallbackState& state,
                          CPXCALLBACKCONTEXTptr context,
                          bool relaxation_context) {
    std::atomic<bool>& attempted = relaxation_context
        ? state.relaxation_vector_sample_attempted
        : state.candidate_vector_sample_attempted;
    bool expected = false;
    if (!attempted.compare_exchange_strong(expected, true)) return;

    if (state.ncols <= 0) {
        std::lock_guard<std::mutex> lock(state.vector_snapshot_mutex);
        if (relaxation_context) {
            state.relaxation_vector_failure_reason = "no_columns_in_model";
            state.relaxation_vector_length_requested.store(0);
            state.relaxation_vector_length_returned.store(0);
        } else {
            state.candidate_vector_failure_reason = "no_columns_in_model";
            state.candidate_vector_length_requested.store(0);
            state.candidate_vector_length_returned.store(0);
        }
        return;
    }

    if (!relaxation_context) {
        int is_point = 0;
        const int point_rc = state.api->callbackcandidateispoint(context, &is_point);
        if (point_rc != 0 || !is_point) {
            std::lock_guard<std::mutex> lock(state.vector_snapshot_mutex);
            state.candidate_vector_api_return_code.store(point_rc);
            state.candidate_vector_length_requested.store(state.ncols);
            state.candidate_vector_length_returned.store(0);
            state.candidate_vector_failure_reason = point_rc == 0
                ? "candidate_context_without_point"
                : "CPXcallbackcandidateispoint_failed:" + std::to_string(point_rc);
            return;
        }
    }

    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    const int rc = relaxation_context
        ? state.api->callbackgetrelaxationpoint(
              context, x.data(), 0, state.ncols - 1, &obj)
        : state.api->callbackgetcandidatepoint(
              context, x.data(), 0, state.ncols - 1, &obj);

    long long nonzero = 0;
    std::ostringstream sample_names;
    std::ostringstream sample_values;
    std::ostringstream full_names;
    std::ostringstream full_values;
    sample_values << std::setprecision(17);
    full_values << std::setprecision(17);
    constexpr int sample_limit = 32;
    int sampled = 0;
    if (rc == 0) {
        for (int i = 0; i < state.ncols; ++i) {
            const double value = x[static_cast<std::size_t>(i)];
            const std::string name =
                i < static_cast<int>(state.col_names.size()) &&
                        !state.col_names[static_cast<std::size_t>(i)].empty()
                    ? state.col_names[static_cast<std::size_t>(i)]
                    : "col_" + std::to_string(i);
            if (i > 0) {
                full_names << ';';
                full_values << ';';
            }
            full_names << name;
            full_values << value;
            if (std::fabs(value) > 1e-10) {
                ++nonzero;
            }
            if (std::fabs(value) > 1e-10 && sampled < sample_limit) {
                if (sampled > 0) {
                    sample_names << ';';
                    sample_values << ';';
                }
                sample_names << name;
                sample_values << value;
                ++sampled;
            }
        }
    }

    std::lock_guard<std::mutex> lock(state.vector_snapshot_mutex);
    if (relaxation_context) {
        state.relaxation_vector_api_return_code.store(rc);
        state.relaxation_vector_length_requested.store(state.ncols);
        state.relaxation_vector_length_returned.store(rc == 0 ? state.ncols : 0);
        state.relaxation_vector_nonzero_values.store(rc == 0 ? nonzero : 0);
        state.relaxation_vector_objective.store(rc == 0 ? obj : 0.0);
        state.relaxation_vector_snapshot_available.store(rc == 0);
        state.relaxation_vector_sample_variable_names =
            rc == 0 ? sample_names.str() : "not_available";
        state.relaxation_vector_sample_variable_values =
            rc == 0 ? sample_values.str() : "not_available";
        state.relaxation_vector_full_variable_names =
            rc == 0 ? full_names.str() : "not_available";
        state.relaxation_vector_full_variable_values =
            rc == 0 ? full_values.str() : "not_available";
        state.relaxation_vector_failure_reason =
            rc == 0 ? "none"
                    : "CPXcallbackgetrelaxationpoint_failed:" +
                          std::to_string(rc);
    } else {
        state.candidate_vector_api_return_code.store(rc);
        state.candidate_vector_length_requested.store(state.ncols);
        state.candidate_vector_length_returned.store(rc == 0 ? state.ncols : 0);
        state.candidate_vector_nonzero_values.store(rc == 0 ? nonzero : 0);
        state.candidate_vector_objective.store(rc == 0 ? obj : 0.0);
        state.candidate_vector_snapshot_available.store(rc == 0);
        state.candidate_vector_sample_variable_names =
            rc == 0 ? sample_names.str() : "not_available";
        state.candidate_vector_sample_variable_values =
            rc == 0 ? sample_values.str() : "not_available";
        state.candidate_vector_full_variable_names =
            rc == 0 ? full_names.str() : "not_available";
        state.candidate_vector_full_variable_values =
            rc == 0 ? full_values.str() : "not_available";
        state.candidate_vector_failure_reason =
            rc == 0 ? "none"
                    : "CPXcallbackgetcandidatepoint_failed:" +
                          std::to_string(rc);
    }
}

bool shouldRunExpensiveSeparation(CallbackState& state) {
    if (state.separation_pacing != "bound-aware") {
        state.expensive_separation_calls.fetch_add(1);
        state.last_expensive_separation_call.store(state.relaxation_calls.load());
        if (state.native_best_bound_available.load()) {
            state.last_expensive_separation_bound.store(
                state.native_best_bound.load());
        }
        return true;
    }
    const long long call = state.relaxation_calls.load();
    if (call <= 2) {
        state.expensive_separation_calls.fetch_add(1);
        state.last_expensive_separation_call.store(call);
        if (state.native_best_bound_available.load()) {
            state.last_expensive_separation_bound.store(
                state.native_best_bound.load());
        }
        return true;
    }
    const long long min_calls =
        std::max(1, state.separation_min_relaxation_calls);
    const long long last_call = state.last_expensive_separation_call.load();
    bool due_by_calls = call - last_call >= min_calls;
    bool due_by_bound = false;
    if (state.native_best_bound_available.load()) {
        const double bound = state.native_best_bound.load();
        const double previous = state.last_expensive_separation_bound.load();
        due_by_bound = std::isfinite(bound) &&
            (!std::isfinite(previous) || bound > previous + 1e-8);
    }
    if (due_by_calls || due_by_bound) {
        state.expensive_separation_calls.fetch_add(1);
        state.last_expensive_separation_call.store(call);
        if (state.native_best_bound_available.load()) {
            state.last_expensive_separation_bound.store(
                state.native_best_bound.load());
        }
        return true;
    }
    state.expensive_separation_skips.fetch_add(1);
    return false;
}

bool callbackProfileAllows(const CallbackState& state,
                           const std::string& family) {
    const std::string& profile = state.callback_cut_profile;
    if (profile == "none" || profile == "off") return false;
    if (profile == "full") return true;
    if (profile == "cheap") {
        return family == "gini_interval" || family == "visit_inventory";
    }
    if (profile == "low-gini" || profile == "low_gini") {
        return family == "gini_interval" ||
            family == "visit_inventory" ||
            family == "low_gini_l1" ||
            family == "variable_s" ||
            family == "local_centering" ||
            family == "subset_cross_h" ||
            family == "local_q";
    }
    if (profile == "local-centering" || profile == "local_centering") {
        return family == "gini_interval" ||
            family == "visit_inventory" ||
            family == "local_centering" ||
            family == "subset_cross_h" ||
            family == "local_q";
    }
    if (profile == "subset-only" || profile == "subset_only") {
        return family == "gini_interval" ||
            family == "gini_subset" ||
            family == "subset_cross_h";
    }
    if (profile == "transfer-only" || profile == "transfer_only") {
        return family == "gini_interval" ||
            family == "transfer_cutset";
    }
    if (profile == "support-only" || profile == "support_only") {
        return family == "gini_interval" ||
            family == "support_duration";
    }
    if (profile == "subset-cross-h-only" || profile == "subset_cross_h_only") {
        return family == "gini_interval" ||
            family == "subset_cross_h";
    }
    if (profile == "local-q-only" || profile == "local_q_only") {
        return family == "gini_interval" ||
            family == "local_q";
    }
    if (profile == "gs-only" || profile == "gs_only") {
        return family == "gini_interval" || family == "gs_product";
    }
    if (profile == "sp-only" || profile == "sp_only") {
        return family == "gini_interval" || family == "disagg_sp";
    }
    if (profile == "gs-sp-only" || profile == "gs_sp_only") {
        return family == "gini_interval" || family == "gs_product" ||
            family == "disagg_sp";
    }
    if (profile == "route-cutset-only" || profile == "route_cutset_only") {
        return family == "gini_interval" || family == "vector_route_cutset";
    }
    if (profile == "route-combined" || profile == "route_combined") {
        return family == "gini_interval" || family == "support_duration" ||
            family == "vector_route_cutset";
    }
    return true;
}

bool rejectCandidateWithLazyRow(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context,
                                const std::vector<std::pair<int, double>>& terms,
                                char sense_value,
                                double rhs_value) {
    std::vector<int> beg = {0};
    std::vector<int> ind;
    std::vector<double> val;
    ind.reserve(terms.size());
    val.reserve(terms.size());
    for (const auto& term : terms) {
        if (term.first < 0 || std::fabs(term.second) <= 1e-12) continue;
        ind.push_back(term.first);
        val.push_back(term.second);
    }
    if (ind.empty()) return false;
    const double rhs[1] = {rhs_value};
    const char sense[1] = {sense_value};
    const int rc = state.api->callbackrejectcandidate(
        context, 1, static_cast<int>(ind.size()), rhs, sense,
        beg.data(), ind.data(), val.data());
    if (rc == 0) {
        ++state.lazy_rejections;
        ++state.incumbents_rejected;
        return true;
    }
    return false;
}

bool rejectCandidateWithGiniBound(CallbackState& state,
                                  CPXCALLBACKCONTEXTptr context,
                                  bool upper_bound) {
    if (state.g_col < 0) return false;
    if (rejectCandidateWithLazyRow(
            state, context, {{state.g_col, 1.0}},
            upper_bound ? 'L' : 'G',
            upper_bound ? state.gamma_U : state.gamma_L)) {
        ++state.lazy_gini_interval_rejections;
        return true;
    }
    return false;
}

int safeCol(const std::vector<std::vector<int>>& cols, int k, int i);

bool addOneUserCut(CallbackState& state,
                   CPXCALLBACKCONTEXTptr context,
                   const std::vector<std::pair<int, double>>& terms,
                   char sense,
                   double rhs) {
    if (terms.empty()) return false;
    std::vector<int> beg = {0};
    std::vector<int> ind;
    std::vector<double> val;
    ind.reserve(terms.size());
    val.reserve(terms.size());
    for (const auto& term : terms) {
        if (term.first < 0 || std::fabs(term.second) <= 1e-12) continue;
        ind.push_back(term.first);
        val.push_back(term.second);
    }
    if (ind.empty()) return false;
    const int purgeable[1] = {kUseCutForce};
    const int local[1] = {0};
    const int rc = state.api->callbackaddusercuts(
        context, 1, static_cast<int>(ind.size()), &rhs, &sense,
        beg.data(), ind.data(), val.data(), purgeable, local);
    if (rc == 0) {
        ++state.user_cuts_added;
        return true;
    }
    return false;
}

void separateGsProductCoupling(CallbackState& state,
                               CPXCALLBACKCONTEXTptr context) {
    if (state.w_gs_col < 0 || state.h_cols.size() <= 1 ||
        state.gs_product_cut_added.load()) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = static_cast<int>(state.h_cols.size()) - 1;
    std::vector<std::pair<int, double>> terms;
    double lhs = -static_cast<double>(V) *
        x[static_cast<std::size_t>(state.w_gs_col)];
    terms.push_back({state.w_gs_col, -static_cast<double>(V)});
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            const int h = state.h_cols[static_cast<std::size_t>(i)]
                                      [static_cast<std::size_t>(j)];
            if (h < 0) return;
            lhs += x[static_cast<std::size_t>(h)];
            terms.push_back({h, 1.0});
        }
    }
    constexpr double tol = 1e-6;
    if (lhs <= tol) return;
    state.gs_product_violations.fetch_add(1);
    atomicMax(state.gs_product_max_violation, lhs);
    bool expected = false;
    if (!state.gs_product_cut_added.compare_exchange_strong(expected, true)) return;
    if (addOneUserCut(state, context, terms, 'L', 0.0)) {
        state.gs_product_cuts_added.fetch_add(1);
    } else {
        state.gs_product_cut_added.store(false);
    }
}

void separateDisaggregatedSpEstimator(CallbackState& state,
                                      CPXCALLBACKCONTEXTptr context) {
    if (state.t_sp_cols.size() <= 1 || state.h_cols.size() <= 1 ||
        state.r_cols.size() <= 1 || !std::isfinite(state.cutoff_value) ||
        state.disagg_sp_cut_added.load()) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = std::min({static_cast<int>(state.h_cols.size()),
                            static_cast<int>(state.r_cols.size()),
                            static_cast<int>(state.t_sp_cols.size()),
                            static_cast<int>(state.station_weight.size())}) - 1;
    if (V <= 0) return;
    std::vector<std::pair<int, double>> terms;
    double lhs = 0.0;
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        const int t = state.t_sp_cols[static_cast<std::size_t>(i)];
        if (r < 0 || t < 0) return;
        const double t_coef = static_cast<double>(V) * state.lambda *
            state.station_weight[static_cast<std::size_t>(i)];
        const double r_coef = -static_cast<double>(V) * state.cutoff_value;
        lhs += t_coef * x[static_cast<std::size_t>(t)] +
               r_coef * x[static_cast<std::size_t>(r)];
        terms.push_back({t, t_coef});
        terms.push_back({r, r_coef});
        for (int j = i + 1; j <= V; ++j) {
            const int h = state.h_cols[static_cast<std::size_t>(i)]
                                      [static_cast<std::size_t>(j)];
            if (h < 0) return;
            lhs += x[static_cast<std::size_t>(h)];
            terms.push_back({h, 1.0});
        }
    }
    constexpr double tol = 1e-6;
    if (lhs <= tol) return;
    state.disagg_sp_violations.fetch_add(1);
    atomicMax(state.disagg_sp_max_violation, lhs);
    bool expected = false;
    if (!state.disagg_sp_cut_added.compare_exchange_strong(expected, true)) return;
    if (addOneUserCut(state, context, terms, 'L', 0.0)) {
        state.disagg_sp_cuts_added.fetch_add(1);
    } else {
        state.disagg_sp_cut_added.store(false);
    }
}

void separateVectorRouteCutset(CallbackState& state,
                               CPXCALLBACKCONTEXTptr context) {
    if (state.x_cols.empty() || state.z_cols.empty() || state.ncols <= 0) return;
    bool expected = false;
    if (!state.vector_route_cutset_separated.compare_exchange_strong(expected, true)) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int max_size = std::min(5, std::max(2, state.vector_route_cutset_max_size));
    const long long max_cuts = std::max(0, state.vector_route_cutset_max_cuts);
    const double tol = std::max(1e-12, state.vector_route_cutset_min_violation);
    for (int k = 0; k < static_cast<int>(state.z_cols.size()); ++k) {
        if (max_cuts > 0 && state.vector_route_cutset_cuts_added.load() >= max_cuts) break;
        std::vector<std::pair<double, int>> ranked;
        for (int i = 1; i < static_cast<int>(state.z_cols[static_cast<std::size_t>(k)].size()); ++i) {
            const int z = safeCol(state.z_cols, k, i);
            if (z >= 0 && x[static_cast<std::size_t>(z)] > tol) {
                ranked.push_back({x[static_cast<std::size_t>(z)], i});
            }
        }
        std::sort(ranked.begin(), ranked.end(), std::greater<>());
        if (ranked.size() > 10) ranked.resize(10);
        std::vector<int> subset;
        std::function<void(int, int)> enumerate = [&](int start, int target_size) {
            if (max_cuts > 0 && state.vector_route_cutset_cuts_added.load() >= max_cuts) return;
            if (static_cast<int>(subset.size()) == target_size) {
                std::set<int> inside(subset.begin(), subset.end());
                for (int representative : subset) {
                    state.vector_route_cutset_candidates.fetch_add(1);
                    std::map<int, double> term_map;
                    double boundary = 0.0;
                    for (int i = 0; i < state.node_count; ++i) {
                        const bool i_in = inside.count(i) > 0;
                        for (int j = 0; j < state.node_count; ++j) {
                            if (i == j) continue;
                            const bool j_in = inside.count(j) > 0;
                            if (i_in == j_in) continue;
                            const int arc = state.x_cols[static_cast<std::size_t>(k)]
                                                       [static_cast<std::size_t>(i)]
                                                       [static_cast<std::size_t>(j)];
                            if (arc < 0) continue;
                            boundary += x[static_cast<std::size_t>(arc)];
                            term_map[arc] += 1.0;
                        }
                    }
                    const int z = safeCol(state.z_cols, k, representative);
                    if (z < 0) continue;
                    const double violation = 2.0 * x[static_cast<std::size_t>(z)] - boundary;
                    if (violation <= tol) continue;
                    state.vector_route_cutset_violations.fetch_add(1);
                    atomicMax(state.vector_route_cutset_max_violation, violation);
                    atomicAdd(state.vector_route_cutset_violation_sum, violation);
                    std::ostringstream key;
                    key << k << ':' << representative;
                    for (int station : subset) key << ':' << station;
                    {
                        std::lock_guard<std::mutex> guard(state.vector_route_cutset_mutex);
                        if (!state.vector_route_cutset_keys.insert(key.str()).second) continue;
                    }
                    term_map[z] -= 2.0;
                    std::vector<std::pair<int, double>> terms(term_map.begin(), term_map.end());
                    if (addOneUserCut(state, context, terms, 'G', 0.0)) {
                        state.vector_route_cutset_cuts_added.fetch_add(1);
                        if (target_size >= 0 && target_size <
                                static_cast<int>(state.vector_route_cutset_cuts_by_size.size())) {
                            state.vector_route_cutset_cuts_by_size[
                                static_cast<std::size_t>(target_size)].fetch_add(1);
                        }
                    }
                    if (max_cuts > 0 && state.vector_route_cutset_cuts_added.load() >= max_cuts) return;
                }
                return;
            }
            for (int pos = start; pos < static_cast<int>(ranked.size()); ++pos) {
                subset.push_back(ranked[static_cast<std::size_t>(pos)].second);
                enumerate(pos + 1, target_size);
                subset.pop_back();
                if (max_cuts > 0 && state.vector_route_cutset_cuts_added.load() >= max_cuts) return;
            }
        };
        for (int size = 2; size <= max_size; ++size) enumerate(0, size);
    }
}

int safeCol(const std::vector<std::vector<int>>& cols, int k, int i);

double callbackDistance(const CallbackState& state, int from, int to) {
    if (from < 0 || to < 0 || from >= state.node_count || to >= state.node_count) {
        return std::numeric_limits<double>::infinity();
    }
    const std::size_t idx = static_cast<std::size_t>(from) *
        static_cast<std::size_t>(state.node_count) + static_cast<std::size_t>(to);
    if (idx >= state.distance_matrix.size()) {
        return std::numeric_limits<double>::infinity();
    }
    return state.distance_matrix[idx];
}

double callbackPairCycleLowerBound(const CallbackState& state, int a, int b) {
    return std::min(callbackDistance(state, 0, a) + callbackDistance(state, a, b) +
                        callbackDistance(state, b, 0),
                    callbackDistance(state, 0, b) + callbackDistance(state, b, a) +
                        callbackDistance(state, a, 0));
}

double callbackTripleCycleLowerBound(const CallbackState& state, int a, int b, int c) {
    const int s[3] = {a, b, c};
    int perm[3] = {0, 1, 2};
    double best = std::numeric_limits<double>::infinity();
    do {
        const double travel = callbackDistance(state, 0, s[perm[0]]) +
            callbackDistance(state, s[perm[0]], s[perm[1]]) +
            callbackDistance(state, s[perm[1]], s[perm[2]]) +
            callbackDistance(state, s[perm[2]], 0);
        best = std::min(best, travel);
    } while (std::next_permutation(perm, perm + 3));
    return best;
}

double callbackSubsetCycleLowerBound(const CallbackState& state,
                                     const std::vector<int>& subset) {
    if (subset.empty()) return 0.0;
    if (subset.size() == 1) {
        return callbackDistance(state, 0, subset.front()) +
               callbackDistance(state, subset.front(), 0);
    }
    if (subset.size() == 2) {
        return callbackPairCycleLowerBound(state, subset[0], subset[1]);
    }
    if (subset.size() == 3) {
        return callbackTripleCycleLowerBound(state, subset[0], subset[1], subset[2]);
    }
    if (subset.size() > 8) {
        return std::numeric_limits<double>::infinity();
    }
    std::vector<int> perm(subset.size());
    std::iota(perm.begin(), perm.end(), 0);
    double best = std::numeric_limits<double>::infinity();
    do {
        double travel = callbackDistance(state, 0, subset[static_cast<std::size_t>(perm[0])]);
        bool finite = std::isfinite(travel);
        for (std::size_t pos = 1; finite && pos < perm.size(); ++pos) {
            travel += callbackDistance(
                state,
                subset[static_cast<std::size_t>(perm[pos - 1])],
                subset[static_cast<std::size_t>(perm[pos])]);
            finite = std::isfinite(travel);
        }
        if (finite) {
            travel += callbackDistance(
                state,
                subset[static_cast<std::size_t>(perm.back())],
                0);
            best = std::min(best, travel);
        }
    } while (std::next_permutation(perm.begin(), perm.end()));
    return best;
}

void separateVisitInventoryLinking(CallbackState& state,
                                   CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.y_cols.empty() || state.z_cols.empty()) return;
    if (state.visit_inventory_cuts_added.load() > 0) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    constexpr double tol = 1e-6;
    long long added = 0;
    const int station_count =
        std::min(static_cast<int>(state.y_cols.size()),
                 static_cast<int>(state.station_initial.size()));
    for (int i = 1; i < station_count; ++i) {
        const int y = state.y_cols[static_cast<std::size_t>(i)];
        if (y < 0) continue;
        const double initial =
            static_cast<double>(state.station_initial[static_cast<std::size_t>(i)]);
        const double capacity =
            static_cast<double>(state.station_capacity[static_cast<std::size_t>(i)]);
        std::vector<std::pair<int, double>> upper_terms;
        std::vector<std::pair<int, double>> lower_terms;
        upper_terms.push_back({y, 1.0});
        lower_terms.push_back({y, -1.0});
        double visit = 0.0;
        for (const std::vector<int>& row : state.z_cols) {
            if (i >= static_cast<int>(row.size())) continue;
            const int z = row[static_cast<std::size_t>(i)];
            if (z < 0) continue;
            visit += x[static_cast<std::size_t>(z)];
            upper_terms.push_back({z, -(capacity - initial)});
            lower_terms.push_back({z, -initial});
        }
        const double upper_lhs = x[static_cast<std::size_t>(y)] -
            (capacity - initial) * visit;
        if (upper_lhs > initial + tol &&
            addOneUserCut(state, context, upper_terms, 'L', initial)) {
            ++added;
        }
        const double lower_lhs = -x[static_cast<std::size_t>(y)] -
            initial * visit;
        if (lower_lhs > -initial + tol &&
            addOneUserCut(state, context, lower_terms, 'L', -initial)) {
            ++added;
        }
    }
    if (added > 0) {
        state.visit_inventory_cuts_added.fetch_add(added);
    }
}

bool callbackDeadlineExceeded(CallbackState& state) {
    if (state.wall_time_limit_seconds <= 0.0) return false;
    const double elapsed = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - state.wall_start).count();
    return elapsed >= state.wall_time_limit_seconds;
}

bool requestCallbackAbortIfDeadlineExceeded(CallbackState& state,
                                            CPXCALLBACKCONTEXTptr context) {
    if (!callbackDeadlineExceeded(state)) return false;
    state.wall_time_abort.store(true);
    state.callback_abort_requests.fetch_add(1);
    if (state.api && state.api->callbackabort) {
        state.api->callbackabort(context);
    }
    return true;
}

void sampleNativeCallbackInfo(CallbackState& state,
                              CPXCALLBACKCONTEXTptr context) {
    if (!state.api || !context) return;
    double best_bound = 0.0;
    if (state.api->callbackgetinfodbl &&
        state.api->callbackgetinfodbl(
            context, kCallbackInfoBestBnd, &best_bound) == 0 &&
        std::isfinite(best_bound)) {
        const bool had_bound = state.native_best_bound_available.load();
        const double old_bound = state.native_best_bound.load();
        state.native_best_bound.store(best_bound);
        state.native_best_bound_available.store(true);
        if (!had_bound || best_bound > old_bound + 1e-9) {
            const double elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - state.wall_start).count();
            state.native_last_bound_improvement_time.store(elapsed);
        }
    }
    double incumbent = 0.0;
    if (state.api->callbackgetinfodbl &&
        state.api->callbackgetinfodbl(
            context, kCallbackInfoBestSol, &incumbent) == 0 &&
        std::isfinite(incumbent)) {
        state.native_incumbent.store(incumbent);
        state.native_incumbent_available.store(true);
    }
    CPXLONG node_count = 0;
    if (state.api->callbackgetinfolong &&
        state.api->callbackgetinfolong(
            context, kCallbackInfoNodeCount, &node_count) == 0) {
        state.native_node_count.store(static_cast<long long>(node_count));
    }
}

void separateGiniSubsetEnvelope(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.r_cols.size() <= 1 ||
        state.gamma_U < -1e-12) {
        return;
    }
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    double sum_r = 0.0;
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r >= 0) sum_r += x[static_cast<std::size_t>(r)];
    }
    const int max_subset_size = std::min(
        std::max(1, state.gini_subset_max_size), std::min(4, V - 1));
    const int max_cuts = state.gini_subset_max_cuts <= 0
        ? std::numeric_limits<int>::max()
        : state.gini_subset_max_cuts;
    if (state.gini_subset_envelope_cuts_added.load() >= max_cuts) return;
    int cuts_added_this_call = 0;
    auto addSubsetCut = [&](const std::vector<int>& subset, int sign) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        if (cuts_added_this_call >= max_cuts ||
            state.gini_subset_envelope_cuts_added.load() >= max_cuts) return;
        state.gini_subset_envelope_candidates.fetch_add(1);
        const int a = static_cast<int>(subset.size());
        std::vector<std::pair<int, double>> terms;
        terms.reserve(static_cast<std::size_t>(V));
        double lhs = 0.0;
        for (int i = 1; i <= V; ++i) {
            const int r = state.r_cols[static_cast<std::size_t>(i)];
            if (r < 0) continue;
            double coef = sign > 0
                ? (-static_cast<double>(a) - static_cast<double>(V) * state.gamma_U)
                : ( static_cast<double>(a) - static_cast<double>(V) * state.gamma_U);
            if (std::find(subset.begin(), subset.end(), i) != subset.end()) {
                coef += sign > 0 ? static_cast<double>(V) : -static_cast<double>(V);
            }
            lhs += coef * x[static_cast<std::size_t>(r)];
            terms.push_back({r, coef});
        }
        constexpr double tol = 1e-6;
        if (lhs > tol) {
            state.gini_subset_envelope_violations.fetch_add(1);
            atomicMax(state.gini_subset_envelope_max_violation, lhs);
            std::vector<int> key_subset = subset;
            std::sort(key_subset.begin(), key_subset.end());
            std::ostringstream key_stream;
            key_stream << sign << ":";
            for (int station : key_subset) key_stream << station << ",";
            {
                std::lock_guard<std::mutex> guard(
                    state.gini_subset_envelope_mutex);
                if (!state.gini_subset_envelope_cut_keys
                         .insert(key_stream.str())
                         .second) {
                    return;
                }
            }
            if (addOneUserCut(state, context, terms, 'L', 0.0)) {
                state.gini_subset_envelope_cuts_added.fetch_add(1);
                ++cuts_added_this_call;
            }
        }
    };
    if (sum_r <= 1e-12) return;

    std::vector<std::pair<double, int>> positive;
    std::vector<std::pair<double, int>> negative;
    positive.reserve(static_cast<std::size_t>(V));
    negative.reserve(static_cast<std::size_t>(V));
    const double mean = sum_r / static_cast<double>(V);
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r < 0) continue;
        const double dev = x[static_cast<std::size_t>(r)] - mean;
        positive.push_back({dev, i});
        negative.push_back({-dev, i});
    }
    auto byDeviation = [](const auto& a, const auto& b) {
        if (std::fabs(a.first - b.first) > 1e-12) return a.first > b.first;
        return a.second < b.second;
    };
    std::sort(positive.begin(), positive.end(), byDeviation);
    std::sort(negative.begin(), negative.end(), byDeviation);
    const int candidate_pool = std::min(V, 8);

    auto testRankedSubsets = [&](const std::vector<std::pair<double, int>>& ranked,
                                 int sign) {
        std::vector<int> prefix;
        prefix.reserve(static_cast<std::size_t>(max_subset_size));
        for (int i = 0; i < static_cast<int>(ranked.size()) && i < candidate_pool; ++i) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            if (ranked[static_cast<std::size_t>(i)].first <= 1e-12) break;
            prefix.push_back(ranked[static_cast<std::size_t>(i)].second);
            if (static_cast<int>(prefix.size()) <= max_subset_size) {
                addSubsetCut(prefix, sign);
            }
            if (cuts_added_this_call >= max_cuts) return;
        }
        if (max_subset_size >= 2) {
            const int n = std::min(static_cast<int>(ranked.size()), candidate_pool);
            for (int i = 0; i < n; ++i) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                if (ranked[static_cast<std::size_t>(i)].first <= 1e-12) continue;
                for (int j = i + 1; j < n; ++j) {
                    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                    if (ranked[static_cast<std::size_t>(j)].first <= 1e-12) continue;
                    addSubsetCut({ranked[static_cast<std::size_t>(i)].second,
                                  ranked[static_cast<std::size_t>(j)].second}, sign);
                    if (cuts_added_this_call >= max_cuts) return;
                }
            }
        }
        if (max_subset_size >= 3) {
            const int n = std::min(static_cast<int>(ranked.size()), std::min(candidate_pool, 6));
            for (int i = 0; i < n; ++i) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                if (ranked[static_cast<std::size_t>(i)].first <= 1e-12) continue;
                for (int j = i + 1; j < n; ++j) {
                    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                    if (ranked[static_cast<std::size_t>(j)].first <= 1e-12) continue;
                    for (int h = j + 1; h < n; ++h) {
                        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                        if (ranked[static_cast<std::size_t>(h)].first <= 1e-12) continue;
                        addSubsetCut({ranked[static_cast<std::size_t>(i)].second,
                                      ranked[static_cast<std::size_t>(j)].second,
                                      ranked[static_cast<std::size_t>(h)].second}, sign);
                        if (cuts_added_this_call >= max_cuts) return;
                    }
                }
            }
        }
        if (max_subset_size >= 4) {
            const int n = std::min(static_cast<int>(ranked.size()), std::min(candidate_pool, 5));
            for (int i = 0; i < n; ++i) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                if (ranked[static_cast<std::size_t>(i)].first <= 1e-12) continue;
                for (int j = i + 1; j < n; ++j) {
                    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                    if (ranked[static_cast<std::size_t>(j)].first <= 1e-12) continue;
                    for (int h = j + 1; h < n; ++h) {
                        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                        if (ranked[static_cast<std::size_t>(h)].first <= 1e-12) continue;
                        for (int q = h + 1; q < n; ++q) {
                            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                            if (ranked[static_cast<std::size_t>(q)].first <= 1e-12) continue;
                            addSubsetCut({ranked[static_cast<std::size_t>(i)].second,
                                          ranked[static_cast<std::size_t>(j)].second,
                                          ranked[static_cast<std::size_t>(h)].second,
                                          ranked[static_cast<std::size_t>(q)].second}, sign);
                            if (cuts_added_this_call >= max_cuts) return;
                        }
                    }
                }
            }
        }
    };
    testRankedSubsets(positive, 1);
    if (cuts_added_this_call < max_cuts) testRankedSubsets(negative, -1);
}

void separateLowGiniL1Centering(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.r_cols.size() <= 1 ||
        state.q_l1_cols.size() <= 1 || state.gamma_U < -1e-12) {
        return;
    }
    if (state.low_gini_l1_cuts_added.load() > 0) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = std::min(static_cast<int>(state.r_cols.size()),
                           static_cast<int>(state.q_l1_cols.size())) - 1;
    std::vector<std::pair<int, double>> terms;
    terms.reserve(static_cast<std::size_t>(2 * V));
    double lhs = 0.0;
    for (int i = 1; i <= V; ++i) {
        const int q = state.q_l1_cols[static_cast<std::size_t>(i)];
        if (q >= 0) {
            lhs += x[static_cast<std::size_t>(q)];
            terms.push_back({q, 1.0});
        }
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r >= 0) {
            const double coef = -2.0 * state.gamma_U;
            lhs += coef * x[static_cast<std::size_t>(r)];
            terms.push_back({r, coef});
        }
    }
    constexpr double tol = 1e-6;
    if (lhs > tol) {
        state.low_gini_l1_violations.fetch_add(1);
        if (addOneUserCut(state, context, terms, 'L', 0.0)) {
            state.low_gini_l1_cuts_added.fetch_add(1);
        }
    }
}

void separateLocalCentering(CallbackState& state,
                            CPXCALLBACKCONTEXTptr context) {
    if (!state.enable_local_centering || state.ncols <= 0 ||
        state.r_cols.size() <= 1 || state.h_cols.size() <= 1) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    if (V <= 1) return;
    double sum_r = 0.0;
    for (int j = 1; j <= V; ++j) {
        const int r = state.r_cols[static_cast<std::size_t>(j)];
        if (r >= 0) sum_r += x[static_cast<std::size_t>(r)];
    }
    constexpr double tol = 1e-6;
    auto hCol = [&](int a, int b) -> int {
        if (a > b) std::swap(a, b);
        if (a < 0 || b < 0 ||
            a >= static_cast<int>(state.h_cols.size()) ||
            b >= static_cast<int>(state.h_cols[static_cast<std::size_t>(a)].size())) {
            return -1;
        }
        return state.h_cols[static_cast<std::size_t>(a)][static_cast<std::size_t>(b)];
    };
    auto tryRow = [&](int station, int sign) {
        const int r_i = state.r_cols[static_cast<std::size_t>(station)];
        if (r_i < 0) return;
        std::map<int, double> term_map;
        auto addTerm = [&](int col, double coef) {
            if (col < 0 || std::fabs(coef) <= 1e-12) return;
            term_map[col] += coef;
            if (std::fabs(term_map[col]) <= 1e-12) term_map.erase(col);
        };
        double lhs = sign > 0
            ? static_cast<double>(V) * x[static_cast<std::size_t>(r_i)] - sum_r
            : sum_r - static_cast<double>(V) * x[static_cast<std::size_t>(r_i)];
        if (sign > 0) {
            addTerm(r_i, static_cast<double>(V));
            for (int j = 1; j <= V; ++j) {
                const int r = state.r_cols[static_cast<std::size_t>(j)];
                addTerm(r, -1.0);
            }
        } else {
            for (int j = 1; j <= V; ++j) {
                const int r = state.r_cols[static_cast<std::size_t>(j)];
                addTerm(r, 1.0);
            }
            addTerm(r_i, -static_cast<double>(V));
        }
        for (int j = 1; j <= V; ++j) {
            if (j == station) continue;
            const int h = hCol(station, j);
            if (h < 0) return;
            lhs -= x[static_cast<std::size_t>(h)];
            addTerm(h, -1.0);
        }
        if (lhs <= tol) return;
        state.local_centering_violations.fetch_add(1);
        atomicMax(state.local_centering_max_violation, lhs);
        std::ostringstream key;
        key << sign << ":" << station;
        {
            std::lock_guard<std::mutex> guard(state.local_centering_mutex);
            if (!state.local_centering_cut_keys.insert(key.str()).second) {
                return;
            }
        }
        std::vector<std::pair<int, double>> terms;
        terms.reserve(term_map.size());
        for (const auto& kv : term_map) terms.push_back(kv);
        if (addOneUserCut(state, context, terms, 'L', 0.0)) {
            state.local_centering_cuts_added.fetch_add(1);
        }
    };
    for (int i = 1; i <= V; ++i) {
        tryRow(i, 1);
        tryRow(i, -1);
    }
}

void separateSubsetCrossHCentering(CallbackState& state,
                                   CPXCALLBACKCONTEXTptr context) {
    if (!state.enable_subset_cross_h_centering || state.ncols <= 0 ||
        state.r_cols.size() <= 1 || state.h_cols.size() <= 1) {
        return;
    }
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    if (V <= 1) return;
    const int max_size = std::min({4, V, std::max(1, state.subset_cross_h_max_size)});
    const long long max_cuts = state.subset_cross_h_max_cuts > 0
        ? static_cast<long long>(state.subset_cross_h_max_cuts)
        : std::numeric_limits<long long>::max();
    if (state.subset_cross_h_centering_cuts_added.load() >= max_cuts) return;

    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    double sum_r = 0.0;
    for (int j = 1; j <= V; ++j) {
        const int r = state.r_cols[static_cast<std::size_t>(j)];
        if (r >= 0) sum_r += x[static_cast<std::size_t>(r)];
    }
    const double avg_r = sum_r / static_cast<double>(V);
    auto hCol = [&](int a, int b) -> int {
        if (a > b) std::swap(a, b);
        if (a < 0 || b < 0 ||
            a >= static_cast<int>(state.h_cols.size()) ||
            b >= static_cast<int>(state.h_cols[static_cast<std::size_t>(a)].size())) {
            return -1;
        }
        return state.h_cols[static_cast<std::size_t>(a)][static_cast<std::size_t>(b)];
    };
    auto safeVal = [&](int col) {
        return col >= 0 ? x[static_cast<std::size_t>(col)] : 0.0;
    };
    std::vector<std::pair<double, int>> ranked;
    ranked.reserve(static_cast<std::size_t>(V));
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        const double deviation =
            r >= 0 ? std::fabs(x[static_cast<std::size_t>(r)] - avg_r) : 0.0;
        double z_mass = 0.0;
        double imbalance = 0.0;
        for (int k = 0; k < static_cast<int>(state.z_cols.size()); ++k) {
            const int z = safeCol(state.z_cols, k, i);
            const double zv = safeVal(z);
            z_mass += std::min(zv, std::fabs(1.0 - zv));
            const int p = safeCol(state.p_cols, k, i);
            const int d = safeCol(state.d_cols, k, i);
            imbalance += std::fabs(safeVal(p) - safeVal(d));
        }
        const double weight = (i < static_cast<int>(state.station_weight.size()))
            ? std::max(0.0, state.station_weight[static_cast<std::size_t>(i)])
            : 0.0;
        const double target = (i < static_cast<int>(state.station_target.size()))
            ? static_cast<double>(std::max(1, state.station_target[static_cast<std::size_t>(i)]))
            : 1.0;
        double score = deviation;
        if (state.subset_cross_h_separation_profile == "fractional") {
            score = z_mass + 0.05 * deviation + 0.01 * imbalance;
        } else if (state.subset_cross_h_separation_profile == "target-weighted") {
            score = deviation * (1.0 + weight / target) + 0.01 * imbalance;
        } else if (state.subset_cross_h_separation_profile == "dominant-bucket") {
            const double capacity_tight =
                state.station_capacity.size() > static_cast<std::size_t>(i)
                    ? 1.0 / static_cast<double>(std::max(1, state.station_capacity[static_cast<std::size_t>(i)]))
                    : 0.0;
            score = 2.0 * deviation * (1.0 + weight / target) +
                    0.40 * z_mass + 0.08 * imbalance + capacity_tight;
        } else if (state.subset_cross_h_separation_profile == "hybrid") {
            score = deviation + 0.10 * z_mass + 0.02 * imbalance +
                    0.05 * deviation * (1.0 + weight / target);
        } else {
            score = deviation + 0.01 * imbalance;
        }
        ranked.push_back({score, i});
    }
    std::sort(ranked.begin(), ranked.end(),
              [](const auto& a, const auto& b) {
                  if (a.first != b.first) return a.first > b.first;
                  return a.second < b.second;
              });
    const int candidate_count = std::min(V, 12);
    std::vector<int> pool;
    pool.reserve(static_cast<std::size_t>(candidate_count));
    for (int i = 0; i < candidate_count; ++i) {
        pool.push_back(ranked[static_cast<std::size_t>(i)].second);
    }
    std::sort(pool.begin(), pool.end());

    constexpr double tol = 1e-6;
    auto addSubsetRow = [&](const std::vector<int>& subset, int sign) {
        if (state.subset_cross_h_centering_cuts_added.load() >= max_cuts) return;
        state.subset_cross_h_centering_candidates.fetch_add(1);
        std::set<int> in_subset(subset.begin(), subset.end());
        std::map<int, double> term_map;
        auto addTerm = [&](int col, double coef) {
            if (col < 0 || std::fabs(coef) <= 1e-12) return;
            term_map[col] += coef;
            if (std::fabs(term_map[col]) <= 1e-12) term_map.erase(col);
        };
        double lhs = 0.0;
        if (sign > 0) {
            for (int i : subset) {
                const int r = state.r_cols[static_cast<std::size_t>(i)];
                lhs += static_cast<double>(V) * safeVal(r);
                addTerm(r, static_cast<double>(V));
            }
            for (int j = 1; j <= V; ++j) {
                const int r = state.r_cols[static_cast<std::size_t>(j)];
                lhs -= static_cast<double>(subset.size()) * safeVal(r);
                addTerm(r, -static_cast<double>(subset.size()));
            }
        } else {
            for (int j = 1; j <= V; ++j) {
                const int r = state.r_cols[static_cast<std::size_t>(j)];
                lhs += static_cast<double>(subset.size()) * safeVal(r);
                addTerm(r, static_cast<double>(subset.size()));
            }
            for (int i : subset) {
                const int r = state.r_cols[static_cast<std::size_t>(i)];
                lhs -= static_cast<double>(V) * safeVal(r);
                addTerm(r, -static_cast<double>(V));
            }
        }
        for (int i : subset) {
            for (int j = 1; j <= V; ++j) {
                if (in_subset.count(j)) continue;
                const int h = hCol(i, j);
                if (h < 0) return;
                lhs -= safeVal(h);
                addTerm(h, -1.0);
            }
        }
        if (lhs <= tol) return;
        state.subset_cross_h_centering_violations.fetch_add(1);
        atomicMax(state.subset_cross_h_centering_max_violation, lhs);
        std::ostringstream key;
        key << sign;
        for (int i : subset) key << ":" << i;
        {
            std::lock_guard<std::mutex> guard(state.subset_cross_h_centering_mutex);
            if (!state.subset_cross_h_centering_cut_keys.insert(key.str()).second) {
                return;
            }
        }
        std::vector<std::pair<int, double>> terms;
        terms.reserve(term_map.size());
        for (const auto& kv : term_map) terms.push_back(kv);
        if (addOneUserCut(state, context, terms, 'L', 0.0)) {
            state.subset_cross_h_centering_cuts_added.fetch_add(1);
        }
    };
    auto testSubset = [&](const std::vector<int>& subset) {
        addSubsetRow(subset, 1);
        addSubsetRow(subset, -1);
    };
    for (int a = 0; a < static_cast<int>(pool.size()); ++a) {
        testSubset({pool[static_cast<std::size_t>(a)]});
    }
    if (max_size >= 2) {
        for (int a = 0; a < static_cast<int>(pool.size()); ++a) {
            for (int b = a + 1; b < static_cast<int>(pool.size()); ++b) {
                testSubset({pool[static_cast<std::size_t>(a)],
                            pool[static_cast<std::size_t>(b)]});
            }
        }
    }
    if (max_size >= 3) {
        for (int a = 0; a < static_cast<int>(pool.size()); ++a) {
            for (int b = a + 1; b < static_cast<int>(pool.size()); ++b) {
                for (int c = b + 1; c < static_cast<int>(pool.size()); ++c) {
                    testSubset({pool[static_cast<std::size_t>(a)],
                                pool[static_cast<std::size_t>(b)],
                                pool[static_cast<std::size_t>(c)]});
                }
            }
        }
    }
    if (max_size >= 4) {
        for (int a = 0; a < static_cast<int>(pool.size()); ++a) {
            for (int b = a + 1; b < static_cast<int>(pool.size()); ++b) {
                for (int c = b + 1; c < static_cast<int>(pool.size()); ++c) {
                    for (int d = c + 1; d < static_cast<int>(pool.size()); ++d) {
                        testSubset({pool[static_cast<std::size_t>(a)],
                                    pool[static_cast<std::size_t>(b)],
                                    pool[static_cast<std::size_t>(c)],
                                    pool[static_cast<std::size_t>(d)]});
                    }
                }
            }
        }
    }
}

void separateLocalQCentering(CallbackState& state,
                             CPXCALLBACKCONTEXTptr context) {
    if (!state.enable_local_q_centering || state.ncols <= 0 ||
        state.q_l1_cols.size() <= 1 || state.h_cols.size() <= 1) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = std::min(static_cast<int>(state.q_l1_cols.size()),
                           static_cast<int>(state.h_cols.size())) - 1;
    if (V <= 1) return;
    auto hCol = [&](int a, int b) -> int {
        if (a > b) std::swap(a, b);
        if (a < 0 || b < 0 ||
            a >= static_cast<int>(state.h_cols.size()) ||
            b >= static_cast<int>(state.h_cols[static_cast<std::size_t>(a)].size())) {
            return -1;
        }
        return state.h_cols[static_cast<std::size_t>(a)][static_cast<std::size_t>(b)];
    };
    constexpr double tol = 1e-6;
    for (int i = 1; i <= V; ++i) {
        const int q = state.q_l1_cols[static_cast<std::size_t>(i)];
        if (q < 0) continue;
        std::map<int, double> term_map;
        term_map[q] = static_cast<double>(V);
        double lhs = static_cast<double>(V) * x[static_cast<std::size_t>(q)];
        for (int j = 1; j <= V; ++j) {
            if (j == i) continue;
            const int h = hCol(i, j);
            if (h < 0) {
                term_map.clear();
                break;
            }
            lhs -= x[static_cast<std::size_t>(h)];
            term_map[h] -= 1.0;
        }
        if (term_map.empty() || lhs <= tol) continue;
        state.local_q_centering_violations.fetch_add(1);
        atomicMax(state.local_q_centering_max_violation, lhs);
        std::ostringstream key;
        key << i;
        {
            std::lock_guard<std::mutex> guard(state.local_q_centering_mutex);
            if (!state.local_q_centering_cut_keys.insert(key.str()).second) {
                continue;
            }
        }
        std::vector<std::pair<int, double>> terms;
        terms.reserve(term_map.size());
        for (const auto& kv : term_map) terms.push_back(kv);
        if (addOneUserCut(state, context, terms, 'L', 0.0)) {
            state.local_q_centering_cuts_added.fetch_add(1);
        }
    }
}

void separateVariableSCentering(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.r_cols.size() <= 1 ||
        state.r_min_col < 0 || state.r_max_col < 0 ||
        state.gamma_U < -1e-12) {
        return;
    }
    if (state.variable_s_centering_cuts_added.load() > 0) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    if (V <= 1) return;
    std::vector<std::pair<int, double>> terms;
    terms.reserve(static_cast<std::size_t>(V + 2));
    terms.push_back({state.r_max_col, static_cast<double>(V - 1)});
    terms.push_back({state.r_min_col, -static_cast<double>(V - 1)});
    double lhs =
        static_cast<double>(V - 1) * x[static_cast<std::size_t>(state.r_max_col)] -
        static_cast<double>(V - 1) * x[static_cast<std::size_t>(state.r_min_col)];
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r < 0) continue;
        const double coef = -static_cast<double>(V) * state.gamma_U;
        terms.push_back({r, coef});
        lhs += coef * x[static_cast<std::size_t>(r)];
    }
    constexpr double tol = 1e-6;
    if (lhs > tol) {
        state.variable_s_centering_violations.fetch_add(1);
        if (addOneUserCut(state, context, terms, 'L', 0.0)) {
            state.variable_s_centering_cuts_added.fetch_add(1);
        }
    }
}

void separateSubsetInventoryImbalance(CallbackState& state,
                                      CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.y_cols.size() <= 1 ||
        state.station_initial.empty() || state.station_capacity.empty()) {
        return;
    }
    bool expected = false;
    if (!state.subset_inventory_separated.compare_exchange_strong(expected, true)) {
        return;
    }
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    constexpr double tol = 1e-6;
    const int station_count = std::min({
        static_cast<int>(state.y_cols.size()),
        static_cast<int>(state.station_initial.size()),
        static_cast<int>(state.station_capacity.size())
    });
    const int V = station_count - 1;
    if (V <= 0) return;

    auto movementBudgetForVehicle = [&](int k) {
        if (k < 0 || k >= static_cast<int>(state.vehicle_capacity.size())) return 0;
        if (state.handling_unit <= 1e-12 || state.total_time_limit <= 0.0) {
            return std::max(0, state.vehicle_capacity[static_cast<std::size_t>(k)]);
        }
        const int handling_budget = static_cast<int>(
            std::floor(state.total_time_limit / state.handling_unit + 1e-9));
        return std::max(0, std::min(
            state.vehicle_capacity[static_cast<std::size_t>(k)],
            handling_budget));
    };

    auto trySubset = [&](const std::vector<int>& subset) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        int initial_sum = 0;
        int room_sum = 0;
        int bikes_sum = 0;
        double y_value = 0.0;
        std::vector<std::pair<int, double>> upper_terms;
        std::vector<std::pair<int, double>> lower_terms;
        upper_terms.reserve(subset.size());
        lower_terms.reserve(subset.size());
        for (int i : subset) {
            if (i <= 0 || i >= station_count) return;
            const int y = state.y_cols[static_cast<std::size_t>(i)];
            if (y < 0) return;
            initial_sum += state.station_initial[static_cast<std::size_t>(i)];
            room_sum += state.station_capacity[static_cast<std::size_t>(i)] -
                state.station_initial[static_cast<std::size_t>(i)];
            bikes_sum += state.station_initial[static_cast<std::size_t>(i)];
            y_value += x[static_cast<std::size_t>(y)];
            upper_terms.push_back({y, 1.0});
            lower_terms.push_back({y, -1.0});
        }
        double plus = 0.0;
        double minus = 0.0;
        for (int k = 0; k < static_cast<int>(state.vehicle_capacity.size()); ++k) {
            const int move_budget = movementBudgetForVehicle(k);
            plus += std::min({state.vehicle_capacity[static_cast<std::size_t>(k)],
                              std::max(0, room_sum),
                              move_budget});
            minus += std::min({state.vehicle_capacity[static_cast<std::size_t>(k)],
                               std::max(0, bikes_sum),
                               move_budget});
        }
        state.subset_inventory_imbalance_candidates.fetch_add(2);
        const double upper_rhs = static_cast<double>(initial_sum) + plus;
        if (y_value > upper_rhs + tol) {
            state.subset_inventory_imbalance_violations.fetch_add(1);
            if (addOneUserCut(state, context, upper_terms, 'L', upper_rhs)) {
                state.subset_inventory_imbalance_cuts_added.fetch_add(1);
            }
        }
        const double lower_lhs = -y_value;
        const double lower_rhs = -static_cast<double>(initial_sum) + minus;
        if (lower_lhs > lower_rhs + tol) {
            state.subset_inventory_imbalance_violations.fetch_add(1);
            if (addOneUserCut(state, context, lower_terms, 'L', lower_rhs)) {
                state.subset_inventory_imbalance_cuts_added.fetch_add(1);
            }
        }
    };

    for (int a = 1; a <= V; ++a) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        trySubset({a});
    }
    for (int a = 1; a <= V; ++a) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        for (int b = a + 1; b <= V; ++b) trySubset({a, b});
    }
    for (int a = 1; a <= V; ++a) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        for (int b = a + 1; b <= V; ++b) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            for (int c = b + 1; c <= V; ++c) trySubset({a, b, c});
        }
    }
}

void separateTransferCutset(CallbackState& state,
                            CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.p_cols.empty() || state.d_cols.empty()) return;
    bool expected = false;
    if (!state.transfer_cutset_separated.compare_exchange_strong(expected, true)) {
        return;
    }
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    constexpr double tol = 1e-6;
    const int vehicle_count =
        std::min(static_cast<int>(state.p_cols.size()),
                 static_cast<int>(state.d_cols.size()));
    const int station_count = vehicle_count > 0
        ? std::min(static_cast<int>(state.p_cols.front().size()),
                   static_cast<int>(state.d_cols.front().size()))
        : 0;
    auto trySubset = [&](int k, const std::vector<int>& subset,
                         const std::vector<std::pair<int, double>>& pickup_terms,
                         double total_pickup) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        state.transfer_cutset_candidates.fetch_add(1);
        std::vector<std::pair<int, double>> terms = pickup_terms;
        double lhs = -total_pickup;
        bool has_drop = false;
        for (int j : subset) {
            const int d = safeCol(state.d_cols, k, j);
            if (d < 0) return;
            terms.push_back({d, 1.0});
            lhs += x[static_cast<std::size_t>(d)];
            has_drop = true;
        }
        if (!has_drop) return;
        if (lhs > tol) {
            state.transfer_cutset_violations.fetch_add(1);
            if (addOneUserCut(state, context, terms, 'L', 0.0)) {
                state.transfer_cutset_cuts_added.fetch_add(1);
            }
        }
    };
    for (int k = 0; k < vehicle_count; ++k) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        std::vector<std::pair<int, double>> pickup_terms;
        double total_pickup = 0.0;
        for (int i = 1; i < station_count; ++i) {
            const int p = safeCol(state.p_cols, k, i);
            if (p < 0) continue;
            pickup_terms.push_back({p, -1.0});
            total_pickup += x[static_cast<std::size_t>(p)];
        }
        if (pickup_terms.empty()) continue;
        for (int i = 1; i < station_count; ++i) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            trySubset(k, {i}, pickup_terms, total_pickup);
        }
        for (int i = 1; i < station_count; ++i) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            for (int j = i + 1; j < station_count; ++j) {
                trySubset(k, {i, j}, pickup_terms, total_pickup);
            }
        }
        for (int i = 1; i < station_count; ++i) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            for (int j = i + 1; j < station_count; ++j) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                for (int h = j + 1; h < station_count; ++h) {
                    trySubset(k, {i, j, h}, pickup_terms, total_pickup);
                }
            }
        }
    }
}

void separateSupportDurationCover(CallbackState& state,
                                  CPXCALLBACKCONTEXTptr context) {
    if (state.support_duration_cover_mode == "off") {
        return;
    }
    if (state.ncols <= 0 || state.z_cols.empty() ||
        state.distance_matrix.empty() || state.node_count <= 0 ||
        state.total_time_limit <= 0.0 || state.handling_unit <= 0.0) {
        return;
    }
    bool expected = false;
    if (!state.support_duration_separated.compare_exchange_strong(expected, true)) {
        return;
    }
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetrelaxationpoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    constexpr double tol = 1e-6;
    constexpr int max_fractional_support = 16;
    const int vehicle_count = static_cast<int>(state.z_cols.size());
    const int station_count = std::min(
        state.node_count,
        vehicle_count > 0 ? static_cast<int>(state.z_cols.front().size()) : 0);

    auto addCover = [&](int k, const std::vector<int>& subset, int rhs) {
        std::vector<std::pair<int, double>> terms;
        terms.reserve(subset.size());
        for (int i : subset) {
            const int z = safeCol(state.z_cols, k, i);
            if (z < 0) return false;
            terms.push_back({z, 1.0});
        }
        return addOneUserCut(state, context, terms, 'L', static_cast<double>(rhs));
    };
    auto minHandlingUnits = [](int subset_size) {
        return (subset_size + 1) / 2;
    };
    auto subsetPossiblyFeasible = [&](const std::vector<int>& subset) {
        const double cycle = callbackSubsetCycleLowerBound(state, subset);
        if (!std::isfinite(cycle)) return false;
        const double min_handling =
            static_cast<double>(minHandlingUnits(static_cast<int>(subset.size()))) *
            state.handling_unit;
        return cycle + min_handling <= state.total_time_limit + 1e-9;
    };
    auto maxPossiblyFeasibleCardinality = [&](const std::vector<int>& subset) {
        const int n = static_cast<int>(subset.size());
        int best = 0;
        const int mask_limit = 1 << n;
        for (int mask = 1; mask < mask_limit; ++mask) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return best;
            std::vector<int> child;
            child.reserve(static_cast<std::size_t>(n));
            for (int idx = 0; idx < n; ++idx) {
                if ((mask & (1 << idx)) != 0) {
                    child.push_back(subset[static_cast<std::size_t>(idx)]);
                }
            }
            const int card = static_cast<int>(child.size());
            if (card <= best) continue;
            if (subsetPossiblyFeasible(child)) best = card;
        }
        return best;
    };
    const bool lifted_enabled =
        state.support_duration_cover_mode == "support_cover_lifted";
    auto accountCandidate = [&](int size) {
        if (size == 2) state.support_duration_pair_candidates.fetch_add(1);
        else if (size == 3) state.support_duration_triple_candidates.fetch_add(1);
        else if (size == 4) state.support_duration_quad_candidates.fetch_add(1);
        if (lifted_enabled) state.support_duration_lifted_candidates.fetch_add(1);
    };
    auto accountViolation = [&](int size, bool lifted) {
        if (size == 2) state.support_duration_pair_violations.fetch_add(1);
        else if (size == 3) state.support_duration_triple_violations.fetch_add(1);
        else if (size == 4) state.support_duration_quad_violations.fetch_add(1);
        if (lifted) state.support_duration_lifted_violations.fetch_add(1);
    };
    auto accountCut = [&](int size, bool lifted) {
        if (size == 2) state.support_duration_pair_cuts_added.fetch_add(1);
        else if (size == 3) state.support_duration_triple_cuts_added.fetch_add(1);
        else if (size == 4) state.support_duration_quad_cuts_added.fetch_add(1);
        if (lifted) state.support_duration_lifted_cuts_added.fetch_add(1);
    };
    auto trySupportSubset = [&](int k,
                                const std::vector<int>& subset,
                                double lhs) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        const int size = static_cast<int>(subset.size());
        if (size < 2 || size > 4) return;
        accountCandidate(size);
        if (subsetPossiblyFeasible(subset)) return;
        const int rhs = lifted_enabled
            ? maxPossiblyFeasibleCardinality(subset)
            : size - 1;
        if (rhs >= size) return;
        const bool lifted = lifted_enabled && rhs < size - 1;
        if (lhs > static_cast<double>(rhs) + tol) {
            accountViolation(size, lifted);
            if (addCover(k, subset, rhs)) accountCut(size, lifted);
        }
    };

    for (int k = 0; k < vehicle_count; ++k) {
        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
        std::vector<std::pair<double, int>> support;
        support.reserve(static_cast<std::size_t>(std::max(0, station_count - 1)));
        for (int i = 1; i < station_count; ++i) {
            const int z = safeCol(state.z_cols, k, i);
            if (z < 0) continue;
            const double val = x[static_cast<std::size_t>(z)];
            if (val > tol) support.push_back({val, i});
        }
        std::sort(support.begin(), support.end(),
                  [](const auto& a, const auto& b) {
                      if (std::fabs(a.first - b.first) > 1e-12) return a.first > b.first;
                      return a.second < b.second;
                  });
        if (support.size() > static_cast<std::size_t>(max_fractional_support)) {
            support.resize(static_cast<std::size_t>(max_fractional_support));
        }
        const int n = static_cast<int>(support.size());
        for (int ai = 0; ai < n; ++ai) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            const int a = support[static_cast<std::size_t>(ai)].second;
            const double za = support[static_cast<std::size_t>(ai)].first;
            for (int bi = ai + 1; bi < n; ++bi) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                const int b = support[static_cast<std::size_t>(bi)].second;
                const double lhs = za + support[static_cast<std::size_t>(bi)].first;
                trySupportSubset(k, {a, b}, lhs);
            }
        }
        for (int ai = 0; ai < n; ++ai) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            const int a = support[static_cast<std::size_t>(ai)].second;
            const double za = support[static_cast<std::size_t>(ai)].first;
            for (int bi = ai + 1; bi < n; ++bi) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                const int b = support[static_cast<std::size_t>(bi)].second;
                const double zb = support[static_cast<std::size_t>(bi)].first;
                for (int ci = bi + 1; ci < n; ++ci) {
                    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                    const int c = support[static_cast<std::size_t>(ci)].second;
                    const double lhs =
                        za + zb + support[static_cast<std::size_t>(ci)].first;
                    trySupportSubset(k, {a, b, c}, lhs);
                }
            }
        }
        for (int ai = 0; ai < n; ++ai) {
            if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
            const int a = support[static_cast<std::size_t>(ai)].second;
            const double za = support[static_cast<std::size_t>(ai)].first;
            for (int bi = ai + 1; bi < n; ++bi) {
                if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                const int b = support[static_cast<std::size_t>(bi)].second;
                const double zb = support[static_cast<std::size_t>(bi)].first;
                for (int ci = bi + 1; ci < n; ++ci) {
                    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                    const int c = support[static_cast<std::size_t>(ci)].second;
                    const double zc = support[static_cast<std::size_t>(ci)].first;
                    for (int di = ci + 1; di < n; ++di) {
                        if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
                        const int d = support[static_cast<std::size_t>(di)].second;
                        const double lhs =
                            za + zb + zc + support[static_cast<std::size_t>(di)].first;
                        trySupportSubset(k, {a, b, c, d}, lhs);
                    }
                }
            }
        }
    }
}

bool validateCandidateVisitInventory(CallbackState& state,
                                     CPXCALLBACKCONTEXTptr context,
                                     const std::vector<double>& x) {
    if (state.y_cols.empty() || state.z_cols.empty()) return false;
    constexpr double tol = 1e-6;
    const int station_count =
        std::min(static_cast<int>(state.y_cols.size()),
                 static_cast<int>(state.station_initial.size()));
    for (int i = 1; i < station_count; ++i) {
        const int y = state.y_cols[static_cast<std::size_t>(i)];
        if (y < 0) continue;
        const double initial =
            static_cast<double>(state.station_initial[static_cast<std::size_t>(i)]);
        const double capacity =
            static_cast<double>(state.station_capacity[static_cast<std::size_t>(i)]);
        std::vector<std::pair<int, double>> upper_terms;
        std::vector<std::pair<int, double>> lower_terms;
        upper_terms.push_back({y, 1.0});
        lower_terms.push_back({y, -1.0});
        double visit = 0.0;
        for (const std::vector<int>& row : state.z_cols) {
            if (i >= static_cast<int>(row.size())) continue;
            const int z = row[static_cast<std::size_t>(i)];
            if (z < 0) continue;
            visit += x[static_cast<std::size_t>(z)];
            upper_terms.push_back({z, -(capacity - initial)});
            lower_terms.push_back({z, -initial});
        }
        const double upper_lhs =
            x[static_cast<std::size_t>(y)] - (capacity - initial) * visit;
        if (upper_lhs > initial + tol &&
            rejectCandidateWithLazyRow(state, context, upper_terms, 'L', initial)) {
            ++state.lazy_visit_inventory_rejections;
            return true;
        }
        const double lower_lhs =
            -x[static_cast<std::size_t>(y)] - initial * visit;
        if (lower_lhs > -initial + tol &&
            rejectCandidateWithLazyRow(state, context, lower_terms, 'L', -initial)) {
            ++state.lazy_visit_inventory_rejections;
            return true;
        }
    }
    return false;
}

bool validateCandidateGiniSubsetEnvelope(CallbackState& state,
                                         CPXCALLBACKCONTEXTptr context,
                                         const std::vector<double>& x) {
    if (state.r_cols.size() <= 1 || state.gamma_U < -1e-12) return false;
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    double sum_r = 0.0;
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r >= 0) sum_r += x[static_cast<std::size_t>(r)];
    }
    if (sum_r <= 1e-12) return false;
    auto rejectSubset = [&](const std::vector<int>& subset, int sign) {
        const int a = static_cast<int>(subset.size());
        std::vector<std::pair<int, double>> terms;
        terms.reserve(static_cast<std::size_t>(V));
        double lhs = 0.0;
        for (int i = 1; i <= V; ++i) {
            const int r = state.r_cols[static_cast<std::size_t>(i)];
            if (r < 0) continue;
            double coef = sign > 0
                ? (-static_cast<double>(a) - static_cast<double>(V) * state.gamma_U)
                : ( static_cast<double>(a) - static_cast<double>(V) * state.gamma_U);
            if (std::find(subset.begin(), subset.end(), i) != subset.end()) {
                coef += sign > 0 ? static_cast<double>(V) : -static_cast<double>(V);
            }
            lhs += coef * x[static_cast<std::size_t>(r)];
            terms.push_back({r, coef});
        }
        constexpr double tol = 1e-6;
        if (lhs > tol &&
            rejectCandidateWithLazyRow(state, context, terms, 'L', 0.0)) {
            ++state.lazy_gini_subset_envelope_rejections;
            return true;
        }
        return false;
    };
    for (int i = 1; i <= V; ++i) {
        if (rejectSubset({i}, 1)) return true;
        if (rejectSubset({i}, -1)) return true;
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            if (rejectSubset({i, j}, 1)) return true;
            if (rejectSubset({i, j}, -1)) return true;
        }
    }
    return false;
}

bool validateCandidateLowGiniL1(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context,
                                const std::vector<double>& x) {
    if (state.r_cols.size() <= 1 || state.q_l1_cols.size() <= 1 ||
        state.gamma_U < -1e-12) {
        return false;
    }
    const int V = std::min(static_cast<int>(state.r_cols.size()),
                           static_cast<int>(state.q_l1_cols.size())) - 1;
    std::vector<std::pair<int, double>> terms;
    terms.reserve(static_cast<std::size_t>(2 * V));
    double lhs = 0.0;
    for (int i = 1; i <= V; ++i) {
        const int q = state.q_l1_cols[static_cast<std::size_t>(i)];
        if (q >= 0) {
            lhs += x[static_cast<std::size_t>(q)];
            terms.push_back({q, 1.0});
        }
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r >= 0) {
            const double coef = -2.0 * state.gamma_U;
            lhs += coef * x[static_cast<std::size_t>(r)];
            terms.push_back({r, coef});
        }
    }
    constexpr double tol = 1e-6;
    if (lhs > tol &&
        rejectCandidateWithLazyRow(state, context, terms, 'L', 0.0)) {
        ++state.lazy_low_gini_l1_rejections;
        return true;
    }
    return false;
}

bool validateCandidateVariableSCentering(CallbackState& state,
                                         CPXCALLBACKCONTEXTptr context,
                                         const std::vector<double>& x) {
    if (state.r_cols.size() <= 1 || state.r_min_col < 0 ||
        state.r_max_col < 0 || state.gamma_U < -1e-12) {
        return false;
    }
    const int V = static_cast<int>(state.r_cols.size()) - 1;
    if (V <= 1) return false;
    std::vector<std::pair<int, double>> terms;
    terms.reserve(static_cast<std::size_t>(V + 2));
    terms.push_back({state.r_max_col, static_cast<double>(V - 1)});
    terms.push_back({state.r_min_col, -static_cast<double>(V - 1)});
    double lhs =
        static_cast<double>(V - 1) * x[static_cast<std::size_t>(state.r_max_col)] -
        static_cast<double>(V - 1) * x[static_cast<std::size_t>(state.r_min_col)];
    for (int i = 1; i <= V; ++i) {
        const int r = state.r_cols[static_cast<std::size_t>(i)];
        if (r < 0) continue;
        const double coef = -static_cast<double>(V) * state.gamma_U;
        terms.push_back({r, coef});
        lhs += coef * x[static_cast<std::size_t>(r)];
    }
    constexpr double tol = 1e-6;
    if (lhs > tol &&
        rejectCandidateWithLazyRow(state, context, terms, 'L', 0.0)) {
        ++state.lazy_variable_s_centering_rejections;
        return true;
    }
    return false;
}

bool validateCandidateSubsetInventoryImbalance(CallbackState& state,
                                               CPXCALLBACKCONTEXTptr context,
                                               const std::vector<double>& x) {
    if (state.y_cols.size() <= 1 || state.station_initial.empty() ||
        state.station_capacity.empty()) {
        return false;
    }
    constexpr double tol = 1e-6;
    const int station_count = std::min({
        static_cast<int>(state.y_cols.size()),
        static_cast<int>(state.station_initial.size()),
        static_cast<int>(state.station_capacity.size())
    });
    const int V = station_count - 1;
    if (V <= 0) return false;

    auto movementBudgetForVehicle = [&](int k) {
        if (k < 0 || k >= static_cast<int>(state.vehicle_capacity.size())) return 0;
        if (state.handling_unit <= 1e-12 || state.total_time_limit <= 0.0) {
            return std::max(0, state.vehicle_capacity[static_cast<std::size_t>(k)]);
        }
        const int handling_budget = static_cast<int>(
            std::floor(state.total_time_limit / state.handling_unit + 1e-9));
        return std::max(0, std::min(
            state.vehicle_capacity[static_cast<std::size_t>(k)],
            handling_budget));
    };

    auto rejectSubset = [&](const std::vector<int>& subset) {
        int initial_sum = 0;
        int room_sum = 0;
        int bikes_sum = 0;
        double y_value = 0.0;
        std::vector<std::pair<int, double>> upper_terms;
        std::vector<std::pair<int, double>> lower_terms;
        for (int i : subset) {
            if (i <= 0 || i >= station_count) return false;
            const int y = state.y_cols[static_cast<std::size_t>(i)];
            if (y < 0) return false;
            initial_sum += state.station_initial[static_cast<std::size_t>(i)];
            room_sum += state.station_capacity[static_cast<std::size_t>(i)] -
                state.station_initial[static_cast<std::size_t>(i)];
            bikes_sum += state.station_initial[static_cast<std::size_t>(i)];
            y_value += x[static_cast<std::size_t>(y)];
            upper_terms.push_back({y, 1.0});
            lower_terms.push_back({y, -1.0});
        }
        double plus = 0.0;
        double minus = 0.0;
        for (int k = 0; k < static_cast<int>(state.vehicle_capacity.size()); ++k) {
            const int move_budget = movementBudgetForVehicle(k);
            plus += std::min({state.vehicle_capacity[static_cast<std::size_t>(k)],
                              std::max(0, room_sum),
                              move_budget});
            minus += std::min({state.vehicle_capacity[static_cast<std::size_t>(k)],
                               std::max(0, bikes_sum),
                               move_budget});
        }
        const double upper_rhs = static_cast<double>(initial_sum) + plus;
        if (y_value > upper_rhs + tol &&
            rejectCandidateWithLazyRow(state, context, upper_terms, 'L', upper_rhs)) {
            ++state.lazy_subset_inventory_imbalance_rejections;
            return true;
        }
        const double lower_lhs = -y_value;
        const double lower_rhs = -static_cast<double>(initial_sum) + minus;
        if (lower_lhs > lower_rhs + tol &&
            rejectCandidateWithLazyRow(state, context, lower_terms, 'L', lower_rhs)) {
            ++state.lazy_subset_inventory_imbalance_rejections;
            return true;
        }
        return false;
    };

    for (int a = 1; a <= V; ++a) {
        if (rejectSubset({a})) return true;
    }
    for (int a = 1; a <= V; ++a) {
        for (int b = a + 1; b <= V; ++b) {
            if (rejectSubset({a, b})) return true;
        }
    }
    for (int a = 1; a <= V; ++a) {
        for (int b = a + 1; b <= V; ++b) {
            for (int c = b + 1; c <= V; ++c) {
                if (rejectSubset({a, b, c})) return true;
            }
        }
    }
    return false;
}

enum class CandidateRouteProjectionStatus {
    Verified,
    Rejected,
    UnsupportedMismatch,
};

int safeCol(const std::vector<std::vector<int>>& cols, int k, int i) {
    if (k < 0 || i < 0 || k >= static_cast<int>(cols.size())) return -1;
    if (i >= static_cast<int>(cols[static_cast<std::size_t>(k)].size())) return -1;
    return cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)];
}

int safeXCol(const CallbackState& state, int k, int i, int j) {
    if (k < 0 || i < 0 || j < 0 ||
        k >= static_cast<int>(state.x_cols.size())) {
        return -1;
    }
    const auto& mat = state.x_cols[static_cast<std::size_t>(k)];
    if (i >= static_cast<int>(mat.size())) return -1;
    if (j >= static_cast<int>(mat[static_cast<std::size_t>(i)].size())) return -1;
    return mat[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];
}

double safeDist(const CallbackState& state, int i, int j) {
    if (i < 0 || j < 0 || state.node_count <= 0 ||
        i >= state.node_count || j >= state.node_count) {
        return 0.0;
    }
    const std::size_t idx = static_cast<std::size_t>(i * state.node_count + j);
    if (idx >= state.distance_matrix.size()) return 0.0;
    return state.distance_matrix[idx];
}

bool rejectCandidateWithRouteProjectionRow(
    CallbackState& state,
    CPXCALLBACKCONTEXTptr context,
    const std::vector<std::pair<int, double>>& terms,
    char sense,
    double rhs,
    std::atomic<long long>& family_counter) {
    if (rejectCandidateWithLazyRow(state, context, terms, sense, rhs)) {
        ++state.candidate_route_projection_rejections;
        ++family_counter;
        return true;
    }
    return false;
}

CandidateRouteProjectionStatus validateCandidateRouteProjection(
    CallbackState& state,
    CPXCALLBACKCONTEXTptr context,
    const std::vector<double>& x) {
    const int V = static_cast<int>(state.station_initial.size()) - 1;
    const int M = static_cast<int>(state.vehicle_capacity.size());
    if (V <= 0 || M <= 0 || state.node_count != V + 1 ||
        state.x_cols.empty() || state.z_cols.empty() ||
        state.p_cols.empty() || state.d_cols.empty() ||
        state.y_cols.empty()) {
        return CandidateRouteProjectionStatus::Verified;
    }

    ++state.candidate_route_projection_checks;
    constexpr double tol = 1e-6;

    for (int i = 1; i <= V; ++i) {
        double visit_sum = 0.0;
        std::vector<std::pair<int, double>> terms;
        for (int k = 0; k < M; ++k) {
            const int z = safeCol(state.z_cols, k, i);
            if (z >= 0) {
                visit_sum += x[static_cast<std::size_t>(z)];
                terms.push_back({z, 1.0});
            }
        }
        if (visit_sum > 1.0 + tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, terms, 'L', 1.0,
                state.candidate_route_projection_station_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }
    }

    for (int k = 0; k < M; ++k) {
        std::vector<std::pair<int, double>> start_terms;
        std::vector<std::pair<int, double>> start_end_terms;
        double start = 0.0;
        double start_end = 0.0;
        for (int j = 1; j <= V; ++j) {
            const int x0j = safeXCol(state, k, 0, j);
            const int xj0 = safeXCol(state, k, j, 0);
            if (x0j >= 0) {
                start += x[static_cast<std::size_t>(x0j)];
                start_end += x[static_cast<std::size_t>(x0j)];
                start_terms.push_back({x0j, 1.0});
                start_end_terms.push_back({x0j, 1.0});
            }
            if (xj0 >= 0) {
                start_end -= x[static_cast<std::size_t>(xj0)];
                start_end_terms.push_back({xj0, -1.0});
            }
        }
        if (std::fabs(start_end) > tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, start_end_terms, 'E', 0.0,
                state.candidate_route_projection_flow_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }
        if (start > 1.0 + tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, start_terms, 'L', 1.0,
                state.candidate_route_projection_flow_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }

        double duration = 0.0;
        std::vector<std::pair<int, double>> duration_terms;
        for (int i = 0; i <= V; ++i) {
            for (int j = 0; j <= V; ++j) {
                if (i == j) continue;
                const int arc = safeXCol(state, k, i, j);
                if (arc < 0) continue;
                const double d = safeDist(state, i, j);
                duration += d * x[static_cast<std::size_t>(arc)];
                duration_terms.push_back({arc, d});
            }
        }
        double final_load = 0.0;
        std::vector<std::pair<int, double>> final_load_terms;
        for (int i = 1; i <= V; ++i) {
            const int p = safeCol(state.p_cols, k, i);
            const int d = safeCol(state.d_cols, k, i);
            const int z = safeCol(state.z_cols, k, i);
            if (p >= 0) {
                duration += state.handling_unit * x[static_cast<std::size_t>(p)];
                duration_terms.push_back({p, state.handling_unit});
                final_load += x[static_cast<std::size_t>(p)];
                final_load_terms.push_back({p, 1.0});
            }
            if (d >= 0) {
                final_load -= x[static_cast<std::size_t>(d)];
                final_load_terms.push_back({d, -1.0});
            }
            if (z >= 0) {
                const int pmax = std::min(
                    state.station_initial[static_cast<std::size_t>(i)],
                    state.vehicle_capacity[static_cast<std::size_t>(k)]);
                const int dmax = std::min(
                    state.station_capacity[static_cast<std::size_t>(i)] -
                        state.station_initial[static_cast<std::size_t>(i)],
                    state.vehicle_capacity[static_cast<std::size_t>(k)]);
                if (p >= 0 && x[static_cast<std::size_t>(p)] >
                        pmax * x[static_cast<std::size_t>(z)] + tol) {
                    if (rejectCandidateWithRouteProjectionRow(
                            state, context, {{p, 1.0}, {z, -static_cast<double>(pmax)}},
                            'L', 0.0,
                            state.candidate_route_projection_service_rejections)) {
                        return CandidateRouteProjectionStatus::Rejected;
                    }
                }
                if (d >= 0 && x[static_cast<std::size_t>(d)] >
                        dmax * x[static_cast<std::size_t>(z)] + tol) {
                    if (rejectCandidateWithRouteProjectionRow(
                            state, context, {{d, 1.0}, {z, -static_cast<double>(dmax)}},
                            'L', 0.0,
                            state.candidate_route_projection_service_rejections)) {
                        return CandidateRouteProjectionStatus::Rejected;
                    }
                }
                const double service = (p >= 0 ? x[static_cast<std::size_t>(p)] : 0.0) +
                    (d >= 0 ? x[static_cast<std::size_t>(d)] : 0.0) -
                    x[static_cast<std::size_t>(z)];
                if (service < -tol) {
                    std::vector<std::pair<int, double>> service_terms;
                    if (p >= 0) service_terms.push_back({p, 1.0});
                    if (d >= 0) service_terms.push_back({d, 1.0});
                    service_terms.push_back({z, -1.0});
                    if (rejectCandidateWithRouteProjectionRow(
                            state, context, service_terms, 'G', 0.0,
                            state.candidate_route_projection_service_rejections)) {
                        return CandidateRouteProjectionStatus::Rejected;
                    }
                }
            }

            double in_flow = 0.0;
            double out_flow = 0.0;
            std::vector<std::pair<int, double>> in_terms;
            std::vector<std::pair<int, double>> out_terms;
            for (int j = 0; j <= V; ++j) {
                if (j == i) continue;
                const int xin = safeXCol(state, k, j, i);
                const int xout = safeXCol(state, k, i, j);
                if (xin >= 0) {
                    in_flow += x[static_cast<std::size_t>(xin)];
                    in_terms.push_back({xin, 1.0});
                }
                if (xout >= 0) {
                    out_flow += x[static_cast<std::size_t>(xout)];
                    out_terms.push_back({xout, 1.0});
                }
            }
            if (z >= 0) {
                in_flow -= x[static_cast<std::size_t>(z)];
                out_flow -= x[static_cast<std::size_t>(z)];
                in_terms.push_back({z, -1.0});
                out_terms.push_back({z, -1.0});
            }
            if (std::fabs(in_flow) > tol &&
                rejectCandidateWithRouteProjectionRow(
                    state, context, in_terms, 'E', 0.0,
                    state.candidate_route_projection_flow_rejections)) {
                return CandidateRouteProjectionStatus::Rejected;
            }
            if (std::fabs(out_flow) > tol &&
                rejectCandidateWithRouteProjectionRow(
                    state, context, out_terms, 'E', 0.0,
                    state.candidate_route_projection_flow_rejections)) {
                return CandidateRouteProjectionStatus::Rejected;
            }
        }
        if (duration > state.total_time_limit + tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, duration_terms, 'L', state.total_time_limit,
                state.candidate_route_projection_duration_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }
        if (final_load < -tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, final_load_terms, 'G', 0.0,
                state.candidate_route_projection_service_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }
    }

    for (int i = 1; i <= V; ++i) {
        const int y = i < static_cast<int>(state.y_cols.size())
            ? state.y_cols[static_cast<std::size_t>(i)] : -1;
        if (y < 0) continue;
        double balance = x[static_cast<std::size_t>(y)];
        std::vector<std::pair<int, double>> terms{{y, 1.0}};
        for (int k = 0; k < M; ++k) {
            const int p = safeCol(state.p_cols, k, i);
            const int d = safeCol(state.d_cols, k, i);
            if (p >= 0) {
                balance += x[static_cast<std::size_t>(p)];
                terms.push_back({p, 1.0});
            }
            if (d >= 0) {
                balance -= x[static_cast<std::size_t>(d)];
                terms.push_back({d, -1.0});
            }
        }
        const double rhs =
            static_cast<double>(state.station_initial[static_cast<std::size_t>(i)]);
        if (std::fabs(balance - rhs) > tol &&
            rejectCandidateWithRouteProjectionRow(
                state, context, terms, 'E', rhs,
                state.candidate_route_projection_inventory_rejections)) {
            return CandidateRouteProjectionStatus::Rejected;
        }
    }

    for (int k = 0; k < M; ++k) {
        int current = 0;
        double load = 0.0;
        std::set<int> visited;
        for (int step = 0; step <= V; ++step) {
            int next = -1;
            int outgoing = 0;
            for (int j = 0; j <= V; ++j) {
                if (j == current) continue;
                const int arc = safeXCol(state, k, current, j);
                if (arc >= 0 && x[static_cast<std::size_t>(arc)] > 0.5) {
                    next = j;
                    ++outgoing;
                }
            }
            if (outgoing == 0 || next == 0) break;
            if (outgoing > 1 || !visited.insert(next).second) {
                ++state.candidate_route_projection_unsupported_mismatches;
                ++state.candidate_route_projection_load_mismatches;
                return CandidateRouteProjectionStatus::UnsupportedMismatch;
            }
            const int p = safeCol(state.p_cols, k, next);
            const int d = safeCol(state.d_cols, k, next);
            const double pickup = p >= 0 ? x[static_cast<std::size_t>(p)] : 0.0;
            const double drop = d >= 0 ? x[static_cast<std::size_t>(d)] : 0.0;
            load += pickup;
            if (load > state.vehicle_capacity[static_cast<std::size_t>(k)] + tol ||
                load + tol < drop) {
                ++state.candidate_route_projection_unsupported_mismatches;
                ++state.candidate_route_projection_load_mismatches;
                return CandidateRouteProjectionStatus::UnsupportedMismatch;
            }
            load -= drop;
            current = next;
        }
        for (int i = 1; i <= V; ++i) {
            const int z = safeCol(state.z_cols, k, i);
            if (z >= 0 && x[static_cast<std::size_t>(z)] > 0.5 &&
                !visited.count(i)) {
                ++state.candidate_route_projection_unsupported_mismatches;
                ++state.candidate_route_projection_load_mismatches;
                return CandidateRouteProjectionStatus::UnsupportedMismatch;
            }
        }
    }

    ++state.candidate_route_projection_verified;
    return CandidateRouteProjectionStatus::Verified;
}

enum class CandidateProjectionStatus {
    Verified,
    Rejected,
    UnsupportedMismatch,
};

CandidateProjectionStatus validateCandidateProjection(CallbackState& state,
                                                      CPXCALLBACKCONTEXTptr context,
                                                      const std::vector<double>& x) {
    const int station_count = std::min({
        static_cast<int>(state.y_cols.size()),
        static_cast<int>(state.r_cols.size()),
        static_cast<int>(state.e_cols.size()),
        static_cast<int>(state.station_target.size()),
        static_cast<int>(state.station_weight.size()),
    });
    if (station_count <= 1) return CandidateProjectionStatus::Verified;

    ++state.candidate_projection_checks;
    constexpr double tol = 1e-6;
    std::vector<double> ratio(static_cast<std::size_t>(station_count), 0.0);
    double s = 0.0;
    double penalty = 0.0;
    double variable_penalty = 0.0;
    for (int i = 1; i < station_count; ++i) {
        const int y_col = state.y_cols[static_cast<std::size_t>(i)];
        const int r_col = state.r_cols[static_cast<std::size_t>(i)];
        const int e_col = state.e_cols[static_cast<std::size_t>(i)];
        const int target = state.station_target[static_cast<std::size_t>(i)];
        if (y_col < 0 || r_col < 0 || e_col < 0 || target <= 0) {
            continue;
        }
        const double y = x[static_cast<std::size_t>(y_col)];
        const double r_model = x[static_cast<std::size_t>(r_col)];
        const double e_model = x[static_cast<std::size_t>(e_col)];
        const double r_projected = y / static_cast<double>(target);
        ratio[static_cast<std::size_t>(i)] = r_projected;
        s += r_projected;
        const double e_projected = std::fabs(r_projected - 1.0);
        const double weight = state.station_weight[static_cast<std::size_t>(i)];
        penalty += weight * e_projected;
        variable_penalty += weight * e_model;

        const double ratio_delta = r_model - r_projected;
        if (ratio_delta > tol) {
            if (rejectCandidateWithLazyRow(
                    state, context, {{r_col, 1.0}, {y_col, -1.0 / target}},
                    'L', 0.0)) {
                ++state.candidate_projection_rejections;
                ++state.candidate_projection_ratio_rejections;
                return CandidateProjectionStatus::Rejected;
            }
        } else if (ratio_delta < -tol) {
            if (rejectCandidateWithLazyRow(
                    state, context, {{r_col, 1.0}, {y_col, -1.0 / target}},
                    'G', 0.0)) {
                ++state.candidate_projection_rejections;
                ++state.candidate_projection_ratio_rejections;
                return CandidateProjectionStatus::Rejected;
            }
        }

        const double e_from_model_ratio = std::fabs(r_model - 1.0);
        if (e_model + tol < e_from_model_ratio) {
            const bool high = r_model >= 1.0;
            if (rejectCandidateWithLazyRow(
                    state, context,
                    high
                        ? std::vector<std::pair<int, double>>{{e_col, 1.0}, {r_col, -1.0}}
                        : std::vector<std::pair<int, double>>{{e_col, 1.0}, {r_col, 1.0}},
                    'G',
                    high ? -1.0 : 1.0)) {
                ++state.candidate_projection_rejections;
                ++state.candidate_projection_penalty_rejections;
                return CandidateProjectionStatus::Rejected;
            }
        }
    }
    if (s <= 1e-12) {
        ++state.candidate_projection_unsupported_mismatches;
        return CandidateProjectionStatus::UnsupportedMismatch;
    }
    double h = 0.0;
    for (int i = 1; i < station_count; ++i) {
        for (int j = i + 1; j < station_count; ++j) {
            h += std::fabs(ratio[static_cast<std::size_t>(i)] -
                           ratio[static_cast<std::size_t>(j)]);
        }
    }
    const double true_g = h / (static_cast<double>(station_count - 1) * s);
    const double g_model = state.g_col >= 0
        ? x[static_cast<std::size_t>(state.g_col)]
        : true_g;
    const double true_objective = true_g + state.lambda * penalty;
    const double model_objective = g_model + state.lambda * variable_penalty;
    const double g_under = true_g - g_model;
    const double obj_under = true_objective - model_objective;
    atomicMax(state.candidate_projection_max_gini_underestimate, g_under);
    atomicMax(state.candidate_projection_max_objective_underestimate, obj_under);

    if (std::isfinite(state.cutoff_value) && model_objective > state.cutoff_value + tol) {
        std::vector<std::pair<int, double>> terms;
        terms.push_back({state.g_col, 1.0});
        for (int i = 1; i < station_count; ++i) {
            const int e_col = state.e_cols[static_cast<std::size_t>(i)];
            if (e_col >= 0) {
                terms.push_back({e_col, state.lambda *
                    state.station_weight[static_cast<std::size_t>(i)]});
            }
        }
        if (rejectCandidateWithLazyRow(state, context, terms, 'L', state.cutoff_value)) {
            ++state.candidate_projection_rejections;
            ++state.candidate_projection_objective_rejections;
            return CandidateProjectionStatus::Rejected;
        }
    }

    if (g_under > 1e-5 || obj_under > 1e-5) {
        ++state.candidate_projection_unsupported_mismatches;
        return CandidateProjectionStatus::UnsupportedMismatch;
    }

    ++state.candidate_projection_verified;
    return CandidateProjectionStatus::Verified;
}

void validateCandidatePoint(CallbackState& state,
                            CPXCALLBACKCONTEXTptr context) {
    if (!state.validate_candidates || state.ncols <= 0 || state.g_col < 0) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    int is_point = 0;
    if (state.api->callbackcandidateispoint(context, &is_point) != 0 || !is_point) {
        return;
    }
    std::vector<double> x(static_cast<std::size_t>(state.ncols), 0.0);
    double obj = 0.0;
    if (state.api->callbackgetcandidatepoint(
            context, x.data(), 0, state.ncols - 1, &obj) != 0) {
        return;
    }
    const double g = x[static_cast<std::size_t>(state.g_col)];
    constexpr double tol = 1e-7;
    if (std::isfinite(g) && g > state.gamma_U + tol) {
        rejectCandidateWithGiniBound(state, context, true);
        return;
    }
    if (std::isfinite(g) && g < state.gamma_L - tol) {
        rejectCandidateWithGiniBound(state, context, false);
        return;
    }
    if (validateCandidateVisitInventory(state, context, x)) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    if (validateCandidateGiniSubsetEnvelope(state, context, x)) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    if (validateCandidateLowGiniL1(state, context, x)) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    if (validateCandidateVariableSCentering(state, context, x)) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    if (validateCandidateSubsetInventoryImbalance(state, context, x)) return;
    if (requestCallbackAbortIfDeadlineExceeded(state, context)) return;
    const CandidateRouteProjectionStatus route_projection =
        validateCandidateRouteProjection(state, context, x);
    if (route_projection == CandidateRouteProjectionStatus::Rejected) return;
    if (route_projection == CandidateRouteProjectionStatus::UnsupportedMismatch) return;
    const CandidateProjectionStatus projection =
        validateCandidateProjection(state, context, x);
    if (projection == CandidateProjectionStatus::Rejected) return;
    if (projection == CandidateProjectionStatus::UnsupportedMismatch) return;
    ++state.incumbents_verified;
}

void createOneShotGiniBranches(CallbackState& state,
                               CPXCALLBACKCONTEXTptr context) {
    if (!state.enable_gini_branch || state.g_col < 0) return;
    if (state.gamma_U - state.gamma_L < state.gini_branch_min_width) return;
    bool expected = false;
    if (!state.gini_branch_created.compare_exchange_strong(expected, true)) return;
    const double mid = 0.5 * (state.gamma_L + state.gamma_U);
    const int beg[1] = {0};
    const int ind[1] = {state.g_col};
    const int varcnt = 0;
    const int* varind = nullptr;
    const char* varlu = nullptr;
    const double* varbd = nullptr;
    int seq = 0;

    const double rhs_lo[1] = {mid};
    const char sense_lo[1] = {'L'};
    const double val_lo[1] = {1.0};
    const int rc_lo = state.api->callbackmakebranch(
        context, varcnt, varind, varlu, varbd,
        1, 1, rhs_lo, sense_lo, beg, ind, val_lo, 0.0, &seq);

    const double rhs_hi[1] = {-mid};
    const char sense_hi[1] = {'L'};
    const double val_hi[1] = {-1.0};
    const int rc_hi = state.api->callbackmakebranch(
        context, varcnt, varind, varlu, varbd,
        1, 1, rhs_hi, sense_hi, beg, ind, val_hi, 0.0, &seq);

    if (rc_lo == 0) ++state.gini_branches_created;
    if (rc_hi == 0) ++state.gini_branches_created;
}

int __stdcall tailoredCallback(CPXCALLBACKCONTEXTptr context,
                               CPXLONG contextid,
                               void* userhandle) {
    auto* state = static_cast<CallbackState*>(userhandle);
    if (!state || !state->api) return 0;
    sampleNativeCallbackInfo(*state, context);
    if (requestCallbackAbortIfDeadlineExceeded(*state, context)) return 0;
    if (contextid == kContextRelaxation) {
        ++state->relaxation_calls;
        sampleCallbackVector(*state, context, true);
        bool expected = false;
        if (callbackProfileAllows(*state, "gini_interval") &&
            state->add_gini_cut && state->g_col >= 0 &&
            state->gini_cut_added.compare_exchange_strong(expected, true)) {
            const double rhs[1] = {state->gamma_U};
            const char sense[1] = {'L'};
            const int beg[1] = {0};
            const int ind[1] = {state->g_col};
            const double val[1] = {1.0};
            const int purgeable[1] = {kUseCutForce};
            const int local[1] = {0};
            int rc = state->api->callbackaddusercuts(
                context, 1, 1, rhs, sense, beg, ind, val, purgeable, local);
            if (rc == 0) {
                ++state->user_cuts_added;
                ++state->gini_interval_cuts_added;
            }
        }
        if (callbackProfileAllows(*state, "visit_inventory")) {
            separateVisitInventoryLinking(*state, context);
        }
        if (callbackProfileAllows(*state, "low_gini_l1")) {
            separateLowGiniL1Centering(*state, context);
        }
        if (callbackProfileAllows(*state, "local_centering")) {
            separateLocalCentering(*state, context);
        }
        if (callbackProfileAllows(*state, "subset_cross_h")) {
            separateSubsetCrossHCentering(*state, context);
        }
        if (callbackProfileAllows(*state, "local_q")) {
            separateLocalQCentering(*state, context);
        }
        if (callbackProfileAllows(*state, "gs_product")) {
            separateGsProductCoupling(*state, context);
        }
        if (callbackProfileAllows(*state, "disagg_sp")) {
            separateDisaggregatedSpEstimator(*state, context);
        }
        if (callbackProfileAllows(*state, "vector_route_cutset")) {
            separateVectorRouteCutset(*state, context);
        }
        if (callbackProfileAllows(*state, "variable_s")) {
            separateVariableSCentering(*state, context);
        }
        if (callbackProfileAllows(*state, "gini_subset") ||
            callbackProfileAllows(*state, "subset_inventory") ||
            callbackProfileAllows(*state, "transfer_cutset") ||
            callbackProfileAllows(*state, "support_duration")) {
            if (shouldRunExpensiveSeparation(*state)) {
                if (callbackProfileAllows(*state, "gini_subset")) {
                    separateGiniSubsetEnvelope(*state, context);
                }
                if (callbackProfileAllows(*state, "subset_inventory")) {
                    separateSubsetInventoryImbalance(*state, context);
                }
                if (callbackProfileAllows(*state, "transfer_cutset")) {
                    separateTransferCutset(*state, context);
                }
                if (callbackProfileAllows(*state, "support_duration")) {
                    separateSupportDurationCover(*state, context);
                }
            }
        }
    } else if (contextid == kContextCandidate) {
        ++state->candidate_calls;
        ++state->incumbents_seen;
        sampleCallbackVector(*state, context, false);
        validateCandidatePoint(*state, context);
    } else if (contextid == kContextBranching) {
        ++state->branch_calls;
        createOneShotGiniBranches(*state, context);
    } else if (contextid == kContextGlobalProgress) {
        ++state->progress_calls;
    }
    return 0;
}

struct PackedGlobalGiniChild {
    std::vector<int> varind;
    std::vector<char> varlu;
    std::vector<double> varbd;
    std::vector<double> rhs;
    std::vector<char> sense;
    std::vector<int> rmatbeg;
    std::vector<int> rmatind;
    std::vector<double> rmatval;
    std::vector<std::string> row_signatures;
    std::vector<std::string> full_row_signatures;
    std::vector<std::string> families;
    std::vector<CanonicalLinearRow> canonical_rows_attached;
    std::vector<CanonicalBoundChange> canonical_bounds_attached;
    IntervalDomainSummary domain;
    ExactIncrementalDelta delta;
    std::string aggregate_signature;
    double factory_seconds = 0.0;
    long long theoretical_full_rows = 0;
    long long theoretical_full_bounds = 0;
    long long exact_duplicate_rows_omitted = 0;
    long long identical_bounds_omitted = 0;
    bool valid = true;
    std::string failure;
};

enum class GlobalLocalRowPhase {
    RootReady,
    PendingFirstRelaxation,
    AwaitingPostRowReoptimization,
    Ready
};

struct GlobalGiniNodeMetadata {
    CPXLONG uid = -1;
    CPXLONG parent_uid = -1;
    CPXLONG sibling_uid = -1;
    CPXLONG native_depth = -1;
    long long gini_generation = 0;
    double lower = 0.0;
    double upper = 0.0;
    double creation_time = 0.0;
    CPXLONG creation_node_count = 0;
    double first_process_time = -1.0;
    CPXLONG first_process_node_count = -1;
    long long relaxation_passes = 0;
    double pre_local_row_relaxation =
        std::numeric_limits<double>::quiet_NaN();
    double post_local_row_relaxation =
        std::numeric_limits<double>::quiet_NaN();
    double local_row_attach_time = -1.0;
    double row_factory_seconds = 0.0;
    double row_api_seconds = 0.0;
    bool post_row_reoptimization_seen = false;
    bool terminal_gini_refinement = false;
    bool created_by_gini_branch = false;
    double child_estimate = std::numeric_limits<double>::quiet_NaN();
    double domain_estimate = std::numeric_limits<double>::quiet_NaN();
    double estimate_lift = 0.0;
    std::string estimate_mode;
    GlobalLocalRowPhase phase = GlobalLocalRowPhase::PendingFirstRelaxation;
    std::vector<CanonicalLinearRow> pending_post_rows;
    // Canonical interval rows are immutable after a callback pass.  Native
    // integer children inherit exactly the same state, so share it instead of
    // copying thousands of coefficient maps into every open-node record.
    std::shared_ptr<const CanonicalInheritanceState> inherited_state;
    std::shared_ptr<const CanonicalInheritanceState> effective_state;
};

struct GlobalGiniCallbackState {
    Api* api = nullptr;
    const Instance* instance = nullptr;
    const SolveOptions* options = nullptr;
    int ncols = 0;
    int g_col = -1;
    std::unordered_map<std::string, int> column_index;
    double root_lower = 0.0;
    double root_upper = 1.0;
    double verified_incumbent = 0.0;
    std::chrono::steady_clock::time_point start =
        std::chrono::steady_clock::now();
    std::ofstream* node_trace = nullptr;
    std::ofstream* bound_trace = nullptr;
    std::ofstream* post_row_trace = nullptr;
    std::ofstream* topology_trace = nullptr;
    std::ofstream* sibling_trace = nullptr;
    std::ofstream* row_delta_trace = nullptr;
    std::ofstream* memory_trace = nullptr;
    std::mutex trace_mutex;
    std::atomic<long long> branch_calls{0};
    std::atomic<long long> relaxation_calls{0};
    std::atomic<long long> candidate_calls{0};
    std::atomic<long long> trace_event_sequence{0};
    std::atomic<long long> progress_calls{0};
    std::atomic<long long> gini_branch_nodes{0};
    std::atomic<long long> gini_children_created{0};
    std::atomic<long long> max_gini_generation{0};
    std::atomic<long long> ordinary_fallbacks{0};
    std::atomic<long long> nonoptimal_relaxation_fallbacks{0};
    std::atomic<long long> local_rows_attached{0};
    std::atomic<long long> local_bounds_attached{0};
    std::atomic<long long> local_row_failures{0};
    std::atomic<long long> column_mapping_failures{0};
    std::atomic<long long> coverage_failures{0};
    std::atomic<long long> child_estimate_failures{0};
    std::atomic<long long> local_bound_api_failures{0};
    std::atomic<long long> node_info_api_failures{0};
    std::atomic<long long> callback_failures{0};
    std::atomic<long long> post_row_reoptimizations{0};
    std::atomic<long long> post_row_reoptimization_failures{0};
    std::atomic<long long> exact_duplicate_rows_omitted{0};
    std::atomic<long long> identical_bounds_omitted{0};
    std::atomic<long long> delta_rows_attached{0};
    std::atomic<long long> delta_bounds_attached{0};
    std::atomic<long long> theoretical_full_rows{0};
    std::atomic<long long> theoretical_full_bounds{0};
    std::atomic<long long> ordinary_before_terminal{0};
    std::atomic<long long> ordinary_after_terminal{0};
    std::atomic<long long> sibling_first_process_count{0};
    std::atomic<long long> sibling_equal_estimate_pairs{0};
    std::atomic<long long> sibling_discriminated_pairs{0};
    std::atomic<double> row_factory_seconds{0.0};
    std::atomic<double> callback_packing_seconds{0.0};
    std::atomic<double> local_row_api_seconds{0.0};
    std::atomic<double> first_gini_branch_time{-1.0};
    std::atomic<bool> callback_abort_used{false};
    std::atomic<bool> migration_complete{true};
    std::atomic<bool> branch_coverage_valid{true};
    std::atomic<bool> bound_monotone{true};
    std::mutex node_metadata_mutex;
    std::unordered_map<CPXLONG, GlobalGiniNodeMetadata> node_metadata;
    std::shared_ptr<const CanonicalInheritanceState> root_inheritance_state;
    double last_global_bound = -std::numeric_limits<double>::infinity();
    std::string factory_version = "round19_v2_projected_centering";
    int presolve_effective = 1;
    int search_effective = 2;
    int node_select_effective = 1;
    std::string run_id;
    std::vector<std::string> global_families;
    std::unique_ptr<DenseProgressRecorder> dense_progress;
};

double globalTreeElapsed(const GlobalGiniCallbackState& state) {
    return std::chrono::duration<double>(
        std::chrono::steady_clock::now() - state.start).count();
}

std::string localRowPhaseName(GlobalLocalRowPhase phase) {
    switch (phase) {
    case GlobalLocalRowPhase::RootReady: return "root_ready";
    case GlobalLocalRowPhase::PendingFirstRelaxation:
        return "pending_first_relaxation";
    case GlobalLocalRowPhase::AwaitingPostRowReoptimization:
        return "awaiting_post_row_reoptimization";
    case GlobalLocalRowPhase::Ready: return "ready";
    }
    return "unknown";
}

std::string csvCell(const std::string& value) {
    if (value.find_first_of(",\"\n\r") == std::string::npos) return value;
    std::string out = "\"";
    for (char ch : value) out += ch == '"' ? "\"\"" : std::string(1, ch);
    out += '"';
    return out;
}

std::string joinText(const std::vector<std::string>& values,
                     const std::string& separator) {
    std::ostringstream out;
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index) out << separator;
        out << values[index];
    }
    return out.str();
}

void abortGlobalTreeCallback(GlobalGiniCallbackState& state,
                             CPXCALLBACKCONTEXTptr context) {
    ++state.callback_failures;
    state.callback_abort_used.store(true);
    state.api->callbackabort(context);
}

std::shared_ptr<const CanonicalInheritanceState> mergedCanonicalState(
    const std::shared_ptr<const CanonicalInheritanceState>& base,
    const std::vector<CanonicalLinearRow>& rows,
    const std::vector<CanonicalBoundChange>& bounds,
    std::string& failure) {
    if (!base || !base->valid) {
        failure = base && !base->failure_reason.empty()
            ? base->failure_reason : "missing_or_invalid_canonical_state";
        return nullptr;
    }
    auto merged = std::make_shared<CanonicalInheritanceState>(*base);
    if (!mergeCanonicalInheritanceState(*merged, rows, bounds, &failure)) {
        return nullptr;
    }
    return merged;
}

PackedGlobalGiniChild packGlobalGiniChild(
    GlobalGiniCallbackState& state,
    double lower,
    double upper,
    bool lower_child,
    bool pack_rows_for_api,
    const CanonicalInheritanceState* inherited) {
    PackedGlobalGiniChild packed;
    const auto factory_start = std::chrono::steady_clock::now();
    IntervalRowFactoryRequest request;
    request.gamma_L = lower;
    request.gamma_U = upper;
    request.verified_incumbent = state.verified_incumbent;
    request.incumbent_epsilon = 0.0;
    request.add_incumbent_row = true;
    request.strengthened = true;
    IntervalRowFactoryResult rows = buildRound18StaticIntervalRows(
        *state.instance, *state.options, request);
    packed.factory_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - factory_start).count();
    atomicAdd(state.row_factory_seconds, packed.factory_seconds);
    packed.aggregate_signature = rows.aggregate_signature;
    packed.domain = rows.domain;
    state.factory_version = rows.factory_version;
    if (!rows.complete_round18_static_migration) {
        state.migration_complete.store(false);
        packed.valid = false;
        packed.failure = "unsupported_active_families:" +
            joinText(rows.unsupported_active_families, "|");
        return packed;
    }
    if (rows.domain.domain_infeasible) {
        packed.valid = false;
        packed.failure =
            "factory_domain_infeasible_without_proved_native_contradiction";
        return packed;
    }
    rows.rows.erase(std::remove_if(rows.rows.begin(), rows.rows.end(),
        [](const CanonicalLinearRow& row) {
            return row.family == "verified_incumbent_objective_row";
        }), rows.rows.end());
    packed.theoretical_full_rows = static_cast<long long>(rows.rows.size());
    packed.theoretical_full_bounds =
        static_cast<long long>(rows.bound_changes.size());
    for (const CanonicalLinearRow& row : rows.rows) {
        packed.full_row_signatures.push_back(row.signature);
    }

    std::vector<CanonicalLinearRow> selected_rows = rows.rows;
    std::vector<CanonicalBoundChange> selected_bounds = rows.bound_changes;
    const bool incremental = state.options->global_gini_tree_row_attachment_mode ==
        "exact-incremental-delta";
    if (incremental) {
        if (inherited == nullptr || !inherited->valid) {
            packed.valid = false;
            packed.failure = "missing_or_invalid_parent_inheritance_metadata";
            return packed;
        }
        packed.delta = computeExactIncrementalDelta(*inherited, rows);
        if (!packed.delta.valid) {
            packed.valid = false;
            packed.failure = "incremental_delta_failure:" +
                packed.delta.failure_reason;
            return packed;
        }
        selected_rows = packed.delta.rows_to_attach;
        selected_bounds = packed.delta.bounds_to_attach;
        packed.exact_duplicate_rows_omitted =
            packed.delta.exact_duplicate_rows_omitted;
        packed.identical_bounds_omitted =
            packed.delta.identical_bounds_omitted;
    }
    std::set<std::string> family_set;
    for (const CanonicalBoundChange& bound : selected_bounds) {
        if (!incremental && bound.variable == "G") {
            if (lower_child && bound.direction != 'U') continue;
            if (!lower_child && bound.direction != 'L') continue;
        }
        const auto column = state.column_index.find(bound.variable);
        if (column == state.column_index.end()) {
            packed.valid = false;
            packed.failure = "missing_bound_column:" + bound.variable;
            ++state.column_mapping_failures;
            return packed;
        }
        packed.varind.push_back(column->second);
        packed.varlu.push_back(bound.direction);
        packed.varbd.push_back(bound.value);
        packed.canonical_bounds_attached.push_back(bound);
        family_set.insert(bound.family);
    }
    for (const CanonicalLinearRow& row : selected_rows) {
        if (pack_rows_for_api) {
            packed.rmatbeg.push_back(static_cast<int>(packed.rmatind.size()));
            packed.rhs.push_back(row.rhs);
            packed.sense.push_back(row.sense);
            for (const auto& coefficient : row.coefficients) {
                const auto column = state.column_index.find(coefficient.first);
                if (column == state.column_index.end()) {
                    packed.valid = false;
                    packed.failure = "missing_row_column:" + coefficient.first +
                        ":family=" + row.family;
                    ++state.column_mapping_failures;
                    return packed;
                }
                packed.rmatind.push_back(column->second);
                packed.rmatval.push_back(coefficient.second);
            }
            packed.canonical_rows_attached.push_back(row);
        }
        packed.row_signatures.push_back(row.signature);
        family_set.insert(row.family);
    }
    packed.families.assign(family_set.begin(), family_set.end());
    return packed;
}

bool chooseGlobalGiniSplit(const GlobalGiniCallbackState& state,
                           double lower,
                           double upper,
                           long long node_depth,
                           double& split,
                           long long& gini_generation) {
    const int initial_count = std::max(1, state.options->frontier_intervals);
    const std::vector<GiniIntervalGeometry> initial =
        makeLegacyFrontierIntervals(state.root_lower, state.root_upper,
                                    initial_count);
    std::vector<double> interior;
    for (std::size_t index = 0; index + 1 < initial.size(); ++index) {
        const double breakpoint = initial[index].upper;
        if (breakpoint > lower + 1e-10 && breakpoint < upper - 1e-10) {
            interior.push_back(breakpoint);
        }
    }
    if (!interior.empty()) {
        split = interior[interior.size() / 2];
        gini_generation = node_depth + 1;
        return true;
    }
    int initial_depth = 0;
    int leaves = 1;
    while (leaves < initial_count) {
        leaves *= 2;
        ++initial_depth;
    }
    const int adaptive_depth = std::max(
        0, static_cast<int>(node_depth) - initial_depth);
    if (!state.options->frontier_adaptive_split ||
        !legacyAdaptiveSplitEligible(
            lower, upper, adaptive_depth,
            state.options->frontier_adaptive_max_depth,
            state.options->frontier_adaptive_min_width)) {
        return false;
    }
    if (state.options->frontier_adaptive_split_factor != 2) return false;
    const std::vector<GiniIntervalGeometry> children =
        splitLegacyFrontierInterval(lower, upper,
                                    state.options->frontier_adaptive_split_factor);
    if (children.size() != 2) return false;
    split = children.front().upper;
    gini_generation = node_depth + 1;
    return split > lower + 1e-12 && split < upper - 1e-12;
}

struct GlobalNodeEvent {
    std::string context;
    std::string action;
    CPXLONG uid = -1;
    CPXLONG parent_uid = -1;
    CPXLONG depth = -1;
    long long gini_generation = 0;
    long long relaxation_pass = 0;
    std::string local_row_phase;
    double lower = 0.0;
    double upper = 0.0;
    double relaxation = std::numeric_limits<double>::quiet_NaN();
    double global_bound = std::numeric_limits<double>::quiet_NaN();
    double native_incumbent = std::numeric_limits<double>::infinity();
    double split = 0.0;
    double lower_child_upper = 0.0;
    double upper_child_lower = 0.0;
    double lower_estimate = std::numeric_limits<double>::quiet_NaN();
    double upper_estimate = std::numeric_limits<double>::quiet_NaN();
    int lower_rc = 0;
    int upper_rc = 0;
    int lower_id = -1;
    int upper_id = -1;
    CPXLONG node_count = -1;
    CPXLONG nodes_left = -1;
    CPXLONG iteration_count = -1;
    double factory_seconds = 0.0;
    double row_api_seconds = 0.0;
};

void writeGlobalNodeEvent(GlobalGiniCallbackState& state,
                          const GlobalNodeEvent& event,
                          const PackedGlobalGiniChild* lower_child,
                          const PackedGlobalGiniChild* upper_child) {
    if (!state.node_trace) return;
    std::lock_guard<std::mutex> lock(state.trace_mutex);
    const std::vector<std::string> empty;
    const std::string local_flag_description =
        event.action == "attach_interval_local_rows"
            ? "forced_local_user_cut:local=1"
            : (event.action == "recursive_gini_split"
                   ? (state.options->global_gini_tree_row_timing_mode == "eager"
                          ? "child_bound_changes:rows_eager_at_branch_creation"
                          : "child_bound_changes:rows_deferred_to_first_relaxation")
                   : "none");
    *state.node_trace
        << csvCell(state.run_id) << ','
        << ++state.trace_event_sequence << ','
        << std::setprecision(17) << globalTreeElapsed(state) << ','
        << event.uid << ',' << event.parent_uid << ',' << event.depth << ','
        << event.gini_generation << ',' << event.relaxation_pass << ','
        << csvCell(event.local_row_phase) << ','
        << event.lower << ',' << event.upper << ',' << event.relaxation << ','
        << event.global_bound << ',' << event.native_incumbent << ','
        << state.verified_incumbent << ',' << csvCell(event.context) << ','
        << csvCell(event.action) << ',' << event.split << ','
        << event.lower << ',' << event.lower_child_upper << ','
        << event.upper_child_lower << ',' << event.upper << ','
        << event.lower_estimate << ',' << event.upper_estimate << ','
        << event.lower_rc << ',' << event.upper_rc << ',' << event.lower_id << ','
        << event.upper_id << ','
        << csvCell(joinText(lower_child ? lower_child->families : empty, "|"))
        << ','
        << csvCell(joinText(upper_child ? upper_child->families : empty, "|"))
        << ',' << csvCell(joinText(state.global_families, "|"))
        << ',' << csvCell(local_flag_description) << ','
        << csvCell(lower_child ? joinText(lower_child->row_signatures, "|") : "")
        << ','
        << csvCell(upper_child ? joinText(upper_child->row_signatures, "|") : "")
        << ',' << state.presolve_effective << ',' << state.search_effective
        << ',' << state.node_select_effective << ',' << event.node_count << ','
        << event.nodes_left << ',' << event.iteration_count << ','
        << event.factory_seconds << ',' << event.row_api_seconds
        << ",not_exposed_in_generic_callback\n";
    state.node_trace->flush();
}

bool snapshotGlobalNode(GlobalGiniCallbackState& state,
                        CPXLONG uid,
                        CPXLONG depth,
                        CPXLONG node_count,
                        double lower,
                        double upper,
                        GlobalGiniNodeMetadata& snapshot,
                        std::string& failure) {
    bool first_process = false;
    {
        std::lock_guard<std::mutex> lock(state.node_metadata_mutex);
        auto found = state.node_metadata.find(uid);
        if (found == state.node_metadata.end()) {
            if (depth == 0 && state.root_inheritance_state &&
                state.root_inheritance_state->valid) {
                GlobalGiniNodeMetadata root;
                root.uid = uid;
                root.parent_uid = -1;
                root.native_depth = depth;
                root.gini_generation = 0;
                root.lower = lower;
                root.upper = upper;
                root.creation_time = 0.0;
                root.creation_node_count = 0;
                root.phase = GlobalLocalRowPhase::RootReady;
                root.inherited_state = state.root_inheritance_state;
                root.effective_state = state.root_inheritance_state;
                found = state.node_metadata.emplace(uid, std::move(root)).first;
            } else {
                // Children created by CPLEX's ordinary integer branching do
                // not pass through CPXcallbackmakebranch, so their native
                // UIDs are not announced to the application.  Their local G
                // bounds are nevertheless inherited exactly.  Recover the
                // unique Gini state from the deepest already-seen node with
                // the same interval.  If more than one such node exists at
                // that depth the exact native parent UID is unknowable, but
                // the inherited canonical row state is identical and is all
                // that correctness of subsequent Gini refinement requires.
                const GlobalGiniNodeMetadata* prototype = nullptr;
                CPXLONG prototype_depth = -1;
                CPXLONG unique_parent_uid = -2;
                int deepest_matches = 0;
                for (const auto& entry : state.node_metadata) {
                    const GlobalGiniNodeMetadata& candidate = entry.second;
                    if (candidate.native_depth >= depth ||
                        std::fabs(candidate.lower - lower) > 1e-8 ||
                        std::fabs(candidate.upper - upper) > 1e-8 ||
                        !candidate.effective_state ||
                        !candidate.effective_state->valid ||
                        candidate.phase ==
                            GlobalLocalRowPhase::PendingFirstRelaxation ||
                        candidate.phase ==
                            GlobalLocalRowPhase::AwaitingPostRowReoptimization) {
                        continue;
                    }
                    if (candidate.native_depth > prototype_depth) {
                        prototype = &candidate;
                        prototype_depth = candidate.native_depth;
                        unique_parent_uid = candidate.uid;
                        deepest_matches = 1;
                    } else if (candidate.native_depth == prototype_depth) {
                        if (state.options->global_gini_tree_row_attachment_mode ==
                                "exact-incremental-delta" &&
                            candidate.effective_state !=
                                prototype->effective_state) {
                            failure =
                                "ambiguous_inherited_canonical_state_for_uid:" +
                                std::to_string(uid) + ":depth=" +
                                std::to_string(depth);
                            return false;
                        }
                        ++deepest_matches;
                        unique_parent_uid = -2;
                    }
                }
                if (!prototype) {
                    failure = "missing_inherited_interval_metadata_for_uid:" +
                        std::to_string(uid) + ":depth=" +
                        std::to_string(depth);
                    return false;
                }
                GlobalGiniNodeMetadata ordinary = *prototype;
                ordinary.uid = uid;
                ordinary.parent_uid = deepest_matches == 1
                    ? unique_parent_uid : -2;
                ordinary.sibling_uid = -1;
                ordinary.native_depth = depth;
                ordinary.creation_time = globalTreeElapsed(state);
                ordinary.creation_node_count = node_count;
                ordinary.first_process_time = -1.0;
                ordinary.first_process_node_count = -1;
                ordinary.relaxation_passes = 0;
                ordinary.pre_local_row_relaxation =
                    std::numeric_limits<double>::quiet_NaN();
                ordinary.post_local_row_relaxation =
                    std::numeric_limits<double>::quiet_NaN();
                ordinary.row_factory_seconds = 0.0;
                ordinary.row_api_seconds = 0.0;
                ordinary.post_row_reoptimization_seen = false;
                ordinary.created_by_gini_branch = false;
                ordinary.phase = GlobalLocalRowPhase::Ready;
                found = state.node_metadata.emplace(
                    uid, std::move(ordinary)).first;
            }
        }
        GlobalGiniNodeMetadata& metadata = found->second;
        if (std::fabs(metadata.lower - lower) > 1e-8 ||
            std::fabs(metadata.upper - upper) > 1e-8) {
            failure = "node_interval_metadata_mismatch:" +
                std::to_string(uid);
            return false;
        }
        metadata.native_depth = depth;
        if (metadata.first_process_time < 0.0) {
            metadata.first_process_time = globalTreeElapsed(state);
            metadata.first_process_node_count = node_count;
            first_process = true;
        }
        snapshot = metadata;
    }
    if (first_process && snapshot.created_by_gini_branch &&
        snapshot.parent_uid >= 0 && state.sibling_trace) {
        std::lock_guard<std::mutex> trace_lock(state.trace_mutex);
        *state.sibling_trace << std::setprecision(17)
            << csvCell(state.run_id) << ',' << snapshot.uid << ','
            << snapshot.parent_uid << ',' << snapshot.sibling_uid << ','
            << snapshot.creation_time << ',' << snapshot.first_process_time << ','
            << snapshot.first_process_time - snapshot.creation_time << ','
            << snapshot.creation_node_count << ','
            << snapshot.first_process_node_count << ','
            << snapshot.first_process_node_count - snapshot.creation_node_count
            << ',' << snapshot.child_estimate << ','
            << snapshot.domain_estimate << ',' << snapshot.estimate_lift << ','
            << csvCell(snapshot.estimate_mode) << '\n';
        state.sibling_trace->flush();
        ++state.sibling_first_process_count;
    }
    return true;
}

bool canonicalRowsSatisfiedAtPoint(
    const GlobalGiniCallbackState& state,
    const std::vector<CanonicalLinearRow>& rows,
    const std::vector<double>& point,
    std::string& failure) {
    if (point.size() != static_cast<std::size_t>(state.ncols)) {
        failure = "invalid_relaxation_dimension";
        return false;
    }
    for (const CanonicalLinearRow& row : rows) {
        double activity = 0.0;
        double scale = 1.0 + std::fabs(row.rhs);
        for (const auto& coefficient : row.coefficients) {
            const auto column = state.column_index.find(coefficient.first);
            if (column == state.column_index.end() || column->second < 0 ||
                column->second >= state.ncols) {
                failure = "canonical_post_row_missing_column:" +
                    coefficient.first;
                return false;
            }
            const double term = coefficient.second *
                point[static_cast<std::size_t>(column->second)];
            activity += term;
            scale += std::fabs(term);
        }
        const double tolerance = 1e-5 * scale;
        const bool satisfied = row.sense == 'L'
            ? activity <= row.rhs + tolerance
            : (row.sense == 'G'
                ? activity + tolerance >= row.rhs
                : std::fabs(activity - row.rhs) <= tolerance);
        if (!satisfied) {
            failure = "canonical_post_row_violation:" + row.signature;
            return false;
        }
    }
    return true;
}

bool canonicalStateSatisfiedAtPoint(
    const GlobalGiniCallbackState& state,
    const CanonicalInheritanceState& canonical,
    const std::vector<double>& point,
    std::string& failure) {
    if (!canonical.valid) {
        failure = "invalid_canonical_state";
        return false;
    }
    std::vector<CanonicalLinearRow> rows;
    rows.reserve(canonical.rows_by_signature.size());
    for (const auto& entry : canonical.rows_by_signature) {
        rows.push_back(entry.second);
    }
    if (!canonicalRowsSatisfiedAtPoint(state, rows, point, failure)) {
        return false;
    }
    for (const auto& entry : canonical.effective_bounds_by_key) {
        const CanonicalBoundChange& bound = entry.second;
        const auto column = state.column_index.find(bound.variable);
        if (column == state.column_index.end() || column->second < 0 ||
            column->second >= state.ncols) {
            failure = "canonical_post_bound_missing_column:" + bound.variable;
            return false;
        }
        const double value = point[static_cast<std::size_t>(column->second)];
        const double tolerance = 1e-6 * (1.0 + std::fabs(bound.value));
        const bool satisfied = bound.direction == 'L'
            ? value + tolerance >= bound.value
            : value <= bound.value + tolerance;
        if (!satisfied) {
            failure = "canonical_post_bound_violation:" + bound.signature;
            return false;
        }
    }
    return true;
}

std::string joinDoubles(const std::vector<double>& values,
                        const std::string& separator,
                        int first_index = 0) {
    std::ostringstream out;
    out << std::setprecision(17);
    for (int index = std::max(0, first_index);
         index < static_cast<int>(values.size()); ++index) {
        if (index > std::max(0, first_index)) out << separator;
        out << values[static_cast<std::size_t>(index)];
    }
    return out.str();
}

void writeRowDeltaAudit(GlobalGiniCallbackState& state,
                        CPXLONG uid,
                        CPXLONG parent_uid,
                        const PackedGlobalGiniChild& packed,
                        const std::string& event) {
    if (!state.row_delta_trace) return;
    std::lock_guard<std::mutex> lock(state.trace_mutex);
    *state.row_delta_trace << std::setprecision(17)
        << csvCell(state.run_id) << ',' << uid << ',' << parent_uid << ','
        << csvCell(event) << ','
        << csvCell(state.options->global_gini_tree_row_attachment_mode) << ','
        << packed.theoretical_full_rows << ','
        << packed.theoretical_full_bounds << ','
        << packed.delta.inherited_rows << ','
        << packed.delta.inherited_bounds << ','
        << packed.exact_duplicate_rows_omitted << ','
        << packed.identical_bounds_omitted << ','
        << packed.delta.dominance_omissions << ','
        << packed.canonical_rows_attached.size() << ','
        << packed.canonical_bounds_attached.size() << ','
        << packed.factory_seconds << ','
        << csvCell(joinText(packed.families, "|")) << ','
        << csvCell(packed.aggregate_signature) << ','
        << (packed.valid ? "passed" : "failed") << ','
        << csvCell(packed.failure) << '\n';
    state.row_delta_trace->flush();
}

#if 0
int __stdcall globalGiniTreeCallbackRound19Disabled(CPXCALLBACKCONTEXTptr context,
                                     CPXLONG contextid,
                                     void* userhandle) {
    auto* state = static_cast<GlobalGiniCallbackState*>(userhandle);
    if (!state || !state->api || !state->instance || !state->options) return 0;
    if (contextid == kContextGlobalProgress ||
        contextid == kContextLocalProgress) {
        ++state->progress_calls;
        double bound = 0.0;
        CPXLONG nodes = 0;
        const int bound_rc = state->api->callbackgetinfodbl(
            context, kCallbackInfoBestBnd, &bound);
        state->api->callbackgetinfolong(context, kCallbackInfoNodeCount, &nodes);
        if (bound_rc == 0 && std::isfinite(bound)) {
            std::lock_guard<std::mutex> lock(state->trace_mutex);
            if (bound + 1e-7 < state->last_global_bound) {
                state->bound_monotone.store(false);
            }
            state->last_global_bound = std::max(state->last_global_bound, bound);
            if (state->bound_trace && !state->dense_progress) {
                *state->bound_trace << std::setprecision(17)
                    << globalTreeElapsed(*state) << ',' << bound << ','
                    << state->verified_incumbent
                    << ','
                    << (std::isfinite(state->verified_incumbent)
                            ? std::max(0.0, state->verified_incumbent - bound)
                            : 0.0)
                    << ',' << nodes << ",,global_progress\n";
                state->bound_trace->flush();
            }
        }
        return 0;
    }
    if (contextid == kContextRelaxation) {
        CPXLONG uid = -1;
        CPXLONG depth = -1;
        CPXLONG nodes = -1;
        if (state->api->callbackgetinfolong(
                context, kCallbackInfoNodeUid, &uid) != 0 ||
            state->api->callbackgetinfolong(
                context, kCallbackInfoNodeDepth, &depth) != 0 ||
            state->api->callbackgetinfolong(
                context, kCallbackInfoNodeCount, &nodes) != 0) {
            ++state->node_info_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        {
            std::lock_guard<std::mutex> lock(state->pending_local_rows_mutex);
            const auto pending = state->pending_local_row_nodes.find(
                static_cast<int>(uid));
            if (pending == state->pending_local_row_nodes.end()) return 0;
            state->pending_local_row_nodes.erase(pending);
        }
        double lower = 0.0;
        double upper = 0.0;
        const int lower_rc = state->api->callbackgetlocallb(
            context, &lower, state->g_col, state->g_col);
        const int upper_rc = state->api->callbackgetlocalub(
            context, &upper, state->g_col, state->g_col);
        if (lower_rc != 0 || upper_rc != 0 || !std::isfinite(lower) ||
            !std::isfinite(upper) || upper < lower - 1e-9) {
            ++state->local_bound_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        PackedGlobalGiniChild local = packGlobalGiniChild(
            *state, lower, upper, true, true);
        if (!local.valid) {
            ++state->local_row_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        int add_rc = 0;
        if (!local.rhs.empty()) {
            std::vector<int> purgeable(local.rhs.size(), kUseCutForce);
            std::vector<int> local_flags(local.rhs.size(), 1);
            add_rc = state->api->callbackaddusercuts(
                context, static_cast<int>(local.rhs.size()),
                static_cast<int>(local.rmatind.size()), local.rhs.data(),
                local.sense.data(), local.rmatbeg.data(),
                local.rmatind.data(), local.rmatval.data(), purgeable.data(),
                local_flags.data());
        }
        double relaxation = std::numeric_limits<double>::quiet_NaN();
        std::vector<double> relaxation_point(
            static_cast<std::size_t>(state->ncols), 0.0);
        state->api->callbackgetrelaxationpoint(
            context, relaxation_point.data(), 0, state->ncols - 1,
            &relaxation);
        double global_bound = 0.0;
        state->api->callbackgetinfodbl(context, kCallbackInfoBestBnd,
                                       &global_bound);
        writeGlobalNodeEvent(
            *state, "relaxation", uid, depth, lower, upper, relaxation,
            global_bound, state->verified_incumbent,
            "attach_interval_local_rows", 0.0, upper, lower, relaxation,
            add_rc, 0, -1, -1, nodes, &local, nullptr);
        if (add_rc != 0) {
            ++state->local_row_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        state->local_rows_attached +=
            static_cast<long long>(local.rhs.size());
        return 0;
    }
    if (contextid != kContextBranching) return 0;
    ++state->branch_calls;
    double lower = 0.0;
    double upper = 0.0;
    const int lower_rc = state->api->callbackgetlocallb(
        context, &lower, state->g_col, state->g_col);
    const int upper_rc = state->api->callbackgetlocalub(
        context, &upper, state->g_col, state->g_col);
    if (lower_rc != 0 || upper_rc != 0 || !std::isfinite(lower) ||
        !std::isfinite(upper) || upper < lower - 1e-9) {
        ++state->local_bound_api_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    CPXLONG uid = -1;
    CPXLONG depth = -1;
    CPXLONG nodes = -1;
    if (state->api->callbackgetinfolong(
            context, kCallbackInfoNodeUid, &uid) != 0 ||
        state->api->callbackgetinfolong(
            context, kCallbackInfoNodeDepth, &depth) != 0 ||
        state->api->callbackgetinfolong(
            context, kCallbackInfoNodeCount, &nodes) != 0) {
        ++state->node_info_api_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    int relaxation_status = 0;
    const int relaxation_status_rc =
        state->api->callbackgetrelaxationstatus(
            context, &relaxation_status, 0);
    if (relaxation_status_rc != 0 ||
        (relaxation_status != kLpStatusOptimal &&
         relaxation_status != kLpStatusOptimalInfeasible)) {
        ++state->ordinary_fallbacks;
        ++state->nonoptimal_relaxation_fallbacks;
        double global_bound = 0.0;
        state->api->callbackgetinfodbl(context, kCallbackInfoBestBnd,
                                       &global_bound);
        writeGlobalNodeEvent(
            *state, "branching", uid, depth, lower, upper,
            std::numeric_limits<double>::quiet_NaN(), global_bound,
            state->verified_incumbent,
            "nonoptimal_relaxation_cplex_fallback_status_" +
                std::to_string(relaxation_status) + "_rc_" +
                std::to_string(relaxation_status_rc),
            0.0, 0.0, 0.0,
            std::numeric_limits<double>::quiet_NaN(), 0, 0, -1, -1,
            nodes, nullptr, nullptr);
        return 0;
    }
    std::vector<double> relaxation_point(
        static_cast<std::size_t>(state->ncols), 0.0);
    double relaxation = 0.0;
    if (state->api->callbackgetrelaxationpoint(
            context, relaxation_point.data(), 0, state->ncols - 1,
            &relaxation) != 0 || !std::isfinite(relaxation)) {
        ++state->child_estimate_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    double global_bound = 0.0;
    double incumbent = std::numeric_limits<double>::infinity();
    state->api->callbackgetinfodbl(context, kCallbackInfoBestBnd,
                                   &global_bound);
    state->api->callbackgetinfodbl(context, kCallbackInfoBestSol,
                                   &incumbent);
    incumbent = state->verified_incumbent;
    double split = 0.0;
    long long generation = 0;
    if (!chooseGlobalGiniSplit(*state, lower, upper, depth, split,
                               generation)) {
        ++state->ordinary_fallbacks;
        writeGlobalNodeEvent(*state, "branching", uid, depth, lower, upper,
                             relaxation, global_bound, incumbent,
                             "ordinary_cplex_branch_fallback", 0.0, 0.0, 0.0,
                             relaxation, 0, 0, -1, -1, nodes, nullptr, nullptr);
        return 0;
    }
    const GiniIntervalGeometry parent{lower, upper};
    const std::vector<GiniIntervalGeometry> children = {
        {lower, split}, {split, upper}
    };
    std::string coverage_reason;
    if (!exactIntervalCoverage(parent, children, 1e-10, &coverage_reason)) {
        ++state->coverage_failures;
        state->branch_coverage_valid.store(false);
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    PackedGlobalGiniChild low = packGlobalGiniChild(
        *state, lower, split, true, false);
    PackedGlobalGiniChild high = packGlobalGiniChild(
        *state, split, upper, false, false);
    if (!low.valid || !high.valid) {
        ++state->local_row_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    int low_id = -1;
    int high_id = -1;
    const int make_low_rc = state->api->callbackmakebranch(
        context,
        static_cast<int>(low.varind.size()),
        low.varind.empty() ? nullptr : low.varind.data(),
        low.varlu.empty() ? nullptr : low.varlu.data(),
        low.varbd.empty() ? nullptr : low.varbd.data(),
        static_cast<int>(low.rhs.size()),
        static_cast<int>(low.rmatind.size()),
        low.rhs.empty() ? nullptr : low.rhs.data(),
        low.sense.empty() ? nullptr : low.sense.data(),
        low.rmatbeg.empty() ? nullptr : low.rmatbeg.data(),
        low.rmatind.empty() ? nullptr : low.rmatind.data(),
        low.rmatval.empty() ? nullptr : low.rmatval.data(),
        relaxation, &low_id);
    const int make_high_rc = state->api->callbackmakebranch(
        context,
        static_cast<int>(high.varind.size()),
        high.varind.empty() ? nullptr : high.varind.data(),
        high.varlu.empty() ? nullptr : high.varlu.data(),
        high.varbd.empty() ? nullptr : high.varbd.data(),
        static_cast<int>(high.rhs.size()),
        static_cast<int>(high.rmatind.size()),
        high.rhs.empty() ? nullptr : high.rhs.data(),
        high.sense.empty() ? nullptr : high.sense.data(),
        high.rmatbeg.empty() ? nullptr : high.rmatbeg.data(),
        high.rmatind.empty() ? nullptr : high.rmatind.data(),
        high.rmatval.empty() ? nullptr : high.rmatval.data(),
        relaxation, &high_id);
    writeGlobalNodeEvent(*state, "branching", uid, depth, lower, upper,
                         relaxation, global_bound, incumbent,
                         "recursive_gini_split", split, split, split,
                         relaxation, make_low_rc, make_high_rc, low_id, high_id,
                         nodes, &low, &high);
    if (make_low_rc != 0 || make_high_rc != 0) {
        ++state->local_row_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    ++state->gini_branch_nodes;
    state->gini_children_created += 2;
    {
        std::lock_guard<std::mutex> lock(state->pending_local_rows_mutex);
        state->pending_local_row_nodes.insert(low_id);
        state->pending_local_row_nodes.insert(high_id);
    }
    state->local_bounds_attached += static_cast<long long>(
        low.varind.size() + high.varind.size());
    long long previous = state->max_gini_generation.load();
    while (generation > previous &&
           !state->max_gini_generation.compare_exchange_weak(
               previous, generation)) {}
    return 0;
}
#endif

int __stdcall globalGiniTreeCallback(CPXCALLBACKCONTEXTptr context,
                                     CPXLONG contextid,
                                     void* userhandle) {
    auto* state = static_cast<GlobalGiniCallbackState*>(userhandle);
    if (!state || !state->api || !state->instance || !state->options) return 0;

    auto infoLong = [&](CPXCALLBACKINFO what, CPXLONG fallback = -1) {
        CPXLONG value = fallback;
        if (state->api->callbackgetinfolong(context, what, &value) != 0) {
            return fallback;
        }
        return value;
    };
    auto infoDouble = [&](CPXCALLBACKINFO what, double fallback) {
        double value = fallback;
        if (state->api->callbackgetinfodbl(context, what, &value) != 0) {
            return fallback;
        }
        return value;
    };

    if (contextid == kContextGlobalProgress) {
        const auto instrumentation_start = std::chrono::steady_clock::now();
        ++state->progress_calls;
        const CPXLONG nodes = infoLong(kCallbackInfoNodeCount);
        const CPXLONG nodes_left = infoLong(kCallbackInfoNodesLeft);
        const CPXLONG iterations = infoLong(kCallbackInfoIterationCount);
        const double bound = infoDouble(
            kCallbackInfoBestBnd, std::numeric_limits<double>::quiet_NaN());
        const double native_incumbent = infoDouble(
            kCallbackInfoBestSol, std::numeric_limits<double>::infinity());
        if (state->dense_progress) {
            DenseProgressSnapshot snapshot;
            snapshot.callback_invocation_sequence =
                state->dense_progress->stats().callback_invocation_count + 1;
            snapshot.observation_time_seconds = globalTreeElapsed(*state);
            const bool global_progress =
                contextid == kContextGlobalProgress;
            snapshot.callback_context = global_progress
                ? "global_progress" : "local_progress";
            snapshot.observation_source = global_progress
                ? "cplex_generic_global_progress"
                : "cplex_generic_local_progress";
            double deterministic_time = 0.0;
            if (state->api->callbackgetinfodbl(
                    context, kCallbackInfoDeterministicTime,
                    &deterministic_time) == 0 &&
                std::isfinite(deterministic_time)) {
                snapshot.deterministic_time_available = true;
                snapshot.deterministic_time = deterministic_time;
            }
            snapshot.native_best_bound_available =
                std::isfinite(bound) &&
                std::fabs(bound) < kCplexInfinityBound;
            snapshot.native_best_bound = bound;
            snapshot.native_incumbent_available =
                std::isfinite(native_incumbent) &&
                std::fabs(native_incumbent) < kCplexInfinityBound;
            snapshot.native_incumbent = native_incumbent;
            snapshot.verified_upper_bound_available = true;
            snapshot.verified_upper_bound = state->verified_incumbent;
            snapshot.processed_nodes_available = nodes >= 0;
            snapshot.processed_nodes = nodes;
            snapshot.open_nodes_available = nodes_left >= 0;
            snapshot.open_nodes = nodes_left;
            snapshot.simplex_iterations_available = iterations >= 0;
            snapshot.simplex_iterations = iterations;
            snapshot.gini_branch_count = state->gini_branch_nodes.load();
            snapshot.ordinary_branch_count = state->ordinary_fallbacks.load();
            if (nodes <= 0) {
                snapshot.phase = iterations > 0 ? "root_cuts" : "root_lp";
            } else if (snapshot.ordinary_branch_count > 0) {
                snapshot.phase = "ordinary_tree";
            } else if (snapshot.gini_branch_count > 0) {
                snapshot.phase = "gini_branching";
            } else {
                snapshot.phase = "early_tree";
            }
            const double now_seconds = snapshot.observation_time_seconds;
            {
                std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
                double maximum_delay = 0.0;
                double oldest_delay = 0.0;
                long long open_siblings = 0;
                for (const auto& item : state->node_metadata) {
                    const GlobalGiniNodeMetadata& metadata = item.second;
                    if (!metadata.created_by_gini_branch ||
                        metadata.first_process_time >= 0.0) {
                        continue;
                    }
                    ++open_siblings;
                    const double delay = std::max(
                        0.0, now_seconds - metadata.creation_time);
                    maximum_delay = std::max(maximum_delay, delay);
                    oldest_delay = std::max(oldest_delay, delay);
                }
                snapshot.current_open_gini_siblings = open_siblings;
                snapshot.gini_sibling_delay_available = open_siblings > 0;
                snapshot.oldest_gini_sibling_delay_seconds = oldest_delay;
                snapshot.maximum_gini_sibling_delay_seconds = maximum_delay;
            }
            state->dense_progress->observe(snapshot);
            const double instrumentation_seconds =
                std::chrono::duration<double>(
                    std::chrono::steady_clock::now() - instrumentation_start)
                    .count();
            state->dense_progress->noteCallbackInvocation(
                instrumentation_seconds);
        }
        if (std::isfinite(bound)) {
            std::lock_guard<std::mutex> lock(state->trace_mutex);
            if (bound + 1e-7 < state->last_global_bound) {
                state->bound_monotone.store(false);
            }
            state->last_global_bound = std::max(state->last_global_bound, bound);
            if (state->bound_trace && !state->dense_progress) {
                *state->bound_trace << std::setprecision(17)
                    << globalTreeElapsed(*state) << ',' << bound << ','
                    << native_incumbent << ',' << state->verified_incumbent << ','
                    << (std::isfinite(native_incumbent)
                            ? std::max(0.0, native_incumbent - bound)
                            : std::numeric_limits<double>::quiet_NaN())
                    << ',' << nodes << ',' << nodes_left << ',' << iterations
                    << ",global_progress\n";
                state->bound_trace->flush();
            }
            if (state->memory_trace && !state->dense_progress) {
                *state->memory_trace << std::setprecision(17)
                    << csvCell(state->run_id) << ',' << globalTreeElapsed(*state)
                    << ',' << nodes << ',' << nodes_left << ',' << iterations
                    << ",,generic_callback_does_not_expose_tree_memory;parse_cplex_log\n";
                state->memory_trace->flush();
            }
        }
        return 0;
    }

    if (contextid == kContextCandidate) {
        ++state->candidate_calls;
        double objective = std::numeric_limits<double>::quiet_NaN();
        std::vector<double> point(static_cast<std::size_t>(state->ncols), 0.0);
        if (state->ncols > 0) {
            state->api->callbackgetcandidatepoint(
                context, point.data(), 0, state->ncols - 1, &objective);
        }
        if (state->bound_trace && !state->dense_progress) {
            std::lock_guard<std::mutex> lock(state->trace_mutex);
            *state->bound_trace << std::setprecision(17)
                << globalTreeElapsed(*state) << ','
                << infoDouble(kCallbackInfoBestBnd,
                              std::numeric_limits<double>::quiet_NaN()) << ','
                << objective << ',' << state->verified_incumbent << ",,"
                << infoLong(kCallbackInfoNodeCount) << ','
                << infoLong(kCallbackInfoNodesLeft) << ','
                << infoLong(kCallbackInfoIterationCount)
                << ",native_candidate\n";
            state->bound_trace->flush();
        }
        return 0;
    }

    if (contextid == kContextRelaxation) {
        ++state->relaxation_calls;
        const CPXLONG uid = infoLong(kCallbackInfoNodeUid);
        const CPXLONG depth = infoLong(kCallbackInfoNodeDepth);
        const CPXLONG nodes = infoLong(kCallbackInfoNodeCount);
        const CPXLONG nodes_left = infoLong(kCallbackInfoNodesLeft);
        const CPXLONG iterations = infoLong(kCallbackInfoIterationCount);
        if (uid < 0 || depth < 0 || nodes < 0) {
            ++state->node_info_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        double lower = 0.0;
        double upper = 0.0;
        if (state->api->callbackgetlocallb(
                context, &lower, state->g_col, state->g_col) != 0 ||
            state->api->callbackgetlocalub(
                context, &upper, state->g_col, state->g_col) != 0 ||
            !std::isfinite(lower) || !std::isfinite(upper) ||
            upper < lower - 1e-9) {
            ++state->local_bound_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        double relaxation = std::numeric_limits<double>::quiet_NaN();
        std::vector<double> relaxation_point(
            static_cast<std::size_t>(state->ncols), 0.0);
        if (state->api->callbackgetrelaxationpoint(
                context, relaxation_point.data(), 0, state->ncols - 1,
                &relaxation) != 0 || !std::isfinite(relaxation)) {
            ++state->child_estimate_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        GlobalGiniNodeMetadata metadata;
        std::string metadata_failure;
        if (!snapshotGlobalNode(*state, uid, depth, nodes, lower, upper,
                                metadata, metadata_failure)) {
            ++state->node_info_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        {
            std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
            auto found = state->node_metadata.find(uid);
            if (found == state->node_metadata.end()) {
                ++state->node_info_api_failures;
                abortGlobalTreeCallback(*state, context);
                return 0;
            }
            ++found->second.relaxation_passes;
            metadata = found->second;
        }
        const double global_bound = infoDouble(
            kCallbackInfoBestBnd, std::numeric_limits<double>::quiet_NaN());
        const double native_incumbent = infoDouble(
            kCallbackInfoBestSol, std::numeric_limits<double>::infinity());

        // GLOBAL_PROGRESS is intentionally sparse in CPLEX, even while a
        // one-thread traditional tree is processing thousands of nodes.  The
        // documented RELAXATION context is already required by the Tailored
        // algorithm, so take the same callback-safe, read-only progress
        // snapshot here before any row or branch action.  This instrumentation
        // subpath performs information reads and recorder updates only.
        if (state->dense_progress) {
            const auto instrumentation_start =
                std::chrono::steady_clock::now();
            DenseProgressSnapshot snapshot;
            snapshot.callback_invocation_sequence =
                state->dense_progress->stats().callback_invocation_count + 1;
            snapshot.observation_time_seconds = globalTreeElapsed(*state);
            snapshot.callback_context = "relaxation";
            snapshot.observation_source =
                "cplex_generic_relaxation_read_only_progress";
            double deterministic_time = 0.0;
            if (state->api->callbackgetinfodbl(
                    context, kCallbackInfoDeterministicTime,
                    &deterministic_time) == 0 &&
                std::isfinite(deterministic_time)) {
                snapshot.deterministic_time_available = true;
                snapshot.deterministic_time = deterministic_time;
            }
            snapshot.native_best_bound_available =
                std::isfinite(global_bound) &&
                std::fabs(global_bound) < kCplexInfinityBound;
            snapshot.native_best_bound = global_bound;
            snapshot.native_incumbent_available =
                std::isfinite(native_incumbent) &&
                std::fabs(native_incumbent) < kCplexInfinityBound;
            snapshot.native_incumbent = native_incumbent;
            snapshot.verified_upper_bound_available = true;
            snapshot.verified_upper_bound = state->verified_incumbent;
            snapshot.processed_nodes_available = nodes >= 0;
            snapshot.processed_nodes = nodes;
            snapshot.open_nodes_available = nodes_left >= 0;
            snapshot.open_nodes = nodes_left;
            snapshot.simplex_iterations_available = iterations >= 0;
            snapshot.simplex_iterations = iterations;
            snapshot.gini_branch_count = state->gini_branch_nodes.load();
            snapshot.ordinary_branch_count =
                state->ordinary_fallbacks.load();
            if (nodes <= 0) {
                snapshot.phase = iterations > 0 ? "root_cuts" : "root_lp";
            } else if (snapshot.ordinary_branch_count > 0) {
                snapshot.phase = "ordinary_tree";
            } else if (snapshot.gini_branch_count > 0) {
                snapshot.phase = "gini_branching";
            } else {
                snapshot.phase = "early_tree";
            }
            const double now_seconds = snapshot.observation_time_seconds;
            {
                std::lock_guard<std::mutex> lock(
                    state->node_metadata_mutex);
                double maximum_delay = 0.0;
                double oldest_delay = 0.0;
                long long open_siblings = 0;
                for (const auto& item : state->node_metadata) {
                    const GlobalGiniNodeMetadata& sibling = item.second;
                    if (!sibling.created_by_gini_branch ||
                        sibling.first_process_time >= 0.0) {
                        continue;
                    }
                    ++open_siblings;
                    const double delay = std::max(
                        0.0, now_seconds - sibling.creation_time);
                    maximum_delay = std::max(maximum_delay, delay);
                    oldest_delay = std::max(oldest_delay, delay);
                }
                snapshot.current_open_gini_siblings = open_siblings;
                snapshot.gini_sibling_delay_available = open_siblings > 0;
                snapshot.oldest_gini_sibling_delay_seconds = oldest_delay;
                snapshot.maximum_gini_sibling_delay_seconds = maximum_delay;
            }
            state->dense_progress->observe(snapshot);
            state->dense_progress->noteCallbackInvocation(
                std::chrono::duration<double>(
                    std::chrono::steady_clock::now() -
                    instrumentation_start).count());
        }

        if (metadata.phase == GlobalLocalRowPhase::PendingFirstRelaxation) {
            const auto packing_start = std::chrono::steady_clock::now();
            PackedGlobalGiniChild local = packGlobalGiniChild(
                *state, lower, upper, true, true,
                metadata.effective_state.get());
            const double packing_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - packing_start).count();
            atomicAdd(state->callback_packing_seconds, packing_seconds);
            if (!local.valid) {
                ++state->local_row_failures;
                abortGlobalTreeCallback(*state, context);
                return 0;
            }
            int add_rc = 0;
            const auto api_start = std::chrono::steady_clock::now();
            if (!local.rhs.empty()) {
                std::vector<int> purgeable(local.rhs.size(), kUseCutForce);
                std::vector<int> local_flags(local.rhs.size(), 1);
                add_rc = state->api->callbackaddusercuts(
                    context, static_cast<int>(local.rhs.size()),
                    static_cast<int>(local.rmatind.size()), local.rhs.data(),
                    local.sense.data(), local.rmatbeg.data(),
                    local.rmatind.data(), local.rmatval.data(),
                    purgeable.data(), local_flags.data());
            }
            const double api_seconds = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - api_start).count();
            atomicAdd(state->local_row_api_seconds, api_seconds);
            if (add_rc != 0) {
                ++state->local_row_failures;
                abortGlobalTreeCallback(*state, context);
                return 0;
            }
            std::string merge_failure;
            {
                std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
                auto found = state->node_metadata.find(uid);
                const bool incremental =
                    state->options->global_gini_tree_row_attachment_mode ==
                    "exact-incremental-delta";
                if (found == state->node_metadata.end()) {
                    ++state->local_row_failures;
                    abortGlobalTreeCallback(*state, context);
                    return 0;
                }
                if (incremental) {
                    const auto merged = mergedCanonicalState(
                        found->second.effective_state,
                        local.canonical_rows_attached, {}, merge_failure);
                    if (!merged) {
                        ++state->local_row_failures;
                        abortGlobalTreeCallback(*state, context);
                        return 0;
                    }
                    found->second.effective_state = merged;
                }
                found->second.pending_post_rows =
                    local.canonical_rows_attached;
                found->second.pre_local_row_relaxation = relaxation;
                found->second.local_row_attach_time = globalTreeElapsed(*state);
                found->second.row_factory_seconds += local.factory_seconds;
                found->second.row_api_seconds += api_seconds;
                found->second.phase = local.rhs.empty()
                    ? GlobalLocalRowPhase::Ready
                    : GlobalLocalRowPhase::AwaitingPostRowReoptimization;
                if (local.rhs.empty()) {
                    found->second.post_local_row_relaxation = relaxation;
                    found->second.post_row_reoptimization_seen = true;
                    ++state->post_row_reoptimizations;
                }
                metadata = found->second;
            }
            state->local_rows_attached +=
                static_cast<long long>(local.rhs.size());
            state->theoretical_full_rows += local.theoretical_full_rows;
            state->exact_duplicate_rows_omitted +=
                local.exact_duplicate_rows_omitted;
            state->delta_rows_attached +=
                static_cast<long long>(local.rhs.size());
            writeRowDeltaAudit(*state, uid, metadata.parent_uid, local,
                               "deferred_first_relaxation_attach");
            if (state->post_row_trace) {
                std::lock_guard<std::mutex> lock(state->trace_mutex);
                *state->post_row_trace << std::setprecision(17)
                    << csvCell(state->run_id) << ',' << uid << ','
                    << metadata.parent_uid << ',' << depth << ','
                    << metadata.gini_generation << ','
                    << metadata.relaxation_passes << ',' << lower << ','
                    << upper << ',' << relaxation << ",," << local.rhs.size()
                    << ',' << local.exact_duplicate_rows_omitted << ','
                    << local.factory_seconds << ',' << api_seconds << ','
                    << (local.rhs.empty() ? "not_required_empty_delta"
                                          : "awaiting_reoptimization")
                    << '\n';
                state->post_row_trace->flush();
            }
            GlobalNodeEvent event;
            event.context = "relaxation";
            event.action = "attach_interval_local_rows";
            event.uid = uid;
            event.parent_uid = metadata.parent_uid;
            event.depth = depth;
            event.gini_generation = metadata.gini_generation;
            event.relaxation_pass = metadata.relaxation_passes;
            event.local_row_phase = localRowPhaseName(metadata.phase);
            event.lower = lower;
            event.upper = upper;
            event.relaxation = relaxation;
            event.global_bound = global_bound;
            event.native_incumbent = native_incumbent;
            event.node_count = nodes;
            event.nodes_left = nodes_left;
            event.iteration_count = iterations;
            event.lower_rc = add_rc;
            event.factory_seconds = local.factory_seconds;
            event.row_api_seconds = api_seconds;
            writeGlobalNodeEvent(*state, event, &local, nullptr);
            return 0;
        }

        if (metadata.phase ==
            GlobalLocalRowPhase::AwaitingPostRowReoptimization) {
            std::string post_row_failure;
            if (!canonicalRowsSatisfiedAtPoint(
                    *state, metadata.pending_post_rows, relaxation_point,
                    post_row_failure)) {
                ++state->post_row_reoptimization_failures;
                abortGlobalTreeCallback(*state, context);
                return 0;
            }
            {
                std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
                auto found = state->node_metadata.find(uid);
                if (found == state->node_metadata.end()) {
                    ++state->post_row_reoptimization_failures;
                    abortGlobalTreeCallback(*state, context);
                    return 0;
                }
                found->second.post_local_row_relaxation = relaxation;
                found->second.post_row_reoptimization_seen = true;
                found->second.phase = GlobalLocalRowPhase::Ready;
                found->second.pending_post_rows.clear();
                found->second.pending_post_rows.shrink_to_fit();
                metadata = found->second;
            }
            ++state->post_row_reoptimizations;
            if (state->post_row_trace) {
                std::lock_guard<std::mutex> lock(state->trace_mutex);
                *state->post_row_trace << std::setprecision(17)
                    << csvCell(state->run_id) << ',' << uid << ','
                    << metadata.parent_uid << ',' << depth << ','
                    << metadata.gini_generation << ','
                    << metadata.relaxation_passes << ',' << lower << ','
                    << upper << ',' << metadata.pre_local_row_relaxation << ','
                    << relaxation << ",,," << metadata.row_factory_seconds << ','
                    << metadata.row_api_seconds << ",passed\n";
                state->post_row_trace->flush();
            }
            GlobalNodeEvent event;
            event.context = "relaxation";
            event.action = "first_post_local_row_reoptimization";
            event.uid = uid;
            event.parent_uid = metadata.parent_uid;
            event.depth = depth;
            event.gini_generation = metadata.gini_generation;
            event.relaxation_pass = metadata.relaxation_passes;
            event.local_row_phase = localRowPhaseName(metadata.phase);
            event.lower = lower;
            event.upper = upper;
            event.relaxation = relaxation;
            event.global_bound = global_bound;
            event.native_incumbent = native_incumbent;
            event.node_count = nodes;
            event.nodes_left = nodes_left;
            event.iteration_count = iterations;
            writeGlobalNodeEvent(*state, event, nullptr, nullptr);
        }
        return 0;
    }

    if (contextid != kContextBranching) return 0;
    ++state->branch_calls;
    const CPXLONG uid = infoLong(kCallbackInfoNodeUid);
    const CPXLONG depth = infoLong(kCallbackInfoNodeDepth);
    const CPXLONG nodes = infoLong(kCallbackInfoNodeCount);
    const CPXLONG nodes_left = infoLong(kCallbackInfoNodesLeft);
    const CPXLONG iterations = infoLong(kCallbackInfoIterationCount);
    if (uid < 0 || depth < 0 || nodes < 0) {
        ++state->node_info_api_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    double lower = 0.0;
    double upper = 0.0;
    if (state->api->callbackgetlocallb(
            context, &lower, state->g_col, state->g_col) != 0 ||
        state->api->callbackgetlocalub(
            context, &upper, state->g_col, state->g_col) != 0 ||
        !std::isfinite(lower) || !std::isfinite(upper) ||
        upper < lower - 1e-9) {
        ++state->local_bound_api_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    GlobalGiniNodeMetadata metadata;
    std::string metadata_failure;
    if (!snapshotGlobalNode(*state, uid, depth, nodes, lower, upper,
                            metadata, metadata_failure)) {
        ++state->node_info_api_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    if (metadata.phase == GlobalLocalRowPhase::PendingFirstRelaxation) {
        ++state->post_row_reoptimization_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    int relaxation_status = 0;
    const int relaxation_status_rc = state->api->callbackgetrelaxationstatus(
        context, &relaxation_status, 0);
    const double global_bound = infoDouble(
        kCallbackInfoBestBnd, std::numeric_limits<double>::quiet_NaN());
    const double native_incumbent = infoDouble(
        kCallbackInfoBestSol, std::numeric_limits<double>::infinity());
    if (relaxation_status_rc != 0 ||
        (relaxation_status != kLpStatusOptimal &&
         relaxation_status != kLpStatusOptimalInfeasible)) {
        ++state->ordinary_fallbacks;
        ++state->nonoptimal_relaxation_fallbacks;
        if (metadata.terminal_gini_refinement) ++state->ordinary_after_terminal;
        else ++state->ordinary_before_terminal;
        GlobalNodeEvent event;
        event.context = "branching";
        event.action = "nonoptimal_relaxation_cplex_fallback_status_" +
            std::to_string(relaxation_status) + "_rc_" +
            std::to_string(relaxation_status_rc);
        event.uid = uid;
        event.parent_uid = metadata.parent_uid;
        event.depth = depth;
        event.gini_generation = metadata.gini_generation;
        event.relaxation_pass = metadata.relaxation_passes;
        event.local_row_phase = localRowPhaseName(metadata.phase);
        event.lower = lower;
        event.upper = upper;
        event.global_bound = global_bound;
        event.native_incumbent = native_incumbent;
        event.node_count = nodes;
        event.nodes_left = nodes_left;
        event.iteration_count = iterations;
        writeGlobalNodeEvent(*state, event, nullptr, nullptr);
        return 0;
    }
    std::vector<double> relaxation_point(
        static_cast<std::size_t>(state->ncols), 0.0);
    double relaxation = std::numeric_limits<double>::quiet_NaN();
    if (state->api->callbackgetrelaxationpoint(
            context, relaxation_point.data(), 0, state->ncols - 1,
            &relaxation) != 0 || !std::isfinite(relaxation)) {
        ++state->child_estimate_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    if (metadata.phase ==
        GlobalLocalRowPhase::AwaitingPostRowReoptimization) {
        std::string post_row_failure;
        if (!canonicalRowsSatisfiedAtPoint(
                *state, metadata.pending_post_rows, relaxation_point,
                post_row_failure)) {
            ++state->post_row_reoptimization_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        {
            std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
            auto found = state->node_metadata.find(uid);
            if (found == state->node_metadata.end() ||
                found->second.phase !=
                    GlobalLocalRowPhase::AwaitingPostRowReoptimization) {
                ++state->post_row_reoptimization_failures;
                abortGlobalTreeCallback(*state, context);
                return 0;
            }
            found->second.post_local_row_relaxation = relaxation;
            found->second.post_row_reoptimization_seen = true;
            found->second.phase = GlobalLocalRowPhase::Ready;
            found->second.pending_post_rows.clear();
            found->second.pending_post_rows.shrink_to_fit();
            metadata = found->second;
        }
        ++state->post_row_reoptimizations;
        if (state->post_row_trace) {
            std::lock_guard<std::mutex> lock(state->trace_mutex);
            *state->post_row_trace << std::setprecision(17)
                << csvCell(state->run_id) << ',' << uid << ','
                << metadata.parent_uid << ',' << depth << ','
                << metadata.gini_generation << ','
                << metadata.relaxation_passes << ',' << lower << ','
                << upper << ',' << metadata.pre_local_row_relaxation << ','
                << relaxation << ",,," << metadata.row_factory_seconds << ','
                << metadata.row_api_seconds
                << ",passed_at_branching_context\n";
            state->post_row_trace->flush();
        }
        GlobalNodeEvent post_event;
        post_event.context = "branching";
        post_event.action =
            "first_post_local_row_relaxation_at_branching_context";
        post_event.uid = uid;
        post_event.parent_uid = metadata.parent_uid;
        post_event.depth = depth;
        post_event.gini_generation = metadata.gini_generation;
        post_event.relaxation_pass = metadata.relaxation_passes;
        post_event.local_row_phase = localRowPhaseName(metadata.phase);
        post_event.lower = lower;
        post_event.upper = upper;
        post_event.relaxation = relaxation;
        post_event.global_bound = global_bound;
        post_event.native_incumbent = native_incumbent;
        post_event.node_count = nodes;
        post_event.nodes_left = nodes_left;
        post_event.iteration_count = iterations;
        writeGlobalNodeEvent(*state, post_event, nullptr, nullptr);
    }
    double split = 0.0;
    long long round19_generation = 0;
    if (!chooseGlobalGiniSplit(*state, lower, upper, depth, split,
                               round19_generation)) {
        ++state->ordinary_fallbacks;
        ++state->ordinary_after_terminal;
        {
            std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
            auto found = state->node_metadata.find(uid);
            if (found != state->node_metadata.end()) {
                found->second.terminal_gini_refinement = true;
                metadata = found->second;
            }
        }
        GlobalNodeEvent event;
        event.context = "branching";
        event.action = "ordinary_cplex_branch_fallback";
        event.uid = uid;
        event.parent_uid = metadata.parent_uid;
        event.depth = depth;
        event.gini_generation = metadata.gini_generation;
        event.relaxation_pass = metadata.relaxation_passes;
        event.local_row_phase = localRowPhaseName(metadata.phase);
        event.lower = lower;
        event.upper = upper;
        event.relaxation = relaxation;
        event.global_bound = global_bound;
        event.native_incumbent = native_incumbent;
        event.lower_estimate = relaxation;
        event.upper_estimate = relaxation;
        event.node_count = nodes;
        event.nodes_left = nodes_left;
        event.iteration_count = iterations;
        writeGlobalNodeEvent(*state, event, nullptr, nullptr);
        return 0;
    }
    const GiniIntervalGeometry parent{lower, upper};
    const std::vector<GiniIntervalGeometry> children = {
        {lower, split}, {split, upper}
    };
    std::string coverage_reason;
    if (!exactIntervalCoverage(parent, children, 1e-10, &coverage_reason)) {
        ++state->coverage_failures;
        state->branch_coverage_valid.store(false);
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    const bool eager =
        state->options->global_gini_tree_row_timing_mode == "eager";
    const auto packing_start = std::chrono::steady_clock::now();
    PackedGlobalGiniChild low = packGlobalGiniChild(
        *state, lower, split, true, eager, metadata.effective_state.get());
    PackedGlobalGiniChild high = packGlobalGiniChild(
        *state, split, upper, false, eager, metadata.effective_state.get());
    const double packing_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - packing_start).count();
    atomicAdd(state->callback_packing_seconds, packing_seconds);
    if (!low.valid || !high.valid) {
        ++state->local_row_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    const ChildDomainEstimate low_domain = computeChildDomainEstimate(
        *state->instance, *state->options, low.domain, lower, relaxation);
    const ChildDomainEstimate high_domain = computeChildDomainEstimate(
        *state->instance, *state->options, high.domain, split, relaxation);
    if (!low_domain.valid || !high_domain.valid) {
        ++state->child_estimate_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    const bool factory_estimate =
        state->options->global_gini_tree_child_estimate_mode ==
        "factory-domain";
    const double low_estimate = factory_estimate
        ? low_domain.final_estimate : relaxation;
    const double high_estimate = factory_estimate
        ? high_domain.final_estimate : relaxation;
    if (!std::isfinite(low_estimate) || !std::isfinite(high_estimate) ||
        low_estimate + 1e-10 < relaxation ||
        high_estimate + 1e-10 < relaxation) {
        ++state->child_estimate_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    int low_id = -1;
    int high_id = -1;
    const auto branch_api_start = std::chrono::steady_clock::now();
    const int make_low_rc = state->api->callbackmakebranch(
        context, static_cast<int>(low.varind.size()),
        low.varind.empty() ? nullptr : low.varind.data(),
        low.varlu.empty() ? nullptr : low.varlu.data(),
        low.varbd.empty() ? nullptr : low.varbd.data(),
        static_cast<int>(low.rhs.size()),
        static_cast<int>(low.rmatind.size()),
        low.rhs.empty() ? nullptr : low.rhs.data(),
        low.sense.empty() ? nullptr : low.sense.data(),
        low.rmatbeg.empty() ? nullptr : low.rmatbeg.data(),
        low.rmatind.empty() ? nullptr : low.rmatind.data(),
        low.rmatval.empty() ? nullptr : low.rmatval.data(),
        low_estimate, &low_id);
    const int make_high_rc = state->api->callbackmakebranch(
        context, static_cast<int>(high.varind.size()),
        high.varind.empty() ? nullptr : high.varind.data(),
        high.varlu.empty() ? nullptr : high.varlu.data(),
        high.varbd.empty() ? nullptr : high.varbd.data(),
        static_cast<int>(high.rhs.size()),
        static_cast<int>(high.rmatind.size()),
        high.rhs.empty() ? nullptr : high.rhs.data(),
        high.sense.empty() ? nullptr : high.sense.data(),
        high.rmatbeg.empty() ? nullptr : high.rmatbeg.data(),
        high.rmatind.empty() ? nullptr : high.rmatind.data(),
        high.rmatval.empty() ? nullptr : high.rmatval.data(),
        high_estimate, &high_id);
    const double branch_api_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - branch_api_start).count();
    atomicAdd(state->local_row_api_seconds, branch_api_seconds);
    if (make_low_rc != 0 || make_high_rc != 0 ||
        low_id < 0 || high_id < 0 || low_id == high_id) {
        ++state->local_row_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    const long long child_generation = metadata.gini_generation + 1;
    const double creation_time = globalTreeElapsed(*state);
    GlobalGiniNodeMetadata low_metadata;
    GlobalGiniNodeMetadata high_metadata;
    auto initializeChild = [&](GlobalGiniNodeMetadata& child,
                               int child_id,
                               int sibling_id,
                               double child_lower,
                               double child_upper,
                               double estimate,
                               const ChildDomainEstimate& domain_estimate,
                               const PackedGlobalGiniChild& packed) {
        child.uid = child_id;
        child.parent_uid = uid;
        child.sibling_uid = sibling_id;
        child.native_depth = depth + 1;
        child.gini_generation = child_generation;
        child.lower = child_lower;
        child.upper = child_upper;
        child.creation_time = creation_time;
        child.creation_node_count = nodes;
        child.child_estimate = estimate;
        child.domain_estimate = domain_estimate.domain_estimate;
        child.estimate_lift = estimate - relaxation;
        child.estimate_mode =
            state->options->global_gini_tree_child_estimate_mode;
        child.created_by_gini_branch = true;
        child.phase = eager ? GlobalLocalRowPhase::Ready
                            : GlobalLocalRowPhase::PendingFirstRelaxation;
        const bool incremental =
            state->options->global_gini_tree_row_attachment_mode ==
            "exact-incremental-delta";
        child.inherited_state = metadata.effective_state;
        child.effective_state = metadata.effective_state;
        std::string merge_failure;
        if (incremental) {
            child.effective_state = mergedCanonicalState(
                child.effective_state,
                eager ? packed.canonical_rows_attached
                      : std::vector<CanonicalLinearRow>{},
                packed.canonical_bounds_attached, merge_failure);
        }
    };
    initializeChild(low_metadata, low_id, high_id, lower, split,
                    low_estimate, low_domain, low);
    initializeChild(high_metadata, high_id, low_id, split, upper,
                    high_estimate, high_domain, high);
    if (!low_metadata.effective_state ||
        !low_metadata.effective_state->valid ||
        !high_metadata.effective_state ||
        !high_metadata.effective_state->valid) {
        ++state->local_row_failures;
        abortGlobalTreeCallback(*state, context);
        return 0;
    }
    {
        std::lock_guard<std::mutex> lock(state->node_metadata_mutex);
        if (state->node_metadata.count(low_id) != 0 ||
            state->node_metadata.count(high_id) != 0) {
            ++state->node_info_api_failures;
            abortGlobalTreeCallback(*state, context);
            return 0;
        }
        state->node_metadata.emplace(low_id, low_metadata);
        state->node_metadata.emplace(high_id, high_metadata);
    }
    ++state->gini_branch_nodes;
    state->gini_children_created += 2;
    state->local_bounds_attached += static_cast<long long>(
        low.varind.size() + high.varind.size());
    state->theoretical_full_bounds +=
        low.theoretical_full_bounds + high.theoretical_full_bounds;
    state->identical_bounds_omitted +=
        low.identical_bounds_omitted + high.identical_bounds_omitted;
    state->delta_bounds_attached += static_cast<long long>(
        low.varind.size() + high.varind.size());
    if (eager) {
        state->local_rows_attached += static_cast<long long>(
            low.rhs.size() + high.rhs.size());
        state->theoretical_full_rows +=
            low.theoretical_full_rows + high.theoretical_full_rows;
        state->exact_duplicate_rows_omitted +=
            low.exact_duplicate_rows_omitted +
            high.exact_duplicate_rows_omitted;
        state->delta_rows_attached += static_cast<long long>(
            low.rhs.size() + high.rhs.size());
    }
    if (std::fabs(low_estimate - high_estimate) <= 1e-12) {
        ++state->sibling_equal_estimate_pairs;
    } else {
        ++state->sibling_discriminated_pairs;
    }
    long long previous = state->max_gini_generation.load();
    while (child_generation > previous &&
           !state->max_gini_generation.compare_exchange_weak(
               previous, child_generation)) {}
    double unset = -1.0;
    state->first_gini_branch_time.compare_exchange_strong(
        unset, creation_time);
    writeRowDeltaAudit(*state, low_id, uid, low,
                       eager ? "eager_branch_attach" : "branch_bounds_only");
    writeRowDeltaAudit(*state, high_id, uid, high,
                       eager ? "eager_branch_attach" : "branch_bounds_only");
    if (state->topology_trace) {
        std::lock_guard<std::mutex> lock(state->trace_mutex);
        *state->topology_trace << std::setprecision(17)
            << csvCell(state->run_id) << ',' << uid << ','
            << metadata.parent_uid << ',' << depth << ','
            << metadata.gini_generation << ',' << child_generation << ','
            << lower << ',' << upper << ',' << split << ',' << relaxation << ','
            << low_id << ','
            << lower << ',' << split << ',' << low_estimate << ','
            << low_domain.gamma_floor_component << ','
            << low_domain.weighted_penalty_lower << ','
            << low_domain.domain_estimate << ',' << low_domain.lift_over_parent
            << ',' << csvCell(joinDoubles(
                    low_domain.station_deviation_lower, "|", 1)) << ','
            << high_id << ',' << split << ',' << upper << ','
            << high_estimate << ',' << high_domain.gamma_floor_component << ','
            << high_domain.weighted_penalty_lower << ','
            << high_domain.domain_estimate << ','
            << high_domain.lift_over_parent << ',' << csvCell(joinDoubles(
                    high_domain.station_deviation_lower, "|", 1)) << ','
            << csvCell(state->options->global_gini_tree_child_estimate_mode)
            << ',' << (std::fabs(low_estimate - high_estimate) > 1e-12
                           ? "true" : "false")
            << ',' << creation_time << ',' << nodes << ',' << nodes_left << ','
            << iterations << ",passed,\n";
        state->topology_trace->flush();
    }
    GlobalNodeEvent event;
    event.context = "branching";
    event.action = "recursive_gini_split";
    event.uid = uid;
    event.parent_uid = metadata.parent_uid;
    event.depth = depth;
    event.gini_generation = metadata.gini_generation;
    event.relaxation_pass = metadata.relaxation_passes;
    event.local_row_phase = localRowPhaseName(metadata.phase);
    event.lower = lower;
    event.upper = upper;
    event.relaxation = relaxation;
    event.global_bound = global_bound;
    event.native_incumbent = native_incumbent;
    event.split = split;
    event.lower_child_upper = split;
    event.upper_child_lower = split;
    event.lower_estimate = low_estimate;
    event.upper_estimate = high_estimate;
    event.lower_rc = make_low_rc;
    event.upper_rc = make_high_rc;
    event.lower_id = low_id;
    event.upper_id = high_id;
    event.node_count = nodes;
    event.nodes_left = nodes_left;
    event.iteration_count = iterations;
    event.factory_seconds = low.factory_seconds + high.factory_seconds;
    event.row_api_seconds = branch_api_seconds;
    writeGlobalNodeEvent(*state, event, &low, &high);
    return 0;
}

struct PlainProgressCallbackState {
    Api* api = nullptr;
    DenseProgressRecorder* recorder = nullptr;
    std::chrono::steady_clock::time_point start =
        std::chrono::steady_clock::now();
};

int __stdcall plainDenseProgressCallback(CPXCALLBACKCONTEXTptr context,
                                         CPXLONG contextid,
                                         void* userhandle) {
    auto* state = static_cast<PlainProgressCallbackState*>(userhandle);
    if (!state || !state->api || !state->recorder ||
        (contextid != kContextGlobalProgress &&
         contextid != kContextLocalProgress)) {
        return 0;
    }
    const auto instrumentation_start = std::chrono::steady_clock::now();
    DenseProgressSnapshot snapshot;
    snapshot.callback_invocation_sequence =
        state->recorder->stats().callback_invocation_count + 1;
    snapshot.observation_time_seconds = std::chrono::duration<double>(
        instrumentation_start - state->start).count();
    const bool global_progress = contextid == kContextGlobalProgress;
    snapshot.callback_context = global_progress
        ? "global_progress" : "local_progress";
    snapshot.observation_source = global_progress
        ? "cplex_generic_global_progress"
        : "cplex_generic_local_progress";

    CPXLONG long_value = 0;
    if (state->api->callbackgetinfolong(
            context, kCallbackInfoNodeCount, &long_value) == 0) {
        snapshot.processed_nodes_available = true;
        snapshot.processed_nodes = long_value;
    }
    if (state->api->callbackgetinfolong(
            context, kCallbackInfoNodesLeft, &long_value) == 0) {
        snapshot.open_nodes_available = true;
        snapshot.open_nodes = long_value;
    }
    if (state->api->callbackgetinfolong(
            context, kCallbackInfoIterationCount, &long_value) == 0) {
        snapshot.simplex_iterations_available = true;
        snapshot.simplex_iterations = long_value;
    }
    double double_value = 0.0;
    if (state->api->callbackgetinfodbl(
            context, kCallbackInfoBestBnd, &double_value) == 0 &&
        std::isfinite(double_value) &&
        std::fabs(double_value) < kCplexInfinityBound) {
        snapshot.native_best_bound_available = true;
        snapshot.native_best_bound = double_value;
    }
    if (state->api->callbackgetinfodbl(
            context, kCallbackInfoBestSol, &double_value) == 0 &&
        std::isfinite(double_value) &&
        std::fabs(double_value) < kCplexInfinityBound) {
        snapshot.native_incumbent_available = true;
        snapshot.native_incumbent = double_value;
    }
    if (state->api->callbackgetinfodbl(
            context, kCallbackInfoDeterministicTime, &double_value) == 0 &&
        std::isfinite(double_value)) {
        snapshot.deterministic_time_available = true;
        snapshot.deterministic_time = double_value;
    }
    snapshot.verified_upper_bound_available =
        state->recorder->config().verified_upper_bound_available;
    snapshot.verified_upper_bound =
        state->recorder->config().verified_upper_bound;
    if (!snapshot.processed_nodes_available || snapshot.processed_nodes == 0) {
        snapshot.phase = snapshot.simplex_iterations_available &&
                                 snapshot.simplex_iterations > 0
            ? "root_cuts" : "root_lp";
    } else {
        snapshot.phase = "ordinary_tree";
    }
    state->recorder->observe(snapshot);
    const double instrumentation_seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - instrumentation_start).count();
    state->recorder->noteCallbackInvocation(instrumentation_seconds);
    return 0;
}
#endif

} // namespace

TailoredBCCplexApiProbe probeTailoredBCCplexApi() {
    TailoredBCCplexApiProbe probe;
#ifdef _WIN32
    const std::filesystem::path dll_path = defaultCplexDllPath();
    probe.dll_path = dll_path.string();
    probe.dll_found = std::filesystem::exists(dll_path) || dll_path.filename() == dll_path;
    Api api;
    std::string fail;
    if (!loadApi(api, fail)) {
        probe.fail_reason = fail;
        return probe;
    }
    probe.required_symbols_found = true;
    probe.callbacks_available = true;
    probe.fail_reason = "none";
    if (api.dll) FreeLibrary(api.dll);
#else
    probe.fail_reason = "cplex_dynamic_callbacks_supported_only_on_windows";
#endif
    return probe;
}

PlainCplexApiSolveResult solvePlainCplexWithStrictApi(
    const std::filesystem::path& lp_path,
    double time_limit_seconds,
    int threads,
    const std::filesystem::path& log_path,
    const DenseProgressConfig& dense_progress) {
    PlainCplexApiSolveResult out;
    out.attempted = true;
    out.threads_requested = std::max(1, threads);
    out.time_limit_requested = time_limit_seconds;
    out.log_path = log_path.string();
    out.dense_progress_raw_event_path =
        dense_progress.raw_event_path.string();
    if (!std::isfinite(time_limit_seconds) || time_limit_seconds <= 0.0) {
        out.fail_reason =
            "strict_native_deadline_must_be_positive_and_finite";
        return out;
    }
#ifdef _WIN32
    Api api;
    std::string fail;
    if (!loadApi(api, fail)) {
        out.fail_reason = fail;
        return out;
    }
    out.available = true;
    CPXENVptr env = nullptr;
    CPXLPptr lp = nullptr;
    auto cleanup = [&]() {
        if (lp != nullptr) {
            out.native.free_problem_return_code = api.freeprob(env, &lp);
            ++out.freeprob_count;
        }
        if (env != nullptr) {
            out.native.close_environment_return_code = api.close(&env);
            ++out.close_count;
        }
        if (api.dll) FreeLibrary(api.dll);
        out.lifecycle_valid = out.environment_count == 1 &&
            out.problem_count == 1 && out.model_read_count == 1 &&
            out.mipopt_count == 1 && out.freeprob_count == 1 &&
            out.close_count == 1 &&
            out.native.free_problem_return_code == 0 &&
            out.native.close_environment_return_code == 0;
    };

    int status = 0;
    env = api.open(&status);
    if (!env || status != 0) {
        out.fail_reason = "CPXopenCPLEX_failed:" + std::to_string(status);
        if (api.dll) FreeLibrary(api.dll);
        return out;
    }
    ++out.environment_count;
    if (!log_path.empty()) {
        if (log_path.has_parent_path()) {
            std::filesystem::create_directories(log_path.parent_path());
        }
        out.log_set_return_code = api.setlogfilename(
            env, log_path.string().c_str(), "w");
        if (out.log_set_return_code != 0) {
            out.fail_reason = "CPXsetlogfilename_failed:" +
                std::to_string(out.log_set_return_code);
            cleanup();
            return out;
        }
    } else {
        out.log_set_return_code = 0;
    }
    lp = api.createprob(env, &status, "plain_cplex_strict");
    if (!lp || status != 0) {
        out.fail_reason = "CPXcreateprob_failed:" + std::to_string(status);
        cleanup();
        return out;
    }
    ++out.problem_count;
    status = api.readcopyprob(env, lp, lp_path.string().c_str(), nullptr);
    if (status != 0) {
        out.fail_reason = "CPXreadcopyprob_failed:" + std::to_string(status);
        cleanup();
        return out;
    }
    ++out.model_read_count;
    out.model_columns = api.getnumcols(env, lp);
    out.model_rows = api.getnumrows(env, lp);
    out.model_nonzeros = static_cast<long long>(api.getnumnz(env, lp));
    out.model_writer_fingerprint = fileFingerprint(lp_path);

    api.setintparam(env, kParamScreenOutput, 1);
    api.setintparam(env, kParamMipDisplay, 2);
    out.threads_set_return_code = api.setintparam(
        env, kParamThreads, out.threads_requested);
    out.presolve_set_return_code = api.setintparam(
        env, kParamPreprocessingPresolve, out.presolve_requested);
    out.search_set_return_code = api.setintparam(
        env, kParamMipStrategySearch, out.search_requested);
    out.node_select_set_return_code = api.setintparam(
        env, kParamMipStrategyNodeSelect, out.node_select_requested);
    if (time_limit_seconds > 0.0) {
        out.time_limit_set_return_code = api.setdblparam(
            env, kParamTimeLimit, time_limit_seconds);
    } else {
        out.time_limit_set_return_code = 0;
    }
    CPXINT int_value = 0;
    out.threads_get_return_code = api.getintparam(
        env, kParamThreads, &int_value);
    out.threads_effective = int_value;
    out.presolve_get_return_code = api.getintparam(
        env, kParamPreprocessingPresolve, &int_value);
    out.presolve_effective = int_value;
    out.search_get_return_code = api.getintparam(
        env, kParamMipStrategySearch, &int_value);
    out.search_effective = int_value;
    out.node_select_get_return_code = api.getintparam(
        env, kParamMipStrategyNodeSelect, &int_value);
    out.node_select_effective = int_value;
    out.time_limit_get_return_code = api.getdblparam(
        env, kParamTimeLimit, &out.time_limit_effective);
    const bool strict_gaps_ok = configureStrictMipGaps(api, env, out.native);
    const bool required_parameters_ok =
        out.threads_set_return_code == 0 &&
        out.threads_get_return_code == 0 &&
        out.threads_effective == out.threads_requested &&
        out.presolve_set_return_code == 0 &&
        out.presolve_get_return_code == 0 && out.presolve_effective == 1 &&
        out.search_set_return_code == 0 &&
        out.search_get_return_code == 0 &&
        out.search_effective == kMipSearchTraditional &&
        out.node_select_set_return_code == 0 &&
        out.node_select_get_return_code == 0 &&
        out.node_select_effective == kNodeSelectBestBound &&
        out.time_limit_set_return_code == 0 &&
        out.time_limit_get_return_code == 0 &&
        (time_limit_seconds <= 0.0 ||
         out.time_limit_effective == time_limit_seconds) && strict_gaps_ok;
    if (!required_parameters_ok) {
        out.fail_reason = "strict_plain_required_parameter_round_trip_failed";
        cleanup();
        return out;
    }

    const std::vector<std::string> names = getColumnNames(
        api, env, lp, out.model_columns);
    out.variable_domain_fingerprint = variableDomainFingerprint(
        api, env, lp, names);
    DenseProgressConfig configured_progress = dense_progress;
    configured_progress.model_rows = out.model_rows;
    configured_progress.model_columns = out.model_columns;
    configured_progress.model_nonzeros = out.model_nonzeros;
    std::unique_ptr<DenseProgressRecorder> progress_recorder;
    PlainProgressCallbackState progress_state;
    if (configured_progress.enabled) {
        if (configured_progress.raw_event_path.empty()) {
            out.fail_reason = "dense_progress_raw_event_path_empty";
            cleanup();
            return out;
        }
        progress_recorder = std::make_unique<DenseProgressRecorder>(
            configured_progress);
        progress_state.api = &api;
        progress_state.recorder = progress_recorder.get();
        progress_state.start = std::chrono::steady_clock::now();
        const int callback_rc = api.callbacksetfunc(
            env, lp, kContextGlobalProgress | kContextLocalProgress,
            plainDenseProgressCallback, &progress_state);
        if (callback_rc != 0) {
            out.fail_reason = "CPXcallbacksetfunc_dense_progress_failed:" +
                std::to_string(callback_rc);
            cleanup();
            return out;
        }
        const DenseProgressReadOnlyPolicy policy =
            denseProgressReadOnlyPolicy();
        out.dense_progress_read_only_contract =
            !policy.may_add_rows && !policy.may_branch &&
            !policy.may_reject_candidate && !policy.may_abort &&
            !policy.may_change_parameters &&
            !policy.may_call_auxiliary_optimizer;
    }
    ++out.mipopt_count;
    status = api.mipopt(env, lp);
    captureNativeMipEvidence(api, env, lp, status, out.native);
    out.node_count = static_cast<long long>(api.getnodecnt(env, lp));
    out.open_node_count = static_cast<long long>(api.getnodeleftcnt(env, lp));
    out.simplex_iterations = static_cast<long long>(api.getmipitcnt(env, lp));
    out.native_solution_count = api.getsolnpoolnumsolns(env, lp);
    out.native_cut_counts = collectNativeCutCounts(api, env, lp);
    if (out.native.objective_available && out.model_columns > 0) {
        std::vector<double> values(
            static_cast<std::size_t>(out.model_columns), 0.0);
        if (api.getx(env, lp, values.data(), 0, out.model_columns - 1) == 0) {
            for (int column = 0; column < out.model_columns; ++column) {
                const std::string& name = names[static_cast<std::size_t>(column)];
                if (!name.empty()) {
                    out.values[name] = values[static_cast<std::size_t>(column)];
                }
            }
        }
    }
    out.solved = out.native.solve_returned &&
        out.native.mipopt_return_code == 0 && out.native.status_code != 0;
    if (progress_recorder) {
        DenseProgressSnapshot final;
        final.observation_time_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - progress_state.start).count();
        final.callback_invocation_sequence =
            progress_recorder->stats().callback_invocation_count;
        final.native_best_bound_available = out.native.best_bound_available;
        final.native_best_bound = out.native.best_bound;
        final.native_incumbent_available = out.native.objective_available;
        final.native_incumbent = out.native.objective;
        final.verified_upper_bound_available =
            configured_progress.verified_upper_bound_available;
        final.verified_upper_bound =
            configured_progress.verified_upper_bound;
        final.processed_nodes_available = out.node_count >= 0;
        final.processed_nodes = out.node_count;
        final.open_nodes_available = out.open_node_count >= 0;
        final.open_nodes = out.open_node_count;
        final.native_solution_count_available =
            out.native_solution_count >= 0;
        final.native_solution_count = out.native_solution_count;
        final.simplex_iterations_available = out.simplex_iterations >= 0;
        final.simplex_iterations = out.simplex_iterations;
        progress_recorder->appendSolverFinal(final);
    }
    cleanup();
    if (progress_recorder) {
        progress_recorder->flush();
        out.dense_progress = progress_recorder->stats();
    }
    if (!out.lifecycle_valid && out.fail_reason.empty()) {
        out.fail_reason = "strict_plain_lifecycle_incomplete";
    } else if (!out.solved && out.fail_reason.empty()) {
        out.fail_reason = "CPXmipopt_failed:" +
            std::to_string(out.native.mipopt_return_code);
    }
#else
    (void)lp_path;
    (void)time_limit_seconds;
    (void)threads;
    (void)log_path;
    out.fail_reason = "cplex_dynamic_api_supported_only_on_windows";
#endif
    return out;
}

TailoredBCCplexApiSolveResult solveLpWithTailoredBCCplexApi(
    const std::filesystem::path& lp_path,
    double time_limit_seconds,
    int threads,
    double gamma_L,
    double gamma_U,
    bool add_redundant_gini_user_cut,
    bool enable_candidate_validation,
    bool enable_gini_branching,
    bool enable_branch_priorities,
    double gini_branch_min_width,
    const std::vector<int>& station_initial,
    const std::vector<int>& station_capacity,
    const std::vector<int>& station_target,
    const std::vector<double>& station_weight,
    const std::vector<int>& vehicle_capacity,
    const std::vector<double>& distance_matrix,
    int route_node_count,
    double total_time_limit,
    double handling_unit,
    const std::string& support_duration_cover_mode,
    int gini_subset_max_size,
    int gini_subset_max_cuts,
    int vector_route_cutset_max_size,
    int vector_route_cutset_max_cuts,
    double vector_route_cutset_min_violation,
    const std::string& separation_pacing,
    int separation_min_relaxation_calls,
    const std::string& callback_cut_profile,
    bool enable_local_centering,
    bool enable_subset_cross_h_centering,
    int subset_cross_h_max_size,
    int subset_cross_h_max_cuts,
    const std::string& subset_cross_h_separation_profile,
    bool enable_local_q_centering,
    double lambda,
    double cutoff_value,
    int vehicle_count,
    const std::filesystem::path& progress_log_path,
    double progress_interval_seconds,
    bool register_callbacks,
    const TailoredBCNativeCheckpointConfig& native_checkpoint) {
    TailoredBCCplexApiSolveResult out;
    out.attempted = true;
#ifdef _WIN32
    Api api;
    std::string fail;
    if (!loadApi(api, fail)) {
        out.fail_reason = fail;
        return out;
    }
    out.available = true;
    int status = 0;
    CPXENVptr env = api.open(&status);
    if (!env || status != 0) {
        out.fail_reason = "CPXopenCPLEX_failed:" + std::to_string(status);
        if (api.dll) FreeLibrary(api.dll);
        return out;
    }
    CPXLPptr lp = api.createprob(env, &status, "tailored_bc_lp");
    if (!lp || status != 0) {
        out.fail_reason = "CPXcreateprob_failed:" + std::to_string(status);
        api.close(&env);
        if (api.dll) FreeLibrary(api.dll);
        return out;
    }
    status = api.readcopyprob(env, lp, lp_path.string().c_str(), nullptr);
    if (status != 0) {
        out.fail_reason = "CPXreadcopyprob_failed:" + std::to_string(status);
        api.freeprob(env, &lp);
        api.close(&env);
        if (api.dll) FreeLibrary(api.dll);
        return out;
    }
    api.setintparam(env, kParamThreads, std::max(1, threads));
    // The caller captures stdout into the run-local log.  Keep native CPLEX
    // output enabled even for the static no-callback diagnostic path so that
    // presolve, cut, root-relaxation, memory, and terminal-status evidence is
    // not silently lost.
    api.setintparam(env, kParamScreenOutput, 1);
    api.setintparam(env, kParamMipDisplay, 2);
    out.native_mip_gap_param_id = kParamMipGap;
    out.native_mip_gap = 1e-8;
    out.native_mip_gap_set_rc =
        api.setdblparam(env, kParamMipGap, out.native_mip_gap);
    if (out.native_mip_gap_set_rc != 0) {
        out.best_bound_fail_reason =
            "CPX_PARAM_EPGAP_set_failed:" +
            std::to_string(out.native_mip_gap_set_rc);
    }
    if (enable_gini_branching) {
        api.setintparam(env, kParamMipStrategySearch, kMipSearchTraditional);
        api.setintparam(env, kParamPreprocessingPresolve, 0);
        api.setintparam(env, kParamMipStrategyHeuristicFreq, -1);
    }
    out.native_time_limit_param_id = kParamTimeLimit;
    out.native_time_limit_seconds = time_limit_seconds;
    if (time_limit_seconds > 0.0) {
        out.native_time_limit_set_rc =
            api.setdblparam(env, kParamTimeLimit, time_limit_seconds);
        if (out.native_time_limit_set_rc != 0) {
            out.best_bound_fail_reason =
                "CPX_PARAM_TILIM_set_failed:" +
                std::to_string(out.native_time_limit_set_rc);
        }
    }
    volatile int cplex_terminate_flag = 0;
    out.terminate_set_rc = api.setterminate(env, &cplex_terminate_flag);
    if (out.terminate_set_rc != 0 && out.best_bound_fail_reason.empty()) {
        out.best_bound_fail_reason =
            "CPXsetterminate_failed:" + std::to_string(out.terminate_set_rc);
    }
    const int ncols = api.getnumcols(env, lp);
    std::vector<std::string> names = getColumnNames(api, env, lp, ncols);
    if (enable_branch_priorities) {
        out.branch_priorities_applied =
            applyBranchPriorities(api, env, lp, names, out.branch_priority_status);
    } else {
        out.branch_priority_status = "disabled";
    }
    int g_col = -1;
    int w_gs_col = -1;
    int r_min_col = -1;
    int r_max_col = -1;
    for (int i = 0; i < ncols; ++i) {
        if (names[static_cast<std::size_t>(i)] == "G") {
            g_col = i;
        } else if (names[static_cast<std::size_t>(i)] == "W_GS") {
            w_gs_col = i;
        } else if (names[static_cast<std::size_t>(i)] == "r_min") {
            r_min_col = i;
        } else if (names[static_cast<std::size_t>(i)] == "r_max") {
            r_max_col = i;
        }
    }
    const int station_count =
        std::min(static_cast<int>(station_initial.size()),
                 static_cast<int>(station_capacity.size()));
    std::vector<int> y_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> r_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> e_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> t_sp_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> q_l1_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<std::vector<int>> h_cols(
        static_cast<std::size_t>(station_count),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    for (int i = 1; i < station_count; ++i) {
        std::vector<int> found = buildNameToIndexLookup(names, yNameForStation(i));
        if (!found.empty()) y_cols[static_cast<std::size_t>(i)] = found.front();
        found = buildNameToIndexLookup(names, rNameForStation(i));
        if (!found.empty()) r_cols[static_cast<std::size_t>(i)] = found.front();
        found = buildNameToIndexLookup(names, eNameForStation(i));
        if (!found.empty()) e_cols[static_cast<std::size_t>(i)] = found.front();
        found = buildNameToIndexLookup(names, "T_SP_" + std::to_string(i));
        if (!found.empty()) t_sp_cols[static_cast<std::size_t>(i)] = found.front();
        found = buildNameToIndexLookup(names, qL1NameForStation(i));
        if (!found.empty()) q_l1_cols[static_cast<std::size_t>(i)] = found.front();
    }
    for (int i = 1; i < station_count; ++i) {
        for (int j = i + 1; j < station_count; ++j) {
            std::vector<int> found = buildNameToIndexLookup(
                names, hNameForPair(i, j));
            if (!found.empty()) {
                const int col = found.front();
                h_cols[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)] = col;
                h_cols[static_cast<std::size_t>(j)][static_cast<std::size_t>(i)] = col;
            }
        }
    }
    std::vector<std::vector<int>> z_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    std::vector<std::vector<int>> p_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    std::vector<std::vector<int>> d_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    std::vector<std::vector<int>> load_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    std::vector<std::vector<std::vector<int>>> x_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<std::vector<int>>(
            static_cast<std::size_t>(std::max(0, route_node_count)),
            std::vector<int>(
                static_cast<std::size_t>(std::max(0, route_node_count)), -1)));
    for (int k = 0; k < vehicle_count; ++k) {
        for (int i = 1; i < station_count; ++i) {
            std::vector<int> found = buildNameToIndexLookup(
                names, zNameForVehicleStation(k, i));
            if (!found.empty()) {
                z_cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)] =
                    found.front();
            }
            found = buildNameToIndexLookup(names, pNameForVehicleStation(k, i));
            if (!found.empty()) {
                p_cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)] =
                    found.front();
            }
            found = buildNameToIndexLookup(names, dNameForVehicleStation(k, i));
            if (!found.empty()) {
                d_cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)] =
                    found.front();
            }
            found = buildNameToIndexLookup(names, loadNameForVehicleStation(k, i));
            if (!found.empty()) {
                load_cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)] =
                    found.front();
            }
        }
        for (int i = 0; i < route_node_count; ++i) {
            for (int j = 0; j < route_node_count; ++j) {
                if (i == j) continue;
                std::vector<int> found = buildNameToIndexLookup(
                    names, xNameForVehicleArc(k, i, j));
                if (!found.empty()) {
                    x_cols[static_cast<std::size_t>(k)]
                          [static_cast<std::size_t>(i)]
                          [static_cast<std::size_t>(j)] = found.front();
                }
            }
        }
    }
    CallbackState cb_state;
    cb_state.api = &api;
    cb_state.ncols = ncols;
    cb_state.col_names = names;
    cb_state.g_col = g_col;
    cb_state.w_gs_col = w_gs_col;
    cb_state.r_min_col = r_min_col;
    cb_state.r_max_col = r_max_col;
    cb_state.r_cols = std::move(r_cols);
    cb_state.e_cols = std::move(e_cols);
    cb_state.t_sp_cols = std::move(t_sp_cols);
    cb_state.q_l1_cols = std::move(q_l1_cols);
    cb_state.h_cols = std::move(h_cols);
    cb_state.y_cols = std::move(y_cols);
    cb_state.z_cols = std::move(z_cols);
    cb_state.x_cols = std::move(x_cols);
    cb_state.p_cols = std::move(p_cols);
    cb_state.d_cols = std::move(d_cols);
    cb_state.load_cols = std::move(load_cols);
    cb_state.station_initial = station_initial;
    cb_state.station_capacity = station_capacity;
    cb_state.station_target = station_target;
    cb_state.station_weight = station_weight;
    cb_state.vehicle_capacity = vehicle_capacity;
    cb_state.distance_matrix = distance_matrix;
    cb_state.node_count = route_node_count;
    cb_state.total_time_limit = total_time_limit;
    cb_state.handling_unit = handling_unit;
    cb_state.support_duration_cover_mode = support_duration_cover_mode;
    cb_state.gini_subset_max_size = gini_subset_max_size;
    cb_state.gini_subset_max_cuts = gini_subset_max_cuts;
    cb_state.vector_route_cutset_max_size = vector_route_cutset_max_size;
    cb_state.vector_route_cutset_max_cuts = vector_route_cutset_max_cuts;
    cb_state.vector_route_cutset_min_violation =
        std::max(0.0, vector_route_cutset_min_violation);
    cb_state.separation_pacing = separation_pacing;
    cb_state.separation_min_relaxation_calls =
        std::max(1, separation_min_relaxation_calls);
    cb_state.callback_cut_profile = callback_cut_profile.empty()
        ? "full"
        : callback_cut_profile;
    cb_state.enable_local_centering = enable_local_centering;
    cb_state.enable_subset_cross_h_centering = enable_subset_cross_h_centering;
    cb_state.subset_cross_h_max_size =
        std::min(4, std::max(1, subset_cross_h_max_size));
    cb_state.subset_cross_h_max_cuts =
        std::max(0, subset_cross_h_max_cuts);
    cb_state.subset_cross_h_separation_profile =
        subset_cross_h_separation_profile;
    cb_state.enable_local_q_centering = enable_local_q_centering;
    cb_state.lambda = lambda;
    cb_state.cutoff_value = cutoff_value;
    cb_state.gamma_L = gamma_L;
    cb_state.gamma_U = gamma_U;
    cb_state.add_gini_cut = add_redundant_gini_user_cut && g_col >= 0;
    cb_state.validate_candidates = enable_candidate_validation;
    cb_state.enable_gini_branch = enable_gini_branching;
    cb_state.gini_branch_min_width = std::max(1e-12, gini_branch_min_width);
    if (register_callbacks) {
        const CPXLONG mask = kContextRelaxation | kContextCandidate |
            kContextBranching | kContextGlobalProgress;
        status = api.callbacksetfunc(env, lp, mask, tailoredCallback, &cb_state);
        if (status != 0) {
            out.fail_reason = "CPXcallbacksetfunc_failed:" + std::to_string(status);
            api.freeprob(env, &lp);
            api.close(&env);
            if (api.dll) FreeLibrary(api.dll);
            return out;
        }
    }

    using SteadyClock = std::chrono::steady_clock;
    const auto solve_start = SteadyClock::now();
    cb_state.wall_start = solve_start;
    double terminate_after_seconds = 0.0;
    if (time_limit_seconds > 0.0) {
        const double grace =
            std::max(5.0, std::min(60.0, 0.10 * time_limit_seconds));
        cb_state.wall_time_limit_seconds = time_limit_seconds + grace;
        terminate_after_seconds = cb_state.wall_time_limit_seconds;
    }
    std::atomic<bool> stop_progress{false};
    std::thread progress_thread;
    std::atomic<bool> stop_terminator{false};
    std::atomic<bool> terminate_triggered{false};
    std::thread terminator_thread;
    std::mutex progress_mutex;
    long long checkpoint_rows = 0;
    std::uint64_t native_checkpoint_sequence = 0;
    double last_checkpoint_time = 0.0;
    const double heartbeat_seconds =
        progress_interval_seconds > 0.0 ? progress_interval_seconds : 30.0;

    auto userCutFamilyString = [&]() {
        std::ostringstream os;
        os << "gini_interval=" << cb_state.gini_interval_cuts_added.load()
           << ";visit_inventory_linking=" << cb_state.visit_inventory_cuts_added.load()
           << ";gini_subset_envelope="
           << cb_state.gini_subset_envelope_cuts_added.load()
           << ";low_gini_l1_centering=" << cb_state.low_gini_l1_cuts_added.load()
           << ";local_centering=" << cb_state.local_centering_cuts_added.load()
           << ";subset_cross_h_centering="
           << cb_state.subset_cross_h_centering_cuts_added.load()
           << ";local_q_centering=" << cb_state.local_q_centering_cuts_added.load()
           << ";gs_product_coupling=" << cb_state.gs_product_cuts_added.load()
           << ";disaggregated_sp_estimator=" << cb_state.disagg_sp_cuts_added.load()
           << ";vector_route_cutset=" << cb_state.vector_route_cutset_cuts_added.load()
           << ";variable_s_centering=" << cb_state.variable_s_centering_cuts_added.load()
           << ";subset_inventory_imbalance="
           << cb_state.subset_inventory_imbalance_cuts_added.load()
           << ";transfer_cutset=" << cb_state.transfer_cutset_cuts_added.load()
           << ";support_duration_pair="
           << cb_state.support_duration_pair_cuts_added.load()
           << ";support_duration_triple="
           << cb_state.support_duration_triple_cuts_added.load()
           << ";support_duration_quad="
           << cb_state.support_duration_quad_cuts_added.load()
           << ";support_duration_lifted="
           << cb_state.support_duration_lifted_cuts_added.load();
        return os.str();
    };
    auto violationFamilyString = [&]() {
        std::ostringstream os;
        os << "gini_subset_envelope="
           << cb_state.gini_subset_envelope_violations.load()
           << ";low_gini_l1_centering=" << cb_state.low_gini_l1_violations.load()
           << ";local_centering=" << cb_state.local_centering_violations.load()
           << ";subset_cross_h_centering="
           << cb_state.subset_cross_h_centering_violations.load()
           << ";local_q_centering=" << cb_state.local_q_centering_violations.load()
           << ";variable_s_centering="
           << cb_state.variable_s_centering_violations.load()
           << ";subset_inventory_imbalance="
           << cb_state.subset_inventory_imbalance_violations.load()
           << ";transfer_cutset=" << cb_state.transfer_cutset_violations.load()
           << ";support_duration_pair="
           << cb_state.support_duration_pair_violations.load()
           << ";support_duration_triple="
           << cb_state.support_duration_triple_violations.load()
           << ";support_duration_quad="
           << cb_state.support_duration_quad_violations.load()
           << ";support_duration_lifted="
           << cb_state.support_duration_lifted_violations.load();
        return os.str();
    };
    auto writeProgressRow =
        [&](const std::string& event,
            const std::string& solver_status,
            bool best_bound_available,
            double best_bound_value,
            bool bound_valid,
            long long node_count_value,
            const std::string& bound_fail_reason) {
            if (progress_log_path.empty()) return;
            const double elapsed =
                std::chrono::duration<double>(SteadyClock::now() - solve_start).count();
            bool effective_best_available = best_bound_available;
            double effective_best_bound = best_bound_value;
            if (!effective_best_available &&
                cb_state.native_best_bound_available.load()) {
                effective_best_available = true;
                effective_best_bound = cb_state.native_best_bound.load();
            }
            const bool incumbent_available =
                cb_state.native_incumbent_available.load();
            const double incumbent =
                incumbent_available ? cb_state.native_incumbent.load() : 0.0;
            const long long effective_node_count =
                node_count_value > 0
                    ? node_count_value
                    : cb_state.native_node_count.load();
            const double absolute_gap =
                effective_best_available && incumbent_available
                    ? std::max(0.0, incumbent - effective_best_bound)
                    : 0.0;
            const double relative_gap =
                incumbent_available && std::fabs(incumbent) > 1e-12
                    ? absolute_gap / std::fabs(incumbent)
                    : 0.0;
            const double last_improvement =
                cb_state.native_last_bound_improvement_time.load();
            const bool plateau =
                effective_best_available && last_improvement > 0.0 &&
                elapsed - last_improvement > std::max(60.0, 3.0 * heartbeat_seconds);
            std::lock_guard<std::mutex> guard(progress_mutex);
            std::ofstream progress(progress_log_path, std::ios::app);
            if (!progress) return;
            progress << std::setprecision(12)
                     << elapsed << ','
                     << event << ','
                     << '"' << solver_status << '"' << ','
                     << (effective_best_available ? effective_best_bound : 0.0) << ','
                     << (effective_best_available ? "true" : "false") << ','
                     << ((bound_valid || effective_best_available) ? "true" : "false") << ','
                     << (incumbent_available ? incumbent : 0.0) << ','
                     << (incumbent_available ? "true" : "false") << ','
                     << cutoff_value << ','
                     << (effective_best_available ? (cutoff_value - effective_best_bound) : 0.0)
                     << ','
                     << effective_node_count << ','
                     << (effective_best_available ? effective_best_bound : 0.0) << ','
                     << last_improvement << ','
                     << absolute_gap << ','
                     << relative_gap << ','
                     << (plateau ? "true" : "false") << ','
                     << cb_state.relaxation_calls.load() << ','
                     << cb_state.candidate_calls.load() << ','
                     << cb_state.branch_calls.load() << ','
                     << cb_state.progress_calls.load() << ','
                     << cb_state.callback_abort_requests.load() << ','
                     << cb_state.expensive_separation_calls.load() << ','
                     << cb_state.expensive_separation_skips.load() << ','
                     << '"' << cb_state.separation_pacing << '"' << ','
                     << '"' << userCutFamilyString() << '"' << ','
                     << '"' << violationFamilyString() << '"' << ','
                     << cb_state.gini_branches_created.load() << ','
                     << gamma_L << ','
                     << gamma_U << ','
                     << "\"tailored_bc_callback\"" << ','
                     << "\"original_fixed_interval\"" << ','
                     << (effective_best_available
                            ? "\"cplex_native_callback_info\""
                            : "\"heartbeat_activity_only\"") << ','
                     << '"' << bound_fail_reason << '"'
                     << '\n';
            ++checkpoint_rows;
            last_checkpoint_time = elapsed;
            if (native_checkpoint.enabled && effective_best_available &&
                !native_checkpoint.path.empty()) {
                NativeCheckpointRecord record;
                record.run_id = native_checkpoint.run_id;
                record.sequence = ++native_checkpoint_sequence;
                record.instance_hash = native_checkpoint.instance_hash;
                record.gamma_L = gamma_L;
                record.gamma_U = gamma_U;
                record.cutoff = cutoff_value;
                record.model_fingerprint = native_checkpoint.model_fingerprint;
                record.formulation_profile = native_checkpoint.formulation_profile;
                record.cplex_threads = std::max(1, threads);
                record.native_time_limit_param_id = out.native_time_limit_param_id;
                record.native_time_limit_seconds = out.native_time_limit_seconds;
                record.native_time_limit_set_rc = out.native_time_limit_set_rc;
                record.best_bound = effective_best_bound;
                std::string checkpoint_reason;
                writeNativeCheckpointAtomic(
                    native_checkpoint.path, record, &checkpoint_reason);
            }
        };

    if (register_callbacks && !progress_log_path.empty()) {
        try {
            if (!progress_log_path.parent_path().empty()) {
                std::filesystem::create_directories(progress_log_path.parent_path());
            }
            std::ofstream progress(progress_log_path, std::ios::out | std::ios::trunc);
            progress
                << "elapsed_seconds,event,cplex_status,best_bound,"
                   "best_bound_available,bound_valid,incumbent,"
                   "incumbent_available,cutoff_UB,gap_to_cutoff,node_count,"
                   "root_bound,last_bound_improvement_time,absolute_gap,"
                   "relative_gap,plateau_detected,"
                   "relaxation_callback_calls,candidate_callback_calls,"
                   "branch_callback_calls,progress_callback_calls,"
                   "callback_abort_requests,"
                   "expensive_separation_calls,expensive_separation_skips,"
                   "separation_pacing,"
                   "user_cuts_added_by_family,violations_by_family,"
                   "gini_branches_created,gamma_L,gamma_U,source_class,"
                   "bound_scope,progress_source,bound_fail_reason\n";
            progress.close();
            writeProgressRow("start", "running", false, 0.0, false, 0,
                             "best_bound_unavailable_before_mipopt");
            progress_thread = std::thread([&]() {
                while (!stop_progress.load()) {
                    std::this_thread::sleep_for(
                        std::chrono::duration<double>(heartbeat_seconds));
                    if (stop_progress.load()) break;
                    writeProgressRow("heartbeat", "running", false, 0.0, false, 0,
                                     "best_bound_unavailable_while_mipopt_running");
                }
            });
            out.checkpoint_log_written = true;
        } catch (const std::exception& e) {
            out.best_bound_fail_reason =
                std::string("progress_log_write_failed:") + e.what();
        }
    }

    if (terminate_after_seconds > 0.0 && out.terminate_set_rc == 0) {
        out.terminate_after_seconds = terminate_after_seconds;
        terminator_thread = std::thread([&]() {
            while (!stop_terminator.load()) {
                const double elapsed = std::chrono::duration<double>(
                    SteadyClock::now() - solve_start).count();
                if (elapsed >= terminate_after_seconds) {
                    cplex_terminate_flag = 1;
                    terminate_triggered.store(true);
                    cb_state.wall_time_abort.store(true);
                    break;
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(200));
            }
        });
    }

    status = api.mipopt(env, lp);
    stop_terminator.store(true);
    if (terminator_thread.joinable()) terminator_thread.join();
    stop_progress.store(true);
    if (progress_thread.joinable()) progress_thread.join();
    out.return_code = status;
    out.status_code = api.getstat(env, lp);
    out.callback_wall_time_abort = cb_state.wall_time_abort.load();
    out.callback_abort_requests = cb_state.callback_abort_requests.load();
    out.terminate_triggered = terminate_triggered.load();
    char statbuf[1024] = {0};
    if (api.getstatstring(env, out.status_code, statbuf)) {
        out.status = statbuf;
    } else {
        out.status = "status_code_" + std::to_string(out.status_code);
    }
    if (out.callback_wall_time_abort) {
        out.status = "callback_wall_time_abort:" + out.status;
    }
    double obj = 0.0;
    if (api.getobjval(env, lp, &obj) == 0) out.objective = obj;
    double bound = 0.0;
    const int best_bound_rc = api.getbestobjval(env, lp, &bound);
    if (best_bound_rc == 0 && std::isfinite(bound)) {
        out.best_bound = bound;
        out.best_bound_available = true;
        if (out.best_bound_fail_reason.empty()) out.best_bound_fail_reason = "none";
    } else {
        out.best_bound_fail_reason =
            "CPXgetbestobjval_unavailable:" + std::to_string(best_bound_rc);
    }
    out.node_count = static_cast<long long>(api.getnodecnt(env, lp));
    out.checkpoint_best_bound_available =
        cb_state.native_best_bound_available.load();
    out.checkpoint_best_bound = cb_state.native_best_bound.load();
    out.checkpoint_incumbent_available =
        cb_state.native_incumbent_available.load();
    out.checkpoint_incumbent = cb_state.native_incumbent.load();
    out.checkpoint_node_count = cb_state.native_node_count.load();
    if (!out.best_bound_available && out.checkpoint_best_bound_available) {
        out.best_bound = out.checkpoint_best_bound;
        out.best_bound_available = true;
        out.best_bound_fail_reason = "checkpoint_cplex_native_best_bound";
    }
    writeProgressRow("final", out.status, out.best_bound_available, out.best_bound,
                     out.best_bound_available, out.node_count,
                     out.best_bound_available ? "none" : out.best_bound_fail_reason);
    out.checkpoint_rows_written = checkpoint_rows;
    out.last_checkpoint_time = last_checkpoint_time;
    out.relaxation_callback_calls = cb_state.relaxation_calls.load();
    out.candidate_callback_calls = cb_state.candidate_calls.load();
    out.branch_callback_calls = cb_state.branch_calls.load();
    out.progress_callback_calls = cb_state.progress_calls.load();
    out.relaxation_vector_snapshot_available =
        cb_state.relaxation_vector_snapshot_available.load();
    out.relaxation_vector_api_called =
        cb_state.relaxation_vector_sample_attempted.load();
    out.relaxation_vector_api_return_code =
        cb_state.relaxation_vector_api_return_code.load();
    out.relaxation_vector_length_requested =
        cb_state.relaxation_vector_length_requested.load();
    out.relaxation_vector_length_returned =
        cb_state.relaxation_vector_length_returned.load();
    out.relaxation_vector_nonzero_values =
        cb_state.relaxation_vector_nonzero_values.load();
    out.relaxation_vector_objective =
        cb_state.relaxation_vector_objective.load();
    out.candidate_vector_snapshot_available =
        cb_state.candidate_vector_snapshot_available.load();
    out.candidate_vector_api_called =
        cb_state.candidate_vector_sample_attempted.load();
    out.candidate_vector_api_return_code =
        cb_state.candidate_vector_api_return_code.load();
    out.candidate_vector_length_requested =
        cb_state.candidate_vector_length_requested.load();
    out.candidate_vector_length_returned =
        cb_state.candidate_vector_length_returned.load();
    out.candidate_vector_nonzero_values =
        cb_state.candidate_vector_nonzero_values.load();
    out.candidate_vector_objective =
        cb_state.candidate_vector_objective.load();
    {
        std::lock_guard<std::mutex> lock(cb_state.vector_snapshot_mutex);
        out.relaxation_vector_sample_variable_names =
            cb_state.relaxation_vector_sample_variable_names.empty()
                ? "not_available"
                : cb_state.relaxation_vector_sample_variable_names;
        out.relaxation_vector_sample_variable_values =
            cb_state.relaxation_vector_sample_variable_values.empty()
                ? "not_available"
                : cb_state.relaxation_vector_sample_variable_values;
        out.relaxation_vector_full_variable_names =
            cb_state.relaxation_vector_full_variable_names.empty()
                ? "not_available"
                : cb_state.relaxation_vector_full_variable_names;
        out.relaxation_vector_full_variable_values =
            cb_state.relaxation_vector_full_variable_values.empty()
                ? "not_available"
                : cb_state.relaxation_vector_full_variable_values;
        out.relaxation_vector_failure_reason =
            cb_state.relaxation_vector_failure_reason.empty()
                ? (out.relaxation_vector_api_called
                       ? "unknown_failure"
                       : "relaxation_context_not_reached")
                : cb_state.relaxation_vector_failure_reason;
        out.candidate_vector_sample_variable_names =
            cb_state.candidate_vector_sample_variable_names.empty()
                ? "not_available"
                : cb_state.candidate_vector_sample_variable_names;
        out.candidate_vector_sample_variable_values =
            cb_state.candidate_vector_sample_variable_values.empty()
                ? "not_available"
                : cb_state.candidate_vector_sample_variable_values;
        out.candidate_vector_full_variable_names =
            cb_state.candidate_vector_full_variable_names.empty()
                ? "not_available"
                : cb_state.candidate_vector_full_variable_names;
        out.candidate_vector_full_variable_values =
            cb_state.candidate_vector_full_variable_values.empty()
                ? "not_available"
                : cb_state.candidate_vector_full_variable_values;
        out.candidate_vector_failure_reason =
            cb_state.candidate_vector_failure_reason.empty()
                ? (out.candidate_vector_api_called
                       ? "unknown_failure"
                       : "candidate_context_not_reached")
                : cb_state.candidate_vector_failure_reason;
    }
    out.user_cuts_added = cb_state.user_cuts_added.load();
    out.callback_gini_interval_cuts_added =
        cb_state.gini_interval_cuts_added.load();
    out.callback_visit_inventory_cuts_added =
        cb_state.visit_inventory_cuts_added.load();
    out.callback_gini_subset_envelope_cuts_added =
        cb_state.gini_subset_envelope_cuts_added.load();
    out.callback_gini_subset_envelope_candidates =
        cb_state.gini_subset_envelope_candidates.load();
    out.callback_gini_subset_envelope_violations =
        cb_state.gini_subset_envelope_violations.load();
    out.callback_gini_subset_envelope_max_violation =
        cb_state.gini_subset_envelope_max_violation.load();
    out.callback_expensive_separation_calls =
        cb_state.expensive_separation_calls.load();
    out.callback_expensive_separation_skips =
        cb_state.expensive_separation_skips.load();
    out.callback_low_gini_l1_cuts_added =
        cb_state.low_gini_l1_cuts_added.load();
    out.callback_low_gini_l1_violations =
        cb_state.low_gini_l1_violations.load();
    out.callback_local_centering_cuts_added =
        cb_state.local_centering_cuts_added.load();
    out.callback_local_centering_violations =
        cb_state.local_centering_violations.load();
    out.callback_local_centering_max_violation =
        cb_state.local_centering_max_violation.load();
    out.callback_subset_cross_h_centering_cuts_added =
        cb_state.subset_cross_h_centering_cuts_added.load();
    out.callback_subset_cross_h_centering_candidates =
        cb_state.subset_cross_h_centering_candidates.load();
    out.callback_subset_cross_h_centering_violations =
        cb_state.subset_cross_h_centering_violations.load();
    out.callback_subset_cross_h_centering_max_violation =
        cb_state.subset_cross_h_centering_max_violation.load();
    out.callback_local_q_centering_cuts_added =
        cb_state.local_q_centering_cuts_added.load();
    out.callback_local_q_centering_violations =
        cb_state.local_q_centering_violations.load();
    out.callback_local_q_centering_max_violation =
        cb_state.local_q_centering_max_violation.load();
    out.callback_gs_product_cuts_added =
        cb_state.gs_product_cuts_added.load();
    out.callback_gs_product_violations =
        cb_state.gs_product_violations.load();
    out.callback_gs_product_max_violation =
        cb_state.gs_product_max_violation.load();
    out.callback_disagg_sp_cuts_added =
        cb_state.disagg_sp_cuts_added.load();
    out.callback_disagg_sp_violations =
        cb_state.disagg_sp_violations.load();
    out.callback_disagg_sp_max_violation =
        cb_state.disagg_sp_max_violation.load();
    out.callback_vector_route_cutset_cuts_added =
        cb_state.vector_route_cutset_cuts_added.load();
    out.callback_vector_route_cutset_candidates =
        cb_state.vector_route_cutset_candidates.load();
    out.callback_vector_route_cutset_violations =
        cb_state.vector_route_cutset_violations.load();
    out.callback_vector_route_cutset_max_violation =
        cb_state.vector_route_cutset_max_violation.load();
    out.callback_vector_route_cutset_violation_sum =
        cb_state.vector_route_cutset_violation_sum.load();
    out.callback_vector_route_cutset_cuts_size_2 =
        cb_state.vector_route_cutset_cuts_by_size[2].load();
    out.callback_vector_route_cutset_cuts_size_3 =
        cb_state.vector_route_cutset_cuts_by_size[3].load();
    out.callback_vector_route_cutset_cuts_size_4 =
        cb_state.vector_route_cutset_cuts_by_size[4].load();
    out.callback_vector_route_cutset_cuts_size_5 =
        cb_state.vector_route_cutset_cuts_by_size[5].load();
    out.callback_variable_s_centering_cuts_added =
        cb_state.variable_s_centering_cuts_added.load();
    out.callback_variable_s_centering_violations =
        cb_state.variable_s_centering_violations.load();
    out.callback_subset_inventory_imbalance_cuts_added =
        cb_state.subset_inventory_imbalance_cuts_added.load();
    out.callback_subset_inventory_imbalance_candidates =
        cb_state.subset_inventory_imbalance_candidates.load();
    out.callback_subset_inventory_imbalance_violations =
        cb_state.subset_inventory_imbalance_violations.load();
    out.callback_transfer_cutset_cuts_added =
        cb_state.transfer_cutset_cuts_added.load();
    out.callback_transfer_cutset_candidates =
        cb_state.transfer_cutset_candidates.load();
    out.callback_transfer_cutset_violations =
        cb_state.transfer_cutset_violations.load();
    out.callback_support_duration_pair_cuts_added =
        cb_state.support_duration_pair_cuts_added.load();
    out.callback_support_duration_pair_candidates =
        cb_state.support_duration_pair_candidates.load();
    out.callback_support_duration_pair_violations =
        cb_state.support_duration_pair_violations.load();
    out.callback_support_duration_triple_cuts_added =
        cb_state.support_duration_triple_cuts_added.load();
    out.callback_support_duration_triple_candidates =
        cb_state.support_duration_triple_candidates.load();
    out.callback_support_duration_triple_violations =
        cb_state.support_duration_triple_violations.load();
    out.callback_support_duration_quad_cuts_added =
        cb_state.support_duration_quad_cuts_added.load();
    out.callback_support_duration_quad_candidates =
        cb_state.support_duration_quad_candidates.load();
    out.callback_support_duration_quad_violations =
        cb_state.support_duration_quad_violations.load();
    out.callback_support_duration_lifted_cuts_added =
        cb_state.support_duration_lifted_cuts_added.load();
    out.callback_support_duration_lifted_candidates =
        cb_state.support_duration_lifted_candidates.load();
    out.callback_support_duration_lifted_violations =
        cb_state.support_duration_lifted_violations.load();
    out.lazy_rejections = cb_state.lazy_rejections.load();
    out.lazy_gini_interval_rejections =
        cb_state.lazy_gini_interval_rejections.load();
    out.lazy_visit_inventory_rejections =
        cb_state.lazy_visit_inventory_rejections.load();
    out.lazy_gini_subset_envelope_rejections =
        cb_state.lazy_gini_subset_envelope_rejections.load();
    out.lazy_low_gini_l1_rejections =
        cb_state.lazy_low_gini_l1_rejections.load();
    out.lazy_variable_s_centering_rejections =
        cb_state.lazy_variable_s_centering_rejections.load();
    out.lazy_subset_inventory_imbalance_rejections =
        cb_state.lazy_subset_inventory_imbalance_rejections.load();
    out.incumbents_seen = cb_state.incumbents_seen.load();
    out.incumbents_verified = cb_state.incumbents_verified.load();
    out.incumbents_rejected = cb_state.incumbents_rejected.load();
    out.candidate_projection_checks =
        cb_state.candidate_projection_checks.load();
    out.candidate_projection_verified =
        cb_state.candidate_projection_verified.load();
    out.candidate_projection_rejections =
        cb_state.candidate_projection_rejections.load();
    out.candidate_projection_unsupported_mismatches =
        cb_state.candidate_projection_unsupported_mismatches.load();
    out.candidate_projection_ratio_rejections =
        cb_state.candidate_projection_ratio_rejections.load();
    out.candidate_projection_penalty_rejections =
        cb_state.candidate_projection_penalty_rejections.load();
    out.candidate_projection_objective_rejections =
        cb_state.candidate_projection_objective_rejections.load();
    out.candidate_projection_max_gini_underestimate =
        cb_state.candidate_projection_max_gini_underestimate.load();
    out.candidate_projection_max_objective_underestimate =
        cb_state.candidate_projection_max_objective_underestimate.load();
    out.candidate_route_projection_checks =
        cb_state.candidate_route_projection_checks.load();
    out.candidate_route_projection_verified =
        cb_state.candidate_route_projection_verified.load();
    out.candidate_route_projection_rejections =
        cb_state.candidate_route_projection_rejections.load();
    out.candidate_route_projection_unsupported_mismatches =
        cb_state.candidate_route_projection_unsupported_mismatches.load();
    out.candidate_route_projection_flow_rejections =
        cb_state.candidate_route_projection_flow_rejections.load();
    out.candidate_route_projection_station_rejections =
        cb_state.candidate_route_projection_station_rejections.load();
    out.candidate_route_projection_service_rejections =
        cb_state.candidate_route_projection_service_rejections.load();
    out.candidate_route_projection_duration_rejections =
        cb_state.candidate_route_projection_duration_rejections.load();
    out.candidate_route_projection_inventory_rejections =
        cb_state.candidate_route_projection_inventory_rejections.load();
    out.candidate_route_projection_load_mismatches =
        cb_state.candidate_route_projection_load_mismatches.load();
    out.gini_branches_created = cb_state.gini_branches_created.load();
    if (ncols > 0) {
        std::vector<double> x(static_cast<std::size_t>(ncols), 0.0);
        if (api.getx(env, lp, x.data(), 0, ncols - 1) == 0) {
            for (int i = 0; i < ncols; ++i) {
                if (!names[static_cast<std::size_t>(i)].empty()) {
                    out.values[names[static_cast<std::size_t>(i)]] =
                        x[static_cast<std::size_t>(i)];
                }
            }
        }
    }
    out.solved = status == 0 || out.status_code != 0 || out.callback_wall_time_abort;
    api.freeprob(env, &lp);
    api.close(&env);
    if (api.dll) FreeLibrary(api.dll);
#else
    out.fail_reason = "cplex_dynamic_callbacks_supported_only_on_windows";
#endif
    return out;
}

GlobalGiniTreeApiSolveResult solveGlobalGiniTreeWithTailoredBCCplexApi(
    const std::filesystem::path& root_lp_path,
    const Instance& instance,
    const SolveOptions& options,
    double root_gamma_L,
    double root_gamma_U,
    double verified_incumbent,
    const std::vector<RoutePlan>& verified_routes,
    double time_limit_seconds,
    int threads,
    const std::filesystem::path& node_trace_path,
    const std::filesystem::path& bound_trace_path,
    const std::filesystem::path& manifest_path) {
    GlobalGiniTreeApiSolveResult out;
    out.attempted = true;
    out.node_trace_path = node_trace_path.string();
    out.bound_trace_path = bound_trace_path.string();
    out.manifest_path = manifest_path.string();
    out.post_row_trace_path = options.global_gini_tree_post_row_trace_path;
    out.topology_trace_path = options.global_gini_tree_topology_trace_path;
    out.sibling_trace_path = options.global_gini_tree_sibling_trace_path;
    out.row_delta_trace_path = options.global_gini_tree_row_delta_trace_path;
    out.memory_trace_path = options.global_gini_tree_memory_trace_path;
    out.mip_start_audit_path = options.global_gini_tree_mip_start_audit_path;
    out.child_estimate_mode = options.global_gini_tree_child_estimate_mode;
    out.row_attachment_mode = options.global_gini_tree_row_attachment_mode;
    out.row_timing_mode = options.global_gini_tree_row_timing_mode;
    out.threads_requested = std::max(1, threads);
    out.native_time_limit_requested = time_limit_seconds;
    out.native_time_limit_seconds = time_limit_seconds;
    out.root_model_fingerprint = fileFingerprint(root_lp_path);
    out.objective_fingerprint = originalObjectiveFingerprint(instance, options);
    out.presolve_requested = options.global_gini_tree_presolve == "off" ? 0 : 1;
    out.search_requested = options.global_gini_tree_search == "traditional"
        ? kMipSearchTraditional
        : (options.global_gini_tree_search == "auto" ? 0 : kMipSearchDynamic);
    out.node_select_requested = kNodeSelectBestBound;
    if (out.search_requested != kMipSearchTraditional) {
        out.fail_reason =
            "global_gini_tree_dynamic_search_unsupported_after_reproduced_"
            "continuous_branch_sibling_loss_use_traditional";
        return out;
    }
    if (!std::isfinite(time_limit_seconds) || time_limit_seconds <= 0.0) {
        out.fail_reason =
            "strict_native_deadline_must_be_positive_and_finite";
        return out;
    }
#ifdef _WIN32
    Api api;
    std::string fail;
    if (!loadApi(api, fail)) {
        out.fail_reason = fail;
        return out;
    }
    out.available = true;
    CPXENVptr env = nullptr;
    CPXLPptr lp = nullptr;
    auto cleanup = [&]() {
        if (lp != nullptr) {
            out.native.free_problem_return_code = api.freeprob(env, &lp);
            ++out.freeprob_count;
        }
        if (env != nullptr) {
            out.native.close_environment_return_code = api.close(&env);
            ++out.close_count;
        }
        if (api.dll != nullptr) {
            FreeLibrary(api.dll);
            api.dll = nullptr;
        }
    };
    auto emitFailureManifest = [&]() {
        if (manifest_path.empty()) return;
        if (manifest_path.has_parent_path()) {
            std::filesystem::create_directories(manifest_path.parent_path());
        }
        std::ofstream manifest(manifest_path);
        if (!manifest) return;
        manifest
            << "field,value\n"
            << "failure_reason," << csvCell(out.fail_reason) << '\n'
            << "cplex_environment_count," << out.environment_count << '\n'
            << "problem_object_count," << out.problem_count << '\n'
            << "lp_read_build_count," << out.model_read_count << '\n'
            << "CPXmipopt_count," << out.mipopt_count << '\n'
            << "free_problem_count," << out.freeprob_count << '\n'
            << "close_environment_count," << out.close_count << '\n'
            << "free_problem_return_code,"
            << out.native.free_problem_return_code << '\n'
            << "close_environment_return_code,"
            << out.native.close_environment_return_code << '\n'
            << "threads_requested," << out.threads_requested << '\n'
            << "threads_set_return_code," << out.threads_set_rc << '\n'
            << "threads_get_return_code," << out.threads_get_rc << '\n'
            << "threads_effective," << out.threads_effective << '\n'
            << "time_limit_requested," << std::setprecision(17)
            << out.native_time_limit_requested << '\n'
            << "time_limit_set_return_code,"
            << out.native_time_limit_set_rc << '\n'
            << "time_limit_get_return_code,"
            << out.native_time_limit_get_rc << '\n'
            << "time_limit_effective," << std::setprecision(17)
            << out.native_time_limit_effective << '\n'
            << "relative_gap_setter_return_code,"
            << out.native.relative_gap.setter_return_code << '\n'
            << "relative_gap_getter_return_code,"
            << out.native.relative_gap.getter_return_code << '\n'
            << "relative_gap_effective,"
            << out.native.relative_gap.effective << '\n'
            << "absolute_gap_setter_return_code,"
            << out.native.absolute_gap.setter_return_code << '\n'
            << "absolute_gap_getter_return_code,"
            << out.native.absolute_gap.getter_return_code << '\n'
            << "absolute_gap_effective,"
            << out.native.absolute_gap.effective << '\n'
            << "lifecycle_valid,0\n";
    };
    auto finishEarly = [&]() {
        cleanup();
        emitFailureManifest();
    };
    int status = 0;
    env = api.open(&status);
    if (!env || status != 0) {
        out.fail_reason = "CPXopenCPLEX_failed:" + std::to_string(status);
        finishEarly();
        return out;
    }
    ++out.environment_count;
    if (!options.log_path.empty()) {
        const std::filesystem::path log_path(options.log_path);
        if (log_path.has_parent_path()) {
            std::filesystem::create_directories(log_path.parent_path());
        }
        out.log_set_rc = api.setlogfilename(
            env, options.log_path.c_str(), "w");
        if (out.log_set_rc != 0) {
            out.fail_reason = "CPXsetlogfilename_failed:" +
                std::to_string(out.log_set_rc);
            finishEarly();
            return out;
        }
    } else {
        out.log_set_rc = 0;
    }
    lp = api.createprob(env, &status, "global_gini_tree");
    if (!lp || status != 0) {
        out.fail_reason = "CPXcreateprob_failed:" + std::to_string(status);
        finishEarly();
        return out;
    }
    ++out.problem_count;
    status = api.readcopyprob(env, lp, root_lp_path.string().c_str(), nullptr);
    if (status != 0) {
        out.fail_reason = "CPXreadcopyprob_failed:" + std::to_string(status);
        finishEarly();
        return out;
    }
    ++out.model_read_count;
    out.model_columns = api.getnumcols(env, lp);
    out.model_rows = api.getnumrows(env, lp);
    out.model_nonzeros = static_cast<long long>(api.getnumnz(env, lp));

    out.threads_set_rc = api.setintparam(
        env, kParamThreads, out.threads_requested);
    api.setintparam(env, kParamScreenOutput, 1);
    api.setintparam(env, kParamMipDisplay, 2);
    const bool strict_gaps_ok = configureStrictMipGaps(api, env, out.native);
    out.presolve_set_rc = api.setintparam(
        env, kParamPreprocessingPresolve, out.presolve_requested);
    out.search_set_rc = api.setintparam(
        env, kParamMipStrategySearch, out.search_requested);
    out.node_select_set_rc = api.setintparam(
        env, kParamMipStrategyNodeSelect, out.node_select_requested);
    if (time_limit_seconds > 0.0) {
        out.native_time_limit_set_rc = api.setdblparam(
            env, kParamTimeLimit, time_limit_seconds);
    } else {
        out.native_time_limit_set_rc = 0;
    }
    CPXINT effective = 0;
    out.presolve_get_rc = api.getintparam(
        env, kParamPreprocessingPresolve, &effective);
    if (out.presolve_get_rc == 0) {
        out.presolve_effective = effective;
    }
    out.search_get_rc = api.getintparam(
        env, kParamMipStrategySearch, &effective);
    if (out.search_get_rc == 0) {
        out.search_effective = effective;
    }
    out.node_select_get_rc = api.getintparam(
        env, kParamMipStrategyNodeSelect, &effective);
    if (out.node_select_get_rc == 0) {
        out.node_select_effective = effective;
    }
    out.heuristics_get_rc = api.getintparam(
        env, kParamMipStrategyHeuristicFreq, &effective);
    if (out.heuristics_get_rc == 0) {
        out.heuristics_effective = effective;
    }
    out.probing_get_rc = api.getintparam(
        env, kParamMipStrategyProbe, &effective);
    if (out.probing_get_rc == 0) {
        out.probing_effective = effective;
    }
    out.threads_get_rc = api.getintparam(env, kParamThreads, &effective);
    if (out.threads_get_rc == 0) {
        out.threads_effective = effective;
    }
    out.native_time_limit_get_rc = api.getdblparam(
        env, kParamTimeLimit, &out.native_time_limit_effective);
    const bool required_parameter_round_trips =
        out.threads_set_rc == 0 && out.threads_get_rc == 0 &&
        out.threads_effective == out.threads_requested &&
        out.presolve_set_rc == 0 && out.presolve_get_rc == 0 &&
        out.presolve_effective == out.presolve_requested &&
        out.search_set_rc == 0 && out.search_get_rc == 0 &&
        out.search_effective == out.search_requested &&
        out.node_select_set_rc == 0 && out.node_select_get_rc == 0 &&
        out.node_select_effective == out.node_select_requested &&
        out.heuristics_get_rc == 0 && out.probing_get_rc == 0 &&
        out.native_time_limit_set_rc == 0 &&
        out.native_time_limit_get_rc == 0 &&
        (time_limit_seconds <= 0.0 ||
         out.native_time_limit_effective == time_limit_seconds) &&
        strict_gaps_ok;
    if (!required_parameter_round_trips) {
        out.fail_reason = "required_parameter_configuration_failed";
        finishEarly();
        return out;
    }

    const int ncols = api.getnumcols(env, lp);
    const std::vector<std::string> names = getColumnNames(api, env, lp, ncols);
    out.variable_domain_fingerprint = variableDomainFingerprint(
        api, env, lp, names);
    GlobalGiniCallbackState callback_state;
    callback_state.api = &api;
    callback_state.instance = &instance;
    callback_state.options = &options;
    callback_state.ncols = ncols;
    callback_state.root_lower = root_gamma_L;
    callback_state.root_upper = root_gamma_U;
    callback_state.verified_incumbent = verified_incumbent;
    callback_state.presolve_effective = out.presolve_effective;
    callback_state.search_effective = out.search_effective;
    callback_state.node_select_effective = out.node_select_effective;
    callback_state.run_id = root_lp_path.parent_path().filename().string();
    if (callback_state.run_id.empty()) callback_state.run_id = "global_gini_tree";
    callback_state.start = std::chrono::steady_clock::now();
    if (options.dense_progress_enabled) {
        if (options.dense_progress_raw_event_path.empty()) {
            out.fail_reason = "dense_progress_raw_event_path_empty";
            finishEarly();
            return out;
        }
        DenseProgressConfig dense;
        dense.enabled = true;
        dense.raw_event_path = options.dense_progress_raw_event_path;
        dense.run_id = options.dense_progress_run_id.empty()
            ? callback_state.run_id : options.dense_progress_run_id;
        dense.algorithm = options.dense_progress_algorithm_arm.empty()
            ? "tailored_global_tree"
            : options.dense_progress_algorithm_arm;
        dense.flow_variant =
            options.global_gini_tree_root_connectivity_flow_variant.empty()
                ? (options.global_gini_tree_root_connectivity_flow
                       ? "round20-current" : "off")
                : options.global_gini_tree_root_connectivity_flow_variant;
        dense.executable_sha256 = options.round22_executable_sha256;
        dense.model_rows = out.model_rows;
        dense.model_columns = out.model_columns;
        dense.model_nonzeros = out.model_nonzeros;
        dense.verified_upper_bound_available =
            std::isfinite(verified_incumbent);
        dense.verified_upper_bound = verified_incumbent;
        callback_state.dense_progress =
            std::make_unique<DenseProgressRecorder>(std::move(dense));
        out.dense_progress_raw_event_path =
            options.dense_progress_raw_event_path;
        const DenseProgressReadOnlyPolicy policy =
            denseProgressReadOnlyPolicy();
        out.dense_progress_read_only_contract =
            !policy.may_add_rows && !policy.may_branch &&
            !policy.may_reject_candidate && !policy.may_abort &&
            !policy.may_change_parameters &&
            !policy.may_call_auxiliary_optimizer;
    }
    for (int column = 0; column < ncols; ++column) {
        if (!names[static_cast<std::size_t>(column)].empty()) {
            callback_state.column_index[names[static_cast<std::size_t>(column)]] =
                column;
        }
    }
    const auto g_column = callback_state.column_index.find("G");
    if (g_column == callback_state.column_index.end()) {
        out.fail_reason = "root_G_column_missing";
        finishEarly();
        return out;
    }
    callback_state.g_col = g_column->second;

    IntervalRowFactoryRequest root_request;
    root_request.gamma_L = root_gamma_L;
    root_request.gamma_U = root_gamma_U;
    root_request.verified_incumbent = verified_incumbent;
    root_request.incumbent_epsilon = 0.0;
    root_request.add_incumbent_row = true;
    root_request.strengthened = true;
    const IntervalRowFactoryResult root_rows = buildRound18StaticIntervalRows(
        instance, options, root_request);
    out.row_factory_version = root_rows.factory_version;
    out.root_row_signature = root_rows.aggregate_signature;
    out.row_migration_complete = root_rows.complete_round18_static_migration;
    callback_state.root_inheritance_state =
        std::make_shared<const CanonicalInheritanceState>(
            makeCanonicalInheritanceState(root_rows));
    std::vector<std::string> active_row_families;
    std::vector<std::string> active_callback_families;
    for (const IntervalRowFamilyRegistryEntry& entry :
         root_rows.family_registry) {
        if (!entry.active) continue;
        active_row_families.push_back(entry.family);
        if (entry.scope == IntervalRowScope::Global) {
            callback_state.global_families.push_back(entry.family);
        } else {
            active_callback_families.push_back(entry.family);
        }
    }
    out.row_family_inventory = joinText(active_row_families, "|");
    out.callback_row_inventory = joinText(active_callback_families, "|");
    out.root_coverage_valid = root_gamma_L <= 1e-12 &&
        root_gamma_U >= std::min(
            verified_incumbent,
            instance.V > 0
                ? static_cast<double>(instance.V - 1) / instance.V
                : 1.0) - 1e-10;
    if (!out.row_migration_complete || !out.root_coverage_valid ||
        !callback_state.root_inheritance_state ||
        !callback_state.root_inheritance_state->valid ||
        root_rows.domain.domain_infeasible ||
        options.frontier_adaptive_split_factor != 2) {
        out.fail_reason = !out.row_migration_complete
            ? "row_factory_migration_incomplete"
            : (!out.root_coverage_valid
                   ? "root_improving_range_incomplete"
                   : (!callback_state.root_inheritance_state ||
                          !callback_state.root_inheritance_state->valid
                           ? "root_canonical_inheritance_invalid:" +
                              (callback_state.root_inheritance_state
                                   ? callback_state.root_inheritance_state->failure_reason
                                   : std::string("missing"))
                          : (root_rows.domain.domain_infeasible
                                 ? "root_factory_domain_infeasible_fail_closed"
                                 : "official_global_tree_requires_unchanged_binary_split_factor_2")));
        finishEarly();
        return out;
    }

    std::ofstream node_trace;
    std::ofstream bound_trace;
    std::ofstream post_row_trace;
    std::ofstream topology_trace;
    std::ofstream sibling_trace;
    std::ofstream row_delta_trace;
    std::ofstream memory_trace;
    if (!node_trace_path.empty()) {
        std::filesystem::create_directories(node_trace_path.parent_path());
        node_trace.open(node_trace_path, std::ios::out | std::ios::trunc);
        node_trace
            << "run_id,event_sequence,elapsed_wall_time,node_uid,parent_uid,"
            << "node_depth,gini_generation,relaxation_pass,local_row_phase,"
            << "gamma_L,gamma_U,node_relaxation_bound,global_best_bound,"
            << "native_incumbent,verified_cutoff,callback_context,branch_action,split_point,"
            << "lower_child_gamma_L,lower_child_gamma_U,upper_child_gamma_L,"
            << "upper_child_gamma_U,lower_child_estimate,upper_child_estimate,"
            << "lower_branch_rc,upper_branch_rc,lower_child_uid,upper_child_uid,"
            << "lower_local_families,upper_local_families,global_rows_active_by_family,local_flags,"
            << "lower_row_signatures,upper_row_signatures,presolve_state,"
            << "search_mode,node_selection_mode,node_count,open_nodes,"
            << "simplex_iterations,row_factory_seconds,row_api_seconds,native_cuts\n";
        callback_state.node_trace = &node_trace;
    }
    if (!bound_trace_path.empty()) {
        std::filesystem::create_directories(bound_trace_path.parent_path());
        bound_trace.open(bound_trace_path, std::ios::out | std::ios::trunc);
        bound_trace << "elapsed_time,native_global_LB,native_incumbent,verified_cutoff,"
                       "native_gap,node_count,open_nodes,simplex_iterations,event_source\n";
        callback_state.bound_trace = &bound_trace;
    }
    auto openTrace = [](std::ofstream& stream, const std::string& path) {
        if (path.empty()) return false;
        const std::filesystem::path file(path);
        if (file.has_parent_path()) {
            std::filesystem::create_directories(file.parent_path());
        }
        stream.open(file, std::ios::out | std::ios::trunc);
        return static_cast<bool>(stream);
    };
    if (openTrace(post_row_trace, options.global_gini_tree_post_row_trace_path)) {
        post_row_trace
            << "run_id,node_uid,parent_uid,native_depth,gini_generation,"
               "relaxation_pass,gamma_L,gamma_U,pre_local_row_relaxation,"
               "post_local_row_relaxation,delta_rows_attached,duplicates_omitted,"
               "row_factory_seconds,row_api_seconds,status\n";
        callback_state.post_row_trace = &post_row_trace;
    }
    if (openTrace(topology_trace, options.global_gini_tree_topology_trace_path)) {
        topology_trace
            << "run_id,parent_uid,parent_parent_uid,parent_native_depth,"
               "parent_gini_generation,child_gini_generation,parent_gamma_L,"
               "parent_gamma_U,split,parent_relaxation,lower_uid,lower_gamma_L,lower_gamma_U,"
               "lower_estimate,lower_gamma_floor,lower_weighted_penalty_lb,"
               "lower_domain_estimate,lower_lift,lower_station_deviation_lbs,"
               "upper_uid,upper_gamma_L,upper_gamma_U,upper_estimate,"
               "upper_gamma_floor,upper_weighted_penalty_lb,upper_domain_estimate,"
               "upper_lift,upper_station_deviation_lbs,estimate_mode,sibling_discriminated,creation_time,"
               "creation_node_count,open_nodes,simplex_iterations,validity_status,"
               "failure_reason\n";
        callback_state.topology_trace = &topology_trace;
    }
    if (openTrace(sibling_trace, options.global_gini_tree_sibling_trace_path)) {
        sibling_trace
            << "run_id,child_uid,parent_uid,sibling_uid,creation_time,"
               "first_process_time,delay_seconds,creation_node_count,"
               "first_process_node_count,delay_processed_nodes,child_estimate,"
               "domain_estimate,estimate_lift,estimate_mode\n";
        callback_state.sibling_trace = &sibling_trace;
    }
    if (openTrace(row_delta_trace, options.global_gini_tree_row_delta_trace_path)) {
        row_delta_trace
            << "run_id,node_uid,parent_uid,event,row_attachment_mode,"
               "theoretical_full_rows,theoretical_full_bounds,inherited_rows,"
               "inherited_bounds,exact_duplicate_rows_omitted,"
               "identical_bounds_omitted,dominance_omissions,delta_rows_attached,"
               "delta_bounds_attached,row_factory_seconds,families,"
               "aggregate_signature,status,failure_reason\n";
        callback_state.row_delta_trace = &row_delta_trace;
    }
    if (openTrace(memory_trace, options.global_gini_tree_memory_trace_path)) {
        memory_trace
            << "run_id,elapsed_time,node_count,open_nodes,simplex_iterations,"
               "native_tree_memory_mb,source\n";
        callback_state.memory_trace = &memory_trace;
    }
    CPXLONG context_mask =
        kContextCandidate | kContextRelaxation | kContextBranching |
        kContextGlobalProgress;
    if (options.dense_progress_enabled) {
        context_mask |= kContextLocalProgress;
    }
    status = api.callbacksetfunc(env, lp, context_mask,
                                 globalGiniTreeCallback, &callback_state);
    if (status != 0) {
        out.fail_reason = "CPXcallbacksetfunc_failed:" + std::to_string(status);
        finishEarly();
        return out;
    }

    out.native_mip_start_attempted = options.global_gini_tree_native_mip_start;
    if (options.global_gini_tree_native_mip_start) {
        const NativeMipStartMapping mapping = buildVerifiedNativeMipStart(
            api, env, lp, instance, options, verified_routes,
            verified_incumbent, names);
        out.native_mip_start_mapping_complete = mapping.complete;
        out.native_mip_start_failure_reason = mapping.failure_reason;
        if (!mapping.complete) {
            out.fail_reason = "native_mip_start_mapping_failed:" +
                mapping.failure_reason;
            finishEarly();
            return out;
        }
        std::vector<int> indices(static_cast<std::size_t>(ncols), 0);
        std::iota(indices.begin(), indices.end(), 0);
        const int begin = 0;
        const int effort = 1;
        char start_name[] = "verified_same_run_incumbent";
        char* start_names[] = {start_name};
        out.native_mip_start_return_code = api.addmipstarts(
            env, lp, 1, ncols, &begin, indices.data(), mapping.values.data(),
            &effort, start_names);
        out.native_mip_start_submitted =
            out.native_mip_start_return_code == 0;
        out.native_mip_start_stored_count = api.getnummipstarts(env, lp);
        out.native_mip_start_stored =
            out.native_mip_start_stored_count > 0;
        if (!out.native_mip_start_submitted ||
            !out.native_mip_start_stored) {
            out.native_mip_start_failure_reason =
                "CPXaddmipstarts_or_storage_failed:rc=" +
                std::to_string(out.native_mip_start_return_code) +
                ":stored=" +
                std::to_string(out.native_mip_start_stored_count);
            out.fail_reason = out.native_mip_start_failure_reason;
            finishEarly();
            return out;
        }
    }
    if (!options.global_gini_tree_mip_start_audit_path.empty()) {
        const std::filesystem::path audit_path(
            options.global_gini_tree_mip_start_audit_path);
        if (audit_path.has_parent_path()) {
            std::filesystem::create_directories(audit_path.parent_path());
        }
        std::ofstream audit(audit_path, std::ios::out | std::ios::trunc);
        audit << "field,value\n"
              << "enabled," << (options.global_gini_tree_native_mip_start
                                     ? "true" : "false") << '\n'
              << "verified_routes," << verified_routes.size() << '\n'
              << "mapping_complete,"
              << (out.native_mip_start_mapping_complete ? "true" : "false")
              << '\n'
              << "submitted,"
              << (out.native_mip_start_submitted ? "true" : "false") << '\n'
              << "return_code," << out.native_mip_start_return_code << '\n'
              << "stored_count," << out.native_mip_start_stored_count << '\n'
              << "stored,"
              << (out.native_mip_start_stored ? "true" : "false") << '\n'
              << "failure_reason,"
              << csvCell(out.native_mip_start_failure_reason) << '\n';
    }

    ++out.mipopt_count;
    status = api.mipopt(env, lp);
    out.return_code = status;
    captureNativeMipEvidence(api, env, lp, status, out.native);
    out.status_code = out.native.status_code;
    out.status = out.native.status_text;
    out.solver_finalization_reached = out.native.solve_returned &&
        out.native.mipopt_return_code == 0;
    if (out.native.objective_available) out.objective = out.native.objective;
    if (out.native.best_bound_available) {
        out.best_bound = out.native.best_bound;
        out.best_bound_available = true;
    }
    out.node_count = static_cast<long long>(api.getnodecnt(env, lp));
    out.native_open_nodes =
        static_cast<long long>(api.getnodeleftcnt(env, lp));
    out.native_simplex_iterations =
        static_cast<long long>(api.getmipitcnt(env, lp));
    out.native_solution_pool_count = api.getsolnpoolnumsolns(env, lp);
    out.native_cut_counts = collectNativeCutCounts(api, env, lp);
    if (out.native_mip_start_stored && out.objective > 0.0 &&
        out.objective <= verified_incumbent +
            1e-7 * std::max(1.0, std::fabs(verified_incumbent))) {
        // The native log audit separately confirms whether CPLEX reports the
        // submitted complete start as its initial solution.
        out.native_mip_start_accepted = true;
    }
    if (callback_state.bound_trace && out.best_bound_available) {
        *callback_state.bound_trace << std::setprecision(17)
            << globalTreeElapsed(callback_state) << ',' << out.best_bound << ','
            << out.objective << ',' << verified_incumbent << ','
            << std::max(0.0, out.objective - out.best_bound) << ','
            << out.node_count << ',' << out.native_open_nodes << ','
            << out.native_simplex_iterations << ",solver_final\n";
        callback_state.bound_trace->flush();
    }
    out.branch_callback_calls = callback_state.branch_calls.load();
    out.relaxation_callback_calls = callback_state.relaxation_calls.load();
    out.candidate_callback_calls = callback_state.candidate_calls.load();
    out.progress_callback_calls = callback_state.progress_calls.load();
    out.gini_branch_nodes = callback_state.gini_branch_nodes.load();
    out.gini_children_created = callback_state.gini_children_created.load();
    out.gini_branch_generations =
        callback_state.max_gini_generation.load();
    out.ordinary_branch_fallbacks = callback_state.ordinary_fallbacks.load();
    out.nonoptimal_relaxation_fallbacks =
        callback_state.nonoptimal_relaxation_fallbacks.load();
    out.local_rows_attached = callback_state.local_rows_attached.load();
    out.local_bound_changes_attached =
        callback_state.local_bounds_attached.load();
    out.local_row_failures = callback_state.local_row_failures.load();
    out.column_mapping_failures = callback_state.column_mapping_failures.load();
    out.coverage_failures = callback_state.coverage_failures.load();
    out.child_estimate_failures =
        callback_state.child_estimate_failures.load();
    out.local_bound_api_failures =
        callback_state.local_bound_api_failures.load();
    out.node_info_api_failures =
        callback_state.node_info_api_failures.load();
    out.callback_failures = callback_state.callback_failures.load();
    out.post_row_reoptimizations =
        callback_state.post_row_reoptimizations.load();
    out.post_row_reoptimization_failures =
        callback_state.post_row_reoptimization_failures.load();
    out.theoretical_full_rows = callback_state.theoretical_full_rows.load();
    out.theoretical_full_bounds =
        callback_state.theoretical_full_bounds.load();
    out.exact_duplicate_rows_omitted =
        callback_state.exact_duplicate_rows_omitted.load();
    out.identical_bounds_omitted =
        callback_state.identical_bounds_omitted.load();
    out.delta_rows_attached = callback_state.delta_rows_attached.load();
    out.delta_bounds_attached = callback_state.delta_bounds_attached.load();
    out.ordinary_branches_before_terminal_gini =
        callback_state.ordinary_before_terminal.load();
    out.ordinary_branches_after_terminal_gini =
        callback_state.ordinary_after_terminal.load();
    out.sibling_first_process_count =
        callback_state.sibling_first_process_count.load();
    out.sibling_equal_estimate_pairs =
        callback_state.sibling_equal_estimate_pairs.load();
    out.sibling_discriminated_pairs =
        callback_state.sibling_discriminated_pairs.load();
    out.first_gini_branch_time = callback_state.first_gini_branch_time.load();
    out.row_factory_seconds = callback_state.row_factory_seconds.load();
    out.callback_packing_seconds =
        callback_state.callback_packing_seconds.load();
    out.local_row_api_seconds = callback_state.local_row_api_seconds.load();
    out.callback_abort_used = callback_state.callback_abort_used.load();
    out.row_migration_complete = out.row_migration_complete &&
        callback_state.migration_complete.load();
    out.branch_coverage_valid = callback_state.branch_coverage_valid.load() &&
        out.coverage_failures == 0;
    out.global_bound_monotone = callback_state.bound_monotone.load();
    out.sibling_isolation_by_construction = out.local_row_failures == 0 &&
        out.gini_children_created == 2 * out.gini_branch_nodes;
    out.recursive_branching_complete = out.row_migration_complete &&
        out.branch_coverage_valid && out.local_bound_api_failures == 0 &&
        out.column_mapping_failures == 0 && out.child_estimate_failures == 0 &&
        out.post_row_reoptimization_failures == 0;
    if (ncols > 0) {
        std::vector<double> x(static_cast<std::size_t>(ncols), 0.0);
        if (api.getx(env, lp, x.data(), 0, ncols - 1) == 0) {
            for (int column = 0; column < ncols; ++column) {
                if (!names[static_cast<std::size_t>(column)].empty()) {
                    out.values[names[static_cast<std::size_t>(column)]] =
                        x[static_cast<std::size_t>(column)];
                }
            }
        }
    }
    out.solved = status == 0 && out.status_code != 0 &&
        !out.callback_abort_used;

    if (callback_state.dense_progress) {
        DenseProgressSnapshot final;
        final.observation_time_seconds = globalTreeElapsed(callback_state);
        final.callback_invocation_sequence =
            callback_state.dense_progress->stats().callback_invocation_count;
        final.native_best_bound_available = out.best_bound_available;
        final.native_best_bound = out.best_bound;
        final.native_incumbent_available = out.native.objective_available;
        final.native_incumbent = out.native.objective;
        final.verified_upper_bound_available = true;
        final.verified_upper_bound = verified_incumbent;
        final.processed_nodes_available = out.node_count >= 0;
        final.processed_nodes = out.node_count;
        final.open_nodes_available = out.native_open_nodes >= 0;
        final.open_nodes = out.native_open_nodes;
        final.native_solution_count_available =
            out.native_solution_pool_count >= 0;
        final.native_solution_count = out.native_solution_pool_count;
        final.simplex_iterations_available =
            out.native_simplex_iterations >= 0;
        final.simplex_iterations = out.native_simplex_iterations;
        final.gini_branch_count = out.gini_branch_nodes;
        final.ordinary_branch_count = out.ordinary_branch_fallbacks;
        callback_state.dense_progress->appendSolverFinal(final);
    }

    cleanup();
    out.lifecycle_valid = out.environment_count == 1 &&
        out.problem_count == 1 && out.model_read_count == 1 &&
        out.mipopt_count == 1 && out.freeprob_count == 1 &&
        out.close_count == 1 && out.interval_oracle_count == 0 &&
        out.child_process_count == 0 &&
        out.native.free_problem_return_code == 0 &&
        out.native.close_environment_return_code == 0;
    if (callback_state.dense_progress) {
        callback_state.dense_progress->flush();
        out.dense_progress = callback_state.dense_progress->stats();
    }
    if (!out.solved && out.fail_reason.empty()) {
        out.fail_reason = out.callback_abort_used
            ? "callback_correctness_abort"
            : "CPXmipopt_failed:" + std::to_string(status);
    }
    if (!manifest_path.empty()) {
        if (manifest_path.has_parent_path()) {
            std::filesystem::create_directories(manifest_path.parent_path());
        }
        std::ofstream manifest(manifest_path, std::ios::out | std::ios::trunc);
        std::vector<std::string> global_families;
        std::vector<std::string> local_families;
        std::vector<std::string> bound_families;
        std::vector<std::string> excluded_families;
        for (const IntervalRowFamilyRegistryEntry& entry :
             root_rows.family_registry) {
            if (!entry.active) continue;
            if (entry.scope == IntervalRowScope::Global) {
                global_families.push_back(entry.family);
            } else if (entry.scope == IntervalRowScope::IntervalLocal) {
                local_families.push_back(entry.family);
            } else if (entry.scope == IntervalRowScope::IntervalBound) {
                bound_families.push_back(entry.family);
            } else {
                excluded_families.push_back(entry.family);
            }
        }
        manifest << "field,value\n";
        manifest
            << "root_model_path," << csvCell(root_lp_path.string()) << '\n'
            << "root_lp_fingerprint," << out.root_model_fingerprint << '\n'
            << "objective_definition,min G + lambda*sum_i(weight_i*e_i)\n"
            << "objective_fingerprint," << out.objective_fingerprint << '\n'
            << "global_row_fingerprint," << out.root_row_signature << '\n'
            << "shared_row_factory_version," << out.row_factory_version << '\n'
            << "active_global_families,"
            << csvCell(joinText(global_families, "|")) << '\n'
            << "active_interval_local_families,"
            << csvCell(joinText(local_families, "|")) << '\n'
            << "active_interval_bound_families,"
            << csvCell(joinText(bound_families, "|")) << '\n'
            << "unsupported_active_families,"
            << csvCell(joinText(excluded_families, "|")) << '\n'
            << "cplex_environment_count," << out.environment_count << '\n'
            << "problem_object_count," << out.problem_count << '\n'
            << "lp_read_build_count," << out.model_read_count << '\n'
            << "root_model_columns," << out.model_columns << '\n'
            << "root_model_rows," << out.model_rows << '\n'
            << "root_model_nonzeros," << out.model_nonzeros << '\n'
            << "CPXmipopt_count," << out.mipopt_count << '\n'
            << "CPXmipopt_return_code," << out.native.mipopt_return_code << '\n'
            << "native_status_code," << out.native.status_code << '\n'
            << "native_status_text," << csvCell(out.native.status_text) << '\n'
            << "CPXgetobjval_return_code,"
            << out.native.objective_return_code << '\n'
            << "native_objective_available,"
            << (out.native.objective_available ? 1 : 0) << '\n'
            << "native_objective," << std::setprecision(17)
            << out.native.objective << '\n'
            << "CPXgetbestobjval_return_code,"
            << out.native.best_bound_return_code << '\n'
            << "native_best_bound_available,"
            << (out.native.best_bound_available ? 1 : 0) << '\n'
            << "native_best_bound," << std::setprecision(17)
            << out.native.best_bound << '\n'
            << "CPXgetmiprelgap_return_code,"
            << out.native.mip_relative_gap_return_code << '\n'
            << "CPXgetmiprelgap_available,"
            << (out.native.mip_relative_gap_available ? 1 : 0) << '\n'
            << "CPXgetmiprelgap_value," << std::setprecision(17)
            << out.native.mip_relative_gap << '\n'
            << "relative_gap_parameter_id,"
            << out.native.relative_gap.parameter_id << '\n'
            << "relative_gap_requested,"
            << out.native.relative_gap.requested << '\n'
            << "relative_gap_setter_return_code,"
            << out.native.relative_gap.setter_return_code << '\n'
            << "relative_gap_getter_return_code,"
            << out.native.relative_gap.getter_return_code << '\n'
            << "relative_gap_effective,"
            << out.native.relative_gap.effective << '\n'
            << "absolute_gap_parameter_id,"
            << out.native.absolute_gap.parameter_id << '\n'
            << "absolute_gap_requested,"
            << out.native.absolute_gap.requested << '\n'
            << "absolute_gap_setter_return_code,"
            << out.native.absolute_gap.setter_return_code << '\n'
            << "absolute_gap_getter_return_code,"
            << out.native.absolute_gap.getter_return_code << '\n'
            << "absolute_gap_effective,"
            << out.native.absolute_gap.effective << '\n'
            << "strict_gap_configuration_valid,"
            << (out.native.strict_gap_configuration_valid ? 1 : 0) << '\n'
            << "free_problem_return_code,"
            << out.native.free_problem_return_code << '\n'
            << "close_environment_return_code,"
            << out.native.close_environment_return_code << '\n'
            << "free_problem_count," << out.freeprob_count << '\n'
            << "close_environment_count," << out.close_count << '\n'
            << "solver_finalization_reached,"
            << (out.solver_finalization_reached ? 1 : 0) << '\n'
            << "lifecycle_valid," << (out.lifecycle_valid ? 1 : 0) << '\n'
            << "threads_requested," << out.threads_requested << '\n'
            << "threads_set_return_code," << out.threads_set_rc << '\n'
            << "threads_get_return_code," << out.threads_get_rc << '\n'
            << "threads_effective," << out.threads_effective << '\n'
            << "presolve_requested," << out.presolve_requested << '\n'
            << "presolve_set_return_code," << out.presolve_set_rc << '\n'
            << "presolve_get_return_code," << out.presolve_get_rc << '\n'
            << "search_requested," << out.search_requested << '\n'
            << "search_set_return_code," << out.search_set_rc << '\n'
            << "search_get_return_code," << out.search_get_rc << '\n'
            << "node_select_requested," << out.node_select_requested << '\n'
            << "node_select_set_return_code," << out.node_select_set_rc << '\n'
            << "node_select_get_return_code," << out.node_select_get_rc << '\n'
            << "time_limit_parameter_id," << kParamTimeLimit << '\n'
            << "time_limit_requested," << std::setprecision(17)
            << out.native_time_limit_requested << '\n'
            << "time_limit_set_return_code,"
            << out.native_time_limit_set_rc << '\n'
            << "time_limit_get_return_code,"
            << out.native_time_limit_get_rc << '\n'
            << "time_limit_effective," << std::setprecision(17)
            << out.native_time_limit_effective << '\n'
            << "interval_oracle_count," << out.interval_oracle_count << '\n'
            << "child_process_count," << out.child_process_count << '\n'
            << "child_estimate_mode,"
            << csvCell(out.child_estimate_mode) << '\n'
            << "row_attachment_mode,"
            << csvCell(out.row_attachment_mode) << '\n'
            << "row_timing_mode,"
            << csvCell(out.row_timing_mode) << '\n'
            << "interval_local_attachment,"
            << (out.row_timing_mode == "eager"
                    ? "local_rows_in_CPXcallbackmakebranch"
                    : "forced_local_user_cut_at_first_child_relaxation")
            << '\n'
            << "interval_local_flag,1\n"
            << "local_rows_attached," << out.local_rows_attached << '\n'
            << "theoretical_full_rows," << out.theoretical_full_rows << '\n'
            << "exact_duplicate_rows_omitted,"
            << out.exact_duplicate_rows_omitted << '\n'
            << "delta_rows_attached," << out.delta_rows_attached << '\n'
            << "theoretical_full_bounds," << out.theoretical_full_bounds << '\n'
            << "identical_bounds_omitted,"
            << out.identical_bounds_omitted << '\n'
            << "delta_bounds_attached," << out.delta_bounds_attached << '\n'
            << "local_row_failures," << out.local_row_failures << '\n'
            << "post_row_reoptimizations,"
            << out.post_row_reoptimizations << '\n'
            << "post_row_reoptimization_failures,"
            << out.post_row_reoptimization_failures << '\n'
            << "native_mip_start_attempted,"
            << (out.native_mip_start_attempted ? 1 : 0) << '\n'
            << "native_mip_start_mapping_complete,"
            << (out.native_mip_start_mapping_complete ? 1 : 0) << '\n'
            << "native_mip_start_stored,"
            << (out.native_mip_start_stored ? 1 : 0) << '\n'
            << "native_mip_start_accepted,"
            << (out.native_mip_start_accepted ? 1 : 0) << '\n'
            << "native_mip_start_failure_reason,"
            << csvCell(out.native_mip_start_failure_reason) << '\n'
            << "nonoptimal_relaxation_fallbacks,"
            << out.nonoptimal_relaxation_fallbacks << '\n'
            << "solver_final_status," << csvCell(out.status) << '\n'
            << "best_bound_source,CPXgetbestobjval\n"
            << "presolve_effective," << out.presolve_effective << '\n'
            << "search_effective," << out.search_effective << '\n'
            << "dynamic_search_compatibility,rejected_after_reproduced_continuous_branch_sibling_loss\n"
            << "node_select_effective," << out.node_select_effective << '\n'
            << "heuristic_frequency_effective," << out.heuristics_effective << '\n'
            << "probing_effective," << out.probing_effective << '\n'
            << "native_cuts,CPLEX_default\n";
    }
#else
    out.fail_reason = "cplex_dynamic_callbacks_supported_only_on_windows";
#endif
    return out;
}

} // namespace ebrp
