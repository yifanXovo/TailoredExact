#include "TailoredBCCplexApi.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <mutex>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <thread>
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
constexpr int kParamPreprocessingPresolve = 1030;
constexpr int kParamMipStrategyHeuristicFreq = 2031;
constexpr int kParamMipStrategySearch = 2109;
constexpr int kMipSearchTraditional = 1;
constexpr int kUseCutForce = 0;
constexpr CPXCALLBACKINFO kCallbackInfoNodeCount = 1;
constexpr CPXCALLBACKINFO kCallbackInfoBestSol = 3;
constexpr CPXCALLBACKINFO kCallbackInfoBestBnd = 4;

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
using CPXcallbackgetrelaxationpoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int, double*);
using CPXcallbackgetinfodbl_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, CPXCALLBACKINFO, double*);
using CPXcallbackgetinfolong_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, CPXCALLBACKINFO, CPXLONG*);
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
    CPXcallbackgetrelaxationpoint_t callbackgetrelaxationpoint = nullptr;
    CPXcallbackgetinfodbl_t callbackgetinfodbl = nullptr;
    CPXcallbackgetinfolong_t callbackgetinfolong = nullptr;
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
    LOAD_REQ(callbackgetrelaxationpoint, "CPXcallbackgetrelaxationpoint");
    LOAD_REQ(callbackgetinfodbl, "CPXcallbackgetinfodbl");
    LOAD_REQ(callbackgetinfolong, "CPXcallbackgetinfolong");
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
    int g_col = -1;
    int r_min_col = -1;
    int r_max_col = -1;
    std::vector<int> r_cols;
    std::vector<int> e_cols;
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
    double progress_interval_seconds) {
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
    int r_min_col = -1;
    int r_max_col = -1;
    for (int i = 0; i < ncols; ++i) {
        if (names[static_cast<std::size_t>(i)] == "G") {
            g_col = i;
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
    cb_state.g_col = g_col;
    cb_state.r_min_col = r_min_col;
    cb_state.r_max_col = r_max_col;
    cb_state.r_cols = std::move(r_cols);
    cb_state.e_cols = std::move(e_cols);
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
        };

    if (!progress_log_path.empty()) {
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

} // namespace ebrp
