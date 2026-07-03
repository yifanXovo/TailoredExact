#include "TailoredBCCplexApi.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace ebrp {
namespace {

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
constexpr int kParamThreads = 1067;
constexpr int kParamTimeLimit = 1039;
constexpr int kParamScreenOutput = 1035;
constexpr int kParamMipDisplay = 2012;
constexpr int kUseCutForce = 0;

using CPXopenCPLEX_t = CPXENVptr (__stdcall *)(int*);
using CPXcloseCPLEX_t = int (__stdcall *)(CPXENVptr*);
using CPXcreateprob_t = CPXLPptr (__stdcall *)(CPXCENVptr, int*, const char*);
using CPXfreeprob_t = int (__stdcall *)(CPXCENVptr, CPXLPptr*);
using CPXreadcopyprob_t = int (__stdcall *)(CPXCENVptr, CPXLPptr, const char*, const char*);
using CPXsetintparam_t = int (__stdcall *)(CPXENVptr, int, CPXINT);
using CPXsetdblparam_t = int (__stdcall *)(CPXENVptr, int, double);
using CPXcallbacksetfunc_t = int (__stdcall *)(CPXENVptr, CPXLPptr, CPXLONG, CPXCALLBACKFUNC, void*);
using CPXmipopt_t = int (__stdcall *)(CPXCENVptr, CPXLPptr);
using CPXgetstat_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetstatstring_t = char* (__stdcall *)(CPXCENVptr, int, char*);
using CPXgetobjval_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*);
using CPXgetbestobjval_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*);
using CPXgetnodecnt_t = CPXLONG (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetnumcols_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr);
using CPXgetx_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, double*, int, int);
using CPXgetcolname_t = int (__stdcall *)(CPXCENVptr, CPXCLPptr, char**, char*, int, int*, int, int);
using CPXcallbackaddusercuts_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, int, const double*, const char*, const int*, const int*, const double*, const int*, const int*);
using CPXcallbackcandidateispoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int*);
using CPXcallbackgetcandidatepoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int, double*);
using CPXcallbackrejectcandidate_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, int, const double*, const char*, const int*, const int*, const double*);
using CPXcallbackmakebranch_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, int, const int*, const char*, const double*, int, int, const double*, const char*, const int*, const int*, const double*, double, int*);
using CPXcopyorder_t = int (__stdcall *)(CPXCENVptr, CPXLPptr, int, const int*, const int*, const int*);

