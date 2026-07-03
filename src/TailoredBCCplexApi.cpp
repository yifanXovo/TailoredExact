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
constexpr int kParamPreprocessingPresolve = 1030;
constexpr int kParamMipStrategyHeuristicFreq = 2031;
constexpr int kParamMipStrategySearch = 2109;
constexpr int kMipSearchTraditional = 1;
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
using CPXcallbackgetrelaxationpoint_t = int (__stdcall *)(CPXCALLBACKCONTEXTptr, double*, int, int, double*);
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
    CPXcallbackgetrelaxationpoint_t callbackgetrelaxationpoint = nullptr;
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
    LOAD_REQ(callbackgetrelaxationpoint, "CPXcallbackgetrelaxationpoint");
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

std::string zNameForVehicleStation(int vehicle, int station) {
    return "z_" + std::to_string(vehicle) + "_" + std::to_string(station);
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
    std::vector<int> r_cols;
    std::vector<int> e_cols;
    std::vector<int> q_l1_cols;
    std::vector<int> y_cols;
    std::vector<std::vector<int>> z_cols;
    std::vector<int> station_initial;
    std::vector<int> station_capacity;
    std::vector<int> station_target;
    std::vector<double> station_weight;
    double lambda = 0.0;
    double cutoff_value = std::numeric_limits<double>::infinity();
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
    std::atomic<long long> gini_interval_cuts_added{0};
    std::atomic<long long> visit_inventory_cuts_added{0};
    std::atomic<long long> gini_subset_envelope_cuts_added{0};
    std::atomic<long long> gini_subset_envelope_candidates{0};
    std::atomic<long long> gini_subset_envelope_violations{0};
    std::atomic<long long> low_gini_l1_cuts_added{0};
    std::atomic<long long> low_gini_l1_violations{0};
    std::atomic<long long> lazy_rejections{0};
    std::atomic<long long> lazy_gini_interval_rejections{0};
    std::atomic<long long> lazy_visit_inventory_rejections{0};
    std::atomic<long long> lazy_gini_subset_envelope_rejections{0};
    std::atomic<long long> lazy_low_gini_l1_rejections{0};
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
    std::atomic<long long> gini_branches_created{0};
    std::atomic<bool> gini_cut_added{false};
    std::atomic<bool> gini_branch_created{false};
};

void atomicMax(std::atomic<double>& target, double value) {
    if (!std::isfinite(value) || value <= 0.0) return;
    double current = target.load();
    while (value > current &&
           !target.compare_exchange_weak(current, value)) {
    }
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

void separateGiniSubsetEnvelope(CallbackState& state,
                                CPXCALLBACKCONTEXTptr context) {
    if (state.ncols <= 0 || state.r_cols.size() <= 1 ||
        state.gamma_U < -1e-12) {
        return;
    }
    if (state.gini_subset_envelope_cuts_added.load() > 0) return;
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
    auto addSubsetCut = [&](const std::vector<int>& subset, int sign) {
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
            if (addOneUserCut(state, context, terms, 'L', 0.0)) {
                state.gini_subset_envelope_cuts_added.fetch_add(1);
            }
        }
    };
    if (sum_r <= 1e-12) return;
    for (int i = 1; i <= V; ++i) {
        addSubsetCut({i}, 1);
        addSubsetCut({i}, -1);
    }
    for (int i = 1; i <= V; ++i) {
        for (int j = i + 1; j <= V; ++j) {
            addSubsetCut({i, j}, 1);
            addSubsetCut({i, j}, -1);
        }
    }
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
    if (validateCandidateGiniSubsetEnvelope(state, context, x)) return;
    if (validateCandidateLowGiniL1(state, context, x)) return;
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
            if (rc == 0) {
                ++state->user_cuts_added;
                ++state->gini_interval_cuts_added;
            }
        }
        separateVisitInventoryLinking(*state, context);
        separateGiniSubsetEnvelope(*state, context);
        separateLowGiniL1Centering(*state, context);
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
    double lambda,
    double cutoff_value,
    int vehicle_count) {
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
    const int station_count =
        std::min(static_cast<int>(station_initial.size()),
                 static_cast<int>(station_capacity.size()));
    std::vector<int> y_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> r_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> e_cols(static_cast<std::size_t>(station_count), -1);
    std::vector<int> q_l1_cols(static_cast<std::size_t>(station_count), -1);
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
    std::vector<std::vector<int>> z_cols(
        static_cast<std::size_t>(std::max(0, vehicle_count)),
        std::vector<int>(static_cast<std::size_t>(station_count), -1));
    for (int k = 0; k < vehicle_count; ++k) {
        for (int i = 1; i < station_count; ++i) {
            std::vector<int> found = buildNameToIndexLookup(
                names, zNameForVehicleStation(k, i));
            if (!found.empty()) {
                z_cols[static_cast<std::size_t>(k)][static_cast<std::size_t>(i)] =
                    found.front();
            }
        }
    }
    CallbackState cb_state;
    cb_state.api = &api;
    cb_state.ncols = ncols;
    cb_state.g_col = g_col;
    cb_state.r_cols = std::move(r_cols);
    cb_state.e_cols = std::move(e_cols);
    cb_state.q_l1_cols = std::move(q_l1_cols);
    cb_state.y_cols = std::move(y_cols);
    cb_state.z_cols = std::move(z_cols);
    cb_state.station_initial = station_initial;
    cb_state.station_capacity = station_capacity;
    cb_state.station_target = station_target;
    cb_state.station_weight = station_weight;
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
    out.callback_low_gini_l1_cuts_added =
        cb_state.low_gini_l1_cuts_added.load();
    out.callback_low_gini_l1_violations =
        cb_state.low_gini_l1_violations.load();
    out.lazy_rejections = cb_state.lazy_rejections.load();
    out.lazy_gini_interval_rejections =
        cb_state.lazy_gini_interval_rejections.load();
    out.lazy_visit_inventory_rejections =
        cb_state.lazy_visit_inventory_rejections.load();
    out.lazy_gini_subset_envelope_rejections =
        cb_state.lazy_gini_subset_envelope_rejections.load();
    out.lazy_low_gini_l1_rejections =
        cb_state.lazy_low_gini_l1_rejections.load();
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