struct Api {
    HMODULE dll = nullptr;
    CPXopenCPLEX_t open = nullptr;
    CPXcloseCPLEX_t close = nullptr;
    CPXcreateprob_t createprob = nullptr;
    CPXfreeprob_t freeprob = nullptr;
    CPXreadcopyprob_t readcopyprob = nullptr;
    CPXsetintparam_t setintparam = nullptr;
    CPXsetdblparam_t setdblparam = nullptr;
    CPXcallbacksetfunc_t callbacksetfunc = nullptr;
    CPXmipopt_t mipopt = nullptr;
    CPXgetstat_t getstat = nullptr;
    CPXgetstatstring_t getstatstring = nullptr;
    CPXgetobjval_t getobjval = nullptr;
    CPXgetbestobjval_t getbestobjval = nullptr;
    CPXgetnodecnt_t getnodecnt = nullptr;
    CPXgetnumcols_t getnumcols = nullptr;
    CPXgetx_t getx = nullptr;
    CPXgetcolname_t getcolname = nullptr;
    CPXcallbackaddusercuts_t callbackaddusercuts = nullptr;
    CPXcallbackcandidateispoint_t callbackcandidateispoint = nullptr;
    CPXcallbackgetcandidatepoint_t callbackgetcandidatepoint = nullptr;
    CPXcallbackrejectcandidate_t callbackrejectcandidate = nullptr;
    CPXcallbackmakebranch_t callbackmakebranch = nullptr;
    CPXcopyorder_t copyorder = nullptr;
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
    LOAD_REQ(callbacksetfunc, "CPXcallbacksetfunc");
    LOAD_REQ(mipopt, "CPXmipopt");
    LOAD_REQ(getstat, "CPXgetstat");
    LOAD_REQ(getstatstring, "CPXgetstatstring");
    LOAD_REQ(getobjval, "CPXgetobjval");
    LOAD_REQ(getbestobjval, "CPXgetbestobjval");
    LOAD_REQ(getnodecnt, "CPXgetnodecnt");
    LOAD_REQ(getnumcols, "CPXgetnumcols");
    LOAD_REQ(getx, "CPXgetx");
    LOAD_REQ(getcolname, "CPXgetcolname");
    LOAD_REQ(callbackaddusercuts, "CPXcallbackaddusercuts");
    LOAD_REQ(callbackcandidateispoint, "CPXcallbackcandidateispoint");
    LOAD_REQ(callbackgetcandidatepoint, "CPXcallbackgetcandidatepoint");
    LOAD_REQ(callbackrejectcandidate, "CPXcallbackrejectcandidate");
    LOAD_REQ(callbackmakebranch, "CPXcallbackmakebranch");
    LOAD_REQ(copyorder, "CPXcopyorder");
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

struct CallbackState {
    Api* api = nullptr;
    int ncols = 0;
    int g_col = -1;
    double gamma_L = 0.0;
    double gamma_U = 1.0;
    bool add_gini_cut = false;
    bool validate_candidates = false;
    bool enable_gini_branch = false;
    double gini_branch_min_width = 1e-4;
    std::atomic<long long> relaxation_calls{0};
    std::atomic<long long> candidate_calls{0};
    std::atomic<long long> branch_calls{0};
    std::atomic<long long> progress_calls{0};
    std::atomic<long long> user_cuts_added{0};
    std::atomic<long long> lazy_rejections{0};
    std::atomic<long long> incumbents_seen{0};
    std::atomic<long long> incumbents_verified{0};
    std::atomic<long long> incumbents_rejected{0};
    std::atomic<long long> gini_branches_created{0};
    std::atomic<bool> gini_cut_added{false};
    std::atomic<bool> gini_branch_created{false};
};

bool rejectCandidateWithGiniBound(CallbackState& state,
                                  CPXCALLBACKCONTEXTptr context,
                                  bool upper_bound) {
    if (state.g_col < 0) return false;
    const double rhs[1] = {
        upper_bound ? state.gamma_U : state.gamma_L
    };
    const char sense[1] = {upper_bound ? 'L' : 'G'};
    const int beg[1] = {0};
    const int ind[1] = {state.g_col};
    const double val[1] = {1.0};
    const int rc = state.api->callbackrejectcandidate(
        context, 1, 1, rhs, sense, beg, ind, val);
    if (rc == 0) {
        ++state.lazy_rejections;
        ++state.incumbents_rejected;
        return true;
    }
    return false;
}

void validateCandidatePoint(CallbackState& state,
                            CPXCALLBACKCONTEXTptr context) {
    if (!state.validate_candidates || state.ncols <= 0 || state.g_col < 0) return;
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
    if (contextid == kContextRelaxation) {
        ++state->relaxation_calls;
        bool expected = false;
        if (state->add_gini_cut && state->g_col >= 0 &&
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
            if (rc == 0) ++state->user_cuts_added;
        }
    } else if (contextid == kContextCandidate) {
        ++state->candidate_calls;
        ++state->incumbents_seen;
        validateCandidatePoint(*state, context);
    } else if (contextid == kContextBranching) {
        ++state->branch_calls;
        createOneShotGiniBranches(*state, context);
    } else if (contextid == kContextGlobalProgress) {
        ++state->progress_calls;
    }
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
    double gini_branch_min_width) {
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
    api.setintparam(env, kParamScreenOutput, 0);
    api.setintparam(env, kParamMipDisplay, 0);
    if (time_limit_seconds > 0.0) {
        api.setdblparam(env, kParamTimeLimit, time_limit_seconds);
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
    for (int i = 0; i < ncols; ++i) {
        if (names[static_cast<std::size_t>(i)] == "G") {
            g_col = i;
            break;
        }
    }
    CallbackState cb_state;
    cb_state.api = &api;
    cb_state.ncols = ncols;
    cb_state.g_col = g_col;
    cb_state.gamma_L = gamma_L;
    cb_state.gamma_U = gamma_U;
    cb_state.add_gini_cut = add_redundant_gini_user_cut && g_col >= 0;
    cb_state.validate_candidates = enable_candidate_validation;
    cb_state.enable_gini_branch = enable_gini_branching;
    cb_state.gini_branch_min_width = std::max(1e-12, gini_branch_min_width);
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
    status = api.mipopt(env, lp);
    out.return_code = status;
    out.status_code = api.getstat(env, lp);
    char statbuf[1024] = {0};
    if (api.getstatstring(env, out.status_code, statbuf)) {
        out.status = statbuf;
    } else {
        out.status = "status_code_" + std::to_string(out.status_code);
    }
    double obj = 0.0;
    if (api.getobjval(env, lp, &obj) == 0) out.objective = obj;
    double bound = 0.0;
    if (api.getbestobjval(env, lp, &bound) == 0) out.best_bound = bound;
    out.node_count = static_cast<long long>(api.getnodecnt(env, lp));
    out.relaxation_callback_calls = cb_state.relaxation_calls.load();
    out.candidate_callback_calls = cb_state.candidate_calls.load();
    out.branch_callback_calls = cb_state.branch_calls.load();
    out.progress_callback_calls = cb_state.progress_calls.load();
    out.user_cuts_added = cb_state.user_cuts_added.load();
    out.lazy_rejections = cb_state.lazy_rejections.load();
    out.incumbents_seen = cb_state.incumbents_seen.load();
    out.incumbents_verified = cb_state.incumbents_verified.load();
    out.incumbents_rejected = cb_state.incumbents_rejected.load();
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
    out.solved = status == 0 || out.status_code != 0;
    api.freeprob(env, &lp);
    api.close(&env);
    if (api.dll) FreeLibrary(api.dll);
#else
    out.fail_reason = "cplex_dynamic_callbacks_supported_only_on_windows";
#endif
    return out;
}

} // namespace ebrp
